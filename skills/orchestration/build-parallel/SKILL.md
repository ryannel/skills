---
name: build-parallel
description: Runs several modules' milestones at once under one Claude lead. Codex generators run through scripts/agent_loop.py with model and effort pinned, evaluator and planner subagents judge and re-plan, escalation goes by count, and the lead forecasts quota. Use when the owner asks to fan out or run modules in parallel. Not for a single stream (build-milestone in one chat).
disable-model-invocation: true
---

# Build in parallel

Run as the lead: Claude Opus 5.5 at medium effort, invoked as `/build-parallel <MODULE> …`. `LOOP` below means
`python3 <this skill>/scripts/agent_loop.py`. Read `ORCHESTRATE.md`, and check it with `LOOP profile --worktree <repo>`.

**Outcome:** each module's milestones close one after another, until each stream is done or parked, or the owner
stops it. The owner gets a short report each day.

You run the steps and keep the books. Generators build, the evaluator judges and the planner re-plans. Brief them with
file paths and nothing of your own, so their work stays independent.

## Start

1. **Check each module has an open milestone** with `LOOP status --module <M> --worktree <repo>`. A module without a
   plan goes to the planner first.
2. **Confirm with the owner once:** the streams, how many run at a time, and the forecast from `LOOP quota`. The owner
   sets the pace by choosing the number of streams.
3. **Give each stream its own worktree** at `.claude/worktrees/stream-<module>`, and keep it across milestones so
   build caches stay warm.

## Run

Start a generator with `LOOP run --module <M> --worktree <path>` as a background command. It prints one JSON line
when it stops. Run `orchestrate-evaluator` and `orchestrate-planner` as subagents without a `model` override, so their
agent files decide the model and effort.

| Result | What you do |
|---|---|
| `CLAIMED`, `review: false` | Start the next milestone. |
| `CLAIMED`, `review: true` | Brief the evaluator with: "Review milestone `<id>` of `<MODULE>` at `<commit>`, worktree `<path>`." |
| `BLOCKED`, `NEEDS_CONTEXT` | If the missing context is in files, resume with `--message`. Send a design problem to the planner. Otherwise report it, and move the stream on to independent work. |
| `BUDGET` | Run the evaluator on what exists, so its findings drive the next attempt. |
| `FLOOR`, `PIN`, `PAUSED` | Stop that stream and report it. `PAUSED` resumes only from the Codex app. |

After a failed review, run `LOOP next --module <M> --worktree <path> --milestone <id>` and follow its action:
- `same-session`: resume with `--message`;
- `fresh-session`: rerun with `--fresh --message`;
- `replan`: send the milestone to the planner;
- `park`: set the milestone's `state` to `parked` and report it.

Don't override these with your own judgement. The count records what's already been tried, and overriding it is how
streams end up looping.

The planner can't launch subagents, so when it says a design review is owed, run a fresh evaluator yourself.

## Shared state

- If a stream breaks the integration branch, the first stream to see it fixes it.
- Runs that use an exclusive resource go through `LOOP lock <name> -- <command>`.

## Report

Each day, send one screen to the owner covering:
- milestones closed, with their evidence;
- the evaluator's verdicts, linked, so the owner can spot-check them (in a project's first weeks, flag every one);
- new inspection items, so the owner can adjust the bar;
- anything parked or blocked;
- the quota forecast.

The first time the forecast says the limit runs out before the reset, tell the owner straight away, and keep running.

When you stop, clean build outputs, remove worktrees whose work has landed, and send a final report.

## Setup

The Claude agents ship with the plugin. Install the Codex evaluator, or every agent after an `npx skills add`
install, with `scripts/install_agents.sh --global` (add `--codex-only` under a plugin install).
