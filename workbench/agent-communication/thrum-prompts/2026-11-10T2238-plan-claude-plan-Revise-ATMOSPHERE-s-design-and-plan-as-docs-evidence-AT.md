# plan: Revise ATMOSPHERE's design and plan as docs/evidence/ATMOSPH

Host: claude. Role: plan. Started: 2026-11-10T22:38:29Z. Session: a24ee8d8-7074-417a-a868-1e30ef7ec635

## Turn 1: prompt sent

````text
Use the plan-module skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/plan-module/SKILL.md) for this task: Revise ATMOSPHERE's design and plan as docs/evidence/ATMOSPHERE/design-review.md asks

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file, and don't commit, merge, pull or land. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then. To dry-run a milestone's checks, run `python3 /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/build/scripts/agent_loop.py check --module <M> --milestone <id> --worktree .`. The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report.
````

### Turn 1: last reply

````text
ATMOSPHERE's design, plan and done-when file are revised to answer all five findings of the design review; nothing is built, and the revised design still needs a fresh design review before M5 starts.

`./dev check-docs` passes. In the dry run, every new or changed check command fails as it should before the work exists, with no broken command. I capped the `./dev check` items at 25 s to keep the shared GPU free, so they timed out rather than completing; that command string is unchanged.

## What changed

- **Finding 1, numerical acceptance (Must Fix).** The design now has a numerical acceptance table in two parts.
  - **Preserved referees P1–P11:** the existing tests, each with its own reference, cases and bound. They must stay unchanged and passing.
  - **Handoff rows H1–H5:** new in M5, one per lent operation, run on Metal and in Chrome against the same references.
  - **Where no bound exists:** for solar sky and solar aerial transport, no independent reference bound exists. The handoff proves only that the lookup returns the stored product in the right units, and the design says so.
  - **Items:** M5.2, M5.3 and M6.3 point at those rows. M6.4 is a new explicit Chrome run.
- **Finding 2, reflection (Must Fix).** Environment reflection is now the fifth lent operation, with its roughness and decoding stated. H5 tests it from an independent contribution across direction, roughness, Sun illuminance, the night term and a rewritten sky.
- **Finding 3, cooked volume.** The volume's march calls one shared cloud-factor function at each lit march sample and keeps today's lighting when there is no provider. M5.6 adds a field that differs between two world points, and M5.4 now covers the volume's shader text. The cost section counts one read per lit march sample.
- **Finding 4, support and limits.**
  - **Lent lookups:** each one's support and its behaviour outside that support are in the design. Aerial transport is from the active camera only, clamped at 32 km.
  - **Cloud field:** the factor is exactly 1 above the plane, outside the region, on an invalid frame, or below the provider's lowest valid Sun elevation.
  - **LUT generation:** defined as a replacement of resources or model, not a recompute of contents.
- **Finding 5, costs.** M6.5 compares the final build against a fresh rerun of the commit M6 starts from. The M1 and M2 records are quoted as history only.
- **From the item notes.** Chrome cost and texture counts are their own item (M5.10). M6.1 now excludes only the moving spur edge of the parked crossing. M6.6 adds solar accuracy to the list of things not qualified.

M6 items were renumbered: the old M6.4 and M6.5 are now M6.5 and M6.6.

## Decisions for the owner

No decision on the `Owner decides` list is required. Two assumptions are logged in the plan, and you can overturn either in a line:

1. **Solar accuracy stays unqualified at the G3s close.** Solar sky radiance and solar aerial transport are not bounded against an all-orders reference, and the maturity ledger will name the gap. Closing it would be a separate accuracy campaign with its own plan and cost.
2. **The Ground E terrain lip and the held 17.4 h stop are judged in M6.1.** Only the moving spur edge of the parked M3 crossing is left out. If the lip turns out to be as stubborn as the parked crossing, M6 stops and reports after two failures on that item.

PLANNED: docs/design/modules/ATMOSPHERE.md, docs/design/modules/ATMOSPHERE-PLAN.md, docs/design/modules/ATMOSPHERE-DONE.json
````

