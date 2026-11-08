---
name: instructing-agents
description: Writes and audits instructions that Claude Code or Codex agents act on, such as a goal or /goal condition, a steer to a running thread, a brief for a subagent, session or reviewer, an agent-facing plan, or AGENTS.md and CLAUDE.md. Use when drafting or revising these for Claude (Opus 5.5) or OpenAI (GPT-6 Astra, GPT-6.1 Sol), or when diagnosing why an agent stopped early, over-reached, meandered or ignored an instruction. Not for building, packaging or evaluating a skill's mechanics (use skill-creator), or for ordinary documentation.
---

# Instructing agents

**Outcome:** instructions a capable agent can act on without stopping to ask, and without being boxed in. It knows:
- what finished looks like, and how to prove it;
- what it may and may not touch;
- where to look.

It chooses the method.

Current models are strong, and both vendors now warn that some older habits hurt them. Start minimal, and add a line
only to correct a failure you have seen. Keep that correction narrow, put it where it applies, and say why it's there.
[Models](references/models.md) says which vendor warns against which habit, and how each model differs.

## The core

- **Outcome, done, constraints, pointers.** Say what must exist or be true at the end and the evidence that proves it.
  Then say what must not change and where the material is. Prescribe steps only where order or completeness matters,
  such as a fragile sequence or a migration; give heuristics where many approaches work.
- **Define completion before work starts.** Done is evidence the agent can produce: an exit code, a test, a capture, a
  measured figure, a reviewer's verdict. Include a stop rule for when the agent is blocked or out of budget. Hitting the
  budget isn't completion.
- **Give the reason with the rule.** Models generalise from the reason. "Avoid ellipses because a text-to-speech
  engine reads this" beats "NEVER use ellipses".
- **Write plainly.** Strong emphasis tends to make current models over-apply a rule or over-trigger. A rule that must
  never bend belongs in a hook, permission rule or sandbox.
- **State the scope and the ambition.** Filters such as "only report critical issues" are taken literally and suppress
  findings, so ask for everything, ranked, and filter afterwards. Say how far to go and what's out of scope.
- **Grant standing permission for safe work.** Name the reversible, local actions the agent may take without asking.
  Reserve questions for decisions that are irreversible, destructive, outward-facing, spending money or changing
  direction.
- **Point to material by use.** Write "Use architecture.md for service boundaries", not "read these three files before
  every edit".
- **Keep state outside the context.** Long work needs a spec, a plan and a short status in files the agent re-reads.
  They survive compaction, and they let you see progress.
- **Ask for honest claims.** Keep verified, approximate, unverified and blocked separate, and never call a proxy the
  real thing.

Whether to push an agent to persist depends on the model and harness, and the vendors disagree. See
[models](references/models.md#persistence-by-model-and-harness) before adding any "keep going" or "carry on" line.

## Routes

- [Goals and briefs](references/goals-and-briefs.md): a goal or long prompt, an unattended run, a plan, a steer, a
  brief for a subagent or session, or a reviewer brief.
- [Examples](references/examples.md): one worked example of each, to copy the shape from.
- [Skills and instruction files](references/skills-and-instruction-files.md): a skill's content and description, or
  AGENTS.md and CLAUDE.md.
- [Models](references/models.md): per-model behaviour, persistence, effort, and the harness stop causes to rule out.
- [Sources](references/sources.md): where each claim comes from.

## Auditing instructions when an agent misbehaves

Rule out the harness first ([stop causes](references/models.md#harness-stop-causes)); then read the instructions
before writing more. Look for:
- recipes where an outcome would do;
- missing or unverifiable done criteria;
- emphasis, or ALWAYS/NEVER without a reason;
- review gates or strong "ask first" lines that stop the agent early;
- mandatory reading lists;
- generic "keep going", "be thorough", "think carefully" or "double-check" lines;
- filter words in review prompts;
- contradictions between skills, AGENTS.md and the prompt;
- corrections written for one model sitting in files that every model reads.

Ask the agent to name the exact file and line that made it pause or diverge, and to separate what the text requires
from its own interpretation. When a model changes, re-test the scaffolding. Each piece assumes something the model
can't do alone, and that assumption may no longer hold.

Steering a running agent is covered in [goals and briefs](references/goals-and-briefs.md#a-steer-to-a-running-agent).
Every steer is a symptom: after it, fix whatever in the goal, plan, skill or method let it happen.
