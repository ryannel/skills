# Audit — `skills/generative-media/minimax-h3/`

Graded against `workbench/uniformity/STANDARD.md` §8 (all 41 checks) plus the four out-of-rubric
items in the brief. SKILL.md = 419 lines / 6,460 words (per STANDARD's own count); references total
8,846 words; corpus 15,306 words, 42% SKILL.md share.

---

## Blocking

**[P1] SKILL.md/references — LTX-2.5 licence claim is now FALSE, five locations.**
Primary-source research (`workbench/ltx-2-5/research-primary.md`) has settled what this skill still
calls unread and gated. Facts: LTX-2.5 ships under the **LTX-2.x Community License Agreement**
(2026-08-11), **public and ungated** at `github.com/Lightricks/LTX-2/blob/main/LICENSE.md` — only the
HF *weights* are gated. Commercial use is free **worldwide under $10M annual revenue**; derivatives,
**explicitly including LoRAs**, inherit the licence and its $10M obligation; the incorporated AUP
**prohibits sexually explicit content**, unlike Wan. LTX-2.3 runs an older, different licence text and
was never gated.
- `SKILL.md:37` — "**LTX-2.5** also does native audio, though its licence is gated behind a
  contact-information agreement and is not verified here." →
  "LTX-2.5 also does native audio, under a differently-shaped licence: the LTX-2.x Community License
  (public text; only the HF weights are gated) is free for commercial use worldwide under **$10M**
  annual revenue, paid above it, and its AUP **prohibits NSFW output** — see
  [`ltx-2-5`](../ltx-2-5/)." `[official — LTX-2/LICENSE.md]`
- `SKILL.md:378` (suite table, "Video with synchronised dialogue/SFX/music" row) — "LTX-2.5 also does
  native audio (gated licence, unverified here)" → "[`ltx-2-5`](../ltx-2-5/) also does native audio,
  under a $10M-revenue-gated commercial licence with an NSFW prohibition — a different shape of risk
  than H3's territory exclusion."
- `SKILL.md:405` (two-bar "Contested / unresolved" list) — the whole bullet ("LTX-2.5's licence... is
  **gated**... and was **not read**... `[flagged — re-verify]`") is **resolved, not unresolved**.
  Delete the bullet from the flagged list entirely; the corrected fact belongs in the licence prose
  (line 37 fix above), not the unresolved-points list.
- `references/licence-and-territory.md:79` (alternatives table row) — "**LTX-2.5** | Community
  licence, **gated** behind a contact-information agreement. Terms **not read**... `[flagged —
  re-verify]`" → "**[`ltx-2-5`](../../ltx-2-5/)** | LTX-2.x Community License (2026-08-11), public
  text, free worldwide under $10M revenue (paid above); LoRA derivatives inherit the obligation; AUP
  bars sexually explicit content `[official — LTX-2/LICENSE.md]`".
- `SKILL.md:386` — "**ReDetail** re-renders H3 clips through the LTX-2.5 upscaler" — factually fine,
  optionally link as `[`ltx-2-5`](../ltx-2-5/)` for consistency once that skill is published.
- `freshness.json` watchlist id `ltx-2-5-licence-unread` (minimax-h3 block) — claim and check fields
  assume the licence is unread and gated; rewrite to record it as read, or retire the id and add a
  fresh version-pin entry for LTX-2.x licence terms if `ltx-2-5` doesn't yet own its own watchlist.

**[P1] SKILL.md:229, ~332 — a `[flagged — re-verify]` claim has been RESOLVED and is now presented
backwards.** "Watch for the core fix. A Kijai PR against ComfyUI (`Comfy-Org/ComfyUI#15243`) addresses
the audio path; once merged the custom node may become unnecessary." I verified via the GitHub API:
PR #15243 ("Fix sampler issues for audio with minimax, support more samplers", kijai) **merged
2026-08-06** and shipped in **ComfyUI v0.31.0 (released 2026-08-08)** — twelve days before this
skill's own "Facts dated 2026-08-13" line, and before today's 2026-08-22 refresh. It adds
`ModelSamplingAV`/`ModelSamplingMiniMaxH3` with a separate `audio_shift`, letting stochastic samplers
and low step counts carry audio correctly without a third-party node. The skill still ranks
larryvrh's custom sampler as the *first* recommendation and treats the core fix as pending.
- Fix `SKILL.md:226-230`: reorder to lead with "Update ComfyUI to ≥v0.31.0 and use the core
  `ModelSamplingMiniMaxH3` node's `audio_shift` setting (PR #15243, merged 2026-08-06) — this now
  fixes the split-scheduling problem without a custom node." Demote larryvrh's node to "fallback for
  installs that haven't updated." Retire the `[flagged — re-verify]` tag on this claim (replace with
  `[community — re-verify current node wiring]` if the exact stock-graph rewiring is unconfirmed).
- Fix the matching failure-table row (~`SKILL.md:332`, "Picture fine, audio garbled or broken — with
  the Turbo LoRA on"): fix column currently ends "...watch ComfyUI PR #15243" → "Update ComfyUI
  ≥v0.31.0 and use the core `ModelSamplingMiniMaxH3` audio_shift setting (PR #15243, merged); or
  larryvrh's sampler node on older installs; or raise to ~10 steps."
- `freshness.json` watchlist id `h3-audio-scheduling-fix` — its own check field already asks "Has
  Comfy-Org/ComfyUI#15243 merged?"; answer is yes — mark resolved and update `last_drift_found`.

**[P1, check 1] Two MANDATORY §2 sections are entirely absent from SKILL.md**, not just misplaced:
- **`## Signature-quality technique` (slot 7)** — grepped `SKILL.md` and every `references/*.md` for
  "signature", "default look", "default motion", "aesthetic": zero hits. The model's default render
  character and — per the video-conditional requirement — its **default motion character** are never
  named anywhere in the skill. The one hint that exists is buried and undeveloped:
  `references/prompting-guide.md:82`, "`static shot` if the default drift is unwanted" — implying an
  un-stated default camera drift. Fix: add a new `##` section between `## Setup & ecosystem` and
  `## Going faster` (e.g. `## The default look, and the camera drift nobody names`), built from that
  drift observation plus whatever the model's default rendering bias actually is (needs a short
  research pass; this audit only locates the gap).
- **`## Production pipelines & mixing models` (slot 9, heading verbatim)** — does not exist. The
  content it should summarize is fully written, but only in
  `references/setup-and-workflows.md §6` ("Production pipeline and the 768p ceiling": the five-stage
  ladder, the restore-before-interpolate rule, the ReDetail constraints). SKILL.md's only trace of it
  is the `## Reference files` pointer row. Fix: add the section with the numbered ladder, the
  bypassable stages, the decode-to-pixels handoff, a link to
  [`image-production-workflows`](../image-production-workflows/), and — because this is video — the
  restore-before-interpolate rule stated explicitly (see also the check-20 finding below, which is the
  sharpest reason this section is missing).

**[P1, check 20] A silent-failure trap lives only in a reference, not in SKILL.md.**
`references/setup-and-workflows.md:194`: "**Mux** the final audio back if any step in your chain
drops it — **the most common way to lose H3's whole point in post**." Most ComfyUI post/upscale nodes
are picture-only and silently discard the audio track — exactly the §5.4 test ("a plausible-looking
wrong result rather than an error"). It is not in SKILL.md's failure-modes table at all. Fix: add a
row — `Symptom: video looks fine after upscale/interpolate but audio is gone | Cause: most ComfyUI
post nodes are picture-only and drop the audio track silently | Fix: verify each post stage preserves
audio, or keep the raw output and re-mux at the end` — and fold the one-sentence version into the new
production-pipelines section above.

**[P1, check 33] Bare (unlinked) sibling mention in a MANDATORY table.**
`SKILL.md:418` — `## Reference files` row for `characters.md`: "...what H3 cannot yet do that
`wan-2-2` can" — bare code span, not `[`wan-2-2`](../wan-2-2/)`. Fix: linkify.

---

## Standard

**[P2, check 2] Section order:** `## What "open weights" means here` (SKILL.md:45, optional slot-8
material) sits **before** `## Task-mode selector` (SKILL.md:64, MANDATORY slot 3). Fix: move
`## Task-mode selector` to directly follow `## Before anything else — the licence and the territory`
(before line 45); `## What "open weights" means here` can follow it or fold into `## Setup &
ecosystem` as a subsection, since its content (what's open vs. hosted-only) is closer to setup
context than to a selector decision.

**[P2, check 4] Selector table has no "Use when…" column.** `SKILL.md:68-71` — columns are
Checkpoint / Tasks / Inputs / ComfyUI node. Fix: add a "Use when…" column (e.g. "text or
first/last-frame only" for FL2VA, "carrying a reference voice, video clip, or fixing Ref2VA's quality
gap via hybrid" for Ref2VA), or relabel "Tasks" if it is meant to serve that role — currently it
doesn't read as one.

**[P2, check 6] No explicit per-mode settings blocks.** STANDARD.md §7 clause 13 already anticipates
this exact finding ("`minimax-h3` should still gain an explicit settings block... but must not be
re-cut by variant"). There is one shared sampler-chain block (`SKILL.md:139-145`) but no `###` block
distinguishing FL2VA vs. Ref2VA settings (steps/CFG/sampler/scheduler/negatives/seed). Fix: add a
`### FL2VA` / `### Ref2VA` pair (or a single `### Both checkpoints` block plus a callout for anything
that actually differs) under `## Setup & ecosystem`, keeping the task-mode framing per §7.

**[P2, check 9 / §4.3] Rename `references/loras-and-training.md` → `lora-training.md`.**
`git mv skills/generative-media/minimax-h3/references/loras-and-training.md
skills/generative-media/minimax-h3/references/lora-training.md`, then update the one internal
reference: `SKILL.md:419` (`## Reference files` row).

**[P2, checks 18/19 + brief item 1 — depth and placement.** Four concrete demotion candidates,
word-counted:

1. **`## Frame count and resolution`** (`SKILL.md:238-260`, ~302 words) fully duplicates the formula
   and complete megapixel table in `references/setup-and-workflows.md §3-4` (already the blessed fix
   named in STANDARD §7 clause 2). Trim SKILL.md to the rule + anchor number (`frames ≡ 5 (mod 17)`;
   default 1344×768 / 0.98 MP) and a `§3-4` pointer; the reference keeps the full formula and table.
2. **`### Long-form: context chaining`** and **`### H3 as a single-image edit model`**
   (`SKILL.md:267-289`, ~379 words) are near-line-for-line duplicates of
   `references/setup-and-workflows.md §7-8` (compare `SKILL.md:269` against `setup-and-workflows.md:206`,
   `SKILL.md:284-285` against `setup-and-workflows.md:223-224`). Trim SKILL.md to the two
   silent-failure traps only ("use `Mamad8/MiniMax-H3-Image-VAE`, generate exactly 1 frame — the
   normal VAE gives a blurry, plausible-looking wrong result") plus a pointer to `§7-8`; drop the
   repeated craft bullets (scene-planning tips, reported quality claims).
3. **`### Video editing — replacing a character in existing footage`** (`SKILL.md:291-323`,
   ~345 words, including the full YAML-shaped worked template) has **no reference-file home at all** —
   it is the opposite problem from #1/#2. `references/prompting-guide.md §7` is already "Worked
   examples" and `§8` already names the `retention_analysis`/`subject_definitions` field vocabulary
   (`prompting-guide.md:176`) without the full template. Move the worked template and its bullets
   there; keep in SKILL.md only the anchor claim ("`retention_analysis` is load-bearing,
   `detailed_description` barely matters — 400+ generations to find that") and a pointer.
4. **`## Going faster — the acceleration stack`** (`SKILL.md:167-236`, ~1,211 words — the single
   largest section in the file) has **zero presence in any reference file.** Layers 0-2 (runtime
   traps, SLA, Spectrum) are inference/node-wiring content that belongs in
   `references/setup-and-workflows.md` per its §4.1 remit; Layer 3 (using the Turbo LoRA) is *loading
   and stacking* a LoRA, which the train/use boundary (§4.1, check 11) also assigns to
   `setup-and-workflows.md`, not `lora-training.md`. Move the full benchmark tables, repo names, and
   the two-stage Spectrum audio-feedback derivation into a new `setup-and-workflows.md` section. Keep
   in SKILL.md, compressed: the CU130/comfy-kitchen-version trap (silent, costs most of the speed),
   the SLA-node-must-be-last placement rule, the Spectrum `audio_blend_weight=0` +
   `offline_smoothing_replay` fix (silent audio corruption otherwise), the Turbo LoRA
   scheduler/step-count mismatch (see the Blocking PR-15243 fix above, which changes this section's
   content anyway), and the default recommendation — with a pointer to the new reference section for
   the full stack and benchmarks.

Net effect if all four land: roughly 1,400-1,500 words move out of SKILL.md (from ~6,460 toward
~5,000-5,100), landing inside the un-justification-needed band while every §5.4 silent-failure trap
stays put. This is placement, not a mandate to cut below the STANDARD's already-blessed 6,460 — §7
clause 2 remains correct on total size; these are pure duplication/placement fixes.

**[P2, check 29] Orphan craft numbers, no marker, no named source in sentence:**
- `SKILL.md:256` — "Errors are reported to rise at *both* ends: around **0.8 MP** is the reported
  sweet spot..." carries no marker itself (only the two derived bullets beneath it are marked, to
  GrayingGamer and nsfwVariant). Add a marker or fold the sourcing up into this sentence.

**[P2, check 30 — summarise-up hop] `SKILL.md:224`** — "...it is reported to work on **Ref2VA**
too — the first evidence that weights transfer between the two task checkpoints" restates
`references/loras-and-training.md:20`'s attributed claim
(`` `[community — Organix33; re-verify]` ``) without carrying the attribution. Add the marker to the
SKILL.md sentence.

**[P2, checks 40/41] Freshness watchlist gaps beyond the two Blocking items above.** Four
reference-level `[flagged — re-verify]` claims have no watchlist entry at all: `RedCraft | REDMIX`
checkpoint provenance (`references/loras-and-training.md:22`), untested `CFGGuider` swap
(`references/setup-and-workflows.md:38`), no official VRAM figure published
(`references/setup-and-workflows.md:70`), undocumented `match` parameter semantics
(`references/setup-and-workflows.md:150`). Add watchlist entries or fold them into an existing
entry's `check` field.

**[P2, check 33, references] Bare `wan-2-2` mentions in `references/characters.md`.** Table header
cell and body sentence at lines 91 and 99 (`| Capability | H3 | `wan-2-2` |` and "`wan-2-2` currently
has the better rig") are unlinked; the section heading at line 87 is conventionally fine as a bare
code span. Linkify lines 91 and 99.

---

## Cosmetic

**[P3, check 31] Marker backtick inconsistency.** All 17 `` `[community — …]` `` markers and both
`` `[flagged]`` /``[contested]` `` markers in SKILL.md are correctly backticked. The four
`[official — …]` markers are **not**: `SKILL.md:21` (`[official — repo `LICENSE`]`), `:39`
(`[official — licence "Additional Note"]`), `:47`, `:60` (`[official — model card]`). Wrap all four in
backticks.

**[P3, check 12] Missing `## Contents` TOC.** Both `references/prompting-guide.md` (2,191 words) and
`references/setup-and-workflows.md` (2,592 words) exceed the 2,000-word threshold and carry a bare
numbered link list under the title instead of a `## Contents` heading (already named in
STANDARD §6.7's known-missing list). Add the heading above the existing list in both files —
mechanical, no content change.

---

## Not findings (checked, PASS or JUSTIFIED)

- Checks 3, 5, 7, 8, 10, 11, 14, 16, 17, 21, 22, 23, 24, 25, 26 (syntax), 27, 28, 32, 34, 37, 38, 39:
  PASS. Notably: no italic-parenthetical or malformed/nested markers anywhere in the skill; no link
  reaches above `skills/generative-media/`; date line is the suite's canonical exemplar; failure table
  has 20 rows with mechanism-stated causes (one thin cell — "common with hybrid checkpoints fed a
  sheet on white" — not worth a separate finding); registered correctly in `marketplace.json`, README,
  and `freshness.json`.
- Check 15 (SKILL.md 25-40%/2,800-5,500w): **JUSTIFIED** per STANDARD §7 clause 2 — three of four
  §5.2 justifications apply (ruling-out licence, acceleration stack, extra capabilities). The
  placement findings above are independent of this and stand regardless.
- Check 36 (reciprocal suite-table links): `wan-2-2/SKILL.md` links back to `minimax-h3` correctly
  (lines 166, 243, 244, 258 — read-only check, out of this audit's write scope). Reciprocity from
  `z-image`, `flux-2`, `sdxl`, `krea-2` is each of those skills' own auditor's concern.
- Check 35 (suite-table axis coverage): 6 of 7 axes clearly present; "post chain, upscale and
  interpolation" is only implied via the "2K output locally" row. Resolves naturally once the
  Blocking `## Production pipelines & mixing models` section is added — not a separate finding.
- Item "Do not touch": the licence-first opening (`## Before anything else — the licence and the
  territory`) is untouched by every recommendation above, per STANDARD §7 clause 1.
