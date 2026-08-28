# Adult and NSFW LoRA training

Adult content is a dominant use of open-weights media models, and most of the difficulty around it gets misdiagnosed. This file covers what actually decides results.

If a real person is anywhere near the dataset, read [`publishing-and-likeness.md`](publishing-and-likeness.md) first. That file decides whether the work can be distributed at all, and that question comes before anything here.

1. [The limit is data, not refusal](#1-the-limit-is-data-not-refusal)
2. [Base model selection by family](#2-base-model-selection-by-family)
3. [Captioning](#3-captioning)
4. [Anatomy failure modes](#4-anatomy-failure-modes)
5. [Video](#5-video)

---

## 1. The limit is data, not refusal

This is the single most useful thing to get straight. Open-weights image and video models **do not generally refuse.** They produce poor anatomy because the base model saw very little of it during training. What looks like censorship is usually just absence.

That explains the ecosystem's most stubborn myth. People swap the text encoder for an abliterated ("heretic") build and expect the swap to unlock capability. **It does not, and the author of the leading abliteration tool has said so directly:**

> Abliteration works by directional ablation on the residual stream, so that an LLM stops *refusing*. But LLMs already represent "harmful" inputs accurately. That accurate representation is how they know to refuse in the first place. The hidden states reaching the diffusion model are therefore not clearer. They are **perturbed relative to what the diffusion model was trained on**, which costs prompt adherence and sometimes adds artefacts. `[community — -p-e-w-, author of Heretic]`

The file sizes corroborate this. The encoder builds shipped with some models are physically **smaller than stock, because the output layers are missing.** Refusal lives in those layers, and a text encoder never uses them. There is no refusal path there to remove.

**Abliterated models do help in one place: prompt expansion.** An LLM asked to *enhance* a prompt can refuse outright, and several official ComfyUI templates ship such an expander switched on by default. The expander is a separate stage that runs before the encoder, so swapping it is legitimate.

The confusion usually comes from template structure. A template's subgraph wires **the same LLM** into both the expander and the text-encode node. A swap meant to fix the refusing expander therefore quietly changes the encoder too. Unpack the subgraph and point the abliterated model at the expander only.

**So if anatomy is poor, change the base model or train it in. No conditioning trick substitutes for training data.**

### But "train it in" is a different job at a different scale

Here is the distinction that catches people. It is worth being blunt about it, because the two jobs get confused constantly:

| | **Character LoRA** | **Capability / concept LoRA** |
|---|---|---|
| Teaching | *who someone is*, on a base that already renders bodies | *anatomy the base model largely lacks* |
| Dataset | **15–30** curated images (up to ~100 for broad-coverage character work) | **1,500+** handpicked, carefully captioned images — "a small dataset of 100–300 won't do it" |
| Rank | 8–64 | **128 minimum** |
| Effort | An afternoon | A project |

`[community — Qwen-Image NSFW LoRA notes, Civitai]`

The consequence: **if your base lacks the coverage, do not try to fix it with a character LoRA.** You will build a LoRA that half-works and then blame the settings. Instead, either pick a base that already has the coverage (§2), or stack an existing general-purpose capability LoRA *underneath* your character LoRA and let each one do its own job.

That layering is the normal production pattern. It is also why the good-citizen advice in `../SKILL.md` matters: a character LoRA that demands strength 1.0 cannot share a stack with the anatomy LoRA it needs.

### The layering is a live constraint, not a solved recipe

One practitioner worked through four published Wan I2V anatomy LoRAs — DASIWA, "Ultimate pussy anus helper", "Edible Anuses" and HearmemanAI's. Each one either failed to render at all or *"changes the character lora too much"* `[community — One-Energy5403; unanswered]`. Nothing in the thread resolved the problem, and nobody has published a working configuration `[contested]`.

Read that report alongside the paragraph above, because they are the same situation seen from opposite ends: **stacking a capability LoRA under a character LoRA is exactly what people are doing when this fails.** The mechanism is not mysterious. Both adapters write into the same attention weights. An anatomy LoRA trained on 1,500+ images of bodies is a much broader change than a 25-image identity, so it has every opportunity to move the face too. Two things follow:

- **Evaluate the stack, not the LoRA.** A character LoRA that passes its strength sweep on its own tells you nothing about whether it survives an anatomy LoRA underneath. The stack test in `../SKILL.md` is the gate, and on adult work it is not optional. Run it before you commit to the base.
- **A base that already has the coverage beats the stack.** This is the strongest practical argument for choosing on §2's axis instead of assembling coverage at generation time. On video it is more than an argument: an NSFW-merged checkpoint is the route that has actually been shown to fix anatomy failures a LoRA could not. See the single-variable study in [`generative-media-atlas/references/adult-work.md`](../../generative-media-atlas/references/adult-work.md) §3. That study also warns that stacking an NSFW LoRA onto such a merge **double-applies** what is already baked in.

**Merging instead of stacking.** Where you are combining several capability LoRAs, published merge tooling folds them into one "meta-LoRA" by **rank concatenation**. It joins the A and B matrices, scaling each contribution by `√(weight × alpha/rank)` `[community — published merge scripts; re-verify]`. Know two things before you go there. First, rank adds up, so the merged file is as big as the sum of its parts. Second, **naming conventions differ**: Kohya-style files use `.lora_down.weight` / `.lora_up.weight` / `.alpha`, while PEFT-style files use `.lora_A.weight` / `.lora_B.weight`. A merge script that assumes the wrong convention finds no modules to merge, and it reports success while changing nothing.

### The gap this framing predicts, and nobody has closed

If the limit is data, then a model fails wherever it saw least. There is a reported case of exactly that, and nothing in this suite answers it. Across SDXL, [`z-image`](../../z-image/) and [`krea-2`](../../krea-2/) alike, scenes specifying **two women** come back with distorted anatomy and **intrusive male anatomy that was never prompted** `[community — ricovelez; unanswered]`.

The mechanism is the one §1 opened with, not a new one. The adult data these bases absorbed is overwhelmingly heteronormative. A same-sex scene therefore sits far enough outside the distribution that the model falls back on what it saw most. That is also why negative prompts disappoint here: they bias sampling away from a token, which is a weak lever against a prior the model is reaching for structurally.

No verified fix has surfaced, and nothing in this suite currently addresses it `[flagged — open gap]`. Two directions have the most behind them. The first is **base choice**: the booru-tagged SDXL finetunes carry explicit act and configuration tags, so you can name the scene instead of hoping for it. The second is **composing instead of generating**: per-face detailer passes or regional conditioning ([`dataset-and-captioning.md`](dataset-and-captioning.md) §5) resolve each figure separately, so no single sampling pass has to hold the whole frame. Training it in is the in-principle answer, and it inherits the scale from the table above — this is a capability LoRA, not a character one.

---

## 2. Base model selection by family

Base choice dominates every other decision here. It matters more than rank, more than steps, more than captioning.

**The usual proxy for a base's adult support is what share of its published LoRAs are adult-flagged. The two measurements of that share disagree, almost inversely, on video.** `[contested]` Both are given here, because quietly picking one would hide the more useful lesson, which is about the metric itself.

| Census | Method | The ordering it produces |
|---|---|---|
| **2026-08-13** — this file's original figures | ~100 LoRAs per base from Civitai's model API | Wan 2.2 I2V **90%**, Wan 2.2 T2V 84%, MiniMax H3 62%, Krea 2 52%, Z-Image 46–47%, SDXL/Pony/Illustrious 29–34%, Anima 29%, Flux 28% |
| **2026-08-23** — re-census `[official — Civitai /api/v1/models]` | 600 most-downloaded LoRAs per base, testing the X and XXX bits of the `nsfwLevel` bitmask (1 PG · 2 PG-13 · 4 R · 8 X · 16 XXX) | Pony **67%**, Illustrious 56%, Anima 52%, NoobAI 50%, Krea 2 46%, Z-Image Turbo 45%, Flux.1 dev 37%, SDXL 1.0 31%, Wan 2.2 T2V/I2V 23%/22%, LTX 2.3 14% |

**The likely explanation covers half the gap, and which half matters.** `nsfwLevel` is a bitmask over a model's **preview images**, not over what the LoRA does. A video LoRA's preview is routinely a tame first frame or a motion demo, so an explicit video LoRA can score PG. The metric therefore undercounts video systematically, and that accounts for Wan falling from the top of one table to the bottom of the other.

It does **not** account for the image half, where Flux rises from 28% to 37% and the booru finetunes climb into the fifties and sixties. There the two samples differ in what they select for: an unspecified ~100 versus the 600 most-downloaded, and popularity correlates with rating. **Treat neither ordering as settled.** In particular, do not read the video rows of either table as a capability ranking.

**A trap for whoever measures next: the API's `nsfw` boolean is dead.** It returns `false` for every model sampled, including ones whose previews are XXX. Any share built on it is therefore wrong, and that is one candidate explanation for the 2026-08-13 numbers `[flagged — re-verify]`. Test bits instead. Explicit is `level & (8|16)`; mature is `level & (4|8|16)`. Using `nsfwLevel > 1` counts PG-13 as adult and inflates everything.

**Reproduce rather than trust.** [`generative-media-atlas`](../../generative-media-atlas/) carries `scripts/civitai_census.py`, and `python scripts/civitai_census.py --adult` re-runs the 2026-08-23 measurement exactly. The full 17-base table with its caveats lives in [`generative-media-atlas/references/adult-work.md`](../../generative-media-atlas/references/adult-work.md) §1. **That file owns model choice; this one owns what to do once you have chosen.** So re-measure there and come back here.

**What survives the disagreement** — none of the following rests on the metric:

- **Adult work is a dominant published use of open video models.** The community evidence is direct rather than inferred: r/unstable_diffusion's top-of-month is dominated by video `[community — r/unstable_diffusion sweep, 2026-08-23]`. Worth knowing before you assume image-side craft carries over.
- **Either table measures which way an ecosystem leans, never what a model can do.** SDXL 1.0's ~31% of a vastly larger library is more material in absolute terms than any newer base's 60%.
- **One family is ruled out for a reason that is not capability.** [`ltx-2-5`](../../ltx-2-5/) is excluded by the acceptable-use policy written into its licence, which bans sexually explicit content everywhere, local weights included. That is absolute — no technical workaround changes a licence term.
- **[`ideogram-4`](../../ideogram-4/) used to sit in that sentence and no longer belongs there.** A filter and a licence are different shapes of obstacle. Its model-level filter is real and officially documented, but it is **leaky rather than absolute** — see the row below. Grouping a technical barrier with a legal one taught the wrong lesson about both.

What each family actually gives you:

| Family | Position | What to reach for |
|---|---|---|
| **SDXL ecosystem** | **Deepest by far.** Purpose-built finetunes with mature tooling and enormous existing LoRA libraries | See below |
| **Flux** | BFL **filtered the pre-training data** for NSFW and unlawful content. Capability comes from community finetunes, not the base | Community NSFW finetunes; verify licence and lineage |
| **Ideogram 4** | **Harder, not closed.** A model-level filter returns a blocked-image response, and it lives in the weights rather than in a wrapper you can strip out `[official — ideogram-oss/ideogram4]` — so it is not a training problem. But adult output *has* been posted from the open weights, with community style LoRAs loaded at 0.4 and a JSON caption `[community — Ashamed-Ad7403; single report]`, and **~26% of its 34 published LoRAs are now explicit**, against zero flagged on 2026-08-13 `[community — Civitai census, 2026-08-23]`. Nobody has shown *why* it gets through — whether a LoRA displaces the filtered behaviour, or the reports simply sit in the filter's false-negative margin `[flagged — re-verify]` | Route elsewhere for **reliable** adult work, and plan for the gray screen firing. Treat it as unsettled rather than impossible — and note the non-commercial weights licence constrains this path anyway. Filter evidence: [`ideogram-4`](../../ideogram-4/references/setup-and-workflows.md) §5 |
| **MiniMax H3** | Community reports no meaningful refusal. Failures show up as data gaps, and reportedly improve with reference images | Ref2VA reference conditioning before training |
| **Wan 2.2** | Active ecosystem — 40+ community LoRAs across T2V and I2V, AI-Toolkit support on consumer GPUs. Its low share in the 2026-08-23 census is the preview-image artefact above, not a verdict | Remember the two-expert rule |
| [`krea-2`](../../krea-2/) | **Well supported, and the image side's centre of gravity.** Both censuses agree (52% / 46%), and the practice matches: purpose-built adult checkpoints rather than base-plus-LoRA | An NSFW checkpoint over the stock base; Identity Edit for the character |
| [`z-image`](../../z-image/) | **Well supported**, and both censuses agree (46–47% / 45% Turbo). Anatomy-specific LoRAs exist, so the coverage is not incidental | Train on Base, run on Turbo — that skill's rule, unchanged here |
| [`anima`](../../anima/) | Rising fast, and unusual in that `nsfw` and `explicit` are **trained rating tags** rather than something you fight the model for | Tag the rating; do not reach for a capability LoRA first |

### The SDXL finetunes

This is the deepest ecosystem, and it is worth understanding as separate lineages rather than interchangeable options. The descriptions below are convergent community verdicts, not measurements. Nobody has benchmarked these finetunes against each other, and the ranking claims in particular move as new versions land:

| Finetune | Character `[community — Civitai model cards and comparisons; convergent]` |
|---|---|
| **NoobAI-XL V-Pred 1.0** | The most anatomically accurate, with the best tag comprehension and the highest community ELO `[flagged — re-verify]`. **Needs v-prediction sampler settings, and Euler specifically — other samplers will not work.** That trap costs people an evening |
| **WAI-NSFW v17** | The usual runner-up, and much easier to set up than v-pred NoobAI |
| **Illustrious** (v2.0 as a finetune base) | The **largest character-LoRA library**, which matters if you want compatibility with existing work |
| **Pony Diffusion V6 XL** | Heavy booru-tagged training with explicit examples. Tolerates arbitrarily long tag strings and stays coherent when tags conflict. Enormous LoRA ecosystem |

**Train against the base you will run on.** A LoRA trained on one of these finetunes and run on another transfers partially at best, because these lineages have diverged a long way. Where an ecosystem separates a training base from a runtime variant, follow that skill's guidance.

All of these are CLIP-class, tag-driven models. Captioning and trigger tokens follow the CLIP column of the conditioning doctrine — **verbatim rare tokens and weighted tags** — not the natural-sentence style newer DiTs want.

---

## 3. Captioning

**Caption the explicit content explicitly.** This is not a stylistic preference. It follows mechanically from caption-the-residual: anything that is constant across the dataset and missing from the captions gets absorbed into the concept you are training.

Caption an explicit dataset vaguely, or with euphemisms, and you teach the model that *the explicit content is the character*. The LoRA then produces explicit output whatever you prompt, and it cannot render the character clothed at all. This is one of the most common complaints about character LoRAs, and it is a captioning error rather than a base-model problem.

So:

- **Name acts, poses, states of dress and framing** in the caption, in the dialect the encoder wants — booru tags for CLIP-class finetunes, natural clauses for LLM-encoder DiTs.
- **Do not caption the identity.** The same rule as always applies: the face is the thing you are teaching.
- **Include clothed images in the dataset** if you want the character to be renderable clothed. A set that is uniformly explicit produces a character who cannot be anything else.
- **Balance the set.** Coverage of angle, expression and shot size matters just as much here — arguably more, since explicit datasets tend to be narrow in framing.

---

## 4. Anatomy failure modes

| Symptom | Cause | Direction of fix |
|---|---|---|
| Anatomy melts or is incoherent | Base model lacks the training data | Change base model; no encoder or conditioning trick fixes this |
| Character is *always* explicit | Explicit elements left uncaptioned, absorbed into the identity | Caption them; add clothed images |
| Character cannot be rendered explicit | The inverse — the dataset was uniformly clothed | Dataset coverage |
| Bodies right, faces wrong at distance | The face occupies too few pixels at generation resolution | Detailer pass; the identity LoRA at the detail stage |
| Proportions drift with pose | Narrow pose coverage in the dataset | Broaden pose and shot-size coverage |
| Output fights the prompt at high LoRA strength | Over-trained, or rank too high for the dataset | Earlier checkpoint; lower strength; reduce rank |
| Hands degrade specifically | A general weakness across this model class, made worse by how few pixels hands occupy | Detailer pass; inpaint; not a training fix |
| Likeness drops the moment an anatomy LoRA is loaded under it | Two adapters writing the same attention weights, and the broad one wins — see §1 | No settled recipe — test the stack before committing to the base |
| Two-woman scene grows male anatomy nobody prompted | Heteronormative training distribution; the model falls back on its prior, and negatives are the wrong-shaped lever — see §1 | Base with explicit configuration tags; or compose per figure rather than per frame — no verified fix |

**Detailer stages matter more here than in SFW work**, because the failures cluster in small regions: faces at distance, hands, fine anatomy. The production ladder in [`image-production-workflows`](../../image-production-workflows/) applies unchanged. The difference is that skipping the detail stage costs you more.

---

## 5. Video

Two things differ materially from image work.

**Automated captioners fail.** Vision-language captioners either refuse or produce useless euphemism on adult footage, so **the community captions adult video by hand.** Video datasets are already the expensive kind, because cost scales with clip count multiplied by frame handling. Hand captioning is therefore a real cost multiplier to budget for, not a detail. It is also a strong argument for **training on single frames** where you care about appearance rather than motion: you get the same curated stills, ordinary image captioning, and far less labour.

**Architecture still governs.** The rules from the model skill do not relax:

- Wan 2.2's MoE split means **two LoRAs from one dataset**, one per expert. The low-noise half carries appearance; the high-noise half carries motion and pose.
- H3 needs a **non-pruned checkpoint** to train at all.
- Speed and distill LoRAs change the sampling trajectory, so **evaluate without them loaded**, then check the combination separately, since that is how it will run.

**Listen to your evaluations as well as looking at them**, on any model that generates audio. A LoRA can sharpen visual identity while degrading voice or ambience, and frames alone will never show you that.
