---
name: image-production-workflows
description: >
  Model-agnostic guide to professional image production with open image models — multi-stage pipelines and
  mixed-model workflows in ComfyUI, diffusers, or ComfyScript. Use this whenever the user wants
  production/professional quality rather than a single render, even obliquely: building a multi-stage pipeline
  (base gen → refine/hires pass → FaceDetailer → tiled upscale → final restorer), upscaling to print/4K
  (UltimateSDUpscale, TTP tiles, SeedVR2, SUPIR status, ESRGAN models), fixing pipeline artefacts (tile seams,
  per-tile hallucinations, color shift between passes, identity drift in a refine pass, black/garbage output
  after feeding one model's latent to another), combining or chaining different models ("refine my SDXL render
  with Flux/Z-Image", "use SDXL ControlNet then render in a DiT", "add Ideogram text to this", "compose in
  Anima then refine"), the cross-family handoff rules (decode to pixels, denoise bands, resolution matching),
  whether the **licences of every model in a chain** allow the finished pipeline to ship, using a **video
  model as an image-edit stage** (MiniMax H3 at one frame) or an image edit as the **first frame of a video
  job**, choosing between restoring and **generatively re-rendering** an upscale, regional prompting and
  inpainting craft (crop-and-stitch, Differential Diffusion), or automating/parametrizing workflows as code
  (ComfyScript, Export-API JSON + /prompt, comfy-cli, diffusers multi-stage pipelines, wildcards, batch QC,
  subgraphs, rgthree). Model-specific numbers live in the z-image, sdxl, flux-2, ideogram-4, krea-2 and anima
  skills; video handoffs belong to wan-2-2, minimax-h3, ltx-2-5 and scail-2 — this skill owns the craft that
  spans them. Choosing between models, comparing them, or working out which skills and install commands a job
  needs is [`generative-media-atlas`](../generative-media-atlas/)'s job — start there when the model is not
  already settled.
---

# Image Production Workflows

This is the **cross-model** skill of the suite. It shows you how to get professional results from open image models by *layering passes* and *mixing models*, instead of hoping one render comes out perfect. It assumes you run models directly — in ComfyUI, diffusers, or ComfyScript. It complements the per-model skills ([`sdxl`](../sdxl/), [`z-image`](../z-image/), [`flux-2`](../flux-2/), [`ideogram-4`](../ideogram-4/), [`krea-2`](../krea-2/), [`anima`](../anima/)), which own their own node settings, prompting dialects and LoRA ecosystems.

Two ideas organize everything here:

1. **Quality is layered, not summoned.** A production image is a pipeline of passes. Each pass is judged on one thing, and is cheap to redo on its own.
2. **Models are specialists, and a pipeline can hire more than one.** The mechanics are simple once you know the three rules. Which model is good at what is the suite map at the end.

> **A `../link/` on this page that doesn't resolve is a skill you have not installed, not a broken
> page.** [`generative-media-atlas`](../generative-media-atlas/) is the map of this suite: which
> model fits a job, which skills that job needs, and the commands to install them. It works on its
> own, so it is the one to add first — `npx skills add ryannel/skills --skill generative-media-atlas`

---

## What this owns, and what it doesn't

Three skills can plausibly answer "how do I build this pipeline?" Two tests settle almost every case.

- **Versus a model skill's `setup-and-workflows.md`**, which owns the ladder *as one model runs it*: **if changing the model changes the answer, it is the model skill's.**
- **Versus [`comfyui-on-runpod`](../comfyui-on-runpod/)**, which owns whether the graph runs at all: **if the answer is the same on your laptop and on a rented H100, it belongs here. If renting changes the answer, it belongs there.**

| Question | Where it belongs |
|---|---|
| Node settings, prompting dialect, native resolution, LoRA ecosystem, one model's licence | the model skill — [`sdxl`](../sdxl/), [`z-image`](../z-image/), [`flux-2`](../flux-2/), [`ideogram-4`](../ideogram-4/), [`krea-2`](../krea-2/), [`anima`](../anima/) |
| **The stage ladder, denoise bands, cross-family handoffs, named mixed-model recipes, regional prompting and inpainting craft, workflows-as-code** | **here** |
| **Whether every licence in a chain allows the finished pipeline to ship** | **here** — one model's terms are the model skill's; the *chain's* are nobody else's job |
| Deploying ComfyUI itself — volume layout, `extra_model_paths.yaml`, serverless, GPU cost | [`comfyui-on-runpod`](../comfyui-on-runpod/) |
| Loading and stacking a LoRA inside a graph | the model skill's `setup-and-workflows.md` |
| **Making** a character or style LoRA | [`character-lora-training`](../character-lora-training/) |
| The video ladder itself — task modes, per-stage settings | [`wan-2-2`](../wan-2-2/), [`minimax-h3`](../minimax-h3/), [`ltx-2-5`](../ltx-2-5/), [`scail-2`](../scail-2/) |
| **The restore-before-interpolate ordering rule, image or video** | **here** — see [Restore before you interpolate](#restore-before-you-interpolate) |
| Running a video-family checkpoint at one frame as an image editor | **here** — output modality decides scope, see below |

---

## The one rule that changes everything

**After the base pass, everything is img2img. Denoise is the master knob.** Every ladder stage, cross-model handoff, detailer and tile pass does the same thing: re-render this image, keeping `1 − denoise` of it. Learn the bands, and the pipeline becomes predictable:

| Denoise | What the pass does `[community — named recipes in mixed-model-recipes.md §2; convergent]` |
|---|---|
| < ~0.2 | texture-only — usually pointless |
| **0.2–0.35** | re-renders surfaces; composition, identity, pose survive — the workhorse band for refines, tiles, and cross-model handoffs |
| 0.4–0.5 | stronger restyle; faces start to drift — re-assert identity afterward |
| > ~0.6 | re-composes; you're treating the input as an init image |

These are bands, not fixed settings, because they mark where independent recipes agree — not one author's numbers. Most pipeline failures come from a denoise mismatch (see *Failure modes*, below). The most misunderstood point is the asymmetry between the two hires routes: latent interpolation *needs* ≥ ~0.5 denoise to repair itself, while the pixel route wants 0.25–0.35.

---

## The production ladder

| # | Stage | Tool | Judge / settings |
|---|---|---|---|
| 1 | **Base gen** | the model's stock graph | composition only — reroll freely; native-res bucket |
| 2 | **Refine / hires pass** | latent upscale (denoise ≥ ~0.5) *or* pixel upscale + re-sample (**0.25–0.35**) | fine detail: fingers, faces, text |
| 3 | **Detailers** | Impact Pack FaceDetailer (model-agnostic), denoise ~0.4–0.5 `[community — myByways, Civitai workflow conventions]` | faces/hands/eyes; **character LoRA swaps in here** |
| 4 | **Tiled upscale** | `UltimateSDUpscale` (denoise 0.2–0.35, simplified prompt) `[community — Civitai USDU conventions; convergent]` — DiTs: **TTP Toolset**, per-tile captions `[official — TTPlanet repos]` | resolution + micro-detail |
| 5 | **Finish** | **ColorMatch** vs the post-refine reference; **SeedVR2** restorer `[community — MyAIForce]` | color truth; final 4K push |

Every stage past 1 is **bypassable**. Preview after stages 1 and 2 before you pay for the heavy passes. Climb only the rungs your model needs. SDXL-family work uses the full ladder. Flux and Z-Image generate 1–2 MP natively, so their stage 2 refines detail rather than jumping resolution. Settings: [`references/production-ladder.md`](references/production-ladder.md).

---

## Restore before you interpolate

One more ordering choice belongs here. The video skills already state it seven times over: **restore or upscale before you interpolate, never after** `[community — convergent]`.

A temporal restorer (SeedVR2, FlashVSR) reads neighbouring *real* frames as evidence to fix real degradation. An interpolator (RIFE) warps between two real frames to invent new ones. That warp carries forward whatever is in the source — noise included — plus a smear of its own wherever the flow estimate is wrong. **Interpolate first, and the restorer inherits both defects across roughly double the frame count. Restore first, and the interpolator warps between frames that are already clean.** The same reasoning rules out a per-frame image upscaler as the restore step, at either position in the order: it has no cross-frame consistency, so the result shimmers regardless.

Full derivation, and the per-model frame-count and dimension constraints that turn a reversed order into a silent-failure trap: [`references/production-ladder.md`](references/production-ladder.md) §5. Named per model in [`wan-2-2`](../wan-2-2/), [`minimax-h3`](../minimax-h3/), [`ltx-2-5`](../ltx-2-5/), [`scail-2`](../scail-2/).

---

## Mixing models — the three handoff rules

1. **Decode to pixels between families.** Latent spaces are family-specific: FLUX.2's VAE is its own, SDXL's is not Z-Image's, and Anima's is Qwen-Image's. A foreign latent produces garbage — sometimes subtle garbage. Always go `VAE Decode (A) → image → VAE Encode (B)`. diffusers does this by construction.
2. **Identity-preserving refines live at denoise ~0.2–0.5** (the bands above; 0.25–0.35 is the sweet spot).
3. **Match resolution to the refining model's native range.** Downscale, refine, then upscale or tile — don't feed 4 MP raw to a 1024-class model.

The recipes that earn the trouble (details and sources in [`references/mixed-model-recipes.md`](references/mixed-model-recipes.md)):

| Pattern | Example |
|---|---|
| **Realism refine** | SDXL base → **Z-Image-Turbo** pass (Cordina's "ZIT Refiner"); SDXL/Pony → **Flux.2 [klein]** img2img (Enzino) |
| **Texture refine** | Flux/DiT render → **photoreal SDXL finetune** img2img (~0.3–0.55) for its skin/film character `[community — no single author; convergent]` |
| **Control front-end** | compose with **SDXL's** ControlNet/IP-Adapter/regional stack → render in a DiT `[community — "Modern Easy SDXL", Civitai]` |
| **Anime control front-end** | an SDXL anime finetune (Illustrious/NoobAI) composes with its ControlNet/regional stack → render through [`anima`](../anima/) at low denoise `[community — u/Alekite]` — the control-front-end pattern in anime clothing, and at 2B the render rung is nearly free |
| **Typography pass** | text/design plate in [`ideogram-4`](../ideogram-4/) (bbox layout, transparency) → composite/inpaint elsewhere `[flagged — no canonical workflow]` |

The pattern behind all of them: **compose where control is deepest, render where quality is highest, finish where the finisher is best.**

**Licence travels with the chain, and it constrains the pipeline, not the picture.** A non-commercial rung usually doesn't poison the *output* — [`anima`](../anima/) puts Outputs outside its Derivative definition, so anyone may sell what they make with it. **Selling pictures asks whether you may use each model. Selling the pipeline asks whether each model may ship.** There, one non-commercial checkpoint stops the whole chain, whether it sits first or last. Swap it out early ([`flux-2`](../flux-2/)'s klein 4B, Apache-2.0). Per model: [`references/mixed-model-recipes.md`](references/mixed-model-recipes.md) §6.

---

## Workflows as code

Four routes, by intent (comparison and examples: [`references/workflows-as-code.md`](references/workflows-as-code.md)):

- **ComfyScript** — workflows *as Python* (loops, sweeps, conditionals), with a transpiler from existing workflow JSON. Alive at v0.6.x, but single-maintainer, so **pin versions** `[official — Chaoses-Ib/ComfyScript]`.
- **Export (API) + `/prompt` + WebSocket** — the most production-proven route `[community — ViewComfy production-API guide; strong]`. Build in the GUI, export API-format JSON, parametrize its inputs, then POST. **comfy-cli** wraps it for shell/CI.
- **diffusers** — no ComfyUI at all. Pipelines are testable Python, and handoffs pass pixels by construction. The trade-off: no detailer or tiled-upscale node ecosystem.
- **Hosted wrappers** (ComfyDeploy, RunComfy serverless) — productized API-format workflows. Rolling your own on rented GPUs is [`comfyui-on-runpod`](../comfyui-on-runpod/)'s job.

At scale, add **subgraphs** per stage, **rgthree** plumbing (Context pipes, Fast Muter, global Seed), **wildcards**, and a saved intermediate per stage so a bad final diagnoses to a stage.

---

## Tool status that changed recently (mid-2026)

Stale tutorials outnumber current ones. These are the load-bearing changes:

| Tool | Status |
|---|---|
| **SUPIR → SeedVR2** | SUPIR frozen (merged into core); SeedVR2 is the current default finisher ([`references/production-ladder.md`](references/production-ladder.md) §5) |
| **cubiq IPAdapter_plus** | maintenance-only since Apr 2025; Comfy-Org maintains a reference implementation |
| **xinsir ControlNet (SDXL)** | training stalled — frozen but still SOTA; ProMax union is the pick |
| **Regional prompting on DiTs** | core mask-based attention masking (PR #5942) is the *only* working approach |
| **Subgraphs** | native since Aug 2025 — replaced group-node conventions for stage packaging |

### The test is output modality, not training modality

**A checkpoint trained on video still belongs to *this* ladder whenever the stage takes pixels in and puts pixels out — one frame, one edit, no motion.** That follows from rule 1, which was always about *latent* families, not model families. The instant a stage's output is a clip, it moves to [`wan-2-2`](../wan-2-2/)'s, [`minimax-h3`](../minimax-h3/)'s, [`ltx-2-5`](../ltx-2-5/)'s or [`scail-2`](../scail-2/)'s ladder — even when the input frame was prepared here.

### A video model is now a legitimate stage in an image pipeline

**[`minimax-h3`](../minimax-h3/) generating exactly one frame is an image editor.** By multiple reports, it beats Krea 2 + Identity Edit, Qwen-Image-Edit and Flux Klein 9B for character fidelity, 3D scene understanding, mirrors and composition — around 8 s per edit on a 5090 `[community — Patient_Ratio4177]`. It wins there because **a model trained on multi-reference video conditioning has learned spatial and physical relationships an image editor has not**.

Two requirements make it work, and skipping either produces garbage instead of an error: a **dedicated image VAE** (`Mamad8/MiniMax-H3-Image-VAE`) and **exactly one frame** (5 frames through that VAE grids). Rule 1 applies unchanged: an H3 latent is not a Qwen-Image or Flux latent. Decode it to pixels, and it drops into the ladder cleanly.

### Generative upscaling versus restoration

`ReDetail` (`Bambushu/redetail`) drives the [`ltx-2-5`](../ltx-2-5/) video upscaler as a **generative re-render**, mostly on [`minimax-h3`](../minimax-h3/) output. It is the video-side analogue of this ladder's detail-preserving-versus-detail-*inventing* choice. **It invents:** it redraws jersey graphics, number plates, logos and text. That is right for AI-generated or genuinely soft footage with nothing real to recover, and wrong wherever a face, label or logo must stay exact.

Three hard constraints, and all of them fail quietly. **Both output dimensions must divide by 64** (not 32). Clip length must be **`8n + 1` frames**, or the tail is silently dropped. **A silent clip fails outright**, because LTX-2.5 encodes audio and video jointly — add a silence track first. Prefer **1.5× over 2×**: most of 2×'s extra detail is invented rather than recovered, at more than double the time and VRAM (measurements: [`references/production-ladder.md`](references/production-ladder.md) §5) `[community — DaLyon92x]`.

---

## Failure modes & QC

| Symptom | Cause (mechanism) | Fix |
|---|---|---|
| Black or deep-fried garbage after switching models mid-graph | Latent from family A fed to family B's sampler/VAE | Decode to pixels between families (rule 1) |
| Tile seams in the upscale | No overlap/seam-fix; per-tile exposure differences | USDU seam-fix (half-tile) + overlap; ColorMatch at the end |
| Objects/text duplicated across the upscale | Full scene prompt passed to the tile pass — each tile renders it locally | Generic prompt for the upscale; on DiTs, TTP per-tile captioning |
| Character's face changed in the refine pass | Refine denoise above ~0.35 | Lower denoise, or re-assert with a detailer pass (the LoRA/adapter lives there) |
| Composition destroyed by "hires fix" | Latent-upscale route run at pixel-route denoise (< 0.5) | Pixel route at 0.25–0.35, or latent route at ≥ 0.5 |
| Colors drift warmer/flatter over the pipeline | VAE round-trips and re-samples compound; two VAEs in mixed chains | One ColorMatch at the end vs the post-refine reference |
| Inpainted region is mush | Masked area sampled far below native resolution | Crop-and-stitch; `InpaintModelConditioning` + Differential Diffusion |
| Regional prompts ignored on Flux/Z-Image | SD-era regional tooling doesn't work on DiTs | Core attention masking (Flux); per-face detailer passes (Z-Image) |
| Batch results unreproducible | Per-stage random seeds | rgthree global Seed, fixed once composition is found |
| Licence blocks delivery after the pipeline is built | A rung cleared for selling the *picture*, never for shipping the *pipeline* | Settle the chain's terms first |

---

## Pre-flight checklist

Before committing to the expensive passes:

1. Base composition approved at stage 1, seed fixed, every later stage bypassable?
2. Each pass's denoise in the right band (refine 0.25–0.35; tiles 0.2–0.35; latent-hires ≥ 0.5)?
3. Cross-model handoff: decoded to pixels, resolution matched, refine denoise ≤ ~0.35?
4. Tile pass given a simplified prompt (or TTP per-tile captions on a DiT)?
5. Character work: identity re-asserted *after* the last whole-image pass?
6. ColorMatch at the end against the post-refine reference?
7. Finisher current (SeedVR2-class), not a frozen tool from an old tutorial?
8. Video stage in the chain? Restored *before* interpolating, never after.
9. Every model licensed for the deliverable — selling the picture, or shipping the pipeline?
10. If batching: API-format JSON or ComfyScript, global seed, intermediates saved per stage?

---

## The suite map

Per-model facts live in the model skills. This skill owns what spans them.

| Skill | Its specialty | Its mixed-pipeline role |
|---|---|---|
| [`sdxl`](../sdxl/) | deepest control/LoRA/adapter ecosystem | control front-end; texture back-end |
| [`z-image`](../z-image/) | realism stacking, layered ZIB/ZIT pipeline | fast realism refiner (ZIT) |
| [`flux-2`](../flux-2/) | prompt comprehension, multi-reference identity; klein 4B Apache-2.0 | quality refiner (klein); composition front-end |
| [`ideogram-4`](../ideogram-4/) | typography, layout, design | the typography pass |
| [`krea-2`](../krea-2/) | widest aesthetic range; tuned against the AI look | aesthetics/composition front-end |
| [`anima`](../anima/) | anime and illustration; 2B, ~6 GB VRAM, booru-tag dialect — **non-commercial weights** | the anime front-end: cheap enough to be a default composing rung, never a realism refiner; blocks any pipeline sold as a service |
| [`wan-2-2`](../wan-2-2/) | **video** — image-to-video, motion and camera control | downstream: a still finished by this ladder is what drives I2V |
| [`ltx-2-5`](../ltx-2-5/) | **video + joint audio**; the suite's generative video upscaler | downstream, and the engine behind ReDetail |
| [`scail-2`](../scail-2/) | **video** — character replacement tracking a driving clip frame-for-frame | downstream, and the strictest consumer: its reference must be the driving clip's own first frame, edited |
| [`minimax-h3`](../minimax-h3/) | **video + native audio** — omni-modal, reference conditioning | downstream, and the one output this ladder can silently break: most video post nodes are picture-only and drop the audio. **Also upstream now**, at one frame |
| [`generative-media-atlas`](../generative-media-atlas/) | choosing between everything above — rankings by job, the elimination ladder, install routes | upstream of this ladder: it decides *which* models the chain hires before this skill decides how they hand off |

**Where the ladder feeds backwards — and where it doesn't.** The table reads left-to-right: image skills feed video skills. Exactly one path runs the other way — [`minimax-h3`](../minimax-h3/) at one frame, by the output-modality test above. The [`krea-2`](../krea-2/) → [`scail-2`](../scail-2/) case looks identical, but is not: Identity Edit prepares the driving clip's first frame, which is ordinary forward flow, and marks where this skill's job *ends*.

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** Node and repo names, the latent-incompatibility mechanism, tool maintenance statuses, ReDetail's dimension and frame-lattice constraints, and the licence terms a chain's shipping rights depend on. **Source of truth is official** — the repos, the model cards, ComfyUI core. These are the volatile ones: a tool marked "current" can freeze in a month. **Re-verify statuses, versions and licence text before building production pipelines on them.**

**Craft — what actually makes a good image.** The denoise bands, per-stage settings, the handoff rules, the named recipes, the QC habits. **The authoritative source here is the community** — named workflow authors (Cordina, Enzino, nsfwVariant, TTPlanet, ltdrdata, MyAIForce, myByways, sandner.art, u/Alekite, DaLyon92x) whose graphs have run at scale. It is stated with confidence: ranges mean "your checkpoint and resolution differ," not "unverified." One limit worth naming: **batch QC is tooled for comparison but not for judgement**, so the cull stays human, and stays biased.

**Contested / unresolved points:**

- The Ideogram typography-pass pattern is practiced, but the composite step is reconstructed craft rather than a graph someone published `[flagged — no canonical workflow]`.
- Per-region *LoRA* application on DiT regional-attention setups is unsettled. It works on SDXL and does not transfer `[contested]`.

**Facts dated 2026-06-12**; community craft refreshed 2026-08-22. Fastest-moving: finishers (SeedVR2's successors and the generative video upscalers), DiT regional and per-region-LoRA tooling, the video-model-as-image-editor path, new weights' licence terms, and ComfyScript/frontend compatibility.

---

## Reference files

| File | When to read it |
|---|---|
| [`references/production-ladder.md`](references/production-ladder.md) | You have picked a rung and need its settings: the two hires routes' denoise asymmetry, detailer `guide_size`/`crop_factor` and `[SEP]` routing, USDU seam-fix and TTP captioning, finishers, inpainting, color management, Detail Daemon and PAG |
| [`references/mixed-model-recipes.md`](references/mixed-model-recipes.md) | You are chaining two models and need a recipe someone has run, the per-family ControlNet/IP-Adapter status, regional-prompting support, identity sequencing, or the chain's licences |
| [`references/workflows-as-code.md`](references/workflows-as-code.md) | You are done clicking Queue: picking an automation route, and the subgraph/rgthree/wildcard/batch-QC conventions |
