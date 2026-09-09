---
name: character-lora-training
description: >
  Train a character LoRA that holds an identity across prompts, poses and models. This is the
  cross-model craft that every model skill in this suite would otherwise have to repeat. Use this
  whenever the user is building, debugging or planning a LoRA, even obliquely: assembling and
  curating a dataset — importing an image pool, deduplicating it, or captioning it counts, even
  when no training run is planned yet — deciding how many images to use and what resolution to render or
  source them at, captioning (including the character-vs-style
  inversion that decides what a LoRA actually learns), picking rank/alpha/LR/steps as starting
  points, or **evaluating a finished run** — which checkpoint to ship, how to build and read an
  XY/checkpoint grid, which comparison tool to use, whether a run over- or under-fit, and how to
  score likeness objectively. It also covers holding likeness across a multi-stage pipeline or into
  video, and choosing which base model to train on in the first place. It covers **adult/NSFW work
  as a first-class case**: which base models actually have the training data (the limit is nearly
  always data, not refusal), why explicit captioning is mandatory rather than optional, anatomy
  failure modes, and why automated captioners fail on adult video. It also covers what determines
  whether a LoRA is **publishable at all**: Civitai bans real-person likeness totally, SFW and NSFW
  alike, and the TAKE IT DOWN Act now has live FTC enforcement. Both constrain dataset sourcing and
  distribution. Per-model hyperparameters, trainer flags and quirks live in the model skills; this
  skill owns what transfers. Choosing between models, comparing them, or working out which skills
  and install commands a job needs is [`generative-media-atlas`](../generative-media-atlas/)'s
  job — start there when the model is not already settled.
---

# Character LoRA training

A character LoRA works when the identity survives prompts it never saw. Everything below serves that test.

**This skill owns what carries over between models.** Exact hyperparameters, trainer support and architecture quirks belong to each model skill. Some of those quirks cost you a whole run if you miss them, so check yours before you start:

| Model | The thing you cannot skip |
|---|---|
| [`sdxl`](../sdxl/) | Base-model choice dominates everything — the finetune you train on decides your ceiling |
| [`z-image`](../z-image/) | Train on Base, deploy via the detailer swap; Ostris AI-Toolkit is the trainer |
| [`flux-2`](../flux-2/) | Licence split across variants; BFL filtered the pre-training data |
| [`krea-2`](../krea-2/) | Train on Raw, run on Turbo — and render dataset sources **inside the 1K band**, never above it |
| [`qwen-image`](../qwen-image/) | Train on the bf16 base of the generation you will *deploy* on — 2509, 2511 and 2512 LoRAs are mutually incompatible, and lowering strength does not fix it; the trigger is a plain name, and there is no adapter to fall back on |
| [`wan-2-2`](../wan-2-2/) | **Two LoRAs** — one per MoE expert — from one dataset |
| [`minimax-h3`](../minimax-h3/) | Both trainers now take the pruned and INT8 builds, so check your trainer's supported bases before downloading (musubi's backward pass fails on pruned-INT8); **rank 16 only** under ai-toolkit — 32 collapsed with distillation handling off; training resolution is the likeness lever |
| [`anima`](../anima/) | **Do not train the LLM adapter** (`llm_adapter_lr 0`) — it rewrites prompt understanding globally and presents as "Anima got worse", not as a broken LoRA |
| [`ltx-2-5`](../ltx-2-5/) | Your LoRA is a **Derivative** — it inherits the licence, and the obligation travels to whoever you give it to |

> **A `../link/` on this page that doesn't resolve is a skill you have not installed, not a broken
> page.** [`generative-media-atlas`](../generative-media-atlas/) is the map of this suite: which
> model fits a job, which skills that job needs, and the commands to install them. It works on its
> own, so it is the one to add first — `npx skills add ryannel/skills --skill generative-media-atlas`

---

## Before anything: can you publish it?

This section goes first because it decides whether the work is usable at all. The rules also changed recently enough that most guides you will find still predate them.

**Civitai bans real-person likeness outright.** The ban covers *"living or deceased … including public figures, celebrities, influencers, and private individuals"*, and it applies at **every rating, SFW and NSFW alike.** It includes historical figures, and it includes fictional characters rendered as the actor who played them. **There is no consent exception.** `[official — Civitai content rules, read 2026-08-13; re-verify]`

**The TAKE IT DOWN Act is live.** It was signed in May 2025, and **FTC enforcement began on 19 May 2026**, the same day platforms had to have 48-hour notice-and-removal working. Civil penalties run to about **$53,088 per violation**. The Act covers AI-generated NCII of real people whenever the output is *"indistinguishable from an authentic visual depiction."*

Three consequences for training:

- **A dataset of a real person cannot be distributed**, whatever you intended. The main host will not take it, and on the NSFW side the exposure is now federal and enforced.
- **The test is resemblance, not where the pictures came from.** A synthetic character is fine, even though the base model learned from photographs of real people. A character who looks like an identifiable individual is not fine. **"It's a lookalike, not them"** is exactly the argument the actor clause closes off.
- **Private commissions and self-portraits are your own call.** The platform rule governs what you distribute. The law governs intimate imagery of other people. Know which one you are under.

For the full treatment, dataset provenance, and the synthetic-character question, read **`references/publishing-and-likeness.md`**.

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

If you caption the face, you teach the model that this face is optional. If you forget to caption the red jacket she wears in twenty of thirty pictures, the jacket becomes part of the character.

**When a trait belongs to the person but still changes, caption what changes it.** Freckles are hers, so never name them. But freckles fade under foundation, and a set holding both versions forces the model to blame that difference on something. If you name nothing, it blames a bystander, such as the formal dress or the indoor light. Caption the **makeup** instead. The freckles stay part of the trigger, and their fading becomes a switch you can flip when you generate. The same shape applies to tan lines, glasses, and hair up or down: name the cause, never the trait, and caption the exception rather than the rule. See `references/dataset-and-captioning.md` §4.

**Constants bind to the trigger — and so do majorities and absences.** Thirty-two bare-eared, bare-faced, dark-haired images teach "no jewellery, no makeup, dark brown hair" as the person, even though the base can draw all three unaided. One synthetic set had dark brown hair on 29 of 32 cells. "Red hair" then rendered a *different woman* on every checkpoint of two training arms. A platinum pixie cut, a lab coat and snow all held. The fix was not more images. It was redistributing colour across the same 32 cells so that no colour had a majority `[live-use — media lab, Ciara dataset v4→v5, 2026-09-09]`. You cannot vary what you never named, and you cannot vary what never varied.

**A trigger token gives you a handle on the character, and the rule is per model, not per encoder class.** On CLIP-class encoders a rare token used literally works. On LLM-encoder models the camps split. BFL prescribes a made-up token on FLUX.2 klein `[official — BFL, 2026-06-04]`. Krea 2 users report random strings surfacing as text or a watermark `[community — promptdexter; single report]`. And a `z<name>` folded into a phrase — "a woman named zciara" — trains and transfers across Krea 2 and H3 unchanged `[live-use — media lab, 2026-09]`. The dispute is listed in the two-bar section. Expect the phrase to bleed onto signage. And on a single-subject set the trigger is not a gate. The LoRA renders the person with the token removed, because nothing in the set ever forced it to discriminate `[live-use — media lab, Amy trigger A/B, 2026-08-31]`. See `references/dataset-and-captioning.md` §4.

---

## The dataset

**Count is not the lever.** The community figure is 15–40 curated images, from NanashiAnon's Illustrious-era 20–30 to BFL's 15–40 for FLUX.2 `[community — NanashiAnon, L3n4/Civitai 25645; official — BFL; convergent]`, and the media lab has now tested the ceiling three separate ways. A 25-image set beat its own 74-image superset on a blind face probe. On H3, 32 → 73 images left likeness exactly where it was. Fifteen coverage-built images came out "very close" to 32 `[live-use — media lab, krea2-v1/v4, h3-v14, krea2-v8, 2026-08-27 → 30]`. Rank and steps were exhausted first: rank 64 and 3,000 steps on the same 25 images lost blind to the rank-32 control `[live-use — media lab, krea2-v2, 2026-08-26]`. When a run disappoints, the question is *which* images, never *how many*.

**What it should contain: coverage, and the starved axes are countable.** Audit the pool before you train — rotation (front / three-quarter / profile / rear), elevation (above and below eye level), shot size, expression, lighting. One 73-image pool read front 41, three-quarter 23, profile 6, rear 3, below eye level **0**. The LoRA then scored strict profile 0/5 on every seed, because the set's only profile was one frame `[live-use — media lab, Amy coverage audit, 2026-08-30]`. Whatever never varies becomes part of the identity. The 8-point rotation protocol and the rest of the axes are in **`references/dataset-and-captioning.md` §2**.

**Split it roughly one-third identity, two-thirds in context** — close-ups and clean head-and-shoulders against full body in varied settings; anywhere from 0.25 to 0.40 works `[community — neonkisu, Civitai 31467]`. A close-up-heavy set gives great faces and an unreliable body; a context-heavy set gives a face that drifts when the prompt zooms in. The lab reproduced both, with a caveat: **0.33 is necessary, not sufficient.** A set inside the band with only 9 close-ups still failed the tight crop where 14 held `[live-use — media lab, Amy v1/v5/v6, 2026-08-27]`. Identity is learned **per face-scale**: the face that reads inside a full-body shot is not the face the close-up taught. So a probe with the face small in the frame is testing a coverage row, not a checkpoint. What the ratio really counts is face pixels, which is why a lower training resolution needs a heavier skew to close-ups. One published Qwen-Image character recipe runs **60/30/10** close/half/full instead; [`qwen-image`](../qwen-image/) records that as contested against this rule, not as a Qwen exception.

**A crop of a photo already in the set is a duplicate, and it teaches the crop.** Two chest-up crops of images already present double-weighted them (the subject read tanner and older) and taught a chest-centred frame that cut heads off at inference `[live-use — media lab, krea2-v12, 2026-09-03]`. Flat, front-lit, shallow-depth portraits with no shadow shaping the face skew a set the same way. Curation criteria, dedup by eye and the per-pair repaired-vs-original call are in **`references/dataset-and-captioning.md` §1**.

**Resolution: render or source inside the base's trained band. Bigger is worse, and the damage survives downscaling.** This reverses the supersampling habit photography teaches, and the lab paid a day for it. Trainers downscale into buckets and never upscale `[official — ostris/ai-toolkit README]`, so a 2048 source and a 1024 source land in the same 1024 latent. What was in the pixels before the resample is what differs. Krea 2 Turbo's band is 1K–2K and Raw is 1K-native. A four-cell sweep there at LoRA strength 0 showed 1024×1280 native clean, 2048 moderately crumpled and 2560 heavily. Downscaling 2048 or 2560 to 1024 *still* lost to 1024 native. The reticulated "scale skin" was baked into the sources before the trainer saw them. It was not the VAE: two decoders were identical at 2048. It was not rank either: two LoRAs retrained on a 1024-native set, at rank 16 and 32, were clean at every checkpoint `[live-use — media lab, Ciara dataset v3→v4, krea2-v4/v5, 2026-09-08 → 09]`. **Keep three resolutions apart** — the source render (inside the base's band), the training bucket, and the deploy render (the deployment checkpoint's band, which differs per checkpoint). The Krea 2 numbers are in [`krea-2/references/lora-training.md`](../krea-2/references/lora-training.md). On H3, where the bucket is 1536, real photos raise the opposite problem. Sources below the bucket teach softness. Upscale them *outside* the trainer, and only where real detail exists to work from — [`minimax-h3/references/lora-training.md`](../minimax-h3/references/lora-training.md).

**Sampling steps are a separate lever, and the wall is the tell.** At 2048 on a distilled checkpoint, 20 steps over-cooks skin into a pore grid the LoRA then learns; 12 and 8 are clean. An artefact that appears **on the background as well as the skin** is a sampler or step problem, not a content problem `[live-use — media lab, Ciara v2→v3, Amy, 2026-09-07]`. Textured-wall wording is a third source: "cyclorama" and "wallpaper" printed their pattern onto skin at 1024 native on every seed, where plain painted walls were clean. **Before you diagnose a subtle skin artefact, verify you are inside the base's resolution band and step band, and look at the wall.** The wrong turn is worth naming. The grain was first read as freckle stipple and nearly declared a hard limit. Meanwhile a VAE swap, texture-anchor words and a detail-heavy finetune were stacked as "sharpeners" on top of over-band renders. None of them was the cause. The full treatment, including real-photo floors and the fake-upscale signature, is **`references/dataset-and-captioning.md` §3**.

**Synthetic images: the measured points are 14% fine and 64% failed.** The recursive-training literature warns that 5–10% synthetic can start degradation in a naive loop `[official — arXiv 2407.17493]`. A set at 14% was uneventful. A set at 64% — 56 renders from the previous LoRA — learned the body and regressed the face, because every synthetic carried one generator's rendering of it `[live-use — media lab, krea2-v15, 2026-09-06]`. Whether a ≤40% or "almost entirely synthetic" set with enforced variety can work is the lab's current operating hypothesis, and unproven (see the two-bar section). A fully synthetic character sidesteps the loop: generate at LoRA strength **0** from the base, so no LoRA trains on its own output. The factory loop, the packaged VNCCS suite, the video turnaround (with the LTX output-use clause, still unsettled — [`ltx-2-5`](../ltx-2-5/) carries the flag) and the seeding rules are in **`references/synthetic-datasets.md`**.

---

## Hyperparameters as starting points

These ranges show the shape of the consensus. They are not settings to copy. Every model skill gives its own, and they differ.

| Parameter | Typical starting range `[community — neonkisu, QuantumBogoSort, L3n4/Civitai 25645]` | Notes |
|---|---|---|
| Rank | **8–32** | Higher catches fine detail and overfits faster. 4–16 is typical on newer DiTs, 32–64 on SDXL-era. Genuinely disputed — see the two-bar section, which carries the flag. The ceiling is model-specific, not a LoRA fact: 32 edges 16 on Krea 2, and 32 collapsed H3 under ai-toolkit in a ladder that trained with distillation handling off `[live-use — media lab, krea2-v4/v5, h3-v3, 2026-09]` |
| Alpha | half of rank, commonly | Interacts with LR, so changing one means retuning the other |
| Learning rate | **~1e-4** | Lower for larger ranks and larger models |
| Steps | **1500–3000** | How it scales is disputed (two-bar section). BFL and ai-toolkit budget 1,500–3,000 for a character *independent of set size* across 15–40 images `[official — docs.bfl.ml; ai-toolkit examples]`; the lab scales ~90–170 per image and finds the peak rung per dataset `[live-use — media lab, 2026-09]`. Either way, save rungs and pick (below) |
| Batch | 1–2 on 16–24 GB | If you drop batch to fit, hold `batch × gradient_accumulation` constant |
| Caption dropout | **0.05–0.3** — disputed | 0.05 is ai-toolkit's default and every lab run; 0.3 is called "the strongest single fix for generalisation" `[community — neonkisu]`; musubi's draft adds it at 0.1. An order of magnitude apart, untested head-to-head |

Two alpha conventions are in use. **Alpha = rank** trains "louder" per step, because it effectively scales the learning rate. **Alpha = rank/2** is the more conservative default given here. Alpha and LR interact, so recipes that use different conventions are not directly comparable. When a model skill in this suite pins a different alpha for its trainer, the model skill wins. This row is only the cross-model fallback.

**One optimiser report to know about.** `adamw8bit` is reported to zero small updates under BF16 on Z-Image. In that report `optimi.AdamW` (Kahan summation) converged at 900 steps against 3,000+, and the 2.15× inference strength the adamw8bit run needed was read as a symptom of the same bug `[community — AInVFX, 2026-04-06; single report; re-verify]`. The lab's `adamw8bit` runs on Krea 2 and H3 show no such symptom, so treat it as Z-Image-specific until reproduced.

**Save checkpoints throughout and judge them as a series.** The best epoch is rarely the last one. This is the single highest-value habit in training: a run with intermediate checkpoints gives you a choice, and a run with only a final one gives you a verdict.

**The floor for training at home has dropped, and that changes the economics.** Most of the suite's models want 16–24 GB, which is why renting ([`comfyui-on-runpod`](../comfyui-on-runpod/)) is the usual answer. [`anima`](../anima/) breaks that pattern: its LoRA training fits in roughly **6 GB at 768 px** `[community — citronlegacy, Civitai 26217; convergent]`. That matters beyond anime work, because the real cost of this craft is the three failed runs it takes to learn what your dataset is missing. At 6 GB those failed runs are free.

---

## Evaluating a run

**Loss is a weak signal.** It tells you the model is fitting. It does not tell you whether the identity generalises. Judge on images, in three layers, cheapest first:

1. **Training previews.** These are already switched on, and they are *not* free on a rented GPU. They run on the clock you are paying for, and on an undistilled training model they can eat more time than the training does. Fix the seed, use 3–5 prompts, save checkpoints often but preview rarely, and read the previews only to find *roughly where the good region is*. Never pick your final checkpoint here, because the trainer's sampler is not the one you ship with.
2. **A grid: checkpoint × strength**, on fixed prompts and a fixed seed, made in the tool you will actually ship from. This is the only step that costs real compute, so narrow the range with layer 1 first.
3. **Judge it blind, and set it up that way from the start.** A grid is labelled on purpose, so you know which cell trained longer before you even look. Knowing that does not protect you, and the labelled sheet is still the easiest thing to open. Have whatever draws the grid write **coded cells plus a key file you leave shut** until your pick is written down. Then open it. This costs the same, and it often flips the answer the labelled grid gave you.

**When a model comes in two halves, previews lie in a predictable direction.** If the trainer previews on the slow half (Krea 2 Raw, Z-Image Base, Flux dev) and you deploy on the fast one, those high-guidance previews smear exactly the fine detail a face is recognised by. The likeness looks weaker than it is. So do not restart because of a preview. Wait until about 60–70% of the run before you worry, and check on the model you actually deploy on. One image at real settings costs far less than a restart.

**Nothing goes into the LoRA library until the blind pick is settled.** And **if the subject is a real person, the pick belongs to whoever knows that face.** How closely a picture resembles a stranger is not something an outside eye or a metric can judge. So whoever ran the training builds the blind set, and whoever knows the subject chooses. A checkpoint handed over early gets used forever, so label it provisional and keep the other candidates until the pick is settled.

**Pick the rung by probe, not by one number.** Across four real-photo arms the three-quarter view was the canary. Every dataset change lost it while the front close-up and full body moved independently. It is also where an over-trained rung collapses first `[live-use — media lab, krea2-v9…v13, 2026-09-03]`. Which probe regressed is the finding; a single likeness score hides it.

**When two rungs tie, take the lower one.** Fewer steps bakes in less of the set. Past the peak the *source medium* trains in, not just the identity. An all-phone-JPEG set learned compression grain as skin past c1750, so it peaked a rung earlier than a set with DSLR frames `[live-use — media lab, krea2-v11, 2026-09-03]`. The peak checkpoint tracks source quality, not dataset size. And a likeness that keeps rising up to strength 1.1 is an underfit signature, not a setting to ship at — it means there is no stacking headroom `[live-use — media lab, krea2-v1, 2026-08-27]`.

**Evaluate on every checkpoint × resolution you will deploy on, with a strength-0 control in every comparison.** A Turbo-only eval shipped a LoRA whose skin broke up on the adult checkpoint at 1024×1536 and was fine at ≥1344×2016. Strength was not the lever, and a different rung survived the hard case `[live-use — media lab, Ciara krea2-v3, 2026-09-08]`. Add a **no-trigger control**: the same prompt minus the trigger must stay close to base, or you overtrained `[community — chengyansen-ai, krea2-lora-training]`. The lab's version of layers 2–3 is a staged ladder that fixes one variable per stage in 90–120 cells: steps and strength, stability, flexibility, the adult stack, render surface, then a blind head-to-head against the incumbent at its shipped settings. It is in `references/evaluation-and-tooling.md` §2.

**Judge in pairs, record the margin, and expect to tire.** Same probe, same seed, flick A/B, one decision per screen; a 1–5 scale asks for a global consistency people do not have. A 9–1 made of close calls is not a 9–1. After roughly a hundred blind pairs in two days the judge reported going "blind" to the face, and one stage was left unscored. So let a metric rank the cells and give the human only the top and bottom. Put the next deck a day out `[live-use — media lab, 2026-09-03]`.

**Three habits decide whether any of that is worth anything** `[community — production practice; convergent]`:

- **Probe out of distribution, or you have tested nothing.** Put the character somewhere unlike the dataset: a costume, a painted style, a wide shot where the face is small. A LoRA that only holds up on near-copies of its training data memorised instead of learning, and in-domain prompts cannot tell you which happened.
- **Write the probe prompts before you see any results, and reuse the same set across runs.** Prompts you invent while browsing outputs drift toward what the LoRA already does well. A fixed set is the only way run 3 stays comparable to run 1.
- **Score likeness and prompt-adherence separately.** They peak at *different* checkpoints, because likeness keeps improving after flexibility has started to die. Asking "which is best?" quietly averages two things moving in opposite directions.

**Numbers are a screen, not a verdict.** `FaceEmbedDistance` (from `cubiq/ComfyUI_FaceAnalysis`, maintenance-only since April 2025; `Kidev/ComfyUI-FaceFilter` is the successor) is the quantitative signal you can actually reach. Calibrate it leave-one-out over real photos first — p50, p90, max — then use it to rank. It inflates on profiles and is too loose at half- and full-body face scale to make a ship call: **it can triage, it must never admit** `[live-use — media lab, Amy triage v17, 2026-09-05]`. DINO/CLIP-I-family metrics are **documented as significantly out of step with human judgement** on exactly this task. That is the central result of **DreamBench++** (ICLR 2025). MaSC (2026) sharpens it: CLIP-I's agreement with humans on identity is +0.135 against a human ceiling of +0.658 `[official — published benchmarks]`. These metrics also inflate when a LoRA overfits pose, so a score that climbs late in a run may just be measuring memorisation.

Run two cheap tests before shipping: a **strength sweep** (a healthy LoRA has a usable band, not a knife-edge) and a **stack test** if the LoRA will run alongside others.

Grid tooling, a copy-pasteable probe set, the cost arithmetic, and what is worth building yourself are in **`references/evaluation-and-tooling.md`**.

---

## Failure modes & QC

Read the cause column and the pattern jumps out: nearly every failure is a **dataset or caption** problem dressed up as a hyperparameter problem.

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
| Reticulated or "scale" skin, a pore grid | Sources rendered above the base's resolution band, or at too many steps on a distilled base — the texture is in the pixels before training and survives the downscale | Re-render inside the band at 8–12 steps; not rank, not the VAE `[live-use — media lab, Ciara, 2026-09-08]` |
| Grain on skin *and* background, with no LoRA loaded | A sampling artefact — cfg above 1 on a guidance-distilled checkpoint, or step count — not something the LoRA learned | cfg 1.0, fewer steps; never diagnose the LoRA before a strength-0 render |
| Skin turns crunchy at later rungs | The source medium baking in — phone-JPEG compression learned as skin | Take the lower rung; caption image quality; add better-captured frames |
| One trait cannot be prompted away (hair colour, jewellery) | A constant or a majority bound to the trigger — absences bind too | Redistribute across the same cells so nothing has a majority; caption the exception |
| Heads cut off at head-and-shoulders | The set taught a framing — crops of existing photos double-weight a composition | Remove the crops; render on a taller canvas |
| Face holds in close-up, dissolves at half body — or the reverse | Identity is learned per face-scale; the missing scale was thin in the set | Fix the identity ratio *and* the absolute close-up count |

---

## Adult and NSFW work

This skill treats adult work as a first-class case, because it is a dominant use of open-weights models and because most of the difficulty gets misdiagnosed.

**The limit is training data, not refusal.** Open-weights models do not generally refuse. They produce poor anatomy because the base model never saw much of it. That is why swapping in an abliterated ("heretic") text encoder does not work, and the author of the leading abliteration tool says so plainly: abliteration removes an LLM's ability to *refuse*, and refusal lives in output layers that a text encoder never uses `[community — -p-e-w-, author of Heretic]`. What you get from the swap is disturbed conditioning, slightly worse prompt adherence, and no new capability. Abliterated models do have one use here: **prompt expansion**, when a prompt-enhancer LLM is the thing refusing. That is a separate stage, before the encoder. **One documented exception: VLM-class encoders that refuse at the understanding level.** Krea 2's Qwen3-VL encoder rejects roughly 30% of prompted content before the diffusion model sees it. A Heretic-abliterated build is packaged for it because the swap measurably raises the share of prompts that reach the model `[community — comfyui-wiki, 2026-07-16; p-e-w/heretic]`. The myth holds for CLIP/T5-class encoders; it does not hold where the encoder is itself a refusing language model. `references/nsfw-training.md` §1.

**So base-model choice dominates.** The usual way people measure it is currently disputed (two-bar section). The proxy is **what share of a base's published LoRAs are adult-flagged**, and two measurements ten days apart disagree almost inversely on video. A 2026-08-13 sample of about 100 LoRAs per base puts **Wan 2.2 I2V highest at 90%** and Flux lowest at 28%. A 2026-08-23 re-census — 600 most-downloaded per base, reading the X/XXX bits of Civitai's `nsfwLevel` bitmask — runs from **Pony at 67%** down to **Wan 2.2 at 22–23%**. The likely explanation is that `nsfwLevel` comes from **preview images**, and a video LoRA's preview is routinely a tame first frame, so the metric undercounts video. Both tables, both methods, and the trap that the API's `nsfw` boolean is dead are in **`references/nsfw-training.md` §2**. The reproducible census script lives in [`generative-media-atlas`](../generative-media-atlas/), which owns model choice.

Two things hold whichever ordering is right. First, these percentages measure *which way an ecosystem leans*, not what a model can do. SDXL's ~31% of a far larger library is more material in absolute terms than any newer base's 60%, and SDXL is still where the purpose-built finetunes live. Second, **adult work is a dominant published use of open video models**, and that claim rests on what the video community actually ships rather than on the metric. Two models stay ruled out for reasons that have nothing to do with capability: **Ideogram 4**, by a hard filter in the model itself, and [`ltx-2-5`](../ltx-2-5/), by an acceptable-use policy that bans explicit content everywhere, local weights included.

**Stacking a capability LoRA under a character LoRA is the standard answer when a base lacks the anatomy, and it is not a reliable one** (two-bar section). One practitioner worked through four published Wan I2V anatomy LoRAs and found each either failed to render or *"changes the character lora too much"* `[community — One-Energy5403]`. The mechanism: two adapters are writing the same attention weights, and the broader one wins. Run the stack test *before* you commit to a base, not after the character LoRA is trained.

**Caption explicitly.** This is not a stylistic choice. Uncaptioned elements get absorbed into the concept, so euphemistic captions teach the model that the explicit content *is* the character. That is the failure people then go on to blame on the base model.

**Automated captioners fail here.** The community captions adult video by hand, which multiplies the cost on datasets where frame count is already the expensive part.

Anatomy failure modes, the full per-family table, and video specifics are in **`references/nsfw-training.md`**.

---

## Pre-flight checklist

Most training checklists start at the config file. This one starts three steps earlier, because a config mistake costs you one run while a likeness problem costs you the project, and no step count trains around missing angular coverage.

1. **Publishable?** If a real person is anywhere near the dataset, settle this now. Civitai bans real-person likeness at every rating, and the TAKE IT DOWN Act is in force (`references/publishing-and-likeness.md`).
2. **Base chosen for the job, not out of familiarity.** Judge it on the axes that actually differ: adult coverage, multi-character support, and the VRAM floor you can afford.
3. **If NSFW output is a goal, the anatomy source is confirmed before any training run.** The anatomy comes from the checkpoint installed on your inference stack. A character LoRA is never the anatomy source. Probe the inference base at LoRA strength 0 first. If the base cannot render it, the fix is an adult checkpoint, not dataset work (`references/nsfw-training.md`).
4. **The base-model control is part of the plan.** Before you blame any capability failure on the LoRA, run the same probes at LoRA strength 0. Four images, and it costs cents. A failure the base shares is not the LoRA's failure.
5. **Per-model trap read**, from the boundary table above. Wan's two experts, H3's rank-16 ceiling, Anima's LLM adapter and LTX's licence inheritance each cost a whole run if missed.
6. **Coverage passes** — 8-point rotation including the rear angles, one elevation above and one below, close-up through full body, neutral plus two expressions, varied lighting and settings.
7. **Curated hard** — no near-duplicates, no crops of images already in the set, no occluded faces, no flat front-lit portraits, no watermarks, consistent apparent age and build. Dedupe by eye, not by checksum: repaired and upscaled copies re-encode, so md5 never sees them (`references/dataset-and-captioning.md` §1).
8. **Sources inside the base's resolution band**, rendered at a clean step count with a plain background. On a real-photo set, nothing below the training bucket unless it was upscaled outside the trainer from real detail (`references/dataset-and-captioning.md` §3).
9. **Captions follow caption-the-residual in your encoder's dialect** — booru tags for CLIP-class, prose for LLM/T5-class. Identity absent, every varying element named, the exception captioned and the default left unwritten, and named explicitly where the content is explicit. On a generated set, captions come from what landed, not from the prompt.
10. **Trigger token matched to the model**: a rare literal token on CLIP-class; on LLM-class, whatever your model skill's recipe uses, folded into a phrase.
11. **The dataset version is frozen** before the run references it, and every arm changes **one variable** — never captions and images together.
12. **Checkpoint saving on**, at an interval that gives you a series rather than a verdict.
13. **Probe prompts written before the run**, saved in the run folder, and carried over from last time so the runs compare. At least one out of distribution, none that reuses a training caption's phrasing, a no-trigger control, and the face above ~15% of frame height on every identity probe (`references/evaluation-and-tooling.md` §4).
14. **Evaluation planned** — which grid tool, how the cells come out **coded instead of labelled**, and who makes the likeness pick. Every deployment checkpoint × resolution covered, with a strength-0 control. The face-distance baseline calibrated leave-one-out now, if you plan to use it.
15. **Budget counted in cells** if renting: checkpoints × strengths × prompts × seeds × seconds per image, worked out *before* rendering starts. Count the **training previews** the same way (`prompts × seconds per preview × steps ÷ sample_every`), because that cost stays invisible until the bill arrives.

---

## Where this fits

The boundary table at the top routes *inward*, to the per-model trap that applies to your run. This table routes *outward*, for when the job sits next to training rather than being training. Between them they define what this skill owns: only the craft that survives a change of model.

| If the job is… | Reach for |
|---|---|
| **Making** a character or style LoRA | Owned here — dataset, captioning, hyperparameter shape, evaluation, publishability |
| **Per-model** hyperparameters, trainer flags, architecture quirks | Each model skill's `references/lora-training.md`. Not owned here, deliberately: the numbers differ per model and would rot |
| **Loading and stacking** a finished LoRA | Each model skill's `references/setup-and-workflows.md`. Making and using are separate jobs across the whole suite |
| **Renting the GPU** for the run | [`comfyui-on-runpod`](../comfyui-on-runpod/) — especially the network-volume pattern, so a grid run does not re-download weights |
| **Deploying** the LoRA into a pipeline | [`image-production-workflows`](../image-production-workflows/) — the detailer-stage identity swap is a pipeline decision, not a training one |
| **Consistent characters without training** | [`qwen-image`](../qwen-image/) (Edit-2511: 1–3 references, no adapter, and the dataset factory the other image skills route through), [`flux-2`](../flux-2/) (multi-reference + PuLID), [`sdxl`](../sdxl/) (deepest adapter toolbox), each skill's `references/characters.md`. Often the better answer for a one-off |
| Training on the **lowest hardware floor** | [`anima`](../anima/) — ~6 GB, which is what makes cheap iteration possible |
| Training on **Ideogram 4** | [`ideogram-4`](../ideogram-4/) — style LoRAs are a real ecosystem there; one character-tagged LoRA of 36 exists with no recipe behind it (2026-09-09), so treat character work as exploratory |
| Holding a character in **video** | [`wan-2-2`](../wan-2-2/), [`minimax-h3`](../minimax-h3/), [`ltx-2-5`](../ltx-2-5/). The craft here applies; video adds manual captioning cost and per-architecture rules |
| Video identity with **no training path** | [`scail-2`](../scail-2/) — identity is a reference image, not an adapter, so nothing on this page applies |
| **Deciding which base to train on at all** | [`generative-media-atlas`](../generative-media-atlas/) — it splits "easiest to train on" into best likeness, fastest loop and best-documented, which have different winners, and it carries the one published cross-model comparison |

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different ways.

**Hard facts — must be exact or it breaks.** These are: Civitai's real-person policy (quoted from their published rules); the TAKE IT DOWN Act's dates, enforcement start and penalty scale (frozen for 2026); the UK creation offence and its date, the EU AI Act classification and the US state count; the DreamBench++ and MaSC results on metric misalignment; LTX-2.x's derivative-inheritance clauses; the mechanism by which abliteration fails as an encoder swap, and the VLM-encoder exception to it; and the trainer fact that buckets downscale and never upscale. **Sources are official or primary**: platform policy pages, the published benchmarks, licence text, trainer READMEs, and legal-practice summaries of the statutes. These claims carry legal and account consequences, and the regulatory picture is **still moving**. **Re-verify before relying on any of it, whoever said it, and treat this as orientation rather than legal advice.**

**Craft — what actually makes a good LoRA.** This covers caption-the-residual and its inversion, captioning the cause for traits that are identity *and* variable, the coverage protocol and the identity ratio, count-is-not-the-lever, the resolution rule and the step-count lever, the dataset factory and the seeding rules, the hyperparameter ranges, XY-grid evaluation, the blind pass and setting it up blind from the start, rung selection by probe and the lower-rung tie-break, and the overfit signals. **Two sources carry it, and the markers tell them apart.** The community bar is named trainers who have run hundreds of these: neonkisu, QuantumBogoSort, Khanykov01, NanashiAnon, L3n4, MyAIForce and the Civitai dataset guides, plus `-p-e-w-` on abliteration, MASilverHammer on Differential Output Preservation, and the trainer authors at BFL, Ostris and kohya where they publish guidance. It is stated with confidence. A range means "your dataset and base differ from theirs". The **`[live-use — media lab, …]`** bar is first-hand: 16 Krea 2 and 17 H3 runs on one real person and 6 on one synthetic character, on rented hardware, each marker naming the run and date. Those are measured single points with a named source, not consensus. The mechanisms behind them generalise; the numbers are one dataset's. Where the lab and the community disagree — steps per image, caption dropout, caption evenness, the synthetic share — the text shows both and marks the disagreement rather than picking.

Held as genuinely open:

- **The adult-flagged-share ordering.** Two censuses ten days apart disagree almost inversely on video, and neither method is clean — the preview-image basis of Civitai's `nsfwLevel` explains the video half of the gap but not the image half. `[contested]`
- **Whether a capability LoRA can be stacked under a character LoRA without destabilising it.** Four published anatomy LoRAs, none of which worked for one practitioner, and no recipe offered in reply. `[contested]`
- **Same-sex and non-heteronormative scenes** fail across SDXL, Z-Image and Krea 2 alike, and nothing in this suite answers it. The mechanism is clear — training distribution — but the fix is not. `[flagged — open gap]`
- **Optimal rank for character work** has been contested across families for years. The ranges above bracket the disagreement; the lab adds that the ceiling is model-specific. `[contested]`
- **Differential Output Preservation's transferability.** It works on Krea 2 and fails outright on Z-Image Base, and nobody has mapped which architectures it takes on. `[contested]`
- **Where the lab's recipe and the community's differ, with no head-to-head published.** Steps: BFL and ai-toolkit budget 1,500–3,000 independent of set size, the lab scales ~90–170 per image and picks the rung per dataset, and one Krea 2 report ships 10–15 images at 600–1,200 steps. Caption dropout, 0.05 against 0.3, and caption evenness against deliberate length variety. The trigger token on LLM-encoder models: BFL prescribes a made-up token, a Krea 2 report has it surfacing as a watermark, and the lab folds a `z<name>` into prose. `[contested]`
- **The synthetic share ceiling.** 14% fine, 64% failed, nothing measured between; the lab's ≤40%-to-"almost entirely" direction is unproven, and the entropy-versus-similarity-gating tension is unresolved. `[contested]`
- **The VLM-encoder exception to the abliteration rule.** Documented for Krea 2's Qwen3-VL; whether it generalises to other VLM-backed encoders is open. `[contested]`

**Facts dated 2026-09-09; community craft refreshed 2026-09-09; live-use craft extended 2026-09-09 from the media lab's Amy and Ciara ladders (2026-08-26 → 2026-09-09), each claim dated where it appears.** The legal material moves fastest, and it is what to re-check before you publish anything: Civitai's policy text, the enforcement posture around the Act, the UK and EU instruments, and the derivative terms of any non-permissive licence you train against. The adult-flagged-share figures are dated in place, disputed between two methods, and will drift as ecosystems mature — re-measure rather than reading either table forward. The lab's numbers are one character's each; re-run the arm before quoting a figure as general.

---

## Reference files

| File | When to read it |
|---|---|
| `references/dataset-and-captioning.md` | Building the set: why count is not the lever (measured three ways), the 8-point rotation protocol and the starved-axes audit, the identity ratio, face-scale and why tiny faces teach a smeared average, curation criteria, **the resolution rule — render or source inside the base's band, the step-count lever, the wall test and the wrong turn named**, captioning by model with the trigger-token dispute and what becomes promptable, multi-outfit limits, and Differential Output Preservation for multi-character work |
| `references/synthetic-datasets.md` | Generating the set: the dataset-factory loop and the three rules from a shipped 32-cell set, the packaged VNCCS suite, seeding from an older LoRA's renders — the recursion hazard, the measured 14%-fine / 64%-failed points and the rules that keep seeding safe — and the video turnaround with its cost and licence caveats |
| `references/nsfw-training.md` | Adult work in depth: both adult-flagged-share censuses with their methods and why they disagree, per-family base selection, the character-vs-capability-LoRA scale difference and why stacking them is unreliable, the same-sex coverage gap, why the encoder-swap myth persists, explicit-captioning practice, anatomy failure modes, and the manual-captioning cost on video |
| `references/evaluation-and-tooling.md` | Judging a run at home: which grid tool and its limits, the A–F stage ladder, the blind-judging pass and how to set it up blind from the start, pairs over scores, the margin record and judge fatigue, the lower-rung tie-break and which-probe-regressed, diagnosing a quality regression, what training previews really cost and why they understate likeness on a two-half model, a copy-pasteable probe set with its design rules, face-distance triage with leave-one-out calibration and its blind spots, cost arithmetic for rented GPUs, and the one small script worth writing yourself |
| `references/publishing-and-likeness.md` | Whether a LoRA is publishable at all: Civitai's rules in full, the TAKE IT DOWN Act, licence inheritance on non-permissive models, dataset provenance, the synthetic-character resemblance test, and where distribution is still open |
