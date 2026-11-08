# Why the process looks like this

## The proven parts and their sources

- **Planner.** Turns a short brief into an ambitious spec at the level of results and high-level design, leaving
  technique to the builder ([harness design for long-running apps](https://www.anthropic.com/engineering/harness-design-long-running-apps), Mar 2026).
- **Generator.** Builds in units, keeping state in git and a progress file
  ([effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents), Nov 2025).
  A fresh session per unit follows that post and [Cursor's scaling work](https://cursor.com/blog/scaling-agents);
  Anthropic's later harness dropped context resets on Opus, so Claude leads keep their session.
- **Evaluator.** A separate agent exercises the running product against agreed criteria. It earns its cost where the
  task is beyond what the model does reliably alone, so it runs on visual milestones, contract changes and module close,
  not every unit (harness design).
- **Oracle.** An automated check answers most questions without any agent. It must be close to perfect, or agents solve
  the wrong problem ([building a C compiler](https://www.anthropic.com/engineering/building-c-compiler), Feb 2026).
- **One lead.** Anthropic's long-run orchestration is one lead session that runs fresh subagents, passes files rather
  than summaries, and decides by script where it can. With a lead there's no need for lock files; the C compiler
  needed locks only because it had none.

## Design choices

- **Done-when files are JSON,** because models overwrite structured files less than prose (effective harnesses).
  Each writer has defined fields.
- **Escalation is by count,** recorded by the evaluator and mapped by the loop: 1–2 failed closes, same session; 3,
  fresh session; 4, re-plan; 4 again after a re-plan, park and report. Effort never rises automatically.
- **The loop checks claims itself:** committed, integrated, and every oracle check rerun, so a milestone without
  review closes on evidence rather than the generator's word.
- **Models and effort are always explicit,** because defaults drift between releases and between vendors.
- **The owner sets the pace** by how many streams run. The loop forecasts quota and never holds work back.
- **Research before experimenting.** Most of what a module needs has been solved in shipped products and published
  work; needing to try things usually means research or design is missing.

## Parked until a failure calls for them

Add one only when its failure is seen, and say why: parallel design approaches; parallel focused reviewers with
finding confirmers; two independent checks before a headline result; report states beyond DONE, BLOCKED and
NEEDS_CONTEXT; a deferred list for minor findings; a per-stream claims ledger beyond the progress note.

## Not yet proven

- Visual evaluators are the weakest part. Watch their verdicts in the first week, and add overturned ones to the
  project's graded examples.
- Fan-out depends on the lead session staying up. A possible fallback, not built, is evaluators launched by the loop as
  `claude -p`, which bills through the API and loses sidebar nesting.
- Whether a high-effort planner subagent runs at high under a medium lead is untested; check its first transcript.
