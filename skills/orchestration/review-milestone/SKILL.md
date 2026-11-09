---
name: review-milestone
description: Judges a claimed milestone from a clean context against its JSON done-when file, by running its checks, driving the running product on its targets, reading its diff and answering its questions, then records the verdict. Also reviews a module design before building. Part of the orchestrate set. Use when a milestone is claimed for review, or a design needs an independent read. Not for building or fixing (build-milestone).
---

# Review a milestone

`agent_loop.py review` (in the build skill's `scripts/`) starts you in a clean checkout of the claimed commit that
the loop owns, and it records and integrates your verdict once it has checked your work.
Reviewers and planners start with no inherited context, as a new session that has seen none of the builder's or the
lead's conversation, so everything you know comes from the files.

Read `ORCHESTRATE.md` first. Then read the graded examples: the file the profile's `Graded examples` line names (by
default `<evidence>/graded-examples.md`), and [the starting set](references/graded-examples.md) that comes with this
skill. They're past verdicts the owner agreed with or overturned, and they're the best guide to how strict to be.

Your job is to decide whether a milestone is really done, and to say so in a way the builder, the loop and the owner
can act on without asking you anything. You're useful because you haven't seen how the builder thought about it. So
work from the done-when file's definitions, the design, the diff and the running product. Form your own view of each
item before you read the builder's `evidence` and notes.

## A known weakness

Anthropic tested Claude (Opus 4.5 and 4.6) as a QA agent and found it lenient. It spots a real problem, talks itself
into deciding the problem is fine, and passes the work anyway. It also tends to test the obvious paths and skip the
edges. Being a separate agent from the builder doesn't fix that by itself.

So whether a defect blocks is settled by the definitions, not by your sense of whether it matters. A defect blocks
when it breaks an item's statement or the milestone's `bar`, or, outside the items, when it breaks something that
worked before, the design or a contract, loses data, opens a security hole, or is a fingerprint of faked work (below).
A blocking defect in an item fails that item. Report every other defect too, as advisory: it doesn't fail the
milestone, and the owner can promote it.

Use the product yourself, on the real target, built from the commit you were given in a clean checkout of it. Take
your own captures. The builder's screenshots show what the builder wanted you to see. Run the edge conditions the
profile lists for each item's target, and say which ones you ran. If you've only seen something work on the easy
path, you don't know that it works, so mark it `cant_tell`.

## Done when

1. Every item has a `verdict`: `pass`, `fail` or `cant_tell`. An item only passes if every proof it uses passes
   ([proofs](../plan-module/references/proofs.md)). Run each `check` yourself. For each `inspect`, write your
   inspection list before you look ([how to inspect](../plan-module/references/proofs.md#how-to-inspect)), then
   judge each entry against the item and the milestone's `bar`. For each `ask`, read the code on both sides of the
   boundary and answer the question. If you couldn't perceive or reach something, mark it `cant_tell` and say what
   evidence would settle it. Don't guess.
2. You've read the milestone's whole diff, not just the files the items mention. On a module's last milestone, read
   the whole module. Look for the fingerprints of work that only looks finished: hard-coded returns, canned data,
   feature flags defaulted on, branches that only run under test, tests that were weakened or deleted, warnings
   silenced, and output files committed instead of computed.
3. Each finding gives enough for someone to reproduce and locate it: what you did, what happened, what should have
   happened, and where (a file and line, steps to reproduce it, or a capture). Put the worst first, mark each
   blocking or advisory, and say whether you verified it or only suspect it. Include problems outside the items, and
   items too weak to catch a fake.
4. The verdict is written down. Put the full review in `<evidence>/<MODULE>/<milestone>-review.md`, with your
   inspection lists. In the done-when file, set each item's `verdict` and point its `review` at that file. Then move
   the milestone on as [the transition table](../plan-module/references/done-when.md#who-changes-what-and-when) says.
   If every verdict is `pass` and nothing outside the items blocks, set `state` to `done`. Otherwise, set `state`
   back to `in_progress` and add 1 to `fails`. A `cant_tell` counts as a fail, because nobody could check it. A
   blocking defect outside the items fails the milestone too, and the review proposes an item that would have caught
   it. Advisory findings never change the state.
   Change only those two files, and don't commit: the loop checks that nothing else changed, sets failed items back
   to `open`, and lands the verdict on the integrated tip itself.
5. Your last line is `PASS <milestone>` or `FAIL <milestone>: <n> fail, <n> cant_tell, <n> outside the items`, counting
   blocking findings only.

Don't change anything else. If you fix what you find, there's no longer an independent check on the fix, and if you
change the definitions or touch another milestone, the loop rejects the whole review and nothing of it lands.

## Things that fool the builder's own checks

Watch for work that has the look without the behaviour, such as stubs, canned data, or buttons that don't do
anything. Watch for work that was only judged in the lab: slowed down, close up, or on a faster machine than the
user's. And watch for work that's technically correct but too subtle for anyone to notice from where the user
actually is.

## Reviewing a design

Sometimes you'll be given a module's brief and its design instead of a milestone. Read the brief first and work out
what the module must do. Then compare that with the design. Look for things it misses, things it adds that nobody
asked for, and mechanisms nobody has shown can produce their behaviour.

Then read the done-when items. Could you actually judge each one, and would it catch a convincing fake? Agreeing the
items before building starts is what makes the later verdict fair.

Write the review to `<evidence>/<MODULE>/design-review.md`, with every finding ranked and marked blocking or advisory.
A finding is blocking when building as designed would go wrong: a mechanism that can't produce the behaviour, a gap
against the brief or a contract, or an item no reviewer could judge or that a convincing fake would pass. A sharper
proof, an extra edge case or clearer wording is advisory. The planner folds advisory findings in without another
review, and the milestone reviews catch what's left, so don't hold the design back for them.

If a `design-review.md` is already there, it's the last round. Check each of its blocking findings first and say
whether it's resolved. Then raise a new blocking finding only for something the revision broke, or something missed
last time that really is blocking. Reviews that find one more refinement each round never let the build start.

Don't touch the done-when file, because no milestone is being judged. Your last line is `DESIGN OK` (advisory
findings can come with it) or `DESIGN CHANGES: <n> blocking findings`. The loop
records the verdict against the design as it stands, so no milestone of the module is built until a design review
passes, and a later change to the design needs another.

## When the owner disagrees

When the owner overturns a verdict, add it to the project's graded examples. Note what was judged, each item's verdict
and your reason, and what the owner said instead. Add the verdicts the owner confirmed too, especially close calls,
so the examples show where the line is from both sides.
