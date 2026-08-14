# The Z-Image Prompting Guide for ComfyUI: Character & LoRA Work

**TL;DR**
- Z-Image (both Base and Turbo) is a Qwen-3-text-encoded, single-stream diffusion transformer that reads your prompt like a *sentence*, not a tag list — write 80–250 words of natural English (or Chinese), structured as Subject → Scene → Composition → Lighting → Style → Constraints.
- Z-Image-**Base** fully supports CFG and negative prompts; Z-Image-**Turbo** is distilled and the Tongyi-MAI team confirms it "does not rely on classifier-free guidance during inference… this model does not use negative prompts at all" (HF discussion #8, 27 Nov 2025) — use positively-phrased constraints inside the prompt instead. This single fact changes how you write everything.
- For LoRA dataset work, control gaze and camera angle explicitly using natural-language anchors ("her gaze fixed on the book", "head bowed", "chin lifted toward the sky") rather than relying on `from above` / `from below` alone, which by default makes the subject tilt their head toward the lens.

---

## 1. How Z-Image Thinks (and how that changes your prompts)

Z-Image is built on a **Scalable Single-Stream DiT (S3-DiT)** architecture: text tokens, semantic image tokens, and VAE tokens travel through one unified sequence. The text encoder is **Qwen 3 4B**, an LLM-grade encoder, not the older CLIP/T5 stack used in SD1.5/SDXL/Flux. The practical consequences:

1. **Natural language beats tag soup.** Comma-separated keyword spam (`masterpiece, best quality, 1girl, solo, 8k, trending on artstation`) underperforms full sentences. Qwen parses syntax — prepositions, relative positions, and clauses actually steer the image ("standing **in front of**", "lit **from the side by**", "her gaze **directed past** the camera").
2. **It is bilingual.** English and Chinese are both first-class; you can switch mid-prompt for text rendering or describe Chinese cultural concepts in Chinese without losing fidelity.
3. **It follows instructions unusually well.** This is a double-edged sword — contradictions don't get averaged away, they create uncanny artefacts. Pick one medium, one mood, one lens.
4. **The default prior is "beauty stock photography".** Out of the box, ask for "a portrait of a woman" and you get an airbrushed influencer. Realism in Z-Image is not summoned by the word "realistic"; it is summoned by naming a **camera, lens, film stock, and an imperfect human feature**.

### Base vs Turbo (the decision that shapes your whole workflow)

| | **Z-Image-Base** | **Z-Image-Turbo** |
|---|---|---|
| Steps | 30–50 | 8 effective (official code: `num_inference_steps=9` — "This actually results in 8 DiT forwards", per the official Tongyi-MAI/Z-Image-Turbo HF model card) |
| Guidance (CFG) | 3.0–5.0 typical | 0.0 (official model card comment: `guidance_scale=0.0, # Guidance should be 0 for the Turbo models`); ComfyUI allows 1.0–1.5 if you want weak negative-prompt influence |
| Negative prompts | **Yes** — robust separate conditioning | **Officially no.** In ComfyUI's KSampler, CFG ≥ 1.2 will re-introduce weak negative subtraction at the cost of slower generation and over-saturation |
| Diversity | High (varied identities/poses across seeds) | Lower (Turbo collapses toward the strongest mode) |
| Best for | Final-quality renders, LoRA training base, fine-grained negative control | Rapid iteration, large dataset generation, drafting |
| ComfyUI components | `z_image_bf16.safetensors` + `qwen_3_4b.safetensors` + `ae.safetensors` | `z_image_turbo_bf16.safetensors` + same encoder & VAE |

**Practical rule:** Use Turbo to *find* the prompt and seed you want, then re-render the keepers in Base for the final asset and for LoRA dataset images.

---

## 2. Prompt Anatomy: the 6-Part Structure

Every reliable Z-Image prompt has the same skeleton. Not every part is mandatory, but knowing the full structure lets you diagnose weak outputs.

1. **Subject** — who/what, with concrete details: age, build, hair, clothing, distinguishing features. For people, include at least one *non-idealised* trait (asymmetric feature, weathered skin, freckles, a scar, an unkempt detail) or you will get the stock-photo default.
2. **Scene** — where and when. Z-Image has strong geographic priors, especially for East Asian and European locations. "A narrow alley in Shibuya at 2 a.m. with steam rising from a ramen stall" beats "Japanese street at night".
3. **Composition** — shot type, framing, angle, lens. The model responds to camera language: "medium shot", "close-up", "85 mm f/1.4", "shot on a Leica M6".
4. **Lighting** — the single variable that moves Z-Image output the most. Always name source, direction, quality, and colour temperature: "soft diffused overcast light from camera-left", "hard noon sun, hard shadows on the cheek", "warm tungsten key, cool window fill from behind".
5. **Style / medium** — pick **one** dominant medium. "Analog film photograph", "oil painting with visible impasto", "cel-shaded anime illustration in the style of a key visual". Mixing three styles produces the uncanny valley.
6. **Constraints** — what must (or must not) be present. In Base, you have negatives. In Turbo, you phrase these positively: "plain studio background, no text, no logos, clean and uncluttered".

### Token / length guidance
- The official maximum is **512 tokens** (~384 English words, using the team's stated 0.75 words-per-token ratio); the Tongyi-MAI team member QJerry confirms in HF discussion #8 that you can "set `max_sequence_length` in pipeline calling to 1024 when running the code locally" if you genuinely need longer prompts.
- **Sweet spot: 80–250 words**. Long-and-precise = good. Long-and-poetic = worse. Put the most important keywords (subject, key text-to-render, primary camera/lens) in the first 75 tokens.
- Avoid more than 3–5 *key visual concepts* per prompt; beyond that, attention drifts.

---

## 3. Realism: Killing the "Plastic" Default

Stock-photo gloss is Z-Image's default failure mode. The fix is **photographic specificity**, not adjectives.

**Replace generic descriptors with concrete equipment:**

| Don't (triggers plastic mode) | Do (triggers realism) |
|---|---|
| "Studio lighting", "perfect lighting", "soft lighting" | "Hard direct flash with harsh shadows", "single bare bulb overhead", "available window light, golden hour through sheer curtains", "rim light from a streetlamp behind, fill from the wet pavement" |
| "Smooth skin", "beautiful", "flawless" | "Visible skin pores, fine peach fuzz, sun freckles across the nose bridge, a small mole below the left eye, slight under-eye shadow" |
| "8k", "masterpiece", "high quality" | "Shot on Leica M6 with Kodak Portra 400 film grain", "Sony A7R IV, 85 mm f/1.4 GM, ISO 800, slight motion blur on the hand", "Fujifilm X-T5 35 mm, Fujifilm Pro 400H emulation" |
| "Clean, vibrant, dramatic" | "Dust motes in the light, faint atmospheric haze, smoke from a cigarette, droplets on the lens" |

**The single most effective realism upgrade** is naming a real camera + a real film stock or sensor + a non-idealised facial detail. Community write-ups (Fliki's Z-Image Turbo prompting guide, the Medium "Plastic Curse" piece) all converge on the same finding: photography-vocabulary stacking snaps Z-Image into documentary mode, whereas adjectives like "realistic" or "8k" do almost nothing.

**Mid-prompt texture anchors** (drop these in when faces still look waxy):
`fine linen weave on the shirt`, `matte ceramic finish`, `worn leather grain`, `subsurface scattering on the ears`, `visible fabric pilling`, `chromatic aberration at the edges`, `light ISO grain in the shadows`.

---

## 4. Negative Prompts and "Anti-Constraints"

### If you use Z-Image-**Base**
Negative prompts work. A reusable baseline that consistently reduces cleanup:

```
text, watermark, signature, logo, jpeg artifacts, border,
extra fingers, extra limbs, deformed hands, malformed anatomy,
plastic skin, waxy skin, porcelain skin, airbrushed, beauty filter,
blurry, low resolution, oversaturated
```

For portraits specifically, add: `looking at viewer` (if you want averted gaze), `over-smoothed skin, doll-like, uncanny`.
For products: `cluttered background, dramatic perspective, tilt, harsh reflections, fingerprints`.

Keep negative blocks under ~180 characters. Longer blocks introduce unintended side effects.

### If you use Z-Image-**Turbo**
The Hugging Face guidance from the Tongyi-MAI team (Cxxs, in HF discussion #8, 27 Nov 2025) is explicit: *"this is a few-step distilled model that does not rely on classifier-free guidance during inference. In other words, unlike traditional diffusion models, this model does not use negative prompts at all."*

Three options, in order of preference:

1. **Phrase constraints positively inside the prompt.** "Plain background, no text, no logos, sharp focus, natural hands and fingers, correct anatomy, modest clothing." Qwen has learned what "no logos" means semantically even without a separate negative stream.
2. **Use ComfyUI's KSampler with CFG 1.2–1.5** to re-introduce weak negative-prompt subtraction (mathematically: `noised = pos + (pos − neg) × (CFG − 1)`). Expect generation time to roughly double and colours to over-saturate slightly. Useful for stubborn artefacts; not for general use.
3. **Switch to Base** for that render if you genuinely need strong negative control.

---

## 5. Bilingual Prompting and Text Rendering

Z-Image's killer feature is legible Chinese + English in the same image, far better than Flux.

- **Wrap the exact text in straight double quotes**: `the neon sign reads "NIGHT MARKET"`.
- Keep each text block in **one language**: `English title "QUIET STREETS" at the top` and on a separate line `Chinese subtitle "静谧之城" below it`.
- Describe typography separately: `bold red neon serif`, `thin sans-serif white sub-text`, `vertical handwritten brush calligraphy along the right edge`.
- Keep rendered text under ~10 words per block; longer strings degrade.
- If you want to **exclude** a script, do it positively: "English text only, no Chinese characters on the sign".

---

## 6. LoRA Considerations

If you load a Z-Image LoRA in ComfyUI, the recommended weight is **around 0.8** — the HF community article *Engineering Notes: Training a LoRA for Z-Image Turbo with the Ostris AI Toolkit* (Shawn, 2 Dec 2025) explicitly sets `adapter_weights=[0.8]` in its inference code, and the wider community range of 0.7–0.9 mirrors that finding. Turbo is sensitive — at strength 1.0 it over-cooks (saturation, edge artefacts, less Turbo speed feel). Trigger words go at the very start of the prompt.

When you are **generating training data** for a new character LoRA (the workflow this guide is for), you want diversity within a narrow identity envelope. The proven pattern is:

1. Generate one anchor portrait (front three-quarter, neutral expression, plain background, soft window light, 50 mm equivalent, 1024×1024).
2. Use that anchor as an image-to-image / reference seed (Nano Banana or Flux.1 Kontext for the image-edit step; Z-Image-Base for the final clean render) to produce 15–25 variants covering the 8-point head rotation, varied lighting, varied wardrobe, and varied shot sizes.
3. Caption each image explicitly with its angle/shot so the LoRA disentangles identity from view.

Recommended LoRA training settings (Ostris AI-Toolkit on Z-Image, per the same HF Engineering Notes article): rank 8–16, learning rate 1e-4 (or 5e-5 for tight identity), 1024×1024, 2000–3000 steps for character LoRAs with 15–25 images. An RTX 5090 finishes a 3k-step run in roughly one hour at these settings.

**You must use the Ostris training adapter for Turbo.** The Engineering Notes article describes two variants — `training_adapter_v1.safetensors` (default) and `training_adapter_v2.safetensors` (experimental, often better for character work) — both available from the `ostris/zimage_turbo_training_adapterV2` HF repo path used in the AI-Toolkit YAML config. Without the adapter, the LoRA fights the distillation and produces blurry identity collapse.

---

## 7. Photography & Camera Vocabulary (curated for LoRA dataset work)

For LoRA training you need **consistent, controllable views of one subject**. The vocabulary below has been curated down to the essentials — angles, shot sizes, and gaze control.

### 7.1 The 8-Point Head Rotation

A complete LoRA dataset should include all eight rotations of the head/upper body. Generate each with the **same subject identity description, lighting, lens, and background** — vary only the angle clause. Numbers are clockwise around the subject as you look down on them; the subject is rotating, the camera stays put.

| # | View | Prompt phrasing (drop-in clause) | Notes |
|---|---|---|---|
| 1 | **Front view (0°)** | "front view, facing the camera directly, head straight, both eyes equally visible" | Default; eye contact is fine here if you want it (otherwise add "gaze directed past the camera"). |
| 2 | **Front three-quarter, right (45°)** | "front three-quarter view, body rotated 45 degrees to the camera's right, her right shoulder closer to the lens, head turned slightly toward the camera, both eyes still visible, classic portrait three-quarter angle" | The most flattering and most useful single view for character LoRAs. |
| 3 | **Profile right (90°)** | "right side profile view, head and body in full profile facing camera-right, one eye visible, sharp silhouette of nose, lips and chin" | Pure side view. Add "sharp silhouette against a plain backdrop" to lock it in. |
| 4 | **Back three-quarter, right (135°)** | "back three-quarter view from the right, body rotated 135 degrees, viewer sees mostly the back of her head and her right shoulder, a sliver of cheek and the corner of her right eye barely visible" | Weakest-trained view; expect 2–3 retries. Reinforce with "rear three-quarter angle". |
| 5 | **Back view (180°)** | "back view, facing directly away from the camera, only the back of her head and shoulders visible, hair fully revealed from behind" | Add the exact hair description here — back views over-rely on the hair description. |
| 6 | **Back three-quarter, left (225°)** | "back three-quarter view from the left, body rotated 225 degrees, viewer sees mostly the back of her head and her left shoulder, a sliver of left cheek and the corner of her left eye barely visible" | Mirror of #4. |
| 7 | **Profile left (270°)** | "left side profile view, head and body in full profile facing camera-left, one eye visible, sharp silhouette of nose, lips and chin" | Mirror of #3. |
| 8 | **Front three-quarter, left (315°)** | "front three-quarter view, body rotated 45 degrees to the camera's left, her left shoulder closer to the lens, head turned slightly toward the camera, both eyes still visible" | Mirror of #2. |

**Tips for consistent rotation series:**
- Lock the seed *only* while iterating prompt wording; **randomise the seed** when generating the actual dataset variants so the LoRA sees diversity.
- Keep the **lighting direction described identically** across all eight views ("soft north-window light from camera-left at 45°") — this is critical for LoRA consistency.
- Use a **neutral standing pose, arms relaxed at the sides** ("relaxed standing pose, arms at her sides, neutral expression") as the baseline; never combine reference views with dramatic action poses.
- For views #4–#6, **describe the hair from the back** explicitly ("hair gathered in a low ponytail visible from behind, loose strands at the nape").

### 7.2 Shot Sizes (the essential 6)

These are the most useful framings for character work. Pick one per image; combine with one of the eight rotation views above.

| Shot | Prompt phrasing | What's framed | Use case |
|---|---|---|---|
| **Extreme close-up** | "extreme close-up, macro detail of the left eye, lashes and iris in focus, skin pores around the eye visible, 100 mm macro lens" | One eye, or mouth, or hands only | LoRA texture training; not for identity capture |
| **Close-up** | "close-up portrait, head and neck framed, top of frame just above the hair, bottom at the collarbones, 85 mm lens, shallow depth of field" | Head + neck | Primary identity-capture shot; ~30 % of the dataset |
| **Medium close-up / bust** | "medium close-up, bust shot, framed from the top of the head to mid-chest, 50 mm lens" | Head + upper chest | Wardrobe-top + face combined |
| **Medium shot / waist-up** | "medium shot, waist-up framing, from the top of the head down to the waistline, 35 mm lens" | Head + torso + hands at waist | Hand-pose variety; most "natural" portrait framing |
| **Cowboy shot / mid-thigh** | "cowboy shot, framed from mid-thigh to the top of the head, 35 mm lens, the subject's hands fully in frame" | Head + torso + hands + hips | Classic full-figure framing without the cropping problems of full body |
| **Full body** | "full body shot, full-length portrait, head to feet in frame with breathing room above and below, 24–35 mm lens, vertical 3:4 crop" | Entire figure | Outfit reference, posture; ~20 % of the dataset |
| **Wide / environmental** | "wide environmental shot, the subject occupies the centre third of the frame, surrounded by [setting], 24 mm lens" | Figure plus setting | Optional; useful for style LoRAs but rarely for character LoRAs |

### 7.3 High-Angle Shot (camera above, looking DOWN)

The default failure mode: the model makes the subject tilt their chin **up** to make eye contact with the lens, defeating the angle. Fix it by **giving the eyes a concrete anchor below**, by **adjusting head geometry**, or both.

**Camera vocabulary (any of these work; rank-ordered):**
- "from above" (the most reliable single phrase across all diffusion models)
- "high-angle shot", "overhead shot"
- "bird's-eye view", "top-down view"
- "shot from directly above" (most extreme)

**Gaze-control phrases to pair with it (use one or two, not all):**
- `she is looking down at the [book / phone / her hands / the floor / her coffee cup]`
- `head bowed, chin tucked toward chest, eyes downcast`
- `gaze lowered, focused on the ground in front of her feet`
- `eyes closed, face relaxed` (eliminates the gaze question entirely; works for sleeping / meditating compositions)
- `unaware of the camera, candid documentary photograph`

**Working high-angle prompt (Z-Image-Turbo, no negatives needed):**

> A high-angle photograph taken from directly above, looking down at a 28-year-old woman sitting cross-legged on a worn oak floor. She is reading a paperback novel held open in her lap, her head bowed, gaze fixed on the page, brown hair falling forward and partially veiling her face. She is completely unaware of the camera. Soft north-window light from camera-left, late afternoon. Shot on a Sony A7R IV with a 35 mm f/1.8 lens, Kodak Portra 400 film emulation, subtle grain, visible skin texture on her hands. Candid editorial photography, plain background, no text, no logos.

**For Base, add negative prompt:** `looking at camera, looking at viewer, eye contact, face tilted up, looking up, posed portrait`

**Things to avoid in a high-angle prompt:**
- The word `portrait` alone (carries a strong eye-contact prior — say "candid documentary photograph" instead).
- A high-angle **close-up of just the face** — there is no surface below the subject for the gaze to anchor onto, and the model will default to upturned eye contact. Switch to medium or wider framing.
- Modifiers like `confident smile`, `posing`, `model pose` — these all summon eye contact.

### 7.4 Low-Angle Shot (camera below, looking UP)

The default failure mode: the model makes the subject tilt their chin **down** to make eye contact (often with a "looking down at viewer" smirk that ruins the heroic effect). Fix it by giving the eyes an anchor **above or in the distance**.

**Camera vocabulary:**
- "from below" (most reliable single phrase)
- "low-angle shot", "low angle"
- "worm's-eye view", "ground-level shot"
- "shot from below at the subject's feet" (most extreme)

**Gaze-control phrases:**
- `gazing into the distance, looking at the horizon`
- `looking up at the sky / clouds / treetops / building above`
- `head tilted back, chin lifted, face turned skyward`
- `eyes fixed on something out of frame to the upper left`
- `staring straight ahead, ignoring the camera at her feet`
- `eyes closed, face turned to the sun`

**Working low-angle prompt (Z-Image-Turbo):**

> A dramatic low-angle photograph taken from ground level, looking steeply up at a tall woman in a long charcoal trench coat standing on a wet city sidewalk at sunset. Her chin is lifted and her gaze is locked on the horizon far above the camera; she has not noticed the camera at her feet. Backlit by an orange-and-pink sky, rim light catching her cheekbone and the edge of her coat. Candid street photography, shot on a Canon EOS R5 with a 24 mm f/1.4 lens, slight lens flare, light haze, 35 mm film grain. Plain wet pavement in the foreground, blurred neon signs in the background.

**For Base, add negative prompt:** `looking down, looking at camera, looking at viewer, smirking down at viewer, condescending look, eye contact, posed`

**Things to avoid in a low-angle prompt:**
- The combination `low angle` + `portrait` + `confident` summons the "Vogue model looking down at you" trope.
- `looming`, `intimidating`, `dominant`, `powerful` — these intensify the look-down-at-camera prior because that's how those concepts are visually represented in training data. Use `heroic, contemplative, distant, focused` instead.
- `looking down` is ambiguous in a low-angle shot — the model may interpret it as the subject looking down at the camera. Be specific: `looking down at the city far below` (if she's on a rooftop) or avoid the phrase entirely.

### 7.5 Lens Reference (for character work)

| Focal length | Effect | When to use |
|---|---|---|
| **24 mm** | Wide, slight distortion of close subjects; emphasises environment | Full body in a setting, low-angle hero shots |
| **35 mm** | Mild wide; natural reportage feel | Medium shot, cowboy shot, environmental portraits |
| **50 mm** | "Normal" perspective, no distortion | Medium close-up, neutral character work |
| **85 mm f/1.4** | Classic portrait; gentle compression flatters the face; creamy bokeh | Close-up, bust portraits — this is the default for headshots |
| **100 mm macro** | Extreme detail, very shallow depth of field | Extreme close-up (eye, lips, hands) |

Specify **lens + aperture together** ("85 mm f/1.4") for the strongest effect on depth of field and bokeh.

### 7.6 Lighting (the highest-leverage variable)

Always name **source, direction, quality, colour**:

- Source: `window light`, `tungsten desk lamp`, `bare overhead bulb`, `streetlight`, `softbox`, `bare flash`, `sunlight`, `fluorescent ceiling tubes`.
- Direction: `from camera-left at 45°`, `backlit`, `top-down`, `from below (under-lit)`, `rim light from behind-right`.
- Quality: `soft diffused`, `hard direct`, `dappled`, `volumetric`, `flat overcast`.
- Colour: `warm 3200 K tungsten`, `cool 6500 K daylight`, `mixed warm interior + cool window`, `magenta neon`.

Useful named looks: `golden hour side light`, `blue hour ambient`, `noon overhead hard sun`, `overcast soft diffused daylight`, `three-point studio with soft key, fill at 1:2, hair light`, `chiaroscuro single source`, `noir high-contrast Venetian-blind shadow`, `practical light only (table lamp)`.

---

## 8. Iteration Workflow in ComfyUI

A reliable loop:

1. **Draft fast in Turbo at 1024×1024.** Lock the seed and vary the prompt until composition + identity feel right.
2. **Once happy, randomise the seed** and run 8–12 variants. Pick the strongest.
3. **Re-render the winner in Z-Image-Base** at 30–50 steps, CFG 4.0, same prompt, same seed (Base will reinterpret slightly — that's normal). Use Base's negative prompt to clean up artefacts.
4. **For LoRA datasets**, repeat the above for each of the eight head rotations and each shot size you need, keeping subject description + lighting *byte-identical* across the set.
5. **Upscale afterward** — Z-Image gives great structure; crisp microtexture comes from a separate upscale pass.

**Vary one thing at a time.** If a generation is 80 % right, change a single variable (lens, lighting direction, gaze anchor) and regenerate — don't rewrite the whole prompt.

---

## 9. Common Mistakes (and the fix)

| Mistake | Why it fails | Fix |
|---|---|---|
| Tag soup (`1girl, solo, masterpiece, best quality, 8k`) | Z-Image was trained on natural-language captions, not booru tags | Write a sentence: "a young woman standing alone in a sunlit kitchen, candid documentary photograph" |
| Writing a negative prompt for Turbo | Officially ignored | Phrase constraints positively in the main prompt |
| Stacking three media in one prompt ("photoreal anime cel-shaded oil painting") | Z-Image obeys every word literally → uncanny artefacts | Pick **one** medium |
| Cramming 40 adjectives | Attention drift past ~75 tokens | 3–5 strong concepts; precise > exhaustive |
| Forgetting texture words | Default is glossy CGI | Name pores, fabric weave, grain, brush strokes |
| Forgetting to quote rendered text | Text becomes a glyph soup | Wrap in straight double quotes |
| Generic "realistic, 8k" | Useless tokens for Z-Image | Replace with a real camera body + a real film stock + an imperfection |
| Loading a Turbo LoRA at strength 1.0 | Over-cooks colours and edges | Drop to ~0.8 (HF Engineering Notes inference example uses `adapter_weights=[0.8]`) |
| Repeating a 600-word prompt and expecting variety | Z-Image converges hard on instruction-following | Reduce to 100–150 words and let the seed do the work |
| Asking for "high angle" + "looking at viewer" | Default tilts the chin up to satisfy both → broken composition | Anchor the gaze on a specific object below the subject |

---

## 10. Drop-in Templates

### A. Identity-anchor portrait (LoRA dataset seed)
> Editorial close-up portrait of a 32-year-old woman with shoulder-length copper hair, sun-freckled olive skin, a small mole below her left jaw, calm relaxed expression. She is standing against a plain warm-grey concrete wall, soft north-window light from camera-left at 45 degrees, late afternoon. Front three-quarter view, body rotated 45 degrees to camera-right, head turned slightly toward the camera, both eyes visible, gaze directed past the lens to camera-right. Shot on a Sony A7R IV with an 85 mm f/1.4 GM lens, shallow depth of field, Fujifilm Pro 400H film emulation, fine grain, visible skin pores, no retouching aesthetic. Plain background, no text, no logos.

### B. Full-body T-pose reference (for LoRA wardrobe capture)
> Full-body character reference, the same woman as above, standing in a neutral relaxed pose with arms at her sides, feet shoulder-width apart, facing the camera directly. Plain white seamless studio backdrop, even three-point softbox lighting, no harsh shadows. Shot on a 35 mm lens at f/8, sharp focus throughout, head to feet in frame with breathing room above and below, vertical 3:4 crop. Documentary character-design reference photograph, no text, no logos.

### C. Cinematic environmental wide
> A 24-year-old man in a navy peacoat and dark jeans walks alone along a rain-slick cobblestone street in Stockholm's Gamla Stan at blue hour. Wide environmental shot, the subject occupies the centre-left third of the frame, surrounded by tall pastel townhouses and warm window lights. Backlit by a distant streetlamp, his breath visible in the cold air, reflections on the wet stones. Shot on a Leica Q3 with a 28 mm lens, slight handheld motion, Kodak Portra 800 emulation, grain visible in the shadows. Cinematic colour grade, teal shadows and amber highlights.

### D. High-angle averted-gaze
> High-angle photograph taken from directly above, looking down at a teenage girl sitting on the wooden floor of her bedroom, knees drawn up to her chest. She is staring at the screen of a smartphone held in both hands, her head bowed, gaze locked on the screen, completely unaware of the camera. Soft overcast daylight from a window to her left, cool blue-grey shadows. Shot on a Fujifilm X-T5 with a 23 mm f/1.4 lens, candid documentary photography, visible carpet fibres and the texture of her cotton hoodie, light film grain. Plain background, no text.

### E. Low-angle heroic averted-gaze
> Low-angle worm's-eye-view photograph taken from ground level, looking steeply up at a tall woman in motorcycle leathers standing beside her bike on a desert highway at sunset. Her chin is lifted, her gaze locked on the horizon far in the distance behind the camera; she has not noticed the camera at her feet. Backlit by an orange-and-magenta sky, rim light on her jawline and the edge of her jacket. Hot dry wind tousling her dark hair. Shot on a Canon EOS R5 with a 24 mm f/1.4 lens, slight lens flare, fine 35 mm film grain.

### F. Bilingual signage scene
> A small ramen stall on a narrow back-alley in Shibuya at midnight, viewed from across the street. The illuminated red noren curtain above the entrance reads "夜市" in bold white brush calligraphy. A smaller English neon sign in the window reads "OPEN" in cursive pink letters. Steam rising from the open kitchen, one customer hunched over a bowl at the counter, his back to camera. Shot on a Sony A7 IV with a 35 mm f/1.4 GM lens, available light only — neon and warm interior bulbs, wet pavement reflecting colour. Cinematic colour grade, slight grain, sharp text rendering.

---

## 11. Quick Pre-Flight Checklist

Before you hit *Queue Prompt*, ask:

1. Did I write a sentence, not a tag list?
2. Did I name a **camera body + lens (+ film stock)**?
3. Did I name **light source, direction, quality, colour**?
4. Did I include at least one **non-idealised human feature** (if the subject is a person)?
5. Did I pick **one** style/medium, not three?
6. If using **Turbo**: are all my "no X" constraints phrased positively?
7. If using **Base**: is my negative prompt under 180 characters and free of contradictions with the positive?
8. For a high or low-angle shot: did I give the gaze a **concrete anchor away from the camera**?
9. For LoRA dataset work: is everything except the **rotation/shot-size clause** identical to the previous image in the set?
10. Is any rendered text wrapped in straight double quotes and under 10 words?

If every answer is yes, you are prompting Z-Image the way it was designed to be prompted: long, structured, camera-style, instruction-following, and with constraints baked in.

---

## Recommendations

**Immediate (this week):**
1. Set up two ComfyUI workflows side-by-side — one Turbo (8 steps, CFG 1.0), one Base (40 steps, CFG 4.0) — sharing identical prompt nodes. This gives you the draft/finalise loop in one canvas.
2. Build a personal "anchor prompt" for your LoRA subject following Template A. Save it as a ComfyUI prompt node preset.
3. Generate one image at each of the eight head rotations + each of the six shot sizes (≈14 images), varying only the rotation/shot clause. This is your seed LoRA dataset.

**Next phase (when ready to train):**
4. Expand to 15–25 images by varying wardrobe and lighting *one variable at a time* across the dataset.
5. Train with the Ostris AI-Toolkit using the Z-Image Turbo training adapter v2 (or v1 as fallback), rank 16, learning rate 1e-4, 2000–3000 steps.
6. Test the LoRA at strength ~0.8 against new prompts; iterate by adding 5 more targeted images if specific angles fail.

**Benchmarks that would change the plan:**
- If outputs still look plastic after applying the camera+film+imperfection stack → drop CFG (Base) to 2.5–3.0 and remove "studio lighting" language.
- If gaze control still fails despite all three techniques (concrete anchor + head geometry + negative prompt on Base) → the shot may be incompatible with the framing (e.g., high-angle face close-up); reframe wider.
- If your LoRA shows identity collapse after 2000 steps → reduce learning rate to 5e-5 and re-train; do not just add more steps.
- If Turbo can't hit your composition no matter what you try → switch to Base for that single render; the diversity/control gain is worth the extra 20–30 seconds.

---

## Caveats

- **Z-Image is new (released 27 November 2025).** Community prompting knowledge is still consolidating. The natural-language preference, the no-negatives behaviour of Turbo, and the 512-token cap are all confirmed by the Tongyi-MAI team directly; many other tips in this guide (texture vocabulary, gaze anchors, the 8-point head rotation phrasings) extrapolate from SDXL/Flux behaviour and from community write-ups (Fliki, Apatero, the illuminatianon GitHub gist, ComfyUI docs, RunComfy, the Hugging Face Engineering Notes article). They are well-supported but not all empirically A/B-tested *on Z-Image specifically*.
- **Turbo negative-prompt behaviour is contested.** The official team says negatives are ignored. ComfyUI users (gist comments by `Kaleidia`, `noct-ml`) report that with CFG ≥ 1.2 the KSampler does re-introduce a weak negative effect at the cost of slower generation. Treat negatives in Turbo as a fallback, not a primary tool.
- **Z-Image-Edit and Z-Image-Omni-Base were not yet released at the time of writing**, only the Turbo and (recently) the Base checkpoints. Workflows targeting edit/inpainting will change once those land.
- **The "8-point head rotation" phrasings above are templates, not guaranteed locks.** Back views (#4, #5, #6) are the weakest-trained angles in essentially every modern diffusion model; expect retries. Reinforce with explicit hair-from-behind descriptions.
- **Gaze-control on high/low-angle close-ups remains the hardest case.** When the framing is tight on the face with no surface for the gaze to anchor to, no prompt formula reliably suppresses upturned/downturned eye contact — widen the shot.
- **UK English is used throughout this guide**, but Z-Image's training data is predominantly US English; spellings like "colour" vs "color" make no observable difference to the output, so write in whichever you prefer.