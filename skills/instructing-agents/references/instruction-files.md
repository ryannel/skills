# AGENTS.md, CLAUDE.md and shared skills

These files load into every session, so every line costs attention on every task, relevant or not. Anthropic suggests
keeping a CLAUDE.md under about 200 lines, and OpenAI that "a short, accurate AGENTS.md is more useful than a long
file full of vague rules". When two lines contradict each other, the model may follow either.

## What belongs

Stable facts and norms the agent can't work out by reading the repository: the commands that build and check it, the
conventions, where things live, the boundaries, and what needs a human. A required check belongs here too. If done
includes `./dev check` passing, say so, because Codex's desktop prompt now skips new tests unless the repository asks
for them. What should go is vague encouragement like "run the tests", not a stated requirement.

Point to other files by when they're needed: "Use docs/architecture.md when changing service boundaries." A list of
files to read before every edit gets read every time, needed or not. A CLAUDE.md line telling Claude to read
AGENTS.md is only followed if Claude decides to open the file.

Move procedures into skills, which load only when the task needs them. Leave out architecture the agent can read for
itself, history, and incident stories.

## What to cut

- Old pushes. "Keep going" makes current Claude models over-work, and Codex already tells GPT-6 models to persist.
- Strong "ask first" wording written to stop older models over-reaching. It makes current models stop work they
  should finish. State the real boundaries once: irreversible, destructive, outward-facing, costly, or someone else's.
- Hedges like "try to" or "if possible" on a real requirement. Current models read them as permission to do less.
- One session's stumble written up as a permanent rule.
- Corrections for one model. A shared file steers every model that reads it, so a fix for Sol's blind spot belongs in
  Sol's brief.
- Emphasis on a line the agent keeps missing. If it must never bend, make it a hook, a permission rule or a sandbox.
  If it keeps being ignored, the file is probably too long.

Say which instructions win when they conflict. The user's words beat a skill's guidance, and Codex already says so.

## Layering

Codex joins AGENTS.md files from the repository root down to the working directory, and nearer files win. It stops
at 32 KiB by default. An `AGENTS.override.md` in a directory replaces that directory's AGENTS.md. Put an override next
to the work it governs.

Claude Code reads CLAUDE.md files up the tree, and AGENTS.md only when no project CLAUDE.md or CLAUDE.local.md exists
([hosts and models](hosts-and-models.md#what-a-new-agent-can-already-see)). CLAUDE.md arrives as a user message after
the system prompt, not as part of it.

## Pruning

For each line, ask whether removing it would cause a mistake you've actually seen. When an agent makes the same
mistake twice, ask it for a retrospective and fix the file. Claude Code's `/doctor prompt-audit` looks for lines
written for older models, references to files that don't exist, and files that contradict each other.

To test a line you suspect, replay one real session prompt twice from the same snapshot, once with the line and once
without, and compare the result, tool calls, tokens and time.

## Shared skills

Writing and testing a skill is `skill-creator`'s job. Two points from here apply inside one. A shared skill steers
every model that loads it, so keep corrections for one model out of it. And prose in a skill is advice, so a rule that
must hold goes in a hook, a permission rule or a script.
