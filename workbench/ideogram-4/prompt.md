# Ideogram 4 skill — authoring notes

**Goal:** a high-quality agent skill for Ideogram 4.0, matching the depth/structure of `generated-skills/z-image`. Authored by hand into `generated-skills/ideogram-4/` (SKILL.md + 3 references).

**What makes Ideogram 4 different from z-image (and shapes the skill):**
- Three surfaces, not two: web app + hosted API + open weights (ComfyUI/diffusers). z-image was open-weights only.
- Licence split is the crux: code Apache-2.0, weights **Non-Commercial**, outputs owned by user; commercial work routes through the web app/API.
- "The one rule that changes everything" = **structured JSON captions** (vs z-image's "sentence not tags"). Model trained exclusively on JSON.
- Realism is the *inverse* of z-image: Ideogram's own Magic Prompt bans "warm" grading and DSLR-bokeh markers; default to neutral/iPhone aesthetic.

**Primary sources used (anchor here, not blogs — model is days old, June 2026):**
- GitHub (Apache code, public): `ideogram-oss/ideogram4` — read raw: `README.md`, `docs/prompting.md`, `docs/inference.md`, `docs/model_architecture.md`, `src/ideogram4/sampler_configs.py`, `constants.py`, `caption_verifier.py`, `magic_prompt.py`, `magic_prompt_system_prompts/v1.txt`, `run_inference.py`, `model_licenses/LICENSE-IDEOGRAM-4-NON-COMMERCIAL`.
- HF model API (public metadata even for gated repos): `ideogram-ai/ideogram-4-fp8` / `-nf4` (confirmed real: `Ideogram4Pipeline`, license `ideogram-4-non-commercial`, real safetensors shards, lastModified 2026-06-03).
- ComfyUI: `blog.comfy.org/p/ideogram-4-day-0-support-in-comfyui`, `docs.comfy.org/tutorials/image/ideogram/ideogram-v4`, raw template `Comfy-Org/workflow_templates/.../image_ideogram4_t2i.json`.
- Hosted API/web app (official-via-summariser, spot-verify): `developer.ideogram.ai`, `docs.ideogram.ai`, `ideogram.ai/api-pricing`, `ideogram.ai/blog/ideogram-4.0/`.

**Secondary/community (labelled in skill as flagged):** the-decoder, gigazine (independent tests); Hacker News thread (open-weight≠open-source backlash, safety false-positives acknowledged by team); Ostris ai-toolkit LoRA proof-of-concept; goenhance "messy open-weight story" review.

**Conflicts resolved:**
- "weights commercial" (some blogs) → WRONG. Primary licence text is Non-Commercial.
- safety filter "baked in weights" vs "optional Hive" → BOTH: model-level gray-screen NSFW filter (can't disable) + optional external Hive in reference pipeline.
- "amber/plastic skin" community claim → unverified for IG4; instead sourced realism guidance to Ideogram's own system-prompt rules (ban "warm", avoid DSLR markers).

**Flagged as community/single-source in the skill (re-verify):** exact VRAM/timings, nf4-vs-nvfp4 ComfyUI file naming, GGUF availability, web-app plan prices, LoRA-training tooling, exact presence of API `seed`/`num_images` and v4 edit/upscale endpoints.
