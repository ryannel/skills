# Qwen-Image — Setup & workflows

This file owns the plumbing and the graphs: every official template's files and numbers, the quantisation and VRAM ladders with their maintainers, diffusers per checkpoint, the Edit reference-path bypass node by node, ControlNet and model-patch wiring, the upscale and halftone chains, **using and stacking LoRAs**, the multi-stage ladder and the handoffs to other families. It does not own **making** a LoRA (`lora-training.md`) or the character protocol (`characters.md`). Hard facts were read from the template JSON, the Comfy-Org HF trees, the model cards and the diffusers source on 2026-09-09. Community craft is attributed inline.

## Contents

1. The templates — files and numbers
2. Quantisation & VRAM — the ladders and their maintainers
3. diffusers per checkpoint
4. Lightning — repos, versions, the fp8 grid
5. The Edit reference-path bypass, node by node
6. ControlNet, model patches, inpainting and Layered
7. Using LoRAs — loading, weights, cross-generation compatibility
8. Upscale, restoration and the halftone round trip
9. The multi-stage ladder
10. Qwen-Image in mixed-model pipelines

---

## 1. The templates — files and numbers

Source: `Comfy-Org/workflow_templates/templates/`. Every Qwen template samples with **`euler` / `simple` / denoise 1.0**. Steps and CFG are `PrimitiveInt` / `PrimitiveFloat` nodes routed through `ComfySwitchNode`s gated by a `PrimitiveBoolean` (`on_false` = base, `on_true` = Lightning), so the KSampler's own widgets are stale. The numbers below are the primitives.

**Shared by every template**, CLIPLoader type `qwen_image` on all of them: `qwen_2.5_vl_7b_fp8_scaled.safetensors` (9.38 GB, `text_encoders/`, `CLIPLoader ["…", "qwen_image", "default"]`) and `qwen_image_vae.safetensors` (0.25 GB, `vae/`), both from `Comfy-Org/Qwen-Image_ComfyUI`. The 2511 and Layered templates point the same encoder filename at `Comfy-Org/HunyuanVideo_1.5_repackaged`; either download is the same file.

| File | Size | `models/` folder | Loader node |
|---|---|---|---|
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` (**shared**) | 9.38 GB | `text_encoders/` | `CLIPLoader`, type **`qwen_image`** |
| `qwen_image_vae.safetensors` (**shared**, all but Layered) | 0.25 GB | `vae/` | `VAELoader` |
| `qwen_image_fp8_e4m3fn` / `qwen_image_2512_fp8_e4m3fn` / `qwen_image_edit_2509_fp8_e4m3fn` | 20.43 GB each | `diffusion_models/` | `UNETLoader` |
| `qwen_image_edit_2511_fp8mixed` (**no plain e4m3fn build exists**) | 20.53 GB | `diffusion_models/` | `UNETLoader` |
| `qwen_image_layered_bf16` + **`qwen_image_layered_vae`** | 40.86 + 0.25 GB | `diffusion_models/` + `vae/` | `UNETLoader` + `VAELoader` |
| Lightning LoRA for the *exact* variant | 0.2–1.6 GB | `loras/` | `LoraLoaderModelOnly`, strength 1 |

| Template (date) | Transformer | Lightning LoRA | Latent / input | Shift | Base | Lightning | Default | Notes |
|---|---|---|---|---|---|---|---|---|
| `image_qwen_image` (2025-08-05) | `qwen_image_fp8_e4m3fn` 20.43 GB | `Qwen-Image-Lightning-8steps-V1.0` | `EmptySD3LatentImage` 1328×1328 | 3.1 | 20 / 4.0 | 8 / 1.0 | base | two plain `CLIPTextEncode` |
| `image_qwen_image_edit` (2025-08-18) | `qwen_image_edit_fp8_e4m3fn` | `Qwen-Image-Edit-Lightning-4steps-V1.0-bf16` | `VAEEncode` ← `ImageScaleToTotalPixels ["lanczos", 1.5]` | 3.0 | 20 / 2.5 | 4 / 1.0 | base | two `TextEncodeQwenImageEdit`; `CFGNorm [1]`; no empty latent |
| `image_qwen_image_edit_2509` (2025-09-25) | `qwen_image_edit_2509_fp8_e4m3fn` | `Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16` (subfolder `Qwen-Image-Edit-2509/`) | `VAEEncode` ← `FluxKontextImageScale` | 3.0 | 20 / 4.0 | 4 / 1.0 | **Lightning** | `TextEncodeQwenImageEditPlus`; `CFGNorm [1, false]` |
| `image_qwen_image_edit_2511` (2025-12-23) | `qwen_image_edit_2511_fp8mixed` 20.53 GB | `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16` (own repo) | two `LoadImage` → `FluxKontextImageScale`; `FluxKontextMultiReferenceLatentMethod` `index_timestep_zero` on both conditionings | 3.1 | 40 / 4.0 | 4 / 1.0 | base | the graph counterpart of `zero_cond_t: true` |
| `image_qwen_image_edit_2511_int8` (2026-07-10) | `qwen_image_edit_2511_int8_convrot` 20.50 GB | same | same | 3.1 | 40 / 4.0 | 4 / 1.0 | base | identical graph |
| `image_qwen_Image_2512` (2025-12-31) | `qwen_image_2512_fp8_e4m3fn` | `Qwen-Image-2512-Lightning-4steps-V1.0-fp32` (own repo; the fp32 build) | `EmptySD3LatentImage` 1328×1328 | 3.1 | 50 / 4.0 | 4 / 1.0 | base | Chinese negative baked in |
| `image_qwen_image_2512_with_2steps_lora` (2026-01-30) | 2512 | `Wuli-Qwen-Image-2512-Turbo-LoRA-2steps-V1.0-bf16` (`Wuli-art/…`, third party) | same | 3.0 | — | **2 / 1.0** | LoRA only | `ConditioningZeroOut` drops the negative |
| `image_qwen_image_layered` (2025-12-22) | `qwen_image_layered_bf16` 40.86 GB (`fp8mixed` 20.53 exists) | — | `EmptyQwenImageLayeredLatentImage [640, 640, 2, 1]`; `ImageScaleToMaxDimension ["lanczos", 640]`; `LatentCut` / `LatentCutToBatch`; two `ReferenceLatent` | **1.0** | 20 / 2.5 | — | base | **`qwen_image_layered_vae.safetensors`**; "Text to Layers" subgraph muted |
| `image_qwen_image_layered_control` (2026-01-15) | `qwen_image_layered_control_bf16` from `DiffSynth-Studio/Qwen-Image-Layered-Control`, `UNETLoader` weight_dtype **`fp8_e4m3fn`** (the only Qwen template that sets it) | — | same | 1.0 | 20 / 2.5 | — | base | |

ControlNet and inpainting templates are in §6. Four numbers a reader gets wrong from priors. **Shift is not constant**: 3.1 for T2I, 2511 and 2512, 3.0 for 2508, 2509 and the 2-step turbo, 1.0 for Layered. **Base CFG is not constant**: 4.0 for T2I, 2509 and 2511, 2.5 for 2508 and the DiffSynth and InstantX-inpaint graphs. **Base steps climb** 20 → 40 (2511) → 50 (2512) to match the cards. **Lightning CFG is always exactly 1.0.**

**Version floor:** Edit-2511 needs ComfyUI ≥ 0.6.0. A LoRA author reports that an un-updated ComfyUI gives "completely distorted or ugly images" on 2511 `[community — NRDX, BFS card; single report]`. Update before debugging.

---

## 2. Quantisation & VRAM — the ladders and their maintainers

### 2.1 Official (Comfy-Org), sizes from the HF tree API

| Repo | File | Size |
|---|---|---|
| `Comfy-Org/Qwen-Image_ComfyUI` | `qwen_image_bf16` / `_fp8_e4m3fn` / `_fp8_hq` / `_fp8mixed` / `_nvfp4` | 40.86 / 20.43 / 22.74 / 20.53 / 19.77 GB |
| same | `qwen_image_2512_bf16` / `_fp8_e4m3fn` | 40.86 / 20.43 |
| same | `qwen_2.5_vl_7b` / `_fp8_scaled` / `_nvfp4` (encoder) | 16.58 / 9.38 / 6.11 |
| `Comfy-Org/Qwen-Image-Edit_ComfyUI` | `qwen_image_edit_bf16` / `_fp8_e4m3fn`; `_2509_bf16` / `_2509_fp8_e4m3fn` / `_2509_fp8mixed` | 40.86 / 20.43; 40.86 / 20.43 / 20.53 |
| same | `qwen_image_edit_2511_bf16` / `_fp8mixed` / `_int8_convrot` | 40.86 / 20.53 / 20.50 |
| `Comfy-Org/Qwen-Image-Layered_ComfyUI` | `qwen_image_layered_bf16` / `_fp8mixed`; `qwen_image_layered_vae` | 40.86 / 20.53; 0.25 |

Reading the ladder. **`fp8_e4m3fn`** is the template default for base, 2508, 2509 and 2512, and it is the file the Lightning maintainers mark as broken under a bf16 LoRA (§4). **`fp8mixed`** is what 2511 and Layered default to; 2511 has no plain e4m3fn build at all. **`int8_convrot`** is 2511-only with its own template, not smaller than fp8, and pitched by the template index as "faster inference while maintaining high quality". **`nvfp4`** and **`fp8_hq`** exist for base T2I only, and no template selects either. What the mixed-precision split and "convrot" actually are goes undocumented, and nvfp4 is a Blackwell format that pre-50-series cards should not expect to load `[flagged — re-verify]`. `qwen_image_distill_full_{bf16,fp8_e4m3fn}` (DiffSynth's full distillation, under `non_official/`) runs at 15 or 10 steps, CFG 1.0 per docs.comfy.org.

**musubi-tuner rejects the fp8 repacks for training** (`fp8_scaled` encoder, `fp8_e4m3fn` Edit DiT, `fp8mixed` Layered DiT). Download bf16 if you will train (`lora-training.md §1`).

### 2.2 GGUF — get the maintainer right

| Generation | Repo | Pulls / 30 d |
|---|---|---|
| Qwen-Image | `city96/Qwen-Image-gguf` (2025-08-05) | 50k |
| Edit, Edit-2509 | `QuantStack/Qwen-Image-Edit-GGUF`, `-2509-GGUF` | 203k (2509) |
| **Edit-2511** | **`unsloth/Qwen-Image-Edit-2511-GGUF`** (2025-12-20) | 282k |
| 2512 | ByteShape re-quantisation (8–17 GB) and others | — |

QuantStack shipped nothing for 2511 or 2512. GGUF DiTs load through the `ComfyUI-GGUF` custom node, not `UNETLoader`. A guide that says "get the QuantStack GGUF" for 2511 is a generation out of date `[flagged — re-verify]`.

**The quality ladder is contested at the low end.** One author: "always use FP8 if you can… only use Q6 and lower if you absolutely have to" `[community — nsfwVariant]`. A 6 GB operator reports a different curve: "Q4 and above is good, I did not see much difference between Q4–Q8" `[community — gebba, r/StableDiffusion 1obg25u]`. One is chasing a ceiling and one a floor. Both can be right (SKILL.md two-bar section).

### 2.3 Nunchaku SVDQuant — stopped at 2509

The org renamed `nunchaku-tech` → `nunchaku-ai`, so older links are stale. Official builds: `nunchaku-qwen-image` (2025-08-14), `nunchaku-qwen-image-edit` (2025-09-10, 65k pulls), `nunchaku-qwen-image-edit-2509` (2025-09-24, with 4- and 8-step **Lightning-fused** int4). **All three stopped updating on 2025-11-16.** There is no official build for 2511, 2512 or Layered; third parties fill the gap with little traction `[flagged — re-verify]`.

The fused 2509 build "runs smoothly even on 8 GB VRAM + 16 GB RAM (just tweak `num_blocks_on_gpu` and `use_pin_memory`)" `[official — Nunchaku team]`. Measured: 4-step SVDQuant Edit in ~30 s on a 4060 Ti, at no noticed quality loss `[community — infearia, Epictetito]`. Two gotchas from the same thread. Stacking a separate Lightning LoRA on the already-fused build gives a **black image**; the fix was no extra launch flags, and a reboot. And only some LoRAs work with the Nunchaku LoRA loader node. The `ComfyUI-nunchaku` pack has its own loader and LoRA nodes.

### 2.4 Merged AIO checkpoints

`Phr00t/Qwen-Image-Edit-Rapid-AIO` v17/v18 merges 2509 and 2511 "with the goal of correcting contrast issues and LORA compatibility with 2511 while maintaining character consistency", bundling a speed LoRA and the VAE. It needs `ModelSamplingAuraFlow`, `CFGNorm` and the `Edit Model Reference Method` node; `euler_ancestral` / `beta` is "highly recommended" `[community — Phr00t via fruesome, r/StableDiffusion 1pw3t5t]`. NSFW/SFW splits ship separately. Civitai's leading third-party checkpoint is **Jib Mix Qwen** (J1B) with a companion skin-detailer LoRA. Merges inherit none of the stock numbers' guarantees.

### 2.5 VRAM thresholds

No official inference figure exists. These are synthesised from named reports.

| VRAM | Path | Source |
|---|---|---|
| **6 GB** + 32 GB RAM | Edit-2509 Q8 GGUF at 1024², 4-step Lightning, 90–120 s/image in SwarmUI — Q8 on 6 GB via offload, so "GGUF ≤ VRAM" is not the rule | `[community — gebba]` |
| **8 GB** + 16 GB RAM | Nunchaku int4 fused-Lightning 2509; or Q4_K_M 2512 at 8 steps under 40 s | `[official — Nunchaku]`, `[community — Puzzled-Valuable-985; single report]` |
| **12 GB** | Q5–Q6 GGUF or Nunchaku int4; system RAM is the binding constraint for Krita and Invoke front ends | `[community — slickyfatgrease; single report]` |
| **16 GB** | Q8 GGUF, or fp8 with block swap; 8-step Lightning to iterate | inferred |
| **24 GB+** | fp8 native, 20–30 steps, no Lightning, double-ref on | `[community — nsfwVariant]` |
| **32 GB** (5090) | everything, including 2–3 MP double-ref edits at 91–131 s | same |

**You do not need 24 GB of VRAM for the 20 GB fp8 build.** ComfyUI streams blocks from host RAM, and ~26 GB *combined* is the working figure. Speed at fixed seeds on a 4090: bf16 at 50 steps and CFG 4.0 takes 369 s, fp8 at 20 steps and CFG 2.5 takes 77 s, and fp8 with Lightning at 4 steps takes 19 s. The fp8-vs-bf16 gap is "much smaller" than the Lightning gap, but bf16 is "noticeably better" and holds input colour closer `[community — FluffyQuack, r/StableDiffusion 1nravcc]`. InvokeAI 6.13 is the only non-ComfyUI front end with first-class Qwen support.

---

## 3. diffusers per checkpoint

Ten pipeline classes ship in `diffusers/pipelines/qwenimage/`. Version floors by tag inspection; the cards' `pip install git+…` line is launch-day legacy.

| Checkpoint | `model_index.json` class | Minimum diffusers |
|---|---|---|
| `Qwen/Qwen-Image`, `Qwen-Image-2512` | `QwenImagePipeline` | 0.35.0 (2025-08-19) |
| `Qwen/Qwen-Image-Edit` | `QwenImageEditPipeline` | 0.35.0 |
| `Qwen/Qwen-Image-Edit-2509`, `-2511` | **`QwenImageEditPlusPipeline`** | 0.36.0 (2025-12-08) |
| `Qwen/Qwen-Image-Layered` | `QwenImageLayeredPipeline` | 0.37.0 (2026-03-05); needs `transformers>=4.51.3` and `python-pptx` |
| — | `QwenImageImg2ImgPipeline`, `QwenImageInpaintPipeline` | 0.35.0 |
| — | `QwenImageEditInpaintPipeline`, `QwenImageControlNetPipeline`, `QwenImageControlNetInpaintPipeline` | 0.36.0 |

Latest release as of 2026-09-09: 0.40.0. The minimal call, which the cards vary only by class, inputs and steps:

```python
# pip install "diffusers>=0.36.0"   (0.35.0 for base/Edit; 0.37.0 for Layered; latest 0.40.0)
from diffusers import QwenImagePipeline, QwenImageEditPlusPipeline
pipe = QwenImagePipeline.from_pretrained("Qwen/Qwen-Image", torch_dtype=torch.bfloat16).to("cuda")
img = pipe(prompt, negative_prompt=" ", num_inference_steps=50, true_cfg_scale=4.0).images[0]
```

Card parameters, verbatim:

| Checkpoint | `num_inference_steps` | `true_cfg_scale` | `negative_prompt` | Other |
|---|---|---|---|---|
| Qwen-Image, Edit | 50 | 4.0 | `" "` | `torch.bfloat16` |
| Edit-2509, Edit-2511 | 40 | 4.0 | `" "` | `guidance_scale=1.0` (inert), `image=[img1, img2]` |
| Qwen-Image-2512 | 50 | 4.0 | the Chinese negative | |
| Layered | 50 | 4.0 | `" "` | `layers=4`, `resolution=640` ("640 is recommended"), `cfg_normalize=True`, `use_en_prompt=True` |

`true_cfg_scale` is the real CFG knob because `guidance_embeds` is false; `guidance_scale` is passed and ignored. **musubi-tuner does not export diffusers keys** (issue #442, open), so a musubi LoRA loads in ComfyUI and not through `load_lora_weights()` (`lora-training.md §1.4`).

---

## 4. Lightning — repos, versions, the fp8 grid

Author: the LightX2V / ModelTC team, not Qwen. It counts as official surface because Comfy-Org's templates load it directly. Code: `ModelTC/Qwen-Image-Lightning`. Weights across three HF repos `[official — Lightning README, 2026-09-09]`:

| Base | Repo | Files |
|---|---|---|
| Qwen-Image | `lightx2v/Qwen-Image-Lightning` | 8-step V1.0 / V1.1 / V2.0, 4-step V1.0 / V2.0 (fp32 + bf16); the scaled fp8 base `Qwen-Image/qwen_image_fp8_e4m3fn_scaled.safetensors`; the fp8-distilled `Qwen-Image-fp8-e4m3fn-Lightning-4steps-V1.0-fp32` |
| Edit (2508) | same | `Qwen-Image-Edit-Lightning-4steps` / `8steps-V1.0` |
| Edit-2509 | same, subfolder `Qwen-Image-Edit-2509/` | 4-step and 8-step V1.0 (fp32 + bf16) |
| Edit-2511 | `lightx2v/Qwen-Image-Edit-2511-Lightning` | 4-step V1.0 (fp32 + bf16) **and a fused fp8 model** |
| 2512 | `lightx2v/Qwen-Image-2512-Lightning` | 4-step V1.0 (fp32 + bf16) |

Recommended: `--steps 8 --cfg 1.0` or `--steps 4 --cfg 1.0` with the matching LoRA, and `--steps 50 --cfg 4.0` on the base. **V2.0** "produces images with reduced over-saturation, resulting in improved skin texture"; the base template still ships V1.0 8-step. The maintainers' own limits: the base wins on dense or small text, and hair-like detail comes out "either noticeably blurred or excessively sharpened".

**The fp8 grid.** `qwen_image_fp8_e4m3fn.safetensors` "was produced by directly downcasting the original bf16 weights, rather than employing a calibrated conversion process with appropriate scaling", so a Lightning LoRA on it produces "grid artifacts" `[official — Lightning README, issue #32]`:

| Base + LoRA | Correct? |
|---|---|
| bf16 base + bf16-trained LoRA | yes |
| `qwen_image_fp8_e4m3fn` + bf16-trained LoRA | **no — grid** |
| `qwen_image_fp8_e4m3fn` + the LoRA distilled on the fp8 base | yes |
| `qwen_image_fp8_e4m3fn_scaled` (Lightning repo) + bf16-trained LoRA | yes |

The stock `image_qwen_image` template is the second row. Whether ComfyUI patched fp8 handling internally is unstated by Comfy-Org `[flagged — re-verify]`. This is a base-quantisation × LoRA interaction, so it applies to any LoRA on that file, including yours.

**Version skew is the other Lightning failure.** A LoRA from a different generation either no-ops (returns the input in 0.01 s) or produces garbage; 2509 with the old Edit Lightning was fixed by the non-Edit `Qwen-Image-Lightning-4steps-V2.0` `[community — imkloon, Caco-Strogg-9; single reports]`. And 2511's own 4-step LoRA is reported to produce **blocky artefacts** that 2509's does not, across samplers and 8–24 steps `[community — MastMaithun]`. Another author reports the 8-step 2511 LoRA *fixing* the 4-step's pixel drift `[community — DrinksAtTheSpaceBar]` `[contested]`. Practical order: the 2509 Lightning on 2511, then the 8-step 2511, then none.

---

## 5. The Edit reference-path bypass, node by node

SKILL.md states the problem: `TextEncodeQwenImageEditPlus` force-downscales to 1,048,576 px with AREA resampling and rounds to 8. This is the graph that avoids it, from the two authors who found the fix independently `[community — nsfwVariant, danamir_; convergent]`.

**Stock 2509/2511 path:**

```
LoadImage → FluxKontextImageScale → TextEncodeQwenImageEditPlus (clip, vae, image_1..3) → conditioning
                                 └→ VAEEncode → KSampler.latent_image
```

**Bypass path:**

```
LoadImage → ImageScale (lanczos, W×H multiple of 16, 2–3 MP) ─┬→ VAEEncode → ReferenceLatent (conditioning in) ─┐
                                                              └→ VAEEncode → KSampler.latent_image              │
CLIPTextEncode ("Picture 1: <five words>. <instruction>") ──────────────────────────────────────────────────────┘
```

1. **Leave the VAE input on `TextEncodeQwenImageEditPlus` empty, or replace the node with `CLIPTextEncode`.** "The forced 1 Mp resolution scale can be skipped if the VAE input is not filled." With the VL image stage gone, you write the `Picture N:` labels yourself (`prompting-guide.md §3`).
2. **Scale with Lanczos, to a multiple of 16.** ComfyUI rounds to 8, the patchifier wants 16, and the mismatch causes "major ruination along the whole edge of your image".
3. **One `ReferenceLatent` per source, chained.** Multi-image: VAE-encode each reference and chain the nodes into the positive conditioning.
4. **Double-ref for single-image edits.** Feed the reference in twice. It improves prompt adherence, sharpness, texture consistency and off-angle likeness at ~50% more time, and is "ALWAYS better" for single-image. It sometimes confuses multi-image, so toggle it.
5. **Keep the author's positive/negative conditioning layout** (references plus a zeroed-out positive fed into the negative). It was chosen from a sixteen-way A/B and should not be improvised.
6. **`CFGNorm` stays** on the model path, as in every Edit template.

Measured on a 5090, Edit-2511, double-ref on: 52 s at 1024², 131 s at 1920×1088, 550 s at 3072×1728. Cost is non-linear (1→2 MP ≈ 2.5×, 1→3 MP ≈ 4×). Anatomy starts failing above ~3 MP; simple in-place edits go far higher. **Working band: 2–3 MP single-image, 1–2 MP multi-image.** Edits land pixel-perfect at native size; a 1852×1440 edit that flicker-matches its source is the published demonstration.

musubi-tuner's inference script has the opposite flag, `--resize_control_to_official_size`: "1M pixels keeping aspect ratio… recommended for better results with Edit models (mandatory for 2511)" `[official — musubi docs]`. That is the official size. The ComfyUI finding is about AREA resampling and the rounding, not about 1 MP itself, and both are true of their own pipelines.

---

## 6. ControlNet, model patches, inpainting and Layered

Five official templates, three loader mechanisms. All apply nodes ship at **strength 1, start 0, end 1**.

| Template (date) | Control file | Folder | Loader → apply | Input scaling | Base / Lightning |
|---|---|---|---|---|---|
| `image_qwen_image_instantx_controlnet` (2025-08-23) | `Qwen-Image-InstantX-ControlNet-Union` (3.54 GB) | `controlnet/` | `ControlNetLoader` → `ControlNetApplyAdvanced` | `FluxKontextImageScale` | 4 / 1.0 hardwired Lightning |
| `image_qwen_image_instantx_inpainting_controlnet` (2025-09-12) | `Qwen-Image-InstantX-ControlNet-Inpainting` (4.23 GB) | `controlnet/` | `ControlNetLoader` → **`ControlNetInpaintingAliMamaApply`** | `ImageScaleToMaxDimension ["area", 1536]`; `SetLatentNoiseMask`; `GrowMask [20, true]` → `ImageBlur [31, 1]` → `ImageCompositeMasked` | 20 / 2.5; Lightning muted |
| `image_qwen_image_union_control_lora` (2025-08-23) | `qwen_image_union_diffsynth_lora` (0.94 GB) | `loras/` | `LoraLoaderModelOnly` + two `ReferenceLatent` | `ImageScaleToTotalPixels ["lanczos", 1]`; `Canny [0.26, 0.35]` | 20 / 2.5 |
| `image_qwen_image_controlnet_patch` (2025-08-24) | `qwen_image_canny_diffsynth_controlnet` (2.27 GB; `_depth_`, `_inpaint_` siblings) | **`model_patches/`** | **`ModelPatchLoader` → `QwenImageDiffsynthControlnet`** (`model`, `model_patch`, `vae`, `image`, `mask`) | `ImageScaleToTotalPixels ["area", 1.68]`; `Canny [0.1, 0.2]` | 20 / 2.5 |
| `image_qwen_Image_2512_controlnet` (2026-02-16) | `Qwen-Image-2512-Fun-Controlnet-Union-2602` (Alibaba PAI) | `controlnet/` | `ControlNetLoader` → `ControlNetApplyAdvanced` | scale total pixels 1.6, area; `Canny [0.33, 0.35]` | 50 / 4.0 |

Repos: `Comfy-Org/Qwen-Image-InstantX-ControlNets`, `Comfy-Org/Qwen-Image-DiffSynth-ControlNets` (`split_files/model_patches/` plus the union LoRA), `alibaba-pai/Qwen-Image-2512-Fun-Controlnet-Union`. The `ModelPatchLoader` → `QwenImageDiffsynthControlnet` pair is the mechanism [`z-image`](../../z-image/) uses for its Fun Union ControlNet; the node name says Qwen because it started here.

**What people actually use.** The native ControlNet inside Edit-2509+ (depth, edge, keypoint), at strength 0.9 in a published head-swap pipeline `[community — Substantial_Angle680]`. And InstantX Union for T2I at `controlnet_conditioning_scale` 0.8–1.0, trained 50k steps at 1328×1328. Its card warns that small-font text is lost unless named in the prompt `[official — InstantX card]`. **DiffSynth EliGen** and **Blockwise-ControlNet** show zero monthly downloads across every repo. One report says depth-driven Edit only behaves with Lightning loaded, "very weird" without, at any step count `[community — SlowDisplay; single report]`; it contradicts the majority Lightning view and has no mechanism.

**Layered** is trainable (musubi `--model_version layered`, `multiple_target = true`, `--remove_first_image_from_target`; DiffSynth) and adopted, and no settings-level write-up exists. The template numbers in §1 are the whole published surface.

---

## 7. Using LoRAs — loading, weights, cross-generation compatibility

- **Node:** `LoraLoaderModelOnly` on the model path, before `ModelSamplingAuraFlow`. Qwen LoRAs never touch the encoder. Lightning stacks in the same chain at strength 1.
- **Weights:** realism LoRAs at **1.0**, and SamsungCam UltraReal stacks with character LoRAs `[community — FortranUA]`. Style LoRAs go per card: PanelPainter 0.45–0.6, a folk-horror style 0.8–1.2 with Lightning. The Multiple-Angles LoRA runs 0.8–1.0 `[community — Proper-Employment263, fal]`.
- **Cross-generation — the rule behind every "key mismatch" report.** T2I LoRAs often load on Edit and sometimes work: "you'll need to test them individually" `[community — nsfwVariant]`. 2512 ↔ 2511 "works but is not perfect; a dedicated training for each version will always give you better results" `[community — FarTable6206]`. **2511 and 2512 folded popular community LoRAs into the base**, so an older LoRA double-applies: "any LoRA destroys the image on 2512", and lowering strength does not fix it `[community — Friendly-Fig-6015; single report]`. The community answered with `-2511` retrains and the Rapid-AIO merge (§2.4). Read the generation on the card before the weight.
- **Format:** diffusion-pipe emits ComfyUI keys by design. musubi emits sd-scripts keys that ComfyUI loads. ai-toolkit emits diffusers-style PEFT keys that named authors ship and load in ComfyUI. The mismatch to expect is musubi → diffusers `load_lora_weights()` (`lora-training.md §1.4`).
- **Stacking:** Qwen tolerated three stacked LoRAs where Z-Image Turbo managed two, and its concept bleed is milder `[community — Top_Buffalo1668]`. 2512 collapses with 2–3 LoRAs. Nunchaku's loader accepts only some (§2.3).
- **Official Edit-2509 LoRAs** in `Comfy-Org/Qwen-Image-Edit_ComfyUI/split_files/loras/`: `Relight`, `Multiple-angles`, `Fusion`, `Light-Migration`, `White_to_Scene` (0.24 GB each), `Anything2RealAlpha` (0.61 GB).

---

## 8. Upscale, restoration and the halftone round trip

1. **Artefact removal first.** The Qwen VAE "will often put a subtle halftone grid pattern over your images… more noticeable at higher resolutions… particularly present with the Edit model" `[community — nsfwVariant]`. Downscale to 0.5–0.75×, then re-upscale: SeedVR2 removes it; `4x Nomos2 HQ DAT2` after a modest downscale (1920p → 1600p) reduces it. Z-Image and Krea 2 share this VAE family, so the trick may apply there (inference, untested).
2. **Qwen as the upscaler.** `vafipas663/Qwen-Edit-2509-Upscale-LoRA`. Prompt `"Enhance image quality"` plus a scene description, 8-step Lightning, ~40 s on an L4. **`ModelSamplingAuraFlow` shift below 0.3, down to 0.02 at high resolution.** Sampler LCM best, then `euler_ancestral`, then `euler`. It was trained on Unsplash-Lite + UltraHR-100K to recover from 16× downscale, noise, blur and JPEG artefacts `[community — vafipas663, r/StableDiffusion 1ormgsm]`. That shift figure is two orders below the template's 3.1, and one T2I report uses 57. **Shift is parameterised differently across graphs. Never carry a value between workflows.**
3. **Others in circulation:** `starsfriday/Qwen-Image-Edit-2511-Upscale2K` (18k monthly pulls), `prithivMLmods/Unblur-Upscale` for 2511.

---

## 9. The multi-stage ladder

Qwen's ladder is short because the edit model does what detailers and inpaint do elsewhere, at native 2–3 MP.

| # | Stage | Model | Settings | Purpose |
|---|---|---|---|---|
| 1 | Compose | Qwen-Image / 2512 | 20–50 steps, CFG 4.0, 1328-class size; or Lightning 4–8 / 1.0 for drafts | layout; reroll freely |
| 2 | Edit passes | Edit-2511 (or 2509 for LoRA reach) | bypass path (§5), 20–30 steps CFG 4.0, double-ref, one instruction each, **re-anchored on the original** | every subsequent shot, outfit, relight, angle |
| 3 | Halftone round trip | — | 0.5–0.75× down, re-up | decode artefact |
| 4 | Detailer | any base + character LoRA | FaceDetailer; swap the LoRA in here | distant faces, needed more often than on Z-Image |
| 5 | Upscale | Edit + Upscale LoRA, or SeedVR2 | §8 | final size |

Every stage after 1 is bypassable. **There is no denoise ladder for Qwen img2img and inpaint.** The community's answer to img2img is the Edit model, which has no denoise dial. What exists: the `Qwen Image Edit Easy Inpaint LoRA` (`_Envy_`), the InstantX inpainting template (§6), and one head-swap pipeline with numbers. That pipeline runs Edit + 4-step Lightning, auto face detect and mask, ControlNet 0.9, and a SeedVR2 final `[community — Substantial_Angle680, 1p8phet]`. A denoise ladder must be measured, not cited. Renting the GPU: [`comfyui-on-runpod`](../../comfyui-on-runpod/).

---

## 10. Qwen-Image in mixed-model pipelines

Qwen-Image-Edit has one role the rest of the suite already depends on: **the edit engine and dataset factory for other families' stills.** [`z-image`](../../z-image/)'s and [`krea-2`](../../krea-2/)'s character references send an anchor image here to be multiplied into a LoRA set. One headshot becomes 20 angle variants in ~130 s on a 5090 (Edit-2509 fp8 + 4-step Lightning) `[community — acekiube]`. The edit model never touches their inference, so its plastic default does not contaminate the trained LoRA.

The reverse handoff is **Z-Image as the realism finisher** for a Qwen composition. Qwen's skin is "still a bit plastic" where "ZIT is clearly superior in terms of realism" `[community — Top_Buffalo1668]`. Compose and edit here, decode, and run the face or skin pass there at denoise ~0.2–0.35.

The rules between families are the suite's. **Decode to pixels between VAE families**: Qwen's latent is not Z-Image's (Flux.1 VAE) or SDXL's. Krea 2 and Wan 2.2 *are* the same VAE family, but decode anyway unless you have verified the latent scale factors match. **Identity-preserving refines live at denoise ~0.2–0.5.** **Match resolution** to the receiving model's band before encoding. Cross-model craft in depth is [`image-production-workflows`](../../image-production-workflows/). The still that goes to video is built here: compose on T2I, give it angles and outfits on Edit, then hand the frame to [`wan-2-2`](../../wan-2-2/).
