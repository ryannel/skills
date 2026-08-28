# Wan 2.2 — LoRA training

> **Shared craft lives in [`character-lora-training`](../../character-lora-training/)** — dataset coverage, caption-the-residual, evaluation, adult/NSFW base selection, and the real-person likeness rules that decide whether a LoRA is publishable. This file covers what is specific to this model.


This file is about *making* a LoRA. Loading and stacking LoRAs is covered in `setup-and-workflows.md`, and deploying a character is covered in `characters.md`.

---

## 1. The two-expert question

**The default answer: train two LoRAs from the same dataset, one per expert, and load both.**

This follows from the architecture rather than from convention. A LoRA patches specific weights, and the high-noise and low-noise experts are different weights. A LoRA trained against one expert does nothing to the other, and the schedule runs both experts.

`musubi-tuner` exposes this directly. It has a `dit_high_noise` path alongside `dit`, plus `timestep_boundary` and `discrete_flow_shift` settings that control where and how training straddles the noise levels.

The split matters in practice because each expert learns something different:

| Expert | Governs | A LoRA here changes… |
|---|---|---|
| **High noise** | Early denoising — layout, structure, **motion** | How the subject is posed and how it moves |
| **Low noise** | Late denoising — texture, detail, **appearance** | What the subject looks like |

**Contested: can you train only the low-noise expert?** `[contested]`

Some authors do, and they report acceptable results for appearance-only work. Training one expert halves the cost and produces one file to manage. The counter-argument is structural rather than empirical: motion and layout are settled before the boundary, so a low-noise-only LoRA *cannot* affect them, whatever the sample images suggest.

The honest resolution: **low-noise-only is a legitimate shortcut for appearance, but it is not a general substitute.** If your LoRA is a face or a style, it may be all you need. If it is a motion, a body type, or anything that changes how the subject occupies the frame, train both experts. When you see a single-file Wan 2.2 LoRA distributed, check which expert it targets before concluding it is broken.

**A known gotcha:** musubi-tuner has an open report (issue #569) of a high+low training run emitting only one LoRA file. **Check you have two artefacts** before concluding the training worked. A missing half presents as "the LoRA sort of works," not as an error. `[flagged — re-verify]`

---

## 2. Trainers

| Trainer | Status |
|---|---|
| **`kohya-ss/musubi-tuner`** | The default. Explicit two-expert support. Same author as sd-scripts, so the discussion culture that made sd-scripts the best craft source carries over — discussion #455 is the main Wan 2.2 thread |
| **`tdrussell/diffusion-pipe`** | The usual second opinion, and the better source for per-model timestep/shift behaviour |
| **ComfyUI-native trainer nodes** | Wrappers around musubi-tuner exist (e.g. a Wan 2.2 trainer node supporting single-frame mode and a high/low noise switch). Convenient; the underlying settings are musubi's |

---

### Choosing between them

| | `musubi-tuner` | `ai-toolkit` |
|---|---|---|
| Wan support | Purpose-built for Wan 2.1/2.2, with explicit two-expert handling | Wan I2V in the UI; supports 5B and 14B, with RunPod/Modal recipes |
| Interface | CLI, config-driven | No-code web UI plus CLI |
| Low-VRAM | FP8 and block-swap, well documented | Layer offloading, low-VRAM toggle |
| Best for | Full control, and anything touching the expert split | Getting a first run out quickly |

**musubi requires pre-caching.** Latents and text-encoder outputs are cached by separate scripts before training starts. People miss this step, because the training command fails in a way that does not obviously say "you skipped the cache."

**Image-only datasets are a first-class mode**, and that is what makes single-frame training practical. The dataset is a folder of `.jpg`/`.png` files with **same-name `.txt` caption sidecars**. The logs confirm the mode with `is_image_dataset: True` plus bucketing. Check for that line, since a misconfigured path silently trains on nothing.

**VRAM in practice:** an image-dataset LoRA needs roughly **12 GB**. FP8 plus block-swapping has fit **I2V LoRA training into 16 GB** `[community — re-verify]`. For deployment mechanics on rented GPUs, see [`comfyui-on-runpod`](../../comfyui-on-runpod/).

## 3. Hyperparameters

These are attributed starting points, not settled law. Named authors differ, and the ranges below reflect real disagreement rather than hedging `[community — musubi-tuner #455, Civitai guides; re-verify]`.

| Parameter | Starting point | Notes |
|---|---|---|
| Rank / alpha | **32 / 16** | 64 for detailed identity work; higher ranks cost VRAM and overfit faster on small sets |
| Learning rate | **~2e-4** | Some authors run **3e-4** on the **high-noise** LoRA specifically when it only needs motion and layout |
| Optimiser | AdamW8bit typical | LoRA+ with a ratio of ~4 at a lower base LR (~3e-5) is a reported alternative |
| Batch size | **1–2** at 16–24 GB | |
| `timestep_boundary` | Leave at the trainer default unless you know why | It defines where training treats the expert split; moving it changes what each LoRA learns |
| `discrete_flow_shift` | Trainer default | Interacts with the inference-side `ModelSamplingSD3` shift |

**Train both halves on the same dataset and the same seed.** If the datasets diverge across experts, the resulting pair disagrees with itself, and that reads as texture that doesn't match the motion.

---

## 4. Datasets

**Video clips vs single frames** is the decision that most affects cost:

| | Use when | Cost |
|---|---|---|
| **Single-frame (image) training** | The target is **appearance** — a face, an object, a style | Much cheaper; datasets are ordinary image sets; VRAM close to image-LoRA training |
| **Video-clip training** | The target involves **motion** — a gait, a gesture, a physical behaviour | Substantially more expensive; frame count multiplies memory |

Single-frame training is the right default for characters and styles. It also composes naturally with the still-first pipeline: the same curated image set you would use to train an image-model character LoRA works here. Reach for video clips only when the thing you are teaching genuinely happens over time.

Dataset construction for appearance work follows still-image practice. See [`character-lora-training`](../../character-lora-training/) for the underlying craft: caption-the-residual, the character vs style captioning inversion, subject diversity for styles, and the out-of-set acceptance test. Those principles are model-independent. What changes here is that you run the resulting dataset through training twice, once per expert.

For video clips: keep clips short and consistent in frame rate, sample so the motion of interest is actually present in most clips, and bucket by resolution as you would images. Wan is trained at 16 fps for the 14B, so datasets far from that frame rate will fight the model's temporal priors.

---

## 4a. Adult / NSFW work

Wan 2.2 has an **active adult LoRA ecosystem** — 40+ community LoRAs across T2V and I2V, with ai-toolkit support on consumer GPUs `[community — re-verify]`. The general doctrine is in [`character-lora-training/references/nsfw-training.md`](../../character-lora-training/references/nsfw-training.md); two things are specific to video and to Wan.

**Automated captioners fail on adult footage**, so the community captions manually. On a video dataset, where frame count already makes labelling the expensive part, this is a serious cost multiplier. It is also the strongest practical argument for **single-frame training** whenever the target is appearance rather than motion: the same curated stills, ordinary image captioning, and a fraction of the labour.

**Check whether a merge has already done it.** Much of this ecosystem also ships as merged checkpoints with the adult LoRAs baked in. When one covers your subject, it is often the better answer than a LoRA. That includes failures a LoRA cannot fix, because a LoRA cannot give the base a prior it does not have (SKILL.md § *When nothing you change moves the result*). If you go the merge route, **do not also load the LoRA**: the merge already carries its delta, and applying it twice puts the weights off the distribution the merge was tuned on. Settings and traps are in [`setup-and-workflows.md §4a`](setup-and-workflows.md#4a-running-a-community-merge).

**The two-expert rule still applies.** Appearance lives in the low-noise expert; motion and pose live in the high-noise one. So an appearance-only LoRA trained on stills genuinely can skip the high-noise half, while anything about how a body moves cannot. That is the same contested question as §1, and adult work is where it most often comes up.

## 5. Evaluation

Video LoRA evaluation is harder than image evaluation, because a still frame does not tell you whether motion survived.

1. **Grid on the low-noise half first** — epoch × strength, judging identity or style on single frames. This is cheap, and it isolates appearance.
2. **Then test motion** with the high-noise half loaded, on prompts with clear physical action. This is where an over-trained high-noise LoRA reveals itself: motion becomes stiff, repetitive, or collapses toward whatever the training clips did.
3. **Test out-of-distribution.** A character LoRA should hold in scenes unlike the dataset, and a style LoRA should be recognisable on subjects it never saw. If it only works on near-copies of training data, it memorised.
4. **Check both halves are actually loaded** when evaluating — see the issue #569 gotcha above.

**Overfitting signals specific to video:** motion that repeats the same trajectory regardless of prompt; the subject snapping to a training pose at the start of every clip; backgrounds from the dataset bleeding into unrelated scenes.

---

## 6. Speed LoRAs during training and evaluation

Evaluate **without** the lightx2v 4-step LoRAs loaded. They alter the sampling trajectory substantially, and judging your LoRA through them conflates two effects. You will misattribute the speed LoRA's motion flattening to your own training.

Once the LoRA is validated, check the combination separately, since that is how most people will actually run it. Stacking a trained pair with a speed pair means **four LoRAs**, two per expert.
