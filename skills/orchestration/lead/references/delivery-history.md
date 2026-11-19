# The delivery history

This is for the lead, the agent the human chats with while it runs a build with the orchestrate set. It covers
the record of what a build cost and what went wrong, kept after the hosts' own session files are gone.

Claude Code deletes its session files after 30 days, and Codex moves or archives its own. So after every turn it
runs, the script copies the figures it needs out of that session's file: tokens by kind, model and effort, how long
the turn took, how full its context got, its tool calls, compactions, and how it ended. It keeps numbers, names and
times, and never what was said. The copy is the delivery history, in `~/.orchestrate/history/<repository>-<hash>/`,
or under `$ORCHESTRATE_HISTORY_DIR` when that is set. It lives outside the hosts' folders and outside the clone, so
deleting either leaves it in place. It also keeps a copy of each review the script counts, under
`reviews/<MODULE>/`, because the reviews themselves are in the working folder, which the human clears with
`cleanup`.

The script also reads the sessions that ran without it, each time you run `report`, `history` or `dashboard`: turns
the human started in the app, Codex auto-review threads, subagents, and the human's own sessions in the
repository. Each is tagged with the kind of agent it was and, where the ledger says, the module, milestone and
version of the script it served.

## Reading it

`history --worktree <repo> --json` brings the history up to date and prints a summary: spend by host, by kind of
agent, by model and by version of the script; every kind of error with a count and the latest ones; and the
costliest milestones. The errors are the ones worth a fix to the process: turns that failed, hit the time limit or
were stopped, errors the host reported, results the script refused, failed checks, Codex goals that hit a usage
limit, turns that ran on a model other than the one the script pinned, and failed reviews with the items they
failed, each marked when an earlier review of the same milestone failed it too.

`dashboard --worktree <repo> --open` writes the same records as one page and opens it. `--json` prints the records
the page draws, if you'd rather read them whole.

## Measuring cost

The hosts bill a plan, not each token, so no single number is the price. The history keeps three, and says which
is which wherever it shows one.

- Weighted tokens count each kind of token at its price relative to a fresh input token. A cached re-read counts a
  tenth, and an output token counts five times on Claude and eight on Codex. This is the measure that compares a
  Claude turn with a Codex turn, because cache reads make up nearly all of a raw count and cost little.
- Codex's share of the weekly limit, from the same fitted figure the `cost` command uses.
- Claude's list price, from what Claude Code records for each model. A plan doesn't charge this, but it shows where
  the Claude spend went.

## Using it

Read the summary before you propose a change to the process, so the change answers what the records show rather
than what one session suggested. Then read it again once the change has run for a while. A new version of the
script appears as its own row, with errors, time limits and compactions per hundred turns, so you can see whether
the change helped. Turns from different projects and milestones differ, so read a version's figures beside its
turn count.

Offer the dashboard when the human asks what a project cost, how a release changed things, or for a retro. Its
Retro view gathers what it cost by kind of agent, what was delivered, the costliest milestones and what went wrong.
