# Fixing a module's plan files

The script found something wrong in a module's plan files that only a planner may fix, and your task names the
problems. Fix those and nothing else, and report any other fault you notice rather than fixing it.

Your task is one of these:

- The done-when file breaks [its format](../references/done-when.md#donejson). Fix the entries the problems name, so
  the script can read the file again.
- A milestone's items were changed outside a planner turn, so they aren't the ones last approved. If the change is
  right, keep it, rewriting the items as the skill describes, and end with `PLANNED`. If it isn't, put the approved
  items back.
- A main-branch check has failed since a commit, and the milestones merged after it fail with it. Find what in that
  commit breaks it and plan the fix before the module's unfinished milestones, or fix the plan files when the plan is
  the cause.
- The main branch has failed its test command since a commit that changed a module's files, and no builder can merge
  until it passes. Find what in that commit breaks it. When the plan is the cause, such as a check added to the test
  command before it could pass, fix the plan files. When the code is, plan the fix before the module's unfinished
  milestones, because one of them may be unable to merge before the fix does. A new milestone waits for a design
  review, so say in your report that the main branch stays broken until the fix merges, and the lead can decide
  whether to wait.
