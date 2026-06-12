# FLUX.2 Characters — creating a consistent character

How to invent an original character and keep them consistent across poses, outfits, scenes, and multi-character images. FLUX.2's distinctive position: it's the open model where the **no-training path is strongest** — native multi-reference conditioning (`ReferenceLatent`, up to ~8–10 images) plus a working PuLID — so the first question is whether you need to train at all.

Tool wiring lives in `controlnet-and-identity.md`; LoRA training mechanics in `lora-training.md`; loading/stacking in `setup-and-workflows.md §7`.

---

## 1. Choose the path

| Path | Tool | When it wins |
|---|---|---|
| **Multi-reference editing** (no training) | `ReferenceLatent` chains — feed 1–10 images of the character; FLUX.2 [dev] re-renders them into new scenes | One-to-few images of the character exist; scene/outfit changes; fastest iteration. Community tip: prefer [dev] over Flux.1 Kontext for character consistency; lock seeds; drop conflicting references *(official template + community)* |
| **PuLID** (no training) | iFayens `ComfyUI-PuLID-Flux2`, strength 1.0–1.4 | Face identity from a single portrait, especially one you can't train on. Supports [dev] and both [klein] sizes — the natively-trained weights are **klein-first** (`pulid_flux2_klein_v1/v2`), and calibration differs between base and distilled variants *(official repo; t2i only as of v0.6.x)* |
| **Character LoRA** (training) | AI-Toolkit on a **base** (non-distilled) variant | A recurring character who must survive angle extremes, carry a body/outfit/mannerisms, and stack with style LoRAs |
| **Combinations** | multi-ref or LoRA for the character + PuLID or a detailer pass to lock the face; ControlNet (Fun Union pose) + PuLID for posed identity shots | Production work — the paths compose because they all output standard conditioning |

**The cross-model decision rule** *(community consensus — MyAIForce's head-to-heads are the citable comparisons)*: adapters and reference conditioning excel at one-shot likeness with zero setup, but drift at extreme angles and under heavy restyling; a trained LoRA is what carries the *whole* character robustly. FLUX.2 softens this rule — multi-reference covers many cases that needed a LoRA on other models — but doesn't repeal it.

---

## 2. Multi-reference as the character engine

The native workflow (ComfyUI [dev] image-edit template, `setup-and-workflows.md §2`):

1. **Build a small reference set** — 2–6 images: a clean front portrait, a three-quarter, a full-body, and optionally the signature outfit flat or worn. A character sheet generated once (front/side/angled on one canvas, or as separate frames) doubles as this bundle — the Mickmumpitz-class "consistent character creator" workflows are the established pattern *(community, strong)*.
2. **Chain one `ReferenceLatent` per image**, then prompt the new scene. Label the references semantically in the prompt ("the woman from the reference images sits at…"). BFL's marketing says 10 references, the prompting guide says 8 — treat ~8 as the safe number (the unresolved discrepancy is flagged in SKILL.md).
3. **Iterate with fixed seeds**; if a reference fights the prompt (e.g. its background keeps leaking), bypass it. `ReferenceLatentPlus` (shootthesound) adds per-image strength and timestep gating when you need one reference dominant.
4. **[klein] 9B KV** is the batch variant — it caches reference K/V states so a fixed character bundle re-renders against many prompts at ~1.5–3× speed (`setup-and-workflows.md §4`).

Multi-reference is also the **dataset factory** for the LoRA path: one anchor image → many consistent variants (angles, outfits, expressions, lighting) → curate into a training set. Generate ~60, keep the best ~30, cutting every frame where the face drifted. (Qwen-Image-Edit 2509/2511 is the other widely-used factory tool — a different model used purely for data manufacturing.) *(Community, strong — WeirdWonderfulAI's Qwen-Edit dataset writeup is the canonical version of this pipeline.)*

---

## 3. The character LoRA pipeline

1. **Anchor image** in FLUX.2 itself: front three-quarter, neutral light, plain background, specific nameable features ("silver-grey cropped hair, a freckle above the left brow") — these are what the LoRA will absorb.
2. **Dataset:** 20–50 images via the factory above. Coverage: the **8-point rotation** (front, both three-quarters, both profiles, both back three-quarters, back — identical descriptions, only the angle clause varying), one high- and one low-elevation close-up, 3+ expressions, 2–3 outfits, shot-size mix (close-up ~30%, full-body ~20%). Vary exactly one thing per image. Back views need explicit back-of-hair/outfit description and retries. (The full clause-by-clause protocol is in the z-image skill's prompting guide §3.3–3.5 — it's written as natural-language sentences, which is exactly FLUX.2's dialect; reuse it directly.)
3. **Caption in prose, caption the residual:** describe pose, clothing, scene, lighting, angle in natural sentences; leave the identity undescribed so it binds to the concept. No bare trigger token — if you want one, fold it into the sentence ("a photo of TRIGGER, a woman with…"); FLUX.2's LLM encoders read description better than made-up tokens (`setup-and-workflows.md §7`).
4. **Train on a base variant** — [klein] 4B Base for commercially-deployable LoRAs (Apache 2.0), [dev] for max quality. Never the 4-step distilled variants. Character rank ~16, LR 1e-4 starting low: `lora-training.md`.
5. **Evaluate:** XY grid (checkpoint × strength) on out-of-set prompts — new outfit, new setting, a profile view. Pass = the face holds while everything else obeys.
6. **Deploy with the detailer swap** *(community, strong — established cross-model technique)*: generate the base image *without* the character LoRA (at full strength in the base pass it drags composition toward its training data), then apply the LoRA inside a FaceDetailer pass (Impact Pack detailers are model-agnostic and run FLUX.2 fine) at denoise ~0.4, with the detailer prompt matched to the image.

---

## 4. Beyond the face

- **Signature outfit:** leave it uncaptioned where the character wears it → it binds to the identity; caption it where it should stay swappable. For one-off wardrobe changes, multi-reference (image 1 = character, image 2 = garment) replaces wardrobe training entirely.
- **Multi-outfit LoRAs:** unique trigger-phrase per outfit, visually distinct outfits, balanced image counts; practical ceiling **~6 outfits** *(community — Khanykov01's guide, written for SDXL but the capacity logic is architecture-general)*.
- **Multi-character scenes:** FLUX-class models have one real regional tool — **mask-based attention masking**, merged into ComfyUI core (PR #5942); the SD-era Regional Prompter approach does *not* work on the DiT. The layered defense: (1) regional attention masks per character, (2) per-face detailer passes each loading its own character LoRA, (3) one distinguishing feature per character in the scene prompt. How well per-region *LoRA* application works on DiT attention masking is still contested — expect retries. *(Core PR is official; the craft layer is community and still forming.)*

---

## 5. Failure modes & fixes

| Symptom | Cause (mechanism) | Fix |
|---|---|---|
| Identity collapses at profiles/back views | Front-heavy dataset, or an adapter at its angle limit | Add targeted angle images via the factory; for adapters, switch to the LoRA path — angle robustness is its core advantage |
| Multi-ref output blends the references into a stranger | Conflicting references (different haircuts/ages) average out | Curate the bundle — consistent era/haircut; drop the weakest reference; raise the cleanest portrait's strength (ReferenceLatentPlus) |
| PuLID face looks pasted / ignores scene lighting | Identity embedding overrides local context at high strength | Drop strength toward 1.0; finish with a low-denoise detailer pass to re-blend |
| Same-face rigidity, dataset poses reproduced | Near-duplicate shots; overtraining | Earlier checkpoint; more variety; re-read the XY grid |
| Character LoRA restyles every image | Style entangled with identity in a one-look dataset | Vary dataset lighting/medium. The SDXL block-weight fix has **no established FLUX.2 equivalent** — prevention at dataset time is the lever *(flagged — no DiT block map yet)* |
| Two characters swap attributes | Single conditioning stream without isolation | Regional attention masks + per-face detailer LoRAs (§4) |
| LoRA won't load at all | Variant mismatch — [dev] vs [klein] 4B vs 9B LoRAs are not interchangeable | Match the LoRA to its exact training variant (`setup-and-workflows.md §7`) |

---

## Sources & confidence

Hard facts (ReferenceLatent/KV templates, PuLID files and limits, attention-masking core PR, variant incompatibility) are **[official]** from ComfyUI templates and the respective repos — PuLID-Flux2 is a fast-moving single-maintainer project, re-verify its current weights/limits before install. The craft (reference-bundle curation, dataset factory, detailer swap, multi-character layering) is **named-community** (Mickmumpitz, WeirdWonderfulAI, MyAIForce, Civitai authors), convergent across models and stated with confidence; FLUX.2-specific numbers are early and flagged where contested.
