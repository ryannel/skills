# anima — writer report, 2026-09-09

## Edits (file · section · change · evidence)

- `SKILL.md` · Variant selector, Aesthetic row · CFG "community converges on ~3" `[community — PromptHero; re-verify]` · prompthero.com/ai-models/anima-official-2458426-download/anima-aesthetic-v11
- `SKILL.md` · Variant selector, Turbo row · v1.1 added, HF tree 2026-08-26, undocumented; early Civitai flatness note `[community — Civitai 2458426; re-verify]` · huggingface.co/circlestone-labs/Anima/tree/main/split_files/diffusion_models
- `SKILL.md` · Variant selector, 2.9B row · silent corruption / block-key remap, PR #2418 pointer, deep-link to setup §7 · lilting.ch article ; kohya-ss/sd-scripts PR #2418
- `SKILL.md` · Variant blockquote · "out-downloads" reversed: official ~219k leads MiaoMiao's Anima builds ~103k; old figure mixed base models; SDXL analogy withdrawn · civitai.com/api/v1/models/2458426 ; /934764
- `SKILL.md` · File layout, Per-variant Aesthetic, Pre-flight 7 · Turbo v1.1 filename; Aesthetic CFG start 3 · as above
- `SKILL.md` · Artist-tag lever · 42k+ → 40k+ (site count), index named for 59k · animastyles.thetacursed.com ; ThetaCursed/Anima-Style-Explorer
- `SKILL.md` · Licence, forks paragraph · unanswered `[flagged]` removed; remap fix and PR #2418 stated; "not production" kept
- `SKILL.md` · Two-bar · 2.9B bullet → Turbo v1.1 `[flagged — re-verify]`; Aesthetic-CFG bullet updated; volatile-items line names the remap and PR #2418; "settled this pass" added; **Facts dated 2026-09-09**
- `setup-and-workflows.md` · §1 · Turbo v1.1 file and date · HF tree
- `setup-and-workflows.md` · §2 · community ~3 with quoted line, marked · PromptHero
- `setup-and-workflows.md` · §7 · 28→40-block shift, 0/3 as-is vs 3/3 remapped `[community — lilting.ch, 2026-08-12; single report]`; PR #2418 `[pending release]`; 3.8B unknown
- `setup-and-workflows.md` · §11 · same-base count (official 218,777 / Base 89,433 / MiaoMiao 215,667 all bases, ~102.6k Anima); top table rows updated and dated; "compare same-base" caveat · Civitai API 2026-09-09
- `setup-and-workflows.md` · §11 discovery · repo live again; flag moved from URL volatility to the 40k-vs-59k count
- `prompting-guide.md` · §6, worked-prompt note · same style-count and repo-status correction
- `lora-training.md` · §2 · OneTrainer merged 2026-07-04, PR #1487, issue #1278 closed, diffusers Cosmos-pipeline dependency `[official — Nerogar/OneTrainer PR #1487]`; sd-scripts row notes PR #2418 · github.com/Nerogar/OneTrainer/pull/1487
- `lora-training.md` · §3 · per-type recipe table `[community — Civitai 31972, 2026-06-28]`; paragraph presenting the 5–50× LR gap against the vendor's 2e-5 `[contested]` · civitai.com/articles/31972
- `lora-training.md` · §7, §10 · style-count wording; closing paragraph on OneTrainer validation loss and the recipe making the difficulty question testable
- `characters.md` · §2 · "forks stay a footnote" → "still experiments", pointer to setup §7

## Findings

Resolved: `onetrainer-anima-support-shipped`, `anima-2.9b-lora-compat-now-answered`, `checkpoint-download-ranking-reversed-and-flawed`, `turbo-v1.1-undocumented`, `aesthetic-cfg-community-figure-exists`, `style-explorer-alive-and-grown`. Declined: none. Softened: the hint's "only trainer with genuine validation loss" is not asserted, since sd-scripts has validation loss too.

## Techniques

Added: `anima-2.9b-lora-block-key-remap` (single report, admitted because the failure is silent; marked), `anima-lora-recipe-by-type`, `sd-scripts-2.9b-block-detection`, `anima-turbo-v1.1-checkpoint`. Omitted: none.

## Watchlist

- Resolved: `anima-trainer-support`; the LoRA-compat sub-claim of `anima-community-forks`.
- Add `anima-turbo-v1.1-vs-v1.0` (figure; variant table, two-bar bullet).
- Add `anima-lora-lr-recipe-contested` (2e-5 @ rank 32 vs Civitai 31972's 1e-4 @ dim 8; `lora-training.md` §3).
- Amend `anima-community-forks`: watch PR #2418 for merge; re-check variant-selector treatment.
- Amend `anima-checkpoint-ecosystem-ranking`: same-base figures only.
- Amend `anima-turbo-vs-aesthetic-default`: CFG ~3 still unofficial; v1.1 unassessed.
- Amend the Style Explorer item: the count, not the URL, is the open question.

## Other skills

None. For the orchestrator: the corpus was already over the 16,000-word cap before this pass (17,001) and is now 17,911, SKILL.md 6,111 against the 5,500 band. Watch-class markers held at 25. A `setup-and-workflows.md` split at §8 would bring it back without losing facts.
