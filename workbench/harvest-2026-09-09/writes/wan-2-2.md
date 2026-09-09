# wan-2-2 — write report, 2026-09-09

Pinned template numbers, lightx2v versions and per-mode settings untouched (re-verified unchanged). Corpus 14,624 words; readability 0/6 files over threshold; no nested markers; watchlist-class markers 15 (~1.0/1k).

Evidence keys: **[A]** blog.comfy.org/p/wan-animate-2-is-now-available-in + workflow_templates/video_wan_animate2.json + HF Wan-AI/Wan2.2-Animate-2-14B-Diffusers (2026-08-08). **[B]** github.com/Comfy-Org/workflow_templates tree (api_wan2_6/2_7/3_0_*.json; video_wan_vace_14B_t2v.json) + HF Wan-AI org + Wan-Video/Wan2.2, checked 2026-09-09. **[C]** HF alibaba-pai/Wan2.2-VACE-Fun-A14B.

## Edits

| File | Section | Change | Ev. |
|---|---|---|---|
| `references/motion-and-camera.md` | Which-tool table | Animate row names Animate 2 first | A |
| same | VACE | Dropped `[community — re-verify current file naming]`; repo/base/last-update stated; **Comfy-Org ships no native Wan 2.2 VACE template** (2.1 only, CausVid 2–4 steps/CFG 1.0 vs base 20/6.0); 2.2 model runs from PAI's bundled workflow | B, C |
| same | Animate | Split into `### Animate 2` (new) and `### Animate (original)`. Animate 2: `video_wan_animate2.json`; no pose extraction, driving video is motion only; background+camera prompt-set; `WanAnimate2Cache` ~halves time for system RAM; 81 frames (~3.4 s @ 24 fps) per pass; Motion Transfer subgraph duplication via `continue_motion`/`video_frame_offset`, batch, trim 1-frame overlap; ComfyUI PR #13180 `[pending release]`; variants base / `-Distilled` / Lite. fp8 filenames deliberately not pinned. Original gains a pose-extraction note | A |
| same | Animate → SCAIL-2 para | Displacement verdict predates Animate 2 `[flagged — re-verify]` | inference |
| same | Not controllable | Clip-length bullet: Animate 2 chains by subgraph, still stitching | A |
| `SKILL.md` | Intro para 3 | 2.5/2.6/2.7 **and 3.0** hosted-API only; sourcing upgraded to Comfy-Org API-node-only templates + empty HF org past 2.2 | B |
| `SKILL.md` | Task-mode selector | Animate row: `Wan2.2-Animate-2-14B` (+`-Distilled`, Lite); original still works | A |
| `SKILL.md` | Control-stack table | Animate 2 (and original) | A |
| `SKILL.md` | Suite table, replacement row | SCAIL-2 verdict predates Animate 2 `[flagged — re-verify]` | inference |
| `SKILL.md` | Release timeline | 3.0 added to API-only list; Comfy-Org corroboration; Animate 2 as newest downloadable 2.2 checkpoint | A, B |
| `SKILL.md` | Two-bar roll-call | `WanAnimate2Cache` added to node names | A |
| `SKILL.md` | Two-bar contested pt 3 | "all hosted-API only as of 2026-09-09", marker kept | B |
| `SKILL.md` | Two-bar date line | `Facts dated 2026-09-09`; craft date left 2026-08-22 | freshness JSON |
| `SKILL.md` | Reference files table | motion-and-camera row updated | — |
| `references/characters.md` | §3 Animate | One sentence pointing to Animate 2 | A |

`description` unchanged (capability unchanged; "Animate" covers Animate 2).

## Findings

Resolved: `vace-wan22-no-native-comfy-template`, `comfy-official-source-for-api-only-successors`; from `freshness.json`: `wan22-animate-2` (repaired in full), `wan-3-0-checked-absent` (no text change required, but note Wan 3.0 now *exists* as a hosted-API model per `api_wan3_0_*`; still no weights).

Declined: none.

## Techniques

Added: `wan-animate-2-no-pose-extraction`, `wan-animate-2-caching-node`, `wan-animate-2-subgraph-chaining`, `wan-animate-2-lite-and-distilled-variants`. Omitted: none.

## Watchlist recommendations

- `vace-for-wan22-naming` → settle as fact, annual re-check: "no native Comfy-Org 2.2 VACE template; PAI bundled workflow".
- `wan-2-5-plus-api-only` → amend sourcing to Comfy-Org template repo + HF org; extend to 3.0.
- `wan-3-0-open-weights` → amend: 3.0 live as API; weights absent; MAJOR-on-release check stands.
- ADD `animate-2-template-filenames` (version-pin): fp8 filenames in `video_wan_animate2.json` not yet pinned.
- ADD `animate-2-native-looping` (pending-release): ComfyUI PR #13180 replaces subgraph duplication when merged.
- ADD `scail2-vs-animate-2` (flagged-inference): displacement verdict predates Animate 2.
- `comfy-template-numbers`, `musubi-569-one-lora`, `lightx2v-slow-motion-fixes` → checked 2026-09-09, no change.

## Other skills

- `scail-2`: its "displaced Wan Animate" claim needs the same Animate 2 caveat.
- `generative-media-atlas`: Animate mentions should say Animate 2.
