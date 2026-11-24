# Glossary of the orchestrate set

The agreed name for each thing in the orchestrate set. The skills, the README and the script use
these names, and each skill defines the ones it uses before their first use, because each skill is read alone.
`Stored as` gives the name as it is written in a file, a command or the script's output, where that differs. An
entry with a `Proposed:` line hasn't been agreed by the user yet; every other entry has.

This file holds names and what they mean. How each thing works is in the script's `--help`, and where each file
lives is what `settings` prints, so neither is repeated here. This file is for the people and agents who write the
set. It is copied with the plugin, but no skill reads it or points agents at it.

## People and agents

**User**
The person the agents work with, who wants the project built and makes its decisions. The README speaks to the
user as "you".
Not: End user. The user decides what is built; end users use what is built.
Avoid: human, owner, person
Source: the standard term in agent prompting, as Anthropic's and OpenAI's docs and the hosts' system prompts use it
Stored as: `human`, as in the `human` commands, `--human-rule`, `decides: human`, `human_feedback` and the
`Human decides` line of the project settings

**End user**
Someone who will use what the project builds, such as a player of a game or a customer of a shop. They may
include the user.
Not: User, the person the agents work with.
Avoid: user, for this meaning
Source: the standard term in software and requirements engineering

**Agent**
One AI session working in the user's repository.

**Host**
The program an agent runs in: Claude Code or Codex.

**Lead**
The agent the user chats with. It runs the script's commands and comes back to the user when a decision is
theirs. It never writes or judges code.
Avoid: orchestrator, coordinator
Source: the lead agent of Anthropic's multi-agent research system, which plans the work and starts subagents

**Planner**
An agent that writes the plan: the module list, and each module's design, plan file and done-when file.

**Task**
What one agent session is asked to do, such as planning a change or building a work package. The lead writes a
planner's task; the script writes a builder's and a reviewer's.
Not: Work package, which is a piece of the plan; a builder's task names the work package it builds.
Avoid: brief (the prompting-agents skill's word for any text written for an agent), `briefs` (now `tasks`)
Source: the agent field's word for what a lead hands a subagent (Anthropic's multi-agent research system)
Stored as: `plan --task`; the `tasks` list in the record file

**Kind of task**
Which of an agent's instructions a task needs. The planner's kinds are a new project, a module, a change,
unblocking, a diagnosis, a design revision and a fix; the reviewer's are a work package review and a design review.
Each has its file in that skill's `tasks/` folder.
Stored as: `plan --kind`; `review --kind work-package` or `review --kind design`

**Builder**
An agent that writes the code for one work package, proves it and merges it.
Avoid: implementer, worker

**Reviewer**
An agent that judges a design or a work package. Always a new session, so it has seen none of the work it judges.
Avoid: evaluator

**Design reviewer**
A reviewer judging a module's design, with its done-when items, before any of the module is built.
Stored as: `design reviewer` in a settings line, such as `Codex design reviewer: high`
Proposed: by Claude, 2026-11-18. Not yet agreed by the user.

**Subagent**
A helper agent that an agent starts from inside its own session.

**The script**
`lead/scripts/agent_loop.py`. Not an agent: a set of commands that start agents, run the tests and keep the
records. Write "the lead runs the `plan` command", never "the lead tells the script to plan".
Avoid: the loop, the harness

## The plan

**Vision and scope document**
What the user wants and why, written in the lead's interview before any planning, and kept for the life of the
product: the user's requests word for word, the goal, who it is for, the milestones on the way, what the first
release covers and what comes later, what is left out, how the user will judge the result, and the decisions made
so far. Always written in full; "vision" alone is a single statement inside it.
Avoid: project brief, brief (several meanings), `BRIEF.md` (now `VISION.md`); project charter (a charter is for one project and closes with it);
product requirements document (a list of requirements, which this is not)
Source: Karl Wiegers, *Software Requirements*, the vision and scope document
Stored as: `VISION.md`

**Goal**
The one long-term aim the product is working toward now, set in the vision and scope document. When it is reached,
the next goal replaces it.
Not: Milestone, a point on the way to the goal.
Source: Scrum's Product Goal, the long-term objective, one at a time

**Glossary**
A project's file of agreed names. This file is the set's own glossary.
Stored as: `GLOSSARY.md`

**Project settings**
The facts about one project that every agent reads first: where the plans are, the test command, the targets and
the project's rules.
Avoid: profile
Stored as: `ORCHESTRATE.md`

**Project guidance**
The project's own guidance for each kind of work, such as a skill on how this project is built, which the project
settings link to.
Avoid: building guidance
Stored as: the `## Project guidance` section of `ORCHESTRATE.md`
Proposed: by Claude, 2026-11-18. Not yet agreed by the user.

**`Human decides` list**
What only the user may decide, such as spending or publishing.
Stored as: the `Human decides` line of the project settings

**Target**
A device or platform the product runs on, such as Chrome on a desktop or an iPhone.
Not: a goal. "Target" never means what a work package aims at.
Stored as: the `target` field of an item

**Stand-in**
Something a proof runs on in place of its target, such as a Mac standing in for an iPhone. Only a planner can
accept one.
Stored as: `stand_in:<what it stands in for>` in an item's `target`

**Module**
A part of the project that one builder can work on without touching the other parts.
Avoid: component, package (unless the code uses the word)

**Module list**
The file that names each module and what each provides to the others.

**Module table**
The table at the top of `ARCHITECTURE.md` listing every module in build order, what each is for and what it needs.

**Interface**
What one module provides to the others, such as a function that returns the balances. Only a planner changes one.

**Design**
A module's file saying what the module must do for the people who use it.

**Plan file**
A module's `PLAN.md`: what is left to build, work package by work package, and the assumptions open for the user.

**Builder's note**
The few sentences under a work package in the plan file, for its builder, on what the items and the design don't say.
Stored as: the text under the work package's heading in `PLAN.md`
Proposed: by Claude, 2026-11-13. Not yet agreed by the user.

**Log**
A module's `LOG.md`: its history, one dated entry per event.

**Milestone**
A significant point on the way to the goal that the user cares about and that shapes the work, such as a first
playable build. It is reached when the work packages it needs are Done.
Not: Work package, which is work; a milestone is a point the work reaches.
Source: PMI, "a significant point or event in a project"

**Work package**
A piece of a module small enough for one builder to finish in one session, with the items that must be true before
it is Done. Always the full phrase, because "package" alone means a code package.
Not: Task, which is what one agent session is asked to do; Milestone, which is a point the work reaches.
Avoid: milestone (its former name), `milestones` (now `work_packages`), `M3` (now `WP3`), story, task
Source: PMBOK, the work package at the lowest level of the work breakdown
Stored as: `work_packages` in the done-when and record files, with IDs such as `WP3`

**Depends on**
A work package depends on a work package in another module when it can't start until that one is Done.
Stored as: the work package's `depends_on` list, such as `["CORE:WP3"]`

**Done-when file**
A module's file that lists, for each work package, the items, how each is proved and its quality bar. It is written
before building, and the builder can't change what it requires.
Avoid: acceptance file, DONE file
Stored as: `DONE.json`

**Item**
One thing that must be true before a work package is Done.
Avoid: criterion, requirement

**Quality bar**
The standard a work package is judged against, with a real example to point at: "help text as clear as
ripgrep's".
Stored as: the work package's `quality_bar` field

**Record file**
A module's file that only the script writes. It records which work packages are Done and what approved the design.
Avoid: acceptance record
Stored as: `RECORD.json`; a work package that is Done has `done` in its entry there

**Ready for Review record**
The script's record that a builder finished a work package and the script's checks passed on the merged work: the
builder's commit, the main branch's tip the checks ran on, and the tokens the builder used.
Avoid: claim, claim record
Stored as: `ready_for_review` in the work package's entry in the record file

**Status page**
The file in the plans folder, which only the script writes, with an overview for the user and every module in
build order with its status.
Not: Dashboard, which is drawn from the delivery history.
Avoid: status lines
Stored as: `STATUS.md`

**Needs you now**, **Choices made for you**
The first two parts of the status page's overview. Needs you now lists what waits on the user, each line saying
who acts. Choices made for you lists what a planner or the lead chose where the user's words left it open, such as
assumptions and proposed glossary names, each standing until the user says otherwise.
Avoid: Waiting on you
Stored as: the `### Needs you now` and `### Choices made for you` headings of `STATUS.md`
Proposed: by Claude, 2026-11-12. Not yet agreed by the user.

**Worktree**
A second working copy of the repository. Each module is built in its own, so builders don't overwrite each other's
files.
Source: git's own term, from `git worktree`
Stored as: the `Worktrees:` line of the project settings, with which the script gives each module its own on the
branch `build/<module>`; the `worktree` field of `run`'s result

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

**Test command**
The project's own command that runs its tests, run before every merge.
Not: Automated Check. An Automated Check proves one item; the test command tests the whole project.
Stored as: the `Test command:` line of the project settings

**Main-branch check**
A check too slow to run before every merge, which runs on the main branch's tip after merges instead. A failure
that holds is traced to the first failing commit, which is fixed forward. It gates no work package.
Not: Test command, which runs before every merge.
Avoid: trunk sentinel, sentinel
Stored as: a `Main-branch check <name>:` line of the project settings; the `main-check` command
Proposed: by Claude, 2026-11-15. Not yet agreed by the user.

**Evidence**
Saved proof that an item passed, such as a test log or a screenshot, taken from the item's target. It is kept in
the working folder, never in git.
Stored as: the item's `evidence` field, which says where the proof is saved

**Working folder**
The one folder per repository where evidence, reviews and handoffs are kept, outside git, shared by every worktree.
Avoid: evidence folder
Stored as: the `Evidence:` line of the project settings, which names where each worktree opens it
Proposed: by Claude, 2026-11-18. Not yet agreed by the user.

**Capture**
A screenshot, recording or log taken from a target while the product runs. A capture becomes evidence when it is
saved as proof of an item.
Avoid: captures, as a word for all evidence

**Saved check output**
The whole output of each check the script runs, kept in a file that the check's failure message names.
Proposed: by Claude, 2026-11-12. Not yet agreed by the user.

**Reused check**
A check the script didn't run again, because the same command had already passed on the same files. A pass is
reused, never a failure.
Stored as: `reused` on an item in `check`'s output, and `reused_checks` in `run`'s result
Proposed: by Claude, 2026-11-12. Not yet agreed by the user.

**Review**
A reviewer's written judgement of a design or a work package.

**Finding**
One problem a review reports, with where it is.

**Must Fix**
A finding that fails the work package or the design.
Avoid: blocking
Stored as: `must_fix`

**Suggestion**
A finding that doesn't fail anything.
Avoid: advisory
Stored as: `suggestion`

**Could Not Judge**
A reviewer's verdict on an item nobody could check. It counts as a fail.
Stored as: `could_not_judge`

**Repeated finding**
A Must Fix that an earlier review also raised.
Avoid: recurring finding
Stored as: `repeat` on the finding

**Needs user feedback, needs access, needs hardware**
How a planner marks an item that a builder can't finish alone. Needs user feedback: someone has to look at the
result and judge it. Needs access: someone has to approve a permission or a prompt. Needs hardware: a device has to
be connected.
Avoid: attended, needs a person
Stored as: the item's `needs` field, with `type` one of `human_feedback`, `access` or `hardware`

**User Feedback**
The user's verdict on an item a builder couldn't judge, such as "looks good to me", recorded with the question the
lead asked. A reviewer reads it as the user's own words.
Not: approving access or connecting a device, which are done, not said. Not a `--message` from the lead either.
Avoid: owner answer
Stored as: `human_feedback` in the record file; the `human feedback` command

**Failed review**
A review that the work package didn't pass.
Avoid: round, as a name for one review
Stored as: `failed_reviews`

**Escalation**
What happens after a failed review, worked out from the counts of failed reviews. In order as the counts rise: the
same builder carries on, a new builder session starts, a planner makes a Diagnosis, and the work package is Blocked:
Too Many Failed Reviews.
Avoid: ladder
Stored as: `escalation` in a result, one of `same_builder`, `new_builder_session`, `diagnosis` or
`too_many_failed_reviews`

**Diagnosis**
A planner's reading of every review of a work package that keeps failing, to decide why. It ends in a Re-plan or in
Plan Kept.
Stored as: `diagnoses` on the work package; `escalation: diagnosis` in a result, with a `cause`

**Re-plan**
The end of a Diagnosis in which the planner changes the work package's items.
Avoid: rewrite, for a change to a plan
Stored as: `replanned` in the result of `plan`

**Plan Kept**
The end of a Diagnosis in which the planner leaves the plan as it is and names who has to act.
Stored as: the `KEEP` line that ends the planner's turn, and the `KEPT` result of `plan`

**Handoff**
What a builder that stops before the work package is finished writes for the session that picks it up: what is
finished, what was tried, and what to do first.
Not: a handoff in the OpenAI Agents SDK, which passes the live conversation to another agent in the same run.
Stored as: `<work-package-id>-handoff.md` in the module's part of the working folder
Proposed: by Claude, 2026-11-13. Not yet agreed by the user.

## Statuses

A work package's status, in the order a work package usually meets them, stored in its `status` field in the done-when
file. Waiting and Blocked each carry a reason, written after a colon, such as "Blocked: Needs Access".

| Status | Means | Stored as |
|---|---|---|
| Not Started | No builder has worked on it yet | `not_started`; `ready` prints `can_start` when nothing stops it starting |
| In Progress | A builder is working on it | `in_progress`, or `in_progress_elsewhere` when another lead started it; the mark other leads see is the git ref `refs/orchestrate/claims/<MODULE>/<work-package-id>` |
| Ready for Review | The builder says it is finished, the script's checks passed on the merged work, and no reviewer has judged it yet. Only the script sets it | `ready_for_review` |
| Waiting | It isn't stuck. The next step is already lined up, and happens without anyone stepping in | `waiting`, in the script's output, with its `reason` |
| Blocked | It can't move until someone steps in | `blocked`, with the work package's `blocked` field giving `reason`, `items` and `what` |
| Done | Every check and review has passed | `done`, in the done-when file and in the record file |

The reasons a work package is Waiting:

| Reason | Means | Stored as |
|---|---|---|
| On Dependency | It can't start until a work package in another module is Done, whether or not that module has planned it yet | `on_dependency` |
| For Planning | Every planned work package of the module is Done, and the plan names more with no items yet, so a planner writes the next stretch | `for_planning`, with `later` |
| For Diagnosis | It keeps failing review, or a review found something only a planner can settle, so a planner finds out why | `for_diagnosis`, with the `cause` |

The reasons a work package is Blocked:

| Reason | Means | Stored as |
|---|---|---|
| Needs User Feedback | An item needs the user's judgement | `needs_human_feedback` |
| Needs Access | The builder couldn't get a permission or an approval prompt, or couldn't reach the product | `needs_access` |
| Needs Hardware | A device wasn't connected | `needs_hardware` |
| Needs Context | The builder is missing a fact, which the lead supplies | `needs_context`, from the builder's `NEEDS_CONTEXT` ending |
| Needs Dependency | It needs something another module owns that no plan provides yet | `needs_dependency` |
| Too Many Failed Reviews | It kept failing review after its Diagnosis, or the planner found that the decision is the user's | `too_many_failed_reviews` |

Avoid: claimed, parked, attended, Waiting on Dependency, For Replan, Awaiting Replan, Awaiting Diagnosis, Needs User
Feedback as a status of its own (in prose)

A design has statuses of its own:

| Status | Means | Stored as |
|---|---|---|
| Design Ready for Review | A planner wrote or changed the design, and no design review has judged it as it now stands | a `design` in the record file that is neither of the others, or none |
| Design Changes Requested | The latest design review asked for changes | `design.verdict` `changes` in the record file; the review's `DESIGN CHANGES` line |
| Design Approved | The design as it now stands is approved, so building can start | `design.verdict` `ok` whose `hash` is the design's; `by` says what approved it |

Proposed: the design statuses as entries, by Claude, 2026-11-20. Not yet agreed by the user.

## Commands and settings

**Merge**
Bring a builder's work into the main branch, through the script's `merge` command, which runs the test command
first.
Avoid: integrate, land (in prose)
Stored as: the `merge` command and the `merge` lock; the `Merge:` line of the project settings

**Merge batch**
Branches that asked to merge while another merge was running, merged together with one run of the test command. If that run fails, the batch is split to find the branch that
broke it.
Avoid: train, which in GitLab's merge trains means a queue that tests each request with the ones ahead of it
Source: batching with bisection, as Bors does it
Stored as: the `batch` field of `merge`'s result
Proposed: by Claude, 2026-11-15. Not yet agreed by the user.

**Run**
One `run`, `review` or `plan` command working on a module, with the agent sessions it starts.
Avoid: loop, the loop
Stored as: the `runs` command, which lists every run on the machine

**Step**
What a run is doing now, such as `builder turn 3` or `merging the review`.
Stored as: `step` and `open_tool_call` in `runs --json`
Proposed: by Claude, 2026-11-12. Not yet agreed by the user.

**Routine steps**
The steps a `run` or `plan` command carries on through by itself, because the process settles them without
judgement, such as the review of a work package that reached Ready for Review. The command stops at anything else and
wakes the lead.
Not: Step, which is what one run is doing now.
Stored as: `steps_run` and `stopped_because` in the result of `run` and `plan`; `--one-step` for one step only
Proposed: by Claude, 2026-11-18. Not yet agreed by the user.

**Checks only**
A `run` that starts no agent. It runs the script's checks on a work package whose work is already merged, and sets it
Ready for Review if they pass.
Stored as: `run --checks-only`
Proposed: by Claude, 2026-11-12. Not yet agreed by the user.

**Most builders**
The most builders the user allows running at once in the project. With no number, there is no most.
Avoid: Builders count, parallelism, concurrency (in prose)
Stored as: the `Builders:` line of the project settings; the `most` field of `builders`
Proposed: by Claude, 2026-11-24. Not yet agreed by the user.

**Working number of builders**
How many builders the lead runs at once, within the user's most, from what the machine and the work can take.
Stored as: `builders --set N --why TEXT`; the `working` field of `builders`
Proposed: by Claude, 2026-11-24. Not yet agreed by the user.

**Exclusive resource**
Something only one run at a time may use, such as a simulator. The script's `lock` command holds it.
Avoid: lease, slot
Stored as: the `Exclusive resources` line of the project settings

**Shared resource**
Something several runs may use at once, up to a number the project settings give, such as a GPU that takes three
renders side by side.
Avoid: slot, pool
Stored as: the `Shared resources` line of the project settings, such as `gpu: 3`; an item's `"lock": "gpu"`, or
`"lock": "gpu.alone"` for a run that needs the whole device
Proposed: by Claude, 2026-11-15. Not yet agreed by the user.

**Hold limit**
How long a command may hold a lock before the script stops it, so one stuck run can't keep everyone else waiting.
Stored as: the `Lock hold limit` line of the project settings
Proposed: by Claude, 2026-11-15. Not yet agreed by the user.

**Background job**
A long command an agent starts with the script's `background` command, so that it carries on when the agent's
turn ends.
Stored as: the `background`, `wait` and `jobs` commands

**Supervisor**
The one process per repository that the script keeps running through a build. It starts the runs whose next step
is routine, up to the builders count, and wakes the lead for everything else. Any command starts it when none is
running.
Source: a process supervisor, the field's name for a process that keeps others running and restarts them.
Stored as: the `supervise` command; `supervisor.json` and `supervisor.lock` in the script's folder under the git
common dir
Proposed: by Claude, 2026-11-23. Not yet agreed by the user.

**Wake**
The supervisor telling the lead that something needs its judgement. It goes through the lead's host where the host
allows it, such as a message to a Claude Code session or a queued message on a Codex app thread, and otherwise
through `watch`.
Stored as: `wake.json` in the script's folder; the `wake` field of a lead's results when nothing can wake it; the
`Lead wake` line of the project settings
Proposed: by Claude, 2026-11-23. Not yet agreed by the user.

**Watch**
The command a lead whose host can't be woken by the script keeps running in the background. It ends when the
supervisor wakes the lead.
Stored as: the `watch` command
Proposed: by Claude, 2026-11-18. Not yet agreed by the user.

**Lead check-in**
How long the supervisor waits for a warning sign before it wakes the lead anyway, so the lead looks at delivery
even when nothing has gone wrong.
Stored as: the `Lead check-in` line of the project settings, such as `3h`
Proposed: by Claude, 2026-11-18. Not yet agreed by the user.

**Warning sign**
Something in the script's records that usually means delivery has slowed, such as a builder that has stopped making
progress.
Stored as: `warning_signs` in `watch`'s result
Proposed: by Claude, 2026-11-18. Not yet agreed by the user.

**Flow**
How fast the work moves: work packages reaching Ready for Review and Done, set beside the effort spent on them.
Source: flow and its metrics (throughput, cycle time, work in progress) as the Kanban Guide defines them. Setting
them beside effort is the set's own addition
Stored as: `flow` in the overview, and the `## Flow` part of the report
Proposed: by Claude, 2026-11-15. Not yet agreed by the user.

**Overview**
What moved, what is waiting, where time goes and what is using the machine, in one result for the lead.
Stored as: the JSON from `flow`, also carried in each wake
Proposed: by Codex, 2026-11-23. Not yet agreed by the user.

**Usage ledger**
The file where the script writes one row for each agent turn with the tokens it used.
Stored as: `usage.jsonl`; the `cost` and `report` commands add it up
Proposed: by Claude, 2026-11-12. Not yet agreed by the user.

**Weighted tokens**
Tokens counted at their price relative to a fresh input token. The one measure that compares a Claude turn's cost
with a Codex turn's.
Avoid: cost (alone), which could mean dollars or the Codex weekly limit
Stored as: `weighted` on a turn or session
Proposed: by Claude, 2026-11-18. Not yet agreed by the user.

**How full a session is**
The size of a session's last request and its reply, against the most the session can hold.
Stored as: `context` and `window`, in the usage ledger and the run's state file; `fresh_because` in `run`'s result
Proposed: by Claude, 2026-11-12. Not yet agreed by the user.

**Stopped turn**
A headless turn the script ended itself, because a tool call stayed open too long.
Stored as: `stopped_turn` in the run's state file and the command's result
Proposed: by Claude, 2026-11-12. Not yet agreed by the user.

**Delivery history**
The figures the script copies out of the hosts' session files for one repository: each session and turn with its
tokens, model, timing and how it ended, and the signals between them. It keeps no message text, and it outlives
the hosts' own files.
Avoid: telemetry, analytics, usage log
Stored as: the `history` command, which reads it
Proposed: by Claude, 2026-11-18. Not yet agreed by the user.

**Dashboard**
The page drawn from the delivery history, for the user's review and the lead's diagnosis.
Not: Status page, which shows where the plan stands.
Stored as: the `dashboard` command, which writes `dashboard.html`
Proposed: by Claude, 2026-11-18. Not yet agreed by the user.

**What changed**
The list of changes to how the set behaves, in the first result any command prints after the script's version
changes in a project.
Stored as: `changed` in that result
Proposed: by Claude, 2026-11-12. Not yet agreed by the user.

**Migrating a branch**
Renaming a worktree's own commits, made before the main branch was migrated, the way `migrate` renamed the main
branch, then rebasing them onto it.
Stored as: `migrate --branch`
Proposed: by Claude, 2026-11-12. Not yet agreed by the user.

## Results

Every command of the script ends by printing one JSON line, its result, whose `result` field is one of the names
below. The help of the command that prints a result says what it means and what comes next. A `reason` field, where
there is one, says which of a result's causes it was.

| Result | Printed by | Means |
|---|---|---|
| `READY_FOR_REVIEW` | `run` | The builder finished, the script's checks passed on the merged work, and the work package is Ready for Review. With `review: false` it needed no reviewer, so it is Done |
| `NEEDS_REVIEW` | `run` | The module's next work package is already Ready for Review and needs its review |
| `DESIGN_NOT_APPROVED` | `run` | The module's design is Design Ready for Review or Design Changes Requested |
| `WAITING` | `run` | The work package is Waiting, with the reason in `reason` |
| `BLOCKED` | `run`, `plan`, `review` | The work package is Blocked, the planner ended Blocked, or the reviewer couldn't reach the product (`reason` needs_access), which leaves the work package Ready for Review |
| `NEEDS_CONTEXT` | `run`, `plan` | The agent is missing a fact |
| `IN_PROGRESS_ELSEWHERE` | `run` | Another lead or run is working on the module |
| `FINISHED` | `run` | Every work package of the module is Done |
| `CHECKS_FAILED` | `run` | The builder said it had finished, and the script's checks disagreed, more times in a row than the script allows |
| `NO_PROGRESS_FOR_HOURS` | `run` | No new item passed and the builder made no commit for the hours given |
| `STALLED` | `run` | Several turns in a row changed nothing and reported nothing |
| `HOST_FAILED` | `run`, `review`, `plan` | The host failed, its program is missing, or its usage limit was reached |
| `SCRIPT_FAILED` | any command | The script couldn't do a step of its own, or met an error in its own code |
| `ERROR` | any command | The command stopped before doing what it was asked, with the reason in `error` |
| `RUNNING` | `run`, `review`, `plan`, `unblock` | Only in a result file: the command that writes it hasn't finished |
| `WRONG_MODEL_OR_EFFORT` | `run`, `review` | A turn ran on a model or effort other than the ones the command named |
| `PAUSED` | `run`, `review`, `plan`, `pause` | `pause` or the user stopped it |
| `INVALID` | `run`, `review`, `plan` | A done-when file can't be read, or an agent changed what isn't its to change |
| `REVIEWED` | `review` | The review was saved, with its verdict in `verdict` |
| `PLANNED` | `plan` | The planner's files were checked and merged |
| `KEPT` | `plan` | A planner asked to diagnose a work package kept the plan as it is and named who has to act |
| `UNFINISHED` | `plan` | The planner's turn ended without one of its endings, so nothing was merged |
| `PLAN_NOT_MERGED` | `plan` | The planner finished, but its files couldn't be merged, so they are set aside for another planner |
| `READY` | `ready` | What each module's next work package is waiting for, grouped |
| `ESCALATION` | `next` | What the counts call for after a failed review, with the command |
| `SETTINGS` | `settings` | The settings as the script reads them, with the loader checks |
| `BUILDERS` | `builders` | The most builders, the working number, the limit between them, and the builders running |
| `SAVED` | `settings --set` | A settings line was set on the main branch, with the user's words in its commit |
| `MERGED`, `FAILED` | `merge` | The work was merged, or wasn't, with the reason in `detail` |
| `ADOPTED` | `adopt` | Plan files left uncommitted or unmerged were committed and merged |
| `MIGRATED` | `migrate` | The plans, the evidence or a worktree's commits were moved to the current layout and names |
| `WOULD_REMOVE`, `REMOVED` | `cleanup` | What `cleanup` would remove, or, with `--yes`, what it removed |
| `NOTHING` | `adopt`, `migrate`, `main-check`, `pause`, `thread`, `cleanup`, `settings --set` | There was nothing to do |
| `STARTED`, `ALREADY_RUNNING` | `main-check` | A run on the main branch's tip started, or one was already in flight |
| `MAIN_CHECKS` | `main-check` | The list of main-branch checks, each with its latest run and pass |
| `RAN` | `main-check` | Only in a runner's log: one run of a main-branch check finished |
| `REFUSED` | `adopt`, `main-check`, `migrate`, `plan`, `run`, `settings --set` | The command wouldn't act, with the reasons in `problems` |
| `UNBLOCKED` | `unblock` | The work package is no longer Blocked |
| `THREAD` | `thread status` | A Codex thread's goal, running turn and queue, and whether the script can stop its turn |
| `STOPPED`, `GOAL_PAUSED`, `GOAL_RESUMED`, `UNQUEUED` | `thread` | The thread's turn was stopped, its goal paused or resumed, or its queued messages removed |
| `NOT_DONE` | `thread` | The script couldn't do it on this version of the Codex app, so the user does it in the app, with what to click in `next` |
| `DONE`, `RELEASED`, `FAILED` | `human` | The user's decision was saved, or a work package another lead started was taken out of In Progress, or it couldn't be saved |
| `CHECK_IN` | `watch` | The lead check-in passed with no warning sign |
| `WARNING_SIGNS` | `watch` | A warning sign appeared that the lead hasn't been told about |
| `RUN_ENDED` | `watch` | A top-level `run`, `review` or `plan` ended, with its result in `results` |
| `BUILD_FINISHED`, `WAITING_FOR_USER` | `watch` | Every module is finished, or nothing can move without the user; the supervisor stops after this wake |
| `SUPERVISOR_FAILED` | `watch` | The supervisor couldn't read the records three times running |
| `SUPERVISOR`, `STOPPING`, `SUPERVISOR_STOPPED`, `WAKE_SENT`, `WAKE_FAILED` | `supervise` | Its status; asked to stop; stopped, with `reason`; a test wake reached the lead or didn't |

Avoid: `FLOOR` (now `HOST_FAILED` or `SCRIPT_FAILED`), `PIN` (now `WRONG_MODEL_OR_EFFORT`), `DESIGN_OWED` (now
`DESIGN_NOT_APPROVED`), `NOT_READY` (now `CHECKS_FAILED`), `BUDGET` (now `NO_PROGRESS_FOR_HOURS`), `REVIEW_OWED` (now
`NEEDS_REVIEW`), `TAKEN` (now `IN_PROGRESS_ELSEWHERE`)

Proposed: `ERROR` and `RUNNING`, by Claude, 2026-11-15; `CHECK_IN`, `WARNING_SIGNS`, `RUN_ENDED` and
`PLAN_NOT_MERGED`, by Claude, 2026-11-18; `BUILD_FINISHED`, `WAITING_FOR_USER`, `SUPERVISOR_FAILED` and the
`supervise` results, by Claude, 2026-11-23; the `thread` results, by Claude, 2026-11-23. Not yet agreed by the user.

## Open questions

- "Design Approved": a design is approved by a DESIGN OK review of it as it now stands, or, after two design
  reviews in a row asked for changes, by the script approving the planner's revision without another review
  (`by: review_limit`). The Delivery Lead read Design Approved as DESIGN OK only. Should the two causes have one
  status or two? The user is still working on the two-round limit.

## Retired

Old names, what replaced them and when. The script's `migrate` command rewrites the ones kept in files.

- Human, for the person the agents work with: now User (2.9.0), in prose and in what the script prints. The
  stored names keep `human`, as the User entry lists.
- `owner` (everywhere it was stored, and the `Owner decides` line): now `human` and `Human decides` (2.2).
- `state`: now `status`, the work package's field (2.2).
- `bar`: now `quality_bar` (2.2).
- `ACCEPTED.json` and `accepted`: now `RECORD.json` and `done` (2.2).
- Claim, and the `claim` field: now Ready for Review record and `ready_for_review` (2.1.0). The git ref
  `refs/orchestrate/claims/` keeps its original prefix.
- `loops`, the command: now `runs` (2.1.0). It is still accepted, and the runs' notes keep the old folder name.
- Evidence folder, a folder in git: now the working folder, outside git (2.6.0).
- Waiting on you, the status page section: now Needs you now and Choices made for you.
- The old result names are under Avoid in Results. The script still reads `PIN` in the state files of runs started
  before 2.1.0.
