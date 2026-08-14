# Krea 2 — Prompting guide

Everything here follows from two facts: the encoder is **Qwen3-VL 4B Instruct** (an instruction-following VLM that parses clause structure — tapped at twelve decoder layers, so both coarse gist and fine wording reach the DiT), and Krea's design thesis that **style is a control surface, not a prompt word**. Sources: the official `docs/prompting.md` and template JSON [official], the tech report [official], and named community authors [attributed inline]. Verified 2026-07-07.

## Contents
1. [The two registers that work](#1-the-two-registers-that-work)
2. [Prompt anatomy](#2-prompt-anatomy)
3. [Realism & texture vocabulary](#3-realism--texture-vocabulary)
4. [Text rendering](#4-text-rendering)
5. [Style: LoRAs, references, moodboards, creativity](#5-style-loras-references-moodboards-creativity)
6. [The prompt expander](#6-the-prompt-expander)
7. [Common mistakes](#7-common-mistakes)

---

## 1. The two registers that work

The official example set [official — docs/prompting.md, all generated at 2K with Turbo] runs two registers, and both produce excellent results:

**Register A — flowing prose.** Full sentences with spatial relationships spelled out:

> *A tiny, russet-brown harvest mouse clings to a slender diagonal branch amid vibrant green lobed leaves and small round buds. The mouse has soft textured fur, glossy black eyes, a pink nose, fine whiskers, and delicate pink paws firmly gripping the wood. In this macro photograph, an extremely shallow depth of field sharply focuses on the animal's face…*

**Register B — dense comma-separated descriptors.** Not booru tags — every fragment is a *descriptive phrase*:

> *high-fashion editorial portrait of a young East Asian woman, short choppy platinum blonde bob with heavy bangs, looking over her bare shoulder to the right, lips playfully pursed, wearing a structured black top with an architectural protruding bust detail…, solid striking crimson red background, soft directional studio lighting, cinematic color palette, medium close-up shot*

A VLM parses either. What it does **not** reward is incantations: `masterpiece, 8k, best quality, ultra-detailed` are near-zero-signal to an instruction-tuned encoder. The test for every fragment: *could a human art director act on it?* "blocky painterly brushstrokes" passes; "masterpiece" doesn't.

Also official: minimal prompts work (`immense rocket launch exhaust as seen from extremely close up` is an official example), but "long detailed prompts yield best results." Length ceiling: **512 tokens** (`max_sequence_length`, padded/truncated) [official — diffusers docs]; front-load the subject.

## 2. Prompt anatomy

A reliable assembly order (synthesised from the official examples' consistent internal structure):

1. **Medium + shot** — "macro photograph", "stylized digital painting", "1990s vintage anime style cel animation", "high-fashion editorial portrait, medium close-up". Naming the medium *first* matters more here than on most models because of the render-bias (see §3).
2. **Subject** — concrete, specific, with material detail ("soft textured fur, glossy black eyes, fine whiskers").
3. **Action / pose / gaze** — "looking over her bare shoulder to the right, lips playfully pursed".
4. **Environment & spatial layout** — official examples are unusually explicit about placement: "A dark, jagged rock rests in the lower left foreground near a pale grey shoreline."
5. **Lighting** — source + direction + quality: "soft, diffused natural lighting", "harsh, direct lighting… casting sharp, hard shadows", "cinematic shafts of light pierce the dusty gloom".
6. **Palette & finish** — "muted earthy color palette, sepia-toned warmth", "vibrant warm color palette, sharp graphic shadows".
7. **Optics (photo work)** — "macro lens, shallow depth of field, distinct film grain texture".

One medium, one mood, one lighting scheme per prompt — the encoder resolves contradictions as uncanny blends, not averages (same failure as every LLM-encoder model).

**Negatives:** on Turbo there is no negative channel (guidance off; the template zeroes the negative branch). Phrase constraints positively: not "no clutter" but "clean, minimal background". On Raw at cfg ~3.5 (or Turbo at the community cfg-2.0 workaround), a short negative string works normally.

## 3. Realism & texture vocabulary

Krea 2's aesthetic prior leans soft, and it has a mild **3D-render/digital-art bias** — an underspecified portrait prompt will happily come back as a render [community — nsfwVariant, Civitai]. For photographs:

- **Declare the photograph early and concretely.** Medium first ("editorial photograph", "35mm street photograph"), then stack the usual LLM-encoder camera anchors: real body ("Canon EOS R5", "Hasselblad X2D"), lens + aperture ("85mm f/1.4"), film stock or grain ("Kodak Portra 400", "distinct film grain texture" — the last is verbatim from an official example).
- **Anchor texture explicitly** — the working anti-airbrush string is "natural skin texture, visible pores, subtle skin imperfections" [community — amida168, kombitz.com]. Official examples do the same for non-skin surfaces ("grainy paper texture", "tactile quality", "smooth vinyl texture") — the model responds well to named textures generally.
- **Know what prompting can't fix.** Residual softness after all of the above is the VAE's rendering character — the fix is the Wan 2.1 VAE swap or a detailer pass, not more words (`setup-and-workflows.md §5`). Muted facial expressions are the safety-tuning tax — bypass LoRA / Rebalance nodes / a Z-Image face pass, not adjectives (`SKILL.md`, *two taxes*).

Prompt-only expression coaxing that helps at the margin: name the *physical* expression, not the emotion — "eyes crinkled, mouth open mid-laugh, head thrown slightly back" beats "laughing joyfully" — but expect the ceiling to be lower than on Z-Image [community — liutyi: "only neutral and smile remain" without tooling].

## 4. Text rendering

Official guidance: **wrap the words to render in quotes** — `a neon sign reading "OPEN LATE"` [official — docs/prompting.md]. Reality check: text rendering is a genuine weakness — "some text appears but not reliably" [community — liutyi]. Keep it short (a few words), straight double quotes, generate several candidates and select. For typography-led work (posters, logos, dense lettering), route to the `ideogram-4` skill — that's what it's for.

## 5. Style: LoRAs, references, moodboards, creativity

**Local: the official style-LoRA line.** Nine style LoRAs ship in `Comfy-Org/Krea-2/loras` (0.47 GB each, `LoraLoaderModelOnly`). The trigger is a **natural descriptive phrase appended to the prompt** — exactly what an LLM encoder wants (a describable concept, not a rare token). The official template auto-appends it via a `CustomCombo` + `StringConcatenate`. Verbatim from the template's trigger table [official]:

| LoRA file | Trigger phrase | Strength |
|---|---|---|
| `krea2_darkbrush` | `monochrome ink wash style` | 1.0 |
| `krea2_dotmatrix` | `monochrome stippling style` | 1.0 |
| `krea2_kidsdrawing` | `naive expressive sketch style` | 1.0 |
| `krea2_neondrip` | `textured abstract style` | 1.0 |
| `krea2_rainywindow` | `rainy window style` | 1.0 |
| `krea2_retroanime` | `purple retro anime style` | 1.0 |
| `krea2_softwatercolor` | `art deco watercolor style` | 1.0 |
| `krea2_sunsetblur` | `ethereal motion blur style` | 1.0 |
| `krea2_vintagetarot` | `vintage tarot style` | 1.0 |

(The docs.comfy.org tutorial lists a few additional LoRAs at 0.8 — `krea2_coolblue`, `krea2_plasmoid`, `krea2_warmpastel`; the loader default in the template is 0.8. Treat 0.8–1.0 as the working band and the per-LoRA table value as the starting point.) More styles in Krea's HF collection (`krea/krea-2-loras`). Trained-LoRA triggers follow the same doctrine: fold a describable phrase into the caption/prompt; don't invent `ohwx`-style rare tokens (encoder-class rule — see the SKILL.md one-rule section).

**Hosted: style references and moodboards.** The web app takes up to **4 style reference images, each with its own strength slider**; the API takes up to 10 (`image_style_references`, with per-ref strength) plus one moodboard [official — user guide / API docs]. The tech report claims "smooth semantic mixing of multiple styles" with continuous strength — this is the flagship feature and the practical replacement for style words. Moodboards are "the most precise way to set a visual direction" [official — user guide].

**Creativity dial (hosted only):** `raw` renders "only explicit descriptions without expansion" — the literal mode, use it when your prompt is complete; `high` takes "meaningful creative liberty" — use it for exploration from thin prompts [official — user guide]. Default is `medium`. No local equivalent exists; locally the analogue is enhancer-off (literal) vs enhancer-on (liberal).

## 6. The prompt expander

Krea trained a dedicated expander LLM (SFT + RL with image-level and prompt-level rewards, plus a diversity reward) [official — tech report]. It surfaces as: the ComfyUI template's `TextGenerate` subgraph (**on by default**), fal's `enable_prompt_expansion`, and the hosted creativity dial. The template's system prompt is readable in the template JSON and is genuinely well-designed (faithfulness-first, groups subjects with their attributes, wraps requested text in quotes, respects a stated medium) — and Krea publishes a copy as `docs/expansion.txt` for use with any LLM [official].

Use it when your prompt is one line and you want the model's idea of a good expansion. Turn it off when: you wrote a full prompt already (rule 7 of its own system prompt says it should only lightly polish, but you lose determinism); you're iterating on exact wording; or it *refuses your benign prompt* — the shipped enhancer moralises (documented: "photo of a dog on a kitchen table" → ethics refusal) [community — 808charlie, Comfy-Org/ComfyUI#14631]. Community workflows replace it with an abliterated Qwen3-VL GGUF [community — lonecatone23] or with OpenAI/Gemini API nodes (the template explicitly supports the swap).

## 7. Common mistakes

| Mistake | Why it fails | Instead |
|---|---|---|
| `masterpiece, 8k, best quality` chains | Instruction-tuned VLM reads them as noise | Descriptive phrases only |
| "in the style of <artist>" as the whole style plan | The model is deliberately unopinionated; vague style words are weak levers | Style LoRA / style refs / moodboard; or describe the style's *properties* ("blocky painterly brushstrokes, golden-hour palette") |
| Rare-token LoRA triggers (`ohwx person`) | LLM encoders parse meaning; bare tokens confuse rather than key | Natural trigger phrases (see §5) |
| Negative prompt on stock Turbo | cfg 1.0 + `ConditioningZeroOut` = negatives never reach the model | Positive phrasing; or cfg 2.0 workaround at 2× cost |
| "photo" buried at the end of a style-heavy prompt | Render-bias wins the ambiguity | Medium first, camera stack early |
| Long text passage to render | Weak text rendering | ≤ a few words, straight quotes, candidates + select, or `ideogram-4` |
| Same prompt, different numbers across surfaces | Two guidance conventions (0-off vs 1-off) | Convert deliberately (SKILL.md, variant selector footnote) |
