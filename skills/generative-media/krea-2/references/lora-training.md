# Krea 2 — LoRA training

> **Shared craft lives in [`character-lora-training`](../../character-lora-training/)** — dataset coverage, caption-the-residual, evaluation, adult/NSFW base selection, and the real-person likeness rules that decide whether a LoRA is publishable. This file covers what is specific to this model.


**Making** a LoRA for Krea 2. Using/stacking one is `setup-and-workflows.md §6`; the character pipeline end-to-end is `characters.md`. Open weights landed 2026-06-22; the official doctrine is unusually explicit, several full named recipes now exist, and the biggest question is genuinely contested. Verified 2026-07-07; community sections refreshed 2026-08-22; §3/§3a re-verified and extended 2026-08-26.

## Contents
1. [The doctrine — and the dispute](#1-the-doctrine--and-the-dispute)
2. [musubi-tuner (the fullest documented path)](#2-musubi-tuner-the-fullest-documented-path)
   - [2a. Training on 12 GB](#2a-training-on-12-gb--the-low-vram-configuration)
   - [2b. Adult / NSFW work](#2b-adult--nsfw-work)
   - [2c. 16 GB, measured — and four corrections](#2c-16-gb-measured--and-four-corrections-that-came-out-of-it)
3. [AI-Toolkit and the Ostris turbo-adapter path](#3-ai-toolkit-and-the-ostris-turbo-adapter-path)
   - [3a. A working AI-Toolkit Raw config](#3a-a-working-ai-toolkit-raw-config-and-where-the-trainer-gets-its-encoder)
4. [fal hosted trainer](#4-fal-hosted-trainer)
5. [Captioning doctrine](#5-captioning-doctrine)
6. [Character LoRAs: two named recipes](#6-character-loras-two-named-recipes)
7. [Style LoRAs](#7-style-loras)
8. [Evaluation](#8-evaluation)

---

## 1. The doctrine — and the dispute

**Official: "TRAIN on Raw and RUN on Turbo"** (caps theirs) `[official — GitHub FAQ]`. Raw is the undistilled checkpoint — "diverse and highly malleable… what you should use for fine-tuning, post-training, and LoRA training"; "LoRAs trained on RAW are designed to express strongly on Turbo". This is the same base-not-distilled principle as every distilled family (Z-Image, FLUX.2 klein), but Krea is the first lab to make the cross-checkpoint transfer an explicit, designed-for contract — they even ship the distillation itself as a LoRA (`krea2_turbo_lora_rank_64_bf16.safetensors`), which is why Raw-trained LoRAs compose with Turbo so directly.

**The dispute:** Ostris (AI-Toolkit) ships a **de-distillation training adapter** (`ostris/krea2_turbo_training_adapter`) for training *directly on Turbo* — the adapter (a LoRA trained at LR 1e-5 on thousands of Turbo generations) holds the step-distillation together during fine-tuning and is removed at inference, so your LoRA runs on Turbo at full speed. Ostris's position: for short runs (styles, concepts, characters), "training directly on the turbo model could yield better results" `[official — Ostris HF adapter card]`. Kohya's musubi docs and Krea's own docs stay Raw-first.

**How to choose today:** both paths now have named end-to-end successes — Raw-path characters (JahJedi, §6) and styles (urabewe, §7; the Arthemy Comics author "training a highly specialized LoRA on the RAW version, as the Krea team suggested"), and Turbo/AI-Toolkit successes including multi-character LoKr runs. Raw-first remains the doctrine-backed default and the path both trainers document; the Turbo-adapter path is lighter on VRAM (§3) and fine for short runs. Which produces *better* LoRAs is still unresolved — A/B if the run matters, and re-check before long training runs.

Two structural facts that hold on either path (encoder-class doctrine):
- **DiT-only.** The Qwen3-VL encoder is never trained; Krea 2 LoRAs are model-only (`LoraLoaderModelOnly` at load time).
- **No rare-token triggers.** Fold a natural descriptive phrase into captions and prompts; the official style LoRAs' triggers are phrases like `monochrome ink wash style` (`prompting-guide.md §5`).

## 2. musubi-tuner (the fullest documented path)

Kohya's musubi-tuner added day-0 experimental Krea 2 support `[official — musubi docs/krea2.md]`. This is the most completely documented trainer and the source of several load-bearing architecture facts (28 blocks, GQA 48Q/12KV, the resolution-aware shift schedule).

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

Key facts from the docs:

- **rank/alpha 32 all-Linear "reproduces the model authors' recommended default"** — 264 Linear layers: attention, MLPs, the text-fusion transformer, projections. The authors' **"long training run" config** is the opposite trade: attention-only (140 Linears — `wq/wk/wv/wo/gate`, via an `exclude_patterns` network-arg) at *higher* rank, to preserve prompt adherence over long runs.
- **Flow shift:** `--discrete_flow_shift 2.5` matches K2's inference-time shift at 1024² (the schedule is resolution-aware: ~1.6 @ 256², ~3.2 @ 1280²). For bucketed multi-resolution datasets, `--timestep_sampling krea2_shift` reproduces the per-sample resolution-aware schedule exactly, no fixed shift needed. (`flux_shift` is close but saturates at 1024px instead of 1280px.) The docs' own caveat: "the optimal settings are not yet established."
- **Memory:** `--fp8_base --fp8_scaled` (must be together; fp8 covers the 28 main blocks, the text-fusion stage stays bf16); `--blocks_to_swap` up to **26**; `--gradient_checkpointing`; `--compile` for the main blocks. **12 GB is enough in practice**: a named style-LoRA config on an RTX 3060 12 GB / 48 GB RAM runs `--fp8_base --fp8_scaled --blocks_to_swap 18 --block_swap_h2d_only --block_swap_ring_size 1 --split_attn --gradient_checkpointing_cpu_offload` — ~1,200 steps in ~2 h at ~5.9 s/it on 30-image datasets `[community — urabewe, r/StableDiffusion, full command published]`.
- **Sample on Turbo while training Raw:** `--turbo_dit turbo.safetensors` applies the in-training LoRA on top of Turbo weights for previews (`--l 1 --s 8` in the sample prompt — CFG off, 8 steps) — previewing on the checkpoint you'll actually run is the doctrine made ergonomic. Raw-side samples need CFG (CFG-off Raw output is blurry by design). `--turbo_dit` is incompatible with `--blocks_to_swap`.
- **Inference script** (`krea2_generate_image.py`) uses the **classic CFG scale** (≤1 = off): Turbo = `--steps 8 --guidance_scale 1 --mu 1.15`; Raw default `--guidance_scale 5.5` ≙ official guidance 4.5. Fits a 24 GB card with `--fp8_scaled` and/or block swap; LoRAs merge into base weights at load (the only correct route under fp8).

## 2a. Training on 12 GB — the low-VRAM configuration

A fully documented 12 GB path exists, and it is worth stating precisely because the naive attempt fails `[community — SirMick, Civitai, 2026-07]`. Verified on an **RTX 3060 12 GB, 64 GB system RAM, Windows**, with musubi-tuner.

**Why it is hard:** the full stack far exceeds the card.

| Component | Approx. size |
|---|---|
| Krea 2 Raw | ~24.5 GB |
| Qwen3-VL 4B text encoder | ~8.3 GB |
| Qwen Image VAE | ~1.1 GB |

**FP8 alone is not enough** — training stayed unstable, slow and prone to CUDA crashes. The working solution is FP8 **plus CPU block swapping**:

```
--fp8_base --fp8_scaled          # base-model quantisation
--blocks_to_swap 20              # move inactive transformer blocks to system RAM
--block_swap_h2d_only            # keep a CPU master copy; stream host→device only,
                                 #   skipping the needless device→host copy in LoRA training
--block_swap_ring_size 2         # two GPU ring buffers so the next block prefetches
                                 #   while the current one is processed (also musubi's default)
```

**System RAM is the hidden requirement.** 64 GB was tested; **32 GB can become tight** depending on dataset, OS overhead, caching and page-file settings. On a 12 GB card the constraint that bites is usually host memory, not VRAM.

Validated bucket geometries at this size: **512×512 and 1024×256**, batch size 1.

The original author notes their benchmark tests the block-swapping flags as a combination and does not isolate `--block_swap_h2d_only`, so no independent speedup is claimed for it — a level of care worth preserving when citing these numbers.

## 2b. Adult / NSFW work

**Krea 2 supports this well** — roughly **52% of published Krea 2 LoRAs are adult-flagged**, the highest share of any image model in this suite `[community — Civitai model API, sampled 2026-08-13]`. That is consistent with `nsfwVariant` already being one of this skill's most-cited craft sources for general Krea 2 technique.

A few Krea-specific points:

- **The doctrine is unchanged: train on Raw, run on Turbo.** Adult LoRAs follow the same path as any other, and several published ones ship exactly that way.
- **Several LoRA families span bases** — the same named adult LoRA lines appear built for Krea 2, Z-Image Turbo and Flux Klein. If you are already running one family on another base, check whether a Krea 2 build exists before training your own.
- **Check for a finetuned checkpoint before training anything.** By August 2026 the adult Krea 2 checkpoint ecosystem is mature and easily the busiest on Civitai — `LUSTIFY!` was the single most-downloaded model on the site over the month sampled, and `FinePorn v3 TURBO`, `Moody Krea 2 Mix (uncensored)` and several Stable Yogi realism finetunes are in wide use. A later sweep found the same names in circulation with no rival base contesting them: **Krea 2 is the dominant adult *image* model by a wide margin** `[community — r/unstable_diffusion, 2026-08-23]`. Reported workflows are unremarkable (Euler or ER SDE, 10 steps, guidance 1.0), which is the point: the checkpoint is doing the work.
- **The `krea2filterbypass` line is past circulating and into routine production use.** The form seen in the wild is **`<lora:krea2filterbypass3:2>`** — version 3, at **weight 2** — stacked on top of `MysticXXX_KREA2_V4` rather than used alone `[community — KlitoriaPierce]`. Read both halves of that. A LoRA can only re-expose behaviour the base weights already encode, never supply what was never trained, so the fact that a bypass line works at all is a fact about the base model: its reticence is tuning, not missing data. And the fact that it takes *double* the usual LoRA strength, on a checkpoint that is itself already a finetune, is a fact about how hard that tuning was applied — a normal-weight counter-LoRA does not clear it. Plan to stack rather than substitute; the same weight-2 figure is quoted in SKILL.md under the muted-expression tax, where the bypass line is also the SFW expressiveness fix.
- **You may not need to train at all.** For a *consistent* character in adult scenes the named production pattern is Krea 2 + the Identity Edit LoRA + an NSFW LoRA `[community — Clone-Protocol-66]` — Identity Edit carries the likeness, the NSFW LoRA carries the content, and neither has to do the other's job. Train a character LoRA when likeness must survive close-ups; see [`characters.md §3`](characters.md).
- Krea 2's soft/airbrushed default and its **two taxes** (see SKILL.md) apply here as everywhere — the Wan 2.1 VAE swap and texture anchoring matter more, not less, for anatomy work.

General doctrine — why base coverage rather than refusal is the limit, explicit captioning, anatomy failure modes — is in [`character-lora-training/references/nsfw-training.md`](../../character-lora-training/references/nsfw-training.md). Publishing constraints, which bind harder than capability, are in [`publishing-and-likeness.md`](../../character-lora-training/references/publishing-and-likeness.md).

## 2c. 16 GB, measured — and four corrections that came out of it

A second fully-measured run, this time on an **RTX 5080 16 GB / 32 GB system RAM**, musubi-tuner `[community — Economy_Cucumber_702, 2026-07]`. It is worth reading not for the numbers but for what the author got wrong and corrected in public.

**Measured:** 1152 steps in **67 minutes at 3.42 s/it**, peak **15,284 of 16,303 MiB VRAM**, 17.5 GB of 32 GB system RAM. Turbo inference afterwards: ~13 s per 768×1024 image at 8 steps.

Drop-in config, with the resolution corrected:

```toml
dit = "/path/to/krea2_raw_bf16.safetensors"
vae = "/path/to/qwen_image_vae.safetensors"
sdpa = true
mixed_precision = "bf16"
fp8_base = true            # must be set together —
fp8_scaled = true          # plain fp8 is rejected on purpose
blocks_to_swap = 16        # max 26
block_swap_h2d_only = true # avoids the copy doubling that eats host RAM
block_swap_ring_size = 1
gradient_checkpointing = true
max_data_loader_n_workers = 0
timestep_sampling = "krea2_shift"
weighting_scheme = "none"
network_module = "networks.lora_krea2"
network_dim = 32
network_alpha = 32
optimizer_type = "adamw8bit"
learning_rate = 1e-4
max_grad_norm = 1.0
max_train_epochs = 16
save_every_n_epochs = 1
seed = 42
```

Dataset toml: `resolution = [1024, 1024]`, `batch_size = 1`, `enable_bucket = true`, `caption_extension = ".txt"`.

**The four corrections, which are the actually useful part:**

1. **Train at 1024, not 768.** The author ran at 768 and was corrected: the technical report says pretraining spanned **256, 512 and 1024 px stages**, so 768 was never a trained resolution. Every number above was measured at 768 — **expect to raise `blocks_to_swap` and re-check VRAM at 1024.** This correction applies to §2a's 12 GB config too: the validated bucket geometries there are 512×512 and 1024×256, both on the lattice; do not split the difference.
2. **16 GB is enough**, contradicting the widely-linked musubi-tuner issue thread that says it is not — the author names the thread in their write-up and their measurement is the only counter-evidence published `[community — Economy_Cucumber_702; single report]`.
3. **The official `krea/Krea-2-*` repos are gated; `Comfy-Org/Krea-2` is not, and carries a byte-identical RAW checkpoint.** Useful only for trainers that take a file path rather than a repo id — but that covers musubi.
4. **A LoRA bleeding into prompts that omit the trigger is normal, and the fix is regularisation images, not caption surgery.** The author initially guessed at a captioning change; that was the wrong lever. This is consistent with §5's residual doctrine — captions control what stays *promptable*, not what leaks.

`timestep_sampling = "krea2_shift"` is the right default here for the same reason as in §2: it reproduces Krea's resolution-aware schedule per sample and survives aspect-ratio bucketing. At a fixed 1024 you can equally use `shift` with `discrete_flow_shift = 2.5`.

**On citing this:** one run, one machine, no ablations, and the writeup is AI-assisted with the measurements taken from the author's own machine. Treat the numbers as a plausibility check for your own hardware, and the four corrections as the durable content.

## 3. AI-Toolkit and the Ostris turbo-adapter path

Krea's README lists Ostris AI-Toolkit as a recommended trainer; the architecture key is `krea2`. There is still **no krea2 example YAML in the repo's `config/examples/`** — the directory's newest DiT entries remain the Qwen-Image and Wan 2.2 configs `[official — repo listing, re-verified 2026-08-26]`. So configure through the UI, adapt a nearby DiT config, or start from §3a's working file:

- **Raw path:** standard AI-Toolkit LoRA run against Raw. Hardware gotcha with a named fix: Raw training **OOMs early on a 24 GB RTX 3090 even in Low-VRAM mode** (fails around 3 GB allocated, 32 GB system RAM) until **Layer Offloading is set to ~10%** (5% also works and is slightly faster) `[community — Fast-Cash1522, r/StableDiffusion, marked SOLVED]`.
- **The best-replicated character recipe** runs on this path: **LoKr factor 4, Automagic3 optimizer, sigmoid scheduling, "Balanced", LR 1e-4 + weight decay, 1024-only, ~50-image datasets, 2–3k steps** — likeness rated above the author's Z-Image results across multiple characters `[community — Any_Tea_3499]`. Note it's LoKr, not classic LoRA — factor 4 is the capacity knob standing in for rank.
- **Turbo-adapter path:** load `ostris/krea2_turbo_training_adapter` as the training adapter over Turbo; train your LoRA; the adapter is dropped at inference. Made for short runs — styles, concepts, characters. Lighter than Raw on the same hardware (the 3090 user above trained Turbo+adapter "without any issues" on the settings that OOM'd Raw).
- Ostris also ships a Krea 2 **edit-training** stack (paired-data edit LoRAs + a 3-reference-image ComfyUI node) — that's `characters.md §3`, not classic LoRA training.

## 3a. A working AI-Toolkit Raw config, and where the trainer gets its encoder

Two sources arrived at the same plain-LoRA recipe independently, which makes it a safer first attempt than §3's LoKr run: a **community-calibrated workflow** published as a repo `[community — chengyansen-ai/krea2-lora-training v0.4.0, read 2026-08-26]`, and a **finished private character run** — 25 photographs, 2250 steps on a 32 GB RTX PRO 4500 Blackwell, likeness landed and shipped `[community — production run, 2026-08-24]`.

| Setting | Value | Why |
|---|---|---|
| `arch` | `krea2` | Built in. `name_or_path` takes a local single-file `.safetensors` for the DiT |
| Network | **LoRA, `linear` 32 / `linear_alpha` 32** | The all-Linear rank and alpha both sources use; matches the musubi default in §2 |
| Optimizer / LR | `adamw8bit`, **1e-4** | Drop to 5e-5 if you want to run past about 3k steps without overfitting `[community — chengyansen-ai]` |
| `noise_scheduler` | `flowmatch` | — |
| `timestep_type` | **`linear`** | Called out specifically as *not* Flux's sigmoid — this is what pairs with flowmatch here `[community — chengyansen-ai]`. §3's best-replicated LoKr recipe uses sigmoid instead, so pick per recipe rather than assuming one is right `[contested]` |
| `train_text_encoder` | **`false`** | Qwen3-VL stays frozen. Saves VRAM and keeps prompt understanding intact |
| `quantize` / `qtype` | `true` / `qfloat8`, encoder too | fp8 on both sides is what makes 32 GB comfortable |
| `resolution` | **`[1024]`** | Per §2c's correction. The community workflow buckets 512+768+1024 to build composition first and detail later, but 768 was never a trained stage — treat that as its author's practice, not a settled answer `[contested]` |
| `caption_dropout_rate` | `0.05` | Both sources |
| Steps | **~90 per image**, `save_every` 250 | 2250 for 25 images; 2500 for a first run on a bigger set `[community — chengyansen-ai]` |

**`cache_text_embeddings: true` is only safe if the trigger word is written into the captions themselves.** It encodes each caption once and reuses that, so anything the trainer would normally swap in later — such as a `trigger_word` field it injects per step — gets frozen at the wrong value. Type the trigger into the `.txt` sidecars yourself, leave `trigger_word` unset, and the cache is free speed. It also takes the text encoder out of the step loop, which is what frees up the VRAM the next paragraph relies on.

**You do not need layer offloading at 32 GB, and §3's out-of-memory report does not scale up to bigger cards.** With fp8 on both sides, text embeddings cached and gradient checkpointing on, the measured run used **15.8 of 32 GB with `low_vram` off**, at batch 1 and 1024 px.

Turning offloading *off* also gained nothing, which is worth knowing. The run sat at **about 5.5 s/step either way** — roughly 3.4 hours for 2250 steps on a 12B model — because the card was the limit, not memory traffic. So treat offloading as a way to fit a job on a smaller card, not as something that slows you down. On a card with room it is neither needed nor harmful, and it is not where a slow run's time is going.

**The trainer wants HuggingFace-format folders for the encoder and VAE, not the ComfyUI single files.** This catches out anyone who has just downloaded the ComfyUI model set. Those single files — `qwen3vl_4b_*.safetensors` and `qwen_image_vae.safetensors` — are for generating images. AI-Toolkit will still go and fetch its own diffusers-format `Qwen3-VL-4B-Instruct` (about 9 GB) and Qwen-Image VAE on top of them. Budget disk for both, and if you already have the folders, point at them instead of downloading again:

```yaml
model:
  arch: "krea2"
  name_or_path: "/workspace/models/diffusion_models/krea2_raw_bf16.safetensors"
  model_kwargs:
    text_encoder_path: "/path/to/Qwen3-VL-4B-Instruct"
    vae_path: "/path/to/Qwen-Image"
```

`[community — chengyansen-ai/krea2-lora-training]`. On rented hardware this is also how you rescue a nearly-full network volume. The encoder can always be downloaded again, so send it and the HF cache to the pod's throwaway container disk and keep the volume for checkpoints — see [`comfyui-on-runpod`](../../comfyui-on-runpod/references/volume-and-models.md) §6.

**Previews on Raw cost enough to take over the run, and they make the likeness look worse than it is.** They render on the undistilled model at guidance 4, which is slow — about 90 seconds each, so a 6-prompt set every 250 steps burns more time than the training it is watching. They are also washed out in exactly the fine skin and bone detail a face is recognised by. In the measured run the face was still generic at step 750 of 2250, unmistakable by 1500, and sharper again on Turbo than any Raw preview had been. Reading those step-750 previews as a failure would have thrown away a perfectly good run.

So keep `save_every` at 250 to build the checkpoint series, but preview only every 750, skip the step-0 preview, and cut the preview step count. The real answer comes from a Turbo grid afterwards anyway (§8). The 8-step Turbo settings the community workflow uses to accept a run: **CFG 0, mu 1.15**.

**This is the one place musubi beats AI-Toolkit on this model.** musubi's `--turbo_dit` (§2) previews the in-training LoRA on Turbo weights directly, which removes the problem instead of asking you to allow for it. AI-Toolkit has nothing equivalent, so here you fix it by habit: preview rarely, judge on Turbo.

Two failures specific to this path can cost you a whole run, both from the community workflow's pitfall list `[community — chengyansen-ai; unverified here]`. **The character bleeds into prompts that never mention the trigger** — fix that by picking an earlier checkpoint, not by retraining. And **`res_2s`-family samplers drift** when you generate. That workflow also recommends DOP with the class `"person"`, which is the same technique `characters.md` records as working on Krea 2 and failing on Z-Image.

## 4. fal hosted trainer

`fal-ai/krea-2-trainer` (train) + `fal-ai/krea-2/turbo/lora` (run). Zero-setup path; hyperparameters are managed. Weights come back as standard safetensors LoRAs usable locally.

## 5. Captioning doctrine

Encoder-class rule (LLM/VLM encoder): **prose captions, caption-the-residual** — describe what varies and what should *not* be absorbed into the trigger; leave the identity/style itself uncaptioned so it binds to the trigger phrase. The one named Krea-2-specific data point agrees: JahJedi captions "describe only what is visible" — plain factual prose per image `[community — JahJedi]`. Character vs style inverts what you caption (character: caption clothing/pose/background so identity binds; style: caption subjects so the *look* binds — [`character-lora-training`](../../character-lora-training/) documents the shared craft in depth, model-independently). **Captionless training** is contested on every DiT family and has no Krea-2-specific evidence either way yet — flag any strong claim you meet as unverified.

A Krea-2-specific caption lesson from multi-character training: a LoRA whose training captions were literal scene descriptions holds up when *prompted in the same register*, and falls apart (character bleed, identity drift) under free-form creative prompts `[community — krigeta1's documented failure case]`. The residual rule cuts both ways — what you caption is what stays *promptable*, so caption in the register you intend to prompt in, and vary caption phrasing across the dataset if you want prompt flexibility.

## 6. Character LoRAs: two named recipes

The lighter, better-replicated recipe is Any_Tea_3499's AI-Toolkit LoKr run (§3: ~50 images, 2–3k steps, LoKr 4 / Automagic3 / sigmoid / LR 1e-4, likeness > Z-Image). The heavyweight musubi/Raw recipe with full settings and outcome `[community — JahJedi, HF krea2-character-lora-recipe]`:

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

**If you intend to load several character LoRAs at once, consider Differential Output Preservation** on a LoKr run — class `"woman"`, 1500 steps rather than 750. Up to **four** characters then reportedly coexist with minimal bleed; five falls apart. This comes from a single author's runs and has not been replicated, so budget a test run before you commit a project to it `[community — MASilverHammer; single report]`. Full account, including the same author's report that the technique fails on Z-Image Base, is in [`characters.md §2`](characters.md#2-the-character-lora-pipeline). If it holds for you it is the strongest reason to choose Krea 2 over Z-Image for a multi-character job.

## 7. Style LoRAs

- Krea's own style-LoRA line (nine on Comfy-Org + the `krea/krea-2-loras` HF collection) demonstrates the format: rank ~modest, DiT-only, natural-phrase trigger, strength 0.8–1.0. No official training write-up accompanies them. The community layer is already large — **1,500+ style LoRAs from a single named trainer** (ilker's `fal-Krea-2-Style-LoRAs`, highlighted in Krea's own community roundup) plus a steady Civitai stream.
- **Named Raw-path style runs with published settings:** urabewe's Garbage Pail Kids / Ren & Stimpy LoRAs — musubi defaults (§2), 30-image datasets, ~1,200–1,250 steps, ~2 h on a 12 GB 3060, used at strength **1.0 with no trigger word** (nudge with "cartoon"/"animation" when needed) `[community — urabewe; full command and dataset-builder tool published]`. Philosopher_Jazzlike's anime-style LoRA (config attached on Civitai; run at 0.85 stacked with a second LoRA at 1.0) reports Krea 2 Turbo "absolutely brilliant at adopting styles while still executing the prompt", in a second published write-up. The style community's consensus-forming rate is fast; strength-1.0-no-trigger is emerging as a common style pattern, in contrast to the official LoRAs' appended trigger phrases — read each author's card.
- Style dataset craft is the suite-shared kind (diverse subjects so the style doesn't bind to content; composition-memorisation and color-cast lock-in as overfit signals; out-of-set subject as the acceptance test) — see [`sdxl`](../../sdxl/) / [`z-image`](../../z-image/) lora-training references for the full treatment.
- Style rank on Krea 2: rank/alpha 32 (musubi default) is what the named style runs above used; the rank-64 Turbo LoRA brackets the high end. LoKr-factor-4 is the AI-Toolkit-side equivalent anchor (§3).

## 8. Evaluation

- **Validate on Turbo, not Raw** — you ship on Turbo; musubi's `--turbo_dit` sampling exists precisely for this (§2). A LoRA that looks great on Raw at cfg 3.5 and falls apart at 8-step guidance-off has failed its acceptance test.
- XY-grid epoch × strength, as on every family: identity/style vs stacking headroom. Krea-2-specific axis worth adding: **with and without the Wan-VAE swap**, since much of the perceived quality difference lives in the decode (`setup-and-workflows.md §5`).
- Overfit signals are the standard ones (same-face, composition memorisation, style bleed into untriggered prompts); the Krea-2-specific confound is the **muted-expression tax** — don't diagnose "expression lock-in" in your LoRA before checking the base model produces the expression at all (`SKILL.md`, *two taxes*).
