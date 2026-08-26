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
  and AI-Toolkit settings, plus measured 12 GB and 16 GB configs and why you must train at 1024 not 768),
  building a consistent character (the character-LoRA path, the mature Identity Edit LoRA for mask-free
  scene-preserving edits, and Differential Output Preservation for running up to four character LoRAs at
  once without bleed), preparing a first frame for a video character-swap model, choosing a VAE (Wan 2.1 vs
  Qwen Image VAE Sharp/Sharp Plus), multi-stage and mixed-model pipelines (the Raw+Turbo-LoRA two-stage recipe, Z-Image as the inpaint partner), or
  debugging muted facial expressions, halftone/grid artefacts, dark-area noise, weak text rendering, or
  prompts the stock enhancer refuses. Use this for any question about Krea 2 in any context.
---

# Krea 2

Krea 2 (K2) is Krea AI's first from-scratch foundation image model — a **12B-parameter single-stream MMDiT** trained with flow matching. It was announced 12 May 2026, with **open weights (Raw + Turbo) released 22 June 2026**. The text encoder is **Qwen3-VL 4B Instruct**, tapped unusually deeply: hidden states from **twelve decoder layers per token** are fused by a small text-fusion stage. This lets the DiT select coarse-to-fine text representations. The open-weights models decode through the **Qwen-Image VAE** (f8, 16 latent channels). Code is Apache-2.0. Weights are under the **Krea 2 Community License** (commercial use gated on company revenue — see Licence below).

Its defining trait is a deliberate refusal to have a house look. Most models optimise a single polished default. Krea 2 instead "is designed to expose a broad visual space" and be "raw, flexible, unopinionated, and unconstrained". Style is a **control surface**, not a prompt word. References, moodboards, style LoRAs and a creativity dial carry the look, and the prompt carries the content. The flip side is that the default output reads *soft*, and the safety tuning mutes facial expressiveness — confirmed independently by three named community testers. Both have named fixes (see *The anti-AI-look and its two taxes*).

---

## Variant selector

The load-bearing axis is the **role split** — which checkpoint you train on, which you run, and which you rent:

| Variant | Nature | Steps / guidance | Resolution | Access | Use when… |
|---|---|---|---|---|---|
| **Raw** | undistilled base — "not recommended for inference use" `[official — HF card]` | 52 / cfg 3.5 (HF card); 28 / 4.5 (diffusers default) ¹ | 1K native | Open weights (`krea/Krea-2-Raw`) | **LoRA training and fine-tuning base**; the Raw+Turbo-LoRA inference recipe `[community — nsfwVariant]` |
| **Turbo** | 8-step TDM-distilled (guidance + timestep distillation) | 8 / guidance off ² | 1K–2K | Open weights (`krea/Krea-2-Turbo`) + fal + web app | **The local workhorse** — fast, high-quality t2i; where LoRAs trained on Raw get applied |
| **Medium** | hosted-only, "stable, general-purpose" | managed | 1K (API, currently) | krea.ai app + API + fal + ComfyUI partner nodes | Hosted default; style refs + moodboards; $0.030/img |
| **Large** | hosted-only, photorealism flagship — **trained with the FLUX.2 VAE**, not the open models' Qwen VAE ³ | managed | 1K (API, currently) | same | Maximum fidelity, hosted; $0.060/img |

> ¹ Two official numbers coexist. The HF model card and inference CLI say **52 steps / cfg 3.5**. The diffusers pipeline documents the non-distilled ("base/midtrain") checkpoint at **28 steps / guidance 4.5**. Both are official: treat 52/3.5 as the Raw-card recommendation, and 28/4.5 as the diffusers default.
> ² **Guidance-off means different numbers on different surfaces.** On diffusers/CLI it is `guidance_scale=0.0` (Krea's convention: velocity = `cond + g·(cond − uncond)`, so 0 = off, and it equals classic CFG `1 + g`). On the ComfyUI KSampler it is **cfg 1.0** (the classic scale) — the official template ships cfg 1.0 with the negative branch through `ConditioningZeroOut`. musubi-tuner uses the classic scale too, so official "guidance 4.5" becomes `--guidance_scale 5.5` there. Copying a number between surfaces without converting it is the #1 setup error.
> ³ Krea's mattnewton confirmed this on HN: hosted Large trained with the FLUX.2 VAE, while open weights use the Qwen-Image VAE `[official — team statement]`. So hosted output differs from open-weights output at the architecture level, not just the size level.

**Default workflow:** run **Turbo** locally (8 steps, guidance off, 1–2K). Use **Raw** only to train on — its CFG-off output is blurry *by design* (undistilled) `[official — musubi docs]`. Reach for **Medium/Large** when you want the style-reference/moodboard system or the last increment of hosted fidelity. Official edit models are announced but not yet released. The tech report names "robust editing, image reference, and native 2K/4K" as future work, and Krea's CTO says they are "coming" `[pending release]`.

---

## The one rule that changes everything

**Put the content in the prompt and the style in the controls.** Krea's own thesis: "Style should not be a vague prompt word. It should be something you can guide, mix, strengthen, reduce, and push". In practice:

- **The prompt** is parsed by Qwen3-VL, an instruction-following VLM. It reads clause structure and word order like a language model, so write **descriptive natural language**, front-loaded. Booru quality chains (`masterpiece, 8k, best quality`) are noise to it. (This comes from the encoder class, not folklore: the same sentence rule governs FLUX.2's Mistral/Qwen3 and Z-Image's Qwen-3. The *opposite* — weighted tags, rare-token triggers — governs CLIP models like SDXL.) The official prompting guide's examples run both registers — full prose paragraphs *and* dense comma-separated descriptor lists — and both work, because a VLM parses either. What matters is that every token is *descriptive*, not incantational. "Long detailed prompts yield best results, but the model is capable of generating high quality images with minimal prompt engineering".
- **The style** goes through the control surfaces. Locally that means style LoRAs — the official nine plus a community explosion (1,500+ style LoRAs from ilker/fal alone) — with natural-phrase triggers (`monochrome ink wash style` — a describable phrase, not a rare token, exactly what an LLM encoder wants). On the hosted surfaces it means style references (with per-reference strength), moodboards, and the creativity dial (raw → high). Creativity **raw** "renders only explicit descriptions without expansion", and **high** takes "meaningful creative liberty".
- **Text to render goes in straight quotes** — `a neon sign reading "OPEN LATE"` `[official — docs/prompting.md]`.

**The community corollary: turn the stock prompt-enhancer off.** The official ComfyUI template ships an LLM prompt-expansion subgraph *enabled by default*. It refuses benign prompts — "photo of a dog on a kitchen table" gets an ethics lecture instead of an expansion `[community — 808charlie, Comfy-Org/ComfyUI#14631]`. Named workflow authors ship abliterated-Qwen replacements rather than use it `[community — lonecatone23, Civitai]`. Toggle `prompt_enhance` off in the subgraph and write the full prompt yourself, or swap in the API-node enhancer of your choice. If you want LLM expansion offline, Krea publishes the expander's system prompt (`docs/expansion.txt` in the GitHub repo) for use with any LLM.

**But swap the enhancer, not the encoder — the subgraph wires the same LLM to both.** Replace the enhancer with an abliterated ("heretic") Qwen build, and the subgraph quietly applies that swap to the `CLIPTextEncode` path too. Heretic's own author states plainly that an abliterated **text encoder** cannot uncensor a diffusion model. Abliteration removes an LLM's ability to *refuse*, and refusal lives in output layers a text encoder never uses, so all you get is disturbed hidden states and slightly worse prompt adherence `[community — -p-e-w-, author of Heretic]`. Unpack the subgraph, point the abliterated model at the **expander only**, and leave the encoder stock. The quality cost is small either way `[community — afinalsin, XY grids over 8 encoders]` — this is a correctness point. Fuller account: [`minimax-h3`](../minimax-h3/).

Full prompt anatomy, official example prompts, realism vocabulary, and the style-LoRA trigger table: **`references/prompting-guide.md`**.

---

## Setup & ecosystem

Krea 2 runs in **ComfyUI core** — no custom nodes. Update ComfyUI first. The DiT is not a single checkpoint: it loads through three loaders.

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

Note what's *absent*. There is no shift node (`ModelSamplingAuraFlow` is unnecessary, because the resolution-aware time shift lives in the model config), and it uses a plain `EmptyLatentImage`, not an SD3/Flux latent node.

### Quantisation & VRAM

**Size the card against `fp8_scaled` at 13.1 GB** plus the 5.2 GB fp8 encoder — the template default. **Read 16–24 GB as the comfort band, not the floor.** That is the tier where both models sit resident and nothing waits on the PCIe bus. Below it the same files still run. ComfyUI evicts the text encoder once the prompt is encoded, and streams DiT blocks in from system RAM as the sampler walks them. So the binding resource becomes host RAM and bus bandwidth, and the cost is seconds per step rather than quality (the weights are bit-identical either way). **Turbo `fp8_scaled` is reported working on an 8 GB RTX 3070 Ti paired with 64 GB of system RAM** `[community — niechta]`. The 64 GB is not incidental: offload relocates the 13.1 GB, it does not shrink it. Comfy publishes no official thresholds. Community GGUF (Q2_K 4.9 GB → Q8_0 13.7 GB, via the `ComfyUI-GGUF` node, not `UNETLoader`) is the other sub-16 GB route. Prefer it when *system* RAM is what you are short of, because it shrinks the weights instead of shuttling them.

One quant choice is worth making deliberately. **`int8_convrot` is reported ~2× faster than fp8** `[community — nsfwVariant, YeahYeah2992]`, but whether that costs complex-prompt adherence is disputed `[contested]`. It also degrades *silently*, so if a complex prompt falls apart on int8, re-test on fp8 before rewriting the prompt. Full ladder, sizes, GGUF repos and both sides of the dispute: `references/setup-and-workflows.md §2`. Community requants and Civitai **checkpoint merges** (Fascium, MysticXXX-class) inherit none of the stock numbers' guarantees.

### diffusers

```python
from diffusers import Krea2Pipeline  # requires diffusers from source (main) as of early July 2026
pipe = Krea2Pipeline.from_pretrained("krea/Krea-2-Raw", torch_dtype=torch.bfloat16)
image = pipe(prompt, num_inference_steps=52, guidance_scale=3.5).images[0]   # Raw card settings
# Turbo: is_distilled=True in the pipeline config → fixed mu=1.15; num_inference_steps=8, guidance_scale=0.0
```

Classes: `Krea2Pipeline`, `Krea2Transformer2DModel`, `AutoencoderKLQwenImage`, `Qwen3VLModel`. `max_sequence_length=512`, and dimensions round up to ×16. It is **t2i only** — no img2img/inpaint/edit pipeline exists yet. Remember the guidance convention (footnote ² above). Scheduler and shift config in full: `references/setup-and-workflows.md §4`.

### Hosted surfaces

Krea API (`api.krea.ai`, async job pattern): `POST /generate/image/krea/krea-2/medium|large`, 1K-only for now, `creativity` raw/low/medium/high, up to 10 style references with per-ref strength (pricing in the selector table above). fal hosts `fal-ai/krea-2/turbo`, `/turbo/lora` and `fal-ai/krea-2-trainer`. ComfyUI partner nodes expose Medium/Large with moodboard IDs. Endpoints, params, pricing and the hosted-vs-open differences: **`references/api-and-hosted.md`**.

---

## Per-variant settings

### Turbo (the local workhorse)

- **Steps:** 8, and gains past 8 are minimal at 1024 `[community — liutyi]`. Going *down* works too — `res_2s`/`beta` at 4–5 steps buys texture `[community — RaymondLuxuryYacht]`. Above 1024 the economy inverts, and named recipes run longer. The sampler ladders in full: `references/setup-and-workflows.md §7b`.
- **Guidance:** off — ComfyUI cfg **1.0**, diffusers/CLI `guidance_scale=0.0`, `--mu 1.15` pinned. Negatives are inert here (the template zeroes them). **cfg 2.0 re-enables negative prompts** at ~2× generation time `[community — nsfwVariant]` — a workaround, not a supported feature.
- **Sampler/scheduler:** `euler`/`simple` stock. The community recipes above swap samplers freely.
- **Resolution:** 1024–2048 px, multiples of 16. Solid at 1024 and native 2048. Extreme ratios (e.g. 1600×400) degrade `[community — liutyi]`. Cinematic wide ratios within reason are a reported strength `[community — nsfwVariant]`.
- **LoRAs:** `LoraLoaderModelOnly`, official style LoRAs at 0.8–1.0 with their trigger phrases. Character LoRAs trained on Raw commonly hold at ~0.8 `[community — JahJedi]`.

### Raw (the training base)

- **As a base for training:** this is its job — see `references/lora-training.md`.
- **As an inference model:** 52 steps / cfg 3.5 `[official — HF card]` (diffusers default 28/4.5; musubi `--guidance_scale 5.5` ≙ official 4.5). CFG-off output is blurry — expected, undistilled. 1K native: it was not trained for 2K.
- **Raw-as-inference is contested craft.** One named author gets "WAY better" photoreal from **Raw + the official Turbo LoRA (`loras/krea2_turbo_lora_rank_64_bf16.safetensors`) at 0.6** in a two-stage workflow `[community — nsfwVariant]`. Another finds plain Raw *more* airbrushed than Turbo at 30 steps/cfg 4 `[community — amida168, kombitz.com]`. The difference is plausibly the Turbo-LoRA + VAE swap in the first recipe. There is no consensus — if you try Raw for inference, use the full recipe, not plain Raw.

### Medium / Large (hosted)

Managed sampling — you control prompt, aspect ratio, seed, creativity, style refs/moodboards, and the intensity/complexity/movement sliders (−100…100). Large is the photoreal pick and renders through the FLUX.2 VAE. Settings and pricing: `references/api-and-hosted.md`.

---

## The anti-AI-look and its two taxes

Krea 2's signature is the *absence* of the over-sharpened, hyper-saturated "AI look" — a deliberate design goal the team defends when challenged `[official — team statements on HN]`. Two costs ride along, and they are the two most-replicated community findings on this model:

**Tax 1 — the soft/airbrushed default.** Outputs read blurry-soft next to Flux-class models, and skin trends airbrushed. The mechanism is partly the deliberate no-over-sharpening tuning, partly the Qwen-Image VAE's rendering character. Fixes, in escalating order:
1. **Prompt for texture explicitly** — "natural skin texture, visible pores, subtle skin imperfections" `[community — amida168]`. The model also has a mild bias toward 3D-render/digital-art interpretations, so photoreal prompts need explicit photographic framing — camera body, lens, film stock, the same stack that works on every LLM-encoder model.
2. **Swap the VAE** — decode through the **Wan 2.1 VAE** (FP32) instead of `qwen_image_vae`. Multiple named users report it "solves" the softness `[community — mobiuscog (HN), nsfwVariant]`. It is latent-compatible, a drop-in at the `VAELoader`.
3. **Detailer passes** — SAM3 face/eye detailers + tiled upscale in the larger community workflows `[community — lonecatone23]`.

**Tax 2 — muted expressions.** Faces cluster at neutral-or-smile, and emotional range is damped. Three named sources independently attribute this to the safety tuning ("quality dilution") `[community — liutyi, nsfwVariant, nova452]`. Fixes include bypass LoRAs (the line in routine production use is **`krea2filterbypass3`, run at weight 2** `[community — KlitoriaPierce]`, reported to improve strictly-SFW output too) and nova452's `ComfyUI-Conditioning-Rebalance` per-layer conditioning nodes. Another option is a noisier first-stage sampler (the deliberately-undercooked 6-step first stage in the two-stage recipe exists partly for this). That a counter-LoRA at double the usual strength is what it takes is itself diagnostic. A LoRA can only re-expose behaviour the weights already hold, so the expressiveness is *present and damped*, not absent — which is why the fixes above work at all. Full context, including what it is stacked with, is in `references/lora-training.md §2b`. If a specific facial expression is the shot's whole point, consider generating the face with Z-Image and compositing instead — see the suite table below.

---

## LoRA training & characters (summary — full treatment in references)

**The official doctrine is unusually explicit: "TRAIN on Raw and RUN on Turbo"** `[official — GitHub FAQ, caps theirs]`. LoRAs trained on Raw are designed to express strongly on Turbo. Supported trainers: diffusers, Ostris AI-Toolkit, fal's hosted `krea-2-trainer`, and kohya's musubi-tuner (community-tier, day-0 experimental support). The authors' recommended default is **rank/alpha 32, all-Linear targeting, LR 1e-4** with flow-shift ~2.5 at 1024px `[official — musubi docs]`. Hardware reality from named runs: **12 GB is enough** with fp8 + block swap. But AI-Toolkit *Raw* training OOMs even on 24 GB until layer offloading is set to ~10% — a failure that reads like a bug rather than a config gap `[community — urabewe, Fast-Cash1522]`. Measured 12 GB and 16 GB configs: `references/lora-training.md §2a, §2c`.

**The live dispute:** Ostris ships a **de-distillation training adapter** (`ostris/krea2_turbo_training_adapter`) that enables training *directly on Turbo*, and suggests it "could yield better results" for short runs. Official/kohya doctrine says Raw-first. Both paths now have multiple named end-to-end successes (JahJedi's Raw-path character recipe; Any_Tea_3499's AI-Toolkit LoKr character recipes; urabewe's Raw-path style LoRAs; style-training results on Turbo). The doctrine question is live, but "either path works" is now the evidenced baseline. Hyperparameters, captioning doctrine, and the dispute: **`references/lora-training.md`**.

**Characters:** no PuLID, InstantID, or IP-Adapter port exists for Krea 2, and the character LoRA is still the highest-fidelity path. Named authors report trained-character likeness *at or above* Z-Image's, from ~50-image datasets and 2–3k steps on AI-Toolkit `[community — Any_Tea_3499]`. Two things changed over July–August 2026:

- **The identity-edit LoRA grew up.** `conradlocke/krea2-identity-edit` reached **v1.2** and is now the community's default identity tool. It does single-sentence, mask-free, scene-preserving edits (profile turns, outfit swaps, expression changes), and background and lighting stay genuinely unmoved. The counter-intuitive craft rule: **one short sentence beats a paragraph.** It stacks with other LoRAs, and its fastest-growing use is *outside* image work — prepping a first frame for a video character-swap model so the reference already matches the driving clip's pose. It needs the `ComfyUI-Krea2Edit` node pack. Weak axis: posing, which will shift the face.
- **Multiple character LoRAs may now coexist — on one author's evidence.** Train with **Differential Output Preservation** against a class on a LoKr config at 1500 steps, and up to **four** characters reportedly load together with minimal bleed. Five falls apart, and characters borrow features (lips especially), so prompt what distinguishes them. The same author reports the technique **failing on Z-Image Base** — which [`z-image`](../z-image/) records with the same caveat, so it is one report, not two. Test it before you plan a job around the four-character cap `[community — MASilverHammer; single report]`.

Also available: Ostris's 3-reference edit node + edit-LoRAs, and a pure-prompt "description-locked character sheet" technique. Full protocol, tools, and failure modes: **`references/characters.md`**.

---

## Production pipelines & mixing models

Krea 2 generates 1–2K natively, so the ladder starts high:

1. **Base gen** — Turbo, 8 steps, guidance off, 1–2K. Judge composition; reroll seeds freely.
2. **Two-stage refine** — the best-documented local recipe. Compose on **Raw + the official Turbo-LoRA @ 0.6**, deliberately *undercooked* (that is the point: it keeps the expressiveness the safety-tuned polish removes). Finish at **denoise 0.2**, decoding through the **Wan 2.1 FP32 VAE**. Per-stage samplers and steps: `references/setup-and-workflows.md §7a` `[community — nsfwVariant]`.
3. **Detailers** — FaceDetailer-class passes. The character-LoRA swap happens here, not in the base gen (`references/characters.md`).
4. **Tiled upscale** — `UltimateSDUpscale` at low denoise with a simplified prompt `[community — lonecatone23's ladder]`.
5. **Repair inpaint** — Krea 2's characteristic trouble zones (hair strands, fine repeating patterns, halftone-prone areas) inpaint cleanly with **Z-Image at denoise ~0.2** `[community — nsfwVariant]`. Decode to pixels first — Qwen-Image VAE latents and Z-Image latents are different families.

**The VAE decision has three options now, and it is a quality lever, not a formality.** The Wan 2.1 FP32 swap remains the standard answer to the soft default. A third path — the retuned **`Qwen Image VAE Sharp` / `Sharp Plus`** decoders — buys fine-edge response and micro-contrast *without* the Wan swap's colour shift. Reach for it when hair, fabric or architecture need to separate but you liked the stock colour, and keep the stock VAE for painterly work `[community — Merserk13]`. Separately, latent-space colour grading (exposure/temperature/tint/contrast vectors extracted from the Qwen-Image VAE) would let you grade *during* sampling and push into the very dark and very bright frames the model resists. But its ComfyUI node is announced rather than shipped, so today it is a watch-item, not a tool `[community — muerrilla; re-verify]`. All three decodes, with the `--fp32-vae` requirement and when each wins: `references/setup-and-workflows.md §5`.

**Krea 2's role in a mixed-model pipeline is the *aesthetics/composition front-end*** — broad visual range, wide-aspect composition, anatomy, animals. It pairs with **Z-Image as its finishing partner** for faces and hair, at ~8× the per-image cost. The pairing is already standard enough that LoRA authors ship matched Krea-2 and Z-Image-Turbo builds of the same style `[community — Civitai "Realistic Snapshot"]`. Handoff rule, as everywhere in the suite: **VAE-decode to pixels between model families**. Identity-preserving refines live at denoise ~0.2–0.5. Cross-model craft in depth: **[`image-production-workflows`](../image-production-workflows/)**.

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| Soft, blurry, airbrushed output | Deliberate no-over-sharpen tuning + Qwen-Image VAE character | Texture words in prompt; **Wan 2.1 VAE swap**; detailer pass (see *two taxes*) |
| Neutral/smiling faces only, damped emotion | Safety tuning mutes expressiveness (3 named sources) | Bypass LoRA / Rebalance nodes / undercooked first stage; or hand the face to Z-Image |
| Renders as 3D/digital art when you wanted a photo | Mild render-bias in the aesthetic prior | Explicit photographic framing: camera body + lens + film stock, "photograph" early in prompt |
| Halftone/grid/moiré artefacts, patchy noise in dark areas, fabric degradation | Qwen-Image VAE grain behaviour in high-frequency and low-luminance zones — sometimes persists even on the Wan VAE, especially on community merges | FP32 Wan VAE; change resolution or step count; inpaint the zone with Z-Image at ~0.2 denoise; on a merge, re-test the stock fp8 checkpoint first |
| Prompt refused or moralised by the workflow itself | Stock template's LLM prompt-enhancer, not the image model | Toggle `prompt_enhance` off; write the prompt yourself or swap the enhancer |
| Negatives ignored (Turbo) | Guidance off — template routes negatives through `ConditioningZeroOut`; distillation removed the CFG path | Phrase constraints positively; cfg 2.0 restores weak negatives at 2× cost (community workaround) |
| Blurry output on Raw with no CFG | Undistilled model — CFG-off is blurry by design | Use cfg 3.5-class guidance on Raw, or just use Turbo |
| Garbled text in image | Text rendering is genuinely weak ("some text appears but not reliably") | Straight quotes around the exact words; keep it short; generate candidates and select — or use [`ideogram-4`](../ideogram-4/) |
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
| Photoreal faces & expressions | Workable with the two-tax fixes; expressions are the weak point | [`z-image`](../z-image/) — better facial expressiveness and hair (at ~8× the per-image cost); the standard finishing partner |
| Anatomy, animals, wide-aspect composition | Reported strengths vs Z-Image `[community — nsfwVariant]` | — |
| Consistent characters | Character LoRA (likeness reported ≥ Z-Image by named trainers); **Identity Edit LoRA v1.2 is now a mature no-training option** | [`flux-2`](../flux-2/) for proven no-training multi-reference identity (ReferenceLatent, PuLID) |
| **Several named characters in one image** | **The most promising answer in the suite — but it rests on one author's report**: Differential Output Preservation on a LoKr run, up to 4 characters, minimal bleed; the same author found it fails on Z-Image Base ([`references/characters.md`](references/characters.md) §2 carries the caveat) | [`sdxl`](../sdxl/) regional prompting above 4 characters, or if DOP does not replicate for you |
| **Prepping a reference for a video character swap** | **The standard tool** — edit the driving clip's real first frame into your character with Identity Edit; [`scail-2`](../scail-2/) is the model that consumes it | Flux [klein] 9B does the same job — but 9B is FLUX Non-Commercial wherever you run it, and the licence travels with the frame into the finished clip; [klein] 4B is the Apache-2.0 variant ([`flux-2`](../flux-2/)) |
| Style LoRAs | Strong and exploding: official line + 1,500+ community style LoRAs (ilker/fal) + explicit train-Raw/run-Turbo doctrine | [`sdxl`](../sdxl/) for the deepest *mature* trained-LoRA ecosystem |
| Anime / booru illustration | Its stylistic range covers anime *looks*, but not the booru tag vocabulary or the character-by-name knowledge that ecosystem runs on | [`anima`](../anima/) — the anime-native base, which names Krea 2 as one of its photoreal-refine partners, so the pairing runs both ways; [`sdxl`](../sdxl/) for the mature Illustrious/Pony finetunes |
| In-image typography | Weak — unreliable text rendering | [`ideogram-4`](../ideogram-4/) — the typography leader |
| Structural control (pose/depth/canny) | First community **depth** ControlNet just landed (Tanmay Patil); no pose/canny/union yet | [`sdxl`](../sdxl/) (mature stack) or [`z-image`](../z-image/) (Fun Union ControlNet) |
| Commercial local use | Community License: free under $1M revenue | [`z-image`](../z-image/) first — Apache-2.0 on weights *and* outputs, no revenue cap and no gate, the least encumbered licence in the suite; then [`flux-2`](../flux-2/) ([klein] 4B, Apache-2.0) or [`sdxl`](../sdxl/) (OpenRAIL++-M, whose use-restrictions do travel downstream) |
| Mixed-model pipelines | Aesthetics/composition front-end; Z-Image inpaints its artefact zones | [`image-production-workflows`](../image-production-workflows/) for the cross-model craft |
| Making it move | Still images only | [`wan-2-2`](../wan-2-2/) or [`ltx-2-5`](../ltx-2-5/) — image-to-video from a still locked here. The debt runs both ways: the **Wan 2.1 VAE swap** central to this skill's realism craft is borrowed from that family |
| **Choosing between all of these in the first place** | — this table is one model's view of the suite | [`generative-media-atlas`](../generative-media-atlas/) — the whole suite ranked by job (realism, identity, LoRA trainability, control, licence, video), the elimination ladder that settles most choices, and end-to-end routes across several skills |

---

## Licence & limitations

| Asset | Licence | Commercial use |
|---|---|---|
| Inference code (`github.com/krea-ai/krea-2`) | Apache 2.0 | Yes |
| **Raw / Turbo weights** | **Krea 2 Community License** | **Yes, if company-wide annual revenue < $1,000,000** — above that, enterprise licence required (opensource@krea.ai) *before* any commercial use |
| Outputs | You own them — "Krea claims no ownership of Outputs" | Yes (subject to licence compliance) |
| Medium / Large | hosted-only, no weights | per Krea's terms of service |

Three further obligations sit in the agreement text. Deployers must "implement reasonable and appropriate Content Filter measures" (classifiers, commercial APIs or manual review all qualify). Redistribution requires shipping the agreement, prefixing derivative model names with "Krea", and including an attribution notice. And the revenue gate covers "you (including all affiliated entities under common ownership or control)" — group revenue, not the project's. A "50-seat" free tier circulates in secondary coverage but is **not** in the agreement. Treat the $1M test as the operative gate, and read `LICENSE.pdf` near any edge.

**Known limitations:** no *official* edit/img2img model yet `[pending release]` (the community Identity Edit LoRA has become the de-facto answer and is no longer fairly called experimental). Structural control is one community depth ControlNet. No identity adapters exist in the PuLID/InstantID sense. Text rendering is unreliable. API resolution is capped at 1K for now. Raw is 1K-native.

**Krea 3 is being teased** (krea_ai, 2026-08-19) with no announced date, weights policy or capabilities. Nothing in this skill assumes it. Note it before starting anything with a long payback period, such as a large LoRA-training programme. `[pending release]`

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** This covers architecture (12B single-stream MMDiT, 28 blocks, GQA 48Q/12KV, Qwen3-VL 4B with the 12-layer tap, Qwen-Image VAE — hosted Large on the FLUX.2 VAE), the Community License terms, and exact filenames and sizes. It also covers node names and the CLIPLoader `krea2` type, the stock template numbers (8 / cfg 1.0 / euler / simple, `ConditioningZeroOut`), the two guidance conventions and their conversion, the diffusers classes, and API slugs and pricing. **Source of truth is official** — the template JSON, HF cards and repo listings, the GitHub README/docs, the licence agreement, diffusers docs — read verbatim there on 2026-07-07. A wrong filename 404s, and a misread licence is a legal problem, so none of these are worth inferring. The volatile ones are the packaging rather than the architecture: quant filenames, GGUF repos, template defaults (the enhancer default has an open issue against it), the source-only diffusers install path, API pricing and the 1K cap, and the "edit models coming" status. **Re-verify these before relying on them, regardless of who said it.**

**Craft — what actually makes a good image.** This covers the two-tax fixes (Wan 2.1 VAE swap, texture anchors, bypass/Rebalance), the two-stage Raw+Turbo-LoRA recipe and its numbers, and sampler alternatives at low and high step counts. It also covers the cfg 2.0 negatives workaround, GGUF placement by VRAM, the Z-Image pairing, and LoRA recipes and strengths. **The authoritative source here is the community** — named, reproducible authors (nsfwVariant, liutyi, RaymondLuxuryYacht, lonecatone23, amida168, JahJedi, Any_Tea_3499, urabewe, nova452, mobiuscog, MASilverHammer, aurelm, chengyansen-ai) who ran the generations, not the model card — across Civitai, HN, GitHub and Reddit. It is stated with confidence. Ranges mean "your weights, dataset or resolution differ from the author's," not "unreliable." What has shifted since the first draft is the pace. At two months old the base craft has settled, while the tooling layer around it — identity edit, ControlNets, checkpoint merges — still moves weekly. Several items remain "no consensus yet": per-quant quality, seed behaviour, hosted-vs-open shootouts.

Contested points worth holding in your head — each carries its marker, because these are the claims the freshness protocol greps for when they resolve:
- **LoRA training doctrine:** official/kohya say train on Raw and run on Turbo. Ostris ships a turbo-adapter path and suggests it may be better for short runs. Named successes now exist on *both* paths. The "which is better" question stays open, but the "does either work" question is settled `[contested]` — `references/lora-training.md`.
- **Raw as an inference model:** "WAY better" with the Turbo-LoRA recipe vs "more airbrushed than Turbo" plain — the recipes differ, the verdicts differ, no consensus `[contested]`.
- **int8 convrot:** the ~2× speedup is replicated. "Equal quality" vs "loses complex-prompt adherence" is disputed between named users — A/B on your own prompts `[contested]`.
- **The softness itself:** defect (community members blaming the VAE) or feature (Krea: deliberate anti-AI-look)? Both are partly right — the Wan-VAE swap resolves the defect reading without giving up the tuning `[contested]`.
- **Multi-character Differential Output Preservation:** the four-character cap, and the claim that the same technique fails on Z-Image Base, both rest on one author's unreplicated runs `[community — MASilverHammer; single report]`.
- **Training resolution:** a widely-shared 16 GB writeup trained at 768 and was corrected in its own comments. Pretraining spanned 256/512/1024 stages, so **768 was never a trained resolution**. Train at 1024. The 768 figure still circulates in derivative writeups. A community-calibrated AI-Toolkit workflow now buckets 512+768+1024 deliberately as a composition→detail progression — a second voice for the practice, not new evidence against the pretraining stages `[flagged — re-verify]` (`references/lora-training.md §2c`, `§3a`).
- **Timestep schedule on the AI-Toolkit path:** `timestep_type: linear` (named explicitly as *not* Flux's sigmoid) versus the best-replicated LoKr recipe's sigmoid. Two working recipes, opposite settings, no comparison published `[contested]` — `references/lora-training.md §3a`.

**Facts dated 2026-07-07; community craft refreshed 2026-08-22, with the AI-Toolkit training path and the ComfyUI version requirement extended 2026-08-26 from a completed private character run plus a community-calibrated workflow repo** from a sweep of r/StableDiffusion, r/unstable_diffusion and Civitai. What moves fastest is everything wrapped *around* the weights — quant repacks and GGUF, the identity/edit tooling, the template defaults and the API's 1K cap. Re-verify those before the architecture facts. On that sweep Krea 2 was the second-largest base-model tag on Civitai by monthly volume, behind Illustrious. It is no longer a new model — it is the image side's centre of gravity.

---

## Reference files

| File | When to read it |
|---|---|
| `references/prompting-guide.md` | You are writing or debugging a prompt: full anatomy for the Qwen3-VL encoder, official examples in both registers, realism/texture vocabulary, text rendering, the style-LoRA trigger-phrase table, and the expander |
| `references/setup-and-workflows.md` | You are installing, sizing a card, choosing a VAE, **using** LoRAs, or building the multi-stage ladder: the template node by node, the quant/GGUF and VRAM tables, the CLI, the three decode paths, and the mixed-model handoffs |
| `references/lora-training.md` | You are **making** a LoRA (using one is setup-and-workflows): the Raw-vs-Turbo doctrine and its dispute, musubi and AI-Toolkit commands and hyperparameters, measured 12 GB and 16 GB configs, captioning, adult work, and the named character and style recipes |
| `references/characters.md` | A character has to survive more than one image: the LoRA path end to end, Identity Edit craft, the multi-character limits, the video-handoff pipeline, and when to route to [`flux-2`](../flux-2/) instead |
| `references/api-and-hosted.md` | You are renting Medium/Large rather than running Turbo: endpoints, params, pricing, the async pattern, style references and moodboards, fal, and how hosted output differs from open weights |
