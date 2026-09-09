# qwen-image — integration report (2026-09-09)

37 files touched. `freshness.json` and `marketplace.json` were not edited by me (both show as modified by the registering agent; `marketplace.json` already lists `qwen-image`).

## 1. Sibling back-links (all of WRITE-REPORT §5)

- **z-image** — SKILL.md *Consistent characters* and *Mixed-model pipelines* rows; `characters.md` linked twice, and the **discrepancy fixed**: 2511 template "CFG 3" → **4.0** `[official — Comfy-Org template JSON, read 2026-09-09]`; first mentions linked in lora-training and setup.
- **krea-2** — *Consistent characters* row; new **Instruction editing** row; `lora-training.md §9` paragraph on what does not transfer (1024-native rule, shift 2.5, LoKr, GA 2, Raw/Turbo) → `qwen-image/references/lora-training.md §9`; first mentions linked in four files.
- **flux-2, sdxl** — *Consistent characters* reach-for names the adapter-free edit engine / dataset factory; `characters.md` factory mentions linked.
- **ideogram-4** — typography row: font-preserving text edits, bilingual rendering.
- **image-production-workflows** — suite-map row (edit rung, dataset factory, pixels in/out); mentions linked.
- **character-lora-training** — routing-inward row (bf16 base of the *deploy* generation, 2509/2511/2512 LoRAs incompatible, plain-name trigger); no-training row leads with Edit-2511; 60/30/10 vs one-third noted.
- **wan-2-2** — *Locking the still first* adds `qwen-image` and the Wan 2.1 VAE kinship.
- **comfyui-on-runpod** — volume sizing: ~30 GB fp8 set per Edit generation; training adds the 40.9 GB bf16 DiT + 16.6 GB encoder.
- **anima, minimax-h3, scail-2** — first mentions linked.

Skipped `nsfw-training.md` (mention inside a marker). Declined Ashen3's photo/photorealistic rule for krea-2: no URL in the harvest.

## 2. Atlas

`SKILL.md`: "not yet covered" row removed, suite-map row added; identity re-ranked **qwen-image → flux-2 → sdxl → krea-2**, face-adapter caveat, `[contested]` for the missing likeness head-to-head; 1 MP-downscale trap; typography second; licence tie with Z-Image (open through 2512/2511, 2.0/3.0 hosted-only); *Pick your job* row; Playbook A stack and install command; contested list; closing paragraph; "Facts dated 2026-09-09" kept. Census **1,637 / 273** with `nsfw=true`; 1,162 / 192 excluded NSFW. `model-rankings.md`: §3, §3.2, §4.5 (the census script does not pass `nsfw=true`, so other rows are floors — `[flagged — method matters here]`), §5, §6, §8, §10. `ecosystem-map.md`: §6.1 row removed; link example → `../bernini-r/`. `adult-work.md`: row linked; 25.8% / 31% re-measure noted. `installing-skills.md`: no-bundle list, Playbook A, a Qwen bundle row. `playbooks.md`: edit step linked.

## 3. README

Row after `z-image`, "Qwen-Image family (Alibaba Qwen)", 42-word cell.

## 4. Size

`SKILL.md` **6,306 → 6,022 raw** (348 → 314 lines); census-equivalent **~5,900 → 5,563**. Moved into references: stock-settings table (setup §1), file-layout table (added to §1), VRAM table (§2.5), diffusers snippet (§3); six paragraphs and the reference-files table tightened. No marker removed. **Still 63 words (~1%) over 5,500**; share 29.5% of 20,419. §5.2 grounds: more task modes than the norm, and the Edit bypass no template exposes.

## 5. Checks

42 files: all `](../` links resolve; every touched `SKILL.md` frontmatter parses and matches HEAD; atlas hint present; ten `§` deep-links resolve.

## 6. Left

Freshness registration (other agent). Anima's suite table unchanged (not named). Ashen3 needs its URL. Re-run the census with `nsfw=true` at the atlas's next check.
