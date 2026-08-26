---
name: character-lora-training
description: >
  Train a character LoRA that holds an identity across prompts, poses and models — the cross-model craft that every model skill in this suite otherwise repeats. Use this whenever the user is building, debugging or planning a LoRA, even obliquely: assembling and curating a dataset, deciding how many images, captioning (and the character-vs-style inversion that decides what a LoRA actually learns), picking rank/alpha/LR/steps as starting points, **evaluating a finished run** — which checkpoint to ship, how to build and read an XY/checkpoint grid, which comparison tool to use, whether a run over- or under-fit, how to score likeness objectively — holding likeness across a multi-stage pipeline or into video, or choosing which base model to train on in the first place. It covers **adult/NSFW work as a first-class case** — which base models actually have the training data (the limit is nearly always data, not refusal), why explicit captioning is mandatory rather than optional, anatomy failure modes, and why automated captioners fail on adult video. It also covers what determines whether a LoRA is **publishable at all**: Civitai's total ban on real-person likeness (SFW and NSFW alike) and the TAKE IT DOWN Act's live FTC enforcement, both of which constrain dataset sourcing and distribution. Per-model hyperparameters, trainer flags and quirks live in the model skills — this owns what transfers.
---

# Character LoRA training

A character LoRA works when the identity survives prompts it never saw. Everything below serves that test.

**This skill owns what carries over between models.** Exact hyperparameters, trainer support and architecture quirks belong to each model skill. Some of those quirks cost you a whole run if you miss them, so check yours before you start:

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

> **A `../link/` on this page that doesn't resolve is a skill you have not installed, not a broken
> page.** [`generative-media-atlas`](../generative-media-atlas/) is the map of this suite: which
> model fits a job, which skills that job needs, and the commands to install them. It works on its
> own, so it is the one to add first — `npx skills add ryannel/skills --skill generative-media-atlas`

---

## Before anything: can you publish it?

This goes first because it decides whether the work is usable at all. The rules also changed recently enough that most guides you will find still predate them.

**Civitai bans real-person likeness outright** — *"living or deceased … including public figures, celebrities, influencers, and private individuals"* — at **every rating, SFW and NSFW alike.** That includes historical figures, and fictional characters rendered as the actor who played them. **There is no consent exception.** `[official — Civitai content rules, read 2026-08-13; re-verify]`

**The TAKE IT DOWN Act is live.** It was signed in May 2025, and **FTC enforcement began on 19 May 2026** — the same day platforms had to have 48-hour notice-and-removal working. Civil penalties run to about **$53,088 per violation**. It covers AI-generated NCII of real people whenever the output is *"indistinguishable from an authentic visual depiction."*

Three consequences for training:

- **A dataset of a real person cannot be distributed**, whatever you intended. The main host will not take it, and on the NSFW side the exposure is now federal and enforced.
- **The test is resemblance, not where the pictures came from.** A synthetic character is fine, even though the base model learned from photographs of real people. A character who looks like an identifiable individual is not. **"It's a lookalike, not them"** is exactly the argument the actor clause closes off.
- **Private commissions and self-portraits are your own call.** The platform rule governs what you distribute; the law governs intimate imagery of other people. Know which one you are under.

Full treatment, dataset provenance, and the synthetic-character question: **`references/publishing-and-likeness.md`**.

---

## The one rule that changes everything

**Caption the residual — describe what varies, never what you are teaching.**

A LoRA learns whatever is *constant across the dataset and missing from the captions*. That one sentence explains most training outcomes. It also flips completely between the two jobs:

| | Character LoRA | Style LoRA |
|---|---|---|
| Constant across the set | **the person** | **the style** |
| Therefore: never caption | the face, the identity | the rendering, the medium |
| Therefore: always caption | pose, outfit, framing, lighting, setting, expression | subject, composition, everything depicted |
| Dataset diversity in | everything *except* the person | subjects, above all else |

Caption the face and you teach the model that this face is optional. Forget to caption the red jacket she wears in twenty of thirty pictures and the jacket becomes part of the character.

**When a trait belongs to the person but still changes, caption what changes it.** Freckles are hers, so never name them — but they fade under foundation. A set holding both versions forces the model to blame that difference on something, and if you name nothing it blames a bystander: the formal dress, or the indoor light. Caption the **makeup** instead. The freckles stay part of the trigger, and their fading becomes a switch you can flip when you generate. Same shape for tan lines, glasses, hair up or down: name the cause, never the trait, and caption the exception rather than the rule. `references/dataset-and-captioning.md` §4.

**A trigger token gives you a handle on the character.** On CLIP-class encoders it should be a rare token, used literally and identically every time. On LLM/T5-class encoders it belongs inside a natural phrase, or left out altogether — a bare rare token just confuses a language encoder. Your encoder class decides this, not your preference. See the conditioning doctrine in your model skill.

---

## The dataset

**Quality and coverage beat volume.** **15–30 well-curated images beat 100 mediocre ones.** This holds up in every base family anyone has tested it on, from NanashiAnon's Illustrious-era figure of 20–30 to L3n4's "a well-curated 30–50 beats a poorly curated 500" `[community — NanashiAnon, L3n4/Civitai 25645; convergent]`. More images will not fix a set that lacks angular coverage. They just cost more steps.

**The coverage protocol decides whether the identity generalises**, and it runs on five axes `[community — MyAIForce, Civitai guides 5301/6990; convergent]`:

- **8-point rotation** around the head: front, three-quarter and profile on each side, and the rear angles. Missing angles is the number-one cause of a LoRA that collapses onto one pose, and the rear views are the ones people skip.
- **Elevation** (one above and one below eye level), **shot size** (close-up, medium, full body), **expression** (neutral plus two more), and **varied lighting and settings**. Every gap fails the same way: whatever never changes becomes part of the identity. A face-only set gives you a character with no body. A single-expression set gives you a character stuck with one face.

Full protocol with the exact angle clauses: **`references/dataset-and-captioning.md` §2**.

**Change one clause at a time.** When you generate a set, hold the character description fixed and vary only the rotation, shot-size or expression clause. Anything else that drifts becomes part of what the model learns.

**The chained approach is now standard**: lock one anchor image, use an edit model to build the varied set from it, curate hard, then train. That gives you coverage photography rarely does, and it sidesteps the likeness problem completely, because the character never existed. Someone has packaged the whole loop as a ComfyUI system — **VNCCS 3.0**, with a 3D pose studio, outfit cloning across characters and per-sprite regeneration `[community — AHEKOT, r/StableDiffusion 892 pts]`. A sprite sheet aims at narrower coverage than a training set does, though, so still curate its output against the protocol above.

**A video model makes a good dataset factory**, and it genuinely *solves* the 8-point rotation problem rather than approximating it. Prompt a slow 360° turnaround with no cuts, then cut the clip into frames. The coverage comes out continuous and consistent because it is one camera move, not several separate generations. Two things to know before reaching for it: it burns a lot of generated frames, and video stills carry less detail than image stills. One more is easy to miss — **check the licence of the model you harvest from**, because some of them restrict using their output to train anything else. [`ltx-2-5`](../ltx-2-5/)'s Attachment A ¶18 does exactly that, and how far it reaches into non-commercial work is unsettled `[contested]`.

Full dataset craft — curation criteria, the synthetic-generation loop, the video turnaround in detail, captioning by encoder class, and the multi-character options: **`references/dataset-and-captioning.md`**.

---

## Hyperparameters as starting points

These show the shape of the consensus. They are not settings to copy — every model skill gives its own, and they differ.

| Parameter | Typical starting range `[community — neonkisu, QuantumBogoSort, L3n4/Civitai 25645]` | Notes |
|---|---|---|
| Rank | **8–32** | Higher catches fine detail and overfits faster. 4–16 is typical on newer DiTs, 32–64 on SDXL-era. Genuinely disputed — see the two-bar section `[contested]` |
| Alpha | half of rank, commonly | Interacts with LR, so changing one means retuning the other |
| Learning rate | **~1e-4** | Lower for larger ranks and larger models |
| Steps | **1500–3000** | Scale with dataset size. The rule of thumb behind that range is ~80–100 steps per image |
| Batch | 1–2 on 16–24 GB | If you drop batch to fit, hold `batch × gradient_accumulation` constant |

Two alpha conventions are in use. **Alpha = rank** trains "louder" per step, because it effectively scales the learning rate. **Alpha = rank/2** is the more conservative default given here. Since alpha and LR interact, recipes using different conventions are not directly comparable. When a model skill in this suite pins a different alpha for its trainer, the model skill wins — this row is only the cross-model fallback.

**Save checkpoints throughout and judge them as a series.** The best epoch is rarely the last one. This is the single highest-value habit in training: a run with intermediate checkpoints gives you a choice, and a run with only a final one gives you a verdict.

**The floor for training at home has dropped, and that changes the economics.** Most of the suite's models want 16–24 GB, which is why renting ([`comfyui-on-runpod`](../comfyui-on-runpod/)) is the usual answer. [`anima`](../anima/) breaks that pattern: LoRA training fits in roughly **6 GB at 768 px** `[community — citronlegacy, Civitai 26217; convergent]`. That matters beyond anime work, because the real cost of this craft is the three failed runs it takes to learn what your dataset is missing — and at 6 GB those are free.

---

## Evaluating a run

**Loss is a weak signal.** It tells you the model is fitting. It does not tell you whether the identity generalises. Judge on images, in three layers, cheapest first:

1. **Training previews** — already switched on, and *not* free on a rented GPU. They run on the clock you are paying for, and on an undistilled training model they can eat more time than the training does. Fix the seed, use 3–5 prompts, save checkpoints often but preview rarely, and read them only to find *roughly where the good region is*. Never pick your final checkpoint here — the trainer's sampler is not the one you ship with.
2. **A grid: checkpoint × strength**, on fixed prompts and a fixed seed, made in the tool you will actually ship from. This is the only step that costs real compute, so narrow the range with layer 1 first.
3. **Judge it blind, and set it up that way from the start.** A grid is labelled on purpose, so you know which cell trained longer before you even look. Knowing that does not protect you — the labelled sheet is still the easiest thing to open. Have whatever draws the grid write **coded cells plus a key file you leave shut** until your pick is written down. Then open it. Same cost, and it often flips the answer the labelled grid gave you.

**When a model comes in two halves, previews lie in a predictable direction.** If the trainer previews on the slow half (Krea 2 Raw, Z-Image Base, Flux dev) and you deploy on the fast one, those high-guidance previews smear exactly the fine detail a face is recognised by. The likeness looks weaker than it is. So do not restart because of a preview. Wait until about 60–70% of the run before you worry, and check on the model you actually deploy on — one image at real settings costs far less than a restart.

**Nothing goes into the LoRA library until the blind pick is settled**, and **if the subject is a real person, the pick belongs to whoever knows that face.** How closely a picture resembles a stranger is not something an outside eye or a metric can judge. So whoever ran the training builds the blind set, and whoever knows the subject chooses. A checkpoint handed over early gets used forever, so label it provisional and keep the other candidates until it is settled.

**Three habits decide whether any of that is worth anything** `[community — production practice; convergent]`:

- **Probe out of distribution, or you have tested nothing.** Put the character somewhere unlike the dataset: a costume, a painted style, a wide shot where the face is small. A LoRA that only holds up on near-copies of its training data memorised instead of learning, and in-domain prompts cannot tell you which happened.
- **Write the probe prompts before you see any results, and reuse the same set across runs.** Prompts you invent while browsing outputs drift toward what the LoRA already does well. A fixed set is the only way run 3 stays comparable to run 1.
- **Score likeness and prompt-adherence separately.** They peak at *different* checkpoints, because likeness keeps improving after flexibility has started to die. Asking "which is best?" quietly averages two things moving in opposite directions.

**Numbers are a screen, not a verdict.** `FaceEmbedDistance` (from `cubiq/ComfyUI_FaceAnalysis`) is the quantitative signal you can actually reach. Calibrate a baseline from real photos first. And know that DINO/CLIP-I-family metrics are **documented as significantly out of step with human judgement** on exactly this task — that is the central result of **DreamBench++** (ICLR 2025) `[official — published benchmark]`. They also inflate when a LoRA overfits pose, so a score that climbs late in a run may just be measuring memorisation.

Two cheap tests before shipping: a **strength sweep** (a healthy LoRA has a usable band, not a knife-edge) and a **stack test** if it will run alongside others.

Grid tooling, a copy-pasteable probe set, the cost arithmetic, and what is worth building yourself: **`references/evaluation-and-tooling.md`**.

---

## Failure modes & QC

Read the cause column and the pattern jumps out: nearly every one is a **dataset or caption** problem dressed up as a hyperparameter problem.

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

Treated as a first-class case, because it is a dominant use of open-weights models and because most of the difficulty gets misdiagnosed.

**The limit is training data, not refusal.** Open-weights models do not generally refuse. They produce poor anatomy because the base model never saw much of it. That is why swapping in an abliterated ("heretic") text encoder does not work, and the author of the leading abliteration tool says so plainly: abliteration removes an LLM's ability to *refuse*, and refusal lives in output layers that a text encoder never uses `[community — -p-e-w-, author of Heretic]`. What you get is disturbed conditioning, slightly worse prompt adherence, and no new capability. Abliterated models do have a use here — **prompt expansion**, when a prompt-enhancer LLM is the thing refusing. That is a separate stage, before the encoder.

**So base-model choice dominates** — and the usual way people measure it is currently disputed `[contested]`. The proxy is **what share of a base's published LoRAs are adult-flagged**, and two measurements ten days apart disagree almost inversely on video. A 2026-08-13 sample of about 100 LoRAs per base puts **Wan 2.2 I2V highest at 90%** and Flux lowest at 28%. A 2026-08-23 re-census — 600 most-downloaded per base, reading the X/XXX bits of Civitai's `nsfwLevel` bitmask — runs from **Pony at 67%** down to **Wan 2.2 at 22–23%**. The likely explanation is that `nsfwLevel` comes from **preview images**, and a video LoRA's preview is routinely a tame first frame, so the metric undercounts video. Both tables, both methods, and the trap that the API's `nsfw` boolean is dead: **`references/nsfw-training.md` §2**. The reproducible census script lives in [`generative-media-atlas`](../generative-media-atlas/), which owns model choice.

Two things hold whichever ordering is right. First, these percentages measure *which way an ecosystem leans*, not what a model can do — SDXL's ~31% of a far larger library is more material in absolute terms than any newer base's 60%, and SDXL is still where the purpose-built finetunes live. Second, **adult work is a dominant published use of open video models**, which rests on what the video community actually ships rather than on the metric. Two models stay ruled out for reasons that have nothing to do with capability: **Ideogram 4**, by a hard filter in the model itself, and [`ltx-2-5`](../ltx-2-5/), by an acceptable-use policy that bans explicit content everywhere, local weights included.

**Stacking a capability LoRA under a character LoRA is the standard answer when a base lacks the anatomy, and it is not a reliable one `[contested]`.** One practitioner worked through four published Wan I2V anatomy LoRAs and found each either failed to render or *"changes the character lora too much"* `[community — One-Energy5403]`. Two adapters are writing the same attention weights, and the broader one wins. Run the stack test *before* you commit to a base, not after the character LoRA is trained.

**Caption explicitly.** This is not a stylistic choice. Uncaptioned elements get absorbed into the concept, so euphemistic captions teach the model that the explicit content *is* the character — the failure people then go on to blame on the base model.

**Automated captioners fail here.** The community captions adult video by hand, which multiplies the cost on datasets where frame count is already the expensive part.

Anatomy failure modes, the full per-family table, and video specifics: **`references/nsfw-training.md`**.

---

## Pre-flight checklist

Most training checklists start at the config file. This one starts three steps earlier, because a config mistake costs you one run while a likeness problem costs you the project — and no step count trains around missing angular coverage.

1. **Publishable?** If a real person is anywhere near the dataset, settle this now. Civitai bans real-person likeness at every rating, and the TAKE IT DOWN Act is in force (`references/publishing-and-likeness.md`).
2. **Base chosen for the job, not out of familiarity** — judged on the axes that actually differ: adult coverage, multi-character support, and the VRAM floor you can afford.
3. **Per-model trap read**, from the boundary table above. Wan's two experts, H3's non-pruned checkpoint, Anima's LLM adapter and LTX's licence inheritance each cost a whole run if missed.
4. **Coverage passes** — 8-point rotation including the rear angles, one elevation above and one below, close-up through full body, neutral plus two expressions, varied lighting and settings.
5. **Curated hard** — no near-duplicates, no occluded faces, no watermarks, consistent apparent age and build.
6. **Captions follow caption-the-residual in your encoder's dialect** — booru tags for CLIP-class, prose for LLM/T5-class. Identity absent, every varying element named, and named explicitly where the content is explicit.
7. **Trigger token matched to the encoder class**: a rare literal token on CLIP-class, folded into a phrase or dropped on LLM-class.
8. **Checkpoint saving on**, at an interval that gives you a series rather than a verdict.
9. **Probe prompts written before the run**, saved in the run folder, and carried over from last time so the runs compare. At least one out of distribution.
10. **Evaluation planned** — which grid tool, how the cells come out **coded instead of labelled**, who makes the likeness pick, and the `FaceEmbedDistance` baseline calibrated now if you plan to use it.
11. **Budget counted in cells** if renting: checkpoints × strengths × prompts × seeds × seconds per image, worked out *before* rendering starts. Count the **training previews** the same way (`prompts × seconds per preview × steps ÷ sample_every`), because that cost stays invisible until the bill arrives.

---

## Where this fits

The boundary table at the top routes *inward*, to the per-model trap that applies to your run. This one routes *outward*, for when the job sits next to training rather than being training. Between them they define what this skill owns: only the craft that survives a change of model.

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
| **Deciding which base to train on at all** | [`generative-media-atlas`](../generative-media-atlas/) — it splits "easiest to train on" into best likeness, fastest loop and best-documented, which have different winners, and it carries the one published cross-model comparison |

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** Civitai's real-person policy (quoted from their published rules), the TAKE IT DOWN Act's dates, enforcement start and penalty scale, the DreamBench++ result on DINO/CLIP-I misalignment, LTX-2.x's derivative-inheritance clauses, and the mechanism by which abliteration fails as an encoder swap. **Sources are official or primary**: platform policy pages, the published benchmark, licence text, and legal-practice summaries of the statute. These carry legal and account consequences, and the regulatory picture is **still moving** — state deepfake law is landing and platform policy follows it. **Re-verify before relying on any of it, whoever said it, and treat this as orientation rather than legal advice.**

**Craft — what actually makes a good LoRA.** Caption-the-residual and its inversion, captioning the cause for traits that are identity *and* variable, the coverage protocol, 15–30 curated images beating 100, the hyperparameter ranges, the dataset factory and when feeding a new LoRA the old one's pictures wrecks the run, XY-grid evaluation, the blind pass and setting it up blind from the start, what previews cost and why they understate likeness on a two-half model, the overfit signals. **The authoritative source here is the community** — named trainers who have run hundreds of these: neonkisu, QuantumBogoSort, Khanykov01, NanashiAnon, L3n4, Ainara, MyAIForce and the Civitai dataset guides, plus `-p-e-w-` on abliteration and MASilverHammer on Differential Output Preservation. Stated with confidence. A range means "your dataset and base differ from theirs", not "this is unreliable".

Five things held as genuinely open:

- **The adult-flagged-share ordering.** Two censuses ten days apart disagree almost inversely on video, and neither method is clean — the preview-image basis of Civitai's `nsfwLevel` explains the video half of the gap but not the image half. `[contested]`
- **Whether a capability LoRA can be stacked under a character LoRA without destabilising it.** Four published anatomy LoRAs, none of which worked for one practitioner, and no recipe offered in reply. `[contested]`
- **Same-sex and non-heteronormative scenes** fail across SDXL, Z-Image and Krea 2 alike, and nothing in this suite answers it. The mechanism is clear — training distribution — but the fix is not. `[flagged — open gap]`
- **Optimal rank for character work** has been contested across families for years. The ranges above bracket the disagreement rather than settling it. `[contested]`
- **Differential Output Preservation's transferability.** It works on Krea 2 and fails outright on Z-Image Base, and nobody has mapped which architectures it takes on. `[contested]`

**Facts dated 2026-08-22; community craft refreshed 2026-08-23; the evaluation and captioning craft extended 2026-08-25 from one finished real-person character run. Its measured numbers are a single data point and are dated where they appear — the mechanisms behind them do generalise.** The legal material moves fastest, and it is what to re-check before you publish anything: Civitai's policy text, the enforcement posture around the Act, and the derivative terms of any non-permissive licence you train against. The adult-flagged-share figures are dated in place, disputed between two methods, and will drift as ecosystems mature — re-measure rather than reading either table forward.

---

## Reference files

| File | When to read it |
|---|---|
| `references/dataset-and-captioning.md` | Building the set: the 8-point rotation protocol in full, curation criteria, the synthetic dataset-factory loop and when reusing your own previous LoRA's pictures is fair, caption formats by encoder class, multi-outfit limits, and Differential Output Preservation for multi-character work |
| `references/nsfw-training.md` | Adult work in depth: both adult-flagged-share censuses with their methods and why they disagree, per-family base selection, the character-vs-capability-LoRA scale difference and why stacking them is unreliable, the same-sex coverage gap, why the encoder-swap myth persists, explicit-captioning practice, anatomy failure modes, and the manual-captioning cost on video |
| `references/evaluation-and-tooling.md` | Judging a run at home: which grid tool and its limits, the blind-judging pass and how to set it up blind from the start, what training previews really cost and why they understate likeness on a two-half model, a copy-pasteable probe set, `FaceEmbedDistance` with baseline calibration and why the metric misleads, cost arithmetic for rented GPUs, and the one small script worth writing yourself |
| `references/publishing-and-likeness.md` | Whether a LoRA is publishable at all: Civitai's rules in full, the TAKE IT DOWN Act, licence inheritance on non-permissive models, dataset provenance, the synthetic-character resemblance test, and where distribution is still open |
