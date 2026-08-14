# Krea 2 — Community-craft research report

Gathered 2026-07-07 by web-research subagent (named community sources). Open weights were ~2 weeks old at gathering time. Staged for the krea-2 skill; nothing here is published.

**Coverage caveat:** Reddit (r/StableDiffusion, r/comfyui) was blocked to the search crawler used — no Reddit threads directly verified. Named-source base: HN, Civitai, GitHub, HF, independent blogs. Where an item says "no consensus," that is the finding.

## 1. Reception & positioning

- **Overall verdict positive, benchmark-strong.** HN thread ~348 pts; [community — u/vunderba, HN "Krea 2: SOTA open-weights 12B image model"](https://news.ycombinator.com/item?id=48646659) reports Turbo scored "highest among locally hostable models" on his personal benchmark, but flags persistent "model killers": nine-pointed star, Count Rugen, overcrowded flat Earth prompts.
- **Sharpness controversy — the central aesthetic dispute.** [community — u/BoredPositron, HN](https://news.ycombinator.com/item?id=48646659) calls outputs "blurry, airbrushed" (blames Qwen VAE); Krea's mattnewton (in-thread) answers they deliberately avoided "hyper AI-look" over-sharpening; [community — u/mobiuscog, HN] says swapping in the **Wan 2.1 VAE** "solves this." Anti-default-look claim partially holds *as softness*, which some read as a defect.
- **Hosted ≠ open:** [Krea team — mattnewton, HN](https://news.ycombinator.com/item?id=48661328): **hosted Krea 2 Large was trained with the FLUX.2 VAE**; open weights use Qwen-Image VAE — real fidelity gap between hosted Large and open Turbo. No independent hosted-vs-open side-by-side yet.
- **vs rivals:** [community — Civitai author liutyi, "KREA 2 Turbo"](https://civitai.com/articles/31823/krea-2-turbo): comparable photoreal quality to ERNIE Image Turbo but worse at non-square ratios than ERNIE; behind Nano Banana 2 on art-style specificity; strong meme/template recognition; no ethnicity default in faces. [community — Civitai author nsfwVariant](https://civitai.com/models/2749367/krea-2-simple-gen-workflow-for-high-quality-realism-lots-of-info-and-tips): **Z-Image Base beats Krea 2 on facial expressiveness and hair, but is ~8× slower; Krea 2 wins on anatomy, animals, wide-aspect composition.** No substantive named Flux.2-dev/klein or Midjourney community shootout found yet — no consensus.
- Krea's own ["First experiments from the community"](https://www.krea.ai/blog/krea-2-first-experiments-from-the-community) [vendor-curated] showcases range across photoreal/fashion/graphic looks.

## 2. Prompting craft

- Official doctrine (long detailed prompts fine, quotes around text-to-render, style refs over style words) is in [krea-ai/krea-2 docs/prompting.md](https://github.com/krea-ai/krea-2/blob/main/docs/prompting.md). Community deltas:
- **Prompt enhancer actively hurts:** [community — 808charlie, Comfy-Org/ComfyUI issue #14631](https://github.com/Comfy-Org/ComfyUI/issues/14631): the default ComfyUI Krea-2 template's enhancer refuses benign prompts ("photo of a dog on a kitchen table" → ethics refusal); workaround is an abliterated Qwen3VL-4B, hampered by TextGenerate not loading sharded models. [community — lonecatone23, Civitai Pro Grade Workflow](https://civitai.com/models/2726952/krea-2-pro-grade-workflow-sfwnsfw-w-image-edit-and-low-vram-options) ships a GGUF **abliterated** Qwen enhancer for the same reason.
- **Realism levers:** nsfwVariant: model has "stronger bias for 3D renders / digital artwork" — photoreal prompts need explicit photographic framing. [community — amida168, kombitz.com Raw GGUF guide](https://www.kombitz.com/2026/07/04/how-to-use-krea-2-raw-gguf-workflow-in-comfyui/): add "natural skin texture, visible pores, subtle skin imperfections" to fight airbrushed skin.
- **Safety-filter quality tax (recurring theme):** nsfwVariant reports muted facial expressions and says bypass LoRAs improve *SFW* output; [community — nova452, ComfyUI-Conditioning-Rebalance](https://github.com/nova452/ComfyUI-Conditioning-Rebalance) claims the trained safety filter causes "quality dilution" his per-layer conditioning nodes bypass. liutyi independently: "only neutral and smile remain" of emotions. Three named sources converge — strongest community consensus so far.
- Creativity raw→high dial: no local-community reports found (hosted-UI feature) — no consensus.

## 3. Settings craft (deltas from official turbo 8-step/cfg1/euler/simple)

- **Steps:** liutyi tested to 12 — minimal gain past 8. [community — RaymondLuxuryYacht, Civitai "RLY Basic Photorealism"](https://civitai.com/articles/31794/rly-krea-2-turbo-basic-photorealism-workflow) goes *down*: res_2s/beta @ 4–5 steps for texture, er_sde/simple @ 4–9 for clean output.
- **CFG>1 on Turbo works:** nsfwVariant runs cfg 2.0 (doubles gen time, enables negative prompts). Turbo at cfg 1.0 ignores negatives — negative-prompt craft is effectively "raise cfg or use Rebalance nodes" (nova452's 06-29 update added negative prompting for edits).
- **Best-documented alternative recipe** (nsfwVariant): **Raw + Turbo-LoRA @ 0.6** instead of Turbo checkpoint ("WAY better" photoreal), two-stage: 6 steps res_2s/beta (deliberately undercooked, keeps expressiveness) → 2 steps deis_3m/bong_tangent @ 0.2 denoise; **Wan 2.1 FP32 VAE** instead of Qwen VAE.
- **Raw-as-inference:** amida168 (kombitz) runs Raw Q8 GGUF at **30 steps / cfg 4** (vs official 52/3.5) but finds Raw *more* airbrushed than Turbo — **direct disagreement** with nsfwVariant's Raw-preference (nsfwVariant adds the Turbo LoRA + Wan VAE, which likely explains the gap). No consensus on Raw-for-inference.
- Resolution: liutyi — solid at 1024 and native 2048, degrades at extreme ratios (1600×400); nsfwVariant — cinematic wide ratios a strength. Mild disagreement; both agree square/2K is safe.
- musubi inference: `--steps 8 --guidance_scale 1 --mu 1.15` ([kohya-ss/musubi-tuner docs/krea2.md](https://github.com/kohya-ss/musubi-tuner/blob/main/docs/krea2.md)).

## 4. VRAM & quantization

- **No city96 repo** — GGUF ecosystem is [gguf-org/krea-2-gguf](https://huggingface.co/gguf-org/krea-2-gguf), [vantagewithai Turbo](https://huggingface.co/vantagewithai/Krea-2-Turbo-GGUF)/[Raw](https://huggingface.co/vantagewithai/Krea-2-Raw-GGUF), [molbal/krea2-gguf](https://huggingface.co/molbal/krea2-gguf), [realrebelai/KREA-2_GGUFs](https://huggingface.co/realrebelai/KREA-2_GGUFs).
- Sizes (vantagewithai): Q2_K 4.9GB, Q4_K_M 7.5GB, Q6_K 10.6GB, Q8_0 13.7GB → roughly Q4 for 12GB cards, Q8 for 16–24GB, plus Qwen3-VL-4B TE (GGUF/offloadable). No per-quant quality shootout published yet — no consensus.
- fp8/int8: official Comfy fp8 files work day-0 ([Comfy blog](https://blog.comfy.org/p/krea-2-open-source-models-are-now)); nsfwVariant recommends **int8 "Convrot"** variant — ~2× faster than fp8 at equal quality (needs current ComfyUI, CUDA 13). liutyi: bf16 needs ~46GB unified memory. [community — u/Eisenstein, HN]: Koboldcpp rolling build runs Krea 2 (with Qwen3-VL + Wan2.1 VAE).

## 5. LoRA training

- **musubi-tuner:** day-0 experimental support ([kohya_tech on X](https://x.com/kohya_tech/status/2069562085592432738); [docs/krea2.md](https://github.com/kohya-ss/musubi-tuner/blob/main/docs/krea2.md)): dim/alpha 32, LR 1e-4, timestep `shift`, discrete_flow_shift 2.5 (or `krea2_shift` for bucketed multires), adamw8bit, fp8_base+fp8_scaled, blocks_to_swap ≤26; train Raw → sample/infer Turbo; `--turbo_dit` incompatible with blocks_to_swap.
- **ai-toolkit:** `arch: krea2`; ostris ships a [**de-distill training adapter**](https://huggingface.co/ostris/krea2_turbo_training_adapter) enabling **direct training on Turbo** for short runs (styles/concepts/characters) — and says turbo-direct "could yield better results" than Raw. **Live doctrine dispute: official/kohya say train-on-Raw-apply-on-Turbo; ostris offers a competing turbo-native path.** Early-adopter config (rank 32/alpha 32, LR 1e-4, ~1000 steps, qfloat8, validate at 8 steps) via [RunComfy trainer page](https://www.runcomfy.com/trainer/ai-toolkit/krea-2-turbo-lora-training) [weak — service docs].
- **Character recipe (best documented):** [community — JahJedi, HF krea2-character-lora-recipe](https://huggingface.co/JahJedi/krea2-character-lora-recipe): musubi on Raw, 474 imgs + 348 reg imgs, dim/alpha 32, LR 1e-4 fp32 AdamW, ~13k steps (~4.6h), captions "describe only what is visible"; identity held at weight 0.8 under heavy style-LoRA mixing — **train-on-Raw-apply-on-Turbo confirmed working in practice** by one named adopter. Also [bongobongo2020/krea2-character-lora-trainer](https://github.com/bongobongo2020/krea2-character-lora-trainer) (unexamined). Captioning doctrine beyond JahJedi: no consensus.
- Slider LoRAs already exist ([Civitai "[KREA 2] Detail Slider"](https://civitai.com/models/2729908/krea-2-detail-slider)).

## 6. Character / identity work

- **No PuLID/InstantID/IP-Adapter port exists.** Closest: nova452's [ComfyUI-Conditioning-Rebalance](https://github.com/nova452/ComfyUI-Conditioning-Rebalance) — "IP-Adapter-like" per-layer conditioning for image-reference editing via the Qwen3-VL tap; and [ostris/ComfyUI-Krea2-Ostris-Edit](https://github.com/ostris/ComfyUI-Krea2-Ostris-Edit) — up to **3 reference images** through Qwen3-VL encoder + model patch, paired-data edit LoRAs (~1,750 steps for a concept; [comfyui-wiki write-up](https://comfyui-wiki.com/en/news/2026-07-04-ai-toolkit-krea2-edit-training)). Identity today = character LoRA (§5). Krea CTO dvrp (HN): official edit models "coming."

## 7. Workflows & pipelines

- **Named workflows:** nsfwVariant "krea2_simple" (Raw+TurboLoRA two-stage, §3); lonecatone23 "Pro Grade v4.0" — Florence caption → abliterated-Qwen enhance → sample w/ detailer daemon → **SAM3 face/eye detailers** → Ultimate Upscaler → post FX; author admits its image-edit stage "is not as good as I thought it would be"; [A3 (a3xrfgb) "Krea 2 8-step workflow v1.5 Raw"](https://civitai.com/models/2725820/krea-2-8-step-workflow) (docs thin on page).
- **Mixed-model:** nsfwVariant inpaints Krea 2's problem areas (hair, fine patterns, halftone zones) with **Z-Image at 0.2 denoise**; [Civitai "Realistic Snapshot" LoRA](https://civitai.com/models/2268008/realistic-snapshot-z-image-turbo-krea-2) ships paired Z-Image-Turbo + Krea 2 versions — Krea2-as-peer-of-Z-Image is emerging as the standard pairing. Wan 2.1 VAE swap (§1) is itself a mixed-model trick.
- **img2img/edit status:** no official edit model; community edit = Ostris edit-LoRAs or Rebalance nodes; [Wan2GP issue #1952](https://github.com/deepbeepmeep/Wan2GP/issues/1952) shows demand for Rebalance-style editing in other frontends. Immature — no consensus workflow.

## 8. Failure modes (named reports)

- **Airbrushed/soft skin & blur** — liutyi, BoredPositron, amida168. Fixes: Wan2.1 VAE (mobiuscog, nsfwVariant), texture-words in prompt (amida168), int8/detailer passes (lonecatone23).
- **Halftone/grid artifacts, patchy noise on dark areas, ribbon/fabric degradation** — nsfwVariant (blames Qwen VAE grain; fix: FP32 Wan VAE, resolution change, or Z-Image inpaint), liutyi (dark-color stains).
- **Muted emotions / censorship damping** — liutyi + nsfwVariant + nova452 (fix: bypass LoRA / Rebalance nodes / noisier scheduler first stage).
- **Text rendering weak** — liutyi ("some text appears but not reliably"); official quote-marks tip only partial help.
- **Extreme aspect ratios degrade** — liutyi; **"pretty person" bias** — nsfwVariant. Seed-behavior lore: none published yet — no consensus.

## Two honest bottom lines

1. The most-replicated community insight: Krea 2's **safety tuning** and **soft VAE** are the two quality taxes, with named workarounds for both.
2. **LoRA doctrine is genuinely contested** right now — kohya/official Raw-first vs ostris Turbo+adapter — and only one named end-to-end character-LoRA success (JahJedi, Raw-path) exists to adjudicate it.
