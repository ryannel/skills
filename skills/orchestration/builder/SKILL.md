---
name: builder
description: Builds one milestone of a module from its plan and done-when file, proves it and merges it, as part of the orchestrate set in Claude Code or Codex. Use when a lead or the user gives you a milestone to build, or asks for a change small enough to build in this session, in a repository that has an ORCHESTRATE.md. Not for planning (planner) or judging a milestone (reviewer).
---

# Build a milestone

Make one milestone work where the product will really run, such as a phone or a browser, save proof that it does,
and merge it. The proof matters as much as the code, because the next agent to look at the work has seen none of it
and goes only by what you saved.

The work comes from a plan. A planner, another agent, split the project into modules, which are parts one builder can
work on without touching the others, and each module into milestones, which are pieces small enough for one session.
You are the builder, the agent that writes the code. The user is the person the project is for. The lead is the agent
the user chats with, and when a lead is running the build, it started you. A reviewer is a new agent that judges your
milestone once you finish. The script, `agent_loop.py`, starts the agents, runs the tests and keeps the project's
records. Run its commands as `python3 <the lead skill's folder>/scripts/agent_loop.py`, which your prompt gives when
the script started you.

## Where things are

The project settings are in `ORCHESTRATE.md`. They say where the plans are kept, which command runs the tests, and
what the project's rules are. They list the devices and platforms the product runs on, which the files call targets.
Their `Project guidance` section links the project's own guidance for each kind of work. Read the settings and the
guidance for building before you start.

If the plans folder has a `GLOSSARY.md`, read it. It holds the agreed name for each thing in the project. Use those
names in anything new you write and in your report, and keep to the code's own word inside existing code.

The module's files are in `<plans folder>/<MODULE>/`. `DESIGN.md` holds the design, `PLAN.md` the milestones, and
`LOG.md` the module's history, which you need only when you pick up unfinished work. Your milestone is the one your
task names. A task that names a module and no milestone means its first milestone that isn't Done, because
milestones are built in order. A task that names neither, such as a fix the user asked for in the chat, is that
change and nothing more, and [a change no milestone covers](#a-change-no-milestone-covers) says how to merge it.
Under your milestone's heading the planner may have left a note on what the items and the design don't say, such as
what already exists. How to break down the work is yours to decide. A plan from an older version of this set may
have steps to tick and stop rules there instead: the steps are a suggestion, and the stop rules are limits to keep.

What the milestone has to achieve is in `DONE.json`, the done-when file. It lists items, and each item is one thing
that must be true before the milestone is Done, with the proof that will show it:

- a `check`, for objective outcomes: a command that passes when it exits with 0;
- an `inspect`, for subjective outcomes: a checklist a reviewer works through in the running product, against a
  reference named in the milestone's `quality_bar`;
- an `ask`, for implementation outcomes: a question a reviewer answers by reading the code or the design.

[Ways to prove an item](../planner/references/proofs.md) says more about each.

## What finished looks like

1. Every item is marked as passed, with evidence from the item's target. Evidence is saved proof, such as a test log
   or a screenshot. It goes in the working folder, at `<evidence>/<MODULE>/<milestone>/`, where `<evidence>` is the
   settings' `Evidence:` path (`.orchestrate/evidence` unless they name another). Git ignores that folder and every
   worktree on this computer sees the same files there, so leave evidence uncommitted. Commit the code, the plan files
   you change, and anything a test or a check reads, which belongs outside the working folder, because `merge` refuses
   a commit that touches `<evidence>`. Start each commit's subject with the module and milestone, as in
   `ENGINE M3: ...`, because that is how the script tells whose commit broke a check on the main branch.
2. The work is merged with `agent_loop.py merge --worktree .`, which prints `MERGED`, and the milestone's `status`
   is still `in_progress`. The script sets Ready for Review or Done itself, and `merge` refuses a commit that sets
   either, because other builders rebase onto the main branch and would take that status as checked.
3. `LOG.md` has an entry of up to eight lines on what you did, with what you verified kept apart from what you think
   is probably true. The script refuses a longer entry, so put longer notes in `<evidence>/<MODULE>/` and link them.
   Leave status out of the plan files, because the script writes the user's status page from the done-when file and
   any other status line goes stale.
4. Your last line is `DONE`, `BLOCKED <reason>: <what would unblock it>`, or `NEEDS_CONTEXT: <the question>`. The
   reason is one of `needs_human_feedback`, `needs_access`, `needs_hardware`, `needs_dependency` or `main_broken`,
   which the sections below explain. When none fits, such as an approach that can't work, write `BLOCKED:` with no
   reason. The script and the lead read this line to decide what happens next, so keep to these forms.

When you end with `DONE`, the script runs the test command and every item's check on the merged work, in its own
clean copy of the main branch and outside your sandbox, so checks that need the GPU or the screen can pass. If one
fails, the script sends you the failure. If they all pass, it sets the milestone to Ready for Review, or to Done when
it needs no reviewer. The reviewer relies on that run, so once you have merged there is no need to run the checks
again yourself.

If you stop without `DONE`, first write a handoff at `<evidence>/<MODULE>/<milestone>-handoff.md`, uncommitted like
the rest of the evidence. Whoever picks the milestone up, a builder or a planner, has seen none of your session, so
say what is finished and on which commit, what you tried and ruled out, what you confirmed and what you only
suspect, and what to do first. The script names the handoff in the next agent's prompt, so your last line can be one
sentence. If an earlier session left a handoff for your milestone, read it before you start, and rewrite it rather
than add to it if you stop too.

In the done-when file you change three fields: an item's `builder_result` (`open` or `pass`), an item's `evidence`
(where its proof is saved), and the milestone's `status`, which you set only to `in_progress`. The planner and the
reviewer own the rest, as [who changes what](../planner/references/done-when.md#who-changes-what-and-when) sets out,
and the script rejects your work if a planner's field has changed. So if an item is wrong, leave it as
written and say so in your report. If it can't be met as written, end with `BLOCKED: <item> can't be met as written`
and why, which sends it to a planner rather than to another builder session.

`pass` means the proof came from the item's target. If you could prove an item only on a stand-in, such as a Mac
standing in for an iPhone, leave it `open` and say so. Whether a stand-in is good enough is the planner's call, which
it records by writing `stand_in:` in the item's `target`.

Some items can't be finished by a builder alone, and the planner marks them with a `needs` field whose `type` says
what is needed:

- `human_feedback`: someone has to judge the result, because you can't tell. Do every other item first, save the
  evidence the user will look at, and end with `BLOCKED needs_human_feedback`, naming the items and the question to
  put to the user. For something they have to play or hear, say which commit to run and how to start it. When they
  turn down every option you made, make new ones only if their words say what to change; otherwise end with `BLOCKED:
  the user turned down every option` and their words, because the reference may be wrong. The lead asks them, and the
  script records their reply as User Feedback. A later session cites where the script recorded it rather than
  restating it.
- `access`: the user has to approve a permission or a prompt, such as Computer Use for an app. Ask for it as soon as
  your session starts, so the prompt appears while the user is there. Their approval in the prompt is all you need.
  If the prompt can't appear, because the session runs in the background, do every other item and end with
  `BLOCKED needs_access`, naming what has to be approved.
- `hardware`: a device has to be connected, such as an iPhone. If it isn't there, do every other item and end with
  `BLOCKED needs_hardware`, naming the device.

When the plan doesn't tell you something you need, such as a fact, a choice the design left open, or what an item
means, look in the brief, the design and the glossary first. If the answer isn't there and a guess would change what
gets built, end with `NEEDS_CONTEXT:` and the question rather than build your guess. The lead answers it, gives it to
a planner or takes it to the user, so write it to be answered without your session: what you need, the choices you
see, and which you would pick and why. Do every part of the milestone the answer doesn't touch first.

## What you write

The lead reads your last line, your handoff and your log entry, and passes what matters to the user. Write them in
whole sentences, the way the `prompting-agents` skill describes. Name an item by its ID and a few words, such as
"M2.5, the window resize recording", and a module by its name in the plans, because the lead knows the plan's names
but not a short name you made up or the name of a file in the code. Say which things you confirmed by running
something and which you only suspect, because the lead acts on your report as written. What other builders should
do is the lead's to decide, because only the lead sees every run.

## Proving your work

Before you finish, run `agent_loop.py check --module <M> --milestone <id> --worktree .`. It runs the milestone's
checks and the project's test command the way the script will, changes nothing in the repository, and saves each
check's output to a file whose path it prints. A check that passes here is remembered, so the script doesn't run it
again on the same files after your merge.

Then judge each `inspect` and `ask` item yourself, the way a reviewer will, on the exact build and the real target.
For an inspection, work down the item's checklist against the reference, as
[how to inspect](../planner/references/proofs.md#how-to-inspect) describes. For an item judged by taste, first get
the fresh opinions described under [subjective work](../planner/references/proofs.md#subjective-work), and keep the
best attempt.

Record in your evidence the commit each proof ran on, and link evidence by its path from the repository's root, such
as `.orchestrate/evidence/WATER/M2/run.log`, because your worktree's absolute paths stop working when it is reused.

What a reviewer inspects isn't rerun after your turn, so a capture of an older build shows code that isn't under
review. `merge` lists the files its rebase brought in, under `upstream_files`. If any could
change what a capture shows, take it again on the merged commit. For visual work, plan one capture pass after your
last merge rather than one after each. Prove the items that need the user at the machine after your last merge too,
on a build of the merged commit, so the user's time is spent once.

Keep any script a proof runs, and anything a check reads, in the repository, because the script runs checks in a
clean checkout where ignored folders such as `tmp/` are empty or missing, so a check that reads from one, or writes
into one it didn't create, fails there.

An item whose check is `python3 "$ORCHESTRATE_SCRIPT" main-check <name>` is proved by a slow check the script runs on
the main branch after merges. On your branch it answers `NOT_ON_MAIN`, so you needn't run it before you merge. After
your merge it answers `COVERED` once a run on the main branch includes your commit, or `PENDING` if that run hasn't
finished, and the next run of the checks picks up its result. `FAILING_ON_MAIN` names the commit that broke it. If
that commit is yours, fix it as part of this milestone. If it is another module's, the script waits for that
module's fix without giving you a turn, so leave it alone.

## Merging

`agent_loop.py merge --worktree .` rebases your branch onto the main branch, runs the settings' `Test command:`, and
pushes or fast-forwards the main branch as the `Merge:` line says. It prints `MERGED` or `FAILED`. The items' checks
don't run here, so they don't hold up anyone's merge.

When several builders merge at about the same time, `merge` queues their branches and merges them as one batch with
one run of the test command. If that run fails, the script splits the batch to find the branch that broke it and
merges the rest, so `merge` can take a while on a busy main branch. The result's `batch` field says which branches
merged with yours.

A `FAILED` says in its `detail` what was wrong and what to do. Three cases change what you do next:

- `conflicts` names files that clash with a branch that merged ahead of yours. Nothing of yours merged: rebase,
  resolve those files, commit and merge again.
- A planner changed your milestone's items since your branch started, so the work was built against items that no
  longer stand. Take the main branch's copy of the plan files, read the items again, and change your work to meet
  them.
- `main_broken` means the main branch fails the test command without your branch. Write your handoff and end with
  `BLOCKED main_broken:` and what it names. The result's `next` gives the fix to whoever owns the breaking commit,
  and a fix of your own would race theirs.

## Shared resources

If a run needs something listed under `Exclusive resources` or `Shared resources` in the settings, such as a
simulator or the GPU, wrap it in `agent_loop.py lock <name> -- <command>`. A lock is about capacity: an exclusive
resource takes one run at a time, and a shared one as many as the settings give it, such as `gpu: 3`. Use
`lock <name>.alone` only when a run needs the whole device, such as all its memory, and keep that command short,
because everyone else waits while you hold it. A lock keeps out only runs that take the same lock, so a timing taken
while builders work is noisy whatever lock it holds, which is why the plan gives timings loose bounds.

Hold a lock only for the command that needs it. `check` takes each item's lock itself and `merge` waits in its own
queue, so don't wrap either in `lock`, which refuses them. Before you take a lock for a run that needs the user or the
screen, check that the user is there and the screen is unlocked, because a lock held while waiting for a person stops
every builder that needs it.

Finding a resource busy is normal, and `agent_loop.py locks` shows who holds each lock and who is queued. Do other
work while you wait, and end with `BLOCKED` only if the holder seems stuck, naming the process. The script stops a
command that holds a lock longer than the settings' `Lock hold limit` (30 minutes by default), with exit code 124, so
split long work into shorter commands.

## Long commands

A command that runs for more than a few minutes, such as a long capture or a full test run, can outlast your turn.
Start it with `agent_loop.py background -- <command>`, which returns the job's id at once, and wait with
`agent_loop.py wait <id>`, which returns when the job ends, or after nine minutes, with the end of its log. The job
carries on when your turn ends, and the next turn's prompt names it. `agent_loop.py jobs` lists your jobs.

Each time you look at a job, your whole session is read again, so a few long waits cost far less than many short
looks with `sleep` and `tail`. For the same reason, read the end of a log rather than the whole file, and judge a
recording from a few still frames rather than the video.

## When a behaviour won't come

When adjusting an approach isn't getting closer, the cause is often that the mechanism can't produce the behaviour at
all. Find out how shipped products and published work do it, and build the smallest reproduction that would show
whether your mechanism can. If it can't, end with `BLOCKED` and what you found.

A result you can't explain, such as a test that fails on one machine, is a problem to find and fix, not a reason to
stop. If fixing it needs a fact or a choice only the user has, end with `NEEDS_CONTEXT:` and the question.

## On Codex

A browser, or any other program that needs more than the `workspace-write` sandbox allows, won't start inside the
sandbox, so ask to run that command outside it. The script starts Codex so that each request is granted or refused
automatically, even in a background session. Each request is decided on its own, so an item is Blocked only once its
own request has been refused.

A command still running after 30 seconds hands control back to you, so keep waiting on it with a long
`yield_time_ms`, such as 300000. The sandbox refuses `ps`, so use `agent_loop.py jobs` to see your jobs.

Edit files with the `apply_patch` tool, which fails when the text it expects isn't there. A script that replaces
text, such as Python's `str.replace`, changes nothing and says nothing in that case.

## Limits

Some things belong to someone else, and each has a way to ask for a change:

- The main branch's history belongs to every builder, because their worktrees are built on it. Bring work in only
  with `merge`, which adds your commits on top. A force-push would replace history the other worktrees rest on.
- The design, and each interface, meaning what one module provides to the others, belong to the planner, because other
  modules are built against them and a design review approved them as written. When one has to change, write a
  proposal in `LOG.md`, and carry on with the work that doesn't depend on it.
- Something another module owns, or a later milestone of this one, belongs there, because built here it would have
  two owners. When an item needs it, end with `BLOCKED needs_dependency` and name it, so a planner can place it.
- A decision on the settings' `Human decides` list belongs to the user. End with `BLOCKED needs_human_feedback:` and
  the decision, so their answer is recorded as theirs.

When you need a name for something new and the glossary has none, add it to the plans folder's `GLOSSARY.md` in the
same commit, as the `domain-language` skill describes, with a `Proposed:` line, and mention it in your report. If your
merge then conflicts with another builder's entry in that file, keep both.

## A change no milestone covers

When the user asks for a change no milestone covers, such as a small fix, make it, add a test if one would catch the
fault coming back, and merge it with `merge` like any milestone, so it can't collide with a builder's merge or skip
the tests. Change only what you were asked to. Mention anything else you notice in your reply, because it may belong
to a module another builder is working on.

## Without a lead

When a lead runs the build, the script starts a reviewer once its checks pass on your merged work, and sends you a
message if the review fails. In a single chat with no lead, you do those steps:

1. After you merge, run `agent_loop.py run --module <M> --worktree . --checks-only`. It starts no agent: it runs the
   checks on the merged work and prints `READY_FOR_REVIEW` once it has set the milestone Ready for Review, or
   `CHECKS_FAILED` with what failed, for you to fix and merge again. `review: false` in the result means the
   milestone is Done and needs no reviewer.
2. Otherwise start the reviewer with `agent_loop.py review --module <M> --milestone <id> --commit <sha> --worktree .`,
   with the commit that result names, and nothing else, so the reviewer forms its own view and the settings'
   `Review host` picks where it runs. Only a review this command starts is saved and can set the milestone to Done.
   If you can't start one, end with `DONE` and say the milestone still needs a review, because otherwise the user
   has to accept it by hand.
3. After a failed review, run `agent_loop.py next --module <M> --milestone <id> --worktree .`. It says where the
   review is, and whether to carry on in this session, hand over to a new one, or send the milestone to a planner.

This skill covers one milestone. To keep going past it, or to build with no one watching, the user asks for the lead.
