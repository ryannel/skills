---
name: z-image
description: >
  Authoritative guide for the Z-Image model family (Z-Image and Z-Image-Turbo, Alibaba Tongyi Lab) in ComfyUI
  or the diffusers API. Use this whenever the user touches Z-Image in any way, even obliquely: choosing
  between Z-Image and Turbo (or weighing Z-Image against other models), installing or setting it up in ComfyUI
  (file layout, loaders, quantisation, ControlNet), writing or fixing prompts (the Qwen-3 LLM encoder needs
  sentences not tags; realism, killing plastic/waxy stock-photo skin, bilingual text rendering, high/low-angle
  gaze control), pose control and structural conditioning (Fun Union ControlNet — Pose, Depth, Canny, HED,
  Scribble; ModelPatchLoader + QwenImageDiffsynthControlnet nodes; Turbo-only; V2.1 model files), face
  identity (no PuLID for Z-Image — character LoRA via FaceDetailer is the standard approach), building single-
  or multi-stage workflows (hires refine, tiled upscale, face detailer, img2img/inpaint) with practical
  sampler/CFG/denoise/resolution/step settings, using LoRAs (loading any downloaded style/realism/character
  LoRA with the right node, weight-by-type tuning, stacking with rgthree, the diffusers-format QKV
  silent-failure gotcha, Base↔Turbo cross-compatibility), generating a dataset and training a LoRA with the
  Ostris AI-Toolkit, creating a consistent original character (anchor image → edit-model dataset factory →
  character LoRA → FaceDetailer deployment; multi-outfit and multi-character limits), training a style LoRA
  (diverse-subject datasets, prose captions, XY-grid evaluation), using Z-Image-Turbo as the realism refiner
  in a mixed-model pipeline (e.g. refining SDXL renders), or checking what the family's Apache-2.0 licence
  permits for commercial work compared with the gated models in this suite. Use this for any question about
  Z-Image in any context. Choosing between models, comparing them, or working out which skills and install
  commands a job needs is [`generative-media-atlas`](../generative-media-atlas/)'s job — start there when the
  model is not already settled.
---

# Z-Image Family

Z-Image is Alibaba Tongyi Lab's open-weights image generation family. It's a **6B-parameter Scalable Single-Stream DiT (S3-DiT)**, where text, visual semantic tokens, and image VAE tokens travel through one unified sequence. The text encoder is **Qwen 3 4B**, an LLM-grade encoder that parses your prompt as natural language. It's bilingual (English + Chinese). Apache-2.0 covers the whole family.

## Variant selector

| Variant | Distilled | Steps | CFG | Negatives | VRAM ³ | Licence | Use when… |
|---|---|---|---|---|---|---|---|
| **Z-Image** | No | 25–50 | 3.0–5.0 | Yes | ~16 GB comfortable ³ | Apache-2.0 | final renders, LoRA training base, fine-grained negative control |
| **Z-Image-Turbo** | Yes (Decoupled-DMD) | 8 effective ¹ | 1.0 ² | No ² | ~16 GB comfortable; 6 GB workable ³ | Apache-2.0 | rapid iteration, dataset generation, drafting |
| **Z-Image-Edit** | — | — | — | — | — | Apache-2.0 | instruction-based image editing — *announced, not yet released* `[pending release]` |
| **Z-Image-Omni-Base** | — | — | — | — | — | Apache-2.0 | generation + editing in one model — *announced, not yet released* `[pending release]` |

> ¹ **ComfyUI KSampler: 8 steps** (sampler `res_multistep`, scheduler `simple` per the official template). **diffusers:** `num_inference_steps=9` → "this actually results in 8 DiT forwards" (official model card).
> ² **CFG 1.0 in a ComfyUI KSampler *is* guidance-off.** It equals `guidance_scale=0` in diffusers, and it's the value in the official template. Never type CFG 0.0 into a KSampler — it outputs the unconditional and ignores the prompt. Negatives are inert here; zero them with `ConditioningZeroOut`. Raising CFG to 1.2–1.5 re-introduces weak negative subtraction, at roughly 2x the cost, and causes over-saturation. This is a community workaround, not a supported feature `[contested]`. Use it only for stubborn artefacts.
> ³ **These are comfort bands, not floors.** Tongyi-MAI publishes no minimum for either variant. At 16 GB, the bf16 DiT and the Qwen-3 encoder both stay resident. Below that, ComfyUI shuttles weights to system RAM between passes. That costs time, not the ability to render. Official int8 DiT builds (~6.2 GB) ship for **base as well as Turbo**, and Turbo is reported running end-to-end on an **RTX 2060** `[community — Royal_Carpenter_1338]`. Read a small card as "pull a quantised build and expect it slower", not "unsupported" — see **Setup & ecosystem**.

**Default workflow:** Draft in Turbo (8 steps, CFG 1.0) to find composition and seed. Re-render keepers in Z-Image (40 steps, CFG 4.0) for the final asset `[community — re-verify]`. Same prompt and seed — but Z-Image will reinterpret it slightly. That's expected. For layered production pipelines, see **Production pipelines & mixing models** below.

> **A `../link/` on this page that doesn't resolve is a skill you have not installed, not a broken
> page.** [`generative-media-atlas`](../generative-media-atlas/) is the map of this suite: which
> model fits a job, which skills that job needs, and the commands to install them. It works on its
> own, so it is the one to add first — `npx skills add ryannel/skills --skill generative-media-atlas`

---

## The one rule that changes everything

Qwen 3 4B is an LLM-grade encoder. It parses syntax and clause structure. Write a **sentence**, not a tag list. (This is the encoder class talking, not folklore: the same rule governs FLUX.2's Mistral/Qwen3 encoders. The *opposite* rule — weighted tags, verbatim trigger tokens — governs CLIP models like SDXL. Prompting dialect, LoRA trigger handling, and caption style all follow the encoder **here**.) One refinement, which does not undo the rule: the encoder is a proxy for the **caption corpus**, and on two suite models the two come apart. [`anima`](../anima/) has an LLM encoder but takes weighted Danbooru tags. [`ideogram-4`](../ideogram-4/) has one too, but takes JSON. Encoder class sets the ceiling on what a dialect *can* express; the corpus decides what the model is actually fluent in. They agree here, and they agree on most models, which is why the encoder remains the right first guess. But **check what a model was captioned on before inferring its dialect from its encoder name.**

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

**Length sweet spot:** 80–250 words. Attention drifts past about 75 tokens, so put the subject, key text-to-render, and primary lens in the first 75 `[community]`. The soft cap is 512 tokens (about 384 words). Set `max_sequence_length=1024` locally if you genuinely need more.

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

**Stock node settings** (from the official template): set the **CLIPLoader type to `lumina2`**. Use **`EmptySD3LatentImage`** for the latent, not the legacy `EmptyLatentImage`. Put a **`ModelSamplingAuraFlow` node (shift 3)** on the model path before the sampler.

**Low-VRAM / quantisation:**
- **Official** (in the Comfy-Org repos): int8 DiT `z_image_int8_convrot.safetensors` / `z_image_turbo_int8_convrot.safetensors` (~6.2 GB each). This build exists for **base as well as Turbo**, and ships with its own ComfyUI templates `image_z_image_int8` and `image_z_image_turbo_int8`. There's also an NVFP4 DiT `z_image_turbo_nvfp4.safetensors` (~4.5 GB, **Turbo only**), plus quantised encoders `qwen_3_4b_fp8_mixed` (~5.6 GB) and `qwen_3_4b_fp4_mixed` (~3.5 GB).
- **Community** (requants, not official): fp8 DiT (e.g. Kijai's `fp8_scaled_e4m3fn`) and GGUF Q2–Q8 (e.g. unsloth). GGUF requires the `ComfyUI-GGUF` custom node (city96). There is no official fp8 DiT.
- **The 16 GB number is a comfort band, not a floor**, and nothing official states a floor. At 16 GB, the bf16 DiT stays resident alongside the encoder with no offload. Below that, ComfyUI pages weights in and out per pass, so you lose throughput, not capability. Quantised builds sit comfortably on 6–8 GB `[community — re-verify]`, and Turbo is reported working on an **RTX 2060** `[community — Royal_Carpenter_1338]`. So treat a small card as a reason to pull an int8 or NVFP4 DiT plus a quantised encoder, not as a reason to skip the model. Base is the harsher variant to run this way, for a reason unrelated to size: it wants 25–50 steps where Turbo wants 8, so whatever offload penalty you pay is paid several times over per image.

**diffusers API:** `from diffusers import ZImagePipeline`. This shipped in **stable diffusers ≥ 0.36** (`pip install -U diffusers`) — the model card's `pip install git+…` line is launch-day legacy from before 0.36. Latent-space `ZImageImg2ImgPipeline` and `ZImageInpaintPipeline` also exist. These run on the released base/Turbo weights and are **not** the still-unreleased, instruction-based Z-Image-Edit.

**ControlNet (pose, depth, canny, and more).** The official Fun Union ControlNet for Z-Image **Turbo** is from Alibaba PAI. A single Union model file handles all conditioning types. File: `Z-Image-Turbo-Fun-Controlnet-Union-2.1-8steps.safetensors` (6.71 GB) or the lite variant (2.02 GB) → `models/model_patches/`. ComfyUI nodes are both built-in core: `ModelPatchLoader` (loads the patch) + `QwenImageDiffsynthControlnet` (applies it). Pose uses `DWPreprocessor` (DWPose). **Turbo only** — base Z-Image ControlNet has no ComfyUI support yet. Full file table, all V2.1 variants, node wiring, and per-type preprocessors: **`references/setup-and-workflows.md §9`**.

**Face identity & characters.** No PuLID or IP-Adapter face model exists for Z-Image. The character LoRA *is* the path, loaded at the FaceDetailer stage (references/setup-and-workflows.md §6). The full character pipeline — anchor image, the Qwen-Image-Edit dataset factory, rotation/expression coverage, multi-outfit and multi-character craft, failure modes — is **`references/characters.md`**. Method comparison is in `references/setup-and-workflows.md §10`.

---

## Per-variant settings

### Z-Image (undistilled)

Preserves the full training signal — best texture diversity, best base for LoRA training.

- **Steps:** 25–50. The official ComfyUI base template uses **25**; the diffusers card recommends 28–50 (example: 50). 40 is a safe all-rounder
- **CFG / guidance:** 3.0–5.0 (4.0 typical — the value in the official base template and diffusers example)
- **Sampler:** the official ComfyUI base template uses **`res_multistep` / `simple`** with `ModelSamplingAuraFlow` shift 3 — same chain as Turbo. Community finetune pipelines often substitute `euler` / `simple` (see `references/setup-and-workflows.md`)
- **Resolution:** 1024×1024 natively (officially 512–2048 px); 1:1, 4:3, 3:4 all work well
- **Negative prompts:** Use them. Baseline: `text, watermark, extra fingers, deformed hands, plastic skin, waxy skin, airbrushed, blurry, oversaturated` — keep under ~180 characters to avoid side effects `[community — re-verify]`
- **Seed diversity:** High; randomise freely

### Z-Image-Turbo (distilled)

Decoupled-DMD distillation removes CFG dependency. Fastest path from prompt to draft.

- **Steps:** ComfyUI KSampler **8 steps**; diffusers `num_inference_steps=9` (8 DiT forwards)
- **Sampler (official ComfyUI):** `res_multistep` / `simple`
- **CFG / guidance:** diffusers `guidance_scale=0`; **ComfyUI KSampler CFG 1.0** (cfg 1 = guidance-off — never 0.0 in a KSampler)
- **Resolution:** 1024×1024
- **Negative prompts:** Do not use — phrase all constraints positively inside the prompt
- **Seed diversity:** Lower than Z-Image; Turbo converges toward the strongest mode
- **LoRAs:** start ~0.7–0.8 and sweep 0.5–1.2. There is **no hard 0.8 cap** — style LoRAs often want 0.3–0.5, character 0.7–1.0. These are per-LoRA tunings read off named authors' cards, not a model-wide ceiling `[community — per-LoRA, not a hard rule]`. So read the card of the LoRA you actually loaded. If a LoRA "does almost nothing," update ComfyUI first: diffusers-format Z-Image LoRAs silently lose their attention weights on builds before core PR #12717. **Check which variant a LoRA you downloaded was trained on before wiring it in.** The published ecosystem is lopsided — ~2,190 LoRAs tagged `ZImageTurbo` against ~670 on base `[community — Civitai census, Aug 2026]` — so the odds are it is a Turbo LoRA even when your graph is a base one. The shared S3-DiT means it loads either way without error, which is exactly what makes the mismatch easy to miss. Full loading/stacking/cross-compat guidance: `references/setup-and-workflows.md §6`. Training: `references/lora-training.md`

---

## Production pipelines & mixing models

For production results, don't render once. **Layer passes: ZIB builds structure, ZIT refines and upscales.** Generate at a *low* base resolution, then climb. ZIB and ZIT are combined here, not either/or. For mixing in *other* model families entirely — where Z-Image-Turbo's usual job is the realism finish on someone else's render — see **Where Z-Image sits in the suite** below and `references/setup-and-workflows.md §11`. That section carries the decode-to-pixels handoff rule that makes cross-family chains work at all.

**The pipeline** (every optional stage is bypassable — preview cheaply, pay for heavy passes only once the base is right):

1. **1st-gen (ZIB)** — composition + pose at low base res (e.g. 640×960). Judge *layout only*; reroll the seed freely.
2. **Latent upscale** — `LatentUpscaleBy`, `bislerp`, ×1.7.
3. **2nd-gen (ZIT)** — hires refine for fingers, face, text. Judge *fine details* here.
4. **Tiled SD upscale (ZIT)** — `UltimateSDUpscale` ×2, low denoise (~0.23).
5. **FaceDetailer (ZIT)** — re-render the face; **swap the character LoRA in here**, not in the base gen.
6. *Optional:* manual inpaint, skin contrast, SeedVR2 final upscale.

Final resolution ≈ **base × 1.7 × 2**. Keep the **same seed across passes** for consistency.

The ×1.7 and ×2 multipliers and the ~0.23 tiled-upscale denoise come from a widely-shared community layered pipeline `[community — layered ZIB+ZIT graphs; convergent]`, whose graphs often run **custom Z-Image finetunes**. The *architecture* — generate small, upscale, refine, detail — transfers to stock weights unchanged. The exact numbers are well-tuned starting points to nudge, not stock requirements. Sourcing and the per-stage table: `references/setup-and-workflows.md §3`.

**The ladder also runs backwards.** Drafting in ZIT and finishing with a low-denoise **base** pass is a reported alternative that buys texture with compute `[community — Royal_Carpenter_1338]`. In practice this means loading the ComfyUI Z-Image upscaling template with the base DiT where it normally loads Turbo. The undistilled weights carry the texture diversity that Turbo's 8-step trajectory flattens, and real CFG and real negatives come back with them. It is a finishing pass on keepers, not a default, because the expensive model is now doing the expensive high-resolution passes. That's the inverse of why the ladder above is ordered as it is. Settings, the cost, and why it suits a small card: `references/setup-and-workflows.md §3`.

**Character LoRA tip:** generate the base from a *detailed prompt* with **no** character LoRA. Then swap the LoRA in at the FaceDetailer stage — match its prompt to the image, or you get the LoRA's generic default face. LoRA on ZIB → structure; on ZIT → detail; load on **both** for maximum likeness `[community — MyAIForce; strong]`.

Full per-stage settings, the resolution table, and optional improvement layers: `references/setup-and-workflows.md`.

---

## Realism — killing the plastic default

Z-Image defaults to airbrushed stock-photo gloss. The fix is **photographic specificity**, not adjectives `[community]`.

Stack all three:
1. Real **camera body + lens** — "Sony A7R IV, 85 mm f/1.4 GM"
2. Real **film stock or sensor emulation** — "Kodak Portra 400, fine grain"
3. One **non-idealised human feature** — "visible skin pores, a small mole below the left jaw"

"Realistic", "8k", "masterpiece" do almost nothing. See `references/prompting-guide.md` §2 for vocabulary tables and texture anchors.

---

## Gaze control for high- and low-angle shots

The characteristic failure: the model tilts the subject's chin to maintain eye contact with the lens, defeating the angle. Fix it by giving the gaze a **concrete anchor away from the camera** `[community]`.

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
| Negatives seem ignored (Turbo) | Guidance-free (CFG 1.0 in ComfyUI) doesn't apply negatives | Phrase constraints positively inside the prompt (the CFG > 1 workaround is in the Turbo-negatives note under *How to read the claims in this skill*) |
| Text, a tattoo or a logo you asked for once is stamped onto shoulder, arm or back after the tiled upscale | `UltimateSDUpscale` samples each tile against the *whole* prompt while the tile only sees its own patch — a smooth-skin tile has nothing else to satisfy "a tattoo reading X" with | Give the upscale pass a **simplified prompt** with the localised text/mark removed, or use the per-tile conditioning switch most graphs expose — `references/setup-and-workflows.md §7` `[community — convergent]` |

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

## Where Z-Image sits in the suite

Choose the model for the job — defaults like realism direction and prompting dialect are model-specific, not universal:

| Job | Z-Image | Reach for instead |
|---|---|---|
| Consistent characters | Strong via character LoRA + FaceDetailer (`references/characters.md`); no adapter shortcut | [`flux-2`](../flux-2/) for no-training multi-reference identity (ReferenceLatent, PuLID) |
| Style / character LoRA ecosystem | Fully supported and cheap to train (AI-Toolkit; `references/lora-training.md`) | [`sdxl`](../sdxl/) for the deepest trained-LoRA ecosystem and mature recipes; [`character-lora-training`](../character-lora-training/) for the craft that transfers across all of them |
| In-image typography | Workable for short bilingual text | [`ideogram-4`](../ideogram-4/) — the open-weights typography leader |
| Structural control (pose/depth/canny) | Fun Union ControlNet, **Turbo only** | [`sdxl`](../sdxl/) for the most mature, complete control stack |
| Photoreal faces and skin | **The headline strength** — once you pay the anti-gloss tax above; also the suite's standard face-pass finisher. This is settled rather than claimed: it is the axis the rest of the suite routes *here* for, and [`sdxl`](../sdxl/), [`krea-2`](../krea-2/), [`ideogram-4`](../ideogram-4/) and [`anima`](../anima/) all send you here on it | Nothing better in the suite on faces and skin themselves. [`sdxl`](../sdxl/) when the frame needs pose/depth control or an identity adapter more than it needs skin — compose and control there, finish here. [`krea-2`](../krea-2/) if you want a *non*-photoreal look without fighting a realism prior |
| Aesthetic range / stylistic exploration | One strong realism-leaning default | [`krea-2`](../krea-2/) — deliberately no house look (style refs, moodboards, official style LoRAs); Z-Image is *its* standard face/detail finisher, so the pairing runs both ways |
| Anime and illustration | Weak — the realism prior fights stylisation, and the anime LoRA ecosystem is thin here | [`anima`](../anima/) is the closest neighbour: also small (2B), also trainable on a consumer card — but its **weights** are non-commercial where Z-Image's Apache-2.0 is not. Its outputs are commercially free, so the difference bites only when you ship or host the model itself. [`sdxl`](../sdxl/) via the Illustrious/Pony dialects for the mature anime checkpoint ecosystem |
| Commercial use under the licence | **Apache-2.0, weights and outputs alike** — no revenue cap, no territory clause, no gate. The least legally encumbered model in the suite | Nothing is freer; the reach-for is the reverse. If a job forces you onto a gated model, read that skill's licence section first: [`ideogram-4`](../ideogram-4/) is non-commercial on its open weights, and [`anima`](../anima/) is non-commercial on the weights but not on what they produce |
| Mixed-model pipelines | **The realism refiner** — ZIT finishing other models' renders (`references/setup-and-workflows.md §11`); the standard face-pass and repair-inpaint partner for [`krea-2`](../krea-2/) scenes (~0.2 denoise `[community]`) | [`image-production-workflows`](../image-production-workflows/) for the cross-model craft itself |
| Making it move | Still images only | [`wan-2-2`](../wan-2-2/) — image-to-video. Wan's I2V path is much stronger than its text-to-video, so a still locked here (character LoRA + FaceDetailer included) is what actually controls the shot; the character work in `references/characters.md` is the upstream half of consistent characters in video |
| **Choosing between all of these in the first place** | — this table is one model's view of the suite | [`generative-media-atlas`](../generative-media-atlas/) — the whole suite ranked by job (realism, identity, LoRA trainability, control, licence, video), the elimination ladder that settles most choices, and end-to-end routes across several skills |

---

## Licence & limitations

**Licence:** Apache-2.0 for all currently released variants (Z-Image and Z-Image-Turbo). Z-Image-Edit and Z-Image-Omni-Base are still unreleased as of mid-2026 — both are marked "to be released" on the official GitHub. Verify their licences before use when they land.

**Release timeline:** Z-Image-Turbo shipped 26 Nov 2025, and the undistilled Z-Image base followed on 27 Jan 2026. This is a fast-moving family — re-verify volatile specifics (quant filenames, VRAM numbers, ComfyUI template details, LoRA tooling) before relying on them.

**VRAM for Z-Image (undistilled):** Tongyi-MAI has not published an inference VRAM figure. At 6B parameters in bfloat16, plus the shared encoder and VAE, **16 GB is the comfort band** — the point at which the weights stay resident and no offload tax is paid. 24 GB+ adds headroom for larger batches or resolutions. That number is inferred from the parameter count, not measured or published `[flagged — re-verify]`, and it is **not a floor**. An official int8 DiT (~6.2 GB) with its own ComfyUI template ships for base as well as Turbo, and Turbo is reported running on an RTX 2060 `[community — Royal_Carpenter_1338]`. Below the band you lose speed, not the model.

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** Architecture (6B S3-DiT, Qwen-3 4B encoder), the Apache-2.0 licence, exact filenames, node names (`ModelSamplingAuraFlow`, `EmptySD3LatentImage`, `LoraLoader` / `LoraLoaderModelOnly`, `QwenImageDiffsynthControlnet`), the CLIPLoader `lumina2` type, what a setting *numerically* does (CFG 1.0 = guidance-off = `guidance_scale=0`), the diffusers pipeline classes, the QKV / ComfyUI PR #12717 LoRA-loading fix. **Source of truth is official**: model card, ComfyUI template, ComfyUI PRs/issues, diffusers. That's where these are verified. A wrong filename 404s the download; a wrong node name won't wire. These are also the **volatile** ones. Filenames, VRAM figures, quant builds, tooling, and template details move week to week in this young family. **Re-verify before relying on them, regardless of who said it.**

**Craft — what actually makes a good image.** Sampler/CFG/denoise ladders, the multi-stage ZIB→ZIT pipeline numbers and the ×1.7/×2 upscale ladder, LoRA weights by type and stacking, the realism camera/film stack, the gaze anchors, the 8-point rotation phrasings. **The authoritative source here is the community**: named workflow authors (Mickmumpitz, WeirdWonderfulAI, MyAIForce, Khanykov01, neurocanvas, Cordina, rgthree) and reproducible Civitai/Reddit/Banodoco results that have run thousands of generations. *Not* the model card, which ships one example image and moves on. This is deep, battle-tested knowledge, not a lesser tier, and it's stated with confidence. Where a craft claim is given as a range or flagged "tune this," that's because **your weights, finetune, and resolution differ from the author's** — not because community sourcing is suspect. Where strong named sources genuinely disagree (exact LoRA weights; Base→Turbo transfer magnitude), the skill shows the disagreement rather than papering over it.

Contested and unresolved points, all greppable as markers:
- **Turbo negatives:** Tongyi-MAI states negatives are inert at the guidance-free setting (CFG 1.0 KSampler / `guidance_scale=0`). ComfyUI users report CFG 1.2–1.5 re-introduces weak negative subtraction. The official guidance is the fact; CFG > 1 on Turbo is a community workaround, not a supported feature `[contested]`.
- **LoRA cross-compat & weights:** loads-on-either-variant is a fact (shared S3-DiT); *clean transfer* and the exact per-type weights are contested craft `[contested]` — see `references/setup-and-workflows.md §6`.
- **Base VRAM:** the 16 GB figure above is inferred from the parameter count, not measured. Tongyi-MAI publishes none `[flagged — re-verify]`. Read it as a comfort band, not a requirement: every *measured* data point is a community one, and they run lower, down to quantised Turbo on an RTX 2060 `[community — Royal_Carpenter_1338]`.
- **Two further open flags live in the references**, both greppable there: no DiT block map exists for block-weighted LoRA application (`references/characters.md §6`), and the style-LoRA rank ceiling is agreed in direction but not in value (`references/lora-training.md §2.1`).

**Facts dated 2026-08-23.** What moves fastest in this family is the *plumbing*, not the craft: quant filenames, ComfyUI template contents, the AI-Toolkit Z-Image config, and the Fun ControlNet file names have all changed inside a release cycle before. Re-verify those against their repos before relying on them, regardless of who said it. The pipeline shapes and prompting craft in the references age far more slowly.

---

## Reference files

| File | When to read it |
|---|---|
| `references/prompting-guide.md` | 6-part prompt anatomy in full detail; realism vocabulary; camera vocabulary (8-point rotation, shot sizes, high/low angle); lighting vocabulary; bilingual text rendering; common mistakes; drop-in templates |
| `references/setup-and-workflows.md` | Multi-stage ComfyUI pipelines: the minimal build, the layered ZIB+ZIT pipeline with per-stage settings, resolution table, universal node settings (ModelSamplingAuraFlow / lumina2 / EmptySD3LatentImage), optional layers (skin contrast, SeedVR2, tiled upscale); **§6: Using LoRAs** (node wiring + `LoraLoaderModelOnly`, the QKV/PR #12717 silent-failure gotcha, weight-by-type, rgthree stacking, ZIB↔ZIT cross-compat, "fights distillation," ecosystem, and the character-via-detailer high-likeness method); **§9: Fun Union ControlNet** (V2.1 files, ModelPatchLoader + QwenImageDiffsynthControlnet nodes, all conditioning types and preprocessors, Turbo-only caveat); **§10: face identity methods** (LoRA, inpaint, IP-Adapter status); **§11: Z-Image in mixed-model pipelines** (the ZIT-as-refiner role, decode-to-pixels handoff rule, refine denoise bands) |
| `references/lora-training.md` | **Making** a LoRA on Z-Image specifically (loading/using is setup-and-workflows.md §6; the model-agnostic training craft is [`character-lora-training`](../character-lora-training/)): the train-on-Base/generate-on-Turbo decision and why, what changes about dataset building because the encoder is Qwen-3, **style-LoRA craft** (diverse-subject rule, prose captions, color-cast lock-in, the out-of-set acceptance test, rank-by-type), the Turbo training-adapter requirement and the de-turbo alternative, Ostris AI-Toolkit hyperparameters with the two knobs that make them readable, the RunPod fast path, the bucket/noise-sigma findings, adult-work coverage, and Z-Image-specific evaluation and debugging |
| `references/characters.md` | Creating a **consistent original character** end-to-end: the two paths (edit-model engine vs LoRA pipeline) and how they chain, the anchor image, the **Qwen-Image-Edit dataset factory** (2511 file table + ComfyUI wiring; generate ~60 → curate ~30; the multiple-angles coverage LoRA; where explicit material must be generated natively instead), rotation/elevation/expression coverage, the detailer-deploy step, **multi-outfit LoRAs** (~6-outfit ceiling), **multi-character scenes** (per-face detailer passes — no regional tooling exists), character failure modes (angle collapse, same-face overfit, expression lock-in, style bleed) |
