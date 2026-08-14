# SDXL skill — authoring notes

**Goal:** a high-quality agent skill for Stable Diffusion XL, matching the depth/structure of `generated-skills/z-image` and `generated-skills/ideogram-4`. Authored by hand into `generated-skills/sdxl/` (SKILL.md + 3 references).

**What makes SDXL different from z-image/ideogram (and shapes the skill):**
- It's an **older CLIP-UNet** (July 2023), not a DiT with an LLM/T5 encoder. This dates it and drives "the one rule."
- **"The one rule that changes everything" = dual-CLIP, 77-token keyword prompting** — weighted comma-separated phrases, front-loaded, matched to the checkpoint dialect. The exact *opposite* of z-image's "sentence not tags" and ideogram's "JSON caption." This is the clean three-way contrast across the suite.
- **Two orthogonal, composable axes:** speed (base / Turbo / Lightning / LCM / Hyper) × style-dialect (base / Juggernaut / RealVis / DreamShaper / Pony / Illustrious). Fast variants ship as LoRAs that stack onto any finetune → spine = variant selector (z-image shape) + a second finetune table.
- **You almost never run base raw** — the finetune ecosystem is the defining practical fact. No hosted-API surface (unlike ideogram), so it's a pure self-hosted-weights model → z-image shape, not ideogram's surface shape.
- **Realism = gear-stacking** (like z-image, opposite of ideogram) BUT the #1 lever is "use a photoreal finetune," then stack camera/film/lens/lighting vocab.

**Primary sources (SDXL is old & stable, so core facts are well-established — but verified the templates + current licences):**
- Paper: arXiv 2307.01952 (2.6B UNet, dual CLIP-L + OpenCLIP-bigG, 2048 concat, micro-conditioning: size/crop/target).
- Stability announcement (3.5B base / 6.6B ensemble figures — note: NOT in the paper or model card).
- HF model cards: `stabilityai/stable-diffusion-xl-base-1.0`, `-refiner-1.0`, `sdxl-turbo`, `ByteDance/SDXL-Lightning`, `madebyollin/sdxl-vae-fp16-fix`.
- Official ComfyUI templates (read verbatim): `Comfy-Org/workflow_templates/.../{sdxl_simple_example, sdxl_refiner_prompt_example, sdxlturbo_example}.json` → stock node settings (1024², 25 steps, cfg 8, euler/normal, 0.8 base/refiner split, Turbo euler_a + SDTurboScheduler + cfg 1 + 512²).
- comfyanonymous ComfyUI_examples (sdxl/sdturbo/lcm); docs.comfy.org node docs (CLIPTextEncodeSDXL fields); city96/ComfyUI-GGUF (don't quantise SDXL).
- diffusers docs (pipeline classes, ensemble denoising_end/start, ≥0.19.0).

**PDF guide mined (NOT pasted):** "Creating Photorealistic Images With AI" (PromptGeek, 2023) — an SD1.5-era keyword guide. Mined the **vocabulary** (style tags, camera bodies, film stocks, lenses, lighting, photographer names) which is CLIP-understood and transfers. **Dropped/recalibrated:** its 1.5–1.8 weights (fry SDXL → lowered to ~1.05–1.3), 512px-first workflow (SDXL is 1024-native), SD1.5 negative embeddings (`UnrealisticDream` won't load), and its 14 verbatim worked prompts (copyrighted expression + SD1.5-calibrated → wrote fresh SDXL examples instead).

**Conflicts/cautions resolved:**
- **Turbo licence is contested** → presented as unsettled (LICENSE.md = Stability Community License, commercial under $1M; but repo metadata still tags `sai-nc-community`). Don't pick a side. Lightning = OpenRAIL++-M (clean). Base = OpenRAIL++-M (clean, commercial OK).
- CFG precision per surface: ComfyUI `cfg=1` == diffusers `guidance_scale=0.0` == guidance off; never type 0.0 in a ComfyUI sampler. Negatives inert on all distilled variants.
- `CLIPTextEncodeSDXL` text_g/text_l = advanced lever; stock templates use plain `CLIPTextEncode`.

**Bidirectional back-links added:** z-image/SKILL.md and ideogram-4/SKILL.md both now point to `sdxl` in their "choose the model" notes.

**Flagged community/single-source in the skill (re-verify):** VRAM numbers, finetune roster + current versions/licences, Pony/Illustrious dialect specifics, GGUF unsuitability, LoRA-training hyperparameters, the photoreal vocabulary calibration.