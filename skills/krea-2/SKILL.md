---
name: krea-2
description: >
  Authoritative guide for Krea 2 (K2) by Krea AI across all variants and surfaces. Use this whenever the user
  touches Krea 2 in any way, even obliquely: choosing a variant (open-weights Raw vs Turbo vs the hosted-only
  Medium/Large — and why hosted Large literally has a different VAE), installing it in ComfyUI (exact
  Comfy-Org filenames and folders, the stock 8-step/cfg-1 template, CLIPLoader type "krea2", the built-in
  prompt-enhancer subgraph and why to turn it off), writing or fixing prompts (the Qwen3-VL LLM encoder wants
  descriptive sentences, not quality tags; content in the prompt, style in the controls; quoted text
  rendering), getting photoreal results (fighting the deliberate soft/airbrushed default — Wan 2.1 VAE swap,
  texture anchors, the 3D-render bias), using style references / moodboards / the creativity dial on the
  hosted surfaces, using and stacking the official style LoRAs (trigger phrases, strengths), calling the Krea
  API or fal endpoints (medium/large slugs, pricing, aspect ratios), running it in diffusers (Krea2Pipeline,
  the guidance-scale convention trap), quantisation and VRAM (fp8 vs int8-convrot vs nvfp4 vs community GGUF),
  training a LoRA (TRAIN on Raw, RUN on Turbo — and the contested Ostris turbo-adapter alternative; musubi-tuner
  and AI-Toolkit settings), building a consistent character (the character-LoRA path; no PuLID/InstantID
  exists yet), multi-stage and mixed-model pipelines (the Raw+Turbo-LoRA two-stage recipe, Z-Image as the
  inpaint partner), or debugging muted facial expressions, halftone/grid artefacts, dark-area noise, weak
  text rendering, or prompts the stock enhancer refuses. Use this for any question about Krea 2 in any context.
---

# Krea 2

Krea 2 (K2) is Krea AI's first from-scratch foundation image model — a **12B-parameter single-stream MMDiT** trained with flow matching, announced 12 May 2026, with **open weights (Raw + Turbo) released 22 June 2026**. The text encoder is **Qwen3-VL 4B Instruct**, tapped unusually deeply: hidden states from **twelve decoder layers per token** are fused by a small text-fusion stage, letting the DiT select coarse-to-fine text representations. The open-weights models decode through the **Qwen-Image VAE** (f8, 16 latent channels). Code is Apache-2.0; weights are under the **Krea 2 Community License** (commercial use gated on company revenue — see Licence below). Krea's positioning claim: "the most aesthetic open-source image model available … #1 text-to-image model from an independent lab on Artificial Analysis" [official — GitHub README].

Its defining trait is a deliberate refusal to have a house look. Where most models optimise a single polished default, Krea 2 "is designed to expose a broad visual space" and be "raw, flexible, unopinionated, and unconstrained" [official — announcement/tech report]. Style is a **control surface**, not a prompt word: style references, moodboards, official style LoRAs, and a creativity dial carry the look; the prompt carries the content. The flip side, confirmed independently by three named community testers, is that the default output reads *soft* — and that the safety tuning mutes facial expressiveness. Both have named fixes (see *The anti-AI-look and its two taxes*).

---

## Variant selector

The load-bearing axis is the **role split** — which checkpoint you train on, which you run, and which you rent:

| Variant | Nature | Steps / guidance | Resolution | Access | Use when… |
|---|---|---|---|---|---|
| **Raw** | undistilled base — "not recommended for inference use" [official — HF card] | 52 / cfg 3.5 (HF card); 28 / 4.5 (diffusers default) ¹ | 1K native | Open weights (`krea/Krea-2-Raw`) | **LoRA training and fine-tuning base**; the Raw+Turbo-LoRA inference recipe (community) |
| **Turbo** | 8-step TDM-distilled (guidance + timestep distillation) | 8 / guidance off ² | 1K–2K | Open weights (`krea/Krea-2-Turbo`) + fal + web app | **The local workhorse** — fast, high-quality t2i; where LoRAs trained on Raw get applied |
| **Medium** | hosted-only, "stable, general-purpose" | managed | 1K (API, currently) | krea.ai app + API + fal + ComfyUI partner nodes | Hosted default; style refs + moodboards; $0.030/img |
| **Large** | hosted-only, photorealism flagship — **trained with the FLUX.2 VAE**, not the open models' Qwen VAE ³ | managed | 1K (API, currently) | same | Maximum fidelity, hosted; $0.060/img |

> ¹ Two official numbers coexist: the HF model card and inference CLI say **52 steps / cfg 3.5**; the diffusers pipeline documents the non-distilled ("base/midtrain") checkpoint at **28 steps / guidance 4.5**. Both are official — treat 52/3.5 as the Raw-card recommendation, 28/4.5 as the diffusers default.
> ² **Guidance-off means different numbers on different surfaces.** diffusers/CLI: `guidance_scale=0.0` (Krea's convention: velocity = `cond + g·(cond − uncond)`, so 0 = off; it equals classic CFG `1 + g`). ComfyUI KSampler: **cfg 1.0** (the classic scale) — the official template ships cfg 1.0 with the negative branch through `ConditioningZeroOut`. musubi-tuner uses the classic scale too: official "guidance 4.5" = `--guidance_scale 5.5` there. Copying a number between surfaces without converting is the #1 setup error.
> ³ Confirmed by Krea's mattnewton on HN: hosted Large trained with the FLUX.2 VAE; open weights use the Qwen-Image VAE [official — team statement]. Hosted output ≠ open-weights output at the architecture level, not just the size level.

**Default workflow:** run **Turbo** locally (8 steps, guidance off, 1–2K). Use **Raw** only to train on — its CFG-off output is blurry *by design* (undistilled) [official — musubi docs]. Reach for **Medium/Large** when you want the style-reference/moodboard system or the last increment of hosted fidelity. Announced but unreleased: official edit models ("robust editing, image reference, and native 2K/4K" are named future work in the tech report; Krea's CTO says edit models are "coming").

---

## The one rule that changes everything

**Put the content in the prompt and the style in the controls.** Krea's own thesis: "Style should not be a vague prompt word. It should be something you can guide, mix, strengthen, reduce, and push" [official — announcement]. In practice:

- **The prompt** is parsed by Qwen3-VL, an instruction-following VLM — it reads clause structure and word order like a language model, so write **descriptive natural language**, front-loaded. Booru quality chains (`masterpiece, 8k, best quality`) are noise to it. (This is the encoder class, not folklore: the same sentence rule governs FLUX.2's Mistral/Qwen3 and Z-Image's Qwen-3; the *opposite* — weighted tags, rare-token triggers — governs CLIP models like SDXL.) The official prompting guide's examples run both registers — full prose paragraphs *and* dense comma-separated descriptor lists — and both work, because a VLM parses either; what matters is that every token is *descriptive*, not incantational. "Long detailed prompts yield best results, but the model is capable of generating high quality images with minimal prompt engineering" [official — docs/prompting.md].
- **The style** goes through the control surfaces: style LoRAs locally — the official nine plus a community explosion (1,500+ style LoRAs from ilker/fal alone) — with natural-phrase triggers (`monochrome ink wash style` — a describable phrase, not a rare token, exactly what an LLM encoder wants); style references (with per-reference strength), moodboards, and the creativity dial (raw → high) on the hosted surfaces. Creativity **raw** "renders only explicit descriptions without expansion"; **high** takes "meaningful creative liberty" [official — user guide].
- **Text to render goes in straight quotes** — `a neon sign reading "OPEN LATE"` [official — docs/prompting.md].

**The community corollary: turn the stock prompt-enhancer off.** The official ComfyUI template ships an LLM prompt-expansion subgraph *enabled by default*. It refuses benign prompts — "photo of a dog on a kitchen table" gets an ethics lecture instead of an expansion [community — 808charlie, Comfy-Org/ComfyUI#14631] — and named workflow authors ship abliterated-Qwen replacements rather than use it [community — lonecatone23, Civitai]. Toggle `prompt_enhance` off in the subgraph and write the full prompt yourself, or swap in the API-node enhancer of your choice. If you want LLM expansion offline, Krea publishes the expander's system prompt (`docs/expansion.txt` in the GitHub repo) for use with any LLM [official].

Full prompt anatomy, official example prompts, realism vocabulary, and the style-LoRA trigger table: **`references/prompting-guide.md`**.

---

## Setup & ecosystem

Krea 2 runs in **ComfyUI core** — no custom nodes; update ComfyUI first. The DiT is not a checkpoint: three loaders.

### File layout

From `Comfy-Org/Krea-2` on Hugging Face (verbatim from the official template `image_krea2_turbo_t2i.json`):

| File | ComfyUI folder | Loader node |
|---|---|---|
| `krea2_turbo_fp8_scaled.safetensors` (13.1 GB) | `models/diffusion_models/` | `UNETLoader` |
| `qwen3vl_4b_fp8_scaled.safetensors` (5.2 GB) | `models/text_encoders/` | `CLIPLoader` (type **`krea2`**) |
| `qwen_image_vae.safetensors` (0.25 GB) | `models/vae/` | `VAELoader` |
| `krea2_<style>.safetensors` (0.47 GB each, optional) | `models/loras/` | `LoraLoaderModelOnly` |

### Stock node settings (template JSON, verbatim)

| Node | Setting | Value |
|---|---|---|
| `KSampler` | steps / cfg / sampler / scheduler / denoise | **8 / 1.0 / `euler` / `simple` / 1.0** |
| `EmptyLatentImage` | size | 1024 × 1024 (a `ResolutionSelector` subgraph offers 1K–2K aspect presets) |
| `ConditioningZeroOut` | negative branch | zeroed — negatives are structurally inert at cfg 1.0 |
| `LoraLoaderModelOnly` | strength | 0.8 (official style LoRAs are documented at 0.8–1.0 per LoRA) |
| `TextGenerate` (prompt-enhance subgraph) | `prompt_enhance` toggle | **on by default — see the one-rule section for why you probably want it off** |

Note what's *absent*: no shift node (no `ModelSamplingAuraFlow` — the resolution-aware time shift lives in the model config), and the plain `EmptyLatentImage`, not an SD3/Flux latent node. A `CustomCombo` on the main canvas auto-appends the selected style LoRA's trigger phrase to your prompt.

### Quantisation & VRAM

**Official** (all in `Comfy-Org/Krea-2`, sizes from the repo listing): Turbo and Raw each ship `bf16` (26.3 GB), `fp8_scaled` (13.1 GB), `int8_convrot` (13.5 GB); Turbo additionally `mxfp8` (13.5 GB) and `nvfp4` (7.7 GB). Text encoder: `qwen3vl_4b_bf16` (8.9 GB) or fp8 (5.2 GB). **int8 convrot is ~2× faster than fp8** — replicated across hardware down to a 1050 Ti [community — nsfwVariant; YeahYeah2992, r/comfyui] — but its quality claim is now disputed: "equal or better" [nsfwVariant, YeahYeah2992] vs "int8 loses complex-prompt adherence that fp8 keeps" [community — ganrocks007, r/StableDiffusion]. If a complex prompt falls apart on int8, re-test on fp8 before rewriting the prompt. bf16 wants ~46 GB unified memory [community — liutyi]. Comfy publishes no official VRAM thresholds. Community fp8 requants (e.g. AlperKTS `Krea2_FP8`) and Civitai **checkpoint merges** (Fascium, MysticXXX-class) are appearing — merges inherit none of the stock numbers' guarantees.

**Community GGUF** (no city96 repo for this model — the ecosystem is `gguf-org/krea-2-gguf`, `vantagewithai/Krea-2-Turbo-GGUF` + `-Raw-GGUF`, others): Q2_K 4.9 GB → Q4_K_M 7.5 GB → Q6_K 10.6 GB → Q8_0 13.7 GB. Rough placement: Q4 for 12 GB cards, Q8/fp8 for 16–24 GB, plus the encoder (GGUF-able/offloadable). Requires the `ComfyUI-GGUF` custom node. No per-quant quality shootout has been published yet — placement is size arithmetic, not measured craft.

### diffusers

```python
from diffusers import Krea2Pipeline  # requires diffusers from source (main) as of early July 2026
pipe = Krea2Pipeline.from_pretrained("krea/Krea-2-Raw", torch_dtype=torch.bfloat16)
image = pipe(prompt, num_inference_steps=52, guidance_scale=3.5).images[0]   # Raw card settings
# Turbo: is_distilled=True in the pipeline config → fixed mu=1.15; num_inference_steps=8, guidance_scale=0.0
```

Classes: `Krea2Pipeline`, `Krea2Transformer2DModel`, `AutoencoderKLQwenImage`, `Qwen3VLModel`. Scheduler is `FlowMatchEulerDiscreteScheduler` with `use_dynamic_shifting=True`, `base_shift=0.5`, `max_shift=1.15` (resolution-aware exponential time shift). `max_sequence_length=512`; dimensions round up to multiples of 16. Remember the guidance convention (footnote ² above). t2i only — no img2img/inpaint/edit pipelines exist yet.

### Hosted surfaces

Krea API (`api.krea.ai`, async job pattern): `POST /generate/image/krea/krea-2/medium|large` — Medium $0.030/img, Large $0.060 (style refs and moodboards add $0.005–0.010); 1K-only for now; `creativity` raw/low/medium/high; up to 10 style references with per-ref strength. fal hosts `fal-ai/krea-2/turbo`, `/turbo/lora`, and `fal-ai/krea-2-trainer`. ComfyUI partner/API nodes expose Medium/Large with style refs and moodboard IDs. Full endpoints, params, pricing, and the hosted-vs-open differences: **`references/api-and-hosted.md`**.

---

## Per-variant settings

### Turbo (the local workhorse)

- **Steps:** 8 [official — template & CLI]. Community: gains past 8 are minimal at 1024 (tested to 12) [community — liutyi]; going *down* works — `res_2s`/`beta` at 4–5 steps for texture, `er_sde`/`simple` at 4–9 for clean output [community — RaymondLuxuryYacht, Civitai]; at higher resolutions some run longer — `euler_ancestral`/`simple` at 15 steps, 1536×1792 (with `uni_pc_bh2` as the alternate) [community — m0ran1 sampler thread, r/StableDiffusion].
- **Guidance:** off — ComfyUI cfg **1.0**, diffusers/CLI `guidance_scale=0.0`, `--mu 1.15` pinned [official]. Negatives are inert here (the template zeroes them). **cfg 2.0 re-enables negative prompts** at ~2× generation time [community — nsfwVariant] — a workaround, not a supported feature.
- **Sampler/scheduler:** `euler`/`simple` stock; the community recipes above swap samplers freely.
- **Resolution:** 1024–2048 px, multiples of 16. Solid at 1024 and native 2048; extreme ratios (e.g. 1600×400) degrade [community — liutyi]; cinematic wide ratios within reason are a reported strength [community — nsfwVariant].
- **LoRAs:** `LoraLoaderModelOnly`, official style LoRAs at 0.8–1.0 with their trigger phrases; character LoRAs trained on Raw commonly hold at ~0.8 [community — JahJedi].

### Raw (the training base)

- **As a base for training:** this is its job — see `references/lora-training.md`.
- **As an inference model:** 52 steps / cfg 3.5 [official — HF card] (diffusers default 28/4.5; musubi `--guidance_scale 5.5` ≙ official 4.5). CFG-off output is blurry — expected, undistilled [official — musubi docs]. 1K native; it was not trained for 2K.
- **Raw-as-inference is contested craft:** one named author gets "WAY better" photoreal from **Raw + the official Turbo LoRA (`loras/krea2_turbo_lora_rank_64_bf16.safetensors`) at 0.6** in a two-stage workflow [community — nsfwVariant]; another finds plain Raw *more* airbrushed than Turbo at 30 steps/cfg 4 [community — amida168, kombitz.com]. The difference is plausibly the Turbo-LoRA + VAE swap in the first recipe. No consensus — if you try Raw for inference, use the full recipe, not plain Raw.

### Medium / Large (hosted)

Managed sampling — you control prompt, aspect ratio, seed, creativity, style refs/moodboards, and the intensity/complexity/movement sliders (−100…100). Large is the photoreal pick and renders through the FLUX.2 VAE. Settings and pricing: `references/api-and-hosted.md`.

---

## The anti-AI-look and its two taxes

Krea 2's signature is the *absence* of the over-sharpened, hyper-saturated "AI look" — a deliberate design goal the team defends when challenged [official — team statements on HN]. Two costs ride along, and they are the two most-replicated community findings on this model:

**Tax 1 — the soft/airbrushed default.** Outputs read blurry-soft next to Flux-class models; skin trends airbrushed. Mechanism: partly the deliberate no-over-sharpening tuning, partly the Qwen-Image VAE's rendering character. Fixes, in escalating order:
1. **Prompt for texture explicitly** — "natural skin texture, visible pores, subtle skin imperfections" [community — amida168]. The model also has a mild bias toward 3D-render/digital-art interpretations, so photoreal prompts need explicit photographic framing — camera body, lens, film stock, the same stack that works on every LLM-encoder model.
2. **Swap the VAE** — decode through the **Wan 2.1 VAE** (FP32) instead of `qwen_image_vae`; multiple named users report it "solves" the softness [community — mobiuscog (HN), nsfwVariant]. Latent-compatible, drop-in at the `VAELoader`.
3. **Detailer passes** — SAM3 face/eye detailers + tiled upscale in the larger community workflows [community — lonecatone23].

**Tax 2 — muted expressions.** Faces cluster at neutral-or-smile; emotional range is damped. Three named sources independently attribute this to the safety tuning ("quality dilution") [community — liutyi; nsfwVariant; nova452]. Fixes: bypass LoRAs (reported to improve strictly-SFW output too), nova452's `ComfyUI-Conditioning-Rebalance` per-layer conditioning nodes, or a noisier first-stage sampler (the deliberately-undercooked 6-step first stage in the two-stage recipe exists partly for this). If a specific facial expression is the shot's whole point, consider generating the face with Z-Image and compositing — see the suite table below.

---

## Production pipelines & mixing models

Krea 2 generates 1–2K natively, so the ladder starts high:

1. **Base gen** — Turbo, 8 steps, guidance off, 1–2K. Judge composition; reroll seeds freely.
2. **Two-stage refine** (the best-documented local recipe, [community — nsfwVariant]): stage 1 **Raw + Turbo-LoRA @ 0.6**, 6 steps `res_2s`/`beta` — deliberately undercooked to keep expressiveness; stage 2 **2 steps `deis_3m`/`bong_tangent` at denoise 0.2**; decode through the **Wan 2.1 FP32 VAE**.
3. **Detailers** — FaceDetailer-class passes; the character-LoRA swap happens here, not in the base gen (`references/characters.md`).
4. **Tiled upscale** — `UltimateSDUpscale` at low denoise with a simplified prompt [community — lonecatone23's ladder].
5. **Repair inpaint** — Krea 2's characteristic trouble zones (hair strands, fine repeating patterns, halftone-prone areas) inpaint cleanly with **Z-Image at denoise ~0.2** [community — nsfwVariant]. Decode to pixels first — Qwen-Image VAE latents and Z-Image latents are different families.

**Krea 2's roles in mixed-model pipelines:** the *aesthetics/composition front-end* (broad visual range, strong wide-aspect composition, anatomy, animals) with **Z-Image as its finishing partner** (facial expressiveness, hair; ~8× slower per image) — this pairing is already the community standard, with LoRA authors shipping paired Krea-2 + Z-Image-Turbo versions of the same style [community — Civitai "Realistic Snapshot"]. The handoff rule is the suite's usual one: **VAE-decode to pixels between model families**; identity-preserving refines live at denoise ~0.2–0.5. Cross-model craft in depth: the **`image-production-workflows`** skill.

---

## LoRA training & characters (summary — full treatment in references)

**The official doctrine is unusually explicit: "TRAIN on Raw and RUN on Turbo"** [official — GitHub FAQ, caps theirs]. LoRAs trained on Raw are designed to express strongly on Turbo. Supported trainers: diffusers, Ostris AI-Toolkit, fal's hosted `krea-2-trainer`, and kohya's musubi-tuner (community-tier, day-0 experimental support). The authors' recommended default is **rank/alpha 32, all-Linear targeting, LR 1e-4** with flow-shift ~2.5 at 1024px [official-via-musubi docs]. Hardware reality from named runs: musubi trains styles on a **12 GB** card (fp8 + block swap, ~2 h for ~1,200 steps) [community — urabewe]; AI-Toolkit *Raw* training OOMs on a 24 GB card until layer offloading is set (~10%), while the Turbo+adapter path fits the same card without fuss [community — Fast-Cash1522].

**The live dispute:** Ostris ships a **de-distillation training adapter** (`ostris/krea2_turbo_training_adapter`) enabling training *directly on Turbo* — and suggests it "could yield better results" for short runs. Official/kohya doctrine says Raw-first. Both paths now have multiple named end-to-end successes (JahJedi's Raw-path character recipe; Any_Tea_3499's AI-Toolkit LoKr character recipes; urabewe's Raw-path style LoRAs; style-training results on Turbo) — the doctrine question is live, but "either path works" is now the evidenced baseline. Hyperparameters, captioning doctrine, and the dispute: **`references/lora-training.md`**.

**Characters:** no PuLID, InstantID, or IP-Adapter port exists for Krea 2, and the character LoRA is still the production path — but the LoRA ecosystem matured fast: named authors now report trained-character likeness *at or above* Z-Image's, from ~50-image datasets and 2–3k steps on AI-Toolkit [community — Any_Tea_3499, r/StableDiffusion]. The no-training layer is arriving too: a community **identity-preserving instruction-edit LoRA** (`conradlocke/krea2-identity-edit`, needs its own `ComfyUI-Krea2Edit` node pack), Ostris's 3-reference edit node + edit-LoRAs, and a pure-prompt "description-locked character sheet" technique. Full protocol, tools, and failure modes: **`references/characters.md`**.

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| Soft, blurry, airbrushed output | Deliberate no-over-sharpen tuning + Qwen-Image VAE character | Texture words in prompt; **Wan 2.1 VAE swap**; detailer pass (see *two taxes*) |
| Neutral/smiling faces only, damped emotion | Safety tuning mutes expressiveness (3 named sources) | Bypass LoRA / Rebalance nodes / undercooked first stage; or hand the face to Z-Image |
| Renders as 3D/digital art when you wanted a photo | Mild render-bias in the aesthetic prior | Explicit photographic framing: camera body + lens + film stock, "photograph" early in prompt |
| Halftone/grid/moiré artefacts, patchy noise in dark areas, fabric/ribbon degradation | Qwen-Image VAE grain behaviour in high-frequency and low-luminance zones — reported to persist sometimes even on the Wan VAE, especially on community checkpoint merges | FP32 Wan VAE; change resolution or step count; inpaint the zone with Z-Image at ~0.2 denoise; on a merge, re-test against the stock fp8 checkpoint before blaming settings |
| Prompt refused or moralised by the workflow itself | Stock template's LLM prompt-enhancer, not the image model | Toggle `prompt_enhance` off; write the prompt yourself or swap the enhancer |
| Negatives ignored (Turbo) | Guidance off — template routes negatives through `ConditioningZeroOut`; distillation removed the CFG path | Phrase constraints positively; cfg 2.0 restores weak negatives at 2× cost (community workaround) |
| Blurry output on Raw with no CFG | Undistilled model — CFG-off is blurry by design | Use cfg 3.5-class guidance on Raw, or just use Turbo |
| Garbled text in image | Text rendering is genuinely weak ("some text appears but not reliably") | Straight quotes around the exact words; keep it short; generate candidates and select — or use `ideogram-4` |
| Degradation at extreme aspect ratios | Trained range is 1–2K at sane ratios | Stay near the preset ratios; outpaint to extremes instead |
| Numbers behave differently in diffusers vs ComfyUI vs musubi | Two CFG baselines: Krea convention (0 = off) vs classic (1 = off) | Convert: official guidance g ≙ classic g+1 ≙ ComfyUI cfg g+1 |

---

## Pre-flight checklist

1. Prompt enhancer toggled **off** (or deliberately on and you know why)?
2. Descriptive sentence(s), front-loaded, no quality-tag chains?
3. Style carried by controls (style LoRA + trigger phrase / style refs / moodboard) rather than vague style words?
4. Photoreal: camera body + lens + film stock named, plus one texture anchor (pores, grain, imperfections)?
5. Turbo: 8 steps, ComfyUI cfg **1.0** (never 0.0 in a KSampler), constraints phrased positively?
6. Raw: only being used for training — or, for inference, with guidance ~3.5 and ideally the Turbo-LoRA recipe?
7. Guidance number converted for the surface you're on (diffusers 0 = ComfyUI 1)?
8. Resolution within 1–2K (Turbo) / 1K (Raw), sane aspect ratio, multiples of 16?
9. Text to render in straight quotes, short?
10. LoRA trained on Raw, applied on Turbo, strength ~0.8–1.0 (style) / ~0.8 (character)?
11. Commercial use: company revenue under $1M, or an enterprise licence in hand? Content filtering in place if you're deploying?

---

## Where Krea 2 sits in the suite

Choose the model for the job — defaults like realism direction and prompting dialect are model-specific, not universal:

| Job | Krea 2 | Reach for instead |
|---|---|---|
| Aesthetic range / stylistic exploration | **The suite's widest visual space** — style refs, moodboards, official style LoRAs, no house look | — |
| Photoreal faces & expressions | Workable with the two-tax fixes; expressions are the weak point | `z-image` — better facial expressiveness and hair (at ~8× the per-image cost); the standard finishing partner |
| Anatomy, animals, wide-aspect composition | Reported strengths vs Z-Image [community — nsfwVariant] | — |
| Consistent characters | Character LoRA (maturing fast — likeness reported ≥ Z-Image by named trainers); community identity-edit LoRA days old | `flux-2` for proven no-training multi-reference identity (ReferenceLatent, PuLID) |
| Style LoRAs | Strong and exploding: official line + 1,500+ community style LoRAs (ilker/fal) + explicit train-Raw/run-Turbo doctrine | `sdxl` for the deepest *mature* trained-LoRA ecosystem |
| In-image typography | Weak — unreliable text rendering | `ideogram-4` — the typography leader |
| Structural control (pose/depth/canny) | First community **depth** ControlNet just landed (Tanmay Patil); no pose/canny/union yet | `sdxl` (mature stack) or `z-image` (Fun Union ControlNet) |
| Commercial local use | Community License: free under $1M revenue | `flux-2` [klein] 4B or `sdxl` for unrestricted-revenue Apache/OpenRAIL paths |
| Mixed-model pipelines | Aesthetics/composition front-end; Z-Image inpaints its artefact zones | `image-production-workflows` for the cross-model craft |

---

## Licence & limitations

| Asset | Licence | Commercial use |
|---|---|---|
| Inference code (`github.com/krea-ai/krea-2`) | Apache 2.0 | Yes |
| **Raw / Turbo weights** | **Krea 2 Community License** | **Yes, if company-wide annual revenue < $1,000,000** — above that, enterprise licence required (opensource@krea.ai) *before* any commercial use |
| Outputs | You own them — "Krea claims no ownership of Outputs" | Yes (subject to licence compliance) |
| Medium / Large | hosted-only, no weights | per Krea's terms of service |

Additional Community License obligations (from the agreement text): deployers must "implement reasonable and appropriate Content Filter measures" (open-source classifiers, commercial APIs, or manual review all qualify); redistribution requires shipping the agreement, prefixing derivative model names with "Krea", and an attribution notice. The revenue gate covers "you (including all affiliated entities under common ownership or control)". A "50-seat" free tier circulates in secondary coverage but is **not** in the agreement text — treat the $1M revenue test as the operative gate and read `LICENSE.pdf` if you're near any edge.

**Known limitations:** no *official* edit/img2img model yet (announced as coming — community edit LoRAs exist but are experimental); structural control is one days-old community depth ControlNet; no identity adapters (a community identity-edit LoRA is the nearest thing); text rendering unreliable; API resolution capped at 1K for now; Raw is 1K-native.

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** Architecture (12B single-stream MMDiT, 28 blocks, GQA 48Q/12KV, Qwen3-VL 4B with the 12-layer tap, Qwen-Image VAE — hosted Large on the FLUX.2 VAE), the Community License terms, exact filenames and sizes (Comfy-Org repo listing), node names and the CLIPLoader `krea2` type, the stock template numbers (8 / cfg 1.0 / euler / simple, `ConditioningZeroOut`), the two guidance conventions and their conversion, the diffusers classes and scheduler config, API slugs and pricing. **Source of truth is official** — the template JSON, HF cards and repo listings, the GitHub README/docs, the licence agreement, diffusers docs — and they were read verbatim there (2026-07-07). These are also the **volatile** ones: this model's open weights are ~2 weeks old. Quant filenames, GGUF repos, template details (the enhancer default has an open issue against it), diffusers install path (currently source-only), API pricing and the 1K cap, and the "edit models coming" status will all move — **re-verify before relying on them, regardless of who said it.**

**Craft — what actually makes a good image.** The two-tax fixes (Wan 2.1 VAE swap, texture anchors, bypass/Rebalance), the two-stage Raw+Turbo-LoRA recipe and its exact numbers, sampler alternatives at low and high step counts, the cfg 2.0 negatives workaround, GGUF placement by VRAM, the Z-Image pairing, LoRA recipes and strengths. **The authoritative source here is the community** — named, reproducible authors (nsfwVariant, liutyi, RaymondLuxuryYacht, lonecatone23, amida168, JahJedi, Any_Tea_3499, urabewe, nova452, mobiuscog, aurelm) who ran the generations — not the model card. Sources span Civitai, HN, GitHub, and Reddit (r/StableDiffusion and r/comfyui read directly on 2026-07-07). It's stated with confidence, but this ecosystem is **two weeks old and moving daily** — the 24 hours before this revision alone produced an identity-edit LoRA, a depth ControlNet, and new character-LoRA recipes. Several items are still explicitly "no consensus yet" (per-quant quality, seed behaviour, hosted-vs-open shootouts, any Flux.2 comparison). Ranges mean "tune this," not "distrust this."

Contested points worth holding in your head:
- **LoRA training doctrine:** official/kohya say train-on-Raw-run-on-Turbo; Ostris ships a turbo-adapter path and suggests it may be better for short runs. Named successes now exist on *both* paths — the "which is better" question stays open, the "does either work" question is settled — `references/lora-training.md`.
- **Raw as an inference model:** "WAY better" with the Turbo-LoRA recipe vs "more airbrushed than Turbo" plain — the recipes differ, the verdicts differ, no consensus.
- **int8 convrot:** the ~2× speedup is replicated; "equal quality" vs "loses complex-prompt adherence" is disputed between named users — A/B on your own prompts.
- **The softness itself:** defect (community members blaming the VAE) or feature (Krea: deliberate anti-AI-look)? Both are partly right — the Wan-VAE swap resolves the defect reading without giving up the tuning.

**Release:** announced 12 May 2026; open weights 22 June 2026; facts verified 7 July 2026.

---

## Reference files

| File | When to read it |
|---|---|
| `references/prompting-guide.md` | Full prompt anatomy for the Qwen3-VL encoder; official example prompts (both registers); realism/texture vocabulary; text rendering; the style-LoRA trigger-phrase table; the expander system prompt and when to use it; creativity-dial behaviour |
| `references/setup-and-workflows.md` | ComfyUI template walkthrough (subgraph, switches, enhancer); full quant/GGUF tables and VRAM placement; the CLI; memory-constrained inference (24 GB memory model, offloading); **using** LoRAs; the two-stage Raw+Turbo-LoRA recipe and detailer ladder in full; Wan 2.1 VAE swap; the Z-Image handoff |
| `references/lora-training.md` | **Making** a LoRA (using is setup-and-workflows): the train-on-Raw/run-on-Turbo doctrine and the contested Ostris turbo-adapter path; musubi-tuner full commands and hyperparameters (rank/alpha 32, LR 1e-4, flow-shift 2.5 / `krea2_shift`, fp8 + block-swap, turbo_dit sampling); AI-Toolkit and fal trainer; character vs style captioning; JahJedi's character recipe end-to-end |
| `references/characters.md` | Consistent characters honestly: the character-LoRA path (dataset factory, 8-point rotation protocol, detailer deployment); identity-adapter status (none — and the nearest tools: Ostris edit node, Conditioning-Rebalance); multi-character limits; failure modes; when to route to `flux-2` instead |
| `references/api-and-hosted.md` | Krea API (endpoints, params, aspect ratios, pricing, async pattern); web app (style references, moodboards, creativity); fal endpoints and trainer; ComfyUI partner nodes; hosted-vs-open architecture differences (the FLUX.2-VAE Large) |
