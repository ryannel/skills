#!/usr/bin/env python3
"""agent-relay: drive Claude Code, Codex and Antigravity from one command line.

Every command takes --host (claude, codex or antigravity) and prints one JSON result:

  {"host", "status", "session", "text", "model", "effort", "usage", "warnings", "transcript", ...}

status is done, failed, interrupted, timeout, limited (a usage limit stopped it), refused (the turn finished but
the host refused a tool call) or unsupported (the host has no route for this; text says why).

Each host's own CLI does the work, through its documented interfaces; see SKILL.md for what each host can do and
README.md for what is experimental. Python 3.10+, standard library only.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from relay import __version__, hosts, models, quota  # noqa: E402

FRESH_S = 10 * 60.0  # a stored quota reading younger than this is shown without asking the host again


def emit(obj, code: int = 0) -> None:
    print(json.dumps(obj, indent=2, default=str))
    sys.exit(code)


def result_code(r: hosts.Result) -> int:
    return 0 if r.status in (hosts.DONE, hosts.REFUSED) else 2 if r.status == hosts.UNSUPPORTED else 1


def read_prompt(value: str) -> str:
    if value == "-":
        return sys.stdin.read()
    if value.startswith("@") and Path(value[1:]).is_file():
        return Path(value[1:]).read_text()
    return value


def cmd_run(a) -> None:
    host = hosts.get(a.host)
    req = hosts.Request(prompt=read_prompt(a.prompt), cwd=str(Path(a.cwd).resolve()), model=a.model,
                        effort=a.effort, session=a.session, mode=a.mode, name=a.name,
                        add_dirs=[str(Path(d).resolve()) for d in a.add_dir], args=a.arg,
                        timeout_s=a.timeout * 60, app=a.app)
    on_event = (lambda e: print(json.dumps(e), file=sys.stderr, flush=True)) if a.stream else None
    r = host.run(req, on_event=on_event)
    if r.status == hosts.FAILED and (note := hosts.sandbox_note()):
        r.warnings.append(note)
    emit(r.to_json(with_output=a.raw), result_code(r))


def cmd_stop(a) -> None:
    r = hosts.get(a.host).stop(a.session)
    emit(r.to_json(), result_code(r))


def cmd_send(a) -> None:
    host = hosts.get(a.host)
    opts = {}
    if a.socket:
        opts["socket_path"] = a.socket
    if a.token:
        opts["token"] = a.token
    r = host.send(a.session, read_prompt(a.text), **opts)
    emit(r.to_json(), result_code(r))


def cmd_open(a) -> None:
    host = hosts.get(a.host)
    r = host.open(a.session, **({"cwd": a.cwd} if a.cwd and a.host == "claude" else {}))
    emit(r.to_json(), result_code(r))


def cmd_status(a) -> None:
    r = hosts.get(a.host).status(a.session)
    emit(r.to_json(), result_code(r))


def reading(name: str, refresh: bool) -> dict | None:
    stored = quota.latest(name)
    if not refresh and stored and time.time() - (stored.get("read_at") or 0) < FRESH_S:
        return stored
    host = hosts.get(name)
    if not host.installed():
        return stored
    got = host.quota()
    if got and (got.get("windows") or got.get("banked")):
        return quota.record(got)
    return {**stored, "error": (got or {}).get("error"), "stale": True} if stored else got


def cmd_quota(a) -> None:
    views = []
    for name in ([a.host] if a.host else hosts.HOSTS):
        try:
            view = quota.summary(reading(name, a.refresh))
        except Exception as e:  # one host failing shouldn't hide the others
            view = {"host": name, "error": str(e)[:200], "windows": [], "plans": []}
        views.append(view or {"host": name, "windows": [], "plans": [], "error": "no reading"})
    if a.json:
        emit(views)
    lines = []
    for v in views:
        head = v["host"] + (f" ({v['plan']})" if v.get("plan") else "")
        if not v.get("windows"):
            lines.append(f"{head}: no reading" + (f" ({v['error']})" if v.get("error") else ""))
            continue
        parts = []
        for w in v["windows"]:
            text = f"{w.get('label')} {w.get('used_pct', 0):.0f}% used, resets {quota.when_text(w.get('resets_at'))}"
            if w.get("left_at_reset_pct") is not None:
                text += f", about {w['left_at_reset_pct']:.0f}% unused then at {w.get('pct_per_hour')}%/h"
            parts.append(text)
        lines.append(f"{head}, read {round((v.get('age_s') or 0) / 60)} min ago: " + "; ".join(parts))
        for p in v.get("plans") or []:
            lines.append(f"  banked reset: {p['say']}")
    lines.append("\nagent-relay never redeems a banked reset; that is yours to do, in the host's own app.")
    print("\n".join(lines))


def cmd_models(a) -> None:
    cat = models.catalogue()
    chosen = [m for m in cat["models"] if not a.host or m.get("host") == hosts.get(a.host).name]
    if a.json:
        emit({"checked": cat["checked"], "models": [{**m, "price_now": models.price_now(m)} for m in chosen]})
    print(models.text(chosen, cat["checked"]))


def cmd_check(a) -> None:
    out = [hosts.get(name).check() for name in ([a.host] if a.host else hosts.HOSTS)]
    emit(out[0] if a.host else out)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="relay.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter,
                                epilog="Run `relay.py <command> --help` for each command's options.")
    p.add_argument("--version", action="version", version=f"agent-relay {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    def with_host(sp, required=True):
        sp.add_argument("--host", required=required, choices=["claude", "codex", "antigravity", "agy"],
                        help="which agent CLI to drive")

    r = sub.add_parser("run", help="run one turn: a new session, or --session to resume one")
    with_host(r)
    r.add_argument("prompt", help="the prompt; - reads it from stdin, @file reads a file")
    r.add_argument("--cwd", default=".", help="the folder the agent works in (default: here)")
    r.add_argument("--session", help="resume this session instead of starting a new one")
    r.add_argument("--model", help="the host's model ID (see `models`)")
    r.add_argument("--effort", help="reasoning effort, as the host names it (low, medium, high, xhigh, max)")
    r.add_argument("--mode", help="the host's permission setting: Claude's --permission-mode, Codex's --sandbox, "
                                  "or Antigravity's agent mode (auto, accept-edits, plan, turbo, skip-permissions)")
    r.add_argument("--name", help="a title for a new session, where the host takes one")
    r.add_argument("--add-dir", action="append", default=[], help="another folder the agent may use (repeatable)")
    r.add_argument("--arg", action="append", default=[], help="an extra flag for the host CLI, as is (repeatable; "
                                                              "use --arg=-c --arg=key=value for a pair)")
    r.add_argument("--timeout", type=float, default=240, help="minutes before the turn is stopped (default 240)")
    r.add_argument("--app", action="store_true", help="run it where the host's desktop app shows it (Codex only, "
                                                      "experimental)")
    r.add_argument("--stream", action="store_true", help="print the host's events to stderr as they arrive")
    r.add_argument("--raw", action="store_true", help="include the host CLI's whole output in the result")
    r.set_defaults(fn=cmd_run)

    s = sub.add_parser("stop", help="stop a running turn the relay started (SIGINT, as Ctrl-C would)")
    with_host(s)
    s.add_argument("--session", required=True)
    s.set_defaults(fn=cmd_stop)

    m = sub.add_parser("send", help="message a session: a live Claude session's inbox, or a Codex thread's queue")
    with_host(m)
    m.add_argument("--session", required=True)
    m.add_argument("text", help="the message; - reads it from stdin, @file reads a file")
    m.add_argument("--socket", help="Claude: the session's inbox socket, for one the relay didn't start "
                                    "(`/status` shows it as the Peer address)")
    m.add_argument("--token", help="Claude: the session's CLAUDE_CODE_MESSAGING_TOKEN, if it has one")
    m.set_defaults(fn=cmd_send)

    o = sub.add_parser("open", help="show a session in the host's desktop app")
    with_host(o)
    o.add_argument("--session", required=True)
    o.add_argument("--cwd", help="Claude: the session's folder, if it isn't live")
    o.set_defaults(fn=cmd_open)

    st = sub.add_parser("status", help="whether a session is busy, idle, ended or unknown")
    with_host(st)
    st.add_argument("--session", required=True)
    st.set_defaults(fn=cmd_status)

    q = sub.add_parser("quota", help="usage windows, banked resets and a plan for each reset (never redeems one)")
    with_host(q, required=False)
    q.add_argument("--refresh", action="store_true", help="ask the host now, even with a reading under 10 minutes")
    q.add_argument("--json", action="store_true")
    q.set_defaults(fn=cmd_quota)

    md = sub.add_parser("models", help="the model catalogue: IDs, efforts, list prices, retirements")
    with_host(md, required=False)
    md.add_argument("--json", action="store_true")
    md.set_defaults(fn=cmd_models)

    c = sub.add_parser("check", help="whether each host's CLI is installed and signed in, and what it can do")
    with_host(c, required=False)
    c.set_defaults(fn=cmd_check)

    a = p.parse_args(argv)
    try:
        a.fn(a)
    except ValueError as e:
        emit({"status": "failed", "text": str(e)}, 1)


if __name__ == "__main__":
    main()
