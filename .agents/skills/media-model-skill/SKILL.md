---
name: media-model-skill
description: >
  Repo-internal authoring machinery for github.com/ryannel/skills; it depends on that repo's layout and will not work elsewhere. Author a complete, publishable skill for a generative-media model — image (Flux.2, SDXL, Qwen-Image, HiDream, Chroma, any text-to-image / image-edit DiT or UNet) or video (Wan 2.2, HunyuanVideo, LTX-2, any T2V / I2V / video-edit model) — following the house style proven by the z-image, ideogram-4, sdxl, flux-2 and krea-2 skills in this repo. Use this whenever the user wants to create, draft, roll out, or improve a skill for an image or video model — "make a skill for flux2", "write an SDXL skill", "do for X what we did for z-image", "add another model skill", "build a prompting guide skill for <model>", "write a Wan 2.2 skill", "add a video model", "make a skill for HunyuanVideo/LTX", "cover image-to-video" — even if they don't say the word "skill". It covers the whole job: which primary sources to read and in what order, the section-by-section anatomy (and which sections are fixed scaffolding vs discovered-per-model), the three deep-coverage pillars (characters, LoRA training, production/mixed-model pipelines), the conditioning-class doctrine, the explain-the-why prose style, the two-bar confidence/provenance discipline, and where the finished skill goes (including marketplace registration). This is a meta-skill for authoring; it does not generate images or video itself.
metadata:
  internal: true
---

# Authoring a generative-media model skill

Your job with this skill is to turn a single generative-media model into a **self-contained, trustworthy, publishable skill** — a `SKILL.md` plus `references/` that another agent can lean on to set the model up, prompt it well, and debug it, without already knowing the model.

The single failure mode to avoid: treating this as a template to fill in from memory. **The sections are scaffolding; the content is research.** A skill written from your priors will get the loader node names, the file list, and the recommended CFG wrong. Almost everything load-bearing comes from primary sources read close to verbatim.

Two illustrations of why, both real and both recent: Wan 2.2's 14B variants ship with `wan_2.1_vae.safetensors` while its own 5B variant uses `wan2.2_vae.safetensors` — a VAE-family split *inside one release*. And the 14B latent node in the official template is `EmptyHunyuanLatentVideo`, borrowed from an entirely different model family. Neither is guessable from the model's name. Both would 404 or silently misbehave if written from priors.

---

## Step 0 — Route by modality

The research protocol, prose style, provenance discipline and placement rules below are shared. The **spine** of the skill — the selector table, the one-rule, the doctrine, the pillars' mechanics — differs by modality. Read the matching reference in full before drafting:

| The model is… | Read | Spine it usually takes |
|---|---|---|
| A **still-image** model (T2I, image-edit) | [`references/image-models.md`](references/image-models.md) | Variant selector *or* surface selector |
| A **temporal** model (T2V, I2V, V2V, video-edit) | [`references/video-models.md`](references/video-models.md) | Task-mode selector (T2V / I2V / V2V / first-last-frame / extend) |

A model can span both — Wan generates stills as well as clips, and several image models now have a video sibling. Lead with the modality the user will actually reach for it for, and cross-link the other rather than splitting the skill.

The modality references also carry the ground-truth examples to pattern-match against. **Pattern-matching against a finished skill beats any description here** — the published skills *are* the spec. Read the ones your reference file names, in full.

One cross-read regardless of modality: the **conditioning-class doctrine** is numbered continuously across the two references. Axes 1–2 (text-encoder class, and guidance state — which is what actually determines negative-prompt behaviour) are defined in `references/image-models.md` and apply to **both** modalities. Video adds axes 3–4 (image-conditioning path, temporal architecture) in its own file. So video authors read that one section of the image reference; image authors need only their own.

### Is this a new skill or an existing one?

The steps below are written for a new model. **If the skill already exists** in `skills/generative-media/`, the job is different and most of Step 5 is already done:

1. **Read the existing skill in full first** — SKILL.md and every reference. You are editing a document with load-bearing internal cross-links and a stated provenance position, not drafting over it.
2. **Check `freshness.json` before researching.** The skill's `watchlist` already names its volatile claims and its `open_findings` may already record what drifted — that is the repair queue, and re-researching from scratch wastes it. `/skill-freshness` is the tool that maintains it, and it deliberately separates detection from repair.
3. **Diff, don't rewrite.** Establish what actually changed in the world since the skill's date stamp, and change those claims. Preserve the parts that still hold — especially craft, which ages more slowly than filenames and pricing.
4. **Skip Step 5's registration items** — marketplace.json, the README row and the freshness entry already exist. Re-adding them creates duplicates. Do update the skill's own date stamp, and add any newly volatile claims to its watchlist. **Do not hand-edit `last_checked`** — that field records that a *freshness check* ran, and stamping it from an authoring pass claims a check that didn't happen and silently resets the cadence clock. Let `/skill-freshness` own it.
5. The pre-flight checklist still applies to whatever you touched.

---

## Step 1 — Research the model (this is the real work)

Before drafting, gather facts from primary sources in roughly this priority. Each source fills specific sections; note which facts came from where, because the confidence tiering at the end of the skill depends on it. Fan this out with subagents (e.g. the `Explore` agent or parallel web research) when you can — it's a lot of independent lookups.

| Source | Where | What it gives you (verbatim where possible) |
|---|---|---|
| **Official ComfyUI template JSON** | `Comfy-Org/workflow_templates` on HF/GitHub; `docs.comfy.org/tutorials/{image,video}/…`; comfyanonymous `ComfyUI_examples/` | The **file layout** (which file → which `models/` folder → which loader node), the **stock node settings** (sampler, scheduler, steps, CFG/guidance, shift, latent node type, CLIPLoader `type`, and for video the frame count and fps), and any unusual graph topology. Read the JSON itself — node defaults are authoritative; blog prose drifts, and docs pages often omit the numbers entirely. |
| **`Comfy-Org/*` HF repos** | e.g. `Comfy-Org/<model>`, `Comfy-Org/<model>_turbo` | Exact **repackaged filenames** and the **official quant variants** (fp8, nvfp4, etc.) with their sizes and folder placement. |
| **Model card** (HF / official site) | the model's HF page; the lab's release post | **Architecture** (params, DiT/UNet, single- vs dual-stream, MoE expert split), **text encoder**, **recommended steps / CFG / guidance / resolution range** (and for video: native fps, frame count, clip length), the **diffusers pipeline class name**, and the install line (check whether it's still `git+…` legacy or now in a stable diffusers release). |
| **GitHub repo** | the lab's inference repo | **License** (code vs weights often differ — this is critical), architecture details, the **inference CLI**, and any **prompt/caption rules baked into code** (e.g. a caption verifier, a `prompting.md`, a system prompt for a prompt-expander). Code is the highest-confidence source for behavior. |
| **diffusers source / docs** | huggingface.co/docs/diffusers | The exact **pipeline class**, the **img2img / inpaint / edit / i2v** variants, and the **minimum diffusers version**. |
| **Official API / docs** (only if the model has a hosted surface) | the vendor's developer docs | Hosted **endpoints, params, rendering-speed tiers, pricing, resolution strings**, commercial-use terms. |
| **Trainer repos/docs** | `ostris/ai-toolkit` (default for image DiTs), `kohya-ss/musubi-tuner` (the video default — same author as sd-scripts), kohya sd-scripts + its GitHub *discussions* (named-author craft evidence lives there), OneTrainer, `tdrussell/diffusion-pipe` (per-model timestep/shift facts) | **LoRA training support and hyperparameter defaults** per model; training-adapter requirements for distilled variants; which format the output LoRA ships in; and whether the architecture forces **more than one LoRA per concept** (see the video reference on MoE expert splits). |
| **Community** (Civitai articles & named workflow authors, Reddit, ComfyUI forums, HN, creator blogs, Banodoco) | search broadly; weight **named, reproducible authors** | **VRAM thresholds**, **GGUF / community fp8 requants**, multi-stage **workflow numbers**, **LoRA tooling** maturity, character/style craft. For *craft*, this tier is the **authoritative** source, not a lesser one (see Step 4) — but attribute it (`[community — named author]`). |

Three research traps to dodge:
- **SEO content farms** rank highly for "<model> LoRA settings" queries and read plausibly (their numbers are usually laundered from the real guides). Cite the named source they copied, not the farm.
- **Login-walled Civitai articles** can often only be read via secondary summaries — downgrade their specifics to `[weak]` until read directly.
- **Discord-only knowledge** (Banodoco and similar) won't surface in web search; treat it as an unverified channel rather than absent, and say so.

Stage what you gather in `workbench/<model-name>/` (reference dumps, screenshots of the template graph, a `prompt.md` capturing intent) — that's what the workbench is for. Nothing there is published.

**Decide the model's shape early**, because it drives the skill's spine. The candidate spines are modality-specific — see your reference file. Whichever axis you pick, the test is the same: *which choice most changes what the reader does next?* Lead with that one and fold the others in.

---

## Step 2 — The anatomy

Every finished skill shares this skeleton. Mark in your head which parts are **fixed scaffolding** (always present, same job) and which are **shape-dependent** (content discovered per model). Don't copy another skill's answers — copy its *questions*.

**Scaffolding — always present, same job every time:**

1. **Frontmatter** — `name` (kebab-case, matches the folder) and a deliberately **pushy `description`**. See the writing-style section below; this field is the single most important line in the skill.

2. **Intro paragraph** — one dense paragraph: params, architecture, text encoder, languages, license, release date. Then a one- or two-sentence statement of the model's **defining trait** — the thing that makes it different.

3. **Setup & ecosystem** — the **file-layout table** (`file → models/ folder → loader node`), the **stock node settings** from the official template, **quantisation** (official vs community, with sizes and VRAM), and the **diffusers** entry point with its version requirement. This section is where verbatim-from-primary-source matters most.

4. **Failure modes & QC table** — a `symptom → cause → fix` table of the model's characteristic artefacts. One of the most-used sections; populate it from community reports plus your own reasoning, and **explain the mechanism in the cause column**.

5. **Pre-flight checklist** — a numbered, skimmable list the reader runs before generating. Derive it from the rest of the skill; it should feel like a distilled summary.

6. **License & limitations** — especially when code-license ≠ weights-license ≠ output-rights. State it plainly and, if commercial use is in play, tell the reader which path is safe.

7. **Confidence / provenance tier** — see Step 4. Non-negotiable for new models.

8. **Reference files table** — `file → when to read it`. Pointers into `references/`.

9. **Comparative "choose the model for the job" note** — easy to forget, and a value multiplier as the suite grows. State plainly where this model is strong and weak relative to the field, and what to reach for instead, with **bidirectional back-links** to the competing skills in `skills/generative-media/`. When you add a model, update *their* notes to point back at the new one. This now crosses modalities too: an image skill should point at the video skill that consumes its stills, and vice versa.

**Shape-dependent — discovered per model, and per modality:**

10. **Selector table** — variant / surface / task-mode, with a "Use when…" column so the reader picks fast. If there are unreleased-but-announced variants, list them marked as such.
11. **"The one rule that changes everything"** — the highest-leverage section. Every good media-model skill has one insight that dominates all others, and it is *discovered* from the model's conditioning path, never assumed.
12. **Per-variant / per-mode settings** — steps, CFG/guidance, sampler, scheduler, resolution, negatives, seed behavior, LoRA weight (plus length and fps for video). Cite where each number comes from.
13. **Signature-quality technique** — the model's default look and the lever that overrides it. Models genuinely disagree here; discover this one's.

Your modality reference covers all four. Both treat the one-rule as something to *discover and falsify* rather than copy — the image reference by showing how much its five exemplars' rules differ, the video reference by naming candidate shapes to test.

### The three deep-coverage pillars

Beyond setup-and-prompting, users hire these skills for three bigger jobs. Every model skill must either cover each pillar or **state honestly that the model can't do it and route to a sibling skill** (`ideogram-4` does this for characters — that's correct coverage, not a gap):

- **Characters** (`references/characters.md`) — holding an identity steady across generations.
- **LoRA training** (`references/lora-training.md`) — *training* lives here; *using and stacking* lives in the workflows file.
- **Production pipelines** (a SKILL.md section + a workflows reference) — the model's multi-stage ladder, and its role in **mixed-model** pipelines. If a suite-level pipelines skill exists in `skills/generative-media/`, link it rather than duplicating.

The pillars are constant; their mechanics are not. Character consistency in a still model is a dataset-and-adapter problem; in a temporal model it is additionally a frame-to-frame and shot-to-shot problem. Your modality reference gives the real content for each.

### Canonical reference slots

Name reference files by concern so the suite stays navigable: `prompting-guide.md`, `setup-and-workflows.md` (or `workflows.md`), `lora-training.md`, `characters.md`, plus model-specific extras (`api-*.md`, `controlnet-and-identity.md`, `motion-and-camera.md`, `self-hosting.md`). A model-specific name is fine when the concern is model-specific; don't invent a new name for a standard slot.

**Keep `SKILL.md` under ~500 lines.** Push depth into `references/` and point at it from the table. Large reference files get a table of contents. Organize references by variant/domain when the model has several — one file per concern, not one giant file.

---

## Step 3 — Write in the house style

The published skills read as trustworthy for reasons the headers don't capture. Match these:

- **Explain the *why*, don't command.** "Emit the floor as an `obj` and the renderer treats it as a flat 2D band and buries the subject's legs" teaches the model to generalize. "ALWAYS put the floor in background" does not. If you catch yourself writing `ALWAYS`/`NEVER` in caps or a rigid MUST, reframe it as a mechanism the reader can reason from.

- **Mechanism over adjective.** "Stack a real camera body + a real film stock + one non-idealised feature" beats "use realistic, high-quality." Give concrete, copy-pasteable specifics — real lens names, exact node settings, literal CFG values, actual filenames.

- **Tables for anything with parallel structure** — selectors, file layouts, settings, failure modes. They're scannable and force you to fill every cell, which surfaces gaps in your research.

- **Make the `description` pushy.** Claude under-triggers skills. Enumerate every oblique way a user might touch this model — choosing a variant, installing it, fixing a prompt, building a workflow, training a LoRA, debugging an artefact — and say "use this whenever the user touches <model> in any way, even obliquely." List concrete trigger phrases. Copy the published skills' *density*, not their words.

- **Surface contested or uncertain claims** rather than smoothing them over. "Turbo negative-prompt behaviour is contested: the team says X, community reports Y; official guidance is authoritative." Honesty about disagreement is what makes the skill safe to trust.

---

## Step 4 — Provenance discipline: two bars, by claim type

Media models ship and change weekly, and a skill that states guesses as fact will mislead. But don't grade claims on a single official-beats-community ladder — the suite's closing section ("How to read the claims in this skill", present in every published skill) holds **two kinds of claim to two different standards, because they fail in two different ways**:

- **Hard facts — must be exact or it breaks.** Filenames, node names, what a setting numerically does, licence terms, architecture, pipeline classes. **Source of truth is official** (repo, model card, licence file, template JSON — read verbatim). These are also the *volatile* ones in a young model — re-verify before relying on them, regardless of who said it. A wrong filename 404s; a misread licence is a legal problem.
- **Craft — what actually makes a good result.** Sampler/CFG/denoise ladders, LoRA weights and datasets, multi-stage pipeline numbers, realism stacking, character protocols, motion tuning. **The authoritative source here is the community** — named, reproducible workflow authors and trainers who've run thousands of generations — *not* the model card, which ships one example and moves on. State craft with confidence; ranges and "tune this" flags mean "your weights/finetune/resolution differ from the author's," not "this is unreliable." Where strong named sources genuinely disagree, **show the disagreement** rather than papering over it.

While researching, still tag every fact inline — `[official]`, `[official-via-docs]`, `[community — named author]`, `[flagged — re-verify]`, and `[contested]` where strong named sources genuinely disagree — because the tags are what let you write the two-bar section honestly at the end. `[flagged]` and `[contested]` are the two that seed the freshness watchlist in Step 5, so apply them deliberately rather than as hedges. The guardrail on the craft bar: "authoritative community" means named/reputable/reproducible (Civitai authors, Ostris, kohya discussions, established workflow channels), not anonymous forum noise or SEO farms.

Include the **release date**, a note on what's fast-moving, and an explicit "re-verify before relying on" for the volatile specifics (pricing, quant filenames, ComfyUI template details, LoRA tooling).

---

## Step 5 — Place and finish

1. Author into **`skills/generative-media/<model-name>/`** — this repo is the skills.sh marketplace, and skills are grouped by **domain** under `skills/`. Model skills always go in `generative-media/`. (This meta-skill lives in `.agents/skills/`, which is authoring machinery and is not part of the published catalogue.)

   **Keep every cross-skill link relative and inside the domain** — `../sibling/` or `../../sibling/reference.md`. Nothing should reach above `skills/generative-media/`. That is what lets the catalogue be reorganised without rewriting links, and a link escaping the domain means the skill is misfiled.
2. Use a clean kebab-case `<model-name>` matching the `name` frontmatter (e.g. `flux-2`, `sdxl`, `wan-2-2`).
3. **Register the new skill** in `.claude-plugin/marketplace.json` (add `"./skills/<model-name>"` to the plugin's `skills` array) and add a row to `README.md`'s skills table. Without this it isn't published.
4. **Register it for freshness** with `/skill-freshness register <name>` — set the tier from how fast the model's ecosystem is actually moving, and seed the watchlist with every claim you tagged `[flagged]` or `[contested]` while researching. A skill that isn't in `freshness.json` silently rots.
5. Re-read your draft with fresh eyes against the published examples: Is the description pushy enough? Is every load-bearing number sourced? Does the failure-modes table explain mechanisms? Is the two-bar closing section honest? Are all three pillars covered or honestly routed?

**Validate by running it.** Because this is an authoring skill, the natural test is to use the finished skill on a real request and eyeball the result — does it set the model up correctly, prompt it the model's way, and debug a real artefact? That demo is worth more than synthetic assertions for prose like this; offer it to the user once a draft exists. (If the user does want a formal eval loop, the `skill-creator` skill has the machinery — but a subjective authoring skill rarely needs it.)

---

## Author's pre-flight checklist

Shared checks — your modality reference adds its own:

1. Routed by modality (Step 0) and read the matching reference **plus its named ground-truth skills** in full first?
2. File layout + stock node settings taken **verbatim from the official template JSON**, not from memory or a docs page that omitted the numbers?
3. Model shape chosen deliberately and reflected in the spine?
4. "The one rule that changes everything" discovered from *this* model's conditioning path — not copied from another skill?
5. Conditioning-class doctrine applied *with each axis stated separately and its mechanism given* — at minimum encoder class and guidance state, plus the image-conditioning and temporal axes for video — and each **verified against this model's template JSON and model card**, not assumed from the doctrine tables?
6. All three pillars covered or honestly routed — characters, LoRA training, production pipelines?
7. Every load-bearing number attributed — `[official]` / `[community — named author]` / `[flagged]` — with craft credited to named community sources, not laundered through SEO farms?
8. Failure-modes table explains the *mechanism* in each cause cell?
9. License split (code / weights / output) stated plainly if it exists?
10. Two-bar "How to read the claims" section present, date-stamped, contested craft shown as contested, with a "re-verify fast-moving specifics" note?
11. `description` pushy, with concrete trigger phrases ("even obliquely") covering the pillars too?
12. `SKILL.md` under ~500 lines, depth pushed into `references/` using the canonical slot names, with a pointer table?
13. Authored into `skills/generative-media/<model-name>/`, name matching the folder, **registered in `marketplace.json` + the README table**, and **registered in `freshness.json`**?
14. Comparative "when to use another model instead" note included, with **bidirectional** back-links — including across modalities, and including updating the other skills to point back?
