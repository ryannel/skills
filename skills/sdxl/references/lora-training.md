# SDXL LoRA Training (kohya_ss / OneTrainer)

> **Using** a LoRA (loading, dialect pools, weights, stacking) is `checkpoints-and-loras.md §4–5`. This file is only about **making** one. The full character pipeline (dataset factory, deployment, multi-character) is `references/characters.md`.

SDXL LoRA training is the most mature in open-source image gen — years of accumulated recipes, two solid trainers, and stable behavior. The numbers below are convergent community recipes from named guides; LR and rank are still genuinely contested across reputable sources, so treat them as strong starting points, not gospel.

## Tools and training base

- **Tools:** **kohya_ss** (`sd-scripts`, the de-facto standard, GUI + CLI) and **OneTrainer** (friendlier UI, good defaults). Both train SDXL LoRA/LoCon/LoHA and full finetunes. kohya's GitHub *discussions* are a primary craft source — named users publish reproducible experiments there.
- **Train on the family you'll deploy on.** Base SDXL 1.0 for maximum compatibility across the photoreal family; **Pony/Illustrious if you target those** — the result only works on that family (separate LoRA pools, `checkpoints-and-loras.md §1`).
- **Text encoder:** SDXL LoRAs *can* train the CLIP encoders (this is why `LoraLoader` exposes `strength_clip`). Whether to is contested: kohya's default TE LR is 5e-5 (half the UNet's); the Illustrious style recipe runs TE at 0.5 Prodigy-relative; others disable TE entirely for styles. Training TE binds vocabulary harder (good for trigger-heavy characters), at the cost of more prompt-hijacking when the LoRA is loaded. *(Contested — both camps have named, reproducible advocates.)*

## Hyperparameters

**The convergent photoreal/general recipe** (several independent named guides — ViewComfy, Bieler, Civitai cheatsheets — land here): **rank 32 / alpha 32, AdamW or AdamW8bit, constant scheduler, 0% warmup, LR ~3e-5** (usable range ~3e-6 to 8e-5), batch 1–4, 1024-area bucketed images. **Prodigy** (set LR 1.0, it self-tunes; d-coef ~0.5 for styles) dominates Pony/Illustrious practice and is the best answer to "I don't want to tune LR."

**Rank-by-type ladder** (lower rank = less capacity to soak up unwanted background/style):

| Target | Rank (dim) | Notes |
|---|---|---|
| Simple character | 8 | identity only |
| Complex / realistic character | 16 | |
| Concept | 16–32 | |
| **Style** | **32** (up to 128/α64 for very detailed styles) | styles need more capacity than characters — direction is agreed across sources, the ceiling is contested |

**How the knobs interact** (architecture-general): total steps ≈ images × repeats × epochs ÷ batch; **effective LR scales as `alpha ÷ rank`** (alpha = rank → no scaling). The old "alpha must never exceed rank or it burns" rule is a myth — `alpha = 2×rank` is a legitimate config that just doubles effective LR. **Steps anchor:** ~3000 total is the SDXL/Illustrious style-training anchor; characters usually converge sooner.

**VRAM:** ~12 GB with gradient checkpointing + 8-bit optimizer; 16–24 GB comfortable.

**LyCORIS:** **LoKr** is the variant with the strongest *style* reputation — better texture/style fidelity at much smaller files, at some cost in trainability and portability. DoRA outperforms plain LoRA in academic benchmarks but remains niche in practice; plain LoRA + LoKr cover nearly all 2026 style work. *(Community, strong — KohakuBlueleaf/LyCORIS, trainer comparisons.)*

## Dataset & captioning — caption the residual

A LoRA learns whatever you *don't* name. Caption in the **target dialect** — booru tags for Pony/Illustrious, descriptive keyword phrases for photoreal SDXL — and remember SDXL's CLIP needs the **trigger verbatim** (a rare literal token; `skw man` binds the man, `skw suit` binds the suit, so place it deliberately).

- **Character** (~15–30 images): caption everything that is *not* the identity — pose, clothing, background, lighting, angle — and let the rare trigger carry the face. Vary pose/angle/lighting; anything you caption stays promptable later. Full dataset protocol: `references/characters.md §2`.
- **Style** (~50 images for Illustrious-class; see below): invert it — caption the **content** of each image and never mention the style; the shared look becomes the residual.
- **Pony-specific:** its `score_X` quality tags participate in training captions and must *honestly match* the image's quality, or they destabilize training. *(Community, strong.)*

## Style LoRAs — the specifics

The governing maxim: **consistency in the thing you're training, diversity in everything else.** A style set must show the style on varied subjects — people, objects, interiors, landscapes — or the LoRA learns "this style = these subjects."

- **Size:** ~50 minimum is the Illustrious-era recommendation; the legacy "300–500 ideal" figure is early-SDXL folklore that curation replaced — **a well-curated 30–50 beats a poorly curated 500** *(community, convergent — L3n4's crash course, Civitai 25645)*. Dedupe hard: near-duplicate compositions are the fastest route to composition memorization.
- **The Illustrious style recipe** *(named, Civitai 25645)*: dim 32 / alpha 32, Prodigy (UNet 0.5 / TE 0.5), cosine scheduler, ~3000 steps, ~50 images, booru captions capped at ~30 tags, no style tags in captions.
- **Palette discipline:** include the style's full tonal range; keep B&W out of a color style set — narrow color statistics cause **color-cast lock-in** (every output takes the dataset's average palette).
- **Trigger:** optional for styles; many ship without one. If used, it's a verbatim rare token like any SDXL trigger.
- **Ethics flag:** a single living artist's style trained without consent is the community's sharpest fault line; Civitai requires real-artist disclosure. Prefer self-made, licensed, or historic/aggregate aesthetics.

**The style acceptance test:** the LoRA passes when the style is recognizable on subjects *not* in the training set. Point the trainer's sample prompts at out-of-set subjects, and include one sample prompt *without* the trigger to catch style leakage early.

## Train a "good citizen" if it'll be stacked

Modest rank, don't over-train, and accept a sweet spot **below 1.0** — that's what lets a LoRA coexist with speed LoRAs and other content LoRAs instead of frying the image. Sub-1.0 strength is normal, *not* a sign of overcooking.

## Assessing fit — judge by images, not loss

The loss curve barely predicts image quality; evaluate visually. Save **multiple checkpoints** (every 200–500 steps — the best one is usually well before the final), then generate an **XY grid of epoch × LoRA strength (0.1–1.0)** on fixed test prompts spanning simple → complex and in-domain → out-of-domain subjects, and pick the "Goldilocks" cell.

| Signal | What you see | Fix |
|---|---|---|
| **Good fit** | Concept reproduced *with flexibility* — pose, clothing, scene all remain promptable | ship that checkpoint |
| **Overfit** | Outputs drift toward the training images: rigid poses, baked backgrounds, fried color. Style-specific tells: composition memorization, training subjects appearing unprompted, color-cast lock-in | earlier epoch; more dataset variety; lower rank |
| **Underfit** | Weak likeness / style won't transfer | more steps or higher LR; check captions actually isolate the trigger |

**ControlNet/IP-Adapter often substitute for training** when you need pose or identity on a one-off — no training run needed (`setup-and-workflows.md §7`, `characters.md §1`).
