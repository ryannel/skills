---
name: ltx-2-5
description: >
  Authoritative guide for LTX-2.5 and LTX-2.3 (Lightricks), the open-weights 22B audio-video diffusion
  transformer that generates picture and synchronised 24 kHz stereo sound in a single joint pass — in ComfyUI,
  the `ltx-pipelines` CLI, or the hosted LTX API. **Read the licence block first: the LTX-2.x Community
  License is free commercially only below $10,000,000 annual revenue aggregated across affiliates; Attachment
  A ¶20 bars any product competing with Lightricks' commercial products or services — photo and design apps
  included, not only video — at any revenue level; every derivative including a LoRA inherits the licence and
  carries the revenue obligation to whoever receives it; and the incorporated Acceptable Use Policy prohibits
  sexually explicit content universally, local weights included.** Use this whenever the user touches LTX in
  any way, even obliquely: choosing between 2.5 and 2.3 and actually setting either up (different checkpoint
  layouts, different text encoders, an unsettled question over which licence text governs 2.3, and the LoRA
  and IC-LoRA ecosystem still on 2.3 — 168 Civitai LoRAs against 3), installing it (the split per-component
  files, the custom Gemma 4 12B a stock Gemma cannot substitute for, the 66 GiB download, VRAM), writing
  prompts, **writing a multishot prompt** — the headline capability, which is a prose technique with no node
  and no flag behind it — hitting the `8k+1` frame lattice or the multiple-of-32 dimension rule, picking a
  legal fps, running the distilled pipeline at CFG 1 where the shipped negative prompt does nothing, choosing
  between the conv and diffusion video decoders (the usual first-run OOM is at *decode*), Diffusion Fidelity
  Rendering, IC-LoRAs, training a LoRA with `ltx-trainer`, holding a character across cuts, generating or
  freezing audio, using LTX as the finishing upscaler on [`minimax-h3`](../minimax-h3/) output, debugging
  smearing, skipped motion beats, face drift, silent-clip failures or dropped tail frames, or comparing it
  against Wan 2.2 and MiniMax H3. Also covers who should reach for something else instead. Choosing between
  models, comparing them, or working out which skills and install commands a job needs is
  [`generative-media-atlas`](../generative-media-atlas/)'s job — start there when the model is not already
  settled.
---

# LTX-2.5

LTX-2.5 is a **22B-parameter asymmetric dual-stream diffusion transformer** from **Lightricks**, released **11 August 2026** under the bespoke **LTX-2.x Community License**. Forty-eight blocks are shared by a video stream (3D RoPE over x, y, t) and an audio stream (1D temporal RoPE). The two streams have different widths, and bidirectional cross-attention plus cross-modality AdaLN link them together. That means **video and 24 kHz stereo audio are denoised jointly in one pass**, not in a separate T2V→V2A chain. The text encoder is a **custom Gemma 4 12B** with the projection bundled in. That is LLM-class conditioning, not T5 and not CLIP, so it wants flowing prose rather than tag soup. The 22B figure is Lightricks' own for 2.3/2.5 `[official — ltx.io/llm-info]`. The block count, the RoPE split and the cross-modality AdaLN come from the architecture doc `[official — ltx-core README]`, which describes the earlier 19B model as 14B video + 5B audio. **How 2.5's 22B divides between the two streams is not published** — do not assume 17B+5B.

**The defining trait:** **native multishot.** One generation produces **two to four connected shots** — one to three cuts — with named transitions between them, holding character, environment, lighting, voice and style across the cut. Nothing else in this suite cuts inside a single pass. You invoke it entirely through the prompt: no shot parameter, no node, and no separate checkpoint behind it.

**The defining constraint:** the licence is not permissive. It gates on four independent axes — revenue, field of use, content, and what happens to anything you train. Settle it before you download 66 GiB.

> **A `../link/` on this page that doesn't resolve is a skill you have not installed, not a broken
> page.** [`generative-media-atlas`](../generative-media-atlas/) is the map of this suite: which
> model fits a job, which skills that job needs, and the commands to install them. It works on its
> own, so it is the one to add first — `npx skills add ryannel/skills --skill generative-media-atlas`

---

## Before anything else — the licence and its four gates

The **LTX-2.x Community License Agreement** is dated **11 August 2026**, governed by New York law with ICC arbitration, and unamended since. The weights are gated on Hugging Face behind contact information and a marketing-consent click-through. The licence text itself is ungated, and anyone can read it at `github.com/Lightricks/LTX-2/blob/main/LICENSE.md`. `[official — LICENSE.md, read from the raw file]`

**Gate 1 — the revenue threshold.** §2.1, verbatim (bold in the original):

> "…you are granted a non-exclusive, worldwide, non-transferable and royalty-free limited license … for any purpose, subject to the restrictions set forth in Attachment A; **provided however, that Entities with annual revenues of at least $10,000,000 (the "Commercial Entities") are required to obtain a paid license for any use** (excluding use solely for a Non-Commercial Purpose as set forth in Section 2.2) **of LTX-2.x and Derivatives of LTX-2.x**…"

§1.6 aggregates that revenue across "all subsidiaries, affiliates, and other companies under common Control … collectively," so a small studio owned by a large parent is over the line. §2.2 is the useful other half: a Commercial Entity may still use the model unpaid **solely for evaluation, testing and non-production R&D**. Paid terms exist only by emailing `ltxv-licensing@lightricks.com` — there is **no published fee schedule**. Unlike MiniMax H3, there is **no territory clause** here beyond the OFAC/EAR warranty in §7.

**Gate 2 — Attachment A ¶20, which has no revenue floor.** Attachment A is not merely a pointer to an acceptable-use policy. It enumerates twenty restrictions, and ¶20 is the commercially sharpest term in the document. You may not use LTX-2.x "in any product, service, or application that **directly competes with Licensor's commercial products or services**, or is designed to replace or substitute Licensor's offerings in the market, without obtaining a separate commercial license." The clause says "commercial products or services", unqualified. Lightricks ships photo and design apps (Facetune, Photoleap) alongside video, so the surface is wider than a video-tool test would suggest. It plausibly reaches much of what anyone would build with an open generative model, **at any revenue, including zero**. Read it before the $10M bar. ¶17 bars military use and ¶19 bars circumventing watermarking. ¶18 bars training other models but scopes itself "for commercial use only," while the incorporated AUP bans the same conduct unconditionally — a hobbyist distilling LTX output into another model sits in that gap.

**Gate 3 — no sexually explicit content, and it binds local weights.** Attachment A incorporates the **Acceptable Use Policy** "into and made part of this Agreement by reference." The AUP (2026-03-30) carries a section headed **"Do Not Generate Sexually Explicit Content"** covering sex acts, fetish content, incest, bestiality and erotic chat. That section sits inside the AUP's **Universal Usage Standards**, above the API-specific part, and the AUP's scope names "on-premises deployments" — so this is not a hosted-only rule you can read around. ¶7 separately bans deepfake impersonation. This is the sharpest practical difference from [`wan-2-2`](../wan-2-2/), which has no acceptable-use clause at all.

**Gate 4 — derivatives inherit, and the obligation travels with them.** §1.5 and §3.5 name a **LoRA adapter as a Derivative**, and §3.2 requires any Derivative be distributed "**exclusively under the terms of this Agreement**." Then §3.5 says: "If the transferee is a Commercial Entity … it must obtain a paid license from Licensor prior to any use of any Derivative of LTX-2.x, **regardless of who created such Derivative**." **This agreement does not let you publish an LTX LoRA under a permissive licence.**

**Outputs are yours, but not free and clear.** §5 says "Licensor claims no rights in the Output you generate," and there is genuinely **no branding duty**. But ¶5 forbids disseminating output "without expressly and intelligibly disclaiming that the information and/or content is machine generated," and §6 forbids stripping watermarking or provenance. It also lets Lightricks **revoke the licence immediately** where it merely "reasonably believes" you did.

**And LTX-2.3's licence is unsettled.** Three live pointers give two documents: the repo *ships* the older **LTX-2 Community License Agreement (5 January 2026)** — with **double liquidated damages** and **no non-commercial carve-out** — while its own `license_link` and body link both resolve to the August text, and §1.9 scopes that text to 2.5 and later. This is unsettled, and the reference argues it clause by clause.

**This skill does not tell you what your legal position is.** Clause by clause, with the 2.3 pointer table and the AUP's scope argument in full: [`references/licence-and-derivatives.md`](references/licence-and-derivatives.md).

---

## Variant selector

LTX runs **two composable axes**, the way [`sdxl`](../sdxl/) runs speed variant × checkpoint dialect: **which version** (here) and **which task mode** (next). Version resolves first. It decides file layout, encoder, licence text and which adapters exist.

| Pick | Use when | What you get |
|---|---|---|
| **2.5 distilled** — `ltx-2.5-22b-distilled-transformer-bf16` / `-comfy-int8-convrot` | Default; all three official Comfy templates load the int8 build | 8+3-step two-stage generation, no guidance needed, multishot, keyframe slots, the diffusion decoder |
| **2.5 dev/full** — `ltx-2.5-22b-dev-transformer-bf16` | You need working CFG and negatives, or maximum fidelity | The guided pipelines. A different hardware class from the distilled build — the only measured report is of the **2.3** dev checkpoint refusing to run on a 3090, and no 2.5-dev figure exists `[community — Comfortable-You-3881; single report, 2.3]` |
| **2.5 int8 / nvfp4** | Consumer cards; nvfp4 needs Blackwell | Pre-optimised builds. **No `LTX-2.5-fp8` repo exists** — use `--quantization fp8-cast` |
| **2.3** — `Lightricks/LTX-2.3` (+ `-fp8`, `-nvfp4`) | You need the IC-LoRA stack, the community LoRA library, or the API's Retake / Extend / Reframe / HDR endpoints | A monolithic checkpoint plus a **separately downloaded Gemma 3 12B** `[official — MODELS-LTX-2.3.md]`, and **168 of ~171 community LoRAs** `[community — Civitai API 2026-08-22]`. Which licence text governs is unsettled — see below |

Two more checkpoints are rarely the answer: **`LTX-2.5-Pre-Trained`**, the raw non-SFT base for domain fine-tuning, and the superseded **LTX-2 (19B)**, which still hosts the camera-control LoRAs — files that may be stale marketing.

**2.3 is not a legacy version, and the ecosystem is still on it.** It has more HF downloads than 2.5 (1.58M vs 695k on 2026-08-22), and **Civitai carried 168 LoRAs tagged LTXV 2.3 against 3 tagged LTXV 2.5** on 2026-08-22. Treating 2.5 as the obvious default misleads anyone whose work depends on an adapter. Whether 2.5 is better is contested by mode: "T2V is looking pretty bad comparatively next to the 2.3 distilled model, but the I2V model has improved substantially" `[community — Comfortable-You-3881; contested]`.

**Do not plan around 2.3 as the ungated escape hatch.** The base repo is ungated, but most of its adapter repos are not. So a 2.3 route still needs an accepted gate and a scoped token: [`references/licence-and-derivatives.md` §9](references/licence-and-derivatives.md#9-gating-and-what-could-not-be-reached).

**The two file sets are mutually exclusive.** 2.5 ships one file per component; 2.3 ships a monolith bundling the transformer, both VAEs and the text projection. "Mixing the two sets is an error." And **a stock Google Gemma 4 will not substitute for 2.5's encoder**: loading checks it against `gemma4-12b-ltx-v1` and rejects a mismatch `[official — LTX-2 README]`.

> **Adapters cross the version line, and that inverts this suite's usual rule.** `MODELS-LTX-2.3.md` says "a LoRA only works with the model it was trained on" — the line every other skill here repeats. But Lightricks' own shipped 2.5 workflows load 2.3-trained adapters. So assume a 2.3 **IC-LoRA** works on 2.5 unless its listing says otherwise, and test a plain 2.3 LoRA at low strength first. `[contested — vendor docs against vendor README]` The evidence: [`references/setup-and-workflows.md` §6](references/setup-and-workflows.md#6-using-loras-and-ic-loras).

**IC-LoRAs** are Lightricks' control mechanism. They are neither a ControlNet nor a style LoRA: an IC-LoRA takes a **reference input** as well as text and applies frame-level spatial control with an optional mask, because it trained on *paired* video and control signal. Exactly one is 2.5-native (`LTX-2.5-22b-IC-LoRA-Pixel-Spatial-Upscaler`). **HDR, Dub-It and Relight are 2.3-only**, and the advertised **Video Editing IC-LoRA** is API-only `[pending release]`. Inventory, nodes and wiring: [`references/setup-and-workflows.md`](references/setup-and-workflows.md).

---

## Task-mode selector

Modes are **pipelines**, not checkpoints: one transformer, twelve `python -m ltx_pipelines.<name>` entry points `[official — docs/pipeline-selection.md]`.

| Mode | Pipeline | Use when | Strong? |
|---|---|---|---|
| **T2V / I2V, two-stage** | `DistilledPipeline` | The default: 8 predefined sigmas, "no guidance required" | **Yes** — the vendor's recommendation |
| **T2V / I2V, max detail** | `DFRPipeline` | Fast motion, fine detail, fps doubling | Yes, **2.5 only** — 2.3 raises rather than silently ignoring |
| **T2V / I2V, guided** | `TI2VidTwoStagesPipeline` / `…HQPipeline` | You want CFG and negatives to work | Yes, on the dev checkpoint |
| **Reference-driven control** | `ICLoraPipeline` | Depth/pose/canny retarget, inpaint, clean plate, motion track — **and reference-sheet character work via Ingredients**, which takes panels rather than a driving clip | Yes — **distilled only**, and only via IC-LoRAs; there is no generic V2V mode |
| **FLF2V / keyframes** | `KeyframeInterpolationPipeline` | Hitting a target end state | Yes — uses *guiding* latents, not replacement |
| **A2V** | `A2VidPipelineTwoStage` | You have a track and want picture for it | Yes — audio frozen and passed through, not re-decoded |
| **Foley / audio-only** | trainer V2A mode; `T2AOneStagePipeline` | Sound for a silent clip; audio with no video | Yes — the audio branch runs standalone |
| **Retake a time region** | `RetakePipeline` | Regenerate seconds 3–6 only | Yes — video and audio regeneration are independent |
| **Extend** | — | Continuing past the last frame | **No local pipeline exists.** The API endpoint is `ltx-2-3-pro` only |

Three more are not worth reaching for yet: `TI2VidOneStagePipeline` is "primarily for educational purposes," and `DubItPipeline` (single-speaker, no translation) and `HDRICLoraPipeline` are betas running **2.3 IC-LoRAs only**.

**Audio, in the three-state sense this suite uses: LTX both generates and consumes.** It gives synchronised stereo by default, A2V with audio frozen, and V2A foley with picture frozen. That is wider than [`minimax-h3`](../minimax-h3/) (generates only) or [`wan-2-2`](../wan-2-2/) (S2V consumes only).

---

## The one rule that changes everything

**The cut is a sentence, not a setting.**

Other video models let you set where the shots change, how long the clip runs, what the soundtrack does across an edit, and who the person in frame is after the camera moves — each as its own parameter. LTX-2.5 exposes all of that only through the prose of one chronological paragraph. There is no `--shots` flag, no multishot node, no shot-list field, in the repo or in `ComfyUI-LTXVideo`.

The mechanism is architectural. A Gemma 4 12B decoder-LM conditions a single sequence in which video tokens and audio tokens denoise together. Temporal structure lives *inside* that sequence, so the only handle on it is the text conditioning the whole thing. Write "a hard cut transitions to a medium close-up of her face" and the model has been told where the edit falls. Leave it out and you get one continuous take, no matter what you set elsewhere.

| Don't | Do |
|---|---|
| `SHOT 1: wide. SHOT 2: close-up.` | *"A wide shot frames a rainy intersection… **A hard cut transitions to** a medium close-up of her face…"* |
| Silently changing subject between cuts | *"**the woman in the yellow raincoat**, earlier at the curb, now…"* — re-identify by the same anchor |
| Leaving the soundtrack unmentioned at a cut | *"**the synth score continues across the cut**, traffic muffled"* |
| Feeding a silent clip to a V2V or upscale run | Add a silence track — **a silent clip fails outright**, because audio and video are encoded jointly `[community — DaLyon92x]` |
| Tag soup, keyword lists, boolean negatives | One flowing present-tense paragraph, 4–8 sentences, under 200 words |

Three things follow from this. **Duration is also a sentence**: with the `ltx-2.5-duration-head` patch and `--auto-duration MIN MAX`, the model reads clip length off the prompt, so "a one-line action stays short, a multi-shot sequence runs longer." **Multishot fights image-to-video**, because the conditioning frame anchors a framing that a cut must then abandon, and vendor guidance is to "prefer a single continuous take" for I2V. And **the working range is 2–4 *shots*, meaning one to three cuts** — the vendor's number counts shots, not edits, so a three-cut sequence is already at the ceiling. Anatomy, the four per-cut rules and worked prompts: [`references/prompting-guide.md`](references/prompting-guide.md).

---

## Setup & ecosystem

### File layout

Everything below is from **`Lightricks/LTX-2.5`** unless noted. On rented GPUs, [`comfyui-on-runpod`](../comfyui-on-runpod/) owns the volume contract. The quick-start set is **roughly 66 GiB** `[official — LTX-2 README]`.

| File | ComfyUI folder | Loader node |
|---|---|---|
| `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` | `models/diffusion_models/` | Load Diffusion Model |
| `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` | `models/text_encoders/` | CLIPLoader |
| `ltx-2.5-video-vae-bf16.safetensors` (diffusion decoder) **or** `ltx-2.5-video-vae-conv-bf16.safetensors` (conv) | `models/vae/` | Load VAE |
| `ltx-2.5-audio-vae-bf16.safetensors` | `models/vae/` | Load VAE |
| `ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors` | `models/latent_upscale_models/` | `LatentUpscaleModelLoader` (the loaded model then feeds `LTXVLatentUpsampler`, which takes no filename) |

Three optional files: the distilled LoRA `ltx-2.5-22b-distilled-lora-450-bf16` (`models/loras/`), the `gemma4_e2b_it_bf16` prompt enhancer, and `ltx-2.5-duration-head-bf16` (`models/model_patches/`) for auto-duration.

> **Which video VAE you pick is a quality *and* a survivability decision, and it is the number-one first-run failure.** The `DiffusionVideoDecoder` iteratively denoises pixels via Euler steps instead of one deterministic pass, giving "sharper faces in close-up, more legible text and signage, and fewer smears in fast motion" — at the cost of decode time and VRAM. On 12–16 GB cards it OOMs **at decode, after sampling has already succeeded**, which is why the failure reads as inexplicable. The fix: *"use video vae conv bf16 fixed for me — I can generate 1mp 20sec no OOM"* `[community — irmemon225, matik802]`. Second line of defence is `VAEDecodeTiled`. Note also that **the `ComfyUI-LTXVideo` top-level README is still 2.3-centric** — the 2.5 material is in `example_workflows/2.5/README.md`, branch `master`.

### Running LTX-2.3 instead

**2.3 is not 2.5 with different filenames.** It is a different install shape, and three facts decide whether it runs at all:

- **One monolithic file** bundles transformer, both VAEs and the text projection, so `models/vae/` stays empty.
- **The text encoder is not bundled and is not 2.5's.** Download **Gemma 3 12B** separately from `google/gemma-3-12b-it-qat-q4_0-unquantized` `[official — MODELS-LTX-2.3.md]`.
- **The lattice applies unchanged** — `8k+1` frames, /32 dimensions, fps in {24, 25, 48, 50}.

The rest of the shape — quantised builds, which README and graphs are the 2.3 ones, what exists only there, and the three numbers this skill cannot give you: [`references/setup-and-workflows.md` §2](references/setup-and-workflows.md#2-files-and-the-split-versus-monolith-rule).

### Stock node settings — verbatim from `video_ltx2_5_t2v.json`

Values below are what the graph **executes**, which is not always what the serialized widgets say — see the warning under the table. The default output is **1280×736 (0.9 MP)** at 16:9, produced by `ResolutionSelector` and halved for stage 1.

| Setting | Value |
|---|---|
| Sigmas (`ManualSigmas`) | Stage 1 `1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0`; stage 2 `0.85, 0.725, 0.4219, 0.0` |
| Sampler / guider | `euler_ancestral`; `LTXVDualCFGGuider [1, 1]` |
| Latent (**executed**, not the serialized widget) | stage 1 builds **640 × 368 × 121** — half the 1280×736 output, 5 s × 24 fps + 1. The `EmptyLTXVLatentVideo [768, 512, 97, 1]` you can grep out of the file is inert |
| Audio latent | `LTXVEmptyLatentAudio`, frame count linked to the video latent's |
| Enhancer | `prompt_enhance` **`False`** — off by default |
| fps / decode / output | `LTXVConditioning [24]` → `VAEDecodeTiled [512, 64, 64, 16]` + `LTXVAudioVAEDecode` → `CreateVideo [24, 8]` |
| Shipped negative prompt | `pc game, console game, video game, cartoon, childish, ugly` |

> **At CFG 1 that negative prompt does nothing.** The dual-CFG guider takes both conditionings, but a guidance scale of 1 collapses the difference between them. Do not spend an hour tuning the string. Raising CFG will not help either: "The distilled model bakes guidance into distillation, so raising CFG doesn't improve output … and adds overhead. If you experiment, stay in the 1.0–1.5 range" `[official — docs.ltx.io]`. **Negatives only do real work on the dev checkpoint through `TI2VidTwoStages*`.**

> **The prompt enhancer ships OFF, and the widget that says otherwise is dead.** `TextGenerateLTX2Prompt`'s `prompt_enhance` boolean is **`False`** in all three official templates, and the template's own note says "(Optional, **off by default**)". An inner `PrimitiveBoolean [True]` survives in the serialized JSON, but its `value` input is link-driven from the parent subgraph, so the outer `False` wins. If you want the enhancer, you must turn it **on**. Worth knowing before you do: it runs a separate Gemma 4 E2B, adds a minute or two, and can rewrite a hard prompt into something unrelated — *"with tougher prompts, I will get a completely random video. Turning off the prompt enhancer fixes the issue"* `[community — Hans-Wermhatt]`. Leave it off unless a prompt is deliberately thin.

> **Trace links before trusting any number pulled from one of these files.** Three widely-copied values are inert: the latent's `768, 512, 97`, the enhancer's `True`, and FLF2V's apparent `25`-versus-`24` frame-rate disagreement. That last one is not really a disagreement — both nodes read the *same* upstream `PrimitiveInt [24]`.

### VRAM, diffusers and hosting

**The vendor contradicts itself in the same week.** Documentation says **32 GB minimum, A100 80 GB / H100 recommended**; `ltx.io/llm-info` says 80 GB full, 32 GB distilled, "as little as 12GB"; the launch table says **16 GB** `[contested]`. Prefer the documentation figure — it is what `low_vram_loaders.py` is engineered to hit — and discount the marketing table specifically, since people running the hardware refuted its adjacent claims about competitors (see the suite table). Community measurement beats every vendor number on the distilled path: **0.5 MP × 10 s in 180 s on a 3060** `[community — rinkusonic]`. The reports do not form a clean VRAM curve. A 3050 with 4 GB completes 0.9 MP × 10 s, while a 4070 Ti with 12 GB fails at 0.3 MP past 10 s. That is because **clip length and decoder choice dominate card size**: the long run offloads and survives, while the short one holds a longer latent through a diffusion decode and does not. Read the table in the reference as pairs of (length, decoder, MP), not as a VRAM ranking. Levers in order: conv VAE; `VAEDecodeTiled`; enhancer off; skip stage 2 and raise base resolution `[community — 2legsRises]`; `--quantization fp8-cast`; `--offload cpu|disk`.

**diffusers support is unestablished.** `Lightricks/LTX-2.5-Diffusers` exists, but not which release loads it, the pipeline class, or whether audio decode is wired `[flagged — re-verify]`. Hosted, `api.ltx.io` and fal bill **per second of output**, **Pro tops out at 1080p and 10 s while Fast reaches 4K and 20 s**, and **Retake, Extend, Reframe and HDR-upscale are `ltx-2-3-pro` only**. Quant matrix, timings, multi-GPU, the megapixel and API duration tables, IC-LoRA wiring and LoRA stacking: [`references/setup-and-workflows.md`](references/setup-and-workflows.md).

---

## Per-mode settings

LTX has **no `shift` parameter.** The schedule is given as an explicit sigma list, so "steps" means the length of that list. Seeds behave conventionally (`--seed`, or the ComfyUI noise node), and nothing model-specific is documented there. Frame count, dimensions and fps are constrained by the lattice below and are the same across every mode.

### Distilled two-stage — T2V and I2V (the default)

| | Stage 1 | Stage 2 |
|---|---|---|
| Steps | **8** (sigma list) | **3** |
| CFG | **1** video, **1** audio | same |
| Sampler | `euler_ancestral` | `euler_ancestral` |
| Resolution | **640×368** latent — half the 0.9 MP output | **1280×736**, the delivered size |
| Negatives | **inert at CFG 1** — the shipped string does nothing | inert |
| LoRA weight | 0.5–1.5 for plain LoRAs; 0–1.0 for IC-LoRAs | same |

Anchor clip: **121 frames at 24 fps** (5 s), the shipped default. **Auto-duration and a fixed frame count are mutually exclusive.** `--auto-duration` works by *omitting* `--num-frames`, so the moment you pin a length for the lattice, you also give up letting the prompt set the duration — and shot balance becomes your problem (see the prompting guide's pacing note). Stage 2 is bypassable — on a low-VRAM rig, raise the base megapixels instead `[community — 2legsRises]`.

### Dev / full, guided two-stage — where CFG and negatives work

`TI2VidTwoStagesPipeline`, or `…HQPipeline` for a `res_2s` second-order sampler at fewer steps. This is the **undistilled** path: guidance is live, so the negative prompt does real work, and the docs' 1.0–1.5 advice does not apply — that band is a statement about the *distilled* model. Expect a different hardware class. The trainer's own validation of the full path runs **30 steps** with per-modality CFG and STG (block 28), which is a reasonable starting point.

### DFR — `DFRPipeline`, 2.5 only

Distilled sigmas on the full checkpoint with the distilled LoRA. Adds **generated keyframe slots** (+16% tokens for five at 512×768 × 241) and `--temporal-upsample-rounds {0,1,2}`, each doubling fps. **Audio is decided in stage 1 and never refined.**

### FLF2V and IC-LoRA V2V

FLF2V conditions with `LTXVAddGuide` at **strength 0.7** on both first and last frame, then `LTXVCropGuides`; keep both images at the same aspect ratio. IC-LoRA V2V runs the same 8+3 distilled schedule with the adapter loaded and its `attention_strength` in **0–1.0**, and requires the **distilled** model — `ICLoraPipeline` will not run on dev.

### Retake — `RetakePipeline`

Single-stage, and the only mode that edits a time region of an existing clip in place. **The source clip must already satisfy the lattice** — `docs/pipelines.md` §8 restates `8k+1` and multiples of 32 for this pipeline specifically — and `regenerate_video` and `regenerate_audio` are independent, so you can replace a passage's soundtrack without touching the picture. Sampling follows whichever base you run it on.

### A2V and audio-only

`A2VidPipelineTwoStage` freezes the audio branch and passes the original waveform through rather than re-decoding it, so audio settings do not apply; `T2AOneStagePipeline` runs the audio branch with no video at all.

---

## The default look, the smear, the skipped beat, and the locked-off camera

**The default look: clean, evenly lit, and slightly commercial.** Unsteered, LTX renders a well-exposed, low-contrast, broadly-lit frame closer to stock or promo footage than to a photographed moment — no grain, no lens character, no motivated key light unless you name one. **The direct evidence is thin, and that is worth saying**: nobody in the sweep put the grade into words. What you can observe is the *correction market* around it, the same signal [`krea-2`](../krea-2/) reads for its own default. The two most-downloaded LTX-2.3 style LoRAs exist to move the look: `LTX 2.3 - Enhancers` (vrgamedevgirl, 18k) and **`Amateur Hour - LTX 2.3`** (QualityControl, 5.4k) `[community — Civitai API 2026-08-22]`. Nobody downloads an "amateur" LoRA for a model that already looks amateur.

The lever is the one that also fixes the camera: **name the light logic and one non-idealised feature.** Give one coherent source ("a single practical over the counter", "hard midday sun through blinds") plus one thing that is not perfect. Reach for a corrective LoRA only after the prompt has failed, since on 2.3 that means inheriting Gate 4's obligations.

**Per-frame: smear.** This is the complaint that recurs most in the sweep — *"it's really bad, and makes almost every output of LTX completely unusable"* `[community — SillyLilithh]`. The first lever is the **diffusion video decoder**, which is what the release actually improved. The second is a community port of **jerk-oracle** nodes from a MiniMax H3 pack. As its author describes it, the oracle inserts extra "hold" frames in proportion to per-frame smearing, runs a further sampling step over them, then chops them off, leaving the original frame count with better inter-frame consistency. That is her account of her own node, not an independently reproduced mechanism — nobody had confirmed it within a day of release `[community — SillyLilithh; single report]`.

**Motion: the skipped beat.** A walk cycle drops a stride — the motion is continuous either side of it, and one beat is simply missing. The best explanation available is structural: the distilled model appears to buy its speed the way Easy Cache and Spectrum buy theirs, by skipping evaluations in the motion-generation phase `[community — V4nKw15h; single report]`. That mechanism is not unique to LTX. [`wan-2-2`](../wan-2-2/) reports the same *cause* on its 4-step speed LoRA, where distilling the expert that decides motion flattens dynamism — but the flattened-motion symptom Wan documents is not this dropped-stride one, so treat the shared mechanism as the link, not the artefact. Two levers follow. Run the **dev/undistilled** checkpoint and pay the speed back `[community — CurrentNew1039]`; or use **DFR keyframe slots**, the vendor's own mechanism for the same problem. Each appends a fully-denoised single-pixel-frame token that *relaxes the effective temporal compression at that position*, "useful where motion is too fast for the base temporal resolution", at +16% tokens for 5 slots at 512×768×241 `[official — docs/conditioning.md]`. (The Comfy template calls this "Pixel Diffusion"; ltx.io calls it Diffusion Fidelity Rendering.)

**Camera: it sits still.** LTX will not volunteer the handheld, suddenly-reframing camera that reads as real footage — *"essa câmera fixa do LTX é um grande problema"* `[community — corod58485jthovencom]`. The lever is prose: name the move, and describe **how the subject looks after it**. That is what lets the model complete the motion `[official — prompt guide]`.

---

## The lattice — frames, dimensions and fps

Four hard constraints, all of which fail *quietly*. Three of them follow from the VAE — **32× spatial, 8× temporal, 128 latent channels**, so `[B,3,F,H,W] → [B,128,1+(F-1)/8,H/32,W/32]`.

| Rule | Value | What goes wrong |
|---|---|---|
| **Frame count** | `8k + 1` | The tail is silently dropped; `DubItPipeline` snaps to the nearest legal value without saying so. One user lost 7 frames off every 240-frame clip, cutting the audio `[community — Cptcrocro]` |
| **Both dimensions** | multiple of **32**, applied to the **output** `[official]` | `ResolutionSelector` snaps the output; stage 1 then runs at half it and need not itself be a multiple of 32 (the 0.9 MP default gives a 640×368 stage-1 latent). Off-lattice output sizes are re-snapped without telling you |
| **Audio latent length** | must equal the video frame count | Change `EmptyLTXVLatentVideo`'s frame count and you must change `LTXVEmptyLatentAudio`'s to match. Mismatch does not error — it desyncs, and changing frame count is the first thing any reader does |
| **fps** | **24, 25, 48 or 50** only | Not 16, not 30 — and fps is set on `LTXVConditioning`, a *conditioning-time* value, as well as on `CreateVideo`. Set only the container and you get correct frames played at the wrong rate |

Frames are `fps × seconds + 1`, so whole seconds are free at 24 and 48 fps and constrained at 25 and 50. Two anchors: **121 frames = 5 s at 24 fps** (the template default), **241 = 10 s**. Worked values for all four rates: [`references/setup-and-workflows.md` §3](references/setup-and-workflows.md#3-resolution--the-megapixel-table).

Resolution comes from a **megapixel budget**, not W×H. Templates default to **1280×736 (0.9 MP)** at 16:9, built by halving to a 640×368 stage-1 latent and doubling back in stage 2.

> **The multiple-of-32 rule does not get you ReDetail's multiple-of-64 rule for free, and the stock default fails it.** ReDetail requires **both dimensions divisible by 64** in the clip you hand it `[community — DaLyon92x]`, and **736 = 64 × 11.5** — so the shipped 1280×736 default is rejected. If a clip is destined for ReDetail or any 64-aligned post stage, pick an output where both axes clear 64: **1280×704**, **1216×704**, **1920×1088**. Do not assume the template default qualifies. To pad up to the next legal frame count, duplicate the last frame and trim before the video combine `[community — Cptcrocro]`.

---

## Production pipelines & mixing models

The suite's video ladder runs **locked still → I2V → restore/upscale → interpolate → audio/finish**, and its ordering rule — **restore or upscale before you interpolate** — holds here too. [`image-production-workflows`](../image-production-workflows/) owns that rule and the cross-model craft behind it. What LTX changes is *whose* rungs they are: both of the last two are native here, so the question stops being where to put RIFE and becomes which flags to pass. Two LTX-specific consequences follow. `--temporal-upsample-rounds` is the interpolation stage, so it is the thing you defer rather than an external tool. And the detailing pass is **generative, not restorative**, which means it does not merely fail to remove interpolation smear — it will elaborate on it. These are the LTX rungs.

1. **Stage 1** — 8 steps, `euler_ancestral`, CFG 1, at half the target resolution. Composition, motion and (under DFR) *all* of the audio are decided here.
2. **Stage 2** — 2× latent upscale, then 3 steps. Bypassable, and worth bypassing on low-VRAM rigs in favour of a higher base resolution `[community — 2legsRises]`.
3. **DFR temporal rounds** — `--temporal-upsample-rounds {0,1,2}`, each doubling fps. The native alternative to RIFE.
4. **Detailing** — the Pixel Spatial Upscaler as `--detailing-lora`. **Two builds share that name**: `LTX-2.3-22b-IC-LoRA-Pixel-Spatial-Upscaler` (2× and 4×) and `LTX-2.5-22b-IC-LoRA-Pixel-Spatial-Upscaler`, the only 2.5-native adapter. DFR expects the 2.5 one. **Generative, not restorative**: it "synthesizes new detail rather than faithfully preserving the reference" and is "not suited to pixel-accurate restoration, blind denoising, or compression-artifact removal."

> **DFR does not refine audio.** "Stage 2 still runs an audio pass, because the video branch needs the cross-modal attention, but **nothing refines audio after stage 1**" `[official — docs/pipelines.md §12]`. If the sound is wrong, re-run from stage 1.

**A large share of real-world LTX-2.5 use is not generation — it is finishing someone else's clip.** In a one-month sweep of r/StableDiffusion and r/comfyui, four of the five most-upvoted high-scoring LTX posts were LTX upscaling or outpainting [`minimax-h3`](../minimax-h3/) output `[community — Cptcrocro, alisitskii, spiderofmars]`. **ReDetail** (`Bambushu/redetail`) is the packaged form, and [`image-production-workflows`](../image-production-workflows/) already documents its constraints: the lattice rules above, plus a silence track on silent input, plus 1.5× preferred over 2× because "on skin most of that extra is invented, not recovered" `[community — DaLyon92x]`.

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| **OOM after sampling completes, at decode** | The diffusion decoder runs iterative Euler denoising in pixel space over the whole clip, so peak memory arrives after the transformer is done | Conv VAE, or wire `VAEDecodeTiled` |
| **Clip shorter than requested; audio cut off at the end** | Frame count off the `8k + 1` lattice — the tail is dropped, not rejected | Recompute from the fps table; pad by duplicating the last frame, trim after combine |
| **A silent input clip fails outright** | Audio and video are encoded jointly; there is no video-only path through the sequence | Add a silence track before any V2V or upscale run |
| Negative prompt visibly does nothing | `LTXVDualCFGGuider [1, 1]`; at scale 1 conditional and unconditional collapse together | Expected. Use the dev checkpoint with `TI2VidTwoStages*` |
| Raising CFG made it worse *and* slower | Guidance is baked into the distillation, so extra CFG adds overhead without steering | Stay 1.0–1.5; change the prompt instead |
| **Output unrelated to a hard prompt, or generation takes 20+ minutes** | The Gemma 4 E2B enhancer is rewriting the prompt and thrashing VRAM — but only if *you* enabled it, since the templates ship it off | Turn it back off; then check your prompt against the register in the prompting guide |
| Smearing through motion | Distilled schedule plus the conv decoder's single deterministic pass | Diffusion decoder; or the jerk-oracle hold-frame nodes |
| A walk or run drops a stride | Step-skipping in the distilled sampling of the motion phase | DFR keyframe slots at the fast passage, or the dev checkpoint |
| Camera stays locked off | An unstated camera is *unspecified*, not neutral, and the model's prior for unspecified is a locked tripod — it will not infer handheld motion from an energetic subject | Name the move *and* how the subject appears after it |
| Identity changes at a cut | Multishot re-anchors identity from the *text* at each cut, not a persistent embedding | Repeat one visual identifier at every cut; keep to **2–4 shots** (one to three cuts) |
| I2V output cuts away from your reference image | A multishot prompt on an I2V run — the two pull against each other by design | Single continuous take for I2V unless the cut is deliberate |
| On-screen text misspelled or unstable across frames | Vendor-acknowledged: spelling and cross-frame consistency "are not guaranteed" | Keep text short; add critical titles in post |
| Nodes missing from the Template Library | The 2.5 templates may require ComfyUI **nightly** | Update; confirm `ComfyUI-LTXVideo` is on `master` `[flagged — re-verify]` |

Errors that fail *loudly* — a stock Gemma 4 rejected by the version check, a 2.3 monolith mixed with 2.5 split files, NATTEN illegal memory access on an old CUDA stack — are covered in [`references/setup-and-workflows.md`](references/setup-and-workflows.md).

---

## Pre-flight checklist

1. **Licence settled** — under $10M aggregated revenue, **not building something that competes with Lightricks' commercial products or services** (¶20 — unqualified, no revenue floor), work is not sexually explicit, output disclosed as machine-generated, and any LoRA you train inherits the licence?
2. **Version chosen deliberately** — 2.5 for multishot, the diffusion decoder and keyframe slots; 2.3 for the adapter and LoRA ecosystem, accepting that its governing licence text is unsettled?
3. Downloaded the **2.5 encoder**, not a stock Gemma 4, and not mixed split files with a 2.3 monolith?
4. **Both VAEs present** — video *and* audio — with the decoder chosen on purpose (conv unless you have headroom to spare; the diffusion decoder is the documented OOM at decode on 12–16 GB cards)?
5. **Prompt enhancer off** for the first run, so adherence and timing are yours and not the enhancer's?
6. Frame count on the **`8k + 1`** lattice, dimensions multiples of **32**, fps in **{24, 25, 48, 50}** and set on `LTXVConditioning` as well as `CreateVideo`?
7. Prompt is **one chronological present-tense paragraph** under ~200 words, with the audio described?
8. If multishot: **2–4 shots — one to three cuts**, each cut naming the transition, re-establishing the shot, re-identifying the subject and stating audio continuity — and you are *not* also running I2V?
9. Accepted that at CFG 1 the shipped negative prompt is inert, and stayed in the 1.0–1.5 band?
10. Post chain ordered **restore/upscale before interpolate**, knowing the detailing upscaler invents detail — and any input clip for a V2V or upscale run **has an audio track**, even if it is silence?

---

## Where LTX-2.5 sits in the suite

| Job | LTX-2.5 | Reach for instead |
|---|---|---|
| **Several connected shots in one generation** | **The reason to be here.** Nothing else in the suite cuts inside a single pass | — |
| Locking a still first | Not an image model | [`z-image`](../z-image/) / [`flux-2`](../flux-2/) / [`krea-2`](../krea-2/) / [`sdxl`](../sdxl/), then I2V |
| **Audio** | **Generates *and* consumes** — joint 24 kHz stereo, A2V with frozen audio, V2A foley with frozen video | [`minimax-h3`](../minimax-h3/) generates only (and excludes US/EU/UK/KR); [`wan-2-2`](../wan-2-2/) S2V consumes only |
| Motion, camera and pose control rigs | **A real rig, and reference-plus-mask rather than ControlNet-shaped.** IC-LoRAs cover depth, canny, pose, motion tracks and in/outpainting from a reference input with an optional mask. But most are 2.3-trained, only one adapter is 2.5-native, and the camera-move LoRAs are LTX-2-era | [`wan-2-2`](../wan-2-2/) — Fun Camera / Fun Control / VACE: deeper, better documented, and the only explicit **camera** rig in the suite |
| **Exact motion transfer or character replacement** | ❌ **No reference-to-video mode at all** — the most-cited reason practitioners stay on H3: *"multishot is awesome but unfortunately need to stick with H3 for native references"* `[community — rk1213]` | **SCAIL-2** ([`scail-2`](../scail-2/)) for frame-accurate replacement; [`minimax-h3`](../minimax-h3/) Ref2VA for an approximate swap with audio |
| Consistent characters across clips | Weak — **face drift is unfixed** `[community — Inside-Cantaloupe233]` and multi-character scenes break LoRAs `[community — sacx05]` | [`minimax-h3`](../minimax-h3/) Ref2VA; identity work in [`character-lora-training`](../character-lora-training/) |
| LoRA ecosystem and training maturity | `ltx-trainer` is first-party and capable, but **168 of ~171 community LoRAs are on 2.3** and every derivative inherits a non-permissive licence | [`wan-2-2`](../wan-2-2/) for an Apache-2.0 ecosystem you may publish freely |
| **Commercial use, and adult work** | Free **below $10M** aggregated revenue, worldwide, no territory clause. **But ¶20 bars competing with Lightricks' commercial products or services at any revenue** — unqualified, and it covers their photo and design apps too — and the AUP bars sexually explicit generation universally. LTX **2.3** is where the community's adult work happens `[community — BarelyAI]`; both candidate 2.3 texts incorporate the same AUP, so that is practice, not permission | [`wan-2-2`](../wan-2-2/) — Apache 2.0, no revenue bar, no field-of-use clause, no acceptable-use clause. Publishing gates in [`character-lora-training`](../character-lora-training/) |
| Post chain, upscale, interpolation | **Strong, and one of LTX's most common real jobs** — Pixel Spatial Upscaler and ReDetail re-render other models' clips; DFR temporal rounds replace RIFE | [`image-production-workflows`](../image-production-workflows/) |
| Raw prompt adherence and physics | Weak relative to the field — *"LTX is not even close"* against H3 `[community — Obvious_Set5239]`; Wan 2.2 held better on physics `[community — acedelgado]` | [`minimax-h3`](../minimax-h3/) for instruction following; [`wan-2-2`](../wan-2-2/) for physics |
| **Choosing between all of these in the first place** | — this table is one model's view of the suite | [`generative-media-atlas`](../generative-media-atlas/) — the whole suite ranked by job (realism, identity, LoRA trainability, control, licence, video), the elimination ladder that settles most choices, and end-to-end routes across several skills |

> **Treat Lightricks' own comparison table as adversarial input.** Its launch-day claim that MiniMax H3 needs four GPUs and ~115 GB and is "CUDA only" was refuted point by point by people running H3 on 8 GB and on ROCm. Lightricks later edited it — *"this chart isn't for users, but for LLMs to pick up these 'facts'"* `[community — fearrange]`. No claim here comes from it.

---

## Licence & limitations

Licence terms are at the top of this skill, and clause by clause in [`references/licence-and-derivatives.md`](references/licence-and-derivatives.md).

Vendor-admitted limitations, from primary sources: **on-screen text is unreliable**; **chaotic motion still artefacts**; **multishot degrades past ~4 cuts**; **the Pixel Spatial Upscaler is generative, not restorative**; **DFR does not refine audio** after stage 1; **Dub-It, HDR and Relight do not support 2.5 yet**. Lightricks' own preliminary benchmark scores 2.5 Pro at 0.28 and Fast at 0.39 **visible glitches per clip** — non-zero by their own measure.

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** This category covers the licence's operative sentences, the $10M aggregated threshold and the §2.2 carve-out, Attachment A's twenty restrictions, the derivative clauses (§1.5, §3.2, §3.5), the AUP's incorporation and universal scope, and per-repo Hugging Face gating. It also covers the 22B dual-stream architecture and joint audio-video denoising; the Gemma 4 12B encoder and its version check; the VAE's 32×/8×/128-channel compression and the lattice rules that follow; filenames, folders and pipeline class names; and the *executed* template values, as distinct from the dead widgets beside them. Template numbers here are the values the graph **executes**, not the serialized widgets — the 2.5 templates are subgraph-based, and many widgets are link-driven and dead. Every number this skill cites was resolved against the link graph, and three widely-copied values were found inert. That pass did not cover the whole file, so resolve links yourself before quoting a number from one of these templates. **The source of truth is official, and every licence claim was independently re-verified against raw text**: both `LICENSE` files pulled raw and read in full, the AUP PDF downloaded and read in full, the commit history for both, `packages/ltx-core/README.md`, the `ltx-pipelines` docs, `MODELS-LTX-2.3.md`, the Hugging Face API, and the `example_workflows/2.5/` and `video_ltx2_5_*` JSON read verbatim. A wrong filename 404s; a misread licence is a legal problem. These facts are also the **volatile** ones — the model is eleven days old, and quant builds, template details and the ComfyUI stable-versus-nightly position all move weekly. **Re-verify before relying on them, regardless of who said it.**

**Craft — what actually makes a good clip.** This covers the decoder-choice-as-OOM-fix, the prompt-enhancer traps, the measured VRAM figures, the smear diagnosis and the jerk-oracle fix, the step-skipping theory behind the missed motion beat, the frame-padding recipe, the low-VRAM ordering, the V2V workflow pick, the identity findings, and the positioning verdicts against H3 and Wan. **The authoritative source here is the community** — named authors on r/StableDiffusion and r/comfyui and in shipped repos: `DaLyon92x` (ReDetail, lattice), `SillyLilithh` (jerk-oracle), `irmemon225` and `matik802` (decoder OOM), `rinkusonic` and `intLeon` (timings), `Cptcrocro` (frame padding), `Hans-Wermhatt` (the enhancer), `Interesting_Room2820` (V2V), `Comfortable-You-3881` (2.3-vs-2.5), `V4nKw15h` (step-skipping), `rk1213` and `sacx05` (identity), `acedelgado` (versus Wan). These are stated with confidence. A range means "your card, resolution and clip length differ from theirs," not "unreliable." **But this model is eleven days old, and its community body is correspondingly thin** — several findings above are single reports nobody has reproduced, and are marked as such.

Points held as unresolved. **Each bullet is one thing to go and check, not one claim.** Questions the same source will settle on the same day are bundled, and each carries a single marker.

- **The licence-resolution question**, one event with three faces: which text governs **LTX-2.3** (the repo ships the January agreement, both of its own links point at the August one, §1.9 scopes the August text to 2.5 and later); whether **¶18's no-training rule** is commercial-only as ¶18 says or unconditional as the AUP says; and the **paid agreement's terms**, email-only with no published schedule — which is also where the in-repo-`LICENSE` question gets answered `[contested]`
- Whether **2.5 output embeds a watermark**: the licence protects one and can revoke on suspicion of stripping it, but nothing documents one `[flagged — re-verify]`
- Whether a **2.3-trained LoRA works on 2.5** — the README says no, Lightricks' own 2.5 workflows say yes `[contested]`
- The **VRAM floor**: 32 GB documentation against 16 GB and 12 GB marketing, same vendor, same week, with the marketing table publicly refuted in a 362-comment thread `[contested]`
- Whether **multishot holds identity** — one positive report, one documented 2.3 failure, no side-by-side — and, resolving with it, **where in a shot a quoted line lands** and what two dialogue-carrying shots do `[contested]`
- **Apple Metal and AMD ROCm** support, and vendor-claimed **real-time streaming** that nobody has reproduced `[contested]`
- **What ships next locally**: no `ExtendPipeline` (the endpoint is `ltx-2-3-pro` only), **diffusers** unestablished as to release, pipeline class and audio decode, no `ltx-2.5-pro` on Replicate `[flagged — re-verify]`
- **The IC-LoRA lineup, mid-migration**: one 2.5-native adapter, HDR / Dub-It / Relight still 2.3-only, the camera-control LoRAs advertised for 2.5 but hosted on the superseded LTX-2, and the headline **Video Editing IC-LoRA** reachable only through the API `[pending release]`
- **The three 2.3 numbers this skill cannot give you**: the monolith filename, the Template Library entry name, and 2.3's sigma list, step count and CFG `[flagged — re-verify]`
- Whether the 2.5 templates need ComfyUI **nightly** rather than stable, and the **enhancer model's on-disk size** (~5 GB by docs.comfy.org against ~10 GB by the template's own note) `[contested]`
- **The training unknowns**, which will resolve together on the first named 2.5 write-up with numbers in it: no rank/alpha/LR/step recipe, no answer on whether 2.5's post-training changes training behaviour, no training VRAM figure, and whether **2.5 changed the VAE compression factors** now that the trainer reads them from metadata `[flagged — re-verify]`
- Whether **2.5 beats 2.3** at all or only at I2V, while the ecosystem stays on 2.3 — 1.58M downloads against 695k, 168 Civitai LoRAs against 3 `[contested]`

**Settled since drafting, and deliberately no longer flagged.** The enhancer's ship state and the FLF2V "fps mismatch" were resolved against the template link graph and are stated as fact above. **How the 22B divides** between the streams is unpublished and not watched. The opening paragraph records it as a thing not to assume, which is all a reader can do with it.

**Facts dated 2026-08-22.** The licence text, the template JSON numbers and the file list move fastest. The 2.3 licence question and the IC-LoRA version story are the two most likely to resolve — or to be quietly changed — within a month.

---

## Reference files

| File | When to read it |
|---|---|
| [`references/prompting-guide.md`](references/prompting-guide.md) | Writing any LTX prompt, and above all a **multishot** one — the four per-cut rules, a worked prompt *and* a diagnosed failure, pacing shots inside a fixed length, **§12's composed multishot-plus-consistent-character path**, dialogue and Dub-It templates, vocabulary, and the mistakes that cost adherence |
| [`references/setup-and-workflows.md`](references/setup-and-workflows.md) | Building or debugging the graph: stage 1 and 2 node by node, megapixel and API duration tables, the quant/VRAM matrix and multi-GPU, the IC-LoRA inventory and wiring, **loading and stacking LoRAs**, the CLI, and hosted surfaces |
| [`references/lora-training.md`](references/lora-training.md) | **Making** a LoRA or IC-LoRA with `ltx-trainer` — the unified mode config, dataset and clip-length choices, audio-branch LoRAs, validation defaults, and the licence-inheritance trap that decides whether you can publish it |
| [`references/characters.md`](references/characters.md) | Holding a person steady across frames, and the harder problem of holding them across a cut — path selection with no ref2vid mode, the Ingredients reference-sheet protocol, and honest routing when LTX is the wrong tool |
| [`references/licence-and-derivatives.md`](references/licence-and-derivatives.md) | Clause by clause: the revenue threshold and aggregation, the §2.2 carve-out, Attachment A's twenty restrictions, derivative redistribution and the transferee duty, the AUP, output duties, watermark revocation, and the unsettled 2.3 question |
