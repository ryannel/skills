# Blind review — `skills/generative-media/anima`

Reviewed 2026-08-22 against `workbench/uniformity/STANDARD.md`, with `../sdxl/` and `../z-image/` as
comparators. No research material, workbench file, or external source was consulted: everything below
is derived from the four published files plus the suite around them.

Corpus measured: SKILL.md 5,416 w / 285 lines; `prompting-guide.md` 3,066; `setup-and-workflows.md`
3,069; `lora-training.md` 2,427; `characters.md` 2,020. Total **15,998 w**, SKILL.md share **33.9%**.
Markers: **26 `[flagged — re-verify]`, 9 `[contested]`, 4 `[pending release]`, 55 `[official]`,
~45 `[community — …]`**.

---

## Verdict

**SHIP WITH FIXES.** This is structurally the cleanest new skill in the suite — every mandatory §2
section is present, in order, with byte-exact headings, and the prose does the thing the house style
is for: it explains mechanisms rather than listing settings. But three defects block a clean ship.
First, **it contradicts itself on the one setting most readers will change** — whether Anima-Aesthetic
drops only `score_*` or all quality tags; SKILL.md and the prompting guide give opposite instructions
and the guide's own worked prompt sides against SKILL.md. Second, **it is not executable as written**:
no scheduler value is named anywhere in four files, and the Aesthetic, Turbo, Turbo-LoRA and Edit-LoRA
filenames are never given, in a skill whose two-bar section claims filenames as hard facts. Third, and
worst, **the licence section states a permissive commercial reading as `[official]` that the licence
text it quotes on the same screen does not support** — the one place in the skill where being wrong
costs the reader money. The marker density is *mostly* rigour, but roughly ten of the 26 `[flagged]`
markers are authoring notes about what the author could not establish, not claims a reader would want
re-checked, and they would inflate the freshness watchlist to ~35 items against a suite range of 6–16.
Fix the contradiction, name the scheduler and the filenames, downgrade the licence claim to
`[contested]` or narrow it to the quoted text, and prune the ten dead flags; then ship.

---

## Could I execute?

The task: a specific anime character, in a specific style, at a usable resolution.

**Steps that work.** Variant choice is easy and well argued (selector table + the Turbo/Aesthetic
`[contested]` note). Tag order is given as a grammar (`prompting-guide.md:41-43`). Character + series
pairing and the check-the-Animedex-first move are in `characters.md §2`. Resolution is unambiguous:
512²–1536², multiples of 16, 1024-area buckets named concretely (`setup-and-workflows.md:76`). Steps
and CFG are per-variant and consistent across all four files. The `@` prefix and the weight
recalibration are both stated three times over, which is correct for silent traps.

**Where I get stuck, in order of severity.**

1. **The scheduler is never named.** `SKILL.md:83` says "stock works"; `SKILL.md:103` says "stock
   scheduler"; `setup-and-workflows.md:69` says "Stock schedulers work." A ComfyUI KSampler forces a
   choice among `normal`, `karras`, `exponential`, `sgm_uniform`, `simple`, `ddim_uniform`, `beta`,
   and more. Every sibling names one — `sdxl/SKILL.md` gives `normal` / `sgm_uniform` /
   `SDTurboScheduler` per variant in the selector table itself. Anima names only `beta57`, which is a
   *non-stock* option requiring a custom node pack. So the one scheduler the skill names is the one
   I cannot use out of the box, and the one I need it does not name. **STANDARD §2.6 requires
   scheduler in each per-variant block.** This is the hard stop.

2. **Only one filename exists.** `anima-base-v1.0.safetensors` is given everywhere. Anima-Aesthetic —
   which the selector table recommends for exactly my job ("a good-looking image without curating
   artist tags") — has no filename, no repo path beyond the org, and no note on whether v1.0 and
   v1.0b are separate downloads. Same for Turbo, the Turbo LoRA, the Edit LoRA, and the LLLite control
   models (the last is routed to `§8`, which gives the *host* repo but not the file). This directly
   contradicts the two-bar section's own hard-facts roll-call, which lists "the filenames" as a
   must-be-exact category and then enumerates three.

3. **The `CLIPLoader` `type` argument is admitted missing** (`SKILL.md:76`, `setup-and-workflows.md:41`).
   This is handled *well* — flagged, with the failure mode explained and an instruction to read it off
   the stock template. But combined with (1) and (2), the honest summary is: **the skill's instruction
   for building the graph is "open the stock template."** Which is fine advice, and makes the file
   layout table redundant rather than load-bearing.

4. **`EmptyLatentImage` is stated flat, in a table cell, with no marker**
   (`setup-and-workflows.md:35, 52`) — in the same section that says the template JSON "was not read
   in this pass." Anima decodes through the Qwen-Image VAE, whose latent is not SDXL's. If that node
   is wrong, the graph either errors or produces noise. The asymmetry is the tell: the author flagged
   the node argument they knew they hadn't checked and stated flat the node they equally hadn't
   checked. See *My one question*.

5. **The style half of my task is undemonstrated.** Six worked prompts, and not one contains a real
   `@artist` tag except the model card's own (`@nnn yryr`). B and E use `@artist one`,
   `(@artist two:1.3)`, `@artist name`. For a skill whose headline asset is a 42k-entry artist
   vocabulary and whose #1 trap is a prefix character, a reader cannot check their syntax against a
   single verifiable example the author chose. Nor is there any worked prompt combining a **named
   existing character + series + a real artist tag + a pushed weight**, which is the exact job.

6. **The training trap has no home in SKILL.md's body.** `lora-training.md §1` correctly calls
   do-not-train-the-LLM-adapter "the load-bearing Anima-specific fact" and says it "degrades
   everything you train without producing an error" — a textbook silent failure. In SKILL.md it
   appears only as a subordinate clause at line 48 and a phrase in the reference table. There is **no
   failure-table row** for "Anima got globally worse after I loaded my LoRA" and no pre-flight item.
   STANDARD §5.4 and rubric check 20 put silent-failure traps in SKILL.md; this one is the model's
   most expensive and it is not there.

Everything else — negatives, seed rerolling, the hires trap, the detailer swap, the video handoff —
is present and executable.

---

## The conditioning-class exception

**It is argued, not merely asserted — but it argues the wrong half, and the argument has a hole where
its target should be.**

What the skill does well. `SKILL.md:44-54` is a genuine three-part evidence structure: the encoder is
an LLM (named file, named model, plus the adapter, with the vendor's own warning as corroboration);
the dialect is genuinely booru (verbatim caption description); weighting is officially supported. Then
a stated mechanism: *"prompt dialect follows the training captions, and the encoder only sets the
ceiling on what a dialect can express."* Then a falsifiable instruction: *"Check the caption corpus
before inferring a dialect from an encoder name."* That last sentence is the best thing in the
section — it converts a one-off exception into a reusable rule, which is what the suite is for.

**The hole.** The skill never states *why* the doctrine held that an LLM encoder precludes attention
weighting. It quotes the doctrine as a bare mapping (`SKILL.md:46`) and then contradicts it. But a
reader cannot tell whether the doctrine was (a) a mechanical claim — "weighting cannot be implemented
against an LLM encoder" — in which case Anima genuinely falsifies it, or (b) an empirical regularity —
"models with LLM encoders were trained on prose, so weighting has nothing to bite on" — in which case
Anima is not a falsification at all, just the first model in the suite whose captions were tags. The
skill's own mechanism sentence strongly implies (b). **If (b) is right, then "this falsifies the rule"
is the wrong frame and the heading over-claims**: nothing was falsified, the doctrine was always
conflating an encoder with a caption corpus, and Anima is the case that separates them. That is a
*better* finding than falsification, and the skill has all the pieces to say it.

**A second gap: the magnitude claim is pure assertion.** "Weights must be pushed far past SDXL" is the
skill's headline mechanic, repeated six times, and it is sourced entirely to one model-card sentence
plus one practitioner. No mechanism is offered for *why*. The skill has the ingredient sitting three
lines away: `SKILL.md:48` and `lora-training.md:24-26` establish that the encoder output passes through
a learned adapter with "an outsized influence." An adapter that re-projects and normalises the
conditioning tensor is the obvious candidate for damping a pre-adapter weight multiplier — and would
predict exactly the observed "needs a higher number than SDXL." The skill never connects them. As
written, the most-repeated instruction in the skill rests on "the card says so."

**Could I predict an uncovered case?** Partially.

- *Predictable:* another model with a small LLM encoder trained on prose captions → prose dialect,
  weighting probably weak. The mechanism handles this cleanly. ✅
- *Predictable:* no `BREAK`, no 77-token cliff, 40-tag prompts fine. Stated, and it follows. ✅
- **Not predictable — and it is a case a reader will hit within an hour:** does attention weighting
  work on the *prose* half? `(An anime girl with blonde hair:1.8)` inside a mixed tag+prose prompt.
  The skill's mechanism gives contradictory pulls — weighting is an encoder-level operation and
  should apply uniformly, but the "needs heavier weights" finding is a training-distribution fact that
  may not transfer to a prose span. §8 (natural-language mode) and §7 (weighting) never meet, and
  worked prompt E — the mixed one — carries no weight at all. **The skill's own flagship example of
  the two dialects composing does not exercise the mechanic that makes the two dialects interesting.**
- **Not predictable:** whether the `@` prefix is required in *prose* mode. §8's example writes
  `@big chungus` in the tag prefix, then prose. If I name an artist inside a sentence, does `@` still
  apply? The mechanism does not say and the skill does not either.

So: argued, and reusably so — but the argument targets a doctrine whose reasoning is never stated, and
it under-determines two adjacent cases that the skill's own structure invites.

---

## Does the prompting guide teach the dialect?

**Mostly yes on the rules, weakly on demonstration.** A reader arriving from SDXL is caught on the two
things that matter:

- The `@` trap is stated in SKILL.md (as one of three numbered silent failures), in the failure table,
  in the pre-flight checklist, in `prompting-guide.md §6` under the heading *"the single highest-value
  trap in the model"*, in the common-mistakes table, and in `lora-training.md §6`. Six placements. For
  a silent failure with a one-character fix, that is correct, not redundant.
- The weight recalibration gets a comparison table with SDXL's band beside Anima's
  (`prompting-guide.md:121-124`), a stepping method ("start at 1.5, step by 0.25, stop when composition
  rather than colour distorts"), and — the best touch in the file — a warning at line 126 that
  *community* prompts are themselves under-weighted because their authors carry SDXL habits.

Three real defects.

1. **The guide's own worked prompts under-weight.** `prompting-guide.md:236` (prompt B) uses
   `(@artist two:1.3)`. `SKILL.md:203` tells the reader to push to "1.5–2.0+". Line 126 explicitly
   calls `1.2` "low." So the skill's flagship original worked prompt sits at the bottom of, or below,
   its own recommended band — and the one artist weight it demonstrates is a value it elsewhere warns
   is a symptom of SDXL habit. This is not a nitpick: the worked prompts are where a reader calibrates.

2. **The band itself is inconsistent.** `prompting-guide.md:124` says `~1.3–2.0+`; `SKILL.md:184` says
   "Push to 1.5–2.0 and up"; `SKILL.md:203` says "1.5–2.0+"; the method paragraph says "start at 1.5."
   Pick 1.5 and use it everywhere.

3. **No real artist tags** (see *Could I execute?* item 5). The single most valuable thing this guide
   could hand a reader is five real `@` tags from the 42k index and what each does. It gives zero.

What the guide does that its siblings do not, and should be kept: §9 (ye-pop / DeviantArt dataset-tag
mode) is a genuinely obscure mechanic with a worked example and a clear "this is the route to
non-booru illustration" framing; §12 (scheduled prompts, and the fact that pipe wildcards do *not*
work without a custom pack) is exactly the kind of small operational fact that saves an afternoon;
§2's "tag dropout was trained in, so you don't need the 60-tag walls Illustrious users write" is a
migrant-specific correction no other file in the suite makes.

---

## Marker density

**Verdict: appropriate rigour in the `[contested]` and `[pending release]` tiers; genuine hedging in
about ten of the 26 `[flagged — re-verify]`.** The problem is not the count — STANDARD §7.14
explicitly refuses to normalise marker counts, and a three-month-old model earns a lot of them. The
problem is that **`[flagged — re-verify]` is being used for two different jobs**: "this is true today
and will change" (correct) and "I could not establish this" (an authoring note that leaked into the
published artefact). The second class tells a reader nothing to do and, per rubric check 40, would
force a `freshness.json` watchlist of ~35 items against a current suite range of **6–16** — more than
double `minimax-h3`, the largest. That is a concrete downstream cost, not an aesthetic complaint.

### Doing real work — keep

| Marker | Where | Why it earns its place |
|---|---|---|
| `[flagged — re-verify]` `CLIPLoader` `type` | `SKILL.md:76`, `setup:41` | An admitted hole in the build path, with the failure mode explained and an instruction to close it. Model of how to flag |
| `[pending release]` `anima-lllite-exp-change-2` | `SKILL.md:152`, `setup:132` | Two named unmerged PRs with branch names. Will resolve, and the reader must know it hasn't |
| `[contested]` Turbo vs Aesthetic default | `SKILL.md:19, :24, :268` | Vendor vs named practitioner, both quoted, changes the reader's default. Textbook |
| `[contested]` character-LoRA difficulty | `SKILL.md:269`, `lora-training:156` | Vendor "light touch" vs 100+ documented hours, with a reconciliation offered rather than a shrug |
| `[contested]` the 2.9B parameter count | `SKILL.md:266` | It is the parameter count. Naming the likely cause (confusion with the fork) is the right treatment |
| `[flagged — re-verify]` T5-XXL secondary encoder | `SKILL.md:267`, `setup:98` | Carries a *rejected* claim explicitly so the next reader doesn't re-discover it. Unusual and good |
| `[flagged — re-verify]` LLM-generated LLLite description | `SKILL.md:152`, `setup:134` | An active "do not repeat this as fact" warning. Rare and valuable |
| `[flagged — re-verify]` Civitai `nsfw: 0` filtering | `characters:91` | Honest measurement caveat on the author's own instrument |
| `[flagged — re-verify]` diffusers pipeline class | `SKILL.md:93`, `setup:97` | Third-party provenance for something a reader will paste into code |

### Drop, or convert to plain prose

| Marker | Where | Why |
|---|---|---|
| `[flagged — re-verify]` Comfy Org's role | `SKILL.md:9`, `:271` | Changes nothing a reader does. STANDARD §5.3: if the reader's next action is unchanged, it is padding — and a flag on padding is worse than the padding |
| `[flagged — re-verify]` "no material says DiT or UNet" | `SKILL.md:264` | A flag on a *taxonomy label* with no reader consequence — and undercut by the skill's own casual "DiT-era models" at `SKILL.md:62` and `setup:24` |
| `[flagged — re-verify]` download counts "will be stale quickly" | `setup:214` | Flags a self-evident property of all data. The sentence already says it |
| `[flagged — re-verify]` OneTrainer "no support found either way" | `lora-training:45` | A flag on a negative search result. Either drop the row or write "unknown — check OneTrainer's changelog" |
| `[flagged — re-verify]` optimiser "no settled consensus" | `lora-training:69` | Absence of consensus is not a re-verify item. Prose already says it |
| `[flagged — re-verify]` fork LoRA compatibility ×3 | `SKILL.md:250`, `:270`, `setup:109` | Three markers for one unknown about a fork the skill tells you not to use. Keep `setup:109`, drop the other two |
| `[flagged — re-verify]` "nobody has shipped it" | `characters:67` | Flags the non-existence of a research direction |
| `[flagged — re-verify]` on the 2.9B fork parenthetical | `characters:43` | Redundant with `SKILL.md:250` |
| `[contested]` style-LoRA rank | `lora-training:119` | Contested *in the wider community*, not an Anima dispute. It will never resolve, so it will sit in the watchlist forever. Route to `character-lora-training` instead |

### Firm up rather than drop

- `[flagged — re-verify]` **inference VRAM** (`SKILL.md:265`, `setup:84`). The flag is attached to "no
  official figure exists" — a stable fact that will not change. What actually needs re-checking is the
  **8 GB floor**, which is one report on one AMD card. Move the marker onto the number.
- The **licence carve-out** at `SKILL.md:242` carries `[official]` and should carry `[contested]` — see
  *Contradictions*. This is the inversion that matters most: the skill flags what Comfy Org's funding
  role was, and does not flag the sentence a reader will make commercial decisions on.

### One more, structural

**`[official]` is used 55 times.** STANDARD §6.2 says it is optional and "should be used *sparingly* —
specifically where an official number sits beside a community number and the contrast is the point."
At 55 uses it is doing the opposite: it is the default, which means it carries no information and it
visually competes with the flags that do. Cut to the ~8 places where an official figure sits beside a
community one.

---

## Contradictions

| Claim A | Claim B | Likely right |
|---|---|---|
| `SKILL.md:111` — "**Quality tags: omit `score_*` in both positive and negative.**" (Aesthetic) — i.e. keep `masterpiece, best quality` | `prompting-guide.md:67` — "**On Anima-Aesthetic, use neither ladder.**" `prompting-guide.md:185` table: Aesthetic quality tags = "**none, either side**" | **B.** The vendor quote inside the guide says both "you don't need quality tags in the positive at all" and "not using `score_*` in both"; worked prompt D (`prompting-guide.md:245`, the only Aesthetic example) drops **all** quality tags. SKILL.md and the checklist (`:204`) are the odd ones out. This is the skill's most consequential internal contradiction — it changes what a reader types on the variant the selector recommends for the default job |
| `SKILL.md:220` — "50+ LoRAs and 40+ checkpoints on Civitai within months" (reads as an ecosystem total) | `setup-and-workflows.md:200` — "Civitai `baseModels=Anima`, most-downloaded, **first 100**: 53 LoRAs, 41 checkpoints, 5 workflows, 1 VAE" | **B is the data; A misreads it.** "53 of a 100-item sample" is not "50+ in total" — the true total is unknown and almost certainly far larger. `lora-training.md:81` repeats the error ("grew to 40+ community finetunes"). A classic summarise-up failure: the reference's sampling frame was dropped, converting a composition statistic into a (wrong, and understated) census |
| `SKILL.md:9` — "a **latent-diffusion backbone**"; `SKILL.md:62` and `setup:24` — "Like the other **DiT-era** models…" | `SKILL.md:264` — "no CircleStone material says 'DiT' or 'UNet' about Anima itself, and the one circulating description that does is LLM-generated `[flagged — re-verify]`" | **The flag is right and the body should match it, or vice versa.** As written the skill hedges the architecture label in its two-bar section while using "DiT-era" twice as settled framing in the body. Pick one: either "treat it as a flow-matching DiT by inheritance from Cosmos-Predict2" (defensible from the derivation the skill already asserts) or stop saying "DiT-era" |
| `SKILL.md:239` — licence quote: commercial = "(a) revenue-generating activity, (b) **in direct interactions with or that has impact on third-party end users**, or (c) to train, fine tune, or distill other models for commercial use" | `SKILL.md:244` — "**What you may not do.** Host the base weights behind a paid API or build a paid product on them" | **A is the text; B is a narrowing.** Clause (b) covers *any* third-party end-user impact including non-revenue, which the "what you may not do" paragraph silently drops. And `SKILL.md:242`'s reading of the individual carve-out — "*Persons operating in an individual capacity may sell Derivatives*" → "That covers selling generated images, paid commissions, and selling LoRAs" `[official]` — treats *images* as "Derivatives," a defined term the skill elsewhere uses only for **Derivative Models** (`SKILL.md:240`). It also sits in unremarked tension with clause (c), which bars fine-tuning for commercial use — so "selling LoRAs you made" is exactly the case (c) appears to prohibit. **This is the single most dangerous passage in the skill**, and it is the one carrying `[official]` |
| `SKILL.md:89` — "`u/Dependent_Quit_3730` reports it is the only model that loads … **at 8–15 min per 1024²/30-step image** via ROCm `[community — u/Bokayoteamo; single report]`" | `setup:86` — two separate reports, correctly split: Dependent_Quit_3730 for "only model that loads," Bokayoteamo for the 8–15 min figure | **B.** SKILL.md fuses two people into one sentence and then attributes it to the second. Cosmetic, but it is precisely the summarise-up attribution loss STANDARD §6.2 was written to catch |
| `prompting-guide.md:124` — usable weight band "**~1.3–2.0+**" | `SKILL.md:184` "Push to **1.5**–2.0 and up"; `SKILL.md:203` "**1.5**–2.0+"; `prompting-guide.md:128` "start at **1.5**" | **1.5.** Three-to-one, and the guide's own method paragraph agrees. Fix the table |
| `SKILL.md:258` two-bar roll-call — "**the filenames** (`anima-base…`, `qwen_3_06b_base…`, `qwen_image_vae…`)" held to the official bar | Aesthetic, Turbo, the Turbo LoRA, the Edit LoRA and the LLLite control models have **no filenames anywhere in the skill** | **The roll-call over-claims.** Either supply the missing filenames or say the roll-call covers the base path only |
| `setup:35, :52` — `EmptyLatentImage`, stated flat with no marker | `setup:41` — "the template JSON **was not read** when this skill was written" | **Unresolvable from inside the skill.** See *My one question* |

---

## Fit with the suite

**It reads as a sibling.** Section sequence matches §2 exactly, including the resolved
one-rule-before-setup ordering that `z-image` gets wrong. All ten verbatim headings are byte-exact.
Two extra slot-8 sections (*Seeds are not equal*, *Image conditioning and editing*) are legitimate and
carry real content. The signature-technique heading (*The neutral base and the artist-tag lever*)
names the actual trait rather than a template, per §2.7 and the `krea-2` precedent. All four §4.1
reference slots exist under canonical names. All markers are backticked, em-dashed, and drawn from the
closed six-token set — no italic-parenthetical legacy, no malformed nesting. Every sibling mention is a
relative link; nothing reaches above `skills/generative-media/`. The two-bar section carries all five
§6.3 elements and the date line opens `**Facts dated 2026-08-22**`. On apparatus this is the best-formed
skill in the suite.

**Positioning is accurate, and the licence is not softened — at the table level.** `SKILL.md:225`
gives the licence its own suite-table row, bolds "**Non-commercial weights, and this is a hard
asymmetry**", and routes commercial anime work away from Anima in the imperative: "**If you are picking
an anime model for commercial work, pick an SDXL finetune.**" The one-paragraph Anima-vs-SDXL-vs-Z-Image
summary at `:229` leads with "Shipping commercially?" That is exactly right, and it matches how
`sdxl/SKILL.md:49` and `:215` already frame the reciprocal — "**The deciding axis is the licence, not
the output**." The two skills agree, which is the transfer property STANDARD §1 is for.

**But the softening happens one level down.** The suite table row's own gloss — "Individuals may sell
outputs and derivatives" — is the contested reading from `Licence & limitations`, and it is repeated in
the frontmatter `description`, which is the first thing an agent matches on. So the *table* is decisive
and the *substance under it* is a permissive interpretation presented as vendor fact. Fix the licence
section and the table row inherits the fix.

**Bidirectionality is half-done.** Reciprocal rows exist in `sdxl` (two places, well written),
`z-image`, `character-lora-training` and `image-production-workflows`. Missing from `flux-2`,
`ideogram-4`, `krea-2`, `comfyui-on-runpod`, and — most substantively — **`wan-2-2` and `minimax-h3`**.
Anima's own table (`:227`) and `characters.md §8` claim Anima is "the **default anime character-still
generator**" for the suite's video models, named by three practitioners. Neither video skill's
"Locking the still first" / "Locking a still before animating" row mentions Anima; both list
`z-image` / `flux-2` / `krea-2` / `sdxl` only. The skill's strongest positional claim has no return
link.

**Registration is incomplete.** `.claude-plugin/marketplace.json` now lists
`./skills/generative-media/anima` (updated during this review). The **README table does not include
it**, and **`freshness.json` has no `anima` entry** — no tier, no `why_tier`, no watchlist. Per
CLAUDE.md, marketplace + README registration is what publishes a skill, and `/skill-freshness register`
is what keeps it from rotting. Both rubric E checks are open.

**Depth is at the ceiling.** 15,998 words against a 16,000 cap; SKILL.md 5,416 against a 5,500 cap.
Inside tolerance on both, but with two words and 84 words of headroom respectively. Any fix that adds
prose needs an offsetting cut — the ten dead flags and the 47 surplus `[official]` markers are the
obvious donors.

---

## Rubric

Graded against STANDARD.md §8. `PASS` / `FINDING [severity]` / `N/A`.

**A. Shape**

1. All MANDATORY §2 sections present at right level — **PASS**.
2. Section order per §2 — **PASS** (one-rule before setup, correctly).
3. Verbatim headings byte-exact — **PASS** (all ten checked).
4. Selector table with "Use when…", unreleased variants marked — **PASS** (preview3 and the community forks both marked).
5. Failure table ≥8 rows, every cause states a mechanism — **PASS**, 11 rows, causes are genuine mechanisms ("each pass re-noises an already-denoised latent, and the 2B backbone compounds…"). One gap: **FINDING [P2]** no row for the LLM-adapter training failure, which `lora-training.md:144` describes as presenting as "Anima got worse."
6. Per-variant `###` blocks covering steps/CFG/sampler/**scheduler**/resolution/negatives/seed — **FINDING [P1]** scheduler value absent from all three blocks and from all four files; sampler absent from the Aesthetic block; resolution absent from the Turbo block.
7. Pre-flight checklist, numbered, 8–12 items — **PASS** (12).

**B. References**

8. Four §4.1 core slots under canonical names — **PASS**.
9. Renames needed — **N/A**, all canonical.
10. `## Reference files` one row per file, says *when* to read — **PASS**, and the rows are unusually good.
11. Train/use boundary with cross-pointer both ways — **PASS** (`lora-training.md:3` ↔ `setup:104`).
12. `## Contents` TOC on every reference ≥2,000 w — **PASS** (all four).
13. Numbered `## N.` headings where `§`-deep-linked — **PASS**.

**C. Depth**

14. Corpus 10,000–16,000 — **PASS** at 15,998, i.e. **FINDING [P3]** for zero headroom.
15. SKILL.md 25–40% and 2,800–5,500 w — **PASS** at 33.9% / 5,416, same headroom caveat.
16. SKILL.md under 500 lines — **PASS** (285).
17. Every reference 700–3,500 w — **PASS**.
18. Any section that does not change what the reader does — **FINDING [P3]** `SKILL.md:9` Comfy Org funding-vs-co-training clause, and `SKILL.md:264` the DiT/UNet taxonomy bullet.
19. Table/derivation duplicated in full between SKILL.md and reference — **PASS**, mostly; the per-variant steps/CFG figures appear in both `SKILL.md:99-118` and `setup:47-52`, but SKILL.md carries the rule and the reference the table, as §5.3 prescribes.
20. Every silent-failure trap in SKILL.md — **FINDING [P1]** the `llm_adapter_lr 0` rule is a silent trap by the skill's own description and lives only in a reference and a subordinate clause.
21. Three pillars covered or routed — **PASS**, all three deeply.

**D. Apparatus**

22. `description` 180–320 w, folded scalar, five §6.1 elements — **PASS** (244 w, "even obliquely:" verbatim, closing sweep present). **FINDING [P2]** it front-loads the contested commercial carve-out in bold.
23. Two-bar section at `##`, byte-identical, second-to-last — **PASS**.
24. Five §6.3 elements present — **PASS**, and the craft roll-call names nine community authors, which is the strongest example in the suite.
25. Date line as final paragraph, `**Facts dated YYYY-MM-DD**`, distinct from release date — **PASS** (release date lives in the intro, correctly).
26. Every flagged/contested/pending claim greppable — **PASS**.
27. Italic-parenthetical markers remaining — **PASS**, none.
28. Malformed markers — **PASS**, none.
29. Orphan craft numbers / bare epistemic hedges — **FINDING [P2]**: `characters.md:51` and `lora-training.md:149` "drop strength ~0.1–0.3" (no owner, and ambiguous between *by* and *to*); `setup:172` "0.25–0.35" re-sample band unattributed; `SKILL.md:164` detailer "~0.4 denoise" unattributed.
30. Summarise-up hop preserves attribution — **FINDING [P2]**: the `SKILL.md:220` "50+/40+" census error and the `SKILL.md:89` two-author fusion.
31. Marker syntax canonical — **FINDING [P3]**: `[community — citronlegacy; reproducible]` uses a qualifier outside the closed set; `[community — ThetaCursed; animastyles.thetacursed.com]` (×2) puts a venue after the semicolon, which is comma territory.
32. ≥1 flagged/contested in SKILL.md — **PASS** (emphatically).
33. Sibling mentions as relative links — **PASS**.
34. Links above `skills/generative-media/` — **PASS**, none.
35. All eight image axes in the suite table — **PASS**.
36. Reciprocal links — **FINDING [P2]**: missing in `wan-2-2`, `minimax-h3`, `krea-2`, `flux-2`, `ideogram-4`, `comfyui-on-runpod`.
37. Unpublished models bolded with status word — **PASS**.
38. Tables for structure, prose for mechanism — **PASS**; *Seeds are not equal* and the LLLite low-weight rule are correctly prose.

**E. Registration**

39. In `marketplace.json` **and** README — **FINDING [P1]**: marketplace yes, **README table missing**.
40. In `freshness.json` with tier, `why_tier`, watchlist — **FINDING [P1]**: **absent entirely**. On registration, the watchlist should carry ~14 items (the keep-list above), not all 35 markers.
41. Watchlist references surviving line numbers — **N/A** until 40 is done.

**Summary: 2 P1 content findings (scheduler, silent trap placement), 2 P1 registration findings, 1 P1-severity contradiction not covered by the rubric (the Aesthetic quality-tag instruction), 7 P2, 5 P3.**

---

## My one question

**Did anyone actually open the stock ComfyUI Anima template — and if not, which node claims are
inferred rather than read?**

`setup-and-workflows.md:41` says plainly that "the template JSON was not read when this skill was
written," and flags the `CLIPLoader` `type` argument accordingly. But the same section then publishes
three unflagged claims that could only come from a template read or an assumption:

- `EmptyLatentImage` as the latent node (`setup:35`, `:52`) — for a model whose VAE is the Qwen-Image
  VAE, not SDXL's. If the latent channel count differs, this node is wrong.
- The graph shape `UNETLoader → LoraLoader → KSampler` with **no sampling/shift node** — where the
  suite's other DiT-family skills discuss shift explicitly.
- "Stock scheduler" as if a default existed, when the KSampler forces an explicit choice.

Two minutes in the template browser resolves all three plus the flagged `type` value, and would let
the skill delete its own biggest caveat. Everything else in this review is a fix; this is a question,
because from inside the skill there is no way to tell whether the file layout table is *reported* or
*reconstructed* — and the two-bar section stakes the skill's hard-facts bar on it being the former.

Second in line, and the one that costs money rather than time: **on what basis does `SKILL.md:242`
read "may sell Derivatives" as covering generated images and commissions, and how does that survive
clause (c)'s bar on fine-tuning for commercial use?** If the answer is "it is the natural reading," the
marker should be `[contested]`, not `[official]`.
