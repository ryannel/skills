# Brief: an `ltx-2-5` skill

**Status:** not started. Highest-priority gap found in the 2026-08-22 community sweep
(`workbench/research-2026-08-22/FINDINGS.md` §2).

## Why this is the top gap

The suite covers three video models — `wan-2-2`, `minimax-h3`, and video craft inside
`image-production-workflows` — and **zero** of the LTX line, which is one of the two
poles of open video generation as of August 2026. Every video skill in the suite
already *references* LTX-2.5 as a comparison point, and `minimax-h3` explicitly flags
that its LTX licence claim is unverified because nobody read it. That is a hole the
suite is already leaning on.

The trigger to write it now: **LTX-2.5 shipped ~2026-08-12** with open weights on
Hugging Face, pipelines on GitHub and workflows in `Lightricks/ComfyUI-LTXVideo`.

## What the sweep established (community + vendor blog — all needs primary verification)

**LTX-2.5, vendor's own framing:**
- **Native multishot** — one generation produces multiple connected shots holding
  character identity, environment, lighting, voice and style across cuts. This is the
  headline and it is a different capability shape from H3's context chaining.
- **Diffusion Fidelity Rendering** — compute allocated by scene complexity rather than
  one fixed compression rate for the whole clip.
- A markedly better **distilled** model, aimed at consumer GPUs.
- Native audio (both 2.3 and 2.5 encode audio and video jointly — the ReDetail author's
  "silent clips fail" constraint is downstream of this).

**Community reality check:** 0.5 MP / 10 s in **180 s on a 3060**. Still shows the
"missed a step" walk/run artefact that Wan 2.2 also had.

**LTX 2.3 is not obsolete** and carries the mature control ecosystem — a skill that
covers only 2.5 will be wrong for most existing workflows:
- `Lightricks/LTX-2.3-22b-IC-LoRA-Clean-Plate` — removes all people and vehicles from a
  clip leaving a matched empty plate. Run with `LTX-2.3_V2V_ICLoRA_Single_Stage_Distilled.json`.
- `Cseti/LTX2.3-22B_IC-LoRA-CrossView-Warp_v2` + `cseti007/ComfyUI-CrossViewWarp` —
  change the camera position or orbit path of an existing clip, defined on an orbit
  sphere rather than by prompt text. v2 shipped 2026-08-20.
- Union Control IC-LoRA (`LTX-2.5_ICLoRA_Union_Control_Distilled.json`) is the current
  community pick for V2V on 2.5.
- DiffusionGemma Prompt Builder is mentioned as improving 2.3 motion transfer.

**ReDetail** (`Bambushu/redetail`) — the LTX-2.5 upscaler as a generative video
re-render, already used on MiniMax H3 output. Constraints recorded in
[`image-production-workflows`](../../skills/generative-media/image-production-workflows/SKILL.md).

**Civitai** now carries `LTXV 2.5`, `LTXV 2.3` and `LTXV2` base-model tags. Notable
artefacts: `REDGraft LTX 2.5 老同学 Fast 2K` (~148k downloads), several INT8/low-VRAM
all-in-one workflows, a "22B cut down to fit your card" checkpoint, and a Mac GGUF build.

## The thing that must be resolved first

**The licence.** `minimax-h3` currently says LTX-2.5's licence is *gated behind a
contact-information agreement and was not read*, and refuses to treat the comparison as
licence clearance. This skill cannot ship until someone reads it. If it turns out to be
restrictive, that changes the recommendation everywhere LTX is named — and the
licence-first structure of the `minimax-h3` skill is the model to copy.

## Authoring notes

- Follow `.agents/skills/media-model-skill` — video modality.
- The defining trait to build the skill around is probably **native multishot**: one
  generation, several cuts, identity held across them. That is the thing no other open
  model in the suite does, and everything else (Diffusion Fidelity Rendering, the
  distilled model, the IC-LoRA control family) organises under "how you direct it".
- The **IC-LoRA** pattern is genuinely distinctive and deserves the conditioning-class
  treatment: it is neither a ControlNet nor a style LoRA, and Lightricks ships them
  first-party. Clean Plate and CrossView-Warp are the two worked examples.
- Cross-links to write: `wan-2-2` (the other Apache-ish open video option and its control
  rig), `minimax-h3` (audio-native comparison, and the ReDetail handoff), and
  `image-production-workflows` (which already documents ReDetail's constraints).
- 2.3 vs 2.5 should be a **variant selector** at the top, not a history section — people
  are running both.
