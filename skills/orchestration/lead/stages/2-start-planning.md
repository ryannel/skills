# Start planning

This stage runs when there is an approved brief and no plan yet, and again whenever the user asks for something new
or changes their mind. The planner can't ask the user anything, so it works from the brief alone.

The `plan` command refuses a working copy with uncommitted files, so put the brief on the main branch first. In a
repository with no `ORCHESTRATE.md`, commit it with git. In one that has it, run
`adopt --worktree <repo> <plans folder>/BRIEF.md`, which commits and merges that one file.

Then run `plan --worktree <repo> --task "<what the user asked for, in their words>"`, adding "The project brief is
<path>." when there is one. The planner writes the project settings and the first plan, and the command goes on to
the design reviews.

The same holds later, when the user asks for something new or changes their mind. Add their words to the brief
with the date, change the decisions their words affect, merge it with `adopt`, and run `plan` with their words as
the task. A change of mind doesn't count as a failed review. The changed milestones are built and reviewed again.

When the user wants one kind of agent set differently on a new project, such as "plan with Fable", put their words
in the planner's task and pass the matching `--model` or `--effort` on that first `plan`.

When `plan` has finished, check where the project stands again. A first plan leaves the settings without a
`Builders:` count, so the next stage is [before the first build](3-before-first-build.md).
