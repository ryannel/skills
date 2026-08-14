# MiniMax H3 — setup & workflows

All node settings below are read **verbatim from the official ComfyUI template JSONs** (`Comfy-Org/workflow_templates`: `video_minimax_h3_t2v.json`, `_i2v.json`, `_r2v.json`), including the resolution table and frame formula, which live in the templates' embedded author notes rather than in any docs page.

1. [The graph](#1-the-graph)
2. [File layout and builds](#2-file-layout-and-builds)
3. [Frame count](#3-frame-count)
4. [Resolution](#4-resolution)
5. [FL2VA vs Ref2VA wiring](#5-fl2va-vs-ref2va-wiring)
6. [Production pipeline and the 768p ceiling](#6-production-pipeline-and-the-768p-ceiling)

---

## 1. The graph

Requires ComfyUI with H3 support — **Comfy-Org/ComfyUI PR #15224**.

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

Two things to notice, both easy to get wrong:

**The graph forks at the decode, not before.** One latent, two decoders — `VAEDecode` for picture and **`VAEDecodeAudio`** for sound — recombined by `CreateVideo`. Every other video model in this suite has a single decode path. If your output is silent, this branch is where it went wrong.

**`BasicGuider`, not `CFGGuider`.** The stock graph is **guidance-free**, so there is no negative-prompt input at all. Constraints have to be phrased positively. Whether swapping in `CFGGuider` gives useful negative-prompt behaviour is **untested here** `[flagged — re-verify]`.

---

## 2. File layout and builds

From `Comfy-Org/MiniMax-H3`.

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

Encoder: `_bf16`, `_int8_convrot`, or **`_nvfp4_awq`** (the template default).

**What "pruned" means, and why it matters.** The model card explains that ~13B of the 33B sit in AdaLN-related branches whose modulation outputs *"can be precomputed and cached,"* so they *"do not need to be loaded for inference-only deployment."* Pruned builds drop them. That is why community GGUF repacks show up as ~20B rather than 33B.

The consequence: **pruned builds are inference-only.** MiniMax released full weights specifically *"to support further development, including fine-tuning"* — so any training run needs a non-pruned checkpoint.

**Memory.** The templates defaulting to int8 weights *and* an nvfp4 encoder tells you what you need to know: 33B of transformer plus a 32B VLM encoder is heavy even before latents. No official VRAM figure is published `[flagged — re-verify]`. Community GGUF and NVFP4 repacks appeared within days; expect the low-VRAM story to be community-driven and to move fast.

---

## 3. Frame count

Frame count must sit on the lattice **`frames ≡ 5 (mod 17)`**. The templates compute it from a duration with:

```
max(5, round(a * 24)) + (5 - (max(5, round(a * 24)) % 17)) % 17     # a = duration in seconds
```

Shipped defaults: **73** frames (`17×4 + 5`, ≈3 s) for t2v/i2v, **124** (`17×7 + 5`, ≈5 s) for r2v.

Valid values: 5, 22, 39, 56, 73, 90, 107, 124, 141, 158, 175, 192, 209, 226, 243, 260, 277, 294, 311, 328, 345, 362 — 362 frames ≈ 15 s at 24 fps, the documented maximum.

The 17 almost certainly reflects the temporal packing of the visual latent (4× temporal compression before patchification), but the templates do not say so and this skill will not assert a mechanism it has not verified. **Use the formula.**

---

## 4. Resolution

A megapixel dial snapped to multiples of 32, via `ResolutionSelector`. The template's own table, at 16:9:

| MP | Output | | MP | Output |
|---|---|---|---|---|
| 0.2 | 608 × 352 | | 0.9 | 1280 × 736 |
| 0.3 | 736 × 416 | | **0.98** | **1344 × 768** |
| 0.4 | 864 × 480 | | 1.0 | 1376 × 768 |
| 0.5 | 960 × 544 | | 1.2 | 1504 × 832 |
| 0.6 | 1056 × 608 | | 1.5 | 1664 × 928 |
| 0.7 | 1152 × 640 | | 1.8 | 1824 × 1024 |
| 0.8 | 1216 × 672 | | 2.0 | 1920 × 1088 |

The conditioning nodes default to **1344 × 768** — the 0.98 row, matching the card's "short side 768" spec. The template's `ResolutionSelector` is set to 0.4 as a fast preview default; the two are meant to be reconciled by the user.

Aspect ratios supported include 21:9, 16:9, 4:3, 1:1, 3:4 and 9:16.

---

## 4a. Deploying on rented GPUs

[`comfyui-on-runpod`](../../comfyui-on-runpod/) owns the volume contract, `extra_model_paths.yaml` and the pod-vs-serverless decision. Three things are H3-specific enough to state here.

**H3 is the model that punishes a sloppy volume hardest.** Five files across three directories, including **two VAEs** — and the failure mode of a missing audio VAE is a *silent video*, not an error. On a fresh volume the checklist is:

| Directory | Files |
|---|---|
| `models/diffusion_models/` | one of `minimax_h3_fl2va_*`, and/or `minimax_h3_ref2va_*` |
| `models/clip/` (mapped from `text_encoders`) | `qwen3vl_32b_minimax_h3_*` |
| `models/vae/` | **both** `minimax_h3_video_vae_fp16` and `minimax_h3_audio_vae_fp32` |
| `models/vae_approx/` | `taeh3.safetensors`, if you want fast previews |

That `vae_approx` row is exactly why the key belongs in `extra_model_paths.yaml` — it's easy to omit and then wonder why the preview node does nothing.

**Budget the download, not just the compute.** Both checkpoints plus a 32B encoder plus two VAEs is a large pull. Do it on a **CPU pod or over the S3 API** — paying GPU rates to download H3 is one of the more expensive mistakes available here. Pull only the checkpoint you need first: FL2VA covers t2va and fl2va, which is most work.

**GPU sizing is genuinely unsettled.** The official templates default to `pruned_int8_convrot` weights with an `nvfp4_awq` encoder, which is itself the strongest available signal that memory is tight — a 33B transformer plus a 32B VLM encoder is a lot to hold even before latents. Community reports put usable inference in the **10–16 GB** range on those quantised builds `[community — re-verify]`, but no official figure is published and the pruned/quantised matrix makes any single number misleading. Treat it as: **start on the templates' quantised defaults**, measure, and only move up if you actually need `bf16`. If you intend to train, you need a non-pruned build and a much larger card.

Cold start is dominated by loading these weights from the volume, so on serverless prefer a longer idle timeout and batched jobs over many small requests — see `comfyui-on-runpod`'s scaling notes.

## 5. FL2VA vs Ref2VA wiring

**FL2VA** — node `MiniMaxH3ImageToVideo`, args `(prompt, width, height, length)`. One node, three modes:

| Images connected | Mode |
|---|---|
| none | `t2va` — text to audio-video |
| `first_frame` **or** `last_frame` | `fl2va` from that end |
| both | `fl2va` between the two |

There is no separate text-to-video node — the `_t2v` and `_i2v` templates use the same node, differing only in whether an image is attached.

**Ref2VA** — node `MiniMaxH3ReferenceToVideo`, args `(prompt, width, height, length, match)`. Accepts:

- ≤ 9 images
- ≤ 3 video clips, each 2–15 s
- ≤ 3 audio clips, each 2–15 s
- **≤ 12 files total**, total duration ≤ 15 s

The `match` parameter defaults to `'match'` in the template; its semantics are not documented in the template notes `[flagged — re-verify]`.

**Reference *audio* is the distinguishing capability.** Passing a voice or a musical texture as a reference — rather than describing it — is something no other model in this suite can do.

---

## 6. Production pipeline and the 768p ceiling

Local output is **768p**. H3-Regenerate-2K is not in the open release, so the 2K path is the hosted API.

A workable local ladder:

1. **Draft** at a low megapixel setting and a short frame count to find composition, motion and — importantly — the soundscape. Audio is as much a thing to iterate as the picture.
2. **Render** at 0.98 MP (1344 × 768) with the final frame count.
3. **Restore / upscale** with a **temporally-aware** restorer (SeedVR2, FlashVSR), not a per-frame image upscaler.
4. **Interpolate** afterwards if you want a higher frame rate.
5. **Mux** the final audio back if any step in your chain drops it — the most common way to lose H3's whole point in post.

**Ordering rule, same as elsewhere: restore/upscale before you interpolate.** Interpolating first doubles the restorer's workload and bakes interpolation smear into what it then sharpens.

**Watch your tooling for audio.** Most ComfyUI video post nodes and upscalers are picture-only and will silently discard the audio track. Keep the original output and re-mux, or verify each stage preserves sound.

Cross-model production craft is in [`image-production-workflows`](../../image-production-workflows/); the video ladder in [`wan-2-2`](../../wan-2-2/) covers the same stages in more depth.
