# minimax-h3 — authoring intent and sources

**Authored 2026-08-13**, eleven days after the model's release. Staged retroactively — the research below was gathered directly rather than into this folder first, which is a process deviation worth not repeating.

## Why this skill exists

MiniMax H3 was the model with all the traction: HF trending flooded with derivatives, Civitai running it as a day-0 launch partner banner, ComfyUI shipping support in v0.30.0, **10.37M downloads on the `Comfy-Org` repackage within days** against 1.61M on the official repo.

## The decision that shaped it: licence-first

Two facts that almost no launch coverage mentioned, both verified from primary sources:

1. **The licence excludes the US, EU, UK and South Korea.** Not "no commercial use" — *no use*. The grant is limited to the Applicable Territory (worldwide **minus** those four), and Exhibit A lists "Use outside the Applicable Territory" as prohibited use #1.
2. **Only one of three system modules is open.** `H3-Context-IR` (which the model card calls critical to output quality) and `H3-Regenerate-2K` are hosted-only; sparse attention is withheld. Local output ceiling is 768p, and official demos run through a module you don't have.

The user chose "build it, licence-first" over skipping it or covering LTX-2.5 instead. So the licence is the opening axis — the `flux-2` pattern — rather than a footnote.

## Sources, by tier

**Official (read verbatim):**
- `MiniMaxAI/MiniMax-H3` model card — architecture (33B dense single-stream, ~13B in AdaLN branches, Qwen3-VL-32B encoder tapped at layer 50), output specs (4–15 s, 24 fps, 32 kHz stereo, 11 languages), the three-module split, VAE compression (`f16t4d24`), FL2VA/Ref2VA input limits
- `MiniMaxAI/MiniMax-H3` `LICENSE` — read in full including Exhibit A. Licensor **Nanonoble Pte. Ltd.**, Hong Kong governing law, $20M revenue threshold, mandatory UI attribution, redistribution + NOTICE mechanics, Qwen3-VL-32B separately Apache 2.0
- `Comfy-Org/MiniMax-H3` file listing — five build variants per checkpoint, three encoder quants, **two VAEs**
- **Official ComfyUI templates** `video_minimax_h3_{t2v,i2v,r2v}.json` pulled from `Comfy-Org/workflow_templates` via the **git tree API** (the contents API caps at 1000 entries and `video_*` sorts past the cut). Every numeric setting came from `widgets_values`; the docs pages omit them entirely. The templates' embedded author notes carried the **resolution table** and the **frame formula**.

**Community (named, attributed):**
- `-p-e-w-` (author of Heretic) — the abliterated-text-encoder myth. Mechanism: ablation stops *refusals*, but refusal lives in output layers a text encoder never uses, so you get perturbed hidden states and worse prompt adherence. Also that abliterated models *are* right for prompt **expansion**.
- `ThatsALovelyShirt` — the H3 encoder build is ~8 GB smaller than stock because output layers are absent
- `larryvrh` (original Turbo LoRA), `drbaph` (ComfyUI conversions), `Organix33` — Turbo recipe: **6–8 steps, `beta` scheduler, strength 1.0**; works across quant builds; FL2VA-trained works on Ref2VA
- The **split video/audio scheduling** failure — audio breaks at low steps with the Turbo LoRA. Fixes: `Larryvrh/ComfyUI-MiniMax-H3-Turbo` sampler node, ComfyUI PR #15243, or ~10 steps with `euler` over `res_multistep`
- `afinalsin` — XY grids showing text-encoder swaps make negligible difference on Z-Image
- Contested: whether the Turbo LoRA is worth its artefacts (`infearia`, `WARRIORPSIX` prefer stock at 10–15 steps)

## Non-obvious facts worth not re-deriving

- **Frame count must satisfy `17n + 5`** — formula `max(5, round(a*24)) + (5 - (max(5, round(a*24)) % 17)) % 17`. Hence defaults 73 and 124. The mod-17 mechanism is *observed, not explained* — do not add a mechanism claim without a source.
- Sampler chain is `SamplerCustomAdvanced` + **`BasicGuider`** — guidance-free, **no negative-prompt path** in the stock graph.
- CLIPLoader type is **`minimax`**.
- Templates default to **quantised** weights (`pruned_int8_convrot` + `nvfp4_awq`), which is itself the signal about memory pressure.
- `pruned` builds are **inference-only** — they drop the AdaLN parameters. Training needs non-pruned.

## Left undone

- **LTX-2.5's licence is gated** behind a contact-info agreement and was **not read**. The skill offers it as an alternative but flags the comparison as unverified. Accepting that gate is a user decision.
- Prompting craft and the Context-IR approximation are **reasoned from architecture**, not measured. Highest-value validation target.
- No LoRA *training* doctrine exists yet.
