# Older projects

Read this when a command stops with a message naming `migrate`. That happens in a project planned by an older
version of this set: one in the flat layout, with files such as `<MODULE>-PLAN.md` directly in the plans folder, or
one with older stored names, such as `state` for a milestone's `status`.

Run `migrate --worktree <repo>` once, adding `--to docs/plans` to move the plans folder to the standard place as well.
It moves the files into a folder per module, splits each plan's log into `LOG.md`, renames the stored names and the
settings lines whose labels changed, and merges the change. It prints `MIGRATED`, or `NOTHING` when there was nothing
to do.

After a move, start a planner to bring the plans into the current shape: the module table at the top of
`ARCHITECTURE.md`, milestones named for what someone can see or do, Done milestones shrunk to a line, review briefs
moved to the evidence folder, and plan files elsewhere converted or deleted.

## Worktrees with commits from before the migration

`run` refuses a worktree with commits of its own from before the migration, and `migrate` lists each one under
`worktrees_on_old_names`. A rebase by hand conflicts in the files the renames rewrote, and those conflicts are easy to
resolve wrongly. Run `migrate --branch --worktree <its worktree>` instead, which renames its commits and rebases them
onto the main branch. It holds only that module's lock, so other modules keep building.

## The names that changed in 2.2

Version 2.2 renamed some stored names so that each says what it holds, and `migrate` renames them all in one
commit. In a done-when file, a milestone's `state` became `status`, an item's `status` became `builder_result`,
`bar` became `quality_bar`, and the counts `rounds` and `fails` became `failed_reviews` and
`failed_reviews_with_repeat`. The record file `ACCEPTED.json` became `RECORD.json`, and `accepted` in it became
`done`. The settings line `Owner decides:` became `Human decides:`.

Before 2.2 a milestone that kept failing review could get a re-plan and then a diagnosis. Now it gets one
diagnosis. `migrate` counts an earlier re-plan or diagnosis as that one, except on a milestone that was waiting
for either when it was migrated, which still gets its diagnosis.

The `owner` command is now `human`, and `--owner-rule` is `--human-rule`. The old command and flag still work, so
a lead that hasn't read the new skill yet isn't stopped.

## Files that say "the owner"

Older versions of this set called the human "the owner". A project planned by one says "the owner" in its brief,
plans, glossary and reviews, and its plan files have a section `## Open for the owner`. All of these mean the
human. They need no change, because the script doesn't read those words.

## Ready for Review set by a builder

Before 2.1.0 a builder set its own milestone Ready for Review. A milestone in that state on the main branch, with no
record of the script's checks, is listed under `can_start`, not `ready_for_review`, and a `review` of it prints
`INVALID` with `next` naming the `run` that checks it first. Follow that `next`.
