# Instruction files

An instruction file is a file an agent reads at the start of every session in a repository. Claude Code reads
`CLAUDE.md`. Codex reads `AGENTS.md`. Because the file is read every time, each line costs attention on every
task, including the tasks it has nothing to do with.

## What goes in

Write down what the agent can't find by reading the repository, or would have to find again every session. Two
questions decide it: could the agent find this in the code, and would it go and look? If both answers are yes,
leave the line out.

Worth a line:

- The command that runs the checks. This is the most useful line in the file.
- Facts that were never in the repository: a decision from a meeting, the environment variable the integration
  tests need, who to ask before a deploy.
- Conventions that differ from what a careful stranger would assume.
- Standing permission for a workflow you know is safe, with the reason: "The local tests use throwaway fixtures
  and can't reach production. Run them, fix failures your change caused, and run them again without asking."
- A pointer to each document and what it is for: "Use `docs/architecture.md` for service boundaries and
  `docs/database.md` for schema changes."

Add a line when the agent makes the same mistake a second time, or when you type a correction you typed last
session.

## What stays out

- The directory layout, the dependency list and an overview of the architecture. The agent reads the repository.
- "Read these three documents before every edit." For a typo fix that is wasted context. Say which document is
  for what.
- "Always run the tests." Give the command and say when it is needed.
- "Ask first" wording left over from an earlier model. Name the actions that need a go-ahead.
- A procedure with several steps. Put it in a skill, which loads only when it is needed.
- Two lines that disagree, in this file or in a nested one. Given two lines that conflict, the model picks one.

To trim an old file, check each line against these two lists.

## How to write a line

Make it concrete enough that someone could check whether it was followed.

| Vague | Checkable |
|---|---|
| "Format code properly" | "`make fmt` formats the code; CI rejects a commit that isn't formatted" |
| "Test your changes" | "`make check` runs the linter and the unit tests; run it before you commit" |
| "Be careful with the database" | "Staging shares its database with the demo environment, so don't run `make db-reset` there" |

Group related lines under a heading. Keep the file small by leaving lines out. A line that stays is a whole
sentence, with its reason where it has one. Claude Code's documentation suggests under 200 lines and says longer
files are followed less well. Codex stops adding instruction files after 32 KiB in total.

## Who reads the file

Every model that works in the repository reads the same file. Guidance written to help a smaller model can hold a
larger one back. Write the shared file for the most capable model that will read it. If one model needs a
correction, put it in the brief for that model.

## A line for one folder

A line that applies to one folder can go in an instruction file inside that folder. Claude Code loads that file
when the agent first opens a file there. Codex reads one instruction file per folder, from the repository root
down to the folder it was started in, and the nearer file wins.
