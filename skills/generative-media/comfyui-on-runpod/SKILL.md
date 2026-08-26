---
name: comfyui-on-runpod
description: >
  Run ComfyUI on RunPod so that a fresh instance loads your workflows and finds every model **out of the box** — the layer between RunPod's platform skills and the model skills. Use this whenever the user is deploying, debugging or budgeting ComfyUI on rented GPUs, even obliquely: laying out a network volume, writing `extra_model_paths.yaml`, deciding where a checkpoint / text encoder / VAE / LoRA / upscaler actually goes, getting tens of gigabytes of weights onto a volume without burning GPU hours, keeping a model manifest so a new pod reproduces the old one, choosing between an interactive pod and a serverless endpoint for ComfyUI, deploying API-format workflow JSON and polling it correctly, smoke-testing an install before spending real time on it, or debugging the classics — "ComfyUI can't find my model", "it works in the studio but breaks in serverless", "the proxy URL 502s", "my LoRA isn't in the dropdown", "why did my pod bill all night". Owns the **ComfyUI-specific** layer only: for provisioning, GPU selection, pod lifecycle, `runpodctl`/MCP commands and networking, it routes to RunPod's own official skills rather than restating them.
---

# ComfyUI on RunPod

The goal this skill serves: **a fresh ComfyUI instance, pointed at your network volume, opens your workflow JSON and every node resolves. No missing-model dialogs, no re-downloads, no manual fixups.** Everything below works toward that goal.

## What this owns, and what it doesn't

RunPod publishes its own skills, and they are good. Do not restate them — route.

| Question | Where it belongs |
|---|---|
| Provisioning a pod, ports, SSH, proxy URLs, `--terminate-after` | **`runpod`** router → `runpodctl` / `runpod-mcp` |
| Which GPU, how much VRAM, pods vs serverless *in general* | **`runpod-usage`** |
| Getting ComfyUI *running at all* on a pod | **`runpod`** golden path 02 — prebuilt `runpod/comfyui` image is the default |
| Bake into the image vs mount from a volume | **`runpod`** golden path 25 |
| HuggingFace / AWS / Docker CLI setup | **`companion-clis`** |
| **Where models live so ComfyUI finds them** | **here** |
| **`extra_model_paths.yaml` and the dual mount root** | **here** |
| **Model manifests and reproducible volumes** | **here** |
| **ComfyUI as a serverless endpoint, API-format workflows** | **here** |
| Model-specific files and settings | the model skill — [`wan-2-2`](../wan-2-2/), [`minimax-h3`](../minimax-h3/), [`z-image`](../z-image/), … |
| Multi-stage pipeline design — which stage does what, denoise bands, mixing models, the decode-to-pixels handoff | [`image-production-workflows`](../image-production-workflows/) — that skill assumes the compute already runs; this one is how it gets there |
| **Which model to run in the first place, and which skills the job needs** | [`generative-media-atlas`](../generative-media-atlas/) — rankings by job, the elimination ladder, and the install commands for this suite and RunPod's own skills |

---

## The one rule that changes everything

**The volume is the contract, and `extra_model_paths.yaml` is how ComfyUI reads it — under *two different roots*.**

The same network volume is mounted at a different path depending on where ComfyUI is running:

| Context | Volume root |
|---|---|
| Interactive pod | **`/workspace/`** |
| Serverless worker | **`/runpod-volume/`** |
| S3 API from your laptop | **`s3://<volume-id>/`** |

So `extra_model_paths.yaml` must declare **both roots with identical key sets**. Miss one and you get the single most confusing failure in this stack: **it works in the studio and breaks in serverless**, with a model-not-found error for a file you can see on the volume.

**Verified on live infrastructure 2026-08-13.** A serverless worker enumerated exactly the volume's `models/vae/` contents. RunPod's docs are explicit too: serverless mounts at `/runpod-volume`, pods at `/workspace`.

> **The trap that makes people disbelieve this.** A RunPod **template** carries a `volumeMountPath` field, and it commonly reads `/workspace` — *including on templates used by serverless endpoints.* But that field is **pod-only, and serverless ignores it**. Serverless templates do not expose a mount-path option at all, because the path is fixed and cannot be changed. So reading `volumeMountPath: /workspace` on a serverless template and concluding the second block is unnecessary is exactly the wrong conclusion — and it is an easy one to reach from the console.

```yaml
network_volume:            # interactive pod
  base_path: /workspace/
  checkpoints: models/checkpoints/
  clip: models/clip/
  text_encoders: models/clip/          # ← see the note below
  clip_vision: models/clip_vision/
  controlnet: models/controlnet/
  diffusion_models: |                  # ← two paths, one key
               models/diffusion_models/
               models/unet/
  embeddings: models/embeddings/
  ipadapter: models/ipadapter/
  loras: models/loras/
  sams: models/sams/                   # ← Impact Pack SAMLoader
  ultralytics_bbox: models/ultralytics/bbox/   # ← Impact Pack detailer detectors
  ultralytics_segm: models/ultralytics/segm/
  upscale_models: models/upscale_models/
  vae: models/vae/
  vae_approx: models/vae_approx/       # ← TAE preview decoders

runpod_volume:             # serverless worker — SAME KEYS, different base
  base_path: /runpod-volume/
  # … identical body …
```

Three details in there that cost people hours:

- **`text_encoders` and `clip` can point at the same directory.** Modern DiT models load their encoder through a `CLIPLoader` that searches `text_encoders`. Older configs only declare `clip`. Declare both at one path, and either style resolves.
- **`diffusion_models` takes multiple paths** as a block scalar. `models/unet/` is the legacy name and some downloads still land there.
- **`vae_approx` is not optional** if you want fast previews. It's where TAE decoders live (for example H3's `taeh3.safetensors`).

Deploy this file to ComfyUI's install directory on boot, not by hand. On a pod that is typically `…/ComfyUI/extra_model_paths.yaml`. In a serverless image, bake it in.

---

## Volume layout

One canonical tree, keyed by **which loader node reads it**. That is the only organising principle that survives contact with ComfyUI.

```
/workspace/                        ← (= /runpod-volume/ in serverless)
└── models/
    ├── diffusion_models/          ← UNETLoader / Load Diffusion Model      [core]
    ├── checkpoints/               ← CheckpointLoaderSimple (all-in-one)    [core]
    ├── clip/                      ← CLIPLoader (text encoders)             [core]
    ├── vae/                       ← VAELoader                              [core]
    ├── upscale_models/            ← UpscaleModelLoader                     [core]
    ├── loras/                     ← LoraLoader — foldered by base model    [core]
    │   ├── <base-a>/
    │   ├── <base-b>/
    │   └── _shared/               ← works on more than one base
    ├── vae_approx/                ← TAE preview decoders        [only if you want previews]
    ├── ultralytics/  sams/        ← Impact Pack detailer detectors + SAM   [if detail-passing]
    ├── insightface/               ← PuLID / InstantID identity nodes — NOT where detailers look
    ├── controlnet/                ← ControlNetLoader
    └── ipadapter/  clip_vision/  embeddings/  style_models/
```

**Create the `[core]` six. Add the rest when a node actually needs them.** A single production ComfyUI-on-RunPod deployment external to this repo, inspected on 2026-08-13, had exactly the core six plus `insightface/`. It had no `controlnet/`, `vae_approx/`, `ipadapter/`, `clip_vision/`, `embeddings/` or `style_models/`, because nothing in its pipelines loaded them. An absent directory is not a fault. A directory absent from `extra_model_paths.yaml` *while a node needs it* is a fault. Declare the keys generously in the yaml, create the folders lazily.

**Fold LoRAs by base model.** `LoraLoader` shows the subfolder as a path prefix in the dropdown, so `z-image-turbo/amy_v9/…` tells you at a glance what it belongs to. And when you retire a base model, the folder tells you what dies with it.

**But the folder is the human view, not the truth.** A LoRA trained on a base often loads on its distilled sibling at reduced strength. Record the real dependency in your manifest (`compat: [base, turbo]`) and let the folder be its *primary home*. A workflow builder can then check compatibility before wiring a LoRA, and skip incompatible ones silently. That way, one scene definition renders correctly under either base.

**Trainer pods mount this same volume**, and their artifacts get assigned homes too. A volume-resident HF cache lives at `/workspace/huggingface/`, and datasets and run outputs sit beside (not inside) `models/`. Budget for base weights living on the volume twice — in diffusers format for training and single-file for inference. See "Training on the same volume" in the reference below.

Full layout rationale, placement table and LoRA conventions: **`references/volume-and-models.md`**.

---

## The manifest — how a fresh volume becomes the old volume

The thing that makes "works out of the box" reproducible is a **declarative model manifest** checked into your repo, not a folder someone populated by hand.

Give each model an entry recording what it is, which files it needs, where each file goes, and what it's compatible with:

```yaml
stack: [z-image-base, z-image-turbo, …]     # what's active right now

models:
  z-image-base:
    description: "6B S3-DiT, non-distilled. Training + inference base."
    architecture: z-image-base
    unet_filename: z_image_bf16.safetensors
    clip_filename: qwen_3_4b_fp8_mixed.safetensors
    clip_type: lumina2                       # the CLIPLoader `type` argument
    vae_filename: ae.safetensors
    files:
      - repo: Comfy-Org/z_image
        filename: split_files/diffusion_models/z_image_bf16.safetensors
        dest: /workspace/models/diffusion_models/
        rename: z_image_bf16.safetensors
```

What this buys you:

- **Rebuild a volume from nothing** with one command, in a known-good state.
- **Workflow builders read the same file.** `unet_filename`, `clip_type` and `vae_filename` are exactly the values a graph needs, so workflows and downloads can't drift apart.
- **Answer "if I remove X, what breaks?"** by querying `compat`, instead of guessing.
- **Renames are explicit.** Upstream repos nest files under `split_files/…` and use long names. `rename` pins the flat name your workflows reference.

---

## Getting the weights there without burning GPU hours

Model downloads are I/O, not compute. **Never do them on a GPU pod.**

| Route | Use when |
|---|---|
| **CPU pod** running `hf download` straight to the mounted volume | Bulk population. Fastest link, no GPU billing. The default |
| **S3 API** — `aws s3 cp/sync` to `s3://<volume-id>/…` with `--endpoint-url https://s3api-<dc>.runpod.io/` | Pushing files from your laptop; auditing what's actually on the volume without booting anything |
| `hf download` on the GPU pod itself | Only for a small file you discovered mid-session |

Two rules worth stating plainly:

- **Use `hf download` (or the S3 API), never `wget`.** You get resume, parallel chunks, and the correct revision. A 20 GB `wget` that dies at 90% is a wasted half hour.
- **The volume is pinned to one datacenter.** Your pod must be created in that same DC, which narrows GPU availability. Check the GPU exists there *before* you plan around it. This is the most common reason a "just spin one up" plan stalls.

---

## Pod or serverless?

Both run ComfyUI. They fail differently, and they bill very differently.

| | Interactive pod | Serverless endpoint |
|---|---|---|
| Bills | Per second **while it exists**, whether or not you're using it | Per second **while a request runs**; scales to zero |
| Runaway risk | **High** — a forgotten pod bills all night | Low — a forgotten endpoint idles free |
| Good for | Building and debugging graphs in the web UI, LoRA training | Batch generation, anything programmatic |
| Cold start | Once, then it's warm | Per scale-up; mitigate with FlashBoot and idle timeout |
| Mount root | `/workspace/` | `/runpod-volume/` |

**Default: build interactively, run in serverless.** The web UI is where graphs get made. The endpoint is where they get executed a thousand times.

**Cost guards that actually work** (details in RunPod's skills — this is the ComfyUI-shaped summary):

- **Two timers on every interactive pod: `--stop-after` at the session ceiling, `--terminate-after` as the backstop.** Both live on `pod create` and do different things: stop *pauses* the pod — GPU billing ends, `runpodctl pod start <id>` resumes it in about a minute — while terminate *deletes* it. Neither alone is right for interactive work: stop-only leaves a paused pod billing its volume disk ($0.20/GB-mo) indefinitely, and terminate-only kills a live session mid-generation the moment the clock runs out. Set the stop a comfortable session length out (4–8 h) and the terminate a day out; hitting the ceiling then costs a one-minute resume instead of lost work. Two caveats that make the volume-as-contract rule matter here too: a stop **wipes the container disk** (the template re-initialises it on resume — anything you installed outside the volume is gone), and a resume is not guaranteed the same GPU if stock ran out, in which case you recreate from the volume in minutes. For unattended batch pods, terminate-only at expected runtime plus margin is right — there is nothing to resume. Verified against `runpodctl 2.3.0` on 2026-08-23.

  > **Use `runpodctl pod create`, not `runpodctl create pod`.** Both exist in `runpodctl` 2.3.0, and they are different command surfaces. The legacy verb-noun form (`create pod`) takes `--gpuType`/`--networkVolumeId`/`--imageName` and has **no cost guard at all** — no `--terminate-after`, no `--stop-after`. The modern noun-verb form (`pod create`) takes `--gpu-id`/`--network-volume-id`/`--image`, and it is the one that carries the guards. Reach for the wrong one, and you will conclude the flag doesn't exist and create an unguarded pod. Verified against `runpodctl 2.3.0-be4ced4` on 2026-08-13. Check with `runpodctl pod create --help` before a first run on a new machine.
  >
  > **And the CLI version matters more than any version floor stated here can.** RunPod's own skills describe a priced `gpu list` — per-GPU `securePricePerHr`, a per-datacenter availability breakdown — that 2.3.0 does not emit. Run `runpodctl update` to close the gap. Until then, the working fallback is `runpodctl datacenter list --output json` for per-DC stock (`gpuAvailability.stockStatus` per DC), plus the public GraphQL `gpuTypes` query (`id`, `displayName`, `memoryInGb`, `securePrice`) for pricing. Verified working 2026-08-23.
- **You can set the timers but not read them back. They count from pod creation, so size them for the whole session, not the first job.** Nothing reads `--terminate-after` back: not the REST API, not the public GraphQL, and introspection is off, so `pod get` cannot confirm what you set. The API accepting the flag is all the evidence you get. That has two consequences. If you need the auto-off to be *provable*, add a **watchdog on the pod itself** — a detached `sleep N && <delete-self>`. You can check that it is running, and it survives your own session dying. And the clock starts at creation and **cannot be extended later**. So a pod created with a 4-hour terminate for a 3.4-hour training run will die partway through the eval that follows. You survive that only because the checkpoints are on the volume. That is the volume-as-contract rule earning its keep — not a reason to set a looser timer. Verified 2026-08-24.
- **Tear down in order:** remove the pod, *then* delete the volume if it was scratch. The volume can't be deleted while a pod holds it.
- **Volume data survives pod removal** — only deleting the volume clears it. That's the point: you rebuild pods freely and never re-download.
- **A billable session is not over until a burn check says it is.** End every session — agent-driven sessions especially — by listing what still exists and bills. One audited account had 37 leaked pods, every one created by agent tooling that skipped the guards. The guards above prevent the overnight bill. This check catches everything else. One call answers it:

  ```bash
  curl -s https://api.runpod.io/graphql -H "Authorization: Bearer $RUNPOD_API_KEY" \
    -H 'content-type: application/json' \
    -d '{"query":"{ myself { clientBalance pods { id name desiredStatus costPerHr volumeInGb } networkVolumes { id name size dataCenterId } } }"}'
  ```

  Anything `RUNNING` bills its `costPerHr`. A stopped pod bills only its `volumeInGb` (at ~$0.20/GB-mo — zero for template-only pods). Every network volume bills ~$0.07/GB-mo while it exists. `runpodctl pod stop <id>` pauses, `runpodctl pod remove <id>` deletes.
- **Keep one agent-free path to see and kill spend.** The moments you most need teardown — out of LLM quota, or the agent itself misbehaving — correlate exactly with money flowing. So the kill switch cannot be the agent. The query and the two commands above, pinned in a shell alias or a ten-line script, are the whole requirement. The RunPod web console is the zero-setup fallback.

---

## Deploying and running workflows

Two formats exist, and mixing them up is a common early error. The **UI format** you save from the ComfyUI canvas is *not* the **API format** the endpoint accepts. Export via *Save (API Format)* — or build the graph programmatically.

Against a serverless endpoint:

- **`POST /run` and poll `/status/{id}`.** Do **not** use `/runsync` for generation. Video and multi-stage image jobs exceed its window, and you get connection resets that look like endpoint failures.
- **Input images go base64-encoded** in the request payload, and `LoadImage` in the graph must reference the matching filename.
- **Model filenames in the workflow must exactly match the volume.** A mismatch surfaces as a validation error inside the `/status` response body, not as a transport error. So check the response body before assuming the endpoint is broken.
- **Bound your concurrency** to the endpoint's max workers. More in-flight requests than workers just queues up and confuses timing.

Endpoint knobs worth knowing: max workers, idle timeout (trades cold-start latency against idle cost), FlashBoot (pre-warms layers), and the queue-delay scaler. Full patterns: **`references/serverless-comfyui.md`**.

---

## Smoke test before you trust it

On rented hardware, find out in two minutes rather than twenty. Run this after any volume change, image change or fresh pod:

1. **UI answers.** Poll the proxy URL until it loads. Expect 502s during warm-up — that is normal, keep polling. *"Running" is not "ready."*
2. **Every loader dropdown is populated** — diffusion model, text encoder, VAE, and your LoRA folders. An empty dropdown means `extra_model_paths.yaml` isn't being read, not that the file is missing.
3. **Smallest possible generation.** Lowest resolution, fewest steps, shortest length. You are testing wiring, not quality.
4. **Check every output branch.** If the model emits more than one modality, verify each one. A video model with audio can produce a perfect-looking silent file, and frames alone won't tell you.
5. **Then the same graph through the API**, if serverless is the target — this is where the second mount root gets exercised.

Fail at step 2 and it's `extra_model_paths.yaml`. Fail at step 5 having passed step 3 and it's the `runpod_volume` block.

### Ask the worker what it can see, instead of guessing

The fastest diagnostic in this stack, and it costs one failed job rather than a debugging session. **Send a workflow with a deliberately invalid model name.** ComfyUI's validation error enumerates the values it *can* resolve:

```
vae_name: '__nonexistent__.safetensors' not in
  ['ae.safetensors', 'flux2-vae.safetensors', 'sdxl_vae_fp16_fix.safetensors', 'pixel_space']
```

A populated list means the volume is mounted and that key resolves. An empty or built-ins-only list means it is not. Compare the list against an S3 listing of the volume and you know within one job whether the problem is the mount, the yaml key, or the filename.

Two things that make this work:

- **The graph needs an output node.** Without one, ComfyUI returns `prompt_no_outputs` and never validates inputs. You burn a worker spin-up and learn nothing. Wire a `SaveImage`.
- **Validation runs before sampling**, so the job fails in well under a second of execution once the worker is warm. No GPU work happens.

Use it before you start editing `extra_model_paths.yaml` on a hunch.

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| Model dropdowns empty | `extra_model_paths.yaml` not deployed, or ComfyUI not restarted since | Deploy the file, restart ComfyUI (Manager → Restart) |
| Works in studio, "model not found" in serverless | Only the `network_volume` block declared; the worker mounts at `/runpod-volume/` | Declare both blocks with identical keys |
| Template shows `volumeMountPath: /workspace`, so the second block "must be unnecessary" | `volumeMountPath` is a **pod-only** field that serverless ignores | Ignore it on serverless templates; declare both blocks anyway |
| A single model type missing, rest fine | That loader's key absent — commonly `text_encoders` or `vae_approx` | Add the key; map `text_encoders` and `clip` to the same dir |
| LoRA on the volume but not in the dropdown | Wrong subfolder, or ComfyUI not restarted | Check the folder, restart; the dropdown shows the subfolder as a prefix |
| Proxy URL 502s | Still booting, or ComfyUI bound to `127.0.0.1` | Keep polling; ensure `--listen 0.0.0.0` |
| Can't add a port to a running pod | Ports are fixed at creation | Recreate with the port exposed (`8188/http`) |
| Endpoint "fails" instantly on dispatch | `/runsync` against a long job | Use `/run` + poll `/status/{id}` |
| Validation error naming a model file | Workflow filename ≠ volume filename | List the volume directory; fix the manifest `rename` or the workflow |
| GPU you wanted is unavailable | Volume is DC-locked and that GPU isn't in that DC | Check GPU availability in the volume's DC first, or place the volume deliberately |
| Surprise bill overnight | Pod created without `--terminate-after` | Always set both timers; end the session with the burn check |
| Pod vanished / paused mid-session | A cost-guard timer fired — this is the guard working, not a platform fault | `runpodctl pod start <id>` resumes a stopped pod; a terminated one recreates from the volume in minutes. Size the stop timer to the session next time |
| Pod alive, GPU at 0%, "still downloading" after 20+ minutes | `hf_xet` has hung — the process waits forever on a transfer that stopped | Set `HF_HUB_DISABLE_XET=1`, or uninstall `hf_xet`; check downloaded bytes rather than exit codes (`references/volume-and-models.md` §5) |
| `hf download` said it worked but the model won't load | Only the config and tokenizer landed; the weight files did not | Delete that model's HF cache completely, download again with Xet off, then check the size |
| Writes fail with "quota exceeded" while `df` shows terabytes free | `df` is reporting the cluster filesystem, not your volume's own limit | Measure the volume itself; move the HF cache, dataset and latent caches to the container disk (§6) |
| Training finishes, then the final checkpoint save fails | The volume hit its limit on the run's biggest write, which is the last one | The earlier checkpoints are fine — ship one of those. Clear space before the next run, not during it |
| `--docker-args` rejected on `pod create` | The current API does not accept it through `runpodctl 2.3.0` | Do that work over SSH after boot. No pod gets created, so nothing is charged |
| Startup `ImportError` after updating ComfyUI in a container | The image's `comfy_kitchen` is older than the ComfyUI you just pulled | Run `pip install -r requirements.txt` after the pull, not just the pull |
| Torch stops seeing the GPU after you restart ComfyUI by hand | You relaunched under a different interpreter than the template used — `python` instead of `python3` | Relaunch using the interpreter from the original process's command line |


> **Every `../name/` link on this page is a separate skill, and it dangles if that skill is not
> installed.** A dead link here is not a broken page. It is a skill you have not pulled yet.
> [`generative-media-atlas`](../generative-media-atlas/) is the map of the whole suite: what each
> skill covers, which ones a given job needs, and the commands to install them. It is written to be
> useful on its own, so it is the one to add first if you only want one:
>
> ```bash
> npx skills add ryannel/skills --skill generative-media-atlas
> ```

---

## Pre-flight checklist

1. `extra_model_paths.yaml` declares **both** `/workspace/` and `/runpod-volume/` roots with identical keys?
2. `text_encoders` **and** `clip` mapped; `diffusion_models` includes `models/unet/`; `vae_approx` present?
3. Every model in a manifest with explicit `dest` and `rename`, not hand-placed?
4. LoRAs foldered by base, with real compatibility recorded in the manifest rather than implied by the folder?
5. Downloads run on a **CPU pod or the S3 API**, never a GPU pod?
6. Volume's datacenter checked against GPU availability *before* planning?
7. **Volume free space measured** — with `du` or `aws s3 ls`, not `df` — against what the job will write, and caches and re-downloadable weights moved to the container disk if it is tight?
8. Pod created with its cost guards — **`--stop-after` + `--terminate-after`** for interactive, **`--terminate-after`** for batch — set long enough for the **whole session**, including the eval that follows the job, and the port exposed at creation?
9. Workflow exported in **API format** (not UI format) for endpoint use?
10. Dispatch via **`/run` + poll**, not `/runsync`?
11. Smoke test passed through **both** the UI and the API before real work?
12. Teardown verified with a burn check — nothing `RUNNING`, no stopped pod holding volume disk, and every volume kept or deleted deliberately? A session that skips this is not finished.

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** The dual mount roots (`/workspace/` vs `/runpod-volume/`), the `extra_model_paths.yaml` key set and its multi-path `diffusion_models` block, which loader reads which directory, the S3 endpoint form `s3api-<dc>.runpod.io`, `--terminate-after` deleting versus `--stop-after` stopping, ports being fixed at pod creation, volumes being datacenter-locked, and API-format-not-UI-format for endpoints. **Source of truth is official** — RunPod's own skills and docs — plus a single production ComfyUI-on-RunPod deployment external to this repo, which these were read out of. **The dual mount root was validated against live infrastructure on 2026-08-13.** A serverless worker enumerated exactly the volume's `models/vae/`, and the `runpodctl` command-surface split was verified against `2.3.0-be4ced4`. A wrong path silently hides a model. A missing cost guard bills all night. **Re-verify the CLI flags and pricing against `runpodctl` before relying on them** — platform surfaces change.

**Craft — what actually makes this work day to day.** The volume-as-contract framing, foldering LoRAs by base with a separate compatibility graph, the manifest pattern, downloading on CPU pods, build-interactively-run-in-serverless, the smoke-test order, and the durability split that decides what goes on the container disk versus the volume. **This is house craft distilled from that same single production ComfyUI-on-RunPod deployment**, not vendor documentation. It is what the vendor docs don't tell you, because it only shows up after you've rebuilt a volume a few times. Stated with confidence — adapt the specifics to your stack.

One thing is deliberately **not** claimed here: GPU recommendations and prices. They move constantly and are model-specific. `runpod-usage` owns the general question, and each model skill owns its own requirement. Any price quoted anywhere in this suite is a stale snapshot. Check `runpodctl gpu list` — on a current CLI, per the version note above.

**Nothing is currently contested or flagged.** The 2026-08-13 pass resolved every open finding (see `freshness.json`). The watchlist there tracks what could still drift.

**A second live pass — a LoRA training run plus its ComfyUI eval, 2026-08-24/25 — added the download, quota and timer-readback findings.** Those were measured on one account in `eu-ro-1` against `runpodctl 2.3.0`. The mechanisms behind them are general. The specific S3-compat gaps are one endpoint's behaviour on one date. `HF_HUB_DISABLE_XET`, and the bug where it is sometimes ignored, are official `huggingface_hub` facts rather than ours.

**Facts dated 2026-08-13. Cost-guard timers and the burn-check query were re-verified live on 2026-08-23, along with the Impact Pack detailer paths (`ultralytics_bbox`/`ultralytics_segm`/`sams`) and the priced-`gpu list` CLI fallback. Download, quota and timer findings were added 2026-08-25.** The `runpodctl` command surface and endpoint knobs are what moves fastest here — re-verify those before relying on them. The ComfyUI-side contract (`extra_model_paths.yaml` keys, loader directories) is stable.

---

## Reference files

| File | When to read it |
|---|---|
| `references/volume-and-models.md` | Full volume layout and placement table, the `extra_model_paths.yaml` in full, LoRA foldering and compatibility, the manifest schema, how to fill or rebuild a volume from scratch — including the downloads that report success and fetch nothing — plus the training layout, the volume size limit, and what belongs on the container disk instead |
| `references/serverless-comfyui.md` | ComfyUI as an endpoint: API-format workflows, the `/run` + poll pattern, base64 image inputs, endpoint scaling knobs, cold start, and the deployment failure table |
