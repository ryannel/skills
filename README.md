# ryannel/skills

Agent skills for image generation models — authoritative setup guides, prompting techniques, and workflow references for use with Claude Code and other agents.

[![skills.sh](https://skills.sh/b/ryannel/skills)](https://skills.sh)

## Skills

| Skill | Model | What it covers |
|---|---|---|
| [`flux-2`](./flux-2/) | FLUX.2 (Black Forest Labs) | ComfyUI setup, 4-part prompting, hex color control, ControlNet, PuLID face identity, BFL API, LoRA training |
| [`ideogram-4`](./ideogram-4/) | Ideogram 4 (Ideogram, Inc.) | JSON caption schema, typography, bbox layout, web app / hosted API / self-hosted open weights |
| [`z-image`](./z-image/) | Z-Image (Alibaba Tongyi) | ComfyUI multi-stage pipelines, Fun Union ControlNet, character LoRA via FaceDetailer, LoRA training |
| [`sdxl`](./sdxl/) | Stable Diffusion XL (Stability AI) | Finetune ecosystem, fast variants (Lightning/LCM/Hyper), ControlNet/IP-Adapter, photoreal prompting, LoRA training |

## Install

```bash
# Single skill
npx skills add ryannel/skills/flux-2

# All skills
npx skills add ryannel/skills
```
