# character-lora-training — write report, 2026-09-09

## Edits

- `SKILL.md` · description · adds "what resolution to render or source them at" (286 words).
- `SKILL.md` · boundary table · krea-2 gains "sources inside the 1K band"; minimax-h3 gains "rank 16 only — 32 collapses" `[live-use — h3-v3]`.
- `SKILL.md` · The one rule · "constants bind — and so do majorities and absences" (Ciara red-hair proof, 2026-09-09); trigger rewritten as per-model (BFL official vs promptdexter vs lab `z<name>`; trigger-redundancy A/B 2026-08-31).
- `SKILL.md` · The dataset · rewritten: count-not-the-lever (three arms + krea2-v2), starved-axes audit (2026-08-30), identity ratio 0.33 `[community — neonkisu]` with the lab's necessary-not-sufficient caveat and per-face-scale, crops-as-duplicates (krea2-v12), the resolution rule (Ciara four-cell sweep, 2026-09-08) with the three-resolutions split, step lever and wall test, the wrong turn named, synthetic points 14% / 64% (arXiv 2407.17493). VNCCS and video turnaround collapsed to pointers.
- `SKILL.md` · Hyperparameters · steps contested (BFL size-independent vs lab ~90–170/img); rank ceiling model-specific; caption-dropout row; adamw8bit/BF16 single report marked Z-Image-specific.
- `SKILL.md` · Evaluating · rung-by-probe, lower-rung tie-break, source-medium bake-in (krea2-v11), deploy checkpoint × resolution with strength-0 and no-trigger controls (Ciara krea2-v3), pairs/margin/fatigue, metric-triages-never-admits, FaceAnalysis dormant, MaSC figure.
- `SKILL.md` · Failure table · six rows (scale skin, background grain, late-rung crunch, trait bound to trigger, crop framing, face-scale). Adult · VLM carve-out. Pre-flight · band/steps, frozen dataset version, one variable per arm. Two-bar · `[live-use]` bar added, five contested bullets, dated 2026-09-09.
- `references/dataset-and-captioning.md` · rewritten with new **§3 Resolution**; §4–6 renumbered, internal links updated (only inbound external `§` link is playbooks → §2, unchanged).
- `references/evaluation-and-tooling.md` · §1 OneTrainer speed, ai-toolkit PRs, H3 sample-pass OOM; §2 A–F ladder; §3 tie-break, pairs/margins/fatigue, regression checklist; §4 probe design rules + control probes; §5 FaceFilter, leave-one-out calibration, blind spots, MaSC/DSH-Bench.
- `references/nsfw-training.md` · §1 VLM carve-out; §2 NoobAI Eps; §5 stills-trained H3 LoRA holds identity in motion (Ciara h3-v1).
- `references/publishing-and-likeness.md` · §2 penalty footnote (OMB freeze); legal table (UK 2026-02-06, EU AI Act, 45+ states, NO FAKES).

## Findings

Resolved: `encoder-abliteration-vlm-exception`, `ncii-legal-landscape-understated`, `take-it-down-penalty-inflation-frozen`, `sdxl-nsfw-finetune-eps-vs-vpred`. Declined: none.

## Techniques

Added: `onetrainer-int8-default-speed`, `ai-toolkit-2026-feature-drip`, `comfyui-captionthis-multi-vlm`. Omitted: `lora-squared-adaptive-rank` (single-report paper, no trainer support); `musubi-tuner-gui-0.5.0`, `sd-scripts-anima-lumina-support` (neither trainer's coverage is named here).

## Citation fix

arXiv **2407.17493** is ReDiFine (Yoon et al.); **2311.12202** is Bohacek & Farid. The old marker paired them wrongly — fixed, both cited. The 5–10% figure is in 2407.17493's body per the harvest, not its abstract; not verified further.

## Watchlist

Add (JSON): `encoder-abliteration-vlm-exception`, `ncii-legal-instruments-eu-uk-state`. Add (new): `steps-per-image`, `caption-dropout-and-evenness`, `trigger-token-llm-encoder`, `synthetic-share-ceiling` (krea2-v16 prepared, not launched), `dataset-size-knee`, `face-metric-tooling`. Amend (JSON): `sdxl-nsfw-finetune-landscape`, `take-it-down-act`. Resolved: none.

## Deviations to flag

- **Word bands.** SKILL.md 7,281 (band 2,000–3,200); corpus 27,768 (band 5,000–10,000); was 5,143 / 17,436 before. The user asked for these sections to be the suite's best. Recommend a §7 entry, or splitting `dataset-and-captioning.md` (8,241) next pass.
- **Watch-class markers: 32 vs ≤24 cap** (1.15/1k). Body duplicates removed; the rest are distinct disputes. Recommend merging dropout + evenness + trigger into one watchlist entry.
- **`live-use` is a seventh tier token**, not in STANDARD §6.2. Used per instruction; the freshness grep will miss it until STANDARD adds it.
- Readability: all files under 15 after a prose pass (median 6.0). Density 6.6/1k, no nested markers, no broken links.

## Other skills needing matching edits

- `krea-2/references/lora-training.md` §2c/§8: 1024-native sources vs bucket, 8–12 steps, wall wording, evaluate on every deploy checkpoint × resolution, caption dropout contested.
- `minimax-h3/references/lora-training.md`: "Still open" stills-in-motion bullet is now answered; r32 collapse; resolution ladder — this skill asserts all three.
- `z-image/references/lora-training.md`: carry or refute the adamw8bit/BF16 report.
- `STANDARD.md` §6.2: add the `live-use` tier.
