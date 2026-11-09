---
name: instructing-agents
description: Use before sending any prompt another agent will act on, even a short one, such as an Agent or Task prompt, `codex exec` or `claude -p` text, a goal, a steer or message to a running agent, a review request, or AGENTS.md and CLAUDE.md. Also use when an agent stopped early, over-reached, meandered or ignored an instruction. The check at the top is often enough for a short prompt. Not for writing or testing a skill (skill-creator).
---

# Instructing agents

## The check before you send

Before you send text another agent will act on, read it as that agent, knowing nothing else:
1. Does it say what the work is for, what done looks like and what will show it, and what to do if blocked?
2. Does it carry what the agent can't know or wouldn't think to look for? That means the boundaries from the project's
   own rules, the required scope, where the material and earlier work are, the owner's preferences, and any known
   reproduction.
3. Have you cut the procedure you invented, such as steps, reading orders, question lists, report templates,
   emphasis and your own conclusion?
4. Are model and effort set in the launch call, and recorded where the person can see them?
5. Have you checked the claims you're passing on?

Run this check on every prompt before you send it. For a short prompt the check is often all you
need; read on for a goal, a long unattended run, a reviewer brief or an instruction file. The
rest of this file explains the five.

The agent you're writing for is capable, and on most tasks at least as capable as you. Writers fail in two ways. The
common one is saying how. A list of steps, files to read, questions or report sections you made up tends to cap the
agent at what you thought of. One review brief listed 24 sources, 11 scenarios and nine report topics, 101 lines in
all. The person it was for said: "You're being too explicit. These models are smarter than you are. Don't list what to
look at." The rewrite is in [examples](references/examples.md#a-reviewer-brief). The other way is dropping a fact the
agent needed, like a quota limit or a rule the project sets, because the brief was trimmed by shape rather than by
content.

## What goes in

Purpose. Say what the work is for, in a sentence or two. The reason is what lets the agent make the calls you didn't
foresee.

Done. Say what has to be true at the end and what will show it: a check that passes, a measurement, a file with a
verdict in it, a reviewer's pass. Make "blocked" something it can observe, like "the benchmark won't run", rather than
a time limit. When only one part is blocked, it should say so and carry on with the rest.

Boundaries. Say what it mustn't touch, what spends money or quota, what other agents or people are working on, what
can't be undone, and what needs a human. Take these from the project's own rules. A brief that forbids what the
project allows (pushing a verified checkpoint, say) is as wrong as one that allows what it forbids. Then give standing
permission for everything else that's safe and reversible.

Context it can't know or wouldn't look for. Say where the material lives and what it's for, what work already exists
and what's been ruled out. Add the source or version that's authoritative, a known reproduction, a technique already
approved, and the owner's preferences. Some lists are the task, such as a compatibility matrix that must pass, the
cases the person named or the steps that reproduce a bug. Keep those whatever their shape. The line falls between
what the task requires and what you'd invent about how to do it. When Claude Code's Agent tool says to point the
agent at the files worth reading, it means naming where things are and what they're for, not setting an order to
read them in.

Check what you pass on. A brief gives your claims the weight of requirements. If the conversation says "nobody has
looked into this" or "the plan's first milestone is M1", look before you repeat it. Mark quoted output, logs or web
text as quoted, so it isn't read as instructions.

What comes back. Say where the result goes, and give any exact format a program or the next agent depends on.
Otherwise leave the report's shape to the agent, except to ask it to keep what it verified apart from what it
suspects.

Model and effort. Set them in the launch call or command, and record them where the person can see them, such as the
launch note, your message or the prompt file's header. Don't put them inside a `/goal` objective: the receiver can't
make that text true, and Codex may audit it as a requirement. What the host lets you set is in its tool schema and
launch configuration. Defaults vary by host and change without notice, as [hosts and
models](references/hosts-and-models.md) shows.

## What stays out

- An invented method: steps, techniques, tools and their order. Give steps when the order or completeness matters,
  as in a data migration.
- Reading lists, question lists and cases you made up. In Codex, `/goal` derives requirements from the objective and
  the files it points to, so a list you add can turn into a checklist. Say which material is required, which is
  evidence and which is background.
- General exhortations the harness already gives, like "persist" or "act without asking". Anything that's part of
  done is different, such as tests, scope or a quality bar. State it even if a system prompt seems to cover it,
  because those prompts change and differ between surfaces.
- Pressure and emphasis: "be thorough", "double-check", capitals. Effort is the control for how hard a model thinks,
  and current models over-apply emphasised rules.
- Your conclusion. A reviewer or investigator handed your hypothesis tends to come back agreeing with it.
- History it won't use, and fixes for mistakes nobody has seen.

When the person asks for an angle, it goes in as one sentence: "Also dogfood it: think about what engineers want to
do day to day, and judge whether the suite handles each." A known blind spot of the model you're launching goes in that
brief, not in a shared file every model reads.

## Where an instruction goes

An instruction works best close to the moment it applies, and best of all as a check that runs. An opening prompt can
carry the brief. A rule that must hold through a long run belongs somewhere it gets re-read:
- the goal itself, which Codex `/goal` re-sends on every continuation;
- a plan or status file the agent rereads;
- a steer at the point it applies;
- a hook, a test or a permission rule.

Don't count on a system prompt or a skill loaded hours ago. Attention thins as context grows. Claude Code doesn't
re-read a loaded skill each turn, and compaction can cut it short. Nobody has measured how much adherence falls with
context on GPT-6.1 Sol or Opus 5.5, but this skill went unused late in a long session even though it was loaded.

## Write from the outcome, not from an old prompt

When an earlier prompt is to hand, even one the person wrote, it's tempting to update it. That copies its lists along
with its facts. Start from purpose, done, boundaries and context. Then take from the old prompt only the facts that
still hold and the angles the person asked for.

Then run the check at the top. Ask whether there's a line the agent would have followed anyway, or a list it would have
produced better itself, and cut those. Ask whether there's a fact it couldn't have found, and put it back. For a review
brief, length is a useful warning sign, since the 101-line draft became 18 lines. For other briefs the length follows
the facts.

## Kinds, hosts and misbehaviour

- [Kinds](references/kinds.md) covers what changes for each kind of instruction:
  - a goal for Codex or Claude Code `/goal`, and long unattended runs;
  - a brief for a subagent or session;
  - a brief for an independent reviewer;
  - a steer;
  - what to do when an agent stopped early, over-reached or ignored an instruction.
- [Instruction files](references/instruction-files.md) covers AGENTS.md and CLAUDE.md.
- [Examples](references/examples.md) has a short instance of each kind.

Claude Code and Codex differ most in what a new agent can already see. A Claude Code subagent starts fresh, with
CLAUDE.md but not your conversation. A Codex subagent forks your whole conversation by default, so launch a reviewer
without the history. [Hosts and models](references/hosts-and-models.md) has the details, dated, because they move.
Check the host's tool schema and launch configuration over anything written here. On any other host, assume nothing is
inherited.
