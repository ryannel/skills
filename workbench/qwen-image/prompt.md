# qwen-image — intent (2026-09-09)

Commissioned after the 2026-09-09 launch sweep (`workbench/harvest-2026-09-09/model-launches.md`) ranked the
Qwen-Image family the suite's biggest gap: Apache 2.0, ComfyUI-native since 2025-08, ~3.9M 30-day HF pulls,
1,162 Civitai LoRAs / 192 character-tagged, and the atlas already routes identity work to Qwen-Image-Edit
with no skill to hand the reader.

Shape: a still-image model skill (media-model-skill → references/image-models.md). Family spans
Qwen-Image (T2I base), Qwen-Image-Edit (2508), Edit-2509 (multi-image), Edit-2511, any 2512 / Layered
variants, and the Lightning speed LoRAs. Qwen-Image 3.0 is closed (2026-07-20) — state that plainly.
Relationship to the suite: Krea 2 is Qwen-Image-derived and Z-Image shares the Qwen VAE family, so
setup and LoRA doctrine cross-link heavily; the user's media-lab Krea 2 learnings (1024-native datasets,
8–12 steps on distilled bases) may transfer and must be marked as Krea evidence, not Qwen evidence.

Pillars: characters (Edit as the identity tool; LoRA path), LoRA training (ai-toolkit / musubi / diffusion-
pipe; Lightning-compatible training; Edit LoRAs on paired data), production (multi-stage ladder; role in
mixed-model pipelines; the T2I → Edit → detailer chain).

House rules: two-bar provenance, `[live-use]` only for this lab's own runs, plain language per STANDARD
§6.8a, links inside `skills/generative-media/` only. Register in marketplace.json, README, atlas suite map
and rankings (replace the "not yet covered" row), sibling back-links, freshness.json.
