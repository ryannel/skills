# Anima — community evidence (2026-08-22)

Harvested from r/StableDiffusion, r/comfyui, r/unstable_diffusion and the civitai.red models
API. Community-sourced unless marked `[model page]` — that tag means the text comes from the
**Civitai model page written by `circlestone_labs`, the model's own authors**, which is
authoritative-adjacent but is still not the HF card or the licence file. Verify before asserting.

Raw page text: `../research-2026-08-22/raw/anima-reddit-search.txt`,
`anima-reddit-comments.txt`, `civitai-api-2026-08-22.txt`, `comfyui-search.txt`,
`unstable-diffusion-search.txt`.

---

## The two facts that reshape the brief

**1. Anima is a derivative of NVIDIA Cosmos-Predict2-2B-Text2Image, and it is
non-commercial.** `[model page]`, verbatim, closing paragraph:

> *"This model is licensed under the CircleStone Labs Non-Commercial License. The model and
> derivatives are only usable for non-commercial purposes. Additionally, this model constitutes
> a 'Derivative Model' of **Cosmos-Predict2-2B-Text2Image**, and therefore is subject to the
> NVIDIA Open Model License Agreement insofar as it applies to Derivative Models. If you would
> like a commercial license, please email tdrussell@circlestone.ai. Built on NVIDIA Cosmos."*

This is the skill's spine, not a footnote. It explains the "Cosmos-Reference" node the brief
found mysterious — **Anima inherits Cosmos-Predict2's reference-conditioning mechanism**, which
is why image conditioning arrives through a node called Cosmos-Reference and needs a special
LoRA. It also means the licence section has to cover *two* licences, and that the honest
comparison against Illustrious/NoobAI/Pony (all Apache/CreativeML-descended SDXL finetunes) has
a commercial-use asymmetry the `sdxl` skill will need to route around.

Civitai's own permission flags on the model corroborate: `allowCommercialUse: ["Image",
"RentCivit"]`, `allowDerivatives: true`, **`allowDifferentLicense: false`**.

**2. The encoder question is settled, and the answer is "both".** Anima's text encoder is
**Qwen3-0.6B base** (`qwen_3_06b_base.safetensors` `[model page]`), its VAE is the **Qwen-Image
VAE** (`qwen_image_vae.safetensors`). So it is an LLM-encoder model *architecturally* — but it
was trained on *"Danbooru-style tags, natural language captions, and combinations of tags and
captions"* `[model page]`, so the prompt dialect is genuinely dual. The brief's guess that
`(split screen, multiple views:1.2)` implied CLIP-class was half right: **tag syntax and prompt
weighting work, but through a small LLM, and the weights have to be pushed harder than SDXL's.**

Community view of the encoder is that it is the model's ceiling. `u/Time-Teaching1926`: *"anima
is really good and a great successor to illustrious but it's small parameter model size and
small Qwen3 0.6b text encoder does have noticeable limits."* `u/wiserdking`, more bluntly:
*"specially if he sticks to the shitty 0.6B text encoder."*

---

## Craft

### Canonical generation settings `[model page]`

- **Resolution:** works between **512² and 1536²**.
- **Base / Aesthetic:** **30–50 steps, CFG 4–6.** Aesthetic *"can tolerate lower CFGs such as 3,
  and often looks better with them."*
- **Turbo:** **CFG 1, 8–12 steps.**
- **Samplers**, with the authors' own characterisations:
  - `er_sde` — *"neutral style, flat colors, sharp lines. I use this as a reasonable default."*
  - `euler_a` — *"Softer, thinner lines. Can sometimes tend towards a 2.5D look. CFG can be
    pushed a bit higher than other samplers without burning the image."*
  - `dpmpp_2m_sde_gpu` — *"similar in style to er_sde but can produce more variety and be more
    'creative'. Depending on the prompt it can get too wild sometimes."*
  - `euler` — *"a bit more creative than er_sde. Good with the Turbo and Aesthetic versions."*
- **Scheduler:** *"If going for a more realistic / painterly look, the **beta57** scheduler
  (ComfyUI RES4LYF custom node pack) can help make better textures, since it puts more emphasis
  on low-noise timesteps."*

### Variant selector `[model page]`

| Variant | What it is | Use it when |
|---|---|---|
| **Anima-Base** | *"The pretrained, unrefined base model. Maximum flexibility, diversity, and style adherence."* | **LoRAs should be trained on this version.** Default style is *"very plain and neutral"* without artist/quality tags |
| **Anima-Aesthetic** | *"Fine-tuned for better consistency and a higher quality default art style"* | quality tags stripped from its captions — don't feed it `score_*` |
| **Anima-Turbo** | distilled, *"increases stability and gives the model a strong default style, but reduces diversity"* | the authors' own recommended starting point |

Author's recommendation verbatim: *"I recommend starting with Anima-Turbo. On average, it is only
slightly worse than Anima-Aesthetic, while being very fast… The increased stability can even make
it better than Aesthetic in some cases."* Community dissents: `u/Time-Teaching1926` — *"I'm not a
fan of the official anima turbo model as the quality, styles, stability and even sometimes prompt
Adherence isn't that great."* `[contested]`

Note the Turbo also exists **as a LoRA** (`Anima Turbo LoRA`, circlestone_labs, 59,890
downloads), and there is a community `RDBT Distilled Turbo LoRA` and a 12-step turbo LoRA
(`u/TheBizarreCommunity`).

### Traps

- **Seeds are not equal.** `u/arthan1011`: *"Not all seeds are equal - some seeds will ruin the
  generation while others will work perfectly. **Anima has this instability.**"* This is the
  single most repeated piece of practitioner advice about Anima.
- **Full-body loses detail; hi-res-fix chains fry the image.** `u/AssistanceSouth9359`
  (r/comfyui): *"anima is pretty good at creating close up shots > Halfbody shots > 3/4 body
  shots but it loses a lot of details or the image gets fried (weird, soft black spots all over
  the image) when i try to use 2 ksamplers, pre and post hi res fixes."* — unresolved in-thread.
- **Text rendering is weak** `[model page]`: *"It can generally do single words and sometimes
  short phrases, but lengthy text rendering won't work well."*
- **Realism is out of scope by design** `[model page]`: *"The model doesn't do realism well.
  This is intended."*
- **Undesired content leaks on short prompts** `[model page]`: *"The model may generate undesired
  content, especially if the prompt is short or lacking details. Avoid this by using the
  appropriate safety tags in the positive and negative prompts."*
- **Memory creep on AMD.** `u/Greyblades2`: generation time creeps from 20 s to over a minute
  after 20–30 images, *"the only way I have found to restore the quick generation is by a full
  reboot."* `u/Alekite` (AMD R9700 32 GB) hits VRAM+RAM exhaustion on an Illustrious→Anima
  refine chain without a VRAM-management node. `[AMD-specific, 2 sources]`

### VRAM reality — Anima's real differentiator

**Anima is the model that runs when nothing else will.** `u/Dependent_Quit_3730`
(r/unstable_diffusion), on an **8 GB AMD RX6600 with 16 GB RAM**: *"Eu só consigo rodar ANIMA na
comfyui. Outros modelos não carregam"* — Anima is the only model that loads at all. Speed on that
class of card is the cost: `u/Bokayoteamo`, RX6600 8 GB via ROCm, *"1024x1024 30 steps takes
around 8-15 mins."*

Training is correspondingly cheap. `u/RealOminousHvh`'s Aozora trainer: *"It can train **100% of
Anima at 1152×1152** resolution while using approximately **11.4 GB of VRAM** at around 2.67
seconds per iteration"* — i.e. full finetuning fits on a 12 GB card, which is not true of any
other model the suite covers.

---

## Prompting (with quoted real prompts)

**Settled: Anima is tag-first, natural-language-capable, and prompt-weighted — but the weights
are bigger than SDXL's.** All `[model page]` unless noted.

### The rules

- *"Use lowercase for tags, and spaces instead of underscores. **Score tags are the only tags
  that use underscores.**"*
- *"When using a tag that is different between Danbooru and Gelbooru, **prefer the Gelbooru
  version**."*
- *"Prompt weighting works, but needs a **weight higher than typically used for SDXL**. Example:
  `(chibi:2)`"* — this is why `u/arthan1011` writes `(at night:2.0)` and
  `(split screen, multiple views:1.2)` and reports *"Anima can handle prompt weights like
  `(at night:2.0)` without breaking - use them to push your generation when needed."*
- **Artist tags must be prefixed with `@`.** *"Prefix artist with @. E.g. `@big chungus`. **You
  must put @ in front of the artist. The effect will be very weak if you don't.**"* This is the
  single highest-value trap in the model — silent, invisible, and it degrades every style prompt.
- **Tag order matters:**
  `[quality/meta/year/safety tags] [1girl/1boy/1other] [character] [series] [artist] [general tags]`
  *"Within each tag section, the tags can be in arbitrary order."*
- **Tag dropout was trained in:** *"You don't need to include every single relevant tag."*

### Tag vocabularies

- **Quality — two independent systems, mixable:** human-score (`masterpiece, best quality, good
  quality, normal quality, low quality, worst quality`) and PonyV7-aesthetic-model-derived
  (`score_9 … score_1`). *"You can use either… both together, or neither. All combinations work."*
- **Time period:** `year 2025`, `year 2024`, … and `newest, recent, mid, early, old`.
  `u/RevolutionaryWater31` (Anima-2.9B finetuner) on this: *"the year tags — this has very strong
  influence on the generated image."*
- **Meta:** `highres, absurdres, anime screenshot, jpeg artifacts, official art`.
- **Safety:** `safe, sensitive, nsfw, explicit`. **These are trained conditioning tokens, not
  filters** — see the NSFW section.
- **Dataset tags** — an unusual mechanism. Anima was additionally trained on filtered
  **LAION-POP (ye-pop)** and **DeviantArt**, and those captions carry a dataset tag *"at the very
  beginning of a prompt followed by a newline. Optionally, the second line can contain either the
  image alt-text (ye-pop) or the title of the work (DeviantArt)."* Example given:

```
ye-pop
For Sale: Others by Arun Prem
Abstract, oil painting of three faceless, blue-skinned figures. Left: white, draped figure;
center: yellow-shirted, dark-haired figure; right: red-veiled, dark-haired figure carrying
another. Bold, textured colors, minimalist style.
```

### Recommended prefixes `[model page]`

```
positive: masterpiece, best quality, score_7, safe,
negative: worst quality, low quality, score_1, score_2, score_3, artist name, blurry,
          jpeg artifacts, chromatic aberration
```
For **Aesthetic**: *"You don't need to use quality tags in the positive at all… I recommend not
using `score_*` tags in both the positive and negative prompt. It is already high quality enough
and the score tags can push it too hard into slop territory."*

### The full worked tag prompt `[model page]`

```
year 2025, newest, normal quality, score_5, highres, safe, 1girl, oomuro sakurako, yuru yuri,
@nnn yryr, smile, brown hair, hat, solo, fur-trimmed gloves, open mouth, long hair, gift box,
fang, skirt, red gloves, blunt bangs, gloves, one eye closed, shirt, brown eyes, santa costume,
red hat, skin fang, twitter username, white background, holding bag, fur trim, simple background,
brown skirt, bag, gift bag, looking at viewer, santa hat, ;d, red shirt, box, gift,
fur-trimmed headwear, holding, red capelet, holding box, capelet
```

### Natural-language mode `[model page]`

- *"Follow standard English capitalization rules for character and series names."*
- *"Aim for at least 2 sentences. **Extremely short prompts can give unexpected results.**"*
- *"You can mix tags and natural language in arbitrary order… `masterpiece, best quality,
  @big chungus. An anime girl with medium-length blonde hair is…`"*
- **Name a character, then describe them** — *"`Digital artwork of Fern from Sousou no Frieren,
  with long purple hair and purple eyes, wearing a black coat over a white dress with puffy
  sleeves…` This is extra important when prompting for multiple characters. If you just list off
  character names with no description of appearance, the model can get confused."*

### Community additions

`u/RevolutionaryWater31` (Anima-2.9B author), which mostly restates the above but adds two
things: *"Characters should (think 'must') be follow by their series/copyrights, (think of these
like anchors, they always tag along) follow by their appearances (the more the better)."* and
*"use keywords such as `cinematic composition` and `dynamic angle` [to] improve your image
significantly."* He also warns off junk: *"You can throw away garbage such as 'raytracing' or
'4k' and '8k', these has never done anything and will just poison your output."*

`u/arthan1011` uses ComfyUI **Schedule Prompt** syntax on Anima: `[:closed eyes:0.3]` —
*"`closed eyes` will only activate after 30% of generation steps have finished."*

Wildcards are a gap: `u/rogerbacon50` — *"One big limitation with anima for me was it couldn't do
pipe-deliminated wildcards like other models `{noon | night | sunset}`. The **EasyUseAnima** pack
fixes that."* (`github.com/n0va39/ComfyUI-EasyUseAnima`)

---

## Ecosystem

### Scale

Civitai `baseModels=Anima`, most-downloaded, first 100: **53 LoRAs, 41 checkpoints, 5 workflows,
1 VAE.** The top of the list:

| Model | Type | Downloads | Creator |
|---|---|---|---|
| **MiaoMiao Harem** | Checkpoint | **198,832** | MIAOKA |
| **Anima** (official base) | Checkpoint | **189,872** | circlestone_labs |
| Aesthetic Quality Modifiers - Masterpiece | LORA | 153,330 | motimalu |
| WAI-ANIMA | Checkpoint | 70,532 | WAI0731 |
| AI styles dump (Anima/Illustrious/RouWei/Noob) | LORA | 66,372 | bakariso |
| **Anima Turbo LoRA** | LORA | 59,890 | circlestone_labs |
| AnimaYume | Checkpoint | 47,319 | duongve13112002 |
| Nova Anime AM | Checkpoint | 37,779 | Crody |
| Anima Highres/Aesthetic Boost | LORA | 33,621 | circlestone_labs |
| Anima Workflows | Workflows | 24,173 | Legendaer |
| RDBT \| Anima | Checkpoint | 23,386 | reakaakasky |
| Anima Detail Tweaker | LORA | 22,294 | lse14 |
| AnimaIka | Checkpoint | 20,307 | giko |
| One obsession_Anima | Checkpoint | 20,120 | maxfeifei8 |
| Hassaku (Anima) | Checkpoint | 19,046 | Ikena |
| Anima Cat Tower | Checkpoint | 16,155 | nuko_masshigura |

**A community finetune out-downloads the official base.** That is the ecosystem's shape in one
line, and it mirrors what happened to SDXL.

Also present: `uwumerge Anima Edition (Cute Furry | E621)` and `uwustyle Anima Edition`
(DarkFawkes) — the furry ecosystem has already ported.

### Image conditioning — three competing, all-incomplete mechanisms

This is the most interesting and least settled part of Anima, and it is where a skill adds most
value.

**(a) Cosmos-Reference + Anima Edit LoRA.** `u/arthan1011`: *"What is Cosmos-Reference you ask?
It's a custom node that enables image conditioning in Anima - you need special LoRAs for it to
work and Anima Edit is one of them."* Its limit, verbatim: *"it's too rigid. I can change outfit
and replace background but **changing a pose is almost impossible - feels like ControlNet
Lineart**."*

His **Anima ReStyler** workaround is the best documented trick in the Anima space:
> *"Attach solid-color block to the input image / Run inpaint workflow with mask covering only
> solid-color area / Add `(split screen, multiple views:1.2)` to the prompt… solid white rectangle
> on the right is the canvas for the model to work with, mask limits generation to this solid
> color area, `split screen` in prompt makes the model pay attention(!) to the left half of the
> image, while the Edit LoRA handles Cosmos-Reference image condition to achieve character
> consistency."*

His tips, all quotable: *"Perfect input image is a character in the neutral pose at simple
background… This workflow sometimes struggles with monochrome images/sketches - colorize them
first… It's easy to change style but hard to maintain it. **If you want to change pose of your
character and keep its style 100% consistent you'd better use Wan 2.2.**"* Hit rate: *"Overall it
works 85% of the time."*

**(b) Anima-LLLite — Kohya's ControlNet family, hosted by Comfy Org.**
`u/Corrupt_file32`: *"ah so that's what Anima-LLLite is, saw it on comfyorg huggingface a while
ago. `huggingface.co/Comfy-Org/Anima-LLLite`. **templates also exist in default comfyui, very
stealthy.** the templates are for: Inpainting, Control image (think scribbles, hed, canny) and
depth."*

The new, undocumented one the brief asked about is
`anima-lllite-exp-change-2-000007.safetensors`, and `u/_BreakingGood_` found the craft rule:
> *"It looks like this model is specifically for editing facial expressions. However, through my
> random testing, I figured out **it can perform any kind of edit by running it at a very low
> weight (0.2 to 0.3)**."*

Independently reproduced by `u/tpinho9`: *"i agree with your conclusions as for strenght. 1 it
changes expressions very well, and i find it that **between 0.15 and 0.2** to allow much more
changes while preserving the character."* Demonstrated edits: put her on a beach, put her in a
bikini, turn her around, add a guy and make them kiss, make it a sunset, make them have a picnic.

Status: **unmerged drafts on both sides** — `kohya-ss/sd-scripts` PR **#2413** for the model and
`kohya-ss/ComfyUI-Anima-LLLite` PR **#10** (branch `feat-v3-semantic-trunk`) for the node. It is
described as a v3 *"semantic trunk"* checkpoint that conditions on frozen DiT hidden states of a
reference image rather than a conv-encoded control image — **but that description comes from a
Claude analysis pasted by `u/Radiant_Teaching_811`, not from Kohya. `[LLM-derived, unverified]`**
Dissent on quality: `u/Grand0rk` — *"I see a lot of issues. So not very impressed."*

Also: Anima's own reference ControlNet for pose is weak. `u/Zephrinox`: *"I was trying out their
any reference controlnet for pose and it wasn't that great… tho they did say in their
documentation that pose stuff wasn't good at the time."*

**(c) IP-Adapter — two separate repos, both broken.**
`u/Internal_Answer_6866` tested `github.com/LuciferTC9527/ComfyUI-Anima_IP-Adapter`:
*"It's clearly still under development, the results aren't good. **Without artist tag (the
original artist of the reference image) the character consistency is bad and art style isn't well
transferred.**"* `u/Big_CokeBelly` (r/comfyui) found a *different* one,
`github.com/Wenaka2004/comfyui-anima-ipadapter`, and: *"it seems like there are a lot of missing
files and information"* — no safetensors published.

### Training

`[model page]` finetuning guidance, and it is unusual enough to be a skill section on its own:

> *"**Don't train the LLM adapter.** My own training script, diffusion-pipe, lets you set
> `llm_adapter_lr 0` to completely disable training it, and the example config has this as a
> default. Other trainers like sd-scripts have similar options that should be used. The LLM
> adapter processes the text embeddings before they get to the diffusion model, and therefore
> has an outsized influence on the generated images. The adapter itself contains a surprising
> amount of knowledge and is easy to degrade by training it.*
> *Use a low learning rate. **For a rank 32 LoRA, start with 2e-5.***
> *As a base model, there is no aggressive aesthetic tuning or RLHF you need to overcome when
> finetuning… **A light touch is all you need.**"*

(Note: "my own training script, diffusion-pipe" plus the commercial-licence contact
`tdrussell@circlestone.ai` identifies the author as tdrussell, the diffusion-pipe author.)

Trainers with Anima support: **diffusion-pipe** (author's own), **sd-scripts** (a fork + PR from
`u/RevolutionaryWater31`), **AI Toolkit**, **Anima Standalone Trainer**,
**Aozora** (`github.com/Hysocs/Aozora_Trainer`, SDXL + Anima, 12 GB), and
**LoRA Dataset Studio** (`github.com/perfectgf/lora-dataset-studio`, which lists Anima in its
family-scoped ai-toolkit presets alongside Z-Image, Krea 2, FLUX.1, FLUX.2 Klein, SDXL).

And a genuine warning for the skill: `u/justbob9`, *"I was defeated by a character LORA training
for anima"* — **100+ hours, a week of 24/7 training, AI Toolkit and Anima Standalone Trainer,
multiple datasets and captioning schemes**, and never got a satisfying result for a webtoon
character + that webtoon's art style. Nobody in-thread solved it. Anima character-LoRA training
is not a solved problem.

### Tooling and tag discovery

- **Style Explorers** (ThetaCursed) — `animastyles.thetacursed.com` (**42k+ styles** for Anima
  Base), `xlstyles.thetacursed.com` (16k+ for Illustrious/NoobAI), `kreastyles.thetacursed.com`
  (1.5k for Krea 2 Turbo). Note the ratio: **Anima's artist-tag vocabulary is ~2.6× Illustrious's
  and ~28× Krea 2's** by that measure. His GitHub was suspended at harvest time; these are the
  mirrors. `u/RegenRegn` had already noticed the originals disappear.
- **`tags.latent.moe`** (`u/Chemical-Nose-2985`) — Danbooru tag browser with real image
  references per model. *"Image references for Anima are about 70% done."*
- **Anima "Animedex"** — a character index; `u/Hi7u7` uses absence from it as the check for
  whether a character is baked in.
- **`ComfyUI-EasyUseAnima`** (n0va39) — wildcards + more.
- Runners/UIs with native Anima support: **ComfyUI** (native, plus stock LLLite templates),
  **Forge-Neo**, **InvokeAI** (`u/_BreakingGood_`'s daily driver), **NexusBTA**, **Stimma**
  (LoRA support added), **Mix Studio**.
- Hosted platforms officially supporting Anima `[model page]`: **TensorArt, KusArt, IMGNAI, mage,
  AliveAI, DreamerLand** (plus Civitai).

### The layer-expansion fork war (live, and moving weekly)

- **Anima-2.9B** (`u/RevolutionaryWater31`) — *"v1 preview is **not a 'full' finetune (the whole
  original weights are frozen)**"*, Muon optimizer, ~2.5 epochs (~5 effective with dynamic
  repeats), dataset focused post-September-2025, *"a slight bias toward modern East-Asian anime
  style illustration, this is in fact intended."* Native ComfyUI + Forge-Neo support within 12
  hours of release. LoRA training via his GUI + an sd-scripts fork.
- **Anima-3.8B** (`lylogummy`, `huggingface.co/lylogummy/Anima-3.8B`, node
  `github.com/GumGum10/comfyui-anima-3-8B`) — **posted 2 hours before this harvest**. Adds a
  **Qwen-3.5 4B** encoder on top of 2.9B. Training card, quoted by `u/wiserdking`:
  *"Trained on highly efficient booru dataset containing all tags >5% occurence / 25%
  Natural-language, 25% booru-tag, and 50% dual/hybrid caption views / 40h on a single 4090 /
  Batch size 56 x 10h [256x256 res] / Batch size 28 x 30h [512x512 res]"* — and the author's own
  caveat: *"This is an experimental model. It was trained only for 40h exclusively at very low
  resolution so I wouldn't expect it to be an overall improvement."*

Community reception is sceptical. `u/LaPapaVerde`: *"Lol. Every week we have a new expanded
anima."* `u/GiGiGus`: *"Upscale of an upscale, crazy."* `u/x11iyu`: *"3.8b builds on top of that
extremely undertrained 2.9b and sticks even more layers on top of it + tacks on an additional
encoder, trained only for 40h on a 4090. we've seen bigger training efforts be abandoned
before."* **A skill should cover base Anima and treat 2.9B/3.8B as a footnote until one survives
a month.**

---

## Characters & identity

**Anima's identity story is knowledge-first, not conditioning-first.** It knows an enormous
number of characters by tag (character + series anchors), and the conditioning mechanisms for
"this specific character from this image" are all immature (see Ecosystem (a)/(b)/(c)).

**Knowledge cut-off is September 2025** `[model page]`, and it bites. `u/Hi7u7`: *"I tried to
recreate the RE:Zero character, Capella Emerada Lugunica. Unfortunately, Anima 1.0 couldn't
recreate it, so I had to use a Lora… But, I realized that there were some old anime characters
that I didn't recognize either, nor did they appear in the Anima Animedex."* That is exactly what
Anima-2.9B was built to fix (*"dataset focus on post September 2025"*).

**The character-consistency route people actually use is the ReStyler trick** (Cosmos-Reference +
Edit LoRA + split-screen canvas), and its stated purpose is verbatim *"Transfer character from
the input image into a new image with Anima."* The gap `u/arthan1011` names as still open:
*"What's left is to train with the task of 'Transfer style from input image' - with all stylistic
range of Anime this should be solvable by training Cosmos-Reference LoRA with self-generated
(synthetic) image pairs."*

**Multi-character is a named unsolved problem.** `u/Front_Praline9683` asks for *"a good prompting
tricks to generate more than 2 characters with specific outfits and pose consistently"* — no
answers. `[model page]` acknowledges the same failure and gives the only mitigation: name the
character *and* describe their appearance.

**Anima is the character-still generator for the suite's video models.** This is a real,
repeated production pattern, not a curiosity:
- `u/irmemon225` (122 pts): a 2:19 MiniMax H3 R2V music video, 14 × 10 s segments —
  *"for characters, I generate it using **Anima**."*
- `u/Ok-Wolverine-5020`, twice: *"I used Anima for text2img, then Minimax H3 ref2v with driving
  audio for 15s clips"*; and a full music video where *"I generated the source images locally in
  ComfyUI using Anima."*
- `u/AzuliarTHP`: *"reference Images - Anima / animation clips - minimax H3."*
- `u/BitterAd8431`: *"I used an 'old' image I had generated with Anima and enhanced it using Flux
  Klein 9B in Maestro."*

**And the handoff has a documented trap** worth carrying into the skill.
`u/WearNatural5992`: feeding a high-res Anima/Krea 2 still into H3 loses a lot of face quality at
the first video frame; his fix is *"using an input at 16:9 and make the video at the same aspect
ratio and the loss of quality, especially in face is considerably less than in other aspect
ratios… I am using the shortest side as 768px."* Plus FaceDetailer (impact-pack) after.

---

## NSFW

**Adult content is a first-class trained conditioning axis, not an afterthought.** `[model page]`
lists the safety vocabulary as `safe, sensitive, nsfw, explicit` — four trained tags, sitting in
the same slot as quality and year tags, usable in positive *or* negative. The recommended
positive prefix ships with `safe,` in it precisely because the model will otherwise drift.

That is the whole story of Anima's NSFW posture from primary-ish sources: no refusal layer, a
graded tag. The `explicit` tier is reachable by prompt.

Derivative evidence: `uwumerge Anima Edition (Cute Furry | E621)` and `uwustyle Anima Edition`
(DarkFawkes) on Civitai; `Furry Enhancer` LoRAs across the ecosystem; and Civitai's Anima
checkpoint list is dominated by exactly the kind of merges (`MiaoMiao Harem`, `Hassaku (Anima)`,
`One obsession_Anima`) whose SDXL ancestors were adult-oriented.

**Caveat on measurement:** unauthenticated Civitai API calls appear to be filtered to the SFW
browsing level — the `nsfw` flag came back 0 across 100 Anima results, which is certainly wrong
and should not be reported as evidence of absence.

**Anima did not appear as a subject in r/unstable_diffusion's top-of-month at all.** The one
mention is `u/Dependent_Quit_3730` saying Anima is the only model his 8 GB AMD card can run. So:
the capability is in the model and in the derivative checkpoints, but the adult *video* pipeline
that dominates that subreddit runs on Krea 2 / Flux Klein / LTX 2.3 / SCAIL-2 / H3, not on Anima.
An Anima skill's NSFW section should be about tag control and derivative checkpoints, not about
a scene.

---

## Positioning vs covered models

**vs Illustrious / NoobAI / Pony (all inside `sdxl`).** The community reads Anima as the
successor, explicitly and repeatedly:

- `u/Massive-One-3543`: *"Right now, most people use Anima—just as they used Illustrious before
  that, and Pony prior to that."*
- `u/Time-Teaching1926`: *"I think anima is really good and a **great successor to illustrious**
  but its small parameter model size and small Qwen3 0.6b text encoder does have noticeable
  limits."*
- `u/nazihater3000` (44 pts, 92 comments), framing it as the LoRA-ecosystem question: *"Civitai
  is FULL of Pony/Illustrious and now Anima LORAs, but KREA only shows a handful of character
  LORAs."* Anima is on the ecosystem-rich side of that divide; the suite's own Krea 2 is not.
- Practical migration friction is real: `u/WallabyFearless7863` (r/comfyui) bounced off SDXL and
  landed on Anima — *"I have been using anima lately and have had a lot more success but a lot of
  the creators I follow states using SDXL models."* (His actual SDXL problem turned out to be a
  512×512 latent, not the model — a good cautionary tale for the `sdxl` cross-link.)
- The hybrid people actually run: `u/Alekite` generates with **Illustrious**, then refines with
  **Anima at low denoise**, then FaceDetailer.
- Cross-model style assets already assume both: `AI styles dump (Anima/Illustrious/RouWei/Noob)`
  (bakariso, 66k), `Velvet's Mythic Fantasy Styles` ships an Anima build alongside
  Flux/Pony/Illustrious/Z-Image.

**Against SDXL's anime line, Anima's asymmetries are: bigger artist vocabulary** (42k vs 16k
styles by the Style Explorer count), **a September-2025 knowledge cut-off**, **native
1536² support**, **full finetuning in 11.4 GB**, and — cutting the other way —
**a non-commercial licence** where Illustrious/NoobAI/Pony derivatives are broadly commercial.

**vs Krea 2 / Z-Image / Flux.2.** Different job entirely — `[model page]`: *"will not work well
at realism… This is intended."* The suite's photoreal models and Anima compose rather than
compete, and the composition is already happening (`u/BitterAd8431` Anima → Flux Klein 9B
enhance; `u/WearNatural5992` Anima/Krea 2 → H3).

**vs the video models.** Anima is upstream of them (see Characters & identity). Every video model
in the suite that takes a still or a reference image can take an Anima still, and for anime that
appears to be what people do.

---

## Contested / unresolved

1. **How much data is Anima-2.9B actually trained on?** The author `u/RevolutionaryWater31` says
   *"1.7M is not a very large number of samples"*; `u/x11iyu` says *"the current version of 2.9b…
   is only trained on a measly 45k images."* Both can't be right. `[contested]`

2. **Turbo vs Aesthetic as the default.** Authors recommend Turbo; `u/Time-Teaching1926` says
   Turbo's *"quality, styles, stability and even sometimes prompt Adherence isn't that great."*
   `[contested]`

3. **Do LoRAs survive onto 2.9B/3.8B?** `u/Neonsea1234`: *"Lora dont work Im assuming."* No
   answer. `[unresolved]`

4. **What is `anima-lllite-exp-change-2` architecturally?** The only description in circulation
   is LLM-generated. Kohya published no readme, no announcement. Both PRs are drafts.
   `[unverified — read PR #2413 before asserting anything]`

5. **Is Anima's parameter count 2B?** `[model page]` says *"2 billion parameter"* and the Cosmos
   parent is `Cosmos-Predict2-**2B**-Text2Image`, so this is consistent — but neither the HF card
   nor the config has been read this pass, and the community keeps calling the forks by their
   total (2.9B/3.8B), which will confuse a reader if the skill isn't precise.

6. **Architecture family.** The Cosmos-Predict2 parentage implies a DiT, and the LLLite thread
   refers to *"frozen DiT hidden states"* — but that phrase is from the LLM-generated comment.
   **Confirm against the Cosmos-Predict2 paper/card before writing "DiT" into the skill.**
   `[strong inference, unconfirmed]`

7. **Character-LoRA training difficulty.** `u/justbob9`'s 100-hour failure is one datapoint
   against `[model page]`'s *"A light touch is all you need."* Nobody diagnosed it.
   `[contested]`

8. **Anima on AMD** — two independent reports of memory creep requiring reboots, plus
   8–15 min/image on an RX6600. Whether this is Anima or ROCm is unestablished. `[unresolved]`

---

## Sources

Reddit (all via old.reddit.com):
- `r/StableDiffusion/search?q=Anima&restrict_sr=on&sort=top&t=month`
- `r/StableDiffusion/comments/1vvfzuc/anima38b_with_qwen35_4b_released_by_lylogummy/` — 19 comments
- `r/StableDiffusion/comments/1vn28ac/kohyass_seems_to_have_quietly_released_a/` — 27 comments
- `r/comfyui/search?q=SCAIL+OR+Anima&restrict_sr=on&sort=top&t=month`
- `r/unstable_diffusion/search?q=SCAIL+OR+Anima+OR+LTX&restrict_sr=on&sort=top&t=month&include_over_18=on`
- Read from search-result selftext: 1v729sl (Anima Cosmos-Reference workflow, u/arthan1011) ·
  1v6ej0k (Aozora trainer) · 1v8aks3 (Why so few Krea2 character LORAs) · 1vaxp2s (missing
  characters) · 1voyz0i (Style Explorer mirrors) · 1vamclb (tags.latent.moe) · Anima-2.9B LoRA
  training support (u/RevolutionaryWater31) · Trying Anima's character ipadapter · EasyUseAnima ·
  I was defeated by a character LORA training for anima · Niche and normal tips and Tricks for
  Anima? · Disco Elysium Harry Du Bois LORA · MiniMax H3 R2V hybrid + turbo · MiniMax H3 +
  Hermes Agent music video · MinMax H3 how to fix loss of quality of inputs

Civitai (JSON API, civitai.red, unauthenticated):
- `/api/v1/models/2458426` — the official Anima model page, full description (the `[model page]`
  source throughout; reproduced verbatim in `../research-2026-08-22/raw/civitai-api-2026-08-22.txt`)
- `/api/v1/models?baseModels=Anima&limit=100&sort=Most Downloaded` (and `&period=Month`)
- `/api/v1/models?query=Anima Edit&sort=Most Downloaded`
- `/api/v1/models?query=Cosmos Reference&sort=Most Downloaded`

Named repos / URLs surfaced (not opened — for the primary-source agent):
`huggingface.co/Comfy-Org/Anima-LLLite`, `github.com/kohya-ss/sd-scripts/pull/2413`,
`github.com/kohya-ss/ComfyUI-Anima-LLLite/pull/10`, `huggingface.co/lylogummy/Anima-3.8B`,
`github.com/GumGum10/comfyui-anima-3-8B`, `github.com/LuciferTC9527/ComfyUI-Anima_IP-Adapter`,
`github.com/Wenaka2004/comfyui-anima-ipadapter`, `github.com/n0va39/ComfyUI-EasyUseAnima`,
`github.com/Hysocs/Aozora_Trainer`, `github.com/perfectgf/lora-dataset-studio`,
`animastyles.thetacursed.com`, `tags.latent.moe`, diffusion-pipe (tdrussell),
NVIDIA Cosmos-Predict2-2B-Text2Image + the NVIDIA Open Model License Agreement,
the CircleStone Labs Non-Commercial License.
