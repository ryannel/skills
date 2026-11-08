---
name: build-milestone
description: Builds, verifies and integrates the next milestone of a module from its plan and JSON done-when file, in Claude Code or Codex, in a repository with an ORCHESTRATE.md. Use for any implementation, fix or refactor there, including small slices. Not for planning (plan-module) or judging a milestone (review-milestone).
---

# Build a milestone

Run as Codex `gpt-6.1-sol` at medium effort, or as Claude Opus 5.5 at medium effort for a bounded slice. The profile
can change this. Read `ORCHESTRATE.md` first, and the building guidance it links to.

**Outcome:** the next open milestone in `<MODULE>-PLAN.md` works on its named targets, and it's integrated. For
an ordinary fix with no plan, the outcome is the fix and a test of it.

## Done when

1. **Every item for the milestone in `<MODULE>-DONE.json` is `pass`, with evidence.** You write items' `status` and
   `evidence`, and the milestone's `state`. Set it to `in_progress` when you start, and to `done` when everything
   passes and `review` is `false`. If an item is wrong or can't be met, say so in your report rather than editing it.
   How each kind of item is proved is in [proofs](../plan-module/references/proofs.md).
2. **The work is committed and integrated.** Rebase on the profile's branch, run its `Check` fresh, and push without
   force. If you're under `/build-parallel`, the loop reruns every oracle check before it accepts the claim.
3. **The plan's status lines and log are current.** Keep verified, approximate and open claims separate.
4. **The milestone is reviewed, if its `review` is `true`.** In a single chat, launch the `orchestrate-evaluator`
   agent and brief it with only the module, milestone, commit and worktree. Under `/build-parallel`, the lead launches
   it instead.
5. **You end with one line:** `DONE`, `BLOCKED: <what you probed, evidence, what would unblock it>`, or
   `NEEDS_CONTEXT: <what's missing>`.

## Method

- **Research how it's done before experimenting.** Shipped products and published work have solved most problems,
  and current practice beats older code that happens to be available.
- **After about three failed attempts at a behaviour, stop tuning.** Check whether the mechanism can produce the
  behaviour at all, using a minimal reproduction. If it can't, report `BLOCKED` with the evidence.
- **Look at the output yourself.** Capture it from the exact build on its target, including the edge conditions the
  profile lists for that target, and judge it against the inspection items. Tests don't replace looking.
- **Label stand-ins `proxy`.** Wrap runs that use a resource listed under the profile's `Exclusive resources` in
  `agent_loop.py lock <name> -- <command>` (in build-parallel's `scripts/`).
- **Contract or design changes go in the plan log as a proposal.** Carry on with work that doesn't depend on them.

You may research, run anything local, change this module's code and integrate verified work without asking. Never
force-push. The profile's "Owner decides" list says what goes to the owner.
