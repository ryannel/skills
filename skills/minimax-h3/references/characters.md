# MiniMax H3 — characters and identity

H3 approaches identity differently from the rest of the suite, because **Ref2VA conditions on references directly** — including audio. There is no mature LoRA path here yet (see `loras-and-training.md`), so reference conditioning is not one option among several; it is essentially the option.

> This file reasons from the documented Ref2VA capability and the suite's established identity craft. The model is days old and there is no community consensus to draw on — treat the specifics as provisional `[flagged — re-verify]`.

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

## What H3 cannot do here that `wan-2-2` can

Stated plainly, because the gaps are real and this model is new:

| Capability | H3 | `wan-2-2` |
|---|---|---|
| Performance transfer from a driving video | Reference clips influence output, but there is no documented motion-transfer mode | **Animate** — purpose-built character animation and replacement |
| Pose / depth structural conditioning | No documented ControlNet-equivalent stack | **Fun Control** |
| Explicit camera trajectories | Prompt-level only | **Fun Camera** — discrete, repeatable moves |
| Trained character LoRA | Ecosystem too young | Established two-expert LoRA training |
| Lip-sync to a supplied track | Generates audio; does not follow an existing track | **S2V** consumes an audio track |

If the job is *"make this specific character do this specific thing, repeatably,"* `wan-2-2` currently has the better rig — and it is Apache 2.0. H3's advantage is that the character **speaks**, in a voice you supplied, with the sound of the scene around them, in one pass.

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
