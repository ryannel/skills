# LTX-2.5 — prompting guide

This file owns the prompt. It covers the register, the six elements, the audio half, and above all **multishot**. Multishot is the model's headline capability, and it is entirely a prompting technique. This file does not cover graph wiring, settings, or LoRA loading. Those live in [`setup-and-workflows.md`](setup-and-workflows.md).

Quotations marked as the vendor's come from the official prompt guide (`ltx.io/blog/ltx-2-5-prompt-guide`, Rachel Luxemburg, 2026-08-10), from the LTX-2 README's "Prompting for LTX-2" section, and from `docs.comfy.org`'s per-mode notes.

## Contents

1. [The register the encoder wants](#1-the-register-the-encoder-wants)
2. [The six elements](#2-the-six-elements)
3. [The audio half](#3-the-audio-half)
4. [Multishot — the whole technique](#4-multishot--the-whole-technique)
5. [Per-mode prompting: T2V, I2V, FLF2V](#5-per-mode-prompting-t2v-i2v-flf2v)
6. [Letting the prompt set the duration](#6-letting-the-prompt-set-the-duration)
7. [Pacing shots inside a fixed length](#7-pacing-shots-inside-a-fixed-length)
8. [Vocabulary](#8-vocabulary)
9. [Dub-It dialogue replacement](#9-dub-it-dialogue-replacement)
10. [The prompt enhancer question](#10-the-prompt-enhancer-question)
11. [Common mistakes](#11-common-mistakes)
12. [Multishot *and* a consistent character — the composed path](#12-multishot-and-a-consistent-character--the-composed-path)
13. [Drop-in templates](#13-drop-in-templates)

---

## 1. The register the encoder wants

LTX-2.5 conditions on a **custom Gemma 4 12B**, which is a decoder language model. That is the same encoder class as [`z-image`](../../z-image/) and [`flux-2`](../../flux-2/) on the image side. The consequence is the same too: **the model reads sentences, not tags.** Comma-delimited keyword strings under-specify it. Negative-style phrasing such as "no blur, not cartoon" does nothing on the distilled path, because guidance there is 1 and the negative conditioning is inert.

The vendor's own rules, verbatim from the README:

> "When writing prompts, focus on detailed, chronological descriptions of actions and scenes. Include specific movements, appearances, camera angles, and environmental details - all in a single flowing paragraph. Start directly with the action, and keep descriptions literal and precise. Think like a cinematographer describing a shot list. **Keep within 200 words.**"

The blog adds three universal principles, also verbatim:

> "**Keep the scene focused** — a few clear characters and actions read better than a crowded frame. **Keep lighting consistent** — use one coherent light logic per shot; mixed light sources confuse the result. **Start simple and layer** — begin with the core shot, then add detail as you iterate."

For a single shot, the blog asks for **4–8 descriptive sentences** in the present tense. Describe camera movement *relative to the subject*, and scale the amount of detail to the shot size. Treat 200 words as the hard edge. The README gives a word cap, and the blog says to match length to complexity. The cap is the safe reading of the two.

**There is one licensed exception to "no screenplay format."** The blog permits screenplay style, meaning scene headers, character cues, and quoted dialogue, for scenes with dialogue or precise timing. Read that permission as applying *within one shot*. It does not license a shot list, because §4's rule against sluglines is about cuts.

---

## 2. The six elements

This is the blog's checklist, in the order the blog gives it. Missing elements are not defaults. They are simply unspecified, and the model fills them with whatever it finds plausible.

| Element | What to write |
|---|---|
| **Establish the shot** | Shot scale and angle in real cinematography terms — wide establishing, medium, over-the-shoulder, low-angle. If you omit it, you get a locked-off medium |
| **Set the scene** | Lighting, colour palette, surface textures, atmosphere. If you omit it, you get flat, generically lit interiors |
| **Describe the action** | "A natural sequence, flowing clearly from beginning to end." If you omit it, you get a near-static tableau — the classic failure of writing an image prompt for a video model |
| **Define the characters** | Age, hairstyle, clothing, distinguishing features. Express emotion through **physical cues**, not abstract labels |
| **Identify camera movement** | The move, and — the guide is specific here — **how subjects appear *after* the movement**, which "helps the model complete the motion accurately" |
| **Describe the audio** | Dialogue in quotation marks with language and accent named; SFX; music; or their absence |

"Express emotion through physical cues" is the element that changes the most output for the least effort. *"Her jaw tightens and she looks away"* gives the model geometry to animate. *"She is upset"* gives it only a label.

---

## 3. The audio half

LTX denoises audio and video in one sequence. So **audio you do not describe is not silent. It is unspecified**, and the model supplies something. [`minimax-h3`](../../minimax-h3/) turns this same structural fact into its one rule, and the rule applies here for the same reason.

Three consequences are specific to LTX:

- **Dialogue goes in quotation marks**, with the language and accent named when they are not obvious. The repo's own quick-start prompt is the best worked example the vendor publishes. It inlines sniffs, describes the voice ("a deep male voice and a satisfied tone"), and carries three quoted lines, all inside one flowing paragraph.
- **Silence is an instruction.** "No music; only wind" is meaningful and often necessary.
- **A silent *input* clip fails outright** on V2V and upscale runs, because there is no video-only path through the joint sequence. Add a silence track first. `[community — DaLyon92x]`

One thing is worth checking on your own material. In MiniMax H3, stripping `<d>` dialogue tags removed audio glitches at clip start `[community — Thorozar]`. Both models encode audio and video jointly, so LTX may have a similar artefact. That has not been tested here.

---

## 4. Multishot — the whole technique

There is no node, no flag, no checkpoint and no `--shots` parameter. Multishot is a way of writing one paragraph. Everything below quotes the vendor's own guidance, because this is the part of the model with the least community craft behind it yet.

### 4.1 The form

> "Write the full scene as **one chronological paragraph** (or a short sequence of sentences). Do **not** use a shot list, numbered beats, or screenplay sluglines unless you also describe the cut in prose."

### 4.2 The four rules, at every cut

1. **Name the transition** in natural language: "A hard cut transitions to…", "The view cuts to a close-up of…", "A match cut connects…", "The image dissolves into…".
2. **Re-establish the new shot**: shot scale, camera angle, who or what is in frame, and lighting if it changed.
3. **Keep identity consistent** by reusing the same visual identifiers for recurring people or objects ("the woman in the red coat, earlier at the table, now…").
4. **State audio continuity**: "the piano score continues across the cut", or "the dialogue drops; only wind remains."

Rule 3 is the one that reveals what the model is actually doing. **Identity is re-anchored from the text at each cut. It is not carried by a persistent embedding.** That is why the guide puts the work on you. It is also why identity drift across cuts is a prompting failure before it is a model failure. This is an inference from the guide's own instruction, not a vendor statement.

### 4.3 Single-shot versus multi-shot, the guide's own contrast

| | Single-shot | Multi-shot |
|---|---|---|
| Camera | One continuous take | New framing after each cut |
| Transitions | Camera moves only — pan, push-in | **Name the edit**: hard cut, match cut, dissolve |
| Continuity | Same space and subjects throughout | Re-identify subjects when they reappear; say what carries across |
| Audio | One continuous soundscape | At every cut, say whether music, dialogue or ambience continues or changes |

### 4.4 The limits, verbatim

> "**Prefer 2–4 shots** in one generation; more cuts usually need clearer, shorter beats per shot."

**Count shots, not cuts.** 2–4 shots means **1–3 cuts**, so a three-cut sequence is at the ceiling rather than comfortably inside it. The distinction matters because the four rules do not all scale the same way. **Rule 2 (re-establish) costs you once per shot.** **Rules 1, 3 and 4 (name the transition, re-identify, state audio continuity) cost you once per cut.** An N-shot prompt therefore spends roughly `N` re-establishments plus `3(N−1)` cut clauses. At four shots, that is nine cut clauses inside a 200-word budget before any of the action is described. This arithmetic comes from the four rules, not from the vendor, but it is usually what makes four shots feel cramped.

> "**Avoid conflicting geography or unexplained costume changes** between cuts unless the cut is meant to jump time or place and you say so."

> "Use a single continuous take when you want unbroken camera motion, intimate performance, or dialogue that must stay lip-synced in one framing. **For image-to-video from a first frame, prefer a single continuous take** unless you intentionally describe a cut away from that opening image."

That last quote covers the interaction people get wrong: **multishot and I2V pull against each other.** The conditioning frame fixes a framing, and a cut then has to abandon it. A multishot prompt on an I2V run therefore tends to produce either a refused cut or a discarded reference.

### 4.5 The vendor's worked example, verbatim — three shots

> "A wide shot frames a rainy city intersection at dusk, neon signs reflecting on wet asphalt. A young woman in a yellow raincoat walks toward camera, gripping a folded newspaper, while cars hiss past behind her. Soft synth music and distant traffic fill the air. A hard cut transitions to a medium close-up of her face under the hood, raindrops catching the neon as she looks off-screen left; the synth score continues across the cut, traffic muffled. She whispers, 'He's late.' Another hard cut jumps to a low-angle shot of a man's scuffed boots stepping into a puddle at the curb; the music drops to a low drone. He lifts his head into frame — short dark hair, soaked jacket — and smiles toward her off-screen as a bus rumbles past."

Read it against the four rules and every one is visible. *"A hard cut transitions to"* is rule 1. *"A medium close-up of her face under the hood"* is rule 2. *"Her face"* is still anchored to "young woman in a yellow raincoat", which is rule 3. *"The synth score continues across the cut"* and *"the music drops to a low drone"* are rule 4.

### 4.6 A prompt that fails, and which rule it broke

This example is worth reading before another good one, because the failure mode is silent: you get a clean single take rather than an error.

> *"A woman in a yellow raincoat walks through a rainy intersection at dusk. Close-up on her face, rain on her hood. Low angle on a man's boots in a puddle. He looks up and smiles."*

Four shots are intended. What this produces is **one continuous take**, probably a slow push-in on the woman. Here is why, rule by rule:

- **Rule 1 is absent.** "Close-up on her face" is a shot *description*, not a transition. Nothing tells the model an edit occurs, so it interpolates camera movement between the framings instead of cutting. This is the whole failure. The other three compound it.
- **Rule 2 is half-done.** The shot scale is named, but nothing else is re-established: no angle, no lighting state, no confirmation of who is in frame.
- **Rule 3 fails at "her face".** The identifier is dropped after the first sentence, so the model has no anchor to re-attach the identity to.
- **Rule 4 is missing entirely.** No soundscape is given at all. On a jointly-denoised model, that means the audio is unspecified rather than absent.

The repair is mechanical: *"…walks through a rainy intersection at dusk; rain hisses on the awnings. **A hard cut transitions to** a medium close-up of **the woman in the yellow raincoat**, hood up, neon catching the raindrops; **the traffic drops to a muffled hum across the cut**. **A second hard cut** drops to a low angle on a man's scuffed boots stepping into a puddle…"* The content is the same, but three cut clauses have been added. Now it reads as an edit.

### 4.7 Dialogue across cuts

Two things are unresolved here, and both are worth knowing before you write a dialogue-heavy sequence. First, **where in a shot a quoted line lands is not controllable.** The model places it, and nothing in the vendor guidance exposes timing within a shot. Second, **what happens when two shots each carry dialogue has no documented behaviour.** The vendor's own worked example puts exactly one line in one shot. Both questions tie back to the identity question in §4.8.

The practical consequence: for a two-line exchange across a cut, expect to generate and select rather than to direct. If lip-sync accuracy matters more than the cut does, the vendor's own advice applies: use a single continuous take, where "dialogue must stay lip-synced in one framing."

### 4.8 Does identity actually hold?

This is unresolved. The vendor claims character, environment, lighting, voice and style all survive the cut. One named practitioner reports it works on 2.5: *"the multi shots maintain consistency a lot better"* `[community — hidden2u; single report]`. That is set against a documented failure on 2.3: *"as soon as I wanted to make just a few simple shots of the same character with cuts, LTX wasn't even remotely capable of that"* `[community — Dry-Statistician-684]`. Nobody has published a side-by-side comparison. Where a quoted line lands inside a shot (§4.7) is not settled either. `[contested]` Treat the four rules as necessary but not proven sufficient. See [`characters.md`](characters.md) for what to do when identity slips.

---

## 5. Per-mode prompting: T2V, I2V, FLF2V

The mode changes the prompt's *job*, not its register. `[official — docs.comfy.org]`

**T2V.** "Include the shot type, scene, action, characters, and camera movement in one flowing paragraph." The prompt does all the work in this mode, so this is where the 200-word budget binds.

**I2V.** This is the important one, because it is the opposite of the T2V instinct:

> "Describe what happens next — write the motion, camera movement, and sounds that follow from the input image; **do not re-describe what is already visible**."

Re-describing the reference costs you words and fights the conditioning. The docs also suggest anchoring explicitly, with phrasing like *"Use the provided start image as the first frame"* when writing a continuation. And per §4.4, keep it a single continuous take.

**FLF2V.** "Describe the transition" rather than either end state, since both are given. Keep the two images at the same aspect ratio, because mismatched frames produce a scramble rather than an error.

---

## 6. Letting the prompt set the duration

Load the optional `ltx-2.5-duration-head` patch and set `--auto-duration MIN_SECONDS MAX_SECONDS`, or simply omit `--num-frames`. The model then chooses the clip length from the prompt: *"a one-line action stays short, a multi-shot sequence runs longer."* On the hosted API the equivalent is sending `"duration": null`.

There are two traps. **Auto-duration cannot be combined with a fixed last frame** on I2V, because a specified end frame requires a known length. And on prepaid API accounts, **credits are held against the longest duration your resolution and fps allow**, so a six-second request is declined if you cannot cover twenty.

---

## 7. Pacing shots inside a fixed length

Once `--num-frames` is pinned to the lattice, you have given up auto-duration. The two are mutually exclusive, since auto-duration works by *omitting* the frame count. Shot balance is then your job, and LTX gives you no timing parameter for it.

There are three levers, in the order they work:

1. **Fewer shots.** Ten seconds across four shots is 2.5 s each. Across two shots, it is five. Beat length is the thing that actually degrades, and the vendor says so ("more cuts usually need clearer, shorter beats per shot").
2. **Roughly equal sentence weight per shot.** The prose is the only pacing signal the model has, so a shot described in one clause and a shot described in four sentences will not come out equal. Balance the description to match the intended balance of screen time.
3. **Explicit timestamps, with low expectations.** Writing bracketed time ranges into the prompt is the community's pacing tool. It is also the thing LTX is specifically reported to *almost* do. One practitioner comparing models found scene changes landing where intended on a rival and called it "the thing LTX kept almost doing and fumbling" `[community — Moarkush]`. It is worth trying on a long clip, but not worth relying on.

**Do not budget shot time by trimming the cut clauses.** They are what holds identity and audio across the edit. Cutting them to buy words is how a multishot prompt collapses into one continuous take.

## 8. Vocabulary

The blog publishes lexicons for categories, lighting, textures, colour palette, atmosphere, ambient sound, dialogue style, volume, camera language, film characteristics, scale and pacing. Two are worth keeping to hand, because the model responds to them most literally. **Camera:** follows · tracks · pans across · circles around · tilts upward · pushes in · pulls back · overhead view · handheld movement · over-the-shoulder · wide establishing shot · static frame. **Volume:** whisper · mutter · shout · scream.

Two usage notes. First, **"static frame" is a real instruction**, and it is worth writing when you want it. The model's default is already close to static, and an unstated camera reads as indecision. Also, per §2, always pair a move with its result state. Second, film-look vocabulary such as grain, halation, anamorphic flare, and shallow depth of field works one or two terms at a time. A stacked list reads as a preset and flattens the shot.

## 9. Dub-It dialogue replacement

`DubItPipeline` is a **beta, 2.3-IC-LoRA-only** path, and it does not support 2.5. Its prompt is a fixed template: `[Speaker] is speaking [Language/Accent], saying: "[Dialogue]"`. The validated languages are **English, French, Spanish, German, Russian**. The docs are explicit about three requirements. Supply the **full dialogue text**, because "It does not translate dialogue for you." Write it in the **native script**. Use **one speaker only**, because "the beta IC-LoRA does not distinguish between multiple speakers." The craft note is timing. Match the original's syllable length, erring slightly long, because "prompt too long: the model might skip words. Prompt too short: the output might sound slow and unnatural."

## 10. The prompt enhancer question

The official templates wire in a Gemma 4 E2B enhancer (`TextGenerateLTX2Prompt` in the graph, `--enhance-prompt` on the CLI) that expands a short prompt into the register above. **The negative prompt is never enhanced.**

The enhancer has two documented problems, and they are different in kind:

- **Speed.** *"I had to turn it off cause it was literrally taking 20 minutes… Once I turned it off a 3 sec clip was done in 3 min"* `[community — AniZeee]`. This was diagnosed as the enhancer model not fitting in VRAM alongside the transformer `[community — MixDistinct1932]`. The problem is not universal: another named user saw only 30 seconds of overhead `[community — rinkusonic; contested]`.
- **Correctness, which matters more.** *"I'm using the template default, but with tougher prompts, I will get a completely random video. Turning off the prompt enhancer fixes the issue at least partially."* `[community — Hans-Wermhatt]`

The pattern that works is the same idea moved outside the graph. Write one line, expand it with a fully-loaded local LLM, then feed the expansion in as a plain prompt. One named user drives `gemma 4 12b` through ComfyUI's qwenvl nodes plus llamacpp for exactly this `[community — intLeon]`. An external enhancer you can inspect is the safer version of the pattern.

**The default position: write the prompt yourself in the §2 form and leave the enhancer off.** Turn it on only when you are exploring and the prompt is deliberately thin.

---

## 11. Common mistakes

| Mistake | Why it fails | Instead |
|---|---|---|
| Comma-separated keyword string | The encoder is a decoder-LM; tags under-specify it | Flowing prose, present tense |
| Tuning the negative prompt on the distilled path | CFG 1 collapses conditional and unconditional | Say what you want; or move to the dev checkpoint |
| A shot list with numbered beats | The vendor discourages sluglines "unless you also describe the cut in prose", so a bare list gives the model nothing to place the edit on | Name each cut in prose (§4.2) |
| A multishot prompt on an I2V run | The conditioning frame and the cut fight each other | Single continuous take, unless the cut away is deliberate |
| Re-describing the reference image in I2V | Spends the word budget contradicting the conditioning | Describe only what happens next |
| Five or six cuts in one generation | Past the vendor's 2–4 range, beats get too short to establish | Split into separate generations and join in post |
| Abstract emotion labels | Nothing to animate | Physical cues — jaw, hands, gaze, posture |
| No audio described | Audio is unspecified, not silent | Name dialogue, SFX and music, or their absence |

---

## 12. Multishot *and* a consistent character — the composed path

This is the brief most readers actually arrive with. The two techniques it needs are documented separately, with nothing joining them. Here is how they compose.

**Start with the collision, stated plainly.** Multishot wants **one flowing chronological paragraph** (§4.1). The Ingredients IC-LoRA, which is the best no-training identity path (see [`characters.md`](characters.md)), wants a **two-part string**:

```
Reference sheet: <what the panels contain>
Generated video: <the action>
```

**They compose by nesting, not by competing.** The two-part string is a *document frame* that tells the adapter which half of the text describes the reference. The multishot rules govern *prose structure* inside the action half. So the entire multishot paragraph goes inside `Generated video:`, including its cuts, transitions, re-identification, and audio continuity. `Reference sheet:` stays a plain description of the panels, with no cuts in it. **No vendor example of this combination exists.** This is a reasoned composition, not a documented one.

**Which pipeline:** `ICLoraPipeline`, on the **distilled** checkpoint. It will not run on dev. The task-mode selector files this under "V2V with control", which undersells it. An IC-LoRA's reference input is whatever it was trained to consume, and Ingredients consumes **reference panels**, not a driving clip.

**The version wrinkle, which turns out to be fine.** Ingredients is a **2.3**-trained adapter, and multishot is **2.5**-only. So this path needs the 2.3 adapter loaded onto the 2.5 distilled transformer. That is exactly what Lightricks' own shipped 2.5 IC-LoRA workflows do, verified by tracing the graph. It is not a hack.

Here is a **worked prompt** with two shots and one cut, which is where to start rather than four:

> `Reference sheet:` *Three panels of the same woman in her thirties — short dark hair, a grey wool coat, a thin silver chain. Front, three-quarter and profile, even neutral lighting, plain background.*
>
> `Generated video:` *A wide shot frames a station concourse at night, cold overhead light on wet tile, departure boards flickering behind. The woman in the grey wool coat walks toward camera holding a paper cup, footsteps and a distant announcement filling the space. A hard cut transitions to a medium close-up of the woman in the grey wool coat, the silver chain catching the light as she glances off-screen right; the concourse ambience continues across the cut, the announcement now muffled. She says quietly, in English, "It's already gone."*

**Four things go wrong on this path, in the order they will:**

1. **Identity survives the shot but not the cut.** Ingredients conditions frame-level, and a cut replaces the frame. Repeat the identifier phrase *verbatim* at the cut: "the woman in the grey wool coat", not "she". Prose re-anchoring is doing as much work here as the adapter.
2. **The sheet's background bleeds in.** Matte the panels, or state the environment explicitly in the action half.
3. **The adapter fights the cut at high strength.** Start `attention_strength` low, around 0.4–0.6, and raise it only if identity slips. At 1.0, the reference can hold the framing against the edit you asked for.
4. **Four shots is too many for a first attempt.** Every cut is an opportunity for the adapter and the prose to disagree. Get one cut working, then add more.

**If this still drifts, stop composing and split.** Generate one shot per call, each conditioned on the same locked still, and cut them together in post. You lose the single-pass property that makes LTX interesting. But identity stops being a per-cut gamble, and for a character-critical piece that is the right trade.

## 13. Drop-in templates

**Single continuous take (T2V):**

> `[Shot scale and angle]` frames `[location]` at `[time of day]`, `[light logic]`. `[Character: age, hair, clothing, one distinguishing feature]` `[physical action, in sequence]`. The camera `[move]`, `[how the subject appears after the move]`. `[Ambient sound]`; `[music or "no music"]`. `[Optional: a line of quoted dialogue, with the language named]`

**Image-to-video:**

> Use the provided start image as the first frame. `[What happens next, as physical action]`. The camera `[move]`, `[result state]`. `[Sound that follows from the action]`; `[music or none]`.

**Multishot, two to four shots (one to three cuts):**

> `[Shot 1: scale, location, light]`. `[Character A: full visual identifier]` `[action]`. `[Soundscape]`. `[Named transition]` to `[Shot 2: scale and angle]` of `[Character A, re-identified by the same words]`, `[what has changed]`; `[what the audio does across the cut]`. `[Named transition]` to `[Shot 3]`, `[re-establish]`; `[audio state]`.

For **foley on an existing silent clip** (V2A, video frozen), describe only the sound: surfaces, impacts, room tone, distance. Do not re-describe the picture. The video branch is frozen, so words spent on it are wasted.
