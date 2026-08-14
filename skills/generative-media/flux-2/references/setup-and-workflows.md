# FLUX.2 — Setup & Workflows Reference

Source tier: ComfyUI template JSONs (primary, read verbatim), Comfy-Org HF repos (primary), diffusers docs and HF blog (official-via-docs), community GGUF repos and Civitai training guide (community-tier, labelled).

---

## Contents

1. [VRAM requirements table](#1-vram)
2. [ComfyUI — [dev] image-edit template](#2-dev-image-edit)
3. [ComfyUI — [klein] 9B templates](#3-klein-9b)
4. [ComfyUI — [klein] 9B KV template](#4-9b-kv)
5. [ComfyUI — GGUF quants (community)](#5-gguf)
6. [diffusers — detailed setup](#6-diffusers)
7. [Using LoRAs](#7-using-loras)
8. [LoRA training → moved to `references/lora-training.md`](#8-lora)

---

## 1. VRAM requirements table

Values are approximate and depend on resolution (1024×1024 unless noted) and batch size 1. Source: HF blog (official-via-docs) + deepwiki architecture analysis (community).

| Config | VRAM (approx) | Notes |
|---|---|---|
| [dev] bf16 full | ~80 GB | Multi-GPU (2× A100/H100) or offload |
| [dev] fp8 mixed (`flux2_dev_fp8mixed.safetensors`) | ~20 GB | Fits single A100/H100 40GB or 3090/4090 24GB |
| [dev] NVFP4 (`FLUX.2-dev-NVFP4`) | ~11 GB | Requires Ada/Hopper GPU (3090+ or 4090); ~2.7× faster, ~55% less VRAM vs bf16 |
| [dev] GGUF Q4_K_M (community) | ~16 GB | `city96/ComfyUI-GGUF` required |
| [dev] GGUF Q2_K (community) | ~13 GB | Quality degradation vs fp8 |
| [dev] text encoder bf16 (Mistral 3.2) | ~35.6 GB | Large — use fp8 (18 GB) or fp4 (12.3 GB) in practice |
| [dev] text encoder fp8 | ~18 GB | Default for most Comfy setups |
| [dev] text encoder fp4 | ~12.3 GB | Lowest quality reduction, highest compression |
| [klein] 4B fp16 | ~13 GB | — |
| [klein] 4B fp8 | ~8 GB | Fits RTX 3080/4070Ti |
| [klein] 9B fp8 | ~14–16 GB | Fits 3090/4090 |
| [klein] 9B bf16 full | ~32+ GB | Needs offload or 40 GB+ |

**GGUF note (community-tier):** Exact sizes change as new quants ship. Verify at `city96/FLUX.2-dev-gguf` and `unsloth/FLUX.2-dev-GGUF` on Hugging Face before planning storage.

---

## 2. ComfyUI — [dev] image-edit template

Source: `Comfy-Org/workflow_templates/image_flux2_image_editing.json` (verbatim).

**File layout:**

| File | Folder | Loader | Notes |
|---|---|---|---|
| `flux2_dev_fp8mixed.safetensors` | `models/diffusion_models/` | `UNETLoader` | Same as t2i template |
| `mistral_3_small_flux2_fp8.safetensors` | `models/text_encoders/` | `CLIPLoader` type `"flux2"` | fp8 (not bf16) in edit template |
| `flux2-vae.safetensors` | `models/vae/` | `VAELoader` | Full encoder — different from t2i's `full_encoder_small_decoder` |
| `Flux_2-Turbo-LoRA_comfyui.safetensors` *(optional)* | `models/loras/` | `LoraLoaderModelOnly` | Same turbo LoRA as t2i |

**Key nodes added for image editing:**
- `LoadImage` → feeds into `VAEEncode` (encodes reference image to latent space)
- `ReferenceLatent` — new FLUX.2 node; takes a latent + optional mask, outputs a reference conditioning token
- Multiple `ReferenceLatent` nodes are wired in sequence; each accepts one reference image
- `BasicGuider` and `FluxGuidance=4` remain unchanged; the reference latents are injected into the conditioning stream, not into the guider

**Stock settings (image-edit template defaults):**

| Setting | Value |
|---|---|
| Steps | 20 |
| FluxGuidance | 4 |
| Sampler | euler |
| Scheduler | Flux2Scheduler |
| Edit strength (noise) | Controlled by denoising start/end sliders |

**Practical tip:** Start with denoising strength 0.7–0.85 for content preservation with style change; 0.9–1.0 for near-full regeneration using the reference as composition seed.

---

## 3. ComfyUI — [klein] 9B templates

Source: `Comfy-Org/workflow_templates/image_flux2_text_to_image_9b.json` (verbatim).

**File layout:**

| File | Folder | Loader |
|---|---|---|
| `flux-2-klein-base-9b-fp8.safetensors` (base) or `flux-2-klein-9b-fp8.safetensors` (distilled) | `models/diffusion_models/` | `UNETLoader` |
| `qwen_3_8b_fp8mixed.safetensors` | `models/text_encoders/` | `CLIPLoader` type `"flux2"` |
| `full_encoder_small_decoder.safetensors` | `models/vae/` | `VAELoader` |

Downloads from `Comfy-Org/flux2-klein-9B` on Hugging Face.

**Stock settings:**

| Variant | Steps | Guider | CFG | Notes |
|---|---|---|---|---|
| 9B distilled | 4 | CFGGuider | 1 | guidance-off; sampler euler |
| 9B base | 20 | CFGGuider | 5 | sampler euler |

**Note on 9B vs 4B VAE:** 9B uses `full_encoder_small_decoder.safetensors` (same as [dev] t2i). 4B uses `flux2-vae.safetensors`. Do not mix — the two VAEs have different architectures.

---

## 4. ComfyUI — [klein] 9B KV template

Source: `Comfy-Org/workflow_templates/image_flux2_klein_9b_kv*.json` (verbatim, exact filename may vary — check the Comfy-Org templates repo for current name).

**Purpose:** KV-caching variant. Caches the reference image's key-value attention states so that repeated inference with the same set of reference images is significantly faster (the reference encoding is computed once and reused). Critical for multi-reference workflows with high reference-image counts.

**File layout:** Same files as the standard 9B template. No additional model files.

**Additional nodes:**
- `Flux2KleinKVCache` node — caches reference latent K/V states
- Standard `ReferenceLatent` nodes for the actual reference images

**When to use KV vs standard 9B:**
- Running batch jobs with the same reference image set and varying prompts → use KV (first call pays the reference encoding; subsequent calls reuse the cache)
- Single-shot generation with one reference → standard 9B is equivalent
- KV caching provides ~1.5–3× speedup on repeated-reference batches (community-tier estimate)

---

## 5. ComfyUI — GGUF quants (community)

**Required custom node:** Install `city96/ComfyUI-GGUF` via ComfyUI Manager before using GGUF models.

**Important path difference:** GGUF `.gguf` files go in `models/unet/` (not `models/diffusion_models/`). The `UnetLoaderGGUF` node (from the custom node) reads from `models/unet/`.

**Repositories (community-tier):**
- `city96/FLUX.2-dev-gguf` — produces Q2_K through Q8_0 quants
- `unsloth/FLUX.2-dev-GGUF` — alternative quant series; may include iQ (importance-weighted) variants

**File naming convention:** `flux2-dev-Q4_K_M.gguf` (approximate — verify exact filenames in the HF repo before downloading).

**Node swap from official templates:**

| Official template node | GGUF equivalent |
|---|---|
| `UNETLoader` with `.safetensors` | `UnetLoaderGGUF` with `.gguf` |
| Everything else | Unchanged |

Text encoder and VAE files remain `.safetensors` — GGUF quantisation applies only to the UNet/DiT; text encoder and VAE run at their usual precision.

**Quality expectation:** Q8_0 ≈ fp8 quality; Q4_K_M: mild quality reduction, good for most subjects; Q2_K: noticeable degradation on fine detail and faces. For portrait and skin-heavy work, Q4_K_M or higher.

---

## 6. diffusers — detailed setup

**Recommended install:**
```bash
pip install git+https://github.com/huggingface/diffusers -U
```
Version v0.38.0 appears in diffusers source code URLs — verify at `pypi.org/project/diffusers` whether it has landed as a stable pip release before relying on the git-install path.

**[dev] — `Flux2Pipeline`**

```python
import torch
from diffusers import Flux2Pipeline

# Standard load (requires ~20 GB VRAM)
pipe = Flux2Pipeline.from_pretrained(
    "black-forest-labs/FLUX.2-dev",
    torch_dtype=torch.bfloat16
)
pipe.to("cuda")

# OR: CPU offload (works on <16 GB VRAM, slower)
pipe.enable_model_cpu_offload()

# OR: Group offloading (finer-grained memory management)
# pipe.enable_group_offload(onload_device=torch.device("cuda"), offload_device=torch.device("cpu"), offload_type="block_level")

image = pipe(
    "A woman in her early 30s with silver-grey cropped hair...",
    num_inference_steps=50,
    guidance_scale=4.0,
    height=1024,
    width=1024,
    generator=torch.Generator("cuda").manual_seed(42)
).images[0]
image.save("output.jpg")
```

**[klein] 9B base — `Flux2KleinPipeline`**

```python
from diffusers import Flux2KleinPipeline

pipe = Flux2KleinPipeline.from_pretrained(
    "black-forest-labs/FLUX.2-klein-base-9B",
    torch_dtype=torch.bfloat16
)
pipe.enable_model_cpu_offload()

image = pipe(
    "A café counter in morning light...",
    num_inference_steps=20,
    guidance_scale=5.0,
    height=1024,
    width=1024,
).images[0]
```

**[klein] 9B KV-cached — `Flux2KleinKVPipeline`**

```python
from diffusers import Flux2KleinKVPipeline
# Load exactly as Flux2KleinPipeline but with the KV class
pipe = Flux2KleinKVPipeline.from_pretrained(
    "black-forest-labs/FLUX.2-klein-base-9B",
    torch_dtype=torch.bfloat16
)
```

**[klein] 4B:** There is no dedicated named pipeline class in the diffusers docs at research time for the 4B variant — load via the same `Flux2KleinPipeline` pattern or directly from the 4B HF repo (check model card for the recommended pipeline at time of use). Community reports indicate `Flux2KleinPipeline` works with appropriate config changes.

**Hardware minimums for diffusers (community-tier):**

| Config | Min VRAM | Notes |
|---|---|---|
| [dev] fp8 with cpu_offload | 12 GB | Slow; model layers shuttle CPU↔GPU |
| [dev] fp8 full | 20 GB | RTX 3090/4090 or A100 |
| [klein] 4B fp8 | 8 GB | RTX 3080Ti/4070Ti |
| [klein] 9B fp8 | 14–16 GB | RTX 3090/4090 |

**4-bit quantisation (bitsandbytes, community):**
```python
from transformers import BitsAndBytesConfig
from diffusers import Flux2Pipeline

nf4_config = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)
pipe = Flux2Pipeline.from_pretrained(
    "black-forest-labs/FLUX.2-dev",
    text_encoder=None,  # load separately to apply bnb config
    transformer=None,
    torch_dtype=torch.bfloat16
)
# See HF bitsandbytes integration docs for full pattern
```

---

## 7. Using LoRAs

The generic path for any downloaded FLUX.2 LoRA. (Training your own is §8.)

> **Sourcing:** the loader node and the frozen-encoder fact are verified (official template + AI-Toolkit configs); the weight ranges and "FLUX.2 dislikes trigger words" are community craft from named Flux LoRA trainers (apatero, RunComfy, fal.ai, bghira/SimpleTuner). FLUX.2 is new — treat the numbers as starting points.

**Node wiring — model-only.** A FLUX.2 LoRA patches the **DiT transformer only**; the text encoders (Mistral 3.2 for [dev], Qwen3 for [klein]) are **frozen** in both training and inference, so there are no encoder weights to apply. Load it with **`LoraLoaderModelOnly`** on the model path:

```
(model loader) → LoraLoaderModelOnly → Flux2 sampler chain
```

If a LoRA *does* ship text-encoder weights (rare for FLUX.2), switch to the full `LoraLoader` so they apply — but model-only is the norm.

**Variant-specific — a [dev] LoRA does not load on [klein], and vice-versa.** Unlike Z-Image (where Base and Turbo share one architecture), FLUX.2's variants are **different model sizes** — [dev] is 32B, [klein] is 4B or 9B — so their LoRAs are **not interchangeable**. Match the LoRA to the exact variant it was trained on. The Klein sizes matter too: **Klein 9B requires the Qwen3-8B encoder** — run it against the 4B encoder and it fails outright. Check the LoRA's stated base model before downloading.

**Weight.** Start ~**0.8**, sweep **0.6–1.2**. Lower for style LoRAs that flatten texture; higher to force a stubborn concept. Read the LoRA's card for the author's tested weight. *(Community; consistent with Flux.1 conventions.)*

**Trigger words — FLUX.2 mostly doesn't want them.** Because the encoder is a full LLM (Mistral/Qwen3), FLUX.2 reads **natural-language description** far better than bare trigger tokens — trainers report that trigger words "confuse the model" and that semi-long descriptive captions activate a LoRA best. If a LoRA defines a trigger, include it verbatim; otherwise just *describe* what you want in prose. This is the opposite of tag-based SDXL, where the literal trigger token is mandatory.

**Stacking.** Chain `LoraLoaderModelOnly` nodes (MODEL out → MODEL in), or use the rgthree **Power Lora Loader**. Community practice runs **3–4 LoRAs** max and **lowers each strength** as you add them (e.g. a character + a style + an effect, each ~0.5–0.8) so they don't fight or over-bake. Use `strength_model` to make one dominant.

**The Turbo LoRA** (`Flux_2-Turbo-LoRA_comfyui.safetensors`) is a special case — an *acceleration* LoRA that cuts [dev]/[klein] to 8 steps (guidance stays 4), toggled via `ComfySwitchNode`. It stacks with content LoRAs like a speed LoRA, not a style one.

**Ecosystem (early 2026, fast-moving).** Civitai is the main LoRA source — filter by the **exact FLUX.2 variant** ([dev] vs [klein]); a Flux.1 LoRA won't load. Most are trained with the **Ostris AI-Toolkit**; BFL published an official "fine-tune [klein] in under 60 min" LoRA guide, and fal.ai / RunComfy / bghira's SimpleTuner all support FLUX.2 training. The published pool was still small and growing close to release.

---

## 8. LoRA training → `references/lora-training.md`

Training moved to its own file, matching the suite's layout: **`references/lora-training.md`** covers the supported training bases (train on base, never distilled; [klein] 4B Base for commercial rights), the AI-Toolkit YAML and the Civitai klein recipe (including its dim-2 floor warning), hyperparameters by target (character vs style — Herbst's 50+-run ablation), caption-the-residual in prose and the contested captionless debate, **style-LoRA specifics** (diversity maxim, color-cast lock-in, the out-of-set acceptance test), and XY-grid evaluation. The full character pipeline is **`references/characters.md`**. Once trained, **§7** above covers loading, weights, stacking, and variant compatibility.
