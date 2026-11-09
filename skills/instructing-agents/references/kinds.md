# Each kind of instruction

Contents:
- [A goal](#a-goal)
- [Long unattended runs and plans](#long-unattended-runs-and-plans)
- [A brief for a subagent or session](#a-brief-for-a-subagent-or-session)
- [A brief for an independent reviewer](#a-brief-for-an-independent-reviewer)
- [A steer to a running agent](#a-steer-to-a-running-agent)
- [When an agent misbehaves](#when-an-agent-misbehaves)

Everything in [the core](../SKILL.md) applies to all of these. This file covers only what changes. There's a short
example of each in [examples](examples.md).

## A goal

A goal turns a request into a loop: the agent works, checks the goal, and carries on or stops. So the goal text is
also the test for finishing. Write it as an end state, like "the checkout tests pass on CI and the flaky retry is
gone", not as an activity like "improve checkout", which never finishes. Because the loop re-reads it, the goal is
also the place for a rule that must hold all the way through.

The two hosts judge that test differently.

Codex `/goal` has the thread audit itself against the objective. Its continuation template (checked 9 November 2026)
tells the model to derive requirements from the objective and the material it refers to, and to find evidence for
each explicit requirement, named item, command, test and deliverable. A file you point at isn't swallowed whole, but
its explicit requirements can become yours. So say what role each reference plays: "the inspection list in
docs/water/M2-DONE.md is the bar; research/wake/ is background". The template already tells the model not to shrink
the task, not to accept weak evidence and never to pause on its own. It may call itself blocked only after the same
blocker has held for three goal turns, so write the stop you want as a blocker it can observe, such as "the device
isn't connected", rather than "after two days". The objective is data with no more authority than the system and
developer instructions above it. It can specialise the task within those rules, but approval policy, sandbox, model
and effort are set in configuration, not in goal text. OpenAI's cookbook names six parts: the outcome, how it's
verified, what mustn't regress, the boundaries, how to choose the next attempt, and when to stop blocked with what to
report. Most goals need only a sentence for each.

Claude Code `/goal` hands the condition to a small, fast model after each turn. That model reads only the
conversation. It can't run commands or open files. So the condition has to be something the agent's own output will
show, such as a named check's exit code appearing in the transcript. The limit is 4,000 characters, and you can add a
turn or time bound, such as "or stop after 20 turns".

Some things hold on both hosts:
- Make the goal a size someone could audit. "Fix the failing test" can be too narrow. "Improve the system" can't be
  audited at all.
- Don't invent numbers. A target nobody needs, like a frame-time budget picked for the goal, becomes the thing the
  agent chases. One agent spent about nine hours on an invented cost gate before anyone noticed. Put a number in done
  only when it's a real requirement.
- A quality bar needs naming. "Polish until excellent" never finishes. Say what it's judged against, such as a list of
  qualities to check in the running product at a level shipped products of that kind reach, and who judges it.
- A research goal needs an evidence standard: what counts as confirmed, approximate or a guess.
- Put the whole task in the first message. Feeding requirements in over several turns costs quality.
- Model and effort belong in the launch, not in the objective.
- A one-line edit, a question or a short review doesn't need a goal.

## Long unattended runs and plans

Before you leave an agent alone, check that it knows what done looks like and can check it, what it may touch, what
stops it, and where the result goes. Give it standing permission for the safe loop: running local checks, fixing what
it broke, committing checkpoints. Name the stops you actually want: irreversible actions, publishing, spending, other
people's areas. Put the human's approval at the end, after it has prepared something concrete to approve.

The loop itself belongs to the harness: Codex `/goal`, Claude Code `/goal`, or a Stop hook. Don't write "keep going"
into the text instead. Whether a nudge helps depends on the model ([persistence](hosts-and-models.md#persistence)).
A session with no loop needs to know exactly when to report: at a milestone, at a seam, or when blocked.

For work that runs for hours, keep the state in files the agent rereads: a short spec, a plan, and a status. Files
survive compaction, you can read progress without interrupting, and a rule written there is read again near the
moment it applies, where a line in the opening prompt has long scrolled away. Let the agent write its own plan. A
useful plan has a purpose, milestones that are observable outcomes with the riskiest first, a short current status,
and a log of decisions with their reasons, so it doesn't go back and forth. It's rewritten in place, so it always reads
as current. If amendments pile up while nothing gets ticked off, the plan has stopped steering the work.

## A brief for a subagent or session

First decide whether to delegate at all. Delegate work that splits by context: independent research paths, separate
components, a noisy search whose output you don't need, a review that needs fresh eyes, or a job that should have
fewer permissions. Don't delegate a handful of tool calls, and don't split work by role or problem type, because each
handoff loses detail. A subagent doing the same task you'd do doesn't give a better answer, only a parallel or fresh
one.

Then find out what it will see, from the agent definition and the launch call rather than from memory. On Claude Code,
a subagent normally gets CLAUDE.md and AGENTS.md but not your conversation, the skills you loaded or the files you
read, so the brief must stand on its own. The Explore and Plan agents skip CLAUDE.md, and so does a custom agent with
`omitClaudeMd`, so restate any project rule they must follow. A fork inherits your conversation and needs only the
task. On Codex, `spawn_agent` forks the whole conversation by default, and every agent shares one workspace. Details
are in [hosts and models](hosts-and-models.md).

A fresh agent's brief needs the core parts. Keep one writer for each set of files, which matters most on Codex, where
subagents share the live workspace. If several agents can message each other, say whose messages are instructions.
GPT-6.1 Sol engages with messages from other agents more readily than earlier models. When the brief quotes another
agent's output or a web page, mark it as quoted material.

Ask for what comes back in the shape you'll use. If you'll merge several results, ask for the same small shape from
each. Otherwise a sentence like "report what you found, what you verified, and what's still open" is enough. A
subagent's mistakes come back in the same confident voice as its findings, so check its evidence before you build on
it.

## A brief for an independent reviewer

A reviewer is useful because it hasn't seen your reasoning, so keep it that way. Give it what the work is for, the
requirements or done-when, and where the raw material is: the diff or revision, the design, the captures, the logs.
Don't give it your hypothesis, the fix you prefer or the verdict you expect, and on Codex launch it without your
conversation.

Don't invent what to examine, which sources to judge against, which scenarios to walk, or which sections to report.
Those are the reviewer's job, and a capable reviewer will find questions you didn't. What the review requires is
different. If the person asked for a specific angle, such as dogfooding, name it in a sentence. If a standard, a
version or a set of cases is the requirement, give it.

Who reads the findings decides the filter. When a person will read the list, ask for everything that fails the
requirements, ranked by consequence, each marked verified (a file and line, a quote, or a way to reproduce it) or
suspected. A severity filter like "only blocking issues" makes some models hide findings that person would want
(Anthropic's Opus 5 guidance). When the next reader is a loop that must act on every finding, ask for what would block
the merge, as Anthropic's Opus 5.5 example does. A filter by kind is fine either way: "skip style" works because a
reviewer asked for problems always finds some.

For running or visual output, ask which build it looked at, whether it watched the thing move or sampled stills, and
at what size. For a design review, have it work out what the design must do from the brief before reading the
design.

Build the independence into the setup where you can: read-only tools, no way to spawn agents, and write access only to
its own report. Act on findings that change a decision, and skip nitpicks and tests for cases that can't happen.
Record each verdict with the revision the reviewer saw.

## A steer to a running agent

A steer has five parts, each usually a line:
- the problem;
- the evidence: files, commits, numbers or captures, with times;
- what it threatens: a milestone, a direction the person gave, a constraint;
- the outcome you want, as a result rather than the fix;
- where to look: the design, the research, a skill section.

Let the agent change its own plan and log why. If a milestone's meaning changes, it can commission a review of the
change and carry on while that runs.

Say whether the steer adds to the task or replaces it. Current Codex models treat a message mid-turn as steering the
active task, and drop the task only when told plainly: "Stop X. The objective is now Y." For a Codex `/goal`, editing
the goal is cleaner, because goal edits persist and are re-read. A request to look without changing anything should
say "report only, don't edit", because models with a bias to action read "can you look at…" as a request to act.

When an agent keeps circling one defect, with trial after trial on the same problem, it's usually missing research or
design, not effort. Point it at current published techniques and shipped practice, rather than asking for more
tuning. Prefer modern state-of-the-art methods, not an older one just because example code exists for it.

## When an agent misbehaves

Check the harness before the text. Plenty of "it stopped" turns out to be a budget, a timeout, a paused goal or a
background job ([why runs stop](hosts-and-models.md#why-runs-stop)). Then look at the instructions, the evidence the
agent had and its trace. The usual culprits in text are:
- a recipe where an outcome would do;
- a done it can't check;
- emphasis;
- a list it treated as mandatory;
- an "ask first" that was too strong;
- files that contradict each other;
- a rule that sat in a prompt or skill far from the moment it applied.

You can ask the agent which line made it stop or turn, and to separate what the text says from how it read it. Check
its answer against the trace, because a retrospective can invent a cause, and Sol overclaims more than Astra.

A corrective steer is a reason to look, not proof the instructions were wrong. The agent may have misread an adequate
instruction, missed evidence or simply erred, and the cause can stay unknown. Fix the immediate problem with a steer or
a goal edit. Change a goal, plan, skill or instruction file when you find a real ambiguity or omission, or when the same
failure repeats. A steer that adds a new preference needs no such fix.
