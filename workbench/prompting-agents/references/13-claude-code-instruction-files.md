# Claude Code docs: CLAUDE.md and AGENTS.md (the memory page)

- URL: https://code.claude.com/docs/en/memory
- Read in Chrome on 2026-11-10 (the sections on when to add, writing effective instructions, AGENTS.md, and
  troubleshooting). Paraphrased.

## What CLAUDE.md is

- It is delivered as a user message after the system prompt. It is context, "not enforced configuration". The
  model tries to follow it; nothing guarantees it, least of all for vague or conflicting lines.
- A rule that must happen at a fixed point (before every commit, after each edit) belongs in a hook. A hook runs
  as a shell command on its event whatever the model decides.

## When to add a line

- The model made the same mistake a second time; a review caught something it should have known about this
  codebase; you typed the same correction you typed last session; a new teammate would need the same context.
- Keep to facts needed in every session: build commands, conventions, layout, standing rules. A multi-step
  procedure, or something that matters for one part of the codebase, goes in a skill or a path-scoped rule.

## Writing lines that get followed

- Concrete enough to verify: "Use 2-space indentation", not "format code properly". "Run `npm test` before
  committing", not "test your changes". "API handlers live in `src/api/handlers/`", not "keep files organized".
- Under 200 lines per file. Longer files use more context and are followed less. Imports organise a file but do
  not reduce its cost.
- Group related lines under headings and bullets.
- Two lines that contradict each other: the model may pick either. Review nested files and rules for conflicts.
- `/doctor` proposes trims: cut what the model can derive from the codebase (directory layout, dependency lists,
  architecture overviews); keep pitfalls, rationale, and conventions that differ from the default.
- `/doctor prompt-audit` reports instructions written for older models, references to files or commands that
  don't exist, and files that contradict each other, across CLAUDE.md, AGENTS.md, rules, skills, commands,
  subagents and output styles.

## AGENTS.md in Claude Code

- By default Claude Code reads AGENTS.md only when there is no CLAUDE.md, `.claude/CLAUDE.md` or `CLAUDE.local.md`
  in the working directory or above it. A setting ("Project instructions") can load both.
- It does not read `AGENTS.override.md` or anything under `.agents/`. (Codex reads both.)
- To share one file between tools, a CLAUDE.md can import the AGENTS.md.
- Subagents that start without project instructions (the built-in Explore and Plan agents) start without these
  files too.
