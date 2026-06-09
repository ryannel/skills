# Z-Image LoRA Training

> **Using** a LoRA (loading, weights, stacking, the QKV gotcha, cross-compatibility) is in `references/workflows.md §6 — Using LoRAs`. This file is only about **making** one.

## Which variant to train on — train on Base, generate on Turbo

The community-recommended path (incl. the official Tongyi-MAI HF discussion #18) is to **train the LoRA on undistilled Z-Image Base and generate with it on Z-Image-Turbo.** Base gives the better cross-prompt control, and a Turbo-trained LoRA tends to "fight" the distillation (blurry at 8 steps, clean only at ~30 — see workflows §6). Train *on* Turbo only if you specifically want fast-delivery behavior baked in.

A Base-trained LoRA still **loads** on Turbo without error (shared S3-DiT), but it doesn't transfer perfectly — face/identity softens and a strength bump may be needed. Test on the variant you'll actually deploy on. *(Best practice; transfer magnitude is contested across sources — see workflows §6.)*

---

## Dataset generation workflow

The proven pattern for a new character LoRA:

**Step 1 — Anchor portrait**
Generate one image: front three-quarter view, neutral expression, plain background, soft north-window light, 50 mm equivalent lens, 1024×1024. This defines the identity envelope everything else must stay inside.

**Step 2 — Expand to 15–25 variants**
Use the anchor as a reference seed — run img2img passes at low denoise to produce variants covering:
- All eight head rotations (see `references/prompting-guide.md` §3.3)
- Varied shot sizes: close-up ~30%, full body ~20%, balance in medium and cowboy
- Varied wardrobe (change only the clothing clause; keep everything else identical)
- Varied lighting (change only the lighting clause; keep everything else identical)

**Step 3 — Caption each image**
Include angle + shot size explicitly in every caption so the LoRA disentangles identity from viewpoint. If the caption omits the angle, the LoRA will conflate identity with the angle it was mostly trained on.

**The core captioning principle — caption the *residual*.** A LoRA learns whatever you *don't* name. So for a **character**, describe everything that is **not** the identity — the pose, clothing, background, lighting, angle — and let the rare trigger word carry the face/identity that's left over. (A bonus: anything you caption becomes *changeable* at inference. Caption the hat in the photos that have one, and you can later prompt the hat on or off.) Captions are natural-language sentences here, not booru tags — Z-Image's Qwen-3 encoder reads prose. *(Caption-the-residual is architecture-general LoRA craft; the natural-language phrasing is the Qwen-3/LLM-encoder specific.)*

**Rule:** vary one thing at a time. If you change both clothing and lighting in the same image, the LoRA cannot disentangle which features belong to the character. For the rotation series specifically, keep the subject description and lighting direction **byte-identical** across all eight views — change only the angle clause.

### Style LoRAs — the dataset inverts

A **style** LoRA flips the residual: you want the *look* to be what's left over, so **caption the content** of each image (the subject, scene, composition) across **diverse subjects** (people, objects, landscapes — not one repeated subject), and the shared visual style becomes the residual the LoRA binds to. Style sets can run larger than character sets, and a trigger word is optional (many style LoRAs need none — see workflows §6). If you train a style on one subject only, the LoRA will entangle that subject *into* the style.

---

## Training with Ostris AI-Toolkit

### Required adapter for Z-Image-Turbo

When training on Z-Image-Turbo, the Ostris training adapter is **required**. Without it, the LoRA fights the distillation signal and produces blurry identity collapse.

Two variants ship in the `ostris/zimage_turbo_training_adapter` HF repo (referenced in the AI-Toolkit YAML config):
- `zimage_turbo_training_adapter_v1.safetensors` — default; stable
- `zimage_turbo_training_adapter_v2.safetensors` — experimental; often better for character work

> Z-Image (undistilled) does not require the training adapter.

### Recommended hyperparameters (character LoRA, 15–25 images at 1024×1024)

| Parameter | Value |
|---|---|
| Rank | 8–16 |
| Learning rate | 1e-4 (5e-5 for tight identity preservation) |
| Resolution | 1024×1024 |
| Steps | 2000–3000 |
| Hardware reference | RTX 5090: ~1 hour for 3k steps at these settings |

**How these interact** (architecture-general mechanics):
- **Total steps ≈ images × repeats × epochs ÷ batch.** Hold this in mind when you change dataset size — doubling the images halves the epochs for the same step count.
- **Effective learning rate scales as `alpha ÷ rank`.** `alpha = rank` means no scaling; `alpha < rank` quietly dampens learning (alpha 8 / rank 16 ≈ half LR). Set `alpha = rank` to start; this is the principled knob, not a magic number.
- **Train low, for a reason — make a "good citizen."** A LoRA that's lower-rank, not over-trained, and lands its sweet spot **below 1.0** stacks with other LoRAs without frying or dominating them. Over-baked high-magnitude LoRAs hijack a stack. *(The modest-delta principle is sound craft; precise "alpha must be X for stacking" prescriptions are folklore — strong sources disagree, so don't over-tune by ritual.)*

> **These Z-Image numbers are a community starting point and the tooling is new** — verify rank/LR/alpha against the **current Ostris AI-Toolkit** Z-Image config examples before a long run. The *relationships* above are stable across architectures; the *exact* Z-Image defaults are fast-moving.

---

## Assessing fit — is the LoRA actually working?

Judge a LoRA by **generated images, not the loss curve.** Loss barely moves in a way that predicts image quality; the community consensus is to evaluate visually. So **save several checkpoints** during the run (e.g. every few hundred steps) instead of only the last one.

**The standard evaluation: an XY grid of saved epochs × LoRA strength.** Put the **checkpoint/epoch on one axis** and **strength 0.1 → 1.0 on the other**, generate the grid on a couple of fixed test prompts, and read off the cell that's strongest. You're hunting the "Goldilocks" epoch — enough to capture the concept, not so much it locks up.

| Signal | What you see | Fix |
|---|---|---|
| **Good fit** | Concept reproduced *with flexibility* — you can change pose, clothing, scene, and it holds | ship that checkpoint |
| **Overfit** | Outputs drift toward the *training images themselves* — rigid/identical poses, baked-in backgrounds, fried color; only usable at low strength | fewer steps / earlier epoch; more dataset variety; lower rank |
| **Underfit** | Concept barely present — weak likeness, style doesn't transfer | more steps / higher LR; check captions actually bind the trigger |

> **A sub-1.0 sweet spot is normal — not an overfit verdict.** Many good LoRAs (especially styles, and anything you'll stack) land best around 0.6–0.9. Needing < 1.0 is not a sign the LoRA is "overcooked"; that's a common myth. Overfit is diagnosed by the *training-image drift* above, not by the sweet-spot weight.

---

## Debugging

| Symptom | Cause | Fix |
|---|---|---|
| Blurry output, identity collapse early | LR too high or adapter missing (Turbo) | Reduce LR to 5e-5; confirm adapter is loaded; retrain from scratch |
| Specific angles fail (especially back views) | Insufficient coverage in the training set | Add 5 more targeted images of those angles; retrain |
| Colours over-saturated, edges over-cooked | LoRA inference weight too high for this LoRA | Lower the weight (try 0.5–0.8; style LoRAs often want less) — see workflows §6 |
| Identity still generic at 2k steps | Too few images or insufficient caption specificity | Add more images; make captions more specific about identity markers |
| Identity drifts across seeds | LR too high or rank too high | Drop to rank 8, LR 5e-5 |

---

Once trained, see `references/workflows.md §6 — Using LoRAs` for loading and weight tuning. The draft-in-Turbo → finalize-in-Z-Image iteration loop is the **Default workflow** in `SKILL.md` and the layered pipeline in `workflows.md §2` — it's the same loop whether or not a LoRA is loaded.
