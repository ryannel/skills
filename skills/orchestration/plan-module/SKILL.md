---
name: plan-module
description: Designs one module of a software project and plans it as milestones, with one JSON done-when file per module, in a repository using the orchestrate process (ORCHESTRATE.md). Use when starting, substantially redesigning or re-planning a module (a feature area, service, screen flow, subsystem or command group), when reconciling existing code with a target design, or when a milestone has failed review four times. Not for building a milestone (build-milestone) or project-wide boundaries and contracts (plan-project).
---

# Plan a module

Run as Claude Opus 5.5 at high effort. Read `ORCHESTRATE.md` first; if the repository has none, set it up with `/orchestrate` before anything else.

**Outcome:** the module has one current design and a plan of milestones. A capable generator can build each milestone
without asking, and an evaluator can judge it. In the profile's plans directory:
- `<MODULE>.md` is the design ([what it covers](references/design.md));
- `<MODULE>-PLAN.md` is the plan, with status lines, the milestones and a log;
- `<MODULE>-DONE.json` holds every milestone's done-when items ([plan and done-when](references/plan.md)).

## What to produce

- **The brief.** Start from `<plans>/<MODULE>-BRIEF.md`, which `/plan-project` wrote. If there is none, write it: from
  the purpose doc for a single-module project, otherwise as a short draft flagged for `/plan-project`.
- **Research, then design the whole module before planning it.** Start from what the user must see, feel or get, with
  operating ranges. Find how shipped products and current research solve it, favouring current state-of-the-art and
  shipped practice. Check that each chosen mechanism can produce its behaviour across the range before anyone builds
  on it. Earlier work in the repository is evidence, not a technique to copy.
- **Results, not technique detail.** Keep the design at the level of mechanisms, contracts and cost, and leave
  implementation technique to the generator's research. A wrong detail in a plan carries through the whole build.
- **Milestones.** Each is one small outcome a user could observe on a named target, riskiest first. Done-when items are
  behaviour a person can verify, proved by an oracle command, an inspection list or a review. Visual and interaction
  items are judged against an inspection list and the profile's quality bar in words, never a target image.
- **Cost,** where performance matters: a cost account and tripwires, never invented budgets ([cost](references/cost.md)).
- **Existing code:** choose the target first, then reconcile what exists against it: keep, adapt, replace or remove,
  with reasons.
- Use the project guidance the profile lists for planning.

## Done when

- The design, plan and done-when file exist and agree. A read-only pass compares them with the profile's contracts
  file and the architecture brief, and its result is in the plan's log. A conflict with a contract is a proposal to
  `/plan-project`, not a local edit.
- An independent reviewer has derived what the module must do from the brief alone and compared it with the design and
  plan ([review](../review-milestone/references/review.md#the-two-reviews-that-matter-most)), and you've acted on its
  findings. The verdict is on the plan's `Reviews:` line with the revision it saw. If you're running as a subagent and
  can't start one, end by saying the review is owed; the lead runs it.
- The plan's `Milestone:`, `Now:`, `Next:` and `Blocked:` lines are current.

## Re-planning a failed milestone

After four failed reviews, read the evaluator verdicts and the progress note, then decide one of:
- **Split:** the milestone was too big.
- **Re-scope:** it hinged on something another module controls.
- **Redesign:** the mechanism can't produce the behaviour. Revise the design and have the change reviewed.

Edit the plan and done-when file, log why, reset the milestone's `fails` to 0 and increase its `replans` by one. A
milestone that fails four more times after a re-plan is parked for the owner.

## Boundaries

- **Without asking, you may:** research; delegate research or review to subagents; write throwaway work in the
  profile's scratch location; edit this module's design, plan and done-when file; integrate verified planning changes
  as the profile says.
- **What goes to `/plan-project`:** boundary questions, contract changes and build order.
- **What goes to the owner:** whatever the profile's "Owner decides" line lists.
- **Licences:** as the profile says. Code under a licence the project can't use may inform ideas only.
