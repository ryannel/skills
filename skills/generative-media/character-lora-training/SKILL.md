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
| [`anima`](../anima/) | **Do not train the LLM adapter** (`llm_adapter_lr 0`) — it rewrites prompt understanding globally and presents as "Anima got worse", not as a broken LoRA |
| [`ltx-2-5`](../ltx-2-5/) | Your LoRA is a **Derivative** — it inherits the licence, and the obligation travels to whoever you give it to |

---

## Before anything: can you publish it?

This section leads because it decides whether the work is usable at all, and because the ground moved recently enough that most guides still predate it.

**Civitai prohibits real-person likeness entirely** — *"living or deceased … including public figures, celebrities, influencers, and private individuals"* — **SFW and NSFW alike**, historical figures included, and fictional characters rendered as the actor who played them. **There is no consent exception.** `[official — Civitai content rules, read 2026-08-13; re-verify]`

**The TAKE IT DOWN Act is live.** Signed May 2025; **FTC enforcement began 19 May 2026**, the same date platforms had to implement 48-hour notice-and-removal, with civil penalties around **$53,088 per violation**. It reaches AI-generated NCII depicting real people where the output is *"indistinguishable from an authentic visual depiction."*

Three consequences for training:

- **A dataset of a real person is a dead end for distribution**, whatever your intent — the main host will not take it, and the exposure on the NSFW side is now federal and enforced.
- **The test is resemblance, not provenance.** A synthetic character is fine even though the base model learned from photographs of real people; a character resembling an identifiable individual is not. **"It's a lookalike, not them"** is exactly the case the actor clause closes.
- **Private commissions and self-portraits are your own call** — the platform rule governs distribution, the law governs intimate imagery of others. Know which constraint you are under.

Full treatment, dataset provenance, and the synthetic-character question: **`references/publishing-and-likeness.md`**.

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

**Quality and coverage beat volume.** **15–30 well-curated images outperform 100 mediocre ones** — a finding that survives every base family it has been tested on, from NanashiAnon's Illustrious-era 20–30 figure to L3n4's "a well-curated 30–50 beats a poorly curated 500" `[community — NanashiAnon, L3n4/Civitai 25645; convergent]`. More images do not fix a dataset that lacks angular coverage; they just cost more steps.

**The coverage protocol** is what actually decides whether the identity generalises, and it runs on five axes `[community — MyAIForce, Civitai guides 5301/6990; convergent]`:

- **8-point rotation** around the head — front, three-quarter and profile each side, and the rear angles. Missing angles is the number-one cause of a LoRA that collapses to one pose, and the rear views are the ones people skip.
- **Elevation** (one above, one below eye level), **shot size** (close-up, medium, full body), **expression** (neutral plus two), and **lighting and setting variety**. Each omission has the same shape: whatever never varies becomes part of the identity. A face-only set gives you a character with no body; a single-expression set gives you expression lock-in.

Full protocol with the exact angle clauses: **`references/dataset-and-captioning.md` §2**.

**Vary one clause at a time.** When generating synthetically, hold the character description fixed and vary only the rotation/shot/expression clause. Anything else that drifts becomes part of what the model learns.

**The chained approach is now standard**: lock an anchor image, use an edit model to generate the varied set from it, curate hard, then train. That gives coverage photography rarely does — and it sidesteps the likeness problem entirely, because the character never existed.

**A video model is now a viable dataset factory**, and it *solves* the 8-point rotation problem rather than approximating it: prompt a slow 360° turnaround with no cuts, then cut the clip into frames. The coverage is continuous and internally consistent by construction, because it is one camera move rather than several independent generations. Two things to know before reaching for it — it is expensive in generated frames, and video stills are lower-detail than image stills — and one that is easy to miss: **check the licence of the model you harvest from**, because some restrict using their output to train anything else. [`ltx-2-5`](../ltx-2-5/)'s Attachment A ¶18 is exactly that, and its scope against non-commercial work is unsettled `[contested]`.

Full dataset craft — curation criteria, the synthetic-generation loop, the video turnaround in detail, captioning by encoder class, and the multi-character options: **`references/dataset-and-captioning.md`**.

---

## Hyperparameters as starting points

These are the shape of the consensus, not settings to copy — every model skill gives its own, and they differ.

| Parameter | Typical starting range `[community — neonkisu, QuantumBogoSort, L3n4/Civitai 25645]` | Notes |
|---|---|---|
| Rank | **8–32** | Higher captures fine detail and overfits faster. 4–16 is typical on newer DiTs; 32–64 on SDXL-era. Genuinely disputed — see the two-bar section `[contested]` |
| Alpha | half of rank, commonly | Interacts with LR — changing one means re-tuning the other |
| Learning rate | **~1e-4** | Lower for larger ranks and larger models |
| Steps | **1500–3000** | Scale with dataset size; ~80–100 steps per image is the durable rule of thumb behind that range |
| Batch | 1–2 on 16–24 GB | When you drop batch to fit, hold `batch × gradient_accumulation` constant |

**Save checkpoints throughout and evaluate them as a series.** The best epoch is rarely the last, and this is the single highest-value habit in training — a run with intermediate checkpoints gives you a choice; a run with only a final gives you a verdict.

**The home-training floor has moved, and it changes the economics.** 16–24 GB is the band for the suite's mainstream models, which is why renting ([`comfyui-on-runpod`](../comfyui-on-runpod/)) is the usual answer. [`anima`](../anima/) breaks it: LoRA training fits in roughly **6 GB at 768 px** `[community — citronlegacy, Civitai 26217; convergent]`. That matters beyond anime work, because the real bottleneck here is the three failed runs it takes to learn what a dataset is missing — and at 6 GB those are free.

---

## Evaluating a run

**Loss is a weak signal.** It tells you the model is fitting; it does not tell you whether the identity generalises. Judge on images, in three layers, cheapest first:

1. **Training samples** — free, already on. Fix the seed, use 3–5 prompts, and read them only to find *roughly where the useful region is*, so the next layer can be small. Never pick a final checkpoint here: the trainer's sampler is not your production one.
2. **A grid: checkpoint × strength**, fixed prompts and seed, generated in the tool you will ship from. The only step that costs real compute — narrow the range with layer 1 first.
3. **Judge it blind.** The grid is labelled by design, so you know which cell trained longer before you look. Shuffle the candidates unlabelled, pick, then reveal. Costs nothing, and routinely reverses the labelled grid's answer.

**Three habits decide whether any of that is worth anything** `[community — production practice; convergent]`:

- **Probe out of distribution, or you have tested nothing.** Put the character somewhere unlike the dataset — a costume, a painted style, a wide shot where the face is small. A LoRA that only holds on near-copies of its training data memorised rather than learned, and in-domain prompts cannot tell you which.
- **Write the probe prompts before you see results, and reuse the set across runs.** Prompts invented while browsing outputs drift toward what the LoRA already does well, and a fixed set is the only way run 3 becomes comparable to run 1.
- **Score likeness and prompt-adherence separately** — they peak at *different* checkpoints, because likeness keeps improving after flexibility has begun to die. One "which is best?" silently averages two axes moving in opposite directions.

**Numbers are a screen, not a verdict.** `FaceEmbedDistance` (from `cubiq/ComfyUI_FaceAnalysis`) is the reachable quantitative signal — but calibrate a baseline from real photos first, and know that DINO/CLIP-I-family metrics are **documented as significantly misaligned with human judgement** on exactly this task, the central result of **DreamBench++** (ICLR 2025) `[official — published benchmark]`. They also inflate when a LoRA overfits pose, so a rising score late in a run can be measuring memorisation.

Two cheap tests before shipping: a **strength sweep** (a healthy LoRA has a usable band, not a knife-edge) and a **stack test** if it will run alongside others.

Grid tooling, a copy-pasteable probe set, the cost arithmetic, and what is worth building yourself: **`references/evaluation-and-tooling.md`**.

---

## Failure modes & QC

Read the cause column and notice the pattern: nearly every one is a **dataset or caption** finding wearing a hyperparameter costume.

| Signal | Cause (mechanism) | Fix |
|---|---|---|
| Same face, same pose, every prompt | Overfit, or the rotations were never in the set — the model can only reproduce angles it saw | Earlier checkpoint; lower strength; fix rotation coverage |
| Background or clothing bleeding in | Uncaptioned constants absorbed into the concept — the LoRA learns whatever is constant and unnamed | Caption those elements; diversify |
| Weak likeness at any strength | Underfit, or the captions name the face, which makes the identity optional | More steps; remove identity words from captions |
| Works at 1.0, breaks at 0.8 | Over-trained — the weights have moved too far for partial application to stay coherent | Earlier checkpoint |
| Expression frozen | No expression variety, so expression is part of the invariant | Add expressions; reduce strength |
| Style drifts toward the dataset's look | No lighting/setting variety, so the lighting is part of the identity | Diversify, or accept and caption it |
| *Always* explicit, cannot be rendered clothed | Explicit elements left uncaptioned or euphemised, so they became the character | Caption explicitly; add clothed images (`references/nsfw-training.md` §3) |
| Fine alone, blows out when stacked | Not a good citizen — its usable band is a knife-edge, so any added weight overshoots | Retrain shorter; run the stack test *before* shipping |
| A prompt fails at every checkpoint and strength | Not a checkpoint problem — the coverage it needs is absent from the dataset | Note the prompt; it specifies your next dataset |

---

## Adult and NSFW work

Treated as a first-class case because it is a dominant use of open-weights models, and because most of the difficulty is misdiagnosed.

**The limit is training data, not refusal.** Open-weights models do not generally refuse — they produce poor anatomy when the base never saw much of it. This is why swapping in an abliterated ("heretic") text encoder does not work, and the author of the leading abliteration tool says so directly: abliteration removes an LLM's ability to *refuse*, and refusal lives in output layers a text encoder never uses `[community — -p-e-w-, author of Heretic]`. You get perturbed conditioning, slightly worse prompt adherence, and no new capability. Use abliterated models for **prompt expansion** if a prompt-enhancer LLM is refusing — a separate stage, before the encoder.

**So base-model choice dominates.** A useful proxy for "does this base support the work": **the share of its published LoRAs that are adult-flagged**, sampled ~100 per base `[community — Civitai models API, 2026-08-13]`. The spread runs from **Wan 2.2 I2V at 90%** down through Z-Image and SDXL in the 30–47% band to **Flux at 28%**, with two models ruled out for reasons that are not capability at all: **Ideogram 4** by a hard model-level filter, and [`ltx-2-5`](../ltx-2-5/) by its acceptable-use policy, which prohibits explicit content universally — local weights included. Full table, per-family: **`references/nsfw-training.md` §2**.

Read those percentages carefully, because the obvious reading is wrong: they measure *ecosystem tilt*, not capability ceiling. SDXL's ~31% of a vastly larger library is more absolute material than Wan's 90% of a newer one, and SDXL is still where the purpose-built finetunes are. What the video numbers do show is that **adult work is the dominant published use of open video models**.

**Caption explicitly.** Not a stylistic choice: uncaptioned elements are absorbed into the invariant concept, so euphemistic captions teach the model that the explicit content *is the character* — the failure people then blame on the base model.

**Automated captioners fail here**, and the community captions adult video manually — a real cost multiplier on datasets where frame count is already the expensive part.

Anatomy failure modes, the full per-family table, and video specifics: **`references/nsfw-training.md`**.

---

## Pre-flight checklist

Most training checklists start at the config file. This one starts three steps earlier, because a config mistake costs one run, while a likeness problem costs the project and no step count trains around missing angular coverage.

1. **Publishable?** If a real person is anywhere near the dataset, settle it now — Civitai bans real-person likeness at every rating, and the TAKE IT DOWN Act is in force (`references/publishing-and-likeness.md`).
2. **Base chosen for the job, not for familiarity** — against the axes that actually differ: adult coverage, multi-character support, and the VRAM floor you can afford.
3. **Per-model trap read**, from the boundary table above. Wan's two experts, H3's non-pruned checkpoint, Anima's LLM adapter and LTX's licence inheritance each cost a whole run if missed.
4. **Coverage passes** — 8-point rotation including the rear angles, one elevation above and one below, close-up through full body, neutral plus two expressions, varied lighting and setting.
5. **Curated hard** — no near-duplicates, no occluded faces, no watermarks, consistent apparent age and build.
6. **Captions follow caption-the-residual in your encoder's dialect** — booru tags for CLIP-class, prose for LLM/T5-class — identity absent, every varying element named, explicitly where the content is explicit.
7. **Trigger token matched to the encoder class**: a rare literal token on CLIP-class; folded into a phrase or omitted on LLM-class.
8. **Checkpoint saving on**, at an interval that gives you a series rather than a verdict.
9. **Probe prompts written before the run**, saved in the run folder, carried over from last time so the runs compare. At least one out-of-distribution.
10. **Evaluation planned** — which grid tool, where the blind pass happens, and the `FaceEmbedDistance` baseline calibrated now if you intend to use it.
11. **Budget estimated in cells** if renting: checkpoints × strengths × prompts × seeds × seconds-per-image, read *before* rendering starts.

---

## Where this fits

The boundary table at the top routes *inward* — which per-model trap applies to your run. This one routes *outward*, for when the job is adjacent to training rather than training itself. Between them they define what this skill owns: only ever the craft that survives a change of model.

| If the job is… | Reach for |
|---|---|
| **Making** a character or style LoRA | Owned here — dataset, captioning, hyperparameter shape, evaluation, publishability |
| **Per-model** hyperparameters, trainer flags, architecture quirks | Each model skill's `references/lora-training.md`. Not owned here, deliberately: the numbers differ per model and would rot |
| **Loading and stacking** a finished LoRA | Each model skill's `references/setup-and-workflows.md`. Making and using are separate jobs across the whole suite |
| **Renting the GPU** for the run | [`comfyui-on-runpod`](../comfyui-on-runpod/) — especially the network-volume pattern, so a grid run does not re-download weights |
| **Deploying** the LoRA into a pipeline | [`image-production-workflows`](../image-production-workflows/) — the detailer-stage identity swap is a pipeline decision, not a training one |
| **Consistent characters without training** | [`flux-2`](../flux-2/) (multi-reference + PuLID), [`sdxl`](../sdxl/) (deepest adapter toolbox), each skill's `references/characters.md`. Often the better answer for a one-off |
| Training on the **lowest hardware floor** | [`anima`](../anima/) — ~6 GB, which is what makes cheap iteration possible |
| Training on **Ideogram 4** | [`ideogram-4`](../ideogram-4/) — style LoRAs are a real ecosystem there; character LoRAs are trainable but undemonstrated, so treat it as exploratory |
| Holding a character in **video** | [`wan-2-2`](../wan-2-2/), [`minimax-h3`](../minimax-h3/), [`ltx-2-5`](../ltx-2-5/). The craft here applies; video adds manual captioning cost and per-architecture rules |
| Video identity with **no training path** | [`scail-2`](../scail-2/) — identity is a reference image, not an adapter, so nothing on this page applies |

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** Civitai's real-person policy (quoted from their published rules), the TAKE IT DOWN Act's dates, enforcement start and penalty scale, the DreamBench++ result on DINO/CLIP-I misalignment, LTX-2.x's derivative-inheritance clauses, and the mechanism by which abliteration fails as an encoder swap. **Sources are official or primary** — platform policy pages, the published benchmark, licence text, and legal-practice summaries of the statute. These carry legal and account consequences, and the regulatory picture is **moving**: state deepfake law is still landing and platform policy follows it. **Re-verify before relying on any of it, regardless of who said it, and treat this as orientation rather than legal advice.**

**Craft — what actually makes a good LoRA.** Caption-the-residual and its inversion, the coverage protocol, 15–30 curated images beating 100, the hyperparameter ranges, the dataset factory, XY-grid evaluation, the blind pass, the overfit signals. **The authoritative source here is the community** — named trainers who have run hundreds of these: neonkisu, QuantumBogoSort, Khanykov01, NanashiAnon, L3n4, Ainara, MyAIForce and the Civitai dataset guides, plus `-p-e-w-` on abliteration and MASilverHammer on Differential Output Preservation. Stated with confidence; ranges mean "your dataset and base differ from theirs," not "this is unreliable."

Three things held as genuinely open:

- **Z-Image and Krea 2's adult-content position** is not well documented either way. `[flagged — re-verify]`
- **Optimal rank for character work** is contested across families and has been for years — the ranges above bracket the disagreement rather than resolving it. `[contested]`
- **Differential Output Preservation's transferability**: it works on Krea 2, fails outright on Z-Image Base, and nobody has mapped which architectures it takes on. `[contested]`

**Facts dated 2026-08-22.** The legal material moves fastest and is the thing to re-check before publishing anything — Civitai's policy text, the enforcement posture around the Act, and the derivative terms of any non-permissive licence you train against. The adult-flagged-share sample is dated in place and drifts as ecosystems mature.

---

## Reference files

| File | When to read it |
|---|---|
| `references/dataset-and-captioning.md` | Building the set: the 8-point rotation protocol in full, curation criteria, the synthetic dataset-factory loop, caption formats by encoder class, multi-outfit limits, and Differential Output Preservation for multi-character work |
| `references/nsfw-training.md` | Adult work in depth: the full adult-flagged-share table and per-family base selection, the character-vs-capability-LoRA scale difference, why the encoder-swap myth persists, explicit-captioning practice, anatomy failure modes, and the manual-captioning cost on video |
| `references/evaluation-and-tooling.md` | Judging a run at home: which grid tool and its limits, the blind-judging pass, a copy-pasteable probe set, `FaceEmbedDistance` with baseline calibration and why the metric misleads, cost arithmetic for rented GPUs, and the one small script worth writing yourself |
| `references/publishing-and-likeness.md` | Whether a LoRA is publishable at all: Civitai's rules in full, the TAKE IT DOWN Act, licence inheritance on non-permissive models, dataset provenance, the synthetic-character resemblance test, and where distribution is still open |
