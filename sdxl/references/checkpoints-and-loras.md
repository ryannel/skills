# SDXL Checkpoints, LoRAs & Control Tooling

The defining practical fact about SDXL: **you almost never run base 1.0 raw — you run a finetune of it.** This file maps the ecosystem. Everything here is **community tier** unless a licence is cited from a model card — verify current versions and licences on the model page (these move; the base model doesn't).

## Table of contents
1. Why finetunes, and the two dialect families
2. The photoreal / general finetunes
3. The anime / booru finetunes (Pony, Illustrious/NoobAI)
4. The fast-variant LoRAs (stacking speed onto any finetune)
5. LoRA training (kohya_ss / OneTrainer)
6. ControlNet & IP-Adapter catalog

---

## 1. Why finetunes, and the two dialect families

Base SDXL 1.0 is a strong foundation but looks undertrained/"plasticky" next to community finetunes that trained it harder on curated data. Finetunes split into **two dialect families** that do not share prompt style *or* LoRA pools:

- **Photoreal/general family** — base, Juggernaut, RealVisXL, DreamShaper. **Dialect:** descriptive photo-keywords (prompting-guide §1–5). LoRAs trained on base SDXL work here.
- **Anime/booru family** — Pony V6, Illustrious, NoobAI. **Dialect:** tag-based (score tags / booru tags). **Separate LoRA pool** — base-SDXL LoRAs don't transfer, and these models drifted far enough from base that they're effectively their own ecosystems.

Match both the **dialect** and the **LoRA pool** to the checkpoint family.

---

## 2. Photoreal / general finetunes

| Checkpoint | Maker | For | Notes |
|---|---|---|---|
| **Juggernaut XL** | RunDiffusion | all-purpose **photoreal**, the default "just works" pick | strong skin/lighting/anatomy; frequent version bumps (v9/v10/v11 line) — check current |
| **RealVisXL** | SG161222 | **maximum photorealism**, portraits, skin/hair | the realism specialist; v5 current line |
| **DreamShaper XL** | Lykon | artistic / fantasy / concept-art generalist | handles stylised scenes; looser prompts |
| **ZavyChroma XL** | — | general, vivid colour, realism/art balance | |
| **NightVision / epiCRealism XL / CrystalClear** | — | further photoreal options | similar dialect; try-and-compare |

All use the **photo-keyword dialect**. Most are OpenRAIL++-M or a permissive Civitai licence (commercial often allowed *with* restrictions like no model-merge resale) — **verify per model**, as Civitai licences vary by uploader.

---

## 3. Anime / booru finetunes

**Pony Diffusion V6 XL** — wildly popular, very flexible (anime/furry/cartoon, strong concept flexibility). Its own sub-ecosystem.
- **Dialect:** start every prompt with the **score ladder** `score_9, score_8_up, score_7_up, score_6_up, score_5_up, score_4_up`, then a **source tag** (`source_anime` / `source_pony` / `source_furry` / `source_cartoon`), a **rating** (`rating_safe` / `rating_questionable` / `rating_explicit`), then Danbooru content tags.
- Normal photoreal prompts produce poor results. Pony **LoRAs are a separate pool**.

**Illustrious XL / NoobAI XL** — leading **anime/illustration** bases, trained on Danbooru tag vocabularies; the current go-to for anime finetuning and LoRAs.
- **Dialect:** comma-separated **booru tags** (`1girl, solo, <character>, <series>, <attributes>`), plus the model's quality tags (`masterpiece, best quality` — which *do* work here, unlike on photoreal SDXL). NoobAI is an Illustrious-derived community continuation; check its card for the exact quality-tag convention and any model-specific tags.
- Separate LoRA pool from base SDXL and from Pony.

---

## 4. The fast-variant LoRAs (stacking speed onto any finetune)

The speed axis composes with the style axis because Lightning, LCM, and Hyper-SDXL all ship as **LoRAs**:

| LoRA | Steps | Sampler · Scheduler | CFG (ComfyUI / diffusers) | Notes |
|---|---|---|---|---|
| **SDXL Lightning LoRA** | 2 / 4 / 8 | `euler` · `sgm_uniform` | 1 / 0.0 | match LoRA file to step count; 4-step popular |
| **LCM-LoRA (SDXL)** | 4–8 | `lcm` · `sgm_uniform` | 1–2 / 1.0–2.0 | needs `ModelSamplingDiscrete`→`lcm`; most portable |
| **Hyper-SDXL LoRA** | 1 / 2 / 4 / 8 | `euler` · `sgm_uniform` | ~1 / ~0.0 | best 1-step; some modes use a unified-guidance LoRA |

**Workflow:** load your finetune → `LoraLoader` (the fast LoRA, strength ~1.0) → set the matching sampler/scheduler/CFG/steps. Result: e.g. **RealVisXL + 4-step Lightning LoRA** = photoreal draft in 4 steps. You can also stack a *content* LoRA on top (character/style) — chain multiple `LoraLoader` nodes; keep content-LoRA strength ~0.6–0.9 so it doesn't fight the speed LoRA. Note distilled = guidance off, so **negatives are inert** in these stacks.

---

## 5. LoRA training (kohya_ss / OneTrainer)

SDXL LoRA training is the most mature in open-source image gen.

- **Tools:** **kohya_ss** (`sd-scripts`, the de-facto standard, GUI + CLI) and **OneTrainer** (friendlier UI, good defaults). Both train SDXL LoRA/LoCon/LoHA and full finetunes.
- **Base for training:** train **character/style LoRAs on base SDXL 1.0** for maximum compatibility across the photoreal family; train on **Pony/Illustrious** if you specifically target those (the result only works on that family).
- **Rough hyperparameters (community starting points, not gospel):** rank/dim 16–32, alpha = rank or rank/2, LR ~1e-4 (UNet) / ~5e-5 (text encoder, or freeze it), batch 1–4, 1024-area bucketed images, ~1500–3000 steps for a character, AdamW8bit or Prodigy optimizer, cosine schedule. VRAM: ~12 GB with gradient checkpointing + 8-bit optimizer; 16–24 GB comfortable.
- **Dataset:** for a character, vary pose/angle/lighting and keep the identity constant (cover the full rotation/elevation range — front, 3/4, profile, low angle, high angle — same diffusion-dataset principles apply). **Caption in the target dialect:** booru tags for Pony/Illustrious, descriptive phrases for photoreal SDXL.
- **ControlNet/IP-Adapter** often substitute for training when you need pose/identity control on a one-off (no training run needed).

---

## 6. ControlNet & IP-Adapter catalog

(Setup/wiring is in `references/setup-and-workflows.md` §7; this is the model roster.)

**ControlNet models for SDXL:**
- Stability's official SDXL ControlNets (canny, depth) + the broader community set from **`xinsir`** (high-quality canny/openpose/scribble/depth), **`diffusers`**, **`kohya`** (the "control-lora" slim variants), and **`thibaud`** (openpose).
- **`xinsir/controlnet-union-sdxl-1.0`** — one model, many control types (the convenient default).
- Preprocessors: `comfyui_controlnet_aux` (DepthAnything, OpenPose, Canny, Lineart, SoftEdge, Normal, MLSD, etc.).

**IP-Adapter models for SDXL** (`h94/IP-Adapter`):
- `ip-adapter_sdxl` / `ip-adapter-plus_sdxl` — image-prompt / style transfer (Plus = finer detail).
- `ip-adapter-faceid_sdxl` / `ip-adapter-faceid-plusv2_sdxl` — identity transfer (needs InsightFace embeddings).
- Strength ~0.5–0.8; combine with ControlNet for pose+identity. This is SDXL's standout capability — identity and structure control with no training, far ahead of most newer DiT models' tooling.

---

**Reminder on volatility:** finetune *versions* and Civitai *licences* change often, and new fast-variant LoRAs appear. The base SDXL facts (architecture, the OpenRAIL++-M base licence, the ComfyUI graph) are stable since July 2023; treat the roster above as a snapshot and check the model page before committing, especially for commercial use.
