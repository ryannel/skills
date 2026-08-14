# FLUX.2 skill — authoring notes

**Goal:** a high-quality agent skill for FLUX.2 by Black Forest Labs (BFL), matching the depth/structure of `generated-skills/z-image` and `generated-skills/ideogram-4`. Authored by hand into `generated-skills/flux-2/` (SKILL.md + 3 references).

## What makes FLUX.2 different (shapes the skill)

**Multiple variants with a license split** — the single most important organizational fact:
- [dev] 32B: open weights (gated HF), FLUX Non-Commercial License v2.0. Flagship quality.
- [klein] 4B: 4B, **Apache 2.0** (the only commercially-free open-weight option). Sub-second distilled, consumer GPU.
- [klein] 9B: 9B, Non-Commercial. Distilled (4 steps). Better quality than 4B.
- [pro]/[max]/[flex]: API-only, closed weights. Commercially usable via API.

**Two axes** (like ideogram-4): multiple variants AND multiple surfaces (open weights + hosted API). Lead with variant selector (most changes what the user does), then surface/license callout.

**"The one rule that changes everything"**: LLM-grade encoders (Mistral Small 3.2 24B for dev; Qwen3 for klein) → write **sentences not tags**, front-load subject, 30–80 words sweet spot. No negative prompts (flow matching at guidance=1; like Turbo in Z-Image). Official 4-part structure: Subject → Action → Style → Context.

**Realism**: Camera gear stacking works well and is officially recommended (BFL guide explicitly recommends "Shot on Hasselblad X2D, 80mm lens, f/2.8" over "professional photo"). Similar to Z-Image's gear-stacking, but for different reasons (Mistral understands camera vocabulary as semantic context).

**Hex color control** (new vs Flux.1): signal hex with "color" or "hex" keyword before code — `"An apple in color #0047AB"`. Unique capability.

**JSON prompts for production**: BFL recommends structured JSON for complex multi-subject scenes — but unlike Ideogram 4, this is optional and the model was NOT trained exclusively on JSON. It's a workflow tool, not a schema requirement.

**No negative prompts**: Flow matching without CFG-based guidance. No negatives in any variant (dev uses BasicGuider, klein distilled uses CFGGuider with guidance=1). Phrase constraints positively.

## Primary sources used

- **GitHub**: `github.com/black-forest-labs/flux2` — README, license files, `src/flux2/text_encoder.py` (Mistral 3.2 24B, 512 max tokens, layer extraction 10/20/30)
- **HF blog**: `huggingface.co/blog/flux-2` — architecture (8 double + 48 single stream blocks, new `AutoencoderKLFlux2`, diffusers pipeline classes, hardware requirements)
- **HF model cards**: `black-forest-labs/FLUX.2-dev`, `black-forest-labs/FLUX.2-klein-4B` — confirmed parameters, encoder, license, recommended steps/guidance
- **ComfyUI templates** (raw JSON): `Comfy-Org/workflow_templates` — `image_flux2_text_to_image.json`, `image_flux2_fp8.json`, `image_flux2_klein_text_to_image.json`, `image_flux2_text_to_image_9b.json`
- **Comfy-Org HF repos**: `Comfy-Org/flux2-dev` (107 GB), `Comfy-Org/flux2-klein` (27.7 GB), `Comfy-Org/flux2-klein-9B` — exact filenames and sizes
- **BFL official docs**: `docs.bfl.ai`, `docs.bfl.ml/guides/prompting_guide_flux2` — API endpoints, model slugs, prompting guide (Subject→Action→Style→Context, hex control, JSON format)
- **diffusers docs**: `huggingface.co/docs/diffusers/api/pipelines/flux2` — pipeline class names, parameters

## Secondary/community sources (labelled in skill)

- `deepwiki.com/black-forest-labs/flux2` — architecture analysis (VRAM breakdown table, text encoder details)
- `fal.ai/learn/devs/flux-2-prompt-guide` — prompting consensus
- `unsloth/FLUX.2-dev-GGUF`, `city96/FLUX.2-dev-gguf` — community GGUF quants
- `developer.civitai.com/orchestration/recipes/training-flux2-klein` — LoRA training
- 302.AI benchmark: Z-Image-Turbo vs Klein comparison

## Conflicts resolved

- "Quality tags work" (many community blogs) → **WRONG**. Mistral/Qwen3 don't need booru tags; quality-adjective tokens are legacy SD behavior. BFL's own guide confirms.
- "Negative prompts work" → **WRONG** for stock setup. Flow matching without CFG = no negative conditioning path. Phrase positively.
- `flux2-vae.safetensors` vs `full_encoder_small_decoder.safetensors` — **BOTH ARE VALID, USED IN DIFFERENT TEMPLATES**: t2i dev uses `full_encoder_small_decoder` (optimized); image-edit and klein 4B use `flux2-vae`. Document both.
- "Klein 4B is commercial" — **CONFIRMED TRUE** (Apache 2.0 weights). Very important.

## Flagged as community/single-source in the skill (re-verify)

- Exact VRAM numbers (especially for GGUF configs)
- GGUF file sizes (changing as new quants ship)
- LoRA training stability and hyperparameters
- API pricing (BFL uses interactive calculator, not fixed table)
- Klein quality vs Z-Image comparisons (single benchmark source)
- Diffusers stable version (v0.38.0 may be in flux)
