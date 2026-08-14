# Mixed-Model Recipes — cross-family handoffs and the control stack

Why mix models: each family has a comparative advantage — SDXL has the deepest control/LoRA ecosystem, the DiT models (Flux.2, Z-Image) render more naturally, Ideogram 4 owns typography, Krea 2 brings the widest aesthetic range with no house look. Cross-model pipelines let each stage run on the model that's best at it. This went from exotic to mainstream during 2025–26; the named workflows below are the evidence.

## Contents
1. The three handoff rules
2. Named recipes
3. The structural-control stack, per family (mid-2026)
4. Regional prompting status
5. Identity across a mixed pipeline

---

## 1. The three handoff rules

**Rule 1 — decode to pixels between families.** Every model family has its own latent space (ComfyUI's `LatentFormat` assigns each its own scale/shift; FLUX.2 has an entirely new VAE — and [dev] vs [klein] 4B even use different VAE files). A latent from family A fed to family B's sampler or VAE produces garbage, sometimes silently weird rather than obviously broken. So every cross-family handoff is:

```
… → VAE Decode (model A) → IMAGE → VAE Encode (model B's VAE) → KSampler (model B) → …
```

In diffusers this is automatic — `pipe_a(...).images` → `pipe_b(image=..., strength=0.3)` hands off pixels by construction.

**Rule 2 — the identity-preserving denoise band is ~0.2–0.5.** The refining model's denoise (diffusers `strength`) decides what survives the handoff *(community-convergent across named sources)*:

| Denoise | What model B contributes |
|---|---|
| < ~0.2 | noise-pattern texture only — usually pointless |
| **0.25–0.35** | the sweet spot: re-renders surface (skin, fabric, light falloff) while composition, identity, and pose survive |
| 0.4–0.5 | stronger restyling; faces start to drift — re-assert identity afterward (detailer pass) |
| > ~0.6 | model B re-composes; you're using model A as a glorified init image |

**Rule 3 — match resolution to the refining model's native range** before encoding. Don't hand a 4 MP render raw to SDXL (1024-class): either downscale → refine → upscale, or tile the refine pass. DiT refiners tolerate larger inputs but still have sweet spots.

Plus the hygiene items: fixed seed in the refine pass; color-match at the end of the whole chain (mixed pipelines cross two VAEs, so drift is guaranteed — `production-ladder.md §7`).

## 2. Named recipes

| Recipe | Direction | Source | Notes |
|---|---|---|---|
| **"ZIT Refiner – SDXL"** (Cordina, Civitai, Jan 2026) | SDXL base (IntoRealism Ultra v8) → **Z-Image-Turbo** refine "to add realism" → detailer subgroups → upscale+sharpen | community, named | the realism-refine pattern; ZIT is fast (8 steps) so the refine pass is nearly free |
| **"Flux Klein IMG2IMG"** (Enzino, Civitai) | SDXL/Pony render → **FLUX.2 [klein]** img2img | community, named | "more natural rendering… better anatomical consistency, reduced SDXL artifacts"; klein 4B is Apache-2.0 → the commercially-clean refine |
| **Flux/DiT → SDXL texture refine** | DiT render → **photoreal SDXL finetune** (RealVis-class) img2img at ~0.3–0.55 | community, replicated widely (no single canonical author) | borrows the finetune's skin/texture character; also the route to SDXL-only LoRA looks |
| **SDXL as control front-end** | SDXL ControlNet/IP-Adapter/regional stack composes the scene → DiT refine | community ("Modern Easy SDXL — 2026 Base for Flux & Z-Image", Civitai) | use SDXL's mature control tooling, render quality elsewhere |
| **Krea 2 → Z-Image repair & face pass** (nsfwVariant, Civitai, Jul 2026) | **Krea 2** composes the scene (aesthetic range, anatomy, wide-aspect) → **Z-Image** inpaints its artefact zones (hair strands, fine patterns, halftone areas) and/or re-renders the face at **~0.2 denoise** | community, named | the emerging standard pairing — LoRA authors already ship paired Krea-2 + Z-Image-Turbo versions of the same style; Z-Image supplies the facial expressiveness Krea 2's safety tuning mutes (see the `krea-2` skill) |
| **Krea 2 gen → Klein 9B edit** (shootthesound, ComfyUI-Angelo, Jul 2026) | **Krea 2** generates → **FLUX.2 [klein] 9B** handles the instruction-edit pass (Krea 2 has no official edit model) | community, named | packaged as an app-style node suite; the generate-here/edit-there split that community edit-LoRAs only approximate |
| **Ideogram typography pass** | text/design plate in **Ideogram 4** (bbox layout, transparent background) → composite/inpaint into another model's imagery; or mask Ideogram's text and restyle the rest elsewhere | **inferred craft — no canonical named workflow; flagged** | handoffs pixel-space; Ideogram's own Magic Fill covers the hosted half |

The pattern behind all of them: **compose where control is deepest, render where quality is highest, finish where the finisher is best.**

## 3. The structural-control stack, per family (mid-2026)

| Family | Best ControlNet | Status | Notes |
|---|---|---|---|
| **SDXL** | `xinsir/controlnet-union-sdxl-1.0` (**ProMax**) | mature; xinsir's further training stalled (GPU funding) — frozen but SOTA | 10+ types + tile/inpaint/outpaint in one checkpoint; plus the full legacy zoo |
| **FLUX.2** | Alibaba PAI `FLUX.2-dev-Fun-Controlnet-Union` | young; custom nodes (VideoX-Fun official or community wrapper) | scale 0.65–0.80; Flux.1 ControlNets are architecturally incompatible |
| **Z-Image** | Alibaba PAI Fun Union 2.1 | official ComfyUI template; **Turbo only** | core nodes (`ModelPatchLoader` + `QwenImageDiffsynthControlnet`) |
| **Ideogram 4** | none | — | `bbox` JSON layout is the only structural lever |
| **Krea 2** | community depth ControlNet (Tanmay Patil, `Krea-2-depth-controlnet`) | days old (Jul 2026), depth only | no pose/canny/union yet; no identity adapters (a community identity-edit LoRA is the nearest); hosted style refs condition *style*, not structure |

Multiple ControlNets chain with per-CN strength/start/end; union models mostly remove the need.

**IP-Adapter status:** cubiq's `ComfyUI_IPAdapter_plus` is **maintenance-only since April 2025** (Comfy-Org maintains a reference implementation). For DiT families, style transfer has largely moved to edit models (Kontext/Klein-edit, Qwen-Image-Edit) and Redux-style adapters rather than classic IP-Adapter. SDXL remains where IP-Adapter is a first-class daily tool.

## 4. Regional prompting status

- **SDXL/SD1.5:** the classic Regional-Prompter / attention-couple approaches work, including per-region LoRA application — the mature option.
- **Flux-class DiTs:** mask-based **attention masking is in ComfyUI core** (PR #5942) and is the *only* approach that works — the SD-era regional tooling does not transfer. Flux-specific node packs (FluxRegionAttention, RES4LYF regional nodes) build on it. Per-region *LoRA* application on DiTs is still contested craft.
- **Z-Image:** no regional tooling as of mid-2026 — use per-face detailer passes instead (each detection gets its own prompt/LoRA).

## 5. Identity across a mixed pipeline

A refine pass in a second model is exactly where a carefully-built character drifts. The working order:

1. Keep the refine denoise ≤ ~0.35 if the face must survive untouched.
2. If you need a stronger refine, let the face drift and **re-assert identity afterward** — a FaceDetailer pass in the model where the character's LoRA/adapter lives (usually the model that generated the base).
3. Multi-character scenes: do the per-face identity passes *after* the last whole-image pass, or the next pass will erode them again.

Per-model identity tooling lives in each model skill's `characters.md`; this file only owns the cross-model sequencing.
