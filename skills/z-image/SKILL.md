---
name: z-image
description: >
  Authoritative guide for the Z-Image model family (Z-Image and Z-Image-Turbo, Alibaba Tongyi Lab) in ComfyUI or the diffusers API. Use this whenever the user touches Z-Image in any way, even obliquely: choosing between Z-Image and Turbo (or weighing Z-Image against other models), installing or setting it up in ComfyUI (file layout, loaders, quantisation, ControlNet), writing or fixing prompts (the Qwen-3 LLM encoder needs sentences not tags; realism, killing plastic/waxy stock-photo skin, bilingual text rendering, high/low-angle gaze control), pose control and structural conditioning (Fun Union ControlNet — Pose, Depth, Canny, HED, Scribble; ModelPatchLoader + QwenImageDiffsynthControlnet nodes; Turbo-only; V2.1 model files), face identity (no PuLID for Z-Image — character LoRA via FaceDetailer is the standard approach), building single- or multi-stage workflows (hires refine, tiled upscale, face detailer, img2img/inpaint) with practical sampler/CFG/denoise/resolution/step settings, or generating a dataset and training a LoRA with the Ostris AI-Toolkit.
---

# Z-Image Family

Z-Image is Alibaba Tongyi Lab's open-weights image generation family — a **6B-parameter Scalable Single-Stream DiT (S3-DiT)** where text, visual semantic tokens, and image VAE tokens travel through one unified sequence. The text encoder is **Qwen 3 4B**, an LLM-grade encoder that parses your prompt as natural language. Bilingual (English + Chinese). Apache-2.0 across the family.

## Variant selector

| Variant | Distilled | Steps | CFG | Negatives | VRAM | Licence | Use when… |
|---|---|---|---|---|---|---|---|
| **Z-Image** | No | 25–50 | 3.0–5.0 | Yes | not published | Apache-2.0 | final renders, LoRA training base, fine-grained negative control |
| **Z-Image-Turbo** | Yes (Decoupled-DMD) | 8 effective ¹ | 1.0 ² | No ² | ≤16 GB | Apache-2.0 | rapid iteration, dataset generation, drafting |
| **Z-Image-Edit** | — | — | — | — | — | Apache-2.0 | instruction-based image editing — *announced, not yet released* |
| **Z-Image-Omni-Base** | — | — | — | — | — | Apache-2.0 | generation + editing in one model — *announced, not yet released* |

> ¹ **ComfyUI KSampler: 8 steps** (sampler `res_multistep`, scheduler `simple` per the official template). **diffusers:** `num_inference_steps=9` → "this actually results in 8 DiT forwards" (official model card).
> ² **CFG 1.0 in a ComfyUI KSampler *is* guidance-off** — it equals `guidance_scale=0` in diffusers, and it's the value in the official template. Never type CFG 0.0 into a KSampler (it outputs the unconditional and ignores the prompt). Negatives are inert here; zero them with `ConditioningZeroOut`. Raising CFG to 1.2–1.5 re-introduces weak negative subtraction at ~2× cost and over-saturation — use only for stubborn artefacts.

**Default workflow:** Draft in Turbo (8 steps, CFG 1.0) to find composition and seed. Re-render keepers in Z-Image (40 steps, CFG 4.0) for the final asset. Same prompt and seed — Z-Image will reinterpret slightly; that's expected. For layered production pipelines, see **Building multi-stage workflows** below.

---

## Setup & ecosystem

Z-Image runs in **ComfyUI core** with no custom nodes since **v0.3.75** (Nov 2025). The DiT is **not a checkpoint** — load it with three separate nodes: **Load Diffusion Model** + **CLIPLoader** (the Qwen-3 encoder) + **Load VAE**.

**File layout** — download the ComfyUI-repackaged files from the `Comfy-Org/z_image` and `Comfy-Org/z_image_turbo` Hugging Face repos:

| File | ComfyUI folder | Loader node |
|---|---|---|
| `z_image_bf16.safetensors` / `z_image_turbo_bf16.safetensors` (DiT) | `models/diffusion_models/` | Load Diffusion Model |
| `qwen_3_4b.safetensors` (text encoder, **shared**) | `models/text_encoders/` | CLIPLoader |
| `ae.safetensors` (VAE, **shared** — the Flux.1 VAE) | `models/vae/` | Load VAE |

The text encoder and VAE are common to every variant — download once. Official ComfyUI templates ship for all three entry points: **`image_z_image`** (base), **`image_z_image_turbo`** (Turbo), and **`image_z_image_turbo_fun_union_controlnet`** (Turbo + an official Fun union ControlNet for structural conditioning). See also comfyanonymous's `ComfyUI_examples/z_image` page.

**Stock node settings** (from the official template): set the **CLIPLoader type to `lumina2`**, use **`EmptySD3LatentImage`** for the latent (not the legacy `EmptyLatentImage`), and put a **`ModelSamplingAuraFlow` node (shift 3)** on the model path before the sampler.

**Low-VRAM / quantisation:**
- **Official** (in the Comfy-Org repos): NVFP4 DiT `z_image_turbo_nvfp4.safetensors` (~4.5 GB, **Turbo only**); quantised encoders `qwen_3_4b_fp8_mixed` (~5.6 GB) and `qwen_3_4b_fp4_mixed` (~3.5 GB).
- **Community** (requants, not official): fp8 DiT (e.g. Kijai's `fp8_scaled_e4m3fn`) and GGUF Q2–Q8 (e.g. unsloth). GGUF requires the `ComfyUI-GGUF` custom node (city96). There is no official fp8 DiT.
- Quantised builds are widely reported to run on 6–8 GB cards, but no official sub-16 GB threshold is published.

**diffusers API:** `from diffusers import ZImagePipeline`. Shipped in **stable diffusers ≥ 0.36** (`pip install -U diffusers`) — the model card's `pip install git+…` line is launch-day legacy from before 0.36. Latent-space `ZImageImg2ImgPipeline` and `ZImageInpaintPipeline` also exist; these run on the released base/Turbo weights and are **not** the (still-unreleased) instruction-based Z-Image-Edit.

**ControlNet (pose, depth, canny, and more).** The official Fun Union ControlNet for Z-Image **Turbo** is from Alibaba PAI. A single Union model file handles all conditioning types. File: `Z-Image-Turbo-Fun-Controlnet-Union-2.1-8steps.safetensors` (6.71 GB) or the lite variant (2.02 GB) → `models/model_patches/`. ComfyUI nodes are both built-in core: `ModelPatchLoader` (loads the patch) + `QwenImageDiffsynthControlnet` (applies it). Pose uses `DWPreprocessor` (DWPose). **Turbo only** — base Z-Image ControlNet has no ComfyUI support yet. Full file table, all V2.1 variants, node wiring, and per-type preprocessors: **`references/workflows.md §9`**.

**Face identity.** No PuLID or IP-Adapter face model exists for Z-Image. The standard approach is a **character LoRA loaded at the FaceDetailer stage** (references/workflows.md §6). Full comparison of available methods: **`references/workflows.md §10`**.

---

## The one rule that changes everything

Qwen 3 4B is an LLM-grade encoder — it parses syntax and clause structure. Write a **sentence**, not a tag list.

| Don't | Do |
|---|---|
| `1girl, solo, masterpiece, 8k, best quality` | *A young woman standing alone in a sunlit kitchen, candid documentary photograph.* |

Contradictions don't average out — they create uncanny artefacts. Pick one medium, one mood, one lens.

**Prompt anatomy** — six parts in this order (details in `references/prompting-guide.md` §1):

1. **Subject** — who/what, concrete details; at least one non-idealised trait if a person
2. **Scene** — where and when (Z-Image has strong geographic priors — name locations specifically)
3. **Composition** — shot type, framing, lens (focal length + aperture: "85 mm f/1.4")
4. **Lighting** — source + direction + quality + colour temperature — always all four
5. **Style / medium** — exactly one
6. **Constraints** — negatives in Z-Image; positive phrasing inside the prompt in Turbo

**Length sweet spot:** 80–250 words. Put subject, key text-to-render, and primary lens in the first 75 tokens. Soft cap is 512 tokens (~384 words); set `max_sequence_length=1024` locally if you genuinely need more.

---

## Variant-specific settings

### Z-Image (undistilled)

Preserves the full training signal — best texture diversity, best base for LoRA training.

- **Steps:** 25–50 — the official ComfyUI base template uses **25**; the diffusers card recommends 28–50 (example: 50). 40 is a safe all-rounder
- **CFG / guidance:** 3.0–5.0 (4.0 typical — the value in the official base template and diffusers example)
- **Sampler:** the official ComfyUI base template uses **`res_multistep` / `simple`** with `ModelSamplingAuraFlow` shift 3 — same chain as Turbo. Community finetune pipelines often substitute `euler` / `simple` (see `references/workflows.md`)
- **Resolution:** 1024×1024 natively (officially 512–2048 px); 1:1, 4:3, 3:4 all work well
- **Negative prompts:** Use them. Baseline: `text, watermark, extra fingers, deformed hands, plastic skin, waxy skin, airbrushed, blurry, oversaturated` — keep under ~180 characters to avoid side effects
- **Seed diversity:** High; randomise freely

### Z-Image-Turbo (distilled)

Decoupled-DMD distillation removes CFG dependency. Fastest path from prompt to draft.

- **Steps:** ComfyUI KSampler **8 steps**; diffusers `num_inference_steps=9` (8 DiT forwards)
- **Sampler (official ComfyUI):** `res_multistep` / `simple`
- **CFG / guidance:** diffusers `guidance_scale=0`; **ComfyUI KSampler CFG 1.0** (cfg 1 = guidance-off — never 0.0 in a KSampler)
- **Resolution:** 1024×1024
- **Negative prompts:** Do not use — phrase all constraints positively inside the prompt
- **Seed diversity:** Lower than Z-Image; Turbo converges toward the strongest mode
- **LoRA weight:** ~0.8 (official inference example: `adapter_weights=[0.8]`); 1.0 overcooks saturation and edges
- **LoRA training:** Requires the Ostris training adapter — see `references/lora-training.md`

---

## Building multi-stage workflows

For production results, don't render once — **layer passes: ZIB builds structure, ZIT refines and upscales.** Generate at a *low* base resolution, then climb. ZIB and ZIT are combined here, not either/or.

**The pipeline** (every optional stage is bypassable — preview cheaply, pay for heavy passes only once the base is right):

1. **1st-gen (ZIB)** — composition + pose at low base res (e.g. 640×960). Judge *layout only*; reroll the seed freely.
2. **Latent upscale** — `LatentUpscaleBy`, `bislerp`, ×1.7.
3. **2nd-gen (ZIT)** — hires refine for fingers, face, text. Judge *fine details* here.
4. **Tiled SD upscale (ZIT)** — `UltimateSDUpscale` ×2, low denoise (~0.23).
5. **FaceDetailer (ZIT)** — re-render the face; **swap the character LoRA in here**, not in the base gen.
6. *Optional:* manual inpaint, skin contrast, SeedVR2 final upscale.

Final resolution ≈ **base × 1.7 × 2**. Keep the **same seed across passes** for consistency.

**Character LoRA tip:** generate the base from a *detailed prompt* with **no** character LoRA, then swap the LoRA in at the FaceDetailer stage (match its prompt to the image, or you get the LoRA's generic default face). LoRA on ZIB → structure; on ZIT → detail; load on **both** for maximum likeness.

Full per-stage settings, the resolution table, and optional improvement layers: `references/workflows.md`.

---

## Key realism technique

Z-Image defaults to airbrushed stock-photo gloss. The fix is **photographic specificity**, not adjectives.

Stack all three:
1. Real **camera body + lens** — "Sony A7R IV, 85 mm f/1.4 GM"
2. Real **film stock or sensor emulation** — "Kodak Portra 400, fine grain"
3. One **non-idealised human feature** — "visible skin pores, a small mole below the left jaw"

"Realistic", "8k", "masterpiece" do almost nothing. See `references/prompting-guide.md` §2 for vocabulary tables and texture anchors.

---

## Gaze control for high- and low-angle shots

The characteristic failure: the model tilts the subject's chin to maintain eye contact with the lens, defeating the angle. Fix it by giving the gaze a **concrete anchor away from the camera**.

- **High angle:** "head bowed, gaze fixed on the book in her lap" — never pair "looking at viewer" with "from above"
- **Low angle:** "chin lifted, gaze locked on the horizon far above the camera"
- **Z-Image:** add negative `looking at camera, looking at viewer, eye contact, face tilted up`
- **Turbo:** phrase positively — "completely unaware of the camera, candid documentary photograph"

A high-angle **face close-up** is the hardest case — there is no surface below for the gaze to anchor to. Widen to medium shot or accept a retry. See `references/prompting-guide.md` §5 for working prompt templates.

---

## Failure modes & QC

Characteristic artefacts of the family and the fastest fix for each:

| Artefact | Cause | Fix |
|---|---|---|
| Plastic / waxy / airbrushed skin, stock-photo gloss | Family default aesthetic | Stack camera body + film stock + one non-idealised feature (see realism technique above) |
| Chin tilts up/down to keep eye contact on a high/low angle | Model maintains eye contact with the lens | Anchor the gaze on a concrete object away from the camera; Z-Image: add `looking at camera` negatives |
| Over-saturated, over-cooked edges (Turbo) | CFG raised above the guidance-free baseline, or LoRA loaded at 1.0 | Keep Turbo at CFG 1.0 (ComfyUI); load LoRA at ~0.8 |
| Outputs look samey across seeds (Turbo) | Distillation converges toward the strongest mode | Switch to Z-Image for diversity, or vary the prompt — not just the seed |
| Garbled / wrong rendered text | Too many words, or curly/smart quotes | ≤10 words per text block, wrapped in straight double quotes |
| Deformed hands, extra fingers | Common DiT weakness | Z-Image: add `extra fingers, deformed hands` negatives; Turbo: re-roll seed or describe hands positively |
| Uncanny / contradictory look | Mixed mediums, moods, or lenses in one prompt | One medium, one mood, one lens — contradictions don't average out |
| Negatives seem ignored (Turbo) | Guidance-free (CFG 1.0 in ComfyUI) doesn't apply negatives | Phrase constraints positively inside the prompt (the CFG > 0 workaround is in Licence & limitations) |

---

## Pre-flight checklist

Before hitting Queue Prompt:

1. Sentence, not a tag list?
2. Camera body + lens named?
3. Light source + direction + quality + colour temperature named?
4. At least one non-idealised feature if the subject is a person?
5. Exactly one style / medium?
6. **Turbo:** all constraints phrased positively inside the prompt?
7. **Z-Image:** negative prompt under ~180 characters, free of contradictions?
8. High / low angle shot: gaze anchored on a concrete object away from the lens?
9. LoRA dataset: only the rotation / shot-size clause varies between set images?
10. Rendered text wrapped in straight double quotes, under ~10 words per block?

---

## Licence and known limitations

**Licence:** Apache-2.0 for all currently released variants (Z-Image and Z-Image-Turbo). Z-Image-Edit and Z-Image-Omni-Base are still unreleased as of mid-2026 (both marked "to be released" on the official GitHub); verify their licences before use when they land.

**Turbo negative-prompt behaviour is contested.** The Tongyi-MAI team states negatives are ignored at the guidance-free setting (CFG 1.0 in a ComfyUI KSampler / `guidance_scale=0` in diffusers). ComfyUI users report that raising CFG to 1.2–1.5 re-introduces weak negative subtraction. The official guidance is authoritative; CFG > 1 on Turbo is a community workaround, not a supported feature.

**Confidence of claims in this skill.** **Primary / verified** (read from the official model card, the official ComfyUI template, and diffusers): architecture (6B S3-DiT, Qwen-3 4B encoder), Apache-2.0 licence, the stock node settings (shift 3, `lumina2`, `res_multistep`/`simple`, the steps/CFG in the templates), the official quant files, the diffusers pipeline classes, and the core prompting rules (natural language not tag soup, bilingual EN/ZH text, Turbo's guidance-free behaviour with negatives inert). **Official-via-docs** (model card recommendations — high confidence, spot-verify if load-bearing): the step/CFG *ranges* for the undistilled base and the Turbo "9 → 8 DiT forwards" detail. **Community / single-source** (flagged inline where used): VRAM thresholds for quantised builds, community fp8/GGUF requants, the **multi-stage pipeline numbers** (per-stage steps/denoise, the ×1.7/×2 upscale ladder — often from custom-finetune workflows, so tune them for stock weights), the Turbo CFG > 1 negative-prompt workaround, and the camera-vocabulary, gaze-anchor, and 8-point rotation phrasings (well-supported extrapolations, not all A/B-tested specifically on Z-Image). **Fun Union ControlNet** — model filenames, ComfyUI node names, and the `control_context_scale` guidance are community/third-party; verify filenames against the `alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1` HF repo before downloading.

**Release timeline:** Z-Image-Turbo shipped 26 Nov 2025; the undistilled Z-Image base 27 Jan 2026. This is a fast-moving family — re-verify volatile specifics (quant filenames, VRAM numbers, ComfyUI template details, LoRA tooling) before relying on them.

**VRAM for Z-Image (undistilled):** Tongyi-MAI has not published an inference VRAM figure. At 6B parameters in bfloat16 plus the shared encoder and VAE, budget at least 16 GB; a high-VRAM card (24 GB+) gives comfortable headroom for larger batches or resolutions.

---

## Reference files

| File | When to read it |
|---|---|
| `references/prompting-guide.md` | 6-part prompt anatomy in full detail; realism vocabulary; camera vocabulary (8-point rotation, shot sizes, high/low angle); lighting vocabulary; bilingual text rendering; common mistakes; drop-in templates |
| `references/workflows.md` | Multi-stage ComfyUI pipelines: the minimal build, the layered ZIB+ZIT pipeline with per-stage settings, resolution table, universal node settings (ModelSamplingAuraFlow / lumina2 / EmptySD3LatentImage), character-LoRA-via-detailer method, optional layers (skin contrast, SeedVR2, tiled upscale); **§9: Fun Union ControlNet** (V2.1 files, ModelPatchLoader + QwenImageDiffsynthControlnet nodes, all conditioning types and preprocessors, Turbo-only caveat); **§10: face identity methods** (LoRA, inpaint, IP-Adapter status) |
| `references/lora-training.md` | LoRA loading settings; dataset generation workflow; Ostris AI-Toolkit hyperparameters; training adapter requirement for Turbo; debugging identity collapse and angle failures |
