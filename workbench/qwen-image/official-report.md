# Qwen-Image family — hard facts from primary sources

Research slice: **official artefacts only** (template JSON, Comfy-Org repackaged repos, HF model cards,
QwenLM GitHub, diffusers, vendor docs, trainer repos). Craft and community evidence are another agent's slice.

Compiled **2026-09-09**. Every claim carries a URL. Tags:
`[official — <artefact>]` = read directly from the named primary artefact;
`[official-via-docs]` = stated on an official docs/blog page rather than in code or a model card;
`[flagged]` = my inference or a gap, not a source claim.

---

## 1. Variants and release timeline

### 1.1 The open weights

| Variant | HF repo | Released | What it is | Licence |
|---|---|---|---|---|
| **Qwen-Image** (T2I base) | [`Qwen/Qwen-Image`](https://huggingface.co/Qwen/Qwen-Image) | 2025-08-04 | 20B MMDiT text-to-image foundation model; the family root | Apache 2.0 |
| **Qwen-Image-Edit** (a.k.a. 2508) | [`Qwen/Qwen-Image-Edit`](https://huggingface.co/Qwen/Qwen-Image-Edit) | 2025-08-18 | Instruction image edit built on the 20B base; single input image | Apache 2.0 |
| **Qwen-Image-Edit-2509** | [`Qwen/Qwen-Image-Edit-2509`](https://huggingface.co/Qwen/Qwen-Image-Edit-2509) | 2025-09-22 | Multi-image editing (1–3 inputs), better person/product/text consistency, native ControlNet | Apache 2.0 |
| **Qwen-Image-Layered** | [`Qwen/Qwen-Image-Layered`](https://huggingface.co/Qwen/Qwen-Image-Layered) | 2025-12-19 | Decomposes an image into N RGBA layers; variable layer count, recursive | Apache 2.0 |
| **Qwen-Image-Edit-2511** | [`Qwen/Qwen-Image-Edit-2511`](https://huggingface.co/Qwen/Qwen-Image-Edit-2511) | 2025-12-23 | Drift mitigation, character consistency, community LoRAs folded into the base, industrial design, geometric reasoning | Apache 2.0 |
| **Qwen-Image-2512** (T2I refresh) | [`Qwen/Qwen-Image-2512`](https://huggingface.co/Qwen/Qwen-Image-2512) | 2025-12-31 | December T2I update: human realism, natural detail, text rendering | Apache 2.0 |
| **Qwen-Image-Lightning** LoRAs | [`lightx2v/Qwen-Image-Lightning`](https://huggingface.co/lightx2v/Qwen-Image-Lightning) and per-variant repos | 2025-08 onward | 4/8-step (and 2-step community) step-distillation LoRAs, one per base variant | see §7 |

`[official — HF model cards, YAML `license: apache-2.0` on every one of the six Qwen repos above]`

Those dates are the Qwen team's own, from the News block of the GitHub README
(`https://github.com/QwenLM/Qwen-Image` — 2025.08.04 Qwen-Image; 2025.08.18 Edit; 2025.09.22 Edit-2509;
2025.12.19 Layered; 2025.12.23 Edit-2511; 2025.12.31 Qwen-Image-2512) and corroborated by the roadmap slide
prompt inside the Qwen-Image-2512 model card, which additionally dates project start to 2025年5月6日.
`[official — QwenLM/Qwen-Image README News; Qwen/Qwen-Image-2512 README showcase prompt]`
ComfyUI template `date` fields agree within days. `[official — templates/index.json]`
Papers: Qwen-Image tech report **arXiv 2508.02324** (2025-08-04); Qwen-Image-Layered **arXiv 2512.15603**.

### 1.2 What is *not* open

**Qwen-Image 3.0 / `qwen-image-3.0-pro` is closed.** As of 2026-09-09 there is **no `Qwen/Qwen-Image-3`
weights repo on Hugging Face**; the only first-party surface ComfyUI exposes for it is an **API node**, not a
loader. Comfy-Org shipped two API templates on **2026-08-06** — `api_qwen3_t2i.json`
("Qwen Image 3.0 Pro: Text to Image") and `api_qwen3_image_edit.json` ("Qwen Image 3.0 Pro: Image Edit") —
whose nodes are `QwenImageTextToImageApi` and `QwenImageEditApi`, both with the model string
`"qwen-image-3.0-pro"`. An API node means a remote call to Alibaba's hosted service; every open variant in
§1.1 instead gets a `UNETLoader` + local `.safetensors`.
`[official — templates/index.json entries, and templates/api_qwen3_t2i.json / api_qwen3_image_edit.json]`

**Qwen-Image-2.0 is closed too**, and this corrects the commissioning brief. The QwenLM README's News block
announces it on **2026.02.10** — *"a next-generation foundational image generation model"* with
*"Native 2K resolution"*, *"1k-token instructions"* and a *"Lighter Model Architecture — Smaller model size
with faster inference speed"*, linking `https://qwen.ai/blog?id=qwen-image-2.0` — but **no `Qwen/Qwen-Image-2.0`
repo exists on Hugging Face**. Alibaba's hosted model list carries `qwen-image-2.0` and `qwen-image-2.0-pro`
with dated snapshots. `[official — https://github.com/QwenLM/Qwen-Image README News;
https://huggingface.co/api/models?author=Qwen returns only the six open image repos plus `Qwen-Image-Bench`]`

So the open/closed line falls after **Qwen-Image-2512 / Qwen-Image-Edit-2511 (December 2025)**: everything up
to and including those is Apache-2.0 open weights; **Qwen-Image-2.0 (2026-02) and 3.0 (2026-07/08) are both
hosted-only.** `[flagged: "closed" means "no downloadable weights as of 2026-09-09" — no Qwen statement says
they never will be, and the family's history makes a later drop plausible.]`

---

## 2. Architecture and encoders

### 2.1 The transformer

Every open variant in the family — base, all three Edit generations, 2512 and Layered — uses the **same
`QwenImageTransformer2DModel` geometry**, verbatim from `transformer/config.json`:

| Field | Value | Same across variants? |
|---|---|---|
| `_class_name` | `QwenImageTransformer2DModel` | yes |
| `num_layers` | `60` | yes |
| `num_attention_heads` | `24` | yes |
| `attention_head_dim` | `128` | yes (24 × 128 = 3072 hidden) |
| `joint_attention_dim` | `3584` | yes — matches the Qwen2.5-VL hidden size |
| `in_channels` | `64` | yes |
| `out_channels` | `16` | yes (16-channel latent) |
| `patch_size` | `2` | yes |
| `axes_dims_rope` | `[16, 56, 56]` | yes |
| `guidance_embeds` | `false` | **yes — no distilled guidance embedding on any variant** |

`[official — https://huggingface.co/Qwen/Qwen-Image/raw/main/transformer/config.json and the same path on
`Qwen-Image-Edit`, `-Edit-2509`, `-Edit-2511`, `-2512`, `-Layered`]`

`guidance_embeds: false` on **every** variant is the most load-bearing architecture fact: Qwen-Image is a
**true-CFG model, not a guidance-distilled one** — hence `true_cfg_scale` in the cards, and a live negative
prompt. Two variants add flags that each explain a piece of the ComfyUI graph: **Edit-2511** adds
`"zero_cond_t": true` (matched by `FluxKontextMultiReferenceLatentMethod = "index_timestep_zero"` in its
template), and **Layered** adds `"use_additional_t_cond": true`, `"use_layer3d_rope": true`,
`"zero_cond_t": false` (hence `EmptyQwenImageLayeredLatentImage`, `LatentCut`, `LatentCutToBatch` — the layer
axis is a third RoPE axis and layers come back as a batch to cut).
`[official — the two transformer configs + their templates]`

Parameter count: the team's own wording is **"our 20B Qwen-Image model"**, ComfyUI's template descriptions say
"20B MMDiT", and the bf16 repackage is **40.86 GB** ≈ 20.4B params at 2 bytes.
`[official — Qwen/Qwen-Image-Edit README; Comfy-Org/Qwen-Image_ComfyUI file sizes]`

### 2.2 Text encoder

**Qwen2.5-VL 7B**, used as *both* the text encoder and (for the Edit variants) the image-semantics encoder.

- `model_index.json` → `"text_encoder": ["transformers", "Qwen2_5_VLForConditionalGeneration"]`,
  `"tokenizer": ["transformers", "Qwen2Tokenizer"]`. `[official — Qwen/Qwen-Image/model_index.json]`
- `text_encoder/config.json` → `model_type: qwen2_5_vl`, `hidden_size: 3584`, `num_hidden_layers: 28`,
  `torch_dtype: bfloat16` — the 7B Qwen2.5-VL. Layered also declares
  `"processor": ["transformers", "Qwen2VLProcessor"]` and requires **transformers>=4.51.3**.
  `[official — Qwen/Qwen-Image text_encoder/config.json; Qwen/Qwen-Image-Layered model_index.json + README]`

The Edit mechanism in the team's own words: *"Qwen-Image-Edit simultaneously feeds the input image into
Qwen2.5-VL (for visual semantic control) and the VAE Encoder (for visual appearance control), achieving
capabilities in both semantic and appearance editing."* `[official — Qwen/Qwen-Image-Edit README]` In ComfyUI
that dual path is `TextEncodeQwenImageEdit` (image → VL encoder) plus a separate `VAEEncode` feeding
`latent_image`. `[official — templates/image_qwen_image_edit.json]`

### 2.3 VAE — and the Wan 2.1 question

The Qwen-Image VAE is `AutoencoderKLQwenImage`, and its config is **hyperparameter-identical to Wan 2.1's
`AutoencoderKLWan`**:

| Field | Qwen-Image | Wan2.1-T2V-14B-Diffusers |
|---|---|---|
| `_class_name` | `AutoencoderKLQwenImage` | `AutoencoderKLWan` |
| `base_dim` | 96 | 96 |
| `dim_mult` | `[1, 2, 4, 4]` | `[1, 2, 4, 4]` |
| `z_dim` | 16 | 16 |
| `num_res_blocks` | 2 | 2 |
| `attn_scales` | `[]` | `[]` |
| `temperal_downsample` | `[false, true, true]` | `[false, true, true]` |

`[official — https://huggingface.co/Qwen/Qwen-Image/raw/main/vae/config.json vs
https://huggingface.co/Wan-AI/Wan2.1-T2V-14B-Diffusers/raw/main/vae/config.json]`

So: **Qwen-Image uses a Wan-2.1-family video VAE architecture** (note `temperal_downsample` surviving in a
still-image model) under its own class, with its own `latents_mean`/`latents_std` and its own weights —
`qwen_image_vae.safetensors`, 0.25 GB, shipped from Comfy-Org's Qwen repo, not any Wan repo.
`[flagged: "same family, different weights" is my reading; no Qwen source names Wan. Write "a Wan-2.1-family
VAE", never "the Wan 2.1 VAE".]`
**Layered is the one exception**: it loads `qwen_image_layered_vae.safetensors` (0.25 GB, from
`Comfy-Org/Qwen-Image-Layered_ComfyUI`), same config hyperparameters, different file — presumably RGBA
`[flagged]`. All fifteen non-Layered templates load the shared VAE.

### 2.4 Languages

`language: [en, zh]` in the YAML frontmatter of every model card. The bilingual claim is specifically about
**text rendering**: *"Whether it's alphabetic languages like English or logographic scripts like Chinese"*,
and Edit's *"bilingual (Chinese and English) text editing"*.
`[official — Qwen/Qwen-Image and Qwen/Qwen-Image-Edit READMEs]`

---

## 3. File layout per template

All of the below is read from the template JSON itself (node `properties.models[]` gives file → directory →
download URL; `widgets_values` gives what the loader is set to). Source root:
<https://github.com/Comfy-Org/workflow_templates/tree/main/templates> ; raw JSON at
`https://raw.githubusercontent.com/Comfy-Org/workflow_templates/main/templates/<name>.json`.
`[official — templates JSON]`

**Shared across the whole family** (the three files you always need):

| File | `models/` folder | Loader node | Loader widgets | Source |
|---|---|---|---|---|
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` | `text_encoders/` | `CLIPLoader` | `["qwen_2.5_vl_7b_fp8_scaled.safetensors", "qwen_image", "default"]` | `Comfy-Org/Qwen-Image_ComfyUI/split_files/text_encoders/` |
| `qwen_image_vae.safetensors` | `vae/` | `VAELoader` | `["qwen_image_vae.safetensors"]` | `Comfy-Org/Qwen-Image_ComfyUI/split_files/vae/` |
| *(variant transformer)* | `diffusion_models/` | `UNETLoader` | `["<file>", "default"]` | see per-template tables |

**The CLIPLoader `type` is `"qwen_image"`** on every single Qwen template in the repo, including the Layered
ones. The third widget is the loader `device`, `"default"`. `[official — every `image_qwen_image*.json`]`

One inconsistency worth carrying verbatim: in the **2511, 2511-int8, Layered and Layered-Control** templates
the *download URL* recorded for that identical text-encoder filename is
`https://huggingface.co/Comfy-Org/HunyuanVideo_1.5_repackaged/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors`
— same filename, different host repo, because Comfy-Org reuses one repackaged encoder across model families.
Older templates point at `Comfy-Org/Qwen-Image_ComfyUI/...`. Either download yields the same target filename.
`[official — templates/image_qwen_image_edit_2511.json node #162; templates/image_qwen_image_layered.json node #38]`

### 3.1 `image_qwen_image.json` — "Text to Image (Qwen-Image)" (2025-08-05)

| File | Folder | Loader | Notes |
|---|---|---|---|
| `qwen_image_fp8_e4m3fn.safetensors` | `diffusion_models/` | `UNETLoader` | 20.43 GB |
| `Qwen-Image-Lightning-8steps-V1.0.safetensors` | `loras/` | `LoraLoaderModelOnly`, strength `1` | optional, off by default; from `lightx2v/Qwen-Image-Lightning` |

Topology: `EmptySD3LatentImage` → `ModelSamplingAuraFlow` → `KSampler` → `VAEDecode`, two plain
`CLIPTextEncode` nodes, and a `PrimitiveBoolean` "Enable Lightning LoRA" driving three `ComfySwitchNode`s
(model / steps / CFG) so one graph covers both paths.

### 3.2 `image_qwen_image_edit.json` — "Qwen-Image-Edit" (2025-08-18)

| File | Folder | Loader |
|---|---|---|
| `qwen_image_edit_fp8_e4m3fn.safetensors` | `diffusion_models/` | `UNETLoader` (from `Comfy-Org/Qwen-Image-Edit_ComfyUI`) |
| `Qwen-Image-Edit-Lightning-4steps-V1.0-bf16.safetensors` | `loras/` | `LoraLoaderModelOnly` strength `1` (off by default) |

Topology, where Edit differs structurally: `LoadImage` → **`ImageScaleToTotalPixels ["lanczos", 1.5]`**
(1.5 MP) → into **two `TextEncodeQwenImageEdit` nodes** *and* into `VAEEncode`, whose latent is the KSampler's
`latent_image`. **`CFGNorm`** (strength `1`) sits between model and sampler. **No empty-latent node at all.**

### 3.3 `image_qwen_image_edit_2509.json` — "Qwen Image Edit 2509" (2025-09-25)

| File | Folder | Loader |
|---|---|---|
| `qwen_image_edit_2509_fp8_e4m3fn.safetensors` | `diffusion_models/` | `UNETLoader` |
| `Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors` | `loras/` | `LoraLoaderModelOnly` strength `1` — **on by default** |

The Lightning LoRA for 2509 lives in a **subfolder** of the Lightning repo:
`https://huggingface.co/lightx2v/Qwen-Image-Lightning/resolve/main/Qwen-Image-Edit-2509/Qwen-Image-Edit-2509-Lightning-4steps-V1.0-bf16.safetensors`
`[official — templates/image_qwen_image_edit_2509.json node #89]`

Changes vs 2508: text-encode becomes **`TextEncodeQwenImageEditPlus`** (multi-image), input scaling becomes
**`FluxKontextImageScale`** (Comfy reuses the Kontext bucketer), `CFGNorm` becomes `[1, false]`, output via
`SaveImageAdvanced ["Qwen_Image_2509", "png", "8-bit", "sRGB"]`.

### 3.4 `image_qwen_image_edit_2511.json` — "Qwen Image Edit 2511 – Material Replacement" (2025-12-23)

| File | Folder | Loader |
|---|---|---|
| `qwen_image_edit_2511_fp8mixed.safetensors` | `diffusion_models/` | `UNETLoader` (20.53 GB) |
| `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` | `loras/` | `LoraLoaderModelOnly` strength `1` (off by default) |

The 2511 Lightning LoRA lives in a **separate repo**, not the original Lightning one:
`https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning/resolve/main/Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors`
`[official — templates/image_qwen_image_edit_2511.json node #153]`

Topology: **two** `LoadImage` nodes (`leather_sofa.png` + `texture_fur.png`), each through
`FluxKontextImageScale`; two `TextEncodeQwenImageEditPlus`; both conditionings pass through
**`FluxKontextMultiReferenceLatentMethod` = `"index_timestep_zero"`** — the graph counterpart of
`zero_cond_t: true`. Sibling `template_qwen_image_edit_2511_systms_action.json` (2026-05-10) uses the **bf16**
`qwen_image_edit_2511_bf16.safetensors` (40.86 GB) with a style LoRA. `[official — that template, node #161]`

### 3.5 `image_qwen_image_edit_2511_int8.json` — "Qwen Image Edit 2511 Int8" (2026-07-10)

Identical graph to §3.4, with one substitution:

| File | Folder | Loader |
|---|---|---|
| `qwen_image_edit_2511_int8_convrot.safetensors` | `diffusion_models/` | `UNETLoader` `["...", "default"]` — 20.50 GB |

Source: `https://huggingface.co/Comfy-Org/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2511_int8_convrot.safetensors`
`[official — templates/image_qwen_image_edit_2511_int8.json node #161]`

### 3.6 `image_qwen_Image_2512.json` — "Qwen Image 2512" (2025-12-31)

| File | Folder | Loader |
|---|---|---|
| `qwen_image_2512_fp8_e4m3fn.safetensors` | `diffusion_models/` | `UNETLoader` (20.43 GB) |
| `Qwen-Image-2512-Lightning-4steps-V1.0-fp32.safetensors` | `loras/` | `LoraLoaderModelOnly` strength `1` (off by default) |

The 2512 Lightning LoRA is again a **new repo**: `https://huggingface.co/lightx2v/Qwen-Image-2512-Lightning/`
and, unusually, the shipped file is the **fp32** build.
`[official — templates/image_qwen_Image_2512.json node #221]`

Topology is the same shape as §3.1 (`EmptySD3LatentImage` → `ModelSamplingAuraFlow` → `KSampler`), with a
non-empty Chinese negative prompt baked in (see §11).

A separate template `image_qwen_image_2512_with_2steps_lora.json` — "Qwen-Image 2512 Turbo" (2026-01-30) —
uses a **third-party 2-step LoRA**, `Wuli-Qwen-Image-2512-Turbo-LoRA-2steps-V1.0-bf16.safetensors` from
`https://huggingface.co/Wuli-art/Qwen-Image-2512-Turbo-LoRA-2-Steps/`, and drops the negative branch entirely
via a `ConditioningZeroOut` node. `[official — templates/image_qwen_image_2512_with_2steps_lora.json]`

### 3.7 `image_qwen_image_layered.json` — "Layer Decomposition" (2025-12-22)

| File | Folder | Loader |
|---|---|---|
| `qwen_image_layered_bf16.safetensors` | `diffusion_models/` | `UNETLoader` (40.86 GB) |
| **`qwen_image_layered_vae.safetensors`** | `vae/` | `VAELoader` — **not** the shared VAE |

Source repo: `Comfy-Org/Qwen-Image-Layered_ComfyUI` (`split_files/diffusion_models/qwen_image_layered_bf16.safetensors`,
`split_files/diffusion_models/qwen_image_layered_fp8mixed.safetensors` 20.53 GB, `split_files/vae/qwen_image_layered_vae.safetensors`).
`[official — https://huggingface.co/api/models/Comfy-Org/Qwen-Image-Layered_ComfyUI/tree/main/split_files]`

Layered-only nodes: **`EmptyQwenImageLayeredLatentImage`** `[640, 640, 2, 1]`, **`LatentCut`** `["t", 1, 16384]`,
**`LatentCutToBatch`** `["t", 1]`, two `ReferenceLatent` nodes, `ImageScaleToMaxDimension ["lanczos", 640]` on
the input. Two subgraphs — "Image to Layers" and "Text to Layers" — the second muted by default (`mode: 4`).

`image_qwen_image_layered_control.json` (2026-01-15) swaps the transformer for
**`qwen_image_layered_control_bf16.safetensors`** downloaded from **DiffSynth-Studio**, not Comfy-Org:
`https://huggingface.co/DiffSynth-Studio/Qwen-Image-Layered-Control/resolve/main/qwen_image_layered_control_bf16.safetensors`,
loaded with `UNETLoader` widgets `["qwen_image_layered_control_bf16.safetensors", "fp8_e4m3fn"]` — note the
**non-default weight dtype**, the only Qwen template that sets it.
`[official — templates/image_qwen_image_layered_control.json node #37]`

### 3.8 ControlNet / inpaint templates

| Template | Control file | Folder | Loader / apply node |
|---|---|---|---|
| `image_qwen_image_instantx_controlnet.json` (2025-08-23) | `Qwen-Image-InstantX-ControlNet-Union.safetensors` (3.54 GB) | `controlnet/` | `ControlNetLoader` → `ControlNetApplyAdvanced` `[1, 0, 1]` |
| `image_qwen_image_instantx_inpainting_controlnet.json` (2025-09-12) | `Qwen-Image-InstantX-ControlNet-Inpainting.safetensors` (4.23 GB) | `controlnet/` | `ControlNetLoader` → **`ControlNetInpaintingAliMamaApply`** `[1, 0, 1]` |
| `image_qwen_image_union_control_lora.json` (2025-08-23) | `qwen_image_union_diffsynth_lora.safetensors` (0.94 GB) | `loras/` | `LoraLoaderModelOnly` strength `1` + two `ReferenceLatent` nodes |
| `image_qwen_image_controlnet_patch.json` (2025-08-24) | `qwen_image_canny_diffsynth_controlnet.safetensors` (2.27 GB) | **`model_patches/`** | **`ModelPatchLoader` → `QwenImageDiffsynthControlnet`** (strength `1`) |
| `image_qwen_Image_2512_controlnet.json` (2026-02-16) | `Qwen-Image-2512-Fun-Controlnet-Union-2602.safetensors` | `controlnet/` | `ControlNetLoader` → `ControlNetApplyAdvanced` `[1, 0, 1]` |

InstantX ControlNets are repackaged by Comfy-Org at
`https://huggingface.co/Comfy-Org/Qwen-Image-InstantX-ControlNets` (`split_files/controlnet/`).
DiffSynth ControlNets at `https://huggingface.co/Comfy-Org/Qwen-Image-DiffSynth-ControlNets`, which holds
**`split_files/model_patches/qwen_image_canny_diffsynth_controlnet.safetensors`,
`..._depth_...`, `..._inpaint_...` (2.27 GB each)** plus `split_files/loras/qwen_image_union_diffsynth_lora.safetensors`.
The 2512 Fun ControlNet is Alibaba PAI's, downloaded direct:
`https://huggingface.co/alibaba-pai/Qwen-Image-2512-Fun-Controlnet-Union/resolve/main/Qwen-Image-2512-Fun-Controlnet-Union-2602.safetensors`.
`[official — the five template JSONs above + the two Comfy-Org repo trees]`

The **`model_patches/`** folder is unusual: DiffSynth's canny/depth/inpaint ControlNets are not
`ControlNetLoader` models but model patches applied via `QwenImageDiffsynthControlnet` (inputs `model`,
`model_patch`, `vae`, `image`, `mask`). `[official — templates/image_qwen_image_controlnet_patch.json]`

### 3.9 Official Edit LoRAs shipped by Comfy-Org

`Comfy-Org/Qwen-Image-Edit_ComfyUI/split_files/loras/` holds six first-party Edit-2509 LoRAs:

| File | Size |
|---|---|
| `Qwen-Image-Edit-2509-Relight.safetensors` | 0.24 GB |
| `Qwen-Edit-2509-Multiple-angles.safetensors` | 0.24 GB |
| `Qwen-Image-Edit-2509-Fusion.safetensors` | 0.24 GB |
| `Qwen-Image-Edit-2509-Light-Migration.safetensors` | 0.24 GB |
| `Qwen-Image-Edit-2509-White_to_Scene.safetensors` | 0.24 GB |
| `Qwen-Image-Edit-2509-Anything2RealAlpha.safetensors` | 0.61 GB |

`[official — Comfy-Org/Qwen-Image-Edit_ComfyUI tree]` `image_qwen_image_edit_2509_relight.json` (2025-12-15)
stacks `Relight` **on top of** the 2509 Lightning 4-step LoRA, with `StringConcatenate` prepending the LoRA
trigger word. `[official — that template]`

---

## 4. Stock node settings per template (verbatim)

Every Qwen template in the repo uses **`euler` / `simple` / `denoise 1.0`** in `KSampler`. Not one uses a
different sampler or scheduler. `[official — all `image_qwen_image*.json` + `template_qwen_*` KSampler widgets]`

Steps and CFG are supplied by `PrimitiveInt` / `PrimitiveFloat` nodes routed through `ComfySwitchNode`s, so
**the KSampler's own `widgets_values` are stale display values and must not be quoted**. The authoritative
numbers are the primitives, and the switch semantics are: `on_false` = base model path, `on_true` = Lightning
path, gated by a `PrimitiveBoolean`. `[official — link tracing in each template's `links` array]`

| Template | Latent node | Resolution | `ModelSamplingAuraFlow` shift | Base steps / CFG | Lightning steps / CFG | Default branch |
|---|---|---|---|---|---|---|
| `image_qwen_image` | `EmptySD3LatentImage` | `1328, 1328, 1` | **3.1000000000000005** | **20 / 4.0** | 8 / 1.0 (8-step LoRA) | base |
| `image_qwen_image_edit` | `VAEEncode` (no empty latent) | input → `ImageScaleToTotalPixels ["lanczos", 1.5]` | **3.0** | **20 / 2.5** | 4 / 1.0 | base |
| `image_qwen_image_edit_2509` | `VAEEncode` | input → `FluxKontextImageScale` | **3.0** | 20 / 4.0 | **4 / 1.0** | **Lightning (boolean `true`)** |
| `image_qwen_image_edit_2509_relight` | `VAEEncode` | `FluxKontextImageScale` | 3.0 | — | 4 / 1.0 (hardwired) | Lightning + Relight LoRA |
| `image_qwen_image_edit_2511` | `VAEEncode` | `FluxKontextImageScale` | **3.1** | **40 / 4.0** | 4 / 1.0 | base |
| `image_qwen_image_edit_2511_int8` | `VAEEncode` | `FluxKontextImageScale` | 3.1 | 40 / 4.0 | 4 / 1.0 | base |
| `image_qwen_Image_2512` | `EmptySD3LatentImage` | `1328, 1328, 1` | 3.1000000000000005 | **50 / 4.0** | 4 / 1.0 | base |
| `image_qwen_image_2512_with_2steps_lora` | `EmptySD3LatentImage` | `1328, 1328, 1` | **3.0** | — | **2 / 1.0** (seed `fixed`) | 2-step LoRA only |
| `image_qwen_image_layered` | **`EmptyQwenImageLayeredLatentImage`** `[640, 640, 2, 1]` | 640 max dim | **1.0** | **20 / 2.5** | — | base |
| `image_qwen_image_layered_control` | `EmptyQwenImageLayeredLatentImage` `[640, 640, 2, 1]` | 640 | **1.0** | 20 / 2.5 | — | base |
| `image_qwen_image_instantx_controlnet` | `EmptySD3LatentImage` via subgraph | `FluxKontextImageScale` on control image | 3.1000000000000005 | — | **4 / 1.0** (hardwired Lightning-4step) | Lightning |
| `image_qwen_image_instantx_inpainting_controlnet` | `VAEEncode` + `SetLatentNoiseMask` | `ImageScaleToMaxDimension ["area", 1536]` | 3.1000000000000005 | **20 / 2.5** | 4 / 1.0 (muted branch) | base |
| `image_qwen_image_union_control_lora` | `VAEEncode` + 2 × `ReferenceLatent` | `ImageScaleToTotalPixels ["lanczos", 1]` | 3.1 | **20 / 2.5** | 4 / 1.0 | base |
| `image_qwen_image_controlnet_patch` | `VAEEncode` | `ImageScaleToTotalPixels ["area", 1.68]` | 3.1000000000000005 | **20 / 2.5** | 4 / 1.0 (muted) | base |
| `image_qwen_Image_2512_controlnet` | `EmptySD3LatentImage` `1328, 1328, 1` | `ResizeImageMaskNode ["scale total pixels", 1.6, "area"]` | 3.1000000000000005 | **50 / 4.0** | 4 / 1.0 | base |
| `template_qwen_Image_2512_360_lora` | `EmptySD3LatentImage` | **`2048, 1024, 1`** | 3.1000000000000005 | 50 / 4.0 | 4 / 1.0 | base |

`[official — templates JSON, node widgets + link tracing]`

Four numbers a skill would get wrong from priors: **shift is not constant** (3.1 for T2I base / 2511 / 2512 /
ControlNet, **3.0** for Edit-2508, Edit-2509 and the 2512 turbo, **1.0** for both Layered templates);
**base CFG is not constant** (4.0 for T2I and 2509/2511, **2.5** for Edit-2508 and the DiffSynth /
InstantX-inpaint graphs); **base step count climbs with the release** (20 → 20 → **40** at 2511 → **50** at
2512, matching each card's `num_inference_steps`); and **Lightning CFG is always exactly 1.0**, with 8 steps
(base T2I V1.0), 4 (everything else) or 2 (the third-party Wuli turbo LoRA).
`[official — templates + Qwen model cards]`

Other verbatim node settings worth carrying:

- `CFGNorm` appears in every Edit template. Widgets: `[1]` in 2508, `[1, false]` in 2509 / 2511 / int8.
  `[official — templates]`
- `Canny` thresholds: `[0.1, 0.2]` in `controlnet_patch`, `[0.26, 0.35]` in `union_control_lora`,
  `[0.33, 0.35]` in `2512_controlnet`. `[official — templates]`
- `ControlNetApplyAdvanced` / `ControlNetInpaintingAliMamaApply` are all set to
  **strength 1, start 0, end 1** (`[1, 0, 1]`). `[official — templates]`
- Inpainting template's mask handling: a "Grow and Blur Mask" subgraph with `GrowMask [20, true]` and
  `ImageBlur [31, 1]`, then `ImageCompositeMasked [0, 0, false]` to paste back.
  `[official — templates/image_qwen_image_instantx_inpainting_controlnet.json]`
- `FluxKontextMultiReferenceLatentMethod` is set to `"index_timestep_zero"` on **both** the positive and
  negative conditioning in the 2511 templates. `[official — templates]`

---

## 5. Quantisation (official)

Comfy-Org's repackaged repos are the official quant surface. Sizes from the HF tree API, 2026-09-09.

### `Comfy-Org/Qwen-Image_ComfyUI` — `split_files/diffusion_models/`
`[official — https://huggingface.co/api/models/Comfy-Org/Qwen-Image_ComfyUI/tree/main/split_files/diffusion_models]`

| File | Size |
|---|---|
| `qwen_image_bf16.safetensors` | 40.86 GB |
| `qwen_image_fp8_e4m3fn.safetensors` | 20.43 GB |
| `qwen_image_fp8_hq.safetensors` | **22.74 GB** |
| `qwen_image_fp8mixed.safetensors` | 20.53 GB |
| `qwen_image_nvfp4.safetensors` | **19.77 GB** |
| `qwen_image_2512_bf16.safetensors` | 40.86 GB |
| `qwen_image_2512_fp8_e4m3fn.safetensors` | 20.43 GB |

Text encoders in the same repo: `qwen_2.5_vl_7b.safetensors` **16.58 GB**,
`qwen_2.5_vl_7b_fp8_scaled.safetensors` **9.38 GB**, `qwen_2.5_vl_7b_nvfp4.safetensors` **6.11 GB**.
VAE: `qwen_image_vae.safetensors` **0.25 GB**.

### `Comfy-Org/Qwen-Image-Edit_ComfyUI` — `split_files/diffusion_models/`
`[official — https://huggingface.co/api/models/Comfy-Org/Qwen-Image-Edit_ComfyUI/tree/main/split_files/diffusion_models]`

| File | Size |
|---|---|
| `qwen_image_edit_bf16.safetensors` | 40.86 GB |
| `qwen_image_edit_fp8_e4m3fn.safetensors` | 20.43 GB |
| `qwen_image_edit_2509_bf16.safetensors` | 40.86 GB |
| `qwen_image_edit_2509_fp8_e4m3fn.safetensors` | 20.43 GB |
| `qwen_image_edit_2509_fp8mixed.safetensors` | 20.53 GB |
| `qwen_image_edit_2511_bf16.safetensors` | 40.86 GB |
| `qwen_image_edit_2511_fp8mixed.safetensors` | 20.53 GB |
| `qwen_image_edit_2511_int8_convrot.safetensors` | 20.50 GB |
| `firered_image_edit_1.0_bf16.safetensors` | 40.86 GB (a different model sharing the repo) |

### `Comfy-Org/Qwen-Image-Layered_ComfyUI`
`qwen_image_layered_bf16.safetensors` 40.86 GB, `qwen_image_layered_fp8mixed.safetensors` 20.53 GB,
`qwen_image_layered_vae.safetensors` 0.25 GB.
`[official — https://huggingface.co/api/models/Comfy-Org/Qwen-Image-Layered_ComfyUI/tree/main/split_files]`

Quant-ladder notes `[official — file naming + which template selects which]`: **`fp8_e4m3fn`** is the default
for base, Edit-2508, 2509 and 2512; **`fp8mixed`** is what **2511** and **Layered** default to (2511 has no
plain `fp8_e4m3fn` build at all) `[flagged: the mixed-precision split is undocumented]`;
**`int8_convrot`** is the family's only int8 build, 2511-only, with its own template (2026-07-10) — at
20.50 GB it is *not* smaller than fp8, the claimed win being speed, *"a quantized model for faster inference
while maintaining high quality"* `[official-via-docs — templates/index.json]`; **`nvfp4`** (19.77 GB
transformer, 6.11 GB encoder) and **`fp8_hq`** (22.74 GB) exist for base T2I only and **no template selects
either**. `[flagged: nvfp4 being Blackwell-only is my claim, not stated.]`

---

## 6. diffusers

Ten Qwen-Image pipeline classes ship in `diffusers/pipelines/qwenimage/`:

| Class | File | First shipped in |
|---|---|---|
| `QwenImagePipeline` | `pipeline_qwenimage.py` | **v0.35.0** (PyPI 2025-08-19) |
| `QwenImageImg2ImgPipeline` | `pipeline_qwenimage_img2img.py` | v0.35.0 |
| `QwenImageInpaintPipeline` | `pipeline_qwenimage_inpaint.py` | v0.35.0 |
| `QwenImageEditPipeline` | `pipeline_qwenimage_edit.py` | v0.35.0 |
| `QwenImageEditPlusPipeline` | `pipeline_qwenimage_edit_plus.py` | **v0.36.0** (PyPI 2025-12-08) |
| `QwenImageEditInpaintPipeline` | `pipeline_qwenimage_edit_inpaint.py` | v0.36.0 |
| `QwenImageControlNetPipeline` | `pipeline_qwenimage_controlnet.py` | v0.36.0 |
| `QwenImageControlNetInpaintPipeline` | `pipeline_qwenimage_controlnet_inpaint.py` | v0.36.0 |
| `QwenImageLayeredPipeline` | `pipeline_qwenimage_layered.py` | **v0.37.0** (PyPI 2026-03-05) |

`[official — https://github.com/huggingface/diffusers/blob/main/src/diffusers/pipelines/qwenimage/__init__.py ,
compared against the same file at tags v0.35.0 / v0.36.0 / v0.37.0; release dates from
https://pypi.org/pypi/diffusers/json]` Latest diffusers release as of 2026-09-09 is **0.40.0** (2026-08-20).

Which pipeline each checkpoint declares, from `model_index.json` `_class_name`:
`Qwen-Image` → `QwenImagePipeline`; `Qwen-Image-Edit` → `QwenImageEditPipeline`;
`Qwen-Image-Edit-2509` **and** `Qwen-Image-Edit-2511` → `QwenImageEditPlusPipeline`;
`Qwen-Image-2512` → `QwenImagePipeline`; `Qwen-Image-Layered` → `QwenImageLayeredPipeline`.
`[official — the five model_index.json files]`

**Minimum version, stated vs actual.** Every Qwen model card still says
`pip install git+https://github.com/huggingface/diffusers` — the legacy "install from main" line, never
updated. `[official — all six cards]` The Lightning repo is more precise: *"diffusers v0.35.1"* for the
original Qwen-Image, and *"For the Qwen-Image-Edit-2509, Qwen-Image-Edit-2511 and Qwen-Image-2512, please
install the latest diffusers from their main branch"*. `[official — ModelTC/Qwen-Image-Lightning README]`
`[flagged: by tag inspection 0.36.0+ suffices for 2509/2511/2512 and 0.37.0+ for Layered; the "main branch"
advice predates those releases.]`

Model-card inference parameters, verbatim:

| Checkpoint | Pipeline | `num_inference_steps` | `true_cfg_scale` | `negative_prompt` | Other |
|---|---|---|---|---|---|
| `Qwen/Qwen-Image` | `DiffusionPipeline` (→ `QwenImagePipeline`) | **50** | **4.0** | `" "` (single space) | `torch.bfloat16` |
| `Qwen/Qwen-Image-Edit` | `QwenImageEditPipeline` | **50** | **4.0** | `" "` | |
| `Qwen/Qwen-Image-Edit-2509` | `QwenImageEditPlusPipeline` | **40** | **4.0** | `" "` | `guidance_scale: 1.0`, `image: [image1, image2]` |
| `Qwen/Qwen-Image-Edit-2511` | `QwenImageEditPlusPipeline` | **40** | **4.0** | `" "` | `guidance_scale: 1.0`, list-of-images |
| `Qwen/Qwen-Image-2512` | `DiffusionPipeline` | **50** | **4.0** | long Chinese negative (see §11) | |
| `Qwen/Qwen-Image-Layered` | `QwenImageLayeredPipeline` | **50** | **4.0** | `" "` | `layers: 4`, `resolution: 640`, `cfg_normalize: True`, `use_en_prompt: True` |

`[official — the Quick Start code block on each model card]`

`true_cfg_scale=4.0` and `guidance_scale=1.0` coexist in the 2509/2511 snippets: with
`guidance_embeds: false` the latter is inert and `true_cfg_scale` is the real CFG knob. `[flagged: mechanism
is my reading; the cards pass both without comment.]` Layered's card documents `"resolution": 640`
(*"Using different bucket (640, 1024) … For this version, 640 is recommended"*), `"cfg_normalize": True`,
`"use_en_prompt": True` (*"Automatic caption language if user does not provide caption"*), and requires
`pip install python-pptx`. `[official — Qwen/Qwen-Image-Layered README]`

---

## 7. Qwen-Image-Lightning (the step-distillation LoRAs)

Repo: code at **<https://github.com/ModelTC/Qwen-Image-Lightning>**, weights at
**<https://huggingface.co/lightx2v/Qwen-Image-Lightning>** and per-variant sibling repos. Author is the
LightX2V / ModelTC team, not the Qwen team — but ComfyUI's *official* templates ship it, which is why it
counts as part of the family's official surface.
`[official — https://github.com/ModelTC/Qwen-Image-Lightning README; Comfy-Org templates reference the
lightx2v HF repos directly]`

Release history, verbatim from the README News block: 2025-08-08 `Qwen-Image-Lightning-8steps-V1.0`;
08-11 `4steps-V1.0`; 08-12 `8steps-V1.1` + bf16 builds; 08-23 `Qwen-Image-Edit-Lightning-8steps-V1.0` (+bf16);
08-24 `Qwen-Image-Edit-Lightning-4steps-V1.0` (+bf16); 09-10 `4steps-V2.0`; 09-12 `8steps-V2.0`;
10-09 `Qwen-Image-Edit-2509-Lightning-4steps-V1.0` and `-8steps-V1.0` (fp32+bf16, under the
`Qwen-Image-Edit-2509/` subfolder); 10-14 the fp8 fix below; 2025-12-22 `Qwen-Image-Edit-2511-Lightning-4steps-V1.0`
(fp32+bf16 **and a fused fp8 model**) in repo `lightx2v/Qwen-Image-Edit-2511-Lightning`;
2026-01-01 `Qwen-Image-2512-Lightning-4steps-V1.0` (fp32+bf16) in `lightx2v/Qwen-Image-2512-Lightning`.
Still open on the todo list: **`Qwen-Image-Edit-Lightning-4/8steps-V2.0`** and "Qwen Edit 2511 ComfyUI Workflow".
`[official — https://github.com/ModelTC/Qwen-Image-Lightning README]`

**Recommended settings from the repo's own CLI examples:** 8-step `--steps 8 --cfg 1.0`; 4-step
`--steps 4 --cfg 1.0`; base (T2I and Edit) `--steps 50 --cfg 4.0`. `[official — README]` These match the
ComfyUI templates on CFG and distilled steps; they disagree only on base T2I steps (Comfy ships 20, the
Lightning repo and the Qwen card both use 50).

**V1 vs V2**: *"Compared to V1.0, V2.0 produces images with reduced over-saturation, resulting in improved
skin texture and more natural-looking visuals."* `[official — README]`
Note the ComfyUI base-T2I template still ships **V1.0 8-step**, not V2.0. `[official — templates/image_qwen_image.json]`

**The fp8 grid-artefact problem — a genuinely load-bearing official fact.** The README states that using
Lightning LoRAs with `qwen_image_fp8_e4m3fn.safetensors` produces *"grid artifacts … wherein generated images
exhibit a grid-like pattern"*, because *"the qwen_image_fp8_e4m3fn.safetensors model was produced by directly
downcasting the original bf16 weights, rather than employing a calibrated conversion process with appropriate
scaling."* Two fixes are offered, and the README's own correctness table marks them:

| Base + LoRA combination | Correct? |
|---|---|
| bf16 base + LoRA trained on bf16 | ✅ |
| `qwen_image_fp8_e4m3fn` + LoRA trained on bf16 | ❌ |
| `qwen_image_fp8_e4m3fn` + `Qwen-Image-fp8-e4m3fn-Lightning-4steps-V1.0-fp32.safetensors` (LoRA distilled on the fp8 base) | ✅ |
| `lightx2v/Qwen-Image-Lightning/Qwen-Image/qwen_image_fp8_e4m3fn_scaled.safetensors` (scaled fp8 base) + LoRA trained on bf16 | ✅ |

`[official — https://github.com/ModelTC/Qwen-Image-Lightning README, "Using Lightning LoRAs with FP8 Models",
resolving https://github.com/ModelTC/Qwen-Image-Lightning/issues/32]`
This directly contradicts the naive read of the stock ComfyUI template, which pairs
`qwen_image_fp8_e4m3fn.safetensors` with a bf16-trained Lightning LoRA — the ❌ row.
`[flagged: the template may predate the fix, or Comfy may have patched fp8 handling internally; I did not find
a Comfy-Org statement either way. Worth flagging in the skill as a live gotcha.]`

Third-party accelerators the Lightning README endorses: **Nunchaku** 4-bit
(`nunchaku-tech/nunchaku-qwen-image`) and **cache-dit**, which claims *"3.5 steps inference"* with caching.
`[official — README "Community Support"]`

---

## 8. Licence (per variant, code vs weights)

**Code and weights are both Apache 2.0, and the two do not diverge** — unusual for this class of model and
worth stating plainly in the skill.

| Artefact | Licence | Evidence |
|---|---|---|
| Inference code, `QwenLM/Qwen-Image` | **Apache License 2.0** | `LICENSE` file at repo root is the verbatim Apache 2.0 text — `[official — https://github.com/QwenLM/Qwen-Image/blob/main/LICENSE]` |
| `Qwen/Qwen-Image` weights | Apache 2.0 | YAML `license: apache-2.0`; body: *"Qwen-Image is licensed under Apache 2.0."* |
| `Qwen/Qwen-Image-Edit` weights | Apache 2.0 | same, both places |
| `Qwen/Qwen-Image-Edit-2509` weights | Apache 2.0 | YAML frontmatter |
| `Qwen/Qwen-Image-Edit-2511` weights | Apache 2.0 | YAML + *"Qwen-Image is licensed under Apache 2.0."* |
| `Qwen/Qwen-Image-2512` weights | Apache 2.0 | YAML frontmatter (the card body has no licence section) |
| `Qwen/Qwen-Image-Layered` weights | Apache 2.0 | YAML + *"Qwen-Image-Layered is licensed under Apache 2.0."* |
| `Qwen-Image 2.0` / `3.0` | **no licence — no weights published** | see §1.2 |

`[official — HF model card YAML + License Agreement sections, all six repos]`

There is **no separate weights licence, no acceptable-use addendum and no output-rights clause** in any of
these repos; Apache 2.0 carries no field-of-use restriction, so commercial use and derivative LoRAs are
permitted by the licence. `[flagged: negative finding from reading the repos; platform rules and local law
still apply.]` Third-party components are **not** covered by Qwen's grant — the Lightning LoRAs
(ModelTC / lightx2v), InstantX and DiffSynth ControlNets, the distill-full checkpoint, and Alibaba PAI's 2512
Fun ControlNet. `[flagged: I did not read those licences.]`

---

## 9. Hosted surface

### Alibaba Cloud Model Studio / DashScope (first-party)

Model strings exposed on the text-to-image endpoint, per Alibaba's own model list:
`qwen-image-3.0-pro`, `qwen-image-3.0`, `qwen-image-2.0-pro` (with dated snapshots `2026-06-22`,
`2026-04-22`, `2026-03-03`), `qwen-image-2.0` (snapshot `2026-03-03`), `qwen-image-max` (snapshot
`2025-12-30`), `qwen-image-plus` (snapshot `2026-01-09`), and `qwen-image`. Image editing: **`qwen-image-edit`**.
`[official-via-docs — https://www.alibabacloud.com/help/en/model-studio/qwen-image-api]`

Parameters common to the family: `negative_prompt` (max 500 characters), **`prompt_extend` (boolean, default
`true`)**, `watermark` (boolean, default `false`), `seed` (0–2147483647), `n`.
Sizes: the 2.0 series takes any size whose *total pixels* fall between 512×512 and 2048×2048, default
**2048×2048**; `qwen-image-max` / `qwen-image-plus` default to **`1664*928`** with the fixed option set
`1664*928, 1472*1104, 1328*1328, 1104*1472, 928*1664` — i.e. the model card's aspect-ratio table.
Regions: **Singapore `ap-southeast-1`** and **China (Beijing) `cn-beijing`**.
`[official-via-docs — same page]`

`prompt_extend` defaulting to `true` is the single most important hosted-vs-local difference: the API rewrites
your prompt by default, local inference does not. `[official-via-docs — parameter default]`

**Pricing: not verified.** The Model Studio docs point at a separate "Model pricing" page that I could not
read for per-image figures, and the model-list page carries none. `[flagged — see §12.]`

### ComfyUI API nodes

`QwenImageTextToImageApi` — widgets `["qwen-image-3.0-pro", <prompt>, <negative>, 1024, 1024, 1, 42,
"randomize", true, false]`, plus a `ResolutionSelector` node set to `["1:1 (Square)", 1, 8]` feeding
`model.width` / `model.height`.
`QwenImageEditApi` — widgets `["qwen-image-3.0-pro", <prompt>, <negative>, "match input", 1, <seed>,
"randomize", true, false]`, with `model.images.image_1` and `model.images.image_2` inputs (so the API edit
node takes at least two reference images).
`[official — templates/api_qwen3_t2i.json, templates/api_qwen3_image_edit.json]`
`[flagged: the trailing `true, false` booleans are almost certainly `prompt_extend` and `watermark` given the
DashScope defaults, but the template does not label them.]`

### Third-party hosts

- **Replicate** (`https://replicate.com/qwen`) lists `qwen/qwen-image`, `qwen/qwen-image-2`,
  `qwen/qwen-image-2-pro`, `qwen/qwen-image-2512`, `qwen/qwen-image-layered`, `qwen/qwen-image-edit`,
  `qwen/qwen-image-edit-plus`, `qwen/qwen-image-edit-plus-lora`, `qwen/qwen-edit-multiangle`,
  **`qwen/qwen-image-lora-trainer`** and `qwen/qwen-image-lora-trainer-legacy`. No prices shown on the index.
  `[official-via-docs — https://replicate.com/qwen]`
- **fal** exposes `alibaba/qwen-image-3/text-to-image` — *"resolutions up to 2048×2048, with automatic prompt
  rewriting and prompt-guided resolution selection"*. `[official-via-docs — https://fal.ai/models?keywords=qwen-image]`

---

## 10. Trainer support facts

| Trainer | Qwen support | Documented defaults |
|---|---|---|
| **ostris/ai-toolkit** | `Qwen/Qwen-Image`, `Qwen-Image-2512`, `Qwen-Image-Edit`, `Qwen-Image-Edit-2509`, `Qwen-Image-Edit-2511` — listed in the README's supported-model table | ships three example configs (below) |
| **kohya-ss/musubi-tuner** | `docs/qwen_image.md`, script `qwen_image_train_network.py`; `--model_version` ∈ `original`, `edit`, `edit-2509`, `edit-2511`, `layered` | full CLI defaults (below) |
| **tdrussell/diffusion-pipe** | "Qwen-Image, Qwen-Image-Edit" in the supported-models line; `examples/qwen_image_24gb_vram.toml` | rank 32, `logit_normal` timesteps (below) |
| **Nerogar/OneTrainer** | "Qwen Image" in the README's supported-models list | **no per-model doc found** `[flagged]` |
| **kohya-ss/sd-scripts** | **no Qwen branch or doc** — the branch list has no `qwen*`; Qwen lives in the author's *musubi-tuner* instead | n/a |

`[official — the four repos' README / docs / examples as cited below]`

**ai-toolkit**, from `config/examples/train_lora_qwen_image_24gb.yaml`, `..._edit_32gb.yaml`,
`..._edit_2509_32gb.yaml`: **rank 16, alpha 16** (`linear: 16, linear_alpha: 16`) in all three;
`lr: 1e-4`, `optimizer: adamw8bit`, `dtype: bf16`, `noise_scheduler: flowmatch`, `batch_size: 1`;
`resolution: [512, 768, 1024]` with the comment **"qwen image enjoys multiple resolutions"**;
`steps: 2000` T2I / **`3000`** Edit; `caption_dropout_rate: 0.05`;
`train_text_encoder: false` — **"probably won't work with qwen image"**;
`arch:` = `qwen_image` / `qwen_image_edit` / **`qwen_image_edit_plus`** (2509).
The 24/32 GB fit comes from `quantize: true`,
`qtype: "uint3|ostris/accuracy_recovery_adapters/qwen_image_torchao_uint3.safetensors"` (per-variant
siblings), `quantize_te: true`, `qtype_te: "qfloat8"`, `low_vram: true`.
**Edit configs add `timestep_type: "weighted"`**, which the T2I config omits; Edit datasets take a
`control_path` (the 2509 config a **list** of control folders), and the job type changes from `sd_trainer`
to **`diffusion_trainer`**.

**musubi-tuner**, from `docs/qwen_image.md`
(`https://github.com/kohya-ss/musubi-tuner/blob/main/docs/qwen_image.md`):

- LoRA command: `--timestep_sampling shift --weighting_scheme none --discrete_flow_shift 2.2
  --optimizer_type adamw8bit --learning_rate 5e-5 --network_dim 16 --max_train_epochs 16 --seed 42
  --mixed_precision bf16 --gradient_checkpointing --sdpa`
- Timesteps, verbatim: *"`shift` with `--discrete_flow_shift` is the default. `qwen_shift` is also available.
  `qwen_shift` is a same method during inference. It uses the dynamic shift value based on the resolution of
  each image (typically around 2.2 for 1328x1328 images)."* plus a note that Qwen's inference shift is low,
  *"so a lower value than other models may be preferable."*
- **Weights constraint: "The fp8_scaled version cannot be used" (text encoder), "fp8_e4m3fn cannot be used"
  (Edit DiT), "fp8mixed cannot be used" (Layered DiT)** — musubi needs the **bf16** Comfy-Org repackages plus
  `qwen_2.5_vl_7b.safetensors` (16.58 GB unquantised encoder)
- VRAM table for 1024×1024, batch 1, bf16 + gradient checkpointing + xformers:
  `--fp8_base --fp8_scaled` → **30 GB**; `+ --blocks_to_swap 16` → **24 GB**; `+ --blocks_to_swap 45` → **12 GB**;
  64 GB system RAM recommended when swapping
- Finetuning (not LoRA): `--optimizer_type adafactor --learning_rate 1e-6 --fused_backward_pass`
- Edit inference flag **`--resize_control_to_official_size`** — *"Resize control image to official size (1M
  pixels keeping aspect ratio). **Recommended for better results with Edit models.** (Mandatory for 2511)"*
- Edit-2509/2511 multi-image: *"While the official version supports up to 3 images, Musubi Tuner allows
  specifying any number of images (though correct operation is confirmed only up to 3)"*, and control images
  may differ in size
- Layered adds `--remove_first_image_from_target` (the first target is the original image, the rest are layers)

**diffusion-pipe**, from `examples/qwen_image_24gb_vram.toml`:
`[model] type = 'qwen_image'`, `dtype = 'bfloat16'`, `transformer_dtype = 'float8'`,
**`timestep_sample_method = 'logit_normal'`**; `[adapter] type = 'lora', rank = 32`;
optimizer `automagic` with `weight_decay = 0.01` (commented alternative: `AdamW8bitKahan`, `lr = 2e-5`,
`betas = [0.9, 0.99]`); `blocks_to_swap = 8`, `gradient_accumulation_steps = 4`, `activation_checkpointing = true`.
`[official — https://github.com/tdrussell/diffusion-pipe/blob/main/examples/qwen_image_24gb_vram.toml]`

**Lightning training adapter: none exists.** No trainer documents a Qwen "Lightning adapter" (the Wan-style
requirement to attach the distilled LoRA during training), and no source states a "train on base, infer with
Lightning" rule in so many words. The nearest official fact is the fp8 problem in §7. `[flagged: negative
finding. Training against the bf16 base then stacking Lightning at inference is what every official config
implies, but treat it as community craft, not official.]`

---

## 11. Official prompt rules

**The "positive magic" suffix**, verbatim from the Qwen-Image model card and `prompt_utils.py`:

```python
positive_magic = {
    "en": ", Ultra HD, 4K, cinematic composition.",   # for english prompt
    "zh": ", 超清，4K，电影级构图."                      # for chinese prompt
}
```

`[official — https://huggingface.co/Qwen/Qwen-Image README; and
https://github.com/QwenLM/Qwen-Image/blob/main/src/examples/tools/prompt_utils.py, where the same string
appears without the leading comma as `magic_prompt = "Ultra HD, 4K, cinematic composition"` and is appended
to every rewritten English prompt; the Chinese path uses `magic_prompt = "超清，4K，电影级构图"`.]`
The identical constants survive into `prompt_utils_2512.py`. `[official — same repo path]`

**Negative prompt.** The base, Edit, 2509, 2511 and Layered cards all pass `negative_prompt = " "` — a single
space, not an empty string — with the base card's comment *"using an empty string if you do not have specific
concept to remove"*. **Qwen-Image-2512 breaks this**: its card and the ComfyUI 2512 template both ship a real
Chinese negative:
`低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，人脸无细节，过度光滑，画面具有AI感。构图混乱。文字模糊，扭曲。`
(low resolution, low quality, deformed limbs, deformed fingers, oversaturated, waxy look, faceless detail,
over-smoothed, AI-looking; chaotic composition; blurry, distorted text).
`[official — Qwen/Qwen-Image-2512 README; templates/image_qwen_Image_2512.json node #228 — the template's copy
omits the final full stop]`

**Aspect-ratio table**, verbatim from the cards (the 4:3 / 3:4 pair changed between releases):

| Ratio | Qwen-Image (2025-08) | Qwen-Image-2512 |
|---|---|---|
| 1:1 | 1328 × 1328 | 1328 × 1328 |
| 16:9 | 1664 × 928 | 1664 × 928 |
| 9:16 | 928 × 1664 | 928 × 1664 |
| 4:3 | **1472 × 1140** | **1472 × 1104** |
| 3:4 | **1140 × 1472** | **1104 × 1472** |
| 3:2 | 1584 × 1056 | 1584 × 1056 |
| 2:3 | 1056 × 1584 | 1056 × 1584 |

`[official — the two model cards' `aspect_ratios` dicts]` `[flagged: 1140 vs 1104 is almost certainly a typo
fixed in the later card — 1472 × 1104 is exactly 4:3, 1472 × 1140 is not. Prefer 1104.]`

**Official T2I rewriter rules** (`polish_prompt_en`'s SYSTEM_PROMPT, verbatim highlights): infer and add
detail for brief inputs *"without altering the core content"*; refine *"subject characteristics, visual style,
spatial relationships, and shot composition"*; **"If the input requires rendering text in the image, enclose
specific text in quotation marks, specify its position (e.g., top-left corner, bottom-right corner) and style.
This text should remain unaltered and not translated"**; pick a *"precise, niche style"*, defaulting to
realistic photography; **"Please ensure that the Rewritten Prompt is less than 200 words."** Language is
auto-detected by CJK codepoint scan (`get_caption_language`); the zh and en system prompts are separate.

**Official Edit enhancer rules** (`EDIT_SYSTEM_PROMPT`, verbatim highlights):
- *"Keep the enhanced prompt direct and specific"*; additions must *"align with the logic and style of the
  edited input image's overall scene."*
- Add/delete/replace: vague instructions get *"minimal but sufficient details (category, color, size,
  orientation, position)"* — *"Add an animal"* → *"Add a light-gray cat in the bottom-right corner, sitting and
  facing the camera"*. Replacement is phrased **"Replace Y with X"**.
- Text: **"All text content must be enclosed in English double quotes. Keep the original language of the text,
  and keep the capitalization."** Adding *and* replacing text are both replacement tasks
  (`Replace "xx" to "yy"`, `Replace the mask / bounding box to "yy"`); position/colour/layout only if asked.
- Human/ID: preserve *"ethnicity, gender, age, hairstyle, expression, outfit"*; **"For expression changes /
  beauty / make up changes, they must be natural and subtle, never exaggerated."** — *"Change the person's hat"*
  → *"Replace the man's hat with a dark brown beret; keep smile, short hair, and gray jacket unchanged"*.

`[official — https://github.com/QwenLM/Qwen-Image/blob/main/src/examples/tools/prompt_utils.py]`

Three more: the 2512 card points at `src/examples/tools/prompt_utils_2512.py` as the current rewriter;
the rewriters call **`qwen-plus`** (text) and **`qwen-vl-max-latest`** (edit) through DashScope
(`DASHSCOPE_API_KEY` / `DASH_API_KEY`), so official prompt expansion is a hosted LLM call, not a local step;
and Edit-2511 *"integrates selected popular LoRAs directly into the base model, unlocking their effects
without extra tuning"* — lighting enhancement and novel viewpoints now work without an adapter.
`[official — QwenLM/Qwen-Image README; prompt_utils.py; Qwen/Qwen-Image-Edit-2511 README]`

---

## 12. Facts I could not verify

1. **Per-image pricing on Alibaba Cloud Model Studio.** The docs route to a "Model pricing" page whose table
   I could not read; the model-list page carries no figures. Secondary reporting (unite.ai, the-decoder,
   llm-stats) claims Qwen-Image-3.0-Pro at roughly $0.04 (1K) / $0.075 (2K) and Standard at a flat $0.03 per
   image, and a ¥0.18-per-image figure circulates — **all secondary, none confirmed against Alibaba's own
   price list. Do not put a number in the skill without re-checking.**
2. **Qwen-Image 3.0's exact launch date and openness statement.** Secondary sources say announced
   **2026-07-21**, invite-only, then general API availability **2026-08-04/05**; ComfyUI's API templates are
   dated **2026-08-06**, which is consistent. I found no Qwen first-party page stating the date, and the
   QwenLM GitHub README's News block **stops at 2026-02-10 (Qwen-Image-2.0)** — it never mentions 3.0.
3. **Qwen-Image-2.0 is also closed.** Announced 2026-02-10 on the QwenLM README with a
   `https://qwen.ai/blog?id=qwen-image-2.0` link, described as *"Lighter Model Architecture – Smaller model
   size with faster inference speed"* and *"Native 2K resolution"*, but **no `Qwen/Qwen-Image-2.0` repo exists
   on Hugging Face** (the Qwen org's last image-family upload is `Qwen/Qwen-Image-Bench`, 2026-05-28). So the
   open/closed line falls after **2512 / Edit-2511**, not after 3.0 — correct the prompt's framing.
   `[official — https://github.com/QwenLM/Qwen-Image README News; https://huggingface.co/api/models?author=Qwen]`
4. **What `fp8mixed` and `int8_convrot` actually quantise.** Comfy-Org publishes no README describing the
   mixed-precision split or what "convrot" means.
5. **Whether ComfyUI works around the Lightning-on-fp8 grid artefact.** The stock template pairs the two
   combinations the Lightning repo marks ❌. No Comfy-Org statement found either way.
6. **VRAM floors for inference.** No official source states a minimum; the only official VRAM numbers in this
   report are musubi-tuner's *training* table.
7. **Qwen-Image-EliGen / DiffSynth's full role.** DiffSynth-Studio demonstrably ships Qwen artefacts that
   ComfyUI's official templates consume — `DiffSynth-Studio/Qwen-Image-Layered-Control`,
   `DiffSynth-Studio/Qwen-Image-Distill-Full` and `-Distill-LoRA` (the latter repackaged by Comfy-Org into
   `non_official/diffusion_models/qwen_image_distill_full_{bf16,fp8_e4m3fn}.safetensors`, 40.86 / 20.43 GB,
   which docs.comfy.org says to run at **15 steps CFG 1.0 or 10 steps CFG 1.0**) — but I did not open the
   EliGen (entity-level control) repo or verify its status.
   `[official — https://huggingface.co/api/models/Comfy-Org/Qwen-Image_ComfyUI/tree/main;
   https://docs.comfy.org/tutorials/image/qwen/qwen-image]`
8. **OneTrainer's Qwen defaults.** Support is claimed in the README's model list; no config example or doc
   page located.
9. **`InstantX/Qwen-Image-ControlNet-Union` and `Qwen-Image-ControlNet-Inpainting` upstream cards.** I read
   only Comfy-Org's repackages and the templates that load them, not InstantX's own documentation.
10. **The three "Qwen-Image 3.0" ComfyUI API booleans.** Labelled only as positional widgets in the template.
