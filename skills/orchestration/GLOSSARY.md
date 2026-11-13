# Glossary of the orchestrate set

The agreed name for each thing in the orchestrate set. The skills, the README and the agent files use these
names, and each skill defines the ones it uses before their first use, because each skill is read alone. The
script, its files, its commands and its messages use these names too. `Stored as` gives the name as it is
written in a file, a command or the script's output, where that differs from the entry's name.

This file is for the people and agents who write the set. It is not installed with the skills.

## People and agents

**Human**
The person the project is being built for. The README speaks to the human as "you".
Avoid: owner, user, person (in the skills)
Stored as: `human`, as in the `human` commands, `--human-rule`, `decides: human` and the `Human decides` line of
the project settings. Before 2.2 each of these said `owner`, and `migrate` renames the ones kept in files
Agreed: by the human, 2026-11-13.

**Agent**
One AI session working in the human's repository.

**Host**
The program an agent runs in: Claude Code or Codex.

**Lead**
The agent the human chats with. It runs the script's commands and comes back to the human when a decision is
theirs. It never writes or judges code.
Avoid: orchestrator, coordinator

**Planner**
An agent that writes the plan: the module list, and each module's design, plan file and done-when file.

**Builder**
An agent that writes the code for one milestone, proves it and merges it.
Avoid: implementer, worker

**Reviewer**
An agent that judges a design or a milestone. Always a new session, so it has seen none of the work it judges.
Avoid: evaluator
Stored as: `orchestrate-reviewer`, the agent file's name

**Subagent**
A helper agent that an agent starts from inside its own session. The lead doesn't use them to build or review.

**The script**
`build/scripts/agent_loop.py`. Not an agent: a set of commands that start agents, run the tests and keep the
records. Write "the lead runs the `plan` command", never "the lead tells the script to plan".
Avoid: the loop, the harness

## The plan

**Project brief**
What the human wants and why, written by the lead before any planning: the human's request word for word, the
reason, what is left out, how the human will judge the result, and the decisions made so far.

**Glossary**
A project's file of agreed names, `GLOSSARY.md` in the plans folder. This file is the set's own glossary.

**Project settings**
The facts about one project that every agent reads first, in `ORCHESTRATE.md`: where the plans are, the test
command, the targets, the project's rules.
Avoid: profile
Stored as: `ORCHESTRATE.md`

**Target**
A device or platform the product runs on, such as Chrome on a desktop or an iPhone. The project settings list
the targets, with how to run the product on each and how to capture it.
Not: a goal. "Target" never means what a milestone aims at.
Stored as: the `target` field of an item; `stand_in:<what it stands in for>` when the planner accepts a stand-in

**Stand-in**
Something a proof runs on in place of its target, such as a Mac standing in for an iPhone. Only the planner can
accept one.
Stored as: `stand_in:` in an item's `target`

**Module**
A part of the project that one builder can work on without touching the other parts.
Avoid: component, package (unless the code uses the word)

**Module list**
The file that names each module and what each provides to the others.

**Interface**
What one module provides to the others, such as a function that returns the balances. Only a planner changes
one, and a builder who needs a change writes a proposal.

**Design**
A module's file saying what the module must do for the people who use it.

**Plan file**
A module's `PLAN.md`: what is left to build, milestone by milestone, and the assumptions open for the human.

**Log**
A module's `LOG.md`: its history, one dated entry per event.

**Status page**
`STATUS.md` in the plans folder, which only the script writes: an overview for the human, then every module in
build order with its status.
Avoid: dashboard, status lines

**Needs you now**, **Choices made for you**
The first two parts of the status page's overview. Needs you now lists what waits on the human, each line saying
who acts. Choices made for you lists what a planner or the lead chose where the human's words left it open, such
as assumptions and proposed glossary names, each standing until the human says otherwise. What a planner or the
lead can settle without the human goes under Now and next.
Avoid: Waiting on you (the one section these replaced)
Stored as: the `### Needs you now` and `### Choices made for you` headings of `STATUS.md`
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

**Module table**
The table at the top of `ARCHITECTURE.md` listing every module in build order, what each is for and what it needs.

**Milestone**
A piece of a module small enough for one builder to finish in one session.

**Depends on**
A milestone depends on a milestone in another module when it can't start until that one is Done.
Stored as: the milestone's `depends_on` list, such as `["CORE:M3"]`

**Done-when file**
A module's `DONE.json`. For each milestone, it lists the items, how each is proved and its quality bar.
It is written before building, and the builder can't change what it requires.
Avoid: acceptance file, DONE file

**Item**
One thing that must be true before a milestone is Done.
Avoid: criterion, requirement

**Quality bar**
The standard a milestone's work is judged against, with a real example to point at: "help text as clear as
ripgrep's".
Stored as: the milestone's `quality_bar` field (`bar` before 2.2)

**Record file**
A module's `RECORD.json`, which only the script writes. It records which milestones are Done.
Avoid: acceptance record
Stored as: `RECORD.json` (`ACCEPTED.json` before 2.2); a milestone that is Done has `done` in its entry there
(`accepted` before 2.2)

**Worktree**
A second working copy of the repository. Each module is built in its own, so builders don't overwrite each
other's files.

## Proving and judging

**Automated Check**
A shell command that proves an item if it exits with 0. The builder runs it, and the script runs it again.
Stored as: the item's `check` field

**Reviewer Inspection**
A proof in which a reviewer runs the product on its target and judges what it sees.
Stored as: the item's `inspect` field

**Reviewer Question**
A proof in which a reviewer answers a question by reading the code, an interface or a design.
Stored as: the item's `ask` field

**Evidence**
Saved proof that an item passed, such as a test log or a screenshot, taken from the item's target.
Stored as: the item's `evidence` field, which says where the proof is saved

**Capture**
A screenshot, recording or log taken from a target while the product runs. A capture becomes evidence when it is
saved as proof of an item.
Avoid: captures as a word for all evidence

**Test command**
The project's own command that runs its tests, run before every merge.
Stored as: the `Test command:` line of the project settings
Not: Automated Check. An Automated Check proves one item; the test command tests the whole project.

**Review**
A reviewer's written judgement of a design or a milestone. Only a review started by the script's `review`
command is saved.

**Finding**
One problem a review reports, with where it is.

**Must Fix**
A finding that fails the milestone or the design.
Avoid: blocking
Stored as: `must_fix`

**Suggestion**
A finding that doesn't fail anything.
Avoid: advisory
Stored as: `suggestion`

**Could Not Judge**
A reviewer's verdict on an item nobody could check. It counts as a fail.
Stored as: `could_not_judge`

**Needs human feedback, needs access, needs hardware**
How a planner marks an item that a builder can't finish alone. Needs human feedback: someone has to look at the
result and judge it, because the builder can't tell. Needs access: someone has to approve a permission or a
prompt, so the builder runs in a visible session while the human is at the machine, and asks for access as soon
as it starts. Needs hardware: a device has to be connected, so the builder runs the same way.
Avoid: attended, needs a person, person or hardware
Stored as: the item's `needs` field, such as `{"type": "access", "what": "approve Computer Use for IINA"}`,
with `type` one of `human_feedback`, `access` or `hardware`

**Human Feedback**
The human's verdict on an item a builder couldn't judge, such as "looks good to me". The script records it with
the question the lead asked, the human's words, the items it covers and the time, and the reviewer reads it as the
human's own words.
Not: approving access or connecting a device. Those are done, not said, so nothing is recorded. Not a `--message`
from the lead either, which a reviewer can't count as the human's words.
Avoid: owner answer, owner's answers
Stored as: `human_feedback` in the record file, each with `asked`, `said`, `items` and `at`; recorded by the
`human feedback` command

**Failed review**
A review that the milestone didn't pass. The script counts them, and the counts decide the Escalation.
Avoid: round, as a name for one review
Stored as: `failed_reviews`, the count since the script last started counting. It starts again after a
Diagnosis, and after the human's `scope` or `reopen`
Agreed: by the human, 2026-11-13.

**Repeated finding**
A Must Fix that an earlier review also raised: one with the same name, or one on an item that failed before,
unless the reviewer says how it differs.
Stored as: `repeat` on the finding; `failed_reviews_with_repeat` counts the failed reviews that had one
Avoid: recurring finding

**Escalation**
What happens after a failed review, which the script works out from the two counts of failed reviews. In order
as the counts rise: the same builder carries on, a new builder session starts, a planner makes a Diagnosis, and
the milestone is Blocked: Too Many Failed Reviews.
Avoid: ladder
Stored as: `escalation` in a result, one of `same_builder`, `new_builder_session`, `diagnosis` or
`too_many_failed_reviews`
Agreed: by the human, 2026-11-13.

**Diagnosis**
A planner's reading of every review of a milestone that keeps failing, to decide why. A milestone is owed one
after four failed reviews with a Repeated finding, or after six failed reviews in all, and it gets only one. A
diagnosis ends in a Re-plan or in Plan Kept.
Stored as: `diagnoses` on the milestone, which is 0 or 1; in a result, `escalation: diagnosis` with a `cause`,
either "a finding keeps coming back" or "reviews keep finding something new"
Agreed: by the human, 2026-11-13.

**Re-plan**
The end of a Diagnosis in which the planner changes the milestone's items. The milestone goes back to Not
Started, with the new items approved.
Avoid: rewrite, for a change to a plan
Stored as: `replanned` in the result of the `plan` command
Agreed: by the human, 2026-11-13.

**Plan Kept**
The end of a Diagnosis in which the planner leaves the plan as it is and names who has to act: the builder, the
reviewer or the human.
Stored as: the `KEEP` line that ends the planner's turn, and the `KEPT` result of the `plan` command
Agreed: by the human, 2026-11-13.

**Handoff**
What a builder that stops before the milestone is finished writes for the session that picks it up: what is
finished, what was tried, and what to do first.
Stored as: `<evidence folder>/<MODULE>/<milestone>-handoff.md`, named in the milestone's `blocked` field
Proposed: by Claude, 2026-11-13. Not yet agreed by the human.

**Builder's note**
The few sentences under a milestone in the plan file, for its builder, on what the items and the design don't
say. Many milestones have none.
Stored as: the text under the milestone's heading in `PLAN.md`
Proposed: by Claude, 2026-11-13. Not yet agreed by the human.

**Ready for Review record**
The script's record that a builder finished a milestone and the script's checks passed on the merged work: the
builder's commit, the main branch's tip the checks ran on, and the tokens the builder used. The script writes it
in the same commit that sets the milestone to Ready for Review. A milestone that is Ready for Review without one,
or whose record is older than its last failed review, was set by a builder before 2.1.0, and `run` checks it
before anyone reviews it. The reviewer's task names the commit from it.
Avoid: claim, claim record
Stored as: `ready_for_review` in the milestone's entry in the record file (`claim` before 2.1.0, which `migrate`
renames)
Agreed: by the human, 2026-11-12.

## Statuses

A milestone's status, in the order a milestone usually meets them, stored in its `status` field in the done-when
file (`state` before 2.2). Waiting and Blocked each carry a reason, written
after a colon, such as "Blocked: Needs Access".

| Status | Means | Stored as |
|---|---|---|
| Not Started | No builder has worked on it yet | `not_started`; the `ready` command prints `can_start` when nothing stops it starting |
| In Progress | A builder is working on it | `in_progress`, or `in_progress_elsewhere` when another lead started it |
| Ready for Review | The builder says it is finished, the script's checks passed on the merged work, and no reviewer has judged it yet. Only the script sets it | `ready_for_review` |
| Waiting | It isn't stuck. The next step is already lined up, and happens without anyone stepping in | `waiting`, in the script's output, with its `reason` |
| Blocked | It can't move until someone steps in | `blocked`, with the milestone's `blocked` field giving `reason`, `items` and `what` |
| Done | Every check and review has passed | `done`, in the done-when file and as the milestone's key in the record file |

When a lead starts a milestone, the script marks it In Progress in the shared git remote, so that no other lead,
in this clone or another, starts it too. The mark is a git ref, `refs/orchestrate/claims/<MODULE>/<milestone>`,
whose path keeps its name from before 2.1.0 so that leads on older versions still see it. The `human release`
command takes a milestone out of In Progress when the lead that started it is gone.

The reasons a milestone is Waiting:

| Reason | Means | Stored as |
|---|---|---|
| On Dependency | It can't start until another module's milestone, already planned, is Done | `on_dependency` |
| For Diagnosis | It keeps failing review, so a planner finds out why: four failed reviews had a repeated finding, or six reviews failed in all | `for_diagnosis`, with the `cause` |

The reasons a milestone is Blocked, and who steps in:

| Reason | Means | Stored as |
|---|---|---|
| Needs Human Feedback | A builder couldn't judge an item and asked for a human eye. The lead shows the human the evidence and the question, and the human's reply is the Human Feedback | `needs_human_feedback` |
| Needs Access | A builder or a reviewer couldn't get a permission or an approval prompt, or couldn't reach the product, usually because it ran where nobody could approve it. The next visible run, with the human at the machine, unblocks it. A reviewer's Needs Access counts no failed review | `needs_access`; a reviewer's `BLOCKED needs_access` ending |
| Needs Hardware | A device wasn't connected. The next run with the device there unblocks it | `needs_hardware` |
| Needs Context | The builder is missing a fact. The lead supplies it | `needs_context`, from the builder's `NEEDS_CONTEXT` ending |
| Needs Dependency | It needs something another module owns that no plan provides yet. A planner adds it | `needs_dependency` |
| Too Many Failed Reviews | It kept failing review after its Diagnosis, or the planner found that the decision is the human's. The human decides what happens to it, and the `human reopen` command records it | `too_many_failed_reviews` |

A milestone stops only when it is finished or Blocked. Nothing should ask the human to confirm a step they have
already taken, such as approving a prompt.

Avoid: claimed, parked, attended, Waiting on Dependency, For Replan, Awaiting Replan, Awaiting Diagnosis, Needs Human
Feedback as a status of its own (in prose)

A design has three statuses of its own: Design Ready for Review, Design Changes Requested and Design Approved.

## Commands and settings

**Merge**
Bring a builder's work into the main branch, through the script's `merge` command, which runs the test command
first and holds a lock so two builders can't merge at once. The milestone stays In Progress: `merge` refuses a
commit that sets it Ready for Review or Done, because only the script sets those, after its own checks.
Avoid: integrate, land (in prose)
Stored as: the `merge` command, and the `merge` lock; the `Merge:` line of the project settings, which says
whether to push or fast-forward

**`Human decides` list**
The line of the project settings that lists what only the human may decide, such as spending or publishing.
Stored as: the `Human decides` line (`Owner decides` before 2.2, which `migrate` renames)

**Exclusive resource**
Something only one run at a time may use, such as a simulator. The script's `lock` command holds it.
Avoid: lease, slot
Stored as: the `Exclusive resources` line of the project settings

**Run**
One `run`, `review` or `plan` command working on a module, with the agent sessions it starts. The `runs`
command lists every run on the machine.
Avoid: loop, the loop
Stored as: the `runs` command (`loops` before 2.1.0, still accepted); the notes it keeps stay under
`~/.local/state/orchestrate/loops`
Agreed: by the human, 2026-11-12.

**Step**
What a run is doing now, such as `builder turn 3`, `checking M2: the test command` or `merging the review`. While
an agent's turn runs, `runs` also names the tool call the agent is waiting on and for how long.
Stored as: `step` and `open_tool_call` in each run's note and in `runs --json`
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

**Builders count**
How many builders the human wants running at once in the project, read from the number in the project settings'
`Builders:` line. `run` refuses a builder past that count, so that the number running is the number the human
asked for. The human's own words, passed with `--more-builders`, let one more start.
Avoid: parallelism, concurrency (in prose)
Stored as: the `Builders:` line; `run --more-builders '<what the human said, in their words>'`; `more_builders` in `run`'s result,
with what they said, how many builders were running and when
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

**Background job**
A long command an agent starts with the script's `background` command, so that it carries on when the agent's
turn ends. The agent waits for it with `wait`, which returns when the job ends, and `jobs` lists them.
Stored as: `<git common dir>/orchestrate/jobs.jsonl`, with each job's log under `orchestrate/jobs/`
Agreed: by the human, 2026-11-12.

**Saved check output**
The whole stdout and stderr of each check the script runs, for the builder's `check`, for `merge`'s test command
and for the script's own checks, kept in files that the check's failure message names. The message holds only
the end of the output, and the line that explains a failure is often earlier.
Stored as: files under `<git common dir>/orchestrate/checks/`. `check --json` names them in each item's `stdout`
and `stderr`.
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

**Reused check**
A check the script didn't run again, because the same command had already passed on the same files: the files
checked out, leaving out the plans folder, with nothing outside it changed. A pass is reused, never a failure.
Without this, the checks at the end of a milestone run up to three times on the same files.
Stored as: `reused` on an item in `check`'s output; `reused_checks` in `run`'s `READY_FOR_REVIEW` result, and
`reused` in the Ready for Review record; each pass is kept beside the saved check output
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

**Checks only**
A `run` that starts no agent. It runs the script's checks on a milestone whose work is already merged, and sets it
Ready for Review if they pass. A builder in a chat with no lead uses it after it merges, since nobody else runs
the checks there.
Stored as: `run --checks-only`
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

**Usage ledger**
The file where the script writes one row for each agent turn with the tokens it used, which the `cost` and
`report` commands add up. A Codex turn's tokens are the rise in its session's running total across the turn, read
from the session's rollout file, the log Codex keeps of each session under `~/.codex/sessions/`. Rows written
before 2.1.0 counted a resumed Codex session's earlier tokens again, so `cost` says from which date its Codex
figures are each turn's own.
Stored as: `<git common dir>/orchestrate/usage.jsonl`. A row's `context` and `window` say how full the turn left
its session, `version` is the script's version, and `stderr` is the end of the host's error output for a failed
turn. `cost --json` gives the date as `codex_per_turn_from`.
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

**How full a session is**
The size of a session's last request and its reply, against the most the session can hold. Before each turn, the
script starts a new session instead of resuming the old one when the old one is more than 60% full, or when
another version of the script started it, or when resuming it failed before its turn started.
Stored as: `context` and `window`, in the usage ledger and in the run's state file
(`<git common dir>/orchestrate/<MODULE>.json`), which also keeps `version`, the version of the script that
started the session. `run`'s result gives `fresh_because`, a list of why each new session was started.
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

**Stopped turn**
A headless turn the script ended itself. It stops a turn whose tool call, other than a shell command, a subagent
or a wait, has been open for more than 15 minutes, because a call such as a screenshot of a locked screen can
wait for hours without failing. The next turn is told which call was stopped. A turn that reached the turn limit names its last
open tool call the same way.
Stored as: `stopped_turn` in the run's state file and in the result of the command whose turn it was, with `why`
and `tool_call` (its `name` and `input`)
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

**What changed**
The list of changes to how the set behaves, in the first result any command prints after the script's version
changes in a project. The lead reads it, so that a lead who learned the older behaviour isn't surprised.
Stored as: `changed` in that result, a list of lines for each version newer than the last one seen; the last
version seen is in `<git common dir>/orchestrate/version.json`
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

**Migrating a branch**
Renaming a worktree's own commits, made before the main branch was migrated, the way `migrate` renamed the main
branch, then rebasing them onto it. `run` refuses such a worktree, and a plain rebase conflicts in the files the
renames rewrote, which are easy to resolve wrongly by hand. It holds only that module's run lock, so other
modules keep building.
Stored as: `migrate --branch`; `worktrees_on_old_names` in `migrate`'s result lists the worktrees that need it
Proposed: by the set's author, 2026-11-12. Not yet agreed by the human.

## Results

Every command of the script ends by printing one JSON line, its result, whose `result` field is one of the names
below. The lead decides what to do next from it, and the `build` skill's tables say what to do for each. A
`reason` field, where there is one, says which of a result's causes it was.

| Result | Printed by | Means |
|---|---|---|
| `READY_FOR_REVIEW` | `run` | The builder finished, the script's checks passed on the merged work, and the script set the milestone to Ready for Review. With `review: false` it needed no reviewer, so it is Done |
| `NEEDS_REVIEW` | `run` | The module's next milestone is already Ready for Review, with its record, and needs its review |
| `DESIGN_NOT_APPROVED` | `run` | The module's design isn't Design Approved: it is Design Ready for Review or Design Changes Requested |
| `WAITING` | `run` | The milestone is Waiting, with the reason in `reason` |
| `BLOCKED` | `run`, `plan`, `review` | The milestone is Blocked, or the planner ended Blocked, or the reviewer couldn't reach the product (`reason` `needs_access`), so nothing was merged and no failed review was counted |
| `NEEDS_CONTEXT` | `run`, `plan` | The agent is missing a fact |
| `IN_PROGRESS_ELSEWHERE` | `run` | Another lead or run is working on the module |
| `FINISHED` | `run` | Every milestone of the module is Done |
| `CHECKS_FAILED` | `run` | The builder said it had finished three times, and each time the script's checks disagreed. With `--checks-only`, the checks failed once, or the work wasn't merged with every item passing |
| `NO_PROGRESS_FOR_HOURS` | `run` | No new item passed and the builder made no commit of its own for the hours given with `--no-progress-hours` |
| `STALLED` | `run` | Three turns in a row changed nothing and reported nothing |
| `HOST_FAILED` | `run`, `review`, `plan` | The host failed: two turns failed in a row, its program is missing, or its usage limit was reached |
| `SCRIPT_FAILED` | any command | The script couldn't do a step of its own, such as fetching the main branch or writing a file the sandbox refused |
| `WRONG_MODEL_OR_EFFORT` | `run`, `review` | A turn ran on a model or effort other than the ones the command named |
| `PAUSED` | `run`, `plan` | `pause` stopped it, or the human stopped it or opened the session in the app |
| `INVALID` | `run`, `review`, `plan` | A done-when file can't be read, or an agent changed what isn't its to change |
| `REVIEWED` | `review` | The review was saved, with its verdict in `verdict` |
| `PLANNED` | `plan` | The planner's files were checked and merged |
| `KEPT` | `plan` | A planner asked to diagnose a milestone kept the plan as it is and named who has to act |
| `UNFINISHED` | `plan` | The planner's turn ended without one of its endings, so nothing was merged |
| `MERGED`, `FAILED` | `merge` | The work was merged, or wasn't, with the reason in `detail` |
| `ADOPTED` | `adopt` | Plan files left uncommitted or unmerged were committed and merged |
| `MIGRATED` | `migrate` | The plans were moved to the current layout and names, or, with `--branch`, a worktree's own commits were renamed and rebased onto the main branch |
| `NOTHING` | `adopt`, `migrate` | There was nothing to do |
| `REFUSED` | `adopt`, `migrate`, `run` | The command wouldn't act, with the reasons in `problems`. `run` refuses a builder past the `Builders:` count, naming the others in `running`, unless `--more-builders` carries the human's words |
| `UNBLOCKED` | `unblock` | The milestone is no longer Blocked |
| `DONE`, `RELEASED`, `FAILED` | `human` | The human's decision was saved, or, for `human release`, a milestone another lead started was taken out of In Progress. `FAILED` says it couldn't be saved |

Avoid: `FLOOR` (now `HOST_FAILED` or `SCRIPT_FAILED`), `PIN` (now `WRONG_MODEL_OR_EFFORT`), `DESIGN_OWED` (now
`DESIGN_NOT_APPROVED`), `NOT_READY` (now `CHECKS_FAILED`), `BUDGET` (now `NO_PROGRESS_FOR_HOURS`), `REVIEW_OWED` (now
`NEEDS_REVIEW`), `TAKEN` (now `IN_PROGRESS_ELSEWHERE`). The script still reads `PIN` in the state files of runs
started before 2.1.0. Proposed: the new names, by the set's author, 2026-11-12. Agreed by the human, 2026-11-12.
