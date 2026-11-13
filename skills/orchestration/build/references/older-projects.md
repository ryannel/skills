# Older projects

Read this when a command stops with a message naming `migrate`. That happens in a project planned by an older
version of this set: one in the flat layout, with files such as `<MODULE>-PLAN.md` directly in the plans folder, or
one with older stored names, such as `claimed` for Ready for Review.

Run `migrate --worktree <repo>` once, adding `--to docs/plans` to move the plans folder to the standard place as
well. It moves the files into a folder per module, splits each plan's log into `LOG.md`, renames the stored names
and the `Integrate:` and `Check:` settings lines, and merges the change. It prints `MIGRATED`, or `NOTHING` when
there was nothing to do.

After a move, start a planner to bring the plans into the current shape: the module table at the top of
`ARCHITECTURE.md`, milestones named for what someone can see or do, Done milestones shrunk to a line, review briefs
moved to the evidence folder, and plan files elsewhere converted or deleted.

## Worktrees with commits from before the migration

`run` refuses a worktree with commits of its own from before the migration, and `migrate` lists each one under
`worktrees_on_old_names`. Its conflicts are in the files the renames rewrote, so don't rebase it by hand: in one
project the lead merged one by hand and its builder resolved the conflicts by deleting the markers. Run
`migrate --branch --worktree <its worktree>`, which renames its commits and rebases them onto the main branch. It
holds only that module's lock, so other modules keep building.

## Ready for Review set by a builder

Before 2.1.0 a builder set its own milestone Ready for Review. A milestone in that state on the main branch, with
no record of the script's checks, is listed under `ready`, not `review_owed`, and a `review` of it prints `INVALID`
with `next` naming the `run` that checks it first. Follow that `next`.
