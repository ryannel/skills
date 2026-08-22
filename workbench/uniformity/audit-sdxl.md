# Uniformity audit — `sdxl`

Graded against `workbench/uniformity/STANDARD.md` §8. Skill: `skills/generative-media/sdxl/`
(SKILL.md 243 lines / 4,143 words; references 9,857 words; corpus 14,000 words, 29.6% SKILL.md share
— both inside target bands, no depth finding). Not touched in the 2026-08-22 refresh; `freshness.json`
`last_checked: 2026-08-13`, tier `stable`, cadence 30d.

---

## Blocking

**[P1] SKILL.md — suite table — every published-sibling mention is a bare code span, not a link (check 33).**
Lines 149, 192, 196, 197, 198, 199 all use `` `flux-2` ``, `` `z-image` ``, `` `krea-2` ``,
`` `wan-2-2` ``, `` `ideogram-4` ``, `` `image-production-workflows` `` instead of
`[`name`](../name/)`. This is the exact pattern STANDARD.md names sdxl for. Fix — convert all six:
`149: the **[\`image-production-workflows\`](../image-production-workflows/)** skill.`
`192: | \`flux-2\` for native multi-reference editing` → `[`flux-2`](../flux-2/) for native multi-reference editing`
`196: | \`flux-2\` or \`z-image\`` → `[`flux-2`](../flux-2/) or [`z-image`](../z-image/)`
`197: | \`krea-2\` — one model…` → `[`krea-2`](../krea-2/) — one model…`
`198: | \`image-production-workflows\` for the cross-model craft` → `[`image-production-workflows`](../image-production-workflows/) for the cross-model craft`
`199: | \`wan-2-2\` — image-to-video…` → `[`wan-2-2`](../wan-2-2/) — image-to-video…`
`242: (\`references/lora-training.md\`) — using is checkpoints-and-loras §4` — internal ref, not a sibling; no change needed there.

**[P1] SKILL.md:229 — Turbo's contested licence stated in prose with no marker (check 26).**
Exact text: *"SDXL is old, so these move slowly — but Turbo's licence (above) is the exception."* This is
the literal sentence STANDARD.md quotes as needing repair. Fix: `…but Turbo's licence (above) is the
exception \`[contested]\`.` Also add the same marker to the licence table row, SKILL.md:213:
`| **SDXL Turbo** | **contested** — see below | ⚠️ Verify |` → `| **SDXL Turbo** | **contested** — see
below \`[contested]\` | ⚠️ Verify |`.

**[P1] SKILL.md — two-bar section has no "Contested / unresolved points" bullet list at all (checks 24, 26, 32).**
Section runs lines 225–232 (lede → hard-facts para → craft para → straight to `## Reference files`).
§6.3 requires a bullet list of contested/flagged points, each carrying its marker; §6.2's floor requires
SKILL.md to carry ≥1 `[flagged]`/`[contested]` marker or an explicit "nothing flagged" line. SKILL.md
currently has **zero** bracket markers (confirmed by grep). Fix — insert before `## Reference files`
(after line 231, i.e. before line 233's `---`):
```
**Contested / unresolved points.**
- Turbo's licence: `LICENSE.md` permits commercial use under $1M revenue, but the HF repo's metadata
  tag and model-card prose still read non-commercial. `[contested]`
- Character-LoRA rank: the classic 8–16 ladder vs. named trainers' 48/48-default, 48–64-when-forgetting
  practice — both defensible, not averaged. `[contested]` (full treatment: `references/lora-training.md §3`)
- Anima as an anime-finetune base: gaining momentum as "the new Illustrious," but most published LoRAs
  for it are still poorly trained. `[flagged — re-verify]` (`references/lora-training.md §1`)
```

**[P1] SKILL.md — two-bar section has no date line at all (check 25).**
The section's only date-shaped statement is the model's *release* date, inside `## Licence &
limitations` (line 221: "SDXL 1.0 shipped 26 July 2023"). Nothing in the skill records when the skill's
*claims* were last checked. Fix — add as the final paragraph of the two-bar section (after the new
contested list above):
```
**Facts dated 2026-08-13**; community craft not independently refreshed since. The fast-moving layer —
finetune version numbers, Turbo's licence status, and Anima's trajectory as an Illustrious challenger —
is what to re-verify first.
```
(Date matches `freshness.json`'s `last_checked` for this skill.)

**[P1] Italic-parenthetical / inline-label provenance markers — 14 instances, none greppable (check 27).**
The largest single fix in this file, and the one the audit brief calls out as highest-value. All convert
mechanically to backticked bracket form per §6.2. Full list with exact text and fix:

| # | Location | Current | Fix |
|---|---|---|---|
| 1 | `SKILL.md:145` | `*(community — Civitai workflow authors)*` | `` `[community — Civitai workflow authors]` `` |
| 2 | `references/characters.md:13` | `*(community consensus — it displaced FaceID as the go-to)*` | `` `[community — displaced FaceID as the go-to consensus]` `` |
| 3 | `references/characters.md:15` | `*(official repo; community validation growing)*` | `` `[official — ByteDance HyperLoRA repo]`; `[community — validation growing]` `` |
| 4 | `references/characters.md:19` | `*(community consensus, convergent across named head-to-heads — MyAIForce's comparisons are the best citable)*` | `` `[community — MyAIForce comparisons; convergent]` `` |
| 5 | `references/characters.md:25` | `*(community, strong — WeirdWonderfulAI, Mickmumpitz, Civitai dataset guides)*` | `` `[community — WeirdWonderfulAI, Mickmumpitz, Civitai dataset guides; strong]` `` |
| 6 | `references/characters.md:40` | `*(community, strong — MyAIForce's ADetailer and FaceDetailer writeups are the clearest named sources)*` | `` `[community — MyAIForce ADetailer/FaceDetailer writeups; strong]` `` |
| 7 | `references/characters.md:48` | `*(Official ADetailer discussion #533.)*` | `` `[official — ADetailer discussion #533]` `` |
| 8 | `references/characters.md:54` | `*(Community, strong — Civitai article 5301; Inspire Pack docs.)*` | `` `[community — Civitai article 5301, Inspire Pack docs; strong]` `` |
| 9 | `references/characters.md:63` | `*(Community, strong — Khanykov01, Civitai 6990.)*` | `` `[community — Khanykov01, Civitai 6990; strong]` `` (this is STANDARD.md's own worked example) |
| 10 | `references/characters.md:83` | `**named-community, convergent** (MyAIForce, Civitai 5301/6990, dataset guides)` | `` `[community — MyAIForce, Civitai 5301/6990, dataset guides; convergent]` `` |
| 11 | `references/setup-and-workflows.md:31` | `**VAE gotcha (community, well-established):**` | `**VAE gotcha** \`[community — well-established]\`:` |
| 12 | `references/setup-and-workflows.md:85` | `…"blows things up" (community).` | `…"blows things up" \`[community]\`.` |
| 13 | `references/setup-and-workflows.md:137` | `**Tiled upscale (community):**` | `**Tiled upscale** \`[community]\`:` — this is the literal example STANDARD.md's check 27 cites |
| 14 | `references/setup-and-workflows.md:167` | `**VRAM (community):**` | `**VRAM** \`[community]\`:` |

Total: **14 instances** (9 canonical `*(…)*` italic-parenthetical, 5 inline-label variants — matches
STANDARD.md's `~15` estimate for sdxl). None are in SKILL.md itself except #1; the rest are in
`characters.md` (8) and `setup-and-workflows.md` (4).

**[P1] `references/lora-training.md:175` — malformed marker, not previously documented (check 28).**
`` `[community — QuantumBogoSort, `ai-toolkit-perceptual` fork]` `` nests a backtick code-span
(`` `ai-toolkit-perceptual` ``) inside a backtick-wrapped bracket marker. Markdown does not nest single
backticks: this renders as two separate `<code>` spans with `ai-toolkit-perceptual` as plain text
between them, and splits the marker's `[` from its `]`. Invisible to any freshness grep. Fix: drop the
inner backticks — `` `[community — QuantumBogoSort, ai-toolkit-perceptual fork]` ``. This is a new
instance beyond the two STANDARD.md already names in krea-2/wan-2-2 — add it to that list.

**[P1] `SKILL.md:165` — failure-table cause cell restates the symptom instead of stating a mechanism (check 5).**
`| Mangled hands, extra fingers | Classic SD weakness | Negative \`extra fingers, deformed hands\`;
inpaint/ControlNet the hands; re-roll |` — "Classic SD weakness" names nothing. Fix: `| Mangled hands,
extra fingers | High intra-class variance and frequent self-occlusion in hand poses, versus a
comparatively narrow range of well-lit, unoccluded faces in the training data | Negative \`extra
fingers, deformed hands\`; inpaint/ControlNet the hands; re-roll |`

---

## Standard

**[P2] Two-bar craft paragraph names no individual community sources (check 24).**
`SKILL.md:231` — *"The authoritative source here is the community — the finetune authors, Civitai model
pages, and practitioners who've run these checkpoints for years"* — describes roles, not people, even
though the references this section summarises name specific authors extensively (neonkisu,
QuantumBogoSort, MyAIForce, WeirdWonderfulAI, Mickmumpitz, Ainara, L3n4, RONK234, NanashiAnon,
Khanykov01). This is the "summarise-up hop" STANDARD.md names generically for this skill; here is the
specific instance. Fix — extend the sentence: *"…practitioners who've run these checkpoints for years
(neonkisu, QuantumBogoSort, and MyAIForce among the most-cited)."*

**[P2] Two-bar hard-facts paragraph is missing the required re-verify clause (check 24).**
`SKILL.md:229` ends *"…a misread licence is a legal problem. SDXL is old, so these move slowly — but
Turbo's licence (above) is the exception."* §6.3 point 2 requires the volatility note to close with
**"re-verify before relying on them, regardless of who said it."** verbatim-in-spirit. Fix: append after
"the exception `[contested]`." → *"Re-verify before relying on them, regardless of who said it."*

**[P2] Anima is absent from SKILL.md entirely, though it already exists two layers down (staleness — see below).**
Detailed in the Beyond-the-rubric section; treated as P2 here because it is a real content gap in the
mandatory selector table, not just a freshness note.

**[P2] `SKILL.md:101–111` "## Per-variant settings" is a flat bullet list, not `###` blocks (check 6).**
§2 slot 6 specifies "One `###` block per variant/mode." sdxl's six variants (Base 1.0, Base+Refiner,
Turbo, Lightning, LCM, Hyper-SDXL) are each a `-` bullet with a bolded name, not a `###` heading — the
only model skill in the suite doing it this way (no §7 justification covers it). None of the six bullets
states seed behaviour either, though the spec requires it per variant. Fix: promote each bullet to
`### Base 1.0`, `### Base + Refiner`, `### Turbo`, `### Lightning`, `### LCM`, `### Hyper-SDXL`, keep the
existing content, and add one clause on seed behaviour per block (e.g. Base: "seed is fully
deterministic at fixed sampler/scheduler"; Turbo/Lightning/LCM/Hyper: "same seed reproducible only if
step count and scheduler match exactly").

**[P2] Suite table is missing 2 of the 8 required image-skill axes (check 35).**
`SKILL.md:190–199` covers characters, style-LoRA ecosystem, structural control, typography,
compositional prompts, stylistic range, mixed-model pipelines, making-it-move — 6 of 8 (folding
"stylistic range" in for one of the two extra rows the spec allows). Missing: **(5) photoreal faces/skin
— or the model's own headline aesthetic axis**, and **(6) commercial use under the licence**. Both have
obvious content already in the skill (the Realism section; the Turbo-vs-base licence split) that just
never made it into the table. Fix — add two rows:
```
| Photoreal faces & skin | **The headline strength once you leave raw base** — a photoreal finetune (Juggernaut/RealVisXL) + `detailed skin` + camera/film vocabulary | `krea-2` if you want the look without checkpoint-hopping |
| Commercial use under the licence | Base/Lightning/Hyper-SDXL are clean OpenRAIL++-M, no cap; **Turbo is contested** `[contested]` — verify before shipping | — |
```

**[P2] Orphan craft numbers with no named source and no marker (check 29).** Confirmed instances:
- `SKILL.md:62` — weight band `~1.05–1.3` stated flatly with no source. Fix: cite it once, e.g. append
  `` `[community]` `` or fold the attribution from `prompting-guide.md §2` up.
- `SKILL.md:138–141` — the five-rung production ladder (denoise 0.3–0.5, ~0.4, 0.2–0.35) carries no
  attribution, while the mixed-model patterns twelve lines below (line 145) do get one (once converted,
  `[community — Civitai workflow authors]`). Fix: extend that marker's scope to cover the ladder, or add
  a second one at the end of the ladder.
- `references/setup-and-workflows.md:138` — *"Settings consensus: `guide_size` 512, `max_size` 1024,
  `bbox_crop_factor` ~1.3–2…"* — "settings consensus" names nobody. Fix: `` `[community]` `` after the
  numbers, or name a source.
- `references/lora-training.md:62` — the classic rank-by-type ladder row carries no marker while the row
  directly beneath it in the same table (`references/lora-training.md:63`) carries
  `` `[community — neonkisu, QuantumBogoSort]` `` — the asymmetry looks like the first row is a hard
  fact when it's the same kind of claim. Fix: add `` `[community]` `` to the first row, or name its
  source if one exists.
- `references/lora-training.md:56` "dominates Pony/Illustrious practice", `:70` "long-standing
  SDXL/Illustrious style anchor", `:135` "recur across guides" — three bare epistemic hedges, the exact
  vocabulary §6.2 calls out as not-attribution. Fix each with `` `[community]` `` or a name.
- `references/lora-training.md:164` — `` `[named — Civitai 25645]` `` uses a retired tier token. Fix per
  §6.2's explicit mapping: `` `[community — Civitai 25645]` ``.
- `references/checkpoints-and-loras.md:67` — *"(community starting points — always read the LoRA's own
  card…)"* is a bare parenthetical hedge on the whole weight-by-type table, same shape as the italic-paren
  markers but unitalicized. Fix: `**Weight by LoRA type** \`[community]\` (always read the LoRA's own
  card; authors publish a tested weight and trigger):`

---

## Cosmetic

**[P3] `references/characters.md:83` — `[official]` marker not backticked (check 31).**
`"…are **[official]** from the respective repos"` — every other marker in this skill is backticked
(confirmed: 24/24 in `lora-training.md`). Fix: `` `[official]` ``.

**[P3] TOC heading text wrong on 3 files, missing entirely on a 4th (check 12).**
`references/prompting-guide.md:5`, `references/checkpoints-and-loras.md:5`,
`references/setup-and-workflows.md:5` all read `## Table of contents` — canonical is `## Contents`.
`references/lora-training.md` (3,424 words, over the 2,000-word TOC threshold, and SKILL.md deep-links
it) has no `## Contents` heading at all — its numbered list starts cold at line 9, right after the
file's intro paragraphs. Fix: rename the three headings; add `## Contents` above `lora-training.md`'s
existing numbered list (the list itself is already correctly formatted, just unheaded).

**[P3] `SKILL.md:39` — checkpoints table column header is "For", not "Use when…" (check 4).**
The speed-variant table two sections up (line 24) correctly uses "Use when…"; the checkpoints table's
"For" column carries the same content shape. Fix: rename the header to "Use when…" for consistency
across sdxl's two composable-axis tables — content in the cells needs no change.

**[P3] Frontmatter description has no explicit closing sweep (check 22).**
`SKILL.md:4` ends on licence content ("It also covers the licence picture…") rather than the canonical
closing sentence. Minor — the description is otherwise complete and inside the 180–320-word band (248
words). Fix if touching this file anyway: append *"Use this for any question about SDXL in any
context."* after the existing final sentence.

---

## Beyond the rubric

### 1. Unattributed craft (actionable claims, no marker, no named source in-sentence)
Covered above under Standard/orphan-numbers — the full list is: `SKILL.md:62` (weight band),
`SKILL.md:138–141` (denoise ladder), `setup-and-workflows.md:138` ("settings consensus"),
`lora-training.md:56,62,70,135` (bare hedges / unmarked ladder row), `checkpoints-and-loras.md:67`
(weight-by-type table). No new instances beyond what's listed there.

### 2. Staleness — this is the significant one for sdxl

**Anima is the headline finding.** The suite is actively authoring an `anima` skill for a 2B anime model
that is now the third-largest base-model ecosystem on Civitai and competes directly with SDXL's
anime finetunes (Pony/Illustrious/NoobAI). Tracing sdxl's own files:

- `references/lora-training.md:34` already carries a full table row for Anima as a training base
  ("Newer, gaining momentum… named trainers describe it as becoming 'the new Illustrious'"), correctly
  marked `` `[flagged — re-verify]` ``.
- `references/lora-training.md:106` already folds Anima into the booru-dialect caption instruction
  ("booru tags for Pony/Illustrious/NoobAI/Anima").
- `freshness.json:326` (the `sdxl-nsfw-base-lineages` watchlist entry) already tracks Anima explicitly
  and flags its status as unresolved.
- **But `SKILL.md` never mentions Anima at all.** Not in the "Checkpoints (the style axis)" selector
  table (`SKILL.md:39–46`, which lists only Juggernaut/RealVisXL/DreamShaper/Pony/Illustrious-NoobAI),
  not in the two-bar craft roll-call, not in the suite-positioning table. A reader who only reads
  SKILL.md — which is most readers, by design — has no idea Anima exists as a fifth checkpoint family or
  as emerging competition for the anime axis.

This is exactly the "summarise-up hop" failure mode STANDARD.md's §6.2 describes generically, caught in
the wild: the fact travelled two directories deep (`lora-training.md`, `freshness.json`) and never made
it to the one file every reader loads. **Once the `anima` skill publishes**, sdxl will need: (a) a row in
the checkpoints table naming Anima as a fifth style-axis option with its own dialect/LoRA-pool caveat,
matching the treatment Pony/Illustrious already get; (b) a cross-link
`[`anima`](../anima/)` in the suite table under a "Anime finetune ecosystem" or similar axis, framed as
"reach for `anima` when the anime-specific base itself, not an SDXL finetune, is what's wanted"; and
(c) the existing `lora-training.md` Anima row should gain a forward pointer to the new skill once it
exists. **Until `anima` ships, the fix is smaller: at minimum add Anima to the SKILL.md checkpoints table
now** (it's already vetted craft, sourced and flagged in the reference) so the table stops being
inconsistent with the file two clicks away from it.

**Finetune-leadership churn (Pony/Illustrious/NoobAI):** already appropriately hedged. `lora-training.md
§1` presents four anime bases side by side with named caveats and two markers
(`[community — re-verify]`, and the Anima flag above); `freshness.json`'s `sdxl-nsfw-base-lineages` entry
explicitly asks "have newer Illustrious/NoobAI/Anima versions displaced these?" on every check cycle.
No SKILL.md-level claim asserts a single leader without qualification. **No new finding beyond the Anima
gap above.**

**VRAM advice:** checked specifically per the brief. `SKILL.md:95` and `setup-and-workflows.md:167` both
give "~4 GB low-VRAM, 6–8 GB comfortable, 8 GB+ for base+refiner." These numbers are a function of
SDXL's fixed 2.6B UNet, not of any particular GPU generation — SDXL's compute/memory footprint hasn't
changed since 2023, so this isn't dated by newer-hardware assumptions the way, say, a training-VRAM
recommendation calibrated to an old top-end card would be. **No finding** — flagged as checked, not
stale.

**Positioning against newer suite models:** `SKILL.md:129`'s strengths/weaknesses paragraph ("ecosystem
depth… weaknesses are in-image text, complex/compositional prompts, hands/anatomy") is architecture-
derived and doesn't make a comparative claim that could be falsified by a new model joining the suite.
The suite table (`SKILL.md:188–199`) already correctly routes typography to `ideogram-4`, compositional
prompts to `flux-2`/`z-image`, and stylistic range to `krea-2`. **No finding** beyond the two missing
axes already flagged under Standard.

### 3. Over-conformity risk — do not touch

1. **The "Two orthogonal axes — they compose" section and its two-table structure**
   (`SKILL.md:13–47`) — explicitly justified by STANDARD.md §7 item 6. Do not merge the speed-variant
   and checkpoint tables into one `## Variant selector`; the two axes genuinely compose and a reader
   needs to pick a point on each independently. The heading name deviating from the canonical
   "## Variant selector" is part of the same justified deviation — it names the actual mechanism instead
   of using the template heading, which is exactly what §2's guidance for slot 7 asks headings to do
   elsewhere in the spec.

2. **`references/checkpoints-and-loras.md`'s filename** — do not rename or fold into
   `setup-and-workflows.md` or `prompting-guide.md`. It is explicitly named in STANDARD.md §4.2's
   canonical extras list as sdxl's own dedicated slot ("only for a model whose ecosystem *is*
   third-party checkpoints (`sdxl`)") and reconfirmed in §7 item 5. SDXL's finetune ecosystem (Pony,
   Illustrious/NoobAI, Juggernaut, RealVisXL, DreamShaper, plus the separate LoRA pools each family
   carries) has no equivalent anywhere else in the suite; forcing it into a generic slot would either
   bloat `setup-and-workflows.md` past its depth target or scatter ecosystem-specific dialect rules away
   from the LoRA-pool-matching rules they're inseparable from.

3. **The already-well-surfaced silent-failure traps in SKILL.md** — the CFG-1-vs-CFG-0 ComfyUI/diffusers
   gotcha (`SKILL.md:33`), the fp16 VAE black-image trap (`SKILL.md:86`), and the crop-/size-conditioning
   traps in the failure table (`SKILL.md:160–161`) are all correctly at the SKILL.md layer per §5.4's
   silent-failure test (wrong value → plausible wrong image, not an error). Any repair pass shortening
   SKILL.md must not push these into a reference file.

4. **The dueling-sources treatment of contested craft** — `references/lora-training.md §1` (base choice)
   and `§3` (rank) present two named, defensible positions side by side rather than averaging them into
   a single number. This is exactly the practice STANDARD.md §6.6 praises ("worth understanding rather
   than averaging away"). Keep it, including after the markers above are added to the currently-unmarked
   row — do not collapse the table to one row.

5. **`references/characters.md`'s `[SEP]` multi-character routing and block-weight style-bleed fix**
   (`§3–4`) — genuinely SDXL-unique (the block concentration finding has no DiT-model equivalent). Do
   not trim this for length; it's the kind of model-specific mechanics slot 8 exists for.

---

## Registration (§E)

- **Check 39** — PASS. Registered in `.claude-plugin/marketplace.json` (`skills` array,
  `./skills/generative-media/sdxl`) and in `README.md:21`.
- **Check 40** — PASS. Present in `freshness.json:298–…` with `tier: stable`, a `why_tier` explaining the
  frozen-architecture/moving-ecosystem split, and a watchlist covering Turbo's licence, finetune
  versions, trainer status, the Anima/base-lineage question, and the rank dispute — i.e. it already
  includes every contested/flagged claim this audit found (Anima, Turbo, rank), just not yet reflected
  as markers in SKILL.md itself.
- **Check 41** — mostly PASS. `freshness.json:311`'s `turbo-licence` entry cites `"SKILL.md ~L211-215"`;
  current location is closer to lines 213 (table row) and 229 (prose) after this file's edits accumulated
  since that watchlist entry was written. Minor drift, not urgent — update the line pointer if this audit's
  fixes are applied, since line 229 is where the `[contested]` marker lands.
