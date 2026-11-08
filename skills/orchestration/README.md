# Orchestration

Skills for building software with AI agents in Claude Code and Codex. They work for web apps, native apps, CLI tools,
libraries and engines. Each project describes itself once in `ORCHESTRATE.md`, so the skills stay generic.

| Skill | Model, effort | What it does |
|---|---|---|
| [`plan-module`](plan-module/) | Opus 5.5, high | Sets the project up, plans the module map and contracts, then each module's design, milestones and done-when file |
| [`build-milestone`](build-milestone/) | Codex `gpt-6.1-sol` or Opus 5.5, medium | Builds, verifies and integrates the next milestone |
| [`review-milestone`](review-milestone/) | Opus 5.5, medium | Gives a clean-context verdict on a milestone or a design |
| [`build-parallel`](build-parallel/) | Opus 5.5 lead, medium | Runs several Codex generators through `agent_loop.py`, with evaluator and planner subagents |
| [`instructing-agents`](instructing-agents/) | | Writes goals, briefs, steers and skills that agents act on |

There are two speeds:
- **One chat:** run `/plan-module`, then `/build-milestone` in Claude Code or Codex. You can switch vendor between
  milestones, because everything handed over is in the files.
- **Fan-out:** `/build-parallel`.

## Why it looks like this

- **Planner, generator, evaluator, oracle.** A planner writes results and high-level design, and leaves technique to
  the builder. A separate evaluator exercises the running product, and is only worth its cost where the work is
  beyond what the model reliably does alone, so it runs on visual milestones, contract changes and module close.
  Automated checks answer everything else. Sources:
  [harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps),
  [long-running harnesses](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents),
  [the C compiler](https://www.anthropic.com/engineering/building-c-compiler),
  [Cursor on scaling agents](https://cursor.com/blog/scaling-agents).
- **Done-when files are JSON, and every field has one writer,** because models overwrite structured files less than
  prose.
- **Ways to prove work** ([proofs](plan-module/references/proofs.md)): each item mixes commands (`check`), captures
  judged against a quality bar in words (`inspect`), and questions answered by reading (`ask`). Several kinds come
  packaged, and projects add their own. Visuals are never judged against a target image.
- **The loop checks claims itself.** Work must be committed and integrated, and the loop reruns the oracle checks.
- **Escalation goes by count:** 1–2 failed reviews, the same session; 3, a fresh session; 4, a re-plan; 4 more after a
  re-plan, park it.
- **Model and effort are always named,** because defaults drift between releases.
- **The owner sets the pace** by choosing how many streams run. The loop forecasts quota and never holds work back.

## Left out until a project needs it

Start minimal and add a feature only when its absence causes a failure someone has seen. These are left out for now:
- pull-request integration (streams integrate by rebasing onto one branch);
- researcher agents (a general subagent does that job);
- parallel design approaches, and a confirmer for each finding;
- report states beyond `DONE`, `BLOCKED` and `NEEDS_CONTEXT`.

The evaluator is the least proven part. Anthropic found Claude, out of the box, a lenient QA agent that tests
superficially. So `review-milestone` makes it drive the product itself, probe edge cases, and fail any defect it
finds rather than argue it away, and the owner calibrates it by spot-checking early verdicts. An overturned verdict
becomes a graded example.
