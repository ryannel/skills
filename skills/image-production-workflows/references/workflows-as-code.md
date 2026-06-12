# Workflows as Code — ComfyScript, the API route, comfy-cli, diffusers, and pro conventions

How to take a working graph from "I click Queue" to parametrized, batched, scriptable production — and the conventions professional ComfyUI users layer on top.

## Contents
1. The four code routes, compared
2. ComfyScript
3. The native API route (Export API + `/prompt` + comfy-cli)
4. diffusers as the code-first alternative
5. Pro conventions: subgraphs, rgthree, wildcards, batch QC

---

## 1. The four code routes, compared

| Route | What it is | Pick it when |
|---|---|---|
| **ComfyScript** | Python DSL over ComfyUI — nodes as Python functions | you want to *write* workflows as code, with loops/conditionals/sweeps, against a local or remote ComfyUI |
| **Export (API) + `/prompt`** | the GUI graph exported as minimal JSON, POSTed to ComfyUI's HTTP API | you build graphs in the GUI and need to *run* them programmatically — the most production-proven route |
| **comfy-cli** (Comfy-Org, official) | command-line runner + installer + model manager | batch driving from shell scripts/CI; converting GUI↔API JSON |
| **diffusers** | no ComfyUI at all — pipelines in Python | code-first multi-stage work; cross-model handoffs are pixels by construction; easiest to test/version |

## 2. ComfyScript

`Chaoses-Ib/ComfyScript` — **alive and current** (v0.6.0 Nov 2025 added ComfyUI v3-schema support and Python 3.14; v0.6.1 followed), but a **single-maintainer project: pin versions in production.** *(Official repo.)*

Three modes:
- **Virtual mode** — your Python builds workflow JSON and submits it to a ComfyUI server (local or remote). The default for production: the server stays the executor, your script is the orchestrator.
- **Real mode** — nodes run as plain Python functions in-process. For research/optimization loops where you want Python control flow *between* node calls.
- **Transpiler** — converts an existing workflow JSON *into* ComfyScript Python. The migration path: build in the GUI, transpile, then parametrize.

The shape of it (virtual mode):

```python
from comfy_script.runtime import *
load()  # connect to the server
from comfy_script.runtime.nodes import *

with Workflow():
    model, clip, vae = CheckpointLoaderSimple('juggernautXL.safetensors')
    for cfg in (4, 5, 6):                      # a sweep the GUI can't express
        pos = CLIPTextEncode(prompt, clip)
        neg = CLIPTextEncode('', clip)
        latent = EmptyLatentImage(1024, 1024)
        out = KSampler(model, seed, 30, cfg, 'euler', 'normal', pos, neg, latent)
        SaveImage(VAEDecode(out, vae), f'sweep_cfg{cfg}')
```

Node classes are generated from the connected server's node registry, so custom nodes appear automatically.

## 3. The native API route

1. In the ComfyUI frontend: **Workflow → Export (API)** — produces the minimal API-format JSON (distinct from the full GUI-format save).
2. POST it to `http://<host>:8188/prompt`; track progress over the WebSocket (`/ws`); fetch outputs from `/history` + `/view`.
3. Parametrize by editing the JSON's input fields (seed, prompt text, filenames) before each POST — the node IDs are stable, so a thin wrapper dict-update is all it takes.
4. **comfy-cli** wraps the same flow for shell use: run workflows from the command line, convert GUI↔API formats, manage models and the queue.

This is what the hosted wrappers (ComfyDeploy, RunComfy serverless, Baseten guides) productize — typed inputs over an API-format workflow. If you'll eventually deploy, building around API-format JSON from day one is the smooth path. *(Community-strong — ViewComfy's production-API guide is the canonical writeup.)*

## 4. diffusers as the code-first alternative

For multi-stage and mixed-model work, diffusers trades the node ecosystem for testable Python:

```python
base   = StableDiffusionXLPipeline.from_pretrained(...)          # compose (SDXL control stack available via ControlNet pipelines)
refine = Flux2KleinPipeline.from_pretrained(...)                  # render quality
img  = base(prompt, ...).images[0]
img  = refine(prompt=prompt, image=img, strength=0.3).images[0]   # pixels by construction — no VAE mismatch possible
```

Multi-stage support is first-class (SDXL base+refiner ensemble, ControlNet and IP-Adapter pipelines, PAG variants). What you give up: the detailer/tiled-upscale node ecosystem — you reimplement or skip those stages. The usual split: **diffusers for reproducible pipelines and services; ComfyUI for craft iteration.**

## 5. Pro conventions

- **Native Subgraphs** (official since Aug 2025, frontend ≥ 1.24.3): package each stage — base / refine / detail / upscale — as a nested, reusable subgraph node. This replaced the old group-node convention and is how the large Civitai workflows are organized. One mega-workflow with toggleable stage-subgraphs beats five separate files.
- **rgthree-comfy** is the de-facto plumbing standard: **Context** pipes (one cable carrying model/clip/vae/conditioning between stages), **Fast Muter** (bypass stages without rewiring), **Power Lora Loader** (stacks with per-LoRA toggles), and the **global Seed** node (one seed reused across all stages — the cheap way to honor the same-seed discipline).
- **Wildcards / dynamic prompts at scale:** Impact Pack's `{a|b|c}` + `__wildcard__` grammar, or `adieyal/comfyui-dynamicprompts` (random *and combinatorial* modes — the latter enumerates every combination, which is what you want for systematic coverage). The same wildcard harness ports across families — a published Civitai pack runs it on Pony, SDXL, Illustrious, Flux, Qwen, and Z-Image-Turbo identically.
- **Batch QC** is ad-hoc in practice *(thin sourcing — no dominant named tool)*: auto-incrementing seeds via the API, grid outputs (XY plot nodes) for human cull, and keeping every stage's intermediate image saved so a bad final can be diagnosed to a stage instead of rerun blind.
- **Queue automation:** comfy-cli or raw `/prompt` with the WebSocket for monitoring; on a fixed reference set, FLUX.2 [klein] 9B KV-caching makes repeated-reference batches ~1.5–3× faster (see the flux-2 skill).
