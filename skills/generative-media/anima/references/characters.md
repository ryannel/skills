# Consistent characters in Anima

This file owns holding an identity steady across images on Anima. **Training** the LoRA that sometimes results is covered in [`lora-training.md`](lora-training.md). The conditioning nodes and their wiring are in [`setup-and-workflows.md`](setup-and-workflows.md) §8. The prompt vocabulary is in [`prompting-guide.md`](prompting-guide.md).

**Anima's identity story is knowledge-first, not conditioning-first.** That is genuinely different from the rest of this suite. On [`flux-2`](../../flux-2/) or [`z-image`](../../z-image/) you get a character by supplying one — a reference image, an adapter, a trained LoRA. On Anima the first and often best answer is that **the model already knows the character by tag**. The second-best answer is that it can be taught cheaply. The image-conditioning route photoreal models lean on is the *weakest* of the three here.

## Contents

1. Route selection
2. Is the character already in the model?
3. When you need a LoRA
4. Image conditioning, and why it is the last resort here
5. Multi-character scenes
6. Adult work and the rating axis
7. Failure modes
8. Handing a locked character to video

---

## 1. Route selection

| Route | Cost | Consistency | Use when |
|---|---|---|---|
| **Tag the character** (character + series + appearance) | free | high for well-known characters | the character is in booru vocabulary and predates September 2025 |
| **Character LoRA** trained on Anima-Base | ~6 GB VRAM, hours | highest | an original or post-cutoff character, or one the model renders generically |
| **Cosmos-Reference + Anima Edit LoRA** (ReStyler) | free, ~85% hit rate | good for style/outfit/background, poor for pose | you have one image and want variations without training |
| **Anima-LLLite at low weight** | free | moderate | edits to an existing image — expression, clothing, relocation |
| **IP-Adapter** | free | poor | not yet — both implementations are incomplete |

The routes chain: tag or LoRA for the character, generate a clean neutral-pose still, then derive variations with ReStyler or LLLite.

---

## 2. Is the character already in the model?

Anima carries a very large character vocabulary, indexed as booru `character` + `series` tags. Two rules make it work:

- **Always pair character with series.** `u/RevolutionaryWater31`: *"Characters should (think 'must') be follow by their series/copyrights, (think of these like anchors…) follow by their appearances (the more the better)."* The series tag tells apart characters that share a name. Without it you get an average of everyone with that name.
- **Then describe the appearance anyway.** The model card is explicit that naming without describing causes confusion. It gets worse with more than one character in frame.

**Check before you assume.** The knowledge cut-off is **September 2025**, and it bites both ways: recent characters are missing, and so are older ones with thin booru coverage. `u/Hi7u7`: *"I tried to recreate the RE:Zero character, Capella Emerada Lugunica. Unfortunately, Anima 1.0 couldn't recreate it, so I had to use a Lora… But, I realized that there were some old anime characters that I didn't recognize either."*

The check is cheap. Use the community **"Animedex"** character index, or `tags.latent.moe`, which shows real per-model image references for a tag `[community — u/Hi7u7, u/Chemical-Nose-2985]`. If the character is absent, that is your signal to train one. (Closing this gap is also what the **Anima-2.9B** fork was built for — see SKILL.md's *Licence & limitations* on why the forks stay a footnote.)

---

## 3. When you need a LoRA

Train when the character is original, post-cutoff, or rendered generically despite a correct character+series tag. Anima makes this unusually affordable — ~6 GB VRAM at 768 px ([`lora-training.md`](lora-training.md)). Three deployment points are specific to characters:

- **Train on Anima-Base** — *"LoRAs should be trained using this version"* — then run the LoRA on whichever variant or community checkpoint you generate with. Reduce strength by ~0.1–0.3 on Aesthetic and Turbo, since those carry their own style `[community — convergent practice]`.
- **Deploy at the detailer stage, not the base gen.** This pattern transfers from [`z-image`](../../z-image/) and [`sdxl`](../../sdxl/). Generate the composition from a detailed tag prompt with **no** character LoRA, then swap the LoRA in at the FaceDetailer pass with a prompt matched to the image. At the base gen it fights your composition tags; used only at the detailer, you get the face without the LoRA's default framing. For maximum likeness, load it at both stages at reduced strength.
- **Keep the character and the art style in separate LoRAs.** This is the single most important structural choice on Anima. [`lora-training.md`](lora-training.md) §10 explains why: the one documented multi-day training failure in the community was a character-plus-webtoon-style LoRA `[contested]`.

---

## 4. Image conditioning, and why it is the last resort here

Anima inherits Cosmos-Predict2's reference-conditioning path rather than the ControlNet/IP-Adapter stack SDXL users expect. The honest summary is that **identity-by-reference is the immature part of this model.** Full wiring is in [`setup-and-workflows.md`](setup-and-workflows.md) §8; here is the character-relevant shape:

**Cosmos-Reference + Anima Edit LoRA** does character transfer — *"Transfer character from the input image into a new image with Anima"* — but `u/arthan1011` names the limit: *"it's too rigid. I can change outfit and replace background but changing a pose is almost impossible — feels like ControlNet Lineart."* His **ReStyler** workaround (stitch a blank canvas beside the character, mask only the blank area, prompt `(split screen, multiple views:1.2)`) is the best-documented method in the Anima space. It works *"85% of the time"* and wants a neutral-pose character on a simple background.

**Anima-LLLite's undocumented expression model** is the other live route: at **0.15–0.3 weight** rather than 1.0, `anima-lllite-exp-change-2` performs general edits while preserving identity `[community — u/_BreakingGood_, u/tpinho9; convergent]`. It is not shipped — both upstream PRs are open, unmerged drafts `[pending release]` — and the weight lives at `kohya-ss/Anima-LLLite`, not the Comfy-Org repackage. The released LLLite weights (`lineart`, `depth`, `pose`, `scribble`, inpainting) *are* native in ComfyUI core, via `ModelPatchLoader` → `AnimaLLLiteApply`.

**IP-Adapter** has two independent community implementations, and neither works yet. One ships no weights at all `[community — u/Internal_Answer_6866, u/Big_CokeBelly]`.

**Here is the honest routing**, from the author of the best workaround: *"If you want to change pose of your character and keep its style 100% consistent you'd better use Wan 2.2."* — [`wan-2-2`](../../wan-2-2/). For structural identity control in general, [`sdxl`](../../sdxl/)'s InstantID/IP-Adapter FaceID stack is far ahead. Composing there and then refining in Anima (`setup-and-workflows.md` §10) is a legitimate answer. The open research direction, named by `u/arthan1011`, is a Cosmos-Reference LoRA trained on synthetic image pairs for style transfer. Nobody has shipped it.

---

## 5. Multi-character scenes

**This is a named unsolved problem on Anima.** `u/Front_Praline9683` asked the community for *"good prompting tricks to generate more than 2 characters with specific outfits and pose consistently"* and got no answers. The card does not call it unsolved itself — it only gives the prompting note below — so the "unsolved" framing is the community's, not the vendor's.

The mechanism is straightforward. There is no regional conditioning for Anima, so every tag is a global signal, and the model must guess which attributes attach to which body. Two characters with distinct hair colours mostly works; two with distinct *outfits and poses* does not reliably.

What helps: **name each character and describe each one's appearance.** This is the only mitigation the card offers, and it frames this as mattering most in multi-character prompts. Also use **prose for the relationship and tags for everything else** (`prompting-guide.md` §8), since relational structure is the one thing the LLM half handles better than tags. And **accept a ceiling around two** — build beyond it with inpainting or per-character detailer passes, or compose in [`sdxl`](../../sdxl/) instead, whose `[SEP]` routing and regional prompting have no Anima equivalent.

---

## 6. Adult work and the rating axis

Anima treats adult content as a **graded, trained conditioning axis**: `safe`, `sensitive`, `nsfw`, `explicit` sit in the same prompt slot as quality and year tags, and you can use them positively or negatively `[official]`. There is no refusal layer, no separate uncensored build. Stating that plainly matters in both directions, including for the reader who wanted `safe` and did not know they had to ask for it.

- **`sensitive` is the useful middle rung.** A binary SFW/NSFW switch cannot express suggestive-but-not-explicit; this axis can.
- **The default drifts.** *"The model may generate undesired content, especially if the prompt is short or lacking details."* That is why the recommended prefix ships with `safe,` in it. On **Turbo**, where negatives are inert, the positive rating tag is your only control.
- **Adult-oriented work concentrates in the derivative checkpoints** — `MiaoMiao Harem`, `Hassaku (Anima)`, `One obsession_Anima`, the `uwumerge`/`uwustyle` furry line `[community — Civitai API]`. One caveat: unauthenticated Civitai calls appear SFW-filtered, returning `nsfw: 0` across all 100 Anima results, which is certainly wrong. It is not evidence of absence `[flagged — re-verify]`.

**Here is what the licence actually says**, since this is the question readers most often assume. §4(a) prohibits *"unlawful content, including child sexual abuse material, or non-consensual intimate images"* and states **no general adult-content prohibition beyond that**. But it does **not** leave real-person likeness to platforms alone: §4(a)(ii) also bars use that violates *"any third party's legal rights, **including rights of publicity or 'digital replica' rights**."* So a real-person likeness LoRA is constrained by this licence *and* by Civitai's real-person ban *and* by the TAKE IT DOWN Act. [`character-lora-training`](../../character-lora-training/) owns the practical gate. Read [`publishing-and-likeness.md`](../../character-lora-training/references/publishing-and-likeness.md) before training a likeness, not before uploading one.

Separately, and often confused with the above: **the images Anima generates are not restricted at all.** The card carves Outputs out of the non-commercial clause entirely, so anyone may sell them. See SKILL.md's *Licence & limitations*.

---

## 7. Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Named character renders as a generic anime figure | Not in the vocabulary (post-September-2025, or thin booru coverage) | Check the Animedex / `tags.latent.moe`; describe appearance explicitly; train a LoRA |
| Right character, wrong design | Series tag omitted, so the model averaged across same-named characters | Always pair `character` with `series` |
| Character drifts between images in a set | No identity conditioning is active — tags alone are only as consistent as the vocabulary | Fix the seed, or move to a LoRA, or derive variants from one still via ReStyler |
| Two characters' features swap or merge | No regional conditioning; all tags are global | Name *and* describe each; use prose for the relation; cap at two and inpaint the rest |
| Character LoRA gives a generic face at the detailer stage | Detailer prompt does not match the image, so the LoRA falls back to its default | Match the detailer prompt to the shot |
| Style bleed — every image now looks like the LoRA's dataset | Character and art style trained together | Split into two LoRAs; caption the style out of the character set |
| Edit LoRA changes the outfit but not the pose | Cosmos-Reference is structurally rigid — it behaves like a lineart control | Use the ReStyler split-screen canvas, or hand the pose change to [`wan-2-2`](../../wan-2-2/) |
| Expression edit works, nothing else does | `anima-lllite-exp-change-2` at full weight | Drop to 0.15–0.3 |

---

## 8. Handing a locked character to video

Anima's most common production role is **generating the character still that a video model then animates.** This is a repeated named pattern, not an occasional one — `u/irmemon225`, `u/Ok-Wolverine-5020` (twice), and `u/AzuliarTHP` all describe Anima → [`minimax-h3`](../../minimax-h3/) pipelines for anime music videos and reference-to-video work.

Two rules, both from practitioners. First, **match the aspect ratio and keep the still modest** — `u/WearNatural5992`: *"using an input at 16:9 and make the video at the same aspect ratio and the loss of quality, especially in face is considerably less… I am using the shortest side as 768px."* An oversized still loses face quality at the first frame, and that loss propagates through the clip. Second, **restore faces after, not before** — run FaceDetailer on the output.

For a pose change with the style held exactly — something Anima's editing stack cannot do — route through [`wan-2-2`](../../wan-2-2/) instead of fighting Cosmos-Reference. This file is the upstream half of consistent characters in video; the video skills own the downstream half.
