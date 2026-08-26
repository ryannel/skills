# LTX-2.5 — LoRA and IC-LoRA training

This file covers **making** an adapter with `ltx-trainer`. *Loading and stacking* one is covered in [`setup-and-workflows.md §6`](setup-and-workflows.md#6-using-loras-and-ic-loras). What transfers across every model in the suite — dataset architecture, captioning doctrine, evaluation — lives in [`character-lora-training`](../../character-lora-training/). This file carries only what is specific to LTX.

## Contents

1. [Before you train: can you publish it?](#1-before-you-train-can-you-publish-it)
2. [The trainer, and its one strategy](#2-the-trainer-and-its-one-strategy)
3. [Training modes](#3-training-modes)
4. [Datasets and clip length](#4-datasets-and-clip-length)
5. [Validation defaults, and what they tell you](#5-validation-defaults-and-what-they-tell-you)
6. [IC-LoRA training](#6-ic-lora-training)
7. [Which version to train against](#7-which-version-to-train-against)
8. [What is not known](#8-what-is-not-known)

---

## 1. Before you train: can you publish it?

This section leads because it is the most surprising thing about LoRA work on LTX, and because finding out afterwards is expensive.

**Your LoRA is a Derivative under the licence.** §1.5 defines "Derivatives of LTX-2.x" to include "any fine-tuned or adapted weights, parameters, or checkpoints derived from LTX-2.x," and §3.5 names "any fine-tuned weights, **LoRA adapters**, or similar adaptations" explicitly. That has three consequences:

1. **It must ship under the same agreement.** §3.2: any Derivative "must be distributed **exclusively under the terms of this Agreement** … with a complete copy of this Agreement included." You cannot relicense it MIT, CC0 or Apache. A Civitai upload with a permissive licence field is not something the agreement allows.
2. **The $10M obligation travels to whoever receives it.** §3.5: "If the transferee is a Commercial Entity … it must obtain a paid license from Licensor prior to any use of any Derivative of LTX-2.x, **regardless of who created such Derivative**." You must notify recipients in writing, and you may not transfer the Derivative to a Commercial Entity that has not already obtained that licence. In practice this makes an open public download hard to square with the clause, since you cannot vet who downloads it.
3. **The content restrictions follow the adapter.** The incorporated Acceptable Use Policy's ban on sexually explicit generation is universal and reaches on-premises use, so an adult LoRA is outside the licence whether or not you publish it. The community's adult work happens on **LTX 2.3** `[community — BarelyAI]`, but both candidate 2.3 licence texts incorporate the same AUP — that is practice, not permission. If NSFW training is the job, [`wan-2-2`](../../wan-2-2/) is Apache 2.0 with no acceptable-use clause. The publishing gates that still apply there (real-person bans, the TAKE IT DOWN Act) are covered in [`character-lora-training`](../../character-lora-training/).

Full clause treatment: [`licence-and-derivatives.md`](licence-and-derivatives.md).

---

## 2. The trainer, and its one strategy

`ltx-trainer` is first-party. It ships in the `Lightricks/LTX-2` monorepo alongside `ltx-core` and `ltx-pipelines`, and covers **LoRA, IC-LoRA and full fine-tune**. Lightricks also ship **their own agent skill for it** at `.claude/skills/train-model/` inside that repo — SKILL.md plus phase files and references for hardware profiles, mode selection, config patching and troubleshooting. Read it before writing a config. It is the vendor's own distillation of the workflow, and it moves with the code.

The design point worth remembering: **there is one unified "flexible" training strategy, and every mode is a config rather than a code path.** You express the mode by setting `is_generated` per modality and adding optional conditions. Two rules constrain it: "At least one modality must have `is_generated: true`," and "Audio does **not** support `first_frame` or `spatial_crop` conditions — only `prefix`, `suffix`, `mask`, and `reference`." `[official — docs.ltx.io training-modes]`

---

## 3. Training modes

| Mode | Video | Audio | Conditions |
|---|---|---|---|
| T2V | generated | generated | — |
| I2V | generated | generated | `first_frame`, with a `probability` (0.5 in the sample config) |
| Video extension | generated | generated | `prefix` / `suffix` — note `temporal_boundary` counts **latent** frames, ×8 for pixel frames |
| V2V IC-LoRA | generated | — | `reference` |
| A2V | generated | **frozen** | — |
| V2A (foley) | **frozen** | generated | — |
| Video in/outpainting | generated | generated | `mask` / `spatial_crop` |
| T2A, audio extend/inpaint, A2A and AV2AV IC-LoRA | — | generated | various |

Two things fall out here that have no analogue in the image skills. **You can train the audio branch alone.** The V2A row freezes video entirely, and a released community adapter already does this (`LTX-2.3 Whisper / Soft-Spoken Audio LoRA`, plz12345) `[community — Civitai]`. And **the `probability` on `first_frame` is a real knob**: at 0.5, half the training samples see a conditioning frame and half do not. That is what produces an adapter usable in both T2V and I2V, rather than one that only works when a frame is attached.

---

## 4. Datasets and clip length

The lattice rules from SKILL.md apply to training data as well as inference: clips want `8k+1` frames and dimensions that are multiples of 32. The trainer's own validation runs at **89 frames** (`8×11+1`), which is a reasonable default clip length to build a dataset around.

Three LTX-specific dataset decisions:

- **Video clips versus stills.** Training on video is the only way to teach *motion*, and it costs far more VRAM and time per sample than an image dataset. Where the target is **appearance** — a face, a style, a costume — single-frame training is much cheaper, and is the right default. That is the same trade [`wan-2-2`](../../wan-2-2/) documents, and the reasoning transfers.
- **Silent clips are a problem in the dataset too.** The model encodes audio and video jointly, so a dataset of muted footage teaches the audio branch that this content is silent. Either add a silence track deliberately, and accept that you are training silence, or use the V2A/frozen-video framing so the audio branch is not being supervised at all.
- **Caption in the model's own register.** The encoder is a Gemma 4 decoder-LM, so captions should read like the prompts in [`prompting-guide.md`](prompting-guide.md) — flowing present-tense prose, physical cues rather than labels. Tag-style captions train a dialect that will not match the inference prompt.

---

## 5. Validation defaults, and what they tell you

From CHANGELOG 1.2.0, the trainer's validation defaults are **960×544 × 89 frames, 24 fps, 30 inference steps, STG block 28**, plus "a substantially expanded negative prompt" and separate video/audio CFG and STG controls. `[official — CHANGELOG]`

Two things worth taking from that:

**Validation runs at 30 steps, not 8.** The distilled 8+3 schedule is an inference convenience. The trainer evaluates on a full schedule with guidance live. If your adapter looks right in validation and wrong in the distilled ComfyUI graph, the schedule is a likely cause before the adapter is.

**Guidance is now per-modality.** `video_cfg_scale`/`audio_cfg_scale` and `video_stg_scale`/`audio_stg_scale` replaced the old flat `guidance_scale`/`stg_scale`/`stg_mode`, which are auto-migrated. STG — Spatio-Temporal Guidance via block perturbation — is a real lever here in a way it is not on the distilled inference path, and block 28 is the trainer's chosen perturbation site.

**No public hyperparameter recipe exists.** Rank, alpha, learning rate and step count for a character or style LoRA on 2.5 are not published by Lightricks, and none were found in a named, reproducible community write-up during this pass. Start from the sample config in the repo rather than from another model's numbers. Treat anything you find on an aggregator claiming LTX-specific rank/LR values as unattributed until you can trace it (§8 flags this and the three training unknowns beside it).

---

## 6. IC-LoRA training

An IC-LoRA is trained on **paired** data — the video plus the control signal that should drive it. That pairing is what separates it from a style LoRA trained on video alone. In trainer terms this is the `reference` condition with video generated and audio absent.

The practical difficulty is the pairing, not the training. For Union Control-style adapters you need depth, canny or pose extracted from the same footage. For an Ingredients-style adapter you need reference sheets that correspond to the clips. Lightricks' released adapters are the model to study: the Ingredients prompt format is a two-part string, `Reference sheet: <panels> / Generated video: <action>`, and an adapter trained on a different pairing convention will not respond to that prompt shape.

Before training one, check whether the released set already covers it. Union Control, Motion Track, Ingredients, Pixel Spatial Upscaler, In-Outpainting, Clean Plate, Deblur, Decompression, Colorization, Day-To-Night and several others already exist first-party, and all but one are 2.3-trained yet load on 2.5 in Lightricks' own workflows.

---

## 7. Which version to train against

**The trainer works with 2.5** — confirmed by the vendor's own account: *"the existing LTX Trainer works with LTX-2.5"* `[official — Lightricks staff, r/StableDiffusion]`. But the ecosystem is not there yet: **168 of ~171 community LoRAs on Civitai are 2.3** `[community — Civitai API 2026-08-22]`, and Lightricks' 2.5 workflows load 2.3 adapters. So a 2.3-trained adapter has a larger audience and is likely to work in both places.

The open question is whether 2.5's post-training changes how training behaves. It was asked publicly and left unanswered by the vendor: *"does it change how lora training behaves? i had decent luck with small curated sets on 2.3 at the usual step counts, wondering if the new base pushes back more."* `[community — Yeti-Bhanot]` Until someone publishes a comparison, treat 2.3 step counts as a starting point, not a transfer.

For **domain fine-tuning** rather than an adapter — robotics, action-conditioned world prediction, synthetic AV or drone data, industrial digital twins — the intended base is `Lightricks/LTX-2.5-Pre-Trained`, the raw non-SFT checkpoint, not the distilled or dev release.

---

## 8. What is not known

Four things are unknown, all specific to training rather than to the model generally. **Hyperparameters:** no published rank/alpha/LR/step recipe for a character or style LoRA on 2.5. **Whether 2.5's post-training changes training behaviour** relative to 2.3: asked publicly, still unanswered. **VRAM cost of training** at the validation resolution: the repo publishes no absolute figures for inference, and none for training either. **Whether a 2.5-trained plain LoRA loads on 2.3:** the IC-LoRA evidence runs the other direction only. All four resolve together, on the first named 2.5 training write-up with numbers in it. `[flagged — re-verify]`

Evaluation, overfit detection, dataset balance and the publishing gates that apply regardless of model: [`character-lora-training`](../../character-lora-training/).
