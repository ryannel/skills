# Audit: `skills/generative-media/comfyui-on-runpod/`

Graded against STANDARD.md §3 (cross-cutting-skill shape) + §8 rubric, with model-skill-only
checks (selector table, per-variant settings, four core reference slots, licence section, suite-table
axes) marked N/A per the task brief. Read: SKILL.md (283 lines / 2,940 body words), both references
(`volume-and-models.md` 1,404 w, `serverless-comfyui.md` 1,198 w — total corpus 5,732 w), `freshness.json`'s
`comfyui-on-runpod` entry, `CLAUDE.md`, and `image-production-workflows/SKILL.md` for the boundary check.

---

## Blocking

**[P1] SKILL.md § "How to read the claims in this skill — two bars, by claim type" — date line missing in canonical form/position (§6.4).**
Evidence: `SKILL.md:270` — `"...**The dual mount root was validated against live infrastructure on 2026-08-13** (a serverless worker enumerated exactly the volume's models/vae/), and the runpodctl command-surface split was verified against 2.3.0-be4ced4."` The date is embedded mid-sentence inside the hard-facts paragraph; the section's actual last paragraph (`SKILL.md:274`, "One thing deliberately **not** claimed: GPU recommendations and prices…") carries no date at all.
This is exactly the case STANDARD.md §6.4 names for this skill by name: *"Mid-paragraph inside the hard-facts bar, not a standalone line | `comfyui-on-runpod` (1)."*
Fix: add a final paragraph to the two-bar section, after the GPU-exclusion note:
```
**Facts dated 2026-08-13.** The `runpodctl` command surface and endpoint knobs are what moves
fastest here — re-verify those before relying on them; the ComfyUI-side contract
(`extra_model_paths.yaml` keys, loader directories) is stable.
```
Leave the existing mid-paragraph date where it is (it's doing useful validation-provenance work) — this is additive, not a move.

**[P1] Two-bar section — the zero-marker exemption is claimed but its "single named source" is never actually named.**
Evidence: the craft bar (`SKILL.md:272`) says only *"distilled from a running studio"*; the hard-facts bar (`SKILL.md:270`) says *"a working production configuration"*; a third phrase, *"a working production volume"*, appears at `SKILL.md:103`. Three different vague phrasings, no consistent identifier, no repo, no system name.
§6.2's exemption is conditional on exactly this: *"A skill whose craft has exactly one source, **named** in the two-bar section, is exempt from per-claim marking."* CLAUDE.md itself names the actual source — `../video-generation`, "the operational source of truth that `comfyui-on-runpod` was generalised from" — but the published skill never says so. As written, a reader has no way to tell "a running studio" is one consistent thing rather than three different anecdotes, which is the exact ambiguity the exemption is supposed to rule out.
Fix: pick one phrase and use it everywhere (craft bar, `SKILL.md:103`, hard-facts bar), e.g. *"a single production ComfyUI-on-RunPod deployment external to this repo"* — naming it as one system without necessarily exposing the private repo name. This doesn't require retrofitting per-claim brackets; it requires the existing sentences to agree with each other.

---

## Standard

**[P2] Boundary table doesn't distinguish this skill from `image-production-workflows`.**
Evidence: the "What this owns, and what it doesn't" table (`SKILL.md:15-26`) has 8 rows routing to `runpod`, `runpod-usage`, `companion-clis`, and the model skills — but no row for `image-production-workflows`, and that skill's SKILL.md (checked directly) has no row back either; its "suite map" (`image-production-workflows/SKILL.md:147-163`) never mentions `comfyui-on-runpod`. Both skills are grouped in the same marketplace plugin entry and both describe "running" something — one the multi-stage image pipeline, one the deployment plumbing — so a reader could plausibly land in either looking for the other.
Fix: add a row to the boundary table: `| Multi-stage image pipelines, denoise bands, mixing models, decode-to-pixels handoff | [\`image-production-workflows\`](../image-production-workflows/) |`, and the reciprocal row in that skill's suite map (e.g. `| Deploying/running any of this on RunPod | comfyui-on-runpod |`).

**[P2] Two-bar section is missing the required contested/unresolved element (§6.3 item 4).**
Evidence: `SKILL.md:268-274` contains the hard-facts bar and craft bar but no "Contested / unresolved points" bullet list and no explicit "nothing is currently contested" line — required content item 4 is simply absent, not satisfied by anything else in the section.
Fix: add one line before the (to-be-added) date line: *"**Nothing is currently contested or flagged.** The 2026-08-13 pass resolved every open finding (see `freshness.json`); the watchlist below tracks what could still drift."*

---

## Cosmetic

**[P3] Two-bar section omits the optional lede sentence.**
Evidence: `SKILL.md:270` jumps straight to "**Hard facts — must be exact or it breaks.**" with no framing sentence. §6.3 item 1 calls this "Optional" but also says "add where missing," and 7 of 10 sibling skills carry it.
Fix: prepend *"This skill holds two kinds of claim to two different standards, because they fail in two different ways."*

**[P3] `references/volume-and-models.md` has no opening scope paragraph.**
Evidence: the file goes straight from the `# Volume layout…` title into the numbered TOC (`volume-and-models.md:1-9`) with no sentence stating what it owns/doesn't, unlike its sibling `serverless-comfyui.md:3` (*"Running ComfyUI behind a RunPod serverless endpoint — the programmatic path, and where it differs from the interactive pod everyone starts with."*). §6.7: "Each reference opens with a one-paragraph statement of what the file owns and what it does not."
Fix: add one sentence before the TOC, e.g. *"Everything ComfyUI needs to find a model on the volume: the dual-root config, the placement table, LoRA foldering, and the manifest that makes a volume reproducible. Deployment mechanics (pods, endpoints, dispatch) are `serverless-comfyui.md`."*

---

## N/A (model-skill-only checks, per task brief)

Selector table, per-variant/per-mode settings, four §4.1 core reference slots, `## Licence & limitations`,
train/use LoRA boundary, §6.5 required suite-table axes, `## Where … sits in the suite` heading (JD#9:
the boundary table correctly substitutes — it routes outward to RunPod's own out-of-repo skills, a
different job than the in-suite positioning table). Gate section (§3.3): no legal/policy/cost precondition
rules the reader out entirely, so none is warranted. Tool/status section (§3.6): the one version-sensitive
dependency (`runpodctl` 2.3.0 surface split) is already pinned, dated and in the freshness watchlist inline
— a separate status table would just restate it. Marker-density floor (check 32): N/A per §6.2's explicit
exemption for this skill — contingent on the Blocking finding above being fixed.

---

## Registration (checks 39-41) — all PASS

- Registered in `.claude-plugin/marketplace.json` (line 36) and README.md (line 26) with an accurate
  description.
- `freshness.json` carries tier `active` (14-day cadence), a substantive `why_tier`, 5 watchlist items and
  4 resolved `open_findings`, all still pointing at real, current sections/lines. No stale watchlist
  pointers found.

---

## Depth verdict — the 51%/55% split (SKILL.md 2,940 words / corpus 5,732 = 51%; by strict word count
including frontmatter, 3,130/5,732 = 55%)

**JUSTIFIED — no demotion needed.** By the letter of §5.2, cross-cutting skills have no percentage
target at all (only model skills do); the only absolute caps are corpus 5,000-10,000 (actual: 5,732, in
band) and SKILL.md 2,000-3,200 words (actual: 2,940, in band, 260 words of headroom). Applying the real
test (§5.3 — "every section must change what the reader does"): I read every section top to bottom
looking for padding and found none. The `extra_model_paths.yaml` block in SKILL.md is not a full
duplicate of the reference's (13 of 17 keys, reference has the complete 17-key version) — it's the
worked example for "the one rule," which is the one place a full worked example belongs. The manifest
YAML in SKILL.md is similarly a single-entry excerpt; the reference carries the full schema plus a
second entry type. The high percentage is a symptom of thin (but appropriately sized, 700-3,500-word-band)
references, not SKILL.md bloat. This is the same shape as JD#7 (`z-image`, 22% low outlier, kept) — a
normal-sized corpus with a lopsided split that the standard already tolerates. No content to demote.

---

## Cost-guard prominence — PASS

`--terminate-after` appears in four independent places: the frontmatter description's trigger list
("why did my pod bill all night"), a dedicated **Cost guards that actually work** subsection inside
`## Pod or serverless?` (including the `runpodctl pod create` vs `create pod` trap, a genuinely
easy-to-miss footgun), a failure-table row ("Surprise bill overnight"), and pre-flight checklist item 7.
Not buried — not in the very first section, but the "one rule" slot is correctly reserved for the
higher-frequency dual-mount-root failure per §1's leverage test, and cost guidance is reinforced at
every other natural touchpoint. **Deliberately out of scope, correctly:** the "stop and wait for
explicit approval before any billable action" operating rule (the user's `runpod-cost-gate` rule,
sourced from `../video-generation/.agents/rules/cost-gate.md`) is agent-operating behavior, not
ComfyUI-specific craft — it belongs to the agent driving RunPod (skill-testbed's territory per
CLAUDE.md's "Scope" section), not to this documentation skill. Including it here would itself be scope
drift across the authoring/operational line CLAUDE.md draws. No finding.

## New video skills (`ltx-2-5`, `scail-2`) — no update needed here

Checked whether this skill needs GPU-selection or manifest-schema changes for the two skills being
authored in parallel. It doesn't: GPU selection is explicitly and deliberately out of scope
(`SKILL.md:274`, "GPU recommendations and prices… `runpod-usage` owns the general question and each
model skill owns its own requirement"), and the manifest schema (`architecture` / `*_filename` /
`clip_type` / `files[]`) is model-agnostic — it already uses `ltxv` as a throwaway example
`CLIPLoader` type (`references/volume-and-models.md:97`) without needing to. Nothing to flag.

## Scope drift — none found

No embedded credentials, no scripts that execute against live infrastructure, no content that duplicates
skill-testbed's cost-gate mechanism or video-generation's production config. All infra facts are
presented as documentation with dated provenance, consistent with "skill-factory authors, does not run."

## Do not touch

The routing table at slot 2 doubling as the suite-positioning section (JD#9) — adding a separate
`## Where … sits in the suite` table would be pure duplication for a skill whose entire job is routing
outward. The zero-marker posture itself is correct in principle (only its *legibility* needs the one-line
fix above) — do not retrofit per-claim brackets across this skill's craft claims. The `[core]` six / lazy
directories framing in "Volume layout" is deliberately non-exhaustive and should stay that way.
