---
name: instructing-agents
description: Writes and audits instructions Claude Code or Codex agents act on, such as goals, steers, briefs for subagents, sessions or reviewers, and AGENTS.md or CLAUDE.md. Use when drafting these, or when an agent stopped early, over-reached, meandered or ignored an instruction. Not for writing or testing a skill (skill-creator).
---

# Instructing agents

Good instructions let a capable agent get on with the job without stopping to ask, and without boxing it in. The
agent should know three things: what finished looks like and how to prove it, what it may and may not touch, and where
to find what it needs. How to do the work is its call.

Today's models are strong, and both Anthropic and OpenAI now warn that some old prompting habits make them worse. So
start with as little as you can. Add a line only when you've seen the agent get something wrong, keep that line
narrow, put it where it applies, and say why it's there. [Models](references/models.md) says which vendor warns
against which habit, and how the models differ.

## The core

Say what has to be true at the end, and what evidence proves it. Then say what mustn't change, and where the material
is. Only spell out steps when the order really matters, like a fragile migration. Where many approaches would work,
give a rule of thumb and let the agent choose.

Decide what "done" means before the work starts. Done should be something the agent can show you: a passing test, an
exit code, a screenshot, a measured number, or a reviewer's verdict. Also say what to do when it gets stuck or runs
out of budget. Running out of budget isn't the same as finishing.

Give the reason along with the rule. Anthropic says models generalise from reasons, and OpenAI says to define
completion and where to stop, rather than the steps. "Don't use ellipses, because a text-to-speech
engine will read this aloud" works better than "NEVER use ellipses", because the model can work out the cases you
didn't list.

Write plainly. Capital letters and strong emphasis make current models over-apply a rule, or apply it where it doesn't
belong. If a rule truly must never bend, don't rely on wording at all: put it in a hook, a permission rule or a
sandbox.

Say how far to go, and what's out of scope. Models take filters literally. In the owner's experience, a reviewer told
to "only report critical issues" hides things you'd have wanted to know, so ask for everything, ranked, and do the
filtering yourself. A filter by kind is different: Claude Code's own reviewer prompt says to skip style, because a
reviewer asked to find problems always finds something.

Tell the agent which safe, reversible, local actions it can take without asking. Save questions for things that are
hard to undo, destructive, visible to other people, cost money, or change direction.

Point to material by what it's for. "Use architecture.md for service boundaries" is better than "read these three
files before every edit", because the agent reads it when it needs it, not every time.

For long work, keep the state in files: a spec, a plan and a short status the agent re-reads. Files survive when the
context gets compacted, and they let you see progress without asking.

Ask for honest claims. The agent should keep what it verified apart from what it thinks is roughly right, what it
hasn't checked, and what's blocked. A stand-in is never the real thing, and the agent should say which one it used.

Whether to tell an agent to keep going depends on the model and the harness, and the vendors disagree. Read
[models](references/models.md#persistence-by-model-and-harness) before adding any "keep going" or "carry on" line.

## Where to look next

- [Goals and briefs](references/goals-and-briefs.md) covers goals and long prompts, unattended runs, plans, steers,
  and briefs for subagents, sessions and reviewers.
- [Examples](references/examples.md) has one worked example of each, to copy the shape from.
- [Skills and instruction files](references/skills-and-instruction-files.md) covers AGENTS.md and CLAUDE.md, and
  the two points about skills that belong here. Writing a skill itself is `skill-creator`'s job.
- [Models](references/models.md) covers how each model behaves, persistence, effort, and the harness problems to rule
  out first.
- [Sources](references/sources.md) says where each claim comes from.

## When an agent misbehaves

Check the harness first, because a lot of "the agent stopped" turns out to be a timeout or a limit
([stop causes](references/models.md#harness-stop-causes)). Then read the instructions it was given before you write
any more. These are the usual culprits:
- a recipe where an outcome would have done;
- no definition of done, or one the agent can't check;
- emphasis, or ALWAYS and NEVER with no reason given;
- review gates or strong "ask first" lines that make it stop early;
- lists of files it must read every time;
- vague lines like "keep going", "be thorough", "think carefully" or "double-check";
- filter words in a review prompt;
- the skill, AGENTS.md and the prompt contradicting each other;
- a fix written for one model, sitting in a file every model reads.

Ask the agent which exact file and line made it stop or go off course, and to separate what the text actually says
from how it read it. When you switch models, re-test your scaffolding. Each piece exists because of something an
older model couldn't do alone, and the new one might be able to.

Steering an agent that's already running is covered in
[goals and briefs](references/goals-and-briefs.md#a-steer-to-a-running-agent). A steer that corrects a mistake is a
symptom: once it's sent, fix whatever in the goal, plan, skill or method let the mistake happen. A steer that adds a
new preference needs no fix.
