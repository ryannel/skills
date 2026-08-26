# SCAIL-2 — identity: when it holds and when it breaks

This file owns identity: where it comes from in this model, how to hold it within a shot and across shots, the real multi-person limits, and the one thing SCAIL-2 cannot do at all. It does **not** own the mechanical procedure for building the reference — that is [`setup-and-workflows.md`](setup-and-workflows.md) §2 — and it does not own training a character, because **no training path exists for SCAIL-2**; that work belongs upstream, in the image model that makes your reference frame ([`character-lora-training`](../../character-lora-training/)).

## Contents

1. [Where identity comes from in this model](#1-where-identity-comes-from-in-this-model)
2. [Holding identity within a shot](#2-holding-identity-within-a-shot)
3. [Identity across shots](#3-identity-across-shots)
4. [What SCAIL-2 cannot do — a specific real face](#4-what-scail-2-cannot-do--a-specific-real-face)
5. [More than one person](#5-more-than-one-person)
6. [Objects and non-human subjects](#6-objects-and-non-human-subjects)
7. [Likeness, consent and adult work](#7-likeness-consent-and-adult-work)
8. [Failure modes](#8-failure-modes)

---

## 1. Where identity comes from in this model

Every other video model in this suite answers the same question: how do you keep a character consistent? They reach for some mix of a LoRA, a reference adapter, and prompt anchoring. **SCAIL-2 answers it differently, with one image and a segmentation track**, and that changes where your effort goes.

Here is the mechanism, stated plainly. A **reference image** plus its **foreground mask** supplies the appearance. A **SAM3 track** over the driving video supplies the per-frame region that appearance gets mapped onto. **In-Context Mask Conditioning** with **Mode-Specific RoPE** binds the two together inside one set of weights. There is no adapter to weight, no LoRA strength to sweep, and no trigger word.

Three consequences follow. Internalising them saves a lot of wasted iteration:

- **Identity work is preparation work.** By the time you press generate, identity is already decided. If the result is wrong, the reference was wrong — settings will not rescue it.
- **The prompt is not an identity lever.** Describing the character in the SCAIL-2 prompt does very little; the reference already carries the appearance. Compare [`minimax-h3`](../../minimax-h3/), where identity *is* prompt-anchored through a `retention_analysis` block. Getting that to hold took one practitioner 400+ generations `[community — Darqsat]`. SCAIL-2 saves you that entire class of work, at the price of requiring footage and a prepared frame.
- **Tracking failure is not identity failure.** The two look nothing alike once you know the difference. A drifting face is a conditioning problem. A subject the model never touches at all is a SAM3 problem, and no reference will fix that (see §8).

---

## 2. Holding identity within a shot

Ordered cheapest-first. Most shots are solved by the first two. **§2.2–§2.5 follow one practitioner's worked practice** `[community — nsfwVariant]`; where a claim has a different source, it is named on the spot.

### 2.1 Make the reference *be* the edited first frame

This is the one rule, and it is also the single strongest identity technique. Here is why it matters specifically for identity: it removes the correspondence problem from the earliest denoising steps. Without it, identity would be competing for capacity against pose, scale and framing at the same time. A studio portrait forces the model to solve *who* and *where* at once, and *who* is what loses `[community — blackmixture, LucidFir, ChairQueen; convergent]`.

Procedure: [`setup-and-workflows.md`](setup-and-workflows.md) §2.

### 2.2 Give it the back of the character too

Clothing and hair are the first attributes to drift, and they drift worst on turns. A front-only reference genuinely contains no information about the back, so the model invents it, and re-invents it each time the character rotates. *"For videos longer than 5 seconds, the clothes will morph into different clothes, especially if the character is turning around or doing different poses"* — reported by someone already using front *and* back references, so this is a mitigation rather than a cure `[community — zsnck; single report]`.

On the stock graph, you do this by **compositing the front and back views onto a single reference image**. The node's own tooltip is *"for multiple references composite all on single image"*, and mask colour is what separates them. (Community guidance to batch *n* references against *n* masks describes an alternate workflow.) Note the vendor's caveat: multi-reference is marked unoptimised — *"video qualities may degrade even though additional information do get referenced"*. You trade a little overall quality for attribute stability. On a turning character, that is usually the right trade.

### 2.3 Keep the shot short

Keep it under **~161 frames** unless the shot is easy. The stated reason is blast radius rather than quality — a fault chains forward into everything downstream. But shorter shots also give conditioning less distance over which to decay. Whether sliding context windows *restore* quality or *degrade adherence* to the driving video is genuinely contested between two credible practitioners ([`setup-and-workflows.md`](setup-and-workflows.md) §5.3 carries both reports). Plan as if adherence decays.

### 2.4 Give the model positional hints

Match the reference's screen position and zoom level to the clip's opening. Reorder a multi-reference batch if the wrong reference dominates. Both moves are the same idea as §2.1, applied to the details.

### 2.5 Fix what is left in post

The inserted character reading **too bright** and **too clear** for the plate is not an identity failure. **The vendor ships a LoRA for exactly this**: the **Relighting LoRA**, *"designed for replacement mode … making the reference character blend more naturally into the target video with consistent lighting and shadows"*. Load that first. Only grade in an NLE after a SAM3 re-mask if that is not enough. Hands, lips and eyes have their own official fix: the **Bias-Aware DPO** LoRA.

---

## 3. Identity across shots

**Cross-shot consistency is inherited from your reference stills, not from the model.** Each shot gets its own edited frame 0, and each edited frame 0 has to depict the same person. So the problem moves entirely upstream into the image model.

That is good news. The still-image side of this suite has the deepest identity tooling available anywhere:

- [`z-image/references/characters.md`](../../z-image/references/characters.md) — the fullest treatment in the suite: the edit-model engine versus the LoRA pipeline, the rotation protocol, multi-outfit ceilings.
- [`krea-2`](../../krea-2/) — Identity Edit, which is also the tool most named for SCAIL-2's frame-0 edit. Doing both jobs with one model is why this pairing dominates.
- [`flux-2`](../../flux-2/) — no-training multi-reference identity.
- [`sdxl`](../../sdxl/) — the deepest identity-adapter ecosystem (InstantID, IP-Adapter FaceID).
- [`character-lora-training`](../../character-lora-training/) — the craft that spans all of them.

**The practical workflow for a sequence:** lock the character once, as a trained identity or a reference set upstream. Then, for each shot, extract that shot's frame 0 and edit *that same character* into it. You are running the same edit N times against N different plates, not generating N different characters. Consistency of the edit prompt matters as much as consistency of the model — vary the wording and you will get variation in the result.

**A subtlety worth budgeting for:** shots differ in lighting, lens and framing, and a good frame-0 edit *preserves* those differences. Your reference for shot 7 will therefore look meaningfully different from your reference for shot 1. That is correct, not drift. Judge cross-shot consistency on the finished clips, not on the reference stills.

---

## 4. What SCAIL-2 cannot do — a specific real face

**Editing frame 0 changes who the person is. It does not reliably hit a named target likeness.** Someone asked directly, in the largest SCAIL-2 thread in the sweep — *"I'm struggling with turning a face into another face"* — and nobody answered `[community — Cre0na; single report]`. A second practitioner reports the same complaint in general form: *"My issue with SCAIL 2 is that it tends to change faces"* `[community — Zenshinn; single report]`.

This is not a settings problem and it is not a tracking problem. It follows from §1: identity arrives as a single image. A single image of a specific person, edited into an unfamiliar pose by an image-edit model, is already a lossy likeness before SCAIL-2 even sees it. The loss compounds.

**If you need a specific likeness to survive, fix it entirely upstream.** Build the identity properly on the image side — a trained character LoRA or a strong multi-reference identity setup. Use *that* to produce the frame-0 edit, and check the likeness in the still before you spend a generation on it. [`character-lora-training`](../../character-lora-training/) owns that work end to end; [`z-image`](../../z-image/) and [`sdxl`](../../sdxl/) own the deployment craft.

The routing rule, plainly: **SCAIL-2 is a performance-transfer model that happens to carry appearance, not an identity model that happens to move.** If the job is "this exact person, in a new context," start somewhere else and arrive here last.

---

## 5. More than one person

This is SCAIL-2's known weak spot. The honest summary: the community has measured it more carefully than the vendor has admitted to it.

**What the vendor admits:** multi-reference input is *"not optimized for such inputs"* and *"video qualities may degrade even though additional information do get referenced."* That is the whole of it. **No vendor document read acknowledges any multi-person artefact.**

**What the community reports:**

| Observation | Status |
|---|---|
| Non-target people in frame acquire an **outline or glow** | Reported previously; did not resurface in the most recent sweep, and never vendor-confirmed `[flagged — re-verify]` |
| **Box** selection over a crowded frame causes tracking problems; **Point** selection is the mitigation | [`masks-and-tracking.md`](masks-and-tracking.md) §3 owns this `[community — External_Trainer_213]` |
| Background crowd members **merge identities** — one figure runs behind another and emerges as a different person in a different shirt | Found in an independent audit of the model's own flagship showcase `[community — Draco18s]` |
| Terrain and scene detail change during an off-screen excursion | Same audit |
| Dual-person motion-transfer workflows exist and are published | `[community — T8star, Civitai]` |

**The mechanism to reason from.** Object permanence is a property of the **tracked subject**, not of the scene. SAM3 gives the model a persistent region for the people you selected. Everything else in frame is regenerated per segment, with no identity anchor at all. So "SCAIL-2 has good object permanence" and "background crowds mutate" are both true, and they are not in tension.

**Practical multi-person protocol** — steps 1–3 are core-node contracts `[official — PR #14373 diff]`:

1. Name the people you want in **`object_indices`** on `SCAIL2ColoredMask` — *"Comma-separated list of person indices to include (e.g. '0,2,3'). Applied to both reference and pose video masks. Empty = all"*. This is a core-node input, not a custom pack.
2. Set **`sort_by`** deliberately. It fixes *"the order in which palette colors are assigned … so each identity keeps the same color"* across both masks. **If two characters swap identities between reference and clip, this is the knob to turn.**
3. Composite every character onto **one** reference image. Colour, not batching, is what separates them. Point-select rather than box-select upstream in SAM3 when the frame is crowded.
4. Accept quality degradation as the price of the extra references, and shorten the shot to compensate.
5. **Where you can, separate them into different shots and cut.** This is the same advice [`wan-2-2`](../../wan-2-2/) gives for its own multi-character limits, and it remains the most reliable answer in the suite.
6. Do not budget for anyone you did not track. If a background figure must stay consistent, track them too, or keep them out of frame.

---

## 6. Objects and non-human subjects

This is worth knowing, because people discover it by accident, and because it changes what you consider this model for. SCAIL-2 replaces **objects** as readily as people, and the physics of the swap holds up better than expected. **This whole section rests on one practitioner's demonstrations** `[community — blackmixture]`.

The most-cited demonstration swapped a flower for a wine glass: *"Hand tracking stays locked, the liquid inside sloshes correctly for the motion, and because the glass is transparent the background actually refracts and distorts through the water"*. Another practitioner reports *"it can replace 6 ish objects perfectly and swap background all local"* `[community — Strange_Test7665]`.

Two things this tells you about the model:

- **The tracked region carries physical behaviour, not just texture.** The model generates plausible secondary physics on top of the motion it tracks — sloshing, refraction, cloth and hair follow-through, fire arcing off a fist with zero fire data in the driving clip. Motion is tracked; secondary physics is generated.
- **The weakness is symbolic content, not physical content.** **Text turns to mush.** Anything requiring glyph-level reconstruction inside the masked region — signage, screens, labels, logos — will not survive. Keep it outside the mask.

---

## 7. Likeness, consent and adult work

SCAIL-2 is the sharpest version of a problem the rest of this suite handles more gently: **it puts one person's appearance into existing footage of another person's body, following their real movement.** That is a different risk profile from generating a character from scratch, and it deserves a paragraph rather than silence.

**Before you publish anything made this way, read [`character-lora-training/references/publishing-and-likeness.md`](../../character-lora-training/references/publishing-and-likeness.md).** It owns the real-person rules that gate this work, including platform bans on real-person likenesses and the TAKE IT DOWN Act. Those rules govern the *output*, regardless of which model produced it. SCAIL-2's licence being permissive changes nothing about what you may lawfully do with a real person's likeness.

**On adult work, the suite's position is that it is first-class craft, and SCAIL-2 is currently the tool of choice for it.** The stack is fixed, and identical to the SFW one: **Flux 2 Klein 9B for the first-frame edit → SCAIL-2 for the animation** `[community — ChairQueen, Jayuniue]`. Two practical notes specific to this work, both from the same practitioner:

- **Reduce input resolution before you hit OOM, not after.** Long adult clips are where the unpredictable OOM bites hardest, and nobody has a formula — *"I still don't know how to calculate durationXresolutionXmodels&loras."*
- **Sharing is the friction, not generation.** The usual paste and file hosts either delete quickly or forbid the content. So these workflows circulate on the Civitai `.red` mirror rather than in the places you would look first.

The physics tracking that impresses people in SFW demos is the same mechanism doing the work here. It is one capability, not two.

---

## 8. Failure modes

| Symptom | Mechanism | Fix |
|---|---|---|
| Face gradually becomes someone else across the shot | Conditioning decays with distance from the anchor, and the anchor was already fighting a pose/scale mismatch at frame 0 | Make the reference the edited frame 0; shorten the shot; re-anchor per shot |
| Face is wrong from frame 1 | The reference itself does not depict the person you want — the loss happened in the image edit, not in SCAIL-2 | Fix it upstream and verify the still before generating (§4) |
| Clothes morph on turns, past ~5 s | A front-only reference contains no information about the back, so the model invents it and re-invents it each rotation | Front *and* back references with matching masks; shorter shots |
| Subject is never touched at all; tracker refuses to lock even on isolated close-ups | SAM3 produced no usable track. This is segmentation, not identity — rewording the prompt changes nothing | Point-select the subject rather than boxing it; supply a start image resembling the clip |
| Distant or full-body figures come out with mushed faces | The subject occupies too few pixels for the tracker to segment and the DiT to resolve | Pre-crop and zoom before generating, composite back after `[community — spiderofmars]` |
| Two characters trade features | Their palette colours are not being assigned consistently between the reference mask and the driving mask | Set `sort_by` explicitly on `SCAIL2ColoredMask` so each identity keeps one colour `[official — PR #14373 diff]`; failing that, separate shots and cut |
| Untracked background people mutate identity mid-shot | Object permanence is a property of the tracked region only; untracked figures are regenerated per segment with no anchor | Track them, or keep them out of frame |
| Character enters from off-screen and never resolves | No on-screen anchor exists at frame 0 to establish correspondence against | Process the shot in reverse, then re-reverse `[community — nsfwVariant]` |
| Character is right but looks pasted on | The inserted character is rendered without the plate's lighting and shadow | Load the vendor's **Relighting LoRA**, built for this; only then grade in post |
| Text on the character or in the region turns to mush | No glyph-level reconstruction is happening — this is the model's clearest weakness | Keep readable text outside the mask |
| Adding a second reference made everything slightly worse | Vendor-stated: multi-reference is unoptimised and degrades overall quality even while the extra information is used | Accept the trade, or drop back to one reference and shorten the shot |
| Extra references appear to do nothing at all | They were batched rather than composited — the node takes one reference image, with identities separated by mask colour | Composite them onto a single canvas |

**Not identity failures, and covered in [`SKILL.md`](../SKILL.md#failure-modes--qc)'s table instead:** hand distortion and lip/eye desync — the fix is the vendor's **Bias-Aware DPO** LoRA.
