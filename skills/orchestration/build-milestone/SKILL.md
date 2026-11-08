---
name: build-milestone
description: Builds, verifies and integrates the next milestone of a module from its plan and JSON done-when file, in Claude Code or Codex, as part of the orchestrate process. Use to implement, fix or refactor code toward a milestone, including ordinary fixes and small slices, in web apps, native apps, CLI tools, libraries or engines. Not for designing or re-planning a module (plan-module), project-wide boundaries (plan-project) or judging a milestone (review-milestone).
---

# Build a milestone

Run as Codex `gpt-6.1-sol` at medium effort, or Claude Opus 5.5 at medium for a bounded slice, unless
`ORCHESTRATE.md` says otherwise. Read `ORCHESTRATE.md` first, and the building guidance it lists.

**Outcome:** the next open milestone in `<plans>/<MODULE>-PLAN.md` works correctly and looks right on its named
targets, every item for it in `<MODULE>-DONE.json` has `status: pass` with evidence, and it's integrated as the profile
says. Without a module plan, for example an ordinary fix, the work serves the current goal and the done-when is the
fix's own test.

## Done when

1. **Every item in the milestone is `pass`, with evidence.** You may change only items' `status` and `evidence`, and
   the milestone's `state`: `in_progress` when you start, `done` when every item passes and `review` is `false`. If an
   item is wrong or can't be met, say so in your report; the rest of the file isn't yours to edit.
   - `oracle` items pass when their command exits 0 on the named target.
   - `inspection` and `review` items: record your own look and the captures as evidence. The evaluator decides the
     final pass for milestones with `"review": true`.
2. **The change is integrated.** With `Integrate: main`: rebase on `origin/main`, run the profile's check fresh on the
   rebased tip, push without force; if the push is rejected, rebase and check again. With `Integrate: pull-request`:
   push a branch, open a PR, and wait for the gating checks the profile names.
3. **The plan's status lines and your progress note are current.** The progress note is the plan's `Now:` and the
   log: decisions with reasons, and claims kept apart as verified, approximate or open.
4. **You end with one report line,** `DONE`, `BLOCKED: <what you probed, the evidence, what would unblock it>` or
   `NEEDS_CONTEXT: <what is missing>`, followed by the evidence. `DONE` needs fresh evidence from this session.

Before claiming items, check each is complete, clear and checkable on its target. If one isn't, report it.

## Staying on course

- **Research before experimenting.** Shipped products and published work have solved most of what a module needs.
  Needing to try things usually means the research or design is missing, so find how it's done first, favouring
  current state-of-the-art and shipped practice. An experiment answers a question, has a stopping point, and goes in
  the log. Delegate hard research to a subagent (the `orchestrate-researcher` agent) where it helps.
- **If a behaviour won't come after about three attempts,** stop tuning it. Find out whether the mechanism can produce
  it at all ([diagnosis](references/diagnosis.md)), and work the milestone's other items meanwhile. If it can't, report
  `BLOCKED` with the evidence. Escalation to a fresh session and then the planner is counted by the loop, not decided
  by you.
- **Contract or design changes** don't happen locally. Write the proposal into the plan's log and your report, and carry
  on with work that doesn't depend on it.

## Build and prove

- **Extend running paths before hardening inactive ones.** Code with no consumer by the end of a slice doesn't land.
- **Make the product able to show the milestone.** If it can't yet host the scenario a milestone needs, adding that
  scenario through public interfaces is part of the work. Label stand-ins for neighbours that don't exist yet.
- **Prefer proven libraries** that meet the targets over building a general subsystem; build your own where a
  specialised path is the point and can show its win.
- **Tests** cover behaviour and plausible failure, including rejected, stale and duplicate input at trust boundaries.
- **Look at the output yourself.** Capture from the exact build on the named target with the profile's capture method,
  covering transitions (empty, loading, error, first use, resize, back-navigation, start and stop) where faults hide.
  Judge against the inspection list and bar. Tests and source review don't replace looking.
- **Claims about devices, speed or visuals** come only from runs on named targets; label stand-ins `proxy`. Wrap runs
  that use an exclusive resource from the profile in `python3 <build-parallel>/scripts/agent_loop.py lock <name> --
  <command>`.
- **Cost:** follow the project's performance guidance, or [cost](../plan-module/references/cost.md). Record
  measurements; investigate tripwires.
- **Evidence** is at most one page per milestone in the profile's evidence location, linked from the done-when items.

## Permissions

- **Without asking, you may:** research; delegate research to subagents; write throwaway reproductions in the profile's
  scratch location; run tests, fixtures and captures; change this module's code; update the plan's status and log;
  integrate verified checkpoints as the profile says.
- **Never:** force-push or rewrite shared history.
- **What goes to the owner:** whatever the profile's "Owner decides" line lists. Continue unblocked work meanwhile.
- **Licences and untouchable paths:** as the profile says.

When work stops, clean build outputs and scratch you created, and remove your worktree once its commit is on the
integration branch.
