# Audit: `skills/generative-media/z-image/`

Audited against `workbench/uniformity/STANDARD.md` §8 rubric. Files read in full: `SKILL.md` (234
lines / 3,305 words), `references/characters.md` (1,588 w), `references/lora-training.md` (2,298 w),
`references/prompting-guide.md` (3,382 w), `references/workflows.md` (3,462 w). Corpus total: 14,035
words (recount; STANDARD's table has 13,819 — both land inside the 10,000–16,000 band, difference is
counting-tool noise, not a finding).

---

## Full rubric checklist (checks 1–41)

| # | Verdict | Note |
|---|---|---|
| 1 | **FINDING (P1)** | `## Production pipelines & mixing models` missing verbatim — see Blocking. |
| 2 | **FINDING (P2)** | Setup & ecosystem before The one rule — see Blocking (grouped P1-adjacent per STANDARD's own framing, kept P2 per rubric's stated severity). |
| 3 | **FINDING (P1)** | Three heading mismatches — see Blocking. |
| 4 | PASS | Selector table has "Use when…" column; unreleased variants marked. |
| 5 | PASS | 8 rows, every cause cell states a mechanism. |
| 6 | **FINDING (P1)** | Heading wording wrong ("Variant-specific settings") — folded into check 3. |
| 7 | PASS | Pre-flight checklist: 10 numbered items. |
| 8 | **FINDING (P2)** | `workflows.md` should be `setup-and-workflows.md` — see Standard. |
| 9 | **FINDING (P2)** | Rename + link list — see Standard. |
| 10 | PASS | Reference-files table: one row per file, "when to read it" framing. |
| 11 | PASS | Train/use boundary cross-pointer present in both files. |
| 12 | **FINDING (P3)** | No `## Contents` on 3 of 4 references — see Cosmetic. |
| 13 | **FINDING (P3)** | `lora-training.md` has no numbered headings despite a §-deep-link into it — see Cosmetic. |
| 14 | PASS | 14,035 words, inside 10,000–16,000. |
| 15 | **N/A** | 23.5% (3,305/14,035) — below 25%, but §7 item 7 explicitly blesses this split. No finding. |
| 16 | PASS | 234 lines, under 500. |
| 17 | PASS | All four references between 700–3,500 words. |
| 18 | PASS | No section found that fails the "changes what the reader does" test. |
| 19 | PASS | SKILL.md carries rules + anchor numbers, not full reference tables (borderline on LoRA-weight bullet — noted, not blocking). |
| 20 | **FINDING (P1)** | Tiled-upscale text-hallucination trap is silent-failure-class and absent from SKILL.md — see Blocking. |
| 21 | PASS | Characters, LoRA training, production pipelines all covered/routed. |
| 22 | **FINDING (P3)** | Description missing "licensing" trigger term and the closing sweep sentence — see Cosmetic. |
| 23 | PASS | Two-bar heading present, byte-identical, correct slot. |
| 24 | **FINDING (P2)** | Craft-bar paragraph never names the actual authors — see Standard. |
| 25 | **FINDING (P1)** | No "Facts dated" line anywhere — see Blocking. |
| 26 | **FINDING (P1)** | Two-bar section's two contested points carry no bracket markers — see Blocking. |
| 27 | **FINDING (P1)** | 23 italic-parenthetical markers — see Blocking (full enumeration below). |
| 28 | PASS | No nested/unterminated markers; backtick counts all even. |
| 29 | **FINDING (P2)** | Orphan numbers + one bare hedge — see Standard. |
| 30 | **FINDING (P1)** | Summarise-up hop: two SKILL.md sections restate reference numbers with no attribution — see Blocking. |
| 31 | **FINDING (P3)** | One marker uses a non-closed-set qualifier — see Cosmetic. |
| 32 | **FINDING (P2)** | SKILL.md carries zero bracket markers and no "nothing flagged" line — resolves once check 26/27 fixes land, tracked separately in Standard. |
| 33 | **FINDING (P1)** | Every sibling mention in the suite table is a bare code span — see Blocking. |
| 34 | PASS | No link (in references — SKILL.md has none at all) reaches above `skills/generative-media/`. |
| 35 | **FINDING (P2)** | Suite table has no "commercial use under the licence" row — see Standard. |
| 36 | PASS (contingent) | Every sibling named in z-image's table already links back to z-image. Resolves fully once check 33's fix lands. |
| 37 | N/A | No unpublished *sibling* models named in this skill; Z-Image-Edit/Omni-Base (its own unreleased variants) already carry status words in the selector table. |
| 38 | PASS | No settings block in prose, no 2-row tables. |
| 39 | PASS | Registered in `.claude-plugin/marketplace.json` (line 30) and `README.md` (line 20). |
| 40 | **FINDING (P2)** | Watchlist is missing 3 claims that need tracking once markers are added — see Standard. |
| 41 | N/A | Existing watchlist line references still resolve; contingent on 40's additions being added correctly. |

---

## Blocking

**[P1] `SKILL.md` § heading — `## Building multi-stage workflows` is not the canonical `## Production pipelines & mixing models` slot → rename the heading verbatim.** (check 1, 3)
Evidence: `SKILL.md:106` `## Building multi-stage workflows`.
Fix: `git`-free text edit — replace the heading with `## Production pipelines & mixing models`. Content already satisfies the slot (numbered stage ladder, bypassable stages, decode-to-pixels rule lives in `workflows.md §11`); add one clause pointing explicitly at mixed-model handoffs so the new heading isn't over-promising, e.g. append to the intro sentence: "...ZIB and ZIT are combined here, not either/or. For mixing in other models entirely, see **Where Z-Image sits in the suite** and `references/workflows.md §11`."

**[P1] `SKILL.md` § heading — `## Variant-specific settings` should read `## Per-variant settings` → rename verbatim.** (check 3, 6)
Evidence: `SKILL.md:79` `## Variant-specific settings`.
Fix: Replace with `## Per-variant settings`. (Grep confirms this is a 3-1 drift against the sibling cohort that uses this axis — `flux-2`, `sdxl`, `krea-2` all say "Per-variant settings"; `wan-2-2`/`minimax-h3` are justified exceptions per §7.13 because they run a task-mode axis, not a variant axis — z-image runs a variant axis (Z-Image vs Turbo) so it belongs with the first group, not the second.)

**[P1] `SKILL.md` § heading — `## Licence and known limitations` should read `## Licence & limitations` → rename verbatim.** (check 3)
Evidence: `SKILL.md:203` `## Licence and known limitations`.
Fix: Replace with `## Licence & limitations`. Content unchanged (ampersand-form wins 4–2 across the suite per STANDARD §2 row 13).

**[P2→ escalated with P1 above, same edit] `SKILL.md` — `## Setup & ecosystem` (line 27) sits before `## The one rule that changes everything` (line 56); canonical order is the reverse.** (check 2)
Evidence: `SKILL.md:27` and `SKILL.md:56`.
Fix: Move the `## Setup & ecosystem` block (lines 27–53, everything from `Z-Image runs in **ComfyUI core**…` through the ControlNet/face-identity paragraphs, up to but not including the `---` before `## The one rule…`) to immediately after `## The one rule that changes everything` and its Don't/Do table and prompt-anatomy list (i.e., after current line 76's `---`). No content changes — just relocate the block.

**[P1] `SKILL.md` § How to read the claims — the two contested points carry no bracket markers, and no `[flagged]`/`[contested]` marker exists anywhere in SKILL.md.** (checks 25, 26, 32)
Evidence: `SKILL.md:221-223`:
```
- **Turbo negatives:** Tongyi-MAI states negatives are inert at the guidance-free setting (CFG 1.0 KSampler / `guidance_scale=0`); ComfyUI users report CFG 1.2–1.5 re-introduces weak negative subtraction. The official guidance is the fact; CFG > 1 on Turbo is a community workaround, not a supported feature.
- **LoRA cross-compat & weights:** loads-on-either-variant is a fact (shared S3-DiT); *clean transfer* and the exact per-type weights are contested craft — see `references/workflows.md §6`.
```
Fix: Add markers at the end of each bullet, before the terminal punctuation:
```
- **Turbo negatives:** Tongyi-MAI states negatives are inert at the guidance-free setting (CFG 1.0 KSampler / `guidance_scale=0`); ComfyUI users report CFG 1.2–1.5 re-introduces weak negative subtraction. The official guidance is the fact; CFG > 1 on Turbo is a community workaround, not a supported feature `[contested]`.
- **LoRA cross-compat & weights:** loads-on-either-variant is a fact (shared S3-DiT); *clean transfer* and the exact per-type weights are contested craft `[contested]` — see `references/workflows.md §6`.
```
This also clears check 32 (SKILL.md now carries ≥1 marker).

**[P1] No "Facts dated" line anywhere in the skill.** (check 25)
Evidence: `SKILL.md:207` carries only `**Release timeline:** Z-Image-Turbo shipped 26 Nov 2025; the undistilled Z-Image base 27 Jan 2026.` — a *release* date, not a *last-checked* date. The two-bar section (`SKILL.md:213-224`) ends at line 224 with no date line at all.
Fix: Append as the final paragraph of the two-bar section (after the contested-points bullets, before `---` / `## Reference files`):
```
**Facts dated 2026-01-27**; community craft refreshed 2026-08-22. This is a young, fast-moving family — re-verify quant filenames, ComfyUI template details, and LoRA tooling before relying on them, regardless of who said it.
```
(The `2026-01-27` anchor is the Z-Image-Base release date already in `SKILL.md:207`, used here as the last point the hard-facts layer is known to have been checked end-to-end; `2026-08-22` matches `freshness.json`'s `last_checked` and the date `characters.md` was actually touched. If a fuller fact-check happened more recently than base-release, the repair agent should use that date instead — this is a defensible default, not a verified one.) Keep `**Release timeline:**` where it is — §6.4 says dates the *model*, not the skill, and both facts should stay distinct.

**[P1] 23 italic-parenthetical provenance markers — the second, undeclared attribution system.** (check 27)
This is the largest and highest-value finding. Full enumeration with canonical bracket-form replacements, in file order. All are wrapped `*(...)*`; three additional `*(opt)*` instances in `workflows.md` (lines 39–41) are **not** provenance markers — they're table shorthand for "optional stage" and need no conversion.

`references/characters.md`:
1. **L11** — `*(community, convergent across named sources — Mickmumpitz workflows, WeirdWonderfulAI, Civitai dataset guides)*` → `` `[community — Mickmumpitz, WeirdWonderfulAI; convergent]` `` (move "Civitai dataset guides" into the preceding prose if you want it kept — payload cap is ~60 chars).
2. **L18** — `*(Community, strong — the canonical writeup is WeirdWonderfulAI's "QWEN Image Edit can create Character Consistent LoRA Dataset" (Oct 2025); Mickmumpitz's Consistent Character Creator v3 workflows are the most-cited turnkey version.)*` → keep the writeup titles in prose (they're doing real work), close with `` `[community — WeirdWonderfulAI, Mickmumpitz; strong]` ``.
3. **L36** — `*(Community, convergent — Civitai dataset guides 7777/21257/21114.)*` → `` `[community — Civitai guides 7777/21257/21114; convergent]` `` (this is the exact example given in the audit brief).
4. **L40** — `*(Community, strong.)*` → **no named source** — this is an orphan tier-label, not just a formatting issue. Either name the actual source (who established the 2511-tuned-for-consistency claim) or downgrade to `` `[community — single report; re-verify]` ``. Flagged again under Standard/orphan-numbers.
5. **L60** — `*(community, strong — MyAIForce's writeups are the clearest named sources)*` → `` `[community — MyAIForce; strong]` ``.
6. **L67** — `*(Community, strong — Khanykov01's multi-outfit guide, Civitai 6990.)*` → `` `[community — Khanykov01, Civitai 6990; strong]` `` (the audit brief's own worked example).
7. **L68** — `*(Community consensus; the per-face-detailer pattern is the same `[SEP]`-routing idea documented for ADetailer — see the sdxl skill's characters reference.)*` → this one contains a **nested backtick-bracket already** (`` `[SEP]` ``), which is exactly the malformed-marker shape §6.2 warns about if left inside another backtick span. Keep the ADetailer cross-reference in plain prose, close with `` `[community — convergent]` ``.
8. **L81** — `*(flagged — no DiT block map yet)*` → `` `[flagged — no DiT block map yet]` `` (mechanical — drop the italics, keep exact payload; this is also the audit brief's own example).

`references/lora-training.md`:
9. **L12** — `*(Best practice; transfer magnitude is contested across sources — see workflows §6.)*` → fold "Best practice" into the main sentence (it already reads as best practice), replace the paren with `` `[contested]` `` at the end of "a strength bump may be needed" and drop the redundant self-pointer (the paragraph already says "see workflows §6" two lines up... actually it doesn't — keep the pointer, just as prose): `"...face/identity softens and a strength bump may be needed `[contested]`. Test on the variant you'll actually deploy on — see `references/workflows.md §6`."`
10. **L35** — `*(Caption-the-residual is architecture-general LoRA craft; the natural-language phrasing is the Qwen-3/LLM-encoder specific.)*` → **not a provenance marker** (no tier word, no source, no actionable claim being sourced — it's a scope clarification about what's architecture-general vs model-specific). Recommend de-italicizing to a plain `(...)` rather than bracket-converting; it fails the §6.2(a)-(c) test cleanly.
11. **L43** — `*(community, convergent — neurocanvas Z-Image guide; alvdansen's published style-training notes; Civitai style guides)*` → `` `[community — neurocanvas, alvdansen; convergent]` `` (trim "Civitai style guides" into prose to hit the ~60-char cap).
12. **L48** — `*(flagged)*` → bare `[flagged]` is not a valid unconditional form (needs a reason per the two worked examples in §6.2) → `` `[flagged — rank ceiling unverified]` ``.
13. **L67** — `*(Community — neurocanvas, Tongyi-MAI issue #64.)*` → `` `[community — neurocanvas, Tongyi-MAI #64]` ``.
14. **L82** — `*(The modest-delta principle is sound craft; precise "alpha must be X for stacking" prescriptions are folklore — strong sources disagree, so don't over-tune by ritual.)*` → split: keep the sentence, close with `` `[contested]` `` where "strong sources disagree" is asserted: `"...Over-baked high-magnitude LoRAs hijack a stack. The modest-delta principle is sound craft; precise "alpha must be X for stacking" prescriptions are folklore `[contested]` — don't over-tune by ritual."`

`references/workflows.md`:
15. **L112** — `*(DiT target is verified from PR #12717; the model-vs-model+clip node choice is a usage detail, not a break-or-not fact.)*` → the PR #12717 half is a hard fact, not craft — convert to `` `[official — PR #12717]` `` on the DiT-target clause only; drop the rest as plain prose (it's already stated in the paragraph above).
16. **L130** — `*(Community; exact numbers are fast-moving and sources mildly disagree — treat as starting points, and prefer the weight printed on the LoRA's own model card.)*` → no named source (orphan) → `` `[community — single report; re-verify]` `` or name actual authors if known; flagged again under Standard.
17. **L134** — `*(rgthree README; community.)*` → `` `[community — rgthree README]` ``.
18. **L140** — `*(Sources: HF Tongyi-MAI #18; RunComfy AI-Toolkit notes; lilting.ch. Fast-moving.)*` → this attaches to a sentence already using the word "contested" two sentences earlier ("genuinely contested across sources") → `` `[contested]` `` plus `` `[community — HF Tongyi-MAI #18, RunComfy, lilting.ch]` `` (two markers, or fold sources into prose and keep one `[contested]` tag).
19. **L144** — `*(lilting.ch; DiffSynth-Studio HF.)*` → `` `[community — lilting.ch, DiffSynth-Studio]` ``.
20. **L148** — `*(Cross-model community pattern; not A/B-tested on Z-Image specifically.)*` → `` `[community — cross-model pattern; re-verify]` ``.
21. **L152** — `*(Civitai; Ostris HF; fast-moving.)*` → `` `[community — Civitai, Ostris HF]` ``.
22. **L188** — `` *(Community-standard practice; see the `image-production-workflows` skill for the full color-management treatment.)* `` → `` `[community]` `` (source is already named via the cross-link in the same sentence, so a bare tier tag suffices — or omit the marker entirely per §6.2's "no marker required when a named source is in the same sentence" clause; the link *is* the source).
23. **L283** — `*(Community, named author.)*` → the author (Cordina) is **already named earlier in the same sentence** ("e.g. Cordina's 'ZIT Refiner workflows – SDXL v1'"), so per §6.2 this marker is not strictly required. For consistency, either delete it or convert to `` `[community — Cordina, Civitai Jan 2026]` ``.

**[P1] Sibling mentions in the suite table are bare code spans, not markdown links.** (check 33)
Evidence: `SKILL.md:193-199`, seven mentions across six rows (`sdxl` appears twice): `` `flux-2` `` (L193), `` `sdxl` `` (L194, L196), `` `ideogram-4` `` (L195), `` `krea-2` `` (L197), `` `image-production-workflows` `` (L198), `` `wan-2-2` `` (L199). **This is the only place in `SKILL.md` any sibling is mentioned — SKILL.md has zero markdown-style cross-links.**
Fix: convert each to `[`name`](../name/)`:
```
| Consistent characters | ... | [`flux-2`](../flux-2/) for no-training multi-reference identity (ReferenceLatent, PuLID) |
| Style LoRAs | ... | [`sdxl`](../sdxl/) for the deepest trained-LoRA ecosystem and mature recipes |
| In-image typography | ... | [`ideogram-4`](../ideogram-4/) — the open-weights typography leader |
| Structural control (pose/depth/canny) | ... | [`sdxl`](../sdxl/) for the most mature, complete control stack |
| Aesthetic range / stylistic exploration | ... | [`krea-2`](../krea-2/) — deliberately no house look ... |
| Mixed-model pipelines | ... | [`image-production-workflows`](../image-production-workflows/) for the cross-model craft itself |
| Making it move | ... | [`wan-2-2`](../wan-2-2/) — image-to-video. ... |
```
Reciprocity (check 36) is already satisfied — every one of these siblings already links back to `z-image` (verified by grep); no return-edit needed once this fix lands.

**[P1] Summarise-up hop: two SKILL.md sections restate reference-file numbers without carrying the reference's attribution.** (check 30)
Evidence 1: `SKILL.md:106-123` (`## Building multi-stage workflows`) states the ×1.7 latent-upscale factor, ×2 SD-upscale factor, and ~0.23 tiled-upscale denoise. `references/workflows.md:51` labels the section these numbers come from `## 3. Per-stage settings (community layered pipeline)`, and its lede (`workflows.md:5-8`) explicitly says these numbers come from **custom community finetunes**, "treat as well-tuned starting points, not stock requirements." None of that qualifier survives into SKILL.md.
Fix: add one clause to the SKILL.md section, e.g. after "Final resolution ≈ base × 1.7 × 2": "These specific multipliers and the 0.23 tiled-upscale denoise come from a widely-shared community pipeline `[community — layered-pipeline pattern; see references/workflows.md §3]` running custom finetunes — the architecture transfers to stock Z-Image; nudge the exact numbers."

Evidence 2: `SKILL.md:102` (Z-Image-Turbo per-variant settings) states "style LoRAs often want 0.3–0.5, character 0.7–1.0" — the same per-type breakdown as `references/workflows.md:124-128`'s table, which carries `` *(Community; exact numbers are fast-moving and sources mildly disagree...)* `` immediately below it (line 130, itself flagged above for conversion). SKILL.md carries none of that hedge.
Fix: append `` `[community — per-LoRA tunings, not a hard rule]` `` to the sentence, or shorten to a pointer: "...character 0.7–1.0 (per-LoRA, read the author's card; full weight table and sourcing in `references/workflows.md §6`)."

**[P1] Silent-failure trap buried in a reference, absent from SKILL.md: the tiled-upscale text-hallucination gotcha.** (check 20)
Evidence: `references/workflows.md:186`: *"When `UltimateSDUpscale` splits the image into tiles, a tile only 'sees' its local patch — so a prompt that says 'a tattoo reading "X" below the collarbone' can make the model stamp that text onto unrelated smooth-skin tiles (shoulder, arm, back)."* This produces a **plausible-looking wrong result** (stray text/marks appearing on skin) with no error — exactly §5.4's silent-failure test. It's not mentioned anywhere in `SKILL.md`, including the Failure Modes & QC table and the multi-stage-workflow section that names the tiled-upscale stage.
Fix: add a row to `SKILL.md`'s `## Failure modes & QC` table:
```
| Localized text/tattoo bleeds onto unrelated body areas after tiled upscale | Each `UltimateSDUpscale` tile only sees its local patch, not the whole prompt | Simplify the prompt for the upscale pass, or use the per-tile conditioning switch — see `references/workflows.md §7` |
```

---

## Standard

**[P2] Rename `references/workflows.md` → `references/setup-and-workflows.md`.** (checks 8, 9)
Evidence: `skills/generative-media/z-image/references/workflows.md` exists; canonical slot name per STANDARD §4.1 is `setup-and-workflows.md`. Content matches the canonical slot's job (node-by-node graph walkthrough, quant/VRAM discussion embedded in SKILL.md rather than here — noted, not blocking — LoRA loading/stacking, the multi-stage ladder, mixed-model handoffs).
Fix: `git mv skills/generative-media/z-image/references/workflows.md skills/generative-media/z-image/references/setup-and-workflows.md`, then update every internal reference to the old filename. **No external/cross-skill inbound links exist** (grepped the whole `skills/` tree for `z-image/references/workflows` — zero hits), so this is entirely self-contained. Occurrences to update:
- `SKILL.md`: lines 50, 52, 87, 102, 123, 198, 223, 232, 233 (9 occurrences — corrects STANDARD §4.3's estimate of "eleven," the true count is 9 in SKILL.md).
- `references/characters.md`: lines 3, 60, 83, 89 (4 occurrences).
- `references/lora-training.md`: lines 6, 149 (2 occurrences).
- Total: 15 in-repo string replacements of `workflows.md` → `setup-and-workflows.md`, all within the z-image skill itself.

**[P2] Craft-bar paragraph in the two-bar section never names actual authors.** (check 24)
Evidence: `SKILL.md:219`: "**The authoritative source here is the community** — named workflow authors and reproducible Civitai/Reddit/Banodoco results that have run thousands of generations — *not* the model card..." — no author is actually named here (compare `minimax-h3` or `krea-2`, which list real names in this exact slot).
Fix: name at least the 3-4 most load-bearing authors already cited elsewhere in the skill, e.g.: "**The authoritative source here is the community** — named workflow authors (Mickmumpitz, WeirdWonderfulAI, MyAIForce, Khanykov01) and reproducible Civitai/Reddit/Banodoco results that have run thousands of generations..."

**[P2] Orphan craft numbers with no marker and no named source.** (check 29)
- `SKILL.md:102` — LoRA weight range "0.7–0.8... sweep 0.5–1.2" — no marker in SKILL.md (partially addressed by the summarise-up-hop fix above; same finding, different rubric angle).
- `references/lora-training.md:69-77` — the hyperparameter table (rank 8-16, LR 1e-4/5e-5, steps 2000-3000, "RTX 5090: ~1 hour for 3k steps") carries no marker on the table itself; the caveat paragraph below it (line 84) hedges in prose ("a community starting point... verify... before a long run") but names no source and uses no bracket. Fix: add `` `[community — Ostris AI-Toolkit config examples; verify before a long run]` `` to the table or its caption.
- `references/workflows.md:236` — `control_context_scale: 0.65-0.80` recommendation carries no marker and no named source. Fix: `` `[community]` `` at minimum, or name the source if known.
- `references/characters.md:40` — "2511 (Dec 2025) is the version tuned for character consistency" is stated flatly with only the bare `*(Community, strong.)*` tag (already flagged above under the italic-paren list) — no actual name. Fix as noted there.
- `references/workflows.md:130` — LoRA-weight-by-type table's `*(Community; ...)*` tag (already flagged above) also has no named source — same underlying gap.
- **Bare epistemic hedge:** `references/lora-training.md:121` — "the community consensus is to evaluate visually" names no one and has no marker nearby. Fix: either name a source or soften to plain unmarked craft prose without invoking "consensus" as a stand-in for a citation (e.g., "the standard approach is to evaluate visually — loss barely predicts image quality").

**[P2] Suite table has no "commercial use under the licence" row.** (check 35)
Evidence: `SKILL.md:187-199` (`## Where Z-Image sits in the suite`) covers 7 of the 8 required image-model axes (consistent characters, style/character LoRA ecosystem, in-image typography, structural control, aesthetic range, mixed-model pipelines, making it move) but has no row for licence comparison, even though `ideogram-4` (non-commercial gated weights) and `minimax-h3` (territory-gated) sit in the same suite and a reader comparing "can I use this commercially" across models gets no help from z-image's own table.
Fix: add a row, e.g.:
```
| Commercial use under the licence | Apache-2.0, no restriction (`## Licence & limitations`) | `ideogram-4` if you need hosted commercial guarantees without self-hosting; avoid `minimax-h3` if you're in a territory it excludes |
```

**[P2] `freshness.json` watchlist is missing 3 claims that need tracking once the fixes above land.** (check 40)
Evidence: current watchlist (9 items) tracks `z-image-edit`, `z-image-omni-base`, `regional-tooling`, `lora-pr-12717`, `base-turbo-transfer`, `base-vram`, `zit-bucket-and-noise`, `z-image-nsfw-position`, `zimage-dop-failure`. It does **not** track:
1. The Turbo-negatives contested point (`SKILL.md:221`, newly marked `[contested]` per the Blocking fix above).
2. The style-LoRA rank-ceiling flag (`references/lora-training.md:48`, `[flagged — rank ceiling unverified]` per the fix above).
3. The DiT-block-map gap (`references/characters.md:81`, `[flagged — no DiT block map yet]`, already a well-formed marker today — it's simply absent from the watchlist).
Fix: add three watchlist entries following the existing schema (`id`, `type`, `claim`, `where`, `check`), pointing at the line locations above. (This is a `freshness.json` edit, out of scope for this audit's single output file — flagging for the repair pass.)

---

## Cosmetic

**[P3] No `## Contents` TOC on 3 of 4 references (all ≥2,000 words).** (check 12)
Evidence: `references/prompting-guide.md` (3,382 w), `references/setup-and-workflows.md` (post-rename, 3,462 w), `references/lora-training.md` (2,298 w) all lack a `## Contents` heading. `characters.md` (1,588 w) is correctly exempt (under the 2,000-word threshold).
Fix: add a `## Contents` block at the top of each, listing the existing numbered `## N.` headings (all three already have them except `lora-training.md` — see next finding).

**[P3] `references/lora-training.md` has no numbered `## N.` headings, despite being both ≥2,000 words (once a TOC is added, numbering becomes required) and already `§`-deep-linked.** (check 13)
Evidence: `references/characters.md:41` links `` `lora-training.md §Dataset` `` — a non-numeric anchor into a file whose actual heading is `## Dataset generation workflow` (line 16), not literally "Dataset."
Fix: number `lora-training.md`'s ten `##`/`###` headings (`## 1. Which variant to train on`, `## 2. Dataset generation workflow`, etc.), add the `## Contents` TOC, and update `characters.md:41`'s `§Dataset` reference to the correct number.

**[P3] Description frontmatter: missing "licensing" trigger term and no closing-sweep sentence.** (check 22)
Evidence: `SKILL.md:4` (210 words, inside the 180-320 band — no length finding) enumerates variant choice, setup, prompting, ControlNet, face identity, workflows, LoRA usage, LoRA training, character creation, style-LoRA training, and mixed-model refining — but never mentions licensing/licence as a trigger, and the paragraph ends on "...refining SDXL renders." with no closing sweep like "Use this for any question about Z-Image in any context."
Fix: append to the trigger list, e.g. "...or checking what the Apache-2.0 licence permits for commercial use" before the final clause, and add a closing sentence: "Use this for any question about Z-Image in any context."

**[P3] One marker uses a qualifier outside the closed set.** (check 31)
Evidence: `references/lora-training.md:110`: `` `[community — Civitai model API, sampled 2026-08-13]` `` — "sampled 2026-08-13" is not one of the six closed-set qualifiers (`re-verify`, `single report`, `contested`, `early`, `strong`, `convergent`).
Fix: move the date into prose and shorten the marker: "...roughly 46-47% of published Z-Image LoRAs are adult-flagged... (sampled 2026-08-13) `` `[community — Civitai model API]` ``."

**[P3, observational, not a rubric violation]** `## Key realism technique` (`SKILL.md:127`) is a generic template-shaped heading rather than naming the model's specific trait, unlike the sibling exemplar this same skill's own reference uses (`references/prompting-guide.md:20`: `## 2. Realism: killing the plastic default`). Not required by any check (§2 row 7 requires *a* trait name, and "realism" is technically named), but reusing the sharper reference heading in SKILL.md would tighten it. Optional, low priority — not counted in the severity totals above.

---

## Beyond the rubric

### 1. Unattributed craft — full list

See the 23-item italic-parenthetical enumeration under **Blocking** above (check 27) — that list *is* the unattributed-craft inventory; every entry either lacks a bracket marker (mechanical fix) or, in five cases (characters.md L40, L67-adjacent-orphan pattern, lora-training.md L130-referenced items, and the two flagged directly above), lacks a *named source entirely* and needs either a name or a downgrade to `[community — single report; re-verify]`. Cross-reference: **Standard** finding "Orphan craft numbers" lists five additional numeric claims (hyperparameter table, `control_context_scale`, LoRA weight-by-type) that were never wrapped in any marker — italic or bracket — at all.

### 2. Staleness

`references/characters.md` was touched 2026-08-22 (the `[community — MASilverHammer; single report, re-verify]` DOP-failure note at line 70). Everything else — `SKILL.md`, `prompting-guide.md`, `lora-training.md`, `setup-and-workflows.md`/`workflows.md` — reads as older and shows no sign of a full re-check on that date (no updated dates, no adjustments to the `2026-01-27` base-release anchor). Concretely stale-reading spots:
- `SKILL.md:209` — "Tongyi-MAI has not published an inference VRAM figure" for base Z-Image — `freshness.json`'s own `base-vram` watchlist item flags this as an open gap; worth a check now that the base model has been out since January.
- `references/workflows.md:268` — "No PuLID or IP-Adapter face implementation exists for Z-Image as of **June 2026**" — this date predates the characters.md touch by two months and is the oldest explicit date-stamp in the corpus; worth confirming it's still true rather than just still-unchecked.
- `references/lora-training.md:84` — "these Z-Image numbers are a community starting point and **the tooling is new**" — reasonable in isolation, but nothing in the file indicates when "new" was last confirmed against current AI-Toolkit.
This is exactly what the missing "Facts dated" line (Blocking finding) would surface if it existed — its absence is *why* staleness here is only discoverable by manual read rather than a grep.

### 3. Over-conformity risk — Do not touch

- **The SKILL.md/reference split (22-23%).** §7 item 7 already names this correctly: the two references it leans on are the deepest in the suite, the total corpus is normal-sized, and every pillar is pointed at. Do not pad SKILL.md to hit 25% — that would be padding by the §5.3 test, not depth. The *only* legitimate edit here is the filename rename; the split itself is healthy delegation, not under-depth, and matches the task's own framing question — verdict: **not under-depth.**
- **The Official/Community two-source framing at the top of `workflows.md` (lines 5-8).** This is a better provenance pattern than most siblings have at the file level — it declares up front which numbers come from the stock template vs. community finetunes, before any individual claim needs its own marker. Preserve this through the rename; it is not required by STANDARD but is not damaged by conforming to it either, and losing it in a mechanical rename pass would be a regression.
- **The `§`-deep-linking practice** (STANDARD §6.7 explicitly praises z-image for this) must survive the `workflows.md → setup-and-workflows.md` rename with section numbers intact — the rename fix above already accounts for this, but a repair agent doing a blind find-replace on the filename alone, without checking that `§6`, `§9`, `§10`, `§11` anchors still resolve post-rename, would silently break the one thing this skill does better than its siblings.
- **The variant-selector footnotes (¹ ²)** (`SKILL.md:20-21`) pack the CFG=1.0-vs-0.0 silent-failure trap and the diffusers/ComfyUI step-count discrepancy directly into the selector table via footnote rather than a separate callout. This is denser than any sibling's selector table and is exactly the kind of "silent-failure trap in SKILL.md" §5.4 asks for — do not flatten it into prose during any heading-reorder pass.

I did not identify any case where the STANDARD itself is wrong and z-image is right — the genuine deviations found (heading text, section order, filename, missing markers, missing date line) are all real drift, not defensible choices the standard failed to anticipate.
