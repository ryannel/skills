# LTX-2.5 — characters and identity

This file covers how to keep a person looking like the same person. That means two problems: holding identity across frames within a clip, and holding it across a **cut**. The cut is the harder problem, and it is the one LTX's headline feature creates. Training the adapters mentioned here is covered in [`lora-training.md`](lora-training.md). The prompt mechanics are in [`prompting-guide.md`](prompting-guide.md).

## 1. The honest lead: there is no reference-to-video mode

LTX-2.5 has no ref2vid. You cannot hand it a photograph of a person and ask for a clip of that person. This is the single most-cited reason practitioners move to [`minimax-h3`](../../minimax-h3/) and stay there:

> *"multishot is awesome but unfortunately need to stick with H3 for native references. Otherwise would use this as default."* `[community — rk1213]`

Two more people asked the vendor account directly on release day. One asked *"Do you know when Ref2Vid will be available?"* and the other asked *"Does it work with character references?"* Neither question was answered `[community — RelationshipSea2360, Concheria]`. **Treat its absence as a fact about the model, not a gap in this skill.**

So the identity question here is not "how do I supply a reference". It is "how do I *construct* one". Four paths exist, and only the first two are LTX-native.

| Path | What it needs | Holds within a clip? | Holds across a cut? | Cost |
|---|---|---|---|---|
| **Prose re-anchoring** | Nothing but the prompt | Reasonably | **This is the only mechanism multishot has** | Free |
| **Ingredients IC-LoRA** (2.3, loads on 2.5) | A reference sheet of panels | Yes | Partly — and only if the prose re-anchors too | Low — no training |
| **Character LoRA** | A trained adapter, licence-encumbered | Yes | Yes, within a generation | High |
| **I2V from a locked still** | An image model upstream | Yes, but the still fixes the framing | ❌ — and multishot fights I2V | Medium |

---

## 2. Identity across a cut is a text problem

The vendor's multishot guidance asks *you* to "reuse the same visual identifiers for recurring people or objects ('the woman in the red coat, earlier at the table, now…')." That instruction reveals how the model works: **identity is re-anchored from the prompt at each cut, rather than carried by a persistent embedding.** Note that this is an inference from the guide's own rule, not a vendor statement.

Three practical rules follow:

- **Pick one identifier phrase and never vary it.** Use "the woman in the yellow raincoat" at every mention. Synonym variation such as "the young woman", "she", or "the figure in yellow" is exactly the kind of drift that lets the model re-roll the face.
- **Anchor on something visually large.** Hair colour, a garment, a prop, or position in frame all work. A bare noun like "the man" gives the model nothing to match against. The H3 skill reports the same finding for its subject definitions.
- **Stay inside 2–4 shots — one to three cuts.** The vendor's ceiling counts *shots*: "Prefer 2–4 shots in one generation; more cuts usually need clearer, shorter beats per shot." Shorter beats mean less room to re-identify, and re-identification is the only identity mechanism multishot has.

**When identity slips at a cut, diagnose the prose before blaming the model.** [`prompting-guide.md` §4.6](prompting-guide.md#46-a-prompt-that-fails-and-which-rule-it-broke) walks through a prompt that collapses into one continuous take, and names which of the four rules each omission broke. Identity failures usually trace to the same place: either the identifier phrase varied, or the transition was described as a framing rather than an edit.

Whether this actually works is unresolved. One named report is positive on 2.5 — *"the multi shots maintain consistency a lot better"* `[community — hidden2u; single report]`. Against it stands a documented and much-upvoted failure on 2.3: *"as soon as I wanted to make just a few simple shots of the same character with cuts, LTX wasn't even remotely capable of that. Which left me so frustrated I eventually gave up on it completely."* `[community — Dry-Statistician-684]` No side-by-side has been published. [`prompting-guide.md` §4](prompting-guide.md#4-multishot--the-whole-technique) holds the flag on it.

---

## 3. Face drift, and the multi-character break

Two failure modes are documented well enough to plan around.

**Face drift within a clip is not fixed.** Someone asked directly on the 2.5 release thread whether it had been fixed. The answer from a named user running the model was a flat no `[community — Inside-Cantaloupe233, aziib]`. Shorter clips help, because the conditioning signal has less distance to decay over. Keeping the face large in frame helps too.

**Multi-character scenes break character LoRAs.** *"Minimax prompt adherence and identity lock are miles ahead of LTX 2.3 even including character loras since multiple characters in a scene would fuck it up."* `[community — sacx05]` The community's answer is a purpose-built adapter: `MaqueAI/LTX2.3-IC-LORA-Dual-Character`, one of the more-downloaded LTX identity assets on Civitai. Like almost everything in this ecosystem, it is a **2.3** asset `[community — Civitai API 2026-08-22]`.

---

## 4. The Ingredients path — the no-training default

`Lightricks/LTX-2.3-22b-IC-LoRA-Ingredients` is the closest thing LTX has to reference conditioning. You supply a **reference sheet** of panels showing characters, props, and locations, and the adapter carries them into the generation. It is the right first attempt because it costs no training and produces no licence-encumbered artefact.

Its prompt is a two-part string, and getting the shape wrong is the usual failure:

```
Reference sheet: <what the panels contain>
Generated video: <the action>
```

**To combine this with multishot** — the brief most readers actually have — see [`prompting-guide.md` §12](prompting-guide.md#12-multishot-and-a-consistent-character--the-composed-path). That section resolves the collision between Ingredients' two-part prompt and multishot's one-paragraph rule, names the pipeline, and gives a worked two-shot prompt.

Build the sheet as you would any character sheet: consistent lighting, neutral background, several angles, one identity per sheet. Matte the sheet or state the background explicitly, because a white-card sheet can drag its background into the shot.

---

## 5. The still-locking handoff

The cross-modality route is the same one the rest of the suite uses: **lock the character as a still in an image model, then drive I2V from it.** The image skills cover that stage. [`z-image`](../../z-image/), [`flux-2`](../../flux-2/), [`krea-2`](../../krea-2/) and [`sdxl`](../../sdxl/) each carry a `characters.md` with the dataset and adapter craft, and [`character-lora-training`](../../character-lora-training/) covers what transfers across all of them.

The LTX-specific caveat is the one from SKILL.md: **a locked still and a multishot prompt pull against each other.** One generation gives you identity *or* cuts, not both. For a multi-shot sequence with a locked character, the workable pattern is one generation per shot, each I2V-conditioned on a still of the same character, joined in post. That is a segment-stitching problem rather than a multishot one.

---

## 6. Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Face changes at every cut | Identity is re-anchored from text; the identifier phrase varied between mentions | One fixed identifier phrase, repeated verbatim at every cut |
| Face drifts over a long single take | Conditioning decays across the clip; no persistent identity anchor | Shorter clips; keep the face larger in frame |
| Two characters swap features | Single-character LoRAs do not separate identities in one scene | The Dual-Character IC-LoRA, or one character per generation |
| Reference sheet's background bleeds into the shot | The sheet's card is part of what Ingredients carries | Matte the sheet, or state the environment explicitly |
| I2V run refuses the cut, or discards the reference | A multishot prompt on an I2V run | Single take per generation; stitch shots in post |
| A LoRA that worked on 2.3 behaves oddly on 2.5 | Cross-version adapter loading is officially contradictory | Test at low strength first; see SKILL.md's version trap |

---

## 7. When to reach for something else

| You need | Reach for |
|---|---|
| A photograph of a person driving a clip | [`minimax-h3`](../../minimax-h3/) Ref2VA — up to nine images, three clips and three audio references |
| Frame-accurate replacement of a person in existing footage | **SCAIL-2** ([`scail-2`](../../scail-2/)) |
| A pose- or motion-driven character rig with no training | [`wan-2-2`](../../wan-2-2/) — VACE and Animate |
| The still-side identity work that feeds any of the above | [`character-lora-training`](../../character-lora-training/), plus the image skills' own `characters.md` |

LTX's contribution to the identity problem is real but narrow. **It is the only model here that can cut between shots inside one generation.** That means it is the only one where cross-shot identity is even a question you can ask of a single call. But when identity is the *primary* requirement, it is not the model to reach for.
