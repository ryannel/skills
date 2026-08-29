# MiniMax H3 — setup & workflows

All node settings below come **straight from the official ComfyUI template JSONs** (`Comfy-Org/workflow_templates`: `video_minimax_h3_t2v.json`, `_i2v.json`, `_r2v.json`). That includes the resolution table and the frame formula. Both live in the templates' embedded author notes, not in any docs page.

## Contents

1. [The graph](#1-the-graph)
2. [File layout and builds](#2-file-layout-and-builds)
3. [Frame count](#3-frame-count)
4. [Resolution](#4-resolution)
5. [FL2VA vs Ref2VA wiring](#5-fl2va-vs-ref2va-wiring)
6. [Production pipeline and the 768p ceiling](#6-production-pipeline-and-the-768p-ceiling)
7. [Going long — context chaining](#7-going-long--context-chaining)
8. [Single-frame image editing](#8-single-frame-image-editing)
9. [The acceleration stack, layer by layer](#9-the-acceleration-stack-layer-by-layer)
10. [The abliterated-encoder myth](#10-the-abliterated-encoder-myth)

---

## 1. The graph

The graph requires ComfyUI with H3 support, which landed in **Comfy-Org/ComfyUI PR #15224**.

```
CLIPLoader (qwen3vl_32b_minimax_h3_*, type: minimax) ──> conditioning ─┐
Load Diffusion Model (minimax_h3_{fl2va|ref2va}_*) ───────────────────┤
                                                                       ├─> BasicGuider
RandomNoise ──┐                                                        │
KSamplerSelect (res_multistep) ──┐                                     │
BasicScheduler (simple, 20, 1.0) ─┼──> SamplerCustomAdvanced <─────────┘
                                  │
                                  └──> latent ─┬─> VAEDecode      (video VAE) ─┐
                                               └─> VAEDecodeAudio (audio VAE) ─┴─> CreateVideo (24 fps) ─> SaveVideo
```

**Sampler chain, verbatim:** `KSamplerSelect` = **`res_multistep`**; `BasicScheduler` = **`simple`, 20 steps, denoise 1.0**; guidance via **`BasicGuider`**.

Two things are easy to get wrong here.

**The graph forks at the decode, not before.** One latent goes to two decoders. `VAEDecode` produces the picture and **`VAEDecodeAudio`** produces the sound, and `CreateVideo` recombines them. Every other video model in this suite has a single decode path. If your output is silent, check this branch first.

**Use `BasicGuider`, not `CFGGuider`.** The stock graph is **guidance-free**, so there is no negative-prompt input at all. You have to phrase constraints positively instead. Whether swapping in `CFGGuider` gives useful negative-prompt behaviour is **untested here** `[flagged — re-verify]`.

---

## 2. File layout and builds

The files come from `Comfy-Org/MiniMax-H3`.

| File | Folder | Loader |
|---|---|---|
| `minimax_h3_fl2va_*.safetensors` | `models/diffusion_models/` | Load Diffusion Model |
| `minimax_h3_ref2va_*.safetensors` | `models/diffusion_models/` | Load Diffusion Model |
| `qwen3vl_32b_minimax_h3_*.safetensors` | `models/text_encoders/` | CLIPLoader — type **`minimax`** |
| `minimax_h3_video_vae_fp16.safetensors` | `models/vae/` | Load VAE |
| `minimax_h3_audio_vae_fp32.safetensors` | `models/vae/` | Load VAE |

**Build matrix** — each checkpoint ships five ways:

| Suffix | Notes |
|---|---|
| `_bf16` | Full precision, full parameters. The training base |
| `_pruned_bf16` | Full precision, **AdaLN branches removed** |
| `_pruned_fp8_scaled` | fp8 |
| `_int8_convrot` | int8 |
| `_pruned_int8_convrot` | **The templates' default** |

The encoder ships as `_bf16`, `_int8_convrot`, or **`_nvfp4_awq`** (the template default).

**What "pruned" means, and why it matters.** The model card explains that ~13B of the 33B parameters sit in AdaLN-related branches whose modulation outputs *"can be precomputed and cached,"* so they *"do not need to be loaded for inference-only deployment."* Pruned builds drop those branches. That is why community GGUF repacks show up as ~20B rather than 33B.

The consequence is that **pruned builds are inference-only.** MiniMax released full weights specifically *"to support further development, including fine-tuning"*, so any training run needs a non-pruned checkpoint.

**Memory.** The templates default to int8 weights *and* an nvfp4 encoder. That default tells you what you need to know: 33B of transformer plus a 32B VLM encoder is heavy even before latents. No official VRAM figure is published `[flagged — re-verify]`. Community GGUF and NVFP4 repacks appeared within days. Expect the low-VRAM story to stay community-driven and to keep moving fast.

**The reported floor is much lower than the parameter count implies.** That matters because people rule themselves out on arithmetic alone:

| Card | Reported | Notes |
|---|---|---|
| **3060 Ti 8 GB** | **540p** with the Turbo LoRA + SageAttention | The lowest floor reported anywhere. It sits below the ~0.8 MP reliability band, so treat it as a drafting rig `[community — r/unstable_diffusion; single report]` |
| 5070 Ti 16 GB | ~5–7 min for ~10 s at 1056×608 (0.6 MP) | Usable working speed at a modest resolution `[community — r/unstable_diffusion; single report]` |
| 5060 Ti 16 GB | 864×1536 × 10 s at 60–80 s/it with SLA | The acceleration-stack benchmark in §9 |

Two things make the low end possible at all. Pruned int8 weights drop ~13B of parameters that inference never needs (see above), and the Turbo LoRA cuts steps from 20 to 6–8 (§9). Neither is optional at 8 GB.

---

## 3. Frame count

Frame count must sit on the lattice **`frames ≡ 5 (mod 17)`**. The templates compute it from a duration with:

```
max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17     # a = duration in seconds
```

The shipped defaults are **73** frames (`17×4 + 5`, ≈3 s) for t2v/i2v, and **124** (`17×7 + 5`, ≈5 s) for r2v.

The valid values are: 5, 22, 39, 56, 73, 90, 107, 124, 141, 158, 175, 192, 209, 226, 243, 260, 277, 294, 311, 328, 345, 362. The maximum, 362 frames, is ≈15 s at 24 fps, and it is the documented ceiling.

The 17 almost certainly reflects the temporal packing of the visual latent (4× temporal compression before patchification). But the templates do not say so, and this skill will not claim a mechanism it has not verified. **Use the formula.**

---

## 4. Resolution

Resolution is a megapixel dial snapped to multiples of 32, set via `ResolutionSelector`. This is the template's own table, at 16:9:

| MP | Output | | MP | Output |
|---|---|---|---|---|
| 0.2 | 608 × 352 | | 0.9 | 1280 × 736 |
| 0.3 | 736 × 416 | | **0.98** | **1344 × 768** |
| 0.4 | 864 × 480 | | 1.0 | 1376 × 768 |
| 0.5 | 960 × 544 | | 1.2 | 1504 × 832 |
| 0.6 | 1056 × 608 | | 1.5 | 1664 × 928 |
| 0.7 | 1152 × 640 | | 1.8 | 1824 × 1024 |
| 0.8 | 1216 × 672 | | 2.0 | 1920 × 1088 |

The conditioning nodes default to **1344 × 768**. That is the 0.98 row, and it matches the card's "short side 768" spec. The template's `ResolutionSelector`, however, is set to 0.4 as a fast preview default. You are meant to reconcile the two yourself.

Supported aspect ratios include 21:9, 16:9, 4:3, 1:1, 3:4 and 9:16.

---

## 4a. Deploying on rented GPUs

[`comfyui-on-runpod`](../../comfyui-on-runpod/) owns the volume contract, `extra_model_paths.yaml` and the pod-vs-serverless decision. Three things are H3-specific enough to state here.

**H3 punishes a sloppy volume harder than any other model here.** It needs five files across three directories, including **two VAEs**. A missing audio VAE does not throw an error. It just gives you a *silent video*. On a fresh volume, the checklist is:

| Directory | Files |
|---|---|
| `models/diffusion_models/` | one of `minimax_h3_fl2va_*`, and/or `minimax_h3_ref2va_*` |
| `models/clip/` (mapped from `text_encoders`) | `qwen3vl_32b_minimax_h3_*` |
| `models/vae/` | **both** `minimax_h3_video_vae_fp16` and `minimax_h3_audio_vae_fp32` |
| `models/vae_approx/` | `taeh3.safetensors`, if you want fast previews |

That `vae_approx` row is exactly why the key belongs in `extra_model_paths.yaml`. It is easy to omit, and then you are left wondering why the preview node does nothing.

**Budget the download, not just the compute.** Both checkpoints plus a 32B encoder plus two VAEs adds up to a large pull. Do the download on a **CPU pod or over the S3 API**. Paying GPU rates to download H3 is one of the more expensive mistakes available here. Pull only the checkpoint you need first: FL2VA covers t2va and fl2va, which is most of the work.

**GPU sizing is genuinely unsettled.** The official templates default to `pruned_int8_convrot` weights with an `nvfp4_awq` encoder. That default is itself the strongest available signal that memory is tight, because a 33B transformer plus a 32B VLM encoder is a lot to hold even before latents. Community reports put usable inference in the **10–16 GB** range on those quantised builds `[community — re-verify]`, but no official figure is published, and the pruned/quantised matrix makes any single number misleading. Treat it this way: **start on the templates' quantised defaults**, measure, and only move up if you actually need `bf16`. If you intend to train, you need a non-pruned build and a much larger card.

Cold start is dominated by loading these weights from the volume. On serverless, prefer a longer idle timeout and batched jobs over many small requests — see `comfyui-on-runpod`'s scaling notes.

## 5. FL2VA vs Ref2VA wiring

**FL2VA** uses the node `MiniMaxH3ImageToVideo`, with args `(prompt, width, height, length)`. It is one node with three modes:

| Images connected | Mode |
|---|---|
| none | `t2va` — text to audio-video |
| `first_frame` **or** `last_frame` | `fl2va` from that end |
| both | `fl2va` between the two |

There is no separate text-to-video node. The `_t2v` and `_i2v` templates use the same node, and differ only in whether an image is attached.

**Ref2VA** uses the node `MiniMaxH3ReferenceToVideo`, with args `(prompt, width, height, length, match)`. It accepts:

- ≤ 9 images
- ≤ 3 video clips, each 2–15 s
- ≤ 3 audio clips, each 2–15 s
- **≤ 12 files total**, total duration ≤ 15 s

The `match` parameter defaults to `'match'` in the template. Its semantics are not documented in the template notes `[flagged — re-verify]`.

**Reference *audio* is the distinguishing capability.** You can pass a voice or a musical texture as a reference instead of describing it. No other model in this suite can do that.

The `match` setting is reported to matter: setting `ref_image_size` to **`MAX`** rather than `match` is said to latch onto a face more reliably. `[community — single report; re-verify]`

### The quality split, and the hybrid that closes it

Ref2VA is visibly worse than FL2VA at identical settings. If you swap the FL2VA checkpoint into an unchanged Ref2VA graph, both picture and audio improve, while references keep broadly working. The divergence between the two checkpoints sits almost entirely in the **`*.adaln_proj.*` tensors**. Overlaying Ref2VA's tensors onto an FL2VA base **for blocks 30–49** keeps the reference capability at FL2VA quality. Overlaying blocks 0–25 wrecks it.

- Loader node: `github.com/scottmudge/ComfyUI_MinimaxH3HybridLoader` (base = FL2VA, overlay = Ref2VA; use README settings, not node defaults; no memory overhead with mmap on)
- Baked checkpoints: `smhfacct/Minimax-H3-fl2va-ref2va-hybrid-models`. Try `b30-49` first. `b25-49` is visually equivalent with slightly better reference retention, `b20-49` gives more retention at less quality, and `b15-49` may lose noticeable quality. `[community — ThatsALovelyShirt]`
- The community default is drifting from `b30-49` toward **blocks 25–49**. dreamkrate ships a BF16-pruned hybrid baked that way. `[community — dreamkrate; re-verify]` A Hybrid-Checkpoint-Builder GUI now exists with 30-49, 25-49, 20-49 and 15-49 presets, so you can bake your own blend instead of waiting for a repack. `[community — BMB12d3; re-verify]`

**Once the hybrid removes the quality objection, the mode choice inverts for most work.** FL2VA's advantage was always picture and audio quality, but its *conditioning* is the more rigid of the two. FL2VA commits a supplied image to a **frame position** and builds the clip to arrive there. Ref2VA takes the same image and pins it to nothing, so it **guides content instead of anchoring the timeline**. The rest of the reference budget stays free for more images, audio or video alongside it. Practitioners doing sustained character work start from hybrid Ref2VA for that reason. `[community — nsfwVariant]` Keep FL2VA for the case where its rigidity is the feature: a continuity seam between two chained clips, where you need the first frame matched rather than interpreted. FL2VA is also the mode the Turbo LoRA was trained against, so the speed recipes are best attested there.

### Sizing reference images

References are not equal inputs. Their pixel size acts as a weighting. One reported allocation that works: **character ~1000 px, environment ~500 px, prop ~300 px** on the long side. Supply a reference for anything the model plausibly does not know, such as an unusual weapon or a specific piece of hardware. H3 has deep pre-trained knowledge of *named* characters and franchises, and correspondingly thin knowledge of things without names. `[community — erioca]`

Hybrid checkpoints are more prone to dragging a character sheet's **white background** into the shot. Matte the sheet, or state the environment instead.

### Lighter text encoders

The stock `Qwen3-VL-32B` encoder is 15.7 GB in NVFP4, and it exists to produce one `[seq, 5120]` conditioning tensor. `nicolab28/ComfyUI-ClipProj` replaces it with **Qwen3-VL-4B or 8B plus a learned linear projection** into that same space. The result is 4.5 GB with the int8_convrot encoder, with no change to the DiT, VAEs or sampler. It works because the 4B and 32B share a tokenizer, so hidden states map position by position. Calibration is ridge regression, with no training loop.

Know what you give up before using it, because the author measured it honestly:

- **Named people come back *wrong*, not missing.** The 4B believes Scarlett Johansson has dark brown hair, and the projection faithfully passes that wrong memory along. **Describe instead of naming.** A description spreads the identity over a dozen agreeing tokens, so reconstruction error averages out. A name is only two tokens and one very precise direction.
- **Non-English speech degrades badly.** A French line came out half Spanish. Cosine ~0.90 is ample for the picture but not enough for phonetics, because the audio branch needs far more precision than the image branch. Only French was tested.
- `ref2va` works, but the encoder must be loaded in **resident** mode. The dynamic path crashes in the vision tower with int8 encoders, and only when an image is present.
- The repo ships **zero and identity control matrices** so you can prove the projection is doing work, rather than trusting a plausible-looking output. That habit is worth copying.

One side finding is worth knowing beyond H3: ComfyUI's `SDClipModel.generate()` drops `embeds_info` and never calls `build_image_inputs`. So Qwen3-VL image tokens land at linear positions with no DeepStack injection, which means **any node on that path will confidently describe an image it never actually saw.** `[community — nicolab28]`

---

## 6. Production pipeline and the 768p ceiling

Local output tops out at **768p**. H3-Regenerate-2K is not in the open release, so the only 2K path is the hosted API.

A workable local ladder:

1. **Draft** at a low megapixel setting and a short frame count to find composition, motion and, importantly, the soundscape. Audio is as much a thing to iterate as the picture.
2. **Render** at 0.98 MP (1344 × 768) with the final frame count.
3. **Restore / upscale** with a **temporally-aware** restorer (SeedVR2, FlashVSR), not a per-frame image upscaler. A newer option is **ReDetail** (`Bambushu/redetail`), which re-renders the clip through the [`ltx-2-5`](../../ltx-2-5/) video upscaler. This is a *generative* re-render, not restoration. It has three hard constraints, and all three fail silently: **both output dimensions must divide by 64** (not 32), clip length must be **`8n + 1` frames** or the tail is dropped, and **a silent clip fails outright**. [`image-production-workflows`](../../image-production-workflows/) owns ReDetail — the invents-versus-recovers judgement, the 1.5×-versus-2× measurements, and where it sits against the image-side upscalers. Read it there rather than trusting a second copy here.

  **The third constraint is the one specific to H3.** LTX-2.5 encodes audio and video jointly, so ReDetail needs a soundtrack. That makes H3 output the one thing in this suite it accepts unmodified, and it makes "add a silence track" a symptom rather than a fix. If ReDetail rejects an H3 clip, an earlier stage stripped the audio, and you have already lost more than the upscaler cares about. Cached conditioning also makes the text encoder optional, which takes peak VRAM from 30.4 to 24.8 GB on a 5090 and skips a 15 GB download. `[community — DaLyon92x]`
4. **Interpolate** afterwards if you want a higher frame rate.
5. **Mux** the final audio back if any step in your chain drops it. Losing the audio in post is the most common way to lose H3's whole point.

**Ordering rule: restore/upscale before you interpolate.** [`image-production-workflows`](../../image-production-workflows/) owns the rule and the reasoning behind it.

**Watch your tooling for audio.** Most ComfyUI video post nodes and upscalers are picture-only, and they will silently discard the audio track. Keep the original output and re-mux, or verify that each stage preserves sound.

Cross-model production craft is in [`image-production-workflows`](../../image-production-workflows/); the video ladder in [`wan-2-2`](../../wan-2-2/) covers the same stages in more depth.

---

## 7. Going long — context chaining

The tool is `Comfyui-H3--Motion-Context` (Nikodemon), usually run as `ethanfel/ComfyUI-MiniMaxH3-Contex-Loop`. It carries **22 frames of the previous clip** forward as context, plus reference images for identity, and stitches the accepted clips together — **with audio** — at the end. Minute-plus continuous video is routine (~10 min per 15 s clip at 1.5 MP on a 5090). Each accepted clip is checkpointed, so a crash does not cost the run, and each clip can be re-rolled before acceptance.

**Chain through the latent, never through decoded frames.** The naive chain hands each segment the decoded last frame of the previous one. Every seam then pays a pixel round-trip through the VAE, which shifts colour, and the motion resets at the join. On a live 31 s chain built this way, the output darkened and degraded at every seam. Save and load the **latent** instead, through `MiniMaxH3MotionContext` (`context_latent` / `context_frames` / `context_audio`). That removes both the colour shift and the motion reset.

**FL2VA first+last-frame interpolation is the tightest scene control at a seam**, because both endpoints are pinned. It has one trap. When the two endpoint frames show mismatched rooms, the clip visibly morphs between them. Match the environments before you lean on it.

Context chaining changes what you write, not what you set:

- A **global prompt** is prepended to every scene. Put style there, along with the naming convention for each character.
- **Describe every other character in each scene's prompt**, in detail. That is the anti-bleed measure.
- **End each scene on a still beat.** The last frame has to connect to the next scene's first frame, and mid-stride does not connect.
- The tool is also useful in reverse: split one 8 s shot into two 4 s halves to afford more resolution.

Two newer routes reduce the chaining, or skip it entirely:

- The Civitai workflow **"Multishot — chained shots"** (v2.7, 2026-08-27, 17.3k downloads) adds a **per-character voice reference clip** to each shot. That stops dialogue bleeding across speakers in chained scenes, which the describe-every-character rule alone does not fix for voices. `[community — Civitai Multishot v2.7; re-verify]`
- **Single-pass shot syntax avoids the chain altogether.** ethanfel's Cinematic Multishot Coverage generates 8 angles at 45° increments, 32–85 mm, in one 124-frame pass. No seams means no chain drift. `[community — ethanfel; re-verify]`

---

## 8. Single-frame image editing

H3 with `length = 1` is an image editor. Several reports say it beats Krea 2 + Identity Edit, Qwen-Image-Edit and Flux Klein 9B for character fidelity, 3D scenes, mirrors and composition, at around **8 s per edit on a 5090**.

| Requirement | Why |
|---|---|
| **`Mamad8/MiniMax-H3-Image-VAE`** | The video VAE gives blurry stills. Generating 5 frames and taking one does not fix it |
| **Exactly 1 frame** | The image VAE produces grid artefacts at 5 frames. ComfyUI used to enforce a 5-frame minimum (`Comfy-Org/ComfyUI#15644`); recent nightlies lift it. Update rather than patching `comfy_extras/nodes_minimax_h3.py`, which you would have to re-apply on every ComfyUI update |

Reported settings: hybrid `b25-49` int8, ComfyKitchen attention, `sa_solver` / `simple`, **8 steps, CFG 1**, lightx2v Turbo LoRA, references at 1024×1536 or up to 1920×1088. `Mamad8/MaxiMin-HHH-R2V-ThisIsFine` is a detail LoRA some use here. `[community — Patient_Ratio4177]`

The frame rule does **not** apply here: `17n + 5` governs *video* length. One frame is a special case that the image VAE exists to serve.

---

## 9. The acceleration stack, layer by layer

SKILL.md carries the traps and the default recommendation. This section is the full stack: what each layer is, what it measures, and how it wires together. The four layers are independent and compose, but fix the runtime before you benchmark any of the other three. A broken runtime silently invalidates every number you take.

### Layer 0: the runtime

This is where most of the missing speed usually hides, and every failure in it is quiet.

| Trap | Symptom | Fix |
|---|---|---|
| **ComfyUI not on CU130** | INT8 ConvRot never actually engages, *even with the INT8 loader node wired up*. One user went 12–13 min → 4 min on the same job by fixing only this | Check the startup log for `pytorch version: 2.13.0+cu130`. If it doesn't say `cu130`, INT8 is decorative. Reinstall torch from the cu130 index, then reinstall a matching SageAttention wheel `[community — AI-imagine]` |
| **`comfy-kitchen` 0.2.10 fails to import** | One `cannot import name 'TensorCoreConvRotW4A4Layout'` ERROR buried in startup, then ComfyUI works normally — just slower. Kills the ConvRot path *and* fp8/fp4 | Update to 0.2.26+. **Check this before benchmarking anything** `[community — DeliciousGorilla]` |
| **The templates ship the `nvfp4` text encoder** | No hardware path for NVFP4 before Blackwell, so pre-50-series cards fall back | On 30/40-series use `qwen3vl_32b_minimax_h3_int8_convrot` instead |
| **SageAttention via the launch flag** | Reports of pure noise output, so people disable Sage entirely and lose ~20% | Apply it through the **KJNodes `Patch Sage Attention` node set to `auto`** instead — reported clean at the same seed, 11.99 → 9.29 s/it `[community — DeliciousGorilla]` |

### Layer 1: sparse attention (SLA) — the biggest single win

The node is `github.com/PlagueKind/ComfyUI-PlagueKind-Nodes` (hosted by Plague_Kind, designed by pl0x). It was measured on a 5060 Ti 16 GB at 864×1536 × 10 s:

| Path | s/it |
|---|---|
| PyTorch attention | 400 |
| ComfyKitchen | 140 |
| **Sparse @ 0.9** (default) | **80** |
| **Sparse @ 0.95** | **60** |

Sparsity 0.85 is reported as practically indistinguishable from PyTorch attention. 0.9 costs minimal degradation for ~15% more speed. 0.95 degrades slightly and is meant for long or high-resolution clips.

> **The node must be LAST in the chain, attached directly to the guider and scheduler.** Nearly every "it was slower" or "quality dropped" report traces back to this, usually because someone also wired a cache node in. Do not combine it with cache nodes. It requires a recent PyTorch on CU130. Blackwell gains the most, but every card gains something.

This layer is also the one most likely to be superseded. MiniMax withheld its own sparse-attention implementation and promised it "in a future update" `[official — model card]`. Once that ships, the recommendation changes.

### Layer 2: Spectrum — and the audio failure that is worth understanding

`github.com/xmarre/ComfyUI-Spectrum-MiniMax-H3` (marres) applies the training-free Chebyshev spectral-forecasting method from the Stanford/ByteDance Spectrum paper. It replaces some expensive transformer evaluations with forecasts from the feature history. A 20-step Euler run becomes 11 real evaluations plus 9 forecasts, which means **34% lower Euler sampler time (1.52×), and 29.6% on RES multistep**.

**Wire it as:** model loader → LoRAs and other patches → **MiniMax H3 Sigma Shift** → Spectrum Apply → guider → sampler. **Never run it alongside EasyCache.** Both skip evaluations while keeping their own cached state, and stacking them produces errors and unreliable output.

**Its audio problem is the clearest demonstration anywhere in this skill of why "one sequence" is the model's defining fact.** H3 packs audio and video features into the same transformer sequence, joined by attention, on *different shifted timestep schedules*. A spectral forecast made on the **video** features changes the live denoising state, and the next real evaluation processes that modified video state *jointly with audio*. Forecast error therefore reaches the audio through the transformer even when the audio was never blended. The symptoms are rough or distorted audio, unstable speech, and tripped or doubled syllables, and they are worst with reference audio.

The fix arrived in two stages. Both are worth knowing, because the first is not enough on its own:

1. **Split the control.** Set `blend_weight` (video) = 0.50 and `audio_blend_weight` = 0.00, so audio uses the local prediction instead of the spectral blend. This is a big improvement, but the indirect path above survives it.
2. **`offline_smoothing_replay`** (the default from v0.2.1). Pass 1 runs the same accelerated schedule with *both* blends forced to zero and archives every real post-transformer feature as an anchor. Pass 2 restarts from the original latent and reconstructs the trajectory from that archive, running **zero transformer blocks**. A skipped step can then interpolate between the nearest real anchors on *both* sides, instead of extrapolating from the past only. The forecast video features never re-enter a joint transformer call, so they cannot reach the audio. The result is the same 45% saving with clean audio.

Spectrum is an approximation, not a bit-identical path. Fast or briefly-visible detail — eyes, fingers, fingernails — can still deviate or degrade, and motion trajectories can differ from native. Use it when the speed is worth that trade-off, and turn it off for a keeper.

### Layer 3: the Turbo LoRA

A speed LoRA landed within days of release and is now the standard acceleration path. **lightx2v publishes an official one** — `lightx2v/Minimax-h3-Turbo`, e.g. `minimax_h3_fl2v_turbo_8step_v1.0_comfyui_bf16.safetensors`, 4–8 step — and it is the default recommendation today. The earlier community line is still in wide use: the original is by **larryvrh**, with ComfyUI-compatible conversions by **drbaph** (`drbaph/MiniMax-H3-Turbo-Lora-ComfyUI`).

> **Run speed LoRAs at 0.8–0.85, not 1.0.** This is a widely-repeated tip from the SLA author, and it applies to whichever Turbo build you use. `[community — Plague_Kind; contested against the LoRA authors' own 1.0 recipe]`

| Setting | Value `[community — Organix33/drbaph]` |
|---|---|
| Recommended build | `minimax_h3_turbo_v4_step600_ema_pruned_comfyui.safetensors` |
| Steps | **6–8** (down from 20) |
| Sampler | `euler` **or** `res_multistep` |
| Scheduler | **`beta`** — note this differs from the stock template's `simple` |
| LoRA strength | **1.0** |

It works across the quantised builds (int8, convrot, pruned, fp8). It was trained against the **FL2VA** checkpoint, but it is reported to work on **Ref2VA** too `[community — Organix33; re-verify]`. That is the first evidence that weights transfer between the two task checkpoints.

**The audio tax, and the core fix.** H3 runs **separate video and audio scheduling**. The original sampler chain mishandled that once the LoRA compressed the step count: the picture stayed fine, but the audio degraded. Kijai's `Comfy-Org/ComfyUI#15243` merged **2026-08-06** and shipped in **ComfyUI v0.31.0 (2026-08-08)**. It adds `ModelSamplingAV` / `ModelSamplingMiniMaxH3` with a separate **`audio_shift`**, so stochastic samplers and low step counts carry audio correctly on the stock path `[official — Comfy-Org/ComfyUI#15243, ComfyUI v0.31.0]`. In order of preference: update ComfyUI and use that node; on an install you cannot update, use larryvrh's `github.com/Larryvrh/ComfyUI-MiniMax-H3-Turbo` sampler; failing both, use ~10 steps with `euler` rather than `res_multistep` `[community — contested]`.

**Preview decoding** is a cheap extra. A tiny VAE exists — `Kijai/MiniMax-H3-TAE` (`taeh3.safetensors`), which goes in `ComfyUI/models/vae_approx/`. Core does not yet use it for final decode, so it works as a preview accelerator via custom node rather than a substitute for the real VAE. `[community — re-verify]`

### Two dials the acceleration work turned up that are not acceleration

Both come out of the same practice as the layers above. Both are quality changes that happen to live on nodes you installed for speed. Each has one named practitioner behind it, each is cheap to test, and both are worth trying before anything more elaborate.

| Dial | Stock | Reported | What it is |
|---|---|---|---|
| **Scheduler** | `simple` | **`beta`** | Described as a *"huge impact"* change on the ordinary path, not only under the Turbo LoRA where the templates already switch to it. If it holds up, the shipped default is simply wrong rather than conservative. That is a strong claim on one report, so verify it on your own seeds `[community — Revolutionary-Bar766; contested]` |
| **Sigma shift** (`MiniMax H3 Sigma Shift`, ships with the Spectrum pack) | video 12, audio 3 | **video 15, audio 1.5** | More of the video schedule spent at high noise, less of the audio schedule there. They move in opposite directions because H3 schedules the two streams separately — the same fact that gives the core `ModelSamplingMiniMaxH3` node its own `audio_shift` `[community — Revolutionary-Bar766; single report]` |

Note the dependency: the sigma-shift node arrives with Spectrum, so you can use this dial without running Spectrum's step-skipping at all. Installing the pack and using only the shift node is a legitimate configuration.

---

## 10. The abliterated-encoder myth

A myth spread so fast after release that a popular Docker template shipped it: the claim that replacing the Qwen3-VL encoder with an abliterated ("heretic") build uncensors the output. **It does not**, per the author of Heretic itself:

> Abliteration works by directional ablation on the residual stream so the LLM stops *refusing*. But LLMs already represent "harmful" inputs accurately — that is how they know to refuse in the first place. So the hidden states reaching the transformer are not clearer, they are **perturbed relative to what the model was trained on**, which costs prompt adherence and can add artefacts. `[community — -p-e-w-, author of Heretic]`

A corroborating detail from the same thread: the Qwen3-VL build shipped for H3 is **~8 GB smaller than stock because the output layers are absent**. Refusal lives in those layers, and only hidden states are needed here. There is no refusal path in the encoder to remove. `[community — re-verify]`

**Where abliterated models *are* useful: prompt expansion**, which is a separate stage *before* the encoder. An LLM asked to enhance a prompt can refuse outright, and an uncensored one won't. The Heretic author agrees this use is legitimate. Keep the two stages distinct: **abliterated model for expansion, official encoder for generation.**

The confusion is worth understanding because it is not really about H3. ComfyUI subgraphs commonly wire **the same LLM** into both the prompt-expander and the text-encode node. So swapping it to fix a refusing expander silently changes the encoder too. That is the same shape as [`krea-2`'s](../../krea-2/) enhancer problem.

**Also worth knowing:** community consensus is that H3 does not meaningfully refuse anything. Reported anatomy failures are attributed to **training-data gaps, not filtering**, and supplying reference images reportedly fixes much of it. `[community — re-verify]`
