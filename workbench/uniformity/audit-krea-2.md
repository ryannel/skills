# Audit — krea-2

Graded against `workbench/uniformity/STANDARD.md` §8, 2026-08-22. Corpus: SKILL.md 5,610 words / 286
lines; references 9,591 words (api-and-hosted 718, characters 2,228, lora-training 3,070,
prompting-guide 1,668, setup-and-workflows 1,907). Total corpus 15,201 words. Marker count: 131
total tokens matching `[tier — …]` shape (48 in SKILL.md, 83 across references); of those, only
**6 are backticked** (2 in SKILL.md, 4 in `lora-training.md`) — 125 are bare.

---

## Blocking

**[P1] check 26 — SKILL.md § How to read the claims — the five contested bullets carry zero markers.**
`SKILL.md:266-272`. The "Contested points worth holding in your head:" list (LoRA training doctrine;
Raw as an inference model; int8 convrot; the softness itself; training resolution) is the exact
construct STANDARD §6.2 calls out as unconditionally requiring `[contested]`/`[flagged — re-verify]`,
and the exact construct `minimax-h3`'s equivalent section does correctly (every one of its six bullets
carries a marker). None of krea-2's five do — not even the ones that map cleanly onto existing
markers used elsewhere in the file (e.g. int8 convrot is disputed with `[community — …]` citations
in the *Setup & ecosystem* section three paragraphs earlier, but the two-bar bullet restating the
dispute has no marker at all).
**Fix:** append a marker to each bullet:
- LoRA training doctrine → `` `[contested]` ``
- Raw as an inference model → `` `[contested]` ``
- int8 convrot → `` `[contested]` ``
- The softness itself → `` `[contested]` ``
- Training resolution → this one is resolved-with-correction, not live-contested; either drop it from
  this list (it belongs as a closed item, already covered by `lora-training.md §2c`'s corrections) or
  mark it `` `[flagged — re-verify]` `` if the concern is that other writeups still repeat the 768
  figure.

**[P1] check 28 — malformed, nested marker in SKILL.md (not in the reference file STANDARD names).**
`SKILL.md:166`: `` [community — muerrilla; node unverified here, `[flagged — re-verify]`] ``. Unbalanced
brackets, a backticked marker nested inside an unbacktick'd one — invisible to the freshness grep.
**Correction to STANDARD's own note:** §6.2 attributes this exact bug to
`krea-2/references/setup-and-workflows.md`; it is not there — `setup-and-workflows.md` has no
"muerrilla" mention at all. The bug is in `SKILL.md`'s *Production pipelines & mixing models* section.
Flag this discrepancy for whoever maintains STANDARD.md.
**Fix:** split into two well-formed markers: `...the method should transfer to anything sharing the
Qwen-Image VAE `` `[community — muerrilla; re-verify]` ``.` (the "node unverified here" content maps to
the closed-set `re-verify` qualifier, so one marker suffices — no need for two).

**[P1] check 33 — sibling mentions are bare code spans almost everywhere, not markdown links.**
Only 4 of ~28 sibling mentions in this skill are proper `` [`name`](../name/) `` links
(`SKILL.md:63` → minimax-h3; `characters.md:102` second mention → minimax-h3; `lora-training.md:3,105`
→ character-lora-training). Every other mention is a bare code span. Full list:
- `SKILL.md:168` `` `image-production-workflows` ``
- `SKILL.md:198` `` `ideogram-4` ``
- `SKILL.md:227` `` `z-image` ``
- `SKILL.md:229` `` `flux-2` ``
- `SKILL.md:230` `` `sdxl` ``
- `SKILL.md:232` `` `sdxl` ``
- `SKILL.md:233` `` `ideogram-4` ``
- `SKILL.md:234` `` `sdxl` ``, `` `z-image` ``
- `SKILL.md:235` `` `flux-2` ``, `` `sdxl` ``
- `SKILL.md:236` `` `image-production-workflows` ``
- `SKILL.md:237` `` `wan-2-2` ``
- `SKILL.md:285` `` `flux-2` `` (Reference files table)
- `references/characters.md:99` `` `flux-2` ``
- `references/characters.md:100` `` `z-image` ``
- `references/characters.md:101` `` `sdxl` ``
- `references/characters.md:102` `` `minimax-h3` `` (first mention, before the linked second one)
- `references/characters.md:108` `` `minimax-h3` ``
- `references/setup-and-workflows.md:151` `` `image-production-workflows` ``
- `references/lora-training.md:168` `` `z-image` ``, `` `flux-2` ``
- `references/lora-training.md:194` `` `sdxl` ``, `` `z-image` ``
- `references/prompting-guide.md:60` `` `ideogram-4` ``
- `references/prompting-guide.md:99` `` `ideogram-4` ``
**Fix:** mechanical — wrap each in `` [`name`](../name/) `` (or `../../name/` from a `references/`
file at one extra level, matching the pattern already used correctly at `characters.md:102`,
`lora-training.md:3`). Bidirectionality already holds — every sibling krea-2 names links back to
krea-2 (verified in z-image, flux-2, sdxl, wan-2-2, minimax-h3, ideogram-4,
image-production-workflows) — this is a link-*form* fix only, not a content gap.

**[P1] check 27 — one inline-label `(community)` stub, unmarked and undersourced.**
`SKILL.md:40`, selector-table cell: "the Raw+Turbo-LoRA inference recipe (**community**)". This is
exactly the inline-label form §6.2/check 27 names for conversion. The recipe is already properly
attributed elsewhere in the same file (`nsfwVariant`, per-variant settings + production pipeline).
**Fix:** either delete the parenthetical (redundant — the recipe is sourced two sections later) or
replace with `` `[community — nsfwVariant]` ``.

---

## Standard

**[P2] check 2 — "LoRA training & characters" (slot 8) sits after Production pipelines (slot 9)
instead of before it.** `SKILL.md:172-183` ("## LoRA training & characters (summary — full treatment
in references)") comes *after* `## Production pipelines & mixing models` (154) and before
`## Failure modes & QC` (187). STANDARD's table places slot-8 "model-specific mechanics" material
between the signature-technique section (7) and Production pipelines (9); the sibling that carries
comparable slot-8 content, `wan-2-2`, does exactly that — its "Motion, camera and structural control"
and "The two-LoRA rule" both sit between per-mode settings and Production pipelines.
**Fix:** move the "## LoRA training & characters" section to directly after "## The anti-AI-look and
its two taxes" (141-150) and before "## Production pipelines & mixing models" (154).

**[P2] check 15 — SKILL.md is 5,610 words, over the 5,500 hard cap, without a named §5.2 justification.**
Percentage share (36.9%) is inside the 25-40% band, but the absolute cap is separately binding. None
of §5.2's four justifications clearly apply: no ruling-out licence (the revenue gate is conditional,
not the territorial exclusion `minimax-h3` has — §2 explicitly says only minimax-h3 qualifies for the
licence-first slot); no acceleration/configuration stack the model is unusable without; not more task
modes than the suite norm (4 variants, same order as `sdxl`'s two-axis system); the closest fit is
"a documented capability set the official templates do not expose" (DOP, VAE Sharp/Sharp Plus, the
latent colour vectors) — but that alone doesn't carry the weight `minimax-h3` needed 3-of-4 criteria
for. **This is a real finding, not a justified deviation**, and it is caused by two identifiable
passages that duplicate or over-extend material that belongs in a reference (see the two findings
immediately below) — trimming those brings SKILL.md back under 5,500 without losing any pillar
coverage.

**[P2] check 19 — Quantisation & VRAM paragraph in SKILL.md restates setup-and-workflows.md §2's
table in full, not just the rule + anchor number.** `SKILL.md:98-100` reproduces every quant tier
(bf16 26.3 GB, fp8_scaled 13.1 GB, int8_convrot 13.5 GB, mxfp8 13.5 GB, nvfp4 7.7 GB, encoder
8.9/5.2 GB) *and* both sides of the int8-quality dispute (nsfwVariant/YeahYeah2992 vs ganrocks007) —
essentially the same granularity as `references/setup-and-workflows.md §2`'s table. Per §5.3's
corollary, SKILL.md should carry the rule and the anchor number (default: fp8_scaled, 13.1 GB; the
2× int8 speed claim, contested) and point to the reference for the full ladder.
**Fix:** trim `SKILL.md:98-100` to ~3 sentences (default precision, the one contested speed/quality
claim, VRAM tier by GB) and route the rest to `references/setup-and-workflows.md §2` (which already
has it in full, as a proper table).

**[P2]/[P3] check 18 — the VAE-Sharp and latent-colour-vector paragraphs exist only in SKILL.md, with
no reference-file counterpart, inverting the usual placement.** `SKILL.md:164` (Qwen Image VAE
Sharp/Sharp Plus) and `SKILL.md:166` (extracted latent colour vectors) are full paragraphs of
reference-grade detail — two named decoder variants with characterised trade-offs, a `--fp32-vae` flag
requirement, and a whole unshipped-tooling paragraph — that do not appear anywhere in
`references/setup-and-workflows.md §5` (the VAE section), which still only covers the Wan 2.1 swap.
This is the opposite of the intended split: SKILL.md is carrying the derivation and the reference has
nothing. The colour-vectors paragraph in particular is not yet actionable — "a ComfyUI node was
announced" (not shipped), and per §5.3's test ("if a section can be deleted and the reader's next
action is unchanged, it is padding") a reader cannot act on it today beyond "watch for this."
**Fix:** move both paragraphs' full detail into `references/setup-and-workflows.md §5` (renaming it
to cover "the VAE decision" generally — Wan 2.1 swap, VAE Sharp/Sharp Plus, and the colour-vector
node), and leave one sentence + pointer in SKILL.md: "A third VAE option (Qwen Image VAE Sharp/Sharp
Plus) trades some of the softness for sharpening without the Wan-VAE colour shift; latent-space colour
grading is emerging but its ComfyUI node isn't shipped yet — `setup-and-workflows.md §5`." This
recovers roughly 150-180 words toward the check-15 finding above.

**[P2] check 25 — date line uses the "Release:" lexeme, not the canonical "Facts dated" opener.**
`SKILL.md:274`: `**Release:** announced 12 May 2026; open weights 22 June 2026; official facts
verified 7 July 2026; **community craft refreshed 22 August 2026** from a sweep of…`. This is one of
the six divergent lexemes §6.4 resolves against; the release-date content is also already present in
the intro paragraph (`SKILL.md:28`), so restating it here is redundant with the thing that actually
needs to open the line — the facts-dated / craft-refreshed distinction, which this line *does* track
correctly, just under the wrong label.
**Fix:** `**Facts dated 2026-07-07; community craft refreshed 2026-08-22** from a sweep of
r/StableDiffusion, r/unstable_diffusion and Civitai. On that sweep Krea 2 was the second-largest
base-model tag on Civitai by monthly volume, behind Illustrious — it is no longer a new model, it is
the image side's centre of gravity.` (Drop "announced 12 May 2026; open weights 22 June 2026" from
this line — it already lives in the intro paragraph per §6.4's own instruction not to move it, only to
stop duplicating it here.)

**[P2] Beyond-rubric — a single-source finding (Differential Output Preservation) is promoted to
superlative status without a confidence qualifier.** The DOP multi-character result traces to one
named author, MASilverHammer (`characters.md:46-55`, `lora-training.md §6`), building on a second
unreplicated author's config. SKILL.md's suite table states it as "**The suite's best answer**"
(`SKILL.md:230`) and the two-bar craft paragraph states it "with confidence." Nothing is wrong with
citing a single strong report, but §6.2's qualifier vocabulary exists exactly for this case
(`single report`), and neither the SKILL.md summary nor the two reference-file passages use it.
**Fix:** add `; single report` to the DOP markers in `characters.md:46`, `lora-training.md §6`'s DOP
paragraph, and the SKILL.md characters bullet at `SKILL.md:181`, without softening the substantive
claim — the finding may well be correct, but the reader should know it rests on one author's runs
before betting a production pipeline on the 4-character cap.

---

## Cosmetic

**[P3] check 31 — 125 of 131 markers in this skill are bare, not backticked.** Confirms STANDARD
§6.2's own count ("krea-2 alone holds 125 of 157 bare markers" suite-wide). This is the largest
mechanical diff of any kind in this skill and touches every file except `api-and-hosted.md` (which has
9 markers, also bare) — SKILL.md 46/48 bare, `characters.md` 15/15 bare, `prompting-guide.md` 17/17
bare, `setup-and-workflows.md` 21/21 bare, `lora-training.md` 16/20 bare (4 already backticked).
**Fix:** mechanical find/replace, wrapping every `[tier — …]` token in backticks. No content changes.

**[P3] check 31 — one marker exceeds the ~60-character payload cap by carrying a full quotation.**
`references/setup-and-workflows.md:120`: `[community — nsfwVariant, Civitai "Krea 2 simple gen
workflow for high quality realism", incl. the author's write-up; their claim: "WAY better" photoreal
than stock Turbo]` — 129 characters, this is the exact instance STANDARD §6.2 cites as the model case
for the cap. **Fix:** `` `[community — nsfwVariant, Civitai]` ``; move the workflow title and "WAY
better" quote into the prose sentence that follows (which already discusses the recipe).

**[P3] check 37 — SCAIL-2 named without a status word.** `references/characters.md:108`: "Applies to
SCAIL-2 and to `minimax-h3`'s Ref2VA video-edit mode alike." — no bold, no status word ("announced",
"unreleased", etc.), unlike the Krea 3 tease which does this correctly. Low priority — SCAIL-2 is
mentioned in passing, not as a comparison target requiring the fuller treatment.
**Fix:** "Applies to **SCAIL-2** (unreleased) and to `minimax-h3`'s Ref2VA video-edit mode alike."

**[P3] non-canonical qualifier vocabulary.** `references/characters.md:25`: `[community — widely
replicated, 2026-07-07 → 2026-08]`. "widely replicated" isn't in §6.2's closed qualifier set
(`re-verify`, `single report`, `contested`, `early`, `strong`, `convergent`). **Fix:** `` `[community
— convergent]` `` (the closest closed-set term), with the named authors already listed two lines below
in the same subsection carrying the specific attribution.

**[P3] bare epistemic hedge.** `references/lora-training.md:145`: "contradicting the **widely-linked
issue thread** that says it is not" — names no source, isn't a marker. Low priority: this is
describing what a correction is *responding to*, not asserting a claim of its own, so the bar is
softer than a forward-looking craft claim — but a `[community — re-verify]` or a named link would
still be cleaner.

---

## Verified correct — do not touch

- **Insertion order in `lora-training.md` is already fixed.** §§1, 2 (with 2a/2b/2c in that order),
  3-8 read in coherent sequence, and the `## Contents` TOC (lines 8-19) matches the actual heading
  order exactly. The `## 2c.` section the task brief warned about is correctly positioned between
  `## 2b.` and `## 3.` — no repair needed here.
- **The two guidance-convention trap (SKILL.md footnote ² and the failure table) is correctly
  surfaced in SKILL.md, not buried in a reference** — STANDARD §5.4 names this exact case as
  exemplary. Do not move it to a reference during any depth-trim pass.
- **The Krea 3 tease is handled exactly right**: bold, named source + date (`krea_ai, 2026-08-19`),
  explicit "no announced date, weights policy or capabilities," a concrete reader action ("note it
  before starting anything with a long payback period"), and a `` `[pending release]` `` marker
  (only mis-backticked as noted above — the *content* is the model other skills' teases should copy).
  This is not over-claimed; if anything it is the skill's most careful hedge.
- **Bidirectionality is intact.** Every sibling named in krea-2's suite table (z-image, flux-2, sdxl,
  wan-2-2, minimax-h3, ideogram-4, image-production-workflows, character-lora-training) links back to
  krea-2 in its own table or craft body — verified by direct grep across all seven files.
- **Two-bar section heading, position and required elements are all present and correct** except for
  the dating-lexeme and contested-marker findings above, which are narrow and mechanical, not
  structural.
