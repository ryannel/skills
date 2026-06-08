# SDXL Setup & Workflows

All ComfyUI node settings here are read from the official `Comfy-Org/workflow_templates` JSONs and comfyanonymous's `ComfyUI_examples`; diffusers code from the Stability HF model cards. Community items are labelled.

## Table of contents
1. File layout & the VAE gotcha
2. ComfyUI — base-only graph
3. ComfyUI — base + refiner ensemble
4. ComfyUI — Turbo / Lightning / LCM / Hyper
5. diffusers — t2i, img2img, inpaint, the ensemble
6. Hires-fix & tiled upscale
7. ControlNet & IP-Adapter
8. Quantisation & VRAM

---

## 1. File layout & the VAE gotcha

| File | `models/` folder | Loader node |
|---|---|---|
| `sd_xl_base_1.0.safetensors` (~6.94 GB fp16) | `checkpoints/` | `CheckpointLoaderSimple` |
| `sd_xl_refiner_1.0.safetensors` (~6.08 GB) | `checkpoints/` | `CheckpointLoaderSimple` |
| `sd_xl_turbo_1.0_fp16.safetensors` | `checkpoints/` | `CheckpointLoaderSimple` |
| `sdxl_lightning_{N}step.safetensors` (full) | `checkpoints/` | `CheckpointLoaderSimple` |
| `sdxl_lightning_{N}step_lora.safetensors` | `loras/` | `LoraLoader` |
| `sdxl_vae.safetensors` / fp16-fix | `vae/` | `VAELoader` |
| finetunes (Juggernaut, RealVisXL, Pony…) | `checkpoints/` | `CheckpointLoaderSimple` |

**The checkpoint is one file** bundling UNet + CLIP-L + OpenCLIP-bigG + VAE; `CheckpointLoaderSimple` outputs `MODEL`, `CLIP`, `VAE`. No separate loaders needed for the stock graph.

**VAE gotcha (community, well-established):** SDXL's original VAE **overflows in fp16 → black/NaN images**. The baked-in VAE used by the stock templates is fine. If you decode in fp16 with a *standalone* VAE, use **`madebyollin/sdxl-vae-fp16-fix`** via a `VAELoader` wired into `VAEDecode`, or run the VAE in fp32. Black outputs almost always = this.

---

## 2. ComfyUI — base-only graph

```
CheckpointLoaderSimple (sd_xl_base_1.0.safetensors)
  ├─ MODEL ─────────────► KSampler
  ├─ CLIP ──► CLIPTextEncode (positive) ─► KSampler.positive
  │           CLIPTextEncode (negative) ─► KSampler.negative
  └─ VAE ───────────────────────────────► VAEDecode
EmptyLatentImage (1024×1024) ────────────► KSampler.latent
KSampler ─ LATENT ─► VAEDecode ─► SaveImage
```

Stock `KSampler` settings for base: **steps 25–40, cfg 5–8, sampler `euler`, scheduler `normal`, denoise 1.0**. (The simple-example template uses an advanced sampler split for the refiner; for base-only a plain `KSampler` at 30 steps / cfg 7 is the common default.)

Use the plain `CLIPTextEncode` (same text to both encoders). Swap to `CLIPTextEncodeSDXL` only for the `text_g`/`text_l` split (see prompting-guide §3).

---

## 3. ComfyUI — base + refiner ensemble

From `sdxl_simple_example.json` (verbatim). Two `CheckpointLoaderSimple` (base + refiner), each with its own positive/negative `CLIPTextEncode`, chained through two `KSamplerAdvanced` by latent:

**BASE — `KSamplerAdvanced`:**
`add_noise=enable, noise_seed=<seed>, steps=25, cfg=8, sampler_name=euler, scheduler=normal, start_at_step=0, end_at_step=20, return_with_leftover_noise=enable`

**REFINER — `KSamplerAdvanced`:**
`add_noise=disable, steps=25, cfg=8, sampler_name=euler, scheduler=normal, start_at_step=20, end_at_step=10000, return_with_leftover_noise=disable`

→ refiner `LATENT` → `VAEDecode` → `SaveImage`.

**Why these exact numbers:** both samplers share the **same 25-step schedule**; base runs steps 0→20 (= **0.8**) and returns its latent *with leftover noise*; the refiner continues 20→end **without adding fresh noise** (`add_noise=disable`). That's the "ensemble of experts" hand-off — base builds structure, refiner adds high-frequency detail at low noise. The refiner uses **only the bigG encoder**. The `sdxl_refiner_prompt_example.json` variant gives the refiner its own prompt.

**Is the refiner worth it?** Often not, once you use a good finetune (which bakes the detail in). Keep it for last-mile sharpness on base SDXL; skip it on Juggernaut/RealVis.

---

## 4. ComfyUI — Turbo / Lightning / LCM / Hyper

**Turbo** (`sdxlturbo_example.json`, verbatim) — custom-sampler graph:
- `CheckpointLoaderSimple` = `sd_xl_turbo_1.0_fp16.safetensors`
- `KSamplerSelect` = **`euler_ancestral`**
- `SDTurboScheduler` = **steps 1, denoise 1**
- `SamplerCustom` = `add_noise=True, noise_seed=0, **cfg=1**`
- `EmptyLatentImage` = **512×512** (Turbo is a 512px model). Works 1–10 steps.

**Lightning** (HF `ByteDance/SDXL-Lightning`):
- **Full checkpoint or UNet:** `CheckpointLoaderSimple`, then standard `KSampler` at **sampler `euler`, scheduler `sgm_uniform`, cfg 1, steps = the checkpoint's step count (1/2/4/8), denoise 1**, 1024².
- **LoRA:** load a base-SDXL *finetune*, add `LoraLoader` with `sdxl_lightning_{N}step_lora.safetensors` at strength 1.0, same sampler settings. Use the LoRA route to make a *custom finetune* fast; use the full checkpoint for best quality on plain SDXL. **Match the step count to the file** — a 4-step LoRA at 8 steps degrades. 1-step is experimental; 2-step is the floor, 4-step the default.

**LCM** (comfyanonymous LCM examples):
- Patch the model with **`ModelSamplingDiscrete`** set to **`lcm`**, then `KSampler` at **sampler `lcm`, scheduler `sgm_uniform`, cfg 1–2, steps 4–8**, 1024². **LCM-LoRA** (`LoraLoader`) applies the same to any finetune. Forgetting the `ModelSamplingDiscrete` patch or leaving CFG high "blows things up" (community).

**Hyper-SDXL** (ByteDance): LoRA or full ckpt, **sampler `euler`, scheduler `sgm_uniform`, cfg ~1, steps 1/2/4/8**. Best-rated 1-step option. Some 1-step modes ship a unified-guidance LoRA — follow the model card.

**Composability (the key workflow):** Lightning/LCM/Hyper **LoRAs stack onto any photoreal finetune** → fast + photoreal. Chain `LoraLoader` (Lightning/LCM/Hyper) after the finetune checkpoint, set the matching sampler/scheduler/cfg/steps, and you draft in 4 steps at Juggernaut quality.

---

## 5. diffusers — t2i, img2img, inpaint, the ensemble

Pipelines: `StableDiffusionXLPipeline` (t2i), `StableDiffusionXLImg2ImgPipeline` (img2img / refiner), `StableDiffusionXLInpaintPipeline` (inpaint). **diffusers ≥ 0.19.0.**

**Text-to-image:**
```python
import torch
from diffusers import StableDiffusionXLPipeline
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16, variant="fp16", use_safetensors=True).to("cuda")
img = pipe(prompt, num_inference_steps=30, guidance_scale=7.0,
           height=1024, width=1024).images[0]
```

**Base + refiner ensemble (80/20 split):**
```python
from diffusers import StableDiffusionXLPipeline, StableDiffusionXLImg2ImgPipeline
base = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16, variant="fp16").to("cuda")
refiner = StableDiffusionXLImg2ImgPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-refiner-1.0",
    torch_dtype=torch.float16, variant="fp16",
    text_encoder_2=base.text_encoder_2, vae=base.vae).to("cuda")

n_steps, high_noise_frac = 40, 0.8
latents = base(prompt=prompt, num_inference_steps=n_steps,
               denoising_end=high_noise_frac, output_type="latent").images
image = refiner(prompt=prompt, num_inference_steps=n_steps,
                denoising_start=high_noise_frac, image=latents).images[0]
```

**Turbo in diffusers:** `guidance_scale=0.0`, `num_inference_steps=1` (up to 4), 512×512. **Lightning/LCM/Hyper:** `guidance_scale=0.0` (LCM ~1.0–2.0 via `LCMScheduler`), steps = the variant's count. **Remember: ComfyUI `cfg=1` == diffusers `guidance_scale=0.0`** — guidance off. Never `guidance_scale` between 0 and 1 expecting "a little" — it's effectively off below ~1.

**VAE in diffusers:** if you hit black images in fp16, pass `vae=AutoencoderKL.from_pretrained("madebyollin/sdxl-vae-fp16-fix", torch_dtype=torch.float16)`.

---

## 6. Hires-fix & tiled upscale

SDXL is 1024-native, so you don't *need* the SD1.5 low-res-first dance — but to exceed ~1.5 MP without duplication/anatomy artefacts, generate in a 1024-area bucket then upscale:

- **Latent hires-fix:** `KSampler` → `LatentUpscaleBy` (×1.5, `bislerp`) → second `KSampler` at **denoise 0.3–0.5** → decode. Low denoise preserves composition while adding detail.
- **Tiled upscale (community):** `UltimateSDUpscale` (custom node) with a 4× ESRGAN model and **denoise ~0.2–0.35**, tile 1024, for large prints. Or model-only upscale (`UpscaleModelLoader` + `ImageUpscaleWithModel`, e.g. `4x-UltraSharp`) with no re-diffusion for a clean non-hallucinating enlarge.
- **Face/hand repair:** inpaint the region or use a detailer node (`FaceDetailer` from Impact Pack) at denoise ~0.4 — the SDXL-era equivalent of SD1.5's aDetailer.

---

## 7. ControlNet & IP-Adapter

Both are mature for SDXL — its biggest practical edge.

**ControlNet** (community model zoo — Stability's official SDXL ControlNets plus `xinsir`, `diffusers`, `kohya` releases):
- Load with `ControlNetLoader` → `ControlNetApplyAdvanced` (set `strength`, `start_percent`, `end_percent`) between conditioning and sampler.
- Common types: **canny, depth, openpose, tile, scribble, lineart, softedge**. `xinsir/controlnet-union-sdxl` bundles many types in one model.
- Preprocess the source with the `comfyui_controlnet_aux` nodes (depth-anything, openpose, canny, etc.).

**IP-Adapter** (image prompt / style / identity transfer):
- `ComfyUI_IPAdapter_plus` custom nodes. Variants: base, **Plus** (more detail), **FaceID** / **FaceID Plus v2** (identity via InsightFace embeddings).
- Pipeline: `IPAdapterUnifiedLoader` → `IPAdapter` node with a reference image and `weight` ~0.5–0.8. FaceID needs the InsightFace model installed.

These let SDXL do pose/structure/identity control that newer DiT models still lack mature tooling for.

---

## 8. Quantisation & VRAM

- **No useful GGUF for SDXL.** It's a **Conv2D-heavy UNet**; GGUF/DiT quantisation targets transformers, and the `city96/ComfyUI-GGUF` author says explicitly *don't quantise SDXL* (quality collapses). fp16 is the format.
- **fp8 weight-casting:** ComfyUI's `--fp8_e4m3fn-unet` casts UNet weights to fp8 to save VRAM (small quality cost); the model still computes in higher precision.
- **VRAM (community):** ComfyUI auto-offloads, so 1024² runs on **~4 GB** (low-VRAM), **6–8 GB** comfortable. Base+refiner keeps both checkpoints resident → budget **8 GB+**. Fast variants don't reduce VRAM (same UNet), only time. Stability/Comfy publish no single hard minimum.
- **Speed:** distilled variants (Turbo/Lightning/LCM/Hyper) cut a 30-step render to 1–8 steps — near-real-time on a mid-range GPU. That's the lever for low-end hardware, not quantisation.
