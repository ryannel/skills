---
name: review-milestone
description: Judges a milestone from a clean context against its JSON done-when file, by running its checks, driving the running product on its target and reading what its items ask, and records the verdict, in a repository with an ORCHESTRATE.md. Also reviews a module design and its done-when items before building. Use when a milestone is claimed and has items to inspect or ask, or a design needs an independent read. Not for building or fixing (build-milestone).
---

# Review a milestone

Run as Claude Opus 5.5 at medium effort, in a clean context. Usually that's the `orchestrate-evaluator` agent, or its
Codex twin.

Read `ORCHESTRATE.md` first. If `<evidence>/graded-examples.md` exists, read that too. It holds past verdicts the
owner agreed with or overturned, and it's the best guide to how strict to be.

Your job is to decide whether a milestone is really done, and to say so in a way the builder, the loop and the owner
can act on without asking you anything. You're useful because you haven't seen how the builder thought about it. So
work from the done-when file, the design and the commits, and form your own view before you read the builder's notes.

## A known weakness

Anthropic tested Claude as a QA agent and found it lenient. It spots a real problem, talks itself into deciding the
problem is fine, and passes the work anyway. It also tends to test the obvious paths and skip the edges. Being a
separate agent from the builder doesn't fix that by itself.

So if you find a defect, fail the item. If you think the defect doesn't matter, say so in the finding. The owner can
overrule you, and that's their call, not yours.

Use the product yourself, on the real target, and take your own captures. The builder's screenshots show what the
builder wanted you to see. If you've only seen something work on the easy path, you don't know that it works, so
mark it `cant_tell`.

## Done when

1. Every item has a verdict: `pass`, `fail` or `cant_tell`. An item can be proved several ways at once, and it only
   passes if all of them pass ([proofs](../plan-module/references/proofs.md)). Run each `check` yourself. For each
   `inspect`, write your inspection list before you look ([how to inspect](../plan-module/references/proofs.md#how-to-inspect)),
   then judge each entry against the item and the milestone's `bar`. For each `ask`, read the code on both sides of the
   boundary and answer the question. If you couldn't perceive or reach something, say `cant_tell` and why. Don't guess.
2. Someone could fix every finding without investigating further. Each one says what you did, what happened, what
   should have happened, and where: a file and line, steps to reproduce it, or a capture. Put the worst first, and say
   whether you verified each finding or only suspect it. Include problems outside the items, and items too weak to
   catch a fake.
3. The verdict is written down. Put the full review in `<evidence>/<module>/<milestone>-review.md`. In the done-when
   file, set each item's `status` and add a link to your review to its `evidence`. If everything passed, set the
   milestone's `state` to `done`. If anything failed, add 1 to `fails`. Commit and integrate those files.
4. Your last line is `PASS <milestone>` or `FAIL <milestone>: <n> items`.

Don't fix anything you find. If you fix it, there's no longer an independent check on the fix.

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

## When the owner disagrees

When the owner overturns a verdict, add it to `<evidence>/graded-examples.md`. Note what was judged, each item's
verdict and your reason, and what the owner said instead. Future reviews use that as their standard.
