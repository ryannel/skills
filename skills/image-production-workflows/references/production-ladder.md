# The Production Ladder — multi-stage settings in depth

Stage-by-stage detail for the base → refine → detail → upscale → finish ladder. Settings are community-convergent starting points from named workflow authors; your checkpoint and resolution shift them — that's why they're ranges.

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

Generate the base at (or below) the model's native resolution and **judge composition only** — pose, layout, framing. Reroll the seed freely; minor defects (soft faces, mangled hands) are downstream problems. The discipline that makes multi-stage pipelines cheap: **preview after the base pass and again after the refine pass, before committing to the expensive upscale stages.** Every later stage should be bypassable (rgthree Fast Muter / native Subgraph toggles) so you pay for heavy passes only once the base is right.

Per-family base habits:
- **SDXL-family:** 1024-area bucket (going far outside duplicates subjects). UNet-era models benefit from the full ladder.
- **Flux/Z-Image/DiT-era:** native 1–2 MP base; the classic low-res-first hires dance is usually skipped — their second pass is a refine/detail pass, not a resolution climb. Z-Image is the exception that *prefers* a low base (~0.6 MP) and climbing (see the z-image skill).

## 2. The hires / refine second pass

Two mechanically different routes; the denoise tolerance differs and explains most "hires fix ruined my image" reports:

| Route | Chain | Denoise | Why |
|---|---|---|---|
| **Latent upscale** | `LatentUpscaleBy` (bislerp ×1.5–1.7) → KSampler | **≥ ~0.5** … or accept artifacts | latent interpolation creates off-manifold values; the sampler needs enough denoise to repair them |
| **Pixel upscale** | VAE Decode → `ImageUpscaleWithModel` (ESRGAN) → VAE Encode → KSampler | **0.25–0.35** | the upscaled image is clean, so low denoise just adds detail without re-composing |

A middle path (sandner.art's latent-interpolate trick) blends original and upscaled latents to run ~0.55 denoise without composition loss. *(Community, named.)*

**Same seed across passes** keeps results coherent; fix the seed once composition is found.

## 3. Detailers

Impact Pack's **FaceDetailer** (detect → crop → upscale crop → re-sample → stitch) is the standard and is **model-agnostic** — SDXL, Pony, Flux, Z-Image all run it. *(Official — ltdrdata/ComfyUI-Impact-Pack.)*

Consensus settings *(community, named — myByways' writeup; Civitai workflow conventions)*:
- **denoise 0.4–0.5** default; drop toward 0.35 to preserve identity, raise toward 0.54 for more prompt/LoRA adherence
- `guide_size` 512, `max_size` 1024 (SDXL-class)
- `bbox_crop_factor` default 3; ~1.3–2 gives tighter face context and fewer background repaints
- detector: yolov8m bbox + SAM for masks; hands and eyes have dedicated detector models

**The character-LoRA swap happens here:** generate the base without the character LoRA, load it only in the detailer pass (full sampling budget on the face, no body/composition drag). Match the detailer prompt to the image. Per-model detail in each model skill's `characters.md`.

**Per-face routing for multi-character scenes:** ADetailer splits its prompt on `[SEP]` per detected face (left-to-right), each segment carrying its own LoRA; in ComfyUI the same pattern is per-SEGS detailer passes. *(Official ADetailer discussion #533.)*

## 4. Tiled diffusion upscale

`UltimateSDUpscale` (ssitu) is the workhorse: tile-by-tile img2img over an ESRGAN-pre-upscaled image.

- **Denoise 0.2–0.35** — high denoise here invents new content *per tile*.
- **Tile size** ≈ the model's native resolution (1024 for SDXL-class); overlap + **seam-fix mode** (half-tile is the usual pick) when seams show.
- **Simplify the prompt for the upscale pass.** A tile only sees its local patch: "a tattoo reading 'X' below the collarbone" gets stamped onto every smooth-skin tile. Pass a generic quality prompt, not the full scene prompt.
- **DiT models: prefer TTPlanet's TTP Toolset** — it tiles the image and runs an interrogator to caption *each tile*, giving per-tile conditioning. That per-tile prompting is the anti-hallucination mechanism, built explicitly "for DiT models… Flux, Hunyuan, SD3." TTPlanet also ships the de-facto SDXL tile ControlNet (`TTPLanet_SDXL_Controlnet_Tile_Realistic`) for ControlNet-assisted tiling. *(Official repos.)*
- Alternative: `shiimizu/ComfyUI-TiledDiffusion` (MultiDiffusion / Mixture-of-Diffusers + tiled VAE).

## 5. Final restorers & GAN upscalers

| Tool | Status (mid-2026) | Use |
|---|---|---|
| **SeedVR2** (ByteDance) | **the current default finisher** — one-step diffusion restorer, official ComfyUI node, 3B/7B + FP8/GGUF | final restoration/upscale to ~4K; images and video. MyAIForce found SeedVR2 chains beat SUPIR chains on skin texture *(community, named)* |
| **SUPIR** | **frozen** — kijai's wrapper README says "FINAL update"; merged into ComfyUI core; needs an SDXL checkpoint + 32 GB+ system RAM | stale-but-functional; existing workflows keep working, don't build new ones on it |
| **ESRGAN-class models** (4x-UltraSharp, Remacri, 4xNomos series) | evergreen | the cheap deterministic step — pre-upscaler feeding tiled diffusion, or a final ×2 with zero hallucination risk |
| 1× skin-contrast models (e.g. `1xSkinContrast-High`) | niche | blended at ~0.4 over the final image for skin micro-texture (photoreal only) |

Typical max-quality chain: tiled diffusion to ~2× → SeedVR2 to 4K. Typical fast chain: ESRGAN ×2, done.

## 6. Inpainting craft

- **Crop-and-stitch:** `ComfyUI-Inpaint-CropAndStitch` (lquesada; mirrored under the Comfy org) crops the masked region, samples it at the model's native resolution, stitches back — the fix for "inpainted a small face and got mush" (the region was being sampled at far-below-native res). *(Official.)*
- **`InpaintModelConditioning`**, not VAE-Encode-for-inpaint, so denoise < 1.0 works and you can do identity-preserving partial repaints.
- **Differential Diffusion** (core node): gradient masks → per-pixel denoise strength. Standard recipe: Gaussian-blur the mask → `DifferentialDiffusion` → `InpaintModelConditioning`. Soft transitions instead of visible inpaint borders. *(Official node; community recipe.)*
- SDXL-specific: Acly's inpaint nodes (Fooocus inpaint head, LaMa pre-fill) remain current.
- Masking: SAM-family grounding nodes (`SAM3Grounding` etc.) → dilate the mask ~8 px before sampling.

## 7. Color management

Every VAE decode/encode round-trip and every re-sample shifts color slightly; long pipelines (and mixed-model pipelines especially — two different VAEs) compound the drift.

- **Fix once, at the end:** a **ColorMatch node (KJNodes**; `mkl` or `hm-mvgd-hm`) comparing the final image against the chosen composition reference (usually the post-refine image). Per-stage correction just adds churn.
- Some hires bundles (ThetaCursed's HiresFix-Ultra) build histogram correction into the hires stage — fine, but the end-of-pipe match is the load-bearing one.
- Watch for it specifically after: tiled upscale (per-tile VAE trips), cross-model handoffs, and fp16 VAE decodes.

## 8. Detail tricks

- **Detail Daemon** (Jonseed; port of muerrilla's A1111 extension): `Multiply Sigmas` / `Lying Sigma Sampler` adjust the sigma schedule to add micro-detail **without changing composition** — works on Flux, SDXL, SD1.5. Use in the refine pass, not the base. *(Official repo.)*
- **PAG (Perturbed-Attention Guidance):** core ComfyUI node; pamparamm's pack adds SEG/NAG/FDG variants. Adds coherence/detail at a compute cost. **Use sparingly or not at all with distilled/guidance-off models** (Turbo/Lightning/klein-distilled) — they weren't trained for extra guidance terms.
- Don't stack these with a high-denoise pass — they shine when denoise is low and you want detail without risk.
