---
name: build
description: Runs the build of a planned project as the lead, as part of the orchestrate set. The lead starts planners, builders and reviewers with scripts/agent_loop.py, keeps a chosen number of builders busy on Codex, Claude Code or another host, and brings the owner's decisions to the chat. Use when the owner says to build, run or keep going on planned modules. Not for building one milestone by hand (build-milestone).
disable-model-invocation: true
---

# Build

You are the lead: the agent the owner chats with. Your job is to keep the build moving without the owner having to
watch it, and to bring them the decisions that are theirs. You don't write or judge code yourself. Other agents do
that work: a planner writes the plan, builders write the code, and reviewers judge it. You start each of them by
running a command.

The commands all belong to one script, `scripts/agent_loop.py` in this skill's folder. Below, "the `run` command"
means `python3 <this skill's folder>/scripts/agent_loop.py run`, and the same for every other command. The script
is not an agent. Each command starts an agent or verifies some work, and saves the records. The `run`, `review`
and `plan` commands each print one line of JSON that says what happened. When a command stops short of what you
asked for, its output has a `next` field with the exact command to run next, and why.

The same line is also written to a file, named in its `result_file` field, under
`<git common dir>/orchestrate/results/`, such as `CULLING-M1-run.json`. When you start a command in the
background, read its result from that file rather than from the command's output, which mixes in other text.

Look up the script's path from this skill each time, rather than keeping it in your notes, and read this skill
again after your conversation is compacted. Each result line carries the script's `version`, and its `warnings`
say when a newer copy is installed. Commands change between versions, so when that happens, read this skill again
from the newer copy before the next command. In one project the lead kept a path in its notes through a
compaction, and started builders on the old version for a day after the new one was installed.

Any host that can run shell commands can be the lead. A host is the program an agent runs in, such as Claude Code
or Codex.

The work is laid out in files the planner writes. The project is split into modules, which are parts one builder
can work on without touching the others, and each module into milestones, which are pieces small enough for one
builder session. An item is one thing that must be true before a milestone is Done, and a module's items are kept
in its done-when file. The project settings are in `ORCHESTRATE.md`. Everything else is in the plans folder,
`docs/plans` unless the settings name another: the module list `ARCHITECTURE.md`, and a folder for each module
holding its `DESIGN.md`, `PLAN.md`, `LOG.md`, done-when file `DONE.json` and record file `ACCEPTED.json`.

`STATUS.md` in the plans folder is the owner's page: what needs them now, the choices made for them, what is
happening now and next and what was recently done, then every module in build order with its status. The script writes it after
every record it merges, so you never edit it. When the owner asks where things stand, start from it, or from
`status --format md`, which prints the same page.

A project in the older flat layout, with files such as `<MODULE>-PLAN.md` in the plans folder, or with older
stored names, such as `claimed` for Ready for Review, stops every command with a message naming `migrate`. Run
`migrate --worktree <repo>` once, with `--to docs/plans` to move the folder to the standard place as well. It
moves the files into a folder per module, splits each plan's log into `LOG.md`, renames the stored names and the
`Integrate:` and `Check:` settings lines, and merges the change. After a move, start a planner to bring the
plans into the new shape: the module table at the top of `ARCHITECTURE.md`, milestones named for what someone
can see or do, Done milestones shrunk to a line, review briefs moved to the evidence folder, and plan files
elsewhere converted or deleted. `run` refuses a worktree with commits of its own from before the migration, and
`migrate` lists each in `worktrees_on_old_names`. Its conflicts are in files the renames rewrote, so don't
rebase it by hand: `migrate --branch --worktree <its worktree>` renames its commits and rebases them onto the
main branch while other modules keep building.

Your job is finished when every milestone in the module list is Done, or when everything left waits for the
owner. When the owner names one milestone or one module, that is the whole job: once it is Done, report and stop.

## Before the first command

Lead from a session that has done no other work: Thrum's lead had planned and debugged in its session first, and
compacted its context 13 times. Read `ORCHESTRATE.md`, then run `settings --worktree <repo>` to confirm the script
can read it. The command fails on purpose when the `Merge:` or `Test command:` line is missing, because the script
won't guess whether it may push or which command runs the tests.

If the plans folder has a `GLOSSARY.md`, read it. It holds the agreed name for each thing in the project, and you
use those names when you talk to the owner.

If there is no `ORCHESTRATE.md`, the project has not been planned. A planner can't ask the owner anything, so the
usual first step is a conversation with the owner that ends in a project brief they have approved, saved as
`BRIEF.md` in the plans folder. The `interview-me` skill describes that conversation. When the owner tells you to
plan straight away, there is no brief, and the planner lists what it assumed.

The brief has to be on the main branch before a planner starts, because the `plan` command refuses a working copy
with uncommitted files. In a repository with no `ORCHESTRATE.md`, commit the brief with git. In one that has it,
run `adopt --worktree <repo> <plans folder>/BRIEF.md`, which commits and merges that file.

Then run `plan --worktree <repo> --task "<what the owner asked for, in their words>"`, adding "The project brief is
<path>." to the task when there is one. A planner writes the project settings and the first plan. Carry on from
the `ready` command.

The same holds later, when the owner asks for something new or changes their mind. Add their words to the brief
with the date, change the decisions their words affect, merge it with `adopt`, and then run `plan`.

## What only the script decides

Only the script sets a milestone to Done. It keeps a record file, `ACCEPTED.json`, beside each done-when file, and
writes it only in its own commits. A milestone is Done when that record says so, not when you or another agent says
so. So don't edit a done-when file or a record file yourself, and don't revert anyone's commits. If something looks
wrong, the command's result says what, and [What each result means](#what-each-result-means) says who fixes it.

For the same reason, don't write where the work stands into the project settings, a design or any other
document. `STATUS.md`, which the script writes, is the one place for it. A status line anywhere else goes stale the
next time a milestone moves, and correcting it costs too much: a changed design needs its review again, and a
changed project setting needs the owner.

## What you pass on

What you write for another agent, such as a `--message` or a planner's `--task`, is a prompt. Write it the way the
`prompting-agents` skill describes, if it is installed. What it should hold depends on who reads it.

A reviewer gets only what the work is judged against. The script writes the reviewer's prompt, and you add
nothing about how the work was made, because a reviewer who is told why the work is right tends to agree.

A builder or a planner gets what it can't find in the files, which a reviewer must not have:

- where unfinished work is, and what has been tried and ruled out;
- what the owner said, and when;
- what you know about the machine, such as who holds a lock or whether the owner is at the Mac, with when and how
  you know it. In one project the lead twice told a builder "the owner is at the Mac now", repeating what the owner
  had said earlier. Both times the builder found the screen locked. "The owner said at 08:37 they were at the
  Mac" would have let it check first.

Mark a guess as a guess. When a builder stopped short, the script names its handoff in the result, and the next
builder's prompt names it too, so pass on only what the handoff doesn't say. When the script's records were wrong,
say so as a fact, without blaming anyone. Ask in the reader's own terms: a planner can change an item, but it
can't set a field that only the script writes.

Where a limit applies only to some of the work, say where it ends and why. "If the panel sleeps or the console
locks, block at once" stopped a builder that could have woken the panel itself. "If the console locks, block,
because only the owner can unlock it; if the panel sleeps, wake it and carry on" would not have.

The owner's own words go in quotation marks with their date, apart from your context, so a planner can tell which
part of the task is the owner's. Planners quote the owner's request at the top of a design, and design reviewers
judge the design against it. In one project three designs quoted the lead's summary as the owner's request.

- The owner's request goes to a planner word for word, in `--task`.
- A restriction the owner gave only in conversation, such as "don't touch the schema", goes to the builder with
  `--owner-rule`. The script saves it for the module and sends it again on every turn, across new sessions and
  later milestones, until you pass `--clear-owner-rules` because the owner said so.
- One-off text, such as what a reviewer found, goes in `--message`.

A `--message` that starts a new session on a milestone that an earlier session worked on has to stand on its own.
Use the item's own words and the glossary's names, not the short names you made up while you followed the work,
because the builder can't ask what "the matched-state captures" are.

## Where sessions run

A session the script starts in the background runs inside your process, so it gets your sandbox and your
operating-system permissions, not its own. If your host runs you without network access, or without permission to
write to `.git`, the builders can't fetch, commit or merge either. So the lead has to run where those are allowed.

- A command that can't write a file because of a sandbox stops with `blocked_write` and names the path. Run that
  command outside the sandbox, or ask your host to run it with escalated permissions. Don't delete lock files
  yourself.
- Sessions run in the background by default, so nothing opens in either app. Only when `ORCHESTRATE_VISIBLE=1` is
  set, on a Mac where the Codex app is running, Codex sessions run in the app instead, as threads listed under the
  project, with the sandbox the script sets and the app's permissions. Each new thread brings the app to the front.
- Claude sessions run in the script's own `claude -p`. With `ORCHESTRATE_VISIBLE=1`, Claude desktop running and the
  CLI signed in, they are also listed in its Code tab.
- On macOS, a builder that records the screen or uses the camera needs that permission granted to the app you run
  in (Terminal, the Codex app or Claude). Its first attempt fails until the owner grants it.
- An item whose `needs` field has the type `access` needs the owner to approve a permission or a prompt, and one
  with the type `hardware` needs a device connected. A builder can finish either kind only in a visible session,
  while the owner is at the machine, because an approval prompt can't appear in a background session. Start that
  builder with `ORCHESTRATE_VISIBLE=1` at a time the owner has said they are there. The builder asks for access as
  soon as it starts, and the owner's approval in the prompt is all it needs. Nobody records it in the chat.

Each result line says where its session ran. `path` is `visible` for the app or `headless` for the background, and
`path_reason` says why when it is `headless`.

The script names each session it starts `<repository> · <MODULE> · <step>`, such as `thrum · CREATOR · M1 build`,
`thrum · CREATOR · M1 review` or `thrum · CREATOR · design review`. A planner's step is `plan:` and the start of
its task, under the first module the task names, or under `plan` when it names none. Claude's Code tab lists
sessions outside any project, and sorting them by title then keeps each module's sessions together.

## What the owner asked for

The owner says it in plain words: "build it with two Claude builders and one Codex builder", "keep three going on
Core and Water", "just do Water M3". Take from that how many builders to run and on which hosts (`codex`,
`claude`, or a host the project settings name), any model or effort the owner named, which modules or which single
milestone, and anything the owner ruled out. If no module is named, it is every module in the module list.

Where the request leaves something open, use the `Builders:` line of the project settings, and say in your first
report what you chose. Don't stop to ask. Without `--host`, the script uses the `Default host:` line of the
project settings, or else the host it is running inside.

The script already chooses the model and effort: the model from the project settings, medium effort for builders
and reviewers, and high for planners. Medium is the owner's choice, so raise it only where a run has been seen to
fall short. Pass `--model` or `--effort` only when the owner asked for something different, and they cover only
that one command. Each result line's `ran_on` field says which host, model and effort the session got, so that is
where to look when you tell the owner what ran. A flag also overrides the settings, so one passed out of habit
would hide a later change to them.

When the owner wants one kind of agent set differently from now on, such as "plan with Fable" or "review at high
effort", that goes in the project settings as a line such as `Claude planner: claude-fable-5-2 high` or
`Reviewer: high`. A line that names a model also names a host, and applies on that host only, so a planner started
on Codex still gets a Codex model.
[The settings reference](../plan-module/references/profile.md#a-model-or-an-effort-for-one-kind-of-agent) has the
forms. On a project that is already planned, add the line yourself and commit it, because the owner asked for the
change. On a new project the settings don't exist yet, so put the owner's words in the planner's task and pass the
flags on that first `plan` command.

Before you start Codex builders, run `quota --worktree <path>`. It forecasts whether the Codex weekly usage limit
will last.

## Which milestone is next

A module's milestones run in order, so only its next milestone matters. `ready --worktree <repo>` reads every
module on the main branch and sorts each module's next milestone into one of these groups.

A milestone that is Waiting isn't stuck: its next step is already lined up, and you take it by running the `next`
command. A milestone that is Blocked can't move until someone steps in. Each of the two carries a `reason`.

| Group in the output | The module's next milestone |
|---|---|
| `ready` | is Not Started, and nothing stops a builder starting it |
| `waiting` | is Waiting. With `reason: on_dependency`, `depends_on` names the milestone in another module it waits for. With `for_replan` or `for_diagnosis`, a planner has to rewrite it or find out why it keeps failing, and `next` is the planner's command |
| `taken` | is In Progress under another lead |
| `review_owed` | is Ready for Review: the script's checks passed and it waits for a reviewer. A milestone a builder set Ready for Review before 2.1.0, with no record of the script's checks, is listed under `ready` instead, because `run` checks it first |
| `design_not_approved` | can't start, because the module's design is not yet Design Approved by a reviewer |
| `blocked` | is Blocked. `reason` says why, such as `needs_human_feedback` or `too_many_failed_reviews` |
| `invalid` | can't be read: the done-when file is malformed, or an agent changed what it may not |
| `finished` | none. Every milestone of the module is Done |

When nothing can start, `ready` adds a `next` field with the command to run. `status` gives the same in a few
lines of text, and `status --module <M>` lists every milestone of one module with its latest review.
[The done-when reference](../plan-module/references/done-when.md#statuses-and-their-stored-names) has the full list
of statuses and their stored names.

The script reads plans from the main branch, not from your working copy. If plan files are uncommitted or not yet
merged, `ready` and `run` name them under `unmerged_plans`, and `next` is `adopt --worktree <repo>`. Use `adopt`
rather than a commit you make by hand: it commits only those plan files and merges them. It also merges a first
`ORCHESTRATE.md`, and the reports under `<evidence>/build-reports/`.

Until a module's design is Design Approved, and while nothing is built, `adopt` also approves revised items, and
the design review judges them. After that it refuses them, and `next` names the `plan` command and `owner scope`.

A changed `ORCHESTRATE.md` on an existing project is the owner's decision. `ready` and `status` name it under
`settings_differ`. Commit it once the owner has agreed to the change in the chat.

### Keeping builders busy

Keep the chosen number of builders running, up to the number of milestones that can start. When a builder stops,
start the next milestone that can start, and prefer the module that builder was just in. When there are fewer
such milestones than builders, give them to the hosts in the order the owner listed. Each milestone gets a new
builder session, and only one builder works in a module at a time.

The owner's number is a limit, not a target. A milestone with items that need access or hardware has to run while
the owner is at the machine, which makes it tempting to start it alongside the builders already running. Don't: give
it the next builder that stops. `run` counts the builders running in the repository against the number in the
`Builders:` line, and past it prints `REFUSED` and starts nothing. Put the `ask` in `next` to the owner, and only on
their yes run its command, with their words in `--more-builders`. Count builders with `runs` before you tell the
owner how many are running.

Before it starts a builder, the script marks the milestone In Progress in a way every copy of the repository can
see. A second lead that runs `run` on it gets `TAKEN` and starts nothing.

Give each module its own worktree on its own branch, in a folder git ignores. A worktree is a second working copy
of the repository, so two builders can work at once. If the repository ignores no folder, add one to
`.git/info/exclude`. Keep the worktree across milestones, so build caches stay warm, and remove it when the module
is Done and nothing in it is unmerged. The result that says a module is finished reminds you. Build output is what
fills the disk on a long build: in one project, checkouts of finished modules held about 15 GB while a builder
stopped for want of 2.

- With `Merge: push`, branch from the remote:
  `git worktree add -b build/<module> <folder>/<module> <remote>/<branch>`.
- With `Merge: local`, branch from the local main branch.

Builders merge with the `merge` command. It rebases, runs the project's test command, and pushes or fast-forwards
the main branch, all under one lock. The milestone stays In Progress: only `run` sets it Ready for Review, after
its own checks pass on the main branch's tip, outside that lock, and `merge` refuses a builder's commit that sets it.

If nothing can start, run fewer builders and say why in the report. Never have a builder start a milestone before
a milestone it depends on is Done. That is how two modules end up with two versions of the same thing.

When a module is down to its last milestone, and the next module in the module list has no done-when file, run
`plan` for that module now, so that builders don't run out of work.

## Starting agents

| To start | Run |
|---|---|
| a builder | `run --module <M> --worktree <path> --host <host>`, as a background command |
| a reviewer of a milestone | `review --module <M> --milestone <id> --commit <sha> --worktree <path> --host <host>` |
| a reviewer of a design | `review --module <M> --milestone design --worktree <path> --host <host>` |
| a planner | `plan --worktree <repo> --task "<what to plan>" --host <host>`, as a background command |

Start reviewers and planners with these commands, never as your own subagents, because only the script can
verify what they changed and save it. Both run in a checkout the script keeps for them, so their `--worktree` only
names the repository, and you don't make a worktree for either.

When a builder stops, `run` prints one line of JSON that says why. A `warnings` field names something the host
would not load, such as an `AGENTS.md` that the Claude CLI won't read, with the fix. Tell the owner in your next
report, and don't stop for it.

From a planner, only a result of `PLANNED` merges anything, including files the planner wrote outside the plans
folder, such as tests. On `BLOCKED`, `NEEDS_CONTEXT` or `UNFINISHED`, nothing merges. The script keeps the files the
planner changed in a git stash, and any commits on a branch, and the result names both (`stash`, `branch`), so
report them and give what holds up to the next planner. One planner runs at a time in a repository. A second
`plan` waits for the first to finish, then plans from what it merged, so you can start planners for two modules
one after the other without checking on the first.

Two more commands help here.

`runs --repo <repo> --json` lists what is running now: each session's module, milestone, kind of agent, host,
turns, tokens, the step it is on, and the tool call its agent is waiting on, if any. Without `--repo` it covers every repository on the machine.
Run it before you start builders, so that you count the ones already running. `status` also marks the modules that
have a session running.

`check --module <M> --milestone <id> --worktree <tree>` runs one milestone's Automated Checks, the commands that
prove its items, in a working copy as it stands, and writes nothing. For each one it says `pass`, `fail`, `error`
or `timeout`, with the end of the output (`--json` gives all of it). A `fail` ran and failed, which is expected
before the work exists, so read the output. An `error` can't run as written: it isn't valid shell, or it exits with
126. Fix an `error` in how the check is written, never by weakening what it tests.

### Which host reviews

When the owner works with two hosts, run each review on the host that didn't build the milestone. A reviewer from
another company shares fewer of the builder's blind spots.

`Review host: other` in the project settings makes that the default, both for `review` without `--host` and for
the design review that `run` does first. A milestone's review then goes to the host that didn't build it, which
the script reads from its own record of the builder run. A design review goes to the host that didn't write the
plan, when the `plan` command started that planner. `--host`, or `run --review-host <host>`, overrides the
settings.

A `next` names the worktree of the command that printed it. So when you follow a `next` from a `ready` or `status`
you ran in the main working copy, put the module's own worktree in its place.

A `next` that runs a module, or reviews its design, reuses the host and the review host of that module's latest
builder run. Before any builder has run, `next` follows the project settings. So when the owner works with two
hosts and the settings say `same` or nothing, name the host yourself.

If the other host fails to start (a `HOST_FAILED` result), run the review on the same host in a new session, and say so
in the report.

## What each result means

A result with `next` tells you the command to run, and `next.by` says who runs it: `lead` is you, and `planner`
means the command starts a planner. Either way you run it without asking the owner, unless `next` also says
`decides: owner`. That is a decision only the owner may make: put the `ask` text to them in the chat, wait, and then
run the command yourself with their answer in `--text`. Give that module's builder other work while you wait.

| The script prints | Which means | You do |
|---|---|---|
| `READY_FOR_REVIEW`, `review: false` | The milestone is Done. It needed no reviewer, and the script's own run of the checks passed. | Start the builder's next milestone. |
| `READY_FOR_REVIEW`, `review: true`, or `REVIEW_OWED` | The script's checks passed, and the script set the milestone to Ready for Review. `reused_checks` lists any check it didn't run again because it had already passed on the same files. | Run the `review` in `next`, at that commit, on the review host. |
| `WAITING`, `reason: for_replan` or `for_diagnosis` | Four failed reviews repeated a finding, so a planner has to rewrite the milestone, or six failed, mostly on new findings, so a planner has to find out why. The script won't start a builder on it. | Run the `plan` command in `next`. It sends the milestone and its reviews to a planner. Once that plan is merged, `run` builds the rewritten milestone. A diagnosing planner may instead keep the plan, and `plan` prints `KEPT`: see below. |
| `DESIGN_NOT_APPROVED` | `run` already ran the design review (unless you passed `--no-design-review`), and its result was not `DESIGN OK`. | `design_review` holds the result, and `next` the follow-up, as described under [After a review](#after-a-review). |
| `WAITING`, `reason: on_dependency` | The milestone can't start until a milestone in another module is Done. | Give the builder other work. |
| `TAKEN` | Another lead has the milestone In Progress, or another `run` in this repository is working on the module. `by` says who. For a `run` in this repository, `holder` gives its process and worktree, and since when. | Give the builder other work. |
| `BLOCKED` | The milestone is Blocked. The script has set its `state` to `blocked` and saved the `reason`, the items and what would unblock it in the milestone's `blocked` field. | See [A milestone that stopped](#a-milestone-that-stopped). |
| `NEEDS_CONTEXT` | The builder is missing a fact: Blocked with `reason: needs_context`. | If the answer is in the files, resume the builder with `--message`. Otherwise bring the question to the owner. |
| `CHECKS_FAILED`, `NO_PROGRESS_FOR_HOURS` or `STALLED` | The builder kept saying it had finished when the script's checks disagreed (`CHECKS_FAILED`, or once with `run --checks-only`), made no progress in the hours given with `--budget-hours` (`NO_PROGRESS_FOR_HOURS`), or kept ending its turns on progress notes (`STALLED`). | Run a `review` on what exists, so the next attempt starts from concrete findings. |
| `INVALID` | The done-when file is malformed, or an agent changed something that isn't its to change, or the items are not the approved ones. | Send the problems to a planner. Don't resume that builder until a planner has fixed them. |
| `FINISHED` | Every milestone of the module is Done. | Nothing more for this module. |
| `HOST_FAILED`, `WRONG_MODEL_OR_EFFORT` or `PAUSED` | The session can't go on as started. `HOST_FAILED` means the host failed: two turns failed in a row, its program is missing, or its usage limit was reached, and `reason` says which. `WRONG_MODEL_OR_EFFORT` means a turn ran on a model or effort other than the ones the run named. `PAUSED` with a `reason` means the owner pressed Stop in the app, or has the session open there. | Stop that builder and report it, with the reason the script gave. A `HOST_FAILED` on one host doesn't stop builders on another. Leave a `PAUSED` builder to the owner until they say to carry on. |
| `SCRIPT_FAILED` | The script couldn't do a step of its own, such as fetching the main branch, making its checkout, writing a file the sandbox refused, or recording that the milestone is Ready for Review. The builder's committed work isn't lost. | Do what `reason` and `next` say, then run the command again. Report it to the owner only if you can't fix it. Don't tell them it was quota or sign-in: that is `HOST_FAILED`. |

The script's other commands print results of their own. `adopt` prints `ADOPTED` and `migrate` prints `MIGRATED`,
and either prints `NOTHING` when there was nothing to do. `unblock` prints `UNBLOCKED`. Any of these prints
`REFUSED`, with `problems` and usually `next`, when it won't act, and `FAILED`, with `detail`, when it tried and
couldn't. An `owner` command prints `DONE` once it has saved the decision, or `RELEASED` for `owner release`.

A result's `stopped_turn` says the script ended a turn itself, because a tool call that isn't a shell command was
open for more than 15 minutes or the turn limit was reached, and names the call. The first result after the script's
version changes carries `changed`, the list of what now behaves differently: tell the owner what affects them.

### A milestone that stopped

A builder stops only when the milestone is finished or Blocked. It never stops to have the owner confirm a step
they have already taken, such as approving a prompt. On a `BLOCKED` result, `reason` says what kind of block it
is, and `next` gives the command for it:

| `reason` | Who steps in, and how |
|---|---|
| `needs_human_feedback` | The builder couldn't judge an item and asked for a human eye. Show the owner the evidence and the question from `next` in the chat. Their reply, such as "looks good to me", is the Human Feedback: save it with `owner feedback`, with the question in `--asked` and their words in `--said`. The script records both, the builder and the reviewer read them there, and the milestone can start again. Don't send their reply through `run --message`, because a reviewer can't count a lead's message as the owner's words. |
| `needs_access` | The builder couldn't get a permission or an approval prompt, usually because it ran where nobody could approve it. Tell the owner what has to be approved, and run the builder again in a visible session while they are at the machine (see [Where sessions run](#where-sessions-run)). Their approval in the prompt unblocks it, so there is nothing to save. |
| `needs_hardware` | A device wasn't connected. Tell the owner which device, and run the builder again once it is there. |
| `needs_context` | The builder is missing a fact. If you can find it, pass it in `run --message`, which unblocks the milestone. Otherwise bring the question to the owner. |
| `needs_dependency` | The milestone needs something another module owns that no plan provides yet. Send it to a planner. |
| `too_many_failed_reviews` | The milestone failed review too many times. `next` asks the owner, with what failed in each round: accept it as it is, change its scope, or reopen it for another try. Bring that question to the chat. |

When the milestone is blocked for several reasons, `next` covers each. When the builder left a handoff, the
`blocked` field names it, and `next` passes it to whoever picks the milestone up. Whatever the reason, give that
module's builder other work while you wait.

### After a review

A review prints `REVIEWED`, with the result in its `verdict` field, `INVALID`, or `BLOCKED` with `reason:
needs_access` when the reviewer couldn't reach the product. That merges nothing and counts no round. Put its `ask`
to the owner, and run its `next`, the same review in a visible session, while they are at the machine. `INVALID` means the reviewer did
something a reviewer doesn't do, such as editing code, writing no review or naming the wrong milestone. Nothing
from an invalid review is saved, so run it again, on the other host if you can. One `INVALID` starts no reviewer:
a milestone that is Ready for Review on the main branch with no record of the script's checks, which a builder
before 2.1.0 set itself. Its `next` is the `run` that checks it.

A reviewer marks each problem it finds as a Must Fix, which fails the review, or a Suggestion, which doesn't. After
a `PASS`, `next` is the module's next milestone, or a `why` that says the module is finished.

After a `FAIL`, the result's `ladder` field names the escalation step that the counts call for, and `next` is the
command for it. `rounds` counts the failed reviews, `fails` those that repeated an earlier finding, and `repeated`
names the findings that did:

| `ladder` | You do |
|---|---|
| `same-session` | Resume the builder with `--message` and what the reviewer found. |
| `fresh-session` | Start a new builder session with `--fresh --message`. |
| `replan` | Run the `plan` command. Its task names the milestone and its reviews. Until a planner has changed the milestone, `ready`, `status` and `run` say it is Waiting with `reason: for_replan`, and `run` won't start a builder on it. |
| `diagnose` | Run the `plan` command. The planner reads every round and either changes the milestone, as for `replan`, or keeps the plan and names who has to act. |
| `too_many_failed_reviews` | The script has set the milestone to Blocked, with `reason: too_many_failed_reviews`. `next` asks the owner, with what failed in each round: accept it as it is, change its scope, or reopen it for another try. Bring that question to the chat. |

When a diagnosing planner keeps the plan, `plan` prints `KEPT`, with `who` and `next`. For `builder` or `reviewer`,
`next` starts a new builder session, and the script tells the next reviewer of a `reviewer` judgement. For `owner`,
the milestone is Blocked with `reason: too_many_failed_reviews`, and `next` is the question for the owner.

Follow the step it names. The count is the record of what has already been tried, and a lead that overrules it
runs the same failing attempt again.
[The done-when reference](../plan-module/references/done-when.md#when-a-review-fails) explains each step.

`next --module <M> --worktree <path> --milestone <id>` works the same step out again later, as `action` with the
message to send. It knows only about failed reviews, not a milestone that stopped for another reason.

A design review's `verdict` is `DESIGN OK` or `DESIGN CHANGES`. After `DESIGN OK` the design is Design Approved,
and `next` is the module's first milestone. After `DESIGN CHANGES` it is Design Changes Requested, and `next` is
the planner's revision, with the review file under `findings`. Send the Must Fix findings to a planner, then run
the design review again. Stop and report the module only when a Must Fix comes back after the planner said it was
fixed, or when a finding needs something on the `Owner decides` list in the project settings.

When a planner plans a new module, its result lists the modules whose designs need a review, and no builder starts
on them until the design is Design Approved.

If a builder breaks the main branch, the first builder to notice fixes it.

## The owner's decisions

The owner follows the build by talking to you and never uses a terminal, so every command is yours to run,
including the ones that save their decisions. Never give the owner a command to type.

If `ORCHESTRATE_VISIBLE=1` is set, they can watch a session that runs in an app, in the Codex app or in Claude's
Code tab, and type into a Codex thread to steer it. If they press Stop on a Codex thread, or open a Claude session to work in it, that builder is `PAUSED`
and the session is theirs until `run` hands it back. When they ask you to stop, `pause --worktree <repo>` stops
the running sessions cleanly, and `run` carries on later.

A decision that is the owner's is saved with
`owner <verb> --worktree <repo> --module <M> --milestone <id> --text "..."`, with what they said in `--text`:

| Verb | What it saves |
|---|---|
| `feedback --item <item> --asked "..." --said "..."` | Their Human Feedback on an item that needs it: the question you put to them in `--asked`, and their words in `--said`. Repeat `--item` when one reply covers several items. The milestone can then start again. |
| `accept` | A milestone is Done without a passing review. With `--milestone design`, the design is Design Approved without one. |
| `rereview` | A milestone that is Done goes back for a new review. The old review is kept. |
| `reopen` | A milestone that is Blocked with `reason: too_many_failed_reviews` gets another try. |
| `release` | A milestone that another lead started, and that lead is gone, is taken out of In Progress, so that this lead can start it. A `TAKEN` result names this command when it applies. |
| `scope` | The done-when file, as edited in the worktree, is the new scope. Use it only for an edit the owner dictated exactly, such as a number: make the edit, show them the diff, and run it on their yes. |

A change of mind about what is wanted goes into the brief, if the project has one, and then to a planner, with
their words as the task: `plan --worktree <repo> --task "<their words>"`. It doesn't count as a failed review. The
changed milestones are built and reviewed again, and `report` lists the task.

When you ask the owner something, give them what they need to decide in the chat itself: the options side by side,
the finding a reviewer keeps raising, the diff. Save only words the owner really gave you, for the thing they were
answering. Don't answer for them, don't fill a gap with your own judgement, and don't save what you expect them to
say. The `owner` commands refuse to run inside a session the script started, and while a `run`, `review` or
`plan` is working on the module. Neither refusal makes the command the owner's to type: in the second case, run
it again once that session has stopped. A note or summary that says the owner must type these commands at a
terminal is from an older version of this set. The script can't tell your invention from their decision, so this rule is
yours to keep. `report` lists every decision saved in the owner's name, with its words, which is how the owner
catches a wrong one, so that list goes in every report.

## Reports

Your first report tells the owner what they can ask for, which app you are running in and where the sessions ran,
what you chose where their request left something open, and the `quota` forecast if Codex builders are running.

After that, once a day, and when you stop, write the owner one screen in `<evidence>/build-reports/<date>.md`, and
send it however the owner follows this session. `report --worktree <repo> --write` writes the factual half there:
what is Done, each review's result, the planners' assumptions, what is Waiting or Blocked, the items that need
the owner, the decisions saved in the owner's name, and the tokens used for each milestone. Add the rest yourself, with links,
and merge the file with `adopt`. Until today's report is on the main branch, the results of `run`, `review` and
`plan` carry a `report_due` field. The whole report covers:

- what is now Done, with links to the evidence;
- each review's result, linked, so the owner can check a few. While the project's graded examples hold fewer than
  about ten reviews, flag every one, because the owner's corrections are how the reviewer learns how strict to be;
- new Reviewer Inspection items, the ones a reviewer judges by running the product, so the owner can adjust the
  milestone's quality bar, the words that say how good the work has to be;
- each reading of the owner's words that a planner chose (the `Assumption:` lines in a plan, which a
  `PLANNED` result counts under `assumptions`), so that an unattended build doesn't settle them silently;
- anything Blocked or Waiting, with its reason and what would move it on;
- every item that needs the owner, in one list, so they can settle them in one sitting: the ones that need human
  feedback, with the question, and the ones that need access or hardware, with what they have to approve or
  connect and when they need to be at the machine;
- each entry in the glossary that has a `Proposed:` line, so the owner can agree the name or pick another. When they
  agree, remove the line and merge the glossary with `adopt`;
- every decision saved in the owner's name since the last report, with the words saved. Quote, in your own part,
  any decision of theirs that the script has no command for, such as a change to the project settings;
- how many builders ran, the forecast for the Codex usage limit, and the tokens each builder run and review used
  where the result lines had a `usage` field. The `cost` command adds these up for each milestone.

If a result line's `quota` field first sets `warn`, the work still to do won't fit in what is left before the usage
limit resets. Tell the owner straight away, with its answer, and keep going. Slowing down is their decision.

## When to stop

Stop when every milestone in the module list is Done, or when everything left is Blocked, or Waiting on a milestone
that is itself Blocked. Then remove build outputs, remove the worktrees whose work has been merged, and send the
final report.
