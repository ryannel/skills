# MiniMax H3 / Krea 2 — Reddit sweep (2026-09-09)

Second-pass supplement to `minimax-prompting-research.md`, using the user's Chrome via the claude-in-chrome MCP (in-app Browser pane and WebFetch both refuse reddit.com). Only adds what the prior report lacks or gets wrong.

## Access

old.reddit.com search and thread pages loaded fully via `navigate` + `get_page_text` in the user's real Chrome — no login, no forms, read-only. Ran all 8 required searches plus two follow-on queries (`h3+lora`, r/aivideo), then opened 12 threads: the 154-comment tag/emotion thread, a subtle-acting thread, a realism-loss thread, a workflow-artifacts thread, a FastH3 LoRA-converter thread, a prompt-enhancer thread, an RTX-3090 112-test sweep, a 25-day-old tags PSA (450 pts, 88 comments — found via a related-posts link, not the original search list), and four LoRA-dataset threads (SD1.5 face distortion, character-consistency-break-first, Krea 2 "Normal People" ethnicity LoRA, and the 3090 settings sweep). Tab closed at the end. No blocks encountered on the second attempt.

## MiniMax H3 findings

**A real (but partial) preset tag vocabulary exists, contra the prior report's "no emotion-tag syntax at all."** Two independent threads 25 days apart converge on the same parenthetical non-verbal-sound tags, placed inside `<d>`: `(laughs)`, `(chuckle)`, `(snorts)`, `(humming)`, `(breath)`, `(pant)`, `(inhale)`, `(exhale)`, `(gasps)`, `(coughs)`, `(clear-throat)`, `(sighs)`, `(lip-smacking)`, `(sniffs)`, `(groans)`, `(yawns)`, `(sneezes)`, `(burps)`, `(whistles)`, `(hissing)`, `(emm)`, `(crying)`, `(applause)`. These are **preset only** — a custom emotion word like `(nervous)` is not supported and gets read as literal text. — r/StableDiffusion, "Pushing AI emotions..." (Mister_Eduards comment, 32 pts) `/1wap0rb/`, 2026-09-08; corroborated in "PSA: Try experimenting with `<tags>`..." `/1vosqqw/`, 450 pts/88 comments, 2026-08-15, where `<laughs>`, `<sighs>`, `<gestures at his head>`, `<shuddering breath>` all worked and only a sneeze tag was silently ignored.

**Angle-bracket `<tag>` directives are the unreliable half, and the failure modes are specific.** Same PSA thread: `<emphasis>` was rendered as a bleeped curse word in one seed; other custom tags sometimes bleed into the spoken audio as garbled fragments ("br", "le-incredible"). `<i>word</i>` emphasis is inconsistent for the same reason. The most reliable emphasis technique found in a controlled A/B test (6/6 vs ~1/10) is to **describe the emphasis in the narration after the dialogue, not tag it inline**: `he says: <d>we are going to do incredible things</d>. He emphasises the word 'incredible'.` — V4nKw15h, `/1wap0rb/`. Markdown-style `*word*`/`**word**` asterisks also work for emphasis, independently reported in both threads.

**Delivery/tone routinely goes *inside* `<d>`'s language tag in practice**, contradicting the prior report's "voice attribution belongs outside `<d>`": `<d>[English, whispered in a pleading tone] Give me the key, please</d>` and `<d>[English, British accent] ...</d>` are both reported working, as is the canonical `(S1) says: <d>[English] ... <laughs></d>` form. — `/1wap0rb/`, `/1vosqqw/`.

**`<d>` has an open, acknowledged bug.** One commenter: "There's a bug with `<d>` tags where it adds gibberish to the generation. It's not recommended at the moment." A partial workaround — plain quotation marks instead of `<d></d>` — reduces (not eliminates) a known first-second audio-bleed/"starting chirp" artifact. Root cause per another commenter: the artifact appears when the spoken line can't fit the requested clip duration; test at 0.2 MP first to verify audio length before raising resolution. — `/1vosqqw/`.

**Whisper is genuinely contested.** One report says whisper needs a dedicated whisper reference audio and fails without one (producing only "mildly quieter lines"). A separate report says H3 *does* whisper, but under unknown, undocumented conditions unrelated to the literal instruction — "you follow the guide... and then suddenly something totally undocumented works out." Treat any "reliable whisper" claim skeptically. — `/1wap0rb/`, `/1wald45/`.

**Reference-audio quality shapes expressiveness, and pacing has a number.** A more nuanced real-human reference clip adds more "attitude" cross-modally (a southern-accent reference produced more hand-talking, unprompted). Never use an AI-generated voice as a clone reference — AI-on-AI compounds every artifact. Keep spoken pacing to roughly **1.5–2 words/second** so the model has room to breathe. — mwoody450, `/1wap0rb/`.

**Subtle/naturalistic acting has a stated mechanism, not just a rule.** Naming an emotion ("serious," "introverted") makes the model regress to the dominant mode of its caption distribution — which skews toward stock/ad/trailer footage, hence the default overacting and the "every male character becomes a confident flirt" complaint. Describing *only* observable mechanics — gaze direction, blink tempo, jaw/hand state, with **zero** emotion words — was the one technique that held up scene-to-scene in the OP's follow-up test. — TaniaDictee, `/1wald45/`. Separately corroborated: turbo/speedup LoRAs measurably strip micro-expression detail, so disable them for performance-critical scenes. — `/1wald45/`, `/1wamoij/`, `/1wb5g0b/`.

**Camera/framing failure mode, with a fix.** H3 is "notoriously bad with faces at distance," and backgrounds visibly swim when the camera moves on a wide shot; tighten framing or explicitly lock the camera in the prompt. Also: don't stack multiple attention-acceleration nodes (Sage/SLA/SOL) at once — pick one. Base settings that cleared up a reported artifact/weird-face case: 26–32 steps (no turbo), `shift_video 12`, euler sampler, normal scheduler. — `/1wb5g0b/`.

**A working speed-LoRA conversion exists for the open weights (FastH3).** FastVideo's 4-step distilled H3 LoRA doesn't load in ComfyUI's repacked checkpoints (layer names don't match); a community converter fixes this but needs **6 steps, not 4** (4 = jitter/flicker/unusable; 6 = the sweet spot; 7–8 = no real gain, though the author later revised to prefer 8). Must run at strength ≥1.0 (below that, structure and color fall apart). Reported to beat stock 20-step on background detail, lighting, and gait stability in side-by-side tests, and pairs well with H3 SLA Attention for further speedup — but "plastic skin" complaints persist from other commenters on the same clips. — `/1w2ssyd/`, corroborated independently in the RTX-3090 sweep (`/1w9rvz6/`, added as "C10").

**A VLM prompt-enhancer front-end for I2V/ref2va exists**: load a reference image + a plain-language instruction, a vision-language model (Qwen3-VL-8B in this build) expands it into H3's structured format before generation, improving adherence on camera moves, actions, and dialogue. Not independently verified beyond the OP's own before/after clips. — `/1w3tofp/`.

**0.98 MP (≈1280×768) is treated as H3's native resolution** by the community, distinct from a round 1.0 MP; multiple commenters use it as their production default. — `/1w9rvz6/`.

## LoRA dataset findings

**Small Krea 2 datasets work if curation is tight.** A usable character LoRA from just **10–15 images at 600–1200 steps**, provided every "off-looking" image is culled and captions describe only what should *vary* (pose, hair, clothes, environment) — not the fixed identity traits. — darkestbrew, `/1wacvcm/`.

**Caption what you don't want the LoRA to own; leave out what you do.** Caption background, lighting, camera angle, and pose exhaustively — these are what should stay promptable, not baked in. Leave a fixed outfit or hairstyle out of the captions entirely so the LoRA owns it. Don't mix training-image styles (realism + anime + painterly) in one LoRA — it bakes a confused blended style. — SDuser12345, `/1wacvcm/`.

**Shot-distance diversity prevents distance drift.** A worked example (Christopher Reeve/Superman LoRA): **29 close-up + 29 medium + 29 far/full-body shots**, plus some crowd shots so the trigger word isolates identity from everyone else in frame. Without far shots, the model has nothing to reconstruct the face from at distance, which is where drift shows up. — mabseyuk, `/1wacvcm/`.

**Mechanism behind face-distortion from bad data**: small/distant/profile/group-shot faces at low native resolution "teach a smeared average," manifesting as warped facial structure; BLIP-style auto-captioning barely describes faces, giving the model no textual signal to disentangle face quality. Fix: filter for a minimum face size, drop or crop group/profile shots, dedupe, recaption with a better (ideally VLM) captioner. SD1.5-specific case, but the mechanism is architecture-agnostic. — `/1wakjxx/`.

**Multi-class LoRAs (e.g., several distinct ethnic-appearance groups in one LoRA) average toward whatever's numerically dominant** unless sampling is deliberately balanced per class, and low rank compresses toward the mean across a wide feature space — so a wide-feature LoRA needs higher rank. Practical compromise floated: 2–4 LoRAs by broad cluster, ~75–100 images each, rather than one omnibus LoRA or a dozen narrow ones. — `/1w9ysn0/`.

## Contradicts or corrects the prior report

- **"H3 has no emotion-tag syntax at all" is too strong.** A real, community-converged preset vocabulary of parenthetical non-verbal tags exists and works inside `<d>` (see above); only free-text custom emotion tags are the unsupported half.
- **"Delivery/voice attribution belongs entirely outside `<d>`" is contradicted by common practice** — tone and accent are routinely written *inside* the language tag inside `<d>` (`<d>[English, whispered in a pleading tone] ...</d>`), and the community's own canonical dialogue form nests a non-verbal tag inside `<d>` too.
- **`<d>` is flagged as presently buggy** by at least one commenter ("adds gibberish... not recommended at the moment"), with a first-second audio-bleed artifact tied to a concrete cause (spoken line doesn't fit the clip duration) and a partial workaround (plain quotes) — this operational nuance was missing from the prior report.
- **Whisper reliability is unresolved, not merely difficult** — one thread says it needs a dedicated reference; another says it happens under unknown conditions unrelated to the instruction given.

## Thin / single-report

- Kohya/sd-scripts `enable_wildcard` caption rotation (short/natural-language/structured captions per epoch) — the feature is real and confirmed in current source, but its benefit for LoRA prompt-tolerance is one poster's untested hypothesis, with a text-encoder-caching caveat noted but not tested.
- Dense-VLM-caption-without-concept-exclusion still teaching a Krea 2 LoRA the character's face — one report, self-flagged as possibly confounded by a sub-10-image dataset forced by VRAM limits.
- ArcFace-embedding dataset curation to auto-drop outlier training images — explicitly "haven't trained it yet," an idea, not a result.
- Individual tag success/failure anecdotes ("blows a raspberry" worked, a sneeze tag was ignored) come from one 88-comment thread and aren't independently replicated per-tag.
- FastH3 converter's "6 steps is the sweet spot" is one author's benchmark (later softened toward 8 steps in the same thread); directionally corroborated elsewhere but the exact number isn't independently pinned down.
