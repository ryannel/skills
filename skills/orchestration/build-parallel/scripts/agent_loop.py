#!/usr/bin/env python3
"""Run one Codex generator on one milestone of the orchestrate process, with model and effort pinned, until a stop
rule fires.

Used by the build-parallel lead and runnable by hand. Project settings come from ORCHESTRATE.md at the worktree root
(`profile` prints what was read). Needs git and the Codex CLI; POSIX only (fcntl, process groups).

The loop runs checks with your own permissions, outside Codex's sandbox. It pins the check strings to the planner's
revision, but a script a check calls can still be changed by the builder, so review new check scripts.

The goal-status and quota readers use Codex's local files (goals_1.sqlite and session rollouts) on a ChatGPT-plan
login. Whether `codex exec` creates a goal row hasn't been confirmed; without one, the goal-based stop rules are
skipped and the rest still apply. Subcommands:

  run   --module ONBOARDING --worktree PATH [--milestone M2] [--fresh] [--message TEXT] [--budget-hours 4]
        Starts (or resumes) a Codex session on the milestone and drives it one turn at a time until:
        CLAIMED       the claim holds: the done-when file is valid and its acceptance definitions are unchanged, the
                      milestone's state is `claimed` (or `done` when it needs no review), every item is `pass` with
                      evidence, the tree is clean with no untracked files, HEAD is on the base branch, and the
                      profile's Check and every item's `check` exit 0 when the loop runs them. Anything short of that
                      goes back to the generator with the reasons. `review` says whether the evaluator must judge it,
                      and `commit` is the commit to review.
        BLOCKED / NEEDS_CONTEXT   the agent's final report line
        UNCLAIMED     the agent said DONE (or its goal completed) three times without a claim that holds
        INVALID       the done-when file is malformed, or its acceptance definitions changed during the run
        REVIEW_OWED   an earlier milestone is claimed and waiting for the evaluator (only without --milestone)
        BUDGET        no new passing item or commit outside the plans folder for --budget-hours
        FLOOR         two failed turns in a row, or the goal is usage- or budget-limited (likely quota or outage)
        PIN           a turn ran on a model or effort other than the pinned ones
        PAUSED        the goal is paused; resume it from the Codex app or with /goal resume
        A run on the same milestone resumes its session (with --message as the first prompt, e.g. the evaluator's
        findings) unless --fresh is given or the profile's model or effort changed.
        Prints one JSON line with the result and the quota forecast as the last line of output.
        The owner sets the pace by how many streams run; the loop never holds work back for quota.

  next  --module ONBOARDING --worktree PATH --milestone M2
        Reads the milestone's `fails` (written by the evaluator) and `replans` (written by the planner) and prints the
        escalation: same-session (1-2 fails), fresh-session (3), replan (4+ with no re-plan yet), park (4+ after a
        re-plan), or none (0), with the message to pass on.

  status --module ONBOARDING --worktree PATH
        Prints each milestone's state, fails and passing items, and flags milestones waiting for review.

  quota
        Forecasts the weekly Codex limit from the last day of use across all sessions.

  profile --worktree PATH
        Prints the settings read from ORCHESTRATE.md, or exits 1 naming the fields that are missing, unfilled or invalid.

  lock [--worktree PATH] NAME -- COMMAND...
        Runs COMMAND (in PATH, if given) under a named lock shared by every worktree of the repository, so runs that
        need an exclusive resource never overlap across parallel streams. The lock covers one repository, not the
        whole machine. Items can name a lock with "lock": NAME, and the loop takes it when it reruns their check.

State lives in <git dir>/orchestrate/<module>.json for the worktree, so re-running the same command resumes.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import argparse
import fcntl
import glob
import hashlib
import json
import os
import re
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_MODEL = "gpt-6.1-sol"
DEFAULT_EFFORT = "medium"
EFFORTS = {"low", "medium", "high", "xhigh"}
CODEX = os.environ.get("ORCHESTRATE_CODEX") or shutil.which("codex") or \
    "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
REPORT_WORDS = ("DONE", "BLOCKED", "NEEDS_CONTEXT")
STATES = {"open", "in_progress", "claimed", "done", "parked"}
STATUSES = {"open", "pass"}
VERDICTS = {"", "pass", "fail", "cant_tell"}
DEFINITION_KEYS = ("statement", "check", "inspect", "ask", "target", "lock")

LOOP = Path(__file__).resolve()

GOAL_TEMPLATE = """Model {model}, effort {effort}. Call your create_goal tool with this objective, then work it.

Objective: milestone {milestone} of module {module} is claimed. That means every item for {milestone} in \
{plans}/{module}-DONE.json has status pass with evidence from its named target, the milestone's state is claimed (or \
done, if no item has inspect or ask and it isn't the module's last milestone), and the work is committed and \
integrated with the profile's Check passing on the integrated tip.

Use $build-milestone for method, constraints and permissions. Work only in this worktree. Change only items' status \
and evidence and the milestone's state; the rest of the done-when file belongs to the planner and reviewer, and the \
loop rejects a claim if it changes. Hold the integrate lock while you rebase, run the Check and push: \
`python3 {loop} lock integrate -- sh -c '<rebase, check and push>'`. Take other exclusive resources the same way.

Don't launch the evaluator; the lead runs review. End with DONE and the evidence when the claim is made. If you're \
blocked (probed directly) or missing context, end with `BLOCKED: ...` or `NEEDS_CONTEXT: ...` and the evidence."""

FINDINGS_TEMPLATE = """The evaluator failed {milestone}: see {evidence}/{module}/{milestone}-review.md. Every finding \
counts, including cant_tell items (they need evidence the evaluator could reach) and defects outside the items. Add \
them to the plan as work items, fix them, re-verify the affected items, integrate, set the state back to claimed, \
and end with DONE, BLOCKED or NEEDS_CONTEXT."""


# ---------------------------------------------------------------------------------------------------------- profile

PROFILE_FIELDS = {"plans": "docs/modules", "evidence": "docs/evidence", "check": "", "branch": "main",
                  "remote": "origin", "integrate": "push", "codex sandbox": "workspace-write", "writable roots": "",
                  "graded examples": ""}
ONE_WORD = {"branch", "remote", "integrate", "codex sandbox"}
ALLOWED = {"codex sandbox": {"workspace-write", "danger-full-access"}, "integrate": {"push", "local"}}


def profile(worktree: Path, strict: bool = False) -> dict:
    """Reads the loop's settings from ORCHESTRATE.md (`- **Label:** value` lines). Missing labels take defaults.
    A missing profile, or an unfilled or invalid value, raises SystemExit when strict, and falls back to defaults with
    a warning otherwise."""
    path = worktree / "ORCHESTRATE.md"
    problems = [] if path.exists() else [f"no ORCHESTRATE.md in {worktree}"]
    text = path.read_text() if path.exists() else ""
    out = {}
    for key, default in PROFILE_FIELDS.items():
        m = re.search(rf"^\s*[-*]\s*\*\*{re.escape(key)}:\*\*[ \t]*(.*)$", text, re.IGNORECASE | re.MULTILINE)
        raw = m.group(1) if m else ""
        raw = re.sub(r"\*\(.*?\)\*", "", raw)                 # trailing *(read by the loop)* notes
        raw = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw)  # markdown links keep their text
        value = raw.replace("`", "").strip()
        if key in ONE_WORD and value:
            value = value.split()[0]
        if not value:
            out[key] = default
        elif "<" in value or (key in ALLOWED and value not in ALLOWED[key]):
            problems.append(f"{key}: {value!r}")
            out[key] = default
        else:
            out[key] = value.rstrip("/") if key in ("plans", "evidence") else value
    gen = re.search(r"\*\*Codex generator:\*\*[ \t]*(.*)$", text, re.MULTILINE)
    out["model"], out["effort"] = DEFAULT_MODEL, DEFAULT_EFFORT
    if gen:
        m = re.match(r"`?([\w.\-]+)`?[ ,]+`?(\w+)`?", re.sub(r"\*\(.*?\)\*", "", gen.group(1)).strip())
        if m and m.group(2) in EFFORTS and "<" not in gen.group(1):
            out["model"], out["effort"] = m.group(1), m.group(2)
        else:
            problems.append(f"codex generator: {gen.group(1).strip()!r} (want '<model> <effort>', effort one of "
                            f"{', '.join(sorted(EFFORTS))})")
    out["sandbox"] = out.pop("codex sandbox")
    out["roots"] = [r.strip() for r in out.pop("writable roots").split(",") if r.strip()]
    out["graded_examples"] = out.pop("graded examples") or f"{out['evidence']}/graded-examples.md"
    if problems:
        message = "ORCHESTRATE.md has missing, unfilled or invalid fields: " + "; ".join(problems)
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


# ------------------------------------------------------------------------------------------------- done-when file

def load_done(worktree: Path, module: str, prof: dict | None = None) -> dict:
    path = worktree / (prof or profile(worktree))["plans"] / f"{module}-DONE.json"
    if not path.exists():
        raise SystemExit(f"error: {path} doesn't exist; the module needs planning (/plan-module) first")
    return json.loads(path.read_text())


def validate(done: dict) -> list[str]:
    """The structural problems that would let a claim through without proof."""
    problems, seen = [], set()
    if not done.get("milestones"):
        return ["no milestones"]
    for m in done["milestones"]:
        mid = m.get("id", "?")
        if mid in seen:
            problems.append(f"duplicate milestone id {mid}")
        seen.add(mid)
        if m.get("state") not in STATES:
            problems.append(f"{mid}: state {m.get('state')!r} isn't one of {sorted(STATES)}")
        if not m.get("items"):
            problems.append(f"{mid}: no items")
        for item in m.get("items", []):
            iid = item.get("id", "?")
            if iid in seen:
                problems.append(f"duplicate item id {iid}")
            seen.add(iid)
            if not item.get("statement"):
                problems.append(f"{iid}: no statement")
            if not any(item.get(k) for k in ("check", "inspect", "ask")):
                problems.append(f"{iid}: no check, inspect or ask, so nothing proves it")
            if item.get("status", "open") not in STATUSES:
                problems.append(f"{iid}: status {item.get('status')!r} isn't one of {sorted(STATUSES)}")
            if item.get("verdict", "") not in VERDICTS:
                problems.append(f"{iid}: verdict {item.get('verdict')!r} isn't one of {sorted(VERDICTS - {''})}")
    return problems


def definitions(milestone: dict) -> str:
    """A hash of what the milestone asks for, as opposed to what anyone has claimed about it."""
    spec = {"bar": milestone.get("bar"), "items": [{k: i.get(k) for k in DEFINITION_KEYS} for i in milestone["items"]]}
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def find(done: dict, mid: str) -> dict:
    for m in done["milestones"]:
        if m["id"] == mid:
            return m
    raise SystemExit(f"error: milestone {mid} not in done-when file")


def needs_review(milestone: dict, done: dict) -> bool:
    """`inspect` and `ask` need the evaluator's judgement, and so does the module's last milestone, whose review reads
    the whole module. Other milestones close on their checks."""
    return milestone is done["milestones"][-1] or any(i.get("inspect") or i.get("ask") for i in milestone["items"])


def passing(milestone: dict) -> int:
    return sum(1 for item in milestone["items"] if item.get("status") == "pass")


def awaiting_review(milestone: dict, done: dict) -> bool:
    """Claimed, or marked done by its builder although it needs a reviewer who hasn't passed every item."""
    if milestone.get("state") == "claimed":
        return True
    return (milestone.get("state") == "done" and needs_review(milestone, done)
            and not all(i.get("verdict") == "pass" for i in milestone["items"]))


def pick_milestone(done: dict, wanted: str | None) -> dict:
    if wanted:
        m = find(done, wanted)
        if m.get("state") in ("done", "parked"):
            print(f"warning: {wanted} is {m['state']}", file=sys.stderr)
        return m
    for state in ("in_progress", "open"):
        for m in done["milestones"]:
            closed_by_checks = not needs_review(m, done) and passing(m) == len(m["items"])
            if m.get("state") == state and not closed_by_checks:
                return m
    raise SystemExit("error: no open milestone")


def escalation(fails: int, replans: int = 0) -> str:
    if fails <= 0:
        return "none"
    if fails <= 2:
        return "same-session"
    if fails == 3:
        return "fresh-session"
    return "replan" if replans == 0 else "park"


# -------------------------------------------------------------------------------------------- processes and locks

def run_proc(args, cwd: Path | None, timeout_s: float, shell: bool = False) -> tuple[int, str, str]:
    """Runs a command in its own process group, so a timeout kills everything it started. 124 means it timed out."""
    proc = subprocess.Popen(args, shell=shell, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        out, err = proc.communicate(timeout=timeout_s)
        return proc.returncode, out, err
    except subprocess.TimeoutExpired:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        out, err = proc.communicate()
        return 124, out or "", (err or "") + "\n(timed out)"


def git_common_dir(worktree: Path) -> str:
    out = subprocess.run(["git", "-C", str(worktree), "rev-parse", "--git-common-dir"], capture_output=True, text=True)
    return str((worktree / out.stdout.strip()).resolve())


@contextmanager
def held(name: str, worktree: Path):
    """Holds the repository-wide lock `name` for the duration of the block."""
    if not re.fullmatch(r"[\w.-]+", name):
        raise SystemExit(f"error: lock name {name!r} may only use letters, digits, '.', '_' and '-'")
    with open(Path(git_common_dir(worktree)) / f"orchestrate-{name}.lock", "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


# ---------------------------------------------------------------------------------------------- the claim itself

def git(worktree: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, text=True)


def head_commit(worktree: Path) -> str:
    return git(worktree, "rev-parse", "HEAD").stdout.strip()


def integration(worktree: Path, prof: dict) -> tuple[bool, str]:
    """Whether the committed work is integrated: a clean tree, no untracked files, and HEAD on the base branch,
    fetched fresh when integration pushes to a remote."""
    status = git(worktree, "status", "--porcelain").stdout.strip()
    if status:
        return False, "uncommitted or untracked files (commit, remove or ignore them): " + status[:300]
    if prof.get("integrate", "push") == "local":
        base = prof["branch"]
    else:
        fetch = git(worktree, "fetch", "--quiet", prof["remote"])
        if fetch.returncode != 0:
            return False, f"git fetch {prof['remote']} failed, so integration can't be checked: {fetch.stderr[-300:]}"
        base = f"{prof['remote']}/{prof['branch']}"
    ok = git(worktree, "merge-base", "--is-ancestor", "HEAD", base).returncode == 0
    return ok, base if ok else f"HEAD is not on {base}"


def check_failures(worktree: Path, prof: dict, milestone: dict, timeout_s: float = 3600) -> list[str]:
    """Runs the profile's Check, then each item's check (under its lock, if it names one). Returns what failed."""
    runs = [("Check", prof.get("check"), None)] if prof.get("check") else []
    runs += [(i["id"], i["check"], i.get("lock")) for i in milestone["items"] if i.get("check")]
    failed = []
    for label, command, lock in runs:
        if lock:
            with held(lock, worktree):
                code, out, err = run_proc(command, worktree, timeout_s, shell=True)
        else:
            code, out, err = run_proc(command, worktree, timeout_s, shell=True)
        if code != 0:
            failed.append(f"{label} `{command}` " + ("timed out" if code == 124 else f"exited {code}") +
                          f": {(out + err)[-600:]}")
    return failed


def claim_problems(worktree: Path, prof: dict, milestone: dict, done: dict) -> list[str]:
    reviewed = needs_review(milestone, done)
    if milestone.get("state") not in ("claimed", "done"):
        return ["set the milestone's state to claimed once every item passes"]
    if milestone.get("state") == "done" and reviewed:
        return ["this milestone needs a reviewer, so set its state to claimed, not done"]
    missing = [i["id"] for i in milestone["items"] if not i.get("evidence")]
    if missing:
        return ["items marked pass with no evidence: " + ", ".join(missing)]
    ok, detail = integration(worktree, prof)
    if not ok:
        return [detail]
    before = git(worktree, "status", "--porcelain", "--untracked-files=no").stdout
    failures = check_failures(worktree, prof, milestone)
    after = git(worktree, "status", "--porcelain", "--untracked-files=no").stdout
    if after != before:
        failures.append("running the checks changed tracked files: " + after.strip()[:300])
    return failures


# ------------------------------------------------------------------------------------------- telemetry (optional)

def rollout_for(thread_id: str) -> Path | None:
    hits = glob.glob(str(CODEX_HOME / "sessions" / "**" / f"rollout-*{thread_id}.jsonl"), recursive=True)
    return Path(max(hits, key=os.path.getmtime)) if hits else None


def json_lines(path: Path, marker: str):
    """Parsed lines containing `marker`, skipping any that don't parse (the file may be mid-write)."""
    try:
        with open(path) as handle:
            for line in handle:
                if marker in line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
    except OSError:
        return


def pin_mismatches(rollout: Path, model_pin: str = DEFAULT_MODEL, effort_pin: str = DEFAULT_EFFORT) -> list[str]:
    # Codex's auto-review turns run in their own rollout files, so they don't show up here.
    bad = []
    for event in json_lines(rollout, '"turn_context"'):
        payload = event.get("payload", {})
        model, effort = payload.get("model"), payload.get("effort")
        if (model, effort) != (model_pin, effort_pin):
            bad.append(f"{payload.get('turn_id')}: {model}/{effort}")
    return bad


def quota_samples(since: float) -> list[tuple[float, float, float]]:
    """(time, used_percent, resets_at) for the weekly Codex limit, from rollouts touched since `since`."""
    samples = []
    for f in glob.glob(str(CODEX_HOME / "sessions" / "**" / "rollout-*.jsonl"), recursive=True):
        try:
            if os.path.getmtime(f) < since:
                continue
        except OSError:
            continue
        for event in json_lines(Path(f), '"token_count"'):
            try:
                limits = event.get("payload", {}).get("rate_limits") or {}
                primary = limits.get("primary") or {}
                if limits.get("limit_id") != "codex" or primary.get("window_minutes") != 10080:
                    continue
                when = datetime.fromisoformat(event["timestamp"].replace("Z", "+00:00")).timestamp()
                samples.append((when, float(primary["used_percent"]), float(primary["resets_at"])))
            except (KeyError, TypeError, ValueError):
                continue
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
    try:
        now = time.time()
        return forecast(quota_samples(now - 26 * 3600), now)
    except Exception as e:  # optional telemetry must never cost the result line
        return {"unavailable": f"{type(e).__name__}: {e}"}


def goal_status(thread_id: str | None) -> str | None:
    db = CODEX_HOME / "goals_1.sqlite"
    if not thread_id or not db.exists():
        return None
    try:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
            row = conn.execute("select status from thread_goals where thread_id=?", (thread_id,)).fetchone()
        return row[0] if row else None
    except sqlite3.Error:
        return None


# ------------------------------------------------------------------------------------------------------- the loop

def run_turn(args: list[str], worktree: Path, timeout_s: float) -> tuple[int, str | None, str, str]:
    """Runs one codex exec call; returns (exit code, thread id, last agent message, stderr tail)."""
    code, stdout, stderr = run_proc([CODEX, *args], worktree, timeout_s)
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
    return code, thread_id, last_message, stderr[-800:]


def report_word(message: str) -> str | None:
    """The report word on the message's last non-empty line, if it has one."""
    lines = [l.strip() for l in message.splitlines() if l.strip()]
    if not lines:
        return None
    word = lines[-1].split(":")[0].strip("`* ")
    return word if word in REPORT_WORDS else None


def emit(result: str, **fields) -> None:
    print(json.dumps({"result": result, **fields, "quota": quota_now()}))
    sys.exit(0)


def finish(state_path: Path, state: dict, result: str, **extra) -> None:
    state.update(result=result, finished=time.time(), **extra)
    state_path.write_text(json.dumps(state, indent=2))
    emit(result, module=state["module"], milestone=state["milestone"], thread=state.get("thread"), **extra)


def moved_outside_plans(worktree: Path, old: str, new: str, plans: str) -> bool:
    """Whether the commits between old and new touch anything besides the plans folder."""
    if old == new:
        return False
    names = git(worktree, "diff", "--name-only", old, new).stdout.split()
    return any(not n.startswith(plans.rstrip("/") + "/") for n in names)


def cmd_run(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    git_dir = git(worktree, "rev-parse", "--absolute-git-dir").stdout.strip()
    state_dir = Path(git_dir) / "orchestrate"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{a.module}.json"
    prof = profile(worktree, strict=True)
    done = load_done(worktree, a.module, prof)
    if problems := validate(done):
        emit("INVALID", module=a.module, problems=problems[:20])
    if not a.milestone:
        owed = next((m for m in done["milestones"] if awaiting_review(m, done)), None)
        if owed:
            emit("REVIEW_OWED", module=a.module, milestone=owed["id"], commit=head_commit(worktree))
    milestone = pick_milestone(done, a.milestone)
    pin = [prof["model"], prof["effort"]]
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    fresh = (a.fresh or state.get("milestone") != milestone["id"] or state.get("result") == "PIN"
             or state.get("pin") != pin)
    if fresh:
        state = {"module": a.module, "milestone": milestone["id"], "thread": None, "turns": 0, "pin": pin}
    replans = int(milestone.get("replans", 0))
    if state.get("defs", {}).get("replans") != replans:  # a re-plan legitimately changes the definitions
        state["defs"] = {"replans": replans, "hash": definitions(milestone)}
    # Every run starts its own counters, so a resume after BUDGET or a failed review isn't judged on old progress.
    state.update(failed_turns=0, reports=0, unclaimed=0, progress_at=time.time(), passing=passing(milestone),
                 head=head_commit(worktree))
    state.pop("result", None)
    flags = codex_flags(prof)
    # Labels the thread the way the Codex app labels its own, so it shows in the app's thread list.
    source = ["--thread-source", "vscode"] if codex_supports("--thread-source") else []
    timeout_s = a.turn_timeout_hours * 3600
    common = ["-C", str(worktree), "--add-dir", git_common_dir(worktree)]

    while True:
        status = goal_status(state.get("thread"))
        if status in ("usage_limited", "budget_limited"):
            finish(state_path, state, "FLOOR", reason=f"goal {status}")
        if status == "paused":
            finish(state_path, state, "PAUSED")
        if state.get("thread") is None:
            prompt = GOAL_TEMPLATE.format(model=prof["model"], effort=prof["effort"], milestone=milestone["id"],
                                          module=a.module, plans=prof["plans"], loop=LOOP)
            if a.message:
                prompt += "\n\n" + a.message
                a.message = None
            code, thread_id, message, err = run_turn(["exec", *flags, *common, *source, "--json", prompt],
                                                     worktree, timeout_s)
            state["thread"] = thread_id
        else:
            prompt = a.message or "Continue the goal."
            a.message = None
            code, _, message, err = run_turn(["exec", *common, "resume", state["thread"], *flags, "--json", prompt],
                                             worktree, timeout_s)
        state["turns"] += 1
        state["failed_turns"] = state["failed_turns"] + 1 if code != 0 else 0
        state_path.write_text(json.dumps(state, indent=2))

        if state["thread"] is None or state["failed_turns"] >= 2:
            finish(state_path, state, "FLOOR", reason="two failed turns or no thread; likely quota or outage",
                   exit_code=code, stderr=err)
        rollout = rollout_for(state["thread"])
        if rollout and (bad := pin_mismatches(rollout, prof["model"], prof["effort"])):
            finish(state_path, state, "PIN", mismatches=bad[:5])
        status = goal_status(state["thread"])
        if status in ("usage_limited", "budget_limited"):
            finish(state_path, state, "FLOOR", reason=f"goal {status}")
        if status == "paused":
            finish(state_path, state, "PAUSED")

        done = load_done(worktree, a.module, prof)
        if problems := validate(done):
            finish(state_path, state, "INVALID", problems=problems[:20])
        current = find(done, milestone["id"])
        if definitions(current) != state["defs"]["hash"] and int(current.get("replans", 0)) == replans:
            finish(state_path, state, "INVALID",
                   problems=["the milestone's acceptance definitions (statements, checks, inspect, ask, targets, "
                             "locks or bar) changed during the run; only the planner changes them, by re-planning"])
        now_passing, head = passing(current), head_commit(worktree)
        if now_passing > state["passing"] or moved_outside_plans(worktree, state["head"], head, prof["plans"]):
            state["progress_at"] = time.time()
        state.update(passing=now_passing, head=head)

        word = report_word(message)
        if now_passing == len(current["items"]):
            reasons = claim_problems(worktree, prof, current, done)
            if not reasons:
                finish(state_path, state, "CLAIMED", review=needs_review(current, done), commit=head)
        else:
            reasons = ["items not yet pass: " + ", ".join(i["id"] for i in current["items"]
                                                           if i.get("status") != "pass")]
        state["claim_blocked"] = "; ".join(reasons)
        if word == "DONE" or status == "complete":
            state["unclaimed"] += 1
            if state["unclaimed"] >= 3:
                finish(state_path, state, "UNCLAIMED", reasons=reasons)
        if word == "DONE" or now_passing == len(current["items"]):
            a.message = f"The loop can't accept the claim yet: {state['claim_blocked']}. Fix that, then end with DONE."
        if word in ("BLOCKED", "NEEDS_CONTEXT"):
            state["reports"] += 1
            if status != "active" or state["reports"] >= 2:
                finish(state_path, state, word, report=message[-1500:])
        else:
            state["reports"] = 0
        if status == "blocked":
            finish(state_path, state, "BLOCKED", report=message[-1500:])
        if time.time() - state["progress_at"] > a.budget_hours * 3600:
            finish(state_path, state, "BUDGET", hours=a.budget_hours)


def cmd_next(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree)
    milestone = find(load_done(worktree, a.module, prof), a.milestone)
    fails, replans = int(milestone.get("fails", 0)), int(milestone.get("replans", 0))
    message = FINDINGS_TEMPLATE.format(milestone=milestone["id"], module=a.module, evidence=prof["evidence"])
    print(json.dumps({"milestone": milestone["id"], "fails": fails, "replans": replans,
                      "action": escalation(fails, replans), "message": message}))


def cmd_profile(a: argparse.Namespace) -> None:
    print(json.dumps(profile(Path(a.worktree).resolve(), strict=True), indent=2))


def cmd_status(a: argparse.Namespace) -> None:
    done = load_done(Path(a.worktree).resolve(), a.module)
    for problem in validate(done):
        print(f"invalid: {problem}")
    for m in done["milestones"]:
        flag = "\treview owed" if awaiting_review(m, done) else ""
        print(f"{m['id']}\t{m.get('state')}\tfails={m.get('fails', 0)}\t{passing(m)}/{len(m['items'])} pass"
              f"\t{m.get('name', '')}{flag}")


def cmd_quota(a: argparse.Namespace) -> None:
    print(json.dumps(quota_now()))


def cmd_lock(a: argparse.Namespace) -> None:
    rest, worktree = list(a.command_args), a.worktree
    split = rest.index("--") if "--" in rest else 0
    before, command = rest[:split], rest[split + 1:] if "--" in rest else rest
    while before:
        if before[0] == "--worktree" and len(before) > 1:
            worktree, before = before[1], before[2:]
        else:
            raise SystemExit("error: usage: lock [--worktree PATH] NAME -- COMMAND...")
    if not command:
        raise SystemExit("error: usage: lock [--worktree PATH] NAME -- COMMAND...")
    where = Path(worktree or Path.cwd()).resolve()
    if subprocess.run(["git", "-C", str(where), "rev-parse"], capture_output=True).returncode != 0:
        raise SystemExit(f"error: {where} is not in a git repository, so there is no shared lock location")
    with held(a.name, where):
        sys.exit(subprocess.run(command, cwd=where if worktree else None).returncode)


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
    lock.add_argument("--worktree")
    lock.add_argument("name")
    lock.add_argument("command_args", nargs=argparse.REMAINDER)
    lock.set_defaults(func=cmd_lock)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
