# Brief: a `scail-2` skill (or a large `wan-2-2` section)

**Status:** not started; a pointer section was added to
[`wan-2-2`](../../skills/generative-media/wan-2-2/SKILL.md) in the 2026-08-22 pass so the
suite is not silent on it. Source: `workbench/research-2026-08-22/FINDINGS.md` §3.

## The open question, and it decides the shape

**Is SCAIL-2 its own skill, or a section of `wan-2-2`?** That turns on a fact nobody in
the sweep sourced properly: users consistently call it "Wan SCAIL-2", say it is Wan
2.1-based, run it in Wan2GP, and use LightX2V and Pusa LoRAs with it — but **no primary
source (model card, repo, paper, licence) was read.** Resolve that first:

- If it is a Wan derivative under Apache 2.0 like Fun and VACE, it is a `wan-2-2`
  section — the same treatment those got.
- If it is an independent model with its own licence and ecosystem, it needs its own
  skill, and the `wan-2-2` section becomes a pointer.

Everything below holds either way.

## Why it is worth covering at all

It has **displaced Wan Animate** in community practice for the specific job of replacing
a person in existing footage while following their motion exactly. That job is one
[`minimax-h3`](../../skills/generative-media/minimax-h3/SKILL.md) can only approximate —
H3's `[video editing]` mode re-generates the motion rather than tracking it — so the
suite currently routes a real, common request to a model it does not document.

## What the sweep established (community only)

**Capabilities.** Reference image + driving video, with **SAM3-based identity tracking**.
Reported strengths: object permanence through off-screen excursions; inventing plausible
motion absent from the driving clip (fire arcing off a fist, hair and cloth follow-through);
transparent-object physics including liquid sloshing and background refraction through
glass; 2D motion transfer and relighting. Weakest at **text**, which turns to mush.

**The load-bearing craft is upstream of the model.** Do not hand it a generic portrait —
edit the driving video's *actual first frame* into the new character (Krea 2 Identity Edit
LoRA or Flux Klein 9B) so the reference already sits in the pose and framing where the
driving clip starts. Named practitioners call this the difference between mediocre and
excellent results. This is the single most valuable thing to put in the skill's
"one rule that changes everything" slot.

**Known limitation:** in multi-person scenes, non-target people acquire an outline or glow.
The Identity Tracker's multi-character mode is the mitigation — clear `object indices`
and select characters by *point* rather than box.

**Ecosystem, all community:**
- `collbroGTR/comfyui-scail2-infinity` + the "SCAIL-2 Unlimited Length" workflow
- `dvelm/SCAIL-2-Unlimited-Video-Low-VRAM` — GGUF, chunked chaining, 8–12 GB cards
- Wan SCAIL-2 Segmentation Control workflow (External_Trainer_213) — Identity Tracker,
  "SCAIL Auto Extend" sampler with colour matching integrated, input-video interpolation
  (smoother motion, but the model "forgets" new parts of the animation faster), RMBG
  background retention, LoRA support
- Wan2GP support; `Mix Studio` (BlackMixture) exposes it as a one-click mode
- Compatible with LightX2V and Pusa speed LoRAs; fp8_scaled builds in use

**Performance datapoints:** ~2–3 min per generation on an RTX 6000 Pro; 9 s at 384p in
30 min on a 4070 Ti Super (a user's own complaint that LTX-2 does similar in 2–5 min).

**Bernini-R** is a sibling Wan-family reference-video-to-video model in the same rotation
— outfit swap reportedly works, face swap reportedly does not. Worth a paragraph wherever
SCAIL-2 lands.

## Authoring notes

- The conditioning class here is **driving-video + reference-image**, which the suite has
  only touched via Wan Animate. Give it the full treatment.
- Cross-links: `krea-2` (first-frame prep — already written from that end),
  `minimax-h3` (the approximate alternative that adds audio), `wan-2-2` (the rest of the
  Wan control rig), `character-lora-training` (identity that has to survive the swap).
