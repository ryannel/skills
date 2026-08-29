---
name: scail-2
description: >
  Authoritative guide for SCAIL-2, the open-weights character-animation and character-replacement video model
  from zai-org (Z.ai / Zhipu AI — not Alibaba). It is built on the Wan 2.1 foundation and was released with the
  paper arXiv 2606.10804. Use this whenever the user touches SCAIL-2 in any way, even obliquely: replacing a
  person in existing footage while following their motion exactly, transferring a performance from a driving
  video onto a reference character, choosing between Animation mode and Replacement mode (and between
  end-to-end-driven and pose-driven animation), installing it in ComfyUI (the `WanSCAILToVideo` node,
  `SCAIL2ColoredMask`, SAM3 tracking, the umT5-XXL encoder and Wan 2.1 VAE, GGUF and fp8 quants, VRAM on 8–16
  GB cards), preparing inputs (the reference image, the two coloured masks, the `replacement_mode` pairing, and
  the first-frame edit that decides whether the whole job works), writing or fixing the prompt (and learning
  why it barely matters here) along with the upstream image-edit prompt that does matter, picking
  steps/CFG/shift/solver, running the LightX2V distilled speed path, loading the vendor's Relighting /
  Bias-Aware DPO / LightX2V LoRAs, asking whether you can train a SCAIL-2 LoRA at all (you cannot — the
  skill says so and routes you), generating clips longer than 81 frames with context windows or chained
  segments, holding identity and clothing steady across a shot, handling multi-person scenes and multiple
  reference images, understanding the split licence (Apache 2.0 code, MIT weights card), or debugging a named
  artefact: mushed faces on small subjects, a tracker that refuses to lock, clothes morphing past five
  seconds, backgrounds changing in replacement mode, an inserted character that is too bright for the plate,
  or Animation mode silently collapsing into Replacement behaviour. Also covers when to reach for something
  else: Wan Animate, MiniMax H3's video-editing mode, or Bernini-R. Use this for any question about SCAIL-2 in
  any context. Choosing between models, comparing them, or working out which skills and install commands a job
  needs is [`generative-media-atlas`](../generative-media-atlas/)'s job — start there when the model is not
  already settled.
---

# SCAIL-2

SCAIL-2 is an open-weights **character animation and character replacement** video model from **zai-org**, which is **Z.ai / Zhipu AI, the lab behind GLM and CogVideoX.** It is **not an Alibaba release and not a Wan-team model**, even though its node names contain `Wan` and community workflows label it "Wan SCAIL-2". It runs on **umT5-XXL** and the **Wan 2.1 VAE**, optionally alongside Wan's I2V CLIP vision tower. It carries a **split licence: Apache 2.0 for the code, MIT on the weights card**. The paper is arXiv 2606.10804, *"Unifying Controlled Character Animation with End-to-End In-Context Conditioning"* (Yan, Guo, Yang, Tang). Its v1 is dated 9 June 2026 and its latest revision is **v3, 5 August 2026**. It succeeds zai-org's own SCAIL-1. No source glosses "SCAIL" as an acronym, so treat it as a name.

**The defining trait:** SCAIL-2 is conditioned by a **driving video plus a reference image plus explicit masks**. It **tracks** the driving motion frame by frame instead of re-imagining it. That is why it beat Wan Animate into the default slot for character replacement, and why [`minimax-h3`](../minimax-h3/)'s video-editing mode can only approximate it. Almost every other property follows from this: your output fps matches your *input's* fps, your clip length matches your *input's* length, and the prompt barely matters.

> **A `../link/` on this page that doesn't resolve is a skill you have not installed, not a broken
> page.** [`generative-media-atlas`](../generative-media-atlas/) is the map of this suite: which
> model fits a job, which skills that job needs, and the commands to install them. It works on its
> own, so it is the one to add first: `npx skills add ryannel/skills --skill generative-media-atlas`

---

## Its relationship to Wan 2.1 runs at three levels

Keeping the three levels apart tells you whether your Wan LoRAs will load:

- **Weights.** SCAIL-2 is a **full fine-tune of the `Wan2.1-14B-I2V` checkpoint**. The paper says so outright: the model is *"adapted from the Wan2.1-14B-I2V backbone"*. The authors *"fully fine-tune … for 3,500 steps with a batch size of 128 and a learning rate of 10⁻⁵"* `[official — arXiv 2606.10804v3 §4.1]`. A DPO stage follows, which freezes the backbone and trains rank-128 LoRA adapters. The model inherits Wan 2.1's motion prior wholesale.
- **Architecture.** It uses Wan 2.1's DiT, but **modified**: an additive mask stream stacks **`4(K+1)` extra in-context conditioning channels** onto the patch embedding, which is **28** channels at the shipped K=6. It also adds **Mode-Specific RoPE**. It is not an unmodified Wan 2.1.
- **Code.** The codebase descends from the Wan 2.1 repo. When the README says *"the overall project architecture is inherited from SCAIL"*, it means the **codebase**, not the network. The same lab's SCAIL-1 README uses that phrase for SAT, which is a training framework `[official — wan-scail2 README, Acknowledgements]`.

ComfyUI backs up the base independently: it labels the model `WAN21_SCAIL2` with `image_model: "wan2.1"` `[official — PR #14373 diff]`. The base is Wan **2.1**, not 2.2, and **no primary source names a 480P or 720P base variant**. The `480p` label on community workflows comes from the official speed LoRA's filename, `lightx2v_I2V_14B_480p_…`, and that filename names *Wan 2.1's* I2V variant. It is what a workflow loads, not what SCAIL-2 trained from.

---

## Task-mode selector

One checkpoint gives you four operating shapes. **In-Context Mask Conditioning** and **Mode-Specific RoPE** unify them inside the weights, so there are no separate heads or downloads. All four modes, their inputs, and the vendor's recommendation among them are vendor-defined `[official — arXiv 2606.10804v3, wan-scail2 README, PR #14373 diff]`. You do not download a mode. Instead, you set a `replacement_mode` boolean and match your driving mask's background colour to it, on two nodes at once. That pairing is the model's single largest footgun. See below.

| Mode | Inputs | Use when… |
|---|---|---|
| **Animation — end-to-end driven** | Reference image + coloured reference mask + driving video + coloured driving mask on a **black** background; `replacement_mode: False` | **The recommended default.** Your character performs the driving clip's motion, from the raw driving frames |
| **Animation — pose-driven** | As above, with an SMPL pose render replacing the raw driving frames | Vendor: *"performs better under 704p"*. Use it when the source performer's appearance bleeds through |
| **Replacement** | As above, but the driving mask has a **white** background and `replacement_mode: True` | You keep the original footage — camera, framing, lighting, everything outside the masked person — and swap only the tracked person. The "Wan Animate replacement" job |
| **Multi-reference** | **One composited reference image** carrying every character, plus one coloured mask giving each an identity colour | More than one character, or front-and-back views of one. The node is explicit: *"for multiple references composite all on single image"*. **Vendor-marked unoptimised**: *"video qualities may degrade even though additional information do get referenced"* |

**There is no text-to-video mode and no image-to-video mode.** SCAIL-2 cannot originate motion. If you have no footage, you must manufacture some (Mixamo, a SnapMoGen mocap export, or a clip from [`wan-2-2`](../wan-2-2/) or [`ltx-2-5`](../ltx-2-5/)) and drive SCAIL-2 with it. See [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §4.

---

## The one rule that changes everything

**Edit the driving video's actual first frame into your new character, and feed *that* as the reference image. Do not feed a portrait or a character sheet.**

This is a **preparation** rule. It happens outside SCAIL-2, and it appears in none of the zai-org sources read here: not the branch READMEs, not the paper, not the ComfyUI tutorial. It is community craft, and practitioners describe it as the difference between mediocre and excellent output `[community — blackmixture, LucidFir, ChairQueen; convergent]`.

The mechanism tells you when the rule matters most. SCAIL-2 must solve two problems at once: *who is this person*, and *how do they map onto the driving performer's pose, scale and framing at frame 0*. A generic portrait forces both problems into the same first denoising steps, and identity loses out. If you instead give it a reference that already *is* the opening frame with the person swapped, the second problem is pre-solved. Pose, scale, screen position, lens and lighting all match. All SCAIL-2 has left to do is track.

| Don't | Do |
|---|---|
| Feed a studio portrait | Extract frame 0 of the driving video, edit the character into it, feed that |
| Write a long descriptive edit prompt | Keep it blunt — the flagship example was literally *"make the man a blonde woman"* |
| Edit the driving video too | Feed the **original, unedited** clip as the motion source; only the reference is edited |
| Expect it to hit a *specific* real face | It changes who the person is; it does not do face→specific-face `[community — Cre0na; single report]` |

**What to edit with:** [`krea-2`](../krea-2/)'s Identity Edit LoRA, Flux 2 Klein 9B, or Qwen-Image-Edit, run image-to-image on the extracted frame `[community — blackmixture, DeerWoodStudios]`.

**The rule generalises into a family of positional hints**: screen position, zoom level, reference ordering in a batch. They all follow the same idea. Pre-solve the correspondence instead of making the model infer it `[community — nsfwVariant]`. Step-by-step instructions: [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §2.

---

## Masks are the control surface

*This section comes before setup and settings because the masks decide which mode you are actually running. No number below matters if the masks are wrong.*

Prompting is not how you steer this model. **Two coloured masks are**, and they are different objects with different rules. Both come from `SCAIL2ColoredMask` and enter `WanSCAILToVideo` on their own inputs `[official — PR #14373 diff]`:

| Mask | Node input | Background | Colour means |
|---|---|---|---|
| **Reference mask** | `reference_image_mask` | **Always black**, in both modes | Which identity each region of the reference is |
| **Driving mask** | `pose_video_mask` — *"Colored per-identity SAM3 mask video"* | **Black = Animation, white = Replacement** | The same palette, so a colour maps a reference region to a tracked person |

**The driving mask's background colour *is* the mode switch, and it must agree with a boolean in two places.** `SCAIL2ColoredMask` and `WanSCAILToVideo` each carry a `replacement_mode` flag. The tooltip tells you to set them together: *"False = mask_video has black bg (Animation Mode). True = white bg (Replacement Mode). Set the matching `replacement_mode` on `WanSCAILToVideo`. `reference_image_mask` is always black-bg regardless."*

> If the pair gets out of step, you hit the vendor's documented failure: *"Without a correct mask, Animation mode collapses into Replacement-mode behavior in certain inputs."* You get a plausible clip doing the wrong job. It keeps the source scene when you asked for a new one, and it shows no error message.

**Identity selection is a core-node input, not a custom pack.** `SCAIL2ColoredMask` exposes `object_indices` (*"Empty = all"*) and `sort_by`, which keeps each identity the same colour across both masks. The full treatment is in [`references/masks-and-tracking.md`](references/masks-and-tracking.md).

---

## Setup & ecosystem

SCAIL-2 runs in **ComfyUI core**. The main node landed in PR **#14373** (`WanSCAILToVideo`), multi-reference support in PR **#14509**, and the tutorial lives at `docs.comfy.org/tutorials/video/zai/scail2`.

### File layout

This table is verbatim from the official ComfyUI tutorial's model table, except the last row `[official — docs.comfy.org/tutorials/video/zai/scail2]`. Most files are Wan 2.1's own, so [`wan-2-2`](../wan-2-2/) users already have nearly everything.

| File | ComfyUI folder | Loader node |
|---|---|---|
| `wan2.1_14B_SCAIL_2_fp16.safetensors` | `models/diffusion_models/` | Load Diffusion Model |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` *(same file Wan 2.2 uses)* | `models/text_encoders/` | CLIPLoader — **type `wan`** |
| `Wan2_1_VAE_bf16.safetensors` *(see trap below)* | `models/vae/` | Load VAE |
| `clip_vision_h.safetensors` *(optional — see below)* | `models/clip_vision/` | CLIPVisionLoader |
| `sam3.1_multiplex_fp16.safetensors` — **SAM 3.1**, and it lives in `checkpoints/` | `models/checkpoints/` | SAM3 loader |
| `wan2.1_SCAIL_2_DPO_lora_bf16.safetensors` — Bias-Aware DPO | `models/loras/` | LoraLoaderModelOnly |
| `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` — speed path | `models/loras/` | LoraLoaderModelOnly |
| **Relighting LoRA** — `model/relighting-lora.pt`, **SAT-format; convert first**. Not in the tutorial's table | `models/loras/` | LoraLoaderModelOnly |

> **The VAE trap.** The right file is `Wan2_1_VAE_bf16.safetensors`. It is *not* the `wan_2.1_vae.safetensors` a Wan 2.2 graph uses, and it is *not* the repo's SAT-format `Wan2.1_VAE.pth`. The same weights ship under three names across three distributions. Only one is what ComfyUI loads, and a wrong-family VAE corrupts colour instead of throwing an error.

**CLIP vision is optional at the node level**: the PR marks `clip_vision_output … optional=True` `[official — PR #14373 diff]`, so a graph without it still runs. The official template supplies it. Leaving it out is a quality choice, not a hard failure.

**One set of weights, two branches.** **`wan-scail2`** (the default) is the Wan-framework inference port that ComfyUI builds on. **`sat-scail2`** is the original **SAT** implementation behind the paper's results. The weights are at HF `zai-org/SCAIL-2`, mirrored as ModelScope `ZhipuAI/SCAIL-2`.

**It is a single dense DiT: one loader, one sampler chain, one LoRA per concept.** If you arrive from Wan 2.2's 14B, unlearn the two-expert wiring. There is no expert pair, no `return_with_leftover_noise` handoff, and no paired LoRA files.

### Stock node settings

The sampler rows are the repo's generation flags. The geometry rows are `WanSCAILToVideo`'s own widget defaults from the PR diff, and the node is what a ComfyUI reader sees `[official — repo generation flags, PR #14373 diff]`.

| Setting | Full-quality path | LightX2V distilled |
|---|---|---|
| Steps / guidance / shift | **40 / 5.0 / 3.0** | **8 / 1.0 / 1** |
| Solver | `unipc` | as above |
| `length` (frames) | **81** | same |
| `width` × `height` | **512 × 896** | same |
| Resolution band | **512p or 704p**; pose-driven *"performs better under 704p"* | same |
| `pose_strength` / `pose_start` / `pose_end` | **1.0 / 0.0 / 1.0** — pose conditioning strength and the step window it spans | same |
| Negatives | Live at guidance 5.0 | **Inert at 1.0** — guidance off |
| Seed | Lower-impact than on a T2V model: motion is tracked, not sampled | same |

**No scheduler is named by any source.** The repo exposes a solver, not a scheduler. The vendor documents a LightX2V path, and that confirms LightX2V only. **Pusa is a separate community claim** `[community — Dzugavili]`.

**Divisibility is contested, but not evenly.** **Two** official sources say **32** (the README and the HF card, both with the worked example 704×1280). The ComfyUI docs page alone says **16** `[contested]`. Use multiples of **32**: it satisfies both readings, and it is where the evidence weighs.

### Quantisation & VRAM

**No vendor VRAM figure exists**, so every figure here is community-measured against no baseline `[community — no official baseline; re-verify]`. **fp8_scaled** clears 16 GB. **GGUF** plus chunking reaches **8–12 GB**, though whether GGUF helps at 16 GB is disputed `[contested]`. One trap belongs up here because it costs speed without throwing an error: **`int8_convrot` can be *slower* than fp8** on a mismatched CUDA/PyTorch build. It is the same CU130 trap that [`minimax-h3`](../minimax-h3/) documents `[community — kayteee1995]`. Measured runs and offload guidance: [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §3.

### diffusers

**There is no diffusers pipeline**, and **no first-party hosted API.** Run ComfyUI or the repo CLI instead. Third-party hosts resell it, on a single unverified report.

---

## Per-mode settings

These are deltas from the stock table above.

### Animation — end-to-end driven

The default: stock numbers, **raw** driving frames, a coloured driving mask on a **black** background, and `replacement_mode: False` on both nodes. If a run goes wrong, re-seeding is the first thing to try `[community — External_Trainer_213]`.

### Animation — pose-driven

Stock numbers, with an SMPL pose render substituting for the driving frames. The vendor states it **performs better at 704p**, so do not run it at 512p and conclude the mode is worse. Reach for it when the source performer's clothing, build or lighting leaks through, because a pose render carries none of that.

A pose or gray-silhouette render also carries no props. Anything the performer holds or moves through is erased, and a close-up crop can collapse the mapping entirely. Keep occluding props out of the drive and stay at medium framing or wider `[community — media-lab dance-swap sessions, 2026-08-28]`. The lived-tested identity moves for this drive family are in [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §4.

### Replacement

Stock numbers, but the driving mask flips to a **white** background and `replacement_mode: True` goes on both nodes. Here the prompt earns what little it earns: describe the replacement character's **clothing** and **what they interact with**. Those are the attributes the model has no reference for once the region is masked `[official — wan-scail2 README]`. Load the **Relighting LoRA**, which is specific to this mode.

### The LightX2V distilled path

8 steps, shift 1, guidance 1.0. Negatives go inert at guidance 1.0, as on any guidance-off path. Use this path to settle masks and reference framing, then re-render keepers on the full path.

**The speed path costs identity, and the cost is measurable.** In lived testing, 8-step distilled renders lost the reference's likeness where a full-guidance run held it. The setup that held identity was **24 steps, guidance 5, shift 3, with the DPO and Relighting LoRAs loaded** — a cheaper delivery point than the stock 40 `[community — media-lab dance-swap sessions, 2026-08-28]`. Iterate at 8 steps, but never judge identity there.

---

## Signature quality — it tracks, and then it embellishes

**Per-frame aesthetic: the swap reads as composited.** The character looks too bright and too clear for the plate `[community — nsfwVariant]`. **The fix is the vendor's Relighting LoRA**, which exists for exactly this. Grade in post only as a fallback. **Text** is the clear weakness, so keep signage and readable screens out of the masked region ([`references/characters.md`](references/characters.md) §6).

**Default motion character: it does not invent choreography.** *"SCAIL-2 tracks the movement sequences and does not invent its own"* `[community — External_Trainer_213]`. Hand it a staged, unconvincing fight and you get a staged, unconvincing fight in a different body. **Output quality is capped by the driving performance.** That is a directing problem, not a prompting one. There is no prompt-side override. The lever is the footage you shoot.

What it *does* invent is **physically consistent embellishment on top of tracked motion**. Examples include fire arcing off a fist with zero fire data in the driving clip, cloth and hair following through, and liquid sloshing inside a swapped-in wine glass `[community — blackmixture]`. **Motion is tracked. Secondary physics is generated.** The limit is that permanence belongs to the *tracked* subject, not the scene. Untracked background figures merge identities `[community — Draco18s]`.

---

## Length, fps and resolution

This budget works differently from every other video model in the suite. **Two of the three axes are set by your input, not by you.**

| Axis | What sets it |
|---|---|
| **fps** | **Your driving video's fps** — motion is tracked frame for frame, so a 24 fps source gives 24 fps out. Action footage downframed to 16 fps looks wrong and the model cannot fix it `[community — nsfwVariant]` |
| **Length** | Your driving clip's, via chunking. Native window **81 frames**; longer output chunks as **81-frame segments, 76-frame stride** `[official — PR #14373 diff]` |
| **Resolution** | Yours, in multiples of 32, inside the documented **512p/704p** band. Practitioners cite a **720p** ceiling, but 720 is not a multiple of 32. Treat **704p** as the real top, and anything above it as post-upscale `[flagged — re-verify]` |

**Whether sliding context windows restore quality or degrade adherence is contested** `[contested]`, so plan as if adherence decays. The guardrail here is **blast radius**: a fault chains downstream, so stay under **~161 frames** per shot `[community — nsfwVariant]`. That is a *risk* limit, not a capacity one. The dispute in full: [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §5.

---

## LoRAs — you load them here, you do not train them

**SCAIL-2 has no LoRA-training path today, and this skill deliberately ships no `lora-training.md`.** A Civitai search returns **workflows only**: no checkpoint, no LoRA, no ControlNet `[community — Civitai models API, 2026-08-22]`. No community trainer documents support `[flagged — re-verify]`. Vendor training code exists on `sat-scail2`, but that is the SAT framework that *produced* the model, not a fine-tuning path with published results. This is coverage rather than a gap: **SCAIL-2's identity mechanism is a reference image, not an adapter.**

**Three vendor LoRAs ship with the model**: **Relighting**, **Bias-Aware DPO**, and **LightX2V**. The one to know is **Relighting**, the vendor's answer to this skill's most-reported artefact. The vendor says it is *"designed for **replacement mode** … making the reference character blend more naturally into the target video with consistent lighting and shadows"*. It ships in SAT format as `model/relighting-lora.pt` and **must be converted to safetensors** for the wan branch. It is absent from the ComfyUI tutorial's model table, which is likely why one practitioner *"couldn't get anything good out of it"* `[community — nsfwVariant; single report]`. Filenames and load order: [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §6.

**Will your Wan 2.1 LoRAs load?** Partly. The architecture says where the line falls. The weights *are* a Wan2.1-14B-I2V fine-tune, so block-level shapes should match. But the **28 extra patch-embedding channels** mean **any LoRA touching the patch embedding cannot transfer**. It will either error or be silently skipped, depending on your loader. Nobody has tested it `[flagged — re-verify]`, so try a throwaway generation first.

Do you need a trained identity, meaning a character in *new* scenes rather than existing footage? Go upstream: [`character-lora-training`](../character-lora-training/) owns the craft, and [`wan-2-2`](../wan-2-2/) owns the video-side training.

---

## Production pipelines & mixing models

SCAIL-2 is a **middle** stage. It cannot originate a shot and produces no audio, so it sits between an image model and a finishing chain:

> **1.** extract driving-clip frame 0 → **2.** edit the character in ([`krea-2`](../krea-2/) Identity Edit / Flux 2 Klein 9B / Qwen-Image-Edit) → **3.** **SCAIL-2** (edited frame + *original* driving video + masks) → **4.** restore/upscale → **5.** interpolate → **6.** audio and finish

**Stage 4 before stage 5, always.** Interpolating first doubles the restorer's workload and bakes smear into the frames it then has to sharpen. Use a temporal restorer (SeedVR2, FlashVSR), never a per-frame image upscaler. A per-frame upscaler has no cross-frame consistency and shimmers.

**Small subjects mush, so give the subject the pixels before you generate.** Pre-crop a wide plate's figures into a tall clip, generate there, then composite back `[community — spiderofmars]`. The worked method: [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §5.

**Audio comes from elsewhere.** SCAIL-2 neither generates nor consumes it. Pair it with [`ltx-2-5`](../ltx-2-5/), [`minimax-h3`](../minimax-h3/), or an NLE. Cross-model craft lives in [`image-production-workflows`](../image-production-workflows/).

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| Output keeps the source scene when you wanted a new one; Animation mode "acts like" Replacement | The driving mask's background colour and the `replacement_mode` booleans disagree, so the model runs the other mode — vendor-stated, and it never errors | Set `replacement_mode` **identically on `SCAIL2ColoredMask` and `WanSCAILToVideo`**, and confirm the mask background matches: black = Animation, white = Replacement |
| Faces drift or become a different person over the shot | The reference had to be re-posed and re-scaled to reach frame 0, so identity competed with correspondence in the earliest denoising steps | Apply the one rule; shorten the shot and re-anchor |
| Distant or full-body figures come out with mushed faces | The character occupies too few pixels for the tracker to segment and the DiT to resolve | Pre-crop and zoom the subject into a tall frame, then composite back |
| Tracker refuses to lock on, even on isolated close-ups | SAM3 produced no usable track; rewording the prompt cannot change a segmentation failure | Re-select the subject by **point** rather than box in your SAM3 nodes, and check `object_indices` on `SCAIL2ColoredMask` is not excluding it `[community — External_Trainer_213]` |
| Character starting off-screen never enters correctly | No on-screen anchor exists at frame 0 for the tracker to fix correspondence against | Process the shot **in reverse**, then re-reverse `[community — nsfwVariant]` |
| Non-target people acquire an outline or glow | Suspected mask/track bleed onto untracked subjects; no vendor acknowledgement exists | Name only the people you want in `object_indices` (empty = all), and point-select each `[flagged — re-verify]` |
| Background changes in Replacement mode when it should be untouched | **No mechanism is known.** Reported consistently, never vendor-acknowledged, and it contradicts the intuition that replacement is character-local | Use a workflow with **RMBG background retention**, which exists to fight exactly this `[community — Coach_Unable; single report]` |
| Hands distort; lips and eyes out of sync | A base-checkpoint weakness the vendor addressed post-hoc rather than in the base weights | Load the **Bias-Aware DPO** LoRA |
| Swapped character reads as pasted on — too bright, too sharp for the plate | The model renders the inserted character without inheriting the plate's lighting and shadow | Load the vendor's **Relighting LoRA**, which exists for exactly this and is specific to Replacement mode; grade in post only if that is not enough |
| Extra references appear to do nothing | The node takes **one** reference image — *"for multiple references composite all on single image"* — with identities distinguished by mask colour, not by batching | Composite the characters onto a single reference and give each its own palette colour |

---

## Pre-flight checklist

1. Reference image **is** the driving clip's edited frame 0, not a portrait?
2. Driving video fed **unedited**, as the motion source?
3. `replacement_mode` set **identically** on `SCAIL2ColoredMask` and `WanSCAILToVideo`?
4. Driving-mask background matching that flag, with black for Animation and white for Replacement?
5. More than one character composited onto **one** reference image, each with its own mask colour?
6. Output fps matched to the **driving video's** fps, not to a habit of 16?
7. Dimensions in multiples of **32**, inside 512p/704p?
8. Pose-driven mode running at **704p**, not 512p?
9. Subject large enough in frame, or pre-cropped and zoomed if not?
10. Shot under ~161 frames?
11. **Relighting LoRA** loaded for a Replacement shot? **Bias-Aware DPO** loaded if hands or lip-sync matter?
12. Post chain ordered **restore/upscale → interpolate**, audio sourced elsewhere?

---

## Where SCAIL-2 sits in the suite

| Job | SCAIL-2 | Reach for instead |
|---|---|---|
| **Replacing a person in existing footage, following their motion exactly** | **The reason to be here.** Tracked, not re-generated — though it changes *who* the person is rather than hitting one named likeness | For a specific real face, build the identity upstream first ([`character-lora-training`](../character-lora-training/)) |
| Locking a still first | Not an image model — but an upstream image edit is mandatory | [`krea-2`](../krea-2/) Identity Edit, Flux 2 Klein 9B, [`flux-2`](../flux-2/), [`z-image`](../z-image/), [`sdxl`](../sdxl/) |
| Originating a shot from text or a still | ❌ No T2V, no I2V — it needs footage to track | [`wan-2-2`](../wan-2-2/), [`ltx-2-5`](../ltx-2-5/), [`minimax-h3`](../minimax-h3/) |
| **Audio** | ❌ **Neither generates nor consumes it** | [`minimax-h3`](../minimax-h3/) generates native stereo audio (**licence excludes US/EU/UK/KR**); [`ltx-2-5`](../ltx-2-5/) also does audio; [`wan-2-2`](../wan-2-2/) S2V *consumes* a track |
| Motion, camera and pose control | Thin — the driving video *is* the control | [`wan-2-2`](../wan-2-2/) — Fun Camera / Fun Control / VACE |
| LoRA ecosystem and training maturity | ❌ **No training path, no published LoRAs** | [`wan-2-2`](../wan-2-2/)'s two-expert ecosystem; [`character-lora-training`](../character-lora-training/) |
| Licence coverage | **Permissive worldwide** — no territory clause | — |
| Post chain, upscale, interpolation | Restore → interpolate, as elsewhere | [`image-production-workflows`](../image-production-workflows/) |
| Multi-person scenes | Weak — the known soft spot | Separate shots, or point-select every character |
| **Choosing between all of these in the first place** | — this table is one model's view of the suite | [`generative-media-atlas`](../generative-media-atlas/) — the whole suite ranked by job (realism, identity, LoRA trainability, control, licence, video), the elimination ladder that settles most choices, and end-to-end routes across several skills |

### The decision you are actually making: *I have a video and I want a different person in it*

| Option | Motion | Identity | Audio | Cost of the win |
|---|---|---|---|---|
| **SCAIL-2** | **Tracked frame for frame** | Reference image, SAM3-tracked | None | You must edit frame 0 first, and you must have footage |
| **Wan Animate** ([`wan-2-2`](../wan-2-2/)) | Transferred, with a relight LoRA | Reference-driven | None | Displaced by SCAIL-2 in community practice, even among people who otherwise run Wan end to end `[community — blackmixture]` |
| **[`minimax-h3`](../minimax-h3/)** video-editing mode | **Re-generated**, not tracked | Prompt-anchored via `retention_analysis` | ✅ native | Approximate motion; a licence excluding US/EU/UK/KR; and an identity latch that gives out somewhere in the **5–7 s** band — two community reports disagree on where and how hard. [`minimax-h3`](../minimax-h3/references/prompting-guide.md) owns that claim and carries both reports plus the reason the 5 s figure may be a harness bug |
| **Bernini-R** (ByteDance — announced, not covered by this suite) | Reference-guided video editing | Reference image(s) + prompt | None | Far more resource-hungry; outfit swap reportedly works, face swap reportedly does not `[community — single report; re-verify]` |

**One verdict spans every row of this table.** With current open tools, source-exact motion and target-exact identity do not coexist in one pass. Plan a two-stage pipeline — a motion pass first, then an identity pass — rather than hunting for a single-pass setting `[community — media-lab dance-swap sessions, 2026-08-28]`.

**Bernini-R is a sibling in function, not lineage.** It is ByteDance's model, built on Wan **2.2** (*"Wan2.2 base — Wan-AI/Wan2.2-T2V-A14B-Diffusers"*), under Apache 2.0 `[official — ByteDance/Bernini-R model card]`.

---

## Licence & limitations

**The licence is split across two artefacts, and both are permissive:**

| Artefact | Licence | Read from |
|---|---|---|
| **Code** — `zai-org/SCAIL-2`, both branches | **Apache License 2.0** | Three independent confirmations: GitHub API `license.spdx_id`, the `LICENSE` file's literal Apache 2.0 text, and the README's own License section |
| **Weights** — `zai-org/SCAIL-2` on Hugging Face | **MIT** | Two: the model card's YAML frontmatter (`license: mit`) and the HF API `cardData` |

Both licences permit commercial use, so this is not the trap that a non-commercial or territorial clause would be. But they are **different texts with different notice obligations**, so a product shipping both artefacts carries both.

**The genuine ambiguity is upstream.** The weights are a full fine-tune of `Wan2.1-14B-I2V`, yet the HF card carries **no `base_model:` field and no Wan 2.1 licence passthrough**. The risk is low, because Wan 2.1 is Apache 2.0 and imposes nothing MIT would violate. Still, the compliance chain here is **inferred, not read**. **Why the split exists at all is unexplained** `[flagged — re-verify]`.

**Vendor-admitted limitations:** a wrong mask silently changes the mode. Multi-reference is unoptimised: *"video qualities may degrade even though additional information do get referenced"*. Pose-driven wants 704p.

**Limitations the vendor does not discuss** are all community-observed and marked at their point of use. They are: text mush, small-subject mush, the multi-person outline/glow, Replacement mode altering backgrounds, and clothing morph past ~5 s. It is also **not real-time**.

**Release & stability:** SCAIL-2 (arXiv 2606.10804, v3 August 2026) is new enough that everything around the weights moves weekly. The front-end **Mix Studio** turns the frame-0 rule into UI, but it is **unaudited**, and an unsubstantiated telemetry accusation against it went unanswered `[flagged — re-verify]`. Do not repeat that accusation as fact, and do not recommend Mix Studio without that caveat.

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts must be exact, or something breaks.** They include zai-org as the maker, the SCAIL-1 predecessor, umT5-XXL and the Wan 2.1 VAE, and the four modes. They include the **three-level Wan 2.1 lineage**: a full fine-tune of `Wan2.1-14B-I2V`, a modified DiT with 28 extra in-context channels plus Mode-Specific RoPE, and code from the Wan 2.1 repo. They include **every filename in the file-layout table**, plus the **two-mask contract and the `replacement_mode` pairing**. They include `WanSCAILToVideo`, `SCAIL2ColoredMask`, `SCAIL2WanModel` and their input names, along with the three vendor LoRAs. They include the 40/5.0/3.0 and 8/1.0/1 pairs, 81 frames, the 76-frame stride, and the 512×896 node defaults. And they include **both halves of the licence split**.

**The source of truth for hard facts is official.** That means arXiv 2606.10804v3 §4.1, which outranks the README on lineage. It also means both branch READMEs read raw, the `LICENSE` file, the HF card frontmatter and API `cardData`, the **PR #14373 file diff**, and `docs.comfy.org/tutorials/video/zai/scail2`. The stakes are concrete. A wrong filename 404s. A misread licence is a legal problem. A mismatched `replacement_mode` yields a plausible clip doing the wrong job. **Two facts circulate wrongly.** First, the README's "project architecture" clause means the *codebase* and attaches to SCAIL-1, not Wan 2.1. Second, the `480p` tag comes from the speed LoRA's filename, which names Wan 2.1's I2V variant. Repack filenames, the template and the quant landscape move weekly, so **re-verify them before relying on them, regardless of who said it.**

**Craft is what actually makes a good clip.** This covers the first-frame edit rule and its positional-hint family, zoom-crop-composite, the reverse-the-shot trick, and the "SCAIL Auto Extend" sampler. It also covers the ~161-frame guardrail, every VRAM and timing figure, and front-and-back reference practice.

**The authoritative source for craft is the community**, meaning practitioners who have run this model on real shots: **blackmixture**, **nsfwVariant**, **spiderofmars**, **External_Trainer_213**, **LucidFir**, **ChairQueen**, **kayteee1995**, **DeerWoodStudios**, **develm0**. The vendor docs cover none of it. Craft claims here are stated with confidence. Ranges mean "your footage and hardware differ from the author's", not "unreliable". **The one rule is community-only and essential, which is exactly why it leads this skill.** This skill sits at the top of the suite's density band, and the reason is structural rather than stylistic. Nine named practitioners carry craft that the vendor documents nowhere, so most craft sentences need their own source.

Held as genuinely contested or unverified:

- **Do sliding context windows restore quality or degrade adherence?** Two credible practitioners report opposite results on minute-plus shots. They may be measuring different things. `[contested]`
- **Dimension divisibility, 32 or 16.** The README and HF card say 32. The ComfyUI docs page says 16. `[contested]`
- **fp8 versus GGUF on 16 GB**. Also an **order-of-magnitude time spread on identical hardware**: 2–3 min against ~20 on the same RTX PRO 6000 class, with no settings dump on either side. `[contested]`
- **Whether general Wan 2.1 LoRAs transfer.** Block-level tensors are plausible, but the 28 extra patch-embedding channels rule out any LoRA touching that layer, and nobody has tested it. The same question applies to the **4-step** Wan speed LoRAs against the documented 8-step path. `[flagged — re-verify]`
- **Why the Apache-2.0 / MIT split exists**, and the HF card's **missing `base_model:` field and absent Wan 2.1 licence passthrough**. The facts are confirmed. Only the reason is not. `[flagged — re-verify]`
- **The multi-person outline/glow artefact**, which was never vendor-acknowledged and is absent from the latest sweep. Also **the 720p working ceiling** practitioners describe, which conflicts with both the 704p band and the /32 rule. `[flagged — re-verify]`
- **Replacement mode altering backgrounds**, **Bernini-R's reported face-swap failure**, and the **Mix Studio telemetry accusation**. Each was raised publicly, each was answered by nobody, and none has been checked against a primary source. `[community — single report; re-verify]`

**Facts dated 2026-08-22**. The fastest-moving parts are the ComfyUI repack filenames, the quant landscape, and the community chunking nodes, so re-verify all three. The mask contract and the licence texts are the stable core.

---

## Reference files

| File | When to read it |
|---|---|
| [`references/masks-and-tracking.md`](references/masks-and-tracking.md) | **Read this before your first run.** The two masks, the `replacement_mode` contract that decides which job the model performs, identity selection, and what masks do not control |
| [`references/setup-and-workflows.md`](references/setup-and-workflows.md) | Wiring the graph, preparing inputs, or planning a long shot: the node walkthrough, the step-by-step first-frame procedure, where to get a driving video, the VRAM/timing table, loading LoRAs, and the chaining ladder |
| [`references/characters.md`](references/characters.md) | Identity has to hold — across a shot, across shots, or across more than one person. When it holds, when it breaks, multi-person limits, likeness and consent, and where identity work belongs upstream |
| [`references/prompting-guide.md`](references/prompting-guide.md) | Writing the prompt. It is deliberately short, because the prompt is the *weakest* control surface here. What the prompt does, what it does not, and the upstream image-edit prompt |

**There is no `lora-training.md`, deliberately.** See [LoRAs](#loras--you-load-them-here-you-do-not-train-them) for why. No training path exists, so [`character-lora-training`](../character-lora-training/) and [`wan-2-2`](../wan-2-2/) own that work.
