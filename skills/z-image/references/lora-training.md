# Z-Image LoRA Training

## Loading a Z-Image LoRA

- **Recommended weight:** ~0.8 (official inference example uses `adapter_weights=[0.8]`; community range 0.7–0.9)
- **Why not 1.0:** Turbo at full strength overcooks saturation and edges and loses its speed characteristic
- **Trigger words:** Place at the very start of the prompt

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

**Rule:** vary one thing at a time. If you change both clothing and lighting in the same image, the LoRA cannot disentangle which features belong to the character.

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
| Colours over-saturated, edges over-cooked | LoRA loaded at weight 1.0 on Turbo | Drop to 0.8 at inference |
| Identity still generic at 2k steps | Too few images or insufficient caption specificity | Add more images; make captions more specific about identity markers |
| Identity drifts across seeds | LR too high or rank too high | Drop to rank 8, LR 5e-5 |

---

## Iteration workflow (prompting with a trained LoRA)

1. Draft in Turbo (8 steps in ComfyUI / 9 in diffusers, CFG 1.0, LoRA at 0.8) to find prompt and seed.
2. Once composition feels right, randomise seed — run 8–12 variants. Pick the strongest.
3. Re-render the winner in Z-Image (40 steps, CFG 4.0) for the final asset. Add negative prompt here.
4. Upscale afterward — Z-Image produces excellent structure; crisp microtexture comes from a separate upscale pass.

**The key constraint for LoRA dataset consistency:** when generating the training set rotation series, keep subject description and lighting direction byte-identical across all eight views — change only the angle clause.
