# Adult and NSFW LoRA training

Adult content is a dominant use of open-weights media models, and most of the difficulty around it is misdiagnosed. This file covers what actually determines results.

Read [`publishing-and-likeness.md`](publishing-and-likeness.md) first if a real person is anywhere near the dataset — that decides whether the work is distributable before any of this matters.

1. [The limit is data, not refusal](#1-the-limit-is-data-not-refusal)
2. [Base model selection by family](#2-base-model-selection-by-family)
3. [Captioning](#3-captioning)
4. [Anatomy failure modes](#4-anatomy-failure-modes)
5. [Video](#5-video)

---

## 1. The limit is data, not refusal

The single most useful reframe. Open-weights image and video models **do not generally refuse** — they produce poor anatomy because the base model saw little of it. What reads as censorship is usually absence.

This explains the ecosystem's most persistent myth. Many people swap the text encoder for an abliterated ("heretic") build expecting it to unlock capability. **It does not, and the author of the leading abliteration tool has said so directly:**

> Abliteration works by directional ablation on the residual stream so an LLM stops *refusing*. But LLMs already represent "harmful" inputs accurately — that is how they know to refuse. The hidden states reaching the diffusion model are therefore not clearer, they are **perturbed relative to what it was trained on**, costing prompt adherence and sometimes adding artefacts. `[community — -p-e-w-, author of Heretic]`

Corroborating: the encoder builds shipped with some models are physically **smaller than stock because the output layers are absent** — refusal lives in those layers, and a text encoder never uses them. There is no refusal path present to remove.

**Where abliterated models genuinely help: prompt expansion.** An LLM asked to *enhance* a prompt can refuse outright, and several official ComfyUI templates ship such an expander enabled by default. That is a separate stage before the encoder, and swapping it is legitimate.

The confusion is usually structural: a template's subgraph wires **the same LLM** into both the expander and the text-encode node, so a swap intended to fix the refusing expander silently changes the encoder too. Unpack the subgraph and point the abliterated model at the expander only.

**So: if anatomy is poor, change the base model or train it in. No conditioning trick substitutes for training data.**

### But "train it in" is a different job at a different scale

This is the distinction that catches people, and it is worth being blunt about because the two are constantly confused:

| | **Character LoRA** | **Capability / concept LoRA** |
|---|---|---|
| Teaching | *who someone is* on a base that already renders bodies | *anatomy the base model largely lacks* |
| Dataset | **15–30** curated images (up to ~100 for broad-coverage character work) | **1,500+** handpicked, carefully captioned images — "a small dataset of 100–300 won't do it" |
| Rank | 8–64 | **128 minimum** |
| Effort | An afternoon | A project |

`[community — Qwen-Image NSFW LoRA notes, Civitai]`

The practical consequence: **if your base lacks the coverage, do not try to fix it with a character LoRA.** You will produce a LoRA that half-works and blame the settings. Either pick a base that already has the coverage (§2), or stack an existing general-purpose capability LoRA *underneath* your character LoRA and let each do its own job.

That layering is the normal production pattern, and it is why the good-citizen advice in `../SKILL.md` matters — a character LoRA that demands 1.0 cannot coexist with the anatomy LoRA it needs.

**Merging as an alternative to stacking.** Where several capability LoRAs are being combined, published tooling merges them into a single "meta-LoRA" by **rank concatenation** — concatenating the A and B matrices with each contribution scaled by `√(weight × alpha/rank)`. Worth knowing two things if you go there: rank adds up, so the merged file is the sum of its parts, and **naming conventions differ** — Kohya-style `.lora_down.weight` / `.lora_up.weight` / `.alpha` versus PEFT-style `.lora_A.weight` / `.lora_B.weight`. A merge script that assumes the wrong one silently finds no modules to merge.

---

## 2. Base model selection by family

Base choice dominates every other decision here — more than rank, more than steps, more than captioning.

| Family | Position | What to reach for |
|---|---|---|
| **SDXL ecosystem** | **Deepest by far.** Purpose-built finetunes with mature tooling and enormous existing LoRA libraries | See below |
| **Flux** | BFL **filtered the pre-training data** for NSFW and unlawful content. Capability comes from community finetunes rather than the base | Community NSFW finetunes; verify licence and lineage |
| **Ideogram 4** | Hard **model-level** filter that returns a blocked-image response. Not a training problem — the filter is in the weights | Route elsewhere entirely |
| **MiniMax H3** | Community reports no meaningful refusal; failures present as data gaps and reportedly improve with reference images | Ref2VA reference conditioning before training |
| **Wan 2.2** | Active ecosystem — 40+ community LoRAs across T2V and I2V, AI-Toolkit support on consumer GPUs | Remember the two-expert rule |
| **Z-Image, Krea 2** | **Not well documented either way.** Test before committing a run `[flagged — re-verify]` | — |

### The SDXL finetunes

The deepest ecosystem, and worth understanding as distinct lineages rather than interchangeable options:

| Finetune | Character |
|---|---|
| **NoobAI-XL V-Pred 1.0** | Reported as the most anatomically accurate with the best tag comprehension and highest community ELO. **Requires v-prediction sampler settings and Euler specifically — other samplers will not work.** That trap costs people an evening |
| **WAI-NSFW v17** | The usual runner-up; substantially easier setup than v-pred NoobAI |
| **Illustrious** (v2.0 as a finetune base) | The **largest character-LoRA library**, which matters if you want compatibility with existing work |
| **Pony Diffusion V6 XL** | Heavy booru-tagged training with explicit examples; tolerates arbitrarily long tag strings and stays coherent when tags conflict. Enormous LoRA ecosystem |

**Train against the base you will run on.** A LoRA trained on one of these and run on another will transfer partially at best — these lineages have diverged substantially. Where an ecosystem distinguishes a training base from a runtime variant, follow that skill's guidance.

All of these are CLIP-class, tag-driven models. Captioning and trigger-token handling follow the CLIP column of the conditioning doctrine — **verbatim rare tokens, weighted tags** — not the natural-sentence style newer DiTs want.

---

## 3. Captioning

**Caption the explicit content explicitly.** This is not a stylistic preference, it follows mechanically from caption-the-residual: anything constant across the dataset and absent from the captions is absorbed into the concept you are training.

Caption an explicit dataset vaguely or euphemistically and you teach the model that *the explicit content is the character*. The LoRA then produces explicit output regardless of prompt, and cannot produce the character clothed. This is one of the most common complaints about character LoRAs, and it is a captioning error rather than a base-model problem.

So:

- **Name acts, poses, states of dress and framing** in the caption, in the dialect the encoder wants — booru tags for CLIP-class finetunes, natural clauses for LLM-encoder DiTs.
- **Do not caption the identity.** Same rule as always: the face is what you are teaching.
- **Include clothed images in the dataset** if you want the character to be renderable clothed. A dataset that is uniformly explicit produces a character that cannot be anything else.
- **Balance the set.** Coverage of angle, expression and shot size matters exactly as much here — arguably more, since explicit datasets tend to be narrow in framing.

---

## 4. Anatomy failure modes

| Symptom | Cause | Direction of fix |
|---|---|---|
| Anatomy melts or is incoherent | Base model lacks the training data | Change base model; no encoder or conditioning trick fixes this |
| Character is *always* explicit | Explicit elements left uncaptioned, absorbed into the identity | Caption them; add clothed images |
| Character cannot be rendered explicit | Inverse — the dataset was uniformly clothed | Dataset coverage |
| Bodies right, faces wrong at distance | Face occupies too few pixels at generation resolution | Detailer pass; the identity LoRA at the detail stage |
| Proportions drift with pose | Narrow pose coverage in the dataset | Broaden pose and shot-size coverage |
| Output fights the prompt at high LoRA strength | Over-trained, or rank too high for the dataset | Earlier checkpoint; lower strength; reduce rank |
| Hands degrade specifically | General weakness across this model class, compounded by the resolution the hands occupy | Detailer pass; inpaint; not a training fix |

**Detailer stages carry more weight here than in SFW work**, because the failures cluster in small regions — faces at distance, hands, fine anatomy. The production ladder in [`image-production-workflows`](../../image-production-workflows/) applies unchanged; the difference is that skipping the detail stage costs more.

---

## 5. Video

Two things differ materially from image work.

**Automated captioners fail.** Vision-language captioners either refuse or produce useless euphemism on adult footage, so **the community captions adult video manually**. Since video datasets are already the expensive kind — clip count multiplied by frame handling — this is a real cost multiplier to budget for, not a detail. It is also a strong argument for **single-frame training** where the target is appearance rather than motion: the same curated stills, ordinary image captioning, far less labour.

**Architecture still governs.** The rules from the model skill do not relax:

- Wan 2.2's MoE split means **two LoRAs from one dataset**, one per expert — and the low-noise half carries appearance while the high-noise half carries motion and pose.
- H3 requires a **non-pruned checkpoint** to train at all.
- Speed/distill LoRAs alter the sampling trajectory, so **evaluate without them loaded**, then check the combination separately since that is how it will run.

**Listen to your evaluations**, not just look at them, on any model that generates audio. A LoRA can sharpen visual identity while degrading voice or ambience, and frames alone will not show it.
