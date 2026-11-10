# Kinds of prompt

Everything in the main file applies to each kind. This file says what each kind adds.

Contents: [A brief for a subagent or another session](#a-brief-for-a-subagent-or-another-session) ·
[A goal for a long unattended run](#a-goal-for-a-long-unattended-run) · [A review request](#a-review-request) ·
[A steer](#a-steer) · [A system prompt](#a-system-prompt)

## A brief for a subagent or another session

A subagent is a second agent that you start to do part of your task. A brief is the prompt you give it.

Before you write the brief, find out what the new agent starts with. The tool that starts it says so in its
description. On some hosts the new agent starts with only your brief. On some it also reads the instruction
files. On some it gets a copy of your whole conversation. Write for what it has.

A brief adds two things:

- What you have already ruled out, so the subagent doesn't start there.
- How long a reply you want. Twenty long reports fill your context as surely as doing the work yourself.

Example:

> The export job writes the wrong totals for accounts with refunds. I've confirmed the totals are right in the
> database and wrong in the CSV, so the fault is between `export/query.py` and `export/write.py`. I have not
> looked at the currency conversion step.
>
> Find the cause and tell me what it is. Don't fix it yet, because another session is editing `export/`.
> Reply in under 200 words: the cause, the file and line, and how you confirmed it.

## A goal for a long unattended run

A goal is a prompt for a run that nobody is watching, which may last hours.

A goal adds five things:

- **A done the reader can check without you.** "All tests in `tests/billing` pass and `make lint` exits 0"
  works. "The billing module is in good shape" doesn't.
- **What "blocked" means,** as something the reader can observe: "the staging database refuses the
  connection". When one part is blocked, the reader should say so and carry on with the rest.
- **Two kinds of obstacle.** An ordinary one, such as an error, a timeout or a failing tool, is for the reader
  to work through. A deliberate one, such as a file marked not to touch or access the reader was not given, is to
  be left alone and reported.
- **When to stop and when not to.** Say which stops you don't want: ending on a summary that announces the next
  step without taking it, offering to continue, listing decisions that don't block the work. Say that approval
  comes last, on a finished result the person can review.
- **Where progress is recorded,** such as a notes file the reader updates. A long run outlives its context,
  and the file is what the next context reads.

Example:

> Goal: every stale feature flag in `services/checkout` is removed, with no change in production behaviour.
>
> A flag is stale when its value has been the same for every user for 90 days. `tools/flag-history` prints the
> history for a flag. Flags also reach the code through the enum in `flags/names.ts` and through names built at
> runtime in `flags/dynamic.ts`, so search for those as well as for the literal names.
>
> Keep any flag whose description says it is a kill switch. Don't change live flag configuration; this task only
> removes code.
>
> Open one draft pull request per flag, and put the output of `tools/flag-history` in its description. Record
> each flag and its status in `notes/flag-cleanup.md` as you go. You are done when every flag in
> `services/checkout` is listed there as removed, kept with a reason, or blocked with a reason, and `make test`
> passes on each pull request.
>
> If a tool fails or a test breaks, work out why and carry on. If you find something that is protected on
> purpose, leave it and note it in the file. Don't stop to ask whether to continue; I will review the pull
> requests when the list is complete.

## A review request

A reviewer is useful because it has not seen how the work was made.

- Leave out your list of worries and your account of why the work is right, as well as your conclusion.
- Give it what to compare the work against: the spec, the ticket, the list of what done means.
- Say what kind of finding you want. A reviewer asked to find problems always finds some. "Report gaps that
  affect correctness. Leave style alone." keeps the review to what matters.

Example:

> Review the diff between `main` and `rate-limiter` against `docs/rate-limiter-spec.md`. Check that each
> requirement in the spec is implemented and that each edge case the spec lists has a test. Report only gaps
> that affect correctness; leave style alone. For each gap give the requirement, the file and line, and whether
> you confirmed it by running something.

## A steer

A steer is a message to an agent that is already working. It arrives in the middle of the agent's own plan.

- Say what changes and what stays: "Keep the schema change. Drop the migration script; we'll run it by hand."
- Give new facts as facts: "The staging database was reset at 14:00, so the seed data is gone."
- Say what you approve, not a bare "continue": "Yes, run the migration on the staging database."
- If you undid one of its edits, tell it, or it may make the edit again.
- After two corrections that didn't work, stop steering. Write one new prompt that includes what you learned,
  and start a new conversation with it. A third correction adds to a context that already holds two failed
  attempts.

## A system prompt

A system prompt is read at the start of every conversation an application has.

- Put the approval rules in one place. One compact policy covers most applications: for a request to explain,
  review or plan, look and report without changing anything; for a request to change or fix, make the change
  and run checks that can't cause harm; ask before an external write, a deletion, a purchase or a wider scope.
- Describe tone by the writing choices, not by a label. "Friendly" is ambiguous. "State the answer first. If the
  user reports a problem, acknowledge that problem before giving the next step." is not.
- For a short answer, say what it must keep: the conclusion, the evidence, any caveat, the next action.
- Put the text that stays the same first and the context for one request last. Mark that context with tags, so
  the reader can tell data from instructions.
- To shorten a system prompt that works, remove one group of lines at a time and see whether the results hold.
  OpenAI measured better scores from shorter system prompts.
