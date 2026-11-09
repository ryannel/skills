---
name: plan-module
description: Plans software work for AI agents to build, as part of the orchestrate set. For a project, it draws the module map, build order and contracts; for a module, it writes the design, milestones and JSON done-when file; it also writes the ORCHESTRATE.md profile. Use when starting or re-planning a project, goal or module, settling a contract change, or after a milestone fails review four times. Not for building (build-milestone) or judging (review-milestone).
model: claude-opus-5-5
effort: high
---

# Plan

Start by reading `ORCHESTRATE.md` at the root of the repository. It tells you where things live and what this project
cares about. If there isn't one, write it from [the template](references/profile.md). Fill in what you can work out
from the repository, then ask the owner once for the rest.

Your job is to make plans good enough that a builder can build each milestone without asking you anything, and a
reviewer can tell whether it's done. For each module, that means three files in the plans directory:

- `<MODULE>.md` is the design. It says what users need to see, feel or get, and across what range. It says what
  mechanisms produce that, what this module promises other modules, and what it costs, if cost matters.
- `<MODULE>-PLAN.md` is the plan: the milestones, a few status lines, and a log.
- `<MODULE>-DONE.json` says, for each milestone, what has to be true for it to count as done, and how each thing is
  proved. The [format](references/done-when.md) is strict, because a script reads it. The
  [ways to prove work](references/proofs.md) cover tests, inspection and review, and how to mix them.

If a module already has a plan in another shape, such as a checklist in prose, convert it: keep its log, turn each
milestone's "done when" list into items, and give every item a proof.

## The whole project

If the project has more than one module, plan the project first. Write `ARCHITECTURE.md` in the plans directory, or
wherever the profile says. It holds the list of modules and what each one owns, the order to build them in, the
contracts between them, and a short brief for each module.

Draw module boundaries around state. Each kind of state should have exactly one module in charge of it, because two
modules editing the same thing is where bugs breed. Build the riskiest and most depended-on modules first, because
they're the ones most likely to force everything else to change.

Modules don't change contracts on their own. When one needs a change, it writes a proposal in its plan log, and you
settle it here with every module that produces or uses that contract.

## Linking modules that depend on each other

When you plan a module, list every capability it uses from other modules. For each one, the module map says which
module owns it. Find the milestone in that module that delivers it, and add it to the `needs` of the first milestone
here that can't work without the real thing, as `"CORE:M3"`. If no milestone there delivers it yet, add one to that
module, or move one earlier, as a re-plan of that module. Write the contract first, so this module can build against
a stand-in until the milestone that needs the real thing. The loop won't start a milestone until everything in its
`needs` is accepted, so a missing link lets a builder start too early, and an unnecessary one holds work back.

When a builder reports `BLOCKED` because something another module owns is missing, decide who owns it from the map.
If another module does, add the milestone there and the `needs` link here. If it's really this module's work, add it
to this module's plan. If the map was wrong, fix the map and the contract first. Never let the blocked builder build
another module's capability inside its own module, because then two modules own the same thing.

## How to plan well

Research before you design. Most problems have been solved before, in shipped products or published work, so find
out how before inventing something. Prefer current practice. Old code in the repository is evidence of what was tried,
not a template.

Settle the mechanisms that matter, and leave the implementation details to the builder. A mechanism is the core idea
that produces the behaviour, like "the wake is a simulated height field, not a scrolling texture". If you leave that
open, the builder may pick one that can't work. The details are everything that can change without changing the
behaviour, like data layout or which file a function lives in. A wrong detail in a plan gets copied faithfully through
the whole build, so leave those out.

Before anyone builds on a mechanism, check that it can actually produce the behaviour you need, across the whole
range. A lot of wasted effort goes into tuning mechanisms that could never have worked.

Make each milestone one coherent outcome that a reviewer can judge, and put the riskiest first. Usually that's
something a user could notice on a real target. For internal work, like a solver or a data pipeline, it can be a
property you can measure, as long as the items say how it's observed. It can have as many done-when items as it
needs, and small specific items make better reviews than big vague ones.

Mark an item `attended` when it needs a person or physical hardware, such as a phone plugged in or a permission
prompt approved. Builders then do everything else first and the owner gets those items in one batch.

Only use cost targets that are real, from the purpose doc or the owner. If nobody has set one, record measurements
and set tripwires instead of making a number up.

## Done when

- The design, the plan and the done-when file exist, and they agree with each other, with the contracts and with the
  module's brief.
- Someone else has reviewed them. Run `agent_loop.py review --module <M> --milestone design --worktree .` (in the
  build skill's `scripts/`), which gives a fresh reviewer only the brief and design and records the verdict, so the
  loop won't build the module until a design review passes. Act on what it finds, and put the review on the plan's
  `Reviews:` line. If you're running inside a loop session and can't start one, say that the design review is owed;
  the lead runs it.
- The plan's `Milestone:`, `Now:`, `Next:` and `Blocked:` lines are up to date.

## When a milestone fails review four times

Something about the plan is wrong. Read the reviews and decide whether the milestone was too big (split it),
depended on something outside this module (re-scope it), or used a mechanism that can't work (redesign it). Write down
why in the log. Then, in one commit, change the definitions, set `fails` to 0, add 1 to `replans`, and set `state` to
`open`. Milestones you split off start with the same `replans` count, so a second run of failures still ends in
parking rather than another re-plan. The loop records the new definitions after your turn and clears the old proof,
because it proved something else. Never edit a `-ACCEPTED.json` file: only the loop writes those, and it rejects a
plan that touches one.

When the owner changes what they want, rather than a milestone failing, they apply it with `owner scope`, which
doesn't spend a re-plan. If you're asked to write that change, edit the done-when file and leave it uncommitted for
the owner to apply.

The profile's "Owner decides" list says what has to go to the owner. Everything else is yours to decide.
