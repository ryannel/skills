# wan-2-2 — authoring intent

**First video skill in the suite.** Also the proving run for `media-model-skill`'s `references/video-models.md`, which is explicitly labelled derived-not-proven and asks the first video skill to feed corrections back.

## Why Wan 2.2 first

- Most versatile open-weights video model as of 2026-08; deepest ecosystem (VACE, LoRA tooling, quants).
- **Same lab as `z-image`** (Alibaba Tongyi) — natural sibling, and the cross-modality link (lock a still → drive I2V) is the suite-level payoff that justified putting image and video in one marketplace.
- Apache 2.0 (verify per-variant), so no licence-split landmine to navigate on the first video skill.

## Shape decision

Per `video-models.md`: **task-mode spine, size as a column within it.** Wan 2.2 tangles the two axes — a 5B TI2V hybrid doing both T2V and I2V, plus separate 14B T2V and 14B I2V. The reader arrives knowing they want to animate a still, not that they want 14B; size is a VRAM constraint resolved *after* the task.

## Traps already identified (do not write from priors)

These are in the meta-skill's own intro as the worked example of why research beats memory:

- 14B variants use `wan_2.1_vae.safetensors`; the 5B uses `wan2.2_vae.safetensors`. A VAE-family split *inside one release*.
- The 14B latent node is `EmptyHunyuanLatentVideo` — borrowed from a different model family entirely. Not guessable.

## The MoE consequence — the likely one-rule

The 14B is a high-noise/low-noise expert split (14B active / 27B total), loaded through two separate `Load Diffusion Model` nodes. Propagates to: **two LoRAs per concept**, per-expert sampler settings, two `LoraLoaderModelOnly` → `ModelSamplingSD3` → `KSamplerAdvanced` chains. A reader assuming one model gets something that half-works and looks subtly wrong — the worst failure, because it doesn't error.

Candidate one-rules to test (from `video-models.md`'s three shapes):
1. "It is two models, not one" — the MoE consequence
2. "Describe the action, not the scene" — the generic video rule
3. "The still does the heavy lifting" — I2V-dominant framing

Pick whichever actually dominates output quality; don't force it.

## Open questions for research

- Is two-LoRA training consensus or contested? Can you get away with low-noise only?
- VACE status for 2.2 specifically (2.1 definitely had it).
- Lightning/lightx2v distill LoRAs — heavily used in practice; do you need one per expert?
- Does Wan still ship a default Chinese negative prompt as 2.1 did?
- Native fps and the 81-frame ≈ 5s @ 16fps anchor — confirm from template JSON, not blog prose.

## Coverage requirements

All three pillars, temporal mechanics per `video-models.md`. Plus the video-only anatomy: task-mode selector, length×fps×resolution budget, motion/camera control, audio axis (Wan has none → route elsewhere), post chain with **restore-before-interpolate**.

Bidirectional cross-links owed: `z-image`, `krea-2`, `flux-2`, `sdxl`, `image-production-workflows` all need a "driving a still into video" pointer added back.
