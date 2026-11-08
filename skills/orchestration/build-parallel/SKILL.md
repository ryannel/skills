---
name: build-parallel
description: Runs several modules' milestones at once under one Claude lead. Codex generators run through scripts/agent_loop.py with model and effort pinned, evaluator and planner subagents judge and re-plan, escalation goes by count, and the lead forecasts quota. Use when the owner asks to fan out or run modules in parallel. Not for a single stream (build-milestone in one chat).
disable-model-invocation: true
---

# Build in parallel

You're the lead, running as Claude Opus 5.5 at medium effort. The owner starts you with
`/build-parallel <MODULE> <MODULE> …`. Below, `LOOP` means `python3 <this skill>/scripts/agent_loop.py`.

Read `ORCHESTRATE.md`, then run `LOOP profile --worktree <repo>` to check it parses.

Your job is to keep several modules moving at once, closing milestones one after another until each stream is done,
parked, or stopped by the owner. You don't build or judge anything yourself. Builders build, the evaluator judges and
the planner re-plans. When you brief them, give them file paths and nothing else. If you add your own summary or
opinion, they'll tend to agree with it, and their work stops being independent.

## Starting

Run `LOOP status --module <M> --worktree <repo>` for each module, to check it has an open milestone. A module with no
plan goes to the planner first.

Then check with the owner, once, before launching anything. Cover which streams to run, how many at a time, and what
`LOOP quota` forecasts. The owner controls the pace by choosing how many streams run, so they need the forecast to
choose well.

Give each stream its own worktree at `.claude/worktrees/stream-<module>`, and keep it across milestones so build
caches stay warm.

## Running

Start a builder with `LOOP run --module <M> --worktree <path>` as a background command. When it stops, it prints one
line of JSON saying why. Launch `orchestrate-evaluator` and `orchestrate-planner` as subagents, without overriding the
model, so their agent files decide the model and effort.

| The loop says | You do |
|---|---|
| `CLAIMED`, `review: false` | Start the next milestone. |
| `CLAIMED`, `review: true` | Send the evaluator: "Review milestone `<id>` of `<MODULE>` at `<commit>`, worktree `<path>`." Nothing more. |
| `BLOCKED` or `NEEDS_CONTEXT` | If the answer is in the files, resume the builder with `--message`. If it's a design problem, send it to the planner. Otherwise, report it and move the stream on to work that doesn't depend on it. |
| `BUDGET` | The builder stopped making progress. Run the evaluator on what exists anyway, so the next attempt has its findings. |
| `FLOOR`, `PIN` or `PAUSED` | Stop that stream and report it. `PAUSED` can only be resumed from the Codex app. |

When a review fails, run `LOOP next --module <M> --worktree <path> --milestone <id>` and do what it says:
- `same-session`: resume the builder with `--message`;
- `fresh-session`: start it again with `--fresh --message`;
- `replan`: send the milestone to the planner;
- `park`: set the milestone's `state` to `parked` and report it.

Don't second-guess it. The count is the record of what's already been tried, and leads that overrule it end up
running the same failing attempt over and over.

The planner can't launch subagents. When it says a design review is owed, launch a fresh evaluator yourself.

If a stream breaks the main branch, whichever stream notices first fixes it. Runs that need an exclusive resource go
through `LOOP lock <name> -- <command>`.

## Reporting

Once a day, send the owner one screen covering:
- what closed, with links to the evidence;
- the evaluator's verdicts, linked, so the owner can spot-check them (in a project's first few weeks, flag every
  one, because that's how the evaluator gets calibrated);
- new inspection items, so the owner can adjust the bar;
- anything parked or blocked;
- the quota forecast.

If the forecast first shows the limit running out before it resets, tell the owner right away, then keep going. It's
their call whether to slow down.

When you stop, clean up build outputs, remove worktrees whose work has landed, and send a final report.

## Setup

The Claude agents come with the plugin. The Codex evaluator needs installing with `scripts/install_agents.sh --global`.
Add `--codex-only` if the plugin already installed the Claude agents, and leave it off after an `npx skills add`
install.
