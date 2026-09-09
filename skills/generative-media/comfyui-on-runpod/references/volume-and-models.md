# Volume layout, `extra_model_paths.yaml`, and the model manifest

This file covers everything ComfyUI needs to find a model on the volume: the dual-root config, the placement table, LoRA foldering, and the manifest that makes a volume reproducible. Deployment mechanics such as endpoints and dispatch are covered in `serverless-comfyui.md`. §8 here is the exception: it is about keeping a trainer or batch pod honest, and it lives here because that pod is writing to this volume.

1. [The dual mount root, in full](#1-the-dual-mount-root-in-full)
2. [Placement table — file type → directory → loader](#2-placement-table)
3. [LoRA organisation and compatibility](#3-lora-organisation-and-compatibility)
4. [The manifest schema](#4-the-manifest-schema)
5. [Populating and rebuilding a volume](#5-populating-and-rebuilding-a-volume)
6. [Training on the same volume](#6-training-on-the-same-volume)
7. [Custom nodes](#7-custom-nodes)
8. [Launching, watching and killing a pod job](#8-launching-watching-and-killing-a-pod-job)

---

## 1. The dual mount root, in full

Most "ComfyUI can't find my model" confusion comes down to a single fact: **the same volume has three addresses.**

| Where code runs | Volume root | Example |
|---|---|---|
| Interactive pod | `/workspace/` | `/workspace/models/loras/` |
| Serverless worker | `/runpod-volume/` | `/runpod-volume/models/loras/` |
| S3 API from local | `s3://<volume-id>/` | `s3://<volume-id>/models/loras/` |

Here is a complete `extra_model_paths.yaml`. It contains both blocks, and both blocks use identical key sets:

```yaml
network_volume:
  base_path: /workspace/
  checkpoints: models/checkpoints/
  clip: models/clip/
  text_encoders: models/clip/
  clip_vision: models/clip_vision/
  configs: models/configs/
  controlnet: models/controlnet/
  diffusion_models: |
               models/diffusion_models/
               models/unet/
  embeddings: models/embeddings/
  gligen: models/gligen/
  hypernetworks: models/hypernetworks/
  ipadapter: models/ipadapter/
  loras: models/loras/
  sams: models/sams/
  style_models: models/style_models/
  ultralytics_bbox: models/ultralytics/bbox/
  ultralytics_segm: models/ultralytics/segm/
  upscale_models: models/upscale_models/
  vae: models/vae/
  vae_approx: models/vae_approx/
  # keys the upstream example added by 2026-09 — declare now, create the folder when a node asks
  audio_encoders: models/audio_encoders/
  background_removal: models/background_removal/
  detection: models/detection/
  diffusers: models/diffusers/
  frame_interpolation: models/frame_interpolation/
  geometry_estimation: models/geometry_estimation/
  latent_upscale_models: models/latent_upscale_models/
  model_patches: models/model_patches/
  optical_flow: models/optical_flow/

runpod_volume:
  base_path: /runpod-volume/
  checkpoints: models/checkpoints/
  clip: models/clip/
  text_encoders: models/clip/
  clip_vision: models/clip_vision/
  configs: models/configs/
  controlnet: models/controlnet/
  diffusion_models: |
               models/diffusion_models/
               models/unet/
  embeddings: models/embeddings/
  gligen: models/gligen/
  hypernetworks: models/hypernetworks/
  ipadapter: models/ipadapter/
  loras: models/loras/
  sams: models/sams/
  style_models: models/style_models/
  ultralytics_bbox: models/ultralytics/bbox/
  ultralytics_segm: models/ultralytics/segm/
  upscale_models: models/upscale_models/
  vae: models/vae/
  vae_approx: models/vae_approx/
  # keys the upstream example added by 2026-09 — declare now, create the folder when a node asks
  audio_encoders: models/audio_encoders/
  background_removal: models/background_removal/
  detection: models/detection/
  diffusers: models/diffusers/
  frame_interpolation: models/frame_interpolation/
  geometry_estimation: models/geometry_estimation/
  latent_upscale_models: models/latent_upscale_models/
  model_patches: models/model_patches/
  optical_flow: models/optical_flow/
```

**Where the file goes.** ComfyUI reads this file from its own install directory. On a pod, that means you write it next to the ComfyUI checkout (`…/ComfyUI/extra_model_paths.yaml`). For serverless, bake it into the image so every worker gets it. Deploy it programmatically on boot rather than editing it by hand. A hand-edited copy on one pod is a config that will not survive the next rebuild.

**Diagnostic order** when a model won't resolve:

1. Is the file actually on the volume? (`aws s3 ls` — no pod needed)
2. Is its directory covered by a key in the yaml?
3. Is that key present in **both** blocks?
4. Has ComfyUI been restarted since the yaml changed? (Manager → Restart)

---

## 2. Placement table

The table is organised by the loader node that reads each file. That is the only scheme that stays correct as models change.

| File type | Directory | Loader node |
|---|---|---|
| Diffusion model / UNet (DiT) | `models/diffusion_models/` | `UNETLoader` / Load Diffusion Model |
| All-in-one checkpoint (SD/SDXL-era) | `models/checkpoints/` | `CheckpointLoaderSimple` |
| Text encoder | `models/clip/` | `CLIPLoader` — with the correct `type` argument |
| VAE | `models/vae/` | `VAELoader` |
| TAE preview decoder | `models/vae_approx/` | preview / custom node |
| ControlNet | `models/controlnet/` | `ControlNetLoader` |
| Upscale model (ESRGAN etc.) | `models/upscale_models/` | `UpscaleModelLoader` |
| IP-Adapter | `models/ipadapter/` | adapter custom nodes |
| CLIP Vision | `models/clip_vision/` | `CLIPVisionLoader` |
| Textual inversion | `models/embeddings/` | referenced inline in prompts |
| LoRA | `models/loras/<base>/` | `LoraLoader` / `LoraLoaderModelOnly` |
| Detailer detector — `face_yolov8m.pt` | `models/ultralytics/bbox/` | Impact Pack `UltralyticsDetectorProvider` |
| SAM segmenter — `sam_vit_b_01ec64.pth` | `models/sams/` | Impact Pack `SAMLoader` |

**Keys added upstream since this table was written.** Comfy-Org's `extra_model_paths.yaml.example` now also lists `audio_encoders`, `background_removal`, `detection`, `diffusers`, `frame_interpolation`, `geometry_estimation`, `latent_upscale_models`, `model_patches` and `optical_flow` `[official — Comfy-Org/ComfyUI extra_model_paths.yaml.example, read 2026-09-09]`. `frame_interpolation` and `optical_flow` are the two this suite's video models are most likely to hit. Declare them all in both blocks, as §1 does, and create a folder only when a node's dropdown comes up empty. An absent directory is not a fault.

**Detailer models have canonical files, and they are not optional if the pipeline runs a detail pass on faces.** The suite's standard deploy path does exactly that. The community-standard pair is `face_yolov8m.pt` (from `Bingsu/adetailer` on Hugging Face), which goes in `models/ultralytics/bbox/`, and `sam_vit_b_01ec64.pth` (the facebook SAM release, commonly mirrored), which goes in `models/sams/`. These two files are community-sourced picks, but they are the ones every FaceDetailer tutorial and workflow assumes. The paths themselves are hard fact: Impact Pack resolves detectors through the `ultralytics_bbox` / `ultralytics_segm` / `sams` keys and nowhere else. This was verified on 2026-08-23, when a deployment planned against this file's yaml had no home for them. **`insightface/` is not that home.** That directory serves PuLID/InstantID-class *identity* nodes (`FaceAnalysis`). A detector placed there leaves the FaceDetailer dropdowns empty.

**The `CLIPLoader` `type` argument is model-specific, and you cannot guess it.** Values such as `lumina2`, `wan`, `minimax`, `ltxv`, and `flux2` all exist. Record it in your manifest next to the filename, because a workflow builder needs it. Getting it wrong produces a confusing encode failure rather than a missing-file error. Each model skill states its own value.

**Multi-file models are normal now.** A modern DiT typically ships as a diffusion model plus a separate text encoder plus a VAE. That is three directories and three loaders. Some models go further. A model with native audio may ship **two** VAEs (video and audio) that land in the same `models/vae/` directory, and a mixture-of-experts model ships **two** diffusion files. Plan the manifest around files, not models.

---

## 3. LoRA organisation and compatibility

**Folder by primary base model:**

```
models/loras/
├── <base-model-a>/
│   └── <character>_v8/          ← a training run archive, not just a file
├── <base-model-b>/
└── _shared/                     ← genuinely works on more than one base
```

Two reasons this beats a flat directory:

1. **Visible in the UI.** `LoraLoader` renders the subfolder as a dropdown prefix, so you can see a LoRA's lineage without opening anything.
2. **Clean retirement.** When you drop a base model, the folder tells you exactly what was built for it.

**The folder is the human view. The manifest is the truth.** A LoRA trained on a base model frequently loads on its distilled sibling at reduced strength. Its *home* is one folder, but its *capability* is a list. Record that list (`compat: [base, turbo]`) and have your workflow builder check it before wiring, so it skips incompatible LoRAs silently. A single scene definition that lists several LoRAs then renders correctly under any base, because only the LoRAs that apply get wired.

To answer *"if I retire base X, what dies?"*, query the manifest for entries whose `compat` lists **only** X. Anything that also lists another base survives.

**Keep run archives, prune deliberately.** A training run leaves multiple checkpoints plus optimiser state. Optimiser files are only needed to resume a run, so delete them once a run is final. Be sure it is final: `optimizer.pt` is ~600 MB per run and the obvious thing to drop when the volume is tight, but keeping it is what let one run extend from 3,000 to 5,000 steps at about 40% of the compute of starting over `[live-use — media lab, 2026-09]`. Intermediate checkpoints are worth keeping while a character is still being iterated. Once the final checkpoint is selected, prune down to that one.

**Promote with a copy, not a symlink.** ComfyUI validates a LoRA name against its own scan of `models/loras`, and that scan does not follow symlinks. A whole eval grid failed on links that `stat -L` resolved perfectly `[live-use — media lab, 2026-08]`. Eval checkpoints are real copies, a few hundred megabytes each; budget for them.

---

## 4. The manifest schema

The manifest is a single checked-in file that describes the whole stack. This is the shape that works:

```yaml
stack:                                  # what is active right now
  - z-image-base
  - z-image-turbo

models:
  z-image-base:
    description: "6B S3-DiT, non-distilled. Training + inference base."
    architecture: z-image-base          # groups LoRA compatibility
    unet_filename: z_image_bf16.safetensors
    clip_filename: qwen_3_4b_fp8_mixed.safetensors
    clip_type: lumina2                  # the CLIPLoader `type`
    vae_filename: ae.safetensors
    source: huggingface
    files:
      - repo: Comfy-Org/z_image
        filename: split_files/diffusion_models/z_image_bf16.safetensors
        dest: /workspace/models/diffusion_models/
        rename: z_image_bf16.safetensors

  some-character-lora:
    architecture: lora
    lora_filename: z-image-turbo/amy_v9/amy_v9_000001500.safetensors
    compat: [z-image-base, z-image-turbo]
    files:
      - repo: …
        dest: /workspace/models/loras/z-image-turbo/amy_v9/

custom_nodes:                           # pinned, see §7
  - repo: …
    commit: …
```

Why each field earns its place:

- **`files[].rename`** — Upstream repos nest files under `split_files/…` and use long descriptive names. Your workflows reference a flat, stable name. `rename` is where those two worlds meet, and it is the reason a re-pull doesn't break every graph.
- **`dest`** — The path is absolute, so the downloader can `mkdir -p` and place the file correctly without guessing.
- **`clip_type`** — This is the one workflow value that cannot be derived from a filename.
- **`compat`** — This is the dependency graph described in §3.
- **`stack`** — This separates "we have this" from "we use this," so a volume can hold archives without implying they're live.

**The payoff is that workflows and downloads read the same source.** A workflow builder that pulls `unet_filename` / `clip_filename` / `clip_type` / `vae_filename` out of the manifest cannot drift from what the downloader put on disk. That equivalence is the whole mechanism behind "a fresh instance opens our workflows and everything resolves."

---

## 5. Populating and rebuilding a volume

**Do it on a CPU pod.** Downloading is I/O work, and paying GPU rates for it is pure waste. The default route is a CPU pod with the volume mounted, running `hf download` for each manifest entry.

**Or push from local over the S3 API:**

```bash
DC=$(echo "$RUNPOD_DATACENTER" | tr '[:upper:]' '[:lower:]')
aws s3 ls "s3://$RUNPOD_NETWORK_VOLUME_ID/models/" \
  --region "$DC" --endpoint-url "https://s3api-$DC.runpod.io/"

aws s3 cp ./my_lora.safetensors \
  "s3://$RUNPOD_NETWORK_VOLUME_ID/models/loras/<base>/" \
  --region "$DC" --endpoint-url "https://s3api-$DC.runpod.io/"
```

The S3 route is also the cheapest way to **audit** a volume. You can list its contents with no pod running at all, which is the fastest answer to "is the file actually there?"

**Never use `wget`.** `hf download` gives you resume support, parallel chunks, and correct revision pinning. A 20 GB `wget` that dies at 90% costs you the whole download again.

**Check the size, because `hf download` can exit successfully after fetching almost nothing.** Its Xet transfer backend (`hf_xet`, which is used automatically once installed) fails in two ways that both look like success:

- **It hangs.** The process stays alive, the GPU sits at 0%, and the cache stops growing part-way through.
- **It lies.** After a cleared or interrupted Xet cache, a run can report success after pulling only the config and tokenizer, skipping the multi-gigabyte weight files.

A pod that looks like it is training but is really waiting on a dead download bills exactly the same per hour as one that is working. There are three defences, cheapest first:

- **Check bytes, never exit codes.** Write your DONE marker only after you have confirmed the downloaded folder is the size you expected. One `du` comparison turns both failures into loud ones.
- **Turn Xet off for big weight downloads** by setting `HF_HUB_DISABLE_XET=1` `[official — huggingface_hub environment-variable docs]`. Plain LFS over HTTPS is less clever and, for these files, more reliable.
- **If that variable seems to be ignored, uninstall `hf_xet`.** The variable does not always take effect, which is a reported bug `[official — huggingface_hub#3266]`, and removing the package leaves no doubt. On a throwaway container that is a fine thing to do.

If a Xet cache is already in a bad state, delete that model's cache completely before retrying. Downloading on top of stale index files is what produces the false success.

**PEP 668 blocks `pip install` on recent base images**, because their system Python is marked externally-managed. On a throwaway container, `--break-system-packages` is the right answer rather than a hack. In anything you plan to keep, use a virtualenv.

**The rebuild procedure**, which should be one command in your tooling:

1. Create the volume in a DC where your GPUs actually exist.
2. Start a CPU pod with it mounted.
3. Walk the manifest, downloading each `files[]` entry to its `dest` with its `rename`.
4. Verify by listing over the S3 API.
5. Remove the CPU pod.

After that, any GPU pod or endpoint that mounts the volume is immediately correct.

---

## 6. Training on the same volume

The layout above is inference-shaped, but LoRA training happens on the same volume. Trainer pods mount it at `/workspace/` like any other pod. Giving trainer artifacts assigned homes is what keeps them from silting up `models/`:

| Purpose | Directory | Why there |
|---|---|---|
| HF cache | `/workspace/huggingface/` **if the volume has room** | Set `HF_HOME=/workspace/huggingface` so the next trainer pod skips the 20 GB re-download — a stop wipes the container disk, the volume survives. **Check free space first**: on a volume near its quota this is the setting that kills the run (see below) |
| Training data | `/workspace/datasets/<name>/` | One folder per dataset, named for the subject — reusable across runs and bases |
| Run outputs | `/workspace/training/<run>/` | Checkpoints, samples and optimiser state per run; the *selected* checkpoint then gets promoted into `models/loras/<base>/` (§3), which stays a curated directory rather than a dumping ground |

**Budget for the weights existing twice.** Trainers read the base model in diffusers format out of the HF cache. ComfyUI loads a single-file `.safetensors` from `models/diffusion_models/`. For a Z-Image-class model, that is roughly 20 GB stored twice. This is a format difference, not waste you can deduplicate. Size the volume for both copies rather than trying to make one file serve both jobs.

The text encoder is the usual surprise here. You can have a complete ComfyUI model set already on the volume, and the trainer will still fetch its own ~9 GB diffusers copy. Where the trainer lets you name paths (AI-Toolkit's `model_kwargs.text_encoder_path` and `vae_path`), point them at a copy you already have instead of storing either duplicate.

### The volume quota is a hard wall, and you hit it late

**Every network volume has a size limit that `df` will not show you.** Run `df -h /workspace` and it reports the cluster filesystem underneath, showing terabytes free, while your writes start failing at your volume's actual size. Measure what is on the volume instead: an `aws s3 ls` walk, or `du` on the pod. Never trust `df`.

**Work out free space before you launch, because the write that fails is the last one.** Training saves checkpoints as it goes, and its biggest write is the *final* save. So a run that fits right up until the end can still lose its last checkpoint to a quota error, after you have paid for the whole run. You only recover because the earlier checkpoints landed, which is one more reason to save a series instead of a single result. In one measured run the failures arrived in this order: the encoder download hit the quota, then latent caching, then the final save `[community — production run, 2026-08-24]`.

**The fix is to sort files by whether losing them matters, not to delete models.** Ask of each file: if the pod stopped right now and this vanished, what would it cost?

| What | Put it on | Why |
|---|---|---|
| HF cache, encoder, dataset copy, latent and text caches | **Container disk** (`HF_HOME=/root/hf` or similar) | All rebuildable in minutes. A stop wipes them and that is fine |
| Checkpoints, the curated `models/` tree, datasets of record | **Volume** | The only things whose loss costs real work |

Container disks are usually 40 GB and mostly empty, which is enough for an encoder plus caches. This deliberately flips the default in the table above: putting the cache on the volume is right when there is room and wrong when there is not. "How full is the volume?" is the question that settles it.

**The wall is real and it arrives mid-transfer.** One volume's cap was 250 GB. An `rsync` of two runs' outputs hit it at once — `Disk quota exceeded (122)`, a broken pipe, and a post-training step reported as failed after the training itself had succeeded `[live-use — media lab, 2026-09-09]`. Three habits follow. Sync only the checkpoints you will evaluate, not a run's full series. Plan quota before launching two arms in parallel, because both will write at the same time. And remember that volume writes need a running pod, so a copy you meant to do "later" belongs in the next pod's setup script.

**Clear space before a run, not during one.** Firefighting a quota mid-run is the expensive kind, because the GPU bills while you decide what to delete. Two habits make it a non-event. Check free space as a pre-flight step, and know which of your big files can simply be downloaded again. A training base, once training is finished, is 24 GB you can drop without losing anything.

**RunPod's S3-compatible endpoint is not a full S3, and the gaps bite right here.** Listing with `--recursive` returns nothing for directories that it will happily list one level at a time. **Server-side copy does not work.** It fails with a tagging 500, so moving a file from one volume path to another means doing it on a pod with `cp`, not over the API. The region has to be lowercase and set on every call. And a deleted directory keeps showing up as an empty `PRE` marker, which looks like a failed delete but is not `[community — measured against `eu-ro-1`, 2026-08-24]`.

---

## 7. Custom nodes

Custom nodes are **code**, not weights, and that distinction decides where they live:

- **Bake them into the image** for serverless. Workers must start deterministically, and a worker that clones a repo on boot is slow and fragile.
- **Install them on the pod** for interactive work, where you are iterating anyway.

**Pin them.** Custom nodes are the least stable part of the stack. An unpinned node that updates between two runs is a leading cause of "the same workflow produced different output." Record the repo plus the commit in the manifest.

A workflow JSON that references a node class that is not installed fails at load with a red node, not a helpful message. When a graph will not open on a fresh instance and the models all resolve, missing custom nodes are the next place to look.

---

## 8. Launching, watching and killing a pod job

A trainer or batch pod bills while it does nothing. Every item here is a way that "nothing" was mistaken for "working," measured on rented GPUs `[live-use — media lab, 2026-08-26 to 2026-09-09]`. None of them is specific to one trainer.

**Boot on a stock RunPod template, and gate the driver first.** An image built for serverless may not install RunPod's SSH key; a `RUNNING` pod with `22/tcp` published still answered `Permission denied (publickey)`. Stock templates take the key. Then, before installing anything, read `nvidia-smi`: a 570.x host driver fails a CUDA 13 stack with `driver too old`, and dropping to cu128 only moves the failure into pip. Four creates in a row landed on the same bad host. The fix is **hold-and-reroll**: keep the dud running so the scheduler cannot hand you that host again, create the next pod, verify it, then remove the duds. Two pip traps sit on the stock CUDA template. It exports `PIP_CONSTRAINT`, which makes a cu130 install fail with `ResolutionImpossible` hidden behind `pip -q`; `unset` it. And `git+https://` requirements need `git config --global http.version HTTP/1.1` — global, because pip's own clones read the same setting.

**A return code is not a start.** Inline `ssh 'nohup bash -c "…"'` chains failed silently three times in one month. Write the setup to a file with `set -euo pipefail` and a banner `echo` at each phase, launch it with `setsid -f` with every file descriptor redirected (`setsid … & exit 0` holds the SSH pipe open, and cost one session seventy minutes), then verify within a minute two ways: `head` the log for the banner, and `pgrep` for the process. **The `pgrep` pattern must name something unique to this run.** A bare `[r]un.py` matched ComfyUI's own `run.py`, a launch was declared good, nothing trained, and an hour of GPU time went by. The same rule applies to the finish: a stray `.safetensors` in a latent cache read as DONE, so scope the completion check to the trainer's output directory and require positive evidence.

**Watch the cap, not `free`.** `free` on a 5090 pod reports 123 GB; the container's cgroup limit (`/sys/fs/cgroup/memory.max`) was 60 GB, and `swapon` is not permitted. A process that crosses it is killed with no traceback. In-training sampling is the usual culprit on a large-encoder model, because it pulls the offloaded text encoder back on top of resident training state. Turn samples off. It costs nothing, since checkpoints and optimiser state are written before the sample pass, so a relaunch resumes where it died.

**Kill by port, never by pattern.** `pkill -f 'main.py --listen'` matched the SSH command line carrying it and killed the session (rc 255, no output). Resolve the PID from `ss -ltnp` and kill that. And never stop or remove pods in bulk: name ids. A bulk stop took another session's pod down with it.

**A monitor event is a nudge, not the state.** One delivered a four-hour-stale step count despite line buffering. When an event fires, go and read the current log. Poll with an `until grep -qE "DONE|Traceback"` loop rather than sleep chains, and stop chatty monitors once they have done their job.

**Two parsing traps.** `runpodctl` prints a non-breaking space (U+00A0) between a port number and `(pub,tcp)`, which breaks naive endpoint parsing while looking identical on screen; split on Unicode whitespace. And zsh does not word-split unquoted variables, so `S="ssh …"; $S "cmd"` exits 0 instantly, and an `until` guard reads that as success.

**Check the datatype before the price.** A cheaper card is not cheaper if the recipe's datatype is not native to it: a card without fp8 units runs an fp8 recipe several times slower than a consumer card that has them. The GPU decision belongs to `runpod-usage` and the model skill; this is the one check that is cheap to skip and expensive to have skipped.
