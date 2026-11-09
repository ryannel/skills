---
name: build-milestone
description: Builds, verifies and integrates the next milestone of a module from its plan and JSON done-when file, as part of the orchestrate set, in Claude Code or Codex. Use for implementation, fixes and refactors in a repository with an ORCHESTRATE.md. Not for planning (plan-module) or judging a milestone (review-milestone).
---

# Build a milestone

Read `ORCHESTRATE.md` first, and any building guidance it links to. Then find the next open milestone in
`<MODULE>-PLAN.md` and its items in `<MODULE>-DONE.json`. Your job is to make that milestone work on its real
targets and get it integrated. Below, `LOOP` means `python3 <the build skill>/scripts/agent_loop.py`.

For an ordinary fix with no plan, just fix it, add a test if one would catch the fault coming back, and integrate it
with `LOOP land --worktree .`. That takes the same lock as every builder and runs the profile's Check, so a quick fix
can't race a builder's integration or skip the gate.

## Done when

1. Every item for the milestone is `pass`, with evidence from its target. [The done-when file](../plan-module/references/done-when.md#who-changes-what-and-when)
   says which fields are yours: items' `status` and `evidence`, and the milestone's `state`. Everything else in that
   file belongs to the planner or the reviewer. If an item is wrong, or can't be met, don't edit it: say so in your
   report, because the loop rejects a claim whose definitions changed. [Proofs](../plan-module/references/proofs.md)
   explains how each kind of item is proved. An item marked `attended` needs a person or hardware you may not have:
   do every other item first, then end with `BLOCKED` naming the attended ones, so the owner can do them together.
2. The work is committed and integrated with `LOOP land --worktree .`. It rebases onto the profile's branch, runs
   the `Check`, and pushes or fast-forwards that branch the way the profile's `Integrate` line says, all under one
   lock so parallel builders don't race each other. Under `/build`, the loop then reruns the `Check` and every item's
   `check` in a clean checkout of the integrated tip before it believes you.
3. The milestone's `state` says what happens next: `claimed` if it needs review, or `done` if it doesn't. It needs
   review if any item has `inspect` or `ask`, or if it's the module's last milestone.
4. The plan's status lines and log are current. Keep what you verified separate from what you think is probably true.
5. Your last line is `DONE`, `BLOCKED: <what you tried, the evidence, what would unblock it>`, or
   `NEEDS_CONTEXT: <what's missing>`.

## Review and what follows it

Before you claim, check the `inspect` and `ask` items yourself, the same way the reviewer will.

In a single chat, you're also the lead, so start a fresh reviewer with `LOOP review --module <M> --milestone <id>
--commit <sha> --worktree .`, ideally with `--host` set to another host. Tell it nothing else, so it forms its own
view. Only a review run through the loop is recorded; a reviewer you launch some other way can't move the milestone
on, and the owner would have to accept it by hand. If you can't start one, end with `DONE` and say the review is
owed. Under `/build`, the lead runs review.

When a review fails, `LOOP next` says what the number of failed reviews calls for: fix the findings in this session,
hand over to a fresh one, or send the milestone to `/plan-module`. Follow it, because the count is the record of
what's already been tried ([the ladder](../plan-module/references/done-when.md#when-a-review-fails)).

## How to work

If the change touches behaviour, check that the affected part of the product runs before you change it. If someone
left it broken, you want to know now, not after you've built on top of it.

When the right approach isn't settled and it matters, find out how it's done before experimenting. Shipped products
and published work have solved most problems, and current practice usually beats whatever old code happens to be
lying around.

If a behaviour still won't come after three different approaches, each built and run, stop tuning. The mechanism may simply be unable to
produce it. Build a minimal reproduction to find out. If it can't, report `BLOCKED` with what you found.

Look at the output yourself. For each `inspect` item, follow [how to inspect](../plan-module/references/proofs.md#how-to-inspect),
using the exact build on its real target.

When you use a stand-in, such as a Mac standing in for an iPhone, label the result `proxy`. If a run needs a resource
listed under the profile's `Exclusive resources`, wrap it in `LOOP lock <name> -- <command>`.

If the work needs a contract or the design to change, don't change it yourself. Write a proposal in the plan log and
carry on with whatever doesn't depend on it. If it needs something another module owns that isn't there yet, don't
build it here: end with `BLOCKED` and name it, so the planner can give it to the module that owns it.

To run unattended, or to keep going past this milestone, use `/build`. This skill covers one milestone.

You can research, run anything locally, change this module's code, and integrate verified work as the profile allows,
without asking. Don't force-push. Anything on the profile's "Owner decides" list goes to the owner.
