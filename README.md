# ryannel/skills

Agent skills for image generation models — authoritative setup guides, prompting techniques, and workflow references for use with Claude Code and other agents.

[![skills.sh](https://skills.sh/b/ryannel/skills)](https://skills.sh)

## Skills

| Skill | Model | What it covers |
|---|---|---|
| [`flux-2`](./skills/flux-2/) | FLUX.2 (Black Forest Labs) | ComfyUI setup, 4-part prompting, hex color control, ControlNet, PuLID face identity, BFL API, LoRA training |
| [`ideogram-4`](./skills/ideogram-4/) | Ideogram 4 (Ideogram, Inc.) | JSON caption schema, typography, bbox layout, web app / hosted API / self-hosted open weights |
| [`z-image`](./skills/z-image/) | Z-Image (Alibaba Tongyi) | ComfyUI multi-stage pipelines, Fun Union ControlNet, character LoRA via FaceDetailer, LoRA training |
| [`sdxl`](./skills/sdxl/) | Stable Diffusion XL (Stability AI) | Finetune ecosystem, fast variants (Lightning/LCM/Hyper), ControlNet/IP-Adapter, photoreal prompting, LoRA training |
| [`image-production-workflows`](./skills/image-production-workflows/) | Cross-model | Multi-stage production pipelines (refine → detail → tiled upscale → finish), mixed-model handoffs between SDXL/Flux/Z-Image/Ideogram, regional prompting & inpainting craft, ComfyScript & workflows-as-code |

## Install

```bash
# Single skill
npx skills add ryannel/skills/flux-2

# All skills
npx skills add ryannel/skills
```
