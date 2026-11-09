#!/usr/bin/env python3
"""Drives builders, reviewers and planners for the orchestrate process on any supported agent host, with model and
effort named at every launch, and decides itself which work is accepted.

Used by the `build` lead (on any host that can run shell commands) and runnable by hand. Project settings come from
ORCHESTRATE.md at the worktree root (`profile` prints what was read). Needs git, plus the CLI of each host it
launches. POSIX only (fcntl, process groups).

Hosts:
  codex    `codex exec`, resumable, with goals, pinned-turn checks and a quota forecast from Codex's local files.
  claude   `claude -p` with stream-json, resumable, launched with no API key in its environment so it uses the
           signed-in plan. Reviewers and planners use the installed orchestrate agent files when present.
  <name>   any other CLI, from a `- **Host <name>:** <command>` line in the profile, with {prompt}, {model}, {effort}
           and {cwd} placeholders. Each turn is a fresh process; the files carry state between turns.
  With no --host, the host is the profile's `Default host`, else the host this command runs inside, else the only
  one installed, else codex.

What the loop owns. Next to each done-when file it keeps `<MODULE>-ACCEPTED.json`, which only the loop writes and
which is committed, so every worktree, clone and lead sees the same thing. Per milestone it holds the authorised hash
of the acceptance definitions, the claim the loop checked (code commit and the integrated tip it ran the checks on),
the reviews that judged it, and whether it was accepted, by checks, a reviewer or the owner. It also holds the
module's design review. A milestone is finished only when the record accepts it with its current definitions; a
`done` state in the done-when file isn't enough. A module with no record yet is adopted as it stands at the
integrated tip the first time the loop reads it.

The loop reruns checks with your own permissions, outside any host's sandbox, in a clean checkout of the integrated
tip. It pins the check strings, but a script a check calls can still be changed by the builder, so review new check
scripts.

Subcommands:

  run   --module CORE --worktree PATH [--host H] [--model M] [--effort E] [--milestone M2] [--fresh]
        [--message TEXT] [--budget-hours 4]
        Starts (or resumes) a builder session on the module's next milestone and drives it one turn at a time until:
        CLAIMED       the claim holds: the done-when file is valid and only the builder's own fields changed, the
                      milestone's state is `claimed` (or `done` when it needs no review), every item is `pass` with
                      evidence, the tree is clean, HEAD is on the integrated tip (fetched fresh), and the profile's
                      Check and every item's `check` exit 0 in a clean checkout of that tip. `review` says whether a
                      reviewer must judge it, `commit` is the commit to review and `checked` the tip the checks ran
                      on. A milestone that needs no review is accepted there and then.
        BLOCKED       the builder can't go on; the loop records `state: blocked` and what unblocks it
        NEEDS_CONTEXT the agent's final report line
        UNCLAIMED     the agent said DONE (or its goal completed) three times without a claim that holds
        INVALID       the done-when file is malformed, or something outside the builder's fields changed
        REVIEW_OWED   the module's next milestone is claimed and waiting for review
        DESIGN_OWED   the module's design hasn't passed a design review (or changed since it did)
        WAITING       the next milestone needs milestones in other modules that aren't accepted yet
        PARKED / FINISHED   the module stops at a parked milestone / has nothing left
        TAKEN         another lead or run holds this module or milestone
        BUDGET        no new passing item, and no commit of the builder's own outside the plans folder, for
                      --budget-hours
        FLOOR         two failed turns in a row, the host CLI is missing, the integrated tip can't be fetched, or
                      the goal is usage- or budget-limited (likely quota, sign-in or outage)
        PIN           a turn ran on a model or effort other than the named ones
        PAUSED        `pause` stopped it, or the Codex goal is paused; `run` again carries on
        A run on the same milestone resumes its session (with --message as the first prompt, e.g. the reviewer's
        findings) unless --fresh is given or the host, model or effort changed. A new milestone starts a new session.
        --milestone only confirms which milestone you expect; it never skips one that comes first.
        Prints one JSON line with the result as the last line of output.

  review --module CORE --milestone M2 --commit SHA --worktree PATH [--host H] [--model M] [--effort E]
        Runs a fresh reviewer in a clean checkout of the claimed commit (or of the integrated tip, with --milestone
        design), then checks what it did: only the review file and the reviewer's own fields changed, the verdicts
        agree with its last line, and a fail added 1 to `fails`. If all holds, the loop lands the review itself,
        sets failed items back to open, and records the verdict. REVIEWED, INVALID (nothing landed), or the host's
        FLOOR, PIN or PAUSED.

  plan  --worktree PATH --task TEXT [--host H] [--model M] [--effort high]
        Runs a fresh planner in a clean worktree, checks its done-when files, commits and lands whatever it left,
        and authorises the new definitions (resetting proof on milestones whose definitions changed). PLANNED lists
        the modules whose design review is now owed.

  land  --worktree PATH [--no-check]
        Integrates the worktree's commits under the integrate lock: rebase onto the base, run the profile's Check,
        then push (Integrate: push) or fast-forward the local branch (Integrate: local). Builders use this.

  ready [--worktree PATH]       What each module's next milestone is waiting for, read at the integrated tip.
  status [--module CORE] --worktree PATH   Every milestone with its state, blockers and last verdict.
  next  --module CORE --worktree PATH --milestone M2   The escalation after a failed review (see done-when.md).
  unblock --module CORE --milestone M2 --worktree PATH   Puts a blocked milestone back in the queue.
  pause [--module CORE] --worktree PATH   Stops running loops in this repository, and their agents, cleanly.
  owner accept|rereview|unpark|scope|release --module CORE --milestone M2|design --worktree PATH --reason TEXT
        Owner decisions, typed at a terminal by the owner; refused inside any session the loop started.
  quota        Forecasts the weekly Codex limit from the last day of use across all sessions.
  profile --worktree PATH       Prints the settings read from ORCHESTRATE.md, or exits 1 naming what's wrong.
  lock [--worktree PATH] NAME -- COMMAND...
        Runs COMMAND under a named lock shared by every worktree of the repository (not the whole machine).

Per-worktree session state lives in <git dir>/orchestrate/<module>.json, so re-running the same command resumes.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import argparse
import copy
import fcntl
import glob
import hashlib
import json
import os
import re
import shlex
import shutil
import signal
import socket
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
STATES = {"open", "in_progress", "claimed", "done", "blocked", "parked"}
STATUSES = {"open", "pass"}
VERDICTS = {"", "pass", "fail", "cant_tell"}
DEFINITION_KEYS = ("statement", "check", "inspect", "ask", "target", "lock", "attended")
TEXT_KEYS = DEFINITION_KEYS + ("evidence", "review")
NEED = re.compile(r"^(?:([A-Za-z0-9_.-]+):)?([A-Za-z0-9_.-]+)$")  # "M2" in this module, or "CORE:M3"
TRAILER = "Orchestrate-Loop: yes"
CLAIMS = "refs/orchestrate/claims"

LOOP = Path(__file__).resolve()
SKILLS = LOOP.parents[2]  # the folder holding build, build-milestone, review-milestone and plan-module

GOAL_LINE = "Call your create_goal tool with this objective, then work it.\n\n"

BUILD_TEMPLATE = """Model {model}, effort {effort}. {goal}Objective: milestone {milestone} of module {module} is \
claimed. That means every item for {milestone} in {done} has status pass with evidence from its named target, the \
milestone's state is claimed (or done, if no item has inspect or ask and it isn't the module's last milestone), and \
the work is committed and integrated.

Use the build-milestone skill ({skill}) for method, constraints and permissions. Work only in this worktree. Change \
only {milestone}'s state and its items' status and evidence; the rest of the done-when file belongs to the planner \
and reviewer, and the loop stops the run if anything else in it changes. Items with `attended` need a person or \
hardware you can't reach: do everything else first, then end with BLOCKED and list them. If the milestone needs \
something another module owns that isn't there yet, don't build it here: end with BLOCKED and name it. Integrate with \
`python3 {loop} land --worktree .`, which rebases, runs the profile's Check and integrates under the integrate lock. \
Take other exclusive resources with `python3 {loop} lock <name> -- <command>`.

Don't launch a reviewer; the lead runs review. End with DONE and the evidence when the claim is made. If you're \
blocked (probed directly) or missing context, end with `BLOCKED: ...` (what would unblock it) or \
`NEEDS_CONTEXT: ...`, with the evidence."""

REVIEW_TEMPLATE = """Model {model}, effort {effort}. Use the review-milestone skill ({skill}) to review milestone \
{milestone} of module {module}. This folder is a clean checkout of commit {commit}, made for you by the loop; build \
and run the product from it. The done-when file is {done}. Write the review to {review}, and set the verdict fields, \
state and fails as the skill says. Don't commit, push or change anything else: the loop checks what you changed, \
then integrates the review itself. Don't launch other agents. End with the skill's last line."""

DESIGN_REVIEW_TEMPLATE = """Model {model}, effort {effort}. Use the review-milestone skill ({skill}) to review the \
design of module {module}, as its "Reviewing a design" section describes. This folder is a clean checkout of the \
integrated tip. Write the review to {review} and change nothing else; the loop integrates it. Don't launch other \
agents. End with the skill's last line."""

PLAN_TEMPLATE = """Model {model}, effort {effort}. Use the plan-module skill ({skill}) for this task: {task}

You can't launch other agents. The loop commits and integrates the files you leave, and records the new \
definitions; never edit a *-ACCEPTED.json file. End with what changed, the files changed, and any decision the owner \
must make."""

FINDINGS_TEMPLATE = """The reviewer failed {milestone}: see {evidence}/{module}/{milestone}-review.md. The loop has \
set the items that didn't pass back to open, so each needs fresh evidence. Every finding counts, including cant_tell \
items (they need evidence the reviewer could reach) and defects outside the items. Add them to the plan as work \
items, fix them, re-verify the affected items, integrate, set the state back to claimed, and end with DONE, BLOCKED \
or NEEDS_CONTEXT."""


class TipError(Exception):
    pass


# ---------------------------------------------------------------------------------------------------------- profile

PROFILE_FIELDS = {"plans": "docs/modules", "evidence": "docs/evidence", "check": None, "branch": "main",
                  "remote": "origin", "integrate": None, "codex sandbox": "workspace-write", "writable roots": "",
                  "graded examples": "", "effort": "", "claude permissions": "auto", "default host": ""}
REQUIRED = {"check": "the command that must pass before integrating, or `none`",
            "integrate": "push (standing permission to push) or local"}
ONE_WORD = {"branch", "remote", "integrate", "codex sandbox", "effort", "claude permissions", "default host"}
ALLOWED = {"codex sandbox": {"workspace-write", "danger-full-access"}, "integrate": {"push", "local"},
           "effort": EFFORTS, "claude permissions": {"auto", "acceptEdits", "bypassPermissions", "dontAsk"}}
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>]*>")  # "<where review files go>", not "cmd < input"


def profile_value(text: str, label: str) -> str | None:
    m = re.search(rf"^\s*[-*]\s*\*\*{re.escape(label)}:\*\*[ \t]*(.*)$", text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    raw = re.sub(r"\*\(.*?\)\*", "", m.group(1))         # trailing *(read by the loop)* notes
    raw = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw)  # markdown links keep their text
    return raw.replace("`", "").strip()


def profile(worktree: Path, strict: bool = False) -> dict:
    """Reads the loop's settings from ORCHESTRATE.md (`- **Label:** value` lines). `Integrate` and `Check` must be
    there, because silently pushing, or integrating with no gate, isn't something to default into. A missing
    profile, or a missing, unfilled or invalid value, raises SystemExit when strict, and falls back to safe defaults
    (local integration, no Check) with a warning otherwise."""
    path = worktree / "ORCHESTRATE.md"
    problems = [] if path.exists() else [f"no ORCHESTRATE.md in {worktree}"]
    text = path.read_text() if path.exists() else ""
    out = {}
    for key, default in PROFILE_FIELDS.items():
        value = profile_value(text, key)
        if key in ONE_WORD and value:
            value = value.split()[0]
        if not value:
            if key in REQUIRED and path.exists():
                problems.append(f"{key}: missing ({REQUIRED[key]})")
            out[key] = default
        elif PLACEHOLDER.search(value) or (key in ALLOWED and value not in ALLOWED[key]):
            problems.append(f"{key}: {value!r}")
            out[key] = default
        else:
            out[key] = value.rstrip("/") if key in ("plans", "evidence") else value
    out["integrate"] = out["integrate"] or "local"
    out["check"] = "" if (out["check"] or "none").lower() == "none" else out["check"]
    out["effort"] = out["effort"] or DEFAULT_EFFORT
    out["models"] = dict(DEFAULT_MODELS)
    for m in re.finditer(r"^\s*[-*]\s*\*\*([\w.-]+) model:\*\*[ \t]*(.*)$", text, re.IGNORECASE | re.MULTILINE):
        value = re.sub(r"\*\(.*?\)\*", "", m.group(2)).replace("`", "").strip().split()
        if value and not PLACEHOLDER.search(value[0]):
            out["models"][m.group(1).lower()] = value[0]
    out["hosts"] = {}
    for m in re.finditer(r"^\s*[-*]\s*\*\*Host ([\w.-]+):\*\*[ \t]*(.*)$", text, re.IGNORECASE | re.MULTILINE):
        name, command = m.group(1).lower(), re.sub(r"\*\(.*?\)\*", "", m.group(2)).replace("`", "").strip()
        if name in ("codex", "claude") or "{prompt}" not in command:
            problems.append(f"host {name}: {command!r} (needs a {{prompt}} placeholder, and codex and claude are built in)")
        else:
            out["hosts"][name] = command
    gen = re.search(r"\*\*Codex generator:\*\*[ \t]*(.*)$", text, re.MULTILINE)  # older profiles
    if gen:
        m = re.match(r"`?([\w.\-]+)`?[ ,]+`?(\w+)`?", re.sub(r"\*\(.*?\)\*", "", gen.group(1)).strip())
        if m and m.group(2) in EFFORTS and "<" not in gen.group(1):
            out["models"]["codex"], out["effort"] = m.group(1), m.group(2)
        else:
            problems.append(f"codex generator: {gen.group(1).strip()!r} (want '<model> <effort>', effort one of "
                            f"{', '.join(sorted(EFFORTS))})")
    out["model"] = out["models"]["codex"]
    out["sandbox"] = out.pop("codex sandbox")
    out["claude_permissions"] = out.pop("claude permissions")
    out["default_host"] = out.pop("default host").lower()
    out["roots"] = [r.strip() for r in out.pop("writable roots").split(",") if r.strip()]
    out["graded_examples"] = out.pop("graded examples") or f"{out['evidence']}/graded-examples.md"
    if problems:
        message = "ORCHESTRATE.md has missing, unfilled or invalid fields: " + "; ".join(problems)
        if strict:
            raise SystemExit(message)
        print("warning: " + message, file=sys.stderr)
    return out


def codex_flags(prof: dict, role: str = "build") -> list[str]:
    flags = ["-m", prof["model"], "-c", f"model_reasoning_effort={prof['effort']}",
             "-c", "approval_policy=on-request", "-c", "approvals_reviewer=auto_review",
             "-c", f"sandbox_mode={prof['sandbox']}"]
    if role in ("review", "plan"):
        flags += ["-c", "features.multi_agent=false"]  # the twin of Claude's --disallowedTools Agent
    if prof["sandbox"] == "workspace-write":
        flags += ["-c", "sandbox_workspace_write.network_access=true"]
        if prof["roots"]:
            roots = ",".join(json.dumps(str(Path(r).expanduser())) for r in prof["roots"])
            flags += ["-c", f"sandbox_workspace_write.writable_roots=[{roots}]"]
    return flags


def codex_supports(flag: str) -> bool:
    try:
        out = subprocess.run([CODEX, "exec", "--help"], capture_output=True, text=True)
    except OSError:
        return False
    return flag in out.stdout


# ------------------------------------------------------------------------------------------------------------- git

def git(worktree: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, text=True, input=stdin)


def ident(worktree: Path) -> list[str]:
    """Identity flags for commits the loop makes, when the repository has no identity of its own."""
    if git(worktree, "config", "user.email").stdout.strip():
        return []
    return ["-c", "user.name=orchestrate loop", "-c", "user.email=orchestrate@localhost"]


def head_commit(worktree: Path) -> str:
    return git(worktree, "rev-parse", "HEAD").stdout.strip()


def git_common_dir(worktree: Path) -> str:
    out = subprocess.run(["git", "-C", str(worktree), "rev-parse", "--git-common-dir"], capture_output=True, text=True)
    return str((worktree / out.stdout.strip()).resolve())


def loop_dir(worktree: Path) -> Path:
    path = Path(git_common_dir(worktree)) / "orchestrate"
    path.mkdir(parents=True, exist_ok=True)
    return path


def base_ref(prof: dict) -> str:
    return f"{prof['remote']}/{prof['branch']}" if prof["integrate"] == "push" else prof["branch"]


def tip(worktree: Path, prof: dict, fetch: bool = True) -> str:
    """The integrated tip's commit: the remote branch after a fresh fetch, or the local branch. Raises TipError
    rather than falling back to something staler, because readiness judged on a stale tip is wrong."""
    if prof["integrate"] == "push" and fetch:
        f = git(worktree, "fetch", "--quiet", prof["remote"], prof["branch"])
        if f.returncode != 0:
            raise TipError(f"git fetch {prof['remote']} {prof['branch']} failed: {f.stderr.strip()[-300:]}")
        git(worktree, "update-ref", f"refs/remotes/{prof['remote']}/{prof['branch']}", "FETCH_HEAD")
    r = git(worktree, "rev-parse", "--verify", "--quiet", base_ref(prof) + "^{commit}")
    if r.returncode != 0:
        raise TipError(f"can't read {base_ref(prof)}")
    return r.stdout.strip()


def show(worktree: Path, ref: str, path: str) -> str | None:
    r = git(worktree, "show", f"{ref}:{path}")
    return r.stdout if r.returncode == 0 else None


def is_ancestor(worktree: Path, a: str, b: str) -> bool:
    return git(worktree, "merge-base", "--is-ancestor", a, b).returncode == 0


def changed_paths(tree: Path, start: str) -> list[str]:
    """Every path that differs from `start`: commits since it, staged and unstaged edits, and untracked files."""
    names = set(git(tree, "diff", "--name-only", start).stdout.split("\n"))
    names |= set(git(tree, "ls-files", "--others", "--exclude-standard").stdout.split("\n"))
    return sorted(n for n in names if n)


def sync_worktree(worktree: Path, prof: dict) -> None:
    """Fast-forwards a clean worktree that's behind the integrated tip, so a warm worktree doesn't start a milestone
    from old files. A worktree with uncommitted or unintegrated work is left for its builder to rebase."""
    try:
        ref = tip(worktree, prof)
    except TipError:
        return
    if not git(worktree, "status", "--porcelain").stdout.strip() and is_ancestor(worktree, "HEAD", ref):
        git(worktree, "merge", "--ff-only", "--quiet", ref)


def own_progress(worktree: Path, seen: int, plans: str) -> tuple[bool, int]:
    """Whether this worktree's HEAD gained a commit of its own (made here or replayed by a rebase) that touches
    anything outside the plans folder, since `seen` reflog entries. Commits a rebase brought in from upstream
    aren't the builder's progress, and they don't appear as commits in this reflog."""
    lines = git(worktree, "reflog", "--format=%H%x09%gs", "HEAD").stdout.splitlines()
    fresh = lines[:max(0, len(lines) - seen)]
    for line in fresh:
        sha, _, subject = line.partition("\t")
        if subject.startswith(("commit", "rebase (pick)", "rebase (continue)", "rebase (reword)", "cherry-pick")):
            names = git(worktree, "show", "--name-only", "--format=", sha).stdout.split()
            if any(not n.startswith(plans.rstrip("/") + "/") for n in names):
                return True, len(lines)
    return False, len(lines)


# ------------------------------------------------------------------------------------------------- done-when file

def module_stem(worktree: Path, prof: dict, module: str) -> str:
    """The module's name as its files spell it, found without regard to case."""
    folder = worktree / prof["plans"]
    for path in sorted(folder.glob("*-DONE.json")) if folder.exists() else []:
        if path.name[:-len("-DONE.json")].upper() == module.upper():
            return path.name[:-len("-DONE.json")]
    raise SystemExit(f"error: {folder}/{module}-DONE.json doesn't exist; the module needs planning (/plan-module) first")


def done_rel(prof: dict, stem: str) -> str:
    return f"{prof['plans']}/{stem}-DONE.json"


def record_rel(prof: dict, stem: str) -> str:
    return f"{prof['plans']}/{stem}-ACCEPTED.json"


def load_done(worktree: Path, module: str, prof: dict | None = None) -> dict:
    prof = prof or profile(worktree)
    path = worktree / done_rel(prof, module_stem(worktree, prof, module))
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return {"unreadable": f"{path.name} isn't valid JSON: {e}"}


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def is_count(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate(done, module: str = "") -> list[str]:
    """The structural problems that would let a claim through without proof, or leave the queue stuck."""
    if isinstance(done, dict) and done.get("unreadable"):
        return [done["unreadable"]]
    if not isinstance(done, dict) or not isinstance(done.get("milestones"), list) or not done["milestones"]:
        return ["the file needs a non-empty \"milestones\" list"]
    problems, seen = [], set()
    order = [m.get("id") if isinstance(m, dict) else None for m in done["milestones"]]
    for index, m in enumerate(done["milestones"]):
        if not isinstance(m, dict):
            problems.append(f"milestone {index + 1} isn't an object")
            continue
        mid = m.get("id")
        if not isinstance(mid, str) or not mid:
            problems.append(f"milestone {index + 1} has no string id")
            mid = f"#{index + 1}"
        if mid in seen:
            problems.append(f"duplicate milestone id {mid}")
        seen.add(mid)
        if m.get("state") not in STATES:
            problems.append(f"{mid}: state {m.get('state')!r} isn't one of {sorted(STATES)}")
        if m.get("state") == "blocked" and not m.get("blocked"):
            problems.append(f"{mid}: blocked, but \"blocked\" doesn't say what unblocks it")
        for counter in ("fails", "replans"):
            if not is_count(m.get(counter, 0)):
                problems.append(f"{mid}: {counter} {m.get(counter)!r} isn't a whole number of 0 or more")
        items = m.get("items")
        if not isinstance(items, list) or not items:
            problems.append(f"{mid}: no items")
            items = []
        for item in items:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item.get("id"):
                problems.append(f"{mid}: an item has no string id")
                continue
            iid = item["id"]
            if iid in seen:
                problems.append(f"duplicate item id {iid}")
            seen.add(iid)
            bad = [k for k in TEXT_KEYS if k in item and not isinstance(item[k], str)]
            if bad:
                problems.append(f"{iid}: {', '.join(bad)} should be text")
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
            continue
        for need in needs:
            other, target = NEED.match(need).groups()
            if other and other.upper() != module.upper():
                continue
            if target not in order:
                problems.append(f"{mid}: needs {target}, which isn't in this module")
            elif order.index(target) >= index:
                problems.append(f"{mid}: needs {target}, which comes at or after it, so it can never start "
                                "(milestones in a module run in order)")
    return problems


def definitions(milestone: dict) -> str:
    """A hash of what the milestone asks for, as opposed to what anyone has claimed about it."""
    spec = {"bar": milestone.get("bar"), "needs": milestone.get("needs") or [],
            "items": [{k: i.get(k) for k in DEFINITION_KEYS} for i in milestone["items"]]}
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def text_hash(text: str | None) -> str:
    return hashlib.sha256((text or "").encode()).hexdigest()


def find(done: dict, mid: str) -> dict:
    for m in done["milestones"]:
        if m["id"] == mid:
            return m
    raise SystemExit(f"error: milestone {mid} not in done-when file")


def needs_review(milestone: dict, done: dict) -> bool:
    """`inspect` and `ask` need the reviewer's judgement, and so does the module's last milestone, whose review reads
    the whole module. Other milestones close on their checks."""
    return milestone["id"] == done["milestones"][-1]["id"] or \
        any(i.get("inspect") or i.get("ask") for i in milestone["items"])


def needs_of(milestone: dict, module: str) -> list[tuple[str, str]]:
    """The milestone's `needs` as (MODULE, milestone) pairs; a bare id means this module."""
    out = []
    for need in milestone.get("needs") or []:
        m = NEED.match(str(need))
        if m:
            out.append(((m.group(1) or module).upper(), m.group(2)))
    return out


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


def reset_proof(milestone: dict, only_failed: bool = False) -> None:
    """Clears claims so the next claim is verified afresh. After a failed review only the items that didn't pass
    reset, unless they all passed and the failure was outside the items."""
    items = milestone["items"]
    if only_failed and any(i.get("verdict") != "pass" for i in items):
        items = [i for i in items if i.get("verdict") != "pass"]
    for i in items:
        i["status"], i["evidence"] = "open", ""
        if not only_failed:
            i["verdict"], i["review"] = "", ""


# ------------------------------------------------------------------------------------------------ deltas by role

BUILDER_FIELDS = {"state"}, {"status", "evidence"}
REVIEWER_FIELDS = {"state", "fails"}, {"verdict", "review"}


def delta_problems(before: dict | None, after: dict, role: str, mid: str | None = None,
                   upstream: list | dict | None = None) -> list[str]:
    """What the role changed in a done-when file that it doesn't own. `upstream` holds other versions the file may
    legitimately match field by field: the loop's own writes that a rebase brought in."""
    if isinstance(upstream, dict):
        upstream = [upstream]
    problems = []
    if role == "plan":
        old = {m.get("id"): m for m in (before or {}).get("milestones", [])}
        for m in after["milestones"]:
            was = old.get(m["id"], {})
            if m.get("state") in ("claimed", "done") and was.get("state") != m.get("state"):
                problems.append(f"{m['id']}: a planner can't set state {m['state']}")
            was_items = {i.get("id"): i for i in was.get("items", [])}
            for i in m["items"]:
                w = was_items.get(i["id"], {})
                for key in ("status", "verdict"):
                    if i.get(key) == "pass" and w.get(key) != "pass":
                        problems.append(f"{i['id']}: a planner can't set {key} pass")
        return problems
    ids = lambda d: [m.get("id") for m in d["milestones"]]
    top = lambda d: {k: v for k, v in d.items() if k != "milestones"}
    versions = [v for v in [before, *(upstream or [])] if isinstance(v, dict) and ids(v) == ids(after)]
    if not versions:
        return ["added, removed or reordered milestones"]
    if all(top(after) != top(v) for v in versions):
        problems.append("changed the file's top-level fields")
    own_m, own_i = BUILDER_FIELDS if role == "build" else REVIEWER_FIELDS if role == "review" else (set(), set())
    item_ids = lambda m: [i.get("id") for i in m.get("items", [])]
    for index, a in enumerate(after["milestones"]):
        olds = [v["milestones"][index] for v in versions]
        if a["id"] != mid or role == "design":
            if all(a != b for b in olds):
                problems.append(f"{a['id']}: changed, but this {role} was given " + (mid or "the design"))
            continue
        b = olds[0]
        keys = (set(a) | set(b)) - own_m - {"items"}
        bad = sorted(k for k in keys if all(a.get(k) != o.get(k) for o in olds))
        if bad:
            problems.append(f"{mid}: changed {', '.join(bad)}, which belong to someone else")
        olds = [o for o in olds if item_ids(o) == item_ids(a)]
        if not olds:
            problems.append(f"{mid}: added, removed or reordered items")
            continue
        for n, ai in enumerate(a["items"]):
            others = [o["items"][n] for o in olds]
            bad = sorted(k for k in (set(ai) | set(others[0])) - own_i if all(ai.get(k) != o.get(k) for o in others))
            if bad:
                problems.append(f"{ai['id']}: changed {', '.join(bad)}, which belong to someone else")
        if role == "build" and a.get("state") not in ("open", "in_progress", "claimed", "done"):
            problems.append(f"{mid}: a builder can't set state {a.get('state')}")
        if role == "review":
            if b.get("state") != "claimed":
                problems.append(f"{mid}: was {b.get('state')}, not claimed, so there was nothing to review")
            elif a.get("state") == "done" and a.get("fails", 0) != b.get("fails", 0):
                problems.append(f"{mid}: a pass doesn't change fails")
            elif a.get("state") == "in_progress" and a.get("fails", 0) != b.get("fails", 0) + 1:
                problems.append(f"{mid}: a fail adds exactly 1 to fails")
            elif a.get("state") not in ("done", "in_progress"):
                problems.append(f"{mid}: a review sets state done (pass) or in_progress (fail), not {a.get('state')}")
    return problems


# ---------------------------------------------------------------------------------------- the acceptance record

def adopt(doc: dict, design: str) -> dict:
    """The record for a module the loop hasn't seen before, taken as it stands: its definitions authorised, and its
    finished milestones accepted. A module already part-built is taken to have had its design agreed."""
    rec = {"module": doc.get("module"), "adopted": True, "design": None, "milestones": {}}
    for m in doc["milestones"]:
        entry = {"definitions": definitions(m), "authorised": {"by": "adopted"}, "reviews": []}
        if m.get("state") == "done" and (not needs_review(m, doc) or
                                         all(i.get("verdict") == "pass" for i in m["items"])):
            entry["accepted"] = {"by": "adopted"}
        rec["milestones"][m["id"]] = entry
    if any(e.get("accepted") for e in rec["milestones"].values()):
        rec["design"] = {"verdict": "ok", "hash": design, "by": "adopted"}
    return rec


def entry(rec: dict, mid: str) -> dict:
    return rec.setdefault("milestones", {}).setdefault(mid, {"reviews": []})


def accepted(m: dict, rec: dict) -> bool:
    e = rec.get("milestones", {}).get(m["id"]) or {}
    return m.get("state") == "done" and bool(e.get("accepted")) and e.get("definitions") == definitions(m)


def authorised(m: dict, rec: dict) -> bool:
    return (rec.get("milestones", {}).get(m["id"]) or {}).get("definitions") == definitions(m)


def design_ok(rec: dict, design: str) -> bool:
    d = rec.get("design") or {}
    return d.get("verdict") == "ok" and d.get("hash") == design


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def project(worktree: Path, prof: dict, ref: str) -> dict[str, dict]:
    """Every module at `ref`: {MODULE: {stem, doc, record, design, problems}}, with records adopted where missing."""
    out = {}
    listing = git(worktree, "ls-tree", "--name-only", f"{ref}:{prof['plans']}")
    for name in listing.stdout.split() if listing.returncode == 0 else []:
        if not name.endswith("-DONE.json"):
            continue
        stem = name[:-len("-DONE.json")]
        key = stem.upper()
        try:
            doc = json.loads(show(worktree, ref, f"{prof['plans']}/{name}") or "")
        except json.JSONDecodeError as e:
            doc = {"unreadable": f"{name} isn't valid JSON: {e}"}
        design = text_hash(show(worktree, ref, f"{prof['plans']}/{stem}.md"))
        problems = validate(doc, key)
        rec_text = show(worktree, ref, record_rel(prof, stem))
        rec = None
        if rec_text is not None:
            try:
                rec = json.loads(rec_text)
            except json.JSONDecodeError as e:
                problems.append(f"{stem}-ACCEPTED.json isn't valid JSON: {e}")
        if rec is None and not problems:
            rec = adopt(doc, design)
        out[key] = {"stem": stem, "doc": doc, "record": rec or {"milestones": {}}, "design": design,
                    "problems": problems}
    return out


def need_cycles(proj: dict) -> dict[str, str]:
    """Modules caught in a cycle of needs (counting the order of milestones within a module), with the cycle."""
    edges = {}
    for key, e in proj.items():
        if e["problems"]:
            continue
        ms = e["doc"]["milestones"]
        for index, m in enumerate(ms):
            deps = needs_of(m, key) + ([(key, ms[index - 1]["id"])] if index else [])
            edges[(key, m["id"])] = [d for d in deps if d != (key, m["id"])]
    found, done_nodes = {}, set()
    for start in edges:
        stack, path, on_path = [(start, iter(edges[start]))], [start], {start}
        while stack:
            node, children = stack[-1]
            child = next(children, None)
            if child is None:
                stack.pop()
                on_path.discard(path.pop())
                done_nodes.add(node)
            elif child in on_path:
                cycle = path[path.index(child):] + [child]
                text = " -> ".join(f"{a}:{b}" for a, b in cycle)
                for a, _ in cycle:
                    found.setdefault(a, text)
            elif child not in done_nodes and child in edges:
                stack.append((child, iter(edges[child])))
                path.append(child)
                on_path.add(child)
    return found


def next_step(key: str, proj: dict, claims: dict | None = None, me: str = "") -> dict:
    """What the module's next milestone is waiting for. The one predicate behind `ready`, `status` and `run`."""
    e = proj[key]
    base = {"module": e["stem"]}
    if e["problems"]:
        return {**base, "status": "invalid", "problems": e["problems"][:10]}
    doc, rec = e["doc"], e["record"]
    for m in doc["milestones"]:
        if accepted(m, rec):
            continue
        out = {**base, "milestone": m["id"], "name": m.get("name", ""), "state": m.get("state")}
        if not authorised(m, rec):
            return {**out, "status": "invalid", "problems": [
                f"{m['id']}: its definitions aren't the ones last authorised by a planner turn or the owner "
                f"(see {e['stem']}-ACCEPTED.json); re-plan it, or run `owner scope`"]}
        if m.get("state") == "parked":
            return {**out, "status": "parked"}
        if m.get("state") == "blocked":
            return {**out, "status": "blocked", "blocked": m.get("blocked", "")}
        if not design_ok(rec, e["design"]):
            return {**base, "status": "design_owed"}
        if m.get("state") == "claimed" or (m.get("state") == "done" and needs_review(m, doc)):
            claim = (rec["milestones"].get(m["id"]) or {}).get("claim") or {}
            return {**out, "status": "review_owed", "commit": claim.get("commit")}
        waiting, problems = [], []
        for mod, mid in needs_of(m, key):
            other = proj.get(mod)
            if other is None:
                waiting.append(f"{mod}:{mid} (not planned)")
                continue
            if other["problems"]:
                problems.append(f"needs {mod}:{mid}, but {mod}'s done-when file is invalid")
                continue
            target = next((x for x in other["doc"]["milestones"] if x.get("id") == mid), None)
            if target is None:
                problems.append(f"needs {mod}:{mid}, which isn't in {mod}'s done-when file")
            elif target.get("state") == "parked":
                problems.append(f"needs {mod}:{mid}, which is parked")
            elif not accepted(target, other["record"]):
                waiting.append(f"{mod}:{mid}")
        if problems:
            return {**out, "status": "invalid", "problems": [f"{m['id']}: {p}" for p in problems]}
        if waiting:
            return {**out, "status": "waiting", "needs": waiting}
        holder = (claims or {}).get((key, m["id"]))
        if holder and holder != me:
            return {**out, "status": "taken", "by": holder}
        return {**out, "status": "ready"}
    return {**base, "status": "finished"}


# -------------------------------------------------------------------------------------------- processes and locks

_STOP = False
_HELD = []  # open lock files, kept for the life of the process


def install_stop() -> None:
    """`pause` (SIGTERM) or Ctrl-C stops the current agent cleanly, and the loop reports PAUSED."""
    def handler(signum, frame):
        global _STOP
        _STOP = True
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


def kill_group(proc: subprocess.Popen) -> None:
    for sig, wait in ((signal.SIGTERM, 10), (signal.SIGKILL, 5)):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=wait)
            return
        except subprocess.TimeoutExpired:
            continue


def run_proc(args, cwd: Path | None, timeout_s: float, shell: bool = False,
             env: dict | None = None) -> tuple[int, str, str]:
    """Runs a command in its own process group, so a timeout or a pause stops everything it started. 124 means it
    timed out, 130 that it was stopped, 127 that the command couldn't start."""
    try:
        proc = subprocess.Popen(args, shell=shell, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True, start_new_session=True, env=env)
    except OSError as e:
        return 127, "", f"couldn't start {args[0] if isinstance(args, list) else args}: {e}"
    deadline = time.time() + timeout_s
    while True:
        try:
            out, err = proc.communicate(timeout=1.0)
            return proc.returncode, out, err
        except subprocess.TimeoutExpired:
            if _STOP or time.time() > deadline:
                kill_group(proc)
                out, err = proc.communicate()
                return (130 if _STOP else 124), out or "", (err or "") + ("\n(stopped)" if _STOP else "\n(timed out)")


@contextmanager
def held(name: str, worktree: Path):
    """Holds the repository-wide lock `name` for the duration of the block."""
    if not re.fullmatch(r"[\w.-]+", name):
        raise SystemExit(f"error: lock name {name!r} may only use letters, digits, '.', '_' and '-'")
    with open(Path(git_common_dir(worktree)) / f"orchestrate-{name}.lock", "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def run_lock(worktree: Path, name: str) -> bool:
    """Takes this process's exclusive hold on a module (or the planner) without waiting, and records the pid so
    `pause` can find it. False if another run holds it."""
    path = loop_dir(worktree) / f"run-{name}.lock"
    handle = open(path, "a+")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        handle.close()
        return False
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    _HELD.append(handle)
    return True


# --------------------------------------------------------------------------------------- integrating, as the loop

def verify_tree(worktree: Path, name: str, ref: str) -> Path:
    """A loop-owned checkout at `ref`, one per module, kept between uses so ignored build caches stay warm."""
    path = loop_dir(worktree) / "verify" / name.upper()
    if (path / ".git").exists():
        if git(path, "checkout", "--quiet", "--force", "--detach", ref).returncode == 0:
            git(path, "clean", "-ffdq")
            return path
        shutil.rmtree(path, ignore_errors=True)
    git(worktree, "worktree", "prune")
    path.parent.mkdir(parents=True, exist_ok=True)
    r = git(worktree, "worktree", "add", "--quiet", "--force", "--detach", str(path), ref)
    if r.returncode != 0:
        raise TipError(f"couldn't make a clean checkout at {path}: {r.stderr.strip()[-300:]}")
    return path


def holder_of(tree: Path, branch: str) -> Path | None:
    """The worktree that has `branch` checked out, if any."""
    current = None
    for line in git(tree, "worktree", "list", "--porcelain").stdout.splitlines():
        if line.startswith("worktree "):
            current = Path(line[len("worktree "):])
        elif line == f"branch refs/heads/{branch}":
            return current
    return None


def land(tree: Path, prof: dict, check: bool = False) -> tuple[bool, str]:
    """Integrates the commits in `tree` under the integrate lock: rebase onto the base, optionally run the profile's
    Check, then push (push) or fast-forward the local branch (local). Returns (ok, landed commit or the problem)."""
    detail = ""
    with held("integrate", tree):
        for _ in range(2):
            if prof["integrate"] == "push":
                f = git(tree, "fetch", "--quiet", prof["remote"], prof["branch"])
                if f.returncode != 0:
                    return False, f"git fetch failed: {f.stderr.strip()[-300:]}"
                git(tree, "update-ref", f"refs/remotes/{prof['remote']}/{prof['branch']}", "FETCH_HEAD")
            base = base_ref(prof)
            r = git(tree, *ident(tree), "rebase", "--quiet", base)
            if r.returncode != 0:
                git(tree, "rebase", "--abort")
                return False, f"rebase onto {base} failed: {(r.stdout + r.stderr).strip()[-400:]}"
            if check and prof["check"]:
                code, out, err = run_proc(prof["check"], tree, 3600, shell=True)
                if code != 0:
                    return False, f"Check `{prof['check']}` exited {code}: {(out + err)[-600:]}"
            new = head_commit(tree)
            if prof["integrate"] == "push":
                p = git(tree, "push", "--quiet", prof["remote"], f"HEAD:refs/heads/{prof['branch']}")
                if p.returncode == 0:
                    git(tree, "update-ref", f"refs/remotes/{prof['remote']}/{prof['branch']}", new)
                    return True, new
                detail = f"push rejected: {p.stderr.strip()[-300:]}"
                continue
            old = git(tree, "rev-parse", f"refs/heads/{prof['branch']}").stdout.strip()
            if old == new:
                return True, new
            holder = holder_of(tree, prof["branch"])
            if holder is None:
                u = git(tree, "update-ref", f"refs/heads/{prof['branch']}", new, old)
                if u.returncode == 0:
                    return True, new
                detail = f"{prof['branch']} moved: {u.stderr.strip()[-200:]}"
                continue
            m = git(holder, "merge", "--ff-only", "--quiet", new)
            if m.returncode == 0:
                return True, new
            return False, (f"couldn't fast-forward {prof['branch']} in {holder}, which has it checked out: "
                           f"{(m.stdout + m.stderr).strip()[-300:]}")
    return False, detail


def loop_write(worktree: Path, prof: dict, name: str, change, message: str) -> tuple[bool, str]:
    """Applies `change(tree)` to a clean checkout of the integrated tip, commits it as the loop, and lands it.
    `change` returns the paths it wrote, or nothing to skip the commit."""
    detail = ""
    for _ in range(2):
        try:
            tree = verify_tree(worktree, name, tip(worktree, prof))
        except TipError as e:
            return False, str(e)
        paths = change(tree)
        if not paths:
            return True, head_commit(tree)
        git(tree, "add", "--", *paths)
        c = git(tree, *ident(tree), "commit", "--quiet", "-m", f"{message}\n\n{TRAILER}")
        if c.returncode != 0:
            return False, f"commit failed: {(c.stdout + c.stderr).strip()[-300:]}"
        ok, detail = land(tree, prof)
        if ok:
            return True, detail
    return False, detail


def record_in(tree: Path, prof: dict, stem: str, doc: dict) -> dict:
    path = tree / record_rel(prof, stem)
    if path.exists():
        return json.loads(path.read_text())
    return adopt(doc, text_hash((tree / prof["plans"] / f"{stem}.md").read_text()
                                if (tree / prof["plans"] / f"{stem}.md").exists() else None))


def loop_versions(worktree: Path, rel: str, old: str, new: str, limit: int = 50) -> list[dict]:
    """The file at `rel` as each loop-made commit between two tips left it. A builder pushes to the same branch, so
    the base's copy alone can't tell a planner's or reviewer's change from the builder's own."""
    out = git(worktree, "log", f"-{limit}", "--format=%H%x00%B%x01", f"{old}..{new}").stdout
    versions = []
    for chunk in out.split("\x01"):
        sha, _, body = chunk.strip().partition("\x00")
        if sha and TRAILER in body and (text := show(worktree, sha, rel)):
            try:
                versions.append(json.loads(text))
            except json.JSONDecodeError:
                pass
    return versions


def record_tampering(worktree: Path, prof: dict, old: str, new: str) -> list[str]:
    """Commits between two tips that changed an acceptance record without being the loop's."""
    out = git(worktree, "log", "--format=%H%x00%B%x01", f"{old}..{new}", "--",
              f":(glob){prof['plans']}/*-ACCEPTED.json").stdout
    bad = []
    for chunk in out.split("\x01"):
        sha, _, body = chunk.strip().partition("\x00")
        if sha and TRAILER not in body:
            bad.append(sha[:12])
    return bad


# ---------------------------------------------------------------------------------------------- claims across clones

def me(worktree: Path) -> str:
    return f"{socket.gethostname()}:{git_common_dir(worktree)}"


def sync_claims(worktree: Path, prof: dict) -> None:
    if prof["integrate"] == "push":
        git(worktree, "fetch", "--quiet", "--prune", prof["remote"], f"+{CLAIMS}/*:{CLAIMS}/*")


def claims(worktree: Path) -> dict[tuple[str, str], str]:
    out = {}
    for line in git(worktree, "for-each-ref", "--format=%(refname)\t%(contents:subject)", CLAIMS).stdout.splitlines():
        ref, _, holder = line.partition("\t")
        parts = ref[len(CLAIMS) + 1:].split("/")
        if len(parts) == 2:
            out[(parts[0].upper(), parts[1])] = holder
    return out


def take_claim(worktree: Path, prof: dict, key: str, mid: str) -> tuple[bool, str]:
    """Claims the milestone with a ref no other lead can create at the same time: a new ref on the remote (push),
    or a local ref created only if absent (local). Two leads never start the same milestone."""
    sync_claims(worktree, prof)
    mine = me(worktree)
    holder = claims(worktree).get((key, mid))
    if holder:
        return holder == mine, holder
    empty = git(worktree, "mktree", stdin="").stdout.strip()
    sha = git(worktree, *ident(worktree), "commit-tree", empty, "-m", mine).stdout.strip()
    ref = f"{CLAIMS}/{key}/{mid}"
    if prof["integrate"] == "push":
        if git(worktree, "push", "--quiet", prof["remote"], f"{sha}:{ref}").returncode != 0:
            sync_claims(worktree, prof)
            holder = claims(worktree).get((key, mid), "another lead")
            return holder == mine, holder
        git(worktree, "update-ref", ref, sha)
        return True, mine
    if git(worktree, "update-ref", ref, sha, "0" * 40).returncode != 0:
        holder = claims(worktree).get((key, mid), "another lead")
        return holder == mine, holder
    return True, mine


def drop_claim(worktree: Path, prof: dict, key: str, mid: str) -> None:
    ref = f"{CLAIMS}/{key}/{mid}"
    if prof["integrate"] == "push":
        git(worktree, "push", "--quiet", prof["remote"], f":{ref}")
    git(worktree, "update-ref", "-d", ref)


# ---------------------------------------------------------------------------------------------- the claim itself

def check_failures(tree: Path, prof: dict, milestone: dict, timeout_s: float = 3600) -> list[str]:
    """Runs the profile's Check, then each item's check (under its lock, if it names one). Returns what failed."""
    runs = [("Check", prof.get("check"), None)] if prof.get("check") else []
    runs += [(i["id"], i["check"], i.get("lock")) for i in milestone["items"] if i.get("check")]
    failed = []
    for label, command, lock in runs:
        if lock:
            with held(lock, tree):
                code, out, err = run_proc(command, tree, timeout_s, shell=True)
        else:
            code, out, err = run_proc(command, tree, timeout_s, shell=True)
        if code != 0:
            failed.append(f"{label} `{command}` " + ("timed out" if code == 124 else f"exited {code}") +
                          f": {(out + err)[-600:]}")
    return failed


def claim_problems(worktree: Path, prof: dict, stem: str, milestone: dict, done: dict, authorised_hash: str,
                   start_tip: str) -> tuple[list[str], str | None]:
    """Why the claim doesn't hold yet, and the integrated tip the checks ran on."""
    if milestone.get("state") not in ("claimed", "done"):
        return ["set the milestone's state to claimed once every item passes"], None
    if milestone.get("state") == "done" and needs_review(milestone, done):
        return ["this milestone needs a reviewer, so set its state to claimed, not done"], None
    missing = [i["id"] for i in milestone["items"] if not i.get("evidence")]
    if missing:
        return ["items marked pass with no evidence: " + ", ".join(missing)], None
    status = git(worktree, "status", "--porcelain").stdout.strip()
    if status:
        return ["uncommitted or untracked files (commit, remove or ignore them): " + status[:300]], None
    try:
        ref = tip(worktree, prof)
    except TipError as e:
        return [f"{e}, so integration can't be checked"], None
    if not is_ancestor(worktree, "HEAD", ref):
        return [f"HEAD is not on {base_ref(prof)} yet; integrate with `python3 {LOOP} land --worktree .`"], None
    if bad := record_tampering(worktree, prof, start_tip, ref):
        return [f"commits changed an acceptance record, which only the loop writes: {', '.join(bad)}"], None
    try:
        at_tip = find(json.loads(show(worktree, ref, done_rel(prof, stem)) or "{}"), milestone["id"])
    except (json.JSONDecodeError, KeyError, SystemExit):
        return [f"{milestone['id']} can't be read at the integrated tip"], None
    if definitions(at_tip) != authorised_hash:
        return [f"{milestone['id']}'s definitions at the integrated tip aren't the authorised ones"], None
    try:
        tree = verify_tree(worktree, stem, ref)
    except TipError as e:
        return [str(e)], None
    failures = check_failures(tree, prof, milestone)
    if left := git(tree, "status", "--porcelain").stdout.strip():
        failures.append("running the checks left changes in a clean checkout of the tip (write outputs somewhere "
                        "git ignores): " + left[:300])
    if head_commit(tree) != ref:
        failures.append("running the checks moved HEAD in the clean checkout")
    return failures, ref


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


def forecast(samples: list[tuple[float, float, float]], now_s: float, window_h: float = 24.0) -> dict | None:
    """Burn rate over the last `window_h` hours of the current limit window, and when the limit runs out at that rate."""
    if not samples:
        return None
    _, used, resets_at = samples[-1]
    recent = [s for s in samples if s[2] == resets_at and s[0] >= now_s - window_h * 3600]
    out = {"used_percent": used, "resets_at": iso(resets_at)}
    if len(recent) < 2 or recent[-1][0] - recent[0][0] < 3600:
        return {**out, "per_day": None, "runs_out": None, "note": "not enough recent use to forecast"}
    per_day = (recent[-1][1] - recent[0][1]) / ((recent[-1][0] - recent[0][0]) / 86400)
    out["per_day"] = round(per_day, 1)
    if per_day <= 0:
        return {**out, "runs_out": None, "note": "no use in the window"}
    runs_out = now_s + (100 - used) / per_day * 86400
    if runs_out >= resets_at:
        return {**out, "runs_out": None, "note": f"lasts to the reset at this rate ({round(100 - used - per_day * (resets_at - now_s) / 86400)}% left then)"}
    return {**out, "runs_out": iso(runs_out),
            "note": f"runs out {round((resets_at - runs_out) / 3600)} h before the reset at this rate"}


def iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).astimezone().strftime("%a %d %b %H:%M")


def quota_now() -> dict | None:
    try:
        t = time.time()
        return forecast(quota_samples(t - 26 * 3600), t)
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


# ------------------------------------------------------------------------------------------------------ the hosts

def clean_env(role: str = "build") -> dict:
    """The environment for a Claude run: no API key or parent-session variables, so it uses the signed-in plan and
    doesn't mistake itself for a nested session. CLAUDE_CONFIG_DIR is kept, because it says which sign-in to use."""
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("ANTHROPIC_") or k.startswith("CLAUDE")) or k == "CLAUDE_CONFIG_DIR"}
    return {**env, "ORCHESTRATE_ROLE": role}


def agent_installed(name: str, worktree: Path) -> bool:
    return any(p.exists() for p in (Path.home() / ".claude/agents" / f"{name}.md",
                                    worktree / ".claude/agents" / f"{name}.md"))


def skill_note(name: str) -> str:
    """How a host finds a skill: by name where it has a skill mechanism, by path where it doesn't."""
    path = SKILLS / name / "SKILL.md"
    where = f"; the file is {path}" if path.exists() else ""
    return f"${name} in Codex{where}"


def default_host(prof: dict) -> str:
    """The profile's Default host, else the host this command runs inside, else the only one installed, else codex."""
    if prof.get("default_host"):
        return prof["default_host"]
    if os.environ.get("CLAUDECODE"):
        return "claude"
    if os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SANDBOX"):
        return "codex"
    installed = [h for h, exe in (("codex", CODEX), ("claude", CLAUDE)) if shutil.which(exe) or Path(exe).exists()]
    return installed[0] if len(installed) == 1 else "codex"


def host_command(host: str, prof: dict, model: str, effort: str, worktree: Path, prompt: str,
                 session: str | None, role: str = "build") -> tuple[list[str], dict | None]:
    """The command line and environment for one turn on `host`."""
    env = {**os.environ, "ORCHESTRATE_ROLE": role}
    if host == "codex":
        flags = codex_flags({**prof, "model": model, "effort": effort}, role)
        common = ["-C", str(worktree), "--add-dir", git_common_dir(worktree)]
        if session:
            return [CODEX, "exec", *common, "resume", session, *flags, "--json", prompt], env
        # Labels the thread the way the Codex app labels its own, so it shows in the app's thread list.
        source = ["--thread-source", "vscode"] if codex_supports("--thread-source") else []
        return [CODEX, "exec", *flags, *common, *source, "--json", prompt], env
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
        return args, clean_env(role)
    template = prof.get("hosts", {}).get(host)
    if not template:
        raise SystemExit(f"error: unknown host {host!r}; use codex, claude, or add a '- **Host {host}:** <command>' "
                         "line to ORCHESTRATE.md")
    values = {"prompt": prompt, "model": model, "effort": effort, "cwd": str(worktree)}
    return [token.format(**values) for token in shlex.split(template)], env


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


def resolve(a: argparse.Namespace, prof: dict, role: str) -> tuple[str, str, str]:
    """The host, model and effort for this launch: what the lead passed, else the profile, else the defaults."""
    host = (a.host or default_host(prof)).lower()
    model = a.model or prof["models"].get(host) or ""
    if not model and host in prof.get("hosts", {}) and "{model}" in prof["hosts"][host]:
        raise SystemExit(f"error: host {host} needs --model, or a '- **{host} model:** <model>' line in the profile")
    effort = a.effort or ("high" if role == "plan" else prof["effort"])
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


def floor_reason(host: str, code: int, err: str) -> str:
    if code == 127:
        return f"the {host} CLI couldn't start: {err.strip()[-200:]}"
    return f"two failed turns or no session on {host}; likely quota, sign-in or outage"


# ------------------------------------------------------------------------------------------------------- building

RUN_RESULTS = {"review_owed": "REVIEW_OWED", "waiting": "WAITING", "design_owed": "DESIGN_OWED",
               "blocked": "BLOCKED", "parked": "PARKED", "finished": "FINISHED", "taken": "TAKEN",
               "invalid": "INVALID"}


def cmd_run(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    host, model, effort = resolve(a, prof, "build")
    stem = module_stem(worktree, prof, a.module)
    key = stem.upper()
    if not run_lock(worktree, key):
        emit("TAKEN", module=stem, by="another run on this repository")
    install_stop()
    git_dir = git(worktree, "rev-parse", "--absolute-git-dir").stdout.strip()
    state_dir = Path(git_dir) / "orchestrate"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{stem}.json"

    sync_worktree(worktree, prof)
    try:
        start_tip = tip(worktree, prof)
    except TipError as e:
        emit("FLOOR", module=stem, reason=str(e))
    proj = project(worktree, prof, start_tip)
    for k, cycle in need_cycles(proj).items():
        proj[k]["problems"].append(f"its needs form a cycle: {cycle}")
    sync_claims(worktree, prof)
    step = next_step(key, proj, claims(worktree), me(worktree))
    if a.milestone and step.get("milestone") != a.milestone:
        emit("WAITING", module=stem, milestone=a.milestone,
             reason=f"{a.milestone} isn't the module's next milestone; that is {step.get('milestone')} "
                    f"({step['status']}), and milestones in a module run in order")
    if step["status"] != "ready":
        emit(RUN_RESULTS[step["status"]], **step)
    mid = step["milestone"]
    ok, holder = take_claim(worktree, prof, key, mid)
    if not ok:
        emit("TAKEN", module=stem, milestone=mid, by=holder)

    done = load_done(worktree, stem, prof)
    if problems := validate(done, key):
        emit("INVALID", module=stem, problems=problems[:20])
    milestone = find(done, mid)
    authorised_hash = proj[key]["record"]["milestones"][mid]["definitions"]
    if definitions(milestone) != authorised_hash:
        emit("INVALID", module=stem, milestone=mid, problems=[
            f"this worktree's copy of {mid}'s definitions isn't the authorised one at the integrated tip; "
            f"rebase the worktree onto {base_ref(prof)} and run again"])
    baseline = copy.deepcopy(done)

    pin = [host, model, effort]
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    fresh = (a.fresh or state.get("milestone") != mid or state.get("result") == "PIN" or state.get("pin") != pin)
    if fresh:
        state = {"module": stem, "milestone": mid, "thread": None, "turns": 0, "pin": pin}
    # Every run starts its own counters, so a resume after BUDGET or a failed review isn't judged on old progress.
    _, reflog = own_progress(worktree, 10 ** 9, prof["plans"])
    state.update(failed_turns=0, reports=0, unclaimed=0, progress_at=time.time(), passing=passing(milestone),
                 reflog=reflog, host=host, model=model, effort=effort, start_tip=start_tip)
    state.pop("result", None)
    timeout_s = a.turn_timeout_hours * 3600
    resumable = host in ("codex", "claude")

    def record_block(reason: str) -> None:
        def change(tree):
            path = tree / done_rel(prof, stem)
            doc = json.loads(path.read_text())
            m = find(doc, mid)
            m.update(state="blocked", blocked=reason[:500])
            write_json(path, doc)
            return [done_rel(prof, stem)]
        loop_write(worktree, prof, key, change, f"orchestrate: {stem} {mid} blocked")
        drop_claim(worktree, prof, key, mid)

    while True:
        status = goal_status(state.get("thread")) if host == "codex" else None
        if status in ("usage_limited", "budget_limited"):
            finish(state_path, state, "FLOOR", reason=f"goal {status}")
        if status == "paused" or _STOP:
            finish(state_path, state, "PAUSED")
        first = state.get("thread") is None or not resumable
        if first:
            prompt = BUILD_TEMPLATE.format(model=model, effort=effort, goal=GOAL_LINE if host == "codex" else "",
                                           milestone=mid, module=stem, done=done_rel(prof, stem), loop=LOOP,
                                           skill=skill_note("build-milestone"))
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

        if _STOP:
            finish(state_path, state, "PAUSED")
        if code == 127 or (resumable and state["thread"] is None) or state["failed_turns"] >= 2:
            finish(state_path, state, "FLOOR", reason=floor_reason(host, code, err), exit_code=code, stderr=err)
        if bad := pin_problem(host, state.get("thread"), seen, model, effort):
            finish(state_path, state, "PIN", mismatches=bad[:5])
        status = goal_status(state["thread"]) if host == "codex" else None
        if status in ("usage_limited", "budget_limited"):
            finish(state_path, state, "FLOOR", reason=f"goal {status}")
        if status == "paused":
            finish(state_path, state, "PAUSED")

        done = load_done(worktree, stem, prof)
        if problems := validate(done, key):
            finish(state_path, state, "INVALID", problems=problems[:20])
        try:
            upstream = loop_versions(worktree, done_rel(prof, stem), start_tip, tip(worktree, prof))
        except TipError:
            upstream = []
        if problems := delta_problems(baseline, done, "build", mid, upstream):
            finish(state_path, state, "INVALID", problems=problems[:20] + [
                "only the builder's own fields may change during a run; if a planner changed the file, start the "
                "builder again"])
        current = find(done, mid)
        moved, state["reflog"] = own_progress(worktree, state["reflog"], prof["plans"])
        now_passing = passing(current)
        if now_passing > state["passing"] or moved:
            state["progress_at"] = time.time()
        state.update(passing=now_passing, head=head_commit(worktree))

        word = report_word(message)
        if now_passing == len(current["items"]):
            reasons, checked = claim_problems(worktree, prof, stem, current, done, authorised_hash, start_tip)
            if not reasons:
                head, review = head_commit(worktree), needs_review(current, done)

                def change(tree):
                    doc = json.loads((tree / done_rel(prof, stem)).read_text())
                    rec = record_in(tree, prof, stem, doc)
                    e = entry(rec, mid)
                    e["claim"] = {"commit": head, "checked": checked, "at": now(), "host": host, "model": model}
                    paths = [record_rel(prof, stem)]
                    if not review:
                        e["accepted"] = {"by": "checks", "commit": head, "checked": checked, "at": now()}
                        if find(doc, mid).get("state") != "done":
                            find(doc, mid)["state"] = "done"
                            write_json(tree / done_rel(prof, stem), doc)
                            paths.append(done_rel(prof, stem))
                    write_json(tree / record_rel(prof, stem), rec)
                    return paths
                ok, detail = loop_write(worktree, prof, key, change,
                                        f"orchestrate: {'accept' if not review else 'claim'} {stem} {mid}")
                if not ok:
                    finish(state_path, state, "FLOOR", reason=f"the loop couldn't record the claim: {detail}")
                if not review:
                    drop_claim(worktree, prof, key, mid)
                finish(state_path, state, "CLAIMED", review=review, commit=head, checked=checked)
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
                if word == "BLOCKED":
                    reason = report_line(message).partition(":")[2].strip() or "see the builder's report"
                    attended = [i["id"] for i in current["items"] if i.get("attended") and i.get("status") != "pass"]
                    if attended and all(i.get("status") == "pass" for i in current["items"] if not i.get("attended")):
                        reason = f"attended items need a person or hardware: {', '.join(attended)}. {reason}"
                    record_block(reason)
                finish(state_path, state, word, report=message[-1500:])
        else:
            state["reports"] = 0
        if status == "blocked":
            record_block(report_line(message) or "the Codex goal is blocked")
            finish(state_path, state, "BLOCKED", report=message[-1500:])
        if time.time() - state["progress_at"] > a.budget_hours * 3600:
            finish(state_path, state, "BUDGET", hours=a.budget_hours)


# ------------------------------------------------------------------------------------------ reviewing and planning

def one_session(host: str, prof: dict, model: str, effort: str, worktree: Path, prompt: str, role: str,
                done_when, timeout_s: float, max_turns: int = 3) -> dict:
    """Runs a reviewer or planner until its last line satisfies `done_when`, nudging it at most twice. Host failures
    come back as FLOOR, PIN or PAUSED with their reasons, so the lead can fall back to another host."""
    session, message, turns = None, "", 0
    while turns < max_turns:
        resume = session if (turns and host in ("codex", "claude")) else None
        text = prompt if not resume else "Finish the task and end with the last line it asks for."
        code, session, message, err, seen = run_turn(host, prof, model, effort, worktree, text, resume, timeout_s,
                                                     role)
        turns += 1
        if _STOP:
            return {"result": "PAUSED", "session": session}
        if bad := pin_problem(host, session, seen, model, effort):
            return {"result": "PIN", "mismatches": bad[:5], "session": session}
        if code != 0:
            return {"result": "FLOOR", "reason": floor_reason(host, code, err) if code == 127 else
                    f"the {role} turn on {host} failed (exit {code}); likely quota, sign-in or outage",
                    "exit_code": code, "stderr": err, "session": session}
        if done_when(message):
            break
    last = next((l.strip() for l in reversed(message.splitlines()) if l.strip()), "")
    return {"result": "FINISHED" if done_when(message) else "UNFINISHED", "last_line": last,
            "report": message[-1500:], "session": session, "turns": turns}


REVIEW_LINE = re.compile(r"^(PASS|FAIL)\s+([A-Za-z0-9_.-]+)\b|^(DESIGN OK|DESIGN CHANGES)\b")


def cmd_review(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    host, model, effort = resolve(a, prof, "review")
    stem = module_stem(worktree, prof, a.module)
    key, mid, design = stem.upper(), a.milestone, a.milestone == "design"
    info = dict(host=host, model=model, effort=effort, module=stem, milestone=mid)
    if not run_lock(worktree, key):
        emit("TAKEN", **info, by="another run on this repository")
    install_stop()
    try:
        ref = tip(worktree, prof)
    except TipError as e:
        emit("FLOOR", **info, reason=str(e))
    proj = project(worktree, prof, ref)
    if key not in proj or proj[key]["problems"]:
        emit("INVALID", **info, problems=(proj.get(key) or {}).get("problems") or ["not planned at the tip"])
    done_path = done_rel(prof, stem)
    review_path = f"{prof['evidence']}/{stem}/" + ("design-review.md" if design else f"{mid}-review.md")
    rec = proj[key]["record"]
    if design:
        start, before_doc = ref, proj[key]["doc"]
    else:
        r = git(worktree, "rev-parse", "--verify", "--quiet", f"{a.commit}^{{commit}}")
        if r.returncode != 0:
            emit("INVALID", **info, problems=[f"commit {a.commit} doesn't exist here"])
        start = r.stdout.strip()
        if not is_ancestor(worktree, start, ref):
            emit("INVALID", **info, problems=[f"{start[:12]} isn't on {base_ref(prof)}, so it isn't integrated"])
        try:
            before_doc = json.loads(show(worktree, start, done_path) or "")
            claimed = find(before_doc, mid)
        except (json.JSONDecodeError, SystemExit):
            emit("INVALID", **info, problems=[f"{mid} can't be read from {done_path} at {start[:12]}"])
        at_tip = next((m for m in proj[key]["doc"]["milestones"] if m["id"] == mid), {})
        if claimed.get("state") != "claimed" or at_tip.get("state") != "claimed":
            emit("INVALID", **info, problems=[f"{mid} is {claimed.get('state')} at {start[:12]} and "
                                              f"{at_tip.get('state')} at the tip; only a claimed milestone is reviewed"])
        if definitions(claimed) != (rec["milestones"].get(mid) or {}).get("definitions"):
            emit("INVALID", **info, problems=[f"{mid}'s definitions at {start[:12]} aren't the authorised ones"])
    try:
        tree = verify_tree(worktree, stem, start)
    except TipError as e:
        emit("FLOOR", **info, reason=str(e))
    before_review = (tree / review_path).read_text() if (tree / review_path).exists() else None
    template = DESIGN_REVIEW_TEMPLATE if design else REVIEW_TEMPLATE
    prompt = template.format(model=model, effort=effort, milestone=mid, module=stem, commit=start, done=done_path,
                             review=review_path, skill=skill_note("review-milestone"))
    wanted = ("DESIGN OK", "DESIGN CHANGES") if design else ("PASS", "FAIL")
    out = one_session(host, prof, model, effort, tree, prompt, "review",
                      lambda msg: report_line(msg).startswith(wanted), a.turn_timeout_hours * 3600)
    result = out.pop("result")
    if result != "FINISHED":
        emit(result, **info, **out)

    # Check what the reviewer did before anything lands.
    allowed = {review_path} | (set() if design else {done_path})
    changed = changed_paths(tree, start)
    problems = [f"changed {p}, which a reviewer doesn't own" for p in changed if p not in allowed]
    review_text = (tree / review_path).read_text() if (tree / review_path).exists() else None
    if not review_text or review_text == before_review:
        problems.append(f"didn't write the review to {review_path}")
    m = REVIEW_LINE.match(out["last_line"].strip("`* "))
    verdict = (m.group(1) or m.group(3)) if m else ""
    after = None
    if not design:
        if m and m.group(2) != mid:
            problems.append(f"the last line names {m.group(2)}, but the review was of {mid}")
        try:
            after = json.loads((tree / done_path).read_text())
        except json.JSONDecodeError as e:
            after = None
            problems.append(f"{done_path} isn't valid JSON after the review: {e}")
        if after is not None:
            problems += validate(after, key) or delta_problems(before_doc, after, "review", mid)
            reviewed = find(after, mid) if not validate(after, key) else None
            if reviewed:
                verdicts = [i.get("verdict", "") for i in reviewed["items"]]
                if "" in verdicts:
                    problems.append("every item needs a verdict")
                if any(not i.get("review") for i in reviewed["items"]):
                    problems.append(f"every item's review field should point at {review_path}")
                if verdict == "PASS" and (reviewed.get("state") != "done" or set(verdicts) != {"pass"}):
                    problems.append("the last line says PASS, but not every verdict is pass with state done")
                if verdict == "FAIL" and reviewed.get("state") != "in_progress":
                    problems.append("the last line says FAIL, but the state isn't back to in_progress")
    if problems:
        emit("INVALID", **info, landed=False, problems=problems[:20], last_line=out["last_line"],
             session=out.get("session"))

    passed = verdict in ("PASS", "DESIGN OK")

    def change(t):
        write = [review_path]
        (t / review_path).parent.mkdir(parents=True, exist_ok=True)
        (t / review_path).write_text(review_text)
        doc = json.loads((t / done_path).read_text())
        record = record_in(t, prof, stem, doc)
        if design:
            record["design"] = {"verdict": "ok" if passed else "changes", "review": review_path, "commit": start,
                                "hash": text_hash((t / prof["plans"] / f"{stem}.md").read_text()
                                                  if (t / prof["plans"] / f"{stem}.md").exists() else None),
                                "by": "review", "host": host, "model": model, "at": now()}
        else:
            reviewed, target = find(after, mid), find(doc, mid)
            target.update(state=reviewed["state"], fails=reviewed.get("fails", 0))
            by_id = {i["id"]: i for i in reviewed["items"]}
            for i in target["items"]:
                i["verdict"], i["review"] = by_id[i["id"]].get("verdict", ""), by_id[i["id"]].get("review", "")
            if not passed:
                reset_proof(target, only_failed=True)
            write_json(t / done_path, doc)
            write.append(done_path)
            e = entry(record, mid)
            e.setdefault("reviews", []).append({"verdict": "pass" if passed else "fail", "commit": start,
                                                "review": review_path, "host": host, "model": model, "at": now()})
            if passed:
                e["accepted"] = {"by": "review", "commit": start, "review": review_path,
                                 "checked": (e.get("claim") or {}).get("checked"), "at": now()}
        write_json(t / record_rel(prof, stem), record)
        return write + [record_rel(prof, stem)]

    ok, landed = loop_write(worktree, prof, key, change, f"orchestrate: review of {stem} {mid}: {verdict}")
    if not ok:
        emit("INVALID", **info, landed=False, problems=[f"the review was valid but couldn't be integrated: {landed}"])
    if passed and not design:
        drop_claim(worktree, prof, key, mid)
    fails = find(after, mid).get("fails", 0) if after else None
    emit("REVIEWED", **info, verdict=verdict, commit=start, review=review_path, review_commit=landed, fails=fails,
         last_line=out["last_line"], session=out.get("session"))


def cmd_plan(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree)  # a first plan writes the profile itself
    host, model, effort = resolve(a, prof, "plan")
    info = dict(host=host, model=model, effort=effort)
    if not run_lock(worktree, "_plan"):
        emit("TAKEN", **info, by="another planner on this repository")
    install_stop()
    if dirty := git(worktree, "status", "--porcelain").stdout.strip():
        emit("INVALID", **info, problems=["the planner needs a clean worktree, so the loop can tell its files from "
                                          "anything else: " + dirty[:300]])
    start = head_commit(worktree)
    before = {}
    for path in (worktree / prof["plans"]).glob("*-DONE.json") if (worktree / prof["plans"]).exists() else []:
        try:
            before[path.name] = json.loads(path.read_text())
        except json.JSONDecodeError:
            pass
    prompt = PLAN_TEMPLATE.format(model=model, effort=effort, task=a.task, skill=skill_note("plan-module"))
    out = one_session(host, prof, model, effort, worktree, prompt, "plan", lambda msg: bool(msg.strip()),
                      a.turn_timeout_hours * 3600, max_turns=1)
    result = out.pop("result")
    if result != "FINISHED":
        emit(result, **info, **out)
    try:
        prof = profile(worktree, strict=True)
    except SystemExit as e:
        emit("PLANNED", **info, **out, landed=False, problems=[str(e)])

    changed = changed_paths(worktree, start)
    problems = [f"changed {p}; only the loop writes acceptance records" for p in changed
                if p.endswith("-ACCEPTED.json")]
    modules = []
    for p in changed:
        if p.startswith(prof["plans"] + "/") and p.endswith("-DONE.json") and (worktree / p).exists():
            stem = Path(p).name[:-len("-DONE.json")]
            try:
                doc = json.loads((worktree / p).read_text())
            except json.JSONDecodeError as e:
                problems.append(f"{p} isn't valid JSON: {e}")
                continue
            problems += [f"{stem}: {x}" for x in validate(doc, stem.upper())]
            if not validate(doc, stem.upper()):
                problems += [f"{stem}: {x}" for x in delta_problems(before.get(Path(p).name), doc, "plan")]
            modules.append(stem)
    if problems:
        emit("INVALID", **info, **out, landed=False, problems=problems[:20])
    if git(worktree, "status", "--porcelain").stdout.strip():
        git(worktree, "add", "-A")
        git(worktree, *ident(worktree), "commit", "--quiet", "-m", f"Plan: {a.task.splitlines()[0][:60]}")
    ok, landed = land(worktree, prof)
    if not ok:
        emit("PLANNED", **info, **out, landed=False, problems=[f"couldn't integrate the plan: {landed}"])

    def change(t):
        written = []
        for stem in modules:
            path = t / done_rel(prof, stem)
            doc = json.loads(path.read_text())
            rec_path = t / record_rel(prof, stem)
            if rec_path.exists():
                record = json.loads(rec_path.read_text())
            elif Path(done_rel(prof, stem)).name in before and not validate(before[Path(done_rel(prof, stem)).name]):
                # first loop write for a module adopted as it stood before this plan
                record = adopt(before[Path(done_rel(prof, stem)).name],
                               text_hash(show(worktree, start, f"{prof['plans']}/{stem}.md")))
            else:
                record = {"module": stem, "design": None, "milestones": {}}
            for m in doc["milestones"]:
                e = record["milestones"].get(m["id"])
                if e and e.get("definitions") == definitions(m):
                    continue
                if e:  # changed definitions: the old proof proves something else
                    reset_proof(m)
                    if m.get("state") in ("in_progress", "claimed", "done"):
                        m["state"] = "open"
                record["milestones"][m["id"]] = {"definitions": definitions(m), "reviews": (e or {}).get("reviews", []),
                                                 "authorised": {"by": "plan", "task": a.task[:200], "at": now()}}
            for gone in set(record["milestones"]) - {m["id"] for m in doc["milestones"]}:
                del record["milestones"][gone]
            write_json(path, doc)
            write_json(rec_path, record)
            written += [done_rel(prof, stem), record_rel(prof, stem)]
        return written

    ok, detail = loop_write(worktree, prof, "_plan", change, "orchestrate: authorise the plan")
    if not ok:
        emit("PLANNED", **info, **out, landed=True, commit=landed, problems=[f"couldn't record the definitions: {detail}"])
    ref = tip(worktree, prof, fetch=False)
    proj = project(worktree, prof, ref)
    owed = [e["stem"] for e in proj.values() if not e["problems"] and not design_ok(e["record"], e["design"])
            and next_step(e["stem"].upper(), proj)["status"] != "finished"]
    emit("PLANNED", **info, **out, landed=True, commit=detail, modules=modules, design_review_owed=owed)


# ------------------------------------------------------------------------------------------------- reading state

def read_project(worktree: Path, prof: dict) -> tuple[str, dict]:
    try:
        ref = tip(worktree, prof)
    except TipError as e:
        raise SystemExit(f"error: {e}")
    proj = project(worktree, prof, ref)
    for k, cycle in need_cycles(proj).items():
        proj[k]["problems"].append(f"its needs form a cycle: {cycle}")
    sync_claims(worktree, prof)
    return ref, proj


def cmd_ready(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree)
    ref, proj = read_project(worktree, prof)
    held_claims, mine = claims(worktree), me(worktree)
    out = {"tip": ref, "ready": [], "waiting": [], "review_owed": [], "design_owed": [], "blocked": [],
           "parked": [], "taken": [], "finished": [], "invalid": []}
    for key in sorted(proj):
        step = next_step(key, proj, held_claims, mine)
        out[step.pop("status")].append(step)
    print(json.dumps(out, indent=2))


def cmd_status(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree)
    ref, proj = read_project(worktree, prof)
    keys = [a.module.upper()] if a.module else sorted(proj)
    for key in keys:
        if key not in proj:
            print(f"{a.module}: not planned at the integrated tip")
            continue
        e, step = proj[key], next_step(key, proj, claims(worktree), me(worktree))
        print(f"{e['stem']}: {step['status']}" + (f" ({step['milestone']})" if step.get("milestone") else ""))
        for problem in e["problems"] or step.get("problems", []):
            print(f"  invalid: {problem}")
        if e["problems"]:
            continue
        for m in e["doc"]["milestones"]:
            flags = []
            if accepted(m, e["record"]):
                flags.append("accepted")
            elif m["id"] == step.get("milestone"):
                flags.append(step["status"].replace("_", " "))
                if step.get("needs"):
                    flags.append("on " + ", ".join(step["needs"]))
                if step.get("blocked"):
                    flags.append(step["blocked"])
            reviews = (e["record"]["milestones"].get(m["id"]) or {}).get("reviews") or []
            if reviews:
                flags.append(f"last review {reviews[-1]['verdict']} {reviews[-1].get('at', '')}".strip())
            print(f"  {m['id']}\t{m.get('state')}\tfails={m.get('fails', 0)}\t{passing(m)}/{len(m['items'])} pass"
                  f"\t{m.get('name', '')}" + ("\t" + "; ".join(flags) if flags else ""))


def cmd_next(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree)
    stem = module_stem(worktree, prof, a.module)
    milestone = find(load_done(worktree, stem, prof), a.milestone)
    fails, replans = int(milestone.get("fails", 0)), int(milestone.get("replans", 0))
    message = FINDINGS_TEMPLATE.format(milestone=milestone["id"], module=stem, evidence=prof["evidence"])
    print(json.dumps({"milestone": milestone["id"], "fails": fails, "replans": replans,
                      "action": escalation(fails, replans), "message": message}))


def cmd_profile(a: argparse.Namespace) -> None:
    print(json.dumps(profile(Path(a.worktree).resolve(), strict=True), indent=2))


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


def cmd_land(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    if dirty := git(worktree, "status", "--porcelain").stdout.strip():
        print(json.dumps({"result": "FAILED", "detail": "commit, remove or ignore these first: " + dirty[:300]}))
        sys.exit(1)
    ok, detail = land(worktree, prof, check=not a.no_check)
    print(json.dumps({"result": "LANDED" if ok else "FAILED", "detail": detail, "commit": head_commit(worktree)}))
    sys.exit(0 if ok else 1)


def cmd_pause(a: argparse.Namespace) -> None:
    folder = loop_dir(Path(a.worktree).resolve())
    names = [f"run-{a.module.upper()}.lock"] if a.module else [p.name for p in folder.glob("run-*.lock")]
    paused = []
    for name in names:
        path = folder / name
        if not path.exists():
            continue
        with open(path, "a+") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                continue  # nobody holds it, so nothing is running
            except BlockingIOError:
                pass
        try:
            pid = int(path.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            paused.append({"run": name[len("run-"):-len(".lock")], "pid": pid})
        except (ValueError, ProcessLookupError):
            continue
    print(json.dumps({"paused": paused}))


def cmd_unblock(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    stem = module_stem(worktree, prof, a.module)

    def change(t):
        path = t / done_rel(prof, stem)
        doc = json.loads(path.read_text())
        m = find(doc, a.milestone)
        if m.get("state") != "blocked":
            raise SystemExit(f"error: {a.milestone} is {m.get('state')}, not blocked")
        m["state"] = "open"
        m.pop("blocked", None)
        write_json(path, doc)
        return [done_rel(prof, stem)]
    ok, detail = loop_write(worktree, prof, stem, change, f"orchestrate: unblock {stem} {a.milestone}")
    print(json.dumps({"result": "UNBLOCKED" if ok else "FAILED", "detail": detail}))


def owner_confirm(action: str, target: str) -> None:
    """Owner commands record decisions only the owner may make, so an agent mustn't be able to run them by itself:
    they're refused inside any session the loop started, and need the owner to type the target at a terminal."""
    if os.environ.get("ORCHESTRATE_ROLE"):
        raise SystemExit("error: owner commands can't run inside a session the loop started")
    if not sys.stdin.isatty():
        raise SystemExit("error: owner commands need the owner at a terminal; run it yourself, outside any agent")
    if input(f"Type {target} to {action} it: ").strip() != target:
        raise SystemExit("error: not confirmed")


def cmd_owner(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    stem = module_stem(worktree, prof, a.module)
    key, mid = stem.upper(), a.milestone
    owner_confirm(a.action, f"{stem}:{mid}")
    if a.action == "release":
        drop_claim(worktree, prof, key, mid)
        print(json.dumps({"result": "RELEASED", "module": stem, "milestone": mid}))
        return
    stamp = {"by": "owner", "reason": a.reason, "at": now()}
    out = {}

    def change(t):
        path, rec_path = t / done_rel(prof, stem), t / record_rel(prof, stem)
        doc = json.loads(path.read_text())
        if problems := validate(doc, key):
            raise SystemExit("error: the done-when file at the tip is invalid: " + "; ".join(problems[:5]))
        record = record_in(t, prof, stem, doc)
        if mid == "design":
            if a.action != "accept":
                raise SystemExit("error: only `owner accept` applies to a design")
            design = (t / prof["plans"] / f"{stem}.md")
            record["design"] = {**stamp, "verdict": "ok", "hash": text_hash(design.read_text() if design.exists() else None)}
            write_json(rec_path, record)
            return [record_rel(prof, stem)]
        if a.action == "scope":
            new = load_done(worktree, stem, prof)
            if problems := validate(new, key):
                raise SystemExit("error: your done-when file is invalid: " + "; ".join(problems[:5]))
            old = {m["id"]: m for m in doc["milestones"]}
            merged = []
            for m in new["milestones"]:
                was = old.get(m["id"])
                if was is not None and definitions(was) == definitions(m):
                    merged.append(was)  # unchanged: keep the progress recorded at the tip
                    continue
                m = copy.deepcopy(m)
                reset_proof(m)
                m["state"] = "open" if was is None or was.get("state") in ("in_progress", "claimed", "done") \
                    else was.get("state")
                if was is not None:
                    m["fails"], m["replans"] = was.get("fails", 0), was.get("replans", 0)
                e = record["milestones"].get(m["id"]) or {}
                record["milestones"][m["id"]] = {"definitions": definitions(m), "reviews": e.get("reviews", []),
                                                 "authorised": stamp}
                merged.append(m)
            for gone in set(record["milestones"]) - {m["id"] for m in merged}:
                del record["milestones"][gone]
            doc = {**{k: v for k, v in new.items() if k != "milestones"}, "milestones": merged}
        else:
            m = find(doc, mid)
            e = entry(record, mid)
            if e.get("definitions") != definitions(m):
                raise SystemExit(f"error: {mid}'s definitions aren't authorised; settle them with `owner scope` first")
            if a.action == "accept":
                m["state"] = "done"
                m.pop("blocked", None)
                e["accepted"] = {**stamp, "commit": head_commit(t)}
            elif a.action == "rereview":
                if not accepted(m, record):
                    raise SystemExit(f"error: {mid} isn't accepted, so there's nothing to re-review")
                old_review = t / prof["evidence"] / stem / f"{mid}-review.md"
                if old_review.exists():
                    n = 1
                    while (t / prof["evidence"] / stem / f"{mid}-review-{n}.md").exists():
                        n += 1
                    shutil.copy(old_review, old_review.with_name(f"{mid}-review-{n}.md"))
                out["commit"] = e["accepted"].get("commit") or (e.get("claim") or {}).get("commit")
                e.setdefault("history", []).append(e.pop("accepted"))
                m["state"] = "claimed"
            elif a.action == "unpark":
                if m.get("state") != "parked":
                    raise SystemExit(f"error: {mid} is {m.get('state')}, not parked")
                m.update(state="open", fails=0)
            e.setdefault("owner", []).append({**stamp, "action": a.action})
        write_json(path, doc)
        write_json(rec_path, record)
        return [done_rel(prof, stem), record_rel(prof, stem)] + (
            [str(p.relative_to(t)) for p in (t / prof["evidence"] / stem).glob(f"{mid}-review-*.md")]
            if a.action == "rereview" else [])

    ok, detail = loop_write(worktree, prof, key, change, f"orchestrate: owner {a.action} {stem} {mid}: {a.reason}")
    if ok and a.action == "accept" and mid != "design":
        drop_claim(worktree, prof, key, mid)
    print(json.dumps({"result": "DONE" if ok else "FAILED", "action": a.action, "module": stem, "milestone": mid,
                      "detail": detail, **out}))
    sys.exit(0 if ok else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def host_args(p):
        p.add_argument("--host", help="codex, claude, or a host named in the profile (default: see above)")
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
    for flag in ("--module", "--milestone", "--worktree"):
        review.add_argument(flag, required=True)
    review.add_argument("--commit", default="HEAD")
    host_args(review)
    review.set_defaults(func=cmd_review)
    plan = sub.add_parser("plan")
    plan.add_argument("--worktree", required=True)
    plan.add_argument("--task", required=True)
    host_args(plan)
    plan.set_defaults(func=cmd_plan)
    land_p = sub.add_parser("land")
    land_p.add_argument("--worktree", default=".")
    land_p.add_argument("--no-check", action="store_true")
    land_p.set_defaults(func=cmd_land)
    ready = sub.add_parser("ready")
    ready.add_argument("--worktree", default=".")
    ready.set_defaults(func=cmd_ready)
    status = sub.add_parser("status")
    status.add_argument("--module")
    status.add_argument("--worktree", default=".")
    status.set_defaults(func=cmd_status)
    nxt = sub.add_parser("next")
    for flag in ("--module", "--worktree", "--milestone"):
        nxt.add_argument(flag, required=True)
    nxt.set_defaults(func=cmd_next)
    unblock = sub.add_parser("unblock")
    for flag in ("--module", "--worktree", "--milestone"):
        unblock.add_argument(flag, required=True)
    unblock.set_defaults(func=cmd_unblock)
    pause = sub.add_parser("pause")
    pause.add_argument("--module")
    pause.add_argument("--worktree", default=".")
    pause.set_defaults(func=cmd_pause)
    owner = sub.add_parser("owner")
    owner.add_argument("action", choices=["accept", "rereview", "unpark", "scope", "release"])
    for flag in ("--module", "--milestone", "--worktree", "--reason"):
        owner.add_argument(flag, required=True)
    owner.set_defaults(func=cmd_owner)
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
