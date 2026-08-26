# Training LoRAs on Anima

This file owns **making** a LoRA for Anima: trainers, the one rule that matters more than every hyperparameter, dataset architecture, captioning in a tag dialect, style and adult work, and how to tell whether it worked. **Loading and stacking** a finished LoRA is covered in [`setup-and-workflows.md`](setup-and-workflows.md) §7 instead. What transfers across every model in this suite — dataset construction, evaluation method, the likeness and publishing gate — lives in [`character-lora-training`](../../character-lora-training/). This file carries only what is Anima-specific.

## Contents

1. Do not train the LLM adapter
2. Trainers
3. Hyperparameters
4. VRAM — the low floor, and why it matters
5. Dataset architecture
6. Captioning in the tag dialect
7. Style LoRAs
8. Adult and NSFW training
9. Assessing fit and debugging
10. The contested part: is Anima character training actually hard?

---

## 1. Do not train the LLM adapter

This is the one Anima-specific fact that matters most. It comes from the model's own author. Get it wrong and everything you train gets worse, with no error message to warn you.

> *"**Don't train the LLM adapter.** My own training script, diffusion-pipe, lets you set `llm_adapter_lr=0` to completely disable training it, and the example config has this as a default. Other trainers like sd-scripts have similar options that should be used. The LLM adapter processes the text embeddings before they get to the diffusion model, and therefore has an **outsized influence on the generated images**. The adapter itself contains a surprising amount of knowledge and is easy to degrade by training it."* `[official]`

**Here is why.** Anima's Qwen3-0.6B encoder does not feed the backbone directly. Its output passes through a learned adapter (`LLMAdapter` / `AnimaTextConditioner`, ~269 MB) that maps LLM embeddings into the diffusion model's conditioning space. That adapter holds much of Anima's tag knowledge, including artist vocabulary and character priors. Any training step that touches it rewrites how the model understands prompts, globally, using gradients from just your twenty images. The result reproduces your subject but quietly damages everything else. It shows up as "Anima got worse," not "my LoRA is broken."

**Check this before your first run.** In **diffusion-pipe**, confirm `llm_adapter_lr=0` (the shipped example config has it, but check it survived your edits). In **sd-scripts**, find and set the equivalent option yourself rather than trusting the default. In **any GUI wrapper**, read the config it generates. Do not trust a wrapper that hides this setting.

SDXL has a similar debate about training its text encoder, and there the answer is contested. Here it is not. The vendor's answer is unambiguous: leave the adapter frozen.

---

## 2. Trainers

| Trainer | Notes |
|---|---|
| **diffusion-pipe** (tdrussell) | The author's own script — *"my own training script"* on the model card, and `tdrussell@circlestone.ai` is the commercial-licence contact, so this is first-party-adjacent tooling. Ships an Anima example config with `llm_adapter_lr 0` |
| **kohya-ss/sd-scripts** | **First-class and merged on `main`** — `anima_train.py`, `anima_train_network.py`, `anima_train_control_net_lllite.py`, `anima_minimal_inference.py`, plus `docs/anima_train_network.md` and `docs/anima_torch_compile.md`. The route most people take, and the base for several forks and GUIs |
| **citron-anima-lora-trainer-ui** | Gradio front-end built for Anima, advertising **6 GB VRAM** at 768 px `[community — citronlegacy; reproducible]` |
| **Aozora Trainer** (Hysocs) | SDXL + Anima. Claims **100% of Anima at 1152² in ~11.4 GB, ~2.67 s/iter** — full finetuning on a 12 GB card `[community — u/RealOminousHvh]` |
| **AI Toolkit** (ostris) | Reported in use, not confirmed in ostris's own docs `[community — u/justbob9; re-verify]` |
| **Anima Standalone Trainer** | Named in practitioner reports; little documentation `[community — u/justbob9]` |
| **LoRA Dataset Studio** (perfectgf) | Dataset tooling; lists Anima in its ai-toolkit presets alongside Z-Image, Krea 2, FLUX and SDXL `[community]` |
| **OneTrainer** | No Anima support found either way — check its changelog before planning around it |

**Train on Anima-Base.** *"LoRAs should be trained using this version"* — Base is unrefined and has no aesthetic tuning to fight. LoRAs trained on it also run on Aesthetic, Turbo and community checkpoints. Training on Aesthetic or Turbo instead bakes their style into your LoRA and narrows where it can be used.

---

## 3. Hyperparameters

These are attributed starting points, not laws. The one number the author gives explicitly:

> *"Use a low learning rate. **For a rank 32 LoRA, start with 2e-5.**"* `[official]`

That is notably low — an order of magnitude below SDXL guides' 1e-4/3e-4. The reason is in the same passage:

> *"As a base model, there is no aggressive aesthetic tuning or RLHF you need to overcome when finetuning… **A light touch is all you need.**"*

This is the opposite of the SDXL-anime situation, where much of a LoRA's learning-rate budget goes into overpowering the checkpoint's baked-in style. On Anima-Base there is nothing to overpower, so a high learning rate mostly just buys overfitting.

| Setting | Starting point | Note |
|---|---|---|
| Rank | **32** | the rank the official LR is calibrated for; drop to 8–16 for a simple style, raise only with evidence |
| Learning rate | **2e-5** at rank 32 | scale down as rank rises; if you halve rank you can nudge LR up modestly |
| Resolution | 768 px for a 6 GB budget; 1024 px if you have the VRAM | Anima's band is 512²–1536², so 1024 training generalises well |
| Adapter LR | **0** | §1 |
| Optimiser | trainer default; the community forks report Muon-family experiments `[community]` | no settled Anima consensus — follow your trainer's default |

Everything not listed — epochs, repeats, batch size, scheduler — has no Anima-specific consensus. Follow [`character-lora-training`](../../character-lora-training/) instead. Treat any confident number you find online without a named author as SEO laundering.

---

## 4. VRAM — the low floor, and why it matters

**LoRA training fits in ~6 GB at 768 px**, corroborated independently by the `citron-anima-lora-trainer-ui` project and by a named Civitai author at the same resolution, both noting higher resolutions need more `[community — citronlegacy, Civitai 26217; convergent]`.

**Full finetuning fits in ~11.4 GB at 1152²** — `u/RealOminousHvh`'s Aozora trainer: *"It can train 100% of Anima at 1152×1152 resolution while using approximately 11.4 GB of VRAM at around 2.67 seconds per iteration."* `[community — u/RealOminousHvh; single report]`

**Why this matters more than it looks.** No other model this suite covers can be *fully finetuned* on a 12 GB consumer card. That is why Anima picked up dozens of community checkpoints within months, while comparable models only pick up LoRAs. The barrier to building a whole checkpoint fell below the price of a mid-range GPU. If you are choosing a model to build a custom anime checkpoint on, this is the fact that should decide it.

---

## 5. Dataset architecture

The model-agnostic craft — set size, rotation and elevation coverage, curation, the identity ratio, regularisation — lives in [`character-lora-training`](../../character-lora-training/) and [`dataset-and-captioning.md`](../../character-lora-training/references/dataset-and-captioning.md). Anima-specific deltas:

- **The edit-model dataset-factory pattern does not really work here.** Anima's editing tooling is weak ([`setup-and-workflows.md`](setup-and-workflows.md) §8), unlike [`flux-2`](../../flux-2/) or [`z-image`](../../z-image/). Build the set with the ReStyler trick at its ~85% hit rate instead, or sweep prompts and seeds and curate hard.
- **Post-cutoff subjects need more data.** Anima's knowledge stops at September 2025. Teaching something the model has never seen takes a larger, more varied set than sharpening something it half-knows.
- **Train at or above 768 px.** Anima's band runs to 1536², and a LoRA trained at 512 px visibly under-delivers at the resolutions people actually generate at.
- **Do not mix a character and a heavy art style in one small dataset**, unless you want the two fused together — that is the shape of the failure in §10.

---

## 6. Captioning in the tag dialect

**Caption in the dialect the model was trained in.** Anima's captions were Danbooru tags, natural language, and hybrids, so tag captions are native and prose captions are also legitimate. In practice, for a character or style LoRA, **tag captions in the trained slot order** (`prompting-guide.md` §2) are the safer default. They match the register people will prompt in, and they make the caption-the-residual discipline mechanical.

**Caption the residual, in tags.** This rule transfers from every model in this suite: caption what *varies* and what you want to be able to *change*, and leave out what you want fused into the trigger. For a **character LoRA**, that means tagging pose, expression, clothing, background and framing, while leaving permanent identity features untagged. For a **style LoRA** it flips — tag the subjects thoroughly and say as little as possible about the rendering.

**Anima-specific caption notes:**

- **Include a rating tag** in every caption (`safe` / `sensitive` / `nsfw` / `explicit`) — it is a trained axis, and omitting it weakens conditioning on it while your LoRA is loaded.
- **Include quality tags consistently or not at all.** Half-captioned quality tags teach the LoRA that `masterpiece` means "the subset I happened to label".
- **Never write a bare artist name in a caption** — without `@` it trains the wrong token (`prompting-guide.md` §6).
- **Tag dropout is already in the base**, so exhaustive captions are not required. Complete-and-relevant beats long.

---

## 7. Style LoRAs

Anima has the deepest built-in artist vocabulary in the suite — 42k+ styles by the Style Explorer count `[community — ThetaCursed]`. So the first question for any style LoRA is **whether the style is already in the model under an `@` tag.** Check before training. Many "I need a style LoRA" cases on Anima are really "I did not know the `@` prefix was mandatory" (`prompting-guide.md` §6).

When training is genuinely warranted, **subject diversity is the whole game.** Twenty portraits produce a portrait LoRA, so spread your set across subjects, compositions and shot sizes. The **acceptance test** is that the style is recognisable on *out-of-set subjects*. If it only looks right on things resembling your dataset, it memorised composition instead of style. The two overfit signals to watch for are composition memorisation and colour-cast lock-in. **Rank** starts lower than for characters — 8–16 is often enough. Rank-for-style is a wider-community dispute rather than an Anima-specific one, and [`character-lora-training`](../../character-lora-training/) owns that discussion. On **ethics**, single-living-artist datasets are where the licence is the least of your constraints ([`publishing-and-likeness.md`](../../character-lora-training/references/publishing-and-likeness.md)). Anima's licence also forbids implying CircleStone endorsement of a derivative, and bars training models for *commercial* use.

---

## 8. Adult and NSFW training

Anima treats adult content as a **trained conditioning axis**, not a filtered edge case: `safe`, `sensitive`, `nsfw`, `explicit` are four tokens in the same prompt slot as quality and year tags. There is no refusal layer to defeat and no separate uncensored checkpoint to hunt for. That makes adult LoRA work much simpler than on models that gate it.

Consequences for training:

- **Caption the rating honestly on every image.** If you caption explicit images as `safe`, you teach the model to ignore the axis, and your LoRA then leaks explicit output into `safe` prompts.
- **Train on Base.** The adult-oriented community merges (`MiaoMiao Harem`, `Hassaku (Anima)`, the `uwumerge`/`uwustyle` furry line) already carry strong content priors. Training on one of these bakes those priors in and narrows where your LoRA can be used.
- **The licence's actual stance:** it prohibits *"unlawful content, including child sexual abuse material, or non-consensual intimate images"* and states no general adult prohibition beyond that. The binding constraints on publishing come from platform rules and the law on real-person likeness — Civitai's real-person ban and the TAKE IT DOWN Act — not from this licence. [`nsfw-training.md`](../../character-lora-training/references/nsfw-training.md) and [`publishing-and-likeness.md`](../../character-lora-training/references/publishing-and-likeness.md) own that decision. Read them before you train, not before you upload.

---

## 9. Assessing fit and debugging

Evaluate with an **XY grid of epoch × LoRA strength** on prompts that were *not* in the dataset. Loss is a weak signal and should not be your stopping criterion ([`evaluation-and-tooling.md`](../../character-lora-training/references/evaluation-and-tooling.md)). Anima-specific reading:

| Symptom | Likely cause |
|---|---|
| Base Anima seems *globally* worse after loading the LoRA — unrelated prompts degrade | The LLM adapter was trained (§1). Re-train with `llm_adapter_lr 0` |
| Subject is right but every image has the same pose/framing | Dataset lacked variety; captions did not name the pose |
| Artist and style tags stop responding while the LoRA is loaded | The LoRA over-fitted a style; lower rank, lower LR, or caption the style out |
| Likeness needs strength > 1.2 to appear | Under-trained, or the subject is post-cutoff and needs more data |
| Good at 768 px, mushy at 1280 px | Trained too low; retrain at ≥768, ideally 1024 |
| Works on Base, wrong on Turbo/Aesthetic | Expected — those carry their own style. Drop strength ~0.1–0.3 rather than re-training |
| An A/B against a bad seed says the LoRA is broken | Anima's seed instability. Compare across 3–4 fixed seeds, never one |

---

## 10. The contested part: is Anima character training actually hard?

The vendor says *"a light touch is all you need."* A named practitioner's experience directly contradicts that `[contested]`:

> `u/justbob9` — *"I was defeated by a character LORA training for anima"*: **100+ hours, a week of 24/7 training**, across AI Toolkit and Anima Standalone Trainer, multiple datasets and multiple captioning schemes, targeting a webtoon character **plus that webtoon's art style**, and never reached a satisfying result. Nobody in the thread diagnosed it.

Both can be true. The likely explanation lies in the target, not the model: **character + a specific non-anime art style in one LoRA** is the hardest configuration for any model, and it is the one that went wrong here. Anima's own strength — a huge baked-in artist vocabulary — works against you in this case, because the base keeps asserting its own rendering conventions over the webtoon style you are trying to teach it.

Until someone diagnoses this properly, here is the practical reading: **separate the concerns.** Train the character on Anima-Base with the style captioned *out*, and get the style instead from `@` artist tags or a second, separately trained style LoRA. Two LoRAs at moderate strength are far easier to debug than one doing both jobs. And **do not escalate hyperparameters first** — the failure above already involved a week of training, so more steps is the least likely fix on a model whose author recommends 2e-5. Treat this as an open question in the Anima community, not settled knowledge.
