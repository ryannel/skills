{task}

Use the planner skill ({skill}), which holds what every planner task shares. This task is {kind_name}, and its instructions follow.

{kind}

About this session:
- The `plan` command started this session, and it commits and merges the files you leave uncommitted when you end with `PLANNED`.
- The vision and scope document is {vision} and the module list is {architecture}, in the plans folder {plans}, if they exist.
- The project's agreed names are in {glossary}, if that file exists.{scope}
- The script is `python3 {loop}`. Its `check --module <M> --work-package <id> --worktree . --items-only` command tries a work package's item checks.

To finish, end with `PLANNED` once the files are written. The script lists the files you changed itself. If the plan should stay as it is, change no file and end with the `KEEP` line your task gives, if it gives one. If you need an answer the vision and scope document and the files don't give, end with `NEEDS_CONTEXT: <the question>`, and the lead gets it answered. If you can't go on for another reason, end with `BLOCKED: ...`. On `KEEP`, `BLOCKED` or `NEEDS_CONTEXT` the script merges no file of yours.
