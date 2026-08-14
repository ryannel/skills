# ComfyUI as a serverless endpoint

Running ComfyUI behind a RunPod serverless endpoint — the programmatic path, and where it differs from the interactive pod everyone starts with.

1. [The four moving pieces](#1-the-four-moving-pieces)
2. [API format vs UI format](#2-api-format-vs-ui-format)
3. [Dispatch and polling](#3-dispatch-and-polling)
4. [Scaling and cost shape](#4-scaling-and-cost-shape)
5. [Failure modes](#5-failure-modes)

---

## 1. The four moving pieces

Changing one without understanding the others is where most confusion starts.

| Piece | What it is | How you change it |
|---|---|---|
| **Endpoint** | The addressable service; owns scaling config | Update workers/scaling on the endpoint |
| **Template** | Binds the endpoint to a container image and env | Swap the image tag on the template |
| **Image** | ComfyUI plus custom nodes plus `extra_model_paths.yaml` | Rebuild and push, then point the template at the new tag |
| **Models** | Files on the network volume | Upload/sync — **no rebuild needed** |

The separation is the point: **weights are too big to bake into an image**, so the image carries code and config while the volume carries weights. Adding a LoRA is an upload; adding a custom node is a rebuild.

**Rollback is a template edit, not a rebuild.** Point the template back at the previous image tag and the endpoint picks it up. Keep old tags around — that is your undo.

**Mount root.** Serverless mounts the volume at `/runpod-volume/` by default, though an endpoint can be configured to mount elsewhere. Either way, the image's `extra_model_paths.yaml` should declare **both** roots so the same image works in both contexts — see `volume-and-models.md` §1.

---

## 2. API format vs UI format

ComfyUI has two JSON serialisations and they are not interchangeable.

| | UI format | API format |
|---|---|---|
| Saved by | *Save* / *Export* in the canvas | *Save (API Format)* |
| Contains | Nodes, links, positions, groups, UI state | The prompt graph only — node ids, class types, inputs |
| Loads in the canvas | Yes | No |
| Accepted by the endpoint | **No** | **Yes** |

Feeding UI-format JSON to an endpoint produces a validation error that doesn't obviously say "wrong format," so check this first when a workflow that "works in the UI" fails over the API.

**Building graphs programmatically** is the better path once you're generating at volume: construct the API-format dict in code, injecting model filenames and `clip_type` **from your manifest** so graphs cannot drift from the volume. Parameterise the handful of values that vary per job — prompt, seed, resolution, length, LoRA and strength — and keep the rest fixed.

**Reference images** go base64-encoded in the request payload, and the `LoadImage` node in the graph must reference the matching filename. A mismatch between the encoded filename and what the node expects is a common and confusing failure — the job runs and fails inside ComfyUI rather than being rejected at dispatch.

---

## 3. Dispatch and polling

**Use `/run` and poll `/status/{id}`. Do not use `/runsync` for generation.**

`/runsync` holds the connection open for the result, which is fine for short jobs and wrong for image pipelines and anything video. When the job outlives the window you get a connection reset that looks like the endpoint died — it didn't, and the job may even have completed. `/run` returns an id immediately; poll until terminal.

A dispatch loop that behaves:

- Submit, get the id, poll on an interval of a few seconds.
- Treat only terminal states as done; keep polling through queued and in-progress.
- **Read the response body on failure.** ComfyUI validation errors — missing model file, unknown node class, bad input — arrive *inside* the status payload, not as an HTTP error. An endpoint that looks healthy while every job fails is almost always a workflow/volume mismatch, and the body says which.
- **Bound concurrency to max workers.** More in-flight requests than workers just sit in the queue and make timing hard to reason about.

**Cache by config hash.** Hash each job's resolved configuration and skip re-running unchanged jobs. On a batch of hundreds this is the difference between iterating and waiting, and it makes a re-run after a partial failure cheap.

**Keep a single-job probe script.** One shot, raw response printed. When the endpoint misbehaves it is far faster than reasoning about a batch, and it's the first thing to reach for after any image or volume change.

---

## 4. Scaling and cost shape

Workers bill **per second while running**. Idle workers cost nothing once spun down, which is why an abandoned endpoint is safe in a way an abandoned pod is not.

| Knob | Trade |
|---|---|
| **Max workers** | Throughput vs concurrent spend. Match your dispatch concurrency |
| **Idle timeout** | Seconds a warm worker survives after a job. Higher = fewer cold starts, more idle cost |
| **FlashBoot** | Pre-warms container layers; materially reduces cold start |
| **Queue-delay scaler** | Max seconds queued before adding a worker. Lower = more responsive, more workers |

**Cold start for ComfyUI is dominated by model loading, not container start.** A multi-file DiT plus a large text encoder is tens of gigabytes read from the volume into VRAM. Consequences worth planning around:

- **Idle timeout matters more here than for a small model.** Paying a few idle seconds beats re-loading 30 GB.
- **Batch work into fewer, longer jobs** where you can — amortise the load across many generations rather than paying it per request.
- **Quantised weights cut cold start as well as VRAM**, since there is simply less to read.

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
| First job slow, rest fast | Normal cold start — model loading | Raise idle timeout; enable FlashBoot; batch work |
| Output missing a modality (e.g. silent video) | A post stage or muxing step dropped it, or a decode branch isn't wired | Verify each output branch explicitly — see the smoke test in SKILL.md |
