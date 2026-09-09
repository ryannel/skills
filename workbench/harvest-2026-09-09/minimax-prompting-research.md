# MiniMax H3 / Hailuo — tag syntax and emotional direction research

Research date **2026-09-09**. Target skill: `skills/generative-media/minimax-h3/`.

**Headline: the premise needs correcting.** There is no emotion-tag syntax in H3, and the bracketed camera tags (`[Push in]`, `[Truck left]`) belong to a *different product line*. What the community has actually built is a layer of **authoring shorthand that is translated into prose before it reaches the model** — plus, at least one popular tool advertising an `[emotion]` slot as "official" when it is not. The genuinely new craft is real; the tag framing is not.

---

## What the skill already says

The published skill (`references/prompting-guide.md`, 4,321 words; SKILL.md §"H3 directs itself") carries:

- **`[Shot N]`** with `mm:ss.000` timestamps, "never timestamp the first shot", timestamp position is semantic.
- **Dialogue tag** written as `` `<d>[Language, in X's voice] line</d>` `` with the speaker named — `[community — GrayingGamer]`.
- **Field names** listed as "seen in circulating structured prompts": `integrated_multimodal_description`, `subject_definitions`, `retention_analysis`, `overall_soundscape`, `non_diegetic_music`, plus `detailed_description`.
- **Ref2VA keywords** `[video editing]`, `[audio reuse]`, `fully_preserved`, `attribute_transfer`.
- **Camera**: "State the camera, including when you want none. Write `static shot`." No vocabulary list, no amplitude/speed axis, no bracket syntax.
- **Ordering craft**: `and` → sequential, `then`/`while`, "80% of the jank"; over-describe the failing element; activity not geometry; ≥3 s per garment; draft at 0.2 MP.
- **Emotional direction: essentially nothing.** The only adjacent line is §4 "Give the delivery — flat, urgent, whispered, over the shoulder. It shapes the performance and the facial animation together." No acting section, no observable-behaviour rule, no statement of what emotion syntax H3 *rejects*.
- **Prompt length**: §2 says only "Expect to write longer prompts here than you would for the hosted API."
- **Context-IR** (§6) is "not in the open release", with an LLM pre-pass as the local approximation, `[flagged — re-verify]`.

---

## Tag / directive syntax found

| Tag or pattern | What it does | Source class | URL | Date |
|---|---|---|---|---|
| `[Truck left]`, `[Truck right]`, `[Pan left/right]`, `[Push in]`, `[Pull out]`, `[Pedestal up/down]`, `[Tilt up/down]`, `[Zoom in/out]`, `[Shake]`, `[Tracking shot]`, `[Static shot]` — 15 commands | Bracketed camera control for the **hosted Hailuo line only**: `T2V-01-Director`, `I2V-01-Director`, `MiniMax-Hailuo-02`, `MiniMax-Hailuo-2.3`. Multiple in one bracket = simultaneous (max 3 recommended); multiple brackets = sequential; command goes first in the prompt | Official (MiniMax API), relayed by aggregator | https://minimax-ai.chat/models/minimax-hailuo-director-models/ | page 2026-07-08, checked 2026-08-13 |
| Same brackets on **H3** | **Not documented.** "MiniMax-H3 V2 reference does not document bracketed command syntax" | Official-by-omission | https://minimax-ai.chat/models/minimax-hailuo-director-models/ | 2026-08-13 |
| `Zoom In/Out, Push In/Pull Out, Pan Left/Right, Truck Left/Right, Tilt Up/Down, Pedestal Up/Down, Arc Shot, Tracking Shot, Static Shot, Shake Slightly/Strongly, POV, Roll Clockwise/Counterclockwise` | H3's **camera motion-type vocabulary**, 12 entries. Written as natural English *inside* the sentence: "Camera motion should be written as a natural English action within the shot, rather than stacked as separate labels at the end of a sentence" | Official | https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md §4.3 | model card 2026-08-13 |
| `with small amplitude` / `with large amplitude`; `at slow speed` / `at fast speed` | The other two axes of a complete camera expression. "Add amplitude and speed only when they are meaningful; medium amplitude and normal speed are usually omitted" | Official | same, §4.3 | 2026-08-13 |
| `[Shot 1]` … `[Shot N] At MM:SS.mmm,` | Shot segmentation. First shot carries no timestamp; later cut times strictly increasing and inside the duration | Official | same, §4.2 | 2026-08-13 |
| `(S1)`, `(S2)`, `(S1,S2)` | Stable speaker IDs, compound ID for simultaneous group speech. "A speaker keeps the same ID across shots; characters who never vocalize receive no speaker ID" | Official | same, §4.4 | 2026-08-13 |
| `<d>[English] words</d>` | Dialogue. **"Place the speaker's identifying phrase, ID, action, and delivery outside `<d>`. Inside `<d>`, include only the language tag and the actual user-provided spoken content."** | Official | same, §4.4 | 2026-08-13 |
| `says in an off-screen voiceover` | Fixed phrase for V.O.; must be followed by a statement that the on-screen character's lips remain closed | Official | same, §4.4 | 2026-08-13 |
| `<scenetrans>` / `<cutoff>` | Dialogue crossing a cut / speech truncated by the end of the video | Official | same, §4.4 | 2026-08-13 |
| `[unclear]` | Placeholder for unintelligible spans in reused reference audio | Official | .../VIDEO_PROMPT_WRITING_GUIDE_ref_en.md §5.4 | 2026-08-13 |
| `"…"` double quotes | Visible on-screen text, preserved verbatim, untranslated | Official | base guide §4.5 | 2026-08-13 |
| `keyframe completion`, `reference generation`, `video editing`, `video continuation`, `audio reuse`, `audio reference` | The **full** `summary` task-type keyword set (skill carries 2 of 6) | Official | ref guide §3 | 2026-08-13 |
| `fully_preserved`, `partially_preserved`, `attribute_transfer`, `weak_reference` (visual); `fully_copy`, `partially_copy`, `reference`, `weak_reference` (audio) | The **full** `retention_analysis` keyword sets (skill carries 2 of 8) | Official | ref guide §4.1, §4.2 | 2026-08-13 |
| `<Subject N>` explicitly covers "Styles, actions, **expressions**, or poses" | An expression can itself be a named reusable Subject drawn from a reference asset | Official | ref guide §2.1 | 2026-08-13 |
| `<Subject N> (SN) [emotion] says: <d>[Language] "…"</d>` | Advertised as "**Official** MiniMax Dialogue & Voice Acting Syntax … for vivid character voices and live acting" | **Contested — single tool's claim, contradicted by the official guide** (which puts delivery outside `<d>` in prose and defines no `[emotion]` slot) | https://github.com/1038lab/Comfyui-Minimax-H3-Promptor README, v1.3.0 | 2026-08-18 (repo pushed 2026-09-03, 218★) |
| `[whispering]`, `(laughs)`, `*sighs*`, `<break time="1s">` | **Do not use.** "H3 has no emotion-tag syntax at all… these are ElevenLabs/Bark syntax — H3 would read them as words to speak" | Community, well-reasoned | https://github.com/hyukudan/ComfyUI-MiniMax-H3-Prompt-Enhancer | README, repo pushed 2026-08-29 |
| Emoji/bracket **authoring marks**: 😠 😌 😰 🤫 📢 ⏸️, and ~30 bracket aliases in EN/ES (`[enfadada]`, `[susurro]`, `[pausa]`) | Tool-side shorthand placed beside a quoted line. **Resolved to prose and stripped before the prompt reaches H3**; the validator fails a finished prompt that still contains one | Community (one tool, but internally verified) | same | 2026-08-29 |
| `⏸️` pause | "**is our own convention, not a documented one.** The official guides contain no pause mechanism whatsoever… rendered as an ellipsis inside the quote" | Community, self-flagged contested | same | 2026-08-29 |
| `@Image 1:` / `[0–2 seconds]` | fal's house convention for assigning reference jobs and timed segments | Community/vendor — **not official**, and the bracketed time range conflicts with the official `[Shot N] At MM:SS.mmm` form | https://fal.ai/learn/devs/minimax-h3-prompting-guide (Bennett Heyn) | stated 2026-07-30 (pre-dates the 2026-08-02 open release; treat the date as unreliable) |

**The bottom line on tags.** Two syntaxes are circulating under one name. The hosted Hailuo Director/02/2.3 models take stacked bracket commands; H3 takes prose with a defined vocabulary. Neither has an emotion tag. Anything that looks like `[angry]` in a community workflow is either a tool's pre-processing shorthand or a claim no primary source supports.

---

## Emotional direction craft

### The rule everyone independently converges on

**Translate emotion into observable behaviour.** Three independent write-ups state it in near-identical terms:

> "Translate emotion, mood, and abstract states into observable behavior a camera could see: where the eyes go, what the hands do, what the breathing does, what stays still. For example, do not write 'she looks anxious'; write 'her gaze is fixed downward, her fingers grip the table edge, and her shoulders stay raised.'"
> — Naxdy, *Minimax H3 Prompt Enhancer* gist, revised **2026-09-06**, 41★ — https://gist.github.com/Naxdy/43b7422a1e4a79fb8b0489c6c39eaace

RunDiffusion's guide gives the before/after in a commercial register:

> *Before:* "A woman feels confident in a premium city campaign."
> *After:* "The woman steps out of the elevator, straightens her cuff, looks toward the sunrise, and walks past the camera with a restrained smile."
> *What changed:* "Tangible movements and expressions replaced abstract emotional states, enabling the model to place actions on a timeline."
> — https://www.rundiffusion.com/minimax-h3-prompt-guide (undated, August 2026)

The official guide only states the negative half of this rule, and only for the score: "do not use abstract mood words or explain the emotional function of the score" (base guide §4.7). The positive half — how to write acting — is entirely community.

### The picture/sound coupling nobody else states

The strongest single finding, from hyukudan's enhancer README:

> "**Each mark also drives the face, not just the voice.** H3 renders picture and sound together, so a voice-only instruction can hand you an angry line delivered by a neutral face. Every mark therefore carries a visible cue as well."

With worked pairs:

```
"Get out of my house" → shouts; visible: jaw setting, brows driving hard down as the line breaks out
"Don't leave me"      → in a low, unsteady voice, close to tears; visible: eyes filling, blink slowing, mouth going unsteady
```

And the shape rule: cues are written "as a small arc — an opening state, a change, a settled state — because that is the shape the emotional-performance translation asks for and a single frozen state under-seeds it." The same contract "rejects muscle lists, pseudo-biometric precision and stacked simultaneous instructions." (https://github.com/hyukudan/ComfyUI-MiniMax-H3-Prompt-Enhancer)

### A verified round-trip

The same repo publishes an actual generation trace — the closest thing to a controlled before/after in this harvest:

```
in   She says 😠 "Don't touch me". He answers 🤫 "Please, listen to me".

out  The woman (S1) speaks with a hard, angry voice while saying <d>[English] Don't touch me</d>.
     The man (S2) replies with a whispered tone, stating <d>[English] Please, listen to me</d>.
```

"Delivery landed outside `<d>`, each mark stayed on its own speaker … and no emoji reached the model." Two attachment rules fall out: **name the speaker before the line** (the mark binds by reading the attribution you wrote), and **keep the quotation marks** (an unquoted line is treated as direction and may be rewritten). Marks bind to the **nearest quote**, which is what makes two speakers on one line work.

Two exceptions are pinned: 📢 (voiceover) carries **no** visible cue, because the official contract requires the on-screen lips to stay closed; and "framing still wins" — where the face is not readable the beat is carried by posture, breath, gaze or hands, and the writer "may not add a cut, push-in or close-up merely to expose it."

### Structure, order and length

- **Order.** The official recommended openings are positional, not emotional: `[Shot 1]` opens with **style then initial composition** ("Live-action, cinematic, a medium-wide shot frames…"), then subject/appearance, action, camera motion, speaker + delivery + `<d>`, then the two audio fields last (base guide §4.1, §5). In Ref2VA the style sentence moves *before* `[Shot 1]` (ref guide §5.2). Emotion is not a section — it is distributed into the action clauses and the delivery phrase beside each line.
- **Length — a real number at last.** "For generation tasks, `detailed_description` is normally **350–500 English words**. Dialogue-dense content prioritizes fitting the complete spoken timeline rather than mechanically reaching a word count. Video-editing descriptions scale with the complexity of the source video and do not have to follow the generation-task range." (ref guide §5.2). The hosted API caps `positivePrompt` at **2–7,000 characters** (https://runware.ai/docs/models/minimax-h3). ComfyUI does not truncate, so the local path has no ceiling — the 7,000-character limit applies only to API delivery (hyukudan README).
- **Beat placement.** "Put the most important beat in the middle of the timeline, not the last, because the final beat is the one most likely to be squeezed" (Naxdy, 2026-09-06). Same source budgets "roughly four seconds" for a prop change or hand-off — slightly looser than the skill's ≥3 s.
- **Negatives.** "H3 has no negative-prompt field; express exclusions as plain English sentences… they earn their place mainly for things the model adds on its own, namely camera movement and on-screen text" (Naxdy). For a locked frame, "say 'the frame never moves' and list the movements that should NOT happen (no pan, no push-in, no reframing)."
- **Wardrobe.** "Name garments in the text even for referenced subjects, because H3 tends to drift wardrobe across generations" (Naxdy).
- **Reference order is semantic.** "H3 labels references by input order and advances its positional clock on them, so reordering the same references is a different request" (Naxdy).

### The optimizer / expander

- `prompt_optimizer` is a **hosted-API** parameter (defaults true; rewrites and enriches the prompt). Turn it **off when exact control matters** — including when you are using bracketed camera commands on the Hailuo line (https://minimax-ai.chat/guide/hailuo-video-prompts/). It has no bearing on local ComfyUI runs of the open weights.
- **Context-IR is reachable after all.** ComfyUI ships a partner node, `MiniMax H3 Context IR` (a.k.a. `MinimaxHailuo03ContextIRNode`): inputs `prompt`, `duration` 4–15, `ratio`, optional `first_frame`/`last_frame`, up to 9 reference images / 3 videos / 3 audios; output is a STRING enhanced prompt with "Image 1"/"Video 2" position references you must reattach in the same order. https://docs.comfy.org/tutorials/partner-nodes/minimax/minimax-h3 · https://comfy.icu/node/MinimaxHailuo03ContextIRNode
- **Do not send emotion marks through an optimizer.** Every tool in this space strips them before emission and validates that none leaked; the reason is that H3 has no slot for them and would speak them.

---

## Other new H3 workflows/techniques since 2026-08-29

- **`MiniMaxH3AddGuide`** — anchors image, video **and audio** guides at *any* `frame_idx` (negative counts from the end), not just first/last; video guides snap to 5/22/39 frames; nodes chain for multiple anchors. Merged 2026-08-13 by drozbay, shipped in **ComfyUI v0.34.0, 2026-08-26**. Example workflow feeds the first 22 frames of an existing clip plus its audio at `frame_idx 0` to continue both streams. https://github.com/Comfy-Org/ComfyUI/pull/15439 · https://github.com/comfyanonymous/ComfyUI/releases (v0.34.0)
- **Temporal stretch → clips well past 15 s.** musubi-tuner `--output_fps N` (default 24, range 1–24) plus `--stretch_keep_bands K` (3 at 12 fps, 4 removes the last glitches; 2 at 16 fps; 1 at 20 fps). Fixed `--frame_count` at 12 fps doubles clip length for nearly the same compute; equal duration at 12 fps runs ~2.1× faster (124 vs 243 frames). https://github.com/kohya-ss/musubi-tuner/blob/dev/docs/minimax_h3.md §"Temporal stretch" — commit 2026-08-27 (#1072)
- **30 s probed, with named failure modes** (2026-09-05). With `--allow_experimental_duration`, 12 fps × 362 frames = 30 s, the trained maximum latent length; "subject identity and speaker voice stay stable across the full 30 s." Caveats: past ~15.7 s a brightness wobble appears on the final 17-frame group (`--stretch_keep_bands 4` cures it to ~23 s, returns by 30 s — generate one group longer and trim); prompt adherence weakens at the far end; and a 362-frame run packs ~110k rows, **requiring the SDPA strided-value fix** or a non-`sdpa` `--attn_mode`, "without it the whole sample decodes to noise". Anime animates on twos, so 12 fps drops character motion to an effective 6 fps — 16 fps + `keep_bands 2` is the better animation compromise. Same doc.
- **Teacher-matching training** — a LoRA regime beyond guidance loss: `--h3_teacher_matching` with `--h3_teacher_conditions first,last` (default) / `ref` / `subject_ref`, gated by `--h3_teacher_condition_sigma_max` (0.75 for the endpoint and reference teachers; **1.0 for `subject_ref`**, whose identity decisions happen at base sigma 0.92–1.0) and `--h3_teacher_condition_sigma_min 0.15`, plus `--h3_teacher_loss_dc_weight 0.3` and `--h3_teacher_loss_mag_weight 0.5`. `subject_ref` is **the only teacher available with `--one_frame`**. Commits 2026-09-02 → 2026-09-08, same doc.
- **More trainer surface**: one-frame Ref2VA training (2026-09-02), control images as untimed Ref2VA references (2026-09-07), any number of one-frame FL2VA `cond_` slots (2026-09-08), `convert_lora` H3 module names (2026-08-26). https://github.com/kohya-ss/musubi-tuner/commits/dev
- **`MiniMax H3_SparseRef15_Hybrid`** — FL2VA-based hybrid applying "sparse Ref2VA influence through AdaLN across 15 main transformer blocks", no LoRA merging; claims "strong resistance to character drift across long multi-clip generations". Use **FL2VA** LoRAs, not Ref2V ones. https://civitai.com/models/2900456 — 2026-09-06
- **`ComfyUI-H3-Continuum`** v3.7/v3.8 — chunked long-form video+audio with Review Each Chunk, Keep/Retry/Finish, Resume & Takes. https://civitai.com/models/2860061 (2026-08-30) · https://github.com/ukr8b3g-cmyk/ComfyUI-H3-Continuum
- **Reverse-prompt + expansion workflow (NSFW)**, on a shared `H3_NSFW_Physics_Engine.txt` system prompt for a Gemma 4 12B expander. https://civitai.com/models/2866184 — 2026-09-02
- **4-step pipelines at 6 GB VRAM** (v8.0, V2V node, slow-motion bug fixed). https://civitai.com/models/2835250 — 2026-09-07
- **Negative finding:** the official `MiniMax-AI/MiniMax-H3` repo's last commit is **2026-08-15** and the HF model card's `lastModified` is **2026-08-13**. No official prompt-doc change since the skill was written.

---

## Deltas vs the skill

| Finding | Belongs in | Verdict |
|---|---|---|
| H3 has no emotion-tag syntax; `[whispering]`/`(laughs)`/`*sighs*` are ElevenLabs/Bark and would be spoken | `prompting-guide.md` §4, new subsection | **NEW** (and the single most useful correction) |
| Bracketed camera commands are the hosted Hailuo Director/02/2.3 syntax, not H3's | `prompting-guide.md` §5 | **NEW** — pre-empts a common wrong import |
| Official 12-term camera vocabulary + amplitude + speed, written as prose inside the sentence | `prompting-guide.md` §5; SKILL.md default #2 | **NEW**, REINFORCES "state the camera" |
| Delivery/emotion goes **outside** `<d>`; inside is only the language tag and the exact words | `prompting-guide.md` §8 "Dialogue tags" | **CONTRADICTS**: skill says *"Write `<d>[Language, in X's voice] line</d>`"* — the voice attribution belongs outside the tag |
| `(S1)` / `(S2)` / `(S1,S2)` speaker IDs | `prompting-guide.md` §4 and §8 | **NEW** — skill says "the speaker named — either by name or through the `<Subject N>` system", which misses the actual mechanism |
| `<scenetrans>`, `<cutoff>`, `says in an off-screen voiceover` + lips-closed clause, on-screen text in double quotes | `prompting-guide.md` §4 | **NEW** |
| Full 6-term `summary` and 8-term `retention_analysis` keyword sets | `prompting-guide.md` §7 | **NEW** (skill carries 4 of 14) |
| `detailed_description` normally **350–500 English words**; API cap 7,000 chars; ComfyUI does not truncate | `prompting-guide.md` §2 "Length" | **NEW** — replaces "expect to write longer prompts" with a number |
| Emotion → observable behaviour, with the arc shape and the face/voice coupling | `prompting-guide.md`, new §on acting | **NEW** — skill's only line is "give the delivery" |
| No negative-prompt field; exclusions as plain sentences, mainly for camera and on-screen text | `prompting-guide.md` §5 | **NEW** |
| Reference input order is semantic (positional clock) | `characters.md` / `prompting-guide.md` §6 | **NEW** |
| Wardrobe drifts across generations; name garments even for referenced subjects | `characters.md` | **NEW**, REINFORCES the over-describe rule |
| Most important beat in the middle; ~4 s for a prop hand-off | `prompting-guide.md` §8 "Budget time" | REINFORCES (skill says ≥3 s; a mild widening, not a conflict) |
| Context-IR is reachable as the ComfyUI `MiniMax H3 Context IR` partner node | `prompting-guide.md` §6 | **CONTRADICTS** in emphasis: skill says the module *"is **not in the open release**"* and offers only an LLM pre-pass. True of the weights; the hosted node closes the gap for anyone willing to spend credits |
| `MiniMaxH3AddGuide` — guides at any frame, audio included, chainable (ComfyUI v0.34.0) | `setup-and-workflows.md` (modes / multishot) | **NEW** — supersedes "first+last frame only" framing |
| `--output_fps` / `--stretch_keep_bands`; 30 s at 12 fps with named artefacts; SDPA fix required | `setup-and-workflows.md`, `lora-training.md` | **CONTRADICTS**: skill states output is *"4–15 seconds"* as a flat fact in SKILL.md §1 |
| Teacher-matching training (`--h3_teacher_matching`, three teacher kinds, sigma gates) | `lora-training.md` §trainers | **NEW** — musubi table currently stops at guidance loss and one-frame |
| One-frame Ref2VA, control-images-as-references, multi `cond_` FL2VA slots, `convert_lora` H3 support | `lora-training.md` | **NEW** |
| Four more prompt tools (hyukudan 15★, 1038lab 218★, colorAi, ethanfel) | `prompting-guide.md` §9 tool table | **NEW** — table currently lists only BMB12d3 and duckyshell |
| `<Subject N> (SN) [emotion] says:` advertised as official | `prompting-guide.md` §9, as a caution | **CONTRADICTS** the official guide — document it as the trap it is |
| `SparseRef15_Hybrid`, `H3-Continuum`, 6 GB 4-step pipelines | `setup-and-workflows.md` | **NEW** |

---

## Confidence notes

**Well attested.** Everything drawn from `VIDEO_PROMPT_WRITING_GUIDE_base_en.md` and `_ref_en.md` is first-party and verified two ways: I diffed the GitHub `skills/h3-prompt-writing/references/*.txt` copies against the Hugging Face `docs/*.md` originals and they are byte-identical modulo whitespace. The camera vocabulary, `(SN)` IDs, the delivery-outside-`<d>` rule, `<scenetrans>`/`<cutoff>`, the keyword taxonomies and the 350–500-word figure are all direct quotes. The Hailuo bracket-command list is official API documentation relayed through an aggregator — the list itself is consistent across every source, so treat it as settled; the *page* is not primary.

**Well reasoned, single-source.** The "no emotion-tag syntax at all" claim and the face/voice coupling come from one repo (hyukudan, 15★). It is unusually strong for a single source: it cites the official skill by path, publishes a real input→output trace, and self-flags its own inventions (⏸️ "is our own convention… Worth A/B testing"). Convergence between hyukudan, Naxdy (41★, revised 2026-09-06) and RunDiffusion on the observable-behaviour rule raises confidence — though all three read the same official guide, so they may share an ancestor rather than corroborate independently.

**Thin.** Naxdy's "most important beat in the middle" and the ~4 s hand-off budget are one author's heuristics with no published test. The `[emotion]` slot in 1038lab's README is a single vendor claim labelled "Official" with no citation, contradicted by the primary guide — flag it, do not adopt it. fal's `@Image 1:` convention and its stated 2026-07-30 date are both suspect (the date precedes the 2026-08-02 open release).

**Not found.** No official MiniMax blog or X post on H3 prompting since the 2026-08-13 model-card update. old.reddit.com is unreachable from this environment (both WebFetch and curl are blocked), so the Reddit sweep is second-hand via search snippets only — a follow-up pass from a machine with Reddit access would be worth doing before treating the community half as complete. **"W011" is not a MiniMax artefact**: it is skills.sh's Snyk agent-scan warning code for indirect prompt injection, already addressed in this repo by commit `f6b4392` (2026-08-29).

**Durations to re-verify.** The 30 s figure is a trainer author's experimental probe behind `--allow_experimental_duration`, not a released capability, and it applies to musubi's generation path — not to ComfyUI. The skill's "4–15 seconds" remains correct for the supported path; it should gain a footnote, not a rewrite.
