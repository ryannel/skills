---
name: instructing-agents
description: Writes and checks the text one agent hands another, such as an Agent or Task prompt, `codex exec` or `claude -p` text, a goal, a steer or message to a running agent, a review request, a session brief, or AGENTS.md and CLAUDE.md. Use it before sending any prompt another agent will act on, even a short one, and when an agent stopped early, over-reached, meandered or ignored an instruction. Covers Claude Code and Codex. Not for writing or testing a skill (skill-creator).
---

# Instructing agents

The agent you're writing for is capable, and on most tasks at least as capable as you. It will look at the material
with fresh eyes, and it will think of questions you haven't. So your text should carry only what it can't find out
for itself: why the work matters, what finished looks like, what it mustn't do, and where things are. The rest is its
call.

Writers rarely fail by saying too little. They fail by saying how. Each list of steps, files to read, questions to
answer or report sections caps the agent at what you thought of, and makes it spend its attention on your plan
instead of the problem. One review brief listed 24 sources, 11 scenarios to walk and nine report topics, 101 lines in
all. The person it was written for said: "You're being too explicit. These models are smarter than you are. Don't
list what to look at." The 15-line rewrite is in [examples](references/examples.md#a-reviewer-brief).

## What goes in

Purpose. Say what the work is for, in a sentence or two. Intent is what lets the agent make the calls you didn't
foresee, and both Anthropic and OpenAI find models do better with the reason than with the steps.

Done. Say what has to be true at the end and what will show it: a check that passes, a measurement, a file with a
verdict in it, a reviewer's pass. Done describes where the work ends up, not what the agent does. Say what to do if
it's blocked, and make "blocked" something it can observe, like "the benchmark won't run", rather than a time limit.
When only one part is blocked, it should say so and carry on with the rest.

Boundaries. Say what it mustn't touch, what spends money or quota, what other agents or people are working on and
where, what can't be undone, and what needs a human. Take these from the project's own rules rather than inventing
them, because a brief that forbids what the project allows (pushing a verified checkpoint, say) is as wrong as one
that allows what it forbids. Then give standing permission for everything else that's safe and reversible, so it
doesn't stop to ask before running tests or making a scratch folder.

Where things are. Name where the material lives and what it's for: "yesterday's reviews and the decisions taken are
in workbench/review/". Include work that already exists on the question, and what you've ruled out, so it doesn't
redo it. That isn't a reading list. The agent decides what to open.

Check what you pass on. A brief carries your claims with the authority of a requirement. If the conversation says
"nobody has looked into this" or "the plan's first milestone is M1", look before you repeat it.

What comes back. Say where the result goes, and give any exact format a program or the next agent depends on. Beyond
that, leave the report's shape to the agent, except to ask it to keep what it verified apart from what it suspects.

Model and effort. Set them at launch, in the tool call or the command, and name them on the brief's first line.
Defaults differ between hosts and change without notice. Codex, for example, runs GPT-6.1 Sol at low effort unless
told otherwise. [Hosts and models](references/hosts-and-models.md) has the details.

## What stays out

- The method: steps, techniques, tools and their order. Give numbered steps only when the order is fragile and getting
  it wrong does damage, as in a data migration.
- What to look at: files, sources or URLs to read, questions to answer, cases to walk through, report sections. In
  Codex, `/goal` treats every item you name and every file you point to as a requirement, so a list becomes a
  checklist the agent has to clear.
- What the harness already says. Codex already tells Sol and Astra to persist, act on "can you…", test in proportion,
  write plainly and put the user above skills, and its `/goal` loop already forbids shrinking the task or finishing
  without evidence. Claude Code subagents already load CLAUDE.md. Saying it again costs attention, and a repeated rule
  gets over-applied.
- Pressure and emphasis: "be thorough", "keep going", "double-check", "think carefully", capitals. Effort is the
  control for how hard a model thinks, and current models over-apply emphasised rules.
- Your conclusion. A reviewer or investigator handed your hypothesis tends to come back agreeing with it.
- History it won't use: how the project got here, and decisions that don't bear on this task.
- Fixes for mistakes nobody has seen. Add a correction after you've watched an agent make the mistake, keep it narrow,
  and give the reason.

Two things look like lists but belong. An angle the person specifically asked for goes in as one sentence: "Also
dogfood it: think about what engineers want to do day to day, and judge whether the suite handles each." Name the
angle and don't enumerate the cases. A known blind spot of the model you're launching goes in that one brief, and not
in a shared file every model reads.

## Write from the outcome, not from an old prompt

When an earlier prompt is to hand, even one the person wrote, it's tempting to update it. That copies its lists along
with its facts. Start from purpose, done, boundaries and where things are. Then take from the old prompt only the facts
that still hold and the angles the person asked for.

Before you send it, read it as the agent will, knowing nothing else. Could it start without asking anything? Could it
tell when it's finished? Is there a line it would have followed anyway, or a list it would have produced better
itself? Cut those. A brief that runs past about 15 lines usually has a list in it that should go. It can run longer
when the extra lines are facts the agent couldn't find, like a constraint or the state of a shared branch.

## Each kind of instruction

[Kinds](references/kinds.md) covers what changes for:
- a goal for Codex or Claude Code `/goal`, and long unattended runs;
- a brief for a subagent or a new session;
- a brief for an independent reviewer;
- a steer to an agent that's already running.

[Instruction files](references/instruction-files.md) covers AGENTS.md and CLAUDE.md, which load into every session.
[Examples](references/examples.md) has a short instance of each kind, with the over-explicit draft beside it where
there was one.

## Hosts

Claude Code and Codex differ in ways that change the text. The biggest is what a new agent can already see. A Claude
Code subagent starts fresh, with CLAUDE.md but not your conversation, unless you fork it. A Codex subagent forks your
whole conversation by default, so a reviewer launched that way sees your hypothesis unless you start it without the
history. The hosts also differ in effort defaults, in how a message to a running agent is read, and in what their goal
loops enforce. [Hosts and models](references/hosts-and-models.md) covers these, and how GPT-6.1 Sol and Opus 5.5
behave. On any other host, assume nothing is inherited, and put what the agent needs in the text or in files it can
read.

## When an agent misbehaves

Check the harness before the text. Plenty of "it stopped" turns out to be a budget, a timeout, a paused goal or a
background job ([why runs stop](references/hosts-and-models.md#why-runs-stop)). Then find the line that sent it wrong.
Ask the agent which line in which file made it stop or turn, and to separate what the text says from how it read it.
The usual culprits are a recipe where an outcome would do, a done it can't check, emphasis, a list it treated as
mandatory, an "ask first" that was too strong, and files that contradict each other.

Fix the immediate problem with a steer or a goal edit. Then fix whatever let it happen, in the goal, plan, skill or
instruction file. A steer that corrects a mistake means the instructions were wrong somewhere. A steer that adds a new
preference needs no such fix.
