# Authoring a temporal (video) model skill

Read this alongside `SKILL.md` when the model produces **video** — text-to-video, image-to-video, video-to-video, or video editing. It covers the video spine, the conditioning-class doctrine, the anatomy sections image skills have no equivalent for, and the temporal mechanics of the three pillars.

> **Status of this file.** Proven once, by `wan-2-2` (2026-08-13), and corrected from that run — the notes below marked *"from the Wan 2.2 run"* are the specific things this file got wrong or missed the first time. One data point is not a pattern; the second video skill should correct it again.

## Ground truth to pattern-match against

Read **`skills/generative-media/wan-2-2/SKILL.md`** in full — it is the only finished video skill, and it is the spec in the way the image skills are for their side.

For voice, section rhythm and the closing two-bar section, also read `skills/generative-media/z-image/SKILL.md` — the fullest example in the suite. Read `krea-2` if your model has a contested training doctrine or a default look people fight; that's the closest analogue to the judgement calls video models demand.

Then read the **official ComfyUI video templates** for your model as the factual spine — and read the **template JSON itself**, not the docs page. *From the Wan 2.2 run:* the official docs pages for Wan 2.2 omit every numeric setting — steps, CFG, shift, the expert split — and only the JSON in `Comfy-Org/workflow_templates` carries them. Pull the template list from the git tree API (the contents API caps at 1000 entries and `video_*` sorts past the cut), then read `widgets_values` directly.

## The spine: a task-mode selector

Image skills organise by variant or surface. Video skills usually organise by **task mode**, because it changes what the reader does more than anything else does:

| Mode | What it is | Why it matters |
|---|---|---|
| **T2V** | text → clip | Often the *weaker* path in practice — no spatial anchor |
| **I2V** | still → clip | The production workhorse. Where most real work happens |
| **FLF2V** | first + last frame → clip | Controlled transitions; the reliable way to hit a target state |
| **V2V** | clip → restyled/edited clip | Pose/depth-driven retargeting, restyling |
| **Extend** | clip → longer clip | Where error accumulation lives (see failure modes) |
| **Audio-driven** | audio + still → lip-synced clip | *From the Wan 2.2 run:* a mode I did not anticipate. Clip length follows the audio |
| **Performance transfer** | driving video → same motion, different subject | Character animation and replacement. Different from a character LoRA: transfers *what they do*, not *who they are* |

Say plainly which modes the model actually supports and which are strong versus nominal. "Supports T2V" and "T2V is worth using" are different claims — image skills rarely have to make that distinction; video skills always do.

*From the Wan 2.2 run:* **check whether each mode is a separate download rather than a mode of one checkpoint.** Wan's audio-driven, performance-transfer and control variants are all distinct model files with their own architectures — one of them is dense where the flagship is MoE. A selector table that implies they are settings on one model will send readers looking for a node that doesn't exist.

**The variant axis usually coexists**, and can cut across task mode rather than nesting under it. Wan 2.2 ships a 5B hybrid that does both T2V and I2V, plus separate 14B T2V and 14B I2V models — so size and task mode are tangled, not hierarchical.

When the two axes genuinely tangle like that, **lead with task mode and express size as a column within it**, rather than drawing a tidy hierarchy in either direction. The reason is what the reader arrives knowing: they know they want to animate a still, not that they want a 14B model. Size is a constraint they resolve *after* the task — usually against their VRAM — so it belongs in a column, not at the top level. Draw the table that reflects the actual product; where a cell is a hybrid serving two modes, say so in the cell rather than duplicating the row.

## Conditioning-class doctrine — four axes for video

Video inherits the still-image doctrine's two axes and adds two of its own. Numbering is continuous with `image-models.md` so the two files agree: **axes 1–2 are defined there, axes 3–4 here.** Derive all four, then verify.

**Axes 1 and 2 — text-encoder class, and guidance state** — these transfer unchanged, so **read the "conditioning-class doctrine" section of `image-models.md` as well as this file**; it is the one part of the image reference a video author genuinely needs. It carries both tables: encoder class (prompt dialect, trigger words, caption style) and, separately, guidance distillation (whether negatives work at all). Keep those two apart here for exactly the reason it gives — video models ship distilled speed variants too, and a distilled variant's negatives go inert regardless of which encoder it uses. Wan uses umT5; others use LLM or CLIP-class encoders.

**3. Image-conditioning path** — how a still drives a clip. Latent injection (the still is encoded into the initial latent) behaves differently from a reference adapter (the still conditions attention throughout). This determines how tightly the first frame is honoured, whether the conditioning decays over the clip, and whether an image LoRA has any effect on an I2V run.

**4. Temporal architecture** — and this is the axis with no image analogue. A single DiT behaves one way; a **mixture-of-experts split across the denoising schedule** behaves very differently. Wan 2.2's 14B is the live example: a **high-noise expert** handling early denoising (scene layout, motion, structure) and a **low-noise expert** handling late denoising (texture, detail, temporal coherence) — 14B active out of 27B total, loaded through **two separate `Load Diffusion Model` nodes**.

The consequence propagates everywhere, and is the single most important thing to get right for such a model:

- **LoRA training doubles.** You train on both experts from the same dataset and load **two LoRAs**, one per expert — high-noise LoRA into the first `LoraLoaderModelOnly`, low-noise into the second, each feeding its own `ModelSamplingSD3` → `KSamplerAdvanced` chain.
- **Sampling is split across two samplers**, so "steps" and "CFG" are per-expert questions, not single numbers. State them per expert.
- A reader who assumes one model, one LoRA, one sampler will produce something that half-works and looks subtly wrong — the worst kind of failure, because it doesn't error.
- *From the Wan 2.2 run:* **the handoff between the two samplers has its own wiring trap.** The first must pass an *unfinished* latent (`return_with_leftover_noise: enable`) and the second must not re-noise it (`add_noise: disable`); get either wrong and output is silently degraded rather than broken. Also, `steps` on both nodes is the **total schedule length**, not a per-sampler count — the split is expressed through `start_at_step`/`end_at_step`. Both are worth stating explicitly; neither is inferable from the node names.

Whatever the architecture, state it **with its mechanism**, the same way the image skills state the encoder class.

## The one rule that changes everything

SKILL.md calls this the highest-leverage section, and it must be **discovered for your model**, never inherited. What follows is not the answer — it is the three shapes a video model's one-rule tends to take, so you know what kind of thing you are looking for. Test all three against your model and keep whichever actually dominates output quality:

- **"Describe the action, not the scene."** The most common shape, because it is the axis stills don't have: a prompt written like an image prompt describes a static tableau, and a model handed a tableau produces a near-static clip. If your model's failure mode under image-style prompting is stalled motion, this is likely its rule.
- **"The still does the heavy lifting."** For I2V-dominant models: composition, identity, style and lighting all come from the conditioning image, and the prompt's only real job is motion and camera. Readers coming from image models routinely over-write the prompt and fight their own reference. If prompt content demonstrably loses to the still, this is the rule.
- **"It is two models, not one."** Where the architecture splits experts across the schedule (see the temporal-architecture axis above), nearly every downstream instruction changes — settings, LoRA count, wiring. If a reader who assumes one model gets something that half-works, that assumption *is* the highest-leverage thing to correct.

The rule can also be a control-surface rule rather than a prompting rule — `krea-2` is the precedent on the image side. Don't force it into prompt shape.

## Signature-quality technique

The image analogue is the realism question: every model has a default look and a lever that overrides it. For video there are **two** defaults to characterise, and the second is the one authors forget:

- **Per-frame aesthetic** — the same question the image skills ask (plastic skin, over-saturation, the model's house look), answered per frame.
- **Default motion character** — and this has no image analogue at all. Models have a recognisable motion signature: over-smoothed slow-motion drift, jitter, unearned dramatic camera push-in, or subjects that gesture constantly regardless of prompt. Name this model's, then find the lever that overrides it — prompt phrasing, fps and frame count, a motion or camera LoRA, or a scheduler/shift change.

State both. A skill that nails per-frame realism and ignores a slow-motion default has solved the easier half of the problem.

## Per-mode settings

Anatomy item 12, and the video version is **per task mode**, not just per variant — I2V, T2V and FLF2V genuinely differ in steps, CFG, shift and negative-prompt usage on the same weights, so one settings block presented as "the model's" is wrong for at least two of its modes. Give a block per mode the model actually supports well, each covering steps, CFG/guidance, sampler, scheduler, shift, resolution, frame count and fps, negatives, and seed behaviour.

Two video-specific complications to handle explicitly:

- **Where the schedule splits experts, every number becomes per-expert** (see axis 4). A block that gives one step count for a two-expert model is under-specified; state the split point too.
- **Distilled speed variants change the numbers and the negatives together** — the same trap as the image side, arriving via axis 2. Keep distilled and undistilled blocks apart. *From the Wan 2.2 run:* they can also change settings you would not expect a speed path to touch — Wan's official templates use a **different sigma-shift** on the 4-step LoRA path than on the full-step path. Diff the whole template, not just steps and CFG.
- **A dense sibling is a different model, not a smaller one.** *From the Wan 2.2 run:* Wan's 5B sits beside the 14B MoE with its own VAE, its own fps, its own frame count and a different sampler. Presenting it as "the low-VRAM option" hides four settings changes. Give it its own block.

## Anatomy sections image skills don't have

Add these to the shared skeleton in `SKILL.md`:

**Length × fps × resolution budget.** Image skills carry one resolution line. Video has a three-way budget that dominates every other decision, and it must be a table with real numbers. Frame count, native fps, clip duration, the VRAM-versus-duration curve, and the offload/block-swap thresholds that make longer clips possible on smaller cards. Give the model's *native* fps explicitly — generating at one fps and playing at another is a common and confusing error. Wan 2.2's I2V default of **81 frames ≈ 5s at 16 fps** is the kind of anchor number to lead with.

**Motion and camera control** (`references/motion-and-camera.md`) — the video analogue of ControlNet, and usually the difference between a demo and a usable shot:
- **VACE** — reference/pose-driven conditioning; on Wan it is the no-training path to consistent character posing and runs from ~8 GB VRAM. Note the strength convention if the workflow has one (in common Wan graphs, VACE strength 0 for T2V and 1 for I2V).
- Camera-trajectory LoRAs, depth/pose video conditioning, and model-family control suites (Wan Fun and similar).
- What is *not* controllable — say so plainly.

**Audio.** *From the Wan 2.2 run: this axis has three states, not two.* A model may **generate** audio (LTX-2 does video and synced audio in one pass), **consume** it (Wan's S2V takes an audio track and lip-syncs to it, generating none), or neither. "Does it do audio?" is ambiguous across that distinction and the answer readers need is which direction it runs. Where the model generates none, say what to reach for instead. Image skills have no analogue for this axis at all.

**Post chain** — interpolation and video restore/upscale. This is a distinct ladder from the image refine → detail → tile ladder, and it has a **load-bearing ordering rule**:

> **Restore/upscale before you interpolate.** Interpolating first doubles the restorer's workload and locks interpolation smear into the frames it then has to sharpen.

Populate with the current tooling and its status — temporal restorers (SeedVR2, and the newer FlashVSR), RIFE for interpolation, and the downscale-first restore trick. Flag this section as fast-moving: the video upscaler landscape churns faster than almost anything else in the ecosystem, and `image-production-workflows` already tracks its image counterpart as its most volatile watchlist item.

## The three pillars — temporal mechanics

**Characters** (`references/characters.md`) — the pillar changes most. Identity must hold across **frames** *and* across **shots**, which are different problems:
- *No-training path* — VACE-style reference conditioning. Fastest route to a consistent character, and the right default to lead with.
- *I2V from a locked still* — generate or lock the character as a still first, then drive I2V from it. **This is the cross-modality handoff and the reason the image and video skills belong in one suite**: link the relevant image skill (`z-image`, `flux-2`, `sdxl`, `krea-2`) for the still-locking stage rather than re-teaching character LoRAs here.
- *Character LoRA on the video model* — most expensive, most controllable; note the two-expert consequence above if it applies.
- *Cross-shot continuity* — holding a character across separate clips is a harder problem than holding them within one. Say what actually works and what doesn't.

**LoRA training** (`references/lora-training.md`) — `kohya-ss/musubi-tuner` is the video default (same author as sd-scripts, so the sd-scripts discussion culture carries over as a craft source), with `tdrussell/diffusion-pipe` for per-model timestep/shift facts. Cover: video-clip datasets versus image datasets, clip length and frame-sampling choices, VRAM cost versus image LoRA training, the **two-expert question** where it applies, and **single-frame training** as the substantially cheaper route when the target is appearance rather than motion. Give hyperparameters as attributed starting points and flag contested ones — video LoRA doctrine is younger and softer than image LoRA doctrine, so expect more contested cells, and show them as contested.

**Production pipelines** — the video ladder, which runs:

> locked still (image suite) → I2V → **restore/upscale** → **interpolate** → audio/finish

State per-stage settings and which stages are optional, the same way `z-image` does for images. Cover segment-stitching for longer pieces, and the cross-modality handoff in both directions. Once a second video skill exists, expect this to move into a `video-production-workflows` sibling — the same reasoning that produced `image-production-workflows` rather than duplicating ~200 lines four times.

## Temporal failure modes

Video adds a whole artefact class image models cannot produce. Populate a `symptom → cause → fix` table for your model covering at least the following. **The mechanisms below are hypotheses to verify against your model, not established fact** — confirm each against community reports before stating it, and mark what you couldn't confirm:

| Symptom | Mechanism to check | Usual direction of fix |
|---|---|---|
| Flicker / shimmer on detail | Per-frame detail regenerated without temporal coherence — often introduced by a per-frame (image) upscaler used on video | Use a temporal-aware restorer, not a per-frame one |
| Identity morph across the clip | Conditioning signal decaying as the clip progresses; no persistent identity anchor past the opening frames | Shorter clips, reference conditioning, or a character LoRA |
| Stalled or slow-motion output | Three distinct causes, worth separating: prompt describes a *state* rather than an *action*; a distilled speed LoRA suppressing dynamism; or an fps mismatch where correct frames are simply played back at the wrong rate | Describe motion explicitly; split LoRA strength and restore guidance where motion is decided; check the output container's fps before debugging anything else |
| Last-frame collapse in extended clips | Error accumulation — each extension conditions on an already-degraded final frame | Re-anchor on a clean keyframe; use first-last-frame conditioning |
| Colour pumping across segments | The same accumulation on the colour channel, compounded by per-segment VAE round-trips | Re-anchor; colour-match segments |
| Visible seams at segment joins | Independently generated segments stitched with a motion discontinuity at the join | Overlap frames, or FLF-condition each segment on its neighbour |

## Pre-flight additions

On top of the shared checklist in `SKILL.md`:

1. Task-mode selector present, with **strong versus merely-supported** modes distinguished honestly, and size expressed as a column rather than a competing top-level axis?
2. One-rule discovered for this model — tested against all three candidate shapes and not inherited from this file?
3. Both defaults characterised — per-frame aesthetic *and* default motion character — each with its override lever?
4. Length × fps × resolution budget table populated with real numbers, including native fps and VRAM-versus-duration?
5. Conditioning axes derived and stated with mechanism — encoder **and guidance state** (read from `image-models.md`), image-conditioning path, temporal architecture?
6. If the architecture splits experts across the schedule: two-LoRA training, per-expert sampler settings, and the wiring **all** stated explicitly?
7. Motion/camera control covered, including what is *not* controllable?
8. Audio axis addressed — even if the answer is "this model has none, reach for X"?
9. Post chain stated with the **restore-before-interpolate** ordering rule and its mechanism?
10. Cross-modality handoff linked in both directions — the image skill that locks the still, and back again?
11. Temporal failure modes populated and each mechanism **verified rather than inherited from this file**?
12. Registered in `freshness.json` — judge the tier as SKILL.md Step 5 says, but expect **`hot`** to be right for most video models today, since these ecosystems currently churn faster than the image ones. Drop to `active` if the model is a stable point release with a quiet ecosystem.
