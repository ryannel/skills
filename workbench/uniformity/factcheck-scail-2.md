# Adversarial fact-check — `skills/generative-media/scail-2/`

Checked 2026-08-22 against live primary sources: arXiv abs/HTML (v2 and v3), `raw.githubusercontent.com` (both branches), `huggingface.co/api/models/zai-org/SCAIL-2`, the HF card raw markdown, `docs.comfy.org/tutorials/video/zai/scail2`, and the raw `.diff` of Comfy-Org/ComfyUI PRs #14373 and #14509.

## Verdict

**MATERIAL ERRORS.** The lineage is right — the three-level statement (full fine-tune of `Wan2.1-14B-I2V` weights / modified Wan DiT with 28 extra in-context channels + Mode-Specific RoPE / code from the Wan 2.1 repo) is verbatim-supported and neither overstated nor understated, and the licence split, the arXiv number, the node names, the mask semantics, the 40/5.0/3.0 and 8/1.0/1 pairs, 81 frames / 76 stride, 512p+704p, and the absence of any 480p base claim all survive. But four things do not. **(1)** The skill treats the **Relighting LoRA** as an unpromising community experiment when it is a vendor-shipped, vendor-documented official artefact (`model/relighting-lora.pt`, described in the `wan-scail2` README) whose stated purpose is exactly the "inserted character reads too bright / composited" artefact the skill tells you to fix in post instead — a wrong recommendation, not just a wrong tag. **(2)** The bolded claim that the **CLIP vision tower is "required, not optional"** is contradicted by the ComfyUI source: `WanSCAILToVideo` declares `clip_vision_output` with `optional=True`. **(3)** The **VAE filename is wrong** for the ComfyUI path the table describes, and **(4)** the **CLIP vision filename** in that same table is the SAT `.pth`, not the file ComfyUI loads. By the skill's own hard-fact bar ("a wrong filename 404s"), (3) and (4) are exactly the failure it warns about. Two of the three author-found facts hold up; the CLIP-vision one is half-true and overstated.

## Errors found

| Claim (`file:line`) | What is actually true | Source URL | Severity |
|---|---|---|---|
| `SKILL.md:178` — "a **relight** LoRA one practitioner tried and abandoned `[community — nsfwVariant; single report]`"; `references/setup-and-workflows.md:207` — same, plus "The reliable fix for lighting is post (§6.4)" | It is an **official vendor LoRA**, shipped in the weights repo and documented in the default-branch README: *"Relighting LoRA is designed for **replacement mode** and improves replacement quality by making the reference character blend more naturally into the target video with consistent lighting and shadows."* File: `model/relighting-lora.pt` (present in the HF `siblings` list). Mode-specific to Replacement, and the vendor's own answer to the "too bright / looks composited" artefact | https://raw.githubusercontent.com/zai-org/SCAIL-2/wan-scail2/README.md · https://huggingface.co/api/models/zai-org/SCAIL-2 | **Material** |
| `SKILL.md:93` — "The **CLIP vision tower is required, not optional** — … a graph missing it fails in a way that reads like a wiring error" | ComfyUI declares it optional: `io.ClipVisionOutput.Input("clip_vision_output", optional=True, tooltip=…)` in `comfy_extras/nodes_scail.py`. It *ships* with the release (`models_clip_open-clip-xlm-roberta-large-vit-huge-14-onlyvisual.pth`) and the tutorial's model table lists `clip_vision_h.safetensors`, so it is expected — but "required, not optional" is false at the node level, and the "fails like a wiring error" consequence is unsupported by any source | https://patch-diff.githubusercontent.com/raw/Comfy-Org/ComfyUI/pull/14373.diff · https://docs.comfy.org/tutorials/video/zai/scail2 | **Material** |
| `SKILL.md:87` — VAE file given as `wan_2.1_vae.safetensors` in the ComfyUI file-layout table | The official tutorial's table names **`Wan2_1_VAE_bf16.safetensors`** in `models/vae/`. (The SAT/repo artefact is `Wan2.1_VAE.pth`.) Neither is `wan_2.1_vae.safetensors` | https://docs.comfy.org/tutorials/video/zai/scail2 | **Material** |
| `SKILL.md:88` — CLIP vision row gives `…xlm-roberta-large-vit-huge-14-onlyvisual…` as the file for `models/clip_vision/` | That is the SAT-format `.pth` in the HF weights repo. ComfyUI loads **`clip_vision_h.safetensors`**. Wrong artefact for the column it sits in | https://docs.comfy.org/tutorials/video/zai/scail2 | **Material** |
| `SKILL.md:9` and `SKILL.md:279` — "v2 June 2026" | arXiv lists **v1 9 Jun 2026, last revised v3 5 Aug 2026**. v3 rewords §4.1: *"adapted from the Wan2.1-14B-I2V backbone"*, *"fully fine-tune the backbone for 3,500 steps with a batch size of 128 and a learning rate of 10−5"*, and states the channel count as *"4(K+1) channels"* with K=6 (=28) rather than *"28 additional channels are stacked to the model"*. Substance unchanged; the skill's verbatim quote is v2-only and the version label is stale | https://arxiv.org/abs/2606.10804 · https://arxiv.org/html/2606.10804v3 | Minor |
| `SKILL.md:258` — Bernini-R "built on Wan **2.2**, Apache 2.0, arXiv 2605.22344 `[official — HF namespace, arXiv abstract]`" | The **facts are right** (HF card: *"Wan2.2 base — Wan-AI/Wan2.2-T2V-A14B-Diffusers … Supplies the VAE, UMT5 text encoder, tokenizer, and the transformer architecture/base weights"*; *"Apache License 2.0. See LICENSE."*; publisher ByteDance) but the **citation is wrong**: the arXiv 2605.22344 abstract ("Bernini: Latent Semantic Planning for Video Diffusion", Liu, Chen, Li et al.) mentions neither ByteDance, nor Wan, nor a licence | https://huggingface.co/ByteDance/Bernini-R · https://arxiv.org/abs/2605.22344 | Minor |
| `references/setup-and-workflows.md:24` — "The nodes ship in `comfy_extras/nodes_scail.py`: `WanSCAILToVideo`, `SCAIL2ColoredMask`, **`SCAILExtension`**…" | `SCAILExtension` is not a node. It is the registrar: `class SCAILExtension(ComfyExtension):` whose `get_node_list()` returns exactly `[WanSCAILToVideo, SCAIL2ColoredMask]` | https://patch-diff.githubusercontent.com/raw/Comfy-Org/ComfyUI/pull/14373.diff | Minor |
| `SKILL.md:114` / `setup-and-workflows.md:46` — divisibility "contested between two official sources": README says 32, ComfyUI docs say 16 | Genuinely contested — but it is **two official sources against one**, not one against one. The **HF model card also says 32**: *"H and W must both be divisible by 32 (e.g. 704×1280)"*, matching the README's *"H and W should be both divisible by 32 (e.g. 704*1280) if using other resolutions."* ComfyUI docs: *"Must be divisible by 16."* The skill's advice (use 32) is correct | https://huggingface.co/zai-org/SCAIL-2/raw/main/README.md · https://raw.githubusercontent.com/zai-org/SCAIL-2/wan-scail2/README.md · https://docs.comfy.org/tutorials/video/zai/scail2 | Minor |
| `SKILL.md:21` — "**no primary source names a 480P or 720P base variant** — ignore the `480p` tag community workflows carry" | True of the *base variant*. But the "480p" tag does not originate in community sloppiness: the **official ComfyUI tutorial's own recommended speed LoRA** is `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors`. The dismissal overshoots; the tag traces to first-party tooling | https://docs.comfy.org/tutorials/video/zai/scail2 | Minor |
| `SKILL.md:89` / `setup-and-workflows.md:34` — "SAM3 tracking weights" | The tutorial names **`sam3.1_multiplex_fp16.safetensors`** (SAM **3.1**) under `models/checkpoints/` | https://docs.comfy.org/tutorials/video/zai/scail2 | Trivial |

## Claims absent from all research

The three the author reported as new finds are all in fact present in `verification-lineage.md` (lines 21, 40, 48) — so none is a bare invention. Verified independently anyway:

| Claim | Determination |
|---|---|
| Checkpoint filename `wan2.1_14B_SCAIL_2_fp16.safetensors` (`SKILL.md:85`) | **CHECKS OUT.** In `verification-lineage.md:21` and confirmed live on the official tutorial's model table under `models/diffusion_models/` |
| A Wan 2.1 I2V CLIP vision tower is involved (`SKILL.md:9,88`) | **CHECKS OUT as to existence.** HF `siblings` contains `models_clip_open-clip-xlm-roberta-large-vit-huge-14-onlyvisual.pth`; the ComfyUI tutorial lists `clip_vision_h.safetensors` under `models/clip_vision/`. **The added word "required" does NOT check out** — see Errors |
| HF card has no `base_model:` field and no Wan licence passthrough (`SKILL.md:273`) | **CHECKS OUT.** HF API `cardData` is exactly `{"license":"mit","pipeline_tag":"image-to-video","tags":[…],"library_name":"scail-2"}` — no `base_model`. `tags` carry `license:mit` and `arxiv:2606.10804` only, no `base_model:` tag. The card's prose never names Wan 2.1 as the base |
| VAE filename `wan_2.1_vae.safetensors` (`SKILL.md:87`) | **Absent from all three research files, and FALSE.** See Errors |
| Relighting LoRA as a community dead end (`SKILL.md:178`) | **Absent from all three research files, and FALSE** — it is official. See Errors |
| `SCAILExtension` in the node list (`setup:24`) | Present in `verification-lineage.md:26` as a name in the diff, but mis-classified as a node in the skill |
| "unipc or dpm++" solver (`SKILL.md:108`) | Supported by `research-primary.md:147`. My README fetch surfaced only `unipc`; `dpm++` **not independently re-confirmed** |
| `--model SCAIL-14B`, `--max_frames 81`, `prompt_enhancer.py` (`setup:223`) | **CHECK OUT** — all three confirmed verbatim in the `wan-scail2` README |
| Kijai as author of PR #14509 (`SKILL.md:34`) | **CHECKS OUT.** PR #14509 `user.login: "kijai"`, "feat: SCAIL-2 multireference (CORE-310)", merged 17 Jun 2026 |

## Markers

**Correctly marked:**
- `[contested]` on divisibility 32 vs 16 — the dispute is **real and live today**, verified in three sources this pass. Only the tally is understated (2:1, not 1:1).
- `[flagged — re-verify]` on the multi-person outline/glow, the 720p ceiling, Wan 2.1 LoRA transfer, and Mix Studio — all correctly unresolved.
- `[community]` on the first-frame rule — confirmed absent from the paper, both READMEs, the HF card and the ComfyUI tutorial.
- `[official]` on mask semantics, the mode-collapse warning, the multi-reference degradation sentence, 40/5.0/3.0/`unipc`/81, and the LightX2V 8/1/1.0 triple — all verbatim-confirmed.

**Mis-marked, understating official status:**
- **Relighting LoRA — marked `[community — nsfwVariant; single report]`, is `[official]`.** The most consequential marker error in the skill: it demotes vendor-shipped tooling to community rumour and then recommends against it.

**Mis-marked, stated flatly but actually contradicted:**
- **"CLIP vision tower is required, not optional" `[official]`** — the ComfyUI node schema says `optional=True`. This should be stated as "ships with the release and the official template loads it; the node input is declared optional."
- **The VAE and CLIP-vision filenames** in the `SKILL.md:83-91` table carry no marker at all but sit under a `[flagged — re-verify]` note that applies only to "repack filenames beyond the core one". Both are wrong; the flag does not cover them.

**Slightly over-flagged:**
- `[flagged — re-verify]` on the Apache-2.0/MIT split (`SKILL.md:271`). The split itself is triple-confirmed on the code side and double-confirmed on the weights side and was re-confirmed again today; only *why* it exists is unknown. The prose says this, but the tag reads as though the facts are shaky.

## Could not verify

- **All VRAM and timing figures** (`SKILL.md:118`, `setup:108-127`). No official baseline exists — correctly stated. Community handles and threads were not re-fetched this pass.
- **Every Reddit-attributed quote and handle** (blackmixture, nsfwVariant, spiderofmars, External_Trainer_213, ChairQueen, kayteee1995, Draco18s, Cre0na, Coach_Unable, zsnck, Dzugavili, develm0 and the rest). Out of scope for a primary-source pass; not checked.
- **The Civitai "workflows only, no LoRAs" finding** (`SKILL.md:176`) — dated 2026-08-22 in the skill; not re-run.
- **`dpm++` as an actual repo flag** — my README fetch returned only `unipc`. Present in `research-primary.md`, not re-confirmed.
- **"SCAIL-Preview" as a genuine alias for SCAIL-1** — only "SCAIL" / SCAIL-1 was confirmed.
- **ModelScope mirror `ZhipuAI/SCAIL-2`** — not fetched.
- **Community tooling**: `collbroGTR/comfyui-scail2-infinity`, `dvelm/SCAIL-2-Unlimited-Video-Low-VRAM`, Wan2GP, Mix Studio, SnapMoGen, `realrebelai/SCAIL-2_GGUF` — existence not re-checked.
- **The claim that no first-party hosted API exists** (`SKILL.md:124`) — a negative; not independently searched this pass.
