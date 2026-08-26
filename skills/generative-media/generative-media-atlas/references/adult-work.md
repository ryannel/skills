# Adult work — which model, and the trade

Adult content is a dominant use of open-weights media models. This file treats it as a
capability axis, not a footnote to the licence section. **It only covers model choice and the
trade-offs involved.** The craft — datasets, captioning, anatomy failure modes, video specifics — belongs to
[`character-lora-training`](../../character-lora-training/) `references/nsfw-training.md`. That is
the deeper treatment, and you should read it alongside this one.

**Two lines are absolute, and neither is a licence question**: sexual content depicting minors, and
sexual imagery of real, identifiable people without their consent. The second is not just a
platform rule. Civitai bans real-person likeness outright, and the TAKE IT DOWN Act has been under
live FTC enforcement since 19 May 2026. Everything below assumes **invented adult characters**.

## Contents

1. [The ecosystem census, and what it does and does not measure](#1-the-ecosystem-census-and-what-it-does-and-does-not-measure)
2. [The stack people actually use, 2026-08](#2-the-stack-people-actually-use-2026-08)
3. [The anatomy-collapse study](#3-the-anatomy-collapse-study--the-most-transferable-finding-here)
4. [Two gaps worth knowing before you start](#4-two-gaps-worth-knowing-before-you-start)

---

## 1. The ecosystem census, and what it does and does not measure

Civitai `nsfwLevel` is a **bitmask over a model's preview images** (1 PG · 2 PG-13 · 4 R · 8 X ·
16 XXX). A model's value ORs together every level present. This table shows the share of the 600 most-downloaded
LoRAs per base whose previews include **X or XXX**, measured 2026-08-23
`[official — Civitai /api/v1/models, counted this pass]`. **Reproduce it rather than trust it.**
`python scripts/civitai_census.py --adult` re-runs this exact measurement, and its header documents
the traps below so you do not have to rediscover them:

| Base | explicit (X/XXX) | mature (R+) |
|---|---|---|
| **Pony** | **67%** | 87% |
| **Illustrious** | 56% | 82% |
| [`anima`](../../anima/) | 52% | 84% |
| **NoobAI** | 50% | 76% |
| [`krea-2`](../../krea-2/) | 46% | 76% |
| [`z-image`](../../z-image/) Turbo | 45% | 75% |
| FLUX.2 [klein] 4B | 41% | 68% |
| FLUX.1 dev | 37% | 61% |
| [`z-image`](../../z-image/) Base | 32% | 63% |
| [`sdxl`](../../sdxl/) 1.0 | 31% | 53% |
| FLUX.2 [klein] 9B | 30% | 57% |
| [`ideogram-4`](../../ideogram-4/) | 26% *(n=34)* | 35% |
| Qwen | 24% | 54% |
| [`wan-2-2`](../../wan-2-2/) T2V / I2V | 23% / 22% | 49% / 45% |
| [`minimax-h3`](../../minimax-h3/) | 23% *(n=22)* | 59% |
| Hunyuan Video | 20% | 34% |
| [`ltx-2-5`](../../ltx-2-5/) — 2.3 | 14% | 39% |

**Three warnings, because this metric is easy to over-read.**

- **It measures preview images, so it systematically undercounts video.** A video LoRA's preview is
  often a tame first frame or a motion demo. The LoRA itself can still be explicit and score PG. That is almost
  certainly why the video rows sit at the bottom here, even though r/unstable_diffusion's top-of-month is
  dominated by video. **Do not read the video rows as capability.**
- **It measures ecosystem tilt, not ceiling.** [`sdxl`](../../sdxl/) 1.0's 31% of a vastly larger
  library is more absolute material than a newer base's 60%.
- **The `nsfw` boolean in this API is dead.** It returns false for every model sampled, including
  ones whose previews are XXX. Any figure built on it is wrong. `[flagged — method matters here]`

> **This disagrees with the suite's existing table.**
> [`character-lora-training`](../../character-lora-training/) `references/nsfw-training.md` §2 (dated
> 2026-08-13, ~100 LoRAs per base) puts **Wan 2.2 I2V highest at 90%** and Flux lowest at 28% — close
> to the inverse of the ordering above. The methods differ, and neither is clean. The preview-image
> undercount above is the most likely explanation for the video half. **This is filed as a finding against
> that skill, not silently overridden.** Its qualitative claim — that adult work is a dominant
> published use of open *video* models — is still well supported by the Reddit evidence, whatever the metric
> says.

## 2. The stack people actually use, 2026-08

From a top-of-month sweep of r/unstable_diffusion, 2026-08-23.

**Image — [`krea-2`](../../krea-2/) dominates**, through purpose-built checkpoints rather than base
plus LoRA: `LUSTIFY!`, `FinePorn v3 TURBO`, `Moody Krea 2 Mix`. Reported settings are deliberately
unremarkable — Euler or **ER SDE**, **10 steps, guidance 1.0**. That is the point: the checkpoint
is doing the work `[community — Deep_Piece5371, convergent across posts]`. Krea 2 + Identity Edit plus
an NSFW LoRA is the named pattern for putting a consistent character into adult scenes
`[community — Clone-Protocol-66]`. [`z-image`](../../z-image/) and the
[`sdxl`](../../sdxl/) anime finetunes hold the rest.

**Character LoRAs are the one case where this ranking does not pick the base, because two different
rankings are answering two different questions.** The stack above is checkpoint-driven. It answers
*which base generates adult scenes best*. The suite's photoreal ranking (atlas, *Photoreal faces and
skin*) answers a different question — *which base holds a photoreal character LoRA best* — and it settles on
[`z-image`](../../z-image/). When the deliverable is a **character LoRA used in adult work**, the
photoreal ranking wins the base-model choice: train on Z-Image. Switching base to chase the table
above trades the settled photoreal #1, and the suite's fastest training loop, for a checkpoint
ecosystem that only matters at scene time. There is no adult handicap to justify the trade:
both censuses converge on ~45–47% adult share for Turbo, a point behind Krea 2, and anatomy LoRAs
exist for it. The checkpoint ecosystem re-enters at *scene* time, not training time. If base anatomy
proves insufficient (the §3 tell, where only the seed moves the result), compose the scene on the
adult-strong checkpoint. Then re-assert the character LoRA at the face/detailer pass, at ~0.2
denoise. That is the suite's ordinary cross-family finishing pattern, not an adult special case.
This is derived from the census above, plus a live routing test of this suite, 2026-08-23. It is a community bar
that rests on the census numbers rather than a published workflow.

**Video — [`minimax-h3`](../../minimax-h3/), decisively**, and it is not close:
*"far above LTX and Wan"*, *"the most powerful open source model"*
`[community — AidenAizawa, Revolutionary-Bar766, Hearmeman98; convergent]`. It reportedly runs at 540p
on a **3060 Ti 8 GB** with the turbo LoRA and SageAttention, and takes ~5–7 min for ~10 s at 1056×608 on a
5070 Ti. **Remember gate 3**: its licence excludes the US, EU, UK and South Korea. That means the community's
capability leader is one many readers cannot lawfully use, whatever the enthusiasm in those threads
says.

**H3 prompting, the parts that transfer** `[community — nsfwVariant, 427 pts]`:

- **Ref2VA over FL2VA** — more flexible: start/end frames become strong guides rather than fixed
  anchors, and you can add reference images, audio or video.
- **`then` for sequential, `while` for simultaneous.** The model assumes sequential when you do not
  say so — *"this lack of distinction about the sequence of events causes 80% of the jank."*
- **Timestamps** in `mm:ss.000`, placed next to the action they govern. Allow at least 3 s per garment for
  undressing sequences, described item by item.
- **Over-describe what the model gets wrong**, in gratuitous detail. H3 is adherent enough that
  hand-holding works where it does not on Wan.
- **More than 20 steps** (about 30) measurably reduces errors on complex physics, and improves audio.
  **~0.8 MP** is the reliability sweet spot.
- A **nude reference image** (or close-up anatomy references) is what makes undressing work. Base
  nudity without one is *"inconsistent & low quality"*.
- Scheduler **beta, not simple** — reported as a large-impact change — plus video sigma shift 12→15
  `[community — Revolutionary-Bar766]`.

**Licence-clean video is [`wan-2-2`](../../wan-2-2/)**: Apache-2.0, no acceptable-use clause at all.
[`ltx-2-5`](../../ltx-2-5/) is barred by its AUP universally. The adult LTX work visible in these
threads is on **2.3** — that is practice, not permission, since both candidate 2.3 texts incorporate the
same AUP.

## 3. The anatomy-collapse study — the most transferable finding here

A single-variable investigation into anatomy collapsing mid-clip on Wan I2V, over 27 generations
`[community — RedMimicStudios]`. **Everything deterministic failed to move it**: prompt phrasing and
eight anti-distortion negatives, 20 vs 12 steps, an NSFW LoRA at 1.0 vs bypassed, 49 vs 33 frames,
shift 6.5/7.0/8.0/9.0, and three retouched source images (<1/255 mean pixel delta). Only a 28-run seed
batch moved anything — **2 usable out of 28**.

> **The tell, and it generalises past adult work entirely: when seed variance dominates and nothing
> deterministic moves the needle, the answer is not in your settings. The base model cannot hold
> that composition.** Change the checkpoint.

Swapping to an NSFW-merged checkpoint fixed it in one run. The author's QC proxy is worth stealing:
**edge density, first frame to last, as a measure of detail decay**.

| Checkpoint | edge-density change | Result |
|---|---|---|
| Wan 2.2 Q4_K_M | **−10.1%** | anatomy broken |
| a "smooth motion" merge | **−27.3%** | anatomy fine, linework dissolved |
| Wan 2.2 I2V 10-step NSFW fp8 merge | **−3.2%** | both fine |

ESRGAN restoration on the smooth-merge output changed nothing (−28.2%). That **told them the late
frames had no detail left to recover — they were not merely blurred.** It ruled out a post-process problem
by measurement rather than by eye.

The merge author's working settings, and two traps inside them:

```
steps 10 (High 0–5 / Low 5–10)
cfg   2.0 HighNoise / 1.0 LowNoise   ← asymmetric; it is a CFG-distilled merge
sampler uni_pc / normal              ← not euler, and this mattered
shift 8.0 both stages
LoRA  none                           ← NSFW LoRAs are already merged in; stacking double-applies
1008×576, 49 frames, 16 fps  ·  ~41 min on a 3060 12 GB (fp8, 13.3 GB per stage, heavy offload)
```

**Both traps were in the workflow JSON and not in its description text** — the asymmetric CFG split
and `uni_pc`. Read the JSON, not the post.

## 4. Two gaps worth knowing before you start

- **Anatomy LoRAs and character LoRAs fight, and it is unresolved.** A practitioner worked through
  four published anatomy LoRAs on Wan I2V. Each either failed to render or *"changes the
  character lora too much"* `[community — One-Energy5403]`. The suite's standing advice is to stack a
  capability LoRA under the character LoRA. That is what people try when this happens, so treat
  it as a live constraint, not a solved recipe `[contested]`.
- **Same-sex and non-heteronormative scenes are a documented weak spot** across SDXL, Z-Image and
  Krea 2 alike: distorted anatomy and intrusive male anatomy show up in scenes that specify two women
  `[community — ricovelez; unanswered]`. This comes from dataset composition, not prompting. It follows
  this file's opening reframe exactly: the limit is data. Nothing in this suite currently addresses it,
  and no community answer surfaced in the sweep. `[flagged — open gap]`
