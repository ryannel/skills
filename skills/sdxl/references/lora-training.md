# SDXL LoRA Training (kohya_ss / OneTrainer / ai-toolkit)

> **Shared craft lives in [`character-lora-training`](../../character-lora-training/)** — dataset coverage, caption-the-residual, evaluation, adult/NSFW base selection, and the real-person likeness rules that decide whether a LoRA is publishable. This file covers what is specific to SDXL and its finetune families.

> **Using** a LoRA (loading, dialect pools, weights, stacking) is `checkpoints-and-loras.md §4–5`. This file is only about **making** one. The full character pipeline is `references/characters.md`.

SDXL LoRA training is the most mature in open-source image generation — years of accumulated recipes, several solid trainers, stable behaviour, and by far the deepest body of published craft. The numbers below are convergent recipes from named guides. LR and **rank in particular are genuinely contested** across reputable sources, so treat them as starting points.

1. [Choosing the base — the decision that dominates](#1-choosing-the-base)
2. [Tools](#2-tools)
3. [Hyperparameters](#3-hyperparameters)
4. [Dataset architecture — the identity ratio](#4-dataset-architecture--the-identity-ratio)
5. [Captioning](#5-captioning)
6. [Dataset traps](#6-dataset-traps)
7. [Style LoRAs](#7-style-loras)
8. [Advanced: weight noising and depth anchoring](#8-advanced-weight-noising-and-depth-anchoring)
9. [Stacking several LoRAs of the same character](#9-stacking-several-loras-of-the-same-character)
10. [Assessing fit](#10-assessing-fit)
11. [Adult / NSFW work on SDXL](#11-adult--nsfw-work-on-sdxl)

---

## 1. Choosing the base

**This decides your ceiling, your tagging dialect, and which existing LoRAs you can stack with.** It matters more than any hyperparameter, and it is not reversible — a LoRA belongs to the family it was trained on.

| Base | Dialect | Position |
|---|---|---|
| **SDXL 1.0 / photoreal finetunes** | Descriptive keyword phrases | Maximum compatibility across the photoreal family. The right choice for realism work |
| **Pony Diffusion V6 XL** | Booru tags **plus `score_X` quality tags** | Enormous ecosystem. The score-tag system is divisive — it participates in training captions and **does not transfer** to other families `[community]` |
| **Illustrious** (v2.0 as a finetune base) | Booru tags | **The largest character-LoRA library.** The default choice for character work if you want compatibility with existing community LoRAs |
| **NoobAI-XL V-Pred 1.0** | Booru tags | Reported as the most anatomically accurate with the best tag comprehension. **Requires v-prediction sampler settings and Euler specifically — other samplers will not work.** Budget an evening for that alone |
| **WAI-NSFW v17** | Booru tags | The usual easier-setup runner-up to v-pred NoobAI |
| **Anima** | Booru tags | Newer, gaining momentum — named trainers describe it as becoming "the new Illustrious," and note that most Civitai LoRAs for it are still poorly trained. An opportunity and a risk `[flagged — re-verify]` |

**Cross-family transfer is partial at best.** Some NoobAI LoRAs are reported to work acceptably on Illustrious, since the lineages share ancestry `[community — re-verify]`. Pony is the outlier: its score-tag conditioning means a Pony-trained LoRA carries assumptions nothing else shares.

**The honest heuristic:** train on the checkpoint you will actually generate with. If you don't know yet, Illustrious for anime/stylised character work and a photoreal SDXL finetune for realism are the safe defaults, because both have the largest pools of compatible LoRAs to stack with.

---

## 2. Tools

- **kohya_ss** (`sd-scripts`) — the de-facto standard, GUI and CLI. Its GitHub **discussions** are a primary craft source: named users publish reproducible experiments there.
- **OneTrainer** — friendlier UI, good defaults, and the most-requested target when new techniques get ported.
- **ai-toolkit** (Ostris) — increasingly the default for newer architectures, and the base for the experimental fork in §8.

**Text-encoder training is contested.** SDXL LoRAs *can* train the CLIP encoders — that's why `LoraLoader` exposes `strength_clip`. kohya's default TE LR is 5e-5 (half the UNet's); the Illustrious style recipe runs TE at 0.5 Prodigy-relative; others disable TE entirely for styles. Training the TE binds vocabulary harder — good for trigger-heavy characters — at the cost of more prompt-hijacking when the LoRA is loaded. Both camps have named, reproducible advocates. `[contested]`

---

## 3. Hyperparameters

**The convergent photoreal/general recipe** (ViewComfy, Bieler, Civitai cheatsheets independently land here): **rank 32 / alpha 32, AdamW or AdamW8bit, constant scheduler, 0% warmup, LR ~3e-5** (usable ~3e-6 to 8e-5), batch 1–4, 1024-area bucketed images.

**Prodigy** (set LR 1.0 and it self-tunes; d-coef ~0.5 for styles) dominates Pony/Illustrious practice and is the best answer to "I don't want to tune LR."

**Rank is genuinely contested, and the disagreement is worth understanding rather than averaging away:**

| Source | Position |
|---|---|
| The classic rank-by-type ladder | Simple character **8**, complex/realistic character **16**, concept 16–32, style **32** (up to 128/α64 for very detailed styles) |
| Named character-LoRA trainers | **48/48** as a working default, with **48–64** prescribed specifically when a LoRA "forgets" at weights below 0.5 `[community — neonkisu, QuantumBogoSort]` |

Both are defensible. Lower rank soaks up less unwanted background and style and produces a better-behaved stacking citizen; higher rank captures fine identity detail and holds up at reduced weight. **If your LoRA needs 1.0 to work, that is the signal to raise rank** — not to accept 1.0.

**Steps.** Two anchors, and they agree better than they look:

- **~80–100 steps per image** is the community rule of thumb, corroborated across SDXL and newer architectures `[community — QuantumBogoSort and others]`. Twenty images ≈ 1600–2000 steps.
- **~3000 total** is the long-standing SDXL/Illustrious *style* anchor. Characters usually converge sooner.

**How the knobs interact:** total steps ≈ images × repeats × epochs ÷ batch; **effective LR scales as `alpha ÷ rank`** (alpha = rank → no scaling). The old "alpha must never exceed rank or it burns" rule is a myth — `alpha = 2×rank` is a legitimate config that simply doubles effective LR.

**VRAM and batch.** ~12 GB with gradient checkpointing plus an 8-bit optimizer; 16–24 GB comfortable. When you drop batch size to fit, **hold `batch × gradient_accumulation` constant** — batch 1 / accum 4 is equivalent in effect to batch 4, at roughly a third of the speed `[community — QuantumBogoSort]`.

**LyCORIS.** **LoKr** has the strongest *style* reputation — better texture fidelity at much smaller file sizes, at some cost in trainability and portability. **LoKr factor 8** is the setting in the current experimental character recipes (§8). DoRA outperforms plain LoRA in academic benchmarks but stays niche; plain LoRA and LoKr cover nearly all practical 2026 work.

**Resolution.** 1024 is the point of diminishing returns — 1536 and 2048 training is analytically better but not perceptually so for most work `[community — QuantumBogoSort]`.

---

## 4. Dataset architecture — the identity ratio

The most useful published structure for character sets, and it reframes "dataset variety" into something you can actually count `[community — neonkisu, Civitai]`.

**Every image plays one of two roles:**

| Role | Share | What it is | What the LoRA learns |
|---|---|---|---|
| **Identity-emphasis** | **~33%** | Close-up portraits, head-and-shoulders, clean backgrounds. The character fills the frame | *Who this person is* |
| **In-context** | **~67%** | Full-body across varied environments, poses, outfits, scenes. The character is doing something somewhere | *How this person renders in the wild* |

Anywhere from **0.25 to 0.4** works. What matters is that both categories are present and meaningfully sized — and the two failure directions are diagnostic:

- **Mostly close-ups** → great faces, but body type, outfit consistency and pose flexibility are lost. The LoRA "knows the face and treats everything below the neck as a stranger." This is the classic selfie-style character LoRA.
- **Mostly in-context** → holds body and outfit, but the face drifts toward generic when the prompt zooms in.

**Verify the split by counting.** Sort the set into the two categories and count them. This takes a minute and catches the most common structural dataset fault.

Size: **20–30 images for a single-outfit character** is the current Illustrious-era figure `[community — NanashiAnon]`; 30–60 across both categories for a fuller character. New trainers routinely overestimate this because older guides quoted much larger numbers.

---

## 5. Captioning

Caption in the **target dialect** — booru tags for Pony/Illustrious/NoobAI/Anima, descriptive keyword phrases for photoreal SDXL. SDXL's CLIP needs the **trigger verbatim**: a rare literal token, placed deliberately (`skw man` binds the man, `skw suit` binds the suit).

**The rule, stated precisely:** caption the things you want to remain **promptable later**. Leave out what should fuse into the trigger.

**But captioning is downstream of the dataset, and this is the part most guides miss.** A hard-won correction from a published post-mortem:

> Identity features were stripped from the captions so they would bind to the trigger — that worked, the face locked. Hair colour was captioned in every single image so it would stay free — and it fused to the trigger anyway, because **all sixteen images had the same hair colour**. *"Describing it is not enough when it never varies in the data."* `[community — Ainara, Civitai]`

**So: you cannot caption your way out of missing variety.** Captioning something only makes it separable if it actually varies across the set. If you want hair colour promptable, the dataset needs more than one hair colour — or accept that it belongs to the character.

**Consistent identity tokens across both dataset categories.** The same identity tags should appear on identity-emphasis and in-context images alike. That repetition is the signal that says "this character is always this person" `[community — neonkisu]`.

**Put off-spec negatives in the captions**, not only in the inference-time negative prompt. If the character has ice-blue eyes, tagging `brown_eyes, green_eyes` as negatives during training reduces colour flipping later `[community — neonkisu]`.

**Caption dropout is the strongest single lever for generalisation**, and most character LoRAs skip it. Setting `caption_dropout ≈ 0.3` randomly drops 30% of caption tokens each step. Without it, the LoRA learns the *whole caption* as its trigger condition — so a character trained on "library, reading" struggles at "beach, swimming," because the environment is entangled with the identity. With dropout, each token's meaning is learned more independently, and the trigger alone activates the character in combinations it never saw `[community — neonkisu]`.

**Prepend / append structure**, for trainers that expose it (Civitai's own trainer does) `[community — RONK234, Civitai]`:

| Slot | Put here |
|---|---|
| **Trigger** | The character's name, and nothing else. Add other traits *after* training, once tested |
| **Prepend** | Permanent physical traits only — hair colour, eye colour, hairstyle, **body type** |
| **Append** | Genuinely minor details. **Never put important character details here** — appended tags are pushed to the back and deprioritised |

Two traps in that structure:

- **If the dataset mixes colour and monochrome images, keep colour terms out of the prepend.** It confuses how the model interprets monochrome inputs — a real problem for manga/manhwa sourcing.
- Use the append slot for something you want to toggle at inference. Tagging source styling (`manga`, `manhwa`) there lets you switch panel styling in or out of the positive prompt later.

Auto-tagger settings that recur across guides: **max ~30 tags, minimum threshold ~0.4**, plus a standard quality blacklist (`bad quality`, `worst quality`, `deformed`, `mutation`, `blurry`).

**Body tokens belong in the captions.** Height, build and proportions are part of an identity, and omitting them is a documented cause of a LoRA whose face is right and whose body is wrong — which matters most where the body is actually visible.

**Pony-specific:** its `score_X` quality tags participate in training captions and must **honestly match** the image's quality, or they destabilise training.

**Subject masking**, where the trainer supports it, masks out the background — and if you use it, captions must describe **only the character, never the setting**. Mixing masked training with setting descriptions gives the model contradictory signal `[community — QuantumBogoSort]`.

---

## 6. Dataset traps

Three that cost people whole training runs, all from published post-mortems:

**A reference sheet cut into pieces is not a dataset.** Sixteen crops from one character sheet is one lighting setup, one background, one camera, one moment. *"A LoRA cannot learn variety it has never seen."* Everything else on this list follows from it `[community — Ainara]`.

**Never pad to square with a solid colour.** Padding non-square crops to 1024 with white teaches the model the white. The result is a pale border baked into every generation — not a rendering artefact, and **no negative prompt removes it**, because from the model's point of view the bar is simply part of what this character looks like. **Crop square; do not pad.**

**Train at the aspect ratios you will generate at.** Training exclusively on 1:1 and then generating portrait degrades output. Use bucketing across the ratios you actually want.

Also: **dedupe hard.** Twenty frames pulled from one video clip look like twenty images and behave like one.

---

## 7. Style LoRAs

The governing maxim: **consistency in the thing you're training, diversity in everything else.** A style set must show the style on varied subjects — people, objects, interiors, landscapes — or the LoRA learns "this style = these subjects."

- **Size:** ~50 minimum is the Illustrious-era recommendation. The legacy "300–500 ideal" figure is early-SDXL folklore that curation replaced — **a well-curated 30–50 beats a poorly curated 500** `[community — L3n4's crash course, Civitai 25645]`.
- **The Illustrious style recipe** `[named — Civitai 25645]`: dim 32 / alpha 32, Prodigy (UNet 0.5 / TE 0.5), cosine scheduler, ~3000 steps, ~50 images, booru captions capped at ~30 tags, no style tags in captions.
- **Invert the captioning:** caption the **content** of each image and never mention the style; the shared look becomes the residual.
- **Palette discipline:** include the style's full tonal range and keep B&W out of a colour style set — narrow colour statistics cause **colour-cast lock-in**, where every output takes the dataset's average palette.
- **Ethics flag:** a single living artist's style trained without consent is the community's sharpest fault line, and Civitai requires real-artist disclosure. Prefer self-made, licensed, or historic/aggregate aesthetics.

**The style acceptance test:** the style is recognisable on subjects *not* in the training set. Point sample prompts at out-of-set subjects, and include one sample **without** the trigger to catch style leakage early.

---

## 8. Advanced: weight noising and depth anchoring

An experimental method with published results and an active feedback loop, worth knowing because it targets the exact failure that plagues character runs `[community — QuantumBogoSort, `ai-toolkit-perceptual` fork]`.

**Weight noising** injects a small Gaussian perturbation directly into the LoRA weights at every training step. The intuition: it helps the model *forget* what is inconsistent and keep only what the data agrees on. Mechanically it biases training toward flatter loss minima and spreads learning across more singular directions of the LoRA factorisation (a measured +20% stable rank on the same config). The practical effect is **resistance to the memorisation that overcooks character runs**, with better likeness at the same step count.

Reference config from the published comparison: batch 4, LR 5e-5, buckets 512/768/1024, **LoKr factor 8**, AdamW8bit, 1200 steps with the best checkpoint at **750**, on an **8-image** dataset. Noise **sigma 0.0125** gave the best results; the right value is believed to scale with dataset and batch size and is not yet mapped.

**Expect mid-training weirdness.** Body horror and extra limbs during the run are *normal* here — the noise explores latent space more aggressively before converging. The heuristic: if you sample every 25 steps and see continuous body horror for more than ~20% of the run, sigma is too high — lower it in 0.0025 increments.

**Status on SDXL:** depth anchoring is supported; the weight-noising parameters for SDXL specifically are still being worked out. `[flagged — re-verify]`

Also emerging from the same discussion: the **Rose optimizer** (stateless, lower VRAM, better reported generalisation) needs a **much higher LR — around 1e-3 rather than 1e-4** — and its overfitting presents as minor artefacting rather than the usual memorisation, so save checkpoints more frequently when using it. `[community — ECF630; contested, early]`

---

## 9. Stacking several LoRAs of the same character

A widely-reproduced finding worth knowing before you train at all: **for a popular character with several existing community LoRAs, stacking them at reduced strength beats any one of them at 1.0** `[community — featherless_fiend]`.

| LoRAs stacked | Strength each |
|---|---|
| 2 | ~0.55 |
| 3 | ~0.425 |
| 4 | ~0.35 |
| 5 | ~0.275 |

The reported gain is **flexibility** — a single LoRA pushed to 1.0 follows prompt actions less, drops quality, and makes more mistakes. The averaging effect has theoretical support in the **Model Soups** line of work (arXiv 2203.05482).

Two consequences: if your character already has good community LoRAs, **try stacking before training**; and if you *are* training one, expect it to be used this way, so build a good citizen (§10).

---

## 10. Assessing fit

**Judge by images, not loss.** The loss curve barely predicts image quality.

Save **checkpoints throughout** — every 200–500 steps on a conventional run, every 25 on an experimental one — because the best checkpoint is usually well before the final. Then build an **XY grid of epoch × strength (0.1–1.0)** on fixed prompts spanning simple → complex and in-domain → out-of-domain, and pick the Goldilocks cell. Generating the grid in ComfyUI is truer than trainer preview samples.

**Then judge the grid blind** — it is labelled by design, so you know which cell trained longer before you look. Which comparison tool to use, the shuffled-candidate pass, a reusable probe set and how to score likeness with numbers: [`character-lora-training/references/evaluation-and-tooling.md`](../../character-lora-training/references/evaluation-and-tooling.md).

**A concrete ship criterion** `[community — neonkisu]`: if the LoRA holds identity at **0.7+ weight across three or more clearly different environments**, ship it. Do not over-optimise the first version — feedback from real use is faster than another isolated iteration round.

**Train a good citizen if it will be stacked.** Modest rank, don't over-train, and accept a sweet spot **below 1.0** — that is what lets a LoRA coexist with speed LoRAs and other content LoRAs. Sub-1.0 strength is normal, not a sign of undercooking.

| Signal | What you see | Fix |
|---|---|---|
| **Good fit** | Concept reproduced *with flexibility* — pose, clothing, scene remain promptable | ship that checkpoint |
| **Overfit** | Drift toward training images: rigid poses, baked backgrounds, fried colour. Style tells: composition memorisation, training subjects appearing unprompted, colour-cast lock-in | earlier epoch; more dataset variety; lower rank |
| **Underfit** | Weak likeness, style won't transfer | more steps or higher LR; check captions actually isolate the trigger |
| Face right, body proportions drift | Too little in-context — identity ratio too high | Add full-body shots; lower ratio toward 0.25 |
| Body consistent, face generic on close-ups | Too little identity-emphasis | Add close-ups; raise ratio toward 0.4 |
| Renders only in training environments | Caption dropout too low or zero | Set `caption_dropout` ~0.3 |
| A captioned attribute fuses to the trigger anyway | That attribute never varied in the dataset | Add variety; captioning alone cannot fix it |
| Pale border or edge artefact in every output | Padded images in the dataset | Recrop square; retrain |
| Forgets the character below ~0.5 weight | Rank too low, or under-converged | Rank 48–64; or more epochs |

**ControlNet and IP-Adapter often substitute for training** when you need pose or identity on a one-off — no run needed (`setup-and-workflows.md §7`, `characters.md §1`).

---

## 11. Adult / NSFW work on SDXL

SDXL is where this is deepest in the whole open-weights field, and base choice does nearly all the work — see §1 and [`character-lora-training/references/nsfw-training.md`](../../character-lora-training/references/nsfw-training.md) for the cross-model treatment.

SDXL-specific points:

- **Pick a base with the training data.** NoobAI-XL V-Pred for anatomical accuracy (with the v-pred/Euler constraint), Illustrious for the largest compatible character-LoRA pool, Pony for breadth, WAI-NSFW for an easier setup. Training an explicit character on vanilla SDXL 1.0 fights the base model the whole way.
- **Booru dialect means explicit tagging is natural.** These finetunes were trained on tagged data, so tag the explicit content plainly and specifically — vague captions cause the content to fuse into the character, producing a LoRA that can only ever be explicit.
- **Include clothed images** if the character needs to be renderable clothed. This falls out of the same rule.
- **Body tokens belong in the identity-emphasis captions too** — build and proportions are part of the identity, and omitting them is a documented cause of "outfit and body type wrong" `[community — neonkisu]`.
- **Publishing is the binding constraint, not capability.** Real-person likeness is prohibited outright on Civitai regardless of rating, and NCII of real people is federally enforced in the US. See [`character-lora-training/references/publishing-and-likeness.md`](../../character-lora-training/references/publishing-and-likeness.md) before sourcing a dataset.
