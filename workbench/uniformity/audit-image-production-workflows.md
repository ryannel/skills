# Audit: `skills/generative-media/image-production-workflows/`

Graded against STANDARD.md §3 (cross-cutting-skill shape) + §8 rubric, with model-skill-only checks
(selector table, per-variant settings, four §4.1 core reference slots, licence section, §6.5
model-suite-table axes) marked N/A per the task brief. Read: SKILL.md (184 lines / 2,785 words
incl. frontmatter), all three references (`production-ladder.md` 1,168 w, `mixed-model-recipes.md`
1,159 w, `workflows-as-code.md` 953 w — corpus 6,065 w), `freshness.json`'s
`image-production-workflows` entry, CLAUDE.md, `comfyui-on-runpod/SKILL.md` (boundary-table
reciprocity), `minimax-h3/SKILL.md` (summarise-up-hop check), and `workbench/anima/prompt.md`
(new-skill cross-link).

---

## Blocking

**[P1] No Boundary section (§3 item 2) exists — the skill's central structural requirement is missing entirely, not just under-filled.**
Evidence: §3 requires a dedicated, MANDATORY table-shaped boundary section, distinct from both the
frontmatter clause and the tail positioning table. This skill has the frontmatter clause (fine) and
the tail `## The suite map` (item 9, fine, correctly placed) — but nothing satisfying item 2. The
only boundary statement is one prose clause in the intro: `SKILL.md:9` — "it complements the
per-model skills (`z-image`, `sdxl`, `flux-2`, `ideogram-4`), which own their models' exact node
settings, prompting dialects, and LoRA ecosystems." §3 is explicit that "the table is not optional."
This is reciprocal with, and worse than, the gap the `comfyui-on-runpod` audit found: that skill
*has* a boundary table (`## What this owns, and what it doesn't`, `comfyui-on-runpod/SKILL.md:11-26`)
but it lacks a row for this skill. Here there is no table at all to hold a row in.
Fix: insert a new section immediately after the intro (`SKILL.md:14`, before `## The production
ladder`), matching the sibling's free-form heading:
```
## What this owns, and what it doesn't

| Question | Where it belongs |
|---|---|
| Exact node settings, prompting dialect, per-model LoRA ecosystem, licence for one specific model | The model skill — [`z-image`](../z-image/), [`sdxl`](../sdxl/), [`flux-2`](../flux-2/), [`ideogram-4`](../ideogram-4/), [`krea-2`](../krea-2/) |
| Multi-stage pipelines, denoise bands, mixed-model handoffs, regional prompting & inpainting craft, workflows-as-code | **here** |
| Deploying/running ComfyUI itself — pods, serverless endpoints, volume/model placement, RunPod cost | [`comfyui-on-runpod`](../comfyui-on-runpod/) |
| Making a character or style LoRA | [`character-lora-training`](../character-lora-training/) |
| The full video production ladder, restore-before-interpolate ordering | [`wan-2-2`](../wan-2-2/) / [`minimax-h3`](../minimax-h3/) |
| Using a video model's single-frame mode as an image editor | **here** — see "A video model is now a legitimate stage in an image pipeline" below |
```
Also add the reciprocal row to `comfyui-on-runpod/SKILL.md`'s own boundary table (already flagged in
that skill's audit) — this is the other half of the same fix.

**[P1] Two-bar section's required "Contested / unresolved points" element (§6.3 item 4) is missing, and the two claims that belong there sit in unmarked prose instead.**
Evidence: `SKILL.md:171` — "Two honest flags: the **Ideogram typography-pass pattern is inferred
craft** (practiced, but no canonical named workflow was found), and **batch QC is tooled for
comparison but not for judgement**..." This is prose inline in the craft paragraph, not a bullet
list, and carries no `[flagged]`/`[contested]` bracket. A second contested claim outside the two-bar
section is in the same state: `references/mixed-model-recipes.md:68` — "Per-region *LoRA*
application on DiTs is still contested craft." — no marker. This also fails the §6.2 floor (check
32): the skill's only bracket marker (`SKILL.md:98`, `` `[community — DaLyon92x]` ``) is a
`community` tier, not `flagged`/`contested`, so nothing satisfies "≥1 `[flagged]`/`[contested]`
marker, or an explicit nothing-flagged line."
Fix: replace the "Two honest flags" clause in `SKILL.md:171` with a proper bullet list before the
date line:
```
**Contested / unresolved points:**
- The Ideogram typography-pass pattern is practiced but has no canonical named workflow. `[flagged — no canonical workflow]`
- Per-region LoRA application on DiT regional-attention setups is still being worked out. `[contested]`
```
(The batch-QC "tooled for comparison, not judgement" sentence isn't itself contested — leave it
in the craft paragraph where it already is.) Convert `mixed-model-recipes.md:47`'s cell text
"**inferred craft — no canonical named workflow; flagged**" → `` `[flagged — no canonical workflow]` ``,
and end `mixed-model-recipes.md:68`'s sentence with `` `[contested]` `` before the period.

**[P1] Date line uses a retired lexeme and prose dates instead of the canonical `Facts dated YYYY-MM-DD` form (§6.4).**
Evidence: `SKILL.md:173` — "Date-stamped June 2026; **tool-status and cross-family sections
refreshed August 2026**." "Date-stamped" is not one of the six lexemes STANDARD.md is retiring in
favour of one, and neither date is ISO. `git log --follow` confirms the file's first substantive
authoring commit is 2026-06-12 (matches "June 2026"); today's pass is 2026-08-22.
Fix: `**Facts dated 2026-06-12**; community craft refreshed 2026-08-22. The fastest-moving parts:
finisher models (SeedVR2's successors and the new generative video upscalers), DiT
regional/per-region-LoRA tooling, the video-model-as-image-editor path, and ComfyScript/frontend
version compatibility.` (keep the existing trailing sentence; only the opener changes.)

**[P1] Ten sibling mentions are bare code spans instead of relative links (§6.5), including the whole "suite map" table — this skill's own canonical exemplar (JD#10).**
Evidence:
- `SKILL.md:9` — `` `z-image`, `sdxl`, `flux-2`, `ideogram-4` `` (4 bare, intro paragraph).
- `SKILL.md:94` — `` `minimax-h3` `` bare (its first mention, `SKILL.md:84`, is correctly linked).
- `SKILL.md:153-159` — the entire `## The suite map` table: all seven rows (`sdxl`, `z-image`,
  `flux-2`, `ideogram-4`, `krea-2`, `wan-2-2`, `minimax-h3`) are bare.
- `SKILL.md:161` — `` `minimax-h3`, `krea-2` `` bare.
- `SKILL.md:163` — "See `wan-2-2` for the video ladder" bare.
- `references/mixed-model-recipes.md:45` — "see the `krea-2` skill" bare.
This is the same drift STANDARD.md §6.5 already found in six other skills' suite tables — but this
skill's suite map is the one JD#10 names as "the suite's canonical map," so its own non-compliance is
the highest-leverage instance in the corpus.
Fix: wrap every instance above as `` [`name`](../name/) ``. For the table rows specifically:
`| [\`sdxl\`](../sdxl/) | ... |`, and so on for all seven rows plus the four intro mentions and the
two prose "See `X`" sentences.

**[P1] Fourteen italic-parenthetical provenance markers remain, more than any other audited skill so far — the second, undeclared attribution system §6.2 retires.**
Evidence and canonical replacements (all backticked bracket form, placed before the governing
sentence/cell's terminal punctuation):
| Location | Current | Replace with |
|---|---|---|
| `SKILL.md:53` | `*(named community workflows — details and sources in `references/mixed-model-recipes.md`)*` | Drop italics; not itself a claim needing a marker — plain parenthetical is fine: `(named community workflows; details and sources in references/mixed-model-recipes.md)` |
| `SKILL.md:60` | `*(inferred craft — no canonical named workflow yet)*` | `` `[flagged — no canonical workflow]` `` |
| `production-ladder.md:34` | `*(Community, named.)*` | `` `[community — sandner.art]` `` |
| `production-ladder.md:40` | `*(Official — ltdrdata/ComfyUI-Impact-Pack.)*` | `` `[official — ltdrdata/ComfyUI-Impact-Pack]` `` |
| `production-ladder.md:42` | `*(community, named — myByways' writeup; Civitai workflow conventions)*` | `` `[community — myByways, Civitai workflow conventions]` `` |
| `production-ladder.md:50` | `*(Official ADetailer discussion #533.)*` | `` `[official — ADetailer discussion #533]` `` |
| `production-ladder.md:59` | `*(Official repos.)*` | `` `[official — TTPlanet repos]` `` |
| `production-ladder.md:66` | `*(community, named)*` | `` `[community — MyAIForce]` `` |
| `production-ladder.md:75` | `*(Official.)*` | `` `[official — lquesada/ComfyUI-Inpaint-CropAndStitch]` `` |
| `production-ladder.md:77` | `*(Official node; community recipe.)*` | Split: `` `[official]` `` after the `DifferentialDiffusion` core-node claim; drop or name the second clause (see finding below — currently unnamed) |
| `production-ladder.md:91` | `*(Official repo.)*` | `` `[official — Jonseed/ComfyUI-Detail-Daemon]` `` |
| `mixed-model-recipes.md:24` | `*(community-convergent across named sources)*` | See separate finding below — this is also a bare hedge, not just a format issue |
| `workflows-as-code.md:25` | `*(Official repo.)*` | `` `[official — Chaoses-Ib/ComfyScript]` `` |
| `workflows-as-code.md:58` | `*(Community-strong — ViewComfy's production-API guide is the canonical writeup.)*` | `` `[community — ViewComfy production-API guide; strong]` `` |
Note: the task brief's count of "3" for this pattern undercounts — 3 appears to have been an
estimate; the actual grep-verified total across the skill is 14, split 2 in SKILL.md and 12 across
the three references.

**[P1, contingent] `freshness.json`'s watchlist has no entry for either flagged/contested claim (§6.2 requires the freshness protocol be able to grep for them; check 40).**
Evidence: the `image-production-workflows` entry's 6 watchlist items (`upscaler-landscape`,
`z-image-regional`, `workflows-as-code`, `mixed-model-recipes`, `cross-skill-sync`,
`redetail-constraints`) cover none of the two flagged/contested claims fixed above. This is
contingent on the marker fix above landing first — before that, the claims aren't greppable at all.
Fix: once the bracket markers exist, add:
```json
{
  "id": "ideogram-typography-pass-unconfirmed",
  "type": "ecosystem-gap",
  "claim": "Ideogram typography-pass pattern flagged as inferred craft, no canonical named workflow",
  "where": "references/mixed-model-recipes.md, Named recipes table",
  "check": "Has a named community workflow emerged for the Ideogram-typography -> composite pattern?"
},
{
  "id": "dit-per-region-lora-contested",
  "type": "community",
  "claim": "Per-region LoRA application on DiT regional-attention setups is contested craft",
  "where": "references/mixed-model-recipes.md §4",
  "check": "Has consensus formed on per-region LoRA application for DiT regional prompting?"
}
```

---

## Standard

**[P2] Section order breaks the §3 normative sequence in two places — craft-body content sits both before "the one rule" and after "tool status."**
Evidence: `## The production ladder` (`SKILL.md:18`, craft-body/item 5) sits *before*
`## The one rule that changes everything` (`SKILL.md:32`, item 4) — the same class of violation
STANDARD.md's §2 RESOLVED note found in `z-image` (setup before the one rule). Separately,
`## Workflows as code` (`SKILL.md:102`, also craft-body/item 5) sits *after*
`## Tool status that changed recently` (`SKILL.md:66`, item 6, conditional) — splitting the
craft-body cluster around a later-numbered section.
Fix: reorder to Intro → Boundary (new) → The one rule → Production ladder → Mixing models →
Workflows as code → Tool status → Failure modes → Pre-flight → Suite map → Two-bar → Reference
files.

**[P2] The identity-preserving denoise-band table is duplicated near-verbatim between SKILL.md and a reference (§5.3/§5.4).**
Evidence: `SKILL.md:36-41` ("The one rule," 4-row denoise table) and
`references/mixed-model-recipes.md:26-31` (Rule 2, same 4 tiers, same thresholds, reworded header)
carry the same content twice in full, not a rule-plus-derivation split.
Fix: collapse `mixed-model-recipes.md`'s Rule 2 table into a one-line pointer: "the identity-preserving
band is ~0.2–0.5 — same four tiers as `## The one rule` in SKILL.md; see there for the full
breakdown."

**[P2] The skill's single most load-bearing craft claim — the master denoise-band table — carries no attribution anywhere in the skill, and the one place that gestures at a source names nobody.**
Evidence: `SKILL.md:36-41` (the "one rule" table) has zero marker and zero named source.
`references/mixed-model-recipes.md:24`'s `*(community-convergent across named sources)*` is the only
gesture toward provenance for this exact claim, and it is itself a bare epistemic hedge — "named
sources" names no one in that sentence, which is precisely the pattern §6.2 flags ("settings
consensus," "recur across guides" etc. name nobody).
Fix: since named recipe authors already exist two sections below (`mixed-model-recipes.md §2` —
Cordina, Enzino, nsfwVariant, etc.), point at them explicitly rather than gesturing: replace
`mixed-model-recipes.md:24`'s marker with `` `[community — convergent across the named recipes in §2]` ``,
and add the same pointer as a table-header-scoped marker on `SKILL.md:36`'s "What the pass does"
column.

**[P2] Summarise-up hop: SKILL.md restates a specific community claim from `minimax-h3` without carrying its attribution (§6.2 consequence).**
Evidence: `SKILL.md:84` — "by multiple reports a better one than Krea 2 + Identity Edit,
Qwen-Image-Edit or Flux Klein 9B for character fidelity, 3D scene understanding, mirrors and
composition — around 8 s per edit on a 5090" is the same claim `minimax-h3/SKILL.md:280` makes,
there correctly marked `` `[community — Patient_Ratio4177]` ``. This skill drops the marker on the
summarise-up hop.
Fix: append `` `[community — Patient_Ratio4177]` `` before the em-dash-clause's closing period at
`SKILL.md:84`.

**[P2] Two more orphan actionable claims with no name and no marker.**
Evidence: `references/production-ladder.md:56-58` (tiled-upscale denoise 0.2–0.35, tile-size ≈
native res, seam-fix mode — the whole §4 core guidance) carries no marker at all (the section's only
marker, `*(Official repos.)*` at line 59, covers only the TTPlanet claim in the last bullet).
`references/production-ladder.md:92` ("Use sparingly or not at all with distilled/guidance-off
models" — PAG guidance) is also unmarked and unnamed.
Fix: add a heading-scoped marker on `## 4. Tiled diffusion upscale` (or name the actual convention
source, e.g. ssitu's own UltimateSDUpscale docs, if verified) and a sentence-scoped marker on the
PAG caution — repair agent should verify the actual source before publishing either marker rather
than defaulting to an unqualified `[community]`.

---

## Cosmetic

**[P3] Two-bar section omits the optional lede sentence (§6.3 item 1).**
Evidence: `SKILL.md:169` jumps straight to "**Hard facts — must be exact or it breaks.**"
Fix: prepend "This skill holds two kinds of claim to two different standards, because they fail in
two different ways." (7 of 10 sibling skills carry it; `comfyui-on-runpod`'s audit found the same
gap.)

**[P3] Frontmatter's boundary clause names only 4 of the 7 sibling model skills it now cross-references.**
Evidence: `SKILL.md:4` — "Model-specific numbers live in the z-image, sdxl, flux-2, and ideogram-4
skills" — omits `krea-2` (used throughout `mixed-model-recipes.md` and the suite map),
`wan-2-2` and `minimax-h3` (both extensively covered in the new video-as-image-stage material).
Fix: "Model-specific numbers live in the z-image, sdxl, flux-2, ideogram-4 and krea-2 skills; video
handoffs are wan-2-2 and minimax-h3 — this skill owns the craft that spans them."

**[P3] `mixed-model-recipes.md`'s Named Recipes table "Source" column uses inconsistent inline provenance phrasing instead of the bracket form.**
Evidence: `mixed-model-recipes.md:41-47` — "community, named" / "community, replicated widely (no
single canonical author)" / "community (\"Modern Easy SDXL...\", Civitai)" — three different
phrasings for the same tier, in a column that exists specifically to carry provenance. Lower
priority than the italic-parenthetical findings above because the named author is present in the
adjacent Recipe cell of the same row in most cases, satisfying §6.2's rule (c) — this is a
consistency nit, not a missing-attribution finding.
Fix: normalise the column to bracket form, e.g. `` `[community — Cordina]` ``, matching the
author already named in the Recipe cell.

---

## Beyond the rubric: the "image" framing verdict

**The MiniMax H3 one-frame case earns its place; the krea-2 "driving video" sentence doesn't yet.**

`SKILL.md:82-90` argues a video model is now a legitimate image-pipeline stage, and for MiniMax H3
at one frame the argument holds: the deliverable stays a still, the section explicitly folds the
operation into this skill's own rule 1 ("decode to pixels between families" — `SKILL.md:88`), and
the requirements (dedicated image VAE, exactly one frame) are framed as image-editor traps, not
video traps. A reader using this section never leaves image-domain work. This is correctly scoped
and should be kept as-is.

The weaker spot is one sentence at `SKILL.md:161`: "krea-2's Identity Edit is used to prepare the
**first frame of a driving video** for a character-swap model, which makes an image edit the first
step of a video job." This asserts scope ("the first step of a video job") without stating why that
first step still belongs to an *image*-production-workflows skill rather than being purely the
downstream video skill's business — and it conflates two different "backwards" directions under one
label: MiniMax-H3-as-image-editor is a video-*family checkpoint doing image work* (stays in this
skill's domain by output), while the krea-2 sentence is *image work whose output feeds a video job*
(the same forward direction the suite map already states for `wan-2-2`, just applied to a
not-yet-published character-swap model). Calling both "the ladder feeding backwards" muddies a
distinction the rest of the section gets right.

**Verdict: the framing survives, but the general principle it relies on is never stated, and should
be.** Recommended addition, as a lead-in sentence before the `### A video model is now a legitimate
stage in an image pipeline` subsection (`SKILL.md:82`):

> **The test is output modality, not training modality.** A checkpoint trained for video work still
> belongs to *this* skill's ladder whenever the stage it performs takes pixels in and puts pixels
> out — one frame, one edit, no motion. The moment a stage's output is a clip rather than a still,
> the job is `wan-2-2`'s or `minimax-h3`'s ladder, not this one, even if the input was prepared here.

This makes explicit why MiniMax-H3-at-one-frame is in scope and why the krea-2 sentence, despite
naming a "video job," is really describing where *this* skill's job ends rather than expanding what
it covers. No rename needed; this is a scope-of-argument fix, not a scope-of-content fix.

---

## New skill landing: `anima`

Checked against the three skills being authored in parallel per the task brief. Only `anima` (2B
anime specialist, Qwen3-0.6B LLM-adapter encoder, tag-dialect prompting, ~6 GB VRAM,
**non-commercial licence**) is image-relevant; `ltx-2-5` and `scail-2` are video and belong to the
video skills' own suite maps, not this one.

Draft suite-map row (do not add yet — `anima` isn't published, per CLAUDE.md's registration gate):
```
| **Anima** (announced, not yet published) | anime specialist, 2B, tag-dialect prompting, ~6 GB VRAM — **non-commercial licence** | plausible anime-style front-end alongside the SDXL-family finetunes (Illustrious/Pony/NoobAI); **not** a realism-refine candidate — the model is explicitly "not for realism" |
```

**The licence interaction worth flagging now, before anima lands:** every named recipe in this skill
composes a *chain*, and a non-commercial checkpoint anywhere in a chain that must ship commercially
poisons the whole pipeline's output rights (the same logic `minimax-h3`'s territory clause and
`ideogram-4`'s non-commercial weights already impose per-model). Concretely: Anima would be safe as
an early exploratory/style-reference stage in a pipeline that *finishes* on a commercially-clean
model (klein 4B, SDXL with a commercial checkpoint), but unsafe as the pipeline's last stage if the
output needs to be sold. When `anima` is authored, this skill's boundary table (once added, see the
first Blocking finding) and suite map should carry that constraint explicitly rather than leaving it
implicit in "non-commercial licence."

---

## Checked and clean: the LoRA-training routing bug

The `character-lora-training` audit found several model skills citing `z-image`'s
`lora-training.md` as authoritative instead of routing to the cross-cutting
`character-lora-training` skill. This skill does not repeat that bug: its only LoRA-training-adjacent
pointer, `references/workflows-as-code.md:78`, correctly links
[`character-lora-training/references/evaluation-and-tooling.md`](../../character-lora-training/references/evaluation-and-tooling.md)
for batch-QC protocol, and nowhere does it cite a model skill's `lora-training.md` as the fuller
treatment. No finding.

---

## N/A (model-skill-only checks, per task brief)

Selector table, per-variant/per-mode settings, four §4.1 core reference slots (this skill's 3
reference files have no prescribed names per §4.3's last line), `## Licence & limitations`,
train/use LoRA boundary (this skill correctly never attempts to own LoRA training), §6.5's
image/video required suite-table axes (this skill's own suite map is the hub table, not a
per-model "reach for instead" table — JD#10). Gate section (§3.3): no legal/policy/cost
precondition rules the reader out of this craft entirely. `## Contents` TOC requirement (§6.7):
none of the three references reach 2,000 words, yet all three carry one anyway with correctly
numbered `## N.` headings matching their TOCs — exceeds the requirement, no finding either way.

---

## Registration (checks 39-41)

- **PASS** — registered in `.claude-plugin/marketplace.json:37` and `README.md:27` with an accurate
  description.
- **PASS (with the contingent gap above)** — `freshness.json` carries tier `active` (14-day
  cadence), a substantive `why_tier`, `linked_skills`, 6 watchlist items and 4 open findings (1
  minor-unresolved re: the SeedVR2-tiling combo node, appropriately low-urgency; 3 resolved,
  including today's video-as-image-stage addition). All watchlist `where` pointers still resolve to
  real sections after today's edits. The two watchlist entries this audit calls for (flagged/contested
  claims) are the only gap — see the contingent Blocking finding.

---

## Depth verdict

**PASS, no finding.** Corpus 6,065 words is inside the cross-cutting band (5,000–10,000). SKILL.md
is 2,574 words of body content (2,785 incl. frontmatter) — inside the 2,000–3,200 absolute cap, and
inside the 2–4 reference-file count (3). The 42% SKILL.md share the task brief flagged is **not**
itself a violation: §5.2 sets a percentage band only for *model* skills; cross-cutting skills get
absolute caps only, and this skill sits inside both of them. Each reference (953–1,168 words) is
inside the 700–3,500 band. No section reads as padding under the §5.3 test — every section
(including the new video-as-image-stage material) changes what the reader does or routes them
somewhere concrete.

---

## Do not touch

- `## Tool status that changed recently (mid-2026)` — the correctly-triggered §3 item 6 conditional
  (craft depends on churning third-party tooling). Do not fold into the craft body or remove.
- The video-as-image-stage and generative-upscaling-vs-restoration subsections — legitimate scope
  per the framing verdict above. Tighten the framing sentence; do not cut the content.
- `## The suite map` staying unique to this skill (JD#10) — do not ask sibling skills to duplicate
  it; do not remove it here.
- The three reference filenames (`mixed-model-recipes.md`, `production-ladder.md`,
  `workflows-as-code.md`) — cross-cutting skills have no prescribed reference-file names (§4.3).
- Prose-over-table choices in "Mixing models" and "Tool status" — correct per §6.6, these are
  mechanism/status narration, not parallel-structure data.
