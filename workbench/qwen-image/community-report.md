# Qwen-Image family — community craft report

Slice: **CRAFT — what makes a good result, and the model's failure modes.** Compiled 2026-09-09.
Read-only research; nothing here is a lab result.

**Marks.** `[community — author, venue]` = named author reporting first-hand · `[official]` = the
maintainer of the artefact · `[contested]` = credible sources disagree · `; single report` = uncorroborated.

**Dates.** Reddit reports ages in coarse relative units; converted against 2026-09-09 and marked `≈`.
Hugging Face repo dates are exact. Reddit post IDs are given so every claim is resolvable.

**Unmeasured.** Banodoco is Discord-only and was not searched. Chinese-language venues (Bilibili,
LiblibAI, 吐司, ModelScope discussions) were not sampled — the largest known blind spot here, since Qwen is
a Chinese-first model, and it bears directly on the Chinese-text-rendering question in §1.4.

---

## 1. Prompting

### 1.1 Conditioning class

Qwen-Image conditions on **Qwen2.5-VL-7B**, a vision-language model, not CLIP/T5. Edit feeds the input
image to *both* Qwen2.5-VL (semantic control) and the VAE encoder (appearance control) — the reason it can
do "rotate this object" as well as "recolour this region" `[official — Qwen, Qwen-Image-Edit card,
https://huggingface.co/Qwen/Qwen-Image-Edit, 2025-08-17]`.

Natural-language sentences, never tag soup. The one contributor to answer the official prompt-guide request
on the 2511 repo: the model "uses a llm as clip" and is "a LOT more flexible than all the various guides
suggest" `[community — Andyx1976, https://huggingface.co/Qwen/Qwen-Image-Edit-2511/discussions/7,
2025-12-24]`. Long prompts are tolerated for T2I; for **Edit they actively hurt** (§1.5).

### 1.2 "Positive magic"

Qwen's inference code appends a fixed suffix it names `positive_magic` — English:
`"Ultra HD, 4K, cinematic composition."`, with a Chinese counterpart `[official — QwenLM/Qwen-Image, 2025-08]`.

`[contested]` in practice: it is baked into most ComfyUI templates and Civitai workflow JSONs, so many
users run it unknowingly — but realism-LoRA authors publishing recommended settings do not reproduce it
(Danrisi's cards give sampler/steps/guidance and a plain descriptive prompt) `[community — FortranUA,
r/StableDiffusion 1odsid9, ≈2025-11]`. Nobody has A/B'd it. The mechanical objection — that "cinematic
composition" is a real style instruction to a VL encoder, biasing toward shallow depth of field and warm
grading — is my inference, not a sourced claim.

### 1.3 Negative prompts, true CFG, the CFG-1 regime

| Regime | CFG | Steps | Negative prompt |
|---|---|---|---|
| Base / non-distilled | true CFG 2.5–4.0 | 20–50 | Live and weighted |
| Lightning / distilled | 1.0 | 4 or 8 | **Inert** — no unconditional branch exists to steer away from |

Mixing the two is the commonest misconfiguration. Official 2511 defaults: **40 steps, `true_cfg_scale` 4.0,
`guidance_scale` 1.0, negative prompt a single space** `[official — Qwen, Edit-2511 card, 2025-12-17]`.

One operator, fixed seeds, RTX 4090 `[community — FluffyQuack, r/StableDiffusion,
https://www.reddit.com/r/StableDiffusion/comments/1nravcc/, ≈2025-10]`:

> bf16 50 steps @ CFG 4.0 = **369 s** · fp8 20 steps @ CFG 2.5 = **77 s** · fp8 + Lightning 4 steps @ CFG 1.0
> = **19 s**. "The difference between fp8 with and without lightning LoRA is pretty big… I suggest turning
> the LoRA off. The difference between fp8 and bf16 is much smaller, but bf16 is noticeably better."

Same author: bf16 holds **input colour** closer than fp8 — the first hint that Edit's colour drift is partly
a precision artefact, not only a model behaviour.

### 1.4 Text rendering, Chinese vs English

Bilingual in-image text editing, preserving original font/size/style, is the headline capability; 2509
extended it to editing font, colour and material `[official — Qwen, Edit-2509 notes,
https://huggingface.co/Qwen/Qwen-Image-Edit-2509, 2025-09-22]`.

One first-hand result cuts against "more steps is better": *"In any image I've tested, 4 step lora provides
better results in shorter time (40–50 secs) compared to original 50 step (300 seconds). **Especially in
text** — on the last photo it's not even in a readable state on 50 steps while it's clean on 4 step"*
`[community — Furacao__Boey, https://www.reddit.com/r/StableDiffusion/comments/1ptvjtg/, ≈2026-01]`
`[contested]` — directly opposed by FluffyQuack and nsfwVariant, who rate Lightning a quality loss. A
reconciliation that fits both: Lightning trades texture fidelity for schedule stability on high-frequency
structure like glyphs. Untested.

**No** first-hand Chinese-vs-Latin glyph comparison was found in the sampled venues. Treat "Chinese renders
better" as unverified.

### 1.5 Edit instruction style

The most detailed reproducible craft document on this family is nsfwVariant's 2511 write-up (same author
did the 2509 one the community treated as canonical) `[community — nsfwVariant, r/StableDiffusion,
"Cracked the case on high res + quality Qwen Edit 2511 outputs",
https://www.reddit.com/r/StableDiffusion/comments/1tqm8ic/, ≈2026-06]`. Its rules:

1. **Simple and direct.** "Pretend you're talking to a child."
   Bad: `Place a red apple on the table, ensuring it's in the center and removing the plate that was in the same spot.`
   Good: `Replace the middle plate with a red apple.`
2. **Name what must not change.** `Change her outfit to a bikini top and short shorts.` often also changes
   pose and gets confused by a prosthetic arm. Adding `Leave her robot arm and pose unchanged.` makes it
   correct "99% of the time".
3. **`relight` is a keyword, not a description** — "the magic word", with a fixed grammar:
   `Relight to <strength> <colour> <direction>.` e.g. `Relight to white diffuse.` /
   `Relight to warm backlit.` / `Relight to bright cool frontlit.` It can be the entire prompt.
4. **Framing is promptable**, and is how you build a reference set:
   `Zoom in on the person's upper body. The composition should frame their head and thighs.` /
   `Zoom out to a full body shot.` / `Zoom in for a close up portrait.`

A pixel-perfect edit prompt from a different author, mixing subject reference, scene and grade in three
short clauses `[community — danamir_, https://www.reddit.com/r/StableDiffusion/comments/1o01e6i/, ≈2025-10]`:

```
The blonde girl from image 1 in a dark forest under a thunderstorm, a tornado in the distance,
heavy rain in front. Change the overall lighting to dark blue tint. Bright backlight.
```

### 1.6 Multi-image: `Picture 1:` is a trained format, not a convention

ComfyUI's `TextEncodeQwenImageEditPlus` runs the VL model over each input and splices descriptions into the
conditioning as literally `Picture 1: <desc>  Picture 2: <desc>`. Bypass that node (which §2.4 argues you
should) and you must supply the labels yourself, in that exact shape, because "Qwedit was trained on this
exact format" — and **shorter labels beat richer ones**: "a 5 word description wins over whatever BS the VL
model spews out, every time" `[community — nsfwVariant, 1tqm8ic]`.

```
Picture 1: a man wearing a t-shirt. Picture 2: a top hat.
Make the man in Picture 1 wear the top hat from Picture 2.

Picture 1: a living room. Picture 2: a woman.
Put the woman from Picture 2 into the living room in Picture 1.
```

A complementary 2509-era trick: **name** the subjects and refer to them by name
`[community — goddess_peeler, https://www.reddit.com/r/StableDiffusion/comments/1o1zsny/, ≈2025-10]`:

```
Jane is in image1.  Forrest is in image2.  Bonzo is in image3.
Jane sits next to Forrest.  Bonzo sits on the ground in front of them.
Janes's hands are on her head.  Forrest has his hand on Bonzo's head.
All other details from image2 remain unchanged.
```

The two conventions differ (`image1` vs `Picture 1:`) and were reported a version apart; both work, but the
`Picture N:` form has the stronger justification since it is what the model's own pipeline emits. Qwen
documents **1–3 input images** as the trained range `[official — Edit-2509 notes, 2025-09-22]`.

### 1.7 What the encoder ignores

Negative prompts at CFG 1 (by construction). The VL image description when the node is bypassed —
deliberately ignored, and output improves; A/B'd across sixteen reference-handling variants by one author,
still `; single report` in that nobody has replicated the sweep. Convoluted phrasing is not ignored so much
as mis-served.

---

## 2. Settings ladders

### 2.1 The ladders

| Config | Steps | CFG | Sampler / scheduler | Source |
|---|---|---|---|---|
| Qwen-Image T2I, quality | 50 | guidance 2.5 | `dpmpp_2m` + `beta` | `[community — Danrisi, 1odsid9]` |
| Qwen-Image T2I, realism stack | 12 | 1 | `res_2s` + `bong_tangent` (RES4LYF) | `[community — Top_Buffalo1668, https://www.reddit.com/r/StableDiffusion/comments/1q5hbha/, ≈2026-01]` |
| Qwen-Image 2512, 8 GB card | 8 | — | `euler` + `beta`, shift 57 | `[community — Puzzled-Valuable-985, https://www.reddit.com/r/StableDiffusion/comments/1sme1k0/, ≈2026-05]` `; single report` |
| Edit-2509 bf16 | 50 | 4.0 | — | `[community — FluffyQuack, 1nravcc]` |
| Edit-2509 fp8 | 20 | 2.5 | — | same |
| Edit + Lightning | 4 / 8 | 1.0 | `euler`+`beta` or `er_sde`+`bong_tangent` | widely reported |
| **Edit-2511, quality** | **20 (30 for max sharpness)** | — | **`euler` + `simple`** | `[community — nsfwVariant, 1tqm8ic]` |
| Edit Rapid-AIO merge | few-step | — | `euler_ancestral` + `beta` "highly recommended" | `[community — Phr00t via fruesome, https://www.reddit.com/r/StableDiffusion/comments/1pw3t5t/, ≈2026-01]` |

`[contested]` on samplers: nsfwVariant on Edit — *"No Clownshark this time. It reduces output quality quite
a bit… I also didn't find any sampler/scheduler combos that were better than euler/simple."* Against that,
Top_Buffalo1668 says T2I "realism drops without" `res_2s`/`bong_tangent`, and 000TSC000's 2512 realism
showcase is built on RES4LYF `[community — 000TSC000,
https://www.reddit.com/r/StableDiffusion/comments/1qt5vdw/, ≈2026-02]`. Different models; may both be true.

### 2.2 Shift

`ModelSamplingAuraFlow` is the shift node for Qwen in ComfyUI (the Rapid-AIO workflow also needs `CFGNorm`).
For the Edit upscale LoRA the author is emphatic: *"ModelSamplingAuraFlow is a must, shift must be kept
below 0.3. With higher resolutions you can set it as low as 0.02"* `[community — 1filipis/vafipas663,
https://www.reddit.com/r/StableDiffusion/comments/1ormgsm/, ≈2025-11]`. One T2I report uses **57**
`; single report`, two orders away — evidence that "shift" is differently parameterised across nodes.
**Do not transfer shift values between workflows.**

### 2.3 Resolution, and the megapixel trap

Everything defaults to 1 MP, including ComfyUI's node. That default is wrong for Edit and causes the blur
complaint. Measured, RTX 5090, Edit-2511 `[community — nsfwVariant, 1tqm8ic]`:

- Comfortable **up to ~3 MP**; simple in-place edits go far higher (a working 1728×3072 = 5.3 MP example).
- Above ~3 MP **anatomy** starts failing; re-rolls usually fix it.
- Cost is **non-linear**: 1→2 MP ≈ 2.5×, 1→3 MP ≈ 4×, 1→5 MP ≈ 9.5×.
- Wall clock: 1024² = 38 s (52 s double-ref) · 1920×1088 = 91 s (131 s) · 3072×1728 = 550 s.
- **Working band: 2–3 MP single-image, 1–2 MP multi-image.**
- **Divisible by 16, not 8** — ComfyUI rounds to 8, and the mismatch causes "major ruination along the whole
  edge of your image."

### 2.4 The "Qwen blur / soft" complaint

The most consequential finding here: a widely-believed model property is actually a **workflow bug**.
`TextEncodeQwenImageEditPlus` (a) force-downscales to 1,048,576 px with no opt-out, (b) does it with the
**AREA** method, (c) rounds to 8.

> "The AREA downscale is what makes all of your output images blurry… this huge problem would easily be
> solved by changing the word 'area' to 'lanczos' in the code." `[community — nsfwVariant, 1tqm8ic]`

Fix: bypass the node — encode the prompt separately, VAE-encode each reference yourself, chain
`ReferenceLatent` per source. The same structural fix was found a version earlier from the *zoom* symptom:
*"Disconnect the VAE input from the TextEncodeQwenImageEditPlus node. Add a VAE Encode per source, and
chained ReferenceLatent nodes… the forced 1 Mp resolution scale can be skipped if the VAE input is not
filled"* `[community — danamir_, 1o01e6i]`, demonstrated as a pixel-perfect 1852×1440 edit that
flicker-matches its source. Two independent authors, different symptoms, same fix — strong corroboration.
**Treat "Qwen Edit is soft" as a claim about ComfyUI, not about Qwen.**

**Double-ref.** Feeding the reference images in *twice* improves prompt adherence, sharpness, texture
consistency, off-angle likeness and inpaint/outpaint guesses, at ~50% more time. Always better for
single-image; sometimes confusing for multi-image, so toggle it. The author A/B'd sixteen reference-handling
combinations; the positive/negative conditioning layout (refs plus a zeroed-out positive fed into the
negative) is specific and should not be improvised `[community — nsfwVariant, 1tqm8ic]`.

### 2.5 The Qwen VAE halftone grid

> "The Qwen VAE will often put a subtle halftone grid pattern over your images… more noticeable at higher
> resolutions. This is a feature of pretty much every Qwen-based model, but it's particularly present with
> the Edit model." `[community — nsfwVariant, 1tqm8ic]`

Fix: **downscale to 0.5–0.75×, then re-upscale.** SeedVR2 removes it; `4x Nomos2 HQ DAT2` after a modest
downscale (1920p → 1600p) reduces it. Because Edit works natively at high resolution the round trip costs
almost no detail. Open question for the suite: **Z-Image shares the Qwen VAE family**, so the same trick may
apply there — my inference, untested.

### 2.6 Plastic skin and realism stacking

Three separable causes, routinely conflated:

1. **Distillation.** "The main issue is the same as with Klein Distilled: it makes people's skin look like
   plastic" `[community — nsfwVariant, 1tqm8ic]`; corroborated by an operator who went looking for realism
   LoRAs precisely because Edit-2509 + 4-step Lightning "look quite plastic"
   `[community — Epictetito, https://www.reddit.com/r/StableDiffusion/comments/1o47cq5/, ≈2025-10]`.
2. **Base-model bias.** At 12 steps with `res_2s`/`bong_tangent`, "the skin texture still looks a bit
   plastic. ZIT is clearly superior in terms of realism" `[community — Top_Buffalo1668, 1q5hbha]`; a second
   observer notes Qwen's "plastic look" in passing `[community — Mean_Ship4545,
   https://www.reddit.com/r/StableDiffusion/comments/1pa2mca/, ≈2025-12]`.
3. **Edit patch mismatch** — "my edits usually have smooth skin that don't match the texture of the rest of
   the body" `[community — Square_Empress_777,
   https://www.reddit.com/r/StableDiffusion/comments/1t4stgi/, ≈2026-05]`.

Realism-LoRA stack, Civitai downloads on 2026-09-09: **Lenovo UltraReal** 163,766 and **NiceGirls UltraReal**
113,098 (both Danrisi) · **Famegrid** (UltraMuse, cross-base) 41,476 · **2000s Analog Core** (Danrisi, Hi8
camcorder; card gives `dpmpp_2m`/`beta`/50 steps/guidance 2.5) 30,823 · **Boreal** (kudzueye) 17,075 ·
**qwen-edit-skin** (TL_) 9,987 · **Jibs Skin Detailer** (J1B) 6,179 · **Skin Fix Qwen** (OgreLemonSoup)
5,138. On HF: **SamsungCam UltraReal** (`Danrisi/Qwen-image_SamsungCam_UltraReal`), used at weight **1.0**
and reported to stack with character LoRAs `[community — FortranUA,
https://www.reddit.com/r/StableDiffusion/comments/1ny9h3f/, ≈2025-10]`; **Smartphone Snapshot Photo
Reality** `[community — AI_Characters, https://www.reddit.com/r/StableDiffusion/comments/1o05bmq/, ≈2025-10]`.

Camera/lens/film vocabulary appears as LoRA trigger context, not as a standalone fix. **No** credible
first-hand report says camera words alone defeat the plastic bias.

### 2.7 Seed behaviour

Thin. No Qwen-specific seed pathologies reported anywhere in the corpus. FluffyQuack holds seeds fixed
across precisions and gets comparable-not-identical compositions — expected for rectified flow under a
changed schedule. `; thin`

### 2.8 Denoise ladders for img2img and inpaint

**The weakest area in the corpus.** The community's answer to img2img is "use the Edit model", which has no
denoise dial — the reference-latent path replaces it. What exists: the `Qwen Image Edit Easy Inpaint LoRA`
(`_Envy_`, 4,105 downloads) or masking plus `ComfyUI-Inpaint-CropAndStitch`; the
`Qwen-Image-Blockwise-ControlNet-Inpaint` weights exist but show **0 HF downloads in 30 days**. The one
pipeline publishing numbers is a head-swap workflow: Edit + Lightning 4 steps, auto face detect/mask,
ControlNet **strength 0.9**, a MaskGrow blur dial, SeedVR2 final upscale
`[community — Substantial_Angle680, https://www.reddit.com/r/StableDiffusion/comments/1p8phet/, ≈2025-12]`.
**A denoise ladder must be measured, not cited.**

### 2.9 Upscaling chains

1. **Artefact removal** (§2.5): downscale 0.5–0.75× → SeedVR2, or a modest downscale → `4x Nomos2 HQ DAT2`.
2. **Qwen as the upscaler**: `vafipas663/Qwen-Edit-2509-Upscale-LoRA`. Prompt `"Enhance image quality"` plus
   a scene description — *"the more descriptive it is, the better the upscale effect."* 8-step Lightning,
   ~40 s on an L4, `ModelSamplingAuraFlow` shift < 0.3 (0.02 at high res), sampler LCM best then
   `euler_ancestral` then `euler`. Trained on Unsplash-Lite + UltraHR-100K to recover from 16× downscale,
   50% noise, 3 px blur and JPEG artefacts `[community — 1filipis/vafipas663, 1ormgsm]`.
3. **Edit as restoration** of degraded sources works, with a quirk: it only engages if the prompt also asks
   for a background change — *"when I don't mention anything about altering the background, it refuses to
   upscale/restore"* `[community — Agile-Role-1042,
   https://www.reddit.com/r/StableDiffusion/comments/1oah1v1/, ≈2025-11]` `; single report`.

Also in circulation: `QIE 2509 Deblur LoRA` (addddd, 3,795), `LuisaP Qwen-Edit Upscaler & Denoise V3`
(10,467), `starsfriday/Qwen-Image-Edit-2511-Upscale2K` (18,273 30-day HF pulls).

---

## 3. Edit craft

### 3.1 The line, dated, with 30-day HF pulls (2026-09-09)

| Release | Date | Pulls | Added |
|---|---|---|---|
| Qwen-Image (T2I) | 2025-08-02 | 313,794 | 20B MMDiT base, Apache-2.0 |
| Qwen-Image-Edit | 2025-08-17 | 139,172 | Instruction edit; dual VL + VAE conditioning |
| Edit-2509 | 2025-09-22 | **457,619** | **Multi-image (1–3)**, better person/product/text consistency, **native ControlNet** (depth, edge, keypoint) |
| Edit-2511 | 2025-12-17 | 302,580 | Mitigates image drift, better character consistency, multi-person fusion, **community LoRAs folded into the base**, industrial design, geometric reasoning |
| Qwen-Image-Layered | 2025-12-17 | 82,828 | Layered / RGBA decomposition |
| Qwen-Image-2512 (T2I) | 2025-12-30 | 71,751 | Photoreal-leaning T2I refresh |

All Apache-2.0; ≈1.37 M 30-day pulls across the six. **Edit-2509 still out-pulls Edit-2511** nine months on —
which tracks the LoRA-compatibility break and the 2511 Lightning artefacts in §6, not mere inertia.

### 3.2 Colour / tone shift across edits

Three contributors. **Precision**: bf16 holds input colour better than fp8 `[FluffyQuack, 1nravcc]`.
**2511's contrast regression**, significant enough that the most popular merge exists to fix it — Rapid-AIO
v17 "merged 2509 and 2511 together with the goal of correcting contrast issues and LORA compatibility with
2511 while maintaining character consistency" `[community — Phr00t via fruesome, 1pw3t5t]`. And **residual
per-edit drift**, still visible in the freshest report found — *"there were also some strange color
variations with Qwen, like in the 'water reflection consistency test'"* `[community — DiagramAwesome,
"Qwen-Image-Edit-2511 vs LLaDA-Image-Turbo",
https://www.reddit.com/r/StableDiffusion/comments/1wai459/, 2026-09-08]`.

Mitigation is the same as for identity: **do not chain edits — return to the reference and re-edit.**

### 3.3 The 2509 multi-image workflow

Trained combinations: person+person, person+product, person+scene, 1–3 images `[official, 2025-09-22]`.

- **Clothing transfer is the hardest.** "All models failed… like having Grace wear Leon's outfit… you have
  to expect multiple attempts." The author's hypothesis — mismatched **aspect ratio and crop** between
  inputs `[FluffyQuack, 1nravcc]` — agrees with nsfwVariant's independent advice to make inputs share at
  least one edge dimension. Dedicated LoRAs exist because the base struggles: `Clothes Try On` and
  `Outfit Extractor` (kingroka, 11,744 / 10,360), `Outfit Transfer Helper` (Semichka, 4,679).
- **Pose transfer**: `Pose Transfer - Qwen Edit` (kingroka, 7,523). **Product placement**:
  `Put it here_QwenEdit_V2.0` (Futurlunatic, 6,586).
- **Novel angles are the standout.** dx8152's Multiple-Angles LoRA plus a slider: *"I've never seen any
  model get new subject angles this well… it works on stylized content (Midjourney, painterly) and it's the
  first model ever to work on locations. I've run it a few hundred times, the success rate is over 90%, and
  with the 4-step lora it costs pennies"* `[community — LeoKadi,
  https://www.reddit.com/r/StableDiffusion/comments/1oqx0hx/, ≈2025-11]`. The 2511 port is among the
  most-pulled Qwen LoRAs anywhere (`fal/Qwen-Image-Edit-2511-Multiple-Angles-LoRA`, 63,808/30 days).

### 3.4 Edit as a character-consistency tool

> "It particularly excels at making new shots of characters while maintaining their likeness. It's
> significantly better than Klein at some things (like character likeness)… I don't think there's a better
> open-weight model out there than Qwedit for making new shots of a character without loras, for now."
> `[community — nsfwVariant, 1tqm8ic]`

His reference-building protocol, the most actionable identity recipe found:

1. **Make a nude (or plain-white-underwear) reference even for SFW work.** It gives the model maximal
   information about proportions and how clothing should sit; re-dressing from it is far easier. **No LoRA
   needed** — the sensitive regions lack detail, which does not matter for a reference.
2. **Make several zoom levels** by prompting the zoom; use the **head-to-thighs** framing as the everyday
   reference, a closer one for close-ups.
3. **Make several angles** (Multiple-Angles LoRA).
4. Drive ~90% of new shots off a **single** reference.

**LoRA combos.** Many Qwen-Image T2I LoRAs load and work on Edit, but must be tested individually
`[nsfwVariant, 1tqm8ic]`. **2511 broke LoRA compatibility** relative to 2509 because Qwen folded popular
community LoRAs into the base `[official, 2511 card]`; the community answered with the 2509+2511 merge and a
wave of `-2511` retrains (`anime2real-2511`, `Anything to Real Characters 2511`, the Multiple-Angles port).

**How far identity holds:** no chain-length experiment has been published. Reported: single-edit likeness is
excellent; distant shots degrade and want a FaceDetailer pass — *"For distant shots, Qwen LoRAs often
require FaceDetailer… ZIT sometimes needs it too, but not as often as Qwen"* `[Top_Buffalo1668, 1q5hbha]`.

Edit as a **dataset** tool: a free workflow fans one headshot into a 20-image, 20-angle LoRA training set
with Edit-2509 fp8 + 4-step Lightning, ~130 s on a 5090, with **one-word captions** (just the character
name) reported sufficient across "dozens of loras trained on FLUX, QWEN and WAN"
`[community — acekiube, https://www.reddit.com/r/StableDiffusion/comments/1o6xjwu/, ≈2025-11]`.

---

## 4. Control

Ranked by evidence of use, not capability claims.

| Path | Status |
|---|---|
| **Native ControlNet in Edit-2509+** (depth, edge, keypoint) | **What people actually use.** Ships in the model `[official, 2025-09-22]`; used at strength 0.9 in the head-swap pipeline `[Substantial_Angle680, 1p8phet]` |
| **InstantX Qwen-Image-ControlNet-Union** (T2I) | Alive, modest: **16,345** 30-day pulls. canny / soft edge / depth / pose; `controlnet_conditioning_scale` **0.8–1.0**; trained 50 k steps at 1328×1328 bf16; card warns small-font text is lost unless the text is named in the prompt `[official — InstantX, https://huggingface.co/InstantX/Qwen-Image-ControlNet-Union, 2025-08-20]` |
| **DiffSynth EliGen / V2 / Poster** | **Effectively dead** — every DiffSynth EliGen repo shows **0 downloads in 30 days** (HF API, 2026-09-09) |
| **Qwen-Image-Blockwise-ControlNet** (canny / depth / inpaint) | **Effectively dead** — all variants 0 30-day pulls; the Civitai mirror has 669 lifetime |
| **Qwen-Image-Layered** | Alive (82,828 pulls) but **no first-hand craft report found**, only the release announcement `[community — Different_Fix_2217, "Qwen-Image-Layered just dropped.", ≈2026-01]` `; thin` |
| Depth-driven Edit | One operator reports it works *only* with Lightning loaded — "the outputs always come out very weird" without, at any step count 20–50 `[community — SlowDisplay, https://www.reddit.com/r/StableDiffusion/comments/1o32s3l/, ≈2025-10]` `; single report`, and it contradicts the majority Lightning-is-worse view |

**Headline: routing readers to EliGen or the blockwise ControlNets would route them to abandoned code.**
Native 2509 ControlNet plus InstantX Union covers real practice. InvokeAI 6.13 (≈2026-06) is the only
non-ComfyUI front end with first-class Qwen support — "text to image, image to image, LoRAs, reference
image, regional guidance, and controlnet" `[community — _BreakingGood_,
https://www.reddit.com/r/StableDiffusion/comments/1tp7e6w/, ≈2026-06]`.

---

## 5. Quantisation and VRAM

### 5.1 The precision ladder

> "The FP8 version of Qwedit is **much higher quality than the Q8 GGUF** — always use FP8 if you can… Only
> use Q6 and lower if you absolutely have to. FP8 is 22 GB, so you'll need ~26 GB of combined RAM + VRAM."
> `[community — nsfwVariant, 1tqm8ic]`

`[contested]` — a 6 GB operator reports a different curve: "Q2 is awful, Q3 significantly low quality,
**Q4 and above is good, I did not see much difference between Q4–Q8**"
`[community — gebba, https://www.reddit.com/r/StableDiffusion/comments/1obg25u/, ≈2025-11]`. Different
quality bars: one chasing a ceiling, one a floor.

### 5.2 GGUF — and a maintainer handover to get right

**city96** built the first Qwen-Image GGUFs (`city96/Qwen-Image-gguf`, 2025-08-05, still 50,279 pulls).
**QuantStack** carried the Edit line (`Qwen-Image-Edit-GGUF` 2025-08-18; `Qwen-Image-Edit-2509-GGUF`
2025-09-22, **202,761** pulls). **From 2511 onward the baton passed to `unsloth`** —
`unsloth/Qwen-Image-Edit-2511-GGUF` (2025-12-20) at **281,846** pulls, with nothing from QuantStack for
2511 or 2512. Any guide saying "get the QuantStack GGUF" is a version out of date. Also
`vantagewithai/…-2511-GGUF`, `w3ss/…`, and ByteShape's 2512 re-quantisation (8–17 GB, 2–5× smaller than
bf16, plus a vLLM-Omni/Humming path claiming 2–3× speed on Linux+NVIDIA)
`[community — enrique-byteshape, https://www.reddit.com/r/StableDiffusion/comments/1va0vfu/, ≈2026-08]`.

### 5.3 Nunchaku SVDQuant — the same handover, worse

The org renamed **`nunchaku-tech` → `nunchaku-ai`**, so older links are stale. Official coverage:
`nunchaku-qwen-image` (2025-08-14, 10,324) · `nunchaku-qwen-image-edit` (2025-09-10, **65,174**) ·
`nunchaku-qwen-image-edit-2509` (2025-09-24, 10,514; includes 4-/8-step Lightning-**fused** int4).
**All three stopped updating on 2025-11-16. There is no official Nunchaku build for 2511, 2512 or Layered.**
Third parties fill the gap — `QuantFunc/Nunchaku-Qwen-Image-EDIT-2511` (2026-01-22, 3,553),
`QuantFunc/Nunchaku-Qwen-Image-2512`, `stuqiu/…`, `tonera/Qwen-Image-Edit-2511-Lightning-Nunchaku` — none
with anything like first-party traction.

Nunchaku's own claim for the fused 2509 int4 build: *"runs smoothly even on 8 GB VRAM + 16 GB RAM (just
tweak `num_blocks_on_gpu` and `use_pin_memory`)"* `[official — Dramatic-Cry-417,
https://www.reddit.com/r/StableDiffusion/comments/1nqsf93/, ≈2025-10]`. First-hand speed: 4-step SVDQuant
Edit in **~30 s on a 4060 Ti** `[community — infearia,
https://www.reddit.com/r/StableDiffusion/comments/1nn51kn/, ≈2025-10]`; another operator: "reduces
generation time by more than half… I haven't noticed any loss of image quality" `[Epictetito, 1oq4huh]`.

**Gotcha:** stacking a separate Lightning LoRA on an already-fused Nunchaku build gives a **black image**;
resolved by launching ComfyUI with no extra flags and rebooting. Same thread: "only some LoRAs work with
the Nunchaku Qwen Image LoRA loader node, and not very well"
`[community — Epictetito, https://www.reddit.com/r/StableDiffusion/comments/1oq4huh/, ≈2025-11]`.

### 5.4 Other paths

**fp8 scaled** is the Comfy-Org default (`qwen_image_fp8_e4m3fn`, encoder `qwen_2.5_vl_7b_fp8_scaled`;
`qwen_image_edit_2511_fp8mixed` for 2511). **int8-convrot**: `cardamonnl/Qwen-Image-Edit-2511-int8-convrot`
(2026-07-01, 11,116 pulls), used in the freshest head-to-head in the corpus. **NVFP4** (Blackwell):
`Bedovyy/Qwen-Image-Edit-2511-NVFP4` (2026-01-20, 5,636). **Merged AIO**: `Phr00t/Qwen-Image-Edit-Rapid-AIO`
v17/v18 (model + speed LoRA + VAE; needs `ModelSamplingAuraFlow`, `CFGNorm`, `Edit Model Reference Method`).

### 5.5 VRAM thresholds — synthesised, verify before publishing

| VRAM | Path | Source |
|---|---|---|
| **6 GB** + 32 GB RAM | Edit-2509 **Q8 GGUF** at 1024², 4-step Lightning, CFG 1, 90–120 s/image in SwarmUI — note Q8 on 6 GB via offload, so "GGUF ≤ VRAM" is not the rule | `[gebba, 1obg25u]` |
| **8 GB** + 16 GB RAM | Nunchaku int4 fused-Lightning 2509 (`num_blocks_on_gpu`/`use_pin_memory`); or Q4_K_M 2512 at 8 steps under 40 s | `[official — Nunchaku]`, `[Puzzled-Valuable-985, 1sme1k0]` |
| **12 GB** | Q5–Q6 GGUF or Nunchaku int4; system RAM is the binding constraint for Krita/Invoke front ends | `[community — slickyfatgrease, Arc B580 12 GB + 16 GB RAM, ≈2026-07]` `; single report` |
| **16 GB** | Q8 GGUF or fp8 with blockswap; 8-step Lightning to iterate | inferred |
| **24 GB+** | fp8 (22 GB) native, 20–30 steps, no Lightning, double-ref on | `[nsfwVariant, 1tqm8ic]` |
| **32 GB (5090)** | Everything, incl. 2–3 MP double-ref edits at 91–131 s | same |

**You do not need 24 GB of VRAM for the 22 GB fp8 build** — ComfyUI blockswap needs ~26 GB *combined*; less
VRAM only costs time.

---

## 6. Failure modes

| Symptom | Cause | Fix | Evidence |
|---|---|---|---|
| **Every Edit output is soft / blurry** | `TextEncodeQwenImageEditPlus` downscales to 1 MP with **AREA** resampling — a box filter that destroys detail before the model sees it | Bypass the node; VAE-encode refs yourself into chained `ReferenceLatent`. Or Lanczos-scale first | nsfwVariant 1tqm8ic; danamir_ 1o01e6i |
| **Edit doesn't register with the source ("unzooming")** | Same forced rescale — output is generated at a different scale | Same bypass; edits then land pixel-perfect at native size | danamir_ 1o01e6i |
| **Ruined strip along one edge** | Node rounds to 8; the patchifier wants 16, so the last partial patch is garbage | Size to a multiple of 16 | nsfwVariant 1tqm8ic |
| **Subtle grid / halftone, worse at high res** | The **Qwen VAE decoder**, across Qwen-derived models, strongest on Edit | Downscale 0.5–0.75×, re-upscale (SeedVR2 removes; Nomos2 DAT2 reduces) | nsfwVariant 1tqm8ic |
| **Plastic skin** | (a) distillation collapsing the high-frequency tail, (b) base-model bias, (c) edit/source texture mismatch | Drop Lightning and run 20 steps; or stack Lenovo / SamsungCam / NiceGirls UltraReal, `qwen-edit-skin`, Jibs Skin Detailer | nsfwVariant; Top_Buffalo1668 1q5hbha; Square_Empress_777 1t4stgi |
| **Blocky artefacts on 2511, absent on 2509** | The **2511** Lightning LoRA specifically; persists across `er_sde`/`bong_tangent`, `euler`/`beta`, 8/16/24 steps at 1280×1632 on a 4090 | Use the **2509** Lightning LoRA on 2511, or drop Lightning | MastMaithun https://www.reddit.com/r/StableDiffusion/comments/1qx8awl/ ≈2026-02 · `[contested]`: DrinksAtTheSpaceBar reports the 8-step 2511 LoRA *fixing* the 4-step variant's pixel drift, https://www.reddit.com/r/StableDiffusion/comments/1q5zact/ ≈2026-01 |
| **Lightning LoRA no-ops (returns input, 0.01 s)** | Version skew — the adapter's keys don't bind | Match the Lightning variant to the exact base (Edit / 2509 / 2511 / Image-2512) | imkloon, "Qwen Image Edit 2511 Lightning LORA does nothing", ≈2026-02 `; single report` |
| **Black image, Nunchaku + separate Lightning LoRA** | Lightning already fused into the int4 build, plus flag/driver state | Launch with no extra flags **and reboot**; use the fused build alone | Epictetito 1oq4huh |
| **2509 + old Edit Lightning LoRA gives garbage** | Version skew at the 2509 transition | Use `Qwen-Image-Lightning-4steps-V2.0` (the **non-Edit** one) on 2509 | Caco-Strogg-9, r/StableDiffusion, 2025-09-23 |
| **Colour / tone shift across edits** | fp8 precision; 2511's contrast regression; per-edit drift | bf16 or fp8-mixed; the 2509+2511 Rapid-AIO merge; **re-edit from the reference, never edit the edit** | FluffyQuack 1nravcc; Phr00t 1pw3t5t; DiagramAwesome 1wai459 |
| **"Same face" / demographic bias** | Concept bleeding — some phrases carry a strong prior ("passport photo" → Asian faces) | Name the traits explicitly. Qwen's bleed is reported **weaker** than Z-Image Turbo's | Top_Buffalo1668 1q5hbha |
| **Likeness degrades in distant shots** | Face occupies too few latent tokens | FaceDetailer pass; needed more often than on ZIT | Top_Buffalo1668 1q5hbha |
| **Hands / anatomy break above ~3 MP** | Anatomy priors learned near 1–2 MP | Stay ≤3 MP or re-roll — "usually one of them will turn out fine" | nsfwVariant 1tqm8ic |
| **A specific hand or limb placement won't obey** | Model-level composition limit | None known — one operator failed 16 times and switched models | Mean_Ship4545 1pa2mca |
| **Subject won't face away from camera; negatives don't help** | Same class of limit | None known; try a pose ControlNet | Suboptimal88 https://www.reddit.com/r/StableDiffusion/comments/1oyo4fk/ ≈2025-12 |
| **Pose changes when you only asked for an outfit change** | Under-specified instruction — unmentioned attributes are treated as free | Add "Leave their pose unchanged" → ~99% correct | nsfwVariant 1tqm8ic |
| **Clothing transfer fails between two images** | Mismatched aspect ratio / crop; the concatenation-trained path is framing-sensitive | Match at least one edge dimension; expect retries; use the Clothes Try On / Outfit Extractor LoRAs | FluffyQuack 1nravcc; nsfwVariant 1tqm8ic |
| **Output inherits grain / blur from the source** | Appearance conditioning comes straight from the VAE-encoded source | Clean or upscale the input first, even for "entirely new shots" | nsfwVariant 1tqm8ic |
| **Text unreadable at 50 steps, clean at 4** | Unexplained; hypothesis is glyph drift over a long schedule | Try Lightning for text-heavy edits | Furacao__Boey 1ptvjtg `[contested]` |
| **2512 regressions** — 3 arms, over-sharpened hair, worse anime, adherence falling as the prompt lengthens, collapse with 2–3 LoRAs | The photoreal-leaning finetune | Stay on Qwen-Image or 2511 Edit for stylised work; keep to one LoRA | ByteZSzn https://www.reddit.com/r/StableDiffusion/comments/1q2qe12/ ≈2026-01 |
| **Any LoRA destroys the image on 2512** | LoRA trained for a different Qwen generation; 2511/2512 folded community LoRAs into the base | Use `-2511`/`-2512` retrains; lowering strength does **not** fix it | Friendly-Fig-6015, ≈2026-06 `; single report` |
| **Depth/ControlNet edits look "very weird" without Lightning** | Unknown | Unresolved | SlowDisplay 1o32s3l `; single report` |
| **Restoration prompt ignored** | Edit appears to need a semantic change to anchor on | Also ask for a background change in the same prompt | Agile-Role-1042 1oah1v1 `; single report` |

---

## 7. Ecosystem adoption

### 7.1 Civitai census, run 2026-09-09

Civitai collapses the whole family into **one** base string, `"Qwen"`. Every other spelling (`Qwen-Image`,
`Qwen Image Edit`, `Qwen Image Edit 2509/2511`) returns **zero**, so the census cannot separate T2I from
Edit LoRAs.

| Cut | Count | Explicit | Mature |
|---|---|---|---|
| `--base Qwen --type LORA` | **1,162** (exact, cursor exhausted) | **20%** | **45%** |
| `--base Qwen --type LORA --tag character` | **192** | **31%** | **64%** |
| `--base Qwen --type Checkpoint` | **52** | **21%** | **38%** |

The **character-tagged subset is markedly more adult than the pool** (31% vs 20% explicit) — the shape the
atlas records for other identity-capable bases, and consistent with Edit being used as a character tool.

The atlas's `adult-work.md` currently records Qwen-Image at **24% / 54%**; this run gives **20% / 45%**.
Either the earlier figure used a different cut or the pool has diluted. Reconcile before publishing.

### 7.2 Speed and quant layer, 30-day HF pulls

`lightx2v/Qwen-Image-Lightning` 436,033 · `lightx2v/Qwen-Image-Edit-2511-Lightning` 360,027 ·
`unsloth/Qwen-Image-Edit-2511-GGUF` 281,846 · `QuantStack/Qwen-Image-Edit-2509-GGUF` 202,761 ·
`lightx2v/Qwen-Image-2512-Lightning` 89,730 · `nunchaku-ai/nunchaku-qwen-image-edit` 65,174 ·
`city96/Qwen-Image-gguf` 50,279. (2509's Lightning LoRAs live inside the `Qwen-Image-Lightning` repo, not a
separate one.) **The Lightning LoRAs are pulled more than several of the base models** — whatever the
quality argument says, the ecosystem's default is few-step.

### 7.3 Notable finetunes and merges (52 Qwen checkpoints total)

**Jib Mix Qwen** (J1B, 26,392 downloads, explicit previews) is the leading third-party checkpoint and ships
a companion skin-detailer LoRA. **Qwen-Image-Edit-Rapid-AIO v17/v18** (Phr00t, HF) is the 2509+2511 merge
that fixes 2511's contrast and LoRA compatibility. Then: **Qwen Image Edit - Remix** (FX_FeiHou, 6,270),
**FasciumQWEN** (3,748), **Real-Qwen-Image** (wikeeyang, 3,234), **Hyphoria Qwen** (ecaj, 3,057),
**The Strongest Anything To Real Characters / 动漫转真人** (AIGC_Singularity, 2,722),
**Qwen-Image-Edit-2511_clear / 2509_clear** (easygoing0114, 2,525 / 2,322), **Ratatoskr** (freek22, 2,592),
**IntoRealism Qwen** (enzino, 1,373). Dominated by merges rather than full finetunes — expected at 20B,
where full finetuning is out of hobbyist reach.

On HF, `prithivMLmods` has published a shelf of Edit-2511 LoRAs (Ultra-Realistic Portrait 35,976;
Hyper-Realistic Portrait 24,023; Unblur-Upscale 14,368; Object-Adder 12,338; Object-Remover 9,116; Polaroid,
Anime, Pixar-3D, Noir Comic) — 2511 LoRA training is healthy even though 2509 out-pulls it. Edit-side
utility LoRAs on Civitai: **Consistence Edit Lora** (xiaozhijason, 56,201), **LuisaP Qwen-Edit Upscaler &
Denoise V3** (10,467), **Qwen Edit Reality Transform** and **Figure Maker** (aldniki217, 9,892 / 9,513),
**PanelPainter** manga colouring (Proper-Employment263, weight 0.45–0.6), **Coloring Book Qwen Image Edit**
(renderartist, released under Apache-2.0).

### 7.4 The NSFW ecosystem, and what "refusal" means

**The encoder does not refuse.** The cleanest statement of the mechanism:

> "It loads Qwen the SAME way that any other model loads any other text encoder… purely processing, with
> absolutely none of the typical Qwen chat format personality being 'alive'. This is why it also cannot
> refuse prompts that Qwen certainly otherwise would in a conventional chat context."
> `[community — ZootAllures9111, https://www.reddit.com/r/StableDiffusion/comments/1pm5vw0/, ≈2025-12]`

Written about Z-Image, but the claim is about how diffusion models consume LLM hidden states, and
Qwen-Image consumes Qwen2.5-VL the same way. What users experience as censorship is **data suppression in
the diffusion weights** — vague anatomy, not an error — hence recurring "only generating SFW images"
questions `[community — Practical-Shake3686,
https://www.reddit.com/r/StableDiffusion/comments/1po13po/, ≈2026-01]` and a community answer built on
LoRAs and merges rather than jailbreak prompts.

**Abliterated encoders.** They exist —
`dummy9996/Qwen2.5-VL-7B-abliterated_nvfp4_int8convrot_comfyui` (2026-07-06, 641 pulls) is a ComfyUI-ready
build; `huihui-ai/Qwen2.5-VL-7B-Instruct-abliterated` (2025-02-17, 18,001) is upstream. The evidence is
against them from two directions:

1. **The author of the leading abliteration tool says it cannot work.** *"When the hidden states from an
   'uncensored' LLM are passed to the diffusion model… it's seeing slightly perturbed representations
   compared to what it was trained on. This either has no effect at all, or the effect of reducing prompt
   adherence and potentially introducing artifacts. But it will never, ever remove censorship from the
   output."* `[community — -p-e-w-, creator of Heretic,
   https://www.reddit.com/r/StableDiffusion/comments/1vmdxzk/, ≈2026-08-13]` — 2,591 points.
2. **The leading Qwen-Edit craft author agrees empirically**: *"Use only the normal FP8 text encoder with
   Qwedit; abliterated/GGUF encoders will reduce your output quality."* `[nsfwVariant, 1tqm8ic]`

`[contested]`, but weakly: *"I saw comments before that ablated TE can def make Qwen Image Edit better"*
`[community — Witty_Mycologist_995,
https://www.reddit.com/r/StableDiffusion/comments/1qgmx83/, ≈2026-02]` — second-hand, no A/B anywhere.

**Where the adult ecosystem lives:** LoRAs and merges. `Baraje/SexGod_NSFW_Female_Nudes_QWEN_Image_Edit_2511`
pulls 15,335/30 days; 20% of Civitai's 1,162 Qwen LoRAs and 31% of its character LoRAs carry explicit
previews; Dead_Sec's cross-base `Japanese Asian Ai Character - SFW+NSFW - Qwen 2512 / Z Image` (6,701) shows
the packaging pattern. Note that nsfwVariant's "nude reference" advice (§3.4) is a craft recommendation for
SFW work too, and needs no LoRA.

---

## Contested

1. **Lightning: quality loss or gain?** Loss — FluffyQuack 1nravcc, nsfwVariant 1tqm8ic, Top_Buffalo1668
   1q5hbha. Gain — Furacao__Boey 1ptvjtg, specifically for text. Likely task-dependent; unresolved.
2. **`euler`/`simple` vs RES4LYF.** nsfwVariant says exotic samplers hurt on **Edit**; Top_Buffalo1668 and
   000TSC000 say they are needed for realism on **T2I**. Probably not a real contradiction, but untested
   across both.
3. **fp8 vs Q8 GGUF.** "Much higher quality" (nsfwVariant) vs "not much difference Q4–Q8" (gebba).
4. **2511 Lightning: broken or fixed?** MastMaithun sees blocky artefacts 2509's LoRA doesn't produce;
   DrinksAtTheSpaceBar reports the 8-step 2511 LoRA fixing the 4-step variant's pixel drift.
5. **Abliterated text encoders.** Heretic's author and the leading craft author say no, with a mechanism; a
   minority say yes, second-hand and without an A/B.
6. **"Positive magic".** In the official code and most templates; absent from every realism-LoRA author's
   published settings. Never tested head to head.
7. **Adult share on Civitai.** This run 20% / 45%; the atlas's existing row 24% / 54%.

## Thin / single-report

- **Denoise ladders for img2img and inpaint** — essentially absent; must be measured, not cited.
- **Chinese vs English text rendering** — vendor claim only; no first-hand comparison in sampled venues.
- **Seed behaviour** — no Qwen-specific reports at all.
- **Qwen-Image-Layered craft** — 82,828 monthly pulls, zero settings-level reports. A real gap.
- **Depth/ControlNet needing Lightning to behave** (SlowDisplay 1o32s3l) — one report, contradicts the
  majority view, mechanism unknown.
- **Restoration needing a background-change clause** (Agile-Role-1042 1oah1v1) — one report.
- **Lightning LoRA no-op in 0.01 s** (imkloon) — one report; the cause (version skew) is obvious.
- **Shift = 57 on 2512** (Puzzled-Valuable-985 1sme1k0) — one report, two orders off everything else;
  almost certainly a different parameterisation.
- **12 GB threshold** — inferred from one Krita/Arc B580 report about RAM-driven disconnects.
- **Identity across an edit chain** — the qualitative advice (don't chain) is well supported; no number
  exists.
- **The halftone also affecting Z-Image** (shared VAE family) — my inference, not a community claim.
