# Audit: `skills/generative-media/ideogram-4/`

Audited against `workbench/uniformity/STANDARD.md` §8 (2026-08-22). Files read in full: `SKILL.md`
(264 lines / 4,856 words), `references/json-caption-guide.md` (3,436 w), `references/self-hosting.md`
(2,290 w), `references/api-and-webapp.md` (1,365 w). Total corpus 11,947 words. Cross-referenced
`freshness.json` (`skills.ideogram-4`), `.claude-plugin/marketplace.json`, `README.md`, and the suite
tables of `flux-2`, `z-image`, `sdxl`, `krea-2`, `wan-2-2`, `minimax-h3`, `image-production-workflows`,
`character-lora-training` (read-only, for check D36).

This is an audit only. No file other than this one was modified.

---

## Blocking (P1)

**A1 — every MANDATORY §2 section exists.** FAIL. Three MANDATORY sections are missing as their own
`##` heading:
- **Selector table** (§2 row 3) — no `## Variant selector` / `## Task-mode selector` / `## Surface
  selector` heading anywhere. Closest content is the unlabelled preset table under `## Rendering
  speed, steps & guidance` (SKILL.md:80–94), which has no "Use when…" column. See A4.
- **Per-variant/per-mode settings** (§2 row 6) — no `## Per-variant settings` / `## Per-mode settings`
  heading. Same table as above is the closest content, but it isn't `###`-blocked per mode and omits
  negatives/seed-behaviour columns. See A6.
- **Production pipelines & mixing models** (§2 row 9) — **does not exist as a section at all.** The
  entire pipeline story is one bolded sentence buried inside `## Text rendering & typography`
  (SKILL.md:141): *"**The typography pass in mixed-model pipelines.** … This pattern is practiced but
  has **no canonical named workflow yet — inferred craft, flagged as such**; the general cross-model
  rules live in the **`image-production-workflows`** skill."* No numbered stage ladder, no
  bypassable-stages statement, no decode-to-pixels handoff rule stated as its own rule (it exists
  implicitly in the ComfyUI section but isn't connected to this claim).

  **Fix — insert a new `## Production pipelines & mixing models` section** between `## Setup &
  ecosystem` (ends ~SKILL.md:183) and `## Failure modes & QC` (SKILL.md:186), and delete the bolded
  paragraph at SKILL.md:141 (its content is absorbed into the new section):

  ```markdown
  ## Production pipelines & mixing models

  Ideogram 4's natural role in a multi-model pipeline is the **text/design pass** — typography is its
  headline strength and every other open model's weakness.

  1. **Generate the base scene** in whichever model suits the imagery — `flux-2`/`z-image` for
     photoreal or illustrated content, `krea-2` for stylised/aesthetic work, `sdxl` for its checkpoint
     ecosystem.
  2. **Generate the text/design layer in Ideogram 4** — either as a transparent-background plate
     (`background: "transparent background"`, `references/json-caption-guide.md` §8) or directly
     inside the target composition using `bbox` layout to pin where each text element lands.
  3. **Composite or inpaint** the Ideogram layer into the base image — or invert the order: mask the
     text region of an Ideogram render and restyle everything else in the other model.
  4. **The handoff is always pixel-space, never latent-space:** export PNG, re-encode in the other
     model's VAE. Ideogram 4 reuses Flux.2's VAE (`flux2-vae.safetensors`) but that does **not** make
     the two latent-compatible for a direct handoff — treat every cross-model step as an image.
  5. **The direction is one-way.** Ideogram 4 has no ControlNet/PuLID path to take a base image as
     structural input, so it can only contribute the text/design layer, not receive one from upstream.

  This pattern is practiced but has **no canonical named workflow yet** `[flagged — re-verify]`; the
  general cross-model rules — denoise bands, resolution matching, the three handoff rules — live in
  [`image-production-workflows`](../image-production-workflows/).
  ```

**A3 — verbatim MANDATORY headings.** FAIL, same three headings as A1: `## Production pipelines &
mixing models`, `## Per-variant settings`/`## Per-mode settings`, and (see D23) `## How to read the
claims in this skill — two bars, by claim type`. Present and byte-exact: `## The one rule that changes
everything` (SKILL.md:23), `## Setup & ecosystem` (SKILL.md:145), `## Failure modes & QC`
(SKILL.md:186), `## Pre-flight checklist` (SKILL.md:202), `## Where Ideogram 4 sits in the suite`
(SKILL.md:220), `## Licence & limitations` (SKILL.md:236), `## Reference files` (SKILL.md:258).

**B8 — four §4.1 core reference slots present or exempted.** FAIL for `lora-training.md`. The §4.1
exemption ("omit only when no training path exists for the model at all") **no longer applies**:
`ostris/ai-toolkit` lists `ideogram-ai/ideogram-4-fp8` and fal runs a live trainer emitting
ComfyUI-format weights (`references/self-hosting.md:212–215`). Coverage currently lives inside
`self-hosting.md § 6` (SKILL.md's own reference-file candidate — see B9). **Correction to
`STANDARD.md` §4.3's own evidence:** the standard cites "63 words inside `self-hosting.md §6`" as the
reason this is thin; that figure is stale — §6 was rewritten 2026-08-13 (see its own note at
`self-hosting.md:204`) and is now **468 words** (`sed -n '202,232p' references/self-hosting.md | wc
-w`). The verdict (promote it) still holds — 468 words folding *training* and *ecosystem inventory*
together in a file about to be renamed `setup-and-workflows.md` (B9) still breaks the train/use
boundary (§4.1, B11) — but the audit trail should cite the current word count, not the stale one.

**Fix:** split `self-hosting.md § 6` ("LoRA training & fine-tuning", lines 202–231) into a new
`references/lora-training.md`. Keep all existing content (trainer table, the fal comfy-format detail,
the Civitai composition analysis, the calibration note) verbatim — it does not need rewriting, only
relocation. Add a one-line cross-pointer in the new file's opening paragraph to
`setup-and-workflows.md` (post-B9-rename) for *loading/stacking* a trained LoRA (currently there is no
"using a LoRA" content to point to — note this as an open gap for the repair agent, not something to
invent here). Add a `references/lora-training.md` row to `## Reference files` (SKILL.md:258–264).

**D23 — two-bar section at `##` level, canonical slot.** FAIL, confirmed. The section does not exist
as a heading anywhere. What survives is a **bolded lead-in paragraph nested inside `## Licence &
limitations`** (SKILL.md:246): *"**How to read the claims in this skill — two bars, by claim type.**
Ideogram 4 is an **open-weights** model…"* — followed by two more bolded-lead-in paragraphs (hard
facts, craft) and a mis-lexeme date line, all still inside the licence section, with `##
Reference files` next (SKILL.md:258). No `##` boundary separates any of it from the licence clauses
above it.

**Fix — full replacement**, verbatim heading, positioned as its own `##` section between the trimmed
`## Licence & limitations` (keep only SKILL.md:238–244, delete 246–254) and `## Reference files`:

```markdown
## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different
ways. Ideogram 4 is an **open-weights** model — gated `nf4`/`fp8` weights under a non-commercial
licence, run via the diffusers `Ideogram4Pipeline` or ComfyUI. The hosted API/web app is a *side
path*, relevant only for commercial use (the weights are NC) and for the web-only Character/Style
Reference features. The two bars below are the same shape as the other open-model skills; the
difference is **recency** — the model is a couple of months old, so the community craft layer is
thinner here than for SDXL or Z-Image, and the tooling picture is still moving.

**Hard facts — must be exact or it breaks.** This skill treats the following as hard facts: the
architecture (9.3B single-stream DiT, 34 layers) and the Qwen3-VL-8B-Instruct text encoder (13
concatenated hidden-state layers); the JSON caption schema and `CaptionVerifier` rules (key order,
required fields, abort-on-warning behaviour); the three sampler presets and their exact
`mu`/`std`/guidance schedules; the Magic Prompt backends and system-prompt rules; quantisation
(`nf4`/`fp8`) and Hugging Face gating; the licence terms; and the `Ideogram4Pipeline` /
`run_inference.py` / ComfyUI node surface. **Source of truth is official** — the `ideogram-oss/ideogram4`
GitHub repo, the HF model cards, and the licence text itself. A wrong quant filename 404s the
download; a misread non-commercial licence is a legal problem, not a rendering bug. **Young and
volatile:** quant filenames (the `nf4`-vs-`nvfp4` naming), VRAM numbers, ComfyUI template details, and
LoRA tooling all move — **re-verify before relying on them, regardless of who said it.** LoRA support
in particular went from "does not exist" to "ai-toolkit and fal both ship it" inside ten weeks.

**Craft — what actually makes a good image.** Almost entirely **JSON caption craft**: single-subject
elements, background-as-shell, dual-mention of shell-affixed hero objects, specificity, and `bbox`
layout strategy. **The authoritative source here is the community** — the people self-hosting
Ideogram 4 in ComfyUI/diffusers, exactly as for SDXL or Z-Image — with one caveat: at a couple of
months old, no individual practitioners have built the kind of named, citable track record the older
skills draw on, so this skill's craft leans on Ideogram's own **open-source Magic Prompt system
prompt** (an official artefact, not community testimony) plus early self-hosted reports. Treat the
caption-craft rules as confident and structural; treat the realism/aesthetic defaults as informed
taste — stated as such throughout. **The LoRA ecosystem is real but lopsided** — 33 published on
Civitai, essentially all style work, no character LoRAs and no identity adapters.

**Independent positioning** (third-party evals): Ideogram 4 ranks #1 among open-weight models on
DesignArena and #2 on a blind designer-preference eval (behind GPT Image 2) — strongest on
text/typography/design, weakest on photoreal faces.

**Contested / unresolved points:**
- Whether Edit/Upscale/Reframe/Replace-Background actually run the 4.0 model through
  `/v1/ideogram-v3/*` paths is an inference from the pricing page, not a stated fact
  `[flagged — re-verify]`.
- The ComfyUI-native 4-bit quant filename — `nf4` (per the HF repo name) or
  `ideogram4_nvfp4_mixed.safetensors` (per some community workflows) — is unresolved
  `[flagged — re-verify]`.
- The `CFGOverride` node's `0.7` field in the official ComfyUI template reads as an override-start
  fraction, but its exact meaning is unconfirmed `[community — single report; re-verify]`.
- Community GGUF support (`stduhpf/ideogram-4-gguf`, `city96/ComfyUI-GGUF`) for the architecture is
  early and undocumented `[community — early; re-verify]`.
- The FLASH API tier is announced but still returns 400 "coming soon" `[pending release]`.
- Using Ideogram 4 as the typography/design pass in a mixed-model pipeline is practiced but has no
  canonical named workflow yet `[flagged — re-verify]`.

**Facts dated 2026-08-13.** LoRA tooling, quant filenames, the FLASH tier, and the v3-edit-path
inference move fastest here — re-verify each before relying on it.
```

**D25 — date line, `Facts dated YYYY-MM-DD`, own paragraph.** FAIL. Currently `**Release:** 3 June
2026. **Skill reviewed 2026-08-13**` (SKILL.md:254), wrong lexeme (conflates release date with
last-checked date, contrary to §6.4), and sits inside `## Licence & limitations` because the two-bar
section doesn't exist. Fixed by the D23 replacement above (its final paragraph). Keep `**Release:** 3
June 2026` where it already lives in the intro material — it is legitimate model-fact content, not the
skill-dating line (§6.4 explicitly says don't move it, just add the missing line elsewhere).

**D26 — every flagged/contested/pending-release claim is a greppable bracket marker.** FAIL. One
concrete violation, and it's the clearest one in the file: SKILL.md:141 states *"no canonical named
workflow yet — inferred craft, flagged as such"* — the word "flagged" appears in prose but **no
bracket marker follows it**, so `freshness.json`'s grep-based tooling cannot see it. Fixed by moving
this claim into the new Production Pipelines section (A1) with `` `[flagged — re-verify]` `` attached.

**D27 — italic-parenthetical markers.** PASS / N/A. None found (`grep` clean across SKILL.md and all
three references). This skill did not inherit the `sdxl`/`z-image` italic-parenthetical habit.

**D28 — malformed (nested/unterminated) markers.** PASS. None found.

**D31 (elevated — see note) / D33 — every sibling mention is a relative markdown link.** FAIL,
total. **Every single sibling mention in this skill is a bare code span — zero markdown links exist
anywhere in SKILL.md or the three reference files.** Full list:

| Location | Bare mention | Should be |
|---|---|---|
| SKILL.md:141 | `**`image-production-workflows`**` | `[`image-production-workflows`](../image-production-workflows/)` |
| SKILL.md:158 | `**`flux-2`**`, `**`z-image`**`, `**`character-lora-training`**` | linked, each |
| SKILL.md:225 | `flux-2`, `z-image`, `sdxl` | linked, each |
| SKILL.md:226 | `` `ideogram-4-fp8` `` (not a sibling — leave), `krea-2` | `krea-2` linked |
| SKILL.md:227 | `sdxl`, `z-image`, `flux-2`, `character-lora-training` | linked, each |
| SKILL.md:228 | `z-image`, `sdxl` | linked, each |
| SKILL.md:229 | `krea-2` | linked |
| SKILL.md:230 | `sdxl`, `flux-2`, `z-image` | linked, each |
| SKILL.md:231 | `image-production-workflows` | linked |
| SKILL.md:232 | `wan-2-2` | linked |

**Fix:** mechanical pass, `` `name` `` → `` [`name`](../name/) `` at each site above. None of these
reach above `skills/generative-media/`, so D34 is clean once this lands.

**D34 — no link reaches above `skills/generative-media/`.** PASS / N/A today (no links exist to check —
see D33). Verify this holds once D33's links are added; none of the proposed targets do.

**D40 — `freshness.json` watchlist covers every flagged/contested claim (check D26/D24).** FAIL,
partial. The skill's `freshness.json` entry (tier `hot`, `last_checked: 2026-08-13`) has a 9-item
watchlist that covers most of what this audit found, but **three flagged/unverified claims currently
in the skill body have no corresponding watchlist entry**:
1. `CFGOverride` field-meaning `` [community/unverified] `` (`self-hosting.md:164`).
2. GGUF/`city96/ComfyUI-GGUF` support status, `` [community/early — flagged] `` (`self-hosting.md:187`).
3. The typography-pass "no canonical named workflow yet" claim (SKILL.md:141 → new production-pipelines
   section per A1) — doubly missing since it also lacks its own bracket marker (D26).

**Fix:** add three watchlist entries to `freshness.json`'s `skills.ideogram-4.watchlist`, mirroring the
existing entry shape (`id`, `type`, `claim`, `where`, `check`).

---

## Standard (P2)

**A2 — section order matches §2.** PASS for everything present. `## The one rule…` correctly precedes
`## Setup & ecosystem` (the resolved z-image-exception rule). No section that exists sits out of
order; the only order problems are the *missing* sections covered under A1.

**A4 — selector table with a "Use when…" column.** FAIL. No selector table exists under any of the
three sanctioned headings. The nearest candidate, the preset table at SKILL.md:84–90 (`Preset | API
rendering_speed | Steps | Guidance schedule | mu | std | API $/image`), has no "Use when…" column.
**Fix:** rename the section heading `## Rendering speed, steps & guidance` → `## Per-mode settings`
(A6 folds into the same fix — this model's only real "mode" axis is the three speed presets) and add
a "Use when…" column to the table, e.g. Quality → "final delivery, hero shots, 2K"; Default → "most
iteration work"; Turbo → "drafts, batch exploration." This single edit closes both A4 and A6.

**A6 — per-variant/mode settings as `###` blocks.** FAIL (see A4 fix — same table, same rename). As
currently written it is one flat table with no negatives/seed-behaviour treatment; Ideogram 4 doesn't
have per-preset negatives or seed differences to report (this is a single-checkpoint model, not
multi-variant), so `###` sub-blocks per preset would be mostly-repeated boilerplate. **Recommend**
folding this into a JUSTIFIED note alongside the rename rather than forcing three near-identical
`###` blocks — record the reasoning in the skill the way §7.13 does for `wan-2-2`/`minimax-h3`
("one axis, not per-checkpoint variants").

**B9 — reference-file renames.** FAIL, per §4.3, two renames:
- `self-hosting.md` → `setup-and-workflows.md` (P2). Contents are exactly the canonical slot —
  diffusers, CLI, ComfyUI graph, quant/VRAM, gating. `git mv
  skills/generative-media/ideogram-4/references/self-hosting.md
  skills/generative-media/ideogram-4/references/setup-and-workflows.md`, then update the three
  `references/self-hosting.md` mentions in SKILL.md (lines 159, 182, 264) and the self-referential
  ones inside the file itself.
- `api-and-webapp.md` → `api-and-hosted.md` — **P3**, explicitly low-priority per §4.3. Same
  mechanical treatment when convenient; not urgent.

**B11 — train/use boundary with cross-pointer both ways.** FAIL, tied to B8. Currently there is no
`lora-training.md` to hold the *making* side, so the boundary can't be expressed structurally.
Resolved by the B8 fix; once split, add "loading and stacking a trained LoRA is
`setup-and-workflows.md`" (post-B9-rename) to the new file's opening paragraph. Note for the repair
agent: `setup-and-workflows.md`/`self-hosting.md` currently has **no LoRA-loading/stacking section at
all** (it documents training and the ecosystem, not applying a `.safetensors` LoRA in ComfyUI/diffusers)
— that's a second, smaller gap this audit surfaces as a byproduct of tracing the boundary, not
something to silently invent content for.

**C19 — table/derivation duplicated in full between SKILL.md and a reference.** FAIL, with a caveat.
`## The JSON caption schema (canonical)` (SKILL.md:47–77) reproduces `json-caption-guide.md § 1`'s
tables near-verbatim: the top-level field table, the `style_description` key-order table
(SKILL.md:59–62 = `json-caption-guide.md:29–32`), and the `elements` key-order table
(SKILL.md:66–69 ≈ `json-caption-guide.md:56–61`). Per §5.4 this should be an anchor-number pointer in
SKILL.md with the full table living only in the reference. **Caveat for the reviewer:** this may be a
legitimate 18th justified deviation rather than a straight finding — the JSON schema *is* "the one
rule that changes everything" for this model in a way no other skill's per-variant settings are, and
getting key order wrong is a **loud** failure (`CaptionVerifier` aborts), not the silent-failure case
§5.4 protects. Flagging as FAIL per the mechanical rubric, but recommend the human reviewer apply the
§1 test explicitly here rather than trim on autopilot — a bad trim would hollow out the section that
makes this skill's "one rule" concrete.

**D24 — two-bar section's 5 required elements.** FAIL as currently structured (see D23 for the full
replacement, which fixes this in one motion). Specific gaps in the *current* text: the hard-facts and
craft "roll-calls" are single run-on paragraphs, not enumerated lists; the craft paragraph names **no
individual community authors** anywhere (unlike every sibling's craft bar) — it says "the open-weights
community" / "the people self-hosting it," never a name; and the contested/unresolved bullet list is
**entirely absent**. The D23 replacement text supplies all of this.

**D29 — orphan craft numbers / bare epistemic hedges.** PASS overall. This skill is unusually
well-attributed: the Caption-craft (SKILL.md:98–111) and Realism (SKILL.md:115–125) sections both open
with an explicit source statement in their lede ("These come straight from Ideogram's open-source
Magic Prompt system prompt…"), which satisfies §6.2(c) for every sentence under that lede. No bare
hedges ("settings consensus," "recur across guides," etc.) were found — `grep` clean. The one orphan
is the D26 case (already counted there, not double-counted here).

**D30 — summarise-up hop.** PASS. The sampler-preset numbers SKILL.md repeats from
`self-hosting.md`/`json-caption-guide.md` are hard facts (architecture, schema, presets), which §6.2
exempts from per-instance marking as long as the two-bar hard-facts roll-call names them — it now does
(D23 fix). No craft-number duplication requiring the hop treatment was found.

**D32 — SKILL.md carries ≥1 `[flagged]`/`[contested]` marker, or an explicit "nothing flagged" line.**
FAIL. SKILL.md today carries **zero** markers of any kind — every marker in the skill lives only in
the references. This is a `hot`-tier skill (`freshness.json`), so the floor rule is not optional here.
Fixed by the D23 two-bar section (six markers) and the A1 production-pipelines section (one marker).

**D35 — suite table covers all 8 required image axes (§6.5).** FAIL. Missing axis 6, **"Commercial use
under the licence"** — the one axis this specific model needs most, since Ideogram 4 is the only
model in the suite whose *weights* carry a use-purpose restriction the others don't. **Fix:** add a
row to `## Where Ideogram 4 sits in the suite` (SKILL.md:222–233):

```markdown
| Commercial use under the licence | Open weights are **non-commercial only** — the restriction is on purpose, not on hosting location | Hosted API/web app (`references/api-and-hosted.md`), or a separate paid weights licence from Ideogram |
```

**D36 — bidirectional sibling links.** MOSTLY PASS. `flux-2`, `z-image`, `sdxl`, `krea-2`,
`image-production-workflows`, and `character-lora-training` all already name `ideogram-4` in their own
suite tables or text. **One gap found:** `wan-2-2/SKILL.md` and `minimax-h3/SKILL.md` do not mention
`ideogram-4` at all, despite `ideogram-4`'s own table linking to `wan-2-2` ("Making it move,"
SKILL.md:232). This is a finding *against `wan-2-2`*, out of this audit's scope to fix (a sibling
agent owns that file) — flagging here per the bidirectionality rule ("an audit finding is valid for a
one-way link") so it's on record.

---

## Cosmetic (P3)

**B12 — `## Contents` TOC on references ≥2,000 words.** FAIL, both already named by the standard
itself (§6.7): `references/self-hosting.md` (2,290 w) and `references/json-caption-guide.md` (3,436 w)
both lack a `## Contents` section. **Fix:** add a `## Contents` block right after each file's opening
paragraph, linking its existing (already-numbered) `## N.` headings.

**B13 — numbered `## N.` headings where a TOC/§-link is used.** PASS. Both files already use `## N.
Title` numbering, and SKILL.md already deep-links with `§` (e.g. `references/self-hosting.md § 4`,
`references/json-caption-guide.md § 3`) — only the `## Contents` header itself is missing (B12).

**D22 — description 180–320 words, 5 required §6.1 elements.** MOSTLY PASS (279 words, verbatim "even
obliquely:" trigger present, full enumerated trigger list). Two small gaps: (a) the licence gate is
folded into the first item of the trigger *list* rather than **bolded, before** the trigger phrase, as
§6.1 point 2 specifies; (b) there is no closing-sweep sentence at the end. **Fix:** insert *"**The open
weights are non-commercial only — for commercial output, route through the hosted API/web app
instead.**"* immediately before "Use this whenever the user touches Ideogram 4…", and append *"Use
this for any question about Ideogram 4 in any context."* as the final sentence.

**D31 — marker syntax canonical (backtick, em-dash, closed tier set, ≤60 chars).** FAIL, extensively —
this is the second headline finding the standard-setting agent flagged, and it is confirmed. Every
marker in this skill uses bold-asterisk or bare bracket form, never backticks, and roughly two-thirds
use non-canonical tier vocabulary outside the six-token closed set. Full enumeration (24 occurrences,
3 already canonical and left as-is):

| # | File:Line | Current | Canonical replacement |
|---|---|---|---|
| 1 | `api-and-webapp.md:16` | `**[official-via-docs]**` | `` `[official — developer.ideogram.ai docs]` `` |
| 2 | `api-and-webapp.md:36` | `**[flagged]**` | `` `[flagged — re-verify]` `` |
| 3 | `api-and-webapp.md:48` (heading) | `[official-via-docs]` | `` `[official — docs.ideogram.ai]` `` |
| 4 | `api-and-webapp.md:53` (heading) | `[confirmed from client source]` | `` `[official — ideogram4 client source]` `` |
| 5 | `api-and-webapp.md:71` | `**[flagged]**` | `` `[flagged — re-verify]` `` |
| 6 | `api-and-webapp.md:77` (heading) | `[ideogram.ai/api-pricing, official]` | `` `[official — ideogram.ai/api-pricing]` `` |
| 7 | `api-and-webapp.md:90` | `**[flagged]**` | `` `[flagged — re-verify]` `` |
| 8 | `api-and-webapp.md:92` (heading) | `[third-party — approximate, official pricing page was inaccessible]` | `` `[flagged — re-verify]` `` |
| 9 | `api-and-webapp.md:101` | `**[flagged]**` | `` `[flagged — re-verify]` `` |
| 10 | `api-and-webapp.md:107` | `**[official-via-docs]**` | `` `[official — docs.ideogram.ai]` `` |
| 11 | `api-and-webapp.md:112` | `[confirmed: developer.ideogram.ai/api-reference/generate-v3]` | `` `[official — developer.ideogram.ai/api-reference/generate-v3]` `` |
| 12 | `api-and-webapp.md:113` | `[confirmed: docs.ideogram.ai/style-reference]` | `` `[official — docs.ideogram.ai/style-reference]` `` |
| 13a | `self-hosting.md:7` | `**[official]**` | `` `[official]` `` |
| 13b | `self-hosting.md:7` | `**[community/single-source]**` | `` `[community — single report; re-verify]` `` |
| 14 | `self-hosting.md:13` | `**[official]**` | `` `[official — ideogram-oss/ideogram4 repo]` `` |
| 15 | `self-hosting.md:20` (cell) | `[official]` | `` `[official — HF model card]` `` |
| 16 | `self-hosting.md:23` | `**[official]**` | `` `[official — HF model card]` `` |
| 17 | `self-hosting.md:88` (heading) | `[official source]` | `` `[official — ideogram4.sampler_configs]` `` |
| 18 | `self-hosting.md:137` | `**[official]**` | `` `[official — ComfyUI template JSON]` `` |
| 19 | `self-hosting.md:164` | `**[community/unverified]**` | `` `[community — single report; re-verify]` `` |
| 20 | `self-hosting.md:177` | `**[official template observation]**` | `` `[official — ComfyUI template JSON]` `` |
| 21 | `self-hosting.md:181` | `[official]` | `` `[official — HF model card]` `` |
| 22 | `self-hosting.md:182` | `**[single-source, low confidence]**` | `` `[community — single report; re-verify]` `` |
| 23 | `self-hosting.md:183` | `**[flagged]**` | `` `[flagged — re-verify]` `` |
| 24 | `self-hosting.md:187` | `**[community/early — flagged]**` | `` `[community — early; re-verify]` `` |
| 25 | `self-hosting.md:193` | `**[official]**` (governs 2 list items) | `` `[official]` `` (list-scoped) |
| — | `self-hosting.md:212` | `` `[official — repo]` `` | already canonical, leave |
| — | `self-hosting.md:213` | `` `[official — fal docs]` `` | already canonical, leave |
| — | `self-hosting.md:229` | `` `[community]` `` | already backticked; source is named in the same sentence so the marker is optional per §6.2(c) — leave |

None of the non-canonical tokens above are the specific strays §6.2 names verbatim
(`[official-kohya]`, `[named — …]`, `[both above]`), but several are functionally identical strays not
yet on that list (`[official source]`, `[official template observation]`, `[confirmed from client
source]`, `[confirmed: …]`, `[single-source, low confidence]`, `[third-party — …]`) — worth folding
into the §6.2 normalisation table so the next audit doesn't have to re-derive the mapping.

**D37 — unpublished models named in plain bold with a status word.** N/A. No unpublished models
(SCAIL-2, LTX-2.5, Anima, Flux 3) are mentioned anywhere in this skill.

**D38 — tables for parallel structure, prose for mechanism.** PASS. No violations of substance. Two
2-row tables exist (the `style_description` key-order table SKILL.md:59–62 and the `elements` key-order
table SKILL.md:66–69) — technically under §6.6's "never a table for a one-or-two-row list" line, but
these are strict schema lookup tables (a reader scans for "which row am I"), not narrative lists; the
same reasoning that makes the FLASH/pricing rows tabular applies. Not treating this as a finding.

**Intro-paragraph phrase drift (unnumbered, cosmetic).** SKILL.md:11 reads *"Its defining trait:"*
where §2 row 1 specifies the phrase *"**The defining trait:**"* verbatim. Trivial one-word fix
(`Its` → `The`), noted for completeness since the standard is explicit about this phrase.

---

## Verdicts already correct — no finding

- **A5** — failure-modes table: 9 rows (≥8 required), every cause cell states a mechanism, not a
  restated symptom. PASS.
- **A7** — pre-flight checklist: 11 numbered items. PASS.
- **B10** — `## Reference files` table: one row per current file, each states *when* to read it, not
  what it contains in the abstract. PASS today; will need a fourth row once B8's `lora-training.md`
  split lands.
- **C14** — total corpus 11,947 words, inside 10,000–16,000. PASS.
- **C15** — SKILL.md at 4,856 w / ~40% share. **JUSTIFIED** per `STANDARD.md` §7.17 by name — the
  long `## Licence & limitations` section is exactly why. Extracting the two-bar content (D23) moves
  words out of that section without deleting them, so this justification and the % figure both survive
  the repair.
- **C16** — 264 lines, well under the 500-line cap. PASS.
- **C17** — every reference between 700 and 3,500 words. PASS (json-caption-guide.md at 3,436 is close
  to the ceiling but inside it).
- **C18** — no padding sections found; the skill is dense throughout.
- **C20** — every silent-failure trap found lives in SKILL.md, not only in a reference: the
  bbox square-on-non-square distortion (SKILL.md:111), the floor-emitted-as-`obj` leg-burying bug
  (SKILL.md:104), and the `gemma4`-downloaded-but-unwired gotcha (SKILL.md:180) are all present at the
  top level. PASS.
- **E39** — registered in `.claude-plugin/marketplace.json:29` and `README.md:19`. PASS.

---

## The three things beyond the rubric

### 1. Unattributed craft

This skill is unusually clean here — the two sections most at risk (Caption craft, Realism) both open
with an explicit source statement that governs everything beneath it (§6.2(c) exemption applies
throughout both). The one real violation is **SKILL.md:141**, already covered under D26/A1: a claim
that literally says "flagged as such" with no actual marker attached. No orphan numeric craft claims
(denoise/CFG/rank bands with no owner) were found — this model's LoRA-training coverage deliberately
gives no hyperparameters (the freshness watchlist notes why: none have been published), so there's
nothing un-owned to flag.

### 2. Staleness for a 2026-08-22 reader

`freshness.json` confirms this skill was **not** touched in the 2026-08-22 refresh
(`last_checked: 2026-08-13`, tier `hot`, `cadence_days: 1` — meaning it is **9 checks overdue** by its
own cadence). Reasoning, not browsing, on what reads stale nine days on:
- The "**Young and volatile**" framing throughout (two-bar section, self-hosting.md:7's confidence
  labelling) was accurate at 71 days post-launch on 2026-08-13; at 80 days it is only marginally more
  aged, so this is not yet a rewrite trigger — but it is the kind of framing that expires quietly, the
  same way the "days-old" language did before it was caught (per `freshness.json`'s own
  `ideogram4-days-old-framing-expired` resolved finding). Worth a fresh look at the next check, not this
  one.
- The FLASH tier, the `nf4`/`nvfp4` naming conflict, and the v3-edit-path inference are all
  explicitly named as fast-moving in the skill's own text — nine days without a check is exactly the
  kind of gap the `hot` tier and `cadence_days: 1` exist to prevent. This isn't a content defect so much
  as confirmation that the freshness *process*, not the skill's prose, is what's behind.
- One `freshness.json` entry is **independently stale regardless of this audit**: the `api-pricing`
  watchlist item's `where` field cites `references/api-and-hosted.md`, a filename that has never
  existed in this skill (the real file is `api-and-webapp.md`, see B9). That's a pre-existing state-file
  bug, not something this pass introduced.

### 3. Over-conformity risk — `## Do not touch`

Besides `json-caption-guide.md` (already protected by §7.3 — do not flatten it into a
`prompting-guide.md`):

- **The official-vs-taste distinction in `json-caption-guide.md § 5` / SKILL.md:125.** The closing
  paragraph of the Realism section explicitly separates "these are the expander's taste, not model
  prohibitions" from "the structural schema rules elsewhere… are model facts, independently confirmed."
  A mechanical marker-conversion pass could try to compress this into a single bracket marker — don't.
  The prose *is* the epistemic content; a marker cannot carry "here is why these two kinds of claim in
  the same section deserve different confidence," and that argument is exactly what §1 of the standard
  asks every skill to make.
- **`self-hosting.md:7`'s own attribution-key line** ("Sources are labelled **[official]**… vs
  **[community/single-source]**…"). The *tokens* need converting per D31, but the *practice* — a file
  declaring its own confidence key up front — is exactly what §6.7 blesses as optional per-file
  practice. Convert the vocabulary, keep the sentence.
- **The Civitai download-count calibration note** (`self-hosting.md:223`, "Civitai reports downloads at
  the *model* level, not the version level, so a big number next to an Ideogram LoRA usually is not an
  Ideogram number"). This is a specific, mechanism-teaching correction to a number a reader would
  otherwise misread — don't cut it as padding under C18, and don't let a rename/restructure pass drop
  it when B8's file split happens.
- **The `## The JSON caption schema (canonical)` duplication (C19).** Already flagged as a mechanical
  FAIL, but repeating the warning here: this is the model's actual "one rule," and a blind trim to an
  anchor-number pointer (the way `minimax-h3`'s frame-count formula was trimmed) would gut the one
  section a reader is most likely to open SKILL.md *for*. If trimmed, keep at minimum the field/required
  status table and the bbox axis-order gotcha; the full key-order tables can move to
  `json-caption-guide.md` only.

---

## `characters.md` — verdict

**JUSTIFIED absence**, per `STANDARD.md` §4.1's exemption and §7.4 (which names `ideogram-4` by
name as the qualifying case). Confirmed independently: no identity adapters exist for Ideogram 4
(ControlNet/PuLID/IP-Adapter all absent per SKILL.md:149 and `self-hosting.md:229`), there is no edit
variant, and **zero of the 33 published Civitai LoRAs are character work** (`self-hosting.md:221`,
"Character/likeness LoRAs are essentially absent"). The exemption's second condition — an explicit
"Consistent characters → reach for X" row in the suite table — is also met (SKILL.md:225, routing to
`flux-2`, `z-image`/`sdxl`, or hosted Character Reference). If a `characters.md` were forced into
existence today, it would either (a) be a stub restating "there is nothing here yet, go to `flux-2`/
`z-image`" — which is strictly worse than the current routing row, since a reader who opens a
`characters.md` expects content and gets a redirect instead of a redirect *at the point they'd look for
it* — or (b) speculate about the untested character-LoRA path SKILL.md:156 already correctly frames as
"exploratory, not a recipe." Neither improves on the current state. **No file should be added.**
