# Z-Image Characters — creating a consistent character

How to invent an original character and keep them consistent across poses, outfits, scenes, and multi-character images. This file is the orchestration layer: dataset craft lives here, training mechanics in `lora-training.md`, deployment wiring in `setup-and-workflows.md` (§6 LoRA usage, §10 identity methods).

**The Z-Image reality first:** there is no PuLID, no IP-Adapter face model, and no released edit model for Z-Image (Z-Image-Edit is announced, unreleased). That means **the character LoRA is not one option among several here — it is the path**. The craft below is about making that path excellent. (On models where adapters exist, they trade against LoRAs — see the flux-2 and sdxl skills. That comparison matters when you're choosing a model, not after.)

---

## 1. The two paths (and how they chain)

The 2026 community consensus across model families is two complementary approaches — convergent across Mickmumpitz's workflows, WeirdWonderfulAI's writeups and the Civitai dataset guides `[community — Mickmumpitz, WeirdWonderfulAI; convergent]`:

| Path | What it is | Z-Image status |
|---|---|---|
| **Edit-model character engine** | No training: a character sheet + a multi-reference edit model (Qwen-Image-Edit 2511, FLUX.2 ReferenceLatent) re-renders the character into new scenes directly | Not available *in* Z-Image — no released edit variant. But see the chain below. |
| **Character LoRA pipeline** | Train a LoRA from 20–50 varied images; deploy at the detailer stage | **The Z-Image path.** Fully supported (Ostris AI-Toolkit). |

**The chain — use an edit model as the dataset factory.** The two paths aren't rivals. The strongest current practice *chains* them: design the character once, then use an edit model — typically **Qwen-Image-Edit 2509/2511** in the same ComfyUI install — to multiply that one image into the varied dataset the LoRA needs. The edit model never touches inference. It only manufactures training data, so its own look doesn't contaminate your Z-Image outputs (the LoRA learns the *identity residual*, and your captions name everything else). The canonical writeup is WeirdWonderfulAI's "QWEN Image Edit can create Character Consistent LoRA Dataset" (Oct 2025). Mickmumpitz's Consistent Character Creator v3 is the most-cited turnkey version `[community — WeirdWonderfulAI, Mickmumpitz; strong]`.

---

## 2. Designing the character: the anchor image

Everything starts from **one anchor portrait** that defines the identity envelope. Generate it in Z-Image itself (so the identity is native to the model's distribution):

- Front three-quarter view, neutral expression, plain background, soft north-window light, 50–85 mm, 1024×1024.
- Write the identity with **named, specific, non-idealised features** — "copper shoulder-length hair, sun-freckled olive skin, small mole below the left jaw". These are the markers you'll later *omit* from captions, so the trigger absorbs them.
- Template A in `prompting-guide.md §8` is exactly this shot. Reroll until the face is one you can describe and recognize.

Keep the anchor's **identity description text** — you will reuse it byte-identical in every dataset prompt and (without the LoRA) in base-generation prompts later.

---

## 3. Building the dataset

Target **20–50 images** (15–25 is workable; the marginal value past ~50 is low). The governing rule: **keep the identity consistent, and make everything else deliberately varied** — angle, expression, shot size, outfit, lighting, background. Near-duplicate shots are the #1 cause of same-face overfit `[community — Civitai guides 7777/21257/21114; convergent]`.

Three ways to multiply the anchor, in order of fidelity:

1. **Qwen-Image-Edit factory (best).** Feed the anchor plus ~20–60 edit prompts: the 8-point rotation, expressions, outfits, lighting setups, settings. Generate ~60, then **curate the best ~30**, cutting anything where the face drifted. 2511 (Dec 2025) is the release character-LoRA builders reach for when consistency matters `[community — single report]`. It is not "one version behind": Qwen-Image-2.0 (Feb 2026) is API-only, so 2511 is the newest edit model you can run locally `[official — QwenLM, 2026-08-23]`. Setup below.
2. **Z-Image img2img at low denoise** from the anchor — the original method in `lora-training.md §2`. Works, but drifts identity faster than an edit model at large angle changes.
3. **Pure txt2img with the identity description + locked clauses** — usable for filling specific gaps (a missing back view) when the other two stall; expect retries.

**Factory setup (ComfyUI).** Same install as Z-Image, different loader stack — three files plus an optional speed LoRA, all from `Comfy-Org/Qwen-Image-Edit_ComfyUI` (diffusion) and `Comfy-Org/Qwen-Image_ComfyUI` (encoder + VAE), `split_files/` trees. ComfyUI ≥ 0.6.0 for 2511 `[official — Comfy-Org repos + docs.comfy.org 2511 template, 2026-08-23]`:

| File | Size | Goes in | Loader |
|---|---|---|---|
| `qwen_image_edit_2511_fp8mixed.safetensors` (or `..._bf16`, ~40.9 GB) | ~20.5 GB | `models/diffusion_models/` | `UNETLoader` |
| `qwen_2.5_vl_7b_fp8_scaled.safetensors` | ~9.4 GB | `models/text_encoders/` | `CLIPLoader`, type `qwen_image` |
| `qwen_image_vae.safetensors` | ~254 MB | `models/vae/` | `Load VAE` |
| `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors` (optional, lightx2v) | — | `models/loras/` | `LoraLoaderModelOnly`, strength 1.0 |

There is **no 2511 e4m3fn fp8 file**. Third-party posts claiming one are misremembering the 2509 generation; `fp8mixed` is the 2511 quant. The official template wires **`TextEncodeQwenImageEditPlus`** (the edit-conditioning node), `ModelSamplingAuraFlow` **shift 3.1**, `CFGNorm`, and `FluxKontextImageScale`, and samples at **40 steps / CFG 3 / euler / simple**, or **4 steps / CFG 1** with the Lightning LoRA. VRAM: fp8 is comfortable on 24 GB and workable on 16 GB with offloading (the fp8 encoder offloads to system RAM); bf16 wants ~40 GB+ `[community — convergent; no official figure]`. Licence: Apache-2.0 weights, no AUP, no output-or-training clause. Nothing restricts feeding the factory's outputs to your LoRA trainer `[official — HF card + QwenLM README, 2026-08-23]`.

**Coverage checklist** (the rotation/elevation craft is in `prompting-guide.md §3.3–3.5` — use those clauses verbatim):
- All **eight horizontal rotations**, identical subject/lighting text, only the angle clause varying. Back views need explicit back-of-hair/outfit description and retries — they're the weakest-trained angles in every diffusion model.
- **One high + one low elevation** close-up per lighting setup (30–45°, gaze anchored away from camera).
- **Shot-size mix:** close-up ~30%, full body ~20%, the rest medium/cowboy.
- **3+ expressions** beyond neutral — the LoRA absorbs the dataset's dominant expression otherwise (expression lock-in).
- **2–3 outfits** if you want wardrobe flexibility; caption the clothing in those shots so it stays promptable.
- **Vary one thing per image.** Change outfit *or* lighting *or* angle — never two at once, or the LoRA can't disentangle which features are the character.

**The coverage shortcut:** fal's **Qwen-Image-Edit-2511-Multiple-Angles LoRA** (Lovis Odin @ fal, Apache-2.0) solves the rotation protocol by construction. Trained on 3,000+ Gaussian-splat renders, it takes a structured trigger — `<sks> [azimuth] [elevation] [distance]` — whose **eight azimuths are exactly this checklist's rotations** (front, the four quarters, both sides, back), with four elevations (−30/0/30/60°) and three distances (0.6/1.0/1.8×). Run it at strength 0.8–1.0 `[community — fal, 2026-08-23]`. Identity hold at the back azimuths is claimed via 2511's own consistency but unbenchmarked, so curate those shots hardest, per character. The older dx8152 *Multiple-angles* LoRA (natural-language camera prompts, far larger download numbers, Comfy-Org rehosts it) targets **2509**. Its 2511 compatibility is unverified, and 2511 natively absorbed much of that multi-angle capability, so prefer the fal 2511 LoRA.

**If the character does adult work, split the dataset by tool.** Vanilla Qwen-Image-Edit does not refuse — local weights, no runtime filter, and nothing suggests SFW character/angle editing is gated at all. But explicit anatomy *degrades*: it's undertrained there, and the community's artifact trail says LoRAs alone hit a ceiling. The working paths are merged/finetuned variants (Phr00t's Rapid-AIO builds ship NSFW/SFW splits, on 2511 since V15; Civitai's "abliterated" edit model is actually a LoRA merge, not an abliteration) `[community — HF/Civitai artifact trail, 2026-08-23]`. So the factory doctrine stands unchanged: multiply the clothed/coverage subset through the factory as normal, and generate the explicit subset **natively in Z-Image**, whose anatomy coverage is the stronger of the two (`lora-training.md §6`). A merged edit variant is the fallback only if you specifically need explicit *edits*.

**Captioning:** caption-the-residual, in prose (Qwen-3 reads sentences, not tags). Name the pose, clothing, background, lighting, and angle in every caption; leave the identity to the trigger. Full reasoning in `lora-training.md`.

---

## 4. Train, evaluate, deploy

- **Train on Z-Image Base, generate on Turbo** — `lora-training.md` covers the why, the Turbo training-adapter requirement, and hyperparameters (rank 8–16, LR 1e-4, 2000–3000 steps for this dataset size).
- **Evaluate with the XY grid** (epoch × strength) on out-of-set prompts — including at least one *new outfit and setting* the dataset never showed. A character LoRA passes when the face holds while everything else obeys the prompt.
- **Deploy with the detailer swap** (`setup-and-workflows.md §6`, end): generate the base image *without* the LoRA using the identity description, then apply the LoRA at the FaceDetailer stage, where it gets the full sampling budget on the face. Load on both ZIB and ZIT passes for maximum likeness. MyAIForce's writeups are the clearest named treatment of this established cross-model technique `[community — MyAIForce; strong]`. It exists because a character LoRA at full strength in the base pass drags composition and body proportions toward its training data.

---

## 5. Beyond the face: outfits, props, multiple characters

- **Signature outfit:** keep it *uncaptioned* in the shots where the character wears it, so it binds to the trigger and appears by default. Caption it where you want it swappable.
- **Multi-outfit LoRAs:** one LoRA can carry several outfits with a **unique trigger tag per outfit**, visually distinct outfits, and balanced per-outfit image counts. The practical ceiling is **~6 outfits** before quality collapses `[community — Khanykov01, Civitai 6990; strong]`. For one-off wardrobe changes, the edit-model factory (image 1 = character, image 2 = garment) is replacing wardrobe training entirely.
- **Multiple characters in one frame** — the honest status: Z-Image has **no regional-prompting or attention-masking tooling** as of mid-2026, so same-prompt multi-character scenes will bleed attributes (hair and clothing colors migrate between figures). The working mitigation is structural, not promptal: generate the scene with *generic* figures, then run **per-face detailer passes, each loading a different character LoRA** with its own prompt (Impact Pack detailers operate per-detection, so each face gets its own pass). Plan for retries; two characters is practical, three is pushing it. The per-face-detailer pattern is the same per-subject routing idea that ADetailer's `[SEP]` syntax implements on SDXL — see [`sdxl`](../../sdxl/references/characters.md) `[community — convergent]`.

  **The training-side fix used elsewhere does not work here.** In August 2026 the community found that **Differential Output Preservation** — training each character LoRA against a class so several load together without bleeding — lets up to four character LoRAs coexist on Krea 2. The same technique was tried on **Z-Image Base and essentially failed to learn the character at all** `[community — MASilverHammer; single report, re-verify]`. Until someone finds a Z-Image configuration that takes, per-face detailer passes remain the answer here. A multi-character job is a genuine reason to render the scene on [`krea-2`](../../krea-2/) instead — see [`character-lora-training`](../../character-lora-training/references/dataset-and-captioning.md) for the technique itself.

---

## 6. Failure modes & fixes

| Symptom | Cause (mechanism) | Fix |
|---|---|---|
| Identity collapses at profiles/back views | Front-heavy dataset — the LoRA never learned those angles | Add 5+ targeted images of the failing angles (edit-model factory makes this cheap); retrain |
| Every output is the same pose/framing ("same face" rigidity) | Near-duplicate training shots; too many steps | Cut steps / earlier epoch; increase pose/shot-size variety; re-check the XY grid for the pre-rigid checkpoint |
| Character always wears the dataset's expression | Expression lock-in — dominant expression absorbed into the trigger | Add deliberate expression variety; caption expressions so they stay promptable |
| Character LoRA drags a style/color cast into every image | Dataset shared one look; style entangled with identity | Vary lighting/background/medium across the set. Note: the SDXL-world fix (block-weighted LoRA application) has **no established equivalent for Z-Image's DiT** — prevention at dataset time is the lever `[flagged — no DiT block map yet]` |
| Two characters swap hair/clothing in one scene | Attribute bleed — one conditioning stream, no regional isolation | Per-face detailer passes with per-character LoRAs (§5); simplify to one distinguishing feature per character in the scene prompt |
| LoRA "barely does anything" | Probably not a training failure — the QKV loading gotcha | Update ComfyUI first (`setup-and-workflows.md §6`) |

---

## Sources & confidence

The pipeline shape (edit-model factory to LoRA to detailer deploy) is **named-community craft, convergent across independent authors** (Mickmumpitz, WeirdWonderfulAI/Harmeet, MyAIForce, Civitai dataset guides), stated with confidence, per this skill's two-bar policy. Z-Image-specific hard facts (no PuLID/IP-Adapter, Z-Image-Edit unreleased, training-adapter requirement) are verified against the repos and `setup-and-workflows.md §10`. The §3 factory-setup files and template wiring are official-bar, read from the Comfy-Org repos and the docs.comfy.org 2511 template on 2026-08-23. Fast-moving: Qwen-Image-Edit versions and the factory filenames, Z-Image-Edit's eventual release (it would absorb much of the factory role natively, so re-check before building new pipelines), and multi-character tooling.
