# Krea 2 — API & hosted surfaces

The hosted side: Krea's own API and web app (Medium/Large — the variants you can't download), fal's endpoints for the open models, and the ComfyUI partner nodes. Pricing and params verified against Krea's developer docs and fal's pages 2026-07-06/07 — **pricing and the 1K resolution cap are exactly the kind of fact that moves; re-verify before quoting in a budget.**

## Contents
1. [Hosted vs open — what's actually different](#1-hosted-vs-open--whats-actually-different)
2. [The Krea API](#2-the-krea-api)
3. [The web app](#3-the-web-app)
4. [ComfyUI partner nodes](#4-comfyui-partner-nodes)
5. [fal (and other hosts) for the open models](#5-fal-and-other-hosts-for-the-open-models)

---

## 1. Hosted vs open — what's actually different

| | Open (Raw/Turbo) | Hosted (Medium/Large) |
|---|---|---|
| Weights | downloadable | no |
| VAE | Qwen-Image VAE | **Large trained with the FLUX.2 VAE** [official — team statement, HN] — a real fidelity difference, not just scale |
| Resolution | 1K (Raw) / 1–2K (Turbo) | **1K only via API, currently** [official — API docs] |
| Style references / moodboards | not in the open stack (style LoRAs instead) | yes — the flagship feature |
| Creativity dial | no (analogue: enhancer on/off) | raw / low / medium / high |
| Sliders (intensity/complexity/movement) | no | −100…100 each |
| Cost | your GPU | $0.030–0.070/img (§2) |
| Licence | Community License (revenue-gated) | Krea ToS; you own outputs |

No independent hosted-vs-open quality shootout has been published yet — assume Large > Turbo on fidelity (Krea's own positioning: "richest output", photorealism) but treat magnitude as unknown.

## 2. The Krea API

Base: `https://api.krea.ai` (docs: krea.ai/docs/developers). Async job pattern: `POST` returns a `job_id`; poll `GET /jobs/{job_id}` or register a webhook.

**Endpoints:** `POST /generate/image/krea/krea-2/medium` and `…/krea-2/large`.

**Parameters** [official — API overview]:

| Param | Values | Notes |
|---|---|---|
| `prompt` | string | same prompting doctrine as local (`prompting-guide.md`) — content in the prompt, style in the controls below |
| `aspect_ratio` | `1:1, 4:3, 3:2, 16:9, 2.35:1, 4:5, 2:3, 9:16` | |
| `resolution` | `1K` | "1K only currently" |
| `creativity` | `raw / low / medium / high` | default `medium`; `raw` = render only what's written, no expansion |
| `seed` | int | |
| `image_style_references` | up to **10**, each with `strength` | style conditioning, not identity |
| `moodboards` | max **1** (moodboard ID) | created in the app |
| `styles` | up to 10 preset/LoRA style IDs | |
| `intensity`, `complexity`, `movement` | −100…100, default 0 | global aesthetic sliders |

**Pricing** [official, verified 2026-07-06 — volatile]:

| | base | + style refs | + moodboards |
|---|---|---|---|
| Medium | $0.030 | $0.035 | $0.040 |
| Large | $0.060 | $0.065 | $0.070 |

## 3. The web app

krea.ai image generator: pick **Medium / Large / Turbo**; up to **4 style references, each with a strength slider**; moodboards ("the most precise way to set a visual direction"); batch up to 4; 1K output [official — user guide]. The app is also where moodboards get created for API use. Krea's broader editor (realtime canvas, upscaler, etc.) wraps the same models but is out of scope here.

## 4. ComfyUI partner nodes

Hosted Medium/Large inside ComfyUI via the official **"Krea 2 Image" API node** (launched 2026-05-27): prompt + style refs + moodboard IDs + creativity Raw/Low/Medium/High, billed through API credits [official — Comfy blog]. This is a *different integration* from the local Turbo template (`setup-and-workflows.md §1`) — partner nodes call Krea's servers; nothing loads on your GPU.

## 5. fal (and other hosts) for the open models

fal is the launch API partner (2026-05-27) [official — press release]:

- `fal-ai/krea-2/turbo` — open Turbo, hosted: `image_size` presets or custom WxH, `enable_prompt_expansion` (the same expander — same considerations as `prompting-guide.md §6`), acceleration `none/regular`, safety checker toggle, png/jpeg [official-via-host — fal API page].
- `fal-ai/krea-2/turbo/lora` — Turbo + your LoRA weights.
- `fal-ai/krea-2-trainer` — hosted LoRA training (`lora-training.md §4`).
- Hosted Medium/Large also proxied as `krea/v2/medium|large/text-to-image` on fal.

Other listed inference partners for the open weights: SGLang (cookbook recipe), Replicate, Cloudflare, Together, GCP, AWS, Runware [official — krea-2-open-source page]. Partner param schemas count as official-via-host; where fal and Krea disagree on a default, the GitHub README/CLI is the tiebreaker.
