# LTX-2.5 — primary-source research

**Gathered 2026-08-22.** Every hard fact below carries a URL. `[inferred]` = my derivation, not read.
`[contested]` = primary sources disagree. Unestablished facts are under **Could not verify**, not
papered over.

Community/Reddit/Civitai research is a *separate* pass — this file is vendor + ComfyUI primary only.

---

## Licence

### Verdict in one line

**LTX-2.5 is NOT Apache-2.0.** It ships under the **LTX-2.x Community License Agreement** (dated
11 August 2026), a bespoke Lightricks licence that is *worldwide and territory-unrestricted*, permits
commercial use free of charge **only for entities under $10,000,000 annual revenue**, requires all
derivatives (including LoRAs) to be redistributed under the same licence, and incorporates
Lightricks' **Acceptable Use Policy — which prohibits sexually explicit content** — by reference.

**The licence text is fully public and I read it in full.** The Hugging Face *weights* are gated;
the *licence* is not. This corrects the claim in `minimax-h3`.

### Where the text lives

| Which | URL | Read? |
|---|---|---|
| LTX-2.x Community License Agreement (governs **LTX-2.5**) | https://github.com/Lightricks/LTX-2/blob/main/LICENSE.md — raw: https://raw.githubusercontent.com/Lightricks/LTX-2/main/LICENSE.md | ✅ full text, 30,938 bytes |
| LTX-2 Community License Agreement (ships with **LTX-2.3**) | https://huggingface.co/Lightricks/LTX-2.3/raw/main/LICENSE | ✅ full text, 21,399 bytes |
| Acceptable Use Policy (incorporated by reference into **both**) | https://static.lightricks.com/legal/ltx-acceptable-use-policy.pdf (Last Updated: March 30, 2026) | ✅ full text, 5 pages |
| Vendor summary page | https://ltx.io/model/license | not fetched (redirect/JS); the GitHub text is authoritative |

**Two different licences are in play**, and this matters for a skill covering both versions:

- **LTX-2.5** → "LTX-2.x Community License Agreement", *License date: August 11, 2026*.
  §1.9: "This license is applicable to all LTX-2.5 versions released since August 11, 2026, and all
  future releases of LTX-2.x under this license."
- **LTX-2.3** → the older "LTX-2 Community License Agreement", *License date: January 5, 2026*.
  Same $10M threshold, but materially harsher in one respect and looser in another (below).

Hugging Face labels both repos `license: other`, `license_name: ltx-2-community-license-agreement`
(https://huggingface.co/api/models/Lightricks/LTX-2.5 and `/LTX-2.3`) — the HF label does **not**
distinguish the two texts. `[trap]`

### Is it gated on Hugging Face?

| Repo | `gated` field | Consequence |
|---|---|---|
| `Lightricks/LTX-2.5` | **`auto`** | Must be logged in, accept terms, share contact info + consent to Privacy Policy. Auto-approved. |
| `Lightricks/LTX-2.5-Pre-Trained` | `auto` | same |
| `Lightricks/LTX-2.5-Diffusers` | `auto` | same |
| `Lightricks/LTX-2.3` | **`false`** | **Not gated.** Open download. |
| All `Lightricks/LTX-2.3-22b-IC-LoRA-*` | not gated | open |

Source: HF API, e.g. `curl https://huggingface.co/api/models/Lightricks/LTX-2.5` → `"gated":"auto"`.
Corroborated by the repo README: "If you get a 401/403, accept the model terms on Hugging Face and
log in with a **Read** token (fine-grained tokens need the 'read gated repos' scope enabled)"
(https://github.com/Lightricks/LTX-2 README). ComfyUI's own docs repeat it: "Model downloads will
fail without access" (https://docs.comfy.org/tutorials/video/ltx/ltx-2-5).

So: **the gate is on the weights, not on the terms.** Anyone can read the licence without an account.

### Commercial use — the operative sentence, verbatim

From §2.1 of the LTX-2.x agreement (bold in original):

> "…you are granted a non-exclusive, worldwide, non-transferable and royalty-free limited license
> under Licensor's intellectual property or other rights owned by Licensor embodied in LTX-2.x to
> use, reproduce, prepare, distribute, publicly display, publicly perform, sublicense, copy, create
> derivative works of, and make modifications to LTX-2.x, for any purpose, subject to the
> restrictions set forth in Attachment A; **provided however, that Entities with annual revenues of
> at least $10,000,000 (the "Commercial Entities") are required to obtain a paid license for any use
> (excluding use solely for a Non-Commercial Purpose as set forth in Section 2.2) of LTX-2.x and
> Derivatives of LTX-2.x**…"

Contact for the paid licence: `ltxv-licensing@lightricks.com` (linked in §2.1).

**Threshold is aggregated across corporate groups.** §1.6: "an Entity shall be deemed to include, on
an aggregative basis, all subsidiaries, affiliates, and other companies under common Control with
such Entity. When determining whether an Entity meets any threshold under this Agreement (including
revenue thresholds in Section 2.1), all subsidiaries, affiliates, and companies under common Control
shall be considered collectively."

**Breach remedy (2.5):** unpaid fees for the period of use, at "Licensor's standard commercial
license fees… or, absent published standard fees, a reasonable market rate", payable within 30 days
of written demand.

**Breach remedy (2.3's older licence) is worse:** "liquidated damages… in an amount equal to **double
the amount** that would otherwise have been paid by you for the relevant period of time." The 2.5
licence dropped the doubling. `[LTX-2.3 LICENSE §2]`

**The 2.5 licence *added* a non-commercial carve-out the 2.3 one lacks.** §2.2 lets a ≥$10M entity
use the model without a paid licence "solely for a Non-Commercial Purpose" — defined as personal
hobby/research use, or "use by a Commercial Entity for testing, evaluation, or non-commercial
research and development in a non-production or development environment", provided no direct or
indirect payment arises. Explicitly excluded from that carve-out: revenue-generating activity,
anything with end-user impact, and training/fine-tuning/distilling any model for commercial use.

### Outputs

**You own your outputs.** §5, verbatim:

> "Except as set forth herein, Licensor claims no rights in the Output you generate using LTX-2.x.
> You are accountable for input you insert into LTX-2.x, the Output you generate and its subsequent
> uses. No use of the Output can contravene any provision as stated in the Agreement."

No branding/attribution requirement on outputs anywhere in the text. (Vendor markets this: "No
mandatory branding — Available" vs MiniMax H3 "Must display 'MiniMax H3'",
https://ltx.io/model/ltx-2-5.)

### NSFW — prohibited

Attachment A opens: "you agree to comply with the [Acceptable Use Policy] which is hereby
**incorporated into and made part of this Agreement by reference**." The AUP is a living document —
"Licensor may update it from time to time, and the version in effect at the time of your use
governs" (Attachment A) — though "no update shall apply retroactively to use occurring before that
effective date."

The AUP (2026-03-30) contains a section headed **"Do Not Generate Sexually Explicit Content"**:

> "This includes using our Products to: Depict or request sexual intercourse or sex acts; Generate
> content related to sexual fetishes or fantasies; Facilitate, promote, or depict incest or
> bestiality; Engage in erotic chats"

This is the sharpest practical difference from Wan 2.2. **A skill that treats LTX as an
NSFW-capable open model would be wrong on the licence.** Note the AUP is written for Lightricks'
hosted "Products" (it talks about accounts and API keys) but Attachment A pulls it wholesale into
the weights licence with no carve-out for local use. `[the AUP's product-framing vs its
incorporation into the weights licence is a real ambiguity — flag it, don't resolve it]`

The AUP also carries a **likeness clause** worth surfacing:

> "Where content from our Products is used commercially, users must assume responsibility for
> ensuring it does not replicate any real-world likeness, person, brand, or location unless
> independently cleared."

And Attachment A item 7 bans using the model "To impersonate or attempt to impersonate (e.g.
deepfakes) others without their consent." This is the LTX analogue of the Civitai real-person ban
already tracked in `character-lora-training`.

### Training derivatives and LoRAs

- **LoRAs are Derivatives.** §1.5 defines "Derivatives of LTX-2.x" to include "(i) any fine-tuned or
  adapted weights, parameters, or checkpoints derived from LTX-2.x"; §3.5 names "any fine-tuned
  weights, LoRA adapters, or similar adaptations" explicitly.
- **Copyleft-ish redistribution.** §3.2: "Any Derivative of LTX-2.x … must be distributed
  **exclusively under the terms of this Agreement**, subject to Section 3.6, with a complete copy of
  this Agreement included."
- **The $10M obligation travels with the LoRA.** §3.5: "If the transferee is a Commercial Entity …
  it must obtain a paid license from Licensor prior to any use of any Derivative of LTX-2.x,
  **regardless of who created such Derivative**." You must notify the transferee in writing, and
  "You shall not transfer any Derivative of LTX-2.x to a Commercial Entity unless such Commercial
  Entity has obtained the required paid license."
- **No training competitors — but only for commercial users.** Attachment A item 18: "**For
  commercial use only:** To train, improve, or fine-tune any other machine learning model,
  artificial intelligence system, or competing model, except for Derivatives of LTX-2.x as expressly
  permitted under this Agreement." Item 20 separately bans deploying LTX in "any product, service,
  or application that directly competes with Licensor's commercial products or services."
- Note the tension with §2.2's exclusion: for a ≥$10M entity, using LTX to "train, fine-tune, or
  distill any model … for commercial use" is not a Non-Commercial Purpose and needs the paid licence.

### Redistribution of weights

Permitted, including SaaS hosting — §3: "You may host for third parties remote access purposes
(e.g. software-as-a-service), reproduce and distribute copies of LTX-2.x or Derivatives of LTX-2.x
thereof in any medium, with or without modifications" — conditional on: passing through §4 +
Attachment A as enforceable terms (§3.1), shipping a complete copy of the Agreement (§3.2), marking
modified files (§3.3), retaining notices (§3.4).

### Other clauses a skill reader should know

- **Watermark / provenance tampering revokes the licence.** §6: you "shall not remove, disable,
  alter, or circumvent, any safety or security measures, disclosures, metadata, watermarking,
  content provenance, latent disclosure, or other transparency features"; if Lightricks believes you
  have, it "may in its sole discretion **revoke the license** … effective immediately upon notice."
  Attachment A item 19 repeats it. **Whether LTX-2.5 output actually carries a latent watermark is
  unverified** — see Could not verify.
- **EU AI Act positioning.** §6: Lightricks "intends that LTX-2.x be treated as a free and
  open-source general purpose AI model within the meaning of Article 53(2) of the EU AI Act", and
  pushes high-risk-system provider obligations onto you.
- **Export controls / OFAC** (§7): you warrant you are not in a comprehensively sanctioned territory
  or on a restricted-party list. This is the closest thing to a territory clause and it is *far*
  narrower than MiniMax H3's.
- **Governing law:** New York (§12). **ICC arbitration, seat New York, jury-trial and class-action
  waiver** (§14) — with an explicit carve-out preserving mandatory consumer-protection rights in the
  EU, UK and California.
- **Patent retaliation** (§13): suing Lightricks over LTX-2.x or its Output terminates your licence.
- **Termination** (§13) requires you to delete all copies of the model *and derivatives* and notify
  downstream recipients.
- **"Use the latest version"** (§6): "You shall undertake reasonable efforts to use the latest
  version of LTX-2.x. Any use of the non-current version of LTX-2.x is done solely at your risk."
  Soft, but it exists — and it is a small argument against pinning 2.3 forever.

### Comparison against the suite's other video licences

| | **LTX-2.5** | **Wan 2.2** | **MiniMax H3** |
|---|---|---|---|
| Licence | LTX-2.x Community License (bespoke) | Apache 2.0 | MiniMax H3 Community License |
| Territory | **Worldwide** (minus OFAC-sanctioned) | Worldwide | **Excludes US, EU, UK, South Korea** |
| Commercial use | Free **under $10M annual revenue**; paid licence above | Free, unconditional | per that skill |
| HF gate | **Yes** (`auto`) on 2.5; **no** on 2.3 | No | per that skill |
| Derivatives | Must ship under the same licence; $10M obligation follows the LoRA to its recipient | Apache — do anything | per that skill |
| NSFW | **Prohibited** via incorporated AUP | No restriction in Apache | per that skill |
| Output rights | Yours; no branding requirement | Yours | H3 requires displaying "MiniMax H3" per LTX's own comparison table (second-hand, verify in `minimax-h3`) |
| Anti-competition | Yes (Attachment A 18, 20) | No | per that skill |

**Practical read for the skill:** LTX-2.5 is the *territorially* safest open video model in the suite
— it is usable in the US/EU/UK where H3 is not — but it is *not* a permissive licence. It sits
between Apache Wan and territory-locked H3: fine for indies, studios and agencies under $10M;
requires a phone call above that; and closed to NSFW work in a way Wan is not.

---

## Architecture

Primary: `packages/ltx-core/README.md`
(https://raw.githubusercontent.com/Lightricks/LTX-2/main/packages/ltx-core/README.md), the LTX-2
technical report (https://arxiv.org/abs/2601.03233), and https://ltx.io/llm-info.

**Family shape.** "LTX-2 is an **asymmetric dual-stream diffusion transformer** that jointly models
the text-conditioned distribution of video and audio signals, capturing true joint dependencies
(unlike sequential T2V→V2A pipelines)." (ltx-core README)

| Fact | Value | Source |
|---|---|---|
| Class | DiT — asymmetric dual-stream, 48 transformer blocks shared by both streams, differing in width | ltx-core README |
| Params, **LTX-2 (19B)** | 14B video stream + 5B audio stream | arXiv 2601.03233 abstract |
| Params, **LTX-2.3 / LTX-2.5** | **22B** | https://ltx.io/llm-info |
| 2.5 per-stream split | not published | see Could not verify |
| Positional encoding | 3D RoPE (x,y,t) on video; 1D temporal RoPE on audio | ltx-core README |
| Cross-modal coupling | bidirectional A↔V cross-attention with 1D temporal RoPE ("enables sub-frame alignment, mapping visual cues to auditory events (lip-sync, foley, environmental acoustics)") + **cross-modality AdaLN** ("Scaling/shift parameters conditioned on the other modality's hidden states for synchronization across differing diffusion timesteps/temporal resolutions") | ltx-core README |
| Guidance | modality-aware CFG (modality-CFG) + STG (Spatio-Temporal Guidance) via block perturbation | arXiv abstract; ltx-core README; `docs/multimodal-guidance.md` |

**Text encoder — the 2.3 → 2.5 break.**

- **LTX-2.5: a custom Gemma 4 12B** with the text projection bundled into one file
  (`gemma4-12b-with-proj-ltx-2.5-bf16.safetensors`). The README is emphatic: "Google's stock Gemma 4
  release is **not a substitute**: loading checks the encoder's version against the one the
  checkpoint was trained with (`gemma4-12b-ltx-v1`)."
- **LTX-2.3: Gemma 3 12B**, downloaded separately from
  `google/gemma-3-12b-it-qat-q4_0-unquantized`; the text projection is bundled inside the monolithic
  2.3 checkpoint. (MODELS-LTX-2.3.md; ComfyUI-LTXVideo README)
- **Separate optional prompt-enhancer model**: `gemma4_e2b_it_bf16.safetensors` (Gemma 4 E2B). Comfy
  int8 build lives at `Comfy-Org/gemma-4`.
- So the encoder class is **LLM-class (decoder-LM) conditioning, not T5 and not CLIP** — LTX-2.5 sits
  with the Qwen/Gemma-conditioned models on the prompt-dialect axis, and the practical consequence
  is that it wants natural, chronological prose, not tag soup.
- LTX-2.0's paper describes only "a multilingual text encoder" (arXiv abstract) — the Gemma naming
  is from the repo. Both are primary.

**Video VAE.** (ltx-core README, "Video VAE" section)

- Encoder: `[B, 3, F, H, W]` → `[B, 128, F', H/32, W/32]`, where `F' = 1 + (F-1)/8` and "frame count
  must satisfy `(F-1) % 8 == 0`". Worked example given: `[B,3,33,512,512]` → `[B,128,5,16,16]`.
- **Compression: 32× spatial, 8× temporal, 128 latent channels.** That is a per-voxel compression of
  3·(32·32·8)/128 = **192:1** `[inferred from the stated shapes]` — the same 1:192 headline LTX has
  carried since 0.9.x.
- **Two decoders ship, and the choice is a real quality/VRAM lever:**
  - `ltx-2.5-video-vae-conv-bf16.safetensors` — `ConvVideoDecoder`, single deterministic forward
    pass. "lighter and needs no extra dependencies."
  - `ltx-2.5-video-vae-bf16.safetensors` — **`DiffusionVideoDecoder` (the "Diffusion Video
    Decoder")**, a neighborhood-attention decoder that "iteratively denoises pixels via Euler steps
    (`default_num_inference_steps=2` for distilled) instead of a single deterministic pass."
    "improved quality at the cost of longer decode time and more VRAM." Fastest with the `natten`
    extra (Linux+CUDA only; Triton/eager fallback elsewhere).
  - Selection is automatic from the checkpoint's `vae._class_name`.
  - This is **the** headline 2.5 quality change: "sharper faces in close-up, more legible text and
    signage, and fewer smears in fast motion" (https://ltx.io/llm-info).

**Audio.** LTX generates audio; it does not merely consume it — and it can do both.

- Separate **Audio VAE**: encoder `[B, mel_bins, T] → [B, 8, T/4, 16]` (4× temporal downsampling,
  8 channels, 16 mel bins, ~1/25 s per token); native stereo via channel concatenation of
  two-channel 16 kHz mel-spectrograms.
- **Vocoder**: HiFi-GAN-based, "modified for stereo synthesis and upsampling (16 kHz mel → **24 kHz
  waveform**, doubled generator capacity for stereo)".
- Audio and video are **jointly denoised in one pass** — not a post-hoc V2A stage. llm-info: "LTX
  produces temporally synchronized 24 kHz stereo audio jointly with video."
- The design rationale is explicit: "**Decoupled Latent Representations**: Separate modality-specific
  VAEs enable 3D RoPE (video) vs 1D RoPE (audio), independent compression optimization, and **native
  V2A/A2V editing workflows**" (ltx-core README). That is why audio-only (T2A), video-only (foley),
  and frozen-modality modes all exist.

**Diffusion Fidelity Rendering (DFR) — marketing vs mechanism.** The vendor line is "a new video
generation technology that allocates rendering compute by scene complexity"
(https://ltx.io/model/ltx-2-5). The repo's mechanism is more specific and more useful:

- `DFRPipeline` runs the distilled sigma schedule **on the full checkpoint with the distilled LoRA**.
  Stage 1 generates at half resolution *plus* **generated keyframe slots** on an 8-frame-border
  segment grid; stage 2 re-denoises at full resolution with the distilled LoRA and an optional 2×
  spatial detailing IC-LoRA, conditioned on the stage-1 reference. (`docs/pipelines.md` §12)
- **Generated keyframe slots** are the actual "compute by complexity" mechanism: "Each slot is an
  empty, fully-denoised token slot appended to the sequence; because a slot carries a single pixel
  frame rather than the eight a normal latent frame carries, **it relaxes the effective temporal
  compression at that position** — useful where motion is too fast for the base temporal
  resolution." Cost: "At 512x768 / 241 frames, 5 keyframes is about +16% tokens (~1.35x attention
  cost); at 1088x1920 / 121 frames it is about +31% (~1.72x)." Requires
  `use_keyframes_abs_pos_embedding` in the transformer config — **LTX-2.5 only**; on 2.3 "the
  pipeline raises rather than silently ignoring the request." (`docs/conditioning.md`)
- Audio in DFR comes from **stage 1 only**: "Stage 2 still runs an audio pass, because the video
  branch needs the cross-modal attention, but nothing refines audio after stage 1."
  (`docs/pipelines.md` §12) — a real gotcha.

**Naming inconsistency worth noting:** the ComfyUI T2V template's own note calls the same feature
"**Pixel Diffusion**: keyframes-first generation…" while docs.comfy.org and ltx.io call it
"Diffusion Fidelity Rendering". Same thing. `[contested naming]`

---

## Variants & checkpoints

### The two live versions

Both are in active use. **2.3 is not obsolete** — it is not gated, its checkpoints are single fat
files, and it is where nearly the whole IC-LoRA ecosystem was trained.

| | **LTX-2.5** | **LTX-2.3** | **LTX-2 (2.0)** |
|---|---|---|---|
| Released | **11 Aug 2026** | March 2026 | original release |
| Params | 22B | 22B | ~19B |
| Text encoder | custom **Gemma 4 12B** (bundled proj) | **Gemma 3 12B** (separate DL) | Gemma 3 |
| Checkpoint layout | **split** — one file per component | **monolith** — one file bundles transformer + both VAEs + text projection | monolith |
| HF gate | yes (`auto`) | **no** | no |
| Licence text | LTX-2.x CLA (2026-08-11) | LTX-2 CLA (2026-01-05) | LTX-2 CLA |
| Keyframe slots / DFR | ✅ | ❌ (pipeline raises) | ❌ |
| Diffusion video decoder | ✅ | ❌ | ❌ |
| Native multishot | ✅ | ❌ | ❌ |
| Auto duration | ✅ (duration head) | ❌ | ❌ |
| HF downloads (2026-08-22) | 694,670 | **1,578,744** | 382,214 |

Sources: https://ltx.io/llm-info, README + MODELS-LTX-2.3.md, HF API.

> "Files are not interchangeable between the two models, and **a LoRA only works with the model it
> was trained on**." — MODELS-LTX-2.3.md
>
> **But that line is contradicted by Lightricks' own shipped 2.5 workflows**, which load
> LTX-2.3-trained IC-LoRAs on the LTX-2.5 distilled transformer (see the IC-LoRA section below).
> `[contested — resolve in the skill, this is a load-bearing reader question]`

### LTX-2.5 files (all in `Lightricks/LTX-2.5` unless noted)

Verified against the HF file listing (17 files) and the repo README.

**Transformer — pick one:**

| File | What |
|---|---|
| `diffusion_models/ltx-2.5-22b-dev-transformer-bf16.safetensors` | full model; used by the guided two-stage pipelines |
| `diffusion_models/ltx-2.5-22b-distilled-transformer-bf16.safetensors` | **the recommended default**; what `DistilledPipeline`, `ICLoraPipeline` and `DubItPipeline` expect |
| `diffusion_models/ltx-2.5-22b-dev-transformer-comfy-int8-convrot.safetensors` | ComfyUI int8 build of dev |
| `diffusion_models/ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` | **ComfyUI int8 build of distilled — what all three official Comfy templates load** |
| `diffusion_models/ltx-2.5-22b-distilled-transformer-nvfp4.safetensors` | NVFP4 (Blackwell only) |

**Everything else:**

| File | Required by |
|---|---|
| `text_encoders/gemma4-12b-with-proj-ltx-2.5-bf16.safetensors` | every pipeline |
| `text_encoders/gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` | Comfy templates |
| `vae/ltx-2.5-video-vae-bf16.safetensors` | diffusion decoder (best quality) |
| `vae/ltx-2.5-video-vae-conv-bf16.safetensors` | conv decoder (lighter/faster) |
| `vae/ltx-2.5-audio-vae-bf16.safetensors` | anything with audio |
| `latent_upscale_models/ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors` | all two-stage pipelines |
| `latent_upscale_models/ltx-2.5-latent-temporal-upscaler-x2-bf16-1.0.safetensors` | `DFRPipeline` temporal rounds only |
| `loras/ltx-2.5-22b-distilled-lora-450-bf16.safetensors` | two-stage pipelines that run the **full** model in stage 1 |
| `model_patches/ltx-2.5-duration-head-bf16.safetensors` | optional; enables auto-duration |

**Download size for the quick-start set: "roughly 66 GiB."** (README)

**Separate repos:**

- `Lightricks/LTX-2.5-Pre-Trained` — **the raw non-SFT base checkpoint** (`ltx-2.5-22b-pt-bf16.safetensors`
  + a bundled Gemma 4 12B dir). Vendor framing: "A raw, non-SFT base built for aggressive
  fine-tuning, intended for use cases including egocentric robotics, action-conditioned world
  prediction, synthetic AV/drone data, and industrial digital twins." (llm-info). 2,502 downloads —
  a niche path, not the default.
- `Lightricks/LTX-2.5-Diffusers` — **diffusers-format 2.5**, last modified 2026-08-20, 6,489
  downloads. Contains `transformer/` (8-shard) *and* `transformer_full/` (4-shard), `vae/`,
  `audio_vae/`, `diffusion_decoder/`, `duration_head/`, `latent_upsampler/`,
  `temporal_latent_upsampler/`, `connectors/`, `vocoder/`, plus `modular_model_index.json`.
- `Lightricks/LTX-2.5-22b-IC-LoRA-Pixel-Spatial-Upscaler` — **the only 2.5-native IC-LoRA published
  so far** (`ltx-2.5-22b-ic-lora-pixel-spatial-upscaler-x2-1.0.safetensors`), used as DFR's
  `--detailing-lora`.

**Quantised 2.3 builds exist and are heavily used**: `Lightricks/LTX-2.3-fp8` (915,702 downloads —
more than the 2.5 base repo) and `Lightricks/LTX-2.3-nvfp4` (11,219). **No equivalent standalone
`LTX-2.5-fp8` repo exists yet**; on 2.5 you either use the int8-convrot Comfy builds, the nvfp4
file, or cast at load with `--quantization fp8-cast`.

### Task modes (pipelines)

`docs/pipeline-selection.md` and `docs/pipelines.md`. Twelve pipelines; the ones that matter:

| Pipeline | Mode | Stages | Notes |
|---|---|---|---|
| `DistilledPipeline` | T2V / I2V | 2 | **Recommended default.** 8 predefined sigmas (8 steps stage 1, 4 stage 2). "No guidance required." |
| `DFRPipeline` | T2V / I2V | 2 (+ up to 2 temporal rounds) | Max detail; needs 2.5; `--temporal-upsample-rounds {0,1,2}` each doubles fps |
| `TI2VidTwoStagesPipeline` | T2V / I2V | 2 | Production quality on the **full** model with CFG |
| `TI2VidTwoStagesHQPipeline` | T2V / I2V | 2 | Same, but **res_2s second-order sampler** — fewer steps, better quality |
| `TI2VidOneStagePipeline` | T2V / I2V | 1 | **"primarily for educational purposes"** — typically 512×768 |
| `ICLoraPipeline` | **V2V / I2V with control** | 2 | "can only be used with a distilled model" |
| `KeyframeInterpolationPipeline` | FLF2V / multi-keyframe | 2 | uses *guiding* latents, not replacing |
| `A2VidPipelineTwoStage` | **A2V** | 2 | audio frozen; original waveform passed through, not re-decoded |
| `RetakePipeline` | **regenerate a time region** | 1 | independent `regenerate_video` / `regenerate_audio` |
| `HDRICLoraPipeline` | V2V → linear HDR float | 2 | ARRI LogC3 inverse; **2.3 IC-LoRA only** |
| `DubItPipeline` | lip-sync dubbing | 2 | **2.3 IC-LoRA only**; frame count silently snapped to nearest `8k+1` |
| `T2AOneStagePipeline` | **text → audio, no video** | 1 | video branch absent (`video=None`) |

**Strong vs merely-supported, from vendor phrasing:** T2V/I2V via `DistilledPipeline` is the
explicit "recommended" path; `TI2VidOneStagePipeline` is self-described as educational; V2V exists
only *through* IC-LoRAs (there is no generic V2V mode); **Extend is API-only on 2.3 and has no local
pipeline** (see Could not verify).

---

## Multishot

**This is the defining 2.5 capability and it is invoked purely through the prompt.** There is no
`shots` parameter, no dedicated node, no separate checkpoint. I looked: the repo has no multishot
pipeline, no `--shots` CLI flag, and no multishot node in ComfyUI-LTXVideo.

### What the vendor claims it is

> "**Native Multishot:** A single generation produces multiple connected shots, holding character,
> environment, lighting, voice, style, and continuity across cuts (wide, over-the-shoulder, medium,
> close-up)." — https://ltx.io/llm-info

> "Native multi-shot means a single generation can produce multiple connected shots, holding
> character, scene, lighting, visual style, and voice consistent across cuts." —
> https://docs.ltx.io/models/ltx-2-5.md

### How you actually invoke it

From the official prompt guide (https://ltx.io/blog/ltx-2-5-prompt-guide, Rachel Luxemburg,
2026-08-10), verbatim:

> "Write the full scene as **one chronological paragraph** (or a short sequence of sentences). Do
> **not** use a shot list, numbered beats, or screenplay sluglines unless you also describe the cut
> in prose."

**What to include at every cut** (four rules, verbatim headings):

1. **"Name the transition** in natural language — e.g. 'A hard cut transitions to…', 'The view cuts
   to a close-up of…', 'A match cut connects…', 'The image dissolves into…'."
2. **"Re-establish the new shot** — shot scale, camera angle, who or what is in frame, and lighting
   if it changed."
3. **"Keep identity consistent** — reuse the same visual identifiers for recurring people or objects
   ('the woman in the red coat, earlier at the table, now…')."
4. **"State audio continuity** — e.g. 'the piano score continues across the cut' or 'the dialogue
   drops; only wind remains.'"

**Limits, verbatim:**

> "**Prefer 2–4 shots** in one generation; more cuts usually need clearer, shorter beats per shot."

> "**Avoid conflicting geography or unexplained costume changes** between cuts unless the cut is
> meant to jump time or place and you say so."

**Single-shot vs multi-shot, the guide's own table** (reflowed):

| | Single-shot | Multi-shot |
|---|---|---|
| Camera | One continuous take | New framing after each cut |
| Transitions | Camera moves only (pan, push-in, etc.) | **Name the edit**: hard cut, match cut, dissolve, etc. |
| Continuity | Same space / subjects throughout | Re-identify subjects when they reappear; say what carries across the cut |
| Audio | One continuous soundscape | At every cut, say whether music / dialogue / ambience continues or changes |

**When NOT to use it, verbatim:**

> "Use a single continuous take when you want unbroken camera motion, intimate performance, or
> dialogue that must stay lip-synced in one framing. **For image-to-video from a first frame, prefer
> a single continuous take** unless you intentionally describe a cut away from that opening image."

That last sentence is important for the skill: **multishot and I2V pull against each other.**

**The guide's own worked multi-shot example** (verbatim, three shots):

> "A wide shot frames a rainy city intersection at dusk, neon signs reflecting on wet asphalt. A
> young woman in a yellow raincoat walks toward camera, gripping a folded newspaper, while cars hiss
> past behind her. Soft synth music and distant traffic fill the air. A hard cut transitions to a
> medium close-up of her face under the hood, raindrops catching the neon as she looks off-screen
> left; the synth score continues across the cut, traffic muffled. She whispers, 'He's late.'
> Another hard cut jumps to a low-angle shot of a man's scuffed boots stepping into a puddle at the
> curb; the music drops to a low drone. He lifts his head into frame — short dark hair, soaked
> jacket — and smiles toward her off-screen as a bus rumbles past."

### Duration interaction

Auto-duration is the vendor's paired feature: "Send `"duration": null` and the model picks the length
itself, from your prompt. Use it when the prompt describes the shot rather than a fixed slot — **a
one-line action stays short, a multi-shot sequence runs longer.**"
(https://docs.ltx.io/models/ltx-2-5.md). Locally this is the optional `model_patches/ltx-2.5-duration-head-bf16.safetensors`
plus `--auto-duration MIN_SECONDS MAX_SECONDS`, or simply omitting `--num-frames` (CHANGELOG 1.2.0).

**API trap:** "Automatic duration cannot be combined with `last_frame_uri` on image-to-video. A last
frame fixes where the clip has to end, which requires a known length."

**Billing trap on prepaid API accounts:** credits are held against the *longest* duration your
resolution/fps allows until the job finishes — "a request that would have produced 6 seconds is
still declined if you cannot cover 20 on `ltx-2-5-fast`."

### Does identity actually hold across cuts?

Vendor says yes, for character/environment/lighting/voice/style. **Not independently verified here**
— that is the community pass's job. Note the vendor's own hedge: "more cuts usually need clearer,
shorter beats per shot," and the guide leans on *you* to re-identify subjects in prose, which implies
the model is not carrying identity autonomously so much as being re-anchored by the text at each cut.
`[inferred from the prompting rules, not stated]`

---

## Constraints (resolution / frames / duration / VRAM)

### The frame-count rule — the single hardest constraint

> "Frame count must be `1 + a multiple of 8`."
> — https://github.com/Lightricks/ComfyUI-LTXVideo/blob/master/example_workflows/2.5/README.md

Restated three more ways in primary sources:

- ltx-core README: `F' = 1 + (F-1)/8`, "frame count must satisfy `(F-1) % 8 == 0`".
- `docs/pipelines.md` §8 (Retake): "Source video frame count must satisfy the **8k+1** format
  (e.g. 97, 193) and **resolution must be multiples of 32**."
- `DubItPipeline`: frame count "is silently snapped to the nearest `8k+1`".

The Comfy templates compute it as `fps × seconds + 1` (`ComfyMathExpression: 'a * b + 1'`), which is
only legal when `fps × seconds` is a multiple of 8 — hence the warning: "Duration in the graphs is
converted from fps × seconds and may land slightly off the number you typed."

Anchor numbers: **121 frames = 5 s at 24 fps** (the repo's own quick-start `--num-frames 121`);
97 frames is the Comfy templates' default latent length; 89 frames is the trainer's validation
default.

### Resolution

- **Must be a multiple of 32** (both axes) — the VAE's spatial compression factor.
- ComfyUI templates drive resolution from a **megapixel budget**, not W×H. Their published 16:9 table:

  | MP | 16:9 output (mult. 32) | | MP | 16:9 output |
  |---|---|---|---|---|
  | 0.2 | 608×352 | | 0.9 | **1280×736** (template default) |
  | 0.3 | 736×416 | | 1.0 | 1376×768 |
  | 0.4 | 864×480 | | 1.2 | 1504×832 |
  | 0.5 | 960×544 | | 1.5 | 1664×928 |
  | 0.6 | 1056×608 | | 1.8 | 1824×1024 |
  | 0.7 | 1152×640 | | 2.0 | 1920×1088 |
  | 0.8 | 1216×672 | | | |

  (from the `MarkdownNote` inside `video_ltx2_5_t2v.json`)
- **Two-stage doubles it**: "these are the Stage-1 dimensions; the pipeline upscales 2× in Stage 2,
  so the final output is twice these dimensions."
  (https://docs.ltx.io/open-source-model/usage-guides/two-stage-generation.md)
- API resolutions are fixed tiers: 720p `1280x720`, 1080p `1920x1080`, 1440p `2560x1440`,
  4K `3840x2160`, each with a portrait twin (`720x1280`, `1080x1920`, `1440x2560`, `2160x3840`).

### Frame rate

**24, 25, 48 or 50 fps** (llm-info; docs support matrix). Not 16, not 30. The Comfy templates default
to **24**, set on `LTXVConditioning` (a conditioning-time value, not just a container value) *and*
on `CreateVideo`. The FLF2V template ships an inconsistency: `LTXVConditioning: [25]` but
`CreateVideo: [24]` — likely a template bug worth flagging to readers. `[contested within one
official file]`

### Duration lattice (API)

| Model | Resolution | FPS | Duration (s) |
|---|---|---|---|
| **ltx-2-5-fast** | 720p / 1080p | 24, 25 | 6, 8, 10, 12, 14, 16, 18, **20** |
| | 720p / 1080p | 48, 50 | 6, 8, 10 |
| | 1440p / 4K | 24, 25, 48, 50 | 6, 8, 10 |
| **ltx-2-5-pro** | 720p / 1080p | 24, 25, 50 | 6, 8, 10 |

(https://docs.ltx.io/models/ltx-2-5.md) Note **Pro tops out at 1080p and 10 s**; Fast is the one that
reaches 4K and 20 s. That inverts the usual "pro = more" intuition and is worth calling out.
Locally there is no such lattice — you set frames directly, subject to `8k+1` and VRAM.

Headline: **"Duration: up to 20 seconds per generation"**; "Videos can be extended beyond 20 seconds
using the Extend pipeline" (llm-info) — but Extend is API-only on 2.3 (see Could not verify).

### VRAM — three inconsistent vendor numbers

| Source | Claim |
|---|---|
| https://docs.ltx.io/open-source-model/getting-started/system-requirements.md | **Minimum: NVIDIA GPU with 32GB+ VRAM**, 32 GB RAM, 100 GB storage, CUDA 12.7+, Python 3.12+. **Recommended: A100 80GB or H100**, 64 GB+ RAM, 200 GB SSD |
| ComfyUI-LTXVideo README + docs.ltx.io ComfyUI page | "CUDA-compatible GPU with **32GB+ VRAM**", 100 GB+ disk |
| https://ltx.io/llm-info | "Hardware requirement for full model: GPU with **80GB+ VRAM**. Distilled and FP8-quantized variants support **32GB**, and run locally on a single GPU with **as little as 12GB VRAM**." |
| https://ltx.io/model/ltx-2-5 comparison table | "**Min VRAM: 16GB** — Available" |

**`[contested]` — 12 GB vs 16 GB vs 32 GB from the same vendor in the same week.** The 32 GB figure
is the one in the *documentation*; 12/16 GB are on *marketing* pages. Treat 32 GB as the honest
local floor for the distilled path at modest resolution, and mark the sub-16 GB claims as unverified
marketing until the community pass says otherwise.

**Levers that actually move the number** (`docs/optimization.md`, README, ComfyUI-LTXVideo README):

- `--quantization fp8-cast` (any FP8-capable GPU, downcasts bf16 on the fly) / `fp8-scaled-mm`
  (needs an fp8 checkpoint + Hopper+) / `nvfp4-cast` / `nvfp4-prequant` (Blackwell SM≥10 +
  `ltx-kernels`). Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
- `--offload {none,cpu,disk}` — cpu holds weights in system RAM, disk streams them (slower).
- **Use the conv video VAE instead of the diffusion one** — "lighter and needs no extra dependencies."
- Tiled VAE decode: ComfyUI `VAEDecodeTiled` defaults `[512, 64, 64, 16]` in the official templates;
  the Lightricks graphs publish a recommended-settings table (`512/64/128/32` → 16×16 tiles, up to
  `1536/384/192/48` → 48×48). "fewer tiles will result in faster execution, but will require more
  memory."
- `--diffvae-optimization`: `chunked_eager` (default, lowest VRAM) / `chunked_compile` /
  `combined_compile` (needs natten; "highest VRAM"; ~1.4× faster than chunked_compile) /
  `blackwell_dsl` (B200). "**Peak VRAM:** `chunked_*` roughly **~½** of `combined_compile`."
- ComfyUI-LTXVideo ships `low_vram_loaders.py`: "Those nodes ensure the correct order of execution
  and perform the model offloading such that generation **fits in 32 GB VRAM**." Plus
  `python -m main --reserve-vram 5`.
- **Offload text encoding to the LTX API** to free the 12B Gemma from VRAM — supported natively in
  the Lightricks two-stage graph ("use the '(via api)' outputs").
- Multi-GPU: sequence parallel, tiled data parallel, distributed VAE decode, distributed Gemma
  (`docs/multigpu/`).

**The repo publishes no absolute VRAM or timing figures.** `docs/optimization.md` says so
explicitly: "(order-of-magnitude; hardware varies - **no absolute timings or VRAM figures**)".

### Speed (vendor benchmark, treat as marketing)

"Self-hosted on **2× GB200** GPUs at 720p, LTX-2.5 generates a 10-second video clip in **6.8
seconds**." API figure: 23.7 s at 1080p on fal.run. Their comparison chart puts MiniMax H3 at 180 s
and Kling 3.0 Pro at 398 s for the same task. Methodology note is on the page and is unusually
candid ("Resolutions vary… LTX API figure is an internal measurement at 1080p").
(https://ltx.io/model/ltx-2-5)

Their artifact benchmark: LTX 2.5 Pro **0.28** visible glitches/clip, LTX 2.5 Fast 0.39, MiniMax
0.46, Wan 2.6 0.65, **LTX 2.3 Pro 0.74**, Veo 3.1 1.20 — "98 prompts, text to video, run through 10
models and graded by automated scoring rather than human viewers. **Preliminary results.**"

---

## Where to run it

### ComfyUI — native core support, three official templates

- **LTX-2 is built into ComfyUI core**: "LTX-2 is built into ComfyUI core
  ([see it here](https://github.com/comfyanonymous/ComfyUI/tree/master/comfy/ldm/lightricks))"
  (ComfyUI-LTXVideo README). The Lightricks custom-node repo adds extras on top.
- **Three native templates** (Template Library → Video → LTX-2.5), sources in
  `Comfy-Org/workflow_templates`:
  - `video_ltx2_5_t2v` — two-stage T2V
  - `video_ltx2_5_i2v` — two-stage I2V
  - `video_ltx2_5_flf2v` — single-stage first/last-frame
  (https://docs.comfy.org/tutorials/video/ltx/ltx-2-5)
- **Version requirement**: docs.comfy.org says "You are not using the latest ComfyUI version
  (**Nightly** version)" is a likely cause of missing nodes, and "Cloud will update after ComfyUI
  stable release." So as of 2026-08-22 the 2.5 templates may need **nightly**, not stable.
  `[time-sensitive — recheck]`
- **Custom nodes**: https://github.com/Lightricks/ComfyUI-LTXVideo (default branch is **`master`**,
  not `main`). Node categories: `LTXVideo/loaders`, `/samplers`, `/conditioning`, `/utils`.
- **Ten advanced 2.5 workflows** ship in `example_workflows/2.5/`: T2V/I2V two-stage and
  single-stage, A2V two-stage, T2A single-stage, and IC-LoRA graphs for Union Control, V2V, Ingredients,
  Motion Track, Inpaint and Outpaint. Their README carries a decision tree.
- Note **the ComfyUI-LTXVideo top-level README is still LTX-2.3-centric** (its model table, LoRA
  list and HF badge all point at 2.3); the 2.5 material lives in `example_workflows/2.5/README.md`.
  A reader following the top-level README will install the wrong stack. `[trap]`

**Official Comfy template settings, read from the JSON** (`video_ltx2_5_t2v.json`, distilled path):

| Setting | Stage 1 | Stage 2 |
|---|---|---|
| Sigmas (`ManualSigmas`) | `1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0` → **8 steps** | `0.85, 0.7250, 0.4219, 0.0` → **3 steps** |
| Sampler | `euler_ancestral` | `euler_ancestral` |
| Guider | `LTXVDualCFGGuider [1, 1]` — **video CFG 1, audio CFG 1** | same |
| Conditioning fps | `LTXVConditioning [24]` | — |
| Latent | `EmptyLTXVLatentVideo [768, 512, 97, 1]`, `LTXVEmptyLatentAudio [97, 25, 1]` | 2× spatial upscale via `LTXVLatentUpsampler` |
| Decode | `VAEDecodeTiled [512, 64, 64, 16]` + `LTXVAudioVAEDecode` | |
| Output | `CreateVideo [24, 8]` | |
| Negative prompt (shipped) | `pc game, console game, video game, cartoon, childish, ugly` | |
| Enhancer | `TextGenerateLTX2Prompt ['', 600, 'on', 0.7, 64, 0.95, 0.05, 1.15, 0, 0, False, True]` (max 600 tokens, temp 0.7, top_k 64, top_p 0.95, min_p 0.05, rep-pen 1.15) | |

I2V adds `LTXVImgToVideoInplace [0.7, False]` in stage 1 and `[1, False]` in stage 2, plus
`LTXVPreprocess [18]` (image-conditioning compression) and `ResizeImageMaskNode ['scale longer
dimension', 1536, 'lanczos']`. FLF2V uses `LTXVAddGuide [0, 0.7]` and `LTXVAddGuide [-1, 0.7]` (first
and last frame, strength 0.7) followed by `LTXVCropGuides`.

**CFG is a trap worth stating loudly.** From
https://docs.ltx.io/open-source-model/usage-guides/two-stage-generation.md:

> "Both stages use CFG 1. The distilled model bakes guidance into distillation, so raising CFG
> doesn't improve output the way it would with a standard diffusion model, and adds overhead. If you
> experiment, stay in the 1.0–1.5 range."

At CFG 1 the shipped negative prompt is inert. `[inferred — the guider takes both prompts but
cfg=1 collapses the difference]` The **dev** checkpoint via `TI2VidTwoStages*` is the path where
CFG and negatives actually do something.

**Prompt-enhancer default disagrees between sources** `[contested]`:
docs.comfy.org: "The workflow keeps it off by default"; docs.ltx.io: "The supplied templates
**enable prompt enhancement by default**; turn off **Prompt Enhance**…". In the JSON I read, the
`PrimitiveBoolean` feeding the enhancer is `True`. Cost: "needs the separate enhancer model (~5 GB)"
(comfy docs) / "~10 GB" (the template's own note) `[contested]` and "adds about 1-2 minutes".

### Local Python — the LTX-2 monorepo

`git clone https://github.com/Lightricks/LTX-2 && cd LTX-2 && uv sync --extra natten`

Three packages: `ltx-core` (model + inference stack), `ltx-pipelines` (12 pipelines, each runnable
as `python -m ltx_pipelines.<name>`), `ltx-trainer` (LoRA / IC-LoRA / full fine-tune).
Shared CLI flags: `--seed`, `--offload`, `--quantization`, `--max-batch-size`, `--compile`,
`--lora <path> [strength]` (repeatable), `--enhance-prompt`, `--hdr`, `--video-vae-path`,
`--diffvae-optimization`. Split vs monolith checkpoint paths are **mutually exclusive** — "Mixing
the two sets is an error."

Attention backends: FlashAttention 4 (`flash-attn-4==4.0.0b9`) on datacenter Blackwell B200 —
"newer betas have known issues on consumer Blackwell"; FA3 wheel on Hopper; PyTorch SDPA elsewhere.
`natten` pins `natten==0.21.7+torch2130cu132` with `torch==2.13.0` (cu132); older stacks can hit a
CUDA illegal memory access inside NATTEN TokPerm.

### diffusers

`Lightricks/LTX-2.5-Diffusers` exists (published/updated 2026-08-20) with `model_index.json` and
`modular_model_index.json`. **I did not verify which diffusers version supports it or what the
pipeline class is called** — see Could not verify.

### Hosted

| Where | Model IDs | Price |
|---|---|---|
| **LTX API** (`api.ltx.io`, console at `console.ltx.video` / `console.ltx.io`) | `ltx-2-5-fast`, `ltx-2-5-pro`, `ltx-2-3-fast`, `ltx-2-3-pro` | T2V/I2V per **second of output**: 2.5-fast $0.09 (720p) / $0.13 (1080p) / $0.19 (1440p) / $0.30 (4K); 2.5-pro $0.12 (720p) / $0.17 (1080p). 2.3-fast is 3× cheaper: $0.03 / $0.06 / $0.12 / $0.24 |
| | | A2V bills **input audio** seconds, same rates for 2.5 |
| | | Retake / Extend / HDR-upscale / Reframe are **`ltx-2-3-pro` only**: retake $0.10/s @1080p; extend $0.10/s (capped at 505 billed frames ≈ 21 s at 24 fps); HDR upscale $0.20/$0.40/$0.80 per s by input tier; reframe $0.10 (720p) / $0.20 (1080p) |
| **fal.ai** | `lightricks/ltx-2.5/text-to-video/fast` and `/pro`, `/image-to-video/fast` and `/pro`, `/audio-to-video/fast` | Same per-second rates as the LTX API ($0.09–$0.30 fast, $0.12/$0.17 pro) |
| **Replicate** | `lightricks/ltx-2.5-fast` (2.7K runs), `lightricks/ltx-2.3-pro` (55.3K), `lightricks/ltx-2.3-fast` (47.5K), `lightricks/ltx-2-retake`, `lightricks/audio-to-video` | pricing not read |
| **LTX Desktop** | free, open-source local editor built on 2.5 | https://ltx.io/ltx-desktop |
| **LTX Studio** | subscription web suite; uses 2.5 as one of several models alongside Kling, Veo, FLUX, Seedance | — |
| **LTX Playground** | https://console.ltx.video/playground | — |

Sources: https://docs.ltx.io/pricing.md, https://fal.ai/ltx-2.5, https://replicate.com/lightricks.
**Replicate has no `ltx-2.5-pro` yet** — only `ltx-2.5-fast`.

### IC-LoRA control ecosystem — and the version question

**Lightricks' own 2.5 workflows load LTX-2.3-trained IC-LoRAs onto the LTX-2.5 distilled
transformer.** Verified by reading the JSON:

| 2.5 workflow | LoRA it loads |
|---|---|
| `LTX-2.5_ICLoRA_Union_Control_Distilled.json` | `ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors` |
| `LTX-2.5_V2V_ICLoRA_Single_Stage_Distilled.json` | `ltx-2.3-22b-ic-lora-deblur-0.9.safetensors` |
| `LTX-2.5_ICLoRA_Ingredients_Single_Stage_Distilled.json` | `ltx-2.3-22b-ic-lora-ingredients-0.9.safetensors` |
| `LTX-2.5_ICLoRA_Motion_Track_Distilled.json` | `ltx-2.3-22b-ic-lora-motion-track-control-ref0.5.safetensors` |
| `LTX-2.5_ICLoRA_Inpaint_Two_Stage_Distilled.json` | `ltx-2.3-22b-ic-lora-in-outpainting-0.9.safetensors` |

The docs corroborate: the page is titled "**All LTX-2.5 IC-LoRAs**" and lists 2.3 model cards
throughout, with the rule "Any adapter that does *not* support a given version of LTX is flagged in
its listing." (https://docs.ltx.io/open-source-model/integration-tools/ic-lo-ra-adapters.md)

**Three adapters are flagged as 2.3-only, "LTX-2.5 support in development":** HDR (Beta), Dub-It
(Beta), Relight.

Full released set (all `Lightricks/LTX-2.3-22b-IC-LoRA-*` unless noted): Union Control (depth +
canny + pose in one), Motion Track Control (sparse spline trajectories; nodes **LTX Draw Tracks** and
**LTX Sparse Track Editor**), Ingredients (reference sheet → consistent characters/props/locations;
two-part prompt `Reference sheet: <panels> / Generated video: <action>`), Pixel Spatial Upscaler
(2× and 4×), In-Outpainting, Water Simulation, Colorization, Decompression, Deblur, Day-To-Night,
Instant Shave, Cross-Eyed, Clean Plate, HDR (beta), Dub-It (beta), Relight. Plus
`LTX-2.3-22b-LoRA-Foley-V2A` and `LTX-2.3-22b-LoRA-Cinemagraph` (plain LoRAs, not IC).
**2.5-native: only `LTX-2.5-22b-IC-LoRA-Pixel-Spatial-Upscaler`.**

**Camera-control LoRAs are still LTX-2 (19B) era**: `LTX-2-19b-LoRA-Camera-Control-{Dolly-In,
Dolly-Out, Dolly-Left, Dolly-Right, Jib-Up, Jib-Down, Static}`. All show 0 HF downloads — either
unused or the counter is broken. `[contested / unverified]`

**IC-LoRA vs plain LoRA, the vendor's own distinction**
(https://docs.ltx.io/open-source-model/usage-guides/ic-lo-ra.md):

> "Unlike standard LoRAs that modify style globally, IC-LoRAs perform targeted, reference-driven
> operations while preserving the original scene's identity."

| | LoRA | IC-LoRA |
|---|---|---|
| Input | Text prompt only | Text prompt + **reference input** (control signal or video clip) |
| Strength | 0.5–1.5 | 0–1.0, **global + spatial mask** |
| Control | Global style | **Frame-level spatial** |
| Training data | Video datasets (single modality) | **Paired** video + control signals |

Key ComfyUI nodes: `LTX IC-LoRA Loader Model Only`, `LTX Add Video IC-LoRA Guide`
(`attention_strength`, `attention_mask`), `LTX Add Video IC-LoRA Guide Advanced` (mask-aware, for
in/outpainting), `LTXVCropGuides` (crops guide frames out after stage 1).

### Training

`ltx-trainer` uses one unified "**flexible**" strategy; every mode is a config, expressed by setting
`is_generated` per modality plus optional conditions
(https://docs.ltx.io/open-source-model/ltx-trainer/training-modes.md):

| Mode | Video | Audio | Conditions |
|---|---|---|---|
| T2V | generated | generated | — |
| I2V | generated | generated | `first_frame` (with a `probability`, default 0.5 in the sample config) |
| Video extension | generated | generated | `prefix`/`suffix` (`temporal_boundary` counts **latent** frames; ×8 pixel frames) |
| V2V IC-LoRA | generated | — | `reference` |
| A2V | generated | **frozen** | — |
| V2A (foley) | **frozen** | generated | — |
| Video in/outpainting | generated | generated | `mask` / `spatial_crop` |
| T2A, audio extend/inpaint, A2A IC-LoRA, AV2AV IC-LoRA | — | generated | various |

"At least one modality must have `is_generated: true`." "Audio does **not** support `first_frame` or
`spatial_crop` conditions — only `prefix`, `suffix`, `mask`, and `reference`."

Trainer validation defaults (CHANGELOG 1.2.0): **960×544×89 frames, 24 fps, 30 inference steps, STG
block 28**, plus "a substantially expanded negative prompt", and separate video/audio CFG+STG
controls. Guidance settings are now **per-modality** (`video_cfg_scale`/`audio_cfg_scale`,
`video_stg_scale`/`audio_stg_scale`); the old flat `guidance_scale`/`stg_scale`/`stg_mode` were
removed and are auto-migrated.

**LTX ships its own agent skill for training** at `.claude/skills/train-model/` inside the LTX-2
repo (SKILL.md + phase files + references for hardware profiles, mode selection, config patching,
troubleshooting). Worth reading before authoring the LoRA reference — it is the vendor's own
distillation of the training workflow.

---

## Official prompting guidance

Two primary sources, and they agree.

### The repo's version (README, "✍️ Prompting for LTX-2"), verbatim

> "When writing prompts, focus on detailed, chronological descriptions of actions and scenes. Include
> specific movements, appearances, camera angles, and environmental details - all in a single flowing
> paragraph. Start directly with the action, and keep descriptions literal and precise. Think like a
> cinematographer describing a shot list. **Keep within 200 words.** For best results, build your
> prompts using this structure:
> - Start with main action in a single sentence
> - Add specific details about movements and gestures
> - Describe character/object appearances precisely
> - Include background and environment details
> - Specify camera angles and movements
> - Describe lighting and colors
> - Note any changes or sudden events"

### The blog's version (https://ltx.io/blog/ltx-2-5-prompt-guide, 2026-08-10)

**Six elements to include:** (1) Establish the Shot — cinematography terms, shot scale; (2) Set the
Scene — lighting, colour palette, surface textures, atmosphere; (3) Describe the Action — "a natural
sequence, flowing clearly from beginning to end"; (4) Define the Character(s) — "age, hairstyle,
clothing, and distinguishing features. Express emotion through **physical cues**, not abstract
labels"; (5) Identify Camera Movement(s) — "Describing how subjects appear **after** the movement
helps the model complete the motion accurately"; (6) Describe the Audio — "Place spoken dialogue in
**quotation marks**. Specify language and accent if needed."

**Three universal principles, verbatim:**

> "**Keep the scene focused** — a few clear characters and actions read better than a crowded frame.
> **Keep lighting consistent** — use one coherent light logic per shot; mixed light sources confuse
> the result. **Start simple and layer** — begin with the core shot, then add detail as you iterate."

**Single-shot form:** "Write your prompt as a **single flowing paragraph**", "Use **present tense**
verbs", "Match the level of detail to the shot scale (close-ups need more detail than wide shots)",
"Describe camera movement relative to the subject", "Aim for roughly **4–8 descriptive sentences**".

**Screenplay style is explicitly allowed for dialogue scenes**: "When a scene involves dialogue,
multiple beats, or precise timing, you can write it in a screenplay style — scene headers, character
cues, and quoted dialogue." Note this sits in tension with the multi-shot rule ("Do **not** use…
screenplay sluglines unless you also describe the cut in prose"). `[apparent tension in one document
— the resolution is that screenplay form is for *dialogue within one shot*, not for cuts;
[inferred]]`

**Length:** "Match length to complexity rather than a fixed count." Blog says 4–8 sentences for a
single shot; README says "Keep within 200 words". `[soft contradiction — the README number is the
harder constraint]`

**Dub-It prompt template**, verbatim: `[Speaker] is speaking [Language/Accent], saying: "[Dialogue]"`
— languages validated: **English, French, Spanish, German, Russian**. Requirements: full dialogue
text ("It does **not** translate dialogue for you"), **native script** (Cyrillic for Russian, etc.),
**single speaker only** ("the beta IC-LoRA does not distinguish between multiple speakers"). Best
practice: "keep your prompt at roughly the same timing and syllable length as the original dialogue.
Slightly longer is better than too short. Prompt too long: the model might skip words. Prompt too
short: the output might sound slow and unnatural."

**Per-mode prompting tips from docs.comfy.org:**

- T2V: "Include the shot type, scene, action, characters, and camera movement in one flowing paragraph"
- **I2V: "Describe what happens next — write the motion, camera movement, and sounds that follow
  from the input image; do not re-describe what is already visible"** and "Anchor the first frame:
  Use phrasing like 'Use the provided start image as the first frame' when writing a continuation"
- FLF2V: "Describe the transition… Keep frames aligned: Use images with the same aspect ratio"

**Vocabulary lists the blog publishes** (useful for a skill's prompt-lexicon table): categories
(Animation / Stylized / Cinematic with ~20 named genres), lighting, textures, colour palette,
atmosphere, ambient sound settings, dialogue style, volume (whisper/mutter/shout/scream), camera
language (follows, tracks, pans across, circles around, tilts upward, pushes in / pulls back,
overhead view, handheld movement, over-the-shoulder, wide establishing shot, static frame), film
characteristics, scale indicators, pacing/temporal effects, visual effects.

**The repo's own quick-start prompt is the best worked example of audio prompting** — it inlines
sniffs, a described voice ("a deep male voice and a satisfied tone"), and three quoted lines of
dialogue in one flowing paragraph. Worth quoting in the skill.

**Prompt enhancer**: `--enhance-prompt` on the CLI, `prompt_enhance` in ComfyUI. "The negative prompt
is never enhanced."

---

## Vendor-admitted limitations

Explicit, from primary sources:

1. **On-screen text is unreliable.** Prompt guide, verbatim: "LTX-2.5 improves short-text accuracy
   and preserves fine details better than earlier versions, but **exact spelling and consistency
   across frames are not guaranteed**. Keep text short and prominent, verify it throughout the clip,
   and add critical titles, labels, or logos in post."
2. **Complex physics.** Verbatim: "highly chaotic motion can still introduce artifacts; simpler,
   plausible motion is more reliable. (Everyday motion like dancing is fine.)"
3. **Multishot degrades past ~4 cuts.** "Prefer 2–4 shots in one generation; more cuts usually need
   clearer, shorter beats per shot."
4. **Multishot fights I2V.** "For image-to-video from a first frame, prefer a single continuous take
   unless you intentionally describe a cut away from that opening image."
5. **The Pixel Spatial Upscaler is generative, not restorative.** Docs, verbatim: "This is a
   generative upscaler, not a refiner. It synthesizes new detail rather than faithfully preserving
   the reference, so it is **not suited to pixel-accurate restoration, blind denoising, or
   compression-artifact removal**."
6. **DFR does not refine audio.** "Stage 2 still runs an audio pass, because the video branch needs
   the cross-modal attention, but **nothing refines audio after stage 1**."
7. **`TI2VidOneStagePipeline` is not for production.** "⚠️ **Important:** This pipeline is primarily
   for educational purposes."
8. **Dub-It, HDR and Relight IC-LoRAs do not yet support 2.5.** "LTX-2.5 support in development."
9. **Dub-It cannot handle multiple speakers**, and does not translate.
10. **Raising CFG on the distilled model doesn't help.** "raising CFG doesn't improve output the way
    it would with a standard diffusion model, and adds overhead."
11. **Auto-duration is incompatible with a fixed last frame** (API).
12. **Own artifact benchmark is non-zero and preliminary**: LTX 2.5 Pro 0.28, Fast 0.39 visible
    glitches per clip; "Preliminary results, expected to evolve as evaluation expands."
13. **NATTEN/CUDA fragility**: "Older PyTorch/NVIDIA stacks can IMA [illegal memory access] inside
    NATTEN TokPerm on large stage-5 volumes."
14. **FlashAttention 4 betas**: only `4.0.0b9` is verified against torch 2.9.1+cu128; "newer betas
    have known issues on consumer Blackwell."
15. **Hosted-only features.** The **Video Editing IC-LoRA (Beta)** is described as "available in Beta
    via IC-LoRA **through the API**" (llm-info) and does not appear in the open IC-LoRA list —
    so the flagship "edit real footage" capability is not fully in the open release. `[see Could not
    verify]` Similarly, **Retake / Extend / Reframe / HDR-upscale API endpoints are `ltx-2-3-pro`
    only** — not available on 2.5 at any tier.

---

## Could not verify

Listed honestly rather than papered over.

1. **The LTX-2.5 per-stream parameter split.** The paper gives 14B video + 5B audio for the 19B
   LTX-2; no source states how the 22B of 2.3/2.5 divides. Do not assume 17B+5B.
2. **Whether 2.5 changed the VAE compression factors.** The CHANGELOG says the trainer now "derive[s]
   spatial and temporal compression factors from checkpoint metadata **instead of assuming
   32x32x8**", and the CLI gained "checkpoint-aware size-, count-, and automatic-tiling APIs that
   support **non-default VAE compression factors**". That strongly implies *some* checkpoint differs
   — but the ltx-core README still documents 32×/8× and the `8k+1` + multiple-of-32 rules still hold
   in the 2.5 workflows. **Unresolved whether the non-default path exists for 2.5 or for a future
   model.**
3. **Whether LTX-2.5 output carries a latent watermark or C2PA provenance.** The licence §6 forbids
   removing "watermarking, content provenance, latent disclosure, or other transparency features…
   including any capability of LTX-2.x to include latent disclosures in Outputs" and makes tampering
   grounds for immediate revocation — but I found **no documentation of what, if anything, is
   actually embedded** in open-weights output. This matters: it is the only clause that can revoke
   the licence unilaterally.
4. **The "Video Editing IC-LoRA (Beta)"** — whether open weights exist. It is a headline 2.5 feature
   on ltx.io and llm-info, is absent from the released IC-LoRA list, and llm-info says it is
   available "through the API". Possibly the same thing as the API's `ltx-2-3-pro` retake endpoint,
   possibly a distinct unreleased adapter.
5. **Extend as a local pipeline.** llm-info lists "Extend: Continue an existing video beyond its last
   frame" as an LTX-2.5 workflow; the trainer has a `video_extend_lora` mode with prefix/suffix
   conditioning; but **there is no `ExtendPipeline` in `ltx-pipelines`**, and the API's extend
   endpoint is `ltx-2-3-pro` only. How you extend a clip locally on 2.5 is unresolved
   (`RetakePipeline` + prefix conditioning is the likely answer `[inferred]`).
6. **diffusers support specifics** — which diffusers release, which pipeline class, whether audio
   decode is wired. `Lightricks/LTX-2.5-Diffusers` exists and has `modular_model_index.json`, but I
   did not read its README or config.
7. **Real-world VRAM at specific resolution/length combinations.** No vendor figures exist; the
   32/16/12 GB claims are mutually inconsistent (see Constraints). Community pass should settle this.
8. **Replicate pricing** for `lightricks/ltx-2.5-fast` — model page not fetched.
9. **The LTX-2.5 technical report.** The arXiv paper (2601.03233) describes **LTX-2**, not 2.5. A
   2.5-specific report is linked from ComfyUI-LTXVideo as a PDF
   (`https://videos.ltx.io/LTX-2/grants/LTX_2_Technical_Report_compressed.pdf`) but that is also the
   LTX-2 report.
10. **Whether the AUP's NSFW ban is enforceable against purely local, unpublished use.** The AUP is
    drafted for hosted "Products" (accounts, API keys, bans) yet Attachment A incorporates it
    wholesale. This is a genuine legal ambiguity, not a research gap — state it as such.
11. **Camera-control LoRA usefulness on 2.5.** They are LTX-2 (19B)-era files with 0 recorded HF
    downloads and no 2.5 workflow references. llm-info still advertises them as a 2.5 creative
    control. Probably stale marketing. `[needs the community pass]`
12. **Multishot identity retention in practice** — vendor claim only; no independent evidence read.
13. **ComfyUI stable-vs-nightly status for the 2.5 templates** as of today.

---

## Sources

**Licence**
- https://raw.githubusercontent.com/Lightricks/LTX-2/main/LICENSE.md — LTX-2.x Community License Agreement, 2026-08-11 (read in full)
- https://huggingface.co/Lightricks/LTX-2.3/raw/main/LICENSE — LTX-2 Community License Agreement, 2026-01-05 (read in full)
- https://static.lightricks.com/legal/ltx-acceptable-use-policy.pdf — Acceptable Use Policy, 2026-03-30 (read in full, 5pp)
- https://huggingface.co/api/models/Lightricks/LTX-2.5 (and `/LTX-2.3`, `/LTX-2.5-Pre-Trained`, `/LTX-2.5-Diffusers`) — gating status, licence labels, file listings

**Vendor primary**
- https://github.com/Lightricks/LTX-2 — README (raw: `raw.githubusercontent.com/Lightricks/LTX-2/main/README.md`)
- https://raw.githubusercontent.com/Lightricks/LTX-2/main/MODELS-LTX-2.3.md
- https://raw.githubusercontent.com/Lightricks/LTX-2/main/CHANGELOG.md — v1.2.0, 2026-08-11
- https://raw.githubusercontent.com/Lightricks/LTX-2/main/packages/ltx-core/README.md — architecture deep dive
- https://raw.githubusercontent.com/Lightricks/LTX-2/main/packages/ltx-pipelines/README.md
- `.../packages/ltx-pipelines/docs/{pipelines,pipeline-selection,conditioning,optimization,installation}.md`
- https://ltx.io/llm-info — official facts-for-LLMs page, "Last updated: August 2026"
- https://ltx.io/model/ltx-2-5 — release page, benchmarks, comparison table
- https://ltx.io/blog/ltx-2-5-prompt-guide — official prompt guide, 2026-08-10
- https://docs.ltx.io/llms.txt — docs index (every page has a `.md` twin; MCP server at `https://docs.ltx.io/_mcp/server`)
- https://docs.ltx.io/models/ltx-2-5.md, `/models/ltx-2-3.md`, `/pricing.md`
- https://docs.ltx.io/open-source-model/getting-started/system-requirements.md
- https://docs.ltx.io/open-source-model/integration-tools/comfy-ui.md
- https://docs.ltx.io/open-source-model/integration-tools/ic-lo-ra-adapters.md
- https://docs.ltx.io/open-source-model/usage-guides/ic-lo-ra.md
- https://docs.ltx.io/open-source-model/usage-guides/two-stage-generation.md
- https://docs.ltx.io/open-source-model/ltx-trainer/training-modes.md
- https://arxiv.org/abs/2601.03233 — "LTX-2: Efficient Joint Audio-Visual Foundation Model"

**ComfyUI**
- https://docs.comfy.org/tutorials/video/ltx/ltx-2-5
- https://github.com/Lightricks/ComfyUI-LTXVideo (branch `master`) — README and `example_workflows/2.5/README.md`
- Workflow JSON read directly: `Comfy-Org/workflow_templates/templates/video_ltx2_5_{t2v,i2v,flf2v}.json`; `Lightricks/ComfyUI-LTXVideo/example_workflows/2.5/*.json`

**Hosts**
- https://fal.ai/ltx-2.5 and `fal.ai/models/lightricks/ltx-2.5/*` — endpoint IDs and pricing (pricing corroborated by docs.ltx.io/pricing)
- https://replicate.com/lightricks — model list and run counts

**Second-hand / not used for hard facts**
- VentureBeat, HackerNoon, ltx23.org, dreampixelforge.com, earngenix.com, runware.ai, kie.ai — all
  surfaced in search; **none used as a source for any claim above.** Runware's multishot guide
  independently describes the same 2–4-cut prose pattern, which corroborates the vendor guide but
  adds nothing.
