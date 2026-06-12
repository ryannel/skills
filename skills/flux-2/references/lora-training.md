# FLUX.2 LoRA Training

> **Using** a LoRA (loader node, variant compatibility, weights, stacking, the Turbo accel-LoRA) is `setup-and-workflows.md §7`. This file is only about **making** one. The full character pipeline (dataset factory, deployment, multi-character) is `references/characters.md`.

**Supported training bases:**
- [dev] 32B (Non-Commercial)
- [klein] 4B Base (**Apache 2.0 — use this for commercially-deployable LoRAs**)
- [klein] 9B Base (Non-Commercial; local training wants 32–48 GB VRAM *(community)*)

**Do not train on the distilled (4-step) variants** — distillation removes the texture diversity fine-tuning needs. Train on the corresponding base, deploy on either.

## Tooling

**Ostris AI-Toolkit** is the default trainer (supports [dev] and both klein bases). Working YAML skeleton:

```yaml
job: extension
config:
  name: my_flux2_lora
  process:
    - type: sd_trainer
      training_folder: "path/to/your/images"
      trigger_word: "my_concept"      # optional on FLUX.2 — see captioning below
      network:
        type: lora
        linear: 16
        linear_alpha: 16
      train:
        batch_size: 1
        steps: 2000
        train_unet: true
        train_text_encoder: false      # always false — encoders are frozen on FLUX.2
        learning_rate: 1e-4
        optimizer: adamw8bit
        lr_scheduler: cosine
      model:
        name_or_path: "black-forest-labs/FLUX.2-dev"
        is_flux2: true                 # verify this flag in current AI-Toolkit
        quantize: true
```

Other live options: **Civitai's official orchestration recipe** for [klein] (`developer.civitai.com/orchestration/recipes/training-flux2-klein` — engine ai-toolkit; includes an edit-training mode with `control_N/` reference folders), SimpleTuner, fal.ai/RunComfy hosted trainers. kohya/sd-scripts FLUX.2 support was pending close to release — verify before relying on it.

> ⚠ **The Civitai klein-4B recipe defaults to dim 2 / alpha 1.** That is a cost-optimized floor for their hosted trainer, not a quality recommendation — community ablation finds rank 4–8 LoRAs barely move FLUX.2's fused attention/MLP blocks. For local training start at 16 (character) / 32+ (style). *(Official-platform recipe vs named-community ablation — a genuine divergence, flagged.)*

## Hyperparameters

| Parameter | Character | Style | Notes |
|---|---|---|---|
| Rank (linear) | 16 (32 high end) | **32–128** | Herbst's 50+-run [klein]/[dev] ablation landed on **128/64/64/32** (linear/alpha/conv/conv-alpha, a 4:2:2:1 ratio) as "universally strong" for style — vs tool defaults of 16. Direction (style ≥ character) is agreed; magnitude is contested *(named community ablation — Calvin Herbst, Medium)* |
| Alpha | = rank | = rank or rank/2 | effective LR scales as `alpha ÷ rank`; `alpha = 2×rank` is legitimate (just doubles effective LR) — the "never exceed rank" rule is an SDXL-era myth |
| LR | 1e-4, drop to 5e-5 if frying | same | FLUX.2's big DiT is **LR-hypersensitive — start low**. [klein] tolerates 1e-4–5e-4. Herbst: weight decay 1e-5 is a surprisingly load-bearing color/tonality knob |
| Steps | 1500–3000 | 2000 (Civitai default) — Herbst's style sweet spot was **7000**, degrading past 10k | almost certainly dataset-size and LR dependent — contested, run checkpoints and read the grid |
| Batch | 1–4 | 1–4 | 1 + gradient accumulation is the safe floor |
| Dataset | 20–50 images | **20–30** (10–50 range) | DiT-class models need far fewer style images than SDXL folklore suggests; curation beats quantity |
| Text encoder | never | never | Mistral/Qwen3 are frozen; FLUX.2 LoRAs are model-only |

**How the knobs interact** (architecture-general): total steps ≈ images × repeats × epochs ÷ batch; effective LR = `alpha ÷ rank` × LR.

## Dataset & captioning — caption the residual, in prose

FLUX.2's encoders are LLMs, so captions are **descriptive natural-language sentences, not tags**, and the residual principle is unchanged: whatever you don't describe is what the LoRA absorbs.

- **Character:** describe everything that is *not* the identity — pose, clothing, scene, lighting, angle. No bare trigger token (it can confuse the LLM encoder); if you use one, embed it naturally ("a photo of TRIGGER, a woman with…"). Dataset protocol (rotation, expressions, factory): `references/characters.md §3`.
- **Style:** invert it — describe the **content** of each image across **diverse subjects** and never mention the style; the shared look becomes the residual.
- ⚠ **Captionless training is genuinely contested on Flux-class models.** The no-caption camp shows strong style replication from raw images alone; the pro-caption camp has the better-documented evidence for *generalization* (recris's "clown test" in kohya discussion #1497: detailed captions transfer beyond the training distribution; captionless LoRAs tend to replicate the dataset). Practical synthesis: **short natural-language scene descriptions that never mention the style** — caption-the-residual in prose. Captionless is defensible for a pure-replication style; captioned generalizes better. *(Named community evidence on both sides — presented as contested, not settled.)*

## Style LoRAs — the specifics

- **The diversity maxim:** consistency in the style, diversity in everything else — people, objects, interiors, landscapes — or the LoRA learns "this style = these subjects."
- **Palette discipline:** cover the style's tonal range; keep B&W out of a color set. Narrow color statistics cause **color-cast lock-in** (every output takes the dataset's average palette).
- **Resolution:** 1024² standard; 512 training demonstrably works on Flux-class models for some named users, but "512 beats 1024" is unresolved *(kohya #1497 — contested)*.
- **Inference strength:** FLUX.2 style LoRAs run hotter than SDXL's — typical 0.7–1.0; Herbst's ablated optimum for his style was 0.73 (usable 0.4–0.75).
- **Ethics flag:** single-living-artist styles without consent are the community fault line; Civitai requires real-artist disclosure. Prefer self-made, licensed, or historic/aggregate aesthetics.

**The style acceptance test:** the LoRA passes when the style is recognizable on subjects *not* in the training set. Point trainer sample prompts at out-of-set subjects, and include one prompt *without* any trigger to catch leakage early.

## Assessing fit — judge by images, not loss

Save **multiple checkpoints** (every 200–500 steps — the best is usually well before the final), then generate an **XY grid of checkpoint × LoRA strength (0.1–1.0)** on fixed prompts spanning in-domain → out-of-domain subjects, and pick the "Goldilocks" cell.

| Signal | What you see | Fix |
|---|---|---|
| **Good fit** | Concept reproduced *with flexibility* — pose/scene/outfit all remain promptable | ship it |
| **Overfit** | Drift toward the training images: rigid poses, baked backgrounds. Style tells: composition memorization, training subjects appearing unprompted, color-cast lock-in | earlier checkpoint; more variety; lower rank |
| **Underfit** | Weak likeness / style won't transfer | more steps; check captions actually isolate the concept |

A sweet spot **below 1.0 is normal**, not overcooking — and a modest, not-over-trained LoRA is the one that **stacks** cleanly (one style + one character is the reliable pairing; `setup-and-workflows.md §7`). Training-time layer targeting (`only_if_contains` / `ignore_if_contains` in AI-Toolkit) is the DiT-world analogue of SDXL's inference-time block-weight editing when a style keeps hijacking composition.

> **FLUX.2 training tooling is new (2026) and fast-moving.** The relationships above are stable; the exact defaults are not — verify against current AI-Toolkit FLUX.2 examples and the BFL "[klein] in 60 min" guide before a long run.
