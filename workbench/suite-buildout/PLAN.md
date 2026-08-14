# Suite alignment & build-out plan — image-model skills

> **STATUS (2026-06-10): EXECUTED.** Phases 1, 2a, 2b, 2c and the meta-skill update are done — all four skills rebuilt (new `characters.md` everywhere applicable, `lora-training.md` split + style expansion, production-pipeline sections, suite positioning tables, refreshed descriptions), the fifth skill `image-production-workflows` created and registered in marketplace.json + README. Remaining from Phase 3: the skill-creator eval loop on pillar prompts, the description-trigger optimization run, and committing/publishing the `generated-skills` sub-repo (working tree left uncommitted deliberately).

**Date:** 2026-06-10
**Scope:** the four published skills (`generated-skills/skills/{z-image, sdxl, flux-2, ideogram-4}`), the `image-model-skill` meta-skill, and one proposed new skill.
**Goal:** keep the suite aligned on one house structure, and build each skill out into a working guide for the three jobs users actually hire these models for:

- **Pillar A — AI characters:** create an original character and keep it consistent across poses, outfits, scenes, and multi-character images.
- **Pillar B — Style LoRAs:** train, evaluate, and stack LoRAs that carry an artistic style.
- **Pillar C — Professional images via complex mixed workflows:** multi-stage pipelines, cross-model handoffs, and workflows-as-code.

**Audience:** people running the models directly — diffusers, ComfyUI, or ComfyScript/workflows-as-code. Hosted APIs stay a side path (as ideogram-4 already frames it).

Supporting research (all claims sourced, confidence-tagged) lives next to this file:
`research/alignment-audit.md` · `research/characters.md` · `research/style-loras.md` · `research/mixed-workflows.md`

---

## Where the suite stands (audit summary)

The four skills already share the house spine (pushy description → intro → selector → one-rule → setup → per-variant settings → realism → failure modes → checklist → licence → two-bars → reference table). The gaps are concentrated, not diffuse:

| | Characters | Style LoRAs | Multi-stage workflows | Mixed-model | Workflows-as-code |
|---|---|---|---|---|---|
| **z-image** | strong (best-in-class) | strong | strong (best-in-class) | none | none |
| **sdxl** | partial (IP-Adapter only; no InstantID/HyperLoRA/rotation protocol) | strong (best-in-class) | shallow (components, no orchestration) | none | none |
| **flux-2** | partial (PuLID + multi-ref; no dataset/sheet protocol) | strong | none | none | none |
| **ideogram-4** | none (correct — but not stated as routing) | none (correct — no ecosystem yet) | none | none (its typography role unstated) | none |

Plus alignment drift: LoRA-section placement, confidence-tag style, trigger-word wording, myth-debunk propagation, incomplete cross-link mesh. Details in `research/alignment-audit.md`.

**ComfyScript, regional prompting, cross-model handoffs, and the 2026 upscaler stack (SeedVR2 over SUPIR) appear in none of the four skills.**

---

## Phase 1 — Alignment (small diffs, all four skills, do first)

1. **Canonical reference slots.** Every skill's `references/` maps to the same concern slots, with these filenames for new content:
   - `prompting-guide.md` (ideogram's `json-caption-guide.md` keeps its name — it *is* the prompting guide; note the role in the reference table)
   - `setup-and-workflows.md` / `workflows.md` — setup, graphs, multi-stage pipeline, using LoRAs, upscaling
   - `lora-training.md` — *training* only (z-image's split is the standard). Extract flux-2 `setup-and-workflows.md §8` and the training half of sdxl `checkpoints-and-loras.md §6` into new `lora-training.md` files, leaving pointers. Usage/stacking stays in the workflows/checkpoints files.
   - `characters.md` — new slot, Phase 2a.
   - Model-specific extras keep their names (`api-and-bfl.md`, `controlnet-and-identity.md`, `checkpoints-and-loras.md`, `self-hosting.md`, `api-and-webapp.md`).
2. **Encoder-class doctrine, stated once per skill.** Prompt dialect, trigger-word rule, captioning doctrine, and negative-prompt behaviour all follow the *encoder class*, not the model brand. Add one consistent sentence to each skill's one-rule section ("SDXL's CLIP wants a verbatim rare-token trigger; LLM-encoder models want it folded into a sentence or omitted — this is the encoder, not folklore") so readers transfer the rule correctly between models. The full doctrine table goes in the meta-skill.
3. **Confidence-tag house style.** Adopt flux-2/ideogram-4's inline tags everywhere: `[official]`, `[community — named author]`, `[flagged — re-verify]`. Keep each skill's closing "two bars" section but converge the wording on the z-image phrasing (it's the fullest).
4. **Propagate the myth-debunks** wherever applicable: sub-1.0 LoRA strength is normal (all), alpha=2×rank is legitimate (add to z-image), speed-LoRA has no hard cap (z-image-specific, leave).
5. **Complete the cross-link mesh + suite positioning row.** Each SKILL.md gets a compact "where this model sits in the suite" table — characters / style LoRAs / typography / control ecosystem / refiner role — with back-links to the competing skill. (E.g. characters: flux-2 or z-image; typography: ideogram-4; control stack + texture refine: sdxl.)
6. **Description frontmatter refresh** so triggering covers the new pillar phrases: "consistent character", "character LoRA", "train a style LoRA", "upscale pipeline", "refine with another model", "ComfyScript", "batch generation".
7. Keep every SKILL.md under ~500 lines — pillar depth goes to references; SKILL.md gets a section-sized summary + pointer.

## Phase 2a — Pillar A: characters (`references/characters.md` per skill + a SKILL.md section)

Shared shape (adapted per model — research in `research/characters.md`):

- **The two paths, then the chain.** (1) *Edit-model character engine* — no training: character sheet from one image (Mickmumpitz-class workflows), multi-reference editing; (2) *Character LoRA pipeline* — edit-model-generated dataset (generate ~60, curate ~30; 20–50 varied images), caption-the-variables (encoder-class-dependent), train, evaluate. The 2026 consensus chains them: the edit model builds the LoRA dataset.
- **Dataset protocol:** port z-image's 8-point rotation + elevation sheet protocol to every trainable model (it's model-agnostic craft, currently buried in one skill).
- **Identity-tool status table** per model (which adapters exist, when LoRA beats adapter).
- **Detailer-stage LoRA swap** as the standard high-likeness technique (already in z-image; generalize).
- **Beyond the face:** multi-outfit LoRAs (~6-outfit ceiling), edit-model wardrobe transfer, multi-character bleed and the layered defense (regional masks → `[SEP]` per-face detailer routing → multi-ID models).
- **Failure modes:** angle collapse, same-face overfit, expression lock-in, style bleed (SDXL block-weight fix; no DiT block map yet — flag), multi-character bleed.

Per skill:
- **z-image** — consolidate existing material into `characters.md`; add the Qwen-Image-Edit dataset-factory pipeline and multi-character status. Smallest job.
- **sdxl** — biggest gap vs ecosystem: add **InstantID** (consensus better than IP-Adapter FaceID, currently absent), **HyperLoRA**, ReActor's 2025 InsightFace-free rewrite (licence implications!), ADetailer `[SEP]` routing, block-weighted LoRA anti-style-bleed, the rotation protocol.
- **flux-2** — frame **ReferenceLatent multi-ref as the character engine** (up to ~8–10 refs), PuLID current status (v0.6.2, klein-v2 weights, Base-vs-distilled calibration), character LoRA dataset protocol.
- **ideogram-4** — honest routing section: no character tooling on open weights (structurally incompatible architecture); route to web-app Character Reference for hosted work, or build the character in flux-2/z-image and reserve Ideogram for typography passes. Cross-link.

## Phase 2b — Pillar B: style LoRAs (extend each `lora-training.md`)

Research in `research/style-loras.md`. Additions per skill (z-image, sdxl, flux-2; ideogram-4 keeps its honest stub):

- **Style inverts the residual** — sharpen the existing treatment with: "consistency in the thing trained, diversity in everything else"; color-cast lock-in as a named overfit signal; the acceptance test (style recognizable on out-of-set subjects).
- **The captioning fork, stated honestly:** tags-without-style for CLIP (SDXL); prose-residual vs captionless contested for DiTs (recris's clown test vs Civitai 7203); trigger embedded naturally or omitted on LLM encoders.
- **Per-family numbers with contested flags:** SDXL/Illustrious dim 32/α32, Prodigy, ~3000 steps; Flux.2 Herbst ablation (128/64/64/32) vs tool defaults — and the Civitai klein recipe's dim-2 floor warning; Z-Image rank 16–64, shift 3, de-distillation adapter vs "de-turbo" route; weight decay as a color/tonality knob.
- **Evaluation:** XY grid epoch×strength; checkpoint-every-200–500; sample prompts on out-of-set subjects including one *without* the trigger.
- **Stacking & block control:** one style + one character (style 0.6 / char 0.9; drop style first when identity collapses); SDXL Inspire-Pack `LoraLoaderBlockWeight`; DiT training-time layer targeting; LoKr as the style-specialist LyCORIS.
- **Ethics flag** on single-artist style datasets.

## Phase 2c — Pillar C: a new fifth skill + per-skill workflow sections

**Recommendation: create `generated-skills/skills/image-production-workflows/`** — a model-agnostic skill for the cross-cutting craft, so four skills don't each duplicate 200 lines. Research in `research/mixed-workflows.md`. Contents:

1. **The production ladder** — base → second pass → detailers → tiled upscale → finisher; per-family rung choices; per-stage denoise bands.
2. **Mixed-model handoffs** (the genuinely new material): the decode-to-pixels rule between VAE families; identity-preserving denoise band 0.2–0.5; resolution matching; named workflows (SDXL→Z-Image-Turbo "ZIT Refiner", SDXL/Pony→Flux Klein img2img, Flux→SDXL texture refine); SDXL as controllable front-end / DiTs as quality back-end; Ideogram typography plates (flagged inferred-craft).
3. **2026 tool-status table:** SeedVR2 over frozen SUPIR; TTP per-tile captioning for DiT tiled upscales; USDU seam-fix modes; ColorMatch + color-drift management; Detail-Daemon/PAG; crop-and-stitch + Differential Diffusion inpainting; regional prompting status per family (core Flux attention masking; Regional Prompter is SD1.5/SDXL-only); IPAdapter-plus maintenance-only.
4. **Workflows-as-code:** ComfyScript (v0.6.x, virtual/real/transpiler modes, single-maintainer pin-versions caveat), Export (API) + `/prompt` + comfy-cli as the production-proven route, diffusers as the code-first alternative (cross-model handoff is pixels by construction).
5. **Pro conventions:** native Subgraphs, rgthree plumbing, wildcard/dynamic-prompt batching, seed discipline, batch QC.

Then in each model skill: a short **"Production pipelines & mixing models"** section (z-image: extend the existing one; sdxl/flux-2: new, modeled on z-image's) covering the model-specific ladder + its *role* in mixed pipelines, with a back-link to the new skill. Register the new skill in `generated-skills/.claude-plugin/marketplace.json` and `README.md`.

Alternative considered: folding all of this into the four skills. Rejected — duplication, drift risk, and the material is genuinely model-agnostic; the suite already cross-links skills by name.

## Phase 3 — Meta-skill, validation, publishing

1. **Update `image-model-skill`** (done in this session, see below): four exemplars, two-bar confidence framing, encoder-class doctrine, pillar anatomy slots, canonical reference slots, research-source canon incl. SEO-farm and login-walled-Civitai warnings, corrected paths (`generated-skills/skills/<name>/` + marketplace/README registration).
2. **Validate the skill-creator way:** for each rebuilt skill, run 2–3 realistic pillar prompts ("build me a consistent character pipeline for Flux.2 klein on a 16 GB card", "train a watercolor style LoRA for SDXL and tell me how to evaluate it", "take this SDXL render and refine it with Z-Image then upscale to 4K") with-skill vs without, eyeball via the eval viewer; then run the description-optimization loop on the refreshed frontmatter descriptions.
3. **Re-verification cadence:** ideogram-4 (days old) and flux-2 klein (months old) carry volatile facts — re-verify quant filenames, LoRA tooling, and template details at build-out time, not from these notes.

## Sequencing & effort

| Phase | Touches | Effort | Depends on |
|---|---|---|---|
| 1 Alignment | 4 skills, small diffs | ~1 session | — |
| 2a Characters | 4 × `characters.md` + SKILL.md sections | 1–2 sessions | 1 |
| 2b Style LoRAs | 3 × `lora-training.md` | ~1 session | 1 |
| 2c Pipelines skill | new skill + 3 SKILL.md sections + registration | 1–2 sessions | 1 |
| 3 Validation & publish | eval runs, description optimization, marketplace | ~1 session | 2a–2c |

Phases 2a/2b/2c are independent of each other and can run in any order or in parallel sessions. Each phase should spot-re-verify its volatile facts (the research files tag what's `[flagged]`).

## Open decisions

1. **Name of the fifth skill** — proposal: `image-production-workflows`. Alternatives: `comfyui-pro-pipelines` (too ComfyUI-narrow given the diffusers/ComfyScript audience), `mixed-model-pipelines` (too narrow given the ladder content).
2. **How hard to commit on contested craft** (Flux captionless training, style rank 32-vs-128, Flux.2 step counts) — plan default: present both positions with the named evidence, per the two-bar discipline.
3. **Whether sdxl's `checkpoints-and-loras.md` split** (training → `lora-training.md`) is worth the churn on a published sub-repo — plan default: yes, with a pointer left behind.
