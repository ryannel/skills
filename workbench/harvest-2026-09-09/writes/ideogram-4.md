# ideogram-4 — write report, 2026-09-09

## Edits

| File | Section | Change | Evidence |
|---|---|---|---|
| `references/lora-training.md` | intro | Dated the update; named what changed | — |
| `references/lora-training.md` | §2 trainer table | Added musubi-tuner row (`networks.lora_ideogram4`, `--validate_caption_structure`, `--blocks_to_swap` ≤33, fp8 on-the-fly dequant, PRs #966/#975/#977) and OneTrainer row (split q/k/v keys, ComfyUI-incompatible); added a "Loads in ComfyUI?" column | github.com/kohya-ss/musubi-tuner/blob/main/docs/ideogram4.md (2026-07-04); github.com/Comfy-Org/ComfyUI/issues/14477 (2026-06-14) |
| `references/lora-training.md` | §2 | Replaced "no hyperparameter guidance exists" with estylon's recipe (16/16, 2500 steps, 1e-4 adamw8bit, ckpt/250, pick an earlier checkpoint), marked `[community — estylon, Substack; single report]` and framed as one author's numbers | estylon.substack.com/p/training-an-ideogram-4-style-lora (2026-06-11) |
| `references/lora-training.md` | §3 | musubi is now the exception to "trainers do not know about JSON captions"; kept the no-comparison flag | musubi docs/ideogram4.md |
| `references/lora-training.md` | §4 | Noted the 2026-09-09 spot-check and the `types=LORA` filter; count left at 34 | civitai.com/api/v1/models?baseModels=Ideogram%204.0 |
| `references/lora-training.md` | §5 | Style bullet updated; added speed-LoRA bullet pointing at setup §4 | huggingface.co/ostris/ideogram_4_turbotime_lora |
| `references/setup-and-workflows.md` | header, §1 | Source line includes Comfy-Org listing; note that the ideogram-ai repos are diffusers files and ComfyUI uses Comfy-Org's | huggingface.co/Comfy-Org/Ideogram-4/tree/main/diffusion_models |
| `references/setup-and-workflows.md` | §4 | Replaced "VRAM & quant naming — flagged" with a three-pair quant table (fp8_scaled / nvfp4_mixed / int8_convrot 9.58 GB), explained the nf4-vs-nvfp4 non-conflict, flagged the missing comparison; split VRAM into its own subsection; added TurboTime subsection (graph change reasoned from the claim, reproduction flagged) | Comfy-Org listing; ostris HF + civitai.com/models/2711950 |
| `references/setup-and-workflows.md` | §6 | Format bullet: musubi loads, OneTrainer's `lora key not loaded`; branch bullet: TurboTime as a data point for the conditional branch | issue #14477; ostris |
| `SKILL.md` | description | Two quant sets, three trainers, OneTrainer, TurboTime; trimmed to stay in band | — |
| `SKILL.md` | intro, Per-mode, Setup & ecosystem, ComfyUI, suite table, reference rows | Quant split by runtime; TurboTime paragraph; trainer list; recipe marker; `Comfy-Org/Ideogram-4` casing | as above |
| `SKILL.md` | two-bar section | Hard-facts volatility line updated; "three months old"; craft/corpus split per the `lora-tooling` amend; contested list: nvfp4 bullet removed, LoRA-branch bullet amended, TurboTime bullet added; date line → 2026-09-09 | — |

## Findings

Resolved: `musubi-tuner-ideogram4-support`, `ideogram4-lora-hyperparameters-published`, `quant-nvfp4-filename-resolved`, `new-int8-convrot-quant-undocumented`, `onetrainer-ideogram4-comfyui-incompatible`, `civitai-lora-composition-still-style-heavy` (note added, count unchanged).

No edit needed (CLAIM HOLDS; dates refreshed via the date line): `flash-tier-still-pending`, `v3-edit-paths-inference-still-unconfirmed`, `no-control-adapters-still-holds`.

Declined: `days-old-framing-already-fixed-drop-from-watchlist` — a `freshness.json`-only change; the text was already fixed.

## Techniques

Added: `musubi-tuner-lora-ideogram4` (official), `comfy-org-int8-convrot-quant` (official), `ideogram4-turbotime-speed-lora` (community, ostris; reproduction flagged), `onetrainer-ideogram4-extension` (community, GH issue), `ideogram4-named-hyperparameter-recipe` (single-report; fills the explicit "no guidance" gap, so admitted with a single-report marker).

Omitted: none.

## Watchlist

- Resolved: `ideogram4-4bit-quant-filename` (no conflict existed; two repos, two runtimes), `days-old-framing`.
- Add: `ideogram4-int8-convrot-quant` (flag lives in setup §4 only; SKILL.md carries the claim unflagged per STANDARD §6.2.1 step 3), `ideogram4-turbotime-adoption` (flag in SKILL.md contested list + setup §4), `musubi-onetrainer-ideogram4-maturity` (no flag marker; tracked via the trainer table).
- Amend: `ideogram4-lora-trainers` and `lora-tooling` as the JSON proposes; `ideogram4-civitai-lora-composition` — re-run with `types=LORA`.

## Limits

Watch-class markers were 25 before this pass (cap 24) and are 25 after it: two resolved nvfp4 flags and one duplicate removed, two added. The one-over residual predates this pass. Description 318 words (unchanged length). Readability: all five files under 15 (SKILL.md 2.9, median 4.9).

## Other skills

- `generative-media-atlas/references/model-rankings.md` L203/225 says Ideogram 4 has **one** published character LoRA; this skill says none. Pre-existing, not from this pass — the atlas writer should reconcile.
- `character-lora-training/SKILL.md` L226 may name musubi-tuner; optional.
