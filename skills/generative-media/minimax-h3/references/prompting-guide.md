# MiniMax H3 — prompting guide

## Contents

1. [The audio half](#1-the-audio-half)
2. [Prompt anatomy](#2-prompt-anatomy)
3. [Soundscape vocabulary](#3-soundscape-vocabulary)
4. [Dialogue](#4-dialogue)
5. [Picture and camera](#5-picture-and-camera)
6. [Approximating H3-Context-IR](#6-approximating-h3-context-ir)
7. [Worked examples](#7-worked-examples)
8. [Ordering, timing and the shot list](#8-ordering-timing-and-the-shot-list)
9. [Prompt tooling](#9-prompt-tooling)
10. [Explicit and adult work](#10-explicit-and-adult-work)

> §1–7 are derived by reasoning about the architecture and the official templates, not from community practice. §8–10 are the opposite: they are community craft from named authors, added on 2026-08-22 and extended on 2026-08-23. The reliability of real H3 output comes mostly from that community half.

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

**Length.** H3 was built for complex multimodal instruction following, and it rewards detail. But local runs bypass Context-IR (see §6), so your prompt has to do work the official pipeline normally does upstream. Expect to write longer prompts here than you would for the hosted API.

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

## 4. Dialogue

Eleven languages have stable support: Arabic, Chinese, English, French, German, Italian, Japanese, Korean, Portuguese, Russian and Spanish. Others work to varying degrees.

- **Write the line.** *"She says, 'You're late again.'"* A quoted line is unambiguous. "They argue" is not.
- **Give the delivery** — flat, urgent, whispered, over the shoulder. It shapes the performance and the facial animation together.
- **Name the language explicitly** when the scene does not imply it, especially for a non-English line. Do not assume the model will infer it.
- **Budget it.** Fifteen seconds is a couple of short lines with room to breathe, not a scene. Long speeches in a short clip come out rushed.

---

## 5. Picture and camera

The visual half follows normal video-prompting practice. The general craft is in [`wan-2-2`'s prompting guide](../../wan-2-2/references/prompting-guide.md), and it transfers here:

- **Describe the action, not the scene.** If every clause is already satisfied by frame one, you get a near-static clip.
- **State the camera, including when you want none.** Write `static shot` if you do not want the default drift.
- **One medium.** Contradictory style cues blend into uncanny output, just as they do with still models.

One thing is specific to H3. Because the encoder is a **VLM** (Qwen3-VL-32B), it parses the prompt as language with real instruction-following. Clause structure and explicit relationships carry through. Write sentences, not tag lists.

---

## 6. Approximating H3-Context-IR

The module that turns free-form multimodal input into the structured representation H3-Base consumes is **not in the open release**, and the model card calls it critical to output quality. Locally, your prompt goes in raw. That gap is the most likely reason a local result underwhelms against the launch reel.

The model card describes what Context-IR does: instruction parsing, cross-modal association, temporal understanding and logical reasoning, all serialised into a structured representation. It also says the module *"may also supplement missing or underspecified semantic details."*

Approximating it locally means doing that work yourself:

1. **Resolve the references explicitly.** With multiple inputs, say which is which and how they relate — *"the woman from image 1, in the setting of image 2, with the voice from audio 1."* Context-IR would infer these associations reliably. Raw H3-Base will not.
2. **Make the timeline explicit.** State what happens first, next, last. Temporal understanding is one of the module's stated jobs.
3. **Fill in the underspecified.** Decide anything a competent director would decide — lighting, mix, framing — rather than leaving it open. The module that would have supplemented those details is absent.
4. **Use an LLM as a pre-pass.** Have a capable model expand your short brief into a dense, explicit, structurally resolved prompt before it reaches H3. This is the same shape as Wan's official prompt-extension feature, and there is no reason it should not help here too. Whether it actually closes the gap is **unverified** `[flagged — re-verify]`.

MiniMax also publishes an API that reproduces the official workflow, plus official prompting skills on GitHub. If parity with the demos matters, that path is the honest one.

---

## 7. Worked examples

**T2VA — the audio doing structural work:**

> A short-order cook works a griddle in a cramped diner kitchen at night, flipping and plating in one continuous motion. Warm tungsten overheads, steam catching the light. The camera holds a locked-off medium shot. Realistic live-action, shallow depth of field.
> Audio: bacon fat spitting and hissing on the flat-top, a spatula scraping steel, plates clattering into a stack, muffled conversation from the dining room. No music.

**FL2VA with dialogue.** The reference still carries the picture, so the prompt narrows to action, camera and sound:

> She turns from the window to face the room and says, in English, quietly and without warmth, "You should go."
> Slow push in to a close-up. Audio: her line forward and close, faint rain on glass behind it, room tone otherwise silent. No music.

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

- `[video editing]` and `[audio reuse]` are **pre-trained summary keywords** from the official reference guide, not free text. The first biases the model toward the source frames instead of a fresh generation. It is **not** frame-for-frame tracking. That difference is the whole reason SKILL.md's suite table sends exact motion transfer to [`scail-2`](../../scail-2/): H3 takes the source clip as *conditioning* and renders new frames from it, so the output resembles the driving performance rather than following it. That is fine for a character swap in a shot you control, and wrong for footage that has to match cut-for-cut. `fully_preserved` and `attribute_transfer` are the retention keywords.
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

### Timestamps

Format is `mm:ss.000`. Two rules:

- **Never timestamp the first shot.** Omitting timestamps entirely lets the model choose its own cuts, which is often fine. Using them gives you control of pacing, comic timing and how long a reaction holds.
- **Position is semantic.** The timestamp binds to the action it sits next to:

| Written | Means |
|---|---|
| *at 00:03.000 she lifts her shirt, which exposes her shoulders* | the **lift** starts at 3 s |
| *she lifts her shirt, which exposes her shoulders at 00:03.000* | the **exposure** happens at 3 s |

### Budget time against content

The model tries to fit everything you asked for into the duration you gave it. Ask for ten seconds of action in five, and it crams, overlaps and truncates. People misread that as the model being bad at dialogue. **Allow ~3 s for any fiddly physical action** (removing one garment, opening a stuck door, a prop handoff), and keep dialogue short for 5–7 s clips.

**Multi-step sequences are where this compounds, and undressing is the worked case.** The rule is **≥3 s per garment, each item named in its own clause, in order.** Three garments make a nine-second clip, not a five-second one with a longer sentence. `[community — nsfwVariant]` The compressed version fails so reliably because the two rules above act together. One clause covering three items reads as **one beat**, so the time budget allots it one beat's worth of seconds, and the mechanical path for items two and three never gets described at all. Written out item by item, you get three beats, three time allocations and three described trajectories, and the garments stop teleporting. The same shape applies to any sequence of similar small actions: unpacking a bag, setting a table, a fight exchange.

**Draft at 0.2 MP first.** A 608×352 pass takes a few minutes and shows you the timing, the shot order and whether the model understood the brief. Fix the prompt there, and spend the long run once.

### The shot list

```
[Shot 1] A medium close-up of … he opens his mouth as if to speak, then shakes his head.
[Shot 2] At 00:06:000 the camera cuts to a static shot framing … arms crossed.
[Shot 3] At 00:10:500 the camera pans quickly back to …, a slow push in to his face.
```

Shot 2 starting at 6 s and shot 3 at 10.5 s tells the model to hold that glare for four and a half seconds. Field names seen in circulating structured prompts: `integrated_multimodal_description`, `subject_definitions`, `retention_analysis`, `overall_soundscape`, `non_diegetic_music` (write `N/A` or `none` for no score).

### Dialogue tags, restated because they fix two bugs at once

Write `<d>[Language, in X's voice] line</d>`, with the speaker named — either by name or through the `<Subject N>` system. Wrong-speaker attribution and gibberish dialogue both come from skipping this. `[community — GrayingGamer]`

---

## 9. Prompt tooling

Writing H3 prompts by hand is slow, and the formatting is fussy. LLMs are good at the content and bad at the syntax, and they drift on small revisions. Two community tools split that problem the right way: you make the creative decisions, and the tool owns the structure.

| Tool | What it is |
|---|---|
| **`BMB12d3/minimax-h3-prompt-composer`** | Offline browser app. All five modes (T2VA, I2VA, FL2VA, L2VA, Ref2VA), reusable characters/environments/voices/continuity frames, camera builder and visual path planner, timed shots and action beats, and **validity checks** for structure, timing, references, camera conflicts, audio and input routing. Runs alongside ComfyUI so you can compose the next shot while one renders |
| **`duckyshell/ComfyUI-MiniMaxH3-Prompt-Writer`** | In-ComfyUI UI extension. A **local** Gemma 4 multimodal model reads your actual references and writes the prompt against the official guides. Tiers from 8 GB (Gemma 4 E4B Q3) to 32 GB (31B Q4); the author's pick is the 24 GB tier. Video references are analysed as an ordered contact sheet; audio can be tagged `<Audio N>` but the local model cannot hear it, so describe its role. Needs the CUDA build of `llama-cpp-python` |

Both are `[community]`, and both are young. But the general lesson stands without either tool: **let a model draft, then fix the ordering words and the timestamps yourself.**

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
