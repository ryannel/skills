# Volume layout, `extra_model_paths.yaml`, and the model manifest

Everything ComfyUI needs to find a model on the volume: the dual-root config, the placement table, LoRA foldering, and the manifest that makes a volume reproducible. Deployment mechanics (pods, endpoints, dispatch) are `serverless-comfyui.md`.

1. [The dual mount root, in full](#1-the-dual-mount-root-in-full)
2. [Placement table — file type → directory → loader](#2-placement-table)
3. [LoRA organisation and compatibility](#3-lora-organisation-and-compatibility)
4. [The manifest schema](#4-the-manifest-schema)
5. [Populating and rebuilding a volume](#5-populating-and-rebuilding-a-volume)
6. [Custom nodes](#6-custom-nodes)

---

## 1. The dual mount root, in full

The single fact that explains most "ComfyUI can't find my model" confusion: **the same volume has three addresses.**

| Where code runs | Volume root | Example |
|---|---|---|
| Interactive pod | `/workspace/` | `/workspace/models/loras/` |
| Serverless worker | `/runpod-volume/` | `/runpod-volume/models/loras/` |
| S3 API from local | `s3://<volume-id>/` | `s3://<volume-id>/models/loras/` |

A complete `extra_model_paths.yaml`, both blocks, identical key sets:

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
  style_models: models/style_models/
  upscale_models: models/upscale_models/
  vae: models/vae/
  vae_approx: models/vae_approx/

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
  style_models: models/style_models/
  upscale_models: models/upscale_models/
  vae: models/vae/
  vae_approx: models/vae_approx/
```

**Where the file goes.** ComfyUI reads it from its own install directory. On a pod that means writing it next to the ComfyUI checkout (`…/ComfyUI/extra_model_paths.yaml`); for serverless, bake it into the image so every worker gets it. Deploy it programmatically on boot rather than editing by hand — a hand-edited copy on one pod is a config that doesn't survive the next rebuild.

**Diagnostic order** when a model won't resolve:

1. Is the file actually on the volume? (`aws s3 ls` — no pod needed)
2. Is its directory covered by a key in the yaml?
3. Is that key present in **both** blocks?
4. Has ComfyUI been restarted since the yaml changed? (Manager → Restart)

---

## 2. Placement table

Organised by the loader node that reads it — the only scheme that stays correct as models change.

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

**The `CLIPLoader` `type` argument is model-specific and not guessable** — `lumina2`, `wan`, `minimax`, `ltxv`, `flux2` and others all exist. It belongs in your manifest next to the filename, because a workflow builder needs it and getting it wrong produces a confusing encode failure rather than a missing-file error. Each model skill states its own.

**Multi-file models are normal now.** A modern DiT is typically a diffusion model *plus* a separate text encoder *plus* a VAE — three directories, three loaders. Some go further: a model with native audio may ship **two** VAEs (video and audio) landing in the same `models/vae/` directory, and a mixture-of-experts model ships **two** diffusion files. Plan the manifest around files, not models.

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

**The folder is the human view; the manifest is the truth.** A LoRA trained on a base model frequently loads on its distilled sibling at reduced strength — its *home* is one folder, its *capability* is a list. Record that list (`compat: [base, turbo]`) and have your workflow builder check it before wiring, skipping incompatible LoRAs silently. Then a single scene definition listing several LoRAs renders correctly under any base, wiring only the ones that apply.

To answer *"if I retire base X, what dies?"* — query the manifest for entries whose `compat` lists **only** X. Anything listing another base survives.

**Keep run archives, prune deliberately.** A training run leaves multiple checkpoints plus optimiser state. Optimiser files are only needed to resume an interrupted run — delete them once a run is final. Intermediate checkpoints are worth keeping while a character is still being iterated and worth pruning to the selected one afterwards.

---

## 4. The manifest schema

A single checked-in file describing the whole stack. The shape that works:

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

custom_nodes:                           # pinned, see §6
  - repo: …
    commit: …
```

Why each field earns its place:

- **`files[].rename`** — upstream repos nest under `split_files/…` and use long descriptive names. Your workflows reference a flat, stable name. `rename` is where those two worlds are reconciled, and it is the reason a re-pull doesn't break every graph.
- **`dest`** — absolute, so the downloader can `mkdir -p` and place correctly without inference.
- **`clip_type`** — the one workflow value that cannot be derived from a filename.
- **`compat`** — the dependency graph (§3).
- **`stack`** — separates "we have this" from "we use this," so a volume can hold archives without implying they're live.

**The payoff is that workflows and downloads read the same source.** A workflow builder pulling `unet_filename` / `clip_filename` / `clip_type` / `vae_filename` out of the manifest cannot drift from what the downloader put on disk. That equivalence is the whole mechanism behind "a fresh instance opens our workflows and everything resolves."

---

## 5. Populating and rebuilding a volume

**Do it on a CPU pod.** Downloading is I/O; paying GPU rates for it is pure waste. A CPU pod with the volume mounted, running `hf download` per manifest entry, is the default route.

**Or push from local over the S3 API:**

```bash
DC=$(echo "$RUNPOD_DATACENTER" | tr '[:upper:]' '[:lower:]')
aws s3 ls "s3://$RUNPOD_NETWORK_VOLUME_ID/models/" \
  --region "$DC" --endpoint-url "https://s3api-$DC.runpod.io/"

aws s3 cp ./my_lora.safetensors \
  "s3://$RUNPOD_NETWORK_VOLUME_ID/models/loras/<base>/" \
  --region "$DC" --endpoint-url "https://s3api-$DC.runpod.io/"
```

The S3 route is also the cheapest way to **audit** a volume — list its contents with no pod running at all, which is the fastest answer to "is the file actually there?"

**Never `wget`.** `hf download` gives resume, parallel chunks and correct revision pinning; a 20 GB `wget` that dies at 90% costs you the whole download again.

**Rebuild procedure**, which should be one command in your tooling:

1. Create the volume in a DC where your GPUs actually exist.
2. Start a CPU pod with it mounted.
3. Walk the manifest, downloading each `files[]` entry to its `dest` with its `rename`.
4. Verify by listing over the S3 API.
5. Remove the CPU pod.

Then any GPU pod or endpoint that mounts the volume is immediately correct.

---

## 6. Custom nodes

Custom nodes are **code**, not weights, and the distinction decides where they live:

- **Bake them into the image** for serverless. Workers must start deterministically, and a worker that clones a repo on boot is slow and fragile.
- **Install them on the pod** for interactive work, where you're iterating anyway.

**Pin them.** Custom nodes are the least stable part of the stack — an unpinned node that updates between two runs is a leading cause of "the same workflow produced different output." Record repo plus commit in the manifest.

A workflow JSON referencing a node class that isn't installed fails at load with a red node, not a helpful message. When a graph won't open on a fresh instance and the models all resolve, missing custom nodes are the next place to look.
