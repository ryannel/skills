# FLUX.2 — Prompting Guide

Source tier: BFL official prompting guide (primary), BFL blog, HF blog (official-via-docs), fal.ai prompting guide and community consensus (community).

---

## Contents

1. [Anatomy of a FLUX.2 prompt](#1-anatomy)
2. [What the encoder actually parses](#2-encoder)
3. [Hex color control](#3-hex-color)
4. [JSON for production (optional, not required)](#4-json)
5. [Realism vocabulary: camera, lens, film stock](#5-realism)
6. [Multi-reference image editing](#6-references)
7. [Text-in-image guidance](#7-text)
8. [Drop-in prompt templates](#8-templates)
9. [Common mistakes and corrections](#9-mistakes)

---

## 1. Anatomy

**The official BFL four-part structure** (from `docs.bfl.ml/guides/prompting_guide_flux2`):

```
[Subject] [Action/Setting] [Style] [Context]
```

| Part | What goes here | Example |
|---|---|---|
| **Subject** | Who or what. Specific, concrete. Avoid generics like "person" or "scene". | `"A woman in her early 30s with silver-grey cropped hair and faint freckles"` |
| **Action / Setting** | What the subject is doing, and/or where. Environmental specifics count here. | `"sits at a rain-wet counter in a narrow Kyoto kissaten, hands around a ceramic cup"` |
| **Style** | Photographic spec, artistic medium, or aesthetic genre. Camera gear lives here. | `"Hasselblad X2D, 55mm f/2.8, Fujifilm Pro 400H emulation, overcast afternoon diffuse"` |
| **Context** | Secondary elements, background details, atmosphere, secondary figures. | `"rain-blurred street visible through the window, steam rising from the coffee"` |

**Length sweet spots:**

| Use case | Recommended length |
|---|---|
| Concept sketch / iteration | 10–30 words |
| Standard generation | 30–80 words |
| Multi-element scene | 50–100 words |
| Multi-reference / structured JSON | Any length, but count subjects |
| Hard cap | 512 tokens (~380 words) |

Front-load subject and key elements — Mistral 3.2 and Qwen3 weight earlier tokens more heavily in their attention mechanism.

---

## 2. What the encoder actually parses

[dev] uses **Mistral Small 3.2 24B** (a 24-billion-parameter vision-language model). [klein] uses **Qwen3** (4B for [klein] 4B, 8B for [klein] 9B). Both are instruction-following LLMs — the same model family used for code generation and text summarisation.

**What they read well:**
- Grammatical clause structure (`"a woman who is holding"` > `"woman holding"`)
- Compositional prepositions and spatial language (`"in front of"`, `"partially hidden behind"`)
- Proper nouns for brands, places, films, periods (`"Kodak Portra 400"`, `"1970s Tokyo"`, `"Bauhaus-era poster"`)
- Colour descriptions in natural language (`"deep indigo"`, `"burnt-sienna matte"`)
- Specific names for known cultural artefacts (`"a Leica M-A body"`, `"Rolleiflex twin-lens"`)
- Hex color codes when signalled correctly (see section 3)

**What they parse as noise:**
- Quality-adjective chains: `masterpiece`, `8k`, `best quality`, `ultra-realistic`, `highly detailed`, `photorealistic`, `trending on artstation` — these are Stable Diffusion 1.5 booru tags with near-zero semantic content for an LLM-class encoder
- Leading comma-separated tokens with no predicate: `woman, hair, eyes, blue, rain, city, night` — describes noun fields, not a scene
- Parenthetical emphasis tokens: `(masterpiece:1.2)`, `((eyes))` — AUTOMATIC1111 syntax, meaningless here
- Negative prompts — there is no CFG path in [dev] and no active guidance in [klein] distilled (see section 9)

---

## 3. Hex color control

FLUX.2 introduced explicit hex-color conditioning, absent from Flux.1. The mechanism requires a keyword trigger before the hex code so the encoder routes it to the color-conditioning pathway.

**Format: `"...in color #XXXXXX"` or `"...in hex #XXXXXX"`**

| Correct | Incorrect |
|---|---|
| `"An apple in color #0047AB"` | `"An apple #0047AB"` |
| `"Logo text 'ACME' in color #FF5733"` | `"bright red #FF5733 logo"` |
| `"Background in hex #1A1A2E, foreground in color #E94560"` | `"#1A1A2E background with #E94560 text"` |

Multiple hex codes work in one prompt. Each needs its own `"in color"` or `"in hex"` signal.

**Use cases:**
- Brand colour consistency across a campaign: define a `color_palette` array in the JSON format (section 4) and reference elements with hex codes inline
- Logo and type-on-image generation: pair hex color conditioning with the JSON `subjects` format and wrap text in quotes
- Replicating a film still's specific colour grading: hex-code the primary midtone and shadow colour

---

## 4. JSON for production (optional, not required)

FLUX.2 was trained on natural language. JSON is a workflow tool for situations where:
- You need multi-subject scenes with explicit positional control
- You want machine-readable, version-controllable prompts in an API pipeline
- You need strict colour consistency across a batch

**Official BFL schema:**

```json
{
  "scene": "brief one-sentence description of the overall scene",
  "subjects": [
    {
      "description": "detailed description of this subject",
      "position": "where in the frame: center / left / right / foreground / background / lower-left / etc."
    }
  ],
  "style": "photographic specification or artistic style",
  "color_palette": ["#hex1", "#hex2", "#hex3"],
  "lighting": "light source, direction, quality, colour temperature",
  "camera": {
    "angle": "eye level / bird's eye / low angle / dutch / ...",
    "lens": "focal length and aperture: e.g. 85mm f/1.4"
  }
}
```

**Rules:**
- Each distinct subject needs its own entry in `subjects[]`
- `position` is a freeform string — the model reads it semantically, not as pixel coordinates
- `color_palette` hex codes compose with inline `"in color #XXXXXX"` syntax
- The JSON can be sent directly as the prompt string in ComfyUI or the API — no special wrapper

**When to use JSON vs natural language:**

| Situation | Best format |
|---|---|
| Single subject, photoreal | Natural language sentence |
| Quick concept iteration | Short natural language |
| Multi-subject compositional scene | JSON with `subjects[]` + `position` |
| Brand asset pipeline (batch) | JSON with `color_palette` |
| Text-heavy layout with specific placement | JSON, each text block as a subject |

---

## 5. Realism vocabulary: camera, lens, film stock

FLUX.2's default tendency (especially [klein]) is over-processed sharpness. Camera vocabulary works because Mistral/Qwen3 have strong priors on what images these setups produce — they're not just keywords, they're world-model activations.

### Camera bodies (photoreal signal strength: high)

| Camera | Typical use / signal |
|---|---|
| Hasselblad X2D | Medium-format, rich tonal range, ultra-fine detail, studio/landscape |
| Leica M-A / M11 | Street, reportage, subtle grain, clinical sharpness |
| Sony A7R V | Editorial, fashion, fine skin gradation |
| Canon EOS R5 / R3 | News, sports, editorial, full-frame authority |
| Nikon Z9 | Documentary, photojournalism |
| Fujifilm GFX 100S | Medium-format landscape, fashion |
| Ricoh GR IIIx | Street, 40mm equivalent, compact, film-noir undertone |
| Mamiya RB67 | Vintage medium-format, square format, smooth bokeh |

### Lenses (signal: aperture controls background separation)

| Spec | What it reads as |
|---|---|
| 85mm f/1.4 | Portrait classic, creamy background separation |
| 35mm f/1.8 | Environmental, slight context, still background-separated |
| 50mm f/2 | "Normal" field of view, documentary |
| 80mm f/2.8 | Medium-format standard, studio quality |
| 135mm f/2 | Compressed background, telephoto compression |
| 24mm f/2.8 | Wide environmental portrait, architecture |

### Film stocks (signal: tonal and colour character)

| Stock | Character |
|---|---|
| Kodak Portra 400 | Warm skin tones, creamy shadows, fine grain, best for people |
| Kodak Ektar 100 | Vivid saturated colours, fine grain, best for landscapes/objects |
| Fujifilm Pro 400H | Cool midtones, subtle blues, even skin, editorial |
| Fujifilm Velvia 50 | High saturation, punchy, landscape slide film |
| Ilford HP5 | B&W, medium contrast, versatile, reportage |
| Kodak Tri-X 400 | B&W, gritty grain, street photography |
| CineStill 800T | Cinematic halation, tungsten colour shift, night scenes |

### Lighting vocabulary

| Term | Effect |
|---|---|
| "available light" / "window light" | Natural, uncontrolled, believable |
| "overcast diffuse" | Even lighting, no harsh shadows, editorial |
| "golden hour back-light" | Warm rim light, slightly flared, lifestyle |
| "mixed tungsten and fluorescent" | Colour-cast authenticity, interior environment |
| "harsh midday sun" | High contrast, deep shadows, documentary |
| "practical lights only" | Sources visible in frame, moody, cinematic |
| "softbox / octabox" | Studio, even skin, fashion |

### Breaking the "over-AI'd" look

Add one or two:
- One non-idealised human feature: "slight under-eye shadow", "visible pores on cheeks", "fine hairline scar above left eyebrow"
- Environment imperfections: "dust on the window", "slightly chipped enamel mug", "worn leather shoulder bag"
- Motion / life: "exhaled breath visible in cold air", "hair caught by a gust", "jacket wrinkled from the bus ride"

Do **not** add: `"realistic"`, `"ultra-realistic"`, `"photorealistic"`, `"8K"`, `"high quality"` — these are zero-signal booru tokens.

---

## 6. Multi-reference image editing

FLUX.2 [dev] and [klein] 9B KV support **reference-based image editing** — provide one or more reference images and the model integrates them into the generated composition. This capability uses `ReferenceLatent` nodes in ComfyUI (this is a FLUX.2-native node, not the older IPAdapter approach).

**Supported reference count:** marketing documentation states up to 10; the official prompting guide states up to 8. Both 4B and 9B documentation mention approximately 4 in some configurations. Use the lower bounds as safe targets until you verify your specific variant's model card.

**Suggested supported counts by variant (verify at time of use):**
- [dev]: up to ~8–10 reference images
- [klein] 9B: up to ~8 (9B KV adds KV-caching to speed repeated reference processing)
- [klein] 4B: up to ~4 (marketing may overstate this for 4B specifically)

### ComfyUI reference workflow (dev image-edit template)

The `image_flux2_image_editing.json` template introduces:
- `ReferenceLatent` node: takes a reference image + optional mask, outputs a latent reference
- Multiple `ReferenceLatent` nodes chain into the conditioning
- Reference images encode separately from the main latent (hence KV-cache speedup in 9B KV)

Full image-edit template notes and node graph: **`setup-and-workflows.md`**.

### Prompting for multi-reference

When using reference images, describe the reference's role explicitly:
- `"[Subject from reference 1] wearing the jacket shown in reference 2, standing in front of the building from reference 3"`
- The model reads semantic labels in the prompt and maps them to provided reference images in order
- Positional language (`"first reference"`, `"the jacket image"`) helps disambiguation

---

## 7. Text-in-image guidance

FLUX.2 improved text rendering significantly over Flux.1. Suitable for: short text overlays (1–5 words), typographic accents, decorative scripts, sign text in scenes. Not suitable for: multi-line body copy, dense typographic layouts, logos with complex internal geometry.

**Rules that improve success:**
1. Wrap the exact text in `'single quotes'` or `"double quotes"` in the prompt: `"A shop sign reading 'CLOSED'"`
2. Keep each text block to ≤10 words; shorter is more reliable
3. Specify typography style: `"hand-lettered in white chalk"`, `"serif metal engraving"`, `"neon tube lettering in color #FF3300"`
4. Use JSON `subjects` to position text blocks precisely:
   ```json
   {"description": "Sign reading 'WELCOME' in brushed copper lettering", "position": "upper-center on the door frame"}
   ```
5. Combine hex color control for text colour: `"Sign text 'ACME' in color #FF5733"`
6. Generate 3–5 candidates and select — text rendering has higher variance than scene composition

For anything heavier (labels on product packaging, business cards, poster layouts, UI mockups): FLUX.2 text rendering is not reliable for dense multi-line copy or layout-driven design — use a model purpose-built for typography.

---

## 8. Drop-in prompt templates

### Portrait — photoreal

```
A [age + specific descriptor] [subject noun] [specific action] in [specific environment]. 
[Camera body], [focal length] [aperture], [film stock or lighting qualifier], [time of day or atmosphere].
[One non-idealised physical detail].
```

Example:
```
A man in his late 40s with grey-streaked temples and a weathered face adjusts fishing line at dawn on a deserted pier.
Leica M11, 35mm f/2, Kodak Portra 400, cool pre-dawn fog.
Slight purple under-eye shadow, collar of a worn flannel shirt.
```

### Product still-life

```
[Product with specific descriptor] on [precise surface and context].
Shot overhead with [camera body], [lens], [lighting description].
[Color palette or mood]. [Background detail].
```

Example:
```
A ceramic espresso cup with a hairline crack on the handle rests on a weathered cypress-wood counter, surrounded by scattered coffee grounds.
Shot overhead with a Hasselblad X2D, 80mm f/4, soft north-facing window light.
Muted greys and cream, slightly underexposed.
```

### Architecture / exterior

```
[Building or structure with period/style/location], [time of day], [weather].
Shot with [camera body], [focal length] [aperture].
[Specific lighting condition]. [Human or life element to give scale/life].
```

Example:
```
A 1960s Tokyo shotgun house sandwiched between two glass towers, early evening, light rain.
Shot with a Ricoh GR IIIx, 28mm f/2.8.
Tungsten glow from the interior windows against blue dusk. A bicycle leaning against the entrance gate.
```

### Commercial / brand (JSON format)

```json
{
  "scene": "A lifestyle product shot of a skincare serum bottle",
  "subjects": [
    {"description": "A 30ml amber glass dropper bottle with the label 'AURIC BOTANICS' in minimal sans-serif type", "position": "center-foreground, slightly right of center"},
    {"description": "Three dried botanical stems and two smooth white river stones", "position": "left-foreground, partially behind the bottle"}
  ],
  "style": "editorial beauty photography, clean and minimal",
  "color_palette": ["#F5F0E8", "#2C3E2D", "#C8A96E"],
  "lighting": "single large soft-box from upper left, slight catch-light on the bottle",
  "camera": {"angle": "eye level, slight downward tilt", "lens": "100mm f/2.8 macro"}
}
```

### Multi-reference editing

```
[Subject from reference 1] wearing [clothing/item from reference 2], standing in [environment from reference 3].
[Camera spec]. [Lighting]. [Atmosphere].
```

Example:
```
The woman from the first reference wearing the deep indigo coat shown in the second reference, standing at a rain-blurred intersection at night.
Sony A7R V, 50mm f/1.8, available street lighting, puddles on the pavement.
```

---

## 9. Common mistakes and corrections

| Mistake | Why it's wrong | Correct |
|---|---|---|
| `"photorealistic, 8K, ultra detailed"` | SD1.5-era booru tokens, near-zero signal for Mistral/Qwen3 | Camera body + lens + film stock instead |
| Negative prompt filled in | No CFG path ([dev]) or guidance-off ([klein] distilled) | Phrase constraints positively in the main prompt |
| CFG=0 in KSampler | 0.0 outputs the unconditional (ignores prompt entirely) | Use **1** for guidance-off in [klein] distilled |
| `"The image should show…"` opening | Reflexive meta-language; the encoder interprets it literally and may generate an image of an image | Open directly with the subject: `"A woman…"` |
| Bare hex code without keyword | `"...#0047AB"` routes as text noise; doesn't trigger color conditioning | `"...in color #0047AB"` |
| Subject buried mid-prompt | LLM encoders front-weight tokens | Front-load subject in first clause |
| Treating JSON as required ("plain text fails") | FLUX.2 was trained on natural language; JSON is optional and a workflow tool | Use plain language for single subjects; JSON for complex multi-subject |
| Dropping camera gear to avoid the "AI look" | Some models benefit from removing DSLR markers; FLUX.2 is the opposite — Mistral/Qwen3 treat camera vocabulary as semantic context | Keep camera body + lens + film stock in FLUX.2 prompts for photoreal results |
| `(text:1.5)` parenthetical weight syntax | AUTOMATIC1111 syntax; meaningless for LLM encoders | No parenthetical weighting; rephrase sentence instead |
