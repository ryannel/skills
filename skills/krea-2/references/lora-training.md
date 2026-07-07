# Krea 2 — LoRA training

**Making** a LoRA for Krea 2. Using/stacking one is `setup-and-workflows.md §6`; the character pipeline end-to-end is `characters.md`. The ecosystem is ~2 weeks old (open weights 2026-06-22): the official doctrine is unusually explicit, one full named recipe exists, and the biggest question is genuinely contested. Verified 2026-07-07.

## Contents
1. [The doctrine — and the dispute](#1-the-doctrine--and-the-dispute)
2. [musubi-tuner (the fullest documented path)](#2-musubi-tuner-the-fullest-documented-path)
3. [AI-Toolkit and the Ostris turbo-adapter path](#3-ai-toolkit-and-the-ostris-turbo-adapter-path)
4. [fal hosted trainer](#4-fal-hosted-trainer)
5. [Captioning doctrine](#5-captioning-doctrine)
6. [Character LoRAs: the JahJedi recipe](#6-character-loras-the-jahjedi-recipe)
7. [Style LoRAs](#7-style-loras)
8. [Evaluation](#8-evaluation)

---

## 1. The doctrine — and the dispute

**Official: "TRAIN on Raw and RUN on Turbo"** (caps theirs) [official — GitHub FAQ]. Raw is the undistilled checkpoint — "diverse and highly malleable… what you should use for fine-tuning, post-training, and LoRA training"; "LoRAs trained on RAW are designed to express strongly on Turbo" [official — README / krea-2-open-source page]. This is the same base-not-distilled principle as every distilled family (Z-Image, FLUX.2 klein), but Krea is the first lab to make the cross-checkpoint transfer an explicit, designed-for contract — they even ship the distillation itself as a LoRA (`krea2_turbo_lora_rank_64_bf16.safetensors`), which is why Raw-trained LoRAs compose with Turbo so directly.

**The dispute:** Ostris (AI-Toolkit) ships a **de-distillation training adapter** (`ostris/krea2_turbo_training_adapter`) for training *directly on Turbo* — the adapter (a LoRA trained at LR 1e-5 on thousands of Turbo generations) holds the step-distillation together during fine-tuning and is removed at inference, so your LoRA runs on Turbo at full speed. Ostris's position: for short runs (styles, concepts, characters), "training directly on the turbo model could yield better results" [official-Ostris — HF adapter card]. Kohya's musubi docs and Krea's own docs stay Raw-first.

**How to choose today:** both paths now have named end-to-end successes — Raw-path characters (JahJedi, §6) and styles (urabewe, §7; the Arthemy Comics author "training a highly specialized LoRA on the RAW version, as the Krea team suggested"), and Turbo/AI-Toolkit successes including multi-character LoKr runs. Raw-first remains the doctrine-backed default and the path both trainers document; the Turbo-adapter path is lighter on VRAM (§3) and fine for short runs. Which produces *better* LoRAs is still unresolved — A/B if the run matters, and re-check before long training runs.

Two structural facts that hold on either path (encoder-class doctrine):
- **DiT-only.** The Qwen3-VL encoder is never trained; Krea 2 LoRAs are model-only (`LoraLoaderModelOnly` at load time).
- **No rare-token triggers.** Fold a natural descriptive phrase into captions and prompts; the official style LoRAs' triggers are phrases like `monochrome ink wash style` (`prompting-guide.md §5`).

## 2. musubi-tuner (the fullest documented path)

Kohya's musubi-tuner added day-0 experimental Krea 2 support [official-kohya — docs/krea2.md; announcement on X]. This is the most completely documented trainer and the source of several load-bearing architecture facts (28 blocks, GQA 48Q/12KV, the resolution-aware shift schedule).

**Models needed:** Raw DiT (`raw.safetensors` from `krea/Krea-2-Raw`); optionally Turbo DiT for sampling; the **Qwen-Image VAE** (same file ComfyUI uses); **Qwen3-VL-4B-Instruct as a single safetensors file** (the Comfy-Org `qwen3vl_4b_bf16.safetensors` works and can be shared with ComfyUI).

**Pre-cache both stages** (image latents via `krea2_cache_latents.py --vae …`; text-encoder outputs via `krea2_cache_text_encoder_outputs.py --text_encoder …` — Krea 2 caches the 12-layer hidden-state stack, so the encoder isn't needed during training itself).

**Training** (`krea2_train_network.py` — the authors'-default configuration, verbatim-adjacent from the docs):

```bash
accelerate launch --num_cpu_threads_per_process 1 --mixed_precision bf16 \
  src/musubi_tuner/krea2_train_network.py \
  --dit raw.safetensors --vae qwen_image_vae.safetensors --dataset_config data.toml \
  --sdpa --mixed_precision bf16 \
  --timestep_sampling shift --weighting_scheme none --discrete_flow_shift 2.5 \
  --optimizer_type adamw8bit --learning_rate 1e-4 --gradient_checkpointing \
  --network_module networks.lora_krea2 --network_dim 32 --network_alpha 32 \
  --max_train_epochs 16 --save_every_n_epochs 1 --seed 42 \
  --output_dir out --output_name my-lora
```

Key facts from the docs [official-kohya]:

- **rank/alpha 32 all-Linear "reproduces the model authors' recommended default"** — 264 Linear layers: attention, MLPs, the text-fusion transformer, projections. The authors' **"long training run" config** is the opposite trade: attention-only (140 Linears — `wq/wk/wv/wo/gate`, via an `exclude_patterns` network-arg) at *higher* rank, to preserve prompt adherence over long runs.
- **Flow shift:** `--discrete_flow_shift 2.5` matches K2's inference-time shift at 1024² (the schedule is resolution-aware: ~1.6 @ 256², ~3.2 @ 1280²). For bucketed multi-resolution datasets, `--timestep_sampling krea2_shift` reproduces the per-sample resolution-aware schedule exactly, no fixed shift needed. (`flux_shift` is close but saturates at 1024px instead of 1280px.) The docs' own caveat: "the optimal settings are not yet established."
- **Memory:** `--fp8_base --fp8_scaled` (must be together; fp8 covers the 28 main blocks, the text-fusion stage stays bf16); `--blocks_to_swap` up to **26**; `--gradient_checkpointing`; `--compile` for the main blocks. **12 GB is enough in practice**: a named style-LoRA config on an RTX 3060 12 GB / 48 GB RAM runs `--fp8_base --fp8_scaled --blocks_to_swap 18 --block_swap_h2d_only --block_swap_ring_size 1 --split_attn --gradient_checkpointing_cpu_offload` — ~1,200 steps in ~2 h at ~5.9 s/it on 30-image datasets [community — urabewe, r/StableDiffusion, full command published].
- **Sample on Turbo while training Raw:** `--turbo_dit turbo.safetensors` applies the in-training LoRA on top of Turbo weights for previews (`--l 1 --s 8` in the sample prompt — CFG off, 8 steps) — previewing on the checkpoint you'll actually run is the doctrine made ergonomic. Raw-side samples need CFG (CFG-off Raw output is blurry by design). `--turbo_dit` is incompatible with `--blocks_to_swap`.
- **Inference script** (`krea2_generate_image.py`) uses the **classic CFG scale** (≤1 = off): Turbo = `--steps 8 --guidance_scale 1 --mu 1.15`; Raw default `--guidance_scale 5.5` ≙ official guidance 4.5. Fits a 24 GB card with `--fp8_scaled` and/or block swap; LoRAs merge into base weights at load (the only correct route under fp8).

## 3. AI-Toolkit and the Ostris turbo-adapter path

Krea's README lists Ostris AI-Toolkit as a recommended trainer [official]; the architecture key is `krea2`. As of 2026-07-07 there is **no krea2 example YAML in the repo's `config/examples/`** — configure through the UI or adapt a nearby DiT config:

- **Raw path:** standard AI-Toolkit LoRA run against Raw. Hardware gotcha with a named fix: Raw training **OOMs early on a 24 GB RTX 3090 even in Low-VRAM mode** (fails around 3 GB allocated, 32 GB system RAM) until **Layer Offloading is set to ~10%** (5% also works and is slightly faster) [community — Fast-Cash1522, r/StableDiffusion, marked SOLVED].
- **The best-replicated character recipe** runs on this path: **LoKr factor 4, Automagic3 optimizer, sigmoid scheduling, "Balanced", LR 1e-4 + weight decay, 1024-only, ~50-image datasets, 2–3k steps** — likeness rated above the author's Z-Image results across multiple characters [community — Any_Tea_3499]. Note it's LoKr, not classic LoRA — factor 4 is the capacity knob standing in for rank.
- **Turbo-adapter path:** load `ostris/krea2_turbo_training_adapter` as the training adapter over Turbo; train your LoRA; the adapter is dropped at inference. Made for short runs — styles, concepts, characters [official-Ostris — adapter card]. Lighter than Raw on the same hardware (the 3090 user above trained Turbo+adapter "without any issues" on the settings that OOM'd Raw).
- Ostris also ships a Krea 2 **edit-training** stack (paired-data edit LoRAs + a 3-reference-image ComfyUI node) — that's `characters.md §3`, not classic LoRA training.

## 4. fal hosted trainer

`fal-ai/krea-2-trainer` (train) + `fal-ai/krea-2/turbo/lora` (run) [official — README / fal]. Zero-setup path; hyperparameters are managed. Weights come back as standard safetensors LoRAs usable locally.

## 5. Captioning doctrine

Encoder-class rule (LLM/VLM encoder): **prose captions, caption-the-residual** — describe what varies and what should *not* be absorbed into the trigger; leave the identity/style itself uncaptioned so it binds to the trigger phrase. The one named Krea-2-specific data point agrees: JahJedi captions "describe only what is visible" — plain factual prose per image [community — JahJedi]. Character vs style inverts what you caption (character: caption clothing/pose/background so identity binds; style: caption subjects so the *look* binds — `z-image` and `flux-2` skills document the shared craft in depth). **Captionless training** is contested on every DiT family and has no Krea-2-specific evidence either way yet — flag any strong claim you meet as unverified.

A Krea-2-specific caption lesson from multi-character training: a LoRA whose training captions were literal scene descriptions holds up when *prompted in the same register*, and falls apart (character bleed, identity drift) under free-form creative prompts [community — krigeta1's documented failure case]. The residual rule cuts both ways — what you caption is what stays *promptable*, so caption in the register you intend to prompt in, and vary caption phrasing across the dataset if you want prompt flexibility.

## 6. Character LoRAs: two named recipes

The lighter, better-replicated recipe is Any_Tea_3499's AI-Toolkit LoKr run (§3: ~50 images, 2–3k steps, LoKr 4 / Automagic3 / sigmoid / LR 1e-4, likeness > Z-Image). The heavyweight musubi/Raw recipe with full settings and outcome [community — JahJedi, HF `krea2-character-lora-recipe`]:

| Parameter | Value |
|---|---|
| Trainer / base | musubi-tuner on **Raw** |
| Dataset | 474 character images + 348 regularisation images |
| Network | dim/alpha **32** |
| LR / optimizer | **1e-4**, AdamW, fp32 |
| Steps | ~13,000 (~4.6 h on the author's hardware) |
| Captions | "describe only what is visible" |
| Result | identity holds at **weight 0.8** under heavy style-LoRA mixing, run on Turbo |

Notes: the dataset is much larger than the 20–50-image protocol that works on sibling models (`characters.md §2`) — nobody has yet published whether Krea 2 *needs* the larger set or JahJedi simply had one. Start smaller, evaluate, extend if identity is unstable. A community wrapper trainer exists (`bongobongo2020/krea2-character-lora-trainer`) — unexamined, verify before trusting.

## 7. Style LoRAs

- Krea's own style-LoRA line (nine on Comfy-Org + the `krea/krea-2-loras` HF collection) demonstrates the format: rank ~modest, DiT-only, natural-phrase trigger, strength 0.8–1.0. No official training write-up accompanies them. The community layer is already large — **1,500+ style LoRAs from a single named trainer** (ilker's `fal-Krea-2-Style-LoRAs`, highlighted in Krea's own community roundup) plus a steady Civitai stream.
- **Named Raw-path style runs with published settings:** urabewe's Garbage Pail Kids / Ren & Stimpy LoRAs — musubi defaults (§2), 30-image datasets, ~1,200–1,250 steps, ~2 h on a 12 GB 3060, used at strength **1.0 with no trigger word** (nudge with "cartoon"/"animation" when needed) [community — urabewe, full command + dataset-builder tool published]. Philosopher_Jazzlike's anime-style LoRA (config attached on Civitai; run at 0.85 stacked with a second LoRA at 1.0) reports Krea 2 Turbo "absolutely brilliant at adopting styles while still executing the prompt" [community — r/StableDiffusion]. The style community's consensus-forming rate is fast; strength-1.0-no-trigger is emerging as a common style pattern, in contrast to the official LoRAs' appended trigger phrases — read each author's card.
- Style dataset craft is the suite-shared kind (diverse subjects so the style doesn't bind to content; composition-memorisation and color-cast lock-in as overfit signals; out-of-set subject as the acceptance test) — see `sdxl`/`z-image` lora-training references for the full treatment.
- Style rank on Krea 2: rank/alpha 32 (musubi default) is what the named style runs above used; the rank-64 Turbo LoRA brackets the high end. LoKr-factor-4 is the AI-Toolkit-side equivalent anchor (§3).

## 8. Evaluation

- **Validate on Turbo, not Raw** — you ship on Turbo; musubi's `--turbo_dit` sampling exists precisely for this (§2). A LoRA that looks great on Raw at cfg 3.5 and falls apart at 8-step guidance-off has failed its acceptance test.
- XY-grid epoch × strength, as on every family: identity/style vs stacking headroom. Krea-2-specific axis worth adding: **with and without the Wan-VAE swap**, since much of the perceived quality difference lives in the decode (`setup-and-workflows.md §5`).
- Overfit signals are the standard ones (same-face, composition memorisation, style bleed into untriggered prompts); the Krea-2-specific confound is the **muted-expression tax** — don't diagnose "expression lock-in" in your LoRA before checking the base model produces the expression at all (`SKILL.md`, *two taxes*).
