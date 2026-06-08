# Z-Image Multi-Stage ComfyUI Workflows

How to build layered rendering pipelines that get production-quality results — generate small, refine, then upscale in passes, using **ZIB for structure and ZIT for detail**.

The settings here come from two sources, kept labelled because they are not interchangeable:
- **Official** — the stock ComfyUI Z-Image-Turbo template (`Comfy-Org/workflow_templates`).
- **Community** — the layered pipeline pattern popularised by widely-shared community ComfyUI workflows (e.g. the "Moody" ZIB+ZIT graphs on Civitai). These often run **custom community finetunes** of Z-Image, so treat their step/CFG numbers as well-tuned starting points, not stock requirements. The *architecture* transfers to stock Z-Image; the exact numbers may need a nudge.

---

## 1. The minimal build (start here)

A single-stage text-to-image graph — the official template:

```
UNETLoader (z_image_turbo_bf16) → ModelSamplingAuraFlow (shift 3) → KSampler
CLIPLoader (qwen_3_4b, type "lumina2") → CLIPTextEncode (positive) ─┘
EmptySD3LatentImage (1024×1024) ──────────────────────────────────┘
KSampler → VAEDecode → SaveImage   (VAELoader = ae.safetensors)
```

Official Turbo KSampler: **8 steps, CFG 1.0, sampler `res_multistep`, scheduler `simple`, denoise 1.0.** That is the whole baseline. Everything below is layered on top of it.

> **Latent node:** use **`EmptySD3LatentImage`** (the official template's choice), not the legacy `EmptyLatentImage`.

---

## 2. The layered pipeline (the full build)

Each stage takes the previous stage's output and improves one thing. Bypass any optional stage you don't need.

| # | Stage | Model | Purpose |
|---|---|---|---|
| 1 | **1st-gen** (txt2img) | ZIB | Composition, pose, overall structure |
| 2 | **Latent upscale** | — | Raise resolution before detailing |
| 3 | **2nd-gen** (hires refine) | ZIT | Fine details: fingers, face, text |
| 4 | **Tiled SD upscale** | ZIT | Resolution + micro-detail, tile by tile |
| 5 | **Face/auto detailer** | ZIT | Re-render the face; swap in a character LoRA |
| 6 | **Manual inpaint** *(opt)* | ZIT | Fix a region the auto-detector misses |
| 7 | **Skin contrast** *(opt)* | — | Add skin micro-texture for realism |
| 8 | **SeedVR2** *(opt)* | SeedVR2 | Heavy final upscale (high VRAM) |

**Two-pass discipline** (the reason this beats one big render):
- **1st gen — judge composition only.** Reroll the seed until the layout and pose are right. Minor defects are fine; they get fixed downstream.
- **2nd gen — judge the fine details.** Fingers/toes, facial expression, rendered text, small artefacts.

Preview after stage 1 (and again after stage 3) *before* committing to the expensive upscale stages.

---

## 3. Per-stage settings (community layered pipeline)

Verified from a representative community ZIB+ZIT graph. CFG values are **ComfyUI KSampler** values (see §5 on the CFG=1 convention).

| Stage | Sampler / scheduler | Steps | CFG | Denoise | Negatives | Notes |
|---|---|---|---|---|---|---|
| 1st-gen (ZIB) | `euler` / `simple` | ~17 | 3.0 | 1.0 | **real prompt** | Base dims (e.g. 640×960) |
| 2nd-gen (ZIT) | `dpmpp_2m_sde` / `sgm_uniform` | ~11 | 1.0 | partial (hires) | **zeroed** | Latent from stage 2 |
| Tiled SD upscale (ZIT) | `dpmpp_2m_sde` / `sgm_uniform` | 3 | 1.0 | **0.23** | zeroed | ~1024 tiles, ×2 factor |
| Face detailer (ZIT) | `dpmpp_2m_sde` / `sgm_uniform` | 4 | 1.0 | **0.42** | zeroed | yolov8m bbox + SAM |
| Manual inpaint (ZIT) | `dpmpp_2m_sde` / `sgm_uniform` | 4 | 1.0 | **0.39** | zeroed | mask → SEGS, dilate ~8 px |

**Detailer/refine denoise rule:** raise denoise up to ~**0.54** for more prompt- and LoRA-adherence; lower it to preserve the original. Keep the **tiled upscale denoise low (~0.2–0.25)** — high denoise there invents new content per tile.

> The 1st-gen → 2nd-gen handoff in some community graphs uses `return_with_leftover_noise` + `add_noise` across mismatched step schedules. That is one author's hires-fix trick, not a canonical requirement — a clean "decode → latent-upscale → re-noise → refine" chain works fine.

---

## 4. Resolution strategy — generate small, upscale in layers

Z-Image is happiest generating at a **low base resolution** (~0.6 MP), then climbing in passes. Final resolution = **base × 1.7 (2nd-gen latent upscale) × 2 (SD upscale)**.

| Aspect | Use | Base (W×H) | Final (×1.7 ×2) |
|---|---|---|---|
| 2:3 | Portrait | 640 × 960 | 2176 × 3264 |
| 3:4 | Portrait (stable) | 672 × 896 | 2285 × 3046 |
| 9:16 | Tall / mobile | 576 × 1024 | 1958 × 3482 |
| 1:1 | Square | 768 × 768 | 2611 × 2611 |
| 4:3 | Landscape | 896 × 672 | 3046 × 2285 |
| 3:2 | Landscape | 960 × 640 | 3264 × 2176 |
| 16:9 | Widescreen | 1024 × 576 | 3482 × 1958 |

Latent upscale node: `LatentUpscaleBy`, method `bislerp`, factor ~1.7. SD upscale: `UltimateSDUpscale`, factor 2, with a dedicated upscale model (§7).

---

## 5. Universal node settings

- **ModelSamplingAuraFlow on every model path, `shift = 3`.** Stock — the official template includes it. Apply it to the ZIB path, the ZIT path, and every detailer/upscaler model input.
- **CLIPLoader type `lumina2`** for `qwen_3_4b.safetensors`. Stock.
- **CFG = 1.0 is "guidance-off" in ComfyUI.** The KSampler formula collapses to the conditional at cfg 1, so Turbo runs at **cfg 1.0 in ComfyUI** — this is the same thing as `guidance_scale = 0` in diffusers. Do **not** type cfg 0.0 into a KSampler (it outputs the unconditional and ignores your prompt). Use cfg 1.0 for every ZIT pass; cfg 3–5 only for ZIB passes that need true classifier-free guidance.
- **Negatives:** ZIB passes take a **real negative prompt**; ZIT passes wire the negative through `ConditioningZeroOut` (turbo ignores negatives, so zero them rather than feed text).
- **Seed:** keep the **same seed across 1st-gen, 2nd-gen, and SD upscale** for consistent results; reset to a fixed value (e.g. 0) once you've found a good composition. Only vary the later-stage seed if a stage needs a localised re-roll.

---

## 6. Using LoRAs (any LoRA — style, concept, character, not just ones you train)

This is the generic "I downloaded a LoRA, how do I run it" path. Training your own is in `references/lora-training.md`; the high-likeness character method is the subsection at the end.

> **Sourcing:** node names and the QKV/PR facts below are hard facts (verified against ComfyUI PRs/issues). The weight numbers and stacking guidance are **community craft** — named Civitai/HF authors who've run thousands of generations — so they're given as ranges and the fast-moving ones are flagged. Read a LoRA's own model card for the weight its author tested.

### Node wiring

Z-Image is loaded as a diffusion model (not a checkpoint). A Z-Image LoRA patches the **DiT** (attention + MLP), loaded with a LoRA loader on the model path — right after the model loader, before `ModelSamplingAuraFlow`:

```
Load Diffusion Model → LoRA loader → ModelSamplingAuraFlow (shift 3) → KSampler
CLIPLoader (qwen_3_4b, "lumina2") ─────────────────────────────────┘
```

**Which loader:** the ComfyUI core PR #12717 repro adds the LoRA with the **full `LoraLoader`** (model + clip). **`LoraLoaderModelOnly`** also works and is the clean choice — Z-Image LoRAs target the DiT, and most (Ostris-trained, diffusers-format) carry **no text-encoder weights**, so the Qwen-3/CLIP side is usually a no-op either way. Don't agonize over it; if a LoRA *does* ship Qwen-3 keys, use the full `LoraLoader` so they apply. *(DiT target is verified from PR #12717; the model-vs-model+clip node choice is a usage detail, not a break-or-not fact.)*

### The gotcha that makes a LoRA silently do almost nothing (Z-Image-SPECIFIC)

Most published Z-Image LoRAs ship in **diffusers format** with separate `to_q` / `to_k` / `to_v` attention keys, but Z-Image stores attention as a single **fused QKV** matrix. On older ComfyUI the loader **silently drops the attention deltas** — you see `lora key not loaded` warnings and the LoRA "barely does anything." The MLP/FFN weights still load, so it's *attention-degraded*, not fully dead — which is exactly why it's easy to misread as "this LoRA is weak, raise the weight."

**Fixed in ComfyUI core PR #12717.** So when a LoRA underperforms, **update ComfyUI first**, before touching weights. (Primary: ComfyUI PR #12717 "fix: Z-Image LoRA and model loading for HuggingFace format weights"; issue #10973. A third-party `Comfyui-ZiT-Lora-loader` did conversion before the core fix; on current ComfyUI you shouldn't need it.)

### Weight — there is no magic 0.8 cap

Start **~0.7–0.8** and sweep **0.5–1.2**. By LoRA type, named authors land at very different places:

| LoRA type | Typical weight | Why |
|---|---|---|
| **Style / film** | often **0.3–0.5** | full strength over-smooths skin and crushes the base look |
| **Realism enhancer** | **~0.6–0.7** | potent; start low and raise |
| **Character / concept** | **~0.7–1.0** | needs more strength to carry identity |

These are **per-LoRA tunings, not a model-wide ceiling.** The old "1.0 overcooks Turbo" framing was overstated — there's no documented hard cap; a saturated result means *that* LoRA is hot, not that 1.0 is illegal. *(Community; exact numbers are fast-moving and sources mildly disagree — treat as starting points, and prefer the weight printed on the LoRA's own model card.)*

### Stacking multiple LoRAs (general ComfyUI craft — stable across models)

Use the rgthree **Power Lora Loader** node: multiple LoRAs in one node, per-LoRA strength, on/off toggles, "no real limit" (`FlexibleOptionalInputType`). Toggle to **separate model/clip strengths** via the advanced view if needed. On Turbo, **keep combined strength near or under ~1.0** to avoid burning/overexposure — a conservative heuristic; with normalization you can go higher, and a Z-Image-specific LoRA-merger node (`ComfyUI-ZImage-LoRA-Merger`) exists precisely because chained strengths accumulate on distilled models. Ordering has minor effects. *(rgthree README; community.)*

### ZIB ↔ ZIT cross-compatibility: loads fine, doesn't transfer cleanly (Z-Image-SPECIFIC)

Base and Turbo share the **identical S3-DiT**, so any LoRA **loads on either without a format error.** But "loads" ≠ "transfers": a **Base-trained LoRA run on Turbo** shows **softer identity, dropped face consistency, shifted color/background** — and may need a strength bump.

**Community best practice (incl. the official Tongyi-MAI HF discussion #18): train on Z-Image Base, generate on Z-Image-Turbo.** Base is the better base for cross-prompt control; train *on* Turbo only if you specifically want fast-delivery behavior. The exact magnitude of Base→Turbo degradation is **genuinely contested** across sources (reports range from "~100% similarity" to "little impact") — so **test it, don't assume.** *(Sources: HF Tongyi-MAI #18; RunComfy AI-Toolkit notes; lilting.ch. Fast-moving.)*

### "Fights distillation" — why a Turbo-trained LoRA can look blurry (Z-Image-SPECIFIC)

A LoRA trained **directly on Turbo** can disturb Turbo's few-step "landing trajectory" — it alters not just the subject/style but how the model converges in 8 steps, producing **blurry output at 8 steps that only cleans up at ~30.** This is the other reason the train-on-Base path is preferred, and why inference-time **DistillPatch** correction LoRAs exist (DiffSynth-Studio `Z-Image-Turbo-DistillPatch`; a Civitai equivalent). If a Turbo LoRA renders soft at 8 steps, suspect this before blaming your prompt. *(lilting.ch; DiffSynth-Studio HF.)*

### Trigger words

Place trigger tokens at the **very start of the prompt**. Z-Image's encoder is the Qwen-3 LLM, not a CLIP tag-matcher, so a trigger generally works best folded into natural language rather than dropped as a bare tag — but **how the LLM encoder weights trigger tokens vs. tag-based SD1.5/SDXL LoRAs is not well established** in community sources yet; follow the LoRA author's stated trigger and phrasing. *(Open question — flagged.)*

### Ecosystem (early–mid 2026)

An active Civitai/HF ecosystem tags its uploads **`ZImageTurbo`**: **style** (e.g. "Technically Color Z," trigger `t3chnic4lly`), **realism enhancers** (e.g. "Realistic Snapshot"), and **character/concept** LoRAs. Most are trained with the **Ostris AI-Toolkit** (which ships a dedicated Z-Image-Turbo training adapter), which is why so many ship in diffusers format — tying straight back to the QKV gotcha above. Community "apply any LoRA" ComfyUI workflows exist (Civitai 2194203, Next Diffusion, RunComfy). *(Civitai; Ostris HF; fast-moving.)*

---

### High-likeness character LoRAs (the detailer "face-swap" method)

Loading a character LoRA into the *base* generation often gives mediocre results. The community-proven pattern:

1. **Generate the base WITHOUT the character LoRA.** Describe the character in as much detail as you can in the positive prompt.
2. **Swap the character LoRA in at the FaceDetailer stage** (stage 5) — it re-renders just the face with the LoRA applied.
3. **Match the detailer's prompt to the rest of the image.** If you leave a generic prompt, you get the LoRA's built-in default face/scene instead of your subject.

**Where to place a LoRA — ZIB vs ZIT:**
- A LoRA on the **ZIB** pass affects **image structure** more strongly.
- A LoRA on the **ZIT** pass leans toward **detail/finish**.
- For **maximum likeness**, load the same character LoRA on **both** ZIB and ZIT passes.
- Because LoRAs load on either variant but transfer best from a Base-trained source (see cross-compat above), **a Base-trained character LoRA is the safest choice** for either slot. Use the `Power Lora Loader` (rgthree) to stack/toggle. (See `references/lora-training.md` for training and `## 6` above for load-weight guidance.)

---

## 7. Optional improvement layers

**Skin contrast (realism).** After detailing, blend the image with a skin-detail upscale model pass:
- Model: a `1x` skin-contrast ESRGAN model (e.g. `1xSkinContrast-High-SuperUltraCompact`), run via `ImageUpscaleWithModel`.
- Blend back over the original with `ImageBlend`, mode `normal`, intensity ~**0.4** (1.0 = full strength, 0 = off).
- Best for Western / photorealistic styles; skip for stylised or everyday work.

**Upscale models** (for the tiled SD upscale, drop in `models/upscale_models/`):
- `4xNomosWebPhoto_RealPLKSR` — balanced, good default.
- `4xNomos8k_atd_jpg` — high quality, slower.
- `4xUltraSharp` — sharper, more aggressive.

**SeedVR2 final upscale** (optional, heavy). A separate diffusion upscaler (`SeedVR2` nodes, e.g. the 7B or 3B GGUF) targeting ~4096 px. First run downloads large models; not recommended on low-VRAM GPUs. Use 3B if the 7B OOMs.

**Tiled-upscale prompt caveat.** When `UltimateSDUpscale` splits the image into tiles, a tile only "sees" its local patch — so a prompt that says "a tattoo reading 'X' below the collarbone" can make the model stamp that text onto unrelated smooth-skin tiles (shoulder, arm, back). If you render localised text/marks, give the upscale pass a **simpler prompt** (or the conditioning switch many graphs expose) so per-tile hallucinations don't reproduce it.

---

## 8. Build order summary

1. Stand up the **minimal build** (§1) and confirm models load.
2. Add **ModelSamplingAuraFlow shift 3** and the **ZIB→latent-upscale→ZIT** two-pass (§2–4).
3. Add the **FaceDetailer** stage; wire the character LoRA here (§6).
4. Add **UltimateSDUpscale** with a 4x model (§4, §7).
5. Layer in **skin contrast / SeedVR2 / manual inpaint** only as needed (§7).

Bypass freely: the optional stages are toggleable so you can preview cheaply and only pay for the heavy passes once the base is right.

---

## 9. Fun Union ControlNet (pose, depth, canny, and more)

Source: `alibaba-pai/Z-Image-Turbo-Fun-Controlnet-Union-2.1` on Hugging Face (official), plus the `Comfy-Org/workflow_templates/image_z_image_turbo_fun_union_controlnet.json` template (verified from raw JSON).

**Critical: Z-Image Turbo only.** The Fun Union ControlNet is distilled for Z-Image-Turbo. The undistilled Z-Image base has its own patch files (`alibaba-pai/Z-Image-Fun-Controlnet-Union-2.1`) but ComfyUI support for the base variant is an open feature request with no current resolution (issue #12243). Use the Turbo + ControlNet combination for all structure-guided work.

### Model files

All files install to `models/model_patches/` (not `models/controlnet/`).

**Recommended file (V2.1, 8-step optimised):**

| File | Size | Conditions | Notes |
|---|---|---|---|
| `Z-Image-Turbo-Fun-Controlnet-Union-2.1-8steps.safetensors` | 6.71 GB | Canny, Depth, Pose, MLSD, HED, Scribble | Tuned for 8-step Turbo — use this |
| `Z-Image-Turbo-Fun-Controlnet-Union-2.1-2601-8steps.safetensors` | 6.71 GB | Canny, Depth, Pose, MLSD, HED, Scribble | Timestep 2601 variant |
| `Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors` | 6.71 GB | Adds Gray | Timestep 2602 variant |
| `Z-Image-Turbo-Fun-Controlnet-Union-2.1-lite-2601-8steps.safetensors` | 2.02 GB | Same types, weaker control | 3 blocks (vs 6 full); use on low VRAM |

For tiled upscaling with ControlNet: `Z-Image-Turbo-Fun-Controlnet-Tile-2.1-8steps.safetensors` (6.71 GB) — same repo, same install path.

### ComfyUI nodes (both built-in core, no custom install needed)

| Node | Role |
|---|---|
| `ModelPatchLoader` | Loads `.safetensors` from `models/model_patches/` |
| `QwenImageDiffsynthControlnet` | Applies the patch to the model; key inputs: `model`, `model_patch`, `vae`, `image` (preprocessed), `strength` (default 1.0), optional `mask` |

These are standard ComfyUI core nodes added in PR #11062 (ComfyUI v0.3.51+). The `QwenImageDiffsynthControlnet` name is misleading — it handles both Qwen-Image and Z-Image patches.

**Recommended `control_context_scale`:** 0.65–0.80 (the parameter on `QwenImageDiffsynthControlnet`). The official template uses `strength=1.0`.

### Conditioning types and preprocessors

The conditioning type is determined by which preprocessor feeds the image — there is no explicit "mode" switch on the apply node. One model handles all types (Union architecture).

| Type | Preprocessor node | Notes |
|---|---|---|
| **Pose** | `DWPreprocessor` (DWPose) | Generates skeleton with body + face + hand keypoints |
| Depth | `DepthAnythingV2Preprocessor` | Depth Anything V2 for real-photo depth |
| Canny | `CannyEdgePreprocessor` | Default thresholds 0.1–0.32 (from template) |
| HED | `HEDPreprocessor` | Soft edges; better than Canny for complex outlines |
| Scribble | `ScribblePreprocessor` or hand-drawn | Rough structural constraint |
| MLSD | `MLSDPreprocessor` | Line segments; good for architectural/interior |

All preprocessors are available via `comfyui_controlnet_aux` (install via ComfyUI Manager).

### Sampler settings with ControlNet

Keep all standard Z-Image-Turbo settings — the ControlNet is additive, it does not change the base sampler:
- **Steps:** 8, **CFG:** 1.0, **Sampler:** `res_multistep`, **Scheduler:** `simple`
- **ModelSamplingAuraFlow shift 3** — required on the ControlNet-patched model path as well
- Negative conditioning: wire through `ConditioningZeroOut` as usual

### Official template

The Comfy-Org template (`image_z_image_turbo_fun_union_controlnet.json`) defaults to Canny edge detection. To use it with pose: swap the `Canny` node for `DWPreprocessor`, connect the skeleton image output to `QwenImageDiffsynthControlnet`'s `image` input. The rest of the graph is unchanged.

---

## 10. Face identity — available methods

No PuLID or IP-Adapter face implementation exists for Z-Image as of June 2026. The following methods are in order of reliability:

| Method | When to use | Notes |
|---|---|---|
| **Subject LoRA** (via FaceDetailer) | Recurring character, product persona | Most reliable; train on 20–50 images; load at stage 5 (§6 above) |
| **Inpaint + SAM mask** | Swap or refine the face region of an existing image | Use `SAM3Grounding` → `InpaintModelConditioning` + `DifferentialDiffusion` |
| **Z-Image-Edit** | Instruction-based editing of an existing image | Announced; verify availability at time of use |
| **Community IP-Adapter (Boyonodes)** | Experimental generic image conditioning | No published weights; requires manual SD3 weight conversion; not recommended for production |

**The practical identity path for Z-Image is: train a character LoRA and inject it at the FaceDetailer stage (§6).** This gives consistent identity and composits cleanly with the multi-stage pipeline.
