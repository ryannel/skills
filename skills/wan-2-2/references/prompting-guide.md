# Wan 2.2 — prompting guide

1. [The shift from image prompting](#1-the-shift-from-image-prompting)
2. [Prompt anatomy](#2-prompt-anatomy)
3. [Motion vocabulary](#3-motion-vocabulary)
4. [Camera vocabulary](#4-camera-vocabulary)
5. [Negatives, and when they apply](#5-negatives-and-when-they-apply)
6. [Prompt extension](#6-prompt-extension)
7. [Worked examples](#7-worked-examples)

---

## 1. The shift from image prompting

The most common Wan 2.2 failure is a prompt that would be excellent for an image model. umT5 encodes it faithfully, the model renders a beautiful composition, and then **almost nothing happens for five seconds**.

The mechanism: a still-image prompt describes a *state*. Video generation needs a *change of state*. If every clause in your prompt is satisfied by frame one, the model has no reason to move anything, and the cheapest way to satisfy your prompt is to hold still.

This is the single highest-value edit to any Wan prompt: **find the verb.** If there isn't one describing physical change over time, the clip will not move.

| Image prompt (produces a near-static clip) | Video prompt |
|---|---|
| *A woman in a red coat standing on a rainy street at night, neon reflections, 85 mm* | *A woman in a red coat **walks toward camera** through rain at night, **coat hem swinging**, neon reflections **rippling** in the puddles she **steps through*** |
| *A cup of coffee on a wooden table, steam, morning light* | *Steam **curls upward** from a cup of coffee, **drifting** left as morning light **shifts** across the wooden table* |

Note what does *not* change: the visual specificity is still there. You are adding motion, not trading detail for it.

**When you already have the still.** If you are running I2V from an image you locked with an image model, the still already carries composition, identity, lighting and style — so the prompt's job narrows to **motion and camera only**. Re-describing the scene competes with the reference and can pull the first frame away from it. Describe what moves and how the camera behaves; let the image do the rest.

---

## 2. Prompt anatomy

For **T2V**, in roughly this order:

1. **Subject** — who or what, with the concrete detail you would give an image model
2. **Action** — the physical change over time. Non-negotiable; see above
3. **Scene** — where, when, lighting
4. **Camera** — shot size and movement, or an explicit `static shot`
5. **Style** — exactly one medium; contradictions produce uncanny blending, the same as in still models

For **I2V**, collapse to **Action → Camera**, plus only enough subject reference to disambiguate ("*the woman on the left*") when the frame has several candidates.

**Length.** Wan responds well to detailed prompts, and the official prompt-extension feature exists precisely because longer, richer prompts improve output [official]. But every added clause is another state the model must satisfy — so add *detail*, not *more subjects*. One clear action beats three competing ones.

---

## 3. Motion vocabulary

Motion needs three components to be legible. Naming only one usually produces a vague drift.

| Component | Weak | Strong |
|---|---|---|
| **What moves** | "she moves" | "her right hand lifts" |
| **Direction** | "the camera moves" | "pushes in toward her face" |
| **Speed / quality** | — | "slowly", "sharply", "in one continuous motion" |

Useful qualifiers that read as intended: `slowly`, `gradually`, `abruptly`, `in one continuous motion`, `looping`, `settling`. Secondary motion is what sells a shot — hair, fabric, steam, water, dust, foliage. Naming one secondary element usually does more for realism than another adjective on the subject.

**Physical plausibility helps.** The model has strong priors for real-world dynamics; motion that obeys them comes out cleaner than motion that doesn't. Fighting gravity, inertia or normal gait speed tends to produce the morphing artefacts described in the failure-mode table.

---

## 4. Camera vocabulary

Camera terms are interpreted literally and reliably — this is one of Wan's genuine strengths.

| Intent | Phrasing |
|---|---|
| Move toward / away | `dolly in`, `dolly out`, `push in`, `pull back` |
| Lateral | `pan left`, `pan right`, `truck left`, `truck right` |
| Vertical | `tilt up`, `tilt down`, `crane up`, `crane down` |
| Around the subject | `orbit left`, `arc around the subject` |
| Feel | `handheld`, `steadicam`, `locked-off tripod` |
| **No movement** | `static shot`, `fixed camera` |

**State the camera explicitly, including when you want none.** The default behaviour is to add drift, so an unstated camera is not a still camera. `static shot` is the fix, and it is also the fix for "why does my locked-off product shot keep floating."

For *discrete, guaranteed* camera moves rather than prompt-suggested ones, use **Fun Camera Control** — see `motion-and-camera.md`. Prompt-level camera direction is a request; Fun Camera is an instruction.

---

## 5. Negatives, and when they apply

**Whether negatives work is determined by guidance state, not by the encoder.** Wan 2.2 gives you both cases in one model family:

| Path | CFG | Negatives |
|---|---|---|
| 14B quality path | 3.5–4.0 | **Work normally** |
| 5B TI2V | 5.0 | **Work normally** |
| S2V | 6.0 | **Work normally** |
| 4-step lightx2v speed path | 1.0 | **Inert** — guidance-off. Phrase constraints positively |

This is worth internalising because it is the opposite of most of the still-image models in this suite, where the fast variants are the *only* option most people run and negatives are usually inert.

**The default negative prompt is Chinese, and should stay Chinese.** Wan ships a long default negative covering over-saturation, overexposure, static frames, blur, subtitles/watermarks, low quality and JPEG artefacts, and the usual anatomy failures. Community consensus is to **use it as shipped rather than translating it** — the encoder saw those tokens in that form during training, and English paraphrases measurably underperform `[community — re-verify]`.

Take the exact string from the official repo's inference config or the ComfyUI template rather than retyping it — it is long, and a partial copy silently loses coverage. Append your own terms rather than replacing it.

---

## 6. Prompt extension

An official feature, not a community trick [official]:

```
--use_prompt_extend --prompt_extend_method 'dashscope'   # Qwen-Plus (T2V) / Qwen-VL-Max (I2V), needs DASH_API_KEY
--use_prompt_extend --prompt_extend_method 'local_qwen'  # Qwen2.5-{14B,7B,3B}-Instruct, VL variants for I2V
```

It rewrites a short prompt into a richer one and measurably improves detail. Two caveats: it costs a model load locally, and it will invent specifics — if you are matching a locked still or an established character, extension can pull the clip away from your reference. For controlled work, write the long prompt yourself.

---

## 7. Worked examples

**T2V, character action:**

> A young woman in a grey wool coat walks briskly along a wet city pavement at dusk, her scarf lifting and settling with each step, puddles rippling as she passes. Shallow depth of field, sodium streetlights, cool blue ambient sky. The camera tracks alongside her at walking pace, handheld. Cinematic live-action footage.

Subject, action with secondary motion (scarf, puddles), scene and light, explicit camera with a speed, one medium.

**I2V from a locked still** — note how little scene description is needed:

> She turns her head slowly to look off-frame left, hair shifting with the movement; steam continues to rise from the cup. Static shot.

**Deliberately still shot** — the camera instruction is doing the work:

> A ceramic vase on a windowsill, dust motes drifting slowly through a shaft of afternoon light. Fixed camera, static shot, no camera movement.
