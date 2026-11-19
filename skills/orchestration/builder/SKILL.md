---
name: builder
description: Builds one milestone of a module from its plan and done-when file, proves it and merges it, as part of the orchestrate set in Claude Code or Codex. Use when a lead or the human gives you a milestone to build, or asks for a change small enough to build in this session, in a repository that has an ORCHESTRATE.md. Not for planning (planner) or judging a milestone (reviewer).
---

# Build a milestone

Your job is to make one milestone work where the product will actually run, such as a phone or a browser, save
proof that it does, and merge it. The proof matters as much as the code, because the next agent to look at
the work has seen none of it and goes only by what you saved.

The work comes from a plan. A planner, another agent, split the project into modules, which are parts one builder can
work on without touching the others, and split each module into milestones, which are pieces small enough to finish in
one session. You are the builder: the agent that writes the code. The human is the person the project is for. The lead
is the agent the human chats with, and when a lead is running the build, it started you.

## Where things are

The project settings are in `ORCHESTRATE.md`. They say where the plans are kept, which command runs the tests,
and what the project's rules are. They also list the devices and platforms the product runs on, and the files
call each of these a target. Their `Project guidance` section links to the project's own guidance for each kind
of work. Read the settings and the guidance for building before you start.

If the plans folder has a `GLOSSARY.md`, read it as well. It holds the agreed name for each thing in the project.
Use those names in anything new you write and in your report, but keep to the code's own word inside existing
code.

The module's files are in its folder, `<plans folder>/<MODULE>/`. Your milestone is the one your task names. A
task that names a module and no milestone means that module's first milestone that isn't Done, because milestones
are built in order. A task that names neither, such as a fix the human asked for in the chat, is that change and
nothing more, and [a change no milestone covers](#a-change-no-milestone-covers) says how to merge it. The plan's
milestones are left for their builders, because a lead may already be running one. Under your milestone's heading
the planner may have left a note on what the items and the design don't say, such as what already exists or what
another module owns. How to break the work down is yours to
decide. A plan written by an older version of this set may have a list of steps to tick and a list of stop rules
there instead. The steps are the planner's suggestion, and the stop rules are limits to keep. `DESIGN.md` holds
the design, and `LOG.md` the module's history, which you need only when you pick up unfinished work.

What the milestone has to achieve is in `DONE.json`, the done-when file. It lists items, and each item is
one thing that must be true before the milestone is Done. Each item says how it will be proved, in one or more of
three ways:

- an Automated Check, in the item's `check` field: a command that passes if it exits with 0;
- a Reviewer Inspection, in the `inspect` field: something a reviewer looks at in the running product;
- a Reviewer Question, in the `ask` field: something a reviewer answers by reading the code or a design.

A reviewer is a new agent that judges your finished milestone. [Proofs](../planner/references/proofs.md)
explains each way of proving an item.

The commands below that start with `agent_loop.py` belong to the script that starts agents, runs the tests and
keeps the project's records. Run them as `python3 <the lead skill's folder>/scripts/agent_loop.py`.

## What finished looks like

1. Every item is marked as passed, with evidence from the item's target. Evidence is saved proof, such as a test
   log or a screenshot. It goes in the repository's working folder, at `<evidence>/<MODULE>/` in your checkout,
   where `<evidence>` is the `Evidence:` path of the project settings (`.orchestrate/evidence` unless they name
   another). Every worktree on this computer sees the same files there, and git ignores the folder, so leave
   evidence uncommitted: git holds what the project needs to build and run, and evidence is only working
   material for the reviewer and the human. Commit code, plans, and the test data your tests read. A file a test or
   a check reads belongs in the repository outside the working folder, because `merge` refuses a commit that adds
   or changes files under `<evidence>`.
2. The work is merged with `agent_loop.py merge --worktree .`, which prints `MERGED`, and the milestone's `status`
   is still `in_progress`. Leave `ready_for_review` and `done` to the script. `merge` refuses a commit that sets
   either, because other builders rebase onto the main branch and would take a status they find there as checked.

   When you end with `DONE`, the script runs the test command and every item's check on the merged work. It runs
   them in its own clean copy of the main branch and outside your sandbox, so checks that need the GPU or the
   screen can pass. If one fails, the script sends you the failure. If they pass, it writes the record and sets
   the milestone to Ready for Review, which means your work is finished and checked and waits for a reviewer. A
   milestone that needs no reviewer goes straight to Done.
3. `LOG.md` has an entry of a few lines saying what you did, with what you verified kept apart from what you think is
   probably true. Keep it to eight lines at most, because the script refuses a longer entry when the plan files
   merge. Longer notes go in the working folder, at `<evidence>/<MODULE>/`, linked from the entry. Leave status out of the plan file.
   The script writes the human's page, `STATUS.md`, from the done-when file, and a status line anywhere else is out
   of date the next time a milestone moves.
4. Your last line is `DONE`, or `BLOCKED <reason>: <what would unblock it>`, or `NEEDS_CONTEXT: <what is
   missing>`. The reason is one of `needs_human_feedback`, `needs_access`, `needs_hardware`, `needs_dependency` or
   `main_broken`, and the sections below say when each applies. When none of them fits, such as an approach that can't work,
   write `BLOCKED:` with no reason. The script and the lead read this line to decide what happens next, so keep
   to these forms.

If you stop without `DONE`, write a handoff first, at `<evidence>/<MODULE>/<milestone>-handoff.md` in the
working folder, and leave it uncommitted like the rest of the evidence. Whoever picks the milestone up next, a
builder or a planner, has seen none of your session, so say what is finished and on which commit, what you tried
and ruled out, what you confirmed and what you only suspect, and what to do first. Every worktree sees the handoff
where you wrote it, even though your work isn't merged, and the script names it in the next agent's prompt. That lets your last line be one sentence. If an earlier session left a
handoff for your milestone, read it before you start, and rewrite it rather than add to it if you stop too.

You change only three fields in the done-when file: an item's `builder_result` (`open` or `pass`), an item's
`evidence` (where the proof is saved), and the milestone's `status`, which you set only to `in_progress`. The planner
and the reviewer own the rest, as [who changes what](../planner/references/done-when.md#who-changes-what-and-when)
sets out, and the script rejects your work if any of the planner's fields has changed. So if an item is wrong or can't
be met, leave it as written and say so in your report.

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

The lead reads your last line, your handoff and your log entry, and passes what matters to the human. Write them in
whole sentences, the way the `prompting-agents` skill describes. Name an item by its ID and a few words of what it is
about, such as "M2.5, the window resize recording", and a module by its name in the plans. The lead knows the plan's
names. It has no way to look up a short name you made up while you worked, or the name of a file or a package in the
code.

Say which things you confirmed by running something and which you only suspect. The lead acts on your report as
it is written, so a guess that reads like a fact turns into an instruction. Ask the lead for what you need. What
other builders should do is the lead's to decide, because only the lead can see every run.

Record in your evidence the commit each proof ran on, and link evidence by its path from the repository's root,
such as `.orchestrate/evidence/WATER/M2.log`, because your worktree's absolute paths stop working when it is reused.
That path opens in every worktree on this computer.

The script's run of the checks after your turn is the proof of record, and the reviewer is told it passed and on
which commit. So once you have merged, there is no need to run your checks again yourself, and on a busy main branch
each extra run is time other builders wait for the same resources.

Evidence a reviewer inspects is different, because the script doesn't take it. A capture of an older build shows code
that isn't the code under review. `merge` lists the files the rebase brought in, under `upstream_files`. If any of
them could change what a capture shows, take that capture again on the merged commit. For visual work, plan one
capture pass after your last merge rather than one after each.

Hold a lock only for the command that needs it. Don't wrap the script's own `check` or `merge` in `lock`: `check`
takes each item's lock just for that item, and `merge` waits in the merge queue, so `lock` refuses them. `merge`
already makes builders take turns, so a script of your own that holds a lock across a rebase, a check and a merge
makes everyone wait through all three, and it usually fails because the main branch moved while it ran. In the same
way, check that the human is there and the screen is unlocked before you take a lock for a run that needs them,
because a lock held while waiting for a person stops
every other builder that needs it.

An item whose check is `python3 "$ORCHESTRATE_SCRIPT" main-check <name>` is proved by a slow check that runs on
the main branch after merges, not by you. You don't need to run it before you merge: on your branch it answers
`NOT_ON_MAIN`. After your merge, the script's run asks it again, and it passes with `COVERED` once a run on the main
branch includes your commit. `PENDING` means that run hadn't finished in time, and the next run of the checks picks up
its result. `FAILING_ON_MAIN` means the main branch fails the check at or before your commit, and the result names
the commit that broke it. If that commit is yours, fix it as part of this milestone. If it isn't, the fix belongs to
that commit's module, so say so in your report rather than working around it.

Some items need the human at the machine, for human feedback or for access. Prove those after your last merge, on a
build of the merged commit, so that the human's time is spent once. When a new proof has to match evidence you took
earlier, take the earlier evidence again on the merged commit. A build of an older commit differs from the one under
review, so the reviewer can't count anything recorded on it.

Keep any script a proof runs, and anything an item's `check` reads, in the repository. The script runs the checks
in its own clean checkout, where ignored folders such as `tmp/` are empty or missing, so a check that reads from
one, or writes into one without creating it, fails there.

## Merging

`agent_loop.py merge --worktree .` rebases your branch onto the main branch, runs the project's test command (the
`Test command:` line in the project settings), and then pushes or fast-forwards the main branch as the `Merge:`
line says. It prints `MERGED` or `FAILED`. The items' checks don't run here: the script runs them after your turn,
so they don't hold up anyone's merge.

When several builders merge at about the same time, `merge` puts their branches in a queue and merges them together
as one batch, with one run of the test command for the lot. If that run fails, the script splits the batch to find
the branch that broke it, and merges the rest. So `merge` can take a while on a busy main branch, which is normal.
The result's `batch` field says which branches merged with yours. If your branch conflicts with one that merged
ahead of it, the result is `FAILED` and `conflicts` names the files. Nothing of yours merged: rebase onto the main
branch, resolve those files, commit, and merge again.

A `FAILED` for any other reason says in its `detail` what was wrong and what to do. Two of them change what you do
next. If a planner has changed your milestone's items since your branch started, `merge` refuses the branch,
because the work was built against items that no longer stand. Take the main branch's copy of the plan files, read
the items again, and change your work to meet them before you merge. If the result has `main_broken`, the main
branch fails the test command without your branch, so the fault isn't yours and nothing of yours landed. Stop
there, write your handoff, and end with `BLOCKED main_broken:` and what `main_broken` names. The result's `next` gives the fix
to whoever owns the commit that broke it, and every builder's merge waits on that fix, so a fix of your own would
race theirs.

## A change no milestone covers

When the human asks for a change that no milestone covers, such as a small fix, merge it the same way: make the
change, add a test if one would catch the fault coming back, and run `merge`. Then the fix can't collide with a
builder's merge or skip the tests. Change only what you were asked to change. Something else you notice on the way
goes in your reply, because it may belong to a module another builder is working on, or to a milestone not yet
built.

## Before you finish

Run `agent_loop.py check --module <M> --milestone <id> --worktree .`. It runs the milestone's `check` commands and the
project's test command the way the script will, and changes nothing in the repository. It saves each check's whole
output to a file, and prints where the file is. A check that passes here is remembered, so when the script checks the
same files after your merge it doesn't run that check again.

Then judge each `inspect` and `ask` item yourself, the way a reviewer will, on the exact build and the real target.
[How to inspect](../planner/references/proofs.md#how-to-inspect) says how. For an item judged by taste, first
get the fresh opinions described under [subjective work](../planner/references/proofs.md#subjective-work),
and keep the best attempt.

## The review

When a lead is running the build, a reviewer is started for you once the script's checks have passed on your merged
work.

In a single chat with no lead, nobody else runs the script's checks, so after you merge, run
`agent_loop.py run --module <M> --worktree . --checks-only`. It starts no agent: it runs the checks on the merged
work and prints `READY_FOR_REVIEW` once it has set the milestone Ready for Review, or `CHECKS_FAILED` with what
failed, for you to fix and merge again. A `READY_FOR_REVIEW` with `review: false` means the milestone is Done and
needs no reviewer. Otherwise you start the reviewer, with
`agent_loop.py review --module <M> --milestone <id> --commit <sha> --worktree .`, where the commit is the one that
result names. If the human uses both Claude Code and Codex, add `--host` with the one you are not running in. Pass
the command nothing else, so the reviewer forms its own view. Only a review started by that command is saved, and
only a saved review can set the milestone to Done. Without one, the human has to accept the milestone by hand. If
you can't start a review, end with `DONE` and say the milestone still needs one.

## When a review fails

When a lead is running the build, the script sends you a message after a failed review, saying where the review is
and how to read it. In a single chat with no lead, run `agent_loop.py next --module <M> --milestone <id> --worktree .`
after a failed review. It prints the same message, and the step the milestone's failed reviews call for: carry on in
this session, hand over to a new session, or send the milestone to a planner.

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

If a run needs something listed under `Exclusive resources` or `Shared resources` in the project settings, such as
a simulator or the GPU, wrap it in `agent_loop.py lock <name> -- <command>`. A lock is about capacity: how many runs
the device can serve at once. An exclusive resource takes one run at a time. A shared one takes as many as the
settings give it, such as `gpu: 3`. Use `lock <name>.alone` only when a run needs the whole device, such as all of its
memory: it waits until nobody else is using it, and everyone else waits while you have it, so keep that command
short. A lock keeps out only runs that take the same lock, so it doesn't make the machine quiet. A timing taken while
builders work is noisy whatever lock it holds, which is why the plan gives timings a loose tripwire.

The lock waits its turn, so finding the resource busy is normal, and `agent_loop.py locks` shows who holds each lock
and who is queued. Do other work while you wait, and end with `BLOCKED` only if the holder seems stuck, naming the
process. A command that holds a lock longer than the project's `Lock hold limit` (30 minutes unless the settings
say otherwise) is stopped with exit code 124 and its output is cut short. Hold the lock only for the part that needs
the resource, or split the work into shorter commands.

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

- The main branch's history belongs to every builder, because their worktrees are built on it. Bring work in only with
  `merge`, which adds your commits on top of what is there. A force-push would replace history that the other
  worktrees are built on.
- The design, and each interface, which is what one module provides to the others, belong to the planner. Other
  modules are built against them, and a design is approved as it is written. When one has to change, write a
  proposal in `LOG.md`, and carry on with the work that doesn't depend on it.
- Something another module owns, or a later milestone of this one, belongs there. Built here, it would have two
  modules in charge of it. When an item needs it, end with `BLOCKED needs_dependency` and name it, so a planner
  can add it to the module that owns it or move the item.
- A decision on the `Human decides` list in the project settings belongs to the human. End with `BLOCKED` and name
  the decision.

When you need a name for something new and the glossary has none, add an entry in the same commit, with the line
`Proposed: by a builder, <date>. Not yet agreed by the human.` Mention it in your report and carry on. If your merge
then fails because another builder added an entry to the same file, keep both.

This skill covers one milestone. To keep going past it, or to run with no one watching, the human uses `/lead`.
