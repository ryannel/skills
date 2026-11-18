# plan: Re-plan APPLE-TILE (G3t, tile dataflow and Metal boundary) s

Host: codex. Role: plan. Started: 2026-11-09T14:02:50Z. Session: 01a1c091-9568-7ca3-ac13-bdc7f92d3602

## Turn 1: prompt sent

````text
The orchestrate loop started this thread from a script; its task arrives as the next message. Reply with exactly: ready
````

### Turn 1: last reply

````text
ready
````

## Turn 2: prompt sent

````text
Use the plan-module skill (`orchestrate:plan-module` in Codex; the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.4.0/skills/orchestration/plan-module/SKILL.md) for this task: Re-plan APPLE-TILE (G3t, tile dataflow and Metal boundary) so it can pass design review and unpark. It was parked after two failed design reviews; docs/evidence/APPLE-TILE/design-review-2.md lists seven findings, still unresolved.
The lead commissions this scoped re-plan, as BUILD-PLAN.md's G3t entry requires.
- Resolve every finding, or answer it with evidence.
- Cut scope rather than carry anything that isn't needed for G4 and Mac M3.
- Keep the existing design (APPLE-TILE.md, APPLE-TILE-PLAN.md and APPLE-TILE-DONE.json) where it still holds.
- Respect what has landed since. T2-CAPTURE M0 and M1 are done. COOKED-DRAW is being added under G5 and shares thrum-asset-gpu/src/draw.rs.
- Done-when items must name capture modes per T2's rollout rules and mark attended setup explicitly.
- Unpark only through the loop: leave the milestone states for the design review to settle.

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then.
````

### Turn 2: last reply

````text
Re-planned APPLE-TILE around G4 and Mac M3, with dispositions for all seven findings. Deferred fusion and M4–M9 optimizations, retained SDR arithmetic, clarified capture modes and attended window proof, and reconciled dependencies and COOKED-DRAW ownership.

Documentation and planner validation pass. No owner decision is needed. M0 remains parked; independent design review and unpark belong to the loop. No acceptance records changed.

PLANNED: ORCHESTRATE.md, docs/BUILD-PLAN.md, docs/design/CONTRACTS.md, docs/design/decisions/G3T-METAL-BOUNDARY.md, docs/design/maturity.json, docs/design/modules/APPLE-PRESENTATION-PLAN.md, docs/design/modules/APPLE-PRESENTATION.md, docs/design/modules/APPLE-TILE-BRIEF.md, docs/design/modules/APPLE-TILE-DONE.json, docs/design/modules/APPLE-TILE-PLAN.md, docs/design/modules/APPLE-TILE.md, docs/design/modules/PLATFORM-RUNTIME-MAC-PLAN.md, docs/design/modules/PLATFORM-RUNTIME.md, docs/design/modules/RENDERING.md
````

