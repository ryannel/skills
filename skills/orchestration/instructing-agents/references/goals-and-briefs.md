# Goals, plans, steers and briefs

Contents:
- [A goal or long-running prompt](#a-goal-or-long-running-prompt)
- [Unattended runs](#unattended-runs)
- [A plan for multi-hour work](#a-plan-for-multi-hour-work)
- [A steer to a running agent](#a-steer-to-a-running-agent)
- [A brief for a subagent or session](#a-brief-for-a-subagent-or-session)
- [A brief for an independent reviewer](#a-brief-for-an-independent-reviewer)

There's a worked example of each one in [examples](examples.md).

## A goal or long-running prompt

A goal turns a request into a loop. The agent works, checks, and then either keeps going or stops. The goal text is
also the test for whether it's finished, so write it as a test. The two harnesses judge that test in different ways.

In Codex, `/goal` has the thread audit its own completion. It checks against the objective and anything the objective
refers to. In practice, it treats every item you name and every file you point to as a requirement. That last part is
an inference from how the harness behaves. OpenAI's cookbook lists six parts a goal should have:

- the outcome
- the verification surface
- constraints that must not regress
- boundaries (files, tools, data)
- an iteration policy for choosing the next attempt
- a blocked stop condition, with what to report

In Claude Code, `/goal` works differently. After each turn, a small, fast model judges the condition from what the
conversation shows. It doesn't run any commands or read any files. So write one end state that can be measured, a
check you name whose result will show up in the transcript, and the constraints that must not change. The limit is
4,000 characters. You can bound it with a turn or time clause, such as "or stop after 20 turns".

Some advice holds for both harnesses.

Describe where the work ends up, not what the agent does. "The checkout benchmark's p95 is under 120 ms" is an end
state. "Improve checkout" is an activity, and an activity has no point where it's finished.

Make the goal a size someone can audit. "Fix the failing test" can be too narrow. "Improve the system" can't be audited
at all.

A quality goal needs a stated bar and someone to judge it. That means naming the views, the shipped settings, the
references, and an independent pass. An open bar like "polish until excellent" never completes, because nothing ever
clears it.

A research goal needs an evidence standard. Say what counts as confirmed, approximate, proxy or blocked, and ask for a
report that keeps those apart.

Put the whole task in the first message. If you feed requirements in over several turns, it costs efficiency and
sometimes quality.

Don't make a goal out of a one-line edit, a question or a short review.

## Unattended runs

Before you leave an agent alone, answer these questions:

- Does it know what done looks like?
- Can it check its own work?
- What may it touch?
- What stops it?
- Where does the result go, and who signs off?

Give it standing permission for the safe loop. That loop is running local tests, fixing failures it caused, rerunning
the tests and committing checkpoints. Then name the stops you actually want, such as irreversible or destructive
actions, publishing, and other people's areas. Put approval at the end. Have the agent first prepare a concrete result
that can be reviewed, so that the human's yes is the last step.

The loop itself belongs to the harness. That's Codex `/goal`, Claude Code `/goal`, or a Stop hook. If there's no loop,
read [persistence by model and harness](models.md#persistence-by-model-and-harness) before you add any "carry on"
wording. A session with no loop needs to be told exactly when to report back. That might be when a milestone closes,
at a seam, or when it's blocked.

## A plan for multi-hour work

Keep the plan in a file the agent rereads and updates. A file survives when the agent loses its context, and you can
audit it.

The shape below comes from OpenAI's long-horizon Codex post and its ExecPlans cookbook. Both are from the GPT-5.x era.
The shape matches what Anthropic advises about structured notes and progress files. No GPT-6 source says it again,
though, so treat it as a starting shape, not a measured rule. A plan has these parts:

- Purpose. A few sentences on what someone can do afterwards, and how to see it working.
- Milestones. Each one is an outcome you can observe, small enough to finish soon, and the riskiest comes first. Each
  has done-when checks, the commands or views that validate it, and links to evidence once it passes. Write acceptance
  as behaviour a person can check: "returns 200 with the body", not "added a HealthCheck struct".
- Work under each milestone, broken down as finely as helps. The agent ticks items off as they finish and revises them
  as it learns.
- A short status. This is the current milestone, what's happening now and since when, what's next, and what's blocked.
- A decision log, with the reason for each decision. It stops the agent going back and forth.
- A stop-and-fix rule. When validation fails, the agent repairs it before moving on.

Let the agent write its own plan from the spec. Then check the plan against this shape, and audit progress against the
plan. The plan should be rewritten in place, so that it always reads as current. If amendments keep piling up while no
done-when box moves, the plan has stopped steering the work.

## A steer to a running agent

A steer has five parts:

- The problem, in one line.
- The evidence: files, commits, figures or captures, with times.
- What it threatens: a milestone, a direction the owner gave, or a constraint.
- The outcome you want, stated as a result rather than as the fix.
- Pointers to what to consult: the design, the skill section, the research.

Have the agent make any change to the plan itself, and log why. If a milestone's meaning changes, the agent commissions
a review of the change and carries on while the review runs. The review doesn't block the work. Steer the running turn
rather than restarting it, because a course correction doesn't throw away the progress already made. After the steer,
fix whatever let the problem happen in the first place.

One house practice, which is the author's and not vendor guidance: when an agent keeps circling one defect, point it at
research into current, state-of-the-art techniques and shipped practice, rather than more tuning.

## A brief for a subagent or session

A fresh agent knows only what you write down. The brief is its whole context. A brief covers these things:

- The goal, and why it matters.
- What you've already ruled out, so the agent doesn't repeat it.
- Pointers to the files and docs worth reading, rather than their content typed out again.
- The scope, stated outright: the files it owns, what it must not touch, and what done looks like.
- What to return, and in what shape. That might be a ranked list, a file path, or a verdict for each check.

Delegate work that is parallel and independent, noisy searches whose output you don't need, and independent review.
Don't delegate something that takes a handful of tool calls. Opus 5 delegates readily, so set a limit on it. Astra
delegates less than you may want, so tell it when to delegate. Keep one writer for each set of files. A forked skill
or a fresh session can't see your conversation, so the brief has to make sense on its own.

## A brief for an independent reviewer

A reviewer is useful because it hasn't seen your reasoning. Keep it that way.

Give it the requirements, the use cases and the raw artifacts. Artifacts here means code, design, captures, logs and
measurements.

Don't give it your hypothesis, the technique you prefer, or the verdict you expect. A reviewer handed a conclusion
tends to confirm it.

Ask for everything that fails the criteria, ranked. Each finding should be marked either as verified, with a file and
line or a way to reproduce it, or as suspected. Don't ask for "only blocking issues".

For a design review, have it work out what the module must do from the brief alone, and then compare that with the
design.

For running or visual output, have it say whether it watched the motion or sampled stills, at what size, and which
build it saw.

Where you can, build the independence into its setup. Give it read-only tools, and no way to spawn other agents or
edit files.

A reviewer asked to find problems always finds something. Act on the findings that change a decision. Skip style
nitpicks and tests for cases that can't happen. Record each verdict along with the revision the reviewer saw and the
brief it was given. Evaluators tend to be lenient out of the box. So tune a standing reviewer by reading its logs and
correcting it where its judgement differs from yours.
