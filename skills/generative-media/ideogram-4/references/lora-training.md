# Training LoRAs on Ideogram 4

This file covers **making** a LoRA for Ideogram 4. It explains what trains it, what the licence permits, what the community has actually produced, and the two things nobody has demonstrated yet. **Loading and stacking** a trained LoRA belongs to `setup-and-workflows.md § 6`, and that section exists mainly to say how little is settled there. Everything that transfers across models lives in [`character-lora-training`](../../character-lora-training/): dataset architecture, captioning doctrine, rank and step budgeting, and judging whether a run took. This file carries only what is specific to Ideogram 4.

**This coverage was rewritten on 2026-08-13.** At launch there was no training path at all, and this skill said so. That is no longer true, and the earlier text routed people away from something that now works. If you are reading an older copy, disregard it.

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

| Path | Status |
|---|---|
| **`ostris/ai-toolkit`** | `ideogram-ai/ideogram-4-fp8` is **named in the supported-models list**. This is the self-hosted route `[official — repo]` |
| **fal — "Ideogram V4 LoRA Trainer"** | **Live, not waitlisted.** Exposes `steps` (100–40,000, default 1000), learning rate (1e-6–1e-2, default 1e-4), resolution (auto / preset / custom `WxH`), and a default caption for uncaptioned images `[official — fal docs]` |

**The fal trainer emits two files, and the second one is the important one.** It produces a `fal` format for fal's own Ideogram V4 endpoint and a **`comfy` format for ComfyUI**. Per fal: *"The two files contain the same trained weights; only the internal key names differ."* The `comfy` file is what makes a hosted-trained LoRA usable on the **open weights**, so you are not locked into their endpoint.

**No published hyperparameter guidance exists yet** for either path. There are no rank/alpha ladders, no step budgets by dataset size, and no learning-rate reports from named practitioners `[flagged — re-verify]`. fal's defaults above are the only numbers anyone has put a name to, and they are product defaults, not a tuned recipe. Treat them as a starting point and expect to sweep. Until Ideogram-4-specific reports appear, the generic budgeting rules in [`character-lora-training`](../../character-lora-training/) are the best substitute.

---

## 3. Captioning — the unresolved part

This is the one place where training Ideogram 4 is genuinely unlike training any other model in the suite. The difficulty follows from the model's defining fact: **it was trained exclusively on structured JSON captions.** Every caption the base model has ever seen is a JSON document with a fixed key order (`json-caption-guide.md § 1`).

Trainers do not know that. ai-toolkit captions datasets in prose or tags by convention, and fal's "default caption for uncaptioned images" field takes a plain string. The default path therefore trains the model on a caption format it has never encountered. That is exactly the train/inference mismatch the JSON schema exists to avoid.

**Nobody has published a comparison** `[flagged — re-verify]`. Reasoning from what is known, rather than from testing: a style LoRA probably tolerates the mismatch, because style is carried in the image signal and the trigger word does little work. Anything that depends on the caption *steering* the result has more to lose. That includes a concept LoRA, a layout behaviour, or a character. Until someone measures it, the defensible rule is this: **caption your training set in the same shape you intend to prompt in.** If you will prompt in JSON, caption in JSON.

---

## 4. What the community has actually trained

**34 Ideogram 4.0 LoRAs are published on Civitai** (re-censused 2026-08-23, 33 on 2026-08-13; the query is `baseModel=Ideogram 4.0` — note the `.0`, because the obvious spellings return zero). So this is a real, if small, ecosystem, not just a proof of concept.

**Read the composition, not just the count.** The shelf is almost entirely **style and aesthetic** work: Ghibli, Tintin, vintage anime, fantasy-realism refiners, a `Gray Screen bypass`. **Character/likeness LoRAs are essentially absent.** Adult work was absent too at the first sampling: zero of the 33 was adult-flagged. But a re-census ten days later put **~26% of 34 explicit** `[community — Civitai baseModel census, 2026-08-23]`. So read the model-level safety filter (`setup-and-workflows.md § 5`) as a strong prior, not a wall. The `Gray Screen bypass` entry above is somebody building against that filter, and enough adult work has now appeared on the shelf that the filter is evidently porous. Neither number is a tooling gap; both are downstream of the filter.

A calibration note on download counts: the most-downloaded entry, `Lenovo UltraReal`, shows 152k downloads. But it spans **12 base models**, and its **Ideogram 4.0 version has 6,866**. Civitai reports downloads at the *model* level, not the version level. A big number next to an Ideogram LoRA usually is not an Ideogram number.

---

## 5. What this does and does not unlock

- **Style LoRAs: supported and in active use.** Train them.
- **Character LoRAs: the training path exists, but nobody has demonstrated it.** No published character LoRAs exist, and there are no identity adapters (below). Treat a character run here as **exploratory work you are doing first**, not a documented recipe. If you need a likeness this week, build it in [`flux-2`](../../flux-2/), [`z-image`](../../z-image/) or [`sdxl`](../../sdxl/) and use Ideogram only for the typography pass. **Note what this bullet is and is not saying.** Training a likeness *into* the weights is undemonstrated. Carrying one across a few generations is not, because that needs no training at all. The locked half-canvas workflow in `SKILL.md` § *Consistent characters without an adapter* does it with the base model alone `[community — reality_comes, 402 pts]`.
- **Adult/NSFW work meets the filter before it meets training.** The NSFW filter is in the weights and cannot be disabled (`setup-and-workflows.md § 5`). That is a model choice, not a tooling gap. What has *not* held is the stronger claim that a LoRA cannot buy its way past it. Adult output has been posted from the open weights with style LoRAs loaded `[community — Ashamed-Ad7403, r/unstable_diffusion; single report]`, and roughly a quarter of the published LoRAs are now explicit (§4). Nobody has shown the mechanism. So treat this as a route others have walked, not a recipe you can follow, and expect gray screens either way `[flagged — re-verify]`. Cross-model craft lives in [`character-lora-training`](../../character-lora-training/references/nsfw-training.md).
- **Still no ControlNet, PuLID, or IP-Adapter** for Ideogram 4, from Ideogram or any community team. A Hugging Face discussion on `ideogram-4-fp8` is titled *"No Controlnet Capability."* `[community]` **This is a separate axis from LoRA training, and it has not moved.** Structural pose/identity conditioning remains unavailable.

Trainer support is young; re-verify flags and supported-model lists before a long run.
