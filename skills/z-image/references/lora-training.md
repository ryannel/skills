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

**Rule:** vary one thing at a time. If you change both clothing and lighting in the same image, the LoRA cannot disentangle which features belong to the character. For the rotation series specifically, keep the subject description and lighting direction **byte-identical** across all eight views — change only the angle clause.

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

Once trained, see `references/workflows.md §6 — Using LoRAs` for loading, weight tuning, and the multi-stage iteration loop (draft in Turbo → finalize in Z-Image).
