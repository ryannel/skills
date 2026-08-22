# Cross-check — the image half of the suite

Scope: `flux-2`, `ideogram-4`, `z-image`, `sdxl`, `krea-2`, `anima` — SKILL.md and every reference.
Method: built a table of every assertion one skill makes about a *different* model, then checked each
against that model's own skill. Dated 2026-08-22. Read-only pass; nothing was edited.

Ranked throughout by whether a reader would be **misled** (wrong decision, wrong legal read, wrong
craft) versus merely **inconvenienced** (a dead link, a missing row).

---

## Contradictions

### Misleading

| Claim A | Claim B | Which is right | Recommended fix |
|---|---|---|---|
| `ideogram-4/SKILL.md:240` — "**The only model here whose weights restrict *purpose*** — non-commercial wherever you run them." | `flux-2/SKILL.md:306` (FLUX Non-Commercial License v2.0 on [dev]/9B) and `:309` — "The restriction is about *purpose*, not *place* — running [dev] weights on RunPod does not grant commercial rights." Also `anima/SKILL.md:228` — Model usable "solely for your Non-Commercial Purposes". | **B.** Ideogram 4 is one of *three* purpose-restricted weight licences in the image half. Ideogram's own reach-for cell in the same row even names flux-2 as having "the Apache-licensed [klein]", which concedes the rest of the family is not. | Replace the cell's opening with: "**Purpose-restricted weights** — non-commercial wherever you run them, like [`flux-2`](../flux-2/)'s [dev] and 9B and [`anima`](../anima/)'s Model. What is unusual here is that there is no commercially-clean *open* variant to fall back to — the fallback is the hosted API." Keep the existing reach-for sentence. |
| `flux-2/SKILL.md:278` — "**[klein] 4B is the suite's only Apache-2.0 path** at this quality level". Reach-for names sdxl and krea-2 only. | `z-image/SKILL.md:9`, `:15–18`, `:203`, `:211` — Z-Image and Z-Image-Turbo are **Apache-2.0, weights and outputs alike**, "the least legally encumbered model in the suite … Nothing is freer." | **B.** Z-Image is Apache-2.0 open weights at 6B; the "at this quality level" hedge is doing work no table-scanning reader will see. A reader shopping for a commercially-free local model is steered away from the freest one. | Cell → "**[klein] 4B is the family's Apache-2.0 path**". Reach-for → "[`z-image`](../z-image/) — Apache-2.0 across the family, weights and outputs; [`sdxl`](../sdxl/) (OpenRAIL++-M) for the mature alternative; [`krea-2`](../krea-2/) is free commercial only under $1M revenue". |
| `sdxl/SKILL.md:214` — photoreal faces & skin row, reach-for: "[`krea-2`](../krea-2/) if you want the look without checkpoint-hopping **and gear-stacking**". | `krea-2/SKILL.md:145` — photoreal on Krea 2 "need[s] explicit photographic framing — camera body, lens, film stock, **the same stack that works on every LLM-encoder model**", plus a VAE swap (`:146`) and detailer passes (`:147`). `krea-2/SKILL.md:224` puts photoreal faces at "Workable with the two-tax fixes; expressions are the weak point" and routes onward to z-image. | **B.** Krea 2 requires the same gear stack *plus* two extra taxes, and self-declares faces as a weak axis. sdxl sends a photoreal-faces reader to a model that immediately sends them somewhere else. | Reach-for → "[`z-image`](../z-image/) — the suite's photoreal-faces and skin owner, and the standard face-pass finisher. [`krea-2`](../krea-2/) for stylistic breadth without checkpoint-hopping, but budget its two taxes (soft default, muted expressions) — the gear stack does not go away there." |
| `flux-2/references/prompting-guide.md:338` — "`(text:1.5)` parenthetical weight syntax \| AUTOMATIC1111 syntax; **meaningless for LLM encoders** \| No parenthetical weighting". | `anima/SKILL.md:31` — the card's own worked example is `(chibi:2)` and a term *"needs a weight higher than typically used for SDXL"* `[official]`; `anima/SKILL.md:53` gives the mechanism (a T5 token stream the LLM adapter multiplies into its output). Anima's encoder is Qwen3-0.6B, an LLM. | **B** on the general claim; A is right about FLUX.2 specifically. This is the doctrine statement anima falsifies, stated at its most universal — an Anima reader who trusts it drops the model's single highest-leverage lever. | Cause column → "AUTOMATIC1111 syntax; FLUX.2's Mistral/Qwen3 conditioning has no per-token weight channel". Add a trailing clause: "(Not a rule about LLM encoders as a class — [`anima`](../../anima/) has one and ships documented attention weighting.)" `flux-2/references/prompting-guide.md:65` is already correctly scoped ("meaningless *here*") and needs nothing. |
| `anima/SKILL.md:51` — "**Every earlier LLM-encoder model here was captioned in prose**, so the two moved together and the doctrine never had to separate them." | `ideogram-4/SKILL.md:12` — "it was trained **exclusively on structured JSON captions**"; `:36`, `:266`. Encoder is Qwen3-VL-8B-Instruct (`:10`). | **B.** Ideogram 4 is an LLM/VLM-encoder model in this suite whose caption corpus is *not* prose — the strongest existing precedent for anima's own thesis, and anima asserts it does not exist. The claim as written is false and it weakens the argument it is making. | Rewrite to: "The one earlier suite model that separates them, [`ideogram-4`](../ideogram-4/), is already treated as a special case rather than a counter-example: a Qwen3-VL encoder captioned exclusively in JSON, which is why its prompt is a schema and not a sentence. Anima makes the same separation impossible to shelve." Also add `ideogram-4` to the encoder-class list at `anima/SKILL.md:45`. |
| `sdxl/references/lora-training.md:36` — Anima "**Weights are non-commercial** … **a LoRA you train on it inherits that**, though the images it makes do not." | `anima/SKILL.md:233` — §2(c): *"Persons operating in an individual capacity may sell Derivatives owned or created by them"*, and "Derivative" means modified weights, LoRAs and textual inversions (§1(a)) — bounded by *"solely to the model weights, and not to any larger product"*. | **B.** A LoRA is exactly the artefact §2(c) carves out. "Inherits that" is a flat non-commercial read that tells a solo LoRA author they may not sell a LoRA, when the licence says they may (weights only). This is the last surviving over-simplification from the central correction — same class of error, one layer down. | → "**Weights are non-commercial**, unlike everything else in this table. Your LoRA is a Derivative and inherits that — with §2(c)'s carve-out: an **individual** may sell the LoRA weights themselves, but not a product built around them. The images it makes are unrestricted for anyone. Full shape: [`anima`](../../anima/)." |

### Inconvenient

| Claim A | Claim B | Which is right | Recommended fix |
|---|---|---|---|
| `sdxl/SKILL.md:49` — Anima "is now roughly **the third-largest base-model ecosystem on Civitai**" `[flagged — re-verify]` | `anima/references/setup-and-workflows.md:201` — the owning skill's evidence is "a **sample of the first 100 items**… That is a composition figure, **not a census** — the true totals are unknown". Anima's own SKILL.md makes no ranking claim at all. | **B.** The passing mention states a rank the full treatment explicitly declines to state. The `[flagged]` marker mitigates but does not license it. (`krea-2/SKILL.md:271` independently places Krea 2 at #2 behind Illustrious, which is at least *compatible* with #3 — but neither number is sourced to the same measurement.) | → "and it is now one of the largest base-model ecosystems on Civitai, competing directly with Pony/Illustrious/NoobAI — a community checkpoint already out-downloads the official base `[flagged — re-verify]`". Drop the ordinal. |
| `krea-2/references/characters.md:42` — "Same author's noted weakness: tattoos (**Ideogram > Krea 2 > Z-Image** at learning them)". | `ideogram-4/SKILL.md:236` — Character LoRAs "Trainable but **undemonstrated** — the path exists, the ecosystem doesn't"; `:266` "no character LoRAs". | **Unresolved, and that is the problem.** krea-2 cites a named author who evidently trained and compared character LoRAs on Ideogram 4; ideogram-4 says nobody has. One of the two is stale. | Cheapest correct fix is in `ideogram-4`: soften `:236` to "Trainable, essentially undemonstrated — one cross-model comparison exists `[community — Any_Tea_3499, via krea-2]`, no published recipe." Alternatively drop the Ideogram term from the krea-2 parenthetical if it cannot be substantiated. |
| `krea-2/SKILL.md:232` — commercial-local reach-for: "[`flux-2`](../flux-2/) (Klein 4B) or [`sdxl`](../sdxl/) for unrestricted-revenue Apache/OpenRAIL paths". | `z-image/SKILL.md:203` — Apache-2.0, no revenue cap, "the least legally encumbered model in the suite". | **B** by omission. Same systematic gap as flux-2:278: the suite's freest licence is missing from the commercial reach-fors of two siblings. | Add `[`z-image`](../z-image/)` to the reach-for cell. |
| `sdxl/SKILL.md:219` — OpenRAIL++-M "quietly **one of SDXL's strongest advantages over the newer models**". | `z-image/SKILL.md:203` — Apache-2.0 is freer than OpenRAIL++-M, which carries downstream use-restrictions (`sdxl/SKILL.md:237`), and Z-Image is newer. | **B**, mildly. The claim is defensible against flux-2/ideogram-4/anima/krea-2 and wrong against z-image. | → "over most of the newer models — [`z-image`](../z-image/)'s Apache-2.0 is the one that is cleaner still, since OpenRAIL++-M's use-restrictions travel downstream." |
| `sdxl/SKILL.md:259` + `sdxl/references/lora-training.md:36` — Anima's LoRA pool is "young and **largely poorly trained**". | `anima/SKILL.md:211` — "**Large and growing fast**". Anima's contested list carries only the narrower character-LoRA-difficulty dispute (`:256`). | **Both, partially** — but the harsh judgement is asserted only in the *passing* skill and has no home in the owning one, which is backwards. | Either soften sdxl to "young, with quality that varies widely `[flagged — re-verify]`", or add the trainers' verdict to `anima/SKILL.md:211`'s cell so the passing mention has something to point at. |
| `z-image/SKILL.md:59` + `z-image/references/setup-and-workflows.md:106` — download `qwen_3_4b.safetensors` to `models/text_encoders/`, `CLIPLoader` type **`lumina2`**, from `Comfy-Org/z_image`. | `flux-2/SKILL.md:102` — download `qwen_3_4b.safetensors` to `models/text_encoders/`, `CLIPLoader` type **`flux2`**, from `Comfy-Org/flux2-klein`. | **Unresolved — and no skill says which.** Same basename, same folder, two repos, two loader types. Either they are one file (and the type dropdown is cosmetic, as `anima/SKILL.md:77` observes for Anima) or they are two files that collide on disk. The suite already treats exactly this hazard as documentation-worthy — see `scail-2/SKILL.md:99` (three names, one weight set) and `wan-2-2/SKILL.md:75` (a VAE split inside one release). | Resolve against the two HF repos, then state it once in both file tables: either "the same file [`z-image`](../z-image/) uses — download once" or "**not** the same file as Z-Image's despite the name; keep them apart or rename". Cannot be settled from repo contents alone. |

---

## The Anima licence sweep

Verified shape (per `anima/SKILL.md:224–235`, which quotes the card and licence verbatim): the
non-commercial restriction binds the **Model, not Outputs**; §1(a) puts Outputs outside "Derivative";
§2(e) grants Output use *"for any purpose (including for commercial purposes)"* **for anyone, company
or individual**; §2(c) lets an **individual** sell derivative *weights* but *"solely to the model
weights, and not to any larger product"*; hosting behind a paid API or embedding weights in a
monetised product is barred **even for individuals**.

Every mention across the six skills, plus the two out-of-slice skills that carry the same claim:

| Location | What it says | Matches? |
|---|---|---|
| `anima/SKILL.md:4` (description) | Outputs commercially free for anyone; weights NC; §2(c) quoted with its "not to any larger product" limit | ✅ exact |
| `anima/SKILL.md:9` | "two licences, both binding, and **generated images are carved out of both**" | ✅ |
| `anima/SKILL.md:202` (pre-flight #12) | "Images are commercially free for anyone; shipping the *weights* inside a product is not" | ✅ |
| `anima/SKILL.md:216` (suite table) | "images yes, model no… only individuals may sell *weights*" | ✅ |
| `anima/SKILL.md:220` | names the old shorthand and calls it "simply wrong" | ✅ — this is the corrective sentence the rest should agree with |
| `anima/SKILL.md:224–235` | full treatment, both licences, §1(a)/§2(c)/§2(e), the disallowed list, §4(a) content terms | ✅ canonical |
| `anima/SKILL.md:249` (two bars) | "the licence split between Outputs and Model" listed as a hard fact | ✅ |
| `anima/references/characters.md:91` | "the images Anima generates are not restricted at all… anyone may sell them" | ✅ |
| `anima/references/lora-training.md:115` | "bars training models for *commercial* use" | ✅ (that is §(c) of the commercial definition) |
| `anima/references/setup-and-workflows.md:212` | hosted platforms "run it under their own arrangements, and CircleStone's terms still bar *you* from serving the weights for money" | ✅ — a good, precise restatement |
| `sdxl/SKILL.md:4` (description) | "whose *weights* are non-commercial, even though its outputs are not" | ✅ |
| `sdxl/SKILL.md:49` | the fullest sibling treatment — §1(a), §2(e) quoted, §2(c)'s "not to any larger product", "for companies as much as individuals" | ✅ exact; this is the model for the others |
| `sdxl/SKILL.md:215` (suite table) | "Its *outputs* are commercially free, so paid illustration work is fine; SDXL wins when you must **ship or host the model itself**" | ✅ |
| `sdxl/SKILL.md:259` | "the weights-side licence restriction caps who can build a *product* on it" | ✅ |
| `sdxl/references/lora-training.md:36` | "Weights are non-commercial… **a LoRA you train on it inherits that**, though the images it makes do not" | ⚠️ **Half right — the surviving imprecision.** Outputs half is correct; the LoRA half omits §2(c)'s individual carve-out and reads as a flat bar on selling a LoRA. Fix in the Contradictions table above. |
| `z-image/SKILL.md:202` | "its **weights** are non-commercial where Z-Image's Apache-2.0 is not. Its outputs are commercially free, so the difference bites only when you ship or host the model itself" | ✅ |
| `z-image/SKILL.md:203` | "[`anima`] is non-commercial on the weights but not on what they produce" | ✅ |
| `image-production-workflows/SKILL.md:86` *(out of slice)* | "puts Outputs outside its definition of Derivative, so anyone, company included, may sell what they make with it — but no one may run Anima behind a paid API or ship its weights inside a product" | ✅ exact |
| `character-lora-training/SKILL.md:21`, `:166` *(out of slice)* | LLM-adapter trap only; makes no licence claim | ✅ n/a |
| `image-production-workflows/references/mixed-model-recipes.md:41`, `:53` *(out of slice)* | control/refine roles only; no licence claim | ✅ n/a |

**Surviving flat "Anima is non-commercial" shorthand: none in prose.** The specific error that was
corrected centrally is gone from every skill. One derived over-simplification survives at
`sdxl/references/lora-training.md:36` — it is about LoRA weights, not outputs, so it is a
narrower failure than the original, but it is the same shape and it is the only cell in the sweep
that would give a reader a wrong answer to a real question ("can I sell this LoRA?").

Two soft edges worth noting, neither wrong: `anima/SKILL.md:165` and
`anima/references/setup-and-workflows.md:189` recommend **Flux Klein 9B** as the photoreal-enhance
partner, and `krea-2/SKILL.md:228` recommends it for video-reference prep — Klein 9B is FLUX
Non-Commercial (`flux-2/SKILL.md:306`), which neither mention flags. The suite's licence-travels-with-
the-chain rule lives in `image-production-workflows/SKILL.md:86`, so a one-clause "(9B is
non-commercial; [klein] 4B is the Apache path)" in each would close it.

---

## Positioning conflicts

**Jobs with two claimed owners:**

1. **Photoreal faces and skin — the real conflict.** `z-image/SKILL.md:200` claims it as "**The
   headline strength**… Nothing better in the suite". `sdxl/SKILL.md:214` claims the identical phrase
   — "**The headline strength once you leave raw base**" — and routes onward to krea-2 rather than
   z-image, never naming z-image on this axis at all. Every *other* skill agrees the owner is z-image:
   `krea-2:224`, `ideogram-4:237`, `anima:215` all route there. sdxl is the outlier, and its reach-for
   is additionally wrong about krea-2 (see Contradictions). **Owner: `z-image`** for faces and skin;
   sdxl's honest claim is *photoreal-via-finetune with the deepest control stack*, which is a different
   axis and worth saying that way.

2. **Commercial-clean local work — two claimants, plus systematic omission.** `z-image:203` ("the
   least legally encumbered model in the suite… Nothing is freer") versus `flux-2:278` ("the suite's
   only Apache-2.0 path"). z-image is right; flux-2 is right only about its own family. Compounding
   it, z-image is absent from the commercial reach-for cells of both `flux-2:278` and `krea-2:232`,
   and `ideogram-4:240` does list it correctly — so the gap is specific, not universal. **Owner:
   `z-image`**, with flux-2 [klein] 4B as the co-equal Apache option at a different size/speed point.

3. **Purpose-restricted weights — a false exclusivity claim.** `ideogram-4:240` claims to be the only
   one; flux-2 and anima are the other two. Covered above. Not a two-owner conflict so much as a
   one-owner claim over a category with three members.

**Jobs with exactly one owner (no conflict):**

- **Anime illustration → `anima`.** `anima:214` claims it ("This is what it is for — the strongest
  open anime model with a modern encoder"); `z-image:202` and `sdxl:215` both route there and neither
  contests it; `sdxl:215` correctly keeps the narrower claim it can defend (booru finetunes, commercially
  clean end to end, deepest ControlNet). krea-2, flux-2 and ideogram-4 are silent — silence, not conflict.
- **In-image typography → `ideogram-4`.** Named as the leader by `z-image:198`, `sdxl:216`,
  `flux-2:276`, `krea-2:230`, `krea-2/references/prompting-guide.md:60` and `:99`, and `anima:212`.
  `ideogram-4:233` claims it with "— (this is why you're here)". Six-for-six. The cleanest positioning
  in the image half.
- **Aesthetic range / stylistic exploration → `krea-2`** (`krea-2:223` claims it with no reach-for;
  `z-image:201`, `flux-2:279`, `ideogram-4:238` all route there).
- **Structural control → `sdxl`** (`sdxl:213` "— (this is SDXL's edge)"; all five siblings route there).
- **Consistent characters — split cleanly, not contested.** No-training/multi-reference → `flux-2`
  (`z-image:196`, `sdxl:211`, `krea-2:226`, `ideogram-4:234`, `anima:210`). Trained + adapter depth →
  `sdxl` (`flux-2:274`, `anima:210`, `ideogram-4:236`). The two sub-axes are named consistently.

**Jobs with no owner:** none found. Every required §6.5 axis has a named destination somewhere,
including the honest "this model can't" cells.

---

## Conditioning-class doctrine

**Anima's exception is real, well-argued, and mostly refines the doctrine rather than breaking it —
but three siblings state the doctrine in a form that anima flatly contradicts, and one reference
states it in a form that is simply wrong.**

The doctrine as stated today:

| Where | Wording | Status against anima |
|---|---|---|
| `z-image/SKILL.md:29` | "Prompting dialect, LoRA trigger handling, and caption style **all follow the encoder**." | ❌ Universal. Anima's encoder is an LLM and its dialect is booru-with-weights. |
| `flux-2/SKILL.md:35` | "Prompt dialect, LoRA triggers, and training captions **all follow the encoder**." | ❌ Universal. |
| `sdxl/SKILL.md:55` | "Dialect, triggers, and captions **all follow the encoder**, not folklore." | ❌ Universal. |
| `flux-2/references/prompting-guide.md:338` | "meaningless **for LLM encoders**" | ❌❌ The strongest form and the most actionable — see Contradictions. |
| `krea-2/SKILL.md:56` | "the same sentence rule governs FLUX.2's Mistral/Qwen3 **and** Z-Image's Qwen-3; the opposite… governs CLIP models like SDXL." | ✅ **Survives.** Enumerates the models it covers instead of quantifying over encoder classes. This is already the right shape. |
| `sdxl/SKILL.md:47` | "**Dialect follows the checkpoint.** Pony and Illustrious were trained on tag vocabularies and need their own dialect" | ✅ **Survives, and is anima's thesis already.** sdxl states the corpus rule two paragraphs *before* it states the encoder rule, and the two do not agree with each other inside one file. |
| `z-image/references/setup-and-workflows.md:164`, `sdxl/references/checkpoints-and-loras.md:76`, `flux-2/references/setup-and-workflows.md:260` | trigger-handling framed as "a consistent LLM-encoder pattern" / "the opposite of tag-based SDXL" | ✅ Survives — these are about trigger *tokens*, where the encoder genuinely is the cause. |

**Does anima's exception sit coherently?** Yes — the argument at `anima/SKILL.md:43–53` is the strongest
piece of reasoning in the six skills: it does not claim the rule is wrong, it identifies the conflated
variable ("Encoder class sets what a dialect *can* express; the **caption corpus** sets what the model
is fluent in"), gives three independently checkable verifications, and supplies the mechanism (the
T5-tokenised weight channel the LLM adapter multiplies into its output). `anima/references/prompting-guide.md:28`
restates it consistently. Nothing in anima overclaims.

**Two defects in how it lands:**

1. **Its premise is false.** `anima/SKILL.md:51` says every earlier LLM-encoder model in the suite was
   captioned in prose. `ideogram-4` — Qwen3-VL-8B encoder, "trained **exclusively** on structured JSON
   captions" — is a second, older separation of encoder from corpus. Anima is the second exception, not
   the first, and saying so makes the thesis stronger, not weaker. Fix in Contradictions.
2. **The doctrine is not restated where it needs to be.** A reader arriving at `z-image:29`,
   `flux-2:35` or `sdxl:55` is told a universal that two suite models violate.

**Concrete restatement — apply the same clause in all three, matched to each skill's voice.** Keep the
existing sentence and append:

> …all follow the encoder **here** — but the encoder is a proxy for the caption corpus, and the two can
> come apart: [`anima`](../anima/) has an LLM encoder and takes weighted Danbooru tags, and
> [`ideogram-4`](../ideogram-4/) has one and takes JSON. **Check what a model was captioned on before
> inferring its dialect from its encoder name.**

(In `flux-2` and `sdxl` the sibling paths are `../anima/` and `../ideogram-4/`; in `z-image` likewise.
`sdxl` should additionally reconcile `:47` and `:55` with each other — `:47`'s "dialect follows the
checkpoint" is the corpus rule and should be named as the general case, with the encoder rule as the
usual consequence of it.)

---

## Duplicated passages

Most apparent duplication in this suite is deliberate per-model calibration and should be left alone —
the photoreal camera/film/lens stacks (`z-image:133–137`, `sdxl:138–146`, `flux-2:210–215`,
`krea-2:145`) genuinely differ per model, and `ideogram-4:116–124` *inverts* the advice, which is the
whole point. Likewise the "VAE-decode to pixels between families" rule appears in all six as a
one-liner pointing at `image-production-workflows` — that is correct restatement, not duplication.

Two genuine cases:

| Passage | Where it appears | Recommended owner |
|---|---|---|
| **The ~6-outfit multi-outfit ceiling**, same finding, same citation (`[community — Khanykov01, Civitai 6990]`), stated four times in near-identical words | `z-image/references/characters.md:67`, `sdxl/references/characters.md:63`, `flux-2/references/characters.md:49`, `krea-2/references/characters.md:84` | **`character-lora-training/references/dataset-and-captioning.md` §5** — which already owns it verbatim at `:122–124`, including the "outfits bleed before the identity degrades" mechanism the four copies drop. None of the four links to it. Replace each with a one-line delta plus the link. |
| **The signature-outfit-uncaptioned trick**, three near-identical sentences | `z-image/references/characters.md:66`, `sdxl/references/characters.md:62`, `flux-2/references/characters.md:48` | Same owner. It is a captioning rule, which is `character-lora-training`'s subject; the model-specific half (edit-model factory vs multi-reference as the wardrobe replacement) is the part worth keeping locally. |

Correctly-owned already, for the record: the 8-point rotation protocol (owner `z-image/references/prompting-guide.md`
§3.3–3.5 for the clause forms, `character-lora-training` for the coverage rule — both cited by
`sdxl/references/characters.md:34` and `flux-2/references/characters.md:38`); Differential Output
Preservation (owner `character-lora-training`, with krea-2 and z-image each recording their half and
each explicitly saying "treat the pair as one report" — `krea-2/references/characters.md:55`,
`z-image/references/characters.md:70`; this is exemplary); the detailer LoRA-swap rung (owner
`image-production-workflows/SKILL.md:60`).

---

## Reciprocity gaps

§6.5: "Adding a row that names a sibling obliges you to add the return row in that sibling."
SKILL.md-level link maps:

| Skill | Links to (SKILL.md) |
|---|---|
| `flux-2` | ideogram-4, image-production-workflows, krea-2, ltx-2-5, minimax-h3, sdxl, wan-2-2 |
| `ideogram-4` | character-lora-training, flux-2, image-production-workflows, krea-2, sdxl, wan-2-2, z-image |
| `z-image` | anima, character-lora-training, flux-2, ideogram-4, image-production-workflows, krea-2, sdxl, wan-2-2 |
| `sdxl` | anima, flux-2, ideogram-4, image-production-workflows, krea-2, wan-2-2, z-image |
| `krea-2` | flux-2, ideogram-4, image-production-workflows, ltx-2-5, minimax-h3, scail-2, sdxl, wan-2-2, z-image |
| `anima` | character-lora-training, comfyui-on-runpod, flux-2, ideogram-4, image-production-workflows, krea-2, minimax-h3, sdxl, wan-2-2, z-image |

| Gap | Detail |
|---|---|
| **`flux-2` → `z-image`** — the known open item, **confirmed** | `z-image:196` routes no-training identity to flux-2; `z-image:217`-equivalent in sdxl also names it. flux-2's suite table names z-image nowhere, and the only z-image link in the whole skill is `flux-2/references/characters.md:38`. flux-2 is the **only** image skill with no z-image link in its suite table. Related cause: flux-2 has no photoreal row (`§6.5` axis 5 is satisfied by "Aesthetic range / anti-AI-look", which is defensible), so the natural slot for the return link does not exist. **Fix:** add a "Photoreal faces & skin" row — "Strong on [dev]; [klein] skews over-sharpened (see *Realism*)" → "[`z-image`](../z-image/) — the suite's face and skin finisher". That closes the reciprocity gap and the axis-5 question at once. |
| **`flux-2` → `anima`** | `anima:210` (characters) and `anima:215` (photoreal) both name flux-2. No return anywhere in flux-2. **Fix:** an "Anime / booru illustration" row → "Not its dialect — an LLM encoder wants sentences" → "[`anima`](../anima/), the anime-native base; [`sdxl`](../sdxl/) for the Illustrious/Pony finetunes". |
| **`krea-2` → `anima`** | `anima:165` and `anima:215` both name krea-2 as a refiner/photoreal destination. No return anywhere in krea-2. **Fix:** same row shape as above, or fold into `krea-2:223`'s aesthetic-range row. |
| **`ideogram-4` → `anima`** | `anima:212` routes typography to ideogram-4. No return. Lower priority — ideogram-4's table is complete against §6.5 without it, and the honest return is a one-cell mention in the stylised-imagery row (`:238`). |
| **`flux-2` → `character-lora-training`** | Every other image skill links it from SKILL.md; flux-2 links it only from `references/lora-training.md:68`. Not a §6.5 requirement, but flux-2 is the odd one out. |

`flux-2` accounts for three of the five gaps and is the clear target for a single repair pass.

---

## Verified consistent

Checked and in agreement across all six — no action:

- **Every Anima licence mention in prose.** The central correction landed; the flat "non-commercial"
  shorthand is gone. One derived imprecision remains (above), not the original error.
- **Typography ownership.** Six skills, one destination, consistent framing.
- **The guidance-off convention.** `CFG 1.0 in a ComfyUI KSampler = guidance-off = diffusers 0.0, never
  type 0.0` is stated identically in `z-image:21/98`, `sdxl:33`, `flux-2:45/247`, `krea-2:45/123/207`
  and `anima:86/116`. krea-2 additionally documents its own second convention (`:45` footnote 2) and
  the conversion — correct, not a conflict.
- **SDXL's ~1.05–1.3 weight band**, stated identically in `sdxl:64/177/196`,
  `sdxl/references/prompting-guide.md:42/169`, and quoted correctly by `anima:31/177/194` and
  `anima/references/prompting-guide.md:116` as the band to recalibrate *away from*.
- **Decode-to-pixels between families**, and the reason for it, in all six plus
  `image-production-workflows:70`. `ideogram-4:189` adds the sharpest version (a shared VAE means the
  decoders agree, not that the latents carry meaning) and it does not contradict anyone.
- **Cross-family refine denoise bands** (~0.25–0.4 for a texture/realism pass): `sdxl:165`,
  `flux-2:232`, `z-image/references/setup-and-workflows.md:299`, `krea-2:180`, `anima/references/setup-and-workflows.md:189`,
  all inside `image-production-workflows:41–50`'s published bands.
- **Train-on-the-undistilled-variant rule**, stated as a suite pattern and attributed as such:
  `z-image:15`, `flux-2:190` + `flux-2/references/lora-training.md:64`, `krea-2:39` +
  `krea-2/references/lora-training.md:25`, `anima:17`, `sdxl:109`.
- **The Qwen-Image VAE shared by `krea-2` and `anima`** (`krea-2:80`, `anima:71`) — genuinely the same
  file, consistently named, and both skills still (correctly) insist on decoding to pixels across the
  boundary.
- **The flux2-vae reuse by `ideogram-4`** (`ideogram-4:164/189`, `flux-2:103`) — correctly identified,
  correctly caveated on both sides.
- **Multi-character positioning.** `krea-2:227` claims the most promising answer, `sdxl/references/characters.md:64`
  claims best-equipped, `z-image/references/characters.md:70` records the failure — all three hedge the
  single-report DOP evidence identically and cross-reference each other. Model behaviour for the suite.
