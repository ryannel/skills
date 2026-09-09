# Evaluating a run: tooling and protocol

This file is written for someone training on a consumer GPU, or on a modestly rented one. That means a handful of runs a week, not a lab. The professional tier is sketched at the end, and only so you can tell what you are choosing not to do.

Start with the uncomfortable part: **at this scale you are the measuring instrument, and you lean in a known direction.** You know which checkpoint trained longer. You want the run to have worked. And you have been staring at this face for an hour. Almost everything below is about getting a usable reading anyway, and getting it cheaply.

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

Every trainer draws sample images as it goes. Kohya, OneTrainer, AI-Toolkit, and musubi-tuner all do this. It is already switched on, and it is the cheapest signal you will get.

**Two things make samples worth reading:**

- **Fix the seed.** With a changing seed, every sample is a different image, and you cannot tell learning from luck. With a fixed seed, the sequence becomes a time-lapse of one image picking up the identity.
- **Use 3–5 sample prompts, not one.** One prompt only tells you the LoRA learned *that prompt*. Include at least one prompt describing something the dataset never showed.

**What to read off them:**

| What you see across steps | What it means |
|---|---|
| Identity emerging gradually, background still varying | Healthy. This is the shape you want |
| Identity appears, then everything stiffens into one look | You have passed the peak. The useful checkpoints are behind you |
| Samples get *smoother* and waxier late | Over-training. Late-run over-smoothing looks like "quality" in a thumbnail, but it is not |
| Nothing resembling the subject by 40% of the run | Suspicious, but **not on its own a reason to restart**. Read the next two paragraphs before touching the config |

**Do not pick your final checkpoint from samples.** Trainer previews use the trainer's sampler and settings, not your production ones. A checkpoint can therefore look better in previews and worse in ComfyUI. Samples tell you *roughly where the useful region is*, so that the grid in layer 2 can stay small.

**Some models come in two halves, and previews from the training half look worse than the truth.** Several models in this suite ship a slow, undistilled version that you train on and a fast version that you actually deploy. Krea 2 Raw and Turbo, Z-Image Base and Turbo, and Flux dev and schnell all follow this pattern. The trainer draws its previews with the training half, at high guidance and a lot of steps. That combination smears exactly the details a face is recognised by: skin texture and fine bone structure. As a result the likeness looks weaker than it really is. Load the same weights on the fast half and the person is plainly there.

One measured run shows how wide the gap gets. At step 750 of 2250, the previews were clean pictures of a generic face, and the subject's freckles were missing. By step 1500 she was unmistakable. On the deployment model, the shipped checkpoint looked sharper than any preview had `[community — production run, Krea 2 + AI-Toolkit, 25 real photos, 2026-08-24]`.

Two rules follow from this, and they are the rules that save a run:

- **Wait until about 60–70% of the run before you worry.** The 40% row in the table above was written for trainers that preview on the same model you deploy on. On a two-half model, that row fires early and talks you into restarting a healthy run. A generic face a third of the way in is normal.
- **Check on the deployment model before you change anything.** One image at your real settings answers the question the previews cannot, and it costs a tiny fraction of a restart. Restarting because of a preview is the expensive version of this mistake, because every restart pays again for loading the model and rebuilding the caches.

**Previews can burn more GPU time than the training does, and almost nobody budgets for them.** The cost is `prompts × seconds per preview × (steps ÷ sample_every)`. On an undistilled model at high guidance, one preview takes tens of seconds rather than two or three. In the run above, 6 prompts at about 89 seconds each, drawn every 250 steps, added up to roughly **80 minutes of previews on a 75-minute training job**. That more than doubled the bill, and it did so to produce the reading the paragraphs above tell you not to trust. Three fixes exist, and all of them are free:

- **Split `save_every` from `sample_every`.** Checkpoints are what you shop from later, so save them often. Previews are only a rough "is it working yet" check, so make them rare. One every third checkpoint is plenty.
- **Skip the preview at step 0.** It draws the base model with an untrained adapter. You already know what that looks like.
- **Cut the preview step count.** Previews answer "is the identity arriving", not "is this good". Half your normal steps reads the same.

Before you rent a GPU, do that multiplication, the same way §6 has you count grid cells. If previews come out as a real slice of the training time, treat that as a bug in the config, not a setting.

**Loss is close to useless here**, and the community and the vendors now agree: "watch the samples, not the loss" `[official — BFL, docs.bfl.ml]`. One exception is worth knowing about: **OneTrainer supports real validation loss.** You mark separate concepts as validation data — explicitly *not* your training images — and it graphs per-concept validation loss to TensorBoard. That is a genuine held-out signal that no other trainer gives you, and it costs nothing. If validation loss turns upward while the sample images still look fine, you are watching overfitting start.

Two 2026 tooling notes. OneTrainer is reported to run 1.4–2× faster than AI-Toolkit on the same hardware, from `torch.compile` and int8 (w8a8) training switched on by default `[community — sanj.dev trainer comparison, 2026-08]`. AI-Toolkit's mid-2026 PR stream added qfloat8 offloading, a dynamic memory manager, offline mode and block-by-block quantisation for Krea 2 `[official — ostris/ai-toolkit PRs, 2026]`. That lowers the VRAM floor on the newer bases this suite trains on.

**Disable in-training samples where the sample pass is what blows the memory.** On H3 under ai-toolkit the first sampling rung pulls the fully offloaded text encoder back on top of resident training state, and can OOM a container with no traceback. The checkpoint and optimizer state are written *before* sampling, so a relaunch resumes exactly where it died `[live-use — media lab, h3-v16/v17, 2026-09-04]`.

---

## 2. Layer 2 — the grid, and the tools that build it

The standard move is a grid of **checkpoint × LoRA strength**, rendered on fixed prompts and a fixed seed. It is standard because it works. The table below says which tool to use. The suite has been prescribing this method without ever naming a tool for it.

| Tool | Use it when |
|---|---|
| **SwarmUI Grid Generator** | **The default recommendation.** It ships with SwarmUI as a reference extension, so there is nothing to install. Grids can have any number of axes, and the "Web Page" output is a live viewer that shows up to 4 axes at once and lets you swap between them freely. That last part is the reason to prefer it: a static grid image locks you into 3 axes and one arrangement |
| **A1111 / Forge X/Y/Z plot** | It is already in your UI and you want two axes and nothing else. This is the original; Grid Generator began as Infinity Grid Generator for A1111 |
| **Efficiency Nodes — `XY Input: LoRA Plot`** | You live in ComfyUI and want the grid inside the workflow that will actually run in production |
| **ComfyUI-LoRAWeightAxisXY** | You want strength sweeps specifically, as an axis for Efficiency Nodes |
| **Published workflows** — "LoRA Testing: Epochs vs Seeds", Civitai's "Easy LoRA Checker" | You want a working grid in five minutes rather than wiring one yourself |
| **rgthree `Image Comparer`**, built-in `ImageCompare` | You want a final head-to-head between two survivors. The wipe-slider is excellent for two images and useless for twelve |

**One note on SwarmUI's LoRA handling:** the Grid Generator has no LoRA-model axis. You vary LoRAs through **prompt replace** instead. Put `<lora:mylora>` in the prompt and give the replacements as `mylora, myotherlora, mythirdlora`. This works fine for checkpoint sweeps once you know to do it that way. People lose an evening hunting for an axis that is not there.

**Keep the grid small.** Cells multiply fast. A grid of 6 checkpoints × 4 strengths × 4 prompts × 1 seed is 96 images, which is already a long wait on a home GPU. Use layer 1 to narrow the checkpoint range first, then spend the grid on the range that could actually win.

### Staging the grid — the A–F ladder

One grid answers one question. The media lab's protocol runs six small ones in order `[live-use — media lab, EVAL-PROTOCOL, 2026-09-03]`. **Each stage fixes its variable for every stage after it, so no later stage runs on more than the survivors**:

| Stage | Question | Cells | Notes |
|---|---|---|---|
| **A — step and strength** | Which rung, at which strength | ~36–54: 3 probes × 3 rungs × 3 strengths × 2 seeds | Ties break to the lower rung (§3) |
| **B — stability** | Does the winner hold across seeds | ~15: 5 seeds on the winner | Diversity collapse shows here |
| **C — flexibility** | Does it survive out-of-distribution prompts | ~8–12: OOD plus the run's own starved axes | The starved axes come from the dataset audit |
| **D — the adult stack** | Does it survive the NSFW checkpoint underneath | ~9–12 over the adult checkpoint, **plus one cell at strength 0** | Skip if not a goal; the strength-0 cell is not optional |
| **E — render surface** | Every deployment checkpoint × resolution | Small | A Turbo-only eval shipped a broken LoRA (§3) |
| **F — head-to-head** | Blind pairs against the incumbent at *its* shipped settings | 20–30 pairs | The only stage that says "ship" |

Ninety to a hundred and twenty cells, a few dollars rented. The ship rule: **wins likeness on the close and three-quarter probes, and does not lose full body or the adult stack.** A LoRA that wins the face and loses the body has not earned the default slot; it is a specialist, and gets labelled as one.

---

## 3. Layer 3 — judging without fooling yourself

No tool does this part for you. It is also where a home setup can genuinely match a professional one, because it costs nothing.

**The problem with grids is that they are labelled.** Labels are what grids are for; the axes are the point. But it means that when you look at a cell, you already know it is epoch 8 rather than epoch 4, and expectation does the rest. Every grid tool above works this way. That is not a flaw in the tools. It is a reason not to let the grid make your final decision.

**The cheap fix is a blind pass:**

1. Pick one strength and one prompt at a time.
2. Show the candidate checkpoints **shuffled and unlabelled**, side by side.
3. Choose the best. Or choose **"none of these are acceptable"**, which is a distinct and important answer.
4. Only then look at which was which.

You can do this by renaming files to `A.png`, `B.png`, `C.png` from a shuffled order, either with a ten-line script or by hand. It sounds fussy. It also routinely flips the answer people got from the labelled grid.

**Make it blind from the start, not by willpower.** Knowing about this bias does not protect you from it. If the labelled grid gets drawn first, you are then supposed to ignore what it tells you, and that does not work. The labelled sheet is sitting right there, it is the obvious thing to open, and a run that took hours wants an answer now. So do not create that file at all. Have whatever draws your grid write out **coded cells plus a separate key**, and leave the key shut until you have written down a pick:

1. Render every cell under a shuffled code — `A`, `B`, `C`…
2. Save the code-to-checkpoint mapping in a `BLIND_KEY.json` next to them. Do not open it.
3. Write down your pick — best likeness and best prompt-adherence, separately, for each prompt.
4. Now open the key.

The images and the cost are the same. The one thing that changes is that no file ever exists showing you a picture and its checkpoint number side by side. That is worth more than promising yourself you will ignore such a file. It also holds up when someone else runs the eval for you, whether agent or human, because "was the key still shut when the pick was written?" is something you can check, and "were you biased?" is not. This is the concrete version of the build-it-yourself advice in §7. The shuffling is not a bonus on top of a grid tool; it is the part grid tools do not do.

**Still draw the labelled grid — just do it afterwards.** Once the pick is recorded, the labelled view is the best way to see the shape of the run: where the likeness arrived, how wide the usable strength band is, and whether late checkpoints go stiff. The labelled grid is a bad judge and a good explanation.

**If the subject is a real person, the person who knows that face makes the pick.** You cannot judge how much a picture looks like someone you have never met, and neither can a metric. You can check the broad structure against a reference photo, but the part that reads as *them* is exactly what a stranger's eye misses. So split the job: **whoever ran the training builds the blind set and says what each prompt was testing; whoever knows the subject chooses.** Prompt-adherence is the opposite case. Anyone can score a picture against the prompt text, so that half of the judging does not have to wait.

**Do not promote a checkpoint until the pick is settled.** Whatever gets copied into the LoRA folder is the one that gets used forever, so a "temporary" promotion quietly becomes permanent. Sometimes you have to hand someone a file early, either to let them try it or because the rented machine is about to disappear. In that case, label it **provisional** in the sidecar, name the pick you are waiting on, and keep the other candidates. Deleting the alternatives is how "we will confirm this properly later" turns into a decision nobody made.

**Score likeness and prompt-adherence separately.** They reliably peak at different checkpoints, because likeness keeps improving after flexibility has started to die. Asking "which is best?" makes you average two things that are moving in opposite directions, and the answer then depends on whichever one you happened to be looking at. So ask twice:

- *Which of these is closest to the person?*
- *Which of these best did what the prompt asked?*

The two answers usually differ. When they do, the gap between them is your usable range. Which end you pick depends on whether this LoRA is for portraits or for putting the character into scenes.

**A prompt that fails on every checkpoint tells you about your dataset, not your checkpoints.** Build that distinction into the habit. If "profile view" is bad at epoch 4, at epoch 12, and at every strength, then no choice of checkpoint will fix it. Your dataset lacks profile coverage, and the answer is another training run with a better set. Write those prompts down separately from your checkpoint verdict. They are the spec for your next dataset.

### Which rung — the tie-break, and which probe regressed

**Which probe regressed is the finding.** A single likeness number averages over probes that move independently. Across four real-photo arms on one recipe and one judge, the three-quarter view was lost by every dataset change (0 of 6, 0 of 4), while the front close-up and the full body moved on their own. The same probe is where an over-trained rung collapsed first: c2500 went 0 wins, 4 losses on the three-quarter alone `[live-use — media lab, krea2-v9…v13, 2026-09-03]`. Score per probe, and report per probe.

**When the grid cannot separate two rungs, take the lower one.** Fewer steps bakes in less of the set, keeps flexibility, and avoids what happens past the peak: the *source medium* trains in, not just the identity. An all-phone-JPEG set learned compression grain as skin past c1750: "higher steps seem to bake in a bit weird skin texture". Its rung ladder ran c1750 > c2250 > final, the first unambiguous one in the project. A set with more views of the same photos tolerated a rung more `[live-use — media lab, krea2-v11 vs v12/v13, 2026-09-03]`. So **the peak is a function of source quality, not dataset size**: measured peaks across nine runs ran from c1750 of 2500 to `final` of 3500. If it matters, carry both rungs into the head-to-head.

**Strength is a diagnostic too.** A likeness that keeps rising up to 1.1 is the weak-likeness signature — the LoRA needs above-normal strength to assert the identity, which means it has no stacking headroom `[live-use — media lab, krea2-v1/v6, 2026-08]`. Later, better-fit runs shipped at 1.0. The same reading from the community side: a style LoRA that peaked at 0.73 with a usable 0.4–0.75 band, where "0.8 to 1.0 starts pulling the image apart" `[community — Herbst, FLUX.2 runs, 2026-02]`. A LoRA that needs 1.0 or more is telling you something about the run.

### Pairs, margins and fatigue

**Blind, paired, one decision per screen — not a 1–5 scale.** Perception is relative, and a pairwise judgement does not ask the judge for a global consistency they do not have; the same finding drives the pairwise-beats-pointwise result in §8. The lab's deck format `[live-use — media lab, EVAL-PROTOCOL, 2026-09-03]`:

- **Pairs** — same probe, same seed, tap to flick A↔B, then *A more her / Same / B more her* — for any stage that compares arms.
- **Grids** — arms as columns, one decision per arm pair rather than per cell — for step, strength and render-surface stages. With grids on the arm stages a full run is about 45 decisions.
- **Gates** — *Her / Close / Not her*, plus leak and fault chips — for single cells.
- A real reference photo pinned on every card, and a fullscreen viewer that flicks A/B **while keeping zoom and pan**, so the same patch of face is compared.

**Record the margin, not just the win.** Two chips — *close call*, *neither strong* — save with each pick, and the scorer splits wins into clear and close. The worked example: one arm beat another 9–1, but both full-body pairs were "very close" and four others "neither strong", so 9–1 overstated the lead. Free-text notes matter too; the judge's most useful signal did not fit the chips.

**Judge fatigue bounds how many decks you can run, and the right response is to stop.** After roughly a hundred blind pairs across four arms in two days, the judge reported getting "a little blind" to the face. Then: "I think I'm actually muddying things when they are this close." One arm's stage F was published as 30 pairs and never scored; the ship call was made unblinded `[live-use — media lab, krea2-v11/v13, 2026-09-03]`. Design for it. Let a metric (§5) rank the cells so the human judges the top and bottom of a ranking rather than the middle. Use grids over per-cell pairs on the arm stages. One question per screen. Put the next deck at least a day out.

### Diagnosing a quality regression

The layers above judge a run. Nothing above debugs one, and the lab lost a day to that gap `[live-use — media lab, EVAL-DISCIPLINE, 2026-09-07]`:

1. **Reproduce the known-good render before forming a hypothesis.** The decisive fact — that a skin artefact originated in the *base model* — came from a no-LoRA render that "should have been the second image made, not the twentieth."
2. **A strength-0 control in every comparison.** A failure the base shares is not the LoRA's failure, and on a guidance-distilled checkpoint cfg above 1.0 grains the image with no LoRA loaded at all.
3. **Check the background.** An artefact on the wall as well as the skin is a sampling artefact — steps, cfg — not something a character LoRA learned (`dataset-and-captioning.md` §3).
4. **Evaluate on every checkpoint × resolution you will deploy on.** One LoRA was trained on Raw, evaluated only on Turbo, and shipped `final`. On the adult checkpoint it was unusable at 1024×1536 and good at ≥1344×2016. Strength was not the lever, and c2500 was the only rung that survived the hard case `[live-use — media lab, Ciara krea2-v3, 2026-09-08]`.
5. **Sidecar every render, including throwaways**, and read `cells.json` rather than the plan file. A recipe JSON carried a variant at cfg 1.5 with a negative that was never used for the dataset. Taking it as "the recipe" produced grain that was blamed on the LoRA.
6. **Enumerate exactly what an error touched before retracting anything.** The cfg-1.5 mistake was announced as contaminating "much of the day's work"; one grep showed two tests.
7. **A blank or flat cell is a checkpoint fault, not a renderer fault.** Per-frame standard deviation ~2 against ~50 for every other cell, one cell in 36, same seed fine at other rungs `[live-use — media lab, h3-v14, 2026-08-30]`. Measure before blaming the renderer.

---

## 4. The held-out probe set

**Write your test prompts before you look at any results, and reuse the same set across runs.** Prompts you invent while browsing outputs drift toward whatever the LoRA already does well. A fixed set is also the only way run 3 stays comparable to run 1. You cannot recover that comparability later.

**Check every probe against the caption corpus before you trust it.** Grep the probe's phrases against your training captions. A probe that overlaps a training caption measures recall, not capability: the model has seen those words attached to those pixels, so a pass proves memory. One near-verbatim overlap is enough to invalidate every verdict a sweep produced `[community — production run, 2026-08]`. The same rule covers images. Never evaluate on, or judge likeness against, an image that is in the training set.

Two rules for building and running the set:

- **Do not reuse caption-corpus phrasing**, in the starter set below or in anything you add to it. And every capability group you test needs at least one probe that is out of distribution for that group. In-distribution probes alone cannot separate learning from memorisation.
- **Every generation prompt carries the trigger token, and frozen probes are reused verbatim.** A probe that drops the trigger tests the base model, not the LoRA, and its outputs read as misleadingly weak. Rewording a frozen probe breaks comparability the same way inventing a new one does. The one deliberate exception is the **no-trigger control** below, which exists to be compared *against* the base.

**Five design rules for a judgeable probe.** They come from a probe-set rebuild after the near-verbatim probe above inverted a headline finding `[live-use — media lab, C1–C8 rebuild, 2026-08-31]`:

1. **The face must be above ~15% of frame height**, or you are testing framing, not identity.
2. **The body must be upright and side-on** — lying or foreshortened poses cannot be read for anatomy.
3. **Never paraphrase a training caption.**
4. **Stay photographic.** Out-of-distribution should mean an unfamiliar setting or light, not an unfamiliar medium: an oil-painting probe abstracts the face until no identity call is possible. (`flex-style` below stays in the set as an *overfit* detector — does the LoRA drag output back to photographic? — not as an identity probe. Score it for adherence only.)
5. **Nude probes need the adult base underneath**, or they measure censorship.

And a sixth from the same rebuild: **standing-figure probes render on a portrait canvas** (768×1344, not 1024²). The first square test complied with the prompt and cropped the head off at the neck.

Keep the set in the run folder as a plain file. Here is a workable starter set, grouped by what each group is actually testing:

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
  text: "<trigger>, oil painting, thick visible brushstrokes, museum lighting"   # adherence only — see rule 4
- id: flex-costume
  text: "<trigger>, wearing full medieval plate armour, castle courtyard"
- id: flex-scene
  text: "<trigger>, sitting in a crowded diner, seen from across the room, wide shot"

# controls — rendered every time, never scored for likeness
- id: ctrl-no-trigger
  text: "portrait, neutral expression, plain grey background, soft even lighting"   # base-portrait minus the trigger: must stay close to base, or you overtrained
- id: ctrl-strength-0
  text: "<trigger>, portrait, neutral expression, plain grey background, soft even lighting"   # LoRA loaded at 0.0: the base's own answer to every probe
```

The two controls are cheap and they close two arguments before they start. `ctrl-no-trigger` is the community's overtrain test: the same text minus the trigger "must stay close to base; if polluted, you overtrained" `[community — chengyansen-ai, krea2-lora-training v0.4.0]`. `ctrl-strength-0` is the base-model control from `../SKILL.md`'s pre-flight, made a standing probe so it is never skipped.

That set does two things on purpose. **`flex-scene` puts the face small in the frame**, which shows you whether the identity survives at low pixel counts. That is the most common failure nobody tests for until production. And **`flex-style` fights the LoRA deliberately**: an over-trained character LoRA drags every output back toward photographic, and this prompt makes that visible in a single image.

Add a group for whatever you actually use the LoRA for. If it exists to make adult content, probe it there too. A LoRA that holds the identity in a portrait but loses it in the work you built it for has not been tested, and `nsfw-training.md` covers why those failures cluster differently.

---

## 5. Putting a number on it

**`cubiq/ComfyUI_FaceAnalysis` provides the `FaceEmbedDistance` node.** It offers InsightFace/ArcFace or DLib backends, and cosine or Euclidean distance between a batch of reference faces and a candidate. This is the accessible way to get a number out of a home setup, and it is a real number. Know that the repo has been **maintenance-only since 2025-04-14** `[official — repo README]`. The one successor located is `Kidev/ComfyUI-FaceFilter` (InsightFace `antelopev2`, cosine against a reference *set*, default threshold 0.30), built as a filter rather than a benchmark `[official — repo README, read 2026-09-09]`. A few lines of Python over any face-embedding model does the same job outside ComfyUI, which is how the lab runs it.

**Calibrate a baseline first, or the number means nothing.** The node's own recipe is 3 real photos as the reference batch and a *4th real photo* scored against them. The better version is **leave-one-out over every real photo you have**: score each against the centroid of the others and record p50, p90 and max. That spread is your floor: the distance genuine photographs of the same person sit from each other in different conditions. Everything you generate is read against it, never against zero. Two calibrations for scale `[live-use — media lab, Amy triage v17, Ciara rotation-01, 2026-09]`. Fifteen real photos of one person gave p50 0.183 / p90 0.347 / max 0.418, with good finals landing at 0.13–0.19 and a LoRA-off render at 0.80. Nine face-visible synthetic rotation cells of another gave p50 0.112 / p90 0.191 / max 0.270, with "inside p90 is her" as the working rule. Skipping this step is the most common way this node gets misused.

**Two measured blind spots.** Profiles score high regardless — half a face — so judge them by eye. And the metric is **not sensitive enough at half- and full-body face scale to be trusted for a ship call**. On one run it said the new arm was at least as good as the old on five of six probes. The person who knows the face failed the run `[live-use — media lab, krea2-v15, 2026-09-06]`. Synthetic cells inside the real spread (0.145–0.31) were rejected on sight as "not at all like her". **The metric can triage; it must never admit an image**, into a dataset or into the LoRA folder.

**Then treat the score as a screen, not a verdict.** This is a hard finding rather than a caution:

> The standard personalization metrics — **DINO and CLIP-I for subject fidelity, CLIP-T for prompt following** — show significant discrepancies from human judgement, because they are image-*similarity* models being asked a question that is not similarity. This is the central result of **DreamBench++** (ICLR 2025). `[official — published benchmark]`

The 2026 successors sharpen it. **MaSC** (2026-05) diagnoses the bug as global pooling: a whole-image cosine averages in background variation that humans ignore when judging identity. It measures agreement with humans on DreamBench++ at CLIP-I **+0.135** and DINO-I +0.311, against a human ceiling of +0.658 `[official — arXiv 2605.22469]`. That CLIP-I figure is the citable evidence that it is near-useless for identity. **DSH-Bench** (2026-04) confirms the weak CLIP/DINO–human correlation over 459 subjects, but annotates with absolute scoring where MaSC does not. So the two leading benchmarks disagree on protocol, and neither validates pairwise here `[official — arXiv 2603.08090]`.

ArcFace distance is in the same family and inherits the problem. Watch for one specific failure: **similarity scores inflate when a LoRA overfits face position and pose**, because the metric rewards spatial resemblance that it ought to be ignoring. A score that climbs through the late checkpoints may therefore just be measuring memorisation. Reading it as improving fidelity hands you exactly the wrong checkpoint.

**Two free signals partly cover the gap**, and both are computable from images you have already generated:

- **Diversity collapse.** Generate the same prompt at several seeds and measure how different the outputs are from each other. When that spread falls off a cliff at some checkpoint, that checkpoint has stopped generating and started reciting. It is a good overfit detector precisely because it does not rely on a similarity model agreeing with human judgement. The community names four signatures of the same thing: **prompt inertia, skin plasticity, pose echoing** (repeated shoulder and neck angles across seeds) and **colour lock**. Its roll-back rule is two consecutive failures `[community — WaveSpeedAI, 2026-01-23; single report]`.
- **Sharpness** (Laplacian variance, a few lines with OpenCV). This catches early blur *and* late waxy over-smoothing. One metric covers two failure modes at opposite ends of the run.

Use the numbers to **rank candidates and flag suspects**. Use the blind pass in §3 to decide. The machine is advisory; the human is decisive.

---

## 6. What a run costs

Nothing here is priced in currency, because GPU rates move and the numbers would rot. Price it in **cells** instead, which do not.

| Stage | Cost | Notes |
|---|---|---|
| Training samples | **Not free on a rented GPU** | They share the GPU the training is already paying for. Count them as `prompts × seconds per preview × (steps ÷ sample_every)` — on an undistilled model that can come to more than the training itself (§1) |
| OneTrainer validation loss | **Free** | Some extra steps per validation interval |
| The grid | **The real cost.** cells = checkpoints × strengths × prompts × seeds | 96 cells is a comfortable ceiling at home; 400 is an afternoon |
| Blind judging | **Free** | Reuses grid images. Costs attention, not compute |
| FaceEmbedDistance scoring | **Effectively free** | CPU-viable, reuses grid images |

**If you rent, the money goes on the grid, and only the grid.** That makes the narrowing move in §2 your single highest-value habit. Using the training previews to cut the checkpoint range from 12 to 4 before you render cuts the bill by two-thirds, and it loses you nothing, because you were never going to ship the checkpoints the previews showed as blurry.

**If you rent, work out the cost before you render.** Multiply the four numbers, multiply by your seconds per image, and look at the result before you start. A grid that quietly grew to 600 cells is the classic way a cheap validation run stops being cheap. If you are renting on RunPod, [`comfyui-on-runpod`](../../comfyui-on-runpod/) covers keeping the models on a network volume, so that a grid run does not re-download weights every time. Re-downloading otherwise costs more than the rendering.

---

## 7. What to build yourself

**Do not build a trainer, and do not build a grid renderer.** Both are solved problems, and the tools in §2 are better than anything you would write.

**The thing worth building is small**, and no tool provides it: a script that drives the render itself, so the pictures arrive already blind. It should

1. write every cell under a shuffled code (`A/B/C…`), with the mapping in a `BLIND_KEY.json` you leave shut,
2. record your picks — best likeness and best adherence, separately, per prompt,
3. write the result next to the run with the checkpoint names filled back in.

The order matters. A script that renames files *after* a labelled grid has been drawn leaves the labelled grid sitting on disk, and §3 is about that file never existing.

That script is an afternoon of work. It is the highest-value hour in this entire document, and it persists across runs, so that run 5 can be compared with run 2.

**Add these only if the first script is earning its keep:** FaceEmbedDistance scoring over the same folder, and a per-prompt summary that flags prompts weak across *all* checkpoints. That summary is your next dataset's to-do list.

**There is one thing you will be tempted to build, and should not:** a general evaluation platform. Nothing off-the-shelf exists for this job because the probes and the pass criteria are project-specific by nature. Which prompts matter, and what "the face holds" means, are yours, and they change with every character. Generalising that is a product, not a tool, and building it costs you the time you meant to spend training.

---

## 8. What the professional tier does

You are not the target audience for this tier, but it is worth knowing which parts of it are worth borrowing.

| What they do | Worth borrowing at home? |
|---|---|
| **Experiment tracking** — W&B as the industry standard: every run logged with full hyperparameter config, dataset version, loss curves, eval results. W&B **Weave** now has an image-eval framework (dataset + scorers + comparison dashboard, model-agnostic and documented for diffusion) | **Partly.** The full platform is overkill; the *habit* is not. A folder per run with the config, the probe set and the verdict in it gets you most of the value for nothing |
| **Benchmark suites** — **DreamBench++** for personalization (7 methods × 150 subjects × 9 prompts), its 2026 successors **MaSC** and **DSH-Bench**; **VBench/VBench++** for video across 16 dimensions | **No, and this is the key point.** These compare *methods* across *the benchmark's* subjects. You need to compare *checkpoints* on *your* subject. That is a different unit of analysis, so running DreamBench++ tells you nothing about your character |
| **Reward models** — ImageReward, PickScore, HPSv2/HPSv3++ | **Rarely.** They predict aggregate human preference for general aesthetics, not whether this is the right person |
| **VLM-as-judge** — the field has converged on VQA/VLM-mediated scoring, and it is where the metric layer went after DINO/CLIP-I | **The finding is worth borrowing, even if the tooling is not.** Raw pointwise VLM judging is unreliable — Qwen3-VL-8B scores **26.5% pointwise vs 59.4% as a direct pairwise judge**. Pairwise beats pointwise, and that is the same reason the blind head-to-head in §3 beats scoring cells one at a time. You can apply that conclusion with no infrastructure at all |

**VBench's subject-consistency dimension** is the one genuinely borrowable idea for video work: identity stability measured across frames via DINO feature similarity. It puts a number on temporal identity drift, which at home is usually a shrug. The same alignment caveat as §5 applies.

---

## How to read the claims in this file

**Hard facts.** The DreamBench++ result on DINO/CLIP-I misalignment, the pointwise-vs-pairwise VLM judging figures, VBench's dimension set, and what each named tool does and does not support (including SwarmUI's lack of a LoRA axis and its 3-axis grid-image / 4-axis web-page limits). **Sources are published benchmarks, papers and project READMEs.** These are checkable, and they were checked.

**Craft.** This covers the blind pass and the trick of making it blind from the start, scoring likeness and adherence separately, who gets to make the pick when the subject is a real person, holding a checkpoint as provisional, the fixed probe set and its design rules, weak-everywhere prompts as a dataset signal, the narrow-then-render budget habit, and §1's readings on preview cost and two-half models. **Two sources carry it.** The community bar is people running these evaluations repeatedly, and it is stated with confidence. The `[live-use — media lab, …]` bar is one lab's protocol over some forty runs on two characters, each claim dated to its run. It covers the A–F ladder, the deck format, the margin record, judge fatigue, the lower-rung tie-break, the which-probe-regressed reading, the regression checklist and the calibration numbers. Trust the mechanisms; treat the numbers as measured single points. The blind discipline is defensible, not documented consensus: no image-community source advocating shuffled comparison for epoch picking was found, and the pairwise-over-pointwise argument is borrowed from the LLM-evaluation literature.

Two things are genuinely open. **There is no accepted home-scale metric for character-LoRA fidelity.** Face-embedding distance is what is reachable, it triages well, and it is measured to be too loose for a ship call at body scale. VLM judging is where the field went, but it has no turnkey local tooling at this scale. `[contested]` And **no reusable checkpoint-selection harness exists**: the published benchmarks evaluate methods on their subjects, not your checkpoints on yours.

**Facts dated 2026-09-09; community craft refreshed 2026-09-09; live-use craft extended 2026-09-09.** The tooling layer moves fastest here — grid extensions, the face-analysis node's successors, and whatever local VLM-judging tooling appears next — so re-verify a named tool's current state before building a habit around it.
