# z-image — 2026-09-09 write report

## Edits (file · section · change · evidence)

- `SKILL.md` · quantisation list · Nunchaku SVDQuant bullet: Turbo-only INT4/NVFP4, ranks 32/128/256, `ComfyUI-nunchaku` loader, v1.1.0/v1.2.0 dates `[community — nunchaku-ai; strong]` · hf.co/nunchaku-ai/nunchaku-z-image-turbo; github.com/nunchaku-ai/ComfyUI-nunchaku
- `SKILL.md` · Turbo › LoRAs · "update ComfyUI first / PR #12717" demoted to a one-line pointer at the §6 footnote · github.com/comfyanonymous/ComfyUI/pull/12717 (merged 2026-03-17)
- `SKILL.md` · Licence · "unreleased as of mid-2026" → "as of 2026-09-09 (issues #163, #169)"
- `SKILL.md` · two-bar · "no DiT block map" bullet replaced by `[flagged — early tooling; re-verify]` covering regional tools and per-layer loaders, plus a bullet listing the three reference-level flags; `Facts dated 2026-09-09`; reference-files table blurbs updated ("no regional tooling exists" removed)
- `references/characters.md` · §5 · "no regional tooling" → "new and experimental"; new paragraph on **zit-regions** `[community — MisterLotto; single report, early]` and **ZIT-Ideogram** `[community — bbc-s; single report, early]`, reported caveats, FaceDetailer kept as the reliable path, closing `[flagged — early tooling; re-verify]` · github.com/MisterLotto/zit-regions; github.com/bbc-s/ZIT-Ideogram
- `references/characters.md` · §6 style-cast row · dataset-time prevention stays the lever; per-layer loaders added as inference-time option with a "knob but not the map" caveat; `[flagged — per-layer loaders early; re-verify]` replaces `[flagged — no DiT block map yet]` · github.com/capitan01R/Comfyui-ZiT-Lora-loader; github.com/shootthesound/comfyUI-Realtime-Lora
- `references/characters.md` · §6 "barely does anything" row, Sources & confidence · version-floor framing; tooling volatility note, checked 2026-09-09
- `references/setup-and-workflows.md` · §6 · Nunchaku wiring paragraph (own loader + LoRA nodes); "The gotcha…" retitled "The QKV version floor (…now a footnote)" with merge date and pinned-install caveat `[official — ComfyUI PR #12717, merged 2026-03-17]`; new subsection "Per-layer (block-weighted) loading — new and experimental" on both loaders with `[flagged — no validated DiT block map; re-verify]`; cross-compat gains the `zimage_turbo_training_adapter` v2 route `[official — Ostris adapter repo; lilting.ch 2026-05-04]` · lilting.ch/en/articles/z-image-turbo-lora-dedistill-adapter
- `references/lora-training.md` · §1, §3.1 · "train on Turbo … through the adapter"; "What the adapter does" paragraph (de-distills during training only; Base still the default) · lilting.ch 2026-05-04
- `references/lora-training.md` · §3.2, §8 · one-paragraph layer-targeting note `[flagged — Civitai 24403; single report, re-verify]` · civitai.com/articles/24403; "barely does anything" row reframed as version floor

## Findings

Resolved: `regional-tooling-now-exists`, `block-weighted-lora-loaders-exist`, `lora-pr-12717-aged-out`, `nunchaku-quantization-uncovered`, `base-turbo-transfer-adapter-nuance`. Declined: none.

Note: the adapter itself (v1/v2 files) was already in `lora-training.md §3.1`; only the mechanism and the cross-reference from the transfer section were missing.

## Techniques

Added: `nunchaku-svdquant-zit`, `zit-regions-attention-bias`, `zit-ideogram-box-regional`, `block-weighted-zit-lora-loader`, `realtime-lora-block-editor`, `zimage-turbo-training-adapter-v2`, `character-lora-layer-targeting` (one flagged sentence; fills a real gap, makes the watchlist entry greppable). Omitted: none.

## Watchlist

- Resolved: none. Amend per the JSON: `regional-tooling`, `dit-block-map`, `lora-pr-12717` (now a footnote; downgrade to a version-floor check), `base-turbo-transfer`, `zit-bucket-and-noise`.
- Add: `nunchaku-quantization` (`[community — nunchaku-ai; strong]`, SKILL.md + setup §6); `character-lora-layer-targeting` (`[flagged — Civitai 24403; single report, re-verify]`, lora-training §3.2).
- New markers for the state file: `[flagged — early tooling; re-verify]` ×2, `[flagged — per-layer loaders early; re-verify]`, `[flagged — no validated DiT block map; re-verify]`. `[flagged — no DiT block map yet]` is gone.

## Other skills needing a matching edit

`image-production-workflows`: `references/mixed-model-recipes.md` L63 ("Z-Image: no regional tooling exists as of mid-2026") and `SKILL.md` L177 failure row. Both should say two experimental Z-Image regional tools exist (zit-regions for Forge, ZIT-Ideogram for ComfyUI), single-report and early, with per-face detailer passes still the reliable path. `SKILL.md` L233/235 can stand.

## Shape notes

Readability: all files under threshold (median 7.0). Watch-class markers: 19 (≤24); none malformed. Corpus 17,734 → 18,925 and `setup-and-workflows.md` 4,324 → 4,753; both were already over their §5 bands before this pass, and I did not cut repairs to compensate. SKILL.md 5,171 is in band.
