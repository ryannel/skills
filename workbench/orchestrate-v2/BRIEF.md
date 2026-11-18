# Orchestrate V2: design brief

11 November 2026. The owner asked for a ground-up design of version 2 of the orchestrate set: one that works for a
production-grade distributed web application spread across several repositories, and takes into account everything
learned building version 1.

## What the owner asked for, in their words

> let's think of a ground up solution that could fit multiple repositories and things like backwards compatibility,
> risk reduced deployments in small increments, and all the other considerations when working in a production grade
> distributed web application environment. … This can be V2 of orchestrator, so let's think big and take into
> account all our learnings so far.

"Think big" licenses a redesign: V1's structure (one repository, one main branch, one Check, the
plan/run/review/land commands, `agent_loop.py`) is an input to learn from, not a constraint.

## What V1 is, and where to read it

The published set is `skills/orchestration/` in `/Users/ryannel/Workspace/skills`. Read in this order:

1. `skills/orchestration/README.md`, especially "Why it is built this way": each choice and the evidence under it.
2. `skills/orchestration/GLOSSARY.md`.
3. `skills/orchestration/plan-module/SKILL.md` and its `references/` (`profile.md`, `done-when.md`, `proofs.md`).
4. Skim `build/SKILL.md`, `build-milestone/SKILL.md`, `review-milestone/SKILL.md`, `interview-me/SKILL.md`, and the
   usage text at the top of `build/scripts/agent_loop.py` (~7,200 lines; don't read it all).

## What we have learned (read these; they are the evidence)

- `workbench/orchestration-review/reports/Multi agent delivery harnesses 2026.md`: the research report on
  multi-agent delivery harnesses (measurements and vendor reports).
- `workbench/orchestration-review/ASSESSMENT.md`: V1 assessed against that research and against the live project.
  Its verdict: the core idea (acceptance written before building, in a file the builder can't change; a script
  re-runs every check; a reviewer who uses the product) is the best-supported in the field. Around it, the set is
  heavy and its cost unmeasured, shaped for software with tests, and spends where it needn't.
- `workbench/orchestration-review/deadlock-review-fable.md`: a review of deadlocks in the loop.
- `workbench/orchestration-review/microservices/`: three designs (written today) for a microservice system kept in
  **one** repository. They converged on: a module that owns the running system (how services start together,
  cross-service flows as its milestones, compatibility tests); per-checkout naming of running services; breaking
  interface changes split into expand / migrate callers / contract milestones, the last confirmed by the owner;
  narrowing the pre-merge check to changed services and their callers, with the full check after merge as the net.
  All three warned that none of it had been tried on a real microservice project.
- `~/Workspace/thrum` (read-only): the live project built with V1. Its records show what really happened.

Lessons the owner has stated directly, which bind the design:

- **The owner only chats.** They never type loop commands; every decision reaches them through the lead, in chat.
- **Explicit plain terms over short coined ones.** A longer plain phrase beats a coined term; define each term before
  using it; always say who does each step. V1's "claimed", "the ladder", "parked" confused the owner.
- **Nothing depends on an agent saying it is finished.** A script or a fresh reviewer verifies; only the script
  writes the record of what is Done.
- **Few builders write at once** (2–4); measured results get worse beyond that.
- **Weight must earn its place.** Every part encodes a guess about what the model can't do; a small project must not
  pay for machinery it doesn't need. Add a rule only for a failure that has been seen, or say plainly that it is
  untested.
- **Deploying, spending and anything irreversible are the owner's decision**, unless they grant standing permission.

## The new territory V2 must handle

A production distributed web application: several services, often in several repositories, owned perhaps by
different teams; shared contracts (HTTP/gRPC APIs, events, schemas); databases with live data; separate deploys
that roll gradually; feature flags; canaries and staged rollouts; observability (metrics, logs, traces, SLOs) as the
signal that a change is safe; rollback; secrets and environments (local, preview, staging, production); CI that
already exists and that V2 should use rather than replace; work that spans repositories and must land in order.

"Done" in V1 means merged with checks passing. In production, the honest end state is closer to "running in
production for every user, observed healthy, with the old path removed", and each step toward it is a separate,
reversible, small change.

## What each design must contain

Write for the owner, in plain prose, terms defined before use. Then:

1. **The model**: the few core concepts, what each is for, and what state each owns. What replaces or reshapes V1's
   project / module / milestone / done-when item / Ready for Review / Done.
2. **Who does what**: the agents (and any script or service), what each may and may not do, and how the owner is
   reached.
3. **Several repositories**: where plans and records live, how work spanning repositories is ordered and verified,
   how one view of status is kept.
4. **Backwards compatibility and data**: how breaking changes to APIs, events and schemas are sequenced and verified.
5. **Delivery in small, low-risk increments**: from merge to production, flags, canaries, observation, rollback, and
   where the owner's permission sits. How "done" is defined and who records it.
6. **Verification**: what is checked, where (local, CI, preview, staging, production), by whom, and how the
   guarantee "nothing depends on an agent's word" survives once real environments and CI are involved.
7. **What it costs a small project**: a single-repository app with no deploy pipeline must still be cheap to run.
8. **What V1 parts are kept, changed or dropped**, and why, citing the learnings.
9. **A worked example**: a breaking change to a payments API used by two other services in separate repositories,
   carried from the owner's request to the old path being removed in production.
10. **Risks and unknowns**: what is untested, what you are guessing, what to try first to find out.

Prefer the fewest concepts that cover the ground. Say which alternatives you rejected and why.
