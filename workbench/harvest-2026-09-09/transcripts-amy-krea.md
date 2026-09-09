# Harvest — Amy / Krea 2 LoRA sessions (media-lab, 2026-08-31 → 2026-09-07)

Mined from 11 Claude Code session transcripts in `~/.claude/projects/-Users-ryannel-Workspace-media-lab/`.
Everything below was checked against `workflows/TRAINING-NOTES.md` and
`characters/amy/DATASET-DESIGN.md`; items already stated there are omitted or flagged as
*extends*. `[live-use]` marks a learning that came out of an actual run or an actual user
verdict, not from research or speculation.

Sessions referenced by short id:
`db8e` (08-31 pool consolidation) · `418a` (08-31 image-by-image curation) · `be09` (08-31
serverless bring-up) · `f44b` (09-01 video) · `09af` (09-03 V13 captions + train) ·
`be28` (09-04 eval-protocol design) · `de57`/`381f` (09-04 h3-v16 follow-ups) ·
`c6f6`/`ab7c` (09-05 new character) · `2cbd` (09-07, the big one: krea2-v10…v14 + synthetics).

---

## Learnings

1. **Real-photo dataset iteration on a 13–16 image set is a closed problem — four arms, one
   recipe, blind, and the *older* LoRA won every time.** krea2-v10 (dataset v14, 16 img),
   v11 (v15, 15), v12 (v16, 15), v13 (v17, 15) were each trained on v9's config byte-for-byte
   except name and dataset path, then judged blind against v6 and v9. v6 beat all four:
   10–2, 8–2, 9–1, and only v13 finally read better to the user unblinded. The conclusion
   written into `CHARACTER.md` was "real-photo curation is closed; the next arm is synthetic."
   `2cbd`, 2026-09-03. `[live-use]`

2. **The single most repeatable failure across those four arms was the three-quarter view,
   not the front.** C2 went 3-of-4 lost on v10, **0 of 6** on v11, **0 of 4** on v12. Every
   change — adding frames, removing frames, adding crops — cost the three-quarter. Front
   close-up (C1) and full body (C7) moved independently of it. Worth treating "which probe
   regressed" as the finding rather than a single likeness score. `2cbd`. `[live-use]`

3. **Adding a tighter crop of a photo already in the set double-weights that photo and shows
   up as an ageing/tanning drift.** v16 added two chest-up crops of two 2025 selfies the set
   already contained. The user's unprompted read: *"V12 is a little bit more tanned and it
   shows skin wrinkles a bit more pushing her older. I think that's the effect of the double
   2025 images."* Same mechanism as near-duplicates, but invisible to a filename or checksum
   dedup because the crop is a different file. Rule: **a crop of an existing frame is a
   duplicate, not a new coverage row.** `2cbd`, 2026-09-03. `[live-use]`

4. **Crops also teach composition.** The v16 arm's crops taught chest-centred framing, and
   the resulting v12 LoRA *cut the head off* on head-and-shoulders prompts (user: *"interesting
   that 12, a very good facial model is cutting the head off"*). Composition is learned with
   identity — this is the practical reason a character set needs the framing spread it will
   later be asked for, and it is a stronger argument than the abstract "shot size axis" in
   DATASET-DESIGN.md §5. `2cbd`. `[live-use]`

5. **Flat, front-lit, shallow-DOF portraits actively hurt.** The user removed two frames from
   v15 with the reason *"they had no dimension at all and I think might be skewing the
   training data."* v11 (which tested exactly that) recovered C1 against v10 2–0. The frames
   removed were also the only two DSLR frames in the set, so the arm is confounded — but the
   directional result held. A "dimension / modelled light" screen belongs alongside the
   resolution screen in a curation pass. `2cbd`. `[live-use]`

6. **Once the DSLR frames were gone the set was all phone JPEGs, and the LoRA started
   learning JPEG compression grain as skin past c1750.** The user's independent read on the
   v11 step grid: *"higher steps seem to bake in a bit weird skin texture."* Blind scoring
   agreed (c1750 > c2250 > final, the first unambiguous rung ladder in the project). **The
   peak checkpoint is a function of source-image quality, not just dataset size** — an
   all-phone-JPEG set peaks earlier. `2cbd`. `[live-use]`

7. **Krea 2 recipe that was never varied and never needed to be** (this is not in either doc):
   ai-toolkit @`5497a001`, LoRA **rank 32 / alpha 32**, **lr 1e-4**, resolution **1024**,
   **2500 steps**, save every 250, `qfloat8`, trained on Krea 2 **Raw**, deployed on **Turbo**.
   Rungs judged: 1750 / 2250 / final. Note the contrast with H3, where rank 32 collapses the
   model under ai-toolkit and only r16 works — the rank ceiling is model-specific, not a
   general LoRA fact. `2cbd`, `09af`. `[live-use]`

8. **"When it's so close, take the lower rung."** User rule, 2026-09-03, now in EVAL-PROTOCOL
   stage A. Rationale as recorded: fewer steps bakes in less of the set, keeps flexibility,
   and avoids the phone-JPEG skin crunch. Paired rule: **record the margin, not just the win
   count** — a 9–1 made of close calls is reported as such. Both came from the user, both
   required a tooling change (margin chips + free-text notes in the deck). `2cbd`. `[live-use]`

9. **Judge fatigue is a real, measurable limit on how much a blind deck can tell you, and the
   right response is to stop.** After ~100 blind pairs across four arms the user said *"I'm
   getting a little Amy blind"* and later *"I don't want to do the blind, I've got fatigue
   from doing those and I think I'm actually muddying things when they are this close."*
   krea2-v13 was graduated on an unblinded read with its stage-F deck deliberately left
   unscored. Mitigations adopted: a metric triage so only the top and bottom of a ranking get
   human eyes; put the next deck at least a day out; one question per screen; pairs not 1–5
   scales. `2cbd`. `[live-use]`

10. **The embedding metric was too loose to gate a dataset.** FaceNet (MTCNN +
    InceptionResnetV1/vggface2) cosine distance to the v17 real-photo centroid: p50 **0.183**,
    p90 **0.347**, max **0.418**. Synthetic cells scoring 0.145–0.31 — inside the real spread —
    were rejected on sight by the user (*"it doesn't look at all like Amy"*). The metric
    inflates on profiles and returns "no face" on chin-cropped cells. Use it to **rank and
    triage**, never to admit an image into a training set. The rule that replaced it: *no
    synthetic goes in unless the user personally reads it as her.* `2cbd`, 2026-09-05.
    `[live-use]`

11. **The trigger word is not a gate — it is redundant — and that is expected, not a bug.**
    A three-condition A/B (base + trigger; LoRA − trigger; LoRA + trigger) showed: the base
    with `zamy` gives an unrelated woman, and the LoRA *with the trigger removed* gives the
    same person as with it. Mechanism: every training image is the same subject and every
    caption carries the trigger, so the token never has to discriminate; the cheapest loss
    reduction is to move the model's generic "woman" toward the subject. Consequences: (a) a
    caption rewrite cannot make the trigger selective; (b) a multi-character scene will drag
    every woman toward the subject; (c) the only levers are **regularisation/class images**
    (other people, captioned *without* the trigger) or reduced strength at inference.
    `418a`, 2026-08-31. `[live-use]`

12. **Caption doctrine that survived all four arms** (extends DATASET-DESIGN.md, which does not
    cover captions): natural prose, not comma tags; trigger folded into a phrase (*"a woman
    named zamy"*); caption **only the residual** — framing, viewpoint, pose, expression,
    clothing, hairstyle, lighting, setting — and never intrinsic facial identity. Two
    additions that came out of real caption audits:
    - **Caption anything at the frame edge that would otherwise bind in.** A baby's head, a
      baby carrier, a hat crossing the hairline, a wall of framed photographs behind her.
    - **Caption the exception.** Makeup is named when it is unusual; the working test found
      was "if her freckles have almost completely disappeared she is probably wearing a base
      layer, so say so." Later sets also named age (born 1992) and camera/image quality
      (phone selfie, DSLR, soft, grainy) so the model does not learn JPEG artefacts as skin.
    - **Do not rewrite captions and change images in the same arm.** The v10 arm did both and
      could not attribute its C1 loss. `2cbd`, `09af`. `[live-use]`

13. **Inference-side rule 10, discovered by the user, worth more than any prompt tweak: never
    describe anything meant to be off camera.** Sweeps 23–26 kept coming out thigh-up despite
    explicit framing words; the user's diagnosis — *"You can't describe things that are meant
    to be off camera. Put the trigger in, say she's nude, then describe what's in frame"* —
    fixed it **18/18** on the next sweep. `2cbd`, 2026-09-03. `[live-use]`

14. **Rule 9: against a LoRA that learned a crop, framing words lose — give it a taller
    canvas.** v12's head-cropping was not fixed by any wording; it was fixed by rendering at
    **832×1216** instead of square. `2cbd`. `[live-use]`

15. **Rule 11: any slimness word anywhere in the prompt shrinks body features.** Across a
    73-cell single-seed churn, "slim narrow frame", "flat bony chest", "slender", "narrowing",
    "thin", "bony sternum" all reduced the target attribute and did **not** narrow the torso.
    The exception that worked was the single word **"petite" in the lead sentence** — it
    narrowed the frame at a cost of about one size notch, which was then bought back by
    stepping the size word up. `2cbd`, 2026-09-03/04. `[live-use]`

16. **Prompt wording has a hard ceiling the base model sets, and the honest move is to stop
    churning and change the lever.** Twelve wordings, clause-first ordering, repetition,
    cfg 1.5 with negatives — all landed within a shade of each other on one attribute, and a
    locked seed showed the noise was deciding it. Three levers that *did* move it: a
    **purpose-built slider LoRA** stacked after the character LoRA (13 MB, range −10…+10,
    settled at **+5**; it also pushes colour, so colour still came from seed choice); an
    **img2img pass from a reference photo** so the shape is inherited rather than described;
    and **LoRA strength** (below 0.5 the base owns shape and size words start reading
    literally). `2cbd`, 2026-09-04/05. `[live-use]`

17. **Wording must push *against* the LoRA's pull, not describe the target.** At strength 1.0
    the character LoRA pulled the body small and high, and only exaggerated wording landed on
    the reference; at strength 0.3 the *same* words read literally and overshot. So a body
    paragraph is only valid **at a stated LoRA strength** — record the strength with the
    prompt or the recipe is unreproducible. `2cbd`. `[live-use]`

18. **User rule: don't prompt anything the LoRA already owns.** Stated 2026-09-05 after face
    drift on a canon grid: *"let's remember to not prompt anything that should be covered by
    the lora (mostly face)."* Face words in the tail diluted the LoRA's own freckle and skin
    behaviour. The one deliberate exception kept was a freckle clause, retained solely so a
    makeup/foundation variation could be asked for. `2cbd`. `[live-use]`

19. **Deck UX findings from real judging sessions** (extends EVAL-PROTOCOL): undo must walk
    back to the *first* card and survive a reload (derive it from persisted scores, not an
    in-memory stack); a sideways swipe fights pan once zoomed, so **tap-to-flick A/B inside the
    fullscreen viewer** is the working gesture; pin a real reference photo on every card; and
    add free-text notes as well as flag chips, because the user's most useful signal ("very
    close", "neither strong") did not fit the chips. `be28`, `2cbd`. `[live-use]`

20. **Render the eval on the training pod before terminating it** — already in TRAINING-NOTES,
    but the *measured* delta is worth carrying: 18 stage-A cells at ~6 s each after one model
    load, zero queue, on a pod already paid for, versus a 107–494 s first-cell wait on
    serverless. `2cbd`, verified live on krea2-v13. `[live-use]`

21. **Serverless "warm" says nothing about which base is loaded.** A worker reported warm and
    the first cell still took **494 s**, because that cell needed a different checkpoint and
    paid a 12–25 GB reload. Health verdicts (warm/warming/throttled/cold) gate *capacity*, not
    *readiness*. The runtime picker built in response reads `/health`, falls back to a running
    pod only when every worker is throttled, excludes pods whose purpose is `training` and
    requires a free GPU (an earlier version sat on the training pod's tunnel), and **never
    creates a pod** — pod creation stays behind the cost gate. `2cbd`, 2026-09-03. `[live-use]`

22. **Worker VRAM floor: 24 GB is not enough for VAE encode on this stack, and it fails
    silently.** `VAEEncode` OOMs on 24 GB workers, ComfyUI falls back to tiled encode without
    an error, and the output is blocky rainbow garbage (explicit `VAEEncodeTiled` reproduces
    it). Route taken: **encode the latent locally** (a ComfyUI checkout on the Mac, torch/MPS,
    the Qwen image VAE) and upload the `.latent` to a `LoadLatent` node. Separately, one
    specific 5090 worker produced prompt-ignoring garbage nondeterministically on plain
    txt2img and had to be deleted via the REST pods endpoint; the endpoint GPU list was
    narrowed to A6000 + 4090. `2cbd`, 2026-09-05. `[live-use]`

23. **Card choice is a per-workload call, and the cheap card can be right for one job and
    wrong for the next.** For serverless stills the user picked **RTX PRO 4500** (*"cheap and
    fast and fits our workloads"*); for *training* the standing rule became *"Go 5090 or
    higher. Don't do the 4500"* after two runs fell to it and took nearly 4 h. Related trap:
    the **A100 has no fp8 units**, so on an fp8 recipe it estimates ~5 s/it at $1.39/hr —
    slower and dearer than a $0.99 5090. Check the datatype before the price. `be09`, `2cbd`.
    `[live-use]`

24. **Curation must be done by eye, image by image; programmatic dedup misses the cases that
    matter.** Consolidating 199 source files, exact-md5 and per-stem chain dedup found 23
    groups but missed 21 duplicates, because the intake pipeline had *renamed* originals to
    `subject_NN.jpg`. The fix was contact sheets → 23 suspect pairs → side-by-side matched
    face crops, judged individually. The user's instruction was explicit: *"Rather than doing
    it programmatically I think you need to look at each one."* `db8e`, 2026-08-31. `[live-use]`

25. **When choosing between an original and its repaired/upscaled twin, the answer is not
    uniform — judge each pair.** 11 pairs kept the original (the repair had smoothed away real
    freckle detail, or left a waxy face-restored look); 10 pairs kept the repair (the originals
    were blurry photos-of-a-screen with moiré, or under 800 px). Blanket "always keep the
    highest resolution" was wrong 11 times out of 21. `db8e`. `[live-use]`

26. **The user rejects on sight, fast, and the categories are consistent** — worth encoding as
    a pre-screen so a curation pass does not spend a turn on them: no dimension / flat
    lighting; near-duplicate angle already covered; visibly upscaled or compression-haloed;
    "these are all bad pictures, I don't think adding them helps"; and — for reference photos
    — *"just pretty low quality, I don't really want them in the dataset"* even when they were
    the only evidence for a body attribute. `418a`, `2cbd`. `[live-use]`

---

## Wrong turns

**The high-res rabbit hole (the headline one).** Three separate attempts to buy quality with
pixels, all of which cost time and two of which made things worse.

1. **Hi-res dataset renders at 2048.** A 62-cell synthetic set was replicated at 2048×2560 /
   2048×3008 / 1536×2304 to match a sibling character's regime. The user: *"these have a weird
   grain to them that is very uncanny valley."* The first diagnosis was **wrong**: it was
   called a freckle stipple (uniform dot size, no clustering), blamed on the subject's dense
   freckling interacting with the base model's 2048 regime, and written up as a hard limit
   with the recommendation to drop hi-res for this character entirely. Ruled out along the
   way, all on one seed: freckle wording including none at all, texture and grain words, the
   Qwen vs Wan decoder, and a Lanczos-to-2048 + LoRA img2img upscale at three denoise levels.
   The user broke it with one observation — *"you can even see it on the wall actually, so
   it's not a skin stipple"* — and the real cause was **20 steps on a distilled base
   over-iterating into mottled noise**. At 8 steps the same 2048 cell is clean on wall, hair
   and skin, and the freckles cluster naturally. A sibling session hit the same wall
   independently and landed on 12. **Lesson: when an artefact appears on the background as
   well as the subject, it is a sampler/step problem, not a content problem — check the
   background first.** `2cbd`, 2026-09-07.
2. **The 832×1216 double-pass repaint stack.** Body pass + full repaint at 0.45 + face pass at
   0.5 came back *soft, waxy and over-freckled* — and every face-pass variant at that size did
   (denoise 0.3–0.5, LoRA 0.8, Turbo unet, with and without the full pass). What fixed it was
   not more passes but **more pixels under the crop**: body pass at **1216×1792** so the face
   crop has real pixels, then **one** face pass at LoRA 1.0 / denoise 0.5 into a 1024² box, and
   no full pass at all. `2cbd`, 2026-09-05.
3. **Feeding upscaled pixels to the trainer.** On the H3 side, 8 of 15 images in dataset v9
   were re-developed via Lightroom Super Resolution (1360→2720, 1024→2048, 1365→2730) so every
   frame cleared the 1536 training bucket; the control run trained on the un-upscaled set came
   back *"mottled and waxy, the worst texture of the six."* That is the pro-upscale data point.
   Against it: 23 files in the pool sit at exactly 1536×2048 with Lightroom as the only EXIF
   software and camera make stripped — a WhatsApp-recompressed image re-exported to land
   exactly on the resolution floor, i.e. **fake detail in the freckle band**, and those were
   excluded. **The distinction that matters is whether the upscale had real detail to work
   from, not whether the number clears the floor.** Also settled: Krea 2 trains at 1024 native
   and none of this applies to it — the entire upscale exercise was an H3-only concern that
   the Krea arms inherited by habit. `418a`, `381f`.

**Reference photos as an image-to-image source.** The reference-latent pipeline (ref crop →
i2i at LoRA 0.3, denoise 0.55 → full repaint at 0.6 → background matte → face pass) did
produce the true body shape with her face — three finals. It was then abandoned, because the
user did not want low-quality reference photos in the dataset in any form and wanted the shape
*generated*. Worth knowing the pipeline exists and works; worth knowing it was not the answer
the user wanted.

**The face-pass / face-swap route, parked twice.** *"the face pass did not give us strong
results when we tried it."* At denoise 0.5 a face pass reskins the base's face structure
rather than replacing it, so identity needs 0.7+ or a fresh full-LoRA face composited — and at
that point you are back to the double-pass softness in (2). The single-pass route (LoRA at
full strength + in-frame-only prompting) beat it and became the standard.

**Pixel-space post-processing.** A script that adjusted colour in a masked region was rejected
flatly: *"No, that's ruined the image, it needs to be done via the prompt."* A related attempt
at per-region tight img2img crops hallucinated extra anatomy. Post-hoc pixel edits were dropped
as a class.

**The trigger-word investigation.** A genuinely useful A/B (learning 11) that then over-ran
into a multi-character contamination test and a regularisation-images recommendation that had
not been documented for the model in question. The user pushed back — *"this feels like we're
well off track here… are you just hallucinating?"* — and the retraction that followed is worth
recording as method: one claim ("a frozen text encoder means no caption change can make the
trigger selective") was **wrong** — a frozen encoder still emits different embeddings with and
without the token, so the DiT *can* learn to key on it given contrast. And the log quoted as
evidence came from a different trainer than the run under discussion. **Check which run a log
belongs to before quoting it as evidence.** `418a`.

**Dataset size as a lever.** Already in TRAINING-NOTES for H3 (32 → 73 bought nothing). The
Krea arms are the second, independent confirmation: every arm sat at 13–16 images and the
differences were entirely about *which* images.

**A run that moved three variables at once.** The strongest H3 result in sixteen runs (v16)
changed selection, native resolution and caption accuracy together, and could not be
attributed. It is documented in TRAINING-NOTES; repeating it here because the same trap was
re-entered on the Krea side with v10 (images + caption rewrite in one arm).

---

## User rules (verbatim)

- *"Rather than doing it programmatically I think you need to look at each one."* — 2026-08-31
- *"These are all bad pictures. I don't think adding them helps."* — 2026-08-31
- *"I removed those images because they had no dimension at all and I think might be skewing the training data."* — 2026-09-03
- *"V12 is a little bit more tanned and it shows skin wrinkles a bit more pushing her older. I think that's the effect of the double 2025 images being included."* — 2026-09-03
- *"I think the 1750 is actually the nicest. It's a bit softer, higher steps seem to bake in a bit weird skin texture."* — 2026-09-03
- *"When it's so close isn't it better to pick the lower number of steps?"* — 2026-09-03
- *"I think it's important to take into account not just the wins but also how close they were."* — 2026-09-03
- *"Done, I'll be honest I'm getting a little Amy blind now after doing this so much."* — 2026-09-03
- *"I don't want to do the blind, I've got fatigue from doing those and I think I'm actually muddying things when they are this close."* — 2026-09-03
- *"You can't describe things that are meant to be off camera. So you should put the amy trigger in, say she's nude, then describe [what's in frame]. Don't talk about anything that's meant to be off frame."* — 2026-09-03
- *"Go 5090 or higher. Don't do the 4500."* — 2026-09-03
- *"Let's just remember that we don't expect this lora to perform well for nude images, it's never seen Amy's body."* — 2026-09-03
- *"It's best if we can get good images while the lora is at full strength."* — 2026-09-05
- *"Yeah, let's remember to not prompt anything that should be covered by the lora (mostly face)."* — 2026-09-05
- *"No, that's ruined the image, it needs to be done via the prompt."* — 2026-09-04
- *"Those reference photos are just pretty low quality, I don't really want them in the dataset. So I'm hoping we can generate an image that matches."* — 2026-09-04
- *"you can even see it on the wall actually. so it's not a skin stipple."* — 2026-09-07
- *"Is this really good practice? I thought you only captioned what changed?"* — 2026-08-31
- *"No, this feels like we're well off track here. I haven't seen or read about anyone doing this. Are you just hallucinating?"* — 2026-08-31
- *"Krea is very stable across seeds for the same prompt. Let's just do different prompts."* — 2026-09-05
- *"RTX PRO 4500 is perfect I think. It's cheap and fast and fits our workloads."* — 2026-08-31 (serverless, not training)

---

## Numbers

| Thing | Value | Where |
|---|---|---|
| Source files scanned for the pool | 199 (video-generation `dataset/` + `source/`) | `db8e` |
| Pool after consolidation → after visual dedup | 30 → 101 → **71 unique** (21 dups removed, 19 in rejects) | `db8e` |
| Repaired/upscaled source sizes discarded as unusable at size | 9216×13824, 8088×12132, 7992×11988, 7660×11490, 6858×10287 (214 MB / 25 files) | `db8e` |
| Krea 2 dataset sizes | v13 **13** · v14 16 · v15 15 · v16 15 · v17 15 · v18 16 | `2cbd` |
| H3 dataset sizes | v6 32 · v7 73 · v9 **15** | `381f`, COVERAGE |
| Resolution floor screened for (H3) | short side ≥1536, never upscaled | `418a` |
| Sub-floor frames in the H3 pool | 12 of 73 under 1024; 29 of 72 under 1536; lowest 336 px | `418a`, `381f` |
| Upscale signature to reject | exactly 1536×2048, 2048 long edge (> WhatsApp's ~1600 cap), Lightroom-only EXIF, camera make stripped — 23 files | `418a` |
| Lightroom Super Resolution 2× applied (H3 v9) | 1360→2720, 1024→2048, 1365→2730 (8 of 15 frames) | `381f` |
| Krea 2 training resolution | **1024** (native; no upscaling needed) | `2cbd` |
| H3 resolution ladder | 768 unusable → 1024 → 1280 → **1536** better each step; 1792 "much the same" | TRAINING-NOTES (context) |
| Krea 2 LoRA rank / alpha | **32 / 32** (H3: 16/16; rank 32 collapses H3 under ai-toolkit) | `2cbd` |
| Krea 2 learning rate | **1e-4** | `2cbd` |
| Krea 2 total steps / save interval | **2500** / every 250 | `2cbd` |
| Rungs judged in stage A | 1750 / 2250 / final(2500) | `2cbd` |
| Shipped checkpoints | v9 c1750 · v11 c1750 · v12 c2250 · **v13 c2250 (graduated default)** · v14 c2250 | `2cbd` |
| Quantisation | `qfloat8` (Krea 2 Raw); H3 needs explicit `qtype: convrot8` | `2cbd` |
| Deployment LoRA strength | **1.0** (v6 shipped at 1.1; 1.1 tried on v9/v12) | `2cbd` |
| Body-pass LoRA strength (repaint stack) | **0.3** | `2cbd` |
| Face-pass settings (settled) | LoRA **1.0**, denoise **0.5**, crop box 257,0,959,702 → 1024² | `2cbd` |
| Face-pass settings (rejected as soft/waxy) | LoRA 0.85, denoise 0.45, at 832×1216; also 0.3–0.5 @ LoRA 0.8 | `2cbd` |
| Body pass resolution (settled) | **1216×1792** (832×1216 was the failure) | `2cbd` |
| Reference img2img denoise sweep | 0.55 / 0.70 / 0.85; settled pipeline 0.55 then full repaint 0.6 | `2cbd` |
| Full-repaint denoise tried | 0.45 (too soft), 0.6 (settled) | `2cbd` |
| Slider LoRA (stacked after character LoRA) | 13 MB, range −10…+10, tried +3…+8, **settled +5** | `2cbd` |
| Turbo render defaults | 8 steps, cfg 1.0, euler/simple, 1024² (or 832×1216 / 768×1344 for tall) | probes.md, `2cbd` |
| Hi-res render steps | **20 = mottled grain**; 8 clean; 12 is the sibling session's pick | `2cbd` |
| Hi-res cell sizes used | 2048×2560, 2048×3008, 1536×2304, 1536×2688 | `2cbd` |
| Stipple/grain by resolution | 2048 worst, 1536 slightly less, 1024 correct (before the step-count fix) | `2cbd` |
| cfg for body rows at hi-res | **1.5** + negative + face guard (vs 1.0 for head rows) | `2cbd` |
| Dataset-generation cfg (from research) | 1.5–2.5, never Turbo's 1.0 | DATASET-DESIGN (context) |
| Blind result — v10 vs v6 (24 pairs) | v6 0.83 · v10 0.42 · v9 0.33; head-to-head v6 10–2 | `2cbd` |
| Blind result — v11 (30 pairs) | v6 0.80 · v10 0.55 · v9 0.45 · v11 0.40; C2 **0/6** | `2cbd` |
| Blind result — v12 (20 pairs) | v6 0.90 · v9 0.70 · v12 0.20; C2 **0/4**, C1 0–1–3 | `2cbd` |
| Blind result — v13 | stage A c2250 2–0; stage F deliberately unscored, graduated on user read | `2cbd` |
| Decisions per full protocol run | ~45 (grids on arm stages) / 90–120 cells | EVAL-PROTOCOL |
| FaceNet triage calibration (real photos) | p50 **0.183**, p90 **0.347**, max **0.418** | `2cbd` |
| Triage on final synthetic rotation | 17/18 in 0.129–0.31; rear cell 0.641 (dropped); clothed 10/12 at 0.145–0.39 | `2cbd` |
| 5090 training throughput | **2.93–2.97 s/it**, 2500 steps in **2h02m**, $0.99/hr → ~$2.05–2.30 | `2cbd` |
| RTX PRO 4500 | **5.5 s/it**, 3h49m, $0.72/hr → ~$2.75–2.95 | `2cbd` |
| RTX PRO 6000 WK / B200 / A100 PCIe | $1.89 ~1h45m est · $6.79 ~55m est · $1.39 ~3.5h (no fp8 — avoid) | `2cbd` |
| VRAM used during Krea 2 training | 18.5–19.2 GB | `2cbd` |
| Serverless first-cell latency | 107–414 s typical; **494 s** on a base switch (12–25 GB reload) | `2cbd` |
| Serverless steady-state | ~7 s/cell; on-pod ~6 s/cell after one model load | `2cbd` |
| Worker VRAM floor | 24 GB **insufficient** for VAE encode → silent tiled fallback → garbage | `2cbd` |
| Endpoint GPU list after the flaky-worker incident | A6000 + 4090 (5090 removed) | `2cbd` |
| Cost — four Krea arms (v10–v13) | ≈ **$10** total plus serverless cents | `2cbd` |
| Cost — krea2-v14 | ~$4 (hit the 4 h auto-stop after an on-pod eval failed) vs $2.30 quoted | `2cbd` |
| Prompt-churn iteration counts | 73 single-edit cells on one locked seed (c01–c73); 12–20 per attribute round | `2cbd` |

---

## Two things to reconcile before this is written into a skill

1. **The synthetic cap contradicts itself across the fortnight.** `DATASET-DESIGN.md` (08-27)
   sets a **hard cap of ~10 %** synthetic and "never generate training data from our own Amy
   LoRA — that is self-consumption in the same lineage." By 09-05 the working rule for dataset
   v18 was **≤40 % synthetic**, generated by the project's own krea2-v13, and by 09-07 the
   user's stated direction was *"the best and most flexible LoRA we can build is going to be
   almost entirely synthetic."* The empirical driver is real: v6, whose set carries synthetic
   body coverage, beat four real-photo arms blind. Whichever way this resolves, the 10 % cap as
   written is no longer the operating rule and the doc should say so.
2. **The dataset-generation cfg rule (1.5–2.5) and the hi-res step finding both point at the
   same underlying knob** — how hard the sampler is driven — and both were discovered by
   noticing texture artefacts. Worth stating once as "sampler settings for images destined for
   a dataset are not the same as for images that are only ever looked at", with cfg and step
   count as the two levers.
