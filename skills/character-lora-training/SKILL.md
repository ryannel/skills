---
name: character-lora-training
description: >
  Train a character LoRA that holds an identity across prompts, poses and models — the cross-model craft that every model skill in this suite otherwise repeats. Use this whenever the user is building, debugging or planning a LoRA, even obliquely: assembling and curating a dataset, deciding how many images, captioning (and the character-vs-style inversion that decides what a LoRA actually learns), picking rank/alpha/LR/steps as starting points, **evaluating a finished run** — which checkpoint to ship, how to build and read an XY/checkpoint grid, which comparison tool to use, whether a run over- or under-fit, how to score likeness objectively — holding likeness across a multi-stage pipeline or into video, or choosing which base model to train on in the first place. It covers **adult/NSFW work as a first-class case** — which base models actually have the training data (the limit is nearly always data, not refusal), why explicit captioning is mandatory rather than optional, anatomy failure modes, and why automated captioners fail on adult video. It also covers what determines whether a LoRA is **publishable at all**: Civitai's total ban on real-person likeness (SFW and NSFW alike) and the TAKE IT DOWN Act's live FTC enforcement, both of which constrain dataset sourcing and distribution. Per-model hyperparameters, trainer flags and quirks live in the model skills — this owns what transfers.
---

# Character LoRA training

A character LoRA succeeds when the identity survives contact with prompts it never saw. Everything below serves that test.

**This skill owns what transfers between models.** Exact hyperparameters, trainer support and architecture quirks belong to each model skill — and some of those quirks are load-bearing, so check yours before starting:

| Model | The thing you cannot skip |
|---|---|
| [`sdxl`](../sdxl/) | Base-model choice dominates everything — the finetune you train on decides your ceiling |
| [`z-image`](../z-image/) | Train on Base, deploy via the detailer swap; Ostris AI-Toolkit is the trainer |
| [`flux-2`](../flux-2/) | Licence split across variants; BFL filtered the pre-training data |
| [`krea-2`](../krea-2/) | Train on Raw, run on Turbo |
| [`wan-2-2`](../wan-2-2/) | **Two LoRAs** — one per MoE expert — from one dataset |
| [`minimax-h3`](../minimax-h3/) | Train on a **non-pruned** checkpoint; doctrine otherwise unsettled |

---

## Before anything: can you publish it?

This section leads because it decides whether the work is usable, and because the ground moved recently enough that most guides still predate it.

**Civitai prohibits real-person likeness entirely.** Verbatim: *"Content that depicts, or is based on the likeness of real people - living or deceased - including public figures, celebrities, influencers, and private individuals, is strictly prohibited."* Applies to **SFW and NSFW alike**. Covers historical figures. Covers fictional characters rendered as the actor who played them. **There is no consent exception** — consent given in one context does not transfer, and training on a real face is prohibited even when the output is a fictional character.

**The TAKE IT DOWN Act is live.** Signed May 2025; covered platforms had until **19 May 2026** to implement 48-hour notice-and-removal; **FTC enforcement began 19 May 2026**, with civil penalties around **$53,088 per violation**. It reaches AI-generated NCII depicting real people where the output is *"indistinguishable from an authentic visual depiction."*

What this means concretely for training:

- **A dataset of a real person is a dead end for distribution**, whatever your intent — the main model host will not take it and the legal exposure on the NSFW side is now federal and enforced.
- **The test is resemblance, not provenance.** A synthetic character is fine even though the base model was trained on photographs of real people. What is not fine is a character that resembles an identifiable individual. Provenance of the *base model* is not the question; resemblance of the *output* is.
- **"It's a lookalike, not them"** is exactly the case the actor clause closes. If people recognise who it resembles, treat it as covered.
- **Private commissions and self-portraits are still your own call** — the platform rule governs distribution, and the law governs intimate imagery of others. Those are different constraints; know which one you are under.

Full treatment, including dataset provenance and the synthetic-character question: **`references/publishing-and-likeness.md`**.

---

## The one rule that changes everything

**Caption the residual — describe what varies, never what you are teaching.**

A LoRA learns whatever is *constant across the dataset and absent from the captions*. That single sentence explains most training outcomes, and it inverts between the two jobs:

| | Character LoRA | Style LoRA |
|---|---|---|
| Constant across the set | **the person** | **the style** |
| Therefore: never caption | the face, the identity | the rendering, the medium |
| Therefore: always caption | pose, outfit, framing, lighting, setting, expression | subject, composition, everything depicted |
| Dataset diversity in | everything *except* the person | subjects, above all else |

Caption the face and you teach the model that this face is optional. Fail to caption the red jacket the subject wears in twenty of thirty images and the jacket becomes part of the character.

**A trigger token gives you a handle.** On CLIP-class encoders it wants to be a rare literal token used verbatim. On LLM/T5-class encoders it belongs folded into a natural phrase, or omitted entirely — bare rare tokens confuse a language encoder. This is determined by the encoder class, not by preference; see the conditioning doctrine in your model skill.

---

## The dataset

**Quality and coverage beat volume.** The consistent community finding is that **15–30 well-curated images outperform 100 mediocre ones**. More images do not fix a dataset that lacks angular coverage; they just cost more steps.

**The coverage protocol** — the thing that actually determines whether the identity generalises:

- **8-point rotation** around the head: front, three-quarter left and right, profile left and right, and the rear three-quarters. Missing angles is the number-one cause of a LoRA that collapses to one pose.
- **Elevation** — at least one above and one below eye level.
- **Shot sizes** — close-up, medium, full body. A face-only dataset produces a character with no body.
- **Expressions** — neutral plus at least two others, or you get expression lock-in.
- **Lighting and setting variety** — otherwise those bake into the identity.

**Vary one clause at a time.** When generating a dataset synthetically, hold the character description fixed and vary only the rotation/shot/expression clause. Anything else that drifts becomes part of what the model learns.

**The chained approach is now standard**: lock an anchor image, use an edit model to generate the varied set from it, curate hard, then train. That gives you coverage that photography rarely does — and it sidesteps the likeness problem entirely, because the character never existed.

Full dataset craft, curation criteria and the synthetic-generation loop: **`references/dataset-and-captioning.md`**.

---

## Hyperparameters as starting points

These are the shape of the consensus, not settings to copy — every model skill gives its own, and they differ.

| Parameter | Typical starting range | Notes |
|---|---|---|
| Rank | **8–32** | Higher captures fine detail and overfits faster. 4–16 is typical on newer DiTs; 32–64 on SDXL-era |
| Alpha | half of rank, commonly | Interacts with LR — changing one means re-tuning the other |
| Learning rate | **~1e-4** | Lower for larger ranks and larger models |
| Steps | **1500–3000** | Scale with dataset size; ~3000 for a 5–15 image set is a reported anchor |
| Batch | 1–2 on 16–24 GB | |

**Save checkpoints throughout and evaluate them as a series.** The best epoch is rarely the last, and this is the single highest-value habit in training — a run with intermediate checkpoints gives you a choice; a run with only a final gives you a verdict.

---

## Evaluating a run

**Loss is a weak signal.** It tells you the model is fitting; it does not tell you whether the identity generalises.

Three layers, cheapest first:

1. **Training samples** — free, already on. Fix the seed and use 3–5 prompts, and they show you *roughly where the useful region is* so the next layer can be small. Don't pick a final checkpoint from them: the trainer's sampler isn't your production one.
2. **A grid: checkpoint × strength**, fixed prompts and seed, generated in the tool you will actually ship from. This is the only step that costs real compute — narrow the checkpoint range using layer 1 first.
3. **Judge it blind.** The grid is labelled by design, so you know which cell trained longer before you look at it. Shuffle the candidates unlabelled, pick, then reveal. This costs nothing and routinely reverses the answer the labelled grid gave.

**Three habits that decide whether the evaluation is worth anything:**

- **Probe out of distribution, or you have tested nothing.** Put the character somewhere unlike anything in the dataset — a costume, a painted style, a wide shot where the face is small. A LoRA that only holds on near-copies of its training data memorised rather than learned, and in-domain prompts cannot tell you which happened.
- **Write the probe prompts before you see any results, and reuse the set across runs.** Prompts invented while browsing outputs drift toward what the LoRA already does well. A fixed set is also the only way run 3 becomes comparable to run 1.
- **Score likeness and prompt-adherence separately** — they peak at *different* checkpoints, reliably, because likeness keeps improving after flexibility has begun to die. One "which is best?" silently averages two axes moving in opposite directions.
- **A prompt that fails on every checkpoint is a dataset finding, not a checkpoint finding.** No epoch choice fixes missing profile coverage. Those prompts are the specification for your next dataset.

**Numbers are a screen, not a verdict.** `FaceEmbedDistance` (from `ComfyUI_FaceAnalysis`) is the reachable quantitative signal — but calibrate a baseline from real photos first, and know that DINO/CLIP-I-family similarity metrics are **documented as significantly misaligned with human judgement** on exactly this task, and inflate when a LoRA overfits pose.

Tools, a copy-pasteable starter probe set, the cost arithmetic, and what is worth building yourself: **`references/evaluation-and-tooling.md`**.

Two further tests worth running before shipping:

- **Strength sweep.** A healthy character LoRA has a usable band, not a knife-edge. If only 1.0 works, it is over-trained.
- **Stack test**, if it will run with others — a "good citizen" LoRA does not blow out when combined.

| Signal | Diagnosis | Fix |
|---|---|---|
| Same face, same pose, every prompt | Overfit, or angular coverage missing | Earlier checkpoint; lower strength; fix the dataset's rotation coverage |
| Background or clothing from the dataset bleeding in | Uncaptioned constants absorbed into the concept | Caption those elements; diversify |
| Weak likeness at any strength | Underfit, or captions describe the face | More steps; remove identity words from captions |
| Works at 1.0, breaks at 0.8 | Over-trained — no usable band | Earlier checkpoint |
| Expression frozen | No expression variety in the set | Add expressions; reduce strength |
| Style drifts toward the dataset's look | Dataset lacks lighting/setting variety | Diversify, or accept and caption it |

---

## Adult and NSFW work

Treated as a first-class case because it is a dominant use of open-weights models, and because most of the difficulty is misdiagnosed.

**The limit is training data, not refusal.** Open-weights image and video models do not generally refuse — they produce poor anatomy when the base model never saw much of it. This is why the widespread practice of swapping in an abliterated ("heretic") text encoder does not work: abliteration removes an LLM's ability to *refuse*, and refusal lives in output layers a text encoder never uses. You get perturbed conditioning and slightly worse prompt adherence, and no new capability. Use abliterated models for **prompt expansion** if a prompt-enhancer LLM is refusing — a separate stage, before the encoder.

**So base-model choice dominates**, and the families differ sharply:

A useful proxy for "does this base support the work": **the share of its published LoRAs that are adult-flagged.** Sampled from Civitai's model API, 2026-08-13, ~100 LoRAs per base:

| Family | Adult-flagged share | Position |
|---|---|---|
| **Wan 2.2 I2V** | **90%** | The highest density in the suite by a wide margin |
| **Wan 2.2 T2V** | **84%** | Active, mature ecosystem |
| **MiniMax H3** | **62%** | 77 LoRAs within days of release. Corroborates "no meaningful refusal" |
| **Krea 2** | **52%** | Well supported in practice |
| **Z-Image** (Turbo and Base alike) | **46–47%** | Well supported, including anatomy-specific LoRAs |
| **SDXL / Pony / Illustrious** | 29–34% | Lower *share*, far larger absolute ecosystem, and the purpose-built finetunes live here |
| **Anima** | 29% | Rising fast — the most common base in a newest-first pull |
| **Flux** | 28% | Despite BFL **filtering the pre-training data** — the community-finetune route works |
| **Ideogram 4** | — | Hard model-level filter. Route elsewhere entirely |

Read the percentages carefully: they measure *ecosystem tilt*, not capability ceiling. SDXL's 31% of a vastly larger library is more absolute material than Wan's 90% of a newer one, and SDXL is still where the purpose-built finetunes are. What the video numbers do show is that **adult work is the dominant published use of open video models**, which is worth knowing before assuming the craft transfers from the image side.

**Caption explicitly.** This follows directly from caption-the-residual and is not a stylistic choice: uncaptioned elements are absorbed into the invariant concept. Vague or euphemistic captions on an explicit dataset teach the model that the explicit content *is the character*, which is exactly the failure people then blame on the base model.

**Automated captioners fail here**, and the community captions adult video manually. Budget for it — it is a real cost multiplier on video datasets, where the frame count is already the expensive part.

Anatomy-specific failure modes, per-family base selection, and video specifics: **`references/nsfw-training.md`**.

---

## How to read the claims in this skill — two bars, by claim type

**Hard facts — must be exact or it breaks.** Civitai's real-person policy (quoted from their published rules), the TAKE IT DOWN Act's dates, enforcement start and penalty scale, and the mechanism by which abliteration fails as an encoder swap. **Sources are official or primary** — platform policy pages and legal-practice summaries of the statute. These carry legal and account consequences, and the regulatory picture is **moving**: state-level deepfake law is still landing and platform policies follow it. **Re-verify before relying on any of it, and treat this as orientation rather than legal advice.**

**Craft — what actually makes a good LoRA.** Caption-the-residual and its inversion, the coverage protocol, 15–30 curated images beating 100, hyperparameter ranges, XY-grid evaluation, the overfit signals. **The authoritative source here is the community** — named trainers who have run hundreds of these — and it is stated with confidence. Ranges mean "your dataset and base differ from theirs," not "this is unreliable."

Two things held as genuinely open:

- **Z-Image and Krea 2's adult-content position** is not well documented either way. `[flagged — re-verify]`
- **Optimal rank for character work** is contested across families and has been for years — the ranges above bracket the disagreement rather than resolving it. `[contested]`

Dated **2026-08-13**.

---

## Reference files

| File | When to read it |
|---|---|
| `references/dataset-and-captioning.md` | Building the set: the 8-point rotation protocol in full, elevation and shot-size coverage, curation criteria, the synthetic dataset-factory loop, caption formats by encoder class, and multi-outfit / multi-character limits |
| `references/nsfw-training.md` | Adult work in depth: per-family base-model selection and what each ecosystem offers, why the encoder-swap myth persists and what to do instead, explicit-captioning practice, anatomy failure modes, and the manual-captioning cost on video datasets |
| `references/evaluation-and-tooling.md` | Judging a finished run at home: which grid tool to use (SwarmUI Grid Generator, Efficiency Nodes, X/Y/Z plot) and their limits, the blind-judging pass, a copy-pasteable held-out probe set, `FaceEmbedDistance` with baseline calibration and why the metric misleads, cost arithmetic for rented GPUs, and the small script worth writing yourself |
| `references/publishing-and-likeness.md` | What determines whether a LoRA is publishable: Civitai's rules in full, the TAKE IT DOWN Act, dataset provenance, the synthetic-character resemblance test, and where distribution is still open |
