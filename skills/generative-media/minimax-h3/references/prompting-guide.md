# MiniMax H3 — prompting guide

## Contents

1. [The audio half](#1-the-audio-half)
2. [Prompt anatomy](#2-prompt-anatomy)
3. [Soundscape vocabulary](#3-soundscape-vocabulary)
4. [Dialogue and performance](#4-dialogue-and-performance) — including *why there is no emotion tag*
5. [Picture and camera](#5-picture-and-camera)
6. [Approximating H3-Context-IR](#6-approximating-h3-context-ir)
7. [Worked examples](#7-worked-examples)
8. [Ordering, timing and the shot list](#8-ordering-timing-and-the-shot-list)
9. [Prompt tooling](#9-prompt-tooling)
10. [Explicit and adult work](#10-explicit-and-adult-work)

> §1, §3 and §7 are derived by reasoning about the architecture and the official templates. §2, §4, §5 and §6 were re-based on 2026-09-09 against MiniMax's two official prompt-writing guides — `docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md` and `_ref_en.md` on the HF model page, last modified 2026-08-13 — and the syntax quoted from them is official. §8–10 are community craft from named authors, added 2026-08-22/23 and extended on 2026-09-09 with one lab's live runs, marked `[live-use]`. The reliability of real H3 output comes mostly from that community and live-use half.

> **Read the official guides.** There are **two** on the HF model page — one for the **T2V/I2V** model and one for the **Reference** model — and their syntax differs. The community repeats one piece of advice more than any other: most complaints (wrong speaker, gibberish dialogue, unrequested cuts, prompts ignored) are answered verbatim in these guides. `[community — GrayingGamer]`

---

## 1. The audio half

H3-Omni-Transformer predicts video and audio latents from **one** sequence. That has a blunt consequence: **audio you do not describe is not absent, it is unspecified**. The model fills the gap with whatever sound it finds plausible for the scene. This is the single biggest difference between an H3 prompt and a prompt for any other model in this suite.

The official ComfyUI template states the job directly. It tells you to describe *"the shots, camera moves, and the accompanying audio (dialogue, SFX, music)."*

Three things follow from this:

- **Silence is an instruction.** "No music," "no dialogue," and "ambient only" are meaningful, and they are often necessary.
- **Sound reinforces motion.** A described sound implies the action that produces it. "Her heels click on wet pavement" is also a statement about gait and footfall timing, so it constrains the picture as well as the track.
- **Audio can be over-specified too.** Dialogue plus dense SFX plus a scored theme in four seconds produces a muddle. Budget the soundscape the same way you budget subjects.

---

## 2. Prompt anatomy

Here is an order that works well. It is adapted from the suite's image-model anatomy, with the audio layer added:

1. **Subject and action** — who, and the physical change over time
2. **Scene** — where, when, lighting
3. **Camera** — shot size and movement, or an explicit static instruction
4. **Style** — exactly one medium
5. **Audio** — dialogue, then sound effects, then music. Naming what is *absent* counts

Keeping audio last is not a strict requirement, but it helps. It stops you writing an image prompt and calling it done, because the missing section is easy to spot.

**The official order is positional, not emotional.** MiniMax's own guide opens `[Shot 1]` with the **style and the initial composition** (*"Live-action, cinematic, a medium-wide shot frames…"*), then subject and appearance, then action, then camera motion, then speaker plus delivery plus the `<d>` line, and the two audio fields last `[official — base guide §4.1, §5]`. In Ref2VA the style sentence moves *before* `[Shot 1]` `[official — ref guide §5.2]`. Notice what is missing. Emotion is not a section anywhere in that order. It is distributed into the action clauses and into the delivery phrase beside each line (§4). The five-part anatomy above is a compatible simplification of the official order, not a rival to it.

**Length has a number.** For generation tasks the official reference guide puts `detailed_description` at **350–500 English words**. Dialogue-dense content should fit the complete spoken timeline rather than chase the count, and video-editing descriptions scale with the source clip and need not follow the range `[official — ref guide §5.2]`. Two ceilings sit above that band. The hosted API caps the prompt at 7,000 characters `[community — runware.ai docs; re-verify]`. ComfyUI does not truncate at all, so the local path has no ceiling `[community — hyukudan]`. Local runs also bypass Context-IR (§6), so your prompt is doing work the hosted pipeline does upstream. Treat 350 words as where to start, not as the long end.

---

## 3. Soundscape vocabulary

Sound splits into three layers, and each one behaves differently. Name them separately.

| Layer | What it covers | Phrasing that works |
|---|---|---|
| **Diegetic SFX** | Sound the scene physically makes | Name source **and** material: *"boots on gravel," "rain hissing on canvas," "a door latch clicking shut"* |
| **Ambience / room tone** | The bed the scene sits in | Name the space: *"distant traffic hum," "quiet room tone," "wind across an open field"* |
| **Music** | Score | Name instrumentation and function: *"solo piano, sparse, underneath"* — or *"no music"* |

Two habits are worth forming:

- **Source plus material beats an adjective.** "Footsteps" gives the model latitude. "Boots on wet gravel" specifies a timbre. This is the same principle as naming a real lens instead of writing "cinematic."
- **State the mix.** *"Dialogue forward, music underneath, traffic distant"* gives relative levels. Without it, the model decides the levels for you. Because the output is stereo, it also decides placement.

---

## 4. Dialogue and performance

Eleven languages have stable support: Arabic, Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian and Spanish. Others work to varying degrees.

### The dialogue syntax

Three rules, all from the official base guide `[official — base guide §4.4]`:

- **Every speaker gets a stable ID.** Write `(S1)`, `(S2)` after the character's identifying phrase. The ID stays the same across every shot, so the model knows the voice in shot 3 is the voice from shot 1. A compound ID, `(S1,S2)`, is simultaneous group speech. A character who never vocalises gets no ID at all.
- **`<d>` holds the language tag and the exact words. Nothing else goes inside.** The speaker's identifying phrase, ID, action and delivery all sit *outside* the tag, in prose:

  ```
  The woman (S1) turns from the window and says in a low, flat voice <d>[English] You should go</d>.
  ```

  The earlier version of this file put the voice attribution inside the tag, as `<d>[English, in her voice] …</d>`. That contradicts the official form, and §8 is corrected to match.
- **Three fixed phrases cover the edge cases.** Voiceover is written `says in an off-screen voiceover`, and it must be followed by a statement that the on-screen character's lips stay closed. A line that crosses a cut carries `<scenetrans>`. A line the clip ends in the middle of carries `<cutoff>`. Reused reference audio with an unintelligible span uses `[unclear]` `[official — ref guide §5.4]`. Visible on-screen text goes in double quotes and is preserved verbatim, untranslated `[official — base guide §4.5]`.

**Where the delivery goes is contested in practice.** Two Reddit threads report tone and accent working *inside* the language tag — `<d>[English, whispered in a pleading tone] Give me the key, please</d>` and `<d>[English, British accent] …</d>` `[community — r/StableDiffusion, 2026-08-15 and 2026-09-08; re-verify]`. The official guide says the opposite, and the one published input→output trace from a working prompt tool lands the delivery outside the tag `[community — hyukudan]`. Default to the official placement, because it is what the model was trained on. If a tone will not land, the inside-the-tag form is a cheap second try. `[contested]`

**The tag has an acknowledged bug.** One commenter reports `<d>` adding gibberish to the generation and advises against it for now. A related artefact is a first-second audio bleed or "starting chirp". The stated cause is a spoken line that cannot fit the requested duration, and plain quotation marks in place of `<d></d>` reduce it without curing it `[community — r/StableDiffusion PSA thread, 2026-08-15; single report]`. The practical rule follows from the cause: draft at 0.2 MP and check that the audio *fits* before you raise resolution.

Then the craft, which has not changed:

- **Write the line.** A quoted line is unambiguous. "They argue" is not.
- **Name the language in the tag** when the scene does not imply it, especially for a non-English line. Do not assume the model will infer it.
- **Budget it.** Fifteen seconds is a couple of short lines with room to breathe, not a scene. Keep pacing to roughly **1.5–2 words per second** so the performance has room `[community — mwoody450; single report]`. Long speeches in a short clip come out rushed, and the chirp above is what running out of room sounds like.

### Non-verbal sounds — the only tags that exist

A **preset** vocabulary of parenthetical sound tags works inside `<d>`, and two threads three weeks apart converge on the same list: `(laughs)`, `(chuckle)`, `(snorts)`, `(humming)`, `(breath)`, `(pant)`, `(inhale)`, `(exhale)`, `(gasps)`, `(coughs)`, `(clear-throat)`, `(sighs)`, `(lip-smacking)`, `(sniffs)`, `(groans)`, `(yawns)`, `(sneezes)`, `(burps)`, `(whistles)`, `(hissing)`, `(emm)`, `(crying)`, `(applause)` `[community — Mister_Eduards, r/StableDiffusion; convergent across two threads]`. Read the list carefully. Every entry is a **sound**. A custom word in the same brackets — `(nervous)`, `(angry)` — is not in the preset and comes out as spoken text.

Angle-bracket tags are the unreliable half. `<laughs>` and `<sighs>` are reported working, but `<emphasis>` was rendered as a bleeped word on one seed, and custom tags bleed into the audio as garbled fragments `[community — r/StableDiffusion PSA thread; re-verify]`. For emphasis, the technique that won a controlled test, 6/6 against roughly 1/10 for inline tags, is to **say it in the narration after the line**: *he says <d>[English] we are going to do incredible things</d>. He emphasises the word "incredible".* `[community — V4nKw15h; single report]` Markdown-style `*word*` asterisks are reported working in both threads.

### Emotional direction — there is no emotion tag

People arrive at H3 from text-to-speech tools and try `[angry]`, `[whispering]`, `(nervous)`, `*sighs*` or `<break time="1s">`. **None of these is H3 syntax.** They are ElevenLabs and Bark conventions, and H3 has no slot for them, so it reads them as words to speak `[community — hyukudan]`. The preset sound tags above are the whole exception, and they are sounds, not emotions. Three things feed the confusion, and it helps to name them:

- **Bracketed camera commands** like `[Push in]` belong to the hosted Hailuo Director line, not to H3 (§5).
- **One popular ComfyUI prompt tool advertises `<Subject N> (SN) [emotion] says:` as "official MiniMax voice-acting syntax".** No primary source supports it. The official guide puts delivery outside `<d>` in prose and defines no `[emotion]` slot `[community — 1038lab Promptor README; contested]`. Do not adopt it.
- **Emoji and bracket marks in prompt-enhancer tools are authoring shorthand.** hyukudan's enhancer lets you write `😠` beside a line, then resolves it to prose and strips it before the prompt reaches the model. Its validator *fails* a finished prompt that still contains one `[community — hyukudan]`. That is the right mental model: tags are something a tool translates for you, never something H3 reads.

What works instead is prose-shaped direction, and three independent write-ups converge on the same method `[community — Naxdy, RunDiffusion, hyukudan; convergent]`:

1. **Translate the emotion into behaviour a camera could see.** Where the eyes go, what the hands do, what the breathing does, what stays still. Not *"she looks anxious"* but *"her gaze is fixed downward, her fingers grip the table edge, and her shoulders stay raised"* `[community — Naxdy, gist revised 2026-09-06]`. The commercial version of the same before/after: *"a woman feels confident"* becomes *"she steps out of the elevator, straightens her cuff, looks toward the sunrise, and walks past the camera with a restrained smile"*. Tangible movements give the model something to place on a timeline; an abstract state does not. The official guide states only the negative half, and only for the score — *"do not use abstract mood words"* `[official — base guide §4.7]` — so the positive half is community craft.

   **Why naming the emotion fails.** A named emotion pulls the model toward the dominant mode of its caption distribution, which skews to stock, advertising and trailer footage. That is where the default overacting comes from, and the complaint that every male character becomes a confident flirt. Describing *only* observable mechanics — gaze, blink tempo, jaw and hand state, with zero emotion words — was the one technique that held up scene to scene in a follow-up test `[community — TaniaDictee; single report]`.

2. **Pair every voice cue with a visible one.** H3 renders picture and sound together, so a voice-only instruction can hand you an angry line delivered by a neutral face. Worked pairs `[community — hyukudan]`:

   | Line | Voice | Visible |
   |---|---|---|
   | "Get out of my house" | shouts | jaw setting, brows driving hard down as the line breaks out |
   | "Don't leave me" | in a low, unsteady voice, close to tears | eyes filling, blink slowing, mouth going unsteady |

3. **Write the cue as a small arc.** An opening state, a change, a settled state. That is the shape the model's performance rendering responds to; a single frozen state under-seeds it. Muscle lists, pseudo-biometric precision and stacked simultaneous instructions all do worse `[community — hyukudan]`.

4. **Keep it light.** The lab's best-received direction on a five-scene piece was one sentence of arc — *"a playful but shy and embarrassed show-off; she starts shy and then builds in confidence"* — with the explicit instruction not to over-prompt it `[live-use — media lab, Ciara hoop piece, 2026-09]`. One arc sentence plus a couple of visible cues beats a paragraph of adjectives, and it leaves the 350-word budget for the things the model cannot infer.

Two exceptions are pinned. **A voiceover carries no visible cue**, because the official contract requires the on-screen lips to stay closed. And **framing wins**: where the face is not readable, carry the beat with posture, breath, gaze or hands. Do not add a cut, push-in or close-up merely to expose it, because a beat that gives the model a reason to change angle *will* produce a cut, whatever else you anchored (§8) `[community — hyukudan]` `[live-use — media lab, 2026-09]`.

Two practical warnings close this out. **Speed LoRAs strip micro-expression.** Three threads independently report turbo and speed-up LoRAs flattening the small facial detail that a performance lives in, so switch them off for a performance-critical shot `[community — r/StableDiffusion, three threads; convergent; re-verify]`. And **never send emotion marks through a prompt optimiser or Context-IR.** Every tool in this space strips them before emission for the same reason: H3 has no slot for them and would speak them.

### Whisper, reference audio and the music trap

- **Whisper is genuinely contested.** One report says a whisper needs a dedicated whisper *reference clip* and fails without one, producing only slightly quieter lines. Another says H3 does whisper, under undocumented conditions unrelated to the literal instruction `[community — r/StableDiffusion, two threads; contested]`. Treat any "reliable whisper" recipe sceptically, and bring a reference clip in that register if it matters.
- **The reference clip shapes more than the voice.** A more expressive real-human clip adds attitude across modalities — a southern-accent reference produced more hand-talking, unprompted. Never use an AI-generated voice as a clone reference; AI-on-AI compounds every artefact `[community — mwoody450; single report]`.
- **Name the music's source, or the character sings it.** When a score was left as "music", the character read as lip-syncing to it. Naming it as *instrumental, from a phone speaker in the room* fixed that `[live-use — media lab, Ciara hoop piece, 2026-09]`. The general rule is §1's: unspecified sound is invented, and an invented source is the invention you notice last.

---

## 5. Picture and camera

The visual half follows normal video-prompting practice. The general craft is in [`wan-2-2`'s prompting guide](../../wan-2-2/references/prompting-guide.md), and it transfers here:

- **Describe the action, not the scene.** If every clause is already satisfied by frame one, you get a near-static clip.
- **State the camera, including when you want none.** Write `static shot` if you do not want the default drift.
- **One medium.** Contradictory style cues blend into uncanny output, just as they do with still models.

**The camera has an official grammar, and it is prose.** Twelve motion types are defined: *Zoom In/Out, Push In/Pull Out, Pan Left/Right, Truck Left/Right, Tilt Up/Down, Pedestal Up/Down, Arc Shot, Tracking Shot, Static Shot, Shake Slightly/Strongly, POV, Roll Clockwise/Counterclockwise*. A complete camera expression adds two axes: **amplitude** (`with small amplitude` / `with large amplitude`) and **speed** (`at slow speed` / `at fast speed`). Medium amplitude and normal speed are the defaults and are usually left out. The guide is explicit about form: *"camera motion should be written as a natural English action within the shot, rather than stacked as separate labels at the end of a sentence"* `[official — base guide §4.3]`. So:

> *The camera pushes in slowly with small amplitude as she looks up.*

not *"…as she looks up. Push in, slow, small."* In live use, writing the camera in that full grammar — type, amplitude and speed — was part of the prompt structure that finally held a room across a 175-frame shot where fifteen looser prompts had not `[live-use — media lab, Ciara hoop piece, 2026-09]`.

**Bracketed camera commands are a different product.** `[Push in]`, `[Truck left]`, `[Pan right]`, `[Pedestal up]`, `[Zoom out]`, `[Shake]`, `[Tracking shot]`, `[Static shot]` — fifteen commands, stackable in one bracket and sequenced across brackets — are the syntax of the hosted **Hailuo** line: `T2V-01-Director`, `I2V-01-Director`, `Hailuo-02` and `Hailuo-2.3`. They are not documented for H3 `[official — MiniMax API docs, via aggregator; re-verify]`. The same is true of `prompt_optimizer`, a hosted-API parameter that rewrites your prompt (turn it off when exact control matters). Neither has any bearing on a local run of the open weights. When a workflow you copied has brackets in the camera line, it came from the other model.

**There is no negative prompt, so exclusions are sentences.** Write them in plain English, and spend them where the model adds things on its own: camera movement and on-screen text. For a locked frame, say *"the frame never moves"* and then list the moves that must not happen — no pan, no push-in, no reframing `[community — Naxdy]`.

**Faces at distance, and the wide-shot swim.** H3 is described as *"notoriously bad with faces at distance"*, and backgrounds visibly swim when the camera moves on a wide shot. Tighten the framing, or lock the camera in the prompt `[community — r/StableDiffusion, 2026-09; re-verify]`. This is the same framing ceiling `characters.md` measured for identity, seen from the prompt side.

**Name the wardrobe, even for a referenced subject.** H3 drifts garments across generations. Stating them in the text costs a clause and stops the drift `[community — Naxdy]`.

One thing is specific to H3. Because the encoder is a **VLM** (Qwen3-VL-32B), it parses the prompt as language with real instruction-following. Clause structure and explicit relationships carry through. Write sentences, not tag lists — which is also why the bracket syntax above does nothing useful here.

---

## 6. Approximating H3-Context-IR

The module that turns free-form multimodal input into the structured representation H3-Base consumes has **no open weights**, and the model card calls it critical to output quality. On a plain local graph, your prompt goes in raw. That gap is the most likely reason a local result underwhelms against the launch reel.

**It is reachable, though, on credits.** ComfyUI ships a partner node, **`MiniMax H3 Context IR`** (`MinimaxHailuo03ContextIRNode`), that calls the hosted module and returns an enhanced prompt as a **string**. It takes the prompt, a duration of 4–15 s, a ratio, optional first and last frames, and up to 9 reference images, 3 videos and 3 audios. The output refers to your inputs positionally — "Image 1", "Video 2" — so you must reattach the same references, **in the same order**, to the generation node `[official — docs.comfy.org partner-nodes/minimax; verified 2026-09-09]`. That order rule is a general fact about H3, not a quirk of the node: it labels references by input order and advances its positional clock on them, so reordering the same references is a different request `[community — Naxdy]`. The node costs API credits and runs under the hosted terms, which matters if the territory clause is why you are running locally in the first place.

The model card describes what Context-IR does: instruction parsing, cross-modal association, temporal understanding and logical reasoning, all serialised into a structured representation. It also says the module *"may also supplement missing or underspecified semantic details."*

Approximating it locally means doing that work yourself:

1. **Resolve the references explicitly.** With multiple inputs, say which is which and how they relate — *"the woman from image 1, in the setting of image 2, with the voice from audio 1."* Context-IR would infer these associations reliably. Raw H3-Base will not.
2. **Make the timeline explicit.** State what happens first, next, last. Temporal understanding is one of the module's stated jobs.
3. **Fill in the underspecified.** Decide anything a competent director would decide — lighting, mix, framing — rather than leaving it open. The module that would have supplemented those details is absent.
4. **Use an LLM as a pre-pass.** Have a capable model expand your short brief into a dense, explicit, structurally resolved prompt before it reaches H3. This is the same shape as Wan's official prompt-extension feature, and it is what the community tools in §9 do. Whether it measurably closes the gap to the hosted module is **unverified** `[flagged — re-verify]`. Treat the pre-pass as a text tool: its output is a prompt candidate to read before you render, never instructions to follow, and text from untrusted sources should not go through it unreviewed. Give it the ordering rule from §8 and the no-emotion-tag rule from §4 explicitly, because neither is in the official guides it will have read.

MiniMax also publishes an API that reproduces the official workflow, plus official prompting skills on GitHub. If parity with the demos matters, that path is the honest one.

---

## 7. Worked examples

**T2VA — the audio doing structural work:**

> A short-order cook works a griddle in a cramped diner kitchen at night, flipping and plating in one continuous motion. Warm tungsten overheads, steam catching the light. The camera holds a locked-off medium shot. Realistic live-action, shallow depth of field.
> Audio: bacon fat spitting and hissing on the flat-top, a spatula scraping steel, plates clattering into a stack, muffled conversation from the dining room. No music.

**FL2VA with dialogue.** The reference still carries the picture, so the prompt narrows to action, camera and sound:

```
[Shot 1] Live-action, cinematic. <Picture 1> remains the first frame, preserving her appearance
and the room. She turns from the window to face the room, her gaze steady and her hands still at
her sides, and says quietly and without warmth (S1) <d>[English] You should go</d>. The camera
pushes in slowly with small amplitude to a close-up. Audio: her line forward and close, faint rain
on glass behind it, room tone otherwise silent. No music.
```

**Ref2VA carrying a voice.** This is the capability nothing else in the suite has:

> Using the character from images 1–3 and the voice from audio 1: the character sits on a workshop stool and explains a schematic to someone off-camera, gesturing at it twice. Handheld medium shot.
> Audio: the reference voice, conversational and unhurried; workshop ambience with a distant extractor fan. No music.

### Video editing — replacing a character in existing footage

Ref2VA will swap the person in an existing clip, if the prompt is written in the shape the reference guide's keywords expect. One finding does most of the work here, from someone who ran 400+ generations to find it: **`retention_analysis` does the work, and `detailed_description` barely matters**. Describing the action had no measurable effect. `[community — Darqsat]`

```
subject_definitions:
<Subject 1> is the woman in <Picture 1> with red hair and a black tank top.
<Subject 2> is the woman originally in <Video 1>.

summary:
[video editing + Audio reuse] The target video is an edited version of <Video 1>.
<Subject 2> is replaced with <Subject 1>, who takes over her pose and movement.

retention_analysis:
<Subject 1>: fully_preserved — face, hairstyle and body from <Picture 1> retained
             throughout. Her clothes are not retained.
<Subject 2>: attribute_transfer — pose, movement and screen position are transferred
             to <Subject 1>.

detailed_description:
The target video keeps <Video 1>'s original style, lighting and camera work unchanged.

overall_soundscape: N/A
non_diegetic_music: N/A
```

- `[video editing]` and `[audio reuse]` are two of **six pre-trained summary keywords** from the official reference guide, not free text. The full set is `keyframe completion`, `reference generation`, `video editing`, `video continuation`, `audio reuse` and `audio reference` `[official — ref guide §3]`. `retention_analysis` likewise has a closed vocabulary: `fully_preserved`, `partially_preserved`, `attribute_transfer` and `weak_reference` for visual references, and `fully_copy`, `partially_copy`, `reference` and `weak_reference` for audio `[official — ref guide §4.1–4.2]`. An expression or pose can itself be a named `<Subject N>` drawn from a reference asset `[official — ref guide §2.1]`. The first biases the model toward the source frames instead of a fresh generation. It is **not** frame-for-frame tracking. That difference is the whole reason SKILL.md's suite table sends exact motion transfer to [`scail-2`](../../scail-2/): H3 takes the source clip as *conditioning* and renders new frames from it, so the output resembles the driving performance rather than following it. That is fine for a character swap in a shot you control, and wrong for footage that has to match cut-for-cut. `fully_preserved` and `attribute_transfer` are the retention keywords.
- **Anchor each Subject on something visually large**, such as hair, clothing, or position in frame. A bare "woman" loses identity roughly half the time in a complex scene, and it fails in both directions: the reference image *and* the reference video.
- It fails when the driving character is barely legible: close to camera, partial face, fast movement.
- `[audio reuse]` works, but the model **re-renders** the audio rather than copying it. A sound the model handles poorly therefore comes back poorly.
- **The identity latch is length-limited, and where it breaks is contested.** This skill owns the claim, and the honest version of it is a band rather than a number. Two single community reports disagree. One has subject matching in Ref2VA **degrading sharply past ~5 s**. Another reports a **hard latch failure past ~7 s** `[community — Mediocre-Toe3212]`. They differ on severity as well as timing — one describes a slide, the other a cliff — and nobody has run them side by side. So treat the whole **5–7 s band** as the region where identity stops being dependable, and build shots that end below it. `[contested]`
- **One of those numbers may not be about the model at all.** Wan2GP issue #2111 (SirusAI, 8 August 2026) reports Ref2VA failing at *exactly* 5 s because the sliding-window inference loops back to the start of the reference video instead of advancing through it. That is a harness bug, not conditioning decay `[community — deepbeepmeep/Wan2GP#2111, open]`. This matters diagnostically. A gradual slide in likeness means the model is running out of conditioning. A sharp, reproducible wall at a round number means your runner is mishandling the window boundary. Check which one you have before shortening every shot.
- The same report as the 5 s figure carries two settings that are much less contested: **12–15 steps latch onto the face better than the default 20**, and `ref_image_size` set to `MAX` beats `match`. `[community — single report; re-verify]`

Where exact motion transfer is the point — following the driving movement frame for frame rather than re-generating it — this is the wrong tool. That job belongs to [`scail-2`](../../scail-2/), which tracks the driving footage with SAM3 instead of re-rendering it. SKILL.md's suite table carries the full comparison, including what you give up: H3's audio, which SCAIL-2 neither generates nor consumes.

**The SAM3+Ref2VA workaround, for when SCAIL-2 is not an option.** This is the recipe people report for doing a person swap inside H3 anyway. Isolate the performer from the source clip with SAM3 and composite them onto a neutral grey background. Use that isolated clip as the motion reference. The grey background matters because it stops the original scene from fighting the swap. Supply face and body reference images for identity. Run at 15 steps with no Turbo LoRA. Be clear about what this is: a workaround, not a substitute for tracked replacement. It surfaced late in a live session that had already lost several runs to the naive recipe above, and we have not verified it ourselves. `[community — reddit; re-verify]`

---

## 8. Ordering, timing and the shot list

Everything in §1–7 assumes the model understands *what* you want. This section is about *when*, and it is where most of the jank in real H3 output comes from. All of it is community-sourced from named authors.

### The ordering rule — the single highest-value thing on this page

**H3 assumes actions are sequential unless you say otherwise.** Two actions joined by "and" will happen one after the other, even when that is obviously wrong. The result reads as subtly awkward staggering rather than as an outright error, which is why people rarely diagnose it. The practitioner with the most detailed public H3 prompting notes attributes **"80% of the jank"** to this one ambiguity. That makes it the highest-leverage line on this page by a wide margin. `[community — nsfwVariant]`

**Why it happens, and why the mechanism matters.** Knowing the mechanism tells you where else to look. H3's conditioning comes from a language model reading your prompt, and a prompt is a linear sequence of tokens. **Textual order is therefore the strongest — often the only — temporal signal the model has.** English "and" carries no temporal information at all: *"she waves and smiles"* is genuinely ambiguous between overlapping and consecutive. The model cannot decline to choose, so it takes the reading that a fixed clip length can always accommodate, which is one beat after another. Two consequences follow directly. First, **any construction that leaves order underspecified inherits the same default**: comma-separated action lists, "as well as", or a bare participial clause tacked onto a sentence. Second, **the fix is a word, not a setting.** Raising steps or re-rolling the seed cannot supply information the prompt never contained. That is exactly what people spend their time on instead.

| Write | Get |
|---|---|
| *She waves at the camera **and** smiles* | The smile arrives after the wave |
| *She waves at the camera **while** smiling* | What you meant |

Use **"while"** for simultaneous actions, **"then"** for sequential ones, and "throughout" for something spanning a sequence. `+` also reads as simultaneous. `[community — nsfwVariant]`

> LLM prompt-writers do not do this, because the rule is not in the official guides. If you generate prompts with a model, tell it the rule explicitly and check its output for a bare "and".

### When the model keeps getting one thing wrong, over-describe *that thing*

H3 is prompt-adherent enough that you can instruct it through its own weak spots. That is genuinely unusual, and it is the practical argument for writing prompts by hand rather than accepting an LLM's paragraph. The canonical example is clothing and props phasing through limbs. The fix is not a stronger adjective. The fix is describing the mechanical path:

> *She pulls her skirt down over her thighs, **then lets go of it so it slides directly down to the floor over her legs**.*

There is no way to misread that, so the model usually gets it right.

**People arriving from [`wan-2-2`](../../wan-2-2/) expect this to cost them something, and it does not.** On Wan, the same tactic buys the fix at the price of other detail. On H3, hand-holding one stubborn element does not visibly degrade the rest. So the right response to a repeated failure here is *more* words aimed precisely at it. `[community — nsfwVariant]` Wan's own guidance is more precise than that folk version. It warns against **competing** subjects and actions — *"one clear action beats three competing ones"* — rather than against detail as such. It also warns, separately, that re-describing what an I2V reference already carries pulls the clip away from the reference. Both of those warnings are about demands that contend with each other. Piling clauses onto the single element that keeps failing is not that kind of demand. That is why the tactic is safe here, and why the instinct to keep H3 prompts lean is the wrong thing to import from Wan.

Two practical notes on applying it. **Describe the path, not the outcome.** "So it slides directly down to the floor over her legs" is a trajectory the model can follow. "The skirt is removed" is a state change the model has to invent a route to. And **pair the description with time**: a mechanical description that does not fit the seconds available gets crammed rather than followed. That is the next subsection.

### Describe the activity, not the geometry

When a prompt states a spatial arrangement directly, the model treats it as a scene to compose, and it composes wrong ones. Describe the action that produces the arrangement instead. An activity implies the geometry, carries an object count, and gives the model a physical route to the pose. A static spatial description does none of those things.

The live example: *"a hoop around her waist, gripping the sides"* drew **two** hoops. *"She has stepped into a single hoop and lifted it to her waist"* fixed it across all seeds. The second phrasing is a short history of how the pose came to be, so there is only one way to stage it.

### Timestamps

Format is `mm:ss.000`. Two rules:

- **Never timestamp the first shot.** Omitting timestamps entirely lets the model choose its own cuts, which is often fine. Using them gives you control of pacing, comic timing and how long a reaction holds.
- **Position is semantic.** The timestamp binds to the action it sits next to:

| Written | Means |
|---|---|
| *at 00:03.000 she lifts her shirt, which exposes her shoulders* | the **lift** starts at 3 s |
| *she lifts her shirt, which exposes her shoulders at 00:03.000* | the **exposure** happens at 3 s |

### Budget time against content

The model tries to fit everything you asked for into the duration you gave it. Ask for ten seconds of action in five, and it crams, overlaps and truncates. People misread that as the model being bad at dialogue. **Allow 3–4 s for any fiddly physical action** (removing one garment, opening a stuck door, a prop handoff — one author budgets roughly four seconds for a hand-off `[community — Naxdy; single report]`), and keep dialogue short for 5–7 s clips. The same author puts the **most important beat in the middle** of the timeline rather than last, because the final beat is the one most likely to be squeezed `[community — Naxdy; single report]`.

**Multi-step sequences are where this compounds, and undressing is the worked case.** The rule is **≥3 s per garment, each item named in its own clause, in order.** Three garments make a nine-second clip, not a five-second one with a longer sentence. `[community — nsfwVariant]` The compressed version fails so reliably because the two rules above act together. One clause covering three items reads as **one beat**, so the time budget allots it one beat's worth of seconds, and the mechanical path for items two and three never gets described at all. Written out item by item, you get three beats, three time allocations and three described trajectories, and the garments stop teleporting. The same shape applies to any sequence of similar small actions: unpacking a bag, setting a table, a fight exchange.

**Draft at 0.2 MP first.** A 608×352 pass takes a few minutes and shows you the timing, the shot order and whether the model understood the brief. Fix the prompt there, and spend the long run once.

### The shot list

```
[Shot 1] A medium close-up of … he opens his mouth as if to speak, then shakes his head.
[Shot 2] At 00:06.000, the camera cuts to a static shot framing … arms crossed.
[Shot 3] At 00:10.500, the camera pans quickly with large amplitude back to …, then a slow push in to his face.
```

Shot 2 starting at 6 s and shot 3 at 10.5 s tells the model to hold that glare for four and a half seconds. The official form is `[Shot N] At MM:SS.mmm,` with the first shot carrying no timestamp and later cut times strictly increasing and inside the duration `[official — base guide §4.2]`. Field names seen in circulating structured prompts: `integrated_multimodal_description`, `subject_definitions`, `retention_analysis`, `overall_soundscape`, `non_diegetic_music` (write `N/A` or `none` for no score).

**A second shot marker *is* a cut, and so is a timestamp.** This is the finding that ended a week of workarounds. Across three passes of a five-scene piece, H3 kept cutting to a different room about a second into each shot. The fix built first was a hop-made end frame per scene — pin both ends and the room holds — at the cost of an extra render per shot. The actual cause was the prompt shape: continuous footage must be **one `[Shot 1]` block with no timestamps**, and for image-to-video the picture line must read *`<Picture 1>` remains … preserving her appearance, [the room layout] …*, with the camera in the full grammar of §5. Same seed, same 175 frames, no end pin, official structure: the room held completely. The end-pin path was kept as a fallback, and the caveat is honest — it was one A/B, and two things moved at once (prompt shape, and Turbo → stock) `[live-use — media lab, Ciara hoop piece, 2026-09]`.

**Beats that trigger a cut are the prompt's fault, not the anchoring's.** A walk-away from the lens produced a ~3 s cutaway to another room in all three passes, pins or no pins. Rewritten so she never leaves the lens, it stopped. An action that gives the model a *reason* to change angle will make it change angle, and no anchoring buys that back `[live-use — media lab, 2026-09]`. §4's "framing wins" rule is the same lesson from the performance side.

### Dialogue tags, restated because they fix two bugs at once

Name the speaker before the line, give them a stable `(S1)` ID, and keep the `<d>` tag to the language and the words: *The man (S2) replies in a whisper <d>[English] Please, listen to me</d>.* Wrong-speaker attribution and gibberish dialogue both come from skipping the attribution `[community — GrayingGamer]`. An earlier version of this file wrote the attribution *inside* the tag; the official form puts it outside (§4), and the marks bind to the nearest quoted line, which is what makes two speakers on one line work `[community — hyukudan]`.

---

## 9. Prompt tooling

Writing H3 prompts by hand is slow, and the formatting is fussy. LLMs are good at the content and bad at the syntax, and they drift on small revisions. Two community tools split that problem the right way: you make the creative decisions, and the tool owns the structure.

| Tool | What it is |
|---|---|
| **`BMB12d3/minimax-h3-prompt-composer`** | Offline browser app. All five modes (T2VA, I2VA, FL2VA, L2VA, Ref2VA), reusable characters/environments/voices/continuity frames, camera builder and visual path planner, timed shots and action beats, and **validity checks** for structure, timing, references, camera conflicts, audio and input routing. Runs alongside ComfyUI so you can compose the next shot while one renders |
| **`duckyshell/ComfyUI-MiniMaxH3-Prompt-Writer`** | In-ComfyUI UI extension. A **local** Gemma 4 multimodal model reads your actual references and writes the prompt against the official guides. Tiers from 8 GB (Gemma 4 E4B Q3) to 32 GB (31B Q4); the author's pick is the 24 GB tier. Video references are analysed as an ordered contact sheet; audio can be tagged `<Audio N>` but the local model cannot hear it, so describe its role. Needs the CUDA build of `llama-cpp-python` |

Four more are worth knowing, mostly for what they teach `[community — GitHub READMEs, checked 2026-09-09; re-verify]`:

| Tool | What it is |
|---|---|
| **`hyukudan/ComfyUI-MiniMax-H3-Prompt-Enhancer`** | The emotion-mark enhancer discussed in §4. Emoji or bracket shorthand beside a quoted line is resolved to prose delivery plus a visible cue, then stripped; a validator fails any prompt that still carries a mark. Publishes a real input→output trace. Its ⏸️ pause mark is self-flagged as the tool's own convention, rendered as an ellipsis — the official guides have no pause mechanism |
| **`1038lab/Comfyui-Minimax-H3-Promptor`** | The most-starred of the set. Useful structure, but its README advertises `<Subject N> (SN) [emotion] says:` as official voice-acting syntax, and no primary source supports that slot `[contested]`. Use the tool; do not learn the syntax from it |
| **Naxdy's enhancer gist** (revised 2026-09-06) | A system prompt rather than a node. The source of the observable-behaviour rule, the middle-beat rule and the exclusions-as-sentences rule in this file |
| **A VLM front-end for I2V/Ref2VA** | Reference image plus a plain instruction, expanded by a vision-language model (Qwen3-VL-8B in the posted build) into H3's structured format. Reported to improve adherence on camera, action and dialogue; one author's before/after only `[community — r/StableDiffusion; single report]` |

fal.ai's guide uses `@Image 1:` and `[0–2 seconds]` house conventions; neither is official, and the bracketed time range conflicts with the `[Shot N] At MM:SS.mmm` form `[community — fal.ai guide; re-verify]`.

All of these are `[community]`, and all are young. But the general lesson stands without any of them: **let a model draft, then fix the ordering words, the timestamps and the tag placement yourself** — and check that no emotion mark survived into the prompt.

---

## 10. Explicit and adult work

**Settle the licence before you read this section.** H3's Community License excludes the US, EU, UK and South Korea from its Applicable Territory, and Exhibit A makes use outside that territory a prohibited use — see SKILL.md's opening section and `licence-and-territory.md`. Nothing below changes that. Because this is the job the community rates H3 highest at, that is a reason to be more careful about the clause, not less. **Which model to use for this work at all** — across image and video, with the platform and consent constraints that go with it — belongs to [`generative-media-atlas`](../../generative-media-atlas/)'s `references/adult-work.md`. What follows assumes that decision is already made, and covers only how to drive H3.

**The single requirement: bring a reference image.** Base nudity prompted from text alone is reported as *"inconsistent & low quality"*. A **nude reference image — or close-up references for the specific anatomy involved — is what makes an undressing sequence work at all**. `[community — nsfwVariant]` This is not a filter being worked around. H3 does not meaningfully refuse (see `setup-and-workflows.md §10`). The failures are gaps in the training distribution, and a gap is not something a prompt can argue with. A reference image puts the missing information into the conditioning directly. That is why it works where adjectives, weighting and encoder swaps all do not. Practically this means using **Ref2VA — in its hybrid form** (`setup-and-workflows.md §5`), since plain Ref2VA's quality gap lands hardest on exactly the fine anatomy you are conditioning for. Reference sizing follows the ordinary budget in `characters.md`: the thing you need right gets the pixels.

**Nothing else here is special-cased.** The general rules in §8 simply bite harder, because this content is physically fiddly, multi-step, and involves two bodies interacting:

| Rule | Why it lands harder here |
|---|---|
| **`then` / `while`** | Two people acting on each other is the case where sequential-by-default is most visibly wrong, and the staggering reads as bad animation rather than as a prompt bug |
| **≥3 s per garment, item by item** | Undressing is the canonical multi-step sequence; one clause for three items gets one beat's worth of time and two undescribed trajectories |
| **Over-describe the mechanical path** | Contact, occlusion and cloth are exactly where H3's physics slips, and it is adherent enough to be hand-held through them |
| **~30 steps, ~0.8 MP** | Both bands were established on this kind of content: steps buy physics and interaction correctness, and error rates rise above *and* below ~0.8 MP `[community — nsfwVariant]` |
| **Timestamp beside the action** | Sequences are timed sequences; a timestamp attached to the wrong clause reschedules the wrong beat |

**On dialogue and sound**, the model's defining trait applies unchanged, and it is worth using rather than suppressing. Unspecified audio is invented, so breath, contact sound and the absence of a score are all things to state (§1, §3). Reference *audio* through Ref2VA carries a voice rather than describing one (§4, `characters.md`).

**Real-person likenesses are a separate problem, and not a technical one.** The constraint does not come from the model. It comes from platform policy and law — Civitai's ban on real-person NSFW and the TAKE IT DOWN Act. [`character-lora-training`](../../character-lora-training/references/publishing-and-likeness.md) covers it. Do not read H3's lack of refusal as permission.
