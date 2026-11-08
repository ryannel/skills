---
name: review-milestone
description: Judges a milestone from a clean context against its JSON done-when file, by running its checks and inspecting captures from its target, and records the verdict, in a repository with an ORCHESTRATE.md. Also reviews a module design against its brief before building. Use when a milestone is claimed and marked for review, or a design needs an independent read. Not for building or fixing (build-milestone).
---

# Review a milestone

Run as Claude Opus 5.5 at medium effort in a clean context: the `orchestrate-evaluator` agent, or its Codex twin. Read
`ORCHESTRATE.md` first, and `<evidence>/graded-examples.md` if it exists.

**Outcome:** a verdict the generator, the loop and the owner can act on without asking you anything. Write it to
`<evidence>/<module>/<milestone>-review.md` and summarise it in the done-when file.

You're useful because you haven't seen the author's reasoning. Work from the done-when file, the design, the commit
range and the raw captures. Form your own view before you read the author's notes.

## Done when

1. **Every item has a verdict,** `pass`, `fail` or `cant_tell`, with evidence. Judge each kind of item as
   [proofs](../plan-module/references/proofs.md) describes, at the commit under review and on the item's target.
   Capture anything you need that's missing.
2. **Everything else wrong is listed, ranked by consequence,** and marked verified (a file and line, a reproduction or
   a capture) or suspected. This includes items too weak to catch a plausible wrong substitute.
3. **The verdict is recorded.**
   - In the done-when file, set each item's `status` and add a link to your review to its `evidence`.
   - If everything passes, set the milestone's `state` to `done`.
   - If anything fails, add 1 to `fails`.
   - Commit and integrate these files.
4. **You end with one line:** `PASS <milestone>` or `FAIL <milestone>: <n> items`.

You only read code: never fix what you find, so the findings stay independent.

## Failures that pass an author's own checks

- **The look without the behaviour,** like a spinner standing in for real loading, or canned data standing in for a
  real query.
- **Judged in the lab:** fine on a fast machine, up close or slowed down, but wrong at real speed, size or network.
- **Correct but imperceptible** where the user actually is.
- **Tuning a mechanism that can't produce the behaviour.**
- **Notes growing while the visible defect stays.**

## Design review

When you're given a module brief and design, first work out what the module must do from the brief alone. Then
compare that with the design and report omissions, unsupported additions, mechanisms not shown to produce their
behaviour, and milestones that wouldn't show it.

When the owner overturns a verdict, add a line to `<evidence>/graded-examples.md` with what was judged, the
verdict and why. Future reviews match that standard.
