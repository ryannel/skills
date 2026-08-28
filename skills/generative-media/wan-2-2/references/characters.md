# Wan 2.2 — consistent characters in motion

Character consistency in a video model is really **two problems**. People get stuck because they treat the two as one:

1. **Within a shot** — does the face stay the same face for 81 frames?
2. **Across shots** — is it the same person in clip 7 as in clip 1?

The two problems have different causes and different fixes. Within-shot drift is a conditioning-decay problem. Across-shot drift is an identity-definition problem, and it is the harder of the two.

---

## Start with the still — the handoff that does most of the work

**The highest-leverage move is not a video technique.** Wan's I2V path is substantially stronger than its T2V path. An image model also gives you far more control over a face than any video prompt can. With stills you can iterate cheaply, inpaint, run a face detailer, and use the whole mature still-image identity stack.

So the pipeline is:

> **establish the character as a still** → **I2V from that still** → repeat per shot from a fresh still

Everything involved in creating that character is already covered in depth on the image side. That includes the anchor image, the edit-model dataset factory, rotation and expression coverage, character LoRA training, and detailer deployment. Do not re-derive it here. Instead, use these references:

- [`z-image/references/characters.md`](../../z-image/references/characters.md) — the fullest treatment in the suite. It covers the two paths (edit-model engine vs LoRA pipeline) and how they chain, the 8-point rotation protocol, multi-outfit ceilings, and multi-character limits.
- [`flux-2`](../../flux-2/) — no-training multi-reference identity, if you want to skip LoRA training entirely.
- [`sdxl`](../../sdxl/) — the deepest identity-adapter ecosystem (InstantID, IP-Adapter FaceID).

**Across-shot consistency is then inherited from the stills.** If every shot starts from a frame of the same trained character, cross-shot identity is as good as your still pipeline. That is much better than anything you can achieve prompt-side in video. It is also the concrete payoff of keeping image and video skills in one suite.

---

## Holding identity within a shot

These techniques are ordered cheapest-first. Most jobs are solved before you reach the bottom of the list.

### 1. Shorten the clip

Conditioning influence decays as the clip progresses. The further a frame is from the anchor, the less the reference constrains it. An 81-frame clip that morphs at frame 60 will usually be clean at frame 40. Two shorter clips re-anchored on fresh stills beat one long clip that degrades, and the shorter clips cut cleanly.

### 2. VACE reference conditioning

This is the no-training path. You supply reference imagery that conditions the whole clip rather than only its first frame. This directly attacks the decay mechanism, which is why it became the default consistent-character method on Wan 2.1. See `motion-and-camera.md`.

### 3. Animate, for a specific performance

Use Animate when you need this character doing *this exact motion*. Transfer the performance from a driving video rather than describing it in the prompt. The relight LoRA is what makes an inserted character sit in the scene's lighting instead of looking pasted in.

If the job is specifically *replacing* someone already in footage, rather than driving your own character, use [`scail-2`](../../scail-2/) instead. It has displaced Animate for that job in community practice. Note that it is a Wan 2.1 fine-tune from zai-org, so it is a separate download and a separate graph, not a mode of this model.

### 4. Character LoRA on Wan itself

This is the most expensive option and the most flexible one. The character becomes summonable by prompt in arbitrary new contexts, with no reference needed per shot.

**Remember the two-expert rule.** A Wan 2.2 character LoRA is a high-noise/low-noise **pair**. Loading only one half is a common cause of "the LoRA sort of works": identity gets applied at one end of the schedule and not the other. See `lora-training.md`.

**Which expert carries identity?** Facial identity is largely a late-denoising, detail-domain property, so the low-noise LoRA does most of the visible identity work. The high-noise LoRA governs how the character is posed and how it moves. If your character looks right but moves generically, that asymmetry is the reason `[community — re-verify]`.

---

## Multi-character scenes

Multi-character scenes are harder than in still models, and it is worth being blunt about why: **there is no regional conditioning across frames.** Image-side tools let you condition regions independently. Wan conditions globally. The consequences:

- **Identity bleed** between characters is likely, and it rises with visual similarity. Two people of similar age, build and colouring will trade features.
- **Two character LoRAs at once** compounds this. Both apply globally, so both influence both faces.
- The practical approach is **compositional**: keep characters in separate shots and cut between them. Alternatively, start from a still where both faces are already correct, and keep the clip short enough that neither face drifts.
- Per-face repair is a **post** step: extract frames, fix faces with the image stack, and re-encode. This is expensive, and it risks temporal flicker unless the fix is applied consistently across every frame.

---

## Failure modes

| Symptom | Mechanism | Fix |
|---|---|---|
| Face gradually becomes someone else | Conditioning decay over clip length | Shorter clips; VACE reference conditioning; re-anchor per shot |
| Identity right, motion generic | Low-noise LoRA applied, high-noise missing or weak | Load both halves; check the high-noise LoRA trained at all |
| Character correct in shot 1, different in shot 5 | Each clip conditioned on a different starting frame | Anchor every shot on stills of the *same* trained character |
| Two characters trade features | Global conditioning, no regional control | Separate shots; shorter clips; accept per-face post repair |
| Expression locked flat across the clip | Over-fitted LoRA, or a neutral anchor with no expression in the prompt | Reduce LoRA strength; name the expression change as an action |
| Face fine, hands and body wrong | Identity training concentrates on faces; body is under-constrained | Frame tighter, or drive the body with Fun Control / Animate |
| Character reverts to a generic face mid-clip | LoRA strength too low to hold against motion, or prompt drifting from training distribution | Raise strength on the low-noise half; match prompt phrasing to captions |
