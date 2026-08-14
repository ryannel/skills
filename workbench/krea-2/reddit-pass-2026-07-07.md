# Krea 2 — Reddit pass, 2026-07-07

Read directly via browser (old.reddit.com), r/StableDiffusion + r/comfyui, past month sorted by new. This pass closed the "Reddit unverified" gap from the original community report and produced material updates to the published skill (all folded in same day).

## New facts folded into the skill

- **Identity-edit LoRA** — `conradlocke/krea2-identity-edit` (r/SD, 153↑, day-of): instruction-based identity-preserving editing; unofficial fine-tune of Raw; requires `ComfyUI-Krea2Edit` node pack (dual conditioning: in-context VAE tokens + image-grounded Qwen3-VL encoding); two workflows ship. → characters.md §1/§3, SKILL.md.
- **Depth ControlNet** — Tanmay Patil's `Krea-2-depth-controlnet`, named in Krea's own 200k-downloads community roundup (posted by Krea account, r/SD). First structural control for the model. → SKILL.md suite table + limitations, mixed-model-recipes control stack.
- **Character LoRA recipe (AI-Toolkit)** — Any_Tea_3499 (r/SD, 132↑, 103 comments): LoKr factor 4, Automagic3, sigmoid, Balanced, LR 1e-4 + weight decay, 1024-only, ~50-image datasets, 2–3k steps; likeness rated above Z-Image across multiple characters; author explicitly retracts their 2-weeks-earlier "worse than Ideogram/ZIT at characters" verdict. Weakness: tattoos. → characters.md, lora-training.md §3/§6.
- **12 GB musubi style training** — urabewe (r/SD): full command published — musubi defaults + `--blocks_to_swap 18 --block_swap_h2d_only --block_swap_ring_size 1 --split_attn --gradient_checkpointing_cpu_offload`; 30-img datasets, ~1,200 steps, ~2 h on 3060 12 GB; LoRAs used at 1.0, no trigger. Also ships an HTML dataset-builder tool. → lora-training.md §2/§7.
- **AI-Toolkit Raw OOM on 24 GB** — Fast-Cash1522 (r/SD, SOLVED): Raw training OOMs on 3090 even in Low-VRAM mode until Layer Offloading ~10% (5% works, slightly faster); Turbo+adapter trained fine on same rig. → lora-training.md §3.
- **int8 convrot dispute** — speedup ~2× replicated down to a 1050 Ti [YeahYeah2992, r/comfyui] but ganrocks007 (r/SD, 3060) reports int8 loses complex-prompt adherence vs fp8. → setup-and-workflows.md §2, SKILL.md quant + contested points.
- **Sampler thread** — m0ran1 (r/SD): euler_ancestral/simple, 15 steps, cfg 1, 1536×1792 (alt: uni_pc_bh2) as a daily driver at higher res. → per-variant settings, setup-and-workflows §7b.
- **Moiré despite Wan VAE** — derTommygun (r/SD): moiré on hair/clothes with WAN VAE, Euler A 9 steps, on the Fascium checkpoint merge, LoRAs off. Checkpoint-merge ecosystem (Fascium, MysticXXX) now exists. → failure modes, setup-and-workflows §5.
- **Description-locked character sheets** — aurelm (r/comfyui, 51↑): exhaustive per-character description blocks repeated verbatim across scene prompts give near-identical characters with no LoRA; VLM splits a master prompt into per-scene prompts. → characters.md §3a.
- **Multi-character caption bleed** — krigeta1 (r/SD): multi-character LoRA holds under training-register captions, bleeds under creative prompts. → lora-training.md §5, characters.md §5.
- **Krea 2 gen → Klein 9B edit** — shootthesound's ComfyUI-Angelo (r/SD + r/comfyui). → mixed-model-recipes named recipes.
- **Detail-enhancer edit LoRA on the Ostris method** — sktksm (r/comfyui, 332↑): trigger "enhance this image"; experimental, weak on horizontal ratios, can shift lighting/colors. → characters.md §3.
- **Ecosystem misc:** ilker's 1,500+ style LoRAs (fal-Krea-2-Style-LoRAs) and AlperKTS Krea2_FP8, both from Krea's roundup; LoRAs add ~5–10 s/gen on Turbo [rarezin]; Mr Flow 512→realESRGAN-2× low-VRAM ladder [MFGREBEL]; "Krea2 Uncensored" workflow ecosystem is large (1,406↑ Tifa post); Krea2-vs-ZIT sentiment remains split (62↑/91 comments — some still find ZIT sharper).

## Notes

- The 12.9B param figure appears in community repo descriptions (conradlocke) — still not in official cards (12B); keep skill at 12B.
- civitai.red mirror links appearing alongside civitai.com — same content.
- A recent ComfyUI dynamic-VRAM regression (models reload from disk every run, 44↑ r/comfyui thread) hits Krea 2 users but is a ComfyUI bug, not model craft — not folded into the skill.
