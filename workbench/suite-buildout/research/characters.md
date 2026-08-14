# Research: consistent AI characters with local models — 2026-06-10

Deep-research report (web, named sources). Confidence: **[official]** = repo/model card/docs; **[community]** = named community author or established tutorial site; **[weak]** = SEO/content-farm or unverifiable. Contested points flagged.

## 1. The character LoRA pipeline end-to-end

**2026 consensus pipeline: one seed image → multi-angle dataset via an edit model → LoRA training in AI-Toolkit (Flux/Z-Image/Qwen) or kohya/OneTrainer (SDXL).** The "edit model as dataset factory" step is the big change since 2024; Qwen-Image-Edit is the de facto standard tool for it.

### Synthetic dataset from a single image
- Harmeet at WeirdWonderfulAI.art ("QWEN Image Edit can create Character Consistent LoRA Dataset," Oct 10 2025): one reference image + ~50 prompt variations (poses, clothing, backgrounds) through Qwen-Image-Edit in ComfyUI, then AI-Toolkit to train a Wan/Flux/Qwen or SDXL LoRA. **[community]** — https://weirdwonderfulai.art/comfyui/qwen-image-edit-can-create-character-consistent-lora-dataset/
- FloYo workflows: "Qwen Image Edit 2509 for LoRA Dataset" loops ~20 pre-written portrait prompts (profile L/R, three-quarter, Rembrandt lighting…); a "Qwen 2511 Edit — Single Image to Character Dataset" variant generates ~60 images → curate best ~30. **[community, weakly named]** — https://www.floyo.ai/workflows/-qwen-image-edit-2509-for-lora-datas-ac2829kggykc , https://www.floyo.ai/workflows/qwen-2511-edit-single-image-to-chara-65qytngb2sux
- **Mickmumpitz's Consistent Character Creator** (YouTube + free ComfyUI workflows; v1 Dec 2024 Flux/SDXL; v3.0 2025-26 rebuilt on Qwen-Image-Edit): generates a turnaround sheet (front/side/angled), expression libraries, relighting (IC-Light) from one input image — usable both as no-training consistency tool and LoRA fodder. Probably the single most-cited community workflow for the topic. **[community, strong]** — https://mickmumpitz.ai/posts/free-workflows-113743435 , https://www.runcomfy.com/comfyui-workflows/consistent-character-creator-3-0
- Stable Diffusion Art covers a "Multiple Angle" Qwen-Edit LoRA for rotating a character to dataset angles. **[community]** — https://stable-diffusion-art.com/qwen-image-edit-multiple-angle-lora/

### Dataset size/variety rules
**20–50 images**, deliberately varied in angle, expression, pose, lighting, framing (full-body/portrait/close-up); near-duplicates are the #1 overfit cause. Synthetic authors: "generate 60, keep best ~30; ~20–30 is the floor for face accuracy." **[community]** — https://civitai.com/articles/7777 , https://civitai.com/articles/21257 , https://civitai.com/articles/21114

### Captioning: caption-the-variables
Trigger token + captions for pose/background/lighting; do NOT caption the character's hair/face/signature outfit (those bind to the trigger). **[community, strong]** — https://civitai.com/articles/8487 , https://civitai.com/articles/12229
**Contested for Flux-family:** Civitai article 7203 ("Captions vs No-Captions") found caption-free/minimal works surprisingly well on Flux's stack; part of the community now skips captions for single-character Flux/Z-Image LoRAs. Solid doctrine for SDXL/Illustrious/Pony; actively debated for Flux/Qwen/Z-Image. **[community; contested]**. JoyCaption (natural language) + WD14 (tags) is the standard captioning tool pair — https://civitai.com/articles/25066

### Per-model tooling and hyperparameters
- **Ostris AI-Toolkit** = default trainer for Flux.1/.2, Qwen-Image, Wan, Z-Image. **[official]** — https://github.com/ostris/ai-toolkit
- **Z-Image (Turbo):** rank 8–16, LR 1e-4 (conservative 5e-5), ~2000–3000 steps for 15–25 images, 1024², batch 1–2; the AI-Toolkit **de-distillation training adapter is mandatory** for Turbo. **[community/official mix]** — https://huggingface.co/blog/content-and-code/training-a-lora-for-z-image-turbo , https://github.com/ostris/ai-toolkit/issues/550 (12 GB VRAM report)
- **Flux.1/Flux.2:** rank 16 typical for characters (32 high end), LR 1e-4–2e-4, 1000–3000 steps, 20–60 images at 1024². **[community]** — https://www.runcomfy.com/trainer/ai-toolkit/flux-2-dev-lora-training , official notebook: https://github.com/ostris/ai-toolkit/blob/main/notebooks/FLUX_1_dev_LoRA_Training.ipynb
- **SDXL (kohya/OneTrainer):** dim 16–32, alpha = dim/2 most-repeated; Prodigy at LR 1.0 the popular alternative. One honest Civitai author: "limited rational consensus" — folklore + experimentation. **[community; soft consensus — flag]** — https://civitai.com/articles/21257 , https://civitai.com/articles/5255 , https://civitai.com/articles/8737
- **SEO warning:** apatero.com character-LoRA pages rank highly but read as content farms — numbers roughly match, don't cite as authority. **[weak]**

## 2. Training-free identity tools, mid-2026 status

- **PuLID for Flux.2 (iFayens `ComfyUI-PuLID-Flux2`)** — first/only Flux.2 PuLID; supports Klein 4B/9B and Dev (best on Klein); weights `pulid_flux2_klein_v1/v2.safetensors` (https://huggingface.co/Fayens/Pulid-Flux2); strength 1.0–1.4; v0.6.2 as of 2026-03-21; img2img/body consistency on roadmap; calibration differs Base vs Distilled (issue #11). **[official repo]** — https://github.com/iFayens/ComfyUI-PuLID-Flux2
- **PuLID Flux.1:** maintained lldacing fork — https://github.com/lldacing/ComfyUI_PuLID_Flux_ll **[official]**
- **InstantID** still the SDXL go-to; IP-Adapter FaceID(-PlusV2) works but is widely held to underperform InstantID; both legacy-stable. **[official + community]** — https://huggingface.co/h94/IP-Adapter-FaceID , https://stable-diffusion-art.com/instantid/
- **HyperLoRA (ByteDance, CVPR 2025 Highlight)** — zero-shot *generation of LoRA weights* from a face photo, SDXL; official ComfyUI nodes; merges LoRA quality with adapter convenience. **[official]** — https://github.com/bytedance/ComfyUI-HyperLoRA , https://arxiv.org/html/2503.16944v1
- **ReActor 2025 rewrite drops InsightFace** (resolving the non-commercial license problem); adds ReSwapper + HyperSwap models. **[official]** — https://github.com/Gourieff/ComfyUI-ReActor
- **InfiniteYou / UNO / OmniGen2** still used; frontier moved to **UMO (ByteDance, Sept 2025, CVPR 2026)** — RL "matching reward" on UNO/OmniGen2 targeting **multi-identity confusion**; claims open-source SOTA for multi-ID. **[official]** — https://github.com/bytedance/UMO , https://github.com/katalist-ai/ComfyUI-InfiniteYou
- **LoRA vs adapter consensus:** adapters excel at one-shot *face* identity, blend lighting, no training — but degrade at extreme angles, drift with pose/background changes, don't capture body/outfit/mannerisms. Trained LoRA wins for whole-character consistency, stylisation, angle robustness; "none reach 100% face match." Best citable head-to-heads: MyAIForce. **[community, strong]** — https://myaiforce.com/flux-pulid-vs-ecomid-vs-instantid/ , https://myaiforce.com/hyperlora-vs-instantid-vs-pulid-vs-ace-plus/

## 3. Multi-reference / in-context editing as character engine

- **Flux.2 [dev]** (Nov 2025): up to 10 references via chained `ReferenceLatent`; ComfyUI day-0 templates. Tips: prefer Flux.2 dev over Kontext for character consistency; lock seeds; reorder/bypass conflicting references. **[official]** — https://docs.comfy.org/tutorials/flux/flux-2-dev
- **Qwen-Image-Edit 2509 → 2511:** 2509 added multi-image (1–3 inputs); **2511** (Dec 2025) explicitly improved character consistency and multi-person editing; native ComfyUI workflows. The workhorse of dataset generation, outfit swaps, character-in-new-scene. **[official]** — https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit-2511 , https://github.com/QwenLM/Qwen-Image
- Hosted comparison: Nano Banana (Pro) ≈ Flux.1 Kontext, slightly ahead of Qwen on detail preservation; but a **fine-tuned** Qwen-Image-Edit beat Nano-Banana on a specific task (Oxen.ai). **[community]** — https://diffusiondoodles.substack.com/p/qwen-image-edit-vs-flux1-kontext , https://ghost.oxen.ai/fine-tuned-qwen-image-edit-vs-nano-banana-and-flux-kontext-dev/

## 4. FaceDetailer-stage LoRA swap

**Established, well-documented, folklore-grade rather than canonized.** Generate base *without* the character LoRA (avoiding its composition/body biases), apply LoRA only in the FaceDetailer/ADetailer inpaint pass.
- MyAIForce has the two clearest writeups (A1111-ADetailer; ComfyUI-FaceDetailer): character LoRA "messes up bodies at full strength"; detailer-only fixes it. **[community, strong]** — https://myaiforce.com/best-way-to-use-lora/ , https://myaiforce.com/face-swapping-in-comfyui-with-lora/
- **ADetailer per-face LoRA routing via `[SEP]`** ("Bobby <lora:bobby:1> [SEP] Tracy <lora:tracy:1>") — standard multi-character extension. **[official discussion]** — https://github.com/Bing-su/adetailer/discussions/533
- Flux-pipeline equivalents on Civitai, e.g. https://civitai.com/models/954879 **[community]**

## 5. Consistency beyond the face

- **Multi-outfit LoRAs:** Khanykov01's "Comprehensive Multi-Outfit LoRA Guide" — unique trigger per outfit, visually distinct outfits, balanced per-outfit images, **practical ceiling ~6 outfits per LoRA**. **[community, strong]** — https://civitai.com/articles/6990 ; broader: https://civitai.com/articles/680
- **Edit-model wardrobe transfer is replacing wardrobe LoRAs** for one-offs: Qwen-Image-Edit 2511 multi-image (image 1 = character, image 2 = outfit). **[community/official]** — https://www.nextdiffusion.ai/tutorials/consistent-outfit-changes-with-multi-qwen-image-edit-2511-in-comfyui
- **Multi-character scenes:** attribute bleed remains the named pain; mitigations layered: regional prompting / attention-couple masks with per-region LoRA, `[SEP]`-routed detailer passes, and model-level (Qwen-Edit 2511, UMO). **[community + official]** — https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues/17013

## 6. Failure modes and accepted fixes

- **Identity collapse at angle extremes:** front-heavy datasets; fix = synthesize profile/three-quarter/back views via Qwen-Edit angle prompts or angle LoRAs. Adapters drift hardest here — standard argument for LoRA. **[community]**
- **"Same face" / overfit rigidity:** near-identical shots, too many steps; fix = cut steps, increase pose/expression/lighting variety, regularization images, fixed-seed samples during training. **[community]** — https://civitai.com/articles/18443
- **Expression lock-in:** dataset's dominant expression absorbed; fix = deliberate expression variety (Mickmumpitz generates expression libraries for this). — https://civitai.com/articles/4563
- **Style bleed from character LoRAs:** standout fix = **block-weighted LoRA application** — in SDXL, style lives mostly in OUT1 (+IN08) attention blocks, subject in OUT0; zero style blocks at inference (`lbw=` / Inspire-Pack LoraLoaderBlockWeight). No equivalent block map established for Flux/Z-Image DiTs — gap worth flagging. **[community, strong]** — https://civitai.com/articles/5301
- **Multi-character identity bleed:** layered defense (regional masks → per-face detailer LoRAs → 2511/UMO-class models); no single tool solves it. **[community consensus; how well regional LoRA masking works on DiTs is contested]**

## Cross-cutting takeaways

1. Two complementary shapes: **edit-model character engine** (no training) and **LoRA pipeline**; the community increasingly chains them (edit model builds the dataset).
2. Hyperparameter "consensus" is real but soft — present numbers as starting points.
3. Captioning doctrine forks by model family (tags+trigger for SDXL-era; minimal/natural-language, even captionless, for Flux/Z-Image) — genuinely contested, surface honestly.
4. Strongest named authors: Mickmumpitz, Harmeet/WeirdWonderfulAI, MyAIForce, Khanykov01 (Civitai), Ostris, iFayens, ByteDance research repos (HyperLoRA/InfiniteYou/UNO/UMO). Banodoco threads are Discord-only — unverified channel rather than absent.
