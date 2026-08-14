# Authoring a still-image model skill

Read this alongside `SKILL.md` when the model generates or edits **still images**. It covers the four shape-dependent anatomy items (spine, one-rule, per-variant settings, signature technique), the conditioning-class doctrine — which **video authors should read too** — image failure modes, and the image mechanics of the three pillars.

## Ground truth — read these before drafting

Five finished skills in `skills/generative-media/`. **Pattern-matching against them beats anything written here.** Read `z-image` plus whichever example matches your model's shape in full; skim the others and their `references/`.

| Skill | Organised by | Its "one rule" | Best-in-class for |
|---|---|---|---|
| `z-image` | **variant** (base vs Turbo) | write a sentence, not a tag list | character protocol, multi-stage pipeline, the two-bar closing section |
| `ideogram-4` | **surface** (web app / hosted API / self-hosted weights) | write a structured JSON caption | honest "route elsewhere" coverage, licence-split handling |
| `sdxl` | **two composable axes** (speed variant × checkpoint dialect) | weighted keyword phrases in ~77 CLIP tokens | LoRA training treatment, contested-licence handling without picking a side |
| `flux-2` | **licence split as the load-bearing axis** (Apache klein-4B vs NC dev/9B) | BFL's Subject → Action → Style → Context sentence | variant selector under a legal constraint |
| `krea-2` | **variant + hosted tier** (Raw / Turbo / hosted Medium-Large) | put the content in the prompt and the **style in the controls** | signature-look craft, contested training doctrine shown as contested |

Note what the one-rules do together. Three of them form a deliberate **encoder contrast** — *sentence* (LLM encoder) / *JSON caption* (JSON-trained) / *weighted tags* (CLIP). Krea's is the useful exception: it's a **control-surface** rule, not an encoder rule. So the lesson is not "derive the one rule from the encoder" but "derive it from whatever most dominates this model's output quality" — which is usually the encoder, and sometimes isn't. Never copy it.

## Choosing the spine

- Multiple **variants/checkpoints** (base, Turbo, distilled, fp8)? → organise like `z-image`, with a **variant selector** table.
- Multiple **surfaces** (web app, hosted API, self-hosted weights), especially with a licence split? → organise like `ideogram-4`, with a **surface selector** and a prominent licence callout.
- A model can have both axes — pick the one that most changes what the reader does, lead with it, fold the other in. `sdxl` runs two axes deliberately because both genuinely matter.

## The conditioning-class doctrine

Several "per-model" rules are not per-model at all — they fall out of the model's conditioning setup, so you can **predict** them and then confirm cheaply, rather than researching each from scratch. Two independent axes drive them. Keep them separate: conflating them is the most common way these skills go wrong.

### Axis 1 — text-encoder class

Determines how the prompt should be written and how training captions and trigger words behave.

| Doctrine | CLIP (SDXL-era) | LLM/T5 encoder (Flux, Z-Image, Qwen-class, Krea, Chroma) | JSON-caption-trained (Ideogram 4) |
|---|---|---|---|
| Prompt dialect | weighted comma keywords, ~77 tokens, front-loaded | natural sentences, front-loaded, no quality-tag chains | structured JSON caption |
| LoRA trigger word | **verbatim rare token**, literal | folded into a natural sentence, or omitted — bare tokens can confuse the encoder | n/a (no LoRA ecosystem yet) |
| Caption style (training) | tags; caption-the-residual | prose; caption-the-residual *in prose* — captionless is contested but works for pure replication | JSON |
| Text-encoder training | optional, contested | never (model-only LoRAs) | — |

### Axis 2 — guidance distillation

**Negative-prompt behaviour lives here, not in the encoder table.** Whether negatives work is determined by whether guidance was distilled into the model, which is *independent* of the encoder:

| Guidance state | Negatives | CFG |
|---|---|---|
| Undistilled | Work normally | Real CFG > 1 |
| Guidance-distilled (Flux dev/schnell-class, Turbo/Lightning/LCM variants) | Inert — phrase positively instead | CFG pinned at ~1; a guidance *embedding* replaces it |
| **De-distilled** (guidance deliberately restored) | **Work normally again** | Real CFG returns |

The third row is why the axes must stay separate. **Chroma** is an LLM/T5-encoder model de-distilled from Flux.1 Schnell precisely to restore real CFG and negative prompts. Reason from the encoder alone — "it shares Flux's encoder, so negatives must be inert" — and you will write the model's headline feature into the skill backwards.

**Qwen-Image** warns in the other direction: it exposes `true_cfg_scale` rather than plain `cfg` (flow-matching models need the former), and community testing reports negatives ignored across CFG 1.0–7.0 in practice `[community — re-verify and attribute before citing]`. So its cell is genuinely *contested*, not clean — show it as contested, and name whoever you end up citing.

### How to use these tables

Treat them as a **prediction to falsify, not an answer to copy.** They tell you what to expect and what evidence would settle it — they do not excuse you from the model card, and this is the one place in this spec where a plausible-looking table can override research it shouldn't. The confirmation is cheap and specific:

- **Encoder class** → the model card's text-encoder line, and the `type` argument on the CLIPLoader node in the official template JSON.
- **Guidance state** → whether the template's sampler runs CFG 1 with a separate guidance node (distilled), or real CFG with a populated negative prompt (not distilled). The template graph settles this in one look.

State the relevant cell *with its mechanism* ("this is the encoder, not folklore") so readers transfer correctly between models — and state the two axes separately for the same reason.

## Signature-quality technique

The place models most genuinely disagree, so it must be discovered rather than assumed. `z-image` stacks real camera gear to reach photoreal; `ideogram-4` does the **reverse**, killing "warm" and aiming at a neutral phone look; `krea-2` fights an airbrushed default hard enough that swapping the VAE is part of the craft. Find this model's default look and the lever that overrides it.

If the model's headline strength is something other than photoreal — typography, layout, anime — make **that** the signature section instead.

## Per-variant settings and image failure modes

**Per-variant settings** (anatomy item 12) — one block per variant or speed preset: steps, CFG/guidance, sampler, scheduler, resolution range, negatives, seed behaviour, LoRA weight. Take the base numbers from the official template JSON and the model card, then note where named community authors deviate and why. Distilled and non-distilled variants of the same model often need *opposite* settings, so never state one block and call it the model's.

**Failure modes** (anatomy item 4) — SKILL.md flags this table as one of the most-used sections. The recurring artefact classes for still-image models, to populate with this model's actual behaviour and mechanisms:

| Class | What to check for this model |
|---|---|
| Anatomy — hands, limbs, teeth, eyes | Which are actually weak here, at what resolution they degrade, and whether a detailer stage is the fix |
| Over-cooked / burnt output | CFG too high for the variant — especially applying non-distilled CFG to a distilled one |
| Plastic or airbrushed skin | The model's default aesthetic, and the specific lever that overrides it (see signature technique above) |
| Composition drift at off-native resolution | The trained resolution band, and what happens outside it |
| Seams and repeats at high resolution | Tiling or hires stages, and whether duplicate subjects appear |
| Text and typography breakdown | The character-count or complexity ceiling before glyphs corrupt |
| VAE artefacts | Colour shift or mush after decode, especially when swapping VAE across families |
| LoRA interference | Style bleed, blown-out output when stacking, silent no-ops on format mismatch |

Explain the *mechanism* in each cause cell — a reader who understands why CFG burns a distilled model can generalise; one told "use CFG 1" cannot.

## The three pillars — image mechanics

**Characters** (`references/characters.md`) — two paths, increasingly chained:
- *Edit-model character engine* — character sheet / multi-reference editing, no training.
- *Character LoRA pipeline* — edit-model-generated dataset → curate 20–50 varied images → train → evaluate.

The community increasingly chains them (the edit model builds the dataset for the LoRA). Include: the **8-point rotation + elevation dataset protocol** (model-agnostic craft — see z-image's prompting guide), the **identity-adapter status table for this model** (PuLID / InstantID / IP-Adapter / multi-ref — when an adapter beats a LoRA and vice versa), the **detailer-stage LoRA-swap** technique, multi-outfit and multi-character limits, and the failure modes: angle collapse, same-face overfit, expression lock-in, style bleed, multi-character bleed.

**LoRA training** (`references/lora-training.md`) — training only; using and stacking belong in the workflows file. Character and style datasets **invert the captioning residual**. Style needs subject diversity, and has its own overfit signals (composition memorisation, colour-cast lock-in) and its own acceptance test: *style recognisable on out-of-set subjects*. Give per-model hyperparameters as attributed starting points — the consensus is real but soft — and flag contested points (captionless DiT training, style rank) as contested. Flag the ethics of single-artist datasets.

**Production pipelines** (SKILL.md section + workflows reference) — the multi-stage ladder (`z-image`'s "Building multi-stage workflows" is the template: named stages, per-stage settings, optional-stage toggles), **and the model's role in mixed-model pipelines**. Cross-family handoffs are mainstream: compose with the deep-ecosystem model, refine with the quality model. The hard rule is *decode to pixels between VAE families; identity-preserving refine lives at denoise ~0.2–0.5*. Link `skills/generative-media/image-production-workflows/` rather than duplicating it.

**Cross-modality link.** A still-image skill should now also point at where its output goes: a locked character or style still is the input to image-to-video. Add a short pointer to the relevant video skill in the production-pipelines section — see `references/video-models.md` for the handoff.

## Pre-flight additions

On top of the shared checklist in `SKILL.md`:

1. Read `z-image` plus the shape-matching example in full, and skimmed the others' `references/`?
2. Spine chosen deliberately between variant / surface / both-axes?
3. One-rule discovered from this model's dominant quality lever, not copied — and checked against the encoder-class table *and* the possibility that it's a control-surface rule instead?
4. **Both** conditioning axes resolved separately — encoder class *and* guidance state — with negative-prompt behaviour derived from the latter, and each confirmed against the template JSON rather than assumed from the table?
5. Per-variant settings given per variant, with distilled and undistilled blocks kept apart?
6. Realism/signature section matched to this model's actual default and strength, not assumed photoreal?
7. Failure-modes table populated across the recurring artefact classes, with mechanisms rather than instructions?
8. Identity-adapter status table populated for *this* model, with "when an adapter beats a LoRA" stated?
9. Cross-modality pointer added to the video skill that would consume this model's stills?
