---
name: image-production-workflows
description: >
  Model-agnostic guide to professional image production with open image models — multi-stage pipelines and mixed-model workflows in ComfyUI, diffusers, or ComfyScript. Use this whenever the user wants production/professional quality rather than a single render, even obliquely: building a multi-stage pipeline (base gen → refine/hires pass → FaceDetailer → tiled upscale → final restorer), upscaling to print/4K (UltimateSDUpscale, TTP tiles, SeedVR2, SUPIR status, ESRGAN models), fixing pipeline artefacts (tile seams, per-tile hallucinations, color shift between passes, identity drift in a refine pass, black/garbage output after feeding one model's latent to another), combining or chaining different models ("refine my SDXL render with Flux/Z-Image", "use SDXL ControlNet then render in a DiT", "add Ideogram text to this"), the cross-family handoff rules (decode to pixels, denoise bands, resolution matching), regional prompting and inpainting craft (crop-and-stitch, Differential Diffusion), or automating/parametrizing workflows as code (ComfyScript, Export-API JSON + /prompt, comfy-cli, diffusers multi-stage pipelines, wildcards, batch QC, subgraphs, rgthree). Model-specific numbers live in the z-image, sdxl, flux-2, and ideogram-4 skills — this skill owns the craft that spans them.
---

# Image Production Workflows

This is the **cross-model** skill of the suite: the craft of getting professional results out of open image models by *layering passes* and *mixing models*, rather than hoping one render comes out perfect. It assumes you run models directly — ComfyUI, diffusers, or ComfyScript — and it complements the per-model skills (`z-image`, `sdxl`, `flux-2`, `ideogram-4`), which own their models' exact node settings, prompting dialects, and LoRA ecosystems.

Two ideas organize everything here:

1. **Quality is layered, not summoned.** A production image is a pipeline — composition pass, refine pass, detail pass, upscale pass, finish — each judged on one thing, each cheap to redo in isolation.
2. **Models are specialists, and pipelines can hire more than one.** SDXL has the deepest control/LoRA ecosystem; the DiT models (Flux.2, Z-Image) render more naturally; Ideogram 4 owns typography. Cross-model handoffs went mainstream in 2025–26 — named community workflows compose in one model and refine in another, and the mechanics are simple once you know the three rules.

---

## The production ladder

| # | Stage | Tool | Judge / settings |
|---|---|---|---|
| 1 | **Base gen** | the model's stock graph | composition only — reroll freely; native-res bucket |
| 2 | **Refine / hires pass** | latent upscale (denoise ≥ ~0.5) *or* pixel upscale + re-sample (**0.25–0.35**) | fine detail: fingers, faces, text |
| 3 | **Detailers** | Impact Pack FaceDetailer (model-agnostic), denoise ~0.4–0.5 | faces/hands/eyes; **character LoRA swaps in here** |
| 4 | **Tiled upscale** | `UltimateSDUpscale` (denoise 0.2–0.35, simplified prompt) — DiTs: **TTP Toolset** (per-tile captions) | resolution + micro-detail |
| 5 | **Finish** | **ColorMatch** vs the post-refine reference; **SeedVR2** restorer | color truth; final 4K push |

Every stage past 1 is **bypassable** — preview after stages 1 and 2 before paying for the heavy passes. Climb only the rungs your model needs: SDXL-family work uses the full ladder; Flux/Z-Image generate 1–2 MP natively and usually skip the classic hires climb (their stage 2 is a refine pass, not a resolution jump). Full per-stage settings: **`references/production-ladder.md`**.

---

## The one rule that changes everything

**After the base pass, everything is img2img — and denoise is the master knob.** Every stage of the ladder, every cross-model handoff, every detailer and tile pass is the same operation: re-render this image, keeping `1 − denoise` of it. Internalize the bands and the whole pipeline becomes predictable:

| Denoise | What the pass does |
|---|---|
| < ~0.2 | texture-only — usually pointless |
| **0.2–0.35** | re-renders surfaces; composition, identity, pose survive — the workhorse band for refines, tiles, and cross-model handoffs |
| 0.4–0.5 | stronger restyle; faces start to drift — re-assert identity afterward |
| > ~0.6 | re-composes; you're treating the input as an init image |

Most pipeline failures are a denoise mismatch: seams and per-tile inventions = tiled denoise too high; "the refine pass changed my character's face" = refine denoise above ~0.35 with no detailer re-assert; "hires fix wrecked the composition" = latent-upscale route at the pixel-route's low denoise (latent interpolation *needs* ≥ ~0.5 to repair itself — that asymmetry is the most-misunderstood fact in multi-stage work).

---

## Mixing models — the three handoff rules

1. **Decode to pixels between families.** Latent spaces are family-specific (FLUX.2's VAE is its own; SDXL's is not Z-Image's). Foreign latents → garbage, sometimes subtle. Always `VAE Decode (A) → image → VAE Encode (B)`. diffusers does this by construction: `pipe_b(image=pipe_a(...).images[0], strength=0.3)`.
2. **Identity-preserving refines live at denoise ~0.2–0.5** (see the bands above; 0.25–0.35 is the sweet spot).
3. **Match resolution to the refining model's native range** — downscale-refine-upscale or tile, don't feed 4 MP raw to a 1024-class model.

The recipes that earn the trouble *(named community workflows — details and sources in `references/mixed-model-recipes.md`)*:

| Pattern | Example |
|---|---|
| **Realism refine** | SDXL base → **Z-Image-Turbo** pass (Cordina's "ZIT Refiner"); SDXL/Pony → **Flux.2 [klein]** img2img (Enzino) — klein 4B is the Apache-2.0, commercially-clean refiner |
| **Texture refine** | Flux/DiT render → **photoreal SDXL finetune** img2img (~0.3–0.55) for its skin/film character |
| **Control front-end** | compose with **SDXL's** ControlNet/IP-Adapter/regional stack → render in a DiT |
| **Typography pass** | text/design plate in **Ideogram 4** (bbox layout, transparency) → composite/inpaint elsewhere *(inferred craft — no canonical named workflow yet)* |

The pattern behind all of them: **compose where control is deepest, render where quality is highest, finish where the finisher is best.**

---

## Tool status that changed recently (mid-2026)

Stale tutorials outnumber current ones; these are the load-bearing status changes:

| Tool | Status |
|---|---|
| **SUPIR** | frozen — kijai's wrapper marked "FINAL update", merged into ComfyUI core; don't build new pipelines on it |
| **SeedVR2** | the current default finisher (official ComfyUI node, 3B/7B, FP8/GGUF) |
| **cubiq IPAdapter_plus** | maintenance-only since Apr 2025; Comfy-Org maintains a reference implementation |
| **xinsir ControlNet (SDXL)** | training stalled (GPU funding) — frozen but still SOTA; ProMax union is the pick |
| **Regional prompting on DiTs** | mask-based attention masking in ComfyUI core (PR #5942) is the *only* working approach — SD-era Regional Prompter does not transfer |
| **ComfyScript** | alive (v0.6.x, Nov 2025, ComfyUI v3 schema) — single maintainer, pin versions |
| **Subgraphs** | native since Aug 2025 — replaced group-node conventions for stage packaging |

---

## Workflows as code

Four routes, by intent (full comparison and examples: **`references/workflows-as-code.md`**):

- **ComfyScript** — write workflows *as Python* (loops, sweeps, conditionals); virtual mode drives a local or remote ComfyUI server; a transpiler converts existing workflow JSON to code.
- **Export (API) + `/prompt` + WebSocket** — the most production-proven route: build in the GUI, export API-format JSON, parametrize its input fields, POST. **comfy-cli** wraps this for shell/CI.
- **diffusers** — skip ComfyUI entirely; multi-stage and cross-model pipelines as testable Python (handoffs are pixels by construction). The trade: you lose the detailer/tiled-upscale node ecosystem.
- **Hosted wrappers** (ComfyDeploy, RunComfy serverless) — productized API-format workflows with typed inputs.

At scale, add: **subgraphs** per stage, **rgthree** plumbing (Context pipes, Fast Muter, global Seed), **wildcard/dynamic prompts** (combinatorial mode for systematic coverage), and save every stage's intermediate so a bad final diagnoses to a stage instead of a blind rerun.

---

## Failure modes & QC

| Symptom | Cause (mechanism) | Fix |
|---|---|---|
| Black or deep-fried garbage after switching models mid-graph | Latent from family A fed to family B's sampler/VAE | Decode to pixels between families (rule 1) |
| Tile seams in the upscale | No overlap/seam-fix; per-tile exposure differences | USDU seam-fix (half-tile) + overlap; ColorMatch at the end |
| Objects/text duplicated across the upscaled image | Full scene prompt passed to the tile pass — each tile renders the whole prompt locally | Simplified/generic prompt for the upscale; on DiTs use TTP per-tile captioning |
| Character's face changed in the refine pass | Refine denoise above ~0.35 | Lower denoise, or let it drift and re-assert with a detailer pass (LoRA/adapter lives there) |
| Composition destroyed by "hires fix" | Latent-upscale route run at pixel-route denoise (< 0.5) | Pixel route at 0.25–0.35, or latent route at ≥ 0.5 |
| Colors drift warmer/flatter over the pipeline | VAE round-trips + re-samples compound; two VAEs in mixed chains | One ColorMatch at the end vs the post-refine reference |
| Inpainted region is mush | Masked area sampled far below native resolution | Crop-and-stitch (sample the crop at native res); `InpaintModelConditioning` + Differential Diffusion for soft edges |
| Regional prompts ignored on Flux/Z-Image | SD-era regional tooling doesn't work on DiTs | Core attention masking (Flux); per-face detailer passes (Z-Image) |
| Batch results unreproducible | Per-stage random seeds | rgthree global Seed; fix it once composition is found |

---

## Pre-flight checklist

Before committing to the expensive passes:

1. Base composition approved at stage 1 — seed fixed?
2. Every optional stage bypassable, previewed cheap-first?
3. Each pass's denoise in the right band for its job (refine 0.25–0.35; tiles 0.2–0.35; latent-hires ≥ 0.5)?
4. Cross-model handoff: decoded to pixels, resolution matched, refine denoise ≤ ~0.35?
5. Tile pass given a simplified prompt (or TTP per-tile captions on a DiT)?
6. Character work: identity re-asserted (detailer + LoRA/adapter) *after* the last whole-image pass?
7. ColorMatch at the end against the post-refine reference?
8. Finisher current (SeedVR2-class), not a frozen tool from an old tutorial?
9. If batching: API-format JSON or ComfyScript, global seed, intermediates saved per stage?

---

## The suite map

Per-model facts live in the model skills — this skill only owns what spans them:

| Skill | Its specialty | Its mixed-pipeline role |
|---|---|---|
| `sdxl` | deepest control/LoRA/adapter ecosystem | control front-end; texture back-end |
| `z-image` | realism stacking, layered ZIB/ZIT pipeline | fast realism refiner (ZIT) |
| `flux-2` | prompt comprehension, multi-reference identity; klein 4B Apache-2.0 | quality refiner (klein); composition front-end |
| `ideogram-4` | typography, layout, design | the typography pass |

---

## How to read the claims in this skill — two bars, by claim type

**Hard facts — must be exact or it breaks.** Node and repo names, the latent-incompatibility mechanism, tool maintenance statuses (SUPIR frozen, IPAdapter-plus maintenance-only, the core attention-masking PR, ComfyScript versions), API endpoints. **Source of truth is official** — the repos and ComfyUI core — and these are the volatile ones in a fast-moving node ecosystem: a tool marked "current" here can freeze in a month. **Re-verify maintenance statuses and version numbers before building new production pipelines on them**, regardless of who said it.

**Craft — what actually makes a good image.** The denoise bands, per-stage settings, the handoff rules, the named mixed-model recipes, the QC habits. **The authoritative source here is the community** — named workflow authors (Cordina, Enzino, TTPlanet, ltdrdata, rgthree, MyAIForce) whose graphs have run at scale — and it's stated with confidence; ranges mean "your checkpoint and resolution differ," not "unverified." Two honest flags: the **Ideogram typography-pass pattern is inferred craft** (practiced, but no canonical named workflow was found), and **batch-QC tooling is thin** (grids + human cull is the actual state of the art).

Date-stamped June 2026. The fastest-moving parts: finisher models (SeedVR2's successors), DiT regional/per-region-LoRA tooling, and ComfyScript/frontend version compatibility.

---

## Reference files

| File | When to read it |
|---|---|
| `references/production-ladder.md` | Per-stage depth: base discipline, the two hires routes and their denoise asymmetry, detailer settings (`guide_size`/`crop_factor`, `[SEP]` routing), tiled upscale (USDU seam-fix, TTP per-tile captioning), finishers (SeedVR2/SUPIR/ESRGAN), inpainting craft (crop-and-stitch, Differential Diffusion), color management, Detail Daemon/PAG |
| `references/mixed-model-recipes.md` | The three handoff rules in full; the named recipes with sources; the per-family ControlNet/IP-Adapter status table; regional prompting status; sequencing identity work across a mixed pipeline |
| `references/workflows-as-code.md` | ComfyScript (modes, example, caveats), the Export-API/`/prompt`/comfy-cli route, diffusers as the code-first alternative, subgraphs/rgthree/wildcards/batch-QC conventions |
