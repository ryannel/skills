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
that isn't marked done. Under its heading the planner may have left a note on what the items and the design
don't say, such as what already exists or what another module owns. How to break the work down is yours to
decide. A plan written by an older version of this set may have a list of steps to tick and a list of stop rules
there instead. The steps are the planner's suggestion, and the stop rules are limits to keep. `DESIGN.md` holds
the design, and `LOG.md` the module's history, which you need only when you pick up unfinished work.

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
2. The work is merged with `agent_loop.py merge --worktree .`, which prints `MERGED`, and the milestone's `state`
   is still `in_progress`. When you end with `DONE`, the script runs the test command and every item's check on
   the merged work, in its own clean copy of the main branch and outside your sandbox, so checks that need the
   GPU or the screen can pass. If they pass, the script sets the milestone to Ready for Review, the status that
   says your work is finished and checked and waits for a reviewer, or to Done when no reviewer is needed, and
   writes the record. If one fails, it sends you the failure. Leave both of those states to the script: `merge`
   refuses a commit that sets `ready_for_review` or `done`, because other builders rebase onto the main branch
   and would take a status they find there as checked.
3. `LOG.md` has an entry of a few lines saying what you did, with what you verified kept apart from what you
   think is probably true. Longer notes go in the module's evidence folder, linked from the entry. Leave status
   out of the plan file. The script writes the human's page,
   `STATUS.md`, from the done-when file, and a status line anywhere else is out of date the next time a milestone
   moves.
4. Your last line is `DONE`, or `BLOCKED <reason>: <what would unblock it>`, or `NEEDS_CONTEXT: <what is
   missing>`. The reason is one of `needs_human_feedback`, `needs_access`, `needs_hardware` or `needs_dependency`,
   and the sections below say when each applies. When none of them fits, such as an approach that can't work,
   write `BLOCKED:` with no reason. The script and the lead read this line to decide what happens next, so keep
   to these forms.

If you stop without `DONE`, write a handoff first, at `<evidence folder>/<MODULE>/<milestone>-handoff.md`, and
commit it with your work. Whoever picks the milestone up next, a builder or a planner, has seen none of your
session, so say what is finished and on which commit, what you tried and ruled out, what you confirmed and what
you only suspect, and what to do first. The script merges the handoff even though your work isn't merged, and
names it in the next agent's prompt. That lets your last line be one sentence. If an earlier session left a
handoff for your milestone, read it before you start, and rewrite it rather than add to it if you stop too.

You change only three fields in the done-when file: an item's `status` (`open` or `pass`), an item's `evidence`
(where the proof is saved), and the milestone's `state`, which you set only to `in_progress`. The planner and
the reviewer own the rest, as
[who changes what](../plan-module/references/done-when.md#who-changes-what-and-when) sets out, and the script
rejects your work if any of the planner's fields has changed. So if an item is wrong or can't be met, leave it as
written and say so in your report.

`pass` means the proof came from the item's target. If you could only prove an item on a stand-in, such as a Mac
standing in for an iPhone, leave it `open` and say so in your report. Whether a stand-in is good enough is the
planner's decision, and the planner records it by writing `stand_in:` in the item's `target`.

Some items can't be finished by a builder alone. The planner marks them with a `needs` field, whose `type` says
what is needed:

- `human_feedback`: someone has to look at the result and judge it, because you can't tell. Do every other item
  first, and save the evidence the human will look at. Then end with `BLOCKED needs_human_feedback`, naming the
  items and the question to put to the human. The lead asks them, and the script records their reply as Human
  Feedback. When a later session reads that reply, cite where the script recorded it rather than restating it.
- `access`: the human has to approve a permission or a prompt, such as Computer Use for an app. Ask for that
  access as soon as your session starts, so the prompt appears while the human is there. Their approval in the
  prompt is all you need, so don't ask them to confirm it in words. If the prompt can't appear, because the session
  runs in the background, do every other item and end with `BLOCKED needs_access`, naming what has to be approved.
- `hardware`: a device has to be connected, such as an iPhone. If it is there, use it. If not, do every other item
  and end with `BLOCKED needs_hardware`, naming the device.

## What you write

The lead reads your last line, your handoff and your log entry, and passes what matters to the human. Write them
in whole sentences, the way the `prompting-agents` skill describes. Name an item by its ID and a few words of what
it is about, such as "D2.5, the window resize recording", and a module by its name in the plans. The lead knows
the plan's names. It has no way to look up a short name you made up while you worked, or the name of a crate.

Say which things you confirmed by running something and which you only suspect. The lead acts on your report as
it is written, so a guess that reads like a fact turns into an instruction. Ask the lead for what you need. What
other builders should do is the lead's to decide, because only the lead can see every run.

Record in your evidence the commit each proof ran on. `merge` rebases your work onto the main branch, and its
result lists the files the rebase brought in, under `upstream_files`. Before you end with `DONE`, run again, on
the merged commit, the proofs of the items those files could affect. Another module's change can alter what your
proof shows, and the reviewer judges the merged commit. Your other proofs still hold, so running them again only
costs time. Link evidence by its path from the repository's root, because your worktree's absolute paths stop
working when it is reused.

Prove an item that needs the human at the machine, for human feedback or for access, after your last merge, on a
build of the merged commit, so that the human's time is spent once. When a new proof has to match evidence you
took earlier, take the earlier evidence again on the merged commit. A build of an older commit differs from the
one under review, so the reviewer can't count anything recorded on it.

Keep any script a proof runs, and anything an item's `check` reads, in the repository. The script runs the checks
in its own clean checkout, where ignored folders such as `tmp/` are empty or missing, so a check that reads from
one, or writes into one without creating it, fails there.

## Merging

`agent_loop.py merge --worktree .` rebases your branch onto the main branch, runs the project's test command (the
`Test command:` line in the project settings), and then pushes or fast-forwards the main branch as the `Merge:`
line says. It does all of this under one lock, so two builders can't merge at once. It prints `MERGED` or
`FAILED`. The items' checks don't run here: the script runs them after your turn, so they don't hold the lock.

If `merge` prints `FAILED` because your commits set the milestone to `ready_for_review` or `done`, which can happen
on a branch an older builder left, set the state back to `in_progress`, commit that, and merge again.

An ordinary fix that has no plan is merged the same way. Make the fix, add a test if one would catch the fault
coming back, and run `merge`. Then a quick fix can't collide with a builder's merge or skip the tests.

## Before you finish

Run `agent_loop.py check --module <M> --milestone <id> --worktree .`. It runs the milestone's `check` commands and
the project's test command the way the script will, and changes nothing in the repository. It saves each check's
whole output to a file and names it. A check that passes here is remembered, so when the script checks the same
files after your merge it doesn't run that check again.

Then judge each `inspect` and `ask` item yourself, the way a reviewer will, on the exact build and the real target.
[How to inspect](../plan-module/references/proofs.md#how-to-inspect) says how. For an item judged by taste, first
get the fresh opinions described under [subjective work](../plan-module/references/proofs.md#subjective-work), and
keep the best round.

## The review

The lead is the agent the human chats with. When a lead is running the build, it started you, and it starts the
reviewer too, once the script's checks have passed on your merged work.

In a single chat with no lead, nobody else runs the script's checks, so after you merge, run
`agent_loop.py run --module <M> --worktree . --checks-only`. It starts no agent: it runs the checks on the merged
work and prints `READY_FOR_REVIEW` once it has set the milestone Ready for Review, or `CHECKS_FAILED` with what
failed, for you to fix and merge again. A `READY_FOR_REVIEW` with `review: false` means the milestone is Done and
needs no reviewer. Otherwise you start the reviewer, with
`agent_loop.py review --module <M> --milestone <id> --commit <sha> --worktree .`, where the commit is the one that
result names. If the human uses both Claude Code
and Codex, add `--host` with the one you are not running in. Pass the command nothing else, so the reviewer forms
its own view. Only a review started by that command is saved, and only a saved review can set the milestone to
Done. Without one, the human has to accept the milestone by hand. If you can't start a review, end with `DONE` and
say the milestone still needs one.

## When a review fails

A failed review is easy to take for the list of what is wrong with the milestone. It is narrower than that. A
reviewer can't try everything, so a review describes what one reviewer happened to try. Where it says an item
failed, it shows one thing that makes the item's statement untrue, and there may be others like it that the
reviewer never reached. The next review is done by a new reviewer, who starts again from the items and chooses
what to try. So the milestone is finished when every item is true as it is written, which is what finished meant
before the review.

The script sets the items that didn't pass back to `open`, and each needs new evidence. An item marked
`could_not_judge` is one the reviewer couldn't see for itself, so it needs evidence a reviewer can reach. The
Suggestions in a review are yours to take or leave.

The milestone's `findings`, in the done-when file, names each Must Fix, and the script marks with `repeat` any
that an earlier review also found. After four reviews with a repeat, the script sends the milestone to a planner
instead of a builder.

When a lead is running the build, the script sends you the review. In a single chat with no lead, run
`agent_loop.py next --module <M> --milestone <id> --worktree .` after a failed review. It prints the step that
the counts of failed reviews call for: carry on in this session, hand over to a new session, or send the
milestone to a planner. [The escalation steps](../plan-module/references/done-when.md#when-a-review-fails)
explain each one.

## When a behaviour won't come

Agents that can't get a behaviour right tend to keep adjusting the same approach. When adjusting isn't getting
closer, the cause is often that the mechanism can't produce the behaviour at all, and more adjusting won't show
that. Most behaviours a milestone needs have been built before, so find out how shipped products and published
work do it, and build the smallest reproduction that would show whether your mechanism can. If it can't, end
with `BLOCKED` and what you found.

A result you can't explain, such as a test that fails on one machine or a screenshot that differs from the
last run, isn't a reason to end with `BLOCKED`. It is a problem to find and fix. If fixing it needs a fact or a
choice only the human has, end with `NEEDS_CONTEXT:` and the question, and the lead puts it to the human.

On Codex, a browser, or any other program that needs more than the `workspace-write` sandbox allows, won't start
inside the sandbox. Ask to run that command outside it. The script starts Codex so that each request is granted
or refused automatically, which works in a background session too. Each one is decided on its own, so one refusal
doesn't settle the next, and an item is Blocked only once its own request has been refused.

On Codex, edit files with the `apply_patch` tool, which fails when the text it expects isn't there. A script
that replaces text, such as Python's `str.replace`, changes nothing and says nothing in that case, so an edit
can be missing without your knowing.

If a run needs something listed under `Exclusive resources` in the project settings, such as a simulator, wrap it
in `agent_loop.py lock <name> -- <command>`, so two builders don't use it at once. The lock waits until the
resource is free, so another builder holding it is normal. Do other work while you wait, and treat it as a block
only if the holder seems stuck, naming the process.

## Long commands

A command that runs for more than a few minutes, such as a long capture or a full test run, can outlast your
turn. Start it with `agent_loop.py background -- <command>`, which returns at once with the job's id, and then
wait for it with `agent_loop.py wait <id>`. `wait` returns when the job ends, or after nine minutes if it hasn't,
with the end of the job's log. A job started this way carries on when your turn ends, and the next turn's prompt
names it. `agent_loop.py jobs` lists your jobs and whether each is still running, which matters on Codex, whose
sandbox refuses `ps`.

Wait with `wait` rather than with `sleep` and `tail`. Each time you look at a job, the whole conversation is
read again, so many short looks cost far more than a few long waits. On Codex, a command that is still running
after 30 seconds hands control back to you, so keep waiting on it with a long `yield_time_ms`, such as 300000
(five minutes).

Read the end of a log, such as its last 50 lines, rather than the whole file, and judge a recording from a few
still frames taken from it rather than from the video. Everything a command prints or a tool shows you stays in
your session and is read again at every later step, and a session that fills up leaves you less room to work.

## Limits

Some things belong to someone else, and each has a way to ask for a change.

- The main branch's history belongs to every builder, because their worktrees are built on it. Bring work in with
  `merge`, and leave force-pushing out.
- The design, and each interface, which is what one module provides to the others, belong to the planner. Other
  modules are built against them, and a design is approved as it is written. When one has to change, write a
  proposal in `LOG.md`, and carry on with the work that doesn't depend on it.
- Something another module owns, or a later milestone of this one, belongs there. Built here, it would have two
  modules in charge of it. When an item needs it, end with `BLOCKED needs_dependency` and name it, so a planner
  can add it to the module that owns it or move the item.
- A decision on the `Owner decides` list in the project settings belongs to the human. End with `BLOCKED` and name
  the decision.

When you need a name for something new and the glossary has none, add an entry in the same commit, with the line
`Proposed: by builder, <date>. Not yet agreed by the human.` Mention it in your report and carry on. If your merge
then fails because another builder added an entry to the same file, keep both.

This skill covers one milestone. To keep going past it, or to run with no one watching, the human uses `/build`.
