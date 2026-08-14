# Suite alignment & coverage audit — 2026-06-10

Audit of the four published skills (`generated-skills/skills/{z-image,sdxl,flux-2,ideogram-4}`) against the three build-out pillars (characters, style LoRAs, complex mixed workflows) and the surface set (ComfyUI / diffusers / ComfyScript). Produced by a full read of every SKILL.md and references file.

## 1. Coverage matrix

### A. AI character creation & consistency

| Pillar | Z-Image | SDXL | Flux-2 | Ideogram-4 |
|--------|---------|------|--------|-----------|
| Character LoRA training (dataset, captioning) | **Deep** `lora-training.md §2-4` — anchor portrait, 15-25 variants with rotation/lighting variation, caption-the-residual, Ostris adapter for Turbo | **Deep** `checkpoints-and-loras.md §6` — 15-30 images, caption-the-residual, kohya_ss/OneTrainer | **Deep** `setup-and-workflows.md §8` — 10-50 images, prose captions, AI-Toolkit `is_flux2: true` | **None** — `self-hosting.md §6` "very early", Ostris PoC only |
| Face identity tools (PuLID/IP-Adapter/InstantID/ReActor/FaceDetailer) | **Shallow** `workflows.md §10` — no PuLID/IP-Adapter; character LoRA at FaceDetailer stage | **Deep** `setup-and-workflows.md §7` — IP-Adapter FaceID / FaceID Plus v2, 0.5-0.8 weight | **Deep** `controlnet-and-identity.md §3-5` — PuLID (iFayens) strength 1.0-1.4; ReferenceLatent | **None** — v3 API Character Reference only |
| Multi-reference editing | **None** | **None** | **Deep** `prompting-guide.md §6`, `setup-and-workflows.md §2` — up to 8-10 refs, ReferenceLatent | **None** |
| Consistency across poses/outfits/scenes | **Shallow** `prompting-guide.md §3.3-3.5` — 8-point rotation protocol, elevation, byte-identical clauses | **Shallow** — framing/angles listed, no rotation protocol | **Mention** — ReferenceLatent preserves "general character" but no sheet guidance | **None** |
| Character sheets / turnarounds | **Deep** `prompting-guide.md §3.3-3.4` — 8-point rotation + elevation + back-view handling | **None** | **None** | **None** |

### B. Style LoRA training

All of Z-Image / SDXL / Flux-2 are **Deep** on dataset curation, captioning strategy (style inverts the residual), tooling, hyperparameters, XY-grid evaluation, and stacking — in their respective LoRA sections (`lora-training.md`, `checkpoints-and-loras.md §4-6`, `setup-and-workflows.md §7-8`). **Ideogram-4 has none** (correctly — no LoRA ecosystem yet). Differences are in placement and emphasis, not substance.

### C. Complex multi-stage workflows

| Pillar | Z-Image | SDXL | Flux-2 | Ideogram-4 |
|--------|---------|------|--------|-----------|
| Hires-fix / latent upscale | **Deep** `workflows.md §2-4` — 1.7× bislerp, per-stage denoise | **Shallow** `setup-and-workflows.md §6` | **None** | **None** |
| Tiled upscale | **Deep** — USDU ×2, tile 1024, denoise ~0.2-0.25, per-tile hallucination warning, named upscale models | **Shallow** | **None** | **None** |
| Detailers | **Deep** — FaceDetailer stage 5, yolov8m+SAM, LoRA swap-in | **Shallow** | **None** | **None** |
| Inpainting craft | **Shallow** | **Shallow** | **Shallow** (Fun Union inpaint mode) | **Shallow** (Magic Fill mention) |
| Regional prompting | **None** | **None** | **None** | **None** |
| ControlNet combos | **Deep** `workflows.md §9` | **Shallow** `setup-and-workflows.md §7` | **Deep** `controlnet-and-identity.md §2` | **None** (n/a) |
| Mixing different models in one pipeline | **Shallow** (ZIB→ZIT, same family) | **None** | **None** | **None** |
| Final upscalers (SUPIR/SeedVR2) | **Shallow** (SeedVR2 optional stage) | **Shallow** | **None** | **None** |

### D. Surfaces

- ComfyUI graphs: **Deep everywhere** (Ideogram-4 shallowest — template-level only).
- diffusers code: **Deep** in SDXL / Flux-2 / Ideogram-4; **None in Z-Image references** (SKILL.md mentions pipeline classes only).
- **ComfyScript / workflows-as-code: zero mentions in all four skills.** Suite-wide gap.

## 2. Alignment inconsistencies

1. **LoRA section placement drift:** z-image = dedicated `lora-training.md` (training) + `workflows.md §6` (usage); sdxl = `checkpoints-and-loras.md §4-6`; flux-2 = `setup-and-workflows.md §7-8`; ideogram-4 = stub in `self-hosting.md §6`.
2. **Reference-file naming:** `workflows.md` vs `setup-and-workflows.md` vs `self-hosting.md` — same concern slot, three names.
3. **Confidence-tag style drift:** flux-2/ideogram-4 use formal inline tags (`[official]`, `[community]`, `[flagged]`); z-image conversational; sdxl middle ground. The closing "two bars" section exists in all four with wording drift only.
4. **Trigger-word guidance** worded differently for the same encoder-class fact: z-image "folded into natural language", flux-2 "mostly doesn't want them", SDXL "must appear verbatim" (correctly opposite — CLIP). The doctrine is *encoder-class-determined* but never stated as such.
5. **Multi-stage workflow section:** only z-image has the orchestrated pipeline in SKILL.md; sdxl/flux-2 list components without orchestration.
6. **Myth-debunks propagate unevenly:** sub-1.0-strength-is-normal in all three LoRA skills; alpha=2×rank legitimacy in sdxl/flux-2 only; speed-LoRA no-hard-cap in z-image only.
7. **Cross-link mesh incomplete:** SKILL.md-level "choose the model" notes exist but no references-level comparison; no suite-wide pillar matrix (which model for characters / typography / control stack).

## 3. Best-in-class per pillar (use as template for the others)

- **Characters:** Z-Image — 8-point rotation protocol (`prompting-guide.md §3.3-3.5`) + FaceDetailer LoRA swap (`workflows.md §6, §10`).
- **Style LoRA training:** SDXL — `checkpoints-and-loras.md §6` (tooling maturity, converged recipes from named sources, contested points flagged).
- **Multi-stage workflows:** Z-Image — `workflows.md §2-7` (named stages, per-stage settings table, two-pass discipline, resolution ladder, optional-stage toggles).
- **ComfyUI graphs:** Z-Image. **diffusers code:** Flux-2 (SDXL close second).
- **Licence/surface handling:** Ideogram-4.
