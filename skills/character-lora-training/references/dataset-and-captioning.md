# Datasets and captioning

The dataset decides the ceiling. Hyperparameters only decide how close you get to it.

1. [Size and curation](#1-size-and-curation)
2. [The coverage protocol](#2-the-coverage-protocol)
3. [The synthetic dataset factory](#3-the-synthetic-dataset-factory)
4. [Captioning](#4-captioning)
5. [Multi-outfit and multi-character](#5-multi-outfit-and-multi-character)

---

## 1. Size and curation

**15–30 well-curated images beat 100 mediocre ones.** This is one of the more consistent findings across trainers and families, and it holds because the failure mode of a large dataset is not "too much data" but "uncontrolled variance" — every uncaptioned inconsistency is something the model tries to learn.

Curate against these, hard:

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

**The one-clause rule.** When generating a dataset, hold the character description **byte-identical** and vary only the clause you are covering — rotation, or shot size, or expression. Anything else that drifts between images is variance the model will try to attribute to the character.

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

**Multi-outfit.** A single character LoRA can hold several distinct outfits if each is captioned as a variant and each has enough coverage of its own. Community experience puts the practical ceiling around **half a dozen outfits** before they start bleeding into each other. Beyond that, separate LoRAs, or an outfit LoRA stacked onto the character.

The failure is asymmetric: outfits bleed into each other long before the identity degrades. If a character starts wearing a mix of two outfits, that is the ceiling announcing itself.

**Multi-character.** Do not train two people into one LoRA. They average. Train separately and compose at generation time:

- **Regional conditioning** where the model supports it (image side).
- **Per-face detailer passes** — generate the scene without character LoRAs, then run a detailer per face with the relevant LoRA loaded. This is the most reliable route on image models.
- **Separate shots and cut between them** on video, where no regional conditioning exists across frames.

**Identity bleed rises with visual similarity.** Two characters of similar age, build and colouring will trade features far more than two who look nothing alike — worth knowing at casting time, when it is still cheap to change.
