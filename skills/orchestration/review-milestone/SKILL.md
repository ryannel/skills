---
name: review-milestone
description: Judges a milestone from a clean context against its JSON done-when file, by running its checks, driving the running product on its target and reading what its items ask, and records the verdict, in a repository with an ORCHESTRATE.md. Also reviews a module design and its done-when items before building. Use when a milestone is claimed and has items to inspect or ask, or a design needs an independent read. Not for building or fixing (build-milestone).
---

# Review a milestone

Run as Claude Opus 5.5 at medium effort in a clean context: the `orchestrate-evaluator` agent, or its Codex twin. Read
`ORCHESTRATE.md` first, and `<evidence>/graded-examples.md` if it exists.

**Outcome:** a verdict the generator, the loop and the owner can act on without asking you anything. Write it to
`<evidence>/<module>/<milestone>-review.md` and summarise it in the done-when file.

You're useful because you haven't seen the author's reasoning. Work from the done-when file, the design and the commit
range. Form your own view before you read the author's notes.

## Why this skill pushes hard

Anthropic found that Claude, used out of the box as QA, finds real issues and then talks itself into deciding they
don't matter, approves anyway, and tests the surface rather than probing edge cases. Separating the evaluator from the
generator didn't fix that on its own. The rules below are there to counter it.

- **A defect you found is a fail.** Don't argue an issue down to a pass. If you think it doesn't matter to the user,
  fail the item anyway and say why you think so; the owner can overturn it, and the overturn becomes a graded example.
- **Use the product the way a user would.** Drive it yourself on the item's target (a browser through Playwright, the
  simulator, the CLI) and make your own captures from the commit under review. The generator's captures and evidence
  are claims to test, not proof.
- **Probe before you pass.** For each item, try the edge conditions the profile lists for its target, the second and
  third levels of a feature, and the input most likely to break it. An item you only saw work on the happy path is
  `cant_tell`, not `pass`.
- **Check it's real.** Display-only controls, stubbed back ends, canned data and placeholders that look finished all
  fail, however good they look.
- **Judge each item on its own.** Strong design doesn't make up for a missing behaviour.

## Done when

1. **Every item has a verdict,** `pass`, `fail` or `cant_tell`. An item with several proofs needs each of them to
   pass ([proofs](../plan-module/references/proofs.md)):
   - **`check`:** run it yourself.
   - **`inspect`:** capture it and judge it against the statement and the `bar`, saying what you looked at, at what
     size and from which build.
   - **`ask`:** read the producers and consumers together and answer the question.

   Use `cant_tell` for anything you couldn't perceive or reach, with the reason, rather than guessing.
2. **Every finding can be acted on without more investigation.** Each says what you did, what happened, what should
   have happened, and where: a file and line, reproduction steps, or a capture. Rank findings by consequence, and
   mark each verified or suspected. Include anything wrong outside the items, and items too weak to catch a plausible
   wrong substitute.
3. **The verdict is recorded.**
   - In the done-when file, set each item's `status` and add a link to your review to its `evidence`.
   - If everything passes, set the milestone's `state` to `done`.
   - If anything fails, add 1 to `fails`.
   - Commit and integrate these files.
4. **You end with one line:** `PASS <milestone>` or `FAIL <milestone>: <n> items`.

You only read code: never fix what you find, so the findings stay independent.

## Failures that pass an author's own checks

- **The look without the behaviour.**
- **Judged in the lab:** fine on a fast machine, up close or slowed down, but wrong at real speed, size or network.
- **Correct but imperceptible** where the user actually is.
- **Tuning a mechanism that can't produce the behaviour.**
- **Notes growing while the visible defect stays.**

## Design review

When you're given a module brief and design, first work out what the module must do from the brief alone. Then compare
that with the design and report omissions, unsupported additions, and mechanisms not shown to produce their behaviour.
Also check every done-when item: would you be able to judge it, would it catch the plausible wrong version, and is
anything the user would notice missing? Agreeing the items before building is what makes the later verdict fair.

## Calibration

When the owner overturns a verdict, add it to `<evidence>/graded-examples.md`: what was judged, each item's verdict
with its reason, and the owner's correction. Future reviews match that standard.
