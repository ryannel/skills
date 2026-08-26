# Mixed-Model Recipes — cross-family handoffs and the control stack

Why mix models: each family has its own strength. [`sdxl`](../../sdxl/) has the deepest control/LoRA ecosystem. The DiT models ([`flux-2`](../../flux-2/), [`z-image`](../../z-image/)) render more naturally. [`ideogram-4`](../../ideogram-4/) owns typography. [`krea-2`](../../krea-2/) brings the widest aesthetic range with no house look. [`anima`](../../anima/) owns anime. Cross-model pipelines let each stage run on the model that is best at it. This went from exotic to mainstream during 2025–26, and the named workflows below are the evidence.

## Contents
1. The three handoff rules
2. Named recipes
3. The structural-control stack, per family (mid-2026)
4. Regional prompting status
5. Identity across a mixed pipeline
6. Licences across a mixed pipeline

---

## 1. The three handoff rules

**Rule 1 — decode to pixels between families.** Every model family has its own latent space. (ComfyUI's `LatentFormat` assigns each its own scale/shift; FLUX.2 has an entirely new VAE, and [dev] vs [klein] 4B even use different VAE files.) A latent from family A fed to family B's sampler or VAE produces garbage — sometimes silently weird rather than obviously broken. So every cross-family handoff looks like this:

```
… → VAE Decode (model A) → IMAGE → VAE Encode (model B's VAE) → KSampler (model B) → …
```

In diffusers this is automatic — `pipe_a(...).images` → `pipe_b(image=..., strength=0.3)` hands off pixels by construction.

**Rule 2 — the identity-preserving denoise band is ~0.2–0.5**, with 0.25–0.35 the sweet spot. The refining model's denoise (diffusers `strength`) decides what survives the handoff. Below ~0.2, model B contributes noise-pattern texture and little else. In the band, it re-renders surface — skin, fabric, light falloff — while composition, identity and pose survive. Above ~0.6, it re-composes, and you are using model A as a glorified init image. The full four-tier breakdown is `## The one rule that changes everything` in SKILL.md, and the recipes in §2 below are where those tiers come from `[community — named recipes in §2; convergent]`.

**Rule 3 — match resolution to the refining model's native range** before encoding. Do not hand a 4 MP render raw to SDXL (1024-class). Either downscale, refine, then upscale — or tile the refine pass. DiT refiners tolerate larger inputs but still have sweet spots.

There are also hygiene items to keep: a fixed seed in the refine pass, and color-matching at the end of the whole chain. Mixed pipelines cross two VAEs, so drift is guaranteed — see [`production-ladder.md`](production-ladder.md) §7.

## 2. Named recipes

| Recipe | Direction | Source | Notes |
|---|---|---|---|
| **"ZIT Refiner – SDXL"** (Cordina, Civitai, Jan 2026) | SDXL base (IntoRealism Ultra v8) → **Z-Image-Turbo** refine "to add realism" → detailer subgroups → upscale+sharpen | `[community — Cordina, Civitai]` | the realism-refine pattern; ZIT is fast (8 steps) so the refine pass is nearly free |
| **"Flux Klein IMG2IMG"** (Enzino, Civitai) | SDXL/Pony render → **FLUX.2 [klein]** img2img | `[community — Enzino, Civitai]` | "more natural rendering… better anatomical consistency, reduced SDXL artifacts"; klein 4B is Apache-2.0 → the commercially-clean refine |
| **Flux/DiT → SDXL texture refine** | DiT render → **photoreal SDXL finetune** (RealVis-class) img2img at ~0.3–0.55 | `[community — no single author; convergent]` | borrows the finetune's skin/texture character; also the route to SDXL-only LoRA looks |
| **SDXL as control front-end** | SDXL ControlNet/IP-Adapter/regional stack composes the scene → DiT refine | `[community — "Modern Easy SDXL", Civitai]` | use SDXL's mature control tooling, render quality elsewhere |
| **Krea 2 → Z-Image repair & face pass** (nsfwVariant, Civitai, Jul 2026) | **Krea 2** composes the scene (aesthetic range, anatomy, wide-aspect) → **Z-Image** inpaints its artefact zones (hair strands, fine patterns, halftone areas) and/or re-renders the face at **~0.2 denoise** | `[community — nsfwVariant, Civitai]` | the emerging standard pairing — LoRA authors already ship paired Krea-2 + Z-Image-Turbo versions of the same style; Z-Image supplies the facial expressiveness Krea 2's safety tuning mutes (see [`krea-2`](../../krea-2/)) |
| **Krea 2 gen → Klein 9B edit** (shootthesound, ComfyUI-Angelo, Jul 2026) | **Krea 2** generates → **FLUX.2 [klein] 9B** handles the instruction-edit pass (Krea 2 has no official edit model) | `[community — shootthesound, ComfyUI-Angelo]` | packaged as an app-style node suite; the generate-here/edit-there split that community edit-LoRAs only approximate |
| **Illustrious front-end → Anima refine** | an SDXL-anime checkpoint composes with its ControlNet/regional stack → decode → [`anima`](../../anima/) img2img at **low denoise** → FaceDetailer | `[community — u/Alekite]` | The SDXL-front-end pattern in anime clothing, and the strongest case for it: Anima-LLLite covers scribble/canny/depth but **pose is its weak spot**, so the borrowed control stack earns more here than it does for a DiT. Anima is never the *realism* refiner — that is a stated non-goal |
| **Ideogram typography pass** | text/design plate in **Ideogram 4** (bbox layout, transparent background) → composite/inpaint into another model's imagery; or mask Ideogram's text and restyle the rest elsewhere | `[flagged — no canonical workflow]` | handoffs pixel-space; Ideogram's own Magic Fill covers the hosted half |

## 3. The structural-control stack, per family (mid-2026)

| Family | Best ControlNet | Status | Notes |
|---|---|---|---|
| **SDXL** | `xinsir/controlnet-union-sdxl-1.0` (**ProMax**) | mature; xinsir's further training stalled (GPU funding) — frozen but SOTA | 10+ types + tile/inpaint/outpaint in one checkpoint; plus the full legacy zoo |
| **FLUX.2** | Alibaba PAI `FLUX.2-dev-Fun-Controlnet-Union` | young; custom nodes (VideoX-Fun official or community wrapper) | scale 0.65–0.80; Flux.1 ControlNets are architecturally incompatible |
| **Z-Image** | Alibaba PAI Fun Union 2.1 | official ComfyUI template; **Turbo only** | core nodes (`ModelPatchLoader` + `QwenImageDiffsynthControlnet`) |
| **Ideogram 4** | none | — | `bbox` JSON layout is the only structural lever |
| **Krea 2** | community depth ControlNet (Tanmay Patil, `Krea-2-depth-controlnet`) | days old (Jul 2026), depth only | no pose/canny/union yet; no identity adapters (a community identity-edit LoRA is the nearest); hosted style refs condition *style*, not structure |
| **Anima** | Anima-LLLite (scribble/canny/depth/inpaint) | young; Cosmos-derived, so image conditioning runs through Cosmos-Reference rather than IP-Adapter | **pose is the gap** — which is why an SDXL front-end is the standard anime control route; details in [`anima`](../../anima/) |

Multiple ControlNets chain together with per-CN strength/start/end, though union models mostly remove the need.

**IP-Adapter status:** cubiq's `ComfyUI_IPAdapter_plus` is **maintenance-only since April 2025** (Comfy-Org maintains a reference implementation). For DiT families, style transfer has largely moved to edit models (Kontext/Klein-edit, Qwen-Image-Edit) and Redux-style adapters, rather than classic IP-Adapter. SDXL remains the place where IP-Adapter is a first-class daily tool.

## 4. Regional prompting status

- **SDXL/SD1.5:** the classic Regional-Prompter / attention-couple approaches work, including per-region LoRA application. This is the mature option.
- **Flux-class DiTs:** mask-based **attention masking is in ComfyUI core** (PR #5942) and is the *only* approach that works — the SD-era regional tooling does not transfer. Flux-specific node packs (FluxRegionAttention, RES4LYF regional nodes) build on it. Per-region *LoRA* application on DiTs is still contested craft `[contested]`.
- **Z-Image:** no regional tooling as of mid-2026. Use per-face detailer passes instead, where each detection gets its own prompt/LoRA.

## 5. Identity across a mixed pipeline

A refine pass in a second model is exactly where a carefully-built character drifts. Here is the working order:

1. Keep the refine denoise at ≤ ~0.35 if the face must survive untouched.
2. If you need a stronger refine, let the face drift and **re-assert identity afterward** with a FaceDetailer pass in the model where the character's LoRA/adapter lives (usually the model that generated the base).
3. For multi-character scenes, do the per-face identity passes *after* the last whole-image pass, or the next pass will erode them again.

Per-model identity tooling lives in each model skill's `characters.md` — [`sdxl`](../../sdxl/references/characters.md), [`z-image`](../../z-image/references/characters.md), [`krea-2`](../../krea-2/references/characters.md). **Making** a LoRA is covered in [`character-lora-training`](../../character-lora-training/). This file covers only the cross-model sequencing.

## 6. Licences across a mixed pipeline

Every recipe above is a chain, and a chain inherits every constituent's licence at once. The mistake worth heading off is treating "non-commercial" as one thing. The suite's restricted models restrict **different objects**, and only one of the two kinds stops a recipe from producing a saleable picture.

| Model | What is restricted | Effect on a chain |
|---|---|---|
| [`anima`](../../anima/) | **Deployment.** Non-commercial *weights*; Outputs are carved out of "Derivative" entirely, so anyone — company or individual — may sell the images and commissions. A separate §2(c) carve-out lets an **individual** sell derivative weights, but "solely to the model weights, and not to any larger product". Nobody may run it behind a paid API or ship it inside a paid product | Free to use at any rung when the deliverable is a picture. Blocks the chain entirely when the *pipeline* itself is the product |
| [`ideogram-4`](../../ideogram-4/) | **Weights, not outputs.** Non-commercial and gated weights; the user owns what they generate | The typography pass can feed commercial work, but self-hosting the weights inside a commercial service cannot |
| [`minimax-h3`](../../minimax-h3/) | **Territory.** The licence excludes whole jurisdictions | Rules out the reader, not the recipe — settle it before designing a chain around H3's one-frame edit |
| [`flux-2`](../../flux-2/) [klein] 4B, [`sdxl`](../../sdxl/) with a commercially-licensed finetune | nothing relevant | The usual substitution when a chain must ship |

Two rules follow, and they are the ones to carry:

1. **The deliverable decides which question you are asking.** Selling pictures asks whether *you* may run each model. Selling the pipeline — as an endpoint, a product feature, a hosted workflow — asks whether each model may be *shipped inside a product*. There, a single non-commercial checkpoint stops the whole chain, regardless of where it sits in it.
2. **Substitute early.** Swapping a restricted rung for a clean equivalent is a re-tune of one pass before the recipe is built. Do it after the recipe is built and it becomes a rebuild of every downstream stage, because the denoise bands and the identity work were calibrated against the model you removed.

Per-model terms are in each model skill's `## Licence & limitations`; this file covers only the combination.
