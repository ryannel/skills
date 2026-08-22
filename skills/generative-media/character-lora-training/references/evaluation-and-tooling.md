# Evaluating a run: tooling and protocol

Written for someone training on a consumer GPU or a modestly rented one — a handful of runs a week, not a lab. The professional tier is sketched at the end only so you can tell what you are choosing not to do.

The uncomfortable premise: **at this scale you are the measuring instrument, and you are biased in a known direction.** You know which checkpoint trained longer, you want the run to have worked, and you have been staring at this face for an hour. Almost everything below is about getting a usable reading anyway, cheaply.

## Contents

1. [Layer 1 — samples during training](#1-layer-1--samples-during-training)
2. [Layer 2 — the grid, and the tools that build it](#2-layer-2--the-grid-and-the-tools-that-build-it)
3. [Layer 3 — judging without fooling yourself](#3-layer-3--judging-without-fooling-yourself)
4. [The held-out probe set](#4-the-held-out-probe-set)
5. [Putting a number on it](#5-putting-a-number-on-it)
6. [What a run costs](#6-what-a-run-costs)
7. [What to build yourself](#7-what-to-build-yourself)
8. [What the professional tier does](#8-what-the-professional-tier-does)

---

## 1. Layer 1 — samples during training

Every trainer generates sample images at intervals — kohya, OneTrainer, AI-Toolkit, musubi-tuner. This is free, it is already on, and it is the cheapest signal you will get.

**Two things make samples worth reading:**

- **Fix the seed.** A varying seed makes each sample a different image and you cannot tell learning from luck. A fixed seed makes the sequence a time-lapse of one image acquiring the identity.
- **Use 3–5 sample prompts, not one.** One prompt tells you the LoRA learned *that prompt*. Include at least one prompt describing something the dataset never showed.

**What to read off them:**

| What you see across steps | What it means |
|---|---|
| Identity emerging gradually, background still varying | Healthy. This is the shape you want |
| Identity appears, then everything stiffens into one look | You have passed the peak — the useful checkpoints are behind you |
| Samples get *smoother* and waxier late | Over-training. Late-run over-smoothing looks like "quality" in a thumbnail and is not |
| Nothing resembling the subject by 40% of the run | Something is wrong with captions or config — stop and check rather than waiting it out |

**Do not pick your final checkpoint from samples.** Trainer previews use the trainer's sampler and settings, not your production ones, so a checkpoint can look better here and worse in ComfyUI. Samples tell you *roughly where the useful region is* so the grid in layer 2 can be small.

**Loss is close to useless for this** and the community is right about that. The exception worth knowing: **OneTrainer supports genuine validation loss** — you flag separate concepts as validation data (explicitly *not* your training images) and it graphs per-concept validation loss to TensorBoard. That is a real held-out signal none of the other trainers give you, and it is free. If validation loss turns up while sample images still look fine, you are watching overfit begin.

---

## 2. Layer 2 — the grid, and the tools that build it

The standard move is a grid of **checkpoint × LoRA strength** on fixed prompts and a fixed seed. It is standard because it works. What follows is which tool to use, because the suite has been prescribing the method without naming an implementation.

| Tool | Use it when |
|---|---|
| **SwarmUI Grid Generator** | **The default recommendation.** Built into SwarmUI by default as a reference extension, no install. Grids are infinite-dimensional, and the "Web Page" output is an interactive live-viewer that lets you reorganise the view and display up to 4 axes at a time, swapping freely between them. That last part is the reason to prefer it — a static grid image locks you to 3 axes and one arrangement |
| **A1111 / Forge X/Y/Z plot** | Already in your UI and you want two axes and nothing else. The original; Grid Generator began as Infinity Grid Generator for A1111 |
| **Efficiency Nodes — `XY Input: LoRA Plot`** | You live in ComfyUI and want the grid inside the workflow that will actually run in production |
| **ComfyUI-LoRAWeightAxisXY** | Strength sweeps specifically, as an axis for Efficiency Nodes |
| **Published workflows** — "LoRA Testing: Epochs vs Seeds", Civitai's "Easy LoRA Checker" | You want a working grid in five minutes rather than wiring one |
| **rgthree `Image Comparer`**, built-in `ImageCompare` | Final head-to-head between two survivors. Wipe-slider, excellent for two, useless for twelve |

**A note on SwarmUI's LoRA handling:** the Grid Generator has no dedicated LoRA-model axis. You vary LoRAs through **prompt replace** — put `<lora:mylora>` in the prompt and give replacements `mylora, myotherlora, mythirdlora`. It works fine for checkpoint sweeps once you know to do it that way; people lose an evening looking for an axis that isn't there.

**Keep the grid small.** Cells multiply: 6 checkpoints × 4 strengths × 4 prompts × 1 seed is 96 images, which is already a long wait on a home GPU. Use layer 1 to narrow the checkpoint range first, then spend the grid on the range that might actually win.

---

## 3. Layer 3 — judging without fooling yourself

This is the part no tool does for you, and it is where a home setup can genuinely match a professional one, because it costs nothing.

**The problem with grids is that they are labelled.** That is their function — the axes are the point. But it means that when you look at a cell you already know it is epoch 8 rather than epoch 4, and expectation does the rest. Every grid tool listed above has this property. It is not a flaw in them; it is a reason not to let the grid be your final judgement.

**The cheap fix — a blind pass:**

1. Pick one strength and one prompt at a time.
2. Show the candidate checkpoints **shuffled, unlabelled**, side by side.
3. Choose the best. Or choose **"none of these are acceptable"**, which is a distinct and important answer.
4. Only then look at which was which.

You can do this by renaming files to `A.png`, `B.png`, `C.png` from a shuffled order — a ten-line script, or by hand. It sounds fussy. It routinely reverses the answer people got from the labelled grid.

**Score likeness and prompt-adherence separately.** They peak at different checkpoints, reliably: likeness keeps improving after flexibility has started to die. Asking "which is best?" forces you to silently average two axes that are moving in opposite directions, and the answer you get depends on which one you happened to be looking at. Ask twice:

- *Which of these is closest to the person?*
- *Which of these best did what the prompt asked?*

If those give different answers — and they usually do — the gap between them is your usable range, and which end you pick depends on whether this LoRA is for portraits or for putting the character in scenes.

**A prompt that fails on every checkpoint is a dataset finding, not a checkpoint finding.** This distinction is worth building into the habit. If "profile view" is bad at epoch 4 and epoch 12 and every strength, no choice of checkpoint will fix it — your dataset lacks profile coverage, and the answer is another training run with a better set. Write those prompts down separately from your checkpoint verdict; they are the specification for the next dataset.

---

## 4. The held-out probe set

**Write your test prompts before you look at any results, and reuse the same set across runs.** Prompts invented while browsing outputs drift toward what the LoRA happens to do well. A fixed set also makes run 3 comparable to run 1, which is otherwise impossible to recover.

Keep it in the run folder as a plain file. A workable starter set, grouped by what each group is actually testing:

```yaml
# baseline — should always work; if these fail, something is broken
- id: base-portrait
  text: "<trigger>, portrait, neutral expression, plain grey background, soft even lighting"
- id: base-upper
  text: "<trigger>, upper body, looking at the camera, natural daylight"

# coverage — the angles and framings datasets usually miss
- id: cov-profile
  text: "<trigger>, strict side profile view, plain background"
- id: cov-full
  text: "<trigger>, full body standing, wide shot, street background"
- id: cov-expression
  text: "<trigger>, laughing, candid, indoor lighting"

# flexibility — nothing like the dataset; this is where overfit shows
- id: flex-style
  text: "<trigger>, oil painting, thick visible brushstrokes, museum lighting"
- id: flex-costume
  text: "<trigger>, wearing full medieval plate armour, castle courtyard"
- id: flex-scene
  text: "<trigger>, sitting in a crowded diner, seen from across the room, wide shot"
```

Two things that set does deliberately. **`flex-scene` puts the face small in frame** — this is the case that reveals whether identity survives at low pixel counts, and it is the most common failure people never test for until production. And **`flex-style` fights the LoRA on purpose**: an over-trained character LoRA drags every output back toward photographic, and this prompt makes that visible in one image.

Add a group for whatever your actual use is. If the LoRA exists to make adult content, probe it there too — a LoRA that holds identity in a portrait and loses it in the work you built it for has not been tested, and `nsfw-training.md` covers why those failures cluster differently.

---

## 5. Putting a number on it

**`cubiq/ComfyUI_FaceAnalysis` provides the `FaceEmbedDistance` node** — InsightFace/ArcFace or DLib backends, cosine or Euclidean distance between a batch of reference faces and a candidate. This is the accessible way to get a number out of a home setup, and it is a real one.

**Calibrate a baseline first, or the number is meaningless.** Take 3 real photos of the subject as the reference batch and score a *4th real photo* against them. That value is your floor — the distance you get between genuine photographs of the same person under different conditions. Generations are then read against that floor, not against zero. Skipping this step is the most common way the node gets misused.

**Then treat it as a screen, not a verdict.** This is a hard finding rather than a caution:

> The standard personalization metrics — **DINO and CLIP-I for subject fidelity, CLIP-T for prompt following** — show significant discrepancies from human judgement, because they are image-*similarity* models being asked a question that is not similarity. This is the central result of **DreamBench++** (ICLR 2025). `[official — published benchmark]`

ArcFace distance is in the same family and inherits the problem. There is a specific failure to watch for: **similarity scores inflate when a LoRA overfits face position and pose**, because the metric rewards spatial resemblance it should be ignoring. So a score that climbs through late checkpoints can be measuring memorisation, and reading it as improving fidelity gets you exactly the wrong checkpoint.

**Two free signals that partly cover the gap**, both computable from images you have already generated:

- **Diversity collapse.** Generate the same prompt at several seeds. Measure how different the outputs are from each other. When that spread falls off a cliff at some checkpoint, that checkpoint has stopped generating and started reciting. This is a good overfit detector precisely because it does not depend on a similarity model being human-aligned.
- **Sharpness** (Laplacian variance, a few lines with OpenCV). Catches early blur *and* late waxy over-smoothing — one metric, two failure modes at opposite ends of the run.

Use the numbers to **rank candidates and flag suspects**. Use the blind pass in §3 to decide. Machine advisory, human decisive.

---

## 6. What a run costs

Nothing here is priced in currency, because GPU rates move and the numbers would rot. Price it in **cells**, which don't.

| Stage | Cost | Notes |
|---|---|---|
| Training samples | **Free** | Already running. A few seconds per sample |
| OneTrainer validation loss | **Free** | Some extra steps per validation interval |
| The grid | **The real cost.** cells = checkpoints × strengths × prompts × seeds | 96 cells is a comfortable ceiling at home; 400 is an afternoon |
| Blind judging | **Free** | Reuses grid images. Costs attention, not compute |
| FaceEmbedDistance scoring | **Effectively free** | CPU-viable, reuses grid images |

**Where the money actually goes if you rent:** the grid, and only the grid. Which makes the narrowing move in §2 the single highest-value habit — using free training samples to cut the checkpoint range from 12 to 4 before rendering cuts the bill by two-thirds and loses nothing, because you were never going to ship the checkpoints the samples showed as blurry.

**If you rent, estimate before you render.** Multiply the four numbers, multiply by your seconds-per-image, and look at the result before starting. A grid that quietly became 600 cells is the classic way a cheap validation run stops being cheap. If you are renting on RunPod, [`comfyui-on-runpod`](../../comfyui-on-runpod/) covers keeping the models on a network volume so a grid run does not re-download weights every time — which otherwise costs more than the rendering.

---

## 7. What to build yourself

**Do not build a trainer, and do not build a grid renderer.** Both are solved, and the tools in §2 are better than what you would write.

**The thing worth building is small**, and it is the thing no tool provides: a script that takes a folder of grid outputs and

1. renames a shuffled subset to `A/B/C…` for a blind pass,
2. records your picks — best-likeness and best-adherence, separately, per prompt,
3. writes the result next to the run with the checkpoint identities restored.

That is an afternoon, it is the highest-value hour in this entire document, and it persists across runs so that run 5 can be compared with run 2.

**Add these only if the first one is earning its keep:** FaceEmbedDistance scoring over the same folder, and a per-prompt summary that flags prompts weak across *all* checkpoints — your next dataset's to-do list.

**The thing you will be tempted to build and should not:** a general evaluation platform. The reason nothing off-the-shelf exists for this job is that the probes and the pass criteria are per-project by nature — which prompts matter and what "the face holds" means are yours, and change per character. Generalising that is a product, not a tool, and you will spend the time you meant to spend training.

---

## 8. What the professional tier does

Not the target audience for this file, but worth knowing which of it is worth borrowing.

| What they do | Worth borrowing at home? |
|---|---|
| **Experiment tracking** — W&B as the industry standard: every run logged with full hyperparameter config, dataset version, loss curves, eval results. W&B **Weave** now has an image-eval framework (dataset + scorers + comparison dashboard, model-agnostic and documented for diffusion) | **Partly.** The full platform is overkill; the *habit* is not. A folder per run with the config, the probe set and the verdict in it gets you most of the value for nothing |
| **Benchmark suites** — **DreamBench++** for personalization (7 methods × 150 subjects × 9 prompts); **VBench/VBench++** for video across 16 dimensions | **No, and this is the key point.** These compare *methods* across *the benchmark's* subjects. You need to compare *checkpoints* on *your* subject. Different unit of analysis — running DreamBench++ tells you nothing about your character |
| **Reward models** — ImageReward, PickScore, HPSv2/HPSv3++ | **Rarely.** They predict aggregate human preference for general aesthetics, not whether this is the right person |
| **VLM-as-judge** — the field has converged on VQA/VLM-mediated scoring, and it is where the metric layer went after DINO/CLIP-I | **The finding is, even if the tooling isn't.** Raw pointwise VLM judging is unreliable — Qwen3-VL-8B scores **26.5% pointwise vs 59.4% as a direct pairwise judge**. Pairwise beats pointwise, which is the same reason the blind head-to-head in §3 beats scoring cells one at a time. You can apply that conclusion with no infrastructure at all |

**VBench's subject-consistency dimension** is the one genuinely borrowable idea for video work: identity stability measured across frames via DINO feature similarity. It gives temporal identity drift a number, where at home it is usually a shrug. Same alignment caveat as §5 applies.

---

## How to read the claims in this file

**Hard facts.** The DreamBench++ result on DINO/CLIP-I misalignment, the pointwise-vs-pairwise VLM judging figures, VBench's dimension set, and what each named tool does and does not support (including SwarmUI's lack of a LoRA axis and its 3-axis grid-image / 4-axis web-page limits). **Sources are published benchmarks, papers and project READMEs.** These are checkable and were checked.

**Craft.** The blind pass, splitting likeness from adherence, the fixed probe set, weak-everywhere prompts as a dataset signal, the narrow-then-render budget habit. **This is community and production practice** rather than measured result — it comes from people running these repeatedly, and from a working private pipeline whose design the pairwise finding independently supports. Stated with confidence; adapt the specifics.

One thing genuinely open: **there is no accepted home-scale metric for character-LoRA fidelity.** ArcFace distance is what is reachable and it is known-imperfect; VLM judging is where the field went but has no turnkey local tooling at this scale. Expect this section to change. `[contested]`

**Facts dated 2026-08-22.** The tooling layer moves fastest here — grid extensions, the `FaceEmbedDistance` node's backends, and whatever local VLM-judging tooling appears next — so re-verify a named tool's current state before building a habit around it.
