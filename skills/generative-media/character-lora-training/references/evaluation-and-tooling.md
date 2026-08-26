# Evaluating a run: tooling and protocol

Written for someone training on a consumer GPU or a modestly rented one — a handful of runs a week, not a lab. The professional tier is sketched at the end only so you can tell what you are choosing not to do.

Start from the uncomfortable bit: **at this scale you are the measuring instrument, and you lean in a known direction.** You know which checkpoint trained longer. You want the run to have worked. And you have been staring at this face for an hour. Almost everything below is about getting a usable reading anyway, cheaply.

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

Every trainer draws sample images as it goes — kohya, OneTrainer, AI-Toolkit, musubi-tuner. It is already switched on, and it is the cheapest signal you will get.

**Two things make samples worth reading:**

- **Fix the seed.** With a changing seed every sample is a different image, and you cannot tell learning from luck. With a fixed seed the sequence becomes a time-lapse of one image picking up the identity.
- **Use 3–5 sample prompts, not one.** One prompt tells you the LoRA learned *that prompt*. Include at least one prompt describing something the dataset never showed.

**What to read off them:**

| What you see across steps | What it means |
|---|---|
| Identity emerging gradually, background still varying | Healthy. This is the shape you want |
| Identity appears, then everything stiffens into one look | You have passed the peak — the useful checkpoints are behind you |
| Samples get *smoother* and waxier late | Over-training. Late-run over-smoothing looks like "quality" in a thumbnail and is not |
| Nothing resembling the subject by 40% of the run | Suspicious, but **not on its own a reason to restart** — read the next two paragraphs before touching the config |

**Do not pick your final checkpoint from samples.** Trainer previews use the trainer's sampler and settings, not your production ones, so a checkpoint can look better here and worse in ComfyUI. Samples tell you *roughly where the useful region is* so the grid in layer 2 can be small.

**Some models come in two halves, and previews from the training half look worse than the truth.** Several models here ship a slow, undistilled version you train on and a fast version you actually deploy — Krea 2 Raw and Turbo, Z-Image Base and Turbo, Flux dev and schnell. The trainer draws its previews with the training half, at high guidance and a lot of steps. That combination smears exactly the details a face is recognised by: skin texture and fine bone structure. So the likeness looks weaker than it really is. Load the same weights on the fast half and the person is plainly there.

One measured run shows how wide the gap gets. At step 750 of 2250 the previews were clean pictures of a generic face, with the subject's freckles missing. By step 1500 she was unmistakable. On the deployment model the shipped checkpoint looked sharper than any preview had `[community — production run, Krea 2 + AI-Toolkit, 25 real photos, 2026-08-24]`.

Two rules follow, and they are the ones that save a run:

- **Wait until about 60–70% of the run before you worry.** The 40% row above was written for trainers that preview on the same model you deploy on. On a two-half model it fires early and talks you into restarting a healthy run. A generic face a third of the way in is normal.
- **Check on the deployment model before you change anything.** One image at your real settings answers the question the previews cannot, and costs a tiny fraction of a restart. Restarting because of a preview is the expensive version of this mistake: every restart pays again for loading the model and rebuilding the caches.

**Previews can burn more GPU time than the training does, and almost nobody budgets for them.** The cost is `prompts × seconds per preview × (steps ÷ sample_every)`. On an undistilled model at high guidance one preview takes tens of seconds, not two or three. In the run above, 6 prompts at about 89 seconds each, every 250 steps, added up to roughly **80 minutes of previews on a 75-minute training job**. That more than doubled the bill — to produce the reading the paragraphs above tell you not to trust. Three fixes, all free:

- **Split `save_every` from `sample_every`.** Checkpoints are what you shop from later, so save them often. Previews are only a rough "is it working yet" check, so make them rare. One every third checkpoint is plenty.
- **Skip the preview at step 0.** It draws the base model with an untrained adapter. You already know what that looks like.
- **Cut the preview step count.** Previews answer "is the identity arriving", not "is this good". Half your normal steps reads the same.

Before you rent a GPU, do that multiplication the same way §6 has you count grid cells. If previews come out as a real slice of the training time, that is a bug in the config, not a setting.

**Loss is close to useless here**, and the community is right about that. One exception is worth knowing: **OneTrainer supports real validation loss.** You mark separate concepts as validation data — explicitly *not* your training images — and it graphs per-concept validation loss to TensorBoard. That is a genuine held-out signal no other trainer gives you, and it costs nothing. If validation loss turns upward while the sample images still look fine, you are watching overfitting start.

---

## 2. Layer 2 — the grid, and the tools that build it

The standard move is a grid of **checkpoint × LoRA strength**, on fixed prompts and a fixed seed. It is standard because it works. Below is which tool to use — the suite has been prescribing the method without ever naming a tool for it.

| Tool | Use it when |
|---|---|
| **SwarmUI Grid Generator** | **The default recommendation.** Ships with SwarmUI as a reference extension, so there is nothing to install. Grids can have any number of axes, and the "Web Page" output is a live viewer that shows up to 4 axes at once and lets you swap between them freely. That last part is the reason to prefer it: a static grid image locks you into 3 axes and one arrangement |
| **A1111 / Forge X/Y/Z plot** | Already in your UI and you want two axes and nothing else. The original; Grid Generator began as Infinity Grid Generator for A1111 |
| **Efficiency Nodes — `XY Input: LoRA Plot`** | You live in ComfyUI and want the grid inside the workflow that will actually run in production |
| **ComfyUI-LoRAWeightAxisXY** | Strength sweeps specifically, as an axis for Efficiency Nodes |
| **Published workflows** — "LoRA Testing: Epochs vs Seeds", Civitai's "Easy LoRA Checker" | You want a working grid in five minutes rather than wiring one |
| **rgthree `Image Comparer`**, built-in `ImageCompare` | Final head-to-head between two survivors. Wipe-slider, excellent for two, useless for twelve |

**One note on SwarmUI's LoRA handling:** the Grid Generator has no LoRA-model axis. You vary LoRAs through **prompt replace** instead — put `<lora:mylora>` in the prompt and give the replacements `mylora, myotherlora, mythirdlora`. It works fine for checkpoint sweeps once you know to do it that way. People lose an evening hunting for an axis that is not there.

**Keep the grid small.** Cells multiply fast: 6 checkpoints × 4 strengths × 4 prompts × 1 seed is 96 images, which is already a long wait on a home GPU. Use layer 1 to narrow the checkpoint range first, then spend the grid on the range that could actually win.

---

## 3. Layer 3 — judging without fooling yourself

No tool does this part for you, and it is where a home setup can genuinely match a professional one, because it costs nothing.

**The problem with grids is that they are labelled.** That is what they are for — the axes are the point. But it means that when you look at a cell, you already know it is epoch 8 rather than epoch 4, and expectation does the rest. Every grid tool above works this way. That is not a flaw in them. It is a reason not to let the grid make your final decision.

**The cheap fix — a blind pass:**

1. Pick one strength and one prompt at a time.
2. Show the candidate checkpoints **shuffled, unlabelled**, side by side.
3. Choose the best. Or choose **"none of these are acceptable"**, which is a distinct and important answer.
4. Only then look at which was which.

You can do this by renaming files to `A.png`, `B.png`, `C.png` from a shuffled order — a ten-line script, or by hand. It sounds fussy. It routinely flips the answer people got from the labelled grid.

**Make it blind from the start, not by willpower.** Knowing about this bias does not protect you from it. The labelled grid gets drawn first, and then you are supposed to ignore what it tells you. That does not work. The labelled sheet is sitting right there, it is the obvious thing to open, and a run that took hours wants an answer now. So do not make that file at all. Have whatever draws your grid write out **coded cells plus a separate key**, and leave the key shut until you have written down a pick:

1. Render every cell under a shuffled code — `A`, `B`, `C`…
2. Save the code-to-checkpoint mapping in a `BLIND_KEY.json` next to them. Do not open it.
3. Write down your pick — best likeness and best prompt-adherence, separately, for each prompt.
4. Now open the key.

Same images, same cost. The one thing that changes is that no file ever exists showing you a picture and its checkpoint number side by side. That is worth more than promising yourself you will ignore one. It also holds up when someone else runs the eval for you, agent or human, because "was the key still shut when the pick was written?" is something you can check and "were you biased?" is not. This is the concrete version of the build-it-yourself advice in §7: the shuffling is not a bonus on top of a grid tool, it is the part grid tools do not do.

**Still draw the labelled grid — just afterwards.** Once the pick is recorded, the labelled view is the best way to see the shape of the run: where the likeness arrived, how wide the usable strength band is, whether late checkpoints go stiff. It is a bad judge and a good explanation.

**If the subject is a real person, the person who knows that face makes the pick.** You cannot judge how much a picture looks like someone you have never met, and neither can a metric. You can check the broad structure against a reference photo, but the part that reads as *them* is exactly what a stranger's eye misses. So split the job: **whoever ran the training builds the blind set and says what each prompt was testing; whoever knows the subject chooses.** Prompt-adherence is the opposite case — anyone can score a picture against the prompt text, so that half does not have to wait.

**Do not promote a checkpoint until the pick is settled.** Whatever gets copied into the LoRA folder is the one that gets used forever, so a "temporary" promotion quietly becomes permanent. If you have to hand someone a file early — to let them try it, or because the rented machine is about to disappear — label it **provisional** in the sidecar, name the pick you are waiting on, and keep the other candidates. Deleting the alternatives is how "we will confirm this properly later" turns into a decision nobody made.

**Score likeness and prompt-adherence separately.** They reliably peak at different checkpoints, because likeness keeps improving after flexibility has started to die. Asking "which is best?" makes you average two things moving in opposite directions, and the answer depends on whichever one you happened to be looking at. So ask twice:

- *Which of these is closest to the person?*
- *Which of these best did what the prompt asked?*

If the two answers differ — and they usually do — the gap between them is your usable range. Which end you pick depends on whether this LoRA is for portraits or for putting the character into scenes.

**A prompt that fails on every checkpoint tells you about your dataset, not your checkpoints.** Build that distinction into the habit. If "profile view" is bad at epoch 4, at epoch 12 and at every strength, no choice of checkpoint will fix it. Your dataset lacks profile coverage, and the answer is another training run with a better set. Write those prompts down separately from your checkpoint verdict — they are the spec for your next dataset.

---

## 4. The held-out probe set

**Write your test prompts before you look at any results, and reuse the same set across runs.** Prompts you invent while browsing outputs drift toward whatever the LoRA already does well. A fixed set is also the only way run 3 stays comparable to run 1 — you cannot recover that later.

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

That set does two things on purpose. **`flex-scene` puts the face small in the frame**, which is what shows you whether the identity survives at low pixel counts — the most common failure nobody tests for until production. And **`flex-style` fights the LoRA deliberately**: an over-trained character LoRA drags every output back toward photographic, and this prompt makes that visible in a single image.

Add a group for whatever you actually use it for. If the LoRA exists to make adult content, probe it there too. A LoRA that holds the identity in a portrait but loses it in the work you built it for has not been tested, and `nsfw-training.md` covers why those failures cluster differently.

---

## 5. Putting a number on it

**`cubiq/ComfyUI_FaceAnalysis` provides the `FaceEmbedDistance` node** — InsightFace/ArcFace or DLib backends, cosine or Euclidean distance between a batch of reference faces and a candidate. This is the accessible way to get a number out of a home setup, and it is a real one.

**Calibrate a baseline first, or the number means nothing.** Take 3 real photos of the subject as the reference batch, then score a *4th real photo* against them. That value is your floor: the distance you get between genuine photographs of the same person in different conditions. Read your generations against that floor, not against zero. Skipping this step is the most common way this node gets misused.

**Then treat it as a screen, not a verdict.** This is a hard finding rather than a caution:

> The standard personalization metrics — **DINO and CLIP-I for subject fidelity, CLIP-T for prompt following** — show significant discrepancies from human judgement, because they are image-*similarity* models being asked a question that is not similarity. This is the central result of **DreamBench++** (ICLR 2025). `[official — published benchmark]`

ArcFace distance is in the same family and inherits the problem. Watch for one specific failure: **similarity scores inflate when a LoRA overfits face position and pose**, because the metric rewards spatial resemblance it ought to be ignoring. So a score that climbs through the late checkpoints may just be measuring memorisation — and reading it as improving fidelity hands you exactly the wrong checkpoint.

**Two free signals that partly cover the gap**, both computable from images you have already generated:

- **Diversity collapse.** Generate the same prompt at several seeds and measure how different the outputs are from each other. When that spread falls off a cliff at some checkpoint, that checkpoint has stopped generating and started reciting. It is a good overfit detector precisely because it does not rely on a similarity model agreeing with human judgement.
- **Sharpness** (Laplacian variance, a few lines with OpenCV). Catches early blur *and* late waxy over-smoothing — one metric, two failure modes at opposite ends of the run.

Use the numbers to **rank candidates and flag suspects**. Use the blind pass in §3 to decide. Machine advisory, human decisive.

---

## 6. What a run costs

Nothing here is priced in currency, because GPU rates move and the numbers would rot. Price it in **cells**, which don't.

| Stage | Cost | Notes |
|---|---|---|
| Training samples | **Not free on a rented GPU** | They share the GPU the training is already paying for. Count them as `prompts × seconds per preview × (steps ÷ sample_every)` — on an undistilled model that can come to more than the training itself (§1) |
| OneTrainer validation loss | **Free** | Some extra steps per validation interval |
| The grid | **The real cost.** cells = checkpoints × strengths × prompts × seeds | 96 cells is a comfortable ceiling at home; 400 is an afternoon |
| Blind judging | **Free** | Reuses grid images. Costs attention, not compute |
| FaceEmbedDistance scoring | **Effectively free** | CPU-viable, reuses grid images |

**If you rent, the money goes on the grid, and only the grid.** That makes the narrowing move in §2 your single highest-value habit. Using the training previews to cut the checkpoint range from 12 to 4 before you render cuts the bill by two-thirds and loses you nothing, because you were never going to ship the checkpoints the previews showed as blurry.

**If you rent, work out the cost before you render.** Multiply the four numbers, multiply by your seconds per image, and look at the result before you start. A grid that quietly grew to 600 cells is the classic way a cheap validation run stops being cheap. If you are renting on RunPod, [`comfyui-on-runpod`](../../comfyui-on-runpod/) covers keeping the models on a network volume so a grid run does not re-download weights every time — which otherwise costs more than the rendering.

---

## 7. What to build yourself

**Do not build a trainer, and do not build a grid renderer.** Both are solved problems, and the tools in §2 are better than anything you would write.

**The thing worth building is small**, and no tool provides it: a script that drives the render itself, so the pictures arrive already blind. It should

1. write every cell under a shuffled code (`A/B/C…`), with the mapping in a `BLIND_KEY.json` you leave shut,
2. record your picks — best likeness and best adherence, separately, per prompt,
3. write the result next to the run with the checkpoint names filled back in.

The order matters. A script that renames files *after* a labelled grid has been drawn leaves the labelled grid sitting on disk, and §3 is about that file never existing.

That is an afternoon, it is the highest-value hour in this entire document, and it persists across runs so that run 5 can be compared with run 2.

**Add these only if the first one is earning its keep:** FaceEmbedDistance scoring over the same folder, and a per-prompt summary that flags prompts weak across *all* checkpoints — your next dataset's to-do list.

**The thing you will be tempted to build, and should not:** a general evaluation platform. Nothing off-the-shelf exists for this job because the probes and the pass criteria are project-specific by nature. Which prompts matter, and what "the face holds" means, are yours — and they change with every character. Generalising that is a product, not a tool, and building it costs you the time you meant to spend training.

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

**Craft.** The blind pass and the trick of making it blind from the start, scoring likeness and adherence separately, who gets to make the pick when the subject is a real person, holding a checkpoint as provisional, the fixed probe set, weak-everywhere prompts as a dataset signal, the narrow-then-render budget habit, and §1's readings on preview cost and two-half models. Those last two come from one production run and are dated where they appear: trust the mechanism, treat the numbers as a single data point. **This is community and production practice** rather than measured result — it comes from people running these repeatedly, and from a working private pipeline whose design the pairwise finding independently supports. Stated with confidence; adapt the specifics.

One thing genuinely open: **there is no accepted home-scale metric for character-LoRA fidelity.** ArcFace distance is what is reachable and it is known-imperfect; VLM judging is where the field went but has no turnkey local tooling at this scale. Expect this section to change. `[contested]`

**Facts dated 2026-08-22.** The tooling layer moves fastest here — grid extensions, the `FaceEmbedDistance` node's backends, and whatever local VLM-judging tooling appears next — so re-verify a named tool's current state before building a habit around it.
