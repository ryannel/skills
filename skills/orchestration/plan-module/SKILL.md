---
name: plan-module
description: Plans software work for AI agents to build. For a whole project, it draws the module map, build order and shared contracts. For one module (a feature area, service, screen flow, subsystem or command group), it writes the design, the milestones and a JSON done-when file that says how each milestone is proved. It also sets a repository up with its ORCHESTRATE.md profile. Use when starting a project, a goal or a module, redesigning or re-planning one, settling a contract change, or after a milestone fails review four times. Not for building (build-milestone) or judging (review-milestone).
---

# Plan

Run as Claude Opus 5.5 at high effort.

Start by reading `ORCHESTRATE.md` at the root of the repository. It tells you where things live and what this project
cares about. If there isn't one, write it from [the template](references/profile.md). Fill in what you can work out
from the repository, then ask the owner once for the rest.

Your job is to make plans good enough that a builder can build each milestone without asking you anything, and a
reviewer can tell whether it's done. For each module, that means three files in the plans directory:

- `<MODULE>.md` is the design. It says what users need to see, feel or get, and across what range. It says what
  mechanisms produce that, what this module promises other modules, and what it costs, if cost matters.
- `<MODULE>-PLAN.md` is the plan: the milestones, a few status lines, and a log.
- `<MODULE>-DONE.json` says, for each milestone, what has to be true for it to count as done, and how each thing is
  proved. The [format](references/done-when.md) is strict, because scripts read it. The
  [ways to prove work](references/proofs.md) cover tests, inspection and review, and how to mix them.

## The whole project

If the project has more than one module, plan the project first. Write `ARCHITECTURE.md` in the plans directory, or
wherever the profile says. It holds the list of modules and what each one owns, the order to build them in, the
contracts between them, and a short brief for each module.

Draw module boundaries around state. Each kind of state should have exactly one module in charge of it, because two
modules editing the same thing is where bugs breed. Build the riskiest and most depended-on modules first, because
they're the ones most likely to force everything else to change.

Modules don't change contracts on their own. When one needs a change, it writes a proposal in its plan log, and you
settle it here with every module that produces or uses that contract.

## How to plan well

Research before you design. Most problems have been solved before, in shipped products or published work, so find
out how before inventing something. Prefer current practice. Old code in the repository is evidence of what was tried,
not a template.

Before anyone builds on a mechanism, check that it can actually produce the behaviour you need, across the whole
range. A lot of wasted effort goes into tuning mechanisms that could never have worked.

Stay at the level of results and mechanisms, and leave the techniques to the builder. A wrong detail in a plan gets
copied faithfully through the whole build.

Make each milestone one small outcome a user could notice on a real target, and put the riskiest first. If a
milestone delivers two outcomes, it's two milestones. It can have as many done-when items as it needs, though, and
small specific items make better reviews than big vague ones.

Only use cost targets that are real, from the purpose doc or the owner. If nobody has set one, record measurements
and set tripwires instead of making a number up.

If there's existing code, decide what you want first, then decide what to keep, change, replace or delete.

## Done when

- The design, the plan and the done-when file exist, and they agree with each other, with the contracts and with the
  module's brief.
- Someone else has reviewed them. Give a fresh `/review-milestone` reviewer only the brief, and let it work out what
  the module must do. Then it compares that with your design and done-when items. Act on what it finds, and note the
  review on the plan's `Reviews:` line. If you're running as a subagent and can't launch one, say that the review
  is still owed.
- The plan's `Milestone:`, `Now:`, `Next:` and `Blocked:` lines are up to date.

## When a milestone fails review four times

Something about the plan is wrong. Read the verdicts and decide whether the milestone was too big (split it), depended
on something outside this module (re-scope it), or used a mechanism that can't work (redesign it). Write down why,
set `fails` back to 0, and add 1 to `replans`.

The profile's "Owner decides" list says what has to go to the owner. Everything else is yours to decide.
