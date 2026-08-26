---
name: anima
description: >
  Authoritative guide for Anima (CircleStone Labs, funded and distributed by Comfy Org) — the 2B open-weights anime image model built on NVIDIA's Cosmos-Predict2 lineage, covering Anima-Base, Anima-Aesthetic and Anima-Turbo in ComfyUI and diffusers. **The licence is not the shape most people assume: generated images are commercially free for anyone — the card states the non-commercial restriction "applies only to the Model, and not to Outputs" — while the weights are non-commercial, and even the individual carve-out for selling weights extends "solely to the model weights, and not to any larger product."** Use this whenever the user touches Anima in any way, even obliquely: choosing between Base, Aesthetic and Turbo (or weighing Anima against Illustrious, NoobAI, Pony or Z-Image), installing it in ComfyUI (`anima-base-v1.0.safetensors`, `qwen_3_06b_base.safetensors`, `qwen_image_vae.safetensors`, UNETLoader/CLIPLoader/VAELoader, `euler`/`simple`), writing or fixing prompts (Anima has a Qwen3-0.6B LLM encoder but prompts in Danbooru tags — tag order, `score_*` and `masterpiece` ladders, `safe`/`nsfw`/`explicit` rating tags, `year 2025` tags, the mandatory `@` artist prefix, weights pushed far past SDXL norms, `(chibi:2)`, natural-language mode), picking steps/CFG/sampler/scheduler/resolution, image conditioning (Anima-LLLite via `ModelPatchLoader`/`AnimaLLLiteApply`, Cosmos-Reference, the ReStyler trick), training a LoRA (sd-scripts, diffusion-pipe, ~6 GB VRAM, the do-not-train-the-LLM-adapter rule), consistent characters and adult/NSFW work via rating tags, mixed-model pipelines and stills feeding image-to-video, licensing, or debugging artefacts (fried hi-res chains, seed instability, weak artist styles). Use this for any question about Anima in any context; it also covers who should reach for something else instead.
---

# Anima

Anima is CircleStone Labs' open-weights **anime and illustration** model, *"created via a collaboration between CircleStone Labs and Comfy Org"* `[official]`. It is a **flow-matching DiT** with **~2B parameters**, built from **NVIDIA's Cosmos-Predict2-2B-Text2Image** — `CosmosTransformer3DModel` in CircleStone's own diffusers repo, `class Anima(MiniTrainDIT)` in ComfyUI core, with the transformer alone at 1.96B in bf16. A **Qwen3-0.6B *base*** text encoder feeds it, routed through a dedicated **LLM adapter**, and the **Qwen-Image VAE** decodes the output. It trained on Danbooru-style tags, natural-language captions and hybrids of the two; knowledge cut-off is **September 2025**; the resolution band is **512²–1536²**. Weights landed **14 May 2026** (announced 15 May) after a January 2026 preview line. Two licences apply: **CircleStone Labs Non-Commercial License v1.2**, plus **NVIDIA Open Model License** terms inherited from the Cosmos derivation. Both bind you, but **generated images are carved out of both**. Comfy Org's contribution is reported as a ~$1M open-model grant plus day-one ComfyUI support `[community — Civitai 26217, HF disc. 185]`.

**The defining trait: Anima has an LLM text encoder but prompts like a booru model.** You write Danbooru tags in a trained order, add `score_7`/`masterpiece` quality ladders, `safe`/`explicit` rating tokens, an `@artist` prefix, and ComfyUI attention weighting — the whole SDXL-anime dialect — but a small LLM drives it instead of dual CLIP. That combination is not supposed to exist (see *The one rule*). It is why a reader arriving from Illustrious feels at home, while one arriving from Z-Image writes prompts that quietly under-perform. The second defining fact is a stated non-goal: **"The model doesn't do realism well. This is intended."** Anima is a companion to the suite's photoreal models, not a competitor.

---

## Variant selector

| Variant | What it is | Steps · CFG | Quality tags | Use when… |
|---|---|---|---|---|
| **Anima-Base** v1.0 (`anima-base-v1.0.safetensors`) | The pretrained, unrefined base. *"Maximum flexibility, diversity, and style adherence"* — default style deliberately *"very plain and neutral"* | 30–50 · **4–5** | Yes | you want full stylistic range, you are stacking artist tags or LoRAs, and **always when training a LoRA** |
| **Anima-Aesthetic** v1.0 / v1.0b / **v1.1** | Finetuned *"for better consistency and a higher quality default art style"*; its captions had quality tags stripped. v1.1 shipped 2026-07-13 and the card still does not document it | 30–50 · no vendor figure — start at 4 | **No — omit both quality ladders** | you want a good-looking image without curating artist tags |
| **Anima-Turbo** (`anima-turbo-v1.0.safetensors`) | Guidance-distilled. *"Increases stability and gives the model a strong default style, but reduces diversity"* | **8–12 · CFG 1** | unstated; treat as Base | fast iteration, drafting, and — per the authors — as the default starting point `[contested]` |
| **Anima Turbo LoRA** | Turbo's distillation as a LoRA, droppable onto any checkpoint | 8–12 · CFG 1 | follow the host | Turbo speed on a checkpoint you already like |
| **Anima-2.9B / Anima-3.8B** | Community layer-expanded forks — **not CircleStone releases**, experimental, own nodes | — | — | not for production; see *Licence & limitations* |

> **The Turbo-vs-Aesthetic default is contested** `[contested]`. CircleStone recommend Turbo — *"only slightly worse than Anima-Aesthetic, while being very fast to generate"* — but `u/Time-Teaching1926` reports its *"quality, styles, stability and even sometimes prompt Adherence isn't that great."* Test both before you commit a pipeline to one.
>
> **A community checkpoint already out-downloads the official base** — MiaoMiao Harem, ~199k against ~190k `[community — Civitai API, 2026-08-22]`. Treat Anima the way this suite treats SDXL: the base is the training substrate, and most people generate on a finetune instead. Roster: [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §11.

---

## The one rule that changes everything

**Prompt Anima in weighted Danbooru tags, in its trained tag order, with an `@` in front of every artist — and push the weights far past what SDXL taught you.** The card's worked example is `(chibi:2)`, and it says in as many words that a term *"needs a weight higher than typically used for SDXL."* `[official]` That is not folklore. It follows from how weighting is wired (below). A reader carrying SDXL's 1.05–1.3 habit will under-weight every emphasis they write and wrongly conclude that Anima ignores weighting.

| Don't (prose) | Don't (SDXL weights) | Do (Anima booru dialect) |
|---|---|---|
| *A young woman in a santa costume smiling at the camera.* | `1girl, (chibi:1.2), smile, artist_name` | `masterpiece, best quality, score_7, safe, 1girl, oomuro sakurako, yuru yuri, @nnn yryr, (chibi:2), smile, santa costume, white background` |

Three mechanics follow. Each fails silently — you get the wrong output, never an error:

1. **The `@` prefix is mandatory on artist tags.** *"You must put @ in front of the artist. The effect will be very weak if you don't."* Omit it and the style degrades to near-nothing while the image still looks fine.
2. **Tag order is trained, not decorative.** `[quality/meta/year/safety] [1girl/1boy/1other] [character] [series] [artist] [general tags]`. Order *within* a section is free.
3. **Quality tags are per-variant.** Aesthetic had them stripped from its captions — feed them back and you push it *"too hard into slop territory."* Drop **both** ladders there, not just `score_*`.

### Why the suite's encoder rule does not predict this model

The doctrine elsewhere in this suite maps LLM/T5 encoder → sentences, no attention weighting ([`z-image`](../z-image/), [`flux-2`](../flux-2/), [`krea-2`](../krea-2/)); CLIP → weighted tags in 77 tokens ([`sdxl`](../sdxl/)). One suite model already sits outside that map — [`ideogram-4`](../ideogram-4/) has a Qwen3-VL encoder and takes neither register, only a JSON schema — and the suite has filed that as a quirk of one model. **Anima has an LLM encoder and behaves like the CLIP column anyway**, which makes it a pattern rather than a quirk. Three checks, each independently verifiable:

- **The encoder is genuinely an LLM.** `qwen_3_06b_base.safetensors` is Qwen3-0.6B *base* — the diffusers repo declares `Qwen3Model`, hidden 1024, 28 layers, no LM head. Its output does not go straight into cross-attention. It passes through a dedicated **LLM adapter** (`LLMAdapter` in ComfyUI core, `AnimaTextConditioner` in the diffusers repo) that CircleStone warn finetuners not to train, because it *"has an outsized influence on the generated images."* `[official]`
- **The dialect is genuinely booru.** *"The model is trained on Danbooru-style tags, natural language captions, and combinations of tags and captions."* `[official]` Tags are the trained-for register, score ladders and rating tokens included.
- **Weighting is documented *and* implemented** — mechanism below.

**The right conclusion is not "Anima breaks the rule" but "the rule was conflating two things."** Encoder class sets the ceiling on what a dialect *can* express. The **caption corpus** sets what the model is actually fluent in. Across most of this suite the two arrived together — the LLM encoders came attached to prose-captioned training sets — so the doctrine never had to separate them. They have now come apart twice, in opposite directions. [`ideogram-4`](../ideogram-4/) was first: an LLM-class encoder trained *"exclusively on structured JSON captions"* `[official]`, which is why its prompt is a schema and not a sentence. Anima is second: an LLM-class encoder trained on Danbooru tags, which is why its prompt is a weighted tag list. Two models, two non-prose dialects, one cause: the corpus, not the encoder. **Check the caption corpus before you infer a dialect from an encoder name.**

**How weighting is wired, and why the numbers must be bigger.** ComfyUI's `AnimaTokenizer` tokenises the prompt **twice**: once with Qwen3, once with a **T5-XXL tokenizer**. It then forces the Qwen token weights to `1.0`, so a `(term:2)` emphasis rides entirely on the **T5 token stream**, which the adapter consumes — `out = self.llm_adapter(text_embeds, text_ids)`, then `out = out * t5xxl_weights`. CircleStone ship the same design: a `t5_tokenizer/` folder and `"target_vocab_size": 32128`, the T5 vocabulary, on the adapter config. So an Anima weight is a **flat multiplicative scale on post-adapter conditioning embeddings**, where a CLIP weight is an *interpolation toward the mean*. A flat scale shifts conditioning less per unit, which is exactly why the card asks for weights above SDXL's. And note what this is *not*: **no T5 weights are loaded anywhere**, only T5 token ids and their multipliers. There is one text encoder, and it is Qwen3-0.6B.

This has two consequences. There is no 77-token cliff, so 40-term tag lists behave and a sentence can sit inside one. And a real ceiling comes from the encoder being *small* (`u/Time-Teaching1926`: *"small Qwen3 0.6b text encoder does have noticeable limits"*).

Full dialect, vocabularies, worked prompts and the natural-language mode: **[`references/prompting-guide.md`](references/prompting-guide.md)**.

---

## Setup & ecosystem

Anima runs in **ComfyUI core**, with official templates. Like the suite's other DiT models, it is **not a single checkpoint**: three files, three nodes.

### File layout

| File | ComfyUI folder | Loader node |
|---|---|---|
| `anima-base-v1.0.safetensors` (**4.18 GB**) · `anima-aesthetic-v1.0` / `-v1.0b` / `-v1.1.safetensors` · `anima-turbo-v1.0.safetensors` · any community checkpoint | `models/diffusion_models/` | `UNETLoader` (Load Diffusion Model) |
| `qwen_3_06b_base.safetensors` (text encoder, **shared across variants**) | `models/text_encoders/` | `CLIPLoader`, type `stable_diffusion` |
| `qwen_image_vae.safetensors` (VAE, **shared**) | `models/vae/` | `VAELoader` |
| Anima LoRAs, incl. the Turbo LoRA | `models/loras/` | `LoraLoader` |
| Anima-LLLite control models | `models/model_patches/` | `ModelPatchLoader` → `AnimaLLLiteApply` — **both ComfyUI core** |

`[official-via-docs]` — the model card, `docs.comfy.org/tutorials/image/anima/anima`, and the stock `image_anima_base_v1` template.

> **`CLIPLoader`'s `type` does not matter.** The stock template sets `stable_diffusion` and there is no `anima` entry. ComfyUI routes by *detected encoder* (`TEModel.QWEN3_06B`), not by the dropdown.

### Stock node settings

**Verbatim from the stock `image_anima_base_v1` template: 30 steps, CFG 4, sampler `euler`, scheduler `simple`, 1024×1024** `[official]`. That is the runnable default, and it also answers "which scheduler" — **`simple`**.

- **Sampler.** The template ships `euler`; the card's prose default is **`er_sde`** — *"neutral style, flat colors, sharp lines."* Either is correct. The four named samplers are style choices, not quality tiers ([`references/setup-and-workflows.md`](references/setup-and-workflows.md) §3).
- **`beta57` is not stock.** The authors recommend it for a painterly look — *"it puts more emphasis on low-noise timesteps"* — but it ships in the **RES4LYF** pack (`ComfyUI-RES4LYF`, via ComfyUI Manager) and will not appear in the dropdown until you install it.
- **Resolution: 512²–1536²**, multiples of 16 (the band is the card's; the multiple-of-16 rule comes from the trainers).
- **CFG `1` is guidance-off.** Never type `0.0` into a KSampler. It outputs the unconditional and ignores the prompt.

### Quantisation & VRAM

CircleStone publish no inference VRAM figure. At **4.18 GB** plus a 0.6B encoder and the VAE, Anima runs when nothing else will. It is reportedly the only model that loads at all on an 8 GB RX6600, at 8–15 min per 1024²/30-step image. Treat **8 GB as a floor, 12 GB as comfortable**, and re-verify: that floor rests on one report on one AMD card `[flagged — re-verify]`. Detail and the quantisation caveat: [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §5.

### diffusers

`circlestone-labs/Anima-Base-v1.0-Diffusers` declares **`AnimaModularPipeline`** with `AnimaAutoBlocks` and `"_diffusers_version": "0.39.0.dev0"` — a dev build, not a release. (`AnimaImagePipeline` is **DiffSynth-Studio's** class, not diffusers'.) Default is 1024×1024.

Node-by-node graph, LoRA loading and stacking, the community-checkpoint roster, and the image-conditioning stack: [`references/setup-and-workflows.md`](references/setup-and-workflows.md).

---

## Per-variant settings

### Anima-Base (undistilled)

- **Steps 30–50 · CFG 4–5 · sampler `euler` (template) or `er_sde` (card) · scheduler `simple` · 512²–1536²**, multiples of 16. The stock template's exact point is **30 / 4 / `euler` / `simple` / 1024×1024**. 1024-area buckets are the safe centre, and native 1536² is a real advantage over SDXL-anime.
- **Negatives:** live. Baseline `worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration`.
- **Quality tags:** use them — positive prefix `masterpiece, best quality, score_7, safe`.
- **Seed behaviour:** unstable, see below. **LoRA:** the variant LoRAs are trained on, and the safest to run them on.

### Anima-Aesthetic

- **Steps 30–50 · sampler `euler` · scheduler `simple` · same resolution band.** **CFG: CircleStone publish no figure for Aesthetic** — start at Base's 4 and try lower; the card only says it *"can tolerate lower CFGs."*
- **Quality tags: omit both ladders, positive and negative.** Its captions had quality tags stripped, so `masterpiece`/`best quality` *and* `score_*` land out of distribution and push it *"too hard into slop territory."*

### Anima-Turbo (guidance-distilled)

- **Steps 8–12 · CFG 1 · sampler `euler` · scheduler `simple` · same 512²–1536² band** — guidance-off.
- **Negatives are inert.** Phrase constraints as positive tags — including the rating tag, the one case where Anima hands you a positive lever for something a negative would otherwise cover.
- **Seed behaviour:** more stable than Base and less diverse — that trade is the point of the distillation. **As a LoRA:** the Turbo LoRA gives the same profile on any checkpoint; drop to CFG 1 and 8–12 steps when you load it.

---

## The neutral base and the artist-tag lever

Base Anima's default look is *"very plain and neutral"* by design — the inverse of [`z-image`](../z-image/)'s stock-photo gloss. Instead of fighting a house style, you must **supply** one. Three levers, in order of impact:

1. **Artist tags with the `@` prefix.** This is the deepest vocabulary and the real differentiator: ThetaCursed's **Style Explorer** indexes **42k+ artist styles for Anima Base** against 16k+ for Illustrious/NoobAI `[community — ThetaCursed]`. Stack two or three to blend, and weight them (`(@artist:1.6)`) rather than repeating them.
2. **Quality and year tags.** The `masterpiece … worst quality` and PonyV7-derived `score_9 … score_1` ladders are **two independent systems, usable alone, together or not at all**. Year tags (`year 2025`, `newest`, `old`) form a separate, unusually strong style axis — `u/RevolutionaryWater31`: *"the year tags — this has very strong influence on the generated image."*
3. **Sampler choice.** `er_sde` gives flat colour and sharp lines; `euler_a` softens toward 2.5D; `beta57` (RES4LYF) adds painterly texture. On an illustration model this is a style control, not a quality knob.

What does *not* work: `raytracing`, `4k`, `8k` — `u/RevolutionaryWater31`, *"these has never done anything and will just poison your output."* Photographic vocabulary doesn't work either; realism is out of scope by design.

---

## Seeds are not equal

This is the most-repeated practitioner observation about Anima, and it changes your workflow rather than your prompt. `u/arthan1011`: *"Not all seeds are equal — some seeds will ruin the generation while others will work perfectly. **Anima has this instability.**"* So when output comes out broken, **re-roll three or four seeds before you touch the prompt.** Tuning against a bad seed is how people conclude the model cannot do something it does perfectly two seeds later.

---

## Image conditioning and editing — three mechanisms, none finished

Because Anima is a **Cosmos-Predict2 derivative**, it inherits Cosmos's reference-conditioning path rather than the ControlNet/IP-Adapter stack an SDXL user expects. That same inheritance brings the second licence. Three routes exist, and all are incomplete. This is the least settled and highest-value area of the model.

| Route | Status |
|---|---|
| **Anima-LLLite** — kohya-ss's control family, repackaged at `Comfy-Org/Anima-LLLite`, **native in ComfyUI core** (`ModelPatchLoader` → `AnimaLLLiteApply`, files in `models/model_patches/`), with official templates for any-control, depth and inpainting | The usable route. Published weights: `lineart`, `depth`, `pose`, `scribble`, `inpainting-v1/v2`, `any-test-like-1/v2` — **no canny or HED weights exist.** Pose is the weak one; kohya's docs call it *"noticeably weaker control than the others"* |
| **Cosmos-Reference + the Anima Edit LoRA** | Character transfer, but *"too rigid… changing a pose is almost impossible — feels like ControlNet Lineart"* `[community — u/arthan1011]` |
| **IP-Adapter** — two community repos | Both incomplete; one ships no safetensors `[community — u/Internal_Answer_6866, u/Big_CokeBelly]` |

**The craft rule to carry out of this section: run `anima-lllite-exp-change-2` at 0.15–0.3, not 1.0.** At full weight it only edits facial expressions — what everyone assumed it was for. At 0.15–0.3 it relocates subjects, changes clothing, turns characters around and adds a second character `[community — u/_BreakingGood_, u/tpinho9; convergent]`.

> **It is not shipped yet** `[pending release]`. Both halves are open, unmerged **drafts** — `kohya-ss/sd-scripts` **PR #2413** (model) and `kohya-ss/ComfyUI-Anima-LLLite` **PR #10**, branch `feat-v3-semantic-trunk` (node) — and kohya's status is *"merging into main is not decided yet."* The weight lives at **`kohya-ss/Anima-LLLite`**, *not* the Comfy-Org repackage.

Full wiring, kohya's architecture description, the split-screen **ReStyler** pose workaround, and the IP-Adapter status table: [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §8.

---

## Production pipelines & mixing models

**Anima's ladder is shorter than SDXL's on purpose** — native 1536² removes the first two rungs. But it has one trap that costs people afternoons: **generate at target size, then run at most *one* hires pass at denoise ~0.3–0.45.** `u/AssistanceSouth9359` reports that chaining two KSamplers with hi-res fixes on both sides leaves the image *"fried (weird, soft black spots all over the image)"* — each pass re-noises an already-denoised latent, and a 2B backbone compounds the artefacts. Detailer and tiled-upscale stages follow as usual; per-stage settings are in [`references/setup-and-workflows.md`](references/setup-and-workflows.md) §9.

**Mixed-model roles.** Anima composes with the suite's photoreal models rather than competing:

- **Illustrious front-end → Anima refine** — compose with an SDXL-anime checkpoint for its control stack, img2img through Anima at low denoise, then FaceDetailer `[community — u/Alekite]`.
- **Anima → photoreal enhance** — `u/BitterAd8431` lifts Anima stills through **Flux Klein 9B**; [`krea-2`](../krea-2/) and [`z-image`](../z-image/) fill the same refiner slot.
- **Anima → image-to-video**, its biggest role outside still work: three practitioners name Anima as the **character-still generator for the suite's video models** and feed it into [`minimax-h3`](../minimax-h3/) `[community — u/irmemon225, u/Ok-Wolverine-5020, u/AzuliarTHP]`. The documented trap: high-res stills lose face quality at the first video frame. `u/WearNatural5992`'s fix is to **feed a 16:9 input with the short side at 768 px, render at the same aspect ratio**, then run FaceDetailer after.

Across every family boundary: **VAE-decode to pixels.** Anima's Qwen-Image latents are not interchangeable with SDXL's or Flux's. Cross-model craft: [`image-production-workflows`](../image-production-workflows/).

---

## Failure modes & QC

| Symptom | Cause | Fix |
|---|---|---|
| Artist style barely registers | The artist tag was written without `@`, so it tokenises as an ordinary general tag instead of hitting the trained artist vocabulary. The image still renders, so nothing errors | Prefix every artist with `@`; weight it `(@artist:1.6)` if still weak |
| Weighted terms seem to do nothing | Weights are a flat multiplicative scale on post-adapter embeddings, not CLIP's interpolation toward the mean, so SDXL's 1.05–1.3 barely moves the conditioning | Start at 1.5 and step by 0.25; Anima tolerates `(at night:2.0)` without breaking |
| Aesthetic output looks over-cooked, "sloppy" | Quality tags were fed to Aesthetic, whose captions had them stripped; the tokens land as an out-of-distribution style push | Drop **both** ladders (`masterpiece`/`best quality` *and* `score_*`) from positive and negative |
| One generation is mangled, the next is perfect on the same prompt | Seed instability — some seeds simply collapse on this backbone | Re-roll 3–4 seeds before editing the prompt; Turbo is more stable |
| Image "fried" — soft black blotches after upscaling | Two chained KSamplers each re-noise an already-denoised latent; a 2B backbone compounds the artefacts instead of resolving them | One hires pass at denoise ≤0.45, or generate natively up to 1536² |
| Unwanted NSFW content on a short prompt | Rating is a *trained conditioning axis*; with no rating token, the model samples the whole distribution | `safe` in the positive, `nsfw, explicit` in the negative; lengthen the prompt |
| A named character comes out generic | September 2025 cut-off, or the character was never in the tag vocabulary | Check the Animedex/tag browser; name the character **and describe them**; or train a LoRA |
| Multiple characters blend into each other | No regional conditioning — every tag is a global signal the model must attribute | Name *and* describe each; expect a ceiling at ~2 and inpaint the rest |
| **Anima itself got worse after you trained a LoRA** — unrelated prompts, artists and characters all degrade | The trainer was left free to update the **LLM adapter**, which sits between the encoder and the backbone and carries much of the model's tag knowledge. Your twenty images rewrote its understanding of *every* prompt, and no error is raised | Set `llm_adapter_lr=0` (diffusion-pipe) or the sd-scripts equivalent and retrain — see [`references/lora-training.md`](references/lora-training.md) §1 |
| Generation time creeps from ~20 s to over a minute after 20–30 images (AMD) | Unresolved memory accumulation; whether the cause is Anima or ROCm is not established `[flagged — re-verify]` | Add a VRAM-management node; a full restart clears it `[community — u/Greyblades2, u/Alekite]` |

---

## Pre-flight checklist

1. Right variant for the job — **Base** for LoRA training and stylistic range, **Aesthetic** for a good default look, **Turbo** for speed?
2. Prompt in **tag order** (`[quality/meta/year/safety] [count] [character] [series] [artist] [general]`), lowercase, spaces not underscores — score tags excepted?
3. Every artist tag prefixed with **`@`**?
4. Weights at **Anima scale** — start 1.5, step 0.25 — not SDXL's 1.05–1.3?
5. Quality tags matched to the variant — both ladders on Base/Turbo, **neither** on Aesthetic?
6. A **rating tag** in the positive (`safe` / `sensitive` / `nsfw` / `explicit`), and its opposite in the negative where negatives work?
7. CFG matched to the variant — **4–5** Base, start at 4 on Aesthetic, **1** on Turbo with negatives treated as inert?
8. Sampler and scheduler set — **`euler` / `simple`** is the stock pair; resolution inside **512²–1536²** and a multiple of 16; `beta57` only if RES4LYF is installed?
9. Natural-language prompt at least **two sentences**, with characters named *and* described?
10. Bad output? Tried three more **seeds** before rewriting the prompt?
11. **Training a LoRA?** `llm_adapter_lr=0` (or your trainer's equivalent) set *before* the first run?
12. Selling something? **Images are commercially free for anyone**; shipping the *weights* inside a product is not — see *Licence & limitations*.

---

## Where Anima sits in the suite

| Job | Anima | Reach for instead |
|---|---|---|
| Consistent characters | **Knowledge-first** — thousands known by tag; identity transfer by reference is immature ([`references/characters.md`](references/characters.md)) | [`sdxl`](../sdxl/) for identity adapters; [`flux-2`](../flux-2/) for no-training multi-reference identity |
| Style / character LoRA ecosystem | **Large and growing fast** — a 100-item most-downloaded Civitai sample (2026-08-22) held 53 LoRAs and 41 checkpoints; training from ~6 GB VRAM | [`sdxl`](../sdxl/) for settled recipes and the largest absolute pool; [`character-lora-training`](../character-lora-training/) for what transfers |
| In-image typography | Weak — single words, short phrases | [`ideogram-4`](../ideogram-4/) |
| Structural control (pose / depth / lineart) | Anima-LLLite covers lineart, depth, scribble and inpainting; **pose is the weak one, and there is no canny or HED** | [`sdxl`](../sdxl/) — union ControlNet, IP-Adapter, regional prompting, all mature |
| Anime and illustration — the headline axis | **This is what it is for** — the strongest open anime model with a modern encoder | [`sdxl`](../sdxl/) if you need Illustrious/NoobAI/Pony-specific LoRAs or ControlNets |
| Photoreal | Explicitly out of scope — *"doesn't do realism well. This is intended."* | [`z-image`](../z-image/), [`krea-2`](../krea-2/), [`flux-2`](../flux-2/) |
| Commercial use under the licence | **Split, and the split is the whole story: images yes, model no.** Anyone may sell Anima's *output images*, including as paid-product assets. Nobody may host the weights behind a paid API or ship them inside a monetised product. Only individuals may sell *weights* | **Selling images? Stay here.** Only *embedding or serving the model* pushes you to [`sdxl`](../sdxl/)'s anime finetunes or [`z-image`](../z-image/) (Apache-2.0) |
| Mixed-model pipelines | Compose in Anima, refine in a photoreal model; Illustrious→Anima low-denoise refine is a live community pattern | [`image-production-workflows`](../image-production-workflows/) for the craft; [`comfyui-on-runpod`](../comfyui-on-runpod/) for rented GPUs |
| Making it move | Stills only — but Anima is the **default anime character-still generator** feeding image-to-video | [`minimax-h3`](../minimax-h3/) and [`wan-2-2`](../wan-2-2/); lock the still here, mind the 16:9 / 768 px handoff |
| **Choosing between all of these in the first place** | — this table is one model's view of the suite | [`generative-media-atlas`](../generative-media-atlas/) — the whole suite ranked by job (realism, identity, LoRA trainability, control, licence, video), the elimination ladder that settles most choices, and end-to-end routes across several skills |

**Anima vs an SDXL anime finetune vs Z-Image, in one paragraph.** Selling *images*? Anima is fine — that is the licence's explicit carve-out, and the suite's older "Anima loses on commercial grounds" shorthand is simply wrong. Shipping *the model* — an API, a plugin, a game bundling weights? Use an Illustrious/NoobAI/Pony finetune under [`sdxl`](../sdxl/), which also keeps the deepest ControlNet and identity stack. Otherwise Anima wins on prompt comprehension, artist vocabulary, native 1536² and cheap training, and the community reads it as Illustrious's successor (`u/Massive-One-3543`: *"most people use Anima — just as they used Illustrious before that, and Pony prior to that"*). [`z-image`](../z-image/) is not in this contest. It is a photoreal-leaning, sentence-prompted generalist, so booru anime fights both its dialect and its aesthetic.


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

## Licence & limitations

**Two licences apply at once.** The Cosmos derivation that shapes the tooling also drags a second licence along.

1. **CircleStone Labs Non-Commercial License v1.2** — the Model is usable *"solely for your Non-Commercial Purposes"*, where commercial means *"(a) for revenue-generating activity, (b) in direct interactions with or that has impact on third-party end users, or (c) to train, fine tune, or distill other models for commercial use."*
2. **NVIDIA Open Model License Agreement**, inherited — Anima *"constitutes a 'Derivative Model' of Cosmos-Predict2-2B-Text2Image, and therefore is subject to the NVIDIA Open Model License Agreement insofar as it applies to Derivative Models."*

**The part almost everyone gets wrong: the outputs are not restricted at all.** The card, verbatim: *"Note that the non-commercial restriction applies only to the Model, and not to Outputs (the generated images). **You may use generated images commercially.**"* `[official]` The licence agrees in its own definitions — §1(a): *"For the avoidance of doubt, Outputs are not considered Derivatives under this License"* — and grants it in §2(e): *"You may use Outputs for any purpose (including for commercial purposes)."* **This applies to anyone, company or individual.** The card's allowed list includes selling images, paid commissions, and *"generating images to use as concept art or assets for a paid product (e.g. video game or visual novel)."*

**What is restricted is the model itself.** §2(c) is a narrow carve-out — *"Persons operating in an individual capacity may sell Derivatives owned or created by them"* — with its own limit: *"This right to sell Derivatives extends solely to the model weights, and not to any larger product, tool, or feature which incorporates the Model."* `[official]` "Derivative" there means modified weights, LoRAs and textual inversions (§1(a)). It does **not** mean images.

**Disallowed without a separate licence**, from the card's list: hosting the model behind a paid API; hosting it on a paid image-generation platform; embedding the weights in a monetised game or product; powering a feature of a larger monetised product. The last two bind individuals too — §2(c) does not rescue them. Licensing: `tdrussell@circlestone.ai`.

**Content terms.** §4(a) bars generating *"unlawful content, including child sexual abuse material, or non-consensual intimate images."* It also bars use — load-bearing for character work — that infringes *"any third party's legal rights, including rights of publicity or 'digital replica' rights."* `[official]` Real-person likeness is therefore constrained by **this licence as well as** platform rules and law; [`character-lora-training`](../character-lora-training/) owns the practical gate. There is no general adult-content prohibition beyond that, which fits `safe`/`sensitive`/`nsfw`/`explicit` shipping as trained rating tokens rather than a refusal layer.

**Vendor-stated limitations** `[official]`: no realism (*"This is intended"*); weak text (*"single words and sometimes short phrases"*); a deliberately plain base style; and *"the model may generate undesired content, especially if the prompt is short or lacking details."*

**Community forks are covered by none of this.** **Anima-2.9B** and **Anima-3.8B** are layer-expanded community experiments, not CircleStone releases. Whether Anima LoRAs load on them is unanswered `[flagged — re-verify]`, their authors caveat them as experimental, and reception is sceptical (`u/x11iyu`, `u/LaPapaVerde`). Treat them as a footnote until one survives a few months.

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** These include the flow-matching DiT architecture and its Cosmos-Predict2-2B derivation; the ~2B parameter count; the Qwen3-0.6B *base* encoder, the LLM adapter and the T5-tokenised weight channel; the Qwen-Image VAE; the base-path filenames and the 4.18 GB checkpoint size; the loaders (`UNETLoader`, `CLIPLoader`, `VAELoader`, and `ModelPatchLoader` → `AnimaLLLiteApply`); the stock template's 30 / CFG 4 / `euler` / `simple` / 1024²; the 512²–1536² band; the tag-order grammar and the `@` prefix; and the licence split between Outputs and Model. **Source of truth is official** — the model card and `LICENSE.md`, the `Anima-Base-v1.0-Diffusers` configs, the `image_anima_base_v1` template JSON, and ComfyUI core (`comfy/text_encoders/anima.py`, `comfy/ldm/anima/model.py`, `comfy_extras/nodes_model_patch.py`). A wrong filename 404s; a wrong loader won't wire; a misread licence is a legal problem. This ecosystem moves weekly, so **re-verify before relying on these, regardless of who said it.**

**Craft — what actually makes a good image.** This covers weight magnitudes and the response threshold; per-sampler style character; artist-tag stacking and the year-tag lever; seed-rerolling as the first response to a bad generation; the single-hires-pass rule; the LLLite 0.15–0.3 edit trick; LoRA hyperparameters and the ~6 GB floor; and the Illustrious→Anima refine and the 16:9/768 px still-to-video handoff. **The authoritative source here is the community** — `u/arthan1011` (Cosmos-Reference, ReStyler), `u/_BreakingGood_` and `u/tpinho9` (LLLite weights), `u/RevolutionaryWater31` (tag craft, training), `u/AssistanceSouth9359` (hi-res chains), `u/WearNatural5992` (video handoff), ThetaCursed (Style Explorer), citronlegacy and Hysocs (trainers), and the Civitai checkpoint authors — *not* the model card, which ships one example and moves on. Ranges mean your checkpoint and resolution differ from theirs, not that the claim is soft.

**Contested and unresolved, carried deliberately:**

- **Turbo vs Aesthetic as the default** — vendor recommends Turbo verbatim, a named practitioner disputes its quality and adherence `[contested]`.
- **Character-LoRA difficulty** — the card says *"a light touch is all you need"*; `u/justbob9` reports 100+ hours across two trainers without a usable result `[contested]`.
- **`anima-lllite-exp-change-2` is not released** — both PRs open, draft and unmerged, with kohya's *"merging into main is not decided yet"* `[pending release]`.
- **The 8 GB inference floor** rests on one report on one AMD card; CircleStone publish no VRAM figure `[flagged — re-verify]`.
- **AMD memory creep** — two reports, cause unattributed between Anima and ROCm `[flagged — re-verify]`.
- **Whether Anima LoRAs load on the 2.9B/3.8B forks** — asked and unanswered `[flagged — re-verify]`.
- **Aesthetic's CFG** — no vendor figure exists anywhere; the guidance here is extrapolated from Base.
- Volatile items carrying their own markers in the references: Civitai download counts, the Style Explorer URLs, Civitai's SFW-filtered API, and OneTrainer/AI-Toolkit support.

**Settled since drafting, and deliberately no longer flagged:** the architecture (flow-matching DiT); the 2B count (the "2.9B" in circulation is the community fork); the T5-XXL component (real, vendor-shipped, and the weighting mechanism); the `CLIPLoader` `type` (irrelevant); the diffusers class; and `exp-change-2`'s architecture, which is kohya's own words.

**Facts dated 2026-08-22**. The fastest-moving parts are the community checkpoint and LoRA ecosystem, the Anima-LLLite control models and their unmerged PRs, the trainer tooling, and the 2.9B/3.8B fork line. Re-verify all of those before relying on them.

---

## Reference files

| File | When to read it |
|---|---|
| [`references/prompting-guide.md`](references/prompting-guide.md) | Writing or fixing an Anima prompt: the tag grammar and slot order, both quality ladders, rating/year/meta vocabularies, the `@` artist system and style stacking, weight calibration, natural-language mode, the ye-pop dataset-tag mode, per-variant differences, negatives, scheduled prompts, common mistakes, worked prompts |
| [`references/setup-and-workflows.md`](references/setup-and-workflows.md) | Building the graph: node-by-node wiring, sampler tables, resolution/VRAM, diffusers, the community-checkpoint roster, **using and stacking LoRAs**, the image-conditioning stack (LLLite nodes and weights, Cosmos-Reference, the ReStyler trick, IP-Adapter status), the multi-stage ladder, mixed-model and still-to-video handoffs |
| [`references/lora-training.md`](references/lora-training.md) | **Making** a LoRA (loading one is setup-and-workflows §7): trainers, **the do-not-train-the-LLM-adapter rule and how to disable it per trainer**, attributed hyperparameters, the ~6 GB floor, dataset architecture and tag captioning, style LoRAs, adult/NSFW training, assessing fit, debugging |
| [`references/characters.md`](references/characters.md) | Holding a character across images: why identity here is knowledge-first, checking whether a character is baked in, when to escalate to a LoRA, the image-conditioning routes and their limits, multi-character ceilings, adult work via rating tags, failure modes, handing a locked still to the video models |
