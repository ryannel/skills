# MiniMax H3 — LoRA training and the LoRA ecosystem

> **Shared craft lives in [`character-lora-training`](../../character-lora-training/)** — dataset coverage, caption-the-residual, evaluation, adult/NSFW base selection, and the real-person likeness rules that decide whether a LoRA is publishable. This file covers what is specific to this model.


**Short version: training doctrine for H3 is forming, and most of it converges.** The model was released 2 August 2026. The trainers all landed in the second half of that month, and this file records what the community had converged on by 2026-08-29, plus what one lab measured by 2026-09-09. That lab ran two ladders: seventeen one-variable runs on one identity (Amy) and one confirming run on a second (Ciara). Its findings are marked `[live-use — media lab, <run>, <date>]`. They are first-hand. They are also one lab, one or two identities, and often n=1. Keep them distinct from the community consensus they sit beside. Check `freshness.json` and re-verify the marked numbers before a long training run.

---

## What exists

**Speed / Turbo LoRAs were the first artefacts to mature, and they are real and usable.** The original is by **larryvrh**, and **drbaph** publishes ComfyUI-compatible conversions of it (`drbaph/MiniMax-H3-Turbo-Lora-ComfyUI`). The recipe, the settings and the audio caveat are in SKILL.md and [`setup-and-workflows.md §9`](setup-and-workflows.md). In short: 6–8 steps, the `beta` scheduler, strength 1.0, and, since ComfyUI v0.31.0, the `audio_shift` input on the core `ModelSamplingMiniMaxH3` node instead of a third-party sampler.

**As of 2026-08-22 there is an official one.** `lightx2v/Minimax-h3-Turbo` publishes `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors` (4–8 step). It is a first-party ComfyUI-format release from the team that does this for the whole open-video field, so prefer it as the default. The community conversions remain in wide use, and most posted workflows still reference them. One widely-repeated tip cuts across both: **run speed LoRAs at 0.8–0.85 rather than 1.0**. This contradicts the LoRA authors' own recipe and is `[contested]`. The lightx2v repo has since refined it. Their Turbo-SLA discussion reports that the Ref2VA-distilled 4-step Turbo LoRA, run at **~0.1 strength with 8-step inference**, gives the best facial consistency — even on FL2VA `[community — lightx2v Turbo-SLA discussion #3; re-verify]`. If your problem is identity drift under a speed LoRA, try that recipe before abandoning acceleration. A second first-party option also exists now: Alibaba PAI's **PDD Acc LoRA** (2026-08-26) is an 8-step accelerator, rank 64, 1.4 GB, run at strength 1.0 `[community — Alibaba PAI release; re-verify]`. FastVideo's **FastH3** 4-step LoRA needs a community converter to load on ComfyUI's repacked checkpoints. Converted, it wants 6 steps and strength ≥ 1.0 rather than its advertised 4 `[community — r/StableDiffusion, two threads; re-verify]`. The wiring and the rival claims are in [`setup-and-workflows.md §9`](setup-and-workflows.md). One cost is not contested: **speed LoRAs strip micro-expression**, so evaluate a character LoRA, and render any performance-critical shot, on the stock path `[community — r/StableDiffusion, three threads; convergent]`.

**The ecosystem is no longer speed-only, and it is no longer small.** A full-pagination Civitai census on 2026-09-09 counts **86 H3 LoRAs, 29 of them character-tagged** (up from 22 and 14 on 2026-08-23) `[community — Civitai API, queried 2026-09-09]`. Civitai carries large NSFW concept LoRAs — `[MMH3] Mystic XXX` (~46.6k downloads) and `HMNSFW AIO` (~43.6k) — plus a modular anatomy-part family from the same HM line (HMPussy ~27.5k, HMPenis ~16k, HMCumshot ~15.4k, HMBreasts ~9.6k), the Ref2VA-tuned "After Midnight" family, the `Faster! Harder! Shake Harder!` motion booster (~18.5k), and character LoRAs (nagisa, Lain Iwakura, h3sully) `[community — Civitai listings; re-verify]`. `Mamad8/MaxiMin-HHH-R2V-ThisIsFine` remains in circulation as a Ref2VA detail LoRA.

**Audio is demonstrably trainable.** A female-moans-plus-body-writhing audio LoRA by moawxx has ~6.8k downloads on Civitai `[community — Civitai, moawxx; re-verify]`. That settles the question this file used to leave open: a LoRA can teach H3 sound behaviour, not just degrade it. Character-voice training, the harder version of the same idea, has still not been shown.

What the timeline tells you: the community's first priority was **making a 33B model with a 32B encoder cheap enough to run**, not teaching it new subjects. That is the usual order of events for a large release. The acceleration story matured first — see the four-layer stack in [`setup-and-workflows.md §9`](setup-and-workflows.md) — and the training story caught up in the second half of August.

**One thing the Turbo LoRA settles: weights transfer between the task checkpoints.** It was trained against **FL2VA** and is reported working on **Ref2VA** as well `[community — Organix33; re-verify]`. So the two checkpoints are close enough that a LoRA is not automatically checkpoint-locked. That is useful, and it is the opposite of what you would assume from the phrase "task-specific checkpoints." It is still worth validating on your target checkpoint rather than assuming.

**Third-party *checkpoints* exist, which is stronger evidence than LoRAs.** `RedCraft | REDMIX Hybrid A2A beta1 … Lightning 8` is a MiniMax H3 checkpoint on Civitai. At ~343k downloads, it is the most-downloaded H3 artefact anywhere. Whether it is a genuine finetune, a merge, or a repackaged quant is **not established here** `[flagged — re-verify]`. But it shows somebody is doing more than converting weights, and the hybrid FL2VA/Ref2VA builds in `setup-and-workflows.md` §5 prove that the community can do surgical tensor-level work on H3.

---

## Which trainer

All of these landed in late August 2026. Support depth varies a lot, so pick by what you are training `[community — trainer repos and docs; re-verify]`:

| Trainer | H3 support | Notes |
|---|---|---|
| **ai-toolkit** | Mainline. T2V and I2V from Aug 3, Ref2VA from ~Aug 13, an official vid2vid tutorial ~Aug 20. | Trains directly on the ComfyUI quantized weights, so no separate training download. **Has three distillation countermeasures of its own** — see "Distillation handling" below; its H3 preset enables two by default. |
| **musubi-tuner** | On `dev` as a series of merged PRs (guidance loss #1045, one-frame #1057/#1058; roadmap issue #1029) — not a single unmerged PR. The deepest support: T2VA, FL2VA, Ref2VA, plus one-frame image training. Since 2026-09-02: teacher-matching (below), one-frame Ref2VA training, control images as untimed Ref2VA references (09-07), any number of one-frame FL2VA `cond_` slots (09-08), and H3 module names in `convert_lora` (08-26) `[official — musubi-tuner dev commits, 2026-08-26 → 09-08]`. | Adds guidance-distillation protection (`--h3_guidance_loss_scale 4.0`, `--h3_guidance_loss_sigma_min 0.15`), precaches text embeds so the 32B encoder is never resident during training, enforces batch 1, supports `--blocks_to_swap 48` of 50 and `--prune_adaln`. |
| **diffusion-pipe** | T2I and T2VA only (2026-08-08). | Wants CFG-augmented training. |
| **SimpleTuner** | Dedicated quickstart with 24/32/48/80 GB presets. | Sets `flow_schedule_shift 12.0` for video and `audio_flow_schedule_shift 3.0` for audio. |
| **fal.ai** (hosted) | Four trainers, $0.015/step. | Video clips only — it rejects stills with a 422. |

Known bug: musubi's backward pass errors with CUBLAS on the pruned-INT8 base (musubi #1059) `[community — musubi-tuner #1059; re-verify]`.

---

## Distillation handling — both trainers have it, and both default differently

H3 is CFG-distilled, so training on the plain flow-matching target pulls the model out of
the amplified space it was distilled into (de-distillation drift). **Both mainline trainers
ship a countermeasure, and musubi's docs describe them as the same mechanism** — target
rewritten as `uncond + scale * (velocity - uncond)` using the model's own no-grad
unconditional prediction `[official — musubi docs/minimax_h3.md]`.

**musubi** — `--h3_guidance_loss_scale`, **default `0.0` (disabled)**, explicitly "for
parity with ai-toolkit"; field reports suggest 3–4, with 4 more reliable for longer runs.
Requires `--h3_guidance_loss_uncond_cache`. Costs ~+50% step time ungated;
`--h3_guidance_loss_sigma_min 0.15` skips the noisiest ~15% of steps for most of that back.
For **one-frame (image) training the docs call it "effectively mandatory"** — without it,
drift shows up within ~50 steps as wobbly lines and broken proportions. A ~50-step LR
warmup is also endorsed there.

**ai-toolkit** — a first-class "Distillation Handling Method" selector (`cg` / `ta` /
`both` = **default** / `none`), with the H3 preset shipping `train.do_guidance_loss: true`
+ `train.guidance_loss_target: 3.5` **and** a training adapter
(`model.assistant_lora_path: ostris/minimax_h3_training_adapter/…_v1.safetensors`) — a
live, never-merged "decompression" LoRA. Ostris has claimed the adapter beats contrastive
guidance and is faster. Traps: `do_guidance_loss` is **mutually exclusive with
`bypass_guidance_embedding`** (validation raises), and the H3 preset also excludes the
AdaLN projection from the LoRA via `network_kwargs.ignore_if_contains: ['adaln_proj']`.

**The practical warning:** ai-toolkit's YAML path does not inherit the UI preset. A
hand-written config omits all of this silently and trains at handling = `none`, which is
consistent with reports of adherence loss near the peak and of higher ranks collapsing.
If you hand-write the YAML, set these keys explicitly.

**Teacher matching — the regime beyond guidance loss.** musubi's `--h3_teacher_matching`
trains the LoRA to match a *conditioned* teacher prediction, and it is mutually exclusive with
the guidance loss. Three teacher kinds, chosen with `--h3_teacher_conditions`: `first,last`
(the default endpoint teacher), `ref`, and `subject_ref`. Each is gated by a sigma window. `--h3_teacher_condition_sigma_max` is **0.75** for the
endpoint and reference teachers but **1.0 for `subject_ref`**, because identity decisions happen
at base sigma 0.92–1.0. `--h3_teacher_condition_sigma_min` is 0.15. The loss is shaped by
`--h3_teacher_loss_dc_weight 0.3` and `--h3_teacher_loss_mag_weight 0.5`. The stills caveat
has narrowed: **`subject_ref` is now the only teacher available with `--one_frame`**
`[official — musubi-tuner docs/minimax_h3.md, commits 2026-09-02 → 09-08]`. Nobody outside the
trainer author has published a result with it yet `[flagged — re-verify]`.

## Memory traps that produce no traceback `[live-use — media lab, Amy ladder, 2026-08/09]`

Three configuration facts cost the lab several silent OOM kills before they were found:

- **`quantize: true` with no `qtype` in ai-toolkit dequantises the shipped weights and
  requantises them** through a path that peaks far above the resident model. On a RunPod
  container the cgroup cap is 60 GB regardless of what `free` reports, and the kill leaves no
  traceback. Set **`qtype: "convrot8"`** explicitly.
- **`qtype_te: nvfp4` breaks the cached-embedding path** (a Qwen3-VL RoPE device mismatch).
  Set `cache_text_embeddings: false` when the encoder is NVFP4.
- **Disable in-training samples on H3.** The sample pass, not the step count, was what killed a
  3000-step run at step 750; the same config resumed to 5000 steps with samples off.

## Flags H3 hard-rejects

Carried over from Wan/SDXL recipes, these make the musubi trainer raise rather than warn
`[official — minimax_h3_train_network.py]`: `--timestep_sampling` must be `uniform`,
`--weighting_scheme` must be `none`, `--discrete_flow_shift` must be `1.0` (H3 uses its own
`--h3_shift_video 12.0` / `--h3_shift_audio 3.0`). Batch size is hard-enforced at 1 — use
gradient accumulation.

---

## Hyperparameters that converge

Independent sources land on the same numbers, which is the best signal available short of a controlled study. None of this has been validated first-hand in this suite `[community — fal.ai examples, musubi-tuner docs, note.com writeup; re-verify]`:

- **Rank 16, alpha 16.** In fal's blind votes, rank 16 beat both 32 and 64.
- **LR 1e-4** with adamw8bit. Use 2e-4 when you need fast convergence and can tolerate the risk.
- **Step counts scale with data:** ~1000 steps for a 31-image stills run, 1500 on 53 clips, 3000+ on 176 clips in fal's published examples.
- **Timestep focus band 0.4–0.8** — the musubi docs call it the range "where content is decided." The flag is **`--h3_timestep_focus_prob`, and it defaults to `0.0`, i.e. OFF** `[official — musubi docs/minimax_h3.md]`. This is the most commonly missed convergence lever: H3 draws the base sigma uniformly and then shifts video by 12, so most steps land far above the band that decides identity (measured at base sigma 0.6–0.75). musubi reports the band converging **~2× faster at `P=0.5`**, with no extra step cost. Bounds are `--h3_timestep_focus_min` / `--h3_timestep_focus_max`; it does not compose with `--min_timestep`/`--max_timestep`.

One caveat on provenance: fal's published step counts come from a style-adapter run, not a character run, so treat them as scale hints rather than a character recipe.

### What one lab measured `[live-use — media lab, Amy h3-v1→v17 and Ciara h3-v1, 2026-08-29 → 09-09]`

Seventeen one-variable-at-a-time runs on one identity, all r16/α16, LR 1e-4, adamw8bit, batch 1, 3000 steps, single-frame stills. The consensus numbers above survived contact; three things the consensus did not say turned out to be the levers:

- **Training resolution is the likeness lever, and it plateaus at 1536.** 768 unusable → 1024 a large consistency win → 1280 clearly better → 1536 stronger still → 1792 "much the same". 1536 was roughly the dataset's native pixel size. Sources below the training resolution teach softness.
- **Rank 32 is fatal under ai-toolkit.** r32 collapsed to random content at every checkpoint on an otherwise identical run. The likely cause is that every hand-written YAML in that ladder trained with distillation handling **off** (see above). A collapse like that is the predicted symptom of de-distillation drift on a CFG-distilled base. r16 is the ceiling until someone shows r32 surviving with handling on.
- **15 curated images beat 73** on the same recipe, and 73 gave no gain over 32. Count is not the lever. The caveat is real. The winning set changed three things at once: selection against starved coverage axes, every image re-developed to ≥1536, and eight framing captions corrected. So "curate for coverage" is not yet isolated as the cause.
- **musubi's `--h3_timestep_focus_prob 0.5` was the largest single objective-side gain** in a first-hand A/B, matching the docs' ~2× claim. Contrastive guidance fixed *adherence*, not likeness. Guidance 2.0 beat 4.0 only marginally. The two levers were never combined.
- **Full-body face weakness is not fixable by render resolution** — 2.3× more face pixels still gave different people. It is a training-distribution problem, and the same framing ceiling `characters.md` reports for reference conditioning.
- **Cost and speed:** 3000 steps at 1536 ran ~2.0–2.6 s/it on a 5090 with ai-toolkit (~$1.70–2.50 a run) and ~4.8 s/it with musubi. The confirming run on the second identity took 3 h at 3.5–3.6 s/it, ~$2–5 including idle time. On the same prompts, the H3 stills LoRA landed ~1.5× further from canon than the same dataset's Krea 2 LoRA (median 0.315 vs 0.199). H3's weakness is likeness, not adherence.

**The headline result: a stills-only H3 LoRA carries identity into motion.** On the second identity, pure T2V at thigh-up scored a 0.200 median face-embed distance (worst frame 0.259) against **0.920 for the no-LoRA control** — a different person. With a pinned keyframe, the LoRA's production value is drift insurance. The face held **flat across 5 s (0.167→0.172)** where the base drifted 0.161→0.263. Full body fell off on both. That is the framing ceiling, not the LoRA. That closes the question this file used to leave open, for stills-trained character LoRAs at thigh-up framing `[live-use — media lab, Ciara h3-v1, 2026-09]`.

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
- **Close and tight beats wide for identity.** The one published comparison found 31 close-up face images beat 32 full-body images `[community — note.com writeup; re-verify]`. One data point, but it matches the suite's general dataset doctrine — and one lab's 15-beat-73 result above says the same thing from the other side: shape and coverage, not count `[live-use — media lab, Amy h3-v14/v16, 2026-08/09]`. Note that the note.com run trained at 512², which the lab's resolution ladder says is below the usable floor, so its absolute numbers do not transfer.
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

The community half of this file is unvalidated here; the `[live-use]` half is one lab's runs. These questions remain genuinely open as of 2026-09-09:

- **FL2VA vs Ref2VA as the training base for identity.** Nobody has published the comparison; the lab trained FL2VA throughout.
- **FL2VA↔Ref2VA transfer for identity LoRAs.** The Turbo LoRA transfers `[community — Organix33; re-verify]`; identity LoRAs are untested.
- ~~Whether a stills-trained character LoRA holds identity in motion.~~ **Answered, for thigh-up framing** — see "What one lab measured" `[live-use — media lab, Ciara h3-v1, 2026-09]`. Still open: whether **clips** add what stills cannot — motion-time face stability without a keyframe, and full-body identity. A face-gated clip arm (10–12 clips, thigh-up, 3 s at 73 frames) is planned and unrun, with a caveat that 768p clips mixed into a 1536p stills set may pull face detail down.
- **What in the 15-image set produced the win** — selection, re-develop or caption audit — has not been isolated.
- **Character-audio training.** A generic audio LoRA exists; a character voice does not.
- **The fal hyperparameter numbers** come from a style-adapter run, not a character run.
- **Teacher matching** has one author's recipe and no independent result.

This is a tracked item in `freshness.json`. When any of these closes, this file should say so.
