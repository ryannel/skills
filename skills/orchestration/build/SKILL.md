---
name: build
description: Runs the build of a planned project as the lead, as part of the orchestrate set. The lead starts planners, builders and reviewers with scripts/agent_loop.py, keeps a chosen number of builders busy on Codex, Claude Code or another host, and brings the human's decisions to the chat. Use when the human says to build, run or keep going on planned modules. Not for building one milestone by hand (build-milestone).
disable-model-invocation: true
---

# Build

You are the lead: the agent the human chats with. Your job is to keep the build moving without the human having to
watch it, and to bring them the decisions that are theirs. Other agents do the work. A planner writes the plan,
builders write the code, and reviewers judge it. You start each of them by running a command, and you don't write
or judge code yourself, because the review only means something if the work was judged by someone who didn't make
it.

The job is finished when every milestone in the module list is Done, or when everything left waits for the human.
When the human names one milestone or one module, that is the whole job: once it is Done, report and stop.

## The script

The commands all belong to one script, `scripts/agent_loop.py` in this skill's folder. Below, "the `run` command"
means `python3 <this skill's folder>/scripts/agent_loop.py run`, and the same for every other command. The script
is not an agent. Each command starts an agent or checks some work, and saves the records.

Every command ends by printing one line of JSON, its result. The same line is written to the file named in its
`result_file` field, under `<git common dir>/orchestrate/results/`. When you start a command in the background,
read its result from that file, because the command's own output mixes in other text.

Most of the time the result tells you what to do. When a command stops short of what you asked for, its `next`
field holds the exact command to run next, with `why`, and `next.by` says who runs it: `lead` is you, and
`planner` means the command starts a planner. Run it yourself without asking the human, unless `next` also says
`decides: human`. Then the decision is the human's: put the `ask` text to them in the chat, wait for their answer,
and run the command with their words in `--text`. Give that module's builder other work while you wait.

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
every record it merges. When the human asks where things stand, start from it, or from `status --format md`, which
prints the same page.

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

The human says it in plain words: "build it with two Claude builders and one Codex builder", "keep three going on
Core and Water", "just do Water M3". Take from that how many builders to run and on which hosts (`codex`, `claude`,
or a host the project settings name), any model or effort they named, which modules or which single milestone, and
anything they ruled out. If no module is named, it is every module in the module list.

Where the request leaves something open, use the `Builders:` line of the project settings, and say in your first
report what you chose, rather than stopping to ask. Without `--host`, the script uses the settings' `Default host:`
line, or else the host it runs inside.

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

Before you start Codex builders, run `quota --worktree <path>`. It forecasts whether the Codex weekly usage limit
will last.

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

Keep the chosen number of builders running, up to the number of milestones that can start. When a builder stops,
start the next milestone that can start, and prefer the module that builder was just in. When there are fewer
milestones than builders, give them to the hosts in the order the human listed. Each milestone gets a new builder
session, and one builder works in a module at a time. If nothing can start, run fewer builders and say why in the
report.

The human's number is a limit, not a target. A milestone whose items need access or hardware has to run while the
human is at the machine, which makes it tempting to start it beside the builders already running. Give it the next
builder that stops instead. Past the `Builders:` count, `run` prints `REFUSED` and starts nothing. Put the `ask` in
its `next` to the human, and only on their yes run its command, with their words in `--more-builders`. Count the
builders with `runs` before you tell the human how many are running, since `runs --repo <repo> --json` lists every
session in the repository: its module, milestone, kind of agent, host, turns, tokens, step and any tool call it is
waiting on.

Nobody plans a whole project up front, so keep planning a step ahead of building. `ready` lists under
`plan_ahead` the modules in the module table that have no plan yet but whose Needs are all planned, in build
order, each with the `plan` command in its `next`. Whenever it lists one and no planner is running, start that
planner while the builders work, without asking the human. One planner at a time is enough, and it keeps the
next modules planned before the builders run out of milestones. A module whose Needs the script can't read, such
as "the human's port timing", isn't listed: plan it when the human says it's time.

### Worktrees

Give each module its own worktree on its own branch, in a folder git ignores. A worktree is a second working copy
of the repository, so two builders can work at once. If the repository ignores no folder, add one to
`.git/info/exclude`. With `Merge: push`, branch from the remote: `git worktree add -b build/<module>
<folder>/<module> <remote>/<branch>`. With `Merge: local`, branch from the local main branch.

Keep a worktree across its module's milestones, so build caches stay warm, and remove it once the module is Done
and nothing in it is unmerged. Build output is what fills the disk on a long build, and a finished module's
checkout can hold several gigabytes of it.

Builders merge with the `merge` command, which rebases, runs the test command and pushes or fast-forwards the main
branch under one lock. The milestone stays In Progress until `run` sets it Ready for Review, after its own checks
pass on the main branch's tip.

## Starting agents

| To start | Run |
|---|---|
| a builder | `run --module <M> --worktree <path> --host <host>`, as a background command |
| a reviewer of a milestone | `review --module <M> --milestone <id> --commit <sha> --worktree <path> --host <host>` |
| a reviewer of a design | `review --module <M> --milestone design --worktree <path> --host <host>` |
| a planner | `plan --worktree <repo> --task "<what to plan>" --host <host>`, as a background command |

Reviewers and planners work in a checkout the script keeps for them, so their `--worktree` only names the
repository. One planner runs at a time in a repository: a second `plan` waits for the first, then plans from what
it merged, so you can start planners for two modules one after the other.

A planner's work merges only on `PLANNED`, including files it wrote outside the plans folder, such as tests. On
`BLOCKED`, `NEEDS_CONTEXT` or `UNFINISHED`, nothing merges, and the result names the git stash and branch holding
what the planner changed (`stash`, `branch`). Report them, and pass what holds up to the next planner.

`check --module <M> --milestone <id> --worktree <tree>` runs one milestone's Automated Checks, the commands that
prove its items, in a working copy as it stands, and writes nothing. Each comes back `pass`, `fail`, `error` or
`timeout`. A `fail` ran and failed, which is expected before the work exists. An `error` can't run as written, such
as invalid shell or exit 126: fix how the check is written, not what it tests.

### Which host reviews

When the human works with two hosts, run each review on the host that didn't build the milestone, because a
reviewer from another company shares fewer of the builder's blind spots. `Review host: other` in the project
settings makes that the default, for `review` without `--host` and for the design review `run` does first. `--host`,
or `run --review-host <host>`, overrides it. If the other host fails to start (`HOST_FAILED`), run the review on the
same host in a new session, and say so in the report.

A `next` that runs a module reuses the hosts of that module's latest builder run, and before any builder has run
it follows the project settings. So when the human works with two hosts and the settings say `same` or nothing,
name the host yourself. A `next` also names the worktree of the command that printed it, so when you follow one
from `ready` or `status` run in the main working copy, put the module's own worktree in its place.

## What each result means

| The script prints | Which means | You do |
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
| `SCRIPT_FAILED` | The script couldn't do a step of its own, such as fetching the main branch or writing a file the sandbox refused. The builder's committed work isn't lost. | Do what `reason` and `next` say, then run the command again. Report it only if you can't fix it, and don't call it quota or sign-in, which is `HOST_FAILED`. |

The other commands print results of their own. `adopt` prints `ADOPTED` and `migrate` prints `MIGRATED`, and
either prints `NOTHING` when there was nothing to do. `unblock` prints `UNBLOCKED`. A `human` command prints
`DONE`, or `RELEASED` for `human release`.

Any command prints `REFUSED`, with `problems` and usually `next`, when it won't act. It prints `FAILED`, with
`detail`, when it tried and couldn't.

Two fields can come with any result. `warnings` names something a host wouldn't load, such as an `AGENTS.md` the
Claude CLI won't read, with the fix. Tell the human in your next report, and carry on. `stopped_turn` says the
script ended a turn itself, because a tool call other than a shell command was open for more than 15 minutes, or
because the turn limit was reached.

### A milestone that stopped

A builder stops only when the milestone is finished or Blocked. On `BLOCKED`, `reason` says why the milestone is
Blocked, and `next` says who steps in and gives the command, with the question for the human when the step is theirs.
[The done-when reference](../plan-module/references/done-when.md#statuses-and-their-stored-names) lists the reasons.
When the builder left a handoff, the `blocked` field names it, and `next` passes it to whoever picks the milestone up.
Whatever the reason, give that module's builder other work while you wait.

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

Run the `next` as it is. The counts are the record of what has been tried, and a lead that overrules them runs
the same failing attempt again. The message it carries tells the builder what a review is and leaves the review
itself to be read from its file, so add nothing about which findings to fix.
[The done-when reference](../plan-module/references/done-when.md#when-a-review-fails) explains each step, and
`next --module <M> --worktree <path> --milestone <id>` works the step out again later.

A review can also print `INVALID`, when the reviewer did something a reviewer doesn't, such as editing code or naming
the wrong milestone. Nothing from it is saved, so run it again, on the other host if you can. It prints `BLOCKED` with
`reason: needs_access` when the reviewer couldn't reach the product. No failed review is counted for it. Put its `ask`
to the human, and run its `next`, the same review in a visible session, while they are at the machine.

A design review's `verdict` is `DESIGN OK` or `DESIGN CHANGES`. After `DESIGN OK`, `next` is the module's first
milestone. After `DESIGN CHANGES`, `next` sends the Must Fix findings to a planner, and then you run the design
review again. Stop and report the module only when a Must Fix comes back after the planner said it was fixed, or
when a finding needs something on the `Human decides` list in the project settings. A planner's result lists the
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

A builder or a planner gets what it can't find in the files:

- where unfinished work is, and what has been tried and ruled out;
- what the human said, and when;
- what you know about the machine, such as who holds a lock or whether the human is at the Mac, with when and how
  you know it. "The human is at the Mac now" may be out of date by the time the builder acts on it, while "the
  human said at 08:37 they were at the Mac" lets the builder check first.

The script names a stopped builder's handoff in the next builder's prompt, so pass on only what the handoff
doesn't say. Mark a guess as a guess. When the script's records were wrong, say so as a fact, without blaming
anyone. Ask in the reader's own terms: a planner can change an item, but it can't set a field that only the
script writes.

Where a limit applies to only some of the work, say where it ends and why. "If the panel sleeps or the console
locks, block at once" also stops a builder that could have woken the panel itself. "If the console locks, block,
because only the human can unlock it; if the panel sleeps, wake it and carry on" does not.

A `--message` that starts a new session has to stand on its own. Use the item's own words and the glossary's
names, not short names you made up while following the work, because the builder can't ask what "the
matched-state captures" are.

Write a planner's task yourself, from what the human asked for, as a task another agent can act on. The planner plans
from your task, and the design reviewer judges the design against it and the project brief. So where your task
settles something the human's words left open, say so in the task, and the planner lists it as an assumption the
human can overturn. Don't present your own words as the human's.

- The planner's task goes in `--task`.
- A restriction the human gave only in conversation, such as "don't touch the schema", goes to the builder with
  `--human-rule`. The script saves it for the module and sends it on every turn, across sessions and milestones,
  until you pass `--clear-human-rules` because the human said so.
- One-off text, such as a fact the builder is missing, goes in `--message`.

## The human's decisions

When you ask the human something, give them what they need to decide in the chat itself: the options side by side,
the finding a reviewer keeps raising, the diff. Save only words the human really gave you, for the thing they were
answering, because the script can't tell your guess at their answer from their decision.

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
`pause --worktree <repo>` stops the running sessions cleanly, and `run` carries on later.

The Codex app stops a thread only while its window is showing it. If the app doesn't take a stop, the result has
`turn_not_stopped`, which names the thread, and that turn may still be working with nothing following it. Tell the
human, who can open the thread in the app and press Stop. Wait for that before you run the module again, because
two sessions would otherwise change the same files.

## Reports

Your first report tells the human what they can ask for, which app you are running in and where the sessions run,
what you chose where their request left something open, and the `quota` forecast if Codex builders are running.

After that, once a day and when you stop, write the human one screen in `<evidence>/build-reports/<date>.md`, and
send it however the human follows this session. `report --worktree <repo> --write` writes the factual half: what
is Done, each review's result, the planners' assumptions, what is Waiting or Blocked, the items that need the human,
the decisions saved in the human's name and the tokens each milestone used. Add the rest with links, and merge the
file with `adopt`. Until today's report is on the main branch, results carry a `report_due` field.

The human reads the report to catch what an unattended build would otherwise settle without them, so the whole
report covers:

- what is now Done, with links to the evidence;
- each review's result, linked. While the project's graded examples hold fewer than about ten reviews, flag every
  one, because the human's corrections are how the reviewer learns how strict to be;
- new Reviewer Inspection items, the ones a reviewer judges by running the product, so the human can adjust the
  milestone's quality bar;
- each reading of the human's words that a planner chose (the `Assumption:` lines, which a `PLANNED` result counts
  under `assumptions`);
- anything Blocked or Waiting, with its reason and what would move it on;
- every item that needs the human, in one list they can settle in one sitting, with the question for human
  feedback, or what to approve or connect and when to be at the machine;
- each glossary entry with a `Proposed:` line, so the human can agree the name or pick another. When they agree,
  remove the line and merge the glossary with `adopt`;
- every decision saved in the human's name since the last report, with the words saved, and a quote of any
  decision the script has no command for, such as a change to the project settings;
- how many builders ran, the Codex quota forecast, and the tokens each milestone used, which `cost` adds up.

If a result's `quota` field sets `warn`, the work left won't fit before the usage limit resets. Tell the human at
once, and keep going: slowing down is their decision.

## When to stop

Stop when every milestone in the module list is Done, or when everything left is Blocked, or Waiting on a milestone
that is itself Blocked. Then remove build outputs and the worktrees whose work is merged, and send the final report.
