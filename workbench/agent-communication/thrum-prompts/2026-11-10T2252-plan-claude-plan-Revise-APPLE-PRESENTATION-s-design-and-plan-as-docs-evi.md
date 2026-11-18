# plan: Revise APPLE-PRESENTATION's design and plan as docs/evidence

Host: claude. Role: plan. Started: 2026-11-10T22:52:23Z. Session: 6471c1de-f6b6-47aa-a40b-3ec791b6f353

## Turn 1: prompt sent

````text
Use the plan-module skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/plan-module/SKILL.md) for this task: Revise APPLE-PRESENTATION's design and plan as docs/evidence/APPLE-PRESENTATION/design-review.md asks

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file, and don't commit, merge, pull or land. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then. To dry-run a milestone's checks, run `python3 /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/build/scripts/agent_loop.py check --module <M> --milestone <id> --worktree .`. The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report.
````

### Turn 1: last reply

````text
Revised APPLE-PRESENTATION to answer all four findings of the design review; the design still needs a fresh design review, which I can't launch.

Only the docs check (`./dev check-docs`) was run, and it passes. The new Chrome check, `node scripts/check_v1_browser.mjs --case temporal`, exits 1 today ("Unknown case"), as it should before the work exists. I did not run the full `agent_loop.py check` dry-run for M2: it would run `./dev check` and the Chrome suite on the GPU while builders are working on this machine.

## What changed

- **Finding 1 (Must Fix, D2.5):** the design now defines a temporal-input witness, rows W1–W7. One fixture serves both targets, and values are read from frames the game actually submitted, not from a side render or a declaration.
  - W1–W5 cover reactive values: 1 on invalid-history geometry, 0 once valid, the volume's alpha, stars and Sun on a phase edit, and 0 elsewhere.
  - W6–W7 cover history across an unsubmitted view: the next frame's predecessor must be the last submitted frame, in identity and in the motion it writes.
  - D2.5 is now that witness in Chrome, with a reviewer question on what the case reads and whether an inert target or early history advance would fail it.
  - The old `--case all` run moved to a new D2.7, labelled as regression only.
- **Finding 2 (reference and tolerance):** the definition moved into the design and is now exact.
  - The reference is 32 distinct samples; the cycle runs twice only to show the state was held.
  - The held state is listed and checked.
  - The difference is CIEDE2000 on the submitted SDR output over the whole frame.
  - The provisional bound of 3 binds until a plan revision changes it. D3.2 follows.
- **Finding 3 (positive reactive checks on Mac):** D2.2 is now the declaration item, including the star pass's own attachments and graph accesses. A new D2.6 reads rows W1–W5 back from the reactive target on the Mac.
- **Finding 4 (planning boundary):** the design and the plan's status lines say an approval covers M1–M3 and seams 1–4 only. They name what the M4–M11 plan run must settle and have reviewed: the EDR transform, the MetalFX fallback handoff, the generation-build lifecycle and the archive mechanism.
- **From the review's item notes:** D3.5 records TAAU's time at M3's 640×360 extent, kept apart from the 1080p estimate.
- **Unchanged:** all M1 items, D2.1, D2.3, D2.4, D3.1, D3.3, D3.3c, D3.4, and the module list. M2's sizing went from 2.5 to 3.5 days.

## Decisions for the owner

Nothing on the `Owner decides` list is touched: no change to purpose or the V1 exit, no spending, publishing or irreversible action.

Three assumptions are logged in the plan, each overturnable in a line:

1. **Chrome witness scope:** Chrome runs the same rows as the Mac, including the volume and phase-edit rows. The review required only the invalid-history rows and the history identity there. I took the wider set because the fixture is shared and Chrome is where the cloud and sunset demos run.
2. **Colour difference:** ΔE is CIEDE2000 on the submitted 8-bit SDR output, and the bound stays at 3. This replaces the earlier "restated after M3's first run" assumption.
3. **T2 capture record:** the per-frame history identity reaches Chrome through the game page's own report, so T2's capture record is not changed. A builder who needs that change proposes it in the log first.

PLANNED: docs/design/modules/APPLE-PRESENTATION.md, docs/design/modules/APPLE-PRESENTATION-PLAN.md, docs/design/modules/APPLE-PRESENTATION-DONE.json
````

