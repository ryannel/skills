# Kinds of prompt

## A brief for a subagent or another session

A subagent is a second agent you start to do part of your task, and the brief is the prompt you give it. The
difference from an ordinary prompt is that you don't know for sure what the new agent can already see. On some
hosts it starts with only your brief, on some it also reads the instruction files, and on some it gets a copy of
your whole conversation. The tool that starts it says which in its description, so check before you write, and
write for what it will have.

Two things matter more in a brief than elsewhere. Say what you have already ruled out, or the subagent will
start by checking it again. And say how long a reply you want, because the reply lands in your own context:
twenty long reports fill it as surely as doing the work yourself.

> The export job writes the wrong totals for accounts with refunds. I've confirmed the totals are right in the
> database and wrong in the CSV, so the fault is between `export/query.py` and `export/write.py`. I have not
> looked at the currency conversion step.
>
> Find the cause and tell me what it is. Don't fix it yet, because another session is editing `export/`.
> Reply in under 200 words: the cause, the file and line, and how you confirmed it.

## A goal for a long unattended run

A goal is a prompt for a run that nobody is watching, which may last hours. Nobody will be there to answer a
question, so the goal has to settle in advance everything the reader would otherwise stop to ask.

Start with what done looks like, in terms the reader can check on its own: "every test in `tests/billing`
passes and `make lint` exits 0", not "the billing module is in good shape". Then say what blocked looks like,
also as something the reader can observe, such as "the staging database refuses the connection", and tell it to
note the blocked part and carry on with the rest.

The reader will hit obstacles, and it needs to know which kind is which. An error, a timeout or a failing tool is
an ordinary obstacle, and the reader should work through it. A file marked not to touch, or access it wasn't
given, is there on purpose, and the reader should leave it alone and report it. Say also that you will review
the result when the run is finished, so the reader doesn't stop partway to ask whether to continue.

Last, say where progress is recorded, such as a notes file the reader keeps up to date. A long run outlives its
context, and that file is what the next context reads.

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

A reviewer is useful because it hasn't seen how the work was made. Everything you add about how it was made
takes that away, so leave out your worries, your account of why the work is right, and your own conclusion.

What the reviewer does need is something to compare the work against, such as the spec, the ticket or the
description of done. It also needs to know what kind of finding you want, because a reviewer asked to find
problems always finds some. "Report gaps that affect correctness, and leave style alone" keeps the review on
what matters. The before and after in the main file is a review request written this way.

## A steer

A steer is a message to an agent that is already working. It arrives in the middle of the agent's own plan, so
it has to say exactly what changes and leave the rest of the plan standing.

- Say what changes and what stays: "Keep the schema change. Drop the migration script; we'll run it by hand."
- Give new facts as facts: "The staging database was reset at 14:00, so the seed data is gone."
- When you approve something, name it. "Yes, run the migration on the staging database" is clearer than
  "continue".
- If you undid one of its edits, tell it, or it may make the edit again.

After two corrections that didn't work, stop steering. Each failed attempt stays in the agent's context and
keeps pulling on what it does next. Write one new prompt that includes what you learned, and start a new
conversation with it.

## A system prompt

A system prompt is read at the start of every conversation an application has, so each line in it applies to
requests you haven't seen yet.

- Put the approval rules in one place. One short policy covers most applications: when asked to explain,
  review or plan, look and report without changing anything; when asked to change or fix something, make the
  change and run checks that can't cause harm; get approval before an external write, a deletion, a purchase or
  a wider scope.
- Describe tone by the writing choices, not by a label. "Friendly" can mean many things. "State the answer
  first. If the user reports a problem, acknowledge that problem before giving the next step" can't.
- If answers must be short, say what a short answer still has to keep: the conclusion, the evidence, any caveat
  and the next action.
- Put the text that stays the same first, and the context for one request last. Mark that context with tags, so
  the reader can tell data from instructions.

To shorten a system prompt that already works, remove one group of lines at a time and check whether the
results hold. OpenAI found that shorter system prompts scored better.
