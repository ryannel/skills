# Wan 2.2 — setup & workflows

1. [The two-expert graph, node by node](#1-the-two-expert-graph-node-by-node)
2. [The 5B graph](#2-the-5b-graph)
3. [The S2V graph](#3-the-s2v-graph)
4. [Quantisation, VRAM and offload](#4-quantisation-vram-and-offload)
   - [4a. Running a community merge](#4a-running-a-community-merge)
5. [The production ladder](#5-the-production-ladder)
6. [Longer pieces: stitching and drift](#6-longer-pieces-stitching-and-drift)
7. [diffusers](#7-diffusers)

All node settings below come from the official ComfyUI templates in `Comfy-Org/workflow_templates`, read directly from the JSON. The written documentation omits most of these numbers.

---

## 1. The two-expert graph, node by node

The 14B graph is the standard ComfyUI graph plus a **duplicated model path**. The text encoder and the VAE are shared. The model path forks into two experts and rejoins at the latent.

```
CLIPLoader (umt5_xxl_fp8_e4m3fn_scaled, type: wan)
    └─> CLIPTextEncode (positive) ─┐
    └─> CLIPTextEncode (negative) ─┤
                                   │
Load Diffusion Model (HIGH noise) ─┼─> [LoraLoaderModelOnly high] ─> ModelSamplingSD3 ─> KSamplerAdvanced #1
Load Diffusion Model (LOW  noise) ─┼─> [LoraLoaderModelOnly low ] ─> ModelSamplingSD3 ─> KSamplerAdvanced #2
                                   │
   latent node (mode-specific) ────┘         #1 ──latent──> #2 ──> VAEDecode ─> CreateVideo ─> SaveVideo
```

**The latent node depends on the mode.** The nodes are not interchangeable: the wrong one either refuses to wire up or fails to condition the generation.

| Mode | Node | Template defaults |
|---|---|---|
| T2V | `EmptyHunyuanLatentVideo` | 640 × 640, 81 frames |
| I2V | `WanImageToVideo` | 640 × 640, 81 frames |
| FLF2V | `WanFirstLastFrameToVideo` | 640 × 640, 81 frames |
| S2V | `WanSoundImageToVideo` | 640 × 640, 77 frames |
| 5B TI2V | `Wan22ImageToVideoLatent` | 1280 × 704, 121 frames |

`EmptyHunyuanLatentVideo` on a Wan graph looks like a mistake, but it is correct. ComfyUI reuses the Hunyuan video latent for Wan T2V. Do not "fix" it.

**The two samplers.** Both are `KSamplerAdvanced`. The widget order is `add_noise, noise_seed, control_after_generate, steps, cfg, sampler_name, scheduler, start_at_step, end_at_step, return_with_leftover_noise`.

| | Sampler #1 (high noise) | Sampler #2 (low noise) |
|---|---|---|
| `add_noise` | **enable** | **disable** |
| `start_at_step → end_at_step` | `0 → 10` (quality) / `0 → 2` (4-step) | `10 → 10000` / `2 → end` |
| `return_with_leftover_noise` | **enable** | **disable** |
| steps / cfg (quality) | 20 / 3.5–4.0 | 20 / 3.5–4.0 |
| steps / cfg (4-step LoRA) | 4 / 1.0 | 4 / 1.0 |
| sampler / scheduler | `euler` / `simple` | `euler` / `simple` |

`steps` is the **total schedule length** on both nodes, not a per-sampler count. The split between the two experts is expressed through `start_at_step` and `end_at_step` instead. A common and quiet mistake is setting sampler #2's `steps` to 10 on the reasoning that it only runs the second half.

**`ModelSamplingSD3` shift: 8 on the full-step path, 5 on the 4-step LoRA path.** There is one shift node per model path. The official templates change this value along with the LoRA, so it is easy to carry over the wrong value when you switch paths.

**Speed LoRAs** load through `LoraLoaderModelOnly`, one per expert, at strength 1.0 in the templates. The node is model-only because these LoRAs have no text-encoder half:

- I2V: `wan2.2_i2v_lightx2v_4steps_lora_v1_{high,low}_noise.safetensors`
- T2V: `wan2.2_t2v_lightx2v_4steps_lora_v1.1_{high,low}_noise.safetensors` — note the **v1.1** on the T2V pair

This file covers *loading and stacking* LoRAs. **Making** one is a different job: hyperparameters, dataset construction, and the two-expert training question all live in [`references/lora-training.md`](./lora-training.md).

**`CreateVideo` fps: 16** for all 14B modes. This value is metadata on the output container, and it does not change generation. A mismatch does make correct output play at the wrong speed, though, and that is a frequent false alarm behind "my video is in slow motion" reports.

---

## 2. The 5B graph

The 5B graph is simpler in every respect: one model, one sampler, and at most one LoRA.

- `wan2.2_ti2v_5B_fp16.safetensors` → `models/diffusion_models/`
- **`wan2.2_vae.safetensors`** → `models/vae/` — *not* the 2.1 VAE
- `Wan22ImageToVideoLatent`, **1280 × 704** (or 704 × 1280), **121 frames**
- `KSampler`: **20 steps, CFG 5.0, `uni_pc` / `simple`**, denoise 1.0
- `ModelSamplingSD3` shift **8**
- `CreateVideo` fps **24**

The 5B VAE compresses more aggressively: 4×16×16, or ×64 overall with patchification. That is why the 5B can hold 121 frames at 720p in far less memory. It is a different reconstruction character, not just a smaller model. Expect a different texture feel, and do not mix this VAE with 14B latents.

---

## 3. The S2V graph

The S2V graph is audio-driven, and it runs a **dense single 14B model, not an expert pair**:

- `wan2.2_s2v_14B_fp8_scaled.safetensors`, one `Load Diffusion Model`
- `WanSoundImageToVideo`, 640 × 640, **77 frames**
- `KSampler`: **10 steps, CFG 6.0, `uni_pc` / `simple`**
- `ModelSamplingSD3` shift **8**, `CreateVideo` fps **16**
- VAE: `wan_2.1_vae.safetensors`

Clip length follows the audio. S2V **consumes** audio for lip-sync. It does not generate any audio itself.

---

## 4. Quantisation, VRAM and offload

| Build | Source | Notes |
|---|---|---|
| fp8-scaled 14B | Official Comfy-Org repackage | The default for every 14B variant; filenames in SKILL.md |
| fp16 5B | Official | The 5B ships fp16 |
| GGUF Q3–Q8 | Community — City96 / QuantStack | Needs the `ComfyUI-GGUF` custom node |

**Practical guidance** `[community — re-verify, these figures move]`:

- **12 GB:** 14B at **Q4_K_M** is the usual quality-per-GB sweet spot.
- **~8 GB:** prefer **5B fp16 over 14B Q3_K**. A purpose-built dense 5B beats a 14B crushed to 3 bits, because at that level the quantisation damage costs more than the parameter gap gains.
- **16–24 GB:** fp8-scaled 14B runs comfortably, including LoRA training at rank 32.

**On rented GPUs**, [`comfyui-on-runpod`](../../comfyui-on-runpod/) owns the volume contract and cost guards. The Wan-specific point is that the 14B needs **both expert files on the volume**. A half-populated volume fails in a way that reads like a wiring error rather than a missing file. Pull the files on a CPU pod rather than a GPU one, and check that your GPU exists in the volume's datacenter before planning around it.

Two experts means **two model loads**. ComfyUI swaps them across the sampler boundary rather than holding both resident, so peak VRAM tracks one expert. The swap costs wall-clock time on every generation, however. On constrained cards this swap, not the compute, is often what makes 14B feel slow. Block-swap and offload settings in the wrapper node packs let you trade more of this if you need it.

---

## 4a. Running a community merge

Merges are a large part of how Wan 2.2 is actually run, and the licence permits them. The merges worth using are tuned for something the base checkpoint is weak at, such as low-step speed, motion smoothness, or a concept the base has no prior for. The cost is that **a merge's settings are its own**, and none of the ways of getting them wrong throws an error. SKILL.md § *Community merges, and why their settings contradict the templates* carries the three traps. This section carries one merge's full working configuration, verbatim from its published workflow, as a worked example of what a merge's numbers look like when they diverge `[community — RedMimicStudios]`.

```
model    Wan 2.2 I2V, 10-step NSFW fp8 merge
steps    10   (High 0–5 / Low 5–10)
cfg      2.0 HighNoise / 1.0 LowNoise     ← asymmetric: the merge is CFG-distilled
sampler  uni_pc / normal                  ← not euler/simple, and the author reports it mattered
shift    8.0 both stages
LoRA     none                             ← the NSFW LoRAs are merged in; stacking double-applies
output   1008×576, 49 frames, 16 fps
cost     ~41 min on a 3060 12 GB — fp8, 13.3 GB per stage, heavy offload
```

Two of those settings, the asymmetric CFG split and the `uni_pc` choice, were in the workflow JSON and not in its description text. That is the general lesson for merges. The description is marketing copy for the merge; the JSON is the configuration it was validated at. Load the JSON and read `widgets_values` the same way this file reads the official templates.

Note the resolution and length: 1008×576 is neither of Wan's supported bands, and 49 frames is not 81. A merge tuned at a specific resolution and clip length is tuned at *that* resolution and clip length. The base model's 81 @ 16 fps and 480p/720p bands do not carry over automatically.

### Choosing between merges by measurement

The same study picked between three checkpoints on **edge density, first frame against last**. This is a proxy for how much high-frequency detail the clip loses as it plays. It is cheap to compute: run an edge filter over frame 0 and frame N, then compare the means. It needs no reference clip, and unlike watching the clip, it distinguishes the two separate ways a video degrades:

| Checkpoint | Edge density, first → last | Result |
|---|---|---|
| Wan 2.2 Q4_K_M | **−10.1%** | anatomy broken |
| a "smooth motion" merge | **−27.3%** | anatomy fine, linework dissolved |
| Wan 2.2 I2V 10-step NSFW fp8 merge | **−3.2%** | both fine |

The two failure modes are independent, which is the point of measuring rather than judging by eye. The Q4_K_M run *held* most of its detail and still broke anatomy. The smooth merge got anatomy right while dissolving the linework. A single "does it look good" verdict collapses the two failures into one; the number separates them.

**The measurement also rules out repairs.** ESRGAN restoration on the −27.3% output moved it to **−28.2%**, which is to say it did nothing. That is the measurable difference between *blurred* detail, which a restorer can sharpen, and *absent* detail, which it cannot invent. By the late frames there was nothing left to recover. Ruling out a post-process fix by measurement costs one number. Ruling it out by trying it costs a restore pass per candidate.

The general version of this lesson — that seed-dominated failure means the base model is at fault, not the settings — is in SKILL.md § *When nothing you change moves the result*. The suite-level write-up is in [`generative-media-atlas`](../../generative-media-atlas/references/adult-work.md).

---

## 5. The production ladder

The optional stages are bypassable, so you can preview cheaply and pay for the heavy passes once the motion is right.

1. **Lock the still.** Compose, cast and style with an image model ([`z-image`](../../z-image/), [`flux-2`](../../flux-2/), [`krea-2`](../../krea-2/), [`sdxl`](../../sdxl/)). You have far more control here than any video prompt gives you.
2. **Draft the motion** on the 4-step speed LoRA path at low resolution. Judge *motion only*, and reroll seeds freely. This stage is cheap enough to iterate honestly.
3. **Render the keeper** on the 20-step quality path at 720p, with the same seed and prompt. Expect some reinterpretation; that is normal.
4. **Restore / upscale** with a **temporally-aware** restorer (SeedVR2, FlashVSR), not a per-frame image upscaler.
5. **Interpolate** with RIFE to 30/60 fps.
6. *Optional:* colour match across segments, grade, audio.

**Stages 4 and 5 are order-sensitive: restore before you interpolate.** [`image-production-workflows`](../../image-production-workflows/) owns that rule and the reason it holds, along with the rest of the cross-model handoff craft: denoise bands, decoding to pixels between VAE families, tiled upscale. Wan's stake in it is stage 5 specifically. Because Wan outputs a native 16 fps, the interpolation rung does more work here than after any other model in the suite. That makes it the stage worth getting right rather than the one to skip.

---

## 6. Longer pieces: stitching and drift

The 14B is built around clips of ~5 s (81 frames @ 16 fps). Longer output is a stitching problem.

The failure is **accumulation**. Each segment is conditioned on the previous segment's final frame, so it inherits that frame's degradation, and the error compounds: colour drifts, detail softens, identity slides. There are three mitigations, in order of reliability:

1. **Re-anchor on clean keyframes.** Generate stills for each beat with an image model and run each segment as its own I2V from a clean frame. Drift resets every segment.
2. **FLF2V to a known end state.** Give each segment both endpoints so it cannot wander.
3. **Overlap and blend.** Generate overlapping frames at the joins and cross-dissolve. This hides the discontinuity but does not stop the drift.

Colour-match segments in post regardless. Even well-anchored segments drift slightly, and a global match is cheap.

---

## 7. diffusers

```python
from diffusers import WanPipeline, WanImageToVideoPipeline
# Wan-AI/Wan2.2-T2V-A14B-Diffusers
# Wan-AI/Wan2.2-I2V-A14B-Diffusers
# TI2V-5B equivalent also integrated
```

T2V, I2V and TI2V are integrated `[official-via-docs]`. The MoE boundary is handled inside the pipeline rather than by wiring two samplers yourself. That is convenient, but it also means the per-expert control you get in ComfyUI, such as different LoRA strengths or CFG on the high expert only, is not directly exposed. **For the slow-motion fixes in SKILL.md, ComfyUI is the surface that lets you apply them.** Check the current pipeline signature for the parameter that exposes the expert boundary before assuming it is tunable.
