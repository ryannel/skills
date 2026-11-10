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

  On a Mac with the Codex app or Claude desktop running, codex and claude sessions are ones the app lists under the
  project, where the owner can watch, steer, pause (Stop) and take over; the loop still drives and checks every turn.
  Codex threads run in the app itself. Claude turns run in the loop's own signed-in `claude -p`, imported into the
  Code tab. Otherwise (another OS, app not installed or not running, Claude CLI signed out, or ORCHESTRATE_HEADLESS=1)
  they run headless as above. Every result line from a turn says which: `path` is `visible` or `headless`, with
  `path_reason` when headless. Stopping a turn in the app gives PAUSED, and `run` again carries on.

What the loop owns. Next to each done-when file it keeps `<MODULE>-ACCEPTED.json`, which only the loop writes and
which is committed, so every worktree, clone and lead sees the same thing. Per milestone it holds the authorised hash
of the acceptance definitions, the claim the loop checked (code commit and the integrated tip it ran the checks on),
the reviews that judged it, and whether it was accepted, by checks, a reviewer or the owner. It also holds the
module's design review. A milestone is finished only when the record accepts it with its current definitions; a
`done` state in the done-when file isn't enough. A module with no record yet has its definitions authorised and
nothing accepted, with its design review owed. Only in a repository that has never had a loop record is a module
adopted as it stands, finished milestones accepted; the loop's first record-keeping commit writes those records.

The loop reruns checks with your own permissions, outside any host's sandbox, in a clean checkout of the integrated
tip. It pins the check strings, but a script a check calls can still be changed by the builder, so review new check
scripts.

Subcommands:

  run   --module CORE --worktree PATH [--host H] [--model M] [--effort E] [--milestone M2] [--fresh]
        [--message TEXT] [--owner-rule TEXT]... [--clear-owner-rules] [--budget-hours 4] [--no-design-review]
        [--review-host H]
        Starts (or resumes) a builder session on the module's next milestone and drives it one turn at a time until:
        CLAIMED       the claim holds: the done-when file is valid and only the builder's own fields changed, the
                      milestone's state is `claimed` (or `done` when it needs no review), every item is `pass` with
                      evidence, the tree is clean, HEAD is on the integrated tip (fetched fresh), and the profile's
                      Check and every item's `check` exit 0 in a clean checkout of that tip. `review` says whether a
                      reviewer must judge it, `commit` is the commit to review and `checked` the tip the checks ran
                      on. A milestone that needs no review is accepted there and then. `next` is the review
                      command on the review host, or, with no review owed, `run` for the next milestone.
        BLOCKED       the builder can't go on; the loop records `state: blocked` and what unblocks it
        NEEDS_CONTEXT the agent's final report line
        UNCLAIMED     the agent said DONE (or its goal completed) three times without a claim that holds
        INVALID       the done-when file is malformed, or something outside the builder's fields changed
        REVIEW_OWED   the module's next milestone is claimed and waiting for review
        REPLAN_OWED   the module's next milestone failed review four times; `next` is the planner's re-plan, and no
                      builder starts on it until the planner has changed its definitions
        DESIGN_OWED   the module's design hasn't passed a design review (or changed since it did). Unless
                      --no-design-review, `run` first runs that review itself, as `review --milestone design` would
                      with the same --effort, on the review host (--review-host, else the profile's `Review host`,
                      else the builder's host; --model only when that is the builder's host), and on DESIGN OK goes
                      on to build; any other outcome stops here with the review's result under `design_review`.
                      After DESIGN OK, every later result of the run carries `design_review` (verdict, host, model,
                      review file and its `usage`), so the review's cost shows with the build's
        WAITING       the next milestone needs milestones in other modules that aren't accepted yet
        PARKED / FINISHED   the module stops at a parked milestone / has nothing left
        TAKEN         another lead or run holds this module or milestone; `by` and `holder` say which (pid, role,
                      worktree, since when) where the records show it
        BUDGET        no new passing item, and no commit of the builder's own outside the plans folder, for
                      --budget-hours
        STALLED       three turns in a row changed nothing and reported nothing (progress updates); the two
                      continuations between them named the open items
        FLOOR         two failed turns in a row, the host CLI is missing, the integrated tip can't be fetched, or
                      the goal is usage- or budget-limited (likely quota, sign-in or outage)
        PIN           a turn ran on a model or effort other than the named ones
        PAUSED        `pause` stopped it, the owner stopped it or has it open in the app, or the Codex goal is
                      paused; `run` again carries on (re-activating a paused goal on a visible thread)
        A run on the same milestone resumes its session (with --message as the first prompt, e.g. the reviewer's
        findings) unless --fresh is given or the host, model or effort changed. A new milestone starts a new session.
        --milestone only confirms which milestone you expect; it never skips one that comes first.
        Each resumed turn restates the objective and what binds the builder (its fields, `land`, the Check, the
        profile's `Licences and paths not to touch` and `Owner decides` lines, attended items, owner rules), except
        on a Codex thread whose goal is active, which gets only the owner rules; `goal` in the result says which, and `constraints_missing` names profile lines that
        weren't there to restate. Claims and reviews record the requested host, model and effort, the CLI's
        version, under `observed` only what the host's own output showed, and under `usage` the tokens its headless
        turns reported (input not read from cache, cache reads, output, and Claude's list-price estimate for that
        turn, taken as the rise in the session's cumulative total), with
        `incomplete_turns` counting turns that showed no tokens (a visible Codex turn) or only some (a Claude turn
        stopped before its result event, counted from its messages). A result line's `usage` is the session's
        running total. A claim record's `usage` is what the session spent since its previous claim, so a milestone's
        claims add up; `session_usage` beside it is the running total, not to be added.
        Every result that stops short of building (WAITING, DESIGN_OWED, REVIEW_OWED, REPLAN_OWED, BLOCKED, INVALID, FLOOR,
        TAKEN, PARKED) carries `next`: {command, by, why}, the exact command to run next. Its `--worktree` is the one
        the command producing it was given, so a `next` from `ready` or `status` run in the main checkout names the
        main checkout. A `run` or design `review` in any `next` (and in `ready`'s and `next`'s) gets the host and
        review host of that module's latest build run on this machine (<git common dir>/orchestrate/last-runs.json,
        written when a build turn starts) where the command names none; with `Review host: other` only a review host
        the lead named on that run is kept, and a design review owed after a planner turn names the host that
        didn't plan it. A milestone review's host is left to
        `review`, which takes the builder's from the claim record. `by: owner` marks a
        decision only the owner may make: `ask` is what the lead asks them in chat, and `command` the `owner`
        command the lead runs once they've answered, with their words in --text; the loop never runs those itself.
        A BLOCKED milestone with attended items that haven't passed also carries `next.owner_answers`, one {item,
        ask, command, by: owner} per item, whatever else `next` says (`ready` lists those items under `attended`;
        `report` gives each one's command). When plan
        files under the profile's plans folder are uncommitted or not integrated, the result names them under
        `unlanded_plans` and `next` is `adopt`, with what would have come next under `then`.
        A project with no ORCHESTRATE.md gives INVALID with `next` naming `plan`.
        Prints one JSON line with the result as the last line of output. Its `warnings` are the launch's loader
        checks for the resolved host and binary (an AGENTS.md that Claude won't read, a skill not installed where
        the host finds skills by name); they never stop a run.

  review --module CORE --milestone M2 --commit SHA --worktree PATH [--host H] [--model M] [--effort E]
        Runs a fresh reviewer in a clean checkout of the claimed commit (or of the integrated tip, with --milestone
        design), then checks what it did: only the review file and the reviewer's own fields changed, the verdicts
        agree with its last line, and a fail added 1 to `fails`. If all holds, the loop lands the review itself,
        sets failed items back to open, and records the verdict. An earlier round's review is kept beside the new
        one as <milestone>-review-N.md (reusing `owner rereview`'s copy of the same text), and its record entry
        points there; entries overwritten before rounds were kept say `review_in_history`. Captures go in the folder beside the review file
        (<evidence>/<MODULE>/<milestone>-review/), which lands with it. REVIEWED, INVALID (nothing landed), or the host's
        FLOOR, PIN or PAUSED. With no --host, a review goes to the profile's `Review host` (`other` means the host
        that built the claim swapped, or for a design review the host of the planner turn that wrote the plan
        swapped, else the profile's default host swapped). REVIEWED's `next` is the
        {command, by, why}. After a failed milestone review `ladder` (and `next.ladder`) is the escalation word
        (same-session, fresh-session, replan, park) and `next` the command it calls for: `run --message` with the
        findings, `run --fresh --message`, `plan` with a re-plan task naming the reviews (by: planner), or `owner
        unpark` (by: owner) for a milestone the loop parked. After a pass it is the
        next ready milestone or "finished", the planner's revision with `findings` after DESIGN CHANGES.
        A second design review keeps the first as design-review-N.md, and its prompt names the done-when items
        added, removed or redefined since the first.

  plan  --worktree PATH --task TEXT [--host H] [--model M] [--effort high]
        Runs a fresh planner in a clean worktree. Its last line must be `PLANNED: <files>` naming files it
        changed that exist (a design beside every changed done-when file), else it's nudged with what's missing, at
        most twice. Then the loop checks its done-when files, commits and lands its files, and authorises the new
        definitions (resetting proof on milestones whose definitions changed). PLANNED lists the modules whose
        design review is now owed. BLOCKED or NEEDS_CONTEXT from the planner, or UNFINISHED, lands nothing and
        leaves its files uncommitted. Its `report` keeps the end of the planner's message (where owner decisions go),
        up to 6000 characters. PLANNED's `next` is the owed design review on the review host, or `ready`;
        `assumptions` counts, per module, the `Assumption:` lines in its plan log. The whole task is kept in the plan
        commit's body and in each module's acceptance record under `briefs` (the authorisation stamps name only its
        first line), which design reviews are pointed at. For each
        milestone that was owed a re-plan and whose definitions the plan changed, the loop sets fails 0, adds 1 to
        replans and opens it, in its own commit, whatever the planner wrote there (`replanned` lists them). In a
        repository with no commits (or origin with no main branch), FLOOR before any planner turn, with `next`
        giving the first commit and push. One planner runs per repository at a time: another gets TAKEN, naming the
        holder, with `next` to run it again once that one stops. A clean worktree behind the tip is fast-forwarded
        first, and one with commits the tip lacks is refused (INVALID, `next` making a fresh worktree on the tip to
        plan in, leaving this one alone). The loop lands only what the planner leaves uncommitted: a turn whose
        worktree's reflog shows a commit made during it, or whose HEAD the tip lacks, is INVALID (`next` by lead, no
        command), and so is one during which a commit
        without the loop's trailer changed an acceptance record on the tip (named, `next` by owner, no command). Its
        HEAD may move along the tip meanwhile (a `land` elsewhere fast-forwards the checkout holding the base
        branch). Everything it leaves uncommitted lands, outside the plans folder too (acceptance tests, say), except
        acceptance records. Any other INVALID turn's `next` stashes its files and gives a planner the task again
        with the problems. The whole task is kept once, under `briefs`. A review is refused the same way when a
        record changes on the tip without the trailer while it runs, or its checkout's reflog shows a commit. `land` refuses to run in a plan or review
        session.

  land  --worktree PATH [--no-check]
        Integrates the worktree's commits under the integrate lock: rebase onto the base, run the profile's Check,
        then push (Integrate: push) or fast-forward the local branch (Integrate: local). Builders use this.

  ready [--worktree PATH]       What each module's next milestone is waiting for, read at the integrated tip. When
        nothing is ready it adds `next`; a milestone owed a re-plan is listed under `replan_owed` with its own
        `next` (the planner's command), never as ready. It names unlanded plan files (`unlanded_plans`) as `run` does, and
        `profile_differs` when ORCHESTRATE.md here differs from the tip's. With no ORCHESTRATE.md it gives `unplanned`
        and `next` naming `plan`, or, when the integrated tip does have one, `behind` and `next` naming the merge
        that brings this worktree up to it.
  adopt [--worktree PATH] [--message TEXT] [PLAN FILE]...
        Commits plan files that are uncommitted, or committed here but not integrated, and integrates them through a
        clean checkout of the tip, as the loop lands its own records, so nothing else in the worktree goes with them.
        Also lands a first ORCHESTRATE.md (one the tip doesn't have yet) and reports under <evidence>/build-reports/.
        A module's definitions are a draft until a design review of it passes. While they are, and nothing has been
        built (no claim, review or acceptance, no milestone past open, no run holding the module), adopt authorises
        changed definitions (`authorised` lists the modules; the record's stamp says why), because the owed design
        review will judge them; it holds the module's run lock while it lands and checks again before each commit.
        Refuses files outside those, acceptance records, invalid done-when files, changed definitions on a module
        that's no longer a draft (with `next` naming `plan` and `owner scope`), a changed ORCHESTRATE.md the tip
        already has (the lead commits it once the owner agrees), anything `ready` would then call invalid, files the tip changed since,
        and any session the loop started. While it lands it has a `loops` record, so a run turned away names it.
        ADOPTED, NOTHING, REFUSED or FAILED (with `next` when the repository has no commits to build on).
  status [--module CORE] --worktree PATH   Every milestone with its state, blockers and last verdict, and which
        modules (and the planner) have a live run. A claim the loop hasn't checked yet shows as `done, unchecked`.
  check --module CORE --milestone M2 [--worktree PATH] [--plans-from PATH] [--timeout 600] [--json]
        Runs the milestone's checks (each item's `check`, then the profile's Check) in the given tree, as it stands,
        and prints a line per check, with the why and last output lines of any that didn't pass (--json: one JSON
        object with everything): per check `pass`, `fail` (it ran and failed: likely not built yet; the output says),
        `error` or `timeout`, with the exit code and the output's tail. `error` means the check can't run as
        written, and is given only where that's certain: it doesn't parse as shell, or exit 126. Its fix is to how the
        check is written, never to what it tests. Exits 0 only when every check passes. Writes nothing.
  cost [--module CORE] [--since HOURS] --worktree PATH [--json]
        Tokens per milestone from this machine's usage ledger (<git common dir>/orchestrate/usage.jsonl), which
        every turn the loop runs appends to, paused ones too: planning, then each milestone's build and review
        (a design review under milestone `design`), with totals and how many turns showed no tokens or only some.
        A milestone the ledger has nothing on (a clone, or a project built before the ledger) is read from the
        `usage` its claims and reviews carry in the committed acceptance record, and marked as from the record.
  report [--since 24] --worktree PATH [--write]
        The factual half of the lead's report: what closed, the verdicts with links (every design review in the
        window, DESIGN CHANGES ones included), every decision recorded in the owner's name with their words (for the
        owner to spot one they didn't make), the planner turns that authorised definitions with the task each
        was given (where the lead puts the owner's words), the planners'
        assumptions (lines starting `Assumption:` in each <MODULE>-PLAN.md) for the owner to overturn, what is parked,
        blocked or waiting, open attended items, and cost (as `cost` reads it). --write puts it in
        <evidence>/build-reports/<date>.md for `adopt`, with its links relative to that file.
  next  --module CORE --worktree PATH --milestone M2   The escalation after a failed review (see done-when.md):
        read at the integrated tip, where the review landed. `action` is the ladder's word, `message` what to send (the builder's findings, or for `replan` the planner's
        task), and `next` the command.
  unblock --module CORE --milestone M2 --worktree PATH   Puts a blocked milestone back in the queue.
  pause [--module CORE] --worktree PATH   Stops running loops in this repository, and their agents, cleanly.
  owner accept|rereview|unpark|scope|release|answer --module CORE --milestone M2|design [--item M2.3]
        --worktree PATH --text TEXT
        Records a decision the owner made in chat; the lead runs it, with the owner's words in --text as they gave
        them. Every verb records those words, when, and which verb, under `decisions` in the module's record (the
        loop can't tell who ran it, so it doesn't say), and `report` lists them all. Refused inside any session the
        loop started (ORCHESTRATE_ROLE set: Claude's environment, and Codex's shell through shell_environment_policy,
        confirmed headless and unconfirmed in the app) and while a run, review or plan holds the module or the
        planner. These stop mistakes and casual shortcuts, not a determined agent. `answer` records the owner's
        words against a milestone or attended item (`owner_answers`) and puts a blocked milestone back in the queue;
        the resumed builder is told to read it there, and the reviewer to check claims about the owner's choice
        against it. `release` drops a claim whose lead is gone. `scope` takes the done-when file as edited in the
        worktree (refused, saying nothing changed, when it matches the tip), leaves the worktree clean on the tip where it can, and says under `worktree` what to do where it
        can't. A `scope` that changes a milestone owed a re-plan is the re-plan: fails 0, one more replans, state
        open, listed under `replanned` with `replanned_why`.
  quota [--worktree PATH] [--budget 120] [--json]
        A short readout leading with the verdict, saying whose use each figure counts; --json gives everything.
        The weekly Codex limit, read from Codex's local rollouts by codex_quota.py beside this file: burn per active
        hour (idle time excluded) and per builder-hour by model and effort, a tokens-to-percent fit with its range, what
        each milestone of this repository cost (its turns and rounds; loops in other repositories count only as the
        machine's loop use), the loop's own use apart from other local threads and from usage
        no local rollout explains, and a forecast of the open milestones against what's left before the reset, with a
        one-sentence verdict. Every result line carries a short `quota` field: used, reset, recent burn, the verdict,
        `warn` (only when the quota won't last) and `runs_out` when one builder at the usual pace would use it up.
        Reading is cached and capped at two seconds on a result line; a first, cold read finishes here. Only result
        lines from a run that launched or meant to launch Codex carry `quota`.
  profile --worktree PATH [--host H]   Prints the settings read from ORCHESTRATE.md, or exits 1 naming what's wrong
        (with no ORCHESTRATE.md, `planned: false` and `next` naming `plan`), plus the loader checks for that host
        (`preflight`). Models appear per host only. On Codex with `Codex sandbox: workspace-write`, the preflight
        (here, and before a build turn) warns, with the fixes, when the profile's targets or an open
        milestone's items plainly need a browser, which won't start inside that sandbox unless the agent asks
        to run it outside and is granted it. A run says so once, on stderr before its first build turn and on its
        result line; reviews aren't warned.
  lock [--worktree PATH] NAME -- COMMAND...
        Runs COMMAND under a named lock shared by every worktree of the repository (not the whole machine).
  loops [--repo PATH] [--json]
        Every run, review and plan running on this machine, in any repository and from any copy of this script: its
        repository, module, milestone, role, host, model, effort, path (visible or headless), pid, start, turns, time
        since the last sign of activity (a turn starting or ending, or its session file growing) and tokens where the
        host reported them. Tokens count when a turn ends, so a turn under way shows as `turn_running_s` (and "turn N
        running for ..."); a run's build row counts from its build, the design review it ran first being under
        `design_review` on its result line. A dollar figure, here and in `cost` and `report`, is Claude's list price
        for the Claude turns only; Codex reports tokens, not a price. Each loop keeps a record in $ORCHESTRATE_LOOPS_DIR (default
        ~/.local/state/orchestrate/loops, or under $XDG_STATE_HOME), which counts only while its process holds a lock
        on it, so a dead loop never shows; this command removes what dead loops left there. A loop
        that can't write its record (a sandboxed home) runs as usual, and is listed from the process table with what
        its command line says. --repo narrows the list to one repository; --json is for a lead.

Per-worktree session state lives in <git dir>/orchestrate/<module>.json, so re-running the same command resumes.
Run locks (run-<MODULE>.lock, run-_plan.lock) live in <git common dir>/orchestrate/. The kernel releases one when its
loop ends; the file stays, holding the last holder's pid. A run, a review or a plan holds its lock for as long as it
runs, and adopt holds the lock of each module whose definitions it authorises while it lands them; nothing else
locks them.

A write under .git that the system or a sandbox refuses (Codex's workspace-write sandbox, for one), or a lock file
another git process holds, stops any command with one line naming the path and the fix (`blocked_write`): FLOOR, or
FAILED from `land`, exit 1. The loop doesn't retry it or delete lock files.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import argparse
import atexit
import copy
import errno
import fcntl
import glob
import hashlib
import json
import os
import queue
import re
import shlex
import shutil
import signal
import socket
import sqlite3
import struct
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_quota  # noqa: E402  (beside this file)

DEFAULT_MODELS = {"codex": "gpt-6.1-sol", "claude": "claude-opus-5-5"}
DEFAULT_MODEL = DEFAULT_MODELS["codex"]
ROLE_KINDS = {"plan": "planner", "build": "builder", "review": "reviewer"}  # a launch's role -> the profile's word
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

BUILD_TEMPLATE = """{goal}Objective: milestone {milestone} of module {module} is \
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
blocked (you tried it and it failed) or missing context, end with `BLOCKED: ...` (what would unblock it) or \
`NEEDS_CONTEXT: ...`, with the evidence."""

REVIEW_TEMPLATE = """Use the review-milestone skill ({skill}) to review milestone \
{milestone} of module {module}. This folder is a clean checkout of commit {commit}, made for you by the loop; build \
and run the product from it. The done-when file is {done}. Write the review to {review}, and set the verdict fields, \
state and fails as the skill says. Put captures and other evidence files in {captures}/ and link them from the \
review, rather than embedding them in it. Don't commit, push or change anything else: the loop checks what you \
changed, then integrates the review itself. {answers}Don't launch other agents. End with the skill's last line."""

DESIGN_REVIEW_TEMPLATE = """Use the review-milestone skill ({skill}) to review the \
design of module {module}, as its "Reviewing a design" section describes. This folder is a clean checkout of the \
integrated tip. {changed}{briefs}Write the review to {review}, put any captures in {captures}/, and change nothing \
else; the loop integrates them. Don't launch other agents. End with the skill's last line."""

PLAN_TEMPLATE = """Use the plan-module skill ({skill}) for this task: {task}

You can't launch other agents. The loop commits and integrates the files you leave, and records the new \
definitions; never edit a *-ACCEPTED.json file, and don't commit, merge, pull or land. Say what changed and any decision the owner must make. Your last line \
is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or \
`NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then. To dry-run a milestone's checks, run `python3 {loop} check --module <M> --milestone <id> --worktree .`. The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report."""

FINDINGS_TEMPLATE = """The reviewer failed {milestone}: see {evidence}/{module}/{milestone}-review.md. The loop has \
set the items that didn't pass back to open, so each needs fresh evidence. Every blocking finding counts, including \
cant_tell items (they need evidence the reviewer could reach) and blocking defects outside the items; advisory ones \
are your call. Add them to the plan as work items, fix them, re-verify the affected items, integrate, set the state back to claimed, and end with DONE, BLOCKED \
or NEEDS_CONTEXT."""


class TipError(Exception):
    pass


# ---------------------------------------------------------------------------------------------------------- profile

PROFILE_FIELDS = {"plans": "docs/modules", "evidence": "docs/evidence", "check": None, "branch": "main",
                  "remote": "origin", "integrate": None, "codex sandbox": "workspace-write", "writable roots": "",
                  "graded examples": "", "effort": "", "claude permissions": "auto", "default host": "",
                  "review host": ""}
REQUIRED = {"check": "the command that must pass before integrating, or `none`",
            "integrate": "push (standing permission to push) or local"}
ONE_WORD = {"branch", "remote", "integrate", "codex sandbox", "effort", "claude permissions", "default host",
            "review host"}
ALLOWED = {"codex sandbox": {"workspace-write", "danger-full-access"}, "integrate": {"push", "local"},
           "effort": EFFORTS, "claude permissions": {"auto", "acceptEdits", "bypassPermissions", "dontAsk"}}
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>]*>")  # "<where review files go>", not "cmd < input"
BOUNDS = ("Licences and paths not to touch", "Owner decides")  # the profile's out-of-bounds lines


def profile_value(text: str, label: str) -> str | None:
    m = re.search(rf"^\s*[-*]\s*\*\*{re.escape(label)}:\*\*[ \t]*(.*)$", text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    raw = re.sub(r"\*\(.*?\)\*", "", m.group(1))         # trailing *(read by the loop)* notes
    raw = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw)  # markdown links keep their text
    return raw.replace("`", "").strip()


def profile(worktree: Path, strict: bool = False, missing_ok: bool = False) -> dict:
    """Reads the loop's settings from ORCHESTRATE.md (`- **Label:** value` lines). `Integrate` and `Check` must be
    there, because silently pushing, or integrating with no gate, isn't something to default into. A missing
    profile, or a missing, unfilled or invalid value, raises SystemExit when strict, and falls back to safe defaults
    (local integration, no Check) with a warning otherwise. `missing_ok` drops the warning for a profile that doesn't
    exist yet, where the caller says so itself (an unplanned project) or a planner is about to write it."""
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
    out["role_models"] = {}  # host -> {planner | builder | reviewer: model}, each overriding that host's model
    for m in re.finditer(r"^\s*[-*]\s*\*\*([\w.-]+) (\w+) model:\*\*[ \t]*(.*)$", text,
                         re.IGNORECASE | re.MULTILINE):
        host, kind = m.group(1).lower(), m.group(2).lower()
        value = re.sub(r"\*\(.*?\)\*", "", m.group(3)).replace("`", "").strip().split()
        if kind not in ROLE_KINDS.values():
            problems.append(f"{m.group(1)} {m.group(2)} model: want '<host> planner model', '<host> builder model' "
                            "or '<host> reviewer model'")
        elif value and not PLACEHOLDER.search(value[0]):
            out["role_models"].setdefault(host, {})[kind] = value[0]
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
    out["review_host"] = out.pop("review host").lower()
    if out["review_host"] not in ("", "same", "other", "codex", "claude", *out["hosts"]):
        problems.append(f"review host: {out['review_host']!r} (want same, other, codex, claude or a host this profile "
                        "names)")
        out["review_host"] = ""
    out["roots"] = [r.strip() for r in out.pop("writable roots").split(",") if r.strip()]
    out["graded_examples"] = out.pop("graded examples") or f"{out['evidence']}/graded-examples.md"
    # Prose rules the loop restates on resumed turns; None when the line is missing or still a placeholder.
    out["bounds"] = {}
    for label in BOUNDS:
        value = profile_value(text, label)
        out["bounds"][label] = value if value and not PLACEHOLDER.search(value) else None
    if problems:
        message = "ORCHESTRATE.md has missing, unfilled or invalid fields: " + "; ".join(problems)
        if strict:
            raise SystemExit(message)
        if not (missing_ok and not path.exists()):
            print("warning: " + message, file=sys.stderr)
    return out


def planned_elsewhere(worktree: Path) -> str | None:
    """With no profile to name the integrated branch, the likeliest candidates for it (the branch's upstream, the
    remote's default branch, a local main or master, after a quiet fetch) that do have an ORCHESTRATE.md: the first
    one found, or None."""
    if not worktree.is_dir() or git(worktree, "rev-parse", "--git-dir").returncode != 0:
        return None
    if git(worktree, "remote").stdout.strip():
        git(worktree, "fetch", "--quiet")
    candidates = []
    for args in (("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"),
                 ("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD")):
        r = git(worktree, *args)
        if r.returncode == 0 and r.stdout.strip():
            candidates.append(r.stdout.strip())
    candidates += ["origin/main", "origin/master", "main", "master"]
    for ref in dict.fromkeys(candidates):
        if file_at(worktree, ref, PROFILE_FILE) is not None:
            return ref
    return None


def unplanned(worktree: Path) -> dict | None:
    """For a worktree with no ORCHESTRATE.md: that the project isn't planned yet, and the `plan` command as `next`.
    Planned or not is decided from the integrated tip, so a worktree that is merely behind a tip that has a profile is
    told that, with the command that brings it up to date, rather than to plan the project again."""
    if (worktree / PROFILE_FILE).exists():
        return None
    if ref := planned_elsewhere(worktree):
        if is_ancestor(worktree, "HEAD", ref):
            return {"reason": f"this worktree is behind {ref}, which is planned (it has {PROFILE_FILE}) when "
                              f"{worktree} has none; bring the worktree up to date and run again",
                    "behind": ref,
                    "next": next_cmd(f"git -C {shlex.quote(str(worktree))} merge --ff-only {shlex.quote(ref)}",
                                     "lead", "fast-forwards this worktree to the planned tip")}
        return {"reason": f"{ref} is planned (it has {PROFILE_FILE}), but {worktree} has none and has commits "
                          f"{ref} doesn't, so it can't simply be brought up to date. Use a worktree on {ref}, or "
                          "ask the owner what this branch is for",
                "behind": ref,
                "next": next_cmd(None, "lead", "this worktree has diverged from the planned tip; the loop leaves "
                                               "merging it to whoever owns that branch")}
    return {"reason": f"the project isn't planned yet: there's no ORCHESTRATE.md in {worktree}",
            "next": next_cmd(loop_cmd("plan", "--worktree", str(worktree), "--task",
                                      "Plan the project: <what the owner asked for, in their words>"), "lead",
                             "a planner writes the profile (ORCHESTRATE.md), the module map and the first module's "
                             "plan; give it the owner's ask, and their answers on hosts, integration and checks")}


def codex_flags(prof: dict, role: str = "build") -> list[str]:
    flags = ["-m", prof["model"], "-c", f"model_reasoning_effort={prof['effort']}",
             "-c", "approval_policy=on-request", "-c", "approvals_reviewer=auto_review",
             "-c", f"sandbox_mode={prof['sandbox']}",
             # the agent's own shell commands see the role, as the loop's environment already gives it headless
             "-c", f"shell_environment_policy.set.ORCHESTRATE_ROLE={json.dumps(role)}"]
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

class WriteBlocked(Exception):
    """A write under the repository that the operating system or a sandbox refused, or a lock file another git
    process holds. The loop stops on it with a plain explanation, rather than retrying or deleting anything."""

    def __init__(self, path: str | None, error: str, held: bool = False):
        super().__init__(path, error, held)
        self.path, self.error, self.held = path, error, held

    def reason(self) -> str:
        where = self.path or "a file under .git"
        if self.held:
            return (f"git couldn't take the lock {where}: another git process holds it, or one that crashed left it "
                    "behind. The loop doesn't delete lock files; check nothing else is running git here, remove it "
                    "yourself if it's stale, then run the command again.")
        return (f"git can't write {where} ({self.error}). This command has to run outside the sandbox, or with "
                "escalation: a sandbox such as Codex's workspace-write blocks writes under .git. The loop didn't retry "
                "or delete anything.")

    def fields(self) -> dict:
        return {"reason": self.reason(), "blocked_write": {"path": self.path, "error": self.error,
                                                           "lock_held": self.held}}


WRITE_REFUSED = re.compile(r"Operation not permitted|Permission denied(?! \()|Read-only file system|"
                           r"insufficient permission", re.IGNORECASE)  # not ssh's "Permission denied (publickey)"
LOCK_HELD = re.compile(r"Unable to create '([^']+\.lock)': File exists")
QUOTED = re.compile(r"'([^']+)'")
BARE_PATH = re.compile(r"((?:/|\.git/)[^\s:'\"]+)")


def blocked_write(text: str, where: Path | None = None) -> WriteBlocked | None:
    """The refused write or held lock in git's error output, with the path it names, if there is one."""
    for line in text.splitlines():
        if m := LOCK_HELD.search(line):
            return WriteBlocked(m.group(1), "File exists", held=True)
        if m := WRITE_REFUSED.search(line):
            paths = [p for p in QUOTED.findall(line) if "/" in p] or BARE_PATH.findall(line)
            path = paths[-1] if paths else None
            if path and where is not None and not path.startswith("/"):
                path = str(where / path)
            return WriteBlocked(path, m.group(0))
    return None


def git(worktree: Path, *args: str, stdin: str | None = None) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(worktree), *args], capture_output=True, text=True, input=stdin)
    if r.returncode != 0 and (blocked := blocked_write(r.stderr, worktree)):
        raise blocked
    return r


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
            if empty := no_base(worktree, prof):
                raise empty
            raise TipError(f"git fetch {prof['remote']} {prof['branch']} failed: {f.stderr.strip()[-300:]}")
        git(worktree, "update-ref", f"refs/remotes/{prof['remote']}/{prof['branch']}", "FETCH_HEAD")
    r = git(worktree, "rev-parse", "--verify", "--quiet", base_ref(prof) + "^{commit}")
    if r.returncode != 0:
        if empty := no_base(worktree, prof):
            raise empty
        raise TipError(f"can't read {base_ref(prof)}")
    return r.stdout.strip()


def no_base(worktree: Path, prof: dict) -> "TipError | None":
    """A TipError saying what to do when there's no base branch to build on yet: a repository with no commits at
    all, or (integrating by push) a remote that doesn't have the branch. None for any other failure."""
    wt, branch, remote = str(worktree), prof["branch"], prof["remote"]
    has_remote = git(worktree, "remote", "get-url", remote).returncode == 0
    local = git(worktree, "rev-parse", "--verify", "--quiet", "HEAD^{commit}").returncode == 0
    push = f" && git -C {shlex.quote(wt)} push -u {remote} {branch}" if has_remote else ""
    if not local:
        e = TipError(f"the repository has no commits yet{' here or on ' + remote if has_remote else ''}, so there's "
                     f"no {branch} branch to build on. Make a first commit on {branch}" +
                     (f" and push it to {remote}" if has_remote else "") +
                     " (an empty one will do), then run this again")
        e.next = next_cmd(f"git -C {shlex.quote(wt)} checkout -q -B {branch} && git -C {shlex.quote(wt)} commit "
                          f"--allow-empty -m 'Initial commit'{push}", "lead",
                          "a first commit gives the loop a base to land plans and records on; it carries no files, "
                          "so nothing of yours goes in it")
        return e
    if prof["integrate"] == "push" and has_remote and \
            git(worktree, "ls-remote", "--exit-code", "--heads", remote, branch).returncode == 2:
        e = TipError(f"{remote} has no {branch} branch yet; push it (`git push -u {remote} {branch}`), then run this "
                     "again")
        e.next = next_cmd(f"git -C {shlex.quote(wt)} push -u {remote} {branch}", "lead",
                          f"Integrate: push builds on {remote}/{branch}, which doesn't exist until it's pushed")
        return e
    return None


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


def reflog_size(tree: Path) -> int:
    return len(git(tree, "reflog", "--format=%H", "HEAD").stdout.splitlines())


def commits_made(tree: Path, seen: int) -> list[str]:
    """`<sha> <reflog subject>` for each commit made in this checkout since `seen` reflog entries: a commit, amend,
    cherry-pick, revert, rebase step or merge commit. A fast-forward or reset makes no commit, so it isn't listed."""
    lines = git(tree, "reflog", "--format=%h%x09%gs", "HEAD").stdout.splitlines()
    made = []
    for line in lines[:max(0, len(lines) - seen)]:
        sha, _, subject = line.partition("\t")
        if subject.startswith(("commit", "cherry-pick", "revert", "rebase (pick)", "rebase (continue)",
                               "rebase (reword)", "rebase (squash)", "rebase (fixup)", "rebase (edit)")) \
                or "Merge made by" in subject:
            made.append(f"{sha} {subject[:80]}")
    return list(reversed(made))


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


def changed_items(before: dict, after: dict) -> list[str]:
    """What a design re-review should read: each item (or milestone) added, removed or redefined between two
    done-when documents, as `M2.3 changed`, `M3 added` and the like, in the newer document's order."""
    def index(doc: dict) -> tuple[dict, dict]:
        ms, items = {}, {}
        for m in doc.get("milestones") or []:
            ms[m.get("id")] = (m.get("bar"), m.get("needs") or [])
            items[m.get("id")] = {i.get("id"): {k: i.get(k) for k in DEFINITION_KEYS} for i in m.get("items") or []}
        return ms, items
    (old_ms, old_items), (new_ms, new_items) = index(before), index(after)
    out = []
    for mid, spec in new_ms.items():
        if mid not in old_ms:
            out.append(f"{mid} added")
            continue
        if spec != old_ms[mid]:
            out.append(f"{mid}'s bar or needs changed")
        was, now = old_items[mid], new_items[mid]
        out += [f"{iid} added" if iid not in was else f"{iid} changed" for iid in now if now[iid] != was.get(iid)]
        out += [f"{iid} removed" for iid in was if iid not in now]
    return out + [f"{mid} removed" for mid in old_ms if mid not in new_ms]


def design_changes(worktree: Path, rec: dict, done_path: str, now: dict) -> str:
    """The sentence a design re-review's prompt carries: what changed in the done-when file since the last design
    review, so the reviewer reads those items rather than working the diff out. Empty for a first review."""
    last = rec.get("design") or {}
    if not last.get("commit"):
        return ""
    try:
        then = json.loads(show(worktree, last["commit"], done_path) or "")
    except (json.JSONDecodeError, SystemExit):
        return ""
    where = f"{last.get('review') or 'the last design review'}, at {last['commit'][:12]}"
    changed = changed_items(then, now)
    if not changed:
        return f"No item's definition has changed since the last design review ({where}). "
    return (f"Since the last design review ({where}), these changed in {done_path}: {', '.join(changed)}. Read each "
            "one against that review's findings. ")


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

def adopt(doc: dict, design: str, as_it_stands: bool = False) -> dict:
    """The record for a module the loop hasn't seen before: its definitions authorised, nothing accepted, and its
    design review owed. `as_it_stands` (only for a repository that has never had a loop record: a project taking up
    the loop with work already done) also accepts its finished milestones, and takes a module already part-built to
    have had its design agreed."""
    rec = {"module": doc.get("module"), "adopted": True, "design": None, "milestones": {}}
    for m in doc["milestones"]:
        entry = {"definitions": definitions(m), "authorised": {"by": "adopted"}, "reviews": []}
        if as_it_stands and m.get("state") == "done" and (not needs_review(m, doc) or
                                                          all(i.get("verdict") == "pass" for i in m["items"])):
            entry["accepted"] = {"by": "adopted"}
        rec["milestones"][m["id"]] = entry
    if any(e.get("accepted") for e in rec["milestones"].values()):
        rec["design"] = {"verdict": "ok", "hash": design, "by": "adopted"}
    return rec


def unrecorded(worktree: Path, prof: dict, ref: str) -> bool:
    """Whether the repository at `ref` has never had a loop record: none at `ref`, and no commit reachable from it
    ever touched one. Only then is a module adopted as it stands; once the loop has written any record, a module it
    has no record for is new, whoever landed it and however."""
    glob = f":(glob){prof['plans']}/*-ACCEPTED.json"
    listing = git(worktree, "ls-tree", "--name-only", f"{ref}:{prof['plans']}").stdout.split()
    if any(n.endswith("-ACCEPTED.json") for n in listing):
        return False
    return not git(worktree, "log", "-1", "--format=%H", ref, "--", glob).stdout.strip()


def take_up(tree: Path, prof: dict) -> list[str]:
    """In the loop's first record-keeping commit in a repository that had no records, writes the record of every
    module still without one, adopted as it stands, so those modules keep what the loop took them as once records
    exist. Returns the paths written."""
    written = []
    folder = tree / prof["plans"]
    for path in sorted(folder.glob("*-DONE.json")) if folder.exists() else []:
        stem = path.name[:-len("-DONE.json")]
        rec_path = tree / record_rel(prof, stem)
        if rec_path.exists():
            continue
        try:
            doc = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if validate(doc, stem.upper()):
            continue
        design = folder / f"{stem}.md"
        write_json(rec_path, adopt(doc, text_hash(design.read_text() if design.exists() else None), True))
        written.append(record_rel(prof, stem))
    return written


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
    """Every module at `ref`: {MODULE: {stem, doc, record, design, problems}}, with records adopted where missing
    (as they stand only in a repository that has never had a loop record)."""
    out = {}
    listing = git(worktree, "ls-tree", "--name-only", f"{ref}:{prof['plans']}")
    legacy = None  # asked only when a module has no record
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
            if legacy is None:
                legacy = unrecorded(worktree, prof, ref)
            rec = adopt(doc, design, legacy)
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
                f"{m['id']}: its definitions aren't the ones last authorised by a planner turn, the owner, or "
                f"`adopt` while the module was a draft (see {e['stem']}-ACCEPTED.json); re-plan it, or run "
                "`owner scope`"]}
        if m.get("state") == "parked":
            return {**out, "status": "parked"}
        if m.get("state") == "blocked":
            return {**out, "status": "blocked", "blocked": m.get("blocked", ""),
                    **({"attended": held} if (held := open_attended(m)) else {})}
        if not design_ok(rec, e["design"]):
            return {**base, "status": "design_owed"}
        if escalation(int(m.get("fails", 0)), int(m.get("replans", 0))) == "replan":
            # four failed reviews: the plan is wrong, and another build round would only repeat them
            return {**out, "status": "replan_owed", "fails": int(m.get("fails", 0))}
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


# ------------------------------------------------------------------------------------- what to do next, and plans

def loop_cmd(*args) -> str:
    """A command line for this loop, as a person or the lead would type it."""
    return shlex.join(["python3", str(LOOP), *[str(x) for x in args]])


RUNS_FILE = "last-runs.json"  # per module: the host and review host of its latest build run
RUN_HERE: dict = {}  # this process's own run, which outranks the file


def note_run(worktree: Path, module: str, host: str, review: str) -> None:
    """Records the host and review host this build run of `module` uses, so a `next` printed later, by any command
    in any worktree of the repository, keeps them. Local to this machine; never fails."""
    entry = {"host": host, "review_host": review, "at": now()}
    RUN_HERE[module.upper()] = entry
    try:
        path = loop_dir(worktree) / RUNS_FILE
        with held("last-runs", worktree):
            runs = json.loads(path.read_text()) if path.exists() else {}
            runs[module.upper()] = entry
            path.with_suffix(".tmp").write_text(json.dumps(runs, indent=2))
            os.replace(path.with_suffix(".tmp"), path)
    except Exception:
        pass


def known_run(worktree: str, module: str) -> dict:
    """The hosts of the latest build run of `module` in the repository `worktree` belongs to, or {}: this process's
    own, else the repository's file."""
    if module.upper() in RUN_HERE:
        return RUN_HERE[module.upper()]
    try:
        return json.loads((Path(git_common_dir(Path(worktree))) / "orchestrate" / RUNS_FILE).read_text()).get(
            module.upper()) or {}
    except Exception:
        return {}


def fit_command(command: str | None) -> str | None:
    """A `run` or design `review` command given the hosts of the module's latest build run on this machine, where it
    names none: the host and review host on `run`, the review host on a design review. The worktree is left as the
    command names it. A milestone review gets no host here: `review` takes the builder's from the claim record."""
    prefix = shlex.join(["python3", str(LOOP)]) + " "
    if not isinstance(command, str) or not command.startswith(prefix):
        return command
    try:
        argv = shlex.split(command)
    except ValueError:
        return command
    flag = lambda name: argv.index(name) + 1 if name in argv and argv.index(name) + 1 < len(argv) else None
    w, m = flag("--worktree"), flag("--module")
    if len(argv) < 3 or argv[2] not in ("run", "review") or w is None or m is None:
        return command
    design = argv[2] == "review" and flag("--milestone") is not None and argv[flag("--milestone")] == "design"
    if argv[2] == "review" and not design:
        return command
    known = known_run(argv[w], argv[m])
    if not known:
        return command
    if argv[2] == "run":
        if "--host" not in argv and known.get("host"):
            argv += ["--host", known["host"]]
        if "--review-host" not in argv and known.get("review_host"):
            argv += ["--review-host", known["review_host"]]
    elif "--host" not in argv and known.get("review_host"):
        argv += ["--host", known["review_host"]]
    return shlex.join(argv)


def fit_next(then):
    """`fit_command` over a `next` field's commands, nested `then`s included."""
    if isinstance(then, dict):
        return {k: (fit_command(v) if k in ("command", "then", "alternative") and isinstance(v, str) else
                    fit_next(v) if k == "then" else v) for k, v in then.items()}
    return then


def next_cmd(command: str | None, by: str, why: str, **more) -> dict:
    """The `next` field: the exact command to run, who runs it (`lead`, or `owner` for decisions only the owner may
    make, which the loop never runs itself), and why."""
    return {"command": command, "by": by, "why": why, **more}


def plan_task(module: str, problems: list[str]) -> str:
    return f"Fix {module}'s done-when file: " + "; ".join(problems)[:400]


def review_rounds(worktree: Path, prof: dict, module: str, mid: str) -> tuple[list[str], bool]:
    """(the review files of every round against the milestone's current definitions, oldest first; whether some of
    those rounds were overwritten before rounds were kept), read from the record at the last-fetched tip."""
    try:
        rec = json.loads(show(worktree, base_ref(prof), record_rel(prof, module)) or "{}")
    except (json.JSONDecodeError, SystemExit):
        rec = {}
    e = (rec.get("milestones") or {}).get(mid) or {}
    since = (e.get("authorised") or {}).get("at") or ""
    rounds = [r for r in e.get("reviews") or [] if (r.get("at") or "") >= since]
    return [r["review"] for r in rounds if r.get("review")], any(r.get("review_in_history") for r in rounds)


def replan_task(module: str, mid: str, fails: int, prof: dict, worktree: Path | None = None) -> str:
    """The planner's task when the ladder reaches a re-plan: which milestone, why, and each round's review."""
    latest = f"{prof['evidence']}/{module}/{mid}-review.md"
    files, lost = review_rounds(worktree, prof, module, mid) if worktree else ([], True)
    where = (f"Its reviews, one per round: {', '.join(files)}" if files else f"The latest review is {latest}") + \
        (f" (earlier rounds are only in git history: git log -p -- {latest})" if lost or not files else "")
    return (f"Re-plan {module} {mid}: it has failed review {fails} times, so the plan is wrong (plan-module, \"When a "
            f"milestone fails review four times\"). {where}. Find what keeps failing and change the definitions of "
            f"{mid} so it can be met; the loop resets its fails, counts the re-plan and opens it when your plan lands")


def keep_round(tree: Path, current: Path) -> tuple[str, list[str]]:
    """Keeps `current` (a review about to be replaced) as <name>-N.md beside it, reusing a copy `owner rereview`
    already made of the same text. Its captures folder <name>/ is copied beside it, to <name>-N/, and the kept file's
    links to it are rewritten, so each round keeps its own evidence. The folder itself stays, so the next round's
    captures land among the earlier ones, replacing any with the same name. Returns the kept file's path relative
    to `tree`, and every path written."""
    text, stem = current.read_text(), current.name[:-len(".md")]
    copies = sorted((p for p in current.parent.glob(f"{stem}-*.md") if re.fullmatch(rf"{re.escape(stem)}-\d+\.md", p.name)),
                    key=lambda p: int(p.name[len(stem) + 1:-3]))
    same = next((p for p in copies if p.read_text() == text), None)
    if same is None:
        n = 1
        while current.with_name(f"{stem}-{n}.md").exists():
            n += 1
        same = current.with_name(f"{stem}-{n}.md")
        shutil.copy(current, same)
    touched = [str(same.relative_to(tree))]
    folder, dest = current.with_name(stem), current.with_name(same.name[:-len(".md")])
    files = sorted(p for p in folder.rglob("*") if p.is_file() or p.is_symlink()) if folder.is_dir() else []
    if files:  # copied, not moved, so a later review that links an earlier capture still finds it
        for p in files:
            target = dest / p.relative_to(folder)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(p), str(target), follow_symlinks=False)
            touched.append(str(target.relative_to(tree)))
        same.write_text(re.sub(rf"(?<![\w.-]){re.escape(stem)}/", f"{dest.name}/", same.read_text()))
    return touched[0], touched


def settle_replans(before: dict | None, after: dict, stem: str) -> list[str]:
    """The re-plan's bookkeeping, done by the loop: each milestone that was owed a re-plan in `before` and whose
    definitions `after` changes gets fails 0, one more replans than before, and state open, whatever the planner or
    owner wrote there (so a forgotten count doesn't send the lead round again, and a done one isn't counted twice).
    Returns the milestones it settled, as `STEM Mn`."""
    old = {m.get("id"): m for m in (before or {}).get("milestones") or [] if isinstance(m, dict)}
    out = []
    for m in after.get("milestones") or []:
        was = old.get(m.get("id"))
        if not was or escalation(int(was.get("fails", 0)), int(was.get("replans", 0))) != "replan":
            continue
        if definitions(was) == definitions(m):
            continue  # nothing re-planned yet: still owed
        m.update(fails=0, replans=int(was.get("replans", 0)) + 1, state="open")
        m.pop("blocked", None)
        out.append(f"{stem} {m['id']}")
    return out


def ladder_next(word: str, module: str, mid: str, fails: int, worktree: Path, prof: dict) -> dict:
    """`next` after a failed milestone review: the ladder's word under `ladder`, with the command it calls for."""
    wt = str(worktree)
    findings = FINDINGS_TEMPLATE.format(milestone=mid, module=module, evidence=prof["evidence"])
    if word == "same-session":
        return next_cmd(loop_cmd("run", "--module", module, "--worktree", wt, "--message", findings), "lead",
                        f"{module} {mid} failed review {fails} time(s): resume the builder with the findings",
                        ladder=word)
    if word == "fresh-session":
        return next_cmd(loop_cmd("run", "--module", module, "--worktree", wt, "--fresh", "--message", findings),
                        "lead", f"{module} {mid} failed review {fails} times: start the builder again in a new "
                                "session with the findings", ladder=word)
    if word == "replan":
        return next_cmd(loop_cmd("plan", "--worktree", wt, "--task", replan_task(module, mid, fails, prof, worktree)),
                        "planner", f"{module} {mid} failed review {fails} times, so the ladder calls for a re-plan; "
                                   "`run` won't start a builder on it until the planner has changed its definitions",
                        ladder=word, findings=f"{prof['evidence']}/{module}/{mid}-review.md")
    return owner_next("unpark", module, mid, wt,
                      f"{module} {mid} failed review {fails} times after a re-plan and is parked. Unpark it for "
                      "another try, change its scope, accept it as it is, or leave it parked?",
                      f"{module} {mid} failed review {fails} times after a re-plan, so the loop parked it. Report "
                      "it; the decision is the owner's (`owner scope` or `owner accept` instead, if that's what they "
                      "choose)", ladder=word)


def open_attended(milestone: dict) -> list[str]:
    """The milestone's attended items that haven't passed: the ones only a person can clear."""
    return [i["id"] for i in milestone.get("items") or [] if i.get("attended") and i.get("status") != "pass"]


def owner_decisions(stem: str, rec: dict) -> list[tuple[str, str]]:
    """(when, report line) for every decision recorded in the owner's name in a module's record: `decisions`, and
    the stamps older records kept instead (an owner action, an answer typed or relayed, a design accepted, a scope)."""
    out = [(d.get("at") or "", f"- {stem} {d.get('milestone')}" + (f" {d['item']}" if d.get("item") else "") +
            f": {d.get('action')}, {d.get('at')}: \"{d.get('words')}\"") for d in rec.get("decisions") or []]
    old = lambda x: isinstance(x, dict) and x.get("by") == "owner"  # written before `decisions` existed
    for d in [rec.get("design"), *(rec.get("design_history") or [])]:
        if old(d):
            out.append((d.get("at") or "", f"- {stem} design: accept, {d.get('at')}: \"{d.get('reason')}\""))
    for mid, e in (rec.get("milestones") or {}).items():
        for x in e.get("owner") or []:
            out.append((x.get("at") or "", f"- {stem} {mid}: {x.get('action')}, {x.get('at')}: \"{x.get('reason')}\""))
        if old(e.get("authorised")):
            a = e["authorised"]
            out.append((a.get("at") or "", f"- {stem} {mid}: scope, {a.get('at')}: \"{a.get('reason')}\""))
        for x in e.get("owner_answers") or []:
            if "by" in x:
                out.append((x.get("at") or "", f"- {stem} {mid}" + (f" {x['item']}" if x.get("item") else "") +
                            f": answer, {x.get('at')}: \"{x.get('text')}\"" +
                            (" (recorded then as relayed by the lead)" if x.get("relayed") else "")))
    return out


def owner_cmd(verb: str, mod: str, mid: str, wt: str, item: str | None = None) -> str:
    """The `owner` command the lead runs once the owner has decided in chat, with their words to fill in."""
    return (loop_cmd("owner", verb, "--module", mod, "--milestone", mid, *(["--item", item] if item else []),
                     "--worktree", wt) + " --text '<the owner's words, as they gave them>'")


def owner_next(verb: str, mod: str, mid: str, wt: str, ask: str, why: str, **more) -> dict:
    """A stop that needs the owner: what the lead asks them in chat (`ask`), and the command it runs on their answer.
    `by: owner` because the decision is theirs; the lead records it, in their words."""
    return next_cmd(owner_cmd(verb, mod, mid, wt, more.pop("item", None)), "owner",
                    why + ". Ask the owner in chat; once they've decided, run the command with their words in --text, "
                    "as they gave them, and never decide for them", ask=ask, **more)


def attended_ask(worktree: Path, prof: dict, proj: dict | None, mod: str, mid: str, item: str, note: str = "") -> str:
    """What an attended item asks of the owner, for the lead to put to them in chat: the item as the done-when file
    states it, the builder's note, and where the evidence to show them is."""
    doc = ((proj or {}).get(mod.upper()) or {}).get("doc")
    if doc is None:
        try:
            doc = json.loads(show(worktree, base_ref(prof), done_rel(prof, mod)) or "{}")
        except json.JSONDecodeError:
            doc = {}
    m = next((x for x in doc.get("milestones") or [] if x.get("id") == mid), {})
    i = next((x for x in m.get("items") or [] if x.get("id") == item), {})
    what = (i.get("statement") or item) + (f" ({i['attended']})" if isinstance(i.get("attended"), str) else "")
    evidence = i.get("evidence") or f"{prof['evidence']}/{mod}/"
    return f"{item}: {what}" + (f". The builder's note: {note}" if note else "") + f". Evidence to show them: {evidence}"


def owner_answers_next(mod: str, mid: str, items: list[str], wt: str, ask) -> list[dict]:
    """For a blocked milestone with open attended items: what to ask the owner about each, and the command."""
    return [{"item": i, "ask": ask(i), "command": owner_cmd("answer", mod, mid, wt, i), "by": "owner"} for i in items]


def next_for(step: dict, worktree: Path, prof: dict, proj: dict | None = None, seen: set | None = None) -> dict | None:
    """What to run after a step that isn't ready, from the same facts `next_step` read. A WAITING step follows its
    first need to the module that has to move first."""
    wt, mod, mid, status = str(worktree), step["module"], step.get("milestone"), step["status"]
    if status == "ready":
        return next_cmd(loop_cmd("run", "--module", mod, "--worktree", wt), "lead",
                        f"{mod} {mid} is ready to build. Run it in the module's worktree; `run` fast-forwards a clean "
                        f"worktree that's behind {base_ref(prof)} itself, so there's no need to merge first")
    if status == "replan_owed":
        return ladder_next("replan", mod, mid, step.get("fails", 4), worktree, prof)
    if status == "design_owed":
        record = ((proj or {}).get(mod.upper()) or {}).get("record")
        # with `Review host: other` and a known planner, the host decided as everywhere else (a review host the
        # lead chose for this module's run is added later, by fit_next); otherwise `review` decides it
        named = prof.get("review_host") == "other" and ((record or {}).get("planner") or {}).get("host") \
            and not known_run(wt, mod).get("review_host")
        host = ["--host", design_review_host(prof, record, default_host(prof))] if named else []
        return next_cmd(loop_cmd("review", "--module", mod, "--milestone", "design", "--worktree", wt, *host), "lead",
                        f"{mod}'s design hasn't passed a design review, or changed since it did")
    if status == "review_owed":
        if step.get("state") == "claimed":
            return next_cmd(loop_cmd("review", "--module", mod, "--milestone", mid, "--commit",
                                     step.get("commit") or base_ref(prof), "--worktree", wt), "lead",
                            f"{mod} {mid} is claimed and waiting for its review")
        return owner_next("accept", mod, mid, wt,
                          f"{mod} {mid} says done in its file, but the loop never accepted it. Accept it without a "
                          "review, or have a builder set it back to claimed so it gets one?",
                          f"{mod} {mid} says done in its file, but the loop never accepted it")
    if status == "blocked" and ATTENDED_BLOCK in (step.get("blocked") or ""):
        listed, _, note = (step.get("blocked") or "").split(ATTENDED_BLOCK, 1)[1].strip().partition(". ")
        item = listed.rstrip(".").split(",")[0].strip() or "<item>"
        ask = lambda i: attended_ask(worktree, prof, proj, mod, mid, i, note.strip())
        return owner_next("answer", mod, mid, wt, ask(item),
                          f"{mod} {mid} waits on attended items only a person can do (one answer per item). The answer "
                          "goes into the loop's record, where the builder is told to read it and the reviewer can "
                          "check it, and puts the milestone back in the queue; then `run` resumes the builder. Don't "
                          "pass it through `run --message`: a reviewer can't tell those words from an agent's",
                          item=item, then=loop_cmd("run", "--module", mod, "--worktree", wt),
                          **({"owner_answers": owner_answers_next(mod, mid, step["attended"], wt, ask)}
                             if len(step.get("attended") or []) > 1 else {}))
    if status == "blocked":
        attended = step.get("attended") or []
        return next_cmd(loop_cmd("unblock", "--module", mod, "--milestone", mid, "--worktree", wt), "lead",
                        f"{mod} {mid} is blocked: {step.get('blocked') or 'see the done-when file'}. Supply what "
                        "unblocks it first; if another module owns it, or it's a design problem, plan instead" +
                        (f". Attended items {', '.join(attended)} also wait on the owner whatever else unblocks it: "
                         "`owner_answers` gives what to ask the owner about each, and the command for their answer"
                         if attended else ""),
                        **({"owner_answers": owner_answers_next(
                            mod, mid, attended, wt, lambda i: attended_ask(worktree, prof, proj, mod, mid, i))}
                           if attended else {}),
                        alternative=loop_cmd("plan", "--worktree", wt, "--task",
                                             f"Unblock {mod} {mid}: {step.get('blocked', '')}"[:300]))
    if status == "invalid":
        problems = step.get("problems") or []
        if any("aren't the ones last authorised" in p for p in problems):
            return next_cmd(loop_cmd("plan", "--worktree", wt, "--task", plan_task(mod, problems)), "lead",
                            f"{mod} {mid}'s definitions changed outside a planner turn. Re-plan them, or the owner "
                            "takes the edited file as the new scope",
                            owner=owner_cmd("scope", mod, mid, wt))
        return next_cmd(loop_cmd("plan", "--worktree", wt, "--task", plan_task(mod, problems)), "lead",
                        f"{mod}'s plan has problems only a planner turn may fix")
    if status == "waiting":
        first = (step.get("needs") or [""])[0]
        other, _, rest = first.partition(":")
        if rest.endswith("(not planned)"):
            return next_cmd(loop_cmd("plan", "--worktree", wt, "--task", f"Plan module {other}"), "lead",
                            f"{mod} {mid} needs {other}, which has no done-when file yet")
        why = f"{mod} {mid} needs {', '.join(step.get('needs') or [])}, not accepted yet"
        seen = (seen or set()) | {mod.upper()}
        if proj and other.upper() in proj and other.upper() not in seen:
            then = next_for(next_step(other.upper(), proj), worktree, prof, proj, seen)
            if then:
                return {**then, "why": f"{why}; {then['why']}"}
        return next_cmd(loop_cmd("run", "--module", other, "--worktree", wt), "lead", why)
    if status == "taken":
        return next_cmd(loop_cmd("ready", "--worktree", wt), "lead",
                        f"{mod} {mid} is held by {step.get('by')}; give the builder other ready work. If that lead is "
                        "gone for good, `owner` under it releases the claim, once the owner says so in chat",
                        owner=owner_cmd("release", mod, mid, wt))
    if status == "parked":
        return owner_next("unpark", mod, mid, wt,
                          f"{mod} {mid} is parked after its reviews and a re-plan ran out. Unpark it for another try, "
                          "change its scope, or leave it parked?",
                          f"{mod} {mid} is parked after its reviews and re-plan ran out (`owner scope` instead, if "
                          "that's what the owner chooses)")
    return None


NEXT_ORDER = ("review_owed", "replan_owed", "design_owed", "blocked", "invalid", "waiting", "taken", "parked")


def nothing_ready_next(steps: list[dict], worktree: Path, prof: dict, proj: dict) -> dict:
    """For `ready` when nothing is: the most useful next command across the modules, or planning when there are
    none, or nothing when all are finished."""
    for status in NEXT_ORDER:
        for step in steps:
            if step["status"] == status and (out := next_for(step, worktree, prof, proj)):
                return out
    if not steps:
        return next_cmd(loop_cmd("plan", "--worktree", str(worktree), "--task", "Plan the project"), "lead",
                        f"no done-when files at the integrated tip, under {prof['plans']}")
    return next_cmd(None, "lead", "every module is finished; plan more work with `plan` if the build order "
                                  "isn't done")


def file_at(worktree: Path, ref: str, rel: str) -> bytes | None:
    r = subprocess.run(["git", "-C", str(worktree), "show", f"{ref}:{rel}"], capture_output=True)
    return r.stdout if r.returncode == 0 else None


def file_here(worktree: Path, rel: str) -> bytes | None:
    path = worktree / rel
    return path.read_bytes() if path.is_file() else None


def names(r: subprocess.CompletedProcess) -> set[str]:
    return {n for n in r.stdout.split("\0") if n}


PROFILE_FILE = "ORCHESTRATE.md"


def folder_drift(worktree: Path, folder: str, ref: str) -> dict[str, list[str]]:
    """Files under `folder` here that the integrated tip doesn't have, uncommitted or committed but not integrated.
    Only files whose content here differs from the tip's count, so a worktree that is merely behind reports none."""
    uncommitted = names(git(worktree, "diff", "-z", "--name-only", "HEAD", "--", folder))
    uncommitted |= names(git(worktree, "ls-files", "-z", "--others", "--exclude-standard", "--", folder))
    base = git(worktree, "merge-base", "HEAD", ref).stdout.strip()
    committed = names(git(worktree, "diff", "-z", "--name-only", base, "HEAD", "--", folder)) if base else set()
    differs = lambda rel: file_here(worktree, rel) != file_at(worktree, ref, rel)
    return {"uncommitted": sorted(p for p in uncommitted if differs(p)),
            "unintegrated": sorted(p for p in committed - uncommitted if differs(p))}


def plan_drift(worktree: Path, prof: dict, ref: str) -> dict:
    """Plan files in this worktree that the integrated tip doesn't have: uncommitted (edited, staged or untracked) or
    committed but not integrated. `run` and `ready` read plans at the tip, so these are invisible to them. A profile
    the tip doesn't have at all is part of a first plan, so it counts too. One the tip has in another form is only
    named, under `profile_differs`: the lead commits it once the owner has agreed."""
    out = folder_drift(worktree, prof["plans"], ref)
    here, there = file_here(worktree, PROFILE_FILE), file_at(worktree, ref, PROFILE_FILE)
    if here is not None and there is None:
        key = "unintegrated" if file_at(worktree, "HEAD", PROFILE_FILE) == here else "uncommitted"
        out[key] = sorted(out[key] + [PROFILE_FILE])
    # merely behind isn't a difference to commit: the profile here must differ from this branch's own commit of it,
    # or that commit must have changed it since the branch left the tip (folder_drift's merge-base guard)
    base = git(worktree, "merge-base", "HEAD", ref).stdout.strip()
    committed = file_at(worktree, "HEAD", PROFILE_FILE)
    out["profile_differs"] = (here is not None and there is not None and here != there
                              and (here != committed or not base or committed != file_at(worktree, base, PROFILE_FILE)))
    return out


def profile_note(drift: dict, prof: dict) -> dict:
    """`profile_differs` for `ready`: the working copy's ORCHESTRATE.md isn't the one at the tip, which every clean
    checkout (builders, reviewers, the loop's checks) reads."""
    if not drift.get("profile_differs"):
        return {}
    return {"profile_differs": f"this worktree's {PROFILE_FILE} differs from the one at {base_ref(prof)}, which "
                               "builders, reviewers and the loop's checks read. The lead commits and integrates a "
                               "changed profile once the owner has agreed to it; the loop doesn't land it"}


def drift_fields(drift: dict, worktree: Path, step_next: dict | None = None) -> dict:
    """The fields a result carries when plan files haven't landed: the files, and `adopt` as the next command, with
    what would have been next anyway under `then`."""
    if not (drift["uncommitted"] or drift["unintegrated"]):
        return {"next": step_next} if step_next else {}
    drift = {k: drift[k] for k in ("uncommitted", "unintegrated")}
    files = drift["uncommitted"] + drift["unintegrated"]
    note = (f"the loop reads plans at the integrated tip, and these plan files aren't there: {', '.join(files[:10])}"
            + (" (uncommitted)" if drift["uncommitted"] and not drift["unintegrated"] else
               " (committed here, not integrated)" if not drift["uncommitted"] else ""))
    return {"unlanded_plans": {**drift, "note": note},
            "next": next_cmd(loop_cmd("adopt", "--worktree", str(worktree)), "lead",
                             f"{note}. `adopt` commits only those plan files and integrates them; then run this "
                             "again", **({"then": step_next} if step_next else {}))}


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
             env: dict | None = None, tick=None) -> tuple[int, str, str]:
    """Runs a command in its own process group, so a timeout or a pause stops everything it started. 124 means it
    timed out, 130 that it was stopped, 127 that the command couldn't start. `tick` is called about once a second
    while it runs."""
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
            if tick:
                tick()
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


LOCK_PATIENCE_S = 0.5  # how long a run waits out a lock another process holds for a moment (an older `pause`)


def take_file_lock(path: Path, patience_s: float = 0.0):
    """An open handle holding the exclusive flock on `path`, or None if another process holds it. Run locks are
    never removed (an older copy of this script locks without checking the file is still the one at the path, so
    removing one could let two runs hold "it"), but a loop's own record lock is, so the handle is checked to still be
    the file at `path`, and taken again if it isn't. `patience_s` retries a held lock for that long, because an older
    copy's `pause` holds a run lock for a moment, and that mustn't turn a start into TAKEN."""
    deadline = time.time() + patience_s
    while True:
        handle = open(path, "a+")
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            handle.close()
            if time.time() < deadline:
                time.sleep(0.02)
                continue
            return None
        try:
            if os.fstat(handle.fileno()).st_ino == os.stat(path).st_ino:
                return handle
        except FileNotFoundError:
            pass
        handle.close()


def run_lock(worktree: Path, name: str) -> bool:
    """Takes this process's exclusive hold on a module (or the planner) without waiting, and records the pid so
    `pause` can find it. False if another run holds it. The kernel drops the lock when the process ends; the file
    stays, holding the last holder's pid, which `run_holder` checks is still that run before believing it."""
    path = loop_dir(worktree) / f"run-{name}.lock"
    handle = take_file_lock(path, LOCK_PATIENCE_S)
    if handle is None:
        return False
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    _HELD.append(handle)
    _RUN_LOCKS.append((path, handle))
    return True


def run_holder(folder: Path, name: str) -> int | None:
    """The pid of the live run holding `run-<name>.lock` in the repository's loop folder, or None. It never locks
    the run lock, even for a moment, because an older copy of this script takes it without waiting and would be
    turned away. It reads the pid the holder wrote, then checks that process is that run: by its own `loops` record
    (live while it holds its record lock, which no run takes), else by the process table (an agent_loop run, review
    or plan for this module, started before the pid was written, so a reused pid doesn't count)."""
    path = folder / f"run-{name}.lock"
    try:
        pid = int(path.read_text().strip())
        written = path.stat().st_mtime
    except (OSError, ValueError):
        return None
    try:
        rec = json.loads((LOOPS_DIR / f"{pid}.json").read_text())
        if rec.get("pid") == pid and lock_held(LOOPS_DIR / f"{pid}.lock") and \
                (rec.get("started_at") or 0) <= written + 2:
            return pid
    except (OSError, ValueError, AttributeError):
        pass
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return None
    except PermissionError:
        pass
    try:
        out = subprocess.run(["ps", "-p", str(pid), "-o", "etime=", "-o", "args="], capture_output=True, text=True,
                             timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    if not out:
        return None
    elapsed, _, args = out.partition(" ")
    args = args.strip()
    running = etime_s(elapsed.strip())
    argv = args.split()
    if running is None or time.time() - running > written + 2 or \
            not any(Path(t).name == "agent_loop.py" for t in argv):
        return None
    if name == "_plan":
        return pid if "plan" in argv else None
    module = next((argv[i + 1] if t == "--module" else t.split("=", 1)[1] for i, t in enumerate(argv)
                   if (t == "--module" and i + 1 < len(argv)) or t.startswith("--module=")), None)
    return pid if module and module.upper() == name.upper() else None


def run_holder_info(worktree: Path, name: str) -> dict:
    """Who holds a run lock, for TAKEN: the pid and, from its `loops` record, its role, milestone, worktree and start.
    Empty when no live process holds it (it ended in between)."""
    try:
        pid = run_holder(Path(git_common_dir(worktree)) / "orchestrate", name)
    except Exception:
        return {}
    if pid is None:
        return {}
    rec = next((r for r in live_loops(clean=False, processes=False)[0] if r.get("pid") == pid), None)
    if not rec:
        return {"pid": pid}
    return {"pid": pid, **{k: rec.get(k) for k in ("role", "milestone", "worktree", "host")},
            "since": iso(rec.get("started_at"))}


def holder_text(info: dict) -> str:
    if not info:
        return ""
    where = f" in {info['worktree']}" if info.get("worktree") else ""
    since = f" since {info['since']}" if info.get("since") else ""
    what = " ".join(x for x in (info.get("role"), info.get("milestone")) if x)
    return f" ({what + ', ' if what else ''}pid {info['pid']}{where}{since})"


def lock_held(path: Path) -> bool:
    """Whether a live process holds the flock on `path`. The kernel drops a flock when its process dies, however it
    dies, so this is never fooled by a dead process or a reused pid. Opens read-only, so it works on a read-only .git."""
    try:
        with open(path) as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_SH | fcntl.LOCK_NB)
                return False
            except BlockingIOError:
                return True
    except OSError:
        return False


# ------------------------------------------------------------------------------------------------- running loops
#
# Every `run`, `review` and `plan` process keeps a small record of itself in one folder per user, so `loops` can list
# what's running in every repository, whichever copy of this script started it. The repository's own folder can't do
# that, because nothing would know which repositories to look in. A record counts only while its process holds the
# flock on the `.lock` beside it. Writing records is best effort: where the folder can't be written (a sandboxed home)
# the loop runs exactly as before, and `loops` still finds it in the process table, with what its command line says.

LOOPS_DIR = Path(os.environ.get("ORCHESTRATE_LOOPS_DIR") or
                 Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state") / "orchestrate" / "loops")
LIVE: dict = {}  # this process's record while it has one; empty when it has none or it couldn't be written
_LIVE_LOCK: list = []  # the handle holding the record's lock
_RUN_LOCKS: list = []  # (path, handle) for each run lock this process holds
ORPHAN_S = 60.0  # a lock or temporary file with no record is left this long, in case its process is just starting
LOOP_ROLES = ("run", "review", "plan")
CONTEXT: dict = {}  # what this process is doing (role, module, milestone, task), for the usage ledger
CONTEXT_KEYS = ("role", "module", "milestone", "task")
HOSTS_USED: set = set()  # hosts this process ran turns on; the Codex quota block goes only on Codex results
_COMMON: dict = {}  # worktree -> git common dir, so the ledger costs one git call per tree


def last_session_cost(worktree: Path, session: str) -> float:
    """The session's last total cost (Claude's cumulative `total_cost_usd`) from the usage ledger, or 0."""
    try:
        path = Path(git_common_dir(worktree)) / "orchestrate" / "usage.jsonl"
        last = 0.0
        for line in path.read_text().splitlines():
            if session in line:
                try:
                    row = json.loads(line)
                except ValueError:
                    continue
                if row.get("session") == session and isinstance(row.get("session_cost_usd"), (int, float)):
                    last = row["session_cost_usd"]
        return last
    except Exception:
        return 0.0


def note_usage(worktree: Path, host: str, model: str, effort: str, session: str | None, code: int,
               session_cost: float | None = None) -> None:
    """Appends the turn's tokens to the repository's usage ledger (<git common dir>/orchestrate/usage.jsonl), which
    `cost` and `report` read. Every turn goes in, paused and failed ones too, with `incomplete_turns` where the host
    showed no tokens or only some. Local to this machine; never fails the caller."""
    try:
        key = str(worktree)
        if key not in _COMMON:
            inside = subprocess.run(["git", "-C", key, "rev-parse"], capture_output=True).returncode == 0
            _COMMON[key] = git_common_dir(worktree) if inside else None
        if not _COMMON[key]:
            return
        line = {"at": now(), **{k: CONTEXT.get(k) for k in CONTEXT_KEYS}, "host": host, "model": model,
                "effort": effort, "session": session, "path": SESSION_PATH.get("path"), "exit": code,
                "usage": dict(TURN_USAGE), **({"session_cost_usd": session_cost} if session_cost is not None else {})}
        folder = Path(_COMMON[key]) / "orchestrate"
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / "usage.jsonl", "a") as handle:
            handle.write(json.dumps(line) + "\n")
    except Exception:
        pass


def repository_of(common_dir: str) -> str:
    """The repository a git common dir belongs to: the folder holding `.git`, or the common dir of a bare one."""
    path = Path(common_dir)
    return str(path.parent if path.name == ".git" else path)


def loop_register(worktree: Path, role: str, **fields) -> None:
    """Starts this process's record. Never fails the caller: on any error the loop simply has no record."""
    loop_end(run_locks=False)
    CONTEXT.clear()
    CONTEXT.update({"role": role, **{k: fields.get(k) for k in CONTEXT_KEYS if k != "role"}})
    try:
        common = git_common_dir(worktree)
        stamp = time.time()
        record = {"pid": os.getpid(), "role": role, "repository": repository_of(common), "git_dir": common,
                  "worktree": str(worktree), "module": None, "milestone": None, "host": None, "model": None,
                  "effort": None, "path": None, "started_at": stamp, "turns": 0, "activity_at": stamp,
                  "session": None, "transcript": None, "usage": {}, "loop": str(LOOP),
                  "run_lock": str(_RUN_LOCKS[-1][0]) if _RUN_LOCKS else None, **fields}
        LOOPS_DIR.mkdir(parents=True, exist_ok=True)
        handle = take_file_lock(LOOPS_DIR / f"{os.getpid()}.lock")
        if handle is None:
            return
        _LIVE_LOCK.append(handle)
        LIVE.update(record)
        loop_note()
    except Exception:
        loop_end(run_locks=False)


def loop_note(**fields) -> None:
    """Updates this process's record, if it has one. Never fails the caller."""
    CONTEXT.update({k: v for k, v in fields.items() if k in CONTEXT_KEYS})
    if not LIVE:
        return
    LIVE.update(fields)
    try:
        tmp = LOOPS_DIR / f".{os.getpid()}.json.tmp"
        tmp.write_text(json.dumps(LIVE))
        os.replace(tmp, LOOPS_DIR / f"{os.getpid()}.json")
    except Exception:
        pass


def loop_end(run_locks: bool = True) -> None:
    """Removes this process's record, and forgets its run locks when it ends (their files stay; see run_lock).
    Runs at exit; never raises."""
    if run_locks:
        _RUN_LOCKS.clear()
    for handle in _LIVE_LOCK:
        for name in (f"{os.getpid()}.json", f"{os.getpid()}.lock"):
            try:
                (LOOPS_DIR / name).unlink()
            except OSError:
                pass
        handle.close()
    _LIVE_LOCK.clear()
    LIVE.clear()


atexit.register(loop_end)


def transcript_for(host: str, session: str | None) -> str | None:
    """The session file whose growth shows the agent is working: Codex's rollout or Claude's transcript."""
    if not session:
        return None
    path = rollout_for(session) if host == "codex" else claude_transcript(session) if host == "claude" else None
    return str(path) if path else None


def clear_dead(path: Path, rec: dict | None) -> list[str]:
    """Removes what a dead loop left in the loops folder: its record and lock. Its run lock in the repository is
    left alone; see run_lock."""
    removed = []
    pid = path.name.lstrip(".").split(".")[0]
    lock = LOOPS_DIR / f"{pid}.lock"
    handle = None
    try:
        handle = take_file_lock(lock) if lock.exists() else None
        if lock.exists() and handle is None:
            return removed  # a live process with this pid has taken it since
        for p in (path, LOOPS_DIR / f".{pid}.json.tmp", lock):
            try:
                p.unlink()
                removed.append(str(p))
            except FileNotFoundError:
                pass
    except OSError:
        pass
    finally:
        if handle is not None:
            handle.close()
    return removed


def etime_s(text: str) -> float | None:
    """Seconds from ps's elapsed time, [[dd-]hh:]mm:ss."""
    days, _, rest = text.rpartition("-")
    try:
        parts = [int(p) for p in rest.split(":")]
        return float(int(days or 0) * 86400 + sum(v * 60 ** i for i, v in enumerate(reversed(parts))))
    except ValueError:
        return None


def process_cwd(pid: int) -> str | None:
    """Another process's working directory, from /proc on Linux or lsof on macOS; None where neither can say."""
    try:
        return os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        pass
    try:
        out = subprocess.run(["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"], capture_output=True, text=True,
                             timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    return next((line[1:] for line in out.splitlines() if line.startswith("n/")), None)


def loop_processes() -> list[dict]:
    """Loops in the process table (`python … agent_loop.py run|review|plan …`), with what their command lines say
    and, for a build, what its run state shows once this run has written it. This finds loops that have no record:
    started by a copy of the script that doesn't keep one, or one that couldn't write it. ps doesn't quote
    arguments, so a value with spaces (a plan's task) isn't read."""
    try:
        out = subprocess.run(["ps", "-A", "-o", "pid=", "-o", "etime=", "-o", "args="], capture_output=True,
                             text=True, timeout=10).stdout
    except (OSError, subprocess.SubprocessError):
        return []
    found = []
    for line in out.splitlines():
        parts = line.split(None, 2)
        if len(parts) < 3 or not parts[0].isdigit() or int(parts[0]) == os.getpid():
            continue
        argv = parts[2].split()
        if not Path(argv[0]).name.lower().startswith("python"):
            continue
        script = next((i for i, t in enumerate(argv[1:], 1) if not t.startswith("-")), None)
        if script is None or Path(argv[script]).name != "agent_loop.py" or len(argv) <= script + 1 \
                or argv[script + 1] not in LOOP_ROLES:
            continue
        flags = {}
        rest = argv[script + 2:]
        for i, t in enumerate(rest[:-1]):
            if t in ("--module", "--milestone", "--worktree", "--host", "--model", "--effort"):
                flags[t[2:]] = rest[i + 1]
        running, pid = etime_s(parts[1]), int(parts[0])
        role = "build" if argv[script + 1] == "run" else argv[script + 1]
        worktree = flags.get("worktree") or "."
        if not Path(worktree).is_absolute() and (cwd := process_cwd(pid)):
            worktree = os.path.normpath(os.path.join(cwd, worktree))
        rec = {"pid": pid, "role": role, "loop": argv[script], "repository": None, "worktree": worktree,
               "module": flags.get("module"), "milestone": flags.get("milestone"), "host": flags.get("host"),
               "model": flags.get("model"), "effort": flags.get("effort"),
               "started_at": time.time() - running if running is not None else None}
        if Path(worktree).is_absolute() and Path(worktree).is_dir():
            inside = subprocess.run(["git", "-C", worktree, "rev-parse", "--absolute-git-dir"], capture_output=True,
                                    text=True)
            if inside.returncode == 0:
                rec["repository"] = repository_of(git_common_dir(Path(worktree)))
                if role == "build" and rec["module"]:
                    rec.update(run_state_view(Path(inside.stdout.strip()) / "orchestrate", rec["module"],
                                              rec["started_at"]))
        found.append(rec)
    return found


def run_state_view(folder: Path, module: str, started_at: float | None) -> dict:
    """What a build's run state (<git dir>/orchestrate/<module>.json) says, when this run has written it since it
    started: milestone, host, model, effort, path, and its last write as the last sign of activity."""
    for name in dict.fromkeys((module, module.upper())):
        path = folder / f"{name}.json"
        try:
            written = path.stat().st_mtime
            if started_at is None or written < started_at:
                continue
            state = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        return {k: v for k, v in {"milestone": state.get("milestone"), "host": state.get("host"),
                                  "model": state.get("model"), "effort": state.get("effort"),
                                  "path": state.get("path"), "activity_at": written}.items() if v}
    return {}


def live_loops(repo: str | None = None, clean: bool = True, processes: bool = True) -> tuple[list[dict], list[str]]:
    """(every live loop on this machine, the files removed because their loop had died). `repo` narrows the loops
    to one repository. Records come first; with `processes`, loops found only in the process table follow, marked
    unregistered."""
    loops, removed, pids = [], [], set()
    try:
        files = sorted(LOOPS_DIR.iterdir())
    except OSError:
        files = []
    for path in files:
        name = path.name
        if name.endswith(".json") and not name.startswith(".") and name[:-5].isdigit():
            try:
                rec = json.loads(path.read_text())
            except (OSError, ValueError):
                rec = None
            if lock_held(LOOPS_DIR / f"{name[:-5]}.lock") and rec:
                pids.add(rec.get("pid"))
                loops.append({**rec, "registered": True})
            elif clean and not lock_held(LOOPS_DIR / f"{name[:-5]}.lock"):
                removed += clear_dead(path, rec)
        elif clean and (name.endswith(".lock") or name.endswith(".json.tmp")):
            pid = name.lstrip(".").split(".")[0]
            try:
                old = time.time() - path.stat().st_mtime > ORPHAN_S
            except OSError:
                continue
            if old and not (LOOPS_DIR / f"{pid}.json").exists() and not lock_held(LOOPS_DIR / f"{pid}.lock"):
                removed += clear_dead(path, None)
    loops += [p for p in loop_processes() if p["pid"] not in pids] if processes else []
    stamp = time.time()
    for rec in loops:
        last = rec.get("activity_at")
        transcript = rec.get("transcript") or (transcript_for("claude", rec.get("session"))
                                               if rec.get("host") == "claude" else None)
        if transcript:
            try:
                last = max(last or 0, os.path.getmtime(transcript))
            except OSError:
                pass
        rec["activity_at"] = last
    if repo:
        loops = [r for r in loops if r.get("repository") == repo]
    return sorted(loops, key=lambda r: (r.get("repository") or "~", r.get("module") or "", r["pid"])), removed


def iso(stamp: float | None) -> str | None:
    return datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if stamp else None


def loop_view(rec: dict) -> dict:
    """One loop as `loops --json` prints it."""
    stamp = time.time()
    started, last = rec.get("started_at"), rec.get("activity_at")
    out = {k: rec.get(k) for k in ("repository", "worktree", "module", "milestone", "role", "host", "model",
                                   "effort", "path", "pid")}
    out.update(started=iso(started), running_s=round(stamp - started) if started else None,
               turns=rec.get("turns"), last_activity=iso(last), idle_s=round(stamp - last) if last else None,
               tokens=rec.get("usage") or None, session=rec.get("session"), loop=rec.get("loop"),
               registered=rec.get("registered", False))
    # Tokens arrive when a turn ends, and most sessions are one long turn, so say one is under way and for how long.
    turn = rec.get("turn_started_at")
    out["turn_running_s"] = round(stamp - turn) if turn else None
    if rec.get("task"):
        out["task"] = rec["task"]
    return out


def ago(seconds: float | None) -> str:
    if seconds is None:
        return "?"
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m"
    if s < 86400:
        return f"{s // 3600}h {s % 3600 // 60}m"
    return f"{s // 86400}d {s % 86400 // 3600}h"


def tokens_text(usage: dict | None, hosts: list | None = None) -> str:
    """Tokens for a person. Only Claude reports a price, so any dollar figure says it covers the Claude turns alone,
    and names the hosts it leaves out."""
    def n(v):
        return f"{v / 1e6:.1f}M" if v >= 1e6 else f"{v / 1e3:.0f}k" if v >= 1e3 else str(v)
    if not usage:
        return "tokens not reported"
    text = f"tokens {n(usage.get('input', 0))} in, {n(usage.get('cached', 0))} cached, {n(usage.get('output', 0))} out"
    if not usage.get("cost_usd"):
        return text
    unpriced = [h for h in hosts or [] if h and h != "claude"]
    return text + (f" (${usage['cost_usd']:.2f} at list price, for the Claude turns only" +
                   (f"; {', '.join(unpriced)} report{'s' if len(unpriced) == 1 else ''} tokens, not a price"
                    if unpriced else "") + ")")


def loop_line(v: dict) -> str:
    """A loop in two lines, for a person: what it is, then how it's going."""
    what = (f"{v['module'] or '?'} {v['milestone'] or ''}".strip() if v["role"] != "plan" else
            "planner" + (f": {v['task']}" if v.get("task") else ""))
    run = " ".join(x for x in (v["host"], v["model"], v["effort"]) if x) or "host not known"
    head = f"  {what}  {v['role']}  {run}" + (f", {v['path']}" if v.get("path") else "") + f"  pid {v['pid']}"
    if not v["registered"]:
        seen = f", last activity {ago(v['idle_s'])} ago" if v["idle_s"] is not None else ""
        return head + (f"\n    started {ago(v['running_s'])} ago{seen}; it keeps no record (an older copy of the "
                       f"loop, or one that couldn't write it), so turns and tokens aren't known"
                       f"\n    worktree {v['worktree'] or '?'}\n    loop {v['loop']}")
    turns = f"{v['turns']} turn" + ("" if v["turns"] == 1 else "s") + " done"
    if v.get("turn_running_s") is not None:
        turns += f", turn {v['turns'] + 1} running for {ago(v['turn_running_s'])}"
    tokens = tokens_text(v["tokens"], [v["host"]]) + (" so far (a turn's tokens count when it ends)"
                                                       if v.get("turn_running_s") is not None and v["tokens"] else
                                                       " yet: they count when a turn ends"
                                                       if v.get("turn_running_s") is not None else "")
    return head + (f"\n    started {ago(v['running_s'])} ago, {turns}, last activity {ago(v['idle_s'])} ago, "
                   f"{tokens}\n    worktree {v['worktree']}")


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


def loop_write(worktree: Path, prof: dict, name: str, change, message: str,
               trailer: bool = True) -> tuple[bool, str]:
    """Applies `change(tree)` to a clean checkout of the integrated tip, commits it as the loop, and lands it.
    `change` returns the paths it wrote, or nothing to skip the commit. Without `trailer` the commit isn't marked as
    the loop's own record-keeping (used for files the loop lands on someone's behalf)."""
    detail = ""
    for _ in range(2):
        try:
            tree = verify_tree(worktree, name, tip(worktree, prof))
        except TipError as e:
            return False, str(e)
        legacy = trailer and unrecorded(tree, prof, "HEAD")
        paths = change(tree)
        if not paths:
            return True, head_commit(tree)
        if legacy:
            paths = [*paths, *take_up(tree, prof)]
        git(tree, "add", "--", *paths)
        c = git(tree, *ident(tree), "commit", "--quiet", "-m", f"{message}\n\n{TRAILER}" if trailer else message)
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
                                if (tree / prof["plans"] / f"{stem}.md").exists() else None),
                 unrecorded(tree, prof, "HEAD"))


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


def turn_settings(rollout: Path) -> list[tuple[str, str, str]]:
    """(turn id, model, effort) for each turn a Codex rollout records."""
    return [(p.get("turn_id"), p.get("model"), p.get("effort"))
            for p in (e.get("payload", {}) for e in json_lines(rollout, '"turn_context"'))]


def pin_mismatches(rollout: Path, model_pin: str = DEFAULT_MODEL, effort_pin: str = DEFAULT_EFFORT) -> list[str]:
    # Codex's auto-review turns run in their own rollout files, so they don't show up here.
    return [f"{turn}: {model}/{effort}" for turn, model, effort in turn_settings(rollout)
            if (model, effort) != (model_pin, effort_pin)]


# The quota forecast. codex_quota reads the account's usage (burn per active hour, the tokens-to-percent fit, usage
# from elsewhere); the loop adds what only it knows: which threads are its own, what each milestone cost, and what the
# open milestones are likely to cost before the reset.

LOOP_PROMPT = re.compile(r"milestone (\S+) of module (\S+?)[ .,]")
LOOP_TITLE = re.compile(r"^(build|review) (\S+) (\S+)$")
QUOTA_BUDGET_S = 2.0          # reading budget on a result line; `quota` takes longer and warms the cache
QUOTA_WORKTREE: list = []     # the worktree a command runs on, for the result line's plan forecast


def note_thread(worktree: Path, host: str, session: str | None, role: str, title: str) -> None:
    """Appends a session the loop started to the repository's thread ledger, so the forecast can tell its own threads
    from the owner's. Never fails the caller."""
    if not session:
        return
    try:
        path = loop_dir(worktree) / "threads.jsonl"
        known = path.read_text() if path.exists() else ""
        if f'"{session}"' in known:
            return
        with open(path, "a") as handle:
            handle.write(json.dumps({"thread": session, "host": host, "role": role, "title": title,
                                     "at": now()}) + "\n")
    except Exception:
        pass


def loop_threads(worktree: Path, reading: dict) -> dict[str, dict]:
    """{thread: {module, milestone, role}} for every thread the loop ran, from its ledger and state files, and
    (for threads from before the ledger) the loop's own titles and objective wording. Auto-review and sub-agent
    threads count with the loop thread they served. `here` marks the threads this repository ran: those in its own
    ledger and state files, and those whose folder is one of its worktrees or under its git dir; the rest are
    loops in other repositories, which count toward the machine's loop use but never toward this one's milestones."""
    own: dict[str, dict] = {}
    roots: list[str] = []
    try:
        roots = [str(Path(git_common_dir(worktree)).resolve())]
        listed = git(worktree, "worktree", "list", "--porcelain").stdout
        roots += [str(Path(line[len("worktree "):]).resolve()) for line in listed.splitlines()
                  if line.startswith("worktree ")]
    except Exception:
        pass

    def here(cwd: str | None) -> bool:
        if not cwd:
            return False
        try:
            cwd = str(Path(cwd).resolve())
        except OSError:
            return False
        return any(cwd == r or cwd.startswith(r.rstrip("/") + "/") for r in roots)

    try:
        common = Path(git_common_dir(worktree))
        ledger = common / "orchestrate" / "threads.jsonl"
        for line in ledger.read_text().splitlines() if ledger.exists() else []:
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            m = LOOP_TITLE.match(d.get("title") or "")
            own[d["thread"]] = {"module": m and m.group(2), "milestone": m and m.group(3), "role": d.get("role"),
                                "here": True}
        for state_file in common.glob("**/orchestrate/*.json"):
            try:
                st = json.loads(state_file.read_text())
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(st, dict) and st.get("thread"):
                own.setdefault(st["thread"], {"module": st.get("module"), "milestone": st.get("milestone"),
                                              "role": "build", "here": True})
    except Exception:
        pass
    threads = reading["threads"]
    for tid, meta in threads.items():
        if tid in own:
            continue
        title = LOOP_TITLE.match(meta.get("name") or "")
        prompt = next((LOOP_PROMPT.search(p) for p in meta.get("prompts") or [] if LOOP_PROMPT.search(p)), None)
        mine = here(meta.get("cwd"))
        if title:
            own[tid] = {"module": title.group(2), "milestone": title.group(3), "role": title.group(1), "here": mine}
        elif prompt and meta.get("kind") in ("app", "exec"):
            own[tid] = {"module": prompt.group(2), "milestone": prompt.group(1), "role": "build", "here": mine}
        elif meta.get("origin") == "orchestrate" and meta.get("kind") in ("app", "exec"):
            own[tid] = {"module": None, "milestone": None, "role": None, "here": mine}
    spans: dict[str, list] = {}
    for t in reading["turns"]:
        if t["thread"] in own:
            spans.setdefault(t["thread"], []).append((t["start"], t["end"]))
    for tid, meta in threads.items():
        if tid in own:
            continue
        parent = meta.get("parent")
        if parent in own:
            own[tid] = dict(own[parent])
        elif meta.get("kind") == "guardian":
            first = min((t["start"] for t in reading["turns"] if t["thread"] == tid), default=None)
            for other, ivs in spans.items():
                if first is not None and threads.get(other, {}).get("cwd") == meta.get("cwd") and \
                        any(a - 60 <= first <= b + 60 for a, b in ivs):
                    own[tid] = dict(own[other])
                    break
    return own


def milestone_costs(worktree: Path, reading: dict, fit: dict, own: dict) -> tuple[list[dict], list[dict], dict]:
    """(history, open milestones, notes): what each milestone with local rollouts cost, and what is left to build,
    read from the done-when files at the last-fetched integrated tip (no fetch)."""
    prof = profile(worktree, missing_ok=True)
    ref = base_ref(prof) if git(worktree, "rev-parse", "--verify", "-q", base_ref(prof)).returncode == 0 else "HEAD"
    proj = project(worktree, prof, ref)
    tokens = codex_quota.tokens_by(reading, lambda r: r["thread"])
    turns: dict[str, int] = {}
    hours: dict[str, float] = {}
    for t in reading["turns"]:
        turns[t["thread"]] = turns.get(t["thread"], 0) + 1
        hours[t["thread"]] = hours.get(t["thread"], 0.0) + max(0.0, t["end"] - t["start"]) / 3600
    by_ms: dict[tuple, dict] = {}
    for tid, who in own.items():
        if not who.get("module") or not who.get("here") or tid not in tokens:  # another repository's loop
            continue
        key = (who["module"].upper(), who["milestone"])
        g = by_ms.setdefault(key, {"tokens": [0, 0, 0], "threads": 0, "turns": 0, "hours": 0.0})
        g["tokens"] = codex_quota.add(g["tokens"], tokens[tid])
        top = codex_quota.top_level(reading["threads"].get(tid) or {})
        g["threads"] += 1 if top else 0
        g["turns"] += turns.get(tid, 0) if top else 0
        g["hours"] += hours.get(tid, 0.0) if top else 0.0
    history, open_ms = [], []
    behind_parked = 0
    for key, e in sorted(proj.items()):
        doc = e["doc"]
        parked = False
        for m in doc.get("milestones") or [] if isinstance(doc, dict) else []:
            if not isinstance(m, dict) or "id" not in m:
                continue
            state = m.get("state")
            parked = parked or state == "parked"
            done = state == "done" or accepted(m, e["record"])
            g = by_ms.get((key, m["id"]))
            row = {"module": e["stem"], "milestone": m["id"], "state": state,
                   "rounds": (m.get("fails") or 0) + 1}
            if g:
                row.update(pct=codex_quota.cost(g["tokens"], fit), turns=g["turns"], builder_hours=round(g["hours"], 1))
                history.append(row)
            if not done and state != "parked":
                if parked:
                    behind_parked += 1  # milestones run in order, so these wait on the owner
                else:
                    open_ms.append(row)
    return history, open_ms, {"plans_at": ref, "behind_parked": behind_parked}


def pct(x: float) -> str:
    """A share of the weekly limit, with a decimal where whole percents would round a real cost to 0%."""
    if x <= 0:
        return "0%"
    if x < 0.1:
        return "under 0.1%"
    return f"{x:.1f}%" if x < 10 else f"{x:.0f}%"


def plural(n: int, word: str) -> str:
    return f"{n} {word}" + ("" if n == 1 else "s")


RECENT_H = 12.0  # other use is projected at its rate over this many hours, so last night's threads don't count twice


def plan_forecast(acc: dict, history: list[dict], open_ms: list[dict], recent: dict) -> dict:
    """The verdict: the expected cost of the open milestones, from what finished ones cost, plus other use (local
    threads not the loop's, and usage from elsewhere) at its rate over the last RECENT_H hours, against what's left
    before the reset. `recent` holds {"loop": [lo, mid, hi], "other": [lo, mid, hi], "hours": h} for that span."""
    left = max(0.0, 100.0 - acc["used_percent"])
    hours_left = acc["hours_left"]
    finished = [h for h in history if h["state"] == "done" and h.get("pct")]
    out = {"left_pct": left, "open_milestones": len(open_ms)}
    other_need = [round(x / recent["hours"] * hours_left, 1) for x in recent["other"]]
    out["other_use_before_reset"] = other_need
    if not open_ms:
        out["plan_pct"] = [0.0, 0.0, 0.0]
        need = other_need
    elif not finished:
        out["plan_pct"] = None
        out["verdict"] = (f"Too little data to cost the {plural(len(open_ms), 'open milestone')}: no finished "
                          f"milestone has local rollouts to learn from. {left:.0f}% is left until the reset in "
                          f"{hours_left:.0f} h.")
        out["warn"] = False
        return out
    else:
        mean = sum(h["pct"][1] for h in finished) / len(finished)
        lo, hi = min(h["pct"][0] for h in finished), max(h["pct"][2] for h in finished)
        if len(finished) == 1:
            lo, hi = lo / 2, hi * 2  # one milestone of history says little about the next
        rounds = sum(h["rounds"] for h in finished) / len(finished)
        spent = [h.get("pct") or [0, 0, 0] for h in open_ms]
        plan = [max(0.0, x * len(open_ms) - sum(s[i] for s in spent)) for i, x in enumerate((lo, mean, hi))]
        out.update(per_milestone=[round(lo, 2), round(mean, 2), round(hi, 2)], rounds_per_milestone=round(rounds, 1),
                   learned_from=len(finished), plan_pct=[round(x, 1) for x in plan])
        need = [plan[i] + other_need[i] for i in range(3)]
    out["need_pct"] = [round(x, 1) for x in need]
    what, need_ = (f"the {plural(len(open_ms), 'open milestone')} and other use", "need") if open_ms else \
        ("other use", "needs")
    if need[2] <= left:
        verdict = f"Quota lasts: {what} {need_} about {pct(need[1])} (at most {pct(need[2])}) before the reset in " \
                  f"{hours_left:.0f} h, and {left:.0f}% is left."
        warn = False
    elif need[0] > left:
        verdict = f"Quota runs short: {what} {need_} at least {pct(need[0])} before the reset in {hours_left:.0f} h, " \
                  f"and only {left:.0f}% is left."
        warn = True
    else:
        verdict = f"Quota may run short: {what} {need_} {pct(need[0])}-{pct(need[2])} before the reset in " \
                  f"{hours_left:.0f} h, and {left:.0f}% is left."
        warn = True
    # Pace: one builder working through the open milestones at the finished ones' cost per builder-hour.
    paced = [h for h in finished if h.get("builder_hours")]
    if open_ms and paced:
        per_hour = sum(h["pct"][1] for h in paced) / sum(h["builder_hours"] for h in paced)
        out["plan_hours_one_builder"] = round(len(open_ms) * sum(h["builder_hours"] for h in paced) / len(paced), 1)
        rate = per_hour + recent["other"][1] / recent["hours"]
        if warn and rate > 0 and left / rate < hours_left:
            out["runs_out"] = codex_quota.iso(time.time() + left / rate * 3600)
            verdict += f" One builder at the usual pace would use it up by {out['runs_out']}."
    out["verdict"], out["warn"] = verdict, warn
    return out


def quota_report(worktree: Path | None, budget_s: float = QUOTA_BUDGET_S, reading: dict | None = None) -> dict | None:
    """The full quota picture: the account (codex_quota), the loop's own and other use this window, what milestones
    cost, and the plan forecast."""
    reading = reading or codex_quota.read(budget_s=budget_s, home=CODEX_HOME)
    acc = codex_quota.account(reading)
    if not acc:
        return None
    fit = acc.pop("_fit")
    lo, now_s = acc["window_start"], reading["now"]
    own = loop_threads(worktree, reading) if worktree else {}
    by_thread = codex_quota.tokens_by(reading, lambda r: r["thread"], lo, now_s)
    mine = [t for t in by_thread if t in own]
    others = [t for t in by_thread if t not in own]
    own_pct = codex_quota.cost(codex_quota.add(*(by_thread[t] for t in mine)), fit) if mine else [0.0, 0.0, 0.0]
    local_pct = codex_quota.cost(codex_quota.add(*(by_thread[t] for t in others)), fit) if others else [0.0] * 3
    names = reading["threads"]
    top_other = sorted(others, key=lambda t: -codex_quota.weighted(*by_thread[t]))[:5]
    acc["use_this_window"] = {
        "covers": {"loop_pct": "Codex threads any orchestrate loop on this machine ran (this repository's, found by "
                               "its ledger, and other repositories', found by the loop's thread titles and prompts)",
                   "other_local_pct": "every other Codex thread on this machine (your own chats, other tools)",
                   "elsewhere_pct": "usage on this account that no local rollout explains (other machines, the "
                                    "web, cloud tasks)"},
        "loop_pct": own_pct, "other_local_pct": local_pct, "elsewhere_pct": acc["outside"]["pct"],
        "loops_apart": bool(worktree),
        "other_local_threads": [{"thread": t, "name": names.get(t, {}).get("name") or names.get(t, {}).get("cwd"),
                                 "pct": codex_quota.cost(by_thread[t], fit)} for t in top_other]}
    since = max(lo, now_s - RECENT_H * 3600)
    recent_h = max(1.0, (now_s - since) / 3600)
    recent_tokens = codex_quota.tokens_by(reading, lambda r: r["thread"] in own, since, now_s)
    elsewhere = sum(j["outside"] for j in fit.get("outside") or [] if j["t1"] >= since)
    recent = {"hours": recent_h,
              "loop": codex_quota.cost(recent_tokens.get(True, [0, 0, 0]), fit) or [0.0] * 3,
              "other": [x + elsewhere for x in codex_quota.cost(recent_tokens.get(False, [0, 0, 0]), fit) or [0.0] * 3]}
    acc["recent"] = {"hours": round(recent_h, 1), "loop_pct": recent["loop"], "other_pct": recent["other"],
                     "burn": codex_quota.burn(reading, fit, since, now_s, elsewhere)}
    history, open_ms, notes = [], [], {}
    if worktree:
        try:
            history, open_ms, notes = milestone_costs(worktree, reading, fit, own)
        except (SystemExit, Exception) as e:  # no profile, no plans: the account picture still stands
            notes = {"plan_unavailable": f"{type(e).__name__}: {e}"}
        acc["milestones"] = history
    else:
        notes = {"plan_unavailable": "no --worktree, so no plan to cost"}
    acc["forecast"] = {**plan_forecast(acc, history, open_ms, recent), **notes}
    return acc


def burn_line(acc: dict) -> str:
    """Recent burn in a phrase: measured from the usage figure when it moved enough, else fitted for the busiest
    model and effort."""
    hours = acc["recent"]["hours"]
    burn = acc["recent"]["burn"]
    if burn.get("per_active_hour"):
        lo, _, hi = burn["per_active_hour"]
        return f"{lo}-{hi}%/active h over the last {hours:.0f} h"
    groups = [(g["hours"], name, g["pct_per_hour"]) for name, g in burn.get("per_builder_hour", {}).items()
              if g.get("pct_per_hour")]
    if not groups:
        return f"too little use to measure over the last {hours:.0f} h"
    _, name, rate = max(groups)
    return f"about {rate[0]}-{rate[2]}%/builder-h on {name} over the last {hours:.0f} h (fitted; the figure moved " \
           "too little to measure directly)"


def quota_summary(acc: dict | None) -> dict | None:
    """The result line's few fields: used, reset, recent burn, a one-sentence verdict, and whether to warn."""
    if not acc:
        return None
    f = acc["forecast"]
    recent = acc["recent"]["burn"].get("per_active_hour")
    out = {"used_percent": acc["used_percent"], "resets_at": acc["resets_at"],
           "burn": burn_line(acc),
           "verdict": f.get("verdict"), "warn": bool(f.get("warn"))}
    if f.get("runs_out"):
        out["runs_out"] = f["runs_out"]
    if not acc.get("complete"):
        out["verdict"] = (f"No forecast yet: up to {acc['behind_mb']} MB of Codex rollouts are still unread "
                          "(each result line reads more; `quota` reads them all).")
        out["warn"] = False
        out["burn"] = "not measured yet"
        out.pop("runs_out", None)
    out["detail"] = "agent_loop.py quota --worktree <path>"
    return out


def quota_text(acc: dict | None) -> str:
    """`quota`'s readout for a person: the verdict first, then the few figures behind it, each saying whose use
    it counts. `--json` has everything."""
    if not acc:
        return "No Codex quota reading: no local Codex rollouts carry the weekly limit yet."
    s = quota_summary(acc)
    f, use = acc.get("forecast") or {}, acc.get("use_this_window") or {}
    mid = lambda r: r[1] if isinstance(r, list) and len(r) == 3 else r or 0
    lines = [s["verdict"] or "No verdict.",
             f"Codex weekly limit: {acc['used_percent']:.0f}% used, resets {acc['resets_at']} "
             f"(in {acc['hours_left']:.0f} h). Burn: {s['burn']}."]
    if use and not use.get("loops_apart", True):
        lines.append(f"Used this window: about {pct(mid(use.get('other_local_pct')))} by Codex threads on this machine "
                     f"(the loop's not told apart without --worktree), {pct(use.get('elsewhere_pct') or 0)} from "
                     "elsewhere (other machines, web, cloud).")
    elif use:
        lines.append(f"Used this window: about {pct(mid(use.get('loop_pct')))} by orchestrate loops on this machine "
                     f"(any repository), {pct(mid(use.get('other_local_pct')))} by your other Codex threads here, "
                     f"{pct(use.get('elsewhere_pct') or 0)} from elsewhere (other machines, web, cloud).")
    if f.get("per_milestone"):
        lo, m, hi = f["per_milestone"]
        lines.append(f"A milestone here has cost {pct(lo)}-{pct(hi)} (about {pct(m)}), learned from "
                     f"{plural(f.get('learned_from', 0), 'finished milestone')}; "
                     f"{plural(f.get('open_milestones', 0), 'milestone')} still open.")
    for row in (acc.get("milestones") or [])[-8:]:
        if row.get("pct"):
            lines.append(f"  {row['module']} {row['milestone']} ({row['state']}): {pct(row['pct'][0])}-"
                         f"{pct(row['pct'][2])}, {plural(row.get('turns', 0), 'turn')}, "
                         f"{row.get('builder_hours', 0)} builder-h" + ("" if row["state"] == "done" else
                                                                       " so far; a running turn counts when it ends"))
    if f.get("plan_unavailable"):
        lines.append(f"No plan to cost: {f['plan_unavailable']}.")
    lines.append("Everything, as JSON: add --json.")
    return "\n".join(lines)


def quota_now() -> dict | None:
    try:
        return quota_summary(quota_report(QUOTA_WORKTREE[0] if QUOTA_WORKTREE else None))
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
    doesn't mistake itself for a nested session. CLAUDE_CONFIG_DIR is kept, because it says which sign-in to use, and
    so is CLAUDE_CODE_OAUTH_TOKEN, the plan's own token from `claude setup-token`."""
    env = {k: v for k, v in os.environ.items()
           if not (k.startswith("ANTHROPIC_") or k.startswith("CLAUDE"))
           or k in ("CLAUDE_CONFIG_DIR", "CLAUDE_CODE_OAUTH_TOKEN")}
    return {**env, "ORCHESTRATE_ROLE": role}


def plugin_components(home: Path, kind: str) -> dict[str, str]:
    """{component name: plugin} for the `kind` ("skills" or "agents") of every plugin installed under `home`
    (CLAUDE_HOME or CODEX_HOME). Both hosts copy an installed plugin to plugins/cache/<marketplace>/<plugin>/<version>/;
    a copy of this repository holds every plugin's files, so only the components its marketplace entry lists count.
    Without an entry, the standard layout (skills/<name>/SKILL.md, agents/<name>.md) does. Claude also loads a plugin
    from a local-path marketplace in place, enabled in settings.json."""
    roots = [(Path(v), Path(v).parent.name) for v in glob.glob(str(home / "plugins/cache/*/*/*")) if Path(v).is_dir()]
    try:
        enabled = json.loads((home / "settings.json").read_text()).get("enabledPlugins") or {}
        known = json.loads((home / "plugins/known_marketplaces.json").read_text())
    except (OSError, ValueError, AttributeError):
        enabled, known = {}, {}
    for key, on in enabled.items():
        plugin, _, market = key.partition("@")
        where = (known.get(market) or {}).get("installLocation") if on and isinstance(known, dict) else None
        if where and Path(where).is_dir():
            roots.append((Path(where), plugin))
    found = {}
    for root, plugin in roots:
        try:
            entries = json.loads((root / ".claude-plugin/marketplace.json").read_text()).get("plugins") or []
            listed = next((e.get(kind) for e in entries if e.get("name") == plugin), None)
        except (OSError, ValueError, AttributeError):
            listed = None
        if isinstance(listed, str):
            listed = [listed]
        if listed:
            paths = [root / p for p in listed]
        else:
            paths = list((root / kind).glob("*")) if (root / kind).is_dir() else []
        for p in paths:
            if kind == "skills" and (p / "SKILL.md").exists():
                found.setdefault(p.name, plugin)
            elif kind == "agents" and p.suffix == ".md" and p.exists():
                found.setdefault(p.stem, plugin)
    return found


def agent_installed(name: str, worktree: Path) -> bool:
    return any(p.exists() for p in (CLAUDE_HOME / "agents" / f"{name}.md", worktree / ".claude/agents" / f"{name}.md")) \
        or name in plugin_components(CLAUDE_HOME, "agents")


def skill_note(name: str, host: str = "codex") -> str:
    """How the agent finds a skill: the file always, plus the name Codex knows it by (namespaced when a plugin
    installed it). Claude finds a plugin skill by its bare name when no other skill has it."""
    path = SKILLS / name / "SKILL.md"
    where = f"the file is {path}" if path.exists() else ""
    if host != "codex":
        return where or name
    plugin = plugin_components(CODEX_HOME, "skills").get(name)
    named = f"`{plugin}:{name}` in Codex" if plugin else f"${name} in Codex"
    return named + (f"; {where}" if where else "")


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
                 session: str | None, role: str = "build", new_id: str | None = None) -> tuple[list[str], dict | None]:
    """The command line and environment for one headless turn on `host`. `new_id` names a new Claude session."""
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
        elif new_id:
            args += ["--session-id", new_id]
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


TURN_USAGE: dict = {}  # the tokens the last turn's host reported; empty when it reported none


def usage_of(host: str, stdout: str) -> dict:
    """The tokens a headless turn's own output reported: `input` (not read from cache), `cached` (cache reads) and
    `output`, plus Claude's `cost_usd`, which is a list-price estimate and not what a plan is charged. Claude reports
    them in its `result` event and `codex exec` in `turn.completed`. A Claude turn stopped before its `result`
    (paused, timed out) still reported each finished message's tokens, so those are summed and the turn is counted
    under `incomplete_turns`, since the message it was writing is missing. A turn that ran in the Codex app, or on
    another host, reports nothing here, and the result stays empty: missing telemetry is never filled in."""
    out: dict = {}
    partial: dict = {}  # Claude's per-message usage, by message id, for a turn that never reached its result
    for line in stdout.splitlines() if host in ("codex", "claude") else []:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if host == "claude" and isinstance(event, dict) and event.get("type") == "assistant":
            message = event.get("message") or {}
            if isinstance(message.get("usage"), dict):
                partial[message.get("id") or len(partial)] = message["usage"]
        use = event.get("usage") if isinstance(event, dict) else None
        if not isinstance(use, dict):
            continue
        if host == "claude" and event.get("type") == "result":
            partial = {}
            turn = {"input": (use.get("input_tokens") or 0) + (use.get("cache_creation_input_tokens") or 0),
                    "cached": use.get("cache_read_input_tokens") or 0, "output": use.get("output_tokens") or 0}
            if isinstance(event.get("total_cost_usd"), (int, float)):
                turn["cost_usd"] = event["total_cost_usd"]
        elif host == "codex" and event.get("type") == "turn.completed":
            cached = use.get("cached_input_tokens") or 0
            turn = {"input": max((use.get("input_tokens") or 0) - cached, 0), "cached": cached,
                    "output": use.get("output_tokens") or 0}
        else:
            continue
        out = add_usage(out, turn)
    if partial and not out:
        out = add_usage({}, {"input": sum((u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
                                          for u in partial.values()),
                             "cached": sum(u.get("cache_read_input_tokens") or 0 for u in partial.values()),
                             "output": sum(u.get("output_tokens") or 0 for u in partial.values()),
                             "incomplete_turns": 1})
    return out


TOKEN_KEYS = ("input", "cached", "output")


def sub_usage(total: dict | None, before: dict | None) -> dict:
    """What `total` holds beyond `before` (both running totals of one session), never below zero."""
    out = {}
    for k, v in (total or {}).items():
        if isinstance(v, (int, float)):
            d = v - ((before or {}).get(k) or 0)
            if d > 0:
                out[k] = round(d, 6) if isinstance(d, float) else d
    return out


def claim_usage(state: dict) -> dict:
    """A claim record's tokens: `usage` is what the session spent since its previous claim (so a milestone's claims
    add up), and `session_usage` the session's running total so far."""
    if not state.get("usage"):
        return {}
    return {"usage": sub_usage(state["usage"], state.get("claimed_usage")), "session_usage": state["usage"]}


def add_usage(total: dict | None, turn: dict | None) -> dict:
    """`total` with `turn`'s tokens added, and one more turn counted when the turn reported any. A turn that
    reported none is counted only under `incomplete_turns`, so a total never looks more complete than it is."""
    total = dict(total or {})
    if not turn:
        return total
    for k, v in turn.items():
        if k != "turns" and isinstance(v, (int, float)):
            total[k] = round(total.get(k, 0) + v, 6) if isinstance(v, float) else total.get(k, 0) + v
    if any(k in turn for k in TOKEN_KEYS):
        total["turns"] = total.get("turns", 0) + (turn.get("turns") or 1)
    return total


def run_turn(host: str, prof: dict, model: str, effort: str, worktree: Path, prompt: str, session: str | None,
             timeout_s: float, role: str = "build", title: str = "") -> tuple[int, str | None, str, str, str | None]:
    """Runs one turn; returns (exit code, session id, last agent message, stderr tail, model the host reported).
    Codex and Claude turns run as sessions their desktop apps show when they can (see `visible_unavailable`), else
    headless; PATH records which, for the result line. 130 means stopped: by `pause`, or by the owner in the app.
    The process's record for `loops` notes the turn starting and ending, with its session and tokens."""
    if LIVE:
        same = bool(session) and session == LIVE.get("session")
        loop_note(host=host, model=model, effort=effort, session=session, activity_at=time.time(),
                  transcript=LIVE.get("transcript") if same else None, turn_started_at=time.time())
    out = _run_turn(host, prof, model, effort, worktree, prompt, session, timeout_s, role, title)
    HOSTS_USED.add(host)
    if host in ("codex", "claude") and not any(k in TURN_USAGE for k in TOKEN_KEYS):
        TURN_USAGE["incomplete_turns"] = 1  # it ran, but its host showed no tokens (the app, a stop, a failure)
    session_cost = None
    if host == "claude" and isinstance(TURN_USAGE.get("cost_usd"), (int, float)) and out[1]:
        # Claude's total_cost_usd covers the whole session, resumed turns included, while its token counts are this
        # invocation's own; so this turn's cost is the rise since the session's last total.
        session_cost = TURN_USAGE["cost_usd"]
        TURN_USAGE["cost_usd"] = round(max(0.0, session_cost - last_session_cost(worktree, out[1])), 6)
    note_usage(worktree, host, model, effort, out[1], out[0], session_cost)
    if LIVE:
        new = out[1]
        known = LIVE.get("transcript") if new and new == LIVE.get("session") else None
        loop_note(turns=LIVE.get("turns", 0) + 1, session=new, path=SESSION_PATH.get("path"), turn_started_at=None,
                  transcript=known or transcript_for(host, new), activity_at=time.time(),
                  usage=add_usage(LIVE.get("usage"), TURN_USAGE) if TURN_USAGE else LIVE.get("usage"))
    return out


def _run_turn(host: str, prof: dict, model: str, effort: str, worktree: Path, prompt: str, session: str | None,
              timeout_s: float, role: str, title: str) -> tuple[int, str | None, str, str, str | None]:
    SESSION_PATH.clear()
    TURN_USAGE.clear()
    why = visible_unavailable(host) if host in ("codex", "claude") else "not an app host"
    if host in ("codex", "claude"):
        SESSION_PATH.update(path="headless" if why else "visible", **({"path_reason": why} if why else {}))
        loop_note(path=SESSION_PATH["path"])
    if host == "codex" and not why:
        return codex_visible_turn(prof, model, effort, worktree, prompt, session, timeout_s, role, title)
    new_id = None
    if host == "claude" and not why:
        new_id = None if session else str(uuid.uuid4())
        sid = session or new_id
        if session and (pid := claude_app_process(session)):
            return 130, session, "", f"the owner has this session open in Claude desktop (pid {pid}); the loop " \
                                     "won't write to it at the same time", None
    args, env = host_command(host, prof, model, effort, worktree, prompt, session, role, new_id)
    tick = None
    if host == "claude" and not why:
        tick = lambda: claude_import(sid)  # noqa: E731
    code, stdout, stderr = run_proc(args, worktree, timeout_s, env=env, tick=tick)
    new_session, message, seen, error = parse_output(host, stdout)
    TURN_USAGE.update(usage_of(host, stdout))
    if tick:
        claude_import(sid, wait_s=CLAUDE_IMPORT_WAIT_S)
        if not claude_app_record(sid):
            SESSION_PATH.update(path="headless", path_reason="Claude desktop didn't list the session after the "
                                                             "import link")
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


WARNINGS: list = []  # the launch's preflight warnings, for the result line


EMIT_EXTRA: dict = {}  # fields every later result line of this process carries, e.g. the design review `run` ran
LAUNCH_HOSTS: set = set()  # hosts this process resolved a launch for


def new_command() -> None:
    """Forgets what an earlier command in this process left for result lines (one process can run several)."""
    EMIT_EXTRA.clear()
    LAUNCH_HOSTS.clear()
    HOSTS_USED.clear()
    RUN_HERE.clear()


def emit(result: str, **fields) -> None:
    """Prints the one-line result and exits. The Codex quota block goes only on results of a process that launched,
    or ran a turn, on Codex, since it says nothing about another host's limits."""
    extra = {"warnings": WARNINGS} if WARNINGS else {}
    if "next" in fields:
        fields["next"] = fit_next(fields["next"])
    more = {k: v for k, v in EMIT_EXTRA.items() if k not in fields}
    codex = "codex" in HOSTS_USED or "codex" in LAUNCH_HOSTS
    print(json.dumps({"result": result, **fields, **more, **SESSION_PATH, **extra,
                      **({"quota": quota_now()} if codex else {})}))
    sys.exit(0)


def finish(state_path: Path, state: dict, result: str, **extra) -> None:
    state.update(result=result, finished=time.time(), **extra)
    state_path.write_text(json.dumps(state, indent=2))
    noted = {k: state[k] for k in ("goal", "constraints_missing", "usage") if state.get(k)}
    emit(result, module=state["module"], milestone=state["milestone"], thread=state.get("thread"), **noted, **extra)


def resolve(a: argparse.Namespace, prof: dict, role: str) -> tuple[str, str, str]:
    """The host, model and effort for this launch: what the lead passed, else the profile, else the defaults. For
    the model, the profile's line for this kind of agent on this host (`Claude planner model`) comes before the
    host's own line (`Claude model`)."""
    host = (a.host or default_host(prof)).lower()
    model = (a.model or prof.get("role_models", {}).get(host, {}).get(ROLE_KINDS[role])
             or prof["models"].get(host) or "")
    if not model and host in prof.get("hosts", {}) and "{model}" in prof["hosts"][host]:
        raise SystemExit(f"error: host {host} needs --model, or a '- **{host} model:** <model>' line in the profile")
    effort = a.effort or ("high" if role == "plan" else prof["effort"])
    if effort not in EFFORTS:
        raise SystemExit(f"error: effort {effort!r} isn't one of {sorted(EFFORTS)}")
    LAUNCH_HOSTS.add(host)
    return host, model, effort


def review_host(prof: dict, builder: str, explicit: str | None = None) -> str:
    """The host a review runs on: the one named (`--host`, or `run --review-host`), else the profile's
    `Review host` (a host, or `other` for the built-in host the builder didn't use), else the builder's own host."""
    if explicit:
        return explicit.lower()
    wanted = prof.get("review_host") or ""
    if wanted == "other":
        return other_host(builder) if builder in ("codex", "claude") else builder
    return wanted if wanted and wanted != "same" else builder


def design_review_host(prof: dict, record: dict | None, fallback: str, explicit: str | None = None) -> str:
    """The host a design review runs on, for every command that names or runs one. With `Review host: other`, the
    built-in host that didn't write the plan, when a loop planner turn recorded its host (`planner` in the record);
    otherwise, and for every other `Review host`, exactly `review_host` against `fallback`. A named host wins."""
    if explicit:
        return explicit.lower()
    planner = ((record or {}).get("planner") or {}).get("host")
    if prof.get("review_host") == "other" and planner:
        return review_host(prof, planner)
    return review_host(prof, fallback)


def pin_check(host: str, session: str | None, seen: str | None, model: str, effort: str) -> tuple[list[str], dict]:
    """(turns that ran on another model or effort, what the loop verified the session ran on). The second holds a
    field only when the host's own output showed it: Codex's rollout shows model and effort, Claude's stream shows the
    model only, and other hosts show neither. Missing telemetry stays missing, never assumed."""
    if host == "codex" and session and (rollout := rollout_for(session)):
        bad, turns = pin_mismatches(rollout, model, effort), turn_settings(rollout)
        return bad, ({"model": model, "effort": effort} if turns and not bad else {})
    if host == "claude" and seen:
        return ([f"ran on {seen}, not {model}"], {}) if not seen.startswith(model) else ([], {"model": seen})
    return [], {}


def still_observed(before: dict | None, now_seen: dict) -> dict:
    """What every turn so far was verified on: a field drops out as soon as one turn couldn't show it."""
    return dict(now_seen) if before is None else {k: v for k, v in before.items() if now_seen.get(k) == v}


_VERSIONS: dict = {}


def cli_version(host: str, path: str | None = None) -> str | None:
    """What the binary that ran the turns says its version is (`--version`), or None where it can't be read. A
    visible Codex turn runs in the app, so its version is the app's bundled CLI."""
    exe = (CODEX_APP_CLI if path == "visible" else CODEX) if host == "codex" else CLAUDE if host == "claude" else None
    if not exe:
        return None
    if exe not in _VERSIONS:
        try:
            out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=20)
            _VERSIONS[exe] = (out.stdout.strip().splitlines() or [None])[0] if out.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            _VERSIONS[exe] = None
    return _VERSIONS[exe]


def launch_record(host: str, model: str, effort: str, path: str | None, observed: dict | None) -> dict:
    """Who ran a claim or review. `model` and `effort` are what the loop asked for; `observed` is only what it
    verified from the host's output; `cli` is the binary's own version string, or null when it couldn't be read."""
    rec = {"host": host, "model": model, "effort": effort, "observed": observed or {}, "cli": cli_version(host, path)}
    return {**rec, "path": path} if path else rec


ATTENDED_BLOCK = "attended items need a person or hardware:"


def answers_note(answers: list[dict], mid: str, record: str) -> str:
    """The owner's answers for a milestone, for the builder: their words as the loop recorded them, and where."""
    lines = [f"- {a.get('item') or mid} ({a.get('at')}): {a.get('text')}" for a in answers]
    return (f"The owner answered; the loop recorded it in {record} under milestones.{mid}.owner_answers, which is "
            "the evidence a reviewer checks. Use their words exactly as given, and cite that record rather than "
            "restating the answer as your own; where answers for one item differ, the latest stands:\n"
            + "\n".join(lines))


def owner_rules_line(rules: list[str]) -> str:
    return " ".join(f"Owner: {r.strip().rstrip('.')}." for r in rules)


def binding(prof: dict, role: str, mid: str = "", milestone: dict | None = None, done: str = "",
            review: str = "", rules: list[str] | None = None) -> tuple[str, list[str]]:
    """The terse restatement of what binds this role, for resumed turns, and the sources it couldn't find. Built only
    from the profile (as read at the start of the run, before the agent could edit it), the done-when file, the
    owner's rules stored with the run (`--owner-rule`) and the loop's own contracts. A builder's opens with its
    objective, which a compaction may have dropped. A reviewer gets its own boundaries, never the instruction to
    integrate."""
    missing = [label for label, value in prof.get("bounds", {}).items() if not value]
    if role == "review":
        own = f"{review}" + (f" and the verdict fields, state and fails in {done}" if done else "")
        text = f"Still binding: change only {own}; don't commit, push or launch agents."
    else:
        how = "push: it rebases and pushes, never force" if prof["integrate"] == "push" else \
            "local: it fast-forwards the local branch; don't push"
        text = (f"Objective: {mid} claimed, every item pass with evidence and the work integrated. "
                f"Still binding: change only {mid}'s state and its items' status and evidence in {done}. Integrate "
                f"only with `python3 {LOOP} land --worktree .` ({how}). Check: " +
                (f"`{prof['check']}`." if prof["check"] else "none."))
        attended = [i["id"] for i in (milestone or {}).get("items", []) if i.get("attended")]
        if attended:
            text += f" Attended items {', '.join(attended)}: do the rest, then BLOCKED naming them."
    for label, value in prof.get("bounds", {}).items():
        if value:
            text += f" {label}: {value.rstrip('.')}."
    if rules:
        text += " " + owner_rules_line(rules)
    return text, missing


def claude_version_tuple(text: str | None) -> tuple[int, ...] | None:
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    return tuple(int(x) for x in m.groups()) if m else None


CLAUDE_AGENTS_MD = (2, 1, 277)  # the first Claude Code that reads AGENTS.md itself (Claude Code memory docs, 9 Nov 2026)
AGENTS_HOME = Path.home() / ".agents"
ROLE_SKILLS = {"build": "build-milestone", "review": "review-milestone", "plan": "plan-module"}


def instruction_warnings(worktree: Path, exe_version: str | None) -> list[str]:
    """Whether a Claude session started in `worktree` reads the repository's AGENTS.md, as far as files and the CLI
    version can show. By default Claude reads AGENTS.md only when no CLAUDE.md, .claude/CLAUDE.md or CLAUDE.local.md
    sits in the folder or above it, and only from v2.1.277; an `@AGENTS.md` import in CLAUDE.md works on any."""
    if not (worktree / "AGENTS.md").exists():
        return []
    fix = "add a CLAUDE.md beside it whose first line is `@AGENTS.md`"
    imports = [p for p in (worktree / "CLAUDE.md", worktree / ".claude/CLAUDE.md") if p.exists() and (
        (p.is_symlink() and p.resolve() == (worktree / "AGENTS.md").resolve())
        or re.search(r"^@(\./|\.\./)?AGENTS\.md\b", p.read_text(errors="replace"), re.MULTILINE))]
    if imports:
        return []
    user = {Path.home() / ".claude/CLAUDE.md", CLAUDE_HOME / "CLAUDE.md"}  # the user's own file doesn't count
    counted = [p for d in (worktree, *worktree.parents)
               for p in (d / "CLAUDE.md", d / ".claude/CLAUDE.md", d / "CLAUDE.local.md") if p.exists()
               and p not in user]
    if counted:
        return [f"{counted[0]} stops Claude reading {worktree / 'AGENTS.md'} (unless Project instructions is "
                f"claude-md-and-agents-md); to share it, add `@AGENTS.md` to {worktree / 'CLAUDE.md'}"]
    version = claude_version_tuple(exe_version)
    if version is None:
        return [f"couldn't read the version of {CLAUDE}, so whether it reads AGENTS.md is unknown; to be sure, {fix}"]
    if version < CLAUDE_AGENTS_MD:
        return [f"{CLAUDE} is {'.'.join(map(str, version))}, which doesn't read AGENTS.md (needs 2.1.277), and this "
                f"repository has no CLAUDE.md, so Claude agents start without its rules; upgrade the CLI or {fix}"]
    return []


def skill_warnings(host: str, worktree: Path, role: str) -> list[str]:
    """Whether the role's skill is installed where `host` finds skills by name. The prompt names the skill's file
    either way, so a miss is a warning: the agent can still read it, but Claude agent files that list the skill
    need it by name."""
    name = ROLE_SKILLS.get(role)
    if not name or host not in ("codex", "claude"):
        return []
    dirs = (worktree, *worktree.parents)
    if host == "claude":
        places = [CLAUDE_HOME / "skills", *(d / ".claude/skills" for d in dirs)]
        found = any((p / name / "SKILL.md").exists() for p in places) or name in plugin_components(CLAUDE_HOME, "skills")
        where = f"{CLAUDE_HOME}/skills, .claude/skills or an installed plugin"
    else:
        places = [AGENTS_HOME / "skills", Path("/etc/codex/skills"), *(d / ".agents/skills" for d in dirs)]
        found = any((p / name / "SKILL.md").exists() for p in places) or name in plugin_components(CODEX_HOME, "skills")
        where = f"{AGENTS_HOME}/skills, .agents/skills or an installed plugin"
        if not found and (CODEX_HOME / "skills" / name / "SKILL.md").exists():
            where += f" (it's in {CODEX_HOME}/skills, which Codex's skills docs don't list)"
    if found:
        return []
    return [f"{name} isn't installed where {host} finds skills by name ({where}); the prompt gives its file path, "
            "so the agent can still read it"]


def preflight(host: str, worktree: Path, role: str) -> list[str]:
    """Launch-aware loader checks for the resolved host and its actual binary. Warnings only: each names its fix,
    and none stops the launch."""
    found = skill_warnings(host, worktree, role)
    if host == "claude":
        found = instruction_warnings(worktree, cli_version("claude")) + found
    if host == "codex" and role == "build":  # a reviewer that needs one asks for it, and has been granted it
        found += browser_warnings(worktree)
    for w in found:
        print("warning: " + w, file=sys.stderr)
    WARNINGS[:] = found
    return found


BROWSER = re.compile(r"\b(chrome|chromium|browsers?|playwright|puppeteer|webkit|firefox|safari|headless|webdriver|"
                     r"selenium|cdp)\b", re.IGNORECASE)


def browser_needs(worktree: Path, prof: dict) -> list[str]:
    """What plainly needs a browser: the profile's targets whose row names one, and the open milestones' items that
    use such a target or name a browser in their check, inspect or target. Read from this worktree's files."""
    text = file_here(worktree, PROFILE_FILE) or b""
    section = re.search(r"^##\s+Targets\s*$(.*?)(?=^##\s|\Z)", text.decode(errors="replace"), re.M | re.S)
    targets = []
    for row in (section.group(1) if section else "").splitlines():
        cells = [c.strip(" `<>") for c in row.strip().strip("|").split("|")]
        if len(cells) > 1 and cells[0] and not set(cells[0]) <= set("-: ") and cells[0].lower() != "target" \
                and BROWSER.search(row):
            targets.append(cells[0])
    found = [f"target {t}" for t in targets]
    folder = worktree / prof.get("plans", "docs/modules")
    for path in sorted(folder.glob("*-DONE.json")) if folder.is_dir() else []:
        try:
            doc = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for m in doc.get("milestones") or []:
            if not isinstance(m, dict) or m.get("state") == "done":
                continue
            for i in m.get("items") or []:
                if not isinstance(i, dict):
                    continue
                said = " ".join(str(i.get(k) or "") for k in ("check", "inspect", "target"))
                if i.get("target") in targets or BROWSER.search(said):
                    found.append(f"{doc.get('module') or path.stem} {i.get('id')}")
    return found


def browser_warnings(worktree: Path) -> list[str]:
    """A Codex agent in workspace-write can't start a browser (Chrome and Playwright's headless shell exit at once,
    with no output). It can run one outside the sandbox only by asking for escalation, which the loop's
    approvals_reviewer=auto_review grants or refuses per command: a reviewer that asked got Chromium that way, and a
    builder that never asked lost a session finding out. So warn, with the fixes, when the work plainly needs one."""
    try:
        prof = profile(worktree, missing_ok=True)
    except SystemExit:
        return []
    if prof.get("sandbox", "workspace-write") != "workspace-write":
        return []
    needs = browser_needs(worktree, prof)
    if not needs:
        return []
    shown = ", ".join(needs[:6]) + (f" and {len(needs) - 6} more" if len(needs) > 6 else "")
    return [f"{shown} need a browser, and a browser won't start inside Codex's workspace-write sandbox. The agent "
            "has to ask to run it outside the sandbox, and auto-review may refuse; Codex reviewers have asked and been "
            "granted one, and a builder that didn't ask lost its turn. If browser work has to be dependable on this "
            "build, the owner can set `Codex sandbox: danger-full-access` in ORCHESTRATE.md (that hands the agent "
            "this machine)"]


def floor_reason(host: str, code: int, err: str) -> str:
    if code == 127:
        return f"the {host} CLI couldn't start: {err.strip()[-200:]}"
    return f"two failed turns or no session on {host}; likely quota, sign-in or outage"


# ------------------------------------------------------------------------------------ sessions the apps show (macOS)
#
# On a Mac where the Codex app or Claude desktop is running, the loop's sessions are made so that the app lists them
# under the project, and the owner can watch, steer, pause and take over there. The loop still drives every turn and
# checks every claim itself. Elsewhere (another OS, no app, app not running, Claude CLI signed out, or
# ORCHESTRATE_HEADLESS=1) it runs `codex exec` and `claude -p` headless, as before. The methods were proven with the
# Codex app 26.1103 (CLI 0.167.0-alpha.3.2) and Claude desktop 4.23118.0; they rest on deep links, a local IPC
# socket and experimental app-server methods, so re-check them after an app update.
#
# Codex: a short-lived `codex app-server` creates the thread (source `vscode`, like the app's own) and runs one tiny
# bootstrap turn, so the rollout records the model, effort and sandbox the app then resumes with. Each loop turn
# queues the prompt (`codex queue`) and fires `codex://threads/wake/<id>`; the app's own app-server runs it. The
# loop waits on the thread's rollout file until the turn (and any goal turns the app chains after it) has ended.
# `codex://threads/<id>` makes the app window own the thread, so the IPC router can stop it on a pause or timeout.
#
# Claude: only the app can sign in a process it starts, so the loop keeps running its own signed-in `claude -p` per
# turn, under a session id it chooses, and imports the session into the app with `claude://resume?session=<id>`.
# The Code tab then lists it with its transcript. A session the owner has open in the app (a live app process on it)
# is never written to by the loop at the same time: the turn reports PAUSED instead.

SESSION_PATH: dict = {}  # which path the last turn ran on, for the result line
_IMPORTS_SENT: set = set()
CODEX_APP_CLI = "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"
CLAUDE_APP_STORE = Path.home() / "Library/Application Support/Claude/claude-code-sessions"
CLAUDE_HOME = Path(os.environ.get("CLAUDE_CONFIG_DIR") or Path.home() / ".claude")
SETTLE_S = 20.0  # quiet time after the last turn ends, so a goal's chained turn isn't mistaken for the end
START_S = 120.0  # how often a queued turn that hasn't started is woken again
STALL_START_S = 3 * 3600.0  # how long a turn may stay queued (the app asleep or busy) before it's given up on
POLL_S = 1.0
CLAUDE_IMPORT_WAIT_S = 15.0
BOOTSTRAP = ("The orchestrate loop started this thread from a script; its task arrives as the next message. "
             "Reply with exactly: ready")


def visible_unavailable(host: str) -> str | None:
    """Why `host` can't run a session its desktop app shows, or None when it can."""
    if os.environ.get("ORCHESTRATE_HEADLESS", "") not in ("", "0"):
        return "ORCHESTRATE_HEADLESS is set"
    if sys.platform != "darwin":
        return "the apps' session links are macOS-only"
    if host == "codex":
        if not Path(CODEX_APP_CLI).exists():
            return "the Codex app isn't installed"
        try:
            CodexIpc(timeout=5).close()
        except (OSError, RuntimeError, ValueError, KeyError) as e:
            return f"the Codex app isn't running (no IPC router: {type(e).__name__})"
        return None
    if not CLAUDE_APP_STORE.is_dir():
        return "Claude desktop isn't installed (no Code tab session store)"
    if not claude_app_running():
        return "Claude desktop isn't running"
    if not claude_signed_in():
        return ("the Claude CLI is signed out (`claude auth login`, or CLAUDE_CODE_OAUTH_TOKEN from "
                "`claude setup-token`)")
    return None


def open_link(url: str) -> bool:
    """Hands a deep link to the app that owns its scheme, in the background. Works with the screen locked."""
    try:
        return subprocess.run(["open", "-g", url], capture_output=True, timeout=30).returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def text_input(text: str) -> list[dict]:
    return [{"type": "text", "text": text, "text_elements": []}]


class CodexAppServer:
    """A short-lived JSON-RPC client for the app's bundled `codex app-server` over stdio. It exists only to create a
    thread record (and to change a goal's status); the app's own app-server runs every turn after the bootstrap."""

    def __init__(self):
        self.p = subprocess.Popen([CODEX_APP_CLI, "app-server", "--listen", "stdio://"], stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.q, self.n, self.notes = queue.Queue(), 0, []
        threading.Thread(target=self._read, daemon=True).start()
        self.call("initialize", {"clientInfo": {"name": "orchestrate", "title": "orchestrate", "version": "1"},
                                 "capabilities": {"experimentalApi": True}})
        self._send({"jsonrpc": "2.0", "method": "initialized", "params": {}})

    def _read(self):
        for line in self.p.stdout:
            try:
                self.q.put(json.loads(line))
            except ValueError:
                pass

    def _send(self, obj):
        self.p.stdin.write(json.dumps(obj) + "\n")
        self.p.stdin.flush()

    def _next(self, deadline):
        try:
            return self.q.get(timeout=max(0.05, min(1.0, deadline - time.time())))
        except queue.Empty:
            return None

    def _note(self, m):
        if "method" in m and "id" in m:  # a server request, such as an approval; the bootstrap needs none
            self._send({"jsonrpc": "2.0", "id": m["id"], "error": {"code": -32601, "message": "not handled"}})
        self.notes.append(m)

    def call(self, method, params, timeout=60):
        self.n += 1
        rid, deadline = self.n, time.time() + timeout
        self._send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params})
        while time.time() < deadline:
            m = self._next(deadline)
            if m is None:
                continue
            if m.get("id") == rid and "method" not in m:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m["result"]
            self._note(m)
        raise TimeoutError(method)

    def wait_for(self, method, timeout=180):
        deadline = time.time() + timeout
        if hit := next((m for m in self.notes if m.get("method") == method), None):
            return hit
        while time.time() < deadline:
            m = self._next(deadline)
            if m is not None:
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


class CodexIpc:
    """The Codex app's local IPC router, `<CODEX_HOME>/ipc/ipc.sock`: frames are a 4-byte little-endian length and
    JSON. The router forwards thread-follower requests to the app window that owns the thread."""
    VERSIONS = {"initialize": 0, "thread-follower-read-model-settings": 1, "thread-follower-interrupt-turn": 3}

    def __init__(self, timeout: float = 20):
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.settimeout(timeout)
        try:
            self.s.connect(str(CODEX_HOME / "ipc" / "ipc.sock"))
            self.buf, self.client_id = b"", None
            self.client_id = self.request("initialize", {"clientType": "orchestrate-loop"})["clientId"]
        except BaseException:
            self.s.close()
            raise

    def _send(self, obj):
        data = json.dumps(obj).encode()
        self.s.sendall(struct.pack("<I", len(data)) + data)

    def _recv(self):
        while True:
            if len(self.buf) >= 4:
                (n,) = struct.unpack("<I", self.buf[:4])
                if len(self.buf) >= 4 + n:
                    msg, self.buf = self.buf[4:4 + n], self.buf[4 + n:]
                    return json.loads(msg)
            chunk = self.s.recv(65536)
            if not chunk:
                raise ConnectionError("the IPC socket closed")
            self.buf += chunk

    def request(self, method, params, timeout_ms=20000):
        rid = str(uuid.uuid4())
        self._send({"type": "request", "requestId": rid, "sourceClientId": self.client_id,
                    "version": self.VERSIONS.get(method, 0), "method": method, "params": params,
                    "timeoutMs": timeout_ms})
        while True:
            m = self._recv()
            if m.get("type") == "response" and m.get("requestId") == rid:
                if m.get("resultType") == "error":
                    raise RuntimeError(f"{method}: {m.get('error')}")
                return m.get("result")
            if m.get("type") == "client-discovery-request":
                self._send({"type": "client-discovery-response", "requestId": m.get("requestId"),
                            "response": {"canHandle": False}})

    def close(self):
        self.s.close()


def codex_project_for(projects: list[dict], paths: list[str]) -> str | None:
    """The id of the Codex project whose root is, or holds, the first of `paths` that one does: the worktree, then
    the repository it belongs to. The deepest root wins, so a project for a subfolder beats one for its parent."""
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


def codex_thread_create(prof: dict, model: str, effort: str, worktree: Path, role: str, title: str) -> str:
    """Creates a thread recorded with the model, effort and permissions the headless path would use, named `title`,
    and placed in the Codex project that holds the repository, if there is one. Returns its id.

    The project goes on the app server's record (experimental `projectId`). As of the 9 Nov 2026 desktop app, the
    sidebar groups threads by its own assignments, which only the app writes, so these threads still list under
    Recents there; they move under the project if the app starts reading the server's record."""
    sandbox = prof.get("sandbox", "workspace-write")
    if sandbox == "danger-full-access":
        policy = {"type": "dangerFullAccess"}
    else:
        roots = [git_common_dir(worktree)] + [str(Path(r).expanduser()) for r in prof.get("roots") or []]
        policy = {"type": "workspaceWrite", "networkAccess": True, "writableRoots": roots}
    # The app's own app-server runs this thread's turns, in the app's environment, which has no ORCHESTRATE_ROLE;
    # Codex's shell environment policy sets it for the agent's commands, as the headless path's environment does.
    config = {"model_reasoning_effort": effort, "shell_environment_policy.set.ORCHESTRATE_ROLE": role}
    if role in ("review", "plan"):
        config["features.multi_agent"] = False
    approvals = {"approvalPolicy": "on-request", "approvalsReviewer": "auto_review"}
    srv = CodexAppServer()
    try:
        start = {"cwd": str(worktree), "model": model, "threadSource": "user", "sandbox": sandbox, "config": config,
                 **approvals}
        try:
            projects = srv.call("project/list", {}).get("data") or []
            repo = str(Path(git_common_dir(worktree)).parent)
            if project := codex_project_for(projects, [str(worktree.resolve()), repo]):
                start["projectId"] = project
        except (RuntimeError, OSError, KeyError, AttributeError) as e:  # placement is a convenience; never block a launch
            print(f"warning: couldn't find the Codex project for {worktree}: {e}", file=sys.stderr)
        thread = srv.call("thread/start", start)["thread"]["id"]
        srv.call("turn/start", {"threadId": thread, "model": model, "effort": effort, "sandboxPolicy": policy,
                                "input": text_input(BOOTSTRAP), **approvals})
        done = srv.wait_for("turn/completed", timeout=180)
        status = done["params"]["turn"].get("status")
        if status != "completed":
            raise RuntimeError(f"the bootstrap turn ended {status}")
        srv.call("thread/name/set", {"threadId": thread, "name": (title or "orchestrate")[:80]})
    finally:
        srv.close()
    return thread


def codex_owner(thread: str) -> dict | None:
    """The model settings the app window holding `thread` reports, or None if no window holds it."""
    try:
        ipc = CodexIpc()
        try:
            return (ipc.request("thread-follower-read-model-settings", {"conversationId": thread}) or {}).get(
                "settings") or {}
        finally:
            ipc.close()
    except (OSError, RuntimeError, ValueError):
        return None


def codex_interrupt(thread: str) -> bool:
    """The app's Stop button: interrupts the running turn and pauses the thread's goal."""
    try:
        ipc = CodexIpc()
        try:
            ipc.request("thread-follower-interrupt-turn", {"conversationId": thread, "mode": "user-stop"})
            return True
        finally:
            ipc.close()
    except (OSError, RuntimeError, ValueError):
        return False


def codex_goal_activate(thread: str) -> bool:
    """The app's play button, minus the wake: a status-only goal change, which writes only the goal store (with an
    `origin` it would also write the rollout, which the app holds), picked up when the thread is next woken."""
    try:
        srv = CodexAppServer()
        try:
            srv.call("thread/goal/set", {"threadId": thread, "status": "active"})
            return True
        finally:
            srv.close()
    except (OSError, RuntimeError, TimeoutError, ValueError):
        return False


def codex_queue(thread: str, text: str) -> None:
    out = subprocess.run([CODEX_APP_CLI, "queue", "--thread", thread, "--resume", "--message", text],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0 or "Queued" not in out.stdout + out.stderr:
        raise RuntimeError(f"codex queue failed: {(out.stdout + out.stderr).strip()[-300:]}")


def codex_unqueue(thread: str) -> bool:
    """Removes the thread's queued messages, so a turn the loop gave up on can't start later unwatched."""
    try:
        ipc = CodexIpc()
        try:
            ipc.request("thread-follower-clear-queued-messages", {"conversationId": thread})
            return True
        finally:
            ipc.close()
    except (OSError, RuntimeError, ValueError):
        return False


def codex_queued(thread: str) -> int:
    db = CODEX_HOME / "queue_1.sqlite"
    if not db.exists():
        return 0
    try:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
            return conn.execute("select count(*) from queued_items where thread_id=?", (thread,)).fetchone()[0]
    except sqlite3.Error:
        return 0


def new_events(path: Path | None, offset: int) -> tuple[list[dict], int]:
    """Complete JSON lines appended to `path` since `offset`, and the offset after them."""
    if path is None:
        return [], offset
    try:
        with open(path, "rb") as handle:
            handle.seek(offset)
            data = handle.read()
    except OSError:
        return [], offset
    end = data.rfind(b"\n") + 1
    events = []
    for line in data[:end].splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            continue
    return events, offset + end


def codex_visible_turn(prof: dict, model: str, effort: str, worktree: Path, prompt: str, thread: str | None,
                       timeout_s: float, role: str, title: str) -> tuple[int, str | None, str, str, str | None]:
    """One loop turn on a thread the Codex app runs and shows. The same contract as a headless turn: (exit code,
    thread id, last agent message, error text, None); the pin check reads the same rollout file."""
    try:
        if thread is None:
            thread = codex_thread_create(prof, model, effort, worktree, role, title)
        settings = codex_owner(thread)
        if settings is None:  # the window must hold the thread for a pause or timeout to stop it
            open_link(f"codex://threads/{thread}")
            for _ in range(30):
                if (settings := codex_owner(thread)) is not None:
                    break
                time.sleep(POLL_S)
        if settings:
            SESSION_PATH["app_settings"] = f"{settings.get('model')} {settings.get('reasoningEffort')}"
        else:
            SESSION_PATH["path_note"] = "no app window holds the thread, so a pause or timeout can't stop its turn"
        rollout = rollout_for(thread)
        offset = rollout.stat().st_size if rollout else 0
        loop_note(session=thread, transcript=str(rollout) if rollout else LIVE.get("transcript"))
        codex_queue(thread, prompt)
        if not open_link(f"codex://threads/wake/{thread}"):
            raise RuntimeError("couldn't open the wake link")
    except (OSError, RuntimeError, TimeoutError, ValueError, KeyError, subprocess.SubprocessError) as e:
        return 1, thread, "", f"the Codex app path failed: {type(e).__name__}: {e}", None

    began = time.time()
    deadline, running, started, quiet, woken = began + timeout_s, set(), False, began, 0
    message, error, aborted = "", "", False
    while True:
        rollout = rollout or rollout_for(thread)
        events, offset = new_events(rollout, offset)
        for event in events:
            p = event.get("payload") or {}
            kind = p.get("type")
            if event.get("type") == "response_item" and kind == "message" and p.get("role") == "assistant":
                text = [c.get("text", "") for c in p.get("content") or [] if isinstance(c, dict)]
                message = "\n".join(t for t in text if t) or message
            if event.get("type") != "event_msg":
                continue
            if kind == "task_started":
                running.add(p.get("turn_id"))
                started, aborted, quiet = True, False, time.time()
            elif kind in ("task_complete", "turn_complete", "turn_aborted"):
                running.discard(p.get("turn_id"))
                aborted, quiet = kind == "turn_aborted", time.time()
                message = p.get("last_agent_message") or message
            elif kind == "error":
                error = str(p.get("message") or p)[:500]
        if _STOP:
            codex_interrupt(thread)
            return 130, thread, message, "(stopped)", None
        if time.time() > deadline:
            if not started:
                codex_unqueue(thread)
            goal = goal_status(thread)
            codex_interrupt(thread)
            if goal == "active":  # Stop pauses the goal; a timeout isn't the owner pausing it
                codex_goal_activate(thread)
            return 124, thread, message, "(timed out)", None
        if not started:
            # The app can hold a queued turn a long time (sleep, a busy window), so keep waking it while the message
            # waits; give up early only when the message has gone without a turn starting, or the app is gone.
            waited = time.time() - began
            gone = waited > 2 * START_S and (not codex_queued(thread) or visible_unavailable("codex"))
            if gone or waited > 2 * START_S + STALL_START_S:
                codex_unqueue(thread)
                return 1, thread, "", ("the Codex app didn't start the queued turn (signed out, or not running?); "
                                       "its queued message was removed"), None
            if waited > START_S * (woken + 1):
                woken += 1 if open_link(f"codex://threads/wake/{thread}") else 0
        elif not running and time.time() - quiet >= SETTLE_S and not codex_queued(thread):
            if aborted:
                return 130, thread, message, "the turn was stopped in the Codex app", None
            return (1 if error and not message else 0), thread, message, error, None
        time.sleep(POLL_S)


def claude_app_running() -> bool:
    try:  # `pgrep -x Claude` misses the app on macOS 26, so read the executables' paths
        out = subprocess.run(["ps", "-axo", "comm="], capture_output=True, text=True, timeout=30).stdout
    except (OSError, subprocess.TimeoutExpired):
        return False
    return any(line.strip().endswith("Claude.app/Contents/MacOS/Claude") for line in out.splitlines())


def claude_signed_in() -> bool:
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return True
    try:
        out = subprocess.run([CLAUDE, "auth", "status"], capture_output=True, text=True, timeout=30,
                             env=clean_env())
        return bool(json.loads(out.stdout).get("loggedIn"))
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False


def claude_app_record(session: str) -> Path | None:
    """The Code tab's record of `session`, which is what makes the app list it."""
    hits = glob.glob(str(CLAUDE_APP_STORE / "*" / "*" / f"local_{session}.json"))
    return Path(hits[0]) if hits else None


def claude_transcript(session: str) -> Path | None:
    hits = glob.glob(str(CLAUDE_HOME / "projects" / "*" / f"{session}.jsonl"))
    return Path(hits[0]) if hits else None


def claude_import(session: str, wait_s: float = 0.0) -> None:
    """Imports a CLI session into the Code tab once its transcript exists (`claude://resume` writes the app's
    record). Called while the turn runs, so the owner can watch the first turn too."""
    if claude_app_record(session) or not claude_transcript(session):
        return
    if session not in _IMPORTS_SENT:
        _IMPORTS_SENT.add(session)
        open_link(f"claude://resume?session={session}")
    deadline = time.time() + wait_s
    while time.time() < deadline and not claude_app_record(session):
        time.sleep(POLL_S)


def claude_app_process(session: str) -> int | None:
    """The pid of a live Claude desktop process on `session`, if the owner has it open in the app."""
    for f in glob.glob(str(CLAUDE_HOME / "sessions" / "*.json")):
        try:
            reg = json.loads(Path(f).read_text())
            if reg.get("sessionId") != session or not (reg.get("hostSessionId") or
                                                       reg.get("entrypoint") == "claude-desktop"):
                continue
            pid = int(reg.get("pid") or Path(f).stem)
            os.kill(pid, 0)
            return pid
        except (OSError, ValueError, TypeError):
            continue
    return None


# ------------------------------------------------------------------------------------------------------- building

RUN_RESULTS = {"review_owed": "REVIEW_OWED", "replan_owed": "REPLAN_OWED", "waiting": "WAITING",
               "design_owed": "DESIGN_OWED", "blocked": "BLOCKED", "parked": "PARKED", "finished": "FINISHED", "taken": "TAKEN",
               "invalid": "INVALID"}


STALL_TURNS = 3  # turns in a row with no change and no report: the first, then two continuations naming open items


def work_marks(worktree: Path, milestone: dict | None) -> str:
    """A fingerprint of the builder's uncommitted work and its milestone's builder fields, so a turn that changed
    neither is told apart from one that did work without committing it."""
    tree = git(worktree, "status", "--porcelain").stdout + git(worktree, "diff", "HEAD").stdout
    fields = json.dumps([(milestone or {}).get("state")] + [(i.get("id"), i.get("status"), i.get("evidence"))
                                                          for i in (milestone or {}).get("items", [])])
    return hashlib.sha256((tree + fields).encode()).hexdigest()


def open_items(milestone: dict | None) -> str:
    ids = [i["id"] for i in (milestone or {}).get("items", []) if i.get("status") != "pass"]
    return f" Still open: {', '.join(ids)}." if ids else ""


def run_again(a: argparse.Namespace, stem: str, worktree: Path, host: str | None = None) -> str:
    """This `run` command as the lead typed it, optionally on another host, for a result's `next`."""
    args = ["run", "--module", stem, "--worktree", str(worktree)]
    for flag, value in (("--host", host or a.host), ("--model", None if host else a.model),
                        ("--effort", None if host else a.effort)):
        if value:
            args += [flag, value]
    return loop_cmd(*args)


def other_host(host: str) -> str:
    return "claude" if host == "codex" else "codex"


def cmd_run(a: argparse.Namespace) -> None:
    new_command()
    worktree = Path(a.worktree).resolve()
    if not_yet := unplanned(worktree):
        emit("INVALID", module=a.module, problems=[not_yet["reason"]], next=not_yet["next"])
    prof = profile(worktree, strict=True)
    host, model, effort = resolve(a, prof, "build")
    preflight(host, worktree, "build")
    stem = module_stem(worktree, prof, a.module)
    key = stem.upper()
    again = run_again(a, stem, worktree)
    if not run_lock(worktree, key):
        who = run_holder_info(worktree, key)
        emit("TAKEN", module=stem, by="another run on this repository" + holder_text(who),
             **({"holder": who} if who else {}), next=next_cmd(
                 again, "lead", f"another `run` on this repository holds {stem}{holder_text(who)}; run it again once "
                                "that one stops (`loops` shows whether it's still working)"))
    install_stop()
    loop_register(worktree, "build", module=stem, host=host, model=model, effort=effort)
    git_dir = git(worktree, "rev-parse", "--absolute-git-dir").stdout.strip()
    state_dir = Path(git_dir) / "orchestrate"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{stem}.json"

    sync_worktree(worktree, prof)

    def unlanded(then: dict | None) -> dict:
        """`next` for a run that stops short, or `adopt` when plan files haven't landed (only looked for here, since
        plans are read at the tip and a run that builds needn't pay for the look)."""
        return drift_fields(plan_drift(worktree, prof, start_tip), worktree, then)

    # An owed design review runs here first, as `review --milestone design` would, unless the lead opted out; a
    # DESIGN OK carries on to build in the same run.
    for attempt in range(2):
        try:
            start_tip = tip(worktree, prof)
        except TipError as e:
            emit("FLOOR", module=stem, reason=str(e), next=getattr(e, "next", None) or next_cmd(
                again, "lead", "the integrated tip can't be fetched; fix the network or remote, then run it again"))
        proj = project(worktree, prof, start_tip)
        for k, cycle in need_cycles(proj).items():
            proj[k]["problems"].append(f"its needs form a cycle: {cycle}")
        sync_claims(worktree, prof)
        if key not in proj:
            emit("INVALID", module=stem, problems=[f"{stem} has no done-when file at the integrated tip "
                                                   f"({base_ref(prof)}), so there's nothing to build yet"],
                 **unlanded(next_cmd(
                     loop_cmd("plan", "--worktree", str(worktree), "--task", f"Plan module {stem}"), "lead",
                     f"{stem} isn't planned at the integrated tip")))
        step = next_step(key, proj, claims(worktree), me(worktree))
        if step["status"] != "design_owed" or getattr(a, "no_design_review", False) or attempt:
            break
        reviewer = design_review_host(prof, proj[key]["record"], host, getattr(a, "review_host", None))
        review = review_once(argparse.Namespace(module=stem, milestone="design", commit=None, worktree=str(worktree),
                                                host=reviewer, model=a.model if reviewer == host else None,
                                                effort=a.effort, turn_timeout_hours=a.turn_timeout_hours), locked=True)
        # the build row starts its own count; the design review's turns and tokens are under `design_review`
        loop_note(role="build", milestone=None, turns=0, usage={}, turn_started_at=None)
        if review.get("counted") is False:  # it judged a plan that changed while it ran
            emit("DESIGN_OWED", module=stem, design_review=review, **unlanded(review.get("next")))
        if review.get("verdict") != "DESIGN OK":
            emit("DESIGN_OWED", module=stem, design_review=review,
                 **unlanded(design_review_next(review, stem, worktree, prof)))
        # Every later result of this run says the review ran, with its verdict and tokens, so cost adds up.
        EMIT_EXTRA["design_review"] = {k: review.get(k) for k in ("result", "verdict", "host", "model", "effort",
                                                                  "review", "review_commit", "session", "usage")
                                       if review.get(k) is not None}
        sync_worktree(worktree, prof)
    if a.milestone and step.get("milestone") != a.milestone:
        emit("WAITING", module=stem, milestone=a.milestone,
             reason=f"{a.milestone} isn't the module's next milestone; that is {step.get('milestone')} "
                    f"({step['status']}), and milestones in a module run in order",
             next=next_for(step, worktree, prof, proj))
    if step["status"] != "ready":
        emit(RUN_RESULTS[step["status"]], **step, **unlanded(next_for(step, worktree, prof, proj)))
    mid = step["milestone"]
    loop_note(milestone=mid)
    ok, holder = take_claim(worktree, prof, key, mid)
    if not ok:
        emit("TAKEN", module=stem, milestone=mid, by=holder,
             next=next_for({**step, "status": "taken", "by": holder}, worktree, prof, proj))

    done = load_done(worktree, stem, prof)
    if problems := validate(done, key):
        emit("INVALID", module=stem, problems=problems[:20], **unlanded(next_cmd(
            loop_cmd("plan", "--worktree", str(worktree), "--task", plan_task(stem, problems[:5])), "lead",
            f"this worktree's copy of {stem}'s done-when file is invalid")))
    milestone = find(done, mid)
    authorised_hash = proj[key]["record"]["milestones"][mid]["definitions"]
    if definitions(milestone) != authorised_hash:
        emit("INVALID", module=stem, milestone=mid, problems=[
            f"this worktree's copy of {mid}'s definitions isn't the authorised one at the integrated tip; "
            f"rebase the worktree onto {base_ref(prof)} and run again"], **unlanded(next_cmd(
                shlex.join(["git", "-C", str(worktree), "rebase", base_ref(prof)]), "lead",
                f"this worktree is behind or apart from {base_ref(prof)}; rebase it, then: {again}")))
    baseline = copy.deepcopy(done)

    pin = [host, model, effort]
    # a build turn is about to start: only now is this the module's run, for `next` commands printed later
    # with `Review host: other` only a review host the lead named is kept: otherwise each review decides its own,
    # against the builder for a milestone and the planner for a design
    note_run(worktree, stem, host, getattr(a, "review_host", None) if prof.get("review_host") == "other" else
             review_host(prof, host, getattr(a, "review_host", None)))
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    fresh = (a.fresh or state.get("milestone") != mid or state.get("result") == "PIN" or state.get("pin") != pin)
    # The owner's rules outlive fresh sessions and milestones, until the owner has them cleared.
    rules = [] if getattr(a, "clear_owner_rules", False) else list(state.get("owner_rules") or [])
    rules += [r.strip() for r in getattr(a, "owner_rule", None) or [] if r.strip() and r.strip() not in rules]
    if fresh:
        state = {"module": stem, "milestone": mid, "thread": None, "turns": 0, "pin": pin}
    state["owner_rules"] = rules
    # Every run starts its own counters, so a resume after BUDGET or a failed review isn't judged on old progress.
    _, reflog = own_progress(worktree, 10 ** 9, prof["plans"])
    state.update(failed_turns=0, reports=0, unclaimed=0, idle=0, progress_at=time.time(), passing=passing(milestone),
                 reflog=reflog, host=host, model=model, effort=effort, start_tip=start_tip,
                 marks=work_marks(worktree, milestone))
    state.pop("result", None)
    restate, missing = binding(prof, "build", mid, milestone, done_rel(prof, stem), rules=rules)
    state["constraints_missing"] = missing
    if missing:
        print("warning: ORCHESTRATE.md has no filled-in " + " or ".join(f"`{m}`" for m in missing) +
              " line, so resumed turns can't restate it", file=sys.stderr)
    timeout_s = a.turn_timeout_hours * 3600
    resumable = host in ("codex", "claude")

    # `run` again carries on, as the app's play button would: after a pause, and after a block the lead has cleared
    # (the milestone is runnable again, so a goal left `blocked` would only end every resumed turn as BLOCKED).
    if host == "codex" and state.get("thread") and goal_status(state["thread"]) in ("paused", "blocked") \
            and not visible_unavailable("codex"):
        codex_goal_activate(state["thread"])

    def floor_next() -> dict:
        return next_cmd(again, "lead", f"the {host} host failed or ran out (quota, sign-in or outage); run it again "
                                       "once it's back, or on the other host", alternative=run_again(
                                           a, stem, worktree, other_host(host)))

    def planner_next(problems: list[str]) -> dict:
        return next_cmd(loop_cmd("plan", "--worktree", str(worktree), "--task", plan_task(stem, problems[:5])),
                        "lead", "send the problems to the planner, and don't resume this builder until a planner "
                                "turn has fixed them")

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
            finish(state_path, state, "FLOOR", reason=f"goal {status}", next=floor_next())
        if status == "paused" or _STOP:
            finish(state_path, state, "PAUSED")
        first = state.get("thread") is None or not resumable
        if first:
            prompt = BUILD_TEMPLATE.format(goal=GOAL_LINE if host == "codex" else "",
                                           milestone=mid, module=stem, done=done_rel(prof, stem), loop=LOOP,
                                           skill=skill_note("build-milestone", host))
            if state["turns"] and not resumable:
                prompt += "\n\nThis continues earlier work on the same milestone; the files show where it got to."
            if a.message:
                prompt += "\n\n" + a.message
                a.message = None
            if state["turns"] and not resumable:
                prompt += "\n\n" + restate
            elif rules:
                prompt += "\n\n" + owner_rules_line(rules)
        else:
            prompt = a.message or "Continue the objective." + open_items(find(load_done(worktree, stem, prof), mid))
            a.message = None
            # A resumed turn may follow a compaction that dropped the first prompt. An active Codex goal already
            # re-sends its objective each turn, so only a thread without one gets the restatement; the owner's rules
            # may postdate the goal, so they go every time.
            if status != "active":
                prompt += "\n\n" + restate
            elif rules:
                prompt += "\n\n" + owner_rules_line(rules)
        answers = (proj[key]["record"]["milestones"].get(mid) or {}).get("owner_answers") or []
        told = text_hash(json.dumps(answers, sort_keys=True))
        if answers and (first or told != state.get("answers_told")):  # new, or another answer came in
            prompt += "\n\n" + answers_note(answers, mid, record_rel(prof, stem))
            state["answers_told"] = told
        code, session, message, err, seen = run_turn(host, prof, model, effort, worktree, prompt,
                                                     None if first else state["thread"], timeout_s,
                                                     title=f"build {stem} {mid}")
        if resumable:
            state["thread"] = session
            note_thread(worktree, host, session, "build", f"build {stem} {mid}")
        state["turns"] += 1
        state["failed_turns"] = state["failed_turns"] + 1 if code not in (0, 130) else 0
        state["path"] = SESSION_PATH.get("path")
        if TURN_USAGE:
            state["usage"] = add_usage(state.get("usage"), TURN_USAGE)
        state_path.write_text(json.dumps(state, indent=2))

        if _STOP or code == 130:
            finish(state_path, state, "PAUSED", **({} if _STOP else {"reason": err.strip()}))
        if code == 127 or (resumable and state["thread"] is None) or state["failed_turns"] >= 2:
            finish(state_path, state, "FLOOR", reason=floor_reason(host, code, err), exit_code=code, stderr=err,
                   next=floor_next())
        bad, seen_now = pin_check(host, state.get("thread"), seen, model, effort)
        state["observed"] = still_observed(state.get("observed"), seen_now)
        if bad:
            finish(state_path, state, "PIN", mismatches=bad[:5])
        status = goal_status(state["thread"]) if host == "codex" else None
        if host == "codex":
            state["goal"] = status or "none"  # whether the builder created its goal; without one, turns restate
        if status in ("usage_limited", "budget_limited"):
            finish(state_path, state, "FLOOR", reason=f"goal {status}", next=floor_next())
        if status == "paused":
            finish(state_path, state, "PAUSED")

        done = load_done(worktree, stem, prof)
        if problems := validate(done, key):
            finish(state_path, state, "INVALID", problems=problems[:20], next=planner_next(problems))
        try:
            upstream = loop_versions(worktree, done_rel(prof, stem), start_tip, tip(worktree, prof))
        except TipError:
            upstream = []
        if problems := delta_problems(baseline, done, "build", mid, upstream):
            finish(state_path, state, "INVALID", problems=problems[:20] + [
                "only the builder's own fields may change during a run; if a planner changed the file, start the "
                "builder again"], next=planner_next(problems))
        current = find(done, mid)
        moved, state["reflog"] = own_progress(worktree, state["reflog"], prof["plans"])
        now_passing = passing(current)
        if now_passing > state["passing"] or moved:
            state["progress_at"] = time.time()
        marks = work_marks(worktree, current)
        changed_anything = moved or marks != state.get("marks")
        state.update(passing=now_passing, head=head_commit(worktree), marks=marks)

        word = report_word(message)
        if now_passing == len(current["items"]):
            reasons, checked = claim_problems(worktree, prof, stem, current, done, authorised_hash, start_tip)
            if not reasons:
                head, review = head_commit(worktree), needs_review(current, done)

                def change(tree):
                    doc = json.loads((tree / done_rel(prof, stem)).read_text())
                    rec = record_in(tree, prof, stem, doc)
                    e = entry(rec, mid)
                    e["claim"] = {"commit": head, "checked": checked, "at": now(),
                                  **launch_record(host, model, effort, state.get("path"), state.get("observed")),
                                  **claim_usage(state)}
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
                    finish(state_path, state, "FLOOR", reason=f"the loop couldn't record the claim: {detail}",
                           next=next_cmd(again, "lead", "the claim held but couldn't be recorded; run it again, "
                                                        "and the loop re-checks and records it"))
                if not review:
                    drop_claim(worktree, prof, key, mid)
                if state.get("usage"):
                    state["claimed_usage"] = dict(state["usage"])  # the next claim on this session counts from here
                reviewer = review_host(prof, host, getattr(a, "review_host", None))
                then = (next_cmd(loop_cmd("review", "--module", stem, "--milestone", mid, "--commit", head,
                                          "--worktree", str(worktree), "--host", reviewer), "lead",
                                 f"{stem} {mid} is claimed at {head[:12]} and waits for its review"
                                 + (f", on {reviewer}, the review host" if reviewer != host else ""))
                        if review else
                        next_cmd(loop_cmd("run", "--module", stem, "--worktree", str(worktree)), "lead",
                                 f"{stem} {mid} was accepted on its checks alone (no item needs a reviewer); run "
                                 "builds the module's next milestone"))
                finish(state_path, state, "CLAIMED", review=review, commit=head, checked=checked, next=then)
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
                        reason = f"{ATTENDED_BLOCK} {', '.join(attended)}. {reason}"
                    record_block(reason)
                    finish(state_path, state, word, report=tail(message, 1500), next=next_for(
                        {"module": stem, "milestone": mid, "status": "blocked", "blocked": reason,
                         "attended": attended}, worktree, prof))
                finish(state_path, state, word, report=tail(message, 1500))
        else:
            state["reports"] = 0
        # A turn that changed nothing and reported nothing is a progress update, not work. After STALL_TURNS of
        # them in a row (each answered with the open items), the loop stops rather than nudging forever.
        state["idle"] = 0 if (changed_anything or word) else state.get("idle", 0) + 1
        if state["idle"] >= STALL_TURNS:
            finish(state_path, state, "STALLED", turns=state["idle"], open=[
                i["id"] for i in current["items"] if i.get("status") != "pass"], report=tail(message, 1500))
        if status == "blocked":
            record_block(report_line(message) or "the Codex goal is blocked")
            finish(state_path, state, "BLOCKED", report=tail(message, 1500), next=next_for(
                {"module": stem, "milestone": mid, "status": "blocked",
                 "blocked": report_line(message) or "the Codex goal is blocked",
                 "attended": open_attended(current)}, worktree, prof))
        if time.time() - state["progress_at"] > a.budget_hours * 3600:
            finish(state_path, state, "BUDGET", hours=a.budget_hours)


# ------------------------------------------------------------------------------------------ reviewing and planning

FINISH = "Finish the task and end with the last line it asks for."


def tail(text: str, limit: int) -> str:
    """The end of an agent's final message, where planners put the owner's decisions; when cut, cut at a line or
    sentence start (else a word) and marked."""
    if len(text) <= limit:
        return text
    cut = text[-limit:]
    m = re.search(r"\n|(?<=[.!?])\s", cut[:limit // 2]) or re.search(r"\s", cut)
    return "[earlier text cut] " + cut[m.end() if m else 0:].lstrip()


def one_session(host: str, prof: dict, model: str, effort: str, worktree: Path, prompt: str, role: str,
                missing, timeout_s: float, max_turns: int = 3, title: str = "", restate: str = "") -> dict:
    """Runs a reviewer or planner until `missing(message)` returns None, nudging it at most twice with what
    `missing` says is still owed. Its first turn is always a new session, so it inherits nothing from the builder or
    the lead. Host failures come back as FLOOR, PIN or PAUSED with their reasons, so the lead can fall back to
    another host."""
    session, message, turns, observed, owed, usage = None, "", 0, None, FINISH, {}
    while turns < max_turns:
        resume = session if (turns and host in ("codex", "claude")) else None
        text = prompt if not turns else owed + (f"\n\n{restate}" if restate else "")
        if turns and not resume:  # a host with no sessions gets the whole task again
            text = prompt + "\n\n" + text
        code, session, message, err, seen = run_turn(host, prof, model, effort, worktree, text, resume, timeout_s,
                                                     role, title)
        note_thread(worktree, host, session, role, title)
        turns += 1
        usage = add_usage(usage, TURN_USAGE)
        spent = {"usage": usage} if usage else {}  # a stop's tokens count too
        if _STOP or code == 130:
            return {"result": "PAUSED", "session": session, **spent, **({} if _STOP else {"reason": err.strip()})}
        bad, seen_now = pin_check(host, session, seen, model, effort)
        observed = still_observed(observed, seen_now)
        if bad:
            return {"result": "PIN", "mismatches": bad[:5], "session": session, **spent}
        if code != 0:
            return {"result": "FLOOR", "reason": floor_reason(host, code, err) if code == 127 else
                    f"the {role} turn on {host} failed (exit {code}); likely quota, sign-in or outage",
                    "exit_code": code, "stderr": err, "session": session, **spent}
        owed = missing(message)
        if owed is None:
            break
    last = next((l.strip() for l in reversed(message.splitlines()) if l.strip()), "")
    return {"result": "FINISHED" if owed is None else "UNFINISHED", "last_line": last, "owed": owed,
            "report": tail(message, 6000 if role == "plan" else 1500), "session": session, "turns": turns, "observed": observed or {},
            **({"usage": usage} if usage else {})}


REVIEW_LINE = re.compile(r"^(PASS|FAIL)\s+([A-Za-z0-9_.-]+)\b|^(DESIGN OK|DESIGN CHANGES)\b")


def review_once(a: argparse.Namespace, locked: bool = False) -> dict:
    """Runs one review, milestone or design, and returns its result instead of printing it. `locked` means the
    caller (a `run` doing an owed design review) already holds the module's run lock."""
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    if not a.host and prof.get("review_host"):  # the profile's Review host, against whoever made what's judged
        builder, rec = default_host(prof), {}
        try:
            rec = json.loads(show(worktree, base_ref(prof), record_rel(prof, module_stem(worktree, prof, a.module)))
                             or "{}")
        except (json.JSONDecodeError, SystemExit):
            pass
        if a.milestone == "design":  # whoever wrote the plan, when the loop knows
            reviewer = design_review_host(prof, rec, builder)
        else:  # whoever built it
            claim = ((rec.get("milestones") or {}).get(a.milestone) or {}).get("claim") or {}
            reviewer = review_host(prof, claim.get("host") or builder)
        a = argparse.Namespace(**{**vars(a), "host": reviewer})
    host, model, effort = resolve(a, prof, "review")
    before = list(WARNINGS)
    preflight(host, worktree, "review")
    if locked:  # keep the build's loader warnings beside the review's
        WARNINGS[:] = list(dict.fromkeys(before + WARNINGS))
    stem = module_stem(worktree, prof, a.module)
    key, mid, design = stem.upper(), a.milestone, a.milestone == "design"
    info = dict(host=host, model=model, effort=effort, module=stem, milestone=mid)
    if not locked and not run_lock(worktree, key):
        who = run_holder_info(worktree, key)
        return _result("TAKEN", **info, by="another run on this repository" + holder_text(who),
                       **({"holder": who} if who else {}))
    install_stop()
    if locked:  # a design review inside `run`: the same process, doing a review for now
        loop_note(role="review", milestone=mid, host=host, model=model, effort=effort)
    else:
        loop_register(worktree, "review", module=stem, milestone=mid, host=host, model=model, effort=effort)
    try:
        ref = tip(worktree, prof)
    except TipError as e:
        return _result("FLOOR", **info, reason=str(e), **({"next": e.next} if getattr(e, "next", None) else {}))
    proj = project(worktree, prof, ref)
    if key not in proj or proj[key]["problems"]:
        return _result("INVALID", **info, problems=(proj.get(key) or {}).get("problems") or ["not planned at the tip"])
    done_path = done_rel(prof, stem)
    review_path = f"{prof['evidence']}/{stem}/" + ("design-review.md" if design else f"{mid}-review.md")
    rec = proj[key]["record"]
    if design:
        start, before_doc = ref, proj[key]["doc"]
    else:
        r = git(worktree, "rev-parse", "--verify", "--quiet", f"{a.commit}^{{commit}}")
        if r.returncode != 0:
            return _result("INVALID", **info, problems=[f"commit {a.commit} doesn't exist here"])
        start = r.stdout.strip()
        if not is_ancestor(worktree, start, ref):
            return _result("INVALID", **info, problems=[f"{start[:12]} isn't on {base_ref(prof)}, so it isn't integrated"])
        try:
            before_doc = json.loads(show(worktree, start, done_path) or "")
            claimed = find(before_doc, mid)
        except (json.JSONDecodeError, SystemExit):
            return _result("INVALID", **info, problems=[f"{mid} can't be read from {done_path} at {start[:12]}"])
        at_tip = next((m for m in proj[key]["doc"]["milestones"] if m["id"] == mid), {})
        if claimed.get("state") != "claimed" or at_tip.get("state") != "claimed":
            return _result("INVALID", **info, problems=[f"{mid} is {claimed.get('state')} at {start[:12]} and "
                                              f"{at_tip.get('state')} at the tip; only a claimed milestone is reviewed"])
        if definitions(claimed) != (rec["milestones"].get(mid) or {}).get("definitions"):
            return _result("INVALID", **info, problems=[f"{mid}'s definitions at {start[:12]} aren't the authorised ones"])
    try:
        tree = verify_tree(worktree, stem, start)
    except TipError as e:
        return _result("FLOOR", **info, reason=str(e))
    before_review = (tree / review_path).read_text() if (tree / review_path).exists() else None
    template = DESIGN_REVIEW_TEMPLATE if design else REVIEW_TEMPLATE
    captures = review_path[:-len(".md")]
    answers = (rec["milestones"].get(mid) or {}).get("owner_answers") if not design else None
    changed = design_changes(worktree, rec, done_path, proj[key]["doc"]) if design else ""
    briefs = (f"The tasks planners were given for this module, whole and verbatim, are in {record_rel(prof, stem)} "
              "under `briefs`, oldest first; they include the loop's own re-plan and retry tasks, so read them for the "
              "request they carry and judge the design against that. "
              if design and rec.get("briefs") else "")
    prompt = template.format(milestone=mid, module=stem, commit=start, done=done_path, captures=captures, changed=changed,
                             briefs=briefs,
                             review=review_path, skill=skill_note("review-milestone", host),
                             answers=(f"The owner's answers for {mid} are in {record_rel(prof, stem)} under "
                                      f"milestones.{mid}.owner_answers (for " + ", ".join(
                                          dict.fromkeys(x.get('item') or mid for x in answers)) +
                                      "). Check any claim about what the owner chose against them. ")
                             if answers else "")
    wanted = ("DESIGN OK", "DESIGN CHANGES") if design else ("PASS", "FAIL")
    try:  # the tip as the turn starts, to check what reaches it while the reviewer works
        launch_tip = tip(worktree, prof)
    except TipError as e:
        return _result("FLOOR", **info, reason=str(e))
    seen = reflog_size(tree)
    out = one_session(host, prof, model, effort, tree, prompt, "review",
                      lambda msg: None if report_line(msg).startswith(wanted) else FINISH,
                      a.turn_timeout_hours * 3600,
                      title=f"review {stem} {mid}",
                      restate=binding(prof, "review", done="" if design else done_path,
                                      review=f"{review_path} (and files under {captures}/)")[0])
    result = out.pop("result")
    launch = launch_record(host, model, effort, SESSION_PATH.get("path"), out.pop("observed", None))
    if out.get("usage"):
        launch["usage"] = out["usage"]
    if result != "FINISHED":
        return _result(result, **info, **out)

    # Check what the reviewer did before anything lands.
    try:
        forged = record_tampering(worktree, prof, launch_tip, tip(worktree, prof))
    except TipError as e:
        return _result("FLOOR", **info, reason=f"the turn can't be checked, so nothing landed: {e}")
    if forged:
        return _result("INVALID", **info, landed=False, problems=[
            f"while this review ran, {plural(len(forged), 'commit')} without the loop's trailer changed an acceptance "
            f"record on the tip: {', '.join(forged)}"], session=out.get("session"), next=next_cmd(
            None, "owner", "report it: those commits reached the integrated tip during a review, and only the loop "
            "writes acceptance records. The owner decides what to do with them; nothing from this review landed"))
    if made := commits_made(tree, seen):
        return _result("INVALID", **info, landed=False, problems=[
            f"the reviewer committed in its checkout ({plural(len(made), 'commit')} in its reflog during the turn: "
            f"{'; '.join(made[:5])}); a reviewer leaves its verdict uncommitted and the loop lands it"],
            session=out.get("session"), next=next_cmd(
                None, "lead", "nothing from this review landed; any commit that reached the integrated tip is "
                "already there, so look at it, then review again"))
    allowed = {review_path} | (set() if design else {done_path})
    changed = changed_paths(tree, start)
    evidence = [p for p in changed if p.startswith(captures + "/")]
    problems = [f"changed {p}, which a reviewer doesn't own" for p in changed if p not in allowed and p not in evidence]
    problems += [f"{p} isn't a plain file; captures must be files" for p in evidence
                 if (tree / p).is_symlink() or ((tree / p).exists() and not (tree / p).is_file())]
    # read now: landing reuses this checkout, so the files must be in hand before it's reset to the tip
    captured = {p: (tree / p).read_bytes() if (tree / p).is_file() and not (tree / p).is_symlink() else None
                for p in evidence}
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
        return _result("INVALID", **info, landed=False, problems=problems[:20], last_line=out["last_line"],
             session=out.get("session"))

    passed = verdict in ("PASS", "DESIGN OK")

    stale: dict = {}

    def change(t):
        write = [review_path]
        (t / review_path).parent.mkdir(parents=True, exist_ok=True)
        earlier, kept = t / review_path, None
        if earlier.exists() and earlier.read_text() != review_text:
            # keep the earlier round beside the new one, named as `owner rereview` names its copies
            kept, moved_files = keep_round(t, earlier)
            write += [p for p in moved_files if p not in write]
        (t / review_path).write_text(review_text)
        for p, data in captured.items():  # captures the reviewer saved beside the review
            if data is not None:
                (t / p).parent.mkdir(parents=True, exist_ok=True)
                (t / p).write_bytes(data)
                write.append(p)
            elif (t / p).exists():
                (t / p).unlink()
                write.append(p)
        doc = json.loads((t / done_path).read_text())
        record = record_in(t, prof, stem, doc)
        if design:
            prev = record.get("design")
            for e_ in ([prev] if prev else []) + list(record.get("design_history") or []):
                if kept and e_.get("review") == review_path:
                    e_["review"] = kept  # the earlier review's file moved beside the new one
            design_rel = f"{prof['plans']}/{stem}.md"
            read = show(worktree, start, design_rel)  # what the reviewer read, not what the tip holds now
            here = (t / design_rel).read_text() if (t / design_rel).exists() else None
            moved = changed_items(before_doc, doc) + (["the design document"] if read != here else [])
            entry_ = {"verdict": "ok" if passed else "changes", "review": review_path, "commit": start,
                      "hash": text_hash(read), "by": "review", **launch, "at": now()}
            if moved:  # it judged a plan that has since changed: it lands, listed, but doesn't count
                stale["moved"] = moved
                record.setdefault("design_history", []).append({**entry_, "not_counted": "the plan changed while "
                                                                f"it ran: {', '.join(moved)}"})
                write_json(t / record_rel(prof, stem), record)
                return write + [record_rel(prof, stem)]
            if prev:  # every design verdict stays listed, so `design_passed` and `report` see them all
                record.setdefault("design_history", []).append(prev)
            record["design"] = entry_
            if passed:  # the reviewer judged these definitions, so a plan revised before review needs no re-plan
                for m in doc["milestones"]:
                    e = record["milestones"].get(m["id"])
                    if e and e.get("definitions") != definitions(m) and not e.get("reviews") \
                            and not e.get("accepted"):
                        e["definitions"] = definitions(m)
                        e["authorised"] = {"by": "design review", "review": review_path, "commit": start,
                                           "at": now()}
        else:
            reviewed, target = find(after, mid), find(doc, mid)
            target.update(state=reviewed["state"], fails=reviewed.get("fails", 0))
            by_id = {i["id"]: i for i in reviewed["items"]}
            for i in target["items"]:
                i["verdict"], i["review"] = by_id[i["id"]].get("verdict", ""), by_id[i["id"]].get("review", "")
            if not passed:
                reset_proof(target, only_failed=True)
                if escalation(target.get("fails", 0), target.get("replans", 0)) == "park":
                    target["state"] = "parked"  # the ladder has run out; only the owner unparks it
            write_json(t / done_path, doc)
            write.append(done_path)
            e = entry(record, mid)
            if kept:  # the earlier round's file moved; its record entry follows it
                rounds = [r for r in e.get("reviews") or [] if r.get("review") == review_path]
                if rounds:
                    rounds[-1]["review"] = kept
                for r in rounds[:-1]:  # overwritten before rounds were kept: only git history has them
                    r["review_in_history"] = r.pop("review")
            e.setdefault("reviews", []).append({"verdict": "pass" if passed else "fail", "commit": start,
                                                "review": review_path, **launch, "at": now()})
            if passed:
                e["accepted"] = {"by": "review", "commit": start, "review": review_path,
                                 "checked": (e.get("claim") or {}).get("checked"), "at": now()}
        write_json(t / record_rel(prof, stem), record)
        return write + [record_rel(prof, stem)]

    ok, landed = loop_write(worktree, prof, key, change, f"orchestrate: review of {stem} {mid}: {verdict}")
    if not ok:
        return _result("INVALID", **info, landed=False,
                       problems=[f"the review was valid but couldn't be integrated: {landed}"])
    if passed and not design:
        drop_claim(worktree, prof, key, mid)
    fails = find(after, mid).get("fails", 0) if after else None
    # On a FAIL, `next` is the command the escalation ladder calls for, with its word under `ladder`.
    ladder = None
    if design and stale:
        why = (f"the plan changed while this design review ran ({', '.join(stale['moved'])}), so its verdict doesn't "
               "count for the plan at the tip: the review is kept and listed, and the design review is still owed")
        return _result("REVIEWED", **info, verdict=verdict, counted=False, not_counted=why, commit=start,
                       review=review_path, review_commit=landed, last_line=out["last_line"],
                       session=out.get("session"), **({"usage": out["usage"]} if out.get("usage") else {}),
                       next=next_cmd(loop_cmd("review", "--module", stem, "--milestone", "design", "--worktree",
                                              str(worktree), "--host", host), "lead", why))
    if not passed and not design:
        ladder = escalation(fails, find(after, mid).get("replans", 0))
        action = ladder_next(ladder, stem, mid, fails, worktree, prof)
    elif not passed:
        action = design_review_next({"verdict": verdict, "review": review_path}, stem, worktree, prof)
    else:
        action = after_pass(worktree, prof, key)
    return _result("REVIEWED", **info, verdict=verdict, commit=start, review=review_path, review_commit=landed,
                   fails=fails, **({"ladder": ladder} if ladder else {}), next=action, last_line=out["last_line"],
                   session=out.get("session"),
                   **({"usage": out["usage"]} if out.get("usage") else {}))


def _result(result: str, **fields) -> dict:
    return {"result": result, **fields}


def after_pass(worktree: Path, prof: dict, key: str) -> dict:
    """`next` after a passing review: the module's next milestone, or that it's finished."""
    try:
        ref = tip(worktree, prof, fetch=False)
        proj = project(worktree, prof, ref)
        step = next_step(key, proj, claims(worktree), me(worktree))
    except (TipError, SystemExit, KeyError) as e:
        return next_cmd(loop_cmd("ready", "--worktree", str(worktree)), "lead", f"see what's ready ({e})")
    if step["status"] == "finished":
        return next_cmd(None, "lead", f"{step['module']} is finished: every milestone is accepted. Start other ready "
                                      f"work (`{loop_cmd('ready', '--worktree', str(worktree))}`)")
    return next_for(step, worktree, prof, proj) or next_cmd(loop_cmd("ready", "--worktree", str(worktree)), "lead",
                                                            f"{step['module']} is {step['status']}; see what's ready")


def design_review_next(out: dict, stem: str, worktree: Path, prof: dict) -> dict:
    """What follows a design review that didn't say DESIGN OK."""
    wt = str(worktree)
    if out.get("verdict") == "DESIGN CHANGES":
        return next_cmd(loop_cmd("plan", "--worktree", wt, "--task",
                                 f"Revise {stem}'s design and plan as {out.get('review')} asks"), "planner",
                        "the design review found blocking changes; send them to the planner, then review the design "
                        "again. Report the module only if a blocking finding returns after the planner fixed it, or "
                        "needs an owner decision", findings=out.get("review"))
    host = out.get("host") or default_host(prof)
    return next_cmd(loop_cmd("review", "--module", stem, "--milestone", "design", "--worktree", wt, "--host",
                             other_host(host)), "lead",
                    f"the design review ended {out.get('result')} without a verdict; run it again, on the other host "
                    "if it was the host that failed")


def cmd_review(a: argparse.Namespace) -> None:
    new_command()
    out = review_once(a)
    result = out.pop("result")
    if result in ("FLOOR", "INVALID", "PIN") and "next" not in out:
        again = ["review", "--module", out.get("module") or a.module, "--milestone", a.milestone]
        again += [] if a.milestone == "design" else ["--commit", a.commit]
        again += ["--worktree", str(Path(a.worktree).resolve()), "--host", other_host(out.get("host") or "codex")]
        out["next"] = next_cmd(loop_cmd(*again), "lead", "nothing landed; run the review again, on the other host "
                                                         "if you can")
    emit(result, **out)


def plan_owed(worktree: Path, start: str, message: str) -> str | None:
    """None when the planner's turn ended with a result: BLOCKED or NEEDS_CONTEXT, or `PLANNED: <files>` naming
    files it changed that exist, with a design beside every done-when file it changed. Otherwise what's missing,
    for the nudge. A progress report isn't a result."""
    line = report_line(message)
    word, _, rest = line.partition(":")
    if report_word(message) in ("BLOCKED", "NEEDS_CONTEXT"):
        return None
    if word.strip("`* ") != "PLANNED":
        return "Your last line wasn't `PLANNED: <files>`. Finish the plan's files, then end with that line, or with " \
               "BLOCKED or NEEDS_CONTEXT."
    plans = profile(worktree, missing_ok=True)["plans"]
    named = [n.strip("`*'\" ") for n in re.split(r"[,\s]+", rest) if n.strip("`*'\" ")]
    changed = changed_paths(worktree, start)
    gaps = [f"{n} doesn't exist" for n in named if not (worktree / n).exists()]
    gaps += [f"{n} isn't changed" for n in named if (worktree / n).exists() and n not in changed]
    gaps += [f"{p} has no design at {plans}/{Path(p).name[:-len('-DONE.json')]}.md" for p in changed
             if p.startswith(plans + "/") and p.endswith("-DONE.json") and (worktree / p).exists()
             and not (worktree / plans / (Path(p).name[:-len("-DONE.json")] + ".md")).exists()]
    if not named or not changed:
        gaps.insert(0, "no changed files are named")
    return None if not gaps else "The plan isn't complete: " + "; ".join(gaps) + \
        ". Finish it, then end with `PLANNED: <files>`."


def done_docs_at(worktree: Path, plans: str, ref: str) -> dict:
    """The done-when files under `plans` at `ref`, by file name, parsed (ones that don't parse are left out)."""
    out = {}
    listed = git(worktree, "ls-tree", "--name-only", f"{ref}:{plans}").stdout.split("\n")
    for name in (n for n in listed if n.endswith("-DONE.json")):
        try:
            out[name] = json.loads(show(worktree, ref, f"{plans}/{name}") or "")
        except json.JSONDecodeError:
            pass
    return out


def cmd_plan(a: argparse.Namespace) -> None:
    new_command()
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, missing_ok=True)  # a first plan writes the profile itself
    host, model, effort = resolve(a, prof, "plan")
    preflight(host, worktree, "plan")
    info = dict(host=host, model=model, effort=effort)
    again = loop_cmd("plan", "--worktree", str(worktree), "--task", a.task,
                     *(["--host", a.host] if a.host else []), *(["--model", a.model] if a.model else []),
                     *(["--effort", a.effort] if a.effort else []))
    if not run_lock(worktree, "_plan"):
        who = run_holder_info(worktree, "_plan")
        emit("TAKEN", **info, by="another planner on this repository" + holder_text(who),
             **({"holder": who} if who else {}), next=next_cmd(
                 again, "lead", "only one planner runs per repository at a time, and another holds it"
                                f"{holder_text(who)}; run this again once it stops (`loops --repo` shows when)"))
    install_stop()
    loop_register(worktree, "plan", task=a.task.splitlines()[0][:80] if a.task.strip() else "", **info)
    if empty := no_base(worktree, prof):  # say so before a planner spends a turn whose files couldn't land
        emit("FLOOR", **info, reason=str(empty), next=empty.next)
    if dirty := git(worktree, "status", "--porcelain").stdout.strip():
        emit("INVALID", **info, problems=["the planner needs a clean worktree, so the loop can tell its files from "
                                          "anything else: " + dirty[:300]])
    if (worktree / PROFILE_FILE).exists():
        sync_worktree(worktree, prof)  # plan from the tip, so the planner has no reason to move the worktree itself
        try:
            ahead = git(worktree, "log", "--format=%h %s", f"{tip(worktree, prof)}..HEAD").stdout.strip().splitlines()
        except TipError:
            ahead = []
        if ahead:  # they would land with the plan unmeasured
            wt = shlex.quote(str(worktree))
            fresh_wt = worktree.parent / f"{worktree.name}-plan-{time.strftime('%Y%m%d%H%M%S')}"
            emit("INVALID", **info, problems=[
                f"this worktree has {len(ahead)} commit{'s' if len(ahead) > 1 else ''} the integrated tip doesn't: "
                f"{'; '.join(ahead[:5])}. A planner starts on the tip, so nothing lands with its plan unchecked"],
                next=next_cmd(f"git -C {wt} worktree add --detach {shlex.quote(str(fresh_wt))} {base_ref(prof)}",
                              "lead", f"leaves this checkout and its commits alone and makes a fresh worktree on the "
                              f"tip, at {fresh_wt}; run the plan there. If those commits are plan files the owner "
                              "wants, `adopt` lands them instead",
                              then=loop_cmd("plan", "--worktree", str(fresh_wt), "--task", a.task,
                                            *(["--host", a.host] if a.host else []),
                                            *(["--model", a.model] if a.model else []),
                                            *(["--effort", a.effort] if a.effort else [])),
                              alternative=loop_cmd("adopt", "--worktree", str(worktree))))
    start = head_commit(worktree)
    seen = reflog_size(worktree)
    before = done_docs_at(worktree, prof["plans"], start)
    prompt = PLAN_TEMPLATE.format(task=a.task, skill=skill_note("plan-module", host), loop=LOOP)
    out = one_session(host, prof, model, effort, worktree, prompt, "plan", lambda msg: plan_owed(worktree, start, msg),
                      a.turn_timeout_hours * 3600, title=f"plan: {a.task.splitlines()[0][:60]}")
    result = out.pop("result")
    out.pop("observed", None)
    if out.get("owed") is None:
        out.pop("owed", None)
    word = report_word(out.get("report", ""))
    if result == "FINISHED" and word in ("BLOCKED", "NEEDS_CONTEXT"):
        result = word
    if result != "FINISHED":  # a progress report, a blocker or a host failure: nothing lands
        emit(result, **info, **out, landed=False, left_uncommitted=changed_paths(worktree, start))
    try:
        prof = profile(worktree, strict=True)
    except SystemExit as e:
        emit("PLANNED", **info, **out, landed=False, problems=[str(e)])

    # What a turn wrote is what it left uncommitted; that is all the loop commits and lands. Its HEAD may have moved
    # along the tip (a `land` elsewhere fast-forwards the checkout holding the base branch), never off it.
    try:
        fresh = tip(worktree, prof)
    except TipError as e:
        emit("PLANNED", **info, **out, landed=False, problems=[f"the turn can't be checked, so nothing landed: {e}"])
    wt = shlex.quote(str(worktree))
    if forged := record_tampering(worktree, prof, start, fresh):
        emit("INVALID", **info, **out, landed=False, problems=[
            f"while this turn ran, {plural(len(forged), 'commit')} without the loop's trailer changed an acceptance "
            f"record on the tip: {', '.join(forged)}"], next=next_cmd(
            None, "owner", "report it: those commits reached the integrated tip during a planner turn, and only the "
            "loop writes acceptance records. The owner decides what to do with them; the loop doesn't take commits "
            f"back out. Nothing from this turn landed, and its files are still uncommitted in {worktree}"))
    if made := commits_made(worktree, seen):  # read before the loop makes its own commit here
        emit("INVALID", **info, **out, landed=False, problems=[
            f"the planner committed in this worktree ({plural(len(made), 'commit')} in its reflog during the turn: "
            f"{'; '.join(made[:5])}); the loop lands only what a planner leaves uncommitted"], next=next_cmd(
            None, "lead", "nothing landed. Any commit that reached the integrated tip is already there, and the "
            "turn's other files are uncommitted here; look at them and keep or drop them yourself, then plan again "
            "from a clean worktree on the tip"))
    if own := git(worktree, "log", "--format=%h %s", f"{fresh}..HEAD").stdout.strip().splitlines():
        emit("INVALID", **info, **out, landed=False, problems=[
            f"the planner committed in this worktree ({plural(len(own), 'commit')} the tip doesn't have: "
            f"{'; '.join(own[:5])}); the loop lands only what a planner leaves uncommitted"], next=next_cmd(
            None, "lead", "nothing landed. The turn's commits are on this worktree's branch and any other files are "
            "uncommitted here; look at them and keep or drop them yourself, then plan again from a clean worktree "
            "on the tip"))
    start = head_commit(worktree)
    before = done_docs_at(worktree, prof["plans"], start)
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
        emit("INVALID", **info, **out, landed=False, problems=problems[:20], next=next_cmd(
            f"git -C {wt} stash push --include-untracked -m 'refused planner turn' && "
            + loop_cmd("plan", "--worktree", str(worktree), "--task",
                       f"{a.task}\n\nYour last turn on this was refused, for: {'; '.join(problems[:5])}. Its files are "
                       "in the latest git stash (`git stash show -p --include-untracked`); reuse what holds up."),
            "lead", "the plan didn't land and its files are still uncommitted here. This sets them aside (nothing is "
                    "lost) and gives a planner the task again with the problems, since only a planner turn may fix "
                    "them"))
    if git(worktree, "status", "--porcelain").stdout.strip():
        git(worktree, "add", "-A")
        git(worktree, *ident(worktree), "commit", "--quiet", "-m", f"Plan: {a.task.splitlines()[0][:60]}",
            "-m", a.task)  # the subject is short; the body keeps the whole task
    try:  # the tip the plan lands on: its counts are the ones a re-plan settles
        prior_ref = tip(worktree, prof)
    except TipError:
        prior_ref = None
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
                # first loop write for a module that stood before this plan without a record: as it stood, only in
                # a repository that had no records; otherwise it's new, and nothing in it is accepted
                record = adopt(before[Path(done_rel(prof, stem)).name],
                               text_hash(show(worktree, start, f"{prof['plans']}/{stem}.md")),
                               unrecorded(t, prof, "HEAD"))
            else:
                record = {"module": stem, "design": None, "milestones": {}}
            try:
                prior = json.loads(show(worktree, prior_ref, done_rel(prof, stem)) or "") if prior_ref else None
            except json.JSONDecodeError:
                prior = None
            replanned.extend(settle_replans(prior or before.get(Path(done_rel(prof, stem)).name), doc, stem))
            # the stamp names the task; the whole of it is kept once, under `briefs`
            authorise_doc(doc, record, {"by": "plan", "task": a.task.splitlines()[0][:120], "at": now()})
            # every planner task, whole, where design reviewers and later planners are pointed to read the ask
            record.setdefault("briefs", []).append({"task": a.task, "at": now()})
            record["planner"] = {"host": host, "at": now()}  # who wrote the plan, so its design review goes elsewhere
            write_json(path, doc)
            write_json(rec_path, record)
            written += [done_rel(prof, stem), record_rel(prof, stem)]
        return written

    replanned: list[str] = []

    ok, detail = loop_write(worktree, prof, "_plan", change, "orchestrate: authorise the plan")
    if not ok:
        emit("PLANNED", **info, **out, landed=True, commit=landed, problems=[f"couldn't record the definitions: {detail}"])
    ref = tip(worktree, prof, fetch=False)
    proj = project(worktree, prof, ref)
    owed = [e["stem"] for e in proj.values() if not e["problems"] and not design_ok(e["record"], e["design"])
            and next_step(e["stem"].upper(), proj)["status"] != "finished"]
    if owed:
        reviewer = design_review_host(prof, proj[owed[0].upper()]["record"], host)
        then = next_cmd(loop_cmd("review", "--module", owed[0], "--milestone", "design", "--worktree", str(worktree),
                                 "--host", reviewer), "lead",
                        f"{', '.join(owed)} {'is' if len(owed) == 1 else 'are'} owed a design review before building; "
                        f"review {owed[0]}'s design" + (" on the host the planner didn't use" if reviewer != host else
                                                        "") + " (or `run` does it first, unless --no-design-review)")
    else:
        then = next_cmd(loop_cmd("ready", "--worktree", str(worktree)), "lead", "see what's ready now")
    found = {stem: len(assumptions(show(worktree, ref, plan_rel(prof, stem)))) for stem in modules}
    emit("PLANNED", **info, **out, landed=True, commit=detail, modules=modules, design_review_owed=owed,
         **({"assumptions": {k: n for k, n in found.items() if n},
             "assumptions_where": "lines starting `Assumption:` in each module's plan log; `report` lists them for "
                                  "the owner to overturn"} if any(found.values()) else {}),
         **({"replanned": replanned} if replanned else {}), next=then)


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
    prof = profile(worktree, missing_ok=True)
    empty = {"ready": [], "waiting": [], "review_owed": [], "replan_owed": [], "design_owed": [], "blocked": [], "parked": [],
             "taken": [], "finished": [], "invalid": []}
    if not_yet := unplanned(worktree):
        try:
            ref = tip(worktree, prof)
        except TipError:
            ref = None
        key = "behind" if not_yet.get("behind") else "unplanned"
        print(json.dumps({"tip": ref, **empty, key: not_yet["reason"], "next": not_yet["next"]}, indent=2))
        return
    ref, proj = read_project(worktree, prof)
    held_claims, mine = claims(worktree), me(worktree)
    out = {"tip": ref, **empty}
    steps = []
    for key in sorted(proj):
        step = next_step(key, proj, held_claims, mine)
        steps.append(dict(step))
        if step["status"] == "replan_owed":  # not the builder's: say whose it is, wherever the lead reads it
            step["next"] = next_for(step, worktree, prof, proj)
        out[step.pop("status")].append(step)
    drift = plan_drift(worktree, prof, ref)
    if drift["uncommitted"] or drift["unintegrated"] or not out["ready"]:
        out.update(drift_fields(drift, worktree, None if out["ready"] else
                                nothing_ready_next(steps, worktree, prof, proj)))
    out.update(profile_note(drift, prof))
    for k in list(out):
        if isinstance(out[k], list):
            out[k] = [dict(x, next=fit_next(x["next"])) if isinstance(x, dict) and "next" in x else x for x in out[k]]
    if "next" in out:
        out["next"] = fit_next(out["next"])
    print(json.dumps(out, indent=2))


def cmd_status(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, missing_ok=True)
    folder = Path(git_common_dir(worktree)) / "orchestrate"
    records = {r["pid"]: r for r in live_loops(clean=False, processes=False)[0] if r.get("registered")}

    def running(name: str) -> str:
        """`, running …` when a live loop in this repository holds `name`'s run lock."""
        pid = run_holder(folder, name)
        if pid is None:
            return ""
        rec = records.get(pid)
        if not rec:
            return f"; running (pid {pid})"
        v = loop_view(rec)
        what = " ".join(x for x in (v["role"], v["milestone"] if v["role"] != "plan" else None, v["host"]) if x)
        turn = f", turn {v['turns'] + 1} running for {ago(v['turn_running_s'])}" \
            if v.get("turn_running_s") is not None else ""
        return (f"; running: {what}, pid {pid}, {v['turns']} turns done{turn}, last activity {ago(v['idle_s'])} ago")

    if planner := running("_plan"):
        print("planner" + planner)
    if not_yet := unplanned(worktree):
        lead = "Bring it up with" if not_yet.get("behind") else "Plan it with"
        reason = f"{not_yet['reason'][0].upper()}{not_yet['reason'][1:]}."
        print(f"{reason} {lead}:\n  {not_yet['next']['command']}" if not_yet["next"]["command"] else reason)
        return
    ref, proj = read_project(worktree, prof)
    drift = plan_drift(worktree, prof, ref)
    if drift["uncommitted"] or drift["unintegrated"]:
        fields = drift_fields(drift, worktree)
        print(f"{fields['unlanded_plans']['note']}; land them with `{fields['next']['command']}`")
    if note := profile_note(drift, prof):
        print(note["profile_differs"])
    if not proj:
        print(f"no modules planned at {base_ref(prof)} yet (no done-when files under {prof['plans']})")
    keys = [a.module.upper()] if a.module else sorted(proj)
    for key in keys:
        if key not in proj:
            print(f"{a.module}: not planned at the integrated tip" + running(key))
            continue
        e, step = proj[key], next_step(key, proj, claims(worktree), me(worktree))
        print(f"{e['stem']}: {step['status']}" + (f" ({step['milestone']})" if step.get("milestone") else "") +
              running(key))
        for problem in e["problems"] or step.get("problems", []):
            print(f"  invalid: {problem}")
        if step["status"] == "replan_owed":
            print(f"  {step['milestone']} failed review {step['fails']} times; re-plan it before any more building:\n"
                  f"    {next_for(step, worktree, prof, proj)['command']}")
        if e["problems"]:
            continue
        for m in e["doc"]["milestones"]:
            flags, state = [], m.get("state")
            if accepted(m, e["record"]):
                flags.append("accepted")
            elif m["id"] == step.get("milestone"):
                if step["status"] == "ready" and state in ("done", "claimed"):
                    # the builder's file says so, but the loop hasn't checked the claim yet; `run` checks it
                    state = f"{state}, unchecked"
                    flags.append("the loop hasn't checked this claim yet; `run` checks it")
                else:
                    flags.append(step["status"].replace("_", " "))
                if step.get("needs"):
                    flags.append("on " + ", ".join(step["needs"]))
                if step.get("blocked"):
                    flags.append(step["blocked"])
            reviews = (e["record"]["milestones"].get(m["id"]) or {}).get("reviews") or []
            if reviews:
                flags.append(f"last review {reviews[-1]['verdict']} {reviews[-1].get('at', '')}".strip())
            print(f"  {m['id']}\t{state}\tfails={m.get('fails', 0)}\t{passing(m)}/{len(m['items'])} pass"
                  f"\t{m.get('name', '')}" + ("\t" + "; ".join(flags) if flags else ""))


def cmd_next(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree)
    stem = module_stem(worktree, prof, a.module)
    try:  # the count at the integrated tip, where the review landed, rather than this worktree's older copy
        doc = json.loads(show(worktree, tip(worktree, prof), done_rel(prof, stem)) or "")
    except (TipError, json.JSONDecodeError, SystemExit):
        doc = load_done(worktree, stem, prof)
    milestone = find(doc, a.milestone)
    fails, replans = int(milestone.get("fails", 0)), int(milestone.get("replans", 0))
    action = escalation(fails, replans)
    if action in ("replan", "park"):  # what goes to the planner, or to the owner, rather than the builder's findings
        then = ladder_next(action, stem, milestone["id"], fails, worktree, prof)
        message = replan_task(stem, milestone["id"], fails, prof, worktree) if action == "replan" else then["why"]
    else:
        message = FINDINGS_TEMPLATE.format(milestone=milestone["id"], module=stem, evidence=prof["evidence"])
        then = ladder_next(action, stem, milestone["id"], fails, worktree, prof) if action != "none" else None
    print(json.dumps({"milestone": milestone["id"], "fails": fails, "replans": replans,
                      "action": action, "message": message, **({"next": fit_next(then)} if then else {})}))


def cmd_profile(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    if not_yet := unplanned(worktree):
        print(json.dumps({"planned": False, "problems": [not_yet["reason"]], "next": not_yet["next"],
                          **({"behind": not_yet["behind"]} if not_yet.get("behind") else {})}, indent=2))
        sys.exit(1)
    prof = profile(worktree, strict=True)
    host = (a.host or default_host(prof)).lower()
    prof.pop("model")  # the Codex model, kept for its flags; `models` holds every host's, so none looks like the default
    found = instruction_warnings(worktree, cli_version("claude")) if host == "claude" else []
    found += [w for role in ROLE_SKILLS for w in skill_warnings(host, worktree, role)]
    found += browser_warnings(worktree) if host == "codex" else []
    prof["preflight"] = {"host": host, "warnings": found}
    print(json.dumps(prof, indent=2))


def cmd_quota(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve() if a.worktree else None
    report = quota_report(worktree, budget_s=a.budget)
    print(json.dumps(report, indent=2) if a.json else quota_text(report))


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


BROKEN_WHY = ("the check as written can't run ({}). Fix how it's written (quoting, the command's name, the inline "
              "code's syntax) without changing what it tests or making it easier to pass; a builder can't edit a "
              "pinned check, so it's fixed in the plan before a builder starts")


def check_broken(command: str, code: int, output: str, tree: Path) -> str | None:
    """Why a check can't run as written, only where that can be told for certain: the string doesn't parse as shell,
    or exit 126 (found but not executable). Anything else is a plain failure: exit 127, since a missing command may
    be one the milestone installs; and a syntax error, even in code passed inline, since exec'd or eval'd files report
    themselves as the inline code. The output says which."""
    parse = subprocess.run(["sh", "-n", "-c", command], capture_output=True, text=True)
    if parse.returncode != 0:
        return f"it doesn't parse as shell: {(parse.stderr or '').strip()[-200:]}"
    if code == 126:
        return "exit 126: the command was found but couldn't be executed"
    return None


def try_check(tree: Path, command: str, lock: str | None, timeout_s: float) -> dict:
    """One check run in `tree`: `pass`, `fail` (it ran and failed: likely the work isn't there yet; read the output),
    `error` (it can't run as written, told only where certain; see check_broken) or `timeout`."""
    in_git = subprocess.run(["git", "-C", str(tree), "rev-parse"], capture_output=True).returncode == 0
    if lock and in_git:
        with held(lock, tree):
            code, out, err = run_proc(command, tree, timeout_s, shell=True)
    else:
        code, out, err = run_proc(command, tree, timeout_s, shell=True)
    text = (out + ("\n" if out and err else "") + err).strip()
    if code == 0:
        result, why = "pass", None
    elif code == 124:
        result, why = "timeout", f"still running after {timeout_s:.0f} s"
    elif broken := check_broken(command, code, text, tree):
        result, why = "error", BROKEN_WHY.format(broken)
    else:
        result, why = "fail", ("the check ran and failed, as it should before the work exists; the output says "
                               "whether that's the reason")
    return {"exit": code, "result": result, **({"why": why} if why else {}), "output": text[-1500:]}


def cmd_check(a: argparse.Namespace) -> None:
    """Runs one milestone's checks in a tree, item by item, without recording anything."""
    tree = Path(a.worktree).resolve()
    source = Path(a.plans_from).resolve() if a.plans_from else tree
    prof = profile(source, missing_ok=True)
    stem = module_stem(source, prof, a.module)
    doc = load_done(source, stem, prof)
    if problems := validate(doc, stem.upper()):
        raise SystemExit(f"error: {done_rel(prof, stem)} in {source} is invalid: " + "; ".join(problems[:5]))
    milestone = find(doc, a.milestone)
    items = []
    for i in milestone["items"]:
        if not i.get("check"):
            proof = [k for k in ("inspect", "ask", "attended") if i.get(k)]
            items.append({"id": i["id"], "result": "no check", "proof": proof})
            continue
        items.append({"id": i["id"], "check": i["check"], **(({"lock": i["lock"]}) if i.get("lock") else {}),
                      **try_check(tree, i["check"], i.get("lock"), a.timeout)})
    if prof.get("check"):  # the profile's Check gates every claim too
        items.append({"id": "Check", "check": prof["check"], **try_check(tree, prof["check"], None, a.timeout)})
    checked = [i for i in items if "check" in i]
    counts = {r: sum(i["result"] == r for i in checked) for r in ("pass", "fail", "error", "timeout")}
    out = {"module": stem, "milestone": milestone["id"], "tree": str(tree),
           "plan": str(source / done_rel(prof, stem)), **counts, "items": items}
    print(json.dumps(out, indent=2) if getattr(a, "json", False) else check_text(out))
    sys.exit(0 if counts["pass"] == len(checked) else 1)


def check_text(out: dict) -> str:
    """`check`'s readout for a person: a count, then each check with its result, why, and its last output lines."""
    shown = ", ".join(f"{out[r]} {r}" for r in ("pass", "fail", "error", "timeout") if out[r] or r == "pass")
    lines = [f"{out['module']} {out['milestone']} in {out['tree']}: {shown}"]
    for i in out["items"]:
        if "check" not in i:
            lines.append(f"  {i['id']}  no check ({', '.join(i.get('proof') or []) or 'nothing to run'})")
            continue
        command = i["check"].strip().splitlines() or [""]
        shown_check = command[0][:90] + ("..." if len(command) > 1 or len(command[0]) > 90 else "")
        lines.append(f"  {i['id']}  {i['result']}" + (f" (exit {i['exit']})" if i["result"] != "pass" else "") +
                     f"  {shown_check}")
        if i["result"] != "pass":
            if i.get("why"):
                lines.append(f"      {i['why']}")
            lines += [f"      | {line}" for line in (i.get("output") or "").splitlines()[-4:]]
    lines.append("Everything, with each check's full output tail, as JSON: add --json.")
    return "\n".join(lines)


def cmd_land(a: argparse.Namespace) -> None:
    if os.environ.get("ORCHESTRATE_ROLE") in ("plan", "review"):
        raise SystemExit(f"error: land isn't for a {os.environ['ORCHESTRATE_ROLE']} session; the loop lands what a "
                         "planner or reviewer leaves, after checking it")
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    if dirty := git(worktree, "status", "--porcelain").stdout.strip():
        print(json.dumps({"result": "FAILED", "detail": "commit, remove or ignore these first: " + dirty[:300]}))
        sys.exit(1)
    ok, detail = land(worktree, prof, check=not a.no_check)
    print(json.dumps({"result": "LANDED" if ok else "FAILED", "detail": detail, "commit": head_commit(worktree)}))
    sys.exit(0 if ok else 1)


def cmd_loops(a: argparse.Namespace) -> None:
    repo = None
    if a.repo:
        where = Path(a.repo).resolve()
        if subprocess.run(["git", "-C", str(where), "rev-parse"], capture_output=True).returncode != 0:
            raise SystemExit(f"error: {where} is not in a git repository")
        repo = repository_of(git_common_dir(where))
    loops, removed = live_loops(repo)
    views = [loop_view(r) for r in loops]
    if a.json:
        print(json.dumps({"loops": views, "cleaned": removed}, indent=2))
        return
    print(f"{len(views)} loop{'' if len(views) == 1 else 's'} running" + (f" in {repo}" if repo else "") +
          (f"; cleared {len(removed)} file{'' if len(removed) == 1 else 's'} left by loops that died" if removed
           else ""))
    shown = object()
    for v in views:
        if v["repository"] != shown:
            shown = v["repository"]
            print(f"\n{Path(shown).name} ({shown})" if shown else "\nrepository not known")
        print(loop_line(v))


def cmd_pause(a: argparse.Namespace) -> None:
    folder = Path(git_common_dir(Path(a.worktree).resolve())) / "orchestrate"
    names = [a.module.upper()] if a.module else [p.name[len("run-"):-len(".lock")] for p in folder.glob("run-*.lock")]
    paused = []
    for name in names:
        pid = run_holder(folder, name)  # reads only, so a run starting now isn't turned away
        if pid is None:
            continue  # nobody holds it, so nothing is running
        try:
            os.kill(pid, signal.SIGTERM)
            paused.append({"run": name, "pid": pid})
        except ProcessLookupError:
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


def ledger_rows(worktree: Path) -> list[dict]:
    """The usage ledger's lines for this repository (every worktree shares it), oldest first."""
    path = Path(git_common_dir(worktree)) / "orchestrate" / "usage.jsonl"
    rows = []
    try:
        for line in path.read_text().splitlines():
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    except OSError:
        pass
    return rows


def since_stamp(hours: float | None) -> str | None:
    if not hours:
        return None
    return datetime.fromtimestamp(time.time() - hours * 3600, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tally(total: dict | None, row: dict) -> dict:
    """`total` with one ledger line added: its tokens, one more turn run, and its host."""
    total = add_usage(total, row.get("usage") or {})
    total["runs"] = total.get("runs", 0) + (row.get("runs") or 1)
    hosts = set(total.get("hosts") or []) | ({row["host"]} if row.get("host") else set())
    total["hosts"] = sorted(hosts)
    return total


def record_rows(worktree: Path) -> list[dict]:
    """Ledger-shaped rows from the committed acceptance records, for milestones this machine's ledger knows nothing
    about (built before it existed, or on another machine): each milestone's last claim with its session's tokens
    (earlier sessions on it aren't kept), every review, and the module's last design review."""
    prof = profile(worktree, missing_ok=True)
    if not (worktree / PROFILE_FILE).exists():
        return []
    ref = base_ref(prof) if git(worktree, "rev-parse", "--verify", "-q", base_ref(prof)).returncode == 0 else "HEAD"
    rows = []
    for key, e in project(worktree, prof, ref).items():
        rec, stem = e["record"], e["stem"]

        def row(mid, role, x):
            if isinstance(x, dict) and isinstance(x.get("usage"), dict):
                use = x.get("session_usage") if isinstance(x.get("session_usage"), dict) else x["usage"]
                rows.append({"module": stem, "milestone": mid, "role": role, "host": x.get("host"),
                             "at": x.get("at"), "usage": use, "runs": use.get("turns") or 1})
        row("design", "review", rec.get("design"))
        for mid, m in (rec.get("milestones") or {}).items():
            row(mid, "build", m.get("claim"))
            for r in m.get("reviews") or []:
                row(mid, "review", r)
    return rows


def cost_of(rows: list[dict], module: str | None = None, since: str | None = None,
            records: list[dict] | None = None) -> dict:
    """Per-milestone totals from ledger lines: planning, then each module's milestones (a design review sits under
    milestone `design`), each split by role (build, review), with a grand total. `runs` counts turns run; `turns`
    counts those that reported tokens; `incomplete_turns` those that showed none or only some. A milestone the
    ledger has nothing on is filled from `records` (record_rows) and marked `source: records`."""
    out: dict = {"planning": {}, "modules": {}, "total": {}}
    for row in rows:
        if since and (row.get("at") or "") < since:
            continue
        mod = row.get("module")
        if module and (mod or "").upper() != module.upper():
            continue
        if row.get("role") == "plan" or not mod:
            out["planning"] = tally(out["planning"], row)
        else:
            ms = out["modules"].setdefault(mod, {}).setdefault(row.get("milestone") or "unassigned", {})
            ms[row.get("role") or "build"] = tally(ms.get(row.get("role") or "build"), row)
            ms["total"] = tally(ms.get("total"), row)
            ms["source"] = "ledger"
        out["total"] = tally(out["total"], row)
    for row in records or []:
        if since and (row.get("at") or "") < since:
            continue
        mod, mid = row["module"], row["milestone"]
        if (module and mod.upper() != module.upper()) or \
                (out["modules"].get(mod, {}).get(mid) or {}).get("source") == "ledger":
            continue
        ms = out["modules"].setdefault(mod, {}).setdefault(mid, {"source": "records"})
        ms[row["role"]] = tally(ms.get(row["role"]), row)
        ms["total"] = tally(ms.get("total"), row)
        out["total"] = tally(out["total"], row)
        out["from_records"] = True
    return out


def cost_line(t: dict) -> str:
    text = f"{plural(t.get('runs', 0), 'turn')}, {tokens_text(t if t.get('turns') else None, t.get('hosts'))}"
    if t.get("incomplete_turns"):
        text += f" ({t['incomplete_turns']} showed no tokens or only some, so this is a floor)"
    return text + (f" on {', '.join(t['hosts'])}" if t.get("hosts") else "")


def cost_text(c: dict) -> list[str]:
    lines = []
    if c["planning"]:
        lines.append(f"planning: {cost_line(c['planning'])}")
    for mod in sorted(c["modules"]):
        for mid, roles in sorted(c["modules"][mod].items(), key=lambda kv: (kv[0] != "design", kv[0])):
            parts = [f"{role} {cost_line(t)}" for role, t in sorted(roles.items())
                     if role not in ("total", "source")]
            lines.append(f"{mod} {mid}: " + "; ".join(parts) +
                         (" [from the committed record]" if roles.get("source") == "records" else ""))
    lines.append(f"total: {cost_line(c['total'])}" if c["total"] else "total: no turns recorded")
    return lines


def cmd_cost(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    c = cost_of(ledger_rows(worktree), a.module, since_stamp(a.since), record_rows(worktree))
    if a.json:
        print(json.dumps(c, indent=2))
        return
    print(cost_header(worktree, c, a.since))
    print("\n".join("  " + line for line in cost_text(c)))


def cost_header(worktree: Path, c: dict, since: float | None) -> str:
    span = f" in the last {since:g} h" if since else ""
    text = (f"Tokens the loop's turns used{span}, from this machine's ledger "
            f"({Path(git_common_dir(worktree)) / 'orchestrate' / 'usage.jsonl'}), which has every turn run here")
    if c.get("from_records"):
        text += ("; milestones it has nothing on (built before it existed, or elsewhere) come from the committed "
                 "acceptance records, marked [from the committed record]: each one's last claim with its session's "
                 "tokens, and every review, so earlier sessions and paused turns aren't in those")
    return text + ":"


def report_text(worktree: Path, hours: float) -> tuple[str, str]:
    """(date, markdown): the factual half of the lead's report for the last `hours`, read from the records at the
    integrated tip and this machine's usage ledger. The lead adds the judgement: what it means, what to do next."""
    prof = profile(worktree)
    ref, proj = read_project(worktree, prof)
    since = since_stamp(hours) or ""
    date = datetime.now().strftime("%Y-%m-%d")
    graded = worktree / prof["graded_examples"]
    graded_n = sum(1 for line in graded.read_text().splitlines() if line.startswith(("## ", "### "))) \
        if graded.exists() else 0
    closed, verdicts, waiting, attended, adopted, decided, assumed = [], [], [], [], [], [], []
    planned: dict = {}  # (minute, task) -> modules: one planner turn writes the same brief to each module it changed
    for key, e in sorted(proj.items()):
        stem, rec = e["stem"], e["record"]
        for b in rec.get("briefs") or []:
            if (b.get("at") or "") >= since:
                planned.setdefault(((b.get("at") or "")[:16], b.get("task") or ""), []).append(stem)
        decided += [line for at, line in sorted(owner_decisions(stem, rec)) if at >= since]
        if chosen := assumptions(show(worktree, ref, plan_rel(prof, stem))):
            assumed += [f"- {stem} ({md_link('plan', plan_rel(prof, stem))}):"] + [f"  - {x}" for x in chosen]
        for d in design_reviews(worktree, prof, ref, stem, rec):
            if (d.get("at") or "") >= since:
                verdicts.append(f"- {stem} design: {d.get('verdict')} ({d.get('at')}" +
                                (f", {d['host']}" if d.get("host") else "") +
                                (f", by {d['by']}" if d.get("by") not in (None, "review") else "") + ")" +
                                (f", {md_link(d['review'], d['review'])}" if d.get("review") else "") +
                                (f"; not counted: {d['not_counted']}" if d.get("not_counted") else ""))
        if e["problems"]:
            waiting.append(f"- {stem}: invalid: {'; '.join(e['problems'])}")
            continue
        step = next_step(key, proj, claims(worktree), me(worktree))
        for m in e["doc"].get("milestones") or []:
            r = rec.get("milestones", {}).get(m["id"]) or {}
            acc = r.get("accepted") or {}
            auth = r.get("authorised") or {}
            if auth.get("by") == "adopt" and auth.get("at", "") >= since:
                adopted.append(f"- {stem} {m['id']}: definitions authorised by adopt {auth.get('at')}, before the "
                               f"design review passed (files: {', '.join(auth.get('files') or [])})")
            if accepted(m, rec) and acc.get("at", "") >= since:
                link = f", {md_link(acc['review'], acc['review'])}" if acc.get("review") else ""
                name = m.get("name") if m.get("name") not in (None, "", m["id"]) else ""
                closed.append(f"- {stem} {m['id']} {name}".rstrip() + f": accepted by {acc.get('by')} "
                              f"{acc.get('at')}{link}")
            for v in r.get("reviews") or []:
                if v.get("at", "") >= since:
                    verdicts.append(f"- {stem} {m['id']}: {v.get('verdict')} ({v.get('at')}, {v.get('host') or 'host?'})"
                                    + (f", {md_link(v['review'], v['review'])}" if v.get("review") else
                                       f", overwritten before rounds were kept (git log -p -- {v['review_in_history']})"
                                       if v.get("review_in_history") else ""))
            if m.get("state") == "parked":
                waiting.append(f"- {stem} {m['id']}: parked after {m.get('fails', 0)} failed reviews; the owner "
                               f"unparks it (`owner unpark`) or re-scopes it")
            elif m.get("state") == "blocked":
                waiting.append(f"- {stem} {m['id']}: blocked: {m.get('blocked', '')}")
            if not accepted(m, rec):
                attended += [f"- {stem} {m['id']} {i['id']}: {i.get('statement', '')}\n  Ask the owner in chat; "
                             f"their answer goes in `{owner_cmd('answer', stem, m['id'], str(worktree), i['id'])}`"
                             for i in m.get("items") or [] if i.get("attended") and i.get("status") != "pass"]
        if step["status"] in ("waiting", "design_owed", "review_owed", "replan_owed") and step.get("milestone"):
            why = step.get("reason") or (", ".join(step["needs"]) if step.get("needs") else "")
            waiting.append(f"- {stem} {step['milestone']}: {step['status'].replace('_', ' ')}" + (f": {why}" if why else ""))
    c = cost_of(ledger_rows(worktree), since=since, records=record_rows(worktree))
    builders = len({(r.get("module"), r.get("milestone"), r.get("session")) for r in ledger_rows(worktree)
                    if r.get("role") == "build" and (r.get("at") or "") >= since})
    flag = (f" The project's graded examples hold {graded_n} verdicts, fewer than about ten, so spot-check every one."
            if graded_n < 10 else "")
    out = [f"# Build report {date}", "",
           f"The last {hours:g} h, from the records at {ref} and this machine's usage ledger. The lead adds what it "
           "means and what comes next.", "",
           "## Closed", "", *(closed or ["- nothing accepted in this window"]), "",
           "## Verdicts", "", *(verdicts or ["- no reviews in this window"])]
    if verdicts and flag:
        out += ["", flag.strip()]
    if adopted:
        out += ["", "## Definitions changed through adopt", "",
                "Revised outside a planner turn while the module was a draft; its design review judges them.", "",
                *adopted]
    if decided:
        out += ["", "## Decisions recorded in the owner's name (check each is one you made)", "",
                "Every `owner` command in this window, with the words recorded as the owner's. The loop can't tell "
                "who ran one, so a decision here that the owner didn't make is the thing to look for.", "", *decided]
    if planned:
        out += ["", "## Planner turns (with the task each was given)", "",
                *[f"- {at.replace('T', ' ')}, {', '.join(mods)}: " + task.replace("\n", "\n  ")
                  for (at, task), mods in sorted(planned.items())]]
    if assumed:
        out += ["", "## Assumptions the planners made (for the owner to overturn)", "",
                "Readings of the request a planner chose where it could be read more than one way, from the lines "
                "starting `Assumption:` in each plan's log. Each stands until the owner overturns it; overturning one "
                "is a re-plan.", "", *assumed]
    out += ["", "## Parked, blocked or waiting", "", *(waiting or ["- nothing"]), "",
            "## Attended items (need a person or hardware)", "", *(attended or ["- none open"]), "",
            "## Cost", "", f"- build sessions: {builders}", *("- " + line for line in cost_text(c)),
            ("- [from the committed record] marks milestones this machine's ledger has nothing on: their last "
             "claim's session and every review, as the acceptance records keep them" if c.get("from_records") else
             "- tokens are this machine's ledger; `quota` gives the Codex forecast"), ""]
    return date, "\n".join(out)


def design_reviews(worktree: Path, prof: dict, ref: str, stem: str, rec: dict) -> list[dict]:
    """Every design review of a module, oldest first: the record's history and its latest, plus any earlier review
    kept as design-review-N.md that the record predates (its verdict read from the file's last line)."""
    out = list(rec.get("design_history") or []) + ([rec["design"]] if rec.get("design") else [])
    named = {d.get("review") for d in out}
    folder = f"{prof['evidence']}/{stem}"
    listed = git(worktree, "ls-tree", "--name-only", f"{ref}:{folder}").stdout.split() if ref else []
    kept = sorted((n for n in listed if re.fullmatch(r"design-review-\d+\.md", n)),
                  key=lambda n: int(re.sub(r"\D", "", n)))
    older = []
    for name in kept:
        path = f"{folder}/{name}"
        if path in named:
            continue
        last = next((line.strip() for line in reversed((show(worktree, ref, path) or "").splitlines())
                     if line.strip()), "")
        verdict = "ok" if last.startswith("DESIGN OK") else "changes" if last.startswith("DESIGN CHANGES") else "?"
        # The copy was made when the next review replaced it, so its own commit time is that later review's; the
        # review it holds landed with the last change to design-review.md before that commit. In UTC.
        added = git(worktree, "log", "-1", "--diff-filter=A", "--format=%H", ref, "--", path).stdout.strip()
        stamp = (git(worktree, "log", "-1", "--format=%ct", f"{added}^", "--", f"{folder}/design-review.md").stdout
                 .strip() if added else "") or git(worktree, "log", "-1", "--format=%ct", ref, "--", path).stdout.strip()
        at = datetime.fromtimestamp(int(stamp), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if stamp.isdigit() else ""
        older.append({"verdict": verdict, "review": path, "at": at})
    return sorted(older + out, key=lambda d: d.get("at") or "")


def cmd_report(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    date, text = report_text(worktree, a.since)
    if a.write:
        prof = profile(worktree)
        path = worktree / reports_dir(prof) / f"{date}.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relink(text, reports_dir(prof)))
        print(json.dumps({"written": str(path.relative_to(worktree)),
                          "next": next_cmd(loop_cmd("adopt", "--worktree", str(worktree)), "lead",
                                           "add the judgement, then land it")}))
        return
    print(relink(text, None), end="")


LINK_MARK = "\x1f"  # marks a link target the report wrote itself, so quoted text's links are never touched


def md_link(text: str, target: str) -> str:
    return f"[{text}]({LINK_MARK}{target})"


def relink(text: str, folder: str | None) -> str:
    """The report's own links (from `md_link`), with targets written from the repository root made relative to a
    file in `folder`, so they resolve where the file is opened; with no folder, left as they are. Links in quoted
    text (an owner's words, an assumption) aren't the report's, and stay as written."""
    def fix(m: re.Match) -> str:
        return f"]({os.path.relpath(m.group(1), folder) if folder else m.group(1)})"
    return re.sub(r"\]\(" + LINK_MARK + r"([^)\s]+)\)", fix, text)


def reports_dir(prof: dict) -> str:
    return f"{prof['evidence']}/build-reports"


def adoptable(prof: dict, worktree: Path, ref: str, p: str) -> str | None:
    """Why `adopt` won't land the path `p`, or None: it lands plan files, a first profile, and build reports."""
    plans, reports = prof["plans"] + "/", reports_dir(prof) + "/"
    if p == PROFILE_FILE:
        if file_at(worktree, ref, p) is not None:
            return (f"{p} differs from the one at {base_ref(prof)}; adopt doesn't land a changed profile on an existing "
                    "project: the lead commits and integrates it with git once the owner has agreed to it")
        return None
    if p.startswith(plans):
        return f"{p} is an acceptance record, which only the loop writes" if p.endswith("-ACCEPTED.json") else None
    if p.startswith(reports):
        return None
    return (f"{p} isn't a plan file under {plans}, a first {PROFILE_FILE} or a report under {reports}; commit and "
            "integrate it another way")


def building_begun(doc: dict, record: dict, held: dict, key: str) -> bool:
    """Whether building has started on a module: a milestone past `open`, a claim, a review or an acceptance."""
    return any(m.get("state") != "open" for m in doc.get("milestones") or []) or \
        any(e.get("claim") or e.get("reviews") or e.get("accepted") for e in (record.get("milestones") or {}).values()) or \
        any(k == key for k, _ in held)


def design_passed(record: dict) -> bool:
    """Whether a design review of the module has ever passed (or the owner or an adoption agreed its design). Until
    then its definitions are a draft, which the owed design review will judge. Once passed, a later DESIGN CHANGES
    doesn't make it a draft again, so the history counts as well as the latest verdict; a review that judged a plan
    which changed while it ran (`not_counted`) never counts."""
    return any(d.get("verdict") == "ok" and not d.get("not_counted")
               for d in [*(record.get("design_history") or []), record.get("design") or {}])


def draft_closed(worktree: Path, prof: dict, doc: dict, record: dict, key: str) -> str | None:
    """Why `adopt` may no longer authorise changed definitions on a module, or None while they're a draft: a design
    review has passed, or building has begun (a claim, review, acceptance, a milestone past open, or a run holding
    the module's lock)."""
    if design_passed(record):
        return "a design review of it has passed"
    sync_claims(worktree, prof)
    if building_begun(doc, record, claims(worktree), key):
        return "building on it has begun"
    if run_holder(Path(git_common_dir(worktree)) / "orchestrate", key) not in (None, os.getpid()):
        return "a run holds it"
    return None


class AdoptRace(Exception):
    """A module stopped being a draft between adopt's check and its landing."""


ADOPT_WHY = "revised before the module's design review passed; that review judges these definitions"


ASSUMPTION = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*)?Assumption:(?:\*\*)?\s*(.+?)\s*$", re.MULTILINE)


def assumptions(text: str | None) -> list[str]:
    """The readings a planner chose for the owner to overturn: each line of a plan's log that starts `Assumption:`
    (a list bullet or bold marker before it is fine). One line each; a reading continued on the next line is cut."""
    return [m.group(1) for m in ASSUMPTION.finditer(text or "")]


def plan_rel(prof: dict, stem: str) -> str:
    return f"{prof['plans']}/{stem}-PLAN.md"


def authorise_doc(doc: dict, record: dict, stamp: dict) -> None:
    """Records `doc`'s definitions as authorised in `record`. A milestone whose definitions changed loses its proof,
    since that proof proved something else, and goes back to open."""
    for m in doc["milestones"]:
        e = record["milestones"].get(m["id"])
        if e and e.get("definitions") == definitions(m):
            continue
        if e:
            reset_proof(m)
            if m.get("state") in ("in_progress", "claimed", "done"):
                m["state"] = "open"
        record["milestones"][m["id"]] = {"definitions": definitions(m), "reviews": (e or {}).get("reviews", []),
                                         "authorised": stamp,
                                         **({"owner_answers": e["owner_answers"]} if (e or {}).get("owner_answers")
                                            else {})}
    for gone in set(record["milestones"]) - {m["id"] for m in doc["milestones"]}:
        del record["milestones"][gone]


def adopt_problems(worktree: Path, prof: dict, ref: str, base: str, paths: list[str]) -> tuple[list[str], list[str],
                                                                                              dict | None]:
    """(why these files can't land as they stand, the modules whose changed definitions adopt will authorise, and a
    `next` for a refusal that has one). Refused: files adopt doesn't land, a done-when file that's invalid or grants
    what a plan can't, a file the tip changed since this worktree's copy was made (landing it would undo that
    change), changed definitions on a module where building has begun, and anything `ready` would then call
    invalid. While nothing has been built on a module, adopt is how an in-chat planner's changes land, so it
    authorises them as a `plan` would."""
    problems = [why for p in paths if (why := adoptable(prof, worktree, ref, p))]
    proj = project(worktree, prof, ref)
    sync_claims(worktree, prof)
    held = claims(worktree)
    authorise, adopted, refusal = [], [], None
    for p in paths:
        if adoptable(prof, worktree, ref, p):
            continue
        if base and file_at(worktree, ref, p) != file_at(worktree, base, p):
            problems.append(f"{p} changed at {base_ref(prof)} since this worktree's copy; rebase this worktree onto "
                            "it first, so landing doesn't undo that change")
        if not (p.startswith(prof["plans"] + "/") and p.endswith("-DONE.json")):
            continue
        if (here := file_here(worktree, p)) is None:
            continue
        stem = Path(p).name[:-len("-DONE.json")]
        key = stem.upper()
        try:
            doc = json.loads(here)
        except json.JSONDecodeError as e:
            problems.append(f"{p} isn't valid JSON: {e}")
            continue
        if found := validate(doc, key):
            problems += [f"{p}: {x}" for x in found]
            continue
        before = file_at(worktree, ref, p)
        if before is not None:  # an existing module: the file can change only as a planner may change it
            try:
                problems += [f"{p}: {x}" for x in delta_problems(json.loads(before), doc, "plan")]
            except json.JSONDecodeError:
                pass
        rec_text = show(worktree, ref, record_rel(prof, stem))
        design = file_here(worktree, f"{prof['plans']}/{stem}.md")
        entry_ = {"stem": stem, "doc": copy.deepcopy(doc), "problems": [],
                  "design": text_hash(design.decode() if design is not None else None)}
        if rec_text is None:
            entry_["record"] = adopt(doc, entry_["design"], unrecorded(worktree, prof, ref))  # as `ready` will
        else:
            record = json.loads(rec_text)
            changed = [m["id"] for m in doc["milestones"] if not authorised(m, record)]
            changed += [mid for mid in record.get("milestones", {}) if mid not in {m["id"] for m in doc["milestones"]}]
            closed = draft_closed(worktree, prof, json.loads(before) if before else {}, record, key) \
                if changed else None
            if closed:
                problems.append(f"{p}: changes the definitions of {', '.join(changed)}, and {closed}, so they're no "
                                "longer a draft: the change needs a planner turn (`plan`) or the owner (`owner scope`)")
                refusal = next_cmd(loop_cmd("plan", "--worktree", str(worktree), "--task",
                                            f"Re-plan {stem}: the changes in {p} that adopt refused"), "lead",
                                   f"{stem}'s definitions are no longer a draft ({closed}); a planner turn re-plans "
                                   "them, or the owner takes the edited file as the new scope",
                                   owner=owner_cmd("scope", stem, changed[0], str(worktree)))
                continue
            if changed:
                authorise.append(stem)
                authorise_doc(entry_["doc"], record, {"by": "adopt", "why": ADOPT_WHY})
            entry_["record"] = record
        proj[key] = entry_
        adopted.append(key)
    if not problems and adopted:  # `ready` must not call invalid what adopt lands
        for k, cycle in need_cycles(proj).items():
            proj[k]["problems"].append(f"its needs form a cycle: {cycle}")
        for key in adopted:
            step = next_step(key, proj, held, me(worktree))
            if step["status"] == "invalid":
                problems += [f"{proj[key]['stem']}: {x}" for x in step.get("problems") or []]
    return problems, authorise, refusal


def cmd_adopt(a: argparse.Namespace) -> None:
    """Lands plan files left uncommitted, or committed but not integrated, so `run` and `ready` can see them, with a
    first ORCHESTRATE.md and any build reports."""
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    if os.environ.get("ORCHESTRATE_ROLE"):
        raise SystemExit("error: adopt can't run inside a session the loop started; a planner's files land through "
                         "`plan`, and a builder's through `land`")

    def done_with(result: str, code: int = 0, **fields) -> None:
        print(json.dumps({"result": result, **fields}))
        sys.exit(code)

    try:
        ref = tip(worktree, prof)
    except TipError as e:
        done_with("FAILED", 1, detail=str(e), **({"next": e.next} if getattr(e, "next", None) else {}))
    drift = plan_drift(worktree, prof, ref)
    reports = folder_drift(worktree, reports_dir(prof), ref)
    unlanded = sorted(set(drift["uncommitted"]) | set(drift["unintegrated"]) | set(reports["uncommitted"]) |
                      set(reports["unintegrated"]))
    if a.paths:
        paths = []
        for p in a.paths:
            full = Path(p) if Path(p).is_absolute() else worktree / p
            paths.append(os.path.relpath(os.path.abspath(full), worktree))
        problems = [f"{p} has no change here that the integrated tip lacks" for p in paths
                    if p not in unlanded and not adoptable(prof, worktree, ref, p)]
    else:
        paths, problems = unlanded, []
    if not paths:
        done_with("NOTHING", detail=f"no plan file under {prof['plans']}, and no report under {reports_dir(prof)}, "
                                    f"differs from {base_ref(prof)}",
                  **profile_note(drift, prof),
                  next=next_cmd(loop_cmd("ready", "--worktree", str(worktree)), "lead", "see what's ready"))
    base = git(worktree, "merge-base", "HEAD", ref).stdout.strip()
    found, authorise, refusal = adopt_problems(worktree, prof, ref, base, paths)
    problems += found
    # Hold each module whose definitions adopt will authorise, so no run here starts on it while this lands; the
    # landing re-checks the records too, for a claim made from another clone meanwhile.
    for stem in authorise:
        if not run_lock(worktree, stem.upper()):
            who = run_holder_info(worktree, stem.upper())
            problems.append(f"{stem}: a run holds it{holder_text(who)}, so building on it has begun; the change "
                            "needs a planner turn (`plan`) or the owner (`owner scope`)")
    if problems:
        done_with("REFUSED", 1, files=paths, problems=problems[:20], **({"next": refusal} if refusal else {}))
    if authorise:  # a record, so a run turned away meanwhile can say who holds the module
        loop_register(worktree, "adopt", module=", ".join(authorise), task="adopt " + ", ".join(paths)[:70])

    def recheck(tree) -> None:
        for stem in authorise:
            rec_path, doc_path = tree / record_rel(prof, stem), tree / done_rel(prof, stem)
            record = json.loads(rec_path.read_text()) if rec_path.exists() else {}
            doc = json.loads(doc_path.read_text()) if doc_path.exists() else {}
            if why := draft_closed(worktree, prof, doc, record, stem.upper()):
                raise AdoptRace(f"{stem}: {why} since adopt checked it")

    # The files as they are here, landed through a clean checkout of the tip, as the loop lands its own records,
    # so nothing else in this worktree (other edits, other commits) goes with them.
    content = {p: file_here(worktree, p) for p in paths}
    ahead = not is_ancestor(worktree, "HEAD", ref)

    def put_back() -> None:
        for p, data in content.items():
            if data is None:
                (worktree / p).unlink(missing_ok=True)
            else:
                (worktree / p).parent.mkdir(parents=True, exist_ok=True)
                (worktree / p).write_bytes(data)

    # A worktree that isn't ahead of the tip gets its copies set back to HEAD first, so integration can fast-forward
    # the base branch even where it's checked out here; they come back from the tip, or are restored on failure.
    if not ahead:
        in_head = names(git(worktree, "ls-tree", "-r", "-z", "--name-only", "HEAD", "--", *paths))
        if in_head:
            git(worktree, "checkout", "--quiet", "HEAD", "--", *sorted(in_head))
        for p in set(paths) - in_head:
            git(worktree, "rm", "-q", "--cached", "--ignore-unmatch", "--", p)
            (worktree / p).unlink(missing_ok=True)

    def change(tree):
        recheck(tree)
        for p, data in content.items():
            if data is None:
                (tree / p).unlink(missing_ok=True)
            else:
                (tree / p).parent.mkdir(parents=True, exist_ok=True)
                (tree / p).write_bytes(data)
        return paths

    def authorise_change(tree):
        recheck(tree)
        written = []
        for stem in authorise:
            doc = json.loads((tree / done_rel(prof, stem)).read_text())
            record = json.loads((tree / record_rel(prof, stem)).read_text())
            authorise_doc(doc, record, {"by": "adopt", "why": ADOPT_WHY, "files": paths[:20], "at": now()})
            record.pop("planner", None)  # these definitions came from outside a planner turn
            write_json(tree / done_rel(prof, stem), doc)
            write_json(tree / record_rel(prof, stem), record)
            written += [done_rel(prof, stem), record_rel(prof, stem)]
        return written

    reports = sum(p.startswith(reports_dir(prof) + "/") for p in paths)
    plans = len(paths) - reports
    kinds = [x for x in (f"build report{'s' if reports > 1 else ''}" if reports else "",
                         f"plan file{'s' if plans > 1 else ''}" if plans else "") if x]
    message = a.message or f"Adopt {' and '.join(kinds) or 'plan files'}: " + \
        ", ".join(Path(p).name for p in paths)[:200]
    try:
        try:
            ok, landed = loop_write(worktree, prof, "_adopt", change, message, trailer=False)
        except AdoptRace as e:
            if not ahead:
                put_back()
            done_with("REFUSED", 1, files=paths, problems=[str(e)], next=refusal or next_cmd(
                loop_cmd("ready", "--worktree", str(worktree)), "lead", "nothing landed; see what changed"))
        if ok and authorise:  # a draft's revisions: no design review has passed and nothing has been built
            try:
                ok, detail = loop_write(worktree, prof, "_adopt", authorise_change,
                                        "orchestrate: authorise the adopted draft of " + ", ".join(authorise))
            except AdoptRace as e:
                ok, detail = False, str(e)
            landed = detail if ok else f"the files landed at {landed}, but their definitions weren't authorised " \
                                       f"({detail}), so `ready` will call them invalid; re-plan them with `plan`"
    except SystemExit:
        raise
    except BaseException:
        if not ahead:
            put_back()
        raise
    if not ok:
        if not ahead:
            put_back()
        done_with("FAILED", 1, files=paths, detail=landed)
    if ahead:
        here = (f"left as it was: this worktree has commits of its own, so rebase it onto {base_ref(prof)}, where "
                "the plan commits it shares drop out as already applied")
    elif git(worktree, "merge", "--ff-only", "--quiet", tip(worktree, prof, fetch=False)).returncode == 0:
        here = f"fast-forwarded to {base_ref(prof)}"
    else:
        put_back()
        here = (f"behind {base_ref(prof)}, with the adopted files still here as local changes (they match the tip); "
                "the fast-forward was refused by other local changes")
    done_with("ADOPTED", files=paths, commit=landed, worktree=here, **({"authorised": authorise} if authorise else {}),
              **profile_note(plan_drift(worktree, prof, tip(worktree, prof, fetch=False)), prof),
              next=next_cmd(loop_cmd("ready", "--worktree", str(worktree)), "lead", "see what's ready now"))


def settle_scoped(worktree: Path, prof: dict, rel: str) -> str:
    """After `owner scope` landed the owner's edited done-when file through the loop's own checkout, this worktree
    still holds the edit uncommitted. Sets it back and fast-forwards, so the tree is clean and on the tip; or says
    what's left when it can't."""
    try:
        ref = tip(worktree, prof)
    except TipError as e:
        return f"not updated: {e}"
    if not is_ancestor(worktree, "HEAD", ref):
        return (f"left as it was: this worktree has commits of its own; set {rel} back with `git checkout -- {rel}`, "
                f"then rebase onto {base_ref(prof)}")
    edited = file_here(worktree, rel)
    git(worktree, "checkout", "--quiet", "HEAD", "--", rel)
    if git(worktree, "merge", "--ff-only", "--quiet", ref).returncode == 0:
        return f"fast-forwarded to {base_ref(prof)}; {rel} here is now the scoped file at the tip"
    if edited is not None:
        (worktree / rel).write_bytes(edited)
    return (f"behind {base_ref(prof)}: other local changes refused the fast-forward, so your edit to {rel} is still "
            f"here uncommitted; `git checkout -- {rel}` and fast-forward once those are dealt with")


def owner_guard(worktree: Path, stem: str, verb: str) -> None:
    """What stands between an owner decision and a session that would record one itself: refused inside any session
    the loop started (ORCHESTRATE_ROLE), and while a run, review or plan holds the module or the planner. These stop
    mistakes and casual shortcuts, not a determined agent."""
    if os.environ.get("ORCHESTRATE_ROLE"):
        raise SystemExit(f"error: owner {verb} can't run inside a session the loop started; the lead records the "
                         "owner's decisions, from what the owner told it")
    folder = Path(git_common_dir(worktree)) / "orchestrate"
    for name, what in ((stem.upper(), f"a run, review or design review holds {stem}"), ("_plan", "a planner is running")):
        if (pid := run_holder(folder, name)) is not None:
            raise SystemExit(f"error: owner {verb} is refused while {what} (pid {pid}), so no session the loop started "
                             "can record a decision in the owner's name; run it once that has stopped")


def cmd_owner(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    stem = module_stem(worktree, prof, a.module)
    key, mid, verb = stem.upper(), a.milestone, a.action
    words = (a.text or "").strip()
    if not words:
        raise SystemExit(f"error: owner {verb} needs --text, the owner's words for this decision as they gave them")
    owner_guard(worktree, stem, verb)
    # what the loop records: the owner's words, when, and which verb. It can't tell who ran the command, so it
    # doesn't say; `report` lists every one, recorded in the owner's name, for the owner to check
    decision = {"action": verb, "milestone": mid, "words": words, "at": now(),
                **({"item": a.item} if getattr(a, "item", None) else {})}
    stamp = {"by": "owner decision", "words": words, "at": decision["at"]}
    out = {}

    def change(t):
        path, rec_path = t / done_rel(prof, stem), t / record_rel(prof, stem)
        try:
            doc = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError) as e:
            doc = {"unreadable": str(e)}
        if problems := validate(doc, key):
            if verb != "release":
                raise SystemExit("error: the done-when file at the tip is invalid: " + "; ".join(problems[:5]))
            if not rec_path.exists():  # nothing to record the release in; the claim is still dropped
                return []
        record = json.loads(rec_path.read_text()) if rec_path.exists() else record_in(t, prof, stem, doc)
        record.setdefault("decisions", []).append(decision)
        written = [record_rel(prof, stem)]
        if verb == "release":
            pass
        elif mid == "design":
            if verb != "accept":
                raise SystemExit("error: only `owner accept` applies to a design")
            design = (t / prof["plans"] / f"{stem}.md")
            if record.get("design"):
                record.setdefault("design_history", []).append(record["design"])
            record["design"] = {**stamp, "verdict": "ok", "hash": text_hash(design.read_text() if design.exists() else None)}
        elif verb == "answer":
            m = find(doc, mid)
            item = getattr(a, "item", None)
            if item and item not in {i["id"] for i in m["items"]}:
                raise SystemExit(f"error: {mid} has no item {item}")
            answer = {"text": words, "at": decision["at"], **({"item": item} if item else {})}
            entry(record, mid).setdefault("owner_answers", []).append(answer)
            out["answer"] = answer
            if m.get("state") == "blocked":  # the answer is what it was waiting for
                m["state"] = "open"
                m.pop("blocked", None)
                write_json(path, doc)
                written.append(done_rel(prof, stem))
                out["unblocked"] = True
        elif verb == "scope":
            new = load_done(worktree, stem, prof)
            if problems := validate(new, key):
                raise SystemExit("error: the edited done-when file is invalid: " + "; ".join(problems[:5]))
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
                    if settle_replans({"milestones": [was]}, {"milestones": [m]}, stem):
                        # the definitions its reviews failed are gone, so this scope is the re-plan
                        if m["id"] not in out.setdefault("replanned", []):
                            out["replanned"].append(m["id"])
                e = record["milestones"].get(m["id"]) or {}
                record["milestones"][m["id"]] = {"definitions": definitions(m), "reviews": e.get("reviews", []),
                                                 "authorised": stamp,
                                                 **({"owner_answers": e["owner_answers"]} if e.get("owner_answers")
                                                    else {})}
                merged.append(m)
            for gone in set(record["milestones"]) - {m["id"] for m in merged}:
                del record["milestones"][gone]
            scoped = {**{k: v for k, v in new.items() if k != "milestones"}, "milestones": merged}
            if scoped == doc:
                raise SystemExit(f"error: nothing changed: {done_rel(prof, stem)} here has the same definitions as the "
                                 "tip, so there's no scope to record. Edit it as the owner asked first")
            write_json(path, scoped)
            written.append(done_rel(prof, stem))
        else:
            m = find(doc, mid)
            e = entry(record, mid)
            if e.get("definitions") != definitions(m):
                raise SystemExit(f"error: {mid}'s definitions aren't authorised; settle them with `owner scope` first")
            if verb == "accept":
                m["state"] = "done"
                m.pop("blocked", None)
                e["accepted"] = {**stamp, "commit": head_commit(t)}
            elif verb == "rereview":
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
            elif verb == "unpark":
                if m.get("state") != "parked":
                    raise SystemExit(f"error: {mid} is {m.get('state')}, not parked")
                m.update(state="open", fails=0)
            write_json(path, doc)
            written.append(done_rel(prof, stem))
            if verb == "rereview":
                written += [str(p.relative_to(t)) for p in (t / prof["evidence"] / stem).glob(f"{mid}-review-*.md")]
        write_json(rec_path, record)
        return written

    ok, detail = loop_write(worktree, prof, key, change,
                            f"orchestrate: owner {verb} {stem} {mid}: {words.splitlines()[0][:80]}")
    if ok and verb in ("accept", "release") and mid != "design":
        drop_claim(worktree, prof, key, mid)
    if ok and verb == "scope":
        out["worktree"] = settle_scoped(worktree, prof, done_rel(prof, stem))
        if out.get("replanned"):
            out["replanned_why"] = (f"{', '.join(out['replanned'])} {'was' if len(out['replanned']) == 1 else 'were'} "
                                    "owed a re-plan; this scope replaced the definitions its reviews failed, so it "
                                    "counts as the re-plan: fails 0, one more replans, state open")
    if ok and verb == "answer":
        out["next"] = next_cmd(loop_cmd("run", "--module", stem, "--worktree", str(worktree)), "lead",
                               f"the answer is in the record; the resumed builder is told to read it there "
                               f"({record_rel(prof, stem)}, milestones.{mid}.owner_answers)")
    print(json.dumps({"result": ("RELEASED" if verb == "release" else "DONE") if ok else "FAILED", "action": verb,
                      "module": stem, "milestone": mid, "detail": detail, **out}))
    sys.exit(0 if ok else 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def host_args(p):
        p.add_argument("--host", help="codex, claude, or a host named in the profile (default: see above)")
        p.add_argument("--model", help="default: the profile's model for this kind of agent on the host, "
                                       "else its model for the host")
        p.add_argument("--effort", help="default: medium (high for planners), or the profile's Effort")
        p.add_argument("--turn-timeout-hours", type=float, default=2.0)

    run = sub.add_parser("run")
    run.add_argument("--module", required=True)
    run.add_argument("--worktree", required=True)
    run.add_argument("--milestone")
    run.add_argument("--fresh", action="store_true", help="start a new session even if one exists")
    run.add_argument("--message", help="first prompt on resume, e.g. the reviewer's findings message")
    run.add_argument("--owner-rule", action="append", help="a restriction the owner gave in conversation; stored "
                     "with the module's run state and restated every turn, across --fresh and milestones")
    run.add_argument("--clear-owner-rules", action="store_true", help="drop stored owner rules (when the owner says)")
    run.add_argument("--budget-hours", type=float, default=4.0)
    run.add_argument("--no-design-review", action="store_true", help="return DESIGN_OWED instead of running the "
                     "owed design review first")
    run.add_argument("--review-host", help="the host for the owed design review run starts itself (default: the "
                     "profile's Review host, `other` meaning the host the planner turn that wrote the plan isn't on, "
                     "or the builder isn't on when the loop doesn't know the planner; else the builder's host)")
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
    adopt_p = sub.add_parser("adopt")
    adopt_p.add_argument("--worktree", default=".")
    adopt_p.add_argument("--message", help="the commit message (default: names the files)")
    adopt_p.add_argument("paths", nargs="*", help="plan files to land (default: every unlanded one)")
    adopt_p.set_defaults(func=cmd_adopt)
    pause = sub.add_parser("pause")
    pause.add_argument("--module")
    pause.add_argument("--worktree", default=".")
    pause.set_defaults(func=cmd_pause)
    owner = sub.add_parser("owner", help="record a decision the owner gave the lead in chat")
    owner.add_argument("action", choices=["accept", "rereview", "unpark", "scope", "release", "answer"])
    for flag in ("--module", "--milestone", "--worktree"):
        owner.add_argument(flag, required=True)
    owner.add_argument("--text", "--reason", dest="text", required=True,
                       help="the owner's words for this decision, as they gave them")
    owner.add_argument("--item", help="answer: the attended item the answer is for")
    owner.set_defaults(func=cmd_owner)
    quota = sub.add_parser("quota")
    quota.add_argument("--worktree", help="also forecast this repository's open milestones")
    quota.add_argument("--budget", type=float, default=120.0, help="seconds to spend reading rollouts")
    quota.add_argument("--json", action="store_true", help="the full report, as JSON")
    quota.set_defaults(func=cmd_quota)
    prof = sub.add_parser("profile")
    prof.add_argument("--worktree", default=".")
    prof.add_argument("--host", help="also check that host's loader (default: see above)")
    prof.set_defaults(func=cmd_profile)
    check = sub.add_parser("check")
    check.add_argument("--module", required=True)
    check.add_argument("--milestone", required=True)
    check.add_argument("--worktree", default=".", help="the tree to run the checks in (default: here)")
    check.add_argument("--plans-from", help="the worktree whose done-when file to read (default: --worktree)")
    check.add_argument("--timeout", type=float, default=600.0, help="seconds per check")
    check.add_argument("--json", action="store_true", help="the full result, as JSON")
    check.set_defaults(func=cmd_check)
    cost = sub.add_parser("cost")
    cost.add_argument("--worktree", default=".")
    cost.add_argument("--module", help="only this module")
    cost.add_argument("--since", type=float, help="only the last this many hours")
    cost.add_argument("--json", action="store_true")
    cost.set_defaults(func=cmd_cost)
    report = sub.add_parser("report")
    report.add_argument("--worktree", default=".")
    report.add_argument("--since", type=float, default=24.0, help="hours to cover (default 24)")
    report.add_argument("--write", action="store_true", help="write <evidence>/build-reports/<date>.md for adopt")
    report.set_defaults(func=cmd_report)
    loops = sub.add_parser("loops")
    loops.add_argument("--repo", help="only loops in the repository holding this path")
    loops.add_argument("--json", action="store_true", help="one JSON object, for a lead")
    loops.set_defaults(func=cmd_loops)
    lock = sub.add_parser("lock")
    lock.add_argument("--worktree")
    lock.add_argument("name")
    lock.add_argument("command_args", nargs=argparse.REMAINDER)
    lock.set_defaults(func=cmd_lock)
    args = parser.parse_args()
    if getattr(args, "worktree", None) and args.func is not cmd_quota:
        QUOTA_WORKTREE[:] = [Path(args.worktree).resolve()]
    try:
        args.func(args)
    except WriteBlocked as e:
        stop_on_write(args, e)
    except OSError as e:  # the loop's own files under .git: its locks, run state and clean checkouts
        if e.errno not in (errno.EPERM, errno.EACCES, errno.EROFS):
            raise
        stop_on_write(args, WriteBlocked(e.filename, e.strerror or str(e)))


def stop_on_write(args: argparse.Namespace, e: WriteBlocked) -> None:
    """One result line for a write the sandbox refused or a lock someone holds, naming the path and the fix."""
    again = shlex.join(["python3", str(LOOP), *sys.argv[1:]])
    if args.func is cmd_land:
        print(json.dumps({"result": "FAILED", "detail": e.reason(), "blocked_write": e.fields()["blocked_write"]}))
    else:
        print(json.dumps({"result": "FLOOR", **e.fields(), "next": next_cmd(
            again, "lead", "the lock is held; run the command again once it's free" if e.held else
            "run the same command outside the sandbox, or with escalation")}))
    sys.exit(1)


if __name__ == "__main__":
    main()
