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
- [Questions from the agents](#questions-from-the-agents)
- [The user's decisions](#the-users-decisions)
- [Telling the user](#telling-the-user)
- [When to stop](#when-to-stop)

## What the user asked for

The user says what to build in plain words, such as "build it with two Claude builders" or "just do the checkout
module". That sets how many builders run, on which hosts (`codex`, `claude`, or a host the project settings name),
which modules, and anything they ruled out. If no module is named, it is every module in the module list. Where
the request leaves something open, the project settings fill it in.

The script already picks the model and effort from the project settings, or medium effort (high for planners) when
they name none. Pass `--model` or `--effort` only when the user asked for something different for
that one command, because a flag overrides the settings and one passed out of habit hides a later change to them.

When the user wants one kind of agent set differently from now on, such as "plan with Fable" or "review at high
effort", that is a line in the project settings, such as `Claude planner: claude-fable-5-2 high` or `Reviewer: high`.
[The settings reference](../../planner/references/profile.md#a-model-or-an-effort-for-one-kind-of-agent) has the
forms. Write such a line yourself, as [changing the settings](../references/settings.md) says.

## How the build runs

Give each module its own worktree on its own branch, in a folder git ignores. A worktree is a second working copy
of the repository, so two builders can work at once. If the repository ignores no folder, add one to
`.git/info/exclude`. With `Merge: push`, branch from the remote:
`git worktree add -b build/<module> <folder>/<module> <remote>/<branch>`. With `Merge: local`, branch from the local
main branch. Builders merge from there with the `merge` command.

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
check-in or sign wakes you. It counts free builder slots against the `Builders:` line, so when the user changes their
number, change that line as [changing the settings](../references/settings.md) says.

If your host doesn't wake you when a background command ends, run `watch --runs` as the command you wait on. It also
ends when a `run`, `review` or `plan` of the repository ends, and prints `RUN_ENDED` with their results.

Every `watch` result says what woke you in `woke_for`, and sums up the build for a lead with no other context: what
moved, what isn't moving and why, milestones going back and forth to review, builder slots, planners and the disk.

### When you're woken

Whether a run stopped or `watch` woke you, the question is the same: is the work moving towards the brief as fast as
it could, and if not, what would move it? You have the mandate to act on the answer. The usual moves are:

- Start a builder on ready work, up to the user's number of builders, which is a limit, not a target. Each
  milestone gets a new builder session, and one builder works in a module at a time. `runs --repo <repo> --json`
  lists every session in the repository, and `quota --worktree <path>` forecasts whether the Codex weekly usage
  limit will last.
- Message a builder that is heading the wrong way, by stopping its run with `pause --module <M>` and starting it
  again with `--message`.
- Start a planner, or bring the user a change to the project settings, when the problem sits above any one
  builder, as under [Reading delivery](#reading-delivery).
- Change the order of the work, so that what the user's next release needs starts first, whether that is a
  module or a planner.
- Ask the user, when the answer is theirs.

Doing nothing is right too, when everything is moving. When the project settings have `Shared resources`,
`Exclusive resources` or `Main-branch check` lines, read [locks and main-branch checks](../references/locks.md)
once in the session, because those shape what builders wait for.

### Reading delivery

Busy builders aren't the same as a build that is moving. A builder waiting for a lock, running a proof again or
retrying a merge looks normal from inside its session. Only you see every session at once, so only you can see them
all waiting on the same thing.

Milestones reaching Ready for Review and Done are the measure of delivery. Commits, background jobs and turns measure
effort, and effort can climb while delivery stays flat. `flow --worktree <repo>` puts the two side by side for the
last day, or for `--since <hours>`. Read them against the number of builders. Ten builders finishing two milestones a
day between them, while the main branch takes three hundred commits, means most of the effort is going somewhere other
than the milestones. For the longer view, by kind of agent, model, error and version of the script, read the [delivery
history](../references/delivery-history.md).

When the two drift apart, the cause usually sits above any one builder, in how the work is split, how it merges,
what a milestone must show, or what builders wait for. Each builder is doing what the process asks, so clearing them
one at a time won't reach it. Follow the effort. Merges that keep conflicting point at the split. Milestones that
fail review again and again point at their items, and when most fail over differences the user would never notice,
the quality bar is stricter than the user's own. Builders queuing for one resource point at the steps around
building.

Once the pattern shows, start a planner whose task names it and the modules it reaches, with those stuck on it
first, because each changed design is reviewed again. Or bring the user a change to the settings or the quality bar,
with its cost and what it gives back. Running fewer builders is often the quickest fix when they all wait on the
same thing, because each extra builder then adds waiting, not output.

## What can start

`ready --worktree <repo>` gives the detail behind the `watch` summary. It reads every module on the main branch and
sorts each module's next milestone into a group, since a module's milestones run in order.

| Group | The module's next milestone |
|---|---|
| `can_start` | is Not Started, and a builder can start it |
| `waiting` | is Waiting, with its next step in `next`. `reason` is `on_dependency`, for the milestones `depends_on` names; `for_diagnosis`, for a planner to find out why it keeps failing review, with what the failures share in `cause`; or `for_planning`, when the plan names milestones (`later`) that have no items yet |
| `in_progress_elsewhere` | is In Progress under another lead |
| `ready_for_review` | is Ready for Review: the script's checks passed and it waits for a reviewer |
| `design_not_approved` | can't start until a reviewer has approved the module's design |
| `blocked` | is Blocked until someone steps in, with the `reason` |
| `invalid` | can't be read, or an agent changed what it may not |
| `finished` | none: every milestone of the module is Done |

`status --module <M>` lists every milestone of one module with its
latest review. [The done-when reference](../../planner/references/done-when.md#statuses-and-their-stored-names)
lists every status and its stored name.

`ready` also lists under `plan_ahead` each module with one planned milestone left whose plan names more, and the
modules in the module table that have no plan yet but whose Needs are all planned, in build order, each with the
`plan` command in its `next`. `watch` wakes you for the first kind, so a planner writes the next milestones while the
last one builds, and the builder doesn't wait for planning. A module whose Needs the script can't read,
such as one that waits on a decision of the user's, isn't listed: plan it when the user says it's time.

The script reads plans from the main branch, not from your working copy. Plan files that are uncommitted or
unmerged are listed under `unmerged_plans`, and `next` is `adopt --worktree <repo>`, which commits only those files
and merges them. Use it rather than a commit of your own. Until a module's design is approved and while nothing is
built, `adopt` also approves revised items. After that it refuses them, and `next` names `plan` and `human scope`.

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
repository. A planner given `--module <M>` may change only that module's folder in the plans folder, the project
files beside the module folders and files outside the plans folder, so planners of different modules run side by
side. The script's own `next` commands add `--module` to tasks about one module. Give it to a task of yours that
reaches only one module, such as a change to one module's quality bar. A planner without it may change any module,
so it waits for the planners running, and they wait for it. A planner that finds it needs another module's files
stops, and its `next` gives the task to a planner without `--module`. Waiting planners go in the order you started
them.

A planner's work merges only on `PLANNED`, including files it wrote outside the plans folder, such as tests. On any
other ending nothing merges, and `stash` and `branch` hold what the planner changed.

When the user works with two hosts, run each review on the host that didn't build the milestone, because a
reviewer from another company shares fewer of the builder's blind spots. `Review host: other` in the project
settings makes that the default, for `review` without `--host` and for the reviews `run` starts. `--host`, or
`run --review-host <host>`, overrides it.

## What each result means

`run` and `plan` carry routine results on by themselves, so you meet a result mostly where a chain stopped. For each,
run `next` unless you see a reason not to. These are the ones that need more from you:

| The script prints | What needs you |
|---|---|
| `REVIEWED`, `DESIGN_NOT_APPROVED` | See [After a review](#after-a-review). |
| `WAITING`, `IN_PROGRESS_ELSEWHERE` | Start a builder on other ready work meanwhile. |
| `BLOCKED`, `NEEDS_CONTEXT` | See [A milestone that stopped](#a-milestone-that-stopped). |
| `CHECKS_FAILED`, `NO_PROGRESS_FOR_HOURS`, `STALLED` | The builder isn't getting anywhere. `next` starts it again in a new session with the script's reasons, or starts a planner first when the builder said an item can't be met. |
| `INVALID` | Send the problems to a planner, and don't resume that builder until they're fixed. When a planner changed the items mid-build, `next` is `run` again. |
| `HOST_FAILED` | Run `next` once the host is back, or its `alternative` on the other host. Tell the user when `reason` is a usage limit, because waiting or moving hosts is their call. Builders on another host carry on. |
| `WRONG_MODEL_OR_EFFORT` | Tell the user what ran instead, from `mismatches`, and check the settings line before you run it again. |
| `PAUSED` | Leave a builder the user stopped to them until they say to carry on. |
| `FINISHED` | Remove its worktree once nothing is unmerged. |
| `SCRIPT_FAILED` | Do what `reason` and `next` say. It isn't quota or sign-in, which is `HOST_FAILED`. |

The rest report a command's own result, and `next` says what follows: `NEEDS_REVIEW` (the checks passed and a
review is owed), `PLAN_NOT_MERGED` and `UNFINISHED` (a planner's files didn't merge, or its turn ended without an
ending, so nothing changed), `ADOPTED`, `RELEASED` for `human release`, and `UNBLOCKED`. Any command prints
`REFUSED`, with `problems`, when it won't act, and changes nothing.

`unblock --module <M> --worktree <path>` puts a Blocked milestone back in the queue once you've cleared what blocked
it. `stopped_turn` says the script ended a turn itself, because a non-shell tool call stayed open for 15 minutes or
the turn limit was reached. `warnings` names something a host wouldn't load, with the fix.

A `BLOCKED` with `reason: main_broken` leaves the milestone In Progress. No builder can merge until the main branch
passes, so run its `next` first. A `PLAN_NOT_MERGED` with `main_broken` means the plan finished but couldn't be
tested, because the main branch fails its test command without it. It is kept on a branch, so once the main branch
passes, run its `merge_kept_later` command, which merges it without a new planner turn.

### A milestone that stopped

A builder stops only when the milestone is finished or Blocked, or the main branch is broken. On `BLOCKED`, `reason`
says why the milestone is Blocked, and `next` says who steps in and gives the command, with the question for the
user when the step is theirs. [The done-when
reference](../../planner/references/done-when.md#statuses-and-their-stored-names) lists the reasons. When the
builder left a handoff, the `blocked` field names it. The `reason` is the builder's own reading, from inside one
session, so weigh it against what you can see across the build. When it is a question, [questions from the
agents](#questions-from-the-agents) says how to get it answered.

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
naming the wrong milestone. Nothing from it is saved, so run it again, on the other host if you can. A review can
also stop with `needs_access`, which [where sessions run](#where-sessions-run) covers.

A design review's `verdict` is `DESIGN OK` or `DESIGN CHANGES`. After `DESIGN CHANGES`, a planner revises the design
from the Must Fix findings, and the design is reviewed again. After two in a row, the script approves the planner's
next revision without another. A finding that needs something on the `Human decides` list in the project settings is
the user's. No builder starts on a module until its design is approved.

## Where sessions run

A session the script starts in the background runs inside your process, so it gets your sandbox and your
operating-system permissions. If your host runs you without network access, or without permission to write to
`.git`, the builders can't fetch, commit or merge either, so lead from where those are allowed. A command that a
sandbox stopped from writing a file stops with `blocked_write` and names the path. Run it outside the sandbox, or
ask your host to run it with escalated permissions.

A design that says a module drives a browser throughout needs a host that can start one for every builder and
reviewer. On Codex, each browser runs only when the agent's request to run it outside the `workspace-write` sandbox is
granted, so give that module Claude builders and reviewers, or ask the user whether to set `Codex sandbox:
danger-full-access`, which only they choose.

Sessions run in the background by default. With `ORCHESTRATE_VISIBLE=1` on a Mac, Codex sessions run as threads in
the Codex app, and Claude sessions are also listed in Claude desktop's Code tab. Each result's `path` says which.

Every worktree keeps its own build outputs, so a long build can fill the disk. Clear those in worktrees nothing is
using. Evidence and the checks' logs and checkouts stay on this computer, outside git, until the user clears them,
as [clearing up](../references/cleanup.md) says. Anything outside the repository is the user's to clear.

An item that needs the user to approve access, or a connected device, can only finish in a visible session while
they are at the machine, because an approval prompt can't appear in a background one. A builder or reviewer that
reaches one stops `BLOCKED` with `needs_access` or `needs_hardware`, and no failed review is counted. Put its `ask` to
the user, and run its `next` (the same command with `ORCHESTRATE_VISIBLE=1`) when they say they're there. On macOS,
a first screen recording or camera use fails until they grant the permission to the app you run in.

### Stopping sessions

In a visible session, the user can type into a Codex thread to steer it. If they press Stop on a Codex thread, or
open a Claude session to work in it, that builder is `PAUSED` and the session is theirs until `run` hands it back.
When they ask you to stop everything, `pause --worktree <repo>` stops the running sessions cleanly, with every step
of a `run` or `plan` that is carrying on by itself, such as a planner revision, and `run` carries on later. To stop
one module's sessions, add `--module <M>`. Stopping processes by matching their names stops every builder that
matches, with its unsaved work.

The Codex app stops a thread only while its window is showing it. If it doesn't take a stop, the result has
`turn_not_stopped`, naming the thread, which may still be working. Ask the user to open it and press Stop, and wait
for that before you run the module again, because two sessions would otherwise change the same files.

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

- The planner's task goes in `--task`. A planner you start yourself takes `--kind change` when it changes existing
  plans: something new the user asked for, their answer to an assumption, a changed name, an interface change a
  builder proposed, or a fix to how the work is split. Without `--kind`, it plans a new project or the next module.
  The script's own `plan` commands name their kind already.
- A restriction the user gave only in conversation, such as "don't touch the schema", goes to the builder with
  `--human-rule`. The script saves it for the module and sends it on every turn, across sessions and milestones,
  until you pass `--clear-human-rules` because the user said so.
- One-off text, such as a fact the builder is missing, goes in `--message`.

## Questions from the agents

Every question an agent can't answer comes to you. A builder ends its turn with `NEEDS_CONTEXT:` and the question,
and a planner does the same, or ends with `BLOCKED:`. A question is the right ending when the answer would change
what gets built, and your job is to get it answered quickly, with as little of the user's attention
as you can.

Answer it at the first of these that can:

1. You, from what you can see: the brief, the design, the glossary, another module's work, or what the user has
   already told you. Resume the builder with the answer in `run --message`.
2. A planner, for anything about the plan, such as a gap in the design, an item that can't be met as written, or
   something another module should provide. It works from the whole plan, on a stronger model than a builder.
   For a builder's question, `next` gives the `plan` command as its alternative.
3. The user, for what only they can decide: what they want, a matter of taste, access, money, or something outside
   the project.

The user is often away, for hours when they're asleep or travelling, and each question costs their attention. So:

- Keep the rest of the build moving while a question waits. A Blocked milestone holds back only the milestones that
  depend on it, so start builders on other ready work.
- When an answer has a sensible default that would be cheap to change later, don't wait for the user. Give the
  question to a planner to plan with that default as an `Assumption:` line, which the user sees in the report and
  can overturn in a line. Wait for the user only where a wrong guess would mean redoing a lot of work.
- Gather the questions and ask them together, in one message, rather than one message each. Ask straight away only
  when nothing else can move. When the user says they're going away, gather the questions now.
- Bring the glossary's `Proposed:` names with the next questions you gather, and settle them as
  [before the first build](3-before-first-build.md) does.
- Bring a later plan's `assumptions`, and any reference it chose for a quality bar, the same way, because the user
  can overturn them as they could the first plan's.
- Ask each one the way the [interview](1-interview.md#map-the-dialogue) does: the question, what each choice would
  commit the project to, and what you recommend, so the user can answer in a word.

The answer goes back where the question came from: to the builder in `run --message`, to a planner as a `plan`
task, or, for User Feedback and approvals, through `human feedback`, as the next section says. When the user's answer
goes against a decision in the brief, add it to the brief with the date and merge it with `adopt` first, because
planners and design reviewers hold the plan to the brief.

## The user's decisions

A decision of the user's is saved with `human <verb> --worktree <repo> --module <M> --milestone <id> --text "..."`,
with what they said in `--text`:

| Verb | What it saves |
|---|---|
| `feedback --item <item> --asked "..." --said "..."` | Their User Feedback on an item that needs it, or their answer to an approval a builder stopped for, with no `--item`, where the builder and the reviewer read it. A reviewer can't count a `--message` as the user's words. Repeat `--item` when one reply covers several items. The milestone can then start again. |
| `accept` | A milestone is Done without a passing review. With `--milestone design`, the design is approved without one. |
| `rereview` | A milestone that is Done goes back for a new review. The old review is kept. |
| `reopen` | A milestone Blocked with `too_many_failed_reviews` gets another try. |
| `release` | A milestone another lead started, when that lead is gone, is taken out of In Progress so you can start it. An `IN_PROGRESS_ELSEWHERE` result names this command when it applies. |
| `scope` | The done-when file, as edited in the worktree, is the new scope. Use it only for an edit the user dictated exactly, such as a number: make the edit, show them the diff, and run it on their yes. |

A milestone with `"alone": true` in its done-when file, such as precise timings, is built with no other agent
working. Its run waits for the turns under way to end, and holds back new builder turns, reviews, planners and
main-branch check runs until it ends, so `runs` shows them waiting for a quiet window. Start it when the other
modules can spare the time. Gather the user's sittings at a device the same way, across modules, so they come once.
A sitting is a visible run, which takes a builder slot like any other, so when every slot is taken, `pause` a builder
whose work can wait rather than asking the user for one more.

When the user picks one of a set of options, the planner usually left the milestones after the pick without items.
Once the pick is Done, `ready` lists under `plan_ahead` a planner task to write them, and a `plan --kind change` task
for each module whose milestones not started yet depend on the pick and were written before it, to rewrite their
quality bars against the chosen option. When the user turns every option down, give their words to a planner as a
`plan --kind change` task, because the reference may be the problem rather than the builder.

When the user overturns a review with `accept` or `rereview`, and the project settings have a `Graded examples:`
line, the script adds the review to that file in the working folder, and the result names it in `graded_example`.
Later reviewers read it to learn how strict the user is. The `human` commands refuse to run while a `run`, `review`
or `plan` is working on the same module, so run it again once that run has stopped.

## Telling the user

Your first message tells the user what they can ask for, which app you are running in and where the sessions run,
what you chose where their request left something open, and the `quota` forecast if Codex builders are running.

After that, write to the user when something needs them or changes what they expect, such as a date that slips. A
message for every result buries the one decision they need to see.

When the user asks how things are going, and when you stop, run `report --worktree <repo>` and send them its facts
with your own judgement on top. [The report](../references/report.md) says what to add and why.

If a result's `quota` field sets `warn`, the work left won't fit before the usage limit resets. Tell the user at
once, and keep going: slowing down is their decision.

## When to stop

Stop when the job is finished, or when nothing left can move without the user. Then stop `watch`, remove build
outputs and the worktrees whose work is merged, and send the user the report.
