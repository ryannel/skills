# Z-Image LoRA Training

**This file covers only what is specific to Z-Image.** The suite's general LoRA-training reference is [`character-lora-training`](../../character-lora-training/). Dataset coverage protocols, caption-the-residual doctrine, evaluation method, adult/NSFW base selection, and the real-person likeness rules that decide whether a LoRA is publishable all live there. They are not repeated here. If you want cross-model LoRA craft, go to that file. This one assumes you have already decided to train on Z-Image.

> **Using** a LoRA (loading, weights, stacking, the QKV gotcha, cross-compatibility) is in `references/setup-and-workflows.md §6 — Using LoRAs`. This file is only about **making** one.

## Contents

1. Which variant to train on — train on Base, generate on Turbo
2. Dataset generation, the Z-Image way — 2.1 Style LoRAs, where the dataset inverts
3. Training with Ostris AI-Toolkit — 3.1 the required Turbo adapter · 3.2 hyperparameters
4. The fast path — RunPod + the Ostris template
5. Experimental methods and how Z-Image responds
6. Adult / NSFW work
7. Assessing fit — what is Z-Image-specific
8. Debugging

---

## 1. Which variant to train on — train on Base, generate on Turbo

The community-recommended path (including the official Tongyi-MAI HF discussion #18) is to **train the LoRA on undistilled Z-Image Base and generate with it on Z-Image-Turbo.** Base gives better cross-prompt control. A Turbo-trained LoRA tends to "fight" the distillation (blurry at 8 steps, clean only at ~30 — see `references/setup-and-workflows.md §6`). Train *on* Turbo only if you specifically want fast-delivery behavior baked in.

A Base-trained LoRA still **loads** on Turbo without error (shared S3-DiT). But it doesn't transfer perfectly. Face and identity soften, and you may need a strength bump `[contested]`. How much it degrades is genuinely disputed between strong sources. Test on the variant you'll actually deploy on rather than trusting either camp — the disagreement is laid out in `references/setup-and-workflows.md §6`.

---

## 2. Dataset generation, the Z-Image way

> The coverage protocol itself — how many images, which angles, how to caption them — is model-agnostic craft and lives in [`character-lora-training/references/dataset-and-captioning.md`](../../character-lora-training/references/dataset-and-captioning.md). The full character orchestration for Z-Image specifically — the Qwen-Image-Edit dataset factory, multi-outfit and multi-character craft, character failure modes — is in **`references/characters.md`**. This section only covers what changes *because it is Z-Image*.

Three things are Z-Image-specific about building the set:

**Generate the anchor in Z-Image itself.** Use one image: front three-quarter view, neutral expression, plain background, soft north-window light, 50 mm equivalent, 1024×1024. This makes the identity native to the model's own distribution, rather than something the LoRA has to drag it toward. `references/prompting-guide.md §8` Template A is exactly this shot.

**The in-model expansion path is img2img at low denoise** from that anchor. It works and needs nothing but Z-Image. But it drifts identity faster than an edit model at large angle changes, which is why `characters.md` prefers the Qwen-Image-Edit factory. Use img2img when you want to stay inside one install, or to fill a single missing angle.

**Captions are prose, not tags.** Z-Image reads through Qwen-3, an LLM encoder, so a caption is a natural-language sentence. It follows the same caption-the-residual principle as everywhere else — name the pose, clothing, background, lighting and angle, and leave the identity to the trigger — but expressed in sentences. Booru-style tag strings are the SDXL dialect and are actively wrong here. Include the angle and shot size explicitly in every caption, or the LoRA will conflate identity with the viewpoint it was mostly trained on.

### 2.1 Style LoRAs — the dataset inverts

A **style** LoRA flips the residual: you want the *look* to be what's left over. So **caption the content** of each image — the subject, scene, composition — across **diverse subjects** (people, objects, landscapes, not one repeated subject). The shared visual style then becomes the residual the LoRA binds to. The governing maxim: **consistency in the thing you're training, diversity in everything else.** If you train a style on one subject only, the LoRA entangles that subject *into* the style. If every image shares one palette, the LoRA locks that color cast onto everything.

Style-specific dataset rules, convergent across neurocanvas's Z-Image guide, alvdansen's published style-training notes and the Civitai style guides `[community — neurocanvas, alvdansen; convergent]`:

- **Size: 15–40 images** for Z-Image, diminishing returns above ~50. A well-curated 30 beats a sloppy 200 — the legacy "style needs 300+" figure is SDXL-era folklore; stronger bases need fewer examples.
- **Captions: short natural-language scene descriptions that never mention the style itself** — caption-the-residual expressed in prose. (On Flux-class models a captionless variant is genuinely contested — see [`flux-2`](../../flux-2/); for Z-Image the prose-residual approach is the documented community path.)
- **Trigger word: optional, often omitted.** If you use one, fold it into the sentence ("an illustration in the style of TRIGGER") — a bare leading token has no stable meaning to an LLM encoder.
- **Watch the palette**: include the style's full tonal range, and keep B&W images out of a color style set — narrow color statistics are what cause color-cast lock-in.
- **Capacity:** styles typically want **more rank than characters** — start rank 16, go 32 for texture-heavy styles (64 appears in realism work). The direction is agreed across sources; the exact ceiling is not `[flagged — rank ceiling unverified]`.
- **Ethics flag:** a single living artist's style trained without consent is the community's sharpest fault line (Civitai requires disclosure). Prefer self-made, licensed, or historic/aggregate aesthetics.

**The style acceptance test:** the LoRA passes when the style is recognizable on subjects that are *not* in the training set. During training, point the trainer's sample prompts at out-of-set subjects. Include at least one sample prompt *without* the trigger to catch style leakage early.

---

## 3. Training with Ostris AI-Toolkit

### 3.1 Required adapter for Z-Image-Turbo

When training on Z-Image-Turbo, the Ostris training adapter is **required**. Without it, the LoRA fights the distillation signal and produces blurry identity collapse.

Two variants ship in the `ostris/zimage_turbo_training_adapter` HF repo (referenced in the AI-Toolkit YAML config):
- `zimage_turbo_training_adapter_v1.safetensors` — default; stable
- `zimage_turbo_training_adapter_v2.safetensors` — experimental; often better for character work

> Z-Image (undistilled) does not require the training adapter.
>
> An alternative "de-turbo" route exists: train on Turbo *without* the adapter and accept that the LoRA undoes some distillation. Then **infer at 20–30 steps, CFG 2–3** instead of the 8-step preset `[community — neurocanvas, Tongyi-MAI #64]`. This is valid when you don't care about Turbo's speed; otherwise use the adapter. Tooling beyond AI-Toolkit: `tdrussell/diffusion-pipe` also supports Z-Image (ComfyUI-format output). It documents the model's **shift = 3** timestep setting, matching the `ModelSamplingAuraFlow` value at inference.

### 3.2 Hyperparameters (character LoRA, 15–25 images at 1024×1024)

| Parameter | Value `[community — Ostris AI-Toolkit configs; re-verify]` |
|---|---|
| Rank | 8–16 |
| Learning rate | 1e-4 (5e-5 for tight identity preservation) |
| Resolution | 1024×1024 |
| Steps | 2000–3000 |
| Hardware reference | RTX 5090: ~1 hour for 3k steps at these settings |

> **These are a starting point on new tooling, not settings to copy.** Verify rank/LR/alpha against the **current Ostris AI-Toolkit** Z-Image config examples before committing to a long run. The *relationships* between these knobs are stable across architectures, but the *exact* Z-Image defaults are fast-moving.

Two of those relationships decide whether the table above reads as sensible or arbitrary. Both are architecture-general — the full treatment is in [`character-lora-training`](../../character-lora-training/) — but they are worth having in front of you while you edit a Z-Image config:

- **Total steps ≈ images × repeats × epochs ÷ batch.** Doubling the dataset halves the epochs for the same step count. So the 2000–3000 figure is only meaningful alongside the 15–25 image assumption.
- **Effective learning rate scales as `alpha ÷ rank`.** `alpha = rank` means no scaling. `alpha < rank` quietly dampens learning (alpha 8 / rank 16 ≈ half LR). Set `alpha = rank` to start. The old "alpha above rank burns the image" rule is a myth. `alpha = 2×rank` is a legitimate, commonly-used config; it just doubles the effective LR, so compensate there.

**Train a "good citizen."** Make the LoRA lower-rank, not over-trained, with a sweet spot **below 1.0**. Such a LoRA stacks with other LoRAs without frying or dominating them. This matters on Z-Image specifically, because the realism and skin-texture LoRAs that fix the family's airbrushed default are things you will be stacking *with*. The modest-delta principle is sound craft. Precise "alpha must be X for stacking" prescriptions are folklore `[contested]`, so don't over-tune by ritual.

---

## 4. The fast path — RunPod + the Ostris template

Z-Image is unusually cheap to train. The published quick path is worth knowing because it lowers the cost of iterating on a dataset `[community — Prompting_Pixels, Civitai]`:

- **RunPod's official Ostris AI-Toolkit template** is a one-click deploy into a browser UI. No local install is needed, and there is a **low-VRAM toggle** in the UI for tight cards. Deployment mechanics: [`comfyui-on-runpod`](../../comfyui-on-runpod/).
- A reported run: **9 images, no captions at all, 3000 steps, ~1 hour on a 5090**, 1024×1024, for a simple character concept. Captionless training is contested in general (see [`character-lora-training`](../../character-lora-training/)), but it does work for straightforward replication. Z-Image's speed makes it cheap to test both ways.
- **The subject typically emerges by 1000–1500 steps.** If nothing recognisable has appeared by then, stop and look at the dataset rather than training longer.
- **Sample every ~250 steps, and put the trigger in the sample prompts.** Forget the trigger and the early samples look like the base model, which makes progress impossible to read.

With small datasets, diversity matters far more than count. It's the same coverage protocol as everywhere else, just with fewer images to carry it.

---

## 5. Experimental methods and how Z-Image responds

The weight-noising / depth-anchoring fork (full method in [`sdxl/references/lora-training.md`](../../sdxl/references/lora-training.md) §8) added **experimental Z-Image Turbo support**. Two findings came out of that specific to this family `[community — QuantumBogoSort, EmploymentLong9284; early]`:

- **Z-Image Turbo dislikes multi-resolution buckets** far more than Flux does. Bucketed training reportedly degrades quality noticeably versus **pure 1024 training**. That is the opposite of the Flux recipe, where varied buckets are part of the method.
- **Noise sigma tuned on Flux is too aggressive for ZiT.** One report: the concept's geometry was learned in half the steps, but style quality collapsed. Start well below the Flux value and raise carefully.

Both are early reports on an experimental method. `[flagged — re-verify]`

---

## 6. Adult / NSFW work

**Z-Image supports this work well, and has a mature LoRA ecosystem for it.** Roughly **46–47% of published Z-Image LoRAs are adult-flagged** (sampled 2026-08-13), on Turbo and Base alike. This figure includes anatomy-specific LoRAs, not only general realism ones. That is the signal that the base has usable coverage rather than needing capability taught in from scratch `[community — Civitai model API]`.

**The names behind that claim** (Civitai, sampled 2026-08-23 — 8–10 distinct anatomy LoRAs sit above ~2,500 downloads, so the ecosystem is healthy rather than thin): the general-purpose one is **"Z-Image Turbo NSFW LoRA"** (Peli86, ~26k downloads, v3 May 2026, Turbo-only). **"GodPussy"** (generatorofthingsreal) ships as a pair — a Turbo edition (~22k) plus a separate Base edition (~5k) — the clearest case of one author serving both variants. **"cum on body"** (er850, ~11k, Turbo, the trigger is the literal phrase) and Mistermango23's male-anatomy LoRA cover the Base side. The realism partners you'll stack with are **"Radiant Realism Pro"** (Escanor_art) and AI_Characters' **"Smartphone Snapshot Photo Reality"** (v8.0, trigger "amateur photo"), both Turbo `[community — Civitai model API, 2026-08-23]`. Anatomy publishing skews roughly **3:1 Turbo-tagged**, matching the ecosystem-wide lopsidedness in `references/setup-and-workflows.md §6`. The tag records intended runtime, not training variant, so a Turbo-only card is the norm, and the GodPussy split editions are what it looks like when an author bothers to publish both. These names ground "anatomy LoRAs exist"; they settle nothing about how LoRAs stack — the `[contested]` cautions in §3.2 stand unchanged.

Practical notes:

- **Both variants are served**, so the normal doctrine holds unchanged: **train on Base, generate on Turbo**. LoRAs exist for each.
- **Anatomy LoRAs stack with realism LoRAs.** Z-Image's airbrushed default (see the realism technique in `SKILL.md`) applies here too. The skin-texture and realism LoRAs that fix it are the same ones. Expect to stack, and train a good citizen accordingly.
- The general rule still governs: limits are **training-data coverage, not refusal**, so no encoder swap or conditioning trick changes an outcome. Mechanism in [`character-lora-training/references/nsfw-training.md`](../../character-lora-training/references/nsfw-training.md) §1.
- **Publishing is the binding constraint** — real-person likeness is prohibited on Civitai regardless of rating. See [`publishing-and-likeness.md`](../../character-lora-training/references/publishing-and-likeness.md).

---

## 7. Assessing fit — what is Z-Image-specific

The evaluation method — the checkpoint × strength grid, judging blind, scoring likeness separately from prompt-adherence, the held-out probe set, and why loss is a weak signal — is model-agnostic and is owned by [`character-lora-training/references/evaluation-and-tooling.md`](../../character-lora-training/references/evaluation-and-tooling.md). Run it from there. Judge by generated images, not the loss curve, and **save several checkpoints** during the run so you have a series to grid.

Three things bite specifically on Z-Image:

- **Grid on the variant you will ship on.** A Base-trained LoRA evaluated on Base and deployed on Turbo will look worse in production than it did in the grid (§1). So if Turbo is the deployment target, put Turbo in the grid.
- **Grid at Turbo's real settings**, 8 steps and CFG 1.0. Soft results at 8 steps that clean up at ~30 are the distillation-fighting signature, not underfitting. No amount of extra training fixes them.
- **A sub-1.0 sweet spot is normal, and doubly so here.** Anything you intend to stack under the realism/skin LoRAs should land below 1.0. Needing < 1.0 is not an overfit verdict.

---

## 8. Debugging

| Symptom | Cause | Fix |
|---|---|---|
| Blurry output, identity collapse early | LR too high or adapter missing (Turbo) | Reduce LR to 5e-5; confirm adapter is loaded; retrain from scratch |
| Blurry only at 8 steps, clean at ~30 | Trained on Turbo — the LoRA is fighting the distilled landing trajectory | Retrain on Base, or use the adapter; a DistillPatch LoRA is the inference-time patch (`references/setup-and-workflows.md §6`) |
| Specific angles fail (especially back views) | Insufficient coverage in the training set | Add 5 more targeted images of those angles; retrain |
| Colours over-saturated, edges over-cooked | LoRA inference weight too high for this LoRA | Lower the weight (try 0.5–0.8; style LoRAs often want less) — see `references/setup-and-workflows.md §6` |
| Identity still generic at 2k steps | Too few images or insufficient caption specificity | Add more images; make captions more specific about identity markers |
| Identity drifts across seeds | LR too high or rank too high | Drop to rank 8, LR 5e-5 |
| LoRA loads but "barely does anything" | Not a training failure — the diffusers-format QKV loading gotcha | Update ComfyUI before touching weights (`references/setup-and-workflows.md §6`) |

---

Once trained, see `references/setup-and-workflows.md §6 — Using LoRAs` for loading and weight tuning. The draft-in-Turbo → finalize-in-Z-Image iteration loop is the **Default workflow** in `SKILL.md` and the layered pipeline in `references/setup-and-workflows.md §2`. It's the same loop whether or not a LoRA is loaded.
