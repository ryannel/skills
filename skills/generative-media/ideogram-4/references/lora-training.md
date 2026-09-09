# Training LoRAs on Ideogram 4

This file covers **making** a LoRA for Ideogram 4. It explains what trains it, what the licence permits, what the community has actually produced, and the two things nobody has demonstrated yet. **Loading and stacking** a trained LoRA belongs to `setup-and-workflows.md § 6`, and that section exists mainly to say how little is settled there. Everything that transfers across models lives in [`character-lora-training`](../../character-lora-training/): dataset architecture, captioning doctrine, rank and step budgeting, and judging whether a run took. This file carries only what is specific to Ideogram 4.

**This coverage was rewritten on 2026-08-13 and updated on 2026-09-09.** At launch there was no training path at all, and this skill said so. That is no longer true, and the earlier text routed people away from something that now works. The 2026-09-09 update added a third trainer, a fourth that does not work with ComfyUI, and the first named hyperparameter recipe. If you are reading an older copy, disregard it.

## Contents

- [1. What the licence permits](#1-what-the-licence-permits)
- [2. Trainers](#2-trainers)
- [3. Captioning — the unresolved part](#3-captioning--the-unresolved-part)
- [4. What the community has actually trained](#4-what-the-community-has-actually-trained)
- [5. What this does and does not unlock](#5-what-this-does-and-does-not-unlock)

---

## 1. What the licence permits

The Ideogram 4 Non-Commercial Model Agreement **permits fine-tuning** for non-commercial use. It excludes commercial fine-tuning and distillation by name `[official — Non-Commercial Model Agreement]`.

People miss one consequence: **the restriction travels with the derivative.** Redistribution has to pass on the same terms. A LoRA trained on Ideogram 4 weights is therefore itself a non-commercial artefact, wherever you publish it and whoever downloads it. Training on a hosted service does not launder that, because fal rents you compute, not a licence. If the output has to be commercial, the whole path is the hosted API or a separate paid weights licence from Ideogram, and a LoRA is not part of it. See `../api-and-hosted.md` and SKILL.md's *Licence & limitations*.

---

## 2. Trainers

Three trainers produce a LoRA that loads on the open weights. A fourth produces one that does not, and it is listed so you do not find that out after a run.

| Path | Status | Loads in ComfyUI? |
|---|---|---|
| **`ostris/ai-toolkit`** | `ideogram-ai/ideogram-4-fp8` is **named in the supported-models list**. This is the self-hosted route with the longest record, and the one the only published recipe (below) was written for `[official — repo]` | Yes |
| **`kohya-ss/musubi-tuner`** | **First-class support since 2026-07-04** (PRs #966, #975, #977; `docs/ideogram4.md`). Train with `--network_module networks.lora_ideogram4`. It loads the fp8 weights directly and dequantises on the fly. `--blocks_to_swap` goes up to 33 of the 34 blocks for low-VRAM cards. It ships its own `CaptionVerifier`, switched on with `--validate_caption_structure`, which makes it the one trainer that checks a JSON training caption the way inference does (§3) `[official — musubi-tuner docs/ideogram4.md]` | Yes |
| **fal — "Ideogram V4 LoRA Trainer"** | **Live, not waitlisted.** Exposes `steps` (100–40,000, default 1000), learning rate (1e-6–1e-2, default 1e-4), resolution (auto / preset / custom `WxH`), and a default caption for uncaptioned images `[official — fal docs]` | Yes, via its `comfy` file |
| **OneTrainer** | An Ideogram4 extension exists, but it writes **split `to_q` / `to_k` / `to_v` LoRA keys**. ComfyUI does not recognise them and logs `lora key not loaded` for each. The ComfyUI issue has been open since 2026-06-14 with no fix in progress. Whether diffusers loads the file is not reported `[community — ComfyUI issue #14477]` | **No** |

**The fal trainer emits two files, and the second one is the important one.** It produces a `fal` format for fal's own Ideogram V4 endpoint and a **`comfy` format for ComfyUI**. Per fal: *"The two files contain the same trained weights; only the internal key names differ."* The `comfy` file is what makes a hosted-trained LoRA usable on the **open weights**, so you are not locked into their endpoint.

**One named hyperparameter recipe exists, and it is one author's numbers, not a consensus.** estylon published a style-LoRA run on ai-toolkit eight days after launch (Substack, 2026-06-11). The recipe: **rank 16 / alpha 16** (32/32 for higher fidelity), **2,500 steps**, learning rate **1e-4** with **`adamw8bit`**, a checkpoint **every 250 steps**. The author's most useful observation is about which checkpoint to keep: **the style sweet spot came before the final step**, so save often and pick an earlier file rather than the last one `[community — estylon, Substack; single report]`. Nobody has corroborated or contradicted these numbers in print, and they are for a *style* LoRA. Treat them as a starting point to sweep from, not a recipe to copy. fal's defaults above are product defaults, not a tuned run. For anything the recipe does not cover, such as step budgets by dataset size, the generic rules in [`character-lora-training`](../../character-lora-training/) are still the best substitute.

---

## 3. Captioning — the unresolved part

This is the one place where training Ideogram 4 is genuinely unlike training any other model in the suite. The difficulty follows from the model's defining fact: **it was trained exclusively on structured JSON captions.** Every caption the base model has ever seen is a JSON document with a fixed key order (`json-caption-guide.md § 1`).

Most trainers do not know that. ai-toolkit captions datasets in prose or tags by convention, and fal's "default caption for uncaptioned images" field takes a plain string. The default path on either therefore trains the model on a caption format it has never encountered. That is exactly the train/inference mismatch the JSON schema exists to avoid. **musubi-tuner is the exception.** Its `--validate_caption_structure` flag runs a `CaptionVerifier` over your training captions, so a JSON-captioned dataset gets the same key-order and schema checks at training time that `run_inference.py` applies at inference `[official — musubi-tuner docs/ideogram4.md]`. If you intend to caption in JSON, it is the trainer that will tell you when you got the shape wrong.

**Nobody has published a comparison** of JSON-captioned against prose-captioned training `[flagged — re-verify]`. The one named recipe (§2) does not say which it used. Reasoning from what is known, rather than from testing: a style LoRA probably tolerates the mismatch, because style is carried in the image signal and the trigger word does little work. Anything that depends on the caption *steering* the result has more to lose. That includes a concept LoRA, a layout behaviour, or a character. Until someone measures it, the defensible rule is this: **caption your training set in the same shape you intend to prompt in.** If you will prompt in JSON, caption in JSON.

---

## 4. What the community has actually trained

**36 Ideogram 4.0 LoRAs are published on Civitai, one of them character-tagged**, per the 2026-09-09 pull `[community — Civitai API, queried 2026-09-09]` (34 on 2026-08-23, 33 on 2026-08-13; the query is `baseModel=Ideogram 4.0` — note the `.0`, because the obvious spellings return zero). Two cautions on the number. The plain query also returns Workflow-type entries, so filter with `types=LORA` when you re-run it. And "character-tagged" is a tag the uploader chose, not evidence that the likeness holds; the entry has no write-up behind it. So this is a real, if small, ecosystem, not just a proof of concept.

**Read the composition, not just the count.** The shelf is almost entirely **style and aesthetic** work: Ghibli, Tintin, vintage anime, fantasy-realism refiners, a `Gray Screen bypass`. **Character/likeness LoRAs are essentially absent: one character-tagged entry of 36, with no recipe or write-up behind it.** Adult work was absent too at the first sampling: zero of the 33 was adult-flagged. But a re-census ten days later put **~26% of 34 explicit** `[community — Civitai baseModel census, 2026-08-23]`. So read the model-level safety filter (`setup-and-workflows.md § 5`) as a strong prior, not a wall. The `Gray Screen bypass` entry above is somebody building against that filter, and enough adult work has now appeared on the shelf that the filter is evidently porous. Neither number is a tooling gap; both are downstream of the filter.

A calibration note on download counts: the most-downloaded entry, `Lenovo UltraReal`, shows 152k downloads. But it spans **12 base models**, and its **Ideogram 4.0 version has 6,866**. Civitai reports downloads at the *model* level, not the version level. A big number next to an Ideogram LoRA usually is not an Ideogram number.

---

## 5. What this does and does not unlock

- **Style LoRAs: supported and in active use.** Train them. Three trainers emit a loadable file, and there is one named starting recipe (§2). The craft is no longer the gap; the corpus of results is.
- **Speed LoRAs exist too.** ostris published *Ideogram 4 TurboTime*, which runs the model in as few as 2 steps with no CFG and no unconditional model `[community — ostris, HF + Civitai]`. That is a distillation LoRA, not a style one, and it belongs to the loading half of the story: `setup-and-workflows.md` §4 covers what it does to the graph.
- **Character LoRAs: the training path exists, but nobody has demonstrated it.** One character-tagged LoRA of 36 is published (§4), with no recipe, no comparison and no write-up, and there are no identity adapters (below). Treat a character run here as **exploratory work you are doing first**, not a documented recipe. If you need a likeness this week, build it in [`flux-2`](../../flux-2/), [`z-image`](../../z-image/) or [`sdxl`](../../sdxl/) and use Ideogram only for the typography pass. **Note what this bullet is and is not saying.** Training a likeness *into* the weights is undemonstrated. Carrying one across a few generations is not, because that needs no training at all. The locked half-canvas workflow in `SKILL.md` § *Consistent characters without an adapter* does it with the base model alone `[community — reality_comes, 402 pts]`.
- **Adult/NSFW work meets the filter before it meets training.** The NSFW filter is in the weights and cannot be disabled (`setup-and-workflows.md § 5`). That is a model choice, not a tooling gap. What has *not* held is the stronger claim that a LoRA cannot buy its way past it. Adult output has been posted from the open weights with style LoRAs loaded `[community — Ashamed-Ad7403, r/unstable_diffusion; single report]`, and roughly a quarter of the published LoRAs are now explicit (§4). Nobody has shown the mechanism. So treat this as a route others have walked, not a recipe you can follow, and expect gray screens either way `[flagged — re-verify]`. Cross-model craft lives in [`character-lora-training`](../../character-lora-training/references/nsfw-training.md).
- **Still no ControlNet, PuLID, or IP-Adapter** for Ideogram 4, from Ideogram or any community team. A Hugging Face discussion on `ideogram-4-fp8` is titled *"No Controlnet Capability."* `[community]` **This is a separate axis from LoRA training, and it has not moved.** Structural pose/identity conditioning remains unavailable.

Trainer support is young; re-verify flags and supported-model lists before a long run. Trainer facts above were checked against source on 2026-09-09.
