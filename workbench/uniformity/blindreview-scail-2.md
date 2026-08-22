# Blind review — `scail-2`

Reviewed 2026-08-22 against `skills/generative-media/scail-2/` (SKILL.md 313 lines / ~5,498 w;
`setup-and-workflows.md` ~3,525 w; `characters.md` ~2,738 w; `prompting-guide.md` ~2,365 w),
`workbench/uniformity/STANDARD.md`, and the published siblings. No research material was consulted.

---

## Verdict

**SHIP WITH FIXES.** The scaffolding is the best in the suite — every §2 slot present in order, every
verbatim heading byte-exact, the two-bar section in the right slot with a real contested list, the
`lora-training.md` omission correctly exempted *and* argued rather than silently dropped. The prose is
genuinely good: it explains mechanisms instead of listing settings, and it is honest about what it does
not know. But it is not shippable as it stands for three reasons, in descending order. First, **it is
registered nowhere** — absent from `.claude-plugin/marketplace.json`, absent from the README table,
absent from `freshness.json`, which per CLAUDE.md means it is not published at all. Second, **a reader
cannot complete the job from it**: the skill declares masks the control surface and then never says
which of its three masks the black/white/colour semantics govern, never says how to make the reference
foreground mask its own one rule depends on, never names the ComfyUI repack repo the file-layout table
implies, and introduces "the Identity Tracker" — the fix for two failure-table rows — with no pack, no
author, no repo. Third, **the worked zoom-crop recipe emits a resolution the skill's own divisibility
rule forbids** (720×1280; 720 is not a multiple of 32). Fix those and this is a strong sibling; two of
the three are small edits, and the mask disambiguation is the one that needs the author to go back to
a source.

---

## Could I execute?

Walking it as a practitioner with a driving clip and a reference photo of a different person.

**Steps that work.** The routing is clear and I never wondered what to do next at the *strategy* level.
I know to extract frame 0, edit my person into it with an image-edit model, feed the edited still as
the reference and the *unedited* clip as motion (SKILL.md:42–57). I know the mode I want is Replacement,
that the prompt barely matters, that fps and length come from my input, and that I should keep the shot
under ~161 frames. That is a real accomplishment and most of the value of the skill.

**Sticking point 1 — I cannot download the model.** SKILL.md:85 names
`wan2.1_14B_SCAIL_2_fp16.safetensors` "(or an fp8 / GGUF repack)" but no host. SKILL.md:88 gives the
CLIP vision tower as an ellipsis — `…xlm-roberta-large-vit-huge-14-onlyvisual…` — which is not a
filename I can search for with confidence. SKILL.md:95 names `zai-org/SCAIL-2` on HF, but that is the
*original* release, not the ComfyUI repack the loader-node table assumes. SKILL.md:93 then hedges the
whole table away: "repack filenames beyond the core one move with the packaging, so take those from the
official tutorial page `[flagged — re-verify]`". Compare `wan-2-2/SKILL.md:61`, which opens its file
layout with "Download the ComfyUI-repackaged files from the `Comfy-Org` Hugging Face repos" and then
gives exact filenames. The sibling solved this; this skill did not.

**Sticking point 2 — I cannot make the reference foreground mask.** It is an input in the selector
table (SKILL.md:31), a rail in the graph (`setup-and-workflows.md:33`), and step 6 of the one-rule
procedure — where it is the whole instruction: *"Generate the reference foreground mask from the edited
still"* (`setup-and-workflows.md:59`). No node, no tool, no method. SAM3 on a still? `sam3_image_object`?
Rembg? The skill mentions all three families elsewhere and connects none of them here. This is a hard
stop on the skill's own critical path.

**Sticking point 3 — I do not know which mask the semantics describe.** The skill stakes its structure
on masks (SKILL.md:61–71) and states one three-valued table: black = background not visible, white =
background visible, colour = character↔motion correspondence (SKILL.md:65, repeated
`setup-and-workflows.md:84–90`). But there are **three** distinct masks in play — the reference
foreground mask, the per-frame driving mask, and the replacement-region mask — and the semantics are
never attached to any of them. Worse, the two halves of the table describe different kinds of object: a
binary background flag and a coloured correspondence encoding. If `SCAIL2ColoredMask` generates the
driving mask automatically from a SAM3 track, what widget do I use to set black versus white? Nothing in
either file answers this. So the section that exists to stop the silent mode-collapse tells me to get
something right without telling me where the knob is.

**Sticking point 4 — "the Identity Tracker" appears from nowhere.** SKILL.md:207,
`setup-and-workflows.md:96` and `characters.md:112` all instruct me to "clear `object indices` to an
empty field and set selection to **Point**". That is the stated fix for tracker-refusal *and* for the
multi-person artefact, and it is called "the community Identity Tracker" once
(`setup-and-workflows.md:96`) with no repo, no author, no install line. Likewise SKILL.md:89 lists
"SAM3 tracking weights → per the SAM3 nodes' own convention → SAM3 loader": the skill never says whether
SAM3 nodes are ComfyUI core (as the SCAIL nodes are) or a custom pack, and never names the pack.

**Sticking point 5 — how do I actually switch to Replacement mode?** The selector says Replacement takes
"a **replacement-region** mask" in place of the driving mask (SKILL.md:33). Does it enter through the
same `WanSCAILToVideo` input? Is it also built by `SCAIL2ColoredMask`, or is it a plain binary SAM3
mask? `setup-and-workflows.md:100` restates the swap and answers neither. For a skill whose headline
job is replacement, this is the wiring question that matters most.

**Sticking point 6 — two named fixes point at unlocatable nodes.** The "**SCAIL Auto Extend**" sampler
is the fix for inter-segment colour shift (SKILL.md:214, `setup-and-workflows.md:182`). A node called
`SCAILExtension` is listed once at `setup-and-workflows.md:24` and never mentioned again. Are they the
same thing? Also unnamed: the "flow-matching shift node" (`setup-and-workflows.md:30`) — `wan-2-2`
names `ModelSamplingSD3` outright — and whatever node performs the 81/76 chunking (SKILL.md:167).

**The conceptual gap I could not resolve.** The one rule says the reference should *be* the driving
clip's edited frame 0 — so the reference's background **is** the plate. Animation mode is described as
producing a new scene and Replacement as preserving the original. If the reference is the plate, what
distinguishes the two, and why is Animation "**the recommended default** `[official]`" (SKILL.md:31)
for a reader following a community rule that appears to collapse it into Replacement? The skill asserts
both propositions eleven lines apart and never reconciles them. I would run the wrong mode.

---

## Contradictions

| Claim A | Claim B | Which is likely right |
|---|---|---|
| "Resolution \| **512p or 704p**" `SKILL.md:110` | "The practical ceiling is treated as **720p**" `SKILL.md:168` | **A.** 704p is the vendor figure and it also satisfies the /32 rule; 720p is `[flagged]` community treatment. Adjacent contradiction inside one file — reconcile explicitly ("704p documented; some practitioners push to 720p, which breaks /32"). |
| "Use multiples of 32" `SKILL.md:114`, `SKILL.md:226`, `setup-and-workflows.md:46` | "Pre-crop … into a **720×1280** clip. Generate at 720×1280" `setup-and-workflows.md:171–172` | **A.** 720 ÷ 32 = 22.5. The recipe also exceeds the 512p/704p band. Almost certainly should read **704×1280**, which is the README's own worked example (`setup-and-workflows.md:46`). A reader following §6.2 literally types an invalid resolution. |
| "Use multiples of 32" (as above) | "a ceiling around 285 frames of **972×1728** input" `setup-and-workflows.md:180` | **A.** 972 is divisible by neither 32 nor 16. Either the quoted figure is mis-transcribed or it silently refutes the divisibility rule two files over. Unremarked either way. |
| "`<Subject 1> is woman in <Picture 1> with redhead and black tank top.`" `prompting-guide.md:151` | "`<Subject 1> is the woman in <Picture 1> with red hair and a black tank top.`" `minimax-h3/SKILL.md:295` | **B.** Same quoted artefact, two transcriptions, plus scail-2 adds `(appears in [Shot 1])` annotations and drops the `overall_soundscape`/`non_diegetic_music` lines. One of them is wrong; the block belongs to the sibling and should be linked, not re-typed. |
| "a hard latch failure past **~7 s** `[community — Mediocre-Toe3212]`" `SKILL.md:255` | "subject matching in Ref2V degrades sharply past **~5 s**" `minimax-h3/SKILL.md:325` | **Unresolved.** Two different authors, two numbers, for the same H3 behaviour, in two skills that link to each other. Whichever survives, the suite should carry one figure. |
| The one rule "appears in **zero** official zai-org documents — not either branch README, not the paper, **not the ComfyUI tutorial**" `SKILL.md:44` | "not a substitute for the template's own node inventory and default widget values `[flagged — re-verify]`" `setup-and-workflows.md:22`; "take those from the official tutorial page `[flagged — re-verify]`" `SKILL.md:93` | **B is the honest one.** An exhaustive negative over a source the skill twice concedes it has not fully read. Soften A to name what was actually checked. |
| Licence split carries three/two independent confirmations, `[official]` `SKILL.md:268–269` | Same split carries `[flagged — re-verify]` `setup-and-workflows.md:225` | **A**, for the *fact*. SKILL.md correctly scopes its flag to *why the split exists* (`SKILL.md:271`); the reference lets the flag swallow the fact. Fix the reference's marker scope. |
| "### Stock node settings — Defaults from the repo's own **generation flags** `[official]`" `SKILL.md:99–101`, incl. "Frames \| **81** (`--max_frames 81`)" | STANDARD §2 slot 5: "**Stock node settings** (verbatim from template JSON, labelled as verbatim)" | **B is the standard.** These are CLI flags presented under a node-settings heading. A reader who loads the official template will see different widget defaults and will not know which wins — and `setup-and-workflows.md:22` says the template's defaults were never read. |
| "stay under **~161 frames** per shot unless the shot is easy" `SKILL.md:170` | The 16 GB VRAM anchor is "**253 frames** in ~9 min on a 4060 Ti" `SKILL.md:118`, `setup-and-workflows.md:112` | **Both, but unremarked.** The guardrail number and the headline capacity number contradict at a glance. One sentence reconciling them ("the anchor run exceeds the guardrail; it is a throughput measurement, not a recommendation") would close it. |

---

## Unsupported or over-confident

**Over-confident.**

- `SKILL.md:112` — "Both paths being vendor-documented independently **confirms the community's
  LightX2V/Pusa compatibility reports** `[official]`." A non sequitur carrying the wrong marker. The
  vendor documenting a LightX2V path confirms nothing whatever about **Pusa**, which is sourced
  elsewhere only to `[community — Dzugavili]` (`setup-and-workflows.md:206`). Split the claim.
- `characters.md:157` — "Both references condition a shared latent with no regional isolation, and
  similarity raises the bleed." A flat architectural assertion, no marker, no source, in a craft file.
  This is exactly the shape the two-bar rule exists to catch: hard-fact-shaped, community-grade
  evidence at best.
- `SKILL.md:208` — "Non-face attributes carry weaker conditioning anchors than the face and decay
  first." Same shape. The *symptom* is `[community — zsnck; single report]`; the mechanism is the
  author's and reads as established.
- `SKILL.md:152` — "SCAIL-2 **relights and re-renders** the subject without inheriting the source
  footage's grade or lens softness." The observation is nsfwVariant's; the causal story is not, and is
  unmarked.
- `SKILL.md:9` — "'SCAIL' is nowhere glossed as an acronym; treat it as a name." An exhaustive negative
  stated flatly. Harmless, but it is the same epistemic move the skill elsewhere flags.
- `SKILL.md:176` — "no community trainer (`musubi-tuner`, `diffusion-pipe`, ai-toolkit) documents
  support." The Civitai half carries `[community — Civitai models API, 2026-08-22]`; this half carries
  nothing, and it is a negative across three separately-maintained repos. This claim is load-bearing —
  it is the entire justification for omitting `lora-training.md`.
- `prompting-guide.md:3` — "scene composition from the masks", stated as one third of a flat
  three-way decomposition. Nothing in the skill establishes that masks control composition; they
  control background visibility and correspondence.
- `SKILL.md:239` — the suite table's own row: replacement is "**The reason to be here**", while
  `characters.md:80–88` says the model cannot reliably hit a specific real face. A reader whose job is
  "put *this* person into the clip" is routed in by a row that the skill later retracts. The caveat
  belongs in the row.

**Marker defects that read as claims** (P3 individually, a pattern collectively):

- `SKILL.md:124` — `` `[community — third-party, not vendor-run]` ``: a marker with no source in it.
- `SKILL.md:118`, `setup-and-workflows.md:106` — `` `[community — re-verify]` `` ×2: a qualifier with
  no source. §6.2's sub-grammar requires `[community — <source>; re-verify]`.
- `SKILL.md:18` — `` `[official — arXiv 2606.10804; ComfyUI PR #14373]` ``: the semicolon introduces a
  second *source*, not a qualifier from the closed set. Should be a comma.
- **53 bare `` `[official]` `` markers** across the skill (21 in SKILL.md alone), against 3 in
  `wan-2-2` and 0 in `minimax-h3`/`krea-2`. §6.2: "`[official]` is optional and should be used
  *sparingly* — specifically where an official number sits beside a community number and the contrast
  is the point." Here it is default punctuation, which devalues it exactly where the contrast matters.

**Under-confident / fails to guide.**

- `SKILL.md:93` — the file-layout table's own footnote tells me not to trust the filenames in it and
  sends me to a page it does not link, for files it does not enumerate. Combined with the missing
  repack repo, the table's practical yield is one filename.
- `setup-and-workflows.md:108–118` — the VRAM table is honest ("treat every figure as an existence
  proof") but has **no 24 GB row at all**: 16 GB and 96 GB only. The most common question a reader
  brings ("will this run on my 3090/4090?") is unanswerable from it, and the hedge is doing the work
  that a missing data point should do.

**Correctly calibrated, worth keeping as the model:** `SKILL.md:170` ("The likely reconciliation — a
hypothesis, not a finding"), `SKILL.md:279` (Mix Studio: state the accusation, refuse to repeat it as
fact, still caveat the recommendation), and `SKILL.md:180` (Wan LoRA transfer: reason from the
architecture, then say nobody has tested it).

---

## Fit with the suite

**It reads as a sibling, structurally.** Slot-for-slot it is closer to §2 than `wan-2-2` or
`minimax-h3` are. Verbatim headings all exact. `## Task-mode selector` with a "Use when…" column, as
the video spine requires. `## Per-mode settings`, not "Per-variant". Two-bar section byte-identical, in
the second-to-last slot, with a real contested-bullet list and named community authors. All seven §6.5
video suite-table axes present, audio explicitly stated as "neither generates nor consumes". Every
published-sibling mention is a relative link. This is a well-socialised skill.

**Where it reads as a stranger.**

1. **The file layout is materially weaker than its nearest sibling's.** `wan-2-2/SKILL.md:61` names the
   `Comfy-Org` repack repos, gives exact filenames, names `ModelSamplingSD3` as the shift node, and
   flags its VAE trap as "verified in the official templates". `scail-2` gives one filename, an
   ellipsis, an unnamed shift node, an unnamed SAM3 pack, and a footnote disowning the rest.
2. **It duplicates a sibling's material.** `prompting-guide.md:149–166` reproduces the Darqsat H3
   prompt block that `minimax-h3/SKILL.md:295–313` owns — and reproduces it *differently*. §8 of the
   prompting guide is a good idea (the contrast genuinely illuminates SCAIL-2's conditioning shape),
   but it should quote two lines and link, not re-type the artefact.
3. **Marker density is 212 across the corpus — the highest in the suite by ~50%** (`krea-2` 140,
   `minimax-h3` 58, `wan-2-2` 39). §7 clause 14 licenses density variation for a young model, so this
   is not a finding on its own; the bare-`[official]` habit inside it is.
4. **Internal duplication between SKILL.md and its own reference.** Near-verbatim in both: the
   single-dense-DiT paragraph (`SKILL.md:97` / `setup-and-workflows.md:42`), the mask semantics table
   and the vendor quote (`SKILL.md:65–67` / `setup-and-workflows.md:84–92`), the divisibility note
   (`SKILL.md:114` / `:46`), the production ladder (`SKILL.md:190` / `:155`), restore-before-interpolate
   (`SKILL.md:192` / `:165`), and the zoom-crop method (`SKILL.md:194` / §6.2). §5.3's corollary:
   SKILL.md keeps the rule and the anchor; the reference keeps the table.

**Positioning accuracy.** The comparisons are careful and, as far as I can check against the siblings,
correct: the Wan-2.1-not-2.2 lineage matches `wan-2-2/SKILL.md:178` exactly; Bernini-R's attribution
(ByteDance, Wan 2.2, Apache 2.0) matches `wan-2-2/SKILL.md:178`; the Wan-Animate-displacement claim
matches `wan-2-2/SKILL.md:251`. The H3 comparison at `SKILL.md:255` is fair rather than triumphal, and
`prompting-guide.md:170` closes with a genuinely even-handed "the trade is real in both directions".
The only oversell is the retracted-later replacement row noted above.

**Reciprocal-link debt (owed by the siblings, per check 36).** `wan-2-2/SKILL.md:182` and
`ltx-2-5/SKILL.md:253` already link `[`scail-2`](../scail-2/)` correctly. **`minimax-h3/SKILL.md:382`
does not** — it routes readers to `[`wan-2-2`](../wan-2-2/)` for SCAIL-2, which was right while
scail-2 was unpublished and is now a dead end. Also `wan-2-2/SKILL.md:251` names SCAIL-2 as a bare
string in the "Reach for instead" column.

**Link risk.** `SKILL.md:36`, `:196`, `:241`, `:242` link `[`ltx-2-5`](../ltx-2-5/)`, which is *also*
unregistered in `marketplace.json`/README. Per §6.5, unpublished models are plain bold with a status
word. Either ship the two together or de-link.

---

## Rubric (STANDARD §8)

**A. Shape**

| # | Check | Result |
|---|---|---|
| 1 | All MANDATORY §2 sections present at right level | **PASS** — all 15 slots. |
| 2 | Section order | **FINDING (P2, deliberate)** — `## Masks are the control surface` is a slot-8 section sitting at 4.5. See ruling below. Everything else in order; one rule correctly precedes setup. |
| 3 | Verbatim headings byte-exact | **PASS** — all ten checked character-for-character, including the em dash in the two-bar heading and the ampersand in `## Licence & limitations`. |
| 4 | Selector table with "Use when…" | **PASS.** |
| 5 | Failure table ≥8 rows, every cause states a mechanism | **FINDING (P1, one cell)** — 11 rows, ten mechanisms. `SKILL.md:211` cause reads "Reported consistently and unexplained; it contradicts the intuition that replacement is character-local" — that is a provenance note, not a mechanism. Say so plainly ("no mechanism known") or supply one. |
| 6 | Per-mode `###` blocks with steps/CFG/sampler/scheduler/resolution/negatives/seed + frames/fps/shift | **FINDING (P2)** — four blocks, distilled kept apart ✓, but **scheduler is never named anywhere in the skill**, negatives appear only in the LightX2V block, and sampler only in the shared stock table. |
| 7 | Pre-flight numbered 8–12 | **PASS** — 12, skimmable, all derived. |

**B. References**

| # | Check | Result |
|---|---|---|
| 8 | Four core slots or exemption | **PASS** — three present under canonical names; `lora-training.md` omitted under the §4.1 exemption, stated in SKILL.md:176 **and** SKILL.md:313 and routed. This is the cleanest exemption claim in the suite. |
| 9 | Renames needed | **N/A.** |
| 10 | One `## Reference files` row per file, saying when to read | **PASS.** |
| 11 | Train/use boundary with cross-pointer both ways | **PASS** — `setup-and-workflows.md:5` and `:198`. |
| 12 | `## Contents` TOC on every reference ≥2,000 w | **PASS** — all three. |
| 13 | Numbered `## N.` headings | **PASS**, and SKILL.md `§`-deep-links resolve. |

**C. Depth**

| # | Check | Result |
|---|---|---|
| 14 | Corpus 10,000–16,000 w | **PASS** — ~14,126. |
| 15 | SKILL.md 25–40% and 2,800–5,500 w | **PASS, at the ceiling** — 38.9%, **5,498 w**. Two words under the threshold that would demand a named §5.2 justification is not a comfortable margin; the duplication in check 19 is where the slack is. |
| 16 | SKILL.md < 500 lines | **PASS** — 313. |
| 17 | Each reference 700–3,500 w | **BORDERLINE** — `setup-and-workflows.md` ~3,525, over by 25; it carries a `## Contents` TOC, which §5.2 accepts. |
| 18 | Any section that doesn't change what the reader does | **PASS** — no padding found. Even `prompting-guide.md`'s "this file is deliberately short" framing earns its place. |
| 19 | Table/derivation duplicated in full between SKILL.md and reference | **FINDING (P2)** — six instances, listed under Fit above. |
| 20 | Every silent-failure trap in SKILL.md | **PASS** — mask mode-collapse, CLIPLoader type `wan`, wrong-family VAE, multi-reference arity, `int8_convrot` slowdown, LightX2V negatives inert. Correctly promoted. |
| 21 | Three pillars covered or routed | **PASS** — characters owned, LoRA training honestly routed with evidence, production pipelines owned + routed to `image-production-workflows`. |

**D. Apparatus**

| # | Check | Result |
|---|---|---|
| 22 | Description 180–320 w, folded scalar, five §6.1 elements | **FINDING (P3)** — 249 w ✓, `>` ✓, "even obliquely:" ✓, closing sweep ✓. But the enumerated trigger list **omits prompting and LoRA training**. The skill ships a `prompting-guide.md`; "how do I prompt SCAIL-2" will not match. "Can I train a SCAIL-2 LoRA" — the question the skill answers best — will not match either. |
| 23 | Two-bar section at `##`, byte-identical, second-to-last | **PASS.** |
| 24 | Five §6.3 elements | **PASS** — lede, hard-facts roll-call with named artefacts and the re-verify clause, craft roll-call with nine named authors, seven contested bullets each carrying a marker, date line. Among the best in the suite. |
| 25 | Date line as final paragraph, `**Facts dated YYYY-MM-DD**` | **PASS (P3 nit)** — `**Facts dated 2026-08-22.**` puts the period inside the bold; canonical form is `**Facts dated 2026-08-22**. <sentence>`. Distinct from the release date, which is correctly in the intro and in `## Licence & limitations` ✓. |
| 26 | Every flagged/contested claim greppable | **PASS** — 17 `[flagged — re-verify]`, 11 `[contested]`; each two-bar bullet carries its marker. |
| 27 | Italic-parenthetical markers | **PASS** — zero. |
| 28 | Malformed/nested markers | **PASS** — none nested or unterminated; all 212 backticked. |
| 29 | Orphan craft numbers / bare hedges | **FINDING (P2)** — the mechanism assertions listed above (`characters.md:157`, `SKILL.md:208`, `SKILL.md:152`) and the unmarked trainer negative (`SKILL.md:176`). No bare epistemic hedges of the "settings consensus" kind. |
| 30 | The summarise-up hop | **PASS** — every number restated in SKILL.md carries the reference's attribution. |
| 31 | Marker syntax canonical | **FINDING (P3)** — `[community — third-party, not vendor-run]`, `[community — re-verify]` ×2, `[official — …; PR #14373]`, and the 53 bare `[official]`. |
| 32 | ≥1 flagged/contested in SKILL.md | **PASS**, abundantly. |
| 33 | Every sibling mention a relative link | **PASS.** |
| 34 | Any link above `skills/generative-media/` | **PASS** — none. |
| 35 | All seven video suite-table axes | **PASS.** |
| 36 | Reciprocal links | **FINDING (P2, owed by siblings)** — `minimax-h3/SKILL.md:382`; `wan-2-2/SKILL.md:251` bare string. |
| 37 | Unpublished models bold + status word, never linked | **FINDING (P2)** — Bernini-R handled correctly (`SKILL.md:256`, "announced, not covered by this suite"). `ltx-2-5` is linked four times while unregistered. |
| 38 | Tables for parallel structure, prose for mechanism | **PASS** — and the choice is made well; the context-window dispute is correctly prose. |

**E. Registration**

| # | Check | Result |
|---|---|---|
| 39 | In `marketplace.json` and the README table | **FAIL (P1)** — in neither. `marketplace.json` still lists ten skills; the README table has no `scail-2` row and the plugin `description` string does not mention it. |
| 40 | In `freshness.json` with tier, `why_tier`, watchlist | **FAIL (P1)** — no `scail-2` key. The only mentions are stale watchlist items inside *other* skills (`freshness.json:609` `scail2-lineage`, `:634` `wan-scail2-uncovered`, whose action note still says "A dedicated scail-2 skill is briefed in workbench/scail-2/"). A `hot`-tier skill with 17 flagged and 11 contested claims and none of them on a watchlist. |
| 41 | Watchlist references still valid | **N/A** until 40 is done — but resolve `wan-scail2-uncovered` when it is. |

---

## The deliberate deviation

**Ruling: the ordering passes §7's test. The section as written does not yet deserve the slot it was
given.**

*Why the argument holds.* §7's test is whether conformity would **misrepresent the subject matter**.
Slot 8 sits after the selector, the one rule, setup, per-mode settings and signature quality — so
conforming would place the mechanism that *selects the mode* after roughly forty lines of settings that
the mechanism can silently invalidate. On this model that ordering would assert something false about
the control hierarchy: it would present steps/CFG/shift as the operative controls and masks as a
mechanic, when the vendor's own warning is that a wrong mask changes what job the model performs. That
is precisely the §5.4 silent-failure logic ("if getting it wrong produces a plausible-looking wrong
result rather than an error") applied to ordering rather than placement, and it is a stronger case than
`minimax-h3`'s licence-first deviation, which §7 already blesses. The author also discharges §1's
obligation to "say why in the skill" with an inline italic note at `SKILL.md:63` — the right way to
signal a knowing deviation to a future auditor.

*The counterargument, which is real but not fatal.* The warning is **already discharged before the
deviation happens**: the selector table's lede at `SKILL.md:27` says the mode "is decided by **what you
feed the masks**, not by which file you load — convenient, and the model's single largest footgun", and
forward-links to the section. A reader is warned in slot 3 regardless. So the deviation buys less than
the justification claims — it buys emphasis, not information. That downgrades it from necessary to
defensible, and it is still defensible.

*Why the section does not yet earn it.* A section promoted above Setup on the argument "no setting
below matters if the masks are wrong" incurs an obligation to make the masks *right*. This one does
not. Eleven lines, of which the semantics table and the vendor quote are duplicated verbatim in
`setup-and-workflows.md:84–92`, and the operative question — **which** of the three masks these three
values describe, and where you set them — is unanswered in both places (sticking point 3). As it
stands the reader is moved earlier only to be told to go read a reference. Two edits fix it: (a) name
the mask each semantic governs, and say which node exposes it; (b) cut the duplicated quote from one of
the two locations. With those, keep the placement and record it in §7 as clause 18.

---

## My one question

**Do the black / white / colour semantics all describe one mask, and if so which one — and where did
that three-valued table come from?**

I am asking because it is the single most load-bearing hard fact in the skill (the two-bar section
names "the **mask colour semantics**" in its hard-facts roll-call at `SKILL.md:287`), it is restated
four times, and it is architecturally odd in a way that suggests a merge. A binary background-visibility
flag and a coloured region-to-motion correspondence encoding are normally *different inputs* — which is
exactly what the selector table implies when it lists "reference foreground mask" and "per-frame driving
mask" as separate rails (`SKILL.md:31`). Collapsing a vendor foreground-mask spec and a
`SCAIL2ColoredMask` spec into one three-valued table would be an easy and invisible error, and it would
be the worst possible one to make here: the skill's own claim is that a misread mask semantic "yields a
plausible clip doing the wrong job" (`SKILL.md:287`). Every other defect above is an edit. This one, if
it is wrong, is the skill teaching the failure it exists to prevent.
