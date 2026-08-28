# Workflows as Code — ComfyScript, the API route, comfy-cli, diffusers, and pro conventions

This file covers how to take a working graph from "I click Queue" to a parametrized, batched, scriptable production setup. It also covers the conventions that professional ComfyUI users layer on top.

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

`Chaoses-Ib/ComfyScript` is **alive and current**. Version 0.6.0 (Nov 2025) added ComfyUI v3-schema support and Python 3.14, and v0.6.1 followed. It is still a **single-maintainer project, so pin versions in production** `[official — Chaoses-Ib/ComfyScript]`.

It has three modes:
- **Virtual mode.** Your Python builds workflow JSON and submits it to a ComfyUI server, local or remote. This is the default for production: the server stays the executor, and your script is the orchestrator.
- **Real mode.** Nodes run as plain Python functions in-process. Use this for research and optimization loops, where you want Python control flow *between* node calls.
- **Transpiler.** This converts an existing workflow JSON *into* ComfyScript Python. It is the migration path: build in the GUI, transpile, then parametrize.

Here is the shape of it in virtual mode:

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

1. In the ComfyUI frontend, choose **Workflow → Export (API)**. This produces the minimal API-format JSON, which is distinct from the full GUI-format save.
2. POST that JSON to `http://<host>:8188/prompt`. Track progress over the WebSocket (`/ws`), and fetch outputs from `/history` + `/view`.
3. Parametrize by editing the JSON's input fields (seed, prompt text, filenames) before each POST. The node IDs are stable, so a thin wrapper that updates the dict is all it takes.
4. **comfy-cli** wraps the same flow for shell use. It runs workflows from the command line, converts GUI↔API formats, and manages models and the queue.

This is the flow that the hosted wrappers (ComfyDeploy, RunComfy serverless, Baseten guides) productize: typed inputs over an API-format workflow. If you will eventually deploy, build around API-format JSON from day one, because that is the smooth path `[community — ViewComfy production-API guide; strong]`. Deploying that JSON on rented GPUs is [`comfyui-on-runpod`](../../comfyui-on-runpod/)'s territory, not this file's.

## 4. diffusers as the code-first alternative

For multi-stage and mixed-model work, diffusers trades the node ecosystem for testable Python:

```python
base   = StableDiffusionXLPipeline.from_pretrained(...)          # compose (SDXL control stack available via ControlNet pipelines)
refine = Flux2KleinPipeline.from_pretrained(...)                  # render quality
img  = base(prompt, ...).images[0]
img  = refine(prompt=prompt, image=img, strength=0.3).images[0]   # pixels by construction — no VAE mismatch possible
```

Multi-stage support is first-class: the SDXL base+refiner ensemble, ControlNet and IP-Adapter pipelines, and PAG variants are all built in. What you give up is the detailer and tiled-upscale node ecosystem, so you have to reimplement those stages or skip them. The usual split is **diffusers for reproducible pipelines and services, ComfyUI for craft iteration.**

## 5. Pro conventions

- **Native Subgraphs** have been in ComfyUI core since Aug 2025 (frontend ≥ 1.24.3). Package each stage — base / refine / detail / upscale — as a nested, reusable subgraph node. Subgraphs replaced the old group-node convention, and they are how the large Civitai workflows are organized. One mega-workflow with toggleable stage-subgraphs beats five separate files.
- **rgthree-comfy** is the de-facto plumbing standard. Its **Context** pipes carry model/clip/vae/conditioning between stages on one cable. **Fast Muter** bypasses stages without rewiring. **Power Lora Loader** stacks LoRAs with per-LoRA toggles. The **global Seed** node reuses one seed across all stages, which is the cheap way to honor the same-seed discipline.
- **Wildcards / dynamic prompts at scale:** use Impact Pack's `{a|b|c}` + `__wildcard__` grammar, or `adieyal/comfyui-dynamicprompts`. The latter has random *and combinatorial* modes; combinatorial mode enumerates every combination, which is what you want for systematic coverage. The same wildcard harness ports across model families. A published Civitai pack runs it on Pony, SDXL, Illustrious, Flux, Qwen, and Z-Image-Turbo identically.
- **Batch QC** has named tooling for *comparison*, and nothing for *judgement*. For comparison there is **SwarmUI's Grid Generator** (built in, with infinite axes; its "Web Page" output is an interactive viewer showing up to 4 axes at a time rather than a frozen grid image), Efficiency Nodes' `XY Input: LoRA Plot` inside ComfyUI, and rgthree's `Image Comparer` wipe-slider for final head-to-heads. Around those tools, the usual practice holds: auto-increment seeds via the API, and save every stage's intermediate image so a bad final can be diagnosed to a stage instead of rerun blind. What no tool does is stop you knowing which cell is which. Grid axes are labelled by design, so add a blind pass wherever the call is close. The protocol is in [`character-lora-training/references/evaluation-and-tooling.md`](../../character-lora-training/references/evaluation-and-tooling.md).
- **Queue automation:** use comfy-cli or raw `/prompt`, with the WebSocket for monitoring. On a fixed reference set, FLUX.2 [klein] 9B KV-caching makes repeated-reference batches ~1.5–3× faster ([`flux-2`](../../flux-2/)).
