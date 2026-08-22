# Anima — primary-source research

Compiled 2026-08-22. All facts tagged `[official]` / `[official-via-docs]` / `[community — named]` / `[inferred]` / `[contested]` per the media-model-skill provenance discipline. WebFetch summaries are the retrieval mechanism used throughout (no browser MCP per instructions); where a quote is reported as verbatim by WebFetch it is presented in quotes below, but a human author should re-open the HF README directly before publishing to confirm exact wording, since WebFetch passes content through a summarizing model.

## Identity & provenance

- **Anima** is a 2 billion parameter text-to-image latent diffusion model published by **CircleStone Labs** (CircleStone Labs LLC), in partnership with **Comfy Org**. `[official]` — https://huggingface.co/circlestone-labs/Anima
- It is explicitly a **"Derivative Model" of NVIDIA's Cosmos-Predict2-2B-Text2Image** — stated on the model card, and this derivation is why the model is also bound by the NVIDIA Open Model License Agreement wherever it applies to Derivative Models. `[official]` — https://huggingface.co/circlestone-labs/Anima
- **Comfy Org's role is funding/distribution, not co-training.** Per the Civitai explainer article: *"ComfyUI themselves sponsored this model on the premise that it is 'open,'"* with grant recipients retaining control over their own model and license. `[community — named, Civitai article]` — https://civitai.com/articles/26217/anima-what-is-anima. This is corroborated by a HF discussion citing a **$1M Comfy Open AI grant** for open-source anime-model work, part of Comfy Org's broader ~$48M VC raise. `[community — HF discussion thread]` — https://huggingface.co/circlestone-labs/Anima/discussions/185, and a LinkedIn post titled "Comfy Announces $1M Open AI Grant for Japanese Anime..." `[community]` — https://www.linkedin.com/posts/yolandyan_im-excited-to-announce-our-1m-comfy-open-activity-7424852466598375424-MLKH. **Could not find a blog.comfy.org post directly confirming grant terms** — treat the exact CircleStone/Comfy Org division of labor as sourced from secondary community accounts, not a primary Comfy Org statement.
- Contact for commercial licensing is listed as **tdrussell@circlestone.ai** `[official-via-docs]` — the same "tdrussell" who authors `diffusion-pipe`, suggesting personnel overlap between CircleStone Labs and established open LoRA-training tooling, though this is not stated outright anywhere `[inferred]`.
- **Release timeline:** preview available from **January 2026**; official **Anima-Base** release **May 15, 2026**. `[community — GIGAZINE]` https://gigazine.net/gsc_news/en/20260515-anima-image-generation-ai/ — GIGAZINE also frames it as running "locally on any PC that can handle SDXL or Illustrious-type models," i.e. positioned as a drop-in-cost peer to SDXL-class anime finetunes, not more expensive.
- **Name collision warning respected:** confirmed via the CircleStone Labs / Comfy Org attribution on every source above; this is not the unrelated "Anima" avatar/wellness apps that also rank for the bare word.

## Conditioning class (decisive)

This is the one axis the brief calls out as needing confirmation rather than inference, because a single community prompt (`(split screen, multiple views:1.2)`) suggested tag-weighted CLIP-style conditioning. **Confirmed from primary sources: the suggestion was right about the prompt dialect but the encoder itself is not CLIP — it's an LLM.**

- **Text encoder: Qwen-3 0.6B**, shipped as `qwen_3_06b_base.safetensors`, loaded into `ComfyUI/models/text_encoders/`. `[official]` — model card via https://huggingface.co/circlestone-labs/Anima and the official ComfyUI tutorial https://docs.comfy.org/tutorials/image/anima/anima
- **There is an LLM adapter network sitting between the Qwen3 encoder and the diffusion backbone.** The model card explicitly warns finetuners: *"Don't train the LLM adapter"* because it "has an outsized influence on the generated images." `[official]` A HF discussion about a hypothetical Cosmos 3 upgrade path adds that Cosmos 3's own encoder (Qwen3-VL) "eliminat[es] Anima's current need for an external llm_adapter network" — confirming, from the community's technical framing, that the *current* Anima architecture routes Qwen3-0.6B output through a dedicated adapter rather than feeding it straight into cross-attention. `[community — HF discussion, technically literate]` https://huggingface.co/circlestone-labs/Anima/discussions/185
- **One inconsistent secondary claim, NOT confirmed:** a ModelScope DiffSynth-Studio docs page, retrieved via WebFetch, described a "secondary encoder: T5-XXL tokenizer from Stability AI's SD3.5 Large." This does not appear anywhere else (not in the HF model card, not in the ComfyUI docs, not in the licensing/architecture discussions) and looks likely to be either a DiffSynth integration detail unrelated to CircleStone Labs' own release, or a WebFetch summarization artifact pulling from adjacent framework documentation. **Flag this and do not carry it into the skill without re-verifying directly against the DiffSynth page and Anima's actual `text_encoders` config.** `[flagged — re-verify]`
- **VAE: Qwen-Image VAE**, `qwen_image_vae.safetensors`, into `ComfyUI/models/vae/`. `[official]`
- **Prompt dialect is Danbooru-style tags, natural language, or a combination — trained on both, by design.** Verbatim per the model card (as retrieved): captioning style is *"Danbooru-style tags, natural language captions, and combinations."* The GIGAZINE piece independently confirms: *"supports both tags and natural language processing."* `[official]` + `[community — corroborating]`
- **Tag dialect is Danbooru, not e621.** The recommended tag ordering is `[quality/meta/year/safety tags] [1girl/1boy/1other count] [character] [series] [artist] [general tags]`, with quality/safety tokens like `score_7`, `safe`, `masterpiece`, `best quality` (Danbooru/booru-style rating and aesthetic tags, the same family as Pony/Illustrious dialect) — not e621 species/rating tag conventions. `[official]`
- Style notes from the card: lowercase tags, spaces instead of underscores, artist tags need an `@` prefix (e.g. `@artist_name`), and the model is trained with **tag dropout** so a prompt needn't enumerate every applicable tag. `[official]`
- **Natural-language prompts need a minimum of ~2 sentences** for best results, per the card. `[official]` This matters for the skill's "one rule" candidate: Anima is bilingual between tag-lists and prose in a way none of the repo's existing five ground-truth skills are — z-image is sentence-only, sdxl-family is tag-only.
- **Attention weighting syntax is confirmed supported, with a stated caveat:** the card states verbatim (as retrieved), *"Prompt weighting works, but needs a weight higher than typically used for SDXL. Example: `(chibi:2)`."* `[official]` This directly validates and refines the workbench brief's community observation: `(split screen, multiple views:1.2)` is real ComfyUI-standard weighting syntax, but a weight of `1.2` is on the *low* end of what Anima's own documentation recommends (`(chibi:2)` as the worked example) — so that community prompt may itself be under-weighted by Anima's own stated norms, worth flagging in the prompting guide.
- **Verdict:** Anima is **not** a CLIP-conditioned model in the SDXL/Illustrious/Pony sense, and it is **not** a pure natural-language LLM-encoder model in the Flux/Z-Image/Krea sense either. It is a **third, hybrid class**: an LLM text encoder (Qwen3-0.6B) via a dedicated adapter, deliberately trained on booru-tag captions (with natural-language captions also in the mix) so that it accepts weighted Danbooru-style tag syntax as a first-class prompt dialect, on top of natural sentences. This falsifies the doctrine table's default expectation that "LLM/T5 encoder → natural sentences, no weighting" — Anima is the exception the media-model-skill doctrine explicitly warns to watch for ("state the relevant cell with its mechanism," "a plausible-looking table can override research it shouldn't"). An author should present Anima's prompting guide as **primarily tag-based (booru dialect, Danbooru-style, `score_x`/`safe` quality tags, weighting syntax at higher-than-SDXL weights)**, with natural-language prompting as a supported secondary mode requiring ≥2 sentences — not the reverse.

## Architecture & checkpoints

- **Parameter count: 2 billion**, stated consistently across the HF model card, ComfyUI docs, and every secondary source. `[official]`
- **Architecture family: derivative of Cosmos-Predict2-2B-Text2Image (NVIDIA).** Cosmos-Predict2 is a flow-matching diffusion transformer (DiT) family, so Anima is very likely DiT-based `[inferred from base-model lineage — not independently confirmed as "DiT" in Anima's own docs]`. No source I could reach states "DiT" or "UNet" outright for Anima itself; the stable-diffusion.cpp GitHub feature-request issue (#1245) that would be the natural place for this detail contains no architecture discussion at all. **Flag architecture family as inferred, not officially stated in Anima's own materials.**
- **Diffusers pipeline class:** `AnimaImagePipeline`, per a ModelScope DiffSynth-Studio integration doc (`AnimaImagePipeline.from_pretrained(...)`, default `height`/`width` 1024, dimensions must be multiples of 16). `[community/third-party integration — re-verify against circlestone-labs' own diffusers repo, e.g. `circlestone-labs/Anima-Base-v1.0-Diffusers`, before citing as canonical]`
- **Checkpoint / version history — more than one release:**
  - **Preview** (available from Jan 2026): `anima-preview3-base.safetensors` — at least a third preview iteration existed before the official release. `[official-via-docs]`
  - **Anima-Base v1.0** (official release, May 15 2026): `anima-base-v1.0.safetensors` — "maximum flexibility," described by the card as intentionally "plain and neutral" in default style, i.e. not aesthetically tuned. `[official]`
  - **Anima-Aesthetic** v1.0 and v1.0b — refined-quality variants layered on the base. `[official-via-docs]`
  - **Anima-Turbo** — a distilled fast variant: **CFG 1, 8–12 steps** (vs. base's 30–50 steps / CFG 4–5). `[official]`
  - A **diffusers repackage** exists: `circlestone-labs/Anima-Base-v1.0-Diffusers`. `[official, HF repo listing]`
  - A **third-party quantization**: `silveroxides/Anima-Quantized`. `[community]`
  - One listing/title in the wild refers to "**Anima-2.9B**" (a "How To Install" blog post) — this conflicts with the 2B figure used everywhere official. Not resolved; likely either a rounding/marketing inconsistency in a low-authority blog or a reference to a specific checkpoint variant with slightly different param count. **Flag as unresolved, do not state 2.9B as fact.** `[flagged — re-verify]`
  - Community anticipates a future **Cosmos 3** based version (Edge 4B variant floated as most likely), not yet released as of 2026-08-22. `[community — speculative]`

## Licence

**CircleStone Labs Non-Commercial License v1.2**, plus an inherited NVIDIA Open Model License obligation via the Cosmos-Predict2 derivation. Verbatim/near-verbatim from the license file (as retrieved):

- Use permitted **"solely for your Non-Commercial Purposes."** Commercial activity is defined to include "(a) for revenue-generating activity, (b) in direct interactions with or that has impact on third-party end users, or (c) to train, fine tune, or distill other models for commercial use."
- **Explicit carve-out: individuals may sell what they make with it.** "Persons operating in an individual capacity may sell Derivatives owned or created by them" — this covers selling generated images, taking paid commissions, and even selling derivative model weights created by an individual.
- Disallowed: **hosting the model behind a paid API** without a separate commercial license (contact tdrussell@circlestone.ai).
- Content restriction: prohibits generating **"unlawful content, including child sexual abuse material, or non-consensual intimate images."** No further explicit general NSFW/adult-content policy stated in the license text itself — i.e., adult content generation is not banned outright, only CSAM and non-consensual intimate imagery specifically. `[official]`
- Redistribution requires passing along the full license text, an attribution notice ("licensed by CircleStone Labs LLC under the CircleStone Non-Commercial License"), marking modifications, and not implying official CircleStone endorsement of derivatives.
- **Practical one-line summary for the skill:** free for personal/non-commercial use and even individual commercial sales of outputs/derivatives, but a business cannot build a paid product or API on the base weights without a separate license from CircleStone Labs — and the model additionally carries NVIDIA's Open Model License terms via its Cosmos-Predict2 lineage.

Source: https://huggingface.co/circlestone-labs/Anima/blob/main/LICENSE.md `[official]`

## Constraints (resolution / VRAM / sampler defaults)

- **Native resolution range:** 512² to 1536² pixels (i.e., trained across a wide bucket range, not fixed to one native size); diffusers default example uses 1024×1024, dimensions must be multiples of 16. `[official]` + `[community integration doc]`
- **Base sampler defaults:** 30–50 steps, **CFG 4–5**. Recommended samplers: `er_sde`, `euler_a`, `dpmpp_2m_sde_gpu`, `euler`. `[official]`
- **Turbo variant:** CFG 1, 8–12 steps (guidance-distilled). `[official]`
- **Recommended positive prefix:** `masterpiece, best quality, score_7, safe`. **Recommended negative:** `worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration`. `[official]`
- **VRAM — inference:** not stated as a hard number on the model card itself. Community estimate: "likely 8–12GB on consumer GPUs (RTX 3060 or better)," with the base checkpoint download itself ~5.84GB (not a VRAM figure — inference also needs the text encoder, VAE, latents, and ComfyUI overhead on top). `[community, unverified — treat as a rough working estimate, re-verify]` **Could not verify an official VRAM number.**
- **VRAM — LoRA training:** confirmed low. Community-built trainer UI (`citron-anima-lora-trainer-ui`, Gradio) advertises **6GB VRAM** training at reduced (768px) resolution; a Civitai author independently reports training LoRAs at ~6GB VRAM at 768px, noting higher-resolution training would need more. `[community — named authors, reproducible tooling]` https://github.com/citronlegacy/citron-anima-lora-trainer-ui, https://civitai.com/articles/26217/anima-what-is-anima

## Where to run it

- **Official HF repo:** `circlestone-labs/Anima` — https://huggingface.co/circlestone-labs/Anima `[official]`
- **Diffusers repackage:** `circlestone-labs/Anima-Base-v1.0-Diffusers` `[official]`
- **ComfyUI: native, first-class support**, with an official tutorial/workflow page at `docs.comfy.org/tutorials/image/anima/anima`. File layout confirmed from the docs:
  | File | Folder | Loader node |
  |---|---|---|
  | `anima-base-v1.0.safetensors` (or `anima-preview3-base.safetensors`) | `ComfyUI/models/diffusion_models/` | `UNETLoader` |
  | `qwen_3_06b_base.safetensors` | `ComfyUI/models/text_encoders/` | `CLIPLoader` |
  | `qwen_image_vae.safetensors` | `ComfyUI/models/vae/` | `VAELoader` |
  `[official]` — https://docs.comfy.org/tutorials/image/anima/anima. (Note: the CLIPLoader `type` argument value specifically was not returned by the fetch — an author should open the actual template JSON before writing the setup table, per the meta-skill's instruction to read node defaults verbatim rather than trust doc prose.)
- **Third-party quantization:** `silveroxides/Anima-Quantized` on HF. `[community]`
- **No hosted API found** from CircleStone Labs directly (licence explicitly disallows hosting it behind a paid API without a separate agreement, which is consistent with no first-party hosted endpoint existing). Third-party generation platforms (Civitai, TensorArt) do support running it as one of many community-hosted checkpoints. `[community]`
- Community/ecosystem tooling: `DiffSynth-Studio` (ModelScope) ships an `AnimaImagePipeline` integration. `[community/third-party]`

## Official prompting guidance

Verbatim/near-verbatim structure, as retrieved from the model card:

- Tag ordering: `[quality/meta/year/safety tags] [1girl/1boy/1other] [character] [series] [artist] [general tags]`
- Lowercase, spaces not underscores; artist tags prefixed with `@`
- "Tag dropout" trained in — prompts don't need to be exhaustive
- Positive baseline: `masterpiece, best quality, score_7, safe`
- Negative baseline: `worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration`
- Natural-language mode: minimum ~2 sentences recommended
- Weighting: supported, needs higher weights than SDXL norms, worked example `(chibi:2)`

`[official]` throughout — https://huggingface.co/circlestone-labs/Anima

## LoRA training

- **Official/semi-official training path exists via `kohya-ss/sd-scripts`.** A HF discussion states "the training script for the Anima model has already been implemented for sd-scripts." `[community — HF discussion, technically substantive]` https://huggingface.co/circlestone-labs/Anima/discussions/35
- **Community trainer UI:** `citron-anima-lora-trainer-ui` — a Gradio front-end specifically for Anima LoRA training, marketed at 6GB VRAM. `[community — named, reproducible]`
- **Experimental full-finetune + LoRA training code** exists that mimics features from **tdrussell's `diffusion-pipe`** approach, per another HF discussion thread (for Linux/WSL2). Given tdrussell is also the commercial-license contact on the model card, this suggests first-party or first-party-adjacent training tooling, not purely third-party. `[community — HF discussion, named-tool-adjacent]` https://huggingface.co/circlestone-labs/Anima/discussions/28
- **Critical training warning from the model card itself: do not train the LLM adapter** — it has outsized influence on output and finetuners should leave it frozen. `[official]` This is a load-bearing fact for the LoRA training reference file.
- **VRAM for training:** ~6GB reported achievable at 768px resolution by multiple independent community sources; higher resolution needs more. `[community — named, corroborated by two sources]`
- No mention found of `ai-toolkit` (ostris) or `OneTrainer` support specifically — the ecosystem so far centers on `sd-scripts`/kohya-style tooling and bespoke Gradio wrappers. **Could not verify** whether ai-toolkit or OneTrainer support Anima.

## Positioning vs SDXL-anime finetunes and Z-Image

- A named Civitai author frames Anima as **"the worthy successor to Illustrious"** and says it **"brings the power of FLUX to anime,"** explicitly distinguishing it in quality from Chroma, ZImageTurbo, Neta Lumina, and Pony v7. `[community — named author, one voice, not vendor-stated — present as a claim, not settled fact]` https://civitai.com/articles/26217/anima-what-is-anima
- GIGAZINE frames it as runnable "locally on any PC that can handle SDXL or Illustrious-type models" — i.e., comparable hardware cost to the incumbent SDXL-anime ecosystem despite the architectural break, which matters for the skill's "choose the model" section (it's not a heavier ask than what Illustrious/Pony users already run). `[community]`
- Relative to **SDXL-family anime finetunes (Illustrious/NoobAI/Pony, covered in this repo's `sdxl` skill):** same tag-dialect prompting surface (Danbooru-style tags, `score_x`/`safe` quality tags — directly recognizable to anyone who already prompts Illustrious/Pony), but a **different, larger-context text encoder** (Qwen3-0.6B LLM vs 77-token dual CLIP), reportedly better prompt adherence per community claims above, and a from-scratch 2B DiT-lineage backbone rather than an SDXL UNet finetune — so LoRAs, checkpoints, and ControlNets are **not cross-compatible** with the SDXL ecosystem.
- Relative to **Z-Image** (this repo's LLM-encoder, natural-language-prompted exemplar): both use small/efficient modern backbones and both are recent 2026 releases, but Z-Image's one-rule is "write a sentence, not a tag list," while Anima inverts that — tags are the primary trained dialect, natural language is secondary and needs ≥2 sentences to work well. An author should **not** reuse Z-Image's prompting doctrine for Anima; they sit on opposite sides of the tag/sentence divide despite both nominally having "an LLM encoder."
- Anima's separate conditioning path noted in the workbench brief (Cosmos-Reference image-conditioning via a custom node, requiring special LoRAs like "Anima Edit," described as ControlNet-Lineart-rigid for pose) was **not independently re-confirmed in this pass** — I did not find primary CircleStone/Comfy Org documentation of a "Cosmos-Reference" node during this research pass; it appears to be community/custom-node territory (kohya's unlisted `anima-lllite-exp-change-2-000007.safetensors` ControlNet fits this same unofficial-tooling pattern). **Flag for a follow-up pass specifically searching ComfyUI custom-node registries and the CircleStone Labs Discord/GitHub**, since neither surfaced in general web search.

## Vendor-admitted limitations

Verbatim/near-verbatim from the model card:

- **"Doesn't do realism well. This is intended."** — not a bug, a stated design boundary; the model targets anime/illustration/non-photorealistic art specifically.
- Base version's default style is **"plain and neutral"** without aesthetic tuning (that's what the separate Aesthetic checkpoint is for).
- **Weak text rendering** noted as a constraint. `[official]`

## Could not verify

- **Exact CLIPLoader `type` argument** in the official ComfyUI template JSON — docs prose didn't surface it; needs the raw template JSON, not the docs page.
- **Official inference VRAM figure** — no number stated by CircleStone Labs directly; only community estimates (8–12GB) exist.
- **Whether Anima is architecturally DiT** — inferred from Cosmos-Predict2 lineage, not stated in Anima's own materials.
- **The secondary "T5-XXL from SD3.5" text-encoder claim** from the DiffSynth-Studio doc — inconsistent with every other source, likely spurious or context-confused; do not carry into the skill without direct re-verification.
- **The "Anima-2.9B" parameter-count reference** seen in one blog post title — conflicts with the universally-stated 2B figure; unresolved.
- **Comfy Org's precise technical involvement** (beyond funding/sponsorship) — no primary Comfy Org blog post was located confirming or denying co-training; current evidence (Civitai article, HF discussion) points to funding/distribution/day-one ComfyUI support rather than co-training, but this rests on secondary sources, not a Comfy Org primary statement.
- **The "Cosmos-Reference" custom node / "Anima Edit" LoRA / kohya `anima-lllite` ControlNet** described in the workbench brief — not independently found in this research pass; needs a dedicated search of ComfyUI custom-node listings and Civitai/GitHub specifically for these artifact names.
- **ai-toolkit / OneTrainer support** for Anima — not found either way.
- **Exact diffusers minimum version / install line** for `AnimaImagePipeline` — only saw it via the third-party DiffSynth-Studio integration, not circlestone-labs' own diffusers repo README.

## Sources

- https://huggingface.co/circlestone-labs/Anima (model card — primary)
- https://huggingface.co/circlestone-labs/Anima/blob/main/LICENSE.md (license — primary)
- https://huggingface.co/circlestone-labs/Anima-Base-v1.0-Diffusers (diffusers repo listing)
- https://huggingface.co/silveroxides/Anima-Quantized (community quantization)
- https://docs.comfy.org/tutorials/image/anima/anima (official ComfyUI docs/tutorial)
- https://civitai.com/articles/26217/anima-what-is-anima (named community explainer, incl. Comfy Org sponsorship framing and VRAM training report)
- https://gigazine.net/gsc_news/en/20260515-anima-image-generation-ai/ (release-date journalism)
- https://huggingface.co/circlestone-labs/Anima/discussions/185 (Cosmos 3 / architecture / grant discussion)
- https://huggingface.co/circlestone-labs/Anima/discussions/35 (sd-scripts training support)
- https://huggingface.co/circlestone-labs/Anima/discussions/28 (experimental full-finetune/LoRA training code)
- https://github.com/citronlegacy/citron-anima-lora-trainer-ui (community LoRA trainer UI, 6GB VRAM)
- https://github.com/leejet/stable-diffusion.cpp/issues/1245 (feature request — confirmed no architecture detail present)
- https://github.com/modelscope/DiffSynth-Studio/blob/main/docs/en/Model_Details/Anima.md (third-party integration doc — source of the flagged T5-XXL claim and the `AnimaImagePipeline` class name)
- https://www.linkedin.com/posts/yolandyan_im-excited-to-announce-our-1m-comfy-open-activity-7424852466598375424-MLKH (Comfy $1M grant post, title-level corroboration only)
- https://x.com/circlestone_ai/status/2017674821987860921 (CircleStone Labs preview-release announcement tweet, per search snippet)
