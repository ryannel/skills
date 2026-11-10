---
name: skill-creator
description: Creates, rewrites and tests agent skills for Claude Code, Codex and other hosts. Use when someone wants to make a skill, turn a workflow into one, or improve, trim, test or fix a skill, including one that loads at the wrong times or was written for an older model. Not for a one-off prompt, a brief, or a CLAUDE.md or AGENTS.md file (prompting-agents).
license: Apache-2.0. Adapted from Anthropic's skill-creator; see LICENSE.txt.
---

# Skill creator

A skill is a folder of instructions that an agent loads when a task calls for it. Most of the time the agent
doesn't see the folder at all. At the start of a session it gets each installed skill's name and a sentence or
two of description, and it opens the rest only when a task seems to match. Use this skill to make a skill,
improve one or test one.

This skill calls the agent that loads the finished skill the reader. The reader is a capable model, such as
Claude Opus 5.5, Claude Fable 5.2, GPT-6 Astra or GPT-6.1 Sol, and on most tasks it plans as well as you do. But
it loads the skill in a session you will never see, so it can't ask what you meant. That gives a skill three ways
to fail:

- The reader never loads it, because the description doesn't match what people ask for.
- It sets out steps the reader could have planned itself. You wrote them in advance, but the reader can see the
  actual task, so its plan would fit better.
- It leaves out a fact the reader needed and had no way to guess.

The body of a skill is a prompt, so the `prompting-agents` skill, which is installed with this one, covers how to
write it: what to put in, what to leave out, the writing style, and the habits of each model. Read its
`SKILL.md` before you write or rewrite a body. This skill covers what is particular to skills: deciding what one
is for, the description, the folder, and testing.

The person is whoever asked for the skill. Many people who want one are not programmers, so use their words, and
explain a term such as "test case" or "frontmatter" the first time you need it.

## What finished means

A skill is finished when three things are true:

1. The reader loads it for the requests it is meant for, and not for neighbouring ones.
2. The reader's result is better with the skill than without it, in the person's judgement.
3. `python3 scripts/check_skill.py <skill-folder>`, run from this skill's folder, prints `ok`.

How much evidence the first two need is the person's decision, so start where they are. Someone who brings a
draft wants it tested, not an interview. A one-line fix needs the edit and the check script. Someone who says
"just write it" gets a draft to react to.

## Decide what the skill is for

First check that a skill is the right place. A skill suits a procedure or a body of knowledge that some tasks
need. A fact that every session in a repository needs belongs in `CLAUDE.md` or `AGENTS.md`. A rule that must
hold every time belongs in a hook, a test or a permission rule, because the host applies those whatever the
reader decides. A skill can carry a hook, as [structure](references/structure.md#rules-that-must-hold-every-time)
explains.

Give the skill one job. If the job is too narrow, several skills load for one task and may disagree. If it is too
broad, no description can say when to use it.

Write it from a real task. The best source is a task the person did with an agent. If this conversation holds
one, take from it the steps that worked, the file formats, the context the person had to supply, and above all
the corrections the person made, because each one is something an agent got wrong without help. The next best
source is the project's own material: runbooks, review comments, the commits that fixed mistakes. A skill
written from general knowledge ends up saying "handle errors appropriately", which the reader does anyway.

Ask the person only for what matters and what you can't find yourself. If you can't tell what the reader would
get wrong, find out. With the person's approval, run one realistic request in a fresh subagent that has no skill,
and read what it did. The gaps in that run are what the skill is for. If there are none, tell the person the
skill may not be needed.

Write down only what your source supports. A guess written into a skill becomes the reader's rule, so put each
guess to the person as a question.

## Write the description

The description is the only part of the skill the reader sees before it decides whether to load it. So the
description alone decides whether the skill is used, and everything about when to use the skill goes there, not
in the body.

Write one sentence on what the skill does, then one that starts "Use when".

- Put the main use first. A host with many skills installed cuts descriptions short, and the start survives.
- Describe what the person is trying to do, in the words they would type. Someone who wants a dashboard may say
  "chart" or "KPI page" and never say "dashboard".
- Be precise. "Use when adding or changing a migration" is right. "Use when working with databases, queries,
  models or persistence" loads the skill for every task that touches data.
- Say where the skill stops only when a neighbouring request would otherwise be sent to it: "Not for one-off
  queries (`sql-helper`)."
- Don't oversell it. Older advice made descriptions pushy, because agents used to skip skills. Current models
  take what they read more literally, and an overstated description loads the skill where it doesn't help.
  Widen a description only after a test shows the skill was missed.

[Writing](references/writing.md#the-description) has examples.

## Write the body

The body carries what `prompting-agents` says any prompt needs: the purpose, what finished looks like and how to
check it, the boundaries, and the facts the reader couldn't guess. A few things are particular to a skill.

The facts the reader couldn't guess belong in `SKILL.md`, not in a reference, because the reader won't know the
moment to go and look one up. They are what make a skill worth loading: a table that marks deleted rows instead
of removing them, or an endpoint that reports healthy while the database is down.

Match how strict each part is to how fragile that part of the work is. Where several approaches would do, give
the aim and the reason. Where there is a preferred pattern, give a template or one example. Where the work breaks
if it is done differently, give the exact command. [Writing](references/writing.md) shows the three levels, and a
whole body before and after.

Put the most important instructions first. After a long conversation is compacted, Claude Code keeps only the
start of each skill that was loaded.

Write instructions that hold for the whole task. The reader reads the skill once, at the start, so "update
`CHANGELOG.md`" gets done once, while "update `CHANGELOG.md` with every change you make" holds.

Name each other file in the folder, and say when to read or run it. The reader opens a reference only when
`SKILL.md` sends it there. Keep `SKILL.md` under 500 lines. A skill with one job and little detail needs no other
files. [Structure](references/structure.md) covers the folder, the frontmatter, references, scripts, and what each
host does differently.

Leave out a "when to use this skill" section, because by the time the reader sees the body it has already decided.
Leave out the story of how the skill was made, too.

When the draft exists, read it once as the reader would, knowing nothing else. For each line, ask whether the
reader would get something wrong without it. If not, cut the line.

## Test it

Keep a new draft out of every folder a host scans for skills until testing is done. Claude Code and Codex pick a
skill up as soon as it lands in one, so the draft would leak into the runs that are meant to go without it. When
you are changing an installed skill, copy its folder twice into a workspace outside those folders. One copy stays
untouched, as the version to compare against, and you edit the other. An installed skill is live in every session
on the machine, so an edit made in place reaches those sessions half-finished.

The test itself goes like this. [Testing](references/testing.md) has the file formats, the ways a comparison
leaks, grading, and what to do on a host with no subagents.

1. Write two or three requests the way a person would type them, with the file names and loose phrasing that real
   requests have. Show them to the person.
2. Before any run, write down what a good result must contain, as checks: statements that are plainly true or
   false. A check written after you have seen the outputs drifts towards the output you already prefer. For a
   result only a person can judge, such as writing or design, write no checks and show the person the results.
3. Run each request twice in the same turn, each time in a fresh subagent: once with the skill, and once without
   it, or with the untouched old copy when you are improving a skill. The subagents have to be fresh, because
   anything left over from this conversation hides gaps in the skill.
4. Read the transcript of each run without the skill, to make sure it really went without. An agent can load any
   installed skill by itself.
5. Show the person every result before you change anything.

One run of each shows whether the skill works at all. To choose between two versions, run each two or three
times, because the same request gives different results from run to run.

## Revise it

Fix the cause, not the test case. The skill will run on requests you will never see.

Look first for a line to remove. If every run wasted time on the same thing, find the line that sent it there. An
agent that asks too often or tests too much has usually read a caution or a reminder it didn't need.

When you add a correction, keep it narrow and give its reason. One failure is not a rule for every task.

If every run wrote the same helper script, put the script in `scripts/`, so the next run doesn't have to.

Then run the same requests again. Stop when the person is satisfied, or when the changes stop helping.

## Check it and hand it over

Run `python3 scripts/check_skill.py <skill-folder>`. It checks the frontmatter, the limits on the name and the
description, every link between the skill's files, and the contents lists on long references. These mistakes fail
without an error: a skill whose frontmatter doesn't parse still loads in Claude Code, but with no description, so
the reader never picks it. The script also prints notes, which are advice and don't fail the check.

Then put the skill where the person wants it, without its `evals/` folder, and under its old name if it replaces
one. [Structure](references/structure.md#where-skills-live) lists the folders each host reads. If you changed an
existing skill, list each thing you removed and why, so the person can put back a line you were wrong about.

If the person counts on the skill loading without being named, test the description once the skill is
installed. [Testing](references/testing.md#does-the-description-load-the-skill) says how, and what it costs.

## Which model will read it

A skill in a repository is read by every model that works there, so write for the most capable one, and read
that model's file in `prompting-agents` for the habits to write against. One difference matters for skills in
particular. On OpenAI's models, a skill's text arrives as something the user said, not as a system prompt, so
where the person's request and the skill disagree, expect the request to win.

When a new model comes out, run the skill's test cases on it without the skill. Where they pass, the model has
caught up with what the skill taught, and that part of the skill can go. Then reread the rest for lines that were
written to push an older model, as `prompting-agents` describes, and run the cases with the old version and the
new before you show the person both.

## Approvals

Get the person's approval before you start test runs, and say how many, because each run spends their quota or
money. Get it also before you replace an installed skill, install a skill where other people's agents will load
it, or publish one.
