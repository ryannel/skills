# SCAIL-2 lineage — adversarial verification

Verified 2026-08-22 against primary sources (GitHub raw, arXiv HTML, HF API, ComfyUI PR diffs).

## Verdict

**PARTIALLY REFUTED — but the true lineage is *stronger* than the research agent claimed, and its supporting quote was misattributed and misleadingly elided.**

The README sentence does exist, but **not in the `sat-scail2` README** as reported — it is in the `wan-scail2` (default) / `master` branch README, under **Acknowledgements**. The agent's ellipsis (`"...built upon the foundation of Wan 2.1... architecture inherited from [SCAIL]"`) collapses two clauses and inverts their sense: the full sentence attaches *architecture* to **SCAIL**, not to Wan 2.1. So the README does **not** confirm "Wan 2.1 architectural derivative"; read alone it supports only "built on the Wan 2.1 **codebase**". Worse, this lab uses "overall project architecture" to mean *repo/framework*, not neural architecture — proven by the parallel sentence in SCAIL-1's README, which says the architecture is "built using **SAT**" (a training framework). However, the **paper** — which outranks the README — states plainly that SCAIL-2 is a **full fine-tune of the Wan2.1-14B-I2V weights**. That is a weights-level derivative, stronger than architecture. The second agent's "still unsourced" is therefore also refuted. The `480p` detail is **not** supported by any primary source.

## Assertion-by-assertion

| Assertion | Verdict | Verbatim quote | Source URL |
|---|---|---|---|
| Made by zai-org (Z.ai / Zhipu AI), not Alibaba | **CONFIRMED** | Repo owner `login: "zai-org"`; paper author note: "Work done during internship at Z.ai."; "Corresponding author: jietang@tsinghua.edu.cn" | https://api.github.com/repos/zai-org/SCAIL-2 · https://arxiv.org/html/2606.10804v2 |
| The quote is in the **`sat-scail2`** README | **REFUTED** | The `sat-scail2` README instead reads: "Built on [Wan 2.1](https://github.com/Wan-Video/Wan2.1); project architecture inherited from [SCAIL](https://github.com/zai-org/SCAIL)." | https://raw.githubusercontent.com/zai-org/SCAIL-2/sat-scail2/README.md |
| `sat-scail2` is a separate repo | **REFUTED** | `zai-org/sat-scail2` → HTTP 404. Branches are exactly: `sat-scail2`, `wan-scail2`. It is a **branch**. | https://api.github.com/repos/zai-org/SCAIL-2/branches |
| The sentence exists (somewhere) | **CONFIRMED (relocated)** | "Our implementation is built upon the foundation of [Wan 2.1](https://github.com/Wan-Video/Wan2.1) and the overall project architecture is inherited from [SCAIL](https://github.com/zai-org/SCAIL)." — under `## ✨ Acknowledgements` | https://raw.githubusercontent.com/zai-org/SCAIL-2/wan-scail2/README.md (L496) |
| README confirms **Wan 2.1 architectural** derivative | **REFUTED** | The architecture clause attaches to SCAIL. Compare SCAIL-1: "Our implementation is built upon the foundation of [Wan 2.1](...) and the overall project architecture is built using [SAT](https://github.com/THUDM/SwissArmyTransformer)." — "project architecture" = framework/repo, not network | https://raw.githubusercontent.com/zai-org/SCAIL/master/README.md (L208) |
| Wan 2.1 (not 2.2) is the base | **CONFIRMED — at weights level** | "We train the model on a 14B I2V Backbone Wan2.1-14B-I2V: during the pretraining stage, we full-finetune the backbone for 3,500 steps with a batch size of 128 at a learning rate of 1e-5; after convergence, we perform DPO Post Training for another 400 steps." (§4.1) | https://arxiv.org/html/2606.10804v2 |
| Independent corroboration of Wan 2.1 | **CONFIRMED** | ComfyUI core: `class WAN21_SCAIL2(WAN21_T2V):` with `unet_config = {"image_model": "wan2.1", "model_type": "scail2"}`; checkpoint filename `wan2.1_14B_SCAIL_2_fp16.safetensors`; docs: "SCAIL-2 is an end-to-end character animation model built on Wan2.1." | https://github.com/Comfy-Org/ComfyUI/pull/14373/files · https://docs.comfy.org/tutorials/video/zai/scail2 |
| Base is **480p** (community workflow tag) | **UNSUPPORTED** | Paper says only "Wan2.1-14B-I2V" — strings `480P`/`720P`/`480p`/`720p` appear **zero** times. Model card: "End-to-end driving supports both 512p and 704p; pose-driven and replacement performs better at 704p" | https://arxiv.org/html/2606.10804v2 · https://huggingface.co/zai-org/SCAIL-2/raw/main/README.md |
| Paper arXiv 2606.10804 exists | **CONFIRMED** | Title: "SCAIL-2: Unifying Controlled Character Animation with End-to-End In-Context Conditioning"; authors Yan Wenhao, Guo Fengjia, Yang Zhuoyi, Tang Jie; v2 dated 10 Jun 2026 | https://arxiv.org/abs/2606.10804 |
| Predecessor SCAIL-1 | **CONFIRMED** | "SCAIL: Towards Studio-Grade Character Animation via In-Context Learning of 3D-Consistent Pose Representations (CVPR 2026 Findings)"; "a 14B DiT" | https://api.github.com/repos/zai-org/SCAIL |
| Training framework SAT | **CONFIRMED** | "This branch holds the original **SAT-based** implementation of SCAIL-2 used to produce the results reported in the paper." | https://raw.githubusercontent.com/zai-org/SCAIL-2/sat-scail2/README.md |
| ComfyUI node `WanSCAILToVideo` | **CONFIRMED** | `comfy_extras/nodes_scail.py` (added, +321): "SCAIL / SCAIL-2 nodes: the WanSCAILToVideo conditioning node and the SAM3…"; also `SCAIL2ColoredMask`, `SCAILExtension`, `SCAIL2WanModel` | https://github.com/Comfy-Org/ComfyUI/pull/14373/files |
| SAM3 identity tracking officially documented | **CONFIRMED** | ComfyUI core: `from comfy.ldm.sam3.tracker import unpack_masks`; `SAM3TrackData = io.Custom("SAM3_TRACK_DATA")`; input tooltip "Colored per-identity SAM3 mask video…". Repo README: "the mask video is generated from SAM3 masks." Docs: "Uses native `WanSCAILToVideo`, `SCAIL2ColoredMask`, and `SAM3` tracking." | PR 14373 · https://raw.githubusercontent.com/zai-org/SCAIL-2/wan-scail2/README.md (L211) · docs.comfy.org |
| Licence split Apache 2.0 / MIT | **CONFIRMED** | See Licence section below | — |

## The precise lineage claim

Three distinct statements, all separately verified — a skill must not conflate them:

1. **Weights (strongest, from the paper).** SCAIL-2 is a **full fine-tune of the Wan2.1-14B-I2V checkpoint**. The paper: "We train the model on a 14B I2V Backbone Wan2.1-14B-I2V: during the pretraining stage, we full-finetune the backbone for 3,500 steps…". A later DPO stage freezes the backbone and trains rank-128 LoRA adapters. Consequence: it inherits Wan 2.1's motion prior, and Wan 2.1 14B LoRA shape compatibility is *plausible* but was **not** tested here — the model adds 28 extra input channels (paper: "K is set at 6, so 28 additional channels are stacked to the model"), so any LoRA touching the patch embedding will not transfer.

2. **Architecture.** Wan 2.1's DiT, **modified**: ComfyUI implements it as `SCAIL2WanModel` subclassing the Wan model, adding an additive mask stream (`patch_embedding_mask`) and Mode-Specific RoPE. It is *not* an unmodified Wan 2.1. The README's phrase "the overall project architecture is inherited from SCAIL" refers to the **repo/codebase**, not the network — read it as code lineage only.

3. **Code.** Inference/training code descends from the Wan 2.1 repo; the `sat-scail2` branch uses SAT (SwissArmyTransformer) for the paper results, the `wan-scail2` branch is the Wan-framework port used for day-to-day inference.

**Auxiliary components:** ships Wan 2.1's VAE (`Wan2.1_VAE.pth`), `umt5-xxl` text encoder, and the Wan 2.1 I2V CLIP vision tower (`models_clip_open-clip-xlm-roberta-large-vit-huge-14-onlyvisual.pth`).

**Resolution:** do *not* say "480p". Say: base is Wan2.1-14B-I2V (variant unspecified in the paper); SCAIL-2 itself was "trained with mixed resolutions and fps" and supports 512p and 704p, with pose-driven/replacement better at 704p.

## Licence

- **GitHub code — Apache 2.0.** `LICENSE` file begins "Apache License / Version 2.0, January 2004". README `## 🗝️ License`: "This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details." GitHub API: `"spdx_id": "Apache-2.0"`. Three independent confirmations.
- **Hugging Face weights — MIT.** Model card frontmatter line 2: `license: mit`. HF API `cardData`: `{"license": "mit", "pipeline_tag": "image-to-video", ...}`, tag `license:mit`.
- The split is real, not a transcription error. Note the weights card carries **no** Wan 2.1 licence passthrough and no `base_model:` field, despite the weights being a Wan2.1-14B-I2V fine-tune — a genuine ambiguity worth flagging to users rather than resolving. (Wan 2.1's own release is Apache 2.0, so the practical risk is low, but the card does not say so.)

## What I could not reach

- **arXiv PDF** — used the arXiv HTML (v1 and v2); both carry identical §4.1 text, so this is not a gap in substance.
- **ModelScope mirror** (`modelscope.cn/models/ZhipuAI/SCAIL-2`) — not fetched; the HF copy is authoritative.
- **GitHub code search API** — requires auth (401); node names were instead confirmed directly from the PR file diffs, which is stronger evidence.
- **Author institutional affiliations beyond the footnotes** — the HTML exposes "Work done during internship at Z.ai" and Tang Jie's `tsinghua.edu.cn` address, but no explicit affiliation block. Z.ai/Zhipu + Tsinghua is well supported; a formal affiliation list is not.
- **The Civitai workflow tags** cited by the community agent — not re-checked. They remain secondary evidence, and a workflow tag reports what a workflow *loads*, not what the model was *trained from*.

## Corrected statement

SCAIL-2 is Z.ai's (zai-org) end-to-end character animation model, successor to SCAIL-Preview, published as arXiv 2606.10804 (Yan, Guo, Yang, Tang; June 2026). It is a **full fine-tune of the Wan2.1-14B-I2V weights** — stated in the paper's §4.1, not inferred — with a modified Wan 2.1 DiT that stacks 28 extra in-context conditioning channels plus Mode-Specific RoPE, followed by a rank-128 LoRA DPO stage. ComfyUI corroborates it independently, registering the model as `WAN21_SCAIL2` with `image_model: "wan2.1"`. It is Wan **2.1**, not 2.2; no primary source specifies the 480P or 720P base variant, and SCAIL-2 itself supports 512p and 704p. It ships Wan 2.1's VAE, umt5-xxl, and I2V CLIP tower. Identity control uses SAM3 colored-mask tracking via the native `WanSCAILToVideo` and `SCAIL2ColoredMask` nodes. Licences differ by artefact: GitHub code Apache 2.0, Hugging Face weights MIT.
