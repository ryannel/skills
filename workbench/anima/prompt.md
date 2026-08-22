# Brief: an `anima` skill

**Status:** not started. Source: `workbench/research-2026-08-22/FINDINGS.md` §4.

## What it is

**Anima** — a **2 billion parameter text-to-image model**, a collaboration between
**CircleStone Labs and Comfy Org**. Anime concepts, characters and styles first, but
capable across non-photorealistic work generally; explicitly **not for realism**. Trained
on several million anime images. (Description read from its Civitai model page, 2026-08-22
— go to the primary repo before asserting any of it.)

## Why it belongs in the suite

The suite has an anime hole. Illustrious, NoobAI and Pony are covered *inside* `sdxl`,
correctly, because they are SDXL finetunes. **Anima is a separate 2B architecture**, so
it cannot live there.

And it is not niche. On a Civitai most-downloaded-this-month sample (2026-08-22), base-model
tags ranked: Illustrious 252, Krea 2 204, **Anima 180**, ZImageTurbo 137, Pony 126. The top
Anima checkpoint (`MiaoMiao Harem`) had ~199k downloads on its own. It is the third-largest
base-model ecosystem on the site and the suite does not name it once.

Comfy Org's involvement also means first-class ComfyUI support is likely, which lowers the
cost of covering it.

## What the sweep established (community only — verify everything)

**Its conditioning story is unusual and is probably the skill's spine.**
**Cosmos-Reference** is a custom node that enables **image conditioning** in Anima; it
requires special LoRAs, of which **Anima Edit** is one. That turns Anima into a
character-focused image-edit model — but a **rigid** one: outfit and background change
work, **pose change is nearly impossible**, described as behaving like ControlNet Lineart.

**A community workaround worth documenting** (`arthan1011`'s "Anima ReStyler"): stitch a
solid-colour block onto the input image, mask *only* that block, add
`(split screen, multiple views:1.2)` to the prompt — the Edit LoRA reads the left half as
a Cosmos-Reference condition and fills the empty canvas with the same character in a new
pose, style or environment. The workflow handles the stitching and cropping. Author's tips:
seeds are not equal (Anima is seed-unstable and some seeds simply ruin a generation);
the ideal input is a neutral-pose character on a simple background.

**kohya-ss quietly published a ControlNet** — `anima-lllite-exp-change-2-000007.safetensors`
— giving Anima broad edit capability (relocate the subject, change clothing, turn the
character around, add a second character, change time of day). Uploaded without
announcement or documentation. Verify it still exists and find out what it actually is.

**Note the prompt register.** `(split screen, multiple views:1.2)` is **weighted tag
syntax**, not sentences — so Anima is likely in the CLIP-ish/tag-prompted class rather
than the LLM-encoder class that governs Krea 2, Z-Image and Flux.2. Confirm the text
encoder before writing the prompting guide; getting the encoder class wrong would make
the whole skill wrong in the way `media-model-skill` warns about.

**Ecosystem names seen:** MiaoMiao Harem, Nova Anime AM, RDBT | Anima (checkpoint + LoRA),
AnimaIka, One obsession_Anima, Hassaku (Anima), plus an "Anima Workflows" collection.
Velvet's Mythic Fantasy Styles ships an Anima build alongside Flux/Pony/Illustrious/ZiT.

## Authoring notes

- Follow `.agents/skills/media-model-skill` — image modality.
- Open questions to settle before drafting: parameter count and architecture (2B — DiT or
  UNet?), text encoder and therefore prompt dialect, VAE, licence, native resolution,
  official repo, and whether Comfy Org ships a stock template.
- Cross-links: `sdxl` (Illustrious/NoobAI/Pony — the incumbent anime ecosystem and the
  honest comparison), `character-lora-training`, `image-production-workflows`.
- The `sdxl` skill should gain a routing line once this exists: "for anime, Anima is now
  a separate architecture worth weighing against Illustrious."
