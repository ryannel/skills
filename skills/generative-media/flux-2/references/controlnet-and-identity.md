# FLUX.2 — Pose Control & Identity Preservation

Source tier: Alibaba PAI Fun Union ControlNet — official repos and model cards (primary). iFayens PuLID and bryanmcguire community nodes — community/third-party (labelled inline).

---

## Contents

1. [Why Flux.1 ControlNets don't work on FLUX.2](#1-why-flux1-wont-work)
2. [ControlNet (Alibaba PAI Fun Union)](#2-controlnet)
3. [PuLID — face identity (iFayens)](#3-pulid)
4. [IP-Adapter face — status](#4-ip-adapter)
5. [ReferenceLatent — native reference conditioning](#5-referencelatent)

---

## 1. Why Flux.1 ControlNets don't work on FLUX.2

FLUX.2 changed the block ratio: **8 double-stream + 48 single-stream** vs Flux.1's 19 double + 38 single. ControlNet injection is anchored to specific double-stream block indices — the weight shapes are incompatible. Loading a Flux.1 ControlNet (InstantX, Shakker-Labs, XLabs) into a FLUX.2 pipeline will produce shape errors or silently corrupted output. All three major Flux.1 ControlNet teams (InstantX, Shakker-Labs, xinsir) have not published a FLUX.2 adaptation as of June 2026.

The only FLUX.2-native ControlNet is from **Alibaba PAI** (as part of the VideoX-Fun framework).

---

## 2. ControlNet (Alibaba PAI Fun Union)

**Primary source:** `alibaba-pai/FLUX.2-dev-Fun-Controlnet-Union` on Hugging Face (part of the VideoX-Fun framework, `github.com/aigc-apps/VideoX-Fun`).

### Model files

| File | Size | Conditioning types |
|---|---|---|
| `FLUX.2-dev-Fun-Controlnet-Union.safetensors` | ~8 GB | Canny, HED, Depth, Pose, MLSD, Inpainting |
| `FLUX.2-dev-Fun-Controlnet-Union-2602.safetensors` | ~8.3 GB | Adds Scribble and Gray — **use this version** |

Download from `alibaba-pai/FLUX.2-dev-Fun-Controlnet-Union` on Hugging Face.

**Install location:** `models/model_patches/` — specified in the official VideoX-Fun documentation. Place both file options here if you download both.

**Important: the standard `ControlNetLoader` node will return an error** ("controlnet file is invalid and does not contain a valid controlnet model"). These are model patch files, not standard ControlNet files.

### ComfyUI nodes

Two paths exist. Use the one that fits your setup:

**Path A — Official VideoX-Fun ComfyUI nodes (authoritative)**

From the `flux2/` subdirectory of `github.com/aigc-apps/VideoX-Fun/tree/main/comfyui/flux2`. Install the custom nodes from that directory. The `nodes.py` defines the official apply/load nodes.

**Path B — bryanmcguire community nodes**

`github.com/bryanmcguire/comfyui-flux2fun-controlnet` — clone to `ComfyUI/custom_nodes/`. Provides:
- `"Load Flux2 Fun ControlNet"` node — reads from `models/controlnet/` (not `model_patches/` per this implementation)
- `"Apply Flux2 Fun ControlNet"` node — outputs standard CONDITIONING

The bryanmcguire integration documents `models/controlnet/` as the path, but `models/model_patches/` is what VideoX-Fun (the upstream source) specifies. If using bryanmcguire nodes, try `models/model_patches/` first; if the loader fails, try `models/controlnet/`.

**Injection mechanism:** The apply node injects into FLUX.2 double-stream blocks 0, 2, 4, and 6 (4 of the 8 double-stream blocks) via a 260-channel control context: 128 conditioning + 4 mask + 128 inpainting. Output connects normally into the FLUX.2 FluxGuidance → BasicGuider → SamplerCustomAdvanced path.

### Supported conditioning types (by preprocessor input)

| Type | Preprocessor | Recommended strength | `control_guidance_end` |
|---|---|---|---|
| Pose | DWPreprocessor (DWPose) | 0.9 | 0.65 |
| Depth | Depth Anything V2 | 0.8 | 0.80 |
| Canny | cv2.Canny | 0.7 | 0.80 |
| HED | HED edge detector | ~0.7 | ~0.80 |
| Scribble | Scribble preprocessor | ~0.8 | ~0.80 |
| MLSD | MLSD line detector | ~0.8 | ~0.80 |
| Gray | — (grayscale input) | ~0.8 | ~0.80 |
| Inpainting | Mask input | — | — |

The conditioning type is determined by which preprocessor feeds the control image — there is no explicit "mode" parameter. A single model handles all types (Union architecture).

### Preprocessor node recommendations

- **Pose:** `DWPreprocessor` from `comfyui_controlnet_aux` — generates skeleton from an image using DWPose body + face + hand keypoints.
- **Depth:** `DepthAnythingV2Preprocessor` — Depth Anything V2, best for real images.
- **Canny:** `CannyEdgePreprocessor` or `cv2.Canny` directly — threshold 0.1–0.3.
- **All-in-one:** `AIO_Preprocessor` handles Canny, Depth, HED, MLSD via a `preprocessor` parameter.

### Integration with FLUX.2 variants

Confirmed to support all FLUX.2 open-weight variants: [dev], [klein] 4B, [klein] 9B. The conditioning strength may need adjustment between variants — [dev]'s 32B architecture responds more strongly than [klein] 4B.

---

## 3. PuLID — face identity (iFayens)

PuLID (Portrait Unique Identity Locking) takes a reference portrait and locks face identity into generation. For FLUX.2, use **iFayens/ComfyUI-PuLID-Flux2** — this is the only FLUX.2-specific PuLID implementation as of June 2026.

**Primary source:** `github.com/iFayens/ComfyUI-PuLID-Flux2` (model weights: `Fayens/Pulid-Flux2` on Hugging Face).

### Required files and install locations

| Component | Source | Install path |
|---|---|---|
| PuLID weights | `Fayens/Pulid-Flux2` on HF | `ComfyUI/models/pulid/` |
| AntelopeV2 face model | InsightFace (`buffalo_l` ONNX files) | `ComfyUI/models/insightface/models/antelopev2/` |
| EVA-CLIP | Auto-downloads on first run (~800 MB) | Auto-managed (do not install manually) |

**Required Python packages** (install before first run):

```bash
pip install insightface onnxruntime-gpu open-clip-torch safetensors "ml_dtypes==0.3.2"
```

Do **not** install EVA-CLIP from GitHub separately — the auto-download is intentional and the versions must match.

### ComfyUI nodes (5 nodes added)

| Node | Role |
|---|---|
| `Load InsightFace (PuLID)` | Loads AntelopeV2 face detector/embedder |
| `Load EVA-CLIP (PuLID)` | Loads EVA-CLIP image encoder |
| `Load PuLID ✦ Flux.2` | Loads PuLID weights from `models/pulid/` |
| `Apply PuLID ✦ Flux.2` | Main apply node — outputs CONDITIONING |
| `Face Debug Preview` | Shows detected face for verification |

### Workflow integration

PuLID's `Apply PuLID ✦ Flux.2` node outputs standard CONDITIONING that connects directly into the FLUX.2 sampler path:

```
Reference portrait → [Load InsightFace] → [Apply PuLID ✦ Flux.2]
                  → [Load EVA-CLIP]    ↗         ↓
                  → [Load PuLID]      ↗     CONDITIONING
                                              ↓
                              FluxGuidance → BasicGuider → SamplerCustomAdvanced
```

Positive and negative conditioning pass through the apply node. The `strength` parameter controls identity lock intensity.

### Recommended settings

| Parameter | Value | Notes |
|---|---|---|
| `strength` | 1.0 | Default; use for moderate identity adherence |
| `strength` | 1.4 | Higher identity preservation; per author docs |
| FluxGuidance | 4 | Unchanged from standard [dev] setup |
| Steps | 20–28 | Same as standard [dev]; PuLID doesn't require step changes |

### Current limitations (June 2026)

- Training scripts temporarily removed — instability in fine-tuning path; official weights are available, custom-trained identity weights are not yet supported
- No img2img mode (text-to-image only)
- Works with [dev], [klein] 4B, [klein] 9B

### PuLID for face identity vs LoRA for face identity

| Method | Pros | Cons |
|---|---|---|
| PuLID | No training required; works from a single reference portrait at inference | Requires custom nodes + extra model files; in-progress (some features unfinished); drifts at extreme angles |
| Character LoRA | More stable; full control over training domain; carries body/outfit/mannerisms, not just the face | Requires training (20–50 images, ~2000 steps); LoRA is subject-specific |

For **one-off identity** (a photo of someone you can't train on): PuLID. For **recurring character** (product persona, IP character, actor): train a LoRA. The PuLID weights are natively trained **klein-first** (`pulid_flux2_klein_v1/v2` in the `Fayens/Pulid-Flux2` repo) and calibration differs between base and distilled variants — a single-maintainer, fast-moving project; re-verify current weights and limits before install. **The full character playbook — choosing between multi-reference, PuLID, and the LoRA pipeline, the dataset factory, and multi-character scenes — is `references/characters.md`.**

---

## 4. IP-Adapter face — status

**No FLUX.2-native IP-Adapter (general or face-specific) has been released as of June 2026.**

All published IP-Adapter implementations for FLUX target FLUX.1-dev only:
- `InstantX/FLUX.1-dev-IP-Adapter` — FLUX.1 only; general image conditioning, not face-specific
- `XLabs-AI/flux-ip-adapter-v2` — FLUX.1 only
- `cubiq/ComfyUI_IPAdapter_plus` — maintenance-only since April 2025; SD1.x/SDXL face models only

Until a FLUX.2 IP-Adapter is published, use **PuLID** (section 3) for face identity and **ReferenceLatent** (section 5) for style/character consistency.

---

## 5. ReferenceLatent — native reference conditioning

FLUX.2 ships native multi-reference conditioning via `ReferenceLatent` nodes — built into ComfyUI core, no custom nodes needed. This is distinct from ControlNet (no structural skeleton input) and PuLID (no face-specific encoding). It preserves general character/style/layout identity from reference images, encoded as latent conditioning tokens.

**Core node:** `ReferenceLatent` — takes a reference image, encodes it to latent via the FLUX.2 VAE, injects it into conditioning. Chain multiple nodes for multiple references.

**Extended options:**
- `shootthesound/comfyui-ReferenceLatentPlus` — adds per-image strength control, timestep gating, MediaPipe auto-masks, and up to 4 inputs in one node
- `xmarre/ComfyUI-Flux2Klein-Conditioning-Toolkit` — region-aware conditioning and corrected reference mixing, primarily for [klein] variants

Full template notes and integration patterns: `references/setup-and-workflows.md` §2 (dev image-edit template).

### ControlNet vs PuLID vs ReferenceLatent: choosing the right tool

| Goal | Best tool |
|---|---|
| Match exact body pose from a reference skeleton | ControlNet (Fun Union, Pose mode) |
| Match depth layout / composition from a reference | ControlNet (Fun Union, Depth mode) |
| Match precise edge structure | ControlNet (Fun Union, Canny/HED) |
| Lock face identity from a portrait photo | PuLID |
| Preserve general character/style/scene from reference images | ReferenceLatent (native) |
| Combine pose control with face identity | ControlNet (pose) + PuLID (face) — both output CONDITIONING and can be combined |
