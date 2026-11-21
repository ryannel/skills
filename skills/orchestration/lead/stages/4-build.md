# Build

This stage runs once the project is planned and the user has said how they want the agents to work. It lasts
until every milestone in the module list is Done, or until nothing left can move without the user.

Contents:
- [What the user asked for](#what-the-user-asked-for)
- [How the build runs](#how-the-build-runs)
- [What can start](#what-can-start)
- [Starting agents](#starting-agents)
- [What each result means](#what-each-result-means)
- [Where sessions run](#where-sessions-run)
- [What you pass on](#what-you-pass-on)
- [The user's decisions](#the-users-decisions)
- [Telling the user](#telling-the-user)
- [When to stop](#when-to-stop)

## What the user asked for

The user says what to build in plain words, such as "build it with two Claude builders" or "just do the checkout
module". That sets how many builders run, on which hosts (`codex`, `claude`, or a host the project settings name),
which modules, and anything they ruled out. If no module is named, it is every module in the module list. Where
the request leaves something open, the project settings fill it in.

The script already picks the model and effort: the model from the project settings, medium effort for builders and
reviewers, high for planners. Pass `--model` or `--effort` only when the user asked for something different for
that one command, because a flag overrides the settings and one passed out of habit hides a later change to them.

When the user wants one kind of agent set differently from now on, such as "plan with Fable" or "review at high
effort", that is a line in the project settings, such as `Claude planner: claude-fable-5-2 high` or
`Reviewer: high`. [The settings reference](../../planner/references/profile.md#a-model-or-an-effort-for-one-kind-of-agent)
has the forms. Write such a line yourself, as [changing the settings](../references/settings.md) says.

## How the build runs

`run --module <M> --worktree <path>` starts a builder on the module's next milestone and carries on through the steps
that need no judgement. When the milestone reaches Ready for Review, it runs the review. After a failed review that
the counts send back to the builder, it starts the builder again. After a pass, it starts the module's next
milestone. When a design review asks for changes, it runs a planner revision and goes on. `plan` does the same for a
plan: it runs each design review the plan left owed, and a planner revision if a review asks for changes.

Each command stops when it reaches something that needs your judgement or the user's, such as a decision for the
user, a Blocked milestone, a milestone that needs a planner's diagnosis, a finished module, a broken main branch or
a newer copy of the script. Its result is the last step's result, with `steps_run`, each step and how it ended, and
`stopped_because`, which says in a sentence why it stopped there. Read `stopped_because` first, because it is the
reason you were woken. `--one-step` runs just one step.

Start each `run` and `plan` as its own background command, and don't chain several into one. Your host wakes you
when a background command ends, so one command per module wakes you for each stop as it happens, while a chain
wakes you only when its last command ends.

### Keeping watch

Keep `watch --worktree <repo>` running in the background for the whole build. It wakes you in two cases. One is the
check-in, every three hours unless the settings' `Lead check-in:` line says otherwise, which prints `CHECK_IN`. The
other is a warning sign it hasn't told you about yet, such as a builder with no progress for two hours or ready work
waiting beside a free builder slot, which prints `WARNING_SIGNS`. Start `watch` again each time it ends, so the next
check-in or sign wakes you. It counts free builder slots against the `Builders:` line, the only number it can read,
so a lower number the user agreed in the chat is yours to keep, and a slot free under it is no reason to start one.

If your host doesn't wake you when a background command ends, run `watch --runs` as the command you wait on. It also
ends when a `run`, `review` or `plan` of the repository ends, and prints `RUN_ENDED` with their results.

Every `watch` result says what woke you in `woke_for`, and sums up the build for a lead with no other context: what
moved, what isn't moving and why, milestones going back and forth to review, builder slots, planners and the disk.

### When you're woken

Whether a run stopped or `watch` woke you, the question is the same: is the work moving towards the brief as fast as
it could, and if not, what would move it? You have the mandate to act on the answer. The usual moves are:

- Start a builder on ready work, up to the user's number of builders.
- Message a builder that is heading the wrong way, by stopping its run with `pause --module <M>` and starting it
  again with `--message`.
- Start a planner, or bring the user a change to the project settings, when the problem sits above any one
  builder, as under [Reading delivery](#reading-delivery).
- Change the order of the work, so that what the user's next release needs starts first, whether that is a
  module or a planner.
- Ask the user, when the answer is theirs.

Doing nothing is right too, when everything is moving. When the project settings have `Shared resources`,
`Exclusive resources` or `Main-branch check` lines, read [locks and main-branch checks](../references/locks.md)
before you act, because those shape what builders wait for.

### Reading delivery

Busy builders aren't the same as a build that is moving. A builder waiting for a lock, running a proof again or
retrying a merge looks normal from inside its session. Only you see every session at once, so only you can see them
all waiting on the same thing.

Milestones reaching Ready for Review and Done are the measure of delivery. Commits, background jobs and turns
measure effort, and effort can climb while delivery stays flat. `flow --worktree <repo>` puts the two side by side
for the last day, or for `--since <hours>`. Read them against the number of builders. Ten builders finishing two
milestones a day between them, while the main branch takes three hundred commits, means most of the effort is going
somewhere other than the milestones.
For the longer view, by kind of agent, model, error and version of the script, read the
[delivery history](../references/delivery-history.md).

When the numbers drift apart like this, the cause usually sits above any one builder, in the process around the
work: how it is split into modules and milestones, how it merges, what a milestone has to show before it counts, and
what builders wait for. Clearing builders one at a time won't reach it, because each of them is doing what the
process asks of it. Follow the effort to where it goes. Merges that keep conflicting point at how the work is split.
Milestones that fail review again and again point at how they are defined. Builders that queue for one resource, or
repeat work each time the main branch moves, point at the steps around building.

The quality bar can be the cause too. When most milestones fail their first review over differences the user would
never notice, the items are stricter than the way the user will judge the work, and each of those milestones costs
another build and review.

Most of these causes belong to a planner or to the project settings. Once the pattern shows, start a planner whose
task names it and the modules it spans, or bring the user the change, to the settings or to the quality bar, with
what it would cost and what it would give back. Only you see the cost across every module, and only the user can
say what the work is for. When the change reaches many modules, say in the planner's task which come first, such as
those stuck on something the change removes, because each changed design is reviewed again before its builder goes
on. Running fewer builders is a fix too, and often the quickest when they all wait on the same thing, because each
extra builder then adds waiting, not output.

## What can start

`ready --worktree <repo>` gives the detail behind the `watch` summary. It reads every module on the main branch and
sorts each module's next milestone into a group, since a module's milestones run in order.

| Group | The module's next milestone |
|---|---|
| `can_start` | is Not Started, and a builder can start it |
| `waiting` | is Waiting, with its next step lined up in `next`. `reason` is `on_dependency`, for the milestone `depends_on` names, or `for_diagnosis`, for a planner to find out why it keeps failing review, with what the failures share in `cause` |
| `in_progress_elsewhere` | is In Progress under another lead |
| `ready_for_review` | is Ready for Review: the script's checks passed and it waits for a reviewer |
| `design_not_approved` | can't start until a reviewer has approved the module's design |
| `blocked` | is Blocked until someone steps in, with the `reason` |
| `invalid` | can't be read, or an agent changed what it may not |
| `finished` | none: every milestone of the module is Done |

`status --module <M>` lists every milestone of one module with its
latest review. [The done-when reference](../../planner/references/done-when.md#statuses-and-their-stored-names)
lists every status and its stored name.

`ready` also lists under `plan_ahead` the modules in the module table that have no plan yet but whose Needs are
all planned, in build order, each with the `plan` command in its `next`. A module whose Needs the script can't read,
such as one that waits on a decision of the user's, isn't listed: plan it when the user says it's time.

The script reads plans from the main branch, not from your working copy. Plan files that are uncommitted or
unmerged are listed under `unmerged_plans`, and `next` is `adopt --worktree <repo>`, which commits only those files
and merges them. Use it rather than a commit of your own. Until a module's design is approved and while nothing is
built, `adopt` also approves revised items. After that it refuses them, and `next` names `plan` and `human scope`.

Each milestone gets a new builder session, and one builder works in a module at a time. The user's number of
builders is a limit, not a target. Past the `Builders:` count, `run` prints `REFUSED` and starts nothing. Put the
`ask` in its `next` to the user, and only on their yes run its command, with their words in `--more-builders`.
`runs --repo <repo> --json` lists every session in the repository, with what each is doing now, and
`quota --worktree <path>` forecasts whether the Codex weekly usage limit will last.

### Worktrees

Give each module its own worktree on its own branch, in a folder git ignores. A worktree is a second working copy
of the repository, so two builders can work at once. If the repository ignores no folder, add one to
`.git/info/exclude`. With `Merge: push`, branch from the remote:
`git worktree add -b build/<module> <folder>/<module> <remote>/<branch>`. With `Merge: local`, branch from the local
main branch. Builders merge from there with the `merge` command.

## Starting agents

| To start | Run |
|---|---|
| a builder | `run --module <M> --worktree <path> --host <host>` |
| a planner | `plan --worktree <repo> --task "<what to plan>" --host <host>` |
| a reviewer of a milestone | `review --module <M> --milestone <id> --commit <sha> --worktree <path> --host <host>` |
| a reviewer of a design | `review --module <M> --milestone design --worktree <path> --host <host>` |

`run` reviews its own milestones, so you start a review yourself mostly for a milestone that is Ready for Review
with no run going, or after a `--one-step` run. A review started on its own stays one step.

Reviewers and planners work in a checkout the script keeps for them, so their `--worktree` only names the
repository. One planner runs at a time in a repository: a second `plan` waits for the first, then plans from what
it merged, so you can start planners for two modules one after the other. Waiting planners go in the order you
started them, and `status` lists them in that order.

A planner's work merges only on `PLANNED`, including files it wrote outside the plans folder, such as tests. On any
other ending nothing merges, and `stash` and `branch` hold what the planner changed.

When the user works with two hosts, run each review on the host that didn't build the milestone, because a
reviewer from another company shares fewer of the builder's blind spots. `Review host: other` in the project
settings makes that the default, for `review` without `--host` and for the reviews `run` starts. `--host`, or
`run --review-host <host>`, overrides it.

## What each result means

`run` and `plan` carry the routine results on by themselves, so you mostly meet these where a chain stopped. For a
routine step, run `next`. The last column says more only where a step needs your judgement.

| The script prints | Which means | What needs you |
|---|---|---|
| `READY_FOR_REVIEW`, `review: false` | The milestone is Done: it needed no reviewer, and the script's checks passed. | |
| `READY_FOR_REVIEW`, `review: true`, or `NEEDS_REVIEW` | The script's checks passed and it set the milestone Ready for Review. | |
| `REVIEWED`, `DESIGN_NOT_APPROVED` | A review was saved, with its result in `verdict`, or the design review `run` ran first didn't approve the design. | See [After a review](#after-a-review). |
| `WAITING` | Its next step is lined up, as under [What can start](#what-can-start). | Start a builder on other work meanwhile. |
| `IN_PROGRESS_ELSEWHERE` | Another lead, or another `run` here, is working on it. `by` and `holder` say which. | Start a builder on other work. |
| `BLOCKED`, `NEEDS_CONTEXT` | The milestone is Blocked, with its `reason`. | See [A milestone that stopped](#a-milestone-that-stopped). |
| `CHECKS_FAILED` | The builder said three times that it had finished, and each time the script's checks disagreed. | `next` starts the builder again in a new session with the script's reasons, or a planner first when the builder said an item can't be met as written. |
| `NO_PROGRESS_FOR_HOURS` | No new item passed, and the builder made no commit of its own, for the hours given with `--no-progress-hours`. | The same as `CHECKS_FAILED`. |
| `STALLED` | The builder kept ending its turns on progress notes. | The same as `CHECKS_FAILED`. |
| `INVALID` | A done-when file is malformed, an agent changed what isn't its to change, or the items aren't the approved ones. | Send the problems to a planner, and don't resume that builder until they're fixed. When a planner changed the items while the milestone was being built, `next` is `run` again, because nothing is wrong with the builder's work. |
| `FINISHED` | Every milestone of the module is Done. | Remove its worktree once nothing is unmerged. |
| `PLANNED` | The planner's files were checked and merged. | |
| `KEPT` | A planner diagnosing a milestone kept the plan, and `who` names who has to act. A kept plan that names the builder also lifts a block of Needs Context or Needs Dependency. | |
| `PLAN_NOT_MERGED`, `UNFINISHED` | The planner's files couldn't merge, such as when they conflict with a commit that merged meanwhile, or its turn ended without one of its endings. Nothing merged, and `next` gives a planner the task again. | |
| `HOST_FAILED` | The host failed: two failed turns, its program missing, or its usage limit reached, as `reason` says. | Stop that builder and report it with the reason. Builders on another host carry on. |
| `WRONG_MODEL_OR_EFFORT` | A turn ran on a model or an effort other than the one asked for. | Stop that builder and report it with the reason. |
| `PAUSED` | `pause` stopped it, or the user stopped the session or opened it in the app. | Leave a builder the user stopped to them until they say to carry on. |
| `CHECK_IN`, `WARNING_SIGNS`, `RUN_ENDED` | `watch` ended, as under [Keeping watch](#keeping-watch). | See [When you're woken](#when-youre-woken), and start `watch` again. |
| `SCRIPT_FAILED` | The script couldn't do a step of its own, such as fetching the main branch or writing a file the sandbox refused, or it met an error in its own code (`traceback`). The builder's committed work isn't lost. | Do what `reason` and `next` say, then run the command again. Report it only if you can't fix it, and don't call it quota or sign-in, which is `HOST_FAILED`. |
| `ERROR` | The command did nothing: its command line was refused, or a check stopped it, as `error` says. | Fix the command from `error` and `usage`, and run it again. |

The other commands print results of their own. `adopt` prints `ADOPTED` and `migrate` prints `MIGRATED`, and either
prints `NOTHING` when there was nothing to do. `unblock --module <M> --worktree <path>` puts a Blocked milestone
back in the queue once you've cleared what blocked it, and prints `UNBLOCKED` with the `run` to start next. It takes
the module's one Blocked milestone, and needs `--milestone <id>` only when there are two. A `human` command prints
`DONE`, or `RELEASED` for `human release`. `main-check` prints `MAIN_CHECKS`, `STARTED` or `ALREADY_RUNNING`, and
its log marks each finished run `RAN`, as [locks and main-branch checks](../references/locks.md) explains. `pause`
prints `PAUSED` with the runs it stopped, or `NOTHING` when none was going. `cleanup` prints `WOULD_REMOVE`, or
`REMOVED` with `--yes`.

Any command prints `REFUSED`, with `problems` and usually `next`, when it won't act. It prints `FAILED`, with
`detail`, when it tried and couldn't.

Two fields can come with any result. `warnings` names something a host wouldn't load, such as an `AGENTS.md` the
Claude CLI won't read, with the fix. `stopped_turn` says the script ended a turn itself, because a tool call other
than a shell command was open for more than 15 minutes, or because the turn limit was reached.

When a builder's merge finds that the main branch fails its test command on its own, the builder stops, and its
`run` ends `BLOCKED` with `reason: main_broken`, carrying `main_broken`. The milestone stays In Progress, because
nothing is wrong with it, but no builder can merge until the main branch passes, so that fix comes first. `next`
gives it to a planner for the modules whose commit broke it, or to you when the script couldn't tell which commit
that was.

### A milestone that stopped

A builder stops only when the milestone is finished or Blocked, or the main branch is broken. On `BLOCKED`, `reason`
says why the milestone is Blocked, and `next` says who steps in and gives the command, with the question for the
user when the step is theirs. [The done-when
reference](../../planner/references/done-when.md#statuses-and-their-stored-names) lists the reasons. When the
builder left a handoff, the `blocked` field names it. The `reason` is the builder's own reading, from inside one
session, so weigh it against what you can see across the build.

### After a review

A reviewer marks each problem it finds as a Must Fix, which fails the review, or a Suggestion, which doesn't.
`found` counts a failed review's findings, and `filled` lists the bookkeeping the script worked out from the
reviewer's verdicts. After a `PASS`, `next` is the module's next milestone.

After a `FAIL`, the script works out the next step from how many reviews the milestone has failed and how many of
those repeated an earlier finding. The `escalation` field names the step, and `next` is its command, with the
message for the builder or the task for the planner already written. As the counts rise, the same builder carries
on (`same_builder`), then a new builder session starts (`new_builder_session`), then a planner finds out why the
milestone keeps failing (`diagnosis`), and last, the milestone is Blocked for the user
(`too_many_failed_reviews`). A `run` carries the first two on by itself. The counts are the record of what has been
tried, so stepping around them repeats an attempt that already failed.
[The done-when reference](../../planner/references/done-when.md#when-a-review-fails) explains each step, and
`next --module <M> --worktree <path> --milestone <id>` works the step out again later. A diagnosis ends `PLANNED`
or `KEPT`, and either settles it, even a `PLANNED` that changed only the design.

The message for a builder leaves the findings to be read from the review file. Add nothing about which to fix,
because a builder handed a list fixes that list and nothing more.

A review can also print `INVALID`, when the reviewer did something a reviewer doesn't, such as editing code or
naming the wrong milestone. Nothing from it is saved, so run it again, on the other host if you can. It prints
`BLOCKED` with `reason: needs_access` when the reviewer couldn't reach the product. No failed review is counted for
it. Put its `ask` to the user, and run its `next`, the same review in a visible session, while they are at the
machine.

A design review's `verdict` is `DESIGN OK` or `DESIGN CHANGES`. After `DESIGN CHANGES`, a planner revises the design
from the Must Fix findings, and the design is reviewed again. After two in a row, the script approves the planner's
next revision without another. A finding that needs something on the `Human decides` list in the project settings is
the user's. No builder starts on a module until its design is approved.

## Where sessions run

A session the script starts in the background runs inside your process, so it gets your sandbox and your
operating-system permissions. If your host runs you without network access, or without permission to write to
`.git`, the builders can't fetch, commit or merge either, so lead from where those are allowed. A command that a
sandbox stopped from writing a file stops with `blocked_write` and names the path. Run it outside the sandbox, or
ask your host to run it with escalated permissions, rather than deleting lock files yourself.

Sessions run in the background by default. With `ORCHESTRATE_VISIBLE=1` on a Mac, Codex sessions run as threads in
the Codex app, and Claude sessions are also listed in Claude desktop's Code tab. Each result's `path` says which.

Every worktree keeps its own build outputs, so a long build can fill the disk. Clear those in worktrees nothing is
using. Evidence and the checks' logs and checkouts stay on this computer, outside git, until the user clears them,
as [clearing up](../references/cleanup.md) says. Anything outside the repository is the user's to clear.

An item whose `needs` type is `access` needs the user to approve a permission or a prompt, and one whose type is
`hardware` needs a device connected. A builder can finish either only in a visible session while the user is at
the machine, because an approval prompt can't appear in a background one. Start that builder with
`ORCHESTRATE_VISIBLE=1` at a time the user has said they are there. It asks for access as soon as it starts. On
macOS, a builder that records the screen or uses the camera also needs that permission granted to the app you run
in, and its first attempt fails until the user grants it.

## What you pass on

What you write for another agent, such as a `--message` or a planner's `--task`, is a prompt. Write it as the
`prompting-agents` skill describes, if it is installed. What it holds depends on who reads it.

A reviewer gets only what the work is judged against. The script writes the reviewer's prompt, and you add nothing
about how the work was made, because a reviewer told why the work is right tends to agree.

The script names a stopped builder's handoff in the next builder's prompt, so pass on only what the handoff
doesn't say.

You write a planner's task yourself, from what the user asked for. The design reviewer judges the design against
that task and the project brief, so where your task settles something the user's words left open, say so in the
task, and the planner lists it as an assumption the user can overturn. Don't present your own words as the user's.

- The planner's task goes in `--task`.
- A restriction the user gave only in conversation, such as "don't touch the schema", goes to the builder with
  `--human-rule`. The script saves it for the module and sends it on every turn, across sessions and milestones,
  until you pass `--clear-human-rules` because the user said so.
- One-off text, such as a fact the builder is missing, goes in `--message`.

## The user's decisions

Save only words the user really gave you, for the thing they were answering, because the script can't tell your
guess at their answer from their decision.

A decision of the user's is saved with `human <verb> --worktree <repo> --module <M> --milestone <id> --text "..."`,
with what they said in `--text`:

| Verb | What it saves |
|---|---|
| `feedback --item <item> --asked "..." --said "..."` | Their User Feedback on an item that needs it, where the builder and the reviewer read it. A reviewer can't count a `--message` as the user's words. Repeat `--item` when one reply covers several items. The milestone can then start again. |
| `accept` | A milestone is Done without a passing review. With `--milestone design`, the design is approved without one. |
| `rereview` | A milestone that is Done goes back for a new review. The old review is kept. |
| `reopen` | A milestone Blocked with `too_many_failed_reviews` gets another try. |
| `release` | A milestone another lead started, when that lead is gone, is taken out of In Progress so you can start it. An `IN_PROGRESS_ELSEWHERE` result names this command when it applies. |
| `scope` | The done-when file, as edited in the worktree, is the new scope. Use it only for an edit the user dictated exactly, such as a number: make the edit, show them the diff, and run it on their yes. |

When the user overturns a review with `accept` or `rereview`, and the project settings have a `Graded examples:`
line, the script adds the review to that file in the working folder, and the result names it in `graded_example`.
Later reviewers read it to learn how strict the user is. The `human` commands
refuse to run inside a session the script started, and while a `run`, `review` or `plan` is working on the same
module. In the second case, run it again once that run has stopped.

An answer that changes a plan, such as the user's reply to a planner's assumption, goes to a planner as a `plan`
task with their words, because only a planner changes plan files.

In a visible session, the user can type into a Codex thread to steer it. If they press Stop on a Codex thread, or
open a Claude session to work in it, that builder is `PAUSED` and the session is theirs until `run` hands it back.
When they ask you to stop everything, `pause --worktree <repo>` stops the running sessions cleanly, with every step
of a `run` or `plan` that is carrying on by itself, such as a planner revision, and `run` carries on later. To stop
one module's sessions, add `--module <M>`. Stopping processes by matching their names stops every builder that
matches, with its unsaved work. A builder's session survives a new version of the script, and starts again only when
the prompts it was given have changed.

The Codex app stops a thread only while its window is showing it. If it doesn't take a stop, the result has
`turn_not_stopped`, naming the thread, which may still be working. Ask the user to open it and press Stop, and wait
for that before you run the module again, because two sessions would otherwise change the same files.

## Telling the user

Your first message tells the user what they can ask for, which app you are running in and where the sessions run,
what you chose where their request left something open, and the `quota` forecast if Codex builders are running.

After that, write to the user when something needs them or changes what they expect, such as a date that slips. A
message for every result buries the one decision they need to see.

When the user asks how things are going, and when you stop, run `report --worktree <repo>` and send them its facts
with your own judgement on top. [The report](../references/report.md) says what to add and why.

When the user says they're going away, ask now about anything that will need them before they're back, because one
unanswered question holds back every module behind it.

If a result's `quota` field sets `warn`, the work left won't fit before the usage limit resets. Tell the user at
once, and keep going: slowing down is their decision.

## When to stop

Stop when the job is finished, or when nothing left can move without the user. Then stop `watch`, remove build
outputs and the worktrees whose work is merged, and send the user the report.
