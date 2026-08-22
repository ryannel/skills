# Anima Prompting Guide

This file owns *writing* an Anima prompt: the tag grammar, the vocabularies, weight calibration, the natural-language and dataset-tag modes, per-variant differences, worked examples. Node wiring, samplers and LoRA loading are [`setup-and-workflows.md`](setup-and-workflows.md); holding a character steady is [`characters.md`](characters.md).

Everything here follows from one model-card sentence: Anima's captions were *"Danbooru-style tags, natural language captions, and combinations of tags and captions."* It reads tags natively because it was taught in tags — even though the thing doing the reading is a Qwen3-0.6B LLM behind an adapter.

## Contents

1. The dialect, and why an LLM encoder ended up here
2. Tag order — the trained slot grammar
3. Quality tags — two independent ladders
4. Rating tags — a trained axis, not a filter
5. Year, meta and general tags
6. Artist tags and the `@` prefix
7. Weighting — recalibrating from SDXL
8. Natural-language mode
9. Dataset-tag mode (ye-pop and DeviantArt)
10. Negatives, and how they change per variant
11. Per-variant prompt differences
12. ComfyUI prompt syntax that works on Anima
13. Common mistakes
14. Worked prompts

---

## 1. The dialect, and why an LLM encoder ended up here

SKILL.md's *one rule* carries the argument: Anima has an LLM encoder ([`z-image`](../../z-image/), [`flux-2`](../../flux-2/), [`krea-2`](../../krea-2/) territory) and a booru dialect with attention weighting ([`sdxl`](../../sdxl/) territory), because **dialect follows the caption corpus, while the encoder only sets the ceiling on what a dialect can express** — and because weighting rides a separate **T5 token stream** the adapter multiplies into its output. Three consequences at the keyboard:

- **No 77-token cliff.** SDXL's tag prompts are shaped by CLIP's chunk boundary; Anima's are not. Forty-tag prompts behave and the card's own runs past fifty. Position still matters (§2), but for *grammatical* reasons — the slot order was trained — not because attention falls off a ledge. There is no `BREAK` here and nothing to use it for.
- **Tags and prose mix freely.** *"You can mix tags and natural language in arbitrary order"* — not usefully possible on a CLIP model.
- **A real ceiling.** 0.6B is small. Clause-heavy relational prose ("the taller girl handing the smaller one a book while looking away") degrades faster than on a Qwen3-4B or Mistral-class encoder; `u/Time-Teaching1926` names this as the model's limit. Express relations as explicit per-character description (§8).

---

## 2. Tag order — the trained slot grammar

The card gives the order the captions were written in, and it is the highest-value structural rule in the model:

```
[quality / meta / year / safety tags]  [1girl / 1boy / 1other count]  [character]
[series]  [artist]  [general tags]
```

*"Within each tag section, the tags can be in arbitrary order."* The discipline is coarse-grained: get the sections in order, then relax inside them.

Two formatting rules that are easy to get wrong and produce no error:

- **Lowercase, spaces not underscores.** *"Score tags are the only tags that use underscores"* — `score_7` keeps its underscore, `blunt bangs` does not become `blunt_bangs`.
- **When Danbooru and Gelbooru disagree on a tag name, prefer the Gelbooru version**. If a tag seems inert, check whether you used the other site's name.

**Tag dropout was trained in.** *"You don't need to include every single relevant tag."* The model was trained with tags randomly dropped, so it fills gaps rather than reading absence as a negative — which is why Anima does not need the exhaustive 60-tag walls Illustrious users write out of habit.

---

## 3. Quality tags — two independent ladders

Anima ships **two separate quality systems, and they compose**: *"You can use either… both together, or neither. All combinations work."*

| Ladder | Tokens | Origin |
|---|---|---|
| **Human score** | `masterpiece` · `best quality` · `good quality` · `normal quality` · `low quality` · `worst quality` | booru aesthetic labels |
| **Aesthetic model score** | `score_9` … `score_1` | derived from the PonyV7 aesthetic model |

The card's recommended positive prefix uses one of each: `masterpiece, best quality, score_7, safe`. Note `score_7`, not `score_9` — unlike Pony's `score_9, score_8_up…` stack, Anima's score tags are a **descriptive axis you set**, not a "more is better" ladder. `score_9` biases toward whatever the aesthetic model rated highest: narrower and glossier.

**On Anima-Aesthetic, use neither ladder.** Its captions had quality tags stripped, and the authors are explicit: *"You don't need to use quality tags in the positive at all… I recommend not using `score_*` tags in both the positive and negative prompt. It is already high quality enough and the score tags can push it too hard into slop territory."* Both ladders, both sides, gone.

---

## 4. Rating tags — a trained axis, not a filter

`safe` · `sensitive` · `nsfw` · `explicit` `[official]`

**Trained conditioning tokens occupying the same prompt slot as quality and year tags**, working in the positive or the negative. No refusal layer to route around, no separate "uncensored" checkpoint to find — the graded axis is in the base model. The consequence runs both ways:

- **If you want SFW output you must say so.** The card warns that *"the model may generate undesired content, especially if the prompt is short or lacking details. Avoid this by using the appropriate safety tags in the positive and negative prompts."* This is why the recommended prefix ships with `safe,` in it. With no rating token the model samples across the whole distribution.
- **If you want adult output, the tag is the lever**, and `sensitive` is a genuinely useful middle rung — suggestive without explicit content — that a binary SFW/NSFW switch cannot express.

On **Turbo** at CFG 1 the negative prompt is inert, so the positive rating tag is doing all the work. That is the one variant where getting this tag right actually matters rather than merely helping. Licence terms and the adult-work craft are in [`characters.md`](characters.md) §6.

---

## 5. Year, meta and general tags

**Year and era tags** — `year 2025`, `year 2024`, … plus `newest`, `recent`, `mid`, `early`, `old`. An unusually strong style lever, because anime style is time-stratified and the training data spans a long period. `u/RevolutionaryWater31`, who has finetuned the model: *"the year tags — this has very strong influence on the generated image."* Reach for these before a stack of adjectives — `year 2025, newest` and `old` produce different line weights, shading and palettes from identical content tags.

**Meta tags** — `highres`, `absurdres`, `anime screenshot`, `jpeg artifacts`, `official art`. The two that most change register are `anime screenshot` (flat cel shading, TV-anime composition) and `official art` (illustration polish).

**General tags** are ordinary Danbooru content tags and carry the bulk of a prompt. Two additions from `u/RevolutionaryWater31`: composition tags earn their place — *"use keywords such as `cinematic composition` and `dynamic angle` [to] improve your image significantly"* — while resolution-marketing tags are harmful, *"You can throw away garbage such as 'raytracing' or '4k' and '8k', these has never done anything and will just poison your output."* For tag discovery, `tags.latent.moe` is a Danbooru browser with per-model image references, ~70% populated for Anima `[community — u/Chemical-Nose-2985]`.

---

## 6. Artist tags and the `@` prefix

**This is the single highest-value trap in the model.**

> *"Prefix artist with @. E.g. `@big chungus`. **You must put @ in front of the artist. The effect will be very weak if you don't.**"* `[official]`

It fails silently: a bare artist name tokenises as ordinary general tags, the image still renders, nothing errors, and the style you asked for is simply not there. Check this first against every "Anima doesn't do styles well" report.

**The vocabulary is Anima's deepest asset.** ThetaCursed's Style Explorer indexes **42k+ artist styles for Anima Base** against 16k+ for Illustrious/NoobAI and ~1.5k for Krea 2 Turbo `[community — ThetaCursed, animastyles.thetacursed.com]`. His GitHub was suspended, so the hosted explorers are mirrors and the URLs are volatile `[flagged — re-verify]`.

**Craft:** stack two or three artists to blend rather than hunting for one exactly-right name — blends are where the large vocabulary pays off. Weight them like anything else (`(@artist name:1.6)` to push, lower to dilute one member of a blend, §7), and keep them in the trained slot, after character and series and before general tags. Separately, **`artist name` belongs in the negative** and does not conflict with `@`-prefixed artists in the positive: it suppresses rendered signatures and watermarks, which the training data is full of.

---

## 7. Weighting — recalibrating from SDXL

Standard ComfyUI attention weighting works: `(term:1.5)`, `(term)` ≈ 1.1, nested parens multiply. What differs is the **scale**:

> *"Prompt weighting works, but needs a weight higher than typically used for SDXL. Example: `(chibi:2)`"* `[official]`

| Model | Usable weight band | What happens past it |
|---|---|---|
| SDXL | ~1.05–1.3 | fried colours, posterisation |
| **Anima** | **~1.5–2.0+**, `(chibi:2)` as the card's own example | degrades gracefully; `(at night:2.0)` is reported stable |

**Why the scale differs.** ComfyUI tokenises an Anima prompt twice — Qwen3 and T5-XXL — forces the Qwen weights to `1.0`, and applies your emphasis as `out = out * t5xxl_weights` on the **adapter's output embeddings**. That is a flat multiplicative scale. CLIP weighting instead *interpolates toward the mean* embedding, which moves conditioning further per unit. Same syntax, blunter instrument, hence bigger numbers.

`u/arthan1011`, who has published more Anima workflow craft than anyone: *"Anima can handle prompt weights like `(at night:2.0)` without breaking — use them to push your generation when needed."* His published prompts run `(at night:2.0)` and `(split screen, multiple views:1.2)` — and by the card's own norms that 1.2 is *low*, worth remembering when you copy community prompts from people carrying SDXL habits.

**Working method:** start at 1.5 for an ignored term, step by 0.25, stop when composition rather than colour starts distorting. A term still inert at 2.0 is usually a vocabulary problem — wrong booru spelling, or a concept the model lacks — not a weight problem.

---

## 8. Natural-language mode

**Both dialects are first-class — this is not a tags-with-a-prose-fallback model.** The captions were tags, natural language *and* mixtures, so prose is a trained register, not a degraded path. §1's claim is narrower: tags map more tightly onto the model's *vocabulary* (characters, artists, poses, ratings all have exact tokens), so tags win wherever a tag exists and prose wins wherever one does not. Most good Anima prompts use both.

Prose has its own rules:

- ***"Aim for at least 2 sentences. Extremely short prompts can give unexpected results."*** A one-line prose prompt is the worst of both worlds: too little signal for the LLM path and no tag structure to fall back on.
- **Follow standard English capitalisation for character and series names** — the opposite of the lowercase tag rule, because these arrived in the prose captions capitalised.
- **Mix freely with tags:** `masterpiece, best quality, @big chungus. An anime girl with medium-length blonde hair is…`. The common shape is a tag prefix carrying quality/rating/artist, then prose carrying the scene. **Keep artist tags in that tag prefix**, as the card's own example does — whether `@` still binds inside a sentence is not documented and not established, so do not find out the hard way on a prompt you care about.
- **Name a character, then describe them.** *"`Digital artwork of Fern from Sousou no Frieren, with long purple hair and purple eyes, wearing a black coat over a white dress with puffy sleeves…` This is extra important when prompting for multiple characters. If you just list off character names with no description of appearance, the model can get confused."*

**Prose over tags** for relations and spatial description tags cannot express ("standing behind and slightly to the left of"), unusual object interactions, and scenes with no booru tag. **Tags** for anything the vocabulary covers — poses, expressions, clothing, framing — because a trained tag is a tighter handle than a paraphrase.

---

## 9. Dataset-tag mode (ye-pop and DeviantArt)

An unusual mechanism most Anima users never discover. Anima was also trained on filtered **LAION-POP (ye-pop)** and **DeviantArt** subsets whose captions carried a **dataset tag at the very start of the prompt, followed by a newline** — optionally with the alt-text (ye-pop) or the work's title (DeviantArt) on the second line. The card's example:

```
ye-pop
For Sale: Others by Arun Prem
Abstract, oil painting of three faceless, blue-skinned figures. Left: white, draped figure;
center: yellow-shirted, dark-haired figure; right: red-veiled, dark-haired figure carrying
another. Bold, textured colors, minimalist style.
```

This is the route to **non-anime, non-booru illustration** — oil painting, abstract, general artwork — otherwise the weakest area of a booru-trained model.

---

## 10. Negatives, and how they change per variant

The recommended baseline:

```
worst quality, low quality, score_1, score_2, score_3, artist name, blurry,
jpeg artifacts, chromatic aberration
```

Read what it does: the bottom rungs of *both* quality ladders, `artist name` to kill rendered signatures, three specific degradation artefacts. Not a wall of anatomy terms — that is not the Anima idiom; quality-ladder negatives do the job more efficiently.

- **Base / Aesthetic** — guidance is live at CFG 3–6, negatives work normally. On **Aesthetic**, strip `score_1, score_2, score_3` along with the positive score tags.
- **Turbo** — CFG 1 is guidance-off and **negatives are inert**. Move every constraint into the positive as a tag: `safe` rather than negating `nsfw`, `simple background` rather than negating `detailed background`, `solo` rather than negating extra characters. Anima's tag vocabulary makes this far less painful than on a prose model, because most negatives have a positive tag meaning the opposite.

---

## 11. Per-variant prompt differences

| | Base | Aesthetic | Turbo |
|---|---|---|---|
| Quality tags | both ladders | **none, either side** | unstated; treat as Base |
| Rating tag | positive + negative | positive + negative | **positive only** (negatives inert) |
| Artist tags | strongest response | works, but competes with the baked style | works; distillation narrows the range |
| Negatives | full baseline | baseline minus quality tags | inert |

**Base rewards a rich, artist-heavy prompt because it supplies no style of its own; Aesthetic and Turbo already have one, so an elaborate style prompt on them partly fights the checkpoint.**

---

## 12. ComfyUI prompt syntax that works on Anima

- **Attention weighting** — `(term:1.8)`, official, see §7.
- **Scheduled prompts** — `[:closed eyes:0.3]` activates `closed eyes` only after 30% of steps `[community — u/arthan1011]`. Useful for details that distort composition from step 0.
- **Pipe wildcards `{noon|night|sunset}` do *not* work** out of the box — `u/rogerbacon50`: *"it couldn't do pipe-deliminated wildcards like other models."* `ComfyUI-EasyUseAnima` (n0va39) restores them.

---

## 13. Common mistakes

| Mistake | Why it hurts |
|---|---|
| Artist tag without `@` | Silent near-total loss of the style effect (§6) |
| SDXL weight values | 1.2 sits below the response threshold (§7); the card's example is `(chibi:2)` |
| `score_9` reflexively | Anima's score tags are descriptive, not a "more is better" stack; `score_7` is the recommended default |
| **Any** quality tag on Aesthetic | Its captions had both ladders stripped; they push toward slop |
| Underscores in general tags | Only score tags use underscores |
| `4k`, `8k`, `raytracing` | Inert at best, poisoning at worst; realism is out of scope by design |
| No rating tag | The model samples the full distribution and drifts NSFW on short prompts |
| An SDXL/Illustrious prompt pasted wholesale | Pony's `source_*`/`rating_safe` vocabulary is not Anima's; `safe`/`sensitive`/`nsfw`/`explicit` is |

---

## 14. Worked prompts

**A — The card's own full tag prompt**, showing the slot grammar at full length. Run it at the template's 30 / CFG 4 / `euler` / `simple`:

```
year 2025, newest, normal quality, score_5, highres, safe, 1girl, oomuro sakurako, yuru yuri,
@nnn yryr, smile, brown hair, hat, solo, fur-trimmed gloves, open mouth, long hair, gift box,
fang, skirt, red gloves, blunt bangs, gloves, one eye closed, shirt, brown eyes, santa costume,
red hat, skin fang, twitter username, white background, holding bag, fur trim, simple background,
brown skirt, bag, gift bag, looking at viewer, santa hat, ;d, red shirt, box, gift,
fur-trimmed headwear, holding, red capelet, holding box, capelet
```

Read the order: era → quality → meta → rating → count → character → series → artist → the rest, unordered.

> **This skill ships no artist list, deliberately.** The only `@` tags quoted anywhere here are the card's own (`@nnn yryr`, `@big chungus`) because those are the two that are verifiable from a primary source. Anima's artist vocabulary is 42k+ entries and changes nothing about the syntax — pull real names from `animastyles.thetacursed.com` and confirm each one renders before building a prompt on it. `@artist one` below is a placeholder, not a tag.

**B — Original character, style-stacked** (Base, 40 steps, CFG 4, `er_sde` — settings illustrative, not vendor-specified)

> `masterpiece, best quality, score_7, year 2025, newest, safe, 1girl, solo, @artist one, (@artist two:1.6), silver hair, long hair, amber eyes, black military coat, gold epaulettes, standing on a battlement at dusk, wind in hair, cinematic composition, dynamic angle, cloudy sky, backlighting`
> Negative: `worst quality, low quality, score_1, score_2, score_3, artist name, blurry, jpeg artifacts, chromatic aberration`

**C — Turbo draft of the same** (Turbo, 10 steps, **CFG 1**, `euler` / `simple`) — constraints moved positive, no negative prompt:

> `masterpiece, best quality, score_7, safe, solo, 1girl, silver hair, long hair, amber eyes, black military coat, standing on a battlement at dusk, simple sky, sharp focus, cinematic composition`

**D — Aesthetic, no quality tags at all** (Aesthetic, 35 steps, CFG 4 → try lower, `euler`)

> `year 2024, safe, 1girl, short brown hair, round glasses, oversized knit sweater, sitting cross-legged on a windowsill, reading, warm afternoon light, indoors, plant on the sill, soft shading`
> Negative: `artist name, blurry, jpeg artifacts, chromatic aberration`

**E — Mixed tag + prose** (Base, 40 steps, CFG 4)

> `masterpiece, best quality, score_7, safe, @artist name. Two students stand in a school corridor at dusk. The taller girl has waist-length black hair and a red ribbon, and is handing a letter to a shorter girl with a blonde bob and green eyes, who looks away in embarrassment. Warm orange light from the windows behind them.`

Prose here because the relationship ("handing to", "looks away") and the two-character disambiguation are exactly what tags cannot express; §8's name-then-describe rule does the heavy lifting.
