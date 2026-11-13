#!/usr/bin/env python3
"""Drives builders, reviewers and planners for the orchestrate process on any supported agent host, with model and
effort named at every launch, and decides itself which work is accepted.

Used by the `build` lead (on any host that can run shell commands) and runnable by hand. Project settings come from
ORCHESTRATE.md at the worktree root (`settings` prints what was read). Needs git, plus the CLI of each host it
launches. POSIX only (fcntl, process groups).

Hosts:
  codex    `codex exec`, resumable, with goals, pinned-turn checks and a quota forecast from Codex's local files.
  claude   `claude -p` with stream-json, resumable, launched with no API key in its environment so it uses the
           signed-in plan. Reviewers and planners use the installed orchestrate agent files when present.
  <name>   any other CLI, from a `- **Host <name>:** <command>` line in the project settings, with {prompt}, {model}, {effort}
           and {cwd} placeholders. Each turn is a fresh process; the files carry state between turns.
  With no --host, the host is the settings' `Default host`, else the host this command runs inside, else the only
  one installed, else codex.

  Sessions run headless as above by default, so nothing opens in either app. With ORCHESTRATE_VISIBLE=1, on a Mac
  with the Codex app or Claude desktop running, codex and claude sessions are ones the app lists under the project,
  where the owner can watch, steer, pause (Stop) and take over; the script still drives and checks every turn. Codex
  threads then run in the app itself, and each new thread brings the app to the front. Claude turns run in the script's
  own signed-in `claude -p`, imported into the Code tab. When the app can't take them (another OS, app not installed
  or not running, Claude CLI signed out), they run headless. Every result line from a turn says which: `path` is
  `visible` or `headless`, with `path_reason` when headless. Stopping a turn in the app gives PAUSED, and `run` again
  carries on.

Where the plans live. The settings' `Plans` line names the plans folder (default docs/plans; a project with no
Plans line, no docs/plans and a docs/modules folder keeps docs/modules). Each module has a folder of its own there:
  <plans>/<MODULE>/DESIGN.md      the planner's design
  <plans>/<MODULE>/PLAN.md        the milestones as they stand now, with open assumptions under `## Open for the owner`
  <plans>/<MODULE>/LOG.md         short dated entries: what changed and why
  <plans>/<MODULE>/DONE.json      the done-when file; a folder with one is a module
  <plans>/<MODULE>/ACCEPTED.json  the record, which only the script writes
  <plans>/<MODULE>/BRIEF.md       a feature brief, when the module has one
The project's own files sit beside the folders: BRIEF.md, GLOSSARY.md, ARCHITECTURE.md (which opens with the module
table, `| # | Module | What it's for | Needs |`, in build order) and STATUS.md, the owner's page, which the script writes
after each record it merges and nobody edits. Plans still in the older flat layout (<MODULE>-DONE.json and the rest
side by side in the plans folder) stop every command until `migrate` has moved them.

What the script owns. In each module's folder it keeps ACCEPTED.json, which only the script writes and
which is committed, so every worktree, clone and lead sees the same thing. Per milestone it holds the authorised hash
of the acceptance definitions, the Ready for Review record the script checked (code commit and the main branch's tip it ran the checks on),
the reviews that judged it, and whether it was accepted, by checks, a reviewer or the owner. It also holds the
module's design review. A milestone is finished only when the record accepts it with its current definitions; a
`done` state in the done-when file isn't enough. A module with no record yet has its definitions authorised and
nothing accepted, with its design review owed. Only in a repository that has never had a record file is a module
adopted as it stands, finished milestones accepted; the script's first record-keeping commit writes those records.

The script reruns checks with your own permissions, outside any host's sandbox, in a clean checkout of the main
branch's tip. It pins the check strings, but a script a check calls can still be changed by the builder, so review new check
scripts.

Subcommands:

  run   --module CORE --worktree PATH [--host H] [--model M] [--effort E] [--milestone M2] [--fresh]
        [--message TEXT] [--owner-rule TEXT]... [--clear-owner-rules] [--budget-hours 4] [--no-design-review]
        [--review-host H] [--checks-only]
        Starts (or resumes) a builder session on the module's next milestone and drives it one turn at a time until:
        READY_FOR_REVIEW  the script checked the milestone and set it to Ready for Review: the done-when file is
                      valid and only the builder's own fields changed, every item is `pass` with evidence, the tree
                      is clean, HEAD is on the main branch's tip (fetched fresh), and the test command and every
                      item's `check` exit 0 in the script's clean checkout of that tip, run in this process, outside
                      the builder's sandbox and the merge lock (a check that already passed on the same files isn't
                      run again; `reused_checks` lists those). Only then does the script write the record and set
                      the state, `ready_for_review`, or `done` when no review is needed, in one commit. The builder
                      leaves the state in_progress, and `merge` refuses a commit that sets it. `review` says whether
                      a reviewer must judge it, `commit` is the builder's commit and `checked` the tip the checks ran
                      on. A milestone that needs no review is accepted there and then. `next` is the review command
                      on the review host, or, with no review owed, `run` for the next milestone. Before any turn,
                      `run` checks a milestone whose work is already merged with every item passing, and after a
                      turn it waits for a `merge` the builder left running as a background job.
        BLOCKED       the milestone can't move until someone steps in. The script records `state: blocked` and a
                      `blocked` object, {reason, items?, what}, and the result carries `reason` and `blocked`. The
                      reason is the one the builder's last line named (`BLOCKED needs_access: ...`); with none, items
                      that need someone decide it once every other item passes, and otherwise it is needs_context
                      (also the reason for a builder's `NEEDS_CONTEXT: ...` ending). A run that isn't visible stops
                      BLOCKED needs_access or needs_hardware by itself once only such items are open, and its `next`
                      is the same `run` with ORCHESTRATE_VISIBLE=1, for when the owner is at the machine; a visible
                      run on a milestone blocked that way unblocks it and builds.
        CHECKS_FAILED the agent said DONE (or its goal completed) three times without the work holding up
        INVALID       the done-when file is malformed, or something outside the builder's fields changed
        REVIEW_OWED   the module's next milestone is Ready for Review, with the script's record, and waiting for its
                      review. One that is Ready for Review without the record is checked by `run` instead
        WAITING       `reason` on_dependency: the next milestone depends on milestones in other modules that aren't
                      Done yet (`depends_on` lists them). `reason` for_replan or for_diagnosis: it failed review four
                      times on a repeated finding, or six times in all (`ladder` replan or diagnose); `next` is the
                      planner's task, and no builder starts on it until the planner has changed its definitions or,
                      for a diagnosis, kept them
        DESIGN_NOT_APPROVED
                      the module's design hasn't passed a design review (or changed since it did). Unless
                      --no-design-review, `run` first runs that review itself, as `review --milestone design` would
                      with the same --effort, on the review host (--review-host, else the settings' `Review host`,
                      else the builder's host; --model only when that is the builder's host), and on DESIGN OK goes
                      on to build; any other outcome stops here with the review's result under `design_review`.
                      After DESIGN OK, every later result of the run carries `design_review` (verdict, host, model,
                      review file and its `usage`), so the review's cost shows with the build's
        FINISHED      the module has nothing left
        TAKEN         another lead or run holds this module or milestone; `by` and `holder` say which (pid, role,
                      worktree, since when) where the records show it
        NO_PROGRESS_FOR_HOURS
                      no new passing item, and no commit of the builder's own outside the plans folder, for
                      --budget-hours
        STALLED       three turns in a row changed nothing and reported nothing (progress updates); the two
                      continuations between them named the open items
        HOST_FAILED   two failed turns in a row, the host CLI is missing, or the goal is usage- or budget-limited
                      (likely quota, sign-in or outage)
        SCRIPT_FAILED the script couldn't do a step of its own: fetch the main branch's tip, make its checkout,
                      write a file the sandbox refused, record that a milestone is Ready for Review, or unblock
                      a milestone
        WRONG_MODEL_OR_EFFORT
                      a turn ran on a model or effort other than the named ones
        PAUSED        `pause` stopped it, the owner stopped it or has it open in the app, or the Codex goal is
                      paused; `run` again carries on (re-activating a paused goal on a visible thread)
        A run on the same milestone resumes its session (with --message as the first prompt, e.g. the reviewer's
        findings) unless --fresh is given or the host, model or effort changed. A new milestone starts a new session.
        --milestone only confirms which milestone you expect; it never skips one that comes first.
        --checks-only starts no agent: it runs the script's checks on a milestone whose work is merged with every item
        passing, and prints READY_FOR_REVIEW, or CHECKS_FAILED with `reasons`. A builder in a chat with no lead uses it.
        Each resumed turn restates the goal and what binds the builder (its fields, `merge`, the test command, the
        settings' `Licences and paths not to touch` and `Owner decides` lines, items that need someone, owner rules), except
        on a Codex thread whose goal is active, which gets only the owner rules; `goal` in the result says which, and `constraints_missing` names settings lines that
        weren't there to restate. Ready for Review records and reviews record the requested host, model and effort, the CLI's
        version, under `observed` only what the host's own output showed, and under `usage` the tokens its headless
        turns reported (input not read from cache, cache reads, output, and Claude's list-price estimate for that
        turn, taken as the rise in the session's cumulative total), with
        `incomplete_turns` counting turns that showed no tokens (a visible Codex turn) or only some (a Claude turn
        stopped before its result event, counted from its messages). A result line's `usage` is the session's
        running total. A Ready for Review record's `usage` is what the session spent since its previous one, so a
        milestone's records add up; `session_usage` beside it is the running total, not to be added.
        Every result that stops short of building (WAITING, DESIGN_NOT_APPROVED, REVIEW_OWED, BLOCKED, INVALID,
        HOST_FAILED, SCRIPT_FAILED, TAKEN) carries `next`: {command, by, why}, the exact command to run next. Its `--worktree` is the one
        the command producing it was given, so a `next` from `ready` or `status` run in the main checkout names the
        main checkout. A `run` or design `review` in any `next` (and in `ready`'s and `next`'s) gets the host and
        review host of that module's latest build run on this machine (<git common dir>/orchestrate/last-runs.json,
        written when a build turn starts) where the command names none; with `Review host: other` only a review host
        the lead named on that run is kept, and a design review owed after a planner turn names the host that
        didn't plan it. A milestone review's host is left to
        `review`, which takes the builder's from the Ready for Review record. `by` names who runs
        `command` (lead or planner). `decides: owner` marks a decision only the owner may make: `ask` is what the
        lead asks them in chat, and `command` the `owner` command the lead runs once they've replied, with their
        words in --said (feedback) or --text; the script never runs those itself. For Blocked: Needs Human Feedback,
        `next` is `owner feedback` naming the blocked items, and `ask` shows each item, what it needs judged and
        its evidence. Items that need access or hardware never get a reply recorded. When plan
        files under the settings' plans folder are uncommitted or not merged, the result names them under
        `unmerged_plans` and `next` is `adopt`, with what would have come next under `then`.
        A project with no ORCHESTRATE.md gives INVALID with `next` naming `plan`.
        Prints one JSON line with the result as the last line of output. Its `warnings` are the launch's loader
        checks for the resolved host and binary (an AGENTS.md that Claude won't read, a skill not installed where
        the host finds skills by name); they never stop a run.

  review --module CORE --milestone M2 --commit SHA --worktree PATH [--host H] [--model M] [--effort E]
        Runs a fresh reviewer in a clean checkout of the commit that is Ready for Review (or of the main branch's tip, with --milestone
        design), then checks what it did: only the review file and the reviewer's own fields changed, the verdicts
        agree with its last line, and a fail added 1 to `fails`. If all holds, the script merges the review itself,
        sets failed items back to open, and records the verdict. An earlier round's review is kept beside the new
        one as <milestone>-review-N.md (reusing `owner rereview`'s copy of the same text), and its record entry
        points there; entries overwritten before rounds were kept say `review_in_history`. Captures go in the folder beside the review file
        (<evidence>/<MODULE>/<milestone>-review/), which merges with it. REVIEWED, INVALID (nothing merged), or the host's
        HOST_FAILED, SCRIPT_FAILED, WRONG_MODEL_OR_EFFORT or PAUSED. With no --host, a review goes to the settings' `Review host` (`other` means the host
        that built the milestone swapped, or for a design review the host of the planner turn that wrote the plan
        swapped, else the settings' default host swapped). REVIEWED's `next` is the
        {command, by, why}. After a failed milestone review `rounds` counts its failed reviews since the last
        re-plan, diagnosis or owner decision, `fails` those with a finding that repeated an earlier round's
        (`repeated` names them), and `ladder` (and `next.ladder`) is the escalation word (same-session,
        fresh-session, replan, diagnose, too_many_failed_reviews) with `next` the command it calls for: `run
        --message` with the findings, `run --fresh --message`, `plan` with a re-plan or diagnosis task naming the
        reviews (by: planner), or `owner reopen` (decides: owner, with each round under `history`) for a milestone
        the script blocked with too many failed reviews.
        A diagnosing planner ends with `PLANNED` (a re-plan) or `KEEP <MODULE> <milestone>: builder|reviewer|owner:
        <why>`, which `plan` records as KEPT, starting the counts again; `owner` there, or a second diagnosis,
        blocks it with too many failed reviews. After a pass it is the
        next ready milestone or "finished", the planner's revision with `findings` after DESIGN CHANGES.
        A second design review keeps the first as design-review-N.md, and its prompt names the done-when items
        added, removed or redefined since the first.

  plan  --worktree PATH --task TEXT [--host H] [--model M] [--effort high]
        Runs a fresh planner in the script's own checkout of the main branch's tip (<git common dir>/orchestrate/verify/
        _PLANNER), so --worktree only names the repository and the lead's worktree is left as it is; a first plan,
        before ORCHESTRATE.md exists, runs in --worktree itself, which must be clean. Its last line must be `PLANNED`, after changing files
        (a DESIGN.md in the folder of every changed done-when file), else it's nudged with what's missing, at most
        twice; PLANNED's `files` lists what it changed. Then the script checks its done-when files, commits and merges its files, and authorises the new
        definitions (resetting proof on milestones whose definitions changed). PLANNED lists the modules whose
        design review is now owed. BLOCKED or NEEDS_CONTEXT from the planner, or UNFINISHED, merges nothing; the
        files it changed are listed under `set_aside` and kept in a stash (`stash`), and any commits on a branch
        (`branch`), since the planner's checkout is reset for the next plan. Its `report` keeps the end of the planner's message (where owner decisions go),
        up to 6000 characters. PLANNED's `next` is the owed design review on the review host, or `ready`;
        `assumptions` counts, per module, the `Assumption:` lines in its PLAN.md. The whole task is kept in the plan
        commit's body and in each module's record file under `briefs` (the authorisation stamps name only its
        first line), which design reviews are pointed at. For each
        milestone that was owed a re-plan or diagnosis and whose definitions the plan changed, the script sets fails
        and rounds 0, adds 1 to replans (and to diagnoses, for a diagnosis) and sets it not_started, in its own commit, whatever the planner wrote there (`replanned` lists them). In a
        repository with no commits (or origin with no main branch), SCRIPT_FAILED before any planner turn, with `next`
        giving the first commit and push. One planner runs per repository at a time: another waits for it (listed in
        `runs` with `waiting_for`), then plans from the tip the first one merged; `pause` doesn't reach a waiting
        planner, but stopping its process does (PAUSED). The script merges only what the planner leaves uncommitted: a
        turn whose checkout's reflog shows a commit made during it, or whose HEAD the tip lacks, is INVALID (`next` by lead, no
        command), and so is one during which a commit
        without the script's trailer changed an record file on the tip (named, `next` decides: owner, no command). Its
        HEAD may move along the tip meanwhile (a `merge` elsewhere fast-forwards the checkout holding the base
        branch). Everything it leaves uncommitted merges, outside the plans folder too (acceptance tests, say), except
        record files. Any other INVALID turn's files are stashed, and its `next` gives a planner the task again
        with the problems. The whole task is kept once, under `briefs`. A review is refused the same way when a
        record changes on the tip without the trailer while it runs, or its checkout's reflog shows a commit. `merge` refuses to run in a plan or review
        session.

  merge --worktree PATH [--no-check]
        Merges the worktree's commits under the merge lock: rebase onto the base, run the test command, then push
        (Merge: push) or fast-forward the local branch (Merge: local). Builders use this. MERGED or FAILED. It
        refuses (FAILED) commits that set a milestone's state to ready_for_review or done, which only the script
        sets, after its checks; the items' checks don't run here, so they never hold the merge lock.

  ready [--worktree PATH]       What each module's next milestone is waiting for, read at the main branch's tip. When
        nothing is ready it adds `next`. A milestone Waiting for a re-plan or diagnosis, or Blocked with too many
        failed reviews, carries its own `next` (the planner's or the owner's command), never as ready. `plan_ahead`
        lists the module table's modules with no plan yet whose Needs are all planned, in build order, each with
        the `plan` command in its `next`. It names unmerged plan files (`unmerged_plans`) as `run` does, and
        `settings_differ` when ORCHESTRATE.md here differs from the tip's. With no ORCHESTRATE.md it gives `unplanned`
        and `next` naming `plan`, or, when the main branch's tip does have one, `behind` and `next` naming the merge
        that brings this worktree up to it.
  adopt [--worktree PATH] [--message TEXT] [PLAN FILE]...
        Commits plan files that are uncommitted, or committed here but not merged, and merges them through a
        clean checkout of the tip, as the script merges its own records, so nothing else in the worktree goes with them.
        Also merges a first ORCHESTRATE.md (one the tip doesn't have yet) and reports under <evidence>/build-reports/.
        A module's definitions are a draft until a design review of it passes. While they are, and nothing has been
        built (no Ready for Review record, review or acceptance, no milestone past not_started, no run holding the module), adopt authorises
        changed definitions (`authorised` lists the modules; the record's stamp says why), because the owed design
        review will judge them; it holds the module's run lock while it merges and checks again before each commit.
        Refuses files outside those, record files, a hand-edited STATUS.md, files under the old flat names,
        a PLAN.md or LOG.md that fails the plan checks (as a planner turn's merging does), invalid done-when files, changed definitions on a module
        that's no longer a draft (with `next` naming `plan` and `owner scope`), a changed ORCHESTRATE.md the tip
        already has (the lead commits it once the owner agrees), anything `ready` would then call invalid, files the tip changed since,
        and any session the script started. While it merges it has a `runs` record, so a run turned away names it.
        ADOPTED, NOTHING, REFUSED or FAILED (with `next` when the repository has no commits to build on).
  status [--module CORE] --worktree PATH [--format md]   Every milestone with its state, blockers and last verdict,
        and which modules (and the planner) have a live run. A milestone the script hasn't checked yet shows as `done,
        unchecked`. It warns about a module folder with no row in ARCHITECTURE.md's module table (`ready` lists the
        same under `module_table`), and about tracked PLAN.md or *-PLAN.md files outside the plans folder.
        --format md prints STATUS.md, the owner's page, as the script writes it after each record it merges (in a
        commit of its own, which never fails or holds up the record), plus any plan files here that haven't merged.
        The page opens with an overview (a progress line, what waits on the owner, what is under way or next, and
        what was accepted in the last 7 days), then every module in build order with its status.
  migrate --worktree PATH [--to docs/plans]
        Moves plans from the old flat layout into a folder per module: <M>.md to <M>/DESIGN.md, <M>-PLAN.md to
        <M>/PLAN.md, and <M>-DONE.json, <M>-ACCEPTED.json and <M>-BRIEF.md into <M>/, with each plan's `## Log`
        section moved to <M>/LOG.md. --to also moves the whole plans folder there and changes the Plans line in
        ORCHESTRATE.md. In the same commit it brings the project to the names of 2.0: the settings lines `Check:`
        and `Integrate:` become `Test command:` and `Merge:`; in each DONE.json the states open, claimed and parked
        become not_started, ready_for_review and blocked (too_many_failed_reviews), a text `blocked` becomes
        {reason: needs_context, what}, a milestone's `needs` list becomes `depends_on`, an item's `attended`
        becomes `needs` ({type: human_feedback, or hardware when it names a device, what}), cant_tell becomes
        could_not_judge and a `proxy:` target `stand_in:`; in each ACCEPTED.json `owner_answers` {text, item}
        becomes `human_feedback` {asked: null, said, items, at} and `parked` becomes `too_many_failed_reviews`.
        Each stored definitions hash the rename alone changed is re-stamped, so nothing reads as changed outside a
        planner turn. Every other command refuses a project with the old names, naming `migrate`. It works on a clean checkout of the tip and merges as the script's own commit, then
        fast-forwards a clean worktree. Acceptance survives: records hold no plan paths, and a design's hash is of
        its text. Refused while any run, review, plan or adopt is running, and while plan files here differ from the
        tip, unless the tip is migrated already, when it changes nothing and needs no run stopped. MIGRATED
        (`renamed` lists the files given the new names), NOTHING (the tip has folders and names already), REFUSED
        or FAILED. Either success lists in `worktrees_on_old_names` every worktree whose files still use the old
        layout or names, each with its `migrate --branch` command.
  migrate --branch --worktree PATH [--module CORE]
        For a worktree whose own commits were made before the main branch was migrated, which `run` refuses:
        renames each of its commits as `migrate` renamed the main branch, then rebases them onto the tip, so the
        rebase meets no conflict in a file the renames changed. It holds only the module's run lock (the module its
        run state names, else the one whose files its commits changed, else --module), so other modules' runs
        carry on. The worktree must be clean. MIGRATED (`commits` renamed, `was` the old HEAD, `renamed` the files),
        NOTHING (its commits use the new names already; a clean worktree behind the tip is fast-forwarded), REFUSED
        (the tip isn't migrated, the worktree has uncommitted changes or merge commits, a run holds the module, or
        the builder's commits conflict with the main branch's own changes, named in `conflicts`; the worktree is
        then left as it was) or FAILED.
  check --module CORE --milestone M2 [--worktree PATH] [--plans-from PATH] [--timeout 600] [--items-only] [--json]
        Runs the milestone's checks (each item's `check` under its `lock`, then the test command, which
        --items-only leaves out, for a planner trying its checks while builders work) in the given tree, as it stands,
        and prints a line per check, with the why and last output lines of any that didn't pass (--json: one JSON
        object with everything): per check `pass`, `fail` (it ran and failed: likely not built yet; the output says),
        `error` or `timeout`, with the exit code and the output's tail. `error` means the check can't run as
        written, and is given only where that's certain: it doesn't parse as shell, or exit 126. Its fix is to how the
        check is written, never to what it tests. Exits 0 only when every check passes. Writes nothing in the
        repository. Each check's whole stdout and stderr is saved under <git common dir>/orchestrate/checks/ (`stdout`
        and `stderr` in --json), and a pass is remembered by the files it ran on (leaving out the plans folder) and its
        command, so `merge` and `run` don't run it again on the same files (`reused`).
  cost [--module CORE] [--since HOURS] --worktree PATH [--json]
        Tokens per milestone from this machine's usage ledger (<git common dir>/orchestrate/usage.jsonl), which
        every turn the script runs appends to, paused ones too: planning, then each milestone's build and review
        (a design review under milestone `design`), with totals and how many turns showed no tokens or only some.
        A milestone the ledger has nothing on (a clone, or a project built before the ledger) is read from the
        `usage` its Ready for Review records and reviews carry in the committed record file, and marked as from the record.
  report [--since 24] --worktree PATH [--write]
        The factual half of the lead's report: what closed, the verdicts with links (every design review in the
        window, DESIGN CHANGES ones included), every decision recorded in the owner's name with their words (for the
        owner to spot one they didn't make), the planner turns that authorised definitions with the task each
        was given (where the lead puts the owner's words), the planners'
        assumptions (lines starting `Assumption:` in each <plans>/<MODULE>/PLAN.md) for the owner to overturn, what is
        blocked or waiting, the open items that need human feedback, access or hardware, and cost (as `cost` reads it). --write puts it in
        <evidence>/build-reports/<date>.md for `adopt`, with its links relative to that file.
  next  --module CORE --worktree PATH --milestone M2   The escalation after a failed review (see done-when.md):
        read at the main branch's tip, where the review merged. `action` is the ladder's word, `message` what to send (the builder's findings, or for `replan` and
        `diagnose` the planner's task), and `next` the command.
  unblock --module CORE --milestone M2 --worktree PATH   Puts a blocked milestone back in the queue, in_progress.
        Refused for Needs Human Feedback (`owner feedback` unblocks it) and Too Many Failed Reviews (`owner reopen`).
  pause [--module CORE] --worktree PATH   Stops the runs in this repository, and their agents, cleanly.
  owner accept|rereview|reopen|scope|release --module CORE --milestone M2|design --worktree PATH --text TEXT
  owner feedback --module CORE --milestone M2 [--item M2.3]... --worktree PATH --asked TEXT --said TEXT
        Records a decision the owner made in chat; the lead runs it, with the owner's words in --text (--said for
        feedback, where --text also works) as they gave them. Every verb records those words, when, and which verb, under `decisions` in the module's record (the
        script can't tell who ran it, so it doesn't say), and `report` lists them all. Refused inside any session the
        script started (ORCHESTRATE_ROLE set: Claude's environment, and Codex's shell through shell_environment_policy,
        confirmed headless and unconfirmed in the app) and while a run, review or plan holds the module or the
        planner. These stop mistakes and casual shortcuts, not a determined agent. `feedback` records Human
        Feedback, {asked, said, items, at}, under `human_feedback`, for items whose `needs.type` is human_feedback
        (by default the blocked items, else every open one); it is refused for an item that needs access or
        hardware, which is done at the machine and never recorded. It puts a milestone Blocked: Needs Human
        Feedback back in the queue; the resumed builder is told to read it there, oldest first, and the reviewer
        counts it as the owner's words. `release` takes a milestone out of In Progress when the lead that started it is gone. `scope` takes the done-when file as edited in the
        worktree (refused, saying nothing changed, when it matches the tip), leaves the worktree clean on the tip where it can, and says under `worktree` what to do where it
        can't. A `scope` that changes a milestone owed a re-plan is the re-plan: fails 0, one more replans, state
        not_started, listed under `replanned` with `replanned_why`. `reopen` takes a milestone Blocked with too many
        failed reviews back to in_progress, with fails, rounds and diagnoses 0.
  quota [--worktree PATH] [--budget 120] [--json]
        A short readout leading with the verdict, saying whose use each figure counts; --json gives everything.
        The weekly Codex limit, read from Codex's local rollouts by codex_quota.py beside this file: burn per active
        hour (idle time excluded) and per builder-hour by model and effort, a tokens-to-percent fit with its range, what
        each milestone of this repository cost (its turns and rounds; runs in other repositories count only as the
        machine's orchestrate use), the script's own use apart from other local threads and from usage
        no local rollout explains, and a forecast of the open milestones against what's left before the reset, with a
        one-sentence verdict. Every result line carries a short `quota` field: the rate (what's left, hours to the
        reset, %/h, what's left at the reset), used, reset, recent burn, the verdict,
        `warn` (only when the quota won't last) and `runs_out` when one builder at the usual pace would use it up.
        Reading is cached and capped at two seconds on a result line; a first, cold read finishes here. Only result
        lines from a run that launched or meant to launch Codex carry `quota`.
  settings --worktree PATH [--host H]   Prints the project settings read from ORCHESTRATE.md, or exits 1 naming what's wrong
        (with no ORCHESTRATE.md, `planned: false` and `next` naming `plan`), plus the loader checks for that host
        (`preflight`). Models appear per host only. On Codex with `Codex sandbox: workspace-write`, the preflight
        (here, and before a build turn) warns, with the fixes, when the settings' targets or an open
        milestone's items plainly need a browser, which won't start inside that sandbox unless the agent asks
        to run it outside and is granted it. A run says so once, on stderr before its first build turn and on its
        result line; reviews aren't warned.
  lock [--worktree PATH] NAME -- COMMAND...
        Runs COMMAND under a named lock shared by every worktree of the repository (not the whole machine).
  runs [--repo PATH] [--json]   (`loops` before 2.1.0, still accepted)
        Every run, review and plan running on this machine, in any repository and from any copy of this script: its
        repository, module, milestone, role, host, model, effort, path (visible or headless), pid, start, turns, time
        since the last sign of activity (a turn starting or ending, or its session file growing) and tokens where the
        host reported them. Tokens count when a turn ends, so a turn under way shows as `turn_running_s` (and "turn N
        running for ..."); a run's build row counts from its build, the design review it ran first being under
        `design_review` on its result line. A dollar figure, here and in `cost` and `report`, is Claude's list price
        for the Claude turns only; Codex reports tokens, not a price. Each loop keeps a record in $ORCHESTRATE_LOOPS_DIR (default
        ~/.local/state/orchestrate/loops, or under $XDG_STATE_HOME), which counts only while its process holds a lock
        on it, so a dead run never shows; this command removes what dead runs left there. A run
        that can't write its record (a sandboxed home) runs as usual, and is listed from the process table with what
        its command line says. --repo narrows the list to one repository; --json is for a lead.

Per-worktree session state lives in <git dir>/orchestrate/<module>.json, so re-running the same command resumes.
Run locks (run-<MODULE>.lock, run-_plan.lock) live in <git common dir>/orchestrate/. The kernel releases one when its
run ends; the file stays, holding the last holder's pid. A run, a review or a plan holds its lock for as long as it
runs, and adopt holds the lock of each module whose definitions it authorises while it merges them; nothing else
locks them.

A write under .git that the system or a sandbox refuses (Codex's workspace-write sandbox, for one), or a lock file
another git process holds, stops any command with one line naming the path and the fix (`blocked_write`): SCRIPT_FAILED, or
FAILED from `merge`, exit 1. The script doesn't retry it or delete lock files.
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
import tempfile
import threading
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import codex_quota  # noqa: E402  (beside this file)

DEFAULT_MODELS = {"codex": "gpt-6.1-sol", "claude": "claude-opus-5-5"}
DEFAULT_MODEL = DEFAULT_MODELS["codex"]
# The settings' word for each kind of agent -> the role a launch resolves. A settings line names a kind, with or
# without a host in front: "- **Claude planner:** claude-fable-5-2 high" or "- **Reviewer:** high".
ROLE_KINDS = {"planner": "plan", "builder": "build", "reviewer": "review", "design reviewer": "design"}
ROLE_FALLBACK = {"design": "review"}  # a design review with no line of its own uses the reviewer's
DEFAULT_EFFORT = "medium"  # the house position for code; planners default to high
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
CODEX = os.environ.get("ORCHESTRATE_CODEX") or shutil.which("codex") or \
    "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex"
CLAUDE = os.environ.get("ORCHESTRATE_CLAUDE") or shutil.which("claude") or "claude"
CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
REPORT_WORDS = ("DONE", "BLOCKED", "NEEDS_CONTEXT")
STATES = {"not_started", "in_progress", "ready_for_review", "done", "blocked"}
STATUSES = {"open", "pass"}  # an item's status; "open" here is not the milestone state
VERDICTS = {"", "pass", "fail", "could_not_judge"}
# Why a milestone is Blocked: the `reason` of its `blocked` object, {"reason", "items"?, "what"}.
BLOCK_REASONS = ("needs_human_feedback", "needs_access", "needs_hardware", "needs_context", "needs_dependency",
                 "too_many_failed_reviews")
# What an item needs that a builder can't do alone: its `needs` object, {"type", "what"}.
NEEDS_TYPES = ("human_feedback", "access", "hardware")
DEFINITION_KEYS = ("statement", "check", "inspect", "ask", "target", "lock", "needs")
TEXT_KEYS = ("statement", "check", "inspect", "ask", "target", "lock", "evidence", "review")
NEED = re.compile(r"^(?:([A-Za-z0-9_.-]+):)?([A-Za-z0-9_.-]+)$")  # "M2" in this module, or "CORE:M3"
TRAILER = "Orchestrate-Script: yes"
TRAILERS = (TRAILER, "Orchestrate-Loop: yes")  # the second marks the script's commits from before 2.0
# A lead's mark that a milestone is In Progress. The ref path keeps its name from before 2.1.0, so leads on older
# versions in other clones still see each other's marks.
HOLDS = "refs/orchestrate/claims"

LOOP = Path(__file__).resolve()
SKILLS = LOOP.parents[2]  # the folder holding build, build-milestone, review-milestone and plan-module

GOAL_LINE = ("Call your create_goal tool with the paragraph that starts \"The goal:\" as the objective, word for word. "
             "The rest of this message is for this turn only.\n\n")

# The builder's first prompt. It carries only what the build-milestone skill can't: the milestone and its files,
# this install's paths, this session's facts and the lead's note. A Codex builder makes the paragraph that starts
# "The goal:" its goal, which Codex re-sends every turn, so nothing that is only for this turn sits in it. {lead} is the lead's --message under
# "From the lead", after the rules, {feedback} the Human Feedback note, {earlier} names the handoff an earlier
# session left, {needs} one rule per kind of item that needs someone, and {rules} the owner's rules; each is empty
# when there is none. {handoff} is where this session writes its own handoff if it stops short.
BUILD_TEMPLATE = """{goal}Build milestone {milestone} of module {module}, using the build-milestone skill ({skill}).

The goal: every item of {milestone} in {done} has status pass, with evidence from the item's target, and the work \
is merged, with {milestone}'s state left as in_progress. When you end with DONE, the script runs the checks on the \
merged work and sets the state itself.
{feedback}{earlier}
For this session:
- Work only in this worktree. The lead starts the review, so don't start a reviewer.
- The script is `python3 {loop}`. Merge with its `merge --worktree .` command.
- Start a command that runs longer than a few minutes with the script's `background -- <command>`, and wait for it \
with its `wait <id>`, not with sleep and tail, as the skill's "Long commands" section says.
- {session}
{resources}{needs}{rules}{lead}
To finish: when the goal is met, end with DONE and the evidence. If you can't go on, write your handoff to \
{handoff} and commit it with your work, then end with `BLOCKED <reason>: <one sentence on what would unblock it>`, \
where the reason is needs_human_feedback, needs_access, needs_hardware or needs_dependency, or, when you're missing \
a fact, with `NEEDS_CONTEXT: <the fact you need>`."""

REVIEW_TEMPLATE = """Review milestone {milestone} of module {module}, using the review-milestone skill ({skill}).

The goal: a review at {review} that judges every item of {milestone} in {done}, with the verdict fields, state and \
findings set as the skill says. The script sets the counts.
{answers}
Rules:
- This folder is a clean checkout of commit {commit}, which the script made for you. Build and run the product \
from it where an item needs you to see it working.{checks}
- Put captures and other evidence files in {captures}/ and link them from the review, rather than embedding them \
in it.
- Start a command that runs longer than a few minutes with `python3 {loop} background -- <command>`, and wait for \
it with `python3 {loop} wait <id>`, which returns when it ends with the end of its log. Waiting with sleep and tail \
re-reads this whole conversation at every check.
- Don't commit, push or change anything else. The script checks what you changed, then merges the review itself.
- Don't start other agents.
- If you can't reach the product at all, because the screen is locked, a permission needs the owner's approval \
or a device isn't connected, judge nothing and end with `BLOCKED needs_access: <what the owner has to do>`. The \
script then counts no round, and the lead runs this review again while the owner is at the machine.

To finish, end with the skill's last line."""

DESIGN_REVIEW_TEMPLATE = """Review the design of module {module}, using the "Reviewing a design" section of the \
review-milestone skill ({skill}).

The goal: a review at {review} that says whether the design does what the owner asked for.
{changed}{briefs}
Rules:
- This folder is a clean checkout of the main branch's tip.
- Put any captures in {captures}/, and change nothing else. The script merges them.
- Don't start other agents.

To finish, end with the skill's last line."""

PLAN_TEMPLATE = """{task}

Use the plan-module skill ({skill}) for this task.

Rules:
- You can't start other agents.
- The script commits and merges the files you leave and records the new definitions, so don't commit, merge, pull \
or push. Never edit an ACCEPTED.json file or the plans folder's STATUS.md, which the script writes.
- Each module's files go in its own folder under the plans folder: DESIGN.md, PLAN.md, LOG.md and DONE.json.
- The script is `python3 {loop}`. Its `check --module <M> --milestone <id> --worktree . --items-only` command \
tries a milestone's item checks without recording anything. It leaves out the project's test command, and runs \
each check under the item's lock, waiting while a builder holds it.

To finish: say what changed and any decision the owner must make, then end with `PLANNED` once the files are \
written. The script lists the files you changed itself. If nothing should change, or you can't go on, end with \
`BLOCKED: ...` or `NEEDS_CONTEXT: ...`, and the script merges nothing."""

FINDINGS_TEMPLATE = """The reviewer failed {milestone}. The review is {evidence}/{module}/{milestone}-review.md. The \
script has set the items that didn't pass back to open, so each needs fresh evidence. Fix every Must Fix finding, \
including items the reviewer marked could_not_judge (they need evidence the reviewer can reach) and Must Fix \
defects outside the items. Suggestions are your call. The milestone's `findings` in the done-when file lists each \
Must Fix and marks with `repeat` any that an earlier round raised; those are what escalate the milestone, so make \
sure they stay fixed. Add the findings to the plan as work items, fix them, re-verify the affected items, merge, \
and end with DONE. Leave the state as in_progress: the script runs the checks again and sets Ready for Review."""


class TipError(Exception):
    pass


# --------------------------------------------------------------------------------------------------------- settings

PROFILE_FIELDS = {"plans": "docs/plans", "evidence": "docs/evidence", "test command": None, "branch": "main",
                  "remote": "origin", "merge": None, "codex sandbox": "workspace-write", "writable roots": "",
                  "graded examples": "", "effort": "", "claude permissions": "auto", "default host": "",
                  "review host": "", "planner host": "", "exclusive resources": ""}
REQUIRED = {"test command": "the command that must pass before merging, or `none`",
            "merge": "push (standing permission to push) or local"}
ONE_WORD = {"branch", "remote", "merge", "codex sandbox", "effort", "claude permissions", "default host",
            "review host", "planner host"}
ALLOWED = {"codex sandbox": {"workspace-write", "danger-full-access"}, "merge": {"push", "local"},
           "effort": EFFORTS, "claude permissions": {"auto", "acceptEdits", "bypassPermissions", "dontAsk"}}
PLACEHOLDER = re.compile(r"<[A-Za-z][^<>]*>")  # "<where review files go>", not "cmd < input"
BOUNDS = ("Licences and paths not to touch", "Owner decides")  # the settings' out-of-bounds lines


def profile_value(text: str, label: str, whole: bool = False) -> str | None:
    """The value of a settings bullet `- **Label:** value`. With `whole`, the bullet's continuation lines too (lines
    indented under it, including nested bullets, which are joined with "; "), for prose rules that run on."""
    m = re.search(rf"^([ \t]*)[-*]\s*\*\*{re.escape(label)}:\*\*[ \t]*(.*)$", text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    raw = m.group(2)
    if whole:
        indent, parts = len(m.group(1).expandtabs()), [raw.strip()]
        for line in text[m.end():].split("\n")[1:]:
            if not line.strip():
                parts.append("")
                continue
            if len(line) - len(line.lstrip(" \t")) <= indent:
                break
            body = line.strip()
            nested = re.match(r"^[-*+]\s+|^\d+[.)]\s+", body)
            parts.append(("\x00" if nested else "") + body[nested.end():] if nested else body)
        raw = ""
        for part in parts:
            if not part:
                continue
            if part.startswith("\x00"):
                raw = raw.rstrip().rstrip(";:.") + ("; " if raw.strip() else "") + part[1:]
            else:
                raw = (raw + " " + part) if raw else part
    raw = re.sub(r"\*\(.*?\)\*", "", raw)                # trailing *(read by the script)* notes
    raw = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", raw)  # markdown links keep their text
    return raw.replace("`", "").strip()


def role_lines(text: str, hosts: set, problems: list) -> dict:
    """The settings' lines for one kind of agent: `{role: {"effort": ..., "hosts": {host: {"model": ..., "effort":
    ...}}}}`. A line with a host in front ("Claude planner") may give a model, an effort or both, and applies on that
    host only, so one company's model name is never sent to another's program. A line with no host ("Planner") gives
    an effort for that kind of agent on every host."""
    out: dict = {}
    for m in re.finditer(r"^\s*[-*]\s*\*\*(?:([\w.-]+) )??(design reviewer|planner|builder|reviewer):\*\*[ \t]*(.*)$",
                         text, re.IGNORECASE | re.MULTILINE):
        host, kind = (m.group(1) or "").lower(), m.group(2).lower()
        label = f"{m.group(1) + ' ' if host else ''}{m.group(2)}"
        raw = re.sub(r"\*\(.*?\)\*", "", m.group(3)).replace("`", "").replace(",", " ").strip()
        if not raw or PLACEHOLDER.search(raw):
            continue
        efforts = [t for t in raw.split() if t.lower() in EFFORTS]
        models = [t for t in raw.split() if t.lower() not in EFFORTS]
        if len(efforts) > 1 or len(models) > 1:
            problems.append(f"{label}: {raw!r} (want one model, one effort, or both)")
        elif host and host not in hosts:
            problems.append(f"{label}: {host!r} isn't a host these settings can start (codex, claude, or one with a "
                            f"'Host {host}:' line)")
        elif models and not host:
            problems.append(f"{label}: {raw!r} (a model belongs to one host, so name the host: "
                            f"'<Host> {kind}: {models[0]}'. With no host the line takes an effort only)")
        else:
            entry = out.setdefault(ROLE_KINDS[kind], {"effort": None, "hosts": {}})
            effort = efforts[0].lower() if efforts else None
            if host:
                entry["hosts"][host] = {"model": models[0] if models else None, "effort": effort}
            else:
                entry["effort"] = effort
    return out


def role_setting(prof: dict, role: str, host: str) -> tuple[str | None, str | None]:
    """The model and effort the settings' lines give this kind of agent on this host; None where they give none."""
    model = effort = None
    while role:
        entry = prof.get("roles", {}).get(role) or {}
        here = entry.get("hosts", {}).get(host) or {}
        model = model or here.get("model")
        effort = effort or here.get("effort") or entry.get("effort")
        role = ROLE_FALLBACK.get(role)
    return model, effort


OLD_PLANS = "docs/modules"  # the plans folder's default before docs/plans; still used when only it exists
NUMBER_WORDS = {w: n for n, w in enumerate(("one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
                                            "ten", "eleven", "twelve"), 1)}


def builders_count(text: str) -> int | None:
    """The first number in the settings' `Builders:` line, as a digit or a word ("two Codex builders"), which `run`
    keeps to; None when the line has no number, which sets no limit. In Thrum four to six builders ran against "two
    Codex builders", once right after the lead had told the owner the setting was in force."""
    value = profile_value(text, "builders")
    if not value or PLACEHOLDER.search(value):
        return None
    m = re.search(r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\b", value, re.IGNORECASE)
    if not m:
        return None
    n = int(m.group(1)) if m.group(1).isdigit() else NUMBER_WORDS[m.group(1).lower()]
    return n or None


def profile(worktree: Path, strict: bool = False, missing_ok: bool = False, flat_ok: bool = False,
            old_ok: bool = False) -> dict:
    """Reads the project settings from ORCHESTRATE.md (`- **Label:** value` lines). `Merge` and `Test command` must
    be there, because silently pushing, or merging with no test, isn't something to default into. A missing
    settings file, or a missing, unfilled or invalid value, raises SystemExit when strict, and falls back to safe
    defaults (local merge, no test command) with a warning otherwise. `missing_ok` drops the warning for a settings
    file that doesn't exist yet, where the caller says so itself (an unplanned project) or a planner is about to
    write it. A plans folder still in the old flat layout (<MODULE>-DONE.json directly in it) stops the command with
    the `migrate` command to run, unless `flat_ok`; so does a project still using the names from before 2.0, unless
    `old_ok`."""
    path = worktree / "ORCHESTRATE.md"
    problems = [] if path.exists() else [f"no ORCHESTRATE.md in {worktree}"]
    text = path.read_text() if path.exists() else ""
    out = {}
    for key, default in PROFILE_FIELDS.items():
        value = profile_value(text, key)
        if value is None and old_ok and key in OLD_FIELD_LABELS:  # migrate reads a settings file it is renaming
            value = profile_value(text, OLD_FIELD_LABELS[key])
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
    if not profile_value(text, "plans") and not (worktree / out["plans"]).exists() and (worktree / OLD_PLANS).is_dir():
        out["plans"] = OLD_PLANS  # a project from before docs/plans keeps its modules where they are
    out["merge"] = out["merge"] or "local"
    test = out.pop("test command")
    out["test_command"] = "" if (test or "none").lower() == "none" else test
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
    out["roles"] = role_lines(text, {"codex", "claude", *out["hosts"]}, problems)
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
        problems.append(f"review host: {out['review_host']!r} (want same, other, codex, claude or a host these settings "
                        "names)")
        out["review_host"] = ""
    out["planner_host"] = out.pop("planner host").lower()
    if out["planner_host"] not in ("", "codex", "claude", *out["hosts"]):
        problems.append(f"planner host: {out['planner_host']!r} (want codex, claude or a host these settings names)")
        out["planner_host"] = ""
    out["builders"] = builders_count(text)
    out["roots"] = [r.strip() for r in out.pop("writable roots").split(",") if r.strip()]
    out["graded_examples"] = out.pop("graded examples") or f"{out['evidence']}/graded-examples.md"
    # Prose rules the script restates on resumed turns; None when the line is missing or still a placeholder.
    out["bounds"] = {}
    for label in BOUNDS:
        value = profile_value(text, label, whole=True)
        out["bounds"][label] = value if value and not PLACEHOLDER.search(value) else None
    if not flat_ok and flat_modules(worktree, out["plans"]):
        raise SystemExit(flat_refusal(worktree, out["plans"]))
    if not old_ok and (old := old_names_here(worktree, out["plans"], text)):
        raise SystemExit(old_names_refusal(worktree, old))
    if problems:
        message = "ORCHESTRATE.md has missing, unfilled or invalid fields: " + "; ".join(problems)
        if strict:
            raise SystemExit(message)
        if not (missing_ok and not path.exists()):
            print("warning: " + message, file=sys.stderr)
    return out


def planned_elsewhere(worktree: Path) -> str | None:
    """With no settings file to name the main branch, the likeliest candidates for it (the branch's upstream, the
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
    Planned or not is decided from the main branch's tip, so a worktree that is merely behind a tip that has a settings file is
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
                "next": next_cmd(None, "lead", "this worktree has diverged from the planned tip; the script leaves "
                                               "merging it to whoever owns that branch")}
    return {"reason": f"the project isn't planned yet: there's no ORCHESTRATE.md in {worktree}",
            "next": next_cmd(loop_cmd("plan", "--worktree", str(worktree), "--task",
                                      "Plan the project: <what the owner asked for, in their words>"), "lead",
                             "a planner writes the project settings (ORCHESTRATE.md), the module table in ARCHITECTURE.md and the first module's "
                             "plan; give it the owner's ask, and their answers on hosts, merging and checks")}


def codex_flags(prof: dict, role: str = "build") -> list[str]:
    flags = ["-m", prof["model"], "-c", f"model_reasoning_effort={prof['effort']}",
             "-c", "approval_policy=on-request", "-c", "approvals_reviewer=auto_review",
             "-c", f"sandbox_mode={prof['sandbox']}",
             # the agent's own shell commands see the role, as the script's environment already gives it headless
             "-c", f"shell_environment_policy.set.ORCHESTRATE_ROLE={json.dumps(role)}"]
    if role in ("review", "plan"):
        flags += ["-c", "features.multi_agent=false"]  # the twin of Claude's --disallowedTools Agent
    if prof["sandbox"] == "workspace-write":
        flags += ["-c", "sandbox_workspace_write.network_access=true"]
        if prof["roots"]:
            roots = ",".join(json.dumps(str(Path(r).expanduser())) for r in prof["roots"])
            flags += ["-c", f"sandbox_workspace_write.writable_roots=[{roots}]"]
    return flags


_HELP: dict = {}  # (binary, subcommand...) -> what its --help printed, asked once per binary


def help_text(*command: str) -> str:
    """What `<command> --help` prints. It is asked once per binary, because the script checks a flag on every turn
    and the binary doesn't change while the script runs."""
    if command not in _HELP:
        try:
            _HELP[command] = subprocess.run([*command, "--help"], capture_output=True, text=True).stdout
        except OSError:
            _HELP[command] = ""
    return _HELP[command]


def claude_supports(flag: str) -> bool:
    return flag in help_text(CLAUDE)


def codex_supports(flag: str) -> bool:
    return flag in help_text(CODEX, "exec")


# ------------------------------------------------------------------------------------------------------------- git

class WriteBlocked(Exception):
    """A write under the repository that the operating system or a sandbox refused, or a lock file another git
    process holds. The script stops on it with a plain explanation, rather than retrying or deleting anything."""

    def __init__(self, path: str | None, error: str, held: bool = False):
        super().__init__(path, error, held)
        self.path, self.error, self.held = path, error, held

    def reason(self) -> str:
        where = self.path or "a file under .git"
        if self.held:
            return (f"git couldn't take the lock {where}: another git process holds it, or one that crashed left it "
                    "behind. The script doesn't delete lock files; check nothing else is running git here, remove it "
                    "yourself if it's stale, then run the command again.")
        return (f"git can't write {where} ({self.error}). This command has to run outside the sandbox, or with "
                "escalation: a sandbox such as Codex's workspace-write blocks writes under .git. The script didn't retry "
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
    """Identity flags for commits the script makes, when the repository has no identity of its own."""
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
    return f"{prof['remote']}/{prof['branch']}" if prof["merge"] == "push" else prof["branch"]


def tip(worktree: Path, prof: dict, fetch: bool = True) -> str:
    """The main branch tip's commit: the remote branch after a fresh fetch, or the local branch. Raises TipError
    rather than falling back to something staler, because readiness judged on a stale tip is wrong."""
    if prof["merge"] == "push" and fetch:
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
    all, or (merging by push) a remote that doesn't have the branch. None for any other failure."""
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
                          "a first commit gives the script a base to merge plans and records on; it carries no files, "
                          "so nothing of yours goes in it")
        return e
    if prof["merge"] == "push" and has_remote and \
            git(worktree, "ls-remote", "--exit-code", "--heads", remote, branch).returncode == 2:
        e = TipError(f"{remote} has no {branch} branch yet; push it (`git push -u {remote} {branch}`), then run this "
                     "again")
        e.next = next_cmd(f"git -C {shlex.quote(wt)} push -u {remote} {branch}", "lead",
                          f"Merge: push builds on {remote}/{branch}, which doesn't exist until it's pushed")
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
    """Fast-forwards a clean worktree that's behind the main branch's tip, so a warm worktree doesn't start a milestone
    from old files. A worktree with uncommitted or unmerged work is left for its builder to rebase."""
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

# The layout of the plans folder, defined here and nowhere else. Each module is a folder <plans>/<MODULE>/ holding
# these files; a folder is a module when it holds DONE.json. The project's own files sit at the top of <plans>.
MODULE_FILES = {"design": "DESIGN.md", "plan": "PLAN.md", "log": "LOG.md", "done": "DONE.json",
                "record": "ACCEPTED.json", "brief": "BRIEF.md"}
PROJECT_FILES = {"brief": "BRIEF.md", "glossary": "GLOSSARY.md", "architecture": "ARCHITECTURE.md",
                 "status": "STATUS.md"}


def module_file(prof: dict, stem: str, kind: str) -> str:
    """A module's file, as a path from the repository root: <plans>/<MODULE>/<the file for `kind`>."""
    return f"{prof['plans']}/{stem}/{MODULE_FILES[kind]}"


def project_file(prof: dict, kind: str) -> str:
    """A file about the whole project, at the top of the plans folder."""
    return f"{prof['plans']}/{PROJECT_FILES[kind]}"


def done_rel(prof: dict, stem: str) -> str:
    return module_file(prof, stem, "done")


def record_rel(prof: dict, stem: str) -> str:
    return module_file(prof, stem, "record")


def design_rel(prof: dict, stem: str) -> str:
    return module_file(prof, stem, "design")


def plan_rel(prof: dict, stem: str) -> str:
    return module_file(prof, stem, "plan")


def log_rel(prof: dict, stem: str) -> str:
    return module_file(prof, stem, "log")


def handoff_rel(prof: dict, stem: str, mid: str) -> str:
    """Where a builder that stops short writes what the next session needs: the evidence folder, which the script
    merges and every agent can read."""
    return f"{prof['evidence']}/{stem}/{mid}-handoff.md"


def status_rel(prof: dict) -> str:
    return project_file(prof, "status")


def module_of(prof: dict, rel: str) -> tuple[str, str] | None:
    """(module, kind) for a path that is one of a module's files, as `module_file` builds them; else None."""
    head = prof["plans"] + "/"
    if not rel.startswith(head):
        return None
    parts = rel[len(head):].split("/")
    if len(parts) != 2 or not parts[0]:
        return None
    kind = next((k for k, name in MODULE_FILES.items() if name == parts[1]), None)
    return (parts[0], kind) if kind else None


def records_glob(prof: dict) -> str:
    """A git pathspec for every record file under the plans folder."""
    return f":(glob){prof['plans']}/*/{MODULE_FILES['record']}"


def modules_here(tree: Path, prof: dict) -> list[str]:
    """The modules in a checkout's files: every folder under the plans folder that holds a done-when file."""
    folder = tree / prof["plans"]
    if not folder.is_dir():
        return []
    return sorted(p.name for p in folder.iterdir() if (p / MODULE_FILES["done"]).is_file())


def modules_at(worktree: Path, prof: dict, ref: str) -> list[str]:
    """The modules at `ref`, found the same way as `modules_here`."""
    listed = git(worktree, "ls-tree", "-r", "--name-only", ref, "--", prof["plans"] + "/")
    found = []
    for rel in listed.stdout.splitlines() if listed.returncode == 0 else []:
        if (where := module_of(prof, rel)) and where[1] == "done":
            found.append(where[0])
    return sorted(found)


FLAT_DONE = re.compile(r"^(.+)-DONE\.json$")


def flat_modules(tree: Path, plans: str) -> list[str]:
    """The modules still in the old flat layout, where <MODULE>-DONE.json sat directly in the plans folder."""
    folder = tree / plans
    if not folder.is_dir():
        return []
    return sorted(m.group(1) for p in folder.iterdir() if p.is_file() and (m := FLAT_DONE.match(p.name)))


OLD_LABELS = {"Check": "Test command", "Integrate": "Merge"}  # the settings lines' labels before 2.0
OLD_FIELD_LABELS = {new.lower(): old.lower() for old, new in OLD_LABELS.items()}


def rename_labels(text: str) -> str:
    """The settings file with its `Check:` and `Integrate:` lines given their 2.0 labels."""
    for old, new in OLD_LABELS.items():
        if profile_value(text, new) is None:
            text = re.sub(rf"^(\s*[-*]\s*\*\*){re.escape(old)}(:\*\*)", rf"\g<1>{new}\g<2>", text, count=1,
                          flags=re.IGNORECASE | re.MULTILINE)
    return text


def old_names_here(tree: Path, plans: str, settings: str | None = None) -> list[str]:
    """What in this working copy still uses the names from before 2.0: the settings file's old labels, and each
    module's done-when and record files, one phrase per file."""
    if settings is None:
        path = tree / PROFILE_FILE
        settings = path.read_text() if path.exists() else ""
    found = [f"{PROFILE_FILE}'s `{old}:` line (now `{new}:`)" for old, new in OLD_LABELS.items()
             if profile_value(settings, old) is not None and profile_value(settings, new) is None]
    folder = tree / plans
    for kind, test in (("DONE.json", old_names_in_doc), ("ACCEPTED.json", old_names_in_record)):
        for p in sorted(folder.glob(f"*/{kind}")) if folder.is_dir() else []:
            try:
                names = test(json.loads(p.read_text()))
            except (json.JSONDecodeError, OSError):
                continue
            if names:
                found.append(f"{p.relative_to(tree)}: {', '.join(names)}")
    return found


def old_names_refusal(tree: Path, found: list[str]) -> str:
    """The message a command stops with when the project still uses the names from before 2.0."""
    return ("error: this project still uses the names from before orchestrate 2.0: " + "; ".join(found[:6]) +
            ("; ..." if len(found) > 6 else "") + ". Bring it to the new names once, in one commit, with:\n  " +
            loop_cmd("migrate", "--worktree", str(tree)) +
            "\nIf the main branch has already been migrated, the same command fast-forwards this worktree instead, "
            "and a worktree with commits of its own is brought over with:\n  " +
            loop_cmd("migrate", "--branch", "--worktree", str(tree)))


def flat_refusal(tree: Path, plans: str) -> str:
    """The message a command stops with when the plans folder still has the old flat layout."""
    found = flat_modules(tree, plans)
    return (f"error: {tree / plans} still has plan files in the old flat layout ({', '.join(f'{s}-DONE.json' for s in found[:5])}"
            f"{', ...' if len(found) > 5 else ''}). The script now keeps each module in a folder of its own, "
            f"{plans}/<MODULE>/DONE.json, and reads nothing else. Move them once, with:\n  "
            + loop_cmd("migrate", "--worktree", str(tree)) +
            "\nIf the main branch has already been moved, the same command fast-forwards this worktree instead, "
            "and a worktree with commits of its own is brought over with:\n  " +
            loop_cmd("migrate", "--branch", "--worktree", str(tree)))


def module_stem(worktree: Path, prof: dict, module: str) -> str:
    """The module's name as its folder spells it, found without regard to case."""
    for stem in modules_here(worktree, prof):
        if stem.upper() == module.upper():
            return stem
    raise SystemExit(f"error: {worktree / done_rel(prof, module)} doesn't exist; the module needs planning "
                     "(/plan-module) first")


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
    """The structural problems that would let a milestone through without proof, or leave the queue stuck."""
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
        if m.get("state") == "blocked":
            b = m.get("blocked")
            if not isinstance(b, dict) or b.get("reason") not in BLOCK_REASONS or not isinstance(b.get("what", ""), str):
                problems.append(f"{mid}: blocked, but \"blocked\" should be an object like {{\"reason\": "
                                f"\"needs_context\", \"what\": \"...\"}}, with reason one of {', '.join(BLOCK_REASONS)}")
        for counter in ("fails", "replans", "rounds", "diagnoses"):
            if not is_count(m.get(counter, 0)):
                problems.append(f"{mid}: {counter} {m.get(counter)!r} isn't a whole number of 0 or more")
        items = m.get("items")
        if not isinstance(items, list) or not items:
            problems.append(f"{mid}: no items")
            items = []
        problems += findings_problems(m, mid, items)
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
            if "needs" in item:
                n = item["needs"]
                if not isinstance(n, dict) or n.get("type") not in NEEDS_TYPES or not isinstance(n.get("what"), str) \
                        or not n["what"].strip():
                    problems.append(f"{iid}: needs {n!r} should be an object like {{\"type\": \"access\", \"what\": "
                                    f"\"approve Computer Use for IINA\"}}, with type one of {', '.join(NEEDS_TYPES)}")
        deps = m.get("depends_on", [])
        if not isinstance(deps, list) or not all(isinstance(n, str) and NEED.match(n) for n in deps):
            problems.append(f"{mid}: depends_on {deps!r} should be a list like [\"M2\", \"CORE:M3\"]")
            continue
        for need in deps:
            other, target = NEED.match(need).groups()
            if other and other.upper() != module.upper():
                continue
            if target not in order:
                problems.append(f"{mid}: depends on {target}, which isn't in this module")
            elif order.index(target) >= index:
                problems.append(f"{mid}: depends on {target}, which comes at or after it, so it can never start "
                                "(milestones in a module run in order)")
    return problems


def findings_problems(m: dict, mid: str, items: list) -> list[str]:
    """What's wrong with a milestone's `findings`: the reviewer's list of the Must Fix findings of its last review,
    each with a short `name` kept the same from round to round, the `item` it fails (none for a defect outside the
    items), and `different` saying how a new failure of an item that failed before isn't the same defect."""
    found = m.get("findings", [])
    if not isinstance(found, list):
        return [f"{mid}: findings should be a list"]
    ids = {i.get("id") for i in items if isinstance(i, dict)}
    problems, names = [], set()
    for f in found:
        if not isinstance(f, dict) or not isinstance(f.get("name"), str) or not f["name"].strip():
            problems.append(f"{mid}: each finding needs a short name")
            continue
        if f["name"] in names:
            problems.append(f"{mid}: two findings are named {f['name']!r}")
        names.add(f["name"])
        if "item" in f and f["item"] not in ids:
            problems.append(f"{mid}: finding {f['name']!r} names item {f['item']!r}, which isn't one of {mid}'s")
        if "different" in f and not isinstance(f["different"], str):
            problems.append(f"{mid}: finding {f['name']!r}: different should be text")
    return problems


def definitions(milestone: dict) -> str:
    """A hash of what the milestone asks for, as opposed to what anyone has claimed about it. Inside the hash the
    fields keep the names they had before 2.0 (`needs` for the dependency list, `attended` for an item's needs), so
    a milestone that uses neither hashes as it always did, and only those that do are re-stamped by `migrate`."""
    spec = {"bar": milestone.get("bar"), "needs": milestone.get("depends_on") or [],
            "items": [{**{k: i.get(k) for k in DEFINITION_KEYS if k != "needs"}, "attended": i.get("needs")}
                      for i in milestone["items"]]}
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


# ------------------------------------------------------------------------------------------------- names before 2.0

OLD_STATES = {"open": "not_started", "claimed": "ready_for_review"}
OLD_DEFINITION_KEYS = ("statement", "check", "inspect", "ask", "target", "lock", "attended")


def old_definitions(milestone: dict) -> str:
    """The definitions hash as the script wrote it before 2.0, for an old-named milestone, so `migrate` can tell a
    hash that matched then and re-stamp it with today's formula."""
    spec = {"bar": milestone.get("bar"), "needs": milestone.get("needs") or [],
            "items": [{k: i.get(k) for k in OLD_DEFINITION_KEYS} for i in milestone.get("items") or []]}
    return hashlib.sha256(json.dumps(spec, sort_keys=True).encode()).hexdigest()


def old_names_in_doc(doc) -> list[str]:
    """The names from before 2.0 that a done-when document still uses, one phrase each; empty when it has none."""
    if not isinstance(doc, dict) or not isinstance(doc.get("milestones"), list):
        return []
    found = []
    for m in doc["milestones"]:
        if not isinstance(m, dict):
            continue
        state = m.get("state")
        if state in ("open", "claimed", "parked"):
            found.append(f"state {state}")
        if state == "blocked" and isinstance(m.get("blocked"), str):
            found.append("a blocked milestone whose `blocked` is text")
        if "needs" in m:
            found.append("a milestone's `needs` list (now `depends_on`)")
        for i in m.get("items") or []:
            if not isinstance(i, dict):
                continue
            if "attended" in i:
                found.append("an item's `attended` (now `needs`)")
            if i.get("verdict") == "cant_tell":
                found.append("verdict cant_tell (now could_not_judge)")
            if isinstance(i.get("target"), str) and i["target"].startswith("proxy:"):
                found.append("a `proxy:` target (now `stand_in:`)")
    return list(dict.fromkeys(found))


def old_needs(item: dict) -> dict:
    """An old `attended` value as the `needs` object: an attended item asked a person to do or judge something, so
    it becomes Needs Human Feedback, unless its note names an approval (Needs Access) or a device (Needs Hardware)."""
    what = item.get("attended")
    text = what if isinstance(what, str) and what.strip() else (item.get("statement") or "the owner's judgement")
    if re.search(r"\b(approve|approval|permission|grant|prompt|computer use|screen recording|unlock)", text, re.I):
        return {"type": "access", "what": text}
    hardware = bool(re.search(r"\b(plug|connect|device|iphone|ipad|phone|hardware|usb|cable)\b", text, re.I))
    return {"type": "hardware" if hardware else "human_feedback", "what": text}


def upgrade_doc(doc):
    """A copy of a done-when document with the names from before 2.0 changed to today's; the same object when it
    has none. It reads old history as well as migrating, so every command can read a file from either side."""
    if not old_names_in_doc(doc):
        return doc
    doc = json.loads(json.dumps(doc))
    for m in doc["milestones"]:
        if not isinstance(m, dict):
            continue
        if "needs" in m:
            deps = m.pop("needs")
            m.setdefault("depends_on", deps)
        state = m.get("state")
        if state in OLD_STATES:
            m["state"] = OLD_STATES[state]
        elif state == "parked":
            m["state"] = "blocked"
            m["blocked"] = {"reason": "too_many_failed_reviews",
                            "what": "it kept failing review after its rewrite or diagnosis; the owner decides"}
        if m.get("state") == "blocked" and isinstance(m.get("blocked"), str):
            m["blocked"] = {"reason": "needs_context", "what": m["blocked"]}
        for i in m.get("items") or []:
            if not isinstance(i, dict):
                continue
            if "attended" in i:
                if i["attended"]:
                    i["needs"] = old_needs(i)
                del i["attended"]
            if i.get("verdict") == "cant_tell":
                i["verdict"] = "could_not_judge"
            if isinstance(i.get("target"), str) and i["target"].startswith("proxy:"):
                i["target"] = "stand_in:" + i["target"][len("proxy:"):]
    return doc


def old_names_in_record(rec) -> list[str]:
    """The old names that a record file still uses."""
    found = []
    for e in ((rec or {}).get("milestones") or {}).values() if isinstance(rec, dict) else []:
        if not isinstance(e, dict):
            continue
        if "owner_answers" in e:
            found.append("`owner_answers` (now `human_feedback`)")
        if "parked" in e:
            found.append("`parked` (now `too_many_failed_reviews`)")
        if "claim" in e:
            found.append("`claim` (now `ready_for_review`)")
        if "cant_tell" in json.dumps(e.get("reviews") or e.get("review") or ""):
            found.append("verdict cant_tell")
    return list(dict.fromkeys(found))


def upgrade_record(rec: dict, old_doc: dict | None = None, new_doc: dict | None = None) -> dict:
    """A copy of a record file with the names from before 2.0 changed. Given the done-when document before and after
    its upgrade, each stored definitions hash that matched the old milestone under the old formula is re-stamped
    with the new one, so the rename alone never reads as a planner's change."""
    rec = json.loads(json.dumps(rec))
    old_doc = old_doc if isinstance(old_doc, dict) else None
    new_doc = new_doc if isinstance(new_doc, dict) else None
    old_ms = {m.get("id"): m for m in (old_doc or {}).get("milestones") or [] if isinstance(m, dict)}
    new_ms = {m.get("id"): m for m in (new_doc or {}).get("milestones") or [] if isinstance(m, dict)}
    for mid, e in (rec.get("milestones") or {}).items():
        if not isinstance(e, dict):
            continue
        if "owner_answers" in e:
            old = e.pop("owner_answers") or []
            e.setdefault("human_feedback", [])
            for a in old:
                if not isinstance(a, dict):
                    continue
                entry = {"asked": a.get("asked"), "said": a.get("said", a.get("text", "")),
                         "items": a.get("items") or ([a["item"]] if a.get("item") else []), "at": a.get("at")}
                if a.get("by"):
                    entry["by"] = a["by"]
                e["human_feedback"].append(entry)
        if "parked" in e:
            e["too_many_failed_reviews"] = e.pop("parked")
        if "claim" in e:  # renamed in 2.1.0
            e["ready_for_review"] = e.pop("claim")
        for key in ("reviews",):
            if isinstance(e.get(key), list):
                e[key] = json.loads(json.dumps(e[key]).replace('"cant_tell"', '"could_not_judge"'))
        stored = e.get("definitions")
        if stored and mid in old_ms and mid in new_ms:
            try:
                if stored == old_definitions(old_ms[mid]):
                    e["definitions"] = definitions(new_ms[mid])
            except (KeyError, TypeError):
                pass
    return rec


def changed_items(before: dict, after: dict) -> list[str]:
    """What a design re-review should read: each item (or milestone) added, removed or redefined between two
    done-when documents, as `M2.3 changed`, `M3 added` and the like, in the newer document's order."""
    def index(doc: dict) -> tuple[dict, dict]:
        ms, items = {}, {}
        for m in doc.get("milestones") or []:
            ms[m.get("id")] = (m.get("bar"), m.get("depends_on") or [])
            items[m.get("id")] = {i.get("id"): {k: i.get(k) for k in DEFINITION_KEYS} for i in m.get("items") or []}
        return ms, items
    (old_ms, old_items), (new_ms, new_items) = index(before), index(after)
    out = []
    for mid, spec in new_ms.items():
        if mid not in old_ms:
            out.append(f"{mid} added")
            continue
        if spec != old_ms[mid]:
            out.append(f"{mid}'s bar or depends_on changed")
        was, now = old_items[mid], new_items[mid]
        out += [f"{iid} added" if iid not in was else f"{iid} changed" for iid in now if now[iid] != was.get(iid)]
        out += [f"{iid} removed" for iid in was if iid not in now]
    return out + [f"{mid} removed" for mid in old_ms if mid not in new_ms]


def path_at(worktree: Path, commit: str, path: str) -> str | None:
    """The name `path` had at `commit`, following renames such as `migrate`'s back from HEAD; None if it didn't
    exist then."""
    if show(worktree, commit, path) is not None:
        return path
    out = git(worktree, "log", "--follow", "--name-only", "--format=%x00%H", "--", path).stdout
    for block in out.split("\x00")[1:]:
        lines = [x for x in block.splitlines() if x.strip()]
        if len(lines) >= 2 and is_ancestor(worktree, lines[0], commit):
            return lines[1] if show(worktree, commit, lines[1]) is not None else None
    return None


def design_changes(worktree: Path, rec: dict, done_path: str, now: dict, design_path: str | None = None,
                   design_now: str | None = None) -> tuple[str, bool | None]:
    """(the sentence a design re-review's prompt carries, whether anything changed). It says what changed in the
    done-when file and the design since the last design review, so the reviewer reads those parts rather than
    working the diff out. When the script can't compare, it says so and names the earlier review, rather than
    staying silent. ("", None) for a first review; None also when it couldn't compare."""
    last = rec.get("design") or {}
    if not last.get("commit"):
        return "", None
    where = f"{last.get('review') or 'the last design review'}, at {last['commit'][:12]}"
    old_done = path_at(worktree, last["commit"], done_path)
    try:
        then = upgrade_doc(json.loads(show(worktree, last["commit"], old_done) or "")) if old_done else None
    except (json.JSONDecodeError, SystemExit):
        then = None
    if then is None:
        return (f"The script couldn't compare the plan with the last design review ({where}), because it can't read "
                f"{done_path} as it was then. Find what changed yourself, starting from that review's findings. "), None
    changed = changed_items(then, now)
    if design_path and last.get("hash") and design_now is not None and text_hash(design_now) != last["hash"]:
        changed.append(f"the design document ({design_path})")
    if not changed:
        return f"Nothing in the items or the design has changed since the last design review ({where}). ", False
    return (f"Since the last design review ({where}), these changed: {', '.join(changed)}. Read each one against "
            "that review's findings. "), True


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
    """The milestone's `depends_on` as (MODULE, milestone) pairs; a bare id means this module."""
    out = []
    for need in milestone.get("depends_on") or []:
        m = NEED.match(str(need))
        if m:
            out.append(((m.group(1) or module).upper(), m.group(2)))
    return out


def passing(milestone: dict) -> int:
    return sum(1 for item in milestone["items"] if item.get("status") == "pass")


# A failed review moves a milestone up the ladder only when one of its findings repeats an earlier round's, so a
# builder that fixes each finding and is shown a new one isn't treated as stuck. `rounds` counts every failed review,
# repeated or not; at ROUNDS_TO_DIAGNOSE a planner is asked what keeps failing, since reviews that keep finding new
# things can mean the checks are too broad.
FRESH_AFTER_ROUNDS = 3
ROUNDS_TO_DIAGNOSE = 6


def escalation(fails: int, replans: int = 0, rounds: int = 0, diagnoses: int = 0) -> str:
    """The ladder's word for a milestone's counts: `fails` is failed reviews with a repeated finding, `rounds` every
    failed review, both since the last re-plan, diagnosis or owner decision."""
    if fails >= 4:
        return "replan" if replans == 0 else "too_many_failed_reviews"
    if rounds >= ROUNDS_TO_DIAGNOSE:
        return "diagnose" if diagnoses == 0 else "too_many_failed_reviews"
    if fails <= 0 and rounds <= 0:
        return "none"
    if fails == 3 or rounds == FRESH_AFTER_ROUNDS:
        return "fresh-session"
    return "same-session"


def ladder(m: dict) -> str:
    """`escalation` for a milestone of a done-when file."""
    return escalation(*(int(m.get(k, 0) or 0) for k in ("fails", "replans", "rounds", "diagnoses")))


def repeats(findings: list, earlier_names: set, earlier_items: set) -> list[str]:
    """The names of this round's findings that repeat an earlier round's: the same name, or a failure of an item
    that failed before, unless the reviewer said under `different` how it isn't the same defect."""
    return [f["name"] for f in findings if f["name"] in earlier_names
            or (f.get("item") in earlier_items and not f.get("different"))]


def reset_proof(milestone: dict, only_failed: bool = False) -> None:
    """Clears the builder's proof so the next Ready for Review is verified afresh. After a failed review only the items that didn't pass
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
# `fails` is listed so that a reviewer following an older skill isn't refused for it; the script sets the counts.
REVIEWER_FIELDS = {"state", "fails", "findings"}, {"verdict", "review"}


def delta_problems(before: dict | None, after: dict, role: str, mid: str | None = None,
                   upstream: list | dict | None = None) -> list[str]:
    """What the role changed in a done-when file that it doesn't own. `upstream` holds other versions the file may
    legitimately match field by field: the script's own writes that a rebase brought in."""
    if isinstance(upstream, dict):
        upstream = [upstream]
    problems = []
    if role == "plan":
        old = {m.get("id"): m for m in (before or {}).get("milestones", [])}
        for m in after["milestones"]:
            was = old.get(m["id"], {})
            if m.get("state") in ("ready_for_review", "done") and was.get("state") != m.get("state"):
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
        if role == "build" and a.get("state") not in ("not_started", "in_progress", "ready_for_review", "done"):
            problems.append(f"{mid}: a builder can't set state {a.get('state')}")
        if role == "review":
            if b.get("state") != "ready_for_review":
                problems.append(f"{mid}: was {b.get('state')}, not ready_for_review, so there was nothing to review")
            elif a.get("state") not in ("done", "in_progress"):
                problems.append(f"{mid}: a review sets state done (pass) or in_progress (fail), not {a.get('state')}")
    return problems


# ---------------------------------------------------------------------------------------- the record file

def adopt(doc: dict, design: str, as_it_stands: bool = False) -> dict:
    """The record for a module the script hasn't seen before: its definitions authorised, nothing accepted, and its
    design review owed. `as_it_stands` (only for a repository that has never had a run record: a project taking up
    the script with work already done) also accepts its finished milestones, and takes a module already part-built to
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
    """Whether the repository at `ref` has never had a run record: none at `ref`, and no commit reachable from it
    ever touched one. Only then is a module adopted as it stands; once the script has written any record, a module it
    has no record for is new, whoever merged it and however."""
    listing = git(worktree, "ls-tree", "-r", "--name-only", ref, "--", prof["plans"] + "/").stdout.splitlines()
    if any((where := module_of(prof, n)) and where[1] == "record" for n in listing):
        return False
    # any record anywhere in history, in the module folders or the older flat layout, wherever the plans folder was
    return not git(worktree, "log", "-1", "--format=%H", ref, "--", f":(glob)**/{MODULE_FILES['record']}",
                   ":(glob)**/*-ACCEPTED.json").stdout.strip()


def take_up(tree: Path, prof: dict) -> list[str]:
    """In the script's first record-keeping commit in a repository that had no records, writes the record of every
    module still without one, adopted as it stands, so those modules keep what the script took them as once records
    exist. Returns the paths written."""
    written = []
    for stem in modules_here(tree, prof):
        path = tree / done_rel(prof, stem)
        rec_path = tree / record_rel(prof, stem)
        if rec_path.exists():
            continue
        try:
            doc = json.loads(path.read_text())
        except json.JSONDecodeError:
            continue
        if validate(doc, stem.upper()):
            continue
        design = tree / design_rel(prof, stem)
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
    legacy = None  # asked only when a module has no record
    for stem in modules_at(worktree, prof, ref):
        key = stem.upper()
        try:
            doc = json.loads(show(worktree, ref, done_rel(prof, stem)) or "")
        except json.JSONDecodeError as e:
            doc = {"unreadable": f"{done_rel(prof, stem)} isn't valid JSON: {e}"}
        design = text_hash(show(worktree, ref, design_rel(prof, stem)))
        old = old_names_in_doc(doc)
        problems = [f"{done_rel(prof, stem)} still uses the names from before 2.0 ({', '.join(old)}); run "
                    f"`migrate`"] if old else validate(doc, key)
        rec_text = show(worktree, ref, record_rel(prof, stem))
        rec = None
        if rec_text is not None:
            try:
                rec = json.loads(rec_text)
            except json.JSONDecodeError as e:
                problems.append(f"{record_rel(prof, stem)} isn't valid JSON: {e}")
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


def blocked_of(m: dict) -> dict:
    """A blocked milestone's `blocked` object, {"reason", "items"?, "what"}, whatever shape the file gave it."""
    b = m.get("blocked")
    if isinstance(b, dict) and b.get("reason") in BLOCK_REASONS:
        return b
    return {"reason": "needs_context", "what": b if isinstance(b, str) else ""}


def next_step(key: str, proj: dict, holds: dict | None = None, me: str = "") -> dict:
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
                f"`adopt` while the module was a draft (see {e['stem']}/{MODULE_FILES['record']}); re-plan it, or run "
                "`owner scope`"]}
        if m.get("state") == "blocked":
            b = blocked_of(m)
            return {**out, "status": "blocked", "reason": b["reason"], "blocked": b}
        if not design_ok(rec, e["design"]):
            return {**base, "status": "design_not_approved"}
        if (word := ladder(m)) in ("replan", "diagnose"):
            # repeated failures, or many new ones: another build round would only repeat them until a planner looks
            return {**out, "status": "waiting", "reason": "for_replan" if word == "replan" else "for_diagnosis",
                    "ladder": word, "fails": int(m.get("fails", 0) or 0), "rounds": int(m.get("rounds", 0) or 0)}
        # Ready for Review with no record of the script's checks was set by a builder before 2.1.0. It isn't owed a
        # review: `run` takes it like any milestone it builds, runs the checks, and records it if they pass.
        if (m.get("state") == "ready_for_review" and ready_current(rec["milestones"].get(m["id"]))) or \
                (m.get("state") == "done" and needs_review(m, doc)):
            ready = ready_record(rec["milestones"].get(m["id"]))
            return {**out, "status": "review_owed", "commit": ready.get("commit")}
        waiting, problems = [], []
        for mod, mid in needs_of(m, key):
            other = proj.get(mod)
            if other is None:
                waiting.append(f"{mod}:{mid} (not planned)")
                continue
            if other["problems"]:
                problems.append(f"depends on {mod}:{mid}, but {mod}'s done-when file is invalid")
                continue
            target = next((x for x in other["doc"]["milestones"] if x.get("id") == mid), None)
            if target is None:
                problems.append(f"depends on {mod}:{mid}, which isn't in {mod}'s done-when file")
            elif target.get("state") == "blocked" and blocked_of(target)["reason"] == "too_many_failed_reviews":
                problems.append(f"depends on {mod}:{mid}, which is Blocked: Too Many Failed Reviews")
            elif not accepted(target, other["record"]):
                waiting.append(f"{mod}:{mid}")
        if problems:
            return {**out, "status": "invalid", "problems": [f"{m['id']}: {p}" for p in problems]}
        if waiting:
            return {**out, "status": "waiting", "reason": "on_dependency", "depends_on": waiting}
        holder = (holds or {}).get((key, m["id"]))
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
    command names it. A milestone review gets no host here: `review` takes the builder's from the Ready for Review record."""
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
    """The `next` field: the exact command to run, who runs it (`lead` or `planner`), and why. A decision only the
    owner may make carries `decides: owner` and an `ask`; the lead still runs its command, once they've answered."""
    return {"command": command, "by": by, "why": why, **more}


def plan_task(module: str, problems: list[str]) -> str:
    return f"Fix {module}'s done-when file: " + "; ".join(problems)[:400]


def counted_since(e: dict) -> str:
    """When a milestone's review counts last started from 0: its definitions' authorisation (a plan, a re-plan or
    `owner scope`), or a later diagnosis or `owner reopen`."""
    return max((e.get("authorised") or {}).get("at") or "", e.get("counted_from") or "")


def counted_rounds(e: dict, after: int | None = None) -> list[dict]:
    """The review rounds a milestone's counts cover, oldest first: those after the last diagnosis or `owner reopen`
    (by position, since both can be recorded in the same second as a round) and not older than its definitions. `after`
    takes the rounds from that position instead."""
    auth = (e.get("authorised") or {}).get("at") or ""
    start = e.get("counted_after", 0) if after is None else after
    return [r for r in (e.get("reviews") or [])[start:] if (r.get("at") or "") >= auth]


def review_rounds(worktree: Path, prof: dict, module: str, mid: str) -> tuple[list[str], bool]:
    """(the review files of every round against the milestone's current definitions, oldest first; whether some of
    those rounds were overwritten before rounds were kept), read from the record at the last-fetched tip."""
    try:
        rec = json.loads(show(worktree, base_ref(prof), record_rel(prof, module)) or "{}")
    except (json.JSONDecodeError, SystemExit):
        rec = {}
    e = (rec.get("milestones") or {}).get(mid) or {}
    rounds = counted_rounds(e)
    return [r["review"] for r in rounds if r.get("review")], any(r.get("review_in_history") for r in rounds)


def round_history(worktree: Path | None, prof: dict, module: str, mid: str, after: int | None = None) -> list[str]:
    """One line per failed review the milestone's counts cover (or every one after position `after`), oldest first: what
    failed, and which findings repeated an earlier round. Read from the record at the last-fetched tip, for a
    planner and for the owner."""
    if worktree is None:
        return []
    try:
        rec = json.loads(show(worktree, base_ref(prof), record_rel(prof, module)) or "{}")
    except (json.JSONDecodeError, SystemExit):
        return []
    return history_lines((rec.get("milestones") or {}).get(mid) or {}, after)


def review_notes(mid: str, prof: dict, stem: str, feedback: list | None, history: list[str], judged: list) -> str:
    """What a milestone reviewer is told beyond the template, as paragraphs: the Human Feedback, the earlier rounds
    that still count (so a finding still there keeps its name), and a planner's judgement that earlier findings
    overreached. Empty when there is none of these."""
    parts = []
    if feedback:
        parts.append(feedback_note(feedback, mid, record_rel(prof, stem), "review"))
    if history:
        parts.append(f"Earlier failed rounds of {mid} that still count, with their findings: " + " | ".join(history) +
                     ". A finding still there keeps its name. An item that failed before and fails for a new reason "
                     "needs `different`.")
    if judged:
        j = judged[-1]
        on = f" on {j['at'][:10]}" if j.get("at") else ""
        parts.append(f"A planner's diagnosis{on} kept {mid}'s items as written, for this reason: {j.get('why', '')}. "
                     "Judge the items as they are written.")
    return "".join(f"\n{p}\n" for p in parts)


def history_lines(e: dict, after: int | None = None) -> list[str]:
    """`round_history` for a milestone's record entry."""
    lines = []
    for n, r in enumerate(r for r in counted_rounds(e, after) if r.get("verdict") == "fail"):
        found = r.get("findings")
        if found is None:  # rounds from before findings were recorded: point at the review rather than say "none"
            failed = [i for i, v in (r.get("items") or {}).items() if v != "pass"]
            read = f"read {r['review']}" if r.get("review") else "its review is only in git history"
            what = (f"items {', '.join(failed)} didn't pass; " if failed else "") + \
                f"its findings weren't recorded, so {read} for their names"
        else:
            what = "; ".join(f["name"] + (f" ({f['item']})" if f.get("item") else " (outside the items)")
                             + (", repeated" if f.get("repeat") else ", new") for f in found)
        lines.append(f"round {n + 1} ({(r.get('at') or '')[:10]}): {what}")
    return lines


def replan_task(module: str, mid: str, fails: int, prof: dict, worktree: Path | None = None) -> str:
    """The planner's task when the ladder reaches a re-plan: which milestone, why, and each round's review."""
    latest = f"{prof['evidence']}/{module}/{mid}-review.md"
    files, lost = review_rounds(worktree, prof, module, mid) if worktree else ([], True)
    where = (f"Its reviews, one per round: {', '.join(files)}" if files else f"The latest review is {latest}") + \
        (f" (earlier rounds are only in git history: git log -p -- {latest})" if lost or not files else "")
    history = round_history(worktree, prof, module, mid)
    rounds = f" What failed in each round: {' | '.join(history)}." if history else ""
    return (f"Re-plan {module} {mid}: {fails} of its failed reviews repeated a finding an earlier round had raised, "
            f"so the plan is wrong (plan-module, \"When a milestone keeps failing on the same finding\"). {where}.{rounds} Find "
            f"what keeps failing and change the definitions of {mid} so it can be met. The script resets its counts, "
            "counts the re-plan and opens it when your plan merges.")


def diagnose_task(module: str, mid: str, rounds: int, prof: dict, worktree: Path | None = None) -> str:
    """The planner's task when a milestone has failed review ROUNDS_TO_DIAGNOSE times, each time on something new."""
    latest = f"{prof['evidence']}/{module}/{mid}-review.md"
    files, lost = review_rounds(worktree, prof, module, mid) if worktree else ([], True)
    where = (f"Its reviews, one per round: {', '.join(files)}" if files else f"The latest review is {latest}") + \
        (f" (earlier rounds are only in git history: git log -p -- {latest})" if lost or not files else "")
    history = round_history(worktree, prof, module, mid)
    rounds_text = f" What failed in each round: {' | '.join(history)}." if history else ""
    return (f"Diagnose {module} {mid}: it has failed review {rounds} times, mostly on findings no earlier round had "
            f"raised (plan-module, \"When reviews keep finding something new\"). {where}.{rounds_text} Decide why. If "
            f"the items are too broad or can't be met, change the definitions of {mid} and end with PLANNED as usual. "
            f"If the plan is right, change no file (your reasons go in the line itself) and end with "
            f"`KEEP {module} {mid}: builder: <why>`, "
            "`... reviewer: <why>` or `... owner: <why>`, naming who has to act: a builder who keeps breaking "
            "something, a reviewer whose findings go beyond the items, or the owner, for a decision only they can make.")


def keep_round(tree: Path, current: Path) -> tuple[str, list[str]]:
    """Keeps `current` (a review about to be replaced) as <name>-N.md beside it, reusing a copy `owner rereview`
    already made of the same text. Its captures folder <name>/ is copied beside it, to <name>-N/, and the kept file's
    links to it are rewritten, so each round keeps its own evidence. The folder itself stays, so the next round's
    captures are saved among the earlier ones, replacing any with the same name. Returns the kept file's path relative
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
    """The re-plan's bookkeeping, done by the script: each milestone that was owed a re-plan in `before` and whose
    definitions `after` changes gets fails 0, one more replans than before, and state open, whatever the planner or
    owner wrote there (so a forgotten count doesn't send the lead round again, and a done one isn't counted twice).
    Returns the milestones it settled, as `STEM Mn`."""
    old = {m.get("id"): m for m in (before or {}).get("milestones") or [] if isinstance(m, dict)}
    out = []
    for m in after.get("milestones") or []:
        was = old.get(m.get("id"))
        word = ladder(was) if was else "none"
        if word not in ("replan", "diagnose"):
            continue
        if definitions(was) == definitions(m):
            continue  # nothing re-planned yet: still owed
        m.update(fails=0, rounds=0, replans=int(was.get("replans", 0)) + 1, state="not_started",
                 diagnoses=int(was.get("diagnoses", 0) or 0) + (1 if word == "diagnose" else 0))
        m.pop("blocked", None)
        m.pop("findings", None)
        out.append(f"{stem} {m['id']}")
    return out


COUNTS = ("fails", "rounds", "replans", "diagnoses")


def keep_counts(before: dict | None, after: dict, settled: list[str], stem: str) -> None:
    """Puts back what a planner changed in the script's counts: on each milestone the plan didn't settle, the counts,
    `findings` and a Too Many Failed Reviews block as they were. A milestone split off a new one keeps the `replans` and `diagnoses`
    it was given, and starts with no failed rounds."""
    old = {m.get("id"): m for m in (before or {}).get("milestones") or [] if isinstance(m, dict)}
    for m in after.get("milestones") or []:
        if f"{stem} {m.get('id')}" in settled:
            continue
        was = old.get(m.get("id"))
        if was is None:
            m.update(fails=0, rounds=0)
            m.pop("findings", None)
            continue
        for k in COUNTS + ("findings",):
            if k in was:
                m[k] = was[k]
            else:
                m.pop(k, None)
        stuck = lambda x: x.get("state") == "blocked" and blocked_of(x)["reason"] == "too_many_failed_reviews"
        if stuck(was) or stuck(m):
            m["state"] = was.get("state")
            if "blocked" in was:
                m["blocked"] = was["blocked"]
            else:
                m.pop("blocked", None)


def ladder_next(word: str, module: str, mid: str, counts: dict, worktree: Path, prof: dict) -> dict:
    """`next` after a failed milestone review: the ladder's word under `ladder`, with the command it calls for.
    `counts` holds the milestone's fails, rounds and replans as the review left them."""
    wt = str(worktree)
    fails, rounds = int(counts.get("fails", 0) or 0), int(counts.get("rounds", 0) or 0)
    findings = FINDINGS_TEMPLATE.format(milestone=mid, module=module, evidence=prof["evidence"])
    tally = (f"{module} {mid} has failed review {plural(rounds, 'time')}, "
             f"{plural(fails, 'time')} on a finding an earlier round had raised")
    if word == "same-session":
        return next_cmd(loop_cmd("run", "--module", module, "--worktree", wt, "--message", findings), "lead",
                        f"{tally}: resume the builder with the findings", ladder=word)
    if word == "fresh-session":
        return next_cmd(loop_cmd("run", "--module", module, "--worktree", wt, "--fresh", "--message", findings),
                        "lead", f"{tally}: start the builder again in a new session with the findings", ladder=word)
    if word == "replan":
        return next_cmd(loop_cmd("plan", "--worktree", wt, "--task", replan_task(module, mid, fails, prof, worktree)),
                        "planner", f"{tally}, so the ladder calls for a re-plan; `run` won't start a builder on it "
                                   "until the planner has changed its definitions",
                        ladder=word, findings=f"{prof['evidence']}/{module}/{mid}-review.md")
    if word == "diagnose":
        return next_cmd(loop_cmd("plan", "--worktree", wt, "--task", diagnose_task(module, mid, rounds, prof, worktree)),
                        "planner", f"{tally}, so a planner decides why before any more building: it changes the "
                                   "definitions, or keeps them and names who has to act; `run` won't start a builder "
                                   "on it until then", ladder=word,
                        findings=f"{prof['evidence']}/{module}/{mid}-review.md")
    return reopen_next(module, mid, wt, worktree, prof, f"{tally}, and the ladder has run out")


def reopen_next(module: str, mid: str, wt: str, worktree: Path | None, prof: dict, how: str | None = None,
                after: int | None = None) -> dict:
    """The owner's decision on a milestone Blocked with too many failed reviews, with each round's failures so they
    can decide in one word. With no `how`, the reason and rounds the script recorded when it blocked it."""
    if how is None:
        held = {}
        if worktree is not None:
            try:
                rec = json.loads(show(worktree, base_ref(prof), record_rel(prof, module)) or "{}")
                held = ((rec.get("milestones") or {}).get(mid) or {}).get("too_many_failed_reviews") or {}
            except (json.JSONDecodeError, SystemExit):
                pass
        how = held.get("why") or "it ran out of review rounds"
        after = held.get("after", after)
    history = round_history(worktree, prof, module, mid, after)
    return owner_next("reopen", module, mid, wt,
                      f"{module} {mid} is Blocked with too many failed reviews: {how}. Accept it as it is, change its "
                      "scope, reopen it for another try, or leave it blocked?",
                      f"{how}, so the script blocked it. Report it to the owner with what failed in each round and "
                      "your recommendation. The decision is theirs: run `owner accept` or `owner scope` instead of "
                      "reopen if that is what they choose. Later milestones of the module wait until it is decided",
                      ladder="too_many_failed_reviews", **({"history": history} if history else {}))


def open_needs(milestone: dict, types: tuple = NEEDS_TYPES) -> list[str]:
    """The ids of the milestone's items that need someone (their `needs` type one of `types`) and haven't passed."""
    return [i["id"] for i in milestone.get("items") or []
            if isinstance(i.get("needs"), dict) and i["needs"].get("type") in types and i.get("status") != "pass"]


HELD_BY_SOMEONE = ("access", "hardware")  # done at the machine, not said, so nothing is recorded for them


def owner_decisions(stem: str, rec: dict) -> list[tuple[str, str]]:
    """(when, report line) for every decision recorded in the owner's name in a module's record: `decisions`, and
    the stamps older records kept instead (an owner action, feedback typed or relayed, a design accepted, a scope)."""
    out = [(d.get("at") or "", f"- {stem} {d.get('milestone')}" +
            (f" {', '.join(d['items'])}" if d.get("items") else f" {d['item']}" if d.get("item") else "") +
            f": {d.get('action')}, {d.get('at')}: " + (f"asked \"{d['asked']}\", said " if d.get("asked") else "") +
            f"\"{d.get('words')}\"") for d in rec.get("decisions") or []]
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
        for x in e.get("human_feedback") or []:
            if "by" in x:
                out.append((x.get("at") or "", f"- {stem} {mid}" + (f" {', '.join(x['items'])}" if x.get("items") else "")
                            + f": feedback, {x.get('at')}: \"{x.get('said')}\""))
    return out


def owner_cmd(verb: str, mod: str, mid: str, wt: str, items: list[str] | str | None = None) -> str:
    """The `owner` command the lead runs once the owner has decided in chat, with their words to fill in. Feedback
    also takes the question the lead asked, and every item the owner's words cover."""
    items = [items] if isinstance(items, str) else list(items or [])
    if verb == "feedback":
        return (loop_cmd("owner", "feedback", "--module", mod, "--milestone", mid,
                         *[x for i in items for x in ("--item", i)], "--worktree", wt) +
                " --asked '<the question you asked the owner>' --said '<what the owner said, in their words>'")
    return (loop_cmd("owner", verb, "--module", mod, "--milestone", mid, *[x for i in items for x in ("--item", i)],
                     "--worktree", wt) + " --text '<what the owner said, in their words>'")


def owner_next(verb: str, mod: str, mid: str, wt: str, ask: str, why: str, **more) -> dict:
    """A stop that needs the owner: what the lead asks them in chat (`ask`), and the command it runs on their reply.
    The lead runs the command (`by: lead`); `decides: owner` because the decision is theirs, in their words."""
    flag = "--said" if verb == "feedback" else "--text"
    return next_cmd(owner_cmd(verb, mod, mid, wt, more.pop("items", None)), "lead",
                    why + f". Ask the owner in chat; once they have replied, run the command with their words in "
                    f"{flag}, as they gave them, and never decide for them", ask=ask, decides="owner", **more)


def needs_ask(worktree: Path, prof: dict, proj: dict | None, mod: str, mid: str, items: list[str],
              note: str = "") -> str:
    """What the lead asks the owner about items that need human feedback: each item as the done-when file states it,
    what it needs judged, the builder's note, and where the evidence to show them is."""
    doc = ((proj or {}).get(mod.upper()) or {}).get("doc")
    if doc is None:
        try:
            doc = json.loads(show(worktree, base_ref(prof), done_rel(prof, mod)) or "{}")
        except json.JSONDecodeError:
            doc = {}
    m = next((x for x in doc.get("milestones") or [] if x.get("id") == mid), {})
    parts = []
    for item in items:
        i = next((x for x in m.get("items") or [] if x.get("id") == item), {})
        what = (i.get("needs") or {}).get("what") if isinstance(i.get("needs"), dict) else None
        evidence = i.get("evidence") or f"{prof['evidence']}/{mod}/"
        parts.append(f"{item}: {i.get('statement') or item}" + (f" ({what})" if what else "") +
                     f". Evidence to show them: {evidence}")
    return " ".join(parts) + (f" The builder's note: {note}" if note else "")


def visible_run(mod: str, wt: str) -> str:
    """The `run` command that starts the builder in a visible session, for items that need access or hardware."""
    return "ORCHESTRATE_VISIBLE=1 " + loop_cmd("run", "--module", mod, "--worktree", wt)


def worktree_roots(worktree: Path) -> list[str]:
    """The folders of every worktree of the repository, as git lists them and as they resolve, longest first."""
    out = git(worktree, "worktree", "list", "--porcelain").stdout if worktree else ""
    roots = {r for line in out.splitlines() if line.startswith("worktree ")
             for r in (line[len("worktree "):], str(Path(line[len("worktree "):]).resolve()))}
    roots |= {r[len("/private"):] for r in roots if r.startswith("/private/")}  # macOS's /var is /private/var
    return sorted(roots, key=len, reverse=True)


def repo_relative(text: str, roots: list[str]) -> str:
    """`text` with paths inside the repository's worktrees made relative to the repository, as every agent's
    checkout has them. In Thrum some Blocked messages linked to one builder's worktree, which other agents and the
    owner's page can't open."""
    for root in roots:
        text = re.sub(re.escape(root.rstrip("/")) + r"/(?=\S)", "", text)
    return text


def builder_work(worktree: Path, prof: dict | None = None) -> dict:
    """Where a stopped builder's unmerged work is: its branch and commit, recorded with the block so a planner, who
    runs in the script's own checkout and can't see the builder's folder, can read it with `git show`. With
    `Merge: push`, the branch is pushed too (never forced, and never the main branch), so a lead on another machine
    can read it; `pushed` says whether that worked."""
    head = git(worktree, "rev-parse", "HEAD")
    if head.returncode != 0:
        return {}
    branch = git(worktree, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    work = {"commit": head.stdout.strip(), **({"branch": branch} if branch and branch != "HEAD" else {})}
    if prof and prof.get("merge") == "push" and work.get("branch") and branch != prof["branch"]:
        p = git(worktree, "push", "--quiet", prof["remote"], f"HEAD:refs/heads/{branch}")
        work["pushed"] = p.returncode == 0
    return work


def sentence(text: str) -> str:
    """`text` ending in a full stop, so a note appended after it reads as a new sentence."""
    text = (text or "").strip()
    return text if not text or text[-1] in ".!?" else text + "."


def work_note(blocked: dict) -> str:
    """Where a stopped builder's handoff and work are, for the next agent's task."""
    b = blocked or {}
    w = b.get("work") or {}
    out = ""
    if b.get("handoff"):
        out += (f" The builder's handoff, {b['handoff']}, says what is finished, what was tried and what to do "
                "first.")
    if w.get("commit"):
        on = f"branch {w['branch']} at {w['commit'][:12]}" if w.get("branch") else f"commit {w['commit'][:12]}"
        out += f" Its work is on {on}, which isn't merged; read it with `git show`."
    return out


def next_for(step: dict, worktree: Path, prof: dict, proj: dict | None = None, seen: set | None = None) -> dict | None:
    """What to run after a step that isn't ready, from the same facts `next_step` read. A step Waiting On Dependency
    follows its first dependency to the module that has to move first."""
    wt, mod, mid, status = str(worktree), step["module"], step.get("milestone"), step["status"]
    reason = step.get("reason")
    if status == "ready":
        return next_cmd(loop_cmd("run", "--module", mod, "--worktree", wt), "lead",
                        f"{mod} {mid} is ready to build. Run it in the module's worktree; `run` fast-forwards a clean "
                        f"worktree that's behind {base_ref(prof)} itself, so there's no need to merge first")
    if status == "waiting" and reason in ("for_replan", "for_diagnosis"):
        return ladder_next(step.get("ladder", "replan"), mod, mid, step, worktree, prof)
    if status == "design_not_approved":
        record = ((proj or {}).get(mod.upper()) or {}).get("record")
        # with `Review host: other` and a known planner, the host decided as everywhere else (a review host the
        # lead chose for this module's run is added later, by fit_next); otherwise `review` decides it
        named = prof.get("review_host") == "other" and ((record or {}).get("planner") or {}).get("host") \
            and not known_run(wt, mod).get("review_host")
        host = ["--host", design_review_host(prof, record, default_host(prof))] if named else []
        return next_cmd(loop_cmd("review", "--module", mod, "--milestone", "design", "--worktree", wt, *host), "lead",
                        f"{mod}'s design hasn't passed a design review, or changed since it did")
    if status == "review_owed":
        if step.get("state") == "ready_for_review":
            return next_cmd(loop_cmd("review", "--module", mod, "--milestone", mid, "--commit",
                                     step.get("commit") or base_ref(prof), "--worktree", wt), "lead",
                            f"{mod} {mid} is Ready for Review")
        return owner_next("accept", mod, mid, wt,
                          f"{mod} {mid} says done in its file, but the script never accepted it. Accept it without a "
                          "review, or have a planner set it back to in_progress, so that the script checks it and a "
                          "reviewer judges it?",
                          f"{mod} {mid} says done in its file, but the script never accepted it")
    if status == "blocked":
        b = step.get("blocked") or {}
        what = repo_relative(b.get("what") or "", worktree_roots(worktree)) or "see the done-when file"
        items = b.get("items") or []
        work = work_note(b)
        if reason == "too_many_failed_reviews":
            return reopen_next(mod, mid, wt, worktree, prof)
        if reason == "needs_human_feedback":
            return owner_next("feedback", mod, mid, wt, needs_ask(worktree, prof, proj, mod, mid, items, what),
                              f"{mod} {mid} is Blocked: Needs Human Feedback on {', '.join(items) or 'its items'}. The "
                              "owner judges it: the lead shows them the evidence and asks the question. Their reply "
                              "goes into the record file, "
                              "where the builder reads it and the reviewer counts it as the owner's words, and puts the "
                              "milestone back in the queue; then `run` resumes the builder. Don't pass it through "
                              "`run --message`, because a reviewer can't tell those words from an agent's." + work,
                              items=items, then=loop_cmd("run", "--module", mod, "--worktree", wt))
        if reason in ("needs_access", "needs_hardware"):
            kind = "approve the access prompts" if reason == "needs_access" else "connect the device"
            return next_cmd(visible_run(mod, wt), "lead",
                            f"{mod} {mid} is Blocked: {reason.replace('_', ' ').capitalize()} ({what}). The owner "
                            f"has to be at the machine to {kind}, and the lead runs the builder again in a visible "
                            "session while they are. The visible run unblocks it; nothing is recorded, and the owner "
                            "isn't asked to confirm it."
                            + work,
                            ask=f"Are you at the machine to {kind} for {mod} {mid}? {what}")
        if reason == "needs_dependency":
            return next_cmd(loop_cmd("plan", "--worktree", wt, "--task",
                                     f"{mod} {mid} needs something no plan provides yet. The builder wrote: "
                                     f"{sentence(what)}" + work), "lead",
                            f"{mod} {mid} is Blocked: Needs Dependency ({what}). A planner adds it to the module "
                            "that owns it." + work,
                            alternative=loop_cmd("unblock", "--module", mod, "--milestone", mid, "--worktree", wt))
        return next_cmd(loop_cmd("run", "--module", mod, "--worktree", wt) + " --message '<the missing fact>'", "lead",
                        f"{mod} {mid} is Blocked: Needs Context ({what}). The lead finds the missing fact, or asks the "
                        "owner when only they know it, and resumes the builder with it in `run --message`, which "
                        "unblocks it. If another module owns it, or it's a design problem, a planner plans it "
                        "instead." + work,
                        alternative=loop_cmd("plan", "--worktree", wt, "--task",
                                             f"Unblock {mod} {mid}. The builder wrote: {sentence(what)}" + work))
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
        first = (step.get("depends_on") or [""])[0]
        other, _, rest = first.partition(":")
        if rest.endswith("(not planned)"):
            return next_cmd(loop_cmd("plan", "--worktree", wt, "--task", f"Plan module {other}"), "lead",
                            f"{mod} {mid} depends on {other}, which has no done-when file yet")
        why = f"{mod} {mid} depends on {', '.join(step.get('depends_on') or [])}, not Done yet"
        seen = (seen or set()) | {mod.upper()}
        if proj and other.upper() in proj and other.upper() not in seen:
            then = next_for(next_step(other.upper(), proj), worktree, prof, proj, seen)
            if then:
                return {**then, "why": f"{why}; {then['why']}"}
        return next_cmd(loop_cmd("run", "--module", other, "--worktree", wt), "lead", why)
    if status == "taken":
        return next_cmd(loop_cmd("ready", "--worktree", wt), "lead",
                        f"{mod} {mid} is held by {step.get('by')}; give the builder other ready work. If that lead is "
                        "gone for good, `owner release` frees it, once the owner says so in chat",
                        owner=owner_cmd("release", mod, mid, wt))
    return None


# The order `ready` looks for something to do when nothing is ready: a step's status, with its reason where that
# changes whose move it is.
NEXT_ORDER = ("review_owed", "waiting:for_replan", "waiting:for_diagnosis", "design_not_approved", "blocked", "invalid",
              "waiting:on_dependency", "taken", "blocked:too_many_failed_reviews")


def step_key(step: dict) -> str:
    """The step's place in NEXT_ORDER."""
    s, reason = step["status"], step.get("reason")
    return f"{s}:{reason}" if s == "waiting" or (s == "blocked" and reason == "too_many_failed_reviews") else s


def nothing_ready_next(steps: list[dict], worktree: Path, prof: dict, proj: dict, ahead: list[dict] = ()) -> dict:
    """For `ready` when nothing is: the most useful next command across the modules, or planning when there are
    none, or nothing when all are finished."""
    for status in NEXT_ORDER:
        for step in steps:
            if step_key(step) == status and (out := next_for(step, worktree, prof, proj)):
                return out
    if not steps:
        return next_cmd(loop_cmd("plan", "--worktree", str(worktree), "--task", "Plan the project"), "lead",
                        f"no done-when files at the main branch's tip, under {prof['plans']}")
    if ahead:
        return ahead[0]["next"]
    return next_cmd(None, "lead", "every module is finished; plan more work with `plan` if the build order "
                                  "isn't done")


def plan_ahead(worktree: Path, prof: dict, ref: str, proj: dict) -> list[dict]:
    """The modules to plan next, in build order: rows of the module table with no plan yet, whose Needs name only
    modules that are planned. Nobody plans a whole project up front, so planning keeps one step ahead of building:
    a module becomes worth planning once what it builds on is planned, and then a planner can run while builders do.
    Thrum, 13 Nov: `ready` held only the two milestones already building, while CONTENT-LOOP, which needs only
    APPLE-PRESENTATION, sat Not Planned Yet."""
    rows = module_table(show(worktree, ref, project_file(prof, "architecture"))) or []
    names = [r["module"].upper() for r in rows]
    by_n = {plain_cell(r["n"]): r["module"].upper() for r in rows}
    out = []
    for r in rows:
        if r["module"].upper() in proj:
            continue
        cell = plain_cell(r["needs"])
        needs = [m for m in names if m != r["module"].upper()
                 and re.search(rf"(?<![\w-]){re.escape(m)}(?![\w-])", cell.upper())]
        for listed in re.findall(r"\bmodules?\s+(\d+(?:\s*(?:,|and|to|-|–)\s*\d+)*)", cell, re.I):  # "modules 1 to 10"
            parts = re.findall(r"\d+|to|-|–", listed)
            for i, x in enumerate(parts):
                if x.isdigit() and i >= 2 and parts[i - 1] in ("to", "-", "–"):
                    numbers = range(int(parts[i - 2]) + 1, int(x) + 1)
                elif x.isdigit():
                    numbers = [int(x)]
                else:
                    continue
                needs += [by_n[str(n)] for n in numbers if by_n.get(str(n)) and by_n[str(n)] not in needs]
        if cell.strip("—–-. ").lower() not in ("", "none", "nothing") and not needs:  # it needs something, but nothing the script can name: the lead decides
            continue
        if all(m in proj for m in needs):
            task = f"Plan module {r['module']}" + (f". It needs: {plain_cell(r['needs'])}" if needs else "")
            out.append({"module": r["module"], "needs": needs,
                        "next": next_cmd(loop_cmd("plan", "--worktree", str(worktree), "--task", task), "lead",
                                         f"{r['module']} has no plan yet, and "
                                         + (f"{', '.join(needs)}, which it needs, {'is' if len(needs) == 1 else 'are'}"
                                            " planned" if needs else "it needs no other module")
                                         + "; a planner can plan it while builders run")})
    return out


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
    """Files under `folder` here that the main branch's tip doesn't have, uncommitted or committed but not merged.
    Only files whose content here differs from the tip's count, so a worktree that is merely behind reports none."""
    uncommitted = names(git(worktree, "diff", "-z", "--name-only", "HEAD", "--", folder))
    uncommitted |= names(git(worktree, "ls-files", "-z", "--others", "--exclude-standard", "--", folder))
    base = git(worktree, "merge-base", "HEAD", ref).stdout.strip()
    committed = names(git(worktree, "diff", "-z", "--name-only", base, "HEAD", "--", folder)) if base else set()
    differs = lambda rel: file_here(worktree, rel) != file_at(worktree, ref, rel)
    return {"uncommitted": sorted(p for p in uncommitted if differs(p)),
            "unmerged": sorted(p for p in committed - uncommitted if differs(p))}


def plan_drift(worktree: Path, prof: dict, ref: str) -> dict:
    """Plan files in this worktree that the main branch's tip doesn't have: uncommitted (edited, staged or untracked) or
    committed but not merged. `run` and `ready` read plans at the tip, so these are invisible to them. A settings file
    the tip doesn't have at all is part of a first plan, so it counts too. One the tip has in another form is only
    named, under `settings_differ`: the lead commits it once the owner has agreed."""
    out = folder_drift(worktree, prof["plans"], ref)
    for key in ("uncommitted", "unmerged"):  # the script writes STATUS.md itself; it never waits to be merged
        out[key] = [p for p in out[key] if p != status_rel(prof)]
    here, there = file_here(worktree, PROFILE_FILE), file_at(worktree, ref, PROFILE_FILE)
    if here is not None and there is None:
        key = "unmerged" if file_at(worktree, "HEAD", PROFILE_FILE) == here else "uncommitted"
        out[key] = sorted(out[key] + [PROFILE_FILE])
    # merely behind isn't a difference to commit: the project settings here must differ from this branch's own commit of it,
    # or that commit must have changed it since the branch left the tip (folder_drift's merge-base guard)
    base = git(worktree, "merge-base", "HEAD", ref).stdout.strip()
    committed = file_at(worktree, "HEAD", PROFILE_FILE)
    out["settings_differ"] = (here is not None and there is not None and here != there
                              and (here != committed or not base or committed != file_at(worktree, base, PROFILE_FILE)))
    return out


def profile_note(drift: dict, prof: dict) -> dict:
    """`settings_differ` for `ready`: the working copy's ORCHESTRATE.md isn't the one at the tip, which every clean
    checkout (builders, reviewers, the script's checks) reads."""
    if not drift.get("settings_differ"):
        return {}
    return {"settings_differ": f"this worktree's {PROFILE_FILE} differs from the one at {base_ref(prof)}, which "
                               "builders, reviewers and the script's checks read. The lead commits and merges a "
                               "changed settings file once the owner has agreed to it; the script doesn't merge it"}


def drift_fields(drift: dict, worktree: Path, step_next: dict | None = None) -> dict:
    """The fields a result carries when plan files haven't merged: the files, and `adopt` as the next command, with
    what would have been next anyway under `then`."""
    if not (drift["uncommitted"] or drift["unmerged"]):
        return {"next": step_next} if step_next else {}
    drift = {k: drift[k] for k in ("uncommitted", "unmerged")}
    files = drift["uncommitted"] + drift["unmerged"]
    note = (f"the script reads plans at the main branch's tip, and these plan files aren't there: {', '.join(files[:10])}"
            + (" (uncommitted)" if drift["uncommitted"] and not drift["unmerged"] else
               " (committed here, not merged)" if not drift["uncommitted"] else ""))
    return {"unmerged_plans": {**drift, "note": note},
            "next": next_cmd(loop_cmd("adopt", "--worktree", str(worktree)), "lead",
                             f"{note}. `adopt` commits only those plan files and merges them; then run this "
                             "again", **({"then": step_next} if step_next else {}))}


# -------------------------------------------------------------------------------------------- processes and locks

_STOP = False
_HELD = []  # open lock files, kept for the life of the process


def install_stop() -> None:
    """`pause` (SIGTERM) or Ctrl-C stops the current agent cleanly, and the script reports PAUSED."""
    def handler(signum, frame):
        global _STOP
        _STOP = True
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


KILL_GRACE_S = (10.0, 5.0)  # how long a stopped process group gets after SIGTERM, then after SIGKILL
RUN_POLL_S = 1.0  # how often a running turn's watch, tick, pause and turn limit are checked


def kill_group(proc: subprocess.Popen) -> None:
    for sig, wait in zip((signal.SIGTERM, signal.SIGKILL), KILL_GRACE_S):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=wait)
            return
        except subprocess.TimeoutExpired:
            continue


def stop_leftovers(pgid: int) -> None:
    """Stops what is left of a process group whose leader has exited."""
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(pgid, sig)
        except (ProcessLookupError, PermissionError):
            return
        for _ in range(50):
            time.sleep(0.1)
            try:
                os.killpg(pgid, 0)
            except (ProcessLookupError, PermissionError):
                return


def run_proc(args, cwd: Path | None, timeout_s: float, shell: bool = False,
             env: dict | None = None, tick=None, watch=None) -> tuple[int, str, str]:
    """Runs a command in its own process group, so a timeout or a pause stops everything it started. 124 means it
    timed out, 130 that it was stopped, 127 that the command couldn't start. `tick` is called about once a second
    while it runs.

    The output goes to files, not pipes. A builder once started a background process that kept the pipe open
    after its turn had finished, and the run waited on the pipe, holding the milestone, until the lead killed it.
    So the run ends when the command exits, and whatever of its group is left is stopped. `watch` gets each new
    piece of output, about once a second, and a non-empty answer ends the run as finished, with the answer noted
    in stderr: it is for a host whose turn is over while its process hasn't exited."""
    with tempfile.TemporaryDirectory(prefix="orchestrate-") as tmp:
        out_path, err_path = Path(tmp) / "out", Path(tmp) / "err"
        with open(out_path, "ab") as out_w, open(err_path, "ab") as err_w:
            try:
                proc = subprocess.Popen(args, shell=shell, cwd=cwd, stdin=subprocess.DEVNULL, stdout=out_w,
                                        stderr=err_w, start_new_session=True, env=env)
            except OSError as e:
                return 127, "", f"couldn't start {args[0] if isinstance(args, list) else args}: {e}"

        def output() -> tuple[str, str]:
            return (out_path.read_text(errors="replace"), err_path.read_text(errors="replace"))

        deadline, seen = time.time() + timeout_s, 0
        with open(out_path, "r", errors="replace") as reader:
            while True:
                try:
                    proc.wait(timeout=RUN_POLL_S)
                    stop_leftovers(proc.pid)
                    return (proc.returncode, *output())
                except subprocess.TimeoutExpired:
                    pass
                if tick:
                    tick()
                ended = watch(reader.read()) if watch else None
                if ended:
                    kill_group(proc)
                    out, err = output()
                    return 0, out, err + f"\n({ended})"
                if _STOP or time.time() > deadline:
                    kill_group(proc)
                    out, err = output()
                    return (130 if _STOP else 124), out, err + ("\n(stopped)" if _STOP else "\n(timed out)")


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
    turned away. It reads the pid the holder wrote, then checks that process is that run: by its own `runs` record
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
    """Who holds a run lock, for TAKEN: the pid and, from its `runs` record, its role, milestone, worktree and start.
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
# Every `run`, `review` and `plan` process keeps a small record of itself in one folder per user, so `runs` can list
# what's running in every repository, whichever copy of this script started it. The repository's own folder can't do
# that, because nothing would know which repositories to look in. A record counts only while its process holds the
# flock on the `.lock` beside it. Writing records is best effort: where the folder can't be written (a sandboxed home)
# the script runs exactly as before, and `runs` still finds it in the process table, with what its command line says.

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
               session_cost: float | None = None, err: str = "") -> None:
    """Appends the turn's tokens to the repository's usage ledger (<git common dir>/orchestrate/usage.jsonl), which
    `cost` and `report` read. Every turn goes in, paused and failed ones too, with `incomplete_turns` where the host
    showed no tokens or only some. A row also holds how full the turn left its session (`context` of `window`
    tokens), the script's `version`, from which `cost` dates its per-turn Codex figures, and for a failed turn the
    end of the host's `stderr`: in Thrum the lead couldn't tell a usage limit from an outage, because the failed
    turns' rows held nothing. Local to this machine; never fails the caller."""
    try:
        key = str(worktree)
        if key not in _COMMON:
            inside = subprocess.run(["git", "-C", key, "rev-parse"], capture_output=True).returncode == 0
            _COMMON[key] = git_common_dir(worktree) if inside else None
        if not _COMMON[key]:
            return
        line = {"at": now(), **{k: CONTEXT.get(k) for k in CONTEXT_KEYS}, "host": host, "model": model,
                "effort": effort, "session": session, "path": SESSION_PATH.get("path"), "exit": code,
                "usage": dict(TURN_USAGE), **({"session_cost_usd": session_cost} if session_cost is not None else {}),
                **dict(TURN_SIZE), "version": VERSION,
                **({"stderr": "\n".join(err.strip().splitlines()[-10:])[-800:]}
                   if code not in (0, 124, 130) and err.strip() else {})}
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
    """Starts this process's record. Never fails the caller: on any error the script simply has no record."""
    loop_end(run_locks=False)
    CONTEXT.clear()
    CONTEXT.update({"role": role, **{k: fields.get(k) for k in CONTEXT_KEYS if k != "role"}})
    try:
        common = git_common_dir(worktree)
        stamp = time.time()
        record = {"pid": os.getpid(), "role": role, "repository": repository_of(common), "git_dir": common,
                  "worktree": str(worktree), "module": None, "milestone": None, "host": None, "model": None,
                  "effort": None, "path": None, "started_at": stamp, "turns": 0, "activity_at": stamp,
                  "session": None, "transcript": None, "usage": {}, "script": str(LOOP),
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
    """Removes what a dead run left in the runs folder: its record and lock. Its run lock in the repository is
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
    and, for a build, what its run state shows once this run has written it. This finds runs that have no record:
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
        rec = {"pid": pid, "role": role, "script": argv[script], "repository": None, "worktree": worktree,
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
    to one repository. Records come first; with `processes`, runs found only in the process table follow, marked
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
        transcript = rec.get("transcript") or transcript_for(rec.get("host"), rec.get("session"))
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
    """One run as `runs --json` prints it."""
    stamp = time.time()
    started, last = rec.get("started_at"), rec.get("activity_at")
    out = {k: rec.get(k) for k in ("repository", "worktree", "module", "milestone", "role", "host", "model",
                                   "effort", "path", "pid")}
    out.update(started=iso(started), running_s=round(stamp - started) if started else None,
               turns=rec.get("turns"), last_activity=iso(last), idle_s=round(stamp - last) if last else None,
               tokens=rec.get("usage") or None, session=rec.get("session"), script=rec.get("script") or rec.get("loop"),
               registered=rec.get("registered", False))
    # Tokens arrive when a turn ends, and most sessions are one long turn, so say one is under way and for how long.
    turn = rec.get("turn_started_at")
    out["turn_running_s"] = round(stamp - turn) if turn else None
    # What the run is doing now, such as "builder turn 3" or "checking M1: M1.2", so the lead reports it rather
    # than guessing: in Thrum it told the owner a run was waiting for the GPU while a tool call had hung.
    out["step"] = rec.get("step")
    call = rec.get("open_tool_call") if turn else None
    if isinstance(call, dict) and call.get("name"):
        out["open_tool_call"] = {"name": call["name"], **({"input": call["input"]} if call.get("input") else {}),
                                 "open_s": round(stamp - call["opened_at"]) if call.get("opened_at") else None}
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
    now_ = f"\n    now: {v['step']}" if v.get("step") else ""
    if v.get("open_tool_call"):
        call = v["open_tool_call"]
        now_ += (", " if now_ else "\n    now: ") + f"waiting on the tool call {call['name']}" + \
            (f" for {ago(call['open_s'])}" if call.get("open_s") is not None else "")
    return head + (f"\n    started {ago(v['running_s'])} ago, {turns}, last activity {ago(v['idle_s'])} ago, "
                   f"{tokens}{now_}\n    worktree {v['worktree']}")


# --------------------------------------------------------------------------------------- merging, as the script

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


def drop_tree(worktree: Path, name: str) -> bool:
    """Removes the script's checkout `name` (a finished module's), with its build output. Disk is the cost of keeping
    a warm cache, and a finished module has nothing left to build; `verify_tree` makes it again if it's ever needed.
    True if there was one to remove."""
    path = loop_dir(worktree) / "verify" / name.upper()
    if not path.exists():
        return False
    if git(worktree, "worktree", "remove", "--force", str(path)).returncode != 0:
        shutil.rmtree(path, ignore_errors=True)
    git(worktree, "worktree", "prune")
    return True


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
    """Merges the commits in `tree` under the merge lock: rebase onto the base, optionally run the project's test
    command, then push (push) or fast-forward the local branch (local). Returns (ok, merged commit or the problem)."""
    detail = ""
    with held("merge", tree):
        for _ in range(2):
            if prof["merge"] == "push":
                f = git(tree, "fetch", "--quiet", prof["remote"], prof["branch"])
                if f.returncode != 0:
                    return False, f"git fetch failed: {f.stderr.strip()[-300:]}"
                git(tree, "update-ref", f"refs/remotes/{prof['remote']}/{prof['branch']}", "FETCH_HEAD")
            base = base_ref(prof)
            r = git(tree, *ident(tree), "rebase", "--quiet", base)
            if r.returncode != 0:
                git(tree, "rebase", "--abort")
                return False, f"rebase onto {base} failed: {(r.stdout + r.stderr).strip()[-400:]}"
            if check and prof["test_command"]:
                # Only the test command runs here, under the merge lock. The items' checks run later in the script's
                # own process, outside the builder's sandbox and outside this lock: in Thrum they took 35 to 49
                # minutes, which would have held every other builder's merge. A pass on these same files, from the
                # builder's `check`, isn't run again.
                r = run_check(tree, prof["test_command"], None, 3600, prof.get("plans"))
                if r["exit"] != 0:
                    whole = f" Its whole output is in {r['stdout']} and {r['stderr']}." if r["stdout"] else ""
                    return False, (f"Test command `{prof['test_command']}` exited {r['exit']}.{whole} The end of its "
                                   f"stdout: {r['out'][-400:]} The end of its stderr: {r['err'][-400:]}")
            new = head_commit(tree)
            if prof["merge"] == "push":
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
               trailer: bool = True, take_up_ok: bool = True) -> tuple[bool, str]:
    """Applies `change(tree)` to a clean checkout of the main branch's tip, commits it as the script, and merges it.
    `change` returns the paths it wrote, or nothing to skip the commit. Without `trailer` the commit isn't marked as
    the script's own record-keeping (used for files the script merges on someone's behalf). After a record merges (with
    `trailer`), STATUS.md is brought up to date in a commit of its own, which can't fail the record. Without
    `take_up_ok`, the first commit in a repository with no records doesn't write the records `take_up` would."""
    detail = ""
    for _ in range(2):
        try:
            tree = verify_tree(worktree, name, tip(worktree, prof))
        except TipError as e:
            return False, str(e)
        legacy = trailer and take_up_ok and unrecorded(tree, prof, "HEAD")
        paths = change(tree)
        if not paths:
            return True, head_commit(tree)
        if legacy:
            paths = [*paths, *take_up(tree, prof)]
        git(tree, "add", "-A", "--", *paths)
        c = git(tree, *ident(tree), "commit", "--quiet", "-m", f"{message}\n\n{TRAILER}" if trailer else message)
        if c.returncode != 0:
            return False, f"commit failed: {(c.stdout + c.stderr).strip()[-300:]}"
        ok, detail = land(tree, prof)
        if ok:
            if trailer:
                land_status(worktree, prof, name, tree)
            return True, detail
    return False, detail


def record_in(tree: Path, prof: dict, stem: str, doc: dict) -> dict:
    path = tree / record_rel(prof, stem)
    if path.exists():
        return json.loads(path.read_text())
    return adopt(doc, text_hash((tree / design_rel(prof, stem)).read_text()
                                if (tree / design_rel(prof, stem)).exists() else None),
                 unrecorded(tree, prof, "HEAD"))


def loop_versions(worktree: Path, rel: str, old: str, new: str, limit: int = 50) -> list[dict]:
    """The file at `rel` as each commit the script made between two tips left it, with old names upgraded. A builder pushes to the same branch, so
    the base's copy alone can't tell a planner's or reviewer's change from the builder's own."""
    out = git(worktree, "log", f"-{limit}", "--format=%H%x00%B%x01", f"{old}..{new}").stdout
    versions = []
    for chunk in out.split("\x01"):
        sha, _, body = chunk.strip().partition("\x00")
        if sha and any(t in body for t in TRAILERS) and (text := show(worktree, sha, rel)):
            try:
                versions.append(upgrade_doc(json.loads(text)))
            except json.JSONDecodeError:
                pass
    return versions


def record_tampering(worktree: Path, prof: dict, old: str, new: str) -> list[str]:
    """Commits between two tips that changed a record file without being the script's."""
    out = git(worktree, "log", "--format=%H%x00%B%x01", f"{old}..{new}", "--",
              records_glob(prof)).stdout
    bad = []
    for chunk in out.split("\x01"):
        sha, _, body = chunk.strip().partition("\x00")
        if sha and not any(t in body for t in TRAILERS):
            bad.append(sha[:12])
    return bad


# ---------------------------------------------------------------------------------------------- holds across clones

def me(worktree: Path) -> str:
    return f"{socket.gethostname()}:{git_common_dir(worktree)}"


def sync_holds(worktree: Path, prof: dict) -> None:
    if prof["merge"] == "push":
        git(worktree, "fetch", "--quiet", "--prune", prof["remote"], f"+{HOLDS}/*:{HOLDS}/*")


def holds(worktree: Path) -> dict[tuple[str, str], str]:
    out = {}
    for line in git(worktree, "for-each-ref", "--format=%(refname)\t%(contents:subject)", HOLDS).stdout.splitlines():
        ref, _, holder = line.partition("\t")
        parts = ref[len(HOLDS) + 1:].split("/")
        if len(parts) == 2:
            out[(parts[0].upper(), parts[1])] = holder
    return out


def take_hold(worktree: Path, prof: dict, key: str, mid: str) -> tuple[bool, str]:
    """Holds the milestone with a ref no other lead can create at the same time: a new ref on the remote (push),
    or a local ref created only if absent (local). Two leads never start the same milestone."""
    sync_holds(worktree, prof)
    mine = me(worktree)
    holder = holds(worktree).get((key, mid))
    if holder:
        return holder == mine, holder
    empty = git(worktree, "mktree", stdin="").stdout.strip()
    sha = git(worktree, *ident(worktree), "commit-tree", empty, "-m", mine).stdout.strip()
    ref = f"{HOLDS}/{key}/{mid}"
    if prof["merge"] == "push":
        if git(worktree, "push", "--quiet", prof["remote"], f"{sha}:{ref}").returncode != 0:
            sync_holds(worktree, prof)
            holder = holds(worktree).get((key, mid), "another lead")
            return holder == mine, holder
        git(worktree, "update-ref", ref, sha)
        return True, mine
    if git(worktree, "update-ref", ref, sha, "0" * 40).returncode != 0:
        holder = holds(worktree).get((key, mid), "another lead")
        return holder == mine, holder
    return True, mine


def drop_hold(worktree: Path, prof: dict, key: str, mid: str) -> None:
    ref = f"{HOLDS}/{key}/{mid}"
    if prof["merge"] == "push":
        git(worktree, "push", "--quiet", prof["remote"], f":{ref}")
    git(worktree, "update-ref", "-d", ref)


# ---------------------------------------------------------------------------------------------- Ready for Review


def ready_record(entry: dict | None) -> dict:
    """A milestone's Ready for Review record in the record file: the commit, the checks the script ran on it and the
    builder's tokens. Records written before 2.1.0 keep it under `claim`, until `migrate` renames it."""
    entry = entry or {}
    return entry.get("ready_for_review") or entry.get("claim") or {}


def state_at(worktree: Path, commit: str, rel: str, mid: str) -> str | None:
    """The state of milestone `mid` in the done-when file `rel` at `commit`, or None if it can't be read."""
    try:
        doc = upgrade_doc(json.loads(show(worktree, commit, rel) or ""))
        return find(doc, mid).get("state")
    except (ValueError, TypeError, AttributeError, KeyError, SystemExit):
        return None


def ready_current(entry: dict | None) -> bool:
    """Whether the milestone's Ready for Review record belongs to its current round: there is one, and no failed
    review came after it. A failed review leaves the old record in place, so a milestone set Ready for Review again
    without the script's checks would otherwise look checked."""
    ready = ready_record(entry)
    if not ready:
        return False
    last = ((entry or {}).get("reviews") or [{}])[-1]
    return not (last.get("verdict") == "fail" and (last.get("at") or "") >= (ready.get("at") or ""))


# Each check's full output is saved under <git common dir>/orchestrate/checks/, and a pass is remembered by the files
# it ran on and its command. In Thrum a builder asked for a failed check's full output, because the panic wasn't in
# the 30 lines its message held (N3); and the checks at the end of one milestone ran three times on the same files,
# once for the builder's `check`, once for `merge` and once for the script, which took 35 minutes (N4).
CHECKS_DIR = "checks"
CHECK_TAIL_LINES = 30


def files_key(tree: Path, plans: str | None) -> str | None:
    """A hash of the files checked out in `tree`, leaving out the plans folder, or None when anything outside the
    plans folder has uncommitted or untracked changes. The plans folder is left out because a builder ticks items
    and writes evidence paths there after its checks have run, and the script commits STATUS.md there, and none of
    that changes what a check tests. Ignored files, such as build output, aren't part of it either."""
    plans = (plans or "").rstrip("/") + "/" if plans else None
    if (r := git(tree, "status", "--porcelain", "-z")).returncode != 0:
        return None
    changed = [p[3:] for p in r.stdout.split("\0") if len(p) > 3]
    if any(not (plans and p.startswith(plans)) for p in changed):
        return None
    listing = git(tree, "ls-tree", "-r", "HEAD")
    if listing.returncode != 0:
        return None
    kept = [line for line in listing.stdout.splitlines()
            if not (plans and line.partition("\t")[2].startswith(plans))]
    return text_hash("\n".join(kept))


def run_check(tree: Path, command: str, lock: str | None, timeout_s: float, plans: str | None = None,
              save: bool = True) -> dict:
    """Runs one check in `tree`, under `lock` if it names one, unless the same command already passed on the same
    files, and saves its stdout and stderr to files under `<git common dir>/orchestrate/checks/`. Returns `exit`,
    `out` and `err` (empty for a reused pass), `stdout` and `stderr` (the saved files' paths, when they could be
    written) and `reused`. A pass is remembered only when the check left the files as it found them, since a check
    that writes files fails the script's clean-checkout test. Nothing is saved for a folder outside git."""
    folder = None
    if save:
        try:
            folder = loop_dir(tree) / CHECKS_DIR
            folder.mkdir(parents=True, exist_ok=True)
        except OSError:
            folder = None
    key = files_key(tree, plans) if folder else None
    name = text_hash(command)[:16]
    memo = folder / f"{key[:24]}-{name}.json" if key else None
    if memo and memo.exists():
        try:
            saved = json.loads(memo.read_text())
        except (OSError, ValueError):
            saved = {}
        if saved.get("exit") == 0 and saved.get("command") == command:
            return {"exit": 0, "out": "", "err": "", "stdout": saved.get("stdout"), "stderr": saved.get("stderr"),
                    "reused": saved.get("at") or True}
    if lock:
        with held(lock, tree):
            code, out, err = run_proc(command, tree, timeout_s, shell=True)
    else:
        code, out, err = run_proc(command, tree, timeout_s, shell=True)
    paths = {"stdout": None, "stderr": None}
    if folder:
        stem = f"{(key or 'changed')[:24]}-{name}" + ("" if key else f"-{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}")
        try:
            for field, text in (("stdout", out), ("stderr", err)):
                path = folder / f"{stem}.{field}"
                path.write_text(text)
                paths[field] = str(path)
        except OSError:
            pass
    if memo and code == 0 and files_key(tree, plans) == key:
        try:
            write_json(memo, {"command": command, "exit": 0, "at": now(), **paths,
                              "role": os.environ.get("ORCHESTRATE_ROLE") or "script"})
        except OSError:
            pass
    return {"exit": code, "out": out, "err": err, **paths, "reused": False}


def stream_end(text: str, lines: int = CHECK_TAIL_LINES) -> str:
    return "\n".join(text.rstrip().splitlines()[-lines:]) or "(nothing)"


def check_failures(tree: Path, prof: dict, milestone: dict, timeout_s: float = 3600,
                   reused: list | None = None) -> list[str]:
    """Runs the project's test command, then each item's check (under its lock, if it names one), in the script's
    own process, never under the merge lock. Returns what failed, each with the end of its stdout and its stderr
    shown apart and the files that hold them whole. A check that already passed on the same files isn't run again;
    its label goes in `reused`."""
    runs = [("Test command", prof.get("test_command"), None)] if prof.get("test_command") else []
    runs += [(i["id"], i["check"], i.get("lock")) for i in milestone["items"] if i.get("check")]
    failed = []
    for label, command, lock in runs:
        loop_note(step=f"checking {milestone.get('id')}: " + ("the test command" if label == "Test command" else label))
        r = run_check(tree, command, lock, timeout_s, prof.get("plans"))
        if r["reused"] and reused is not None:
            reused.append(label)
        if r["exit"] != 0:
            whole = (f" Its whole output is in {r['stdout']} (stdout) and {r['stderr']} (stderr)."
                     if r["stdout"] and r["stderr"] else "")
            failed.append(f"{label} `{command}` " + ("timed out" if r["exit"] == 124 else f"exited {r['exit']}") +
                          f".{whole}\nThe end of its stdout:\n{stream_end(r['out'])}\n"
                          f"The end of its stderr:\n{stream_end(r['err'])}\n")
    return failed


SCRIPT_SETS_STATE = ("Only the script sets a milestone to Ready for Review or Done, once its own checks pass on the "
                     "merged work. A builder leaves the state in_progress. Set {what} back to in_progress in {done}, "
                     "commit that, and run `merge` again. Then end your turn with DONE, and the script checks the "
                     "work and sets the state itself.")


def states_set(worktree: Path, prof: dict, old: str, new: str = "HEAD") -> list[tuple[str, str, str]]:
    """(done-when file, milestone, state) for each milestone that the commits between `old` and `new` set to
    ready_for_review or done. Builders did that before 2.1.0, and some branches still carry such a commit. Only a
    milestone the main branch already holds counts: a builder can't add one, so a new module or milestone came from a
    planner, or from another repository, and its state isn't a builder's to have set."""
    found = []
    for rel in git(worktree, "diff", "--name-only", old, new).stdout.split():
        if (module_of(prof, rel) or (None, None))[1] != "done":
            continue
        try:
            before = upgrade_doc(json.loads(show(worktree, old, rel) or '{"milestones": []}'))
            after = upgrade_doc(json.loads(show(worktree, new, rel) or '{"milestones": []}'))
        except (ValueError, TypeError, AttributeError):
            continue
        was = {m.get("id"): m.get("state") for m in before.get("milestones") or [] if isinstance(m, dict)}
        for m in after.get("milestones") or []:
            if isinstance(m, dict) and m.get("state") in ("ready_for_review", "done") and \
                    m.get("id") in was and was[m.get("id")] != m.get("state"):
                found.append((rel, m.get("id"), m["state"]))
    return found


def state_refusal(found: list[tuple[str, str, str]], old_branch: bool = False) -> str:
    """What a builder is told when its commits set a milestone's state, which only the script does now. With
    `old_branch`, the commits are in the worktree when its run starts, left by a builder before 2.1.0."""
    what = ", ".join(f"{mid} to {state}" for _, mid, state in found)
    rels = sorted({rel for rel, _, _ in found})
    said = (f"Commits in this worktree that haven't merged yet set {what}, as builders did before 2.1.0. "
            if old_branch else f"Your commits set {what}. ")
    return (said + SCRIPT_SETS_STATE.format(
        what="the state" if len(found) == 1 else "each state", done=" and ".join(rels)))


def ready_problems(worktree: Path, prof: dict, stem: str, milestone: dict, done: dict, authorised_hash: str,
                   start_tip: str, reused: list | None = None) -> tuple[list[str], str | None]:
    """Why the script can't set the milestone to Ready for Review yet, and the main branch's tip the checks ran on.
    The builder merges its work with the milestone still in progress, and the script then runs the checks on the
    tip in its own clean checkout. A milestone the tip already says is Ready for Review, from a builder before 2.1.0,
    is checked the same way."""
    missing = [i["id"] for i in milestone["items"] if not i.get("evidence")]
    if missing:
        return ["items marked pass with no evidence: " + ", ".join(missing)], None
    status = git(worktree, "status", "--porcelain").stdout.strip()
    if status:
        return ["uncommitted or untracked files (commit, remove or ignore them): " + status[:300]], None
    try:
        ref = tip(worktree, prof)
    except TipError as e:
        return [f"{e}, so the merge can't be checked"], None
    if not is_ancestor(worktree, "HEAD", ref):
        base = git(worktree, "merge-base", "HEAD", ref).stdout.strip()
        if base and (found := states_set(worktree, prof, base)):
            return [state_refusal(found)], None
        return [f"HEAD is not on {base_ref(prof)} yet; merge with `python3 {LOOP} merge --worktree .`"], None
    if bad := record_tampering(worktree, prof, start_tip, ref):
        return [f"commits changed a record file, which only the script writes: {', '.join(bad)}"], None
    try:
        at_tip = find(json.loads(show(worktree, ref, done_rel(prof, stem)) or "{}"), milestone["id"])
    except (json.JSONDecodeError, KeyError, SystemExit):
        return [f"{milestone['id']} can't be read at the main branch's tip"], None
    if definitions(at_tip) != authorised_hash:
        return [f"{milestone['id']}'s definitions at the main branch's tip aren't the authorised ones"], None
    try:
        tree = verify_tree(worktree, stem, ref)
    except TipError as e:
        return [str(e)], None
    failures = check_failures(tree, prof, milestone, reused=reused)
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


def last_event(path: Path | None, marker: str, accept=lambda event: True, block: int = 1 << 16) -> dict | None:
    """The last line of `path` that contains `marker`, parses, and passes `accept`. It reads from the end, because a
    rollout file can hold hundreds of megabytes of screenshots and the line wanted is near the end."""
    try:
        with open(path, "rb") as handle:
            end = handle.seek(0, os.SEEK_END)
            rest = b""
            while end > 0:
                start = max(0, end - block)
                handle.seek(start)
                lines = (handle.read(end - start) + rest).split(b"\n")
                rest = lines.pop(0) if start else b""  # the first piece may be the end of an earlier line
                for line in reversed(lines):
                    if marker.encode() in line:
                        try:
                            event = json.loads(line)
                        except ValueError:
                            continue  # the last line may be mid-write
                        if isinstance(event, dict) and accept(event):
                            return event
                end = start
    except (OSError, TypeError):
        pass
    return None


def session_tokens(host: str, session: str | None, stdout: str = "") -> dict:
    """What a session's host says about its tokens, as far as it says: `total`, the session's running total
    (Codex only), `context`, how full the session is, which is the size of its last request with the reply, and
    `window`, the most the session can hold. Codex writes all three in the `token_count` events of the session's
    rollout file, and the script reads the last one. Claude puts each message's usage in its stream, and the window
    in its `result` event, so a Claude turn's `stdout` is read instead. Missing figures are left out."""
    out: dict = {}
    if host == "codex" and session:
        event = last_event(rollout_for(session), '"token_count"',
                           lambda e: isinstance(((e.get("payload") or {}).get("info") or {}).get("total_token_usage"),
                                                dict))
        if event:
            info = event["payload"]["info"]
            total, last = info["total_token_usage"], info.get("last_token_usage") or {}
            cached = total.get("cached_input_tokens") or 0
            # Codex's input_tokens includes the cached ones, as in `turn.completed`.
            out["total"] = {"input": max((total.get("input_tokens") or 0) - cached, 0), "cached": cached,
                            "output": total.get("output_tokens") or 0}
            if last.get("total_tokens") or last.get("input_tokens"):
                out["context"] = last.get("total_tokens") or (last.get("input_tokens") or 0) + \
                    (last.get("output_tokens") or 0)
            if isinstance(info.get("model_context_window"), int):
                out["window"] = info["model_context_window"]
    elif host == "claude":
        last, windows = None, []
        for line in stdout.splitlines():
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            if event.get("type") == "assistant" and isinstance((event.get("message") or {}).get("usage"), dict) \
                    and not event.get("parent_tool_use_id"):  # a subagent's messages are in its own session
                last = event["message"]["usage"]
            elif event.get("type") == "result" and isinstance(event.get("modelUsage"), dict):
                windows = [m.get("contextWindow") for m in event["modelUsage"].values()
                           if isinstance(m, dict) and isinstance(m.get("contextWindow"), int)]
        if last is None and session:  # a turn stopped before it printed anything still wrote its transcript
            found = last_event(claude_transcript(session), '"usage"', lambda e: e.get("type") == "assistant")
            last = ((found or {}).get("message") or {}).get("usage")
        if isinstance(last, dict):
            out["context"] = sum(last.get(k) or 0 for k in ("input_tokens", "cache_creation_input_tokens",
                                                             "cache_read_input_tokens", "output_tokens"))
        if windows:
            out["window"] = max(windows)  # a subagent on a smaller model has its own entry
    return out


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
# from elsewhere); the script adds what only it knows: which threads are its own, what each milestone cost, and what the
# open milestones are likely to cost before the reset.

LOOP_PROMPT = re.compile(r"milestone (\S+) of module (\S+?)[ .,]")
LOOP_TITLE = re.compile(r"^(?:(build|review) (\S+) (\S+)|.+ · (\S+) · (\S+) (build|review))$")


def title_parts(title: str | None) -> tuple[str, str, str] | None:
    """(role, module, milestone) from a title the script gave a session, in the current form
    ('<repository> · <MODULE> · <milestone> <role>') or the form before 1.7.0 ('<role> <MODULE> <milestone>')."""
    m = LOOP_TITLE.match(title or "")
    if not m:
        return None
    return (m.group(1), m.group(2), m.group(3)) if m.group(1) else (m.group(6), m.group(4), m.group(5))


def repository_name(worktree: Path) -> str:
    """The repository's folder name, the same from every worktree of it: 'thrum' for /x/thrum/.git."""
    try:
        common = Path(git_common_dir(worktree))
    except Exception:
        return worktree.name
    return common.parent.name if common.name == ".git" else common.name.removesuffix(".git")


def plan_title(worktree: Path, tree: Path, prof: dict, task: str) -> str:
    """A planner's title: grouped with the module its task names first, or under 'plan' when it names none."""
    line = task.splitlines()[0] if task.strip() else ""
    named = [(m.start(), stem) for stem in modules_here(tree, prof)
             for m in [re.search(rf"(?<![\w-]){re.escape(stem)}(?![\w-])", line, re.IGNORECASE)] if m]
    return session_title(worktree, min(named)[1] if named else "plan", f"plan: {line[:60]}")


def session_title(worktree: Path, module: str, phase: str) -> str:
    """The title of a session the script starts: '<repository> · <MODULE> · <phase>', such as
    'thrum · CREATOR · M1 build' or 'thrum · CREATOR · design review'. The owner sees every session in one list
    sorted by title, so the repository comes first and then the module, which groups each module's sessions together,
    and the milestone comes before the role, so a milestone's build and review sit next to each other."""
    return f"{repository_name(worktree)} · {module} · {phase}"
QUOTA_BUDGET_S = 2.0          # reading budget on a result line; `quota` takes longer and warms the cache
QUOTA_WORKTREE: list = []     # the worktree a command runs on, for the result line's plan forecast


def note_thread(worktree: Path, host: str, session: str | None, role: str, title: str) -> None:
    """Appends a session the script started to the repository's thread ledger, so the forecast can tell its own threads
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
    """{thread: {module, milestone, role}} for every thread the script ran, from its ledger and state files, and
    (for threads from before the ledger) the script's own titles and objective wording. Auto-review and sub-agent
    threads count with the script thread they served. `here` marks the threads this repository ran: those in its own
    ledger and state files, and those whose folder is one of its worktrees or under its git dir; the rest are
    runs in other repositories, which count toward the machine's orchestrate use but never toward this one's milestones."""
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
            m = title_parts(d.get("title"))
            own[d["thread"]] = {"module": m and m[1], "milestone": m and m[2], "role": d.get("role"),
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
        title = title_parts(meta.get("name"))
        prompt = next((LOOP_PROMPT.search(p) for p in meta.get("prompts") or [] if LOOP_PROMPT.search(p)), None)
        mine = here(meta.get("cwd"))
        if title:
            own[tid] = {"module": title[1], "milestone": title[2], "role": title[0], "here": mine}
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
    read from the done-when files at the last-fetched main branch tip (no fetch)."""
    prof = profile(worktree, missing_ok=True)
    ref = base_ref(prof) if git(worktree, "rev-parse", "--verify", "-q", base_ref(prof)).returncode == 0 else "HEAD"
    proj = project(worktree, prof, ref)
    if not proj:  # e.g. a checkout still on an old layout: say so, rather than forecast 0 open milestones
        return [], [], {"plans_at": ref, "plan_unavailable": f"no plans found at {ref} from {worktree} (no "
                        "ORCHESTRATE.md or no plans folder there); pass --worktree with a checkout on the current "
                        "main branch"}
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
    behind_blocked = 0
    for key, e in sorted(proj.items()):
        doc = e["doc"]
        held = False
        for m in doc.get("milestones") or [] if isinstance(doc, dict) else []:
            if not isinstance(m, dict) or "id" not in m:
                continue
            state = m.get("state")
            held = held or (state == "blocked" and blocked_of(m)["reason"] == "too_many_failed_reviews")
            done = state == "done" or accepted(m, e["record"])
            g = by_ms.get((key, m["id"]))
            row = {"module": e["stem"], "milestone": m["id"], "state": state,
                   "rounds": (m["rounds"] if "rounds" in m else m.get("fails") or 0) + 1}
            if g:
                row.update(pct=codex_quota.cost(g["tokens"], fit), turns=g["turns"], builder_hours=round(g["hours"], 1))
                history.append(row)
            if not done and not (state == "blocked" and blocked_of(m)["reason"] == "too_many_failed_reviews"):
                if held:
                    behind_blocked += 1  # milestones run in order, so these wait on the owner
                else:
                    open_ms.append(row)
    return history, open_ms, {"plans_at": ref, "behind_blocked": behind_blocked}


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
    threads not the script's, and usage from elsewhere) at its rate over the last RECENT_H hours, against what's left
    before the reset. `recent` holds {"runs": [lo, mid, hi], "other": [lo, mid, hi], "hours": h} for that span."""
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
    """The full quota picture: the account (codex_quota), the script's own and other use this window, what milestones
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
        "covers": {"runs_pct": "Codex threads any orchestrate run on this machine ran (this repository's, found by "
                               "its ledger, and other repositories', found by the script's thread titles and prompts)",
                   "other_local_pct": "every other Codex thread on this machine (your own chats, other tools)",
                   "elsewhere_pct": "usage on this account that no local rollout explains (other machines, the "
                                    "web, cloud tasks)"},
        "runs_pct": own_pct, "other_local_pct": local_pct, "elsewhere_pct": acc["outside"]["pct"],
        "runs_apart": bool(worktree),
        "other_local_threads": [{"thread": t, "name": names.get(t, {}).get("name") or names.get(t, {}).get("cwd"),
                                 "pct": codex_quota.cost(by_thread[t], fit)} for t in top_other]}
    since = max(lo, now_s - RECENT_H * 3600)
    recent_h = max(1.0, (now_s - since) / 3600)
    recent_tokens = codex_quota.tokens_by(reading, lambda r: r["thread"] in own, since, now_s)
    elsewhere = sum(j["outside"] for j in fit.get("outside") or [] if j["t1"] >= since)
    recent = {"hours": recent_h,
              "runs": codex_quota.cost(recent_tokens.get(True, [0, 0, 0]), fit) or [0.0] * 3,
              "other": [x + elsewhere for x in codex_quota.cost(recent_tokens.get(False, [0, 0, 0]), fit) or [0.0] * 3]}
    acc["recent"] = {"hours": round(recent_h, 1), "runs_pct": recent["runs"], "other_pct": recent["other"],
                     "burn": codex_quota.burn(reading, fit, since, now_s, elsewhere)}
    acc["rate"] = quota_rate(acc["used_percent"], acc["hours_left"], recent)
    history, open_ms, notes = [], [], {}
    if worktree:
        try:
            history, open_ms, notes = milestone_costs(worktree, reading, fit, own)
        except (SystemExit, Exception) as e:  # no settings file, no plans: the account picture still stands
            notes = {"plan_unavailable": f"{type(e).__name__}: {e}"}
        acc["milestones"] = history
    else:
        notes = {"plan_unavailable": "no --worktree, so no plan to cost"}
    acc["forecast"] = {**plan_forecast(acc, history, open_ms, recent), **notes}
    if notes.get("plan_unavailable"):  # the milestone forecast would count other use only, so the rate stands alone
        short = acc["rate"]["left_at_reset_pct"][0] <= 0
        acc["forecast"].update(open_milestones=None, warn=short,
                               verdict=f"No milestone forecast: {notes['plan_unavailable']}. The rate above is the "
                                       "forecast" + (", and at its fastest it runs out before the reset." if short
                                                     else "."))
    return acc


def quota_rate(used: float, hours_left: float, recent: dict) -> dict:
    """What is left, how fast it is going, and what that leaves at the reset: all use on the account (orchestrate
    runs, other Codex threads, usage from elsewhere) over the last RECENT_H hours, carried on to the reset."""
    left = max(0.0, 100.0 - used)
    spent = [recent["runs"][i] + recent["other"][i] for i in range(3)]
    per_h = [x / recent["hours"] for x in spent]
    return {"left_pct": round(left, 1), "hours_left": round(hours_left, 1), "over_hours": round(recent["hours"], 1),
            "used_pct": [round(x, 2) for x in spent], "pct_per_hour": [round(x, 2) for x in per_h],
            "left_at_reset_pct": [round(max(0.0, left - x * hours_left), 1) for x in reversed(per_h)]}


def rate_line(acc: dict) -> str:
    """The quota in one sentence, as a rate: e.g. 21% left and 28 h to the reset; 0.16%/h over the last 12 h;
    about 16% left at the reset at that rate."""
    r = acc.get("rate")
    if not r:
        return f"{max(0.0, 100.0 - acc['used_percent']):.0f}% left and {acc['hours_left']:.0f} h to the reset."
    lo, mid, hi = r["left_at_reset_pct"]
    at_reset = f"about {mid:.0f}% left at the reset" + (f" ({lo:.0f}%-{hi:.0f}%)" if round(lo) != round(hi) else "")
    if mid <= 0:
        hours = r["left_pct"] / r["pct_per_hour"][1] if r["pct_per_hour"][1] else 0
        at_reset = f"it runs out in about {hours:.0f} h, before the reset"
    return (f"{r['left_pct']:.0f}% left and {r['hours_left']:.0f} h to the reset. All use on the account ran at "
            f"{r['pct_per_hour'][1]:.2f}%/h over the last {r['over_hours']:.0f} h ({r['used_pct'][1]:.1f}% in all); "
            f"at that rate, {at_reset}.")


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
    """The result line's few fields: the rate line, used, reset, recent burn, a one-sentence verdict, and whether to warn."""
    if not acc:
        return None
    f = acc["forecast"]
    recent = acc["recent"]["burn"].get("per_active_hour")
    out = {"rate": rate_line(acc), "used_percent": acc["used_percent"], "resets_at": acc["resets_at"],
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
    lines = [s["rate"], s["verdict"] or "No verdict.",
             f"Codex weekly limit: {acc['used_percent']:.0f}% used, resets {acc['resets_at']} "
             f"(in {acc['hours_left']:.0f} h). Burn: {s['burn']}."]
    if use and not use.get("runs_apart", True):
        lines.append(f"Used this window: about {pct(mid(use.get('other_local_pct')))} by Codex threads on this machine "
                     f"(the script's not told apart without --worktree), {pct(use.get('elsewhere_pct') or 0)} from "
                     "elsewhere (other machines, web, cloud).")
    elif use:
        lines.append(f"Used this window: about {pct(mid(use.get('runs_pct')))} by orchestrate runs on this machine "
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
    """The settings' Default host, else the host this command runs inside, else the only one installed, else codex."""
    if prof.get("default_host"):
        return prof["default_host"]
    if os.environ.get("CLAUDECODE"):
        return "claude"
    if os.environ.get("CODEX_THREAD_ID") or os.environ.get("CODEX_SANDBOX"):
        return "codex"
    installed = [h for h, exe in (("codex", CODEX), ("claude", CLAUDE)) if shutil.which(exe) or Path(exe).exists()]
    return installed[0] if len(installed) == 1 else "codex"


def host_command(host: str, prof: dict, model: str, effort: str, worktree: Path, prompt: str,
                 session: str | None, role: str = "build", new_id: str | None = None, title: str = "") -> tuple[list[str], dict | None]:
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
        agent = {"review": "orchestrate-reviewer", "plan": "orchestrate-planner"}.get(role)
        if agent and agent_installed(agent, worktree):
            args += ["--agent", agent]
        if role in ("review", "plan"):
            args += ["--disallowedTools", "Agent"]
        if session:
            args += ["--resume", session]
        elif new_id:
            args += ["--session-id", new_id]
        if title and not session and claude_supports("--name"):  # the name the Code tab lists it under
            args += ["--name", title]
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
TURN_SIZE: dict = {}  # how full the last turn left its session, `context` of `window` tokens, where the host says
TURN_STOP: dict = {}  # why the script stopped the last turn, with the tool call that was open; empty when it didn't


def usage_of(host: str, stdout: str) -> dict:
    """The tokens a headless turn's own output reported: `input` (not read from cache), `cached` (cache reads) and
    `output`, plus Claude's `cost_usd`, which is a list-price estimate and not what a plan is charged. Claude reports
    them in its `result` event and `codex exec` in `turn.completed`. A Claude turn stopped before its `result`
    (paused, timed out) still reported each finished message's tokens, so those are summed and the turn is counted
    under `incomplete_turns`, since the message it was writing is missing. A turn that ran in the Codex app, or on
    another host, reports nothing here, and the result stays empty: missing telemetry is never filled in. For Codex,
    `run_turn` replaces these figures with the turn's rise in the session's rollout file whenever it can read one
    (see `session_tokens`), and they are used only when it can't."""
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


def ready_usage(state: dict) -> dict:
    """A Ready for Review record's tokens: `usage` is what the session spent since its previous one (so a
    milestone's records add up), and `session_usage` the session's running total so far."""
    if not state.get("usage"):
        return {}
    return {"usage": sub_usage(state["usage"], state.get("ready_usage_at") or state.get("claimed_usage")),
            "session_usage": state["usage"]}


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
    The process's record for `runs` notes the turn starting and ending, with its session and tokens."""
    if LIVE:
        same = bool(session) and session == LIVE.get("session")
        loop_note(host=host, model=model, effort=effort, session=session, activity_at=time.time(),
                  transcript=LIVE.get("transcript") if same else None, turn_started_at=time.time())
    # A Codex turn's tokens are the rise in its session's running total across the turn, both read from the rollout
    # file. `codex exec` prints its own figures only when a turn completes, so a turn stopped at the turn limit
    # recorded none (about 61 million input tokens for one milestone in Thrum), and they count a resumed session's
    # cached tokens again (the usage ledger was 83% high). A new session starts from nothing.
    before = (session_tokens(host, session).get("total") if session else {}) if host == "codex" else None
    out = _run_turn(host, prof, model, effort, worktree, prompt, session, timeout_s, role, title)
    HOSTS_USED.add(host)
    if host == "codex":
        after = session_tokens(host, out[1])
        TURN_SIZE.update({k: after[k] for k in ("context", "window") if k in after})
        if before is not None and after.get("total") is not None:
            rise = {k: max(after["total"][k] - (before.get(k) or 0), 0) for k in TOKEN_KEYS}
            TURN_USAGE.clear()
            if any(rise.values()):
                TURN_USAGE.update(rise, turns=1)
    if host in ("codex", "claude") and not any(k in TURN_USAGE for k in TOKEN_KEYS):
        TURN_USAGE["incomplete_turns"] = 1  # it ran, but its host showed no tokens (the app, a stop, a failure)
    session_cost = None
    if host == "claude" and isinstance(TURN_USAGE.get("cost_usd"), (int, float)) and out[1]:
        # Claude's total_cost_usd covers the whole session, resumed turns included, while its token counts are this
        # invocation's own; so this turn's cost is the rise since the session's last total.
        session_cost = TURN_USAGE["cost_usd"]
        TURN_USAGE["cost_usd"] = round(max(0.0, session_cost - last_session_cost(worktree, out[1])), 6)
    note_usage(worktree, host, model, effort, out[1], out[0], session_cost, err=out[3])
    if LIVE:
        new = out[1]
        known = LIVE.get("transcript") if new and new == LIVE.get("session") else None
        loop_note(turns=LIVE.get("turns", 0) + 1, session=new, path=SESSION_PATH.get("path"), turn_started_at=None,
                  transcript=known or transcript_for(host, new), activity_at=time.time(),
                  usage=add_usage(LIVE.get("usage"), TURN_USAGE) if TURN_USAGE else LIVE.get("usage"))
    return out


TOOL_CALL_LIMIT_S = 15 * 60.0  # how long a tool call that isn't a shell command may stay open before the turn stops
# Tool calls that are left open however long they take. A shell command can rightly run for an hour, and so can a
# wait on one or a subagent; each has its own limits. Codex runs shell commands through its `exec` tool, whose input
# calls `tools.exec_command` or `tools.write_stdin`, and waits on them with `wait`.
SHELL_TOOLS = {"Bash", "BashOutput", "TaskOutput", "KillShell", "Agent", "Task", "shell", "shell_command",
               "exec_command", "write_stdin", "local_shell", "local_shell_call", "container.exec", "wait",
               "clock.sleep", "sleep", "spawn_agent", "wait_agent"}
CODEX_SHELL_IN_EXEC = re.compile(r"\btools\.(exec_command|write_stdin)\b")


def tool_call_view(call: dict, at: float | None = None) -> dict:
    """A tool call as a result or `runs` names it: its name, the start of its input, and how long it was open."""
    at = at or time.time()
    return {"name": call["name"], **({"input": call["input"]} if call.get("input") else {}),
            "open_s": round((call.get("closed") or at) - call["opened"]), "open": not call.get("closed")}


class HeadlessWatch:
    """Reads a headless turn's output as it arrives. It notes the session and its transcript in this process's
    record as soon as the host names them, so `runs` measures idle time from the transcript while the turn runs,
    not from when the turn started. For Codex it also reads the session's transcript, and ends the turn once the
    turn has completed and nothing new has happened for SETTLE_S: a `codex exec` builder once reported its
    milestone done and then didn't exit for 46 minutes, holding the milestone and its review.

    It also follows the agent's tool calls, from Claude's stream and from Codex's rollout file, and ends the turn
    when one that isn't a shell command has been open for TOOL_CALL_LIMIT_S. In Thrum two Computer Use calls hung
    for 98 and 116 minutes, and the lead, which couldn't see them, told the owner the run was waiting for the GPU.
    The script can't limit a host's tool, but it can stop waiting for one. `stopped` holds the call it stopped on,
    and `last_call` the last call opened, for a turn the script stops at the turn limit."""

    def __init__(self, host: str, session: str | None):
        self.host, self.session, self.partial = host, session, ""
        self.rollout = rollout_for(session) if host == "codex" and session else None
        self.offset = self.rollout.stat().st_size if self.rollout else 0  # a resumed thread's old turns don't count
        self.running, self.completed, self.quiet, self.message = set(), False, time.time(), ""
        self.calls: dict = {}  # call id -> {"name", "input", "shell", "opened", "closed"}
        self.last_call: dict | None = None
        self.stopped: dict | None = None
        self.noted_call = None
        if session:
            self.note()

    def note(self) -> None:
        loop_note(session=self.session, transcript=transcript_for(self.host, self.session))

    def opened(self, call_id, name: str, text, shell: bool | None = None) -> None:
        if not call_id or call_id in self.calls:
            return
        text = text if isinstance(text, str) else json.dumps(text) if text else ""
        call = {"name": name or "?", "input": " ".join(text.split())[:200],
                "shell": name in SHELL_TOOLS if shell is None else shell, "opened": time.time(), "closed": None}
        self.calls[call_id] = self.last_call = call

    def closed(self, call_id) -> None:
        if call_id in self.calls and not self.calls[call_id]["closed"]:
            self.calls[call_id]["closed"] = time.time()

    def open_call(self) -> dict | None:
        """The call opened last of those still open, if any."""
        open_ = [c for c in self.calls.values() if not c["closed"]]
        return max(open_, key=lambda c: c["opened"]) if open_ else None

    def claude_event(self, event: dict) -> None:
        message = event.get("message") if isinstance(event.get("message"), dict) else {}
        for part in message.get("content") or []:
            if not isinstance(part, dict):
                continue
            if event.get("type") == "assistant" and part.get("type") == "tool_use":
                self.opened(part.get("id"), part.get("name"), part.get("input"))
            elif event.get("type") == "user" and part.get("type") == "tool_result":
                self.closed(part.get("tool_use_id"))

    def codex_item(self, p: dict) -> None:
        kind = p.get("type")
        if kind in ("function_call", "custom_tool_call", "local_shell_call"):
            name = ".".join(x for x in (p.get("namespace"), p.get("name")) if x) or kind
            text = p.get("arguments") or p.get("input") or p.get("action")
            shell = True if kind == "local_shell_call" else \
                bool(CODEX_SHELL_IN_EXEC.search(str(text))) if p.get("name") == "exec" else None
            self.opened(p.get("call_id"), name, text, shell)
        elif kind and kind.endswith("_output"):
            self.closed(p.get("call_id"))

    def __call__(self, new: str) -> str | None:
        lines = (self.partial + new).split("\n")
        self.partial = lines.pop()
        for line in lines:
            if not line.startswith("{") or (self.session and self.host != "claude"):
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            found = event.get("thread_id") if self.host == "codex" and event.get("type") == "thread.started" \
                else event.get("session_id") if self.host == "claude" else None
            if found and found != self.session:
                self.session = found
                self.note()
            if self.host == "claude":
                self.claude_event(event)
        if self.host == "codex" and self.session:
            if not self.rollout and (found := rollout_for(self.session)):
                self.rollout = found
                self.note()
            events, self.offset = new_events(self.rollout, self.offset)
            for event in events:
                p = event.get("payload") or {}
                if event.get("type") == "response_item":
                    self.codex_item(p)
                if event.get("type") != "event_msg":
                    continue
                if p.get("type") == "task_started":
                    self.running.add(p.get("turn_id"))
                    self.quiet = time.time()
                elif p.get("type") in ("task_complete", "turn_complete", "turn_aborted"):
                    self.running.discard(p.get("turn_id"))
                    self.completed, self.quiet = True, time.time()
                    self.message = p.get("last_agent_message") or self.message
                    for call_id in list(self.calls):  # a turn's end closes whatever it left open
                        self.closed(call_id)
            if self.completed and not self.running and time.time() - self.quiet >= SETTLE_S:
                return f"the turn completed, but codex exec hadn't exited {round(time.time() - self.quiet)}s later"
        current = self.open_call()
        if current is not self.noted_call:  # `runs` shows the call the agent is waiting on
            self.noted_call = current
            loop_note(open_tool_call={"name": current["name"], "input": current["input"],
                                      "opened_at": current["opened"]} if current else None)
        hung = [c for c in self.calls.values()
                if not c["closed"] and not c["shell"] and time.time() - c["opened"] > TOOL_CALL_LIMIT_S]
        if hung:
            self.stopped = min(hung, key=lambda c: c["opened"])
            return (f"the tool call {self.stopped['name']} had been open for "
                    f"{round((time.time() - self.stopped['opened']) / 60)} minutes, so the script stopped the turn")
        return None


def _run_turn(host: str, prof: dict, model: str, effort: str, worktree: Path, prompt: str, session: str | None,
              timeout_s: float, role: str, title: str) -> tuple[int, str | None, str, str, str | None]:
    SESSION_PATH.clear()
    TURN_USAGE.clear()
    TURN_SIZE.clear()
    TURN_STOP.clear()
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
            return 130, session, "", f"the owner has this session open in Claude desktop (pid {pid}); the script " \
                                     "won't write to it at the same time", None
    args, env = host_command(host, prof, model, effort, worktree, prompt, session, role, new_id, title)
    tick = None
    if host == "claude" and not why:
        tick = lambda: claude_import(sid)  # noqa: E731
    watch = HeadlessWatch(host, session or new_id) if host in ("codex", "claude") else None
    code, stdout, stderr = run_proc(args, worktree, timeout_s, env=env, tick=tick, watch=watch)
    TURN_STOP.update(stopped_turn(watch, code, timeout_s))
    new_session, message, seen, error = parse_output(host, stdout)
    message = message or (watch.message if watch else "")
    TURN_USAGE.update(usage_of(host, stdout))
    if host == "claude":
        TURN_SIZE.update(session_tokens(host, new_session or session or new_id, stdout))
    if tick:
        claude_import(sid, wait_s=CLAUDE_IMPORT_WAIT_S)
        if not claude_app_record(sid):
            SESSION_PATH.update(path="headless", path_reason="Claude desktop didn't list the session after the "
                                                             "import link")
    if error and code == 0:
        code, stderr = 1, (stderr + "\n" + message)[-800:]
    return code, new_session or session, message, stderr[-800:], seen


def stopped_turn(watch: HeadlessWatch | None, code: int, timeout_s: float) -> dict:
    """Why the script stopped a headless turn, and the tool call that was open, for the result and the next prompt:
    a call that stayed open past TOOL_CALL_LIMIT_S, or the turn limit with the last call opened. In Thrum the lead
    couldn't see what a stopped turn had been doing, and guessed wrong. Empty for a turn the script didn't stop."""
    if watch is not None and watch.stopped:
        call = tool_call_view(watch.stopped)
        return {"why": f"the tool call {call['name']} had been open for {round(call['open_s'] / 60)} minutes, past "
                       f"the script's {TOOL_CALL_LIMIT_S / 60:g}-minute limit for a call that isn't a shell command",
                "tool_call": call}
    if code == 124:
        last = (watch.open_call() or watch.last_call) if watch is not None else None
        return {"why": f"the turn reached the {timeout_s / 3600:g}-hour turn limit",
                **({"tool_call": tool_call_view(last)} if last else {})}
    return {}


def stopped_note(stop: dict | None, earlier: bool = False) -> str:
    """What a resumed agent is told about a turn the script stopped because a tool call stayed open."""
    call = (stop or {}).get("tool_call") or {}
    if not call or "turn limit" in (stop or {}).get("why", ""):
        return ""
    whose = "The earlier session's" if earlier else "Your"
    return (f"{whose} last turn was stopped by the script, because the tool call {call['name']} had been open for "
            f"{round(call.get('open_s', 0) / 60)} minutes with no answer. Don't wait on it again the same way. If it "
            "was reaching something this session can't reach, such as a locked screen or a permission nobody can "
            "approve, end with `BLOCKED needs_access: <what has to be unlocked or approved>`.")


def report_line(message: str) -> str:
    lines = [l.strip().strip("`*") for l in message.splitlines() if l.strip()]
    return lines[-1] if lines else ""


def report_word(message: str) -> str | None:
    """The report word on the message's last non-empty line, if it has one."""
    lines = [l.strip() for l in message.splitlines() if l.strip()]
    if not lines:
        return None
    word = re.split(r"[:\s]", lines[-1].strip("`* "), maxsplit=1)[0].strip("`*")
    return word if word in REPORT_WORDS else None


def blocked_report(line: str) -> tuple[str | None, str]:
    """(the reason a BLOCKED or NEEDS_CONTEXT line names, or None; what it says would unblock it). A builder writes
    `BLOCKED needs_access: approve Computer Use`, or plain `BLOCKED: ...` when no reason fits."""
    m = re.match(r"^(BLOCKED|NEEDS_CONTEXT)\b\s*([a-z_]+)?\s*:?\s*(.*)$", line.strip("`* "), re.S)
    if not m:
        return None, line
    word, reason, what = m.groups()
    if word == "NEEDS_CONTEXT":
        return "needs_context", ((reason or "") + " " + what).strip() if reason not in BLOCK_REASONS else what
    if reason in BLOCK_REASONS and reason != "too_many_failed_reviews":
        return reason, what.strip()
    return None, ((reason or "") + " " + what).strip()


WARNINGS: list = []  # the launch's preflight warnings, for the result line


EMIT_EXTRA: dict = {}  # fields every later result line of this process carries, e.g. the design review `run` ran
LAUNCH_HOSTS: set = set()  # hosts this process resolved a launch for


def new_command() -> None:
    """Forgets what an earlier command in this process left for result lines (one process can run several)."""
    EMIT_EXTRA.clear()
    LAUNCH_HOSTS.clear()
    HOSTS_USED.clear()
    RUN_HERE.clear()
    COMMAND_STARTED[0] = time.time()


VERSION = "2.1.0"  # the orchestrate plugin's version, as in .claude-plugin/marketplace.json


def version_tuple(text: str) -> tuple[int, ...] | None:
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", text)
    return tuple(int(x) for x in m.groups()) if m else None


def newer_install() -> str | None:
    """A newer copy of this script installed beside this one, when this one runs from a plugin cache
    (`.../orchestrate/<version>/...`). In Thrum the lead kept a cached copy's path in its notes and started builders
    on 1.7.1 for a day after 2.0.0 was installed."""
    parts = LOOP.parts
    for i in range(len(parts) - 1, 0, -1):
        if parts[i - 1] == "orchestrate" and version_tuple(parts[i]):
            ours, root, rest = version_tuple(parts[i]), Path(*parts[:i]), Path(*parts[i + 1:])
            try:
                found = [(version_tuple(d.name), d / rest) for d in root.iterdir() if version_tuple(d.name)]
            except OSError:
                return None
            newer = sorted((v, path) for v, path in found if v > ours and path.exists())
            return str(newer[-1][1]) if newer else None
    return None


# What behaves differently in each version, for a lead whose project has just moved to it. The first result after
# the change carries the lines as `changed`. In Thrum the lead guessed what 2.0.0 fixed, guessed wrong, and told the
# owner so.
CHANGES = {
    "2.1.0": [
        "Only the script sets a milestone to Ready for Review now. A builder merges its work with the milestone still "
        "In Progress and ends with DONE; `run` then runs the checks on the main branch and sets the state if they "
        "pass. `merge` refuses a commit that sets Ready for Review or Done.",
        "`run` starts a new session, instead of resuming the old one, when the old one is over 60% full, was started "
        "by another version of the script, or fails to resume. `fresh_because` says why, so `--fresh` is rarely "
        "needed.",
        "Results have new names: FLOOR is now HOST_FAILED when the host failed and SCRIPT_FAILED when the script "
        "couldn't do a step of its own; PIN is WRONG_MODEL_OR_EFFORT, DESIGN_OWED is DESIGN_NOT_APPROVED, NOT_READY "
        "is CHECKS_FAILED and BUDGET is NO_PROGRESS_FOR_HOURS. The `loops` command is now `runs`, and it shows the "
        "step each run is on.",
        "`run` prints REFUSED when as many builders as the project settings' Builders line names are already "
        "running. Ask the owner, and pass their words with `--more-builders` to start one more.",
        "A reviewer who can't reach the product ends with BLOCKED needs_access. `review` then prints BLOCKED, merges "
        "nothing and counts no round, and `next` is the same review in a visible session.",
        "The script stops a background turn when a tool call that isn't a shell command has been open for 15 "
        "minutes, and `stopped_turn` names the call.",
        "`migrate --branch --worktree <path>` brings over a worktree whose own commits were made before the main "
        "branch was migrated: it renames them and rebases them onto the main branch, holding only that module's run "
        "lock, so other modules keep building. Plain `migrate` no longer waits for runs once the main branch is "
        "migrated, and lists the worktrees still on the old names.",
    ],
}
VERSION_FILE = "version.json"  # under <git common dir>/orchestrate: the version of the script that last printed a result
COMMAND_STARTED = [time.time()]


def version_change(worktree: Path) -> dict | None:
    """What changed since the version of the script that last printed a result in this repository, as `{version:
    lines}`, once: the note is updated at the same time. Before 2.1.0 the script kept no such note, so a repository
    with the script's files from before this command started ran an older version. One with none is new, and gets
    nothing."""
    try:
        common = git(worktree, "rev-parse", "--git-common-dir")
        if common.returncode != 0:
            return None
        folder = (worktree / common.stdout.strip()).resolve() / "orchestrate"
        path = folder / VERSION_FILE
        try:
            seen = json.loads(path.read_text()).get("version")
        except (OSError, ValueError, AttributeError):
            seen = None
        if seen == VERSION:
            return None
        older = seen is not None or (folder.is_dir() and any(
            f.is_file() and f.name != VERSION_FILE and f.stat().st_mtime < COMMAND_STARTED[0]
            for f in folder.iterdir()))
        folder.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"version": VERSION, "at": now()}) + "\n")
        since = version_tuple(seen) if seen else None
        changed = {v: lines for v, lines in CHANGES.items()
                   if version_tuple(v) <= version_tuple(VERSION) and (since is None or version_tuple(v) > since)}
        return changed if older and changed else None
    except Exception:
        return None


def report_due(worktree: Path) -> str | None:
    """Whether today's report is missing from the main branch, for a `run`, `review` or `plan` result. The lead is
    asked for one a day; in Thrum it wrote none in two days, and answered the owner's questions about speed from
    `git log`."""
    try:
        prof = profile(worktree, missing_ok=True)
        rel = f"{reports_dir(prof)}/{datetime.now().strftime('%Y-%m-%d')}.md"
        if git(worktree, "cat-file", "-e", f"{base_ref(prof)}:{rel}").returncode == 0:
            return None
        return f"no report for today at {rel} yet; write one with `report --worktree <repo> --write`"
    except (Exception, SystemExit):
        return None


def result_file(worktree: Path, fields: dict) -> Path | None:
    """Where this result is also written, so a lead that ran the command in the background reads it from a known
    file: in Thrum the lead spent 40 commands digging the JSON line out of mixed output."""
    try:
        name = "-".join(x for x in (fields.get("module"), fields.get("milestone"),
                                    sys.argv[1] if len(sys.argv) > 1 else "") if x)
        path = loop_dir(worktree) / "results" / (re.sub(r"[^A-Za-z0-9._-]", "_", name or "result") + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    except OSError:
        return None


def emit(result: str, **fields) -> None:
    """Prints the one-line result and exits. The Codex quota block goes only on results of a process that launched,
    or ran a turn, on Codex, since it says nothing about another host's limits. The line is also written to
    <git common dir>/orchestrate/results/<MODULE>-<milestone>-<command>.json."""
    warnings = list(WARNINGS)
    if newer := newer_install():
        warnings.append(f"this is orchestrate {VERSION}, and a newer copy is installed at {newer}; run the next "
                        "command from that copy, and read the build skill again, because its commands may have "
                        "changed")
    extra = {"warnings": warnings} if warnings else {}
    if "next" in fields:
        fields["next"] = fit_next(fields["next"])
    more = {k: v for k, v in EMIT_EXTRA.items() if k not in fields}
    codex = "codex" in HOSTS_USED or "codex" in LAUNCH_HOSTS
    worktree = QUOTA_WORKTREE[0] if QUOTA_WORKTREE else None
    due = report_due(worktree) if worktree and len(sys.argv) > 1 and sys.argv[1] in ("run", "review", "plan") \
        else None
    changed = version_change(worktree) if worktree else None
    line = {"result": result, **fields, **more, **SESSION_PATH, **extra, "version": VERSION,
            **({"changed": changed} if changed else {}),
            **({"report_due": due} if due else {}), **({"quota": quota_now()} if codex else {})}
    path = result_file(worktree, fields) if worktree else None
    if path:
        line["result_file"] = str(path)
    text = json.dumps(line)
    if path:
        try:
            path.write_text(text + "\n")
        except OSError:
            pass
    print(text)
    sys.exit(0)


def finish(state_path: Path, state: dict, result: str, **extra) -> None:
    state.update(result=result, finished=time.time(), **extra)
    state_path.write_text(json.dumps(state, indent=2))
    noted = {k: state[k] for k in ("goal", "constraints_missing", "usage", "fresh_because", "stopped_turn")
             if state.get(k)}
    emit(result, module=state["module"], milestone=state["milestone"], thread=state.get("thread"), **noted, **extra)


def resolve(a: argparse.Namespace, prof: dict, role: str) -> tuple[str, str, str]:
    """The host, model and effort for this launch. Each is the first of these that is set: what the lead passed; the
    settings line for this kind of agent on this host; for the effort, its line for this kind of agent on any host;
    the settings' line for the host (`Codex model`) or for every agent (`Effort`); the built-in default. A planner's
    default effort is high. `role` is plan, build, review or design. A planner with no --host runs on the settings'
    `Planner host`, if it names one."""
    host = (a.host or (prof.get("planner_host") if role == "plan" else None) or default_host(prof)).lower()
    line_model, line_effort = role_setting(prof, role, host)
    model = a.model or line_model or prof["models"].get(host) or ""
    if not model and host in prof.get("hosts", {}) and "{model}" in prof["hosts"][host]:
        raise SystemExit(f"error: host {host} needs --model, or a '- **{host} model:** <model>' line in the project settings")
    effort = a.effort or line_effort or ("high" if role == "plan" else prof["effort"])
    if effort not in EFFORTS:
        raise SystemExit(f"error: effort {effort!r} isn't one of {sorted(EFFORTS)}")
    LAUNCH_HOSTS.add(host)
    # The result line says what the session ran on, so the lead can report it without passing every flag itself.
    EMIT_EXTRA.setdefault("ran_on", {"host": host, "model": model, "effort": effort})
    return host, model, effort


def review_host(prof: dict, builder: str, explicit: str | None = None) -> str:
    """The host a review runs on: the one named (`--host`, or `run --review-host`), else the settings'
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
    """(turns that ran on another model or effort, what the script verified the session ran on). The second holds a
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
    """Who ran a build or review. `model` and `effort` are what the script asked for; `observed` is only what it
    verified from the host's output; `cli` is the binary's own version string, or null when it couldn't be read."""
    rec = {"host": host, "model": model, "effort": effort, "observed": observed or {}, "cli": cli_version(host, path)}
    return {**rec, "path": path} if path else rec


def feedback_note(feedback: list[dict], mid: str, record: str, role: str = "build") -> str:
    """The Human Feedback for a milestone, oldest first: each question the lead asked, and the owner's words as the
    script recorded them. For the builder, and for the reviewer, who counts it as the owner's own words."""
    lines = []
    for f in feedback:
        items = ", ".join(f.get("items") or []) or mid
        asked = f"asked \"{f['asked']}\"; " if f.get("asked") else ""
        lines.append(f"- {f.get('at')}, on {items}: {asked}the owner said \"{f.get('said')}\"")
    use = ("Check any claim about what the owner chose against it." if role == "review" else
           "Use their words as given, and cite that record rather than restating them as your own, because the "
           "reviewer checks your work against it.")
    return (f"Human Feedback on {mid}, recorded by the script in {record} under milestones.{mid}.human_feedback, "
            f"oldest first. These are the owner's own words. {use}\n" + "\n".join(lines))


def owner_rules_line(rules: list[str]) -> str:
    return " ".join(f"Owner: {r.strip().rstrip('.')}." for r in rules)


def resources_rule(prof: dict) -> str:
    """The project's exclusive resources, and that `lock` queues for them: in Thrum a builder that met a held lock
    reported it as a fault and asked for another builder's work to be restarted."""
    names = (prof.get("exclusive resources") or "").strip()
    if not names or names.lower() in ("none", "none."):
        return ""
    return (f"- This project's exclusive resources are: {names.rstrip('.')}. Wrap any command that uses one in the "
            "script's `lock <name> -- <command>`. The lock waits its turn: another builder holding it is normal, so "
            "do other work while you wait, and treat it as a block only if the holder seems stuck, naming the "
            "process that holds it.\n")


def session_rule(headless: bool, host: str) -> str:
    """Whether an approval prompt can appear in this session, which the script knows and the lead often doesn't:
    in Thrum a headless session spent three turns trying to use Computer Use, whose prompts it could never show.
    Questions asked through a tool reach nobody either: a builder and a reviewer in Thrum each asked one and
    waited."""
    if headless:
        return ("This session runs in the background, so approval prompts, such as a Computer Use or a permission "
                "dialog, can't appear in it. A question you ask through a tool reaches nobody either, so when you "
                "need an answer, end your turn with `BLOCKED` or `NEEDS_CONTEXT` instead, as below.")
    app = "the Codex app" if host == "codex" else "the Claude app"
    return (f"This session is visible in {app}, so an approval prompt can appear in it if someone is there to "
            "answer it.")


def earlier_handoff(worktree: Path, prof: dict, stem: str, mid: str) -> str:
    """A note naming the handoff an earlier session on this milestone left, when there is one at the main branch's
    tip, for a session that starts without it."""
    rel = handoff_rel(prof, stem, mid)
    try:
        here = show(worktree, tip(worktree, prof, fetch=False), rel)
    except TipError:
        here = None
    if not (here or "").strip():
        return ""
    return handoff_note(rel, mid)


def handoff_note(rel: str, mid: str) -> str:
    """What a new session is told about the handoff at `rel` that an earlier session on `mid` left."""
    return (f"\nAn earlier session on {mid} stopped short and left a handoff at {rel}. Read it before you start. "
            "Where it disagrees with the done-when file or the plan, those win, because a planner may have changed "
            "them since. Rewrite the handoff if you stop short too.\n")


def build_prompt(host: str, headless: bool, prof: dict, stem: str, mid: str, milestone: dict | None, lead: str = "",
                 feedback: list[dict] | None = None, earlier: str = "", rules: list[str] = ()) -> str:
    """A builder's first prompt in a session. `milestone` is the milestone as the done-when file has it now.
    `feedback` is the Human Feedback to show, or None when the session has seen all of it. `earlier` is the note on
    earlier sessions and the script's own note, if there are any."""
    return BUILD_TEMPLATE.format(
        goal=GOAL_LINE if host == "codex" else "", milestone=mid, module=stem, done=done_rel(prof, stem),
        loop=LOOP, skill=skill_note("build-milestone", host),
        lead=f"\nFrom the lead:\n{lead}\n" if lead else "",
        feedback=("\n" + feedback_note(feedback, mid, record_rel(prof, stem)) + "\n") if feedback else "",
        handoff=handoff_rel(prof, stem, mid), earlier=earlier,
        needs="".join(f"- {line}\n" for line in needs_rules(milestone, headless)),
        resources=resources_rule(prof), session=session_rule(headless, host),
        rules="".join(f"- {owner_rules_line([x])}\n" for x in rules))


def needs_rules(milestone: dict | None, headless: bool) -> list[str]:
    """One rule for each kind of item in the milestone that needs someone, naming the items. Items that need access
    or hardware can be done only in a visible session, with someone at the machine; a headless run does the rest."""
    by_type: dict = {}
    for i in (milestone or {}).get("items", []):
        n = i.get("needs")
        if isinstance(n, dict) and n.get("type") in NEEDS_TYPES and i.get("status") != "pass":
            by_type.setdefault(n["type"], []).append(f"{i['id']} ({n.get('what')})" if n.get("what") else i["id"])
    out = []

    def named(kind: str) -> str:
        items = by_type[kind]
        return ", ".join(items) + (" needs" if len(items) == 1 else " need")
    if "human_feedback" in by_type:
        out.append(f"{named('human_feedback')} human feedback: someone has to look at the result and judge it. Do "
                   "every other item first and save the evidence for the owner to look at, then end with "
                   "`BLOCKED needs_human_feedback: <the question for the owner>`.")
    for kind, word in (("access", "approve a permission or a prompt"), ("hardware", "connect a device")):
        if kind not in by_type:
            continue
        if headless:
            out.append(f"{named(kind)} {kind}: someone has to {word}, and nobody can in this session. Do every "
                       f"other item, then end with `BLOCKED needs_{kind}: <what is needed>`. Don't ask anyone to "
                       "confirm anything.")
        elif kind == "access":
            out.append(f"{named(kind)} access. Ask for it as soon as you start, before other work, while someone may "
                       "be there to approve it. If nobody approves it, do the rest and end with "
                       "`BLOCKED needs_access: <what is needed>`.")
        else:
            out.append(f"{named(kind)} hardware. Check the device is connected before other work. If it isn't, do "
                       "the rest and end with `BLOCKED needs_hardware: <the device>`.")
    return out


def binding(prof: dict, role: str, mid: str = "", milestone: dict | None = None, done: str = "",
            review: str = "", rules: list[str] | None = None, headless: bool = True,
            lead_spoke: bool = False) -> tuple[str, list[str]]:
    """The short restatement for resumed turns, which may follow a compaction that dropped the first prompt, and the
    settings lines it found empty. It restates the goal and the role's own boundaries, and points to ORCHESTRATE.md
    for the project's rules rather than copying them: in Thrum the copy cut multi-line rules short. The owner's rules
    stored with the run (`--owner-rule`) go in whole. The line about items that need someone is left out when the
    lead has just written, because the lead's message is the newer fact. A reviewer is never told to merge."""
    missing = [label for label, value in prof.get("bounds", {}).items() if not value]
    if role == "review":
        own = f"{review}" + (f" and the verdict fields, state and fails in {done}" if done else "")
        text = f"Still binding: change only {own}; don't commit, push or start agents."
    else:
        text = (f"Still binding: the goal is every item of {mid} pass with evidence and the work merged with "
                f"`python3 {LOOP} merge --worktree .`, with {mid}'s state left in_progress for the script to set. In "
                f"{done}, change only {mid}'s items' status and evidence, and its state only to in_progress.")
        if not lead_spoke:
            for line in needs_rules(milestone, headless):
                text += " " + line
    if any(prof.get("bounds", {}).values()):
        text += f" The project's rules are in {PROFILE_FILE}; re-read them if this conversation no longer holds them."
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


def preflight(host: str, worktree: Path, role: str, module: str | None = None, milestone: str | None = None) -> list[str]:
    """Launch-aware loader checks for the resolved host and its actual binary. Warnings only: each names its fix,
    and none stops the launch. The browser warning needs the milestone, so `run` adds it once it knows which one
    it builds (see `browser_warnings`)."""
    found = skill_warnings(host, worktree, role)
    if host == "claude":
        found = instruction_warnings(worktree, cli_version("claude")) + found
    if host == "codex" and role == "build" and milestone:  # a reviewer that needs one asks for it, and gets it
        found += browser_warnings(worktree, module, milestone)
    for w in found:
        print("warning: " + w, file=sys.stderr)
    WARNINGS[:] = found
    return found


BROWSER = re.compile(r"\b(chrome|chromium|browsers?|playwright|puppeteer|webkit|firefox|safari|headless|webdriver|"
                     r"selenium|cdp)\b", re.IGNORECASE)


def browser_needs(worktree: Path, prof: dict, module: str | None = None, milestone: str | None = None) -> list[str]:
    """What plainly needs a browser: the settings' targets whose row names one, and the open milestones' items that
    use such a target or name a browser in their check, inspect or target. Read from this worktree's files. With a
    module and a milestone, only that milestone's items: in Thrum one builder's result listed 18 items from other
    modules, which its builder would never touch."""
    text = file_here(worktree, PROFILE_FILE) or b""
    section = re.search(r"^##\s+Targets\s*$(.*?)(?=^##\s|\Z)", text.decode(errors="replace"), re.M | re.S)
    targets = []
    for row in (section.group(1) if section else "").splitlines():
        cells = [c.strip(" `<>") for c in row.strip().strip("|").split("|")]
        if len(cells) > 1 and cells[0] and not set(cells[0]) <= set("-: ") and cells[0].lower() != "target" \
                and BROWSER.search(row):
            targets.append(cells[0])
    found = [] if milestone else [f"target {t}" for t in targets]
    stems = [s for s in modules_here(worktree, prof) if not module or s.upper() == module.upper()]
    for path in [worktree / done_rel(prof, stem) for stem in stems]:
        try:
            doc = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for m in doc.get("milestones") or []:
            if not isinstance(m, dict) or m.get("state") == "done" or (milestone and m.get("id") != milestone):
                continue
            for i in m.get("items") or []:
                if not isinstance(i, dict):
                    continue
                said = " ".join(str(i.get(k) or "") for k in ("check", "inspect", "target"))
                if i.get("target") in targets or BROWSER.search(said):
                    found.append(f"{doc.get('module') or path.parent.name} {i.get('id')}")
    return found


def browser_warnings(worktree: Path, module: str | None = None, milestone: str | None = None) -> list[str]:
    """A Codex agent in workspace-write can't start a browser (Chrome and Playwright's headless shell exit at once,
    with no output). It can run one outside the sandbox only by asking for escalation, which the script's
    approvals_reviewer=auto_review grants or refuses per command: a reviewer that asked got Chromium that way, and a
    builder that never asked lost a session finding out. So warn, with the fixes, when the work plainly needs one."""
    try:
        prof = profile(worktree, missing_ok=True)
    except SystemExit:
        return []
    if prof.get("sandbox", "workspace-write") != "workspace-write":
        return []
    needs = browser_needs(worktree, prof, module, milestone)
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
# Off by default: the script runs `codex exec` and `claude -p` headless, so nothing opens in either app. With
# ORCHESTRATE_VISIBLE=1, on a Mac where the Codex app or Claude desktop is running, the script's sessions are made so
# that the app lists them under the project, and the owner can watch, steer, pause and take over there. The script
# still drives every turn and checks every Ready for Review itself. Elsewhere (another OS, no app, app not running, Claude CLI
# signed out) it runs headless. The methods were proven with the
# Codex app 26.1103 (CLI 0.167.0-alpha.3.2) and Claude desktop 4.23118.0; they rest on deep links, a local IPC
# socket and experimental app-server methods, so re-check them after an app update.
#
# Codex: a short-lived `codex app-server` creates the thread (source `vscode`, like the app's own) and runs one tiny
# bootstrap turn, so the rollout records the model, effort and sandbox the app then resumes with. Each loop turn
# queues the prompt (`codex queue`) and fires `codex://threads/wake/<id>`; the app's own app-server runs it. The
# loop waits on the thread's rollout file until the turn (and any goal turns the app chains after it) has ended.
# `codex://threads/<id>` makes the app window own the thread, so the IPC router can stop it on a pause or timeout.
#
# Claude: only the app can sign in a process it starts, so the script keeps running its own signed-in `claude -p` per
# turn, under a session id it chooses, and imports the session into the app with `claude://resume?session=<id>`.
# The Code tab then lists it with its transcript. A session the owner has open in the app (a live app process on it)
# is never written to by the script at the same time: the turn reports PAUSED instead.

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
BOOTSTRAP = ("The orchestrate script started this thread; its task arrives as the next message. "
             "Reply with exactly: ready")


def visible_unavailable(host: str) -> str | None:
    """Why `host` can't run a session its desktop app shows, or None when it can."""
    if os.environ.get("ORCHESTRATE_VISIBLE", "") in ("", "0"):
        return "headless is the default (ORCHESTRATE_VISIBLE=1 shows sessions in the apps)"
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


def codex_goal_activate(thread: str, status: str = "active") -> bool:
    """The app's play button, minus the wake: a status-only goal change, which writes only the goal store (with an
    `origin` it would also write the rollout, which the app holds), picked up when the thread is next woken. With
    `status="paused"` it is the pause the script sets when a builder stops Blocked, so the goal doesn't go on
    re-checking a block no build turn can change."""
    try:
        srv = CodexAppServer()
        try:
            srv.call("thread/goal/set", {"threadId": thread, "status": status})
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
    """Removes the thread's queued messages, so a turn the script gave up on can't start later unwatched."""
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

RUN_RESULTS = {"review_owed": "REVIEW_OWED", "waiting": "WAITING", "design_not_approved": "DESIGN_NOT_APPROVED", "blocked": "BLOCKED",
               "finished": "FINISHED", "taken": "TAKEN", "invalid": "INVALID"}


def block_for(current: dict, named: str | None, what: str) -> tuple[str, list[str], str]:
    """(reason, items, what) for a milestone the builder stopped on. The reason the builder named stands. With none,
    items that need someone decide it when every other item has passed (access or hardware first, since those
    need the owner at the machine), and otherwise the builder is missing context."""
    if named:
        kind = named[len("needs_"):]
        return named, open_needs(current, (kind,)) if kind in NEEDS_TYPES else [], what
    others_pass = all(i.get("status") == "pass" for i in current["items"] if not isinstance(i.get("needs"), dict))
    for kind in ("access", "hardware", "human_feedback"):
        if others_pass and (items := open_needs(current, (kind,))):
            return f"needs_{kind}", items, what or "; ".join(
                f"{i['id']}: {i['needs'].get('what')}" for i in current["items"] if i["id"] in items)
    return "needs_context", [], what


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


def checks_note(prof: dict, milestone: dict | None, checked: str | None) -> str:
    """What the script already ran before it set Ready for Review, for the reviewer: in Thrum reviewers rebuilt and
    ran the test command twice and re-recorded captures the script's own clean-checkout run had covered."""
    if not milestone or not checked:
        return ""
    ids = [i["id"] for i in milestone.get("items", []) if i.get("check")]
    ran = ([f"the project's test command (`{prof['test_command']}`)"] if prof.get("test_command") else []) + \
        ([f"the `check` of {', '.join(ids)}"] if ids else [])
    if not ran:
        return ""
    return (f" Before it set Ready for Review, the script made sure that {' and '.join(ran)} passed on the files "
            f"at {checked[:12]}. It ran them in its own clean checkout, apart from any that had already passed on "
            "exactly those files. Run one again only if you doubt that result.")


def resume_facts(worktree: Path, milestone: dict | None, last_exit: int | None, timeout_h: float,
                 brief: bool = False, base: str | None = None, earlier: bool = False, stop: dict | None = None) -> str:
    """What a resumed builder needs to pick up where it was, which the script knows and the builder may have lost:
    whether its last turn was cut off, its last commit, which items have passed, and the background jobs it started
    that are still running. In Thrum a builder stopped at the turn limit was told only "Continue the objective" and
    the open items, and spent its next turn finding its own jobs and commits again. With `earlier`, the same facts
    are worded for a new session taking over from an earlier one. `stop` is the run's note of a turn the script
    stopped (see `stopped_turn`), which names the tool call that was open."""
    parts = []
    call = (stop or {}).get("tool_call") or {}
    if last_exit == 124:
        whose = "The earlier session's" if earlier else "Your"
        parts.append(f"{whose} last turn reached the {timeout_h:g}-hour turn "
                     "limit and was stopped" + (f", while the tool call {call['name']} was open" if call.get("open")
                                                 else "") +
                     ". Commands it ran in the foreground were stopped with it; background jobs started with "
                     "`background` carry on.")
    elif note := stopped_note(stop, earlier):
        parts.append(note)
    # With a message from the lead or the script, which says what to do next, only the facts the builder can't see
    # for itself are added.
    if not brief:
        # Only the builder's own commits: not the main branch's, nor the script's STATUS.md commits.
        span = [f"{base}..HEAD"] if base else []
        last = git(worktree, "log", "-1", "--invert-grep", "--grep=^orchestrate:", "--format=%h (\"%s\")",
                   *span).stdout.strip()
        if last:
            parts.append(f"{'The last commit in this worktree' if earlier else 'Your last commit'} is {last}.")
        items = (milestone or {}).get("items", [])
        passed = [i["id"] for i in items if i.get("status") == "pass"]
        if passed:
            parts.append(f"Passed: {', '.join(passed)}.")
    running = worktree_jobs(worktree, running_only=True)
    if running:
        parts.append("Background jobs still running: " + "; ".join(
            f"{j['id']} ({j['age']}) `{j['command'][:120]}`, log {j['log']}" for j in running[-5:]) +
            f". Wait for one with `python3 {LOOP} wait <id> --worktree .`.")
    return " ".join(parts)


NEW_SESSION_AT = 0.6  # how full a session may be before the next turn starts a new one; the owner chose 60%


def stale_session(state: dict) -> str | None:
    """Why the run's session shouldn't be resumed, or None. A session more than 60% full re-reads all of it on every
    step: in Thrum a builder resumed at 322,000 tokens used 16 million input tokens in 42 minutes. And a session
    another version of the script started may hold instructions that version gave, such as a goal naming `land`,
    a command 2.0.0 renamed to `merge`. A state file from before 2.1.0 has no `version`."""
    if state.get("version") != VERSION:
        return (f"the session was started by {'version ' + str(state['version']) if state.get('version') else 'a version before 2.1.0'} "
                f"of the script, and this is {VERSION}")
    used, window = state.get("context"), state.get("window")
    if isinstance(used, int) and isinstance(window, int) and window > 0 and used > NEW_SESSION_AT * window:
        return f"the session was {round(100 * used / window)}% full ({used:,} of {window:,} tokens)"
    return None


def earlier_session_note(worktree: Path, milestone: dict | None, last_exit: int | None, timeout_h: float,
                         base: str | None, mid: str, stop: dict | None = None) -> str:
    """The facts a resumed builder gets, for a new session that takes over a milestone from an earlier session,
    which the script stopped resuming because it was full or old. The commits carry most of what the earlier
    session knew; what only its conversation held is lost."""
    facts = resume_facts(worktree, milestone, last_exit, timeout_h, base=base, earlier=True, stop=stop)
    return (f"\nThis is a new session. An earlier session worked on {mid}, and the script started this one in its "
            "place, so start from the worktree and the done-when file rather than from scratch."
            + (" " + facts if facts else "") + "\n")


def builders_running(worktree: Path) -> list[dict]:
    """The other builder runs in this repository, each as module, milestone and process id: the runs that `runs`
    lists, less this one, reviews, planners and `run --checks-only`, which starts no agent."""
    try:
        loops, _ = live_loops(repository_of(git_common_dir(worktree)), clean=False)
    except Exception:
        return []
    return [{"module": r.get("module"), "milestone": r.get("milestone"), "pid": r.get("pid")} for r in loops
            if r.get("role") == "build" and r.get("pid") != os.getpid() and not r.get("checks_only")]


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


def not_ready_message(why: str, checkout: Path | None) -> str:
    """What the builder is told when it says it's finished and the script's checks disagree. `checkout` is where the
    checks ran, when any did: in Thrum a builder spent turns on a check that passed in its own shell."""
    return (f"The script can't set the milestone to Ready for Review yet: {why}" +
            (f"\n\nThe script ran these in its own clean checkout of the main branch, {checkout}, without your "
             "shell's environment, so a difference between there and your worktree can be the cause." if checkout
             else "") +
            "\n\nFix the cause and end with DONE. If an item can't be met as written, leave it as it is and say so.")


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
    # Items that need access or hardware are done only in a session the owner can see and answer.
    headless = host not in ("codex", "claude") or visible_unavailable(host) is not None
    if not run_lock(worktree, key):
        who = run_holder_info(worktree, key)
        emit("TAKEN", module=stem, by="another run on this repository" + holder_text(who),
             **({"holder": who} if who else {}), next=next_cmd(
                 again, "lead", f"another `run` on this repository holds {stem}{holder_text(who)}; run it again once "
                                "that one stops (`runs` shows whether it's still working)"))
    install_stop()
    loop_register(worktree, "build", module=stem, host=host, model=model, effort=effort,
                  **({"checks_only": True} if getattr(a, "checks_only", False) else {}))
    git_dir = git(worktree, "rev-parse", "--absolute-git-dir").stdout.strip()
    state_dir = Path(git_dir) / "orchestrate"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_path = state_dir / f"{stem}.json"

    sync_worktree(worktree, prof)

    def unlanded(then: dict | None) -> dict:
        """`next` for a run that stops short, or `adopt` when plan files haven't merged (only looked for here, since
        plans are read at the tip and a run that builds needn't pay for the look)."""
        return drift_fields(plan_drift(worktree, prof, start_tip), worktree, then)

    # An owed design review runs here first, as `review --milestone design` would, unless the lead opted out; a
    # DESIGN OK carries on to build in the same run.
    for attempt in range(2):
        try:
            start_tip = tip(worktree, prof)
        except TipError as e:
            emit("SCRIPT_FAILED", module=stem, reason=str(e), next=getattr(e, "next", None) or next_cmd(
                again, "lead", "the main branch's tip can't be fetched; fix the network or remote, then run it again"))
        proj = project(worktree, prof, start_tip)
        for k, cycle in need_cycles(proj).items():
            proj[k]["problems"].append(f"its needs form a cycle: {cycle}")
        sync_holds(worktree, prof)
        if key not in proj:
            emit("INVALID", module=stem, problems=[f"{stem} has no done-when file at the main branch's tip "
                                                   f"({base_ref(prof)}), so there's nothing to build yet"],
                 **unlanded(next_cmd(
                     loop_cmd("plan", "--worktree", str(worktree), "--task", f"Plan module {stem}"), "lead",
                     f"{stem} isn't planned at the main branch's tip")))
        step = next_step(key, proj, holds(worktree), me(worktree))
        lifts = (("needs_access", "needs_hardware") if not headless else ()) + \
            (("needs_context",) if getattr(a, "message", None) else ())
        if step["status"] == "blocked" and step.get("reason") in lifts:
            # what this block waits for is here: a visible run with the owner at the machine, or the missing fact in
            # the lead's --message. The run unblocks it itself
            def reopen(tree, mid=step["milestone"]):
                path = tree / done_rel(prof, stem)
                doc = json.loads(path.read_text())
                m = find(doc, mid)
                m["state"] = "in_progress"
                m.pop("blocked", None)
                write_json(path, doc)
                return [done_rel(prof, stem)]
            ok, detail = loop_write(worktree, prof, key, reopen,
                                    f"orchestrate: {stem} {step['milestone']} unblocked by a run: {step['reason']}")
            if not ok:
                emit("SCRIPT_FAILED", module=stem, reason=f"the script couldn't unblock {step['milestone']}: {detail}",
                     next=next_cmd(again, "lead", "run it again"))
            sync_worktree(worktree, prof)
            start_tip = tip(worktree, prof)
            proj = project(worktree, prof, start_tip)
            step = next_step(key, proj, holds(worktree), me(worktree))
        if step["status"] != "design_not_approved" or getattr(a, "no_design_review", False) or \
                getattr(a, "checks_only", False) or attempt:
            break
        reviewer = design_review_host(prof, proj[key]["record"], host, getattr(a, "review_host", None))
        # `--model` and `--effort` on `run` are the builder's. The design review takes them only where the project settings
        # has no line for a design reviewer (or a reviewer) on that host.
        set_model, set_effort = role_setting(prof, "design", reviewer)
        review = review_once(argparse.Namespace(module=stem, milestone="design", commit=None, worktree=str(worktree),
                                                host=reviewer,
                                                model=None if set_model or reviewer != host else a.model,
                                                effort=None if set_effort else a.effort,
                                                turn_timeout_hours=a.turn_timeout_hours), locked=True)
        # the build row starts its own count; the design review's turns and tokens are under `design_review`
        loop_note(role="build", milestone=None, turns=0, usage={}, turn_started_at=None)
        if review.get("counted") is False:  # it judged a plan that changed while it ran
            emit("DESIGN_NOT_APPROVED", module=stem, design_review=review, **unlanded(review.get("next")))
        if review.get("verdict") != "DESIGN OK":
            emit("DESIGN_NOT_APPROVED", module=stem, design_review=review,
                 **unlanded(design_review_next(review, stem, worktree, prof)))
        # Every later result of this run says the review ran, with its verdict and tokens, so cost adds up.
        EMIT_EXTRA["design_review"] = {k: review.get(k) for k in ("result", "verdict", "host", "model", "effort",
                                                                  "review", "review_commit", "session", "usage")
                                       if review.get(k) is not None}
        sync_worktree(worktree, prof)
    if a.milestone and step.get("milestone") != a.milestone:
        emit("WAITING", module=stem, milestone=a.milestone,
             why=f"{a.milestone} isn't the module's next milestone; that is {step.get('milestone')} "
                    f"({step['status']}), and milestones in a module run in order",
             next=next_for(step, worktree, prof, proj))
    if step["status"] != "ready":
        emit(RUN_RESULTS[step["status"]], **step, **unlanded(next_for(step, worktree, prof, proj)))
    mid = step["milestone"]
    loop_note(milestone=mid)
    if host == "codex":  # the browser warning covers only the milestone this run builds
        for w in browser_warnings(worktree, stem, mid):
            print("warning: " + w, file=sys.stderr)
            WARNINGS.append(w)
    more = (getattr(a, "more_builders", None) or "").strip()
    if prof.get("builders") and not getattr(a, "checks_only", False):
        others = builders_running(worktree)
        if len(others) >= prof["builders"]:
            if not more:
                names = ", ".join(f"{r['module'] or '?'} {r['milestone'] or ''}".strip() for r in others)
                be = "is" if len(others) == 1 else "are"
                why = (f"{plural(len(others), 'builder')} {be} already running in this repository ({names}), and the "
                       f"project settings' Builders line allows {prof['builders']}. The owner decides whether to run "
                       "one more: ask them, and if they say yes, run this command with their words in "
                       "--more-builders. Otherwise start it when one of those builders stops")
                emit("REFUSED", module=stem, milestone=mid, problems=[why], running=others, next=next_cmd(
                    again + " --more-builders '<what the owner said, in their words>'", "lead", why,
                    decides="owner", ask=f"{plural(len(others), 'builder')} {be} running ({names}), the number in the "
                                         f"project settings. Shall I start one more, for {stem} {mid}?"))
            # Kept with the run, so the result shows whose words started the extra builder.
            EMIT_EXTRA["more_builders"] = {"said": more, "running": len(others), "at": now()}
    ok, holder = take_hold(worktree, prof, key, mid)
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
            f"this worktree's copy of {mid}'s definitions isn't the authorised one at the main branch's tip; "
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
    # "PIN" is the name before 2.1.0, still in the state files of runs started earlier.
    fresh = (a.fresh or state.get("milestone") != mid or state.get("result") in ("WRONG_MODEL_OR_EFFORT", "PIN")
             or state.get("pin") != pin)
    # The owner's rules outlive fresh sessions and milestones, until the owner has them cleared.
    rules = [] if getattr(a, "clear_owner_rules", False) else list(state.get("owner_rules") or [])
    rules += [r.strip() for r in getattr(a, "owner_rule", None) or [] if r.strip() and r.strip() not in rules]
    if fresh:
        state = {"module": stem, "milestone": mid, "thread": None, "turns": 0, "pin": pin}
    state["owner_rules"] = rules
    # Every run starts its own counters, so a resume after NO_PROGRESS_FOR_HOURS or a failed review isn't judged on old progress.
    _, reflog = own_progress(worktree, 10 ** 9, prof["plans"])
    state.update(failed_turns=0, reports=0, not_ready_turns=0, idle=0, progress_at=time.time(), passing=passing(milestone),
                 reflog=reflog, host=host, model=model, effort=effort, start_tip=start_tip,
                 marks=work_marks(worktree, milestone))
    state.pop("result", None)
    state.pop("fresh_because", None)  # the result names only the new sessions this run started
    restate, missing = binding(prof, "build", mid, milestone, done_rel(prof, stem), rules=rules, headless=headless)
    state["constraints_missing"] = missing
    if missing:
        print("warning: ORCHESTRATE.md has no filled-in " + " or ".join(f"`{m}`" for m in missing) +
              " line, so the agents have no such rule", file=sys.stderr)
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

    def record_block(reason: str, items: list[str], what: str) -> dict:
        what = repo_relative(what, worktree_roots(worktree))
        blocked = {"reason": reason, **({"items": items} if items else {}), "what": what[:2000],
                   **({"work": w} if (w := builder_work(worktree, prof)) else {})}
        # The builder's handoff merges on its own, as the builder's file and not a record, before the block that
        # names it, so whoever reads the block can open it at the main branch's tip.
        rel = handoff_rel(prof, stem, mid)
        source = worktree / rel
        if source.is_file() and source.read_text(errors="replace").strip():
            text = source.read_bytes()

            def put(tree):
                target = tree / rel
                if target.is_file() and target.read_bytes() == text:
                    return []
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(text)
                return [rel]
            ok, _ = loop_write(worktree, prof, key, put, f"{stem} {mid}: the builder's handoff", trailer=False)
            if ok:
                blocked["handoff"] = rel

        def change(tree):
            path = tree / done_rel(prof, stem)
            doc = json.loads(path.read_text())
            m = find(doc, mid)
            m.update(state="blocked", blocked=blocked)
            write_json(path, doc)
            return [done_rel(prof, stem)]
        loop_write(worktree, prof, key, change, f"orchestrate: {stem} {mid} blocked: {reason}")
        drop_hold(worktree, prof, key, mid)
        return blocked

    def stop_blocked(named: str | None, what: str, message: str) -> None:
        reason, items, what = block_for(current, named, what)
        blocked = record_block(reason, items, what)
        if host == "codex" and state.get("thread") and goal_status(state["thread"]) == "active":
            codex_goal_activate(state["thread"], "paused")  # `run` sets it active again
        finish(state_path, state, "BLOCKED", reason=reason, blocked=blocked, report=tail(message, 1500),
               next=next_for({"module": stem, "milestone": mid, "status": "blocked", "reason": reason,
                              "blocked": blocked}, worktree, prof))

    def new_session(why: str) -> None:
        """Drops the session in `state`, so the next turn starts a new one, and notes why for the result."""
        old = state.get("thread")
        if host == "codex" and old and goal_status(old) == "active":
            codex_goal_activate(old, "paused")  # the new session's goal replaces it
        state["fresh_because"] = (state.get("fresh_because") or []) + [why]
        state.update(thread=None)
        state.pop("context", None)

    def check_and_record(current: dict, done: dict) -> list[str]:
        """Steps 2 and 3 of finishing a milestone, once every item passes. The builder has merged its work with the
        milestone in progress; the script runs the test command and the item checks on the main branch's tip, in
        its own clean checkout, outside the builder's sandbox and outside the merge lock. If they pass, it writes
        the Ready for Review record and sets the state in one commit, and the run ends READY_FOR_REVIEW. If not, it
        returns why, for the builder."""
        reused: list = []
        reasons, checked = ready_problems(worktree, prof, stem, current, done, authorised_hash, start_tip, reused)
        state["reused_checks"] = reused
        if reasons:
            if checked:
                reopen_unchecked(checked)
            return reasons
        head, review = head_commit(worktree), needs_review(current, done)

        def change(tree):
            doc = json.loads((tree / done_rel(prof, stem)).read_text())
            rec = record_in(tree, prof, stem, doc)
            e = entry(rec, mid)
            e["ready_for_review"] = {"commit": head, "checked": checked, "at": now(),
                                     **({"reused": reused} if reused else {}),
                                     **launch_record(host, model, effort, state.get("path"), state.get("observed")),
                                     **ready_usage(state)}
            paths = [record_rel(prof, stem)]
            if not review:
                e["accepted"] = {"by": "checks", "commit": head, "checked": checked, "at": now()}
            target = "ready_for_review" if review else "done"
            if find(doc, mid).get("state") != target:
                find(doc, mid)["state"] = target
                write_json(tree / done_rel(prof, stem), doc)
                paths.append(done_rel(prof, stem))
            write_json(tree / record_rel(prof, stem), rec)
            return paths
        loop_note(step="merging the Ready for Review record")
        ok, detail = loop_write(worktree, prof, key, change,
                                f"orchestrate: accept {stem} {mid}" if not review else
                                f"orchestrate: {stem} {mid} is ready for review")
        if not ok:
            finish(state_path, state, "SCRIPT_FAILED",
                   reason=f"the script couldn't record that {mid} is Ready for Review: {detail}",
                   next=next_cmd(again, "lead", "the checks passed but the record couldn't be written; run it again, "
                                                "and the script re-checks and records it"))
        if not review:
            drop_hold(worktree, prof, key, mid)
        if state.get("usage"):
            state["ready_usage_at"] = dict(state["usage"])  # the next record on this session counts from here
        reviewer = review_host(prof, host, getattr(a, "review_host", None))
        then = (next_cmd(loop_cmd("review", "--module", stem, "--milestone", mid, "--commit", head,
                                  "--worktree", str(worktree), "--host", reviewer), "lead",
                         f"{stem} {mid} is Ready for Review at {head[:12]}"
                         + (f", on {reviewer}, the review host" if reviewer != host else ""))
                if review else
                next_cmd(loop_cmd("run", "--module", stem, "--worktree", str(worktree)), "lead",
                         f"{stem} {mid} was accepted on its checks alone (no item needs a reviewer); run "
                         "builds the module's next milestone"))
        finish(state_path, state, "READY_FOR_REVIEW", review=review, commit=head, checked=checked,
               **({"reused_checks": reused} if reused else {}), next=then)

    def reopen_unchecked(checked: str) -> None:
        """Sets the milestone back to in_progress on the main branch when the tip says Ready for Review or Done
        without the script's record, and the script's checks have just failed it. A builder set that state before
        2.1.0, and in Thrum such a milestone stayed on the main branch for three hours after its checks failed,
        while other builders rebased onto it."""
        try:
            at_tip = find(upgrade_doc(json.loads(show(worktree, checked, done_rel(prof, stem)) or "")), mid)
        except (ValueError, SystemExit):
            return
        if at_tip.get("state") not in ("ready_for_review", "done"):
            return

        def change(tree):
            path = tree / done_rel(prof, stem)
            doc = json.loads(path.read_text())
            m = find(doc, mid)
            if m.get("state") not in ("ready_for_review", "done"):
                return []
            m["state"] = "in_progress"
            write_json(path, doc)
            return [done_rel(prof, stem)]
        ok, _ = loop_write(worktree, prof, key, change,
                           f"orchestrate: {stem} {mid} back to in_progress: the script's checks failed")
        if ok:
            state["reopened"] = checked

    # A milestone whose work is already merged, with every item passing, is checked before any builder turn. That is
    # a merge that finished after the run had stopped (in Thrum a builder's merge, run in the background, pushed after
    # its turn was stopped, and the run reported a failure), or a milestone a builder set Ready for Review before
    # 2.1.0, or a run started again after the checks failed.
    script_note, reasons = "", []
    if passing(milestone) == len(milestone["items"]) and is_ancestor(worktree, "HEAD", start_tip) and \
            not git(worktree, "status", "--porcelain").stdout.strip():
        reasons = check_and_record(milestone, done)
        state["not_ready_reasons"] = "; ".join(reasons)
        ran = any("` exited " in r or "` timed out" in r for r in reasons)
        script_note = not_ready_message(state["not_ready_reasons"],
                                        loop_dir(worktree) / "verify" / stem.upper() if ran else None)
    else:
        base = git(worktree, "merge-base", "HEAD", start_tip).stdout.strip()
        if base and (found := states_set(worktree, prof, base)):
            # a branch from before 2.1.0: its builder set the state in a commit that hasn't merged
            script_note = state_refusal(found, old_branch=True)
        if getattr(a, "checks_only", False):
            reasons = [script_note] if script_note else []
            if git(worktree, "status", "--porcelain").stdout.strip():
                reasons.append("the worktree has uncommitted or untracked files; commit, remove or ignore them")
            if not is_ancestor(worktree, "HEAD", start_tip) and not script_note:
                reasons.append(f"HEAD is not on {base_ref(prof)} yet; merge with `python3 {LOOP} merge --worktree .`")
            if passing(milestone) < len(milestone["items"]):
                reasons.append("items not yet pass: " + ", ".join(i["id"] for i in milestone["items"]
                                                                  if i.get("status") != "pass"))
            state["not_ready_reasons"] = "; ".join(reasons)
    if getattr(a, "checks_only", False):
        # nothing passed: the checks failed, or the work isn't merged with every item passing yet
        finish(state_path, state, "CHECKS_FAILED", reasons=reasons)

    lead_pending = bool(a.message)  # the lead's own --message, not one the script writes after a turn
    resume_retried = False
    while True:
        # Checked before every turn, because a long run fills its session turn by turn.
        if resumable and state.get("thread") and (why := stale_session(state)):
            new_session(why)
        status = goal_status(state.get("thread")) if host == "codex" else None
        if status in ("usage_limited", "budget_limited"):
            finish(state_path, state, "HOST_FAILED", reason=f"goal {status}", next=floor_next())
        if status == "paused" or _STOP:
            finish(state_path, state, "PAUSED")
        first = state.get("thread") is None or not resumable
        feedback = (proj[key]["record"]["milestones"].get(mid) or {}).get("human_feedback") or []
        told = text_hash(json.dumps(feedback, sort_keys=True))
        new_feedback = bool(feedback) and (first or told != state.get("feedback_told"))  # new, or more came in
        if first:
            lead_pending = False
            lead = a.message or ("This continues earlier work on the same milestone; the files show where it got to."
                                 if state["turns"] and not resumable else "")
            earlier = earlier_handoff(worktree, prof, stem, mid)
            if script_note:
                earlier += f"\nFrom the script:\n{script_note}\n"
                script_note = ""
            if state["turns"] and resumable:  # a new session on a milestone an earlier session worked on
                earlier += earlier_session_note(worktree, find(load_done(worktree, stem, prof), mid),
                                                state.get("last_exit"), a.turn_timeout_hours, base_ref(prof), mid,
                                                state.get("stopped_turn"))
            resent = a.message
            a.message = None
            prompt = build_prompt(host, headless, prof, stem, mid, find(load_done(worktree, stem, prof), mid),
                                  lead=lead, feedback=feedback if new_feedback else None, earlier=earlier, rules=rules)
        else:
            lead_spoke, lead_pending = lead_pending, False
            if script_note:
                a.message = script_note + (f"\n\nFrom the lead:\n{a.message}" if a.message else "")
                script_note = ""
            resent = a.message
            now_done = find(load_done(worktree, stem, prof), mid)
            facts = resume_facts(worktree, now_done, state.get("last_exit"), a.turn_timeout_hours,
                                 brief=bool(a.message), base=base_ref(prof), stop=state.get("stopped_turn"))
            prompt = (a.message + ("\n\n" + facts if facts else "")) if a.message else \
                "Continue the objective." + open_items(now_done) + (" " + facts if facts else "")
            a.message = None
            # A resumed turn may follow a compaction that dropped the first prompt. An active Codex goal already
            # re-sends its objective each turn, so only a thread without one gets the restatement; the owner's rules
            # may postdate the goal, so they go every time.
            if status != "active":
                prompt += "\n\n" + (binding(prof, "build", mid, milestone, done_rel(prof, stem), rules=rules,
                                              headless=headless, lead_spoke=True)[0] if lead_spoke else restate)
            elif rules:
                prompt += "\n\n" + owner_rules_line(rules)
        if new_feedback:
            if not first:
                prompt += "\n\n" + feedback_note(feedback, mid, record_rel(prof, stem))
            state["feedback_told"] = told
        loop_note(step=f"builder turn {LIVE.get('turns', 0) + 1}" + (" (a new session)" if first and state["turns"] else ""))
        code, session, message, err, seen = run_turn(host, prof, model, effort, worktree, prompt,
                                                     None if first else state["thread"], timeout_s,
                                                     title=session_title(worktree, stem, f"{mid} build"))
        state["stopped_turn"] = dict(TURN_STOP)
        if not TURN_STOP:
            state.pop("stopped_turn")
        resumed_from = None if first else state.get("thread")
        if resumable:
            if first:
                state["version"] = VERSION  # the version that started this session
            state["thread"] = session
            note_thread(worktree, host, session, "build", session_title(worktree, stem, f"{mid} build"))
        state.update(TURN_SIZE)
        state["turns"] += 1
        # A turn stopped at the turn limit (124) is a long turn, not a failing host: in Thrum two in a row stopped
        # runs as "quota, sign-in or outage". The stall and budget checks below still end a run that gets nowhere.
        state["failed_turns"] = state["failed_turns"] + 1 if code not in (0, 124, 130) else 0
        state["last_exit"] = code
        state["path"] = SESSION_PATH.get("path")
        if TURN_USAGE:
            state["usage"] = add_usage(state.get("usage"), TURN_USAGE)
        # A resume that failed before its turn started (no tokens) gets one try in a new session before the run
        # stops HOST_FAILED: in Thrum the lead restarted runs with --fresh 15 times for this, mostly sessions the
        # Codex app had started that `codex exec` couldn't resume.
        if resumed_from and code not in (0, 124, 127, 130) and not _STOP and not resume_retried and \
                not any(TURN_USAGE.get(k) for k in TOKEN_KEYS):
            resume_retried = True
            new_session(f"resuming session {resumed_from} failed before its turn started"
                        + (f": {err.strip().splitlines()[-1][:300]}" if err.strip() else ""))
            a.message = resent
            state_path.write_text(json.dumps(state, indent=2))
            continue
        state_path.write_text(json.dumps(state, indent=2))

        if _STOP or code == 130:
            finish(state_path, state, "PAUSED", **({} if _STOP else {"reason": err.strip()}))
        if code == 127 or (resumable and state["thread"] is None) or state["failed_turns"] >= 2:
            finish(state_path, state, "HOST_FAILED", reason=floor_reason(host, code, err), exit_code=code, stderr=err,
                   next=floor_next())
        bad, seen_now = pin_check(host, state.get("thread"), seen, model, effort)
        state["observed"] = still_observed(state.get("observed"), seen_now)
        if bad:
            finish(state_path, state, "WRONG_MODEL_OR_EFFORT", mismatches=bad[:5])
        status = goal_status(state["thread"]) if host == "codex" else None
        if host == "codex":
            state["goal"] = status or "none"  # whether the builder created its goal; without one, turns restate
        if status in ("usage_limited", "budget_limited"):
            finish(state_path, state, "HOST_FAILED", reason=f"goal {status}", next=floor_next())
        if status == "paused":
            finish(state_path, state, "PAUSED")
        # A `merge` the builder started in the background can outlast its turn. The run waits for it rather than
        # judge a half-merged worktree: in Thrum one pushed after its turn was stopped, and the run reported a
        # failure (P3).
        if waited := wait_for_merges(worktree):
            state["waited_for_merge"] = waited
        if _STOP:
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
            reasons = check_and_record(current, done)
        else:
            reasons = ["items not yet pass: " + ", ".join(i["id"] for i in current["items"]
                                                           if i.get("status") != "pass")]
        state["not_ready_reasons"] = "; ".join(reasons)
        if word == "DONE" or status == "complete":
            state["not_ready_turns"] += 1
            if state["not_ready_turns"] >= 3:
                finish(state_path, state, "CHECKS_FAILED", reasons=reasons)
        if word == "DONE" or now_passing == len(current["items"]):
            ran = any("` exited " in r or "` timed out" in r for r in reasons)
            a.message = not_ready_message(state["not_ready_reasons"],
                                          loop_dir(worktree) / "verify" / stem.upper() if ran else None)
        if word in ("BLOCKED", "NEEDS_CONTEXT"):
            state["reports"] += 1
            named, what = blocked_report(report_line(message))
            # A block with a reason (or a missing fact) is one no further build turn can change, so the run stops on
            # the first report. A plain BLOCKED keeps one more turn while the goal is active: in Thrum that turn
            # sometimes found a way round.
            if named or status != "active" or state["reports"] >= 2:
                stop_blocked(named, what or "see the builder's report", message)
        else:
            state["reports"] = 0
        # A headless run can't do items that need access or hardware. Once they are all that is left, the run stops
        # Blocked on them, for a visible run while the owner is at the machine; nobody is asked to confirm anything.
        if headless and open_needs(current, HELD_BY_SOMEONE) and all(
                i.get("status") == "pass" for i in current["items"]
                if (i.get("needs") or {}).get("type") not in HELD_BY_SOMEONE):
            stop_blocked(None, "", message)
        # A turn that changed nothing and reported nothing is a progress update, not work. After STALL_TURNS of
        # them in a row (each answered with the open items), the script stops rather than nudging forever.
        state["idle"] = 0 if (changed_anything or word) else state.get("idle", 0) + 1
        if state["idle"] >= STALL_TURNS:
            finish(state_path, state, "STALLED", turns=state["idle"], open=[
                i["id"] for i in current["items"] if i.get("status") != "pass"], report=tail(message, 1500))
        if status == "blocked":
            named, what = blocked_report(report_line(message))
            stop_blocked(named, what or "the Codex goal is blocked", message)
        if time.time() - state["progress_at"] > a.budget_hours * 3600:
            finish(state_path, state, "NO_PROGRESS_FOR_HOURS", hours=a.budget_hours)


# ------------------------------------------------------------------------------------------ reviewing and planning

FINISH = "Finish the task and end with the last line it asks for."
# For a Claude reviewer or planner, where the script reads the end of a turn as the end of the work. In Thrum a
# reviewer ended its first turn with its test command still running in the background. Background tasks stay on,
# because without them a command is cut off at the Bash tool's ten-minute limit.
CLAUDE_TURN_NOTE = ("Your turn ending is read as your work ending, so wait for any command you run in the "
                    "background to finish before you reply.")


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
    the lead. Host failures come back as HOST_FAILED, SCRIPT_FAILED, WRONG_MODEL_OR_EFFORT or PAUSED with their reasons, so the lead can fall back to
    another host."""
    session, message, turns, observed, owed, usage, stop = None, "", 0, None, FINISH, {}, {}
    while turns < max_turns:
        resume = session if (turns and host in ("codex", "claude")) else None
        text = prompt if not turns else owed + (f"\n\n{restate}" if restate else "")
        if turns and (note := stopped_note(stop)):  # the script stopped the last turn on a tool call
            text = note + "\n\n" + text
        if not turns and host == "claude":
            text += "\n\n" + CLAUDE_TURN_NOTE
        if turns and not resume:  # a host with no sessions gets the whole task again
            text = prompt + "\n\n" + text
        loop_note(step=f"{'planner' if role == 'plan' else 'reviewer'} turn {turns + 1}")
        code, session, message, err, seen = run_turn(host, prof, model, effort, worktree, text, resume, timeout_s,
                                                     role, title)
        stop = dict(TURN_STOP)
        note_thread(worktree, host, session, role, title)
        turns += 1
        usage = add_usage(usage, TURN_USAGE)
        spent = {"usage": usage} if usage else {}  # a stop's tokens count too
        spent.update({"stopped_turn": stop} if stop else {})
        if _STOP or code == 130:
            return {"result": "PAUSED", "session": session, **spent, **({} if _STOP else {"reason": err.strip()})}
        bad, seen_now = pin_check(host, session, seen, model, effort)
        observed = still_observed(observed, seen_now)
        if bad:
            return {"result": "WRONG_MODEL_OR_EFFORT", "mismatches": bad[:5], "session": session, **spent}
        if code != 0:
            return {"result": "HOST_FAILED", "reason": floor_reason(host, code, err) if code == 127 else
                    f"the {role} turn on {host} was stopped: {stop['why']}" if code == 124 and stop else
                    f"the {role} turn on {host} failed (exit {code}); likely quota, sign-in or outage",
                    "exit_code": code, "stderr": err, "session": session, **spent}
        owed = missing(message)
        if owed is None:
            break
    last = next((l.strip() for l in reversed(message.splitlines()) if l.strip()), "")
    return {"result": "FINISHED" if owed is None else "UNFINISHED", "last_line": last, "owed": owed,
            "report": tail(message, 6000 if role == "plan" else 1500), "session": session, "turns": turns, "observed": observed or {},
            **({"usage": usage} if usage else {}), **({"stopped_turn": stop} if stop else {})}


REVIEW_LINE = re.compile(r"^(PASS|FAIL)\s+([A-Za-z0-9_.-]+)\b|^(DESIGN OK|DESIGN CHANGES)\b")
KEEP_LINE = re.compile(r"^KEEP\s+([A-Za-z0-9_.-]+)\s+([A-Za-z0-9_.-]+)\s*:\s*(builder|reviewer|owner)\b\s*:?\s*(.*)$",
                       re.IGNORECASE)


def review_once(a: argparse.Namespace, locked: bool = False) -> dict:
    """Runs one review, milestone or design, and returns its result instead of printing it. `locked` means the
    caller (a `run` doing an owed design review) already holds the module's run lock."""
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    if not a.host and prof.get("review_host"):  # the settings' Review host, against whoever made what's judged
        builder, rec = default_host(prof), {}
        try:
            rec = json.loads(show(worktree, base_ref(prof), record_rel(prof, module_stem(worktree, prof, a.module)))
                             or "{}")
        except (json.JSONDecodeError, SystemExit):
            pass
        if a.milestone == "design":  # whoever wrote the plan, when the script knows
            reviewer = design_review_host(prof, rec, builder)
        else:  # whoever built it
            ready = ready_record((rec.get("milestones") or {}).get(a.milestone))
            reviewer = review_host(prof, ready.get("host") or builder)
        a = argparse.Namespace(**{**vars(a), "host": reviewer})
    host, model, effort = resolve(a, prof, "design" if a.milestone == "design" else "review")
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
        return _result("SCRIPT_FAILED", **info, reason=str(e), **({"next": e.next} if getattr(e, "next", None) else {}))
    proj = project(worktree, prof, ref)
    if key not in proj or proj[key]["problems"]:
        return _result("INVALID", **info, problems=(proj.get(key) or {}).get("problems") or ["not planned at the tip"])
    done_path = done_rel(prof, stem)
    review_path = f"{prof['evidence']}/{stem}/" + ("design-review.md" if design else f"{mid}-review.md")
    rec = proj[key]["record"]
    moved_note = ""
    if design:
        start, before_doc = ref, proj[key]["doc"]
    else:
        r = git(worktree, "rev-parse", "--verify", "--quiet", f"{a.commit}^{{commit}}")
        if r.returncode != 0:
            return _result("INVALID", **info, problems=[f"commit {a.commit} doesn't exist here"])
        start = r.stdout.strip()
        if not is_ancestor(worktree, start, ref):
            return _result("INVALID", **info, problems=[f"{start[:12]} isn't on {base_ref(prof)}, so it isn't merged"])
        def migrated(c: str) -> bool:
            text = show(worktree, c, done_path)
            try:
                return text is not None and not old_names_in_doc(json.loads(text))
            except json.JSONDecodeError:
                return True
        moved_note = ""
        if not migrated(start):  # made Ready for Review before `migrate` moved the plan files or renamed them
            moved = next((c for c in git(worktree, "rev-list", "--reverse", "--ancestry-path", f"{start}..{ref}")
                          .stdout.split() if migrated(c)), None)
            if moved:
                WARNINGS.append(f"{mid} was made Ready for Review at {start[:12]}, before `migrate` brought "
                                f"{done_path} to its current place and names; reviewed at {moved[:12]}, the first "
                                "commit where it has them")
                moved_note = (f"\nThe builder made {mid} Ready for Review at {start[:12]}. After that, the script's "
                              f"`migrate` commit {moved[:12]} moved or renamed the plan files, so you are on "
                              f"{moved[:12]}. Anything that move broke, such as links to the old paths, isn't the "
                              "builder's doing; to see the builder's own work, compare with "
                              f"`git show {start[:12]}`.\n")
                start = moved
        try:
            before_doc = upgrade_doc(json.loads(show(worktree, start, done_path) or ""))
            under_review = find(before_doc, mid)
        except (json.JSONDecodeError, SystemExit):
            return _result("INVALID", **info, problems=[f"{mid} can't be read from {done_path} at {start[:12]}"])
        at_tip = next((m for m in proj[key]["doc"]["milestones"] if m["id"] == mid), {})
        if at_tip.get("state") != "ready_for_review":
            return _result("INVALID", **info, problems=[f"{mid} is {at_tip.get('state')} at the tip; only a "
                                                        "milestone that is Ready for Review is reviewed"])
        if not ready_current(rec["milestones"].get(mid)):
            # In Thrum a merge that outlived its turn left a milestone Ready for Review with no record, and its
            # reviewer, told nothing about the checks, ran the test command itself for 35 minutes (P3).
            why = (f"{mid} is Ready for Review at the main branch's tip, but the script has no record that its checks "
                   "passed: a builder set the state itself, as builders did before 2.1.0, or its merge finished after "
                   "the run had stopped. `run` runs the checks in the module's worktree. If they pass, it writes the "
                   "record and the review can start; if not, it sets the milestone back to in_progress and resumes "
                   "the builder")
            return _result("INVALID", **info, problems=[why], next=next_cmd(
                loop_cmd("run", "--module", stem, "--worktree", str(worktree)), "lead", why))
        if under_review.get("state") != "ready_for_review":
            # The builder's commit has the milestone in progress, and the script set Ready for Review in a later
            # commit of its own, after its checks. The reviewer works there, where the state and the work agree.
            set_at = next((c for c in git(worktree, "log", "--reverse", "--format=%H", "--ancestry-path",
                                          f"{start}..{ref}", "--", done_path).stdout.split()
                           if state_at(worktree, c, done_path, mid) == "ready_for_review"), None)
            if not set_at:
                return _result("INVALID", **info, problems=[
                    f"{mid} is {under_review.get('state')} at {start[:12]}, and no later commit on "
                    f"{base_ref(prof)} sets it to Ready for Review; review the commit the result named"])
            moved_note += (f"\nThe builder's work ends at {start[:12]}. The script ran its checks after that and set "
                           f"{mid} Ready for Review in {set_at[:12]}, which is where you are. To see the builder's own "
                           f"work, compare with `git show {start[:12]}`.\n")
            start = set_at
            before_doc = upgrade_doc(json.loads(show(worktree, start, done_path) or ""))
            under_review = find(before_doc, mid)
        if definitions(under_review) != (rec["milestones"].get(mid) or {}).get("definitions"):
            return _result("INVALID", **info, problems=[f"{mid}'s definitions at {start[:12]} aren't the authorised ones"])
    try:
        tree = verify_tree(worktree, stem, start)
    except TipError as e:
        return _result("SCRIPT_FAILED", **info, reason=str(e))
    before_review = (tree / review_path).read_text() if (tree / review_path).exists() else None
    captures = review_path[:-len(".md")]
    feedback = (rec["milestones"].get(mid) or {}).get("human_feedback") if not design else None
    e_ = rec["milestones"].get(mid) or {}
    judged = [d for d in e_.get("diagnoses") or [] if d.get("who") == "reviewer"
              and (d.get("at") or "") >= counted_since(e_)]  # only a judgement on the rounds the counts still cover
    changed, any_change = design_changes(worktree, rec, done_path, proj[key]["doc"], design_rel(prof, stem),
                                         show(worktree, start, design_rel(prof, stem))) if design else ("", None)
    if design and any_change is False and (rec.get("design") or {}).get("verdict") == "changes":
        why = (f"nothing in {stem}'s items or design has changed since its design review asked for changes "
               f"({rec['design'].get('review')}), so a new review would only repeat it; the planner hasn't acted yet")
        return _result("INVALID", **info, problems=[why], next=design_review_next(
            {"verdict": "DESIGN CHANGES", "review": rec["design"].get("review")}, stem, worktree, prof))
    briefs = (f"The tasks planners were given for this module, whole and verbatim, are in {record_rel(prof, stem)} "
              "under `briefs`, oldest first. Some are the lead's or the script's own words, such as re-plan tasks. "
              "Where a task disagrees with the owner's words, in the project brief or quoted in the design, the "
              "owner's words win."
              if design and rec.get("briefs") else "")
    context = " ".join(x.strip() for x in (changed, briefs) if x.strip())
    prompt = review_prompt(host, prof, stem, mid, start, done_path, review_path, None if design else under_review, e_,
                           feedback, judged, moved_note, context, design)
    wanted = ("DESIGN OK", "DESIGN CHANGES") if design else ("PASS", "FAIL")
    try:  # the tip as the turn starts, to check what reaches it while the reviewer works
        launch_tip = tip(worktree, prof)
    except TipError as e:
        return _result("SCRIPT_FAILED", **info, reason=str(e))
    seen = reflog_size(tree)
    def owed(msg: str) -> str | None:
        """None once the reviewer has ended with its verdict, or, for a milestone, with Needs Access."""
        line = report_line(msg)
        if line.startswith(wanted) or (not design and blocked_report(line)[0] == "needs_access"):
            return None
        return FINISH

    out = one_session(host, prof, model, effort, tree, prompt, "review", owed,
                      a.turn_timeout_hours * 3600,
                      title=session_title(worktree, stem, f"{mid} review"),
                      restate=binding(prof, "review", done="" if design else done_path,
                                      review=f"{review_path} (and files under {captures}/)")[0])
    result = out.pop("result")
    launch = launch_record(host, model, effort, SESSION_PATH.get("path"), out.pop("observed", None))
    if out.get("usage"):
        launch["usage"] = out["usage"]
    if result != "FINISHED":
        return _result(result, **info, **out)

    # Check what the reviewer did before anything merges.
    try:
        forged = record_tampering(worktree, prof, launch_tip, tip(worktree, prof))
    except TipError as e:
        return _result("SCRIPT_FAILED", **info, reason=f"the turn can't be checked, so nothing merged: {e}")
    if forged:
        return _result("INVALID", **info, merged=False, problems=[
            f"while this review ran, {plural(len(forged), 'commit')} without the script's trailer changed a record "
            f"file on the tip: {', '.join(forged)}"], session=out.get("session"), next=next_cmd(
            None, "lead", "report it to the owner, who decides what to do with those commits: they reached the "
            "main branch's tip during a review, and only the script writes record files. Nothing from this review "
            "was merged", decides="owner"))
    if made := commits_made(tree, seen):
        return _result("INVALID", **info, merged=False, problems=[
            f"the reviewer committed in its checkout ({plural(len(made), 'commit')} in its reflog during the turn: "
            f"{'; '.join(made[:5])}); a reviewer leaves its verdict uncommitted and the script merges it"],
            session=out.get("session"), next=next_cmd(
                None, "lead", "nothing from this review was merged; any commit that reached the main branch's tip "
                "is already there, so look at it, then review again"))
    named, what = blocked_report(out["last_line"]) if not design else (None, "")
    if named == "needs_access":
        # In Thrum a reviewer that couldn't reach the Mac's locked screen failed the milestone on it, and the builder
        # lost a round to a problem that wasn't in the work (F1). Access is the owner's to give, not the builder's.
        what = repo_relative(what, worktree_roots(worktree)) or "the reviewer couldn't reach the product"
        why = (f"the reviewer of {stem} {mid} couldn't reach the product from its session: {sentence(what)} Nothing "
               "was merged and no round was counted, and the milestone is still Ready for Review. The lead runs the "
               "same review again in a visible session while the owner is at the machine to unlock or approve it")
        return _result("BLOCKED", **info, reason="needs_access", what=what, merged=False, commit=start,
                       last_line=out["last_line"], session=out.get("session"),
                       **({"usage": out["usage"]} if out.get("usage") else {}),
                       **({"stopped_turn": out["stopped_turn"]} if out.get("stopped_turn") else {}),
                       next=next_cmd("ORCHESTRATE_VISIBLE=1 " + loop_cmd(
                           "review", "--module", stem, "--milestone", mid, "--commit", a.commit, "--worktree",
                           str(worktree), "--host", host), "lead", why,
                           ask=f"The review of {stem} {mid} needs you at the machine: {sentence(what)} Are you there "
                               "now?"))
    allowed = {review_path} | (set() if design else {done_path})
    changed = changed_paths(tree, start)
    evidence = [p for p in changed if p.startswith(captures + "/")]
    problems = [f"changed {p}, which a reviewer doesn't own" for p in changed if p not in allowed and p not in evidence]
    problems += [f"{p} isn't a plain file; captures must be files" for p in evidence
                 if (tree / p).is_symlink() or ((tree / p).exists() and not (tree / p).is_file())]
    # read now: merging reuses this checkout, so the files must be in hand before it's reset to the tip
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
                found = reviewed.get("findings") or []
                if verdict == "FAIL":
                    named = {f.get("item") for f in found if isinstance(f, dict)}
                    unnamed = [i["id"] for i in reviewed["items"] if i.get("verdict") != "pass" and i["id"] not in named]
                    if not found:
                        problems.append("the last line says FAIL, but findings is empty; list each Must Fix "
                                        "with a short name")
                    elif unnamed:
                        problems.append(f"findings names no finding for {', '.join(unnamed)}, which didn't pass")
    if problems:
        return _result("INVALID", **info, merged=False, problems=problems[:20], last_line=out["last_line"],
             session=out.get("session"))

    passed = verdict in ("PASS", "DESIGN OK")

    stale: dict = {}
    counts: dict = {}  # the milestone's counts as the script left them, read back from `change`

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
            design_at = design_rel(prof, stem)
            read = show(worktree, start, design_at)  # what the reviewer read, not what the tip holds now
            here = (t / design_at).read_text() if (t / design_at).exists() else None
            moved = changed_items(before_doc, doc) + (["the design document"] if read != here else [])
            entry_ = {"verdict": "ok" if passed else "changes", "review": review_path, "commit": start,
                      "hash": text_hash(read), "by": "review", **launch, "at": now()}
            if moved:  # it judged a plan that has since changed: it merges, listed, but doesn't count
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
            e = entry(record, mid)
            # what failed in the rounds the counts cover; a round recorded before rounds kept their items falls
            # back to the verdicts the previous review left in the file
            earlier = [r for r in counted_rounds(e) if r.get("verdict") == "fail"]
            names = {f["name"] for r in earlier for f in r.get("findings") or []}
            items = {i for r in earlier for i, v in (r.get("items") or {}).items() if v != "pass"}
            # a milestone counted before rounds kept their items: its last review's verdicts are still in the file.
            # Not after a reset (rounds 0), when the rounds those verdicts came from no longer count
            counted = under_review["rounds"] if "rounds" in under_review else under_review.get("fails", 0)
            if int(counted or 0) > 0 and not any("items" in r for r in earlier):
                items |= {i["id"] for i in under_review["items"] if (i.get("verdict") or "pass") != "pass"}
            found = [] if passed else [dict(f) for f in reviewed.get("findings") or []]  # a pass clears the last round's
            again = repeats(found, names, items) if not passed else []
            for f in found:
                f["repeat"] = f["name"] in again
            target.update(state=reviewed["state"], findings=found)
            if not found:
                target.pop("findings", None)
            by_id = {i["id"]: i for i in reviewed["items"]}
            for i in target["items"]:
                i["verdict"], i["review"] = by_id[i["id"]].get("verdict", ""), by_id[i["id"]].get("review", "")
            if not passed:
                target["rounds"] = int(target.get("rounds", 0) or 0) + 1
                target["fails"] = int(target.get("fails", 0) or 0) + (1 if again else 0)
                reset_proof(target, only_failed=True)
                if ladder(target) == "too_many_failed_reviews":
                    # the ladder has run out; only the owner reopens it
                    why = ("it ran out of review rounds" if int(target.get("fails", 0) or 0) < 4 else
                           "its failed reviews kept repeating the same findings after a re-plan")
                    target["state"] = "blocked"
                    target["blocked"] = {"reason": "too_many_failed_reviews", "what": why}
                    e["too_many_failed_reviews"] = {"why": why, "after": e.get("counted_after", 0), "at": now()}
            counts.update({k: int(target.get(k, 0) or 0) for k in ("fails", "replans", "rounds", "diagnoses")},
                          repeated=again, state=target["state"])
            write_json(t / done_path, doc)
            write.append(done_path)
            if kept:  # the earlier round's file moved; its record entry follows it
                rounds = [r for r in e.get("reviews") or [] if r.get("review") == review_path]
                if rounds:
                    rounds[-1]["review"] = kept
                for r in rounds[:-1]:  # overwritten before rounds were kept: only git history has them
                    r["review_in_history"] = r.pop("review")
            e.setdefault("reviews", []).append({"verdict": "pass" if passed else "fail", "commit": start,
                                                "review": review_path,
                                                "items": {i["id"]: i.get("verdict", "") for i in reviewed["items"]},
                                                **({"findings": found} if found else {}), **launch, "at": now()})
            if passed:
                e["accepted"] = {"by": "review", "commit": start, "review": review_path,
                                 "checked": ready_record(e).get("checked"), "at": now()}
        write_json(t / record_rel(prof, stem), record)
        return write + [record_rel(prof, stem)]

    loop_note(step="merging the review")
    ok, landed = loop_write(worktree, prof, key, change, f"orchestrate: review of {stem} {mid}: {verdict}")
    if not ok:
        return _result("INVALID", **info, merged=False,
                       problems=[f"the review was valid but couldn't be merged: {landed}"])
    if passed and not design:
        drop_hold(worktree, prof, key, mid)
    fails = counts.get("fails") if counts else None
    # On a FAIL, `next` is the command the escalation ladder calls for, with its word under `ladder`.
    if design and stale:
        why = (f"the plan changed while this design review ran ({', '.join(stale['moved'])}), so its verdict doesn't "
               "count for the plan at the tip: the review is kept and listed, and the design review is still owed")
        return _result("REVIEWED", **info, verdict=verdict, counted=False, not_counted=why, commit=start,
                       review=review_path, review_commit=landed, last_line=out["last_line"],
                       session=out.get("session"), **({"usage": out["usage"]} if out.get("usage") else {}),
                       next=next_cmd(loop_cmd("review", "--module", stem, "--milestone", "design", "--worktree",
                                              str(worktree), "--host", host), "lead", why))
    if not passed and not design:
        word = escalation(*(counts.get(k, 0) for k in ("fails", "replans", "rounds", "diagnoses")))
        action = ladder_next(word, stem, mid, counts, worktree, prof)
    elif not passed:
        action = design_review_next({"verdict": verdict, "review": review_path, "line": out["last_line"]}, stem,
                                    worktree, prof)
    else:
        action = after_pass(worktree, prof, key)
    return _result("REVIEWED", **info, verdict=verdict, commit=start, review=review_path, review_commit=landed,
                   fails=fails, **({"rounds": counts["rounds"], "repeated": counts["repeated"], "ladder": word}
                                   if not passed and not design else {}),
                   next=action, last_line=out["last_line"],
                   session=out.get("session"),
                   **({"usage": out["usage"]} if out.get("usage") else {}))


def _result(result: str, **fields) -> dict:
    return {"result": result, **fields}


def after_pass(worktree: Path, prof: dict, key: str) -> dict:
    """`next` after a passing review: the module's next milestone, or that it's finished."""
    try:
        ref = tip(worktree, prof, fetch=False)
        proj = project(worktree, prof, ref)
        step = next_step(key, proj, holds(worktree), me(worktree))
    except (TipError, SystemExit, KeyError) as e:
        return next_cmd(loop_cmd("ready", "--worktree", str(worktree)), "lead", f"see what's ready ({e})")
    if step["status"] == "finished":
        drop_tree(worktree, step["module"])
        return next_cmd(None, "lead", f"{step['module']} is finished: every milestone is accepted. Remove the worktree "
                                      "you built it in (`git worktree remove <path>`) once nothing in it is unmerged, "
                                      "since its build output takes disk the other builders need. Then start other "
                                      f"ready work (`{loop_cmd('ready', '--worktree', str(worktree))}`)")
    return next_for(step, worktree, prof, proj) or next_cmd(loop_cmd("ready", "--worktree", str(worktree)), "lead",
                                                            f"{step['module']} is {step['status']}; see what's ready")


def design_review_next(out: dict, stem: str, worktree: Path, prof: dict) -> dict:
    """What follows a design review that didn't say DESIGN OK."""
    wt = str(worktree)
    if out.get("verdict") == "DESIGN CHANGES":
        m = re.search(r"(\d+)\s+must_fix", out.get("line") or "")
        found = f"its {m.group(1)} Must Fix findings" if m else "its Must Fix findings"
        task = (f"The design review of {stem} at {out.get('review')} asked for changes. Resolve {found} in the "
                "design and the plan. Its Suggestions are yours to take or leave; say which you took and why.")
        return next_cmd(loop_cmd("plan", "--worktree", wt, "--task", task), "planner",
                        "the design review found Must Fix findings; send them to the planner, then review the design "
                        "again. Report the module only if a Must Fix finding returns after the planner fixed it, or "
                        "needs an owner decision", findings=out.get("review"))
    host = out.get("host") or default_host(prof)
    return next_cmd(loop_cmd("review", "--module", stem, "--milestone", "design", "--worktree", wt, "--host",
                             other_host(host)), "lead",
                    f"the design review ended {out.get('result')} without a verdict; run it again, on the other host "
                    "if it was the host that failed")


def review_prompt(host: str, prof: dict, stem: str, mid: str, commit: str, done: str, review: str,
                  milestone: dict | None, entry: dict, feedback: list[dict] | None, judged: list[dict], moved: str = "",
                  context: str = "", design: bool = False) -> str:
    """A reviewer's prompt. `entry` is the milestone's entry in the record file, `judged` the diagnoses that kept
    the plan and blamed the reviews, `moved` the note on a Ready for Review the script set after the builder's
    commit, and `context` what changed since the last design review."""
    template = DESIGN_REVIEW_TEMPLATE if design else REVIEW_TEMPLATE
    return template.format(milestone=mid, module=stem, commit=commit, done=done, captures=review[:-len(".md")],
                           loop=LOOP, checks="" if design else checks_note(prof, milestone,
                                                                            ready_record(entry).get("checked")),
                           changed=f"\n{context}\n" if context else "", briefs="", review=review,
                           skill=skill_note("review-milestone", host),
                           answers=moved + review_notes(mid, prof, stem, feedback,
                                                        [] if design else history_lines(entry), judged))


def cmd_review(a: argparse.Namespace) -> None:
    new_command()
    out = review_once(a)
    result = out.pop("result")
    if result in ("HOST_FAILED", "SCRIPT_FAILED", "INVALID", "WRONG_MODEL_OR_EFFORT") and "next" not in out:
        again = ["review", "--module", out.get("module") or a.module, "--milestone", a.milestone]
        again += [] if a.milestone == "design" else ["--commit", a.commit]
        again += ["--worktree", str(Path(a.worktree).resolve())]
        if result == "INVALID":  # the request was wrong, not the host: another host would refuse it the same way
            out["next"] = next_cmd(loop_cmd(*again), "lead", "nothing merged; fix what `problems` names, then run "
                                   "the review again. Without --host, the settings' Review host picks the reviewer")
        elif a.milestone == "design":
            out["next"] = next_cmd(loop_cmd(*again, "--host", other_host(out.get("host") or "codex")), "lead",
                                   "nothing merged; run the review again, on the other host if you can")
        else:  # a milestone's reviewer follows the settings' Review host, which never picks the builder's host
            out["next"] = next_cmd(loop_cmd(*again), "lead", "nothing merged; run the review again. Without --host, "
                                   "the settings' Review host picks the reviewer, which keeps it off the builder's host")
    emit(result, **out)


def plan_owed(worktree: Path, start: str, message: str) -> str | None:
    """None when the planner's turn ended with a result: BLOCKED or NEEDS_CONTEXT, or `PLANNED` after changing
    files, with a design beside every done-when file it changed. Otherwise what's missing, for the nudge. A progress
    report isn't a result. The script finds the changed files itself and prints them in its result, so the planner's
    report, not a file list, is what the lead reads at its end; a list after `PLANNED:`, as before 2.0, is still
    checked."""
    line = report_line(message)
    word, _, rest = line.partition(":")
    if report_word(message) in ("BLOCKED", "NEEDS_CONTEXT") or KEEP_LINE.match(line):
        return None
    if word.strip("`* ") != "PLANNED":
        return "Your last line wasn't `PLANNED`. Finish the plan's files, then end with that line, or with " \
               "BLOCKED or NEEDS_CONTEXT, or, for a diagnosis that keeps the plan, the `KEEP` line your task gives."
    prof = profile(worktree, missing_ok=True)
    named = [n.strip("`*'\" ") for n in re.split(r"[,\s]+", rest) if n.strip("`*'\" ")]
    changed = changed_paths(worktree, start)
    gaps = [f"{n} doesn't exist" for n in named if not (worktree / n).exists()]
    gaps += [f"{n} isn't changed" for n in named if (worktree / n).exists() and n not in changed]
    gaps += [f"{p} has no design at {design_rel(prof, where[0])}" for p in changed
             if (where := module_of(prof, p)) and where[1] == "done" and (worktree / p).exists()
             and not (worktree / design_rel(prof, where[0])).exists()]
    if not changed:
        gaps.insert(0, "no file has changed")
    return None if not gaps else "The plan isn't complete: " + "; ".join(gaps) + \
        ". Finish it, then end with `PLANNED`."


def keep_plan(worktree: Path, prof: dict, start: str, keep: re.Match, host: str, info: dict, out: dict,
              tree: Path | None = None) -> None:
    """A planner asked to diagnose a milestone kept its plan and named who has to act. The script records that,
    starts the milestone's counts again, and says what follows; a planner naming the owner blocks it with too many
    failed reviews, for the owner to decide. `tree` is the checkout the planner worked in, when that isn't
    `worktree`."""
    module, mid, who, why = keep.group(1), keep.group(2), keep.group(3).lower(), keep.group(4).strip()
    if changed := changed_paths(tree or worktree, start):
        emit("INVALID", **info, **out, merged=False,
             **(keep_leftovers(tree, prof, "diagnosis that kept the plan") if tree and tree != worktree else {}), problems=[
            f"the last line keeps the plan, but the turn changed {', '.join(changed[:5])}; end with PLANNED to merge a "
            "changed plan, or leave every file as it was"])
    try:
        stem = module_stem(worktree, prof, module)
        doc = json.loads(show(worktree, tip(worktree, prof), done_rel(prof, stem)) or "")
        m = find(doc, mid)
    except (TipError, SystemExit, json.JSONDecodeError, KeyError) as e:
        emit("INVALID", **info, **out, merged=False, problems=[f"KEEP names {module} {mid}, which can't be read: {e}"])
    if ladder(m) != "diagnose":
        emit("INVALID", **info, **out, merged=False, problems=[
            f"KEEP is the answer to a diagnosis, and {stem} {mid} isn't owed one (its ladder is {ladder(m)})"])
    try:  # the rounds the planner diagnosed, which the owner sees if it's theirs to decide
        diagnosed = ((json.loads(show(worktree, tip(worktree, prof), record_rel(prof, stem)) or "{}")
                      .get("milestones") or {}).get(mid) or {}).get("counted_after", 0)
    except (TipError, SystemExit, json.JSONDecodeError):
        diagnosed = None
    at = now()

    def change(t):
        doc = json.loads((t / done_rel(prof, stem)).read_text())
        target = find(doc, mid)
        target.update(fails=0, rounds=0, diagnoses=int(target.get("diagnoses", 0) or 0) + 1)
        record = record_in(t, prof, stem, doc)
        e = entry(record, mid)
        if who == "owner":
            why_owner = f"a planner read every round, kept the plan, and found it needs your decision: {why}"
            target["state"] = "blocked"
            target["blocked"] = {"reason": "too_many_failed_reviews", "what": why_owner[:500]}
            e["too_many_failed_reviews"] = {"why": why_owner, "after": e.get("counted_after", 0), "at": at}
        e.setdefault("diagnoses", []).append({"who": who, "why": why, "host": host, "at": at})
        e["counted_from"], e["counted_after"] = at, len(e.get("reviews") or [])
        write_json(t / done_rel(prof, stem), doc)
        write_json(t / record_rel(prof, stem), record)
        return [done_rel(prof, stem), record_rel(prof, stem)]

    ok, landed = loop_write(worktree, prof, "_plan", change, f"orchestrate: diagnosis of {stem} {mid}: {who}")
    if not ok:
        emit("INVALID", **info, **out, merged=False, problems=[f"couldn't record the diagnosis: {landed}"])
    wt = str(worktree)
    findings = FINDINGS_TEMPLATE.format(milestone=mid, module=stem, evidence=prof["evidence"])
    if who == "builder":
        then = next_cmd(loop_cmd("run", "--module", stem, "--worktree", wt, "--fresh", "--message",
                                 f"{findings}\n\nA planner read every round and kept the plan: {why}"), "lead",
                        f"the planner kept {stem} {mid}'s plan and found the building at fault; start the builder "
                        "again in a new session with its reasons")
    elif who == "reviewer":
        then = next_cmd(loop_cmd("run", "--module", stem, "--worktree", wt, "--fresh", "--message",
                                 f"A planner read every review of {mid} and judged that the findings went beyond its "
                                 f"items: {why}\n\nDo what the items ask, prove them, merge and end with DONE, and the script "
                                 "checks the work and sets it Ready for Review again. The next reviewer is told of "
                                 "this judgement."), "lead",
                        f"the planner kept {stem} {mid}'s plan and found the reviews went beyond its items; start the "
                        "builder again in a new session to prove the items")
    else:
        then = reopen_next(stem, mid, wt, worktree, prof, f"a planner read every round, kept the plan, and found it "
                                                         f"needs your decision: {why}", after=diagnosed)
    emit("KEPT", **info, **out, merged=True, commit=landed, module=stem, milestone=mid, who=who, why=why, next=then)


def done_docs_at(worktree: Path, prof: dict, ref: str) -> dict:
    """The done-when files at `ref`, by module, parsed (ones that don't parse are left out)."""
    out = {}
    for stem in modules_at(worktree, prof, ref):
        try:
            out[stem] = json.loads(show(worktree, ref, done_rel(prof, stem)) or "")
        except json.JSONDecodeError:
            pass
    return out


def keep_leftovers(tree: Path, prof: dict, task: str) -> dict:
    """Keeps what a planner left in the script's planner checkout before the next plan resets it. Uncommitted files go
    to a stash, and commits the tip lacks go to a branch; every worktree of the repository sees both. Returns
    {stash, branch} for what was kept, so the result can name it."""
    kept = {}
    label = f"planner: {task.splitlines()[0][:60] if task.strip() else ''}"
    try:
        ahead = git(tree, "rev-list", f"{tip(tree, prof, fetch=False)}..HEAD").stdout.split()
    except TipError:
        ahead = []
    if ahead:  # named by the commit, so the same commit kept twice is one branch
        branch = f"orchestrate/planner-{head_commit(tree)[:12]}"
        if git(tree, "branch", "--force", branch, "HEAD").returncode == 0:
            kept["branch"] = branch
    if git(tree, "status", "--porcelain").stdout.strip():
        if git(tree, "stash", "push", "--include-untracked", "-m", label).returncode == 0:
            kept["stash"] = f"the latest stash, '{label}'"
    return kept


def kept_text(kept: dict) -> str:
    """The end of a sentence saying where a planner's unmerged work was kept, or where it was left."""
    if "left_uncommitted" in kept:
        return "; its files are still uncommitted in the worktree"
    parts = [kept["stash"]] if "stash" in kept else []
    parts += [f"the branch {kept['branch']}"] if "branch" in kept else []
    return f"; its work is kept in {' and '.join(parts)}" if parts else ""


PLANNER_POLL_S = 2.0  # how often a second planner checks whether the first has finished


def cmd_plan(a: argparse.Namespace) -> None:
    new_command()
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, missing_ok=True)  # a first plan writes the project settings itself
    host, model, effort = resolve(a, prof, "plan")
    preflight(host, worktree, "plan")
    info = dict(host=host, model=model, effort=effort)
    task_line = a.task.splitlines()[0][:80] if a.task.strip() else ""
    if not run_lock(worktree, "_plan"):  # one planner per repository: wait for it, then plan on the tip it merged
        install_stop()
        who = run_holder_info(worktree, "_plan")
        loop_register(worktree, "plan", task=task_line, waiting_for="another planner" + holder_text(who), **info)
        print(f"waiting for another planner on this repository{holder_text(who)}", file=sys.stderr, flush=True)
        while not run_lock(worktree, "_plan"):
            if _STOP:
                emit("PAUSED", **info, merged=False, reason="stopped while waiting for another planner to finish")
            time.sleep(PLANNER_POLL_S)
    install_stop()
    loop_register(worktree, "plan", task=task_line, **info)
    if empty := no_base(worktree, prof):  # say so before a planner spends a turn whose files couldn't merge
        emit("SCRIPT_FAILED", **info, reason=str(empty), next=empty.next)
    if (worktree / PROFILE_FILE).exists():
        # The planner works in the script's own checkout of the tip, as a reviewer does, so the lead's worktree is
        # never in its way and no worktree is made for it. --worktree only names the repository.
        try:
            tree = verify_tree(worktree, "_planner", tip(worktree, prof))
        except TipError as e:
            emit("SCRIPT_FAILED", **info, reason=f"the planner's checkout of the main branch's tip couldn't be made: {e}")
    else:  # a first plan, before the settings name a base branch, works in the worktree it was given
        tree = worktree
        if dirty := git(tree, "status", "--porcelain").stdout.strip():
            emit("INVALID", **info, problems=["the first planner needs a clean worktree, so the script can tell its "
                                              "files from anything else: " + dirty[:300]])

    def leave() -> dict:
        """What a turn that doesn't merge left behind, kept where the lead can find it, since the script's checkout is
        reset for the next planner."""
        paths = changed_paths(tree, start)
        if tree == worktree:
            return {"left_uncommitted": paths}
        return {"set_aside": paths, **keep_leftovers(tree, prof, a.task)}

    start = head_commit(tree)
    seen = reflog_size(tree)
    before = done_docs_at(tree, prof, start)
    prompt = PLAN_TEMPLATE.format(task=a.task, skill=skill_note("plan-module", host), loop=LOOP)
    out = one_session(host, prof, model, effort, tree, prompt, "plan", lambda msg: plan_owed(tree, start, msg),
                      a.turn_timeout_hours * 3600, title=plan_title(worktree, tree, prof, a.task))
    result = out.pop("result")
    out.pop("observed", None)
    if out.get("owed") is None:
        out.pop("owed", None)
    word = report_word(out.get("report", ""))
    if result == "FINISHED" and word in ("BLOCKED", "NEEDS_CONTEXT"):
        result = word
    if result != "FINISHED":  # a progress report, a blocker or a host failure: nothing merges
        emit(result, **info, **out, merged=False, **leave())
    try:
        prof = profile(tree, strict=True)
    except SystemExit as e:
        emit("PLANNED", **info, **out, merged=False, problems=[str(e)], **leave())
    if keep := KEEP_LINE.match(report_line(out.get("report", ""))):
        keep_plan(worktree, prof, start, keep, host, info, out, tree=tree)

    # What a turn wrote is what it left uncommitted; that is all the script commits and merges. Its HEAD may have moved
    # along the tip (a `merge` elsewhere fast-forwards the checkout holding the base branch), never off it.
    try:
        fresh = tip(tree, prof)
    except TipError as e:
        emit("PLANNED", **info, **out, merged=False, problems=[f"the turn can't be checked, so nothing merged: {e}"],
             **leave())
    if forged := record_tampering(tree, prof, start, fresh):
        kept = leave()
        emit("INVALID", **info, **out, merged=False, **kept, problems=[
            f"while this turn ran, {plural(len(forged), 'commit')} without the script's trailer changed a record "
            f"file on the tip: {', '.join(forged)}"], next=next_cmd(
            None, "lead", "report it to the owner, who decides what to do with those commits: they reached the "
            "main branch's tip during a planner turn, and only the script writes record files. The script doesn't take "
            f"commits back out. Nothing from this turn was merged{kept_text(kept)}", decides="owner"))
    if made := commits_made(tree, seen):  # read before the script makes its own commit here
        kept = leave()
        emit("INVALID", **info, **out, merged=False, **kept, problems=[
            f"the planner committed ({plural(len(made), 'commit')} in its checkout's reflog during the turn: "
            f"{'; '.join(made[:5])}); the script merges only what a planner leaves uncommitted"], next=next_cmd(
            None, "lead", "nothing merged. Any commit that reached the main branch's tip is already there"
            f"{kept_text(kept)}; look at what's there and keep or drop it yourself, then plan again"))
    if own := git(tree, "log", "--format=%h %s", f"{fresh}..HEAD").stdout.strip().splitlines():
        kept = leave()
        emit("INVALID", **info, **out, merged=False, **kept, problems=[
            f"the planner committed ({plural(len(own), 'commit')} the tip doesn't have: "
            f"{'; '.join(own[:5])}); the script merges only what a planner leaves uncommitted"], next=next_cmd(
            None, "lead", f"nothing was merged{kept_text(kept)}; look at what's there and keep or drop it yourself, then "
            "plan again"))
    start = head_commit(tree)
    before = done_docs_at(tree, prof, start)
    changed = changed_paths(tree, start)
    problems = [f"changed {p}; only the script writes record files" for p in changed
                if (where := module_of(prof, p)) and where[1] == "record" or p.endswith("-ACCEPTED.json")]
    problems += [f"changed {p}, which the script writes from the records after each one it merges; leave it as it was"
                 for p in changed if p == status_rel(prof)]
    problems += flat_names(prof, changed)
    problems += plan_checks(tree, prof, changed)
    modules = []
    for p in changed:
        if (where := module_of(prof, p)) and where[1] == "done" and (tree / p).exists():
            stem = where[0]
            try:
                doc = json.loads((tree / p).read_text())
            except json.JSONDecodeError as e:
                problems.append(f"{p} isn't valid JSON: {e}")
                continue
            problems += [f"{stem}: {x}" for x in validate(doc, stem.upper())]
            if not validate(doc, stem.upper()):
                problems += [f"{stem}: {x}" for x in delta_problems(before.get(stem), doc, "plan")]
            modules.append(stem)
    if problems:
        if tree == worktree:
            wt = shlex.quote(str(worktree))
            command, kept = f"git -C {wt} stash push --include-untracked -m 'refused planner turn' && ", {}
            where = "the latest git stash"
        else:
            kept = leave()
            command, where = "", kept.get("stash", "a git stash")
        emit("INVALID", **info, **out, merged=False, problems=problems[:20], **kept, next=next_cmd(
            command + loop_cmd("plan", "--worktree", str(worktree), "--task",
                               f"{a.task}\n\nYour last turn on this was refused, for: {'; '.join(problems[:5])}. Its "
                               f"files are in {where} (`git stash list`, then `git stash show -p --include-untracked "
                               "<stash>`); reuse what holds up."),
            "lead", "the plan didn't merge and its files are set aside in a stash (nothing is lost). This gives a "
                    "planner the task again with the problems, since only a planner turn may fix them"))
    if git(tree, "status", "--porcelain").stdout.strip():
        git(tree, "add", "-A")
        git(tree, *ident(tree), "commit", "--quiet", "-m", f"Plan: {a.task.splitlines()[0][:60]}",
            "-m", a.task)  # the subject is short; the body keeps the whole task
    try:  # the tip the plan merges on: its counts are the ones a re-plan settles
        prior_ref = tip(tree, prof)
    except TipError:
        prior_ref = None
    ok, landed = land(tree, prof)
    if not ok:
        emit("PLANNED", **info, **out, merged=False, problems=[f"couldn't merge the plan: {landed}"], **leave())

    def change(t):
        written = []
        for stem in modules:
            path = t / done_rel(prof, stem)
            doc = json.loads(path.read_text())
            rec_path = t / record_rel(prof, stem)
            if rec_path.exists():
                record = json.loads(rec_path.read_text())
            elif stem in before and not validate(before[stem]):
                # first loop write for a module that stood before this plan without a record: as it stood, only in
                # a repository that had no records; otherwise it's new, and nothing in it is accepted
                record = adopt(before[stem],
                               text_hash(show(worktree, start, design_rel(prof, stem))),
                               unrecorded(t, prof, "HEAD"))
            else:
                record = {"module": stem, "design": None, "milestones": {}}
            try:
                prior = json.loads(show(worktree, prior_ref, done_rel(prof, stem)) or "") if prior_ref else None
            except json.JSONDecodeError:
                prior = None
            was = prior or before.get(stem)
            settled = settle_replans(was, doc, stem)
            keep_counts(was, doc, settled, stem)
            replanned.extend(settled)
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
        emit("PLANNED", **info, **out, merged=True, commit=landed, problems=[f"couldn't record the definitions: {detail}"])
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
    emit("PLANNED", **info, **out, merged=True, commit=detail, modules=modules, design_review_owed=owed,
         files=changed,
         **({"assumptions": {k: n for k, n in found.items() if n},
             "assumptions_where": "lines starting `Assumption:` in each module's PLAN.md; `report` lists them for "
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
    sync_holds(worktree, prof)
    return ref, proj


def cmd_ready(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, missing_ok=True)
    empty = {"ready": [], "waiting": [], "review_owed": [], "design_not_approved": [], "blocked": [], "taken": [],
             "finished": [], "invalid": []}
    if not_yet := unplanned(worktree):
        try:
            ref = tip(worktree, prof)
        except TipError:
            ref = None
        key = "behind" if not_yet.get("behind") else "unplanned"
        print(json.dumps({"tip": ref, **empty, key: not_yet["reason"], "next": not_yet["next"]}, indent=2))
        return
    ref, proj = read_project(worktree, prof)
    held, mine = holds(worktree), me(worktree)
    out = {"tip": ref, **empty}
    steps = []
    folder = Path(git_common_dir(worktree)) / "orchestrate"
    for key in sorted(proj):
        step = next_step(key, proj, held, mine)
        steps.append(dict(step))
        if step["status"] == "finished" and run_holder(folder, step["module"].upper()) is None:
            drop_tree(worktree, step["module"])  # also frees checkouts left from before this was done on finishing
        if step_key(step) in ("waiting:for_replan", "waiting:for_diagnosis", "blocked:too_many_failed_reviews"):
            step["next"] = next_for(step, worktree, prof, proj)  # not the builder's: say whose it is
        out[step.pop("status")].append(step)
    if ahead := plan_ahead(worktree, prof, ref, proj):
        out["plan_ahead"] = ahead
    drift = plan_drift(worktree, prof, ref)
    if drift["uncommitted"] or drift["unmerged"] or not out["ready"]:
        out.update(drift_fields(drift, worktree, None if out["ready"] else
                                nothing_ready_next(steps, worktree, prof, proj, ahead)))
    out.update(profile_note(drift, prof))
    if found := table_warnings(worktree, prof, ref, [e["stem"] for e in proj.values()]):
        out["module_table"] = found
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
    if getattr(a, "format", "text") == "md":  # the owner's page, as the script commits it, plus what hasn't merged here
        print(status_page(worktree, prof, ref, proj, drift["uncommitted"] + drift["unmerged"]), end="")
        return
    if drift["uncommitted"] or drift["unmerged"]:
        fields = drift_fields(drift, worktree)
        print(f"{fields['unmerged_plans']['note']}; merge them with `{fields['next']['command']}`")
    if note := profile_note(drift, prof):
        print(note["settings_differ"])
    for warning in table_warnings(worktree, prof, ref, [e["stem"] for e in proj.values()]):
        print(f"warning: {warning}")
    for stray in stray_plans(worktree, prof):
        print(f"warning: {stray} is a plan file outside {prof['plans']}, where no agent looks for plans; a planner "
              "moves what still matters into a module's PLAN.md or LOG.md and deletes it")
    if not proj:
        print(f"no modules planned at {base_ref(prof)} yet (no done-when files under {prof['plans']})")
    keys = [a.module.upper()] if a.module else sorted(proj)
    for key in keys:
        if key not in proj:
            print(f"{a.module}: not planned at the main branch's tip" + running(key))
            continue
        e, step = proj[key], next_step(key, proj, holds(worktree), me(worktree))
        print(f"{e['stem']}: {step['status']}" + (f": {step['reason']}" if step.get("reason") else "") +
              (f" ({step['milestone']})" if step.get("milestone") else "") + running(key))
        for problem in e["problems"] or step.get("problems", []):
            print(f"  invalid: {problem}")
        if step_key(step) in ("waiting:for_replan", "waiting:for_diagnosis"):
            print(f"  {step['milestone']} failed review {plural(step.get('rounds', 0), 'time')}, "
                  f"{step['fails']} on a repeated finding; a planner looks at it before any more building:\n"
                  f"    {next_for(step, worktree, prof, proj)['command']}")
        if e["problems"]:
            continue
        for m in e["doc"]["milestones"]:
            flags, state = [], m.get("state")
            if accepted(m, e["record"]):
                flags.append("accepted")
            elif m["id"] == step.get("milestone"):
                if step["status"] == "ready" and state in ("done", "ready_for_review"):
                    # the builder's file says so, but the script hasn't checked it yet; `run` checks it
                    state = f"{state}, unchecked"
                    flags.append("the script hasn't checked this yet; `run` checks it")
                else:
                    flags.append(step["status"].replace("_", " ") +
                                 (f": {step['reason'].replace('_', ' ')}" if step.get("reason") else ""))
                if step.get("depends_on"):
                    flags.append("on " + ", ".join(step["depends_on"]))
                if step.get("blocked"):
                    flags.append(step["blocked"].get("what") or step["blocked"]["reason"])
            reviews = (e["record"]["milestones"].get(m["id"]) or {}).get("reviews") or []
            if reviews:
                flags.append(f"last review {reviews[-1]['verdict']} {reviews[-1].get('at', '')}".strip())
            print(f"  {m['id']}\t{state}\tfails={m.get('fails', 0)} rounds={m.get('rounds', 0)}\t{passing(m)}/{len(m['items'])} pass"
                  f"\t{m.get('name', '')}" + ("\t" + "; ".join(flags) if flags else ""))


def cmd_next(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree)
    stem = module_stem(worktree, prof, a.module)
    try:  # the count at the main branch's tip, where the review was merged, rather than this worktree's older copy
        doc = json.loads(show(worktree, tip(worktree, prof), done_rel(prof, stem)) or "")
    except (TipError, json.JSONDecodeError, SystemExit):
        doc = load_done(worktree, stem, prof)
    milestone = find(doc, a.milestone)
    counts = {k: int(milestone.get(k, 0) or 0) for k in ("fails", "replans", "rounds", "diagnoses")}
    action = "too_many_failed_reviews" if milestone.get("state") == "blocked" and \
        blocked_of(milestone)["reason"] == "too_many_failed_reviews" else ladder(milestone)
    if action in ("replan", "diagnose", "too_many_failed_reviews"):  # for the planner or the owner, rather than the builder's findings
        then = ladder_next(action, stem, milestone["id"], counts, worktree, prof)
        message = (replan_task(stem, milestone["id"], counts["fails"], prof, worktree) if action == "replan" else
                   diagnose_task(stem, milestone["id"], counts["rounds"], prof, worktree) if action == "diagnose" else
                   then["why"])
    else:
        message = FINDINGS_TEMPLATE.format(milestone=milestone["id"], module=stem, evidence=prof["evidence"])
        then = ladder_next(action, stem, milestone["id"], counts, worktree, prof) if action != "none" else None
    print(json.dumps({"milestone": milestone["id"], **counts,
                      "action": action, "message": message, **({"next": fit_next(then)} if then else {})}))


def cmd_settings(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    if not_yet := unplanned(worktree):
        print(json.dumps({"planned": False, "problems": [not_yet["reason"]], "next": not_yet["next"],
                          **({"behind": not_yet["behind"]} if not_yet.get("behind") else {})}, indent=2))
        sys.exit(1)
    prof = profile(worktree, strict=True, flat_ok=True, old_ok=True)  # the settings print; old layout or names below
    if flat_modules(worktree, prof["plans"]):
        prof["flat_layout"] = flat_refusal(worktree, prof["plans"])[len("error: "):]
    if old := old_names_here(worktree, prof["plans"]):
        prof["old_names"] = old_names_refusal(worktree, old)[len("error: "):]
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


# A background job is a long command an agent starts with `background` and waits for with `wait`. In Thrum, builders
# waited for long captures with `sleep` and `tail`: CULLING M1 spent 86M of its 113M input tokens on those checks, each
# one re-reading the whole conversation, and listed processes with `ps`, which the Codex sandbox refuses. A job runs in
# its own process session, so it outlives the turn that started it, and its log is under the git directory, outside
# the worktree, where neither the clean checkout nor a commit picks it up.
JOBS_FILE = "jobs.jsonl"
JOB_WAIT_S = 540.0  # under the ten-minute limit of Claude's Bash tool
JOB_TAIL_LINES = 30
JOB_TAIL_CHARS = 3000


def jobs_dir(worktree: Path) -> Path:
    path = loop_dir(worktree) / "jobs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def job_rows(worktree: Path) -> list[dict]:
    """This repository's jobs, oldest first."""
    path = loop_dir(worktree) / JOBS_FILE
    rows = []
    for line in (path.read_text().splitlines() if path.exists() else []):
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    return rows


def job_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:  # it exists, under a sandbox that won't let this process signal it
        return True
    return True


def job_state(job: dict) -> tuple[str, int | None]:
    """`running`, `exited` with the exit code, or `gone` (it stopped without writing one, as when it was killed)."""
    code_file = Path(job["log"] + ".exit")
    if code_file.exists():
        try:
            return "exited", int(code_file.read_text().strip() or "-1")
        except ValueError:
            return "exited", None
    return ("running", None) if job_alive(int(job["pid"])) else ("gone", None)


def job_tail(log: str, lines: int = JOB_TAIL_LINES) -> str:
    try:
        with open(log, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            size = handle.tell()
            handle.seek(max(0, size - 64 * 1024))
            text = handle.read().decode(errors="replace")
    except OSError:
        return ""
    text = "\n".join(text.splitlines()[-lines:])
    return text[-JOB_TAIL_CHARS:]


def job_age(job: dict) -> str:
    seconds = max(0, int(time.time() - job.get("started_s", time.time())))
    return f"{seconds // 3600}h{seconds % 3600 // 60:02d}m" if seconds >= 3600 else f"{seconds // 60}m{seconds % 60:02d}s"


def worktree_jobs(worktree: Path, running_only: bool = False) -> list[dict]:
    """The jobs started from `worktree`, newest last, each with its state, exit code and age."""
    here = str(worktree.resolve())
    out = []
    for job in job_rows(worktree):
        if job.get("worktree") != here:
            continue
        state, code = job_state(job)
        if running_only and state != "running":
            continue
        out.append({**job, "state": state, **({"exit": code} if code is not None else {}), "age": job_age(job)})
    return out


MERGE_WAIT_S = 2.5 * 3600  # `merge` may run the test command for an hour, and twice when its first push is refused
MERGE_POLL_S = 2.0  # how often the run checks whether a builder's background merge has ended


def is_merge_job(command: str) -> bool:
    """Whether a background job's command is this script's `merge`."""
    try:
        words = shlex.split(command)
    except ValueError:
        words = command.split()
    return any(w.endswith("agent_loop.py") for w in words) and "merge" in words


def wait_for_merges(worktree: Path, limit_s: float = MERGE_WAIT_S) -> list[str]:
    """Waits for the `merge` jobs still running in the builder's worktree, up to `limit_s`, and returns each one's id
    with how it ended. Nothing to wait for returns an empty list at once."""
    out = []
    deadline = time.time() + limit_s
    for job in worktree_jobs(worktree, running_only=True):
        if not is_merge_job(job.get("command", "")):
            continue
        loop_note(step=f"waiting for the builder's merge, background job {job['id']}")
        while job_state(job)[0] == "running" and time.time() < deadline and not _STOP:
            time.sleep(MERGE_POLL_S)
        state, code = job_state(job)
        out.append(f"{job['id']}: " + (f"exited {code}" if state == "exited" else state))
    return out


def cmd_background(a: argparse.Namespace) -> None:
    """Starts a command as a background job and prints its id, pid and log at once."""
    command = list(a.command_args)
    if command[:1] == ["--"]:
        command = command[1:]
    if not command:
        raise SystemExit("error: usage: background [--worktree PATH] [--log PATH] -- COMMAND... (one argument runs "
                         "in the shell)")
    where = Path(a.worktree or Path.cwd()).resolve()
    if subprocess.run(["git", "-C", str(where), "rev-parse"], capture_output=True).returncode != 0:
        raise SystemExit(f"error: {where} is not in a git repository, so there is no place to record the job")
    job_id = f"{time.strftime('%Y%m%d-%H%M%S')}-{os.getpid()}"
    log = Path(a.log).resolve() if a.log else jobs_dir(where) / f"{job_id}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    exit_file = f"{log}.exit"
    Path(exit_file).unlink(missing_ok=True)
    # The shell around the command writes its exit code beside the log, so `wait` and `jobs` can report it after the
    # process that started the job has gone.
    if len(command) == 1:
        argv = ["sh", "-c", 'sh -c "$1"; echo $? > "$ORCHESTRATE_JOB_EXIT"', "sh", command[0]]
    else:
        argv = ["sh", "-c", '"$@"; echo $? > "$ORCHESTRATE_JOB_EXIT"', "sh", *command]
    with open(log, "ab") as out:
        proc = subprocess.Popen(argv, cwd=where, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                                start_new_session=True, env={**os.environ, "ORCHESTRATE_JOB_EXIT": exit_file})
    job = {"id": job_id, "pid": proc.pid, "worktree": str(where), "command": shlex.join(command)
           if len(command) > 1 else command[0], "log": str(log), "started": now(), "started_s": time.time(),
           "role": os.environ.get("ORCHESTRATE_ROLE")}
    with open(loop_dir(where) / JOBS_FILE, "a") as handle:
        handle.write(json.dumps(job) + "\n")
    print(json.dumps({"job": job_id, "pid": proc.pid, "log": str(log),
                      "wait": loop_cmd("wait", job_id, "--worktree", str(where))}))


def cmd_jobs(a: argparse.Namespace) -> None:
    """The background jobs started from this worktree in the last day, with their state."""
    where = Path(a.worktree).resolve()
    since = time.time() - 24 * 3600
    jobs = [j for j in worktree_jobs(where) if j.get("started_s", 0) >= since or j["state"] == "running"]
    if a.json:
        print(json.dumps(jobs, indent=2))
        return
    if not jobs:
        print("No background jobs from this worktree in the last day.")
        return
    for j in jobs:
        state = f"exited {j['exit']}" if j["state"] == "exited" else j["state"]
        print(f"{j['id']}  pid {j['pid']}  {state}  {j['age']}  {j['command'][:100]}\n    log: {j['log']}")


def cmd_wait(a: argparse.Namespace) -> None:
    """Blocks until a job ends, its log matches --until, or --timeout passes, then prints the state and the log's
    last lines. One call that waits nine minutes costs one turn of the conversation; a sleep-and-tail loop costs one
    per check."""
    where = Path(a.worktree).resolve()
    if a.job:
        jobs = [j for j in job_rows(where) if j.get("id") == a.job or str(j.get("pid")) == a.job]
        if not jobs:
            raise SystemExit(f"error: no job {a.job}; `jobs --worktree {where}` lists them")
        job = jobs[-1]
    elif a.file:
        job = {"id": None, "pid": a.pid or 0, "log": str(Path(a.file).resolve())}
    else:
        raise SystemExit("error: name a job (from `background` or `jobs`), or give --file with --pid or --until")
    if not a.job and not a.pid and not a.until:
        raise SystemExit("error: with --file, give --until, --pid or both, so the wait knows when to stop")
    pattern = re.compile(a.until) if a.until else None
    deadline, outcome = time.time() + a.timeout, None
    while outcome is None:
        if pattern and pattern.search(job_tail(job["log"], 400)):
            outcome = f"matched {a.until!r}"
        elif job.get("id") or job.get("pid"):
            state, code = job_state(job) if job.get("id") else (
                ("running", None) if job_alive(int(job["pid"])) else ("gone", None))
            if state == "exited":
                outcome = f"exited {code}"
            elif state == "gone":
                outcome = "ended (no exit code recorded)"
        if outcome is None:
            if time.time() >= deadline:
                outcome = (f"still running after {a.timeout:.0f} s; wait again" if job.get("id") or job.get("pid")
                           else f"no match after {a.timeout:.0f} s; wait again")
                break
            time.sleep(min(5.0, max(0.5, deadline - time.time())))
    label = job.get("id") or job["log"]
    print(f"{label}: {outcome}\n--- last lines of {job['log']} ---\n{job_tail(job['log'], a.lines)}")


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


def try_check(tree: Path, command: str, lock: str | None, timeout_s: float, plans: str | None = None) -> dict:
    """One check run in `tree`: `pass`, `fail` (it ran and failed: likely the work isn't there yet; read the output),
    `error` (it can't run as written, told only where certain; see check_broken) or `timeout`. A pass on the same
    files is reused, as `run_check` says, and the whole output is saved, with the files named in `stdout` and
    `stderr`."""
    in_git = subprocess.run(["git", "-C", str(tree), "rev-parse"], capture_output=True).returncode == 0
    r = run_check(tree, command, lock if in_git else None, timeout_s, plans, save=in_git)
    code, out, err = r["exit"], r["out"], r["err"]
    saved = {k: r[k] for k in ("stdout", "stderr") if r.get(k)}
    if r["reused"]:
        return {"exit": 0, "result": "pass", "reused": r["reused"], **saved,
                "output": "(not run again: it passed on these same files before)"}
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
    return {"exit": code, "result": result, **({"why": why} if why else {}), "output": text[-1500:], **saved}


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
            proof = [k for k in ("inspect", "ask") if i.get(k)] + \
                ([f"needs {i['needs'].get('type')}"] if isinstance(i.get("needs"), dict) else [])
            items.append({"id": i["id"], "result": "no check", "proof": proof})
            continue
        items.append({"id": i["id"], "check": i["check"], **(({"lock": i["lock"]}) if i.get("lock") else {}),
                      **try_check(tree, i["check"], i.get("lock"), a.timeout, prof.get("plans"))})
    # the project's test command gates every Ready for Review too; a planner trying the checks it wrote leaves it
    # out, because in Thrum it held the shared GPU builders were using, and planners skipped the dry run instead
    if prof.get("test_command") and not getattr(a, "items_only", False):
        items.append({"id": "Test command", "check": prof["test_command"], **try_check(tree, prof["test_command"], None, a.timeout, prof.get("plans"))})
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


def cmd_merge(a: argparse.Namespace) -> None:
    if os.environ.get("ORCHESTRATE_ROLE") in ("plan", "review"):
        raise SystemExit(f"error: merge isn't for a {os.environ['ORCHESTRATE_ROLE']} session; the script merges what "
                         "a planner or reviewer leaves, after checking it")
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    if dirty := git(worktree, "status", "--porcelain").stdout.strip():
        print(json.dumps({"result": "FAILED", "detail": "commit, remove or ignore these first: " + dirty[:300]}))
        sys.exit(1)
    # A builder's plan edits (ticked boxes, a log entry) merge with its work; the plan checks only warn here.
    # The tip is fetched first, so that the script's own records already on the main branch, such as another
    # milestone it set Ready for Review, count as the main branch's and not as this branch's change.
    try:
        upstream = tip(worktree, prof)
    except TipError:
        upstream = base_ref(prof)
    base = git(worktree, "merge-base", "HEAD", upstream).stdout.strip()
    # Only the script sets Ready for Review or Done, after its own checks pass. In Thrum a builder's Ready for Review
    # reached the main branch before the script's checks failed it, and other builders rebased onto it for three
    # hours. A planner or a reviewer never runs `merge`, and the owner's and the script's records are merged by the
    # script itself, so this catches only a builder, including one from before 2.1.0 or a branch it left.
    if base and (found := states_set(worktree, prof, base)):
        print(json.dumps({"result": "FAILED", "detail": state_refusal(found), "commit": head_commit(worktree)}))
        sys.exit(1)
    touched = git(worktree, "diff", "--name-only", base, "HEAD").stdout.split() if base else []
    warnings = plan_checks(worktree, prof, touched)
    warnings += [f"{p} changed; the script writes it after each record it merges, so this change will be overwritten"
                 for p in touched if p == status_rel(prof)]
    own = int(git(worktree, "rev-list", "--count", f"{base}..HEAD").stdout.strip() or 0) if base else 0
    ok, detail = land(worktree, prof, check=not a.no_check)
    print(json.dumps({"result": "MERGED" if ok else "FAILED", "detail": detail, "commit": head_commit(worktree),
                      **(upstream_changes(worktree, base, own) if ok else {}),
                      **({"plan_warnings": warnings} if warnings else {})}))
    sys.exit(0 if ok else 1)


def upstream_changes(worktree: Path, old_base: str, own: int) -> dict:
    """The files the rebase brought in from the main branch, so the builder re-runs only the proofs they can affect.
    In Thrum builders re-ran every capture after each merge, and one builder's evidence came from before a rebase
    that changed the camera. The new base is HEAD less the builder's own commits, which the rebase kept on top."""
    if not old_base or own <= 0:
        return {}
    new_base = git(worktree, "rev-parse", "--verify", "--quiet", f"HEAD~{own}").stdout.strip()
    if not new_base or new_base == old_base:
        return {"upstream": "the main branch hadn't moved, so nothing new came in"}
    paths = git(worktree, "diff", "--name-only", old_base, new_base).stdout.split()
    shown = paths[:60]
    return {"upstream": f"the rebase brought in {len(paths)} changed files from {old_base[:12]}..{new_base[:12]}; "
                        "re-run the proofs of items these could affect, on the merged commit",
            "upstream_files": shown + ([f"... and {len(paths) - len(shown)} more"] if len(paths) > len(shown) else [])}


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
        print(json.dumps({"runs": views, "cleaned": removed}, indent=2))
        return
    print(f"{len(views)} run{'' if len(views) == 1 else 's'} going" + (f" in {repo}" if repo else "") +
          (f"; cleared {len(removed)} file{'' if len(removed) == 1 else 's'} left by runs that died" if removed
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
        reason = blocked_of(m)["reason"]
        if reason == "too_many_failed_reviews":
            raise SystemExit(f"error: {a.milestone} is Blocked with too many failed reviews, which only the owner "
                             "decides: ask them, then run `owner reopen`, `owner accept` or `owner scope` with their "
                             "words")
        if reason == "needs_human_feedback":
            raise SystemExit(f"error: {a.milestone} is Blocked: Needs Human Feedback. Ask the owner, then record "
                             "their reply with `owner feedback`, which unblocks it")
        m["state"] = "in_progress"
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
    """Ledger-shaped rows from the committed record files, for milestones this machine's ledger knows nothing
    about (built before it existed, or on another machine): each milestone's last Ready for Review record with its session's
    tokens
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
            row(mid, "build", ready_record(m) or None)
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


def per_turn_from(rows: list[dict]) -> str | None:
    """When the ledger's Codex rows start counting each turn's own tokens: the first Codex row 2.1.0 or later wrote,
    which reads them from the session's rollout file. Earlier Codex rows count a resumed session's earlier tokens
    again, so they are too high, and a turn stopped at the turn limit has none."""
    return next((r.get("at") for r in rows if r.get("host") == "codex" and
                 (version_tuple(str(r.get("version") or "")) or (0,)) >= (2, 1, 0)), None)


def cmd_cost(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    rows = ledger_rows(worktree)
    c = cost_of(rows, a.module, since_stamp(a.since), record_rows(worktree))
    if any(r.get("host") == "codex" and (version_tuple(str(r.get("version") or "")) or (0,)) < (2, 1, 0)
           for r in rows):  # only a ledger with rows that are too high needs the date
        c["codex_per_turn_from"] = per_turn_from(rows)
    if a.json:
        print(json.dumps(c, indent=2))
        return
    print(cost_header(worktree, c, a.since))
    print("\n".join("  " + line for line in cost_text(c)))


def cost_header(worktree: Path, c: dict, since: float | None) -> str:
    span = f" in the last {since:g} h" if since else ""
    text = (f"Tokens the script's turns used{span}, from this machine's ledger "
            f"({Path(git_common_dir(worktree)) / 'orchestrate' / 'usage.jsonl'}), which has every turn run here")
    if c.get("from_records"):
        text += ("; milestones it has nothing on (built before it existed, or elsewhere) come from the committed "
                 "record files, marked [from the committed record]: each one's last Ready for Review record with its session's "
                 "tokens, and every review, so earlier sessions and paused turns aren't in those")
    if "codex_per_turn_from" in c:
        start = c["codex_per_turn_from"]
        text += (f". Codex figures are each turn's own from {start}, read from the session's rollout file. Codex "
                 f"rows before then count a resumed session's earlier tokens again, so they are too high"
                 if start else ". The Codex figures here were written before 2.1.0, which counted a resumed "
                               "session's earlier tokens again, so they are too high")
    return text + ":"


def report_text(worktree: Path, hours: float) -> tuple[str, str]:
    """(date, markdown): the factual half of the lead's report for the last `hours`, read from the records at the
    main branch's tip and this machine's usage ledger. The lead adds the judgement: what it means, what to do next."""
    prof = profile(worktree)
    ref, proj = read_project(worktree, prof)
    since = since_stamp(hours) or ""
    date = datetime.now().strftime("%Y-%m-%d")
    graded = worktree / prof["graded_examples"]
    graded_n = sum(1 for line in graded.read_text().splitlines() if line.startswith(("## ", "### "))) \
        if graded.exists() else 0
    closed, verdicts, waiting, needing, adopted, decided, assumed = [], [], [], [], [], [], []
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
        step = next_step(key, proj, holds(worktree), me(worktree))
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
            if m.get("state") == "blocked":
                b = blocked_of(m)
                if b["reason"] == "too_many_failed_reviews":
                    why = ((rec.get("milestones") or {}).get(m["id"]) or {}).get("too_many_failed_reviews", {}) \
                        .get("why") or b.get("what") or "it ran out of review rounds"
                    waiting.append(f"- {stem} {m['id']}: Blocked: Too Many Failed Reviews, because {why}. The owner "
                                   "accepts it (`owner accept`), re-scopes it (`owner scope`) or reopens it "
                                   "(`owner reopen`)")
                else:
                    waiting.append(f"- {stem} {m['id']}: Blocked: {b['reason'].replace('_', ' ').capitalize()}" +
                                   (f": {b['what']}" if b.get("what") else ""))
            if not accepted(m, rec):
                for i in m.get("items") or []:
                    n = i.get("needs")
                    if not isinstance(n, dict) or i.get("status") == "pass":
                        continue
                    how = (f"Ask the owner in chat; their reply goes in "
                           f"`{owner_cmd('feedback', stem, m['id'], str(worktree), i['id'])}`"
                           if n.get("type") == "human_feedback" else
                           f"Done at the machine, not said: run the builder visibly while the owner is there, with "
                           f"`{visible_run(stem, str(worktree))}`")
                    needing.append(f"- {stem} {m['id']} {i['id']} (needs {n.get('type', '').replace('_', ' ')}: "
                                   f"{n.get('what', '')}): {i.get('statement', '')}\n  {how}")
        if step["status"] in ("waiting", "design_not_approved", "review_owed") and step.get("milestone"):
            why = (step.get("reason") or "").replace("_", " ") + \
                (f": {', '.join(step['depends_on'])}" if step.get("depends_on") else "")
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
                "Every `owner` command in this window, with the words recorded as the owner's. The script can't tell "
                "who ran one, so a decision here that the owner didn't make is the thing to look for.", "", *decided]
    if planned:
        out += ["", "## Planner turns (with the task each was given)", "",
                *[f"- {at.replace('T', ' ')}, {', '.join(mods)}: " + task.replace("\n", "\n  ")
                  for (at, task), mods in sorted(planned.items())]]
    if assumed:
        out += ["", "## Assumptions the planners made (for the owner to overturn)", "",
                "Readings of the request a planner chose where it could be read more than one way, from the lines "
                "starting `Assumption:` in each module's PLAN.md. Each stands until the owner overturns it; overturning one "
                "is a re-plan.", "", *assumed]
    out += ["", "## Blocked or waiting", "", *(waiting or ["- nothing"]), "",
            "## Items that need human feedback, access or hardware", "", *(needing or ["- none open"]), "",
            "## Cost", "", f"- build sessions: {builders}", *("- " + line for line in cost_text(c)),
            ("- [from the committed record] marks milestones this machine's ledger has nothing on: their last "
             "Ready for Review record's session and every review, as the record files keep them" if c.get("from_records") else
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
        # review it holds merged with the last change to design-review.md before that commit. In UTC.
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
                                           "add the judgement, then merge it")}))
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
    """Why `adopt` won't merge the path `p`, or None: it merges plan files, a first settings file, and build reports."""
    plans, reports = prof["plans"] + "/", reports_dir(prof) + "/"
    if p == PROFILE_FILE:
        if file_at(worktree, ref, p) is not None:
            return (f"{p} differs from the one at {base_ref(prof)}; adopt doesn't merge a changed settings file on an existing "
                    "project: the lead commits and merges it with git once the owner has agreed to it")
        return None
    if p == status_rel(prof):
        return (f"{p} is written by the script from the records after each one it merges, so a change to it by hand "
                f"would only be overwritten; set it back with `git checkout -- {p}`")
    if p.startswith(plans):
        if (where := module_of(prof, p)) and where[1] == "record" or p.endswith("-ACCEPTED.json"):
            return f"{p} is a record file, which only the script writes"
        return next(iter(flat_names(prof, [p])), None)
    if p.startswith(reports):
        return None
    return (f"{p} isn't a plan file under {plans}, a first {PROFILE_FILE} or a report under {reports}; commit and "
            "merge it another way")


def building_begun(doc: dict, record: dict, held: dict, key: str) -> bool:
    """Whether building has started on a module: a milestone past `not_started`, a Ready for Review record, a review or
    an acceptance."""
    return any(m.get("state") != "not_started" for m in doc.get("milestones") or []) or \
        any(ready_record(e) or e.get("reviews") or e.get("accepted") for e in (record.get("milestones") or {}).values()) or \
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
    review has passed, or building has begun (a Ready for Review record, review, acceptance, a milestone past open, or a run holding
    the module's lock)."""
    if design_passed(record):
        return "a design review of it has passed"
    sync_holds(worktree, prof)
    if building_begun(doc, record, holds(worktree), key):
        return "building on it has begun"
    if run_holder(Path(git_common_dir(worktree)) / "orchestrate", key) not in (None, os.getpid()):
        return "a run holds it"
    return None


class AdoptRace(Exception):
    """A module stopped being a draft between adopt's check and its merging."""


ADOPT_WHY = "revised before the module's design review passed; that review judges these definitions"


ASSUMPTION = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*)?Assumption:(?:\*\*)?\s*(.+?)\s*$", re.MULTILINE)


def assumptions(text: str | None) -> list[str]:
    """The readings a planner chose for the owner to overturn: each line of a module's PLAN.md that starts `Assumption:`
    (a list bullet or bold marker before it is fine). One line each; a reading continued on the next line is cut."""
    return [m.group(1) for m in ASSUMPTION.finditer(text or "")]


PLAN_WORDS = 1500  # a plan holds the present only; past this it has started to collect history or design
LOG_ENTRY_LINES = 8  # a log entry is a few lines, with the detail linked from the evidence folder
STATUS_LINE = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*)?(Now|Next|Blocked|Milestone|Reviews):", re.MULTILINE)
DONE_HEADING = re.compile(r"^##\s+M\d+\b.*:\s*done\s*$", re.IGNORECASE)
FENCE = re.compile(r"^```.*?^```[^\n]*$", re.MULTILINE | re.DOTALL)


def plan_text_problems(rel: str, text: str) -> list[str]:
    """What is wrong with a module's PLAN.md, each said so that a planner can fix it. A plan holds the present only:
    one `##` heading per milestone, work lists for the current and later ones, and the open assumptions."""
    out = []
    words = len(text.split())
    if words > PLAN_WORDS:
        out.append(f"{rel} is {words} words. A plan holds only the present, so keep it under about {PLAN_WORDS:,}: "
                   "move history to LOG.md and design to DESIGN.md")
    body = FENCE.sub("", text)  # an example in a code block isn't the plan's own structure
    if m := STATUS_LINE.search(body):
        out.append(f"{rel} has a `{m.group(1)}:` line. The script knows each milestone's status and shows it in "
                   "STATUS.md, so delete status lines from the plan")
    if re.search(r"^###\s", body, re.MULTILINE):
        out.append(f"{rel} has a `###` heading. Give each milestone one `##` heading and nothing under it but its "
                   "work list; design goes in DESIGN.md and history in LOG.md")
    if re.search(r"^##\s+Log\s*$", body, re.MULTILINE | re.IGNORECASE):
        out.append(f"{rel} has a `## Log` section. Move its entries to LOG.md beside it")
    lines = body.splitlines()
    for n, line in enumerate(lines):
        if DONE_HEADING.match(line.strip()):
            under = []
            for rest in lines[n + 1:]:
                if rest.startswith("## ") or rest.startswith("# "):
                    break
                if rest.strip():
                    under.append(rest)
            if len(under) > 1:
                out.append(f"{rel}: under `{line.strip()}` there are {len(under)} lines. A milestone that is done "
                           "keeps one line, a link to its review; move anything worth keeping to LOG.md")
    return out


def log_text_problems(rel: str, text: str) -> list[str]:
    """What is wrong with a module's LOG.md: an entry (a `- ` line and the lines that continue it) that runs past a
    few lines."""
    entries, current = [], None
    for line in FENCE.sub("", text).splitlines():
        if line.startswith("- "):
            current = [line]
            entries.append(current)
        elif current is not None and line.strip() and not line.startswith("#"):
            current.append(line)
        else:
            current = None
    long = [e for e in entries if len(e) > LOG_ENTRY_LINES]
    if not long:
        return []
    return [f"{rel} has {len(long)} {'entry' if len(long) == 1 else 'entries'} longer than {LOG_ENTRY_LINES} lines "
            f"(the first starts \"{long[0][0][:60]}\"). Keep each entry to a few lines, and put the detail in the "
            "evidence folder with a link to it"]


def plan_checks(tree: Path, prof: dict, paths: list[str]) -> list[str]:
    """The plan checks for those of `paths` that are a module's PLAN.md or LOG.md, read from `tree`."""
    out = []
    for p in paths:
        where = module_of(prof, p)
        if not where or where[1] not in ("plan", "log") or not (tree / p).is_file():
            continue
        text = (tree / p).read_text(errors="replace")
        out += plan_text_problems(p, text) if where[1] == "plan" else log_text_problems(p, text)
    return out


def flat_names(prof: dict, paths: list[str]) -> list[str]:
    """Plan files written under the old flat names, which the script no longer reads."""
    out = []
    for p in paths:
        folder, _, name = p.rpartition("/")
        m = re.fullmatch(r"(.+)-(DONE\.json|PLAN\.md|ACCEPTED\.json|BRIEF\.md)", name)
        if folder == prof["plans"] and m:
            kind = {"DONE.json": "done", "PLAN.md": "plan", "ACCEPTED.json": "record", "BRIEF.md": "brief"}[m.group(2)]
            out.append(f"{p} uses the old flat name, which the script doesn't read; write it as "
                       f"{module_file(prof, m.group(1), kind)}")
    return out


def stray_plans(worktree: Path, prof: dict) -> list[str]:
    """Tracked plan files outside the plans folder (a PLAN.md or <name>-PLAN.md), which no agent is pointed to."""
    listed = git(worktree, "ls-files").stdout.splitlines()
    return [p for p in listed if (p.rpartition("/")[2] == "PLAN.md" or p.endswith("-PLAN.md"))
            and not p.startswith(prof["plans"] + "/")]


# --------------------------------------------------------------------------------- the module table and STATUS.md

TABLE_HEADER = ("#", "module", "what it's for", "needs")


def table_cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def plain_cell(cell: str) -> str:
    """A table cell without its markdown: links keep their text, and backticks and bold go."""
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", cell).replace("`", "").replace("**", "").strip()


def module_table(text: str | None) -> list[dict] | None:
    """The rows of the module table in ARCHITECTURE.md, in build order: the first markdown table whose header is
    `# | Module | What it's for | Needs` (any case, either apostrophe). Each row is {n, module, what, needs}, as
    written. None when there's no such table."""
    lines = (text or "").splitlines()
    for i, line in enumerate(lines):
        if not line.strip().startswith("|") or i + 1 >= len(lines):
            continue
        head = [plain_cell(c).lower().replace("’", "'") for c in table_cells(line)]
        if len(head) < 4 or head[0] != "#" or head[1] != "module" or not head[2].startswith(TABLE_HEADER[2]) \
                or head[3] != "needs" or not set(lines[i + 1].replace("|", "").strip()) <= set("-: "):
            continue
        rows = []
        for row in lines[i + 2:]:
            if not row.strip().startswith("|"):
                break
            cells = table_cells(row) + ["", "", "", ""]
            if plain_cell(cells[1]):
                rows.append({"n": cells[0], "module": plain_cell(cells[1]), "what": cells[2], "needs": cells[3]})
        return rows
    return None


def table_warnings(worktree: Path, prof: dict, ref: str, stems: list[str]) -> list[str]:
    """A module folder the module table has no row for. A row with no folder is fine: that module isn't planned yet."""
    rel = project_file(prof, "architecture")
    text = show(worktree, ref, rel)
    if text is None or not stems:
        return []
    rows = module_table(text)
    if rows is None:
        return [f"{rel} has no module table (a table headed `| # | Module | What it's for | Needs |`, one row per "
                "module in build order), so STATUS.md lists the modules without it; a planner adds it"]
    listed = {r["module"].upper() for r in rows}
    return [f"{stem} has a folder under {prof['plans']} but no row in the module table in {rel}; a planner adds it"
            for stem in stems if stem.upper() not in listed]


def proposed_names(text: str | None) -> list[str]:
    """The glossary entries the owner hasn't agreed: each entry (a bold name line) with a `Proposed:` line."""
    out, name = [], None
    for line in (text or "").splitlines():
        if m := re.fullmatch(r"\s*\*\*(.+?)\*\*\s*", line):
            name = m.group(1)
        elif (m := re.match(r"\s*(?:[-*]\s+)?Proposed:\s*(.*)$", line)) and name:
            out.append(f"{name} ({m.group(1).strip().rstrip('.')})" if m.group(1).strip() else name)
            name = None
    return out


def status_word(step: dict, record: dict | None = None) -> str:
    """The plain status of a module's next milestone, in the words of done-when.md's status table."""
    status, state = step["status"], step.get("state")
    if status == "finished":
        return "Done"
    if status in ("ready", "taken"):
        return "Not Started" if state == "not_started" else "In Progress"
    if status == "design_not_approved":
        return "Design Changes Requested" if ((record or {}).get("design") or {}).get("verdict") == "changes" \
            else "Design Ready for Review"
    if status in ("waiting", "blocked"):
        return f"{status.capitalize()}: " + " ".join(w.capitalize() for w in (step.get("reason") or "").split("_"))
    return {"review_owed": "Ready for Review"}.get(status, "Invalid")


def short_date(at: str | None) -> str:
    try:
        d = datetime.strptime((at or "")[:10], "%Y-%m-%d")
    except ValueError:
        return ""
    return f"{d.day} {d.strftime('%b')}"


RECENT_DAYS = 7


def status_page(worktree: Path, prof: dict, ref: str, proj: dict | None = None, unlanded: list[str] | None = None) -> str:
    """STATUS.md, the owner's page, built only from what is stored at `ref`: the done-when files, the acceptance
    records, the module table in ARCHITECTURE.md, the `Assumption:` lines in each PLAN.md and the `Proposed:` names in
    GLOSSARY.md. Its links are relative to the plans folder, where the page lives. `unlanded` lists plan files that
    aren't at the tip, when the caller knows them."""
    if proj is None:
        proj = project(worktree, prof, ref)
        for k, cycle in need_cycles(proj).items():
            proj[k]["problems"].append(f"its needs form a cycle: {cycle}")
    rows = module_table(show(worktree, ref, project_file(prof, "architecture"))) or []
    order = {r["module"].upper(): n for n, r in enumerate(rows)}
    keys = sorted(proj, key=lambda k: (order.get(k, len(order)), k))
    steps = {k: next_step(k, proj) for k in keys}
    since = datetime.fromtimestamp(time.time() - RECENT_DAYS * 86400, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def started(e: dict) -> bool:
        return not e["problems"] and (any(m.get("state") != "not_started" for m in e["doc"]["milestones"]) or
                                      any(accepted(m, e["record"]) for m in e["doc"]["milestones"]))

    planned_rows = [r for r in rows if r["module"].upper() not in proj]
    done_n = sum(steps[k]["status"] == "finished" for k in keys)
    going = sum(steps[k]["status"] != "finished" and started(proj[k]) for k in keys)
    total = len(keys) + len(planned_rows)
    # "Waiting on you" is split in two. In Thrum it held 30 lines, about 28 of them a planner's assumptions, so the
    # two or three that needed the owner were lost among them.
    waiting, chosen, now_next, recent = [], [], [], []
    roots = worktree_roots(worktree)
    for key in keys:
        e, step = proj[key], steps[key]
        stem, rec = e["stem"], e["record"]
        plan = md_link("plan", plan_rel(prof, stem))
        chosen += [f"- {stem} assumes: {x} ({plan})" for x in assumptions(show(worktree, ref, plan_rel(prof, stem)))]
        if e["problems"]:
            continue
        ms = {m["id"]: m for m in e["doc"]["milestones"]}
        m = ms.get(step.get("milestone")) or {}
        name = m.get("name") or step.get("milestone") or ""
        mid = step.get("milestone")
        status = step["status"]
        reason = step.get("reason")
        if status == "blocked" and reason == "too_many_failed_reviews":
            why = ((rec.get("milestones") or {}).get(mid) or {}).get("too_many_failed_reviews", {}).get("why") or \
                "it ran out of review rounds"
            waiting.append(f"- {stem} {mid} {name}: Blocked: Too Many Failed Reviews, because {why}. You decide: "
                           "accept it, change its scope or give it another try")
        elif status == "blocked" and reason in ("needs_human_feedback", "needs_access", "needs_hardware"):
            listed = (step.get("blocked") or {}).get("items") or open_needs(m)
            who = {"needs_human_feedback": "You judge it from the evidence the lead shows you",
                   "needs_access": "You approve it at the machine, in a visible run the lead starts",
                   "needs_hardware": "You connect the device, and the lead runs the builder again"}[reason]
            for i in m.get("items") or []:
                if i["id"] in listed:
                    what = (i.get("needs") or {}).get("what") if isinstance(i.get("needs"), dict) else None
                    waiting.append(f"- {stem} {mid} {name}: {status_word(step, rec)}, {i['id']}: "
                                   f"{i.get('statement', '')}" + (f" ({what})" if what else "") + f". {who}")
        elif status == "blocked":  # the lead or a planner acts, so it is under "Now and next"
            who = ("A planner adds it to the module that owns it" if reason == "needs_dependency" else
                   "The lead finds the missing fact, or asks you for it")
            what = repo_relative((step.get("blocked") or {}).get("what") or "", roots) or "see the done-when file"
            now_next.append(f"- {stem} {mid} {name}: {status_word(step, rec)}: {sentence(what)} {who}")
        elif status == "review_owed" and m.get("state") == "done":
            waiting.append(f"- {stem} {mid} {name}: says done, but no check or review accepted it. Accept it as it "
                           "is, or have it reviewed")
        if status in ("ready", "taken", "review_owed") and m.get("state") != "done":
            reviews = ((rec.get("milestones") or {}).get(mid) or {}).get("reviews") or []
            latest = next((r["review"] for r in reversed(reviews) if r.get("review")), None)
            now_next.append(f"- {name} ({stem} {mid}): {status_word(step, rec)} · {plan}" +
                            (f" · {md_link('latest review', latest)}" if latest else ""))
        elif status == "design_not_approved":
            now_next.append(f"- {stem}'s design: {status_word(step, rec)} · "
                            f"{md_link('design', design_rel(prof, stem))} · {plan}")
        for x in e["doc"]["milestones"]:
            acc = ((rec.get("milestones") or {}).get(x["id"]) or {}).get("accepted") or {}
            if accepted(x, rec) and (acc.get("at") or "") >= since:
                review = acc.get("review") or next(
                    (r["review"] for r in reversed(((rec.get("milestones") or {}).get(x["id"]) or {}).get("reviews")
                                                   or []) if r.get("review")), None)
                recent.append((acc.get("at") or "", f"- {x.get('name') or x['id']} ({stem} {x['id']}), "
                                                    f"{short_date(acc.get('at'))}" +
                               (f" · {md_link('review', review)}" if review else "")))
    chosen += [f"- A name in the glossary waits for your agreement: {x}"
               for x in proposed_names(show(worktree, ref, project_file(prof, "glossary")))]
    if unlanded:
        waiting.append(f"- Plan files that haven't been merged, so the script can't see them: {', '.join(unlanded[:10])}")
    reports = [n for n in git(worktree, "ls-tree", "--name-only", f"{ref}:{reports_dir(prof)}").stdout.split()
               if re.fullmatch(r"\d{4}-\d{2}-\d{2}\.md", n)]
    recent_lines = [line for _, line in sorted(recent, reverse=True)]
    if reports:
        latest = max(reports)
        recent_lines.append(f"- The latest build report: {md_link(latest[:-3], reports_dir(prof) + '/' + latest)}")
    out = ["# Status", "",
           "The orchestrate script writes this page from the plan files and record files after each record it "
           "merges. Don't edit it, because the next merge overwrites it. `status --format md` prints the same page.", "",
           "## Overview", "",
           f"{done_n} of {total} modules done · {going} in progress · {total - done_n - going} to come", "",
           "### Needs you now", "", *(waiting or ["- Nothing."]), "",
           "### Choices made for you", "",
           *(["A planner or the lead chose each of these where your words left it open. Each stands until you say "
               "otherwise.",
              ""] + chosen if chosen else ["- Nothing."]), "",
           "### Now and next", "", *(now_next or ["- Nothing is under way or ready to start."]), "",
           "### Recently done", "", *(recent_lines or [f"- Nothing accepted in the last {RECENT_DAYS} days."]), "",
           "## All modules", "",
           "| # | Module | What it's for | Needs | Status |", "|---|---|---|---|---|"]

    def cell(key: str) -> str:
        e, step = proj[key], steps[key]
        if e["problems"]:
            return "Invalid: a planner has to fix its files"
        if step["status"] == "finished":
            ats = [((e["record"].get("milestones") or {}).get(m["id"]) or {}).get("accepted", {}).get("at") or ""
                   for m in e["doc"]["milestones"]]
            return f"Done {short_date(max(ats))}".strip()
        if step["status"] == "waiting" and step.get("reason") == "on_dependency":
            return "Waiting: On Dependency, " + ", ".join(n.replace(" (not planned)", "")
                                                          for n in step.get("depends_on") or [])
        if step["status"] == "design_not_approved":
            return status_word(step, e["record"])
        return f"{step['milestone']} of {len(e['doc']['milestones'])} · {status_word(step, e['record'])}"

    for r in rows:
        key = r["module"].upper()
        status = cell(key) if key in proj else "Not planned yet"
        out.append(f"| {r['n']} | {r['module']} | {r['what']} | {r['needs']} | {status} |")
    for key in keys:
        if key not in order:
            out.append(f"|  | {proj[key]['stem']} | (no row in the module table) |  | {cell(key)} |")
    return relink("\n".join(out) + "\n", prof["plans"])


def land_status(worktree: Path, prof: dict, name: str, tree: Path | None = None) -> None:
    """Writes STATUS.md in a commit of its own after a record has merged, and merges it. It is best effort: the record
    has merged already, and nothing here may fail it. A rebase conflict (another merging's STATUS.md) regenerates the
    page once from the newer tip; if that fails too, it says so on stderr and the next merging catches up. An
    unchanged page makes no commit."""
    why = ""
    for attempt in range(2):
        try:
            if tree is None or attempt:
                tree = verify_tree(worktree, name, tip(worktree, prof))
            here = profile(tree, missing_ok=True)  # the tip's own settings: `migrate --to` may have moved the plans
            text = status_page(tree, here, "HEAD")
            path = tree / status_rel(here)
            if path.is_file() and path.read_text() == text:
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
            git(tree, "add", "--", status_rel(here))
            c = git(tree, *ident(tree), "commit", "--quiet", "-m", "orchestrate: update STATUS.md")
            if c.returncode != 0:
                why = f"commit failed: {(c.stdout + c.stderr).strip()[-200:]}"
                continue
            ok, detail = land(tree, prof)
            if ok:
                return
            why = detail
        except (Exception, SystemExit) as e:  # never the record's problem
            why = str(e)
    print(f"note: STATUS.md wasn't updated ({why[:300]}); the next record the script merges writes it", file=sys.stderr)


def authorise_doc(doc: dict, record: dict, stamp: dict) -> None:
    """Records `doc`'s definitions as authorised in `record`. A milestone whose definitions changed loses its proof,
    since that proof proved something else, and goes back to not_started."""
    for m in doc["milestones"]:
        e = record["milestones"].get(m["id"])
        if e and e.get("definitions") == definitions(m):
            continue
        if e:
            reset_proof(m)
            if m.get("state") in ("in_progress", "ready_for_review", "done"):
                m["state"] = "not_started"
        record["milestones"][m["id"]] = {"definitions": definitions(m), "reviews": (e or {}).get("reviews", []),
                                         "authorised": stamp,
                                         **({"human_feedback": e["human_feedback"]} if (e or {}).get("human_feedback")
                                            else {})}
    for gone in set(record["milestones"]) - {m["id"] for m in doc["milestones"]}:
        del record["milestones"][gone]


def adopt_problems(worktree: Path, prof: dict, ref: str, base: str, paths: list[str]) -> tuple[list[str], list[str],
                                                                                              dict | None]:
    """(why these files can't merge as they stand, the modules whose changed definitions adopt will authorise, and a
    `next` for a refusal that has one). Refused: files adopt doesn't merge, a done-when file that's invalid or grants
    what a plan can't, a file the tip changed since this worktree's copy was made (merging it would undo that
    change), changed definitions on a module where building has begun, and anything `ready` would then call
    invalid. While nothing has been built on a module, adopt is how an in-chat planner's changes merge, so it
    authorises them as a `plan` would."""
    problems = [why for p in paths if (why := adoptable(prof, worktree, ref, p))]
    problems += plan_checks(worktree, prof, [p for p in paths if not adoptable(prof, worktree, ref, p)])
    proj = project(worktree, prof, ref)
    sync_holds(worktree, prof)
    held = holds(worktree)
    authorise, adopted, refusal = [], [], None
    for p in paths:
        if adoptable(prof, worktree, ref, p):
            continue
        if base and file_at(worktree, ref, p) != file_at(worktree, base, p):
            problems.append(f"{p} changed at {base_ref(prof)} since this worktree's copy; rebase this worktree onto "
                            "it first, so merging doesn't undo that change")
        if not ((where := module_of(prof, p)) and where[1] == "done"):
            continue
        if (here := file_here(worktree, p)) is None:
            continue
        stem = where[0]
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
        design = file_here(worktree, design_rel(prof, stem))
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
    if not problems and adopted:  # `ready` must not call invalid what adopt merges
        for k, cycle in need_cycles(proj).items():
            proj[k]["problems"].append(f"its needs form a cycle: {cycle}")
        for key in adopted:
            step = next_step(key, proj, held, me(worktree))
            if step["status"] == "invalid":
                problems += [f"{proj[key]['stem']}: {x}" for x in step.get("problems") or []]
    return problems, authorise, refusal


def cmd_adopt(a: argparse.Namespace) -> None:
    """Merges plan files left uncommitted, or committed but not merged, so `run` and `ready` can see them, with a
    first ORCHESTRATE.md and any build reports."""
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    if os.environ.get("ORCHESTRATE_ROLE"):
        raise SystemExit("error: adopt can't run inside a session the script started; a planner's files merge through "
                         "`plan`, and a builder's through `merge`")

    def done_with(result: str, code: int = 0, **fields) -> None:
        print(json.dumps({"result": result, **fields}))
        sys.exit(code)

    try:
        ref = tip(worktree, prof)
    except TipError as e:
        done_with("FAILED", 1, detail=str(e), **({"next": e.next} if getattr(e, "next", None) else {}))
    drift = plan_drift(worktree, prof, ref)
    reports = folder_drift(worktree, reports_dir(prof), ref)
    unlanded = sorted(set(drift["uncommitted"]) | set(drift["unmerged"]) | set(reports["uncommitted"]) |
                      set(reports["unmerged"]))
    if a.paths:
        paths = []
        for p in a.paths:
            full = Path(p) if Path(p).is_absolute() else worktree / p
            paths.append(os.path.relpath(os.path.abspath(full), worktree))
        problems = [f"{p} has no change here that the main branch's tip lacks" for p in paths
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
    # Hold each module whose definitions adopt will authorise, so no run here starts on it while this merges; the
    # merging re-checks the records too, for a milestone set Ready for Review from another clone meanwhile.
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

    # The files as they are here, merged through a clean checkout of the tip, as the script merges its own records,
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

    # A worktree that isn't ahead of the tip gets its copies set back to HEAD first, so merging can fast-forward
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
                loop_cmd("ready", "--worktree", str(worktree)), "lead", "nothing merged; see what changed"))
        if ok and authorise:  # a draft's revisions: no design review has passed and nothing has been built
            try:
                ok, detail = loop_write(worktree, prof, "_adopt", authorise_change,
                                        "orchestrate: authorise the adopted draft of " + ", ".join(authorise))
            except AdoptRace as e:
                ok, detail = False, str(e)
            landed = detail if ok else f"the files merged at {landed}, but their definitions weren't authorised " \
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
    """After `owner scope` merged the owner's edited done-when file through the script's own checkout, this worktree
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
    the script started (ORCHESTRATE_ROLE), and while a run, review or plan holds the module or the planner. These stop
    mistakes and casual shortcuts, not a determined agent."""
    if os.environ.get("ORCHESTRATE_ROLE"):
        raise SystemExit(f"error: owner {verb} can't run inside a session the script started; the lead records the "
                         "owner's decisions, from what the owner told it")
    folder = Path(git_common_dir(worktree)) / "orchestrate"
    for name, what in ((stem.upper(), f"a run, review or design review holds {stem}"), ("_plan", "a planner is running")):
        if (pid := run_holder(folder, name)) is not None:
            raise SystemExit(f"error: owner {verb} is refused while {what} (pid {pid}), so no session the script started "
                             "can record a decision in the owner's name. Nothing more is needed from the owner: you "
                             "have their words, so run this same command again once that has stopped (`runs` shows "
                             "when)")


def cmd_owner(a: argparse.Namespace) -> None:
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True)
    stem = module_stem(worktree, prof, a.module)
    key, mid, verb = stem.upper(), a.milestone, a.action
    feedback = verb == "feedback"
    words = ((getattr(a, "said", None) if feedback else None) or a.text or "").strip()
    asked = (getattr(a, "asked", None) or "").strip()
    items = list(dict.fromkeys(getattr(a, "item", None) or []))
    if not words:
        raise SystemExit(f"error: owner {verb} needs " + ("--said, the owner's words as they gave them" if feedback else
                         "--text, the owner's words for this decision as they gave them"))
    if feedback and not asked:
        raise SystemExit("error: owner feedback needs --asked, the question you asked the owner, so the builder and "
                         "the reviewer read the owner's words against it")
    if items and not feedback:
        raise SystemExit(f"error: --item is for owner feedback, not owner {verb}")
    owner_guard(worktree, stem, verb)
    # what the script records: the owner's words, when, and which verb. It can't tell who ran the command, so it
    # doesn't say; `report` lists every one, recorded in the owner's name, for the owner to check
    decision = {"action": verb, "milestone": mid, "words": words, "at": now(),
                **({"asked": asked} if feedback else {}), **({"items": items} if items else {})}
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
            if not rec_path.exists():  # nothing to record the release in; the hold is still dropped
                return []
        record = json.loads(rec_path.read_text()) if rec_path.exists() else record_in(t, prof, stem, doc)
        record.setdefault("decisions", []).append(decision)
        written = [record_rel(prof, stem)]
        if verb == "release":
            pass
        elif mid == "design":
            if verb != "accept":
                raise SystemExit("error: only `owner accept` applies to a design")
            design = t / design_rel(prof, stem)
            if record.get("design"):
                record.setdefault("design_history", []).append(record["design"])
            record["design"] = {**stamp, "verdict": "ok", "hash": text_hash(design.read_text() if design.exists() else None)}
        elif feedback:
            m = find(doc, mid)
            by_id = {i["id"]: i for i in m["items"]}
            covered = items or (blocked_of(m).get("items") if m.get("state") == "blocked" and
                                blocked_of(m)["reason"] == "needs_human_feedback" else None) or \
                open_needs(m, ("human_feedback",))
            if not covered:
                raise SystemExit(f"error: {mid} has no open item that needs human feedback; name the items with --item")
            for item in covered:
                if item not in by_id:
                    raise SystemExit(f"error: {mid} has no item {item}")
                kind = (by_id[item].get("needs") or {}).get("type") if isinstance(by_id[item].get("needs"), dict) \
                    else None
                if kind in HELD_BY_SOMEONE:
                    raise SystemExit(f"error: {item} needs {kind}, which is done at the machine, not said, so no reply "
                                     "is recorded for it. Run the builder again in a visible session while the owner "
                                     "is there: " + visible_run(stem, str(worktree)))
                if kind != "human_feedback":
                    raise SystemExit(f"error: {item} isn't marked as needing human feedback, so the reviewer judges it, "
                                     "not the owner. If the owner has something to say about it, pass it to the "
                                     "builder with `run --message`, or have a planner mark the item")
            given = {"asked": asked, "said": words, "items": covered, "at": decision["at"]}
            decision["items"] = covered
            entry(record, mid).setdefault("human_feedback", []).append(given)
            out["feedback"] = given
            if m.get("state") == "blocked" and blocked_of(m)["reason"] == "needs_human_feedback":
                m["state"] = "in_progress"  # the feedback is what it was waiting for
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
                m["state"] = "not_started" if was is None or was.get("state") in ("in_progress", "ready_for_review",
                                                                                   "done", "blocked") \
                    else was.get("state")
                if m["state"] != "blocked":
                    m.pop("blocked", None)
                if was is not None:
                    for k in ("fails", "replans", "rounds", "diagnoses", "findings"):
                        if k in was:
                            m[k] = was[k]
                    if settle_replans({"milestones": [was]}, {"milestones": [m]}, stem):
                        # the definitions its reviews failed are gone, so this scope is the re-plan
                        if m["id"] not in out.setdefault("replanned", []):
                            out["replanned"].append(m["id"])
                    m.update(fails=0, rounds=0, diagnoses=0)  # the owner's new scope starts the counts again
                    m.pop("findings", None)
                e = record["milestones"].get(m["id"]) or {}
                record["milestones"][m["id"]] = {"definitions": definitions(m), "reviews": e.get("reviews", []),
                                                 "authorised": stamp, "counted_after": len(e.get("reviews") or []),
                                                 **({"human_feedback": e["human_feedback"]} if e.get("human_feedback")
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
                out["commit"] = e["accepted"].get("commit") or ready_record(e).get("commit")
                e.setdefault("history", []).append(e.pop("accepted"))
                m["state"] = "ready_for_review"
            elif verb == "reopen":
                if m.get("state") != "blocked" or blocked_of(m)["reason"] != "too_many_failed_reviews":
                    raise SystemExit(f"error: {mid} is {m.get('state')}, not Blocked with too many failed reviews")
                m.update(state="in_progress", fails=0, rounds=0, diagnoses=0)
                m.pop("blocked", None)
                e["counted_from"], e["counted_after"] = stamp["at"], len(e.get("reviews") or [])  # counts start again
                e.pop("too_many_failed_reviews", None)
            write_json(path, doc)
            written.append(done_rel(prof, stem))
            if verb == "rereview":
                written += [str(p.relative_to(t)) for p in (t / prof["evidence"] / stem).glob(f"{mid}-review-*.md")]
        write_json(rec_path, record)
        return written

    ok, detail = loop_write(worktree, prof, key, change,
                            f"orchestrate: owner {verb} {stem} {mid}: {words.splitlines()[0][:80]}")
    if ok and verb in ("accept", "release") and mid != "design":
        drop_hold(worktree, prof, key, mid)
    if ok and verb == "scope":
        out["worktree"] = settle_scoped(worktree, prof, done_rel(prof, stem))
        if out.get("replanned"):
            out["replanned_why"] = (f"{', '.join(out['replanned'])} {'was' if len(out['replanned']) == 1 else 'were'} "
                                    "owed a re-plan; this scope replaced the definitions its reviews failed, so it "
                                    "counts as the re-plan: fails 0, one more replans, state not_started")
    if ok and feedback:
        out["next"] = next_cmd(loop_cmd("run", "--module", stem, "--worktree", str(worktree)), "lead",
                               f"the Human Feedback is in the record file; the resumed builder is told to read it "
                               f"there ({record_rel(prof, stem)}, milestones.{mid}.human_feedback)")
    print(json.dumps({"result": ("RELEASED" if verb == "release" else "DONE") if ok else "FAILED", "action": verb,
                      "module": stem, "milestone": mid, "detail": detail, **out}))
    sys.exit(0 if ok else 1)


# ------------------------------------------------------------------------------------------------- migrate

FLAT_NAMES = (("{}.md", "design"), ("{}-PLAN.md", "plan"), ("{}-DONE.json", "done"), ("{}-ACCEPTED.json", "record"),
              ("{}-BRIEF.md", "brief"))


def split_log(text: str) -> tuple[str, str]:
    """(a plan without its `## Log` section, the section's lines). The section runs to the next `#` or `##` heading."""
    kept, log, inside = [], [], False
    for line in text.splitlines(keepends=True):
        if re.match(r"^##\s+Log\s*$", line, re.IGNORECASE):
            inside = True
            continue
        if inside and re.match(r"^#{1,2}\s", line):
            inside = False
        (log if inside else kept).append(line)
    return "".join(kept).rstrip("\n") + "\n", "".join(log).strip("\n")


def set_plans_line(text: str, to: str) -> str:
    """ORCHESTRATE.md with its Plans line naming `to`, adding the line after the last settings line if it has none."""
    line = re.compile(r"^(\s*[-*]\s*\*\*Plans:\*\*[ \t]*).*$", re.IGNORECASE | re.MULTILINE)
    if line.search(text):
        return line.sub(lambda m: m.group(1) + to, text, count=1)
    settings = list(re.finditer(r"^\s*[-*]\s*\*\*[^*]+:\*\*.*$", text, re.MULTILINE))
    at = settings[-1].end() if settings else len(text)
    return text[:at] + ("\n" if at else "") + f"- **Plans:** {to}" + ("" if at < len(text) else "\n") + text[at:]


def migrate_tree(tree: Path, prof: dict, to: str | None, done: dict) -> list[str]:
    """Moves the plans in a checkout from the flat layout into a folder per module, splits each plan's `## Log` into
    LOG.md, and with `to` moves the whole plans folder there and rewrites the Plans line. Returns every path
    written or removed, and fills `done` with what it did. Records hold no paths and a design's hash is of its
    text, so acceptance survives the move. Then it brings the settings file, each done-when file and each record
    file to the names of 2.0, re-stamping each stored definitions hash the rename alone would change."""
    plans, paths = prof["plans"], []

    def move(src: str, dst: str) -> None:
        if (tree / dst).exists():
            raise SystemExit(f"error: can't move {src} to {dst}, which already exists; move or merge it by hand first")
        (tree / dst).parent.mkdir(parents=True, exist_ok=True)
        os.rename(tree / src, tree / dst)
        paths.extend([src, dst])

    for stem in flat_modules(tree, plans):
        for pattern, kind in FLAT_NAMES:
            if (tree / plans / pattern.format(stem)).is_file():
                move(f"{plans}/{pattern.format(stem)}", module_file(prof, stem, kind))
        done.setdefault("modules", []).append(stem)
        plan = tree / plan_rel(prof, stem)
        if plan.is_file():
            kept, log = split_log(plan.read_text())
            if log:
                plan.write_text(kept)
                path = tree / log_rel(prof, stem)
                earlier = path.read_text().rstrip("\n") if path.exists() else f"# {stem} log"
                path.write_text(f"{earlier}\n\n{log}\n")
                paths.extend([plan_rel(prof, stem), log_rel(prof, stem)])
                done.setdefault("logs_split", []).append(stem)
    if to and to != plans:
        listed = git(tree, "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", plans + "/").stdout
        for rel in sorted(n for n in listed.split("\0") if n and (tree / n).exists()):
            move(rel, to + rel[len(plans):])
        profile_path = tree / PROFILE_FILE
        before = profile_path.read_text() if profile_path.exists() else ""
        if profile_value(before, "plans") or to != PROFILE_FIELDS["plans"]:
            profile_path.write_text(set_plans_line(before, to))
            paths.append(PROFILE_FILE)
        done["plans"] = to
    settings = tree / PROFILE_FILE
    if settings.exists() and (renamed := rename_labels(settings.read_text())) != settings.read_text():
        settings.write_text(renamed)
        paths.append(PROFILE_FILE)
        done.setdefault("renamed", []).append(PROFILE_FILE)
    now_plans = {**prof, "plans": done.get("plans", plans)}
    for stem in modules_here(tree, now_plans):
        doc_path, rec_path = tree / done_rel(now_plans, stem), tree / record_rel(now_plans, stem)
        try:
            old_doc = json.loads(doc_path.read_text())
            old_rec = json.loads(rec_path.read_text()) if rec_path.exists() else None
        except json.JSONDecodeError:
            continue
        new_doc = upgrade_doc(old_doc)
        if new_doc is not old_doc:
            write_json(doc_path, new_doc)
            paths.append(done_rel(now_plans, stem))
            done.setdefault("renamed", []).append(done_rel(now_plans, stem))
        if old_rec is not None:
            new_rec = upgrade_record(old_rec, old_doc, new_doc)
            if new_rec != old_rec:
                write_json(rec_path, new_rec)
                paths.append(record_rel(now_plans, stem))
                done.setdefault("renamed", []).append(record_rel(now_plans, stem))
    tracked = set(git(tree, "ls-files", "-z", "--", *paths).stdout.split("\0")) if paths else set()
    # a file moved twice (into its folder, then with the folder) passed through a path that never existed in git
    return [p for p in dict.fromkeys(paths) if (tree / p).exists() or p in tracked]


MIGRATE_SUBJECT = "orchestrate: migrate the plans to a folder per module and the names of 2.0"


def old_names_in_tree(tree: Path) -> tuple[list[str], dict]:
    """(what in a checkout still uses the flat layout or the names from before 2.0, one phrase each; the settings
    as `migrate` reads them there)."""
    p = profile(tree, missing_ok=True, flat_ok=True, old_ok=True)
    flat = [f"{p['plans']}/{s}-DONE.json (the flat layout)" for s in flat_modules(tree, p["plans"])]
    return flat + old_names_here(tree, p["plans"]), p


def worktrees_on_old_names(worktree: Path) -> list[dict]:
    """Every worktree of the repository whose files still use the flat layout or the names from before 2.0, each
    with the `migrate --branch` command that brings it over. The script's own checkouts aren't listed."""
    own = loop_dir(worktree)
    blocks = git(worktree, "worktree", "list", "--porcelain").stdout.split("\n\n")
    out = []
    for block in blocks:
        lines = block.splitlines()
        path = next((Path(l[len("worktree "):]) for l in lines if l.startswith("worktree ")), None)
        if path is None or "bare" in lines or not path.is_dir() or own in path.resolve().parents:
            continue
        branch = next((l[len("branch refs/heads/"):] for l in lines if l.startswith("branch refs/heads/")), None)
        try:
            found, _ = old_names_in_tree(path)
        except SystemExit:  # settings there that can't be read: `run` names the problem itself
            continue
        if found:
            out.append({"worktree": str(path), "branch": branch or "a detached HEAD", "old_names": found[:3],
                        "command": loop_cmd("migrate", "--branch", "--worktree", str(path))})
    return out


def bring_up(worktree: Path, prof: dict, ref: str) -> str:
    """Fast-forwards a clean worktree that's behind `ref`, and says what became of it: fast-forwarded, or left as it
    was and why, naming `migrate --branch` for commits of its own still on the old names."""
    if git(worktree, "status", "--porcelain").stdout.strip():
        return "left as it was, because it has uncommitted changes; fast-forward it once they're dealt with"
    if is_ancestor(worktree, "HEAD", ref):
        if git(worktree, "merge", "--ff-only", "--quiet", ref).returncode == 0:
            return f"fast-forwarded to {base_ref(prof)}"
        return "left as it was"
    if old_names_in_tree(worktree)[0]:
        return ("left as it was: it has commits of its own on the old names, so bring them over with "
                f"`{loop_cmd('migrate', '--branch', '--worktree', str(worktree))}`")
    return f"left as it was: it has commits of its own, so rebase it onto {base_ref(prof)}"


def branch_module(worktree: Path, prof: dict, ref: str, start: str, end: str) -> str | None:
    """The module a builder's worktree is for: the one its run state names, else the one whose files its own
    commits (from `start` to `end`, in the new names) changed. None when that isn't one module."""
    at_tip = {m.upper(): m for m in modules_at(worktree, prof, ref)}
    state = Path(git(worktree, "rev-parse", "--absolute-git-dir").stdout.strip()) / "orchestrate"
    if Path(git_common_dir(worktree)) != state.parent:  # a linked worktree's own state; the main one's is shared
        named = {at_tip[p.stem.upper()] for p in state.glob("*.json") if p.stem.upper() in at_tip}
        if len(named) == 1:
            return named.pop()
    touched = {where[0].upper() for rel in git(worktree, "diff", "--name-only", start, end).stdout.split()
               if (where := module_of(prof, rel))}
    found = [at_tip[m] for m in touched if m in at_tip]
    return found[0] if len(found) == 1 else None


def migrate_branch(a: argparse.Namespace, worktree: Path, prof: dict, done_with) -> None:
    """`migrate --branch`: renames a worktree's own commits, made before the main branch was migrated, as `migrate`
    renamed the main branch, then rebases them onto it. Each commit's tree is migrated in a checkout of its own, so the
    rebase replays only the builder's changes, in the new names, and meets no conflict in a file the renames
    changed. It holds only the module's run lock, so other modules' runs carry on."""
    wt = str(worktree)
    try:
        ref = tip(worktree, prof)
        scratch_name = "_migrate-" + hashlib.sha1(wt.encode()).hexdigest()[:10]
        scratch = verify_tree(worktree, scratch_name, ref)
    except TipError as e:
        done_with("FAILED", 1, detail=str(e))
    at_tip, tip_prof = old_names_in_tree(scratch)
    if at_tip:
        drop_tree(worktree, scratch_name)
        done_with("REFUSED", 1, problems=[
            f"{base_ref(prof)} still uses the old layout or names ({'; '.join(at_tip[:3])}). --branch brings a "
            "worktree over once the main branch has been migrated, so migrate that first"],
            next=next_cmd(loop_cmd("migrate", "--worktree", wt), "lead",
                          "migrate the main branch first; it waits until no run is working in the repository"))
    if dirty := git(worktree, "status", "--porcelain").stdout.strip():
        done_with("REFUSED", 1, problems=[f"{wt} has uncommitted changes ({dirty[:200]}). Its builder commits them, "
                                          "or you set them aside with `git stash`, before its commits are renamed"])
    was = head_commit(worktree)
    base = git(worktree, "merge-base", "HEAD", ref).stdout.strip()
    if not base:
        done_with("FAILED", 1, detail=f"{wt} shares no history with {base_ref(prof)}")
    if git(worktree, "rev-list", "--merges", f"{base}..HEAD").stdout.strip():
        done_with("REFUSED", 1, problems=[
            f"{wt} has merge commits of its own since it left {base_ref(prof)}, and --branch renames a straight line "
            "of commits. Its builder rebases them into one line first"])
    own = git(worktree, "rev-list", "--reverse", f"{base}..HEAD").stdout.split()
    if not own:
        drop_tree(worktree, scratch_name)
        done_with("NOTHING", detail="this worktree has no commits of its own, so there is nothing to rename",
                  worktree=bring_up(worktree, prof, ref))
    trees, did = [], {}
    for c in [base, *own]:
        git(scratch, "checkout", "--quiet", "--force", "--detach", c)
        git(scratch, "clean", "-ffdq")
        here = profile(scratch, missing_ok=True, flat_ok=True, old_ok=True)
        migrate_tree(scratch, here, tip_prof["plans"] if here["plans"] != tip_prof["plans"] else None, did)
        git(scratch, "add", "-A")
        trees.append(git(scratch, "write-tree").stdout.strip())
    drop_tree(worktree, scratch_name)
    if all(t == git(worktree, "rev-parse", f"{c}^{{tree}}").stdout.strip() for c, t in zip([base, *own], trees)):
        done_with("NOTHING", detail="this worktree's commits already use the current layout and names",
                  worktree=bring_up(worktree, prof, ref))

    def commit(tree: str, parent: str, source: str | None) -> str:
        if source is None:
            message = f"orchestrate: {base[:12]} in the current layout and names, for migrate --branch\n\n{TRAILER}\n"
            env = os.environ
        else:
            name, email, date, message = git(worktree, "log", "-1", "--format=%an%x00%ae%x00%aI%x00%B",
                                             source).stdout.split("\x00", 3)
            env = {**os.environ, "GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": date}
        r = subprocess.run(["git", "-C", wt, *ident(worktree), "commit-tree", tree, "-p", parent, "-F", "-"],
                           input=message, capture_output=True, text=True, env=env)
        if r.returncode != 0:
            done_with("FAILED", 1, detail=f"couldn't write a renamed commit: {r.stderr.strip()[-300:]}")
        return r.stdout.strip()

    renamed_base = last = commit(trees[0], base, None)
    for c, t in zip(own, trees[1:]):
        last = commit(t, last, c)
    if module := getattr(a, "module", None):
        stem = next((m for m in modules_at(worktree, tip_prof, ref) if m.upper() == module.upper()), None)
        if not stem:
            done_with("REFUSED", 1, problems=[f"{module} isn't a module at {base_ref(prof)}"])
    else:
        stem = branch_module(worktree, tip_prof, ref, renamed_base, last)
    if not stem:
        done_with("REFUSED", 1, problems=[f"the script can't tell which module {wt} builds, so it can't hold that "
                                          "module's run lock. Name it with --module"])
    if not run_lock(worktree, stem.upper()):
        who = run_holder_info(worktree, stem.upper())
        done_with("REFUSED", 1, problems=[f"a run holds {stem}{holder_text(who)}, and its builder may be working in "
                                          f"{wt}. Its commits are renamed while nothing is"],
                  next=next_cmd(loop_cmd("pause", "--module", stem, "--worktree", wt), "lead",
                                f"stop {stem}'s run, then run migrate --branch again; other modules' runs carry on",
                                then=loop_cmd("migrate", "--branch", "--worktree", wt, "--module", stem)))
    if head_commit(worktree) != was or git(worktree, "status", "--porcelain").stdout.strip():
        done_with("REFUSED", 1, problems=[f"{wt} changed while its commits were being renamed; run this again"])
    if (r := git(worktree, "reset", "--quiet", "--keep", last)).returncode != 0:
        done_with("FAILED", 1, detail=f"couldn't move {wt} to its renamed commits: {r.stderr.strip()[-300:]}")
    log = git(worktree, "log", "--first-parent", "--format=%H%x00%P%x00%s", f"{base}..{ref}").stdout.splitlines()
    migration = next(((h, parents.split()[0]) for h, parents, subject in (l.split("\x00", 2) for l in log)
                      if subject.startswith(MIGRATE_SUBJECT) and parents), None)

    def rebase_onto(target: str) -> list[str]:
        """Rebases the renamed commits onto `target`: the files that conflicted, after aborting, or none."""
        if git(worktree, *ident(worktree), "rebase", "--quiet", "--onto", target, renamed_base).returncode == 0:
            return []
        conflicts = git(worktree, "diff", "--name-only", "--diff-filter=U").stdout.split() or ["the same files"]
        git(worktree, "rebase", "--abort")
        return conflicts

    behind = ""
    if conflicts := rebase_onto(ref):
        # The main branch's changes since the migration are an ordinary rebase for the builder's next `merge`. Onto
        # the migration commit itself, only changes made before it can conflict.
        if migration and migration[0] != ref and not rebase_onto(migration[0]):
            behind = (f", onto {migration[0][:12]}, the migration commit, and not the tip: the builder's commits and "
                      f"later commits on {base_ref(prof)} both changed {', '.join(conflicts[:10])}, which the "
                      "builder resolves in its next merge, as in any rebase")
        else:
            git(worktree, "reset", "--quiet", "--keep", was)
            why = (f"the builder's own commits and {base_ref(prof)} both changed {', '.join(conflicts[:10])} since "
                   "the worktree branched, before the migration. The renames didn't cause it, and the worktree is left "
                   "as it was")
            done_with("REFUSED", 1, problems=[why], conflicts=conflicts, **({"next": next_cmd(
                f"git -C {shlex.quote(wt)} rebase {migration[1][:12]}", "lead",
                f"have the worktree's builder rebase it onto {migration[1][:12]}, the main branch just before the "
                "migration, where both sides still use the old names, and resolve the conflicts there. Then run "
                "migrate --branch again, which then meets none", then=loop_cmd("migrate", "--branch", "--worktree", wt))}
                if migration else {}))
    renamed = sorted(set(did.get("renamed", [])) | {f"{tip_prof['plans']}/{m}/" for m in did.get("modules", [])})
    done_with("MIGRATED", module=stem, commit=head_commit(worktree), was=was, commits=len(own), renamed=renamed,
              worktree=f"its {plural(len(own), 'commit')} renamed and rebased{behind or ' onto ' + base_ref(prof)}; "
                       "they have new ids, and `was` is the old HEAD",
              **({"conflicts": conflicts} if behind else {}), **upstream_changes(worktree, base, len(own)),
              next=next_cmd(loop_cmd("run", "--module", stem, "--worktree", wt), "lead",
                            f"the worktree uses the current names now, so {stem}'s builder can carry on"))


def left_behind(behind: list[dict], otherwise: dict | None = None) -> dict:
    """The result fields that name the worktrees still on the old names, with `next` bringing over the first."""
    if not behind:
        return {"next": otherwise} if otherwise else {}
    return {"worktrees_on_old_names": behind, "next": next_cmd(
        behind[0]["command"], "lead",
        f"{plural(len(behind), 'worktree')} still {'uses' if len(behind) == 1 else 'use'} the old names, and `run` "
        "refuses each until it is brought over. migrate --branch renames a worktree's own commits and rebases them "
        "onto the main branch, holding only its module's run lock, so other modules' runs carry on")}


def cmd_migrate(a: argparse.Namespace) -> None:
    """Moves a project from flat plan files (<MODULE>-DONE.json and the rest, side by side) to a folder per module,
    and brings it to the names of 2.0, through a clean checkout of the tip, in one commit made as the script. With
    --branch, brings one worktree's own commits over to a main branch already migrated (`migrate_branch`)."""
    worktree = Path(a.worktree).resolve()
    prof = profile(worktree, strict=True, flat_ok=True, old_ok=True)

    def done_with(result: str, code: int = 0, **fields) -> None:
        print(json.dumps({"result": result, **fields}))
        sys.exit(code)

    if os.environ.get("ORCHESTRATE_ROLE"):
        raise SystemExit("error: migrate can't run inside a session the script started; the lead runs it")
    if getattr(a, "branch", False):
        if getattr(a, "to", None):
            raise SystemExit("error: --to moves the main branch's plans folder; --branch follows wherever it went")
        migrate_branch(a, worktree, prof, done_with)
    to = a.to.strip().rstrip("/") if getattr(a, "to", None) else None
    if to and (to.startswith("/") or ".." in Path(to).parts or not to):
        raise SystemExit(f"error: --to {a.to!r} must be a folder inside the repository, such as docs/plans")
    if to and to != prof["plans"] and (to.startswith(prof["plans"] + "/") or prof["plans"].startswith(to + "/")):
        raise SystemExit(f"error: --to {to} is inside {prof['plans']}, or holds it; pick a folder beside it")
    # A main branch already migrated needs no lock: nothing on it changes. In Thrum the lead asked eight times when
    # to stop every run for a migrate that had nothing left to do but name the worktrees left behind.
    try:
        ref = tip(worktree, prof)
        at_tip, tip_prof = old_names_in_tree(verify_tree(worktree, "_migrate-tip", ref))
    except TipError as e:
        done_with("FAILED", 1, detail=str(e))
    drop_tree(worktree, "_migrate-tip")
    if not at_tip and (not to or to == tip_prof["plans"]):
        here = bring_up(worktree, prof, ref)
        behind = worktrees_on_old_names(worktree)
        done_with("NOTHING", detail=f"the plans at {base_ref(prof)} already have a folder per module and the names "
                                    "of 2.0", worktree=here, **left_behind(behind))
    folder = loop_dir(worktree)
    busy = [name for name in (p.name[len("run-"):-len(".lock")] for p in folder.glob("run-*.lock"))
            if run_holder(folder, name) not in (None, os.getpid())]
    if busy or not run_lock(worktree, "_plan"):
        done_with("REFUSED", 1, problems=[
            f"a run, review, plan or adopt is running here ({', '.join(busy) or '_plan'}). migrate moves every "
            "module's files on the main branch, so run it once they've stopped (`runs --repo` shows them, `pause` "
            "stops them). After that, a worktree left with commits of its own on the old names is brought over with "
            "`migrate --branch`, while the other modules build"])
    for name in {s.upper() for s in flat_modules(worktree, prof["plans"]) + modules_here(worktree, prof)}:
        run_lock(worktree, name)  # nothing starts on a module while its files move
    drift = folder_drift(worktree, prof["plans"], ref)
    if stranded := drift["uncommitted"] + drift["unmerged"]:
        done_with("REFUSED", 1, problems=[
            f"these plan files here aren't at {base_ref(prof)}: {', '.join(stranded[:10])}. migrate moves the files "
            f"at the tip, so set these aside first (`git stash push --include-untracked -- {prof['plans']}`), "
            "migrate, then put them back under their new names"])
    did: dict = {}

    def change(t):
        return migrate_tree(t, profile(t, missing_ok=True, flat_ok=True, old_ok=True), to, did)

    ok, landed = loop_write(worktree, prof, "_migrate", change, MIGRATE_SUBJECT + (f", under {to}" if to else ""),
                            take_up_ok=False)
    if not ok:
        done_with("FAILED", 1, detail=landed)
    try:
        landed_tip = tip(worktree, prof, fetch=False)  # past the migration, to the STATUS.md written after it
    except TipError:
        landed_tip = landed
    here = bring_up(worktree, prof, landed_tip)
    behind = worktrees_on_old_names(worktree)
    if not did:
        done_with("NOTHING", detail=f"the plans at {base_ref(prof)} already have a folder per module and the names "
                                    "of 2.0", worktree=here, **left_behind(behind))
    done_with("MIGRATED", commit=landed, plans=did.get("plans", prof["plans"]), modules=did.get("modules", []),
              **({"logs_split": did["logs_split"]} if did.get("logs_split") else {}),
              **({"renamed": did["renamed"]} if did.get("renamed") else {}), worktree=here,
              **left_behind(behind, next_cmd(loop_cmd("status", "--worktree", str(worktree)), "lead",
                                             "see the project in its new layout; STATUS.md is written beside the "
                                             "module folders")))


def build_parser() -> argparse.ArgumentParser:
    """The command line: every command, its flags and their defaults."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    def host_args(p):
        p.add_argument("--host", help="codex, claude, or a host named in the project settings (default: see above)")
        p.add_argument("--model", help="default: the settings' line for this kind of agent on the host "
                                       "(e.g. 'Claude planner'), else its model for the host")
        p.add_argument("--effort", help="default: medium (high for planners), or the settings' Effort")
        p.add_argument("--turn-timeout-hours", type=float, default=2.0)

    run = sub.add_parser("run")
    run.add_argument("--module", required=True)
    run.add_argument("--worktree", required=True)
    run.add_argument("--milestone")
    run.add_argument("--fresh", action="store_true",
                     help="start a new session even if one exists. Without it the script starts one anyway when the "
                          "old session is over 60%% full, another version of the script started it, or resuming it "
                          "failed, and says why in fresh_because")
    run.add_argument("--message", help="first prompt on resume, e.g. the reviewer's findings message")
    run.add_argument("--owner-rule", action="append", help="a restriction the owner gave in conversation; stored "
                     "with the module's run state and restated every turn, across --fresh and milestones")
    run.add_argument("--clear-owner-rules", action="store_true", help="drop stored owner rules (when the owner says)")
    run.add_argument("--budget-hours", type=float, default=4.0)
    run.add_argument("--no-design-review", action="store_true", help="return DESIGN_NOT_APPROVED instead of running the "
                     "owed design review first")
    run.add_argument("--checks-only", action="store_true", help="start no agent: run the script's checks on the "
                     "milestone's merged work and set it Ready for Review if they pass (READY_FOR_REVIEW), or say why "
                     "not (CHECKS_FAILED). For a builder in a chat with no lead, after it merges")
    run.add_argument("--more-builders", metavar="OWNER_WORDS", help="the owner's words, as they gave them, for "
                     "starting a builder past the count in the project settings' Builders line, where `run` "
                     "otherwise prints REFUSED")
    run.add_argument("--review-host", help="the host for the owed design review run starts itself (default: the "
                     "settings' Review host, `other` meaning the host the planner turn that wrote the plan isn't on, "
                     "or the builder isn't on when the script doesn't know the planner; else the builder's host)")
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
    merge_p = sub.add_parser("merge", help="rebase, run the test command and merge, under the merge lock")
    merge_p.add_argument("--worktree", default=".")
    merge_p.add_argument("--no-check", action="store_true", help="skip the test command")
    merge_p.set_defaults(func=cmd_merge)
    ready = sub.add_parser("ready")
    ready.add_argument("--worktree", default=".")
    ready.set_defaults(func=cmd_ready)
    status = sub.add_parser("status")
    status.add_argument("--module")
    status.add_argument("--worktree", default=".")
    status.add_argument("--format", choices=["text", "md"], default="text",
                        help="md: the owner's page, STATUS.md, as the script writes it")
    status.set_defaults(func=cmd_status)
    migrate = sub.add_parser("migrate", help="move flat plan files into a folder per module, and bring a project to "
                                             "the names of orchestrate 2.0")
    migrate.add_argument("--worktree", default=".")
    migrate.add_argument("--to", help="also move the whole plans folder here, and change the Plans line to match "
                                      "(for example docs/plans)")
    migrate.add_argument("--branch", action="store_true",
                         help="bring this worktree's own commits, made before the main branch was migrated, over to "
                              "the new names and rebase them onto it, holding only the module's run lock")
    migrate.add_argument("--module", help="with --branch: the module the worktree builds, when the script can't tell")
    migrate.set_defaults(func=cmd_migrate)
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
    adopt_p.add_argument("paths", nargs="*", help="plan files to merge (default: every unmerged one)")
    adopt_p.set_defaults(func=cmd_adopt)
    pause = sub.add_parser("pause")
    pause.add_argument("--module")
    pause.add_argument("--worktree", default=".")
    pause.set_defaults(func=cmd_pause)
    owner = sub.add_parser("owner", help="record a decision the owner gave the lead in chat")
    owner.add_argument("action", choices=["accept", "rereview", "reopen", "scope", "release", "feedback"])
    for flag in ("--module", "--milestone", "--worktree"):
        owner.add_argument(flag, required=True)
    owner.add_argument("--text", "--reason", dest="text",
                       help="the owner's words for this decision, as they gave them (for feedback, --said)")
    owner.add_argument("--said", help="feedback: the owner's words, as they gave them")
    owner.add_argument("--asked", help="feedback: the question the lead asked the owner")
    owner.add_argument("--item", action="append", help="feedback: an item the owner's words cover (repeatable)")
    owner.set_defaults(func=cmd_owner)
    quota = sub.add_parser("quota")
    quota.add_argument("--worktree", help="also forecast this repository's open milestones")
    quota.add_argument("--budget", type=float, default=120.0, help="seconds to spend reading rollouts")
    quota.add_argument("--json", action="store_true", help="the full report, as JSON")
    quota.set_defaults(func=cmd_quota)
    prof = sub.add_parser("settings", aliases=["profile"], help="print the project settings, as the script reads them")
    prof.add_argument("--worktree", default=".")
    prof.add_argument("--host", help="also check that host's loader (default: see above)")
    prof.set_defaults(func=cmd_settings)
    check = sub.add_parser("check")
    check.add_argument("--module", required=True)
    check.add_argument("--milestone", required=True)
    check.add_argument("--worktree", default=".", help="the tree to run the checks in (default: here)")
    check.add_argument("--plans-from", help="the worktree whose done-when file to read (default: --worktree)")
    check.add_argument("--timeout", type=float, default=600.0, help="seconds per check")
    check.add_argument("--json", action="store_true", help="the full result, as JSON")
    check.add_argument("--items-only", action="store_true",
                       help="run only the items' checks, each under its own lock, and not the project's test command")
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
    runs = sub.add_parser("runs", aliases=["loops"])  # `loops` before 2.1.0
    runs.add_argument("--repo", help="only runs in the repository holding this path")
    runs.add_argument("--json", action="store_true", help="one JSON object, for a lead")
    runs.set_defaults(func=cmd_loops)
    lock = sub.add_parser("lock")
    lock.add_argument("--worktree")
    lock.add_argument("name")
    lock.add_argument("command_args", nargs=argparse.REMAINDER)
    lock.set_defaults(func=cmd_lock)
    background = sub.add_parser("background", help="start a long command as a background job, logged under the git "
                                                   "directory; `wait` waits for it")
    background.add_argument("--worktree", help="the worktree the job belongs to and runs in (default: here)")
    background.add_argument("--log", help="where its output goes (default: a file under <git dir>/orchestrate/jobs)")
    background.add_argument("command_args", nargs=argparse.REMAINDER,
                            help="-- COMMAND... (one argument runs in the shell)")
    background.set_defaults(func=cmd_background)
    jobs = sub.add_parser("jobs", help="list this worktree's background jobs and whether each is still running")
    jobs.add_argument("--worktree", default=".")
    jobs.add_argument("--json", action="store_true")
    jobs.set_defaults(func=cmd_jobs)
    wait = sub.add_parser("wait", help="block until a background job ends or its log matches, then print its last "
                                       "lines")
    wait.add_argument("job", nargs="?", help="a job id or pid from `background` or `jobs`")
    wait.add_argument("--worktree", default=".")
    wait.add_argument("--file", help="wait on this log instead of a job (with --pid or --until)")
    wait.add_argument("--pid", type=int, help="with --file: stop when this process ends")
    wait.add_argument("--until", help="stop when the log's end matches this regular expression")
    wait.add_argument("--timeout", type=float, default=JOB_WAIT_S, help="seconds before returning anyway "
                      f"(default {JOB_WAIT_S:.0f}, under Claude's ten-minute Bash limit)")
    wait.add_argument("--lines", type=int, default=JOB_TAIL_LINES, help="how many of the log's last lines to print")
    wait.set_defaults(func=cmd_wait)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "worktree", None) and args.func is not cmd_quota:
        QUOTA_WORKTREE[:] = [Path(args.worktree).resolve()]
    try:
        args.func(args)
    except WriteBlocked as e:
        stop_on_write(args, e)
    except OSError as e:  # the script's own files under .git: its locks, run state and clean checkouts
        if e.errno not in (errno.EPERM, errno.EACCES, errno.EROFS):
            raise
        stop_on_write(args, WriteBlocked(e.filename, e.strerror or str(e)))


def stop_on_write(args: argparse.Namespace, e: WriteBlocked) -> None:
    """One result line for a write the sandbox refused or a lock someone holds, naming the path and the fix."""
    again = shlex.join(["python3", str(LOOP), *sys.argv[1:]])
    if args.func is cmd_merge:
        print(json.dumps({"result": "FAILED", "detail": e.reason(), "blocked_write": e.fields()["blocked_write"]}))
    else:
        print(json.dumps({"result": "SCRIPT_FAILED", **e.fields(), "next": next_cmd(
            again, "lead", "the lock is held; run the command again once it's free" if e.held else
            "run the same command outside the sandbox, or with escalation")}))
    sys.exit(1)


if __name__ == "__main__":
    main()
