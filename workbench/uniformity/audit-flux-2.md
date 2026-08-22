# Uniformity audit — `skills/generative-media/flux-2/`

Graded against `workbench/uniformity/STANDARD.md` §8. SKILL.md is 320 lines / 4,191 words
(was 3,922 before the 2026-08-22 FLUX 3 addition). References total 9,953 words. Corpus 14,144
words, SKILL.md share 29.6% — inside the 10,000–16,000 / 25–40% / 2,800–5,500 targets. No depth
findings.

---

## Blocking

**[P1] SKILL.md § position — the FLUX 3 section breaks "two-bar immediately before Reference files"**
`§6.3` requires the two-bar section to sit second-to-last, immediately before `## Reference files`.
The 2026-08-22 edit inserted `## FLUX 3 — announced, not available…` (line 297) *after* the two-bar
section (line 283) and *before* `## Reference files` (line 311), making two-bar third-to-last.
→ **Fix:** move the entire `## FLUX 3` block (lines 297–309) to immediately after
`## Where FLUX.2 sits in the suite` (which ends line 262) and before `## Licence & limitations`
(line 265). New order: …Where FLUX.2 sits in the suite → FLUX 3 → Licence & limitations → two-bar →
Reference files. Do not shorten the section in the move — see "Do not touch" below.

**[P1] check 26/32 — the skill's own contested point is never tagged, so SKILL.md has zero
`[flagged]`/`[contested]` markers**
Two-bar section, line 291: *"**One genuinely-unresolved fact:** the multi-reference image count —
BFL marketing says 10, the prompting guide says 8. Discrepancy unresolved across official
sources…"* — states a contested fact in prose with no `[contested]` token anywhere in the sentence.
Grepping `SKILL.md` for `\[contested\]` or `\[flagged` returns nothing; only `[pending release]`
(line 303) and `[official — bfl.ai/blog/flux-3]` (line 299) exist. This fails check 32's floor
(`active`-tier skill must carry ≥1 `[flagged]`/`[contested]` marker or an explicit "nothing flagged"
line — flux-2 has neither).
→ **Fix:** append the token to the existing sentence: *"…Discrepancy unresolved across official
sources; treat ~8 as the safe working number and test if you need more.
`` `[contested]` ``."* (place it before the final period per §6.2 placement rule).

**[P1] check 27 — 14 italic-parenthetical markers not converted to bracket form**
The STANDARD's census (§6.2 table) lists flux-2 at "0 italic-paren markers" and only flags
`sdxl`/`z-image` for this repair. That count is wrong for this skill — the census undercounted.
Actual instances, all needing conversion to `` `[tier — source; qualifier]` ``:

| Location | Current text | Convert to |
|---|---|---|
| `SKILL.md:211` | `*(named community workflows)*` | `` `[community]` `` (sources are named individually in the two bullets below — this token can stay generic) |
| `references/lora-training.md:11` | `*(community)*` | `` `[community]` `` |
| `references/lora-training.md:47` | `*(Official-platform recipe vs named-community ablation — a genuine divergence, flagged.)*` | `` `[contested]` `` (this is the strongest miss — the sentence literally says "flagged" in prose and never emits the token) |
| `references/lora-training.md:74` | `*(named community ablation — Calvin Herbst, Medium)*` | `` `[community — Calvin Herbst, Medium]` `` |
| `references/lora-training.md:90` | `*(Named community evidence on both sides — presented as contested, not settled.)*` | `` `[contested]` `` (same pattern — "contested" in prose, no token) |
| `references/lora-training.md:96` | `*(kohya #1497 — contested)*` | `` `[contested — kohya #1497]` `` |
| `references/characters.md:13` | `*(official template + community)*` | `` `[community]` `` (mixed claim — the multi-ref mechanics are official, the "prefer [dev] over Kontext / lock seeds / drop conflicting refs" tip is craft) |
| `references/characters.md:14` | `*(official repo; t2i only as of v0.6.x)*` | `` `[official — iFayens/ComfyUI-PuLID-Flux2]` `` |
| `references/characters.md:18` | `*(community consensus — MyAIForce's head-to-heads are the citable comparisons)*` | `` `[community — MyAIForce]` `` |
| `references/characters.md:26` | `*(community, strong)*` | `` `[community — Mickmumpitz-class workflows; strong]` `` |
| `references/characters.md:31` | `*(Community, strong — WeirdWonderfulAI's Qwen-Edit dataset writeup is the canonical version of this pipeline.)*` | `` `[community — WeirdWonderfulAI; strong]` `` |
| `references/characters.md:42` | `*(community, strong — established cross-model technique)*` | `` `[community — established cross-model technique; strong]` `` |
| `references/characters.md:49` | `*(community — Khanykov01's guide, written for SDXL but the capacity logic is architecture-general)*` | `` `[community — Khanykov01]` `` (move the SDXL caveat into prose) |
| `references/characters.md:50` | `*(Core PR is official; the craft layer is community and still forming.)*` — note the preceding sentence also says "is still contested — expect retries" with no token | `` `[official]` `` for the PR clause + append `` `[contested]` `` right after "still contested" in the prior sentence |

→ **Fix:** mechanical pass per §6.2's conversion table, same as the sdxl/z-image repair. Flag this
finding back to whoever owns `STANDARD.md` §6.2 — the census table needs a corrected flux-2 row (14,
not 0).

**[P1] check 33 — bare code-span sibling mentions instead of markdown links**
The entire "Where FLUX.2 sits in the suite" table (the skill's primary cross-navigation surface) uses
bare code spans, not links:

- `SKILL.md:254` — `` `sdxl` `` (×2 in cell) → `` [`sdxl`](../sdxl/) ``
- `SKILL.md:255` — `` `sdxl` `` → `` [`sdxl`](../sdxl/) ``
- `SKILL.md:256` — `` `ideogram-4` `` → `` [`ideogram-4`](../ideogram-4/) ``
- `SKILL.md:257` — `` `sdxl` `` → `` [`sdxl`](../sdxl/) ``
- `SKILL.md:258` — `` `sdxl` ``, `` `krea-2` `` → `` [`sdxl`](../sdxl/) ``, `` [`krea-2`](../krea-2/) ``
- `SKILL.md:259` — `` `krea-2` `` → `` [`krea-2`](../krea-2/) ``
- `SKILL.md:260` — `` `image-production-workflows` `` → `` [`image-production-workflows`](../image-production-workflows/) ``
- `SKILL.md:261` — `` `wan-2-2` `` → `` [`wan-2-2`](../wan-2-2/) ``
- `SKILL.md:215` — `` **`image-production-workflows`** `` (prose, "Production pipelines" section) → `` [`image-production-workflows`](../image-production-workflows/) ``
- `references/characters.md:38` — "the z-image skill's prompting guide §3.3–3.5" is not even code-spanned → `` [`z-image`](../../z-image/references/prompting-guide.md) `` (§3.3–3.5)
- `references/lora-training.md:68` — `` `sdxl/references/lora-training.md` §8 `` bare → `` [`sdxl`](../../sdxl/references/lora-training.md) `` §8

The only compliant sibling links in the skill are `[`minimax-h3`](../minimax-h3/)` (SKILL.md:307,
new FLUX 3 section) and the three `character-lora-training` links in `lora-training.md`. Every
older sibling mention is bare. → **Fix:** mechanical find/replace per the list above; all targets
stay inside `skills/generative-media/`, no link crosses that boundary (check 34 passes).

---

## Standard

**[P2] check 6 — per-variant settings blocks don't keep distilled/undistilled apart**
`## Per-variant settings` (line 161) has one `###` block per variant ([dev], [klein] 4B, [klein] 9B),
but each block conflates distilled and base numbers in the same bullet list (e.g. `### [klein] 4B` —
"Steps: 4 (distilled) or 20 (base)", "Guidance: CFGGuider 1 (distilled) or 5 (base)"). §2 row 6 wants
distilled and undistilled kept apart.
→ **Fix:** split `### [klein] 4B — distilled (Apache 2.0)` into two blocks, `### [klein] 4B —
distilled` and `### [klein] 4B Base — undistilled`, each with its own steps/guidance/negatives bullets
(the base block additionally notes "use for LoRA training"). Same split for the 9B block.

**[P2] check 29 — orphan craft numbers in the production ladder (STANDARD already names this case)**
`SKILL.md` § Production pipelines & mixing models: "img2img on itself at denoise **~0.3–0.45**"
(line 206), FaceDetailer "denoise **~0.4**" (line 207), tiled-upscale "low denoise (**~0.2–0.3**)"
(line 208) — three actionable numbers, no named source, no marker, and no reference file covers
this content to attribute up from (there is no production-pipelines reference in flux-2; it's meant
to route to `image-production-workflows`).
→ **Fix:** either name a source inline (if one exists — e.g. "the TTP Toolset author's recommended
denoise band") or mark each: `` `[community — re-verify]` `` appended to the sentence containing all
three numbers, since they're one claim-unit ("Refine pass… detail without re-composition
`` `[community]` ``.").

**[P2] check 29 — bare epistemic hedge**
`references/setup-and-workflows.md:262` — *"**Community practice** runs 3–4 LoRAs max and lowers
each strength…"* names no author, just "community practice."
→ **Fix:** either name a source or convert to `` `[community]` `` immediately after "3–4 LoRAs max".

**[P2] check 9 — filename rename (already flagged in STANDARD §4.3, low priority there but real)**
`references/api-and-bfl.md` → `references/api-and-hosted.md`. Internal references to update: the
`## Reference files` table row in `SKILL.md` (line 316) and the file's own title line 1.
→ **Fix:** `git mv references/api-and-bfl.md references/api-and-hosted.md`, then update the one
`SKILL.md` row. No other file links to it by name.

**[P2] check 41 — freshness watchlist line number has drifted**
`freshness.json` watchlist id `captionless-debate` cites `references/lora-training.md ~L66`; the
actual captionless-training bullet is at line 90 (line 66 is now the unrelated "Klein 9B has
documented collapse patterns" bullet, which correctly carries its own `` `[community — re-verify]` ``
marker). A 24-line drift is outside the "~" tolerance the rest of the watchlist observes.
→ **Fix:** update the watchlist entry's `where` field to `references/lora-training.md ~L90`.

---

## Cosmetic

**[P3] check 31 — zero backticked markers in the whole skill**
Every bracket-form marker in this skill (`SKILL.md:299,303`; `lora-training.md:60,66`;
`characters.md:70`) is bare, not backticked. §6.2's RESOLVED rule makes backtick canonical suite-wide.
→ **Fix:** wrap each in backticks: `[official — bfl.ai/blog/flux-3]` → `` `[official — bfl.ai/blog/flux-3]` ``,
`[pending release]` → `` `[pending release]` ``, `[official — BFL Klein training docs]` →
`` `[official — BFL Klein training docs]` ``, `[community — re-verify]` →
`` `[community — re-verify]` ``, `[official]` → `` `[official]` ``. Do this pass together with the
italic-parenthetical conversion above so every marker in the skill ends up in one syntax at once.

---

## Unattributed craft (beyond the rubric)

Actionable claims with no named source and no marker, not already listed above:

- `references/prompting-guide.md` §5 (lines 141–196): the camera-body, lens, and film-stock
  vocabulary tables are entirely unattributed. The file's opening lede (line 3) names tiers
  generically ("fal.ai prompting guide and community consensus") but no individual row, cell, or the
  section as a whole carries a marker. This is a large block of specific, typeable craft (camera
  models, apertures, film stocks) with zero named authors anywhere near it — a stronger candidate for
  a **heading-scoped marker** (§6.2's "legal on a `###` whose entire subsection rests on one source")
  than per-cell marking would be disruptive. Suggested fix: add one line under the `### Camera bodies`
  / `### Lenses` / `### Film stocks` sub-headings: `` `[community — fal.ai prompting guide and
  convergent ComfyUI-author practice]` ``.
- `SKILL.md:197` — "The over-AI'd look is worst on [klein] 4B distilled; [dev] is more measured." No
  source. Lower priority than the items above (it's a comparative observation, not a number a reader
  types), but still meets (a)+(b)+(c).

---

## Staleness (2026-08-22 reader)

`references/controlnet-and-identity.md` dates four separate claims **"as of June 2026"** (lines 19,
90, 143 heading, 162) — the "no FLUX.2 ControlNet port from InstantX/Shakker-Labs/xinsir," "iFayens
is the only PuLID," and "no FLUX.2 IP-Adapter" claims. `freshness.json`'s `last_checked` is
2026-08-22 (today) and these exact claims are on the watchlist (`flux1-cn-teams`, `no-ip-adapter`,
`pulid-flux2`), so a check plausibly *did* run — but the prose dates were not bumped even if the
facts were reconfirmed. A reader in August, two months past the stated date, in a skill whose own
`why_tier` says the ecosystem "moves weekly," has no way to tell whether this is current or an
8-week-stale check. Recommend either updating the date string to reflect the actual last-verified
date or dropping the specific month and leaning on the two-bar section's volatility note instead.

Separately: `references/setup-and-workflows.md:266` ("The published pool was still small and growing
close to release") and `:214`/`:45` ("at research time" / "pending close to release") read as
launch-week hedges for a model that's now 3+ months (klein) to 9 months ([dev]) old. These should be
revisited on the next freshness pass even though they're not making a specific factual claim that
could 404.

---

## Do not touch

1. **The FLUX 3 section's content and hedging is exactly right — only its position is wrong.** It
   correctly uses `[pending release]`, cites BFL's numbers as "their own, preliminary," and states
   plainly "what this changes for you today: nothing, except planning." A repair agent fixing the
   position finding above must move the block verbatim, not trim it — the honest "this will need its
   own skill in the video half of the suite" framing is a model of how to handle an
   announced-not-shipped successor and should not be compressed into a routing footnote.
2. **`## Realism — the FLUX.2 approach`** is the STANDARD's own cited example of a correctly-named
   signature-technique heading (§2 row 7). Leave it exactly as-is; do not "fix" it toward a generic
   template heading.
3. **`references/lora-training.md`'s "official reference config" section** (BFL's own rank
   64/alpha 128/batch 4/LR 1e-5 recipe) is flagged in the file itself as "the one model in the suite
   with a vendor-stated LoRA recipe rather than a purely community-derived one." That's a real,
   verified differentiator versus the rest of the suite (which infers hyperparameters from ablations)
   — do not fold it into the Hyperparameters table below it or otherwise demote it; it is correctly
   given its own section precisely because it's a different tier of evidence.
4. **The `bryanmcguire` vs `VideoX-Fun` ControlNet path conflict note**
   (`controlnet-and-identity.md:56`, "try `models/model_patches/` first; if the loader fails, try
   `models/controlnet/`") is exactly the kind of hard-won, silently-conflicting-docs detail the suite
   is supposed to preserve. A brevity-motivated repair pass could easily cut this as a two-path edge
   case; it should stay.
5. **All ten mandatory `SKILL.md` headings are already byte-identical to the canonical forms**
   (including the two-bar heading and `## Where FLUX.2 sits in the suite`), and the section order is
   otherwise fully correct (one rule before setup, Licence & limitations using the ampersand form).
   Don't let a bulk heading-normalization pass touch this file's headings — there's nothing to fix
   there, and it's a useful reference example for the other nine audits.
