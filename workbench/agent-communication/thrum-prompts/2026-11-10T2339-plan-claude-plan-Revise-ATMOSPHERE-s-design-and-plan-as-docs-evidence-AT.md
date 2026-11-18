# plan: Revise ATMOSPHERE's design and plan as docs/evidence/ATMOSPH

Host: claude. Role: plan. Started: 2026-11-10T23:39:30Z. Session: 9f978b7c-ca8d-473c-bd1d-5994c9c880c6

## Turn 1: prompt sent

````text
Use the plan-module skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/plan-module/SKILL.md) for this task: Revise ATMOSPHERE's design and plan as docs/evidence/ATMOSPHERE/design-review.md asks

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file, and don't commit, merge, pull or land. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then. To dry-run a milestone's checks, run `python3 /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/build/scripts/agent_loop.py check --module <M> --milestone <id> --worktree .`. The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report.
````

### Turn 1: last reply

````text
ATMOSPHERE's design, plan and done-when file are revised for both findings of the second design review. A third design review is still owed before M5 starts; I can't launch it.

**Finding 1 (Must Fix: the texel-range rule accepted a wrong aerial lookup).** The range rule in handoff rows H2 (sky) and H4 (aerial) is replaced by a filtered-decode rule:

- **Expected value:** an f64 evaluation of the lookup's addressing and blend on the read-back texels, written in the test and independent of the lent library's code.
- **Bound:** `C/32 + 1e-5 × M` per channel, where `C` is the spread of the texels the blend reads and `M` the largest of them.
- **Two arms:** the live product at the existing cases, and a known nonconstant field with queries between texel centres on every axis.
- **Negative controls:** deliberately wrong lookups must fail on Metal and in Chrome. For sky these are nearest texel, one row and one column; for aerial, lower slice, upper slice and nearest texel in screen.

M5.2 and M5.3 now name the wrong lookups in their statements and asks. M6.3 and M6.4 repeat the same rows, so their wording is unchanged.

**Finding 2 (Suggestion: pre-exposure wording).** The design now says the lent values are physical and free of pre-exposure, and that a contribution applies the lent exposure scale once as it writes to the scene target. I also added the non-unit exposure control the review suggested: one case of each row H1–H5 is repeated at a scale other than 1.

Beyond what the review asked, I added two risk rows to the design, for a lookup that steps instead of blending and for double or missing pre-exposure.

`./dev check-docs` and `git diff --check` pass. I did not dry-run the milestone checks, because no `check` command changed.

**Owner decisions:** none. Nothing here touches purpose, the V1 exit, spending or publishing, and there are no new `Assumption:` lines.

One thing to know: the `C/32` weight allowance rests on GPU samplers keeping 8-bit filter weights, which is common practice but not measured on the M3 Max or in Chrome. If a correct lookup misses the bound, the plan tells the builder to report the measured weight resolution and return the bound to planning, not widen it.

PLANNED: docs/design/modules/ATMOSPHERE.md, docs/design/modules/ATMOSPHERE-PLAN.md, docs/design/modules/ATMOSPHERE-DONE.json
````

