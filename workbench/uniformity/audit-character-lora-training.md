# Audit: `character-lora-training`

Graded against STANDARD.md §3 (cross-cutting-skill shape) and the applicable §8 checks. Model-skill-only
checks (selector table, per-variant settings, licence block, §4.1 core reference slots) are marked N/A
per the task brief and per §3's explicit exemption list.

Corpus: SKILL.md 2,869 w / 191 lines; references 7,097 w (dataset-and-captioning 1,406, evaluation-and-tooling
2,912, nsfw-training 1,676, publishing-and-likeness 1,103). Total 9,966 w — inside the 5,000–10,000
cross-cutting band (check 14 PASS), SKILL.md inside 2,000–3,200 (check 15 PASS), every reference inside
700–3,500 (check 17 PASS), SKILL.md well under the 500-line cap (check 16 PASS).

---

## Blocking

**[P1] SKILL.md — missing mandatory section: `## Pre-flight checklist`** (§3 row 8) — grepped the whole
skill (`SKILL.md` + `references/*.md`) for "checklist"/"pre-flight": zero matches. The section does not
exist in any form, folded-in or otherwise. → Add `## Pre-flight checklist`, verbatim heading, 8–12
numbered items, placed after "Adult and NSFW work" and before the two-bar section. Draft items to pull
from existing content: publish-check done (Civitai/TAKE IT DOWN), base model chosen for the job's
NSFW/character needs, dataset passes the 8-point/elevation/shot-size/expression coverage, captions follow
caption-the-residual for the encoder class, checkpoints saved throughout the run, probe set written before
training, grid tool chosen, blind pass planned, FaceEmbedDistance baseline calibrated if used.

**[P1] SKILL.md — missing mandatory section: `## Suite map / positioning`** (§3 row 9, "Where this fits")
— zero matches for "suite map", "where this fits", "reach for instead", "positioning". The intro's
model-routing table (lines 13–20) satisfies §3 row 2 (the boundary section) but is a different table doing
a different job — it routes *inward* for LoRA-training specifics only. Nothing in the skill positions it
against the rest of the suite (`comfyui-on-runpod`, `image-production-workflows`, `ideogram-4`'s lack of
a training path, etc.). → Add `## Where this fits` mapping this craft's role against every published
sibling, at minimum: `comfyui-on-runpod` (where to rent the GPU this craft needs), `image-production-workflows`
(where a trained LoRA gets deployed in a pipeline), and a row for `ideogram-4` ("no training path — route
to `sdxl`/`z-image`/`flux-2` instead", already stated correctly in `ideogram-4/SKILL.md` but not
reciprocated here).

**[P1] SKILL.md — no dedicated `## Failure modes & QC` section** (§3 row 7) — the content exists (a
6-row `Signal | Diagnosis | Fix` table, SKILL.md:126–133, which would clear the ≥6-row bar) but it is
folded inside `## Evaluating a run` with no heading of its own, so it is invisible to anyone scanning
headings for it, and the verbatim-heading check (§8.3) fails outright. → Split it out as its own
`## Failure modes & QC` section, verbatim heading, immediately after "Evaluating a run" and before "Adult
and NSFW work" (which has its own anatomy failure table in the reference and could gain a summary row or
two here as well).

**[P1] Two-bar section date line is wrong lexeme and stale relative to the 2026-08-22 material added
today.** SKILL.md:180 and `references/evaluation-and-tooling.md:203` both read `Dated **2026-08-13**.` —
wrong opener per §6.4 (canonical is `**Facts dated YYYY-MM-DD**`) and, more importantly, unchanged despite
today's addition of the video-dataset-factory paragraph (SKILL.md:78) and the full DOP subsection
(`dataset-and-captioning.md:118–131`). This is exactly the case §6.4 describes: *"The `; community craft
refreshed <date>` clause is added when a refresh pass touched craft without re-verifying hard facts —
exactly what the 2026-08-22 pass did."* → Change both to
`**Facts dated 2026-08-13; community craft refreshed 2026-08-22.**` (or re-verify the hard facts today and
drop the split). `freshness.json`'s `last_checked: 2026-08-22` is correct and should not be touched
(§6.4's own rule) — only the in-file date line is wrong.

**[P1] Summarise-up hop: SKILL.md drops attribution the reference carries for the same claim, twice.**
- SKILL.md:117 restates the DreamBench++ DINO/CLIP-I misalignment finding with no marker at all —
  `references/evaluation-and-tooling.md:131` carries `` `[official — published benchmark]` `` for the
  identical claim. → Add the marker to SKILL.md:117.
- SKILL.md:141 restates the abliteration-doesn't-work mechanism with no marker — `references/nsfw-training.md:21`
  attributes the same mechanism to a direct quote, `` `[community — -p-e-w-, author of Heretic]` ``.
  → Add the marker (or a shorter form, `` `[community — Heretic author]` ``) to SKILL.md:141.

---

## Standard

**[P2] Orphan craft numbers with no named source and no marker** (§6.2 rule: craft + actionable + no
named source in-sentence ⇒ marker required). None of the following carry a name or a bracket marker:
- SKILL.md:64 — "The consistent community finding is that **15–30 well-curated images outperform 100
  mediocre ones**." (bare hedge "consistent community finding" is not a name per §6.2's explicit list of
  disqualified hedges.)
- SKILL.md:68–72 — the entire 8-point rotation / elevation / shot-size / expression / lighting coverage
  protocol. No source anywhere in the section.
- SKILL.md:88–94 — the rank/alpha/LR/steps/batch table. Hedged as "the shape of the consensus" in the
  section lede, which is itself a bare hedge, not a name.
- `references/dataset-and-captioning.md:15` and `:64` — same 15–30-images claim and curation table, no
  source.
- `references/dataset-and-captioning.md:106` — "**Community experience** puts the practical ceiling
  around half a dozen outfits" — names no one.
- `references/nsfw-training.md:48` — the rank-concatenation LoRA-merge technique ("published tooling
  merges them... by rank concatenation") — no name, no marker, despite being a specific enough technique
  (with a formula) that a reader will act on it.
- `references/nsfw-training.md:71–74` — the SDXL-finetune character table ("**Reported** as the most
  anatomically accurate...") — "reported" names no one; `sdxl/references/lora-training.md`'s equivalent
  table attributes the same claims to named sources (ViewComfy, Bieler, ai-toolkit discussions etc.) that
  this file could borrow.

→ Fix by either naming the source in prose (several already exist in the sibling model skills — e.g.
`sdxl/references/lora-training.md`'s NoobAI/WAI/Illustrious attributions could be echoed here) or adding
`` `[community — …]` ``/`` `[community — single report; re-verify]` `` markers.

**[P2] `Anima` row lacks the required status word** (§6.5, §8 check 37). SKILL.md:155 — `| **Anima** |
29% | Rising fast — the most common base in a newest-first pull |` — correctly plain-bold and unlinked,
but carries no status word ("unpublished", "not yet covered by this suite", etc.) the way §6.5 requires
for an unpublished model. → Append a status clause, e.g. "Rising fast … — **no dedicated skill yet**."

**[P2] `ltx-2-5` and `anima` are not acknowledged as forthcoming siblings anywhere in this skill.**
`anima` appears once (SKILL.md:155, the NSFW-share table) but only as a data point, not as a named
upcoming skill; `ltx-2-5` does not appear at all. Two concrete gaps once those skills publish:
- The video-as-dataset-factory paragraph (SKILL.md:78) currently names only `minimax-h3`'s Ref2VA mode.
  It already hedges "whichever video model you use," so no rewrite is required today, but it will need an
  `ltx-2-5` example/row once that skill exists, and probably a second boundary-table row.
- Anima's ~6 GB VRAM floor changes the "what can I train at home" story this skill implicitly tells
  (SKILL.md:94's `16–24 GB` batch-size note, and the base-model-selection framing throughout `nsfw-training.md`
  §2 and SKILL.md's adult-flagged-share table) — worth a line once Anima is published, not now.
Not a finding against the current file (the standard names both as correctly unlinked/unpublished), just
routing debt to carry forward.

**[P3] `evaluation-and-tooling.md` is missing its `## Contents` TOC heading** (2,912 words, ≥2,000
threshold). It has a numbered link list at the top (lines 7–14) functioning as a TOC, but not under the
canonical `## Contents` heading — this is the exact file STANDARD.md §6.7 already names as missing it.
→ Add `## Contents` immediately above the existing list.

---

## Cosmetic

None beyond what's listed above — marker syntax is clean (all backtick counts even, no nested/nested
markers, no italic-parenthetical form anywhere in this skill), all sibling mentions are proper
`[`name`](../name/)` links (none bare), no link reaches above `skills/generative-media/`, and the
frontmatter description is 220 words (inside 180–320) with the verbatim "even obliquely:" trigger and a
closing sweep.

---

## N/A (model-skill-only checks)

Checks 4, 6 (per-variant/mode settings), 8, 11, 21 (§4.1 core reference-slot boundary — this skill has no
prescribed reference set per §4.3), and the licence-block requirement are N/A per §3's explicit exemption
list ("selector table, per-variant settings, setup & ecosystem, licence & limitations, signature
technique... Do not open findings for their absence"). Check 6.6's tables-vs-prose rule and check 9
(§4.3 rename map) are also N/A — this skill has no §4.1-named files to rename.

---

## Boundary table — exists, complete, correctly placed

**Verdict: PASS.** SKILL.md:13–20 carries the mandatory routing-inward table, one row per model skill
with an active LoRA ecosystem (`sdxl`, `z-image`, `flux-2`, `krea-2`, `wan-2-2`, `minimax-h3`) — all six
named in the task brief are present, each with a genuinely distinguishing "thing you cannot skip." Its
placement in the intro rather than a tail section is explicitly blessed (§7, justified deviation #11).
`ideogram-4` is correctly absent (no training path; that skill's own SKILL.md routes to
`character-lora-training` and to `sdxl`/`z-image`/`flux-2` reciprocally — confirmed at `ideogram-4/SKILL.md:158,227`).

No missing rows. The one soft gap: the table links to each sibling's *skill root* (`../sdxl/`), not to the
specific `references/lora-training.md` file the boundary is actually about — acceptable per §6.5's link
form guidance (which permits either), but a reader landing on `../sdxl/` still has to find the training
reference themselves. Not scored as a finding; noted for awareness only.

---

## Duplication found in model skills

Routing note for the orchestrator — these are findings *against the model skills*, not this skill, and no
edits were made to them.

1. **`z-image/references/lora-training.md:35`** restates the full "caption the residual" doctrine and
   mechanism in prose — not a pointer, a complete independent explanation ("A LoRA learns whatever you
   *don't* name. So for a character, describe everything that is not the identity...") — duplicating
   `character-lora-training/SKILL.md:45–58` ("The one rule that changes everything"). The file does carry
   the boundary pointer at its top (line 3), but the doctrine itself is fully re-derived below it rather
   than linked.

2. **`z-image/references/lora-training.md:22–37`** (the anchor-image → 15–25-variant → one-clause-at-a-time
   dataset workflow) duplicates `character-lora-training/references/dataset-and-captioning.md` §2–3 (the
   8-point rotation protocol and the synthetic dataset factory) in substance, including the "byte-identical"
   phrasing for the one-clause rule (`dataset-and-captioning.md:57` vs `z-image/…/lora-training.md:37`).

3. **`z-image/references/lora-training.md:119–123`** restates the evaluation method (save checkpoints
   throughout, "Goldilocks" epoch language, XY grid of epoch × strength) that
   `character-lora-training/references/evaluation-and-tooling.md` §1–2 owns in full — again with a link
   at the end (line 125) but the substance duplicated above it.

4. **Two model skills route to `z-image` instead of to `character-lora-training` for the shared doctrine
   itself**, which is the more consequential problem — it means the cross-cutting skill is being bypassed
   as the canonical source in favor of a sibling model skill:
   - `minimax-h3/references/loras-and-training.md:70` — "**Caption the residual**... [`z-image/references/lora-training.md`](../../z-image/references/lora-training.md) **is the fullest treatment**."
   - `wan-2-2/references/lora-training.md` (§4, "Dataset construction... see
     [`z-image/references/lora-training.md`](../../z-image/references/lora-training.md) for the underlying
     craft") and `krea-2/references/lora-training.md:105` ("`z-image` and `flux-2` skills document the
     shared craft in depth") do the same.

   Given finding 1–3 above, this is not a harmless alternate route — `z-image`'s file is duplicated content,
   not a canonical source, so these three model skills are citing a copy instead of the original. The
   fix belongs to those skills (repoint the citations to `character-lora-training`), but it is worth
   flagging here because it is evidence the boundary table's *intent* — "this owns what transfers" — is
   not being honored suite-wide even where the mechanical pointer boilerplate is present at the top of
   each file.

---

## Beyond the rubric

**Unattributed craft** — see the "Orphan craft numbers" finding above (§ Standard) for the full list with
line numbers; roughly seven distinct unattributed-but-actionable claims found across SKILL.md and two
reference files, none rising to a P1 (all are craft, not hard fact, and the skill's two-bar section already
sets craft-wide confidence correctly) but collectively the clearest gap in this skill given how
craft-dominant it is. The skill's marker discipline is otherwise good — 2 markers in SKILL.md, 7 across
references, all syntactically clean — the gap is coverage, not hygiene.

**Staleness** — nothing found beyond what `freshness.json` already tracks. The TAKE IT DOWN Act's 19 May
2026 enforcement date is now 3+ months in the past relative to today (2026-08-22) and the file correctly
describes it as live/enforced rather than pending — no drift there. `freshness.json`'s own watchlist
already carries both the Civitai policy and the Act as tracked items with a 7-day cadence, which is
appropriate given §7's minimax-h3 precedent for a ruling-out legal gate. The one dating problem found is
the two-bar section's own date line (P1 above), which is a *skill-freshness-mechanics* bug, not a *content*
staleness bug.

**Over-conformity risk** — none observed. The skill does not force any model-skill-shaped section (no
fabricated selector table, no licence block, no per-variant settings) — it correctly follows §3's shape.
If anything the risk ran the other way: two entire mandatory §3 sections (pre-flight checklist, suite map)
were dropped rather than force-fitted, which is the opposite failure mode from over-conformity and the one
actually present here.
