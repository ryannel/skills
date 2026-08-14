# Krea 2 — Setup & workflows

Local setup (ComfyUI, diffusers, the reference CLI), quantisation and VRAM strategy, using LoRAs, and the multi-stage / mixed-model workflows. Facts verified against the template JSON, HF repo listings, GitHub README, diffusers docs, and musubi-tuner docs on 2026-07-07; community recipes attributed inline.

## Contents
1. [ComfyUI: the official template, node by node](#1-comfyui-the-official-template-node-by-node)
2. [Quantisation & VRAM](#2-quantisation--vram)
3. [The reference CLI](#3-the-reference-cli)
4. [diffusers](#4-diffusers)
5. [The Wan 2.1 VAE swap](#5-the-wan-21-vae-swap)
6. [Using LoRAs](#6-using-loras)
7. [Multi-stage workflows](#7-multi-stage-workflows)
8. [Krea 2 in mixed-model pipelines](#8-krea-2-in-mixed-model-pipelines)

---

## 1. ComfyUI: the official template, node by node

Template: **`image_krea2_turbo_t2i.json`** (Comfy-Org/workflow_templates; in-app under Templates → Image once ComfyUI is updated). Tutorial: docs.comfy.org/tutorials/image/krea/krea-2. No custom nodes. Only a Turbo t2i template exists — there is no official Raw template (Raw isn't recommended for inference) [official].

**Downloads** (all from `Comfy-Org/Krea-2`):

| File | Size | → folder |
|---|---|---|
| `diffusion_models/krea2_turbo_fp8_scaled.safetensors` | 13.1 GB | `models/diffusion_models/` |
| `text_encoders/qwen3vl_4b_fp8_scaled.safetensors` | 5.2 GB | `models/text_encoders/` |
| `vae/qwen_image_vae.safetensors` | 0.25 GB | `models/vae/` |
| `loras/krea2_<style>.safetensors` (optional) | 0.47 GB | `models/loras/` |

**The graph** (a subgraph wraps the pipeline; double-click to open):

- `UNETLoader` → `krea2_turbo_fp8_scaled.safetensors`, weight_dtype `default`
- `CLIPLoader` → `qwen3vl_4b_fp8_scaled.safetensors`, type **`krea2`**, device `default`
- `VAELoader` → `qwen_image_vae.safetensors`
- `LoraLoaderModelOnly` → strength **0.8**, behind an `enable_lora?` boolean switch (model-only — Krea 2 LoRAs never touch the text encoder)
- `CLIPTextEncode` positive; the negative path runs through **`ConditioningZeroOut`** — the mechanism that makes negatives structurally inert at cfg 1.0
- `EmptyLatentImage` 1024×1024 — note: the *plain* latent node, not an SD3/Flux one, and **no shift node** (no `ModelSamplingAuraFlow`; the resolution-aware time shift is handled by the model config). A `ResolutionSelector` offers 1K–2K aspect presets.
- `KSampler`: **steps 8, cfg 1.0, sampler `euler`, scheduler `simple`, denoise 1.0**
- `VAEDecode` → `SaveImage` (prefix `Krea2_turbo`)

**Subgraph switches:** `prompt_enhance` (default **true** — the `TextGenerate` LLM expander; see `prompting-guide.md §6` for when and why to turn it off, including the documented refusal bug Comfy-Org/ComfyUI#14631) and `enable_lora?` (default false). A `CustomCombo` on the main canvas picks the style LoRA and auto-appends its trigger phrase to your prompt via `StringConcatenate`.

**Hosted Medium/Large in ComfyUI:** separate path entirely — the "Krea 2 Image" API/partner node (API-key billing, style refs, moodboard IDs, creativity Raw/Low/Medium/High) [official — Comfy blog]. See `api-and-hosted.md §4`.

## 2. Quantisation & VRAM

**Official precisions** (Comfy-Org/Krea-2 repo listing, sizes exact):

| File | Size | Notes |
|---|---|---|
| `krea2_turbo_bf16` / `krea2_raw_bf16` | 26.3 GB | full precision; ~46 GB unified memory in practice [community — liutyi] |
| `krea2_turbo_fp8_scaled` / `krea2_raw_fp8_scaled` | 13.1 GB | the template default |
| `krea2_turbo_int8_convrot` / `krea2_raw_int8_convrot` | 13.5 GB | **~2× faster than fp8** — replicated down to a 1050 Ti [community — nsfwVariant; YeahYeah2992]. Quality disputed: "same if not better" [both above] vs **worse complex-prompt adherence than fp8** [community — ganrocks007, 3060 12 GB]. Needs a recent ComfyUI |
| `krea2_turbo_mxfp8` | 13.5 GB | Turbo only |
| `krea2_turbo_nvfp4` | 7.7 GB | Turbo only; Blackwell-class hardware |
| `qwen3vl_4b_bf16` / `_fp8_scaled` | 8.9 / 5.2 GB | text encoder |
| `qwen_image_vae` | 0.25 GB | |

**Community GGUF** — the ecosystem formed without city96 this time: `gguf-org/krea-2-gguf`, `vantagewithai/Krea-2-Turbo-GGUF` and `-Raw-GGUF`, `molbal/krea2-gguf`, `realrebelai/KREA-2_GGUFs`. vantagewithai sizes: Q2_K 4.9 GB, Q4_K_M 7.5 GB, Q6_K 10.6 GB, Q8_0 13.7 GB. Requires the `ComfyUI-GGUF` custom node (GGUF DiTs load via its loader, not `UNETLoader`). **No per-quant quality comparison has been published yet** — the table below is size arithmetic plus the general GGUF experience from sibling models, not measured Krea-2 craft:

| VRAM | Working setup |
|---|---|
| 8–12 GB | GGUF Q2–Q4 DiT + fp8 encoder (or encoder on CPU) — expect quality loss at Q2/Q3 |
| 12–16 GB | Q4_K_M–Q6_K, or nvfp4 (7.7 GB) on Blackwell |
| 16–24 GB | fp8_scaled or int8_convrot (13.1–13.5 GB) + fp8 encoder — the comfortable tier |
| 24 GB+ | fp8/int8 with full headroom; bf16 wants ~46 GB (unified/多-GPU territory) |

The memory pattern that matters (documented for musubi, same physics in ComfyUI): the DiT stays resident; the ~5–9 GB encoder and the VAE shuttle on/off the GPU around it. On a 24 GB card, fp8 (or block offloading) is what buys the headroom for the encode/decode — not evacuating the DiT [official — musubi docs]. Koboldcpp's rolling build also runs Krea 2 (with Qwen3-VL + a Wan 2.1 VAE) [community — u/Eisenstein, HN].

## 3. The reference CLI

`github.com/krea-ai/krea-2` (Apache-2.0, `uv sync`; set `OSS_RAW` / `OSS_TURBO` env vars to the downloaded `raw.safetensors` / `turbo.safetensors` from the `krea/Krea-2-Raw` / `krea/Krea-2-Turbo` HF repos):

```bash
# Raw — full sampler with CFG; trained to 1K
uv run inference.py "a fox walking in the snow" --checkpoint oss_raw --steps 52 --cfg 3.5
# Turbo — 8 steps, CFG off, pinned mu; 1K–2K
uv run inference.py "a fox walking in the snow" --checkpoint oss_turbo --steps 8 --cfg 0.0 --mu 1.15 --width 2048 --height 2048
```

Flag defaults: `--steps 28`, `--cfg 4.5` (0 disables), `--y1 0.5` / `--y2 1.15` (resolution-interpolated time shift; `--mu` pins a constant — recommended 1.15 for Turbo), dimensions padded to multiples of 16, `--seed 0` with image *i* using seed+*i* [official — README]. Note the CFG numbers are Krea-convention (0 = off).

## 4. diffusers

Requires **diffusers from source** as of early July 2026 (docs are on `main`; check pypi before assuming a stable release carries it):

```python
import torch
from diffusers import Krea2Pipeline

pipe = Krea2Pipeline.from_pretrained("krea/Krea-2-Raw", torch_dtype=torch.bfloat16).to("cuda")
image = pipe("a fox in the snow", height=1024, width=1024,
             num_inference_steps=52, guidance_scale=3.5,      # Raw HF-card settings; diffusers class default is 28 / 4.5
             generator=torch.Generator("cuda").manual_seed(0)).images[0]
```

- Classes: `Krea2Pipeline` / `Krea2Transformer2DModel` / `AutoencoderKLQwenImage` / `Qwen3VLModel` (+ `text_encoder_select_layers` — the 12-layer tap indices).
- **Turbo:** `is_distilled=True` in the pipeline config → fixed `mu=1.15`; run `num_inference_steps=8, guidance_scale=0.0`.
- **Guidance convention:** velocity = `cond + g·(cond − uncond)`; g>0 enables guidance; equals classic CFG at `1+g`. `negative_prompt` is ignored when `g ≤ 0`.
- Scheduler: `FlowMatchEulerDiscreteScheduler`, `use_dynamic_shifting=True`, `base_shift=0.5`, `max_shift=1.15`, `base_image_seq_len=256`, `max_image_seq_len=6400`.
- `max_sequence_length=512`; dims rounded to ×16. **t2i only** — no img2img/inpaint/edit pipeline classes yet.
- The HF repos carry a full diffusers layout (`transformer/`, `text_encoder/`, `vae/`, `scheduler/`, `model_index.json`) alongside the single-file checkpoints.

## 5. The Wan 2.1 VAE swap

The single highest-leverage quality fix for the soft/airbrushed default and the halftone/dark-noise artefacts: decode through the **Wan 2.1 VAE (FP32)** instead of `qwen_image_vae`. Reported independently as "solves this" for the blur complaint [community — mobiuscog, HN] and adopted in the best-documented realism workflow [community — nsfwVariant, Civitai]. Mechanics: drop the Wan 2.1 VAE file into `models/vae/` and point the `VAELoader` at it — the latent spaces are compatible enough for decode; you're changing the renderer, not the model. Keep the Qwen VAE for encode-side operations (img2img-style passes) to stay conservative, and A/B the swap on your own content — this is community craft, not an official configuration. It is not a cure-all: moiré/halftone artefacts on hair and clothing are reported *on the Wan VAE too*, notably on community checkpoint merges (Fascium-class) even with all LoRAs off [community — derTommygun, r/StableDiffusion] — when that happens on a merge, re-test the stock checkpoint before debugging settings.

## 6. Using LoRAs

- **Node:** `LoraLoaderModelOnly` — Krea 2 LoRAs are DiT-only (the encoder is never trained; encoder-class doctrine). GGUF DiT + LoRA works through the same node.
- **Official style LoRAs:** strengths 0.8–1.0, natural-phrase triggers auto-appended by the template (`prompting-guide.md §5` has the verbatim table).
- **The official Turbo LoRA:** `loras/krea2_turbo_lora_rank_64_bf16.safetensors` in Comfy-Org/Krea-2 — the Turbo distillation *as a rank-64 LoRA*. Applied over **Raw**, it turns Raw into a few-step model; at partial strength it blends distillation speed with Raw's diversity. This is the enabling piece of the two-stage recipe below.
- **Trained LoRAs:** train on Raw, apply on Turbo (the official doctrine — `lora-training.md`); character LoRAs commonly hold identity at ~0.8 while stacking with style LoRAs [community — JahJedi]. Sweep 0.6–1.0 per LoRA; there's no established per-type weight table yet (two-week-old ecosystem — expect this to firm up).
- **Slider/utility LoRAs** are already appearing (e.g. a Detail Slider on Civitai) — treat weights per the author's card.

## 7. Multi-stage workflows

### 7a. The two-stage Raw+Turbo-LoRA recipe (the best-documented local workflow)

[community — nsfwVariant, Civitai "Krea 2 simple gen workflow for high quality realism", incl. the author's write-up; their claim: "WAY better" photoreal than stock Turbo]

| Stage | Model | Settings | Purpose |
|---|---|---|---|
| 1 — compose | **Raw + Turbo-LoRA @ 0.6** | 6 steps, `res_2s` / `beta`, full denoise | deliberately *undercooked* — keeps Raw's expressiveness and texture diversity, dodges the safety-tuned polish |
| 2 — finish | same | 2 steps, `deis_3m` / `bong_tangent`, **denoise 0.2** | resolves the undercooked noise without re-imposing the default look |
| decode | **Wan 2.1 FP32 VAE** | — | the §5 swap |

Author's companion numbers: int8 convrot quant; cfg 2.0 variant when negatives are needed (2× time).

### 7b. Alternative sampler ladders (stock Turbo)

[community — RaymondLuxuryYacht, Civitai "RLY Basic Photorealism"]: `res_2s`/`beta` at **4–5 steps** for maximum texture; `er_sde`/`simple` at **4–9 steps** for a cleaner look. Past 8 steps, gains are minimal at 1024 [community — liutyi, tested to 12] — but at higher resolutions the step economy shifts: `euler_ancestral`/`simple` at **15 steps, 1536×1792, cfg 1** (alternate: `uni_pc_bh2`, seeds batch of 2) is a named daily-driver [community — m0ran1's sampler thread, r/StableDiffusion]. LoRA loading note: each active LoRA adds ~5–10 s per generation on Turbo (reported on int8 + rgthree Power Lora stacking) — more noticeable against an 8-step base than it ever was on slower models [community — rarezin, r/comfyui].

### 7b'. Low-VRAM pixel-space ladder

For weak GPUs, generate at **512×512 and upscale in pixel space with realESRGAN 2×** instead of rendering native-res — Mr Flow-style nodes adapted for Krea-2/ZIT keep detail while cutting compute [community — MFGREBEL, `RealRebelAI/Rebels_MrFlow`, workflows in repo].

### 7c. The full production ladder

[community — lonecatone23's "Pro Grade" workflow, generalised]: caption/enhance (abliterated local LLM) → base gen → detailer-daemon sampling → **SAM3 face/eye detailers** → `UltimateSDUpscale` at low denoise with simplified prompt → post FX. The character-LoRA swap belongs at the detailer stage, not the base gen (`characters.md §4`). Note the author's own honesty: the workflow's image-edit stage underperforms — there is no real edit model yet.

## 8. Krea 2 in mixed-model pipelines

Krea 2's role: **aesthetics/composition front-end** — widest stylistic range, strong anatomy/animals/wide-aspect [community — nsfwVariant's comparison]. Its finishing partners:

- **Z-Image as the face/detail finisher and repair-inpainter.** Z-Image Base beats Krea 2 on facial expressiveness and hair at ~8× the generation time; the efficient split is Krea 2 for the scene, Z-Image for the face pass. Krea 2's characteristic artefact zones (hair strands, fine repeating patterns, halftone-prone fabric, dark-area noise) inpaint cleanly with **Z-Image at denoise ~0.2** [community — nsfwVariant]. Paired LoRA releases (same style, Krea-2 + Z-Image-Turbo versions) are already a Civitai pattern — the community treats them as a standard pairing.
- **Wan 2.1 VAE** (§5) is itself a cross-family graft — renderer from one family, generator from another.
- **Handoff rule** (suite-standard): **VAE-decode to pixels between model families** — Qwen-Image-VAE latents are not Z-Image/SDXL/Flux latents. Identity-preserving refines live at denoise ~0.2–0.5; 0.2 is the Krea2→Z-Image repair number above.
- No hosted↔open handoff subtlety is documented yet, but remember hosted Large renders through the FLUX.2 VAE — hosted and local outputs of "the same model" won't match pixel-level.

Cross-model craft in depth (denoise bands, resolution matching, color management, workflows-as-code): the **`image-production-workflows`** skill.
