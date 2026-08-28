# Wan 2.2 — motion, camera and structural control

Wan 2.2's control stack is the deepest in the open video ecosystem. It consists of Fun Camera, Fun Control, Fun InP and VACE. This stack is the reason to reach for Wan even when [`minimax-h3`](../../minimax-h3/) or [`ltx-2-5`](../../ltx-2-5/) win on raw fidelity or native audio.

Be precise about why. The honest claim is depth, not exclusivity. [`minimax-h3`](../../minimax-h3/) has no conditioning rig at all, so it controls only through the prompt. [`ltx-2-5`](../../ltx-2-5/) does ship one: IC-LoRAs that take a reference input plus an optional mask, and they cover depth, canny, pose and motion tracks. Wan's stack is still the deeper and better-documented one. Most of LTX's adapters were trained on 2.3, and its camera-move LoRAs are LTX-2-era files that may be stale `[flagged — re-verify]`.

So **a named camera path is the one job that genuinely comes back here**, because nothing else in the suite ships a working camera rig. Pose and depth, meanwhile, are now a choice between two suites. All of Wan's control models come from **Alibaba PAI**, the same team behind the Fun Union ControlNet that [`z-image`](../../z-image/) uses. And all of it is **Apache 2.0**, which is the second half of the reason.

## Which tool for which job

| You want… | Reach for | Training needed |
|---|---|---|
| A specific camera move | **Fun Camera Control** | No |
| Pose / depth / structure from a driving video | **Fun Control** | No |
| A controlled transition between two frames | **Fun InP**, or core FLF2V | No |
| A character to hold its identity across a shot | **VACE (Fun)** reference conditioning | No |
| A character to perform a specific performance | **Animate** — motion transfer / replacement | No |
| A character reusable across many shots and prompts | **Character LoRA** (`lora-training.md`) | Yes |

The rough decision rule: **anything you can express as a reference or a driving signal should be expressed that way before you consider training.** Training is for identity you need to summon by prompt in arbitrary new contexts. Everything else is cheaper and more controllable as conditioning.

---

## Fun Camera Control

Fun Camera gives you explicit, discrete camera moves rather than prompt-suggested ones: **pan up / down / left / right, zoom in / out**, and combinations of these.

- Model: `alibaba-pai/Wan2.2-Fun-A14B-Control-Camera`
- ComfyUI files: `wan2.2_fun_camera_{high,low}_noise_14B_fp8_scaled.safetensors` → `models/diffusion_models/`
- Template settings: 20 steps, **CFG 3.5**, `euler`/`simple`, shift 8, 81 frames @ 16 fps; the 4-step LoRA path uses 4 steps / CFG 1.0 with the high expert `0 → 2` and low `2 → 4`

**Prompt-level camera direction versus Fun Camera:** a prompt is a request that the model may only partially honour. Fun Camera is an instruction with a defined trajectory. Use prompt phrasing for feel (`handheld`, `steadicam`). Use Fun Camera when the move itself is the point, such as a product turntable, a matched cut, or anything that has to repeat.

---

## Fun Control

Fun Control provides structural conditioning from a driving video. It is the ControlNet analogue: pose, depth and edge signals transfer motion and composition, while the prompt supplies appearance.

- ComfyUI files: `wan2.2_fun_control_{high,low}_noise_14B_fp8_scaled.safetensors`
- Template settings: 20 steps, CFG 3.5, `euler`/`simple`, shift 8

The usual application is retargeting: take a real performance, extract the pose, and drive a different subject with it. Preprocessing uses the same family of extractors as image ControlNets. The difference is that consistency across frames now matters, so a jittery pose extraction produces jittery output.

---

## Fun InP

Fun InP does first-last-frame generation with smooth interpolation between the endpoints. It overlaps with core FLF2V (`WanFirstLastFrameToVideo`). Fun InP is the PAI model built for the job; core FLF2V is the built-in path.

- ComfyUI files: `wan2.2_fun_inpaint_{high,low}_noise_14B_fp8_scaled.safetensors`

Either way, the value is the same: **giving the model both endpoints removes its freedom to wander.** That is why FLF-conditioning is the standard mitigation for drift in long stitched pieces (`setup-and-workflows.md` §6).

---

## VACE

VACE is reference-driven conditioning. It is the **no-training** path to a consistent character or subject. It is available for Wan 2.2 as a Fun variant (`Wan2.2-VACE-Fun-A14B`, including community GGUF builds) `[community — re-verify current file naming]`.

VACE was established on Wan 2.1, where it became the default method for posing a consistent character. It is reportedly workable from ~8 GB VRAM `[community — re-verify]`. Treat the 2.2 line as the same technique on a newer base. Verify file names and node wiring against the current ComfyUI templates before relying on specifics, because this is the fastest-moving part of the Wan ecosystem.

---

## Animate

Animate does character animation and replacement. You drive a character with a reference performance video, or you replace a character in existing footage.

- ComfyUI file (Kijai repackage in the official template): `Wan2_2-Animate-14B_fp8_e4m3fn_scaled_KJ.safetensors`
- It ships alongside `WanAnimate_relight_lora_fp16.safetensors`, a relight LoRA that matches the inserted character to the target scene's lighting. That LoRA is what makes replacement look composited rather than pasted
- The template also loads `lightx2v_I2V_14B_480p_cfg_step_distill_rank64_bf16.safetensors` for acceleration; shift 8

Animate answers "make *this specific person* do *this specific thing*". It is a genuinely different tool from a character LoRA: Animate transfers a performance, while a LoRA teaches an identity. The two compose well — use a LoRA for who the character is, and Animate for what they do.

**Animate is no longer the first reach for replacement, though.** [`scail-2`](../../scail-2/) is a Wan 2.1 fine-tune from zai-org, not an Alibaba release, and it has displaced Animate for reference-image-plus-driving-video character replacement in community practice. Animate remains the in-family option. It stays inside this two-expert graph, and its relight LoRA is already wired for compositing into the target scene. Reach for Animate when you want replacement without leaving the Wan 2.2 stack. Reach for SCAIL-2 when replacement fidelity is the whole job.

---

## What is not controllable

These gaps are stated plainly, because they matter as much as the features:

- **No audio generation.** S2V consumes an audio track for lip-sync, but nothing in the family produces sound. For generated audio, [`minimax-h3`](../../minimax-h3/) models video and stereo audio jointly in one forward pass. Check its licence section first, since it excludes several major territories. [`ltx-2-5`](../../ltx-2-5/) does the same, under a licence gated on your company's revenue.
- **No regional prompting across frames.** There is no per-region conditioning equivalent to image-side regional prompting. Multi-character scenes are conditioned globally.
- **Clip length is not a free parameter.** The 14B is built around ~81 frames. Anything longer is stitching, with the drift consequences that stitching implies.
- **Camera moves are discrete, not arbitrary trajectories.** Fun Camera exposes named moves and combinations, not a freeform keyframed path.
- **Frame-exact timing is not directly controllable.** You cannot specify that an action completes on frame 47. You shape timing through phrasing, clip length and FLF endpoints.
