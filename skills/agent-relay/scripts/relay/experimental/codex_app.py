"""EXPERIMENTAL: a Codex turn that the desktop app runs and shows, so the user can watch and steer it there.

OpenAI documents no way for another program to start or follow a turn in the Codex app: the app runs a private
app-server that talks only to the app (openai/codex#40134, #41014). This module uses what works today, and each
piece names what would retire it:

  - The thread is created by a short-lived `codex app-server` (`thread/start`, then a one-line bootstrap turn so
    the thread records the model, effort and sandbox the app resumes it with). `projectId` places it under the
    project that holds the folder; the app's sidebar ignores that field for now, so these threads list under
    Recents until openai/codex#40935 is fixed.
  - Each turn is queued with `codex queue` (documented) and the app is told to take it with the
    `codex://threads/wake/<id>` link (undocumented).
  - The turn is followed in the thread's session file, `$CODEX_HOME/sessions/**/rollout-*<id>.jsonl`, whose event
    format is Codex's own and not a published interface.
  - A turn is stopped with `turn/interrupt` only when the app runs on the shared app-server daemon
    (`codex app-server daemon start`, and the app started with CODEX_APP_SERVER_USE_LOCAL_DAEMON=1), whose control
    socket speaks JSON-RPC over a websocket. Otherwise only the user can stop it, in the app; the goal is paused
    and the queue cleared so nothing new starts.

Everything here is macOS-only and may break on any app update. The documented alternative is a headless run
(`codex exec`), which the app doesn't show.
"""

from __future__ import annotations

import base64
import json
import os
import queue
import socket
import struct
import sys
import threading
import time
from pathlib import Path

from .. import codex as codex_host
from .. import hosts
from ..hosts import DONE, FAILED, INTERRUPTED, TIMEOUT, Result

WARNING = ("Ran in the Codex app through agent-relay's experimental app mode, which rests on undocumented app "
           "behaviour (openai/codex#40134); headless runs are the supported route.")
BOOTSTRAP = "agent-relay started this thread; its task arrives as the next message. Reply with exactly: ready"
SETTLE_S = 20.0  # quiet time after the last turn ends, so a goal's chained turn isn't taken for the end
WAKE_S = 120.0  # how often a queued turn that hasn't started is woken again
GIVE_UP_S = 3 * 3600.0  # how long a turn may stay queued (the app asleep or busy) before the relay gives up
POLL_S = 1.0
CONTROL_SOCK = codex_host.CODEX_HOME / "app-server-control" / "app-server-control.sock"


def app_cli() -> str:
    """The CLI the Codex app bundles, which shares the app's thread store (AGENT_RELAY_CODEX_APP overrides it)."""
    return os.environ.get("AGENT_RELAY_CODEX_APP") or codex_host.APP_BUNDLED


def unavailable() -> str | None:
    """Why app mode can't run here, or None."""
    if sys.platform != "darwin":
        return "the Codex app's links are macOS-only"
    if not Path(app_cli()).exists():
        return "the Codex app isn't installed"
    if not app_running():
        return "the Codex app isn't running"
    return None


def app_running() -> bool:
    app = next((p for p in Path(app_cli()).parents if p.suffix == ".app"), None)
    try:
        import subprocess
        out = subprocess.run(["ps", "-axo", "comm="], capture_output=True, text=True, timeout=30).stdout
    except OSError:
        return False
    return app is not None and any(line.strip().startswith(f"{app}/Contents/MacOS/") for line in out.splitlines())


def project_for(projects: list[dict], paths: list[str]) -> str | None:
    """The Codex project whose root is, or holds, the first of `paths` one does; the deepest root wins."""
    for path in paths:
        best = None
        for p in projects:
            for root in p.get("roots") or []:
                r = str(Path(root.get("path", "")).resolve()) if root.get("path") else ""
                if r and (path == r or path.startswith(r.rstrip("/") + "/")) and (best is None or len(r) > best[0]):
                    best = (len(r), p.get("id"))
        if best:
            return best[1]
    return None


def create_thread(req) -> str:
    """Creates a thread with the request's model, effort and sandbox, named and placed under its project."""
    sandbox = req.mode or "workspace-write"
    if sandbox == "danger-full-access":
        policy = {"type": "dangerFullAccess"}
    elif sandbox == "read-only":
        policy = {"type": "readOnly"}
    else:
        roots = list(req.add_dirs)
        policy = {"type": "workspaceWrite", "networkAccess": True, "writableRoots": roots}
    # The thread takes the request's `-c` settings as its config, except those thread/start sets by its own fields
    set_apart = ("approval_policy", "approvals_reviewer", "sandbox_mode", "sandbox_workspace_write.", "model")
    config = {k: _toml_value(v) for k, v in (f.split("=", 1) for f in _config_flags(req.args))
              if not k.startswith(set_apart)}
    if req.effort:
        config["model_reasoning_effort"] = req.effort
    approvals = {"approvalPolicy": "on-request", "approvalsReviewer": "auto_review"}
    with codex_host.AppServer(app_cli()) as srv:
        start = {"cwd": str(Path(req.cwd).resolve()), "threadSource": "user", "sandbox": sandbox, "config": config,
                 **approvals, **({"model": req.model} if req.model else {})}
        try:
            projects = (srv.call("project/list", {}) or {}).get("data") or []
            repo = hosts.git_common_dir(req.cwd)
            paths = [str(Path(req.cwd).resolve())] + ([str(Path(repo).parent)] if repo else [])
            if project := project_for(projects, paths):
                start["projectId"] = project
        except (RuntimeError, OSError, KeyError, AttributeError):
            pass  # placement is a convenience
        thread = srv.call("thread/start", start)["thread"]["id"]
        srv.call("turn/start", {"threadId": thread, "sandboxPolicy": policy,
                                "input": [{"type": "text", "text": BOOTSTRAP, "text_elements": []}], **approvals,
                                **({"model": req.model} if req.model else {}),
                                **({"effort": req.effort} if req.effort else {})})
        done = srv.wait_for("turn/completed", timeout=180)
        if (status := done["params"]["turn"].get("status")) != "completed":
            raise RuntimeError(f"the bootstrap turn ended {status}")
        if req.name:
            srv.call("thread/name/set", {"threadId": thread, "name": req.name[:80]})
    return thread


def _config_flags(args: list[str]) -> list[str]:
    """The `key=value` of each `-c key=value` in a request's extra args, which a thread takes as its config."""
    return [args[i + 1] for i, a in enumerate(args[:-1]) if a in ("-c", "--config") and "=" in args[i + 1]]


def _toml_value(text: str):
    try:
        return json.loads(text)
    except ValueError:
        return {"true": True, "false": False}.get(text, text)


class SharedServer:
    """JSON-RPC to the shared app-server daemon: a websocket at /rpc over its control socket. When the app runs on
    the daemon, `turn/interrupt` here stops a turn as the app's Stop button does."""

    def __init__(self, timeout: float = 10.0, path: Path | None = None):
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.settimeout(timeout)
        try:
            self.s.connect(os.path.realpath(path or CONTROL_SOCK))
            key = base64.b64encode(os.urandom(16)).decode()
            self.s.sendall((f"GET /rpc HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                            f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
            head = b""
            while b"\r\n\r\n" not in head:
                chunk = self.s.recv(4096)
                if not chunk:
                    raise ConnectionError("the daemon closed the connection during the handshake")
                head += chunk
            head, self.buf = head.split(b"\r\n\r\n", 1)
            if b" 101 " not in head.split(b"\r\n", 1)[0]:
                raise ConnectionError(f"the daemon refused the websocket: {head[:120]!r}")
            self.s.settimeout(None)
        except BaseException:
            self.s.close()
            raise
        self.q, self.n, self.lock = queue.Queue(), 0, threading.Lock()
        threading.Thread(target=self._read, daemon=True).start()
        self.call("initialize", {"clientInfo": {"name": "agent-relay", "title": "agent-relay", "version": "1"},
                                 "capabilities": {"experimentalApi": True}}, timeout=timeout)
        self._send({"jsonrpc": "2.0", "method": "initialized", "params": {}})

    def _frame(self, opcode: int, data: bytes) -> None:
        mask, n = os.urandom(4), len(data)
        size = bytes([0x80 | n]) if n < 126 else bytes([0x80 | 126]) + struct.pack(">H", n) if n < 1 << 16 \
            else bytes([0x80 | 127]) + struct.pack(">Q", n)
        with self.lock:
            self.s.sendall(bytes([0x80 | opcode]) + size + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _send(self, obj):
        self._frame(0x1, json.dumps(obj).encode())

    def _take(self):
        if len(self.buf) < 2:
            return None
        n, at = self.buf[1] & 0x7F, 2
        if n == 126:
            if len(self.buf) < 4:
                return None
            n, at = struct.unpack(">H", self.buf[2:4])[0], 4
        elif n == 127:
            if len(self.buf) < 10:
                return None
            n, at = struct.unpack(">Q", self.buf[2:10])[0], 10
        if len(self.buf) < at + n:
            return None
        head, data, self.buf = self.buf[0], self.buf[at:at + n], self.buf[at + n:]
        return head & 0x80, head & 0x0F, data

    def _read(self):
        message = b""
        try:
            while True:
                while (frame := self._take()) is None:
                    chunk = self.s.recv(65536)
                    if not chunk:
                        return
                    self.buf += chunk
                fin, opcode, data = frame
                if opcode == 0x8:
                    return
                if opcode == 0x9:
                    self._frame(0xA, data)
                    continue
                message += data
                if fin:
                    try:
                        self.q.put(json.loads(message))
                    except ValueError:
                        pass
                    message = b""
        except OSError:
            return

    def call(self, method: str, params: dict, timeout: float = 30.0):
        self.n += 1
        rid, deadline = self.n, time.time() + timeout
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        while time.time() < deadline:
            try:
                m = self.q.get(timeout=max(0.05, min(1.0, deadline - time.time())))
            except queue.Empty:
                continue
            if m.get("id") == rid and "method" not in m:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result")
        raise TimeoutError(method)

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass


def interrupt(thread: str, turn: str | None) -> str:
    """Stops the thread's turn through the daemon: "" when it took the stop, else why it couldn't."""
    if not CONTROL_SOCK.exists():
        return ("the Codex app runs this thread in its own app-server, which only the app can reach, and no shared "
                "app-server daemon is running")
    try:
        srv = SharedServer()
    except (OSError, RuntimeError, TimeoutError, ValueError) as e:
        return f"the app-server daemon refused the connection ({type(e).__name__}: {e})"
    try:
        loaded = (srv.call("thread/loaded/list", {}) or {}).get("data") or []
        if thread not in loaded:
            return "the daemon doesn't hold this thread, so the app runs it in its own app-server"
        try:
            goal = (srv.call("thread/goal/get", {"threadId": thread}) or {}).get("goal") or {}
            if goal.get("status") == "active":  # first, so no goal turn is chained after the stopped one
                srv.call("thread/goal/set", {"threadId": thread, "status": "paused"})
        except RuntimeError:
            pass
        if turn:
            srv.call("turn/interrupt", {"threadId": thread, "turnId": turn})
        return ""
    except (OSError, RuntimeError, TimeoutError, ValueError) as e:
        return f"the daemon refused the stop ({type(e).__name__}: {e})"
    finally:
        srv.close()


def turn_id(payload: dict) -> str | None:
    return payload.get("turn_id") or (payload.get("turn_attribution") or {}).get("turn_id")


def new_events(path: Path | None, offset: int) -> tuple[list[dict], int]:
    if path is None:
        return [], offset
    try:
        with open(path, "rb") as handle:
            handle.seek(offset)
            data = handle.read()
    except OSError:
        return [], offset
    end = data.rfind(b"\n") + 1
    out = []
    for line in data[:end].splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            continue
    return out, offset + end


def run(host, req, on_event=None, should_stop=None, watch_event=None, **_ignored) -> Result:
    """One turn in the Codex app. `on_event` gets each session-file event as it is written; `watch_event` may return
    a reason to stop the turn early, as a finished one (a tool call that hung, say)."""
    if why := unavailable():
        return Result(host="codex", status=FAILED, session=req.session, text=f"app mode is unavailable: {why}")
    thread = req.session
    warnings = [WARNING]
    try:
        if thread is None:
            thread = create_thread(req)
        path = codex_host.rollout(thread)
        offset = path.stat().st_size if path else 0
        sent = host.send(thread, req.prompt)
        if sent.status != DONE:
            raise RuntimeError(sent.text)
        if not hosts.open_url(f"codex://threads/wake/{thread}"):
            raise RuntimeError("the wake link didn't open")
    except (OSError, RuntimeError, TimeoutError, ValueError, KeyError) as e:
        return Result(host="codex", status=FAILED, session=thread, text=f"{type(e).__name__}: {e}", warnings=warnings)

    began = time.time()
    deadline, running, started, quiet, woken = began + req.timeout_s, set(), False, began, 0
    message, error, aborted, last_turn = "", "", False, None

    def stop(goal_back: bool = False) -> str:
        why = interrupt(thread, next(iter(running), None) or last_turn)
        if why:
            host.set_goal(thread, "paused")
            host.unqueue(thread)
            warnings.append(f"the turn may still be running in the app ({why}); stop it there")
        elif goal_back:
            host.set_goal(thread, "active")  # a timeout isn't the user pausing the goal
        return why

    while True:
        path = path or codex_host.rollout(thread)
        events, offset = new_events(path, offset)
        for event in events:
            if on_event:
                on_event(event)
            p = event.get("payload") or {}
            kind = p.get("type")
            if event.get("type") == "response_item" and kind == "message" and p.get("role") == "assistant":
                text = [c.get("text", "") for c in p.get("content") or [] if isinstance(c, dict)]
                message = "\n".join(t for t in text if t) or message
            if event.get("type") != "event_msg":
                continue
            if kind == "task_started":
                last_turn = turn_id(p)
                running.add(last_turn)
                started, aborted, quiet = True, False, time.time()
            elif kind in ("task_complete", "turn_complete", "turn_aborted"):
                running.discard(turn_id(p))
                aborted, quiet = kind == "turn_aborted", time.time()
                message = p.get("last_agent_message") or message
            elif kind == "error":
                error = str(p.get("message") or p)[:500]
            if watch_event and (ended := watch_event(event)):
                stop()
                return Result(host="codex", status=DONE, session=thread, text=message, model=req.model,
                              effort=req.effort, warnings=warnings, transcript=str(path) if path else None,
                              extra={"ended_by": str(ended), "app": True})
        if should_stop and should_stop():
            stop()
            return Result(host="codex", status=INTERRUPTED, session=thread, text=message, warnings=warnings,
                          transcript=str(path) if path else None, extra={"app": True})
        if time.time() > deadline:
            if not started:
                host.unqueue(thread)
            stop(goal_back=True)
            return Result(host="codex", status=TIMEOUT, session=thread, text=message, warnings=warnings,
                          transcript=str(path) if path else None, extra={"app": True})
        if not started:
            waited = time.time() - began
            gone = waited > 2 * WAKE_S and (host.queued(thread) == 0 or unavailable())
            if gone or waited > 2 * WAKE_S + GIVE_UP_S:
                host.unqueue(thread)
                return Result(host="codex", status=FAILED, session=thread, warnings=warnings,
                              text="the Codex app didn't start the queued turn (signed out, or not running?); its "
                                   "queued message was removed", extra={"app": True})
            if waited > WAKE_S * (woken + 1):
                woken += 1 if hosts.open_url(f"codex://threads/wake/{thread}") else 0
        elif not running and time.time() - quiet >= SETTLE_S and not (host.queued(thread) or 0):
            if aborted:
                return Result(host="codex", status=INTERRUPTED, session=thread, text=message, warnings=warnings,
                              transcript=str(path) if path else None,
                              extra={"app": True, "why": "the turn was stopped in the Codex app"})
            return Result(host="codex", status=FAILED if error and not message else DONE, session=thread,
                          text=message or error, model=req.model, effort=req.effort, warnings=warnings,
                          transcript=str(path) if path else None, extra={"app": True})
        time.sleep(POLL_S)
