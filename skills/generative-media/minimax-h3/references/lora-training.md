# MiniMax H3 — LoRA training and the LoRA ecosystem

> **Shared craft lives in [`character-lora-training`](../../character-lora-training/)** — dataset coverage, caption-the-residual, evaluation, adult/NSFW base selection, and the real-person likeness rules that decide whether a LoRA is publishable. This file covers what is specific to this model.


**Short version: there is no settled training doctrine for H3 yet.** The model was released 2 August 2026. This file records what is actually known eleven days later, and marks the rest as unknown rather than filling it with plausible-sounding numbers. That is the honest state, and it will date quickly — check `freshness.json` and re-verify before relying on any of it.

---

## What exists

**Speed / Turbo LoRAs are the dominant artefact so far, and they are real and usable.** The original is by **larryvrh**, with ComfyUI-compatible conversions by **drbaph** (`drbaph/MiniMax-H3-Turbo-Lora-ComfyUI`). Recipe, settings and the audio caveat are in SKILL.md and [`setup-and-workflows.md §9`](setup-and-workflows.md) — the short version is 6–8 steps, `beta` scheduler, strength 1.0, and, since ComfyUI v0.31.0, the core `ModelSamplingMiniMaxH3` node's `audio_shift` rather than a third-party sampler.

**As of 2026-08-22 there is an official one.** `lightx2v/Minimax-h3-Turbo` publishes `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` (4–8 step) — a first-party ComfyUI-format release from the team that does this for the whole open-video field. Prefer it as the default; the community conversions remain in wide use and are still what most posted workflows reference. A separate widely-repeated tip cuts across both: **run speed LoRAs at 0.8–0.85 rather than 1.0**, which contradicts the LoRA authors' own recipe and is `[contested]`.

**Non-speed LoRAs now exist too**, which is the more meaningful signal: `Mamad8/MaxiMin-HHH-R2V-ThisIsFine` is a detail LoRA in circulation for Ref2VA work. So "the ecosystem is speed-only" is no longer strictly true — but it is still overwhelmingly true by volume.

What that tells you: the community's first priority was **making a 33B model with a 32B encoder cheap enough to run**, not teaching it new subjects. That is the usual order for a large release, and it means the acceleration story matured well before the customisation one — see the four-layer acceleration stack in [`setup-and-workflows.md §9`](setup-and-workflows.md), which matured while the training story is still a blank.

**One thing the Turbo LoRA settles: weights transfer between the task checkpoints.** It was trained against **FL2VA** and is reported working on **Ref2VA** as well `[community — Organix33; re-verify]`. So the two checkpoints are close enough that a LoRA is not automatically checkpoint-locked — useful, and the opposite of what you would assume from "task-specific checkpoints." Still worth validating on your target checkpoint rather than assuming.

**Third-party *checkpoints* exist, which is stronger evidence than LoRAs.** `RedCraft | REDMIX Hybrid A2A beta1 … Lightning 8` is a MiniMax H3 checkpoint on Civitai and, at ~343k downloads, the most-downloaded H3 artefact anywhere. Whether it is a genuine finetune, a merge, or a repackaged quant is **not established here** `[flagged — re-verify]` — but somebody is doing more than converting weights, and the hybrid FL2VA/Ref2VA builds in `setup-and-workflows.md` §5 prove that surgical tensor-level work on H3 is tractable in the community.

**What is not established** `[flagged — re-verify]`:

- Which trainer supports H3, and how well. `musubi-tuner`, `diffusion-pipe` and `ai-toolkit` are the obvious candidates by track record, but H3 support status is unverified here.
- Any hyperparameter consensus — rank, alpha, learning rate, optimiser, timestep handling. Note that the released Turbo LoRA's own training details (it ships as versioned checkpoints, EMA and non-EMA, at steps 500/600/850) suggest an ordinary LoRA training setup is viable; the recipe just is not published.
- Whether style, character or motion LoRAs behave differently on a dense omni-modal transformer than on the video-only models the community's instincts come from.
- **Whether audio can be trained at all.** H3 generates audio from the same transformer, so in principle a LoRA could affect voice or sound character. Nobody appears to have demonstrated this. If it works, it is a genuinely new capability with no precedent in this suite — and given that the Turbo LoRA *degrades* audio as a side effect, audio is demonstrably reachable from LoRA weights.

---

## The one thing you must get right

**Train on a non-pruned checkpoint.**

The `pruned` builds — including `pruned_int8_convrot`, which the official templates default to — drop the ~13B of AdaLN-branch parameters that can be precomputed and cached for inference. The model card is explicit that MiniMax released the **complete** weights *"to support further development, including fine-tuning,"* and equally explicit that the AdaLN parameters *"do not need to be loaded for inference-only deployment."*

So the build you should be running for speed is exactly the build you must not train on. Take `minimax_h3_{fl2va|ref2va}_bf16.safetensors` for any training run.

This is the H3 analogue of `wan-2-2`'s two-LoRA rule: an architecture detail that silently invalidates a training run if you miss it.

---

## Which checkpoint to train

H3 ships two task-specific checkpoints, and they are **not interchangeable**:

| Checkpoint | Train it for |
|---|---|
| **FL2VA** | Text-to-video and first/last-frame work — the general-purpose path |
| **Ref2VA** | Multi-reference work, including anything involving reference audio |

A LoRA trained against one has no defined meaning for the other. Whether weights transfer at all between them is **unknown** — they share an architecture but are separately trained task specialists. Assume they do not until someone demonstrates otherwise.

---

## Before you train, ask whether you need to

Reference conditioning is unusually strong here, and it is free. Ref2VA takes up to 9 images, 3 video clips and 3 audio clips — for many jobs that a LoRA would traditionally solve (a specific character, a specific voice, a specific look), **passing references is the cheaper and currently better-supported path**. See `characters.md`.

Train when you need something summonable by prompt across arbitrary contexts without carrying references, or when the reference budget genuinely cannot express what you want. On a model this young, that bar is higher than usual.

---

## Datasets, if and when

Nothing H3-specific is established, so the transferable principles from the suite apply and nothing more:

- **Caption the residual** — describe what varies, not what is constant. [`character-lora-training`](../../character-lora-training/) is the suite's full treatment; it is model-independent by design.
- **Character datasets need angle and expression diversity**; style datasets need **subject** diversity, and the acceptance test is that the style survives on out-of-set subjects.
- **Single-frame vs clip training** is the cost decision on every video model — stills for appearance, clips for motion. Whether H3 supports single-frame training is unverified.
- **If audio is in scope**, no established practice exists at all. Anyone doing this is doing it first.

---

## Evaluating

Two things worth saying even without H3-specific data:

**Evaluate without speed LoRAs loaded.** Distillation alters the sampling trajectory; judging your LoRA through a Turbo LoRA conflates two effects and will have you tuning the wrong thing. Validate clean, then check the combination separately since that is how it will be run.

**Evaluate the audio separately from the picture.** This is not hypothetical on H3 — the released Turbo LoRA is the worked example: it accelerates the picture acceptably while **breaking the audio**, because the two modalities are scheduled separately. A LoRA that improves frames while degrading voice or ambience is a live failure mode, and you will not see it if you only look at stills. Listen to every evaluation.

---

## Adult / NSFW work

Community reports are that **H3 does not meaningfully refuse** — what looks like censorship presents as training-data gaps, with anatomy degrading rather than generations being blocked. Reference images reportedly help materially, which fits the diagnosis: you are supplying coverage the model is thin on rather than defeating a filter `[community — re-verify]`.

Two consequences specific to H3:

- **Try Ref2VA before training.** Nine images, three video clips and three audio clips of reference conditioning is a lot of signal, it is free, and on a model this young it is much better supported than training. See `characters.md`.
- **Ref2VA is the right mode for this work specifically**, not just the convenient one. You can still pass start and end frames, but you can *also* pass anatomy references, and a start frame behaves as a strong guide the model adjusts toward the prompt rather than a fixed copy — which is usually what you want. Supply a **nude reference** so the model knows what is underneath; **close-up anatomy references substitute** when you have no full-body nude of that character. `[community — nsfwVariant, throwaway0204055]`
- **The craft that actually fixes explicit output is prompt ordering, not weights.** H3 assumes sequential actions unless told otherwise, and the phasing-clothes-through-limbs failure everyone hits is an under-description problem the model is adherent enough to be talked out of. Allow **≥3 s per garment**, timestamp each step, work near **0.8 MP**, and use **30 steps rather than 20** — which improves cloth physics *and* audio quality. Full treatment in [`prompting-guide.md` §8](prompting-guide.md#8-ordering-timing-and-the-shot-list).
- **MiniMax runs automated moderation** on submitted text, images and video through its hosted surfaces. That governs the API and app rather than local inference, and it does not change your obligations under the licence — which, as the SKILL.md opens with, excludes several major territories outright. Read [`character-lora-training/references/publishing-and-likeness.md`](../../character-lora-training/references/publishing-and-likeness.md) before building anything on a real likeness.

General doctrine — base-model coverage, explicit captioning, why abliterated encoders do nothing — is in [`character-lora-training/references/nsfw-training.md`](../../character-lora-training/references/nsfw-training.md).

## Re-verify

This file is the least reliable in the skill and is written to be replaced. Before acting on it, check: whether a named trainer has shipped H3 support, whether hyperparameters have converged anywhere reproducible, whether anyone has trained audio behaviour, and whether FL2VA↔Ref2VA transfer has been tested. This is a tracked item in `freshness.json`.
