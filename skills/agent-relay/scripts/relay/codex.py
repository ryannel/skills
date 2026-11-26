"""Codex, through its documented interfaces.

  run     `codex exec --json`, and `codex exec resume <id>` (learn.chatgpt.com/docs/non-interactive-mode). Threads it
          starts have the `exec` source, which the app's thread list leaves out by default (`thread/list`
          `sourceKinds`: "defaults to interactive sources"), so headless runs don't fill the app's Recents.
          Stopped with SIGINT.
  send    `codex queue --thread <id> --resume --message <text>`: a thread the app or the app-server daemon holds runs
          it once idle; any other thread runs it at its next resume.
  open    the `codex://threads/<id>` link, which opens the thread in the app.
  status  the relay's own run records, then the app-server's `thread/read` status and `thread/goal/get`.
  quota   the app-server's `account/rateLimits/read`, which spends nothing.

`--app` (a turn the desktop app runs and shows) has no documented route, so it lives in experimental/codex_app.py.
"""

from __future__ import annotations

import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from . import hosts
from .hosts import DONE, FAILED, INTERRUPTED, LIMITED, TIMEOUT, Request, Result

CODEX_HOME = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")
APP_BUNDLED = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"  # the CLI the macOS app ships


def codex_exe() -> str:
    return os.environ.get("AGENT_RELAY_CODEX") or shutil.which("codex") or \
        (APP_BUNDLED if Path(APP_BUNDLED).exists() else "codex")


def parse(stdout: str) -> dict:
    """What a `codex exec --json` turn reported: thread, last message, error, limit and usage."""
    out = {"session": None, "text": "", "error": "", "limited": False, "usage": {}}
    for event in hosts.json_lines(stdout):
        kind = event.get("type")
        if kind == "thread.started":
            out["session"] = event.get("thread_id") or out["session"]
        item = event.get("item") or {}
        if item.get("type") == "agent_message" and item.get("text"):
            out["text"] = item["text"]
        if kind == "turn.completed" and isinstance(event.get("usage"), dict):
            use = event["usage"]
            cached = use.get("cached_input_tokens") or 0
            out["usage"] = hosts.add_usage(out["usage"], {"input": max((use.get("input_tokens") or 0) - cached, 0),
                                                          "cached": cached, "output": use.get("output_tokens") or 0})
        elif kind in ("turn.failed", "error"):
            message = (event.get("error") or {}).get("message") if isinstance(event.get("error"), dict) else None
            out["error"] = str(message or event.get("message") or event)[:800]
            out["limited"] = out["limited"] or hosts.looks_limited(out["error"])
    return out


def rollout(thread: str) -> Path | None:
    """The thread's session file under $CODEX_HOME/sessions."""
    hits = list((CODEX_HOME / "sessions").glob(f"**/rollout-*{thread}.jsonl"))
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


class AppServer:
    """A short-lived `codex app-server` over stdio (JSON-RPC, one message per line), started by the relay for one
    job and closed after it. It reads the account and the thread store; it doesn't run turns the app is running."""

    def __init__(self, exe: str | None = None, timeout: float = 30.0):
        self.p = subprocess.Popen([exe or codex_exe(), "app-server", "--listen", "stdio://"], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q, self.n, self.notes = queue.Queue(), 0, []
        threading.Thread(target=self._read, daemon=True).start()
        try:
            self.call("initialize", {"clientInfo": {"name": "agent-relay", "title": "agent-relay", "version": "1"},
                                     "capabilities": {"experimentalApi": True}}, timeout=timeout)
            self._send({"jsonrpc": "2.0", "method": "initialized", "params": {}})
        except BaseException:
            self.close()
            raise

    def _read(self):
        for line in self.p.stdout:
            try:
                self.q.put(json.loads(line))
            except ValueError:
                pass

    def _send(self, obj):
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()

    def _note(self, m):
        if "method" in m and "id" in m:  # a request from the server, such as an approval; none is expected here
            self._send({"jsonrpc": "2.0", "id": m["id"], "error": {"code": -32601, "message": "not handled"}})
        self.notes.append(m)

    def call(self, method: str, params: dict, timeout: float = 60.0):
        self.n += 1
        rid, deadline = self.n, time.time() + timeout
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        while time.time() < deadline:
            try:
                m = self.q.get(timeout=max(0.05, min(1.0, deadline - time.time())))
            except queue.Empty:
                if self.p.poll() is not None:
                    raise RuntimeError(f"{method}: the app-server exited")
                continue
            if m.get("id") == rid and "method" not in m:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result")
            self._note(m)
        raise TimeoutError(method)

    def wait_for(self, method: str, timeout: float = 180.0) -> dict:
        deadline = time.time() + timeout
        if hit := next((m for m in self.notes if m.get("method") == method), None):
            return hit
        while time.time() < deadline:
            try:
                m = self.q.get(timeout=max(0.05, min(1.0, deadline - time.time())))
            except queue.Empty:
                continue
            self._note(m)
            if m.get("method") == method:
                return m
        raise TimeoutError(method)

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(10)
        except Exception:
            self.p.kill()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def with_server(use, default=None):
    """`use(server)` on a short-lived app-server; `default` and the error when that fails."""
    try:
        with AppServer() as srv:
            return use(srv), ""
    except (OSError, RuntimeError, TimeoutError, ValueError, KeyError, AttributeError) as e:
        return default, f"{type(e).__name__}: {e}"


QUEUE_WARNING = re.compile(r"warn|fail|error|could not|couldn't|unable", re.IGNORECASE)


class Codex(hosts.Host):
    name = "codex"

    def exe(self) -> str:
        return codex_exe()

    def command(self, req: Request) -> tuple[list[str], dict]:
        flags = []
        if req.model:
            flags += ["-m", req.model]
        if req.effort:
            flags += ["-c", f"model_reasoning_effort={req.effort}"]
        if req.mode:
            flags += ["--sandbox", req.mode]
        flags += list(req.args)
        common = ["-C", str(req.cwd)]
        for d in req.add_dirs:
            common += ["--add-dir", d]
        env = {**os.environ, **req.env}
        if req.session:
            return [self.exe(), "exec", *common, "resume", req.session, *flags, "--json", req.prompt], env
        return [self.exe(), "exec", *flags, *common, "--json", req.prompt], env

    def run(self, req: Request, on_event=None, **hooks) -> Result:
        if req.app:
            from .experimental import codex_app
            return codex_app.run(self, req, on_event=on_event, **hooks)
        args, env = self.command(req)
        seen = {"session": req.session}

        def on_line(line: str) -> None:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                return
            if not isinstance(event, dict):
                return
            if event.get("type") == "thread.started" and event.get("thread_id") and not seen["session"]:
                seen["session"] = event["thread_id"]  # recorded as soon as it's known, so `stop` can find it
                hosts.record_run(self.name, seen["session"], seen["pid"], req.cwd)
            if on_event:
                on_event(event)

        def started(pid: int) -> None:
            seen["pid"] = pid
            if req.session:
                hosts.record_run(self.name, req.session, pid, req.cwd)

        stopped = False
        try:
            run = hosts.run_process(args, req.cwd, env, req.timeout_s, on_line=on_line, on_start=started, **hooks)
        finally:
            if seen["session"]:
                stopped = hosts.clear_run(self.name, seen["session"])
        got = parse(run.stdout)
        session = got["session"] or req.session
        if run.code == 130 or stopped:
            status = INTERRUPTED
        elif run.code == 124:
            status = TIMEOUT
        elif got["limited"]:
            status = LIMITED
        elif run.ended_by:
            status = DONE
        else:
            status = FAILED if run.code != 0 or (got["error"] and not got["text"]) else DONE
        path = rollout(session) if session else None
        text = got["text"] or got["error"] or (run.stderr.strip()[-800:] if status == FAILED else "")
        return Result(host=self.name, status=status, session=session, text=text, model=req.model, effort=req.effort,
                      usage=got["usage"], transcript=str(path) if path else None, exit_code=run.code,
                      stderr=run.stderr[-2000:], stdout=run.stdout,
                      extra={"ended_by": run.ended_by} if run.ended_by else {})

    def send(self, session: str, text: str, **opts) -> Result:
        """Queues `text` as the thread's next turn. `codex queue` prints "Queued" even when its resume failed, and
        only warns, so the warning is what is read."""
        try:
            out = subprocess.run([self.exe(), "queue", "--thread", session, "--resume", "--message", text],
                                 capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError) as e:
            return Result(host=self.name, status=FAILED, session=session, text=f"codex queue didn't run: {e}")
        said = (out.stdout + out.stderr).strip()
        if out.returncode != 0:
            return Result(host=self.name, status=FAILED, session=session, text=said[-500:] or "codex queue failed",
                          exit_code=out.returncode)
        warnings = [line.strip() for line in said.splitlines() if QUEUE_WARNING.search(line)]
        if warnings:
            warnings.append("The message is queued, but nothing resumed the thread: it runs when the app or the "
                            "app-server daemon next takes the thread, or at the next `run --session`.")
        return Result(host=self.name, status=DONE, session=session, text=said[-500:] or "queued", warnings=warnings)

    def unqueue(self, session: str) -> Result:
        """Deletes the thread's queued messages, so a turn the caller gave up on can't start later unwatched."""
        def clear(srv) -> int:
            removed = 0
            for _ in range(20):
                items = (srv.call("thread/queue/list", {"threadId": session, "limit": 100}) or {}).get("data") or []
                if not items:
                    break
                for item in items:
                    got = srv.call("thread/queue/delete", {"threadId": session, "queuedSubmissionId": item["id"]})
                    removed += 1 if (got or {}).get("deleted") else 0
            return removed
        removed, why = with_server(clear)
        if removed is None:
            return Result(host=self.name, status=FAILED, session=session, text=why)
        return Result(host=self.name, status=DONE, session=session, text=f"removed {removed} queued message(s)",
                      extra={"removed": removed})

    def queued(self, session: str) -> int | None:
        got, _ = with_server(lambda srv: len((srv.call("thread/queue/list", {"threadId": session, "limit": 100})
                                              or {}).get("data") or []))
        return got

    def goal(self, session: str) -> dict | None:
        got, _ = with_server(lambda srv: (srv.call("thread/goal/get", {"threadId": session}) or {}).get("goal"))
        return got

    def set_goal(self, session: str, status: str) -> str:
        """Sets the thread's goal `active` or `paused`: "" when done, else why not."""
        _, why = with_server(lambda srv: srv.call("thread/goal/set", {"threadId": session, "status": status}))
        return why

    def open(self, session: str, **opts) -> Result:
        if sys.platform != "darwin":
            return hosts.unsupported(self.name, "the Codex app's thread links open only on macOS", session)
        ok = hosts.open_url(f"codex://threads/{session}")
        return Result(host=self.name, status=DONE if ok else FAILED, session=session,
                      text="opened in the Codex app" if ok else "the codex:// link didn't open (is the app installed?)")

    def status(self, session: str) -> Result:
        if rec := hosts.live_record(self.name, session):
            return Result(host=self.name, status=DONE, session=session, text="busy",
                          extra={"state": "busy", "pid": rec["pid"]})

        def read(srv) -> dict:
            thread = (srv.call("thread/read", {"threadId": session}) or {}).get("thread") or {}
            goal = None
            try:
                goal = (srv.call("thread/goal/get", {"threadId": session}) or {}).get("goal")
            except RuntimeError:
                pass
            return {"thread": thread, "goal": goal}
        got, why = with_server(read)
        if got is None:
            return Result(host=self.name, status=FAILED, session=session, text=why)
        kind = ((got["thread"].get("status") or {}).get("type")) or "unknown"
        # A short-lived app-server only loads threads it is asked to, so one the app is running reads `notLoaded`.
        state = {"active": "busy", "idle": "idle", "notLoaded": "unknown", "systemError": "error"}.get(kind, kind)
        extra = {"state": state, "thread_status": kind, "source": got["thread"].get("source"),
                 "name": got["thread"].get("name")}
        if got["goal"]:
            extra["goal"] = {k: got["goal"].get(k) for k in ("status", "objective", "tokensUsed", "timeUsedSeconds")}
        return Result(host=self.name, status=DONE, session=session, text=state,
                      extra={k: v for k, v in extra.items() if v is not None})

    def quota(self) -> dict:
        from . import quota
        got, why = with_server(lambda srv: quota.read_codex(lambda m, p: srv.call(m, p, timeout=20)))
        return got or {"host": "codex", "read_at": time.time(), "source": "app-server", "error": why,
                       "windows": [], "banked": []}

    def check(self) -> dict:
        info = super().check()
        if not info.get("installed"):
            return info
        try:
            out = subprocess.run([self.exe(), "login", "status"], capture_output=True, text=True, timeout=30)
            said = (out.stdout + out.stderr).strip()
            info["signed_in"] = out.returncode == 0 and "not logged in" not in said.lower()
            info["auth"] = said.splitlines()[-1] if said else ""
        except (OSError, subprocess.SubprocessError):
            info["signed_in"] = None
        info["can"] = {"run": True, "resume": True, "stop": True, "send": True, "open": sys.platform == "darwin",
                       "status": True, "app": "experimental"}
        return info
