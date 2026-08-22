# MiniMax H3 — characters and identity

H3 approaches identity differently from the rest of the suite, because **Ref2VA conditions on references directly** — including audio. There is no mature LoRA path here yet (see [`lora-training.md`](lora-training.md)), so reference conditioning is not one option among several; it is essentially the option.

> Most of this file reasons from the documented Ref2VA capability and the suite's established identity craft `[flagged — re-verify]`. The sections marked `[community]` were added 2026-08-22 from a sweep of named practitioners and are firmer.

---

## The Ref2VA budget

The constraint that shapes everything:

- ≤ **9 images**
- ≤ **3 video clips**, each 2–15 s
- ≤ **3 audio clips**, each 2–15 s
- ≤ **12 files total**, total duration ≤ 15 s

Twelve files is the real ceiling. Nine identity images plus a voice clip plus two style/motion clips already hits it, so **the reference set is a budget to allocate**, not a bucket to fill. Decide what the shot most needs to pin down before spending slots.

A defensible default allocation for a character shot:

| Slots | Spend on |
|---|---|
| 4–6 images | Identity — the face across angles and expressions |
| 1 audio | The voice |
| 1–2 images | Wardrobe or setting, if they must match |
| remainder | Held back — more references is not monotonically better |

---

## Build the identity as stills first

The suite's strongest identity work lives on the image side, and it feeds H3 the same way it feeds `wan-2-2`. Generate a consistent character with an image model, curate the best angles, and pass **those** as Ref2VA images rather than hoping H3 invents a consistent face.

- [`z-image/references/characters.md`](../../z-image/references/characters.md) — the fullest treatment in the suite: the edit-model dataset factory, the 8-point rotation protocol, multi-outfit ceilings, and the failure modes of character LoRAs
- [`flux-2`](../../flux-2/) — no-training multi-reference identity
- [`sdxl`](../../sdxl/) — the deepest identity-adapter ecosystem

Curate for **angle and expression coverage**, not for the nine prettiest images. Nine near-identical frontal portraits pin down one pose; four angles plus two expressions pin down a person.

### Size the references by importance `[community]`

Reference pixel size acts as a weighting. A working allocation: **character ~1000 px, environment ~500 px, prop ~300 px** on the long side. Supply a reference for anything unusual — H3 knows *named* characters and franchises deeply and generic-but-specific objects (an unusual weapon, a particular tool) barely at all. `[community — erioca]`

Related, and easy to miss: **H3's pre-trained knowledge of named characters is broad enough that people maintain lists of it** (a "MiniMax H3 Known Characters" list is being kept on Hugging Face by `malcolmrey`, v2 dated 2026-08-21). If your character is famous, naming them may beat referencing them — and if you are using a *projected* text encoder rather than the full 32B, naming them will actively hurt, because the smaller sibling remembers them wrongly. See `setup-and-workflows.md` §5.

### Let H3 build its own reference sheet `[community]`

H3's own knowledge can bootstrap the reference set: feed up to 9 mediocre images and have it generate a **360° turnaround**, then cut that into a character sheet.

`PoopMan333/H3_Character_Sheet_Generator` does exactly this — your description plus a fixed "B prompt" that spins the character slowly with no hard cuts, output as a 4- or 6-panel sheet plus the individual frames. Caveats from the author, which are the honest part:

- It generates **124 frames to use 6**. The 4-panel variant is ~40% cheaper.
- Turbo LoRAs speed it up but **cost prompt adherence** — reroll rather than fight it.
- It is a video model making stills, so **resolution limits detail**. Pair the sheet with dedicated close-ups of face and clothing for close shots; for a one-off clip you may be better off skipping the sheet entirely.
- The stock B prompt specifies a **neutral A-pose** — delete that clause for anything else.
- Works for props and objects too, with prompt changes.

Two things follow. First, this is a dataset factory in the [`z-image` sense](../../z-image/references/characters.md) that happens to run on a video model — see [`character-lora-training`](../../character-lora-training/) for what to do with the frames. Second, hybrid FL2VA/Ref2VA checkpoints are prone to **dragging the sheet's white background into the shot**; matte it or state the environment.

---

## The voice is part of the identity

This is what H3 adds that nothing else in the suite has. A character is a face *and* a voice, and Ref2VA takes both.

- **One good clip beats three mediocre ones.** Clean speech, no music bed, no overlapping speakers, 2–15 s.
- **Match the register you want.** A reference clip of calm narration will not deliver a shouted line convincingly.
- **Say what the reference is for.** Local runs bypass Context-IR, so name the association explicitly — *"the voice from audio 1"* — rather than assuming the model infers which reference plays which role.

Across shots, reusing the same audio reference is what makes the character sound like one person. That is the audio analogue of anchoring every shot on stills of the same trained character.

---

## Across shots

The 15-second ceiling makes any real sequence a multi-shot problem, and identity has to survive the cuts.

**Reuse the same reference set.** The set is the identity definition — vary the prompt, not the references. Swapping in different images between shots is the most likely way to get a character who drifts.

**Re-anchor rather than extend.** Each shot is its own Ref2VA generation from the same references, not a continuation of the previous clip. This avoids the error-accumulation drift that plagues extended generation — see [`wan-2-2`'s stitching notes](../../wan-2-2/references/setup-and-workflows.md).

**Expect the voice to drift more than the face.** Vocal timbre from a short reference is a thinner constraint than facial identity from six images. If continuity of voice matters across a long piece, consider generating dialogue-heavy shots close together, and check them against each other rather than against the reference alone.

---

## What H3 cannot do here — and which sibling does

Stated plainly, because the gaps are real and this model is new:

| Capability | H3 | [`wan-2-2`](../../wan-2-2/) |
|---|---|---|
| Performance transfer from a driving video | Reference clips influence output, but there is no documented motion-transfer mode | **Animate** — purpose-built, but no longer the first reach; see the note under the table |
| Pose / depth structural conditioning | No documented ControlNet-equivalent stack | **Fun Control** |
| Explicit camera trajectories | Prompt-level only | **Fun Camera** — discrete, repeatable moves |
| Trained character LoRA | Ecosystem too young | Established two-expert LoRA training |
| Lip-sync to a supplied track | Generates audio; does not follow an existing track | **S2V** consumes an audio track |

**The first row is the one where neither column is the answer any more.** For replacing a person in footage that already exists, [`scail-2`](../../scail-2/) has displaced Wan **Animate** in community practice. It tracks the driving clip frame for frame with SAM3 identity masks rather than transferring a performance onto a fresh render — the difference between a cut that *matches* the plate and one that merely resembles it, which is exactly the axis H3 loses on too. Wan **Animate** stays the in-family alternative when you are already running Wan end to end and would rather not add a third checkpoint stack. The price of going to SCAIL-2 is everything this page is about: it has **no audio in either direction**, it cannot originate a shot, and it needs you to lock frame 0 with an image edit first. So the route is *identity → SCAIL-2* when the footage exists, and *identity → H3* when the shot does not yet.

For the rest of the table — pose and depth conditioning, explicit camera paths, a trained character LoRA, lip-sync to a supplied track — the routing is unchanged: if the job is *"make this specific character do this specific thing, repeatably,"* [`wan-2-2`](../../wan-2-2/) currently has the better rig, and it is Apache 2.0. H3's advantage is that the character **speaks**, in a voice you supplied, with the sound of the scene around them, in one pass.

---

## Failure modes

| Symptom | Likely cause | Direction of fix |
|---|---|---|
| Face inconsistent across shots | Reference set varied between generations | Freeze the reference set; vary only the prompt |
| Voice doesn't resemble the reference | Reference clip too short, noisy, or in a different register | One clean 2–15 s clip in the target register |
| References seem ignored | Roles not stated; Context-IR would have resolved them, and it is absent locally | Name each reference's job explicitly in the prompt |
| Identity degrades late in the clip | Conditioning influence decaying over duration — the standard temporal failure | Shorter clips; re-anchor per shot |
| Wardrobe or setting drifts | Slots spent on identity only | Reallocate the 12-file budget to include wardrobe/setting references |
| Multiple characters trade features | Global conditioning with no regional control — same limitation as the rest of the field | Separate shots per character; keep clips short |
