---
name: build-milestone
description: Builds, verifies and integrates the next milestone of a module from its plan and JSON done-when file, in Claude Code or Codex, in a repository with an ORCHESTRATE.md. Use for any implementation, fix or refactor there, including small slices. Not for planning (plan-module) or judging a milestone (review-milestone).
---

# Build a milestone

Run as Codex `gpt-6.1-sol` at medium effort. For a small, bounded piece of work, Claude Opus 5.5 at medium effort
works too. The profile can change either.

Read `ORCHESTRATE.md` first, and any building guidance it links to. Then find the next open milestone in
`<MODULE>-PLAN.md` and its items in `<MODULE>-DONE.json`. Your job is to make that milestone work on its real
targets and get it onto the main branch. For an ordinary fix with no plan, just fix it and add a test.

## Done when

1. Every item for the milestone is `pass`, with evidence. You're allowed to change items' `status` and `evidence`,
   and the milestone's `state`. Set `state` to `in_progress` when you start. Set it to `done` when everything passes,
   but only if no item has `inspect` or `ask`, because those need a reviewer. If an item is wrong, or can't be met,
   don't edit it: say so in your report. [Proofs](../plan-module/references/proofs.md) explains how each kind of item
   is proved.
2. The work is committed and integrated. Rebase onto the profile's branch, run its `Check` fresh, and push without
   force. Under `/build-parallel`, the loop reruns every item's `check` itself before it believes you.
3. The plan's status lines and log are current. Keep what you verified separate from what you think is probably true.
4. If any item has `inspect` or `ask`, the milestone gets reviewed. Check those items yourself first, the same way the
   reviewer will. In a single chat, launch the `orchestrate-evaluator` agent, and tell it only the module, milestone,
   commit and worktree, so it forms its own view. Under `/build-parallel`, the lead launches it for you.
5. Your last line is `DONE`, `BLOCKED: <what you tried, the evidence, what would unblock it>`, or
   `NEEDS_CONTEXT: <what's missing>`.

## How to work

Before changing anything, check the product still runs end to end on its main target. If someone left it broken,
you want to know now, not after you've built on top of it.

Find out how something is done before experimenting. Shipped products and published work have solved most problems,
and current practice usually beats whatever old code happens to be lying around.

If a behaviour still won't come after about three attempts, stop tuning. The mechanism may simply be unable to
produce it. Build a minimal reproduction to find out. If it can't, report `BLOCKED` with what you found.

Look at the output yourself. For each `inspect` item, follow [how to inspect](../plan-module/references/proofs.md#how-to-inspect),
using the exact build on its real target. Passing tests tell you the code does what the tests say. They don't tell
you it looks or feels right.

When you use a stand-in, such as a Mac standing in for an iPhone, label the result `proxy`. If a run needs a resource
listed under the profile's `Exclusive resources`, wrap it in `agent_loop.py lock <name> -- <command>` (the script is
in build-parallel's `scripts/`), so parallel streams don't collide.

If the work needs a contract or the design to change, don't change it yourself. Write a proposal in the plan log and
carry on with whatever doesn't depend on it.

You can research, run anything locally, change this module's code, and integrate verified work without asking. Don't
force-push. Anything on the profile's "Owner decides" list goes to the owner.
