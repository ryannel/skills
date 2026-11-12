# Orchestrate improvement plan, 2026-11-12

This plan says what to change in the orchestrate set next, in what order, and why. It comes from three passes
over the project Thrum on 10–12 November, written up in `thrum-harness-audit-2026-11-12.md` in this folder. A
code such as C2 or P4 names a finding in that file: C, F and L are the first pass, N the second and P the third.

On the night of 12 November the owner asked for every release to ship at once, so releases 1 to 6 were all built
into 2.1.0 rather than the versions named below. The test suite was reworked in the same change, as
`test-suite-plan-2026-11-12.md` in this folder describes. What each release's agent left undone, or did
differently from this plan, is listed under "Where the build differs from this plan" at the end.

The plan uses the names in the set's glossary, `skills/orchestration/GLOSSARY.md`. Two names here aren't in it.
The usage ledger is the file `<git common dir>/orchestrate/usage.jsonl`, where the script writes one row for each
agent turn with the tokens it used. A rollout file is the log Codex keeps of a session, one per session, in
`~/.codex/sessions/`. A field, option or result that the script doesn't have yet is marked as proposed where it
first appears.

## What the changes are for

The passes found four costs.

Tokens are the largest. A builder whose session is nearly full re-reads it on every step, and in Thrum one such
builder used 16 million input tokens in 42 minutes (P2). The usage ledger can't say how large the cost is. It
counts Codex's cached tokens about 83% too high (C2), and it records nothing for a turn that the script stops at
the turn limit, which lost about 61 million tokens for one milestone (P4).

Review rounds are lost to problems that aren't in the work. A reviewer couldn't reach the Mac's screen (F1). A
builder proved items on a build of an older commit (N1). A reviewer didn't know the script had already run the
checks, and ran them again for 35 minutes (P3).

The owner's time is spent on things that don't need them. One afternoon the owner spent at the Mac was wasted (N1).
About 28 of the 30 lines under "Waiting on you" on the status page were choices the planner had already made (L5).
The lead asked the same question about `migrate` eight times (N6).

The owner was told wrong things. The lead couldn't see what a run was doing, so it guessed, and three of its
guesses in one morning were wrong (N5). The main branch held a milestone marked Ready for Review for three hours
after the script's checks had failed it (N2).

These changes have worked if, in the next pass over a project:

- the usage ledger is within 5% of the hosts' own totals;
- no builder turn starts with its session more than 60% full;
- no failed round's only finding is about access;
- nothing on the main branch is Ready for Review without the script's checks having passed;
- "Waiting on you" has five lines or fewer.

## What is already fixed

2.0.0 and 2.1.0 already answer these findings, so no release below repeats them.

- A builder waits for a long job with the script's `background` and `wait` commands instead of polling it with
  `sleep` and `tail` (C1), and lists its jobs with `jobs` instead of `ps` (part of F7).
- A resumed builder is told its last commit, the items that passed and its running background jobs (C4).
- A builder is told not to keep proof drivers in `tmp/` (F5), and on Codex to edit with `apply_patch` (F6).
- Every result names the script's version, and warns when a newer copy is installed (L1).
- A turn the script stops at the turn limit no longer counts as a failed turn (part of F2, and P5).
- `merge` lists the files a rebase brought in, so a builder re-proves only the items they affect (C6).
- Each result is also written to a file under `<git common dir>/orchestrate/results/` (part of L2).
- An item that needs the owner at the machine is proved after the last merge, on a build of the merged commit,
  and a builder never rebuilds an older commit to match earlier evidence (N1).
- The script's results and fields use the glossary's names, and a test fails when one drifts. `FLOOR`, the result
  the lead misread as "likely quota" (P3), is now `HOST_FAILED` when the host failed and `SCRIPT_FAILED` when the
  script couldn't do a step of its own.

## What was checked in the code

These were read in the uncommitted 2.1.0 `agent_loop.py`:

- `usage_of` adds up Codex's `turn.completed` figures as they arrive. A turn that exits 124, which is the exit
  code the script uses when it stops a turn at the turn limit, records only `incomplete_turns`. Nothing in the
  script reads the rollout file's `token_count` events.
- A `token_count` event holds the session's running total (`total_token_usage`), the size of the last request,
  which is how full the session is (`last_token_usage`), and the session's limit (`model_context_window`). This
  was read in one local rollout file, not one of Thrum's.
- `cmd_run` starts a new session only for `--fresh`, a new milestone, or a change of host, model or effort. It
  never looks at how full the session is or which version of the script started it.
- `ready_problems` requires the builder's commit to be on the main branch before it runs the item checks, so N2
  is how the script is built today, not a slip. `land`, the function behind the `merge` command, runs the test
  command in the builder's worktree while it holds the `merge` lock, and the script then runs it again in its
  clean checkout (N4).
- The builder runs `merge` from inside its own session, so anything `merge` runs is inside the builder's sandbox.
- `check_failures` joins a check's stdout and stderr and keeps the last 30 lines (N3).
- `review_once` checks the milestone's status and its items, but not that the script ran its checks (P3).
- `browser_needs` reads every open milestone of every module (N8).
- `status_page` puts every assumption line under "Waiting on you" (L5).
- Nothing reads the `Builders:` line of the project settings (F3).
- `cmd_migrate` refuses while any run holds a lock (N6).
- The script writes the status page in a commit of its own on purpose, so that a failure there can't lose a
  record (C7).

These are inferred and not yet checked. The passes' figures suggest that Codex's `turn.completed` counts are
running totals for a resumed session (C2), but release 1 doesn't depend on it. A search found nothing that stops
a turn whose tool call has hung, but `HeadlessWatch` wasn't read in full. The reviewer seems to have no ending
like the builder's for items that need access, from a search of `review_once` only. The last assistant message of
a Claude session is assumed to give how full that session is.

## The order

First, the set's author ships 2.1.0, and the lead runs `migrate` in Thrum, so that its effect shows in the next
pass before anything else changes. Thrum's builders have stopped, each with a handoff file, so `migrate` runs
with nothing in flight. A new lead then starts each builder from its handoff file, in a new session.

After that, the releases measure first, then cut the largest token cost, then make the records true, then stop
the lost rounds, and last change what the lead and the owner see. Measuring comes first because every later
release is judged by a token figure. The `migrate` work comes last, because none of releases 1 to 5 renames a
stored name.

### Release 1 (2.1.1): count tokens correctly

This answers C2, P4 and the rest of F2, and gives release 2 the figure it needs.

Before each Codex turn, the script notes the session's running total from the last `token_count` event in its
rollout file. After the turn, however it ended, it reads the last event again and records the rise as that
turn's tokens, so a turn stopped at the turn limit gets a row too. Taking both figures from the rollout file
means the old rows in a project's usage ledger, which are too high, never enter the sum. The script also records
how full the session is and its limit, in the usage ledger and in the run's state file, as `context` and
`window` (both proposed). For a Claude session it takes `context` from the last assistant message's usage. The
code goes in a new function beside `rollout_for`, called from `usage_of`, `run_turn` and `note_usage`, so that
it stays inside the host adapters.

When a turn fails, the script also saves the last lines of the host's stderr in that turn's row. In Thrum the
lead couldn't tell a usage limit from an outage, because the failed turns' rows held nothing.

It is about 70 lines and three tests. Old rows stay too high beside new rows that are right, so the `cost`
command says from which date its figures are per turn. A test with a two-turn rollout file shows the rows add up
to the file's final total, and a turn that exits 124 gets a row with its tokens.

### Release 2 (2.2.0): start a new session instead of resuming a full or old one

This answers P2, the rest of C3, and N7. The script resumes the same session for as long as the milestone is
the same, whatever state that session is in, and that one cause is behind P2 and C3.

Before every turn, not only when a run starts, the script starts a new session when the session's `context` is
over 60% of its `window`, or when the version of the script that started it differs from `VERSION`. A long run
fills its session turn by turn, so a check made only at the start would miss most of it. The new session gets
the normal first prompt, the facts 2.1.0 already gives a resumed builder, and the handoff file if there is one. A
new Codex session also gets a new goal, which replaces a goal that still names an old command, as one in Thrum
named `land`. The result says why, in `fresh_because` (proposed).

When resuming a session fails before any turn starts, `run` tries once with a new session before it prints
`HOST_FAILED`. In Thrum the lead did this by hand, with `--fresh`, 15 times.

The headless half of `session_rule` gains one sentence for N7. An agent in a headless session that asks a
question through a tool reaches nobody, so it ends with `BLOCKED` or `NEEDS_CONTEXT` instead. A builder and a
reviewer in Thrum both asked that way, and waited.

For C3, `build-milestone` and `review-milestone` each gain a sentence: read the end of a log rather than the
whole file, and judge a recording from still frames. One line of a session in Thrum held a 4.2 MB screenshot.

The state file gains `version`, `context` and `window` (all proposed). A new session loses whatever only the old
conversation held, but the facts above and the commits carry most of it, and reading in costs about 40,000
tokens against the millions a full session spends. When a project upgrades, each module's next turn starts a new
session, which is the intent. Tests cover the 60% case, a session that crosses 60% mid-run, and the version
case. In the next pass, no builder turn should start more than 60% full, and the lead should pass `--fresh` fewer
than three times.

### Release 3 (2.3.0): only the script sets Ready for Review

This answers N2, P3, N4 and N3. N2 and P3 share a cause. Today the builder sets its milestone to Ready for
Review in the done-when file and merges that onto the main branch, and the script runs its checks only
afterwards. If the checks fail, or the turn is stopped first, the main branch says something untrue, and other
builders rebase onto it. In Thrum that left another module with a three-way conflict, which its builder resolved
by deleting the conflict markers.

The owner decided on 12 November that only the script sets Ready for Review. The plan had first proposed that
the builder's `merge` run the checks before it pushed. That doesn't work, for two reasons. The builder runs
`merge` inside its own sandbox, so checks that need the GPU or the screen would fail there. And `merge` already
holds the `merge` lock while it runs the test command, so adding 35 to 49 minutes of item checks would stop every
other builder's merge for that long.

After this release:

1. The builder merges its work with the milestone still In Progress, and ends its turn with `DONE`.
2. The script, outside any sandbox, runs the test command and the milestone's item checks in its clean checkout
   of the main branch's tip, taking the exclusive resources the items name.
3. If they pass, the script writes the Ready for Review record and sets the milestone to Ready for Review, in
   one commit to the main branch. If they fail, it resumes the builder with what failed, as it does today.

If the builder's `merge` is still running as a background job when its turn ends, the script waits for that job
before step 2, rather than reporting a failure. In Thrum a `merge` pushed after the script had stopped the turn,
and the run reported it as failed (P3).

`check_failures` saves each check's full stdout and stderr to files under `<git common dir>/orchestrate/checks/`
(proposed), names them in its message, and shows the end of each stream on its own. In Thrum a builder asked for
the full output, because the panic wasn't in the 30 lines it was given (N3). It also saves each result under the
hash of the tree it checked, with the command, and a later call on the same tree and command reuses a pass. Then
the `check` a builder runs, the test command `merge` runs, and the script's checks in step 2 run the same
commands on the same tree once instead of three times (N4).

A builder from an older skill may still set Ready for Review itself. `merge` refuses a commit that sets a
milestone to Ready for Review or Done, and says the script does that now. `review` prints `INVALID` for a
milestone that is Ready for Review with no Ready for Review record, with `next` set to the `run` command that
checks it, for projects whose main branch already holds one.

This changes who writes the milestone's status, so it updates the done-when reference's table of who changes
what, `build-milestone`'s sections on finishing and merging, and the script's `ready_problems`, `land`,
`cmd_merge`, `cmd_run` and `review_once`. It renames no stored name, so it needs no `migrate`. Tests show that a
failing item check leaves the main branch without Ready for Review, that a second check of the same tree runs no
command, and that `merge` refuses a builder's Ready for Review. In the next pass, no Ready for Review commit
should lack a record of the checks, and the checks at the end of a milestone should take about a third of the
time they do now.

### Release 4 (2.3.1): a reviewer who can't reach the product costs no round

This answers F1, the half of N5 about hung tool calls, and the rest of C5.

The reviewer gets the ending a builder already has, `BLOCKED needs_access: <what>`. On that ending, `review`
merges nothing, counts no round, and prints `BLOCKED` (proposed for `review`), with `next` set to the same review
in a visible session for when the owner is at the machine.

The script also stops a headless turn when one tool call that isn't a shell command has been open for more than
15 minutes, and names that call in the result. C5 asked for a time limit on Computer Use, but the script can't
limit a host's tool. It can stop waiting for one. In Thrum two Computer Use calls hung for 98 and 116 minutes. A
turn the script stops at the turn limit also names the last tool call that was open, so the lead doesn't have to
guess what the agent was doing (N5).

The code is in `review_once`, `HeadlessWatch` and both hosts' `parse_output`, and in the "What finished looks
like" section of `review-milestone`. The glossary's entry for Needs Access gains the reviewer beside the builder,
and its Results table gains `review` beside `BLOCKED`. A slow tool call that would have finished may be stopped,
which is why shell commands are left alone. Tests cover the new ending and a rollout file with an open call. In
the next pass, no failed round should have access as its only finding, and no turn should sit idle for more than
20 minutes.

### Release 5 (2.4.0): what the lead and the owner see

This answers N5, L5, N8, F3, L6, the rest of P5, and two of the first pass's smaller issues. Each part is small
and has its own test.

For N5, `cmd_run` and `review_once` note the step they are on, such as "builder turn 3", "checking M1.2" or
"merging the record", and the `runs` command prints it. The lead then reports what is happening instead of
guessing.

For L5, the status page splits "Waiting on you" into "Needs you now" and "Choices made for you", and the
planner's assumptions go in the second. A project's status page changes shape at its next record.

For N8, `browser_needs` reads only the milestone being run, so a result no longer lists 18 items from other
modules.

For F3, `profile()` reads the first number in the `Builders:` line of the project settings, as a digit or a
word. `run` prints `REFUSED` (proposed for `run`) when that many builders are already running in the repository,
unless the lead passes the owner's words with `--more-builders` (proposed). A line with no number sets no limit,
so existing projects behave as before until they add one. The owner decided on 12 November that `run` refuses
rather than warns, because the skill's wording alone failed twice in Thrum, once right after the lead had told the
owner the setting was in force.

For L6, `build/SKILL.md` gains a sentence: start the lead in a session that has done no other work. Thrum's lead
compacted its context 13 times.

For P5, the script keeps a short list of what changed in each version. The first result after a project's
version changes carries that list as `changed` (proposed). In Thrum the lead guessed what 2.0.0 fixed, and
guessed wrong.

For the smaller issues, the script's Blocked messages give paths relative to the repository and name who acts:
the owner, the lead or a planner. Some of Thrum's named no one. And `build-milestone` gains a sentence: a result
the builder can't explain, such as the "two-pixel mismatch … unexplained" a builder in Thrum left in a block
reason, is a problem to fix or to put to the owner, not a reason to block.

### Release 6: migrate one branch while other modules run

This answers N6 and P1. Build it before the next release that renames a stored name, and rename nothing until
then.

`migrate --branch` (proposed) applies the renames to one worktree's own commits while holding only that module's
run lock, so it works while other modules are building. Plain `migrate` lists the worktrees still on the old
names. This replaces the earlier idea of stopping every run first. In Thrum, with nothing like it, the lead merged
a worktree by hand and its builder resolved the conflicts by deleting the markers. It is a medium-sized change.

## Decisions the owner made, 12 November

- Only the script sets Ready for Review, after its checks pass (release 3).
- `run` refuses to start a builder past the `Builders:` count, unless the lead passes the owner's words for the
  extra builder (release 5).
- The script starts a new session when the old one is 60% full. The figure is fixed in the script, and becomes a
  project setting only if a project needs another figure (release 2). For Thrum's builders 60% is about 285,000
  tokens.
- Evidence gets no field for the commit it was proved on, for now. The line in `build-milestone` about proving
  after the last merge comes first, and the field is added only if the next pass shows another round lost to
  evidence from an older commit (N1, F4).
- A project can't yet name a command that tests access before a review starts (F1). Release 4 already stops the
  lost round, so this waits.

## Findings not to act on

Chaining commands (L2), such as running a review straight after a builder's turn inside one command, stays left
out, as the domain README records. Nothing has changed to justify it. Each time a result wakes the lead, the lead
re-reads its conversation, about 180,000 tokens, against millions for one builder turn, and L6 makes that
conversation smaller. Release 3 makes each `next` trustworthy, which chaining would need first anyway.

Repeated flags in the lead's commands (L3) cost a few tokens each, and the background-job and lock rules the lead
repeated are now in the builder's prompt. Nothing more is planned.

The separate status page commits (C7) cost noise in `git log`, not tokens or rounds, and the separate commit
protects the record. On evidence size, 2.1.0 already tells reviewers not to capture again what the script has
checked, so the next pass should measure growth per day before anything limits it.

Capping command output (C3) can't be done by the script, because the script doesn't run the agents' commands.

Comparing exact images at merge (F4) belongs in a project's test command, not in the script.

Routing git writes through the script (F7) isn't worth it. Only 2 of 170 approval requests in Thrum were
refused, and the sessions Codex uses to review approvals cost under 1% of tokens. For the same reason those
sessions stay out of the usage ledger (P4).

A fixed path for the script (L1) depends on the hosts' plugin folders, which the set doesn't control. See first
whether the warning about a newer installed copy is enough.

A place on the status page for the lead's own open questions (L5) waits until the shorter list shows whether
they still get lost.

The daily report (L4) is already in the `build` skill. Whether the new lead writes it is for the next pass to
check.

## Where the build differs from this plan

Each release's agent reported these. None of them was checked against a live project before 2.1.0 shipped.

Release 1 reads a Codex turn's tokens in `run_turn` and a Claude turn's in `_run_turn`, rather than in `usage_of`
and `note_usage`. A Claude session gets `window` only when its last event arrives, so the 60% check can't run on
the very first turn of a Claude session that is stopped early.

Release 2 starts every session again once after any version change, not only after 2.1.0. `fresh_because` lists
only the new reasons: a full session, an older version and a failed resume.

Release 3 needed two things the plan didn't name. A milestone built in one chat, with no `run` afterwards, gets its
checks from `run --checks-only`. And the review now judges the script's commit that set Ready for Review, since the
builder's own commit leaves the milestone In Progress. A Ready for Review record made before a failed review no
longer counts, so after `owner accept` and then `owner rereview`, `run` checks the work again before the review.
A remembered pass is keyed on the tracked files, so a stale ignored build output could be reused.

Release 4 tracks open tool calls in `HeadlessWatch` rather than in each host's `parse_output`. Turns in the app
aren't watched. Subagent, sleep and wait calls are exempt as well as shell commands. A review stopped at the turn
limit still prints `HOST_FAILED`, with a reason that says so.

Release 5 counts builders from the live run records, so two `run` commands started in the same instant can both
pass. The owner's words given with `--more-builders` go into the result only. Blocked: Needs Context and Needs
Dependency moved from "Waiting on you" to "Now and next", because the lead or a planner acts on them. A project
with no `version.json` lists every 2.1.0 change once.
