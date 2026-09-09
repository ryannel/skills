# image-production-workflows — write report, 2026-09-09

## Edits (file · section · change · evidence)

1. `SKILL.md` · *A video model is now a legitimate stage* · New paragraph after "exactly one frame": stock `comfy_extras/nodes_minimax_h3.py` still clamps to 5 frames, `#15644` open with no linked PR as of 2026-09-09, so the GUI route yields a gridded still with no error. Workaround: patch the node minimum locally (re-apply per update) or run the edit outside the stock node via API/script. `[official — Comfy-Org/ComfyUI#15644]` + `[flagged — re-verify]`, linked to minimax-h3. · https://github.com/Comfy-Org/ComfyUI/issues/15644 (corroborated by minimax-h3's `frame-min-fix-not-landed`, 2026-08-29)
2. `SKILL.md` · *Failure modes* · New row: gridded one-frame H3 edit / node refuses `length=1`. · same
3. `SKILL.md` · *Failure modes* Z-Image row; *Tool status* regional row · Z-Image's new regional nodes noted as experimental, pointing at mixed-model-recipes.md §4. · z-image.json `regional-tooling-now-exists`
4. `SKILL.md` · *Tool status* · New Topaz partner-node row; ladder stage-5 cell names it as the commercial alternative. · https://comfy.org/workflows/1c0a3a9faad3-1c0a3a9faad3/ (2026-08-09)
5. `SKILL.md` · *Suite map* H3 row · "with the stock-node caveat above". · as (1)
6. `SKILL.md` · *Two bars* · New flagged bullet for the H3 node limit; date line `Facts dated 2026-06-12; community craft refreshed 2026-09-09` plus "H3 node status and finisher table re-verified 2026-09-09"; fast-moving list extended.
7. `references/production-ladder.md` · §4 · `moonwhaler/comfyui-seedvr2-tilingupscaler` runs SeedVR2 tile-by-tile, folding stages 4+5; VRAM bounded by tile (README: 1024 tiles, 32–64 px padding) `[community — moonwhaler repo; re-verify]`. · https://github.com/moonwhaler/comfyui-seedvr2-tilingupscaler, fetched 2026-09-09 to confirm existence. The README does **not** claim "constant VRAM regardless of output size"; I wrote the weaker, supported claim.
8. `references/production-ladder.md` · §5 · Topaz row `[official — comfy.org workflow gallery]`; header "Status (as of 2026-09-09)"; chain paragraph notes the tiling node. · as (4), (7)
9. `references/mixed-model-recipes.md` · §4 · Z-Image line rewritten: `MisterLotto/zit-regions` (Forge) and `bbc-s/ZIT-Ideogram` (ComfyUI) exist; seed-sensitive, boundary blur, inconsistent per-region LoRA, lightly tested past 3 regions `[community — MisterLotto, bbc-s repos; early]`; FaceDetailer stays the reliable route. · https://github.com/MisterLotto/zit-regions ; https://github.com/bbc-s/ZIT-Ideogram
10. `references/mixed-model-recipes.md` · §2 · Paragraph after the recipe table: edit rung wider than Klein — Qwen-Image-Edit 2511 or hosted Nano Banana Pro `[community — runflow.io write-up; single report]`; H3 at one frame competes for the rung. · https://www.runflow.io/blog/comfyui-qwen-image-edit (2026-08-01)

## Findings
- **Resolved:** `h3-single-frame-comfy-node-limit` (1, 2, 5, 6); `ipw-seedvr2-tiling-node` (7 — existence confirmed, maintenance/8K VRAM not verified, hence `re-verify`); `ipw-upscaler-landscape-holds` (severity none, no edit — close it); cross-skill `regional-tooling-now-exists` (3, 9).
- **Declined:** none.

## Techniques
- **Added:** `topaz-comfyui-partner-nodes` (official); `qwen-nano-banana-edit-routing` (single-report, per the user's note, marked low-confidence; fills the edit-model gap the finding named).
- **Omitted:** none.

## Watchlist
- **Amend `z-image-regional`:** no longer "no tooling"; track zit-regions / ZIT-Ideogram maturity. Still linked to z-image.
- **Add `h3-single-frame-comfy-node-limit`** as the harvest proposes; fix with minimax-h3.
- **Add `edit-rung-routing`** (community): promote from single-report when a named workflow appears.
- **Amend `upscaler-landscape`:** add Topaz partner nodes and the moonwhaler tiling node.
- Move `ipw-upscaler-landscape-holds` and `ipw-seedvr2-tiling-node` to `resolved`.

## Other skills
- **minimax-h3**: `SKILL.md` L278 and `references/setup-and-workflows.md` L252 still say #15644 is "lifted in recent nightlies"; its own `frame-min-fix-not-landed` covers it. This skill now says minimax-h3 "carries the same caveat", which assumes that fix lands in the same pass.
- **z-image**: `references/characters.md` ~L68 needs the matching regional rewrite.

## Shape
SKILL.md 3,759 words (was 3,442) against the 2,000–3,200 cross-cutting band — already over before this pass; §7 lists no deviation. Corpus 8,701, in band. Tangle 4.0–6.4 per file. 49 markers, ~5.6/1k, layer ratio ≈1.0.
