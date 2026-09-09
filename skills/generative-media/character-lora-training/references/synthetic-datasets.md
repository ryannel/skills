# Synthetic datasets

The dataset decides the ceiling, and a generated dataset is the one kind you control end to end. This file owns the model-agnostic craft of *making* one: the factory loop, the packaged suites, seeding a new set from an older LoRA's renders, and the video turnaround. Size, coverage, the resolution rule and captioning stay in [`dataset-and-captioning.md`](dataset-and-captioning.md), and everything here assumes those. Claims marked `[live-use — media lab, …]` come from first-hand runs on rented hardware, each naming its run and date. They are measured points from two characters, not consensus.

## Contents

1. [The synthetic dataset factory](#1-the-synthetic-dataset-factory)
2. [Feeding a new LoRA with an old one's pictures](#2-feeding-a-new-lora-with-an-old-ones-pictures--when-it-helps-when-it-wrecks-the-run)
3. [The video turnaround](#3-the-video-turnaround--a-better-factory-for-rotation-specifically)

---

## 1. The synthetic dataset factory

This is now the standard route, and the one to prefer for anything you intend to publish:

1. **Lock an anchor image.** One image that defines the character. Iterate here as long as it takes, because everything downstream inherits it, and no amount of training fixes a weak anchor.
2. **Generate the varied set with an edit model, or with the base and a byte-identical character block.** Drive it from the anchor and change one clause at a time, per [`dataset-and-captioning.md`](dataset-and-captioning.md) §2. An edit model holds an identity across an edit far better than a text prompt holds it across separate generations. Render **inside the base's band, at a clean step count, at LoRA strength 0** (`dataset-and-captioning.md` §3).
3. **Over-generate and curate down.** Produce roughly twice what you need and cut to the best, for example 60 down to 30. Curation is where dataset quality actually comes from.
4. **Caption from what landed, not from what you asked for** (`dataset-and-captioning.md` §4).
5. **Train, evaluate, and expect to revisit the dataset** rather than the hyperparameters when results disappoint.

There are two advantages beyond convenience. You get **coverage photography rarely gives you**, because a real photo set almost never has all eight rotations under matched lighting. And the character **resembles nobody**, which entirely removes the likeness problem described in [`publishing-and-likeness.md`](publishing-and-likeness.md).

Which edit model to use for step 2 is a per-family question; your model skill names the one for its ecosystem. Edit-model superiority is asserted everywhere and validated nowhere: every source describes generation and stops before training.

**Three rules from a 32-cell set that shipped** `[live-use — media lab, Ciara dataset v4, 2026-09-09]`. The set was 32 cells at an identity ratio of 0.31 (10 identity-emphasis, 11 in-context medium, 11 in-context full), all 1024 wide, one prompt block per variable. First, **vary everything the synthetics share.** A synthetic set has an invariant the one-clause rule does not cover: its own generation settings. Fifty-six renders sharing one seed, one camera sentence and one soft studio look taught the generator's *rendering* as the face. The corrected set changed what was uniform — twelve place-and-light scenes, a seed per cell, six camera styles `[live-use — media lab, Amy dataset v19→v20, 2026-09-06]`. Second, **some variables need the base's vocabulary, not yours.** Eyes are identity and never captioned, so the generation wording is the only lever, and the whole set must be re-rendered for the average to move. Third, **a region gets the pixels its frame area earns.** A feature ~50–90 px wide in the 1024 bucket will not render to spec whatever you write. The same sentence on a crop that puts it at ~300 px lands on every seed. Wording moves adjacent things, not the starved region. For body attributes that *are* describable, relational and geometric description beats adjectives: "several times wider than", "almost the colour of her skin". The lab credits it as its biggest single realism win.

**Someone has packaged the whole loop.** VNCCS 3.0, the Visual Novel Character Creation Suite, is a ComfyUI system that wires steps 1–3 together `[community — AHEKOT, r/StableDiffusion 892 pts]`. Over building it yourself, it gives you: a **Control Center** that downloads and manages the models the workflows need, an interactive 3D **Pose Studio** for posing, framing, lighting and pose libraries, a **Character Cloner** that builds the anchor from reference images, a **Clothes Designer** that copies an outfit onto different characters, an **Emotion Studio** for expression sets, and **per-sprite regeneration**, so one bad frame does not cost you the sheet. Install via `github.com/AHEKOT/VNCCS_Easy-Install` `[official — repo README, read 2026-08-23]`.

Settle two things before you train on its output. First, its generation stack is reported to be built around **Anima-Base-1.0** `[community — AHEKOT; re-verify]`. That means the stills inherit that model's look and its weights-side licence, so check [`anima`](../../anima/) before publishing anything trained on them. Second, it aims at a **visual-novel sprite sheet**, which is a different coverage target from `dataset-and-captioning.md` §2. It optimises for expression and outfit variety, and leaves rotation and elevation for you to check. Curate its output against that protocol rather than assuming a finished sheet is a finished dataset.

**Putting a real identity onto a generated body** is a dataset-generation stack of its own: a body pass with the LoRA low, then one face pass with it at full strength. Its measured bands are Krea-specific: [`krea-2/references/characters.md`](../../krea-2/references/characters.md).

## 2. Feeding a new LoRA with an old one's pictures — when it helps, when it wrecks the run

Seeding a dataset with a predecessor LoRA's renders is a widely used gap-filler. The identity is already locked, you have full provenance, and it can supply coverage the real photos never had.

**The hazard is recursion, not synthesis.** Each generation trained on the previous generation's outputs compounds that generation's errors. In a self-consuming chain of diffusion fine-tuning, as little as **5–10% synthetic** — the figure depends on the dataset — is enough to start degradation. Mixing 50% real gives minimal protection. Diversity collapses before image quality visibly does `[official — arXiv 2407.17493 (ReDiFine); arXiv 2311.12202 (Bohacek & Farid)]`. Trait drift is the visible form: a slightly wrong freckle pattern in v1's renders becomes v2's fact, and nothing in v2's data disagrees with it. The survey literature's optimistic figures (60–90% synthetic) assume a preserved real anchor and active diversity monitoring — a gated loop, not the naive one `[official — arXiv 2608.21366]`.

**The measured points are two.** A set at 14% synthetic was uneventful and was the strongest model at the time. A set at **64% synthetic** — 56 of 88 entries rendered by the previous LoRA — learned the body and regressed the face. The verdict: "the face looks off at higher strength and doesn't hold on the full body nudes or even the half body" `[live-use — media lab, Amy dataset v19, krea2-v15, 2026-09-06]`. The mechanism was specific: every synthetic carried one generator's rendering of the face, weakest at small scale, and training amplified it. Nothing between 14% and 64% has been measured. The lab's next sets ran at ≤40% and then at 65% with high variety, on the stated direction that "the best and most flexible LoRA is going to be almost entirely synthetic". That is the current operating hypothesis, and it is unproven `[contested]`. The lab's own harder rule for a synthetic character runs the other way: **never generate training data from the character's own LoRA.** Dataset cells are drawn at LoRA strength 0.0 on the base, which is what makes them a clean source.

Rules that keep seeding safe, each confirmed by a failure:

- **Keep the synthetic fraction low — around 10% — unless you are running the gated version deliberately.** Gated means the real photos are preserved in every version and variety across the synthetics is enforced. At 10% the real photos still anchor every trait, so drift gets corrected instead of compounded.
- **Seed for one generation only.** vN's renders may feed vN+1's dataset. Never let vN+1's renders feed vN+2. That chain is the recursion the research warns about. The stricter lab rule — strength 0 always — removes the question.
- **Vary everything the synthetics share** (above), or their shared signature is what trains.
- **No synthetic where a real photo does the job.** The corrected set dropped nine cells that duplicated real coverage.
- **Source only from renders you judged and kept, at full size, next to the real references.** Model artefacts are invisible at contact-sheet size and permanent once trained: over-baked traits, plastic skin, a softness the original photos never had.
- **A metric can triage a candidate but must never admit one.** Face-embedding distance to a real-photo centroid, calibrated leave-one-out, passed synthetic cells that the person who knows the face rejected on sight: "it doesn't look at all like her" `[live-use — media lab, Amy triage v17, 2026-09-05]`. The rule that replaced it: no synthetic goes in unless a human who knows the subject reads it as them. There is also a real tension nobody has resolved. A similarity gate *reduces* set entropy, and entropy is the quantity that best predicts generalisation in recursive training (r = 0.91) `[official — arXiv 2509.16499]`. Nobody has published how to run both gates.
- **Caption each render's visible traits.** A caption that names what the render actually shows turns its drift into a variable the training can correct, rather than a fact it reinforces.

**A previously rejected render carries its rejection reason with it.** Re-admit it only after the full-size side-by-side check, and only if the reason it was rejected is not about to be trained in.

## 3. The video turnaround — a better factory for rotation specifically

An edit model generates each angle separately, so eight edits give the identity eight chances to drift. **A video model generates them as one continuous camera move.** The angles then come out consistent because of how they were made, not because you curated them. On the hardest axis of the coverage protocol (`dataset-and-captioning.md` §2), that is a different kind of answer, not just a convenience.

The recipe: feed a handful of imperfect references into a reference-conditioned video mode, with a prompt that spins the character **slowly through 360°, with no cuts**, then pull out the frames. [`minimax-h3`](../../minimax-h3/)'s Ref2VA is the worked example. There is a packaged workflow for it: `PoopMan333/H3_Character_Sheet_Generator` `[community — PoopMan333, Civitai]`. No external source has yet reported training results from harvested turnaround frames, for or against.

Three caveats decide whether it is worth it:

- **It is expensive in generated frames.** The packaged workflow generates **124 frames to keep 6**. You are paying video-generation cost for a still dataset.
- **Video stills are lower-detail than image stills.** Pair the turnaround with dedicated close-ups from an image model before training, or the LoRA learns a slightly soft face. The lab's version of the same caveat: a 768p clip set mixed with 1536p stills may pull face detail down on the stills.
- **Check the licence of the model you harvest from.** Some open video licences restrict using their output to train other models. [`ltx-2-5`](../../ltx-2-5/)'s Attachment A ¶18 does exactly that, and how far it reaches into non-commercial work is unsettled; [`ltx-2-5/references/licence-and-derivatives.md`](../../ltx-2-5/references/licence-and-derivatives.md) carries the contested flag on that paragraph. A dataset factory is precisely the use that sits in that gap, and the LoRA you end up with is the thing that carries the problem forward.

The trick works on any video model with reference conditioning. So do the caveats.

---
