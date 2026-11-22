# Carrying out the second review of the orchestrate set

## What this is for

The orchestrate set is in `/Users/ryannel/Workspace/skills/skills/orchestration/`: the skills `lead`, `planner`,
`builder` and `reviewer`, a `README.md` and `GLOSSARY.md` for people, and the CLI `lead/scripts/agent_loop.py`
(standard-library Python, about 16,400 lines), which builds every prompt agents read and prints each command's
`--help` from `COMMAND_HELP`.

The set follows one principle. A skill says what the tool is, which command to reach for when, and the judgement
that is the agent's own: the goal, its mandate, and the reasons. The CLI holds how things work, through its `--help`,
its JSON output (`next`, and `decides: human` with an `ask`) and the work it does itself. Agents are capable models
(Claude Opus 5.5, GPT-6.2) and need no teaching on what they already know. `lead/stages/4-build.md` is the example of
the result; read it first.

Seven reviewers each looked for one kind of mistake across every file. Their merged list is
`/Users/ryannel/Workspace/skills/workbench/orchestrate-cleanup/review2/summary.md`, and their full reports, with
file, line, quote and suggested fix for each finding, are `1.md` to `7.md` beside it. The user has approved the whole
list. Treat each report's findings as a reviewer's suggestion to check, not as an order: confirm each against the
current file and the code before you act, and skip one that turns out wrong, saying why in your final reply.

## The user's decisions

- The user's pick between options IS reviewed, as the code does today (the module's last milestone is always
  reviewed, and the pick is always last). Fix the docs that say it closes without a reviewer, and the docstrings and
  strings in the script that say so; the code's behaviour stays.
- A builder that ran on a different model or effort than the settings name: the lead reruns it as set and tells the
  user, without asking. Only when the same mismatch comes back on the rerun does the script give `decides: human`
  with the ask. And the script must name the model and effort explicitly on every launch and every turn, never
  leaving either to a host's default (details in the script part).
- The Codex note in the build prompt's `session_rule()`: cut the `yield_time_ms`, `ps`/`jobs` and `apply_patch`
  tips. Keep the browser line and the line about requests outside the sandbox, as one or two sentences.

## How to write

- Rewrite a section whole from its purpose when the cut is more than a line or two, rather than patching phrases.
  Copy across only facts that are still true.
- Plain prose, the way Randall Munroe explains things, without the jokes: short sentences, the reason with each
  rule, lists only for real lists, no bold-led bullets, no chains of semicolons.
- Guidance with its reason, not hard rules, and no stories of past failures.
- Name who does each step ("the lead runs `plan`"). The script is not an agent.
- Call the person "the user" (stored names keep `human`). Product users are "end users". Use the glossary's names,
  define each before first use in each skill, prefer the field's standard term, and say "merge", never "land".
- Say each thing once, close to where its reader needs it.
- Read `/Users/ryannel/.claude/plugins/cache/ryannel-skills/prompting-agents/1.2.2/skills/prompting-agents/SKILL.md`
  before you write; a skill body and a prompt template are prompts.

## Working in a shared checkout

Several agents are working in this checkout at once, each on its own files, listed in your part. Edit only those.
The script agents share `agent_loop.py`: one owns the code and the prompt functions, the other owns `CHANGES` and
`COMMAND_HELP`; if an Edit fails because the file changed, read the region again and redo it. Don't commit, stash,
reset, switch branches or run `git checkout` on any file: the working tree holds uncommitted work.

If your cut needs something from a file you don't own (a script change, a link to fix), say so in your final reply
rather than editing it.

## Done looks like

- Your files changed, each finding handled or skipped with a reason.
- From `/Users/ryannel/Workspace/skills`: `python3 skills/skill-creator/scripts/check_skill.py skills/orchestration/<skill>`
  prints `ok` for any skill you changed.
- Script agents: `python3 -m py_compile skills/orchestration/lead/scripts/agent_loop.py`, and the tests for what you
  changed (`python3 -m unittest tests.orchestration.<module>`). Don't regenerate the saved prompts and don't run
  the whole suite; the lead session does both at the end, once everyone is finished.

Your final reply: lines before and after per file, findings you skipped and why, anything another file's owner
needs to do, and anything you were unsure of.
