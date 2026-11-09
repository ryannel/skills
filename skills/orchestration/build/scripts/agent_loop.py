#!/usr/bin/env python3
"""Drives builders, reviewers and planners for the orchestrate process on any supported agent host, with model and
effort named at every launch, and checks every claim itself.

Used by the `build` lead (on any host that can run shell commands) and runnable by hand. Project settings come from
ORCHESTRATE.md at the worktree root (`profile` prints what was read). Needs git, plus the CLI of each host it
launches. POSIX only (fcntl, process groups).

Hosts:
  codex    `codex exec`, resumable, with goals, pinned-turn checks and a quota forecast from Codex's local files.
  claude   `claude -p` with stream-json, resumable, launched with no API key in its environment so it uses the
           signed-in plan. Reviewers and planners use the installed orchestrate agent files when present.
  <name>   any other CLI, from a `- **Host <name>:** <command>` line in the profile, with {prompt}, {model}, {effort}
           and {cwd} placeholders. Each turn is a fresh process; the files carry state between turns.

The loop runs checks with your own permissions, outside any host's sandbox. It pins the check strings to the
planner's revision, but a script a check calls can still be changed by the builder, so review new check scripts.

Subcommands:

  run   --module CORE --worktree PATH [--host codex] [--model M] [--effort E] [--milestone M2] [--fresh]
        [--message TEXT] [--budget-hours 4]
        Starts (or resumes) a builder session on the milestone and drives it one turn at a time until:
        CLAIMED       the claim holds: the done-when file is valid and its acceptance definitions are unchanged, the
                      milestone's state is `claimed` (or `done` when it needs no review), every item is `pass` with
                      evidence, the tree is clean with no untracked files, HEAD is on the base branch, and the
                      profile's Check and every item's `check` exit 0 when the loop runs them. Anything short of that
                      goes back to the builder with the reasons. `review` says whether a reviewer must judge it,
                      and `commit` is the commit to review.
        BLOCKED / NEEDS_CONTEXT   the agent's final report line
        UNCLAIMED     the agent said DONE (or its goal completed) three times without a claim that holds
        INVALID       the done-when file is malformed, or its acceptance definitions changed during the run
        REVIEW_OWED   an earlier milestone is claimed and waiting for review (only without --milestone)
        WAITING       no milestone is ready: the next ones need milestones in other modules that aren't done
        BUDGET        no new passing item or commit outside the plans folder for --budget-hours
        FLOOR         two failed turns in a row, or the goal is usage- or budget-limited (likely quota or outage)
        PIN           a turn ran on a model or effort other than the named ones
        PAUSED        the Codex goal is paused; resume it from the Codex app or with /goal resume
        A run on the same milestone resumes its session (with --message as the first prompt, e.g. the reviewer's
        findings) unless --fresh is given or the host, model or effort changed. A new milestone starts a new session.
        Prints one JSON line with the result as the last line of output.

  review --module CORE --milestone M2 --commit SHA --worktree PATH [--host claude] [--model M] [--effort E]
        Runs a fresh reviewer session on the claimed milestone (or on the module's design, with --milestone design), then reports its last line, the files its commit
        touched, and any field it changed that a reviewer doesn't own.

  plan  --worktree PATH --task TEXT [--host claude] [--model M] [--effort high]
        Runs a fresh planner session on the task (plan a module, re-plan a milestone, route a missing dependency).

  ready --worktree PATH
        Reads every done-when file at the integrated tip and prints which milestones are ready to build, which are
        waiting on another module, which are owed review, and which modules have nothing left.

  next  --module CORE --worktree PATH --milestone M2
        Reads the milestone's `fails` (written by the reviewer) and `replans` (written by the planner) and prints the
        escalation: same-session (1-2 fails), fresh-session (3), replan (4+ with no re-plan yet), park (4+ after a
        re-plan), or none (0), with the message to pass on.

  status --module CORE --worktree PATH
        Prints each milestone's state, fails, passing items and unmet needs, and flags milestones waiting for review.

  quota
        Forecasts the weekly Codex limit from the last day of use across all sessions.

  profile --worktree PATH
        Prints the settings read from ORCHESTRATE.md, or exits 1 naming the fields that are missing, unfilled or invalid.

  lock [--worktree PATH] NAME -- COMMAND...
        Runs COMMAND (in PATH, if given) under a named lock shared by every worktree of the repository, so runs that
        need an exclusive resource never overlap across parallel builders. The lock covers one repository, not the
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
import shlex
import shutil
import signal
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_MODELS = {"codex": "gpt-6.1-sol", "claude": "claude-opus-5-5"}
DEFAULT_MODEL = DEFAULT_MODELS["codex"]
DEFAULT_EFFORT = "medium"  # the house position for code; planners default to high
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
CODEX = os.environ.get("ORCHESTRATE_CODEX") or shutil.which("codex") or \
    "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"
CLAUDE = os.environ.get("ORCHESTRATE_CLAUDE") or shutil.which("claude") or "claude"
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
REPORT_WORDS = ("DONE", "BLOCKED", "NEEDS_CONTEXT")
STATES = {"open", "in_progress", "claimed", "done", "parked"}
STATUSES = {"open", "pass"}
VERDICTS = {"", "pass", "fail", "cant_tell"}
DEFINITION_KEYS = ("statement", "check", "inspect", "ask", "target", "lock")
NEED = re.compile(r"^(?:([A-Za-z0-9_.-]+):)?([A-Za-z0-9_.-]+)$")  # "M2" in this module, or "CORE:M3"

LOOP = Path(__file__).resolve()

GOAL_LINE = "Call your create_goal tool with this objective, then work it.\n\n"

BUILD_TEMPLATE = """Model {model}, effort {effort}. {goal}Objective: milestone {milestone} of module {module} is \
claimed. That means every item for {milestone} in {plans}/{module}-DONE.json has status pass with evidence from its \
named target, the milestone's state is claimed (or done, if no item has inspect or ask and it isn't the module's last \
milestone), and the work is committed and integrated with the profile's Check passing on the integrated tip.

Use the build-milestone skill ($build-milestone in Codex) for method, constraints and permissions. Work only in this \
worktree. Change only items' status and evidence and the milestone's state; the rest of the done-when file belongs to \
the planner and reviewer, and the loop rejects a claim if it changes. If the milestone needs something another module \
owns that isn't there yet, don't build it here: end with BLOCKED and name it. Hold the integrate lock while you \
rebase, run the Check and push: `python3 {loop} lock integrate -- sh -c '<rebase, check and push>'`. Take other \
exclusive resources the same way.

Don't launch a reviewer; the lead runs review. End with DONE and the evidence when the claim is made. If you're \
blocked (probed directly) or missing context, end with `BLOCKED: ...` or `NEEDS_CONTEXT: ...` and the evidence."""

REVIEW_TEMPLATE = """Model {model}, effort {effort}. Use the review-milestone skill ($review-milestone in Codex) to \
review milestone {milestone} of module {module} at commit {commit}. The done-when file is {plans}/{module}-DONE.json. \
Change only the review file and the verdict fields the skill names, and don't launch other agents. End with the \
skill's last line."""

DESIGN_REVIEW_TEMPLATE = """Model {model}, effort {effort}. Use the review-milestone skill ($review-milestone in \
Codex) to review the design of module {module}, as its "Reviewing a design" section describes. Don't launch other \
agents. End with the skill's last line."""

PLAN_TEMPLATE = """Model {model}, effort {effort}. Use the plan-module skill ($plan-module in Codex) for this task: \
{task}

You can't launch other agents. If a design review is owed, end by saying so. End with what changed, the files \
changed, and any decision the owner must make."""

FINDINGS_TEMPLATE = """The reviewer failed {milestone}: see {evidence}/{module}/{milestone}-review.md. Every finding \
counts, including cant_tell items (they need evidence the reviewer could reach) and defects outside the items. Add \
them to the plan as work items, fix them, re-verify the affected items, integrate, set the state back to claimed, \
and end with DONE, BLOCKED or NEEDS_CONTEXT."""


# ---------------------------------------------------------------------------------------------------------- profile

PROFILE_FIELDS = {"plans": "docs/modules", "evidence": "docs/evidence", "check": "", "branch": "main",
                  "remote": "origin", "integrate": "push", "codex sandbox": "workspace-write", "writable roots": "",
                  "graded examples": "", "codex model": "", "claude model": "", "effort": "",
                  "claude permissions": "auto"}
ONE_WORD = {"branch", "remote", "integrate", "codex sandbox", "codex model", "claude model", "effort",
            "claude permissions"}
ALLOWED = {"codex sandbox": {"workspace-write", "danger-full-access"}, "integrate": {"push", "local"},
           "effort": EFFORTS, "claude permissions": {"auto", "acceptEdits", "bypassPermissions", "dontAsk"}}


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
    out["models"] = {"codex": out.pop("codex model") or DEFAULT_MODELS["codex"],
                     "claude": out.pop("claude model") or DEFAULT_MODELS["claude"]}
    out["effort"] = out["effort"] or DEFAULT_EFFORT
    out["hosts"] = {}
    for m in re.finditer(r"^\s*[-*]\s*\*\*Host ([\w.-]+):\*\*[ \t]*(.*)$", text, re.IGNORECASE | re.MULTILINE):
        name, command = m.group(1).lower(), re.sub(r"\*\(.*?\)\*", "", m.group(2)).replace("`", "").strip()
        if name in ("codex", "claude") or "{prompt}" not in command:
            problems.append(f"host {name}: {command!r} (needs a {{prompt}} placeholder, and codex and claude are built in)")
        else:
            out["hosts"][name] = command
    gen = re.search(r"\*\*Codex generator:\*\*[ \t]*(.*)$", text, re.MULTILINE)  # older profiles
    out["model"] = out["models"]["codex"]
    if gen:
        m = re.match(r"`?([\w.\-]+)`?[ ,]+`?(\w+)`?", re.sub(r"\*\(.*?\)\*", "", gen.group(1)).strip())
        if m and m.group(2) in EFFORTS and "<" not in gen.group(1):
            out["model"], out["effort"] = m.group(1), m.group(2)
            out["models"]["codex"] = m.group(1)
        else:
            problems.append(f"codex generator: {gen.group(1).strip()!r} (want '<model> <effort>', effort one of "
                            f"{', '.join(sorted(EFFORTS))})")
    out["sandbox"] = out.pop("codex sandbox")
    out["claude_permissions"] = out.pop("claude permissions")
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


def integrated_done(worktree: Path, prof: dict) -> dict[str, dict]:
    """Every module's done-when file at the integrated tip (fetched fresh when integration pushes), so readiness is
    judged on what has actually landed. Falls back to the worktree's files if the base can't be read."""
    base = prof["branch"]
    if prof.get("integrate", "push") != "local":
        if git(worktree, "fetch", "--quiet", prof["remote"]).returncode == 0:
            base = f"{prof['remote']}/{prof['branch']}"
    listing = git(worktree, "ls-tree", "--name-only", f"{base}:{prof['plans']}")
    out = {}
    if listing.returncode == 0:
        for name in listing.stdout.split():
            if name.endswith("-DONE.json"):
                shown = git(worktree, "show", f"{base}:{prof['plans']}/{name}")
                try:
                    out[name[:-len("-DONE.json")].upper()] = json.loads(shown.stdout)
                except json.JSONDecodeError:
                    out[name[:-len("-DONE.json")].upper()] = {"milestones": [], "unreadable": True}
        return out
    for path in sorted((worktree / prof["plans"]).glob("*-DONE.json")):
        try:
            out[path.name[:-len("-DONE.json")].upper()] = json.loads(path.read_text())
        except json.JSONDecodeError:
            out[path.name[:-len("-DONE.json")].upper()] = {"milestones": [], "unreadable": True}
    return out


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
        needs = m.get("needs", [])
        if not isinstance(needs, list) or not all(isinstance(n, str) and NEED.match(n) for n in needs):
            problems.append(f"{mid}: needs {needs!r} should be a list like [\"M2\", \"CORE:M3\"]")
    return problems


def definitions(milestone: dict) -> str:
    """A hash of what the milestone asks for, as opposed to what anyone has claimed about it."""
    spec = {"bar": milestone.get("bar"), "needs": milestone.get("needs") or [], "items": [{k: i.get(k) for k in DEFINITION_KEYS} for i in milestone["items"]]}
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def find(done: dict, mid: str) -> dict:
    for m in done["milestones"]:
        if m["id"] == mid:
            return m
    raise SystemExit(f"error: milestone {mid} not in done-when file")


def needs_review(milestone: dict, done: dict) -> bool:
    """`inspect` and `ask` need the reviewer's judgement, and so does the module's last milestone, whose review reads
    the whole module. Other milestones close on their checks."""
    return milestone is done["milestones"][-1] or any(i.get("inspect") or i.get("ask") for i in milestone["items"])


def needs_of(milestone: dict, module: str) -> list[tuple[str, str]]:
    """The milestone's `needs` as (module, milestone) pairs; a bare id means this module."""
    out = []
    for need in milestone.get("needs") or []:
        m = NEED.match(str(need))
        if m:
            out.append(((m.group(1) or module).upper(), m.group(2)))
    return out


def unmet(milestone: dict, module: str, all_done: dict[str, dict]) -> list[str]:
    """The needs that aren't done yet, read from every module's done-when file."""
    waiting = []
    for mod, mid in needs_of(milestone, module):
        other = next((m for m in (all_done.get(mod) or {}).get("milestones", []) if m.get("id") == mid), None)
        if not other or other.get("state") != "done":
            waiting.append(f"{mod}:{mid}" + ("" if other else " (not planned)"))
    return waiting


def passing(milestone: dict) -> int:
    return sum(1 for item in milestone["items"] if item.get("status") == "pass")


def awaiting_review(milestone: dict, done: dict) -> bool:
    """Claimed, or marked done by its builder although it needs a reviewer who hasn't passed every item."""
    if milestone.get("state") == "claimed":
        return True
    return (milestone.get("state") == "done" and needs_review(milestone, done)
            and not all(i.get("verdict") == "pass" for i in milestone["items"]))


def pick_milestone(done: dict, wanted: str | None, module: str = "", all_done: dict | None = None) -> dict:
    """The named milestone, or the first in-progress then open one whose needs are done. Raises SystemExit if there's
    none; `waiting` on the exception lists milestones held back by unmet needs."""
    all_done = all_done or {}
    if wanted:
        m = find(done, wanted)
        if m.get("state") in ("done", "parked"):
            print(f"warning: {wanted} is {m['state']}", file=sys.stderr)
        return m
    # Milestones in a module run in order, so a waiting milestone holds back the ones after it.
    waiting = []
    for state in ("in_progress", "open"):
        for m in done["milestones"]:
            closed_by_checks = not needs_review(m, done) and passing(m) == len(m["items"])
            if m.get("state") != state or closed_by_checks:
                continue
            if blockers := unmet(m, module, all_done):
                waiting.append({"milestone": m["id"], "needs": blockers})
                break
            return m
        if waiting:
            break
    error = SystemExit("error: no open milestone" + (" that's ready" if waiting else ""))
    error.waiting = waiting
    raise error


def escalation(fails: int, replans: int = 0) -> str:
    if fails <= 0:
        return "none"
    if fails <= 2:
        return "same-session"
    if fails == 3:
        return "fresh-session"
    return "replan" if replans == 0 else "park"


# -------------------------------------------------------------------------------------------- processes and locks

def run_proc(args, cwd: Path | None, timeout_s: float, shell: bool = False,
             env: dict | None = None) -> tuple[int, str, str]:
    """Runs a command in its own process group, so a timeout kills everything it started. 124 means it timed out."""
    proc = subprocess.Popen(args, shell=shell, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, start_new_session=True, env=env)
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

def clean_env() -> dict:
    """The environment for a Claude run: no API key or parent-session variables, so it uses the signed-in plan and
    doesn't mistake itself for a nested session. CLAUDE_CONFIG_DIR is kept, because it says which sign-in to use."""
    return {k: v for k, v in os.environ.items()
            if not (k.startswith("ANTHROPIC_") or k.startswith("CLAUDE")) or k == "CLAUDE_CONFIG_DIR"}


def agent_installed(name: str, worktree: Path) -> bool:
    return any(p.exists() for p in (Path.home() / ".claude/agents" / f"{name}.md",
                                    worktree / ".claude/agents" / f"{name}.md"))


def host_command(host: str, prof: dict, model: str, effort: str, worktree: Path, prompt: str,
                 session: str | None, role: str = "build") -> tuple[list[str], dict | None]:
    """The command line (and environment, if it differs from ours) for one turn on `host`."""
    if host == "codex":
        flags = codex_flags({**prof, "model": model, "effort": effort})
        common = ["-C", str(worktree), "--add-dir", git_common_dir(worktree)]
        if session:
            return [CODEX, "exec", *common, "resume", session, *flags, "--json", prompt], None
        # Labels the thread the way the Codex app labels its own, so it shows in the app's thread list.
        source = ["--thread-source", "vscode"] if codex_supports("--thread-source") else []
        return [CODEX, "exec", *flags, *common, *source, "--json", prompt], None
    if host == "claude":
        args = [CLAUDE, "-p", prompt, "--model", model, "--effort", effort, "--output-format", "stream-json",
                "--verbose", "--permission-mode", prof.get("claude_permissions", "auto"),
                "--add-dir", git_common_dir(worktree)]
        agent = {"review": "orchestrate-evaluator", "plan": "orchestrate-planner"}.get(role)
        if agent and agent_installed(agent, worktree):
            args += ["--agent", agent]
        if role in ("review", "plan"):
            args += ["--disallowedTools", "Agent"]
        if session:
            args += ["--resume", session]
        return args, clean_env()
    template = prof.get("hosts", {}).get(host)
    if not template:
        raise SystemExit(f"error: unknown host {host!r}; use codex, claude, or add a '- **Host {host}:** <command>' "
                         "line to ORCHESTRATE.md")
    values = {"prompt": prompt, "model": model, "effort": effort, "cwd": str(worktree)}
    return [token.format(**values) for token in shlex.split(template)], None


def parse_output(host: str, stdout: str) -> tuple[str | None, str, str | None, bool]:
    """(session id, last agent message, model the host reported, whether the host reported an error)."""
    session, message, model, error = None, "", None, False
    if host not in ("codex", "claude"):
        return None, stdout.strip()[-4000:], None, False
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if host == "codex":
            if event.get("type") == "thread.started":
                session = event.get("thread_id")
            item = event.get("item") or {}
            if item.get("type") == "agent_message" and item.get("text"):
                message = item["text"]
        else:
            session = event.get("session_id") or session
            if event.get("type") == "system" and event.get("subtype") == "init":
                model = event.get("model")
            elif event.get("type") == "assistant":
                text = [c.get("text", "") for c in (event.get("message") or {}).get("content") or []
                        if isinstance(c, dict) and c.get("type") == "text"]
                if any(text):
                    message = "\n".join(text)
            elif event.get("type") == "result":
                message = event.get("result") or message
                error = bool(event.get("is_error"))
    return session, message, model, error


def run_turn(host: str, prof: dict, model: str, effort: str, worktree: Path, prompt: str, session: str | None,
             timeout_s: float, role: str = "build") -> tuple[int, str | None, str, str, str | None]:
    """Runs one turn; returns (exit code, session id, last agent message, stderr tail, model the host reported)."""
    args, env = host_command(host, prof, model, effort, worktree, prompt, session, role)
    code, stdout, stderr = run_proc(args, worktree, timeout_s, env=env)
    new_session, message, seen, error = parse_output(host, stdout)
    if error and code == 0:
        code, stderr = 1, (stderr + "\n" + message)[-800:]
    return code, new_session or session, message, stderr[-800:], seen


def report_line(message: str) -> str:
    lines = [l.strip().strip("`*") for l in message.splitlines() if l.strip()]
    return lines[-1] if lines else ""


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


def resolve(a: argparse.Namespace, prof: dict, role: str) -> tuple[str, str, str]:
    """The host, model and effort for this launch: what the lead passed, else the profile, else the defaults."""
    host = (a.host or "codex").lower()
    model = a.model or prof["models"].get(host) or ""
    if not model and host in prof.get("hosts", {}) and "{model}" in prof["hosts"][host]:
        raise SystemExit(f"error: host {host} needs --model")
    effort = a.effort or ("high" if role == "plan" and not a.effort else prof["effort"])
    if effort not in EFFORTS:
        raise SystemExit(f"error: effort {effort!r} isn't one of {sorted(EFFORTS)}")
    return host, model, effort


def pin_problem(host: str, session: str | None, seen: str | None, model: str, effort: str) -> list[str]:
    """Turns that ran on another model or effort, where the host lets us see that."""
    if host == "codex" and session:
        rollout = rollout_for(session)
        return pin_mismatches(rollout, model, effort) if rollout else []
    if host == "claude" and seen and not seen.startswith(model):
        return [f"ran on {seen}, not {model}"]
    return []


def cmd_run(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    git_dir = git(worktree, "rev-parse", "--absolute-git-dir").stdout.strip()
    state_dir = Path(git_dir) / "orchestrate"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{a.module}.json"
    prof = profile(worktree, strict=True)
    host, model, effort = resolve(a, prof, "build")
    done = load_done(worktree, a.module, prof)
    if problems := validate(done):
        emit("INVALID", module=a.module, problems=problems[:20])
    if not a.milestone:
        owed = next((m for m in done["milestones"] if awaiting_review(m, done)), None)
        if owed:
            emit("REVIEW_OWED", module=a.module, milestone=owed["id"], commit=head_commit(worktree))
    try:
        others = integrated_done(worktree, prof) if any(m.get("needs") for m in done["milestones"]) else {}
        milestone = pick_milestone(done, a.milestone, a.module.upper(), others)
    except SystemExit as e:
        if getattr(e, "waiting", None):
            emit("WAITING", module=a.module, waiting=e.waiting)
        raise
    pin = [host, model, effort]
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
                 head=head_commit(worktree), host=host, model=model, effort=effort)
    state.pop("result", None)
    timeout_s = a.turn_timeout_hours * 3600
    resumable = host in ("codex", "claude")

    while True:
        status = goal_status(state.get("thread")) if host == "codex" else None
        if status in ("usage_limited", "budget_limited"):
            finish(state_path, state, "FLOOR", reason=f"goal {status}")
        if status == "paused":
            finish(state_path, state, "PAUSED")
        first = state.get("thread") is None or not resumable
        if first:
            prompt = BUILD_TEMPLATE.format(model=model, effort=effort, goal=GOAL_LINE if host == "codex" else "",
                                           milestone=milestone["id"], module=a.module, plans=prof["plans"], loop=LOOP)
            if state["turns"] and not resumable:
                prompt += "\n\nThis continues earlier work on the same milestone; the files show where it got to."
            if a.message:
                prompt += "\n\n" + a.message
                a.message = None
        else:
            prompt = a.message or "Continue the objective."
            a.message = None
        code, session, message, err, seen = run_turn(host, prof, model, effort, worktree, prompt,
                                                     None if first else state["thread"], timeout_s)
        if resumable:
            state["thread"] = session
        state["turns"] += 1
        state["failed_turns"] = state["failed_turns"] + 1 if code != 0 else 0
        state_path.write_text(json.dumps(state, indent=2))

        if (resumable and state["thread"] is None) or state["failed_turns"] >= 2:
            finish(state_path, state, "FLOOR", reason="two failed turns or no session; likely quota, sign-in or outage",
                   exit_code=code, stderr=err)
        if bad := pin_problem(host, state.get("thread"), seen, model, effort):
            finish(state_path, state, "PIN", mismatches=bad[:5])
        status = goal_status(state["thread"]) if host == "codex" else None
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
                             "locks, needs or bar) changed during the run; only the planner changes them, by "
                             "re-planning"])
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


def one_session(host: str, prof: dict, model: str, effort: str, worktree: Path, prompt: str, role: str,
                done_when, timeout_s: float, max_turns: int = 3) -> dict:
    """Runs a reviewer or planner until its last line satisfies `done_when`, nudging it at most twice."""
    session, message, turns, code, err = None, "", 0, 0, ""
    while turns < max_turns:
        resume = session if (turns and host in ("codex", "claude")) else None
        text = prompt if not resume else "Finish the task and end with the last line it asks for."
        code, session, message, err, seen = run_turn(host, prof, model, effort, worktree, text, resume, timeout_s,
                                                     role)
        turns += 1
        if bad := pin_problem(host, session, seen, model, effort):
            return {"result": "PIN", "mismatches": bad[:5], "session": session}
        if code != 0:
            return {"result": "FLOOR", "exit_code": code, "stderr": err, "session": session}
        if done_when(message):
            break
    last = next((l.strip() for l in reversed(message.splitlines()) if l.strip()), "")
    return {"result": "FINISHED" if done_when(message) else "UNFINISHED", "last_line": last,
            "report": message[-1500:], "session": session, "turns": turns}


def reviewer_overreach(worktree: Path, prof: dict, module: str, before: str, after: str) -> list[str]:
    """Files or fields a reviewer's commits changed that a reviewer doesn't own."""
    if before == after:
        return []
    done_path = f"{prof['plans']}/{module}-DONE.json"
    allowed_dir = f"{prof['evidence']}/{module}/"
    names = git(worktree, "diff", "--name-only", before, after).stdout.split()
    problems = [f"changed {n}" for n in names if n != done_path and not n.startswith(allowed_dir)]
    old, new = git(worktree, "show", f"{before}:{done_path}"), git(worktree, "show", f"{after}:{done_path}")
    try:
        old_done, new_done = json.loads(old.stdout), json.loads(new.stdout)
    except json.JSONDecodeError:
        return problems + ["the done-when file doesn't parse at one end of the review"]
    old_ms = {m["id"]: m for m in old_done.get("milestones", [])}
    for m in new_done.get("milestones", []):
        was = old_ms.get(m["id"])
        if was is None:
            problems.append(f"added milestone {m['id']}")
            continue
        if definitions(m) != definitions(was):
            problems.append(f"{m['id']}: changed its acceptance definitions")
        if int(m.get("replans", 0)) != int(was.get("replans", 0)):
            problems.append(f"{m['id']}: changed replans")
        olds = {i["id"]: i for i in was["items"]}
        for i in m["items"]:
            o = olds.get(i["id"], {})
            if (i.get("status"), i.get("evidence")) != (o.get("status"), o.get("evidence")):
                problems.append(f"{i['id']}: changed the builder's status or evidence")
    return problems


def cmd_review(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    host, model, effort = resolve(a, prof, "review")
    before = head_commit(worktree)
    template = DESIGN_REVIEW_TEMPLATE if a.milestone == "design" else REVIEW_TEMPLATE
    prompt = template.format(model=model, effort=effort, milestone=a.milestone, module=a.module,
                             commit=a.commit, plans=prof["plans"])
    marker = re.compile(r"^(PASS|FAIL|DESIGN OK|DESIGN CHANGES)\b")
    out = one_session(host, prof, model, effort, worktree, prompt, "review",
                      lambda msg: bool(marker.match(report_line(msg))), a.turn_timeout_hours * 3600)
    after = head_commit(worktree)
    out.update(host=host, model=model, effort=effort, module=a.module, milestone=a.milestone, commit=after,
               overreach=reviewer_overreach(worktree, prof, a.module, before, after))
    emit("REVIEWED" if out.pop("result") == "FINISHED" else "UNFINISHED", **out)


def cmd_plan(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    host, model, effort = resolve(a, prof, "plan")
    prompt = PLAN_TEMPLATE.format(model=model, effort=effort, task=a.task)
    out = one_session(host, prof, model, effort, worktree, prompt, "plan", lambda msg: bool(msg.strip()),
                      a.turn_timeout_hours * 3600, max_turns=1)
    out.update(host=host, model=model, effort=effort, commit=head_commit(worktree))
    emit("PLANNED" if out.pop("result") == "FINISHED" else "UNFINISHED", **out)


def cmd_ready(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree)
    all_done = integrated_done(worktree, prof)
    out = {"ready": [], "waiting": [], "review_owed": [], "finished": [], "invalid": {}}
    for module, done in all_done.items():
        if problems := validate(done):
            out["invalid"][module] = problems[:10]
            continue
        open_left = False
        for m in done["milestones"]:
            if awaiting_review(m, done):
                out["review_owed"].append({"module": module, "milestone": m["id"]})
                open_left = True
                break
            if m.get("state") in ("open", "in_progress"):
                open_left = True
                if blockers := unmet(m, module, all_done):
                    out["waiting"].append({"module": module, "milestone": m["id"], "needs": blockers})
                else:
                    out["ready"].append({"module": module, "milestone": m["id"], "state": m["state"]})
                break  # milestones in a module run in order; only the first open one counts
        if not open_left:
            out["finished"].append({"module": module, "parked": [m["id"] for m in done["milestones"]
                                                                 if m.get("state") == "parked"]})
    print(json.dumps(out, indent=2))


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
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree)
    done = load_done(worktree, a.module, prof)
    for problem in validate(done):
        print(f"invalid: {problem}")
    others = integrated_done(worktree, prof) if any(m.get("needs") for m in done["milestones"]) else {}
    for m in done["milestones"]:
        flag = "\treview owed" if awaiting_review(m, done) else ""
        if m.get("state") in ("open", "in_progress") and (blockers := unmet(m, a.module.upper(), others)):
            flag += "\twaiting on " + ", ".join(blockers)
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
    def host_args(p):
        p.add_argument("--host", help="codex, claude, or a host named in the profile (default codex)")
        p.add_argument("--model", help="default: the profile's model for the host")
        p.add_argument("--effort", help="default: medium (high for planners), or the profile's Effort")
        p.add_argument("--turn-timeout-hours", type=float, default=2.0)

    run = sub.add_parser("run")
    run.add_argument("--module", required=True)
    run.add_argument("--worktree", required=True)
    run.add_argument("--milestone")
    run.add_argument("--fresh", action="store_true", help="start a new session even if one exists")
    run.add_argument("--message", help="first prompt on resume, e.g. the reviewer's findings message")
    run.add_argument("--budget-hours", type=float, default=4.0)
    host_args(run)
    run.set_defaults(func=cmd_run)
    review = sub.add_parser("review")
    for flag in ("--module", "--milestone", "--commit", "--worktree"):
        review.add_argument(flag, required=True)
    host_args(review)
    review.set_defaults(func=cmd_review)
    plan = sub.add_parser("plan")
    plan.add_argument("--worktree", required=True)
    plan.add_argument("--task", required=True)
    host_args(plan)
    plan.set_defaults(func=cmd_plan)
    ready = sub.add_parser("ready")
    ready.add_argument("--worktree", required=True)
    ready.set_defaults(func=cmd_ready)
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
