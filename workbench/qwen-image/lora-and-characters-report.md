# Qwen-Image — LoRA training and characters (research report)

Compiled 2026-09-09. Slice: LoRA training and character work for Qwen-Image (T2I), Qwen-Image-2512, and Qwen-Image-Edit (2508 / 2509 / 2511). Bars: `[official — artefact]`, `[community — author, venue]`. Nothing here is `[live-use]` — this lab has not trained a Qwen LoRA. Dates are the artefact's, or the date read where undated.

Contents: 1 Trainers · 2 Lightning · 3 Dataset practice · 4 Edit LoRAs · 5 Characters without training · 6 Evaluation and collapse · 7 NSFW · 8 Hyperparameter table · 9 Transfers / does not transfer from Krea 2 · 10 Contested · 11 Thin · 12 Open questions

---

## 1. Trainers

### 1.1 Support matrix, verified 2026-09-09

| Trainer | Qwen-Image | 2512 | Edit 2508 | 2509 | 2511 | Layered |
|---|---|---|---|---|---|---|
| **ai-toolkit** (ostris) | yes | yes | yes | yes | yes | — |
| **musubi-tuner** (kohya) | yes | not named | yes | yes | yes | **yes** |
| **diffusion-pipe** | yes | not named | yes | not named | not named | — |
| **SimpleTuner** | yes | not named | "Qwen Edit" listed under reference-input training | | | — |
| **OneTrainer** | yes ("Qwen Image" in supported models) | | | | | |
| **DiffSynth-Studio** | yes | yes | yes | yes | yes | yes |
| **kohya sd-scripts** | **not a Qwen trainer** — its only Qwen artefact is a 2D-only Qwen-Image **VAE** (`--qwen_image_vae_2d`, PR #2382) | | | | | |

`[official — each repo's README / docs, read 2026-09-09]`. Read the last row carefully: people say "kohya" and mean **musubi-tuner**. Any guide telling you to run sd-scripts on Qwen-Image is confused.

### 1.2 ai-toolkit

Three shipped configs: `train_lora_qwen_image_24gb.yaml`, `train_lora_qwen_image_edit_32gb.yaml`, `train_lora_qwen_image_edit_2509_32gb.yaml`. **No 2511 or 2512 example exists** despite both being listed as supported — adapt the 2509 file or use the UI `[official — repo listing, 2026-09-09]`.

T2I config, condensed `[official]`:

```yaml
network:  { type: lora, linear: 16, linear_alpha: 16 }
datasets: [{ caption_dropout_rate: 0.05, cache_latents_to_disk: true, resolution: [512, 768, 1024] }]
train:    { batch_size: 1, cache_text_embeddings: true, steps: 2000, gradient_checkpointing: true,
            train_text_encoder: false, noise_scheduler: flowmatch, optimizer: adamw8bit, lr: 1e-4, dtype: bf16 }
model:    { name_or_path: "Qwen/Qwen-Image", arch: qwen_image, low_vram: true,
            quantize: true,    qtype: "uint3|ostris/accuracy_recovery_adapters/qwen_image_torchao_uint3.safetensors",
            quantize_te: true, qtype_te: qfloat8 }
sample:   { width: 1024, height: 1024, guidance_scale: 3, sample_steps: 25, sample_every: 250 }
```

Qwen-specific points:

- **`qtype: uint3` plus an accuracy-recovery adapter.** Qwen-Image is a **20B** DiT, so the shipped 24 GB path quantises to **3-bit** and loads a matching recovery adapter. Each variant names its **own** adapter file (`qwen_image_edit_torchao_uint3`, `qwen_image_edit_2509_torchao_uint3`). Using the wrong one is a silently degraded run, not an error.
- **Rank 16, alpha = rank** in all three configs.
- **`resolution: [512, 768, 1024]`** — multi-bucket by default (§3.1).
- **`train_text_encoder: false`** — Qwen2.5-VL is frozen. Same encoder-class doctrine as Krea 2 and Z-Image.

The Edit configs differ in four ways: `steps: 3000`, `timestep_type: "weighted"`, a dataset `control_path`, and `ctrl_img` / `ctrl_img_1..n` in samples. `arch` is `qwen_image_edit` (2508) or **`qwen_image_edit_plus`** (2509); the 2509 `control_path` is a **list of up to three folders**, and the `QwenImageEditPlusModel` class does **not** resize control images by default.

### 1.3 musubi-tuner — the fullest documented path

```bash
accelerate launch --mixed_precision bf16 src/musubi_tuner/qwen_image_train_network.py \
  --dit … --vae … --text_encoder … --model_version original --dataset_config …toml --sdpa \
  --timestep_sampling shift --weighting_scheme none --discrete_flow_shift 2.2 \
  --optimizer_type adamw8bit --learning_rate 5e-5 --gradient_checkpointing \
  --network_module networks.lora_qwen_image --network_dim 16 \
  --max_train_epochs 16 --save_every_n_epochs 1 --seed 42 --output_dir out --output_name my-lora
```

- **`--model_version`**: `original` / `edit` / `edit-2509` / `edit-2511` / `layered` (`--edit`, `--edit_plus` are legacy aliases).
- **`--discrete_flow_shift 2.2`, chosen deliberately:** *"set quite low for Qwen-Image during inference … so a lower value than other models may be preferable."* Compare Krea 2's 2.5.
- **`--timestep_sampling qwen_shift`** is Qwen's `krea2_shift`: the dynamic, resolution-dependent inference shift per sample, *"typically around 2.2 for 1328x1328 images."* Use it for bucketed sets; `shift` + fixed 2.2 at a fixed resolution.
- **LR 5e-5** — half the ai-toolkit / DiffSynth figure, never A/B'd (§10).
- **Quantisation:** `--fp8_base` + `--fp8_scaled` (DiT), **`--fp8_vl`** (text encoder, recommended below 16 GB). `flash3` unsupported; `--split_attn` if not on `--sdpa`.
- **VRAM ladder** (1024², batch 1, bf16 + gradient checkpointing): **42 GB** → fp8_base+fp8_scaled **30 GB** → `+ blocks_to_swap 16` **24 GB** → `+ blocks_to_swap 45` **12 GB**. 64 GB system RAM recommended. **Edit needs more**, for the control images.
- **Weight gotchas:** Comfy-Org repacks work, but `qwen_image` **fp8_scaled cannot be used**, Edit DiT **fp8_e4m3fn cannot be used**, Layered rejects fp8mixed. Download bf16.
- **Two pre-cache scripts, both required.** For Edit, controls are cached as latents *and* the text cache is built **with the control images in the prompt** — so `--model_version` must be right at *cache* time.
- **Full finetuning** (`qwen_image_train.py`): adafactor + `--fused_backward_pass` + `--full_bf16` + `--max_grad_norm 0`, LR **1e-6 – 1e-5**. Edit finetuning marked **unverified**.
- Disclaimer, verbatim: *"The appropriate settings for each parameter are unknown. Feedback is welcome."*

`[official — musubi docs/qwen_image.md, read 2026-09-09]`

### 1.4 diffusion-pipe, SimpleTuner, DiffSynth

**diffusion-pipe** `[official — docs/supported_models.md]`: `type = 'qwen_image'`, `transformer_dtype = 'float8'`, **`timestep_sample_method = 'logit_normal'`** — a third schedule family. *"Use bf16 files even if you are casting the transformer to float8; fp8_scaled weights won't work at all."* Example dataset resolution **640**; 24 GB needs block swap plus the expandable-segments allocator. Edit is *"the same as Flux-Kontext"*, references must roughly match the target aspect or they over-crop, and *"I don't know if you can train it on 24GB VRAM."* **Both Qwen-Image and Edit LoRAs are saved in ComfyUI format.**

**SimpleTuner** `[official — QWEN_IMAGE.md]`: `lora_rank` **8 or lower** at 24 GB; `lora_type` `standard` or **`lycoris`** (LoKr); LR **1e-4**; `optimi-lion` or `adamw-bf16`; start **512/768** → 1024; **`flow_schedule_shift 1.73`**; base precision **int2-quanto or nf4-bnb** required at 24 GB; batch pinned to 1 with grad-accum 2–8. The blunt Qwen fact: **the Qwen2.5-VL encoder alone is ~16 GB before quantisation** — on a 24 GB card the encoder, not the DiT, is what breaks naive setups.

**DiffSynth-Studio** ships a script per variant. All LoRA scripts share `--max_pixels 1048576` (an *area* cap = 1024², any aspect), `--learning_rate 1e-4`, `--num_epochs 5`, **`--lora_rank 32`**, `--lora_base_model dit`, `--remove_prefix_in_ckpt "pipe.dit."`, and this target list `[official]`:

`to_q,to_k,to_v,add_q_proj,add_k_proj,add_v_proj,to_out.0,to_add_out,img_mlp.net.2,img_mod.1,txt_mlp.net.2,txt_mod.1`

That is the clearest published statement of what a Qwen LoRA touches: a **dual-stream MMDiT** — `to_*` / `img_*` are the image stream, `add_*_proj` / `txt_*` the text stream, plus two output projections. Edit training adds `--data_file_keys "image,edit_image" --extra_inputs "edit_image"`. **`--zero_cond_t` is required for Edit-2511 and only 2511** — the script's own comment: *"This is a special parameter introduced by Qwen-Image-Edit-2511. Please enable it for this model."* It has no counterpart in ai-toolkit's or musubi's documented surface.

### 1.5 LoRA formats and ComfyUI

- **diffusion-pipe** — ComfyUI format by design, stated twice `[official]`.
- **musubi** — sd-scripts key dialect via `networks.lora_qwen_image`; loads in ComfyUI. What it does **not** emit is **diffusers** keys: issue [#442](https://github.com/kohya-ss/musubi-tuner/issues/442), *"Request: Add Diffusers-compatible export for Qwen-Image LoRA"* (alfredplpl, opened 2025-08-13), still open when read. The mismatch to expect is musubi → `load_lora_weights()`, not musubi → ComfyUI.
- **ai-toolkit** — diffusers-style PEFT keys. No maintainer statement about ComfyUI was found in the repo, but ai-toolkit LoRAs are what most named authors below ship and load in ComfyUI. Verify rather than assert.
- **DiffSynth** — its own keys, with the `pipe.dit.` prefix stripped so the file is usable outside DiffSynth.

**Most "key mismatch" reports are actually *variant* mismatches, and Qwen is unusually permissive:** *"Many Qwen Image loras work with Qwen Edit too, but you'll need to test them individually"* `[community — nsfwVariant, r/StableDiffusion, 2026-06]`; *"You can use 2512 LoRAs on 2511 and vice versa, but it's not perfect. A dedicated training for each version will always give you better results"* `[community — FarTable6206, r/StableDiffusion, 2026-01]`.

---

## 2. Lightning interplay

Qwen's speed LoRAs are **Qwen-Image-Lightning** (ModelTC / lightx2v) — not a Qwen-team artefact and not a Krea-Turbo analogue. **Qwen-Image is undistilled.** There is one base plus an optional inference-time speed LoRA, so the Krea question "which checkpoint do I train on?" has no referent here, and **no de-distillation training adapter exists for Qwen.**

**Releases** `[official — README, read 2026-09-09]`: Lightning 8-step V1.0 (2025-08-08), 4-step V1.0 (08-11), 8-step V1.1 (08-12); Edit-Lightning 8/4-step V1.0 (08-23/24); Lightning 4/8-step **V2.0** (2025-09-10/12); Edit-2509-Lightning 4- and 8-step (2025-10-09); Edit-2511-Lightning 4-step plus a fused fp8 build (2025-12-22); Qwen-Image-2512-Lightning 4-step (2026-01-01).

**V2.0 exists because V1.x over-saturated** — V2.0 *"produces images with reduced over-saturation, resulting in improved skin texture and more natural-looking visuals."* Debugging a colour cast? Check the Lightning version before blaming the LoRA. The vendor is candid about limits: 12–25× faster with no significant loss *in most cases*, but the base wins on **dense or small text**, and on **hair-like detail** the distilled models come out *"either noticeably blurred or excessively sharpened"* — exactly where identity is judged.

### 2.1 The fp8 grid trap — the most concrete Lightning fact in the family

Stacking a Lightning LoRA on **`qwen_image_fp8_e4m3fn.safetensors`** (Comfy-Org) produces a visible **grid pattern**, because that file was made by directly downcasting bf16 with no calibrated scaling. The maintainers' correctness table: bf16 base + bf16-trained LoRA ✓ · **fp8_e4m3fn base + bf16-trained LoRA ✗ (grid)** · fp8 base + LoRA distilled on that fp8 base ✓ · **`qwen_image_fp8_e4m3fn_scaled` base + bf16-trained LoRA ✓** `[official — README §"Using Lightning LoRAs with FP8 Models"; issue #32, resolved 2025-10-14]`.

This is a base-quantisation × LoRA interaction, so **it applies to your character LoRA too**. A faint grid means check the base file first.

### 2.2 Train on base, infer with Lightning stacked

That is what named authors do, and it works:

- **Nyao** (Urasawa manga style): ai-toolkit, 2,750 steps, LR **2e-4**, 44 images, **no trigger word**; *"All the image attached have been generated in 4 steps (with the lightning lora by lightx2v)"* `[community, 2025-08]`.
- **Substantial_Angle680** (folk-horror style): OneTrainer, 50 frames, 120 epochs, no trigger; *"works with lightning loras aw, working weight is 0.8–1.2"* `[community, 2025-11]`.
- **acekiube** generates the *training set itself* on Edit-2509 fp8 + the 4-step Lightning LoRA — 20 images in 130 s on a 5090 `[community, 2025-10]`.
- **Top_Buffalo1668** ran character LoRAs at **12 steps, CFG 1** rather than 4 `[community, 2026-01]`.

### 2.3 The failure mode, and the dissent

*"All the lightning loras / distils for Qwedit (that I've tested) are terrible and make your outputs look bad… it makes people's skin look like plastic."* The author's alternative is fewer steps on the base — *"just set it to 10 steps instead of 20"* while iterating — and they concede *"it's ok if you want to use the lightning loras, just expect some degradation"* `[community — nsfwVariant, 2026-06]`. On the other side, a second author sees Qwen skin *"still a bit plastic"* at 12 steps with **no Lightning loaded**, even with `res_2s` + `bong_tangent` `[community — Top_Buffalo1668]`. So plastic skin is partly a Qwen property that Lightning worsens. `[contested]`

**Practice:** train on the undistilled base; grid the checkpoints on the base at 20 steps *and* on your real deploy configuration. Never judge a character LoRA only through a Lightning graph.

**One open hole:** how to *train* your own Lightning LoRA for Edit-Plus was asked directly and got **zero replies** `[community — Mobile_Peace5639, r/StableDiffusion, 2025-11]`. The distillation recipes live in the lightx2v repo, not in any consumer trainer.

---

## 3. Dataset practice specific to Qwen

### 3.1 Resolution

| Source | Value | Framing |
|---|---|---|
| ai-toolkit | `[512, 768, 1024]` multi-bucket | shipped default, all three configs `[official]` |
| DiffSynth | `--max_pixels 1048576` (area cap = 1024²) | shipped default, every variant `[official]` |
| musubi | 1024² | the VRAM benchmark size `[official]` |
| diffusion-pipe | **640** | "a resolution the model was trained on"; also the 24 GB lever `[official]` |
| SimpleTuner | 512/768 → 1024 | explicitly VRAM-driven `[official]` |
| Icy_Upstairs3187 | **1440 px @ 4:5**, 1440 bucket added | matched the subject's Instagram size `[community, 2025-08]` |
| FarTable6206 | *"assuming your dataset is 1024px or higher"* | the rank-32 verdict is conditioned on it `[community, 2026-01]` |

**The Qwen-specific fact underneath:** musubi's `qwen_shift` quotes *"typically around 2.2 for 1328×1328 images"*, and Qwen's supported aspect set is built around **~1.5 Mpx (the 1328 class)**, not 1 Mpx. Qwen's *inference* band therefore sits **above** 1024, unlike Krea 2 Raw which is 1K-native. That is why 1440 is defensible here and would be an error on Krea 2. **Nobody has A/B'd 1024 against a 1328-class bucket.** Every shipped default is at or below 1024, and the low end is always framed as VRAM, never quality.

**Hi-res sources:** no Qwen report reproduces Krea 2's "render above the band and the texture survives downscaling" finding. Qwen authors say the opposite-facing thing — *"always use the highest resolution and sharpest images you can… Blurry, compressed, or low-resolution images will poison the LoRA"*, with extreme close-ups justified as information density (a face inside a 1 Mpx full-body shot is a ~20×15 px eye region) `[community — AwakenedEyes, r/StableDiffusion LoRA primer v2, 2026-05]`. These are not in conflict: Krea's rule governs *generated* sources; this governs *photographic* ones. Keep them apart in the skill.

### 3.2 Captions

Four named positions, all from authors who shipped something:

- **Verbose.** *"Tried short captions, medium captions, novel-length captions… longer/descriptive ones worked best."* 79 images, GPT-5 wrote the captions `[Icy_Upstairs3187, "Learnings from Qwen Lora Likeness Training", 2025-08]`.
- **30–50 words.** *"I tried everything from only tag & 10-word tags to 100-word descriptions. Medium-length works best."* With a named trap: *"AI-generated captions can be too detailed. Qwen VL (the text encoder) can get confused by too much noise"* `[FarTable6206, 2026-01]`.
- **One word** (the character's name). *"Over the dozens of loras I've trained on FLUX, QWEN and WAN… verbose captioning doesn't seem to be necessary to get good likeness"* `[acekiube, 2025-10]`.
- **None** — two shipped *style* LoRAs `[Nyao; Substantial_Angle680]`. A different job; not direct counter-evidence.

**Everyone training a character agrees on the residual rule**, whatever the length. FarTable6206's Qwen-specific version:

> **Never write `face`, `head`, `eyes`, `mouth`, `lips`, `nose`** — *"If you label the 'mouth,' the text encoder tries to learn what a mouth is instead of just learning 'this person's mouth.'"*
> **Avoid `woman` / `girl` / `man` / `person`** — *"prevents the model from pulling in generic 'woman' data from the base model."*
> Background as one word ("cafe"); clothing as style plus colour; expression only when obvious; composition only when unusual — *"If you label 'front view' on every single photo, the LoRA will get stuck in that view."*

The gender-word rule **contradicts this suite's shipped practice** (`"a woman named zciara"`). Flag it, do not adopt it.

### 3.3 Triggers — a plain name, not a rare token

> *"Unlike Flux, Qwen doesn't really vibe with the single trigger word → description thing… it works better as a natural human name inside a normal sentence. Good: "A beautiful Chinese woman named Kayan." Bad: "TOK01 woman""* `[Icy_Upstairs3187, 2025-08]`

Hearmeman98's shipped character prompts use `Sydney01` in ordinary prose `[community, 2025-10]`; acekiube writes the bare name as the whole caption; style authors use none.

**Does the Krea 2 "rare tokens surface as watermarks" report apply? No Qwen equivalent has been published.** The nearest sibling report is *Krea 2* again — trigger `avtr` bled Avatar features (sharp ears, stripes) until it was changed to `zkrs`, which is *semantic leakage*, not watermarking `[community — repolevedd, 2026-07; Krea 2, not Qwen]`. So the **conclusion** transfers and is independently confirmed on Qwen; the **failure mode** is Krea evidence only.

### 3.4 Size, composition, steps

| Author | Images | Composition | Steps | Trainer |
|---|---|---|---|---|
| FarTable6206 | **40–60** (tested 30–100) | **60 / 30 / 10** close / half / full; 70% front | 80–100 repeats/img → 3,000–6,000 | ai-toolkit, H200 |
| Icy_Upstairs3187 | **79** | **33 / 33 / 33** | **6,000** | ai-toolkit / fal / Replicate |
| AI_Characters | **18** | — | — (custom polynomial scheduler with a minimum LR; ships a patched `scheduler.py`) | ai-toolkit, H100 |
| acekiube | **20**, all Edit-generated | face angles only | — | musubi / ai-toolkit |
| Nyao (style) | 44 | — | 2,750 | ai-toolkit |
| Substantial_Angle680 (style) | 50 | — | 120 epochs | OneTrainer |
| ProGamerGov (360 concept) | ~100k + 64k regularisation | — | 2.3M over ~4 months | nf4 → int8 |

**The composition ratio is the sharpest conflict with this suite.** *"Many people tell you to include lots of full-body shots. Don't. If you have too many full-body shots (20–30%), your LoRA will produce blurry or distorted faces when you try to generate full-body images"* `[FarTable6206]`. 60/30/10 is close to the inverse of `character-lora-training`'s "one-third identity, two-thirds context" — and of Icy_Upstairs3187's own 33/33/33 on the same model. It does agree with the sibling's *mechanism* (identity is learned per face-scale) and with AwakenedEyes' *"at least 50% headshots."* No A/B exists.

### 3.5 Rank and LR

- **Rank 32 is the character consensus.** *"Why not 16? It skips fine details — facial micro-expressions, specific makeup, and skin textures. Why not 64? It over-generalizes. It starts to lose the specific 'vibe' of the person"* `[FarTable6206]`. DiffSynth ships 32 for every variant `[official]`.
- **But every shipped default is 16** (ai-toolkit ×3, musubi `--network_dim 16`), or **8 or lower** on SimpleTuner at 24 GB `[official]`. Rank **128** is in use for concepts (ProGamerGov's Qwen 360).
- **LR is 1e-4 everywhere except musubi (5e-5) and the character specialists (2e-4).** *"0.0002 is actually more efficient for real people… I tried 0.00005 with 8,000 steps, but the quality wasn't even close to 0.0002 with 4,000 steps. Even 0.0001 didn't perform as well. But this high LR works best when paired with the sigmoid timestep"* `[FarTable6206]`. Nyao's style LoRA also used 2e-4.
- **`timestep_type: sigmoid` plus a `constant` scheduler for characters on ai-toolkit** — *"sigmoid is miles ahead of weighted… for character LoRAs, sigmoid is the only way to go"*, attributed to the toolkit author's own video. Ostris's shipped Edit configs use `weighted`, so this is a character-specific override of the shipped default.
- **Batch 1, grad-accum 1** — *"Larger batches tend to generalize the character too much… Avoid identity dilution"* `[FarTable6206]`. This directly contradicts a well-argued Krea 2 report that grad-accum 2 is *"severely underrated"* `[repolevedd, Krea 2]`. Different models, opposite advice. `[contested]`
- **LoKr** is available (SimpleTuner `lycoris`, ai-toolkit) but **no named Qwen *character* author uses it.** The one prominent Qwen LoKr is `SNOFS`, an adult *concept* LoRA. The LoKr enthusiasm in this suite is Krea 2 and Z-Image evidence.

---

## 4. Edit LoRA training

### 4.1 Paired-data layout

**musubi** — parallel directories matched by filename `[official — dataset_config.md]`:

```toml
[[datasets]]
image_directory    = "/targets"    # the AFTER images
control_directory  = "/controls"   # the BEFORE images
resolution         = [1024, 1024]
control_resolution = [1024, 1024]  # "We strongly recommend specifying this value."
no_resize_control  = false
```

Filenames match, extensions need not (`targets/a.jpg` ↔ `controls/a.png`). Multiple controls take numeric suffixes (`a_0.png`, `a_1.png`, or `a_0000.png`); JSONL uses `control_path_0/1`. **Only one control is allowed on plain Edit (2508)**; multi-control needs `edit-2509` or `edit-2511`. `control_resolution` matters because musubi otherwise resizes controls to the *target's* resolution and aspect, whereas the official code resizes them to ~1 Mpx independently — a silent quality loss, not an error. Official multi-image support is three; musubi allows more and has tested to three.

**ai-toolkit** — `control_path`: one folder for `qwen_image_edit`, a **list of up to three** for `qwen_image_edit_plus`; samples take `ctrl_img` or `ctrl_img_1..3` `[official]`.
**DiffSynth** — one metadata file with two columns (`--data_file_keys "image,edit_image"`), plus `--zero_cond_t` for 2511 `[official]`.
**diffusion-pipe** — "same as Flux-Kontext"; **references must roughly match the target aspect or they over-crop** `[official]`.

**One community claim with no official confirmation:** Edit-2511 in ai-toolkit **requires a 1024×1024 solid black image as the control map**, and uses **30–50% more VRAM than 2512** because it processes that map even when blank `[FarTable6206; single report]`. Verify before a paid run.

### 4.2 What people train Edit LoRAs for

| LoRA | Job | Numbers | Source |
|---|---|---|---|
| **BFS — Best Face Swap** | face swap ("Focus Faces": keeps head shape and hair) and head swap ("Focus Head") | **5,500+ steps**; the 2511 build ships both a pure train and a **2509-v4 × 2511 merge**, which the author rates better for expression range; ~71k downloads | `[NRDX/Alissonerdx, Civitai]` |
| **Multiple-Angles (2511)** | 96 camera poses, arbitrary re-angling | **3,000+ pairs generated from Gaussian Splatting** | `[Affectionate-Map1163 / fal, 2026-01]` |
| **Next Scene (2509)** | next shot, same character, lighting, environment | prefix `"Next scene:"` | `[Affectionate-Map1163, 2025-10]` |
| **InScene / InScene Annotate** | consistent shots in a scene; navigate by drawing green rectangles | built to compose with the author's InStyle / InSubject | `[PetersOdyssey, 2025-11]` |
| **AnyPose (2511)** | ControlNet-free posing from a reference | — | `[SillyLilithh, 2026-01]` |
| **Pose Transfer V2** | pose from the left image onto the person in the right | the prompt is the whole instruction sentence | `[kingroka, 2025-09]` |
| **Upscale LoRA (2509)** | restoration | Unsplash-Lite + UltraHR-100K with synthetic degradations (16× downscale, 50% noise, JPEG q5, 64 px motion blur, 3-bit banding); needs `ModelSamplingAuraFlow` **shift < 0.3**, LCM sampler | `[vafipas663, 2025-10]` |
| **PanelPainter (2509)** | manga colourisation | **~7k steps on ~7.5k pairs**; deploy weight **0.45–0.6** | `[Proper-Employment263, 2025-11]` |
| **ICEdit LoRA (2511)** | infer A→B, apply it to C | 2025-12-24 | `[official — DiffSynth]` |
| **Qwen-Image-i2L** | **image → LoRA** | 2025-12-09; authors flag weak generalisation and detail preservation | `[official — DiffSynth]` |

**The pattern to name in the skill:** on Qwen an Edit LoRA is usually a **capability** LoRA — a new verb (swap, repose, relight, colourise, upscale) built from *synthetically paired* data — not a character LoRA. The only widely-used identity-adjacent one is a face/head swap. The two recipes with real numbers (BFS 5,500+; PanelPainter ~7k on 7.5k pairs) are far longer than a character run, which is what teaching an operation rather than a face should cost.

**The prompt is part of the dataset.** BFS ships its trigger as a whole paragraph of instruction, and the `Picture 1: / Picture 2:` convention is **the format Qwen-Image-Edit was trained on** (§5.2). Edit-LoRA captions must be written in that format or the LoRA will not fire the way the base model expects.

---

## 5. Character consistency without training

### 5.1 Edit is the identity tool, and the vendor says so

`[official — Qwen/Qwen-Image-Edit-2511 model card, read 2026-09-09]`: *"Character consistency has been significantly improved. The model can perform imaginative edits based on an input portrait while preserving the identity and visual characteristics."* And it *"further enhances consistency in multi-person group photos — enabling high-fidelity fusion of two separate person images into a coherent group shot."* Headline changes over 2509: mitigate **image drift**, improved **character consistency**, **integrated LoRA capabilities**, industrial design, geometric reasoning.

Independent read: *"Qwedit 2511 is fucking sick. IMO it particularly excels at making new shots of characters while maintaining their likeness. It's significantly better than Klein at some things (like character likeness), but not as good at others"* `[nsfwVariant, 2026-06]`.

**Reference count:** official support is **three** control images on 2509/2511 `[official — musubi docs]`; hosted deployments commonly expose a base image plus **two** references.

**How many edits does identity survive? Nobody has published a number.** No named author reports an N. Treat sequential-edit endurance as **unmeasured**; the honest advice is to re-anchor on the original reference each edit rather than chaining.

### 5.2 The four things that decide Qwedit identity quality

From one author who A/B'd sixteen reference-handling combinations `[nsfwVariant, r/StableDiffusion, 2026-06]`:

1. **ComfyUI's `TextEncodeQwenImageEditPlus` node degrades your input.** It force-downscales the reference to 1 Mpx, uses **AREA** downsampling — *"the primary reason all ComfyUI qwen edits give blurry images out"* — and rounds to divisible-by-8 where Qwen needs **16**. Bypassing it and scaling with Lanczos yourself is the single biggest quality win, and it is what enables native 1440–1920 px edits.
2. **Double-ref** — feed the reference in **twice**: better prompt adherence, sharper output, *"better resemblance of characters at different angles"*, at ~50% more time. *"For single image edits it's ALWAYS better."*
3. **`Picture 1: … Picture 2: …`**, one simple sentence per input, at the start of the prompt. *"You must write it this way because Qwedit was trained on this exact format."* Bypassing the node removes the vision-language stage that normally writes these labels in unhelpful detail — *"A 5 word description wins over whatever BS the VL model spews out, every time."*
4. **The Qwen VAE prints a faint halftone grid**, worse at high resolution and worse on Edit than on T2I. Fix with a 0.5–0.75× downscale and re-upscale (SeedVR2, or `4x Nomos2 HQ DAT2`). A **decode** artefact — do not diagnose it as LoRA overfit.

Cost on a 5090, double-ref on, single-image edit: 1 Mpx **52 s**, 2 Mpx **131 s**, 5.3 Mpx **550 s**. Stay at **2–3 Mpx**.

### 5.3 Character LoRA plus Edit

- **Train on T2I, use with Edit** — usually loads, sometimes works, a dedicated train always better (§1.5).
- **Use Edit to *build* the dataset.** acekiube's published workflow takes one upper-body headshot and generates **20 angle variants** on Edit-2509 fp8 + 4-step Lightning (130 s on a 5090), writing the character name into 20 `.txt` sidecars `[2025-10]`. A Nunchaku fp4 variant does 12 captioned images in ~4 min under 16 GB `[The-ArtOfficial, 2025-10]`. **This is Qwen's answer to the v0-LoRA chicken-and-egg problem, and it is cheaper: the Edit model *is* the v0.**
- **Swap the identity in afterwards** — BFS plus a head-swap workflow needs no training at all; a separate no-LoRA workflow chains Qwen Edit + Lightning 4-step + face detection + ControlNet + SeedVR2 `[Substantial_Angle680, 2025-12]`.
- **Budget a face detailer.** *"For distant shots, Qwen LoRAs often require FaceDetailer to make the likeness look better. ZIT sometimes needs FaceDetailer too, but not as often as Qwen"* `[Top_Buffalo1668, 2026-01]`.

### 5.4 Identity adapters — verified negative

**There is no PuLID, InstantID, or IP-Adapter-FaceID for Qwen-Image** (searched 2026-09-09; that family remains SD1.5 / SDXL / Flux). Qwen has instead: the Edit model's own multi-reference conditioning, the community face-swap Edit LoRAs, and DiffSynth's experimental **Qwen-Image-i2L**, whose own authors flag weak generalisation and detail preservation. **State the absence plainly** — readers arriving from SDXL will look for it.

---

## 6. Evaluation and collapse modes

### 6.1 Civitai, re-measured 2026-09-09

Counted from the Civitai API (`types=LORA&baseModels=Qwen&nsfw=true`, full cursor pagination, 17 pages) `[community — Civitai model API, sampled 2026-09-09]`: **1,637** Qwen LoRAs; **273 character-tagged (16.7%)**; **773 style-tagged (47.2%)**; 257 concept; **422 (25.8%) flagged `nsfw: true`**.

The commission brief quotes **1,162 / 192** from the same day's launch sweep. The character *ratio* is nearly identical (16.5% vs 16.7%), so the difference is almost certainly the `nsfw=true` parameter — **the brief's figure excludes adult models.** Use either, but say which.

**Style outnumbers character 2.8:1**, and Qwen's adult share (26%) is half Krea 2's (52%). Qwen is a broader, less adult-dominated ecosystem. Top downloads: `SNOFS` (Ashen3, 249k), `Lenovo UltraReal` (Danrisi, 164k), an Edit-2511 anatomy adjuster (m99, 160k), `Mystic XXX` (146k), `NiceGirls UltraReal` (113k), `Amateur Photography` (84k), `BFS` (71k). **Realism-booster styles and adult-anatomy LoRAs dominate; no character LoRA is near the top.**

### 6.2 Collapse tells

- **A band with both edges named:** *"80–100 repeats per image is the gold standard… Under 50 repeats and it doesn't look like the person; over 100 and the quality starts to break or get 'fried'"* `[FarTable6206]`.
- **Rank failure on Qwen is *over-generalisation*, not over-fit** — rank 64 loses the person's specificity; rank 16 skips fine detail. Compare Krea 2 (r64 bought nothing) and H3 (r32 collapsed).
- **View lock-in from captions** — labelling "front view" on every photo sticks the LoRA in that view.
- **Full-body over-representation → blurry faces** at full-body inference.
- **Plastic skin has at least three separable causes:** the Lightning distillation, the base model itself at 12 steps, and the sampler (`res_2s` + `bong_tangent` is offered as a partial fix — note `res_2s` is a known *drift source* on Krea 2).
- **Two distinct grid artefacts, neither of them your LoRA:** the **VAE halftone** (fixed by a downscale/upscale round-trip) and the **fp8 grid** (fixed by the scaled fp8 file or bf16).
- **Colour cast: check the Lightning version first.** V1.x over-saturates by the maintainers' own admission.
- **Concept bleeding is comparatively *mild* on Qwen.** Same-dataset test: *"the concept bleeding on ZIT is worse than Qwen"*, and Qwen tolerated three stacked LoRAs where Z-Image Turbo managed two `[Top_Buffalo1668]`.

### 6.3 A Qwen evaluation matrix (synthesis — nothing published prescribes one)

Deploy checkpoint × step regime {base @20, Lightning @4 or @8} · base file bf16 or **scaled** fp8, never plain `fp8_e4m3fn` · two face scales (close-up and full-body), with and without a detailer · **a strength-0 control in every grid**, to separate base artefacts from LoRA artefacts · the trigger-removed prompt for bleed · and **raise `max_step_saves_to_keep`** above ai-toolkit's shipped 4, or you lose the rungs you need to grid.

---

## 7. NSFW

- **Base behaviour: safety-tuned, not stripped.** The community frames it as "uncensoring" — `MCNL` is *"a convenient way to uncensor Qwen with many concepts included"* `[jorkingtoncityshallwe, Civitai]`. A large working adult LoRA layer means the base weights carry the anatomy; the reticence is tuning. Same read the suite records for Krea 2.
- **26% of Qwen LoRAs are adult-flagged** (422 of 1,637) against Krea 2's 52% `[Civitai API, 2026-09-09]`.
- **Encoder refusals: no report found of Qwen2.5-VL refusing a training or inference prompt.** What people describe is the *base model declining to draw*. Do not assert an encoder refusal without evidence.
- **Abliterated encoders** exist in the wider Qwen-LLM ecosystem and are used with other image models (a named ComfyUI node runs a Q4 abliterated Qwen3-VL GGUF encoder for Z-Image `[mybrianonacid, 2026-03]`). For **Qwedit specifically there is a direct recommendation against them**: *"Use only the normal FP8 text encoder with Qwedit; abliterated/GGUF encoders will reduce your output quality"* `[nsfwVariant, 2026-06]` — one author, stated flatly, no A/B, and the only Qwen-specific statement on the question.
- **Named adult artefacts** `[Civitai API, read 2026-09-09]`:
  - **`SNOFS`** (Ashen3, ~249k downloads, the most-downloaded Qwen LoRA of any kind). Built as a **LoKr**, with a merged-checkpoint edition and a companion "photo detail slider". The author's prompting rule, written for their Krea 2 build: **say "photo" or "photograph"; never "photorealistic"** or a near-synonym, because the base saw a lot of artwork and those words pull the render back toward it.
  - **`MCNL`** — leet-style triggers (`nsfw, cum_on_face, blowjob, cowgirlout, creamp1e, penis, l1ck, missionary, nipples, reversecowgirlpov, vagina`), with the author's own caveat that single-concept LoRAs beat multi-purpose ones on quality.
  - **`Mystic XXX`, `QWEN 4 PLAY` (AIO), `Send Nudes`, `Real_Nud3s`, `SexGod NSFW … 2511`, `Jib's Nudity Fixer`, per-anatomy enhancers** — a segmented ecosystem, several shipping **cross-base lines** (Qwen, Krea 2, Z-Image, Flux, Chroma) from one dataset.
  - **`Qwen-Rapid-AIO-LiteNSFW`** (Phr00t) — an AIO Qwen-Edit checkpoint with NSFW capability baked in, used in a published multi-angle workflow `[Hearmeman98, 2025-11]`.
- **The trigger finding inverts for concept LoRAs.** Character authors converge on plain names in prose; adult *concept* LoRAs use short leet tokens (`l1ck`, `creamp1e`, `h34d_sw4p`) and they work. That is consistent: a concept LoRA needs a handle the base has no prior for, and a character LoRA needs the base's person-prior to cooperate.
- **Publishing gates still bind harder than capability** (Civitai's real-person ban, TAKE IT DOWN Act) — owned by `character-lora-training/references/publishing-and-likeness.md`. Note that BFS's own model card asks users not to post swaps of public figures or non-consenting individuals: the constraint is visible *inside* the Qwen ecosystem, not only above it.

---

## 8. Hyperparameter table

What the named source states, not a recommendation. `—` = the source is silent.

| Source | Base | Rank/alpha | LR | Optimizer | Resolution | Steps | Shift / timestep | Provenance |
|---|---|---|---|---|---|---|---|---|
| ai-toolkit example | Qwen-Image | 16 / 16 | 1e-4 | adamw8bit | `[512,768,1024]` | 2,000 | flowmatch, no `timestep_type` | `[official — train_lora_qwen_image_24gb.yaml, 2026-09-09]` |
| ai-toolkit example | Edit (2508) | 16 / 16 | 1e-4 | adamw8bit | `[512,768,1024]` | 3,000 | `timestep_type: weighted` | `[official, 2026-09-09]` |
| ai-toolkit example | Edit-2509 | 16 / 16 | 1e-4 | adamw8bit | `[512,768,1024]` | 3,000 | `timestep_type: weighted` | `[official, 2026-09-09]` |
| musubi-tuner | any variant | dim 16 | **5e-5** | adamw8bit | 1024² (VRAM table) | 16 epochs | `shift` + `discrete_flow_shift 2.2`, or `qwen_shift` | `[official — docs/qwen_image.md, 2026-09-09]` |
| musubi finetune | any | full FT | **1e-6 – 1e-5** | adafactor + fused backward | — | 16 epochs | `max_grad_norm 0` | `[official, 2026-09-09]` |
| DiffSynth | every variant | **32** | 1e-4 | — | `max_pixels 1048576` | 5 epochs × repeat 50 | `--zero_cond_t` for 2511 | `[official — lora/*.sh, 2026-09-09]` |
| diffusion-pipe | Qwen-Image | — | — | — | **640** in the example | — | `logit_normal` | `[official — supported_models.md, 2026-09-09]` |
| SimpleTuner | Qwen-Image | **8 or lower** @24 GB | 1e-4 | optimi-lion / adamw-bf16 | 512/768 → 1024 | — | `flow_schedule_shift 1.73` | `[official — QWEN_IMAGE.md, 2026-09-09]` |
| FarTable6206 (character) | 2512, Edit-2511 | **32** | **2e-4** | — | ≥1024 | **80–100 repeats/img** → 3,000–6,000 | `sigmoid` + `constant`; batch 1, GA 1 | `[community — r/StableDiffusion, 2026-01]` |
| Icy_Upstairs3187 (character) | Qwen-Image | — | — | — | **1440 @ 4:5** + a 1440 bucket | **6,000** | — | `[community, 2025-08]` |
| AI_Characters (realism style) | Qwen-Image | — | — | — | — | — | custom **polynomial scheduler with min LR** (patched `scheduler.py`) | `[community, 2025-08]` |
| Nyao (style) | Qwen-Image | — | **2e-4** | — | — | **2,750** | — | `[community, 2025-08]` |
| Substantial_Angle680 (style) | Qwen-Image, OneTrainer | — | — | — | — | **120 epochs / 50 imgs** | — | `[community, 2025-11]` |
| ProGamerGov (360 concept) | Qwen-Image | **128** | — | — | 2048×1024 target | 2.3M steps, ~4 months | nf4 32 ep → int8 16 ep | `[community, 2026-01]` |
| NRDX / BFS (Edit swap) | Edit-2509, 2511 | — | — | — | — | **5,500+**, then a 2509×2511 merge | — | `[community — Civitai, 2026-09-09]` |
| PanelPainter (Edit) | Edit-2509 | — | — | — | — | **~7,000** on ~7,500 pairs | deploy weight 0.45–0.6 | `[community, 2025-11]` |

---

## 9. Transfers from Krea 2 / does not transfer

Krea 2 is Qwen-Image-derived and shares the **Qwen-Image VAE**, so *setup* transfers further than *doctrine* does.

**Transfers.** DiT-only with the encoder frozen (all trainers) · plain-name-in-prose triggers, reached independently on Qwen · caption-the-residual, sharpened here to "never write `face`/`eyes`/`mouth`/`nose`" · a distilled inference path costs skin and hair detail (the Lightning vendor says so for hair) · the Qwen VAE decode is an artefact source you must not blame on the LoRA (here, the halftone grid) · validate on the deploy checkpoint at the deploy step count with a strength-0 control — **reinforced**, because Qwen has *three* base-artefact sources (halftone, plastic skin, fp8 grid) that one strength-0 render separates · adult work is a data question, so look for an existing LoRA or AIO checkpoint first · count is not the lever (named authors span 18 → 100 images with no monotone relationship) · and literally the same `qwen_image_vae.safetensors` file.

**Does not transfer.**

- **"Train on Raw, run on Turbo."** No Raw/Turbo split exists. Qwen-Image is undistilled; Lightning is an inference-time LoRA. The doctrine has no referent here.
- **The Ostris turbo *training* adapter.** No Qwen equivalent. Do not invent one by analogy.
- **`discrete_flow_shift 2.5` / `krea2_shift`.** Qwen's figure is **2.2**, kohya says its inference shift is deliberately *low*, the resolution-aware sampler is `qwen_shift`, and SimpleTuner uses **1.73**. Carrying 2.5 across is a real error.
- **LR 1e-4 as settled.** Qwen's band is **5e-5 → 2e-4**, wider than Krea's.
- **Rank/alpha 32 as "the" setting.** Every shipped Qwen default is 16 (8 at 24 GB on SimpleTuner); 32 is a community character finding; 128 is used for concepts.
- **"Render sources at 1024-native, never above."** Krea-specific, measured on *generated* sources against a 1K-native base. Qwen's inference band is the **1328-class ~1.5 Mpx** aspect set and a named author trained at 1440. **No Qwen measurement of the hi-res-source hazard exists.**
- **"Rare tokens surface as text and watermarks."** Krea 2, single report. Qwen reaches the same conclusion by a different route; the mechanism is unevidenced here.
- **`gradient_accumulation: 2` as a free win.** The strongest Qwen character report prescribes GA 1, to *"avoid identity dilution."*
- **LoKr as the preferred character decomposition.** Krea 2 / Z-Image evidence; no named Qwen *character* author uses it.
- **One-third identity / two-thirds context.** The named Qwen recipe is **60/30/10** and argues against full-body-heavy sets by name.
- **Adult-finetune resolution bands** (`fineporn`-style). Krea 2 checkpoint craft; Qwen's adult layer is LoRAs and AIO Edit checkpoints, with no published band findings.

---

## 10. Contested

1. **Caption length** — verbose `[Icy_Upstairs3187]` vs 30–50 words `[FarTable6206]` vs one word `[acekiube]` vs none (style authors). Only FarTable6206 claims to have tested the range.
2. **Learning rate** — 5e-5 (musubi) vs 1e-4 (three trainers) vs 2e-4 (measured best, *conditioned on* sigmoid).
3. **Rank** — shipped 8–16, character consensus 32, concepts 128. One published 16/32/64 ladder, one author, one dataset.
4. **Training resolution** — 512/640/768 vs 1024 vs 1440. Nobody has A/B'd 1024 against a 1328-class bucket, which is the question Qwen's native aspect set actually raises.
5. **Composition ratio** — 60/30/10 vs 33/33/33 vs "≥50% headshots" vs the suite's ~0.33. Same model, opposite prescriptions.
6. **Gradient accumulation** — 1 on Qwen vs 2 as a strong win on Krea 2. Cross-model, so possibly both right.
7. **`timestep_type`** — shipped Edit configs say `weighted`; the character report says `sigmoid` is *"miles ahead"* and cites the toolkit author's own video.
8. **How much of "plastic skin" is Lightning's fault** — one author blames the distillation flatly, another sees it with no Lightning loaded.
9. **Qwen vs Z-Image for character realism** — one same-dataset comparison: ZIT wins realism and prompt adherence, Qwen wins concept bleeding and multi-LoRA stacking. One report.
10. **Whether the uint3 + recovery-adapter path costs LoRA quality.** It is the shipped 24 GB default; no bf16-vs-uint3 comparison published.

---

## 11. Thin / single-report

- **Edit-2511 in ai-toolkit needs a 1024×1024 solid black control image**, and uses 30–50% more VRAM than 2512 `[FarTable6206]`. Load-bearing if true.
- **2512 ↔ 2511 LoRA cross-loading "works but is not perfect"** `[FarTable6206]`.
- **`--zero_cond_t` for Edit-2511** — one unexplained line in a DiffSynth script `[official, but one line]`.
- **Edit-2511 "has an architecture with a few more layers" than 2509**, so an un-updated ComfyUI gives *"completely distorted or ugly images"* `[NRDX / BFS card]` — stated by a LoRA author, not by Qwen.
- **`res_2s` + `bong_tangent` for Qwen realism** `[Top_Buffalo1668]` — note `res_2s` is a known drift source on Krea 2, so both suite entries need labelling.
- **`ModelSamplingAuraFlow` shift below 0.3 (down to 0.02 at high resolution)** for the Edit upscale LoRA `[vafipas663]`.
- **BFS's 2509 × 2511 merge beats the pure 2511 train on expression range** `[NRDX]`.
- **"Only the normal FP8 text encoder; abliterated/GGUF reduce quality"** on Qwedit `[nsfwVariant]`.
- **"Say photo/photograph, never photorealistic"** — the SNOFS author, writing about their Krea 2 build on a Qwen-derived base. Plausible for Qwen, evidenced on Krea `[Ashen3]`.
- **The double-ref trick and the sixteen-way reference A/B** — one author, but the most systematic Qwedit testing published and reproducible from the shipped workflows `[nsfwVariant]`.
- **No published number for how many sequential Edit passes identity survives.** Genuinely absent.
- **No published Qwen Lightning-LoRA *training* recipe.** Asked publicly, zero replies.
- **Qwen-Image-i2L** — official, self-described as weak, no independent evaluation found.

---

## 12. Open questions for the skill author

1. Does the 1328-class native aspect set change the training-bucket recommendation? Untested — say so rather than defaulting to 1024 silently.
2. musubi's 5e-5 or the community's 2e-4? They differ 4×; the safest framing is the sigmoid/constant conditioning attached to 2e-4.
3. `qwen_shift` vs a fixed `2.2` — the same shape as Krea's question, with no Qwen A/B.
4. **Qwen-Image-2512 is a different base** with its own Lightning LoRA and its own ai-toolkit arch, but nearly all community craft was written for the original Qwen-Image. Decide how the skill handles that split.
5. **Qwen-Image-Layered** is trainable in musubi (`--model_version layered`, `multiple_target = true`, its own VAE) and DiffSynth, and no community LoRA literature covers it. A genuine white space.
