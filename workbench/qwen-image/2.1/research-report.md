# Qwen-Image-2.1 — research report (2026-09-20)

Weights went public **today, 2026-09-20** (HF repo created 09-14 private, LICENSE dated 09-20, README "2026.09.20: We released"). Everything below is
from primary sources read the same day. Community evidence is **near-zero**: no Reddit threads were reachable (blocked from every surface),
Civitai has no 2.1 entries, HF discussions are three "thank you" posts. **Re-run the community pass in 7–10 days**; the 50 ModelScope
early-access testers must publish hands-on reviews by **2026-09-28**.

## 1. The three facts that change the existing skill

1. **Licence is no longer Apache 2.0.** `Qwen RESEARCH LICENSE AGREEMENT`, release date 2026-09-20 (`LICENSE.txt` here, verbatim).
   §1(i) "Non-Commercial" = research or evaluation only; §2(b) commercial use needs a separate licence from
   `model-business@notice.qwencloud.com`; §4(b) derivative models must display "Built with Qwen" / "Improved using Qwen"; §4(c) may not use
   "Qwen" as primary name of derivatives; §8 governed by PRC law, Hangzhou courts. Same licence on both prompt-rewriter models and
   inherited by the Comfy-Org repackage (`license_name: qwen-research`). **This puts 2.1 on the wrong side of the atlas's licence-first
   elimination ladder for any commercial job.** The 20B family (base, Edit-2509/2511, 2512, Layered) stays Apache 2.0 — those cards are unchanged.
   `[official — LICENSE file, verified]`
2. **It is a new architecture, not a 20B variant.** 7B (vLLM/mflux say 7.1B) **single-stream** DiT, 32 layers, block-causal attention;
   text encoder **Qwen3-VL-8B** (not Qwen2.5-VL-7B); **new 64-channel RGBA VAE at 16× compression** (not the Wan-2.1 16-ch/8× VAE). Nothing
   from the 20B shelf carries over: **no LoRA, no Lightning, no ControlNet, no GGUF loader, no Nunchaku** works on it. `[official — configs]`
3. **One model does T2I and edit.** Same weights for both; edit is "pass images". Up to **10 reference images**; RGBA output decided by the
   prompt; local edits by drawn circles, painted regions, or a separate mask image passed as a second input. Absorbs Qwen-Image-Layered's
   transparency ("In December 2025, we introduced Qwen-Image-Layered … 2.1 now integrates this capability") — blog. `[official]`

Open-weights 2.1 is distinct from the **hosted 2.0/3.0 Pro** line: the HF Space demo (`app.py`) calls DashScope model
`pre-qwen-image-2.1-pro-yunqi` with `prompt_extend` — i.e. the demo is a hosted *Pro* variant with server-side rewriting, not the downloadable
weights. Do not attribute demo quality to the local model. Qwen-Image-Bench top-5 lists "Qwen Image 2.0 Pro" at 57.84 overall; **no published
score for open 2.1** (blog shows a chart image only).

## 2. Architecture and files `[official]`

| Component | Class (diffusers) | Detail | bf16 size |
|---|---|---|---|
| DiT | `QwenImage21Transformer2DModel` | 32 layers, 32 heads × 128, in/out 64 ch, patch 1, mlp_ratio 3, `causal_condition: true`, RoPE axes [16,56,56] | 14.23 GB |
| Text encoder | Qwen3-VL-8B (`Qwen3VLForConditionalGeneration`) | reads text + reference images; vision hidden states dropped and replaced by VAE latents at those positions (ComfyUI PR) | 17.53 GB |
| VAE | `AutoencoderKLQwenImage21` | 4-ch in/out (RGBA), 64-ch latent, 16× spatial; Wan-2.2-family module parametrised for single images (`is_residual`, `base_dim 96`, `decoder_base_dim 144`) | 1.35 GB (0.68 GB Comfy bf16) |
| Scheduler | FlowMatchEuler, dynamic shift | `base_shift 0.5 @ 256 tokens`, `max_shift 0.9 @ 8192 tokens`, `shift_terminal 0.02`, exponential time-shift. ComfyUI hardcodes `shift 0.69` (= mu at 1024²) | — |

Mixed-granularity attention: text tokens token-level causal, image blocks chunk-level bidirectional; block-causal `(q_idx >= kv_idx) or same_image_block`.
Text + reference tokens are modulated at t=0 → step-independent → **prefix KV cache** computed once per run (~1.7× on edits, ComfyUI PR).

Comfy-Org repackage (`Comfy-Org/Qwen-Image-2.1`, names verbatim, 2026-09-20): `diffusion_models/qwen_image_2.1_bf16` (14.23 GB),
`qwen_image_2.1_int8_convrot` (7.26 GB, **template default**); `text_encoders/qwen3vl_8b_bf16` (17.53 GB), `qwen3vl_8b_int8_convrot`
(9.35 GB, template default since templates v0.11.66), `qwen3vl_8b_w4a8` (6.31 GB); `vae/qwen_image_2.1_vae_bf16` (0.68 GB).
**No fp8_e4m3fn build.** Community GGUFs appeared within hours (Abiray, AlperKTS — 0 downloads) but ComfyUI-GGUF has had no commit since
2026-01-12, so there is no loader path yet `[flagged — re-verify]`.

Prompt rewriters (optional, same research licence): `Qwen/Qwen-Image-2.1-PE-T2I` and `-PE-I2I`, fine-tuned **Qwen3.5-VL 9B** (~19 GB each),
thinking mode on, output JSON `{"rewritten_prompt","wh_ratio"}` (+ `"ratio_follow": "<image1>"` for edits). Their `system_prompt.txt` files are
the best available official prompt-writing guidance (see §5).

## 3. Sampling regime `[official]`

- **Steps 40, CFG off (`true_cfg_scale=1.0`)** — the diffusers defaults and the card. ComfyUI templates start at **25 steps, cfg 1, euler/simple**;
  template note: "official pipeline uses about 40–50 with euler … more advanced samplers need fewer steps". No `guidance_scale` parameter exists.
- **CFG only engages with a negative prompt** and doubles per-step cost (diffusers doc, vLLM recipe). Negative is inert at cfg 1 (template note).
  DiffSynth: empty prompt is coerced to a single space because Qwen has no BOS token.
- **Resolution:** native 2K. Official sizes: 1:1 2048², 4:3 2400×1792, 3:2 2528×1696, 16:9 2752×1536 (+ portraits). Multiples of 32
  (Comfy step 32; vLLM floors to 32). Comfy T2I template defaults to **1 MP** and says set 4 MP for 2K.
- **Edit sizing (Comfy `TextEncodeQwenImage21`):** `resolution` is a **total-pixel budget** (≈ res×res, aspect kept, default 1024; 0 = keep each
  reference's own size rounded to 32). Output canvas follows **image_1**; node emits an empty latent on image_1's grid because "any other size
  shifts the edit". `custom_size` on → use ResolutionSelector but keep it near the resized image_1 or the edit drifts. Edit template ships
  `resolution 0`. vLLM: output derives from the *last* reference at ~1024² when size omitted — implementations disagree; treat as unsettled.
- **Sizes seen in official demo cases:** RGBA bride at 1664×2496, shoe campaign at 1760×2368 — non-standard sizes work.

## 4. ComfyUI `[official — PR #16400 by kijai, merged 2026-09-19; templates v0.11.65/66, 2026-09-20]`

Core support, no custom nodes; needs a nightly newer than v0.36.0 (2026-09-15) until the next tag `[flagged — check release]`.
Loaders: `UNETLoader` (int8_convrot default), `CLIPLoader` type **`qwen_image`** ← `qwen3vl_8b_*`, `VAELoader` ← `qwen_image_2.1_vae_bf16`.
New nodes (category `model/conditioning/qwen image`):
- **`TextEncodeQwenImage21`** — prompt, negative_prompt, optional VAE, `resolution`, autogrow `image_1`…`image_16` (model supports 10). Outputs
  positive, negative, latent. Alpha in references: the vision tower sees alpha composited over white, the VAE keeps all four channels.
  Without a VAE connected, references condition through the encoder alone (no latent splice).
- **`QwenImage21Cache`** (experimental) — `device` auto/gpu/cpu/off, `dtype` default/int8/int4. int8 halves cache at ~bf16 accuracy; int4
  quarters it, ~2× per-step error; `off` recomputes prefix each step (debug). Template default auto/default.
- No `ModelSamplingAuraFlow` in the graph — shift is baked in the model config (0.69).
- Templates: `image_qwen_image_2_1_t2i`, `image_qwen_image_2_1_image_edit` (two-image denim-shirt try-on), `image_qwen_image_2_1_background_removal`
  (prompt "Remove the background, and output a PNG image"; save via `SaveImageAdvanced` png). Sampler in all: KSampler euler/simple 25 / cfg 1 / denoise 1.
- **LoRA plumbing exists** (`comfy/lora.py` maps `img_mlp.gate_up` → gate_layer/proj halves; transformer / lycoris prefixes) — but no LoRA exists yet.
- kijai's deliberate divergence from upstream: reference grids offset half a token when parity differs from the target, to avoid position drift.

## 5. Prompting `[official — card, templates, demo cases, PE system prompts]`

- **Reference tokens are `<image1>`, `<image2>` …** (4 tokens each). Not "Picture 1:". Chinese demo prompts also use 【图1】. image_1 is the
  edit target; the rest are references. Template exemplar: "Keep the character and pose in <image1> unchanged, put this light blue denim shirt from
  <image2> on the character, preserve the original facial features, hair, body shape and pose …".
- **RGBA wrapper, verbatim:** "This is an RGBA image with transparency. ⟨subject⟩. The image has alpha channel and the background is transparent."
  Chinese: "这是一张带有透明度的RGBA格式图像 … 该图像具有alpha通道，背景是透明的。" Save PNG; `.convert("RGB")` or JPEG drops alpha (DiffSynth).
  DiffSynth craft: avoid describing environment/ambient light or the model fills the canvas; hair/ribbons/water produce wide semi-transparent
  alpha — add "clear silhouette / clean edges" for hard cutouts. Background removal is an edit with an RGB input and an RGBA output.
- **Local edits, three grammars** (demo cases): (a) coloured circles drawn on the input — "Remove the watch in the blue circle, change the hair in
  the red circle to black, replace the green-circled area with …; the blue, red and green annotation lines must not be rendered"; (b) painted
  region — "in the white-masked area on the right add a scuba diver …"; (c) **original + separate mask as two inputs** — "at the circled place add
  a cowboy …" (mask image is the second input, so the original stays unobscured).
- **Style of the official rewriter (PE-T2I):** one long English paragraph "as if looking at the finished image"; opening sentence names medium,
  style, subject, background; 8–14 positional phrases reaching corners and edges; every legible string in straight double quotes in its own
  script with weight/colour/case; unreadable text called "blurred / indistinct" rather than invented; never write ratio or pixel counts in the
  prompt (goes in `wh_ratio`). Default ratios 3:2 / 2:3.
- **Rewriter for edits (PE-I2I):** "edit exactly the attribute named, push it to a strong degree, hold everything else at input fidelity"; name what
  stays by type/position/role *without* describing its appearance (a concrete preservation description reads as a generation instruction and
  causes drift); for identity, point at the reference image rather than describe the face. Rendered-text language: user-specified → image's
  dominant existing text language → instruction language; monolingual inside quotes.
- Bilingual: demo prompts are heavy Chinese; text rendering in both scripts is a headline claim.

## 6. Hardware and speed

- **No official VRAM statement.** Data points: vLLM-Omni bf16, 1024², 40 steps → **4.5 s, 34.0 GB peak on GB300** `[official-adjacent — vLLM recipe]`.
  mflux on **M5 Max**, 1024², 40 steps bf16: ~1.5 s/step, ~78 s, **peak ~46 GB bf16 / ~30.7 GB q8**; text encoder kept bf16 because quantising the
  VL tower degrades conditioning `[community — ivanfioravanti, mflux PR #736, open]`. SGLang cookbook: "full resident pipeline exceeds" a 4090/5090;
  4090 path keeps DiT+VAE resident and streams encoder layers; NVFP4 on Blackwell only. DiffSynth claims **7 GB minimum** with disk offload.
  ComfyUI int8 pair = 7.26 + 9.35 GB on disk; `memory_usage_factor 6.0`.
- Edits with many references are where the KV cache pays; T2I gains little.

## 7. Training `[official]`

- **DiffSynth-Studio is the only trainer with 2.1 support today** (commits 2026-09-20). Example LoRA script: rank 32, LR 1e-4, `--max_pixels 1048576`,
  5 epochs, `--lora_target_modules ""` (default set), gradient checkpointing. Images load as **RGBA by default → transparent datasets train
  transparent generation directly**. Edit-LoRA path via `--data_file_keys "image,edit_image" --extra_inputs "edit_image"` (commented example
  reuses the Edit-2511 paired dataset). Full fine-tune script also shipped.
- ai-toolkit (last Qwen commit 09-16, pre-release), musubi-tuner, SimpleTuner: **no 2.1 support yet** `[flagged — re-verify weekly]`.
- Licence §4(b): any published LoRA must carry "Built with Qwen"; §2 makes selling LoRAs or outputs commercially non-compliant without a licence.

## 8. Inference stacks (day-0) `[official README]`

diffusers `QwenImage21Pipeline` (merged 2026-09-18, release 0.41.0; card says `transformers>=5.17`); ComfyUI; vLLM-Omni (PR #7759 unmerged at
recipe time; max 4 refs; `/v1/images/edits` takes a form not JSON; server default steps 50 and true_cfg 4.0 — override both); SGLang-Diffusion;
LightX2V (inference only — **no Lightning/distill LoRA for 2.1 exists**; lightx2v's HF org has no 2.1 repo); mflux (Apple, T2I + img2img only, no edit).

## 9. What the skill should say about 2.1 vs the 20B family

| | 20B family (base/2512/Edit-2509/2511/Layered) | 2.1 |
|---|---|---|
| Licence | Apache 2.0 | **Research, non-commercial** |
| Arch | 20B dual-stream MMDiT, Qwen2.5-VL-7B, Wan-2.1 VAE 16ch/8× | 7B single-stream, Qwen3-VL-8B, RGBA VAE 64ch/16× |
| T2I vs edit | separate checkpoints | one model |
| Refs | 1–3 (Edit-2509/2511) | up to 10 (Comfy exposes 16) |
| Transparency | Layered model, separate VAE | native, prompt-switched |
| Mask editing | inpaint via ComfyUI graph | circles / paint / separate mask image |
| CFG | true CFG 2.5–4.0 | off (1.0) by default |
| Shift | AuraFlow 3.0/3.1/1.0 | dynamic mu, 0.69 @ 1MP, baked in |
| Steps | 20–50 | 40 (Comfy 25) |
| Lightning | yes, per variant | none |
| LoRA shelf | 1,100+ on Civitai | zero; DiffSynth only trainer |
| Quant | fp8/fp8mixed/int8_convrot/GGUF/Nunchaku | bf16 + int8_convrot (+ w4a8 TE) only |
| Prompt image refs | "Picture 1:" | `<image1>` |

Recommendation for the skill: add 2.1 as a **second generation** row set, not a replacement. Route: research/eval, transparency, many-reference
composition, mask-guided local edits → 2.1; anything commercial, anything needing the LoRA shelf or Lightning speed → stay on Edit-2511 / 2512.
Update the atlas licence ladder and the "identity tool" claim (2.1 claims stronger identity/product fidelity but it is unverified and non-commercial).

## 10. Gaps / re-verify list

- Community craft: none yet (Reddit unreachable; EA reviews due 09-28). Check r/StableDiffusion, Civitai, Banodoco after 09-28.
- Whether identity holds across 10 refs; whether alpha edges are usable without matting; plastic-skin status on 2.1.
- ComfyUI tagged release containing #16400; GGUF loader support; ai-toolkit / musubi 2.1 support; first Lightning-style distill.
- Output size rule on edits (image_1 vs last reference) — Comfy and vLLM disagree.
- Whether a commercial licence path or an Apache re-licence follows (Qwen-Image-2.0 open weights never came; 2.1 is the first open 7B).
- Qwen-Image-Bench score for open 2.1 (paper: arXiv 2605.28091 covers the bench, not 2.1).

## Sources
HF card + LICENSE + configs (`Qwen/Qwen-Image-2.1`, PE-T2I, PE-I2I); `QwenLM/Qwen-Image-2.1` README; qwen.ai blog `qwen-image-2.1`;
diffusers PR #14804 + docs; `Comfy-Org/ComfyUI` PR #16400; `Comfy-Org/workflow_templates` v0.11.65–66 JSON; `Comfy-Org/docs` PR #1742;
`Comfy-Org/Qwen-Image-2.1` HF; DiffSynth-Studio docs/zh/Model_Details/Qwen-Image-2.1.md + examples/qwen_image_21; vLLM recipe; SGLang cookbook;
LightX2V scripts/qwen_image_21; mflux PR #736; HF Space `Qwen/Qwen-Image-2.1` app.py + examples/cases.json; Qwen-Image-Bench README;
ArtRealmAI / kie.ai / TechFlow secondary write-ups (EA programme details only).
