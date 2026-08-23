# Staged freshness findings — z-image

Staged by the 2026-08-23 repair pass. Both findings came from live use (a media-lab
character-LoRA planning run + its NSFW extension) and **need research before authoring** —
that is why they were staged rather than patched inline. Run the update with the
`media-model-skill` conventions.

## 1. `qwen-image-edit-uncovered-dependency` (major, found 2026-08-23)

`references/characters.md` §3 makes Qwen-Image-Edit the preferred dataset factory, but the
suite documents none of its operational facts. A planning agent had to reconstruct them from
`Comfy-Org/Qwen-Image-Edit_ComfyUI` on HF and *guess* `clip_type: qwen_image`.

Research needed before writing:

- Exact ComfyUI file list for Qwen-Image-Edit 2511 (fp8 and full): diffusion model, text
  encoder, VAE — filenames, sizes, destination folders, loader nodes, correct `clip_type`.
- VRAM floor for an edit pass at dataset-factory resolutions.
- The `Qwen-Edit-2509-Multiple-angles` LoRA (same ecosystem): does it work under 2511, and
  does it solve the 8-point rotation coverage protocol as directly as it appears to? If yes
  it belongs in characters.md §3 as the coverage shortcut.
- **Does Qwen-Image-Edit execute explicit edits?** Untested. This gates the factory × NSFW
  intersection (`character-lora-training/references/nsfw-training.md` §3 vs characters.md §3):
  if it refuses or degrades, the documented path must be "factory for the clothed/coverage
  subset, native Z-Image generation for the explicit subset". One cheap pod test settles it.

Decision also needed: minimal setup block inside `characters.md` vs a standalone
`qwen-image-edit` skill. Lean minimal-block unless the file list + wiring exceeds ~a page —
Qwen-Image-Edit is load-bearing for *this* skill's workflow, not (yet) a suite citizen.

## 2. `anatomy-loras-named-none` (minor, found 2026-08-23)

`references/lora-training.md` §6 rests the adult-capability claim on "anatomy-specific LoRAs
exist" but names none — so a deployment manifest cannot be made concrete from the skill.

Research needed: a Civitai browse (JSON API, per the house community-research method) for 1–2
verified Z-Image anatomy/realism LoRAs — name, author, download stats, last-updated — cited
community-bar with the retrieval date. Also note whether any are Turbo-compatible, since the
suite's doctrine is train-on-Base, generate-on-Turbo and stacking behaviour there is
`[contested]`.
