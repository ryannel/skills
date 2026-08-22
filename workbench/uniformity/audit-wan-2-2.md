# Audit: `skills/generative-media/wan-2-2/` — against `workbench/uniformity/STANDARD.md`

Audited 2026-08-22. Skill: video, MODEL type (§2 shape applies). Corpus: SKILL.md 4,454 words /
290 lines; references 5,923 → now 5,923 words unchanged, total corpus **10,377 words** (SKILL.md
grew from the 2026-08-22 SCAIL-2 addition; total still 10,000–16,000, in range).

Format per finding: **check id — verdict — evidence (path:line, quote) — fix**.

---

## Blocking

**[Check: SCAIL-2 content, §8 rubric checks 1/24/26/28/29 combined] — FAIL — the worst-class
defect: incomplete/misleading attribution plus a now-false `[flagged]` marker, plus wrong scope
for a skill being split off.**

Evidence: `SKILL.md:162-174`, the `### SCAIL-2 — the Wan-family model that took over character
replacement` subsection.

What's wrong, itemized against `workbench/scail-2/research-primary.md`:

1. **Maker never named, and the framing implies Alibaba.** The heading calls it "the Wan-family
   model" and the lede says "part of the Wan ecosystem" — with no lab named anywhere in the
   subsection. A reader infers Alibaba/PAI (the same inference the section makes correctly for Fun
   and VACE two paragraphs earlier). Primary source: **zai-org (Z.ai / Zhipu AI)** — a different
   lab — is the maker (`research-primary.md` "Identity & lineage").
2. **Stale `[flagged — re-verify]` on a now-confirmed fact**, and it's malformed to boot — a
   bracket marker nested inside another bracket marker (also **check 28 FAIL**, the exact pattern
   STANDARD.md §6.2 names as a known suite-wide bug in this file): `` `[community — 2026-08;
   architecture lineage stated by users as "Wan SCAIL-2" and Wan 2.1-based, `[flagged — re-verify]`
   against a primary source before asserting it]` ``. The `sat-scail2` README's own
   Acknowledgements section states verbatim that the implementation "is built upon the foundation
   of Wan 2.1" — this is settled, not inferred, and citable as `[official]`.
3. **SAM3 tracking undersold as unverified community lore.** It's officially confirmed: the
   ComfyUI docs tutorial names `sam3_video_object` / `sam3_image_object` inputs feeding
   `SCAIL2ColoredMask`.
4. **No licence note at all.** Split licence: GitHub code **Apache 2.0**, Hugging Face weights
   card frontmatter **MIT**. Both permissive, but the split is worth a line per house style.
5. **ComfyUI node name absent.** It's `WanSCAILToVideo` — confirms the tooling-level lineage and
   is exactly the kind of concrete, greppable fact this suite's style favors.
6. **Bernini-R's lineage is unstated.** It's confirmed **ByteDance**, built on **Wan 2.2** (not
   2.1) — a different lab and a different Wan base than SCAIL-2. Currently the text just calls it
   "a second Wan-family reference-video-to-video model" with no attribution at all.
7. **Wrong scope, full stop.** A standalone `scail-2` skill is being authored in parallel from
   this same research file. Per STANDARD.md's own reasoning (this is structurally the Bernini-R
   case, not the Fun/VACE case — different lab, own paper, own licence, own node family), this
   subsection should never have carried the full ecosystem inventory, the "why it wins the swap
   job" craft paragraph, or the first-frame-editing technique. Once `scail-2` exists, this is
   duplicated content two places will need to keep in sync.

**Fix — replace `SKILL.md:162-174` in full with:**

```markdown
### SCAIL-2 and Bernini-R — Wan-derived, different labs

Two models share Wan's architecture but are not part of this skill and are not Alibaba releases.
**SCAIL-2** is made by **zai-org (Z.ai / Zhipu AI)** — a different lab from Alibaba — and is
genuinely built on **Wan 2.1**: the `sat-scail2` README's Acknowledgements section states the
implementation "is built upon the foundation of Wan 2.1" `[official — zai-org/SCAIL-2 README]`.
It does reference-image + driving-video character animation and replacement, with officially
confirmed **SAM3-based identity tracking** and the ComfyUI node `WanSCAILToVideo`. Licence is
split: **Apache 2.0** for the GitHub code, **MIT** on the Hugging Face weights card — both
permissive. It has displaced Wan Animate for character-replacement work in community practice.
**Bernini-R** is a separate model doing the same reference-driven video-editing job — **ByteDance**,
built on **Wan 2.2** (not 2.1).

Full coverage — architecture, licence detail, the mask-conditioning contract, the reference-prep
craft that decides whether either one works, and ecosystem tooling: [`scail-2`](../scail-2/).
```

(~115 words vs. the current ~520 — cut the "why it wins the swap job" paragraph, the
first-frame-editing craft paragraph, and the full community-tooling inventory; all of it belongs
in the new `scail-2` skill, which `research-primary.md` already contains the sourcing for.)

**Also update the suite table**, `SKILL.md:243`:

```
| **Replacing a person in existing footage, following their motion exactly** | Animate does it; **SCAIL-2** (zai-org, Wan 2.1-derived) **has displaced it** in community practice | [`scail-2`](../scail-2/) — reference-image + driving-video replacement with SAM3 tracking. [`minimax-h3`](../minimax-h3/) can do it *approximately* and adds audio |
```

Note: the `../scail-2/` links will 404 until that skill merges — sequence this repair after (or in
the same commit as) `scail-2` publishing, not before.

**Companion fix (freshness.json, not this skill's files but load-bearing on the correction):**
`freshness.json`'s `wan-2-2.watchlist` entry `scail2-lineage` (currently: "No primary source read
... Confirm the base architecture, licence and who publishes it before the claim hardens") is now
answered and stale — remove it, or narrow it to the one thing `research-primary.md` itself flags
as unresolved (why the HF card says MIT while GitHub says Apache 2.0). Update `open_findings`
entry `wan-scail2-uncovered` from "PARTIALLY RESOLVED" to reflect the shrink-to-pointer fix and
the new `scail-2` skill's existence.

---

**[Check 1] — FAIL — no `## Signature-quality technique` section (§2 row 7, MANDATORY, video
requires a named "default motion character").**

Evidence: full `## ` heading scan of `SKILL.md` shows no such section. The one fact that belongs
there — Wan 2.2's default is to *add* camera drift/motion rather than hold still — exists only as
a single clause in `references/prompting-guide.md:77` ("The default behaviour is to add drift...")
and a fragment inside `## Prompting Wan 2.2` (`SKILL.md:140`, "because the model's default is to
add drift"). Per §5.3 a pointer can satisfy a pillar, but there's no heading at all naming this as
the model's defining aesthetic/motion trait — it reads as a prompting tip, not the mandatory
signature-technique slot.

Fix: add a short section between `## Prompting Wan 2.2` and `## Motion, camera and structural
control` (`SKILL.md` around line 146), e.g.:

```markdown
## The default is motion, not stillness

Wan 2.2 adds camera drift and subject motion unless told not to — the opposite failure from most
image-derived video prompts, which assume a still frame unless motion is requested. State the
camera explicitly, including `static shot` / `fixed camera` when you want none; an unstated camera
is not a still one. Full vocabulary: `references/prompting-guide.md`.
```

---

**[Check 3] — FAIL — heading drift: `## Licence and known limitations` should read
`## Licence & limitations`.**

Evidence: `SKILL.md:252`. STANDARD.md §2 row 13 names the ampersand form canonical (4 skills to 2)
and explicitly lists `wan-2-2` as one of the two drifted skills.

Fix: rename the heading. Also update `freshness.json`, which quotes the old heading text verbatim
in three `where` fields for `wan-2-2` (lines ~528, ~535, ~630) — update those strings too so
check 41 (watchlist references still resolve) stays true after the rename.

---

**[Check 25] — FAIL — no `Facts dated YYYY-MM-DD` line anywhere; only a model-release date is
recorded, which is a different fact.**

Evidence: two-bar section `SKILL.md:266-279` ends at the contested-points bullet list with no
date paragraph. `SKILL.md:256` has `**Release timeline:** Wan 2.2 shipped **August 2025**...` —
that's when the *model* shipped, not when this *skill's claims* were last checked. STANDARD.md
§6.4 names `wan-2-2` explicitly as one of three skills with only a release date.

Fix: append as the final paragraph of the two-bar section (after the contested-points list, before
`## Reference files`):

```markdown
**Facts dated 2026-08-13**; community craft refreshed 2026-08-22. Template numbers, quant
filenames and speed-LoRA versions move fastest — re-verify before relying on them.
```

(Dates taken from `freshness.json`'s `wan-2-2.last_checked`/history; confirm the hard-facts date
against the actual last full verification pass rather than the craft-refresh date, since the two
now differ.)

---

## Standard

**[Check 24] — FAIL — craft roll-call in the two-bar section names no actual authors, only a
generic descriptor.**

Evidence: `SKILL.md:272`, "**The authoritative source here is the community** — named trainers and
workflow authors who have run this model thousands of times — not the model card..." No names
appear. §6.3 item 3 requires the roll-call to name the sources. The skill *does* name authors
elsewhere (wan27.org, blackmixture, LastCrusaderVHS, musubi-tuner discussion contributors) — they
just aren't surfaced at this required summary point.

Fix: replace "named trainers and workflow authors" with the actual names already used in the
skill's markers, e.g. "named trainers and workflow authors — blackmixture, LastCrusaderVHS, the
musubi-tuner training community, wan27.org's guide authors — who have run this model thousands of
times."

---

**[Check 11] — FAIL — train/use cross-pointer is one-directional.**

Evidence: `references/lora-training.md:6` correctly points to `setup-and-workflows.md` for
loading/stacking ("*Making* a LoRA. Loading and stacking is in `setup-and-workflows.md`..."), but
`grep -n lora-training references/setup-and-workflows.md` returns nothing — no reciprocal pointer
back.

Fix: add one line near `setup-and-workflows.md`'s LoRA-loading/speed-LoRA section (around line 60,
next to the `wan2.2_..._lightx2v...` file table): "Making a LoRA — hyperparameters, dataset
construction, the two-expert training question: [`references/lora-training.md`](./lora-training.md)."

---

**[Check 35/36] — FAIL — suite table missing the "LoRA ecosystem and training maturity" axis
required for video skills (§6.5 axis 5), and the reciprocal link from `minimax-h3` is therefore
one-way.**

Evidence: `SKILL.md:238-248` (the "Where Wan 2.2 sits in the suite" table) has no such row.
`minimax-h3/SKILL.md:383` already carries the return row: "LoRA ecosystem and training maturity |
Very young... | [`wan-2-2`](../wan-2-2/), or [`sdxl`](../sdxl/) on the image side" — pointing at
wan-2-2 for exactly the axis wan-2-2's own table omits.

Fix: add a row to `SKILL.md`'s suite table, e.g.: `| LoRA ecosystem and training maturity |
**Mature** — two-expert training is a settled, documented recipe (musubi-tuner) | — |`.

---

**[Staleness / §5.3, beyond-rubric item 2] — FAIL — the 2026-08-22 "no longer the default open
video model" repositioning is not coherent skill-wide; it stops at the licence section.**

Evidence: `SKILL.md:258` (the repositioning: "It is no longer the default open video model in
community practice — **MiniMax H3** took that position..."). But `references/motion-and-camera.md:3`
still opens with: "Wan 2.2's control stack is the strongest in the open video ecosystem, and it is
the main reason to choose it over HunyuanVideo or LTX." — unqualified superlative framing, no
mention of MiniMax H3 at all, comparing against a stale competitor set (HunyuanVideo/LTX rather
than MiniMax H3/LTX-2.5). A reader who opens the reference file directly (which the "Motion, camera
and structural control" section explicitly routes them to) gets the pre-repositioning framing.

Note: the intro paragraph's separate claim ("Wan 2.2 is the current open-weights frontier, and may
be the last," `SKILL.md:13`) is internally consistent — it's scoped to *Wan-family* versions
(2.5/2.6/2.7/3.0), not a claim about the whole video landscape, and doesn't contradict the
repositioning. Only `motion-and-camera.md` is out of step.

Fix: reword `references/motion-and-camera.md:3`, e.g.: "Wan 2.2's control stack — Fun Camera, Fun
Control, VACE — is the deepest in the open ecosystem, and the reason to reach for Wan even where
MiniMax H3 or LTX-2.5 win on raw quality or native audio."

---

**[Check 37] — FAIL — LTX-2.5 named three times as an unpublished/uncovered model but never
carries the required status word.**

Evidence: `SKILL.md:244` ("LTX-2.5 also does native audio"), `SKILL.md:258` ("with LTX-2.5 the
other pole"), `references/motion-and-camera.md:77` ("LTX-2.5 does the same"). Compare
`minimax-h3/SKILL.md:378`, which correctly appends "(gated licence, unverified here)" every time
it names LTX-2.5. §6.5 requires the status word on every unpublished-model mention.

Fix: append the same qualifier used in `minimax-h3` at each of the three sites, e.g. "LTX-2.5 also
does native audio (gated licence, unverified here)." Once the parallel `ltx-2-5` skill ships,
convert all three mentions to `[`ltx-2-5`](../ltx-2-5/)` links and add the reciprocal row there.

---

**[Check 22] — FAIL — frontmatter description's trigger list omits "licensing," one of the §6.1
minimum-coverage triggers.**

Evidence: `SKILL.md:4`, full description scanned — covers variant/size, setup, prompts,
steps/CFG, speed LoRAs, I2V handoff, characters, LoRA training, motion/camera, production
pipeline, debugging — no licence/commercial-use trigger phrase anywhere.

Fix: insert a clause into the trigger list, e.g. "...confirming Wan 2.2's Apache-2.0 licence covers
a commercial or territory-restricted use case where a sibling model's licence would not...".

---

**[Check 41] — FAIL — freshness.json bookkeeping not yet updated for this pass's findings**
(companion to the Blocking SCAIL-2 fix above; listed here at its real P2 severity). Update the
`scail2-lineage` watchlist entry and the `wan-scail2-uncovered` open-finding status once the
SCAIL-2 rewrite lands, and fix the three `where` fields that quote the old `Licence and known
limitations` heading text (see Check 3 above).

---

## Cosmetic

**[Check 19] — minor, not a full duplication.** `SKILL.md`'s "Per-mode settings" table
(`SKILL.md:100-115`, steps 20/4, CFG 3.5-4.0/1.0, shift 8/5) and
`references/setup-and-workflows.md:49-55` carry the same headline numbers. Not flagged as a
FAIL because the reference adds real derivation (widget order, the `steps`-is-total-schedule
gotcha) rather than just repeating the table — but if trimming SKILL.md is ever on the table,
this is where the rule/anchor-number split from §5.3 applies.

---

## PASS / N-A ledger — remaining §8 checks

| Check | Verdict | Note |
|---|---|---|
| 2 | PASS | Section order matches §2 exactly (one-rule before setup, etc.) |
| 4 | PASS | Task-mode selector has "Use when…" column, all modes covered |
| 5 | PASS | Failure-modes table: 9 data rows (≥8), every cause cell states a mechanism |
| 6 | PASS | Per-mode `###` blocks present, distilled/undistilled kept apart, frames/fps/shift included |
| 7 | PASS | Pre-flight checklist: 11 numbered items |
| 8 | PASS | All four §4.1 core slots present under canonical names |
| 9 | PASS | No renames owed — `motion-and-camera.md` is already the canonical extra per §4.3 |
| 10 | PASS | Reference-files table: 5 rows, 5 files, each states *when to read it* |
| 12 | N/A | No reference file ≥2,000 words — TOC not required |
| 13 | PASS | Numbered `## N.` headings already present in `lora-training.md`, `prompting-guide.md`, `setup-and-workflows.md` |
| 14 | PASS | Total corpus 10,377 words, inside 10,000–16,000 |
| 15 | JUSTIFIED | SKILL.md 4,454w = 42.9% of corpus, nominally above the 25–40% band, but STANDARD.md §5.2 explicitly grandfathers wan-2-2's ~42% share as "inside tolerance, needs no repair." Absolute word count (4,454) is inside the 2,800–5,500 floor/ceiling |
| 16 | PASS | SKILL.md 290 lines, well under the 500-line cap |
| 17 | PASS | All 5 reference files between 871–1,483 words, inside 700–3,500 |
| 18 | PASS | No section identified as pure padding |
| 20 | PASS | All silent-failure traps (VAE swap, `return_with_leftover_noise`, Chinese negative) live in SKILL.md |
| 21 | PASS | Characters, LoRA training, production pipelines all covered or routed |
| 23 | PASS | Two-bar heading byte-identical, correctly positioned before Reference files |
| 26 | PASS* | Every flagged/contested claim is a bracket marker; *the one SCAIL-2 instance is malformed — see Blocking |
| 27 | PASS | No italic-parenthetical markers found |
| 28 | FAIL | Folded into the Blocking SCAIL-2 finding — nested marker at `SKILL.md:164` |
| 29 | PASS | No unmarked orphan numbers found beyond the SCAIL-2 section (which is being cut) |
| 30 | PASS | Elsewhere in the skill, SKILL.md ladders/settings carry the same markers as their reference sections |
| 31 | PASS | Marker syntax canonical throughout (aside from the malformed SCAIL-2 instance) |
| 32 | PASS | Multiple `[flagged]`/`[contested]` markers present in SKILL.md |
| 33 | PASS | Every sibling mention is a proper `[`name`](../name/)` link — checked all occurrences in SKILL.md and all 5 references |
| 34 | PASS | No link reaches above `skills/generative-media/` |
| 38 | PASS | Tables used for parallel structure, prose for mechanism; no misused two-row tables |
| 39 | PASS | Registered in `.claude-plugin/marketplace.json:33` and `README.md:23` |
| 40 | PASS | freshness.json watchlist covers all flagged/contested claims (scail2-lineage entry is stale content, not a missing entry — see Standard) |

---

## Beyond the rubric

**Unattributed craft:** the SCAIL-2 section's community-tooling inventory (`collbroGTR/...`,
`dvelm/...`, "Wan2GP support") is unmarked prose-only attribution ("Ecosystem, all community:") —
moot once that section is cut per the Blocking fix; the new `scail-2` skill should mark it
properly using the `[community — …]` form, not inherit the prose-only style.

**Staleness:** see the motion-and-camera.md repositioning gap under Standard. No other
contradiction with the "no longer default" reframing found — the suite-table row "Permissive
licence worldwide... the suite's safe default" is a narrower, still-true claim (licence cleanliness,
not overall popularity) and doesn't conflict.

## Do not touch

- `## Per-mode settings` (not "Per-variant settings") — correct per §7 item 13, task-mode is the
  real axis for this model. Do not "fix" to match the image skills.
- Do not shrink SKILL.md to force the 25–40% band — §5.2 explicitly exempts wan-2-2's current
  ~42% share; only the SCAIL-2 cut (which shrinks it back toward normal) should move that number,
  not a deliberate trim elsewhere.
- `references/motion-and-camera.md` and `lora-training.md`'s filenames — both canonical, no rename
  owed (§4.3).
- Do not delete the SCAIL-2/Bernini-R pointer entirely — the "which Wan-family model replaces a
  character" question is real and asked; shrink it to a pointer, don't remove it.
