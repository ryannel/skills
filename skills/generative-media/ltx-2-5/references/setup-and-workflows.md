# LTX-2.5 — setup & workflows

This file covers the graph, the files, the numbers you type, **loading and stacking LoRAs and IC-LoRAs**, the CLI, the hosted surfaces, and the install-side failures that error out loudly. *Making* a LoRA is covered in [`lora-training.md`](lora-training.md), and prompt craft in [`prompting-guide.md`](prompting-guide.md).

All node settings come **straight from the official template JSON**, not from a docs page. The sources are `Comfy-Org/workflow_templates`' `video_ltx2_5_{t2v,i2v,flf2v}.json` and `Lightricks/ComfyUI-LTXVideo`'s `example_workflows/2.5/*.json`.

## Contents

1. [The graph](#1-the-graph)
2. [Files, and the split-versus-monolith rule](#2-files-and-the-split-versus-monolith-rule)
3. [Resolution — the megapixel table](#3-resolution--the-megapixel-table)
4. [Quantisation, VRAM and the levers that move it](#4-quantisation-vram-and-the-levers-that-move-it)
5. [The `ltx-pipelines` CLI](#5-the-ltx-pipelines-cli)
6. [Using LoRAs and IC-LoRAs](#6-using-loras-and-ic-loras)
7. [The multi-stage ladder and mixed-model handoffs](#7-the-multi-stage-ladder-and-mixed-model-handoffs)
8. [Hosted surfaces](#8-hosted-surfaces)
9. [Loud failures](#9-loud-failures)

---

## 1. The graph

LTX-2 is **built into ComfyUI core** (`comfy/ldm/lightricks`). `Lightricks/ComfyUI-LTXVideo` adds extras on top of that core support. Three native templates ship under Template Library → Video → LTX-2.5: `video_ltx2_5_t2v`, `_i2v`, and `_flf2v`. The 2.5 templates may need **nightly** ComfyUI rather than stable.

```
CLIPLoader (gemma4-12b-with-proj-ltx-2.5-*) ──> conditioning ─┐
Load Diffusion Model (ltx-2.5-22b-distilled-*) ───────────────┤
                                                              ├─> LTXVDualCFGGuider [1, 1]
EmptyLTXVLatentVideo [768, 512, 97, 1] ──┐                     │
LTXVEmptyLatentAudio [97, 25, 1] ────────┼─> LTXVConditioning [24]
ManualSigmas (8 values) ─> KSamplerSelect (euler_ancestral) ──┴─> SamplerCustom  [STAGE 1]
        │
        └─> LTXVLatentUpsampler (x2 spatial) ─> ManualSigmas (3 values) ─> SamplerCustom  [STAGE 2]
                    │
                    ├─> VAEDecodeTiled [512, 64, 64, 16]  (video VAE) ─┐
                    └─> LTXVAudioVAEDecode (audio VAE) ────────────────┴─> CreateVideo [24, 8] ─> SaveVideo
```

**The graph carries two latents from the start.** `EmptyLTXVLatentVideo` and `LTXVEmptyLatentAudio` both feed the same sampler, and the audio latent's frame count must match the video's. This is why a silent input clip is impossible on V2V. There is no video-only path.

**Guidance runs through `LTXVDualCFGGuider`, which has separate video and audio scales.** Both scales are **1** in every shipped 2.5 template. At 1, the negative conditioning does nothing. The docs say plainly that raising the scale does not help on the distilled model, and they recommend staying inside **1.0–1.5**. Real CFG only lives on the dev checkpoint, via `TI2VidTwoStagesPipeline`.

**Sigmas are given explicitly, not derived from a step count.** Stage 1's eight values pack the first five near 1.0, which makes a very fine early schedule, and then jump three times in long steps. Stage 2's three values start *below* 1.0, because stage 2 refines a latent that already exists. Changing "steps" therefore means editing the sigma list, not turning a spinner. The lists themselves are in SKILL.md's stock-settings table.

> **Widgets in these templates are often dead.** The templates are subgraph-based, and most numeric widgets are driven by links from the parent graph. A value you grep out of `widgets_values` may never actually run. Known-inert cases in `video_ltx2_5_t2v.json`: the latent's `768, 512, 97` (the graph actually builds **640 × 368 × 121**), the enhancer's `True` (it is **off**), and FLF2V's `25`. Trace the links before you quote a number from one of these files.

**Mode-specific additions.** I2V inserts `LTXVImgToVideoInplace [0.7, False]` in stage 1 and `[1, False]` in stage 2. It also adds `LTXVPreprocess [18]` and a lanczos resize of the longer dimension to 1536. FLF2V uses `LTXVAddGuide [0, 0.7]` and `[-1, 0.7]`, which condition the first and last frame at strength 0.7, and then `LTXVCropGuides`, which strips the guide frames after stage 1. A `[25]` shows up on FLF2V's `LTXVConditioning` beside `CreateVideo [24]`, but that is **not** a bug. Both widgets are link-driven from the same upstream `PrimitiveInt [24]`. The serialized widget values never actually run, so no mismatch is possible.

**Ten further workflows** ship in `ComfyUI-LTXVideo/example_workflows/2.5/`, with a decision tree in their README. They cover two-stage and single-stage T2V/I2V, A2V two-stage, T2A single-stage, and IC-LoRA graphs for Union Control, V2V, Ingredients, Motion Track, Inpaint and Outpaint. **The repo's top-level README is still 2.3-centric**, so start from the `2.5/` README instead, on branch `master`.

---

## 2. Files, and the split-versus-monolith rule

**2.5 ships one file per component. 2.3 ships a monolith** that bundles the transformer, both VAEs and the text projection. "Mixing the two sets is an error": the loader will not reconcile them.

| File | Folder | Notes |
|---|---|---|
| `ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors` | `models/diffusion_models/` | What all three official templates load. `-bf16` and `-nvfp4` (Blackwell) also exist |
| `ltx-2.5-22b-dev-transformer-bf16.safetensors` | `models/diffusion_models/` | Full model; needed for real CFG |
| `gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors` | `models/text_encoders/` | **A stock Google Gemma 4 is not a substitute** — loading checks the encoder version against `gemma4-12b-ltx-v1` |
| `ltx-2.5-video-vae-bf16.safetensors` | `models/vae/` | `DiffusionVideoDecoder`. Best quality, highest VRAM |
| `ltx-2.5-video-vae-conv-bf16.safetensors` | `models/vae/` | `ConvVideoDecoder`. "Lighter and needs no extra dependencies" |
| `ltx-2.5-audio-vae-bf16.safetensors` | `models/vae/` | Required by anything with audio, which is everything |
| `ltx-2.5-latent-spatial-upscaler-x2-bf16-1.0.safetensors` | `models/latent_upscale_models/` | All two-stage pipelines. Loaded by `LatentUpscaleModelLoader`; `LTXVLatentUpsampler` consumes the result and takes no filename |
| `ltx-2.5-latent-temporal-upscaler-x2-bf16-1.0.safetensors` | `models/latent_upscale_models/` | `DFRPipeline` temporal rounds only |
| `ltx-2.5-22b-distilled-lora-450-bf16.safetensors` | `models/loras/` | Two-stage pipelines that run the **full** model in stage 1 |
| `gemma4_e2b_it_bf16.safetensors` | `models/text_encoders/` | Optional prompt enhancer (Comfy int8 build at `Comfy-Org/gemma-4`) |
| `ltx-2.5-duration-head-bf16.safetensors` | `models/model_patches/` | Optional; enables auto-duration |

**The quick-start download is roughly 66 GiB.** ComfyUI picks the decoder automatically from the checkpoint's `vae._class_name`. The choice therefore comes from *which VAE file you place*, not from a node setting.

### Running 2.3 instead — the install shape

SKILL.md carries the three facts that decide whether a 2.3 install works: the monolith, a separately downloaded Gemma 3 12B, and the unchanged lattice. This table is the rest of it.

| | LTX-2.3 |
|---|---|
| Weights | **`Lightricks/LTX-2.3`** — ungated. Quantised builds `Lightricks/LTX-2.3-fp8` (915k downloads, more than the 2.5 base repo) and `-nvfp4` |
| Checkpoint shape | **One monolithic file** bundling transformer, video VAE, audio VAE *and* the text projection. There are no separate VAE files to place, and `models/vae/` stays empty |
| Text encoder | **Not bundled, and not the 2.5 encoder.** Download **Gemma 3 12B** separately from `google/gemma-3-12b-it-qat-q4_0-unquantized` `[official — MODELS-LTX-2.3.md]`. This is the single fact that decides whether a 2.3 install works |
| Workflows | The `ComfyUI-LTXVideo` **top-level README is the 2.3 documentation** — it reads stale only from a 2.5 angle. The 2.3 graphs sit beside the `2.5/` folder in `example_workflows/`, e.g. `LTX-2.3_V2V_ICLoRA_Single_Stage_Distilled.json` |
| CLI | The same `ltx-pipelines` package on the **monolith** path. Monolith and split paths are mutually exclusive — "mixing the two sets is an error" |
| Lattice | **Applies unchanged** — `8k+1` frames, dimensions multiples of 32, fps in {24, 25, 48, 50}. [§3](#3-resolution--the-megapixel-table) says why that is safe to rely on across both versions |
| Only on 2.3 | The **HDR**, **Dub-It** and **Relight** IC-LoRAs; the hosted **Retake / Extend / Reframe / HDR-upscale** endpoints (`ltx-2-3-pro` only); the 168-LoRA Civitai library |
| Absent on 2.3 | Native multishot, DFR and keyframe slots (`DFRPipeline` **raises** rather than silently ignoring), the diffusion decoder, auto-duration |

**Three things this skill cannot give you for 2.3.** They are the exact monolith **filename**, the name of the 2.3 entry in ComfyUI's Template Library, and 2.3's **sigma list, step count and CFG**. None of these were read for this skill. The 2.5 numbers do not carry over either, because the schedules differ `[flagged — re-verify]`. `MODELS-LTX-2.3.md` and the `ComfyUI-LTXVideo` top-level README carry all three.

**Gating, operationally.** Every 2.5 repo, and most 2.3 adapter repos, are `gated: auto`. Log in, accept the terms, and use a **Read** token. A fine-grained token needs the "read gated repos" scope, or downloads return 401. For which repos are gated, and for the marketing-consent wording you are accepting, see [`licence-and-derivatives.md` §9](licence-and-derivatives.md#9-gating-and-what-could-not-be-reached).

---

## 3. Resolution — the megapixel table

The templates drive resolution from a **megapixel budget**, and they snap both axes to multiples of 32. This table comes from the `MarkdownNote` embedded in `video_ltx2_5_t2v.json`, at 16:9:

| MP | Output | MP | Output |
|---|---|---|---|
| 0.2 | 608×352 | 0.9 | **1280×736** (template default) |
| 0.3 | 736×416 | 1.0 | 1376×768 |
| 0.4 | 864×480 | 1.2 | 1504×832 |
| 0.5 | 960×544 | 1.5 | 1664×928 |
| 0.6 | 1056×608 | 1.8 | 1824×1024 |
| 0.7 | 1152×640 | 2.0 | 1920×1088 |
| 0.8 | 1216×672 | | |

**These are stage-1 dimensions.** Two-stage pipelines upscale 2× in stage 2, so the delivered file is twice the figure above. The 0.9 MP default lands at 2560×1472. On a low-VRAM rig, raising the base MP and *skipping* stage 2 is often faster, and it is no worse than doing it the other way round `[community — 2legsRises, Comfortable-You-3881]`.

**The frame lattice, worked out.** SKILL.md carries the four rules and the two anchor values (121 frames = 5 s at 24 fps, 241 = 10 s). This section gives the derivation and the full table. The VAE encodes `[B,3,F,H,W] → [B,128,F',H/32,W/32]` with `F' = 1 + (F-1)/8`. A frame count that is not `8k+1` therefore has no whole-latent representation, and the remainder gets dropped. The templates compute frames as `fps × seconds + 1`, so the frame rate decides which whole-second durations are legal:

| fps | Legal whole seconds | Worked values |
|---|---|---|
| **24** | any | 4 s = **97** · 5 s = **121** frames (**the template default**) · 10 s = **241** |
| **25** | multiples of 8 | 8 s = **201** · 16 s = **401** |
| **48** | any | 5 s = **241** · 10 s = **481** |
| **50** | multiples of 4 | 4 s = **201** · 8 s = **401** |

**The lattice is safe on both 2.5 and 2.3**, and the VAE-compression-factor flag does not change that. That flag is about the *trainer*: it now reads factors from checkpoint metadata "instead of assuming 32x32x8", so a future or non-default checkpoint might differ. Every live artefact still enforces this lattice. That includes `DubItPipeline`, a **2.3**-only path, which snaps to the nearest `8k+1`.

---

## 4. Quantisation, VRAM and the levers that move it

**The repo publishes no absolute figures, and says so.** `docs/optimization.md` states plainly that its guidance is "order-of-magnitude; hardware varies — no absolute timings or VRAM figures." Vendor claims elsewhere range from 12 GB to 80 GB. Plan against the documentation's own figure of **32 GB minimum / 80 GB recommended**. `ComfyUI-LTXVideo`'s `low_vram_loaders.py` exists specifically to "ensure the correct order of execution and perform the model offloading such that generation fits in 32 GB VRAM."

Measured community reports, distilled path:

| Rig | Job | Result |
|---|---|---|
| 3060, 16 GB system RAM | 0.5 MP × 10 s | **180 s** `[community — rinkusonic]` |
| 4070 Ti 12 GB + Sage or ComfyKitchen attention | 0.4 MP × 15 s | **< 120 s** `[community — intLeon]` |
| 3050 4 GB VRAM laptop, 16 GB RAM | 0.9 MP × 10 s | 246 s `[community — Pitiful-Clothes3133; single report]` |
| 4070 Ti, 64 GB RAM | > 10 s at 0.3 MP | fails at sampling `[community — Ill_Health_4996; single report]` |
| 3090, 128 GB RAM | 2.3 **dev**, non-distilled | would not run `[community — Comfortable-You-3881]` |

Treat the dev checkpoint as a different hardware class, not just a slower option. One report is blunt: *"the Dev model was released with the expectation that people were running workstation cards or at the bare minimum, something the likes of a 5090"* `[community — Comfortable-You-3881]`.

**Levers, roughly in order of how much they help:**

| Lever | Effect |
|---|---|
| **Conv video VAE instead of the diffusion one** | Removes the single largest memory spike. This is the standard fix for the decode-time OOM |
| `VAEDecodeTiled` | Templates default `[512, 64, 64, 16]`. Lightricks publish a recommended range from `512/64/128/32` (16×16 tiles) to `1536/384/192/48` (48×48). "Fewer tiles will result in faster execution, but will require more memory" |
| Leave the prompt enhancer off | It ships off; enabling it loads a second Gemma alongside the transformer. Its on-disk size is reported as ~5 GB by docs.comfy.org and ~10 GB by the template's own note |
| Skip stage 2; raise base MP | Removes the upscale pass entirely `[community — 2legsRises]` |
| `--quantization fp8-cast` | Downcasts bf16 on the fly on any FP8-capable GPU. `fp8-scaled-mm` needs an fp8 checkpoint plus Hopper+; `nvfp4-cast` / `nvfp4-prequant` need Blackwell SM ≥ 10 and `ltx-kernels`. Set `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True` |
| `--offload cpu` / `disk` | CPU holds weights in system RAM; disk streams them, much slower |
| `--diffvae-optimization` | `chunked_eager` (default, lowest VRAM) · `chunked_compile` · `combined_compile` (needs `natten`, highest VRAM, ~1.4× faster) · `blackwell_dsl` (B200). **Peak VRAM of the `chunked_*` modes is roughly half `combined_compile`'s** |
| Text encoding via the LTX API | The Lightricks two-stage graph exposes "(via api)" outputs, keeping the 12B Gemma out of VRAM entirely. Multi-GPU options — sequence parallel, tiled data parallel, distributed VAE decode and distributed Gemma — are in `docs/multigpu/` |

**Attention backends.** Use FlashAttention 4 (`flash-attn-4==4.0.0b9`) on datacenter Blackwell B200, because "newer betas have known issues on consumer Blackwell". Use the FA3 wheel on Hopper, and PyTorch SDPA everywhere else. On consumer cards, SageAttention and ComfyKitchen attention both give a large speed-up. The second needs no build step: add a `ModelAttentionBackend` node and pick comfy kitchen attention `[community — intLeon]`.

**Verify that INT8 ConvRot is actually engaging.** All three official templates load an `-comfy-int8-convrot` build. On a mismatched CUDA/PyTorch runtime, that kernel **falls back silently instead of erroring**. You still get a working generation, but you lose the speed the build exists for, and nothing in the log tells you. [`minimax-h3`](../../minimax-h3/) documents this trap in full for the same runtime. It gives the startup-log line to check, and the `comfy-kitchen` version floor below which the import fails into a single buried ERROR. Check this before you benchmark anything here, because an unengaged INT8 build looks exactly like a slow model.

**Community builds worth knowing.** `REDGraft LTX 2.5 老同学 Fast 2K` (AiMetatron) has ~148k Civitai downloads, an order of magnitude above anything else tagged LTXV 2.5, including Lightricks' own upload. A `Joy-LTX 2.5 Distilled` family (joeygambino) covers GGUF / INT8 / NVFP4 / W4A8 / Mac `[community — Civitai API 2026-08-22]`.

---

## 5. The `ltx-pipelines` CLI

```
git clone https://github.com/Lightricks/LTX-2 && cd LTX-2 && uv sync --extra natten
python -m ltx_pipelines.distilled --prompt "..." --num-frames 121 --seed 42
```

There are three packages: `ltx-core` (model and inference stack), `ltx-pipelines` (twelve pipelines, each its own module entry point), and `ltx-trainer` (LoRA, IC-LoRA and full fine-tune, covered in [`lora-training.md`](lora-training.md)).

Shared flags: `--seed`, `--offload`, `--quantization`, `--max-batch-size`, `--compile`, `--lora <path> [strength]` (repeatable), `--enhance-prompt`, `--hdr`, `--video-vae-path`, `--diffvae-optimization`, `--auto-duration MIN MAX`. You cannot mix the split and monolith checkpoint paths.

`natten` pins `natten==0.21.7+torch2130cu132` against `torch==2.13.0` (cu132). On older stacks, large volumes can trigger a CUDA illegal memory access inside NATTEN TokPerm.

---

## 6. Using LoRAs and IC-LoRAs

*Making* a LoRA is covered in [`lora-training.md`](lora-training.md). This section is about loading and stacking.

**Plain LoRAs** load through the normal ComfyUI LoRA loader, or through `--lora <path> [strength]` on the CLI, which you can repeat to stack them. Use the 0.5–1.5 strength band. That band is standard across diffusion LoRAs generally, not specific to LTX. The Civitai library is overwhelmingly 2.3-trained: **168 LoRAs against 3 for 2.5** on 2026-08-22. It includes `LTX 2.3 - Enhancers` (vrgamedevgirl), `Amateur Hour - LTX 2.3` (QualityControl), `Camera Controls [LTX-2.3]` (ReltivlyObjectv), and style LoRAs. One entry is worth knowing for the conditioning picture: **`LTX-2.3 Whisper / Soft-Spoken Audio LoRA` (plz12345), which targets the audio branch** `[community — Civitai API 2026-08-22]`.

**Forward compatibility is claimed but soft, and the evidence splits by adapter type.** SKILL.md carries the ruling. This is what the ruling rests on.

For **IC-LoRAs**, the first-party evidence points the same way in three places. First, `LTX-2.5_ICLoRA_Union_Control_Distilled.json` loads `ltx-2.3-22b-ic-lora-union-control-ref0.5.safetensors`. Second, the 2.5 V2V, Ingredients, Motion Track and Inpaint graphs all load 2.3-trained adapters onto the 2.5 distilled transformer. Third, the docs page is titled "All LTX-2.5 IC-LoRAs" while listing 2.3 model cards throughout. Its stated rule is that "any adapter that does *not* support a given version of LTX is flagged in its listing." Against that stands one sentence in `MODELS-LTX-2.3.md`, written before 2.5 existed: "a LoRA only works with the model it was trained on." Shipped workflows are stronger evidence than a general statement in a prior version's model card.

For **plain LoRAs** there is no first-party evidence at all. A widely-seen post titled "Most LTX 2.3 Loras work on LTX 2.5" calls it *"pretty much confirmed by the devs"* `[community — ArttTaku; single report]`. But its 75 comments produced no clean confirmation and no counter-example either. Test at low strength before committing.

**IC-LoRAs** use dedicated nodes:

| Node | Job |
|---|---|
| `LTX IC-LoRA Loader Model Only` | Loads the adapter onto the transformer |
| `LTX Add Video IC-LoRA Guide` | Attaches the reference input; carries `attention_strength` and `attention_mask` |
| `LTX Add Video IC-LoRA Guide Advanced` | Mask-aware variant, used by the in/outpainting graphs |
| `LTXVCropGuides` | Crops guide frames out after stage 1 |
| `LTX Draw Tracks` / `LTX Sparse Track Editor` | Author the sparse spline trajectories Motion Track Control consumes |

Unless noted, every released adapter lives at `Lightricks/LTX-2.3-22b-IC-LoRA-*`. **Union Control** combines depth, canny and pose in one adapter. **Ingredients** turns a reference sheet into consistent characters, props and locations, using the two-part prompt `Reference sheet: <panels> / Generated video: <action>`. **Pixel Spatial Upscaler** comes in 2× and 4×. The rest of the list is **Motion Track Control**, In-Outpainting, Clean Plate, Deblur, Decompression, Colorization, Day-To-Night, Water Simulation, Instant Shave and Cross-Eyed. **HDR**, **Dub-It** and **Relight** are also released, but they are in beta and **2.3-only**. Two plain LoRAs sit alongside them: `LTX-2.3-22b-LoRA-Foley-V2A` and `-Cinemagraph`. The only 2.5-native adapter is `Lightricks/LTX-2.5-22b-IC-LoRA-Pixel-Spatial-Upscaler`.

Two third-party IC-LoRAs are worth knowing. `Cseti/LTX2.3-22B_IC-LoRA-CrossView-Warp_v2` (with `cseti007/ComfyUI-CrossViewWarp`) re-poses the camera of an existing clip on an orbit sphere, instead of through prompt text. `MaqueAI/LTX2.3-IC-LORA-Dual-Character` handles multi-character scenes that break single-character LoRAs `[community — Civitai]`.

For V2V, the current community pick is the first-party `LTX-2.5_ICLoRA_Union_Control_Distilled.json`. The recommendation reads: *"After running a bunch of tests, the one I'd recommend right now is … the most consistent one I've tried for V2V so far"* `[community — Interesting_Room2820]`.

---

## 7. The multi-stage ladder and mixed-model handoffs

The in-model ladder and the restore-before-interpolate rule are in SKILL.md. Two things belong here instead.

**DFR in detail.** `DFRPipeline` runs the distilled sigma schedule on the **full** checkpoint, using the distilled LoRA. Stage 1 generates at half resolution, plus **generated keyframe slots** on an 8-frame-border segment grid. Stage 2 re-denoises at full resolution with the distilled LoRA and an optional 2× detailing IC-LoRA, conditioned on the stage-1 reference. Keyframe slots need `use_keyframes_abs_pos_embedding`, which is **2.5 only**. On 2.3 the pipeline raises an error instead of silently ignoring the request. The cost is roughly +16% tokens (≈1.35× attention) for five slots at 512×768 / 241 frames, and roughly +31% (≈1.72×) at 1088×1920 / 121 frames. **Audio comes from stage 1 only.**

**Mixed-model handoffs.** Still-locking runs from the image skills feed into I2V here: [`z-image`](../../z-image/), [`flux-2`](../../flux-2/), [`krea-2`](../../krea-2/) and [`sdxl`](../../sdxl/). The finishing direction is what people actually use LTX for: [`minimax-h3`](../../minimax-h3/) output gets re-rendered through the LTX-2.5 upscaler. That runs either through a hand-built graph (`MINIMAX_H3_LTX2.5_Upscaler_v1.json`, Peter Duncan) or through **ReDetail** (`Bambushu/redetail`), whose constraints and per-scale costs are in [`image-production-workflows`](../../image-production-workflows/). For clips over 10 s, swapping in the first-party **LTX Looping Sampler** reached 20 s on a 4090 without an out-of-memory error `[community — Cptcrocro]`. Two interfaces bundle the whole thing: **Mix Studio** v1.2.4 (blackmixture) and **ComfyUI-Stimma** 1.0.13, which adds extend, loop, stitch and up to ten LoRAs `[community — blackmixture; Stimma release notes]`.

---

## 8. Hosted surfaces

| Where | IDs | Rate |
|---|---|---|
| **LTX API** (`api.ltx.io`, console at `console.ltx.video`) | `ltx-2-5-fast`, `ltx-2-5-pro`, `ltx-2-3-fast`, `ltx-2-3-pro` | Per **second of output**: 2.5-fast $0.09 (720p) / $0.13 (1080p) / $0.19 (1440p) / $0.30 (4K); 2.5-pro $0.12 / $0.17. 2.3-fast is 3× cheaper |
| **fal.ai** | `lightricks/ltx-2.5/{text-to-video,image-to-video}/{fast,pro}`, `/audio-to-video/fast` | Same per-second rates |
| **Replicate** | `lightricks/ltx-2.5-fast`, `ltx-2.3-pro`, `ltx-2.3-fast`, `ltx-2-retake`, `audio-to-video` | **No `ltx-2.5-pro`.** Pricing not read here |
| **LTX Desktop** | free open-source local editor built on 2.5 | — |

A2V bills by **input audio** seconds. **Retake, Extend, HDR-upscale and Reframe are `ltx-2-3-pro` only.** Extend is capped at 505 billed frames (≈21 s at 24 fps).

The API also imposes a **fixed duration lattice** that local runs do not have. Fast allows 6–20 s in even steps at 720p/1080p and 24/25 fps. Everywhere else, including all of Pro, the choices are 6/8/10 s. **Pro tops out at 1080p and 10 s, while Fast reaches 4K and 20 s.** That is the reverse of what you would expect, so check it before choosing a tier. On prepaid accounts, **credits are held against the longest duration your resolution and fps allow** until the job completes. A six-second request therefore gets declined if you cannot cover twenty.

---

## 9. Loud failures

These error out instead of quietly degrading, so they belong here rather than in SKILL.md's failure table.

| Error | Cause | Fix |
|---|---|---|
| 401 / 403 downloading weights | The 2.5 repos are `gated: auto`, and 16 of 18 2.3 adapter repos are too | Accept terms on HF; use a **Read** token with the "read gated repos" scope |
| Encoder rejected at load | Version check against `gemma4-12b-ltx-v1` | Use `gemma4-12b-with-proj-ltx-2.5-*`, not a stock Google Gemma 4 |
| Checkpoint load fails with a shape or key error | A 2.3 monolith mixed with 2.5 split files | Pick one set — "mixing the two sets is an error" |
| Keyframe-slot request raises on 2.3 | `use_keyframes_abs_pos_embedding` is 2.5-only; the pipeline raises deliberately | Move to 2.5 or drop the slots |
| CUDA illegal memory access inside NATTEN TokPerm | Old PyTorch/CUDA against the `natten==0.21.7+torch2130cu132` pin | Match the pin, or `--diffvae-optimization chunked_eager` |
| Nodes missing from the Template Library | 2.5 templates may need ComfyUI **nightly** | Update; confirm `ComfyUI-LTXVideo` is on `master` |
