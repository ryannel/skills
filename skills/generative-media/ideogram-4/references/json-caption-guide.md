# Ideogram 4 JSON Caption Guide

Ideogram 4 was trained **exclusively on structured JSON captions**. Plain text works, but it underperforms and trips the safety filter more often. This guide covers the full schema plus the caption-craft rules. Both come from Ideogram's own open-source Magic Prompt system prompt, which is the set of instructions Ideogram gives an LLM to write captions. That system prompt is the most authoritative prompting guidance available. The rules below are quoted or paraphrased from it, and from `docs/prompting.md` in the official repo.


**This file owns the caption itself**: schema, craft rules, layout, palette, templates. Running the
model (nodes, quants, CLI) is covered in `setup-and-workflows.md`. Captioning a *training* set is a
different and much less settled problem, and it is covered in `lora-training.md § 3`.

## Contents

- [1. The schema](#1-the-schema)
- [2. Plain text vs JSON vs Magic Prompt](#2-plain-text-vs-json-vs-magic-prompt)
- [3. Caption-craft rules](#3-caption-craft-rules-from-ideograms-magic-prompt-system-prompt)
- [4. Bounding-box strategy](#4-bounding-box-strategy)
- [5. Realism — the Ideogram way](#5-realism--the-ideogram-way)
- [6. Text rendering, typography & multilingual](#6-text-rendering-typography--multilingual)
- [7. Color-palette conditioning](#7-color-palette-conditioning)
- [8. Transparency / cutouts](#8-transparency--cutouts)
- [9. Drop-in templates](#9-drop-in-templates)

---

## 1. The schema

Three top-level fields, in this order:

1. `high_level_description` — optional string, **strongly recommended**.
2. `style_description` — optional object.
3. `compositional_deconstruction` — **required** object (must contain `background` then `elements`).

A `CaptionVerifier` runs on every prompt. It warns on unknown keys, missing required keys, out-of-order keys, malformed bbox, bad hex, and `\uXXXX` escapes with no literal non-ASCII. **`run_inference.py` aborts on warnings by default.** Pass `--warn-on-caption-issues` to continue anyway. The "required/must" language below describes what the verifier checks. The model itself still accepts any string; deviating just samples outside the training distribution.

### 1.1 `high_level_description`

One or two sentences summarising the whole image, with a 50-word cap in the Magic Prompt. It reads like a short natural-language prompt. Start with the subject, and skip openers like "this image shows / depicts / captures". Name recognised entities in full ("Nike Air Jordan 1", "Eiffel Tower"). General categories (`various`, `multiple`) are fine *here*. Granular detail belongs in the element descs.

```json
"high_level_description": "A medium-shot photograph of a barista pouring latte art in a cozy cafe."
```

### 1.2 `style_description`

This controls style, lighting, medium, and palette. It must contain **exactly one** of `photo` (photographic) or `art_style` (non-photographic). `aesthetics`, `lighting`, and `medium` are required when the block is present. `color_palette` is optional and must come **last**.

| Caption type | Required key order |
|---|---|
| Photo (uses `photo`) | `aesthetics`, `lighting`, `photo`, `medium`, `color_palette` |
| Non-photo (uses `art_style`) | `aesthetics`, `lighting`, `medium`, `art_style`, `color_palette` |

| Field | Type | Description |
|---|---|---|
| `aesthetics` | string | aesthetic keywords ("moody, cinematic, desaturated") |
| `lighting` | string | "golden hour, rim light, dramatic shadows" |
| `photo` | string | camera/lens details for photographic outputs ("35mm, f/1.4, bokeh") — use this OR `art_style` |
| `medium` | string | `"photograph"`, `"illustration"`, `"3d_render"`, `"painting"`, `"graphic_design"`, etc. |
| `art_style` | string | art-style description for non-photo ("flat vector illustration, bold outlines") — use this OR `photo` |
| `color_palette` | list[str] | up to 16 uppercase `#RRGGBB` hex codes |

> See the realism caveat in §5. For photographic captions, the official Magic Prompt actually *folds style into prose and drops `style_description`*, and it avoids stacking DSLR camera terms. Use `style_description` when you want explicit, repeatable style and palette control. For casual photoreal work, lean on prose instead.

### 1.3 `compositional_deconstruction`

This handles fine-grained layout. `background` (string) **must come before** `elements` (list). Both are required.

Each element is one of:

```json
{"type":"obj","bbox":[y1,x1,y2,x2],"desc":"..."}
{"type":"text","bbox":[y1,x1,y2,x2],"text":"LINE ONE\nLINE TWO","desc":"..."}
```

Fixed key order per type (`bbox`, `color_palette` optional but positioned):

| Type | Key order |
|---|---|
| `"obj"` | `type`, `bbox`, `desc`, `color_palette` |
| `"text"` | `type`, `bbox`, `text`, `desc`, `color_palette` |

| Field | Type | Notes |
|---|---|---|
| `type` | string | `"obj"` or `"text"` |
| `bbox` | list[int] | `[y_min, x_min, y_max, x_max]`, **0–1000 both axes**, origin top-left, `y` first. Optional. |
| `desc` | string | detailed element description (30–60 words; standalone, identity-first) |
| `text` | string | (text only) the literal characters to render |
| `color_palette` | list[str] | optional per-element palette, up to 5 uppercase `#RRGGBB` |

### 1.4 Encoding

Serialize with `json.dumps(caption, separators=(",", ":"), ensure_ascii=False)`. Keep non-ASCII characters literal: CJK, Cyrillic, accented Latin. The verifier warns when it sees `\uXXXX` escapes with no literal non-ASCII, which usually means someone left `ensure_ascii=True`. Hex colors must be uppercase `#RRGGBB`. Never write `#fff` and never use lowercase.

---

## 2. Plain text vs JSON vs Magic Prompt

| Path | How | When |
|---|---|---|
| **Plain text** | pass a sentence as the prompt | casual single-subject images; quick drafts. Underperforms on layout/text/palette and trips the safety filter more |
| **Magic Prompt** | LLM expands plain text → JSON before generation | the easy path to JSON quality. Auto in the web app and for API `text_prompt`; on by default in `run_inference.py` |
| **Hand-authored JSON** | write the caption yourself (or expand, then hand-tune) | maximum control: exact layout (bbox), typography, brand colors, every object guaranteed |

**Magic Prompt backends (local):**

| Registry key | Backend | Key env var |
|---|---|---|
| `ideogram-4-v1` *(default)* | Ideogram's free hosted API (`POST api.ideogram.ai/v1/ideogram-v4/magic-prompt`, returns `{aspect_ratio, json_prompt}`) | `IDEOGRAM_API_KEY` |
| `claude-opus-v1` | Claude Opus 4.8 via OpenRouter, using the open-source system prompt | `MAGIC_PROMPT_API_KEY` |
| `claude-sonnet-v1` | Claude Sonnet 4.6 via OpenRouter | `MAGIC_PROMPT_API_KEY` |

There is **no fully-offline Magic Prompt**: `ideogram-4-v1` and the `claude-*` backends both call a hosted LLM. For an offline pipeline, either hand-write JSON or run the shipped open-source system prompt (`src/ideogram4/magic_prompt_system_prompts/v1.txt`) through your own local LLM. ComfyUI bundles a local `gemma4` for exactly this purpose. The shipped Magic Prompt also **strips bboxes by default** (`strip_bboxes=True`) and removes the `aspect_ratio` field before generation. So the easy path does *not* give you bbox layout control; that is a hand-authoring feature.

---

## 3. Caption-craft rules (from Ideogram's Magic Prompt system prompt)

These are the rules that separate a mediocre caption from one that renders cleanly. They are Ideogram's own rules. Follow them whether you hand-write the JSON or prompt an LLM to write it.

### 3.1 One subject = one element

A coherent subject (one animal, person, vehicle, building, plant, instrument, or machine) is **exactly one `obj`**. Anatomical and structural parts are attributes inside that element's `desc`. They are not separate elements.

- **Forbidden:** a bee split into thorax/abdomen/wings/legs; a car into body/wheels/windshield; a person into head/torso/each-limb.
- **Multiple distinct subjects** (a person *and* a dog; two bees; three runners) → one element each.
- **Transparent enclosure + contents = one element** (snow globe, terrarium, display case).
- **Configured part + revealed interior = one element** (car with open door, machine with raised hood).

The test: if something is part of one thing, it goes in that thing's `desc`. If it is a separate thing, it gets its own element.

### 3.2 Element `desc` — what to write (30–60 words)

Write identity first, then the major attributes briefly, then one distinguishing detail. Each `desc` is a standalone catalog entry. Open with the subject's identity rather than "the X", because that phrasing assumes the reader already saw the scene.

**Always name:** people → skin tone, hair (color + style), each garment with color, expression/gaze, pose, one distinguishing feature; objects → shape, material, color, distinctive parts; structures → type, primary material, color, distinctive elements.

**Skip (wastes budget):** per-limb pose mechanics (give one summary action phrase), surface-finish micro-prose (one word: matte/glossy/metallic, or omit), fabric weave / skin-texture nuance, camera/shadow/lighting micro-detail.

**Never in an `obj` desc:**
- **Shadows.** This covers cast, drop, and contact shadows, plus ambient occlusion. The renderer infers these on its own. Describe scene-wide light in `background` only.
- **Camera / render language.** This covers depth of field, focus, bokeh, exposure, motion blur, lens flare, and grain. Put these in `high_level_description` or `background`, and only if the user asked for them. There is one exception: viewpoint and angle (`low-angle`, `bird's-eye`, `eye-level`) are allowed in a desc.
- **Impression words** used instead of physical reality, such as `luminous`, `radiant`, `vibrant`, `gorgeous`, `stunning`. Use observable properties instead ("cheekbone catches a small highlight", not "luminous complexion").
- **Scene-context repetition.** Describe lighting direction, ambient surface, and weather once in `background`, not per element.

**Anchor placements to named references.** Write "applied to the forehead near the hairline above the left eyebrow", not "pressed against the skin". Write "resting on the lower-right corner of the table in front of the laptop", not "sitting on the surface".

### 3.3 `background` is the shell only (critical)

`background` is the scene shell. The shell means walls and finishes, the floor or ground and its surface state, the ceiling and its fixtures, windows-as-architecture, atmosphere (sky, clouds, fog, dust), scene-wide ambient light, and distant out-of-focus context (horizon, blurred crowds).

**Always-background — never an `obj` element:** sky, clouds, horizon, distant mountains/tree-lines, weather (fog/haze/mist/smoke), distant cityscape/stadium, distant blurred crowds, the floor/ground/turf/pavement the scene sits on, and ambient walls or studio backdrop. You cannot split these by region: "sky upper-left" and "sky behind the fortress" are the same component.

**Ground, floor, and pavement are always background, with zero tolerance.** This covers floor, ground, turf, dirt, sand, asphalt, sidewalk, deck, water surface, snow, tile, hardwood, and marble. This holds even if the input lists "wet pavement below" as a foreground bullet; re-classify it. Surface *state* (wet, rain-slicked, cracked, polished, muddy) is part of the ground surface, and so are **puddles, reflections, and wet patches**. They are never separate elements, even when a puddle reflects the hero.

> **The failure this prevents:** suppose a standing hero is the focal element, and the floor is *also* emitted as an `obj` at the bottom of the frame. The renderer then treats that floor obj as a flat 2D band rather than a receding plane, and it **clips the hero's legs into it**. The figure renders half-buried, with feet and calves gone.

**But discrete objects *on* the floor are still elements:** broken glass, crushed cans, scattered debris, dropped tools, leaves. The rule is about the *surface*, not about solid objects resting on it.

**The background is the shell, so it holds no individually-placeable things.** Furniture, vehicles, equipment, people, animals, decor (artwork, signs, potted plants, book stacks), and free-standing lamps are `obj` elements, never background. Don't smuggle furniture in as "rows of desks recede toward the back" or "cars parked along the street". That arrangement *is* foreground content, so emit elements for it.

**No double-counting.** Each component lives in exactly one field. Before emitting an `obj`, scan `background` first. If the component is already named there, drop the `obj`.

**No medium or post-processing in `background`.** This covers film grain, lens flare, vignette, paper or canvas texture, halftone, and brushstroke texture. These describe *how the image was made*, not *what is in the scene*. Route them to `high_level_description`.

The test: read `background` aloud. If you can picture the **empty room**, with no furniture, no people, and no decor, you are describing the shell. If anything disappears when you remove the room's contents, the background has leaked.

### 3.4 Shell-affixed hero objects → dual mention

Some objects are simultaneously part of the shell *and* a focal element that defines the room. Examples: a chalkboard covering the back wall, a built-in fireplace, a large mounted TV, a stage proscenium, a built-in bookshelf, a fixed reception desk, a fixed banner. For these, do **all three** of the following:

1. **Mention in `background`** as part of the shell (anchors it to the wall).
2. **Emit as an `obj`** whose `desc` starts with "the primary background element" (it carries the detail — material, content, frame, mounting).
3. **Place it first in `elements`** so painter's-algorithm draws it behind foreground items.

Skipping step 1 floats the object in mid-room, or draws it in front of foreground subjects. This exception is only for objects that genuinely define the room's identity. Free-standing items (chairs, table lamps, framed pictures) get the normal treatment: elements only.

### 3.5 Specificity — commit to one value

This JSON feeds a diffusion model, so leave nothing for it to invent.

- **Banned hedges:** `things like`, `such as`, `e.g.`, `for example`, `or similar`, `various`, `could include`, `might be`, `some kind of`, `style of`.
- **Banned alternative listings for one property:** `pale off-white or pale green`, `oak or walnut`, `cream or ivory`, `bold or semibold`. Pick one. (`or` is reserved for exclusive-choice rendered text like `'YES' or 'NO'`.)
- **Typography:** one typeface category (serif / sans-serif / display / script / monospace), one weight, one style (italic or upright) — never two joined by `or`.
- **Banned "implied/suggested" hedges:** `a chair suggested beneath the figure`, `a building hinted at`, `barely visible`, `possibly`. If it's in the scene, paint it concretely. If not, leave it out.
- **Every named visual unit must appear as its own element.** That means every quoted string, every speech bubble (a text element for the words plus an obj for the balloon), every named badge/icon/CTA, and every item in an enumerable set (stones 1–50, a 22-name roster). No `etc.`, no grouping. The "dense unenumerable group" exception for crowds, wildflower fields, and starfields does *not* apply to enumerable sets.
- **Don't invent concepts the user didn't ask for.** No `glitch art`, `wireframe overlay`, or `digital artifacts` unless requested.

### 3.6 Populate sparse scenes

When the brief is sparse, populate the scene the way a real one would be. Add believable secondary subjects and micro-props by **depth layer**; a foreground crop (an out-of-focus leaf, a bowl rim) separates a photo from a postcard. **Commit to a specific cultural or regional identity**: write "a Vietnamese pho stall by the rice paddies outside Hoi An", not "a Southeast Asian village". **Built environments need text everywhere**: shop signs, sub-signs, menu boards, price labels, jar labels, posters. `text: []` is almost always wrong for a shop, stall, market, or vehicle. **Override this and stay sparse** when the brief says `minimal`, `empty`, `lonely`, `negative space`, `single subject`, or similar. Fantastical and sci-fi briefs get a populate bonus: sky drama, scale anchors, exotic architecture.

---

## 4. Bounding-box strategy

**Coordinates:** `[y_min, x_min, y_max, x_max]`, normalised **0–1000 in both axes**, origin top-left, `y1 < y2`, `x1 < x2`. `y` comes first.

**Include bboxes** where precise placement matters: portrait subjects, products on a surface, logos, signs, distinct placeable objects. **Omit bboxes** for dense or hard-to-enumerate visuals: crowds, wildflower fields, scattered particles, starry skies.

**The #1 bbox failure is square-on-non-square.** Because both axes run 0–1000, `[0,0,500,500]` is square *only* on a 1:1 frame. On 16:9 it is a wide rectangle; on 9:16 it is a tall one. Most bbox bugs (extra subjects, duplicates, mis-scaled objects) come from this mismatch.

- For round objects or on-screen-square regions, scale spans so `(x2−x1)/(y2−y1) ≈ W/H`.
- On wide frames with a single subject, prefer a narrower x-span.
- For multi-subject prompts, give each a tight box so no one box dominates and invites a duplicate.

Pick the aspect ratio *first*, because it drives every bbox decision.

---

## 5. Realism — the Ideogram way

These are the **defaults the shipped caption-expander injects for *underspecified* photographic prompts**, meaning cases where the medium is photo/photorealistic/selfie/real-world and nothing more is specified. They are the expander's taste, not model prohibitions. If you deliberately want a warm golden-hour or cinematic DSLR look, **specify it concretely and you'll get it.** When you *haven't* asked for a specific look, these defaults avoid the most common "AI look" tells:

- **Avoid "warm" as a bare grading adjective.** `warm light`, `warm tone`, and `warm grading` tend to trigger the amber/golden AI look. If a source is physically warm (a candle, a sodium lamp, a sunset), name the **source** and the **light-pool color** ("amber pool from the candle") instead of grading the whole image "warm".
- **Default to the iPhone aesthetic:** phone snapshot, ambient natural or overcast daylight, **cool-neutral white balance**, accurate (not flattering) skin tones, ordinary framing. DSLR-magazine markers such as creamy bokeh, telephoto compression, dramatic rim light, and a cinematic grade read as AI when they are *unrequested*.
- **No motion blur** in candid, realistic, or iPhone shots. Real phone snaps freeze the moment.
- **Saturation once.** Don't stack `vibrant + bright + intense + saturated + neon` for a neutral subject.
- **"Professional photo of a person"** means professional *context* (corporate headshot, neutral attire, soft even daylight, friendly expression), **not** professional camera gear.
- **Off-center / rule-of-thirds composition by default.** Centre the subject only when asked, or for inherently symmetric genres.

> **These aesthetic defaults come from Ideogram's open-source expander system prompt, which Ideogram says differs from its production Magic Prompt.** Treat them as informed taste rather than hard rules. The structural schema rules in §1–§4, by contrast, are model facts. Naming a real camera body and film stock in Ideogram prompts is counterproductive, because the expander treats unrequested camera-stacking as an AI tell, not a realism signal. Photoreal faces and skin are Ideogram 4's relative weak spot. For portrait photorealism, consider a model purpose-built for that. Reach for Ideogram 4 instead when text, typography, layout, or design are central.

---

## 6. Text rendering, typography & multilingual

Text rendering is Ideogram 4's headline strength: 0.97 X-Omni English in-image OCR `[official — Ideogram 4 model card]`.

- **Sources of text to include:** user-quoted strings (verbatim), format-required copy (headlines, taglines, dates, CTAs, brand names), in-scene text (signage, labels, jersey numbers, license plates, t-shirt prints), numeric content (prices, scores, addresses; **numbers are text**), and prominent product brand text.
- **One text element per visually distinct block.** Each text string appears **once** in the list. Don't also spell it out in a `desc`; refer to it there by role or position instead.
- **Use `\n` for line breaks within one block.** For stylised hero typography, **stack with `\n` at natural word breaks**, because long single-line stylised titles produce typos and dropped letters (`"ENTRE\nVERSOS E\nCONTOS"`, not `"ENTRE VERSOS E CONTOS"`).
- **Multilingual:** keep the prose, `desc`, and position fields in **English** regardless of the brief's language. Only the literal `text` field carries the target-language characters. Store them as literal UTF-8 (`ensure_ascii=False`).
- **Exhaustive:** if a viewer could read it, it goes in the list. Every itinerary, menu, or roster item gets its own element.

---

## 7. Color-palette conditioning

Steer dominant colors with hex codes.

- **`style_description.color_palette`** holds up to **16** colors for the overall image.
- **`elements[*].color_palette`** holds up to **5** colors per element, to steer that element specifically.
- **Uppercase `#RRGGBB` only.** No shorthand (`#fff`), no lowercase.
- **Include background colors** in the palette if you want a specific backdrop (e.g. a dark hex for a dark background).
- **Include contrast pairs** (highlight + shadow) for more controlled lighting.

```json
"style_description": {
  "aesthetics": "moody, cinematic",
  "lighting": "low-key, deep shadows",
  "photo": "35mm, f/1.4",
  "medium": "photograph",
  "color_palette": ["#1B1B2F", "#162447", "#1F4068", "#E43F5A", "#F5F5F5"]
}
```

---

## 8. Transparency / cutouts

Native transparency is a first-class v4 feature; the web app can output transparent PNGs and "layerize" text. To request a cutout in a caption, set `background` to **exactly** the string `"transparent background"` (don't paraphrase it). Also include the phrase `on a transparent background` in `high_level_description`.

---

## 9. Drop-in templates

### A. Photographic portrait (full schema)
```json
{
  "high_level_description": "An eye-level photograph of a 32-year-old woman with shoulder-length copper hair standing against a plain concrete wall.",
  "style_description": {
    "aesthetics": "natural, candid, understated",
    "lighting": "overcast daylight, soft even fill, cool-neutral white balance",
    "photo": "phone snapshot, eye-level, ordinary framing",
    "medium": "photograph"
  },
  "compositional_deconstruction": {
    "background": "A plain warm-grey concrete wall under flat overcast daylight, slightly off-center behind the subject.",
    "elements": [
      {"type": "obj", "bbox": [120, 300, 980, 760], "desc": "A 32-year-old woman with shoulder-length copper hair, sun-freckled olive skin and a small mole below the left jaw, calm relaxed expression, wearing a grey crew-neck sweater. Positioned slightly right of center, facing the camera."}
    ]
  }
}
```

### B. Poster with hero typography (graphic design)
```json
{
  "high_level_description": "A bold concert poster for a jazz night with large stacked typography and a saxophone silhouette.",
  "style_description": {
    "aesthetics": "high-contrast, vintage, geometric",
    "lighting": "flat even studio lighting",
    "medium": "graphic_design",
    "art_style": "flat vector design, bold sans-serif typography, generous whitespace",
    "color_palette": ["#0D0D0D", "#E8C547", "#C0392B", "#F5F5F5"]
  },
  "compositional_deconstruction": {
    "background": "A solid near-black poster surface with subtle paper grain.",
    "elements": [
      {"type": "obj", "bbox": [250, 120, 720, 520], "desc": "A golden saxophone in clean flat-vector silhouette, angled diagonally across the upper-left.", "color_palette": ["#E8C547"]},
      {"type": "text", "bbox": [60, 80, 240, 940], "text": "JAZZ\nNIGHT", "desc": "Large bold sans-serif title stacked on two lines across the top third, bright yellow on black."},
      {"type": "text", "bbox": [820, 120, 900, 880], "text": "FRIDAY 9PM · BLUE ROOM", "desc": "Small red sans-serif detail line near the bottom."}
    ]
  }
}
```

### C. Bilingual signage scene
```json
{
  "high_level_description": "A photograph of a small ramen stall on a narrow Shibuya back-alley at midnight, viewed from across the street.",
  "style_description": {
    "aesthetics": "candid, atmospheric, neutral grade",
    "lighting": "available neon and warm interior light from the stall, cool-neutral grade overall, wet pavement reflecting color",
    "photo": "eye-level, ordinary framing",
    "medium": "photograph"
  },
  "compositional_deconstruction": {
    "background": "A narrow rain-slicked Shibuya alley at midnight, dark shopfronts receding, wet asphalt reflecting neon, faint mist.",
    "elements": [
      {"type": "obj", "bbox": [300, 180, 820, 760], "desc": "A small open ramen stall with a red noren curtain and a warmly lit counter, one customer hunched over a bowl with their back to the camera."},
      {"type": "text", "bbox": [320, 240, 410, 520], "text": "夜市", "desc": "Bold white brush-calligraphy on the red noren curtain over the stall entrance."},
      {"type": "text", "bbox": [430, 560, 500, 700], "text": "OPEN", "desc": "Small pink cursive neon sign in the stall window."}
    ]
  }
}
```

### D. Transparent sticker / cutout
```json
{
  "high_level_description": "A die-cut sticker of a ginger cat wearing a tiny wizard hat, on a transparent background.",
  "style_description": {
    "aesthetics": "cute, clean, bold outlines",
    "lighting": "even flat lighting",
    "medium": "illustration",
    "art_style": "flat sticker illustration with a thick white die-cut border"
  },
  "compositional_deconstruction": {
    "background": "transparent background",
    "elements": [
      {"type": "obj", "bbox": [120, 200, 900, 820], "desc": "A ginger tabby cat sitting upright, wearing a small blue conical wizard hat with yellow stars, friendly expression, thick white sticker outline around the whole figure."}
    ]
  }
}
```
