# MiniMax H3 — prompting guide

1. [The audio half](#1-the-audio-half)
2. [Prompt anatomy](#2-prompt-anatomy)
3. [Soundscape vocabulary](#3-soundscape-vocabulary)
4. [Dialogue](#4-dialogue)
5. [Picture and camera](#5-picture-and-camera)
6. [Approximating H3-Context-IR](#6-approximating-h3-context-ir)
7. [Worked examples](#7-worked-examples)

> Most of this file is reasoned from the architecture and the official templates rather than distilled from community practice — the model is days old and that practice does not exist yet. Treat it as a well-grounded starting point, not settled craft.

---

## 1. The audio half

H3-Omni-Transformer predicts video and audio latents from **one** sequence. The practical consequence is blunt: **audio you do not describe is not absent, it is unspecified**, and the model supplies whatever it finds plausible for the scene. Unspecified audio is the single biggest difference between an H3 prompt and a prompt for any other model in this suite.

The official ComfyUI template states the job directly — describe *"the shots, camera moves, and the accompanying audio (dialogue, SFX, music)."*

Three implications:

- **Silence is an instruction.** "No music," "no dialogue," "ambient only" are meaningful and often necessary.
- **Sound reinforces motion.** A described sound implies the action producing it. "Her heels click on wet pavement" is also a statement about gait and footfall timing — it constrains the picture as well as the track.
- **Audio can be over-specified too.** Dialogue plus dense SFX plus a scored theme in four seconds produces a muddle. Budget the soundscape the way you budget subjects.

---

## 2. Prompt anatomy

A serviceable order, adapted from the suite's image-model anatomy with the audio layer added:

1. **Subject and action** — who, and the physical change over time
2. **Scene** — where, when, lighting
3. **Camera** — shot size and movement, or an explicit static instruction
4. **Style** — exactly one medium
5. **Audio** — dialogue, then sound effects, then music. Naming what is *absent* counts

Keeping audio last is a discipline rather than a requirement: it stops you writing an image prompt and calling it done, because the section is visibly missing.

**Length.** H3 was built for complex multimodal instruction following and rewards detail. But local runs bypass Context-IR (see §6), so your prompt is doing work the official pipeline does upstream — expect to write longer here than you would for the hosted API.

---

## 3. Soundscape vocabulary

Sound divides into three layers that behave differently. Name them separately.

| Layer | What it covers | Phrasing that works |
|---|---|---|
| **Diegetic SFX** | Sound the scene physically makes | Name source **and** material: *"boots on gravel," "rain hissing on canvas," "a door latch clicking shut"* |
| **Ambience / room tone** | The bed the scene sits in | Name the space: *"distant traffic hum," "quiet room tone," "wind across an open field"* |
| **Music** | Score | Name instrumentation and function: *"solo piano, sparse, underneath"* — or *"no music"* |

Two habits worth forming:

- **Source + material beats an adjective.** "Footsteps" gives the model latitude; "boots on wet gravel" specifies a timbre. Same principle as naming a real lens instead of writing "cinematic."
- **State the mix.** *"Dialogue forward, music underneath, traffic distant"* gives relative levels. Without it, the model decides — and stereo output means it decides placement as well.

---

## 4. Dialogue

Eleven languages have stable support: Arabic, Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian and Spanish. Others work to varying degrees.

- **Write the line.** *"She says, 'You're late again.'"* Quoted lines are unambiguous; "they argue" is not.
- **Give the delivery** — flat, urgent, whispered, over the shoulder. It shapes the performance and the facial animation together.
- **Name the language explicitly** when it is not implied by the scene, especially for a non-English line, rather than assuming the model will infer it.
- **Budget it.** Fifteen seconds is a couple of short lines with room to breathe, not a scene. Long speeches within a short clip produce rushed delivery.

---

## 5. Picture and camera

The visual half follows normal video-prompting practice — the general craft is in [`wan-2-2`'s prompting guide](../../wan-2-2/references/prompting-guide.md) and transfers:

- **Describe the action, not the scene.** A prompt every clause of which is satisfied by frame one produces a near-static clip.
- **State the camera, including when you want none** — `static shot` if the default drift is unwanted.
- **One medium.** Contradictory style cues blend into uncanny output, as with still models.

H3-specific: because the encoder is a **VLM** (Qwen3-VL-32B), the prompt is parsed as language with real instruction-following, so clause structure and explicit relationships carry. Write sentences, not tag lists.

---

## 6. Approximating H3-Context-IR

The module that turns free-form multimodal input into the structured representation H3-Base consumes is **not in the open release**, and the model card calls it critical to output quality. Locally, your prompt goes in raw. That gap is the most likely reason a local result underwhelms against the launch reel.

What Context-IR does, per the model card: instruction parsing, cross-modal association, temporal understanding and logical reasoning, serialised into a structured representation — and it *"may also supplement missing or underspecified semantic details."*

So approximating it locally means doing that work yourself:

1. **Resolve the references explicitly.** With multiple inputs, say which is which and how they relate — *"the woman from image 1, in the setting of image 2, with the voice from audio 1."* Context-IR would infer these associations; raw H3-Base will not reliably.
2. **Make the timeline explicit.** State what happens first, next, last. Temporal understanding is one of the module's stated jobs.
3. **Fill in the underspecified.** Anything a competent director would decide — lighting, mix, framing — decide it rather than leaving it open, because the module that would have supplemented it is absent.
4. **Use an LLM as a pre-pass.** Have a capable model expand your short brief into a dense, explicit, structurally-resolved prompt before it reaches H3. This is the same shape as Wan's official prompt-extension feature, and there is no reason it should not help here — though whether it closes the gap is **unverified** `[flagged — re-verify]`.

MiniMax also publishes an API that reproduces the official workflow, and official prompting skills on GitHub. If parity with the demos matters, that path is the honest one.

---

## 7. Worked examples

**T2VA — the audio doing structural work:**

> A short-order cook works a griddle in a cramped diner kitchen at night, flipping and plating in one continuous motion. Warm tungsten overheads, steam catching the light. The camera holds a locked-off medium shot. Realistic live-action, shallow depth of field.
> Audio: bacon fat spitting and hissing on the flat-top, a spatula scraping steel, plates clattering into a stack, muffled conversation from the dining room. No music.

**FL2VA with dialogue** — the reference still carries the picture, so the prompt narrows to action, camera and sound:

> She turns from the window to face the room and says, in English, quietly and without warmth, "You should go."
> Slow push in to a close-up. Audio: her line forward and close, faint rain on glass behind it, room tone otherwise silent. No music.

**Ref2VA carrying a voice** — the capability nothing else in the suite has:

> Using the character from images 1–3 and the voice from audio 1: the character sits on a workshop stool and explains a schematic to someone off-camera, gesturing at it twice. Handheld medium shot.
> Audio: the reference voice, conversational and unhurried; workshop ambience with a distant extractor fan. No music.
