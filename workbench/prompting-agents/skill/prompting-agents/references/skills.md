# Skills

A skill is a folder with a `SKILL.md` file in it. Claude Code, Codex and other agents read the same format. A
skill is a prompt that is stored and loaded when a task needs it, so everything in the main file applies. This
file covers what is different.

Contents: [How a skill is loaded](#how-a-skill-is-loaded) · [What a skill is made from](#what-a-skill-is-made-from)
· [The description](#the-description) · [The body](#the-body) · [Other files in the folder](#other-files-in-the-folder)

## How a skill is loaded

1. At the start of every session, the agent sees the name and description of every installed skill. It sees
   nothing else of them.
2. When a task matches a description, the agent reads that skill's `SKILL.md`.
3. `SKILL.md` names other files in the folder. The agent reads one when `SKILL.md` tells it to.

Three things follow, and most of the advice below comes from them.

- Only the description decides whether the skill is used.
- Once loaded, `SKILL.md` stays in the conversation and takes the agent's attention on every turn. The agent does
  not read it again. In Claude Code, after a long conversation is compacted, only the first 5,000 tokens of the
  skill are kept.
- The other files cost nothing until the agent reads them.

## What a skill is made from

Write a skill from a real task: the steps that worked, and above all the corrections the person had to make. A
skill written from general knowledge comes out as "handle errors appropriately", which the agent already does.

Give a skill one job. If the job is too narrow, several skills load for one task and may disagree. If it is too
broad, no description can say when to use it.

## The description

Write one sentence on what the skill does and one on when to use it. Put the main use first, because a host with
many skills installed cuts descriptions short, and the start is what survives.

- Describe what the user is trying to do, in the words a user would use.
- Say precisely when to use it. "Use when adding or changing a migration" is right. "Use when working with
  databases, queries, models or persistence" makes the agent load the skill for every task that touches data.
- Where a neighbouring skill exists, say where this one stops: "Not for one-off queries (use `sql-helper`)."
- Everything about when to use the skill goes here. A "When to use this skill" section in the body is read after
  the decision has been made.
- Don't make the description pushy. Older advice said to, because agents used to skip skills they should have
  used. Current models respond more strongly to what they read, and an overstated description loads the skill
  where it doesn't help. Widen a description only after you have seen the skill missed.

The description may be at most 1,024 characters; most good ones are well under half that. The name is lowercase
letters, numbers and hyphens, at most 64 characters. The frontmatter fields that work on every host are `name`
and `description`, plus optional `license`, `compatibility`, `metadata` and `allowed-tools`. If the frontmatter
is not valid YAML, the skill loads with no description and is never chosen, and no error is shown.

## The body

**Put what matters most first,** because the top of the file is what survives compaction.

**Add what the agent lacks.** For each line ask: would the agent get this wrong without it? The lines worth most
are facts that defy a reasonable guess: a table that marks deleted rows instead of removing them, an endpoint
that reports healthy while the database is down. Keep these in `SKILL.md`, because the agent won't know the
moment to go and look them up.

**Leave out the recipe.** Step-by-step skills helped earlier models. Current ones are limited by them to the
steps you thought of. Keep steps for the parts where the order is the point.

**Write standing instructions.** The agent reads the skill once. "Run the tests" is done once. "Run the tests
after every edit" holds for the task.

**Match strictness to how fragile the step is.** Where several approaches work, say what to aim for and why.
Where a step breaks if done differently, give the exact command and say not to change it.

**Give a default.** "Use `pdfplumber`. For scanned pages, use OCR instead." A list of four libraries makes the
agent choose with nothing to go on.

**Teach the method.** A skill should work on the next task of its kind, so write how to approach the class of
problem. An exact answer to one case helps once.

**Show the output format** with a template when the format matters. Mark it as exact only when a program reads
the output.

Keep `SKILL.md` under 500 lines.

## Other files in the folder

- `references/` holds detail that only some tasks need. In `SKILL.md`, say when to read each file: "Read
  `references/api-errors.md` if the API returns a status other than 200." Link each reference straight from
  `SKILL.md`, because a file reached only through another reference may be skimmed. Give a reference over 100
  lines a list of contents at the top.
- `scripts/` holds code the agent runs. In `SKILL.md`, say what each script does and whether the agent should
  run it or read it.
- `assets/` holds files that go into the output, such as templates.
- Leave out a README, a changelog and notes on how the skill was made. The folder is for the agent doing the job.
