# Ideogram 4 setup & workflows (open weights)

This file covers how to run the open-weight model yourself, through diffusers, the shipped CLI, or ComfyUI. "Self-hosted" means that you run the model. It says nothing about where the hardware lives. Every path here works the same on your own workstation **or a rented cloud GPU** (RunPod, Vast.ai, Lambda, etc.). Renting a box is the usual way to get a 24 GB+ / H100 GPU for the larger quants and 2K renders. See §1.1.

**Licence reminder:** the weights are **Non-Commercial**. Commercial use needs a separate paid licence from Ideogram. The inference code is Apache-2.0. The non-commercial restriction is about the *purpose* of use. **Running on a paid cloud GPU does not make commercial use OK.** For commercial output, use the hosted API/web app instead (`api-and-hosted.md`).

**Training** a LoRA is covered in the neighbouring file, `lora-training.md`. Section 6 here covers only the loading half of that split.

Sources are labelled `[official]` when they come from the `ideogram-oss/ideogram4` repo, the HF model cards, or the `Comfy-Org/Ideogram-4` file listing. They are labelled `[community — single report; re-verify]` when they come from forum and blog reports. The community record for this model is still too thin to corroborate those reports.

## Contents

- [1. Model access (gating)](#1-model-access-gating)
- [2. diffusers](#2-diffusers)
- [3. The `run_inference.py` CLI](#3-the-run_inferencepy-cli)
- [4. ComfyUI (day-0 native support)](#4-comfyui-day-0-native-support)
- [5. Safety filter (self-hosted)](#5-safety-filter-self-hosted)
- [6. Using a LoRA you have trained](#6-using-a-lora-you-have-trained)

---

## 1. Model access (gating)

The weights are **gated** on Hugging Face. You must accept the licence and authenticate, or downloads fail with `404` / `GatedRepoError` `[official — ideogram-oss/ideogram4 repo]`.

1. Open `ideogram-ai/ideogram-4-nf4` (or `-fp8`) and click **Agree and access repository**.
2. Authenticate: `hf auth login`, or `export HF_TOKEN="hf_..."`.

| Repo | Quant | Hardware | diffusers | Fits |
|---|---|---|---|---|
| `ideogram-ai/ideogram-4-nf4` | bitsandbytes 4-bit (nf4) | **CUDA only** | Yes | a single 24 GB GPU `[official — HF model card]`; 32 GB recommended for headroom |
| `ideogram-ai/ideogram-4-fp8` | weight-only float8 e4m3 (activations stay bf16) | **all** (CUDA / MPS / CPU) | via `Ideogram4Pipeline` | larger; runs anywhere, no FP8 hardware needed |

"We plan to support more quantizations in the future." No official GGUF yet `[official — HF model card]`.

**These two repos are the diffusers and CLI weights.** ComfyUI does not load them. It uses a separate set of files from the `Comfy-Org/Ideogram-4` repo, in three quants of its own (§4). Mixing the two up was the source of a filename confusion this skill carried until 2026-09-09.

### 1.1 Running on a cloud GPU (RunPod, Vast.ai, …)

You don't need the hardware locally. The same diffusers / CLI / ComfyUI stacks run on a rented GPU pod, and renting is the common way to get the VRAM Ideogram 4 needs: 24 GB+ for `nf4`, or an H100/A100 for comfortable `fp8` 2K renders.

- Pick a **ComfyUI** template/image (or a bare CUDA image for diffusers/CLI) and a GPU with enough VRAM (§4).
- **Update ComfyUI to nightly** inside the pod. The Ideogram-4 loaders are new, and pre-baked images often ship an older build.
- Authenticate to Hugging Face in the pod (`HF_TOKEN`) so the **gated** weights download (§1).
- The model is large. Use **persistent/network storage** for `models/` so you don't re-download multi-GB files on every pod start.
- **Licence still applies.** A paid cloud GPU is just compute. It does not convert the **non-commercial** weights into a commercial licence. Commercial output goes through the hosted API/web app.

---

## 2. diffusers

The pipeline class is **`Ideogram4Pipeline`**. Plain-text prompts work, but JSON captions (see `json-caption-guide.md`) give the best results. Sampling parameters come from named presets in `ideogram4.PRESETS`.

```python
import json, torch
from ideogram4 import Ideogram4Pipeline, Ideogram4PipelineConfig, PRESETS

pipe = Ideogram4Pipeline.from_pretrained(
    config=Ideogram4PipelineConfig(weights_repo="ideogram-ai/ideogram-4-nf4"),
    device="cuda",
    dtype=torch.bfloat16,
)

caption = {
  "high_level_description": "A golden retriever riding a skateboard down a sunny sidewalk.",
  "compositional_deconstruction": {
    "background": "A sun-drenched suburban sidewalk lined with green hedges and a white picket fence.",
    "elements": [
      {"type": "obj", "bbox": [200, 300, 800, 900], "desc": "A golden retriever standing on a red skateboard with all four paws, tongue out, ears flapping."}
    ]
  }
}

preset = PRESETS["V4_QUALITY_48"]
images = pipe(
    json.dumps(caption, separators=(",", ":"), ensure_ascii=False),
    height=1024, width=1024,
    num_steps=preset.num_steps,
    guidance_schedule=preset.guidance_schedule,
    mu=preset.mu, std=preset.std,
    seed=0,
)
images[0].save("out.png")
```

> The HF card also shows the generic `DiffusionPipeline.from_pretrained("ideogram-ai/ideogram-4-fp8", ...)` entry point; the repo's own examples use `Ideogram4Pipeline`/`Ideogram4PipelineConfig` as above.

### `pipe(...)` parameters

| Parameter | Default | Notes |
|---|---|---|
| `height` / `width` | 1024 | multiples of 16; range 256–2048; aspect ratios to 6:1 / 1:6 |
| `num_steps` | 48 | more = higher quality |
| `guidance_scale` | 7.0 | constant guidance when no schedule given; higher = more adherence |
| `guidance_schedule` | `None` | per-step weights (loop-index order: index 0 is the final/polish step); overrides `guidance_scale` |
| `mu` | 0.5 | logit-normal schedule mean (auto-adjusted for resolution; presets override) |
| `std` | 1.0 | logit-normal schedule std (presets override) |
| `seed` | `None` | set for reproducibility |
| `raise_on_caption_issues` | `True` | abort on `CaptionVerifier` warnings; set `False` to continue |

### Sampler presets (`ideogram4.PRESETS`) `[official — ideogram4.sampler_configs]`

| Preset | Steps | `guidance_schedule` (chronological) | `mu` | `std` |
|---|---|---|---|---|
| `V4_QUALITY_48` *(default)* | 48 | 45 @ 7.0, then 3 polish @ 3.0 | 0.0 | 1.5 |
| `V4_DEFAULT_20` | 20 | 18 @ 7.0, then 2 polish @ 3.0 | 0.0 | 1.75 |
| `V4_TURBO_12` | 12 | 11 @ 7.0, then 1 polish @ 3.0 | 0.5 | 1.75 |

> In source, `guidance_schedule` is stored in loop-index order (polish steps first): e.g. `(3.0,)*3 + (7.0,)*45`. The comment "index 0 is the LAST (polish) step" means chronologically you sample the gw-7 steps first, then the gw-3 polish steps. Define your own preset by adding to `ideogram4.sampler_configs.PRESETS`.

### Resolutions

Any `H×W` where both are multiples of 16 in 256–2048; aspect ratios to 6:1. Pair **2048×2048 with `V4_QUALITY_48`** for top quality. Examples: `1024×1024` (1:1), `1536×1024` (3:2), `1024×1536` (2:3), `1920×1088` (~16:9), `2048×768` (~21:9), `1024×1792` (~9:16), `1600×400` (4:1).

---

## 3. The `run_inference.py` CLI

This expands a plain `--prompt` into a JSON caption via Magic Prompt (on by default), then generates the image.

```bash
python run_inference.py \
  --prompt "a ginger cat wearing a tiny wizard hat reading a spellbook" \
  --output out.png \
  --quantization nf4 \
  --sampler-preset V4_QUALITY_48 \
  --height 2048 --width 2048 \
  --magic-prompt-key "$IDEOGRAM_API_KEY"
```

Key flags:

| Flag | Default | Notes |
|---|---|---|
| `--quantization` | `nf4` on CUDA, else `fp8` | which gated repo to load |
| `--sampler-preset` | `V4_QUALITY_48` | `V4_QUALITY_48` / `V4_DEFAULT_20` / `V4_TURBO_12` |
| `--height` / `--width` | 1024 | multiples of 16 |
| `--magic-prompt` / `--no-magic-prompt` | on | `--no-magic-prompt` feeds your prompt verbatim (use when you already have a JSON caption) |
| `--magic-prompt-model` | `ideogram-4-v1` | `ideogram-4-v1` (free hosted, `IDEOGRAM_API_KEY`) / `claude-opus-v1` / `claude-sonnet-v1` (OpenRouter, `MAGIC_PROMPT_API_KEY`) |
| `--magic-prompt-key` | env | required unless `--no-magic-prompt` |
| `--warn-on-caption-issues` | off | downgrade verifier aborts to warnings |
| `--hive-text-key` / `--hive-visual-key` | env | **optional external** Hive moderation of prompt/output; the CLI warns loudly if absent (screening is then off) |

Note: even the "free" `ideogram-4-v1` Magic Prompt is **server-side** and needs `IDEOGRAM_API_KEY`. For a fully-offline run, use `--no-magic-prompt` with a hand-written caption, or run the open-source system prompt through your own LLM.

---

## 4. ComfyUI (day-0 native support)

ComfyUI is a **runtime for the open weights**, and it added native support on launch day. Run it on your workstation or a cloud GPU pod (§1.1). It works the same either way. The official template is **`image_ideogram4_t2i.json`** (`Comfy-Org/workflow_templates`). The day-0 walkthrough is on `blog.comfy.org` and `docs.comfy.org/tutorials/image/ideogram/ideogram-v4`. **This requires an updated/nightly ComfyUI** because the loaders are new, and Desktop/Cloud builds on the stable channel may lag (pull nightly inside a pod). The node and file details below were read from the raw template JSON `[official — ComfyUI template JSON]`.

### File layout

```
ComfyUI/models/
├── vae/              flux2-vae.safetensors                      ← reuses the Flux.2 VAE
├── diffusion_models/ ideogram4_fp8_scaled.safetensors          ← conditional model
│                     ideogram4_unconditional_fp8_scaled.safetensors  ← unconditional model
└── text_encoders/    qwen3vl_8b_fp8_scaled.safetensors         ← text encoder
                      gemma4_e4b_it_fp8_scaled.safetensors      ← in-stack captioner LLM (separate Comfy-Org/gemma-4 repo)
```

> **Two diffusion models load**, combined via a `DualModelGuider`. This is the model's dual-branch (asymmetric) CFG: a conditional transformer plus a separate unconditional transformer, rather than a negative-prompt string. Ideogram 4 also **reuses Flux.2's VAE and latent space** (`flux2-vae.safetensors`, `EmptyFlux2LatentImage`).

### Key nodes (verbatim from the template)

| Node `type` | Role | Default widget values |
|---|---|---|
| `VAELoader` | Flux.2 VAE | `flux2-vae.safetensors` |
| `UNETLoader` ×2 | conditional + unconditional models | `ideogram4_fp8_scaled` / `ideogram4_unconditional_fp8_scaled`, `default` |
| `CLIPLoader` | Qwen3-VL text encoder | `qwen3vl_8b_fp8_scaled.safetensors`, type **`ideogram4`** |
| `CLIPTextEncode` | the prompt — **its default value is a JSON caption** | — |
| `EmptyFlux2LatentImage` | latent | `1024, 1024, 1` |
| `KSamplerSelect` | sampler | `euler` |
| `Ideogram4Scheduler` | schedule | `20, 1024, 1024, 0.5, 1.75` — 20 steps (the Default tier); the trailing `0.5, 1.75` are the node's schedule params (ComfyUI's parameterization differs from the diffusers preset's `mu`/`std`) |
| `DualModelGuider` | asymmetric CFG over both models | guidance `7` |
| `CFGOverride` | per-step CFG ramp | `[3, 0.7, 1]` (the `0.7` reads as the override start fraction; exact field meaning `[community — single report; re-verify]`) |
| `CustomCombo` | preset selector | Quality / **Default** / Turbo |
| `SamplerCustomAdvanced`, `VAEDecode`, `SaveImage` | sampling + decode + save | output prefix `Ideogram_4.0` |

Defaults are **euler / 20 steps / DualModelGuider 7**, latent 1024×1024. The `CustomCombo` switches between Quality (48), Default (20), and Turbo (12).

### The two prompt modes

- **Natural language** — type a sentence. This is quick, and good for simple ideas.
- **Structured JSON** — paste a JSON caption directly into the multiline `CLIPTextEncode` field. Its default already holds a JSON object. Downstream `JsonExtractString` nodes pull width, height, and other fields out of it.

### The `gemma4` puzzle

`gemma4_e4b_it_fp8_scaled.safetensors` is in the required-download list, from a separate `Comfy-Org/gemma-4` repo, but **no node in the shipped template actually loads it.** It is the recommended **in-stack** LLM for the natural-language-to-JSON-caption step: it runs on your own GPU instead of relying on the hosted `ideogram-4-v1` Magic Prompt. The template does include an "Ideogram4 Caption Prompt Template" helper subgraph, a set of string nodes that assemble the system prompt plus your idea, but it contains **no LLM-execution node**. You run that conversion through gemma4 yourself. Downloading gemma4 and then finding nothing to plug it into is a common first-day confusion `[official — ComfyUI template JSON]`.

### The three ComfyUI quants

The ComfyUI diffusion models live in `Comfy-Org/Ideogram-4` on Hugging Face, under `diffusion_models/`. As of 2026-09-09 that folder holds **three quants, each as a conditional + unconditional pair**, and nothing else `[official — Comfy-Org/Ideogram-4 repo, 2026-09-09]`:

| Conditional file | Unconditional pair | Quant | Notes |
|---|---|---|---|
| `ideogram4_fp8_scaled.safetensors` | `ideogram4_unconditional_fp8_scaled.safetensors` | fp8, scaled | What the official template loads. The default |
| `ideogram4_nvfp4_mixed.safetensors` | `ideogram4_unconditional_nvfp4_mixed.safetensors` | NVFP4, mixed precision | **The ComfyUI 4-bit file.** This is what the community workflows that referenced `nvfp4_mixed` were pointing at |
| `ideogram4_int8_convrot.safetensors` | `ideogram4_unconditional_int8_convrot.safetensors` | int8, convolutional rotation | Newest of the three (conditional file 9.58 GB). Same build family as the `int8_convrot` files [`z-image`](../../z-image/) ships |

**The old naming puzzle is closed.** Earlier versions of this skill flagged a conflict between `nf4` (the HF repo name) and `nvfp4_mixed` (what workflows referenced). There was no conflict. `nf4` is the bitsandbytes quant in `ideogram-ai/ideogram-4-nf4`, which is a **diffusers** file; the Comfy-Org repo has no `nf4` file at all. `nvfp4_mixed` is the ComfyUI 4-bit file. They are different files for different runtimes, and the confusion came from reading one repo's listing against the other's workflows. Swap a pair in by changing both `UNETLoader` widgets; the rest of the graph is the same.

**What is not published yet:** a quality or speed comparison between `int8_convrot`, `fp8_scaled` and `nvfp4_mixed` on this model, or a VRAM figure per pair `[flagged — re-verify]`. Until one appears, the only sizing guidance is the general one: fp8 is the reference, the 4-bit file is the smallest, and int8 sits between them on disk.

### VRAM

- **nf4** (diffusers) fits a single **24 GB** GPU `[official — HF model card]`; **32 GB** is recommended.
- **fp8** reportedly ran on **16 GB VRAM / 32 GB RAM** (~48-step image in <5 min; turbo-12 in <90 s) `[community — single report; re-verify]`.
- The ComfyUI pairs above have no published per-quant VRAM numbers (see the flag in the previous section).

### TurboTime — a speed LoRA that removes the second model

ostris (the ai-toolkit author) published **Ideogram 4 TurboTime**, on Hugging Face as `ostris/ideogram_4_turbotime_lora` and on Civitai (2026-06). Its claim: the model runs in **as few as 2 steps, with no CFG and no unconditional model** `[community — ostris, HF + Civitai]`. This is the same pattern as Wan's lightx2v LoRAs ([`wan-2-2`](../../wan-2-2/)): guidance is distilled into the weights, so you stop asking for it at sampling time.

What that does to the stock graph, reasoned from the claim rather than transcribed from a published node list: the second `UNETLoader` and the `DualModelGuider` come out, because there is no unconditional branch to guide against. The LoRA loads on the **conditional** model, and sampling runs at CFG 1 with a step count near the author's 2. Check the model card for the exact graph and step range before assuming these. Two cautions. It is one author's release with no independent reproduction on record, so whether the quality holds outside the author's samples is open `[flagged — re-verify]`. And nothing here changes the licence: a faster non-commercial model is still non-commercial.

### GGUF

There is no official GGUF. A community `stduhpf/ideogram-4-gguf` and an `unsloth/gemma-4-E4B-it-GGUF` (for the captioner) have surfaced, but they are early and undocumented. `city96/ComfyUI-GGUF` support for the Ideogram-4 architecture is **unconfirmed** `[community — early; re-verify]`.

---

## 5. Safety filter (self-hosted)

Two layers, both `[official]`:

1. **Model-level NSFW filter.** Blocked generations return a gray screen reading "Image blocked by safety filter". It is in the weights and cannot be disabled in ComfyUI or diffusers. **False-positive rates are higher for plain-text than JSON prompts** — using a JSON caption reduces spurious blocks. The team has acknowledged over-blocking and signalled a future checkpoint update.

   **The filter is real, but it is not absolute.** That difference matters, because "in the weights" was being read as "route elsewhere entirely". An adult generation has been posted from the open weights with two ordinary style LoRAs loaded (`real engine` and `lenovo` at 0.4 strength, 48 steps, driven by a JSON caption) `[community — Ashamed-Ad7403, r/unstable_diffusion; single report]`. One of the published Civitai LoRAs is named `Gray Screen bypass` (`lora-training.md` §4), so somebody is building for exactly this. The Civitai shelf went from zero adult-flagged entries on 2026-08-13 to ~26% explicit across 34 on 2026-08-23 `[community — Civitai baseModel census, 2026-08-23]`. None of that explains the mechanism: it is unclear whether a LoRA displaces the filtered behaviour, or whether the reports simply sit inside the filter's false-negative margin `[flagged — re-verify]`. Plan for the gray screen. Do not plan on defeating it.
2. **Optional external Hive moderation.** This is wired into the reference `run_inference.py` (text and visual). You supply `HIVE_TEXT_MODERATION_KEY` / `HIVE_VISUAL_MODERATION_KEY`. If absent, that screening is simply off (the CLI warns).

(The ComfyUI blog's "safety is baked into the weights, can't disable" refers to layer 1; the Hive layer 2 is the optional external one in the reference code.)

---

## 6. Using a LoRA you have trained

This section is short because the ecosystem has not filled this gap in yet. **Making** a LoRA is
covered in `lora-training.md`. This section covers the *using* half of that split.

- **Format.** fal's trainer emits a `comfy`-format `.safetensors` alongside its own. That is an
  ordinary ComfyUI LoRA file, and it is the one you load. ai-toolkit and musubi-tuner write their
  output in the same place they do for every other model they support. **OneTrainer's output does
  not load.** Its Ideogram4 extension writes split `to_q`/`to_k`/`to_v` keys, and ComfyUI logs
  `lora key not loaded` for each of them; the issue has been open since 2026-06-14
  `[community — ComfyUI issue #14477]`. If you see that message, the trainer is the cause, not
  your graph.
- **Where it plugs in.** The shipped template `image_ideogram4_t2i.json` contains **no LoRA loader
  node at all**, and no wired example has been published by Comfy-Org, by fal, or on Civitai
  `[flagged — re-verify]`. Ideogram 4 also loads **two** diffusion models (§4), so it is an open
  question rather than a settled default which branch the LoRA attaches to: the conditional model,
  the unconditional model, or both. Expect to wire it yourself, and to test whether the
  unconditional branch needs the same patch. One data point now exists: ostris's TurboTime LoRA
  (§4) removes the unconditional model entirely, so it patches the conditional branch alone. That
  settles the question for a distillation LoRA. It does not settle it for a style LoRA that keeps
  both branches.
- **Strengths and stacking.** There are no published weight bands, and there are no reports on
  stacking two LoRAs `[flagged — re-verify]`. Sweep from 1.0 downward as you would on any DiT, and
  judge by eye. Do not import a band from another model's skill, because the dual-branch guider
  makes the effective strength non-comparable.

If you get this working, it would be the most useful thing anyone could currently write up about
Ideogram 4.
