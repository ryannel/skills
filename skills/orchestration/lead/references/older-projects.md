# Older projects

Read this when a command stops with a message naming `migrate`. That happens in a project planned by an older
version of this set: one in the flat layout, with files such as `<MODULE>-PLAN.md` directly in the plans folder,
one with older stored names, such as `state` for a milestone's `status`, or one whose evidence is committed to git.

Run `migrate --worktree <repo>` once, adding `--to docs/plans` to move the plans folder to the standard place as well.
It moves the files into a folder per module, splits each plan's log into `LOG.md`, renames the stored names and the
settings lines whose labels changed, and merges the change. It prints `MIGRATED`, or `NOTHING` when there was nothing
to do.

After a move, start a planner with `plan --kind fix` to bring the plans into the current shape: the module table at
the top of `ARCHITECTURE.md`, milestones named for what someone can see or do, Done milestones shrunk to a line,
review briefs moved to the working folder, and plan files elsewhere converted or deleted.

## Evidence committed to git

Before 2.6.0 the script committed reviews, captures, handoffs and graded examples under the `Evidence:` folder of
the settings, `docs/evidence` by default. Now they live in the repository's working folder, outside git, because git
should hold only what the project needs to build and run, and a repository that carries every capture grows by
gigabytes. Every command refuses a project that still has committed evidence there, until `migrate` has run.

`migrate --worktree <repo>` moves it over and merges one commit. It copies each file git holds under the old folder
into the working folder, leaving the files in git and in history. It sets the `Evidence:` line to
`.orchestrate/evidence`, and moves the `Graded examples:` line with it when that named a file there. It points each
done-when file's `review`, `evidence` and handoff fields, and each record's reviews, at the new place. It rewrites
links into the old folder in every markdown file under the plans folder. Commit hashes in reviews, handoffs
and results are left as they are. An item whose `check` or wording names the old folder is listed under
`definitions_naming_it` rather than changed, because changing an item's definition starts it again: give those to a
planner as a `plan --kind fix` task. Running `migrate` again does nothing more.

A link the migration rewrote points into `.orchestrate/evidence`, which opens in every worktree on this computer but
not in a fresh clone, on CI or in a tool that lists only the files git holds, such as a docs link checker. Tell the
user that such a checker will report those links, and that the files under the old folder are still in git: taking
them out of history is a separate job, done with every run stopped, and `merge` refuses any new commit there in the
meantime. A test or check that reads a file there should have it moved to test data in the repository first.

Rewriting history gives every commit a new hash, while the records and the run state still name the old ones, so
a review of a milestone that was Ready for Review comes back INVALID. Straight after the rewrite, with every run
still stopped, run `migrate --commit-map <map> --worktree <repo>`, where the map is the `old new` list the rewrite
wrote, such as `.git/filter-repo/commit-map`. It points the records and the run state at the new hashes.

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

Older plans say "the owner", and `## Open for the owner`, for the user. They need no change, because the script
doesn't read those words.

## Ready for Review set by a builder

Before 2.1.0 a builder set its own milestone Ready for Review. A milestone in that state on the main branch, with no
record of the script's checks, is listed under `can_start`, not `ready_for_review`, and a `review` of it prints
`INVALID` with `next` naming the `run` that checks it first. Follow that `next`.

## A report a day

Before 2.4 the lead wrote a report each day to `<evidence>/build-reports/<date>.md`. Those files move to the working
folder with the rest of the evidence, and `adopt` no longer merges them. Nothing new is written there: `report` now
prints the facts when the user asks, as [the report](report.md) describes.

## No `Graded examples:` line

A project planned before the settings had a `Graded examples:` line still gives reviewers
`<evidence>/graded-examples.md` in the working folder to read, but `human accept` and `human rereview` add nothing to
it, because the script adds the user's overturned reviews only to a file the settings name. Suggest to the user that
you add the line, naming the file the project already uses, so their corrections reach later reviewers. A settings
change is committed with git on the main branch, as the lead skill says.
