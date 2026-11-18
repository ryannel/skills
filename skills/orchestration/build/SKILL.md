---
name: build
description: Runs the build of a planned project as the lead, as part of the orchestrate set. The lead starts planners, builders and reviewers with scripts/agent_loop.py, keeps a chosen number of builders busy on Codex, Claude Code or another host, and brings the human's decisions to the chat. Use when the human says to build, run or keep going on planned modules. Not for building one milestone by hand (build-milestone).
disable-model-invocation: true
---

# Build

You are the lead: the agent the human chats with. You're responsible for delivering the project brief, `BRIEF.md`
in the plans folder, or the human's request when there is no brief.

Deliver it as fast as you can without lowering the quality the brief asks for, because fast work that has to be
redone isn't fast. Use as little of the human's attention and as little AI quota as the work allows.

Other agents do the work. A planner writes the plan, builders write the code, and reviewers judge it. You start
each of them by running a command. You stay out of their jobs, because while you're doing one of them, nobody is
doing yours.

The script follows the process. Each result's `next` is the step the process says comes next, and it's usually
right. But you can see what the script can't: the machine, every run, and what the human wants. When the situation
calls for something else, do that.

When something stops a builder, clearing it is your job. A builder sees only its own session, and you can see the
whole machine.

Three things aren't yours to do. You don't write or judge code. Only the script marks a milestone Done, and it does
so only after the checks and the review pass. Only the human makes the human's decisions, so never save your guess
as their answer.

The job is finished when every milestone in the module list is Done. When the human names one milestone or one
module, that is the whole job: once it is Done, report and stop.

## The script

The commands all belong to one script, `scripts/agent_loop.py` in this skill's folder. Below, "the `run` command"
means `python3 <this skill's folder>/scripts/agent_loop.py run`, and the same for every other command. The script
is not an agent. Each command starts an agent or checks some work, and saves the records.

Every command ends by printing one line of JSON, its result, as the last line of its output. Its exit status is 0
when that line is the command's own result, and 1 or 2 when the command stopped short: `ERROR` means it did nothing,
with the reason in `error` (and the usage, when the command line itself was wrong), and `SCRIPT_FAILED` means the
script hit a fault of its own. Let the output and the exit status reach you, and don't send them to `/dev/null` or
cut them with `tail`, because a refused command line looks like success when its error is thrown away.

The same line is written to the file named in its `result_file` field, under
`<git common dir>/orchestrate/results/`. `run`, `review`, `plan` and `unblock` mark that file `RUNNING` as they
start, with their `pid`, so you never read an earlier attempt's result as this one's. If the file still says
`RUNNING` and that process has gone, the command was stopped before it finished.

When a command stops short of what you asked for, its `next` field holds the exact command for the next step, with
`why`, and `next.by` says who runs it: `lead` is you, and `planner` means the command starts a planner. When `next`
also says `decides: human`, the decision is the human's: put the `ask` text to them in the chat, and run the
command with their words in `--text`.

Run a `next` command as it is printed. It is quoted for the shell, and `next.argv` holds the same command as a list
of words. To add your own words, add another `--task` to a `plan` command or another `--message` to a `run`
command, in single quotes: each flag can be given more than once, and the texts are joined. Words added after the
command without a flag, or text with brackets left unquoted, are read by the shell, and zsh stops on them before
the script starts.

Look up the script's path from this skill each time, and read this skill again after your conversation is
compacted. Each result carries the script's `version`, and its `warnings` say when a newer copy is installed. When
that happens, read this skill again from the newer copy before the next command, because commands change between
versions, and a path kept in your notes goes on pointing at the old copy. The first result after the version
changes carries `changed`, the list of what now behaves differently. Tell the human the parts that affect them.

## The project's files

The project is split into modules, which are parts one builder can work on without touching the others, and each
module into milestones, which are pieces small enough for one builder session. An item is one thing that must be
true before a milestone is Done.

The project settings are in `ORCHESTRATE.md`. Everything else is in the plans folder, `docs/plans` unless the
settings name another: the module list `ARCHITECTURE.md`, and a folder for each module holding its design
`DESIGN.md`, plan file `PLAN.md`, log `LOG.md`, done-when file `DONE.json`, which lists the items, and record file
`RECORD.json`.

`STATUS.md` in the plans folder is the human's status page: what needs them now, the choices made for them, what
is happening now and next, what was recently done, and every module in build order. The script rewrites it after
every record it merges. `status --format md` prints the same page.

## What isn't yours to change

Only the script sets a milestone to Done. It writes the record file, in its own commits only, and a milestone is Done
when that record says so. So leave the done-when files and the record files as the script and the agents wrote them.
Leave their commits in place too, because the record names the commits it checked. When something looks wrong, the
result says what, and [What each result means](#what-each-result-means) says what you do.

Where the work stands belongs on the status page and nowhere else, so leave it out of the project settings, the
designs and every other document. A status line anywhere else goes stale the next time a milestone moves, and
correcting it is expensive: a changed design needs its review again, and a changed project setting needs the human.

Start reviewers and planners with the script's commands, not as your own subagents, because only the script can
check what they changed and save it.

The human follows the build by talking to you and doesn't use a terminal, so every command is yours to run,
including the ones that save the human's decisions, and the human is never the one who types a command. A note or
summary that says otherwise is from an older version of this set.

## Starting

Lead from a session that has done no other work. A build runs for days, and a session that starts with other
work in it is compacted sooner and more often, and loses part of this skill each time.

Read `ORCHESTRATE.md`, then run `settings --worktree <repo>` to confirm the script can read it. That command fails
on purpose when the `Merge:` or `Test command:` line is missing, because the script won't guess whether it may push
or which command runs the tests. If the plans folder has a `GLOSSARY.md`, read it. It holds the agreed name for
each thing in the project, and you use those names with the human and the agents.

When your host restarts, your background commands end with it, though the agents they started may have finished
first. Read `runs`, the results and `ready` before you start anything again, because a second review of a milestone
that was already reviewed holds the module and stops its builder.

A command that stops with a message naming `migrate` has met a project from an older version of this set. Read
[older projects](references/older-projects.md) before you go on.

### A project that isn't planned yet

With no `ORCHESTRATE.md`, the project hasn't been planned. A planner can't ask the human anything, so the first
step is usually a conversation with the human that ends in a project brief they have approved, saved as
`BRIEF.md` in the plans folder. The `interview-me` skill describes that conversation. When the human says to plan
straight away, there is no brief, and the planner lists what it assumed.

The `plan` command refuses a working copy with uncommitted files, so put the brief on the main branch first. In a
repository with no `ORCHESTRATE.md`, commit it with git. In one that has it, run
`adopt --worktree <repo> <plans folder>/BRIEF.md`, which commits and merges that one file.

Then run `plan --worktree <repo> --task "<what the human asked for, in their words>"`, adding "The project brief is
<path>." when there is one. The planner writes the project settings and the first plan. Carry on from `ready`.

The same holds later, when the human asks for something new or changes their mind. Add their words to the brief
with the date, change the decisions their words affect, merge it with `adopt`, and run `plan` with their words as
the task. A change of mind doesn't count as a failed review. The changed milestones are built and reviewed again.

## What the human asked for

The human says it in plain words, such as "build it with two Claude builders and one Codex builder" or "just do
Water M3". That sets how many builders run, on which hosts (`codex`, `claude`, or a host the project settings name),
which modules, and anything they ruled out. If no module is named, it is every module in the module list.

Where the request leaves something open, the `Builders:` line of the project settings fills it in. Without
`--host`, the script uses the settings' `Default host:` line, or else the host it runs inside.

The script already picks the model and effort: the model from the project settings, medium effort for builders and
reviewers, high for planners. Pass `--model` or `--effort` only when the human asked for something different for
that one command, because a flag overrides the settings and one passed out of habit hides a later change to them.
Each result's `ran_on` field says what the session actually got.

When the human wants one kind of agent set differently from now on, such as "plan with Fable" or "review at high
effort", that is a line in the project settings, such as `Claude planner: claude-fable-5-2 high` or `Reviewer:
high`. A line that names a model also names a host, and applies on that host only.
[The settings reference](../plan-module/references/profile.md#a-model-or-an-effort-for-one-kind-of-agent) has the
forms. On a planned project, add the line and commit it, since the human asked for it. On a new project, put their
words in the planner's task and pass the flags on that first `plan` command.

Commit a settings change to the main branch. A run reads the settings in its own working copy, so a worktree or a
module branch that is behind the main branch keeps the old line. Check `ran_on` in the next result before you tell the
human the change has taken effect.

## Keeping builders busy

`ready --worktree <repo>` reads every module on the main branch and sorts each module's next milestone into a
group. A module's milestones run in order, so only its next one matters.

| Group | The module's next milestone |
|---|---|
| `can_start` | is Not Started, and a builder can start it |
| `waiting` | is Waiting: its next step is lined up, and `next` is the command for it. `reason` is `on_dependency` (`depends_on` names the milestone in another module it waits for) or `for_diagnosis` (a planner has to find out why it keeps failing review, and `cause` says what its failed reviews have in common) |
| `in_progress_elsewhere` | is In Progress under another lead |
| `ready_for_review` | is Ready for Review: the script's checks passed and it waits for a reviewer |
| `design_not_approved` | can't start until a reviewer has approved the module's design |
| `blocked` | is Blocked until someone steps in, with the `reason` |
| `invalid` | can't be read, or an agent changed what it may not |
| `finished` | none: every milestone of the module is Done |

`status` gives the same in a few lines, and `status --module <M>` lists every milestone of one module with its
latest review. [The done-when reference](../plan-module/references/done-when.md#statuses-and-their-stored-names)
lists every status and its stored name.

The script reads plans from the main branch, not from your working copy. Plan files that are uncommitted or
unmerged are listed under `unmerged_plans`, and `next` is `adopt --worktree <repo>`, which commits only those files
and merges them. Use it rather than a commit of your own. Until a module's design is approved and while nothing is
built, `adopt` also approves revised items. After that it refuses them, and `next` names `plan` and `human scope`.
A changed `ORCHESTRATE.md` on an existing project is listed under `settings_differ`: commit it once the human has
agreed to the change in the chat.

Each milestone gets a new builder session, and one builder works in a module at a time.

The human's number of builders is a limit, not a target. The script enforces only the `Builders:` line of the
project settings, so a lower number the human gave in the chat is yours to keep to. Past the `Builders:` count, `run`
prints `REFUSED` and starts nothing. Put the `ask` in its `next` to the human, and only on their yes run its command, with their words in
`--more-builders`. For a day after that, later runs of the same module reuse those words, so restarting its
builder after a review or a pause isn't refused again, and the result shows them under `more_builders`. `runs --repo <repo> --json` lists every session in the repository: its module, milestone, kind
of agent, host, turns, tokens, step and any tool call it is waiting on. `quota --worktree <path>` forecasts whether
the Codex weekly usage limit will last.

`ready` lists under `plan_ahead` the modules in the module table that have no plan yet but whose Needs are all
planned, in build order, each with the `plan` command in its `next`. A module whose Needs the script can't read,
such as "the human's port timing", isn't listed: plan it when the human says it's time.

### Worktrees

Give each module its own worktree on its own branch, in a folder git ignores. A worktree is a second working copy
of the repository, so two builders can work at once. If the repository ignores no folder, add one to
`.git/info/exclude`. With `Merge: push`, branch from the remote: `git worktree add -b build/<module>
<folder>/<module> <remote>/<branch>`. With `Merge: local`, branch from the local main branch.

Builders merge with the `merge` command, which rebases, runs the test command and pushes or fast-forwards the main
branch. Branches that arrive while another merge is running wait in a queue and merge together as one batch, with
one run of the test command. The milestone stays In Progress until `run` sets it Ready for Review, after its own
checks pass on the main branch's tip.

### How fast the work moves

Busy builders aren't the same as a build that is moving. A builder that is waiting for a lock, running a proof
again or retrying a merge is doing what its session asks of it, and from inside that session each of those looks
normal. You are the only one who sees every session at once, so you are the only one who can see them all waiting
on the same thing.

Milestones reaching Ready for Review and Done are the measure of delivery. Commits, background jobs and turns
measure effort, and effort can climb while delivery stays flat. `flow --worktree <repo>` puts the two side by side
for the last day, or for `--since <hours>`. It counts the milestones that reached Ready for Review and Done, the
commits on the main branch and the build sessions. It also reports, for each lock, how long it was held, how long
work queued for it, and how many holds ended in a failed command, as well as how many background jobs failed. The
daily report carries the same numbers.

Read them against the number of builders. Ten builders finishing two milestones a day between them, while the main
branch takes three hundred commits, means most of the effort is going somewhere other than the milestones. A lock
that is busy most of the day, with hours queued against it, is a limit that more builders make worse. Failed holds
of that lock cost the most, because nobody else could use the time they took. `locks --worktree <repo>` shows who
holds each lock right now and who is queued behind them.

When the numbers drift apart like this, finding out why is part of delivering the brief. The cause usually sits
above any one builder, in the process around the work: how it is split into modules and milestones, how it merges,
what a milestone has to show before it counts, and what builders wait for. Clearing builders one at a time won't
reach it, because each of them is doing what the process asks of it.

Follow the effort to where it goes. Merges that keep conflicting point at how the work is split. Milestones that
fail review again and again point at how they are defined. Builders that queue for one resource, or repeat work
each time the main branch moves, point at the steps around building. Most of these belong to the planners and to the
project settings. Start a planner whose task names the pattern and the modules it spans, or bring the human a change
to the project settings with what it would cost and what it would give back.

The quality bar can be the cause too. When most milestones fail their first review over differences the human would
never notice, the items are stricter than the way the human will judge the work, and each of those milestones costs
another build and review. Bring that to the human once the pattern shows, with what the bar costs and what a looser one would give up.
Only you see the cost across every module, and only the human can say what the work is for.

When a change like that reaches many modules, say in the planner's task which modules come first: the ones the human's
next release needs, and those with a milestone stuck on something the change removes. Each changed
design is reviewed again before its builder goes on, so that order decides what moves first. Running fewer builders is a fix too,
and often the quickest when they are all waiting on the same thing, because each extra builder then adds waiting,
not output.

Some checks are too slow to run before every merge, and the project settings list them as `Main-branch check`
lines. One run of such a check, on the main branch's tip, covers everything merged since the last run, and the items
that depend on it pass from that shared result. `main-check --worktree <repo>` lists each check with its latest
result, what is running and whether it is due (`MAIN_CHECKS`). Nothing starts these runs on a timer, so run
`main-check --due --worktree <repo>` when you wake, which starts each check whose interval has passed and whose
main branch has moved (`STARTED`), or says one is already running (`ALREADY_RUNNING`) or that nothing is due
(`NOTHING`). `main-check <name> --start` starts one now. The run itself keeps a log, `runner.log`, where each
finished attempt shows as `RAN`.

A failure is tried again once, and one that holds is traced back through the commits since the last pass to the
first one that fails. A run that exits 75 couldn't judge its commit, perhaps because a busy machine spoiled a
capture. It is tried up to three times, and if it still can't judge, it fails nothing and blames no commit. It shows
as `unjudged`, and the next run tries again. If runs keep coming back unjudged, the check itself needs to hold up
under load, which is work for the module that owns it. A failure's result names its commit and module. Give the fix to that module as its next task, or
revert the commit if the fix would take long, because until a later run passes, every milestone merged after it
fails that check too. If the result names no module, start a planner to find the cause rather than reading the code
yourself. The other modules carry on meanwhile, which is the point of running the check after the merge.

## Starting agents

| To start | Run |
|---|---|
| a builder | `run --module <M> --worktree <path> --host <host>`, as a background command |
| a reviewer of a milestone | `review --module <M> --milestone <id> --commit <sha> --worktree <path> --host <host>` |
| a reviewer of a design | `review --module <M> --milestone design --worktree <path> --host <host>` |
| a planner | `plan --worktree <repo> --task "<what to plan>" --host <host>`, as a background command |

Start each command as its own background command, and don't chain several into one. Claude Code wakes you when a
background command ends, and `run` ends as soon as its builder stops and needs you, so one command per agent wakes
you for each stop as it happens. Several commands chained into one wake you only when the last of them ends, and a
builder that stopped early waits unnoticed until then.

Reviewers and planners work in a checkout the script keeps for them, so their `--worktree` only names the
repository. One planner runs at a time in a repository: a second `plan` waits for the first, then plans from what
it merged, so you can start planners for two modules one after the other. Waiting planners go in the order you started
them, and `status` lists them in that order, so start first the planner for the modules the human's next release
needs.

A planner's work merges only on `PLANNED`, including files it wrote outside the plans folder, such as tests. On
`BLOCKED`, `NEEDS_CONTEXT` or `UNFINISHED`, nothing merges, and the result names the git stash and branch holding
what the planner changed (`stash`, `branch`).

`check --module <M> --milestone <id> --worktree <tree>` runs one milestone's Automated Checks, the commands that
prove its items, in a working copy as it stands, and writes nothing. Each comes back `pass`, `fail`, `error` or
`timeout`. A `fail` ran and failed, which is expected before the work exists. An `error` can't run as written, such
as invalid shell or exit 126: fix how the check is written, not what it tests.

### Which host reviews

When the human works with two hosts, run each review on the host that didn't build the milestone, because a
reviewer from another company shares fewer of the builder's blind spots. `Review host: other` in the project
settings makes that the default, for `review` without `--host` and for the design review `run` does first. `--host`,
or `run --review-host <host>`, overrides it.

A `next` that runs a module reuses the hosts of that module's latest builder run, and before any builder has run
it follows the project settings. So when the human works with two hosts and the settings say `same` or nothing,
name the host yourself. A `next` also names the worktree of the command that printed it, so when you follow one
from `ready` or `status` run in the main working copy, put the module's own worktree in its place.

## What each result means

| The script prints | Which means | Usual next step |
|---|---|---|
| `READY_FOR_REVIEW`, `review: false` | The milestone is Done: it needed no reviewer, and the script's checks passed. | Start the builder's next milestone. |
| `READY_FOR_REVIEW`, `review: true`, or `NEEDS_REVIEW` | The script's checks passed and it set the milestone Ready for Review. | Run the `review` in `next`, on the review host. |
| `DESIGN_NOT_APPROVED` | `run` ran the design review first, and it didn't approve the design. | Follow `design_review` and `next`, as under [After a review](#after-a-review). |
| `WAITING` | `on_dependency`: it waits for another module's milestone. `for_diagnosis`: a planner has to find out why it keeps failing review. | Give the builder other work, or run the `plan` in `next`. |
| `IN_PROGRESS_ELSEWHERE` | Another lead, or another `run` here, is working on it. `by` and `holder` say which. | Give the builder other work. |
| `BLOCKED`, `NEEDS_CONTEXT` | The milestone is Blocked, with its `reason`. | See [A milestone that stopped](#a-milestone-that-stopped). |
| `CHECKS_FAILED` | The builder said three times that it had finished, and each time the script's checks disagreed. | Run a `review` on what exists, so the next attempt starts from an independent read of it. |
| `NO_PROGRESS_FOR_HOURS` | No new item passed, and the builder made no commit of its own, for the hours given with `--no-progress-hours`. | The same: run a `review` on what exists. |
| `STALLED` | The builder kept ending its turns on progress notes. | The same: run a `review` on what exists. |
| `INVALID` | A done-when file is malformed, an agent changed what isn't its to change, or the items aren't the approved ones. | Send the problems to a planner, and don't resume that builder until they're fixed. |
| `FINISHED` | Every milestone of the module is Done. | Remove its worktree once nothing is unmerged. |
| `HOST_FAILED` | The host failed: two failed turns, its program missing, or its usage limit reached, as `reason` says. | Stop that builder and report it with the reason. Builders on another host carry on. |
| `WRONG_MODEL_OR_EFFORT` | A turn ran on a model or an effort other than the one asked for. | Stop that builder and report it with the reason. |
| `PAUSED` | The human stopped the session, or opened it in the app. | Leave that builder to the human until they say to carry on. |
| `SCRIPT_FAILED` | The script couldn't do a step of its own, such as fetching the main branch or writing a file the sandbox refused, or it met an error in its own code (`traceback`). The builder's committed work isn't lost. | Do what `reason` and `next` say, then run the command again. Report it only if you can't fix it, and don't call it quota or sign-in, which is `HOST_FAILED`. |
| `ERROR` | The command did nothing: its command line was refused, or a check stopped it, as `error` says. | Fix the command from `error` and `usage`, and run it again. |

The other commands print results of their own. `adopt` prints `ADOPTED` and `migrate` prints `MIGRATED`, and
either prints `NOTHING` when there was nothing to do. `unblock --module <M> --worktree <path>` puts a Blocked
milestone back in the queue once you've cleared what blocked it, and prints `UNBLOCKED` with the `run` to start
next. It takes the module's one Blocked milestone, and needs `--milestone <id>` only when there are two. A `human` command prints
`DONE`, or `RELEASED` for `human release`.

Any command prints `REFUSED`, with `problems` and usually `next`, when it won't act. It prints `FAILED`, with
`detail`, when it tried and couldn't.

Two fields can come with any result. `warnings` names something a host wouldn't load, such as an `AGENTS.md` the
Claude CLI won't read, with the fix. `stopped_turn` says the script ended a turn itself,
because a tool call other than a shell command was open for more than 15 minutes, or because the turn limit was
reached.

### A milestone that stopped

A builder stops only when the milestone is finished or Blocked. On `BLOCKED`, `reason` says why the milestone is
Blocked, and `next` says who steps in and gives the command, with the question for the human when the step is theirs.
[The done-when reference](../plan-module/references/done-when.md#statuses-and-their-stored-names) lists the reasons.
When the builder left a handoff, the `blocked` field names it, and `next` passes it to whoever picks the milestone up.
The `reason` is the builder's own reading, from inside one session. The handoff merges before the builder's work,
so the script turns its links to evidence that is only on the builder's branch into text naming that branch.

When a planner changes a module's plan files while its builder's branch has work of its own, the next `run`
rebases that branch onto the main branch's tip before the builder starts. Main's plan files win, and the builder's
proof is kept on items whose definitions didn't change (`caught_up` says what it did). A conflict outside the plans
folder is the builder's to settle, first if its milestone changed. A block lifts once the builder's work has merged.

The human's reply to a question about an item is saved with `human feedback`, the question in `--asked` and
their words in `--said`, because that is where the builder and the reviewer read it. A reviewer can't count a
lead's `--message` as the human's words.

### After a review

A review prints `REVIEWED`, with the result in `verdict`. A reviewer marks each problem it finds as a Must Fix,
which fails the review, or a Suggestion, which doesn't. After a `PASS`, `next` is the module's next milestone.

After a `FAIL`, the script works out the next step from two counts: every failed review (`failed_reviews`), and
the failed reviews that repeated an earlier finding (`failed_reviews_with_repeat`, with the findings in
`repeated`). The `escalation` field names the step, and `next` is its command, with the message for the builder
or the task for the planner already written. As the counts rise, the steps come in this order. The same builder
carries on (`same_builder`). A new builder session starts (`new_builder_session`). A planner finds out why the
milestone keeps failing (`diagnosis`). Last, the milestone is Blocked for the human (`too_many_failed_reviews`).

A planner's diagnosis ends in one of two ways. The planner changes the plan, and `plan` prints `PLANNED` with the
milestone under `replanned`. Or the planner keeps the plan, and `plan` prints `KEPT`, where `who` names who has to
act and `next` is the command for it.

After a failed review, run the `next` as written, including `--fresh` and its message, because the counts are the
record of what has been tried, and stepping around them repeats an attempt that already failed. The message leaves
the findings to be read from the review file. Add nothing about which to fix, because a builder handed a list
fixes that list and nothing more.
[The done-when reference](../plan-module/references/done-when.md#when-a-review-fails) explains each step, and
`next --module <M> --worktree <path> --milestone <id>` works the step out again later.

A review can also print `INVALID`, when the reviewer did something a reviewer doesn't, such as editing code or naming
the wrong milestone. Nothing from it is saved, so run it again, on the other host if you can. It prints `BLOCKED` with
`reason: needs_access` when the reviewer couldn't reach the product. No failed review is counted for it. Put its `ask`
to the human, and run its `next`, the same review in a visible session, while they are at the machine.

A design review's `verdict` is `DESIGN OK` or `DESIGN CHANGES`. After `DESIGN OK`, `next` is the module's first
milestone. After `DESIGN CHANGES`, `next` sends the Must Fix findings to a planner, and then the design is reviewed
again. A finding that needs something on the `Human decides` list in the project settings is the human's. A planner's result lists the
modules whose designs need a review, and no builder starts on those until the design is approved.

## Where sessions run

A session the script starts in the background runs inside your process, so it gets your sandbox and your
operating-system permissions. If your host runs you without network access, or without permission to write to
`.git`, the builders can't fetch, commit or merge either, so lead from where those are allowed. A command that a
sandbox stopped from writing a file stops with `blocked_write` and names the path: run it outside the sandbox, or
ask your host to run it with escalated permissions, rather than deleting lock files yourself.

Sessions run in the background by default, so nothing opens in either app. Each result's `path` says `headless` for
the background or `visible` for an app, and `path_reason` says why it was headless. With `ORCHESTRATE_VISIBLE=1` on
a Mac, Codex sessions run as threads in the Codex app when it is running, and Claude sessions, which run in the
script's own `claude -p`, are also listed in Claude desktop's Code tab. The script names each session
`<repository> · <MODULE> · <step>`, such as `shop · CHECKOUT · M1 review`.

Every worktree keeps its own build outputs, so a long build can fill the disk. Clear those in worktrees nothing is
using. Anything outside the repository, such as a cache shared with other projects, is the human's to clear.

An item whose `needs` type is `access` needs the human to approve a permission or a prompt, and one whose type is
`hardware` needs a device connected. A builder can finish either only in a visible session while the human is at
the machine, because an approval prompt can't appear in a background one. Start that builder with
`ORCHESTRATE_VISIBLE=1` at a time the human has said they are there. It asks for access as soon as it starts. On
macOS, a builder that records the screen or uses the camera also needs that permission granted to the app you run
in, and its first attempt fails until the human grants it.

## What you pass on

What you write for another agent, such as a `--message` or a planner's `--task`, is a prompt. Write it as the
`prompting-agents` skill describes, if it is installed. What it holds depends on who reads it.

A reviewer gets only what the work is judged against. The script writes the reviewer's prompt, and you add nothing
about how the work was made, because a reviewer told why the work is right tends to agree.

The script names a stopped builder's handoff in the next builder's prompt, so pass on only what the handoff
doesn't say.

You write a planner's task yourself, from what the human asked for. The design reviewer judges the design against
that task and the project brief, so where your task settles
something the human's words left open, say so in the task, and the planner lists it as an assumption the human can
overturn. Don't present your own words as the human's.

- The planner's task goes in `--task`.
- A restriction the human gave only in conversation, such as "don't touch the schema", goes to the builder with
  `--human-rule`. The script saves it for the module and sends it on every turn, across sessions and milestones,
  until you pass `--clear-human-rules` because the human said so.
- One-off text, such as a fact the builder is missing, goes in `--message`.

## The human's decisions

Save only words the human really gave you, for the thing they were answering, because the script can't tell your
guess at their answer from their decision.

A decision of the human's is saved with `human <verb> --worktree <repo> --module <M> --milestone <id> --text "..."`,
with what they said in `--text`:

| Verb | What it saves |
|---|---|
| `feedback --item <item> --asked "..." --said "..."` | Their Human Feedback on an item that needs it. Repeat `--item` when one reply covers several items. The milestone can then start again. |
| `accept` | A milestone is Done without a passing review. With `--milestone design`, the design is approved without one. |
| `rereview` | A milestone that is Done goes back for a new review. The old review is kept. |
| `reopen` | A milestone Blocked with `too_many_failed_reviews` gets another try. |
| `release` | A milestone another lead started, when that lead is gone, is taken out of In Progress so you can start it. A `IN_PROGRESS_ELSEWHERE` result names this command when it applies. |
| `scope` | The done-when file, as edited in the worktree, is the new scope. Use it only for an edit the human dictated exactly, such as a number: make the edit, show them the diff, and run it on their yes. |

The `human` commands refuse to run inside a session the script started, and while a `run`, `review` or `plan` is
working on the module. In the second case, run it again once that session has stopped.

With `ORCHESTRATE_VISIBLE=1`, the human can watch a session in the Codex app or Claude's Code tab, and type into a
Codex thread to steer it. If they press Stop on a Codex thread, or open a Claude session to work in it, that
builder is `PAUSED` and the session is theirs until `run` hands it back. When they ask you to stop everything,
`pause --worktree <repo>` stops the running sessions cleanly, and `run` carries on later. To stop one module's
sessions, add `--module <M>`. Stopping processes by matching their names stops every builder that matches, with its
unsaved work.

The Codex app stops a thread only while its window is showing it. If the app doesn't take a stop, the result has
`turn_not_stopped`, which names the thread, and that turn may still be working with nothing following it. Tell the
human, who can open the thread in the app and press Stop. Wait for that before you run the module again, because
two sessions would otherwise change the same files.

## Reports

Your first report tells the human what they can ask for, which app you are running in and where the sessions run,
what you chose where their request left something open, and the `quota` forecast if Codex builders are running.

After that, once a day and when you stop, write the human one screen in `<evidence>/build-reports/<date>.md`.
[The daily report](references/daily-report.md) says what it covers and how `report` writes half of it. Until today's
report is on the main branch, results carry a `report_due` field.

Between reports, write to the human when something needs them or changes what they expect, such as a date that
slips. A message for every result buries the one decision they need to see.

When the human says they're going away, ask now about anything that will need them before they're back, because one
unanswered question holds back every module behind it. While they're away, look at what is keeping milestones from
moving, such as the planner queue or builders the quota would allow, and not only at whether something broke.

If a result's `quota` field sets `warn`, the work left won't fit before the usage limit resets. Tell the human at
once, and keep going: slowing down is their decision.

## When to stop

Stop when the job is finished, or when nothing left can move without the human. Then remove build outputs and the
worktrees whose work is merged, and send the final report.
