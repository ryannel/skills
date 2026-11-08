---
name: review-milestone
description: Judges a milestone from a clean context against its JSON done-when file and inspection list, by running the oracle checks and inspecting captures from the named target, then records the verdict, as part of the orchestrate process. Use when a milestone marked for review has all items claimed, at module close, or to review a module design and plan before building. Not for building or fixing (build-milestone).
---

# Review a milestone

Run as Claude Opus 5.5 at medium effort in a clean context, as the `orchestrate-evaluator` agent (from a Codex chat,
its `gpt-6.1-sol` medium twin), unless `ORCHESTRATE.md` says otherwise. Read `ORCHESTRATE.md` first, and the reviewing
guidance and graded examples it lists.

**Outcome:** a verdict on one milestone the generator, the loop and the owner can act on without asking you anything,
written to `<evidence>/<module>/<milestone>-review.md` and summarised in the done-when file.

Your value is that you haven't seen the author's reasoning. Work from the requirements and raw artifacts: the done-when
file (items, inspection list, bar), the design, the commit range, the captures and logs. Don't read the author's
progress narrative until you've formed your own view.

## Done when

1. **Each item has a verdict,** `pass`, `fail` or `can't tell`, with evidence.
   - **Oracle items:** run the check yourself on the named target at the commit under review.
   - **Inspection items:** inspect captures from that build on the named target, using the profile's capture method:
     screenshot sequences, frame sequences or contact sheets, traces, or command transcripts. Say what you inspected,
     at what size, and which build. Judge against the item and the `bar`, which is acceptance in a well-reviewed shipped
     product of this kind, in words; there's no target image. Cover transitions (empty, loading, error, first use,
     resize, start and stop) where faults hide. Capture what you need yourself if it's missing.
   - **Review items:** read the code or contract change across its producers and consumers.
2. **Everything else wrong is listed, ranked by consequence,** each marked verified (file and line, a reproduction or a
   capture) or suspected. Include items too weak to catch the plausible wrong substitute.
3. **The verdict is recorded:**
   - in the review file: the commit, the build, the target, each verdict and the findings;
   - in the done-when file: each item's `status`, with a link to the review file added to its `evidence` (keep the
     generator's evidence);
   - if every item passes: set the milestone's `state` to `done`, and record the pass in the profile's status ledger
     if it has one;
   - if any item fails: increase the milestone's `fails` by one. The findings stay in the review file; the generator
     turns them into work items. `agent_loop.py next` reads `fails` to decide the escalation.
4. **You end with one line:** `PASS <milestone>` or `FAIL <milestone>: <n> items`.

## Reviewing a design and plan

When asked to review a module's design and plan before building: derive what the module must do from its brief alone,
then compare with the design and plan. Report omissions, unsupported additions, mechanisms not shown to produce their
behaviour, milestones that wouldn't show it, and items that couldn't be judged.

## Pointers

- [Review](references/review.md): what to challenge, how findings close, and common calibration failures. Read its
  calibration section before judging visual or interaction output.
- The profile's graded examples: verdicts the owner confirmed or overturned. Match their standard. When the owner
  overturns a verdict, it's added there ([format](references/graded-examples.md)).

## Boundaries

- **Read-only on code.** You may build, run checks and capture. You may edit only the review file, the done-when file
  and the status ledger.
- **Don't fix what you find,** so findings stay independent.
- **Commit and integrate** the verdict files from the worktree you were given, so the generator's next rebase has them.
