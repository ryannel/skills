---
name: orchestration-skill
description: Authoring spec for the orchestration domain (skills/orchestration). Use when adding or changing a skill, agent file or script in that domain. Not for the generative-media domain (media-model-skill).
metadata:
  internal: true
---

# Writing an orchestration skill

A skill in `skills/orchestration/` is finished when it works installed in any repository, in Claude Code and in
Codex, and reads as part of the set. Write it with `skill-creator`, and write its prose as `prompting-agents`
describes: the purpose, what finished looks like, the boundaries and the facts the reader couldn't guess, with a
reason beside each rule, no emphasis or pressure, and a description that says when to use the skill and doesn't
overlap a sibling's. The rules below are the ones particular to this domain.

Write plain prose, the way Randall Munroe explains things, without the jokes: short sentences, concrete
examples, the obvious said out loud, and the reason before or with the rule. Use a list for a real list, and not
in place of sentences. Avoid bold-led bullets, chains of semicolons, and clauses packed together to save words.

Use the set's names. The [glossary](../../../skills/orchestration/GLOSSARY.md) holds the agreed name for each
thing in the set, the names to avoid, and the stored name where it differs. Read it before you write, and add an
entry, marked as proposed, for any new thing you have to name. The glossary isn't installed, so define each name
in each skill before its first use, because each skill is read alone. The script, its files and its messages
use the glossary's names too, so a stored name is the agreed name written as a field, a value or a command, such
as `ready_for_review` or `owner feedback`. Give the stored name once, where the reader will meet it.
[The done-when reference](../../../skills/orchestration/plan-module/references/done-when.md#statuses-and-their-stored-names)
holds the full table of statuses and their stored names. Renaming a stored name changes existing projects' files,
so it goes with a step in the script's `migrate` command that rewrites them.

The script is not an agent. Write "the lead runs the `plan` command", and never "the lead tells the script to
plan". Name who does each step.

Nothing in a skill is particular to one project. Paths, commands, targets, the owner's rules and the
standards for a kind of work come from the project's `ORCHESTRATE.md`
([template](../../../skills/orchestration/plan-module/references/profile.md)). If a skill needs a new setting, add
it to the template, and to `profile()` in `agent_loop.py` if the script reads it.

Model and effort are set when a session starts, by the script's flags or the project settings, and saved in
the record of that session. Skills and Claude agent files name neither, because Claude lets that frontmatter
override the command line.

One kind of agent writes each field of the done-when file, as the table in
`plan-module/references/done-when.md` lists. A change to who writes what updates that table, the skills that
write, and the script.

Links stay inside the domain (`../sibling/…`), because an install flattens the domain folder.

The prompts the script sends, such as the build, plan and review templates in `agent_loop.py`, are prompts like
any other, and follow `prompting-agents` too. The skills name `prompting-agents` wherever an agent writes for
another agent: the plan files, the brief, a `--message`, a review. Name it as a skill, not as a link, because it
lives in another domain, and `install.py` installs it whenever it installs orchestrate.

Scripts are standard-library Python, with tests in `tests/orchestration/`, which are not shipped with the
skill. Run `python3 tests/orchestration/run.py` before a commit. It runs them in up to eight processes and takes
about 70 seconds on the owner's Mac; `python3 -m unittest discover tests/orchestration` runs the same tests in one
process, in about seven minutes. The tests share a fake host, a repository and the reset between tests in
`tests/orchestration/support.py`; put a new test on `Repo` only when it needs a repository. A
script that starts agents goes through the host adapters in `agent_loop.py`, so that every host is handled in one
place and Claude sessions get no API key.

Agent files for Claude live in `build/agents/claude/` and are listed in the marketplace entry. The Codex
copies live in `build/agents/codex/` and are installed by `install_agents.sh`. The script and the installer use
the files' names, so keep the names.

Add a line only for a failure that has been seen, and say what happened. Record what was left out on purpose
in the domain README.

Check the result with `python3 skills/agent-writing/skill-creator/scripts/check_skill.py <skill-folder>`,
`claude plugin validate .` and `npx skills add ./ --list`.
