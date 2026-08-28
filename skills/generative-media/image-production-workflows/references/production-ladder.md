# The Production Ladder — multi-stage settings in depth

This file gives stage-by-stage detail for the base → refine → detail → upscale → finish ladder. The settings are starting points that named workflow authors converge on, and each one is attributed where it appears. They are given as ranges because your checkpoint and resolution will shift them.

## Contents
1. Base generation & the two-pass discipline
2. The hires / refine second pass
3. Detailers (FaceDetailer / ADetailer-class)
4. Tiled diffusion upscale
5. Final restorers & GAN upscalers
6. Inpainting craft
7. Color management
8. Detail tricks (Detail Daemon, PAG)

---

## 1. Base generation & the two-pass discipline

Generate the base at the model's native resolution, or below it, and **judge composition only**. Composition means pose, layout, and framing. Reroll the seed freely at this stage. Minor defects such as soft faces or mangled hands are downstream problems, so ignore them here. One discipline makes multi-stage pipelines cheap: **preview after the base pass, and again after the refine pass, before committing to the expensive upscale stages.** Make every later stage bypassable, using rgthree Fast Muter or native Subgraph toggles. That way you pay for the heavy passes only once the base is right.

Base habits differ by model family:
- **SDXL-family:** use a 1024-area bucket. Going far outside it duplicates subjects. UNet-era models benefit from the full ladder.
- **Flux/Z-Image/DiT-era:** generate a native 1–2 MP base. These models usually skip the classic low-res-first hires dance. Their second pass is a refine/detail pass, not a resolution climb. Z-Image is the exception: it prefers a low base of about 0.6 MP followed by climbing — [`z-image`](../../z-image/).

## 2. The hires / refine second pass

There are two mechanically different routes. Their denoise tolerance differs, and that difference explains most "hires fix ruined my image" reports:

| Route | Chain | Denoise | Why |
|---|---|---|---|
| **Latent upscale** | `LatentUpscaleBy` (bislerp ×1.5–1.7) → KSampler | **≥ ~0.5** … or accept artifacts | latent interpolation creates off-manifold values; the sampler needs enough denoise to repair them |
| **Pixel upscale** | VAE Decode → `ImageUpscaleWithModel` (ESRGAN) → VAE Encode → KSampler | **0.25–0.35** | the upscaled image is clean, so low denoise just adds detail without re-composing |

There is also a middle path. sandner.art's latent-interpolate trick blends the original and upscaled latents, which lets you run about 0.55 denoise without losing the composition `[community — sandner.art]`.

Use the **same seed across passes** to keep results coherent. Fix the seed once you find the composition.

## 3. Detailers

Impact Pack's **FaceDetailer** is the standard detailer. It detects a face, crops it, upscales the crop, re-samples it, and stitches it back. It is **model-agnostic**: SDXL, Pony, Flux, and Z-Image all run it `[official — ltdrdata/ComfyUI-Impact-Pack]`.

Settings `[community — myByways, Civitai workflow conventions]`:
- **denoise 0.4–0.5** as the default; drop toward 0.35 to preserve identity, raise toward 0.54 for more prompt/LoRA adherence
- `guide_size` 512, `max_size` 1024 (SDXL-class)
- `bbox_crop_factor` defaults to 3; a value of ~1.3–2 gives tighter face context and fewer background repaints
- detector: yolov8m bbox plus SAM for masks; hands and eyes have dedicated detector models

**The character-LoRA swap happens at this stage.** Generate the base without the character LoRA, then load the LoRA only in the detailer pass. This gives the full sampling budget to the face, with no drag on the body or composition. Match the detailer prompt to the image. Per-model detail lives in each model skill's `characters.md`, for example [`sdxl`](../../sdxl/references/characters.md) and [`z-image`](../../z-image/references/characters.md).

**Per-face routing handles multi-character scenes.** ADetailer splits its prompt on `[SEP]`, one segment per detected face, ordered left to right, and each segment can carry its own LoRA. In ComfyUI the same pattern is built from per-SEGS detailer passes `[official — ADetailer discussion #533]`.

## 4. Tiled diffusion upscale `[community — Civitai USDU workflow conventions; convergent]`

`UltimateSDUpscale` (ssitu) is the workhorse here. It runs tile-by-tile img2img over an image that ESRGAN has already pre-upscaled.

- **Denoise 0.2–0.35.** High denoise at this stage invents new content in every tile.
- **Tile size** should be about the model's native resolution (1024 for SDXL-class). Add overlap, and enable **seam-fix mode** (half-tile is the usual pick) when seams show.
- **Simplify the prompt for the upscale pass.** A tile only sees its local patch, so a prompt like "a tattoo reading 'X' below the collarbone" gets stamped onto every smooth-skin tile. Pass a generic quality prompt instead of the full scene prompt.
- **For DiT models, prefer TTPlanet's TTP Toolset.** It tiles the image and runs an interrogator to caption *each tile*, which gives per-tile conditioning. That per-tile prompting is the anti-hallucination mechanism, and the toolset was built explicitly "for DiT models… Flux, Hunyuan, SD3." TTPlanet also ships the de-facto SDXL tile ControlNet (`TTPLanet_SDXL_Controlnet_Tile_Realistic`) for ControlNet-assisted tiling `[official — TTPlanet repos]`.
- An alternative is `shiimizu/ComfyUI-TiledDiffusion`, which offers MultiDiffusion / Mixture-of-Diffusers plus tiled VAE.

## 5. Final restorers & GAN upscalers

| Tool | Status (mid-2026) | Use |
|---|---|---|
| **SeedVR2** (ByteDance) | **the current default finisher** — one-step diffusion restorer, official ComfyUI node, 3B/7B + FP8/GGUF | final restoration/upscale to ~4K; images and video. MyAIForce found SeedVR2 chains beat SUPIR chains on skin texture `[community — MyAIForce]` |
| **SUPIR** | **frozen** — kijai's wrapper README says "FINAL update"; merged into ComfyUI core; needs an SDXL checkpoint + 32 GB+ system RAM | stale-but-functional; existing workflows keep working, don't build new ones on it |
| **ESRGAN-class models** (4x-UltraSharp, Remacri, 4xNomos series) | evergreen | the cheap deterministic step — pre-upscaler feeding tiled diffusion, or a final ×2 with zero hallucination risk |
| 1× skin-contrast models (e.g. `1xSkinContrast-High`) | niche | blended at ~0.4 over the final image for skin micro-texture (photoreal only) |

The typical max-quality chain runs tiled diffusion to about 2×, then SeedVR2 to 4K. The typical fast chain is a single ESRGAN ×2 pass.

**Generative restorers are a different class, and the numbers show it.** `ReDetail` does not restore a clip; it re-renders the clip through [`ltx-2-5`](../../ltx-2-5/). Its scale factor therefore buys invented detail rather than recovered detail, which is why its author prefers 1.5× over 2×. On 243 frames from 768×1408, the run took **7 min and 65 GB peak VRAM at 1.5×, against 17 min and 80.5 GB at 2×** `[community — DaLyon92x]`. ReDetail also has constraints that fail silently: dimensions must be divisible by 64, frame counts must be `8n + 1`, and an audio track is mandatory. Those live in SKILL.md, so a reader meets them before building.

**Here is the full reason restore-before-interpolate holds.** A temporal restorer such as SeedVR2 or FlashVSR is trained to remove real degradation, meaning compression noise or generation softness. It does this by reading neighbouring *real* frames as corroborating evidence for what the clean signal should look like. A frame interpolator such as RIFE solves a different problem. Given two real frames, it warps the pixels along the estimated motion to synthesize the frames between them. The warp has no concept of "noise" versus "detail." It faithfully carries forward whatever texture is present in its two source frames, and it adds a defect of its own wherever the flow estimate is wrong: a smear across the interpolated frame, or ghosting where an edge is occluded in one source frame and not the other.

If you run interpolation first, both problems compound. Frame count roughly doubles, because that is what raising fps means, so the restorer has twice the frames to process. That is the workload cost. The quality cost is worse: half of those frames never existed. They are the interpolator's synthetic output, and their defect is a warp artefact, which is not the kind of degradation the restorer's training distribution was built to recognise and correct. The restorer either passes the smear through unchanged, or it "sharpens" the smear by treating the artefact as legitimate high-frequency detail, baking it permanently into the final frame. Run restoration first and this problem collapses. The restorer only ever touches real frames, so the interpolator's two source frames are already clean, and the synthetic in-betweens it warps between them inherit that correction instead of the original flaw.

The same logic explains why a **per-frame image upscaler** is never the right tool for the restore step, regardless of ordering. It processes each frame in isolation, so nothing enforces agreement between what it invents on frame *N* and what it invents on frame *N+1*. The result shimmers, because a purely spatial upscaler has no mechanism to know a temporal axis exists.

## 6. Inpainting craft

- **Crop-and-stitch:** `ComfyUI-Inpaint-CropAndStitch` (lquesada; mirrored under the Comfy org) crops the masked region, samples it at the model's native resolution, then stitches it back. This is the fix for "inpainted a small face and got mush", which happens because the region was being sampled at far below native resolution `[official — lquesada/ComfyUI-Inpaint-CropAndStitch]`.
- Use **`InpaintModelConditioning`** rather than VAE-Encode-for-inpaint. It lets denoise below 1.0 work, so you can do identity-preserving partial repaints.
- **Differential Diffusion** (a core node) turns gradient masks into per-pixel denoise strength `[official]`. The standard recipe is: Gaussian-blur the mask, then `DifferentialDiffusion`, then `InpaintModelConditioning`. This gives soft transitions instead of visible inpaint borders.
- SDXL-specific: Acly's inpaint nodes (Fooocus inpaint head, LaMa pre-fill) remain current.
- Masking: use SAM-family grounding nodes (`SAM3Grounding` etc.), then dilate the mask by about 8 px before sampling.

## 7. Color management

Every VAE decode/encode round-trip and every re-sample shifts color slightly. Long pipelines compound the drift. Mixed-model pipelines compound it especially, because they cross two different VAEs.

- **Fix color once, at the end.** Use a **ColorMatch node (KJNodes**; `mkl` or `hm-mvgd-hm`) that compares the final image against the chosen composition reference, which is usually the post-refine image. Per-stage correction just adds churn.
- Some hires bundles, such as ThetaCursed's HiresFix-Ultra, build histogram correction into the hires stage. That is fine, but the end-of-pipe match is the load-bearing one.
- Watch for drift specifically after tiled upscale (per-tile VAE trips), after cross-model handoffs, and after fp16 VAE decodes.

## 8. Detail tricks

- **Detail Daemon** (Jonseed; a port of muerrilla's A1111 extension): its `Multiply Sigmas` and `Lying Sigma Sampler` nodes adjust the sigma schedule to add micro-detail **without changing composition**. It works on Flux, SDXL, and SD1.5 `[official — Jonseed/ComfyUI-Detail-Daemon]`. Use it in the refine pass, not the base.
- **PAG (Perturbed-Attention Guidance):** a core ComfyUI node `[official]`; pamparamm's pack adds SEG/NAG/FDG variants. PAG adds coherence and detail at a compute cost. **Use it sparingly or not at all with distilled/guidance-off models** (Turbo/Lightning/klein-distilled). PAG works by adding a second guidance term, and a guidance-distilled model runs at CFG 1 precisely because it was trained to need none. The perturbation therefore has nothing to steer against, and mostly just costs compute.
- Do not stack these tricks with a high-denoise pass. They shine when denoise is low and you want detail without risk.
