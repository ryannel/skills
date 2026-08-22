# Final conformance — `ltx-2-5`, `scail-2`, `anima`, plus suite-wide marker calibration

**Date:** 2026-08-22. **Graded against:** `workbench/uniformity/STANDARD.md` §8, same rubric and
same severity scale as the ten sibling audits in this folder.

**Headline.** All three pass. Two carry a single P2 each; `ltx-2-5` carries three P2s, one of which
is the depth question. The revision rounds did **not** break structure — no section drifted out of
order, no `## Contents` list lost sync with its headings, no `§` deep-link went dead, no reference
table row went stale, and exactly one duplicated line exists in the whole set. What the revision
rounds *did* leave behind is concentrated in one place: **provenance markers**, where `scail-2` and
`ltx-2-5` are outside any defensible band, in two different ways.

Mechanical sweeps run before grading, all clean unless noted:

| Sweep | Result |
|---|---|
| `## Contents` TOC vs actual `##` headings, every reference | **13/13 in sync** (the one variance is cosmetic: `anima/references/prompting-guide.md` TOC says "Worked prompts (A–E)", heading says "14. Worked prompts") |
| `§` deep-links from SKILL.md into references | **0 dead** across all three |
| `## Reference files` rows vs files on disk | **exact parity**, all three |
| Duplicated ≥70-char lines across each skill's corpus | **1 total** (`scail-2`) |
| Malformed / nested / unterminated markers | **0** |
| Stray tier vocabulary outside the closed set of six | **0** |
| Links reaching above `skills/generative-media/` | **0** |
| Bare code-span sibling mentions | **0** |
| Registration in `marketplace.json` + README | **3/3** |

---

## ltx-2-5

**Verdict: PASS with three P2s.** Corpus 20,439 w · SKILL.md 8,053 w body (370 lines) · 41% share.

| # | Check | Result | Evidence | Fix |
|---|---|---|---|---|
| 1 | MANDATORY sections present | **PASS** | all 15 slots present; slot 1a at `SKILL.md:15`, slot 2 at `:17` | — |
| 2 | Section order | **PASS** | selector → one-rule → setup → per-mode → signature → mechanics → pipelines → failures → pre-flight → suite → licence → two-bar → refs | — |
| 3 | Verbatim headings | **PASS** | `:90`, `:110`, `:173`, `:254`, `:269`, `:291`, `:306`, `:325`, `:333`, `:362` all byte-exact | — |
| 3b | Two selector tables (`Variant` **and** `Task-mode`) | **JUSTIFIED** | `:41` and `:68`; the skill declares the deviation and cites the precedent at `:43` — "LTX runs two composable axes, the way `sdxl` runs speed variant × checkpoint dialect" | Keep. §7.6 blesses exactly this shape, and the skill says why in-line as §1 requires |
| 4 | Selector "Use when…" column, unreleased variants marked | **PASS** | `:45–:50`; `LTX-2.5-Pre-Trained` and LTX-2 (19B) marked at `:52`; Video Editing IC-LoRA `[pending release]` at `:64` | — |
| 5 | Failure table ≥8 rows, cause states mechanism | **PASS** | 12 rows, `:271–:288`. Causes are mechanisms throughout — "peak memory arrives after the transformer is done", "guidance is baked into the distillation", "an unstated camera is *unspecified*, not neutral" | — |
| 6 | Per-mode `###` blocks, distilled/undistilled apart | **PASS** | 6 blocks `:177–:210`; distilled `:177` and dev/undistilled `:187` explicitly separated, with the CFG-band caveat scoped to the distilled path | — |
| 7 | Pre-flight numbered 8–12 | **PASS** | 10 items, `:293–:304` | — |
| 8 | Four §4.1 core slots | **PASS** | all four present under canonical names | — |
| 9 | Renames needed | **PASS** | `licence-and-derivatives.md` is a §4.2 extra by concern; §7.1 precedent (`minimax-h3/licence-and-territory.md`) | — |
| 10 | Reference table = files, says *when to read* | **PASS** | `:364–:370`, 5 rows / 5 files, all phrased as occasions | — |
| 11 | Train/use boundary + cross-pointer | **PASS** | `lora-training.md` owns making; `setup-and-workflows.md §6` owns loading and stacking; both pointed at from `:366`/`:368` | — |
| 12 | `## Contents` on refs ≥2,000 w | **PASS** | 4/4 required; `characters.md` at 1,422 w is exempt | — |
| 13 | Numbered `## N.` headings | **PASS** | all four TOC'd files numbered | — |
| 14 | Corpus 10,000–16,000 | **FAIL (P2)** | 20,439 w — 28% above the band, and 13% above `minimax-h3`, the current accepted suite maximum at 18,098 | See **Depth ruling**. The SKILL.md demotions do not fix this — they move words within the corpus. Resolve as a §7 justified deviation with the reasoning written down, or revisit §5.2's upper bound, whose sample never contained a two-model skill |
| 15 | SKILL.md ≤5,500 w / 25–40% | **FAIL (P2)** | 8,053 w body, 41% | See **Depth ruling** — the justification holds for two of the four §5.2 grounds but licenses ~7,000 w, not 8,053 |
| 16 | SKILL.md <500 lines | **PASS** | 370 | — |
| 17 | Each reference 700–3,500 w | **PASS** | `prompting-guide.md` at 4,187 w is over, but §5.2 permits over-3,500 with a `## Contents` TOC, which it has | — |
| 18 | Sections that change nothing | **FAIL (P3)** | `:356` "**On this skill's length**" is a note to auditors, not readers; delete it and the reader's next action is unchanged. It is also self-refuting — it claims the length is justified by two grounds, and the overage sits outside both | Delete `:356`. The justification belongs in this audit |
| 19 | Table/derivation duplicated SKILL↔reference | **FAIL (P2)** | The inert-widget finding is stated twice at near-full length: `:163` ("Read these templates as a graph, not as text") and again inside the two-bar hard-facts bar at `:337` ("Template numbers here are the values the graph **executes**…") | Keep the methodology caveat in the two-bar section; cut `:163` to its actionable last sentence — "Trace links before trusting any number pulled from one of these files" — plus the three named inert values |
| 20 | Silent-failure traps in SKILL.md | **PASS** | the `8k+1` tail drop, the audio-latent desync, the fps-on-`LTXVConditioning` trap, the inert negative at CFG 1, the enhancer's dead widget, ReDetail's /64 rule against the /32 default — all in SKILL.md | — |
| 21 | Three pillars covered or routed | **PASS** | `characters.md`, `lora-training.md`, `## Production pipelines & mixing models` `:254` | — |
| 22 | Description 180–320 w, folded `>`, five §6.1 elements | **PASS** | 319 w — one word under the ceiling. "even obliquely:" present, closing sweep present | Watch it: any further addition breaches §6.1 |
| 23 | Two-bar `##`, byte-identical, second-to-last | **PASS** | `:333`, immediately before `## Reference files` `:362` | — |
| 24 | Five §6.3 elements | **PASS** | lede `:335`, hard-facts roll-call + named artefacts `:337`, craft roll-call + 13 named authors `:339`, contested bullets `:343–:355`, date line `:358` | — |
| 25 | Date line, `**Facts dated YYYY-MM-DD**`, ISO | **PASS** | `:358` | — |
| 26 | Every flagged/contested/pending greppable | **PASS** | 56 markers; all two-bar contested bullets carry theirs | — |
| 27 | Italic-parenthetical markers | **PASS** | 0 | — |
| 28 | Malformed markers | **PASS** | 0 | — |
| 29 | Orphan craft numbers / bare hedges | **PASS** | spot-checked the VRAM figures, the 0.5–1.5 LoRA band, the 0.7 FLF2V strength, the denoise ladder — all attributed or officially sourced | — |
| 30 | Summarise-up hop | **PASS** | ratio **1.68** (SKILL 9.2/1k vs refs 5.5/1k) — well above §6.2.1's 0.6 floor. `setup-and-workflows.md:93` explicitly declares the division of labour rather than duplicating | — |
| 30a | §6.2.1 density band | **FAIL (P2)** | total 7.0/1k (at ceiling); **watchlist class 2.78/1k, 56 absolute** — 2.3× the 24 cap | See **Marker calibration**. Merge sibling flags in the two-bar list; push separable ones into the reference that owns them |
| 30b | Bare `[official]` | **PASS** | **1** of 18 official markers. `ltx-2-5` does **not** have the `anima`/`scail-2` inflation problem | — |
| 31 | Marker syntax canonical | **PASS** | backticked, em-dash, six tiers only, payloads under ~60 chars | — |
| 32 | ≥1 flagged/contested in SKILL.md | **PASS** | 30 | — |
| 33 | Sibling mentions are relative links | **PASS** | 0 bare code-spans | — |
| 34 | Links above `generative-media/` | **PASS** | 0 | — |
| 35 | Seven video suite-table axes | **PASS** | `:308–:322` covers all seven; the "Exact motion transfer" row honestly answers "❌ no reference-to-video mode at all" | — |
| 36 | Bidirectionality | **FAIL (P2), in the sibling** | `wan-2-2/SKILL.md:174, 178, 180, 251` still name **SCAIL-2** in plain bold; that was correct under §6.5 while it was unpublished and is now a dead reference for an agent | Reciprocal edit in `wan-2-2`, not here — see **Recommended edits** #9 |
| 37 | Unpublished models plain bold + status word | **PASS** | Flux 3 and Bernini-R not claimed; `LTX-2 (19B)` marked superseded at `:52` | — |
| 38 | Tables for parallel structure, prose for mechanism | **PASS** | no settings block in prose, no two-row table. The Lightricks-comparison-table warning at `:324` is correctly prose | — |
| 39 | Registered | **PASS** | `marketplace.json:38`, `README.md:26` | — |
| 40 | `freshness.json` entry + watchlist | **PENDING** | not yet in `freshness.json` (another agent holds the file) | Register `hot`. **But do not transcribe 56 markers into a watchlist** — see limit 3 |
| 41 | Watchlist line refs survive repair | **N/A** | no entry yet | — |

---

## scail-2

**Verdict: PASS with one P2.** Corpus 15,058 w · SKILL.md 5,201 w body (321 lines) · 36% share.

| # | Check | Result | Evidence | Fix |
|---|---|---|---|---|
| 1 | MANDATORY sections | **PASS** | all present. Slot 1a N/A — the licence is permissive on both halves and gates nobody | — |
| 2 | Section order | **PASS** | one deviation, judged below | — |
| 2b | `## Masks are the control surface` `:61` sits **before** `## Setup & ecosystem` `:80` | **JUSTIFIED** | a slot-8 mechanic placed ahead of slot 5, and the skill declares why in an italic lede at `:63`: "*This precedes setup and settings because it decides which mode you are actually running — no number below matters if the masks are wrong.*" | Keep. §1's test is met on both limbs — the reader is surprised, and the surprise teaches the true thing about this model. The self-declaration is exactly what §1 asks for |
| 2c | `### Its relationship to Wan 2.1 runs at three levels` at `:13` is an `###` with **no parent `##`** — it sits above every `##` in the file | **FAIL (P3)** | `SKILL.md:13` | Promote to `## Its relationship to Wan 2.1 runs at three levels`. The *placement* is right — the lineage decides whether Wan LoRAs load, and it corrects an active misattribution — but an orphan `###` above the document's first `##` is a heading-tree defect, not a section |
| 3 | Verbatim headings | **PASS** | `:40`, `:80`, `:136`, `:194`, `:208`, `:225`, `:242`, `:269`, `:290`, `:312` byte-exact | — |
| 3b | `## Signature quality — it tracks, and then it embellishes` `:158` | **FAIL (P3)** | §2.7 says the heading names the actual trait, not a template. "Signature quality" is the template word | Rename to the trait alone, e.g. `## It tracks, and then it embellishes` — the clause after the dash is already correct and already names both defaults (per-frame aesthetic and motion character) |
| 4 | Selector "Use when…", unreleased marked | **PASS** | `:29–:34`; multi-reference carries the vendor's own "unoptimised" warning | — |
| 5 | Failure table ≥8 rows, mechanism in cause | **PASS** | 9 rows `:210–:222`. Note `:216` states "**No mechanism is known.** Reported consistently, never vendor-acknowledged" — that is honest absence, not a restated symptom, and it is the right way to fill the cell | — |
| 6 | Per-mode `###` blocks | **PASS** | 4 blocks `:140–:156`, written as deltas from the stock table with the distilled LightX2V path kept separate | — |
| 7 | Pre-flight 8–12 | **PASS** | 12 items `:227–:238` | — |
| 8 | Four core slots | **PASS, one exemption claimed** | no `lora-training.md`. §4.1's exemption requires no training path *and* saying so in SKILL.md and routing — `:182` does both ("SCAIL-2 has no LoRA-training path today, and this skill deliberately ships no `lora-training.md`"), routes to `character-lora-training` and `wan-2-2`, and the `## Reference files` table repeats it at `:321`. Exemption **granted** | — |
| 9 | Renames | **PASS** | `masks-and-tracking.md` is a §4.2 concern-named extra and it is the right call — the masks are the control surface, and no canonical slot covers them | — |
| 10 | Reference table parity + *when to read* | **PASS** | 4/4, each phrased as an occasion. The `masks-and-tracking.md` row opens "**Read this before your first run**" | — |
| 11 | Train/use boundary | **N/A** | no training path; loading is `setup-and-workflows.md §6`, pointed at from `:188` | — |
| 12–13 | TOCs and numbering | **PASS** | 4/4 numbered and TOC'd | — |
| 14 | Corpus band | **PASS** | 15,058 w | — |
| 15 | SKILL.md size/share | **PASS** | 5,201 w body, 36% — inside both limits, though 5,500 including frontmatter sits exactly on §5.2's absolute cap | Do not add to this file without demoting something |
| 16 | <500 lines | **PASS** | 321 | — |
| 17 | Each reference 700–3,500 | **PASS** | 826 / 2,332 / 2,930 / 3,470 — all inside | — |
| 18 | Padding | **PASS** | every section changes an action | — |
| 19 | Duplication SKILL↔reference | **FAIL (P3)** | `SKILL.md:219` and `references/characters.md:162` carry the **same failure-table row verbatim** ("Hands distort; lips and eyes out of sync…") — the only exact duplicate in all three skills, and the signature of a partial edit | Keep the SKILL.md row; in `characters.md:162` replace it with a pointer, or vary the framing to the identity-specific angle that file owns |
| 20 | Silent-failure traps in SKILL.md | **PASS** | the `replacement_mode` pairing (`:70–:74`), the three-name VAE trap (`:98`), the /32-vs-/16 divisibility ruling (`:129`), the `int8_convrot` slowdown (`:131`) — all present, all correctly judged as silent | — |
| 21 | Three pillars | **PASS** | characters covered; LoRA training honestly routed (§4.1 exemption); pipelines at `:194` | — |
| 22 | Description | **PASS** | 297 w, folded `>`, "even obliquely:" present, closing sweep present, routing note names Wan Animate / H3 / Bernini-R | — |
| 23–25 | Two-bar heading, contents, date line | **PASS** | `:290`, five elements present, `**Facts dated 2026-08-22**` as the final paragraph `:308` | — |
| 26 | Flagged/contested greppable | **PASS** | 30 markers; every two-bar bullet carries its own | — |
| 27–28 | Italic-paren / malformed | **PASS** | 0 / 0 | — |
| 29 | Orphan numbers / bare hedges | **PASS** | the 40/5.0/3.0 and 8/1.0/1 pairs, 81 frames, the 76-frame stride, the ~161-frame guardrail, the 512×896 defaults — all sourced | — |
| 30 | Summarise-up hop | **PASS** | ratio **1.04** | — |
| 30a | §6.2.1 density band | **FAIL (P2)** | **14.8/1k — double the ceiling and the highest in the suite by 57%.** Watchlist class 2.03/1k, 30 absolute, also over | See **Marker calibration** and **Recommended edits** #3–#4 |
| 30b | Bare `[official]` | **FAIL (P2)** | **54 of 77** official markers are bare `[official]` with no artefact. Sampled instances at `:27`, `:32`, `:74`, `:82`, `:103`, `:109`, `:146`, `:150`, `:154` — every one marks a fact the skill's own two-bar hard-facts roll-call already declares (`:294`: "the four modes… the two-mask contract… the 40/5.0/3.0 and 8/1.0/1 pairs; 81 frames, the 76-frame stride, the 512×896 node defaults") | §6.2 exempts exactly these. Delete the bare markers whose claim is inside the roll-call; give the remainder their artefact (`[official — PR #14373 diff]`, `[official — docs.comfy.org/…]`, `[official — arXiv 2606.10804v3 §4.1]`) |
| 31 | Marker syntax | **PASS** | backticked, em-dash, closed tier set, payloads short | — |
| 32 | ≥1 flagged/contested in SKILL.md | **PASS** | 19 | — |
| 33–34 | Links | **PASS** | 0 bare spans, 0 escaping links | — |
| 35 | Seven video axes | **PASS** | `:244–:254` covers all seven, including two honest ❌ rows | — |
| 36 | Bidirectionality | **PASS** | `wan-2-2:174–180` and `minimax-h3:319` both carry SCAIL-2 rows; `minimax-h3:319` already links `[scail-2](../scail-2/)`. `wan-2-2`'s mentions are still plain bold — the reciprocal edit is #9 | — |
| 37 | Unpublished models | **PASS** | **Bernini-R** plain bold with the status words "announced, not covered by this suite" `:264`, and `:266` gives its lineage without linking | — |
| 38 | Tables vs prose | **PASS** | the extra decision table at `:256` ("*I have a video and I want a different person in it*") is four rows of genuinely parallel structure — correct as a table | — |
| 39 | Registered | **PASS** | `marketplace.json:39`, `README.md:27` | — |
| 40–41 | `freshness.json` | **PENDING** | not yet registered | Register `hot`; watchlist ~18 entries after the limit-3 merge |

---

## anima

**Verdict: PASS with one P3.** Corpus 15,990 w · SKILL.md 5,152 w body (277 lines) · 34% share.

| # | Check | Result | Evidence | Fix |
|---|---|---|---|---|
| 1 | MANDATORY sections | **PASS** | all 15 applicable slots. Slot 1a (defining constraint) **N/A-justified** — Anima's licence gates *shipping the weights*, not *using the model*; images are commercially free to anyone, so nothing here can rule a reader out. The intro correctly uses that slot for the stated non-goal ("The model doesn't do realism well. This is intended.") | — |
| 2 | Section order | **PASS** | selector `:13` → one-rule `:29` → setup `:61` → per-variant `:100` → signature `:122` → mechanics `:134`, `:140` → pipelines `:158` → failures `:172` → pre-flight `:189` → suite `:206` → licence `:224` → two-bar `:245` → refs `:270`. Textbook | — |
| 3 | Verbatim headings | **PASS** | all ten byte-exact, including `## Per-variant settings` (not "Variant-specific settings" — the known drift) | — |
| 3b | Missing `---` rule between the intro and `## Variant selector` | **FAIL (P3)** | 13 rules for 14 `##` sections; every other section boundary carries one | Insert `---` before `SKILL.md:13`. Cosmetic, and the classic residue of text inserted at the top during a revision |
| 4 | Selector "Use when…", unreleased marked | **PASS** | `:15–:21`; Aesthetic v1.1 flagged as undocumented, the 2.9B/3.8B forks marked "**not CircleStone releases**", `[pending release]` on LLLite at `:152` | — |
| 5 | Failure table ≥8 rows, mechanism in cause | **PASS** | 9 rows `:174–:185`. Strongest cause cell in all three skills at `:184`: "The trainer was left free to update the **LLM adapter**… your twenty images rewrote its understanding of *every* prompt. No error is raised" | — |
| 6 | Per-variant `###` blocks, distilled apart | **PASS** | 3 blocks `:102–:119`; Turbo (guidance-distilled) explicitly separated with negatives marked inert | — |
| 7 | Pre-flight 8–12 | **PASS** | 12 items `:191–:203` | — |
| 8 | Four core slots | **PASS** | all four present, canonical names | — |
| 9 | Renames | **PASS** | no extras, nothing to rename | — |
| 10 | Reference table parity + *when to read* | **PASS** | 4/4, phrased as occasions, with the train/use split spelled out inside the `lora-training.md` row | — |
| 11 | Train/use boundary + cross-pointer | **PASS** | `:277` "**Making** a LoRA (loading one is setup-and-workflows §7)"; `setup-and-workflows.md §7` is "Using and stacking LoRAs" | — |
| 12–13 | TOCs + numbering | **PASS** | 4/4. One cosmetic variance: `prompting-guide.md` TOC entry "Worked prompts (A–E)" vs heading "14. Worked prompts" | Align the TOC entry to the heading |
| 14 | Corpus band | **PASS** | 15,990 w — inside 10,000–16,000, with 10 words of headroom | Any further reference growth needs a demotion or a split |
| 15 | SKILL.md size/share | **PASS** | 5,152 w body, 34% | — |
| 16 | <500 lines | **PASS** | 277 | — |
| 17 | Each reference 700–3,500 | **PASS** | 2,006 / 2,346 / 3,065 / 3,178 | — |
| 18 | Padding | **PASS** | `## Seeds are not equal` `:134` is 79 words and changes the reader's first debugging move — the clearest example in the set of a short section earning its place | — |
| 19 | Duplication | **PASS** | 0 duplicated lines; the weighting mechanism is stated once in SKILL.md `:53` and expanded in `prompting-guide.md §7` | — |
| 20 | Silent-failure traps in SKILL.md | **PASS** | the mandatory `@` prefix, quality tags poisoning Aesthetic, SDXL-scale weights under-moving conditioning, the `llm_adapter_lr=0` rule, the two-KSampler frying — every one produces a plausible wrong result rather than an error, and every one is in SKILL.md | — |
| 21 | Three pillars | **PASS** | all three, each with a reference | — |
| 22 | Description | **PASS** | 241 w, folded `>`, gate bolded before the trigger list, "even obliquely:" verbatim, closing sweep with routing note | — |
| 23–25 | Two-bar + date line | **PASS** | `:245`, five elements, `**Facts dated 2026-08-22**` `:266`. Note the extra "**Settled since drafting, and deliberately no longer flagged**" paragraph at `:264` — not required by §6.3 but it is the right way to close out a revision round, and it prevents resolved items being re-flagged on the next pass. Worth proposing to §6.3 as an optional sixth element | — |
| 26 | Flagged/contested greppable | **PASS** | 25; each two-bar bullet carries its marker | — |
| 27–28 | Italic-paren / malformed | **PASS** | 0 / 0 | — |
| 29 | Orphan numbers / bare hedges | **PASS** | the 0.15–0.3 LLLite band, the ~6 GB floor, denoise ~0.3–0.45, the 768 px handoff — all attributed | — |
| 30 | Summarise-up hop | **PASS** | ratio **1.18** | — |
| 30a | §6.2.1 density band | **PASS** | 5.4/1k total, 1.59/1k watchlist (25 absolute — just inside the 24-absolute cap at the /1k limit, worth watching). **The author's cut from 55 `[official]` to 18 worked** and is what put this skill inside the band | — |
| 30b | Bare `[official]` | **FAIL (P3)** | 18 of 20 official markers are bare. Smaller than `scail-2`'s in both count and share of corpus, and the skill is inside the band regardless | Optional second pass: drop the bare ones whose claim is inside the roll-call at `:249`. Lands the skill near 4.3/1k |
| 31 | Marker syntax | **PASS** | one wrinkle — 4 bare `` `[community]` `` with no named source, which names nobody and is the community-tier equivalent of a bare hedge (§6.2). Suite-wide pre-existing: `sdxl` 10, `flux-2` 5, `z-image` 2 | Name the source or drop to prose |
| 32 | ≥1 flagged/contested in SKILL.md | **PASS** | 14 | — |
| 33–34 | Links | **PASS** | 0 bare sibling spans (the two `` `anima` `` spans are self-references), 0 escaping links | — |
| 35 | Eight image suite-table axes | **PASS** | `:208–:218` covers all eight — characters, LoRA ecosystem, typography, structural control, headline aesthetic axis (split across the "Anime and illustration" and "Photoreal" rows), commercial use, mixed-model pipelines, making it move | — |
| 36 | Bidirectionality | **FAIL (P2), in the sibling** | `character-lora-training:21` already links `[anima](../anima/)`, and `image-production-workflows:70` names Anima's VAE correctly. **`sdxl/SKILL.md:49` and `:259` still name Anima in plain bold** — correct while unpublished, now a dead reference | Reciprocal edit in `sdxl` — see **Recommended edits** #9 |
| 37 | Unpublished models | **PASS** | the 2.9B/3.8B forks are plain bold with "**not CircleStone releases**, experimental" as their status | — |
| 38 | Tables vs prose | **PASS** | the weighting mechanism at `:53` is correctly prose (a causal chain); the three-mechanism conditioning table at `:144` is correctly a table | — |
| 39 | Registered | **PASS** | `marketplace.json:35`, `README.md:23` | — |
| 40–41 | `freshness.json` | **PENDING** | not registered | Register `hot`; ~14 watchlist entries, comfortably sustainable |

---

## Depth ruling

**On `ltx-2-5`'s argument: two of the three grounds hold, and none of them holds for the *amount*.**
The finding stands. Below is what to demote and where.

### The grounds, taken one at a time

The parent brief reports three claimed justifications. **The skill itself claims only two** —
`SKILL.md:356`: "It runs past the suite's usual SKILL.md ceiling for two stated reasons." I grade
all three.

1. **"A licence that can rule the reader out." HOLDS, and strongly.** Four independent gates, and
   Attachment A ¶20 has no revenue floor at all — it bars any product competing with Lightricks'
   "commercial products or services", which includes Facetune and Photoleap, so the field-of-use
   surface is much wider than a video-tool reading suggests. Add an incorporated AUP whose
   sexually-explicit prohibition binds **local weights**, and derivative inheritance that makes
   publishing a permissively-licensed LTX LoRA impossible. This is the `minimax-h3` §7.1 precedent
   and it is at least as strong.
2. **"More task modes than the suite norm." HOLDS — and it is already paid for.** Twelve
   `ltx_pipelines` entry points against `wan-2-2`'s six. But measure what it actually costs:
   `## Task-mode selector` is **335 w** and `## Per-mode settings` is **512 w** — 847 words for
   twelve modes, against `wan-2-2` spending a comparable share on six. **This ground is genuine and
   it does not explain the overage, because the overage is not in these sections.** A justification
   licenses the content it names, not a global budget.
3. **"Capabilities the shipped templates do not expose." HOLDS, and it is the strongest of the
   three** — though the skill does not claim it. The inert-widget discovery (the dead
   `EmptyLTXVLatentVideo [768, 512, 97]`, the dead enhancer `PrimitiveBoolean [True]`, the FLF2V
   apparent-fps disagreement that is not a disagreement) is content no reader can get from the
   template and every reader will otherwise get wrong. It earns its 468 words.

**So: the argument is sound and the conclusion does not follow.** `minimax-h3` carries **three** of
§5.2's four grounds and is accepted at **7,022 w** of body. `ltx-2-5` carries **two** firmly (three
if you credit the one it omits) and sits at **8,053 w** — 1,031 words above the suite's accepted
high-water mark, set by a skill with a stronger claim. **The ceiling this argument licenses is
`minimax-h3`'s, not more.** Target ~7,100 w.

### What to demote, and where — ~925 words, five named places

None of these is in a section the justification names. Each is a §5.4 placement error, not a
length trim: *SKILL.md carries the decision; the reference carries what you need once you have
decided.*

| # | Demote | From | To | Words | Why it is placement, not trimming |
|---|---|---|---|---|---|
| **D1** | `### Running LTX-2.3 instead` — the 9-row install-shape table and the "Three things this skill cannot give you for 2.3" paragraph | `SKILL.md:126–:145` | `references/setup-and-workflows.md §2` ("Files, and the split-versus-monolith rule") | **~400** | This is 2.3's **install shape**, not the 2.3-vs-2.5 **decision** — `## Variant selector` already makes that decision in 724 words, and makes it well. §2 of the reference already owns the split-vs-monolith rule; this is its missing body. **Keep in SKILL.md:** three lines — monolith checkpoint, **Gemma 3 12B downloaded separately** (the one fact that decides whether a 2.3 install works), lattice unchanged — plus the pointer |
| **D2** | The IC-LoRA-crosses-the-version-line evidence chain: the three-artefact corroboration, the docs-page title argument, the 75-comment thread | `SKILL.md:60–:62` (blockquote) | `references/setup-and-workflows.md §6` ("Using LoRAs and IC-LoRAs") | **~180** | §6.6 is right that a dispute between named sources wants prose — but §5.4 puts the *evidence* in the reference and the *decision* in SKILL.md. The decision is two sentences: assume a 2.3 IC-LoRA works on 2.5 unless its listing says otherwise `[contested — vendor docs against vendor README]`; test a plain 2.3 LoRA at low strength first `[community — ArttTaku; single report]` |
| **D3** | The Hugging Face gating forensics — "16 of the 18 2.3 adapter repos are `gated: auto`… gates dating from **2026-07-26**, a fortnight *before* 2.5 shipped" | `SKILL.md:56` | `references/licence-and-derivatives.md §9` ("Gating, and what could not be reached") | **~60** | The date forensics is authorial evidence for a conclusion, not a reader action. §9 exists for exactly this. **Keep the rule:** "Do not plan around 2.3 as the ungated escape hatch — most 2.3 adapter repos are gated too" |
| **D4** | The fps → legal-whole-seconds table, and the "the lattice is safe on both 2.5 and 2.3" rebuttal paragraph | `SKILL.md:230`, `:241–:246` | `references/setup-and-workflows.md §3` | **~190** | The four lattice **rules** are silent-failure traps and must stay in SKILL.md (check 20 — do not touch them). The four-row worked-values table is a derivation, and §5.3's corollary is explicit: SKILL.md keeps the rule and the anchor number, the reference keeps the table. **Keep in SKILL.md:** `8k+1`, /32, fps ∈ {24, 25, 48, 50}, and two anchors — 121 frames = 5 s at 24 fps, 241 = 10 s. Note this **inverts** `setup-and-workflows.md:93`, which currently defers the worked values upward; edit both sides |
| **D5** | The methodology half of the "Read these templates as a graph" blockquote (check 19 duplication) and the whole of "**On this skill's length**" (check 18) | `SKILL.md:163`, `:356` | `:163` → collapse to its last sentence; `:356` → delete outright | **~95** | The template-methodology caveat is stated at near-full length in **both** `:163` and the two-bar hard-facts bar `:337`. One of them is the pointer, and §6.3 puts source-methodology in the two-bar section. The length note is a message to auditors — §5.3's test deletes it, and it is self-refuting besides |

**Net: 8,053 → ~7,128 w body, 41% → ~38% share.** Inside §5.2's percentage band, level with the
`minimax-h3` precedent, and every silent-failure trap still in SKILL.md.

### The corpus finding is separate, and the demotions do not fix it

Check 14 fails on 20,439 words against a 10,000–16,000 band. **Demoting moves words within the
corpus; it does not shrink it.** Three honest options, in preference order:

1. **Accept it as a §7 justified deviation, with the reasoning written down.** `ltx-2-5` is
   genuinely a **two-model** skill — 2.5 and 2.3 are different file layouts, different encoders,
   different adapter ecosystems and arguably different licence texts, and the skill argues
   convincingly at `:54` that the ecosystem is still on 2.3. No other skill in the suite carries two
   live models. Add `licence-and-derivatives.md` (1,954 w, the §7.1 precedent) and 20,439 stops
   looking anomalous.
2. **Note that §5.2's upper bound is empirically stale.** It was set against a seven-skill sample
   whose largest corpus was 15,306. `minimax-h3` has since been accepted at **18,098**. A band whose
   ceiling the suite has already overrun by 13% is describing the old sample, not the current one.
   This belongs to whoever owns §5 — I did not touch it.
3. **Split `prompting-guide.md`** (4,187 w, the only over-3,500 reference). I recommend **against**
   it: §12's "Multishot *and* a consistent character — the composed path" is the payoff of §4's
   multishot technique, and splitting them would separate a method from its worked application. The
   TOC escape hatch in §5.2 exists for this case and it is being used correctly.

**My ruling: option 1.** Record it in §7 as a justified deviation on the two-model ground, and let
§5.2's ceiling be revisited on its own schedule rather than by cutting a skill that is not padded.

### The other two

**`scail-2` and `anima` both pass check 15 without needing a justification** — 5,201 w / 36% and
5,152 w / 34%. `scail-2` is at the wall, though: **5,500 words including frontmatter is exactly
§5.2's absolute cap.** Anything added to that file from here needs a matching demotion.
`anima`'s corpus at 15,990 has **10 words of headroom** against the 16,000 ceiling — the same
constraint one level up.

---

## Marker calibration

### The band

Three limits, all per 1,000 words of the whole corpus (`SKILL.md` + `references/`). Now recorded in
`STANDARD.md §6.2.1`.

> **1. Total density: 2.5–7.0 markers per 1,000 words.**
> **2. Layer balance: SKILL.md density ≥ 0.6 × the same skill's `references/` density.**
> **3. Watchlist class (`[flagged]` + `[contested]` + `[pending release]`): ≤ 1.6 per 1,000 words
> *and* ≤ 24 per corpus, whichever binds first.**

### Where limit 3 comes from — the operational anchor

Check 40 requires every watchlist-class marker to map to a `freshness.json` watchlist entry.
Observed today across the ten registered skills:

| | entries | watchlist-class markers | markers per entry |
|---|---|---|---|
| `minimax-h3` | 16 | 19 | 1.19 |
| `character-lora-training` | 16 | 11 | 0.69 |
| `krea-2` | 15 | 10 | 0.67 |
| `wan-2-2` | 13 | 8 | 0.62 |
| `flux-2` | 11 | 8 | 0.73 |
| `ideogram-4` | 10 | 19 | 1.90 |
| `z-image` | 9 | 8 | 0.89 |
| `sdxl` | 8 | 11 | 1.38 |
| `comfyui-on-runpod` | 6 | 0 | — |
| `image-production-workflows` | 6 | 5 | 0.83 |

Entries run **6–16**, median 10.5; the marker-to-entry ratio runs **0.6–1.9**, because one claim is
usually marked in both SKILL.md and its reference. **A sustainable ceiling of 16 entries is
therefore ~24 markers**, which on a 15,000-word corpus is 1.6/1k.

This is the limit that decides the others, and it is not stylistic. `ltx-2-5` at **56** watchlist
markers — every one a distinct claim, none repeated — implies roughly **30 independent claims** for
a `hot`-tier daily check to re-verify per pass. That is nearly double the observed maximum, and the
failure mode is not noisy: the protocol quietly stops keeping up and the skill's flags become
decorative. **When limit 3 and limit 1 disagree, limit 3 wins.**

### How much of the spread is real? Less than the story predicts

The intuition — a thinly-documented three-week-old model needs more hedging than SDXL — is
**weakly supported at best**, and the corpus contradicts it in the obvious places:

- **Freshness tier does not predict density.** `sdxl` — three years old, `stable` tier — carries
  **2.9** community markers/1k. `minimax-h3` — three weeks old, `hot` — carries **2.8**.
  `ideogram-4`, also `hot`, carries **0.6**. If age drove marking, that ordering would be impossible.
- **What predicts density is whether the author marked hard facts.** `[official]` density spans
  **0.13/1k** (`z-image`) to **5.1/1k** (`scail-2`) — a **39× spread** on a claim class §6.2 already
  calls optional and sparing. `[community]` density spans 0.6 to 7.4, a 12× spread.
- Strip the redundant `[official]`s and the corpus range collapses from 0–14.8 to roughly **2–8**.

**Verdict: read roughly a third of the spread as real** — `scail-2` genuinely rests on nine named
practitioners with **zero** vendor coverage of its craft, and says so in its own two-bar section
("not the vendor docs, which cover none of it"). A high **community** share is defensible there. The
other two-thirds is `[official]` inflation plus repeat-marking of one source.

### Where marking stops helping — quantified, by tier

The `anima` blind review found the tell: not the total, but the **share of markers carrying no
discriminating information**. Applying that test to the three named skills gives three *different*
diagnoses, which is why a single count would have been the wrong instrument.

**Bare `[official]` — markers with no artefact in the payload.** These name nobody; they are the
bracket form of the "bare epistemic hedge" §6.2 forbids. 91 suite-wide, and concentrated:

| Skill | bare `[official]` | of total official | share |
|---|---|---|---|
| `scail-2` | **54** | 77 | **70%** |
| `anima` | 18 | 20 | 90% |
| `krea-2` | 8 | 50 | 16% |
| `wan-2-2` | 3 | 12 | 25% |
| `ideogram-4` / `flux-2` / `image-production-workflows` | 2 each | — | — |
| `ltx-2-5` | **1** | 18 | **6%** |
| `sdxl` / `z-image` / `character-lora-training` / `minimax-h3` | 0–1 | — | — |

Every `scail-2` instance sampled (`SKILL.md:27`, `:32`, `:74`, `:82`, `:103`, `:109`, `:146`, `:150`,
`:154`) marks a fact its **own two-bar hard-facts roll-call already declares** at `:294`. §6.2
exempts precisely these.

**Repeat-marking — instances per distinct payload.** Inside the band the suite runs **1.1–1.8**:

| Skill | community markers | distinct payloads | reuse | most-repeated |
|---|---|---|---|---|
| `scail-2` | 111 | 33 | **3.4** | `[community — nsfwVariant]` **20×**, `[community — External_Trainer_213]` **16×** |
| `minimax-h3` | 51 | 21 | 2.4 | `[community — re-verify]` 7× |
| `flux-2` | 18 | 10 | 1.8 | — |
| `krea-2` | 85 | 53 | 1.6 | 8× |
| `ltx-2-5` | 66 | 41 | 1.6 | 6× |
| `sdxl` | 44 | 28 | 1.6 | — |
| `anima` | 40 | 29 | 1.4 | — |
| `z-image` | 25 | 23 | 1.1 | — |

A marker appearing twenty times has stopped being a contrast signal and become page furniture.
**Reuse above ~2.0 is the diagnostic, and the fix is scope, not deletion** — §6.2 and §7.16 already
bless heading-scoped and table-header-scoped markers for exactly this.

**The three diagnoses, then:**

- **`scail-2` has the `anima` problem, twice over.** 70% bare `[official]` *and* 3.4× reuse. Both
  repairs are mechanical and lossless: bare-marker deletion takes it 14.8 → ~11.2; collapsing the
  36 `nsfwVariant` / `External_Trainer_213` repeats to section scope takes it to ~7.5.
- **`krea-2` does *not* have it, and its overage is milder than the raw 9.4/1k suggests.** Only 8 of
  its 50 official markers are bare, and its community layer is the healthiest in the suite (53
  distinct payloads, 1.6× reuse). Its excess is 42 payloaded `[official — …]` at 3.2/1k against a
  suite median of ~0.9 — real, but a smaller and lower-priority diff than `scail-2`'s.
- **`ltx-2-5` does *not* have it either — this is the important negative result.** One bare
  `[official]`; official density 0.88/1k, *below* the suite median; reuse 1.6×, normal. Its overage
  is entirely watchlist class — 31 `[flagged]` + 23 `[contested]` + 2 `[pending release]`, every one
  a distinct claim about a model eleven days old. **That is honest marking, and it is still
  unmaintainable.** It fails limit 3 rather than limits 1 or 2, and the repair is correspondingly
  different: merge and relocate, never delete.
- **`anima`'s cut worked.** 55 `[official]` → 18 is what put it inside the band at 5.4/1k. Its
  remaining 18 bare `[official]`s are an optional P3 pass worth ~1.1/1k.

### Under-marking — and the layer where it lives

**No skill is under 2.5/1k except `flux-2` (2.2) and `z-image` (2.4)**, both marginal. The real
under-marking is not in the corpus total but in **limit 2** — the SKILL.md-to-references ratio,
which is §6.2's "summarise-up hop" made numeric. It was derived independently and reproduces §6.2's
hand-diagnosis exactly:

| Skill | ratio | §6.2 already names it for the summarise-up hop? |
|---|---|---|
| `image-production-workflows` | **0.30** | (not named, but fails hardest — 1.8/1k in SKILL.md against 6.1 in references) |
| `z-image` | **0.39** | yes — the ×1.7/×2 ladder, denoise 0.23, the Turbo LoRA sweep |
| `sdxl` | **0.48** | yes — the five-rung denoise ladder |
| `flux-2` | **0.57** | yes |
| `ideogram-4` | **0.58** | yes |
| — floor — | **0.60** | |
| `scail-2` | 1.04 | |
| `anima` | 1.18 | |
| `krea-2` | 1.21 | |
| `minimax-h3` | 1.29 | |
| `ltx-2-5` | 1.68 | |
| `character-lora-training` | 1.70 | |
| `wan-2-2` | 2.55 | |

That four of the five failures are the four skills §6.2 diagnoses by hand is why I trust the ratio
as a check rather than a coincidence. `image-production-workflows` at 0.30 is a **new** finding the
prose diagnosis missed.

### Per-skill verdicts

| Skill | total/1k | ratio | watch/1k | watch N | verdict |
|---|---|---|---|---|---|
| `scail-2` | **14.8** | 1.04 | **2.03** | **30** | **over on limits 1 and 3.** Largest diff in the suite |
| `krea-2` | **9.4** | 1.21 | 0.65 | 10 | **over on limit 1.** `[official]` inflation only |
| `ltx-2-5` | 7.0 | 1.68 | **2.78** | **56** | at ceiling on 1; **over on 3 by 2.3×.** Merge, don't delete |
| `anima` | 5.4 | 1.18 | 1.59 | 25 | **in band** — watch the 24-absolute cap |
| `minimax-h3` | 4.4 | 1.29 | 1.07 | 19 | in band |
| `image-production-workflows` | 4.2 | **0.30** | 0.70 | 5 | **over on limit 2** — worst ratio in the suite |
| `sdxl` | 3.9 | **0.48** | 0.74 | 11 | over on 2 |
| `wan-2-2` | 3.6 | 2.55 | 0.73 | 8 | in band |
| `ideogram-4` | 3.5 | **0.58** | 1.41 | 19 | over on 2 |
| `character-lora-training` | 2.8 | 1.70 | 0.94 | 11 | in band |
| `z-image` | **2.4** | **0.39** | 0.54 | 8 | **under on 1**, over on 2 |
| `flux-2` | **2.2** | **0.57** | 0.56 | 8 | **under on 1**, over on 2 |
| `comfyui-on-runpod` | 0.0 | — | 0.00 | 0 | **exempt** — §6.2 single-source, §7.8 |

### The census correction, verified

`STANDARD.md §6.2` claimed **33 italic-parenthetical markers across `sdxl` and `z-image`**, and
recorded **0 for `flux-2`**. Re-counted mechanically against the pre-conversion tree
(`git show HEAD:<file>` per file, `grep -o '\*([A-Za-z][^)]*)\*'` filtered to the tier words):

| Skill | actual, pre-conversion | census said |
|---|---|---|
| `flux-2` | **16** | **0** |
| `z-image` | **16** | ~18 |
| `image-production-workflows` | **14** | **0** |
| `sdxl` | **9** | ~15 |
| **total** | **55 across four skills** | 33 across two |

**`flux-2` was scored 0 for a skill the section was quoting.** Two of §6.2's three worked conversion
examples are verbatim `flux-2` lines: `*(flagged — no DiT block map yet)*` is
`flux-2/references/characters.md:62`, and the Khanykov01 example is `characters.md:49`.

The correction does not change the ruling — the form is retired either way. It changes two things
that follow from it, and both are now written into §6.2: the diff was **1.7× the budgeted size**,
and it was **not** confined to the "older cohort" the section blames. `flux-2` and
`image-production-workflows` were running the undeclared second system too, which means the form
was **spreading by imitation** rather than surviving in two unmaintained corners — a materially
stronger argument for retiring it, and a reason to keep check 27 as a permanent regression test.

**Conversion status: complete.** Verified over the whole working tree —
`grep -rIo --include='*.md' '\*([A-Za-z][^)]*)\*' skills/ | grep -ic 'community\|official\|flagged\|contested\|named'`
returns **0**. Seven inline-label forms survive (check 27's second half, P3): `flux-2/references/setup-and-workflows.md`
lines 13, 22, 29, 30, 120; `flux-2/references/prompting-guide.md:3`; `ideogram-4/SKILL.md:36`.
`z-image/references/setup-and-workflows.md:222` carries a `(official)` source line that reads as
prose — judge it, do not convert it mechanically.

---

## Recommended edits

Ordered so each is independently applicable and verifiable. Renames and content edits are kept
apart per §8's emitting rule. **P1 first**, then by leverage.

**None of these blocks publication.** All three skills are conformant enough to ship today.

### Marker repairs — the largest diffs, and the only P2s that affect the reader

1. **[P2] `scail-2` — delete redundant bare `[official]` markers.** 54 instances. For each, check
   whether its claim appears in the two-bar hard-facts roll-call at `SKILL.md:294`; if yes, delete
   the marker (§6.2 exempts it); if no, give it its artefact — `[official — PR #14373 diff]`,
   `[official — docs.comfy.org/tutorials/video/zai/scail2]`, `[official — arXiv 2606.10804v3 §4.1]`.
   Start at `SKILL.md:27, :32, :74, :82, :103, :109, :146, :150, :154`. **Effect: 14.8 → ~11.2/1k.**

2. **[P2] `scail-2` — collapse repeat markers to scope.** `[community — nsfwVariant]` appears 20×
   and `[community — External_Trainer_213]` 16×. Where one of them governs a table, a `###`
   subsection or a column, use the table-header-scoped or heading-scoped form (§6.2, §7.16) instead
   of repeating down the rows. Lossless. **Effect: ~11.2 → ~7.5/1k, inside the band.**

3. **[P2] `ltx-2-5` — bring the watchlist class under limit 3.** 56 → ≤24. **Do not delete
   `[flagged]` markers.** Two moves, in order: (a) **merge sibling flags that resolve together** —
   the two-bar list at `SKILL.md:343–:355` already bundles several into single bullets, so make the
   markers match the bundling (the 2.3-licence question, the ¶18 scope question and the in-repo
   `LICENSE` question are one licence-resolution event; the `ExtendPipeline` and diffusers flags are
   one "what ships next" event); (b) **push separable flags down** into the reference that owns the
   claim, so SKILL.md carries the claim and the reference carries the flag — the trainer
   compression-factor flag belongs in `lora-training.md §8` ("What is not known"), the gating and
   paid-licence flags in `licence-and-derivatives.md §9`. Target ~18 watchlist entries.

4. **[P2] `krea-2` — thin the payloaded `[official — …]` layer.** 42 instances at 3.2/1k against a
   suite median of ~0.9. Same test as #1 against `krea-2`'s own roll-call. Lower priority than
   `scail-2`: its community layer is healthy and its reuse factor is normal.

5. **[P2] Repair limit-2 failures in the older cohort.** `image-production-workflows` (ratio 0.30),
   `z-image` (0.39), `sdxl` (0.48), `flux-2` (0.57), `ideogram-4` (0.58). This is §6.2's existing
   summarise-up finding with a number attached, and §6.2 already names the specific passages for
   `z-image` and `sdxl`. **`image-production-workflows` is new** — 1.8/1k in SKILL.md against 6.1 in
   its references, the worst gap in the suite, and it is the hub skill every other skill links into.

### `ltx-2-5` depth — apply as one changeset, verify against §5.2

6. **[P2] Demotions D1–D5** exactly as tabled in **Depth ruling** — ~925 words, 8,053 → ~7,128.
   D4 requires editing **both** sides: `setup-and-workflows.md:93` currently defers the worked fps
   values upward to SKILL.md, and that deferral inverts when the table moves down.

7. **[P2] Record the corpus size as a §7 justified deviation.** `ltx-2-5` at 20,439 w is the suite's
   only genuinely **two-model** skill. Write the reasoning into §7 rather than cutting a skill that
   is not padded. Separately, flag to whoever owns §5 that §5.2's 16,000 ceiling was set against a
   sample whose largest corpus was 15,306 and that `minimax-h3` has since been accepted at 18,098.

### Structural residue from the revision rounds — small, mechanical

8. **[P3] `scail-2/SKILL.md:13`** — promote the orphan `### Its relationship to Wan 2.1 runs at
   three levels` to `##`. The placement is right; only the heading level is wrong.

9. **[P2] Reciprocal links for the three now-published skills** (check 33 / 36). Both are in
   siblings, not in the three new skills:
   - `sdxl/SKILL.md:49` and `:259` — **Anima** → ``[`anima`](../anima/)``
   - `wan-2-2/SKILL.md:174, :178, :180, :251` — **SCAIL-2** → ``[`scail-2`](../scail-2/)``

   `minimax-h3:319` and `image-production-workflows:135` are already converted. `STANDARD.md §7.15`
   and §6.5's unpublished-models list have been updated to match.

10. **[P3] `scail-2`** — the duplicated failure row at `SKILL.md:219` / `references/characters.md:162`.
    Keep the SKILL.md copy; in `characters.md` replace it with a pointer or re-angle it to the
    identity-specific framing that file owns.

11. **[P3] `scail-2/SKILL.md:158`** — rename `## Signature quality — it tracks, and then it
    embellishes` to `## It tracks, and then it embellishes`. §2.7 wants the trait, not the template
    word; the clause after the dash is already correct.

12. **[P3] `anima/SKILL.md:13`** — insert the missing `---` rule before `## Variant selector`.
    13 rules for 14 sections; every other boundary has one.

13. **[P3] `anima/references/prompting-guide.md`** — TOC entry "Worked prompts (A–E)" vs heading
    "14. Worked prompts". Align the TOC to the heading.

14. **[P3] `ltx-2-5/SKILL.md:356`** — delete "**On this skill's length**". Covered by D5; listed
    separately because it can be applied alone.

15. **[P3] `anima`** — optional second `[official]` pass: 18 of 20 official markers are bare. Same
    test as #1. **Effect: 5.4 → ~4.3/1k.** The skill is already in band; this is polish.

16. **[P3] Bare `` `[community]` `` with no named source** — `sdxl` 10, `flux-2` 5, `anima` 4,
    `z-image` 2. Names nobody; the community-tier equivalent of a bare hedge (§6.2). Name the source
    or drop to prose.

17. **[P3] Inline-label residue** (check 27's second half) — seven instances listed in
    §6.2 and above. Mechanical except `z-image/references/setup-and-workflows.md:222`, which is prose.

### Registration

18. **[P1] Register all three in `freshness.json`** — `hot` tier for all three (all under three
    months old, all with live unresolved flags). **Another agent holds the file; this was read, not
    written.** Watchlist sizes after the limit-3 repairs: `ltx-2-5` ~18, `scail-2` ~18, `anima` ~14.
    Do **not** transcribe `ltx-2-5`'s 56 markers into 30 entries — that is the failure limit 3
    exists to prevent, and check 40 now says so.

### Already applied to `STANDARD.md` by this audit

- **§6.2** — census corrected (flux-2 0 → 16; 33-across-two → 55-across-four), with the reasoning
  that depends on it rewritten; conversion recorded as complete and verified at 0 remaining;
  surviving inline-label forms enumerated.
- **§6.2.1** — new section: the three-limit calibration band, its derivation from the
  `freshness.json` watchlist constraint, the thirteen-skill census, the reuse-factor diagnostic, and
  the repair order (bare `[official]` → collapse to scope → merge flags; never "delete markers").
- **§7.14** — amended: counts still must not be normalised, but the age-drives-density premise is
  not supported by the corpus, and density is now banded.
- **§7.15 and §6.5** — the unpublished-models clause updated now that all three have shipped, with
  the two remaining unlinked sibling mentions named.
- **Rubric** — new checks **30a** (density band, all three limits) and **30b** (bare `[official]`
  audit); check 27 re-scoped as a regression test; check 40 given the ~16-entry ceiling and a
  pointer to limit 3.
