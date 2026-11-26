"""The shape every host shares: a request, a result, the host interface, and the process runner.

A host adapter turns a `Request` into its CLI's command line, runs it with `run_process`, and reads the CLI's own
output into a `Result`. Operations a host has no route for return a result with status `unsupported` and the reason,
so a caller can treat the three hosts the same way and still see the gaps.
"""

from __future__ import annotations

import fcntl
import json
import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Callable

HOSTS = ("claude", "codex", "antigravity")

# A result's status. `done` means the host finished the turn; the others say why it didn't, or what to look at.
DONE, FAILED, INTERRUPTED, TIMEOUT = "done", "failed", "interrupted", "timeout"
LIMITED = "limited"  # the host refused the turn because a usage limit was reached
REFUSED = "refused"  # the turn finished, but the host refused one or more tool calls without stopping it
UNSUPPORTED = "unsupported"  # the host has no route for this operation; `text` says why
STATUSES = (DONE, FAILED, INTERRUPTED, TIMEOUT, LIMITED, REFUSED, UNSUPPORTED)

POLL_S = 0.5  # how often a running turn's output, stop flag and deadline are checked
STOP_GRACE_S = (15.0, 10.0, 5.0)  # how long a stopped turn gets after SIGINT, then SIGTERM, then SIGKILL


def state_dir() -> Path:
    """Where the relay keeps what must outlive one command: run records, inbox sockets, quota readings. When that
    folder can't be written, as inside Codex's workspace-write sandbox, it falls back to a per-user folder in the
    temporary directory, which sandboxes leave writable; every relay inside the same sandbox then shares it."""
    base = os.environ.get("AGENT_RELAY_STATE_DIR") or \
        Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache") / "agent-relay"
    for path in (Path(base), Path(tempfile.gettempdir()) / f"agent-relay-{os.getuid()}"):
        try:
            path.mkdir(parents=True, exist_ok=True)
            probe = path / f".probe-{os.getpid()}"
            probe.write_text("")  # a sandbox can deny a write that os.access allows
            probe.unlink()
            return path
        except OSError:
            continue
    raise OSError(f"no writable state folder: {base}, or the temporary directory")


@dataclass
class Request:
    """One turn to run. `mode` is the host's own permission setting, passed through by name: Claude's permission mode
    (`default`, `acceptEdits`, `plan`, `auto`, `bypassPermissions`), Codex's sandbox (`read-only`,
    `workspace-write`, `danger-full-access`), or Antigravity's agent mode (`auto`, `accept-edits`, `plan`).
    Left empty, the host's own configuration decides. `args` are extra flags for the host's CLI, passed as they are."""
    prompt: str
    cwd: str = "."
    model: str | None = None
    effort: str | None = None
    session: str | None = None  # resume this session; None starts a new one
    mode: str | None = None
    name: str | None = None  # a title for a new session, where the host takes one
    add_dirs: list[str] = field(default_factory=list)
    args: list[str] = field(default_factory=list)
    env: dict = field(default_factory=dict)
    timeout_s: float = 4 * 3600.0
    app: bool = False  # run it where the host's desktop app shows it


@dataclass
class Result:
    host: str
    status: str
    session: str | None = None
    text: str = ""
    model: str | None = None
    effort: str | None = None
    usage: dict = field(default_factory=dict)  # {input, cached, output}: input excludes cache reads
    warnings: list[str] = field(default_factory=list)
    transcript: str | None = None  # the host's own record of the session, where it keeps one on disk
    exit_code: int | None = None
    stderr: str = ""  # the tail of the CLI's stderr
    stdout: str = field(default="", repr=False)  # the CLI's whole output, for callers that read more from it
    extra: dict = field(default_factory=dict)  # host-specific facts, such as Claude's context size or cost

    def to_json(self, with_output: bool = False) -> dict:
        out = asdict(self)
        if not with_output:
            out.pop("stdout")
        return {k: v for k, v in out.items() if v not in (None, "", [], {}) or k in ("status", "host", "text")}


def unsupported(host: str, why: str, session: str | None = None) -> Result:
    return Result(host=host, status=UNSUPPORTED, session=session, text=why)


class Host:
    """The interface each adapter implements. Every method returns a Result, so the CLI prints the same shape for
    every host and every operation."""
    name = ""
    binary = ""

    def exe(self) -> str:
        return self.binary

    def installed(self) -> bool:
        return bool(shutil.which(self.exe()) or Path(self.exe()).is_file())

    def run(self, req: Request, on_event: Callable[[dict], None] | None = None, **hooks) -> Result:
        raise NotImplementedError

    def stop(self, session: str) -> Result:
        return stop_recorded(self.name, session)

    def send(self, session: str, text: str, **opts) -> Result:
        return unsupported(self.name, f"{self.name} has no documented way to message a session", session)

    def open(self, session: str) -> Result:
        return unsupported(self.name, f"{self.name} has no desktop app route to open a session in", session)

    def status(self, session: str) -> Result:
        rec = live_record(self.name, session)
        state = "busy" if rec else "unknown"
        return Result(host=self.name, status=DONE, session=session, text=state,
                      extra={"state": state, **({"pid": rec["pid"]} if rec else {})})

    def quota(self) -> dict:
        return {"host": self.name, "error": "no quota reading for this host", "windows": [], "banked": []}

    def check(self) -> dict:
        exe = self.exe()
        if not self.installed():
            return {"host": self.name, "installed": False, "binary": exe}
        try:
            out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=30)
            version = (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr).strip() else ""
        except (OSError, subprocess.SubprocessError, IndexError):
            version = ""
        return {"host": self.name, "installed": True, "binary": exe, "version": version}


def get(name: str) -> Host:
    """The adapter for `name`: claude, codex or antigravity (agy and gemini are accepted for antigravity)."""
    name = {"agy": "antigravity", "gemini": "antigravity"}.get(name, name)
    if name == "claude":
        from . import claude
        return claude.Claude()
    if name == "codex":
        from . import codex
        return codex.Codex()
    if name == "antigravity":
        from . import antigravity
        return antigravity.Antigravity()
    raise ValueError(f"unknown host {name!r}; use one of {', '.join(HOSTS)}")


# ----------------------------------------------------------------------------------------------------- run records
# A headless turn's process is recorded under <state>/runs/<host>/<session>.json while it runs, so `stop` and
# `status` work from another process: a lead stopping a builder, say.

def sandbox_note() -> str | None:
    """Why a host CLI may fail here, when this process runs inside Codex's sandbox (which sets CODEX_SANDBOX): the
    other host's CLI then can't reach the network or read its own sign-in, so it reports being signed out."""
    if not os.environ.get("CODEX_SANDBOX"):
        return None
    return ("This ran inside Codex's sandbox, where another agent's CLI can't reach the network or read its own "
            "sign-in. Run the relay command outside the sandbox: ask for that approval in Codex, or start the Codex "
            "session with a sandbox that allows it, which is the user's decision.")


def _record_path(host: str, session: str) -> Path:
    folder = state_dir() / "runs" / host
    folder.mkdir(parents=True, exist_ok=True)
    return folder / f"{session.replace('/', '_')}.json"


def record_run(host: str, session: str, pid: int, cwd: str) -> None:
    _record_path(host, session).write_text(json.dumps({"pid": pid, "pgid": pid, "cwd": cwd, "started_at": time.time()}))


def clear_run(host: str, session: str) -> bool:
    """Removes the run record; True when `stop` had marked it, so the turn's result says it was interrupted even
    where the CLI exits 0 on SIGINT."""
    path = _record_path(host, session)
    try:
        stopped = bool(json.loads(path.read_text()).get("stopped_at"))
    except (OSError, ValueError, AttributeError):
        stopped = False
    try:
        path.unlink()
    except OSError:
        pass
    return stopped


def live_record(host: str, session: str) -> dict | None:
    """The run record for `session` when its process is still alive, else None (a stale one is removed)."""
    path = _record_path(host, session)
    try:
        rec = json.loads(path.read_text())
        os.kill(int(rec["pid"]), 0)
        return rec
    except (OSError, ValueError, KeyError, TypeError):
        try:
            path.unlink()
        except OSError:
            pass
        return None


def stop_recorded(host: str, session: str) -> Result:
    rec = live_record(host, session)
    if not rec:
        return Result(host=host, status=FAILED, session=session,
                      text="no running turn the relay started is recorded for this session")
    try:
        _record_path(host, session).write_text(json.dumps({**rec, "stopped_at": time.time()}))
    except OSError:
        pass
    stopped = stop_group(int(rec["pgid"]))
    return Result(host=host, status=DONE if stopped else FAILED, session=session,
                  text="stopped" if stopped else "the process group didn't exit after SIGKILL")


# ---------------------------------------------------------------------------------------------------- the runner

def _signal_group(pgid: int, sig: int) -> bool:
    try:
        os.killpg(pgid, sig)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def _group_alive(pgid: int) -> bool:
    try:
        os.killpg(pgid, 0)
        return True
    except (ProcessLookupError, PermissionError):
        return False


def stop_group(pgid: int, proc: subprocess.Popen | None = None) -> bool:
    """Stops a process group the way a user at the terminal would: SIGINT first, which every one of these CLIs
    treats as "stop the turn and save it" (Claude exits 143 on SIGTERM with the turn half written), then SIGTERM,
    then SIGKILL. True once the group has gone."""
    for sig, wait in zip((signal.SIGINT, signal.SIGTERM, signal.SIGKILL), STOP_GRACE_S):
        if not _signal_group(pgid, sig):
            return True
        deadline = time.time() + wait
        while time.time() < deadline:
            if proc is not None:
                proc.poll()
            if not _group_alive(pgid):
                return True
            time.sleep(0.1)
    return not _group_alive(pgid)


@dataclass
class Run:
    code: int  # the exit code; 124 timed out, 130 stopped, 127 couldn't start
    stdout: str
    stderr: str
    ended_by: str = ""  # what the watch hook said when it ended the turn early


def run_process(args: list[str], cwd: str | None, env: dict | None, timeout_s: float,
                on_line: Callable[[str], None] | None = None,
                watch: Callable[[str], str | None] | None = None,
                tick: Callable[[], None] | None = None,
                should_stop: Callable[[], bool] | None = None,
                on_start: Callable[[int], None] | None = None,
                stdin_text: str | None = None) -> Run:
    """Runs a CLI turn in its own process group and returns its output.

    Output goes to files, not pipes, so a background process the agent left holding the pipe can't keep the turn
    open after the CLI exits; whatever is left of the group is stopped then. `on_line` gets each complete stdout
    line as it arrives. `watch` gets each new piece of stdout; a non-empty answer ends the turn as finished (for a
    host whose turn is over while its process lingers). `tick` runs about every half second. `should_stop` returning
    True stops the turn (exit 130), and the deadline stops it too (exit 124)."""
    with tempfile.TemporaryDirectory(prefix="agent-relay-") as tmp:
        out_path, err_path = Path(tmp) / "out", Path(tmp) / "err"
        stdin = subprocess.DEVNULL
        if stdin_text is not None:
            in_path = Path(tmp) / "in"
            in_path.write_text(stdin_text)
            stdin = open(in_path, "rb")
        with open(out_path, "ab") as out_w, open(err_path, "ab") as err_w:
            try:
                proc = subprocess.Popen(args, cwd=cwd, stdin=stdin, stdout=out_w, stderr=err_w,
                                        start_new_session=True, env=env)
            except OSError as e:
                return Run(127, "", f"couldn't start {args[0]}: {e}")
            finally:
                if stdin_text is not None:
                    stdin.close()
        if on_start:
            on_start(proc.pid)

        def output() -> tuple[str, str]:
            return out_path.read_text(errors="replace"), err_path.read_text(errors="replace")

        deadline, partial = time.time() + timeout_s, ""
        with open(out_path, "r", errors="replace") as reader:
            def drain() -> str:
                nonlocal partial
                chunk = reader.read()
                if chunk and on_line:
                    lines = (partial + chunk).split("\n")
                    partial = lines.pop()
                    for line in lines:
                        if line.strip():
                            on_line(line)
                return chunk

            while True:
                try:
                    proc.wait(timeout=POLL_S)
                    drain()
                    if partial.strip() and on_line:
                        on_line(partial)
                    _signal_group(proc.pid, signal.SIGTERM)  # leftovers of a group whose leader has exited
                    return Run(proc.returncode, *output())
                except subprocess.TimeoutExpired:
                    pass
                chunk = drain()
                if tick:
                    tick()
                ended = watch(chunk) if watch else None
                if ended:
                    stop_group(proc.pid, proc)
                    return Run(0, *output(), ended_by=str(ended))
                stopping = bool(should_stop and should_stop())
                if stopping or time.time() > deadline:
                    stop_group(proc.pid, proc)
                    out, err = output()
                    return Run(130 if stopping else 124, out, err + ("\n(stopped)" if stopping else "\n(timed out)"))


def run_in_pty(args: list[str], cwd: str | None, env: dict | None, timeout_s: float,
               should_stop: Callable[[], bool] | None = None, tty_stdin: bool = False) -> Run:
    """`run_process` for a CLI that writes nothing unless its output is a terminal (and, with `tty_stdin`, one that
    also wants its input to be). Lines that parse as JSON are returned as stdout and the rest as stderr."""
    import pty
    import select
    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen(args, cwd=cwd, stdin=slave if tty_stdin else subprocess.DEVNULL, stdout=slave,
                                stderr=slave, start_new_session=True, env=env)
    except OSError as e:
        os.close(master)
        os.close(slave)
        return Run(127, "", f"couldn't start {args[0]}: {e}")
    os.close(slave)
    chunks, deadline, code = [], time.time() + timeout_s, None
    while True:
        ready, _, _ = select.select([master], [], [], POLL_S)
        if ready:
            try:
                data = os.read(master, 1 << 16)
            except OSError:
                data = b""
            if data:
                chunks.append(data)
                continue
        if proc.poll() is not None:
            code = proc.returncode
            break
        stopping = bool(should_stop and should_stop())
        if stopping or time.time() > deadline:
            stop_group(proc.pid, proc)
            code = 130 if stopping else 124
            break
    os.close(master)
    _signal_group(proc.pid, signal.SIGTERM)
    text = b"".join(chunks).decode(errors="replace").replace("\r\n", "\n")
    out, err = [], []
    for line in text.splitlines():
        try:
            json.loads(line)
            out.append(line)
        except json.JSONDecodeError:
            err.append(line)
    return Run(code, "\n".join(out), "\n".join(err))


class FileLock:
    """An exclusive lock on a file under the state folder, held across processes: `with FileLock("agy-start"):`."""

    def __init__(self, name: str, timeout_s: float = 300.0):
        self.path, self.timeout_s, self.handle = state_dir() / f"{name}.lock", timeout_s, None
        self._guard = threading.Lock()

    def __enter__(self):
        self.handle = open(self.path, "a")
        deadline = time.time() + self.timeout_s
        while True:
            try:
                fcntl.flock(self.handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                if time.time() > deadline:
                    raise TimeoutError(f"{self.path} stayed locked for {self.timeout_s:g}s")
                time.sleep(0.2)

    def release(self) -> None:
        with self._guard:
            if self.handle:
                try:
                    fcntl.flock(self.handle, fcntl.LOCK_UN)
                finally:
                    self.handle.close()
                    self.handle = None

    def __exit__(self, *exc):
        self.release()


# ---------------------------------------------------------------------------------------------------- utilities

def json_lines(text: str):
    """The JSON objects in `text`, one per line, skipping lines that aren't JSON objects."""
    for line in text.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            yield event


def add_usage(total: dict, turn: dict) -> dict:
    out = dict(total)
    for k, v in turn.items():
        if isinstance(v, (int, float)):
            out[k] = round(out.get(k, 0) + v, 6) if isinstance(v, float) else out.get(k, 0) + v
    return out


LIMIT_WORDS = ("usage limit", "rate limit", "quota", "limit reached", "resource_exhausted", "too many requests")


def looks_limited(text: str) -> bool:
    low = (text or "").lower()
    return any(w in low for w in LIMIT_WORDS)


def git_common_dir(cwd: str) -> str | None:
    """The repository's shared .git folder, which a worktree's agent must be able to write to commit; None outside
    a repository."""
    try:
        out = subprocess.run(["git", "-C", cwd, "rev-parse", "--git-common-dir"], capture_output=True, text=True,
                             timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0 or not out.stdout.strip():
        return None
    return str((Path(cwd) / out.stdout.strip()).resolve())


def open_url(url: str) -> bool:
    """Hands a URL to the app that owns its scheme, in the background (macOS `open -g`, else `xdg-open`)."""
    opener = ["open", "-g"] if shutil.which("open") and os.uname().sysname == "Darwin" else ["xdg-open"]
    try:
        return subprocess.run([*opener, url], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
