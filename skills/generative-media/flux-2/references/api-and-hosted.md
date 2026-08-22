# FLUX.2 — BFL Hosted API

Source tier: BFL official API docs at `docs.bfl.ai` and `docs.bfl.ml` (official-via-docs, fetched via research agents); pricing and region endpoints verified via BFL docs/blog. Pricing is community-tier — BFL uses an interactive calculator; verify at `bfl.ai/pricing` before relying on any stated prices.

---

## Contents

1. [Endpoints and regions](#1-endpoints)
2. [Authentication](#2-auth)
3. [API model slugs and capabilities](#3-models)
4. [Request format and parameters](#4-request)
5. [Async polling pattern](#5-polling)
6. [Python example](#6-python)
7. [Commercial use via API](#7-commercial)
8. [API pricing (community-tier)](#8-pricing)

---

## 1. Endpoints and regions

| Region | Base URL |
|---|---|
| Global (default) | `https://api.bfl.ai` |
| EU | `https://eu1.api.bfl.ai` |
| US | `https://us1.api.bfl.ai` |

**Path structure:** `POST /<version>/<model-slug>`

Current stable version: `v1`. All examples below use `https://api.bfl.ai/v1/<endpoint>`.

---

## 2. Authentication

**Header:** `X-Key: <your-api-key>`

```http
POST https://api.bfl.ai/v1/flux-2-pro
Content-Type: application/json
X-Key: YOUR_API_KEY

{...}
```

Keys are issued at `api.bfl.ai` (account → API keys). There is no OAuth/Bearer flow — key-in-header only.

---

## 3. API model slugs and capabilities

| Slug | Quality | Notes |
|---|---|---|
| `flux-2-pro` | High | Closed weights; step-optimised for quality/speed balance |
| `flux-2-max` | Highest | Closed weights; adds web grounding for current events, brands, and public figures; best for complex prompts |
| `flux-2-flex` | Configurable | Exposes `steps`, `guidance`, and sampler parameters explicitly; best for experimentation and workflows requiring precise control |
| `flux-2-klein` | Fast | Routes to [klein] 9B or 4B (BFL may vary per workload); lowest latency and cost; fastest for iterating |
| `flux-2-dev` | High | [dev] 32B accessible via API; commercially-usable API outputs even though open weights are Non-Commercial |

> The exact compute tier behind each closed slug ([pro]/[max]/[flex]) is undisclosed. Use `flux-2-max` when query complexity is high (multi-reference, detailed scenes, current-event grounding). Use `flux-2-flex` when you need to control sampling parameters programmatically.

### Capability comparison

| Feature | [pro] | [max] | [flex] | [klein] | [dev] |
|---|---|---|---|---|---|
| Steps/guidance control | No | No | **Yes** | No | No |
| Web grounding | No | **Yes** | No | No | No |
| Multi-reference edit | — | — | — | — | — |
| Fastest latency | — | — | — | **Yes** | — |
| Best for complex prompts | — | **Yes** | — | — | — |
| Commercial output use | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** |

---

## 4. Request format and parameters

**Common parameters across all models:**

| Parameter | Type | Description | Default |
|---|---|---|---|
| `prompt` | string | Natural language or JSON prompt | required |
| `width` | integer | Pixel width (multiples of 16, 256–2048) | 1024 |
| `height` | integer | Pixel height (multiples of 16, 256–2048) | 1024 |
| `output_format` | string | `"jpeg"` or `"png"` | `"jpeg"` |
| `output_quality` | integer | 1–100 (JPEG compression) | 80 |
| `seed` | integer | Seed for reproducibility; omit for random | null |
| `safety_tolerance` | integer | 1 (strictest) to 6 (most permissive); authenticated users only | 2 |
| `prompt_upsampling` | boolean | Whether to internally expand/upscale the prompt | false |

**`flux-2-flex` additional parameters:**

| Parameter | Type | Description |
|---|---|---|
| `steps` | integer | Number of denoising steps; default 20; range 1–50 |
| `guidance` | float | Guidance scale; default 4.0; applicable to [dev]-tier compute |
| `image` | string | Base64-encoded reference image for image-to-image |
| `strength` | float | Noising strength for img2img; 0.0 (no change) to 1.0 (full regen); typical range 0.6–0.85 |

**Resolution notes:**
- Dimensions must be multiples of 16
- Maximum: 2048 × 2048 (approximately 4 megapixels)
- Non-square aspect ratios are supported: 512×2048, 1024×576, etc.
- The model supports up to ~4 MP total; reduce both dimensions if targeting non-standard extreme aspect ratios

---

## 5. Async polling pattern

The BFL API is **fully asynchronous** — POST to start a job, then poll `GET /v1/get_result?id=<task_id>` until the job completes. There is no streaming or websocket path.

**Job lifecycle:**

```
POST /v1/<model-slug>  →  { "id": "<task-id>" }
        ↓
GET /v1/get_result?id=<task-id>  →  { "status": "Pending" }
        ↓ (poll every 0.5–2 seconds)
GET /v1/get_result?id=<task-id>  →  { "status": "Ready", "result": { "sample": "<url>" } }
```

**Status values:**

| Status | Meaning |
|---|---|
| `"Pending"` | Job queued, not yet started |
| `"Processing"` | Inference running |
| `"Ready"` | Completed; `result.sample` contains a signed URL |
| `"Error"` | Failed; check `result.error` |
| `"Content Moderated"` | Blocked by safety filter; raise `safety_tolerance` if appropriate or revise prompt |

**Polling interval:** 0.5–1 second for fast [klein] jobs; 1–2 seconds for [dev]/[pro]/[max]. The signed URL in `result.sample` is temporary — download promptly.

---

## 6. Python example

```python
import requests
import time

API_KEY = "YOUR_API_KEY"
BASE_URL = "https://api.bfl.ai/v1"

def generate(prompt: str, model: str = "flux-2-pro", width: int = 1024, height: int = 1024) -> str:
    # 1. Submit job
    resp = requests.post(
        f"{BASE_URL}/{model}",
        headers={"X-Key": API_KEY, "Content-Type": "application/json"},
        json={"prompt": prompt, "width": width, "height": height, "output_format": "jpeg"}
    )
    resp.raise_for_status()
    task_id = resp.json()["id"]

    # 2. Poll for completion
    while True:
        poll = requests.get(
            f"{BASE_URL}/get_result",
            headers={"X-Key": API_KEY},
            params={"id": task_id}
        )
        poll.raise_for_status()
        data = poll.json()
        status = data.get("status")

        if status == "Ready":
            return data["result"]["sample"]  # signed URL
        elif status in ("Error", "Content Moderated"):
            raise RuntimeError(f"Job failed: {status} — {data.get('result', {}).get('error', 'unknown')}")
        
        time.sleep(1.0)

# Usage
url = generate("A ceramic espresso cup on a rain-wet counter, Hasselblad X2D, 80mm f/2.8, Fujifilm Pro 400H")
print(url)
```

**With `flux-2-flex` (custom steps/guidance):**

```python
resp = requests.post(
    f"{BASE_URL}/flux-2-flex",
    headers={"X-Key": API_KEY, "Content-Type": "application/json"},
    json={
        "prompt": "A woman in her 30s...",
        "width": 1024, "height": 1024,
        "steps": 28,
        "guidance": 4.0,
        "seed": 42
    }
)
```

---

## 7. Commercial use via API

**API outputs are commercially usable regardless of underlying model weights.** This is critical:

| Situation | Commercial use? |
|---|---|
| Calling `flux-2-dev` via API | **Yes** — API outputs, not weight distribution |
| Running [dev] weights yourself | **No** — FLUX Non-Commercial License v2.0 |
| Calling `flux-2-pro` / `flux-2-max` / `flux-2-flex` | **Yes** |
| Running [klein] 4B Apache-2.0 weights yourself | **Yes** |

BFL's terms state that you own your API outputs and BFL claims no rights to them. The weight-distribution license is separate from the API output-use license.

**For high-volume commercial production**, the API is the correct path unless:
- You need [klein] 4B open-weight benefits (local, no per-request cost, full data privacy)
- Latency requirements preclude round-trip API calls

---

## 8. API pricing (community-tier — verify at bfl.ai/pricing)

BFL publishes pricing through an interactive calculator rather than a static price table — the numbers below are from research-agent lookups and should be treated as directional only.

**Approximate relative tier ordering** (not published as fixed prices):
- `flux-2-klein` — cheapest per image
- `flux-2-pro` — mid-tier
- `flux-2-flex` — mid-tier (varies by step count)
- `flux-2-max` — most expensive per image (web grounding overhead)
- `flux-2-dev` — comparable to pro

All BFL pricing is per-image, not per-second. Resolution affects cost (higher resolution = more compute).

**To get current prices:** `bfl.ai/pricing` — enter model and resolution in the interactive calculator.
