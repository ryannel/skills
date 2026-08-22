# Krea 2 — Consistent characters

Creating a persistent, reusable character with Krea 2, honestly: the character-LoRA pipeline is the only production path today; the adapter shortcut that exists on FLUX.2 does not exist here. Ecosystem verified 2026-07-07 (~2 weeks after open weights).

## Contents
1. [The state of identity tooling](#1-the-state-of-identity-tooling)
2. [The character-LoRA pipeline](#2-the-character-lora-pipeline)
3. [The nearest no-training tools (young)](#3-the-nearest-no-training-tools-young)
4. [Deployment: the detailer-stage swap](#4-deployment-the-detailer-stage-swap)
5. [Multi-outfit, multi-character](#5-multi-outfit-multi-character)
6. [Failure modes](#6-failure-modes)
7. [When to use another model](#7-when-to-use-another-model)

---

## 1. The state of identity tooling

| Tool class | Krea 2 status |
|---|---|
| PuLID | **does not exist** |
| InstantID / IP-Adapter (face) | **does not exist** |
| Native multi-reference generation | not in the open models; hosted style refs condition *style*, not identity |
| Official edit model | **announced, unreleased** — "robust editing, image reference" named as future work; "coming" `[official — tech report; Krea CTO on HN]` `[pending release]` |
| Character LoRA | **works — the production path** (multiple named recipes; `lora-training.md §6`) |
| Community identity-edit LoRA | **now the standard tool, not an experiment** — `conradlocke/krea2-identity-edit`, at **v1.2** as of August 2026: instruction-based, identity-preserving editing; requires its own `ComfyUI-Krea2Edit` node pack (dual conditioning: in-context VAE tokens + image-grounded Qwen3-VL encoding — stock nodes can't drive it); ships workflows. See §3 for the craft `[community — NatalieCrypto, MelodicFuntasy; convergent]` |
| Community edit/reference nodes | Ostris edit stack + Conditioning-Rebalance (§3) |
| Pure-prompt consistency | the "description-locked character sheet" technique (§3a) — no training, no adapter |

Plan on the LoRA for production **when likeness must survive close-ups**. That advice has weakened since it was written: **Identity Edit reached v1.2 and became the community's default identity tool**, used well outside Krea 2 work — it is now the standard way to prepare a first frame for video character-swap models (see §7), and the standard undressing tool in the adult community. Treat the adapter layer as *working*, and the LoRA as the higher-fidelity option rather than the only one.

## 2. The character-LoRA pipeline

The chain is the suite-standard one ([`z-image`](../../z-image/)'s `characters.md` documents the full craft; this section is the Krea-2 deltas):

1. **Anchor image** — generate the character once, at your best quality. Krea 2 note: fight the two taxes *before* anchoring (Wan-VAE decode, texture anchors, expression coaxing — `SKILL.md`) so you don't lock a waxy default into the character.
2. **Dataset factory** — Krea 2 has **no edit model yet**, so the edit-model dataset factory (the z-image/Qwen-Image-Edit trick: one anchor → prompted rotations/expressions/lighting) must borrow a *different* family's edit model, or use Ostris's Krea-2 edit-LoRA stack (§3) once you've validated it on your subject. Cross-family is fine for datasets — the LoRA learns from pixels, not latents; just keep the identity consistent across the set.
3. **Coverage protocol** (model-agnostic craft): 20–50 curated images; the **8-point rotation** (front, 3/4 L/R, profile L/R, back-3/4 L/R, back) plus elevation variety (eye-level, above, below); expression spread wide enough to outrun the muted-expression prior — over-represent non-neutral expressions relative to what you'd collect for other models, since the base model under-produces them; vary outfit/background/lighting in everything you *don't* want bound to the trigger.
4. **Captioning** — prose, caption-the-residual: describe clothing, pose, background, lighting per image; never re-describe the identity itself (`lora-training.md §5`).
5. **Train on Raw** (rank/alpha 32, LR 1e-4 starting point), **validate on Turbo** at 8-step guidance-off — the checkpoint you'll actually run (`lora-training.md §2, §8`).
6. **Deploy at the detailer stage** (§4).

Dataset size: the earliest recipe used 474 images + 348 regularisation images `[community — JahJedi]`, but the now-better-replicated result is that **protocol-size datasets work**: ~50 images, 2–3k steps, trained at 1024 only, with likeness the author rates *above* their Z-Image results from the same datasets — settings: AI-Toolkit, **LoKr factor 4, Automagic3 optimizer, sigmoid scheduling, LR 1e-4** `[community — Any_Tea_3499, r/StableDiffusion]`. Same author's noted weakness: tattoos (Ideogram > Krea 2 > Z-Image at learning them). Start at protocol size; scale up only if identity wobbles across seeds.

Multi-character LoRAs: possible but caption-sensitive — a documented failure has two characters holding up under training-style captions and *bleeding into each other* under creative free-form prompts `[community — krigeta1, r/StableDiffusion]`. Keep each character's identity block verbatim-stable in your prompts (see §3a — description discipline is the same lever) and keep per-character detailer passes as the fallback (§5).

**There is a training-side answer, and if it replicates it is the most consequential Krea-2 training finding of the last month: Differential Output Preservation.** Train each character LoRA with DOP enabled against a **class** (`"woman"`), on top of a LoKr config, at **1500 steps** rather than 750 — previews stabilise around 1500. Multiple character LoRAs then load together with minimal bleed; the author reports accidentally leaving a character LoRA active and seeing almost no contamination. Read the confidence honestly: this is **one author's runs**, on top of LilBrownBebeShoes's LoKr config, which is itself unreplicated — nobody has published a second set.

What it does not do, stated by the same author — so these limits carry exactly the same single-source confidence as the result:

- **Hard cap of 4 characters.** A five-character generation fell apart; four works reliably.
- Characters **borrow features from each other** — lips especially — so similar-looking characters drift toward looking related. The greater the visual difference between characters, the better it holds.
- **Prompt the distinguishing features.** If one character has a long nose, say so; naming what separates them is what keeps them separated.
- The author's datasets were captioned lazily (trigger word only), and better captioning is expected to strengthen likeness — the well-captioned dataset in their set produced the more resilient LoRA.

**The cross-model detail that matters for this suite:** the same technique **failed on Z-Image Base** — DOP there essentially prevented the character from being learned at all — and **worked on Krea 2**. If it holds, that is a real, testable difference between two models this suite otherwise treats as near-interchangeable for character work, and a reason to pick Krea 2 when the job is several characters in one frame. [`z-image`](../../z-image/) records the failure half from the same source and hedges it the same way, so treat the pair as one report, not two — A/B it on your own characters before you plan a shoot around it `[community — MASilverHammer; single report]`.

## 3. The nearest no-training tools (young)

- **Identity-edit LoRA** — `conradlocke/krea2-identity-edit` (unofficial fine-tune of Raw), **v1.2**: give it an image plus a plain-language instruction; it edits while preserving what you didn't ask to change, *including the person*. Requires the `ComfyUI-Krea2Edit` node pack (the LoRA's dual conditioning — in-context VAE tokens + image-grounded Qwen3-VL encoding — needs nodes stock ComfyUI doesn't have); ready-made workflows ship with it. The most direct identity tool that exists, and the obvious dataset-factory engine (§2.2).

  **Craft that emerged from a month of use** `[community — NatalieCrypto, MelodicFuntasy, r/unstable_diffusion]`:

  - **One short sentence beats a paragraph.** This is the single most-repeated finding, and it inverts normal Krea 2 prompting doctrine. *"Turn her to profile."* *"Change her outfit to a singlet and a short skirt."* Paragraphs degrade the edit.
  - Background and lighting genuinely **do not move** — edits that would need masking and inpainting on other stacks are one sentence here. No masks, no inpainting.
  - Demonstrated: profile turns, object swaps, taking outfit from one reference and pose from another, expression-only changes.
  - **Posing is the weak axis**, and a pose change will shift the face somewhat. If the pose is the point, this is the wrong tool.
  - **It stacks with other LoRAs.** Combining Identity Edit with an NSFW LoRA is the community's standard undressing pipeline — the edit LoRA holds identity, the other LoRA supplies the content the base model is thin on.
  - Its **fastest-growing use is outside image work entirely**: prepping a first frame for a video character-swap model, so the reference already matches the driving clip's pose and framing. See §7.
- **Ostris edit stack** — `ostris/ComfyUI-Krea2-Ostris-Edit`: up to **3 reference images** fed through the Qwen3-VL encoder + a model patch, driving paired-data **edit LoRAs** (a concept-edit LoRA trains in ~1,750 steps) `[community — Ostris; comfyui-wiki write-up]`. Third parties are already training on the method (e.g. sktksm's detail-enhancer edit LoRA, trigger "enhance this image" — its author's own caveats: experimental, weaker on horizontal aspect ratios, can shift lighting/colors `[community — sktksm]`). Not an identity guarantee — an edit conditioner, not a face embedder.
- **Conditioning-Rebalance** — `nova452/ComfyUI-Conditioning-Rebalance`: "IP-Adapter-like" per-layer conditioning manipulation exploiting the 12-layer text tap; image-reference editing plus the safety-tuning bypass; late-June update added negative prompting for edits `[community — nova452]`. Powerful and experimental in equal measure.

All are single-maintainer projects days-to-weeks old — pin versions, expect churn.

### 3a. Pure-prompt: the description-locked character sheet

Krea 2's prompt adherence is strong enough that an **exhaustively specific character description, repeated verbatim across scene prompts, holds a near-identical character with no training at all** — one author generates unlimited "panels" this way (character-sheet prompt per character: age, height, build, skin, hair, eyes, wardrobe down to belt buckle and earrings; then every scene prompt re-states the full block, with a local VLM splitting a master prompt into per-scene prompts) `[community — aurelm, r/comfyui "Infinite panels" workflow]`. Mechanism: the 12-layer Qwen3-VL tap rewards precise, repeated description — identity lives in the text. Costs: prompts run very long (watch the 512-token ceiling per scene), and likeness is "near-identical", not pixel-locked — good for storyboards, keyframes, and dataset bootstrapping; use a LoRA when likeness must survive close-ups.

## 4. Deployment: the detailer-stage swap

Suite-standard, applies verbatim: generate the base image from a detailed prompt with **no** character LoRA (composition stays free), then apply the LoRA in the FaceDetailer-class pass where the face is re-rendered — at ~0.8 strength for the published recipe. Match the detailer's prompt to the actual image or you get the LoRA's default face. On Krea 2 specifically, run the detailer on the two-stage recipe's output or post-Wan-VAE decode (`setup-and-workflows.md §7`) so the detailer isn't fighting the soft default; SAM3 face/eye detailers are the community's current pick `[community — lonecatone23]`.

## 5. Multi-outfit, multi-character

No Krea-2-specific evidence yet — the suite's shared limits are the planning assumption: multi-outfit LoRAs cap out around ~6 outfits before bleed; multi-character scenes have **no regional tooling** here (no regional prompter, no attention masking like FLUX.2's), so the working method is per-face detailer passes — one pass per character, each with its own LoRA, each prompted to its own face. Character style-bleed rules follow the LoRA-stacking norms (identity ~0.8, drop style LoRAs to 0.3–0.6 when stacking) — the JahJedi recipe's "holds at 0.8 under heavy style mixing" is the one measured point.

## 6. Failure modes

| Failure | Mechanism | Fix |
|---|---|---|
| Expression lock-in (character always neutral) | Base model's muted-expression tax compounding a neutral-heavy dataset | Over-represent expressions in the dataset; verify base can produce the expression first (`SKILL.md` taxes); bypass/Rebalance at inference |
| Angle collapse (only frontal views resolve) | Dataset missing rotation coverage | 8-point protocol; regenerate the missing angles via an edit model |
| Same-face overfit (every generated person is the character) | Over-trained / captions didn't isolate identity | Fewer steps or lower weight; caption-the-residual properly; regularisation images (JahJedi used 348) |
| Waxy/soft character at deploy time | The VAE/softness tax, not the LoRA | Wan-VAE decode + detailer pass before blaming training |
| Style bleed from stacked style LoRAs | Weight budget exceeded | Identity 0.8, styles lower; re-test each style added |
| Identity great on Raw, unstable on Turbo | Validated on the wrong checkpoint | Always evaluate at Turbo 8-step guidance-off (musubi `--turbo_dit`) |

## 7. When to use another model

- **No-training identity today:** [`flux-2`](../../flux-2/) — native multi-reference (ReferenceLatent) + PuLID is the suite's strongest adapter path.
- **Expressive close-up faces:** [`z-image`](../../z-image/) — better *base-model* facial expressiveness and hair; also the natural *finisher* for a Krea-2 scene (generate the scene here, run the face pass there — `setup-and-workflows.md §8`). Note the distinction that emerged in July 2026 testing: Z-Image still wins on un-trained expressiveness, but *trained character likeness* on Krea 2 is now reported at or above Z-Image's (`lora-training.md` §5 carries the run).
- **Mature multi-character tooling:** [`sdxl`](../../sdxl/) — regional prompting and the deepest adapter toolbox, and still the safe choice. §2's Differential Output Preservation result would close much of that gap on Krea 2 (up to **4** character LoRAs with minimal bleed, where Z-Image fails outright), but it is a single unreplicated report (§2) — treat it as the promising option to test, not the settled one to plan around.
- **Editing a character into a new scene, pose or state:** now genuinely contested. [`minimax-h3`](../../minimax-h3/) run at **one frame** is reported to beat Krea 2 + Identity Edit on character fidelity, 3D scenes, mirrors and composition — see that skill's edit-mode coverage. Krea 2 + Identity Edit remains far cheaper to set up and is the better default for scene-preserving one-sentence edits.

Krea 2 earns the character job when the character lives inside its aesthetic strengths — wide-aspect scenes, stylised looks driven by style LoRAs/refs, anatomy-heavy compositions — and you're willing to run the LoRA pipeline.

### Krea 2 as the front half of a video pipeline

Worth stating separately, because it is now the single most common thing people do with Identity Edit and it is not an image job at all. **Video character-replacement models want a reference that already matches the driving clip's pose and framing.** So the pipeline is: take the actual first frame of the driving video → edit it into your character with Identity Edit (or Flux Klein 9B) → hand *that* to the video model as the reference. Doing this rather than supplying a generic portrait is reported as the difference between mediocre and excellent character swaps `[community — blackmixture]`. Applies to [`scail-2`](../../scail-2/) — which documents this handoff from the video side — and to [`minimax-h3`](../../minimax-h3/)'s Ref2VA video-edit mode alike.
