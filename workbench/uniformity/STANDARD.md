# The generative-media suite standard

**Status:** canonical. Written 2026-08-22 against the 10 published skills plus the machine census in
`workbench/research-2026-08-22/SHAPE-CENSUS.md`. Consistent with, and subordinate to,
`.agents/skills/media-model-skill/` — where that spec is silent or offers a choice, this file
**resolves it**, and each resolution is marked **RESOLVED** with what the spec left open.

Audience: an agent auditing or repairing one skill. Section 8 is the rubric; sections 1–7 are why.

---

## 1. The principle

Uniformity here is not tidiness — it is **transfer**. A reader who has used one skill in this suite
should be able to open any other and already know where the licence lives, where the failure table
is, what a `[community — …]` bracket means, and which reference file to pull for LoRA
hyperparameters. Every skill that puts those in a different place taxes that reader, and the tax
compounds across ten skills. Uniformity of *scaffolding* is what buys the freedom for the *content*
to be as different as the models actually are.

**The test for a justified deviation, in one sentence: a deviation is justified when the subject
matter would be misrepresented by conformity — not when conformity would merely be inconvenient to
retrofit.** Three ways to fail it, all seen in this suite:

- **Not justified:** `z-image` calls its settings section "Variant-specific settings" where four
  siblings say "Per-variant settings". Same content, same job, different words. Pure drift.
- **Justified:** `minimax-h3` opens with 450 words of licence before anything else. Its licence
  excludes the reader's country. Putting that in the usual tail slot would be a misrepresentation of
  what matters about the model.
- **The failure mode to avoid:** flattening `ideogram-4`'s `json-caption-guide.md` into
  `prompting-guide.md`. The model's prompt is a JSON document, not prose; the filename carries real
  signal and readers search for it.

When in doubt, ask: *would a reader who knows the sibling skills be surprised, and would the surprise
teach them something true about this model?* If yes, keep it and say why in the skill. If no,
conform.

---

## 2. Model-skill shape

The canonical `SKILL.md` section sequence. Order is normative — an audit finding is valid for a
section that exists but sits in the wrong place.

**RESOLVED:** the spec's Step 2 lists the anatomy but not its order, and the published skills disagree
in exactly one place — `z-image` puts **Setup & ecosystem** before **The one rule**, while `krea-2`,
`flux-2`, `sdxl`, `wan-2-2` and `minimax-h3` all put the one-rule first. **The one rule comes first.**
It is the highest-leverage section and it frames every setting that follows; setup is reference
material the reader scrolls back to.

| # | Section | Status | Must contain |
|---|---|---|---|
| 0 | **Frontmatter** | MANDATORY | `name` (kebab-case, matches folder) + `description`. See §6.1. |
| 1 | **Intro paragraph** (`# <Model>`) | MANDATORY | One dense paragraph: params, architecture, text encoder, languages, licence, release date. Then **"The defining trait:"** — one or two sentences on what makes it different. |
| 1a | **The defining constraint** | CONDITIONAL(the model has a gate that can rule the reader out entirely — territory clause, revenue cap, hard NSFW filter, gated weights) | One or two sentences naming the gate, and a pointer to the section that settles it. |
| 2 | **Licence-first block** | CONDITIONAL(§1a applies *and* the gate is legal rather than technical) | The full clause treatment, ahead of everything else. Only `minimax-h3` qualifies today. Where §1a does not apply, licence stays in slot 12. |
| 3 | **Selector table** | MANDATORY | A table with a **"Use when…"** column. Heading is `## Variant selector` (image, multi-checkpoint), `## Task-mode selector` (video), or `## Surface selector` (hosted/self-hosted split). Announced-but-unreleased variants listed and marked as such. |
| 4 | **The one rule that changes everything** | MANDATORY | Heading verbatim. Discovered from this model's dominant quality lever, with its **mechanism** stated. A Don't/Do table where the rule is a prompting rule. |
| 5 | **Setup & ecosystem** | MANDATORY | Sub-headed: **File layout** (`file → models/ folder → loader node` table), **Stock node settings** (verbatim from template JSON, labelled as verbatim), **Quantisation & VRAM**, **diffusers** (pipeline class + minimum version). Add **Hosted surfaces** if any. |
| 6 | **Per-variant settings** | MANDATORY | Heading verbatim (`## Per-mode settings` for a task-mode spine). One `###` block per variant/mode: steps, CFG/guidance, sampler, scheduler, resolution, negatives, seed behaviour, LoRA weight — plus frame count, fps and shift for video. Distilled and undistilled blocks kept apart. |
| 7 | **Signature-quality technique** | MANDATORY | The model's default look and the lever that overrides it. Heading names the actual trait, not a template (`## Realism — the FLUX.2 approach`, `## The anti-AI-look and its two taxes`). Video adds **default motion character** as a second named default. |
| 8 | **Model-specific mechanics** | OPTIONAL, repeatable | Sections that exist because this model does something the others don't. `minimax-h3`'s acceleration stack, `wan-2-2`'s two-LoRA rule, `z-image`'s gaze control, `ideogram-4`'s JSON caption schema. This is where legitimate length lives. |
| 9 | **Production pipelines & mixing models** | MANDATORY | Heading verbatim. Numbered stage ladder with per-stage settings, which stages are bypassable, the decode-to-pixels handoff rule, and a link to [`image-production-workflows`](../image-production-workflows/) rather than duplicating it. Video skills additionally state the **restore-before-interpolate** ordering rule. |
| 10 | **Failure modes & QC** | MANDATORY | Heading verbatim. `symptom → cause → fix` table, ≥8 rows for a model skill. **The cause column states the mechanism**, not a restatement of the symptom. |
| 11 | **Pre-flight checklist** | MANDATORY | Heading verbatim. Numbered, 8–12 items, skimmable, derived from the rest of the skill. |
| 12 | **Where <Model> sits in the suite** | MANDATORY | Heading verbatim (`Where <Model> sits in the suite`). `Job | this model | Reach for instead` table. See §6.5 for the required rows and the link form. |
| 13 | **Licence & limitations** | MANDATORY unless slot 2 was used | Heading verbatim: `## Licence & limitations`. **RESOLVED:** `z-image` and `wan-2-2` say "Licence and known limitations"; the ampersand form is canonical (`sdxl`, `ideogram-4`, `flux-2`, `krea-2` — 4 to 2). Must state the code/weights/output split where one exists, and what the safe path is for commercial use. |
| 14 | **How to read the claims in this skill — two bars, by claim type** | MANDATORY | Heading verbatim, at `##` level. See §6.3. Ends with the date line (§6.4). |
| 15 | **Reference files** | MANDATORY, last | Heading verbatim. `File | When to read it` table, one row per file in `references/`, describing *when to reach for it* — not what it contains in the abstract. |

Anything not on this list is slot 8 and needs no permission. Anything on this list that is missing is
a finding.

---

## 3. Cross-cutting-skill shape

`character-lora-training`, `comfyui-on-runpod` and `image-production-workflows` are **craft skills**:
they own what spans models, and they have no variants, no file layout and no licence of their own.
Forcing them into §2 would produce empty sections. They get their own sequence, which the three of
them already ~80% agree on.

| # | Section | Status | Must contain |
|---|---|---|---|
| 0 | **Frontmatter** | MANDATORY | As §6.1, plus an explicit **boundary clause**: "Per-model X lives in the model skills — this owns what transfers." All three already have one. |
| 1 | **Intro** | MANDATORY | What the skill owns, in one or two paragraphs, framed as the *goal it serves* rather than a topic. |
| 2 | **Boundary section** | MANDATORY | The single most important section of a cross-cutting skill and the one that keeps the suite from duplicating itself. A table. Two shapes, both valid: **routing outward** (`comfyui-on-runpod`'s "What this owns, and what it doesn't" → question → where it belongs) or **routing inward** (`character-lora-training`'s model → "the thing you cannot skip" table). Heading is free-form; the table is not optional. |
| 3 | **Gate section** | CONDITIONAL(the craft has a legal, policy or cost precondition) | Leads if it can invalidate the work. `character-lora-training`'s "Before anything: can you publish it?" is the model. |
| 4 | **The one rule that changes everything** | MANDATORY | Heading verbatim. All three already have one, and they are the best sections in those skills. |
| 5 | **The craft body** | MANDATORY, repeatable | The actual content, `##`-sectioned by concern. No prescribed shape — this is what the skill is for. |
| 6 | **Tool/status section** | CONDITIONAL(the craft depends on third-party tooling that churns) | A status table with maintenance state, as `image-production-workflows` does. Flag it in the freshness watchlist. |
| 7 | **Failure modes & QC** | MANDATORY | Heading verbatim, same rules as §2.10. ≥6 rows. |
| 8 | **Pre-flight checklist** | MANDATORY | Heading verbatim, 8–12 numbered items. |
| 9 | **Suite map / positioning** | MANDATORY | A table mapping every published sibling to its role relative to this craft. `image-production-workflows`'s "The suite map" is the exemplar and should stay the suite's canonical map. Heading may be `## The suite map` (hub skills) or `## Where this fits` (others). |
| 10 | **How to read the claims…** | MANDATORY | Heading verbatim, as §6.3. |
| 11 | **Reference files** | MANDATORY, last | As §2.15. |

**Explicitly absent from this shape, and correctly so:** selector table, per-variant settings,
setup & ecosystem, licence & limitations, signature technique. Do not open findings for their
absence in these three skills.

---

## 4. Canonical references set

### 4.1 The four core slots

Every **model skill** carries these four unless the row's exemption applies. Filenames are exact.

| File | Owns | Exemption |
|---|---|---|
| `prompting-guide.md` | Prompt anatomy in full, encoder-specific dialect, vocabulary tables (camera / lighting / motion / soundscape), text rendering, common mistakes, drop-in templates. | May be renamed when the model's prompt is not prose — see §7. |
| `setup-and-workflows.md` | Node-by-node graph walkthrough, full quant/VRAM tables, the CLI, diffusers detail, **using and stacking LoRAs**, the multi-stage ladder with per-stage settings, mixed-model handoffs. | None. |
| `lora-training.md` | **Making** a LoRA only: trainers, hyperparameters as attributed starting points, dataset architecture, captioning doctrine, style-LoRA specifics, adult/NSFW work, assessing fit, debugging. Links [`character-lora-training`](../character-lora-training/) for what transfers. | Omit only when no training path exists for the model at all; then say so in SKILL.md and route. |
| `characters.md` | Identity across generations: path selection (adapter vs LoRA vs multi-reference), the dataset protocol, deployment (detailer-stage swap), multi-outfit/multi-character limits, failure modes, and honest routing to a better sibling. | Omit only when the model has no identity tooling *and* SKILL.md's suite table carries an explicit "Consistent characters → reach for X" row. `ideogram-4` qualifies. |

The **train vs. use** boundary is load-bearing and every skill already states it: *making* a LoRA is
`lora-training.md`, *loading and stacking* one is `setup-and-workflows.md`. Keep the cross-pointer in
both files.

### 4.2 Extras

Named by concern, one file per concern. Canonical names for the recurring ones:

- `api-and-hosted.md` — the vendor's hosted surface: endpoints, auth, params, pricing, async pattern,
  commercial terms, and how hosted output differs from open weights.
- `motion-and-camera.md` — video only: the control suite, camera-trajectory LoRAs, VACE-class
  reference conditioning, and **what is not controllable**.
- `controlnet-and-identity.md` — image only, where structural control is deep enough to need its own
  file rather than a `setup-and-workflows.md` section.
- `licence-and-territory.md` — only where the licence needs clause-by-clause treatment.
- `checkpoints-and-loras.md` — only for a model whose ecosystem *is* third-party checkpoints (`sdxl`).

Anything else takes a descriptive kebab-case name. Do not invent a new name for a slot in §4.1.

### 4.3 Rename map — what exists today

| Skill | Current | Canonical | Verdict |
|---|---|---|---|
| `z-image` | `workflows.md` | `setup-and-workflows.md` | **Drift.** The spec permitted both names; six of seven model skills chose one. Rename, and update the eleven `§`-deep-links in SKILL.md. (Alternative considered: keep, because z-image's setup lives entirely in SKILL.md. Rejected — the file carries node settings, LoRA loading and the quant discussion, which is the same content the siblings' file carries.) |
| `minimax-h3` | `loras-and-training.md` | `lora-training.md` | **Drift.** The plural was chosen because the file inventories released speed LoRAs as well as training them. Rename; keep the inventory section — for an ecosystem this young the inventory *is* the training story. |
| `flux-2` | `api-and-bfl.md` | `api-and-hosted.md` | **Drift**, low priority (P3). The vendor name adds nothing once you are inside `flux-2/`. |
| `ideogram-4` | `api-and-webapp.md` | `api-and-hosted.md` | **Drift**, low priority (P3). |
| `ideogram-4` | `self-hosting.md` | `setup-and-workflows.md` | **Drift.** Its contents are exactly the canonical slot — diffusers, the CLI, ComfyUI graph, quant/VRAM, gating. "Self-hosting" reads as a surface, which it is not; the surface pair is `api-and-hosted.md`. |
| `ideogram-4` | `json-caption-guide.md` | *keep* | **Justified** — see §7. |
| `ideogram-4` | *(no `characters.md`)* | *keep absent* | **Justified** — §4.1 exemption is met. |
| `ideogram-4` | *(no `lora-training.md`)* | **add, or expand in place** | **Gap.** The exemption no longer applies: ai-toolkit and fal both ship trainers. 63 words inside `self-hosting.md §6` is not coverage. Either promote to a `lora-training.md` or expand the section and route to [`character-lora-training`](../character-lora-training/). |
| `sdxl` | `checkpoints-and-loras.md` | *keep* | **Justified** — §7. |
| `minimax-h3` | `licence-and-territory.md` | *keep* | **Justified** — §7. |
| `wan-2-2` | `motion-and-camera.md` | *keep* | Canonical extra. |
| `flux-2` | `controlnet-and-identity.md` | *keep* | Canonical extra. |

Cross-cutting skills have no prescribed reference set; their files are named by concern and all six
current names are fine.

---

## 5. Depth targets

### 5.1 The measurement that matters

Total corpus size across the suite is **already uniform**, and this is the finding that settles the
"is `minimax-h3` bloated / is `z-image` thin" question:

| Skill | SKILL.md | + references | total | SKILL.md share |
|---|---|---|---|---|
| `z-image` | 3,089 | 10,730 | **13,819** | 22% |
| `sdxl` | 3,889 | 9,857 | **13,746** | 28% |
| `flux-2` | 3,922 | 9,953 | **13,875** | 28% |
| `krea-2` | 5,292 | 9,591 | **14,883** | 36% |
| `ideogram-4` | 4,571 | 7,091 | **11,662** | 39% |
| `wan-2-2` | 4,228 | 5,923 | **10,151** | 42% |
| `minimax-h3` | 6,460 | 8,846 | **15,306** | 42% |

**Neither is a defect.** `minimax-h3` is not 2× `z-image`; it is 1.1× `z-image`. What differs is the
**split**, and the split is the thing to standardise.

### 5.2 Targets

**Model skills:**

- **Total corpus: 10,000–16,000 words.** Below 10,000 the model is under-researched; above 16,000
  split a reference or cut.
- **SKILL.md: 25–40% of corpus, and 2,800–5,500 words absolute.** `z-image` (22%) is the low outlier
  and `minimax-h3` / `wan-2-2` (42%) the high ones; all three are inside tolerance and need no
  repair, but a new skill outside 25–40% is a finding.
- **SKILL.md hard cap: 500 lines** (from the spec). Current max is `minimax-h3` at 419.
- **Each reference file: 700–3,500 words.** Under 700, fold it into a sibling file or into SKILL.md.
  Over 3,500, split it or accept it with a `## Contents` TOC (see §6.7).
- **Above 5,500 words in SKILL.md requires a named justification** in the audit. The only
  justifications that count are: a licence that can rule the reader out; an acceleration or
  configuration stack without which the model is unusable in practice; more task modes than the
  suite norm; or a documented capability set the official templates do not expose. `minimax-h3`
  carries three of the four and is therefore correct at 6,460.

**Cross-cutting skills** are legitimately smaller — they own craft, not an ecosystem:

- **Total corpus: 5,000–10,000 words.** (Current: `comfyui-on-runpod` 5,542, `image-production-workflows`
  5,854, `character-lora-training` 9,740.)
- **SKILL.md: 2,000–3,200 words**, 2–4 reference files.

### 5.3 The principle that decides it

Word counts are a smell test; this is the rule.

> **Every section must change what the reader does.** If a section can be deleted and the reader's
> next action is unchanged, it is not depth — it is padding. If a paragraph states a number the
> reader will type into a node, a filename they will download, a mechanism that lets them debug a
> class of failure they have not met yet, or a routing decision that sends them elsewhere, it earns
> its place regardless of length.

Two corollaries that catch the real cases:

- **Restating a reference in SKILL.md is padding, not summary.** `minimax-h3`'s frame-count formula
  and megapixel table appear in full in both SKILL.md and `setup-and-workflows.md §3–4`. One of them
  should be the pointer. The rule: SKILL.md carries the *rule and the anchor number*
  (`frames ≡ 5 mod 17`; the 1344×768 default); the reference carries the *full table and derivation*.
- **A pillar covered by a pointer alone is still covered.** `z-image` gives characters two sentences
  in SKILL.md and a 1,588-word reference. That is correct, not thin — the spec's requirement is that
  each pillar is covered *or honestly routed*, and a named pointer is coverage.

### 5.4 SKILL.md vs reference — the placement rule

SKILL.md is what an agent loads first, unprompted. A reference is pulled when the agent already knows
it has that specific job. So:

> **SKILL.md carries what a reader needs in order to know what to do next — including what they
> would not think to ask for. A reference carries what they need once they have decided to do it.**

Operationally, SKILL.md gets: the decision (selector), the one rule, the anchor numbers for the stock
path, every trap that fails *silently*, the failure table, the routing. A reference gets: full tables,
derivations, node-by-node walkthroughs, alternate paths, per-author recipe variants, and anything
whose reader has already committed.

The test for a silent-failure trap: **if getting it wrong produces a plausible-looking wrong result
rather than an error, it belongs in SKILL.md** regardless of how niche it is. `minimax-h3`'s missing
audio VAE, `wan-2-2`'s sampler-handoff noise flags, `z-image`'s diffusers-format LoRA QKV no-op, and
`krea-2`'s two guidance conventions are all correctly in SKILL.md for this reason.

---

## 6. Apparatus

### 6.1 Frontmatter `description`

**This is not a real divergence and should not generate churn.** The census range is 185–313 words;
all ten are inside a sensible band.

- **Length: 180–320 words.** Outside that band is a finding; inside it is not.
- **YAML: `>` folded-block scalar**, `name` first, `description` second. No other keys unless the
  skill genuinely restricts tools.
- **Required content, in order:**
  1. **What it is** — "Authoritative guide for <Model> (<vendor>) …" plus the surfaces covered.
  2. **The gate, if there is one** — bolded, before the trigger list. `minimax-h3` does this
     correctly with its territory clause.
  3. **The trigger phrase** — "Use this whenever the user touches <Model> in any way, even
     obliquely:" verbatim for model skills; cross-cutting skills use "Use this whenever the user
     <does the craft>, even obliquely:".
  4. **An enumerated trigger list** covering, at minimum: choosing a variant, installing/setup,
     writing or fixing prompts, building a workflow, training a LoRA, consistent characters,
     licensing, and debugging a named artefact. Use the model's own vocabulary — real filenames,
     node names, error strings — because those are what a user actually types.
  5. **A closing sweep** — "Use this for any question about <Model> in any context." or the routing
     note ("Also covers who should reach for something else instead").
- Cross-cutting skills additionally carry the **boundary clause** (§3.0).

### 6.2 Provenance markers — the REQUIRED rule

**Ruling on the older cohort: they are not unmarked, and the census undercounts them.** Counting
markers across `SKILL.md` *and* `references/`:

| Skill | brackets in SKILL.md | brackets in references | italic-paren markers |
|---|---|---|---|
| `krea-2` | 49 | 82 | 0 |
| `minimax-h3` | 30 | 27 | 0 |
| `wan-2-2` | 23 | 13 | 0 |
| `sdxl` | **0** | 26 | **9** |
| `ideogram-4` | **0** | 23 | 0 |
| `z-image` | **0** | 5 | **16** |
| `flux-2` | 2 | 3 | **16** |
| `character-lora-training` | 2 | 7 | 0 |
| `image-production-workflows` | 1 | 0 | **14** |
| `comfyui-on-runpod` | 0 | 0 | 0 |

> **CORRECTED 2026-08-22.** The italic-paren column above originally read `~15` / `~18` for `sdxl`
> and `z-image` and **0 for every other skill**, giving a suite total of "33 instances across `sdxl`
> and `z-image`". Both halves were wrong. Re-counted mechanically against the pre-conversion tree
> (`git show HEAD:` on each file, `grep -o '\*([A-Za-z][^)]*)\*'` filtered to the tier words), the
> real distribution was **55 instances across four skills**: `flux-2` **16**, `z-image` **16**,
> `image-production-workflows` **14**, `sdxl` **9**.
>
> **`flux-2` was recorded as 0 for a skill this section was quoting.** Two of the three worked
> conversion examples below are verbatim `flux-2` lines — `*(flagged — no DiT block map yet)*` is
> `flux-2/references/characters.md:62`, and the Khanykov01 example is `characters.md:49`. The census
> read the examples off the page in front of it and still scored the source skill at zero, which is
> what a hand-count does when it is scoped to the two skills it already suspects.
>
> The correction does not change the **ruling** — the form is still retired, and the conversion is
> still mechanical and lossless. It changes two things that follow from it: the diff was **1.7× the
> size** the section budgeted for, and it was **not** confined to the "older cohort" the section
> blames. `flux-2` and `image-production-workflows` were running the undeclared second system too,
> which means the form was spreading by imitation across the suite rather than surviving in two
> unmaintained corners. That is the stronger argument for retiring it.

`sdxl` and `ideogram-4` mark heavily — in their references. Two things are actually going on:

- **Markers stop at the SKILL.md boundary in the older cohort.** `z-image`'s multi-stage ladder is
  labelled "community layered pipeline" three times in `workflows.md` and carries nothing at all in
  SKILL.md, which summarises the same numbers. **Attribution is being lost on the summarise-up hop.**
  §6.2.1's *layer-balance ratio* makes this testable rather than anecdotal.
- **Four skills ran a second, undeclared attribution system**: an italic parenthetical,
  `*(community, strong — WeirdWonderfulAI, Mickmumpitz, Civitai dataset guides)*`. **55 instances**
  across `flux-2`, `z-image`, `image-production-workflows` and `sdxl`.
  It carries the same payload as a bracket marker — tier, named sources, and a confidence qualifier
  the bracket form does not even have — but none of its syntax, so it is invisible to every grep the
  freshness protocol runs.

> **CLOSED 2026-08-22 — the conversion is complete suite-wide.** All 55 instances across all four
> skills are now bracket markers. Verified over the whole working tree: `grep -rIo --include='*.md'
> '\*([A-Za-z][^)]*)\*' skills/ | grep -ic 'community\|official\|flagged\|contested\|named'` returns
> **0**. Check 27's first half is therefore a regression test, not an open finding; keep running it,
> because the form spread by imitation once already.
>
> **Still open — check 27's second half.** The bare inline label forms survive in seven places:
> `flux-2/references/setup-and-workflows.md` lines 13, 22, 29, 30, 120 (`(community)` in a TOC entry,
> a source line, two table cells and a `##` heading), `flux-2/references/prompting-guide.md:3`, and
> `ideogram-4/SKILL.md:36` (`(official)` closing a sentence). `z-image/references/setup-and-workflows.md:222`
> carries a source line with `(official)` that reads as prose rather than a marker — judge it, do not
> convert it mechanically. These are P3.

So the answer is neither "under-marked" nor "fine". It is **differently marked, plus genuinely
under-marked at the SKILL.md layer** — both bounded and repairable.

**RESOLVED — the italic-parenthetical form is retired.** Convert each instance to a bracket marker,
preserving the qualifier in the payload:

```
*(Community, strong — Khanykov01, Civitai 6990.)*   →   `[community — Khanykov01, Civitai 6990; strong]`
*(Community, convergent — Civitai dataset guides 7777/21257/21114.)*
                                                     →   `[community — Civitai guides 7777/21257/21114; convergent]`
*(flagged — no DiT block map yet)*                   →   `[flagged — no DiT block map yet]`
```

The conversion is mechanical and lossless. (Alternative considered: bless it as a second sanctioned
form with its own grammar. Rejected — two grammars for one job is the drift this document exists to
end, and only the bracket form is greppable.)

**The rule.**

> **A bracket marker is REQUIRED when all three hold:** (a) the claim is *craft*, not a hard fact;
> (b) it is *actionable* — a number a reader will type, a named tool/checkpoint/node they will
> install, a recipe, or a comparative verdict they will act on; and (c) **no named source appears in
> the same sentence or in the governing parenthetical or section lede.**

> **A bracket marker is REQUIRED unconditionally, regardless of (a)–(c), for
> `[flagged — re-verify]`, `[contested]` and `[pending release]`.** These are not stylistic — they
> seed the `freshness.json` watchlist, and the freshness protocol greps for them. A contested point
> described only in prose is invisible to the tooling that exists to catch it when it resolves.

> **A bracket marker is NOT required** for hard facts already covered by the two-bar section's
> hard-facts roll-call. `[official]` is optional and should be used *sparingly* — specifically where
> an official number sits beside a community number and the contrast is the point (`krea-2`'s
> 52/3.5-vs-28/4.5 footnote is the model).

**Consequences, so the auditor knows what to open:**

- ~~**`sdxl` and `z-image`:** convert the 33 italic-parenthetical markers to bracket form.~~
  **DONE 2026-08-22** — and it was 55 instances across four skills, not 33 across two (see the
  correction above). Zero remain. What survives is the inline-label residue listed above.
- **Repair the summarise-up hop.** Where SKILL.md restates a reference's craft numbers, it must carry
  the reference's attribution too. Concretely: `z-image/SKILL.md` § *Building multi-stage workflows*
  (the ×1.7 / ×2 ladder, denoise 0.23) and § *Z-Image-Turbo* (LoRA 0.7–0.8, sweep 0.5–1.2) both
  restate numbers that `workflows.md` labels "community layered pipeline"; `sdxl/SKILL.md`
  § *Production pipelines* gives a five-rung denoise ladder unattributed while attributing the
  mixed-model patterns twelve lines below.
- **`sdxl`, `z-image`, `ideogram-4`, `flux-2`:** promote SKILL.md-level contested and flagged material
  from prose into greppable markers. `z-image`'s two-bar section names two contested points in prose
  with no marker; `sdxl` calls Turbo's licence "the exception" with no marker. Small, specific diffs —
  **not** a mandate to retrofit 30 markers per skill.
- **Orphan craft numbers need an owner or a marker.** Real cases: `flux-2`'s production ladder
  (denoise ~0.3–0.45, ~0.4, ~0.2–0.3); `sdxl`'s weight band `~1.05–1.3`; `sdxl`'s
  `guide_size 512 / max_size 1024 / bbox_crop_factor 1.3–2` behind the bare hedge "settings
  consensus"; `sdxl`'s rank ladder row labelled only "The classic rank-by-type ladder" while the row
  *beneath it in the same table* carries `` `[community — neonkisu, QuantumBogoSort]` ``;
  `z-image`'s LoRA hyperparameter table and the `control_context_scale` 0.65–0.80 band. Either name
  the source in prose or add a marker.
- **Bare epistemic hedges are not attribution.** "settings consensus", "recur across guides",
  "long-standing", "dominates … practice" all name nobody. Replace with a marker or a named source.
- **`comfyui-on-runpod` at zero markers is correct.** Its two-bar section states that its craft comes
  from a single named source — a running studio. **A skill whose craft has exactly one source, named
  in the two-bar section, is exempt from per-claim marking.** Do not open findings against it.

**Marker syntax — canonical form.** A marker is `` `[<tier> — <source>; <qualifier>]` ``, wrapped in
backticks.

```
`[community — <named author>, <venue>]`     `[official — <artefact>]`
`[official]`                                 `[official-via-docs]`
`[flagged — re-verify]`                      `[contested]`
`[pending release]`
```

- **The tier token is one of exactly six**: `official`, `official-via-docs`, `community`, `flagged`,
  `contested`, `pending release`. Nothing else. **Normalise these strays** (all real, all in the
  suite today): `[official-kohya — …]`, `[official-Ostris — …]`, `[official-via-musubi docs]`,
  `[official-via-host — …]` → `` `[official — <artefact>]` ``; `[official source]`,
  `[official template observation]`, `[official, verified <date>]` → `` `[official — <artefact>]` ``;
  `[community/unverified]`, `[community/single-source]` →
  `` `[community — single report; re-verify]` ``; `[community/early — …]` →
  `` `[community — …; early]` ``; `[named — Civitai 25645]` → `` `[community — Civitai 25645]` ``;
  `[both above]` → repeat the source explicitly.
- **Em dash separator**, spaced. (`[community — …]` 230 uses; `[community: …]` and `[community - …]`
  **zero**. Already settled — no finding to open.)
- **Payload sub-grammar.** `<source>` is named authors and/or venues, comma-separated.
  A **semicolon** introduces qualifiers, from a closed set: `re-verify`, `single report`,
  `contested`, `early`, `strong`, `convergent`. **Cap the payload at ~60 characters** — `krea-2`
  carries a 129-character marker containing a full quotation. Quotations belong in the prose; the
  marker points at who said it.
- **Backticked, not bare. RESOLVED** — the suite is genuinely split (133 backticked / 157 bare), but
  the split is *per skill*: six skills backtick (`sdxl`, `z-image`, `minimax-h3`, `wan-2-2`,
  `character-lora-training`, `image-production-workflows`), two do not (`krea-2` alone holds 125 of
  the 157 bare markers, `ideogram-4` the rest). Backtick wins on three grounds: six skills to two;
  a marker is *metadata about* the claim, and code-span rendering separates it visually — which
  matters most in exactly the dense table cells where `krea-2` puts three markers in one row; and it
  guarantees markdown never parses the brackets as a link reference. Migrating `krea-2` and
  `ideogram-4` is a mechanical pass. (Alternative: bare, which is the raw-count majority. Rejected
  for the reasons above.)
- **Placement — one rule: the marker precedes the terminal punctuation of the unit it attributes.**
  **RESOLVED:** the corpus splits 52 (marker, then period — `krea-2`) against 48 (period, then marker
  — `minimax-h3`, `wan-2-2`), which is a coin flip with no convention to discover. Marker-then-period
  wins because the marker is part of the claim, not a footnote after it.
  - Sentence-scoped → immediately before that sentence's period.
  - Cell-scoped → end of the cell, no terminal punctuation.
  - Paragraph-scoped → before the final period of the last sentence.
  - **Table-header-scoped is legal**: a marker in a header cell governs every row below it
    (`| Setting | Value `[community — Organix33/drbaph]` |`). Use it instead of repeating.
  - **Heading-scoped is legal** on a `###` whose entire subsection rests on one source.
  - Never mid-clause.
  - **Mention vs use:** when referring to a marker as a token rather than applying it, say so
    ("the sections tagged `[community]`"). Do not leave a bare token that reads as an assertion.
- **Malformed markers are P1 bugs.** Two nested/unterminated ones exist today —
  `krea-2/references/setup-and-workflows.md` (`` [community — muerrilla; node unverified here, `[flagged — re-verify] ``)
  and the same pattern in `wan-2-2`. A nested marker is invisible to the freshness grep.
- **Floor:** every model skill's SKILL.md carries **at least one** `[flagged]` or `[contested]`
  marker, **or** the two-bar section states explicitly that nothing is currently flagged. Zero
  markers on a `hot`-tier skill is a finding; zero markers on a mature `stable` skill with an explicit
  "nothing flagged" line is fine.

### 6.2.1 Marker density — the calibration band

**RESOLVED 2026-08-22.** §7.14 said "marker density varies 0–49 per SKILL.md and that is correct —
do not normalise marker counts." That was right about *counts* and wrong as a stopping point. With
thirteen skills the spread runs **0 to 14.8 markers per 1,000 words**, and the top of that range is
no longer telling a reader anything. The band below normalises **density**, not counts, and it is
anchored on an operational constraint rather than on taste.

**How much of the spread is real?** Less than the "young model, thin sources" story predicts.
Freshness tier does not predict density: `sdxl` — three years old, `stable` — carries **2.9**
community markers/1k, *above* `minimax-h3` (three weeks old, `hot`) at 2.8 and five times
`ideogram-4` (`hot`) at 0.6. What predicts density is whether the author marked **hard facts**:
`[official]` density spans **0.13/1k** (`z-image`) to **5.1/1k** (`scail-2`), a 39× spread on a claim
class this section already calls optional and sparing. Strip the redundant `[official]`s and the
corpus range collapses from 0–14.8 to roughly 2–8. **Read roughly a third of the spread as real
craft-source variation and the rest as `[official]` inflation plus repeat-marking of one source.**

**Three limits. All are measured over the whole corpus — `SKILL.md` plus `references/`.**

> **1. Total density: 2.5–7.0 markers per 1,000 words.**
>
> **2. Layer balance: SKILL.md density ≥ 0.6 × the same skill's `references/` density.**
>
> **3. Watchlist class — `[flagged]` + `[contested]` + `[pending release]` combined:
> ≤ 1.6 per 1,000 words *and* ≤ 24 per corpus, whichever binds first.**

**Where limit 3 comes from, and why it is the one that actually decides the others.** Check 40
requires every watchlist-class marker to correspond to a `freshness.json` watchlist entry. Observed
entries run **6–16** across the ten registered skills (median 10.5), and the observed
marker-to-entry ratio runs **1.0–1.9** because one claim is usually marked in both SKILL.md and its
reference. A sustainable ceiling of 16 entries is therefore ~24 markers, which on a 15,000-word
corpus is 1.6/1k. This is not a style limit — a skill that emits 56 watchlist markers is asking a
`hot`-tier daily check to re-verify roughly thirty independent claims per pass, and the protocol
will silently stop keeping up. **When limit 3 and limit 1 disagree, limit 3 wins.**

**Where limit 1's ceiling comes from.** Not the raw count — the **reuse factor**, distinct marker
payloads against total instances. Inside the band the suite runs **1.1–1.8** instances per distinct
payload. `scail-2` at 14.8/1k runs **3.4**, repeating `[community — nsfwVariant]` **20 times** and
`[community — External_Trainer_213]` **16 times**. A marker that appears twenty times has stopped
being a contrast signal and become page furniture — which is precisely the `anima` blind-review
finding (`[official]` at 55 uses, cut to 18) generalised to the community tier. **Reuse above ~2.0
is the diagnostic; the fix is the heading-scoped and table-header-scoped forms this section already
blesses, not deletion.**

**Where limit 1's floor comes from.** The two skills below 2.5 — `flux-2` (2.2) and `z-image` (2.4) —
are two of the four this section already names for the summarise-up hop and for orphan craft
numbers. The floor is not a quota; it is a smell test that reliably fires on the skills independently
known to be under-attributed.

**Limit 2 is the summarise-up hop made testable.** It was derived independently of §6.2's prose
finding and reproduces it exactly: the five skills failing the 0.6 ratio are
`image-production-workflows` (0.30), `z-image` (0.39), `sdxl` (0.48), `flux-2` (0.57) and
`ideogram-4` (0.58) — the same set §6.2 diagnoses by hand. That agreement is why the ratio is worth
trusting as a check rather than a coincidence.

**Census, 2026-08-22.** Bracket markers matching the six canonical tiers, counted over each skill's
whole corpus. Bold marks a limit breached.

| Skill | corpus words | total/1k | SKILL/1k | refs/1k | ratio | watch/1k | watch N | verdict |
|---|---|---|---|---|---|---|---|---|
| `scail-2` | 15,058 | **14.8** | 15.2 | 14.5 | 1.04 | **2.03** | **30** | over on 1 and 3 |
| `krea-2` | 15,726 | **9.4** | 10.6 | 8.8 | 1.21 | 0.65 | 10 | over on 1 |
| `ltx-2-5` | 20,439 | 7.0 | 9.2 | 5.5 | 1.68 | **2.78** | **56** | at ceiling on 1, **over on 3** |
| `anima` | 15,990 | 5.4 | 6.0 | 5.1 | 1.18 | 1.59 | 25 | in band |
| `minimax-h3` | 18,098 | 4.4 | 5.1 | 4.0 | 1.29 | 1.07 | 19 | in band |
| `image-production-workflows` | 7,425 | 4.2 | 1.8 | 6.1 | **0.30** | 0.70 | 5 | over on 2 |
| `sdxl` | 15,091 | 3.9 | 2.3 | 4.7 | **0.48** | 0.74 | 11 | over on 2 |
| `wan-2-2` | 11,209 | 3.6 | 5.4 | 2.1 | 2.55 | 0.73 | 8 | in band |
| `ideogram-4` | 13,768 | 3.5 | 2.4 | 4.2 | **0.58** | 1.41 | 19 | over on 2 |
| `character-lora-training` | 11,960 | 2.8 | 3.9 | 2.3 | 1.70 | 0.94 | 11 | in band |
| `z-image` | 15,008 | **2.4** | 1.1 | 2.8 | **0.39** | 0.54 | 8 | under on 1, over on 2 |
| `flux-2` | 14,494 | **2.2** | 1.4 | 2.5 | **0.57** | 0.56 | 8 | under on 1, over on 2 |
| `comfyui-on-runpod` | 5,885 | 0.0 | 0.0 | 0.0 | — | 0.00 | 0 | **exempt** (§6.2, §7.8) |

**What being over the band obliges you to do — in this order, and it is never "delete markers".**

1. **Bare `[official]` first.** `[official]` with no artefact after it names nobody; it is the bracket
   form of the "bare epistemic hedge" this section forbids two bullets up. Suite-wide there are
   **91** of them, and they are concentrated: `scail-2` **54 of its 77** official markers, `anima`
   **18 of 20**, `krea-2` 8 of 50, `wan-2-2` 3, `ideogram-4` 2, `flux-2` 2,
   `image-production-workflows` 2. Every `scail-2` instance sampled marks a fact its own two-bar
   hard-facts roll-call already declares — the four modes, the 704p note, the mask-collapse failure,
   the PR numbers, the 40/5.0/3.0 pair — and is therefore redundant by this section's own rule.
   **Delete the bare ones whose claim is inside the roll-call; give the rest their artefact.** That
   one pass takes `scail-2` from 14.8 to ~11.2 and `anima` from 5.4 to ~4.3.
2. **Then collapse repeats to scope.** Where one source governs a table, a `###` subsection or a
   whole column, use the table-header-scoped or heading-scoped form (§6.2, §7.16) instead of
   repeating the marker down the rows. This is lossless — attribution is preserved, instances fall.
3. **Then, and only then, look at the watchlist class.** Over limit 3, the repair is **not** to strip
   `[flagged]` markers, which would hide real uncertainty. It is to **merge sibling flags into one
   claim** where they resolve together, and to move genuinely separate ones into the reference that
   owns them so SKILL.md carries the claim and the reference carries the flag.

**What this does not license.** Do not add markers to reach the floor, and do not open a finding
against a skill inside the band for the tier mix it chose. The band brackets a corpus; the
conditional rule at the top of §6.2 still decides each individual claim.

### 6.3 The two-bar confidence section

**Position:** second-to-last, immediately before `## Reference files`, after `## Licence & limitations`.

**Heading, verbatim, at `##` level:**

```
## How to read the claims in this skill — two bars, by claim type
```

**RESOLVED:** nine of ten skills carry this heading **byte-identical**. `ideogram-4` is the exception:
its two bars exist only as a **bolded lead-in paragraph buried inside `## Licence & limitations`**,
with no `##` heading anywhere between `## Licence & limitations` and `## Reference files`. That is
the single clearest structural defect in the suite, and it is causally linked to the second one —
`ideogram-4` is also the only skill inventing its own marker vocabulary (`[community/unverified]`,
`[official source]`), because **it never declared one**. Promote the section to `##` in the canonical
slot, then normalise its markers against §6.2.

**Required content, in this order:**

1. Optional one-line lede: "This skill holds two kinds of claim to two different standards, because
   they fail in two different ways." (7 of 10 carry it; keep it where present, add where missing.)
2. **Hard facts — must be exact or it breaks.** Bolded lead-in, then an *enumerated roll-call* of the
   specific facts this skill treats as hard — architecture, filenames, node names, licence terms,
   pipeline classes, template numbers. Then "**Source of truth is official**" naming the actual
   artefacts read. Then the failure consequence ("a wrong filename 404s; a misread licence is a legal
   problem"). Then the volatility note and "**re-verify before relying on them, regardless of who
   said it.**"
3. **Craft — what actually makes a good <image/clip/LoRA/result>.** Bolded lead-in, then an
   enumerated roll-call of the craft claims. Then "**The authoritative source here is the
   community**" *with the named authors listed*. Then the confidence statement: stated with
   confidence; ranges mean "your weights/dataset/resolution differ from the author's," not
   "unreliable."
4. **Contested / unresolved points** as a bullet list, each carrying its `[contested]` or
   `[flagged — re-verify]` marker. Where nothing is contested, say so in one line.
5. **The date line** (§6.4), as the final paragraph.

**Cross-cutting skills** carry the same section with the same heading; only the roll-call contents
differ. A single-source craft skill (`comfyui-on-runpod`) replaces the "authoritative source is the
community" clause with a plain statement of its actual source — which it already does, correctly.

### 6.4 Dating

**RESOLVED**, and this is the messiest divergence in the suite: **six distinct opening lexemes for
one construct**, split across two positions, with three skills conflating two different facts.

| Position | Skills |
|---|---|
| Last line of the two-bar section | `krea-2`, `flux-2`, `minimax-h3`, `character-lora-training`, `image-production-workflows` (5) |
| Inside `## Licence & limitations` instead | `sdxl`, `z-image`, `wan-2-2`, `ideogram-4` (4) |
| Mid-paragraph inside the hard-facts bar, not a standalone line | `comfyui-on-runpod` (1) |

Lexemes in use: `**Release:**` · `**Release timeline:**` · `**Release & stability:**` ·
`**Facts dated …**` · `Dated **…**.` · `Date-stamped …`.

**Two different facts are being conflated.** *When the model shipped* and *when this skill's claims
were last checked* are independent, and `sdxl`, `z-image` and `wan-2-2` record only the former —
so there is nothing in those three skills recording when they were last audited at all.

**Canonical: the last paragraph of the two-bar section, in this form:**

```
**Facts dated YYYY-MM-DD**[; community craft refreshed YYYY-MM-DD]. <One sentence on what moves
fastest and must be re-verified.>
```

- **`Facts dated <ISO date>`** is the required opener — the one lexeme that names the right fact.
  ISO dates, never prose months. `minimax-h3` is the only skill using it today; it is the model.
- The **`; community craft refreshed <date>`** clause is added when a refresh pass touched craft
  without re-verifying hard facts — exactly what the 2026-08-22 pass did. It usefully distinguishes
  the two bars in the date stamp too.
- **Release dates belong in the intro paragraph and in `## Licence & limitations`, not here.** This
  line dates *the skill*. Keep `**Release timeline:**` where it is in `z-image` and `wan-2-2` — it is
  legitimate content about the model — and *add* the missing `Facts dated` line to the two-bar
  section rather than moving anything.
- **Do not hand-edit `freshness.json`'s `last_checked` from an authoring pass** (spec, Step 0). This
  line and that field are different claims: this one says when the facts were written, that one says
  when a freshness check ran.

### 6.5 Cross-links and the suite table

**Link form — RESOLVED.** Every mention of a published sibling is a relative markdown link:

```
[`sibling-name`](../sibling-name/)                  → the skill
[`sibling-name`](../sibling-name/references/file.md) → a specific reference
```

`minimax-h3`, `character-lora-training`, `comfyui-on-runpod` and `image-production-workflows` already
do this. `z-image`, `krea-2`, `flux-2`, `sdxl`, `wan-2-2` and `ideogram-4` use bare code spans
(`` `flux-2` ``) in their suite tables — navigable by a human, dead for an agent. Convert them.
Nothing may reach above `skills/generative-media/` (CLAUDE.md).

**Unpublished models** (Flux 3, Bernini-R, Wan Animate as a standalone) are named in plain bold,
never linked, and must carry a status word — "announced", "gated licence, unverified here", "not covered by this suite".

**Required suite-table rows.** The `Job | this model | Reach for instead` table must cover these axes.
A row whose honest answer is "this model can't" is *coverage*, not a gap — that is the point of the
table.

*Image model skills:*
1. Consistent characters
2. Style / character LoRA ecosystem
3. In-image typography
4. Structural control (pose / depth / canny)
5. Photoreal faces and skin — or the model's own headline aesthetic axis
6. Commercial use under the licence (where licences differ across the suite)
7. Mixed-model pipelines → [`image-production-workflows`](../image-production-workflows/)
8. **Making it move** → the video skills, naming the still-locking handoff

*Video model skills:*
1. Locking a still first → the image skills
2. Audio — state which of the three: generates / consumes / neither
3. Motion, camera and pose control rigs
4. Exact motion transfer or character replacement
5. LoRA ecosystem and training maturity
6. Licence coverage
7. Post chain, upscale and interpolation

**Bidirectionality.** Adding a row that names a sibling obliges you to add the return row in that
sibling. An audit finding is valid for a one-way link.

### 6.6 Tables vs prose

- **Table** when the content has parallel structure across ≥3 items: selectors, file layouts,
  per-variant settings, failure modes, suite positioning, licence splits, reference pointers, quant
  matrices, status roll-ups. Tables force every cell to be filled, which is how they surface gaps.
- **Prose** when the content is a mechanism, a causal chain, a dispute between named sources, or a
  judgement call with conditions. `minimax-h3`'s Spectrum audio-feedback explanation would be
  destroyed by a table; `krea-2`'s two-taxes section is right to be prose with a numbered escalation.
- **Never a table for a one- or two-row list** — that is a sentence.
- **Never prose for a settings block** — those are the cells readers scan for.
- A `symptom → cause → fix` table's cause column is prose *inside* a table: state the mechanism.
- Table density is not a defect: `minimax-h3` has 104 table rows in SKILL.md against `z-image`'s 39,
  and both are appropriate to their subject.

### 6.7 Reference-file internals

- **`## Contents` TOC required for any reference ≥2,000 words.** **RESOLVED:** `sdxl` says "Table of
  contents", others say "Contents"; **`## Contents`** is canonical. Currently missing on:
  `z-image/prompting-guide.md`, `z-image/workflows.md`, `z-image/lora-training.md`,
  `ideogram-4/json-caption-guide.md`, `ideogram-4/self-hosting.md`, `sdxl/lora-training.md`,
  `minimax-h3/prompting-guide.md`, `minimax-h3/setup-and-workflows.md`,
  `character-lora-training/evaluation-and-tooling.md`.
- **Numbered `## N.` headings are required in any file that has a `## Contents` TOC or that SKILL.md
  deep-links by `§`.** Otherwise optional.
- **`§` deep-links are encouraged** (`references/setup-and-workflows.md §6`) and are the reason
  numbering matters. `z-image` uses them well; other skills should adopt them for the sections their
  SKILL.md points at repeatedly.
- Each reference opens with a one-paragraph statement of what the file owns and what it does not.
- A reference may carry its own short "How to read the claims in this file" section when it is long
  and craft-dense (`character-lora-training/evaluation-and-tooling.md` does). Optional, not required.

---

## 7. Justified deviations — do not flatten these

Each of these looks like drift and is not. An audit that "fixes" one has made the suite worse.

1. **`minimax-h3` opens with 450 words of licence before the selector.** Its licence excludes the US,
   EU, UK and South Korea — a large share of readers are not permitted to use the model at all.
   Slot-14 placement would be a misrepresentation. **Keep.** Same reasoning licenses
   `references/licence-and-territory.md` as an extra file.

2. **`minimax-h3`'s SKILL.md at 6,460 words.** Three of the four §5.2 justifications apply: a
   ruling-out licence, an acceleration stack the model is unusable without, and three capabilities
   the official templates hide. **Keep.** Trim only the frame-count/megapixel duplication against
   `setup-and-workflows.md §3–4`.

3. **`ideogram-4/json-caption-guide.md` keeps its name.** The model's prompt is a JSON document with a
   schema and a `CaptionVerifier`. Renaming it `prompting-guide.md` would hide the one thing a reader
   is searching for. **Keep** — and keep the `## Reference files` row leading with "Prompting —" so
   the slot is still legible.

4. **`ideogram-4` has no `characters.md`.** No identity adapters, no edit variant, no published
   character LoRAs. The spec explicitly names this as correct coverage. **Keep absent**, provided the
   suite table's "Consistent characters" row routes explicitly (it does).

5. **`sdxl/checkpoints-and-loras.md`.** SDXL's ecosystem *is* third-party checkpoints and dialects
   (Pony, Illustrious, NoobAI); no other model in the suite has an equivalent. That file has no
   canonical slot because the concern is genuinely unique. **Keep.**

6. **`sdxl` runs two composable axes** (speed variant × checkpoint dialect) where siblings run one.
   Both genuinely change what the reader does, and the spec names this as a deliberate choice.
   **Keep** — do not force it into a single selector table.

7. **`z-image`'s SKILL.md at 22% of its corpus.** The two references it leans on
   (`prompting-guide.md` 3,382 w, `workflows.md` 3,462 w) are the deepest in the suite. The split is
   aggressive but the corpus is normal-sized and every pillar is pointed at. **Keep the split**; only
   the filename rename (§4.3) applies.

8. **`comfyui-on-runpod` has zero provenance markers.** Single-source craft, named in the two-bar
   section. §6.2 exempts it. **Keep.**

9. **`comfyui-on-runpod` has no `## Where … sits in the suite` table, and uses "What this owns, and
   what it doesn't" instead.** It routes *outward* to RunPod's own published skills, which are
   outside this repo. That is a different table doing a different job. **Keep.**

10. **`image-production-workflows` owns `## The suite map` and the other skills do not duplicate it.**
    It is the hub; a full map in every skill would be nine copies to keep in sync. **Keep** the
    asymmetry.

11. **`character-lora-training` puts its model-routing table in the intro rather than in a
    positioning section at the tail.** It is the first thing a reader needs — the per-model quirk
    decides whether the rest of the skill even applies. **Keep.**

12. **`krea-2`'s signature section is called "The anti-AI-look and its two taxes", not "Realism".**
    The model's signature is the *absence* of a look, and the section is about paying for that.
    Section 7 headings are supposed to name the actual trait. **Keep** — and the same licence extends
    to any skill whose headline strength is not photoreal.

13. **`wan-2-2` and `minimax-h3` have no `## Per-variant settings` heading in the image-skill sense.**
    They use `## Per-mode settings` (wan) or fold settings into the task-mode selector and setup
    (minimax). Task mode, not variant, is the axis. **Keep the per-mode framing**; `minimax-h3`
    should still gain an explicit settings block (§8, finding 6) but must not be re-cut by variant.

14. **Marker density varies 0–49 per SKILL.md and that is correct.** A three-week-old model with a
    self-correcting community produces dozens of attributable claims; a three-year-old model whose
    craft is settled consensus produces few. **Do not normalise marker counts** — only apply the
    §6.2 conditional rule.

    **AMENDED 2026-08-22 — half of this held and half did not.** *Counts* still must not be
    normalised, and the conditional rule still decides each claim. But the premise is not supported
    by the thirteen-skill corpus: age and freshness tier **do not** predict density (`sdxl`, three
    years old and `stable`, out-marks `minimax-h3` at three weeks and `hot`), and the observed
    spread is driven mostly by redundant `[official]` marking and by one source being repeated up to
    twenty times. **Density is now banded — see §6.2.1.** Where §6.2.1's three limits and this clause
    disagree, §6.2.1 governs.

15. ~~**`minimax-h3` links unpublished models (SCAIL-2, LTX-2.5) as plain bold with status words.**~~
    **SUPERSEDED 2026-08-22 — all three shipped.** `scail-2`, `ltx-2-5` and `anima` are published and
    registered, so §6.5's plain-bold rule no longer applies to them and check 33 does. `minimax-h3`
    and `image-production-workflows` have already been converted. **Still unlinked and now findings:**
    `sdxl/SKILL.md:49` and `:259` (**Anima**), and `wan-2-2/SKILL.md:174, 178, 180, 251` (**SCAIL-2**).
    The underlying principle stands and applies to whatever is uncovered next (Flux 3, Bernini-R):
    a comparative note naming an uncovered competitor is more honest than silence.

16. **`minimax-h3` puts markers in table-header cells and in `###` headings.** No other skill does,
    and it looks like an error. It is not: a header-scoped marker governs every row below it, which
    is strictly better than repeating the same marker eight times down a column. §6.2 blesses both
    forms suite-wide. **Keep**, and prefer them elsewhere where a whole table or subsection rests on
    one source.

17. **`ideogram-4`'s SKILL.md is 39% of its corpus and carries an unusually long
    `## Licence & limitations` (714 words).** Its weights are non-commercial and gated while its
    outputs are owned by the user, and the split changes what a reader may legally do with the model
    they just installed. **Keep the length**; only the two-bar section needs extracting from it.

---

## 8. Grading rubric

Apply to one skill. Each numbered check emits **PASS**, **FINDING** (with the exact file, section and
proposed diff), or **N/A** (with the §7 clause or exemption that applies). Severity: **P1** breaks
trust or navigation, **P2** taxes the reader, **P3** cosmetic.

### A. Shape

1. **P1** — Does every MANDATORY section from §2 (model skill) or §3 (cross-cutting) exist, at the
   right heading level? List any missing.
2. **P2** — Is the section *order* as in §2/§3? Name any section that exists but sits out of place.
   The known case: `## Setup & ecosystem` before `## The one rule that changes everything`.
3. **P1** — Are the verbatim headings exact? Check character-for-character:
   `## The one rule that changes everything`, `## Setup & ecosystem`, `## Per-variant settings` /
   `## Per-mode settings`, `## Production pipelines & mixing models`, `## Failure modes & QC`,
   `## Pre-flight checklist`, `## Where <Model> sits in the suite`, `## Licence & limitations`,
   `## How to read the claims in this skill — two bars, by claim type`, `## Reference files`.
   Known drift: "Variant-specific settings", "Licence and known limitations", "Table of contents".
4. **P2** — Selector table present, with a "Use when…" column, and announced-but-unreleased variants
   marked?
5. **P1** — Failure-modes table ≥8 rows (≥6 for cross-cutting), and does **every cause cell state a
   mechanism** rather than restate the symptom? Quote any cell that fails.
6. **P2** — Per-variant/per-mode settings present as `###` blocks, one per variant the model
   supports, with distilled and undistilled kept apart, each covering steps / CFG / sampler /
   scheduler / resolution / negatives / seed — plus frames, fps and shift for video?
7. **P2** — Pre-flight checklist present, numbered, 8–12 items?

### B. References

8. **P1** — Do all four §4.1 core slots exist under their canonical filenames, or does a §4.1
   exemption apply? Name the exemption if claimed.
9. **P2** — Any file needing a rename per §4.3? Emit the `git mv` plus the list of internal links to
   update.
10. **P2** — Does `## Reference files` have exactly one row per file in `references/`, with no missing
    or stale rows, and does each row say *when to read it* rather than what it contains?
11. **P2** — Is the train/use boundary respected — *making* a LoRA in `lora-training.md`, *loading and
    stacking* in `setup-and-workflows.md` — with a cross-pointer in both?
12. **P3** — `## Contents` TOC on every reference ≥2,000 words, spelled `Contents` not
    `Table of contents`?
13. **P3** — Numbered `## N.` headings in any file with a TOC or that SKILL.md `§`-deep-links?

### C. Depth

14. **P2** — Total corpus inside 10,000–16,000 words (model) or 5,000–10,000 (cross-cutting)?
15. **P2** — SKILL.md inside 25–40% of corpus and 2,800–5,500 words (model) / 2,000–3,200
    (cross-cutting)? Above 5,500, name the §5.2 justification or open a finding.
16. **P1** — SKILL.md under 500 lines?
17. **P2** — Every reference 700–3,500 words? Name any under 700 (fold) or over 3,500 (split or TOC).
18. **P2** — Any **section that does not change what the reader does** (§5.3)? Quote it and propose
    a cut.
19. **P2** — Any **table or derivation duplicated in full** between SKILL.md and a reference? SKILL.md
    keeps the rule and anchor number; the reference keeps the table.
20. **P1** — Is every **silent-failure trap** in SKILL.md rather than buried in a reference (§5.4)?
    A trap is silent if getting it wrong yields a plausible wrong result, not an error.
21. **P2** — All three pillars covered or honestly routed — characters, LoRA training, production
    pipelines?

### D. Apparatus

22. **P3** — `description` 180–320 words, folded `>` scalar, containing all five §6.1 elements
    including the verbatim "even obliquely:" trigger and the closing sweep?
23. **P1** — Two-bar section present at `##` level, heading byte-identical, in the second-to-last
    slot immediately before `## Reference files`? (Known failure: `ideogram-4` has the content as a
    bolded paragraph inside `## Licence & limitations` and no heading at all.)
24. **P2** — Two-bar section contains all five §6.3 elements — lede, hard-facts roll-call with named
    official artefacts and the re-verify clause, craft roll-call with **named community authors**,
    a contested/unresolved bullet list, and the date line?
25. **P1** — Date line present, as the final paragraph of the two-bar section, opening
    `**Facts dated YYYY-MM-DD**`, ISO dates? Separately: does the skill record a *last-checked* date
    at all, distinct from the model's *release* date? (Known failures: `sdxl`, `z-image`, `wan-2-2`
    record only a release date; `comfyui-on-runpod` has its date mid-paragraph inside the hard-facts
    bar; `ideogram-4`'s sits in the licence section.)
26. **P1** — Is **every** `[flagged — re-verify]`, `[contested]` and `[pending release]` claim a
    greppable bracket marker rather than prose? Grep the skill; then read the two-bar section's
    contested bullets and confirm each carries its marker.
27. **P1** — Any **italic-parenthetical markers** left — `*(community, strong — …)*`,
    `*(Community, convergent — …)*`, `*(flagged)*`, or the inline label forms `(community)`,
    `(community, well-established)`, `**Tiled upscale (community):**`, or a `(community …)` inside a
    heading? Convert each to bracket form per §6.2, preserving the qualifier after a semicolon.
    (The italic-paren form is **fully converted as of 2026-08-22** — 55 instances across `flux-2`,
    `z-image`, `image-production-workflows` and `sdxl`, zero remaining. Run this as a regression
    test. The inline-label forms are **not** clear: seven survive, listed in §6.2.)
28. **P1** — Any **malformed marker** — nested, unterminated, or with an unclosed backtick? Grep for
    `` `\[[^]]*\[ `` and for backtick counts. (Known: one each in `krea-2` and `wan-2-2`.)
29. **P2** — Does every craft claim meeting §6.2 (a)+(b)+(c) carry a marker? Scan specifically for
    **orphan numbers**: denoise bands, step counts, LoRA strengths, rank/alpha/LR values, CFG values
    and dataset sizes with no named owner in the sentence and no marker. Also flag **bare epistemic
    hedges** standing in for a source: "settings consensus", "recur across guides", "long-standing",
    "dominates … practice". List them.
30. **P2** — **The summarise-up hop:** where SKILL.md restates craft numbers that a reference
    attributes, does SKILL.md carry the attribution too? Diff SKILL.md's ladders and settings blocks
    against the reference sections they summarise.
30a. **P2** — **Marker density inside §6.2.1's band?** Compute all three limits over the whole
    corpus: total markers/1k (2.5–7.0), the SKILL.md-to-references density ratio (≥ 0.6), and
    watchlist-class markers (≤ 1.6/1k **and** ≤ 24 absolute). Report all three even when they pass —
    the ratio is what catches the summarise-up hop. Over the band, apply §6.2.1's repair order:
    bare `[official]` first, then collapse repeats to heading/header scope, then merge sibling flags.
    Never open a finding that says "delete markers".

30b. **P2** — **Bare `[official]` audit.** Count `` `[official]` `` with no artefact in the payload.
    For each, is its claim already inside the two-bar hard-facts roll-call? If yes it is redundant by
    §6.2 and comes out; if no, give it its artefact. (Known concentrations: `scail-2` 54, `anima` 18.)

31. **P3** — Marker syntax canonical: backticked, em-dash separator, tier token from the closed set
    of six, payload ≤ ~60 chars with `;` before qualifiers, no stray vocabulary
    (`[community/unverified]`, `[official source]`, `[official-kohya]`, `[named — …]`,
    `[both above]`)?
32. **P2** — Does SKILL.md carry ≥1 `[flagged]`/`[contested]` marker, **or** an explicit
    "nothing currently flagged" line in the two-bar section? (N/A for single-source craft skills
    per §6.2.)
33. **P1** — Is every published-sibling mention a relative markdown link `[`name`](../name/)` rather
    than a bare code span? List every bare mention.
34. **P1** — Does any link reach above `skills/generative-media/`?
35. **P2** — Does the suite table cover all eight (image) or seven (video) required §6.5 axes?
36. **P2** — Is every sibling named in the suite table **linked back** from that sibling's own table?
    Emit the reciprocal edit needed.
37. **P3** — Are unpublished models named in plain bold with a status word, never linked?
38. **P3** — Tables used for parallel structure, prose for mechanism (§6.6)? Flag any settings block
    written as prose, or any two-row table.

### E. Registration

39. **P1** — Registered in `.claude-plugin/marketplace.json` and in the README table?
40. **P1** — Present in `freshness.json` with a tier, a `why_tier`, and a watchlist that includes
    **every** `[flagged]` and `[contested]` claim found in check 26? **If that list exceeds ~16
    entries the skill has failed §6.2.1's limit 3, not `freshness.json`** — fix it at the marker end
    (merge sibling flags, push separable ones down into the reference that owns them) rather than by
    writing an unmaintainable watchlist. Observed sustainable range is 6–16 entries.
41. **P2** — Does the skill's `freshness.json` watchlist reference line numbers or section names that
    still exist after any repair in this audit?

### Emitting findings

One line per finding:

```
[P1] <skill>/<file> § <heading> — <what is wrong> → <the exact edit>
```

Group by severity, P1 first. Do not batch a rename with a content edit; §4.3 renames are their own
findings so they can be applied and verified independently.
