# Krea 2 — Official-sources research report

Gathered 2026-07-06 by web-research subagent (official/primary sources only). Staged for the krea-2 skill; nothing here is published.

## 0. Verdict: what "Krea 2" is

**Krea 2 exists and is an IMAGE model** (text-to-image, not video) — Krea's "first foundation model built completely from scratch and focused on aesthetics and creative control" [official, https://www.krea.ai/blog/krea-2-image-model]. It is **dual-natured**: hosted proprietary variants (Medium/Large) on krea.ai + API, AND **open weights** (Raw/Turbo) on HuggingFace since June 2026.

## 1. Identity & release timeline

- **Name**: Krea 2 (also "K2"). By Krea.ai, Inc.
- **Announced**: May 12, 2026 [official, https://www.krea.ai/blog/krea-2-image-model]. (Pro users May 15, GA May 18 — via aggregated search summaries, medium confidence.)
- **fal API partner launch**: May 27, 2026 [official press release, https://www.prnewswire.com/news-releases/fal-launches-krea-2-as-an-official-api-partner-bringing-kreas-first-foundation-image-model-to-developers-302783543.html]
- **Open weights released**: v1.0, June 22, 2026 (HF model cards); **Technical report**: June 23, 2026 [official, https://www.krea.ai/blog/krea-2-technical-report]
- **Relationship to predecessors**: "first foundation model built completely from scratch" — distinct from Krea 1 (mid-2025) and FLUX.1 Krea [dev] (a BFL FLUX fine-tune). No official Krea 1 → Krea 2 comparison document found.

## 2. Architecture [official: tech report + HF diffusers docs + krea-2-open-source page]

- **Type**: flow-matching text-to-image, **single-stream MMDiT**, "12B dense DiT backbone" [official, https://www.krea.ai/krea-2-open-source]; model cards say "Diffusion Transformer with 12 billion parameters" [official, https://huggingface.co/krea/Krea-2-Raw]. (Secondary summaries cite 12.9B, 28 blocks, width 6144 — treat as unconfirmed detail.)
- **Blocks**: single-stream ("for the sake of simplicity"), SwiGLU MLPs 4x, grouped-query attention with gated sigmoid attention, zero-centered RMSNorm, 3D axial RoPE (frame/h/w), per-block tunable bias replacing AdaLN-MLP [official, https://www.krea.ai/blog/krea-2-technical-report]
- **Text encoder**: **Qwen3-VL** (ComfyUI/diffusers ship `Qwen/Qwen3-VL-4B-Instruct`-class, 4B). Novel conditioning: hidden states tapped from **twelve decoder layers per token**, fused by a small text-fusion stage ("dynamically select coarse-to-fine text representations") [official, https://huggingface.co/docs/diffusers/main/en/api/pipelines/krea2 + tech report]
- **VAE**: **Qwen-Image VAE** (f8, 16 latent channels) for the open-weights models [official, diffusers docs]. Tech report: Qwen Image VAE for early models, **FLUX 2 VAE for "larger final models"** (i.e. hosted Large likely differs) [official, tech report]
- **Training**: rectified-flow v-parameterization; 256→512→1024px curriculum; no synthetic data in pretraining; SFT on hand-curated aesthetic set; preference optimization; multi-reward GRPO RL; iREPA, 8-bit training [official, tech report]
- **Turbo distillation**: **Trajectory Distribution Matching (TDM)**, guidance + timestep distillation → 8 steps, CFG off [official, tech report]
- **Resolution**: 1024–2048 px (inference repo `--width/--height 1024-2048`); Turbo demonstrates 2048×2048; native 2K–4K listed as future work [official, https://github.com/krea-ai/krea-2 + tech report]
- **Benchmark claim**: "among the top 10 models on the Artificial Analysis leaderboard for text-to-image, and scores 2nd place among models from independent labs" [official, tech report]

## 3. Weights & license

- **Open weights**: YES — `krea/Krea-2-Raw` (`raw.safetensors`, 26.3 GB, repo 62 GB, with `text_encoder/`, `transformer/`, `vae/`, `scheduler/`, `model_index.json` diffusers layout) and `krea/Krea-2-Turbo` (`turbo.safetensors`) [official, https://huggingface.co/krea/Krea-2-Raw, https://huggingface.co/krea/Krea-2-Turbo]
- **Code**: Apache-2.0 (github.com/krea-ai/krea-2). **Weights**: "Krea 2 Community License" (LICENSE.pdf) [official, GitHub README]
- **License key terms** [official, https://www.krea.ai/krea-2-licensing]: free commercial use up to **50 seats**; commercial use permitted only if company-wide annual revenue **< $1,000,000**; >50 seats / SSO / SLA / DPA ⇒ enterprise license (contact opensource@krea.ai); **deployers must implement input/output classifiers or equivalent content filtering**; users own outputs — "users are solely responsible for their outputs"; Krea claims no copyright over generated content [official, HF README]
- **Style LoRA collection**: https://huggingface.co/collections/krea/krea-2-loras [official]

## 4. Variants

| Variant | Nature | Access |
|---|---|---|
| **Krea 2 Raw** | undistilled base, "not recommended for inference use"; for fine-tuning/LoRA | open weights [official, HF] |
| **Krea 2 Turbo** | 8-step TDM-distilled, CFG=0 | open weights + fal + web app [official] |
| **Krea 2 Medium** | hosted-only, "stable, general-purpose" | krea.ai app + API + fal + ComfyUI API nodes [official] |
| **Krea 2 Large** | hosted-only, photorealism, "richest output" | same [official] |

- ComfyUI-optimized files: `Comfy-Org/Krea-2` — `krea2_turbo_fp8_scaled.safetensors`, **`krea2_raw_int8_convrot.safetensors`**, `qwen3vl_4b_fp8_scaled.safetensors` (+ bf16), `qwen_image_vae.safetensors`, `loras/` (e.g. `krea2_darkbrush.safetensors`) [official, https://huggingface.co/Comfy-Org/Krea-2]
- LoRA doctrine: "Train LoRAs on Krea 2 RAW, then apply them on Krea 2 Turbo. LoRAs trained on RAW are designed to express strongly on Turbo." [official, https://www.krea.ai/krea-2-open-source]. Trainers: diffusers, Ostris ai-toolkit, fal trainer (`fal-ai/krea-2-trainer`), kohya musubi-tuner (community) [official, GitHub README]

## 5. Stock inference settings [official]

- **Raw**: 52 steps, cfg 3.5 (`--checkpoint oss_raw --steps 52 --cfg 3.5`); diffusers `num_inference_steps=52, guidance_scale=3.5` [HF card + GitHub]
- **Turbo**: 8 steps, cfg 0.0, **mu=1.15** (fixed timestep shift), up to 2048×2048 [GitHub + HF card]
- **Base/midtrain diffusers default**: 28 steps, guidance 4.5 [diffusers docs]
- **CFG convention caveat**: velocity = `cond + guidance_scale*(cond − uncond)`; equals classic CFG scale `1 + guidance_scale`; guidance on when >0 [official, diffusers docs]
- Scheduler: `FlowMatchEulerDiscreteScheduler`, `use_dynamic_shifting=True`, `base_shift=0.5, max_shift=1.15, base_image_seq_len=256, max_image_seq_len=6400`; resolution-aware exponential time shift; max_sequence_length=512; dims rounded to multiple of 16 [official, diffusers docs]

## 6. diffusers

- Pipeline: **`Krea2Pipeline`**; transformer `Krea2Transformer2DModel`; VAE `AutoencoderKLQwenImage`; text encoder `Qwen3VLModel`; `is_distilled=True` for Turbo (fixed mu=1.15); `text_encoder_select_layers` tuple. **Requires diffusers from source** (docs "main"; note "no hub repo yet" for converted layout in docs, though HF cards show `from_pretrained("krea/Krea-2-Raw")`) [official, https://huggingface.co/docs/diffusers/main/en/api/pipelines/krea2]

## 7. ComfyUI [official]

- Tutorial: https://docs.comfy.org/tutorials/image/krea/krea-2; template `image_krea2_turbo_t2i.json` in Comfy-Org/workflow_templates; announcement https://blog.comfy.org/p/krea-2-open-source-models-are-now
- File placement: `krea2_turbo_fp8_scaled.safetensors` → `models/diffusion_models/`; `qwen3vl_4b_fp8_scaled.safetensors` → `models/text_encoders/`; `qwen_image_vae.safetensors` → `models/vae/`; style LoRAs → `models/loras/`
- **Template JSON stock settings**: KSampler steps **8**, cfg **1.0**, sampler **euler**, scheduler **simple**, denoise 1; 1024×1024 default; **no shift node**; `LoraLoaderModelOnly` strength 0.8 (recommended 0.8–1.0); prompt-enhancement TextGenerate node **enabled by default**; subgraph layout with ResolutionSelector (1K–2K) and CustomCombo trigger-word LoRA picker [official, https://github.com/Comfy-Org/workflow_templates/blob/main/templates/image_krea2_turbo_t2i.json]
- Hosted **Medium/Large via Partner/API nodes** ("Krea 2 Image node", May 27, 2026): style refs, moodboard IDs, creativity Raw/Low/Medium/High [official, https://blog.comfy.org/p/krea-2-image-is-now-available-via]

## 8. Krea API & web app [official]

- **Krea API** (https://www.krea.ai/docs/developers/krea-2/overview): base `https://api.krea.ai`; `POST /generate/image/krea/krea-2/medium|large`; async job → poll `/jobs/{job_id}` or webhook. Params: `prompt`, `aspect_ratio` (1:1, 4:3, 3:2, 16:9, 2.35:1, 4:5, 2:3, 9:16), `resolution` ("1K only currently"), `creativity` (raw/low/medium[default]/high), `seed`, `image_style_references` (≤10 on hosted API, w/ strength), `moodboards` (max 1), `styles` (LoRA presets, ≤10), sliders `intensity`/`complexity`/`movement` (−100..100, default 0). **Pricing**: Medium $0.030/img ($0.035 w/ srefs, $0.040 w/ moodboards); Large $0.060/$0.065/$0.070.
- **Web app** (https://www.krea.ai/docs/user-guide/features/krea-2): pick Medium/Large/Turbo; up to **4 style references each with strength slider**; moodboards = "the most precise way to set a visual direction"; batch up to 4; 1K output.
- **fal** [official-via-host]: `fal-ai/krea-2/turbo` (image_size presets/custom, `enable_prompt_expansion`, acceleration none/regular, safety checker, png/jpeg), `fal-ai/krea-2/turbo/lora`, `fal-ai/krea-2-trainer`, plus hosted `krea/v2/medium|large/text-to-image` [https://fal.ai/models/fal-ai/krea-2/turbo/api]. Other listed partners: SGLang (cookbook docs.sglang.io/cookbook/diffusion/Krea/Krea-2), Replicate, Cloudflare, Together, GCP, AWS, Runware [official list, krea-2-open-source page].

## 9. Prompting & aesthetic positioning [official]

- Thesis: "Style should not be a vague prompt word. It should be something you can guide, mix, strengthen, reduce, and push." Model is "raw, flexible, unopinionated, and unconstrained. Something that you can break if you want to." [blog announcement]
- Anti-default-look claim: "Instead of optimizing only for a single polished default, Krea 2 is designed to expose a broad visual space" [tech report]. Creativity=**raw** "renders only explicit descriptions without expansion"; high takes "meaningful creative liberty" [user guide].
- **Prompt expander**: LLM trained with SFT+RL (image-level quality rewards + prompt-level faithfulness rewards); exposed as `enable_prompt_expansion` (fal) / prompt-enhancement node (ComfyUI, on by default) [tech report].
- Style-ref system: "smooth semantic mixing of multiple styles," continuous per-reference strength, "state-of-the-art adherence to complex styles" [tech report]. Official prompting doc: https://github.com/krea-ai/krea-2/blob/main/docs/prompting.md (long detailed prompts fine; quote marks around text-to-render).

## Gaps / cautions

- Param count discrepancy (12B official cards vs 12.9B in secondary summaries) — verify against tech report directly before publishing.
- Raw's ComfyUI workflow settings (52-step template variant) not confirmed from template JSON — only Turbo template inspected.
- Krea hosted API currently 1K-only resolution; open-weights Turbo does 2K.
- Hosted Medium/Large likely use FLUX 2 VAE per tech report ("larger final models") — architecture of hosted ≠ open weights.
