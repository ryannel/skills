# Datasets and captioning

The dataset decides the ceiling. Hyperparameters only decide how close you get to it.

## Contents

1. [Size and curation](#1-size-and-curation)
2. [The coverage protocol](#2-the-coverage-protocol)
3. [The synthetic dataset factory](#3-the-synthetic-dataset-factory)
4. [Captioning](#4-captioning)
5. [Multi-outfit and multi-character](#5-multi-outfit-and-multi-character)

---

## 1. Size and curation

**15–30 well-curated images beat 100 mediocre ones.** One of the more consistent findings across trainers and families — NanashiAnon puts the Illustrious-era single-outfit figure at 20–30, L3n4's crash course at "a well-curated 30–50 beats a poorly curated 500" `[community — NanashiAnon, L3n4/Civitai 25645; convergent]`. It holds because the failure mode of a large dataset is not "too much data" but "uncontrolled variance" — every uncaptioned inconsistency is something the model tries to learn.

Curate against these, hard `[community — MyAIForce, Civitai guides 5301/6990; convergent]`:

| Reject | Why |
|---|---|
| Blurry, low-resolution, heavily compressed | Teaches the artefacts |
| Heavy stylisation or filters | Bakes the filter into the identity |
| Occluded face (hands, hair, sunglasses) | Weakens the thing you are training |
| Near-duplicates | Effectively upweights one pose |
| Inconsistent apparent age or build | Produces an averaged, unstable identity |
| Watermarks, text overlays | Reliably learned and reliably reproduced |

**Near-duplicates are the most common self-inflicted wound.** Twenty frames pulled from one video clip look like twenty images and behave like one — the model sees a single pose twenty times and collapses onto it.

---

## 2. The coverage protocol

Coverage, not count, is what makes an identity generalise. The target is that every axis the model will be asked to vary at generation time appears varied in the dataset.

**Rotation — the 8-point protocol.** Around the head:

1. Front
2. Three-quarter left
3. Three-quarter right
4. Profile left
5. Profile right
6. Rear three-quarter left
7. Rear three-quarter right
8. Rear

Rear angles matter more than people expect. Without them the model has no idea what the back of the head looks like and will improvise — usually badly, and usually at the worst moment.

**Elevation.** At least one above eye level and one below. A dataset shot entirely at eye level produces a character that distorts the moment you ask for a high or low angle.

**Shot size.** Close-up, medium, and full body. A face-only dataset gives you a character with an unreliable body; a full-body-only dataset gives you a face that dissolves at distance.

**Expression.** Neutral plus at least two others. Otherwise expression locks — the character can only ever wear the face it was trained on, which reads as uncanny well before anyone can say why.

**Lighting and setting.** Vary both, or they become part of the identity and every generation inherits the dataset's lighting.

**The one-clause rule.** When generating a dataset, hold the character description **byte-identical** and vary only the clause you are covering — rotation, or shot size, or expression. Anything else that drifts between images is variance the model will try to attribute to the character. `[community — Civitai dataset guides 7777/21257/21114; convergent]`

---

## 3. The synthetic dataset factory

The now-standard route, and the one to prefer for anything you intend to publish:

1. **Lock an anchor image.** One image that defines the character. Iterate here as long as it takes — everything downstream inherits it, and no amount of training fixes a weak anchor.
2. **Generate the varied set with an edit model**, driving it from the anchor and varying one clause at a time per §2. Edit models hold identity across an edit far better than a text prompt holds it across generations.
3. **Over-generate and curate down.** Produce roughly twice what you need and cut to the best — perhaps 60 down to 30. Curation is where dataset quality actually comes from.
4. **Caption per §4.**
5. **Train, evaluate, and expect to revisit the dataset** rather than the hyperparameters when results disappoint.

Two advantages beyond convenience: you get **coverage photography rarely provides** — a real photoset almost never has all eight rotations at matched lighting — and the character **resembles nobody**, which removes the likeness problem described in [`publishing-and-likeness.md`](publishing-and-likeness.md).

Which edit model to use for step 2 is a per-family question; your model skill names the one for its ecosystem.

### The video turnaround — a better factory for rotation specifically

An edit model generates each angle independently, so eight edits give you eight chances for the identity to drift. **A video model generates them as one continuous camera move**, which makes the angular coverage internally consistent by construction rather than by curation. That is a categorical improvement on the hardest axis of §2, not a convenience.

The recipe: feed a handful of imperfect references to a reference-conditioned video mode — [`minimax-h3`](../../minimax-h3/)'s Ref2VA is the worked example — with a prompt that spins the character **360° slowly, with no cuts**, then extract frames. A packaged workflow exists: `PoopMan333/H3_Character_Sheet_Generator` `[community — PoopMan333, Civitai]`.

Three caveats decide whether it is worth it:

- **It is expensive in generated frames.** The packaged workflow generates **124 frames to keep 6**. You are paying video-generation cost for a still dataset.
- **Video stills are lower-detail than image stills.** Pair the turnaround with dedicated close-ups from an image model before training, or the LoRA learns a slightly soft face.
- **Check the licence of the model you harvest from.** Some open video licences restrict using their output to train other models — [`ltx-2-5`](../../ltx-2-5/)'s Attachment A ¶18 does, with its scope against non-commercial work unsettled `[contested]`. A dataset factory is precisely the use that sits in that gap, and the resulting LoRA is the artefact that carries the problem forward.

The trick generalises to any video model with reference conditioning; the caveats generalise with it.

---

## 4. Captioning

**The rule: caption the residual.** Describe everything that varies. Never describe what you are teaching.

| | Character LoRA | Style LoRA |
|---|---|---|
| Never caption | the face, the identity, the trigger's referent | the medium, rendering, palette |
| Always caption | pose, angle, shot size, expression, clothing, setting, lighting | the subject and everything depicted |
| Diversity needed in | everything except the person | **subjects above all** |

**Format follows the encoder class**, not preference:

| Encoder | Caption style | Trigger token |
|---|---|---|
| CLIP-class (SDXL-era, Pony/Illustrious/NoobAI) | Weighted comma-separated tags, booru dialect | **Verbatim rare token**, used literally |
| LLM/T5-class (Flux, Z-Image, Qwen-class, Krea) | Natural prose clauses | Folded into a phrase, or omitted — bare rare tokens confuse a language encoder |

Getting this backwards is a common cause of a LoRA that "trained fine but won't trigger."

**Consistency of vocabulary matters more than richness.** If you call it "three-quarter view" in one caption and "angled slightly away" in another, you have split one concept into two. Pick terms and reuse them exactly.

**Caption length should be even across the set.** A set where some images have three words and others have forty upweights the sparse ones in ways that are hard to predict.

**Captionless training is contested.** Some trainers run DiT character LoRAs with no captions at all and report good replication. It works for pure replication and gives up controllability — you cannot vary what you never named. Treat it as a specialised technique, not a default. `[contested]`

---

## 5. Multi-outfit and multi-character

**Multi-outfit.** A single character LoRA can hold several distinct outfits if each gets a unique trigger tag, is visually distinct from the others, and has enough coverage of its own. The practical ceiling is around **six outfits** before they start bleeding into each other `[community — Khanykov01, Civitai 6990; strong]`. Beyond that, separate LoRAs, or an outfit LoRA stacked onto the character.

The failure is asymmetric: outfits bleed into each other long before the identity degrades. If a character starts wearing a mix of two outfits, that is the ceiling announcing itself.

**Multi-character.** Do not train two people into one LoRA. They average. Train separately and compose at generation time:

- **Regional conditioning** where the model supports it (image side).
- **Per-face detailer passes** — generate the scene without character LoRAs, then run a detailer per face with the relevant LoRA loaded. This is the most reliable route on image models.
- **Separate shots and cut between them** on video, where no regional conditioning exists across frames.

**Identity bleed rises with visual similarity.** Two characters of similar age, build and colouring will trade features far more than two who look nothing alike — worth knowing at casting time, when it is still cheap to change.

### Differential Output Preservation — a training-time answer, on some models

The advice above assumes composition at generation time is the only lever. As of mid-2026 there is a **training**-side option worth knowing about, though it is model-dependent in a way that matters.

**Differential Output Preservation** (DOP) trains each character LoRA against a **class** — e.g. `"woman"` — preserving the base model's output for the class while learning the individual. Several such LoRAs then load together in one generation with minimal bleed. A reproducible recipe: a LoKr config with DOP enabled, class `"woman"`, **1500 steps** rather than 750 (previews stabilise around 1500) `[community — MASilverHammer, r/StableDiffusion]`.

Boundaries, from the same source:

- **Hard cap of four characters.** Five falls apart; four holds.
- Characters **borrow features from each other** — lips are the reported offender — so similar-looking characters converge toward looking related. Section-5's similarity rule still applies, it is just less punishing.
- **Prompt the distinguishing features.** Naming what separates two characters (a long nose, a jawline) is what keeps them separated at inference.
- Captioning still matters. The author's lazily-captioned sets (trigger word only) worked; their well-captioned set produced the more resilient LoRA.

**The model-dependence is the important part.** The same technique **failed on Z-Image Base** — DOP there prevented the character being learned at all — and **worked on Krea 2**. Do not assume it transfers. If a multi-character job is the requirement, that is now a reason to choose the base model on this axis specifically: see [`krea-2/references/characters.md`](../../krea-2/references/characters.md). Above four characters, or on a model where DOP does not take, fall back to per-face detailer passes.
