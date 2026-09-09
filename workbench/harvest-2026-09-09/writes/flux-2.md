# flux-2 — write report, 2026-09-09

## Edits (file · section · change · evidence)

- `SKILL.md` · `description` · added `Flux2KleinKVPipeline` to the diffusers class list (300 words, in band) · diffusers flux2 docs
- `SKILL.md` · § diffusers · v0.38.0/git-install caveat → `pip install "diffusers>=0.40"` (0.40.0 stable on PyPI 2026-08-20, verified 2026-09-09); `[flagged — re-verify]` promoted to `[official — diffusers 0.40.0 docs]` · https://pypi.org/project/diffusers/ ; https://huggingface.co/docs/diffusers/api/pipelines/flux2
- `SKILL.md` · § diffusers · new paragraph on `Flux2KleinKVPipeline`: first-step K/V caching of reference tokens, reused on later steps; when it pays off · same docs
- `SKILL.md` · § [klein] 9B KV settings · one sentence naming the diffusers equivalent · same
- `SKILL.md` · § two-bar · volatile list now says "0.40.0 verified on PyPI 2026-09-09; a later breaking release could re-cut the classes"; "Facts dated" → 2026-09-09
- `SKILL.md` · § Reference files · setup-and-workflows row names the three classes, 0.40.0+
- `references/setup-and-workflows.md` · §6 · install block replaced as above, with release date and marker · PyPI + docs
- `references/setup-and-workflows.md` · §6 KV stanza · class was already present as a bare code block; added mechanism, batch-vs-single guidance, and "check the docstring for the reference-image argument name" (no invented kwargs) · docs
- `references/lora-training.md` · § The official reference config · vague "documented collapse patterns" → cited ostris/ai-toolkit#654 (opened 2026-01-19, collapse by ~step 250, degenerate by 500, no maintainer response as of 2026-09-09); added "sample early on 9B — a 500-step checkpoint interval misses the reported onset"; `[community — ostris/ai-toolkit#654; single report, re-verify]` · https://github.com/ostris/ai-toolkit/issues/654
- `references/api-and-hosted.md` · §8 · "Illustrative numbers (aggregator-sourced, 2026-09-09)": klein ~$0.014/image, pro $0.03/MP ($0.045/MP edits), flex $0.05–0.06/MP, max $0.07/MP; per-MP unit flagged; bfl.ai/pricing instruction kept; `[community — dynalord, flowith aggregators; re-verify]` · https://dynalord.com/blog/flux-2-pricing ; https://flowith.io/blog/flux-2-pro-pricing-2026-dev-vs-pro-vs-schnell-api/
- `references/characters.md` · §1 · PuLID "t2i only as of v0.6.x" → v0.6.2, checked 2026-09-09, edit mode still on roadmap · freshness JSON amend (pulid-flux2)
- `references/characters.md` · §5 failure modes · new row: edit chain warps untouched regions; mechanism (each pass re-encodes the previous output); fix (keep the original reference in every pass) plus the Klein 9B edit-mode Consistency LoRA `[community — Civitai article 27410; single report]` · https://civitai.com/articles/27410/flux2-klein-9b-consistency-lora (2026-03-18)
- `references/controlnet-and-identity.md` · §3 · "as of June 2026" → as of 2026-09-09 (v0.6.2), still the only FLUX.2 PuLID, still t2i only · watchlist amend

Readability unchanged: median tangle 5.2, 0 files over 15. SKILL.md 5,150 words.

## Findings

Resolved: `diffusers-flux2-stable-release`, `diffusers-flux2-klein-kv-pipeline-missing`, `klein-9b-collapse-now-has-named-issue`, `bfl-pricing-numbers-now-circulating`.

Declined: none. Correction to the JSON: `diffusers-flux2-klein-kv-pipeline-missing` claims the references name only two classes, but `setup-and-workflows.md §6` already had a bare `Flux2KleinKVPipeline` block. SKILL.md was the real gap.

## Techniques

Added: `diffusers-flux2-klein-kv-pipeline-technique` (official). `flux2-klein-consistency-lora-iterative-edit` (single report, marked; fills a real gap — nothing addressed compounding drift across edit chains).

Omitted: `flux2-int8-quant-node` — one undated extension listing with an uncorroborated speed claim; the skill already documents three quant paths.

## Watchlist

- `diffusers-status` — resolved. Re-open only on a breaking diffusers release that renames the Flux2 classes.
- `pulid-flux2` — amend per JSON (v0.6.2, t2i only); text now cites v0.6.2 in two files.
- `klein-9b-collapse` — amend per JSON; now anchored to ai-toolkit#654; check for maintainer response or a second report.
- `bfl-pricing` — amend: §8 carries aggregator numbers dated 2026-09-09; spot-check against bfl.ai/pricing, and the per-MP vs per-image unit.
- Add (low priority): `klein-consistency-lora` — single Civitai report in characters.md §5; promote or drop on a second source.

## Other skills

None. The atlas does not restate the diffusers install line or pricing numbers.
