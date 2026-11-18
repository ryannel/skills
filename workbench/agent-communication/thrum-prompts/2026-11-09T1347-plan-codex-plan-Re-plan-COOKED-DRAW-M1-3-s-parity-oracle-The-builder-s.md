# plan: Re-plan COOKED-DRAW M1.3's parity oracle. The builder's bloc

Host: codex. Role: plan. Started: 2026-11-09T13:47:35Z. Session: 01a1c08b-0c38-7823-a2eb-b16d9b9db915

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
Use the plan-module skill (`orchestrate:plan-module` in Codex; the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.4.0/skills/orchestration/plan-module/SKILL.md) for this task: Re-plan COOKED-DRAW M1.3's parity oracle. The builder's blocked checkpoint 9c230ff4 (local in /Users/ryannel/Workspace/thrum/.claude/worktrees/cooked-draw; evidence in docs/evidence/render/cooked-draw/README.md) shows on Apple M3 Max / Metal:
- the direct whole-range draw differs from the meshlet-partitioned indirect draw at 1,506 pixels along terrain triangle edges, max delta 18;
- keeping all meshlets doesn't change that;
- one full-range indirect command per mesh is byte-identical to direct.
So the result depends on draw partitioning, not on culling. The likely cause is pixel-quad derivatives or ordering at draw boundaries, which is unverified.
Decide what M1.3 should require so it still catches a real defect in the direct path without demanding something the hardware doesn't guarantee. Say whether the cause must be identified first, and whether a partition-invariant shader change is worth it.
Keep these constraints: indirect stays selected and unchanged where supported, and the selection rule is unchanged. Don't loosen any other item. Update the design, plan and done-when file.

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then.
````

### Turn 2: last reply

````text
M1.3 now requires exact production-direct parity against a diagnostic full-range indirect reference, plus inspection against selected meshlet indirect. A deliberate missing-mesh control must prove the oracle catches direct-path defects. All views and exact repeats remain required.

Cause identification is not a prerequisite; derivatives/ordering remain hypotheses. A partition-invariant shader change is not justified for M1.

Indirect output, work and selection remain unchanged. All eleven other items are untouched. Documentation checks pass. Fresh design review is owed to the loop; no owner decision is required.

PLANNED: docs/design/modules/COOKED-DRAW.md, docs/design/modules/COOKED-DRAW-PLAN.md, docs/design/modules/COOKED-DRAW-DONE.json
````

