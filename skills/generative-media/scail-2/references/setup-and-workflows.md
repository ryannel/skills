# SCAIL-2 — setup, inputs and workflows

This file owns everything between "I have footage and a character in mind" and "I have a finished clip": the ComfyUI graph, the input-preparation procedure that decides whether the run works at all, mask construction, quantisation and measured VRAM/timing, where to get a driving video, chaining for long shots, and **loading and stacking LoRAs**.

It does **not** own *making* a LoRA — and for SCAIL-2 nobody does, which is why this skill ships no `lora-training.md`. See §6 and [`character-lora-training`](../../character-lora-training/). It also does not own identity strategy, which is [`characters.md`](characters.md).

## Contents

1. [The graph, node by node](#1-the-graph-node-by-node)
2. [Preparing the reference — the first-frame procedure](#2-preparing-the-reference--the-first-frame-procedure)
3. [Quantisation, VRAM and measured timings](#3-quantisation-vram-and-measured-timings)
4. [Getting a driving video when you have no footage](#4-getting-a-driving-video-when-you-have-no-footage)
5. [Long shots and the production ladder](#5-long-shots-and-the-production-ladder)
6. [Using and stacking LoRAs](#6-using-and-stacking-loras)
7. [The CLI and the two branches](#7-the-cli-and-the-two-branches)

---

## 1. The graph, node by node

SCAIL-2 is in **ComfyUI core** — PR **#14373** brought the `WanSCAILToVideo` node, PR **#14509** added multi-reference, and there is an official tutorial at `docs.comfy.org/tutorials/video/zai/scail2`. **Load that template rather than rebuilding the graph from this description.** What follows is the topology so you can debug it, not a substitute for the template's own node inventory and default widget values `[flagged — re-verify]`.

The nodes ship in `comfy_extras/nodes_scail.py`, and there are exactly **two**: **`WanSCAILToVideo`** (the conditioning node) and **`SCAIL2ColoredMask`**. `SCAILExtension` is *not* a node — it is the registrar class whose `get_node_list()` returns those two. Internally, **`SCAIL2WanModel`** subclasses ComfyUI's Wan model and registers as `WAN21_SCAIL2` with `image_model: "wan2.1"` `[official — PR #14373 diff]`.

**Five input rails converge on `WanSCAILToVideo`:**

| Rail | Carries | Built from |
|---|---|---|
| **Model** | The SCAIL-2 14B DiT, optionally through `LoraLoaderModelOnly` nodes, then a flow-matching shift node | Load Diffusion Model |
| **Conditioning** | Positive and negative prompt embeddings | CLIPLoader (**type `wan`**, umT5-XXL) → CLIP Text Encode ×2 |
| **CLIP vision** | Image features from the **Wan 2.1 I2V CLIP tower** shipped with the release | CLIPVisionLoader → CLIP Vision Encode |
| **Reference** | The reference image (or a *batch*) plus a matching foreground mask (or batch) | Load Image → optional Batch Images |
| **Driving** | The driving video's frames plus the per-frame mask video | Video loader → SAM3 tracking (`SAM3_TRACK_DATA`) → `SCAIL2ColoredMask` |

Output goes to the sampler, then a **Wan 2.1** VAE decode, then a video combine.

**Three wiring facts that are easy to get wrong and do not error:**

- **The CLIPLoader `type` must be `wan`.** SCAIL-2 uses the same umT5-XXL encoder as [`wan-2-2`](../../wan-2-2/). Set the wrong type and you get embeddings from a differently-shaped tokenizer rather than a load failure.
- **The VAE ComfyUI loads is `Wan2_1_VAE_bf16.safetensors`** — not `wan2.2_vae`, and not the repo's SAT-format `Wan2.1_VAE.pth` (both branches load that one directly). A VAE from the wrong family produces colour and detail corruption, not an error — the same trap [`wan-2-2`](../../wan-2-2/) documents for its 5B/14B split.
- **This is a single dense DiT, not a mixture-of-experts.** One `Load Diffusion Model`, one sampler chain, one LoRA per concept. Arriving from Wan 2.2's 14B, **unlearn the two-expert wiring** — no high-noise/low-noise pair, no `return_with_leftover_noise` handoff, no paired LoRA files.

**Stock settings**, from the repo's own generation flags: 40 steps, guidance 5.0, flow-matching shift 3.0, `unipc` or `dpm++`, 81 frames, 512p or 704p. The distilled LightX2V path is 8 steps, shift 1, guidance 1.0.

**Dimensions:** the GitHub README requires height and width divisible by **32** (its worked example is 704×1280); the ComfyUI docs page says **16**. Use multiples of 32, which satisfies both readings.

---

## 2. Preparing the reference — the first-frame procedure

This is [the one rule](../SKILL.md#the-one-rule-that-changes-everything) as a procedure. It happens entirely outside SCAIL-2, it takes a few minutes, and it is the difference practitioners describe between mediocre and excellent output. **It appears in no official zai-org document** — not either README, not the paper, not the ComfyUI tutorial.

1. **Pick your driving clip and trim it first.** Trim before you extract, so that "frame 0" is the frame the model will actually start from. Re-trimming afterwards invalidates the whole reference.
2. **Extract frame 0** as a still, at the clip's native resolution.
3. **Edit the new character into that frame** with an image-edit model — [`krea-2`](../../krea-2/)'s Identity Edit LoRA, Flux 2 Klein 9B, or Qwen-Image-Edit, running image-to-image on the extracted still `[community — blackmixture, DeerWoodStudios]`.
4. **Keep the edit prompt blunt.** The flagship demonstration used literally *"make the man a blonde woman"*. Long descriptive edit prompts push the edit model into re-composing the frame, which destroys the pose and framing match you are doing this for. One attribute change per pass; iterate if you need several.
5. **Check the edit preserved pose, scale, screen position and lighting.** If the character moved, shrank, or got re-lit, the edit failed at its actual job even if the face looks good. Re-roll.
6. **Generate the reference mask** by running the edited still through a **SAM3 image track** into `SCAIL2ColoredMask`'s `ref_track_data` input — the same node that builds your driving mask, so both share one identity palette. Its background is always black regardless of mode.
7. **Feed the edited still as the reference and the *original, unedited* driving video as the motion source.** Editing the driving video too is a common misreading and gives the model a performance it then has to reconcile with itself.

### When the plain procedure is not enough

All of these are the same idea — **pre-solve the correspondence rather than making the model infer it** `[community — nsfwVariant]`:

| Situation | What to do |
|---|---|
| Character sits somewhere unexpected in frame | Move the character within the reference image to the screen position the replaced person occupies, as if you overlaid the reference on the video |
| Reference is framed tighter or wider than the clip opens | Match the reference's zoom level to the clip's opening zoom |
| Multiple references, wrong one is dominating | Change the order the references are fed into the batch |
| Character enters from off-screen | **Process the shot in reverse** so they start on-screen, then re-reverse the output |
| Character is small in a wide plate | Pre-crop and zoom — see §5 |

### What this does not fix

**Face → one specific real face.** Editing frame 0 changes *who* the person is; it does not reliably hit a named target likeness. That request was posted into the largest thread in the sweep and went unanswered ([`characters.md`](characters.md) §4 owns that claim). If you need a specific identity to hold, the work belongs upstream in the image model — see [`characters.md`](characters.md) §3.

---

## 3. Quantisation, VRAM and measured timings

**No vendor VRAM figure exists in any official document**, so every row below is community-measured against no baseline `[community — no official baseline; re-verify]`. The Source column names who ran it.

| Rig | Job | Time | Source |
|---|---|---|---|
| RTX 6000 Pro 96 GB | one generation | ~2–3 min | blackmixture |
| RTX PRO 6000 Blackwell 96 GB | 10–15 s clip | ~20 min | Cloud9_pilot |
| 4060 Ti 16 GB, fp8_scaled | 253 frames | 9 min | kayteee1995 |
| 4060 Ti 16 GB, int8_convrot | 253 frames | **15 min — slower** | kayteee1995 |
| 5080 16 GB | 5 s, low-res | 13 min | uxl |
| 5060 Ti 16 GB (Wan2GP) | 720p, 5–15 s | ~20 min | paulct91 |
| 4070 Ti Super | 9 s @ 384p, 10 steps | 30 min | wikid24 |

**Read the spread rather than the numbers.** The first two rows are the same GPU class an order of magnitude apart, and neither author published a settings dump. Treat every figure as an existence proof — "this ran on that card" — not a benchmark you can schedule against.

**Four things that actually decide your throughput:**

- **fp8_scaled is the mainstream path** and clears 16 GB comfortably.
- **`int8_convrot` can be slower than fp8** on a mismatched CUDA/PyTorch build — the measurement above was `torch-2.8.0 + cu128`, and the kernel falls back silently instead of erroring. The same trap [`minimax-h3`](../../minimax-h3/) documents for CU130.
- **GGUF at 16 GB is contested.** The low-VRAM ecosystem is GGUF-first — `realrebelai/SCAIL-2_GGUF` plus `dvelm/SCAIL-2-Unlimited-Video-Low-VRAM`, which auto-chunks for **8–12 GB** cards by *"chaining overlapping segments while preserving motion continuity"* `[community — develm0]`. But one practitioner measures GGUF as *slower* than fp8 on 16 GB `[contested]`. Benchmark both before committing.
- **System RAM is the real low-VRAM constraint**: *"it really really likes high system ram amounts, 32, 64, 64+ gbs"* `[community — paulct91]`.

**The gap in that table: there is no 24 GB row.** Nobody in the sweep published a 3090/4090 measurement, which is the most common card a reader brings. Interpolating between the 16 GB and 96 GB rows is guesswork, so this skill does not do it — expect fp8 to be comfortable and plan your first run as a measurement.

**The OOM you cannot predict.** Nobody in the sweep has a formula relating duration × resolution × models × LoRAs to peak VRAM — *"I still don't know how to calculate durationXresolutionXmodels&loras to figure out if I'm going to OOM or not"* `[community — ChairQueen]`. The working practice is to **reduce input resolution before you start**, not after the first OOM. Renting rather than owning the card? [`comfyui-on-runpod`](../../comfyui-on-runpod/) owns volume layout and `extra_model_paths.yaml`.

**Runners other than plain ComfyUI:** **Wan2GP** is the low-VRAM runner of choice; **Mix Studio** exposes SCAIL-2 as a one-click mode alongside Krea 2, Flux 2 Klein and Qwen-Image-Edit — literally the first-frame rule built into a UI — but it is **unaudited**, and an unsubstantiated telemetry accusation against it went unanswered `[flagged — re-verify]`.

---

## 4. Getting a driving video when you have no footage

SCAIL-2 has no T2V and no I2V mode, so **a driving video is a hard prerequisite** — and the performance in it caps your output, because the model tracks rather than invents choreography.

| Source | What you get | When |
|---|---|---|
| **Real footage** | The best results, and the reason to use this model at all | You are replacing someone in something that already exists |
| **Mixamo** | Clean rigged mocap; tick "in place" for locomotion you want to composite `[community — LucidFir]` | You need a specific, clean body action |
| **SnapMoGen mocap library** | Searchable mocap exported as OpenPose / mannequin / clay / volumetric drivers, explicitly for SCAIL-2 among others `[community — nghtdrp]` | You want to search a motion by description |
| **A generated clip** | A driving video from [`wan-2-2`](../../wan-2-2/), [`ltx-2-5`](../../ltx-2-5/) or [`minimax-h3`](../../minimax-h3/) | You need motion that does not exist and cannot be mocapped |
| **Yourself on a phone** | Underrated. You are directing a performance, not writing a prompt | Anything gestural |

**Match the fps you intend to deliver at.** Output fps follows the driving video, because motion is tracked frame for frame. Downframing action footage to 16 fps to match a Wan habit looks wrong and the model will not fix it — *"I did it in the native 24fps the movie is in. You can't really do it any other way with action scenes"* `[community — nsfwVariant]`.

**Pose-driven mode changes what the driving video must be.** An SMPL pose render carries the skeleton and nothing else — no clothing, build or lighting from the source performer. Reach for it when the original performer bleeds through, and run it at **704p**.

---

## 5. Long shots and the production ladder

### 5.1 The ladder

> **1.** extract driving-clip frame 0 → **2.** edit the character in ([`krea-2`](../../krea-2/) / Flux 2 Klein 9B / Qwen-Image-Edit) → **3.** **SCAIL-2** → **4.** restore/upscale → **5.** interpolate → **6.** audio and finish

| Stage | Settings | Bypassable? |
|---|---|---|
| 2 — first-frame edit | Blunt single-attribute prompt, image-to-image on the extracted still | **No.** This is the one rule |
| 3 — SCAIL-2 | 40 / 5.0 / 3.0, 81-frame window, ≤ ~161 frames per shot | No |
| 4 — restore / upscale | A **temporal** restorer: SeedVR2 or FlashVSR. Never a per-frame image upscaler | Yes, at a quality cost |
| 5 — interpolate | RIFE, after stage 4 | Yes |
| 6 — audio | External: [`ltx-2-5`](../../ltx-2-5/), [`minimax-h3`](../../minimax-h3/), or an NLE | Only if the piece is silent |

**Restore before you interpolate.** Interpolating first doubles the restorer's workload and bakes interpolation smear into the frames it then has to sharpen; a per-frame image upscaler has no cross-frame consistency and produces shimmer. Cross-model craft — denoise bands, decode-to-pixels handoffs, tiled upscale — is [`image-production-workflows`](../../image-production-workflows/).

### 5.2 The zoom-crop-composite method

SCAIL-2 handles small subjects badly: a 1280×720 plate with head-to-toe figures gives mushed faces, because the characters occupy too few pixels for the tracker to segment and the DiT to resolve. **Give the subject the pixels before you generate.** The method below is one practitioner's, worked end to end `[community — spiderofmars]`.

1. Pre-crop the characters out of the wide plate into a tall clip.
2. Generate at **704×1280** — a 720-pixel-tall figure in the plate becomes a 1280-pixel-tall one. (The cited practitioner writes 720×1280, but **720 is not a multiple of 32**; 704 is the nearest legal width and the README's own worked example.)
3. Scale the result back down onto the 1280×720 timeline. *"The colour matching out of the box is almost perfect."*
4. Outpaint the black borders — the cited method uses LTX for this step.

A coarser version handles any wide shot: zoom in so SCAIL-2 recognises and replaces the character, then composite the zoomed footage back over the wide plate `[community — nsfwVariant]`.

### 5.3 Going past 81 frames

**Chunking is built into `WanSCAILToVideo` itself** — no custom pack needed. Three inputs do it: `previous_frames` (*"Full decoded output of the previous chunk"*), `previous_frame_count` (default **5** — *"SCAIL-2 trained at 5 (81-frame chunks, 76-frame step)"*), and `video_frame_offset` (*"Cumulative output frame this chunk begins at. Wire from the previous chunk's `video_frame_offset` output"*) `[official — PR #14373 diff]`. That is where the 81/76 numbers come from and how you chain segments on the stock graph.

Community tooling extends it further: `collbroGTR/comfyui-scail2-infinity` (reported at 11 s of 1408×2560 after upscale, with a ceiling near 285 frames of roughly 972×1728 input — 972 is not a multiple of 32, so treat that figure as an approximate report `[community — LucidFir]`) and the "SCAIL-2 Unlimited Length" workflow.

**Sampler choice matters for chained output.** The **"SCAIL Auto Extend"** sampler *"seems to have no or fewer color shifts. And doesn't need the 'Color Match' option (This is already integrated)"* `[community — External_Trainer_213]`.

**Input-video interpolation is a real trade, not a free win.** Interpolating the *driving* video before generation makes the animation much smoother, at the cost of more compute and — the part that matters — *"Scail-2 is quicker to 'forget' new parts of the animation"* `[community — External_Trainer_213]`.

**Context windows are contested.** One practitioner reports a 1:45 single shot at full consistency with quality *restored* past a window boundary; another reports *"only the first 30 seconds were perfect"* on a one-minute clip `[contested]`. They are plausibly measuring different things — image quality versus adherence to the driving video. **Plan as if adherence decays**, and keep shots under **~161 frames** regardless, because the real risk is chaining: a fault propagates into everything downstream of it `[community — nsfwVariant]`.

**Joining separate clips** is a different problem from extending one. The named long-form stack runs [`wan-2-2`](../../wan-2-2/)'s **VACE** to join clips, then an **SVI** LoRA with context windows to refine the join — *"brings the quality back up across the whole thing and also hides the boundaries between all the individual clips - they tend to have things like color shifts and quality drops"* — demonstrated on a 42-second loop assembled from ~16 clips `[community — nsfwVariant]`.

### 5.4 Fixing lighting and clarity in post rather than re-rolling

The two standing artefacts — the inserted character being **too bright** and **too clear** for the plate — are cheaper to fix downstream than to fight with settings. Re-mask the character with **SAM3** in post and adjust brightness and clarity in a normal NLE `[community — nsfwVariant]`. Re-rolling for this specific pair of problems is wasted GPU time.

---

## 6. Using and stacking LoRAs

**Making** a LoRA for SCAIL-2 is not covered here, and not anywhere else either — no trainer supports the architecture and no SCAIL LoRA has been published; a Civitai search returns **workflows only**, no checkpoints and no adapters `[community — Civitai models API, 2026-08-22]`. Identity work belongs in the image model that makes your reference frame; see [`character-lora-training`](../../character-lora-training/) for the craft and [`wan-2-2`](../../wan-2-2/) for video-side training on the nearest architecture.

**Loading** is ordinary: `LoraLoaderModelOnly` on the model rail, before the shift node. **One loader per LoRA — there is no expert pairing here.** The first three rows below ship with the weights and are vendor-documented `[official — wan-scail2 README]`; the last two are not.

| LoRA | What it is | File |
|---|---|---|
| **Relighting** | **Vendor-shipped and vendor-documented**: *"Relighting LoRA is designed for **replacement mode** and improves replacement quality by making the reference character blend more naturally into the target video with consistent lighting and shadows."* This is the intended fix for the composited, too-bright insert — reach for it before grading in post (§5.4) | `model/relighting-lora.pt` — **SAT format; convert to safetensors** for the wan branch. **Not in the ComfyUI tutorial's model table**, so it is a manual add |
| **Bias-Aware DPO** | The vendor's own post-training stage — rank-128 adapters over a frozen backbone — shipped separately rather than baked in. Alleviates hand distortion, improves lip/eye sync. Load it first if hands are your failure mode | `wan2.1_SCAIL_2_DPO_lora_bf16.safetensors` |
| **LightX2V** | Distilled speed path: **8 steps, shift 1, guidance 1.0**, via `--lora_path`. Negatives go inert at guidance 1.0; whether the **4-step** Wan variants work as well was asked and never answered `[flagged — re-verify]` | `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` |
| **Pusa** | A second speed-LoRA family reported compatible — community-sourced, unlike the three above | `[community — Dzugavili]` |
| General **Wan 2.1** LoRAs | Block-level shapes should match — the weights are a Wan2.1-14B-I2V fine-tune — but the **28 extra patch-embedding channels** block any LoRA touching that layer. Untested by anyone `[flagged — re-verify]` | — |

**On the Relighting LoRA's reputation.** One practitioner tried it and got nothing usable — *"don't take my word on that"* `[community — nsfwVariant; single report]`. Weigh that against the vendor's description, not above it: the LoRA is mode-specific to Replacement and needs a format conversion the ComfyUI path does not do for you, so a disappointing result is at least as likely to be a setup problem as a capability one.

**Use the speed path to iterate, the full path to deliver.** Masks, tracker selection and reference framing are what you are actually tuning, and all three are visible at 8 steps. Re-render keepers at 40.

---

## 7. The CLI and the two branches

There is **no diffusers pipeline** and **no first-party hosted API**. Outside ComfyUI, you run the repo:

- **`wan-scail2`** — the **default branch**: a streamlined inference reimplementation in the Wan checkpoint/config idiom, with `convert.py` turning the SAT checkpoint into `.safetensors`. This is what ComfyUI and every community tool build on, and what you want unless you are training.
- **`sat-scail2`** — *"the original **SAT-based** implementation of SCAIL-2 used to produce the results reported in the paper"* `[official — branch README]`. SAT is SwissArmyTransformer, the same training framework behind CogVideoX. Training lives here.

**A citation trap worth knowing.** `zai-org/sat-scail2` does not exist as a repo — it 404s; `sat-scail2` is a *branch*. And the much-quoted Acknowledgements sentence, *"Our implementation is built upon the foundation of Wan 2.1 and the overall project architecture is inherited from SCAIL"*, is in the **`wan-scail2`** README, not the SAT one — and its architecture clause attaches to **SCAIL-1**, meaning the codebase. The weights-level lineage comes from the **paper**, not from that sentence.

CLI generation names the checkpoint `--model SCAIL-14B` and takes `--max_frames 81` alongside the steps/shift/guidance/solver flags in §1. A **Gemini-backed `prompt_enhancer.py`** ships in the repo for expanding short prompts into the long, detailed result-descriptions the model was trained on — see [`prompting-guide.md`](prompting-guide.md) §3.

Weights: `zai-org/SCAIL-2` on Hugging Face, mirrored as `ZhipuAI/SCAIL-2` on ModelScope. Note the **licence split** — Apache 2.0 on the repo's `LICENSE`, MIT in the HF card frontmatter. Both are confirmed from primary sources; only **why they differ** is unknown `[flagged — re-verify]`.
