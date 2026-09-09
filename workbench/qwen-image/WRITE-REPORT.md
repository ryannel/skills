# qwen-image — write report (2026-09-09)

Authored `skills/generative-media/qwen-image/` — `SKILL.md`, five references, `LICENSE` (copied from `krea-2`). No sibling, atlas, README, `marketplace.json` or `freshness.json` was touched. No web fetches were made; every claim traces to the three workbench reports.

## 1. Word counts against STANDARD §5

Raw `wc -w`. The 2026-08-22 census counted "per-section body excluding the heading" — calibrated against `krea-2/SKILL.md` at commit `a5d6473` (raw 5,564 vs census 5,292) it is approximately raw minus frontmatter and headings, so the census-equivalent column subtracts the 311-word description and ~80 words of headings from `SKILL.md`, and ~2–3% from the references.

| File | Raw | Census-equivalent | Band | Verdict |
|---|---|---|---|---|
| `SKILL.md` | 6,306 (348 lines) | ~5,900 | 2,800–5,500 abs; 25–40% of corpus; ≤500 lines | **~400 over the absolute cap**; share 30.7% ✓; lines ✓. Justification below |
| `references/prompting-guide.md` | 2,552 | ~2,480 | 700–3,500 | ✓ (`## Contents` present, ≥2,000) |
| `references/setup-and-workflows.md` | 3,929 | ~3,820 | 700–3,500 | over; accepted with `## Contents` TOC per §5.2 |
| `references/lora-training.md` | 4,480 | ~4,360 | 700–3,500 | over; accepted with `## Contents` TOC per §5.2 |
| `references/characters.md` | 2,193 | ~2,130 | 700–3,500 | ✓ |
| `references/api-and-hosted.md` | 1,096 | ~1,070 | 700–3,500 | ✓ |
| **Corpus** | **20,556** | **~19,750** | 10,000–16,000 | **~3,700 over** |

The first draft was 23,337 raw; three trim passes removed ~2,800 words. What remains over the band is tables that carry numbers a reader will type: the per-template settings table (11 templates), the quant ladder and its maintainers, the ControlNet/inpainting template table, the Edit-LoRA recipe table, the hyperparameter table. Cutting those would drop mechanism, not padding (§5.3). **Named justification for `SKILL.md` above 5,500** (§5.2 allows two of its four grounds here): *more task modes than the suite norm* — T2I, single-image edit, three Edit generations with different LoRA compatibility, multi-image fusion, layer decomposition, four control mechanisms, and a hosted 2.0/3.0 surface; and *a documented capability set the official templates do not expose* — the Edit reference-path bypass, which is the single largest quality lever on the model and appears in no template. For the corpus, the second pass should decide between accepting the overage on the same grounds or cutting the two template tables in `setup-and-workflows.md §1` and `§6` down to the four templates a reader actually runs.

Other §6 checks: description 311 words (band 180–320) ✓; two-bar heading verbatim, second-to-last ✓; `Facts dated 2026-09-09; community craft refreshed 2026-09-09` as the final paragraph ✓; atlas hint blockquote at the top ✓; suite table with all eight required image-model rows plus the atlas row, links all `../sibling/` and all resolve ✓; `§` deep-links from `SKILL.md` all resolve to numbered headings ✓; no bare (unbackticked) markers, no nested markers, no payload over ~60 characters except one 62-character convergent marker ✓.

**Marker census (§6.2.1):** 136 markers over ~19,750 census words = **6.9/1k** (band 2.5–7.0). `SKILL.md` 38 (6.4/1k), references 98 (7.1/1k), layer ratio 0.90 (≥0.6 ✓). Watchlist class: **24 markers exactly** (cap 24; 1.22/1k ≤ 1.6 ✓). Distinct payloads 83, reuse factor 1.64 (≤2.0 ✓). The most-repeated payloads are `[contested]` (12), `[flagged — re-verify]` (9), `[community — nsfwVariant]` (8), `[community — Top_Buffalo1668]` (7).

**Readability (§6.8a):** median tangle 7.5, none over 15 — `SKILL.md` 11.3, `lora-training.md` 8.1, `characters.md` 8.1, `prompting-guide.md` 6.9, `api-and-hosted.md` 6.8, `setup-and-workflows.md` 5.9.

## 2. The one rule, and why

**Chosen: "Every Qwen-Image variant is a true-CFG model; the family runs in exactly two regimes, and you never mix them."** `guidance_embeds: false` on all six transformer configs is the discovered conditioning fact, and it decides every number the reader types: steps (20–50 vs 4–8), CFG (2.5–4.0 vs exactly 1.0), whether the negative prompt is live, `true_cfg_scale` vs the inert `guidance_scale` in diffusers, and why the templates use switch nodes. It also corrects the encoder-based misreading the image-models reference warns about — negatives die at CFG 1 because of guidance state, not because the encoder is Qwen. It applies to every reader (T2I and Edit alike), which is the test the spec sets: *which choice most changes what the reader does next.* The stock template's broken fp8 + bf16-Lightning pairing is folded into the same section as its third consequence.

**The runner-up, the `TextEncodeQwenImageEditPlus` 1 MP AREA downscale, is folded in prominently:** it is named in the one-rule section as "the other rule, for Edit only", carries its own slot-8 section (*The Edit reference path — bypass the 1 MP downscale*), the first two rows of the failure table, and item 5 of the pre-flight. It lost the top slot only because it applies to Edit users alone and is a workflow bug rather than a property of the model's conditioning path.

## 3. Every `[flagged]` and `[contested]` marker (seeds the freshness watchlist)

24 markers; grouped into 15 watchlist claims where a claim is marked in both `SKILL.md` and a reference.

| # | Claim | Markers (file : section) |
|---|---|---|
| 1 | Stock base template pairs downcast `fp8_e4m3fn` with a bf16 Lightning LoRA; Lightning maintainers mark it broken; no Comfy-Org statement on whether fp8 handling was patched | `SKILL.md` : one rule — `[flagged — re-verify]` · `setup-and-workflows.md §4` — `[flagged — re-verify]` |
| 2 | Qwen-Image-Layered: adopted, trainable, no settings-level craft anywhere | `SKILL.md` : Variant selector — `[flagged — gap; re-verify]` |
| 3 | Negatives on the base regime: the authoring spec's unattributed "ignored across CFG 1–7" report could not be sourced; treated as live at CFG > 1 | `SKILL.md` : two-bar — `[flagged — re-verify]` |
| 4 | Packaging that moves: Lightning and GGUF filenames and maintainers (QuantStack → unsloth at 2511), the Nunchaku gap (official builds stopped 2025-11-16, nothing for 2511/2512/Layered), the closed status of 2.0 and 3.0, hosted pricing | `SKILL.md` : two-bar — `[flagged — re-verify]` · `setup-and-workflows.md §2.2` — `[flagged — re-verify]` · `§2.3` — `[flagged — re-verify]` |
| 5 | What `fp8mixed` and `int8_convrot` quantise is undocumented; nvfp4 assumed Blackwell-only | `setup-and-workflows.md §2.1` — `[flagged — re-verify]` |
| 6 | Hosted pricing (all secondary: ~$0.04/1K, $0.075/2K, $0.03 standard, ¥0.18) and the 3.0 launch date | `api-and-hosted.md §5` — `[flagged — secondary, unverified; re-verify before quoting]` |
| 7 | The two unlabelled trailing booleans on the ComfyUI API nodes are assumed to be `prompt_extend` and `watermark` | `api-and-hosted.md §3` — `[flagged — re-verify]` |
| 8 | `--zero_cond_t` for Edit-2511 is documented by one comment line in a DiffSynth script and has no ai-toolkit/musubi counterpart | `lora-training.md §1.3` — `[flagged — re-verify]` |
| 9 | Edit-2511 in ai-toolkit needs a 1024² solid black control image and uses 30–50% more VRAM than 2512 (single report) | `lora-training.md §6` — `[flagged — re-verify before a paid run]` |
| 10 | Lightning quality: loss (plastic skin, three authors) vs gain for text (one author); 2511's 4-step LoRA blocky (MastMaithun) vs the 8-step fixing drift (DrinksAtTheSpaceBar) | `SKILL.md` : two-bar — `[contested]` · `setup-and-workflows.md §4` — `[contested]` |
| 11 | Samplers: `euler`/`simple` best on Edit vs RES4LYF needed for T2I realism | `SKILL.md` : two-bar — `[contested]` |
| 12 | Quant floor: fp8 ≫ Q8 GGUF vs no difference Q4–Q8 | `SKILL.md` : two-bar — `[contested]` |
| 13 | Abliterated text encoders: mechanism + leading craft author say no; second-hand minority says yes | `SKILL.md` : two-bar — `[contested]` |
| 14 | "Positive magic" suffix: in official code and most templates, absent from realism authors' settings, never A/B'd | `SKILL.md` : two-bar — `[contested]` · `prompting-guide.md §4` — `[contested]` |
| 15 | LoRA hyperparameters: LR 5e-5/1e-4/2e-4; rank 16/32/128; training resolution 1024 vs the 1328 class (untested); `weighted` vs `sigmoid`; caption length (verbose / 30–50 words / one word / none; plus the gender-word rule that contradicts suite practice); composition 60/30/10 vs 33/33/33 vs one-third; GA 1 vs 2; uint3 quality cost | `SKILL.md` : two-bar — `[contested]` · `lora-training.md §3` (1328 class) — `[contested]` · `§4` (captions) — `[contested]` · `§5` (composition) — `[contested]` · `§8` (the roll-up) — `[contested]` |

## 4. Proposed freshness tier: **hot**, with a review to `active` once the 2.0/3.0 weights question settles

Reasons: the family shipped six open variants in five months and two hosted models since, and a weights drop for 2.0 or 3.0 would rewrite the selector, the licence table and the open/closed line in the same pass. The packaging layer moves weekly — GGUF changed maintainer at 2511, Nunchaku stalled, the int8 template appeared 2026-07-10, the 3.0 API templates 2026-08-06, and Edit-Lightning V2.0 is on the maintainers' todo list. Hosted pricing is unverified. Watchlist items 1, 4, 5 and 6 are the ones a daily check should hit; items 10–15 resolve slowly and can be checked monthly.

## 5. Comparative notes siblings must reciprocate (second pass)

| Sibling | What this skill says | Return row or sentence needed |
|---|---|---|
| `z-image` | Suite table: Z-Image is the realism finisher for a Qwen composition; Z-Image sends its anchor to Qwen-Image-Edit to be multiplied; "no camera-words fix here — the reverse of z-image". | (a) Suite table *Consistent characters* and *Mixed-model pipelines* rows: link [`qwen-image`](../qwen-image/) as the dataset factory and the composition it finishes. (b) `references/characters.md §3` names Qwen-Image-Edit as the factory in plain text — link it. (c) **Discrepancy to fix:** `z-image/references/characters.md §3` states the 2511 template samples at "40 steps / CFG 3"; the template JSON carries 40 / **4.0** (official-report §4). |
| `krea-2` | Suite table: Krea 2 for Identity Edit and multi-character DOP; Krea 2 sends anchors to Qwen-Image-Edit; `lora-training.md §9` lists Krea doctrine that does not transfer (shift 2.5, 1024-native source rule, LoKr, GA 2, Raw/Turbo); Ashen3's "photo, never photorealistic" is cited as Krea evidence. | (a) Suite table *Consistent characters* / a new *Instruction editing* row: link [`qwen-image`](../qwen-image/) as the multi-reference edit engine and dataset factory (its `characters.md §2` says "borrow another family's edit model" — link it). (b) `lora-training.md §9`: one sentence that the 1024-native rule, shift 2.5, LoKr and GA-2 are Krea findings that do not transfer to Qwen-Image, with the link. (c) Consider carrying Ashen3's photo/photorealistic rule in `prompting-guide.md §3`, since it was written for the Krea 2 build. |
| `flux-2` | Suite table: flux-2 for PuLID / ReferenceLatent-class adapters and its multi-reference path. | Its comparative table should link [`qwen-image`](../qwen-image/) as the open-weights alternative for multi-reference editing and character re-shooting without adapters. |
| `ideogram-4` | Suite table: ideogram-4 for typography-led layout and dense lettering. | Its typography row should name [`qwen-image`](../qwen-image/) for *editing existing in-image text while preserving font*, and for bilingual Chinese/English rendering. |
| `sdxl` | Suite table: sdxl for the most complete control stack and the deepest mature LoRA ecosystem. | Its *Consistent characters* / edit rows should name [`qwen-image`](../qwen-image/) as the no-training edit engine and dataset factory. |
| `image-production-workflows` | Linked as the owner of cross-model craft; qwen-image is "the edit engine and dataset factory for other families' stills; decode to pixels; Z-Image finishes its skin". | Add a `qwen-image` row to the suite map with that role. |
| `character-lora-training` | Linked for the craft that transfers; qwen-image records 60/30/10 vs the one-third rule as contested, and the plain-name trigger. | Add a Qwen-Image row to the routing-inward table: "the thing you cannot skip" = train on the bf16 base for the *deploy generation* (2509/2511/2512 LoRAs are mutually incompatible), plain-name trigger, no adapter. Note the 60/30/10 dispute against the one-third rule. |
| `comfyui-on-runpod` | Linked for renting the GPU. | Optional: volume sizing note — the fp8 build wants ~26 GB combined, and training needs the 40.86 GB bf16 DiT plus the 16.58 GB encoder. |
| `wan-2-2` | Suite table *Making it move*: a still composed on T2I and given its angles on Edit goes to Wan I2V; the VAE is the same family. | Its *Locking a still first* row should name [`qwen-image`](../qwen-image/) alongside z-image and krea-2, and may note the Wan-2.1-family VAE kinship. |
| `generative-media-atlas` | Linked in the atlas hint and the suite table's last row. | Replace the "not yet covered" row; add to the suite map and rankings (no-training identity → Edit-2511; typography → strong bilingual; licence → Apache-2.0 tie with Z-Image; control → native 2509 + InstantX). Reconcile `adult-work.md`: the atlas has 24% / 54%; this pass has 25.8% adult of 1,637 total LoRAs (full pagination with `nsfw=true`) and 31% explicit among character-tagged; the community report's NSFW-excluded cut gave 20% / 45%. |

## 6. What could not be sourced (carried as absences, not guesses)

- Per-image pricing on Alibaba Model Studio — every figure is secondary (`api-and-hosted.md §5`).
- Qwen-Image 3.0's first-party launch date and openness statement; the QwenLM README stops at 2.0.
- What `fp8mixed` and `int8_convrot` actually quantise.
- Whether ComfyUI works around the Lightning-on-`fp8_e4m3fn` grid.
- Official inference VRAM floors — the table is synthesised from named reports.
- A first-hand Chinese-vs-Latin glyph comparison; the Chinese-language venues were not sampled.
- A denoise ladder for Qwen img2img/inpaint — absent; the skill says it must be measured.
- How many sequential Edit passes identity survives — absent.
- Any settings-level craft for Qwen-Image-Layered.
- Qwen-specific seed behaviour (thin), OneTrainer's Qwen defaults (none found), a Qwen Lightning-LoRA *training* recipe (asked, no replies).
- The authoring spec's "negatives ignored across CFG 1.0–7.0" community claim — no named author found; recorded as a flag rather than adopted.
- The 1472 × 1140 vs 1104 aspect figure — read as a typo on geometric grounds and the hosted size set, not on a Qwen statement.

Nothing in the skill is `[live-use]`; every media-lab finding a sibling cites is Krea 2 evidence and is labelled as such where it appears.
