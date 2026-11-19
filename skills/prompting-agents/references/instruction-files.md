# Instruction files

An instruction file is a file an agent reads at the start of every session in a repository: `CLAUDE.md` for
Claude Code, `AGENTS.md` for Codex. Because it is read every time, each line in it costs attention on every task,
including the many tasks it has nothing to do with. So the question for each line isn't whether it is true, but
whether it earns that cost.

## What goes in

A line earns its place when it says something the agent can't find by reading the repository, or would have to
find again every session. Two questions settle it: could the agent find this in the code, and would it go and
look? If the answer to both is yes, leave the line out.

The most useful line in most files is the command that runs the checks. After that come facts that were never
in the repository at all, such as a decision made in a meeting, the environment variable the integration tests
need, or who has to approve a deploy. Then conventions that differ from what a careful newcomer would assume. And
then a pointer to each document, with what it is for: "Use `docs/architecture.md` for service boundaries and
`docs/database.md` for schema changes."

If agents keep asking for approval on a workflow that is safe, the file is also the place to say so, with the
reason: "The local tests use throwaway fixtures and can't reach production. Run them, fix failures your change
caused, and run them again without asking." Add a line like this when you have seen the problem, not in advance.

The best time to add any line is when the agent makes the same mistake a second time, or when you find yourself
typing a correction you typed last session.

## What stays out

Most of what makes these files long is something the agent would have done or found anyway:

- The directory layout, the dependency list and an architecture overview. The agent reads the repository.
- "Read these three documents before every edit." For a typo fix, that is wasted context. Say which document is
  for what, and let the agent decide when it needs one.
- "Always run the tests." Give the command, and say when it is needed.
- "Ask first" wording left over from an earlier model. Current models follow it too widely, so name the exact
  actions that need approval instead.
- A procedure with several steps. Put it in a skill, which loads only when a task needs it.
- Two lines that disagree, whether in this file or in a nested one. Given a conflict, the model picks one, and
  you can't tell which.

To trim an old file, go through it line by line and check each one against these two lists.

## How to write a line

Write each line so that someone could check whether it was followed. "Test your changes" can't be checked; "`make
check` runs the linter and the unit tests, so run it before you commit" can. "Be careful with the database"
leaves the agent to guess what careful means; "staging shares its database with the demo environment, so don't
run `make db-reset` there" says exactly what to avoid and why.

Group related lines under a heading, and write each one as a whole sentence, with its reason where it has one.
Keep the file small by leaving lines out, not by shortening the ones that stay. Claude Code's documentation
suggests staying under 200 lines and says longer files are followed less well. Codex stops reading instruction
files once they reach 32 KiB in total.

## Who reads the file

Every model that works in the repository reads the same file, and a line written to help a smaller model can
hold a larger one back. So write the shared file for the most capable model that will read it. If one model
needs an extra correction, put it in the prompt for that model, not in the file everyone shares.

## A line for one folder

A line that applies only to one folder can go in an instruction file inside that folder. Claude Code loads it
when the agent first opens a file there. Codex reads one instruction file per folder, from the repository root
down to the folder it started in, and where two disagree, the one nearer the folder wins.
