---
name: minimax-h3
description: >
  Authoritative guide for MiniMax H3, the open-weights omni-modal video-with-native-audio model (MiniMax / Nanonoble Pte. Ltd., released 2 August 2026), in ComfyUI or diffusers. **Read the licence section first: the MiniMax H3 Community License excludes the United States, the European Union, the United Kingdom and South Korea from its Applicable Territory, and use outside that territory is an explicitly prohibited use.** Use this whenever the user touches MiniMax H3 in any way, even obliquely: asking whether they may legally use it at all, choosing between the FL2VA and Ref2VA checkpoints, installing it in ComfyUI (the dual video+audio VAE, the two decode nodes, the Qwen3-VL-32B encoder, quantised builds, VRAM), writing prompts (the prompt drives dialogue, sound effects and music as well as picture — that is the whole point of the model), hitting the frame-count rule, picking resolution from the megapixel table, generating video with synchronised stereo audio, first/last-frame and multi-reference conditioning, understanding what is *not* in the open release (Context-IR and Regenerate-2K are hosted-only, so local output is 768p and 2K is API-only), debugging audio/video desync or artefacts, or comparing it against Wan 2.2 and LTX-2.5. Also covers who should reach for something else instead — which, on licence grounds, is a large share of readers.
---

# MiniMax H3

MiniMax H3 is a **33B-parameter dense, single-stream omni-modal transformer** from MiniMax (licensor: **Nanonoble Pte. Ltd.**), released **2 August 2026**. It jointly understands text, images, video and audio, and generates **video with native 32 kHz stereo audio** — voice, sound effects and music modelled together with the picture in a single forward pass, not layered on afterwards. Output runs to 24 fps, 4–15 seconds, and up to 2K. The text encoder is the full **Qwen3-VL-32B** (hidden states taken from its 50th layer).

**The defining trait:** it is the first widely-adopted open-weights model where **sound is part of the generation, not a separate stage**. Everything else about how you use it follows from that.

**The defining constraint:** the licence does not cover the US, EU, UK or South Korea. That is not a footnote — see below, and settle it before you download anything.

---

## Before anything else — the licence and the territory

This section leads because it is the fact most likely to matter to you, and it is the one the launch coverage almost universally omits.

**MiniMax H3 Community License Agreement**, licence date 2 August 2026, licensor **Nanonoble Pte. Ltd.**, governed by the law of **Hong Kong SAR** with exclusive jurisdiction in Hong Kong courts. [official — repo `LICENSE`]

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

**If you are in an excluded territory**, the practical routes are: use the **hosted API/app** under whatever terms govern those (a separate agreement from this one — check it); or reach for a model whose licence covers you — **[`wan-2-2`](../wan-2-2/)** is **Apache 2.0**, worldwide, commercial use included, and is the strongest open video model without a territory clause. **LTX-2.5** also does native audio, though its licence is gated behind a contact-information agreement and is not verified here.

Two smaller notes: the **encoder is separately licensed** — Qwen3-VL-32B is Apache 2.0 [official — licence "Additional Note"]. And MiniMax runs **automated moderation** on submitted text, images and video, which does not alter your obligations under the licence.

Full clause-by-clause treatment, the Exhibit A list, and the redistribution mechanics: **`references/licence-and-territory.md`**.

---

## What "open weights" means here — one module of three

The complete H3 system is three modules. **Two of them are not in the open release.** [official — model card]

| Module | What it does | Open? |
|---|---|---|
| **H3-Context-IR** | Preprocesses free-form multimodal input into the structured representation H3-Base consumes. The card calls it *"critical to the quality of the final output"* | ❌ **Hosted only.** An API reproduces the official workflow |
| **H3-Base** | The generator. Produces 768p video + stereo audio | ✅ **This is what you download** |
| **H3-Regenerate-2K** | Regenerates the 768p result in-context at 2K | ❌ **Not open.** *"We will release it once it is ready"* |

Two consequences worth internalising before you judge the model:

1. **Local output is 768p.** The 2K figure in the marketing is the API path. You can upscale by other means, but that is not what produces MiniMax's own 2K samples.
2. **Your prompt handling is not theirs.** Official demos run through Context-IR. Running H3-Base on a raw prompt is a different pipeline, and the gap is the reason local results often look weaker than the launch reel. The card's "Prompting Guidance" exists precisely so you can approximate Context-IR yourself — see `references/prompting-guide.md`.

The **sparse-attention implementation is also withheld** from this release; open inference is full-attention only, with sparse attention promised "in a future update." That is a speed and context-length ceiling, not a quality one.

---

## Task-mode selector

H3 ships as **two task-specific checkpoints**, both BF16, each bundling its own processor, tokenizer, text encoder and VAEs.

| Checkpoint | Tasks | Inputs | ComfyUI node |
|---|---|---|---|
| **FL2VA** | `t2va` (text→audio-video), `fl2va` (first/last-frame→audio-video) | Text; **zero, one or two** images — none = T2V, one = first *or* last frame, two = both | `MiniMaxH3ImageToVideo` |
| **Ref2VA** | `ref2va` (omni-reference) | ≤ 9 images, ≤ 3 video clips (2–15 s each), ≤ 3 audio clips (2–15 s each), **≤ 12 files total**, total ≤ 15 s | `MiniMaxH3ReferenceToVideo` |

**One node covers three modes.** `MiniMaxH3ImageToVideo` is T2V when nothing is connected and FLF2V when you attach frames — there is no separate text-to-video node, which surprises people looking for one.

**Ref2VA is the genuinely unusual capability.** Passing reference *audio* alongside reference images and video is something nothing else in this suite can do — it is how you carry a voice or a musical texture into the output rather than merely describing it.

| Output spec | Value |
|---|---|
| Duration | 4–15 s |
| Frame rate | **24 fps** |
| Audio | **32 kHz stereo** |
| Resolution | short side 768 by default; 2K only via the hosted Regenerate-2K |
| Aspect ratios | wide range — 21:9, 16:9, 4:3, 1:1, 3:4, 9:16 and others |
| Dialogue languages | 11 stable: Arabic, Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian, Spanish |

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

> **The official templates ship quantised by default** — `pruned_int8_convrot` weights and an `nvfp4_awq` encoder. That is a statement about memory pressure: 33B of transformer plus a 32B VLM encoder is a lot to hold. The **`pruned`** builds drop the ~13B of AdaLN-branch parameters that can be precomputed and cached — they are **inference-only**, so take a non-pruned build if you intend to fine-tune.

### Sampling

H3 uses the **custom sampler chain**, not `KSampler`:

`RandomNoise` → `BasicGuider` → `KSamplerSelect` → `BasicScheduler` → `SamplerCustomAdvanced`

Template values, verbatim: sampler **`res_multistep`**, scheduler **`simple`**, **20 steps**, denoise **1.0**. Note it wires `BasicGuider`, not `CFGGuider` — **the stock graph is guidance-free and has no negative prompt path**. Phrase constraints positively.

### Do not swap in a "heretic" / abliterated text encoder

A myth spread fast enough after release that a popular Docker template shipped it: that replacing the Qwen3-VL encoder with an abliterated ("heretic") build uncensors the output. **It does not**, per the author of Heretic itself:

> Abliteration works by directional ablation on the residual stream so the LLM stops *refusing*. But LLMs already represent "harmful" inputs accurately — that is how they know to refuse in the first place. So the hidden states reaching the transformer are not clearer, they are **perturbed relative to what the model was trained on**, which costs prompt adherence and can add artefacts. `[community — -p-e-w-, author of Heretic]`

Corroborating detail from the same thread: the Qwen3-VL build shipped for H3 is **~8 GB smaller than stock because the output layers are absent** — refusal lives in those layers, and only hidden states are needed here. There is no refusal path in the encoder to remove. `[community — re-verify]`

**Where abliterated models *are* useful: prompt expansion**, which is a separate stage *before* the encoder. An LLM asked to enhance a prompt can refuse outright, and an uncensored one won't — the Heretic author agrees this use is legitimate. Keep the two stages distinct: **abliterated model for expansion, official encoder for generation.**

This matters beyond H3. The confusion largely comes from ComfyUI subgraphs wiring **the same LLM** into both the prompt-expander and the text-encode node, so swapping it to fix a refusing expander silently changes the encoder too — which is exactly the shape of [`krea-2`'s](../krea-2/) enhancer problem.

**Also worth knowing:** community consensus is that H3 does not meaningfully refuse anything — reported anatomy failures are attributed to **training-data gaps, not filtering**, and supplying reference images reportedly fixes much of it. `[community — re-verify]`

### diffusers

`DiffusionPipeline.from_pretrained("MiniMaxAI/MiniMax-H3", dtype=torch.bfloat16)`. The card's snippet is HF's generic autogenerated one and shows an *image* call — treat it as a placeholder and check the current pipeline class before relying on it. `[flagged — re-verify]`

---

## Going faster — the Turbo LoRA, and what it costs the audio

A speed LoRA landed within days and is now the standard acceleration path. Original by **larryvrh**; ComfyUI-compatible conversions by **drbaph** (`drbaph/MiniMax-H3-Turbo-Lora-ComfyUI`).

| Setting | Value `[community — Organix33/drbaph]` |
|---|---|
| Recommended build | `minimax_h3_turbo_v4_step600_ema_pruned_comfyui.safetensors` |
| Steps | **6–8** (down from 20) |
| Sampler | `euler` **or** `res_multistep` |
| Scheduler | **`beta`** — note this differs from the stock template's `simple` |
| LoRA strength | **1.0** |

It works across the quantised builds (int8, convrot, pruned, fp8), and although it was trained against the **FL2VA** checkpoint it is reported to work on **Ref2VA** too — the first evidence that weights transfer between the two task checkpoints.

**The tax is audio, and it is specific to this model.** H3 runs **separate video and audio scheduling**, and the stock sampler chain does not handle that correctly once the Turbo LoRA compresses the step count — so audio degrades or breaks at low steps while the picture still looks fine. Three responses, in order of preference:

1. **Use larryvrh's dedicated sampler** — `github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo` ships a Turbo sampler built around H3's split video/audio scheduling specifically to fix this.
2. **Watch for the core fix.** A Kijai PR against ComfyUI (`Comfy-Org/ComfyUI#15243`) addresses the audio path; once merged the custom node may become unnecessary. `[flagged — re-verify]`
3. **Raise the step count.** Audio is reported acceptable at ~10 steps and poor at 6 on the stock chain — and `euler` is reported to handle audio noticeably better than `res_multistep`. `[community — contested]`

**Contested:** whether the Turbo LoRA is worth it at all. Some named users report visible artefacts and prefer simply dropping the stock path to ~15 steps; another reports 10 steps + EasyCache beating it on both speed and quality. Treat 6-step generation as a draft mode and validate keepers on the full path. `[contested]`

**Preview decoding:** a tiny VAE exists — `Kijai/MiniMax-H3-TAE` (`taeh3.safetensors`) → `ComfyUI/models/vae_approx/`. Core does not yet use it for final decode, so it is a preview accelerator via custom node rather than a substitute for the real VAE. `[community — re-verify]`

---

## Frame count and resolution — two rules the UI hides

**Frame count must satisfy `frames ≡ 5 (mod 17)`.** The official templates compute it from a duration in seconds with this expression:

```
max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17     # a = seconds
```

Which is why the shipped defaults look arbitrary: **73** frames (≈3 s) and **124** frames (≈5 s). Both are `17n + 5`. Set a frame count off that lattice and you are outside what the template guarantees — use the formula rather than typing a round number.

**Resolution comes from a megapixel dial**, snapped to a multiple of 32. From the template's own table (16:9):

| MP | 0.2 | 0.4 | 0.6 | 0.8 | 0.98 | 1.2 | 1.5 | 2.0 |
|---|---|---|---|---|---|---|---|---|
| **Size** | 608×352 | 864×480 | 1056×608 | 1216×672 | **1344×768** | 1504×832 | 1664×928 | 1920×1088 |

The conditioning nodes default to **1344×768** — the 0.98 MP row, which is the "short side 768" spec.

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| Video generates, output is silent | Audio VAE or `VAEDecodeAudio` not wired; audio branch missing from `CreateVideo` | Load **both** VAEs and both decode nodes — this is the most common H3 setup error |
| **Picture fine, audio garbled or broken — with the Turbo LoRA on** | H3 schedules video and audio **separately**; the stock sampler chain mishandles that once the LoRA compresses the step count | larryvrh's Turbo sampler node; or raise to ~10 steps; or use `euler` over `res_multistep`; watch ComfyUI PR #15243 |
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
| Dialogue in the wrong language | 11 languages supported but the target was not named | State the language explicitly |

---

## Pre-flight checklist

0. **Deploying on rented GPUs?** Volume carries all five files including **both** VAEs; downloads done on a CPU pod; pod created with a termination guard. See [`comfyui-on-runpod`](../comfyui-on-runpod/).
1. **Checked the licence territory** and satisfied yourself you are covered — including the **datacenter region** if you are renting?
2. Right checkpoint — FL2VA for text/first-last-frame, Ref2VA for multi-reference?
3. **Both VAEs loaded and both decode nodes wired**, including `VAEDecodeAudio`?
4. CLIPLoader type set to **`minimax`**?
5. Prompt describes **dialogue, SFX and music**, not just picture?
6. Frame count on the **`17n + 5`** lattice?
7. Resolution taken from the megapixel table, dimensions multiples of 32?
8. Using a **pruned** build for inference, a **non-pruned** one if you intend to train?
9. Accepted that local output is **768p** and the demos used a module you do not have?
10. Commercial use: displaying "MiniMax H3" in the UI, and under the $20M threshold?

---

## Where MiniMax H3 sits in the suite

| Job | MiniMax H3 | Reach for instead |
|---|---|---|
| **Usable under a permissive licence worldwide** | ❌ **Excludes US/EU/UK/KR** | **[`wan-2-2`](../wan-2-2/)** — Apache 2.0, no territory clause |
| Video with synchronised dialogue/SFX/music | **The reason to be here.** Joint audio-video in one pass | LTX-2.5 also does native audio (gated licence, unverified here) |
| Carrying a reference *voice* or sound into output | Ref2VA accepts reference audio — unique in this suite | — |
| Lip-sync to an existing audio track | Not its shape; it generates audio rather than following one | [`wan-2-2`](../wan-2-2/) S2V consumes an audio track for lip-sync |
| Motion/camera/pose control rigs | Thin — no ControlNet-equivalent stack documented | [`wan-2-2`](../wan-2-2/) — Fun Camera/Control/InP, VACE, Animate |
| LoRA ecosystem and training maturity | Very young — Turbo/speed LoRAs exist, training is unsettled | [`wan-2-2`](../wan-2-2/), or [`sdxl`](../sdxl/) on the image side |
| Locking a still before animating | Not an image model | [`z-image`](../z-image/) / [`flux-2`](../flux-2/) / [`krea-2`](../krea-2/) / [`sdxl`](../sdxl/) |
| 2K output locally | ❌ hosted module only | Upscale externally; see [`image-production-workflows`](../image-production-workflows/) |

---

## How to read the claims in this skill — two bars, by claim type

**Hard facts — must be exact or it breaks.** The licence terms and the Excluded Territories list, the licensor and governing law, the three-module open/closed split, the 33B dense single-stream architecture, the Qwen3-VL-32B encoder and its layer-50 tap, the dual video/audio VAE and the `VAEDecodeAudio` node, the CLIPLoader `minimax` type, exact filenames, the `res_multistep`/`simple`/20-step sampler chain, the `17n + 5` frame rule and the megapixel table, and the 24 fps / 32 kHz / 4–15 s output specs. **Source of truth is official**: the licence file and model card in `MiniMaxAI/MiniMax-H3`, the file list in `Comfy-Org/MiniMax-H3`, and the **official ComfyUI template JSONs read verbatim** — including the embedded author notes, which is where the resolution table and the frame formula actually live. A wrong filename 404s; a misread licence is a legal problem. These are also the **volatile** ones: this model is days old, quant filenames and template details will move, and the two closed modules are promised for later release. **Re-verify before relying on any of it.**

**Craft — what actually makes a good result.** **The authoritative source here is the community**, and unusually for a model this young a real body of it already exists: the Turbo LoRA recipe and its `beta` scheduler, the split video/audio scheduling failure and its fixes, the abliterated-encoder myth debunked by the author of the tool in question, the VRAM reports. Those are attributed to named authors and are stated with confidence.

The rest — how to write the audio half of a prompt, how to approximate Context-IR, the reference-budget allocation in `characters.md` — is still **reasoned from the architecture and the official templates** rather than distilled from thousands of generations, and is marked where that is so. Treat *that* half as provisional in a way the rest of the suite's craft is not.

Points held as unresolved:

- **Whether local H3-Base output can approach the official demos** without Context-IR. The card implies the gap is real; how large it is in practice is not yet established. `[flagged — re-verify]`
- **Whether the Turbo LoRA is worth its artefacts.** Named users disagree: some prefer it at 6–8 steps, others prefer the stock path at ~15 steps or 10 steps + EasyCache. `[contested]`
- **LoRA *training*** on H3 — as opposed to using the released speed LoRAs. No trainer support story or hyperparameter consensus yet. `[flagged — re-verify]`
- **The diffusers entry point.** The model card carries HF's generic autogenerated snippet, which shows an image call and is unlikely to be the real API. `[flagged — re-verify]`
- **LTX-2.5's licence**, referenced above as an alternative, is **gated** behind a contact-information agreement and was **not read** for this skill. Do not treat the comparison as a licence clearance. `[flagged — re-verify]`

**Dated 2026-08-13**, eleven days after release. Nothing here has aged into reliability yet.

---

## Reference files

| File | When to read it |
|---|---|
| `references/licence-and-territory.md` | The licence clause by clause: Applicable/Excluded Territory, Exhibit A prohibited uses, the $20M threshold and attribution duty, redistribution and NOTICE mechanics, governing law, and the separately-licensed encoder |
| `references/prompting-guide.md` | Writing the audio and the picture together: soundscape vocabulary, dialogue formatting and language selection, camera language, approximating H3-Context-IR locally, worked examples |
| `references/setup-and-workflows.md` | The graph node by node including both VAE branches; the quantised build matrix and VRAM; the frame-count formula and megapixel table in full; FL2VA vs Ref2VA wiring; production pipeline and the 768p ceiling |
| `references/characters.md` | Identity across frames and shots with Ref2VA multi-reference conditioning, the still-first handoff from the image skills, and what H3 cannot yet do that `wan-2-2` can |
| `references/loras-and-training.md` | The young LoRA ecosystem: Turbo/speed LoRAs in circulation, pruned-vs-full checkpoints for training, and an honest account of what is not yet known |
