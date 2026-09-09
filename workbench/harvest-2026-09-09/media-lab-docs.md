# Harvest — media-lab LoRA-training learnings (2026-09-09)

Source: `/Users/ryannel/Workspace/media-lab` (read-only). Covers 16 Amy Krea 2 runs, 17 Amy H3
runs, 5 Ciara Krea 2 runs and 1 Ciara H3 run, plus the dataset ladder v1→v21 (Amy) and v1→v5
(Ciara). Every rule below is `[live-use]` — first-hand, on rented hardware, with a named run and
date. Nothing here is community-sourced unless it says so.

**Two things to know before reading.** First, the two characters are different experiments: **Amy
is a real person with a real photo pool**, so her ladder is about curating scarce real images;
**Ciara is fully synthetic**, so her ladder is about generating a dataset and is where the
resolution rabbit hole lives. Second, most of the Amy Krea 2 ladder (v9→v13) is a *negative*
result series — four dataset arms that lost to an incumbent — and the negatives are the valuable
part.

---

## Settled rules

### Dataset curation

**R1. Coverage, not count. Image count is definitively not the lever.** `[live-use]`
Three independent arms. Krea 2: v1 (25 images) beat v4 (74, a strict *superset* of itself) on the
5-model × 5-seed blind face re-probe, 2026-08-27 ("X is the dominant winner" = v1-1750). H3:
h3-v14 took dataset v6 (32) to v7 (73), byte-identical otherwise at 1536, and likeness landed in
the same place — *"faces are kinda ok … bodies are all over the place"* (2026-08-30). Krea 2
again: krea2-v8 used 15 coverage-built images against v6's 32 and came out "very close".
Working band: **15–32 for a real-photo set**, 30–35 named as diminishing returns.

**R2. Capacity and training length are exhausted as levers before the dataset is.** `[live-use]`
krea2-v2 moved rank 32→64 and steps 2250→3000 on the identical dataset v1. The blind Turbo grid
(11 cells, v1's winner hidden as a control) put **the v1 control first**, and every 0.6/0.8 cell
was *"not even the same person"* (2026-08-26). Mid-run at step 1500 the user confirmed rank 64
did improve *facial shape* — the change was real, it just did not convert into identity.

**R3. Whatever never varies becomes part of the identity, and the starved axes are countable.**
`[live-use]` Audit of Amy's 73-image pool (COVERAGE.md, 2026-08-30): rotation front 41 / ¾ 23 /
profile 6 / rear 3; elevation above 5, **below 0**; expression neutral 8 / smile 52; lighting
daylight 41 / studio 4; body refs frontal only. The probes sat in exactly that corner, so
*"some measured weak likeness is distribution mismatch, not model capability."* Confirmed
downstream: krea2-v9 stage B scored **C3 strict profile 0/5 across every seed** — the set's only
profile was one bobble-hat frame.

**R4. Identity ratio ~0.33, but absolute close-up count matters too.** `[live-use]` Measured
close-up share against outcome: v1 **56% → best faces, weak bodies, refuses nudity**; v6 43% →
between; v5 **32% → best bodies, face fails on tight crop**. Both published failure modes
reproduced. Our caveat: *"v5 sits inside the 0.25–0.40 tolerance band yet still has weak
close-ups, so absolute count matters too (v5 has 9 close-ups, v1 has 14). Treat 0.33 as
necessary, not sufficient."*

**R5. Identity is learned per face-scale.** `[live-use]` Amy CHARACTER.md, 2026-08-27, across
three trained datasets: v5 (39% full-body) produced faces that read strongly *inside a full-body
shot* while ranking worst on the close-up probe; v1 (56% close-up) inverted. The user noticed it
twice independently before it was written down. *"This reframes the 'face likeness ceiling'. It
is not a ceiling — earlier runs varied image count, era span, rank and steps, none of which touch
face scale."*

**R6. A second crop of a photo already in the set is not free coverage — it teaches a framing.**
`[live-use]` krea2-v12 (dataset v16) added two chest-up crops of photos already present, lost
C1/C2, and *"v12's crops taught a chest-centred frame that cut heads off on nude waist-ups
(sweep 24); v13 has no such crops."*

**R7. Era-narrowing does not fix a drifting identity; nude-reference density does fix nudity
adherence.** `[live-use]` krea2-v5 narrowed v1's 2017→2025 span to one 24-month window (28
images). Blind pass 2026-08-27: **no v5 cell placed on faces at all**, confirmed by the 5-seed
re-probe. Hypothesis closed. What v5 won was anatomy, and the mechanism was compositional: real
nude references were ~21% of its 28 images vs ~8% of v4's 74. Adherence tracked density —
**v1 @ 8% refuses · v4 @ 13.5% 2/8 nude · v6 @ 28% partial · v5 @ 32% 4/8 + 1 underwear.**

**R8. Near-duplicate anchors and flat light are separate defects; removing them trades one probe
for another.** `[live-use]` dataset v15 removed the two near-duplicate DSLR frontals — the
sharpest files in the set — because they had *"no dimension at all: flat, even front light with
no shadow shaping the face"*. krea2-v11: the close **front** face came part-way back (C1 3–3,
beat v10 2–0) but **C2 three-quarter collapsed 0/6**. *"The DSC portraits carried real front-lit
structure that C2 apparently drew on too."*

**R9. The three-quarter view is the canary.** `[live-use]` Across four real-photo arms on one
recipe and one judge, **every change to dataset v13 lost C2 0/N** (v11 0/6, v12 0/4) while v9 wins
it every time. C2 is also where an over-trained rung collapses first (krea2-v9: c2500 goes 0 wins
/ 4 losses on C2 alone).

**R10. Dataset versions are immutable once a run references them.** `[live-use]` Enforced after
v13 was edited in place post-run and became v14; v13 had to be reconstructed and **sha256-verified
file-by-file against the as-trained copy on the volume** (2026-09-03, all 26 files identical). One
reconstructed caption had already leaked into v16, so krea2-v12 trained on a caption that was
never the real one.

### Resolution — the high-res rabbit hole

**R11. For a 1024-bucket LoRA, render the dataset at 1024 native. Hi-res-then-downscale is what
causes the reticulated "scale" skin.** `[live-use]` The most expensive finding in the repo (a full
day, Ciara CHARACTER.md §10, 2026-09-08). Measured on fineporn, seed 88, 12 steps cfg 1, cheek
patches sized as a fixed fraction of inter-eye distance so every resolution shows the same skin:
**1024×1280 native is clean** (discrete freckles); **2048 moderately crumpled, 2560 heavily**; and
**the crumple survives the downscale** — at the 1024 the trainer sees, 2048→1024 and 2560→1024 are
both speckled while 1024-native is clean. **Not the VAE** (Wan 2.1 and Qwen Image decode to
identical texture at 2048). Confirmed by training: krea2-v4 (r16) and krea2-v5 (r32) on the
1024-native dataset v4 showed **no reticulated skin on fineporn at 1024 or 1344 at any rung of
either arm** (2026-09-09), and `final` no longer overtrains. *"The 'scale' was the hi-res sources
and the per-image freckle re-roll, not rank."*

**Three resolutions must be kept apart** — the repo conflated them for a week:

| | Ciara (Krea 2) | Amy (H3) |
|---|---|---|
| Dataset source render | **1024×1280 native** (v4); v2/v3 at 2048/1536 produced the artefact | ≥1536 short side, never upscaled |
| Training bucket | 1024 (Krea 2 trained at 256/512/1024 only) | 1536 |
| Deploy render | Turbo 1024–2048; fineporn **1024×1536 unusable**, ≥1344×2016 good | H3 stills 0.9–1.0 MP |

**R12. On H3, training resolution is the dominant likeness lever up to 1536, then it plateaus.**
`[live-use]` One variable per run, dataset v6 held: **768 unusable (h3-v1) → 1024 large
consistency win (h3-v2) → 1280 clearly better (h3-v5) → 1536 stronger still (h3-v7) → 1792 "much
the same" (h3-v8)**, user-judged 2026-08-29/30. 1536 ≈ the dataset's native pixels (17 of 32
sources are exactly 1536×2048); higher means upscaled data, a dataset experiment.

**R13. Sub-training-resolution sources teach softness; upscale externally, not in the trainer.**
`[live-use]` dataset v7 had **29 of 72 images with a short edge below 1536, some as low as
336 px**. dataset v9 re-developed 8 of 15 sources at 2× (1360→2720, 1024→2048, 1365→2730) so all
clear 1536, which let `bucket_no_upscale = true` be set. Checked at 100% before acceptance: real
captures gained genuine eyelash separation with no ringing.

**R14. Source render step count trains in as texture.** `[live-use]` At 2048, **20 steps
over-cooks skin into a harsh pore grid; 12 gives real natural skin; 8 is a touch soft.** Ciara
krea2-v2 (62 hi-res sources at 20 steps) trained a fine speckle in; krea2-v3 (identical 62 cells,
only the render step count changed to 12) did not, and won every in-distribution prompt (all-cell
triage median **0.199 vs 0.232 / 0.227**). A *source-render* setting, invisible on contact sheets.

**R15. Upscale + img2img is not a substitute for a fresh render.** `[live-use]` Every img2img
variant over an upscaled latent — Lanczos or 4xNomos input, Wan or Qwen decode, with or without
pore/grain words, denoise 0.25–0.50 — left the same mottled speckle. Recorded counter-fact: a
fresh 2048 draw moved the face **0.16** from its 1024 original while the upscale pass moved it
0.08–0.11, so upscaling is better for *identity stability* and worse for *texture*. On R11 the
question is moot.

### Steps, rank, checkpoint selection

**R16. One Krea 2 recipe held unchanged across nine runs and two characters.** `[live-use]`
ai-toolkit on **Krea 2 Raw, LoRA r32/alpha 32, adamw8bit, LR 1e-4, resolution [1024], batch 1,
qfloat8, `low_vram: false`, `cache_text_embeddings: true`, `caption_dropout_rate 0.05`,
`save_every 250`, samples disabled.** Steps scale with entries: ~90–170 per image (2250 on 25,
2500 on 13–16, 3000 on 32, 3500 on 54–91).

**R17. Rank 32 beats rank 16 on Krea 2, slightly — and rank is not the fix for a texture
artefact.** `[live-use]` Ciara krea2-v4 (r16) vs krea2-v5 (r32), same dataset v4, same 3000 steps,
two 5090 pods in parallel, 2026-09-09: **v5 wins every table** (Turbo median 0.155–0.196 vs
0.164–0.216; fineporn 0.156–0.163 vs 0.167–0.186) and holds strict profiles 4/4 vs 2/4. Skin was
equally clean on both, which is what proved the rank cut had not removed the v3 artefact.

**R18. Rank 32 destroys H3 under ai-toolkit. r16 only.** `[live-use]` h3-v3 (768, r32/a32,
otherwise identical to h3-v1) collapsed: adherence destroyed at every checkpoint — random text
pages, objects and scenes instead of the probe. Capacity de-distilled the CFG-distilled base under
naive training, the failure musubi's guidance-distillation protection exists for.

**R19. The rung is per-dataset, and ties break downward.** `[live-use]` Measured peaks: krea2-v1
c1750/2250; v5 c2750/3000; **v9 c1750/2500** (2500 collapses C2, 1250 undercooks C1); v11 c1750
(clean monotone 1750 > 2250 > 2500); v12 and v13 **c2250/2500**; v15 `final` (3500); Ciara v5
`final` (3000) with c2500 equivalent. User rule, EVAL-PROTOCOL 2026-09-03: **when the grid cannot
separate two rungs, take the LOWER one** — fewer steps bakes in less of the set. If it matters,
carry both into the head-to-head.

**R20. Past the peak, the *source medium* bakes in, not just the identity.** `[live-use]`
krea2-v11's set is 15 phone JPEGs with the DSLR frames removed; user, unblinded: *"the 1750 is
actually the nicest… higher steps seem to bake in a bit weird skin texture."* A set with more
views of the same photos tolerates more steps (v12/v13 peaked a rung later at 2250).

**R21. Deployment strength 1.0 on both models; a monotone rise to 1.1 is an underfit signature,
not a setting.** `[live-use]` H3: 1.0, with 0.7/0.85 worse on the v7 sweep. Krea 2 early runs
shipped at 1.1, correctly read as *"needing above-normal strength to assert identity is the
weak-likeness signature, and it means there is effectively no stacking headroom."* Later,
better-fit runs (v9, v13, Ciara v5) ship at **1.0**. On fineporn the band is 1.0–1.1: *"0.7 face
clearly not her; 0.9 sort of there; I wouldn't go below 1."*

### Captioning

**R22. Caption what the image shows, not what the prompt asked for.** `[live-use]` Ciara's
`manifest.json` records per-cell what each picked render actually contains (nose stud landed,
barbell did not, "full" makeup left the freckles visible, two cells framed to thigh despite "head
to feet"), and captions generate from that. Recorded as **"The prompt is not the image."**

**R23. The pre-krea2-v8 caption audit is the model of what one catches.** `[live-use]`
(dataset v8, 2026-08-30) — framing terms on all four body cells (`full body nude` →
`three-quarter length nude cropped at the knees`); an uncaptioned tongue-out expression (*"the
highest-cost error in the set"*); an unnamed low camera angle on the set's **only**
below-eye-level frame, which would otherwise have bound the low angle to the open-mouth laugh
sharing it; indoor/outdoor and backdrop-colour errors; `blonde` → `strawberry blonde`. Two earlier
flags were **withdrawn as wrong** — the audit can over-correct.

**R24. Naming a trait can make it a prompt variable that fights the LoRA while still failing to
become promptable.** `[live-use]` dataset v18 captioned **age** ("aged N") and **freckle density**
on every real photo. Verdict after krea2-v14 (2026-09-06): *"age wording did not become
promptable, and naming freckle density made freckles a prompt variable that fights the LoRA."*
Both stripped for v19–v21 — **no age, no freckle words, no fine-line words in any caption** — and
left to bind to the trigger. Foundation is still captioned as plain makeup, with **no mention of
what it hides**; the model learns the lighter freckling from the image.

**R25. Hair colour and length DO become promptable when captioned.** `[live-use]` krea2-v13 could
not be prompted off light-brown shoulder-length hair. The v14 flex probe at the same seeds
(2026-09-05): **"auburn" renders auburn, "dark-brown" darker, "dark-blonde" lighter, the bob is a
bob, "long" reaches past the shoulders** — where v13 gave light brown for all of them. Stated
cost: prompts must name hair from then on.

**R26. A colour majority binds to the trigger.** `[live-use]` Ciara, 2026-09-09: `ood_red` renders
a *different woman* on every rung of v4 and v5 (triage 0.36, the only prompt outside the spread),
while platinum pixie, lab coat and leather all hold. Dataset v4 had red on 2 of 32 cells. Fix is a
spread with **no majority** (dark brown 10 / auburn 8 / copper 4 / dark blonde 4 / chestnut 3 /
black 3) so *"the LoRA sees one face under six captioned colours and cannot bind any of them."*

**R27. Trigger dialect: `z<name>` folded into prose; `cache_text_embeddings: true` is safe only
because the trigger is literal in the `.txt` sidecars.** `[live-use]` Used unchanged on Krea 2 and
H3 — the H3 runs read the same sidecars the Krea runs used, with no re-captioning. Two caption
experiments were built and **deliberately never trained**: dataset v10 (H3's canonical
`integrated_multimodal_description` / `overall_soundscape` fields) and v11 (bare `[trigger]`,
class noun dropped), both retained as provenance with their rationale marked an overreach. Known
bleed on Ciara v5: *"a woman named zciara"* prints the trigger on signage and name badges.

**R28. No face words in the prompt at inference — for two separate reasons.** `[live-use]`
(a) On full-length cells *"the long face description claims the frame"*: the "camera stepped back"
lead, feet and floor named, and a six-metre distance all still cropped at the shins until the face
block was trimmed to one sentence. (b) Prompt length drives the reticulated skin at render time —
the same three ideas at **~95 words** render freckles as a reptile-scale pattern; at **~45 words**
the skin is clean, verified across seeds 42/7/707/1234. *"One clause per idea."* And **never
re-add a base-model realism tail** ("distinct film grain texture, visible pores, fine peach fuzz")
over a LoRA render — it doses skin the LoRA already carries. `"an unretouched film photograph."`
is the whole tail.

### Synthetic data

**R29. The literature cap is ~10%; the measured failure is at 64%.** `[live-use] + [research]`
DATASET-DESIGN §1 sets a hard cap **under 10%**, from the chain-of-diffusion study (arXiv
2407.17493 — LoRA-finetuning on own output tripled FID over 6 iterations; 10% synthetic is enough
to degrade; 50% real "rarely slows the degradation") and its replication (2311.12202 — diversity
collapse precedes quality collapse). It calibrates honestly: at iteration 1–2 the effect is mild,
and v5 (14% synthetic) was the strongest model at the time. **The measured failure is dataset v19
— 56 synthetic of 88 entries (64%), krea2-v15.** User, 2026-09-06: *"The face looks off at higher
strength and the face doesn't hold on the full body nudes or even the half body."* Diagnosis:
56/88 entries carried v14's *rendering* of her face, weakest at small scale, and training
amplified it. **Body learned, face regressed.**
> The "≤40%" figure in the brief is **not** in these documents. What is documented is a <10%
> literature cap, an uneventful 12–14%, and a measured failure at 64%.

**R30. Three rules keep seeding safe, each confirmed by a failure.** `[live-use]` (a) **Never
generate training data from the character's own LoRA in the same lineage** — Ciara's dataset is
generated at **LoRA strength 0.0** on the base model, which is what makes it a clean source; the
proposal to train the next LoRA on the previous one's output was raised and correctly rejected.
(b) **Vary everything the synthetics share** — v19's 56 cells shared one seed, one camera sentence
and one soft studio look, so the LoRA learned v14's rendering *as* the face; v20 kept the scaffold
and changed what was uniform (12 place+light scenes, a per-cell seed, six camera styles).
(c) **No synthetic where a real photo does the job** — v19 dropped nine cells duplicating real
coverage.

**R31. Face triage is calibrated leave-one-out on real references, and it is a screen.**
`[live-use]` Amy `triage/v17.json`: 15 real faces, leave-one-out **p50 0.183, p90 0.347, max
0.418**; anchors — good finals 0.13–0.19, a LoRA-0.7 body render 0.27, an actual 2019 reference
photo 0.30, LoRA-0.3 body 0.50, LoRA-0 0.80. Ciara `triage/rotation-01.json`: 9 face-visible
rotation cells, **p50 0.112, p90 0.191, max 0.270**; inside p90 is her. Two measured blind spots:
**profiles score high regardless** (half a face — judge by eye), and the metric **is not sensitive
enough at half/full-body face scale to be trusted for a ship call** — on krea2-v15 it said v15 ≤
v14 on 5 of 6 probes and the user failed the run.

**R32. The repaint stack gets the real identity back onto a synthetic body.** `[live-use]`
Settled 2026-09-05 after the 832×1216 version came back soft, waxy and over-freckled in every
variant: **body pass at 1216×1792 with the LoRA at 0.3** (the base owns the shape and size words
work again; below 0.5 the face is no longer her), then **one** face pass (`facerepaint-02` prompt,
LoRA 1.0, denoise 0.5, box 257,0,959,702 → 1024²), **no full pass**. Denoise 0.30 is too timid,
0.6+ drifts the hair, and chaining several 0.5 passes drifts rounder each step. Both img2img
passes VAE-encode locally and upload a `.latent`, because worker-side `VAEEncode` and FaceDetailer
are unreliable on the endpoint.

### Evaluation discipline

**R33. Grep every probe against the caption corpus before trusting it.** `[live-use]` The most
damaging methodological error in the repo. The body probe used through v4/v5/v6 read *"full body
nude, standing, front view, arms relaxed at her sides, plain grey studio backdrop, even soft
lighting"*; training image `z-image-turbo_00064_`'s caption reads *"full body nude, front view,
standing with arms relaxed at her sides against a plain grey studio backdrop, even soft studio
lighting"* — **near-verbatim**. It measured **recall**, and it inverted a headline: "nude
compliance rises monotonically with steps (2250: 1/3 → 3000: 2/3)" was **memorisation deepening**.
krea2-v7, an 8000-step ladder built on that premise, was killed at step 170 for ~$0.30.

**R34. Five design rules for a judgeable probe.** `[live-use]` From the C1–C8 rebuild,
2026-08-31: (1) the face must be **>~15% of frame height** or you are testing framing, not
identity; (2) the body must be upright and side-on — lying or foreshortened poses cannot be read
for anatomy; (3) never paraphrase a training caption; (4) **stay photographic** — OOD should mean
unfamiliar setting or light, not an unfamiliar medium, because an oil-painting probe abstracts the
face until no identity call is possible; (5) nude probes need the NSFW base or they measure
censorship. Plus: **standing-figure probes render at 768×1344, not 1024²** — the first square test
complied with the nude prompt and cropped her head off at the neck.

**R35. Blind, paired, one decision per screen — not 1–5 scoring.** `[live-use]` **Pairs** (same
probe, same seed, tap to flick A↔B, then *A more her / Same / B more her*) for any stage with
arms; **grids** (arms as columns, one decision per arm pair rather than per cell) for step,
strength and render-surface stages; **gates** (*Her / Close / Not her* plus leak and fault chips)
for single cells. With grids on the arm stages a full run is ~45 decisions. A real reference photo
stays pinned on every card, and the fullscreen viewer flicks A/B **while keeping zoom and pan** so
the same patch of face is compared.

**R36. Record the margin, not just the win.** `[live-use]` User rule 2026-09-03: *"take into
account not just the wins but how close they were."* Two chips (*close call*, *neither strong*)
save with each pick and the scorer prints a Margin table splitting wins into clear and close.
Worked example: v6 beat v12 **9–1**, but both C7 pairs were "very close", a C6 "neither
particularly strong" and three C4/C6 pairs "neither" — *"9–1 overstates v6's lead."*

**R37. Judge fatigue bounds how many decks you can run.** `[live-use]` After four decks in two
days the judge reported *"getting a little Amy blind"* (krea2-v11, 2026-09-03), and krea2-v13's
stage F was 30 pairs published but **never scored** for the same reason — the ship call was made
on an unblinded read. This is the argument for triage as a pre-screen (rank cells so the human
judges the top and bottom, not the middle) and for grids over per-cell pairs.

**R38. The A–F stage ladder: each stage fixes its variable for every stage after it, and no later
stage runs on more than the survivors.** `[live-use]` A **step and strength** (~36–54 cells: 3
probes × 3 rungs × 3 strengths × 2 seeds) → B **stability** (~15: 5 seeds on the winner) → C
**flexibility** (~8–12: OOD plus the run's own starved axes) → D **nudity stack** (~9–12 over the
NSFW checkpoint, **plus one cell at strength 0**) → E **render surface** → F **blind head-to-head
vs the incumbent at its own shipped settings**. 90–120 cells, a few dollars. Ship rule: wins
likeness on C1/C2 **and** does not lose C7 or D.

**R39. Reproduce the known-good render before forming a hypothesis, and keep a strength-0 control
in every comparison.** `[live-use]` EVAL-DISCIPLINE, 2026-09-07, written after a lost day. The
decisive fact — that the freckle clumping originates in the *base model* — came from a no-LoRA
render that *"should have been the second image made, not the twentieth."* And: an artefact that
appears on the **background** as well as the skin is a sampling artefact, not something a
character LoRA learned.

**R40. Sidecar every render including throwaways; `cells.json` beats the plan file.** `[live-use]`
A recipe JSON holds several variants — Ciara's `canon-25.json` has a variant "c" at cfg 1.5 with a
negative and a 462-word prompt, reserved for the body rows, while **the 60 good dataset cells used
cfg 1.0, 8 steps, no negative and a 249-word prompt**. Taking variant "c" as "the recipe" produced
grain that was then blamed on the LoRA and the checkpoint. Corollary: **enumerate exactly which
artefacts an error touched before retracting anything** — the cfg-1.5 mistake was announced as
contaminating "much of the day's work"; one grep showed **two** tests.

**R41. Evaluate on the checkpoint and resolution you will deploy on.** `[live-use]` Ciara
krea2-v3 was trained on Raw, evaluated **only on Turbo**, and shipped `final` — while `run.yaml`
named fineporn as a deploy target. Measured later: fineporn at **1024×1536 is unusable** (cheeks
break up) and **LoRA strength is not the lever** (1.0/0.85/0.70/0.55 all bad); fineporn at
**≥1344×2016 is good**; `krea2_raw` is a speckled posterised mess even at 52 steps / cfg 3.5. And
**c2500 was the only rung that survived the hardest case**, where the Turbo-only eval had picked
`final`. The v4/v5 matrix became **{Turbo, fineporn} × {1024, 1344+} × ≥2 seeds at cfg 1.0 with a
strength-0 control.**

**R42. cfg > 1 on a guidance-distilled checkpoint is a grain source with no LoRA loaded.**
`[live-use]` Verified no-LoRA at seed 707: cfg 1.0 at 8 and 12 steps clean, cfg 1.5 with or
without a negative grainy, and the grain covers the background. The deliberate exception:
**face-hidden body cells (135°, rear) may run cfg 1.5 with a negative freely**, and face-visible
body cells only with a face guard, because mass words (bottom, thighs, muscle) do not move at cfg
1.0 on this base.

**R43. A blank or flat cell is a checkpoint fault, not a renderer fault.** `[live-use]` h3-v14
c2250, face probe, seed 1234: all 5 decoded frames flat (per-frame stddev ~2 against ~50 for every
other face cell), while the same seed at 2750/3000 is fine. One cell in 36. Measure per-frame
stddev before blaming the renderer.

### Operations worth generalising

**R44. Silent-failure catalogue — the recurring shape is treating "the command returned" as
evidence something started.** `[live-use]` Inline `ssh 'nohup bash -c "…"'` chains **fail
silently** (three times: v4, v7, v8) — write the setup script to a file with `set -euo pipefail`
and **phase banner echoes**, `setsid -f` it, then verify within one minute by `head`ing for the
banner **and** `pgrep`ing. **A process check must name an artefact unique to this run**: a bare
`[r]un.py` matched ComfyUI's own `run.py`, h3-v16's launch was declared good and never trained,
and an hour of 5090 time was lost. **A stray `.safetensors` reads as DONE** — dataset latent
caches are `.safetensors` too, so scope the completion check to the trainer's output dir.
**zsh does not word-split unquoted variables**, so `S="ssh …"; $S "cmd"` fails instantly and an
`until` guard reads it as "training finished". **`pkill -f` kills its own ssh session** when the
pattern matches the command line carrying it — kill by **port**, not by pattern. And **a Monitor
event is a nudge to go and look, never the current state** (one delivered a 4-hour-stale step
count despite `--line-buffered`).

**R45. Boot training pods on the stock template, gate the driver, and use cu130.** `[live-use]`
The serverless studio image does not take the RunPod ssh key (`Permission denied (publickey)` on a
RUNNING pod with a published 22/tcp port); **every successful krea2/h3 run used `--stock`**
(RunPod's CUDA13 template). **Gate on `nvidia-smi` driver ≥ 580.x before installing anything** — a
570.x host gives `driver too old (found 12080)`, and cu128 is not a fallback because ai-toolkit's
requirements are unresolvable against the cu128 index. Four 5090 pods in a row landed on one bad
host; the fix is **hold-and-reroll** (keep the dud running so the next create cannot land on it,
then terminate all duds). Two pip traps on that template: `git config --global http.version
HTTP/1.1` (must be global — pip clones `git+https://…diffusers` from requirements.txt too), and
`unset PIP_CONSTRAINT`, which the template exports and which makes a cu130 install fail with
`ResolutionImpossible` hidden behind `pip -q`.

**R46. Container RAM is capped far below `free`, and ai-toolkit's sample pass is what blows it.**
`[live-use]` A 5090 pod shows 123 GB in `free`; the cgroup cap is **60 GB**
(`/sys/fs/cgroup/memory.max`), and `swapon` is not permitted. h3-v16 was OOM-killed at step 750
with **no traceback** when the first sampling rung pulled the fully-offloaded Qwen3-VL-32B encoder
back on top of resident training state. **On H3, disable in-training samples** — it costs nothing,
because the checkpoint and `optimizer.pt` are written *before* sampling, so a relaunch resumes
exactly where it died.

**R47. Symlinked LoRAs do not load in ComfyUI.** `[live-use]` ComfyUI validates the name against
its own scan of `models/loras`, which does not follow symlinks — all 36 cells of the h3-v8 grid
failed although `stat -L` resolved the file. Eval checkpoints must be **real copies**, ~300 MB
each.

**R48. Render the eval on the training pod — but verify the first cell inside ten minutes.**
`[live-use]` Verified on krea2-v13 (2026-09-03): 18 stage-A cells on the training pod at ~6 s/cell
after one model load, zero queue, against a 2–7 minute serverless cold start per batch (20+
minutes when the region is throttled). Counter-case krea2-v14: the stock template had no ComfyUI
running, the director cold-started it, the renderer sat with no cells for an hour, and the pod ran
to its 4h auto-stop (~$4 vs ~$2.30 quoted). **Rule: after DONE, verify the FIRST cell lands within
10 minutes or fall back to serverless.**

**R49. Hardware and quota.** `[live-use]` **5090 ≈ 2× RTX PRO 4500 throughput at 1.375× price** —
Krea 2 2500 steps in **2h01–2h06 at ~2.9 s/it (~$2.30)** vs **3h43–3h49 at ~5.4 s/it (~$3.00)**;
H3 at 1536, 2.61 s/it vs 4.64 s/it. A 3000-step stills run is $1.50–2.50; the whole 9-run H3
ladder was ~$20. Volume is 200–250 GB with models at ~147 GB and each run's series ~3.5 GB;
`optimizer.pt` (~600 MB/run) is the thing to delete — **unless you intend to resume**, which is
exactly what let h3-v17 extend h3-v16 to 5000 steps at 40% of the compute. Volume writes need a
running pod, so fold the copy into the next pod's setup script. And **give each run's eval plan a
unique stem** — the renderer skips cells already on disk, and two runs sharing `eval-A` silently
produce one result.

## Open / contested

- **What in dataset v9 produced the h3-v16 win.** v16 is *"the strongest likeness we've seen on
  h3"*, but the v7→v9 swap moved **three things at once** — selection (15 of 73 against the
  starved axes), native resolution (8 of 15 re-developed at 2× so all clear 1536), and caption
  accuracy (8 of 15 framing terms rewritten on identical pixels). v14's verdict was "faces kinda
  ok, bodies all over the place", and (2) and (3) both bear on body/framing. **Do not curate for
  coverage alone and skip the re-develop and the caption audit.** Attribution needs one arm each.
- **The musubi objective levers were tested independently and never combined.**
  `--h3_timestep_focus_prob 0.5` (v12, *"definitely stronger than v9, far from usable"* — the
  largest single objective-side gain measured) and guidance scale 4.0→2.0 (v13, *"stronger,
  marginal; pale skin and freckles coming out more"*). The combination is the obvious next arm and
  has never been run.
- **ai-toolkit's own distillation countermeasures were off for every run v1–v8.** The UI exposes a
  Distillation Handling Method (`cg`/`ta`/`both`, default **both**) and the H3 preset sets
  `train.do_guidance_loss: true` + `guidance_loss_target: 3.5` plus
  `model.assistant_lora_path: ostris/minimax_h3_training_adapter/…_v1.safetensors`. Our YAMLs
  contained none of these, i.e. handling = `none` — the likely cause of both the v3 rank-32
  collapse and drift near peak. When they *were* tested (v10 CG, v11 adapter) neither bought
  likeness; CG clearly fixed adherence, the adapter was less stable on this identity.
- **The synthetic-share ceiling.** 12–14% was uneventful; 64% failed. Nothing between has been
  measured. dataset v20 (65% synthetic, high variety) and v21 (four blocks, nothing doubled) were
  both built; **krea2-v16 is PREPARED, not launched**, so neither has a verdict.
- **Face loss masks on synthetics.** Built for every v20 synthetic (`masks/`, black ellipse over
  the face padded 35%, all-white for face-hidden cells) as the fix for the v15 face compounding —
  **deliberately not used in the v16 run** (user decision 2026-09-07). Untested.
- **Caption dropout.** Every config we have written uses `0.05`; the 0.33-identity-ratio article
  says `0.3` and names "only renders in training environments" as the symptom of too little. An
  order of magnitude apart, untested here.
- **The internal contradiction on render resolution.** The `synthetic-character` skill still
  prescribes the hi-res regime (head 2048×2560, "2048 is the ceiling", 12 steps) as the settled
  render regime; CHARACTER.md §10 (later, 2026-09-08) says **1024×1280 native** for anything
  destined for a 1024 training bucket, and dataset v4 was built that way. Both are true for
  different purposes — hi-res for final deliverables, 1024-native for training sources — but the
  skill does not say so.
- **Whether the low-pass fallback is needed.** V4-PLAN's fallback (low-pass the training images
  until skin looks slightly waxy, keep skin covered in the body rows, per a Civitai practitioner
  who hit the identical "reptile-like" artefact and could **not** fix it with hyperparameters) was
  never reached, because 1024-native sources fixed it.
- **The canonical-freckle-map pilot** (one canonical reference re-staged into every dataset image
  by Krea 2 Identity Edit, 5 images not 62, one hop from canonical, never chained, denoise
  0.15–0.25 face-only) was designed and not run.
- **H3 clips vs stills for identity (Ciara H3-PLAN Arm 2).** Arm 1 (stills) answered its two
  questions yes; the face-gated clip arm is planned and unrun. Also unresolved: FL2VA↔Ref2VA
  transfer for an identity LoRA, and character-voice training.
- **Full-length crops on Krea 2 at 45°.** On this base the mid-thigh crop cannot be turned (0/10
  across wordings and seeds) while the full-length crop turns on every seed; open exteriors resist
  the turn, bounded interiors do not. Worked around by shooting full-length and cropping.
- **The pubic mound is at the base's prior and twenty wordings did not move it.** Two sweeps,
  including relational/geometric phrasing. What changes it is **pose** and **region size in
  frame** (a navel-to-thigh crop puts it at ~300 px in the 1024 bucket instead of 50–90).
  Recorded as **"do not sweep wording for this again."**

---

## Deltas vs published skills

| Finding | Where it should land | Status |
|---|---|---|
| R11 — 1024-native dataset renders; hi-res-then-downscale causes reticulated skin that survives the downscale; not the VAE | `character-lora-training/references/dataset-and-captioning.md` §3 (new sub-section: source resolution for a synthetic set) **and** `krea-2/references/lora-training.md` §2c | **NEW.** Nothing in the suite distinguishes source-render resolution from training bucket resolution. §2c only argues "train at 1024, not 768" |
| R14 — source render **step count** trains in as texture (20 over-cooks at 2048, 12 clean) | `dataset-and-captioning.md` §3 | **NEW** |
| R12/R13 — H3 resolution ladder 768→1536 measured, plateau at 1792; sub-res sources teach softness | `minimax-h3/references/lora-training.md`, "Hyperparameters that converge" | **NEW + REINFORCES.** The file's only resolution datum is the 12 GB run at 512²; it currently says *"~1000 steps for a 31-image stills run"* with no resolution guidance |
| R18 — r32 collapses H3 under ai-toolkit; r16 only | `minimax-h3/references/lora-training.md`, same section | **REINFORCES with first-hand evidence.** Existing: *"Rank 16, alpha 16. In fal's blind votes, rank 16 beat both 32 and 64"* — community-only; we now have a measured catastrophic failure |
| Distillation handling was OFF on every hand-written YAML v1–v8 | `minimax-h3/references/lora-training.md`, "Distillation handling" | **REINFORCES.** Existing: *"ai-toolkit's YAML path does not inherit the UI preset. A hand-written config omits all of this silently and trains at handling = `none`"* — we are the case study, and the v3 collapse is the predicted symptom |
| R47 — `qtype: convrot8` is mandatory on H3 ai-toolkit or the shipped weights are dequantised and requantised into a 60 GB cgroup cap, OOM with no traceback; disable in-training samples | `minimax-h3/references/lora-training.md`, new "Memory traps" section | **NEW** |
| musubi `--h3_timestep_focus_prob 0.5` measured as the largest single objective gain; guidance 2.0 marginal; the two never combined | `minimax-h3/references/lora-training.md`, "Hyperparameters that converge" | **REINFORCES.** Existing calls it *"the most commonly missed convergence lever"* on musubi's own claim; we have a first-hand A/B |
| H3 "Still open" list: **a stills-trained LoRA does hold identity in motion** (Ciara h3-v1: T2V thigh-up 0.200 median vs 0.920 control; FL2VA+keyframe 0.167→0.172 flat vs base 0.161→0.263) | `minimax-h3/references/lora-training.md`, "Still open" bullet 3 | **CONTRADICTS.** Existing line: *"**Whether a stills-trained character LoRA holds identity in motion.** The 12 GB proof run trained on stills, but no end-to-end report shows that LoRA holding up in generated video."* This is now answered first-hand |
| H3 dataset shape: 15 coverage-built images beat 73; count is not the lever | `minimax-h3/references/lora-training.md`, "Datasets" | **REINFORCES + refines.** Existing: *"Close and tight beats wide for identity. The one published comparison found 31 close-up face images beat 32 full-body images"* — our v16 result is a *shape* win at 15 images, and DATASET-DESIGN explains why the note.com A/B does not transfer (its mechanism was ai-toolkit training H3 at 512) |
| R16/R17 — the nine-run Krea 2 recipe, unchanged; r32 > r16 measured on identical datasets | `krea-2/references/lora-training.md` §3a and §6 | **REINFORCES §3a strongly.** §3a already carries this exact config from "a finished private character run: 25 photographs, 2250 steps on a 32 GB RTX PRO 4500" — that is krea2-v1. Now it has 15 more runs behind it, and the r16-vs-r32 A/B is new |
| R41 — evaluate on the deployment checkpoint: fineporn at 1024×1536 unusable, ≥1344×2016 good; Raw is not an inference target; c2500 survived where `final` did not | `krea-2/references/lora-training.md` §8 | **REINFORCES + extends.** Existing §8: *"Validate on Turbo, not Raw — you ship on Turbo."* Extend to: validate on **every** checkpoint × resolution you will deploy on; a Turbo-only eval shipped a broken LoRA |
| R42 — cfg 1.5 grains a guidance-distilled Krea 2 checkpoint with **no LoRA loaded**, background included | `krea-2/SKILL.md` failure-modes table; `character-lora-training/SKILL.md` failure table | **NEW.** The suite says cfg-off/1.0 for Turbo but never names cfg as a *grain* source, nor the background test that distinguishes a sampling artefact from a learned one |
| R29 — measured synthetic-share failure at 64% | `dataset-and-captioning.md` §3, "Feeding a new LoRA with an old one's pictures" | **REINFORCES the number, extends the mechanism.** Existing: *"Keep the synthetic fraction around 10% of the set"* — our failure at 64% is the first measured point, and the mechanism is specific: the synthetics carried one generator's *rendering of the face*, weakest at small scale, and training amplified it |
| R30(b) — vary seed, camera and scene *across* the synthetics, or their shared signature is what trains | `dataset-and-captioning.md` §3 | **NEW.** The one-clause rule (§2) covers holding the character fixed; nothing covers the inverse — that the synthetics' shared *generation* settings become the learned invariant |
| R32 — the body-pass-at-0.3 / one-face-pass-at-1.0 repaint stack, with resolution as the quality lever (1216×1792 body pass, not 832×1216) | `krea-2/references/characters.md` §4 (detailer-stage swap) or a new sub-section | **NEW.** §4 covers the deployment-side detailer swap; this is the *dataset-generation* stack, with measured denoise and strength bands |
| R24 — captioning age and freckle density made them prompt variables that fight the LoRA, and neither became promptable | `dataset-and-captioning.md` §4 | **CONTRADICTS a nuance.** Existing text says name the **cause** not the trait, and warns that naming a trait in generation prompts bakes it in. Our result adds a third case: naming a trait *in captions* can make it a fighting variable while still failing to become promptable — the fix was to strip it and let it bind |
| R25 — hair colour/length **did** become promptable when captioned, at a cost | `dataset-and-captioning.md` §4 | **REINFORCES.** This is caption-the-residual working as advertised, with a measured before/after and the stated cost (prompts must name hair from then on) |
| R26 — a 29-of-32 colour majority binds to the trigger; spread with no majority is the fix | `dataset-and-captioning.md` §2 (coverage) | **NEW as a quantified case** of "whatever never varies becomes part of the identity" |
| R33/R34 — probe design rules; the near-verbatim probe that inverted a headline finding | `evaluation-and-tooling.md` §4 | **REINFORCES.** Existing: *"Check every probe against the caption corpus before you trust it … One near-verbatim overlap is enough to invalidate every verdict a sweep produced `[community — production run, 2026-08]`"* — that citation *is* this repo. The five **design** rules (face >15% of frame, upright and side-on, stay photographic, portrait aspect for standing figures, NSFW base for nude probes) are new |
| R35/R36/R37 — arena-style pairs/grids/gates instead of 1–5; margin chips; judge fatigue after four decks in two days | `evaluation-and-tooling.md` §3 | **NEW.** §3 covers blind coding and pairwise-beats-pointwise, but not the deck format, the margin record, or fatigue as a design constraint |
| R38 — the A–F stage ladder with cell counts and the ship rule | `evaluation-and-tooling.md` (new section) or `character-lora-training/SKILL.md` "Evaluating a run" | **NEW.** The skill has three layers (previews → grid → blind); this is a per-stage protocol that fixes one variable at a time on top of them |
| R19 — the lower-rung tie-break | `character-lora-training/SKILL.md` "Evaluating a run"; `evaluation-and-tooling.md` §3 | **NEW** |
| R20 — past the peak, the *source medium* bakes in (phone-JPEG compression as skin) | `SKILL.md` failure-modes table, new row | **NEW.** Related to "Style drifts toward the dataset's look" but a distinct mechanism |
| R31 — triage calibration numbers, leave-one-out method, and the two documented blind spots (profiles; small-face scale) | `evaluation-and-tooling.md` §5 | **REINFORCES + extends.** Existing calibration advice is "3 real photos as reference, score a 4th" — leave-one-out over 15 with p50/p90/max is a better recipe, and *"not sensitive enough at half/full-body face scale to be trusted for a ship call"* is a new, measured limit |
| R39/R40 — reproduce the known-good render first; strength-0 control in every comparison; sidecar every diagnostic render; `cells.json` beats the plan; enumerate blast radius before retracting | `evaluation-and-tooling.md` (new "diagnosing an artefact" section) | **NEW.** The suite covers judging a run; nothing covers debugging a quality regression |
| R5 — identity is learned per face-scale, with the measured 3-dataset table | `dataset-and-captioning.md` §2 (shot size) | **REINFORCES with numbers.** Existing: *"A face-only dataset gives you a character with an unreliable body. A full-body-only dataset gives you a face that dissolves at distance."* — exactly right; we have the percentages and the probe results |
| R6 — a second crop of the same photo is not free coverage; it teaches a framing | `dataset-and-captioning.md` §1 (near-duplicates) | **NEW nuance.** §1 covers near-duplicates from a burst; crops of one photo behave the same way *and* teach the crop |
| R10 — immutable dataset versions; sha-verify a reconstruction against the as-trained copy | `SKILL.md` pre-flight checklist | **NEW** |
| R44–R51 — the ops catalogue (silent launches, `--stock`, driver gate, cu130, `PIP_CONSTRAINT`, HTTP/1.1, symlinked LoRAs, cgroup cap, on-pod eval with the 10-minute rule, 5090 vs 4500, volume quota / `optimizer.pt`) | `comfyui-on-runpod/` — a new `references/training-pods.md`, **not** the training skills | **MOSTLY NEW.** Only the symlink and volume-quota items touch anything existing. Per the repo boundary these are operational, so they belong with the pod skill, and the generalisable subset is: verify a launch by artefact not by return code; gate the driver; kill by port; a monitor event is a nudge not a state |
| R28 — prompt length dilutes the LoRA's hold (~95 words reticulates, ~45 clean); never re-add a base realism tail over a LoRA; a long face block claims the frame | `krea-2/references/characters.md` §6 (failure modes) and `krea-2/SKILL.md` | **NEW.** The skill covers texture anchors as a *fix* for Krea's softness; this is the inverse — the same anchors are harmful once a LoRA carries the texture |

---

## Hyperparameter ledger

**Krea 2 — Amy.** All ai-toolkit @ `5497a001` on Krea 2 Raw, arch `krea2`, adamw8bit, LR 1e-4,
resolution [1024], batch 1, qfloat8, `low_vram: false`, `cache_text_embeddings: true`,
`save_every 250`, samples disabled from v7 onward. Deploy Turbo (8 steps, cfg 1.0, euler/simple);
nude work over `fineporn_v4_int8`.

| Run | Dataset (size / source res) | Rank | Steps | Winning rung | Verdict |
|---|---|---|---|---|---|
| krea2-v1 | v1 — 25 real, ≥1536 | r32 | 2250 | **c1750 @ 1.1** | Shipped. Underfit signature (likeness rises monotonically to 1.1) |
| krea2-v2 | v1 — 25 (unchanged) | **r64** | 3000 | c2500 @ 1.0 | **Lost to the v1 control.** Capacity + length ruled out |
| krea2-v4 | v4 — 74, full pool | r32 | 3000 | c3000 @ 1.1 | 2nd/3rd on faces behind v1. Nude adherence 2/8 |
| krea2-v5 | v5 — 28, single era, 32% nude | r32 | 3000 | **c2750 @ 1.1** | Body/nude winner (swept all four nude picks); no face cell placed |
| krea2-v6 | v6 — 32 = v1 + 7 nudes, 28% nude | r32 | 3000 | **c3000 @ 1.1** | General-purpose default for a month; face-parity with v1 |
| krea2-v7 | v6 | r32 | 8000 planned | — | **Killed at step 170** (~$0.30) — its premise was falsified by the OOD grid |
| krea2-v8 | v8 — 15, coverage-built | r32 | 2500 (167/img) | 1500/2000/2250/final staged | "Very close" to the 32-image control at <half the count |
| krea2-v9 | v13 — 13 real, face-focused | r32 | 2500 | **c1750 @ 1.0** | **Face specialist.** C1/C2 win vs v6; C3 profile 0/5; loses every body pair |
| krea2-v10 | v14 — 16 real + 3 standing frames | r32 | 2500 | c2250 @ 1.0 | **Does not ship.** C7/C4 up vs v9, C1 0/4 down. v6 beat it 10–2 |
| krea2-v11 | v15 — 15, DSLR pair removed | r32 | 2500 | c1750 @ 1.0 | **Does not ship.** C1 recovers, **C2 0/6** |
| krea2-v12 | v16 — 15, two doubled crops | r32 | 2500 | c2250 @ 1.0 | **Does not ship.** Weakest of the four; v6 9–1, v9 6–2–2 |
| krea2-v13 | v17 — 15, real full-length, no doubles | r32 | 2500 | **c2250 @ 1.0** | **SHIPPED DEFAULT.** First real-photo arm to beat v6 on the close face |
| krea2-v14 | v18 — 16, all captions rewritten | r32 | 2500 (156/img) | c2250 / final | Captions arm: hair colour and length become promptable; age and freckles do not |
| krea2-v15 | v19 — 88 entries (16 real ×2 + 56 synthetic) | r32 | 3500 (~40/entry) | final (3500) by triage | **FAIL (user).** Body learned, face regressed — 64% synthetic |
| krea2-v16 | v20 — 91 entries, high-variety synthetics | r32 | 3500 | — | **Prepared, not launched** |

**Krea 2 — Ciara** (fully synthetic datasets; same recipe, `caption_dropout 0.05`; eval by face
triage against `triage/rotation-01.json`, p50 0.112).

| Run | Dataset (size / source render) | Rank | Steps | Winning rung | Verdict |
|---|---|---|---|---|---|
| krea2-v1 | v1 — 54 cells, **1024-class, 8 steps** | r32 | 3500 (~65/img) | c2000 (median 0.182) | Recipe works. All-cell median 0.227. Body under-rendered; skin smooth |
| krea2-v2 | v2 — 62, **hi-res 2048/1536, 20 steps** | r32 | 3500 | c2500/c3000 (flat) | Face unchanged, body to spec, **fine speckle trained in** from 20-step sources. Median 0.232 |
| krea2-v3 | v3 — same 62 at **12 steps** | r32 | 3500 | final (0.181) | Best of the three, **median 0.199** — then found to carry reticulated skin on fineporn |
| krea2-v4 | v4 — 32 cells, **1024 native** | **r16** | 3000 | c1500 (0.164) / final (0.170) | Skin clean at every rung. Lost to v5 on every table |
| krea2-v5 | v4 — same 32 | r32 | 3000 | **final (3000)**, c2500 equivalent | **Ship candidate.** Turbo median 0.155–0.196, fineporn 0.156–0.163; profiles strict 4/4; flexibility and stability pass |
| krea2-v6 | v5 — same 32 cells, hair colour spread | r32 | 3000 | — | Planned (V5-PLAN, 2026-09-09) |

**MiniMax H3 — Amy.** All r16/alpha16, LR 1e-4, adamw8bit, batch 1, 3000 steps, `save_every 250`,
`num_frames: 1`. ai-toolkit @ `5497a001` on `fl2va_pruned int8_convrot`; musubi @ `41ae4be1` (dev)
on the **non-pruned** `int8_convrot` (musubi #1059). Deploy strength 1.0.

| Run | Trainer | Dataset | Res | The one variable | Verdict |
|---|---|---|---|---|---|
| h3-v1 | ai-toolkit | v6 (32) | 768 | baseline | **Not usable** — likeness varies seed to seed for faces *and* bodies; plateau 2250≈2750≈3000 |
| h3-v2 | ai-toolkit | v6 | **1024** | resolution | Large consistency win; still not shippable. Peak 2250–2750 |
| h3-v3 | ai-toolkit | v6 | 768 | **rank 32** | **Catastrophic collapse** — adherence destroyed at every rung |
| h3-v4 | ai-toolkit | v6 | 1024 | rank 32 × res | Died silently at step 1320; abandoned |
| h3-v5 | ai-toolkit | v6 | **1280** | resolution | Best arm to that point; the 3000-step degradation disappears |
| h3-v6 | **musubi** | v6 | 1024 | trainer + guidance loss 4.0 / σ-min 0.15, swap 36 | *"Much more stable, much better prompt adherence. But the likeness just hasn't landed"* |
| h3-v7 | ai-toolkit | v6 | **1536** | resolution | **Best likeness of the objective ladder.** 2.0 s/step on a 5090, ~$1.70 |
| h3-v8 | ai-toolkit | v6 | 1792 | resolution | *"Much the same"* as 1536 — ladder over. 4.64 s/it on a 4500 |
| h3-v9 | musubi | v6 | 1536 | resolution (vs v6) | 3h58m at 4.80 s/it, swap 24 + `h2d_only`. Baseline for v12/v13 |
| h3-v10 | ai-toolkit | v6 | 1536 | `do_guidance_loss` + target 3.5 | Fixes **adherence**, not likeness |
| h3-v11 | ai-toolkit | v6 | 1536 | `assistant_lora_path` (training adapter) | Less stable than guidance on this identity |
| h3-v12 | musubi | v6 | 1536 | `--h3_timestep_focus_prob 0.5` | *"Definitely stronger than v9, far from usable"* — largest single objective gain |
| h3-v13 | musubi | v6 | 1536 | guidance scale 4.0→2.0 | *"Stronger, marginal; pale skin and freckles coming out more"* |
| h3-v14 | ai-toolkit | **v7 (73)** | 1536 | dataset **size** | **No gain.** Closes the count question. 2h17 at 2.71 s/it |
| h3-v15 | musubi | **v9 (15)** | 1536 | dataset shape + `bucket_no_upscale` | 3h57m at 4.75 s/it, clean finish, ~$4.20 |
| h3-v16 | ai-toolkit | **v9 (15)** | 1536 | dataset shape (config diff = 2 lines) | **SHIPPED — the strongest likeness on H3.** c3000 @ 1.0, 2.61 s/it. `qtype: convrot8`, offload 0.5 / TE 1.0, samples disabled |
| h3-v17 | ai-toolkit | v9 | 1536 | **resume 3000→5000** | 20 rungs, 3h33m, ~$3.50. Confirms the v16 OOM was the sample pass, not the step count |

**MiniMax H3 — Ciara.** `runs/h3-v1`: ai-toolkit @ `5497a001`, dataset v3 (62 images at
1536×2688), r16/α16, 1536, 3000 steps, `sample_every` disabled, offload 0.5 / TE 1.0,
`cache_text_embeddings: false`. 3h00 on a 5090, 12 rungs, no incidents (~$4.90 including an idle
hour). **Best rung c2750** (all-prompt median **0.315** vs krea2-v3's 0.199 on the same prompts —
~1.5× further from canon, and it falls off with framing exactly as the Amy ladder did). Motion
result is the headline: T2V + LoRA at thigh-up **0.200 median / 0.259 worst** against a no-LoRA
control at **0.920** (a different, older woman); FL2VA from a Krea keyframe + LoRA holds flat
across 5 s (**0.167→0.172**) where the base drifts (0.161→0.263), and worst-frame distance halves.
