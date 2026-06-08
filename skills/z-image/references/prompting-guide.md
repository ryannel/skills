# Z-Image Prompting Guide

## 1. Prompt anatomy

Six parts in this order. Order matters — Qwen parses syntax, so earlier clauses carry more weight.

| Part | What to include | Why |
|---|---|---|
| **Subject** | Who/what; concrete details (age, build, hair, clothing, distinguishing features); at least one non-idealised trait for people | Avoids the stock-photo default |
| **Scene** | Where + when. Z-Image has strong priors for East Asian and European locations — be specific | "narrow alley in Shibuya at 2 a.m." > "Japanese street at night" |
| **Composition** | Shot type, framing, angle, focal length + aperture | Camera language steers framing reliably |
| **Lighting** | Source + direction + quality + colour temperature — always all four | The single highest-leverage variable |
| **Style / medium** | Exactly one dominant medium | Two or more → uncanny valley |
| **Constraints** | **Z-Image:** separate negative prompt. **Turbo:** positive phrasing inside the prompt | See SKILL.md for per-variant CFG / negative rules |

**Length sweet spot:** 80–250 words. Up to 512 tokens (~384 words) by default; set `max_sequence_length=1024` locally for longer prompts. Keep to 3–5 key visual concepts — attention drifts past that.

---

## 2. Realism: killing the plastic default

Z-Image's default prior is airbrushed beauty stock photography. Realism is summoned by photographic specificity, not adjectives.

| Don't | Do |
|---|---|
| "Studio lighting" / "perfect lighting" / "soft lighting" | "Hard direct flash, harsh shadows"; "single bare bulb overhead"; "available window light, golden hour through sheer curtains"; "rim light from a streetlamp behind, fill from the wet pavement" |
| "Smooth skin" / "beautiful" / "flawless" | "Visible skin pores, fine peach fuzz, sun freckles across the nose bridge, a small mole below the left eye, slight under-eye shadow" |
| "8k" / "masterpiece" / "high quality" | "Shot on Leica M6 with Kodak Portra 400 film grain"; "Sony A7R IV, 85 mm f/1.4 GM, ISO 800, slight motion blur on the hand"; "Fujifilm X-T5 35 mm, Fujifilm Pro 400H emulation" |
| "Clean, vibrant, dramatic" | "Dust motes in the light, faint atmospheric haze, smoke from a cigarette, droplets on the lens" |

**Mid-prompt texture anchors** (drop in when faces still look waxy):
`fine linen weave on the shirt` · `matte ceramic finish` · `worn leather grain` · `subsurface scattering on the ears` · `visible fabric pilling` · `chromatic aberration at the edges` · `light ISO grain in the shadows`

---

## 3. Camera vocabulary

### 3.1 Lens reference

| Focal length | Effect | When to use |
|---|---|---|
| **24 mm** | Wide, slight distortion of close subjects; emphasises environment | Full body in a setting, low-angle hero shots |
| **35 mm** | Mild wide; natural reportage feel | Medium shot, cowboy shot, environmental portraits |
| **50 mm** | "Normal" perspective, no distortion | Medium close-up, neutral character work |
| **85 mm f/1.4** | Portrait compression; creamy bokeh | Close-up, bust portraits — default for headshots |
| **100 mm macro** | Extreme detail, very shallow DoF | Extreme close-up (eye, lips, hands) |

Specify focal length + aperture together ("85 mm f/1.4") for the strongest depth-of-field and bokeh effect.

### 3.2 Shot sizes

| Shot | Framing | Prompt phrasing |
|---|---|---|
| **Extreme close-up** | One feature (eye, mouth, hands) | "extreme close-up, 100 mm macro, skin pores around the eye visible" |
| **Close-up** | Head + neck | "close-up portrait, head and neck framed, bottom at the collarbones, 85 mm, shallow DoF" |
| **Medium close-up / bust** | Head + upper chest | "medium close-up, bust shot, from head to mid-chest, 50 mm" |
| **Medium / waist-up** | Head + torso + hands at waist | "medium shot, waist-up, from head to waistline, 35 mm" |
| **Cowboy / mid-thigh** | Head + torso + hands + hips | "cowboy shot, from mid-thigh to top of head, 35 mm, hands fully in frame" |
| **Full body** | Entire figure | "full body, head to feet with breathing room, 24–35 mm, vertical 3:4 crop" |
| **Wide / environmental** | Figure + setting | "wide environmental, subject in the centre third, 24 mm" |

For LoRA datasets: close-up (~30% of images), full body (~20%), the rest as medium and cowboy.

### 3.3 Horizontal rotation — angle clauses (for LoRA datasets)

These clauses describe subject orientation only — combine them with any shot size from §3.2. §3.4 below has full-body framing baked in if you want a ready-to-drop-in version.

Generate all eight with **identical** subject description, lighting, and background — vary only the angle clause. Randomise seed across the set; lock it only while iterating phrasing.

| # | View | Drop-in angle clause |
|---|---|---|
| 1 | Front (0°) | "front view, facing the camera directly, head straight, both eyes equally visible" |
| 2 | Front ¾ right (45°) | "front three-quarter view, body rotated 45° to camera-right, right shoulder closer, head slightly toward camera, both eyes visible" |
| 3 | Profile right (90°) | "right side profile, head and body in full profile facing camera-right, one eye visible, sharp silhouette of nose, lips, and chin" |
| 4 | Back ¾ right (135°) | "back three-quarter view from the right, mostly the back of the head and right shoulder, a sliver of right cheek barely visible" |
| 5 | Back (180°) | "back view, facing directly away from camera, only the back of the head and shoulders visible, hair fully revealed from behind" |
| 6 | Back ¾ left (225°) | "back three-quarter view from the left, mostly the back of the head and left shoulder, a sliver of left cheek barely visible" |
| 7 | Profile left (270°) | "left side profile, head and body in full profile facing camera-left, one eye visible, sharp silhouette of nose, lips, and chin" |
| 8 | Front ¾ left (315°) | "front three-quarter view, body rotated 45° to camera-left, left shoulder closer, head slightly toward camera, both eyes visible" |

**Tips for consistent sets:**
- Keep the lighting direction description byte-identical across all eight views ("soft north-window light from camera-left at 45°").
- For views #4–#6 (back-facing), describe the hair from behind explicitly ("hair gathered in a low ponytail visible from behind, loose strands at the nape").
- Back views are the weakest-trained angles in every modern diffusion model — expect 2–3 retries. Reinforce with "rear three-quarter angle" and explicit back-hair description.
- Baseline pose for the rotation series: "relaxed standing, arms at her sides, neutral expression."

### 3.4 Horizontal rotation — full body (head to feet)

For a full-body set, take each §3.3 angle clause and append a framing clause — no separate table needed: **"full figure from head to feet in frame, 35 mm lens, vertical 3:4 crop"** (use 24 mm for more breathing room around the figure). Pose consistently: "relaxed standing, arms at her sides, feet shoulder-width apart." Include footwear in the subject description — shoes will be fully visible.

- **Front (0°):** "full body, facing the camera directly, feet shoulder-width apart, head to feet in frame, 35 mm lens, vertical 3:4 crop"
- **Back (180°) — the hardest:** "full body back view, facing directly away from camera, full-length figure from head to feet, back of hair and outfit fully visible, 35 mm lens, vertical 3:4 crop"

**Extra tips for full-body views:**
- Describe **footwear** in the subject block ("white canvas high-tops", "black oxford shoes") — it reads clearly in the full-body frame
- Back views (#4–#6): name back-of-outfit details and shoe backs ("back seam and zipper of the jacket visible, black oxford heels")
- Profile views (#3, #7): name silhouette-defining elements ("jacket collar, belt buckle, and shoe profile visible in silhouette")
- Use a **plain neutral backdrop** — the entire outfit is visible, so a busy background competes more than in close-up shots

### 3.5 Elevation shots — face close-up, high and low (for LoRA datasets)

The horizontal 8-point rotation covers azimuthal variety (left–right). Elevation shots add the vertical axis. Together they approach full 3D head coverage. Include **one high and one low** elevation shot per lighting setup in your dataset.

Use **close-up or bust framing** (85 mm f/1.4) — keep the face large in frame so the LoRA learns identity, not environment. See §5 for the full gaze-phrase library.

**Recommended angle:** 30–45° above or below eye level. Extreme overhead and worm's-eye angles are difficult to control and less useful for LoRA training than moderate elevations.

---

#### High elevation (camera above, looking down at the face)

Camera elevated 30–45° above eye level, angled downward. The default failure is chin-up eye contact; give the gaze a forward-or-down anchor.

Prompt pairs — pick one from each column and combine:

| Camera clause | Gaze clause |
|---|---|
| "close-up from above, camera elevated 35° above eye level and angled down to the face" | "her gaze directed straight ahead and slightly downward, unfocused — she has not looked up" |
| "high-angle close-up, camera at 45° above eye level looking down" | "eyes cast gently downward, head held level, completely unaware of the camera above" |
| "above-eye-level portrait angle, looking down at the top and front of the head and face" | "gaze lowered to a point two metres ahead, head level, chin not tilted up" |

**Working prompt (Turbo):**
> Close-up from above, camera elevated 35° above eye level and angled down to the face. A 28-year-old woman, [identity description]. Her gaze is directed straight ahead and slightly downward, unfocused — she has not looked up at the camera. Soft north-window light from camera-left, late afternoon. Shot on a Sony A7R IV, 85 mm f/1.4 GM, Fujifilm Pro 400H emulation, fine grain, visible skin pores. Candid portrait, plain background, no text, no logos.

**For Z-Image, add negative:** `looking up, looking at camera, eye contact, chin tilted up, face tilted up`

---

#### Low elevation (camera below, looking up at the face)

Camera at chin height or slightly below, angled 20–30° upward. Keep it moderate — at extreme worm's-eye, the underside of the jaw dominates and the face becomes hard for the LoRA to read. The default failure is chin-down eye contact; give the gaze a forward-or-up anchor.

| Camera clause | Gaze clause |
|---|---|
| "low-angle close-up, camera at chin level and angled upward 25° to the face" | "her gaze directed straight ahead, past the camera, fixed on the middle distance" |
| "close-up from below, camera positioned below the jaw and angled up to the face" | "chin level, eyes forward, gazing into the distance — unaware of the camera below" |
| "slight upward-angle close-up, camera at shoulder height angled up to the face" | "head held level, gaze fixed on something far ahead, not looking down" |

**Working prompt (Turbo):**
> Low-angle close-up, camera at chin level angled upward 25° to the face. A 28-year-old woman, [identity description]. Her gaze is directed straight ahead, past the camera — she has not looked down. Soft overcast window light from camera-left. Shot on a Sony A7R IV, 85 mm f/1.4 GM, Kodak Portra 400 emulation, light grain, visible skin pores. Candid portrait, plain background, no text, no logos.

**For Z-Image, add negative:** `looking down, looking at camera, eye contact, chin tilted down, smirking down at viewer`

---

## 4. Lighting reference

Always name all four axes:

- **Source:** `window light` · `tungsten desk lamp` · `bare overhead bulb` · `streetlight` · `softbox` · `bare flash` · `sunlight` · `fluorescent ceiling tubes`
- **Direction:** `from camera-left at 45°` · `backlit` · `top-down` · `from below` · `rim light from behind-right`
- **Quality:** `soft diffused` · `hard direct` · `dappled` · `volumetric` · `flat overcast`
- **Colour:** `warm 3200 K tungsten` · `cool 6500 K daylight` · `mixed warm interior + cool window` · `magenta neon`

**Named looks:** `golden hour side light` · `blue hour ambient` · `noon overhead hard sun` · `overcast soft diffused daylight` · `three-point studio (soft key, 1:2 fill, hair light)` · `chiaroscuro single source` · `noir Venetian-blind shadow` · `practical light only (table lamp)`

---

## 5. High- and low-angle gaze control

### High-angle (camera above, looking down)

**Default failure:** the model tilts the chin up so the subject can make eye contact with the lens.

**Fix:** give the eyes a concrete anchor below the subject.

Gaze phrases (use one or two):
- `she is looking down at the [book / phone / her hands / the floor / her coffee cup]`
- `head bowed, chin tucked toward chest, eyes downcast`
- `gaze lowered, focused on the ground in front of her feet`
- `eyes closed, face relaxed`
- `unaware of the camera, candid documentary photograph`

**Working prompt (Turbo — no negatives):**
> A high-angle photograph taken from directly above, looking down at a 28-year-old woman sitting cross-legged on a worn oak floor. She is reading a paperback novel held open in her lap, her head bowed, gaze fixed on the page, brown hair falling forward and partially veiling her face. She is completely unaware of the camera. Soft north-window light from camera-left, late afternoon. Shot on a Sony A7R IV with a 35 mm f/1.8 lens, Kodak Portra 400 film emulation, subtle grain, visible skin texture on her hands. Candid editorial photography, plain background, no text, no logos.

**For Z-Image, add negative:** `looking at camera, looking at viewer, eye contact, face tilted up, looking up, posed portrait`

**Avoid:** the word `portrait` alone (strong eye-contact prior — use "candid documentary photograph" instead) · a high-angle face close-up with nothing below to anchor the gaze · `confident smile`, `posing`, `model pose` (all summon eye contact)

---

### Low-angle (camera below, looking up)

**Default failure:** the model tilts the chin down for a "looking down at viewer" smirk.

**Fix:** give the eyes an anchor above or in the distance.

Gaze phrases:
- `gazing into the distance, looking at the horizon`
- `looking up at the sky / clouds / treetops / building above`
- `head tilted back, chin lifted, face turned skyward`
- `eyes fixed on something out of frame to the upper left`
- `staring straight ahead, ignoring the camera at her feet`
- `eyes closed, face turned to the sun`

**Working prompt (Turbo):**
> A dramatic low-angle photograph taken from ground level, looking steeply up at a tall woman in a long charcoal trench coat standing on a wet city sidewalk at sunset. Her chin is lifted and her gaze is locked on the horizon far above the camera; she has not noticed the camera at her feet. Backlit by an orange-and-pink sky, rim light catching her cheekbone and the edge of her coat. Candid street photography, shot on a Canon EOS R5 with a 24 mm f/1.4 lens, slight lens flare, light haze, 35 mm film grain. Plain wet pavement in the foreground, blurred neon signs in the background.

**For Z-Image, add negative:** `looking down, looking at camera, looking at viewer, eye contact, smirking down at viewer, posed`

**Avoid:** `low angle` + `portrait` + `confident` (summons the "Vogue model looking down" trope) · `looming`, `intimidating`, `dominant`, `powerful` (these intensify the look-down prior — use `heroic`, `contemplative`, `distant`, `focused` instead) · `looking down` without a specific anchor (ambiguous — the model may direct the gaze at the camera)

---

## 6. Bilingual prompting and text rendering

Z-Image renders legible Chinese + English in the same image with strong reliability.

- **Wrap rendered text in straight double quotes:** `the neon sign reads "NIGHT MARKET"`
- Keep each text block in one language: `English title "QUIET STREETS" at the top` and `Chinese subtitle "静谧之城" below it`
- Describe typography separately: `bold red neon serif` · `thin sans-serif white sub-text` · `vertical handwritten brush calligraphy along the right edge`
- Keep rendered text under **~10 words per block** — longer strings degrade
- To exclude a script: "English text only, no Chinese characters on the sign" (positive phrasing works; avoid negatives in Turbo)

---

## 7. Common mistakes

| Mistake | Why it fails | Fix |
|---|---|---|
| Tag soup (`1girl, solo, masterpiece, 8k`) | Qwen was trained on natural-language captions | Write a sentence |
| Negative prompt in Turbo | Officially ignored at the guidance-free setting (ComfyUI CFG **1.0** / diffusers `guidance_scale=0`) | Phrase constraints positively in the main prompt |
| Three media stacked | Z-Image obeys every word literally → uncanny artefacts | Pick exactly one medium |
| 40 adjectives | Attention drifts past ~75 tokens | 3–5 strong concepts; precise > exhaustive |
| Forgetting texture words | Default output is glossy CGI | Name pores, fabric weave, grain, brush strokes |
| Rendered text without quotes | Becomes glyph soup | Wrap in straight double quotes |
| "Realistic", "8k", "masterpiece" | Near-useless tokens for Z-Image | Real camera body + real film stock + one imperfection |
| Turbo LoRA at strength 1.0 | Overcooks colours, edges; loses Turbo speed feel | Drop to ~0.8 |
| 600-word prompt, same seed, many variants | Z-Image converges hard on instruction-following | Reduce to 100–150 words; let the seed drive diversity |
| "High angle" + "looking at viewer" | Model tilts chin up to satisfy both → broken composition | Anchor the gaze on a concrete object below |

---

## 8. Drop-in templates

### A. Identity-anchor portrait (LoRA dataset seed)
> Editorial close-up portrait of a 32-year-old woman with shoulder-length copper hair, sun-freckled olive skin, a small mole below her left jaw, calm relaxed expression. She is standing against a plain warm-grey concrete wall, soft north-window light from camera-left at 45°, late afternoon. Front three-quarter view, body rotated 45° to camera-right, head turned slightly toward the camera, both eyes visible, gaze directed past the lens. Shot on a Sony A7R IV with an 85 mm f/1.4 GM lens, shallow depth of field, Fujifilm Pro 400H film emulation, fine grain, visible skin pores, no retouching aesthetic. Plain background, no text, no logos.

### B. Full-body T-pose reference (wardrobe capture)
> Full-body character reference, the same woman as above, standing in a neutral relaxed pose with arms at her sides, feet shoulder-width apart, facing the camera directly. Plain white seamless studio backdrop, even three-point softbox lighting, no harsh shadows. Shot on a 35 mm lens at f/8, sharp focus throughout, head to feet in frame with breathing room above and below, vertical 3:4 crop. Documentary character-design reference photograph, no text, no logos.

### C. Cinematic environmental wide
> A 24-year-old man in a navy peacoat and dark jeans walks alone along a rain-slick cobblestone street in Stockholm's Gamla Stan at blue hour. Wide environmental shot, the subject occupies the centre-left third of the frame, surrounded by tall pastel townhouses and warm window lights. Backlit by a distant streetlamp, his breath visible in the cold air, reflections on the wet stones. Shot on a Leica Q3 with a 28 mm lens, Kodak Portra 800 emulation, grain visible in the shadows. Cinematic colour grade, teal shadows and amber highlights.

### D. High-angle averted-gaze
> High-angle photograph taken from directly above, looking down at a teenage girl sitting on the wooden floor of her bedroom, knees drawn up to her chest. She is staring at a smartphone held in both hands, head bowed, gaze locked on the screen, completely unaware of the camera. Soft overcast daylight from a window to her left, cool blue-grey shadows. Shot on a Fujifilm X-T5 with a 23 mm f/1.4 lens, candid documentary photography, visible carpet fibres and the texture of her cotton hoodie, light film grain. Plain background, no text.

### E. Bilingual signage scene
> A small ramen stall on a narrow back-alley in Shibuya at midnight, viewed from across the street. The illuminated red noren curtain reads "夜市" in bold white brush calligraphy. A smaller neon sign in the window reads "OPEN" in cursive pink letters. Steam rising from the open kitchen, one customer hunched over a bowl at the counter, back to camera. Shot on a Sony A7 IV with a 35 mm f/1.4 GM lens, available neon and warm interior light, wet pavement reflecting colour. Slight grain, sharp text rendering.
