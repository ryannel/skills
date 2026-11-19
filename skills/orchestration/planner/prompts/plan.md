{task}

Use the planner skill ({skill}) for this task.

About this session:
- The `plan` command started this session, and it commits and merges the files you leave uncommitted when you end with `PLANNED`. A reviewer in a new session then reviews the design of each module that is owed one.
- The script is `python3 {loop}`. Its `check --module <M> --milestone <id> --worktree . --items-only` command tries a milestone's item checks without recording anything. It leaves out the project's test command, and runs each check under the item's lock, waiting while a builder holds it.

To finish: say what changed and any decision the human must make, then end with `PLANNED` once the files are written. The script lists the files you changed itself. If the plan should stay as it is, change no file and end with the `KEEP` line your task gives. If you can't go on, end with `BLOCKED: ...` or `NEEDS_CONTEXT: ...`. On `KEEP`, `BLOCKED` or `NEEDS_CONTEXT` the script merges no file of yours.
