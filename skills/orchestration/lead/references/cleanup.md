# Clearing up

This covers what the build keeps on this computer outside git, and how the user clears it.

## What stays on the computer

Git holds what the project needs to build and run: code, plans, and the test data tests read. Everything else the
build makes stays on this computer, in the repository's `.git` folder, so every worktree shares one copy and the
repository doesn't grow by every capture:

- The working folder, `<git common dir>/orchestrate/evidence/`, holds builders' proof, reviews and their captures,
  handoffs, review briefs and the graded examples. Each worktree opens it at the settings' `Evidence:` path through a
  link the script makes and git ignores, so links to it work on this computer but not in a fresh clone.
- The script's clean checkouts, under `<git common dir>/orchestrate/verify/` and `main-checks/<name>/checkout/`,
  where it runs checks, merges and reviews.
- Logs: the output of each item's check, each background job, and each main-branch check run.
- The usage and result ledgers, which the [delivery history](delivery-history.md) copies after each turn. The
  history keeps a copy of every merged review too, so the record of what failed outlives the working folder.

## `cleanup`

`cleanup --worktree <repo>` lists what it would remove, by kind and size, as `WOULD_REMOVE`, and removes nothing. Show
the user that list, and run it again with `--yes` only on their yes, because nothing removed comes back. It then
prints `REMOVED`. Its `next` carries the question to put to them.

| Kind | What it removes |
|---|---|
| `evidence` | The working folder's files for milestones that are Done, and a module's design reviews once all of its milestones are Done |
| `checkouts` | The script's clean checkouts that no run is using. The next run makes them again, more slowly |
| `logs` | Saved check output, background job logs, and main-branch check logs |
| `ledgers` | Rows of the usage and result ledgers that the delivery history has already copied |
| `graded` | The graded examples file. Only when named with `--kind graded`, because it teaches later reviewers how strict the user is |

With no `--kind` it lists the first four. `--older-than DAYS` keeps anything that changed more recently, and
`--json` prints every path with its size. It never touches a module whose run lock is held, a milestone that isn't
Done, the plans, or the delivery history.

Evidence for a milestone that is Done has served its reviewer, and the delivery history keeps every review, so
removing it loses captures and handoffs, not verdicts. Offer `--older-than` when the user wants to keep recent
captures to look at.
