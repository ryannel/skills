# krea-2 skill — intent & design decisions

Authored 2026-07-07. Research staged in `official-report.md` (2026-07-06) and `community-report.md` (2026-07-07).

## Intent

Publishable skill for **Krea 2** (Krea's 12B from-scratch foundation image model, open weights 2026-06-22) in the house style of z-image / flux-2 / sdxl / ideogram-4.

## Design decisions

- **Shape: variant selector**, flux-2 is the shape match. Load-bearing axis is the **role split**: Raw (train on it), Turbo (run it locally), Medium/Large (hosted — and architecturally different: FLUX.2 VAE on Large vs Qwen-Image VAE on open weights). Licence + open-vs-hosted folds into the same table.
- **One rule**: Krea's own thesis — "style should not be a vague prompt word" — content lives in the prompt (Qwen3-VL LLM encoder → detailed natural sentences), style lives in style references / style LoRAs / moodboards / creativity dial. Community corollary: bypass or replace the stock ComfyUI prompt-enhancer (issue #14631).
- **Encoder-class doctrine**: LLM-encoder column (sentences, no bare trigger tokens, negatives inert at cfg ≤ 1 on Turbo via guidance distillation; cfg 2.0 workaround = community craft, mirrors z-image Turbo-negatives note).
- **Signature section**: the anti-AI-look thesis and its two community-confirmed quality taxes (safety tuning → muted expressions; soft Qwen VAE → airbrushed look) with named fixes (Wan 2.1 VAE swap, Rebalance nodes, texture words).
- **Pillars**: characters = LoRA path (JahJedi recipe) + honest "no identity adapters yet" routing; LoRA training = contested Raw-first vs ostris Turbo-adapter doctrine shown as contested; production = two-stage Turbo ladder + Z-Image partnership, link `image-production-workflows` rather than duplicate.
- **References**: `prompting-guide.md`, `setup-and-workflows.md`, `lora-training.md`, `characters.md`, `api-and-hosted.md`.
- **Cross-links (bidirectional)**: z-image (primary pairing partner), flux-2 (VAE relationship, positioning), sdxl, ideogram-4; plus mixed-model-recipes.md in image-production-workflows.
- **Freshness**: register at tier **hot** (weights < 1 month old). Watchlist seeds: official edit models "coming", LoRA doctrine contested, ComfyUI enhancer issue #14631, GGUF repo churn, hosted pricing / 1K-only limit, licence terms, template details, 12B vs 12.9B param count.
