# comfyui-on-runpod — authoring intent and sources

**Authored 2026-08-13.** The suite's first pure-infrastructure skill: not a model, and not model-agnostic *craft* like `image-production-workflows`, but the deployment layer underneath both.

## Why it exists

The goal stated by the user: *"how we work with and manage the virtual disk is pretty important because that's where all the models need to sit so that a fresh instance of comfyui works with the workflows we build out of the box."*

That sentence is the whole skill. Everything in it serves one outcome — a fresh ComfyUI instance, pointed at a network volume, opens a workflow JSON and every node resolves.

## The scoping decision — what NOT to write

**RunPod publishes its own skills, and they are better than assumed.** I initially told the user "nothing covers ComfyUI," which was wrong and worth remembering as a lesson: check the vendor's own material before scoping.

`runpod/runpod-plugins-official` (the `runpod/skills` repo redirects there) ships six skills — `runpod` (router), `runpod-usage`, `runpodctl`, `runpod-mcp`, `flash`, `companion-clis` — plus ~25 golden paths including:

- **`02-comfyui-pod`** — ComfyUI on a pod, two variants (from-scratch vs the prebuilt `runpod/comfyui` image), live-verified 2026-07-07
- **`25-bake-vs-mount`**, **`20-model-caching-endpoint`**, **`21-storage-tiers`**, **`07-network-volume-handoff`**
- `runpodctl/evals/pod-auto-terminate` — which is where `--terminate-after` surfaced

So the skill **routes rather than restates**: provisioning, GPU choice, pod lifecycle, networking and cost-guard mechanics all defer to RunPod's skills via an explicit table. What remains is the genuinely uncovered middle layer.

## What the skill owns

Everything RunPod's material doesn't touch because it isn't ComfyUI-specific:

1. **The dual mount root** — `/workspace/` on a pod, `/runpod-volume/` on serverless, `s3://<volume-id>/` from local — and `extra_model_paths.yaml` declaring **both blocks with identical keys**. This is the spine.
2. **Volume layout keyed by loader node** — the only organising principle that survives model churn.
3. **LoRA foldering by base model, with a separate `compat` graph** as the real dependency truth.
4. **The manifest pattern** — one declarative file driving both downloads and workflow construction, which is *the* mechanism behind "works out of the box."
5. **Getting weights there** — CPU pods and the S3 API, never a GPU pod, never `wget`.
6. **ComfyUI as a serverless endpoint** — API-format vs UI-format JSON, `/run` + poll rather than `/runsync`, base64 inputs, validation errors arriving inside the status body.
7. **Smoke tests**, including checking every output branch (a video model with audio can emit a perfect silent file).

## Sources

**Generalised from `/Users/ryannel/Workspace/video-generation`** — the user's production studio, and the operational source of truth:

| Source file | What it gave |
|---|---|
| `docs/volume-layout.md` | "The One Fact" — the three mount roots; the canonical tree; LoRA foldering + `compat`; placement table |
| `docker/studio/extra_model_paths.yaml` | The real dual-block config, verbatim — incl. `text_encoders`→`clip` aliasing, the multi-path `diffusion_models` scalar, `vae_approx` |
| `models.yaml` | The manifest schema — `stack`/`models`/`custom_nodes`/`assets`, and `files[].{repo,filename,dest,rename}` plus `clip_type` |
| `docs/deployment.md` | The four moving pieces (endpoint/template/image/models); `/run`+poll vs `/runsync`; the deployment failure table; S3 endpoint form |
| `docs/hardware-guide.md` | Two-pod strategy, cost-control framing — **prices deliberately not carried over** |
| `.agents/rules/cost-gate.md`, `runpod-secure-cloud.md` | Adopted as the operating protocol, and copied to `skill-testbed` |

**Official (RunPod):** golden path 02 for the acceptance bar (port `8188` at creation, bind `0.0.0.0`, ≥16 GB, network volume, `--terminate-after`), the DC-lock constraint, ports-fixed-at-creation, and that the proxy URL is public and unauthenticated.

## Deliberate omissions

- **No GPU prices anywhere.** They go stale within weeks and are model-specific. `runpod-usage` owns the general question; each model skill owns its own requirement; observed numbers belong in `skill-testbed/validations/`.
- **No provisioning commands.** Routed to `runpodctl`/`runpod-mcp` rather than duplicated and left to rot.
- Dated material in the source docs (Flux-era pipelines, Wan 2.1, the retired PuLID/InsightFace stack) was **not** carried over.

## Status

**Entirely unvalidated.** Written from a working production configuration plus RunPod's docs, but nothing in it has been run end to end from this repo. The dual-mount-root claim is the top item in `skill-testbed/validations/README.md`'s priority queue.
