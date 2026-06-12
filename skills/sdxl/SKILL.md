---
name: sdxl
description: >
  Authoritative guide for Stable Diffusion XL (SDXL 1.0, Stability AI) and its ecosystem — base + refiner, the distilled fast variants (Turbo, Lightning, LCM, Hyper-SDXL), and the community finetunes (Juggernaut, RealVisXL, DreamShaper, Pony, Illustrious/NoobAI) — in ComfyUI or the diffusers API. Use this whenever the user touches SDXL in any way, even obliquely: choosing a checkpoint or fast variant (base vs Turbo vs Lightning vs LCM vs Hyper, or which photoreal/anime finetune), installing or setting it up in ComfyUI (single-checkpoint loader, the fp16-fix VAE, file layout, base+refiner ensemble graph), writing or fixing prompts (SDXL is a dual-CLIP 77-token model — weighted comma-separated keyword phrases, not LLM sentences and not generic "masterpiece 8k"; matching the prompt dialect to the checkpoint; the text_g/text_l split; negative prompts and CFG), getting photoreal results (use a photoreal finetune, then stack camera body + film stock + lens + lighting vocabulary), choosing steps/CFG/sampler/scheduler/resolution per variant, running ControlNet / IP-Adapter / LoRA, training a LoRA (kohya_ss / OneTrainer) including style LoRAs (the Illustrious recipe, dataset diversity, XY-grid evaluation), creating a consistent character (InstantID vs IP-Adapter FaceID vs HyperLoRA vs a trained character LoRA, the detailer LoRA swap, ADetailer [SEP] multi-character routing, block-weighted LoRA to stop style bleed), building multi-stage production pipelines (hires-fix, tiled upscale, detailers) or using SDXL as the controllable front-end / texture back-end in mixed-model workflows, or debugging artefacts (fried colours, cut-off heads, plastic skin, mangled hands, unreadable text). It also covers the licence picture (OpenRAIL++-M is commercially clean; Turbo's licence is contested).
---

# Stable Diffusion XL (SDXL)

SDXL 1.0 is Stability AI's open-weights latent-diffusion model (released July 2023). It is a **convolutional UNet — not a DiT** — with a **2.6B-parameter UNet backbone**; the full **base + refiner "ensemble of experts" pipeline is ~6.6B parameters**. It uses **two fixed CLIP text encoders working together** — **CLIP-ViT/L** ("CLIP-L") and **OpenCLIP-ViT/bigG** ("CLIP-G") — whose penultimate hidden states are concatenated to a 2048-dim conditioning, plus the pooled bigG embedding fed to the timestep. Native **1024×1024**. Licence: **CreativeML Open RAIL++-M** (commercial use permitted).

Its defining trait, and the thing that dates it: **it is a CLIP-conditioned UNet, not an LLM/T5-conditioned transformer.** That means a hard **77-token** prompt window, keyword/tag-style prompting rather than sentences, no reliable in-image text, and weaker compositional understanding than transformer-based models with LLM text encoders. In exchange it has the **deepest ecosystem of any open model** — thousands of finetunes, LoRAs, ControlNets, and IP-Adapters — runs on **6–8 GB VRAM**, and is fast. You almost never run base SDXL raw; you run a finetune of it.

## Two orthogonal axes — they compose

SDXL choices fall on **two independent axes that stack**:

- **Speed** — base (full quality) vs a distilled fast variant (Turbo / Lightning / LCM / Hyper-SDXL), trading steps for seconds.
- **Style / dialect** — which checkpoint: raw base, a photoreal finetune (Juggernaut, RealVisXL), an art generalist (DreamShaper), or an anime/booru model (Pony, Illustrious/NoobAI).

They are **composable**: Lightning, LCM, and Hyper-SDXL all ship as **LoRAs** that drop onto *any* SDXL finetune — so "Juggernaut + 4-step Lightning LoRA" gives you fast *and* photoreal in one stack. Pick a point on each axis.

### Speed variants (the fast axis)

| Variant | Method | Steps | CFG (ComfyUI / diffusers) | Sampler · Scheduler | Native res | Licence | Use when… |
|---|---|---|---|---|---|---|---|
| **Base 1.0** | — | 25–40 | 5–8 / 5.0–8.0 | `euler` · `normal` | 1024² | OpenRAIL++-M | final quality, max control, LoRA training base |
| **Base + Refiner** | ensemble of experts | 25 (split ~0.8) | 8 / 5.0 | `euler` · `normal` | 1024² | OpenRAIL++-M | squeeze extra high-frequency detail (optional; finetunes make it redundant) |
| **Turbo** | ADD | 1–4 | **1** / **0.0** | `euler_ancestral` · `SDTurboScheduler` | 512² | contested ¹ | real-time preview / drafting |
| **Lightning** | progressive + adversarial distil | 2 / 4 / 8 | **1** / **0.0** | `euler` · `sgm_uniform` | 1024² | OpenRAIL++-M | fast at 1024², commercially clean; **LoRA or full ckpt** |
| **LCM** | latent consistency | 4–8 | **1–2** / **1.0–2.0** | `lcm` · `sgm_uniform` | 1024² | OpenRAIL-ish | fast on *any* finetune (LCM-LoRA); needs `ModelSamplingDiscrete`→`lcm` |
| **Hyper-SDXL** | TSCD + reward | 1 / 2 / 4 / 8 | ~1 / ~0.0 | `euler` · `sgm_uniform` | 1024² | OpenRAIL++-M | best-rated 1-step; **LoRA or full ckpt** |

> ¹ **Turbo's licence is contested** — see *Licence & limitations*. **CFG note (read this):** for every distilled variant, "guidance off" is **CFG `1.0` in a ComfyUI sampler** and **`guidance_scale=0.0` in diffusers**. They are the same thing. **Never type CFG `0.0` into a ComfyUI sampler** (it outputs the unconditional and ignores your prompt). At guidance-off, **negative prompts are inert** (see *The one rule* and *Failure modes*).

### Checkpoints (the style axis) — you want a finetune, not raw base

Base SDXL 1.0 is a strong *foundation* but looks undertrained/plasticky next to its finetunes. For real work, start from one of these (all **community tier** — verify current versions and licences on the model page):

| Checkpoint | For | Prompt dialect |
|---|---|---|
| **Juggernaut XL** | all-purpose **photoreal** — the default "just works" pick | descriptive photo-keywords (this skill's default) |
| **RealVisXL** | **maximum photorealism**, portraits, skin/hair | descriptive photo-keywords |
| **DreamShaper XL** | artistic / fantasy / concept-art generalist | descriptive keywords, looser |
| **Pony Diffusion V6 XL** | anime/furry/cartoon, very flexible, own sub-ecosystem | **`score_9, score_8_up, …` + `source_*` + booru tags** — normal prompts fail |
| **Illustrious / NoobAI XL** | anime/illustration powerhouse | **Danbooru booru tags** |

> **Dialect follows the checkpoint.** Pony and Illustrious were trained on tag vocabularies and need their own dialect; their LoRAs are a **separate pool** incompatible with base-SDXL LoRAs. Everything else in this skill assumes the photoreal/base dialect unless noted. Details and current-version notes: `references/checkpoints-and-loras.md`.

---

## The one rule that changes everything

SDXL is conditioned by CLIP, which matches **tokens and short phrases**, not syntax. So **write a weighted, comma-separated list of keyword phrases — front-loaded, within ~77 tokens — and match the dialect to your checkpoint.** This is the opposite of the LLM-encoder models: don't write a flowing sentence (CLIP can't parse clause structure the way LLM-encoder models do), and don't lean on a generic `masterpiece, best quality, 8k` booster block (near-useless on SDXL — earn quality with concrete photographic terms instead). The encoder class also flips the LoRA rules: SDXL triggers are **verbatim rare tokens** (CLIP tag-matching) and training captions are tags — where Flux/Z-Image fold triggers into prose or omit them. Dialect, triggers, and captions all follow the encoder, not folklore.

| Don't (LLM-style) | Don't (empty booster) | Do (SDXL keyword phrases) |
|---|---|---|
| *A candid documentary photograph of a young woman standing alone in a sunlit kitchen…* | `1girl, masterpiece, best quality, 8k, ultra detailed` | `candid documentary photo, young woman, detailed skin, standing in a sunlit kitchen, soft window light, 35mm, shot on Fujifilm X-T4, Kodak Portra 400` |

Four mechanics that follow from the CLIP encoder:

1. **Position = emphasis.** CLIP weights earlier tokens more. Put subject + the 2–3 highest-value concepts first.
2. **Weighting syntax** is `(phrase:1.2)` — raise toward 1.3, lower toward 0.9. **SDXL fries faster than SD1.5**: keep weights in **~1.05–1.3**; the 1.5–1.8 values common in SD1.5 guides over-saturate and posterise SDXL.
3. **77 tokens per chunk.** Past ~77 tokens prompt-weight falls off a cliff. Keep it tight; if you genuinely need more, split with `BREAK` (ComfyUI/A1111) so each chunk is encoded separately.
4. **Dialect by checkpoint** — photoreal keywords for base/Juggernaut/RealVis; `score_*`/`source_*` for Pony; booru tags for Illustrious/anime.

**Advanced lever — the dual-encoder split.** SDXL has two text encoders, and the **`CLIPTextEncodeSDXL`** node lets you feed them different text (`text_g` → OpenCLIP-bigG, the global/scene channel; `text_l` → CLIP-L, the local/detail channel). The **stock ComfyUI base and base+refiner templates use the plain `CLIPTextEncode` node** (same text to both) — the split is an *optional* power-user technique, not the default path. Use it when you want scene vs detail steered separately (e.g. global mood in `text_g`, specific object/texture detail in `text_l`).

Full prompt anatomy, the complete photoreal vocabulary (camera bodies, film stocks, lenses, lighting, photographer names), the Pony/booru dialects, negatives, and worked SDXL-calibrated examples: **`references/prompting-guide.md`**.

---

## Setup & ecosystem

SDXL runs in **ComfyUI core** with no custom nodes. Unlike the DiT models, the checkpoint is a **single file that bundles UNet + both CLIP encoders + VAE** — load it with one **`CheckpointLoaderSimple`** node, which outputs `MODEL`, `CLIP`, and `VAE`.

**File layout** (download from the Stability HF repos):

| File | ComfyUI folder | Loader node |
|---|---|---|
| `sd_xl_base_1.0.safetensors` (~6.94 GB) | `models/checkpoints/` | CheckpointLoaderSimple |
| `sd_xl_refiner_1.0.safetensors` (~6.08 GB) | `models/checkpoints/` | CheckpointLoaderSimple |
| `sdxl_vae.safetensors` / `sdxl-vae-fp16-fix` (~335 MB) | `models/vae/` | VAELoader (optional override) |
| any finetune / fast-variant checkpoint | `models/checkpoints/` | CheckpointLoaderSimple |
| LoRAs (incl. Lightning/LCM/Hyper LoRAs) | `models/loras/` | LoraLoader |

**The VAE gotcha:** SDXL's original VAE **overflows in fp16 and produces black/NaN images**. The VAE baked into the checkpoint is fine and the stock templates use it. But if you decode in fp16 with a standalone VAE, point a `VAELoader` at **`madebyollin/sdxl-vae-fp16-fix`** (or run the VAE in fp32). Black outputs = this.

**Stock node settings (verbatim from the official `sdxl_simple_example.json` template):**
- **Base:** `EmptyLatentImage` **1024×1024**; `KSamplerAdvanced` → **steps 25, cfg 8, sampler `euler`, scheduler `normal`**, `start_at_step 0`, `end_at_step 20`, `return_with_leftover_noise enable`.
- **Refiner (ensemble):** a second `KSamplerAdvanced` with **`add_noise disable`**, **steps 25, cfg 8, `euler`/`normal`**, `start_at_step 20`, `end_at_step 10000`. The **20/25 = 0.8 split** means base runs 0→0.8 and the refiner finishes 0.8→1.0 on the *same* 25-step schedule, continuing the base's leftover-noise latent (no fresh noise, no decode in between).
- Recommended SDXL resolutions (from the template's note): **1024×1024 · 1152×896 · 896×1152 · 1216×832 · 832×1216 · 1344×768 · 768×1344 · 1536×640 · 640×1536** (all ≈1 MP, multiples of 64). 512² gives badly degraded output — unlike SD1.5, do not go below the 1024-area buckets.

**diffusers:** pipelines are **`StableDiffusionXLPipeline`** (t2i), **`StableDiffusionXLImg2ImgPipeline`** (img2img / the refiner pass), **`StableDiffusionXLInpaintPipeline`** (inpaint). Minimum **diffusers ≥ 0.19.0**. The base+refiner ensemble is wired with `denoising_end=0.8` on the base and `denoising_start=0.8` on the refiner (handing off latents). Full code: `references/setup-and-workflows.md`.

**Quantisation — there is effectively no GGUF path for SDXL.** It's a **Conv2D-heavy UNet**, and GGUF/DiT quantisation is built for transformer models; the `ComfyUI-GGUF` author explicitly says *don't quantise SDXL*. fp16 is the standard format (~6.5 GB), with optional `--fp8_e4m3fn-unet` weight-casting in ComfyUI for tight VRAM. ComfyUI auto-offloads, so 1024² runs on ~**4 GB** (low-VRAM), **6–8 GB comfortable**; base+refiner keeps both checkpoints resident, so budget **8 GB+**.

ControlNet, IP-Adapter (incl. FaceID), hires-fix and tiled-upscale workflows are all mature for SDXL — this control depth is its biggest practical edge. See `references/setup-and-workflows.md` and `references/checkpoints-and-loras.md`.

---

## Per-variant settings

One compact block per variant. Numbers are from the official templates/model cards (primary) except where flagged community.

- **Base 1.0** — steps **25–40** (30–40 sweet spot), **CFG 5–8** (template uses 8; finetunes often prefer 3–7), `euler`/`normal`, 1024-area bucket. **Use negative prompts.** Best LoRA-training base.
- **Base + Refiner** — total **steps 25**, hand off at **0.8** (base 0→20, refiner 20→25), **CFG 8**, `euler`/`normal`. Refiner adds high-frequency detail only; *optional* and largely redundant once you use a good finetune.
- **Turbo** — **1–4 steps**, **CFG 1** (ComfyUI) / **0.0** (diffusers), **`euler_ancestral`** via `SamplerCustom`, scheduler **`SDTurboScheduler`** (`steps`, `denoise 1`), **512²**. Negatives inert. 1 step usable, 4 better.
- **Lightning** — **2 / 4 / 8 steps** (match the checkpoint/LoRA to the step count), **CFG 1** / **0.0**, **`euler`**, **`sgm_uniform`**, 1024². Full ckpt or UNet > LoRA quality; use the **LoRA** to add speed onto a *custom finetune*. 1-step is experimental; 2-step the floor, 4-step the popular default.
- **LCM** — **4–8 steps**, **CFG 1–2** / **1.0–2.0**, sampler **`lcm`**, **`sgm_uniform`**. **LCM-LoRA** applies to any SDXL finetune but requires a **`ModelSamplingDiscrete`** node set to **`lcm`** patched onto the model. Softer than Lightning/Hyper but the most portable.
- **Hyper-SDXL** — **1 / 2 / 4 / 8 steps**, **CFG ~1** / **~0.0**, **`euler`**, **`sgm_uniform`**, 1024². LoRA or full ckpt; often the best **1-step** quality of the fast variants.

---

## Realism: pick a finetune, then stack the gear

SDXL reaches photoreal by the **gear-stacking route** — concrete photographic vocabulary piled on top of a photoreal finetune. Two levers, in order of impact:

1. **Use a photoreal finetune, not base.** This is the single biggest lever — **Juggernaut XL** or **RealVisXL** outclass raw base SDXL on skin, light, and anatomy before you change a single prompt word.
2. **Stack concrete photographic vocabulary** — earn realism with specifics, not adjectives. Build the prompt from these slots (full vocabulary tables in `references/prompting-guide.md`):
   - **Style tag first:** `candid photo`, `documentary photography`, `glamour photography`, `analog photo`, `polaroid`…
   - **`detailed skin`** — the highest-value realism keyword on SDXL finetunes (adds pores, texture; kills the plastic look).
   - **Camera body:** `shot on Canon EOS 5D`, `Fujifilm X-T4`, `Hasselblad X1D II`, `ARRI ALEXA 65`, `RED digital cinema`…
   - **Film stock:** `Kodak Portra 400` (flattering skin), `Cinestill 800T` (halation), `Ektar 100` (saturated), `Tri-X 400` (B&W), `Fujicolor Pro`…
   - **Lighting:** name source + quality + direction — `soft window light from camera-left`, `golden hour rim light`, `harsh direct flash`, `chiaroscuro single source`.
   - **One imperfection / texture anchor:** `film grain`, `slight vignette`, `subsurface scattering`, `visible skin pores`.

   Keep effect/style weights modest (`(detailed skin:1.2)`, not `:1.6`). `8k`, `masterpiece`, `realistic` do almost nothing — drop them for the concrete terms above.

SDXL's strengths are **ecosystem depth (LoRAs, ControlNet, IP-Adapter), speed, low-VRAM accessibility, artistic/anime range, and photoreal-via-finetune** — plus clean commercial licensing on base. Its weaknesses are **in-image text (it basically can't render legible words), complex/compositional prompts (77-token CLIP, no LLM encoder), and hands/anatomy**. Use SDXL when you want control tooling, a specific finetune/LoRA look, fast iteration, or to run on a small GPU. For tasks where SDXL's CLIP limitations are the bottleneck (reliable text, compositional prompts, natural-language description), you need a model with an LLM text encoder.

---

## Production pipelines & mixing models

For production output, SDXL runs the **full multi-stage ladder** — it's the family with the most rungs worth climbing:

1. **Base gen** in a 1024-area bucket (finetune + optional speed LoRA). Judge composition only; reroll freely.
2. **Hires second pass** — latent ×1.5 at denoise 0.3–0.5, or pixel-space upscale + re-sample at 0.25–0.35.
3. **Detailers** — FaceDetailer/ADetailer at denoise ~0.4; swap the character LoRA in *here* (`references/characters.md §3`).
4. **Tiled upscale** — `UltimateSDUpscale` with a 4× ESRGAN model, denoise 0.2–0.35, simpler prompt than the base gen.
5. **Finish** — ColorMatch against the pre-upscale image; optional SeedVR2-class restorer.

Per-stage settings: `references/setup-and-workflows.md §6`.

**SDXL's role in mixed-model pipelines** is defined by its ecosystem: it has the control tooling the DiT models lack, and they have the rendering quality it lacks. Two named, mainstream patterns *(community — Civitai workflow authors)*:
- **Controllable front-end:** compose with SDXL's ControlNet/IP-Adapter/regional stack → decode to pixels → refine in Z-Image-Turbo or Flux.2 Klein img2img at denoise ~0.25–0.4 for natural rendering and cleaner anatomy.
- **Texture back-end:** generate in a DiT model → img2img through a photoreal SDXL finetune (RealVis-class) at ~0.3–0.55 to add its skin/texture character.

The handoff rule between families: **always VAE-decode to pixels first** — SDXL's latent space is incompatible with Flux/Z-Image latents. The full cross-model craft (denoise bands, resolution matching, color management, workflows-as-code) is the **`image-production-workflows`** skill.

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| Plastic / waxy / undertrained look | Running **base** SDXL raw | Switch to a photoreal finetune (Juggernaut/RealVisXL); add `detailed skin` |
| Fried, over-saturated, posterised colours | Prompt weights too high (SD1.5-style 1.5–1.8), or CFG too high | Keep weights ~1.05–1.3; drop CFG toward 5–7 |
| Black / NaN image | SDXL VAE overflowing in fp16 | Use `sdxl-vae-fp16-fix` via VAELoader, or decode the VAE in fp32 |
| Subject's head / feet cut off at frame edge | Non-zero crop-conditioning (`crops_coords_top_left`) | Set crop coords to **(0,0)** (centered); the `CLIPTextEncodeSDXL` `crop_w/crop_h` = 0 |
| Output looks low-res / soft even at 1024² | Low size-conditioning (`original_size`) | Set `original_size`/`target_size` to your actual resolution (e.g. 1024×1024) |
| Duplicated subjects, warped anatomy | Rendering far outside a 1024-area bucket (e.g. native 2048²) | Generate in a listed bucket, then upscale (hires-fix / tiled) |
| Negative prompt seems ignored | Distilled variant at **CFG 1 / guidance 0.0** — negatives are inert | Phrase constraints positively; or use base/finetune at CFG > 1 for negative control |
| Garbled / absent in-image text | CLIP-UNet can't render reliable typography | Don't ask SDXL for text — composite it in post-production instead |
| Mangled hands, extra fingers | Classic SD weakness | Negative `extra fingers, deformed hands`; inpaint/ControlNet the hands; re-roll |
| Prompt past ~77 tokens ignored | CLIP token window | Tighten, or split with `BREAK` so each chunk encodes separately |
| Pony/Illustrious output is mush | Wrong dialect (photoreal prompt on a tag-trained model) | Use `score_*`/`source_*` (Pony) or booru tags (Illustrious) |

---

## Pre-flight checklist

Before hitting Queue Prompt:

1. Using a **finetune** suited to the job (photoreal → Juggernaut/RealVis; anime → Pony/Illustrious), not raw base?
2. Prompt is **weighted keyword phrases**, front-loaded, not an LLM sentence or an empty `8k masterpiece` block?
3. Weights in **~1.05–1.3** (not SD1.5's 1.5–1.8)?
4. Prompt **dialect matches the checkpoint** (photo-keywords vs `score_*` vs booru)?
5. Resolution is a **1024-area bucket**; crop-conditioning at **(0,0)**?
6. Photoreal: `detailed skin` + camera body + film stock + named lighting?
7. Right **CFG for the variant** — base 5–8; distilled at **CFG 1 (ComfyUI) / 0.0 (diffusers)**, never 0.0 in ComfyUI?
8. Negative prompt present **only where it works** (base/finetune at CFG > 1), inert on distilled?
9. fp16 decode → `sdxl-vae-fp16-fix` loaded (no black images)?
10. Not asking SDXL to render in-image text?

---

## Where SDXL sits in the suite

| Job | SDXL | Reach for instead |
|---|---|---|
| Consistent characters | **Deepest toolbox** — InstantID/HyperLoRA adapters, mature LoRA training, `[SEP]` routing, block-weight control (`references/characters.md`) | `flux-2` for native multi-reference editing |
| Style LoRAs | **The mature ecosystem** — years of recipes, two trainers, separate Pony/Illustrious pools (`references/lora-training.md`) | a DiT model when the style needs prompt comprehension SDXL lacks |
| Structural control | **The most complete stack** — union ControlNet, IP-Adapter, regional prompting | — (this is SDXL's edge) |
| In-image typography | Basically can't | `ideogram-4` |
| Compositional / long prompts | 77-token CLIP ceiling | `flux-2` or `z-image` (LLM encoders) |
| Mixed-model pipelines | **Front-end (control) and back-end (texture)** roles | `image-production-workflows` for the cross-model craft |

---

## Licence & limitations

**Commercial-use picture (verify on each model page before relying on it):**

| Variant | Licence | Commercial? |
|---|---|---|
| **SDXL 1.0 base / refiner** | CreativeML **Open RAIL++-M** | ✅ Yes, no revenue cap |
| **SDXL Lightning** (ByteDance) | Open RAIL++-M (inherits base) | ✅ Yes, no cap — the cleanest fast variant |
| **Hyper-SDXL** | Open RAIL++-M | ✅ Yes |
| **LCM-LoRA** | OpenRAIL/permissive | ✅ Generally yes |
| **SDXL Turbo** | **contested** — see below | ⚠️ Verify |

**OpenRAIL++-M** permits royalty-free commercial use and you own your outputs, but it is a *responsible-AI* licence, not OSI-open: it carries **use-restrictions** (no illegal use, CSAM, harassment, disinformation, unlicensed medico-legal advice, etc.) that you must **pass downstream** when you redistribute the model or derivatives.

**Turbo's licence is genuinely contested — don't state a flat verdict.** The current `LICENSE.md` in `stabilityai/sdxl-turbo` is the **Stability AI Community License** (updated 5 July 2024), which **permits free commercial use for entities under US $1M annual revenue** (paid membership above that). *But* the same repo's metadata tag still reads `sai-nc-community` and the model-card prose still says "non-commercial / research." The actual LICENSE.md governs, but **anyone relying on commercial Turbo use should confirm with Stability directly** rather than trust one field.

**Architectural limitations** (primary, from the encoder design): the **77-token CLIP window** and absence of an LLM/T5 encoder cap compositional/long-prompt comprehension; **no reliable in-image text**; hands/anatomy need negatives, inpainting, or ControlNet. Don't import **SD1.5 negative-embedding** crutches (`UnrealisticDream`, etc.) — they don't load on SDXL.

**Release & stability:** SDXL 1.0 shipped 26 July 2023 — by image-model standards it is **old and stable**, so the core facts here move slowly. The **fast-moving parts** are the community layer: finetune versions (Juggernaut/RealVis release new versions regularly), the fast-variant LoRAs, and Turbo's licence status — re-verify those before relying on them.

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** Architecture (2.6B UNet, dual CLIP-L + OpenCLIP-bigG, 2048-dim concat, micro-conditioning), the ~6.6B ensemble figure, native 1024² and the resolution buckets, node names (`CLIPTextEncodeSDXL`, `CLIPTextEncodeSDXLRefiner`, `LoraLoader`), the stock node settings (1024², 25 steps, CFG 8, euler/normal, the 0.8 base/refiner split), the diffusers pipeline classes and ensemble code, the distillation methods, the OpenRAIL++-M / Lightning licence terms, the fp16-VAE overflow. **Source of truth is official** — the SDXL paper (arXiv 2307.01952), the Stability + ByteDance HF model cards, the licence files, the official ComfyUI templates — and they're verified there. A wrong node name won't wire; a misread licence is a legal problem. SDXL is old, so these move slowly — but Turbo's licence (above) is the exception.

**Craft — what actually makes a good image.** Which finetune to start from and at what version (Juggernaut, RealVisXL, DreamShaper, Pony V6, Illustrious/NoobAI), the Pony/Illustrious prompt dialects (score tags, booru ordering), the photoreal camera/film/lens/lighting vocabulary, LoRA weights and how the fast-variant LoRAs stack onto finetunes, VRAM thresholds, GGUF (un)suitability. **The authoritative source here is the community** — the finetune authors, Civitai model pages, and practitioners who've run these checkpoints for years — *not* the base model card, which describes the undertrained base SDXL nobody ships for real work. This is the deep, battle-tested layer, stated with confidence; where it's a range or "verify the current version," that's because the community layer moves (new finetune versions land monthly), not because it's unreliable. One calibration note: the photoreal *vocabulary* is CLIP-understood, but the SD1.5-era **weight values** from older guides don't transfer — those were dropped.

---

## Reference files

| File | When to read it |
|---|---|
| `references/prompting-guide.md` | Full prompt anatomy; the complete photoreal vocabulary (style tags, camera bodies, film stocks, lenses, lighting, photographer names, filters); weighting and 77-token/BREAK economy; the dual-encoder text_g/text_l split; negative-prompt guidance (variant-aware); the Pony score-tag and Illustrious booru dialects; worked SDXL-calibrated example prompts |
| `references/setup-and-workflows.md` | ComfyUI graphs in full (base, base+refiner ensemble, Turbo, Lightning, LCM, Hyper); every stock node setting; the fp16-fix VAE wiring; diffusers code (t2i, img2img, inpaint, the ensemble); hires-fix and tiled upscale; ControlNet and IP-Adapter setup; quantisation/VRAM |
| `references/checkpoints-and-loras.md` | The finetune ecosystem in depth (Juggernaut, RealVisXL, DreamShaper, Pony V6, Illustrious/NoobAI) with dialects and licence notes; the separate Pony/Illustrious LoRA pools; **§4 Using LoRAs** (loading any LoRA — the full `LoraLoader` patches UNet + both CLIP encoders, `strength_model`/`strength_clip`, dialect-pool matching, weight-by-type, triggers, stacking); the fast-variant speed LoRAs; ControlNet and IP-Adapter model catalog |
| `references/lora-training.md` | **Making** a LoRA (using is checkpoints-and-loras §4): kohya_ss/OneTrainer, the convergent recipes and rank-by-type ladder, Prodigy, caption-the-residual in the target dialect, **style-LoRA specifics** (the Illustrious recipe, the diversity maxim, color-cast lock-in, the out-of-set acceptance test), LoKr, good-citizen training, XY-grid evaluation |
| `references/characters.md` | Creating a **consistent character**: the identity-tool decision table (InstantID vs FaceID vs HyperLoRA vs ReActor vs character LoRA), the character LoRA pipeline (edit-model dataset factory, 8-point rotation in keyword dialect), the detailer LoRA swap, **`[SEP]` multi-character routing**, the **block-weight style-bleed fix** (SDXL-unique), multi-outfit LoRAs, failure modes |
