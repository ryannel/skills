# plan: Some done-when items treat a locked Mac console as a precond

Host: codex. Role: plan. Started: 2026-11-09T18:27:26Z. Session: 01a1c18b-b3b4-74f1-99fc-c389b70f13d5

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
Use the plan-module skill (`orchestrate:plan-module` in Codex; the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.5.1/skills/orchestration/plan-module/SKILL.md) for this task: Some done-when items treat a locked Mac console as a precondition for running a check. COOKED-DRAW M1.7 says the simulator run happens "with the console locked", and scripts/cooked_draw_ios_sim.py refuses to run unless IOConsoleLocked is Yes. That came from the overnight runs, where the point was a capability: the evidence must not depend on desktop screen capture, so it has to work with the console locked and Screen Recording denied. Written as a precondition, it blocks every verification while the owner is using the Mac and adds nothing to the proof; the denied Screen Recording preflight is what shows independence from desktop capture. The owner wants this fixed.

Revise the affected items so the lock state is recorded as a witness, never required, and the no-desktop-capture proof rests on the denied Screen Recording preflight (or whatever the item's real claim needs), so the checks pass whether or not the console is locked. Start with COOKED-DRAW M1.7 and M1.8, which are in a live claim: the loop stopped its verification before review, so their passes will need re-running under the new wording; say so in the plan. Then find any other open or blocked item, in any module, that makes console locking a precondition (T2-CAPTURE M2 and PLATFORM-RUNTIME-MAC are likely) and give it the same treatment. Leave items already accepted as they stand; their lock witnesses are valid history. Name the harness change the builder must make, but leave the code to the builder.

Done when the revised definitions are committed, the docs check passes, and the plan log says what changed and why.

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then.
````

### Turn 2: last reply

````text
Revised seven unaccepted items across COOKED-DRAW, T2-CAPTURE and PLATFORM-RUNTIME-MAC. Console state is witness metadata. Denied Screen Recording preflights establish capture independence.

Plans name the builder’s harness changes and require fresh M1.7/M1.8 passes before review. Accepted history is preserved. `./dev check-docs` and `git diff --check` pass. Files await the loop’s commit and integration. No owner decision is needed.

PLANNED: ORCHESTRATE.md, docs/CAPTURE.md, docs/design/modules/COOKED-DRAW-DONE.json, docs/design/modules/COOKED-DRAW-PLAN.md, docs/design/modules/COOKED-DRAW.md, docs/design/modules/PLATFORM-RUNTIME-MAC-DONE.json, docs/design/modules/PLATFORM-RUNTIME-MAC-PLAN.md, docs/design/modules/T2-CAPTURE-BRIEF.md, docs/design/modules/T2-CAPTURE-DONE.json, docs/design/modules/T2-CAPTURE-PLAN.md, docs/design/modules/T2-CAPTURE.md
````

## Turn 3: prompt sent

````text
The plan isn't complete: docs/design/modules/PLATFORM-RUNTIME-MAC-DONE.json has no design at docs/design/modules/PLATFORM-RUNTIME-MAC.md. Finish it, then end with `PLANNED: <files>`.
````

### Turn 3: last reply

````text
Added `PLATFORM-RUNTIME-MAC.md`, linked it from the plan, and logged the completion. It covers runtime ownership, recovery, console witnesses, capture, cadence and bounded trace qualification.

Documentation and diff checks pass. Independent design review remains owed to the loop. No owner decision is needed.

PLANNED: ORCHESTRATE.md, docs/CAPTURE.md, docs/design/modules/COOKED-DRAW-DONE.json, docs/design/modules/COOKED-DRAW-PLAN.md, docs/design/modules/COOKED-DRAW.md, docs/design/modules/PLATFORM-RUNTIME-MAC.md, docs/design/modules/PLATFORM-RUNTIME-MAC-DONE.json, docs/design/modules/PLATFORM-RUNTIME-MAC-PLAN.md, docs/design/modules/T2-CAPTURE-BRIEF.md, docs/design/modules/T2-CAPTURE-DONE.json, docs/design/modules/T2-CAPTURE-PLAN.md, docs/design/modules/T2-CAPTURE.md
````

