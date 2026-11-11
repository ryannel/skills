---
name: build-milestone
description: Builds one milestone of a module from its plan and done-when file, proves it and merges it, as part of the orchestrate set in Claude Code or Codex. Use when implementing, fixing or refactoring in a repository that has an ORCHESTRATE.md. Not for planning (plan-module) or judging a milestone (review-milestone).
---

# Build a milestone

Your job is to make one milestone work where the product will actually run, such as a phone or a browser, save
proof that it does, and merge it. The proof matters as much as the code, because the next agent to look at
the work has seen none of it and goes only by what you saved.

The work comes from a plan. A planner, another agent, split the project into modules, which are parts one builder
can work on without touching the others, and split each module into milestones, which are pieces small enough to
finish in one session. You are the builder: the agent that writes the code.

## Where things are

The project settings are in `ORCHESTRATE.md`. They say where the plans are kept, which command runs the tests,
and what the project's rules are. They also list the devices and platforms the product runs on, and the files
call each of these a target. The settings link to the project's building guidance, and you read both before you
start.

If the plans folder has a `GLOSSARY.md`, read it as well. It holds the agreed name for each thing in the project.
Use those names in anything new you write and in your report, but keep to the code's own word inside existing
code.

The module's files are in its folder, `<plans folder>/<MODULE>/`. Your milestone is the first one in `PLAN.md`
that isn't marked done, and its work list is there. `DESIGN.md` holds the design, and `LOG.md` the module's
history, which you need only when you pick up unfinished work.

What the milestone has to achieve is in `DONE.json`, the done-when file. It lists items, and each item is
one thing that must be true before the milestone is Done. Each item says how it will be proved, in one or more of
three ways:

- an Automated Check, in the item's `check` field: a command that passes if it exits with 0;
- a Reviewer Inspection, in the `inspect` field: something a reviewer looks at in the running product;
- a Reviewer Question, in the `ask` field: something a reviewer answers by reading the code or a design.

A reviewer is a new agent that judges your finished milestone. [Proofs](../plan-module/references/proofs.md)
explains each way of proving an item.

The commands below that start with `agent_loop.py` belong to the script that starts agents, runs the tests and
keeps the project's records. Run them as `python3 <the build skill's folder>/scripts/agent_loop.py`.

## What finished looks like

1. Every item is marked as passed, with evidence from the item's target. Evidence is saved proof, such as a test
   log or a screenshot.
2. The work is merged with `agent_loop.py land --worktree .`, which prints `LANDED`.
3. The milestone's `state` says what happens next. A milestone needs a reviewer if any of its items has an
   `inspect` or `ask` field, or if it is the module's last milestone. If it does, set `state` to `claimed`, the
   stored name for Ready for Review. If not, set it to `done`.
4. The work you finished is ticked in `PLAN.md`, and `LOG.md` has an entry of a few lines saying what you did,
   with what you verified kept apart from what you think is probably true. Longer notes go in the module's
   evidence folder, linked from the entry. Write no status lines in the plan: the script writes the owner's page,
   `STATUS.md`, from the done-when file.
5. Your last line is `DONE`, or `BLOCKED: <what you tried, the evidence, and what would unblock it>`, or
   `NEEDS_CONTEXT: <what is missing>`. The script and the lead read this line to decide what happens next, so keep
   to these three forms.

You change only three fields in the done-when file: an item's `status` (`open` or `pass`), an item's `evidence`
(where the proof is saved), and the milestone's `state`. The planner and the reviewer own the rest, as
[who changes what](../plan-module/references/done-when.md#who-changes-what-and-when) sets out, and the script
rejects your work if any of the planner's fields has changed. So if an item is wrong or can't be met, leave it as
written and say so in your report.

`pass` means the proof came from the item's target. If you could only prove an item on a stand-in, such as a Mac
standing in for an iPhone, leave it `open` and say so in your report. Whether a stand-in is good enough is the
planner's decision, and the planner records it by writing `proxy:` in the item's `target`.

An item with an `attended` field needs a person's feedback, or hardware you may not have. Do every other item
first. Then end with `BLOCKED` and name those items, so the owner can settle them in one sitting.

## Merging

`agent_loop.py land --worktree .` rebases your branch onto the main branch, runs the project's test command (the
`Check:` line in the project settings), and then pushes or fast-forwards the main branch as the `Integrate:` line
says. It does all of this under one lock, so two builders can't merge at once. It prints `LANDED` or `FAILED`.

An ordinary fix that has no plan is merged the same way. Make the fix, add a test if one would catch the fault
coming back, and run `land`. Then a quick fix can't collide with a builder's merge or skip the tests.

## Before you set Ready for Review

Run `agent_loop.py check --module <M> --milestone <id> --worktree .`. It runs the milestone's `check` commands and
the project's test command the way the script will, and changes nothing.

Then judge each `inspect` and `ask` item yourself, the way a reviewer will, on the exact build and the real target.
[How to inspect](../plan-module/references/proofs.md#how-to-inspect) says how. For an item judged by taste, first
get the fresh opinions described under [subjective work](../plan-module/references/proofs.md#subjective-work), and
keep the best round.

## The review

The lead is the agent the owner chats with. When a lead is running the build, it started you, and it starts the
reviewer too. It also doesn't take your word for anything: after you finish, the script's `run` command makes a
clean copy of the main branch and runs the test command and every item's `check` there.

In a single chat with no lead, you start the reviewer, with
`agent_loop.py review --module <M> --milestone <id> --commit <sha> --worktree .`. If the owner uses both Claude Code
and Codex, add `--host` with the one you are not running in. Pass the command nothing else, so the reviewer forms
its own view. Only a review started by that command is saved, and only a saved review can set the milestone to
Done. Without one, the owner has to accept the milestone by hand. If you can't start a review, end with `DONE` and
say the milestone still needs one.

When a review fails, run `agent_loop.py next --module <M> --milestone <id> --worktree .` and do what it prints.
Depending on how many reviews the milestone has failed, and how many of those repeated an earlier finding, it
tells you to fix what the reviewer found in this session, to hand over to a new session, or to send the milestone
back to a planner. [The escalation steps](../plan-module/references/done-when.md#when-a-review-fails) explain
each one.

The milestone's `findings`, in the done-when file, lists each Must Fix and marks with `repeat` each one
an earlier round raised. Repeats are what send a milestone back to a planner, so make sure those stay fixed.

## When a behaviour won't come

Agents that can't get a behaviour right tend to keep adjusting the same approach. After three different
approaches, each built and run, stop adjusting. Most behaviours a milestone needs have been built before, so find
out how shipped products and published work do it. If the mechanism you have may be unable to produce the
behaviour at all, build the smallest reproduction that would show whether it can. If it can't, end with `BLOCKED`
and what you found.

On Codex, a browser, or any other program that needs more than the `workspace-write` sandbox allows, won't start
inside the sandbox. Ask to run that command outside it before you end with `BLOCKED`. Each request is granted or
refused on its own. In one test run a builder ended Blocked on four items without ever asking.

If a run needs something listed under `Exclusive resources` in the project settings, such as a simulator, wrap it
in `agent_loop.py lock <name> -- <command>`, so two builders don't use it at once.

## Limits

- Don't force-push.
- Don't change the design, or an interface, which is what one module provides to the others. Write a proposal in
  `LOG.md`, and carry on with the work that doesn't depend on it.
- Don't build something another module owns, or a later milestone of this one. If an item needs it, end with
  `BLOCKED` and name it, so a planner can add it to the module that owns it or move the item. If you built it here, two modules would own the same thing.
- If the work needs a decision on the `Owner decides` list in the project settings, end with `BLOCKED` and name the
  decision.

When you need a name for something new and the glossary has none, add an entry in the same commit, with the line
`Proposed: by builder, <date>. Not yet agreed by the owner.` Mention it in your report and carry on. If your merge
then fails because another builder added an entry to the same file, keep both.

This skill covers one milestone. To keep going past it, or to run with no one watching, the owner uses `/build`.

The script's own messages still use some older words. "The loop" is the script. "The profile" is the project
settings. "Integrate" means merge. "Claimed" means Ready for Review. A "blocking" finding is a Must Fix, and an
"advisory" one is a Suggestion.
