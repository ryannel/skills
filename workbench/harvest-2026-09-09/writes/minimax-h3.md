# minimax-h3 — writer report, 2026-09-09

## Edits (file · section · change · evidence)

- `prompting-guide.md` §2 · official shot order; `detailed_description` **350–500 words**; 7,000-char API cap, ComfyUI no ceiling · base guide §4.1/§5, ref guide §5.2, runware, hyukudan.
- `prompting-guide.md` §4 → "Dialogue and performance" · `(S1)`/`(S1,S2)` IDs; **delivery outside `<d>`, only language + words inside** (corrects the old form); `<scenetrans>`, `<cutoff>`, voiceover phrase + lips-closed, `[unclear]`, quoted on-screen text · base guide §4.4–4.5, ref guide §5.4. Inside-tag delivery reported working → `[contested]`; `<d>` chirp bug, 1.5–2 words/s · Reddit sweep. Preset sound-tag list (the only tags that exist), `(nervous)` read as text, emphasis-in-narration 6/6 · Mister_Eduards, V4nKw15h. New "Emotional direction — there is no emotion tag": TTS-syntax trap, Promptor `[emotion]` slot `[contested]`, enhancer marks are stripped shorthand; observable-behaviour method + caption-distribution mechanism, face/voice pairs, arc shape, voiceover/framing exceptions, speed LoRAs strip micro-expression, whisper `[contested]` · Naxdy, RunDiffusion, hyukudan, TaniaDictee; "keep it light" and the music-source trap `[live-use — Ciara hoop piece]`.
- `prompting-guide.md` §5 · 12-term camera vocabulary + amplitude/speed as prose · base guide §4.3; bracket commands = hosted Hailuo; exclusions as sentences; faces at distance; wardrobe drift · Naxdy, Reddit; full grammar held the room `[live-use]`.
- `prompting-guide.md` §6 · ComfyUI `MiniMax H3 Context IR` partner node; reference order semantic · docs.comfy.org, Naxdy.
- `prompting-guide.md` §7–9 · FL2VA example in official syntax; full `summary`/`retention_analysis` keyword sets · ref guide §3, §4; 3–4 s per action, middle-beat rule (single); timestamp typo fixed; **"a second shot marker or timestamp is a cut" — `[Shot 1]` structure replaced end-pins, n=1** `[live-use]`; cut-triggering beats `[live-use]`; four tools added with the Promptor caution.
- `SKILL.md` · description +8 words; duration "supported path" + stretch pointer; Context-IR row, fal H3 Max `[re-verify]`; dialogue bullet; diffusers → `ModularPipeline` (PR #14355); frame default 124; directs-itself #1 `[live-use]`, #2 camera grammar; "It also acts" paragraph; Turbo switch default-off, SLA competitors, pick-one rule; #15644 still clamps; six failure rows; pre-flight #5; two-bar bullets, `[live-use]` source-class paragraph, `Facts dated 2026-09-09`; reference-file and suite rows.
- `setup-and-workflows.md` · §1 Turbo switch; §3 defaults 124 + "Past 15 seconds" stretch subsection (musubi docs 08-27/09-05, SDPA caveat); §5 SparseRef15 (single); §7 `MiniMaxH3AddGuide` (PR #15439), PR #15375, chaining doctrine, H3-Continuum; §8 #15644 open; §9 VRAM watch row (#16150), sol-attn/H3-Optimizations, Spectrum pin stale + Sol-H3 not recommended, FastH3 6-step/≥1.0, V8 (single), artefact-reset settings (single).
- `lora-training.md` · one-lab framing; Civitai 86/29; FastH3 + micro-expression; musubi surface (teacher matching, `subject_ref` with `--one_frame`, one-frame Ref2VA, `convert_lora`); "Memory traps" (`convrot8`, 60 GB cgroup, samples off) `[live-use — Amy]`; "What one lab measured" (1536 plateau, r32 collapse, 15 beat 73 with caveat, focus_prob A/B, cost) and **stills LoRA carries identity into motion, 0.200 vs 0.920** `[live-use — Ciara h3-v1]`; "Still open" rewritten.
- `characters.md` · intro, reference-order and wardrobe rules, micro-jump kept for identity not cuts `[live-use]`, LoRA paragraph, table and failure rows.

## Findings
**Resolved:** `t2v-i2v-frame-default-now-124`, `spectrum-version-25-releases-stale`, `comfyui-nightly-vram-regression-open`, `frame-min-fix-not-landed`, `diffusers-entrypoint-resolved`, `sparse-attention-competitors`, `fal-h3-max-shipped` (hedged; evidence was "(verify)").
**Reversed, not applied:** `official-template-now-turbo` — the 09-09 diff shows the switch default False; the skill's text was right. Close it per `turbo-default-flipped-back-to-off`.

## Techniques
Added: `sparseref15-hybrid-checkpoint`, `h3-continuum-chunked-long-form-node-pack`, `ultra-fastest-4-step-v8-workflow`, each by source class. Omitted: Promptor `[emotion]` syntax (caution only), hyukudan ⏸️ pause (self-flagged), per-tag Reddit anecdotes.

## Watchlist
Resolve: `h3-image-vae-frame-limit` claim text; `h3-template-settings` check text (bundled but off). Amend: `h3-context-ir-closed` (node reachable), `h3-lora-hyperparam-consensus` (first-hand ladder), `h3-spectrum-audio`, `h3-musubi-pr-1030`. Add: `h3-turbo-default-flip-flop`, `h3-frame-default-124-everywhere`, `h3-d-tag-delivery-placement` (contested), `h3-emotion-tag-syntax` (guide vs Promptor), `h3-temporal-stretch-30s` (musubi-only), `h3-comfyui-16150-vram`.

## Other skills / shape
- `generative-media-atlas`: LoRA row may cite the stills-LoRA-in-motion result `[live-use]` and 86/29.
- `character-lora-training`: 15-beat-73 stated here with the three-variables caveat; keep aligned.
- `prompting-guide.md` is 7,553 words (TOC present); description 345 words (already over 320 before this pass); SKILL.md 413 lines; all files under the readability threshold (median 8.0).
