# Wan 2.2 — motion, camera and structural control

Wan 2.2's control stack is the strongest in the open video ecosystem, and it is the main reason to choose it over HunyuanVideo or LTX. All of it comes from **Alibaba PAI** — the same team behind the Fun Union ControlNet that [`z-image`](../../z-image/) uses — and all of it is **Apache 2.0**.

## Which tool for which job

| You want… | Reach for | Training needed |
|---|---|---|
| A specific camera move | **Fun Camera Control** | No |
| Pose / depth / structure from a driving video | **Fun Control** | No |
| A controlled transition between two frames | **Fun InP**, or core FLF2V | No |
| A character to hold its identity across a shot | **VACE (Fun)** reference conditioning | No |
| A character to perform a specific performance | **Animate** — motion transfer / replacement | No |
| A character reusable across many shots and prompts | **Character LoRA** (`lora-training.md`) | Yes |

The rough decision rule: **anything you can express as a reference or a driving signal should be, before you consider training.** Training is for identity you need to summon by prompt in arbitrary new contexts; everything else is cheaper and more controllable as conditioning.

---

## Fun Camera Control

Explicit, discrete camera moves rather than prompt-suggested ones: **pan up / down / left / right, zoom in / out**, and combinations.

- Model: `alibaba-pai/Wan2.2-Fun-A14B-Control-Camera`
- ComfyUI files: `wan2.2_fun_camera_{high,low}_noise_14B_fp8_scaled.safetensors` → `models/diffusion_models/`
- Template settings: 20 steps, **CFG 3.5**, `euler`/`simple`, shift 8, 81 frames @ 16 fps; the 4-step LoRA path uses 4 steps / CFG 1.0 with the high expert `0 → 2` and low `2 → 4`

**Prompt-level camera direction versus Fun Camera:** a prompt is a request the model may partially honour; Fun Camera is an instruction with a defined trajectory. Use prompt phrasing for feel (`handheld`, `steadicam`) and Fun Camera when the move itself is the point — a product turntable, a matched cut, anything that has to repeat.

---

## Fun Control

Structural conditioning from a driving video — the ControlNet analogue. Pose, depth and edge signals transfer motion and composition while the prompt supplies appearance.

- ComfyUI files: `wan2.2_fun_control_{high,low}_noise_14B_fp8_scaled.safetensors`
- Template settings: 20 steps, CFG 3.5, `euler`/`simple`, shift 8

The usual application is retargeting: take a real performance, extract pose, and drive a different subject with it. Preprocessing is the same family of extractors used for image ControlNets; the difference is that consistency across frames now matters, so a jittery pose extraction produces jittery output.

---

## Fun InP

First-last-frame generation with smooth interpolation between the endpoints. Overlaps with core FLF2V (`WanFirstLastFrameToVideo`); Fun InP is the PAI model built for the job, core FLF2V is the built-in path.

- ComfyUI files: `wan2.2_fun_inpaint_{high,low}_noise_14B_fp8_scaled.safetensors`

Either way, the value is the same: **giving the model both endpoints removes its freedom to wander**, which is why FLF-conditioning is the standard mitigation for drift in long stitched pieces (`setup-and-workflows.md` §6).

---

## VACE

Reference-driven conditioning — the **no-training** path to a consistent character or subject. Available for Wan 2.2 as a Fun variant (`Wan2.2-VACE-Fun-A14B`, including community GGUF builds) `[community — re-verify current file naming]`.

VACE was established on Wan 2.1, where it became the default consistent-character-posing method, reportedly workable from ~8 GB VRAM `[community — re-verify]`. Treat the 2.2 line as the same technique on a newer base, and verify file names and node wiring against the current ComfyUI templates before relying on specifics — this is the fastest-moving part of the Wan ecosystem.

---

## Animate

Character animation and replacement: drive a character with a reference performance video, or replace a character in existing footage.

- ComfyUI file (Kijai repackage in the official template): `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors`
- Ships alongside `WanAnimate_relight_lora_fp16.safetensors` — a relight LoRA that matches the inserted character to the target scene's lighting, which is what makes replacement look composited rather than pasted
- The template also loads `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` for acceleration; shift 8

Animate is the strongest answer to "make *this specific person* do *this specific thing*" and is a genuinely different tool from a character LoRA: it transfers a performance, where a LoRA teaches an identity. They compose — a LoRA for who, Animate for what they do.

---

## What is not controllable

Stated plainly, because the gaps matter as much as the features:

- **No audio generation.** S2V consumes an audio track for lip-sync; nothing in the family produces sound. For generated audio, [`minimax-h3`](../../minimax-h3/) models video and stereo audio jointly in one forward pass — check its licence section first, since it excludes several major territories — and LTX-2.5 does the same.
- **No regional prompting across frames.** There is no per-region conditioning equivalent to image-side regional prompting; multi-character scenes are conditioned globally.
- **Clip length is not a free parameter.** The 14B is built around ~81 frames. Longer is stitching, with the drift consequences that implies.
- **Camera moves are discrete, not arbitrary trajectories.** Fun Camera exposes named moves and combinations, not a freeform keyframed path.
- **Frame-exact timing is not directly controllable.** You cannot specify that an action completes on frame 47; you shape it through phrasing, clip length and FLF endpoints.
