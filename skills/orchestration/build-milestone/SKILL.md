---
name: build-milestone
description: Builds, verifies and integrates the next milestone of a module from its plan and JSON done-when file, as part of the orchestrate set, in Claude Code or Codex. Use for implementation, fixes and refactors in a repository with an ORCHESTRATE.md. Not for planning (plan-module) or judging a milestone (review-milestone).
model: claude-opus-5-5
effort: medium
---

# Build a milestone

Run at medium effort, on the model the profile names for your host (in Codex, `gpt-6.1-sol` unless it says
otherwise).

Read `ORCHESTRATE.md` first, and any building guidance it links to. Then find the next open milestone in
`<MODULE>-PLAN.md` and its items in `<MODULE>-DONE.json`. Your job is to make that milestone work on its real
targets and get it integrated. For an ordinary fix with no plan, just fix it, and add a test if one would catch the
fault coming back.

## Done when

1. Every item for the milestone is `pass`, with evidence from its target. [The done-when file](../plan-module/references/done-when.md#who-changes-what-and-when)
   says which fields are yours: items' `status` and `evidence`, and the milestone's `state`. Everything else in that
   file belongs to the planner or the reviewer. If an item is wrong, or can't be met, don't edit it: say so in your
   report, because the loop rejects a claim whose definitions changed. [Proofs](../plan-module/references/proofs.md)
   explains how each kind of item is proved.
2. The work is committed and integrated the way the profile's `Integrate` line says. For `push`, rebase onto the
   profile's branch, run its `Check` fresh, and push without force, all while holding the `integrate` lock so
   parallel builders don't race each other. Under `/build`, the loop reruns the `Check` and every item's
   `check` itself before it believes you.
3. The milestone's `state` says what happens next: `claimed` if it needs review, or `done` if it doesn't. It needs
   review if any item has `inspect` or `ask`, or if it's the module's last milestone.
4. The plan's status lines and log are current. Keep what you verified separate from what you think is probably true.
5. Your last line is `DONE`, `BLOCKED: <what you tried, the evidence, what would unblock it>`, or
   `NEEDS_CONTEXT: <what's missing>`.

## Review and what follows it

Before you claim, check the `inspect` and `ask` items yourself, the same way the reviewer will.

In a single chat, you're also the lead, so start a fresh reviewer. Run `agent_loop.py review` (in the build
skill's `scripts/`) with the module, milestone, commit and worktree, ideally on another host, or launch the
`orchestrate-evaluator` agent where your host has one. Tell it nothing else, so it forms its own view. If you can't
start either, end with `DONE` and say the review is owed. Under `/build`, the lead runs review.

When a review fails, how you carry on depends on how many times this milestone has failed. After one or two, fix the
findings in the same session. After three, hand over to a fresh session with only the files and the review. After
four, the plan is wrong, so stop and send it to `/plan-module`. If it then fails four more times, park it for the
owner. The count is the record of what's already been tried, and repeating an attempt it has ruled out wastes the
next one.

## How to work

If the change touches behaviour, check that the affected part of the product runs before you change it. If someone
left it broken, you want to know now, not after you've built on top of it.

When the right approach isn't settled and it matters, find out how it's done before experimenting. Shipped products
and published work have solved most problems, and current practice usually beats whatever old code happens to be
lying around.

If a behaviour still won't come after about three attempts, stop tuning. The mechanism may simply be unable to
produce it. Build a minimal reproduction to find out. If it can't, report `BLOCKED` with what you found.

Look at the output yourself. For each `inspect` item, follow [how to inspect](../plan-module/references/proofs.md#how-to-inspect),
using the exact build on its real target.

When you use a stand-in, such as a Mac standing in for an iPhone, label the result `proxy`. If a run needs a resource
listed under the profile's `Exclusive resources`, wrap it in `agent_loop.py lock <name> -- <command>`. The script is
in the build skill's `scripts/`.

If the work needs a contract or the design to change, don't change it yourself. Write a proposal in the plan log and
carry on with whatever doesn't depend on it. If it needs something another module owns that isn't there yet, don't
build it here: end with `BLOCKED` and name it, so the planner can give it to the module that owns it.

To run unattended, or to keep going past this milestone, use `/build`. This skill covers one milestone.

You can research, run anything locally, change this module's code, and integrate verified work as the profile allows,
without asking. Don't force-push. Anything on the profile's "Owner decides" list goes to the owner.
