---
name: plan-project
description: Plans a whole software project at the highest level of the orchestrate process (in a repository with an ORCHESTRATE.md) - its module map, build order, shared contracts and a brief per module - for web apps, native apps, CLI tools, libraries or engines. Use when starting a project or a new goal, splitting work into modules, ordering them, settling a contract change a module proposed, or commissioning a new module. Not for one module's design and milestones (plan-module) or building (build-milestone).
---

# Plan the project

Run as Claude Opus 5.5 at high effort. Read `ORCHESTRATE.md` first; if the repository has none, set it up with `/orchestrate` before anything else. A project with a single module can skip this level.

**Outcome:** the levels below can work without asking. Concretely:
- the purpose-and-goal doc named in the profile states what the project is for and what finishes the current goal,
  and both are the owner's (propose changes; don't make them);
- the architecture brief (at the profile's `Architecture` path) names the modules, what each owns, and how they
  interact, and gives the build order with reasons (riskiest and most depended-on first);
- the contracts file (the profile's `Contracts` path; create it when the first shared invariant appears) lists every
  invariant two or more modules rely on, each with what is guaranteed, its producer, its consumers, and how a
  violation is detected;
- each commissioned module has a brief at `<plans>/<MODULE>-BRIEF.md` that `/plan-module` can start from: what it's for, its consumers, the user-visible
  experiences it must deliver with their operating ranges, constraints, and what's out of scope.

## How to get there

- **Start from users and outcomes,** not from the current folders or a feature list. Who uses this, doing what, on
  which targets, and what must they see or feel? For a reusable library or engine, derive contrasting usage profiles to
  expose shared needs and legitimate differences.
- **Research how shipped products of this kind are structured** and where they fail. Favour current state-of-the-art
  practice over older techniques that merely have code available.
- **Draw boundaries around ownership of state.** Each kind of state has one authority. A module boundary is a
  hypothesis to improve with evidence, not a copy of the directory tree.
- **Account for what is expensive and frequently repeated** before choosing structure, where performance matters to the
  goal ([cost](../plan-module/references/cost.md)).
- **Keep it provisional.** Discuss unresolved choices with the owner in small rounds; don't invent answers to finish.
- Use the project guidance the profile lists for planning.

## Contracts

You own the shared contracts. A change proposed by a module or milestone comes here: reconcile its producers and
consumers, update the contracts file, and tell the affected modules through their plans' logs. Each contract says what
is guaranteed, who produces it, who consumes it, and how a violation is detected.

## Done when

- The brief, build order, contracts and module briefs exist and agree with each other and with the purpose doc.
- An independent reviewer, given only the purpose doc, has derived what the project needs and compared it with your
  map ([review](../review-milestone/references/review.md#the-two-reviews-that-matter-most)), and you've acted on its
  findings. If you're running as a subagent and can't start one, end by saying the review is owed; the lead runs it.
- You end with what changed, the files changed, and any decision the owner must make.

## Boundaries

- **Without asking, you may:** research; delegate research or review to subagents; write throwaway work in the
  profile's scratch location; edit the architecture brief, build order, contracts and module briefs; integrate
  verified planning changes as the profile says.
- **What goes to the owner:** whatever the profile's "Owner decides" line lists. Continue unblocked work meanwhile.
