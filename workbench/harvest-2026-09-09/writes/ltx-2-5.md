# ltx-2-5 — write report, 2026-09-09

Evidence keys: **R** = github.com/Lightricks/LTX-2/releases/tag/v1.3.0 (2026-08-26); **D** = current `packages/ltx-pipelines/docs/pipelines.md` §12 (fetched 2026-09-09); **HF** = huggingface.co/Lightricks/LTX-2.5 and /LTX-2.3 cards (2026-09-09).

## Edits

| File | Section | Change | Evidence |
|---|---|---|---|
| SKILL.md | Variant selector, ecosystem para | Downloads flipped (2.5 1.64M/month vs 1.18M); 08-22 figures kept as history; LoRA count 168 vs 3 kept, dated, marked not resampled. Added singing-avatar / music-video lip-sync carve-out `[community — HF discussion #57; single report]` | HF; huggingface.co/Lightricks/LTX-2.5/discussions/57 (2026-08-19) |
| SKILL.md | VRAM, diffusers and hosting | Replicate has `ltx-2.5-fast`, still no `-pro` | replicate.com/lightricks (2026-09-09) |
| SKILL.md | Per-mode settings › DFR | Rewritten: distilled checkpoint via `--distilled-checkpoint-path`; `--checkpoint-path`, `--distilled-lora`, `--num-generated-keyframes` removed; `--temporal-upscalings {0,1,2}` replaces `--temporal-upsample-rounds`; 64/128-pixel size rule (`3840×2176`); `--spatial-upscalings 2` tiled 4K epilogue; `dfr_mgpu` | R, D |
| SKILL.md | Production rungs 3–4; loud-errors line | Flag renamed at both call sites; detailing strength pinned 0.5; removed-flag error named | R, D |
| SKILL.md | Two-bar hard-facts and craft paras | "eleven days" → "four weeks"; v1.3.0 re-read noted; CLI-broke-once warning | R |
| SKILL.md | Two-bar bullets | VRAM floor: NVFP4 → Jetson Thor, no figure. Metal/ROCm: macOS `uv sync` fix is packaging, plus MLX wave. What-ships-next: Replicate 2.5-fast, DFR `--help` check folded under the existing flag. Ecosystem: download flip vs unresampled LoRA count | R; mlx-community/ltx-2.5-mlx, -q8 (2026-09-01) |
| SKILL.md | Date line; reference-files table | `Facts dated 2026-09-09; community craft refreshed 2026-09-09`, stating what was not re-read; setup row names DFR flags, 4K, MLX | — |
| setup-and-workflows.md | §2 file table | Temporal upscaler tied to `--temporal-upscalings`; distilled LoRA no longer used by DFR | R |
| setup-and-workflows.md | §4 quant lever, multi-GPU cell, new `### Apple Silicon — the MLX route, not Metal PyTorch` | Jetson Thor `110a`; `dfr_mgpu`; packaging fix vs MLX conversions `[community — mlx-community and others; convergent]` | R; HF mlx-community cards |
| setup-and-workflows.md | §5 CLI | v1.3.0 breaking-change paragraph: flags, `--compile max_*_tokens`, `natten` optional for `combined_compile`, `PipelineOutput` | R |
| setup-and-workflows.md | §7 DFR in detail | Four paragraphs: checkpoint rule, size rule, temporal rounds with fps values, 4K epilogue and multi-GPU | D, R |
| setup-and-workflows.md | §8 Replicate row; §9 loud failures | `ltx-2.5-fast` 6.8K runs; two rows for removed flags and dev-transformer / 32-grid rejection | replicate.com; D |

## Findings

Resolved: `dfr-checkpoint-format-changed`; `temporal-upsample-rounds-flag-removed` (replacement confirmed from R and D, not guessed); `hf-downloads-flip-2-5-leads-2-3` (softened, LoRA half kept and dated); `replicate-adds-ltx-2-5-fast`; `macos-install-fix-not-full-metal-support`. Declined: none.

## Techniques

Added: `mlx-quantization-apple-silicon`, `nvfp4-blackwell-jetson-quantization`, `multi-gpu-dfr-runner`, `4k-tiled-spatial-epilogue-dfr`, `gemma4-audio-sync-music-video-regression` (single report, marked; fills the selector gap). Omitted: none.

## Watchlist

- Add `ltx-dfr-checkpoint-and-flag-breaking-changes`. Hook: the existing `[flagged — re-verify]` on the "What ships next locally" bullet now names `--temporal-upscalings` / `--spatial-upscalings`; no new marker, because the skill was already over §6.2.1 limit 3.
- Amend `ltx-2-3-vs-2-5-ecosystem-split` and `ltx-platform-support-and-realtime` per the JSON notes; text now matches. Next check must resample Civitai LoRA counts.
- Amend `ltx-extend-diffusers-and-hosted-surface`: Replicate has `ltx-2.5-fast`, no `-pro`, pricing unread.
- Amend `ltx-vram-floor`: look for a measured Jetson Thor NVFP4 figure.
- Resolved: none.

## Notes

- Watch-class markers 17 + 7 = 24, at the cap; I removed two duplicates of my own.
- SKILL.md 9,095 words, corpus 23,226 — both already over §5 before this pass (8,533 / 21,817) with no §7 deviation. Net +560 here, mostly the DFR rewrite replacing a now-wrong paragraph. A trim is a separate job.
- Readability: all six files under 15 (median 4.2).
- No sibling cites the old flag by name; no cross-skill edit needed.
