# ComfyUI as a serverless endpoint

Running ComfyUI behind a RunPod serverless endpoint is the programmatic path. This file covers the ways it differs from the interactive pod that everyone starts with.

1. [The four moving pieces](#1-the-four-moving-pieces)
2. [API format vs UI format](#2-api-format-vs-ui-format)
3. [Dispatch and polling](#3-dispatch-and-polling)
4. [Scaling and cost shape](#4-scaling-and-cost-shape)
5. [Failure modes](#5-failure-modes)

---

## 1. The four moving pieces

A serverless setup has four separate pieces. Most confusion starts when you change one piece without understanding how it relates to the others:

| Piece | What it is | How you change it |
|---|---|---|
| **Endpoint** | The addressable service; owns scaling config | Update workers/scaling on the endpoint |
| **Template** | Binds the endpoint to a container image and env | Swap the image tag on the template |
| **Image** | ComfyUI plus custom nodes plus `extra_model_paths.yaml` | Rebuild and push, then point the template at the new tag |
| **Models** | Files on the network volume | Upload/sync — **no rebuild needed** |

This separation exists for a reason: **weights are too big to bake into an image**. The image carries code and config, and the volume carries the weights. In practice, adding a LoRA only requires an upload, while adding a custom node requires a rebuild.

**Rollback is a template edit, not a rebuild — but a template swap does not drain warm workers.** Point the template back at the previous image tag. Only *new* workers start from that tag. Workers that are already warm keep running the old image until they scale to zero or you terminate them `[community — live deploy 2026-08; re-verify]`. So after any swap, verify the image a worker is actually running, not what the endpoint config says. Keep your old tags around, because they are your undo mechanism. Endpoints themselves cost nothing while idle, so one endpoint per deployable unit beats mutating a shared one.

**Building a current worker image.** RunPod's published worker-comfyui base images lag new model releases, so a recent model usually needs a rebuild from source `[community — live deploy 2026-08; re-verify]`. Build with `--target base`. The default downloader stage silently bakes a ~17 GB FLUX checkpoint into the image `[community — live deploy 2026-08; re-verify]`. Two API gotchas sit next to this. The REST API silently drops `gpuTypeIds` it does not recognise, so read the endpoint back and check what it actually got `[community — live deploy 2026-08; re-verify]`. And set `minCudaVersion` to match the CUDA build your image's torch was compiled against, or workers land on hosts that cannot run it.

**Mount root.** Serverless mounts the volume at `/runpod-volume/` by default, though an endpoint can be configured to mount elsewhere. Either way, the image's `extra_model_paths.yaml` should declare **both** roots so that the same image works in both contexts. See `volume-and-models.md` §1.

---

## 2. API format vs UI format

ComfyUI has two JSON serialisations, and they are not interchangeable.

| | UI format | API format |
|---|---|---|
| Saved by | *Save* / *Export* in the canvas | *Save (API Format)* |
| Contains | Nodes, links, positions, groups, UI state | The prompt graph only — node ids, class types, inputs |
| Loads in the canvas | Yes | No |
| Accepted by the endpoint | **No** | **Yes** |

Feeding UI-format JSON to an endpoint produces a validation error that does not obviously say "wrong format." When a workflow that works in the UI fails over the API, check this first.

**Building graphs programmatically** is the better path once you are generating at volume. Construct the API-format dict in code, and inject the model filenames and `clip_type` **from your manifest** so that graphs cannot drift from the volume. Parameterise the handful of values that vary per job — prompt, seed, resolution, length, LoRA and strength — and keep everything else fixed.

**Reference images** go base64-encoded in the request payload, and the `LoadImage` node in the graph must reference the matching filename. A mismatch between the encoded filename and the filename the node expects is a common and confusing failure. The job is not rejected at dispatch; it runs and then fails inside ComfyUI.

---

## 3. Dispatch and polling

**Use `/run` and poll `/status/{id}`. Do not use `/runsync` for generation.**

`/runsync` holds the connection open until the result is ready. That is fine for short jobs, but wrong for image pipelines and anything involving video. When the job outlives the connection window, you get a connection reset that looks like the endpoint died. The endpoint did not die, and the job may even have completed. `/run` returns an id immediately, so you can poll until the job reaches a terminal state.

A dispatch loop that behaves:

- Submit the job, get the id, and poll on an interval of a few seconds.
- Treat only terminal states as done. Keep polling through the queued and in-progress states.
- **Read the response body on failure.** ComfyUI validation errors — missing model file, unknown node class, bad input — arrive *inside* the status payload, not as an HTTP error. An endpoint that looks healthy while every job fails is almost always a workflow/volume mismatch, and the body tells you which mismatch it is.
- **Bound concurrency to max workers.** In-flight requests beyond the worker count just sit in the queue, and they make timing hard to reason about.

**Cache by config hash.** Hash each job's resolved configuration and skip re-running jobs whose configuration has not changed. On a batch of hundreds, this is the difference between iterating and waiting. It also makes a re-run after a partial failure cheap.

**Keep a single-job probe script.** It submits one job and prints the raw response. When the endpoint misbehaves, running the probe is far faster than reasoning about a batch, and it is the first thing to reach for after any image or volume change.

---

## 4. Scaling and cost shape

Workers bill **per second while running**. Once workers spin down, idle capacity costs nothing. That is why an abandoned endpoint is safe in a way that an abandoned pod is not.

| Knob | Trade |
|---|---|
| **Max workers** | Throughput vs concurrent spend. Match your dispatch concurrency |
| **Idle timeout** | Seconds a warm worker survives after a job. Higher = fewer cold starts, more idle cost |
| **FlashBoot** | Pre-warms container layers; clearly reduces cold start |
| **Queue-delay scaler** | Max seconds queued before adding a worker. Lower = more responsive, more workers |

**Cold start for ComfyUI is dominated by model loading, not container start.** A multi-file DiT plus a large text encoder means reading tens of gigabytes from the volume into VRAM. Three consequences are worth planning around:

- **Idle timeout matters more here than for a small model.** Paying for a few idle seconds beats re-loading 30 GB.
- **Batch work into fewer, longer jobs** where you can. This amortises the model load across many generations rather than paying it per request.
- **Quantised weights cut cold start as well as VRAM**, because there is simply less data to read.

---

## 5. Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Connection reset shortly after dispatch | `/runsync` against a long job | `/run` + poll `/status/{id}` |
| Every job fails; endpoint looks healthy | Workflow references a filename the volume doesn't have | Read the `/status` body; list the volume; reconcile manifest and graph |
| Works in the UI, fails over the API | UI-format JSON submitted | Re-export as API format |
| "Model not found" only in serverless | `runpod_volume` block missing from `extra_model_paths.yaml` | Declare both roots identically |
| Red node / graph won't load | Custom node in the graph isn't in the image | Rebuild the image with the node pinned |
| `LoadImage` file not found | Base64 filename ≠ what the node references | Align the encoded name with the graph |
| Garbage base64, all jobs fail | Source images are Git LFS pointer stubs, not real files | `git lfs pull` before encoding |
| Workers never warm | Max workers at zero, or no GPU free in the volume's DC | Check endpoint config; consider another DC when placing the volume |
| Probes still hit the old image after a template swap | Warm pool is pinned to the old image; the account worker quota may also be fully claimed by another endpoint | Terminate the warm workers, or create a fresh endpoint `[community — live deploy 2026-08; re-verify]` |
| Workers sit "throttled" | Account-wide worker quota exhausted — not GPU scarcity | Check quota across all endpoints before hunting for capacity `[community — live deploy 2026-08; re-verify]` |
| First job slow, rest fast | Normal cold start — model loading | Raise idle timeout; enable FlashBoot; batch work |
| Output missing a modality (e.g. silent video) | A post stage or muxing step dropped it, or a decode branch isn't wired | Verify each output branch explicitly — see the smoke test in SKILL.md |
