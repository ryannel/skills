# Orchestrator steer for the krea-2 and character-lora-training writers (from the user, 2026-09-09)

The user's direction: **lean on what Ciara taught, not Amy.** Amy's process contained false reads, and the high-res rabbit hole was one of them.

## Primary evidence for the resolution rule = Ciara (transcripts-ciara-h3.md §1–2, Numbers table)
- Four-cell sweep, 2026-09-08, LoRA strength 0: 1024×1280 native clean; 2048 moderately crumpled; 2560 heavily.
- Downscaling 2048→1024 or 2560→1024 still loses to 1024 native. The crumple survives the downscale.
- Wan 2.1 VAE vs Qwen VAE: identical at 2048. It was never the VAE.
- Root cause: Krea 2 Turbo's band is 1K–2K, Raw is 1K-native; the dataset had been rendered at 2048–2816, above the band.
- Confirmed after training: krea2-v4 (r16) and krea2-v5 (r32) on the 1024-native dataset are both clean at every rung. The dataset was the fix, not rank.
- Independent lever: sampling steps. 20 steps produces a hex/pore mesh; 12 and 8 are clean on a distilled base.
- New: textured/patterned wall wording prints its pattern onto skin at 1024 native, every seed. Plain painted walls are clean.

## Amy's false reads — write them as the wrong turn, named
- The 2048/20-step "uncanny grain" was read as freckle stipple and nearly declared a hard limit; the grain was on the wall too.
- The VAE swap, texture-anchor words, and a detail-heavy finetune were stacked as "sharpeners" on top of over-band renders. None of them was the cause.
- The freckle-map diagnosis in Ciara's V4-PLAN was inherited from Amy and superseded before its pilot ran.
- Rule to state: before diagnosing a subtle skin artefact, verify you are inside the base model's trained resolution band and step band.

## Three resolutions must be kept apart in the text
dataset source render (1024-native for Krea 2) · training bucket (1024) · deploy render (Turbo 1K–2K; the fineporn finetune unusable at 1024×1536, good at ≥1344×2016).

## Synthetics share — inputs disagree, present as contested
media-lab-docs.md: <10% literature cap, 12–14% uneventful, 64% a measured failure (krea2-v15: body learned, face regressed). transcripts-amy-krea.md: v18 ran at ≤40% with the stated direction "almost entirely synthetic". Report both; the only measured data points are 12–14% fine and 64% failed.
