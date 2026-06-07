# SDXL Prompting Guide

SDXL is a **dual-CLIP, 77-token UNet**. It matches tokens and short phrases, not sentence syntax. Everything below follows from that. The vocabulary lists are the copy-pasteable core; the weights and workflow numbers are SDXL-calibrated (lower than the SD1.5-era guides this vocabulary was mined from — see §9).

## Table of contents
1. Prompt anatomy
2. Weighting, ordering, token economy
3. The dual-encoder split (`text_g` / `text_l`)
4. Photoreal vocabulary (the copy-paste lists)
5. Lighting, framing, camera angles
6. Negative prompts (variant-aware)
7. Checkpoint dialects: Pony score-tags, Illustrious booru
8. Worked SDXL-calibrated examples
9. What was dropped from the SD1.5-era source

---

## 1. Prompt anatomy

A reliable slot order for **photoreal** SDXL (base / Juggernaut / RealVisXL). Comma-separated phrases, most important first:

```
[style tag], [subject + key feature], detailed skin, [secondary details],
[pose / action], [framing], [setting / background], [lighting],
[camera angle], [camera body + film/lens], [photographer], [filters]
```

- **Style tag leads** and sets the whole register (`candid photo`, `documentary photography`, `glamour photography`).
- **Subject early** with the one or two features that define it; pin age with `age 30` if it drifts.
- **`detailed skin`** is the single highest-value realism token on SDXL photoreal finetunes.
- Keep it **evocative, not exhaustive** — 3–5 strong concepts beat 40 adjectives; CLIP attention drifts past the first chunk.
- Add `portrait` or tighten the framing if the subject renders too small/far.

This is a *default*, not a law. Anime/booru checkpoints use a different structure entirely (§7).

---

## 2. Weighting, ordering, token economy

- **Position = weight.** CLIP weights earlier tokens more heavily. Front-load subject + the highest-value concepts. The model "prioritises key/early words and ignores less important ones."
- **Emphasis syntax:** `(phrase:1.2)` raises, `(phrase:0.9)` lowers. Bare `(phrase)` ≈ 1.1, `[phrase]` ≈ 0.9 in A1111-style UIs.
- **SDXL-calibrated weight range: ~1.05–1.3.** This is the most important recalibration in this guide. SD1.5 photorealism guides routinely use 1.5–1.8; on SDXL those **fry colours, posterise, and over-contrast**. Start at 1.15, nudge in 0.05 steps.
- **77-token chunks.** Each CLIP chunk is 77 tokens (~60 words). Past that, weight falls off sharply. Keep prompts tight. If you truly need more, insert `BREAK` (ComfyUI/A1111) — each side of `BREAK` is encoded as its own chunk and the embeddings are concatenated, so put a self-contained idea in each chunk rather than splitting mid-phrase.
- **No generic booster blocks.** `8k, masterpiece, best quality, ultra detailed, hyperrealistic` are near-inert on SDXL — they consume tokens without earning quality. Replace them with concrete photographic terms (§4).

---

## 3. The dual-encoder split (`text_g` / `text_l`)

SDXL has two text encoders. The **stock ComfyUI templates feed both the same text** via plain `CLIPTextEncode`. The **`CLIPTextEncodeSDXL`** node exposes them separately — an *advanced* lever, not the default:

| Field | Routes to | Put here |
|---|---|---|
| `text_g` | OpenCLIP-ViT/bigG (global) | overall scene, mood, composition, style |
| `text_l` | CLIP-ViT/L (local) | specific objects, textures, fine detail |
| `width` / `height` | size-conditioning | your actual render resolution (e.g. 1024 / 1024) |
| `crop_w` / `crop_h` | crop-conditioning | **0 / 0** for centered framing |
| `target_width` / `target_height` | target-size | your output resolution |

Use the split when global vs detail want different emphasis — e.g. a cinematic mood in `text_g` while pinning a precise garment/material in `text_l`. When unsure, duplicate the same prompt into both (the plain-node default). The **refiner** has its own `CLIPTextEncodeSDXLRefiner` node with an `ascore` (aesthetic score) field — default ~6.0 for positives, ~2.0 for negatives.

**Micro-conditioning matters even when you ignore it.** A non-zero `crop` coordinate is the usual cause of "head cut off at the top of the frame" — keep it (0,0). A low `original_size`/`width` value makes output look low-res even at 1024² — keep it at your real resolution unless you deliberately want a degraded look.

---

## 4. Photoreal vocabulary (the copy-paste lists)

These are CLIP-understood terms. The *words* transfer to SDXL; weight them modestly (§2). Mined from a 2023 Stable Diffusion photorealism guide and recalibrated.

### Style tags (lead the prompt)
`candid photo` · `documentary photography` · `glamour photography` · `high fashion photography` · `street fashion photography` · `beauty shot` · `lifestyle photography` · `analog photo` · `polaroid` · `instant photo` · `large format` · `tintype` · `pinhole photography` · `paparazzi` · `pictorialist photo`

Notes: `documentary` → realistic skin, good in B&W. `glamour`/`beauty` → add `NSFW` to negatives if you want clothed. `polaroid`/`instant` → faded retro. `tintype` → reads old-fashioned at high weight.

### Camera bodies
- **Cinema:** `shot on ARRI ALEXA 65` (crisp, high DR) · `shot on RED digital cinema` · `shot on Aaton LTR` · `shot on Bolex H16` (vintage 16mm)
- **Digital:** `shot on Canon EOS 5D` (shallow DoF, bokeh) · `Fujifilm X-T4` (Fuji colour, grain) · `Sony A7 III` · `Hasselblad X1D II` (medium format, fine texture) · `Pentax 645Z` (medium format, high DR) · `Lumix GH5` (cinematic bokeh) · `Leica T` (Leica colour, vignetting) · `(GoPro Hero:1.2)` (fisheye POV)
- **Retro film bodies:** `Hasselblad 500CM` · `Rolleiflex` (square, ultra-sharp) · `Leica M3` (microcontrast) · `Polaroid SX-70` (square, muted) · `Kodak Brownie` (square, vignette, soft) · `Holga 120N` / `Diana F+` (lo-fi, light leaks — weight ~1.2, pair with grain/haze)

### Film stocks
`Kodak Portra 400` (flattering skin) · `Portra 160` · `Cinestill 800T` (halation, cinematic) · `Ektar 100` (saturated, sharp) · `Velvia 100` (vivid landscape) · `Agfa Vista` (oversaturated) · `Fujicolor Pro` (natural balance) · `Kodak Vision3` (cinematic) · `Ilford HP5 Plus` (B&W) · `Tri-X 400` (B&W, contrasty) · `Lomochrome` (colour-shift, pair with Holga/Diana)

Grain phrasing: `film grain` · `fine grain` · `prominent grain` · `muted low grain`.

### Lenses
`50mm` (natural FOV) · `35mm` (reportage) · `85mm` (portrait compression) · `Voigtländer Nokton 50mm f1.1` (dreamy bokeh) · `8mm fisheye` (180° distortion). Note: on a CLIP model, plain focal-length numbers move the image **weakly** — named/iconic lenses and the camera body do more. SDXL's bigG encoder responds somewhat better than SD1.5 did, but don't rely on `f/1.4` alone for bokeh; pair it with `shallow depth of field, bokeh`.

### Quality-via-concrete-detail (instead of "8k masterpiece")
`detailed skin` · `visible skin pores` · `subsurface scattering` · `fine grain` · `shallow depth of field` · `bokeh` · `wide dynamic range` · `microcontrast` · `smooth tonality` · `crisp details`

### Photographer attributions (`in style of [name]`)
Portraits/fashion: Richard Avedon · Martin Schoeller · George Hurrell · Paolo Roversi · Nick Knight · Tim Walker · Miles Aldridge · David LaChapelle · Yousuf Karsh. Documentary/street: Walker Evans · Garry Winogrand · Nan Goldin · Lee Friedlander · August Sander · Alfred Stieglitz. Moody/fine-art: Nathan Wirth · Oleg Oprisco · Brandon Woelfel · Miko Lagerstedt · Chris Friel · Anne Brigman. Weight ~1.1–1.3; the name is a *flavour*, not a guarantee.

### Filters & effects
`black and white` · `sepia tone` (low weight) · `bokeh` · `dreamy haze` · `soft focus` · `lens flare` · `vignette` · `desaturated grunge` · `long exposure` · `overexposed` / `underexposed` · `technicolor` · `infrared`. Weight effect tags ~1.1–1.3.

---

## 5. Lighting, framing, camera angles

**Lighting — name source + quality + direction** (the highest-leverage realism variable after the finetune):
`soft window light from camera-left` · `golden hour side light` · `harsh direct flash` · `soft bounced lighting` · `chiaroscuro single source` · `dramatic rim lighting` · `low-key lighting` · `high-key brightly lit` · `overcast flat lighting` · `god rays through haze` · `neon lighting`.

**Framing:** `close up on face` · `head shot` (more hair/shoulders) · `upper body` (waist-up) · `full body`.

**Camera angles:** `eye level` · `high angle` / `from above` · `low angle` / `from below` · `(Dutch angle:1.3)`.

---

## 6. Negative prompts (variant-aware)

**Negatives only work where guidance is on.** On base and standard finetunes (CFG > 1), use them. On **distilled variants at CFG 1 (ComfyUI) / `guidance_scale=0.0` (diffusers)** — Turbo, Lightning, LCM, Hyper — **negatives are inert**; phrase constraints positively in the main prompt instead.

A practical SDXL negative baseline (base/finetune):
```
deformed, extra fingers, mutated hands, bad anatomy, lowres, blurry, jpeg artifacts,
oversaturated, plastic skin, watermark, text, signature
```
- Keep it short — bloated negatives cost adherence and can wash out the image.
- **Do not** use SD1.5 negative-embedding textual inversions (`UnrealisticDream`, `EasyNegative`, `bad-hands-5`, etc.) — they're trained on the SD1.5 text encoder and **won't load on SDXL**. There are SDXL-native negative embeddings, but plain words suffice.
- `glamour`/`beauty` styles: add `NSFW, nude` to negatives to keep subjects clothed.

---

## 7. Checkpoint dialects: Pony & Illustrious

The photoreal dialect above is for base/Juggernaut/RealVis/DreamShaper. **Tag-trained checkpoints need their own dialect** — a normal photo prompt produces mush on them.

**Pony Diffusion V6 XL** — steer quality with **score tags** and pin the domain with **source/rating tags**, then Danbooru-style content tags:
```
score_9, score_8_up, score_7_up, source_anime, rating_safe, 1girl, solo, <booru tags…>
```
The `score_9, score_8_up, score_7_up, score_6_up, …` ladder is near-mandatory; `source_anime` / `source_pony` / `source_furry` and `rating_safe` / `rating_explicit` set the register. Pony LoRAs are a **separate pool** — base-SDXL LoRAs don't transfer.

**Illustrious / NoobAI XL** — **Danbooru booru tags**, comma-separated, no score ladder (or a model-specific quality tag set — check the model card). `1girl, solo, <character>, <series>, <attributes>, masterpiece, best quality`. These quality boosters *do* work here (the model was trained with them), unlike on photoreal SDXL.

When the user names a checkpoint, match the dialect to it. See `references/checkpoints-and-loras.md` for the full roster.

---

## 8. Worked SDXL-calibrated examples

Fresh prompts written for SDXL (weights ~1.1–1.3, 1024-area buckets). Assume a photoreal finetune (Juggernaut/RealVisXL) unless noted.

**A — Editorial close-up portrait** (1024×1216, base/finetune, CFG 6, 30 steps)
> `candid photo, 28 year old woman with copper hair and freckled olive skin, (detailed skin:1.2), calm relaxed expression, close up on face, plain concrete wall background, soft window light from camera-left, eye level, shot on Canon EOS 5D, Kodak Portra 400, shallow depth of field, fine grain`
> Negative: `deformed, extra fingers, plastic skin, oversaturated, blurry, watermark, text`

**B — Cinematic environmental wide** (1344×768, base/finetune, CFG 6, 35 steps)
> `documentary photography, man in a navy peacoat walking a rain-slick cobblestone street at blue hour, full body, pastel townhouses and warm window lights behind, backlit by a distant streetlamp, reflections on wet stone, low angle, shot on ARRI ALEXA 65, Cinestill 800T, (film grain:1.1)`

**C — High-key product/beauty** (1024×1024, RealVisXL, CFG 5, 30 steps)
> `beauty shot, close up of a woman's face, (detailed skin:1.25), visible skin pores, dewy natural makeup, soft bounced lighting, high-key brightly lit, plain white background, shot on Hasselblad X1D II, microcontrast, smooth tonality`
> Negative: `plastic skin, airbrushed, oversaturated, harsh shadows, blemishes removed, NSFW`

**D — Fast draft on Lightning** (1024×1024, Juggernaut + 4-step Lightning LoRA, **CFG 1 in ComfyUI**, 4 steps, `euler`/`sgm_uniform`)
> `candid photo, elderly fisherman mending a net on a harbor dock, weathered detailed skin, overcast flat lighting, 35mm, Fujifilm X-T4, fine grain`
> (No negative — guidance is off at CFG 1; fold constraints into the prompt: e.g. add `clear sharp focus` rather than negating `blurry`.)

**E — Pony dialect** (1024×1024, Pony V6 XL, CFG 7, 25 steps)
> `score_9, score_8_up, score_7_up, source_anime, rating_safe, 1girl, solo, long silver hair, blue eyes, school uniform, classroom, sunlight through window, looking at viewer`

---

## 9. What was dropped from the SD1.5-era source

The vocabulary here was mined from a 2023 photorealism guide written for **SD1.5 checkpoints** (Absolute Reality 1.6 etc.). Carried over: the prompt anatomy and **all the vocabulary** (style tags, camera/film/lens/photographer names, lighting, framing) — these are semantic content the CLIP encoders understand. **Recalibrated or dropped:**

- **Weights lowered** from 1.5–1.8 to ~1.05–1.3 (SDXL fries at high weights).
- **Resolution advice inverted** — the "generate at 512 then upscale" workflow is SD1.5's 512px-native habit; **SDXL is 1024px-native**, render in a 1024-area bucket directly.
- **SD1.5 tooling dropped** — A1111 HiRes-Fix recipes, `aDetailer` denoise values, and the SD1.5 inpainting numbers are not carried as SDXL gospel (SDXL equivalents are in `references/setup-and-workflows.md`).
- **SD1.5 negative embeddings dropped** (`UnrealisticDream` etc. won't load).
- **Lens-spec skepticism softened** — the source found focal-length numbers inert on SD1.5; SDXL's bigG encoder responds a bit better, but still pair numbers with `shallow depth of field, bokeh`.
