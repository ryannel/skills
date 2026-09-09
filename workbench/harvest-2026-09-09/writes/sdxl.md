# sdxl — write report, 2026-09-09

## Edits

| File | Section | Change | Evidence |
|---|---|---|---|
| `SKILL.md` | frontmatter `description` | Word-neutral swap (stays at 320): the "leave the SDXL family" clause now names Anima and Pony V7 (AuraFlow, not SDXL) | HF `purplesmartai/pony-v7-base` |
| `SKILL.md` | Checkpoints table | Pony V6 XL row flagged as "the last SDXL Pony", pointing at the callout | same |
| `SKILL.md` | anime-axis callouts | New blockquote parallel to the Anima one: V7 shipped 2025-10-08, ~7B AuraFlow, own LoRA pool, SimpleTuner, drops the score ladder for tag+description, team flags prompting inconsistent pending V7.1; V6 XL stays the practical pick `[official — …]` + `[flagged — re-verify]` | HF card; Civitai article 6309 |
| `SKILL.md` | suite table, Anime row | "Pony" → "Pony V6 XL"; V7 routed out | same |
| `SKILL.md` | two-bar section | Contested count 4 → 5; new "Pony V7 against Pony V6 XL" bullet `[flagged — re-verify]`; dated line → 2026-09-09 and now lists two anime-axis challengers | same |
| `SKILL.md` | Reference files table | lora-training row mentions Pony V7 → SimpleTuner routing and the Civitai on-site trainer | — |
| `references/checkpoints-and-loras.md` | §2 Juggernaut row | Dropped the stale "v9/v10/v11" hedge; v10 / "Juggernaut X" ships as separate SFW and NSFW checkpoints `[official — rundiffusion.com/juggernaut-xl, 2026-09-09]` | rundiffusion.com/juggernaut-xl |
| `references/checkpoints-and-loras.md` | §3 | New Pony V7 paragraph after the V6 bullets, same content as the SKILL.md callout, plus "check which generation before matching pool" | HF card; Civitai 6309 |
| `references/prompting-guide.md` | §7 Pony dialect | One sentence: this dialect is V6 XL's; V7 drops the score ladder, see checkpoints-and-loras §3 | HF card |
| `references/lora-training.md` | §1 base table | New Pony V7 row (not SDXL, SimpleTuner, recipes here do not apply, train on V6 until pool matures); V6 row cross-refs it; transfer paragraph notes V7 is a different architecture | HF card; Civitai 6309 |
| `references/lora-training.md` | §2 Tools | kohya sd-scripts now lists LoKr/LoHa for "SDXL/Anima" plus multi-res bucketing `[official — changelog, 2026]`; Pony V7 exception → SimpleTuner. New Civitai on-site trainer bullet (repeats=1 scale batch, flip-only aug, Prodigy always trains TE, buzz-per-step) `[community — Civitai 21257; single report; re-verify]` | github.com/kohya-ss/sd-scripts; civitai.com/articles/21257 |
| `references/lora-training.md` | §3 LyCORIS | One sentence on kohya's native LoKr/LoHa for SDXL and Anima | sd-scripts changelog |
| `references/lora-training.md` | §5 body tokens | Added "put them in identity-emphasis captions too" with `[community — neonkisu, Civitai 31467]` | civitai.com/articles/31467 |
| `references/lora-training.md` | §8 Status on SDXL | Softened: SDXL now listed supported for weight noising and depth anchoring, generic sigma 0.01–0.017 only, no SDXL-tuned recipe; 0.0125 was not established on SDXL. Kept `[flagged — re-verify]` | github.com/BuffaloBuffaloBuffaloBuffalo/ai-toolkit-perceptual |
| `references/lora-training.md` | §11 | "Pony" → "Pony V6 XL (V7 is not SDXL; §1)"; body-token bullet cites Civitai 31467 | — |

Checks: description 320 words (band ceiling, unchanged); readability median 7.5, no file over 15; corpus grew ~760 words, spread across references.

## Findings resolved
- `pony-v7-auraflow-not-sdxl` — callouts in SKILL.md, checkpoints-and-loras §3, lora-training §1, prompting-guide §7.
- `weight-noising-sdxl-now-listed-supported` — lora-training §8.
- `kohya-lokr-loha-sdxl-anima-native` — lora-training §2 and §3.
- `juggernaut-x-sfw-nsfw-split` — checkpoints-and-loras §2.

## Findings declined
- `anima-third-party-finetunes-emerging` — per its own fix_hint this belongs to the `anima` skill's freshness entry; the sdxl Anima row already says the pool is young and routes to `anima`.

## Techniques
- Added: `pony-v7-simpletuner-lora-path` (lora-training §1 base table, §2 Tools).
- Added, marked single report: `civitai-onsite-trainer-as-alternative` (lora-training §2). Fills the no-local-GPU gap; the skill already referenced this trainer in §5's prepend/append note.
- Citation refresh only: `identity-ratio-companion-article-body-tokens` (lora-training §5, §11). No new mechanism.

## Watchlist recommendations
- Add `pony-v7-non-sdxl-successor` as drafted in the freshness JSON. I marked it `[flagged — re-verify]` in-text to parallel the Anima callout; if the orchestrator prefers `type: contested`, the marker still greps.
- Amend `weight-noising-depth-anchoring` — claim now reads "SDXL supported for both, generic sigma only"; check asks for an SDXL-specific sigma/config.
- Amend `trainer-status` — note kohya's SDXL/Anima LoKr/LoHa convergence; check whether OneTrainer / ai-toolkit matched it.
- Amend `finetune-versions` — Juggernaut now carries an SFW/NSFW split, not a version pin; check whether RealVisXL "v5 current line" still holds.
- Amend `anima-as-illustrious-challenger` — the check should now say the anime axis has two non-SDXL challengers.
- Nothing resolved.

## Other skills
- `anima`: its "PonyV7-derived score_9 … score_1 ladder" line (SKILL.md ~L154) should be read against this pass's claim that V7 dropped V6's `score_9, score_8_up` ladder. Both can be true (V7 uses single score tags, not the `_up` ladder), but the anima writer should confirm wording so the two skills do not appear to contradict.
- `generative-media-atlas`: anime rows (~L214, L253) say "Pony" generically; consider "Pony V6 XL" and a note that V7 is AuraFlow.
- `character-lora-training`: the Pony 67% NSFW census row is V6-era; no edit needed unless the census is rerun.
