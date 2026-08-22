# Fact-check — `skills/generative-media/anima/`

Adversarial pass, 2026-08-22. Primary sources fetched directly with `curl` (verbatim, not
WebFetch summaries): the Hugging Face model card and `LICENSE.md`, the HF API file listings,
CircleStone's own diffusers repo config files, ComfyUI core source (`comfy/text_encoders/anima.py`,
`comfy/ldm/anima/model.py`, `comfy/sd.py`, `comfy_extras/nodes_model_patch.py`), the stock ComfyUI
workflow template JSON, kohya-ss's LLLite model cards, the two GitHub PRs, and the Civitai API.

## Verdict

**MATERIAL ERRORS.** The skill's intellectual centre — the conditioning-class exception — **survives
verbatim checking completely**; every quote attributed to the model card is real, and the underlying
claim is not merely true but *more* true than the skill knows. The errors are elsewhere, and they
repeat the `scail-2` pattern exactly. Two vendor-shipped facts are wrongly demoted to rumour: the
**T5-XXL component** (dismissed as a "framework artefact" — it is in ComfyUI core *and* in
CircleStone's own diffusers repo, and it is the mechanism that makes prompt weighting work at all),
and the **architecture of `anima-lllite-exp-change-2`** (called "LLM-generated and not from Kohya" —
it is verbatim from Kohya's own PR #2413 body). Alongside those: the **licence is misstated in the
restrictive direction** (the skill tells businesses they may not sell Anima's output images; the card
and licence say anyone may), the base checkpoint's size is overstated by 40%, the LLLite loader node
is wrong (ComfyUI core ships `ModelPatchLoader` + `AnimaLLLiteApply`; the skill sends readers to
Kohya's custom node), and the download URL given for `exp-change-2` 404s. Four `[flagged]` items are
now fully settled against the skill's guess. None of this touches the prompting guide, which is the
most accurate file in the skill.

## The conditioning-class claim

**It survives, verbatim, on every point the brief asked me to attack.** Source for all card quotes:
<https://huggingface.co/circlestone-labs/Anima/raw/main/README.md> (fetched raw, not summarised).

**1. Text encoder is Qwen3-0.6B base.** Card, line 37: `qwen_3_06b_base.safetensors goes in
ComfyUI/models/text_encoders`. Independently confirmed from CircleStone's own diffusers repo
`text_encoder/config.json`: `"architectures": ["Qwen3Model"]`, `hidden_size: 1024`,
`num_hidden_layers: 28`, `vocab_size: 151936` — the Qwen3-0.6B geometry, base (`Qwen3Model`, no
LM head, no chat/instruct tuning). Weights are 1,192,133,232 bytes in bf16 ≈ 0.596B params. ✅ **Base,
not instruct; 0.6B, not another size.**

**2. Dedicated LLM adapter, with the "outsized influence" warning.** Card, lines 127–129, verbatim:

> **Don't train the LLM adapter.** My own training script, diffusion-pipe, lets you set
> llm_adapter_lr=0 to completely disable training it, and the example config has this as a default.
> - Other trainers like sd-scripts have similar options that should be used.
> - The LLM adapter processes the text embeddings before they get to the diffusion model, and
>   therefore has an outsized influence on the generated images. The adapter itself contains a
>   surprising amount of knowledge and is easy to degrade by training it.

The skill's rendering (`SKILL.md:48`, `lora-training.md:24`) is faithful. ✅ Confirmed in code too:
`comfy/ldm/anima/model.py:143` `class LLMAdapter(nn.Module)`, instantiated at line 196 as
`self.llm_adapter`; and in the diffusers repo as a separate `text_conditioner/` component,
`"_class_name": "AnimaTextConditioner"`, 6 layers, 16 heads, `model_dim: 1024`, 269 MB of weights.

**3. Caption corpus.** Card, line 51, verbatim:

> The model is trained on Danbooru-style tags, natural language captions, and combinations of tags
> and captions.

`SKILL.md:49` presents this as *"Danbooru-style tags, natural language captions, and combinations."*
— truncated mid-phrase inside quote marks and marked `[official]`. `prompting-guide.md:5` gets it
right in full. Meaning is preserved; the quotation is not exact. Minor.

**4. Weighting is officially documented, above SDXL norms, `(chibi:2)`.** Card, line 56, verbatim:

> - Prompt weighting works, but needs a weight higher than typically used for SDXL. Example: "(chibi:2)"

`SKILL.md:32` and `prompting-guide.md:119` both quote this correctly. ✅

**5. The `@` artist prefix.** Card, line 85, verbatim:

> Prefix artist with @. E.g. "@big chungus". **You must put @ in front of the artist.** The effect
> will be very weak if you don't.

`SKILL.md:40` and `prompting-guide.md:100` quote it exactly. ✅

**What the skill missed — and it is the best fact in the model.** The skill says weighting "works"
but does not know *how*, and its ignorance of the mechanism is what caused error E2. In ComfyUI core,
`comfy/text_encoders/anima.py` defines `AnimaTokenizer`, which tokenises the prompt **twice**:

```python
class AnimaTokenizer:
    def __init__(self, ...):
        self.qwen3_06b = Qwen3Tokenizer(...)
        self.t5xxl = T5XXLTokenizer(...)

    def tokenize_with_weights(self, text, return_word_ids=False, **kwargs):
        out = {}
        qwen_ids = self.qwen3_06b.tokenize_with_weights(text, return_word_ids, **kwargs)
        out["qwen3_06b"] = [[(k[0], 1.0, k[2]) ... ]]  # Set weights to 1.0
        out["t5xxl"] = self.t5xxl.tokenize_with_weights(text, return_word_ids, **kwargs)
```

The Qwen token weights are **forced to 1.0**; the attention weights ride on the *T5-XXL* token
stream. They are then applied in `comfy/ldm/anima/model.py:198–206`:

```python
def preprocess_text_embeds(self, text_embeds, text_ids, t5xxl_weights=None):
    if text_ids is not None:
        out = self.llm_adapter(text_embeds, text_ids)
        if t5xxl_weights is not None:
            out = out * t5xxl_weights
```

And `LLMAdapter.__init__` sets `self.embed = operations.Embedding(32128, target_dim)` — 32128 is the
T5 vocabulary size. Confirmed officially by CircleStone, not just by ComfyUI:
`text_conditioner/config.json` in `circlestone-labs/Anima-Base-v1.0-Diffusers` carries
`"target_vocab_size": 32128` and `"min_sequence_length": 512`, and the repo ships a `t5_tokenizer/`
folder registered in `modular_model_index.json` as `["transformers", "T5Tokenizer"]`.

So the adapter is a **cross-attention module whose queries are a T5-tokenised embedding of the
prompt, attending to Qwen3-0.6B hidden states**, and ComfyUI weighting is a **multiplicative scale on
the adapter's output embeddings**. That is why weights must be pushed past SDXL norms: a plain scalar
multiply on a post-adapter embedding is a blunter instrument than CLIP's interpolation-toward-mean.
The skill's thesis ("dialect follows the caption corpus, not the encoder") is right; this mechanism
would make the section *stronger*, and the skill instead files the key evidence under "likely
spurious" (E2).

**Verdict on the section: keep it as written, add the mechanism, fix the truncated quote.**

## Licence

Both licences confirmed, and the skill's headline framing is wrong in one specific, consequential way.

**Card, lines 145–162, verbatim (the operative sentences):**

> This model is licensed under the CircleStone Labs Non-Commercial License. The model and derivatives
> are only usable for non-commercial purposes. Additionally, this model constitutes a "Derivative
> Model" of Cosmos-Predict2-2B-Text2Image, and therefore is subject to the [NVIDIA Open Model License
> Agreement](…) insofar as it applies to Derivative Models.
>
> If you would like a commercial license, please email tdrussell@circlestone.ai
>
> **Note that the non-commercial restriction applies only to the Model, and not to Outputs (the
> generated images). You may use generated images commercially.**
>
> **Examples of allowed commercial use**:
> - selling images
> - paid commissions for images
> - generating images to use as concept art or assets for a paid product (e.g. video game or visual novel)
> - selling Derivative model weights, if you are operating as an individual (Section 2.c contains a
>   carve-out for this specific use)
>
> **Examples of disallowed commercial use without a separate license**:
> - hosting the model behind an API and charging for access
> - hosting the model on a paid online image generation platform
> - embedding the model weights inside a monetized game or other product
> - using the model to power some feature as part of a larger, monetized product

**`LICENSE.md` (CircleStone Labs Non-Commercial License v1.2), verbatim:**

- §1(a): *"'Derivative' means any (i) modified version of the CircleStone Model … (ii) work based on
  the CircleStone Model, including Low-rank Adaptations ("LoRAs") and textual inversions … **For the
  avoidance of doubt, Outputs are not considered Derivatives under this License.**"*
- §1(c): *"For clarity, use (a) for revenue-generating activity, (b) in direct interactions with or
  that has impact on third-party end users, or (c) to train, fine tune, or distill other models for
  commercial use, in each case, is not a Non-Commercial Purpose."* — the skill quotes this correctly
  at `SKILL.md:239`.
- §2(a): *"…solely for your Non-Commercial Purposes."* ✅ as quoted.
- §2(c): *"**Persons operating in an individual capacity may sell Derivatives owned or created by
  them.** This includes (i) requiring payment to download model weights, (ii) paid commissions for
  the creation of Derivatives … **This right to sell Derivatives extends solely to the model weights,
  and not to any larger product, tool, or feature which incorporates the Model.**"*
- §2(e): *"We claim no ownership rights in and to the Outputs. … **You may use Outputs for any purpose
  (including for commercial purposes)**, except as expressly prohibited herein."*
- §4(a): *"…(ii) in any manner that infringes, misappropriates, or otherwise violates … any third
  party's legal rights, **including rights of publicity or 'digital replica' rights**, … (iv) to
  generate unlawful content, including child sexual abuse material, or non-consensual intimate
  images."*

**The NVIDIA Open Model License claim is confirmed twice over** — by the card sentence above and by
the repo's YAML front-matter, `base_model: - nvidia/Cosmos-Predict2-2B-Text2Image`.

**Where the skill goes wrong.** It fuses two separate grants into one and attaches the individual
limit to both. §2(c) covers **model weights only** and says so explicitly; **Outputs are carved out
of the definition of Derivative entirely** and are commercially free for *anyone*, entity or
individual. So:

- `SKILL.md:4` — *"individuals may sell the images and LoRAs they make with it"* → a company may
  sell the images too, and may ship them as game/VN assets (the card lists that as allowed).
- `SKILL.md:225` — *"Individuals may sell outputs and derivatives"* → same conflation.
- `SKILL.md:242` — quotes §2(c) correctly, then says *"That covers selling generated images, paid
  commissions, and selling LoRAs"*. §2(c) does **not** cover generated images; §2(e) does, for
  everyone. It also drops §2(c)'s own limit (weights only, not a larger product).

This errs restrictively, which is the safer direction, but it is still wrong and it will send a
studio to buy a licence it does not need for the thing it actually wants (selling images), while
under-warning about the thing that is genuinely restricted (embedding weights in a monetised
product — which §2(c) forbids even for individuals).

`SKILL.md:246`'s *"Real-person likeness is governed by platform rules and law, not this licence"* is
also wrong: §4(a)(ii) names rights of publicity and digital-replica rights directly.

## Errors found

| Claim (`file:line`) | What is actually true | Source | Severity |
|---|---|---|---|
| `SKILL.md:4`, `:225`, `:242` — commercial use of **outputs** restricted to individuals | Non-commercial restriction *"applies only to the Model, and not to Outputs"*; §1(a) *"Outputs are not considered Derivatives"*; §2(e) *"You may use Outputs for any purpose (including for commercial purposes)"*. §2(c)'s individual carve-out covers **model weights only**, *"not to any larger product, tool, or feature which incorporates the Model"* | [README](https://huggingface.co/circlestone-labs/Anima/raw/main/README.md) L150–156; [LICENSE.md](https://huggingface.co/circlestone-labs/Anima/raw/main/LICENSE.md) §1(a), §2(c), §2(e) | **material** |
| `SKILL.md:267`, `setup-and-workflows.md:98` — secondary T5-XXL *"appears nowhere else … likely a framework artefact"*, deliberately excluded | Real and vendor-shipped. CircleStone's diffusers repo ships `t5_tokenizer/` (`T5Tokenizer`) and `text_conditioner/config.json` with `"target_vocab_size": 32128`; ComfyUI core's `AnimaTokenizer` tokenises with both Qwen3 **and** T5-XXL, forces Qwen weights to 1.0, and applies `t5xxl_weights` multiplicatively to the adapter output. It is the weighting mechanism | [modular_model_index.json](https://huggingface.co/circlestone-labs/Anima-Base-v1.0-Diffusers/raw/main/modular_model_index.json); [text_conditioner/config.json](https://huggingface.co/circlestone-labs/Anima-Base-v1.0-Diffusers/raw/main/text_conditioner/config.json); [comfy/text_encoders/anima.py](https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/comfy/text_encoders/anima.py); [comfy/ldm/anima/model.py](https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/comfy/ldm/anima/model.py) | **material** |
| `SKILL.md:152`, `setup-and-workflows.md:134` — the *"frozen DiT hidden states of a reference image"* description is *"LLM-generated and not from Kohya — do not repeat it as fact"* | It is Kohya's own words. PR #2413 body: *"v3 uses **frozen DiT hidden states of a reference image as the conditioning source**, injected into the trained blocks via a low-rank value path with a multiplicative gate (`--lllite_trunk semantic`)"*, plus documented flags and *"Docs: new section 9 (semantic trunk) … in `docs/anima_train_control_net_lllite.md`"* | [kohya-ss/sd-scripts#2413](https://github.com/kohya-ss/sd-scripts/pull/2413) | **material** |
| `setup-and-workflows.md:132` — *"pull the `-000007` safetensors from `Comfy-Org/Anima-LLLite`"* | Not in that repo. The Comfy-Org repackage holds 10 files, none of them `exp-change`. The weight lives only at `kohya-ss/Anima-LLLite/anima-lllite-exp-change-2-000007.safetensors` (77.7 MB) | [Comfy-Org file list](https://huggingface.co/api/models/Comfy-Org/Anima-LLLite); [kohya-ss file list](https://huggingface.co/api/models/kohya-ss/Anima-LLLite) | **material** |
| `SKILL.md:68`, `:89`, `setup-and-workflows.md:28`, `:87` — base checkpoint *"~5.84 GB"* | **4,182,218,328 bytes (3.90 GiB / 4.18 GB)**. Matches 1.96B-param transformer + 0.13B adapter at bf16 — which is also independent confirmation of the 2B figure | [HF API](https://huggingface.co/api/models/circlestone-labs/Anima?blobs=true) | **material** |
| `SKILL.md:72` — LLLite control models load via *"Kohya's LLLite node"*; folder given only as "see §8", and §8 never gives one | Native in ComfyUI core: files go in `ComfyUI/models/model_patches/`, loaded by `ModelPatchLoader` ("Load Model Patch") and applied by `AnimaLLLiteApply` ("Apply Anima LLLite", inputs `model`, `model_patch`, `image`, `strength`, `start_percent`, `end_percent`, optional `mask`; category `model_patches/anima`). Kohya's custom node is needed only for the unreleased v3 | [comfy_extras/nodes_model_patch.py](https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/comfy_extras/nodes_model_patch.py) L229, L339, L899–917; [Comfy-Org README](https://huggingface.co/Comfy-Org/Anima-LLLite/raw/main/README.md) | **material** |
| `SKILL.md:17`, `:103`, `:207`, `setup-and-workflows.md:50`, `prompting-guide.md:176` — Base *"CFG 4–6"* `[official]` | Card says *"30-50 steps, CFG 4-5."* The stock ComfyUI template ships **CFG 4, 30 steps, `euler`, `simple`, 1024×1024**. Nothing official supports 6 | [README](https://huggingface.co/circlestone-labs/Anima/raw/main/README.md) L42; [image_anima_base_v1.json](https://raw.githubusercontent.com/Comfy-Org/workflow_templates/main/templates/image_anima_base_v1.json) | minor |
| `SKILL.md:18`, `:110`, `setup-and-workflows.md:50` — Aesthetic *"CFG 3–5"*, in an `[official]`-framed table | No source anywhere. The card's Aesthetic section discusses quality tags only and gives no CFG. Absent from both research files | — | minor |
| `SKILL.md:76`, `setup-and-workflows.md:41–43` — `CLIPLoader` `type` unknown; *"a wrong `type` produces plausible-looking but consistently off-target images"* | Stock template value is **`stable_diffusion`**, and it does not matter: ComfyUI routes by *detected encoder* — `elif te_model == TEModel.QWEN3_06B: clip_target.clip = comfy.text_encoders.anima.te(...)`. There is no `anima` entry in the `type` list at all. The stated failure mode cannot occur | [comfy/sd.py](https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/comfy/sd.py) L1011, L1927–1929; template JSON above | minor (but it is a fabricated warning) |
| `setup-and-workflows.md:122` — LLLite control image = *"scribble / HED / canny"* | No canny or HED weights exist. Published set: `lineart`, `depth`, `pose`, `scribble` (Preview3-era), `inpainting-v1/v2`, `any-test-like-1/v2`. The "any control" template uses the any-test-like weights, trained on *"Lineart / scribble / grayscale, heavily augmented"* | [kohya-ss/Anima-LLLite README](https://huggingface.co/kohya-ss/Anima-LLLite/raw/main/README.md) | minor |
| `SKILL.md:146` — pose weakness *"by CircleStone's own documentation"* | It is **kohya-ss's** documentation, not CircleStone's, and it is about kohya's LLLite pose weight: *"the pose model in particular has noticeably weaker control than the others"* / *"best treated as a soft pose prior rather than a strict pose-locking ControlNet."* An official pose weight does exist (`anima-lllite-pose-1.safetensors`, DWPose-conditioned, 1,544 pairs) | [PREVIEW3.md](https://huggingface.co/kohya-ss/Anima-LLLite/raw/main/PREVIEW3.md) L36, L152 | minor |
| `SKILL.md:93`, `setup-and-workflows.md:97` — diffusers pipeline *"`AnimaImagePipeline`"*, min version unknown | CircleStone's own repo declares `"_class_name": "AnimaModularPipeline"`, `"_blocks_class_name": "AnimaAutoBlocks"`, `"_diffusers_version": "0.39.0.dev0"`. `AnimaImagePipeline` is DiffSynth-Studio's class, not diffusers' | [modular_model_index.json](https://huggingface.co/circlestone-labs/Anima-Base-v1.0-Diffusers/raw/main/modular_model_index.json) | minor |
| `SKILL.md:246` — real-person likeness *"governed by platform rules and law, not this licence"* | §4(a)(ii) bars use that violates *"any third party's legal rights, including rights of publicity or 'digital replica' rights"* | LICENSE.md §4(a)(ii) | minor |
| `setup-and-workflows.md:108`, `lora-training.md:47` — *"LoRAs should be trained on this version"* `[official]` | Card says *"LoRAs should be trained **using** this version."* Also `lora-training.md:24` renders `llm_adapter_lr=0` as `llm_adapter_lr 0` inside a verbatim block, and `SKILL.md:24` truncates *"very fast to generate"* to *"very fast"* | README L21, L127 | trivial |
| `SKILL.md:18`, variant selector — Aesthetic listed as *"v1.0 / v1.0b"* | A third Aesthetic checkpoint shipped: `anima-aesthetic-v1.1.safetensors`, uploaded **2026-07-13**, still undocumented in the card's Versions section. Turbo's filename (`anima-turbo-v1.0.safetensors`) is also never given | [HF commits](https://huggingface.co/api/models/circlestone-labs/Anima/commits/main) | minor |
| `lora-training.md:39` — sd-scripts support marked `[community — HF discussion #35]` | First-class and merged on `main`: `anima_train.py`, `anima_train_network.py`, `anima_train_control_net_lllite.py`, `anima_minimal_inference.py`, plus `docs/anima_train_network.md` and `docs/anima_torch_compile.md` | [sd-scripts contents](https://api.github.com/repos/kohya-ss/sd-scripts/contents/) | minor |
| `setup-and-workflows.md:124` — exp-change-2 published *"with no readme and no announcement"* | No readme entry: correct. But it *was* announced — PR #2413 links it under "For experimental generation", with a usage note (*"use a prompt similar to the one used for standard generation, rather than a short prompt that specifies only the facial expression"*) the skill does not carry | PR #2413 | minor |
| `setup-and-workflows.md:122` — stock templates cited `[community — u/Corrupt_file32]` | They are official: `image_anima_lllite_any_control_to_image.json`, `image_anima_lllite_depth_control_to_image.json`, `image_anima_lllite_image_inpainting.json` in Comfy-Org/workflow_templates | [templates dir](https://api.github.com/repos/Comfy-Org/workflow_templates/contents/templates) | minor |

**Verified correct (attacked and survived):** the Cosmos-Predict2-2B-Text2Image derivation and both
licences; 2B parameters; Qwen-Image VAE (`"_class_name": "AutoencoderKLQwenImage"`, `z_dim: 16`);
September 2025 cut-off; 512²–1536²; the three filenames and the three loader nodes and their folders;
`er_sde` as the authors' default with the exact quote; the `beta57`/RES4LYF quote; the four
sampler characterisations, all verbatim; Turbo at CFG 1 / 8–12 steps; the recommended positive and
negative prompts; the full tag-order grammar, both quality ladders, the safety and year and meta
vocabularies, the Gelbooru rule, tag dropout, the ≥2-sentence prose floor, the ye-pop/DeviantArt
dataset-tag mode and its worked example; every "Limitations" quote; the 2e-5 @ rank-32 LR and
*"a light touch is all you need"*; the hosted-platform list; **PR numbers #2413 and #10 — both open,
both `draft: true`, both unmerged as of today, node branch `feat-v3-semantic-trunk` exactly as
stated**; the `Comfy-Org/Anima-LLLite` repo name; the Turbo LoRA as a genuine `circlestone_labs`
Civitai asset; and every Civitai download figure (MiaoMiao Harem 198,875 vs 198,832 quoted; official
base 189,910 vs 189,872; Turbo LoRA 59,903 vs 59,890; motimalu 153,348 vs 153,330) plus the
permission flags `allowCommercialUse: ["Image","RentCivit"], allowDerivatives: true,
allowDifferentLicense: false` — exact.

## Claims absent from all research

- **Aesthetic CFG 3–5.** Not in the card, not in the ComfyUI docs, not in either research file.
  It appears in four places dressed as official.
- **Base CFG upper bound of 6.** The research file records the card's 4–5 correctly
  (`research-primary.md:59`); the drift to 4–6 was introduced during authoring.
- **"Turbo — quality tags: Yes"** (`SKILL.md:19`, `prompting-guide.md:185`). Nothing states what
  Turbo was distilled from or whether its captions retained quality tags. Plausible, unsourced.
- **The per-example settings on worked prompts** (`prompting-guide.md:221` "Base, 35 steps, CFG 5,
  er_sde"; `:243` "CFG 3.5"; `:254` "CFG 4.5"). The card attaches no settings to its example prompt.
  In-range and harmless, but invented.
- **"Multiples of 16"** (`SKILL.md:84`, `:208`, `setup-and-workflows.md:75`) marked `[official]`.
  Not on the card. It is almost certainly right — kohya trains Anima LLLite with
  `bucket_reso_steps = 16` and DiffSynth documents the same — but the provenance tag is wrong.
- **`SKILL.md:9` "a latent-diffusion backbone."** Anima is a **flow-matching DiT**
  (`FlowMatchEulerDiscreteScheduler`, `shift: 3.0`; `CosmosTransformer3DModel`). Not what the card
  says, and not what the research says.
- **`characters.md:73` "the model card admits it"** (multi-character being unsolved). The card says
  only *"If you just list off character names with no description of appearance, the model can get
  confused."* That is a prompting note, not an admission of an unsolved problem.

## Markers

**Should be removed — now settled:**

1. **Architecture family** (`SKILL.md:264`, *"no CircleStone material says 'DiT' … the one circulating
   description that does is LLM-generated"*). Settled three ways: CircleStone's own diffusers repo
   declares the backbone `"_class_name": "CosmosTransformer3DModel"` (28 layers, 16 heads ×
   128 = 2048 dim, `patch_size [1,2,2]`, `in/out_channels 16`); ComfyUI core has
   `class Anima(MiniTrainDIT)` importing `from comfy.ldm.cosmos.predict2 import MiniTrainDIT`; and
   kohya-ss writes *"ported to Anima's DiT (MiniTrainDIT) architecture."* It is a flow-matching DiT.
2. **The 2B-vs-2.9B `[contested]`** (`SKILL.md:266`). Not contested — 2B is right and the marker
   should go. The transformer alone is 3,912,877,104 bytes at bf16 = **1.96B params**; the
   single-file checkpoint (transformer + adapter) is 4.18 GB. The "2.9B" is either the
   layer-expanded community fork (`lylogummy`-style repos; a dozen `Anima-2.9B` mirrors exist on HF)
   or a whole-pipeline sum including the 0.6B encoder — not a competing claim about the base model.
3. **The T5-XXL `[flagged]`** (`SKILL.md:267`). Settled — and settled *against* the skill's guess.
   See the conditioning-class section; this needs to become a positive, documented fact.
4. **`CLIPLoader` `type` `[flagged]`** (`SKILL.md:76`, `setup-and-workflows.md:41`). Settled:
   `stable_diffusion` in the stock template, and irrelevant because routing is by detected encoder.
5. **The diffusers pipeline class `[flagged]`** (`SKILL.md:93`). Settled: `AnimaModularPipeline` /
   `AnimaAutoBlocks`, diffusers `0.39.0.dev0`.
6. **exp-change-2's architecture `[flagged — re-verify]`** (`SKILL.md:152`,
   `setup-and-workflows.md:134`). Settled by Kohya's PR body; the skill's flag currently asserts a
   false negative, which is worse than an open flag.

**Genuinely still open — keep the marker:**

- Inference VRAM (`SKILL.md:265`) — no official figure exists; I could not find one either.
- AMD memory creep (`SKILL.md:271`) — cause still unattributed between Anima and ROCm.
- Whether Anima LoRAs load on the 2.9B/3.8B forks (`setup-and-workflows.md:109`) — unanswered.
- Civitai download counts (`setup-and-workflows.md:214`) — correctly flagged as volatile; they moved
  ~40 downloads in a day, so the flag is doing real work.
- ThetaCursed Style Explorer URLs (`prompting-guide.md:104`) — correctly flagged as volatile.
- OneTrainer / AI Toolkit support (`lora-training.md:42`, `:45`) — still not established either way.
- Turbo-vs-Aesthetic `[contested]` (`SKILL.md:19`, `:24`) — genuinely contested; the vendor
  recommendation is verbatim correct and the dissent is a named practitioner. Keep.
- Character-LoRA difficulty `[contested]` (`SKILL.md:269`) — genuinely contested. Keep.
- **`[pending release]` on exp-change-2 is CORRECT and should stay.** Both PRs verified open and
  draft today; sd-scripts #2413 is *"[Experimental] Anima ControlNet-LLLite v3: semantic trunk…"*,
  head `exp-anima-lllite-v3-semantic-trunk`, opened 2026-08-02, `merged: false`; node PR #10 is
  *"Support v3 (semantic trunk) LLLite weights"*, head `feat-v3-semantic-trunk`, same date, also
  draft. Kohya's own status line: *"merging into main is not decided yet."*

**Mis-marked in the other direction (over-flagged):**

- **Comfy Org's role** (`SKILL.md:9`, `:271`). The skill asserts the negative — *"not co-training"* —
  while flagging it. The card's own first sentence is *"created via a collaboration between
  CircleStone Labs and Comfy Org"*, and the ComfyUI docs say *"by CircleStone Labs in partnership
  with Comfy Org."* The $1M grant framing is corroborated only by secondary sources (a Feb 2026
  announcement, LinkedIn, the Civitai explainer). Safer to quote *"collaboration"* verbatim and
  describe the grant as the community's account, rather than asserting a negative no primary source
  states.

## Could not verify

- **Anima's release date as 15 May 2026.** `anima-base-v1.0.safetensors` was uploaded
  **2026-05-14 17:00:00 UTC**; the repo itself was created 2026-01-29 (preview line:
  `anima-preview` → `anima-preview2` 2026-03-11 → `anima-preview3-base` 2026-04-07). Secondary
  coverage says 15 May, consistent with a JST announcement. The skill's date is defensible; the
  weights landed 14 May UTC. Also datable from the same log: **Turbo and the Turbo LoRA ~2026-07-08**,
  Aesthetic v1.0b 2026-07-09, Aesthetic v1.1 2026-07-13.
- **The ModelScope DiffSynth-Studio page** — I did not fetch it, so I cannot say whether it says
  "T5-XXL tokenizer" (accurate) or "T5-XXL text encoder" (would be wrong: no T5 *weights* are loaded
  anywhere; only T5 token ids and their weights are used). Either way the skill's dismissal fails.
- **Every Reddit-sourced quote** (seed instability, the fried-hi-res chain, LLLite 0.15–0.3, the
  16:9/768 px video handoff, ReStyler). Out of scope for this pass; the community research file is
  detailed and internally consistent, and where its claims touch checkable artefacts — the Civitai
  numbers, the Turbo LoRA, the two IP-Adapter repos' names, `Mirumo0u0/ComfyUI-Cosmos-Reference`
  (which exists, *"Add an image reference feature to the Cosmos model or models based on it"*, and
  which the skill never names as a findable repo) — they hold up.
- **ThetaCursed's 42k-vs-16k artist-style counts** and the `tags.latent.moe` coverage figure.
- **`silveroxides/Anima-Quantized`** is real but is mostly *resized turbo-distill LoRAs* from the
  preview2 era, not obviously a quantisation of Anima-Base v1.0; the skill's one-line
  `[community]` mention overstates its relevance. I did not enumerate the whole repo.
