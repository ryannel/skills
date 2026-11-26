"""Claude Code, through its documented interfaces.

  run     `claude -p --output-format stream-json`, with `--session-id` for a new session and `--resume` for an old one
          (code.claude.com/docs/en/headless). Stopped with SIGINT, never SIGTERM, which leaves the turn half written.
  send    the session's inbox socket (code.claude.com/docs/en/cross-session-messaging, "The session's inbox socket").
          Sessions the relay starts are given `crossSessionInbound: accept`, so a `-p` worker takes a message
          unattended, and a SessionStart hook that records the socket's path, since only hooks and the session's own
          commands are told it.
  open    `claude --desktop --resume <id>` once no turn is running (Claude Code 2.1.285 or later).
  status  `claude agents --json`, which lists every live session and whether it's busy.
  quota   `claude -p /usage`, which runs no model, and the `rate_limit_event` each turn prints.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import socket
import subprocess
import uuid
from pathlib import Path

from . import hosts
from .hosts import DONE, FAILED, INTERRUPTED, LIMITED, TIMEOUT, Request, Result

CLAUDE_HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")


def inbox_dir() -> Path:
    path = hosts.state_dir() / "claude-inbox"
    path.mkdir(parents=True, exist_ok=True)
    return path


def clean_env(extra: dict | None = None) -> dict:
    """The environment for a Claude run: no API key, so it uses the signed-in plan, and none of the parent session's
    variables, so a run started from inside Claude Code isn't taken for a nested session. CLAUDE_CONFIG_DIR says
    which sign-in to use and CLAUDE_CODE_OAUTH_TOKEN is the plan's own token, so both are kept."""
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("ANTHROPIC_") or k.startswith("CLAUDE"))
           or k in ("CLAUDE_CONFIG_DIR", "CLAUDE_CODE_OAUTH_TOKEN")}
    return {**env, **(extra or {})}


def session_settings(session: str) -> str:
    """The `--settings` value for a session the relay starts: take messages from other sessions unattended, and
    record the inbox socket's path where `send` can find it."""
    where = shlex.quote(str(inbox_dir() / f"{session}.sock"))
    record = f'[ -n "$CLAUDE_CODE_MESSAGING_SOCKET" ] && printf %s "$CLAUDE_CODE_MESSAGING_SOCKET" > {where} || true'
    return json.dumps({"crossSessionInbound": "accept",
                       "hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": record}]}]}})


def parse(stdout: str) -> dict:
    """What a stream-json turn reported: session, last message, model, error, limit, usage, context size, cost."""
    out = {"session": None, "text": "", "model": None, "error": False, "limited": False, "usage": {},
           "context": None, "window": None, "cost_usd": None, "limits_event": None}
    partial, last_usage = {}, None
    for event in hosts.json_lines(stdout):
        out["session"] = event.get("session_id") or out["session"]
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            out["model"] = event.get("model") or out["model"]
        elif kind == "assistant":
            message = event.get("message") or {}
            text = [c.get("text", "") for c in message.get("content") or []
                    if isinstance(c, dict) and c.get("type") == "text"]
            if any(text) and not event.get("parent_tool_use_id"):
                out["text"] = "\n".join(text)
            if isinstance(message.get("usage"), dict):
                partial[message.get("id") or len(partial)] = message["usage"]
                if not event.get("parent_tool_use_id"):  # a subagent's messages belong to its own context
                    last_usage = message["usage"]
        elif kind == "result":
            out["text"] = event.get("result") or out["text"]
            out["error"] = bool(event.get("is_error"))
            use = event.get("usage") if isinstance(event.get("usage"), dict) else None
            if use is not None:
                out["usage"] = {"input": (use.get("input_tokens") or 0) + (use.get("cache_creation_input_tokens") or 0),
                                "cached": use.get("cache_read_input_tokens") or 0,
                                "output": use.get("output_tokens") or 0}
                partial = {}
            if isinstance(event.get("total_cost_usd"), (int, float)):
                out["cost_usd"] = event["total_cost_usd"]  # list price for the whole session, not what a plan pays
            windows = [m.get("contextWindow") for m in (event.get("modelUsage") or {}).values()
                       if isinstance(m, dict) and isinstance(m.get("contextWindow"), int)]
            if windows:
                out["window"] = max(windows)
            if out["error"] and hosts.looks_limited(str(event.get("result") or "")):
                out["limited"] = True
        elif kind == "rate_limit_event":
            out["limits_event"] = event
            if str((event.get("rate_limit_info") or {}).get("status") or "").lower() == "rejected":
                out["limited"] = True
    if not out["usage"] and partial:  # stopped before its result: each finished message still reported its tokens
        out["usage"] = {"input": sum((u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
                                     for u in partial.values()),
                        "cached": sum(u.get("cache_read_input_tokens") or 0 for u in partial.values()),
                        "output": sum(u.get("output_tokens") or 0 for u in partial.values()), "incomplete": True}
    if isinstance(last_usage, dict):
        out["context"] = sum(last_usage.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens",
                                                              "cache_read_input_tokens", "output_tokens"))
    return out


def transcript(session: str) -> Path | None:
    """The session's transcript, `~/.claude/projects/<project>/<session>.jsonl` (code.claude.com/docs/en/sessions)."""
    hits = list((CLAUDE_HOME / "projects").glob(f"*/{session}.jsonl"))
    return hits[0] if hits else None


def agents(cwd: str | None = None, exe: str | None = None) -> list[dict]:
    """`claude agents --json --all`: every session Claude Code knows is live, interactive or background."""
    exe = exe or Claude().exe()
    args = [exe, "agents", "--json", "--all"] + (["--cwd", cwd] if cwd else [])
    try:
        out = subprocess.run(args, capture_output=True, text=True, timeout=30, env=clean_env())
        got = json.loads(out.stdout or "[]")
        return got if isinstance(got, list) else []
    except (OSError, subprocess.SubprocessError, ValueError):
        return []


def post(sock: str, text: str, token: str | None = None) -> str:
    """Posts `text` to an inbox socket: "" when it was taken, else why not. The auth line is documented; the
    message line's shape (`{"type": "user", "message": {...}}`) is not, and is what Claude Code 2.1.224 to 2.1.319
    accept, so it is the one experimental piece of this adapter."""
    lines = ([{"type": "auth", "token": token}] if token else []) + \
        [{"type": "user", "message": {"role": "user", "content": text}}]
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
            s.settimeout(10)
            s.connect(sock)
            s.sendall("".join(json.dumps(x) + "\n" for x in lines).encode())
        return ""
    except OSError as e:
        return f"{type(e).__name__}: {e}"


class Claude(hosts.Host):
    name = "claude"

    def exe(self) -> str:
        return os.environ.get("AGENT_RELAY_CLAUDE") or shutil.which("claude") or "claude"

    def command(self, req: Request, new_id: str | None = None) -> tuple[list[str], dict]:
        args = [self.exe(), "-p", req.prompt, "--output-format", "stream-json", "--verbose"]
        if req.model:
            args += ["--model", req.model]
        if req.effort:
            args += ["--effort", req.effort]
        if req.mode:
            args += ["--permission-mode", req.mode]
        for d in req.add_dirs:
            args += ["--add-dir", d]
        sid = req.session or new_id
        if req.session:
            args += ["--resume", req.session]
        elif new_id:
            args += ["--session-id", new_id]
        if req.name and not req.session:
            args += ["--name", req.name]
        if sid:
            args += ["--settings", session_settings(sid)]
        return args + list(req.args), clean_env(req.env)

    def run(self, req: Request, on_event=None, **hooks) -> Result:
        new_id = None if req.session else str(uuid.uuid4())
        sid = req.session or new_id
        if req.session and (busy := self.live_session(req.session)) and busy.get("pid") and \
                not hosts.live_record(self.name, req.session):
            return Result(host=self.name, status=FAILED, session=req.session,
                          text=f"the session is open in another Claude Code process (pid {busy['pid']}); "
                               "message it with `send` instead of resuming it twice")
        args, env = self.command(req, new_id)
        warnings = ["Claude Code has no documented way to show a headless session live in Desktop; it ran headless. "
                    "`open` hands the session to Desktop once its turn has ended."] if req.app else []
        on_line = _events(on_event)
        stopped = False
        try:
            run = hosts.run_process(args, req.cwd, env, req.timeout_s, on_line=on_line,
                                    on_start=lambda pid: hosts.record_run(self.name, sid, pid, req.cwd), **hooks)
        finally:
            stopped = hosts.clear_run(self.name, sid)
            try:
                (inbox_dir() / f"{sid}.sock").unlink()
            except OSError:
                pass
        got = parse(run.stdout)
        if got["limits_event"]:
            try:
                from . import quota
                quota.note_claude_event(got["limits_event"])  # each turn says how full the plan is, for free
            except Exception:
                pass
        status = _status(130 if stopped else run.code, got["error"], got["limited"], run.ended_by)
        path = transcript(got["session"] or sid)
        extra = {k: got[k] for k in ("context", "window", "cost_usd") if got[k] is not None}
        if run.ended_by:
            extra["ended_by"] = run.ended_by
        text = got["text"] or (run.stderr.strip()[-800:] if status == FAILED else "")
        return Result(host=self.name, status=status, session=got["session"] or sid, text=text, model=got["model"],
                      effort=req.effort, usage=got["usage"], warnings=warnings, transcript=str(path) if path else None,
                      exit_code=run.code, stderr=run.stderr[-2000:], stdout=run.stdout, extra=extra)

    def live_session(self, session: str) -> dict | None:
        return next((a for a in agents() if a.get("sessionId") == session), None)

    def status(self, session: str) -> Result:
        entry = self.live_session(session)
        if entry:
            busy = entry.get("status") == "busy" or entry.get("state") in ("working", "running")
            state = "busy" if busy else "idle"
            return Result(host=self.name, status=DONE, session=session, text=state,
                          extra={"state": state, **{k: entry[k] for k in ("kind", "cwd", "name", "pid", "state",
                                                                          "status", "waitingFor") if k in entry}})
        if hosts.live_record(self.name, session):
            return Result(host=self.name, status=DONE, session=session, text="busy", extra={"state": "busy"})
        state = "ended" if transcript(session) else "unknown"
        return Result(host=self.name, status=DONE, session=session, text=state, extra={"state": state})

    def send(self, session: str, text: str, socket_path: str | None = None, token: str | None = None,
             **opts) -> Result:
        """Messages a live session: one the relay started, the session this command runs inside (Claude Code exports
        its socket and token to every Bash command), or any session whose socket is given (`/status` shows it as the
        Peer address)."""
        env = os.environ
        if not socket_path and session == env.get("CLAUDE_CODE_SESSION_ID"):
            socket_path, token = env.get("CLAUDE_CODE_MESSAGING_SOCKET"), token or env.get("CLAUDE_CODE_MESSAGING_TOKEN")
        if not socket_path:
            recorded = inbox_dir() / f"{session}.sock"
            try:
                socket_path = recorded.read_text().strip() or None
            except OSError:
                socket_path = None
        if not socket_path or not Path(socket_path).exists():
            return Result(host=self.name, status=FAILED, session=session,
                          text="no inbox socket is known for this session: it has no live process (resume it with "
                               "`run --session`), or it wasn't started by the relay (pass --socket, the path "
                               "`/status` shows as the Peer address)")
        why = post(socket_path, text, token)
        if why:
            return Result(host=self.name, status=FAILED, session=session, text=f"the socket didn't take it: {why}")
        return Result(host=self.name, status=DONE, session=session, text="delivered to the session's inbox",
                      warnings=["The inbox message line's format is undocumented (experimental). A session that "
                                "bypasses permission prompts holds messages unless crossSessionInbound is accept."])

    def stop(self, session: str) -> Result:
        got = hosts.stop_recorded(self.name, session)
        if got.status == DONE or not (entry := self.live_session(session)):
            return got
        return Result(host=self.name, status=FAILED, session=session,
                      text=f"the session is live in a Claude Code process the relay didn't start ({entry.get('kind')}); "
                           "stop it there, or `send` it a message asking it to stop")

    def open(self, session: str, cwd: str | None = None) -> Result:
        entry = self.live_session(session)
        if hosts.live_record(self.name, session) or (entry and entry.get("pid")):
            return Result(host=self.name, status=FAILED, session=session,
                          text="a Claude Code process is running this session; open it in Desktop once it has ended")
        # `--desktop` refuses redirected input or output, so it gets a terminal of its own.
        out = hosts.run_in_pty([self.exe(), "--desktop", "--resume", session], cwd or (entry or {}).get("cwd"),
                               clean_env(), 60, tty_stdin=True)
        said = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", out.stdout + out.stderr).strip()
        return Result(host=self.name, status=DONE if out.code == 0 else FAILED, session=session,
                      text=said[-500:] or "opened in Claude Desktop", exit_code=out.code)

    def quota(self) -> dict:
        from . import quota
        return quota.read_claude(self.exe(), env=clean_env())

    def check(self) -> dict:
        info = super().check()
        if not info.get("installed"):
            return info
        try:
            out = subprocess.run([self.exe(), "auth", "status"], capture_output=True, text=True, timeout=30,
                                 env=clean_env())
            auth = json.loads(out.stdout)
            info["signed_in"] = bool(auth.get("loggedIn"))
            info["auth"] = {k: auth[k] for k in ("authMethod", "subscriptionType") if k in auth}
        except (OSError, subprocess.SubprocessError, ValueError, AttributeError):
            info["signed_in"] = bool(os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")) or None
        info["can"] = {"run": True, "resume": True, "stop": True, "send": True, "open": True, "status": True,
                       "app": False}
        return info


def _events(on_event):
    if not on_event:
        return None

    def on_line(line: str) -> None:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return
        if isinstance(event, dict):
            on_event(event)
    return on_line


def _status(code: int, error: bool, limited: bool, ended_by: str) -> str:
    if code == 130:
        return INTERRUPTED
    if code == 124:
        return TIMEOUT
    if limited:
        return LIMITED
    if ended_by:
        return DONE
    return FAILED if error or code != 0 else DONE
