---
name: plan-module
description: Plans software work for AI agents to build. For a whole project it sets the module map, build order and shared contracts. For one module (a feature area, service, screen flow, subsystem or command group) it writes the design, the milestones and a JSON done-when file saying how each milestone is proved. Also sets a repository up with its ORCHESTRATE.md profile. Use when starting a project, a goal or a module, redesigning or re-planning one, settling a contract change, or after a milestone fails review four times. Not for building (build-milestone) or judging (review-milestone).
---

# Plan

Run as Claude Opus 5.5 at high effort. Read `ORCHESTRATE.md` at the repository root first. If there isn't one, write
it from [the profile template](references/profile.md): work out what you can from the repository, and ask the owner
once for the rest.

**Outcome:** a capable generator can build each milestone without asking, and an evaluator can judge it. The files go
in the profile's `Plans` directory:
- `<MODULE>.md`: the design. It covers what users must see, feel or get, with operating ranges; the mechanisms that
  produce it; contracts with other modules; and cost where performance matters.
- `<MODULE>-PLAN.md`: the milestones, status lines and a log.
- `<MODULE>-DONE.json`: every milestone's done-when items ([format](references/done-when.md)), each proved in one of
  the [ways to prove work](references/proofs.md).

## Whole project

When a project has more than one module, `ARCHITECTURE.md` in the plans directory (or wherever the profile's project
guidance says) holds:
- the module map, drawn around who owns each kind of state;
- the build order, riskiest and most depended-on first;
- the shared contracts, each with its producer, consumers and how a violation is detected;
- a brief per module: its purpose, consumers, required experiences and what's out of scope.

A module that needs a contract changed writes the proposal in its plan log. Settle it here with the module's
producers and consumers.

## How

- **Research before designing.** Look at how shipped products and current work solve the problem, and prefer current
  practice. Earlier code in the repository is evidence, not a template.
- **Check each mechanism can produce its behaviour across the range** before anyone builds on it. Leave
  implementation technique to the generator, because a wrong detail in a plan carries through the whole build.
- **Milestones are small outcomes a user could observe on a named target,** riskiest first. A milestone that
  delivers more than one outcome is two milestones. Its items can be many and granular, each proved by whatever mix
  would catch the plausible wrong version.
- **Use real cost targets only,** from the purpose doc or the owner. Otherwise record measurements and tripwires.
- **For existing code,** choose the target first, then decide what to keep, adapt, replace or remove.

## Done when

- The design, plan and done-when file exist and agree with each other, with the contracts and with the module brief.
- An independent reviewer has worked out what the module must do from the brief alone and compared that with your
  design and done-when items (`/review-milestone`, design review), and you've acted on its findings. Record it on the plan's `Reviews:`
  line. If you're running as a subagent and can't launch one, say the review is still owed.
- The plan's `Milestone:`, `Now:`, `Next:` and `Blocked:` lines are current.

## Re-planning after four failed reviews

Read the verdicts, then split the milestone, re-scope it, or redesign the mechanism. Log why, set `fails` back to 0,
and add 1 to `replans`.

The profile's "Owner decides" list says what goes to the owner. Everything else is yours to decide.
