#!/usr/bin/env python3
"""Run one Codex generator on one milestone of the orchestrate process, with model and effort pinned, until a stop
rule fires.

Used by the build-parallel lead and runnable by hand. Project settings come from ORCHESTRATE.md at the worktree root
(`profile` prints what was read). Needs git and the Codex CLI; POSIX only (fcntl).
The goal-status and quota readers use Codex's local session files and work on a ChatGPT-plan login; without them those
stop rules and the forecast are skipped. Subcommands:

  run   --module ONBOARDING --worktree PATH [--milestone M2] [--fresh] [--message TEXT] [--budget-hours 4]
        Starts (or resumes) a Codex session on the milestone and drives it one turn per `codex exec resume` until:
        CLAIMED   every item passes in the committed done-when file, the tree is clean, the work is on the base branch,
                  and every oracle item's check exits 0 when the loop
                  runs it. A failing check goes back to the generator instead.
        DONE / BLOCKED / NEEDS_CONTEXT   the agent's final report line
        BUDGET    no new passing item or commit for --budget-hours
        FLOOR     two failed turns in a row, or the goal is usage- or budget-limited (likely quota or outage)
        PIN       a turn ran on a model or effort other than the pinned ones
        PAUSED    the goal is paused; only the Codex app's play button resumes it
        A run on the same milestone resumes its session (with --message as the first prompt, e.g. the evaluator's
        findings) unless --fresh is given; with --fresh, --message is added to the new goal.
        Prints one JSON line with the result and the quota forecast as the last line of output.
        The owner sets the pace by how many streams run; the loop never holds work back for quota.

  next  --module ONBOARDING --worktree PATH --milestone M2
        Reads the milestone's `fails` (written by the evaluator) and `replans` (written by the planner) and prints the
        escalation: same-session (1-2 fails), fresh-session (3), replan (4+ with no re-plan yet), park (4+ after a
        re-plan), or none (0), with the message to pass on.

  status --module ONBOARDING --worktree PATH
        Prints each milestone's state, fails and passing items.

  quota
        Forecasts the weekly Codex limit from the last day of use across all sessions: used %, burn per day, and
        when it runs out compared with the reset.

  profile --worktree PATH
        Prints the settings read from ORCHESTRATE.md, or exits 1 naming the fields that are unfilled or invalid.

  lock NAME [--worktree PATH] -- COMMAND...
        Runs COMMAND under a named lock shared by every worktree of the repository, so runs that need an exclusive
        resource (a device, a fixed port, a simulator, a GPU for timing) never overlap across parallel streams.

State lives in <git dir>/orchestrate/<module>.json for the worktree, so re-running the same command resumes.
"""

from __future__ import annotations

from datetime import datetime, timezone

import argparse
import fcntl
import glob
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_MODEL = "gpt-6.1-sol"
DEFAULT_EFFORT = "medium"
CODEX = os.environ.get("ORCHESTRATE_CODEX") or shutil.which("codex") or \
    "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
REPORT_WORDS = ("DONE", "BLOCKED", "NEEDS_CONTEXT")

LOOP = Path(__file__).resolve()

GOAL_TEMPLATE = """Model {model}, effort {effort}. Call your create_goal tool with this objective, then work it:

Milestone {milestone} of module {module} is done: every item for {milestone} in {plans}/{module}-DONE.json has status \
pass with evidence on its named target, and the change is on the profile's branch, with its check passing fresh on the \
integrated tip. Use $build-milestone, which covers method, constraints and \
permissions. Work only in this worktree. Keep the plan's status lines and log current. If you are blocked (probed \
directly) or missing context, stop and end with `BLOCKED: ...` or `NEEDS_CONTEXT: ...` and the evidence. When finished, \
end with `DONE` and the evidence. Commit the done-when file with the work. Don't launch the evaluator: the lead runs \
review. Take exclusive resources with `python3 {loop} lock <name> -- <command>`."""

FINDINGS_TEMPLATE = """The evaluator failed {milestone}: see {evidence}/{module_lower}/{milestone}-review.md. Add its \
findings to the plan as work items, fix them, re-verify the affected items, integrate, and end with DONE, BLOCKED or \
NEEDS_CONTEXT."""


PROFILE_DEFAULTS = {"plans": "docs/modules", "evidence": "docs/evidence", "branch": "main",
                    "remote": "origin", "sandbox": "workspace-write", "writable roots": ""}
ALLOWED = {"sandbox": {"workspace-write", "danger-full-access"}}


def profile(worktree: Path, strict: bool = False) -> dict:
    """Reads the loop's settings from ORCHESTRATE.md (`- **Label:** value` lines). Missing labels take defaults;
    unfilled or invalid values raise SystemExit when strict, and fall back to defaults with a warning otherwise."""
    path = worktree / "ORCHESTRATE.md"
    text = path.read_text() if path.exists() else ""
    out, problems = {}, []
    for key, default in PROFILE_DEFAULTS.items():
        m = re.search(rf"\*\*{re.escape(key)}:\*\*[ \t]*(.*)", text, re.IGNORECASE)
        raw = m.group(1) if m else ""
        raw = re.sub(r"\*\(.*?\)\*", "", raw)                 # trailing *(read by the loop)* notes
        raw = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw)  # markdown links keep their text
        value = raw.replace("`", "").strip()
        if key != "writable roots":
            value = value.split()[0] if value else ""
        if not value:
            out[key] = default
        elif "<" in value or (key in ALLOWED and value not in ALLOWED[key]):
            problems.append(f"{key}: {value!r}")
            out[key] = default
        else:
            out[key] = value.rstrip("/") if key in ("plans", "evidence") else value
    model = re.search(r"\*\*Codex generator:\*\*[ \t]*`?([\w.\-]+)`?[ ,]+`?(\w+)", text)
    out["model"], out["effort"] = (model.group(1), model.group(2)) if model else (DEFAULT_MODEL, DEFAULT_EFFORT)
    out["roots"] = [r.strip() for r in out.pop("writable roots").split(",") if r.strip()]
    if problems:
        message = "ORCHESTRATE.md has unfilled or invalid fields: " + "; ".join(problems)
        if strict:
            raise SystemExit(message)
        print("warning: " + message, file=sys.stderr)
    return out


def codex_flags(prof: dict) -> list[str]:
    flags = ["-m", prof["model"], "-c", f"model_reasoning_effort={prof['effort']}",
             "-c", "approval_policy=on-request", "-c", "approvals_reviewer=auto_review",
             "-c", f"sandbox_mode={prof['sandbox']}"]
    if prof["sandbox"] == "workspace-write":
        flags += ["-c", "sandbox_workspace_write.network_access=true"]
        if prof["roots"]:
            roots = ",".join(json.dumps(str(Path(r).expanduser())) for r in prof["roots"])
            flags += ["-c", f"sandbox_workspace_write.writable_roots=[{roots}]"]
    return flags


def codex_supports(flag: str) -> bool:
    out = subprocess.run([CODEX, "exec", "--help"], capture_output=True, text=True)
    return flag in out.stdout


def load_done(worktree: Path, module: str) -> dict:
    path = worktree / profile(worktree)["plans"] / f"{module}-DONE.json"
    return json.loads(path.read_text())


def pick_milestone(done: dict, wanted: str | None) -> dict:
    milestones = done["milestones"]
    if wanted:
        for m in milestones:
            if m["id"] == wanted:
                if m.get("state") in ("done", "parked"):
                    print(f"warning: {wanted} is {m['state']}", file=sys.stderr)
                return m
        raise SystemExit(f"error: milestone {wanted} not in done-when file")
    for state in ("in_progress", "open"):
        for m in milestones:
            closed_by_oracle = not m.get("review") and passing(m) == len(m["items"])
            if m.get("state") == state and not closed_by_oracle:
                return m
    raise SystemExit("error: no open milestone")


def passing(milestone: dict) -> int:
    return sum(1 for item in milestone["items"] if item.get("status") == "pass")


def escalation(fails: int, replans: int = 0) -> str:
    if fails <= 0:
        return "none"
    if fails <= 2:
        return "same-session"
    if fails == 3:
        return "fresh-session"
    return "replan" if replans == 0 else "park"


def rollout_for(thread_id: str) -> Path | None:
    hits = glob.glob(str(CODEX_HOME / "sessions" / "**" / f"rollout-*{thread_id}.jsonl"), recursive=True)
    return Path(max(hits, key=os.path.getmtime)) if hits else None


def pin_mismatches(rollout: Path, model_pin: str = DEFAULT_MODEL, effort_pin: str = DEFAULT_EFFORT) -> list[str]:
    bad = []
    for line in rollout.read_text().splitlines():
        if '"turn_context"' not in line:
            continue
        payload = json.loads(line).get("payload", {})
        model, effort = payload.get("model"), payload.get("effort")
        if (model, effort) != (model_pin, effort_pin):
            bad.append(f"{payload.get('turn_id')}: {model}/{effort}")
    return bad


def quota_samples(since: float) -> list[tuple[float, float, float]]:
    """(time, used_percent, resets_at) for the weekly Codex limit, from rollouts touched since `since`."""
    samples = []
    for f in glob.glob(str(CODEX_HOME / "sessions" / "**" / "rollout-*.jsonl"), recursive=True):
        if os.path.getmtime(f) < since:
            continue
        with open(f) as handle:
            for line in handle:
                if '"token_count"' not in line:
                    continue
                event = json.loads(line)
                limits = event.get("payload", {}).get("rate_limits") or {}
                primary = limits.get("primary") or {}
                if limits.get("limit_id") != "codex" or primary.get("window_minutes") != 10080:
                    continue
                when = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).timestamp()
                samples.append((when, float(primary["used_percent"]), float(primary["resets_at"])))
    return sorted(samples)


def forecast(samples: list[tuple[float, float, float]], now: float, window_h: float = 24.0) -> dict | None:
    """Burn rate over the last `window_h` hours of the current limit window, and when the limit runs out at that rate."""
    if not samples:
        return None
    _, used, resets_at = samples[-1]
    recent = [s for s in samples if s[2] == resets_at and s[0] >= now - window_h * 3600]
    out = {"used_percent": used, "resets_at": iso(resets_at)}
    if len(recent) < 2 or recent[-1][0] - recent[0][0] < 3600:
        return {**out, "per_day": None, "runs_out": None, "note": "not enough recent use to forecast"}
    per_day = (recent[-1][1] - recent[0][1]) / ((recent[-1][0] - recent[0][0]) / 86400)
    out["per_day"] = round(per_day, 1)
    if per_day <= 0:
        return {**out, "runs_out": None, "note": "no use in the window"}
    runs_out = now + (100 - used) / per_day * 86400
    if runs_out >= resets_at:
        return {**out, "runs_out": None, "note": f"lasts to the reset at this rate ({round(100 - used - per_day * (resets_at - now) / 86400)}% left then)"}
    return {**out, "runs_out": iso(runs_out),
            "note": f"runs out {round((resets_at - runs_out) / 3600)} h before the reset at this rate"}


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).astimezone().strftime("%a %d %b %H:%M")


def quota_now() -> dict | None:
    now = time.time()
    return forecast(quota_samples(now - 26 * 3600), now)


def goal_status(thread_id: str) -> str | None:
    db = CODEX_HOME / "goals_1.sqlite"
    if not db.exists():
        return None
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
        row = conn.execute("select status from thread_goals where thread_id=?", (thread_id,)).fetchone()
    return row[0] if row else None


def head_commit(worktree: Path) -> str:
    return subprocess.run(["git", "-C", str(worktree), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()


def integration(worktree: Path, prof: dict) -> tuple[bool, str]:
    """Whether the committed work is integrated: a clean tree whose HEAD is on <remote>/<branch>."""
    git = ["git", "-C", str(worktree)]
    if subprocess.run([*git, "status", "--porcelain", "--untracked-files=no"], capture_output=True,
                      text=True).stdout.strip():
        return False, "uncommitted changes"
    subprocess.run([*git, "fetch", "--quiet", prof["remote"]], capture_output=True)
    base = f"{prof['remote']}/{prof['branch']}"
    ok = subprocess.run([*git, "merge-base", "--is-ancestor", "HEAD", base], capture_output=True).returncode == 0
    return ok, base if ok else f"HEAD is not on {base}"


def oracle_failures(worktree: Path, milestone: dict, timeout_s: float = 3600) -> list[str]:
    """Runs each oracle item's check in the worktree; returns the failing items with the tail of their output."""
    failed = []
    for item in milestone["items"]:
        if item.get("proof") != "oracle" or not item.get("check"):
            continue
        try:
            run = subprocess.run(item["check"], shell=True, cwd=worktree, capture_output=True, text=True,
                                 timeout=timeout_s)
            if run.returncode != 0:
                failed.append(f"{item['id']} `{item['check']}` exited {run.returncode}: {(run.stdout + run.stderr)[-600:]}")
        except subprocess.TimeoutExpired:
            failed.append(f"{item['id']} `{item['check']}` timed out")
    return failed


def git_common_dir(worktree: Path) -> str:
    out = subprocess.run(["git", "-C", str(worktree), "rev-parse", "--git-common-dir"], capture_output=True, text=True)
    return str((worktree / out.stdout.strip()).resolve())


def run_turn(args: list[str], timeout_s: float) -> tuple[int, str | None, str]:
    """Runs one codex exec call; returns (exit code, thread id, last agent message). A timeout counts as failed."""
    try:
        proc = subprocess.run([CODEX, *args], capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=timeout_s)
        code, stdout = proc.returncode, proc.stdout
    except subprocess.TimeoutExpired as e:
        code, stdout = 124, e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
    thread_id, last_message = None, ""
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "thread.started":
            thread_id = event.get("thread_id")
        item = event.get("item") or {}
        if item.get("type") == "agent_message" and item.get("text"):
            last_message = item["text"]
    return code, thread_id, last_message


def report_word(message: str) -> str | None:
    for line in reversed([l.strip() for l in message.splitlines() if l.strip()]):
        word = line.split(":")[0].strip("`* ")
        if word in REPORT_WORDS:
            return word
    return None


def finish(state_path: Path, state: dict, result: str, **extra) -> None:
    state.update(result=result, finished=time.time(), **extra)
    state_path.write_text(json.dumps(state, indent=2))
    print(json.dumps({"result": result, "module": state["module"], "milestone": state["milestone"],
                      "thread": state.get("thread"), **extra, "quota": quota_now()}))
    sys.exit(0)


def cmd_run(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    git_dir = subprocess.run(["git", "-C", str(worktree), "rev-parse", "--absolute-git-dir"],
                             capture_output=True, text=True).stdout.strip()
    state_dir = Path(git_dir) / "orchestrate"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{a.module}.json"
    prof = profile(worktree, strict=True)
    milestone = pick_milestone(load_done(worktree, a.module), a.milestone)
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    fresh = a.fresh or state.get("milestone") != milestone["id"] or state.get("result") == "PIN"
    if fresh:
        state = {"module": a.module, "milestone": milestone["id"], "thread": None, "turns": 0}
    # Every run starts its own counters, so a resume after BUDGET or a failed review isn't judged on old progress.
    state.update(module=a.module, milestone=milestone["id"], failed_turns=0, reports=0, progress_at=time.time(),
                 passing=passing(milestone), head=head_commit(worktree))
    state.pop("result", None)
    flags = codex_flags(prof)
    source = ["--thread-source", "vscode"] if codex_supports("--thread-source") else []
    timeout_s = a.turn_timeout_hours * 3600

    while True:
        if state.get("thread") is None:
            prompt = GOAL_TEMPLATE.format(model=prof["model"], effort=prof["effort"], milestone=milestone["id"],
                                          module=a.module, plans=prof["plans"], loop=LOOP)
            if a.message:
                prompt += "\n\n" + a.message
                a.message = None
            code, thread_id, message = run_turn(["exec", *flags, "--add-dir", git_common_dir(worktree),
                                                 *source, "-C", str(worktree), "--json", prompt],
                                                timeout_s)
            state["thread"] = thread_id
        else:
            prompt = a.message or "Continue the goal."
            a.message = None
            code, _, message = run_turn(["exec", "resume", state["thread"], *flags, "--json", prompt], timeout_s)
        state["turns"] += 1
        state["failed_turns"] = state["failed_turns"] + 1 if code != 0 else 0
        state_path.write_text(json.dumps(state, indent=2))

        if state["thread"] is None or state["failed_turns"] >= 2:
            finish(state_path, state, "FLOOR", reason="two failed turns or no thread; likely quota or outage")
        rollout = rollout_for(state["thread"])
        if rollout and (bad := pin_mismatches(rollout, prof["model"], prof["effort"])):
            finish(state_path, state, "PIN", mismatches=bad[:5])
        status = goal_status(state["thread"])
        if status in ("usage_limited", "budget_limited"):
            finish(state_path, state, "FLOOR", reason=f"goal {status}")
        if status == "paused":
            finish(state_path, state, "PAUSED")

        current = pick_milestone(load_done(worktree, a.module), milestone["id"])
        now_passing, head = passing(current), head_commit(worktree)
        if now_passing > state["passing"] or head != state["head"]:
            state.update(progress_at=time.time(), passing=now_passing, head=head)
        if now_passing == len(current["items"]):
            ok, detail = integration(worktree, prof)
            failures = oracle_failures(worktree, current) if ok else []
            if ok and not failures:
                finish(state_path, state, "CLAIMED", review=bool(current.get("review")), integrated=detail)
            # Not claimable yet: tell the generator why on its next turn rather than stopping.
            state["claim_blocked"] = "; ".join(failures) if failures else detail
            a.message = f"The loop can't accept the claim yet: {state['claim_blocked']}. Fix it, then end with DONE."
            message = ""
        word = report_word(message)
        state["reports"] = state.get("reports", 0) + 1 if word else 0
        if word and (status != "active" or state["reports"] >= 2):
            finish(state_path, state, word, report=message[-1500:])
        if status in ("complete", "blocked"):
            finish(state_path, state, "BLOCKED" if status == "blocked" else "DONE", report=message[-1500:])
        if time.time() - state["progress_at"] > a.budget_hours * 3600:
            finish(state_path, state, "BUDGET", hours=a.budget_hours)


def cmd_next(a: argparse.Namespace) -> None:
    milestone = pick_milestone(load_done(Path(a.worktree), a.module), a.milestone)
    fails, replans = int(milestone.get("fails", 0)), int(milestone.get("replans", 0))
    message = FINDINGS_TEMPLATE.format(milestone=milestone["id"], module_lower=a.module.lower(),
                                       evidence=profile(Path(a.worktree))["evidence"])
    print(json.dumps({"milestone": milestone["id"], "fails": fails, "replans": replans,
                      "action": escalation(fails, replans), "message": message}))


def cmd_profile(a: argparse.Namespace) -> None:
    print(json.dumps(profile(Path(a.worktree).resolve(), strict=True), indent=2))


def cmd_status(a: argparse.Namespace) -> None:
    for m in load_done(Path(a.worktree), a.module)["milestones"]:
        print(f"{m['id']}\t{m.get('state')}\tfails={m.get('fails', 0)}\t{passing(m)}/{len(m['items'])} pass\t{m['name']}")


def cmd_quota(a: argparse.Namespace) -> None:
    print(json.dumps(quota_now()))


def cmd_lock(a: argparse.Namespace) -> None:
    command = a.command_args[1:] if a.command_args[:1] == ["--"] else a.command_args
    if not command or not re.fullmatch(r"[\w.-]+", a.name):
        raise SystemExit("error: usage: lock NAME -- COMMAND...")
    where = Path(a.worktree or Path.cwd()).resolve()
    if subprocess.run(["git", "-C", str(where), "rev-parse"], capture_output=True).returncode != 0:
        raise SystemExit(f"error: {where} is not in a git repository, so there is no shared lock location")
    lock = Path(git_common_dir(where)) / f"orchestrate-{a.name}.lock"
    with open(lock, "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        sys.exit(subprocess.run(command).returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("--module", required=True)
    run.add_argument("--worktree", required=True)
    run.add_argument("--milestone")
    run.add_argument("--fresh", action="store_true", help="start a new Codex session even if one exists")
    run.add_argument("--message", help="first prompt on resume, e.g. the evaluator's findings message")
    run.add_argument("--budget-hours", type=float, default=4.0)
    run.add_argument("--turn-timeout-hours", type=float, default=2.0)
    run.set_defaults(func=cmd_run)
    for name, func in (("next", cmd_next), ("status", cmd_status)):
        p = sub.add_parser(name)
        p.add_argument("--module", required=True)
        p.add_argument("--worktree", required=True)
        if name == "next":
            p.add_argument("--milestone", required=True)
        p.set_defaults(func=func)
    sub.add_parser("quota").set_defaults(func=cmd_quota)
    prof = sub.add_parser("profile")
    prof.add_argument("--worktree", default=".")
    prof.set_defaults(func=cmd_profile)
    lock = sub.add_parser("lock")
    lock.add_argument("name")
    lock.add_argument("--worktree")
    lock.add_argument("command_args", nargs=argparse.REMAINDER)
    lock.set_defaults(func=cmd_lock)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
