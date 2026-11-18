# plan: COOKED-DRAW M1 is blocked on M1.10: on the iOS simulator the

Host: codex. Role: plan. Started: 2026-11-09T15:00:23Z. Session: 01a1c0cc-25d1-77b2-b0c1-48751a53ed8a

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
Use the plan-module skill (`orchestrate:plan-module` in Codex; the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.4.0/skills/orchestration/plan-module/SKILL.md) for this task: COOKED-DRAW M1 is blocked on M1.10: on the iOS simulator the cooked valley renders at a fixed 640x360 and is letterboxed in both orientations instead of filling the current oriented surface extent. Evidence: docs/evidence/render/cooked-draw/rotation/layout-failure.json and the README beside it, on the builder's local checkpoint b0dae34c (branch-less, in .claude/worktrees/cooked-draw; read it with git show). The builder judged this G3b iOS/render-owner work, outside COOKED-DRAW.

Decide which module owns matching the scene and internal render size to the oriented surface extent (PLATFORM-RUNTIME-IOS-PLAN.md and PLATFORM-RUNTIME.md mention G3b), and plan that work there as a milestone with checkable done-when items, including a rotation proof on the simulator. Then record COOKED-DRAW M1's dependency on it so the loop sequences them. Don't weaken M1.10. Done when the plan is committed, the docs check passes, and the next ready step for the extent work is clear from `agent_loop.py ready`.

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then.
````

### Turn 2: last reply

````text
Planned G3b `PLATFORM-RUNTIME-IOS:M7` for oriented scene/render sizing, simulator rotation and recovery proof. COOKED-DRAW M1 now depends on it; M1.10 is unchanged.

Docs and loop validation pass. Readiness preview shows design review next, then M7 ready. No owner decision required. Files are left for the loop to commit and integrate.

PLANNED: docs/BUILD-PLAN.md, docs/design/decisions/V1-IOS-SURFACE.md, docs/design/maturity.json, docs/design/modules/COOKED-DRAW-DONE.json, docs/design/modules/COOKED-DRAW-PLAN.md, docs/design/modules/PLATFORM-RUNTIME-IOS-DONE.json, docs/design/modules/PLATFORM-RUNTIME-IOS-PLAN.md, docs/design/modules/PLATFORM-RUNTIME-IOS.md, docs/design/modules/PLATFORM-RUNTIME.md
````

