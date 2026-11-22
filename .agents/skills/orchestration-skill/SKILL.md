---
name: orchestration-skill
description: Sets the rules for writing the orchestrate skills in skills/orchestration and agent_loop.py. Use when adding or changing lead, planner, builder or reviewer, or the script and its prompts. Not for the generative-media domain (media-model-skill).
metadata:
  internal: true
---

# Writing an orchestration skill

A skill in `skills/orchestration/` is finished when it works installed in any repository, in Claude Code and in
Codex, and reads as part of the set. Write it with `skill-creator`, and write its prose as `prompting-agents`
describes: the purpose, what finished looks like, the boundaries and the facts the reader couldn't guess, with a
reason beside each rule, no emphasis or pressure, and a description that says when to use the skill and doesn't
overlap a sibling's. The rules below are the ones particular to this domain.

## How it reads

Write plain prose, the way Randall Munroe explains things, without the jokes: short sentences, concrete examples,
the obvious said out loud, and the reason before or with the rule. Use a list for a real list, and not in place of
sentences. Avoid bold-led bullets, chains of semicolons, and clauses packed together to save words.

Give guidance with its reason, not hard rules, so the reader can apply it to cases the rule didn't foresee. Add
guidance only for a failure that has been seen, and leave the story of what happened out of the skill. The story
goes in the commit message, or in the domain README when it explains why the set is built the way it is. Record what
was left out on purpose in the README too.

The script is not an agent. Write "the lead runs the `plan` command", and never "the lead tells the script to plan".
Name who does each step. Call the person the agents work with "the user", and the people who use what the project
builds "end users". Stored names keep `human`, as in `human accept` and `decides: human`.

Say each thing once, close to the moment it applies. Don't explain what a capable model already knows, such as what
a worktree is, how to branch, or general testing practice.

## What a skill says, and what the script says

A skill says what the script is, which command to reach for when, and the judgement that is the agent's own: what
to decide, what to ask the user, and why. Everything about how the script works lives in the script: paths,
defaults, settings, procedures and what each result means. The agent reads it from `--help`, from a command's output
(`next`, `decides: human` with its `ask`, `warnings`, `changed`), and from the work the command does itself.

The reason is drift. Prose that copies what the script does goes wrong every time the script changes, and the
agent then trusts a skill over the script it is running. So:

- Where an agent needs a path or a setting, the skill says "`settings` prints it", once, and gives no path.
- Where a procedure is a command, the skill names the command and says when to reach for it, and leaves the steps
  to that command's help.
- A new setting goes in `SETTINGS_TEMPLATE` in `agent_loop.py`, which `settings --template` prints with each line's
  meaning and default, and in `profile()` if the script reads it.
- A new result's meaning goes in its command's entry in `COMMAND_HELP`, and the rules every result keeps go in the
  script's top-level help. `tests/orchestration/test_names.py` fails when a result the script prints isn't explained
  in the help of a command, and `test_help.py` when a command has no help of its own.
- When an agent keeps needing a fact the script doesn't give, make the script give it, in a field of the result or a
  `next`, rather than writing it into the skill.

The README is for people, and it is where the set's lifecycle is written out for someone who wants to understand it:
the statuses and who changes what, the record file, the escalation steps after a failed review, and what stays on
the computer. It points at `--help` for detail rather than copying it.

## Names

The [glossary](../../../skills/orchestration/GLOSSARY.md) holds the agreed name for each thing in the set, the names
to avoid, and the stored name where it differs, and its Statuses section lists every status with its stored name.
Read it before you write, and add an entry, marked as proposed, for any new thing you have to name. It holds names
only, so a `Stored as` line gives the field, value, command or settings line, never a path.

The glossary isn't installed, so define each name in each skill before its first use, because each skill is read
alone. The script, its files and its messages use the glossary's names too, so a stored name is the agreed name
written as a field, a value or a command, such as `ready_for_review` or `human feedback`. Give the stored name once,
where the reader will meet it. Every result the script prints is a row of the glossary's Results table, which the
names test parses. Renaming a stored name changes existing projects' files, so it goes with a step in the script's
`migrate` command that rewrites them, and the old name goes under the table's `Avoid:` line as "`OLD` (now `NEW`)".

## The set's shape

Nothing in a skill is particular to one project. Paths, commands, targets, the user's rules and the standards for a
kind of work come from the project's `ORCHESTRATE.md`, whose template `settings --template` prints.

Model and effort are set when a session starts, by the script's flags or the project settings, and saved in the
record of that session. Skills name neither, because Claude lets a skill's frontmatter override the command line.

One kind of agent writes each field of the done-when file, and the script refuses a change from anyone else. The
README's table of who changes what lists them. A change to who writes what updates that table, the skills that
write, and the script's checks.

Links stay inside the domain (`../sibling/…`), because an install flattens the domain folder.

Each folder is named for the agent that reads it: `lead` for the agent the user chats with, then `planner`,
`builder` and `reviewer`. The lead's `SKILL.md` is a router: it works out which stage the project is in, and each
stage has its own file in `lead/stages/`, numbered in order: interview, start planning, before the first build,
build. The main prompts the script sends to an agent live beside that agent's skill, in `<role>/prompts/`, and the
script reads them with `prompt_text`. Where the script knows which kind of task it is starting, as with a planner or
a reviewer, the prompt also carries that kind's instructions, read from the skill's `tasks/` folder, and the skill
keeps only what every kind shares.

Those prompts, and the shorter texts still in `agent_loop.py` (search `_TEMPLATE`), follow `prompting-agents` too. A
session's first prompt carries that session's facts: its paths, whether it is visible, which items need someone, the
user's rules. The message on a resumed turn restates the goal, because a compacted session may have lost the skill.
A boundary the script enforces needs no line in a prompt. A message about a failed review says what a review is and
where it is kept, and leaves out a list of what to fix, because a list of findings gets cleared and nothing more,
while the next reviewer starts again from the items.

The skills name `prompting-agents` wherever an agent writes for another agent: the plan files, the brief, a
`--message`, a review. They name `domain-language` wherever an agent adds or agrees a name in the project's
glossary: the orchestrate skills say when, and that skill says how. Name both as skills, not as links, because they
live outside the domain, and `install.py` installs them whenever it installs orchestrate.

The set ships skills and no agent files. The script starts each planner and reviewer as a plain session whose
prompt names its skill, and passes the host's flag that stops it starting agents of its own, so an agent file would
add nothing. The `lead` skill loads by itself, because it is the way into a project: someone describing what they
want built starts with its interview. That is safe because nothing runs for hours before the user has approved a
brief and said how they want the agents to work, and `run` refuses to start a builder until the settings'
`Builders:` line has a count.

## The script and its tests

The script is standard-library Python. A script that starts agents goes through the host adapters in
`agent_loop.py`, so that every host is handled in one place and Claude sessions get no API key.

Its tests are in `tests/orchestration/`, which isn't shipped with the skill. Run `python3 tests/orchestration/run.py`
before a commit: it runs about 600 tests in up to eight processes, in about two minutes on the user's Mac. The tests
share a fake host, a repository and the reset between tests in `tests/orchestration/support.py`. Put a new test on
`Repo` only when it needs a repository.

`tests/orchestration/prompts/` holds a saved copy of each prompt the script sends, and `test_prompts.py` fails when
a template or a file the script puts in a prompt changes. When the change is intended, write the new copies with
`ORCHESTRATE_WRITE_PROMPTS=1 python3 -m unittest tests.orchestration.test_prompts`, and read their diff.

Check a changed skill with `python3 skills/skill-creator/scripts/check_skill.py <skill-folder>`, and the repository
with `claude plugin validate .` and `npx skills add ./ --list`.
