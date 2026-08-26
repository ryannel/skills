# Ideogram 4 hosted API & web app

> **Secondary path.** The main skill is about running the **open weights** yourself (ComfyUI / diffusers / CLI). Reach for this file only for the two things the open weights can't do: **commercial use** (the weights are non-commercial) and the **web-only Character/Style Reference** features.

These are the commercial cloud surfaces. **Output you generate here is yours and may be used commercially** (web/API Terms of Service assign output ownership to you). This is unlike the non-commercial local weights. This is the path for commercial work.

Confidence: the **magic-prompt endpoint** is confirmed from the open-source client code (`src/ideogram4/magic_prompt.py`). The rest of the API surface and pricing come from `developer.ideogram.ai` / `docs.ideogram.ai` / `ideogram.ai/api-pricing`, fetched through a summariser. This gives **high confidence, but spot-verify against the live docs before building**, especially for the presence or absence of optional params.

---

## 1. Auth & base

- Base: `https://api.ideogram.ai`
- Auth header: **`Api-Key: <your-key>`** (get a key at `developer.ideogram.ai`).
- `generate` / `remix` / `describe` use `multipart/form-data`.
- Default rate limit: ~**10 in-flight requests** (contact Ideogram for more) `[official — developer.ideogram.ai docs]`.

The v4 surface is **deliberately minimal** compared with v3. Many of the old v3 request params (style_type, negative_prompt, color_palette, character/style reference, seed, num_images, aspect_ratio) are **not** v4 generate params. Control now lives **inside the JSON caption** instead.

---

## 2. Generate — `POST /v1/ideogram-v4/generate`

This takes text or JSON and returns an image. It is synchronous and runs the 4.0 model.

| Param | Type | Values / notes | Default |
|---|---|---|---|
| `text_prompt` | string | natural language; **mutually exclusive with `json_prompt`**. When used, **Magic Prompt is applied automatically** | required* |
| `json_prompt` | object | a `V4JsonPrompt` structured caption (schema below); when used, **Magic Prompt is bypassed** — you control everything | required* |
| `resolution` | string | explicit pixel dims, e.g. `"2048x2048"`, `"2880x1440"` (the API uses `resolution`, **not** `aspect_ratio`) | optional |
| `rendering_speed` | string | `FLASH` *(announced — currently returns 400)* / `TURBO` / `DEFAULT` / `QUALITY` | `DEFAULT` |
| `enable_copyright_detection` | boolean | post-gen Hive likeness/logo checks | optional |

\* Exactly one of `text_prompt` / `json_prompt`.

**Not present in the v4 generate schema** (these were v3, or live elsewhere): `style_type`, `magic_prompt` (it's automatic, not a toggle), `negative_prompt`, `color_palette` (→ goes inside the JSON caption), `style_reference` / style codes, `character_reference`, `aspect_ratio` (→ on the magic-prompt endpoint). `seed` / `num_images` were **not** enumerated in the fetched schema. They may exist as optional fields. **Verify on the live API if you need reproducibility or batching** `[flagged — re-verify]`.

### `V4JsonPrompt` (same schema as local)

This is identical to the local caption schema (full detail in `json-caption-guide.md`):

- `high_level_description` (string, recommended)
- `style_description` (object, optional) — `aesthetics`, `lighting`, `photo`|`art_style`, `medium`, `color_palette` (strict key order; exactly one of photo/art_style)
- `compositional_deconstruction` (object, **required**) — `background` (string) + `elements` (list of obj/text; `bbox` is `[y_min,x_min,y_max,x_max]`, 0–1000)

Sending `json_prompt` is how you get the model's full controllability over the API: exact layout, typography, and color. Color palettes go **inside** the JSON (style-level up to 16, per-element up to 5 uppercase `#RRGGBB`), not as a separate request param.

### Resolutions (accepted enum, partial) `[official — docs.ideogram.ai]`
`2048x2048`, `1440x2880`, `2880x1440`, `1664x2496`, `2496x1664`, `1792x2240`, `2240x1792`, `1440x2560`, `2560x1440`, `1600x2560`, `2560x1600`, `1728x2304`, `2304x1728`, `1296x3168`, `3168x1296`, `1152x2944`, `2944x1152`, `1248x3328`, `3328x1248`, `1280x3072`, `3072x1280`, `1024x3072`, `3072x1024`.

---

## 3. Magic Prompt — `POST /v1/ideogram-v4/magic-prompt` `[official — ideogram4 client source]`

This expands a plain prompt into a ready-to-use JSON caption, so you can inspect or tune it before generating.

- Request: `{ "text_prompt": "<idea>", "aspect_ratio": "<WxH>" }` — `aspect_ratio` uses the **`WxH`** form (e.g. `"16x9"`), or `"AUTO"`. Accepted ratios include `AUTO, 1x4, 1x3, 1x2, 9x16, 10x16, 2x3, 3x4, 4x5, 1x1, 5x4, 4x3, 3x2, 16x10, 16x9, 2x1, 3x1, 4x1` (default `AUTO`).
- Response: `{ "aspect_ratio": ..., "json_prompt": {...} }` — feed `json_prompt` straight into `/generate`.
- Free; this is the default Magic Prompt backend (`ideogram-4-v1`) the local CLI also calls.

---

## 4. Other v4 endpoints

| Endpoint | Does | Key params |
|---|---|---|
| `POST /v1/ideogram-v4/remix` | image + prompt → variation | `image` (binary ≤10 MB, JPEG/PNG/WebP), `text_prompt` (required), `image_weight` (higher = keep input structure), `resolution`, `rendering_speed`, `enable_copyright_detection` |
| `POST /v1/ideogram-v4/describe` | image → structured `V4JsonPrompt` | `image_file` (binary ≤10 MB), `include_bbox` (bool, default `true`) → returns `{ json_prompt }` |
| `POST /v1/ideogram-v4/magic-prompt` | prompt enhancer | see §3 |

**Edit / inpaint, upscale, reframe/extend, replace-background:** there are **no v4-namespaced endpoints** for these in the fetched reference. They are documented under **v3** (`/v1/ideogram-v3/*`), but the pricing page bills Edit / Reframe / Replace-Background at the 4.0 rate. This implies you run the 4.0 model through the v3 edit-family paths. **The v3-path-runs-4.0 linkage is an inference, not a stated fact. Verify before relying on it** `[flagged — re-verify]`.

---

## 5. Pricing & credits

### API — per image `[official — ideogram.ai/api-pricing]`

| Operation | Price |
|---|---|
| 4.0 **Turbo** generate | **$0.03** |
| 4.0 **Default** generate | **$0.06** |
| 4.0 **Quality** generate | **$0.10** |
| Describe | $0.01 / input image |
| Upscale | $0.06 / input image |
| Instructional Edit | $0.20 / image |

(Generate, Remix, Edit, Reframe, and Replace-Background are all covered by the per-image generate rate at the chosen speed. There is no published `FLASH` price, since that tier is not live.)

> The pricing page is internally dated "August 6, 2025" — *before* the June 2026 launch — so the timestamp is unreliable even though the 4.0 prices are listed — **re-check the live page** `[flagged — re-verify]`.

### Web-app plans `[flagged — re-verify]`

| Plan | ~Price | Rough allowance |
|---|---|---|
| Free | $0 | ~10 slow credits/week; free-tier images **public** by default |
| Basic | ~$8/mo | ~400 priority credits/mo + slow credits |
| Plus | ~$20/mo | ~1,000 priority credits/mo; **private** generation |
| Pro | ~$60/mo | ~3,000 priority credits/mo |

A 4.0 **Quality** image costs ≈ ~6 credits, and **Turbo** costs ≈ ~1 credit — so you get ~8× as many Turbo images per Quality image's credits. **All web-plan numbers are third-party and approximate. Confirm at `ideogram.ai/pricing`** `[flagged — re-verify]`.

---

## 6. Web app features (v4)

Per `docs.ideogram.ai`, where available 4.0 supports post-generation workflows: **remove background, prompt edit, layerize / editable text layers, extend, reframe, upscale, remix, and Magic Fill**, plus "prompt fidelity, crystal-clear type, reliable editing, **native transparency**, style control, and design-quality outputs" `[official — docs.ideogram.ai]`.

- **Magic Fill / inpaint, Reframe/Extend, Upscale, Remove background, Remix, Prompt edit** — these are live for 4.0 "where available".
- **Editable text layers ("layerize")** — typed text elements (a literal string plus separate styling) that you can re-edit. This is the "design as layers, not a flat frame" thesis. Live.
- **Native transparency** — transparent-PNG output. In a caption, set `background` to exactly `"transparent background"`.
- **Character Reference (web app and v3 API)** — upload a portrait, and the system auto-masks face and hair, then carries that identity through subsequent generations. The mask is editable, so you can exclude hair to allow restyling. Limitation: it cannot be used at the same time as Style Reference, and Color Palette, Negative Prompt, and Seed are disabled when active. **Available in web app and `POST /v1/ideogram-v3/generate`** via `character_reference_images` + `character_reference_images_mask` params. **Not available in the v4 API**, since the v4 generate endpoint has no image conditioning params `[official — developer.ideogram.ai/api-reference/generate-v3]`.
- **Style Reference (web app and v3 API)** — upload a reference image to condition the visual style of the generation. **Available in web app and `POST /v1/ideogram-v3/generate`** via `style_reference_images`. **Not available in the v4 API.** It is mutually exclusive with Character Reference `[official — docs.ideogram.ai/style-reference]`.
- The plain-text Magic Prompt rewrites your idea into a JSON caption behind the scenes. Toggling it off, where exposed, feeds your text more literally.

---

## 7. Commercial usage

- **You own your outputs.** Ideogram's Terms of Service assign all rights in user output to you, and the API Terms do the same. This applies to web and API output, free and paid (free-tier images are just *public* by default; private generation is a paid feature).
- **Restrictions:** respect third-party rights and the Acceptable Use Policy. You bear liability for your commercial use. There is a standard **no-compete** clause — don't use inputs or outputs to build something competitive with Ideogram or the model.
- **vs. local weights:** the hosted surfaces are the supported route to *commercial* Ideogram 4 output. The downloadable weights are **non-commercial**, so generating commercial product imagery from them falls outside that licence (see SKILL.md → *Licence & limitations*).
