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

**15–30 well-curated images beat 100 mediocre ones.** This is one of the more consistent findings across trainers and families. NanashiAnon puts the Illustrious-era single-outfit figure at 20–30; L3n4's crash course says "a well-curated 30–50 beats a poorly curated 500" `[community — NanashiAnon, L3n4/Civitai 25645; convergent]`. It holds because a big dataset does not fail by having too much data. It fails by having variance nobody controlled — and every inconsistency you did not caption is something the model tries to learn.

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

Rear angles matter more than people expect. Without them the model has no idea what the back of the head looks like, so it improvises — usually badly, and usually at the worst moment.

**Elevation.** At least one above eye level and one below. A dataset shot entirely at eye level produces a character that distorts the moment you ask for a high or low angle.

**Shot size.** Close-up, medium, and full body. A face-only dataset gives you a character with an unreliable body; a full-body-only dataset gives you a face that dissolves at distance.

**Expression.** Neutral plus at least two others. Otherwise expression locks, and the character can only ever wear the face it was trained on. That reads as uncanny well before anyone can say why.

**Lighting and setting.** Vary both, or they become part of the identity and every generation inherits the dataset's lighting.

**The one-clause rule.** When you generate a dataset, keep the character description **byte-identical** and change only the clause you are covering — rotation, or shot size, or expression. Anything else that drifts between images is variance, and the model will try to attribute it to the character. `[community — Civitai dataset guides 7777/21257/21114; convergent]`

---

## 3. The synthetic dataset factory

The now-standard route, and the one to prefer for anything you intend to publish:

1. **Lock an anchor image.** One image that defines the character. Iterate here as long as it takes — everything downstream inherits it, and no amount of training fixes a weak anchor.
2. **Generate the varied set with an edit model**, driving it from the anchor and changing one clause at a time, per §2. An edit model holds an identity across an edit far better than a text prompt holds it across separate generations.
3. **Over-generate and curate down.** Produce roughly twice what you need and cut to the best — perhaps 60 down to 30. Curation is where dataset quality actually comes from.
4. **Caption per §4.**
5. **Train, evaluate, and expect to revisit the dataset** rather than the hyperparameters when results disappoint.

There are two advantages beyond convenience. You get **coverage photography rarely gives you** — a real photo set almost never has all eight rotations under matched lighting. And the character **resembles nobody**, which removes the likeness problem described in [`publishing-and-likeness.md`](publishing-and-likeness.md) entirely.

Which edit model to use for step 2 is a per-family question; your model skill names the one for its ecosystem.

**Someone has packaged the whole loop.** VNCCS 3.0 — the Visual Novel Character Creation Suite — is a ComfyUI system that wires steps 1–3 together `[community — AHEKOT, r/StableDiffusion 892 pts]`. What you get over building it yourself: a **Control Center** that downloads and manages the models the workflows need, an interactive 3D **Pose Studio** for posing, framing, lighting and pose libraries, a **Character Cloner** that builds the anchor from reference images, a **Clothes Designer** that copies an outfit onto different characters, an **Emotion Studio** for expression sets, and **per-sprite regeneration**, so one bad frame does not cost you the sheet. Install via `github.com/AHEKOT/VNCCS_Easy-Install` `[official — repo README, read 2026-08-23]`.

Settle two things before you train on its output. Its generation stack is reported to be built around **Anima-Base-1.0** `[community — AHEKOT; re-verify]`, so the stills inherit that model's look and its weights-side licence — check [`anima`](../../anima/) before publishing anything trained on them. And it aims at a **visual-novel sprite sheet**, which is a different coverage target from §2: it optimises for expression and outfit variety, and leaves rotation and elevation for you to check. Curate its output against §2 rather than assuming a finished sheet is a finished dataset.

### Feeding a new LoRA with an old one's pictures — when it helps, when it wrecks the run

Using your previous version's output to fill a coverage hole is just the factory above pointed at your own back catalogue, and it is a fair move: the identity is already locked, you have full provenance, and it is often the only way to get angles a photo set never had. **The question to ask is whether the old LoRA was actually good at the exact thing you are borrowing.**

That question fails more often than it sounds, for an annoying reason: the hole you are filling now is usually the same hole the old model had. The coverage was missing back then too — that is *why* it never learned those angles. So harvesting its profile and rear views to fix your profile and rear coverage means training the new version on the old version's guesses about the one thing it could not do. The new model treats those angles as fact, cannot do better than them, and never shows you the ceiling, because nothing in its data disagrees.

Two rules keep this honest:

- **Look at the candidates full size, next to the real references, before you decide.** Not as thumbnails. Model artefacts are invisible at contact-sheet size and permanent once trained: over-baked traits (above), plastic skin, a softness the original photos never had.
- **If you started over because the old one was not good enough, seeding from it contradicts the reason you started over.** "Fresh start" and "keep the old model's characteristics" are opposite instructions. A fresh line built on the old one's pictures is just the old line again, with extra steps. When the coverage genuinely cannot be got any other way, the honest move is to train without it and write down which prompts failed — that list is the spec for your next dataset. A gap you documented beats one you invented.

Seeding earns its place when the old model was strong where you are borrowing and weak somewhere else. That is a different situation, and worth deciding on purpose rather than by whether the pictures happen to be lying around.

### The video turnaround — a better factory for rotation specifically

An edit model generates each angle separately, so eight edits give the identity eight chances to drift. **A video model generates them as one continuous camera move.** The angles then come out consistent because of how they were made, not because you curated them. On the hardest axis of §2, that is a different kind of answer — not just a convenience.

The recipe: feed a handful of imperfect references into a reference-conditioned video mode — [`minimax-h3`](../../minimax-h3/)'s Ref2VA is the worked example — with a prompt that spins the character **slowly through 360°, with no cuts**. Then pull out the frames. There is a packaged workflow for it: `PoopMan333/H3_Character_Sheet_Generator` `[community — PoopMan333, Civitai]`.

Three caveats decide whether it is worth it:

- **It is expensive in generated frames.** The packaged workflow generates **124 frames to keep 6**. You are paying video-generation cost for a still dataset.
- **Video stills are lower-detail than image stills.** Pair the turnaround with dedicated close-ups from an image model before training, or the LoRA learns a slightly soft face.
- **Check the licence of the model you harvest from.** Some open video licences restrict using their output to train other models. [`ltx-2-5`](../../ltx-2-5/)'s Attachment A ¶18 does exactly that, and how far it reaches into non-commercial work is unsettled `[contested]`. A dataset factory is precisely the use that sits in that gap, and the LoRA you end up with is the thing that carries the problem forward.

The trick works on any video model with reference conditioning. So do the caveats.

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

Getting this backwards is a common reason a LoRA "trained fine but won't trigger".

**When a trait belongs to the person but still changes, caption whatever changes it.** Caption-the-residual has a blind spot the table above hides: some things are clearly part of the identity *and* clearly variable. Freckles are the tidy example. They belong to her, so the rule says never name them — but they fade under foundation, so a set shot over both bare-faced and made-up days contains two versions of her skin.

Leaving both unnamed does not quietly average out. The model has to blame the difference on *something*, and it picks whatever else happens to line up: the formal dress that shows up in the made-up shots, or the indoor light, or the year. You end up with a character who mysteriously loses her freckles in evening wear.

The fix is to name the **cause** — which is not part of the identity, and does change — and leave the trait unnamed:

| | Caption it? | What you get |
|---|---|---|
| The freckles (the trait) | **Never** | They stay part of `<trigger>` — the default face |
| The makeup (the cause) | **Wherever you can see it** | A switch you can flip: add "wearing foundation" when you generate, and the freckles fade, exactly as they do in the photos |

Caption the **exception, not the rule.** If most of the set is bare-faced, leave bare-faced unmentioned so it becomes the default, and put a makeup clause only on the made-up images. The same shape covers tan lines, glasses, a beard grown and shaved, hair up or down, a necklace she always wears — anything where "is this the person, or is this a variable?" answers *both*. Ask what nameable thing changes it, and caption that `[community — production practice; convergent with the caption-the-residual mechanism]`.

The opposite mistake is common and real: **naming the trait in your generation prompts bakes it in too hard.** One character LoRA whose synthetic set was made with "freckles across her face and body" in every prompt learned heavy, even freckling all over her — far more than the real person had. The words were in the caption *and* the thing was in every image, so it got taught twice. If a trait is part of the identity, let the pictures teach it and control it through its cause.

**Using the same words matters more than using rich ones.** Call it "three-quarter view" in one caption and "angled slightly away" in another, and you have split one concept into two. Pick your terms and reuse them exactly.

**Keep caption length even across the set.** If some images get three words and others get forty, the short ones carry more weight than you intended, in ways that are hard to predict.

**Training with no captions at all is contested.** Some trainers run DiT character LoRAs that way and report good replication. It does work for pure replication, but you give up control: you cannot vary what you never named. Treat it as a specialised technique, not a default. `[contested]`

---

## 5. Multi-outfit and multi-character

**Multi-outfit.** One character LoRA can hold several distinct outfits, as long as each gets its own trigger tag, looks clearly different from the others, and has enough coverage of its own. The practical ceiling is around **six outfits** before they start bleeding together `[community — Khanykov01, Civitai 6990; strong]`. Past that, use separate LoRAs, or stack an outfit LoRA onto the character.

The failure is lopsided: outfits bleed into each other long before the identity suffers. If your character starts wearing a mix of two outfits, that is the ceiling announcing itself.

**Multi-character.** Do not train two people into one LoRA. They average. Train separately and compose at generation time:

- **Regional conditioning** where the model supports it (image side).
- **Per-face detailer passes** — generate the scene without character LoRAs, then run a detailer per face with the relevant LoRA loaded. This is the most reliable route on image models.
- **Separate shots and cut between them** on video, where no regional conditioning exists across frames.

**Identity bleed goes up with visual similarity.** Two characters of similar age, build and colouring trade features far more than two who look nothing alike. Worth knowing at casting time, while it is still cheap to change.

### Differential Output Preservation — a training-time answer, on some models

Everything above assumes composing at generation time is your only lever. Since mid-2026 there is a **training**-side option too, though it depends on the model in a way that matters.

**Differential Output Preservation** (DOP) trains each character LoRA against a **class**, such as `"woman"`. It preserves the base model's output for that class while learning the individual. Several such LoRAs can then load together in one generation with very little bleed. A reproducible recipe: a LoKr config with DOP enabled, class `"woman"`, **1500 steps** rather than 750 (previews stabilise around 1500) `[community — MASilverHammer, r/StableDiffusion]`.

Boundaries, from the same source:

- **Hard cap of four characters.** Five falls apart; four holds.
- Characters **borrow features from each other**, with lips the reported offender, so similar-looking characters drift toward looking related. The similarity rule above still applies. It is just less punishing.
- **Prompt the distinguishing features.** Naming what separates two characters (a long nose, a jawline) is what keeps them separated at inference.
- Captioning still matters. The author's lazily-captioned sets (trigger word only) worked; their well-captioned set produced the more resilient LoRA.

**The model-dependence is the important part.** The same technique **failed on Z-Image Base**, where DOP stopped the character being learned at all, and **worked on Krea 2**. Do not assume it transfers. If a multi-character job is the requirement, that is now a reason to choose the base model on this axis specifically: see [`krea-2/references/characters.md`](../../krea-2/references/characters.md). Above four characters, or on a model where DOP does not take, fall back to per-face detailer passes.
