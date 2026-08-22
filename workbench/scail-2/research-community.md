# SCAIL-2 — community evidence (2026-08-22)

Harvested from r/StableDiffusion, r/unstable_diffusion, r/comfyui and the civitai.red models
API. **Everything here is community-sourced.** No primary source (model card, repo, paper,
licence) was reachable in this pass — see "Contested / unresolved" for what that leaves open.

Raw page text: `../research-2026-08-22/raw/scail-2-reddit-search.txt`,
`scail-2-reddit-comments.txt`, `unstable-diffusion-search.txt`, `comfyui-search.txt`,
`civitai-api-2026-08-22.txt`.

---

## Craft

### The one rule that changes everything (confirmed again, from the source)

`u/blackmixture` — "I ran SCAIL 2 through a bunch of scenarios it should not handle", **1,793
points, 178 comments**, the highest-scoring post in this entire sweep:

> *"Character swaps are the strongest use case. The trick is prepping your reference properly.
> Use Flux Klein 9B or the Krea 2 Identity Edit LoRA to edit your **actual first frame** into
> the new character, so the reference is already in roughly the same pose and framing as where
> the driving video starts. Do that and the results are excellent."*

Independently arrived at by three other practitioners:
- `u/DeerWoodStudios` (GTA 6 remake, 466 pts): *"For the image edit I used a mix of flux klein,
  qwen image edit and Krea identity edit."*
- `u/LucidFir` / `u/ChairQueen`: *"1: flux2klein9b image to image the 1st frame of your video
  into whatever style you want. 2: that image and your video go into the workflow. 3: generate."*
- `u/Jayuniue`: "Flux Klein 9b + scail 2".

**Caveat the brief doesn't have:** the edit prompt has to be *simple*. `u/blackmixture`'s actual
prompt for the flagship clip was *"make the man a blonde woman"*. And it does not solve
face→specific-face: `u/Cre0na`, after trying, *"I'm struggling with turning a face into another
face"* — unanswered.

### The craft nobody else has written down: u/nsfwVariant's shot-by-shot method

This is the deepest SCAIL-2 material in the sweep, from a single long comment thread under
`u/blackmixture`'s post. Every item is a workaround for a specific model failure:

**SCAIL hates small subjects.**
> *"the very zoomed out shot near the start (SCAIL hates small people). For those you have to
> zoom in close so SCAIL recognises & replaces the characters, then composite the zoomed-in
> footage back on top of the zoomed-out footage to get your finished shot."*

`u/spiderofmars` (r/comfyui) independently derived the same rule and quantified it: a 1280×720
clip with head-to-toe people gives mushed faces; **pre-crop the characters into a 720×1280 clip,
generate at 720×1280, then scale back down onto the 1280×720 timeline and LTX-2.3-outpaint the
black borders.** *"This takes it from a 720 pixel full person input/output to a 1280 pixel full
person… The colour matching out of the box is almost perfect."*

**Characters entering from off-screen.**
> *"you might need to process a certain shot in reverse to make sure SCAIL can handle characters
> that start off-screen (thus making them start on-screen), then re-reverse it back."*

**Giving the model positional hints.**
> *"manually place your character reference near the spot where the to-be-replaced character is
> in the shot (as in, move them to the same spot they'd be if you overlaid the ref image over
> the video)… Or just change the order your reference images are being fed in. Or change the
> zoom level of your reference images to match the initial zoom level in the clip."*

**Multiple references — and the mask rule everyone misses.**
> *"To feed SCAIL more refs you just have to batch them together (using the batch images node in
> Comfy)… you need to feed in a corresponding mask as well though; **need same number of images
> in the ref image batch and the mask batch**. Also make sure you read the SCAIL docs on how it
> interprets the mask colors (especially the black vs white backgrounds), it's super
> important!"*

`u/infearia` (8 pts) points at the first-party path for this: Kijai's multi-reference example
workflow landed in `Comfy-Org/ComfyUI` PR **#14509**, and the pattern is *"a start frame AND one
or more separate reference images of the objects/persons in the clip."*

**fps.**
> *"I did it in the native 24fps the movie is in. You can't really do it any other way with
> action scenes, they're too fast to look right downframed to 16 fps… Wan can do both 16 and 24
> fps without issue as long as there's enough context for how fast things should really be
> moving."*

**Post-fix the two standing artefacts with SAM3 rather than re-rolling.**
> *"Lighting and clarity (character being too bright or too clear) are common inconsistencies
> with SCAIL, both of which are thankfully pretty easy to fix"* — mask the character again with
> SAM3 in post and adjust in a normal NLE.

He tried and abandoned the **relight LoRA**: *"I think I tried the relight lora once and
couldn't get anything good out of it, but don't take my word on that."* `[single source, weak]`

### Context windows — the biggest contested craft claim

`u/nsfwVariant` reverses the usual assumption:
> *"It's the opposite! I don't know why exactly, but using context windows usually **restores**
> the quality rather than degrading it. As in, if you start from the end of a partially degraded
> video it'll actually bring it back up to a less degraded state once it goes past a window or
> two. The longest single shot I've tested SCAIL 2 on is **1 min 45 seconds** long, and the
> quality is 100% consistent the entire way through."*

His practical guardrail is about *risk*, not quality: *"if something goes wrong it can easily
chain to the rest of the video… So I recommend generally sticking to shots up to around **~161
frames**… You can go to ~201 or even higher for 'easy' shots."*

**Directly contradicted by `u/blackmixture`:** *"In practice though, the sliding context degrades
the adherance to the original video. I've done a 1 minute video but only the first 30 seconds
were perfect."* `[contested]` — and the difference may be that blackmixture is measuring
*adherence to the driving video* while nsfwVariant is measuring *image quality*. Worth resolving
before writing this into a skill.

Related long-form stack from the same author: **VACE** to join clips (workflow:
`pastebin.com/w01EEy3e`), then **SVI** LoRA + context windows to refine
(`pastebin.com/AfyAEpep`) — *"brings the quality back up across the whole thing and also hides
the boundaries between all the individual clips - they tend to have things like color shifts and
quality drops."* Demonstrated on a 42-second seamless loop assembled from ~16 clips.

### Sampler / workflow settings

From `u/External_Trainer_213`'s "Wan SCAIL-2 Segmentation Control" (civitai.red/models/2699283):

- **"SCAIL Auto Extend" is the preferred sampler**: *"This one seems to have no or fewer color
  shifts. And doesn't need the 'Color Match' option (This is already integrated)."*
- **Input-video interpolation** — new option, and it has a real cost: *"The animation is much
  smoother. The downside, however, is increased computational overhead, and Scail-2 is quicker
  to 'forget' new parts of the animation."*
- **Identity Tracker, multi-character**: *"set `object indices` to 'nothing' (empty field, no
  value). Then set the SCAIL-2 Identity Tracker to **'Point'** and select your characters by
  clicking on them… You can also try 'Box,' but if there are more people present, this could
  lead to problems. Use a start image similar to the one in the video."*
- General escape hatch: *"If you encounter issues, setting a new seed or switching the sampler
  usually helps."*
- Feature list also includes RMBG background retention, LoRA support, image sharpener,
  Sage Attention, alternative audio file loading, colour correction.

**SCAIL-2 tracks; it does not invent choreography.** `u/External_Trainer_213`: *"the input video
was a staged fight. Consequently, the kick and the movement could look significantly more
realistic if they were actually fighting. **SCAIL-2 tracks the movement sequences and does not
invent its own.**"* Note this sits slightly against `u/blackmixture`'s *"It invents motion it was
never given very well"* — reconcile as: it invents *embellishment* (fire arcs, cloth, hair) on
top of tracked motion, not the motion itself.

### Speed and quantisation — a mess, and the mess is informative

| Rig | Job | Time | Source |
|---|---|---|---|
| RTX 6000 Pro 96 GB / 128 GB | one generation | **~2–3 min** | `u/blackmixture` |
| RTX PRO 6000 Blackwell 96 GB | 10–15 s clip | **~20 min** | `u/Cloud9_pilot` (r/comfyui) |
| 5080 16 GB | 5 s low-res | 13 min | `u/uxl` |
| 5070 Ti | 720p | *"if a generation takes 10 minutes… I know I have a memory leak"* | `u/Dzugavili` |
| 5060 Ti 16 GB, Wan2GP | 720p, 5–15 s | ~20 min | `u/paulct91` |
| 4070 Ti Super 64 GB | 9 s @ 384p, 60 fps, 10 steps | **30 min** | `u/wikid24` |
| 4060 Ti 16 GB, fp8_scaled | 253 frames | 9 min | `u/kayteee1995` |
| 4060 Ti 16 GB, int8-convrot | 253 frames | **15 min (slower!)** | `u/kayteee1995` |

Two actionable things fall out:

1. **`int8_convrot` can be *slower* than fp8 if your CUDA/PyTorch build is wrong.**
   `u/kayteee1995` was on `torch-2.8.0 + cu128`. This is the same CU130 trap the suite already
   documents for MiniMax H3 in `research-2026-08-22/FINDINGS.md` §1b — it reproduces on the Wan
   family. `[strong inference, not directly confirmed]`
2. **`u/MoreColors185`: *"Use the fp8, not the gguf quants. They slow things down across all
   models for me with 16 vram."*** Directly against the GGUF-first advice in the low-VRAM
   workflows. `[contested]`

Speed LoRAs: `u/Dzugavili` — *"it likes the lightx2v loras"*, pointing at Kijai's build.
`u/Friendly-Fig-6015` asks whether 4-step LoRAs work; unanswered. `u/paulct91` on Wan2GP:
*"if using low vram gpus it really really likes high system ram amounts, 32, 64, 64+ gbs."*
`u/wikid24`'s own complaint frames the whole cost picture: *"pretty damn long considering that
ltx2 usually takes me 2 to 5 minutes similar resolution using transfer motion."*

---

## Prompting (with quoted real prompts)

**SCAIL-2 barely has a prompt.** Every posted example is a one-line description of the intended
result; all the control lives upstream (reference prep) and in the node graph (masks, tracker).

`u/ChairQueen`'s complete two-stage prompt pair, and it is the whole prompt:
> Flux2Klein9b: *"Convert the penis to a tentacle dildo and the duckt tape to a magical portal"*
> Scail2infinity: *"the woman is being fucked by the tentacle"*

`u/blackmixture`'s first-frame edit prompt: *"make the man a blonde woman"*.

`u/LucidFir` on the upstream stage: *"it's just a flux2klein9b workflow, the prompting
understands natural language really well"* (`pastebin.com/YdNy8cJ3`).

**The contrast prompt worth carrying into the skill** is the MiniMax H3 prompt someone wrote to
*emulate* SCAIL — because it shows exactly how much structure H3 needs to do the same job, and
therefore what SCAIL is saving you. `u/Darqsat`, after **400+ test generations**:

```
subject_definitions:
<Subject 1> is woman in <Picture 1> with redhead and black tank top.
<Subject 2> is the woman originally in <Video 1>.

summary:
[video editing + Audio reuse] The target video is an edited version of <Video 1>.
<Subject 2> is replaced with <Subject 1>, who takes over her pose and movement.

retention_analysis:
<Subject 1> (appears in [Shot 1]): fully_preserved - her face, hairstyle, and body from
  <Picture 1> are retained throughout. Her clothes are not retained.
<Subject 2> (appears in [Shot 1]): attribute_transfer - her pose, movement, and screen
  position are transferred to <Subject 1>.

detailed_description:
The target video keeps <Video 1>'s original style, lighting, and camera work unchanged.

overall_soundscape: N/A
non_diegetic_music: N/A
```

His findings, which are also a good description of what SCAIL does *without* being told:
*"You don't need to describe action in detailed_description… Retention analysis section seems
like the next MAIN or even only main driver… you have to add better and stronger anchor for
model - something visually big like hair, clothing, position on screen. The stronger you
describe `<Subject N>` the more stable the reference."*

---

## Ecosystem

### Civitai says something important about what SCAIL-2 *is*

`query=SCAIL`, sorted by downloads: **every single hit is a `Workflows` entry.** There is no
checkpoint, no LoRA, no ControlNet tagged SCAIL on Civitai. The base-model tag creators pick for
those workflows is overwhelmingly **`Wan Video 14B i2v 480p`** — a Wan 2.1 tag:

| Workflow | Base tag | Downloads | Creator |
|---|---|---|---|
| SCAIL2 - Long videos + High-res fix + NVIDIA VSR + Interpolation | Wan Video 14B i2v 480p | 1,207 | LatentHeart |
| SCAIL2 Motion Transfer / Character Replacement | **Wan Video 2.2 I2V-A14B** | 592 | DeepWhiteAI |
| Scail Single-Person Motion Transfer (720P HQ) V2 | Wan Video 14B i2v 480p | 335 | T8star |
| SCAIL-2 Single-Person Reference Editing Long-Video | Other | 229 | AIKSK |
| Scail Single-Character Motion Transfer (720P Uni3c Camera Work) V2 | Wan Video 14B i2v 480p | 149 | T8star |
| Scail Dual-Person Motion Transfer (720P HQ) V2 | Wan Video 14B i2v 480p | 141 | T8star |

Plus, referenced from Reddit but not surfaced by that query:
`civitai.red/models/2699283` (Wan SCAIL-2 Segmentation Control, External_Trainer_213) and
`civitai.com/models/2707066` (SCAIL-2 Unlimited Length Workflow and Nodes).

### Nodes, forks and runners

- **`collbroGTR/comfyui-scail2-infinity`** — the community's current favourite. `u/LucidFir`:
  *"this pretty god-like workflow. I can render 11 seconds of width=1408 height=2560 (after it
  runs upscale) with this. Frame Load cap set to 285."* Ceiling he hit: *"beyond 285 frames of
  972x1728 input."*
- **`dvelm/SCAIL-2-Unlimited-Video-Low-VRAM`** (`u/develm0`, posted 10 hours before harvest) —
  GGUF + automatic chunking for **8–12 GB** cards, *"chaining overlapping segments while
  preserving motion continuity."* Describes the model as *"SCAIL-2 / Wan 2.1"*.
- **Wan SCAIL-2 Segmentation Control** (External_Trainer_213) — Identity Tracker, SCAIL Auto
  Extend sampler, input interpolation, RMBG, LoRA support (details in Craft above).
- **Mix Studio** (`BlackMixture/Mix-Studio`, GPL-3.0) exposes SCAIL 2 as a one-click video mode
  next to Krea 2, Flux 2 Klein, Qwen Image Edit, LTX 2.3/2.5, Wan 2.2 and 10Eros; the "Edit →
  use as first frame → SCAIL 2" path *is* the reference-prep rule made into UI.
- **Wan2GP** — the low-VRAM runner of choice (`u/wikid24`, `u/paulct91`).
- **Maestro** (via Pinokio) — `u/Delightful_Disciple` runs SCAIL-2/SAM 3 there.
- **`nghtdrp/nghtdrp_snapmogen_motion_library`** — searchable SnapMoGen mocap browser that
  exports OpenPose/mannequin/clay/volumetric drivers *"in LTX, Scail 2 or Bernini."* This is a
  way to get a driving video when you don't have footage; `u/LucidFir` uses Mixamo
  ("walking", "in place" checked) for the same purpose.
- **SAM 3** is the tracking substrate (`u/Delightful_Disciple` names "SCAIL-2/SAM 3"), and SAM3
  also does the post-production masking (`u/nsfwVariant`).

### Bernini-R, the sibling

`u/Pyros-SD-Models` (18 pts): *"bernini and scail2 are crazy underrated."*
Links: `bernini-ai.github.io` and `huggingface.co/Comfy-Org/Bernini-R` (Comfy-Org hosted).
`u/Future-Coffee8138`: *"Bernini-r is based on **wan 2.2** not 2.1 and it can use wan2.2 Loras.
My only complain is that it's pretty resource demanding."* Corroborated:
`u/traithanhnam90` — *"Even though I used `wan2.2_bernini_r_high-Q5_K_M.gguf`, my machine was
still sluggish, while Scail2 was excellent"*; `u/kayteee1995` — *"I got OOM anytime try to make
a more than 5s (with Context Windows Manual)."*
On capability, `u/throwaway0204055` (asked twice, unanswered both times): *"I am able to swap
source video's outfit but not face. Is Bernini-R supposed to work with face swap?"* — which
matches the brief's note exactly and remains **unresolved**.

---

## Characters & identity

**Strengths, from `u/blackmixture`'s systematic test** (all verbatim):
- *"Object permanence held up better than expected. In the car clip the vehicle becomes
  completely out of frame and then comes back in, and it stays consistent."*
- *"It invents motion it was never given very well… the fire comes off my fist in a believable
  arc, even though there is zero fire data in the driving footage. It copies the underlying
  movement and then adds embellishments that fit."*
- *"The physics test was the biggest surprise. I swapped a flower for a wine glass. Hand tracking
  stays locked, the liquid inside sloshes correctly for the motion, and because the glass is
  transparent the background actually refracts and distorts through the water."*
- *"Weakest spots were text… the text turns into mush, so I'd avoid text."*

**Failure modes, named and unfixed:**
- `u/Zenshinn`: *"My issue with SCAIL 2 is that it tends to change faces."* — unanswered.
- `u/zsnck`, using Kijai's multi-reference workflow with front *and* back refs: *"for videos
  longer than 5 seconds, the clothes will morph into different clothes, especially if the
  character is turning around or doing different poses."* — unanswered.
- `u/Wezaluketek`: *"Scail-2 has big issue with skin texture in many cases, luckily dev team
  opens training code soon so we can fix such things."* `[single source]` — also the only
  reference anywhere in the sweep to a SCAIL "dev team" with a release plan.
- `u/Coach_Unable` (r/comfyui): *"When I try to use the default workflow in **replace mode**, the
  background also changes… tried a few workflows and it happens in all of them."* — unanswered,
  and it contradicts the intuition that replacement is character-local. Note RMBG background
  retention in External_Trainer_213's workflow exists precisely to fight this.
- `u/Delightful_Disciple` (60 pts): tracking simply refuses on some footage. *"even the close up
  shots I've isolated refuse to track when it's basically just him on screen. I've tried every
  variation of description from simple to complex and still nothing."* 5090 laptop 24 GB / 96 GB.
- `u/Draco18s` audited `u/blackmixture`'s own showcase and found background-crowd identity
  merging and terrain changes during the off-screen excursion: *"AI has a guy in a red shirt run
  towards a guy in a white shirt, merges with him, and emerges again on the other side ten feet
  further away and wearing a brown shirt."* The object-permanence claim survives for the
  *tracked* subject; it does not extend to the scene.

**The multi-person outline/glow problem** named in the brief did not resurface in this pass —
neither confirmed nor contradicted. The Identity Tracker "Point" mode guidance above remains the
recorded mitigation. `[unverified this pass]`

---

## NSFW

SCAIL-2 is the current NSFW character-replacement tool of choice, and the pipeline is fixed:
**Flux 2 Klein 9B for the first-frame edit → SCAIL-2 Infinity for the animation.**

- `u/ChairQueen`, *"SCAIL-2 + flux2klein9b is magic. Unbeatable."* (64 pts) and *"SCAIL-2
  Infinity is best option for NSFW anime to real / style transfer"* (19 pts). Method verbatim:
  *"After a solid week of trying options... my opinion is that this is the best current method.
  1: flux2klein9b image to image the 1st frame of your video into whatever style you want.
  2: that image and your video go into the workflow linked above. 3: generate."*
- Her one hardware rule: *"I just highly recommend that you **reduce the resolution of your
  inputs** down to something manageable before you get the dreaded OOM. I still don't know how
  to calculate durationXresolutionXmodels&loras to figure out if I'm going to OOM or not."*
- Practical friction worth knowing: *"catbox.moe is unreliable, filegarden.com deletes things too
  quickly, and pastebin won't allow nsfw content"* — NSFW SCAIL workflows are hard to share, so
  the Civitai `.red` mirror is where they actually live.
- `u/Jayuniue`, "Flux Klein 9b + scail 2" (36 pts) — same stack, workflow on Google Drive.
- `u/External_Trainer_213` ships a *"Breast jiggling tracking"* demo and a PG-13 Civitai rating
  alongside his workflow; the physics tracking that impresses people in SFW demos is the same
  thing being used here.

**The reason SCAIL wins over H3 for this work is exactness of motion**, stated most clearly by
`u/LucidFir`: *"Minimax H3 is obviously fantastic, but when I was trying to use it for style
transfer with the ref2v workflows the output wouldn't follow the reference motion exactly.
**Exact adherence to the motion reference is critical to my use case, iykyk.**"*

Also note `u/blackmixture`'s Mix Studio ships **PIN-protected private profiles and locked
folders** — *"keeping private generations out of your everyday library"* — i.e. adult use is
designed for, not tolerated, in the dominant SCAIL front-end.

---

## Positioning vs covered models

**vs Wan Animate.** `u/CelestVestra`: *"This looks just as good if not better than wan animate
and kling mo control... I thought those were better than Scail?"* → `u/blackmixture`: *"I think
it is better for sure than Wan Animate and Kling motion control. On my insane GPU it is
significantly faster too."* And after shipping **Wan Animate 2** support in Mix Studio v1.2.4 he
still says: *"**I still prefer SCAIL 2 for fidelity.**"* That is the cleanest available answer to
the brief's routing question.

`u/thisiztrash02` (7 pts): *"it's objectively better than Kling — first time a Local Model is
Ahead in anything since the stone ages of AI."*

**vs MiniMax H3.** Three separate practitioners describe the same split:
- `u/LucidFir` (above): H3 doesn't follow motion exactly; SCAIL does.
- `u/Darqsat` spent 6 hours and 400 generations building an H3 prompt to imitate SCAIL, and the
  result still needs heavy anchoring to hold identity (prompt above).
- `u/Mediocre-Toe3212` documented H3 Ref2V's hard limit on this job: *"As long as the Float
  Duration is 5s or less, there is no issue at all… at 7s, it usually never latches on."*
  His tuning, useful either way: **12–15 steps beats the template's 20** (*"the preview node
  tries to latch onto the face too much and then just gives up"*), `ref_image_size` **MAX** beats
  `match`, videos normalised to 24 fps / 864×480, and *describe the subject, not the action* —
  *"Previously, I tried to describe what happens in the scene, but I found that it changes the
  video entirely."*
- `u/Friendly-Fig-6015`, the low-end version of the same routing decision: *"im thinking in back
  to scail because minimax cant do character replace in my low config pc."*

**vs LTX-2.x.** Complementary, not competing. `u/spiderofmars` uses **SCAIL for the animation +
LTX 2.3 outpaint for the frame** (full method in Craft). `u/Strange_Test7665`: *"it can replace 6
ish objects perfectly and swap background all local. Post processing with ltx for some sound and
you really can generate video that rival any closed application"* — SCAIL is silent, so LTX or
H3 supplies audio. `u/wikid24` is the dissent on cost: LTX-2 does comparable work in 2–5 min
where SCAIL took him 30.

**vs Krea 2 / Flux 2 Klein.** Not competitors — they are SCAIL's mandatory front end. The suite
already documents Krea 2 Identity Edit from the image side; this is the consumer.

---

## Contested / unresolved

1. **The base model — still not primary-sourced, but the community is nearly unanimous on Wan
   2.1.** `u/MortytheMort` (18 pts): *"Scail 2 utilizes wan 2.1."* `u/ffzero58`: *"It is part of
   Wan 2.1, open source."* `u/Schandermania`: *"Scail is based on Wan model."* `u/develm0`'s repo
   title says *"SCAIL-2 / Wan 2.1."* Civitai workflow authors overwhelmingly tag
   `Wan Video 14B i2v 480p`. **One dissent:** DeepWhiteAI tags his workflow
   `Wan Video 2.2 I2V-A14B`. `[contested, but weakly]` **Nobody has cited a model card, repo or
   licence.** The skill-vs-section decision in the brief still hangs on this.

2. **Context-window quality: restores or degrades?** `u/nsfwVariant` (1:45 at 100% consistency,
   quality *improves*) vs `u/blackmixture` (1 minute, *"only the first 30 seconds were
   perfect"*). Possibly two different metrics. `[contested]`

3. **20 min vs 2–3 min on the same GPU class.** `u/Cloud9_pilot` and `u/blackmixture` both run
   RTX PRO 6000 96 GB and report an order-of-magnitude difference. Neither published a full
   settings dump. `[contested]`

4. **fp8 vs GGUF on 16 GB.** `u/MoreColors185` says GGUF is slower across all models;
   the whole low-VRAM ecosystem (`dvelm`, Wan2GP) is GGUF-first. `[contested]`

5. **Resolution ceiling.** `u/teekay_1994`: *"doesn't SCAIL only generate up to 720p? Don't you
   lose a lot of quality from the original video when you run it through SCAIL?"* — unanswered,
   yet `u/LucidFir` reports 1408×2560 *after upscale* and `u/spiderofmars` treats 720p as the
   working ceiling. Unresolved.

6. **Does replace mode preserve the background?** `u/Coach_Unable` says no, consistently, across
   workflows. Nobody answered. `[single source, unanswered]`

7. **Bernini-R face swap.** Asked in two subreddits, answered in neither. `[unresolved]`

8. **Real-time.** `u/Ultragreed` asked about VTuber-style live use; `u/blackmixture`: *"Not
   possible real time at the moment."*

9. **Mix Studio telemetry.** `u/Unfair-Warthog-3298` asked whether it phones home;
   `u/seppe0815` asserted *"lol this workflow have tons of telemetry and other stuff"* with no
   evidence and no reply from the author. **Unverified accusation — do not repeat it as fact,
   but do not recommend Mix Studio without noting it is unaudited.** `[single source]`

---

## Sources

Reddit (all via old.reddit.com):
- `r/StableDiffusion/search?q=SCAIL&restrict_sr=on&sort=top&t=month`
- `r/StableDiffusion/comments/1v9rzk8/i_ran_scail_2_through_a_bunch_of_scenarios_it/` — u/blackmixture, 1793 pts, 178 comments (read in full)
- `r/unstable_diffusion/search?q=SCAIL+OR+Anima+OR+LTX&restrict_sr=on&sort=top&t=month&include_over_18=on`
- `r/comfyui/search?q=SCAIL+OR+Anima&restrict_sr=on&sort=top&t=month`
- Read from search-result selftext: 1vf20df (GTA 6 FAT) · 1v8sz9j (Tifa vs Solid Snake) · 1v6ylck (Weekend testing) · 1v3rjy1 (Mix Studio) · 1vssgow (Minimax H3 Video Edit like SCAIL) · 1v770tp (Chun-Li vs Ryu) · Wan SCAIL-2 Segmentation Control (update) · SCAIL-2/SAM 3 Tracking Help · Testing out SCAIL-2 (Wan2gp) · SCAIL-2 reigns supreme for style transfer · SCAIL-2 on 8GB+ VRAM · scail-2 supports lora 4 steps? · [Help] ComfyUI Ref2V · Bernini rv2v workflow

Civitai (JSON API, civitai.red, unauthenticated):
- `/api/v1/models?query=SCAIL&limit=30&sort=Most Downloaded`

Named repos / URLs surfaced (not opened — for the primary-source agent):
`github.com/collbroGTR/comfyui-scail2-infinity`, `github.com/dvelm/SCAIL-2-Unlimited-Video-Low-VRAM`,
`github.com/BlackMixture/Mix-Studio`, `github.com/Comfy-Org/ComfyUI/pull/14509` (Kijai multi-ref),
`github.com/nghtdrp/nghtdrp_snapmogen_motion_library`, `bernini-ai.github.io`,
`huggingface.co/Comfy-Org/Bernini-R`, `civitai.red/models/2699283`, `civitai.com/models/2707066`,
`pastebin.com/w01EEy3e` (VACE join), `pastebin.com/AfyAEpep` (SVI refine),
`pastebin.com/YdNy8cJ3` (flux2klein9b style transfer), `mixamo.com`.
