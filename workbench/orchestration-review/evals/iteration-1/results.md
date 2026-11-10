# Iteration 1 results: `plan-module`, old against revised

9 November 2026. A smoke test, not a benchmark: two runs per arm on one case and one run per arm on the other.

## What was run

- **Arm a (old):** `skills/orchestration` at `2ad09f8` (orchestrate 1.5.3).
- **Arm b (revised):** the working tree on branch `orchestrate-polish`, uncommitted, as it stood when the runs
  started.
- **Model and effort:** Claude Opus through the Agent tool (`model: opus`), effort not set, so the subagent default.
  The suite's own planner default is Opus 5.5 at high, so these runs may have used less effort than a real planner.
- **Cases:** `props` (taste-led, two runs per arm) and `logsift` (measurable, one run per arm). The prompts and the
  grading statements are in [statements.md](statements.md), written before any run finished.
- **Grader:** one Claude Sonnet subagent, blind. The folders were renamed (props K, L, M, N and logsift P, Q) and
  matched back to arms only after grading: K is b/run-2, L is a/run-1, M is a/run-2, N is b/run-1, P is logsift b
  and Q is logsift a.
- The plans themselves are in `props/` and `logsift/` beside this file.

## Grades

### `props`

| Statement | a/run-1 | a/run-2 | b/run-1 | b/run-2 |
|---|---|---|---|---|
| 1. Owner chooses a direction from alternatives before the full set | fail | fail | pass | pass |
| 2. The creak is judged by a person | pass | pass | pass | pass |
| 3. Triangle limit and single atlas each proved by a command | pass | pass | pass | pass |
| 4. Every look item names something concrete to compare against | fail | fail | fail | fail |
| 5. The first milestone can start without the owner | pass | pass | pass | pass |

- **Statement 1 is the only one that separates the arms.** Both old runs build real props first and ask the owner
  for a yes or no on one style sheet; a/run-2's log lists "no variants" as an assumption. Both revised runs open
  with three variants that must "differ in kind" and an `attended` pick, recorded under a `docs/anchors` folder.
- **Statements 2, 3 and 5 pass in every run,** so they measure nothing the revision added. Keep them as guards.
- **Statement 4 fails everywhere on the grader's reading,** which looked at each item's own text. Every milestone
  `bar` in all four plans does name a comparison. The statement was ambiguous, so this is a flaw in the test.

### `logsift`

| Statement | a (old) | b (revised) |
|---|---|---|
| 1. 5 GB memory bound proved by a command a load-everything build would fail | pass | pass |
| 2. Rotation proved by a command an ignore-rotation build would fail | pass | pass |
| 3. Items say what is observed, not the builder's steps | fail | pass |

Statement 3 turned on one item in the old plan (M1.5 tells the builder to copy numbers to the evidence page). One
run per arm, so this is within what chance could produce.

## Measured by script

| Run | Plan words | Milestones | Items | Median words per item | Longest item | Items with `ask` |
|---|---|---|---|---|---|---|
| props a/run-1 | 5,344 | 5 | 36 | 41 | 94 | 4 |
| props a/run-2 | 6,368 | 6 | 36 | 49 | 95 | 5 |
| props b/run-1 | 4,790 | 5 | 39 | 31 | 41 | 8 |
| props b/run-2 | 4,647 | 6 | 32 | 35 | 73 | 5 |
| logsift a | 4,544 | 3 | 23 | 45 | 94 | 2 |
| logsift b | 4,092 | 3 | 23 | 31 | 60 | 4 |

Items are shorter in every revised run, by about a quarter to a third at the median. Milestone counts didn't move.
All six done-when files pass `agent_loop.validate`.

## What the grades don't show

Noted by the grader, outside the statements:

- **A possible cost on the measurable case.** The old `logsift` plan covers more with checks (timestamp formats,
  logfmt, long lines, a million-line burst, a filtered 5 GiB run). The revised one has none of those. Item counts
  are equal, so this isn't simply fewer items, and with one run each it could be chance. Watch for it.
- Both old `props` plans check that the build reproduces from a clean clone. Neither revised plan does.
- b/run-2 has two `inspect` or `ask` items on a headless target, which looks like a target mismatch.
- b/run-2 picks the direction on crates and barrels and rebuilds them later; b/run-1 picks on the lantern, the
  hardest prop, and carries the winner forward.

## Time and tokens

As the harness reported them when each run finished:

| Run | Tokens | Seconds |
|---|---|---|
| props a/run-1 | 94,297 | 257 |
| props a/run-2 | 101,170 | 343 |
| props b/run-1 | 98,387 | 289 |
| props b/run-2 | 94,231 | 252 |
| logsift a | 88,653 | 214 |
| logsift b | 87,543 | 173 |

No difference in planning cost between the arms.

## Required fields

- **Leakage checked:** yes. Each transcript was searched for Skill tool calls, reads of the installed plugin's
  cache, reads of the other arm's folder and `agent_loop.py` runs. None was found: each run read only its own copy
  of the skill. The orchestrate plugin was installed in the session, and the runs were told not to use it.
- **Trigger trials:** not done. `plan-module`'s description changed ("Plans software work" became "Plans work …
  whether software, a game or a set of assets"), and whether it still fires, or now fires where it shouldn't, is
  untested.
- **Receiver-side run:** not done. A plan's real test is what a builder and reviewer do with it. Nothing here was
  built, so the direction milestone, anchors and critique rounds are untested in use.
- **What the owner said:** not yet shown to the owner.
