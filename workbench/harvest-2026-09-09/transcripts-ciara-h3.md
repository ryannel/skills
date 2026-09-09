# Transcript harvest — Ciara (Krea 2 v1–v5) and MiniMax H3, 2026-08-31 → 2026-09-09

Mined from seven `media-lab` session transcripts. Everything below is `[live-use]` — discovered by
running the pipeline, not by reading documentation. Baselined against
`characters/ciara/{DATASET-RESEARCH.md,V4-PLAN.md,V5-PLAN.md,H3-PLAN.md}`, so this records
**deltas and things those docs never captured**, plus the outcomes that overturned them.

Sessions: `bc6b2dbd` (08-31, Amy H3 ladder v1–v14), `e74af8e2` (09-06, Ciara created),
`65440253` (09-06→08, H3 research + h3-v1 + hoop piece + the resolution diagnosis),
`74b52f05` / `9452f9e5` (09-08→09, dataset v4 and the krea2-v4/v5 arms),
`b3b6f769` (09-09, Amy synthetic set), `2537e1da` (09-09, the user's read of the v5 test images).

---

## Learnings — Krea 2 / synthetic datasets

### 1. The settled resolution rule: render the dataset at 1024 native, never hi-res-then-downscale

This is the single biggest reversal in the whole arc and it **contradicts the hi-res doctrine that
`DATASET-RESEARCH.md` inherited**. `krea2-v3/run.yaml` states its experiment as *"Does training on
hi-res sources (downsampled into the 1024 buckets) give the LoRA real skin texture"*. The answer,
established 2026-09-08, is **no — it gives the wrong texture, and the texture survives the
downscale.**

The evidence chain, in the order it was actually run (`65440253`):

- A day was spent blaming the "scale"/reptile skin on **inconsistent freckle placement** across the
  62 v3 images (each render re-rolls freckle coordinates → the LoRA learns a distribution, not a
  map). That diagnosis is what `V4-PLAN.md` is built on, complete with LoFT / T-LoRA / Civitai-16340
  citations and a Krea 2 Identity Edit pilot. **It was superseded before the pilot ever ran.**
- A canonical-face hunt at 1536×1920 produced faces 710–846 px wide; the dataset already held
  1082 px (2048) and 1426 px (2560) faces. Rendering *bigger* was the obvious move.
- 2560 @ 12 steps beat 2560 @ 20 steps and 2048 @ 12 on lash separation, which separated two
  confounded variables: **the hexagonal mesh is a step-count artefact, not a resolution one.**
- Then a four-cell VAE-vs-band sweep settled it: **Wan 2.1 VAE and Qwen VAE are identical at 2048.
  It was never the VAE.** 1024×1280 native is clean; 2048 moderately crumpled; 2560 heavily.
  Downscaling 2048→1024 or 2560→1024 still loses to 1024 native.
- Root cause named: **Krea 2 Turbo's band is 1K–2K and Raw is 1K-native; the dataset had been
  rendered at 2048–2816, above the band**, with four sharpeners stacked on top (Wan VAE swap,
  texture-anchor words, a detail-heavy porn finetune, over-band resolution). Committed `d8eedc0`.
- Confirmed after training: `9452f9e5` — *"Scale skin: gone. Since rank 16 and rank 32 are equally
  clean, the fix was the 1024-native dataset, not rank."*

**The generalisable rule:** find the base checkpoint's trained resolution band and render the
dataset *inside* it. Supersampling is a photography habit, not a diffusion one. `[live-use]`

### 2. Step count is a separate, independent lever — and 20 is wrong

12 steps is the settled dataset render count on fineporn at cfg 1.0; 8 is also clean. 20 "over-cooked
skin into a pore grid at 2048" (`dataset/v3/README.md`) and reappeared independently on the Amy side,
where the user diagnosed it correctly: *"you can even see it on the wall actually. so it's not a skin
stipple"* (`b3b6f769`). Grain on the background is the tell that separates a step-count artefact from
a skin/freckle artefact. `[live-use]`

### 3. Textured or patterned wall wording prints its pattern onto the skin at 1024 native

New finding from the v4 native-resolution inspection (`9452f9e5`, 09-09). "White studio cyclorama"
rendered as terrazzo speckle **and the speckle appeared on the hip, thigh and torso skin**; "bare
studio" became patterned wallpaper whose cell pattern printed across abdomen and breasts; a bedroom
wallpaper printed as orange-peel on the buttocks. All three failed on **every seed** — it is the
wording, not seed luck. Every cell on a plain painted wall was clean. Fix: name a *smooth, plain
painted wall*, or reuse a setting already proven clean. `[live-use]`

### 4. A constant absence binds to the trigger exactly as a constant presence does

The reason 16 of 32 cells carry jewellery, 4 carry makeup, 3 carry a non-default hair colour, even
though the base model can draw all of them unaided. Thirty-two bare-eared, bare-necked, bare-faced,
dark-brown cells teach *"no jewellery, no makeup, dark brown"* as her. Stated in the shot list as
**"you cannot vary what you never named"** and **"caption the exception, not the rule"** (absent =
default, stays unwritten). This was the user's own question that forced the rule to be written down:
*"are those still valid, or does the model know how to do those things and we don't need to have them
in the lora?"* `[live-use]`

### 5. The v5 red-hair finding is the proof of #4, arrived at the hard way

krea2-v5 shipped with hair colour bound to the trigger. `ood_red` scored 0.36–0.41 against a spread
of 0.09–0.26 and rendered *a different woman on every rung*. Cause: 29 of 32 cells dark brown, red on
2 cells with only one face visible, and "long" hair dark on every cell. Everything else flexed fine
— platinum pixie, lab coat, leather, snow, suit, glasses, pool all held. **Only the colour broke.**

The user's fix instruction is the reusable part: *"can't we keep the same scenes as 4 but just make
her a red head, or even just more hair colours mixed in? So let's try and completely break the dark
bob association."* The first proposal — 12 extra red cells appended, taking the set to 44 — was
rejected as ballooning. The accepted design keeps **the same 32 cells** and spreads six colours with
**no majority** (dark brown 10, auburn 8, copper 4, dark blonde 4, chestnut 3, black 3), every colour
landing on a head cell, red on 11 face-visible cells across all three cuts. Same seeds, same leads,
byte-identical everything else. `[live-use]`

### 6. Eyes: "green" was not enough, and eyes cannot be captioned out of it

The v5 eye-band crops read brown at portrait size — a muted olive-hazel with an amber ring and a
heavy limbal edge; Turbo warms it further. The FACE block only said "large green eyes". Because eyes
are identity they are **never captioned**, so the *generation wording is the only lever*, and the
whole set must be re-rendered for the average to move. New wording: *"large, clear light-green eyes,
a cool natural grey-green all the way to the pupil"* — lighter and cooler, not brighter. The user's
own guardrail: *"let's not push it to hard so it's too good to be true."* `[live-use]`

### 7. Anatomy the model caps: wording is not the lever, frame area is

Eleven pubic-mound phrasings across three sweeps (plump, puffy, swollen, fat, camel toe, bulging,
plus cfg 1.5 + negative) all hit the same ceiling; extreme wordings only changed the *hair*, not the
mound. The measurement that explained it: at the trainer's 1024 bucket the region is **~52 px on a
full-length cell, ~90 px on a mid-thigh cell, ~130 px lying down, ~300 px on a navel-to-thigh crop**.
Two dedicated hip-crop cells came back full on 6/6 seeds using *the same sentence* that stayed tucked
on wide cells. So the model can draw it; it will not spend the pixels when the region is 50–90 px of
the frame.

**The user rejected the hip crops anyway** (*"I don't think the hip only shot is a good idea"*) and
declined a region-detailer pass (*"No I don't want to do anything fancy"*). Net conclusion recorded:
fineporn's ceiling is "full", not "puffy"; a genuinely prominent mons would need a different
checkpoint family. Second sweep of nine relational/geometric wordings closed it: **wording moves the
hair, not the mound** (`af2faa1`). `[live-use]`

The parallel that *did* work and is worth generalising: the areola line was found by **relational and
geometric description rather than adjectives** ("large pale areolae several times wider than her
nipples, almost the colour of her skin"), and the user credits it as the single biggest realism win.
Same technique failed on the mound because the mound is pixel-starved, not under-described.

### 8. Mirror sets are a legitimate rotation tool, and updos break profiles

A5 (right profile) took **26 renders**. Plain reseeds, a stronger far-eye clause, and even a
byte-mirrored copy of the left-profile lead all landed ~75°, 22 of 22, while A4's left-profile bob
seeds were a true 90° on 3/3. Cause isolated: **the updo. The model turns the head to show the knot.**
Fix: switch A5 to long hair, render it as a *left* profile, and flip it on assembly through a
`MIRROR` set in the recipe (verified `A5 flipped matches: True`). Recorded as "do not put an updo on
a profile cell". `[live-use]`

### 9. Breast size drifts across seeds on a byte-identical body block

B4 s708 small, s710 large; B8 s707 huge. The lever is **seed + triage against a canonical cell**, not
wording. This matters because it is the failure that looks like a prompting problem and isn't.
`[live-use]`

### 10. Recorded findings decay if you re-derive instead of re-reading

The v4 second pass looked like a regression — profiles, nipple piercings and nose rings "all broke".
The user challenged it: *"We also had a rock solid set of prompts for doing the profile, etc. It's
weird that this all broke."* Nothing had broken. The recorded wordings had simply not been re-applied:

- head-crop profile with the short gaze clause: **0/6**; the long side-view lead at
  head-and-shoulders framing: **6/6**
- "silver barbells through both nipples": renders nothing. The v1 wording *"each bar visible entering
  one side of the nipple and exiting the other"*: lands both
- straight-rear cells need the **face block removed entirely** from the prompt, or a front portrait
  comes back
- full-length crops land at ankle/knee unless the feet are named explicitly ("both feet fully inside
  the bottom edge of the frame, with floor visible beneath them")
- nose jewellery is **ignored at cfg 1** — 1 of 4 attempts landed, by luck; dropped, then found in 2
  of the shipped 32 and captioned there

The instruction added to CHARACTER.md is the durable one: *"Read this file before writing any rotation
or jewellery wording."* `[live-use]`

### 11. Caption regime, as actually shipped

32 captions, 46–78 words each, generated from `manifest.json` rather than written by hand, so the
caption cannot drift from the image. Written: framing → "a woman named zciara" → hair style and
colour → makeup where worn → pose/gaze → expression → dress state → jewellery/piercings → pubic hair
state → setting → light → "an unretouched film photograph." Never written: face, skin, freckles,
breasts, build, the mound (identity, learned from pixels). `[live-use]`

### 12. Trigger bleed is visible, not theoretical

`"a woman named zciara"` prints **"zciara" on signage and name badges** in the rendered output — the
podium shot in the v5 flexibility sheet. Options recorded: prompt around signage, or drop "named" and
use the trigger bare. `[live-use]`

### 13. The same LoRA gives a different body on each deployment checkpoint

From the user's own read of the test images (`2537e1da`): *"Turbo full-body renders her slim and
small-chested. Fineporn renders her noticeably bustier with wider hips."* Also: c2500 varies bust
size across seeds where `final` is tighter, which is what tipped the pick to `final`. Recorded as a
line for the LoRA sidecar so nobody expects one body from both deployment models. `[live-use]`

### 14. Krea 2 checkpoint identity is not portable

Turbo and Raw render **a different woman** from the same prompt — no freckles, different face. Ciara
exists only on `fineporn_v4_int8`. The proposed workaround (dressed shots on Raw, nudes on fineporn,
face-swap between) fails because **the face is exactly what differs**. `[live-use]`

### 15. cfg > 1 grains a distilled checkpoint when no LoRA is loaded

This produced a false diagnosis (cfg 1.5 + negative on a strength-0 sweep) that was then
over-retracted. Two rules came out of it, now in `characters/EVAL-DISCIPLINE.md`: reproduce a
known-good render before diagnosing, and **check the blast radius before retracting a conclusion**.
`[live-use]`

---

## Learnings — MiniMax H3 training

### 16. The headline result: a stills-only H3 LoRA does carry identity into motion

This is what `H3-PLAN.md` staged Arm 1 to test, and it passed. `ciara/h3-v1` — Amy's v16 recipe
verbatim, dataset v3 unchanged (62 stills at 1536×2688), FL2VA base, r16/α16, adamw8bit 1e-4, 1536,
3000 steps, ~3.6 s/it, ~3 h on a 5090.

Motion probe, per-frame face-embed distance over ~5 s clips (calibration real-photo p50 = 0.112):

| cell | median | worst | first→last |
|---|---|---|---|
| `t2v_lora_tq` (pure T2V, thigh-up, LoRA) | 0.200 | 0.259 | 0.196→0.259 |
| `t2v_ctrl_tq` (no LoRA) | 0.920 | 1.058 | 0.870→0.938 |
| `t2v_lora_full` (full body) | 0.324 | 0.384 | 0.356→0.384 |
| `fl_lora_tq` (Krea keyframe pinned + LoRA) | **0.171** | 0.216 | 0.167→0.172 |
| `fl_ctrl_tq` (keyframe, no LoRA) | 0.263 | 0.311 | 0.161→**0.263** |
| `fl_lora_full` | 0.227 | 0.385 | 0.250→0.202 |
| `fl_ctrl_full` | 0.334 | 0.485 | 0.289→0.426 |

Read: **pure T2V at thigh-up stays her — a first for this repo on H3.** And the LoRA's production
value is exactly the drift insurance it was hypothesised to be: with the LoRA the face holds *flat*
across 5 s (0.167→0.172) where the base drifts (0.161→0.263). Full body falls off on both, which is
the known H3 framing ceiling and not a LoRA fault. `[live-use]`

### 17. H3 stills are ~1.5× further from canon than the Krea LoRA on the same prompts

eval-A stills (length-1 T2V through `h3_graph.py`, so directly comparable with the Krea triage):

| prompt | c2250 | c2750 | c3000 | no LoRA |
|---|---|---|---|---|
| hero | 0.170 | 0.151 | 0.154 | 0.661 |
| tq | 0.355 | 0.314 | 0.326 | — |
| full | 0.341 | 0.355 | 0.349 | 0.696 |
| profile | 0.678 | 0.647 | 0.573 | — |
| ood_red | 0.562 | 0.521 | 0.497 | 0.956 |
| ood_gown | 0.340 | 0.250 | 0.330 | 0.810 |
| **median** | 0.374 | **0.315** | 0.376 | 0.736 |

Against krea2-v3's hero 0.105 / tq 0.145 / full 0.174. **c2750 is the best rung.** Prompt adherence
is strong everywhere (red hair, green sundress, gown, bob all obey) — so H3's weakness is *likeness*,
not controllability. Profile and small-face scores are called unreliable by design and judged by eye.
`[live-use]`

### 18. The eval structure that made this readable: three decks, A / H / R

- **eval-A** — stills grid, the six eval prompts × three rungs × a no-LoRA control × two seeds
  (48 cells), scored with the same face_triage calibration as the Krea run so numbers are comparable
  across model families. This cross-family comparability is the design point.
- **eval-R** — the *realism* arm: four clips isolating one lever each — turbo + film-grade lead;
  stock 30-step `simple`; stock 30-step `beta`; stock 30 `beta` + a pinned Krea keyframe.
- **eval-H** — the hoop challenge: Amy's exact hoop prompt with the trigger swapped, four variants
  (turbo+LoRA, turbo no-LoRA control, stock 30-step realism grade, pure T2V), keyframes auto-picked
  by face triage (best 0.187).

Scored by `h3eval_ciara.py {stills,motion,score}` — a per-frame face-embed sweep reporting
**median and worst frame**, and `(b)-with minus (b)-without` as the LoRA's actual production value.
`[live-use]`

### 19. Arm 2 (clips) was re-scoped in-session, and the reason changed

`H3-PLAN.md` argued for stills-first from four inferences. Live use narrowed it to one honest reason:
*"The stills LoRA already carries identity into motion, so clips aren't needed for that. What the
clips would test is the two things stills can't teach: motion-time face stability without a keyframe,
and full-body identity."* The refined spec: **10–12 gated clips, thigh-up or closer, 3 s at 73
frames, from krea2-v3 keyframes with this LoRA on, gate = worst frame under ~0.22**, restrained
motion, audio stripped. New caveat that did not exist in the plan: **the clips would be 768p while
the stills are 1536p, so a mixed set may pull face detail down on stills** — watch the hero cell, and
keep the clip count small on the first attempt. `[live-use]`

### 20. Amy's H3 ladder — the recipe map that Ciara inherited for free (`bc6b2dbd`)

Seventeen runs of one-variable-at-a-time. What settled:

- **Resolution is the likeness lever and it plateaus at 1536.** 768 unusable → 1024 → 1280 → 1536
  each strictly better; v8 at 1792 ≈ v7 at 1536.
- **Rank 32 is fatal under ai-toolkit** (v3 collapsed to random content). Diagnosed as
  de-distillation drift on a CFG-distilled base. r16 is the ceiling.
- **Every ai-toolkit run v1–v9 trained with distillation handling off *and* through a wasteful
  dequantize/requantize path.** Root cause of silent 60 GB OOM kills: `quantize: true` with no
  `qtype`. Fix: `qtype: "convrot8"`. This is a config-shape bug that produces no traceback.
- `qtype_te: nvfp4` breaks the cached-embedding path (Qwen3-VL RoPE device mismatch) → set
  `cache_text_embeddings: false`.
- **musubi's `--h3_timestep_focus_prob 0.5` is the largest single objective-side gain** (~2× faster
  convergence, default 0.0 = off); contrastive guidance fixes *adherence*, not likeness; guidance
  2.0 marginally beat 4.0. User's verdict on the whole musubi branch: *"I'm not seeing anything from
  musubi that makes me thing this is going to be meaningfully better."*
- **v16 — 15 curated images beat 73.** Dataset v9 is a strict *subset* of v7, re-selected against the
  starved coverage axes, re-developed so every image is ≥1536 (v7 had 29 of 72 under 1536, min
  336 px), and re-captioned with 8 of 15 framing terms corrected on identical pixels. Best likeness
  of the whole ladder. Which of the three changes did it was **never isolated** — worth flagging
  before anyone quotes "curate for coverage" as the lesson.
- **Full-body face weakness is not fixable by render resolution** — 2.3× more face pixels still
  yields different people. It is a training-distribution problem.
- Base H3 has a nude prior that Krea 2 Turbo lacks: h3-v1's OOD flexibility pass **passed 19/20 where
  Krea failed**. So H3 likeness is a recipe problem, not a concept problem. `[live-use]`

### 21. Two corrections the user made to H3 dataset reasoning, both generalisable

- *"surely the models play a large role here? Just because a dataset is fine for Krea doesn't mean it
  will be fine for H3."* — the inference is **asymmetric; only the negative direction is informative.**
- *"that advice seems pretty weird to me, I thought character loras were normally small?"* — retracted
  a 120–150-image recommendation; research and the skill both say 15–30 curated. `[live-use]`

---

## Learnings — H3 prompting and video craft

### 22. The `[Shot 1]` format is what stops H3 cutting to a new room — pins were a workaround for a format bug

The most valuable prompting finding in the harvest. Across three passes of the hoop piece, H3 kept
inserting cuts to different rooms (~frame 22 of a 175-frame clip; ~1 s into a 192-frame clip). The
workaround built was **hop-made end frames**: a 22–56-frame H3 micro-jump from scene N's last frame
into scene N+1's pose, take *its* last frame, pin both ends. It worked — 27 both-pinned shots, zero
cuts — and it cost one extra render per scene.

The user refused to accept it: *"I'm very confused about how you can get H3 to generate the last frame
while keeping the room stable, but you can't get H3 to generate the shot keeping the room stable"*,
then *"can you look online to see how people are handling this. It feels like a really poor work
around."*

The web sweep found the actual cause: **MiniMax's own prompt guide requires continuous footage to be
one `[Shot 1]` block with no timestamps**; a timestamp or a second shot marker *is* a cut. For
image-to-video the picture line must read `<Picture 1> remains … preserving her appearance, [the room
layout] …`, and the camera must be given in **full grammar: type + amplitude + speed**. None of the
15 prompts used that structure. The A/B: shot 5, 175 frames, **no end pin, official structure, same
seed** — held the room completely. `p.chain()` became pin-free by default; `pin_end=True` kept as
fallback. Caveat honestly recorded: n=1, and two variables moved (prompt shape *and* Turbo → stock).
`[live-use]`

### 23. Chaining doctrine the field uses, which this repo was not using

From the same sweep: **nobody chains by relaying decoded last frames.** Serious tooling chains through
the latent — Motion-Context tails, ComfyUI `AddGuide` interior anchors (0.34+), and since 2026-08-18
a masked in-place method (ComfyUI PR #15375) where the previous clip's latent is copied into the new
one and protected so the join is never regenerated. Their measured lessons:

- repeat the room and lighting paragraph **verbatim** in every shot
- **new seed per shot** — a shared seed drifts face and voice
- run a **normaliser** on the chain: texture ratchets ~1.3× per join
- use last frames only as occasional quality resets, never as the join itself
- when an end frame is genuinely wanted, make it by **image-editing the previous last frame**
  (Qwen-Image-Edit 2511 preferred for scene preservation), or from H3 itself at one frame
- references + pins in one graph is possible via a hybrid checkpoint and `minimax-h3-hybrid-cond`
  `[live-use]`

### 24. Prompted beats that trigger a cut are the prompt's fault, not the anchoring's

Scene 3 (a walk-away) inserted a ~3-second cutaway to a curtained room in **all three passes, pins or
no pins**. Rewritten so she never walks away from the lens. The generalisation: an action that gives
the model a *reason* to change angle will make it change angle, and no amount of anchoring buys it
back. `[live-use]`

### 25. Emotional and musical direction, kept light

The user's own direction on vibe is worth quoting as craft: *"it should feel natural, at home, a
playful but shy and embarrassed show off, so she starts shy and then builds in confidence… Don't
prompt it too much, just keep the guidance light and natural."* Two concrete fixes came from watching
takes: music must be named as **instrumental from a phone speaker in the room** or she reads as
lip-syncing/singing; and the recurring artefact of **a second hoop appearing around her waist** is a
prompt-level failure the user caught by eye. Shot lengths were written onto the **17n+5 lattice**
(73, 107, 141, 175, 243 frames at 24 fps) from the start. `[live-use]`

### 26. Two dialects, never mixed

The Krea keyframe render must use the **LoRA's own caption dialect** — one flowing sentence opening
"A close head-and-shoulders portrait photograph of a woman named zciara, …" closed by the realism
tail. No `[Shot 1]`, no "Picture 1 remains". The user caught this being wrong in the notebook: *"The
krea image can't use this prompt style that we use for H3."* An automated check was added
(`contains '[Shot 1]': False`). `[live-use]`

### 27. Face identity passes on video frames must be face-only

Recorded verbatim in the `krea-img2img` template's `_meta`: *"NEVER full-image identity passes on
video frames — face-only."* `[live-use]`

---

## Learnings — other models and ops

### 28. SCAIL-2, LTX, Wan — thin, but what there is

- **SCAIL-2** is the recorded answer for **source-referenced character replacement** — replacing a
  person in existing footage while following the driving motion frame for frame. H3's FL2VA
  approximates it (*"scene and identity both drifted"*); SCAIL-2 (a full fine-tune of Wan2.1-14B-I2V
  with SAM3 identity tracking) is built for it. Stack on the volume:
  `wan2.1_14B_SCAIL_2_fp8_scaled`, DPO + relight LoRAs, `lightx2v_I2V`, `umt5_xxl`,
  `sam3.1_multiplex`, `clip_vision_h`; recipe at `workflows/generation/amy-scail-replace.*`.
  **No new first-hand results in these seven sessions** — it was only ever referenced.
- **Wan 2.1 VAE** as a Krea 2 anti-softness swap: **measured to make no difference at 2048** in the
  band sweep. The softness fix it is prescribed for is a different problem from over-band crumple.
- **LTX** — nothing beyond the atlas description. `[live-use, thin]`

### 29. Ops lessons that generalise

- **`./lab up --stock`** — the studio image refuses the RunPod SSH key; the stock CUDA13 template works.
- **Gate the driver at ≥580 before installing anything.** 570.x hosts cannot run cu130 and the cu128
  fallback hits `ResolutionImpossible` against ai-toolkit's requirements. Four consecutive 5090s
  landed on the same bad host; the fix is **hold-and-reroll** — keep the dud alive so the next create
  lands elsewhere.
- **5090 availability is not guaranteed.** One evening went 5090 → RTX PRO 6000 → RTX PRO 4500
  ($0.99 → $2.09 → $0.72/hr). Pre-approve the fallback ladder rather than negotiating mid-run.
- **Serverless cannot run H3 clips.** Two different workers both lost ComfyUI mid-render (at 2 min and
  6 min) on a 124-frame job — the worker's ComfyUI dying under the job, not a one-off bad worker.
  Pods are the proven route for H3 video; serverless is fine for Krea stills and H3 keyframes.
- **Volume quota bites mid-`rsync`.** 250 GB hit during the v4/v5 sync → `Disk quota exceeded (122)`,
  broken pipe, `POSTTRAIN FAILED`. Freed every `optimizer.pt` under `training/` and superseded eval
  rungs. **Only the four eval rungs per run were synced, not the full series.** Plan quota before
  launching two arms in parallel.
- **Two ComfyUIs fight over a port.** The pod template's own instance squats 8188, answers
  `/system_stats`, has the core H3 nodes since ComfyUI 0.34, then **400s every graph** (no volume
  paths, no Motion-Context nodes) and restarts if killed. Run ours on **8189** and gate readiness on
  a **sentinel node** (`MiniMaxH3MotionContextSaveLatent`), not on an HTTP 200.
- **Kill by port, never by pattern.** `pkill -f 'main.py --listen'` killed its own SSH session (rc
  255, no output). Use `'[m]ain.py --listen'`, or resolve the PID via `ss -ltnp` and kill that.
- **`setsid … & exit 0` holds the ssh pipe open** — 70 min lost on a ComfyUI that was already serving.
  Use `setsid -f` with all fds redirected.
- **Sleep-chained Bash is blocked**; use Monitor with an `until grep -qE "DONE|Traceback"` loop, and
  stop chatty monitors once they have served their purpose.
- **Silence is never a verdict.** `runpodctl` prints a **non-breaking space (U+00A0)** between port and
  `(pub,tcp)`, silently breaking endpoint parsing; zsh does not word-split, so `S="ssh …"; $S "cmd"`
  exits 0 instantly; a stray `.safetensors` in a latent cache produced a **false DONE**. Completion
  needs positive evidence, scoped to the output dir.
- **A bare `./lab down` stops every pod, including another session's.** It did, twice; the second time
  the other pod could not restart (host reclaimed) and two training pods lost their container disks
  (**a stop wipes `/root`**). It now requires explicit pod ids or `--all`.
- **`--terminate-after` on every pod**, and a pod's auto-stop cannot be extended in place. `[live-use]`

---

## Wrong turns

Worth recording because each cost real time and each has a durable rule attached.

1. **The freckle-map diagnosis.** A full day, a research sweep, `V4-PLAN.md`, a Krea 2 Identity Edit
   pilot design and a canonical-face hunt — all built on inconsistent freckle placement. The actual
   cause was render resolution above the checkpoint's band. **Rule: before diagnosing a subtle
   artefact, verify you are inside the base model's trained resolution and step bands.**
2. **Chasing bigger canonical renders.** The 1536 hunt shipped candidates with *half the linear face
   detail* already on disk. **Rule: measure the face box before sending candidates.**
3. **Re-deriving recorded wordings** (§10) — ~40 wasted renders and a "why did this all break".
4. **cfg 1.5 on a strength-0 sweep**, then over-stating the blast radius of the retraction.
5. **The hip-crop cells.** The correct answer to a pixel-starvation problem, rejected on aesthetic
   grounds. **Rule: a cell that solves a measurement problem but that the user would not want in the
   set is not a solution.**
6. **The low-camera C1.** Knee height with hips forward gave a stout body with belly folds on 3 of 6
   seeds. Camera-angle changes are not free.
7. **Ballooning the set to fix a variable.** 12 extra red cells → rejected; redistribute, don't add.
8. **The hop machinery.** Real engineering (`Project.chain`, `h3-microjump`, per-scene hop prompts, a
   notebook UI) built around a prompt-format error, and deleted the day the format was applied.
9. **A test fixture with a hard-coded output path** overwrote three real takes with 14-byte clips, and
   `rm -f` destroyed ~314 lines of untracked tests. Both unrecoverable.

---

## User rules (verbatim)

| date | quote | force |
|---|---|---|
| 2026-09-06 | *"we can't use the lora to train the next lora"* | dataset generation is **always** at LoRA strength 0.0 |
| 2026-09-06 | *"I do think you're being over confident about the video training… we never tried to feed it generated video for amy so we have no idea what that will perform like"* | clip arm became **planned, not conditional**; inference must be labelled as inference |
| 2026-09-06 | *"the pod running is the cost, generating images, etc doesn't cost anything over and above that"* | per-render approval prompts removed; the **pod** is the gate |
| 2026-09-06 | *"that's a bug right. It should check the status, not rely on some flag that's manually set. The authorotative source is run pod."* | never trust a locally-written state flag over the provider's API |
| 2026-09-07 | *"can you look online to see how people are handling this. It feels like a really poor work around."* | a workaround that feels wrong usually is; check the field before building around it |
| 2026-09-07 | *"you keep writing a small book"* / *"again with the small book. simply?"* | be short |
| 2026-09-08 | *"We also had a rock solid set of prompts for doing the profile, etc. It's weird that this all broke."* | read the recorded findings before writing wording |
| 2026-09-09 | *"I don't think the hip only shot is a good idea. Also we haven't seem to move the size of her public mound."* | rejected the pixel-area fix |
| 2026-09-09 | *"No I don't want to do anything fancy. Can we just play with the prompts a bit more till we find something that lands? Or we accept that we're not going to win."* | prefer closing a question to escalating machinery |
| 2026-09-09 | *"We did really well with the areola and it makes a huge difference to making the character look more natural."* | relational/geometric wording is the technique that works |
| 2026-09-09 | *"we need to be able to support red hair that's a great look on her. can we rebuild the set to support that better?"* | drove dataset v5 |
| 2026-09-09 | *"ok but this just ballooning the set. can't we keep the same scenes as 4 but just make her a red head, or even just more hair colours mixed in? So let's try and completely break the dark bob association."* | redistribute, don't add |
| 2026-09-09 | *"in the test renders they were a like dark. I'd like them to read a natural Irish green. but let's not push it to hard so it's too good to be true. I'll trust your eye on that."* | realism ceiling on identity tuning |
| 2026-08-31 | *"let's just make sure we change one thing at a time so we can actually figure this out"* / *"if we're going to figure out if the trainer is better it needs to be two runs at exactly the same settings and resolution"* | one-variable discipline; fair comparisons |
| 2026-09-05 (standing) | *"let's remember to not prompt anything that should be covered by the lora (mostly face)"* — but *"use the freckle clause… It's there to help with makeup covering the freckles"* | real-person LoRAs: no face words, one deliberate exception |
| standing | every billable RunPod action stops for explicit approval; **Secure Cloud only**; always `--terminate-after` | cost gate |

---

## Numbers

| quantity | value | where |
|---|---|---|
| Dataset v4/v5 cell count | **32** | shipped |
| Bucket split | A identity-emphasis 10 · B in-context medium 11 · C in-context full 11 | V4-SHOTLIST |
| Identity ratio achieved | **0.31** (target band 0.25–0.40) | v4 |
| Cell sizes (all 1024 wide) | 1024×1024, ×1280, ×1536, ×1792 | v4 manifest |
| Dataset render settings | 12 steps, cfg 1.0, seed 707 baseline, `fineporn_v4_int8`, `wan_2.1_vae`, LoRA strength **0.0** | v4/v5 |
| Krea 2 resolution bands | Turbo **1K–2K**; Raw **1K-native** (cfg 3.5 / 52 steps) | krea-2 skill, confirmed live |
| Crumple by render size | 1024 clean · 2048 moderate · 2560 heavy (survives downscale) | 09-08 sweep |
| Step artefact | 20 steps → pore grid/hex mesh; 12 and 8 clean | v3 README + Amy |
| Face box by render size | 1536→710–846 px · 2048→1082 px · 2560→1426 px | canonical hunt |
| Pubic region at 1024 train res | full-length ~52 px · mid-thigh ~89 px · lying ~130 px · hip crop ~295 px | measured |
| Cells carrying variables | jewellery 16/32 · makeup 4 · hair colour 3 (v4) · nipple piercing 2 · nose stud 2 · pubic states 6 on 7 cells | v4 |
| v5 colour spread (planned) | dark brown 10 · auburn 8 · copper 4 · dark blonde 4 · chestnut 3 · black 3 | V5-PLAN |
| Caption length | **46–78 words**, 32 files | v4 |
| A5 profile renders to land one cell | **26** | 09-09 |
| Krea training recipe | ai-toolkit @ 5497a001, Raw base, r32/α32 (v5) or r16 (v4), adamw8bit 1e-4, res `[1024]`, bs 1, **3000 steps**, save_every 250, samples disabled, fp8 | runs |
| Steps per image | ~94 (3000/32) | v4/v5 |
| Checkpoint sizes | r16 **114 MB** · r32 **229 MB** | eval rungs |
| krea2-v5 eval-A medians (Turbo) | c1500 **0.155** · final 0.172 · c2000 0.177 · c2500 0.196 | 09-08 |
| krea2-v5 eval-B medians (fineporn) | c2500 **0.156** · c2000 0.159 · final 0.163 | 09-08 |
| krea2-v4 (r16) eval-A medians | c1500 0.164 · final 0.170 · c2500 0.180 · c2000 0.216 | 09-08 |
| krea2-v3 best (previous ship) | 0.181–0.199 | v3 |
| Hero across seeds 1–4 | 0.093–0.096 | v5 stability |
| `ood_red` (the failure) | **0.36–0.41** at every rung, both arms | v4 + v5 |
| Flexibility median (eval-C, 12 prompts) | 0.216 at both v5final and v52500; worst `flex_paint` 0.450–0.480, `flex_pixie` 0.410–0.421 | 09-09 |
| Triage calibration (Ciara) | real p50 **0.112** · p90 0.191 · max 0.270; accept ≤0.21 | `triage/rotation-01.json` |
| Krea training wall time | ~2.5 h per arm on a 5090; two arms in parallel | 09-08 |
| Krea eval render rate | ~15 s/cell on-pod (LoRA reload per rung); 64 eval-A + 30 eval-B cells per arm | 09-08 |
| Serverless Krea render | ~8–13 s warm, ~130–200 s cold | 09-08/09 |
| h3-v1 recipe | ai-toolkit @ 5497a001, `minimax_h3`, `fl2va_pruned`, `qtype: convrot8`, r16/α16, adamw8bit 1e-4, **1536**, 3000 steps, save 250, `sample_every: 100000`, layer_offloading 0.5 / TE 1.0, `cache_text_embeddings: false` | run.yaml |
| h3-v1 dataset | dataset v3 unchanged — **62 stills at 1536×2688**, prose captions | run.yaml |
| h3-v1 throughput | **3.53–3.62 s/it**, 3000 steps ≈ **3 h**, 12 checkpoints, ~$2–3 | pod log |
| h3-v1 checkpoint size | 310 MB | volume |
| H3 stills median (best rung c2750) | **0.315** vs no-LoRA 0.736 | eval-A |
| H3 motion best (FL2VA + LoRA, thigh-up) | median **0.171**, worst 0.216, drift 0.167→0.172 | eval-R/motion |
| H3 pure T2V thigh-up | median 0.200, worst 0.259 | motion |
| H3 clip render size | 768×1152, 124 frames (~5.2 s) | probes |
| H3 frame lattice | **17n+5** @ 24 fps → 39, 56, 73, 107, 124, 141, 175, 243 | `H3_LENGTHS` |
| H3 sigma shift | video 12 / audio 3 | settled |
| H3 stock path | 30 steps, Turbo LoRA strength 0, ~6 min/clip on a 5090 | eval-R |
| H3 hop lengths used | 39 f (~1.6 s) and 56 f; 31–42 s each warm, 216 s cold | chain logs |
| Amy H3 resolution ladder | 768 unusable → 1024 → 1280 → **1536 (plateau)**; 1792 ≈ 1536 | v1–v8 |
| Amy H3 dataset finding | **15 curated images (v9) beat 73 (v7)** at identical recipe | v16 |
| musubi flags | `--h3_guidance_loss_scale` 3–4 (default 0) · `--h3_guidance_loss_sigma_min` 0.15 · `--h3_timestep_focus_prob` 0.5 (default 0, ~2× convergence) · `--blocks_to_swap 24 --block_swap_h2d_only` · warmup 50 | dev branch |
| musubi throughput | 21.5 GB @1024, 4.4–4.9 s/step | v6/v9 |
| Container RAM cap on RunPod | **60 GB** cgroup (`free` reports host 123 GB) | OOM diagnosis |
| Driver gate | **≥580** for cu130 | lab up |
| Volume | `tab84u2isr`, EU-RO-1, **250 GB** (was 200), at quota 2026-09-09 | SYNC.md |
| Volume contents at quota | 177 GB models · 45 GB training · 15 GB eval rungs · 2 GB datasets | 09-09 |
| GPU prices seen | RTX 5090 $0.99/hr · RTX PRO 4500 $0.72/hr · RTX PRO 6000 $2.09/hr | 09-06 |
| Total spend, krea2-v4 + v5 | **~61 kr** (two pods, train + eval) | 09-09 |
| Krea prompt budget | ~45 words (official); dataset prompts run 243–434 words at cfg 1.0 | krea-2 skill vs practice |
