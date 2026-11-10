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

Any host that can run shell commands can be the lead. A host is the program an agent runs in, such as Claude Code
or Codex.

The work is laid out in files the planner writes. The project is split into modules, which are parts one builder
can work on without touching the others, and each module into milestones, which are pieces small enough for one
builder session. An item is one thing that must be true before a milestone is Done, and a module's items are kept
in its done-when file, `<MODULE>-DONE.json`. The project settings are in `ORCHESTRATE.md`, and the module list is
`ARCHITECTURE.md`, in the plans folder the project settings name.

Your job is finished when every milestone in the module list is Done, or when everything left waits for the
owner. When the owner names one milestone or one module, that is the whole job: once it is Done, report and stop.

## Before the first command

Read `ORCHESTRATE.md`, then run `profile --worktree <repo>` to confirm the script can read it. The command fails
on purpose when the `Integrate:` or `Check:` line is missing, because the script won't guess whether it may push
or which command runs the tests.

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

Only the script sets a milestone to Done. It keeps a record file, `<MODULE>-ACCEPTED.json`, beside each done-when
file, and writes it only in its own commits. A milestone is Done when that record says so, not when you or
another agent says so. So don't edit a done-when file or a record file yourself, and don't revert anyone's
commits. If something looks wrong, the command's result says what, and
[What each result means](#what-each-result-means) says who fixes it.

## What you pass on

Give a planner, builder or reviewer file paths and the owner's own words, and nothing of your own. If you add your
summary or your opinion, the agent tends to agree with it, and its work is no longer independent.

- The owner's request goes to a planner word for word, in `--task`.
- A restriction the owner gave only in conversation, such as "don't touch the schema", goes to the builder with
  `--owner-rule`. The script saves it for the module and sends it again on every turn, across new sessions and
  later milestones, until you pass `--clear-owner-rules` because the owner said so.
- One-off text, such as what a reviewer found, goes in `--message`.

Whatever you write yourself for another agent, such as a `--message` or a task for a planner, is a prompt. Write it
the way the `prompting-agents` skill describes, if it is installed.

## Where sessions run

A session the script starts in the background runs inside your process, so it gets your sandbox and your
operating-system permissions, not its own. If your host runs you without network access, or without permission to
write to `.git`, the builders can't fetch, commit or merge either. So the lead has to run where those are allowed.

- A command that can't write a file because of a sandbox stops with `blocked_write` and names the path. Run that
  command outside the sandbox, or ask your host to run it with escalated permissions. Don't delete lock files
  yourself.
- On a Mac where the Codex app is running, Codex sessions run in the app instead, as threads listed under the
  project, with the sandbox the script sets and the app's permissions.
- Claude sessions run in the script's own `claude -p`. With Claude desktop running and the CLI signed in, they are
  also listed in its Code tab.
- On macOS, a builder that records the screen or uses the camera needs that permission granted to the app you run
  in (Terminal, the Codex app or Claude). Its first attempt fails until the owner grants it.

Each result line says where its session ran. `path` is `visible` for the app or `headless` for the background, and
`path_reason` says why when it is `headless`.

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
that one command.

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
module on the main branch and sorts each module's next milestone into one of these groups. The group names are
the script's stored names for the milestone statuses.

| Group in the output | The module's next milestone |
|---|---|
| `ready` | is Not Started, and nothing stops a builder starting it |
| `waiting` | is Waiting on Dependency. `needs` names the milestone it waits for |
| `taken` | is In Progress under another lead |
| `review_owed` | is Ready for Review |
| `replan_owed` | is Awaiting Replan. Its `next` is the planner's command |
| `design_owed` | can't start, because the module's design is not yet Design Approved by a reviewer |
| `blocked` | is Blocked or Needs Human Feedback |
| `parked` | is Too Many Failed Reviews |
| `invalid` | can't be read: the done-when file is malformed, or an agent changed what it may not |
| `finished` | none. Every milestone of the module is Done |

When nothing can start, `ready` adds a `next` field with the command to run. `status` gives the same in a few
lines of text, and `status --module <M>` lists every milestone of one module with its latest review.
[The done-when reference](../plan-module/references/done-when.md#statuses-and-their-stored-names) has the full list
of statuses and their stored names.

The script reads plans from the main branch, not from your working copy. If plan files are uncommitted or not yet
merged, `ready` and `run` name them under `unlanded_plans`, and `next` is `adopt --worktree <repo>`. Use `adopt`
rather than a commit you make by hand: it commits only those plan files and merges them. It also merges a first
`ORCHESTRATE.md`, and the reports under `<evidence>/build-reports/`.

Until a module's design is Design Approved, and while nothing is built, `adopt` also approves revised items, and
the design review judges them. After that it refuses them, and `next` names the `plan` command and `owner scope`.

A changed `ORCHESTRATE.md` on an existing project is the owner's decision. `ready` and `status` name it under
`profile_differs`. Commit it once the owner has agreed to the change in the chat.

### Keeping builders busy

Keep the chosen number of builders running, up to the number of milestones that can start. When a builder stops,
start the next milestone that can start, and prefer the module that builder was just in. When there are fewer
such milestones than builders, give them to the hosts in the order the owner listed. Each milestone gets a new
builder session, and only one builder works in a module at a time.

Before it starts a builder, the script marks the milestone In Progress in a way every copy of the repository can
see. A second lead that runs `run` on it gets `TAKEN` and starts nothing.

Give each module its own worktree on its own branch, in a folder git ignores. A worktree is a second working copy
of the repository, so two builders can work at once. If the repository ignores no folder, add one to
`.git/info/exclude`. Keep the worktree across milestones, so build caches stay warm.

- With `Integrate: push`, branch from the remote:
  `git worktree add -b build/<module> <folder>/<module> <remote>/<branch>`.
- With `Integrate: local`, branch from the local main branch.

Builders merge with the `land` command. It rebases, runs the project's test command, and pushes or fast-forwards
the main branch, all under one lock.

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
| a planner | `plan --worktree <path> --task "<what to plan>" --host <host>`, in a clean worktree |

Start reviewers and planners with these commands, never as your own subagents, because only the script can
verify what they changed and save it.

When a builder stops, `run` prints one line of JSON that says why. A `warnings` field names something the host
would not load, such as an `AGENTS.md` that the Claude CLI won't read, with the fix. Tell the owner in your next
report, and don't stop for it.

From a planner, only a result of `PLANNED` merges anything, including files the planner wrote outside the plans
folder, such as tests. On `BLOCKED`, `NEEDS_CONTEXT` or `UNFINISHED`, the planner's files stay uncommitted for you
to report and then clear. One planner runs at a time in a repository. A second `plan` gets `TAKEN`, which names
the holder, with a `next` to run it again when that planner stops. When two modules both need a planner, run them
in turn, or give one planner both tasks.

Two more commands help here.

`loops --repo <repo> --json` lists what is running now: each session's module, milestone, kind of agent, host,
turns, time since it last did anything, and tokens. Without `--repo` it covers every repository on the machine.
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

If the other host fails to start (a `FLOOR` result), run the review on the same host in a new session, and say so
in the report.

## What each result means

A result with `next` tells you the command to run, and `next.by` says whose move it is. `lead` or `planner` means
you carry it out without asking the owner. `owner` means it is a decision only the owner may make: put the `ask`
text to them in the chat, wait, and run the command with their answer in `--text`. Give that module's builder
other work while you wait.

| The script prints | Which means | You do |
|---|---|---|
| `CLAIMED`, `review: false` | The milestone is Done. It needed no reviewer, and the script's own run of the checks passed. | Start the builder's next milestone. |
| `CLAIMED`, `review: true`, or `REVIEW_OWED` | The milestone is Ready for Review. | Run the `review` in `next`, at that commit, on the review host. |
| `REPLAN_OWED` | The milestone is Awaiting Replan (four failed reviews repeated a finding) or Awaiting Diagnosis (six failed reviews, mostly on new findings), so the script won't start a builder on it. `ladder` says which. | Run the `plan` command in `next`. It sends the milestone and its reviews to a planner. Once that plan is merged, `run` builds the rewritten milestone. A diagnosing planner may instead keep the plan, and `plan` prints `KEPT`: see below. |
| `DESIGN_OWED` | `run` already ran the design review (unless you passed `--no-design-review`), and its result was not `DESIGN OK`. | `design_review` holds the result, and `next` the follow-up, as described under [After a review](#after-a-review). |
| `WAITING` | The milestone is Waiting on Dependency. | Give the builder other work. |
| `TAKEN` | Another lead has the milestone In Progress, or another `run` in this repository is working on the module. `by` says who. For a `run` in this repository, `holder` gives its process and worktree, and since when. | Give the builder other work. |
| `BLOCKED` | The milestone is Blocked, or Needs Human Feedback. The script has set its `state` to `blocked` and saved what would unblock it. | See [A milestone that stopped](#a-milestone-that-stopped). |
| `NEEDS_CONTEXT` | The builder is missing a fact. | If the answer is in the files, resume the builder with `--message`. Otherwise treat it as `BLOCKED`. |
| `UNCLAIMED`, `BUDGET` or `STALLED` | The builder kept saying it had finished when the script's checks disagreed, or stopped making progress, or kept ending its turns on progress notes. | Run a `review` on what exists, so the next attempt starts from concrete findings. |
| `INVALID` | The done-when file is malformed, or an agent changed something that isn't its to change, or the items are not the approved ones. | Send the problems to a planner. Don't resume that builder until a planner has fixed them. |
| `PARKED` | The milestone is Too Many Failed Reviews. | Put it in the report. `next` is the owner's `unpark`. |
| `FINISHED` | Every milestone of the module is Done. | Nothing more for this module. |
| `FLOOR`, `PIN` or `PAUSED` | The session can't go on as started. | Stop that builder and report it, with the reason the script gave. A `FLOOR` on one host doesn't stop builders on another. A `PAUSED` with a `reason` means the owner pressed Stop in the app, or has the session open there. Leave it to them until they say to carry on. |

### A milestone that stopped

On a `BLOCKED` result, `next` covers the cause.

When an item needs human feedback, `next` gives the question for the owner and the `owner answer` command for
their reply. Their answer goes into the script's record, where the builder and the reviewer read it, and the
milestone can start again. Don't send their answer through `run --message`. When the milestone is blocked for
other reasons as well, `next` covers those, and `next.owner_answers` still gives the question and the command for
each such item that hasn't passed.

For any other cause:

- If you can supply what is missing from the files, do so, and then run `unblock`.
- If something another module owns is missing, or the design is the problem, send it to a planner.
- Otherwise put it in the report, and give the builder other work.

### After a review

A review prints `REVIEWED`, with the result in its `verdict` field, or `INVALID`. `INVALID` means the reviewer did
something a reviewer doesn't do, such as editing code, writing no review or naming the wrong milestone. Nothing
from an invalid review is saved, so run it again, on the other host if you can.

A reviewer marks each problem it finds as a Must Fix, which fails the review, or a Suggestion, which doesn't. After
a `PASS`, `next` is the module's next milestone, or a `why` that says the module is finished.

After a `FAIL`, the result's `ladder` field names the escalation step that the counts call for, and `next` is the
command for it. `rounds` counts the failed reviews, `fails` those that repeated an earlier finding, and `repeated`
names the findings that did:

| `ladder` | You do |
|---|---|
| `same-session` | Resume the builder with `--message` and what the reviewer found. |
| `fresh-session` | Start a new builder session with `--fresh --message`. |
| `replan` | Run the `plan` command. Its task names the milestone and its reviews. Until a planner has changed the milestone, `ready`, `status` and `run` say `replan_owed`, and `run` won't start a builder on it. |
| `diagnose` | Run the `plan` command. The planner reads every round and either changes the milestone, as for `replan`, or keeps the plan and names who has to act. |
| `park` | The script has set the milestone to Too Many Failed Reviews. `next` asks the owner, with what failed in each round: accept it as it is, change its scope, or unpark it for another try. Bring that question to the chat. |

When a diagnosing planner keeps the plan, `plan` prints `KEPT`, with `who` and `next`. For `builder` or
`reviewer`, `next` starts a new builder session, and the script tells the next reviewer of a `reviewer` judgement.
For `owner`, the milestone is parked, and `next` is the question for the owner.

Follow the step it names. The count is the record of what has already been tried, and a lead that overrules it
runs the same failing attempt again.
[The done-when reference](../plan-module/references/done-when.md#when-a-review-fails) explains each step.

`next --module <M> --worktree <path> --milestone <id>` works the same step out again later, and prints it as
`action` with the message to send. It knows only about failed reviews, so don't run it for a milestone that
stopped for another reason.

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

They can watch a session that runs in an app, in the Codex app or in Claude's Code tab, and type into a Codex thread
to steer it. If they press Stop on a Codex thread, or open a Claude session to work in it, that builder is `PAUSED`
and the session is theirs until `run` hands it back. When they ask you to stop, `pause --worktree <repo>` stops
the running sessions cleanly, and `run` carries on later.

A decision that is the owner's is saved with
`owner <verb> --worktree <repo> --module <M> --milestone <id> --text "..."`, with what they said in `--text`:

| Verb | What it saves |
|---|---|
| `answer --item <item>` | Their answer to an item that needs human feedback. The milestone can then start again. |
| `accept` | A milestone is Done without a passing review. With `--milestone design`, the design is Design Approved without one. |
| `rereview` | A milestone that is Done goes back for a new review. The old review is kept. |
| `unpark` | A milestone that is Too Many Failed Reviews is reopened. |
| `release` | Another lead's hold on a milestone is dropped, so that this lead can start it. A `TAKEN` result names this command when it applies. |
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
what is Done, each review's result, the planners' assumptions, what waits, the items that need human feedback, the
decisions saved in the owner's name, and the tokens used for each milestone. Add the rest yourself, with links,
and merge the file with `adopt`. The whole report covers:

- what is now Done, with links to the evidence;
- each review's result, linked, so the owner can check a few. While the project's graded examples hold fewer than
  about ten reviews, flag every one, because the owner's corrections are how the reviewer learns how strict to be;
- new Reviewer Inspection items, the ones a reviewer judges by running the product, so the owner can adjust the
  milestone's quality bar, the words that say how good the work has to be;
- each reading of the owner's words that a planner chose (the `Assumption:` lines in a plan's log, which a
  `PLANNED` result counts under `assumptions`), so that an unattended build doesn't settle them silently;
- anything Blocked, Waiting on Dependency or Too Many Failed Reviews, with what would unblock it;
- every item that needs human feedback or hardware, in one list, so the owner can settle them in one sitting;
- each entry in the glossary that has a `Proposed:` line, so the owner can agree the name or pick another. When they
  agree, remove the line and merge the glossary with `adopt`;
- every decision saved in the owner's name since the last report, with the words saved. Quote, in your own part,
  any decision of theirs that the script has no command for, such as a change to the project settings;
- how many builders ran, the forecast for the Codex usage limit, and the tokens each builder run and review used
  where the result lines had a `usage` field. The `cost` command adds these up for each milestone.

If a result line's `quota` field first sets `warn`, the work still to do won't fit in what is left before the usage
limit resets. Tell the owner straight away, with its answer, and keep going. Slowing down is their decision.

## When to stop

Stop when every milestone in the module list is Done, or when everything left is Blocked, Waiting on Dependency,
Too Many Failed Reviews or waiting for the owner. Then remove build outputs, remove the worktrees whose work has
been merged, and send the final report.

The script's own messages still use some older words. "The loop" is the script. "The profile" is the project
settings. "Integrate" means merge. "Claimed" means Ready for Review. A "blocking" finding is a Must Fix, and an
"advisory" one is a Suggestion.
