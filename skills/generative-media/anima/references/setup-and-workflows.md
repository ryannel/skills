# Anima — Setup & Workflows

This file owns the machinery. It covers the ComfyUI graph, sampler settings, resolution and VRAM, diffusers, the community checkpoint ecosystem, **loading and stacking LoRAs**, the image-conditioning stack, the production ladder, and handoffs to other models. If you want to **make** a LoRA, read [`lora-training.md`](lora-training.md). If you want to write the prompt, read [`prompting-guide.md`](prompting-guide.md).

## Contents

1. File layout and the three-node load
2. Stock settings, verbatim from the template
3. Samplers and schedulers — style, not just quality
4. Resolution and aspect
5. VRAM, quantisation and slow hardware
6. diffusers
7. Using and stacking LoRAs
8. Image conditioning and editing
9. The multi-stage ladder
10. Mixed-model handoffs, including still-to-video
11. Community checkpoints and where the ecosystem actually is
12. Runners other than ComfyUI

---

## 1. File layout and the three-node load

Anima is native in ComfyUI core. It has official templates and needs no custom nodes for text-to-image. Like the suite's other DiT models, it is **not a bundled checkpoint**. It needs three files and three loaders `[official-via-docs]`:

| File | ComfyUI folder | Loader node |
|---|---|---|
| `anima-base-v1.0.safetensors` (**4.18 GB**) · `anima-aesthetic-v1.0.safetensors` / `-v1.0b` / `-v1.1` · `anima-turbo-v1.0.safetensors` · community checkpoints · the superseded `anima-preview3-base.safetensors` | `models/diffusion_models/` | `UNETLoader` |
| `qwen_3_06b_base.safetensors` (Qwen3-0.6B *base* encoder, **shared**) | `models/text_encoders/` | `CLIPLoader`, type `stable_diffusion` |
| `qwen_image_vae.safetensors` (Qwen-Image VAE, **shared**) | `models/vae/` | `VAELoader` |
| LoRAs, including the Anima Turbo LoRA | `models/loras/` | `LoraLoader` |
| Anima-LLLite control models | `models/model_patches/` | `ModelPatchLoader` → `AnimaLLLiteApply` |

The encoder and VAE are common to every variant and every community checkpoint, so you only download them once.

**Graph shape** (from the stock `image_anima_base_v1` template): `UNETLoader` → (`LoraLoader`…) → `KSampler`; `CLIPLoader` → two `CLIPTextEncode` nodes → `KSampler`; `EmptyLatentImage` → `KSampler` → `VAEDecode` (fed by `VAELoader`) → `SaveImage`. The stock graph has no sampling-shift node. Shift lives in the model config instead, as `shift: 3.0` on the flow-matching scheduler.

**Version dates**, from the repo commit log: base v1.0 shipped **2026-05-14**; Turbo and the Turbo LoRA around **2026-07-08**; Aesthetic v1.0b on **2026-07-09**; Aesthetic **v1.1 on 2026-07-13**, and v1.1 is still undocumented in the card.

---

## 2. Stock settings, verbatim from the template

**The stock `image_anima_base_v1` template ships: 30 steps, CFG 4, sampler `euler`, scheduler `simple`, 1024×1024, `EmptyLatentImage`** `[official]`. Start there.

> **`CLIPLoader`'s `type` is `stable_diffusion` and it does not matter.** There is no `anima` entry in the list. ComfyUI does not route Anima by the dropdown at all. Instead, `comfy/sd.py` dispatches on the *detected* encoder (`elif te_model == TEModel.QWEN3_06B: … comfy.text_encoders.anima.te(...)`). Set it to anything. The correct encoder stack is wired regardless.

| | Base | Aesthetic | Turbo |
|---|---|---|---|
| Steps | 30–50 (template 30) | 30–50 | **8–12** |
| CFG | **4–5** (template 4) | no vendor figure — start at 4 | **1** |
| Sampler · scheduler | `euler` (template) or `er_sde` (card) · `simple` | same | `euler` · `simple` |
| Negatives | live | live | inert |
| Latent node | `EmptyLatentImage` | same | same |

The card gives *"30-50 steps, CFG 4-5"* for Base. **Nothing official gives Aesthetic a CFG.** The card's Aesthetic section covers quality tags only. It says Aesthetic *"can tolerate lower CFGs"* without naming one.

**CFG 1 means guidance is off.** That is the same convention as every distilled model in this suite. Never type `0.0` into a ComfyUI KSampler, because that outputs the unconditional and ignores your prompt entirely.

---

## 3. Samplers and schedulers — style, not just quality

Anima's authors characterise their own samplers. On an illustration model, these read as **style controls** rather than quality/speed trade-offs:

| Sampler | Character (authors' words) | Reach for it when |
|---|---|---|
| `er_sde` | *"neutral style, flat colors, sharp lines. I use this as a reasonable default."* | cel-shaded and clean-line work |
| `euler_a` | *"Softer, thinner lines… CFG can be pushed a bit higher than other samplers without burning the image."* | softer rendering; more CFG headroom |
| `dpmpp_2m_sde_gpu` | *"similar in style to er_sde but can produce more variety and be more 'creative'… can get too wild sometimes."* | exploration, when the prompt over-converges |
| `euler` | *"a bit more creative than er_sde. Good with the Turbo and Aesthetic versions."* | the template default; Turbo and Aesthetic |

**Scheduler.** `simple` is the stock template's setting, and that is the default to use. The authors call out one non-stock option: *"If going for a more realistic / painterly look, the **beta57** scheduler (ComfyUI RES4LYF custom node pack) can help make better textures, since it puts more emphasis on low-noise timesteps."* That makes it the closest thing Anima has to a texture knob. It will not appear in the scheduler dropdown until you install `ComfyUI-RES4LYF`, either through ComfyUI Manager or by cloning it into `custom_nodes/`.

---

## 4. Resolution and aspect

- **The trained band is 512²–1536²** `[official]`, with dimensions in **multiples of 16**. The multiples-of-16 constraint comes from the trainers and DiffSynth, not from the card.
- **1024-area buckets are the safe centre.** They behave like SDXL's: 1024×1024, 832×1216, 1216×832, 768×1344.
- **Native 1536² is a real capability, not an upscale.** That is a concrete advantage over SDXL-anime, where 1024-area is the ceiling before duplication artefacts appear. Prefer generating large over generating small and climbing (§9). Outside the band, expect duplicated subjects and stretched anatomy above it, and mush below it.

---

## 5. VRAM, quantisation and slow hardware

**No official inference VRAM number exists** `[flagged — re-verify]`. Here is what the evidence supports:

- **8 GB is a working floor, and 12 GB is comfortable.** That claim rests on one report on one AMD card `[flagged — re-verify]`. `u/Dependent_Quit_3730`, on an 8 GB RX6600 with 16 GB RAM, says Anima is the only model that loads at all. The cost is speed. `u/Bokayoteamo`, on the same GPU via ROCm, reports: *"1024x1024 30 steps takes around 8-15 mins."*
- **The base checkpoint is 4.18 GB** (4,182,218,328 bytes). That is a 1.96B transformer plus the ~0.13B adapter at bf16, which independently corroborates the 2B figure.
- **Quantisation.** `silveroxides/Anima-Quantized` is often cited, but it is largely preview2-era *resized turbo-distill LoRAs* rather than a quantisation of Base v1.0 `[community — re-verify]`. At 4.18 GB, most people never need a quantisation.
- **AMD memory creep** `[flagged — re-verify]`. Two independent reports back this up. `u/Greyblades2` saw generation time climb from ~20 s to over a minute after 20–30 images, cleared only by a full restart. `u/Alekite`, on an R9700 32 GB, saw VRAM and RAM exhaustion on an Illustrious→Anima refine chain that had no VRAM-management node. The cause is not pinned down between Anima and ROCm. On AMD, put a VRAM-cleanup node in the graph before concluding the model is broken.

Renting a GPU is rarely necessary here. If you do rent one, [`comfyui-on-runpod`](../../comfyui-on-runpod/) owns that job.

---

## 6. diffusers

- The repackage is **`circlestone-labs/Anima-Base-v1.0-Diffusers`**. Its `modular_model_index.json` declares `"_class_name": "AnimaModularPipeline"`, `"_blocks_class_name": "AnimaAutoBlocks"` and `"_diffusers_version": "0.39.0.dev0"`. That is **a dev build, not a released diffusers**. The default is 1024×1024, with dimensions in multiples of 16.
- **`AnimaImagePipeline` is DiffSynth-Studio's class, not diffusers'.** If you copied that name from a ModelScope page, it will not import from `diffusers`.
- **The repo ships a `t5_tokenizer/` folder, and it is not a mistake.** `modular_model_index.json` registers it as `["transformers", "T5Tokenizer"]`, and the adapter config carries `"target_vocab_size": 32128`, which is the T5 vocabulary. **No T5 encoder weights are loaded anywhere.** The T5 tokenizer exists only to carry prompt-weight multipliers into the LLM adapter. See SKILL.md's *one rule* for why this mechanism is what lets Anima take higher prompt weights than SDXL.

**Components**, from the same index: transformer `CosmosTransformer3DModel`; encoder `Qwen3Model`; conditioner `AnimaTextConditioner` (6 layers, 16 heads, `model_dim` 1024, ~269 MB); VAE `AutoencoderKLQwenImage` (`z_dim: 16`); scheduler `FlowMatchEulerDiscreteScheduler`, `shift: 3.0`.

---

## 7. Using and stacking LoRAs

*Making* a LoRA is covered in [`lora-training.md`](lora-training.md). This section is about loading and running them.

- **Node:** use a standard `LoraLoader` on the model path between `UNETLoader` and the sampler. Anima LoRAs are ordinary safetensors LoRAs.
- **There is no cross-compatibility with SDXL, Illustrious, NoobAI or Pony LoRAs.** The architecture, latent space and encoder are all different. An SDXL LoRA either fails to load or no-ops, and there is no conversion path. This is the most common false expectation that Illustrious migrants carry over.
- **Train on Base, run anywhere.** The card says *"LoRAs should be trained using this version"* `[official]`. Base-trained LoRAs then run on Aesthetic, Turbo and most community checkpoints, usually with strength reduced by ~0.1–0.3, because those checkpoints already carry a style of their own `[community — convergent practice]`.
- **Whether Anima LoRAs load on the 2.9B/3.8B forks is unanswered** `[flagged — re-verify]`. `u/Neonsea1234` asked and got no reply. Assume they do not, since the forks add extra layers.
- **The Turbo LoRA** (`circlestone_labs`, ~60k downloads) applies Turbo's distillation to any checkpoint. Switch to **CFG 1, 8–12 steps** when you load it. A community `RDBT Distilled Turbo LoRA` and a 12-step variant also exist `[community — u/TheBizarreCommunity]`.
- **Utility LoRAs are a real part of this ecosystem.** `Aesthetic Quality Modifiers - Masterpiece` (motimalu, ~153k downloads) is the second-most-downloaded Anima asset of any kind. `Anima Highres/Aesthetic Boost` and `Anima Detail Tweaker` (lse14) are widely stacked too `[community — Civitai API, 2026-08-22]`.
- **Stacking:** chain `LoraLoader` nodes, or use rgthree's power loader. Style LoRAs compound fast on a base that already has a style. Reduce each LoRA's strength as you add more.

---

## 8. Image conditioning and editing

Anima inherits **Cosmos-Predict2's reference-conditioning path**. That is why its editing tooling looks nothing like SDXL's. Three routes exist, and none of them is finished.

### (a) Anima-LLLite — kohya-ss's control family, and the usable route

**Native in ComfyUI core.** No custom node is needed for the released weights; kohya's node is only for the unreleased v3 described below. Weights go in `ComfyUI/models/model_patches/`. They are loaded by **`ModelPatchLoader`** and applied by **`AnimaLLLiteApply`** (inputs `model`, `model_patch`, `image`, `strength`, `start_percent`, `end_percent`, optional `mask`; category `model_patches/anima`).

Weights are repackaged at **`Comfy-Org/Anima-LLLite`**, and **official templates ship in ComfyUI**: `image_anima_lllite_any_control_to_image`, `image_anima_lllite_depth_control_to_image`, `image_anima_lllite_image_inpainting`. `u/Corrupt_file32` calls them *"very stealthy"*, and most people never notice they are there.

**Published control types**: `lineart`, `depth`, `pose`, `scribble` (Preview3-era), `inpainting-v1`/`-v2`, `any-test-like-1`/`-v2`. **There are no canny or HED weights.** The "any control" template uses the any-test-like weights instead. Those were trained on *"Lineart / scribble / grayscale, heavily augmented"*, and in practice they absorb canny-ish and HED-ish inputs.

**Pose is the weak one, and the caveat is kohya's, not CircleStone's.** An official pose weight exists (`anima-lllite-pose-1.safetensors`, DWPose-conditioned, 1,544 pairs). But kohya's `PREVIEW3.md` says *"the pose model in particular has noticeably weaker control than the others"*, and that it is *"best treated as a soft pose prior rather than a strict pose-locking ControlNet."* `u/Zephrinox` reports the same.

**The undocumented expression model, and the craft rule it hides.** kohya-ss shipped `anima-lllite-exp-change-2-000007.safetensors` (77.7 MB) with no README entry. At weight 1.0 it only edits facial expressions. But:

> `u/_BreakingGood_`: *"it can perform any kind of edit by running it at a very low weight (0.2 to 0.3)."*
>
> Independently reproduced by `u/tpinho9`: *"between 0.15 and 0.2 to allow much more changes while preserving the character."*

Users have demonstrated the following at those weights: relocate the subject to a beach, change clothing, turn the character around, add a second character, change the time of day. **Start at 0.2 and sweep 0.15–0.3.** Kohya's usage note is to prompt it *"similar to the one used for standard generation, rather than a short prompt that specifies only the facial expression."*

**Status — not shipped** `[pending release]`. Both halves are open, unmerged **drafts**: `kohya-ss/sd-scripts` **PR #2413** (head `exp-anima-lllite-v3-semantic-trunk`) and `kohya-ss/ComfyUI-Anima-LLLite` **PR #10** (branch `feat-v3-semantic-trunk`). Kohya's own status line: *"merging into main is not decided yet."* **The weight lives at `kohya-ss/Anima-LLLite`, not the Comfy-Org repackage.** To try it, pull the safetensors, check out `feat-v3-semantic-trunk` into `ComfyUI/custom_nodes/`, and expect the node API to change when the PRs land. It is not a production graph yet.

**What it is, in Kohya's own words** (from the PR #2413 body, not a rumour): v3 *"uses frozen DiT hidden states of a reference image as the conditioning source, injected into the trained blocks via a low-rank value path with a multiplicative gate (`--lllite_trunk semantic`)."* Quality is disputed. `u/Grand0rk` writes: *"I see a lot of issues. So not very impressed."* `[contested]`

### (b) Cosmos-Reference + the Anima Edit LoRA

`u/arthan1011` explains it directly: *"What is Cosmos-Reference you ask? It's a custom node that enables image conditioning in Anima — you need special LoRAs for it to work and Anima Edit is one of them."* The node pack is `Mirumo0u0/ComfyUI-Cosmos-Reference`. In its own words, it exists to *"Add an image reference feature to the Cosmos model or models based on it."*

Its limit, verbatim: *"it's too rigid. I can change outfit and replace background but **changing a pose is almost impossible — feels like ControlNet Lineart**."*

**The ReStyler workaround** exists to get around that rigidity. The mechanism is worth understanding rather than copying. Stitch a **solid-colour block** onto the input, so the left half is your character and the right half is blank. **Inpaint**, masking **only the blank area**. Add **`(split screen, multiple views:1.2)`** to the prompt. Then crop the right half. In the author's words: *"`split screen` in prompt makes the model pay attention(!) to the left half of the image, while the Edit LoRA handles Cosmos-Reference image condition to achieve character consistency."* The published workflow does the stitching and cropping for you.

His tips are all worth keeping: *"Perfect input image is a character in the neutral pose at simple background"*; *"This workflow sometimes struggles with monochrome images/sketches — colorize them first"*; *"It's easy to change style but hard to maintain it"*; *"Overall it works 85% of the time"* (seeds matter here — see SKILL.md's seed-instability note); and the honest routing, *"If you want to change pose of your character and keep its style 100% consistent you'd better use Wan 2.2"* — see [`wan-2-2`](../../wan-2-2/).

Note the weight in that prompt. `1.2` is *low* by Anima's own documented norms (`prompting-guide.md` §7). Try 1.5–2.0 if the split-screen effect is not triggering.

### (c) IP-Adapter — two repos, both incomplete

`LuciferTC9527/ComfyUI-Anima_IP-Adapter` is *"clearly still under development, the results aren't good. Without artist tag… the character consistency is bad and art style isn't well transferred"* `[community — u/Internal_Answer_6866]`. `Wenaka2004/comfyui-anima-ipadapter` has *"a lot of missing files and information"*, and no safetensors have been published `[community — u/Big_CokeBelly]`.

**Routing verdict:** for structural control that must be exact, [`sdxl`](../../sdxl/)'s stack is far ahead, so compose there. For identity, Anima's answer is knowledge tags and LoRAs ([`characters.md`](characters.md)).

---

## 9. The multi-stage ladder

Anima's ladder is **shorter than SDXL's on purpose**. Native 1536² removes the reason for the first two rungs, and chaining passes is actively dangerous here.

1. **Base gen.** Generate at target size directly, up to 1536². Judge the composition, and re-roll seeds freely before touching anything else.
2. **One hires pass, optional.** Use a single second sampler at **denoise 0.3–0.45**, or a latent/pixel upscale followed by one re-sample at **0.25–0.35** `[community — suite-wide refine bands]`.
3. **Detailer.** Use FaceDetailer/ADetailer at **~0.4 denoise**, with the prompt matched to the face you want. Swap a character LoRA in **here**, not at the base gen `[community — suite-wide detailer convention]` (see [`characters.md`](characters.md) §3).
4. **Tiled upscale.** Use `UltimateSDUpscale` at **denoise 0.2–0.35** `[community — suite-wide upscale convention]`, with a simplified tag prompt. Drop artist tags and most general tags. A full prompt at tile scale produces per-tile subjects.

> **The trap: do not chain two KSamplers with hi-res fixes on both sides.** `u/AssistanceSouth9359`: *"anima is pretty good at creating close up shots > Halfbody shots > 3/4 body shots but it loses a lot of details or the image gets fried (weird, soft black spots all over the image) when i try to use 2 ksamplers, pre and post hi res fixes."* Nobody in-thread solved it. The mechanism is this: each pass re-noises an already-denoised latent, and a 2B backbone compounds the resulting high-frequency artefacts instead of resolving them, the way a larger model would. **One hires pass, or none.**
>
> A second rule sits in the same quote: detail quality tracks how many pixels the face occupies. Close-up beats half-body, half-body beats ¾-body, and ¾-body beats full-body. A full-body shot with a good face needs a detailer pass.

---

## 10. Mixed-model handoffs, including still-to-video

The hard rule across every family boundary: **VAE-decode to pixels before handing off.** Anima's Qwen-Image latents are not interchangeable with SDXL's or Flux's. Passing latents across produces colour-shifted mush. Cross-model craft lives in [`image-production-workflows`](../../image-production-workflows/).

**Illustrious front-end → Anima refine.** Compose with an SDXL-anime checkpoint for its ControlNet/regional stack, decode, img2img through Anima at **low denoise**, then FaceDetailer `[community — u/Alekite]`. Watch VRAM on AMD (§5).

**Anima → photoreal enhance.** `u/BitterAd8431` runs Anima stills through **Flux Klein 9B**. [`krea-2`](../../krea-2/) and [`z-image`](../../z-image/) fill the same refiner slot. Keep denoise at 0.2–0.35. The anime styling is the first thing you lose above that.

**Anima → image-to-video.** This is Anima's most-used role outside still work, and a repeated production pattern: `u/irmemon225` built a 2:19 music video from 14 × 10 s segments (*"for characters, I generate it using Anima"*); `u/Ok-Wolverine-5020` writes *"I used Anima for text2img, then Minimax H3 ref2v with driving audio for 15s clips"*; `u/AzuliarTHP` writes *"reference Images - Anima / animation clips - minimax H3"*.

> **The documented handoff trap.** A high-resolution Anima still loses noticeable face quality at the first video frame. `u/WearNatural5992`'s fix: *"using an input at 16:9 and make the video at the same aspect ratio and the loss of quality, especially in face is considerably less than in other aspect ratios… I am using the shortest side as 768px."* Then run FaceDetailer (Impact Pack) on the output. So the rule is: **generate the still at 16:9 with the short side ~768 px, match the video's aspect ratio exactly, and restore faces after.**

Video targets in this suite: [`minimax-h3`](../../minimax-h3/), which is the one the Anima community actually names, and [`wan-2-2`](../../wan-2-2/), which is the route `u/arthan1011` recommends when you need a pose change with style held exactly.

---

## 11. Community checkpoints and where the ecosystem actually is

**A community finetune out-downloads the official base.** The ecosystem is repeating what happened to SDXL. A Civitai `baseModels=Anima` most-downloaded **sample of the first 100 items** (2026-08-22) held 53 LoRAs, 41 checkpoints, 5 workflows and 1 VAE `[community — Civitai API]`. That is a composition figure, not a census. The true totals are unknown and larger.

| Model | Type | Downloads | Creator |
|---|---|---|---|
| **MiaoMiao Harem** | Checkpoint | 198,832 | MIAOKA |
| **Anima** (official base) | Checkpoint | 189,872 | circlestone_labs |
| Aesthetic Quality Modifiers - Masterpiece | LoRA | 153,330 | motimalu |
| WAI-ANIMA · AnimaYume · Nova Anime AM · RDBT \| Anima · AnimaIka · Hassaku (Anima) | Checkpoints | 19–71k | WAI0731 · duongve13112002 · Crody · reakaakasky · giko · Ikena |
| AI styles dump · Anima Turbo LoRA · Highres/Aesthetic Boost · Detail Tweaker | LoRAs | 22–66k | bakariso · circlestone_labs · lse14 |

Download counts move daily `[flagged — re-verify]`. The *ranking* is the durable signal. The furry ecosystem has ported (`uwumerge`/`uwustyle Anima Edition`), and cross-model style assets now ship an Anima build alongside Flux, Pony, Illustrious and Z-Image builds. Check for one before assuming you must retrain ([`image-production-workflows`](../../image-production-workflows/)).

**Tag and style discovery** `[community]`: `animastyles.thetacursed.com` (42k+ artist styles — these are mirrors, since ThetaCursed's GitHub was suspended, so the URLs are volatile `[flagged — re-verify]`), `tags.latent.moe` (a Danbooru browser, ~70% populated for Anima), and the Anima "Animedex" character index.

---

## 12. Runners other than ComfyUI

Native support is reported in **Forge-Neo**, **InvokeAI**, **NexusBTA**, **Stimma** and **Mix Studio** `[community]`. Hosted platforms named by the authors are **TensorArt, KusArt, IMGNAI, mage, AliveAI, DreamerLand** and Civitai. Those platforms run it under their own arrangements, and CircleStone's terms still bar *you* from serving the weights for money. Node packs worth having: **`ComfyUI-EasyUseAnima`** (n0va39) for wildcards `[community — u/rogerbacon50]`, **RES4LYF** for `beta57`, and `Mirumo0u0/ComfyUI-Cosmos-Reference` for image conditioning.
