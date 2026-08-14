# Research: professional multi-stage & mixed-model pipelines (ComfyUI / diffusers / ComfyScript) — 2026-06-10

Deep-research report (web, named sources). Confidence: **[official]** = vendor/repo docs; **[community-strong]** = named author/site with specifics; **[weak]** = aggregator/SEO/unverified.

## 1. The canonical multi-stage pipeline, 2026

Consensus ladder: **base gen → hires/latent second pass → detailers → tiled diffusion upscale → final GAN/restorer upscale**; rungs climbed depend on family.

- **Hires second pass:** ComfyUI's own 2-pass examples define it (generate low-res → upscale → re-sample partial denoise) **[official]** — https://comfyanonymous.github.io/ComfyUI_examples/2_pass_txt2img/ . Latent upscale wants denoise ≥ ~0.5 to avoid interpolation artifacts; pixel-space upscale tolerates lower — SDXL second pass 0.25–0.35 (Tech Tactician **[community-strong]**); sandner.art's Latent Interpolate Upscale blends original+upscaled latents to run ~0.55 denoise without composition loss **[community-strong]**. DiT models (Flux/Z-Image) often skip classic hires (native 1–2 MP); their second pass is a refine/detail pass.
- **Detailers:** Impact Pack `FaceDetailer` (detect → crop → upscale crop → re-sample → stitch) standard, model-agnostic **[official]** — https://github.com/ltdrdata/ComfyUI-Impact-Pack . Settings consensus: denoise ~0.4–0.5; `bbox_crop_factor` default 3, many drop to ~1.3–2; `guide_size` 512 / `max_size` 1024 (myByways **[community-strong]**). Canonical SDXL stage order: Civitai 15956 **[community-strong]**.
- **Tiled upscale:** `UltimateSDUpscale` (ssitu) is the workhorse — seam-fix modes (none/band-pass/half-tile/half-tile+intersections), tile overlap blending. **For DiTs: TTPlanet's TTP Toolset** — tiles the image and **captions each tile** for per-tile conditioning ("for DiT models… Flux, Hunyuan, SD3"); the anti-hallucination trick for tiled DiT upscales **[official]** — https://github.com/TTPlanetPig/Comfyui_TTP_Toolset . TTPlanet also ships the de-facto SDXL tile ControlNet (TTPLanet_SDXL_Controlnet_Tile_Realistic) **[official]**. `shiimizu/ComfyUI-TiledDiffusion` (MultiDiffusion + tiled VAE) the other live option **[official]**.
- **Final restorer — SUPIR semi-retired, SeedVR2 the 2026 default.** kijai's ComfyUI-SUPIR README carries a "**FINAL update**" notice — merged into ComfyUI core, wrapper frozen **[official]**. SUPIR needs an SDXL checkpoint + 32 GB+ system RAM — stale-but-functional. **SeedVR2** (ByteDance one-step diffusion restorer): official ComfyUI node, 3B/7B, FP8/GGUF **[official]** — https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler . MyAIForce found SeedVR2+SRPO beats SUPIR+SRPO on skin texture **[community-strong]** — https://myaiforce.com/seedvr2-srpo-upscaling/ . ESRGAN models (4x-UltraSharp, Remacri, 4xNomos) survive as the cheap deterministic step before/after diffusion upscale.
- **Per-family stage usage (synthesis):** SDXL/Illustrious/Pony run the full ladder (hires → detailer → USDU). Flux/Z-Image: base → refine/detail pass → TTP or USDU tiled → SeedVR2; latent hires rarer (distillation + native res).

## 2. Mixed-model pipelines (cross-family handoffs) — now mainstream, both directions

- **SDXL base → Z-Image-Turbo refine:** Cordina's "**ZIT Refiner workflows – SDXL v1**" (Civitai, Jan 2026): SDXL base (IntoRealism Ultra v8) → ZIT pass "to add realism" → detailer subgroups → upscale+sharpen **[community-strong, named]** — https://civitai.com/models/2337188
- **SDXL/Pony → Flux.2 Klein refine:** Enzino's "**Flux Klein IMG2IMG Workflow**": img2img with Klein for "more natural rendering… better anatomical consistency, reduced SDXL artifacts" **[community-strong]** — https://civitai.com/models/2401644
- **Flux → SDXL finetune refine (reverse, for texture/skin):** decode Flux output → img2img through a realism SDXL checkpoint (RealVis-class) at ~0.3–0.55 denoise **[weak — video-tutorial mirror, widely replicated]**
- **Rationale:** SDXL owns the deepest ControlNet/LoRA/IPAdapter ecosystem → "compose with SDXL control stack → refine with a DiT" and "generate with DiT → texture with SDXL finetune" both common. Civitai's "Modern Easy SDXL (2026 Base for Flux & Z-Image)" positions SDXL as the controllable front-end **[community-strong]** — https://civitai.com/models/2279672
- **Ideogram-4 for typography:** typography leader (quoted-string text, editable layers, Magic Fill) **[official]**. The cross-model pattern (Ideogram text plate → mask-preserve → restyle with SDXL/Flux inpaint, or inpaint text regions with Ideogram) is practiced but **no canonical named workflow found — present as inferred craft [weak]**.

**Handoff rules (well-sourced):**
1. **Different families = incompatible latent spaces.** ComfyUI's `LatentFormat` assigns each family its own scale/shift; Flux.2 uses its own VAE entirely — latents from one family cannot feed another's sampler/VAE (DeepWiki ComfyUI VAE/latent formats **[derived-official]**; comfyui.dev: Flux2 VAE with SD/SDXL/Flux1 "won't work"/garbage **[community-strong]**). **Every cross-family handoff = VAE Decode (A) → pixels → VAE Encode (B) → sample.** All named workflows above do exactly this.
2. **Identity-preserving refine denoise band ≈ 0.2–0.5.** Detailer default 0.5, drop to 0.35–0.45 to keep identity; >0.6 "compromises composition, facial features"; <~0.2–0.25 contributes mostly texture. **[community-strong, convergent]**
3. **Match resolution to the refining model's native range** before encoding (don't hand 4 MP raw to SDXL — tile or downscale-refine-upscale).

## 3. Structural control stack, mid-2026

- **SDXL:** mature. **xinsir controlnet-union-sdxl-1.0 (ProMax)** consensus best — 10+ types + tile/inpaint/outpaint in one checkpoint **[official]**; xinsir's further training **stalled for GPU funding** (frozen but stable) — https://huggingface.co/xinsir/controlnet-union-sdxl-1.0
- **Flux.2:** alibaba-pai FLUX.2-dev-Fun-Controlnet-Union; `controlnet_conditioning_scale` 0.65–0.80; Klein support unconfirmed; ComfyUI via community wrapper (bryanmcguire) **[official + community]**
- **Z-Image:** Z-Image-Turbo-Fun-Controlnet-Union (Turbo-only), v2.1 added gray/recolor; official ComfyUI template exists **[official]**
- **Multiple ControlNets:** chain Apply nodes with per-CN strength/start/end; union models reduce the need.
- **IPAdapter:** cubiq's `ComfyUI_IPAdapter_plus` **maintenance-only since 2025-04-14** **[official — flag stale]**; Comfy-Org maintains a reference implementation (comfyorg/comfyui-ipadapter). For DiTs, style transfer has shifted to edit-models (Kontext/Klein, Qwen-Image-Edit) and Redux-style adapters.
- **Regional prompting:** ComfyUI core merged **Flux attention masking** (PR #5942) **[official]**; mask-based regional conditioning is the only method that works on Flux — old Regional Prompter is SD1.5/SDXL-only (Apatero regional guide **[community-strong]**); Flux-specific: attashe/ComfyUI-FluxRegionAttention, RES4LYF FluxRegionalPrompt **[community]**
- **Inpainting craft:** **lquesada ComfyUI-Inpaint-CropAndStitch** (crop masked region → sample at native res → stitch), mirrored under Comfy org **[official]**; best practice `InpaintModelConditioning` (not VAE-Encode-for-inpaint) so denoise <1.0 works; resize crop to 1024². **Differential Diffusion is a core node**: gradient mask → per-pixel denoise; recipe = Gaussian Blur Mask + DifferentialDiffusion + InpaintModelConditioning (nomadoor **[community-strong]**). Acly's inpaint nodes (Fooocus head, LaMa pre-fill) current for SDXL **[official]**.

## 4. Workflows-as-code

- **ComfyScript is alive:** Chaoses-Ib/ComfyScript v0.6.0 (2025-11-19, ComfyUI v3 schema, Python 3.14), v0.6.1 2025-11-20; ~680 stars. Modes: **virtual** (builds workflow JSON, submits to server — works remote), **real** (nodes as plain Python functions), **transpiler** (workflow JSON → Python). Single maintainer — **pin versions in production**. **[official]** — https://github.com/Chaoses-Ib/ComfyScript
- **Native route (most production-proven):** Workflow menu → **Export (API)** → POST to `/prompt`, WebSocket progress (ViewComfy production guide; timlrx standalone-script writeup **[community-strong]**).
- **comfy-cli** (Comfy-Org, official): run workflows from CLI, convert GUI↔API JSON, manage models/queue — the standard batch driver.
- **Hosted/parametrized:** ComfyDeploy, RunComfy serverless, Baseten/Cerebrium wrappers **[official-vendor]**.
- **diffusers = the code-first alternative:** official multi-stage support (SDXL base+refiner; ControlNet+PAG; IP-Adapter+PAG). Cross-model handoff trivially explicit: `pipe_a(...).images → pipe_b(image=..., strength=0.3)` — pixels by construction.

## 5. Color & consistency management

- **Tiled seams:** USDU seam-fix modes + overlap; TTP per-tile captioning reduces hallucination; consistent global prompt across tiles.
- **Color shift between passes:** **ColorMatch node (KJNodes**, mkl/hm-mvgd-hm) applied after refine/upscale against the pre-pass image; ThetaCursed's HiresFix-Ultra bundles histogram color correction because VAE round-trips and second samplers drift color **[community-strong]**. Each VAE decode/encode cycle compounds drift — **color-match once at the end against the composition reference.**
- **Seed/composition stability:** fixed seeds + low denoise bands; rgthree global Seed node for cross-stage reuse.
- **Detail tricks still current:** **ComfyUI-Detail-Daemon** (Jonseed — Multiply Sigmas, Lying Sigma Sampler; works on Flux/SDXL/SD1.5) **[official]**; **PAG not obsolete** — core PerturbedAttentionGuidance node; pamparamm pack (PAG/SEG/NAG/FDG) updated 2025; used sparingly with distilled models.

## 6. What professional users add

- **rgthree-comfy:** Context/Context Switch pipes, Fast Muter, Power Lora Loader, global Seed — de-facto plumbing standard; muting+switches let one mega-workflow run many configs **[official]**.
- **Native Subgraphs** (official release 2025-08-07, frontend ≥1.24.3): package stage-blocks (base/refine/detail/upscale) into nested reusable nodes — replaced old group-node convention; how Civitai mega-workflows are organized **[official]** — https://blog.comfy.org/p/subgraph-official-release
- **Wildcards/dynamic prompts at scale:** Impact Pack `{a|b|c}` + `__wildcard__`; adieyal/comfyui-dynamicprompts (random + combinatorial). Civitai "Wildcard workflows (Pony, SDXL, Illustrious, Flux, Qwen, Z-Image Turbo)" — same harness across six families **[community-strong]** — https://civitai.com/models/2149956
- **Queue automation/QC:** comfy-cli or raw `/prompt` API, auto-incrementing seeds, WebSocket monitoring. Formalized batch QC is ad-hoc (grids + human cull) — **thin sourcing, flag**.
- **Community hubs:** Civitai (distribution), r/StableDiffusion + r/comfyui (consensus), **Banodoco Discord** (live workflow R&D).

## Staleness flags

| Tool | Status |
|---|---|
| SUPIR (kijai) | Frozen ("FINAL update"); merged into ComfyUI core; superseded for most uses by SeedVR2 |
| cubiq IPAdapter_plus | Maintenance-only since 2025-04-14; comfyorg fork is the maintained reference |
| xinsir ControlNet | Training halted (GPU funding); ProMax remains SDXL SOTA |
| ComfyScript | Maintained (v0.6.1, Nov 2025), single maintainer — pin versions |
| Ideogram→local inpaint handoff | Practiced, no canonical named workflow — present as inferred craft |
