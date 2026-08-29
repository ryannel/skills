# MiniMax H3 — LoRA training and the LoRA ecosystem

> **Shared craft lives in [`character-lora-training`](../../character-lora-training/)** — dataset coverage, caption-the-residual, evaluation, adult/NSFW base selection, and the real-person likeness rules that decide whether a LoRA is publishable. This file covers what is specific to this model.


**Short version: training doctrine for H3 is forming, and most of it converges.** The model was released 2 August 2026. The trainers all landed in the second half of that month, and this file records what the community had converged on by 2026-08-29. None of it has been validated first-hand in this suite. The advice below is the published, community-consensus method, marked honestly as such. Check `freshness.json` and re-verify the marked numbers before a long training run.

---

## What exists

**Speed / Turbo LoRAs were the first artefacts to mature, and they are real and usable.** The original is by **larryvrh**, and **drbaph** publishes ComfyUI-compatible conversions of it (`drbaph/MiniMax-H3-Turbo-Lora-ComfyUI`). The recipe, the settings and the audio caveat are in SKILL.md and [`setup-and-workflows.md §9`](setup-and-workflows.md). In short: 6–8 steps, the `beta` scheduler, strength 1.0, and, since ComfyUI v0.31.0, the `audio_shift` input on the core `ModelSamplingMiniMaxH3` node instead of a third-party sampler.

**As of 2026-08-22 there is an official one.** `lightx2v/Minimax-h3-Turbo` publishes `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` (4–8 step). It is a first-party ComfyUI-format release from the team that does this for the whole open-video field, so prefer it as the default. The community conversions remain in wide use, and most posted workflows still reference them. One widely-repeated tip cuts across both: **run speed LoRAs at 0.8–0.85 rather than 1.0**. This contradicts the LoRA authors' own recipe and is `[contested]`. The lightx2v repo has since refined it. Their Turbo-SLA discussion reports that the Ref2VA-distilled 4-step Turbo LoRA, run at **~0.1 strength with 8-step inference**, gives the best facial consistency — even on FL2VA `[community — lightx2v Turbo-SLA discussion #3; re-verify]`. If your problem is identity drift under a speed LoRA, try that recipe before abandoning acceleration. A second first-party option also exists now: Alibaba PAI's **PDD Acc LoRA** (2026-08-26) is an 8-step accelerator, rank 64, 1.4 GB, run at strength 1.0 `[community — Alibaba PAI release; re-verify]`.

**The ecosystem is no longer speed-only, and it is no longer small.** Civitai carries large NSFW concept LoRAs — `[MMH3] Mystic XXX` (~46.6k downloads) and `HMNSFW AIO` (~43.6k) — plus a modular anatomy-part family from the same HM line (HMPussy ~27.5k, HMPenis ~16k, HMCumshot ~15.4k, HMBreasts ~9.6k), the Ref2VA-tuned "After Midnight" family, the `Faster! Harder! Shake Harder!` motion booster (~18.5k), and character LoRAs (nagisa, Lain Iwakura, h3sully) `[community — Civitai listings; re-verify]`. `Mamad8/MaxiMin-HHH-R2V-ThisIsFine` remains in circulation as a Ref2VA detail LoRA.

**Audio is demonstrably trainable.** A female-moans-plus-body-writhing audio LoRA by moawxx has ~6.8k downloads on Civitai `[community — Civitai, moawxx; re-verify]`. That settles the question this file used to leave open: a LoRA can teach H3 sound behaviour, not just degrade it. Character-voice training, the harder version of the same idea, has still not been shown.

What the timeline tells you: the community's first priority was **making a 33B model with a 32B encoder cheap enough to run**, not teaching it new subjects. That is the usual order of events for a large release. The acceleration story matured first — see the four-layer stack in [`setup-and-workflows.md §9`](setup-and-workflows.md) — and the training story caught up in the second half of August.

**One thing the Turbo LoRA settles: weights transfer between the task checkpoints.** It was trained against **FL2VA** and is reported working on **Ref2VA** as well `[community — Organix33; re-verify]`. So the two checkpoints are close enough that a LoRA is not automatically checkpoint-locked. That is useful, and it is the opposite of what you would assume from the phrase "task-specific checkpoints." It is still worth validating on your target checkpoint rather than assuming.

**Third-party *checkpoints* exist, which is stronger evidence than LoRAs.** `RedCraft | REDMIX Hybrid A2A beta1 … Lightning 8` is a MiniMax H3 checkpoint on Civitai. At ~343k downloads, it is the most-downloaded H3 artefact anywhere. Whether it is a genuine finetune, a merge, or a repackaged quant is **not established here** `[flagged — re-verify]`. But it shows somebody is doing more than converting weights, and the hybrid FL2VA/Ref2VA builds in `setup-and-workflows.md` §5 prove that the community can do surgical tensor-level work on H3.

---

## Which trainer

All of these landed in late August 2026. Support depth varies a lot, so pick by what you are training `[community — trainer repos and docs; re-verify]`:

| Trainer | H3 support | Notes |
|---|---|---|
| **ai-toolkit** | Mainline. T2V and I2V from Aug 3, Ref2VA from ~Aug 13, an official vid2vid tutorial ~Aug 20. | Trains directly on the ComfyUI quantized weights, so no separate training download. |
| **musubi-tuner** | Dev branch only (PR #1030, unmerged). The deepest support: T2VA, FL2VA, Ref2VA, plus experimental one-frame image training. | Adds guidance-distillation protection (`--h3_guidance_loss_scale 4.0`, `--h3_guidance_loss_sigma_min 0.15`), precaches text embeds so the 32B encoder is never resident during training, enforces batch 1, supports `--blocks_to_swap 48` of 50 and `--prune_adaln`. |
| **diffusion-pipe** | T2I and T2VA only (2026-08-08). | Wants CFG-augmented training. |
| **SimpleTuner** | Dedicated quickstart with 24/32/48/80 GB presets. | Sets `flow_schedule_shift 12.0` for video and `audio_flow_schedule_shift 3.0` for audio. |
| **fal.ai** (hosted) | Four trainers, $0.015/step. | Video clips only — it rejects stills with a 422. |

Known bug: musubi's backward pass errors with CUBLAS on the pruned-INT8 base (musubi #1059) `[community — musubi-tuner #1059; re-verify]`.

---

## Hyperparameters that converge

Independent sources land on the same numbers, which is the best signal available short of a controlled study. None of this has been validated first-hand in this suite `[community — fal.ai examples, musubi-tuner docs, note.com writeup; re-verify]`:

- **Rank 16, alpha 16.** In fal's blind votes, rank 16 beat both 32 and 64.
- **LR 1e-4** with adamw8bit. Use 2e-4 when you need fast convergence and can tolerate the risk.
- **Step counts scale with data:** ~1000 steps for a 31-image stills run, 1500 on 53 clips, 3000+ on 176 clips in fal's published examples.
- **Timestep focus band 0.4–0.8** — the musubi docs call it the range "where content is decided."

One caveat on provenance: fal's published step counts come from a style-adapter run, not a character run, so treat them as scale hints rather than a character recipe.

**A full low-VRAM proof exists.** A note.com writeup demonstrates single-frame image-only character training on an RTX 4070 12 GB: rank 16 / alpha 16, LR 1e-4, adamw8bit (weight decay 1e-4), 1000 steps at 512², `num_frames: 1`, ConvRot INT8 DiT plus NVFP4 encoder, 6–7 hours, 11.7 GB VRAM with ~35 GB of RAM offload `[community — note.com writeup; re-verify]`. The same writeup carries a dataset lesson worth keeping: 31 close-up face images beat 32 full-body images for identity. Rough VRAM bands: INT8 + NVFP4 + block swap needs about 20–24 GB, and bf16 needs 48–50 GB `[community; re-verify]`.

**What is still unverified** `[flagged — re-verify]`: whether style, character or motion LoRAs behave differently on a dense omni-modal transformer than on the video-only models the community's instincts come from. The numbers above converge, but nobody has published a controlled comparison.

---

## The one thing you must get right

**Know which build your trainer can actually train on.**

An earlier version of this file said to train only on the non-pruned bf16 checkpoints. That rule is now wrong. The `pruned` builds drop the ~13B of AdaLN-branch parameters that can be precomputed for inference, and the model card released the **complete** weights *"to support further development, including fine-tuning."* But both musubi-tuner and ai-toolkit now treat the pruned and INT8 checkpoints as first-class training bases — ai-toolkit trains directly on the ComfyUI quantized weights, and musubi even offers `--prune_adaln` itself `[community — trainer docs; re-verify]`.

Two caveats keep the choice from being free:

- Musubi's backward pass currently fails with a CUBLAS error on the pruned-INT8 base (musubi #1059) `[community; re-verify]`. If you hit it, switch base rather than debugging CUBLAS.
- `minimax_h3_{fl2va|ref2va}_bf16.safetensors` remains the safest base when you have the ~48–50 GB of VRAM it needs. It is the build with nothing removed, so nothing can silently go missing from the run.

The general lesson survives even though the specific rule did not: on H3, the build you run for speed and the build you train on are separate decisions. Check your trainer's supported bases before downloading anything.

---

## Which checkpoint to train

H3 ships two task-specific checkpoints, and they are **not interchangeable**:

| Checkpoint | Train it for |
|---|---|
| **FL2VA** | Text-to-video and first/last-frame work — the general-purpose path |
| **Ref2VA** | Multi-reference work, including anything involving reference audio |

They share an architecture but are separately trained task specialists. The Turbo LoRA shows that transfer is possible: trained on FL2VA, reported working on Ref2VA `[community — Organix33; re-verify]`. Whether an *identity* LoRA transfers as cleanly is untested, and so is the prior question of which checkpoint makes the better training base for identity in the first place. Until someone publishes that comparison, train against the checkpoint you will generate with, and validate on it.

---

## Before you train, ask whether you need to

Reference conditioning is unusually strong on this model, and it is free. Ref2VA takes up to 9 images, 3 video clips and 3 audio clips. Many jobs that a LoRA would traditionally solve — a specific character, a specific voice, a specific look — can be done by **passing references, which is the cheaper and currently better-supported path**. See `characters.md`.

Train when you need something summonable by prompt across arbitrary contexts without carrying references, or when the reference budget genuinely cannot express what you want. On a model this young, that bar is higher than usual.

**And when you do train a character, the LoRA and the references are partners, not alternatives.** The converging doctrine across guides is that a character LoRA *supplements* Ref2VA references rather than replacing them: the LoRA anchors the identity, and the references stop the model inventing detail the LoRA left underspecified `[community — corroborated across guides; re-verify]`. Plan your Ref2VA reference set alongside the training run, not instead of it. See `characters.md` for how the reference budget is spent.

---

## Datasets

The transferable principles from the suite apply, and a few H3-specific facts now sit alongside them:

- **Caption the residual** — describe what varies, not what is constant. [`character-lora-training`](../../character-lora-training/) is the suite's full treatment of this, and it is model-independent by design.
- **Character datasets need angle and expression diversity.** Style datasets need **subject** diversity, and the acceptance test is that the style survives on out-of-set subjects.
- **Single-frame vs clip training** is the cost decision on every video model: stills for appearance, clips for motion. H3 supports single-frame training — musubi's experimental one-frame mode, and the 12 GB proof run above used `num_frames: 1` throughout `[community — note.com writeup; re-verify]`. Note that fal's hosted trainers refuse stills, so single-frame work is local-only for now.
- **Close and tight beats wide for identity.** The one published comparison found 31 close-up face images beat 32 full-body images `[community — note.com writeup; re-verify]`. One data point, but it matches the suite's general dataset doctrine.
- **If audio is in scope**, one existence proof is published (the moawxx audio LoRA above) but no recipe is. SimpleTuner's `audio_flow_schedule_shift 3.0` is the only audio-specific training knob documented anywhere `[community — SimpleTuner quickstart; re-verify]`. Anyone training character voice is still doing it first.

---

## Evaluating

Two things are worth saying even without H3-specific data:

**Evaluate without speed LoRAs loaded.** Distillation alters the sampling trajectory. If you judge your LoRA through a Turbo LoRA, you conflate two effects and end up tuning the wrong thing. Validate clean, then check the combination separately, since the combination is how it will actually be run.

**Evaluate the audio separately from the picture.** This is not hypothetical on H3. The released Turbo LoRA is the worked example: it accelerates the picture acceptably while **breaking the audio**, because the two modalities are scheduled separately. A LoRA that improves frames while degrading voice or ambience is a live failure mode, and you will not see it if you only look at stills. Listen to every evaluation.

---

## Adult / NSFW work

Community reports say **H3 does not meaningfully refuse**. What looks like censorship presents as training-data gaps: anatomy degrades rather than generations being blocked. Reference images reportedly help a lot, which fits the diagnosis — you are supplying coverage the model is thin on rather than defeating a filter `[community — re-verify]`.

Two consequences specific to H3:

- **Try Ref2VA before training.** Nine images, three video clips and three audio clips of reference conditioning is a lot of signal. It is free, and on a model this young it is much better supported than training. See `characters.md`.
- **Ref2VA is the right mode for this work specifically**, not just the convenient one. You can still pass start and end frames, and you can *also* pass anatomy references. A start frame behaves as a strong guide the model adjusts toward the prompt rather than a fixed copy, which is usually what you want. Supply a **nude reference** so the model knows what is underneath. **Close-up anatomy references substitute** when you have no full-body nude of that character. `[community — nsfwVariant, throwaway0204055]`
- **The craft that actually fixes explicit output is prompt ordering, not weights.** H3 assumes sequential actions unless told otherwise. The phasing-clothes-through-limbs failure everyone hits is an under-description problem, and the model is adherent enough to be talked out of it. Allow **≥3 s per garment**, timestamp each step, work near **0.8 MP**, and use **30 steps rather than 20**, which improves cloth physics *and* audio quality. The full treatment is in [`prompting-guide.md` §8](prompting-guide.md#8-ordering-timing-and-the-shot-list).
- **MiniMax runs automated moderation** on submitted text, images and video through its hosted surfaces. That governs the API and app rather than local inference. It does not change your obligations under the licence, which, as the SKILL.md opens with, excludes several major territories outright. Read [`character-lora-training/references/publishing-and-likeness.md`](../../character-lora-training/references/publishing-and-likeness.md) before building anything on a real likeness.

General doctrine — base-model coverage, explicit captioning, why abliterated encoders do nothing — is in [`character-lora-training/references/nsfw-training.md`](../../character-lora-training/references/nsfw-training.md).

## Still open

Everything in this file is community-sourced. Nothing here has been trained first-hand in this suite, so nothing carries first-party validation. These questions remain genuinely open as of 2026-08-29:

- **FL2VA vs Ref2VA as the training base for identity.** Nobody has published the comparison.
- **FL2VA↔Ref2VA transfer for identity LoRAs.** The Turbo LoRA transfers `[community — Organix33; re-verify]`; identity LoRAs are untested.
- **Whether a stills-trained character LoRA holds identity in motion.** The 12 GB proof run trained on stills, but no end-to-end report shows that LoRA holding up in generated video.
- **Character-audio training.** A generic audio LoRA exists; a character voice does not.
- **The fal hyperparameter numbers** come from a style-adapter run, not a character run.

This is a tracked item in `freshness.json`. When any of these closes, this file should say so.
