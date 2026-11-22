# Review of the orchestrate set for one kind of mistake

## Why

The orchestrate set is in `/Users/ryannel/Workspace/skills/skills/orchestration/`: the skills `lead`, `planner`,
`builder` and `reviewer` (each a `SKILL.md` plus `stages/`, `tasks/`, `references/`, `prompts/`), a `README.md`
and `GLOSSARY.md` for people, and the CLI `lead/scripts/agent_loop.py` (about 16,000 lines of standard-library
Python). The script builds the prompts agents read: templates in each skill's `prompts/` folder, plus text it adds
in functions such as `needs_rules()`, `resources_rule()` and `session_rule()`, the `next`/`why`/`message` strings
in its results, and `COMMAND_HELP` (each command's `--help`). The saved copies of every prompt are in
`/Users/ryannel/Workspace/skills/tests/orchestration/prompts/`.

The set was just cleaned up on one principle. A skill says what the tool is, which command to reach for when, and
the judgement that is the agent's own: the goal, its mandate, and the reasons. The CLI holds how things work,
through its `--help`, its JSON output (`next`, and `decides: human` with an `ask`) and the work it does itself.
Agents are capable models (Claude Opus 5.5, GPT-6.2) and need no teaching on what they already know.

`lead/stages/4-build.md` is the example of the result. Read it first, and compare it with its previous version
(`git -C /Users/ryannel/Workspace/skills show HEAD:skills/orchestration/lead/stages/4-build.md`), to see the kind
of cut the user wants. Here are two things the user said about the old text:

> As long as the agent is familiar with the process and what settings exist ... then this is all wasted breath. The
> agent knows how to take instruction.

> The goal here isn't to list things the agent can do, it's to tell it the goal, give it the mandate to own the
> problem and drive that outcome.

## Your job

You look for one kind of mistake, named below, across every file in the set: all the skill files, the README and
glossary, the prompt templates, and the agent-facing text in `agent_loop.py`. Ignore the code itself, and ignore
`lead/stages/4-build.md`, which was just rewritten. Other reviewers are each looking for a different kind of
mistake, so stay inside yours.

This is read-only. Don't edit any file in the repository: the working tree holds uncommitted work, and other
sessions share it. You may run `python3 skills/orchestration/lead/scripts/agent_loop.py <command> --help` from
`/Users/ryannel/Workspace/skills`, and read the code to check what the CLI does or says. Don't run commands that
start agents or change state.

For each finding, give:

- the file and line range, with a short quote so it can be found;
- what is wrong with it;
- the fix: delete it, cut it to one sentence (give the sentence), move it to a named command's `--help` or output,
  have the script do it, or rewrite it as goal and mandate (give the gist);
- whether you checked it against the code or `--help`, and what you found.

Rank by size of win: whole sections first, single lines last. Group findings that share one fix.

Write the full report to
`/private/tmp/claude-501/-Users-ryannel-Workspace-skills/83533ccc-d83f-405b-ae66-ba7f9b3dcc39/scratchpad/review2/<pattern-number>.md`.
Your final reply should be short: the report's path, your five to ten biggest findings in a sentence each, and the
rough number of lines that would go.
