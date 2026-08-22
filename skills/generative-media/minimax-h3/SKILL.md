---
name: minimax-h3
description: >
  Authoritative guide for MiniMax H3, the open-weights omni-modal video-with-native-audio model (MiniMax / Nanonoble Pte. Ltd., released 2 August 2026), in ComfyUI or diffusers. **Read the licence section first: the MiniMax H3 Community License excludes the United States, the European Union, the United Kingdom and South Korea from its Applicable Territory, and use outside that territory is an explicitly prohibited use.** Use this whenever the user touches MiniMax H3 in any way, even obliquely: asking whether they may legally use it at all, choosing between the FL2VA and Ref2VA checkpoints, installing it in ComfyUI (the dual video+audio VAE, the two decode nodes, the Qwen3-VL-32B encoder, quantised builds, VRAM), writing prompts (the prompt drives dialogue, sound effects and music as well as picture — that is the whole point of the model), hitting the frame-count rule, picking resolution from the megapixel table, generating video with synchronised stereo audio, first/last-frame and multi-reference conditioning, **making it fast** (the sparse-attention/SLA node, Spectrum and its audio-feedback trap, the lightx2v Turbo LoRA, and the CU130 / comfy-kitchen / nvfp4-encoder traps that silently cost most of the speed), **fixing Ref2VA's quality gap with the `adaln_proj` hybrid checkpoints**, **generating minute-plus video by context chaining**, **using it as a single-image edit model** (one frame + the dedicated image VAE), **replacing a character in existing footage** with the `[video editing]` / `retention_analysis` prompt shape, building character reference sheets, understanding what is *not* in the open release (Context-IR and Regenerate-2K are hosted-only, so local output is 768p and 2K is API-only), debugging audio/video desync or artefacts, or comparing it against Wan 2.2, SCAIL-2 and LTX-2.5. Also covers who should reach for something else instead — which, on licence grounds, is a large share of readers.
---

# MiniMax H3

MiniMax H3 is a **33B-parameter dense, single-stream omni-modal transformer** from MiniMax (licensor: **Nanonoble Pte. Ltd.**), released **2 August 2026**. It jointly understands text, images, video and audio, and generates **video with native 32 kHz stereo audio** — voice, sound effects and music modelled together with the picture in a single forward pass, not layered on afterwards. Output runs to 24 fps, 4–15 seconds, and up to 2K. The text encoder is the full **Qwen3-VL-32B** (hidden states taken from its 50th layer).

**The defining trait:** it is the first widely-adopted open-weights model where **sound is part of the generation, not a separate stage**. Everything else about how you use it follows from that.

**The defining constraint:** the licence does not cover the US, EU, UK or South Korea. That is not a footnote — see below, and settle it before you download anything.

---

## Before anything else — the licence and the territory

This section leads because it is the fact most likely to matter to you, and it is the one the launch coverage almost universally omits.

**MiniMax H3 Community License Agreement**, licence date 2 August 2026, licensor **Nanonoble Pte. Ltd.**, governed by the law of **Hong Kong SAR** with exclusive jurisdiction in Hong Kong courts. `[official — repo LICENSE]`

| Term | What it says |
|---|---|
| **Applicable Territory** | *"worldwide, excluding the Excluded Territories"* |
| **Excluded Territories** | *"the European Union, the United Kingdom, the Republic of Korea and the United States of America"* |
| **Prohibited use #1** (Exhibit A) | *"Use outside the Applicable Territory"* |
| Commercial threshold | Separate **prior written authorization** required above **US$20 million** yearly revenue (`api@minimax.io`) |
| Commercial attribution | You **shall prominently display "MiniMax H3"** on the UI of any commercial product or service using it |
| Downstream obligations | You must bind every recipient to terms at least as protective, and notify them |
| Redistribution | Pass on the Agreement, mark modified files, and ship a `NOTICE` file reading: *"MiniMax H3 is licensed under the MiniMax H3 Community License Agreement, Copyright © 2026 MiniMax. All Rights Reserved."* |

**Read plainly: if you are in the US, EU, UK or South Korea, this licence grants you nothing, and Exhibit A lists territorial use as a prohibited use.** This is stricter than "no commercial use" — it is *no use*. It is also unusual; none of the other open-weights video models in this suite carry a territorial restriction.

**This skill does not tell you what your legal position is.** Licence scope, enforceability of a Hong Kong-governed click-through, and how any of it applies to you are questions for a lawyer, not a model guide. What this skill does is make sure you know the clause exists before you build on it, because the cost of finding out later is high.

**If you are in an excluded territory**, the practical routes are: use the **hosted API/app** under whatever terms govern those (a separate agreement from this one — check it); or reach for a model whose licence covers you. Two candidates, and they do not fail in the same way:

- **[`wan-2-2`](../wan-2-2/)** — **Apache 2.0**, worldwide, commercial use included, no revenue test and no content clause. It is the clean answer, and the suite's **licence-clean default** — the only one of the three with no gate on it at all. Note precisely what that claims: Wan's own skill hands the title of *default open video model* to H3 and keeps a narrower, more durable one instead. That is the right reading, and it is also why Wan is the right answer **here** — on this page you have already been ruled out by a licence, and the property you need is not popularity but the ability to ship.
- **[`ltx-2-5`](../ltx-2-5/)** — also generates native audio, under the **LTX-2.x Community License Agreement** (11 August 2026). The licence text itself is **public and ungated** on GitHub; only the weights sit behind a Hugging Face contact-information gate. Use is free worldwide **below US$10M annual revenue**, aggregated across subsidiaries and affiliates — and derivatives, **LoRA adapters explicitly**, inherit the agreement, with the revenue obligation following the LoRA to whoever ends up using it. Two clauses catch people who assume "under $10M" means clear: Attachment A ¶20 bars using the model in anything that **competes with Lightricks' own products, at any revenue level**, which binds a hobbyist as hard as a studio; and the incorporated Acceptable Use Policy **prohibits sexually explicit generation** — its scope covers on-premises deployments, so that applies to the local weights, not only the hosted service. `[official — Lightricks/LTX-2 LICENSE.md, incorporated AUP]`

**Three models, three different shapes of licence risk, and it is worth holding them apart.** H3 excludes whole **territories** — a fact about where you are, which no amount of care about your use case fixes. LTX gates on your **company's revenue** and on **what you build** — facts about your business, which change under you as the business grows. Wan 2.2 has neither. So "which licence is most permissive" is the wrong question; the right one is which axis applies to you, because only one of these three can be satisfied by moving.

Two smaller notes: the **encoder is separately licensed** — Qwen3-VL-32B is Apache 2.0 `[official — licence "Additional Note"]`. And MiniMax runs **automated moderation** on submitted text, images and video, which does not alter your obligations under the licence.

Full clause-by-clause treatment, the Exhibit A list, and the redistribution mechanics: **`references/licence-and-territory.md`**.

---

## Task-mode selector

H3 ships as **two task-specific checkpoints**, both BF16, each bundling its own processor, tokenizer, text encoder and VAEs. A third option — a hybrid of the two — is community-built and is what most serious reference work now runs.

| Checkpoint | Tasks | Use when… | Inputs | ComfyUI node |
|---|---|---|---|---|
| **FL2VA** | `t2va` (text→audio-video), `fl2va` (first/last-frame→audio-video) | You are starting from text alone, or from a first and/or last frame. The default path, and the better-looking one | Text; **zero, one or two** images — none = T2V, one = first *or* last frame, two = both | `MiniMaxH3ImageToVideo` |
| **Ref2VA** | `ref2va` (omni-reference) | You need to carry a specific face, clip or **voice** into the output rather than describe it | ≤ 9 images, ≤ 3 video clips (2–15 s each), ≤ 3 audio clips (2–15 s each), **≤ 12 files total**, total ≤ 15 s | `MiniMaxH3ReferenceToVideo` |
| **Hybrid** (FL2VA base + Ref2VA `adaln_proj`, blocks 30–49) | `ref2va` at FL2VA quality | You want references *and* FL2VA's picture and audio. Start here for any Ref2VA work you care about | as Ref2VA | as Ref2VA, plus the hybrid loader — or a pre-baked build |

**One node covers three modes.** `MiniMaxH3ImageToVideo` is T2V when nothing is connected and FLF2V when you attach frames — there is no separate text-to-video node, which surprises people looking for one.

**Ref2VA is the genuinely unusual capability.** Passing reference *audio* alongside reference images and video is something nothing else in this suite can do — it is how you carry a voice or a musical texture into the output rather than merely describing it.

**But Ref2VA looks worse than FL2VA, and there is now a fix.** This is the most reported quality complaint about the model, and it is real: swap the FL2VA checkpoint into an unchanged Ref2VA workflow and picture and audio both improve while references still broadly work. Someone diffed the two checkpoints — same architecture, and the divergence is almost entirely in the **`*.adaln_proj.*` tensors**. Overlaying Ref2VA's `adaln_proj` tensors onto an FL2VA base **for blocks 30–49 only** keeps reference capability at FL2VA quality; blocks 0–25 destroy it, which is where Ref2VA's problems live. `[community — ThatsALovelyShirt]`

Two ways to get it, both in `references/setup-and-workflows.md §5`: `scottmudge/ComfyUI_MinimaxH3HybridLoader` overlays the tensors at load time with no disk or memory cost, or `smhfacct/Minimax-H3-fl2va-ref2va-hybrid-models` ships pre-baked builds — start at **`b30-49`**. One side effect to expect either way: hybrids drag a character sheet's **white background** into the shot more readily than plain Ref2VA, so matte the sheet or state the environment. `[community — erioca; re-verify]`

| Output spec | Value |
|---|---|
| Duration | 4–15 s |
| Frame rate | **24 fps** |
| Audio | **32 kHz stereo** |
| Resolution | short side 768 by default; 2K only via the hosted Regenerate-2K |
| Aspect ratios | wide range — 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 and others |
| Dialogue languages | 11 stable: Arabic, Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian, Spanish |

---

## What "open weights" means here — one module of three

The complete H3 system is three modules. **Two of them are not in the open release.** `[official — model card]`

| Module | What it does | Open? |
|---|---|---|
| **H3-Context-IR** | Preprocesses free-form multimodal input into the structured representation H3-Base consumes. The card calls it *"critical to the quality of the final output"* | ❌ **Hosted only.** An API reproduces the official workflow |
| **H3-Base** | The generator. Produces 768p video + stereo audio | ✅ **This is what you download** |
| **H3-Regenerate-2K** | Regenerates the 768p result in-context at 2K | ❌ **Not open.** *"We will release it once it is ready"* |

Two consequences worth internalising before you judge the model:

1. **Local output is 768p.** The 2K figure in the marketing is the API path. You can upscale by other means, but that is not what produces MiniMax's own 2K samples.
2. **Your prompt handling is not theirs.** Official demos run through Context-IR. Running H3-Base on a raw prompt is a different pipeline, and the gap is the reason local results often look weaker than the launch reel. The card's "Prompting Guidance" exists precisely so you can approximate Context-IR yourself — see `references/prompting-guide.md`.

The **sparse-attention implementation is also withheld**, promised "in a future update." `[official — model card]` **The community did not wait** — a third-party SLA node now delivers roughly the speed-up the withheld module was expected to, so "open inference is full-attention only" is no longer true in practice (see [Going faster](#going-faster--the-acceleration-stack)). Treat MiniMax's own sparse attention as a *pending release* that will change the recommendation again, not as a live ceiling.

---

## The one rule that changes everything

**Prompt the sound and the picture in the same breath.**

Every other video model in this suite takes a prompt describing what you *see*. H3 predicts video and audio latents jointly, so the prompt is also the script and the sound design. The official ComfyUI template says it directly: describe *"the shots, camera moves, and the accompanying audio (dialogue, SFX, music)."*

The mechanism is architectural, not stylistic. H3-Omni-Transformer emits video and audio latents from one sequence — so audio that goes undescribed is not silent, it is *unspecified*, and the model fills it with whatever it considers plausible. Naming the soundscape is how you control it.

| Video-model habit | H3 prompt |
|---|---|
| *A woman walks down a rainy street at night, neon reflections* | *A woman walks down a rainy street at night, neon reflections. **Her heels click on wet pavement, rain hisses on the awnings, distant traffic hum; no music.*** |

Three things fall out of this:

- **Dialogue is written, not implied.** Give the line and the delivery. With 11 supported languages, name the language when it is not obvious.
- **"No music" is a real instruction.** Unspecified scores get invented — say so when you want none.
- **Sound anchors motion.** Describing a sound implies the action that makes it, which reinforces the picture. A model that must produce a footstep has to animate the foot.

Full anatomy, audio vocabulary, dialogue formatting and the Context-IR approximation: **`references/prompting-guide.md`**.

---

## Setup & ecosystem

Requires ComfyUI with H3 support (added via **Comfy-Org/ComfyUI PR #15224**). Files come from the `Comfy-Org/MiniMax-H3` repackage.

### File layout

Deploying on rented GPUs? [`comfyui-on-runpod`](../comfyui-on-runpod/) owns the volume contract — and H3 is the model that punishes getting it wrong hardest, because it needs **five files across three directories including two VAEs**, and a missing audio VAE produces a silent video rather than an error.

| File | ComfyUI folder | Loader node |
|---|---|---|
| `minimax_h3_fl2va_pruned_int8_convrot.safetensors` (or `_bf16`, `_pruned_bf16`, `_pruned_fp8_scaled`) | `models/diffusion_models/` | Load Diffusion Model |
| `minimax_h3_ref2va_pruned_int8_convrot.safetensors` (same variant set) | `models/diffusion_models/` | Load Diffusion Model |
| `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (or `_bf16`, `_int8_convrot`) | `models/text_encoders/` | CLIPLoader — **type `minimax`** |
| **`minimax_h3_video_vae_fp16.safetensors`** | `models/vae/` | Load VAE |
| **`minimax_h3_audio_vae_fp32.safetensors`** | `models/vae/` | Load VAE |

> **Two VAEs, two decoders.** This is the structural thing that catches people. You load a **video VAE and an audio VAE**, and the graph ends in **two** decode nodes: `VAEDecode` for picture and **`VAEDecodeAudio`** for sound, both feeding `CreateVideo`. Miss the audio branch and you have quietly built a silent video model with a 33B parameter overhead.

> **The official templates ship quantised by default** — `pruned_int8_convrot` weights, `nvfp4_awq` encoder — which is itself the statement about memory pressure. **`pruned` builds are inference-only**: they drop the ~13B of AdaLN-branch parameters that can be precomputed, so take a non-pruned build if you intend to fine-tune. Build matrix and VRAM: `references/setup-and-workflows.md §2`.

### Do not swap in a "heretic" / abliterated text encoder

A myth spread fast enough after release that a popular Docker template shipped it: that replacing the Qwen3-VL encoder with an abliterated ("heretic") build uncensors the output. **It does not** — per the author of Heretic himself, abliteration perturbs the hidden states relative to what the transformer was trained on, costing prompt adherence and adding artefacts, and the encoder shipped for H3 has **no refusal path in it to remove** (its output layers are absent, which is why it is ~8 GB smaller than stock). The failure is silent: output gets subtly worse, nothing errors. `[community — -p-e-w-, author of Heretic]`

**Abliterated models belong one stage earlier — prompt expansion**, where a refusing LLM is a real problem. Keep the stages distinct, and watch for ComfyUI subgraphs that wire **the same LLM** into both the expander and the text-encode node: swapping it to fix the expander silently swaps the encoder too, the same shape as [`krea-2`'s](../krea-2/) enhancer problem.

**Also worth knowing:** community consensus is that H3 does not meaningfully refuse anything — reported anatomy failures are attributed to **training-data gaps, not filtering**, and supplying reference images reportedly fixes much of it. `[community — re-verify]` Full argument, quotes and the cross-model lesson: `references/setup-and-workflows.md §10`.

### diffusers

`DiffusionPipeline.from_pretrained("MiniMaxAI/MiniMax-H3", dtype=torch.bfloat16)`. The card's snippet is HF's generic autogenerated one and shows an *image* call — treat it as a placeholder and check the current pipeline class before relying on it. `[flagged — re-verify]`

---

## Per-mode settings

H3's axis is **task mode, not variant**: FL2VA and Ref2VA are BF16 builds of one architecture, and they share a sampler chain. People go looking for a second recipe and do not find one, so the differences are stated explicitly here.

### Both modes — the stock path

H3 uses the **custom sampler chain**, not `KSampler`:

`RandomNoise` → `BasicGuider` → `KSamplerSelect` → `BasicScheduler` → `SamplerCustomAdvanced`

| Setting | Value |
|---|---|
| Sampler | **`res_multistep`** (template, verbatim) |
| Scheduler | **`simple`** (template, verbatim) |
| Steps | **20** (template). **30 is reported to fix cloth physics and interaction errors *and* audibly improve the audio** `[community — nsfwVariant]` |
| Denoise | **1.0** |
| Guidance / CFG | **none.** The graph wires `BasicGuider`, not `CFGGuider` — it is guidance-free |
| Negative prompt | **No path exists.** Phrase every constraint positively |
| Resolution | **1344 × 768** (0.98 MP) default; ~0.8 MP is the reliability sweet spot; 0.2 MP for drafts |
| Frame count | on the **`17n + 5`** lattice — 73 ≈ 3 s, 124 ≈ 5 s, 362 ≈ 15 s (the maximum) |
| fps | **24**, fixed |
| Shift | no shift widget in the stock templates. `MiniMax H3 Sigma Shift` arrives with the Spectrum pack and is where the acceleration chain attaches — treat shift as part of that stack rather than a quality dial |
| Seed | ordinary `RandomNoise` behaviour, but judge a seed **per shot**: one that is clean in one shot of a sequence can be a glitchy mess in the next `[community — re-verify]` |
| LoRA weight | Turbo LoRA at **1.0** with 6–8 steps and the `beta` scheduler, per its authors; **0.8–0.85** is a widely repeated counter-tip `[contested]` |

### Frame count and resolution — two rules the UI hides

**Frame count must satisfy `frames ≡ 5 (mod 17)`**, which is why the shipped defaults look arbitrary: **73** (≈3 s) and **124** (≈5 s) are both `17n + 5`, and 362 (≈15 s) is the documented maximum. Type a round number and you are off the lattice the templates guarantee. **Resolution** comes from a megapixel dial snapped to multiples of 32 — remember **0.98 MP = 1344 × 768** (the conditioning default, and what "short side 768" means) and **0.2 MP = 608 × 352** (the draft size). Formula, valid frame counts and the full fourteen-row table: `references/setup-and-workflows.md §3–4`.

**Resolution is a reliability dial, not just a cost dial**, and that is the part that changes how you work: errors are reported to rise at *both* ends, with around **0.8 MP** the sweet spot for complex actions holding together and more small mistakes above *and* below it. `[community — nsfwVariant]` So **draft at 0.2 MP** — timing, shot order and whether the model understood the brief are all legible at 608×352 in a few minutes `[community — GrayingGamer]` — and when one specific thing keeps breaking, raise steps before you raise resolution.

### FL2VA

Nothing connected → `t2va`. `first_frame`, `last_frame`, or both → `fl2va`. The non-obvious part: **a supplied frame is a strong guide, not a copy** — the model adjusts it to match the prompt rather than reproducing it. When you need it held, say so in the prompt (*"The scene begins with `<Picture 1>` as the first frame at 00:00.000"*) and add a retention block if that is not enough. `[community — nsfwVariant]` This is also the mode the Turbo LoRA was trained against, so it is where the speed recipes are best attested.

### Ref2VA

Same chain, plus a `match` parameter and a reference budget: ≤ 9 images, ≤ 3 video clips, ≤ 3 audio clips, ≤ 12 files, ≤ 15 s total — and reference *pixel size* acts as a weight, allocation table in `references/setup-and-workflows.md §5`. Two settings deltas worth trying rather than adopting, one report each: **`ref_image_size = MAX`** latches a face more reliably than the default `match`, and **12–15 steps** latch better than 20. `[community — single report; re-verify]` Run the hybrid checkpoint unless you have a reason not to — plain Ref2VA is the mode with the quality gap.

---

## H3 directs itself — the default look, the default cuts, the default drift

Every model has defaults it applies when you say nothing. H3's are unusual in kind, because H3 is not just rendering a shot — it is **directing a scene**. Left alone it picks the cuts, the pacing, the camera move and the score. So the signature technique for this model is not a lighting trick or a negative prompt; it is **taking each of those decisions away from it explicitly**, because an unstated decision here is not a neutral one.

Four defaults, in the order they bite:

1. **It cuts.** "Random cuts I didn't ask for" is one of the most-repeated complaints about H3, and it is not a bug: hand it several beats with no shot structure and it invents its own edit. The override is the `[Shot N]` structure with `mm:ss.000` timestamps. Omit the timestamps and the model still chooses when to cut (often fine); supply them and you own the pacing — never timestamp the first shot. `[community — GrayingGamer]`
2. **The camera drifts.** With no camera instruction, expect slow movement rather than a locked-off frame. Write `static shot` when you want none — and name the move when you want one, because "the camera" left unqualified is a wandering handheld.
3. **It stages sequentially.** Two actions joined by "and" happen one *after* the other. Use **"while"** for simultaneous, **"then"** for sequential. The tell is subtle — awkward staggering that reads as bad animation rather than as a misread prompt — which is why it goes undiagnosed for so long. `[community — nsfwVariant]`
4. **It scores the scene.** The sharpest of the four, and it is the one rule above: unspecified sound is invented, not absent.

**On the picture itself,** the lever is the same one the encoder gives you. Qwen3-VL parses the prompt as language, so the medium and the grade move the render when you state them as a **leading clause** — the prompts circulating with the best-looking output open with something like *"Live-action film footage, professionally colour graded, slightly desaturated for a premium film feel"* before a single subject is named. What H3's *un-steered* render default actually looks like has not been characterised by anyone testing it systematically, so treat that clause as the lever rather than as a description of what you get without it. `[flagged — re-verify]`

Seen from the other side, this is the model's real strength: a properly formatted H3 prompt reads like a **shooting script**, and it is the first model in this suite where writing one like a director — blocking, beats, timings, sound — actually pays off rather than being ignored. `[community — GrayingGamer]`

---

## Going faster — the acceleration stack

H3 is slow enough that acceleration is not optional, and the community built **four independent layers** that compose: the runtime, a sparse-attention node, Spectrum's step-skipping, and the Turbo LoRA. Benchmarks, repo names and wiring order for all four are in `references/setup-and-workflows.md §9`. What stays here is the part that fails **silently** — every layer below can look like it is working while costing you most of the speed or quietly corrupting the audio.

**The default:** fix the runtime first, then add the SLA node, then the official lightx2v Turbo LoRA at 6–8 steps with the `beta` scheduler. Add Spectrum when you need more, and turn it off for a keeper — it is an approximation, and fine detail deviates.

| Trap | What you see | What to do |
|---|---|---|
| **ComfyUI not on CU130** | INT8 ConvRot never engages, *even with the INT8 loader wired up*. One user went 12–13 min → 4 min by fixing only this | Startup log must read `pytorch version: 2.13.0+cu130`; otherwise INT8 is decorative `[community — AI-imagine]` |
| **`comfy-kitchen` below 0.2.26** | One `cannot import name 'TensorCoreConvRotW4A4Layout'` ERROR buried in startup, then ComfyUI runs normally — just slower | Update, and check this **before** benchmarking anything `[community — DeliciousGorilla]` |
| **The templates' `nvfp4` encoder on a pre-Blackwell card** | No hardware path, silent fallback | Use `qwen3vl_32b_minimax_h3_int8_convrot` on 30/40-series |
| **SageAttention via the launch flag** | Pure noise — so people disable Sage entirely and lose ~20% | Apply it through KJNodes **`Patch Sage Attention`** set to `auto` `[community — DeliciousGorilla]` |
| **SLA node not last in the chain** | It made things *slower*, or quality dropped | Attach it directly to the guider and scheduler; never stack a cache node with it. Effectively every complaint about the node traces here |
| **Spectrum with audio blending on** | Picture fine; speech tripped, doubled or distorted — worst with reference audio | `audio_blend_weight = 0.0` **and** `offline_smoothing_replay = true` (v0.2.1+) |
| **Turbo LoRA at stock sampler settings** | Blurry mess | The LoRA wants **6–8 steps and `beta`**, not 20 and `simple` |

**The Turbo LoRA's audio tax has already been fixed in core — if you read elsewhere that the fix is still pending, that advice is out of date.** H3 runs **separate video and audio scheduling**, which the sampler chain originally mishandled once the LoRA compressed the step count: picture fine, audio degraded. Kijai's `Comfy-Org/ComfyUI#15243` merged **2026-08-06** and shipped in **ComfyUI v0.31.0 (2026-08-08)**, adding `ModelSamplingAV` / `ModelSamplingMiniMaxH3` with a separate **`audio_shift`** that lets stochastic samplers and low step counts carry audio correctly. `[official — Comfy-Org/ComfyUI#15243, ComfyUI v0.31.0]` So: **update ComfyUI to ≥ v0.31.0 and use the core `ModelSamplingMiniMaxH3` node** `[community — re-verify the exact stock-graph wiring]`; on an install you cannot update, larryvrh's `github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo` sampler is the fallback it was written to be; failing both, ~10 steps with `euler` rather than `res_multistep`. `[community — contested]`

**Contested:** whether the Turbo LoRA is worth it at all. Some named users report visible artefacts and prefer the stock path at ~15 steps; another reports 10 steps + EasyCache beating it on both counts. Treat 6-step generation as a draft mode and validate keepers on the full path. `[contested]`

---

## Beyond one clip — three modes the templates do not show you

The stock templates make H3 look like a 4–15 second clip generator. It is being used for three other jobs, all of them the reference machinery pointed somewhere new. Each is named here with the trap that makes it fail *quietly*; the mechanics live in the references.

**Long-form: context chaining.** `Comfyui-H3--Motion-Context` (Nikodemon), usually run as the fork `ethanfel/ComfyUI-MiniMaxH3-Contex-Loop`, carries **22 frames of the previous clip** forward as context and concatenates accepted clips **with their audio**, checkpointing each one. Minute-plus continuous video is routine (~10 min per 15 s clip at 1.5 MP on a 5090). What it changes is what you *write*, not what you set: end every scene on a **still beat** so its last frame connects to the next scene's first, and describe every other character in every scene's prompt to stop bleed. Scene-planning rules in full: `references/setup-and-workflows.md §7`.

**H3 as a single-image edit model.** Generate **one frame** and it becomes an image editor — reported to beat Krea 2 + Identity Edit, Qwen-Image-Edit and Flux Klein 9B on character fidelity, 3D scenes, mirrors and composition, at ~8 s per edit on a 5090 `[community — Patient_Ratio4177]`. Two requirements, both of which fail silently rather than erroring: **use the dedicated image VAE** (`Mamad8/MiniMax-H3-Image-VAE` — the video VAE gives soft, plausible-looking stills, and generating 5 frames to pick one does not fix it), and **generate exactly 1 frame** (the image VAE grids at 5; ComfyUI's old 5-frame minimum, `Comfy-Org/ComfyUI#15644`, is lifted in recent nightlies, so update rather than patching `comfy_extras/nodes_minimax_h3.py`). Settings: `references/setup-and-workflows.md §8`. This is why [`image-production-workflows`](../image-production-workflows/) now treats a video model as a stage in an image pipeline.

**Video editing — replacing a character in existing footage.** Ref2VA will swap the person in a clip if the prompt is in the shape the official reference guide's keywords expect, and guessing that shape does not work. The finding that matters, from 400+ generations: **`retention_analysis` is the load-bearing block and `detailed_description` barely matters** — describing the action had no measurable effect. `[community — Darqsat]` `[video editing]` and `[audio reuse]` are **pre-trained summary keywords**, not free text, and `[audio reuse]` **re-renders** the audio rather than copying it. Worked template and failure conditions: `references/prompting-guide.md §7`. Where exact motion transfer is the point, this is the wrong tool — see [Where MiniMax H3 sits in the suite](#where-minimax-h3-sits-in-the-suite).

---

## Production pipelines & mixing models

Local H3 output is 768p **with a 32 kHz stereo track attached**, and every stage you add afterwards is a chance to lose one of those two things. The ladder:

1. **Draft** at 0.2 MP and a short frame count — timing, shot order, and the soundscape, which is as much a thing to iterate as the picture. Skippable only for a prompt you have run before.
2. **Render** at 0.98 MP (1344 × 768) with the final frame count. Not bypassable; this is the keeper.
3. **Restore or upscale** — *optional* — with a **temporally-aware** restorer (SeedVR2, FlashVSR), not a per-frame image upscaler. `ReDetail` is the generative alternative, re-rendering the clip through the [`ltx-2-5`](../ltx-2-5/) upscaler and inventing detail rather than recovering it; its constraints and measurements belong to [`image-production-workflows`](../image-production-workflows/). **The one that bites here is audio:** ReDetail refuses a silent clip, so it works on H3 output straight out of the box and fails on the same clip after any stage that dropped the track.
4. **Interpolate** for a higher frame rate — *optional*, and always **after** the restore. The ordering rule and why it holds are [`image-production-workflows`](../image-production-workflows/)'s. H3's wrinkle: interpolators are almost all picture-only, so this is usually the step that eats the audio.
5. **Re-mux the audio.** Not optional, unless you have verified that every stage above preserved it.

**The handoff between stages is pixels, not latents.** H3's single latent stream is decoded by two VAEs into a picture stream and an audio stream, and nothing downstream of `CreateVideo` shares that latent space — so every stage after step 2 is a pixel-level tool operating on a decoded file. That is what makes step 5 necessary, and it is also what makes H3 mixable at all: a still locked with any image skill can drive FL2VA, and H3's output can enter any video post chain.

Cross-model production craft is in [`image-production-workflows`](../image-production-workflows/), and [`wan-2-2`](../wan-2-2/) covers the same video ladder in more depth. Per-stage settings and ReDetail's VRAM and timing numbers: `references/setup-and-workflows.md §6`.

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| Video generates, output is silent | Audio VAE or `VAEDecodeAudio` not wired; audio branch missing from `CreateVideo` | Load **both** VAEs and both decode nodes — this is the most common H3 setup error |
| **Video looks fine after an upscale or interpolation pass, but the audio is gone** | Most ComfyUI post and upscale nodes are picture-only and **discard the audio track silently** — no warning, no error, just a video file that plays mute | Verify each post stage preserves audio, or keep the raw output and **re-mux at the end**. This is the commonest way to lose H3's whole point in post |
| **Picture fine, audio garbled or broken — with the Turbo LoRA on** | H3 schedules video and audio **separately**; the pre-v0.31.0 sampler chain mishandled that once the LoRA compressed the step count | Update ComfyUI to **≥ v0.31.0** and use the core `ModelSamplingMiniMaxH3` node's `audio_shift` (PR #15243, merged 2026-08-06); larryvrh's sampler node on older installs; or raise to ~10 steps with `euler` |
| Audio present but generic/wrong | Prompt described picture only, so the soundscape was unspecified rather than silent | Name dialogue, SFX and music explicitly; *"no music"* when you want none |
| Blurry mess with the Turbo LoRA loaded | Step count or scheduler left at stock values — the LoRA wants **6–8 steps and the `beta` scheduler**, not 20 and `simple` | Match all of steps, scheduler and strength to the LoRA's recipe, not just steps |
| Swapped in an abliterated encoder, output got worse | Perturbed hidden states relative to training; there is no refusal path in the encoder to remove | Restore the official encoder — use abliterated models only for prompt *expansion* |
| Anatomy melts on explicit content | Training-data gaps, not refusal — this is not censorship you can unlock | Supply reference images; no encoder swap will fix it |
| Local results far below the launch demos | Demos run through **H3-Context-IR**, which is not in the open release | Approximate it — see the prompting guide's Context-IR section — or use the API for parity |
| Can't reach 2K locally | **H3-Regenerate-2K is not open** | 768p is the local ceiling; upscale externally or use the API |
| Frame count rejected or output length odd | Frame count not on the `17n + 5` lattice | Use the template formula |
| Out-of-memory on a large card | Non-pruned BF16 weights plus a BF16 32B encoder | Use `pruned_int8_convrot` + `nvfp4_awq` as the templates do |
| Fine-tuning fails on a `pruned` build | Pruned builds omit AdaLN-branch parameters and are inference-only | Take a non-pruned checkpoint |
| Negative prompt has no effect | Stock graph uses `BasicGuider` — guidance-free, no negative path | Phrase positively |
| Dialogue in the wrong language | 11 languages supported but the target was not named | State the language explicitly inside the `<d>` tag |
| **Generation is absurdly slow despite INT8 weights and the INT8 loader** | ComfyUI not on **CU130**, or `comfy-kitchen` < 0.2.26 failing to import `TensorCoreConvRotW4A4Layout` — both fail *quietly* | Check the startup log for `+cu130` and for that one ERROR line — see the acceleration traps above |
| Ref2VA output visibly worse than FL2VA at the same settings | Real, and localised to the `adaln_proj` tensors | Use a **hybrid b30-49 / b25-49** checkpoint or the hybrid loader node |
| Speech trips, doubles syllables or sounds distorted **with Spectrum on** | Forecast video features re-enter joint attention and corrupt the audio through it | `audio_blend_weight = 0.0` **and** `offline_smoothing_replay = true` (v0.2.1+); mechanism in `setup-and-workflows.md §9` |
| SLA node made it *slower*, or quality dropped | The node is not last in the chain, or a cache node is stacked with it | Attach it directly to the guider/scheduler; remove cache nodes |
| Actions happen one after another when they should overlap | H3 assumes **sequential** order unless told otherwise — "and" is ambiguous to it | Use **"while"** for simultaneous, **"then"** for sequential |
| Clothing or props phase through limbs | Under-described mechanics in a physically fiddly action | Spell out the path in gratuitous detail, and give the action ≥3 s |
| Character sheet's white background bleeds into the shot | Common with hybrid checkpoints fed a sheet on white | Matte the sheet, or state the environment explicitly |
| Single-frame image edits come out blurry or gridded | Wrong VAE, or more than one frame | `Mamad8/MiniMax-H3-Image-VAE` **and** exactly 1 frame |

---

## Pre-flight checklist

0. **Deploying on rented GPUs?** Volume carries all five files including **both** VAEs; downloads done on a CPU pod; pod created with a termination guard. See [`comfyui-on-runpod`](../comfyui-on-runpod/).
1. **Checked the licence territory** and satisfied yourself you are covered — including the **datacenter region** if you are renting?
1a. **ComfyUI ≥ v0.31.0** (for the core audio-scheduling fix), **startup log says `+cu130`**, and `comfy-kitchen` is 0.2.26+? Everything below is wasted otherwise.
2. Right checkpoint — FL2VA for text/first-last-frame, Ref2VA for multi-reference, **hybrid b30-49 if you want both**?
3. **Both VAEs loaded and both decode nodes wired**, including `VAEDecodeAudio`?
4. CLIPLoader type set to **`minimax`**?
5. Prompt describes **dialogue, SFX and music**, not just picture — and marks simultaneous actions with "while" rather than "and"?
5a. Drafted at **0.2 MP** to check timing before committing to the long run?
6. Frame count on the **`17n + 5`** lattice?
7. Resolution taken from the megapixel table, dimensions multiples of 32?
8. Using a **pruned** build for inference, a **non-pruned** one if you intend to train?
9. Accepted that local output is **768p** and the demos used a module you do not have?
10. Post chain, if any: restore **before** you interpolate, and **audio re-muxed** at the end — did you check the track survived?
11. Commercial use: displaying "MiniMax H3" in the UI, and under the $20M threshold?

---

## Where MiniMax H3 sits in the suite

| Job | MiniMax H3 | Reach for instead |
|---|---|---|
| **Usable under a permissive licence worldwide** | ❌ **Excludes US/EU/UK/KR** | **[`wan-2-2`](../wan-2-2/)** — Apache 2.0, no territory clause |
| Video with synchronised dialogue/SFX/music | **The reason to be here.** Joint audio-video in one pass | [`ltx-2-5`](../ltx-2-5/) also does native audio, under a **$10M-revenue** commercial gate plus an **NSFW prohibition** and a no-compete clause — a different shape of risk from H3's territory exclusion, not a milder one |
| Carrying a reference *voice* or sound into output | Ref2VA accepts reference audio — unique in this suite | — |
| Lip-sync to an existing audio track | Not its shape; it generates audio rather than following one | [`wan-2-2`](../wan-2-2/) S2V consumes an audio track for lip-sync |
| Motion/camera/pose control rigs | Thin — no ControlNet-equivalent stack documented | [`wan-2-2`](../wan-2-2/) — Fun Camera/Control/InP, VACE, Animate |
| **Exact motion transfer** — replacing a person in footage while following the driving movement frame for frame | **Approximate.** The `[video editing]` recipe above swaps a character convincingly, but it re-generates the motion rather than tracking it | **SCAIL-2** (Z.ai) — a full fine-tune of the Wan2.1-14B-I2V weights with SAM3 identity tracking, built for exactly this job — see [`scail-2`](../scail-2/) |
| LoRA ecosystem and training maturity | Very young — Turbo/speed LoRAs exist, training is unsettled | [`wan-2-2`](../wan-2-2/), or [`sdxl`](../sdxl/) on the image side |
| Locking a still before animating | Not an image model | [`z-image`](../z-image/) / [`flux-2`](../flux-2/) / [`krea-2`](../krea-2/) / [`sdxl`](../sdxl/) |
| **Editing a single image** | **Actually good at it** — one-frame generation with the image VAE, see above | [`krea-2`](../krea-2/) Identity Edit for scene-preserving one-sentence edits; Flux Klein 9B / Qwen-Image-Edit otherwise |
| Post chain — upscale, restore, interpolate, 2K | ❌ 2K is a hosted module only; local output is 768p with an audio track most post nodes will drop | Temporally-aware restorers (SeedVR2, FlashVSR), or **ReDetail** re-rendering H3 clips through the [`ltx-2-5`](../ltx-2-5/) upscaler; restore before you interpolate, then re-mux. See [`image-production-workflows`](../image-production-workflows/) |

---

## How to read the claims in this skill — two bars, by claim type

**Hard facts — must be exact or it breaks.** The licence terms and the Excluded Territories list, the licensor and governing law, the three-module open/closed split, the 33B dense single-stream architecture, the Qwen3-VL-32B encoder and its layer-50 tap, the dual video/audio VAE and the `VAEDecodeAudio` node, the CLIPLoader `minimax` type, exact filenames, the `res_multistep`/`simple`/20-step sampler chain, the `17n + 5` frame rule and the megapixel table, the 24 fps / 32 kHz / 4–15 s output specs, and the LTX-2.x licence terms quoted in the comparison above. **Source of truth is official**: the licence file and model card in `MiniMaxAI/MiniMax-H3`, the file list in `Comfy-Org/MiniMax-H3`, and the **official ComfyUI template JSONs read verbatim** — including the embedded author notes, which is where the resolution table and the frame formula actually live. A wrong filename 404s; a misread licence is a legal problem. These are also the **volatile** ones: this model is days old, quant filenames and template details will move, and the two closed modules are promised for later release. **Re-verify before relying on any of it.**

**Craft — what actually makes a good result.** **The authoritative source here is the community**, and three weeks after release a substantial, self-correcting body of it exists: the acceleration stack and its measured numbers, the `adaln_proj` hybrid finding, the Spectrum audio-feedback diagnosis and its two-stage fix, the `retention_analysis` video-edit recipe, the sequential-vs-simultaneous prompting rule, the abliterated-encoder myth debunked by the author of the tool in question, the runtime traps. Those are attributed to named authors and stated with confidence; several are notably good sources, publishing control experiments and saying what they did not test. The remainder — approximating Context-IR, the reference-budget allocation in `characters.md` — is **reasoned from the architecture and the official templates** rather than distilled from thousands of generations, is marked where that is so, and should be treated as provisional in a way the rest of the suite's craft is not.

Points held as unresolved:

- **Whether local H3-Base output can approach the official demos** without Context-IR. The card implies the gap is real; how large it is in practice is not yet established. `[flagged — re-verify]`
- **Whether the Turbo LoRA is worth its artefacts.** Named users disagree: some prefer it at 6–8 steps, others prefer the stock path at ~15 steps or 10 steps + EasyCache. The 0.8–0.85 strength tip cuts across this and is not reconciled with the authors' own 1.0 recipe. `[contested]`
- **LoRA *training*** on H3 — as opposed to using the released speed LoRAs. Speed LoRAs now ship from lightx2v with versioned checkpoints, and detail LoRAs exist, so training clearly works; no public hyperparameter recipe. `[flagged — re-verify]`
- **The diffusers entry point.** The model card carries HF's generic autogenerated snippet, which shows an image call and is unlikely to be the real API. `[flagged — re-verify]`
- **Whether MiniMax's own sparse attention will supersede the community SLA node** when released, and on what terms. `[pending release]`
- **What H3's un-steered render default actually looks like.** Its default *direction* — the invented cuts, the camera drift, the sequential staging — is well attested. The picture default is not: everyone who posts good output states the medium and grade in a leading clause, so nobody has published a clean description of what you get without one. `[flagged — re-verify]`

**Facts dated 2026-08-13; community craft refreshed 2026-08-22** from a sweep of r/StableDiffusion, r/unstable_diffusion and Civitai. Two hard facts were re-checked against primary sources on 2026-08-22 and are recorded above as settled rather than pending: ComfyUI PR #15243 (merged, shipped in v0.31.0) and the LTX-2.x Community License text. The tooling here is weeks old and moving weekly — re-verify node names and recommended checkpoints before relying on them.

---

## Reference files

| File | When to read it |
|---|---|
| `references/licence-and-territory.md` | You are deciding whether you may use the model at all, or shipping something built on it: the licence clause by clause — Applicable/Excluded Territory, Exhibit A prohibited uses, the $20M threshold and attribution duty, redistribution and NOTICE mechanics, governing law, the separately-licensed encoder, and how the alternatives' licences differ |
| `references/prompting-guide.md` | You are writing or fixing a prompt: soundscape vocabulary, dialogue formatting and language selection, camera language, approximating H3-Context-IR locally, worked examples **including the video-editing template (§7)**, ordering and timestamp craft, prompt tooling |
| `references/setup-and-workflows.md` | You are wiring or debugging the graph: both VAE branches node by node, the quantised build matrix and VRAM, the frame formula and full megapixel table, FL2VA vs Ref2VA wiring and reference sizing, the production ladder, **the four acceleration layers with their benchmarks (§9)**, and the abliterated-encoder argument in full (§10) |
| `references/characters.md` | You need the same face — or voice — across shots: Ref2VA multi-reference conditioning, the still-first handoff from the image skills, and what H3 cannot yet do that [`wan-2-2`](../wan-2-2/) can |
| `references/lora-training.md` | You are about to train on H3, or want to know whether you can: the young LoRA ecosystem, pruned-vs-full checkpoints, and an honest account of what is not yet known |
