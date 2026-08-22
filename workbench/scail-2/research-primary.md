# SCAIL-2 — primary-source research (2026-08-22)

Scope note up front: **the primary record is not thin — it is unusually good** for a
model this new. zai-org ships a real paper, two full inference branches, training code,
an official ComfyUI docs tutorial, and an explicit acknowledgements section that answers
the lineage question directly. What's thin is *independent verification of the specific
community craft claims* (first-frame editing, multi-person glow) — those are absent from
every official source read below, not because the record is sparse but because the vendor
genuinely doesn't discuss them.

## Identity & lineage

**Maker:** [`zai-org`](https://github.com/zai-org) — this is **Z.ai / Zhipu AI**, the lab
behind GLM and CogVideoX. **Not Alibaba**, and not a Wan-team release.
`[official — GitHub org, HF namespace zai-org/SCAIL-2, ModelScope ZhipuAI/SCAIL-2]`

**Full name:** *SCAIL-2: Unifying Controlled Character Animation with End-to-end
In-Context Conditioning*. "SCAIL" is not glossed as an acronym anywhere in the repo,
paper, or project page — treat it as a model name, not an initialism to expand.
`[official]` Paper: arXiv 2606.10804, authors Wenhao Yan, Fengjia Guo, Zhuoyi Yang, Jie
Tang. `[official — arXiv abstract page]`

**Lineage — settled, not inferred.** The `sat-scail2` branch README states this exactly,
in its own Acknowledgements section:

> "Our implementation is built upon the foundation of [Wan 2.1](https://github.com/Wan-Video/Wan2.1)
> and the overall project architecture is inherited from [SCAIL](https://github.com/zai-org/SCAIL).
> We specially thank [Wan-Animate](https://github.com/Wan-Video/Wan2.2), [MoCha]... as
> supplement data generators besides SCAIL to make MotionPair-60K."

`[official — zai-org/SCAIL-2 README, sat-scail2 branch, "Acknowledgements" section, read verbatim]`

So: **it is a genuine Wan 2.1 architectural derivative**, not a from-scratch model and not
a thin wrapper around another vendor's API. But it is also not a simple fine-tune of a Wan
checkpoint — it has its own predecessor lineage (SCAIL / SCAIL-Preview, zai-org's own prior
model, arXiv 2512.05905, "SCAIL: Towards Studio-Grade Character Animation via In-Context
Learning of 3D-Consistent Pose Representations"), a large custom-synthesized training set
(**MotionPair-60K**, built using Wan-Animate and MoCha as data-generation tools among
others — those two are *data sources*, not architecture donors), novel conditioning
mechanisms (In-Context Mask Conditioning, Mode-Specific RoPE, "reserve driving"), and a
novel training objective (Bias-Aware DPO). `[official]`

**Two parallel codebases, same weights, different purpose:**
- `sat-scail2` branch — the original implementation in Zhipu's own SAT training framework
  (same lineage as CogVideoX). This is where training happens and where the paper's
  results were produced. `[official]`
- `wan-scail2` branch (the **default branch**) — a streamlined *inference* reimplementation
  that speaks the Wan-style checkpoint/config idiom, converting the SAT checkpoint to
  `.safetensors` via `convert.py`. This is the branch ComfyUI integration and community
  tooling builds on. `[official — GitHub API default_branch field, confirmed 2026-08-22]`

Both branches load `Wan2.1_VAE.pth` and `umt5-xxl` (Wan's T5 text encoder) directly —
reused components, not evidence of a full-weight fine-tune, but consistent with "built on
the Wan 2.1 foundation." The official ComfyUI node is literally named `WanSCAILToVideo`
`[official — docs.comfy.org/tutorials/video/zai/scail2]`, which is the tooling-level
confirmation of the same lineage.

**Verdict on the open question:** SCAIL-2 **is** a Wan 2.1-derived model — the vendor says
so themselves — but it ships as a **distinct, separately-branded, separately-licensed
product from a different lab**, with its own paper, checkpoint, training code, and
ecosystem (ComfyUI PR, GGUF quants, LoRAs, project page, community ports). It is not a
PAI-style same-org derivative like Fun or VACE.

## Licence

**Split licence, verified from two independent primary sources — flag this loudly:**

- **Code (GitHub repo):** **Apache License 2.0.** Confirmed two ways: `gh api
  repos/zai-org/SCAIL-2` reports `license.spdx_id: "Apache-2.0"`, and the `LICENSE` file
  content (fetched and base64-decoded directly) is the literal Apache 2.0 text. The
  `sat-scail2` README also states in its own License section: "This project is licensed
  under the Apache License 2.0." `[official — GitHub API + LICENSE file + README, all
  read verbatim, 2026-08-22]`
- **Weights (Hugging Face model card):** The card's YAML frontmatter reads `license: mit`.
  `[official — huggingface.co/zai-org/SCAIL-2/raw/main/README.md frontmatter, read verbatim]`

Both are permissive and both allow commercial use, so this is not a legal trap the way a
non-commercial clause would be — but it is a genuine **code/weights licence split**
(Apache-2.0 code, MIT weights), which is exactly the kind of thing the authoring spec says
to state plainly. `[contested/flagged — re-verify before publishing; it's possible the HF
card's frontmatter is simply wrong/unmaintained relative to the GitHub LICENSE file, but
both are dated the same release and neither reads as a placeholder]`

Wan 2.1 itself (the base being built on) shipped Apache 2.0 for both code and weights, same
as Wan 2.2 `[official, per the already-published wan-2-2 skill]` — so there is no upstream
licence conflict driving the split; it looks like a zai-org packaging choice.

## What it does

SCAIL-2 is a **driving-video + reference-image → video** model (task mode:
"performance transfer" / driving-video-conditioned animation, in the video-models.md
vocabulary), with two named operational modes `[official]`:

- **Animation mode** — the reference character performs the driving video's motion.
  Two sub-modes: **end-to-end driven** (the model consumes the raw driving frames
  directly — "recommended") and **pose-driven** (an SMPL pose-render of the driving
  video is used instead, which the README says performs better at 704p).
- **Replacement mode** — swaps a tracked person in existing footage for the reference
  character, keeping the original motion, framing, camera and scene. This is the job
  the community calls "the Wan Animate replacement" and the reason it's being evaluated
  against `minimax-h3`'s video-editing mode.

**Inputs required, always:** a reference image, a reference-image foreground mask, a
driving video, and a per-frame driving/control mask (or, for replacement mode, a
replacement-region mask in place of the driving mask). `[official — README "Getting
Started" / mask semantics section]` Multi-reference (additional reference images beyond
the primary one) is supported but explicitly marked experimental/unoptimized by the
vendor. `[official]`

Mask semantics are load-bearing and documented precisely: black = background should not
be visible, white = background should be visible, colour = correspondence between
character region and driving motion. The README states plainly: **"Without a correct
mask, Animation mode collapses into Replacement-mode behavior in certain inputs."**
`[official]`

Prompting: SCAIL-2 is trained on **long, detailed prompts** describing the *resulting*
video (not an instruction to the model) — for replacement, describe the replacement
character's clothing and what they interact with. A Gemini-based `prompt_enhancer.py`
helper ships in the repo for this. `[official]`

## Architecture

- **Base:** Wan 2.1 architecture foundation, 14B parameter class — the CLI invocation
  itself names the checkpoint `--model SCAIL-14B`. `[official — README usage examples]`
- **Text encoder:** umT5-xxl (Wan's encoder), shipped inside the checkpoint download.
  `[official]`
- **VAE:** Wan2.1 VAE (`Wan2.1_VAE.pth`), also bundled. `[official]`
- **Novel components on top of the Wan foundation:** In-Context Mask Conditioning and
  Mode-Specific RoPE (unify animation/replacement/pose-driven/multi-reference under one
  set of weights via mask-channel and RoPE design, rather than separate heads); Bias-Aware
  DPO (a preference-optimization LoRA that specifically fixes hand distortion and improves
  lip/eye sync — shipped as a downloadable LoRA, not baked into the base checkpoint).
  `[official]`
- **Identity/tracking component — SAM3, confirmed official, not just community claim.**
  The preprocessing submodule (`SCAIL-Pose`) generates driving masks from **SAM3** tracks
  in end-to-end mode ("the mask video is generated from SAM3 masks" — README). The
  official ComfyUI integration exposes this directly: the docs tutorial names
  `sam3_video_object` / `sam3_image_object` inputs and a `SAM3` tracking step feeding
  `SCAIL2ColoredMask`. `[official — docs.comfy.org/tutorials/video/zai/scail2, read
  2026-08-22 — upgrades the wan-2-2 skill's current `[flagged]` SAM3 claim to confirmed]`
  The README additionally notes zero-shot support for **SAM3D-Body** mesh rendering as an
  advanced control intermediate — a *different*, separate Meta model (body mesh, not the
  segmentation-tracking SAM3), used opportunistically rather than as a required component.
- **Sampling defaults** (from `generate.py --help`-equivalent flags in the README):
  40 sampling steps, flow-matching shift 3.0, CFG/guidance scale 5.0, `unipc` or `dpm++`
  solver. `[official]` A LightX2V distilled-LoRA path is documented explicitly (8 steps,
  shift 1, guidance scale 1.0), confirming the community's LightX2V/Pusa speed-LoRA
  compatibility claim from the official side. `[official]`

## Constraints (VRAM / resolution / duration)

- **Resolution:** 512p and 704p for end-to-end-driven mode; the vendor states pose-driven
  mode "performs better under 704p." Height and width must be divisible by 32 per the
  GitHub README (e.g. 704×1280); the ComfyUI docs page instead states divisible by 16 —
  **minor inconsistency between the two official sources**, worth re-verifying before
  publishing a specific number. `[official, contested between two official sources]`
- **Frame count:** training/caching examples default to `--max_frames 81` (matching Wan's
  81-frame/~5s-at-16fps convention). The official ComfyUI workflow chunks longer output in
  81-frame segments with a 76-frame stride between segments for pose offset. `[official —
  docs.comfy.org tutorial]`
- **VRAM:** not stated in any vendor document read. Community figures (not vendor-sourced):
  full fp16/fp8 checkpoint ~16 GB+; community GGUF requants run on 8–12 GB cards.
  `[community — re-verify; no official VRAM figure exists to cross-check against]`

## Where to run it

- **GitHub (canonical):** `zai-org/SCAIL-2` — default branch `wan-scail2` (inference),
  sibling branch `sat-scail2` (training, original implementation).
  `[official]`
- **Weights:** Hugging Face `zai-org/SCAIL-2`; mirrored on ModelScope as `ZhipuAI/SCAIL-2`.
  `[official]`
- **ComfyUI:** official integration merged via `Comfy-Org/ComfyUI` PR #14373 (`WanSCAILToVideo`
  node), multi-reference support added via PR #14509; an official tutorial exists at
  `docs.comfy.org/tutorials/video/zai/scail2`. `[official]`
- **Community quantisations:** `realrebelai/SCAIL-2_GGUF`, `xocialize/SCAIL-2-bf16` on HF.
  `[community — not independently re-verified beyond confirming the HF listing exists]`
- No hosted first-party API found from zai-org directly; third-party hosts (e.g. WaveSpeed)
  offer it as an API. `[community/third-party, not vendor-run]`

## Ecosystem

- **Bernini-R — separate model, different lab, established this pass:** `ByteDance/Bernini-R`
  on Hugging Face. Bernini is ByteDance's open-source video generation/editing framework —
  an MLLM-based semantic planner paired with a DiT renderer **built on Wan 2.2**
  (not Wan 2.1), Apache 2.0, released ~June 2026 (paper: arXiv 2605.22344, "Bernini: Latent
  Semantic Planning for Video Diffusion"). It does reference-guided video editing —
  character replacement, motion-preserving edits, garment swap, object add/remove — using
  a source video + reference image(s) + prompt, keeping camera/choreography from the
  source. So: **Bernini-R and SCAIL-2 are siblings in function (both are Wan-family
  reference-driven video editors) but from different labs (ByteDance vs. zai-org) and
  different Wan base versions (2.2 vs. 2.1)** — they are not the same lineage.
  `[official — HF namespace, arXiv abstract]` The community's specific claim that Bernini-R
  does outfit swap well but not face swap was not independently checked against ByteDance's
  own docs this pass — carry forward as `[community — single report; re-verify]`.
- **Predecessor:** `zai-org/SCAIL` (SCAIL-1 / SCAIL-Preview), arXiv 2512.05905 — the pose-
  representation-based prior model whose "project architecture" SCAIL-2 inherits, and
  which was itself used as one of the three data generators for MotionPair-60K.
  `[official]`
- **Named community tooling** (carried forward from the prior sweep, not independently
  re-verified this pass beyond confirming general plausibility against the HF/GitHub
  ecosystem that clearly exists around this model): `collbroGTR/comfyui-scail2-infinity`,
  `dvelm/SCAIL-2-Unlimited-Video-Low-VRAM`, a Segmentation Control / Identity Tracker
  community workflow, Wan2GP support, `Mix Studio` one-click mode. `[community — unverified
  this pass, flag for re-check]`
- Community fork/mirror repos (`Ardynai/scail-2`, `kotthoff/scail-2`) surfaced in search —
  these read as GitHub forks/mirrors of the official repo rather than distinct projects;
  not independently confirmed.

## Vendor-admitted limitations

- **Weakest at text** — this was in the community sweep, and no official document read
  this pass confirms or denies it; leave as `[community]`.
- **Mask correctness is explicitly called out as a failure mode by the vendor**: "Without a
  correct mask Animation mode collapses into Replacement-Mode behavior in certain inputs."
  This is a real, vendor-stated limitation, not community lore. `[official]`
- **Multi-reference is explicitly marked unoptimized by the vendor**: "as the model is not
  optimized for such inputs, video qualities may degrade even though additional
  information do get referenced." `[official]`
- **No vendor acknowledgment found of the multi-person "outline/glow" artefact** the
  community reports. Targeted search for this specific claim (Reddit, official docs)
  turned up nothing on-topic — it may be real and simply undocumented, or it may be a
  workflow-specific artefact from a particular community graph rather than a model
  property. Keep it tagged `[community — single-source-class claim, not vendor-confirmed]`
  rather than promoting it.

## Could not verify

- **The first-frame-editing craft claim's official status.** Multiple community sources
  (RunComfy workflow notes, GGUF workflow tutorials) independently describe exactly this
  technique — edit/generate the reference image to match the driving video's actual first
  frame, then feed the *original, unedited* driving video as the motion source — and
  frame it as the difference between mediocre and excellent results. But it appears in
  **zero** official zai-org documents (GitHub READMEs on either branch, the paper abstract,
  or the ComfyUI tutorial) read this pass. **Conclusion: this is a community workaround
  that compensates for something the mask/RoPE conditioning doesn't fully solve on its
  own — not documented vendor guidance.** State it in the skill as community craft, not
  official technique.
- **Exact multi-person "outline/glow" mechanism and vendor acknowledgment** — see above.
- **VRAM figures from any official source** — none exist to check community numbers
  against.
- **HF vs. GitHub licence mismatch** (MIT weights vs. Apache-2.0 code) — both read directly
  from primary sources, but *why* they differ is not explained anywhere; worth a follow-up
  check closer to publication in case the HF card gets corrected.
- **Bernini-R's face-swap-fails / outfit-swap-works claim** — not checked against
  ByteDance's own docs this pass.
- **Height/width divisibility (32 vs. 16)** — the two official sources disagree; re-verify
  against the current template JSON before stating a number in the skill.

## Sources

- https://github.com/zai-org/SCAIL-2 (repo root, API metadata: default branch, license spdx_id)
- https://github.com/zai-org/SCAIL-2/tree/wan-scail2 (README read in full, verbatim, via `gh api`)
- https://github.com/zai-org/SCAIL-2/tree/sat-scail2 (README read in full, verbatim, via `gh api` — contains the lineage/acknowledgements statement and the Apache-2.0 licence statement)
- https://github.com/zai-org/SCAIL-2/blob/main/LICENSE (base64-decoded directly — Apache License 2.0 text)
- https://huggingface.co/zai-org/SCAIL-2/raw/main/README.md (YAML frontmatter — `license: mit`)
- https://arxiv.org/abs/2606.10804 (SCAIL-2 paper abstract, authors)
- https://github.com/zai-org/SCAIL (SCAIL-1/SCAIL-Preview predecessor, arXiv 2512.05905)
- https://docs.comfy.org/tutorials/video/zai/scail2 (official ComfyUI tutorial — node names, SAM3 confirmation, frame/segment numbers)
- https://github.com/Comfy-Org/ComfyUI/pull/14373 and #14509 (ComfyUI integration PRs)
- https://huggingface.co/ByteDance/Bernini-R and https://arxiv.org/html/2605.22344v1 (Bernini-R identity/lineage)
- https://huggingface.co/realrebelai/SCAIL-2_GGUF, https://huggingface.co/xocialize/SCAIL-2-bf16 (community quant listings, existence confirmed only)
- Community (existence/plausibility only, not fact-verified): RunComfy, earngenix.com, stablediffusiontutorials.com workflow write-ups on the first-frame technique

## Recommendation: own skill or wan-2-2 section?

**Own skill.** The lineage question resolves to "yes, Wan 2.1-derived" — but that alone
doesn't make it a `wan-2-2` section, because the analogy the brief poses (Fun, VACE) is
the wrong one. Fun and VACE are **Alibaba's own** derivatives of **their own** model,
released under the same governance as Wan itself — that's what makes them sections of one
skill. SCAIL-2 is a **different lab's** model (zai-org/Zhipu, not Alibaba), with its own
paper, its own predecessor lineage (SCAIL-1), its own training code and framework (SAT),
its own licence text (split Apache/MIT, neither of which is "inherit Wan's licence"), its
own checkpoint namespace, and its own ComfyUI node family (`WanSCAILToVideo` is *named*
after Wan for discoverability, but it's zai-org's node, not Alibaba's). That's a
cross-organization derivative, structurally the same situation as Bernini-R (ByteDance,
built on Wan 2.2) — and nobody would suggest folding Bernini-R into `wan-2-2` either. Both
belong beside it, cross-linked, not inside it.

Practically: the model also earns its own skill on depth alone. It has a real conditioning-
class shape the suite hasn't covered (driving-video + reference-image + explicit mask
semantics, distinct from Wan's VACE/Animate path), a genuine one-rule candidate (the
first-frame-editing craft, which is *not* documented anywhere officially and needs a skill
to carry it), two operating modes with different mask contracts, and enough ecosystem
(GGUF quants, LoRAs, ComfyUI PRs, ModelScope mirror) to fill out the standard anatomy
without padding. Keep the current `wan-2-2` pointer section, correct its lineage language
from "Wan 2.1-derived, unverified" to the verdict above, and fold in the SAM3-official
upgrade — then build the real `scail-2` skill from this file.
