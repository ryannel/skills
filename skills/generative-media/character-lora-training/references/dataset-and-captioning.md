# Datasets and captioning

The dataset decides the ceiling. Hyperparameters only decide how close you get to it.

This file owns the model-agnostic dataset craft: how big, what it contains, what resolution to render or source at, and how to caption it. Generating a set — the factory loop, seeding from an older LoRA, the video turnaround — is in [`synthetic-datasets.md`](synthetic-datasets.md). Per-model numbers — the training bucket, the trainer config, the deploy band — live in each model skill's `references/lora-training.md`. Claims marked `[live-use — media lab, …]` come from first-hand runs on rented hardware, each naming its run and date. They are measured points from two characters, not consensus. They sit beside the community view wherever the two differ.

## Contents

1. [Size and curation](#1-size-and-curation)
2. [The coverage protocol](#2-the-coverage-protocol)
3. [Resolution — render or source inside the band](#3-resolution--render-or-source-inside-the-band)
4. [Captioning](#4-captioning)
5. [Multi-outfit and multi-character](#5-multi-outfit-and-multi-character)

The synthetic dataset factory, the seeding rules and the video turnaround moved to [`synthetic-datasets.md`](synthetic-datasets.md).

---

## 1. Size and curation

**15–30 well-curated images beat 100 mediocre ones.** This is one of the more consistent findings across trainers and families. NanashiAnon puts the Illustrious-era single-outfit figure at 20–30, L3n4's crash course says "a well-curated 30–50 beats a poorly curated 500", and BFL's own FLUX.2 guidance lands at 15–40 `[community — NanashiAnon, L3n4/Civitai 25645; official — BFL 2026-06-04; convergent]`. The reason it holds is that a big dataset does not fail by having too much data. It fails by having variance that nobody controlled. Every inconsistency you did not caption is something the model tries to learn.

**Count is not the lever. The media lab tested that three separate ways, and count lost every time** `[live-use — media lab, 2026-08-26 → 2026-08-30]`:

| Arm | What changed | Result |
|---|---|---|
| krea2-v1 vs krea2-v4 | 25 real photos vs 74 — a strict superset of the same 25 | v1 the dominant winner on a 5-model × 5-seed blind face probe |
| h3-v14 | dataset 32 → 73 images, byte-identical config | Likeness landed in the same place: "faces kinda ok, bodies all over the place" both times |
| krea2-v8 vs krea2-v6 | 15 coverage-built images vs 32 | "Very close" — at under half the count |
| krea2-v2 vs krea2-v1 | Same 25 images; rank 32 → 64, steps 2250 → 3000 | Lost blind to the rank-32 control; every 0.6/0.8 cell "not even the same person" |

The last row matters as much as the first three. Capacity and training length were exhausted as levers *before* the dataset was, on the identical set. When a run disappoints, the question is *which* images, never *how many*. The lab's working band for a real-photo set is **15–32**, with 30–35 named as diminishing returns.

One community report goes lower still, on Krea 2: a usable character LoRA from **10–15 tightly curated images at 600–1,200 steps**, on the condition that every off-looking image is culled and the captions name only what should vary `[community — r/StableDiffusion 1wacvcm, 2026-09; single report]`. Set that beside the lab's 2,500 steps on 13–16 images and the two disagree on the step budget by a factor of two or more. Nobody has run both on the same set. Read it as the low end of a contested range — steps per image is listed as open in the SKILL.md two-bar section — not as a replacement for picking the rung from a checkpoint series.

**The floors and the knee.** Per-family floors from the dataset-tooling side run Z-Image 12, Krea 2 and FLUX 15, SDXL 20 — SDXL the only family that needs more `[community — perfectgf/lora-dataset-studio]`. Official floors sit far below practice (Krea's hosted trainer accepts three images) and carry no signal. Where the knee is — 30, 50, 100, several hundred — is disputed across an order of magnitude. No source anywhere ran a controlled test holding everything else equal `[contested]`. The most useful framing found is ~50 *only when the character has many distinct visual states* `[community — apatero, 2026-01-06; single report]`. The one published same-recipe comparison (800 pairs vs 127) reports training loss, which does not track likeness on these models, so nothing follows from it.

Curate against these, hard `[community — MyAIForce, Civitai guides 5301/6990; convergent]`:

| Reject | Why |
|---|---|
| Blurry, low-resolution, heavily compressed | Teaches the artefacts — and past the peak checkpoint the compression trains in as skin (§3) |
| Heavy stylisation, beauty filters, retouching | Bakes the filter into the identity; over-smoothed sources teach a smoothed skin distribution |
| Occluded face (hands, hair, sunglasses, masks) | Weakens the thing you are training |
| Near-duplicates, and crops of images already in the set | Effectively upweights one pose — and a crop teaches its framing (below) |
| Inconsistent apparent age or build; a span of many years | Produces an averaged, unstable identity — "if your training data spans 20 years, the LoRA will average features" `[community — apatero]` |
| Flat, front-lit, shallow-depth portraits with no shadow shaping the face | No dimension to learn from. Removing two such frames recovered the front close-up `[live-use — media lab, krea2-v11, 2026-09-03]` |
| Wildly divergent lighting across a real-person set | Confuses skin tone into a variable the model cannot attribute |
| Group shots that cannot be cropped to one subject | The other faces become variance nobody captioned |
| Watermarks, text overlays, readable signage | Reliably learned and reliably reproduced |

The governing heuristic: **when in doubt, leave it out rather than hope the trainer ignores it.** The lab's judge rejected on sight, fast, and the categories were consistent: no dimension, an angle already covered, visibly upscaled or compression-haloed. "These are all bad pictures, I don't think adding them helps" held even when a frame was the only evidence for a body attribute `[live-use — media lab, Amy curation, 2026-08-31]`.

**Near-duplicates are the most common self-inflicted wound.** Twenty frames pulled from one video clip look like twenty images, but they behave like one image. The model sees a single pose twenty times and collapses onto it.

**A crop of a photo already in the set is a duplicate, not a coverage row — and it teaches the crop.** Two chest-up crops of selfies the set already held double-weighted those photos: the subject read tanner and older, because those two 2025 frames now counted four times. And the crops taught a chest-centred frame, so the resulting LoRA cut heads off on head-and-shoulders prompts `[live-use — media lab, krea2-v12, dataset v16, 2026-09-03]`. Composition is learned with identity. That is the practical reason a set needs the framing spread it will later be asked for. The carve-out is editing that removes noise — cropping empty borders, splitting a group photo to one subject.

**Checksum matching only catches byte-identical copies, so do not dedupe with it.** Repair and upscale pipelines rename files and re-encode them, and md5 sees each result as a new image. In one 199-file pool, exact-md5 and filename-chain dedup found 23 groups and missed 21 duplicates, because the intake pipeline had renamed originals `[live-use — media lab, Amy pool consolidation, 2026-08-31]`. Dedupe by eye instead: contact sheets to find suspects, then full-size side-by-side face crops to confirm. Perceptual hashes or face embeddings do the same job at scale, but the cases that matter were caught by looking.

**When an original and its repaired or upscaled copy both survive, judge the pair, not the pipeline.** Face restoration often wins the file-quality battle and loses the likeness one. Waxy skin and smoothed detail read as polish at thumbnail size and as a different person at full size. Across 21 such pairs, 11 kept the original, because the repair had smoothed away real freckle detail. The other 10 kept the repair, because the originals were blurry photos-of-a-screen with moiré, or under 800 px. A blanket "keep the highest resolution" would have been wrong eleven times `[live-use — media lab, 2026-08-31]`.

**Dataset versions are immutable once a run references them.** Edit a set in place after a run and you no longer know what that run trained on. The lab enforces this after one set was edited post-run. It had to be reconstructed and verified file-by-file by sha256 against the as-trained copy on the volume. By then one reconstructed caption had already leaked into the next version, so a later run trained on a caption that was never the real one `[live-use — media lab, dataset v13/v14, 2026-09-03]`. A change makes a new version, and the run folder records which one.

---

## 2. The coverage protocol

Coverage, not count, is what makes an identity generalise. The goal is simple: anything you will later ask the model to change should already vary in the dataset.

**Rotation — the 8-point protocol.** Around the head:

1. Front
2. Three-quarter left
3. Three-quarter right
4. Profile left
5. Profile right
6. Rear three-quarter left
7. Rear three-quarter right
8. Rear

Rear angles matter more than people expect. Without them the model has no idea what the back of the head looks like, so it improvises. It usually improvises badly, and usually at the worst moment.

**Elevation.** Include at least one shot above eye level and one below. A dataset shot entirely at eye level produces a character that distorts the moment you ask for a high or low angle.

**Shot size.** Include close-up, medium, and full body. A face-only dataset gives you a character with an unreliable body. A full-body-only dataset gives you a face that dissolves at distance.

One worked example puts numbers on the split and gives the reason. A Christopher Reeve LoRA used **29 close-up, 29 medium and 29 far or full-body shots**, plus a few crowd shots so the trigger isolates the subject from everyone else in frame. Without far shots the model has nothing to reconstruct the face *from* at distance, which is exactly where drift shows up `[community — r/StableDiffusion 1wacvcm, 2026-09; single report]`. That is the identity-per-face-scale mechanism the lab measured (below), seen from the dataset side. The crowd shots are the community's version of regularisation images; §4 explains why a single-subject set never forces the trigger to discriminate.

**Expression.** Include neutral plus at least two others. Otherwise expression locks, and the character can only ever wear the face it was trained on. That reads as uncanny well before anyone can say why.

**Lighting and setting.** Vary both. If you do not, they become part of the identity, and every generation inherits the dataset's lighting.

**Count the starved axes before you train, because they are countable.** An audit of one 73-image real-photo pool read: rotation front 41 / three-quarter 23 / profile 6 / rear 3; elevation above 5, **below 0**; expression neutral 8 / smile 52; lighting daylight 41 / studio 4; body references frontal only `[live-use — media lab, Amy COVERAGE audit, 2026-08-30]`. The probes sat in exactly that corner, so some of the measured weak likeness was distribution mismatch, not model capability. Confirmed downstream: the LoRA scored strict profile **0/5 across every seed**, because the set's only profile was one frame in a bobble hat. Whatever never varies becomes part of the identity — and the audit tells you what never varied before the run does.

### The identity ratio, and what it is really counting

**Split the set roughly one-third identity-emphasis, two-thirds in-context.** Identity-emphasis means close-ups and clean head-and-shoulders on plain backgrounds; in-context means full body, varied environments, poses and outfits. Anywhere from 0.25 to 0.40 works `[community — neonkisu, Civitai 31467; convergent]`. The value of the ratio is that it names both failure modes. A set that is 95% close-up gives great faces but loses body type, outfit consistency and pose flexibility. A set that is 95% in-context gives a face that drifts toward generic when the prompt zooms in. The literature is two-bucket; nobody proposes a three-way split.

**The lab reproduced both failures, and added a caveat: 0.33 is necessary, not sufficient.** Measured close-up share against outcome across three trained sets of one real person `[live-use — media lab, Amy v1/v6/v5, 2026-08-27]`:

| Set | Close-up share | Faces | Bodies |
|---|---|---|---|
| v1 | 56% | Best faces | Weak; refuses nudity |
| v6 | 43% | Between | Between |
| v5 | 32% | Fails on the tight crop | Best bodies |

v5 sits inside the 0.25–0.40 band and still has weak close-ups, because it has 9 of them where v1 has 14. **Absolute close-up count matters too.**

**Identity is learned per face-scale.** The same three sets showed it from the other side: v5's faces read strongly *inside a full-body shot* while ranking worst on the close-up probe, and v1 inverted. That reframes the "face likeness ceiling" people report. It is not a ceiling; earlier runs had varied image count, era span, rank and steps, and none of those touches face scale. A probe that puts the face small in the frame is testing a coverage row, not a checkpoint.

**Face pixels are what the ratio is really counting, so the training resolution moves the target.** The sharpest evidence is a negative result on MiniMax H3. Thirty-two images mixing full-body, upper-body and close-ups at 512×512 gave almost no likeness. A retrain on 31 face-focused images was a substantial improvement, because at 512² a full-body framing leaves the face tiny `[community — かみもと, note.com, 2026-08-07; single report]`. The same author later fixed it by schedule instead — 1,000 steps on full-body, then 500 more on a face-only set. Set that beside a successful 1024² Krea 2 run at only ~6% close-ups, where bust shots substituted and face consistency was "acceptable" `[community — natural-light, HF discussion, 2026-07-01]`. The lower the training resolution, the harder the set must skew to close-ups. That resolves the apparent conflict between the ratio camps rather than contradicting 0.33.

**A face that is tiny in the source does worse than nothing: it teaches a smeared average.** An SD1.5 post-mortem names the mechanism, and nothing about it is architecture-specific. Small, distant, profile and group-shot faces at low native resolution give the model a blurred average of the face, and that comes out as warped facial structure. BLIP-style auto-captions barely describe faces, so nothing in the text lets the model tell a good face from a bad one. The fix was a minimum face size at intake, dropping or cropping group and profile shots, deduping, and recaptioning with a stronger captioner. Two threads and the lab land on the same point underneath: a face small in the frame is a coverage row, and a starved one hurts `[community — r/StableDiffusion 1wakjxx, 1wacvcm, 2026-09; convergent]`. Keep the profile *rotation* — the 8-point protocol needs it — and drop only the profile that is also tiny.

### Constants bind to the trigger — and so do majorities and absences

The one-rule in `../SKILL.md` says a LoRA learns whatever is constant and uncaptioned. Two corollaries are easy to miss until they cost a run.

**A majority binds.** One synthetic set had dark brown hair on 29 of 32 cells and red on 2. "Red hair" then rendered *a different woman* on every checkpoint of two separate training arms, scoring far outside the spread of every other probe. A platinum pixie cut, a lab coat, leather, snow and glasses all held. Only the colour broke `[live-use — media lab, Ciara krea2-v4/v5 red-hair probe, 2026-09-09]`. The first proposed fix — append 12 red-haired cells, taking the set to 44 — was rejected as ballooning. The accepted fix kept the same 32 cells and redistributed colour so that **nothing has a majority**: dark brown 10, auburn 8, copper 4, dark blonde 4, chestnut 3, black 3. Every colour lands on at least one face-visible cell. The LoRA then sees one face under six captioned colours and cannot bind any of them. Redistribute; do not add.

**An absence binds exactly as a presence does.** Thirty-two bare-eared, bare-necked, bare-faced cells teach "no jewellery, no makeup" as part of her, even though the base model can draw all of those unaided. That is why the same set carries jewellery on 16 of 32 cells and makeup on 4. The LoRA does not have to learn earrings. It must not learn *their absence*. The rule the lab wrote down: **you cannot vary what you never named, and you cannot vary what never varied.** Caption the exception; leave the default unwritten (§4).

**The three-quarter view is the canary.** Across four real-photo arms on one recipe and one judge, every change to the dataset lost the three-quarter probe (0 of 6, 0 of 4). The front close-up and the full body moved independently of it. It is also where an over-trained rung collapses first `[live-use — media lab, krea2-v9…v13, 2026-09-03]`. Two things follow. Treat *which probe regressed* as the finding, not a single likeness score. And when the three-quarter is thin in the set, expect it to be the first thing any dataset change breaks.

**Mirror sets are a legitimate rotation tool.** A right profile took 26 renders and kept landing at ~75°, while the left profile was a true 90° in three of three. The cause was an updo: the model turns the head to show the knot. The fix was to render the cell as a *left* profile with long hair and flip it on assembly `[live-use — media lab, Ciara A5, 2026-09-09]`. A flipped profile is real coverage; an updo on a profile cell is not.

**The one-clause rule.** When you generate a dataset, keep the character description **byte-identical** and change only the clause you are covering: rotation, or shot size, or expression. Anything else that drifts between images is variance, and the model will try to attribute it to the character. `[community — Civitai dataset guides 7777/21257/21114; convergent]`

**The inference across base models is asymmetric.** A set that fails on one base fails for a reason worth finding. A set that works on Krea 2 is not thereby proven for H3 — the lab's user caught this being assumed and the assumption was withdrawn `[live-use — media lab, 2026-09-06]`. Only the negative direction is informative.

---

## 3. Resolution — render or source inside the band

This is the section the media lab paid a full day for, and it reverses a habit photography teaches. **Supersampling is not a diffusion habit.** For a dataset, render or source inside the base model's trained resolution band. Bigger is worse, and the damage survives downscaling.

### Why the extra pixels cannot help, mechanically

**Trainers downscale into buckets; they never upscale.** ai-toolkit: "Images are never upscaled but they are downscaled and placed in buckets for batching" `[official — ostris/ai-toolkit README, read 2026-09-09]`. musubi's `bucket_no_upscale` only affects images *smaller* than the bucket, so on an all-high-res set it has no effect at all `[community — AInVFX, 2026-04-06]`. A 4K source and a 1024 source therefore land in the same 1024 latent. What differs is what was in the pixels before the resample — and that is where the trouble is.

### The finding: over-band renders crumple, and the crumple survives the downscale

Krea 2 Turbo's band is 1K–2K and Raw is 1K-native. A synthetic dataset had nonetheless been rendered at 2048–2816, on the theory that hi-res sources downsampled into the 1024 bucket would give the LoRA real skin texture. A four-cell sweep settled it `[live-use — media lab, Ciara resolution sweep, 2026-09-08]`. LoRA strength 0, seed fixed, 12 steps, and cheek patches cropped as a fixed fraction of inter-eye distance so every resolution shows the same patch of skin:

| Render size | Skin at native size | Skin after downscale to 1024 |
|---|---|---|
| 1024×1280 (inside the band) | Clean — discrete freckles | — |
| 2048 | Moderately crumpled | Still speckled; loses to 1024 native |
| 2560 | Heavily crumpled | Still speckled; loses to 1024 native |

**The reticulated "scale skin" is in the pixels before the trainer sees them, and the resample does not remove it.** It was not the VAE: Wan 2.1 and Qwen decoders produced identical texture at 2048. And it was not rank. Two LoRAs retrained on a 1024-native set at rank 16 and rank 32 were equally clean at every checkpoint, on both deployment checkpoints, at 1024 and 1344 `[live-use — media lab, krea2-v4/v5 on dataset v4, 2026-09-09]`. The dataset was the fix. A fresh 2048 draw also moved the face further from its 1024 original (0.16) than an upscale pass did (0.08–0.11). So upscaling is better for identity stability and worse for texture. Under this rule the question is moot.

**Keep three resolutions apart.** The lab conflated them for a week:

| | What it is | Example (Krea 2, synthetic set) | Example (MiniMax H3, real photos) |
|---|---|---|---|
| **Source render / source capture** | The size at which dataset images are made or photographed | 1024×1280 native, inside the 1K band | ≥1536 short side, never upscaled in the trainer |
| **Training bucket** | The size the trainer resamples to | 1024 | 1536 — the likeness lever up to there, then a plateau |
| **Deploy render** | The size the *deployment* checkpoint wants | Turbo 1K–2K; the adult finetune unusable at 1024×1536, good at ≥1344×2016 | 0.9–1.0 MP stills |

The numbers are per model and live in [`krea-2/references/lora-training.md`](../../krea-2/references/lora-training.md) and [`minimax-h3/references/lora-training.md`](../../minimax-h3/references/lora-training.md). The distinction is what transfers: source, bucket and deploy are three different questions, and an answer to one is not an answer to the others.

### Sampling steps are a separate lever, and the wall is the tell

**Source-render step count trains in as texture.** At 2048 on a distilled checkpoint, 20 steps over-cooks skin into a harsh pore grid; 12 gives natural skin; 8 is a touch soft. Two datasets identical in every cell except the render step count proved it. The 20-step set trained a fine speckle in. The 12-step set did not, and won every in-distribution prompt `[live-use — media lab, Ciara krea2-v2 vs v3, 2026-09]`. It is a source-render setting, invisible on contact sheets.

**Check the background first.** The same grain appeared independently on the real-person side and was nearly written up as freckle stipple and a hard limit for that character. What broke the diagnosis was one observation: *"you can even see it on the wall actually, so it's not a skin stipple"* `[live-use — media lab, Amy hi-res renders, 2026-09-07]`. An artefact that appears on the background as well as the subject is a sampler or step problem, not a content problem and not something a character LoRA learned. The same holds for cfg: on a guidance-distilled checkpoint, cfg 1.5 grains skin *and* wall with no LoRA loaded, where cfg 1.0 at 8 or 12 steps is clean. **Sampler settings for images destined for a dataset are not the settings for images you only look at**, and steps and cfg are the two levers.

**Textured-wall wording prints its pattern onto skin.** At 1024 native, "white studio cyclorama" rendered as terrazzo speckle that reappeared on hip, thigh and torso. "Bare studio" became patterned wallpaper whose cells printed across the abdomen. A bedroom wallpaper came out as orange-peel on skin. All three failed on every seed — it is the wording, not seed luck — and every cell on a *plain painted wall* was clean `[live-use — media lab, Ciara dataset v4 inspection, 2026-09-09]`. Name a smooth, plain painted wall, or reuse a setting already proven clean.

### Real photos: the floor, and when to upscale

Real photos raise the opposite problem. **Sources below the training bucket teach softness.** One pool had 29 of 72 images with a short edge under the 1536 bucket, some at 336 px. A control run on the un-upscaled set came back "mottled and waxy, the worst texture of the six" `[live-use — media lab, Amy H3 dataset v7/v9, 2026-09-04]`. The fix was to re-develop 8 of 15 sources at 2× *outside* the trainer, from the camera files, and check each at 100% before acceptance. Real captures gained genuine eyelash separation with no ringing. Only then could `bucket_no_upscale` be set.

**The distinction is whether the upscale had real detail to work from, not whether the number clears the floor.** The same pool held 23 files sitting at exactly 1536×2048 with Lightroom as the only EXIF software and the camera make stripped. That signature is a messaging-app recompression re-exported to land exactly on the resolution floor: fake detail in the freckle band. Those were excluded. "Enlarged blur is still blur. Synthetic detail can become an unwanted texture prior" is the community's phrasing of the same point `[community — LocalForge, zsky, WaveSpeedAI; convergent]`. And an upscale plus img2img pass is not a substitute for a fresh render. Every variant over an upscaled latent left the same mottled speckle: Lanczos or 4xNomos input, either decoder, with or without grain words, denoise 0.25–0.50 `[live-use — media lab, Ciara, 2026-09-08]`.

**On Krea 2 none of this applies**: it trains at 1024 and native phone or camera output already clears the bucket. The lab's upscale exercise was an H3-only concern that the Krea arms inherited by habit.

### Other things that look like this, and are not

Two other causes produce reticulated skin, and the fixes differ:

- **Aliasing from re-learning skin the base already renders well.** One trainer blamed freckles, built a freckle-free set, and *still* got "stretch marks scattered all over the body", arriving exactly when likeness stabilised. They concluded it was moiré-like aliasing from overtraining skin micro-detail `[community — Civitai 16340; single report, login-gated]`. If that is your case, removing the trait will not help; it is a training-intensity problem, and the lower rung is the fix (see `evaluation-and-tooling.md` §3).
- **Over-smoothed sources.** Beauty retouching and face-restoration passes teach a smoothed distribution; the fix is unretouched exports `[community — sozee]`.

And one false positive: on Krea 2, **Raw previews look plastic by design**. Raw is undistilled and flat; verify on Turbo and do not read the previews as a texture problem `[community — chengyansen-ai, krea2-lora-training v0.4.0]`.

### Multi-resolution buckets

Multi-resolution training is mainstream on most DiTs: ai-toolkit ships `resolution: [512, 768, 1024]` for Flux and Qwen-Image `[official — ai-toolkit example configs]`, and BFL says start at 512 for iteration, finish at 1024 or higher `[official — docs.bfl.ml]`. On Krea 2 it is contested, and [`krea-2/references/lora-training.md`](../../krea-2/references/lora-training.md) §2c carries the flag. Two community sources bucket 512+768+1024; this suite's krea-2 skill argues 768 was never a trained stage; the lab's nine-run recipe used `[1024]` only. The "768-only" tooling default is a memory lever, not a quality claim. The argument is in [`krea-2/references/lora-training.md`](../../krea-2/references/lora-training.md) §2c.

### The wrong turn, named

The lab's high-res rabbit hole ran three attempts to buy quality with pixels, and two made things worse. The 2048/20-step grain was read as freckle stipple and nearly declared a hard limit. A VAE swap, texture-anchor words and a detail-heavy finetune were stacked as "sharpeners" on top of over-band renders; none of them was the cause. A canonical-face hunt at 1536 shipped candidates with half the linear face detail the dataset already held, because nobody measured the face box first. And a freckle-placement diagnosis, complete with a research sweep and a pilot design, was superseded before its pilot ever ran. **The rule that would have saved the day: before diagnosing a subtle skin artefact, verify you are inside the base model's trained resolution band and step band. Then look at the wall.**

---

## 4. Captioning

**The rule: caption the residual.** Describe everything that varies. Never describe what you are teaching. Krea's own phrasing from the other side: "if an image has a detail you don't want the LoRA to learn, call it out in the caption" `[official — krea.ai, 2026-05-21]`. The community states the same rule as a sorting test: caption background, lighting, camera angle and pose exhaustively, because those are what should stay promptable rather than baked in, and leave a fixed outfit or hairstyle out of the captions entirely when you want the LoRA to own it `[community — r/StableDiffusion 1wacvcm, 2026-09; convergent]`. The same thread adds a rule the table below implies: do not mix realism, anime and painterly sources in one LoRA, or it learns a blended style nobody asked for.

| | Character LoRA | Style LoRA |
|---|---|---|
| Never caption | the face, the identity, the trigger's referent | the medium, rendering, palette |
| Always caption | pose, angle, shot size, expression, clothing, setting, lighting | the subject and everything depicted |
| Diversity needed in | everything except the person | **subjects above all** |

**Caption what the image shows, not what the prompt asked for.** On a generated set the prompt is not the image. The nose stud landed and the barbell did not. "Full" makeup left the freckles visible. Two cells framed to the thigh despite "head to feet". The lab records per cell what each kept render actually contains and generates the captions from that manifest, so a caption cannot drift from its pixels `[live-use — media lab, Ciara manifest.json, 2026-09]`. On real photos the equivalent is a caption audit before every run. The model of what one catches `[live-use — media lab, dataset v8 audit, 2026-08-30]`:

- framing terms wrong on all four body cells (`full body nude` → `three-quarter length nude cropped at the knees`);
- an uncaptioned tongue-out expression — the highest-cost error in the set;
- an unnamed low camera angle on the set's *only* below-eye-level frame, which would otherwise have bound the low angle to the laugh sharing it;
- indoor/outdoor and backdrop-colour errors.

Two earlier flags in that audit were withdrawn as wrong; the audit can over-correct. And **caption anything at the frame edge that would otherwise bind in** — a baby carrier, a hat crossing the hairline, a wall of framed photographs behind her.

**Caption contextually by shot size.** Describe only what is in frame, so a close-up omits the outfit below the crop `[community — JahJedi, 2026-06-26]`. It is an anti-composition-overfit measure, and it is the same rule as the manifest one seen from the other end.

**Format follows the model, and the trigger rule is per model, not per encoder class:**

| Encoder | Caption style | Trigger token |
|---|---|---|
| CLIP-class (SDXL-era, Pony/Illustrious/NoobAI) | Weighted comma-separated tags, booru dialect | **Verbatim rare token**, used literally |
| LLM/T5-class (Flux, Z-Image, Qwen-class, Krea) | Natural prose clauses; Z-Image is tolerant of tags by construction, Qwen-Image prefers concise | **Camps split by vendor** — see below |

Getting the caption style backwards is a common reason a LoRA "trained fine but won't trigger". The trigger question is genuinely open `[contested]`. BFL prescribes a made-up token (`SPR1TE8`, `RISO_PR1NT`) used consistently across all captions on FLUX.2 klein, an LLM-encoder model `[official — BFL, 2026-06-04]`. A Qwen-Image guide uses `ohwx personname`. A Z-Image trainer puts a non-word token at the very start of the caption in sentence position, never in quotes `[community — AInVFX]`. Against that, on Krea 2 random strings are reported to be ignored or learned poorly, surfacing as text or a watermark `[community — promptdexter, 2026-07-24; single report]`. What the lab shipped: a `z<name>` token folded into prose — "a woman named zciara". It was used unchanged across Krea 2 and H3, from the same `.txt` sidecars without re-captioning, and `cache_text_embeddings: true` was safe only because the token is literal in the sidecars `[live-use — media lab, 2026-09]`. Expect bleed: "named zciara" printed the token on signage and name badges in one flexibility sheet. Options are to prompt around signage or drop "named" and use the token bare. No published A/B of `ohwx` against a natural name on an LLM encoder exists.

**On a single-subject set the trigger is not a gate, and that is expected.** A three-condition A/B — base plus trigger, LoRA minus trigger, LoRA plus trigger — settled it `[live-use — media lab, Amy trigger A/B, 2026-08-31]`. The base rendered an unrelated woman with the token. The LoRA rendered the same person with or without it. Every image is the same subject and every caption carries the token, so it never has to discriminate. The cheapest loss reduction is to move the model's generic "woman" toward the subject. Three consequences follow. A caption rewrite cannot make the trigger selective. A multi-character scene will drag every woman toward the subject (§5). And the levers are regularisation images of other people captioned *without* the token, or reduced strength at inference. Every generation prompt should still carry the trigger — a probe that drops it tests the base — but do not expect it to switch the person off.

**When a trait belongs to the person but still changes, caption whatever changes it.** Caption-the-residual has a blind spot that the table above hides: some things are clearly part of the identity *and* clearly variable. Freckles are the tidy example. They belong to her, so the rule says never name them. But they fade under foundation, so a set shot over both bare-faced and made-up days contains two versions of her skin.

Leaving both unnamed does not quietly average out. The model has to blame the difference on *something*, and it picks whatever else happens to line up: the formal dress that shows up in the made-up shots, or the indoor light, or the year. You end up with a character who mysteriously loses her freckles in evening wear.

The fix is to name the **cause**, which is not part of the identity and does change, and leave the trait unnamed:

| | Caption it? | What you get |
|---|---|---|
| The freckles (the trait) | **Never** | They stay part of `<trigger>` — the default face |
| The makeup (the cause) | **Wherever you can see it** | A switch you can flip: add "wearing foundation" when you generate, and the freckles fade, exactly as they do in the photos |

Caption the **exception, not the rule.** If most of the set is bare-faced, leave bare-faced unmentioned so it becomes the default, and put a makeup clause only on the made-up images. One curator's working test: "if her freckles have almost completely disappeared she is probably wearing a base layer, so say so". Makeup is named as plain makeup, with no mention of what it hides `[live-use — media lab, Amy caption doctrine, 2026-09]`. The same shape covers tan lines, glasses, a beard grown and shaved, hair up or down, a necklace she always wears — anything where the question "is this the person, or is this a variable?" answers *both*. Ask what nameable thing changes it, and caption that.

**Which traits become promptable when captioned, and which fight the LoRA instead, was measured** `[live-use — media lab, krea2-v13 vs v14, dataset v18, 2026-09-05/06]`:

| Captioned on every image | Result |
|---|---|
| Hair colour and length | **Became promptable.** "Auburn" renders auburn, "dark-blonde" lighter, the bob is a bob, "long" reaches past the shoulders — where the previous LoRA gave light-brown shoulder-length for all of them. Cost: prompts must name hair from then on |
| Age ("aged N") | Did not become promptable |
| Freckle density | Did not become promptable, and **became a prompt variable that fights the LoRA** |

Both of the last two were stripped for every later set — no age, no freckle, no fine-line words in any caption — and left to bind to the trigger. The distinction is the one the table above draws. Hair is a *variable* the model can separate. Age and freckle density are the *identity*, and naming them tells the model they are optional without giving it anything it can separate.

**Naming a trait in the generation prompt while showing it in every image over-bakes it.** One synthetic set made with "freckles across her face and body" in every prompt learned heavy, even freckling far beyond the real person `[live-use — media lab, 2026-08]`. The words were in the caption *and* the thing was in every image, so it got taught twice. No external source supports this mechanism, and the nearest published experiment points the other way. Pulling hair colour *out* of a trigger into its own tag caused colour drift that stabilised only when reabsorbed `[community — lilting.ch, 53-image experiment, 2026-04-26; single report]` `[contested]`. If a trait is part of the identity, let the pictures teach it and control it through its cause.

**Using the same words matters more than using rich ones.** Call it "three-quarter view" in one caption and "angled slightly away" in another, and you have split one concept into two. Pick your terms and reuse them exactly.

**Caption length: even, or deliberately varied — contested.** The older rule is to keep caption length even across the set, because three-word captions carry more weight per word than forty-word ones in ways that are hard to predict. Against it: on Z-Image "caption variety matters more than length", and a deliberate mix of short (5–10 word) and long (30–50 word) captions is reported to improve generalisation. Two sources name "identically structured captions for every image" as a failure mode `[community — AInVFX, Scenario; convergent]`. The lab's shipped sets run 46–78 words per caption and have not tested variety. Neither this nor the dropout rate below has a head-to-head `[contested]`. What both camps agree on: never exceed ~70 words, and never write the same caption twice.

**Caption dropout is disputed by the same gap, an order of magnitude with no head-to-head.** ai-toolkit ships `caption_dropout_rate: 0.05`, and every lab run used it. The 0.33-ratio article calls **0.3** "the strongest single fix for generalisation", naming "only renders in training environments" as the symptom of too little `[community — neonkisu]`. musubi is only now adding it (PR #1084, draft, default 0.0, example 0.1), and rejects it outright for image-conditioned text-encoder caching such as Qwen-Image-Edit `[official — kohya-ss/musubi-tuner PR #1084, 2026-08-31]`. That last constraint bites the factory in [`synthetic-datasets.md`](synthetic-datasets.md): a synthetic pipeline trained on an edit model in musubi cannot also use the one mitigation the collapse literature recommends.

**Do not rewrite captions and change images in the same arm.** The run that did both could not attribute its loss `[live-use — media lab, krea2-v10, 2026-09-03]`. One variable per run applies to captions as much as to hyperparameters.

**Tooling.** `ComfyUI-CaptionThis` packages Janus Pro, Florence-2 and JoyCaption behind one node for dataset captioning; Florence-2 + WD14 combo workflows give a natural description plus booru tags in one pass `[community — MieMieeeee/ComfyUI-CaptionThis, 2026]`. Whatever generates the draft, the manifest or the audit above is what makes it true.

**Training with no captions at all is contested.** Some trainers run DiT character LoRAs that way and report good replication. It does work for pure replication, but you give up control: you cannot vary what you never named. Treat it as a specialised technique, not a default. `[contested]`

---

## 5. Multi-outfit and multi-character

**Multi-outfit.** One character LoRA can hold several distinct outfits, as long as each gets its own trigger tag, looks clearly different from the others, and has enough coverage of its own. The practical ceiling is around **six outfits** before they start bleeding together `[community — Khanykov01, Civitai 6990; strong]`. Past that, use separate LoRAs, or stack an outfit LoRA onto the character.

The failure is lopsided: outfits bleed into each other long before the identity suffers. If your character starts wearing a mix of two outfits, that is the ceiling announcing itself.

**Multi-character.** Do not train two people into one LoRA. They average. The same averaging governs any multi-class LoRA. A Krea 2 LoRA meant to cover several distinct ethnic-appearance groups pulled toward whichever group had the most images unless sampling was balanced per class, and a low rank compressed the whole wide feature space toward its mean, so a wide-feature LoRA needs more rank than a single identity does. The compromise that thread landed on was two to four LoRAs by broad cluster at ~75–100 images each, rather than one omnibus LoRA or a dozen narrow ones `[community — r/StableDiffusion 1w9ysn0, 2026-09; single report]`. Train separately and compose at generation time:

- **Regional conditioning** where the model supports it (image side).
- **Per-face detailer passes** — generate the scene without character LoRAs, then run a detailer per face with the relevant LoRA loaded. This is the most reliable route on image models.
- **Separate shots and cut between them** on video, where no regional conditioning exists across frames.

**Identity bleed goes up with visual similarity.** Two characters of similar age, build and colouring trade features far more than two who look nothing alike. This is worth knowing at casting time, while it is still cheap to change. A single-subject LoRA moves the model's generic "woman" rather than keying on its trigger (§4). So expect *every* woman in a scene to drift toward the subject, unless the LoRA was trained with regularisation images or is run at reduced strength.

### Differential Output Preservation — a training-time answer, on some models

Everything above assumes composing at generation time is your only lever. Since mid-2026 there is a **training**-side option too, though it depends on the model in a way that matters.

**Differential Output Preservation** (DOP) trains each character LoRA against a **class**, such as `"woman"`. It preserves the base model's output for that class while learning the individual. Several such LoRAs can then load together in one generation with very little bleed. A reproducible recipe: a LoKr config with DOP enabled, class `"woman"`, and **1500 steps** rather than 750 (previews stabilise around 1500) `[community — MASilverHammer, r/StableDiffusion]`.

Boundaries, from the same source:

- **Hard cap of four characters.** Five falls apart; four holds.
- Characters **borrow features from each other**, with lips the reported offender, so similar-looking characters drift toward looking related. The similarity rule above still applies. It is just less punishing.
- **Prompt the distinguishing features.** Naming what separates two characters (a long nose, a jawline) is what keeps them separated at inference.
- Captioning still matters. The author's lazily-captioned sets (trigger word only) worked; their well-captioned set produced the more resilient LoRA.

**The model-dependence is the important part.** The same technique **failed on Z-Image Base**, where DOP stopped the character being learned at all, and **worked on Krea 2**. Do not assume it transfers. If a multi-character job is the requirement, that is now a reason to choose the base model on this axis specifically: see [`krea-2/references/characters.md`](../../krea-2/references/characters.md). Above four characters, or on a model where DOP does not take, fall back to per-face detailer passes.
