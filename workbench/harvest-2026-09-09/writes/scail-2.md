# scail-2 — write report, 2026-09-09

## Edits

Evidence for the Wan Animate edits: docs.dreamerland.ai/video/wan2.2-video/character-animation/wan-animate-vs-scail2 and x.com/SlipperyGem/status/2000761345738948888. Evidence for the Mix Studio edits: github.com/BlackMixture/Mix-Studio/blob/main/docs/installation-and-operations.md.

- `SKILL.md`, intro "The defining trait": "beat Wan Animate into the default slot for character replacement" → "took the default slot from Wan Animate for **whole-body** character replacement".
- `SKILL.md`, suite table: new routing row, close-up facial performance (lip sync, eye and expression nuance) → Wan Animate. Unmarked; the marker lives once, in the comparison table.
- `SKILL.md`, comparison table, Wan Animate row: "Displaced by SCAIL-2…" → task split. Wan Animate wins lip sync, eye movement, expression nuance; SCAIL-2 wins non-human subjects, complex 3D action, multi-character, low-res stability `[community — Brie Wensleydale, same-scene comparison on X; dreamerland.ai task guide, 2026-09-09]`. Blackmixture claim kept, narrowed to whole-body replacement.
- `SKILL.md`, Licence & limitations, Release & stability: "unaudited / unanswered accusation" → documented scope: two PostHog events (`App_Launched`, `Generation_Started`), memory-only, autocapture/session replay/person profiles off, first-run notice, Settings → General toggle, server-side project/IP overrides `[official — Mix-Studio docs, read 2026-09-09]`. Untraced-accusation caveat kept as `[flagged — re-verify]`.
- `SKILL.md`, two-bar craft roll-call: added the Wan Animate task split and **Brie Wensleydale**; "Nine" → "Ten" practitioners.
- `SKILL.md`, two-bar contested bullets: Mix Studio split out of the three-way single-report bullet into its own `[flagged — re-verify]` bullet. Scope is documented; only the accusation's origin is untraced.
- `SKILL.md`, date line: `Facts dated 2026-09-09; community craft refreshed 2026-09-09`. The freshness check re-read README/HF/comfy docs (the /32 vs /16 disagreement is unchanged), which supports re-dating the hard-facts bar.
- `references/setup-and-workflows.md` §3, runners paragraph: same telemetry replacement in short form, linking `../SKILL.md#licence--limitations` for the full scope; caveat kept.

SKILL.md 6,087 → 6,294 words. It was already above the §5 5,500-word band before this pass; pre-existing, flagged for the orchestrator. Readability: all five files under threshold (SKILL.md tangle 0.5, max 8.8).

## Findings resolved
- `mix-studio-telemetry-now-documented` — both locations.
- `wan-animate-tradeoff-more-nuanced-than-displaced` — comparison table, plus the intro sentence and a suite-table row so all three agree.

## Findings declined
None.

## Techniques
None offered (`new_techniques: []`); none added or omitted.

## Watchlist
- `scail2-mix-studio-unaudited` — amend per JSON: check only whether the accusation's source surfaces or is retracted. Suggest renaming to `scail2-mix-studio-accusation-untraced`; `where` is now the Release & stability paragraph, the new two-bar bullet, and setup-and-workflows.md §3.
- `scail2-wan21-lora-transfer` — amend per JSON, folding in the stablediffusiontutorials.com (2026-06-16) remark as a weak data point. Not written into the skill: generic, no mechanism, no test, below the `[community]` bar.
- Add `scail2-wan-animate-task-split` (community-consensus, two sources): the split rests on one same-scene X comparison and one third-party guide. Check whether a second same-scene test confirms it or a Wan Animate/SCAIL-2 update moves the line. `where`: intro, suite table row, comparison table, craft roll-call.

## Other skills
- **`wan-2-2/SKILL.md`** ~L212 and ~L296 still say SCAIL-2 "has displaced" Animate `[community — 2026-08; convergent]`. Soften both to the task split (Animate keeps close-up facial and lip-sync work; SCAIL-2 takes whole-body replacement, non-human subjects, complex action, multi-character), same two URLs.
- `generative-media-atlas` ~L121 ("Tracked person-replacement → only scail-2") is a capability statement, not a preference, and stays correct.
