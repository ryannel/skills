# The Production Ladder — multi-stage settings in depth

Stage-by-stage detail for the base → refine → detail → upscale → finish ladder. Settings are starting points that named workflow authors converge on, and each is attributed where it appears. Your checkpoint and resolution will shift them, which is why they are given as ranges.

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

Generate the base at (or below) the model's native resolution and **judge composition only** — pose, layout, framing. Reroll the seed freely. Minor defects (soft faces, mangled hands) are downstream problems. The discipline that makes multi-stage pipelines cheap: **preview after the base pass, and again after the refine pass, before committing to the expensive upscale stages.** Every later stage should be bypassable (rgthree Fast Muter / native Subgraph toggles), so you pay for heavy passes only once the base is right.

Per-family base habits:
- **SDXL-family:** 1024-area bucket (going far outside duplicates subjects). UNet-era models benefit from the full ladder.
- **Flux/Z-Image/DiT-era:** native 1–2 MP base. The classic low-res-first hires dance is usually skipped — their second pass is a refine/detail pass, not a resolution climb. Z-Image is the exception that *prefers* a low base (~0.6 MP) and climbing — [`z-image`](../../z-image/).

## 2. The hires / refine second pass

There are two mechanically different routes. The denoise tolerance differs between them, and that difference explains most "hires fix ruined my image" reports:

| Route | Chain | Denoise | Why |
|---|---|---|---|
| **Latent upscale** | `LatentUpscaleBy` (bislerp ×1.5–1.7) → KSampler | **≥ ~0.5** … or accept artifacts | latent interpolation creates off-manifold values; the sampler needs enough denoise to repair them |
| **Pixel upscale** | VAE Decode → `ImageUpscaleWithModel` (ESRGAN) → VAE Encode → KSampler | **0.25–0.35** | the upscaled image is clean, so low denoise just adds detail without re-composing |

A middle path exists too: sandner.art's latent-interpolate trick blends original and upscaled latents to run ~0.55 denoise without composition loss `[community — sandner.art]`.

**Same seed across passes** keeps results coherent. Fix the seed once composition is found.

## 3. Detailers

Impact Pack's **FaceDetailer** (detect → crop → upscale crop → re-sample → stitch) is the standard, and it is **model-agnostic** — SDXL, Pony, Flux, Z-Image all run it `[official — ltdrdata/ComfyUI-Impact-Pack]`.

Settings `[community — myByways, Civitai workflow conventions]`:
- **denoise 0.4–0.5** default; drop toward 0.35 to preserve identity, raise toward 0.54 for more prompt/LoRA adherence
- `guide_size` 512, `max_size` 1024 (SDXL-class)
- `bbox_crop_factor` default 3; ~1.3–2 gives tighter face context and fewer background repaints
- detector: yolov8m bbox + SAM for masks; hands and eyes have dedicated detector models

**The character-LoRA swap happens here.** Generate the base without the character LoRA, then load it only in the detailer pass, giving the full sampling budget to the face with no body/composition drag. Match the detailer prompt to the image. Per-model detail lives in each model skill's `characters.md` — e.g. [`sdxl`](../../sdxl/references/characters.md), [`z-image`](../../z-image/references/characters.md).

**Per-face routing for multi-character scenes:** ADetailer splits its prompt on `[SEP]` per detected face (left-to-right), with each segment carrying its own LoRA. In ComfyUI the same pattern is per-SEGS detailer passes `[official — ADetailer discussion #533]`.

## 4. Tiled diffusion upscale `[community — Civitai USDU workflow conventions; convergent]`

`UltimateSDUpscale` (ssitu) is the workhorse: tile-by-tile img2img over an ESRGAN-pre-upscaled image.

- **Denoise 0.2–0.35.** High denoise here invents new content *per tile*.
- **Tile size** ≈ the model's native resolution (1024 for SDXL-class), with overlap plus **seam-fix mode** (half-tile is the usual pick) when seams show.
- **Simplify the prompt for the upscale pass.** A tile only sees its local patch, so "a tattoo reading 'X' below the collarbone" gets stamped onto every smooth-skin tile. Pass a generic quality prompt instead of the full scene prompt.
- **For DiT models, prefer TTPlanet's TTP Toolset.** It tiles the image and runs an interrogator to caption *each tile*, giving per-tile conditioning. That per-tile prompting is the anti-hallucination mechanism, built explicitly "for DiT models… Flux, Hunyuan, SD3." TTPlanet also ships the de-facto SDXL tile ControlNet (`TTPLanet_SDXL_Controlnet_Tile_Realistic`) for ControlNet-assisted tiling `[official — TTPlanet repos]`.
- An alternative is `shiimizu/ComfyUI-TiledDiffusion` (MultiDiffusion / Mixture-of-Diffusers + tiled VAE).

## 5. Final restorers & GAN upscalers

| Tool | Status (mid-2026) | Use |
|---|---|---|
| **SeedVR2** (ByteDance) | **the current default finisher** — one-step diffusion restorer, official ComfyUI node, 3B/7B + FP8/GGUF | final restoration/upscale to ~4K; images and video. MyAIForce found SeedVR2 chains beat SUPIR chains on skin texture `[community — MyAIForce]` |
| **SUPIR** | **frozen** — kijai's wrapper README says "FINAL update"; merged into ComfyUI core; needs an SDXL checkpoint + 32 GB+ system RAM | stale-but-functional; existing workflows keep working, don't build new ones on it |
| **ESRGAN-class models** (4x-UltraSharp, Remacri, 4xNomos series) | evergreen | the cheap deterministic step — pre-upscaler feeding tiled diffusion, or a final ×2 with zero hallucination risk |
| 1× skin-contrast models (e.g. `1xSkinContrast-High`) | niche | blended at ~0.4 over the final image for skin micro-texture (photoreal only) |

Typical max-quality chain: tiled diffusion to ~2×, then SeedVR2 to 4K. Typical fast chain: ESRGAN ×2, done.

**Generative restorers are a different class, and the numbers say so.** `ReDetail` re-renders a clip through [`ltx-2-5`](../../ltx-2-5/) instead of restoring it, so its scale factor buys invented detail rather than recovered detail. That is why its author prefers 1.5× to 2×. On 243 frames from 768×1408: **7 min and 65 GB peak VRAM at 1.5×, against 17 min and 80.5 GB at 2×** `[community — DaLyon92x]`. The constraints that fail silently (dimensions divisible by 64, `8n + 1` frames, a mandatory audio track) are in SKILL.md, where a reader meets them before building.

**Why restore-before-interpolate holds, in full.** A temporal restorer (SeedVR2, FlashVSR) is trained to remove real degradation — compression noise, generation softness — by reading neighbouring *real* frames as corroborating evidence for what the clean signal should look like. A frame interpolator (RIFE) solves a different problem: given two real frames, it warps the pixels along the estimated motion to synthesize the frames between them. The warp has no concept of "noise" versus "detail." It carries forward whatever texture is present in its two source frames, faithfully, and adds a defect of its own wherever the flow estimate is wrong: smear across the interpolated frame, or ghosting where an edge is occluded in one source frame and not the other.

Run interpolation first and both problems compound. Frame count roughly doubles — that is what raising fps means — so the restorer has twice the frames to process. That is the *workload* cost. Worse, half of those frames never existed. They are the interpolator's synthetic output, and their defect is a warp artefact, not the kind of degradation the restorer's training distribution was built to recognise and correct. The restorer either passes the smear through unchanged or, worse, "sharpens" it, treating the artefact as legitimate high-frequency detail and baking it permanently into the final frame. Run restoration first and this problem collapses: the restorer only ever touches real frames, so the interpolator's two source frames are already clean, and the synthetic in-betweens it warps between them inherit that correction instead of the original flaw.

This is also why a **per-frame image upscaler** is never the right tool for the restore step, regardless of ordering. It processes each frame in isolation, so nothing enforces agreement between what it invents on frame *N* and frame *N+1*. The result shimmers, since a purely spatial upscaler has no mechanism to know a temporal axis exists.

## 6. Inpainting craft

- **Crop-and-stitch:** `ComfyUI-Inpaint-CropAndStitch` (lquesada; mirrored under the Comfy org) crops the masked region, samples it at the model's native resolution, then stitches it back. This is the fix for "inpainted a small face and got mush" — the region was being sampled at far-below-native res `[official — lquesada/ComfyUI-Inpaint-CropAndStitch]`.
- **`InpaintModelConditioning`**, not VAE-Encode-for-inpaint, so denoise < 1.0 works and you can do identity-preserving partial repaints.
- **Differential Diffusion** (core node): gradient masks → per-pixel denoise strength `[official]`. Standard recipe: Gaussian-blur the mask → `DifferentialDiffusion` → `InpaintModelConditioning`, which gives soft transitions instead of visible inpaint borders.
- SDXL-specific: Acly's inpaint nodes (Fooocus inpaint head, LaMa pre-fill) remain current.
- Masking: SAM-family grounding nodes (`SAM3Grounding` etc.) → dilate the mask ~8 px before sampling.

## 7. Color management

Every VAE decode/encode round-trip and every re-sample shifts color slightly. Long pipelines compound the drift, and mixed-model pipelines compound it especially, since they cross two different VAEs.

- **Fix once, at the end.** Use a **ColorMatch node (KJNodes**; `mkl` or `hm-mvgd-hm`) that compares the final image against the chosen composition reference (usually the post-refine image). Per-stage correction just adds churn.
- Some hires bundles (ThetaCursed's HiresFix-Ultra) build histogram correction into the hires stage. That is fine, but the end-of-pipe match is the load-bearing one.
- Watch for it specifically after tiled upscale (per-tile VAE trips), cross-model handoffs, and fp16 VAE decodes.

## 8. Detail tricks

- **Detail Daemon** (Jonseed; port of muerrilla's A1111 extension): `Multiply Sigmas` / `Lying Sigma Sampler` adjust the sigma schedule to add micro-detail **without changing composition** — works on Flux, SDXL, SD1.5 `[official — Jonseed/ComfyUI-Detail-Daemon]`. Use it in the refine pass, not the base.
- **PAG (Perturbed-Attention Guidance):** a core ComfyUI node `[official]`; pamparamm's pack adds SEG/NAG/FDG variants. It adds coherence and detail at a compute cost. **Use it sparingly or not at all with distilled/guidance-off models** (Turbo/Lightning/klein-distilled). PAG works by adding a second guidance term, and a guidance-distilled model runs at CFG 1 precisely because it was trained to need none. So the perturbation has nothing to steer against, and mostly just costs compute.
- Do not stack these with a high-denoise pass. They shine when denoise is low and you want detail without risk.
