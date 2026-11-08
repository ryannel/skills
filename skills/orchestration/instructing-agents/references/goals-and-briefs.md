# Goals, plans, steers and briefs

Contents:
- [A goal or long-running prompt](#a-goal-or-long-running-prompt)
- [Unattended runs](#unattended-runs)
- [A plan for multi-hour work](#a-plan-for-multi-hour-work)
- [A steer to a running agent](#a-steer-to-a-running-agent)
- [A brief for a subagent or session](#a-brief-for-a-subagent-or-session)
- [A brief for an independent reviewer](#a-brief-for-an-independent-reviewer)

Worked examples of each are in [examples](examples.md).

## A goal or long-running prompt

A goal turns a request into a loop: work, check, then continue or complete. The goal text is also the completion test,
so write it as one. The two harnesses judge it differently.

- **Codex `/goal`.** The thread audits its own completion against the objective and anything it references. In
  practice, every named item and referenced file is treated as a requirement (an inference from the harness). OpenAI's
  cookbook lists six parts:
  - the outcome;
  - the verification surface;
  - constraints that must not regress;
  - boundaries (files, tools, data);
  - an iteration policy for choosing the next attempt;
  - a blocked stop condition with what to report.
- **Claude Code `/goal`.** A small, fast model judges the condition after each turn from what the conversation shows. It
  runs no commands and reads no files. Write one measurable end state, a stated check whose result will appear in the
  transcript, and the constraints that must not change. The limit is 4,000 characters. A turn or time clause bounds it
  ("or stop after 20 turns").

For either harness:
- **State the outcome as an end state, not an activity.** "The checkout benchmark's p95 is under 120 ms", not "improve
  checkout".
- **Size it to audit.** "Fix the failing test" can be too narrow, and "improve the system" can't be audited.
- **Give quality goals a stated bar and a judge:** named views, shipped settings, references, an independent pass. An
  open bar such as "polish until excellent" never completes.
- **Define the evidence standard for research:** what counts as confirmed, approximate, proxy or blocked. Ask for a
  report that keeps these apart.
- **Put the whole task in the first message.** Requirements fed in over several turns cost efficiency and sometimes
  quality.
- **Don't make a goal of a one-line edit, a question or a short review.**

## Unattended runs

Before leaving an agent alone, answer these questions:
- Does it know what done looks like?
- Can it check its own work?
- What may it touch?
- What stops it?
- Where does the result go, and who signs off?

Grant standing permission for the safe loop: run local tests, fix failures it caused, rerun them and commit
checkpoints. Then name the stops you do want, such as irreversible or destructive actions, publishing, and other
people's areas. Put approval last: have the agent prepare the concrete, reviewable result first, so the human's yes is
the final step.

The loop belongs to the harness: Codex `/goal`, Claude Code `/goal`, or a Stop hook. Without one, see
[persistence by model and harness](models.md#persistence-by-model-and-harness) before adding any "carry on" wording.
Tell a session that has no loop exactly when to report back, for example at a milestone close, at a seam, or when
blocked.

## A plan for multi-hour work

Keep the plan in a file the agent re-reads and updates. It survives context loss, and you can audit it.

The shape below comes from OpenAI's long-horizon Codex post and its ExecPlans cookbook, both from the GPT-5.x era. It
matches Anthropic's advice on structured notes and progress files. No GPT-6 source restates it, so treat it as a
starting shape, not a measured rule.
- **Purpose:** a few sentences on what someone can do afterwards and how to see it working.
- **Milestones:** each one an outcome you can observe, small enough to finish soon, with the riskiest first. Each has
  done-when checks, its validation commands or views, and linked evidence once it passes. Phrase acceptance as
  behaviour a person can verify: "returns 200 with the body", not "added a HealthCheck struct".
- **Work** under each milestone, at whatever grain helps. Tick items as they finish and revise as the agent learns.
- **A short status:** the current milestone, what's happening now and since when, what's next, and what's blocked.
- **A decision log** with reasons, which stops the agent oscillating.
- **A stop-and-fix rule:** when validation fails, repair before moving on.

Let the agent write its own plan from the spec, then check it against this shape and audit progress against it. Rewrite
the plan in place so it reads as current. A plan whose amendments pile up while no done-when box moves has stopped
steering the work.

## A steer to a running agent

A steer contains:
- **The problem**, in one line.
- **The evidence:** files, commits, figures or captures, with times.
- **What it threatens:** a milestone, a direction the owner gave, a constraint.
- **The outcome wanted**, stated as a result rather than the fix.
- **Pointers:** the design, the skill section, the research to consult.

Have the agent make any plan change itself and log why. If a milestone's meaning changes, it commissions a review of
the change and carries on while the review runs; the review doesn't block the work. Steer the running turn rather than
restarting it, since a course correction doesn't wipe progress. After the steer, fix whatever let the problem happen.

House practice (the author's, not vendor guidance): when an agent circles on one defect, point it at research into
current, state-of-the-art techniques and shipped practice rather than more tuning.

## A brief for a subagent or session

A fresh agent knows only what you write; the brief is its whole context.
- **The goal and why it matters.**
- **What you've already ruled out**, so it doesn't repeat it.
- **Pointers** to the files and docs worth reading, rather than retyped content.
- **Explicit scope:** the files it owns, what it must not touch, and what done looks like.
- **What to return, and in what shape:** a ranked list, a file path, a verdict per check.

Delegate parallel, independent work, noisy searches whose output you don't need, and independent review. Don't delegate
what takes a handful of tool calls. Opus 5 delegates readily, so limit it; Astra delegates less than you may want, so
say when to delegate. Keep one writer per set of files. A forked skill or a fresh session can't see your conversation,
so the brief has to stand alone.

## A brief for an independent reviewer

The reviewer's value is that it hasn't seen your reasoning, so keep it that way.
- **Give it the requirements, the use cases and the raw artifacts:** code, design, captures, logs and measurements.
- **Withhold your hypothesis, your preferred technique and the verdict you expect.** A reviewer handed a conclusion
  tends to confirm it.
- **Ask for everything that fails the criteria, ranked.** Each finding is marked verified (with file and line, or a
  reproduction) or suspected. Don't ask for "only blocking issues".
- **For a design review,** have it derive what the module must do from the brief alone, then compare that with the
  design.
- **For running or visual output,** have it say whether it watched motion or sampled stills, at what size, and which
  build it saw.
- **Make independence structural where you can:** read-only tools, and no ability to spawn or edit.

A reviewer asked to find problems always finds something. Act on the findings that change a decision, and skip style
nitpicks and tests for cases that can't happen. Record each verdict with the revision it saw and the brief it was given.
Out of the box, evaluators tend to be lenient, so tune a standing reviewer by reading its logs and correcting it where
its judgement diverges from yours.
