# MiniMax H3 — characters and identity

H3 handles identity differently from the rest of the suite. **Ref2VA conditions on references directly**, and those references can include audio. There is no mature LoRA path for H3 yet (see [`lora-training.md`](lora-training.md)). That means reference conditioning is not one option among several. It is essentially the only option.

> Most of this file reasons from the documented Ref2VA capability and the suite's established identity craft `[flagged — re-verify]`. The sections marked `[community]` were added 2026-08-22 from a sweep of named practitioners, and they are firmer.

---

## The Ref2VA budget

One constraint shapes everything else in this file:

- ≤ **9 images**
- ≤ **3 video clips**, each 2–15 s
- ≤ **3 audio clips**, each 2–15 s
- ≤ **12 files total**, total duration ≤ 15 s

Twelve files is the real ceiling. Nine identity images plus a voice clip plus two style or motion clips already hits it. Treat **the reference set as a budget to allocate**, not a bucket to fill. Before you spend any slots, decide what the shot most needs to pin down.

Here is a defensible default allocation for a character shot:

| Slots | Spend on |
|---|---|
| 4–6 images | Identity — the face across angles and expressions |
| 1 audio | The voice |
| 1–2 images | Wardrobe or setting, if they must match |
| remainder | Held back — more references is not monotonically better |

---

## Build the identity as stills first

The suite's strongest identity work lives on the image side, and it feeds H3 the same way it feeds `wan-2-2`. Generate a consistent character with an image model first. Curate the best angles. Then pass **those** images to Ref2VA, rather than hoping H3 invents a consistent face on its own.

- [`z-image/references/characters.md`](../../z-image/references/characters.md) — the fullest treatment in the suite. It covers the edit-model dataset factory, the 8-point rotation protocol, multi-outfit ceilings, and the failure modes of character LoRAs.
- [`flux-2`](../../flux-2/) — identity from multiple references, with no training
- [`sdxl`](../../sdxl/) — the deepest identity-adapter ecosystem

Curate for **angle and expression coverage**, not for the nine prettiest images. Nine near-identical frontal portraits pin down one pose. Four angles plus two expressions pin down a person.

### Size the references by importance `[community]`

Reference pixel size acts as a weighting. A working allocation is **character ~1000 px, environment ~500 px, prop ~300 px** on the long side. Supply a reference for anything unusual. H3 knows *named* characters and franchises deeply, but it barely knows generic-but-specific objects, such as an unusual weapon or a particular tool. `[community — erioca]`

A related point is easy to miss: **H3's pre-trained knowledge of named characters is broad enough that people maintain lists of it**. A "MiniMax H3 Known Characters" list is being kept on Hugging Face by `malcolmrey`, with v2 dated 2026-08-21. If your character is famous, naming them may work better than referencing them. But if you are running a *projected* text encoder rather than the full 32B, naming them will actively hurt, because the smaller sibling remembers them wrongly. See `setup-and-workflows.md` §5.

### Let H3 build its own reference sheet `[community]`

H3's own knowledge can bootstrap the reference set. Feed it up to 9 mediocre images and have it generate a **360° turnaround**, then cut that video into a character sheet.

`PoopMan333/H3_Character_Sheet_Generator` does exactly this. It combines your description with a fixed "B prompt" that spins the character slowly with no hard cuts, and it outputs a 4- or 6-panel sheet plus the individual frames. The author lists several caveats, and they are the honest part:

- It generates many frames to keep a few. The 2026-08-29 update cut the 4-panel turnaround from 124 frames to **73**, roughly 40% faster, running 8 steps with the speed-up stack. `[community — PoopMan333; re-verify]`
- Turbo LoRAs speed it up, but they **cost prompt adherence**. Reroll rather than fight it.
- It is a video model making stills, so **resolution limits detail**. Pair the sheet with dedicated close-ups of face and clothing for close shots. For a one-off clip, you may be better off skipping the sheet entirely.
- The stock B prompt specifies a **neutral A-pose**. Delete that clause for anything else.
- It works for props and objects too, with prompt changes.

Two things follow from this. First, this is a dataset factory in the [`z-image` sense](../../z-image/references/characters.md) that happens to run on a video model. See [`character-lora-training`](../../character-lora-training/) for what to do with the frames. Second, hybrid FL2VA/Ref2VA checkpoints are prone to **dragging the sheet's white background into the shot**. Matte it out, or state the environment in the prompt.

---

## The voice is part of the identity

This is what H3 adds that nothing else in the suite has. A character is a face *and* a voice, and Ref2VA takes both.

- **One good clip beats three mediocre ones.** Use clean speech with no music bed and no overlapping speakers, 2–15 s.
- **Match the register you want.** A reference clip of calm narration will not deliver a shouted line convincingly.
- **Say what the reference is for.** Local runs bypass Context-IR, so the model will not infer which reference plays which role. Name the association explicitly, for example *"the voice from audio 1"*.

Across shots, reusing the same audio reference is what makes the character sound like one person. It is the audio analogue of anchoring every shot on stills of the same trained character.

---

## Across shots

The 15-second ceiling makes any real sequence a multi-shot problem, and identity has to survive the cuts.

**Reuse the same reference set.** The set is the identity definition. Vary the prompt, not the references. Swapping in different images between shots is the most likely way to end up with a character who drifts.

**Re-anchor rather than extend.** Each shot is its own Ref2VA generation from the same references, not a continuation of the previous clip. This avoids the error-accumulation drift that plagues extended generation. See [`wan-2-2`'s stitching notes](../../wan-2-2/references/setup-and-workflows.md).

**Expect the voice to drift more than the face.** Vocal timbre from a short reference is a thinner constraint than facial identity from six images. If continuity of voice matters across a long piece, generate the dialogue-heavy shots close together, and check them against each other rather than against the reference alone.

---

## Holding a face without a LoRA — what survived live use

The advice above was tested in anger across live sessions in late August 2026. These findings are first-party, not community reports, and they are the current best practice for this file.

**Framing sets a hard ceiling on likeness.** At 768p, a full-body frame leaves the face too few pixels to carry an identity. No reference set fixes that, however the references are driven. The fix is framing, not more references. Frame thigh-up or closer for any shot where the face must read as the character. When the story needs a wide shot, accept a generic face in it and cut to a closer shot for recognition.

**References help only when they agree with the anchor image.** In an A/B test, a reference that mismatched the start frame made likeness worse, not better. The best neutral face reference is a crop of the start frame itself. The recipe that held: matched references, a pinned anchor frame, and restrained motion.

**For sequences, re-inject identity at every keyframe.** Likeness drift compounds when each clip extends the last. This chain beat it without any H3 LoRA:

1. Take the previous true frame.
2. Run an H3 micro-jump: a 5-frame clip in the same scene, keeping only the last frame.
3. Pass that frame through a light img2img identity pass with a character **image** LoRA at denoise ~0.4. Backgrounds survive denoise 0.4–0.55.
4. Use the result as the next keyframe.

Drift cannot compound, because identity re-enters at every link. The image-side LoRA comes from [`character-lora-training`](../../character-lora-training/).

**A character LoRA does not replace references.** When you have one, use both together. The LoRA anchors the identity. The references stop the model inventing detail the LoRA does not carry.

---

## What H3 cannot do here — and which sibling does

The gaps are real and this model is new, so here they are, stated plainly:

| Capability | H3 | [`wan-2-2`](../../wan-2-2/) |
|---|---|---|
| Performance transfer from a driving video | Reference clips influence output, but there is no documented motion-transfer mode | **Animate** — purpose-built, but no longer the first reach; see the note under the table |
| Pose / depth structural conditioning | No documented ControlNet-equivalent stack | **Fun Control** |
| Explicit camera trajectories | Prompt-level only | **Fun Camera** — discrete, repeatable moves |
| Trained character LoRA | Ecosystem too young | Established two-expert LoRA training |
| Lip-sync to a supplied track | Generates audio; does not follow an existing track | **S2V** consumes an audio track |

**In the first row, neither column is the answer any more.** For replacing a person in footage that already exists, [`scail-2`](../../scail-2/) has displaced Wan **Animate** in community practice. SCAIL-2 tracks the driving clip frame for frame using SAM3 identity masks, rather than transferring a performance onto a fresh render. That is the difference between a cut that *matches* the plate and one that merely resembles it, and that is exactly the axis H3 loses on too. Wan **Animate** remains the in-family alternative when you are already running Wan end to end and would rather not add a third checkpoint stack. Going to SCAIL-2 costs you everything this page is about: it has **no audio in either direction**, it cannot originate a shot, and it needs you to lock frame 0 with an image edit first. So the route is *identity → SCAIL-2* when the footage exists, and *identity → H3* when the shot does not exist yet.

For the rest of the table — pose and depth conditioning, explicit camera paths, a trained character LoRA, lip-sync to a supplied track — the routing is unchanged. If the job is *"make this specific character do this specific thing, repeatably,"* [`wan-2-2`](../../wan-2-2/) currently has the better rig, and it is Apache 2.0. H3's advantage is that the character **speaks**, in a voice you supplied, with the sound of the scene around them, in one pass.

---

## Failure modes

| Symptom | Likely cause | Direction of fix |
|---|---|---|
| Face inconsistent across shots | Reference set varied between generations | Freeze the reference set; vary only the prompt |
| Face soft or generic in a full-body shot | Too few face pixels at 768p — a framing ceiling, not a reference problem | Frame thigh-up or closer; cut in for recognition instead of adding references |
| Likeness got *worse* after adding a reference | The reference disagrees with the anchor image | Use only references that match the anchor; a crop of the start frame is the best neutral face reference |
| Likeness drifts across a chained sequence | Drift compounds when each clip extends the last | Re-anchor identity at every keyframe — the micro-jump chain above |
| Voice doesn't resemble the reference | Reference clip too short, noisy, or in a different register | One clean 2–15 s clip in the target register |
| References seem ignored | Roles not stated; Context-IR would have resolved them, and it is absent locally | Name each reference's job explicitly in the prompt |
| Identity degrades late in the clip | Conditioning influence decaying over duration — the standard temporal failure | Shorter clips; re-anchor per shot |
| Wardrobe or setting drifts | Slots spent on identity only | Reallocate the 12-file budget to include wardrobe/setting references |
| Multiple characters trade features | Global conditioning with no regional control — same limitation as the rest of the field | Separate shots per character; keep clips short |
