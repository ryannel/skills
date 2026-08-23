---
name: ideogram-4
description: >
  Authoritative guide for running Ideogram 4.0 (Ideogram, Inc.) — Ideogram's first open-weight text-to-image model — yourself, on your own GPU or a rented cloud GPU (RunPod, Vast.ai), via ComfyUI, the diffusers Ideogram4Pipeline, or the run_inference.py CLI; the hosted API and web app are covered as the secondary, commercial-clean surface. **The open weights are non-commercial wherever you run them — for commercial output, route through the hosted API or web app instead.** Use this whenever the user touches Ideogram 4 in any way, even obliquely: choosing a surface and understanding the licence split (non-commercial weights, Apache code, outputs yours), writing or fixing prompts (the model is trained exclusively on structured JSON captions — schema, key ordering, the CaptionVerifier, plain-text vs JSON, Magic Prompt expansion), text rendering and typography (its headline strength — multi-line stacking, multilingual, editable text layers, transparency), bounding-box layout and hex color-palette control, getting photoreal results the Ideogram way (neutral white balance, killing the "warm"/amber look), choosing rendering speed / sampler preset (Quality 48 / Default 20 / Turbo 12) and resolution, setting up the open weights (nf4/fp8 quant, VRAM, HF gating, ComfyUI nodes and file layout, DualModelGuider, the gemma4 gotcha), training a LoRA on it (ai-toolkit and fal's trainer, which emits ComfyUI-format weights; style LoRAs work, character LoRAs are trainable but undemonstrated), using it as the typography/design pass in a mixed-model pipeline, routing through the hosted API/web app when commercial use or the web-only Character/Style Reference features require it, and debugging the safety filter, verifier aborts and layout failures. Also use it to learn what Ideogram 4 is the wrong tool for — consistent characters on open weights, where no identity adapters exist. Use this for any question about Ideogram 4 in any context.

---

# Ideogram 4

Ideogram 4 is **Ideogram, Inc.'s first open-weight text-to-image model** (released 3 June 2026). It is a **9.3B-parameter, fully single-stream Diffusion Transformer (DiT)** trained from scratch — text tokens and image latent tokens travel through one 34-layer sequence. The text encoder is **Qwen3-VL-8B-Instruct**, a full vision-language model (hidden states from 13 layers concatenated). It is a flow-matching model with **dual-branch (asymmetric) classifier-free guidance** — a separate unconditional transformer — and renders **native 2K** at any resolution 256–2048 px (multiples of 16, aspect ratios to 6:1).

**The defining trait:** it was trained **exclusively on structured JSON captions**. Plain-text prompts work, but a JSON caption that follows the schema is how you unlock its real strengths — best-in-class text rendering, bounding-box layout, and hex color-palette control.

**This skill is about running the open weights** — the gated `nf4`/`fp8` model on your own GPU (or a rented cloud GPU) via **ComfyUI**, the diffusers **`Ideogram4Pipeline`**, or the **`run_inference.py`** CLI. That's the path with full control over every sampler knob, and the one the rest of this guide assumes.

**Know the licence split before you start** — it is the single most-misunderstood fact about this release. The **code** is Apache-2.0, the **weights** are under the Ideogram 4 Non-Commercial Model Agreement, and the **outputs** are yours. The restriction is on *purpose*, not place: renting a cloud GPU grants no commercial rights. Which surface that leaves you is the next section; the clauses themselves are *Licence & limitations*.

---

## Surface selector

There is one checkpoint, so the first choice is not *which weights* but *which surface* — and unusually for this suite, the licence decides it rather than the hardware. Settle this before writing a caption: the surfaces differ in what they can do, not just in convenience.

| Surface | Use when… | What you give up |
|---|---|---|
| **Self-hosted open weights** — ComfyUI, diffusers `Ideogram4Pipeline`, `run_inference.py` (your GPU or a rented pod) | Non-commercial work — research, personal, hobby, internal. You want every sampler knob, reproducible seeds, batch runs, or a LoRA in the graph | Commercial rights; Character/Style Reference; the edit family (Magic Fill, reframe, upscale, layerize) |
| **Hosted API** — `POST /v1/ideogram-v4/generate` | The output is commercial, or you want the edit/describe/remix endpoints, or you'd rather not own a 24 GB GPU | Sampler control — you get three `rendering_speed` tiers, not schedules; per-image cost; `seed`/`num_images` unconfirmed on v4 `[flagged — re-verify]` |
| **Web app** | You need **Character Reference** (face identity) or **Style Reference** — they exist nowhere else — or the interactive editing tools | Automation and reproducibility; it is a UI, not an endpoint |

**Renting a cloud GPU does not move you between rows** — a RunPod H100 running the open weights is still the top row. Surfaces two and three: `references/api-and-hosted.md`.

---

## The one rule that changes everything

**Write a structured JSON caption, not a prose paragraph or a tag list.** The model was trained only on JSON, so JSON minimises train/inference mismatch and is the reliable way to get every requested object, every line of text, and your exact layout. Plain text is a fallback that underperforms — and trips the safety filter more often `[official — ideogram-oss/ideogram4 docs/prompting.md]`.

Minimal valid caption — `compositional_deconstruction` is the only **required** top-level field:

```json
{
  "high_level_description": "A medium-shot photograph of a barista pouring latte art in a cozy cafe.",
  "compositional_deconstruction": {
    "background": "A warm cafe interior with blurred shelves of mugs and a chalkboard menu on the back wall.",
    "elements": [
      {"type": "obj", "desc": "A barista with short dark hair and a green apron, tilting a steel pitcher to pour a leaf pattern into a white ceramic cup held in both hands."}
    ]
  }
}
```

**Don't want to write JSON?** That is what **Magic Prompt** is for: an LLM expands your idea into a full caption first — automatic in the web app and for `text_prompt` on the API, on by default in `run_inference.py`, with three shipped backends. **None is offline**; each calls a hosted LLM, so a fully local path means running the open-source system prompt through your own model (ComfyUI bundles `gemma4` for exactly this).

Full schema, the caption-craft rules, and worked examples: **`references/json-caption-guide.md`**.

---

## The JSON caption schema (canonical)

Three top-level fields, in this order. **Key order is strict** — the pipeline runs a `CaptionVerifier` that warns on wrong order, unknown keys, or missing required keys, and `run_inference.py` **aborts on those warnings by default** (`--warn-on-caption-issues` downgrades to warnings).

| Field | Required? | Holds |
|---|---|---|
| `high_level_description` | optional, strongly recommended | one or two sentences summarising the whole image |
| `style_description` | optional | the visual style block (see below) |
| `compositional_deconstruction` | **required** | `background` (string, required) + `elements` (list, required) |

**`style_description`** must contain **exactly one** of `photo` (photographic) or `art_style` (everything else), plus `aesthetics`, `lighting`, `medium`; `color_palette` is optional and **must be last**. **`elements`** are objects (`type:"obj"`) or text (`type:"text"`). Each of those three blocks has its own strict key order — including where an optional `bbox` or `color_palette` must sit — and the exact orders, field meanings and worked examples are `references/json-caption-guide.md` §1. Look them up rather than guessing: the verifier catches you, but only after you have written the caption.

- **`bbox` = `[y_min, x_min, y_max, x_max]`**, normalised **0–1000 on both axes**, origin top-left. (Note: **y comes first** — easy to invert.)
- **`color_palette`** entries are uppercase `#RRGGBB` only (no shorthand). Up to **16** at style level, **5** per element.
- **`text`** (text elements only) is the literal string to render, verbatim.
- Serialize with `json.dumps(caption, separators=(",", ":"), ensure_ascii=False)` — keep non-ASCII (CJK, accents) literal; the verifier warns on `\uXXXX` escapes.

> **Two valid shapes, both official.** The schema above (with `style_description`) is best for hand-authoring — it gives explicit style + palette control. The shipped **Magic Prompt** produces a *prose-style* variant: it folds style into `high_level_description`/`background` text, omits `style_description`, and **strips bboxes by default**. Both pass the verifier (`style_description` is optional). Use the full schema when you want layout/palette control; let Magic Prompt handle casual prompts.

---

## Per-mode settings

**One axis, not per-checkpoint variants.** There is a single Ideogram 4 checkpoint, and the only mode axis is speed — the same three presets everywhere: sampler presets on the self-hosted weights, `rendering_speed` tiers on the API, credit tiers in the web app. One table rather than three `###` blocks, because nothing else varies with the mode: sampler, scheduler, resolution range and seed behaviour are identical across all three, and negatives don't exist at any tier (the model has no negative-prompt string — see *ComfyUI* below).

| Preset (self-hosted) | API `rendering_speed` | Use when… | Steps | Guidance schedule | `mu` | `std` | API $/image¹ |
|---|---|---|---|---|---|---|---|
| `V4_QUALITY_48` *(default)* | `QUALITY` | Final delivery, hero shots, anything at 2K, dense typography | 48 | 45 steps @ gw 7, then 3 polish @ gw 3 | 0.0 | 1.5 | $0.10 |
| `V4_DEFAULT_20` | `DEFAULT` *(API default)* | Most iteration work — composition and layout read correctly here | 20 | 18 @ gw 7, then 2 polish @ gw 3 | 0.0 | 1.75 | $0.06 |
| `V4_TURBO_12` | `TURBO` | Drafts and batch exploration; judging a caption before committing | 12 | 11 @ gw 7, then 1 polish @ gw 3 | 0.5 | 1.75 | $0.03 |

Across all three: sampler **`euler`**, scheduler **`Ideogram4Scheduler`**, `seed` for reproducibility, and guidance **7.0** constant whenever no schedule is supplied. Higher guidance = more prompt adherence, lower = more diversity.

> ¹ API per-image prices from ideogram.ai/api-pricing `[official — ideogram.ai/api-pricing]`. A `FLASH` API tier is announced but returns 400 ("coming soon") `[pending release]`.

**Resolution.** Default 1024×1024. Native range 256–2048, multiples of 16, aspect ratios to 6:1 / 1:6. For maximum quality pair **2048×2048 with `V4_QUALITY_48`**. Three surfaces, three parameter shapes: the diffusers pipeline takes `height`/`width`, the API an explicit `resolution` string (`"2880x1440"`), the web app and Magic Prompt endpoint an `aspect_ratio` string (`"16x9"`). Common pairs: `references/setup-and-workflows.md` §2.

---

## Caption craft — the high-leverage rules

These come straight from Ideogram's **open-source Magic Prompt system prompt** — i.e. how Ideogram itself instructs an LLM to write captions. They are the single best guide to what the model actually wants. Full detail in `references/json-caption-guide.md` §3.

- **One subject = one element.** A person, animal, car, or building is exactly one `obj`; anatomical/structural parts go in that element's `desc`, never as separate elements. Multiple *distinct* subjects (a person *and* a dog) = multiple elements.
- **`background` is the shell only.** Walls, floor/ground, sky, atmosphere, ambient light, distant blurred context. **The ground/floor/pavement is ALWAYS `background`** (including puddles, reflections, wet/cracked surface state) — *zero tolerance*. Furniture, vehicles, people, decor, free-standing lamps are **elements**, never background.
  - **Why it matters (a real failure mode):** emit the floor as an `obj` and the renderer treats it as a flat 2D band at the bottom of the frame and **buries the subject's legs in it**. Keep the floor in `background`.
- **No double-counting.** Every component lives in exactly one field: before emitting an `obj`, scan `background`, and if it's named there, drop the `obj`.
- **Shell-affixed hero objects → dual mention.** A chalkboard wall, built-in fireplace, mounted TV: (1) name it in `background`, (2) also emit it as an `obj` whose `desc` starts with "the primary background element", (3) place it **first** in `elements` (painter's algorithm draws it behind foreground items).
- **Commit to one value — no hedging.** Banned in element/background text: `things like`, `such as`, `various`, `or similar`, `e.g.`, `style of`, and alternative listings (`oak or walnut`, `bold or semibold`). Pick one and commit. Typography: one typeface category, one weight, one style.
- **Keep render-language out of `obj` descs.** Depth of field, bokeh, grain, motion blur and shadows belong in `high_level_description`/`background`, and only if asked — the renderer infers shadows. Viewpoint (`low-angle`, `bird's-eye`) *is* allowed in a desc.
- **Populate sparse scenes** by depth layer, and commit to a *specific* place ("a pho stall outside Hoi An", not "a Southeast Asian village"). Built environments carry text on every surface — `text: []` is almost always wrong for a shop or market.

**Bounding boxes — the #1 failure.** `bbox` is normalised 0–1000 on **both** axes, so a "square" `[0,0,500,500]` is square only on a 1:1 frame; on 16:9 it is a wide rectangle, on 9:16 a tall one. **Most duplicate, extra-subject and mis-scale bugs come from this.** Scale spans so `(x2−x1)/(y2−y1) ≈ W/H`, give each subject a tight box so none dominates and invites a duplicate, and omit bboxes entirely on unenumerable content (crowds, fields, starfields).

---

## Realism the Ideogram way (the *opposite* default to most models)

Ideogram 4's shipped caption-expander does the **reverse** of many models: for an *underspecified* photographic prompt it injects a neutral, phone-snapshot look and steers away from camera-gear markers, because they tend to read as AI-generated. These are the expander's **defaults, not model prohibitions** — if you deliberately want a warm golden-hour or cinematic DSLR look, just specify it concretely and you'll get it. But when you haven't asked for a specific look, prefer:

- **Avoid "warm" as a bare grading adjective.** `warm light`, `warm tone`, `warm grading` tend to trigger the amber/golden "AI look". If a scene has a physically warm source (candle, sodium lamp, sunset), name the **source** and the **colour of the light pool** ("amber pool from the candle") rather than grading the whole image "warm".
- **Default to the iPhone aesthetic, not DSLR-magazine.** Creamy bokeh, telephoto compression, dramatic rim light, and cinematic grades read as AI when *unrequested*. For a neutral realistic look prefer "natural/overcast daylight, cool-neutral white balance, accurate (not flattering) skin tones, ordinary framing".
- **No motion blur in candid/realistic shots** (real phone snaps freeze the moment).
- **"Professional photo of a person" = professional context** (corporate headshot, neutral attire, soft even daylight), **not** professional camera equipment.
- **Off-center / rule-of-thirds by default**; centre only when the prompt asks.

> These aesthetic defaults come from Ideogram's **open-source expander system prompt**, which Ideogram notes differs from its production Magic Prompt — treat them as well-informed taste, not hard rules. The *structural* schema rules elsewhere in this skill (one-subject-per-element, background-as-shell, key ordering, bbox) are model facts, independently confirmed by the repo's `prompting.md` and `caption_verifier.py`.

Photoreal faces and skin are Ideogram 4's relative **weak spot**. Its strengths are design, typography, and layout.

---

## Text rendering & typography (the headline strength)

Ideogram 4 leads open models on in-image text — 0.97 X-Omni English OCR `[official — Ideogram 4 model card]`. To use it well:

- **One text element per visually distinct block.** Use `\n` for line breaks *within* one block; use separate elements for separate blocks.
- **Stack stylised hero titles with `\n` at word breaks** — long single-line stylised titles produce typos and dropped letters (`"ENTRE\nVERSOS E\nCONTOS"`, not one line).
- **Numbers are text** — jersey numbers, prices, dates, addresses each go in a `text` element.
- **Multilingual:** English + CJK/Cyrillic/etc. render well; keep prose fields in English and put only the literal characters in `text`, stored as literal UTF-8 (`ensure_ascii=False`).
- **Editable text layers & native transparency** are first-class v4 features — the web app can "layerize" text and output transparent PNGs; for a cutout, set `background` to exactly `"transparent background"`.

Typography is also what Ideogram contributes to work that starts in another model — that handoff is *Production pipelines & mixing models*, below.

---

## Setup & ecosystem

- **Web app / API:** nothing to install. Auth header is `Api-Key`; the core call is `POST /v1/ideogram-v4/generate` with `text_prompt` *or* `json_prompt`. Endpoints, params, pricing, web-app tools: **`references/api-and-hosted.md`**.
- **Self-hosted open weights (gating):** gated on Hugging Face — accept the licence and authenticate (`hf auth login` / `HF_TOKEN`) or downloads 404. Two quants: **`nf4`** (bitsandbytes 4-bit, **CUDA-only**, diffusers-compatible, fits a 24 GB GPU) and **`fp8`** (weight-only float8, **any hardware**, activations stay bf16). diffusers exposes **`Ideogram4Pipeline`**; the repo ships a `run_inference.py` CLI. All three stacks run identically on a **rented cloud GPU**, which is the usual way to reach 24 GB+ for the larger quants and 2K renders. Quick start, sampler presets and VRAM notes: **`references/setup-and-workflows.md`**.

**What the open weights don't have is a short list with long consequences.** No ControlNet, no PuLID, no IP-Adapter face, no edit variant — and the 34-layer single-stream DiT is structurally incompatible with existing ControlNet and IP-Adapter implementations, so this is not a "not ported yet" gap. The only structural control is the **`bbox` layout** inside the caption: it constrains *where* elements land, never skeleton or depth. **Character Reference** and **Style Reference** are web-app and v3-API only (`references/api-and-hosted.md` §6).

**LoRA training, though, does exist — as a style ecosystem, not a character one.** `ostris/ai-toolkit` lists `ideogram-4-fp8`, and fal's live **Ideogram V4 LoRA Trainer** emits a ComfyUI-format file alongside its own, so a hosted-trained LoRA runs on the open weights; **33 are published on Civitai**, overwhelmingly style work. **So consistent characters still route elsewhere — but for a narrower reason than "there is no path":** the path exists and nobody has walked it. Build the character in [`flux-2`](../flux-2/) or [`z-image`](../z-image/), or use hosted Character Reference, then bring the result here for the typography pass. Training: `references/lora-training.md`, plus [`character-lora-training`](../character-lora-training/) for what transfers.

### ComfyUI (day-0 native support)

Native support landed on launch day. Use the official template **`image_ideogram4_t2i.json`** (`Comfy-Org/workflow_templates`); the walkthrough is on `docs.comfy.org/tutorials/image/ideogram/ideogram-v4`. **Requires an updated/nightly ComfyUI** — the loaders are new and stable Desktop/Cloud builds lag (inside a pod, pull the nightly). Details below are read verbatim from the template JSON.

**File layout** (download into these folders):

| File | ComfyUI folder | Role |
|---|---|---|
| `ideogram4_fp8_scaled.safetensors` | `models/diffusion_models/` | conditional model — `UNETLoader` |
| `ideogram4_unconditional_fp8_scaled.safetensors` | `models/diffusion_models/` | unconditional model — `UNETLoader` |
| `qwen3vl_8b_fp8_scaled.safetensors` | `models/text_encoders/` | text encoder — `CLIPLoader`, type **`ideogram4`** |
| `flux2-vae.safetensors` | `models/vae/` | VAE — download from `Comfy-Org/ideogram-4` on Hugging Face |
| `gemma4_e4b_it_fp8_scaled.safetensors` | `models/text_encoders/` | optional in-stack captioner LLM (separate `Comfy-Org/gemma-4` repo) |

**What's unusual:** **two diffusion models load** and combine through a **`DualModelGuider`** — this is the model's dual-branch (asymmetric) CFG (a conditional + a separate unconditional transformer), not a negative-prompt string. Stock template defaults: sampler **`euler`**, **`Ideogram4Scheduler`** at **20 steps** (the Default tier; a `CustomCombo` switches Quality 48 / Default 20 / Turbo 12), `DualModelGuider` guidance **7**, latent **1024×1024**.

**Two prompt modes:** a plain sentence, or a JSON caption pasted into the multiline `CLIPTextEncode` field — its default already holds one, and downstream `JsonExtractString` nodes pull dimensions out of it.

> **`gemma4` gotcha:** it is on the required-download list but **no node in the shipped template loads it**. It is the recommended *in-stack* LLM for the natural-language → JSON caption step (your own GPU, versus the hosted `ideogram-4-v1` Magic Prompt), and the template ships a string-assembly helper subgraph but no LLM-execution node — so you run that conversion yourself. Downloading it and finding nowhere to plug it in is the most common first-day confusion.

Full node table, VRAM reports, the `nf4`-vs-`nvfp4` file-naming caveat, and GGUF status: **`references/setup-and-workflows.md` §4**.

---

## Production pipelines & mixing models

Most skills in this suite describe a ladder that stays inside one model — base, refine, detail, upscale. Ideogram 4's does not, and that is the honest shape of it: on the open weights there is **no edit variant and no image conditioning of any kind** (no ControlNet, no IP-Adapter, no remix — that lives on the hosted API only), so the model can neither refine its own output nor accept a base image from upstream. The pipeline is a **handoff**, one-way by construction, and Ideogram owns exactly one rung of it: the text and design layer.

1. **Generate the base scene** in whichever model suits the imagery — [`flux-2`](../flux-2/) or [`z-image`](../z-image/) for photoreal and illustrated work, [`krea-2`](../krea-2/) for stylised, [`sdxl`](../sdxl/) when you need its checkpoint ecosystem or a ControlNet rig. Lock composition **at the final aspect ratio**; you cannot reframe later without regenerating the type.
2. **Generate the text/design layer in Ideogram 4**, in one of two shapes. A **transparent plate** — `background` set to exactly `"transparent background"` (`references/json-caption-guide.md` §8) — gives a PNG with alpha to drop over the base, and is the more controllable option. Rendering the type **inside the target composition**, with `bbox` pinning each `text` element and the base scene restated in `background`, integrates better because the lighting reads.
3. **Composite, or inpaint the plate in.** A straight alpha composite where the type sits flat on the frame; an inpaint pass in the *base* model at low denoise where it has to sit **on** a surface — a sign, a shirt, a shop window — and pick up that surface's perspective and light.
4. **The inverse order often beats it.** Render the whole design in Ideogram, mask everything *except* the text, and restyle the imagery in the other model: you keep Ideogram's layout and typography, buy the other model's texture, and the masked type cannot be garbled by an SDXL or Flux pass.
5. **Generate the plate at final size.** Ideogram renders native 2K at arbitrary 16-multiples; upscaling a text plate afterwards softens exactly the edges that make type read as type.

**Which rungs are bypassable:** all but 2 and 3. Steps 1 and 4 are alternatives rather than a sequence, and a purely design-led job (poster, ad, packaging mock) skips the other model entirely, leaving 2 and 5.

**Every step crosses model families, so every step is pixel-space:** export PNG, re-encode in the receiving model's VAE. The trap specific to this pairing is that Ideogram 4 **reuses Flux.2's VAE file** (`flux2-vae.safetensors`) and latent space, which makes a direct latent handoff look like it should work. It doesn't — a shared VAE means the two *decoders* agree, not that a latent conditioned by one model carries meaning in the other. Decode to pixels like any other cross-model step.

This role is widely practiced but has **no canonical named workflow** — no published node graph, no named author's recipe `[flagged — re-verify]`. Treat the ladder above as reasoned from what the model can and cannot do, not transcribed from one. Cross-model craft in general — denoise bands, resolution matching, colour management — is [`image-production-workflows`](../image-production-workflows/), where this belongs once someone writes it down.

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| Gray screen, "Image blocked by safety filter" | Model-level NSFW filter (in the weights, can't disable); fires more on plain text | Rephrase; **use a JSON caption** — lower false-positive rate `[official — ideogram-oss/ideogram4]`; the team has acknowledged over-blocking and plans a checkpoint update |
| Pipeline aborts / caption warnings | Wrong key order, unknown key, missing required key, or `\uXXXX` escapes | Match the canonical key order; serialize with `ensure_ascii=False`; or pass `--warn-on-caption-issues` to continue |
| Subject's legs buried in the floor / floor looks like a 2D band | Floor emitted as an `obj` element | Move the floor/ground into `background` (always) |
| Extra/duplicate subjects, mis-scaled objects | `bbox` square-on-non-square distortion (0–1000 both axes) | Scale bbox spans to the frame's W/H ratio; tight box per subject |
| Requested object or line of text missing | Plain-text prompt, or object not given its own element | Use JSON; give every named subject and every text string its own element |
| Garbled / wrong long title | Long single-line stylised text | Split into `\n` chunks at word breaks; ≤ a few words per visual unit |
| Over-processed amber/golden "AI" look on an unrequested photo | bare `warm` grading, DSLR-bokeh/cinematic markers added by default | Neutral white balance, iPhone aesthetic; name the light *source*, not "warm" (or specify the look you actually want) |
| Casual prompt underperforms vs expectation | Plain text under-specifies; model trained on dense JSON | Write JSON (or let Magic Prompt expand), pinning positions, colors, per-element styling |
| Wrong colors / palette ignored | Lowercase or shorthand hex, or palette missing background color | Uppercase `#RRGGBB`; include background + contrast colors in the palette |

---

## Pre-flight checklist

Before generating:

1. JSON caption (not prose / not tags), or deliberately letting Magic Prompt expand plain text?
2. `compositional_deconstruction` present, with both `background` and `elements`?
3. Key order correct everywhere (top level, `style_description`, each element)?
4. One subject per `obj`; multiple subjects → multiple elements?
5. Floor/ground/sky/ambient light in `background` only — nothing individually-placeable in there?
6. bboxes scaled to the frame's aspect ratio (0–1000 both axes, `[y,x,y,x]`)?
7. Every line of text its own `text` element; long titles split with `\n`?
8. Hex palette uppercase `#RRGGBB`, ≤16 at style / ≤5 per element, background color included?
9. Photoreal: neutral grade, no "warm", no DSLR-bokeh markers?
10. Right surface for the job — commercial output via web app/API, **not** the non-commercial self-hosted weights (RunPod/cloud doesn't change that)?
11. Serialized with `separators=(",",":")` and `ensure_ascii=False`?

---

## Where Ideogram 4 sits in the suite

| Job | Ideogram 4 | Reach for instead |
|---|---|---|
| In-image typography, layout, design | **The leader** — JSON captions, `bbox` layout, text layers, transparency | — (this is why you're here) |
| Consistent characters | **Weak on open weights** — no identity adapters, no edit variant, no published character LoRAs | [`flux-2`](../flux-2/) (multi-ref + PuLID), [`z-image`](../z-image/) or [`sdxl`](../sdxl/) (character LoRA); or hosted Character Reference |
| **Style LoRAs** | **Supported** — ai-toolkit lists `ideogram-4-fp8`; fal's trainer emits ComfyUI-format weights; 33 published on Civitai | Fine to train here. [`krea-2`](../krea-2/) if you want the official train-Raw/run-Turbo doctrine |
| **Character LoRAs** | Trainable, essentially **undemonstrated** — the path exists, the ecosystem doesn't. One cross-model comparison exists, rating Ideogram 4 *above* Krea 2 and Z-Image at learning tattoos `[community — Any_Tea_3499; single report]` — recorded in [`krea-2`](../krea-2/references/characters.md), which means somebody has trained one; no published recipe | [`sdxl`](../sdxl/) (mature) or [`z-image`](../z-image/)/[`flux-2`](../flux-2/); craft in [`character-lora-training`](../character-lora-training/) |
| Photoreal faces & skin | Relative weak spot | [`z-image`](../z-image/) (realism stacking) or an [`sdxl`](../sdxl/) photoreal finetune |
| Stylised / aesthetic-led imagery (non-typographic) | Design-literate but one aesthetic register | [`krea-2`](../krea-2/) — style references, moodboards, the widest open-weights visual range; [`anima`](../anima/) if the register you want is anime or booru illustration, which is a vocabulary this model was never captioned in |
| Structural control (pose/depth) | `bbox` layout only | [`sdxl`](../sdxl/) or the Fun Union ControlNets ([`flux-2`](../flux-2/), [`z-image`](../z-image/)) |
| Commercial use under the licence | **Purpose-restricted weights** — non-commercial wherever you run them, the same shape as [`flux-2`](../flux-2/)'s [dev] and 9B variants and [`anima`](../anima/)'s Model. What is unusual here is not the restriction but the absence of an escape hatch: FLUX.2 keeps [klein] 4B under Apache-2.0, and Anima carves its *outputs* out of the restriction entirely, whereas Ideogram's grant excludes generating output for revenue-generating products at all. Outputs are yours to own; producing them commercially *from the weights* is outside the grant | The hosted API or web app (`references/api-and-hosted.md`), or a paid weights licence — here the fallback is hosted, not another variant. Commercial *and* self-hosted isn't this model: [`z-image`](../z-image/) is the freest path in the suite (Apache-2.0 on weights and outputs alike), [`sdxl`](../sdxl/) carries no purpose restriction, and [`flux-2`](../flux-2/) has the Apache-licensed [klein] 4B |
| Mixed-model pipelines | **The typography pass** — text plates and design layers for other models' imagery | [`image-production-workflows`](../image-production-workflows/) for the cross-model craft |
| Making it move | Still images only | [`wan-2-2`](../wan-2-2/) — image-to-video from a still locked here. Know the limit: rendered text does not survive motion cleanly, so animate *around* type rather than through it |
| **Choosing between all of these in the first place** | — this table is one model's view of the suite | [`generative-media-atlas`](../generative-media-atlas/) — the whole suite ranked by job (realism, identity, LoRA trainability, control, licence, video), the elimination ladder that settles most choices, and end-to-end routes across several skills |

---

## Licence & limitations

**The licence split (verify before any commercial use):**
- **Inference code** (GitHub `ideogram-oss/ideogram4`): **Apache-2.0**.
- **Model weights** (HF `ideogram-ai/ideogram-4-nf4` / `-fp8`): **Ideogram Non-Commercial Model Agreement** (dated 3 June 2026). Free for research, personal, hobby, charitable, and internal non-production use. "Non-Commercial Purposes" **explicitly excludes** generating output for, or to advertise, revenue-generating products, and excludes commercial fine-tuning/distillation. Weights are **gated** on Hugging Face. Redistribution must pass on the same terms, include the attribution notice, and mark modifications.
- **Outputs:** you own them — Ideogram claims no rights in your outputs (both the Non-Commercial Agreement and the web/API Terms). But generating those outputs *via the self-hosted weights* for commercial purposes is outside the grant — and that holds wherever you run them (your GPU, RunPod, any cloud). **For commercial work, use the web app or hosted API** (whose Terms assign output ownership to you and permit commercial use), or obtain a separate commercial weights licence from Ideogram.
- **Use restrictions** (weights): no military/surveillance, no biometric processing, no competing-model training from outputs, must not remove watermarking/safety measures, AI-disclosure where legally required.

**Safety filter.** Two layers: (1) a **model-level** NSFW filter that returns a gray "Image blocked by safety filter" screen — it is in the weights and false-positives are **higher for plain-text than JSON** prompts `[official — ideogram-oss/ideogram4]`, with a fix signalled; and (2) **optional external Hive** text+image moderation wired into the reference `run_inference.py` (you supply `HIVE_*` keys; it warns loudly if absent). The "open-weight ≠ open source" critique and the irony that the non-commercial licence restricts exactly the design/branding use-cases the model is best at are the main community grievances `[community — Hacker News]`.

**Release:** 3 June 2026. Ideogram has signalled checkpoint updates, notably for the safety filter, so the limitations above are a snapshot of one checkpoint rather than a permanent shape.

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways. Ideogram 4 is an **open-weights** model — gated `nf4`/`fp8` weights under a non-commercial licence, run through the diffusers `Ideogram4Pipeline` or ComfyUI — with the hosted API and web app as a side path for commercial output and the two web-only reference features. The bars below are the same shape as the other open-model skills; what differs is **recency**, and it changes the craft bar in a way worth stating outright.

**Hard facts — must be exact or it breaks.** Treated as hard fact here: the architecture (9.3B single-stream DiT, 34 layers) and the Qwen3-VL-8B-Instruct encoder with its 13 concatenated hidden-state layers; the JSON schema and every `CaptionVerifier` rule (key order, required fields, abort-on-warning); the three sampler presets and their exact `mu`/`std`/guidance schedules; the Magic Prompt backends; quantisation, the ComfyUI file layout and node names, and Hugging Face gating; the licence terms; and the `Ideogram4Pipeline` / `run_inference.py` surface. **Source of truth is official** — the `ideogram-oss/ideogram4` repo, the HF model cards, the raw ComfyUI template JSON, and the licence text. The failure modes are unforgiving in two directions: a wrong quant filename 404s the download, and a misread non-commercial licence is a legal problem rather than a rendering bug. **Young and volatile:** quant filenames (`nf4` vs `nvfp4`), VRAM numbers, template details and LoRA tooling all move — **re-verify before relying on them, regardless of who said it.** LoRA support went from "does not exist" to "ai-toolkit and fal both ship it" inside ten weeks.

**Craft — what actually makes a good image.** Almost entirely **JSON caption craft**: one subject per element, background-as-shell, dual-mention for shell-affixed hero objects, committing to one value instead of hedging, `bbox` strategy and its painter's-algorithm ordering, and the neutral-white-balance realism defaults. **Here the suite's usual answer does not hold.** Everywhere else the authoritative source for craft is the community — named practitioners with a track record. At a couple of months old Ideogram 4 has no such corpus: the self-hosting community exists (Civitai's 33 LoRA authors, the `ideogram-4-fp8` HF discussions, the ComfyUI day-0 walkthrough) but nobody has published the repeated, attributable testing a `[community — author]` marker points at. So this skill's craft rests on an **official artefact used as craft evidence** — Ideogram's open-source Magic Prompt system prompt, the instructions Ideogram gives an LLM to caption for its own model. Unusually strong for the structural rules, since they are what the model was trained against; only *informed taste* for the aesthetic defaults, which is why the realism section says so rather than stating them as prohibitions. **The LoRA ecosystem is real but lopsided** — essentially all style work, no character LoRAs, no identity adapters.

**Independent positioning** (third-party evals): #1 among open-weight models on DesignArena, #2 on a blind designer-preference eval (behind GPT Image 2) — strongest on text, typography and design, weakest on photoreal faces.

**Contested / unresolved points:**

- Whether Edit / Upscale / Reframe / Replace-Background actually run 4.0 through the `/v1/ideogram-v3/*` paths is an inference from the pricing page, not a stated fact `[flagged — re-verify]`.
- The ComfyUI-native 4-bit quant filename — `nf4` per the HF repo, or `ideogram4_nvfp4_mixed.safetensors` per some community workflows `[flagged — re-verify]`.
- The `CFGOverride` node's `0.7` field reads as an override-start fraction; exact meaning unconfirmed `[community — single report; re-verify]`.
- Community GGUF support (`stduhpf/ideogram-4-gguf`, `city96/ComfyUI-GGUF`) for this architecture is early and undocumented `[community — early; re-verify]`.
- Where a trained LoRA plugs into a graph that loads **two** diffusion models, and at what strength, has no published example `[flagged — re-verify]`.
- Whether a training set should be captioned in JSON, to match what the base model saw, is untested `[flagged — re-verify]`.
- Ideogram 4 as the typography pass in a mixed-model pipeline is widely practiced but has no canonical named workflow `[flagged — re-verify]`.
- The `FLASH` API tier is announced but still returns 400 "coming soon" `[pending release]`.

**Facts dated 2026-08-22**; hard facts last re-verified against source 2026-08-13, when the LoRA-training coverage was rewritten. LoRA tooling, quant filenames, the `FLASH` tier and the v3-edit-path inference move fastest — re-verify each before relying on it.

---

## Reference files

| File | When to read it |
|---|---|
| `references/json-caption-guide.md` | **Prompting** — read whenever writing or debugging a caption. The schema field by field; the complete caption-craft ruleset; text rendering & multilingual; color-palette conditioning; transparency; Magic Prompt; and drop-in templates to paste and edit |
| `references/setup-and-workflows.md` | Read when getting the weights running or a graph wired, on your GPU or a rented pod: diffusers `Ideogram4Pipeline`, the `run_inference.py` CLI, sampler presets, resolutions, nf4/fp8 quant + VRAM, HF gating, the full ComfyUI node table, GGUF status, the safety filter, and loading a LoRA you have trained |
| `references/lora-training.md` | Read before starting a training run: what the non-commercial licence permits and what it does to your LoRA, the ai-toolkit and fal trainers, the unresolved question of how to caption a training set for a JSON-trained model, what the 33 Civitai LoRAs actually are, and why character work here is exploratory. Cross-model craft: [`character-lora-training`](../character-lora-training/) |
| `references/api-and-hosted.md` | **Secondary / commercial-routing path only** — read when commercial use or the web-only Character/Style Reference features force you off the open weights. The hosted API (generate / remix / describe / magic-prompt endpoints, params, resolutions, pricing, rate limits), the web app (Magic Fill, reframe, upscale, transparency, editable text layers), and the ownership terms |
