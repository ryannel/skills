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
7. [LoRA training](#7-lora)

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

## 7. LoRA training

**Supported base models for training:**
- [dev] 32B (Non-Commercial)
- [klein] 4B Base (Apache 2.0 — use this for commercially-deployable LoRAs)
- [klein] 9B Base (Non-Commercial)

**Do not use distilled (4-step) variants as LoRA training bases** — the distillation removes texture diversity needed for fine-tuning. Always use the corresponding base.

### AI-Toolkit (Ostris) — community, most common

Supports [dev], [klein] 4B base, [klein] 9B base.

```yaml
# config.yaml example
job: extension
config:
  name: my_flux2_lora
  process:
    - type: sd_trainer
      training_folder: "path/to/your/images"
      device: cuda:0
      trigger_word: "my_concept"
      network:
        type: lora
        linear: 16
        linear_alpha: 16
      train:
        batch_size: 1
        steps: 2000
        gradient_accumulation_steps: 1
        train_unet: true
        train_text_encoder: false
        content_or_style: balanced
        learning_rate: 1e-4
        optimizer: adamw8bit
        lr_scheduler: cosine
        max_grad_norm: 1.0
      model:
        name_or_path: "black-forest-labs/FLUX.2-dev"
        is_flux2: true  # flag for FLUX.2 architecture (verify this flag in current AI-Toolkit)
        quantize: true
```

Install: `pip install git+https://github.com/ostris/ai-toolkit` (check for FLUX.2 support tag). **Community-tier** — training stability and optimal hyperparameters for FLUX.2 were still being established close to the model's release. Check AI-Toolkit GitHub issues/discussions for current recommendations.

### Kohya-ss / sd-scripts — community

Kohya supports Flux.1 LoRA training; FLUX.2 support was pending/in-progress close to release. Verify at `github.com/kohya-ss/sd-scripts` before relying on it for FLUX.2.

### Civitai AI-Toolkit recipe — community

Civitai published an AI-Toolkit-based training recipe for [klein] at `developer.civitai.com/orchestration/recipes/training-flux2-klein`. It targets [klein] distilled (4-step) for inference but you should train on the base for texture diversity.

**Practical training notes (community-tier):**

| Parameter | Suggested range | Notes |
|---|---|---|
| Steps | 1500–3000 | Fewer for concepts; more for complex styles |
| Rank (r / linear) | 16–64 | Higher rank = more capacity = larger file |
| Learning rate | 5e-5 to 2e-4 | FLUX.2's large DiT is sensitive to LR — start at the low end |
| Batch size | 1–4 | Higher VRAM allows higher batch; 1 with gradient accumulation is safe |
| Training data | 10–50 images | Concept: 10–20; style/character: 25–50 |
| Train text encoder | No | Standard recommendation; encoder is frozen |

LoRA files load in ComfyUI with `LoraLoaderModelOnly` — they apply to the UNet only, not the text encoder (Mistral/Qwen3 are frozen in inference). The SKILL.md main file documents the `LoraLoaderModelOnly` node.
