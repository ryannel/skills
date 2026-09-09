# cleanup — write report, 2026-09-09

## Edits by file

- `z-image/references/lora-training.md` · §3.2 · adamw8bit/BF16 report carried, Z-Image-specific until reproduced `[community — AInVFX, 2026-04-06; single report; re-verify]`; §8 debug row.
- `ideogram-4/references/lora-training.md` · §4, §5 · "36 LoRAs, one character-tagged, per the 2026-09-09 pull" `[community — Civitai API, queried 2026-09-09]`; `types=LORA` caveat kept. `SKILL.md` · six mentions of 34 / "no character LoRAs" aligned.
- `character-lora-training/SKILL.md` · minimax-h3 boundary row rewritten (pruned/INT8 trainable; r32 collapse "with distillation handling off"); pre-flight #5; rank row; Ideogram row; four body markers folded into two-bar; three two-bar bullets merged into one "lab vs community recipe" bullet (steps incl. the 600–1,200 report, dropout/evenness, trigger); `§5`→`§4` pointers; new reference row.
- `character-lora-training/references/dataset-and-captioning.md` · §4 moved out; §5/§6 → §4/§5; Reddit: 10–15 images @ 600–1,200 steps (§1, single report, beside the lab's 2,500 as a contested range), 29/29/29 shot-distance split with the far-shot reasoning (§2), small-face smeared-average mechanism (§2, `1wakjxx`+`1wacvcm`, convergent), caption-what-stays-promptable + don't-mix-styles (§4), multi-class averaging (§5). Multi-res flag points at krea-2 §2c, its owner; length + dropout share one `[contested]`.
- `character-lora-training/references/synthetic-datasets.md` · **new** (1,863 w): old §4; LTX ¶18 flag points at `ltx-2-5/references/licence-and-derivatives.md`, its owner.
- `character-lora-training/references/nsfw-training.md` · two § pointers renumbered.
- `krea-2/references/lora-training.md` · §3b, §5, §8, §9, §10 cut to rules + anchors + pointers (doctrine now pointed at c-l-t; prompting rules at `prompting-guide.md §3`); §3b adds the 600–1,200 report and the H3 r32 caveat; §3a hardware → one line.
- `krea-2/references/media-lab-runs.md` · **new** (2,258 w): Amy and Ciara run tables, peak rung per dataset, hardware/cost, resolution sweep, cfg check, wall wording, the wrong turn as it happened. Only facts already in the sources.
- `krea-2/SKILL.md` · reference table row for the ledger. `krea-2/references/characters.md` · nested-backtick marker normalised.
- `minimax-h3` · **no edit**: every note addressed to it, FastH3 6-step ≥1.0 included, is already in its text.

## Conflicts

1. c-l-t said "train H3 on a non-pruned checkpoint"; minimax-h3 says that rule is now wrong (trainer docs). Kept minimax-h3, fixed c-l-t.
2. c-l-t and krea-2 stated the H3 r32 collapse bare; minimax-h3 attributes it to distillation handling off. Aligned both to minimax-h3.
3. Ideogram 34 vs 36/1: applied 36/1 as instructed; whether the 09-09 pull used `types=LORA` is not recorded, so the caveat stays.
4. Brief asked for `; corroborated`; STANDARD §6.2's closed set has no such qualifier, so `convergent` is used.

## Already consistent (verified, no edit)

c-l-t→krea-2; c-l-t→minimax-h3; krea-2→minimax-h3; image-production-workflows→minimax-h3 (#15644) and →z-image (regional).

## Marker counts (watch class)

c-l-t **32 → 23**; krea-2 23; z-image 19; ideogram-4 25 (pre-existing); minimax-h3 24. No uncertainty deleted: each merge names every claim, and the two cross-skill flags point at their owners.

## Word counts (`wc -w`)

krea-2 `lora-training.md` 8,300 → 7,659 (+ledger 2,258) — still over the 3,500 band; what remains is the recipe, two trainer configs, adult work and deploy rules, under a TOC. c-l-t: SKILL 7,281 → 7,392; `dataset-and-captioning.md` 8,241 → 7,106 (106 over 7,000 after the Reddit additions; §3 could join the new file next pass); evaluation 6,644; nsfw 3,777; publishing 1,825; synthetic 1,863. c-l-t now has five references against the 2–4 shape; the 7,000-word rule forced it.

## Checks

288 relative links resolve; 0 broken. No malformed or bare watch-class markers (three residual grep hits in minimax-h3 are LoRA names / prompt syntax in code spans). All `Facts dated` ≥ 2026-09-09. Five frontmatters parse. Readability: c-l-t median 6.7, krea-2 7.1, none over 15.

## For the orchestrator

New markers: `[community — r/StableDiffusion 1wacvcm|1wakjxx|1w9ysn0, 2026-09; …]` (c-l-t, krea-2 §3b). c-l-t's merged two-bar bullet is one watchlist entry. Register `synthetic-datasets.md` and `media-lab-runs.md` in freshness.
