# Research: style LoRA training best practice — 2026-06-10

Deep-research report (web, named sources). Confidence: **[official]** = tool/model vendor docs or repo; **[strong]** = named, reproducible community author; **[weak]** = aggregated/unnamed/login-walled. ⚠ = contested.

## 1. Dataset curation for style

- **Size is family-dependent and smaller than character-LoRA folklore suggests.** Flux-class DiTs: 20–30 working norm, 10–50 range (Civitai 7777 **[strong]**). Araminta (alvdansen), the most-cited named style trainer: 20–30 typical, 54 for m3lt (https://huggingface.co/blog/alvdansen/training-lora-m3lt **[strong]**). Z-Image: 15–40 varied subjects, diminishing returns >~50 (https://neurocanvas.net/blog/zimage-lora-training-guide/ **[strong]**). SDXL/Illustrious: ~50 minimum (Civitai 25645 **[strong]**); legacy SDXL guides said 300–500 (Civitai 3169 **[weak]**). ⚠ Reconciliation accepted by most: stronger bases need fewer examples; "a well-curated 30–50 beats a poorly curated 500+" (L3n4, Civitai 9376 **[strong]**).
- **Subject diversity is the defining requirement.** Maxim: *consistency in the thing you're training, diversity in everything else.* Style sets must show the style on varied subjects — people, objects, interiors, landscapes — or the LoRA learns "this style = these subjects." Too-narrow palette statistics → color-cast lock-in (§4). **[strong]**
- **Resolution/bucketing:** train at native res (1024²); AR bucketing standard in all four trainers; avoid low-res and B&W contamination for color styles. ⚠ Flux 512-training works for some (kohya sd-scripts discussion #1497, user b-7777777); "512 better than 1024" contested in same thread. **[strong]**
- **Dedupe/quality:** near-duplicates/same-composition crops = fastest route to composition memorization. **[strong]**
- **Ethics:** single-living-artist style without consent is the community fault line; Civitai requires real-artist disclosure; prefer self-made/licensed/historic-aggregate datasets. **[weak — policy landscape]**

## 2. Captioning for style — the central debate

- **CLIP-era (SDXL) caption-the-residual:** caption everything that should stay *controllable*, omit the style; the uncaptioned residual is absorbed. "For a graphic style you describe the scene details, no mention of the style/colors at all" (Civitai 8487 **[strong]**). Pony adds `score_X` tags that must honestly match image quality or destabilize training (stable-diffusion-art Pony tags **[strong]**).
- ⚠ **No-caption vs detailed captions on Flux-class:** no-caption camp — Flux trains excellent style LoRAs on raw images if set is consistent-style/diverse-subject (Civitai 7203, login-walled **[weak]**). Pro-caption camp, named evidence — **recris's "clown test"** in kohya #1497: detailed captions yield better generalization; **slashedstar**: captionless LoRAs merely replicate the dataset **[strong]**. Civitai trainer docs prefer natural-language captions for Flux **[official-platform]**. **Practical synthesis most 2026 guides converge on: short-to-medium natural-language scene descriptions that never mention the style — caption-the-residual expressed in prose.** (neurocanvas Z-Image guide **[strong]**)
- **CLIP vs LLM-encoder mechanics:** CLIP treats tokens as semi-independent attractors → rare-token trigger works as a style "slot". T5/LLM encoders embed whole-sentence semantics → a nonsense token has no stable meaning, can "confuse the model" (RunDiffusion **[strong]**). DiT LoRA training is model-only; BFL never trained TEs (SimpleTuner #634 **[strong]**). ⚠ Triggers on Flux: many still use one and it works (mostly no-op/mild amplifier); recris: if used, embed naturally ("painting in the style of TRIGGERNAME"), not bare leading token **[strong]**. Civitai Flux.2-klein recipe makes captions and triggers explicitly optional **[official-platform]** — https://developer.civitai.com/orchestration/recipes/training-flux2-klein

## 3. Hyperparameters per family

- **Rank/alpha — style wants more capacity than character (direction agreed, magnitude ⚠).** AI-Toolkit default rank 16 **[official]**; RunComfy Flux.2-dev: 32 **[strong]**; **Calvin Herbst's 50+-run Flux.2 Klein/Dev ablation: 128/64/64/32 (linear/alpha/conv/conv-alpha, 4:2:2:1) "universally strong" for style** (https://medium.com/@calvinherbst/50-flux-2-klein-lora-training-runs-dev-and-klein-to-see-what-config-parameters-actually-matter-3196e4f64fd5 **[strong]**). SDXL/Illustrious style: dim 32/alpha 32 (Civitai 25645) up to dim 128/alpha 64–32 for very detailed styles (Civitai 21257) **[strong]**. Z-Image: 16 default, 32 texture-heavy, 64 cited for realism (neurocanvas; Tongyi-MAI Z-Image issue #64) **[strong]**. ⚠ rank-4–8 LoRAs barely move Flux.2's fused attention/MLP blocks (RunComfy).
- **Learning rates:** AI-Toolkit Flux.1 default 4e-4/rank 16 **[official]**; Flux.2-dev 1e-4 (5e-5 if frying) **[strong]**; Flux.2 Klein LR-sensitive, 1e-4–5e-4, AdamW8bit **[official-platform]**; Z-Image 1e-4–2e-4, batch 1, AdamW8bit **[strong]**. SDXL style runs hotter than character (3e-4–8e-4 unet-LR AdamW, or Prodigy d-coef ~0.5) **[strong/weak mix]**. Herbst: Flux LR hypersensitive; weight decay 1e-5 a load-bearing color/tonality knob **[strong]**.
- **Steps:** ~3000 SDXL/Illustrious style anchor; alvdansen ~55 steps/image; Z-Image 2500–3000; Flux.2 klein default 2000; ⚠ Herbst's Flux.2 sweet spot 7000 (degrades past 10k) — dataset-size dependent.
- **Optimizers:** AdamW8bit cross-family default **[official]**; Prodigy dominates SDXL/Pony/Illustrious practice (self-tunes LR); recris recommends AdamWScheduleFree for Flux **[strong]**; CAME mainly video/diffusion-pipe **[weak]**.
- **Timestep sampling (DiTs):** flow-matching = logit-normal/sigmoid sampling with shift. diffusion-pipe: `logit_normal` for Qwen-Image, resolution-dependent shift for Flux/Lumina-2, **shift = 3 for Z-Image** (https://github.com/tdrussell/diffusion-pipe/blob/main/docs/supported_models.md **[official]**). AI-Toolkit Qwen-Image-2512: "sigmoid" timestep type measurably better than "weighted" (RunComfy **[strong]**).
- **Text encoder:** SDXL optional/contested (Illustrious style recipe TE-LR 0.5 Prodigy-relative); DiTs never (`trainTextEncoder: false` in klein recipe). **[official-platform/strong]**
- **LyCORIS 2026:** LoKr first-class in AI-Toolkit (`lokr_full_rank`, `lokr_factor`) **[official]**; strongest style reputation among LyCORIS variants — better texture/style fidelity at smaller files, less trainable/portable (Tensor.Art comparison; KohakuBlueleaf/LyCORIS) **[strong]**. DoRA beats LoRA academically (arXiv 2402.09353) but no AI-Toolkit support; plain LoRA + LoKr cover ~all 2026 style work **[strong]**.

## 4. Evaluation

- **XY grids: epoch/checkpoint × LoRA strength**, fixed seeds, prompt set spanning simple→complex and in-domain→out-of-domain subjects (alvdansen tested "a woman" through full scenes) **[strong]**. Save checkpoints every 200–500 steps; best checkpoint "usually well before the final."
- **Style-specific overfit signals:** (a) composition memorization — training-image layouts reproduced regardless of prompt; (b) subject bleed — training subjects appear unprompted; (c) color-cast lock-in — every image takes the dataset's average palette; (d) frying/oversaturation. **Acceptance test: the style is recognizable on subjects NOT in the training set.** **[strong]**
- **Sample-prompt discipline:** out-of-set subjects in trainer sample prompts; include at least one prompt *without* the trigger to catch style leakage early (neurocanvas **[strong]**).

## 5. Per-model specifics, mid-2026

- **Flux.2 [klein]:** Civitai official orchestration recipe — engine ai-toolkit; klein-base-4B default 2000 steps, LR 5e-4, **dim 2/alpha 1 (cost-optimized floor — community pushes 32–128 for style)**; klein-base-9B 2000 steps, LR ~1e-4, dim 32/alpha 32, cosine; TE off; edit-training mode with `control_N/` folders. Local 9B training wants 32–48 GB VRAM. **[official-platform + strong]**
- **Z-Image:** fully trainable. Turbo requires AI-Toolkit **de-distillation adapter** (v2 default, v1 fallback), or the "de-turbo" route (adapter-free, infer at 20–30 steps/CFG 2–3). Base trains conventionally. diffusion-pipe supports Z-Image (ComfyUI-format output, shift 3). **[strong/official]**
- **SDXL/Pony/Illustrious:** mature recipes. Illustrious style: dim 32/alpha 32, Prodigy (unet 0.5/TE 0.5), cosine, ~3000 steps, ~50 images, booru tags max ~30 (Civitai 25645 **[strong]**). Pony differs by score-tag captioning; Illustrious is now the default anime-style target. Same LoRA must be retrained per base. **[strong]**
- **Qwen-Image / Chroma / Lumina:** trainable in AI-Toolkit and diffusion-pipe; Qwen-Image trains on 24 GB with block swapping; Chroma/Lumina-2 output ComfyUI-format LoRAs. **[official]**

## 6. Using/stacking at inference

- **Strengths:** SDXL style 0.4–0.8 model / 0.3–0.7 clip; character 0.7–1.1 (neurocanvas multi-LoRA guide **[strong]**). Flux/Flux.2 style higher (0.7–1.0); Herbst's ablated optimum 0.73, usable 0.4–0.75 **[strong]**.
- **Stacking:** one style ("how it looks") + one character ("who it is"), e.g. style 0.6 / character 0.9; if identity collapses, lower style to 0.3–0.5 and cut `strength_clip` first; two style LoRAs fight over color science; predictable only to 2–3 stacked. Load order style→character→object is convention, not math. **[strong]**
- **Block-weight editing:** alive on SDXL via Inspire-Pack `LoraLoaderBlockWeight` (per-block strength vectors) **[official-repo]** — classic use: mute composition-carrying blocks, keep texture blocks. DiT analogue is *training-time* layer targeting (`only_if_contains`/`ignore_if_contains` in AI-Toolkit) **[official]**; inference-side block editing for Flux-class is less standardized **[weak]**.

## Contested points summary

1. Captioning for style on Flux-class (no-caption vs prose) — strongest named evidence (recris) favors captions for flexibility; no-caption works for pure replication.
2. Trigger words on LLM-encoder models — likely unnecessary, possibly harmful as bare tokens, harmless embedded naturally.
3. Style rank — 16/32 (tool defaults) vs 128-class (Herbst ablation); direction agreed (style ≥ character).
4. Dataset size — 20–40 (DiT era) vs 300+ (legacy SDXL); curation-over-quantity is the resolution.
5. Flux.2 step counts — 2000 (Civitai default) vs 7000 (Herbst); dataset/LR-dependent.
6. 512 vs 1024 training on Flux — unresolved (kohya #1497).

**Caveat:** Civitai articles 7203 and 6792 are login-walled — characterized via secondary summaries; treat their specifics as **[weak]** until read with an account.
