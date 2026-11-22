# Audit of the orchestrate skills: what belongs in the CLI, not the skills

## The goal

The orchestrate set lives in `/Users/ryannel/Workspace/skills/skills/orchestration/`: four skills (`lead`, `planner`,
`builder`, `reviewer`), each with `SKILL.md` plus `stages/`, `tasks/`, `references/` and `prompts/`, and a
`README.md` and `GLOSSARY.md` for people. The skills drive a CLI, `lead/scripts/agent_loop.py` (about 15,700 lines of
standard-library Python), which starts builders, reviewers and planners, keeps records, merges, checks and cleans up.
The prompts it sends are templates inside `agent_loop.py` (search for `_TEMPLATE`), plus the `prompts/` folders.

The user who owns the set thinks the skills duplicate a lot of writing that belongs with the CLI: defaults,
settings, file locations and how they are overridden, and step-by-step mechanics of what the script does. That
prose goes stale every time the script changes. The target is:

- A skill tells its agent that the tool exists, how to find it, what it does at a high level, which command to
  reach for when, and the judgement that is genuinely the agent's (what to decide, what to ask the user, why).
- The CLI holds how it works. Paths, defaults and overrides come from the CLI's output (the user suggests a
  settings file the CLI reads, and a command that tells agents exactly where everything is). Procedures the script
  could carry out itself should be done by the script. What an agent needs to know to use a command goes in that
  command's `--help` or in its output (many commands already emit JSON with a `next` field telling the lead what to
  do next).
- Skills don't teach a capable model what it already knows, such as what a git worktree is, how to branch, or
  general testing practice.

Examples the user gave:

- `lead/references/cleanup.md` is a whole file, but cleanup is a CLI command (`cleanup`); its `--help` could teach
  most of it.
- `lead/references/settings.md` is a red flag.
- `lead/stages/4-build.md` says "Give each module its own worktree on its own branch, in a folder git ignores. A
  worktree is a second working copy of the repository, so two builders can work at once. If the repository ignores
  no folder, add one to .git/info/exclude. With Merge: push, branch from the remote: `git worktree add -b
  build/<module> <folder>/<module> <remote>/<branch>`. With Merge: local, branch from the local main branch." The
  script should do this, and the skill shouldn't explain worktrees.

## Your job

Read-only. Don't edit any file in the repository: the working tree holds uncommitted work, and other sessions share
it. Read files as they are on disk. You may run `python3 skills/orchestration/lead/scripts/agent_loop.py <command>
--help` (from `/Users/ryannel/Workspace/skills`) and read the script's code to check what the CLI already does or
says. Don't run commands that start agents or change state.

For each finding, record:

- the file and line range, and a short quote (one line) so it can be found;
- what the passage does (describes a path, a default, a procedure, general knowledge, duplicates X…);
- where it should go: script behaviour (the script does it), command output (the script reports it, e.g. a new or
  existing JSON field), `--help` of a named command, a settings file the CLI reads, delete outright, or keep in the
  skill (say why it is the agent's judgement);
- whether the CLI already does or says it, with the function or help text you checked. This matters: a passage
  whose content the CLI already covers can simply go, while one that needs new script work is a bigger change.

Rank by size of win: whole files or long passages that can go first, one-liners last. Group findings that share a
fix (e.g. "every passage describing evidence paths" → one `paths` command).

Write your full report to `/private/tmp/claude-501/-Users-ryannel-Workspace-skills/83533ccc-d83f-405b-ae66-ba7f9b3dcc39/scratchpad/audit/<your-name>.md`.
Your final reply should be short: the path to the report, your five to ten biggest findings in a sentence each,
and any CLI changes the findings depend on (new commands, new output fields, new settings), since those decide the
order of the cleanup.
