"""Antigravity (`agy`), through its documented print mode.

  run     `agy -p --output-format stream-json`, and `--conversation <id>` to resume (antigravity.google/docs/cli/headless).
          Stopped with SIGINT, which ends the turn with status INTERRUPTED.
  quota   `agy -p /usage --output-format json`, which runs no model.

Two known agy bugs shape this adapter:

  - `--mode auto` is refused in print mode before sign-in finishes, and the run falls back to the account's default
    mode, which can be Turbo (google-antigravity/antigravity-cli#1787). The mode is passed through `--settings
    '{"agentMode": ...}'` instead, which print mode honours.
  - Two `agy -p` runs starting at once on the same data folder can corrupt a live conversation (#1884), so the relay
    lets one run start at a time, holding a lock until the new run has announced its conversation.

agy's print mode can't message, inspect or show a running conversation; its ACP server (`agy acp`) can, and is the
route a later version of this adapter would take. Until then send, status and app mode are reported as unsupported.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import threading
from pathlib import Path

from . import hosts
from .hosts import DONE, FAILED, INTERRUPTED, LIMITED, REFUSED, TIMEOUT, Request, Result

START_LOCK_S = 45.0  # the most a run holds the start lock while waiting to announce its conversation
FAILED_STATES = {"ERROR", "INVALID"}  # a result status that means the turn failed; CANCELED and INTERRUPTED are stops
DENIED = re.compile(r"(soft[- ]?denied|denied|not approved|blocked)\b.*", re.IGNORECASE)


def env_for(extra: dict | None = None) -> dict:
    """No Gemini API key or custom endpoint, so `agy` uses the signed-in plan and never bills an API account, and no
    self-update in the middle of a run."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "AGY_ADC_AUTH", "GOOGLE_GEMINI_BASE_URL",
                        "GOOGLE_APPLICATION_CREDENTIALS")}
    return {**env, "AGY_CLI_DISABLE_AUTO_UPDATE": "true", **(extra or {})}


def events(stdout: str):
    """agy's stream-json lines as (event name, payload). Each line names its event under `event` and carries the
    payload under a key of the same name; `--output-format json` prints one envelope, read as `result`."""
    for event in hosts.json_lines(stdout):
        name = event.get("event") or event.get("type")
        if not name and "conversation_id" in event and "status" in event:
            name = "result"
        body = event.get(name) if isinstance(event.get(name), dict) else event
        yield name, body


def parse(stdout: str) -> dict:
    out = {"session": None, "text": "", "model": None, "error": False, "status": None, "limited": False, "usage": {}}
    deltas = []
    for name, body in events(stdout):
        out["session"] = body.get("conversation_id") or out["session"]
        if name == "init":
            out["model"] = body.get("model") or out["model"]
        elif name == "step_update":
            if body.get("step_type") == "agent_response" and body.get("text_delta"):
                deltas.append(body["text_delta"])
            if body.get("step_type") == "agent_response" and body.get("state") == "DONE" and deltas:
                out["text"], deltas = "".join(deltas), []
        elif name == "result":
            out["status"] = str(body.get("status") or "").upper() or None
            out["text"] = body.get("response") or out["text"] or "".join(deltas)
            out["error"] = out["status"] in FAILED_STATES or bool(body.get("error"))
            if body.get("error") and not body.get("response"):
                out["text"] = str(body["error"])
            out["limited"] = out["error"] and hosts.looks_limited(str(body.get("error") or out["text"]))
            use = body.get("usage")
            if isinstance(use, dict):
                cached, given = use.get("cache_read_tokens") or 0, use.get("input_tokens") or 0
                out["usage"] = hosts.add_usage(out["usage"], {  # Gemini counts cached tokens inside the prompt
                    "input": max(given - cached, 0), "cached": cached,
                    "output": (use.get("output_tokens") or 0) + (use.get("thinking_tokens") or 0)})
    out["text"] = out["text"] or "".join(deltas)
    return out


def denials(stderr: str) -> list[str]:
    """The tool calls agy refused, from its stderr. In print mode a call that needs approval is refused without
    stopping the turn, which still exits 0, so a turn that couldn't run its tests looks like one that chose not to."""
    found = []
    for line in stderr.splitlines():
        if DENIED.search(line) and line.strip()[:200] not in found:
            found.append(line.strip()[:200])
    return found[:5]


class Antigravity(hosts.Host):
    name = "antigravity"

    def exe(self) -> str:
        return os.environ.get("AGENT_RELAY_AGY") or shutil.which("agy") or str(Path.home() / ".local/bin/agy")

    def command(self, req: Request) -> tuple[list[str], dict]:
        args = [self.exe(), "-p", req.prompt, "--output-format", "stream-json"]
        if req.model:
            args += ["--model", req.model]
        if req.effort:
            args += ["--effort", req.effort]
        for d in req.add_dirs:
            args += ["--add-dir", d]
        mode = (req.mode or "").lower()
        if mode == "skip-permissions":
            args += ["--dangerously-skip-permissions"]
        elif mode and mode != "turbo":  # turbo is agy's own default, so it needs no setting
            args += ["--settings", json.dumps({"agentMode": mode})]
        if req.session:
            args += ["--conversation", req.session]
        return args + list(req.args), env_for(req.env)

    def run(self, req: Request, on_event=None, **hooks) -> Result:
        if req.app:
            return hosts.unsupported(self.name, "agy's print mode can't run a turn in the Antigravity app; only an "
                                                "interactive session or Remote Control can show one", req.session)
        args, env = self.command(req)
        lock = hosts.FileLock("antigravity-start", timeout_s=600)
        lock.__enter__()
        announced = threading.Event()
        seen = {"session": req.session, "pid": None}

        def on_line(line: str) -> None:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                return
            if not isinstance(event, dict):
                return
            for name, body in events(line):
                cid = body.get("conversation_id")
                if cid and not announced.is_set():
                    announced.set()
                    lock.release()
                    if not seen["session"]:
                        seen["session"] = cid
                        hosts.record_run(self.name, cid, seen["pid"], req.cwd)
            if on_event:
                on_event(event)

        def started(pid: int) -> None:
            seen["pid"] = pid
            if req.session:
                hosts.record_run(self.name, req.session, pid, req.cwd)
            timer = threading.Timer(START_LOCK_S, lambda: (announced.set(), lock.release()))
            timer.daemon = True
            timer.start()

        stopped = False
        try:
            run = hosts.run_process(args, req.cwd, env, req.timeout_s, on_line=on_line, on_start=started, **hooks)
            if run.code == 0 and not run.stdout.strip():
                # agy has been reported to print nothing when stdout isn't a terminal; give it one
                run = hosts.run_in_pty(args, req.cwd, env, req.timeout_s, should_stop=hooks.get("should_stop"))
        finally:
            lock.release()
            if seen["session"]:
                stopped = hosts.clear_run(self.name, seen["session"])
        got = parse(run.stdout)
        refused = denials(run.stderr)
        if run.code == 130 or stopped or got["status"] in ("CANCELED", "CANCELLED", "INTERRUPTED"):
            status = INTERRUPTED
        elif run.code == 124:
            status = TIMEOUT
        elif got["limited"]:
            status = LIMITED
        elif got["error"] or run.code != 0:
            status = FAILED
        else:
            status = REFUSED if refused else DONE
        warnings = [f"agy refused a tool call without stopping the turn: {line}" for line in refused]
        if refused:
            warnings.append("Allow it with a `permissions.allow` rule in agy's settings.json, or run with "
                            "--mode skip-permissions.")
        text = got["text"] or (run.stderr.strip()[-800:] if status == FAILED else "")
        return Result(host=self.name, status=status, session=got["session"] or req.session, text=text,
                      model=got["model"] or req.model, effort=req.effort, usage=got["usage"], warnings=warnings,
                      exit_code=run.code, stderr=run.stderr[-2000:], stdout=run.stdout,
                      extra={"refused": refused} if refused else {})

    def send(self, session: str, text: str, **opts) -> Result:
        return hosts.unsupported(self.name, "agy's print mode has no way to message a conversation; resume it with "
                                            "`run --session`, which starts a new turn on it", session)

    def status(self, session: str) -> Result:
        got = super().status(session)
        if got.text == "unknown":
            got.warnings.append("agy reports a conversation's state only through its ACP server; the relay knows "
                                "only the turns it started itself")
        return got

    def open(self, session: str, **opts) -> Result:
        return hosts.unsupported(self.name, "agy has no link that opens a print-mode conversation in the app", session)

    def quota(self) -> dict:
        from . import quota
        return quota.read_agy(self.exe(), env=env_for())

    def check(self) -> dict:
        info = super().check()
        if info.get("installed"):
            info["can"] = {"run": True, "resume": True, "stop": True, "send": False, "open": False,
                           "status": "own runs", "app": False}
        return info
