# thrum · ATMOSPHERE · plan: Unblock ATMOSPHERE M5: H2 fails its Metal precision bound. C

Host: claude. Role: plan. Started: 2026-11-11T06:03:12Z. Session: b2f8f6db-ac1e-461c-93ed-fa8edcb5cb64

## Turn 1: prompt sent

````text
Use the plan-module skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.7.1/skills/orchestration/plan-module/SKILL.md) for this task: Unblock ATMOSPHERE M5: H2 fails its Metal precision bound. Current main retains the design instruction requiring a planner decision on this measured miss. Evidence: docs/evidence/ATMOSPHERE/m5-h2-blocker.md

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit an ACCEPTED.json file or the plans folder's STATUS.md, which the loop writes, and don't commit, merge, pull or land. Each module's files go in its own folder under the plans folder: DESIGN.md, PLAN.md, LOG.md and DONE.json. PLAN.md holds only the present: one `##` heading per milestone, no status lines and no log, and the loop refuses a plan that breaks this, saying why. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change, except for a diagnosis, which ends with its `KEEP` line); the loop lands nothing then. To dry-run a milestone's checks, run `python3 /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.7.1/skills/orchestration/build/scripts/agent_loop.py check --module <M> --milestone <id> --worktree .`. The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report.
````

### Turn 1: last reply

````text
M5 is unblocked on paper: the H2 bound was wrong, not the lookup, so the bound gains one stored half-float step and the lookup stays as it is. The design changed, so it needs a new design review before M5 resumes, and I can't start one.

**What the evidence shows.** On the M3 Max, Metal returns a filtered `RGBA16Float` read rounded to the nearest half-float.
- **Two texels one stored step apart** return only those two values across 257 positions.
- **Two texels far apart** resolve all 257 weights inside the old bound, so the sampler weights are fine.
- **Addressing** agrees with the f64 reference to 0.000007 texels, so it does not explain the miss.
- **Every measured error** is at most half a stored step.

The old design text assumed exact read-back texels meant no storage step.

**What changed.**
- **Bound for H2 and H4:** `C/32 + 1e-5 × M + Q`, where `Q` is one stored half-float step (at most 0.1% of the value). I chose a whole step, not half, because neither WebGPU nor Metal specifies the rounding of a filtered result.
- **Known field:** neighbouring texels must differ by at least 32 stored steps, so `Q` cannot hide a wrong lookup. The builder's current sky field is a ramp of 8–16 steps and needs to become a repeating pattern.
- **Lookup mechanism and cost:** unchanged, one hardware-filtered read. Blending exact texels in the shader and float32 charts are recorded as rejected alternatives.
- **Precision record:** the builder's 257-position measurement stays in the Metal run as a printed record, with no gate of its own.
- **M5.2's reviewer question** now names the new allowance and the 32-step floor. No milestone, check, case or other bound changed.

`./dev check-docs` passes. I did not dry-run M5's checks: the check commands are unchanged and `./dev check` is a full GPU run.

The builder's blocker note and logs exist only in WIP commit `7911c75b` on `build/atmosphere`, not on main. The full reasoning and figures are in entry 3 of `docs/evidence/ATMOSPHERE/log-entries.md`, which cites that commit.

**For the lead.**
- Run the design review: `agent_loop.py review --module ATMOSPHERE --milestone design --worktree .`
- M5 is still recorded as blocked; run `unblock --module ATMOSPHERE --milestone M5` once the design is approved.

**For the owner.** One new assumption in the plan's `Open for the owner`, overturnable in a line:
- Assumption: the lent sky and aerial lookups stay one hardware-filtered read, and their handoff bound allows one stored half-float step. The alternative is float32-precision blending in the shader, which costs more texel reads on every sky pixel and lit fragment and changes every scene's image. Whether a 0.1% step ever shows as sky banding is left to M6's visual review, and a visible step there reopens the choice.

Nothing here touches the `Owner decides` list.

Sources: [Direct3D 10 floating-point rules](https://msdn.microsoft.com/library/windows/desktop/cc308050), [Apple Metal linear filter docs](https://developer.apple.com/documentation/metal/mtlsamplerminmagfilter/linear.md), [gpuweb issue 1034](https://github.com/gpuweb/gpuweb/issues/1034)

PLANNED: docs/plans/ATMOSPHERE/DESIGN.md, docs/plans/ATMOSPHERE/PLAN.md, docs/plans/ATMOSPHERE/DONE.json, docs/plans/ATMOSPHERE/LOG.md, docs/evidence/ATMOSPHERE/log-entries.md
````

