---
name: skill-creator
description: Creates, rewrites and tests agent skills for Claude Code, Codex and other hosts. Use when someone wants to make a skill, turn a workflow into one, or improve, trim, test or fix a skill, including one that loads at the wrong times or was written for an older model. Not for a one-off prompt, a brief, or a CLAUDE.md or AGENTS.md file (prompting-agents).
license: Apache-2.0. Adapted from Anthropic's skill-creator; see LICENSE.txt.
---

# Skill creator

A skill is a folder of instructions that an agent loads when a task calls for it. Use this skill to make one,
improve one or test one.

Three parties appear below. You are the agent reading this. The person is whoever asked for the skill. The reader
is the agent that will load the finished skill, in a session you will never see. A host is the program that runs
the reader and gives it skills, such as Claude Code or Codex.

The reader is a capable model, such as Claude Opus 5.5, Claude Fable 5.2, GPT-6 Astra or GPT-6.1 Sol. On most
tasks it plans at least as well as you do. But it knows only what the skill says and what it can find in the
files it opens, and it can't ask what you meant. So a skill fails in three ways:

- The reader never loads it, because its description doesn't match what people ask for.
- It tells the reader how to do work the reader would have done well alone. That holds the reader to the steps
  you thought of.
- It leaves out a fact the reader needed and could not have guessed.

## What a finished skill is

A skill is finished when three things are true:

1. The reader loads it for the requests it is meant for, and not for their neighbours.
2. The reader's result is better with the skill than without it, in the person's judgement.
3. `python3 scripts/check_skill.py <skill-folder>`, run from this skill's folder, prints `ok`.

How much evidence the first two need is the person's decision. Start where the person is. Someone who brings a
draft wants it tested, not an interview. A one-line fix to an existing skill needs the edit and the check script.
Someone who says "just write it" gets a draft to react to.

When you change an existing skill, keep its name. For more than a small fix, first copy its folder twice into a
workspace folder that no host scans for skills. One copy stays untouched, as the old version to compare against.
Edit the other, and put it in place of the installed skill when the person is satisfied. An installed skill is
live in every session on the machine, so an edit made in place reaches other sessions half-finished. When you
hand the skill back, list each thing you removed and why, so the person can restore a line you were wrong about.

Many people who want a skill are not programmers. Use the words the person uses, and explain a term such as
"test case" or "frontmatter" the first time you need it.

## Decide what the skill is

**Check that a skill is the right place for it.** An instruction works best close to the moment it applies.

| The instruction | Where it goes |
|---|---|
| Applies to one task | The prompt for that task |
| A fact needed in every session in a repository | The instruction file (`CLAUDE.md`, `AGENTS.md`) |
| A procedure or body of knowledge needed for some tasks | A skill |
| Must hold every time, with no exceptions | A hook, a test or a permission rule. The host applies these whatever the reader decides. A skill can carry one, as [structure](references/structure.md#rules-that-must-hold-every-time) explains |

**Give the skill one job.** If the job is too narrow, several skills load for one task and may disagree. If it is
too broad, no description can say when to use it.

**Write it from a real task.** The best source is a task the person did with an agent. If this conversation holds
one, take from it the steps that worked, the corrections the person made, the file formats, and the context the
person had to supply. The corrections are worth most, because each is something an agent got wrong without help.
The next best source is the project's own material: runbooks, review comments, the commits that fixed mistakes.
A skill written from general knowledge says "handle errors appropriately", which the reader does anyway.

Ask the person only for what matters and what you can't find or infer. If you can't tell what the reader would
get wrong without help, find out: with the person's go-ahead, run one realistic request in a fresh subagent with
no skill, and read what it did. The gaps in that run are what the skill is for. If there are none, tell the
person the skill may not be needed.

Write down only what your source supports. A guess written into a skill becomes the reader's rule, so put a
guess to the person as a question.

## Write the description

At the start of a session the reader sees the name and description of every installed skill, and nothing else of
them. It reads the body only after it has decided the task matches. So the description alone decides whether the
skill is used, and everything about when to use the skill goes there.

Write one sentence on what the skill does, then one that starts "Use when".

- Put the main use first. A host with many skills installed cuts descriptions short, and the start survives.
- Describe what the person is trying to do, in the words a person would type.
- Be precise. "Use when adding or changing a migration" is right. "Use when working with databases, queries,
  models or persistence" loads the skill for every task that touches data.
- Say where the skill stops only if a neighbouring request would otherwise be sent to it: "Not for one-off
  queries (`sql-helper`)."
- Don't overstate it. Older advice said to make descriptions pushy, because agents used to skip skills. Current
  models respond more strongly to what they read, and an overstated description loads the skill where it doesn't
  help. Widen a description only after a test shows the skill was missed.

## Write the body

Read [writing](references/writing.md) before you write or rewrite a body. It shows each point below at work.

**What the body carries**

- The purpose, in a sentence or two. The reader uses it to decide the cases you didn't think of.
- What finished looks like, and a check the reader can run: a test that passes, a file that validates, a
  screenshot beside the design. A reader with no check stops when the work looks finished.
- Each boundary, stated once. A boundary is something the reader must not do, or must get a go-ahead for. Name
  the exact action, put the exception inside the rule ("get a go-ahead before you run a migration"), and give the
  reason in one clause. Then say what the reader may do without asking, and name only actions the person or the
  project has cleared. Take boundaries from the project's rules and the person's words, not from caution. A skill
  supports the task the person asked for. It doesn't widen the task or grant permission the person hasn't given.
- The facts the reader couldn't guess: a table that marks deleted rows instead of removing them, an endpoint that
  reports healthy while the database is down. These are worth more than anything else in a skill.
- The format of the output, when the format matters. Mark a template as exact only when a program reads the
  output.
- Each other file in the folder, with when to read it or run it.

**What the body leaves out**

- Steps the reader would work out. Step-by-step skills helped earlier models. Keep numbered steps for work where
  the order is the point, such as a migration, and an exact command for a step that breaks if done differently.
- What the reader already knows, such as what a PDF is or how to write a loop.
- Emphasis and pressure: capitals, "IMPORTANT", "be thorough", "think hard". Current models follow a plain line,
  and emphasis makes them apply a rule too widely.
- Reminders to do what the reader does anyway. "Always run the tests" makes GPT-6 Astra and Claude Opus 5 test
  more than a change needs. Say what check this kind of change needs.
- A menu. "Use `pdfplumber`. For scanned pages, use OCR instead" gives a default. A list of four libraries makes
  the reader choose with nothing to go on.
- The same point made again, in other words or with a second example.
- A "when to use this skill" section, and the story of how the skill was made.

**How to word it**

Write the way Randall Munroe writes in "What If?", without the jokes: for a clever reader who is new to the
subject.

1. Say the main thing first. In a long conversation Claude Code keeps only the start of a loaded skill.
2. Name who does each thing. "Run the tests before you merge" makes it the reader's job. "The tests are run
   before merging" doesn't say whose job it is.
3. Explain a term before you use it, then keep using that word.
4. Use ordinary words. A technical word is fine when it is the name of the thing.
5. Tell things in the order they happen.
6. Be concrete. A path, a command, a number or one example carries more than a description of them.
7. Write whole sentences. A skill stays small because of what you leave out, not because words were dropped
   until the sentences turned into labels.
8. Say what to do. "Write in paragraphs" works better than "don't use bullet points".
9. Write instructions that hold for the whole task. The reader reads the skill once, so "update `CHANGELOG.md`"
   is done once, and "update `CHANGELOG.md` with every change you make" holds.

Keep `SKILL.md` under 500 lines. A skill with one job and little detail needs no other files. When it needs
them, [structure](references/structure.md) covers the folder, the frontmatter, references, scripts, and what
each host does differently.

Keep a new draft out of any folder a host scans for skills until testing is done. Claude Code and Codex pick a
skill up as soon as it is in such a folder, so the draft would leak into the runs meant to go without it.

When the draft exists, read it once as the reader, knowing nothing else. For each line ask whether the reader
would get something wrong without it. If not, cut the line.

## Test it

[Testing](references/testing.md) has the file formats, the ways a comparison leaks, grading, and what to do on a
host with no subagents. The outline:

1. Write two or three requests as a person would type them, with the file names and loose phrasing real requests
   have. Show them to the person.
2. Before any run, write down what a good result must contain, as checks: statements that are plainly true or
   false. A check written after you have seen the outputs drifts towards the output you already prefer. For
   results only a person can judge, such as writing or design, write no checks and show the person the results.
3. Run each request twice in the same turn, each in a fresh subagent: once with the skill, and once without it.
   When you are improving a skill, the second run uses the untouched old copy. Fresh subagents matter because
   anything left over from this conversation hides gaps in the skill.
4. Read the transcript of the run without the skill, to see that it really went without. An agent can load any
   installed skill by itself.
5. Show the person every result before you change anything.

One run of each side shows whether the skill works at all. To choose between two versions, run each side two or
three times, because the same request gives different results from run to run.

## Revise it

- Fix the cause, not the test case. The skill will run on requests you will never see.
- Look first for a line to remove. If every run wasted time on something, find the line that sent it there. An
  agent that asks too often, or tests too much, has usually read a caution or a reminder that isn't needed.
- When you add a correction, keep it narrow and give its reason. One failure is not a rule for every task.
- If every run wrote the same helper script, put the script in `scripts/` so the next run doesn't have to.

Then run the same requests again. Stop when the person is satisfied or the changes stop helping.

## Check it and hand it over

Run `python3 scripts/check_skill.py <skill-folder>`. It checks the frontmatter, the name and description limits,
every link between the skill's files, and contents lists on long references. These are the mistakes that fail
without an error: a skill whose frontmatter doesn't parse still loads in Claude Code, with no description, so the
reader never picks it. The script also prints notes, which are advice and don't fail the check.

Then put the skill where the person wants it, without its `evals/` folder.
[Structure](references/structure.md#where-skills-live) lists the folders each host reads.

If the person counts on the skill loading without being named, test the description once the skill is
installed. [Testing](references/testing.md#does-the-description-load-the-skill) says how, and what it costs.

## Which model will read it

A skill in a repository is read by every model that works there. Write for the most capable one.

| Model | In a skill, watch for |
|---|---|
| Claude Opus 5.5 | No statement of what finished means. In unattended runs it may end on a progress report |
| Claude Fable 5.2 | Cautions. It follows every one it finds, so each needless caution costs approvals and retries |
| GPT-6 Astra | Two lines that disagree, or strong "ask first" wording. It stops to ask where you wanted it to continue |
| GPT-6.1 Sol | Indirect cases. It misses some that Astra finds, and a narrow line naming the pattern helps |

[Models](references/models.md) lists what to change in a skill for each symptom, and how to move a skill to a
newer model. Read it when a skill misbehaves on one model, or when the model changes.

## What you may do without asking

Reading the person's files, researching, writing a draft, editing a skill's working copy and running the check
script need no approval.

Get the person's go-ahead before you start test runs, and say how many, because each run spends their quota or
money. Get it also before you replace an installed skill, install a skill where other people's agents will load
it, or publish one.
