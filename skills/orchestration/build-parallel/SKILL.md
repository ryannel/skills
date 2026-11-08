---
name: build-parallel
description: Runs several module streams of the orchestrate process at once under one Claude lead session. The lead runs Codex generators through scripts/agent_loop.py, evaluators and planners as subagents, forecasts quota and decides escalation by script. Use when the owner asks to fan out, run modules in parallel, or build several modules' milestones at once. Not for one stream (build-milestone in a single chat).
disable-model-invocation: true
---

# Build in parallel

Run as the lead, Claude Opus 5.5 at medium effort unless `ORCHESTRATE.md` says otherwise, in a Claude Code session the
owner started. Invoked as `/build-parallel <MODULE> <MODULE> …`. Read `ORCHESTRATE.md` first, and run `LOOP profile
--worktree <repo>`; fix the profile with the owner if it fails.

**Outcome:** each named module's milestones close, one after another, until each stream is done, parked or stopped by a
rule below. Each day the owner gets a short report.

You run the steps and the bookkeeping. You don't build and you don't judge. Generators build, the evaluator judges, and
the planner re-plans, each from files. Pass them file paths rather than your own summaries, and add no hints or opinions
to their briefs, so their work stays independent.

`LOOP` below is `python3 <this skill's folder>/scripts/agent_loop.py`.

## Start

1. **Check each module** has a plan and a done-when file with an open milestone (`LOOP status --module <M> --worktree
   <repo>`). A module without them goes to `/plan-module` first, through the planner below.
2. **Confirm with the owner, once, before launching anything:** the streams; the quota forecast (`LOOP quota`: used,
   burn per day, and whether it lasts to the reset); your proposed number of concurrent streams. The owner sets the
   pace by choosing how many streams run; the loop never holds work back for quota. Ask this once, up front, so the
   run doesn't wait on the owner later; anything on the profile's "Owner decides" list that comes up mid-run still goes
   to them, while the other streams carry on.
3. **Set up each stream:** a worktree from the base branch at `.claude/worktrees/stream-<module>`, kept across the
   stream's milestones so build caches stay warm; and keep the machine awake for the run if the host offers it.

## Run each stream

- **Generator (Codex).** Run `LOOP run --module <M> --worktree <path>` as a background command. It pins the profile's
  Codex model and effort on every turn and prints one JSON result line when it stops.
- **Generator (Claude, for a bounded slice the owner asked for).** Run it as a subagent with the Agent tool (Opus 5.5,
  medium), briefed with the module, the milestone id and `/build-milestone`.
- **Evaluator and planner** run as the `orchestrate-evaluator` and `orchestrate-planner` subagents
  (`orchestrate:`-prefixed under a plugin install). Pass them no `model`, so their agent files' model and effort hold
  (a set `CLAUDE_CODE_EFFORT_LEVEL` also overrides them). Subagents can't start subagents, so when the planner says an
  independent design review is owed, run it yourself: a fresh `orchestrate-evaluator` asked to review the module's
  design and plan against its brief.
- **Act on the result line:**

| Result | What you do |
|---|---|
| `CLAIMED` with `review: false` | The loop reran the oracle checks and the generator set `state` to `done`. Start the next milestone (in pull-request mode, after the merge, as above). |
| `CLAIMED` with `review: true` | Run the evaluator: "Review milestone `<id>` of `<MODULE>` at `<commit>`, worktree `<path>`." Nothing else. In pull-request mode, merge after a pass if the profile's `Merge` is `lead`; otherwise report it and start only milestones that don't depend on it. |
| `DONE` with items not passing, or not yet integrated | Resume with `--message` naming what's missing. |
| `BLOCKED`, `NEEDS_CONTEXT` | Read the report. Context you can supply from files goes back by resume (`--message`). A design or contract problem goes to the planner. Otherwise it goes in the daily report, and the stream moves to its next independent milestone if there is one. |
| `BUDGET` | Treat it as a failed close: run the evaluator on what exists, so the findings drive the next attempt. |
| `FLOOR` | Stop launching Codex work, and put it in the report with the evidence. |
| `PIN` | Stop that stream and report: a turn ran on the wrong model or effort. |
| `PAUSED` | The goal was paused in the Codex app, and only its play button resumes it. Report it and leave the stream. |

- **After a failed review,** run `LOOP next --module <M> --worktree <path> --milestone <id>`. It prints the action and
  a `message`: `same-session` (re-run with `--message <message>`), `fresh-session` (re-run with `--fresh --message
  <message>`), `replan` (the planner re-plans the milestone with `/plan-module`), or `park` (set `state` to `parked`
  and report it). Follow the action rather than your own judgement: the count is the record of what has already been
  tried, and overriding it is how streams loop.
- **Contract proposals** in a plan's log go to the planner at project level (`/plan-project`), run on the next pause in
  that stream.

## Shared resources

- **Exclusive resources** listed in the profile are taken with `LOOP lock <name> -- <command>`, a lock shared by every
  worktree of the repository. Ordinary tests can overlap.
- **The integration branch is shared.** Generators rebase and run the profile's check before integrating. If it breaks,
  the first stream to see it fixes it before continuing, and you note it in the report.

## Daily report to the owner

Keep it to a screen: milestones closed, with links to their evidence; the evaluator's verdicts; new inspection lists, so
the owner can adjust a bar; parked or blocked items; and the quota forecast. Every result line carries a forecast; when
it first says the limit runs out before the reset, tell the owner in chat with the forecast, and keep running until they
change the streams.

When the owner overturns a verdict, add it to the profile's graded examples.

## Stop

Stop when every stream is done, parked or stopped by a rule, or when the owner says so. Clean build outputs in the
stream worktrees, remove worktrees whose work has landed, and send the final report.
