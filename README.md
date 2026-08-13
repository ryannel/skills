# ryannel/skills

Agent skills for generative media models — authoritative setup guides, prompting techniques, and production workflow references for use with Claude Code and other agents.

Covers **image** and **video** models. The image-to-video handoff — lock a still with an image skill, then drive it with a video model — is why both live in one marketplace.

[![skills.sh](https://skills.sh/b/ryannel/skills)](https://skills.sh)

## Skills

| Skill | Model | What it covers |
|---|---|---|
| [`flux-2`](./skills/flux-2/) | FLUX.2 (Black Forest Labs) | ComfyUI setup, 4-part prompting, hex color control, ControlNet, PuLID face identity, BFL API, LoRA training |
| [`ideogram-4`](./skills/ideogram-4/) | Ideogram 4 (Ideogram, Inc.) | JSON caption schema, typography, bbox layout, web app / hosted API / self-hosted open weights |
| [`z-image`](./skills/z-image/) | Z-Image (Alibaba Tongyi) | ComfyUI multi-stage pipelines, Fun Union ControlNet, character LoRA via FaceDetailer, LoRA training |
| [`sdxl`](./skills/sdxl/) | Stable Diffusion XL (Stability AI) | Finetune ecosystem, fast variants (Lightning/LCM/Hyper), ControlNet/IP-Adapter, photoreal prompting, LoRA training |
| [`krea-2`](./skills/krea-2/) | Krea 2 (Krea AI) | Raw/Turbo open weights + hosted Medium/Large, ComfyUI setup, style references & style LoRAs, the anti-AI-look craft (Wan VAE swap), train-on-Raw/run-on-Turbo LoRA training, Krea API & fal |
| [`wan-2-2`](./skills/wan-2-2/) | Wan 2.2 (Alibaba Tongyi) — **video** | Task modes (I2V/T2V/FLF2V/S2V/Animate), the two-expert MoE wiring, motion & camera control (Fun Camera/Control/InP, VACE), the lightx2v speed LoRAs and their slow-motion tax, two-LoRA training, the image-to-video handoff, temporal failure modes |
| [`minimax-h3`](./skills/minimax-h3/) | MiniMax H3 — **video + native audio** | Omni-modal video with synchronised stereo audio in one pass; **licence territory exclusions (US/EU/UK/KR) up front**; what's open vs hosted-only; FL2VA/Ref2VA modes, reference-audio conditioning, dual video+audio VAE wiring, prompting the soundtrack |
| [`character-lora-training`](./skills/character-lora-training/) | Cross-model | Character LoRA craft that transfers: caption-the-residual, the 8-point coverage protocol, synthetic dataset factories, evaluation and overfit signals — plus **adult/NSFW work as a first-class case** (base-model selection, explicit captioning, anatomy failures) and what makes a LoRA publishable at all (real-person likeness rules, NCII law) |
| [`comfyui-on-runpod`](./skills/comfyui-on-runpod/) | Infrastructure | Running ComfyUI on rented GPUs so a fresh instance finds every model: the dual mount root (`/workspace` vs `/runpod-volume`), `extra_model_paths.yaml`, volume layout by loader, model manifests, pod vs serverless, API-format workflow deployment, cost guards |
| [`image-production-workflows`](./skills/image-production-workflows/) | Cross-model | Multi-stage production pipelines (refine → detail → tiled upscale → finish), mixed-model handoffs between SDXL/Flux/Z-Image/Ideogram, regional prompting & inpainting craft, ComfyScript & workflows-as-code |

## Install

```bash
# Single skill
npx skills add ryannel/skills/flux-2

# All skills
npx skills add ryannel/skills
```
