# krea-2 — write report, 2026-09-09

## Edits

| File | Section | Change | Evidence |
|---|---|---|---|
| `SKILL.md` | description | Adds pose ControlNet, "recipe held across twenty-one runs", the 1024-not-768-or-2048 rule, "reticulated skin from a LoRA"; trimmed elsewhere to land at 318 words | — |
| `SKILL.md` | Setup → Quantisation | int8 paragraph: benchmark reported, not readable, adherence still `[contested]` | lilcheaty HF card (read: no benchmark on it); instasd 403 |
| `SKILL.md` | Setup → diffusers | Code comment → stable since 0.40.0, `pip install "diffusers>=0.40.0"` | pypi / newreleases 0.40.0, 2026-08-20 |
| `SKILL.md` | LoRA summary | Rewritten: recipe held across 21 runs with anchor numbers; new "one rule that cost a week" paragraph (1024-native, wall as the tell, resolution+step band check); dispute paragraph adds the popularity tilt, no same-dataset A/B; adult paragraph adds the finetune's own resolution band | `[live-use — media lab]` Ciara band sweep 09-08, krea2-v4/v5, krea2-v3; ostrisai X, buildfastwithai, musubi krea2.md |
| `SKILL.md` | Production pipelines | Colorcraft shipped; Wan swap does not fix over-band texture | github muerrilla/ComfyUI-Colorcraft; `[live-use]` 09-08 |
| `SKILL.md` | Failure modes | Three rows: grain on wall = sampling (20 steps / cfg>1); reticulated skin from over-band dataset; wall pattern printed on skin | `[live-use]` 09-07/08/09 |
| `SKILL.md` | Pre-flight | Item 10 → character strength 1.0, 1.1 = underfit; new item 12 dataset render rule | `[live-use]` |
| `SKILL.md` | Suite table, Known limitations | Structural control → depth + OpenPose, no canny/union | HF thedeoxen/Krea-2-pose-controlnet, 2026-08-04 |
| `SKILL.md` | Two-bar | Volatile list drops source-only diffusers; craft sources add muerrilla, thedeoxen; new paragraph defining `[live-use]` as one lab, not consensus; age reframed to eleven weeks; int8, doctrine and resolution bullets updated; two new `[contested]` bullets (deploy route; synthetic share); `Facts dated 2026-09-09` line | — |
| `SKILL.md` | Reference files | lora-training row updated | — |
| `lora-training.md` | whole file | Rewritten. §1 tilt + no-A/B `[contested]`, per-model trigger note; §2 "still experimental"; §2b finetune band; §2c multi-res livelier `[contested]`, trainers-never-upscale; §3 LoKr technique; **§3a** the 21-run recipe table, hardware ($2.30/5090, 4500, A100 no fp8), samples off; **§3b new** rank A/B, rung per dataset, lower-rung tie-break, source medium bakes in; §4 Krea's own trainer; §5 trimmed to Krea-specific (trigger A/B, signage bleed, hair vs age/freckles); §6 three-recipe table, count-not-lever, synthetic works; §8 deploy checkpoint×resolution, strength-0 control, cfg>1 grain; **§9 new** three-resolutions table, 1024-native rule, mechanism, Amy's wrong turn named, 12-not-20 steps, cfg 1.0, wall texture, LoRA 0.0, synthetic share `[contested]`; **§10 new** strength 1.0, body per checkpoint, identity not portable, five prompting rules, repaint stack | media-lab-docs R11/R14/R16/R17/R19/R20/R21/R24–R29/R32/R41/R42; transcripts-ciara §1–3, 12–15, Numbers; transcripts-amy 7, 11, 13–18, wrong turns 1–2; lora-dataset-research §3–5 |
| `setup-and-workflows.md` | intro, §2, §4, §5a, §5c, §6, **§7d new** | Re-check date; quant benchmark softened `[re-verify]`+`[contested]`; diffusers 0.40; Wan swap limit; Colorcraft shipped; LoRA strength 1.0 vs 0.8, eleven weeks; Turbo img2img ladder 0.4/0.55/0.7 | as above; Civitai 2768351, kombitz 2026-07-19 |
| `characters.md` | intro, §1, §2, §3, §4, §6 | Age reframed; ControlNet row + edit-workflow mention; pipeline steps 2–6 rewritten (synthetic-from-base route, coverage → sibling, deploy 1.0); 13–32 band; RunComfy workflow described mechanically; single-pass vs detailer `[contested]`; six failure rows | RunComfy page (fetched: open Turbo + `Krea2EditRebalance`/`TextEncodeKrea2`, no style refs); `[live-use]` |
| `prompting-guide.md` | §3, §7 | LoRA-render inversion (no face words, ~45 words, no realism tail); wall wording; two mistakes rows | `[live-use]` 09-05, 09-09 |
| `api-and-hosted.md` | §3 | Krea's own LoRA trainer, min 3 images | krea.ai blog 2026-05-21 |

Checks: description 318; readability median 7.9, none over 15; markers 7.6/1k, watchlist-class 23; all `§` and `../` links resolve.

## Findings resolved
`diffusers-krea2pipeline-now-stable`, `openpose-controlnet-landed`, `colorcraft-vae-node-shipped`, `lora-doctrine-ostris-trending-but-not-settled`, `two-weeks-old-framing-now-eleven-weeks-stale`.

`gguf-quant-shootout-published` — partially. The lilcheaty card carries no benchmark (only "near-lossless in testing"); instasd returned 403. I wrote "reported, not readable here" and kept adherence `[contested]`. The JSON's attribution (Merserk13 in the watchlist, lilcheaty in the finding) is unresolved.

## Findings declined
None.

## Techniques
- Added: `lokr-over-lora-for-krea2-characters` (§3), `turbo-img2img-denoise-ladder` (setup §7d), `reference-image-edit-comfyui-workflow` (characters §1/§3 — as `single report`; the JSON's "style-reference conditioning" mechanism was wrong, the fetched page shows Rebalance-class nodes on open Turbo).
- Cited directly: `musubi-krea2-doc-flag-names-confirmed` (already covered).

## Watchlist recommendations
- Resolve `diffusers-source-only`, `krea2-vae-options`.
- Add `gguf-quant-shootout-followup` and `pose-controlnet-maturation` as drafted; amend `lora-doctrine` and `two-weeks-old-framing` as drafted.
- Add `krea2-deploy-route` (contested: detailer-stage 0.8 vs single pass 1.0) — characters §4, SKILL two-bar.
- Add `krea2-synthetic-share` (contested: 12–14% fine, 64% failed, ≤40% run) — lora-training §9.
- Add `krea2-1024-native-replication` (ecosystem-gap: one lab's rule, no outside replication) — lora-training §9.
- Add `krea2-caption-dropout` (contested 0.05 vs 0.3) — lora-training §3a.

## Other skills / orchestrator
- **Size:** prose grew 12,892 → 17,878 words; `lora-training.md` is 7,395, over §5's 3,500 and the 16,000 corpus ceiling. The added material is what the prompt asked for. Recommend splitting §9–§10 into `references/synthetic-datasets-and-deployment.md` in a follow-up, since the brief forbids new files this pass.
- **Marker tier:** `[live-use — …]` is a seventh tier token not in STANDARD §6.2's closed set of six; §6.2 needs a line registering it (34 instances here).
- `character-lora-training`: this skill now links `dataset-and-captioning.md` for coverage/ratio/crops/synthetic rules and `evaluation-and-tooling.md` for blind pairs, probe design and triage — confirm those sections exist after its rewrite. Its arXiv ID for the recursion study (2311.12202 vs 2407.17493) is flagged in lora-dataset-research §6.
- `minimax-h3`: lora-training §3b states "rank 32 collapses H3 under AI-Toolkit; r16 only" — should match that skill's wording.
- `generative-media-atlas`: control ranking for Krea 2 should read "depth + pose CN".
