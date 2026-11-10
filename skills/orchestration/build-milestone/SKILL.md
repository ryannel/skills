---
name: build-milestone
description: Builds one milestone of a module from its plan and done-when file, proves it and merges it, as part of the orchestrate set in Claude Code or Codex. Use when implementing, fixing or refactoring in a repository that has an ORCHESTRATE.md. Not for planning (plan-module) or judging a milestone (review-milestone).
---

# Build a milestone

You are a builder: the agent that writes the code for one milestone. A module is a part of the project that one
builder can work on without touching the other parts, and a milestone is a piece of a module small enough to finish
in one session. Your job is to make the milestone work on its real targets and merge it into the main branch.

Three other kinds of agent appear below. A planner wrote the plan you build from. A reviewer is a new agent that
judges your finished milestone. The lead is the agent the owner chats with, and when there is one, it started
you. A host is the program an agent runs in, such as Claude Code or Codex.

Read `ORCHESTRATE.md` first. It holds the project settings: where the plans are kept, the command that runs the
tests, the targets the product runs on, and the project's rules. Read the building guidance it links to as well.
If the plans folder has a `GLOSSARY.md`, read it. It holds the agreed name for each thing in the project. Use
those names for anything new you write, in text a user sees and in your report. Where the code already has its
own word for a thing, keep to the code's word in the code.
Then find the module's next milestone in `<MODULE>-PLAN.md`, and that milestone's items in `<MODULE>-DONE.json`,
which is called the done-when file. An item is one thing that must be true before the milestone is Done.

A command below that starts `agent_loop.py` belongs to the script that starts agents, runs the tests and keeps the
project's records. Run it as `python3 <the build skill's folder>/scripts/agent_loop.py`.

For an ordinary fix that has no plan, fix it, add a test if a test would catch the fault coming back, and merge it
with `agent_loop.py land --worktree .`. That command takes the same lock as every builder and runs the project's
test command, so a quick fix can't collide with a builder's merge or skip the tests.

## What finished looks like

1. Every item of the milestone is marked as passed, with evidence from the item's target. Evidence is saved proof,
   such as a test log or a screenshot. In the done-when file you change three fields and no others: an item's
   `status` (`open` or `pass`), an item's `evidence` (where the proof is saved), and the milestone's `state`.
   Everything else in that file belongs to the planner or the reviewer, as
   [who changes what](../plan-module/references/done-when.md#who-changes-what-and-when) sets out. If an item is
   wrong, or can't be met, leave it as written and say so in your report. The script rejects a builder's work when
   any of the planner's fields has changed: an item's statement, its proof, its target, or the milestone's
   quality bar. [Proofs](../plan-module/references/proofs.md) explains how each kind of item is
   proved.
2. The work is committed and merged with `agent_loop.py land --worktree .`. The command rebases your branch onto
   the main branch, runs the project's test command (the `Check:` line in the project settings), and then pushes or
   fast-forwards the main branch as the `Integrate:` line says. It does all of that under one lock, so two builders
   can't merge at the same moment. It prints `LANDED` or `FAILED`.
3. The milestone's `state` says what happens next. Set it to `claimed`, which means Ready for Review, when the
   milestone needs a reviewer. Set it to `done` when it doesn't. A milestone needs a reviewer if any of its items
   has an `inspect` or `ask` field, or if it is the module's last milestone.
4. The plan's status lines and its log are up to date. Keep what you verified apart from what you think is probably
   true.
5. Your last line is `DONE`, or `BLOCKED: <what you tried, the evidence, and what would unblock it>`, or
   `NEEDS_CONTEXT: <what is missing>`.

An item with an `attended` field needs human feedback, or hardware you may not have. Do every other item first.
Then end with `BLOCKED` and name those items, so the owner can settle them in one sitting.

When a lead is running the build, the script does not take your word for any of this. After you finish, its `run`
command makes a clean copy of the main branch and runs the project's test command and every item's `check` there.

## Before you set Ready for Review

Run `agent_loop.py check --module <M> --milestone <id> --worktree .`. It runs the milestone's `check` commands and
the project's test command the way the script will, and writes nothing.

Then judge each `inspect` and `ask` item yourself, the way a reviewer will.
[How to inspect](../plan-module/references/proofs.md#how-to-inspect) says how, and it applies to the exact build on
its real target. For an item judged by taste, get the fresh opinions described under
[subjective work](../plan-module/references/proofs.md#subjective-work) first, and keep the best round.

## The review

When a lead is running the build, the lead starts the reviewer.

In a single chat with no lead, you start it:
`agent_loop.py review --module <M> --milestone <id> --commit <sha> --worktree .`, with `--host` set to the other
host if the owner uses two. Tell the reviewer nothing else, so that it forms its own view. Only a review started
by that command is saved. A reviewer you start any other way can't set the milestone to Done, and the owner would
have to accept the milestone by hand. If you can't start a review, end with `DONE` and say that the milestone still
needs one.

When a review fails, `agent_loop.py next --module <M> --milestone <id> --worktree .` prints what to do. It depends
on how many reviews the milestone has failed, and how many of those repeated an earlier finding: fix what the
reviewer found in this session, hand over to a new session, or send the milestone back to a planner. Do what it
prints. The counts are the record of what has already been tried, and
[the escalation steps](../plan-module/references/done-when.md#when-a-review-fails) explain each one.

The milestone's `findings` in the done-when file lists the blocking findings, and marks with `repeat` each one an
earlier round raised. Repeats are what send a milestone back to a planner, so make sure those stay fixed.

## Facts that save a session

If the change touches behaviour, run the affected part of the product before you change it. If someone left it
broken, you want to know before you build on it.

When the right approach isn't settled and it matters, find out how shipped products and published work do it
before you experiment. Old code in the repository shows what was tried. It isn't a template.

On Codex, a browser, or any program that needs more than the `workspace-write` sandbox allows, won't start inside
the sandbox. Ask to run that one command outside it before you end with `BLOCKED`. Each request is granted or
refused separately. In one test run a builder ended Blocked on four items and had never asked.

If a behaviour still won't come after three different approaches, each one built and run, stop tuning. The
mechanism may be unable to produce it. Build the smallest reproduction that would show whether it can. If it
can't, end with `BLOCKED` and what you found.

When you prove an item on something other than its target, such as a Mac standing in for an iPhone, label the
result `proxy`.

If a run needs something listed under `Exclusive resources` in the project settings, wrap it:
`agent_loop.py lock <name> -- <command>`.

When you need a name for something new, and the glossary has no entry for it, add one in the same commit, with
the line `Proposed: by <the kind of agent you are>, <date>. Not yet agreed by the owner.`
Name it in your report, and carry on. If your merge then fails because another builder added an entry to the
same file, keep both entries.

## What you may change

You may research, run anything locally, change this module's code, and merge verified work as the project settings
allow. None of that needs approval.

- Don't force-push.
- Don't change the design, or an interface, which is what one module provides to the others. Write a proposal in
  the plan's log, and carry on with the work that doesn't depend on it.
- Don't build something another module owns. If it is missing, end with `BLOCKED` and name it, so a planner can
  add it to the module that owns it. Built here, two modules would own the same thing.
- Anything on the `Owner decides` list in the project settings goes to the owner.

This skill covers one milestone. To keep going past it, or to run with no one watching, the owner uses `/build`.

The script's own messages still use some older words. "The loop" is the script. "The profile" is the project
settings. "Integrate" means merge. "Claimed" means Ready for Review. A "blocking" finding is a Must Fix, and an
"advisory" one is a Suggestion.
