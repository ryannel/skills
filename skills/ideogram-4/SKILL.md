---
name: ideogram-4
description: >
  Authoritative guide for running Ideogram 4.0 (Ideogram, Inc.) — Ideogram's first open-weight text-to-image model — yourself, on your own GPU or a rented cloud GPU (RunPod, Vast.ai), via ComfyUI, the diffusers Ideogram4Pipeline, or the run_inference.py CLI. Use this whenever the user touches Ideogram 4 in any way, even obliquely: understanding the licence split (non-commercial open weights, Apache code → route any commercial work through the hosted API/web app) and which surface a task actually needs, writing or fixing prompts (the model is trained exclusively on structured JSON captions — schema, key ordering, the CaptionVerifier, plain-text vs JSON, Magic Prompt expansion), text rendering and typography (its headline strength — multi-line stacking, multilingual, editable text layers, transparency), bounding-box layout and hex color-palette control, getting photoreal results (the Ideogram way — neutral white balance, kill the "warm"/amber look), choosing rendering speed / sampler preset (Quality 48 / Default 20 / Turbo 12) and resolution, setting up the open weights (nf4/fp8 quant, VRAM, gating, ComfyUI nodes and file layout, the diffusers Ideogram4Pipeline, the run_inference.py CLI), or — only when commercial use or the web-only Character/Style Reference features require it — routing through the hosted API/web app (endpoints, params, pricing), and debugging the safety filter, verifier errors, and layout failures.
---

# Ideogram 4

Ideogram 4 is **Ideogram, Inc.'s first open-weight text-to-image model** (released 3 June 2026). It is a **9.3B-parameter, fully single-stream Diffusion Transformer (DiT)** trained from scratch — text tokens and image latent tokens travel through one 34-layer sequence. The text encoder is **Qwen3-VL-8B-Instruct**, a full vision-language model (hidden states from 13 layers concatenated). It is a flow-matching model with **dual-branch (asymmetric) classifier-free guidance** — a separate unconditional transformer — and renders **native 2K** at any resolution 256–2048 px (multiples of 16, aspect ratios to 6:1).

Its defining trait: **it was trained *exclusively* on structured JSON captions.** Plain-text prompts work, but a JSON caption that follows the schema is how you unlock its real strengths — best-in-class text rendering, bounding-box layout, and hex color-palette control.

**This skill is about running the open weights** — the gated `nf4`/`fp8` model on your own GPU (or a rented cloud GPU) via **ComfyUI**, the diffusers **`Ideogram4Pipeline`**, or the **`run_inference.py`** CLI. That's the path with full control over every sampler knob, and the one the rest of this guide assumes.

**Know the licence split before you start** — it's the single most-misunderstood fact about this release (full detail in *Licence & limitations*):

- **Code** (GitHub): Apache-2.0. **Weights:** the **Ideogram 4 Non-Commercial Model Agreement**. **Outputs you generate:** yours.
- The open weights are **non-commercial wherever you run them** — your GPU, RunPod, any cloud. Renting hardware doesn't grant commercial rights; it's about *purpose*, not place.
- **For commercial work, route through Ideogram's hosted API or web app** (their Terms permit commercial use and assign you output ownership) — or obtain a separate paid weights licence. The hosted web app is also the *only* place the **Character Reference** (face identity) and **Style Reference** features exist — they're not in the open weights. API params, pricing, and web-app tools, if you need that path: `references/api-and-webapp.md`.

---

## The one rule that changes everything

**Write a structured JSON caption, not a prose paragraph or a tag list.** The model was trained only on JSON, so JSON minimises train/inference mismatch and is the reliable way to get every requested object, every line of text, and your exact layout. Plain text is a fallback that underperforms — and trips the safety filter more often (official).

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

**Don't want to write JSON?** That is exactly what **Magic Prompt** does: an LLM expands your plain-text idea into a full caption before generation. It is automatic in the web app, automatic for `text_prompt` on the API, and on by default in the repo's `run_inference.py`. Three backends ship with the package: `ideogram-4-v1` (Ideogram's free hosted API, needs `IDEOGRAM_API_KEY`), `claude-opus-v1`, and `claude-sonnet-v1` (via OpenRouter, need `MAGIC_PROMPT_API_KEY`). **There is no fully-offline Magic Prompt** — either it calls a hosted LLM, or you run the open-source system prompt through your own model (ComfyUI bundles an in-stack `gemma4` for this).

Full schema, the caption-craft rules, and worked examples: **`references/json-caption-guide.md`**.

---

## The JSON caption schema (canonical)

Three top-level fields, in this order. **Key order is strict** — the pipeline runs a `CaptionVerifier` that warns on wrong order, unknown keys, or missing required keys, and `run_inference.py` **aborts on those warnings by default** (`--warn-on-caption-issues` downgrades to warnings).

| Field | Required? | Holds |
|---|---|---|
| `high_level_description` | optional, strongly recommended | one or two sentences summarising the whole image |
| `style_description` | optional | the visual style block (see below) |
| `compositional_deconstruction` | **required** | `background` (string, required) + `elements` (list, required) |

**`style_description`** must contain **exactly one** of `photo` (photographic) or `art_style` (everything else), plus `aesthetics`, `lighting`, `medium`; `color_palette` is optional and **must be last**. Key order is fixed per type:

| Caption type | Required key order |
|---|---|
| Photo | `aesthetics`, `lighting`, `photo`, `medium`, `color_palette` |
| Non-photo | `aesthetics`, `lighting`, `medium`, `art_style`, `color_palette` |

**`elements`** are objects (`type:"obj"`) or text (`type:"text"`), each with a fixed key order. `bbox` and `color_palette` are optional but, if present, must sit in the position shown:

| Type | Key order |
|---|---|
| `"obj"` | `type`, `bbox`, `desc`, `color_palette` |
| `"text"` | `type`, `bbox`, `text`, `desc`, `color_palette` |

- **`bbox` = `[y_min, x_min, y_max, x_max]`**, normalised **0–1000 on both axes**, origin top-left. (Note: **y comes first** — easy to invert.)
- **`color_palette`** entries are uppercase `#RRGGBB` only (no shorthand). Up to **16** at style level, **5** per element.
- **`text`** (text elements only) is the literal string to render, verbatim.
- Serialize with `json.dumps(caption, separators=(",", ":"), ensure_ascii=False)` — keep non-ASCII (CJK, accents) literal; the verifier warns on `\uXXXX` escapes.

> **Two valid shapes, both official.** The schema above (with `style_description`) is best for hand-authoring — it gives explicit style + palette control. The shipped **Magic Prompt** produces a *prose-style* variant: it folds style into `high_level_description`/`background` text, omits `style_description`, and **strips bboxes by default**. Both pass the verifier (`style_description` is optional). Use the full schema when you want layout/palette control; let Magic Prompt handle casual prompts.

---

## Rendering speed, steps & guidance

Speed/quality is one axis with three named presets. On the self-hosted weights these are sampler presets; on the API they are `rendering_speed` tiers; in the web app they are credit tiers.

| Preset (self-hosted) | API `rendering_speed` | Steps | Guidance schedule | `mu` | `std` | API $/image¹ |
|---|---|---|---|---|---|---|
| `V4_QUALITY_48` *(default)* | `QUALITY` | 48 | 45 steps @ gw 7, then 3 polish @ gw 3 | 0.0 | 1.5 | $0.10 |
| `V4_DEFAULT_20` | `DEFAULT` *(API default)* | 20 | 18 @ gw 7, then 2 polish @ gw 3 | 0.0 | 1.75 | $0.06 |
| `V4_TURBO_12` | `TURBO` | 12 | 11 @ gw 7, then 1 polish @ gw 3 | 0.5 | 1.75 | $0.03 |

> ¹ API per-image prices from ideogram.ai/api-pricing. A `FLASH` API tier is announced but returns 400 ("coming soon"). The default constant `guidance_scale` is **7.0** when no schedule is given; presets supply the per-step schedule. Higher guidance = more prompt adherence, lower = more diversity.

**Resolution.** Default 1024×1024. Native range 256–2048, multiples of 16, aspect ratios to 6:1 / 1:6. For maximum quality pair **2048×2048 with `V4_QUALITY_48`**. The diffusers pipeline takes `height`/`width`; the API takes an explicit `resolution` string (e.g. `"2048x2048"`, `"2880x1440"`); the web app and the Magic Prompt endpoint take an `aspect_ratio` string (e.g. `"16x9"`).

Common resolutions: `1024×1024` (1:1) · `1536×1024` (3:2) · `1024×1536` (2:3) · `1920×1088` (~16:9) · `2048×768` (~21:9) · `1024×1792` (~9:16) · `1600×400` (4:1 banner).

---

## Caption craft — the high-leverage rules

These come straight from Ideogram's **open-source Magic Prompt system prompt** — i.e. how Ideogram itself instructs an LLM to write captions. They are the single best guide to what the model actually wants. Full detail in `references/json-caption-guide.md` §3.

- **One subject = one element.** A person, animal, car, or building is exactly one `obj`; anatomical/structural parts go in that element's `desc`, never as separate elements. Multiple *distinct* subjects (a person *and* a dog) = multiple elements.
- **`background` is the shell only.** Walls, floor/ground, sky, atmosphere, ambient light, distant blurred context. **The ground/floor/pavement is ALWAYS `background`** (including puddles, reflections, wet/cracked surface state) — *zero tolerance*. Furniture, vehicles, people, decor, free-standing lamps are **elements**, never background.
  - **Why it matters (a real failure mode):** emit the floor as an `obj` and the renderer treats it as a flat 2D band at the bottom of the frame and **buries the subject's legs in it**. Keep the floor in `background`.
- **No double-counting.** Every component lives in exactly one field. Before emitting an `obj`, scan `background` — if it's named there, drop the `obj`.
- **Shell-affixed hero objects → dual mention.** A chalkboard wall, built-in fireplace, mounted TV: (1) name it in `background`, (2) also emit it as an `obj` whose `desc` starts with "the primary background element", (3) place it **first** in `elements` (painter's algorithm draws it behind foreground items).
- **Commit to one value — no hedging.** Banned in element/background text: `things like`, `such as`, `various`, `or similar`, `e.g.`, `style of`, and alternative listings (`oak or walnut`, `bold or semibold`). Pick one and commit. Typography: one typeface category, one weight, one style.
- **Keep render-language out of `obj` descs.** Depth of field, bokeh, grain, motion blur, shadows belong in `high_level_description`/`background` (and only if asked) — not in element descs (the renderer infers shadows). Viewpoint/angle (`low-angle`, `bird's-eye`) *is* allowed in a desc.
- **Populate sparse scenes** by depth layer and commit to a *specific* place ("a pho stall outside Hoi An", not "a Southeast Asian village"). Built environments need text on every surface — `text: []` is almost always wrong for a shop/stall/market.

**Bounding boxes — the #1 failure.** `bbox` is normalised 0–1000 on **both** axes, so a "square" `[0,0,500,500]` is only square on a 1:1 frame; on 16:9 it becomes a wide rectangle, on 9:16 a tall one. **Most duplicate/extra-subject/mis-scale bugs come from this.** For round or on-screen-square regions, scale spans so `(x2−x1)/(y2−y1) ≈ W/H`. Give each subject a tight bbox so no one box dominates and invites a duplicate. Omit bboxes on dense/unenumerable content (crowds, fields, starfields).

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

Ideogram 4 leads open models on in-image text (official: 0.97 X-Omni English OCR). To use it well:

- **One text element per visually distinct block.** Use `\n` for line breaks *within* one block; use separate elements for separate blocks.
- **Stack stylised hero titles with `\n` at word breaks** — long single-line stylised titles produce typos and dropped letters (`"ENTRE\nVERSOS E\nCONTOS"`, not one line).
- **Numbers are text** — jersey numbers, prices, dates, addresses each go in a `text` element.
- **Multilingual:** English + CJK/Cyrillic/etc. render well; keep prose fields in English and put only the literal characters in `text`, stored as literal UTF-8 (`ensure_ascii=False`).
- **Editable text layers & native transparency** are first-class v4 features — the web app can "layerize" text and output transparent PNGs; for a cutout, set `background` to exactly `"transparent background"`.

---

## Setup & ecosystem

- **Web app / API:** nothing to install. API auth header is `Api-Key`; the core call is `POST /v1/ideogram-v4/generate` with `text_prompt` *or* `json_prompt`. Endpoints, params, pricing, and web-app editing tools: **`references/api-and-webapp.md`**.

**Pose control and face identity (open weights):** ControlNet, PuLID, and IP-Adapter face do not exist for Ideogram 4 — none have been released by Ideogram or any community team as of June 2026. The model's 34-layer single-stream DiT architecture is structurally incompatible with existing ControlNet or IP-Adapter implementations. For structural control on open weights, the only available mechanism is the **bounding-box `bbox` layout** inside the JSON caption (constrains *where* elements appear in the frame, not skeleton or depth input). **Character Reference** (face identity) and **Style Reference** are available in the **web app and v3 API only** — not the v4 API and not the open-weight release. Details: **`references/api-and-webapp.md` §6**.
- **Self-hosted open weights (gating):** gated on Hugging Face — accept the licence and authenticate (`hf auth login` / `HF_TOKEN`) or downloads 404. Two quants: **`nf4`** (bitsandbytes 4-bit, **CUDA-only**, diffusers-compatible, fits a 24 GB GPU) and **`fp8`** (weight-only float8, **any hardware**, activations stay bf16). diffusers exposes **`Ideogram4Pipeline`**; the repo ships a `run_inference.py` CLI. The diffusers/CLI quick start, sampler presets, and VRAM notes are in **`references/self-hosting.md`**.
  - **You don't need local hardware.** ComfyUI / diffusers / the CLI all run the same on a **rented cloud GPU** — RunPod, Vast.ai, etc. — which is the usual way to get a 24 GB+ (or H100) box for the larger quants and 2K renders. The non-commercial licence is unchanged by renting (it's about *purpose*, not place).

### ComfyUI (day-0 native support)

ComfyUI is a **runtime for the open weights**, not a "local-only" path — run it on your workstation *or* a cloud GPU pod identically. It added native support on launch day. Use the official template **`image_ideogram4_t2i.json`** (`Comfy-Org/workflow_templates`); the walkthrough is on `blog.comfy.org` / `docs.comfy.org/tutorials/image/ideogram/ideogram-v4`. **Requires an updated/nightly ComfyUI** — the loaders are brand-new and stable Desktop/Cloud builds may lag (on a RunPod template, pull the nightly). The details below are read verbatim from the template JSON.

**File layout** (download into these folders):

| File | ComfyUI folder | Role |
|---|---|---|
| `ideogram4_fp8_scaled.safetensors` | `models/diffusion_models/` | conditional model — `UNETLoader` |
| `ideogram4_unconditional_fp8_scaled.safetensors` | `models/diffusion_models/` | unconditional model — `UNETLoader` |
| `qwen3vl_8b_fp8_scaled.safetensors` | `models/text_encoders/` | text encoder — `CLIPLoader`, type **`ideogram4`** |
| `flux2-vae.safetensors` | `models/vae/` | VAE — download from `Comfy-Org/ideogram-4` on Hugging Face |
| `gemma4_e4b_it_fp8_scaled.safetensors` | `models/text_encoders/` | optional in-stack captioner LLM (separate `Comfy-Org/gemma-4` repo) |

**What's unusual:** **two diffusion models load** and combine through a **`DualModelGuider`** — this is the model's dual-branch (asymmetric) CFG (a conditional + a separate unconditional transformer), not a negative-prompt string. Stock template defaults: sampler **`euler`**, **`Ideogram4Scheduler`** at **20 steps** (the Default tier; a `CustomCombo` switches Quality 48 / Default 20 / Turbo 12), `DualModelGuider` guidance **7**, latent **1024×1024**.

**Two prompt modes:** (1) **natural language** — a plain sentence; (2) **structured JSON** — paste a JSON caption into the multiline `CLIPTextEncode` field (its default already holds one); downstream `JsonExtractString` nodes pull dimensions/fields out of it. JSON unlocks layout/text/palette control (see *The JSON caption schema* above).

> **`gemma4` gotcha:** it's on the required-download list but **no node in the shipped template loads it**. It's the recommended *in-stack* LLM (runs on your own GPU, vs the hosted `ideogram-4-v1` Magic Prompt) for the natural-language → JSON caption step — the template includes a string-assembly helper subgraph but no LLM-execution node, so you run that conversion yourself. Downloading it and finding nowhere to plug it in is the most common first-day confusion.

Full node table, VRAM reports, the `nf4`-vs-`nvfp4` file-naming caveat, and GGUF status: **`references/self-hosting.md` §4**.

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| Gray screen, "Image blocked by safety filter" | Model-level NSFW filter (in the weights, can't disable); fires more on plain text | Rephrase; **use a JSON caption** (lower false-positive rate, official); the team has acknowledged over-blocking and plans a checkpoint update |
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

## Licence & limitations

**The licence split (verify before any commercial use):**
- **Inference code** (GitHub `ideogram-oss/ideogram4`): **Apache-2.0**.
- **Model weights** (HF `ideogram-ai/ideogram-4-nf4` / `-fp8`): **Ideogram Non-Commercial Model Agreement** (dated 3 June 2026). Free for research, personal, hobby, charitable, and internal non-production use. "Non-Commercial Purposes" **explicitly excludes** generating output for, or to advertise, revenue-generating products, and excludes commercial fine-tuning/distillation. Weights are **gated** on Hugging Face. Redistribution must pass on the same terms, include the attribution notice, and mark modifications.
- **Outputs:** you own them — Ideogram claims no rights in your outputs (both the Non-Commercial Agreement and the web/API Terms). But generating those outputs *via the self-hosted weights* for commercial purposes is outside the grant — and that holds wherever you run them (your GPU, RunPod, any cloud). **For commercial work, use the web app or hosted API** (whose Terms assign output ownership to you and permit commercial use), or obtain a separate commercial weights licence from Ideogram.
- **Use restrictions** (weights): no military/surveillance, no biometric processing, no competing-model training from outputs, must not remove watermarking/safety measures, AI-disclosure where legally required.

**Safety filter.** Two layers: (1) a **model-level** NSFW filter that returns a gray "Image blocked by safety filter" screen — it is in the weights and false-positives are **higher for plain-text than JSON** prompts (official; a fix is planned); and (2) **optional external Hive** text+image moderation wired into the reference `run_inference.py` (you supply `HIVE_*` keys; it warns loudly if absent). The "open-weight ≠ open source" critique and the irony that the non-commercial licence restricts exactly the design/branding use-cases the model is best at are the main community grievances (verified on Hacker News).

**How to read the claims in this skill — two bars, by claim type.** Ideogram 4 is an **open-weights** model — gated `nf4`/`fp8` weights under a non-commercial licence, run via the diffusers `Ideogram4Pipeline` or ComfyUI. The hosted API/web app is a *side path*, relevant only for commercial use (the weights are NC) and for the web-only Character/Style Reference features. The two bars below are the same shape as the other open-model skills; the only real difference is **recency** — it's days old, so the community craft layer is still forming.

- **Hard facts — must be exact or it breaks.** Architecture and encoder, the 13 Qwen3-VL caption layers, the **JSON caption schema and `CaptionVerifier` rules**, the three sampler presets and their exact `mu`/`std`/guidance schedules, the Magic Prompt backends and system-prompt rules, quantisation (`nf4`/`fp8`) and HF gating, the licence terms, and the `Ideogram4Pipeline` / `run_inference.py` / ComfyUI node surface. **Source of truth is official** — the GitHub repo, model source, and licence. A wrong quant filename or sampler value breaks the run; a misread non-commercial licence is a legal problem. **Days-old and volatile:** quant filenames (the `nf4`-vs-`nvfp4` naming), VRAM numbers, ComfyUI template details, and LoRA tooling will move — re-verify before relying on them.

- **Craft — what actually makes a good image.** Almost entirely **JSON caption craft**: single-subject elements, background-as-shell, dual-mention, specificity, the `bbox` layout (painter's-algorithm ordering). The authoritative source here will be the **open-weights community** — the people self-hosting it in ComfyUI/diffusers — exactly as for SDXL or Z-Image. The one caveat is *recency, not closedness*: at days old the deep practitioner corpus hasn't accumulated yet, so today's craft leans on the official schema and examples plus early testing, and will sharpen as the community runs it. LoRA training is a working Ostris proof-of-concept; no production LoRA ecosystem exists **yet**.

**Independent positioning** (third-party evals): Ideogram 4 ranks #1 among open-weight models on DesignArena and #2 on a blind designer-preference eval (behind GPT Image 2) — strongest on text/typography/design, weakest on photoreal faces.

**Release:** 3 June 2026. This is a days-old model; the community is still learning it and Ideogram has signalled checkpoint updates (notably for the safety filter). Re-verify fast-moving specifics (pricing, quant files, ComfyUI template details, LoRA tooling) before relying on them.

---

## Reference files

| File | When to read it |
|---|---|
| `references/json-caption-guide.md` | The full JSON caption schema; the complete caption-craft ruleset (single-subject elements, background-as-shell, dual-mention, specificity, bbox strategy); text rendering & multilingual; color-palette conditioning; transparency; Magic Prompt; and drop-in templates |
| `references/self-hosting.md` | Self-hosted open-weight setup (your GPU or a cloud GPU like RunPod): diffusers `Ideogram4Pipeline`, the `run_inference.py` CLI, sampler presets, resolutions, nf4/fp8 quant + VRAM, HF gating, the ComfyUI day-0 node graph (files, folders, node names, settings, the `gemma4` in-stack captioner), GGUF status, and early LoRA/fine-tuning notes |
| `references/api-and-webapp.md` | **Secondary / commercial-routing path only** — read when commercial use (NC weights) or the web-only Character/Style Reference features force you off the open weights. The hosted API (generate / remix / describe / magic-prompt endpoints, params, `json_prompt` vs `text_prompt`, resolutions, pricing & rate limits), the web app (Magic Fill, reframe, upscale, transparency, editable text layers), and the commercial-use/ownership terms |
