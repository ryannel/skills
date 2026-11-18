# plan: Resolve APPLE-TILE M0's scope conflict: the builder blocked 

Host: claude. Role: plan. Started: 2026-11-11T01:45:10Z. Session: 0d5f1d39-10b8-4803-b32f-0a2d7fe7b1c3

## Turn 1: prompt sent

````text
Use the plan-module skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/plan-module/SKILL.md) for this task: Resolve APPLE-TILE M0's scope conflict: the builder blocked because done-when item D0.2 requires a native witness that the plan assigns to M10 (see the M0 blocked note and docs/evidence/render/apple-tile-m0/README.md at 03bc878a). Make M0's criteria and M10's consistent so M0 can be claimed on what it can prove, without weakening what V1 needs.

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file, and don't commit, merge, pull or land. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then. To dry-run a milestone's checks, run `python3 /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/build/scripts/agent_loop.py check --module <M> --milestone <id> --worktree .`. The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report.
````

### Turn 1: last reply

````text
M0's scope conflict is resolved by correcting one item: D0.2 no longer claims the native copy/select witness, and M10 remains its only owner. M0 can now be claimed on the ordinary comparison proof it already has.

## What changed

- **D0.2 statement:** the clause "the diagnostic native copy/select witness is exact against its own stateful twin" is replaced by a sentence saying the witness is not part of M0 and that M10 first builds and proves it (D10.1/D10.2). D0.2's `ask` and every other M0 item are word for word as before.
- **M10–M12:** unchanged. D10.1 (small same-submit fixture first), D10.2 (exact against the twin through route, reset and replacement), D11.2 and D12.3 already require everything the removed clause said, so nothing V1 needs is dropped.
- **Plan file:** status lines, the M0 section, the carried-state notes and the review handoff now describe the present, with a log entry giving the reasoning.

I did not pull the fixture forward into M0, because that would put native boundary work ahead of the C06 review that D10.1 requires and ahead of M1–M3.

The loop's delta and validation rules accept the change, and `./dev check-docs` passes. I did not dry-run M0's checks: their commands are unchanged and need the GPU.

## What the lead needs to do

- **Unblock M0:** it stays `blocked` until you run `unblock --module APPLE-TILE --milestone M0`; I left that state for the lead, as the done-when rules assign it.
- **Expect M0's proof to be cleared:** changing D0.2 changes M0's definitions, so the loop resets all five item statuses when it authorises this plan. The builder re-records them against the retained record at `03bc878a` and reruns the milestone checks. A recapture is needed only if renderer, shader, capture or cooked inputs changed since then.
- **Design review:** none is owed. `APPLE-TILE.md` is untouched, so its DESIGN OK at `2514d824` still matches. That review already reads D0.1/D0.2 as ordinary controls and D10.1/D10.2 as the native fixture and twin.

## Stale lines I left alone

These still say APPLE-TILE is parked or owed a design review. They are outside this task, and editing the design header would void its approval:

- `ORCHESTRATE.md`, Targets section
- `docs/BUILD-PLAN.md`, line 116
- `docs/design/modules/APPLE-TILE.md`, header

## Owner decisions

None. There are no assumptions and no `replans` counter changes.

PLANNED: docs/design/modules/APPLE-TILE-DONE.json, docs/design/modules/APPLE-TILE-PLAN.md
````

