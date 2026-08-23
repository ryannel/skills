---
name: generative-media-atlas
description: >
  The entry point to the generative-media suite: which open image or video model to use for a given
  job, how they rank and trade off against each other, which skills to install to do the work, and
  in what order. Use this whenever the user is choosing, comparing or planning rather than operating
  a model they have already settled on — even when they never say the words "which model" — and
  reach for it early, because the constraints it screens for (licence, territory, VRAM, prompt
  dialect) are cheap to check now and unrecoverable later. Triggers: "which model is best for
  photoreal faces / anime / typography / text in images", "which is easiest to train a character
  LoRA on", "rank these for realism", "Z-Image vs Krea 2 vs FLUX.2", "what can I run on 12 GB",
  "which video model gives me audio", "can I sell what this makes", "which licence lets me ship the
  pipeline", "best model for NSFW / adult / uncensored work" and which ones bar it, "I want
  realistic photos of a character I invented, in ComfyUI on RunPod — where do I start", or any
  multi-step goal crossing model choice, LoRA training, pipeline design and GPU deployment. It also
  owns **getting the skills onto the machine**: what to install with `npx skills add`, which
  siblings a job needs, and the canonical skills published outside this suite by RunPod, Comfy-Org
  and Hugging Face. Install this skill alone and it will tell you which others to pull and when. Per-model settings, filenames, node
  wiring, prompt dialects and licence clause detail live in the model skills — this owns the
  comparison between them, the route through them, and the decision of which ones you need. When a
  question could plausibly be answered by a model skill or by this one, start here: routing costs
  one read, and choosing the wrong model costs a week.
---

# Generative media atlas

This is the **map** of the suite: the skill you read *before* you know which skill you need.

Every other skill here answers "how do I do this with model X". This one answers the questions that
come first — **which X, why that one, what it costs you, which skills to install, and in what
order** — and then hands you off. It is deliberately the one skill in the suite that is useful on
its own, because it is the one people install first.

Two ideas organize everything below:

1. **Model choice is an elimination, not a beauty contest.** The constraints that rule a model out
   are binary and public; the quality differences between the survivors are small and taste-shaped.
2. **A finished result is a route through several skills, not one.** Locking a character, training
   its LoRA, rendering it well and running it on a rented GPU are four different skills' jobs, and
   the expensive mistakes happen at the joins.

---

## What this owns, and what it doesn't

**Routing outward is the whole job.** If an answer changes when you change the model, it is not
this skill's.

| Question | Where it belongs |
|---|---|
| **Which model for this job, and how do they rank** | **here** |
| **What a ranking costs you — the trade behind the winner** | **here** |
| **Which skills to install for a stated goal, and in what order to use them** | **here** |
| **The end-to-end route from "I want X" to a finished file** | **here** — the playbooks |
| **Which canonical skills exist outside this suite, and what each is actually for** | **here** |
| Node settings, filenames, prompt dialect, sampler, resolution, that model's licence text | the model skill — [`flux-2`](../flux-2/), [`ideogram-4`](../ideogram-4/), [`z-image`](../z-image/), [`sdxl`](../sdxl/), [`krea-2`](../krea-2/), [`anima`](../anima/), [`wan-2-2`](../wan-2-2/), [`minimax-h3`](../minimax-h3/), [`ltx-2-5`](../ltx-2-5/), [`scail-2`](../scail-2/) |
| The stage ladder, denoise bands, cross-family handoffs, mixing models | [`image-production-workflows`](../image-production-workflows/) |
| Dataset, captioning, hyperparameters, evaluating a run, publishing a LoRA | [`character-lora-training`](../character-lora-training/) |
| Volume layout, `extra_model_paths.yaml`, ComfyUI as a serverless endpoint | [`comfyui-on-runpod`](../comfyui-on-runpod/) |
| Provisioning a pod, GPU selection, `runpodctl`, pod lifecycle, cost guards | **RunPod's own skills** — see [The ecosystem beyond this suite](#the-ecosystem-beyond-this-suite) |
| Actually running a job on Comfy Cloud | **Comfy-Org's skills** — same section |

**One rule about disagreement, because this skill will occasionally be wrong before its siblings
are:** where a ranking here conflicts with the model skill it summarises, **the model skill wins.**
It is closer to the evidence and it is checked on its own freshness cadence. Report the conflict.

---

## Before you pick anything: three gates that can end the project

These lead because none of them is recoverable later, and this is the only skill that sees all of
them at once. Each is owned in full elsewhere; this is the triage.

**1. What are you shipping?** The licences in this suite do not split into "free" and "paid" — they
split by *what leaves the building*.

| You are selling… | The question the licence asks |
|---|---|
| **Pictures or clips** | May you *use* the model? Almost everything here clears this — including [`anima`](../anima/), whose non-commercial term explicitly excludes Outputs |
| **A pipeline, product or hosted API** | May you *ship or serve* the weights? One non-commercial rung stops the whole chain, first or last — [`image-production-workflows`](../image-production-workflows/) owns the chain question |
| **Anything, above a revenue line** | [`krea-2`](../krea-2/) is free under $1M; [`ltx-2-5`](../ltx-2-5/) under $10M — and LTX bars competing with Lightricks' products **at any revenue** |
| **…and the licence you pick has an ecosystem cost** | FLUX.2's Apache-2.0 [klein] 4B carries 133 published LoRAs against 9B's 653. Clearing gate 1 can mean training your own `[official — Civitai API, 2026-08-23]` |
| **Adult work** | [`ltx-2-5`](../ltx-2-5/)'s AUP bars it outright; [`wan-2-2`](../wan-2-2/) has no acceptable-use clause at all |

**2. Is the person real?** If a character resembles an identifiable living or deceased individual,
**Civitai will not host the LoRA — SFW or NSFW, no consent exception** — and the TAKE IT DOWN Act
has been under live FTC enforcement since 19 May 2026, reaching AI-generated intimate imagery of
real people. **The test is resemblance, not provenance**: a character you invented is clean, a
lookalike is the case the rule was written for. Settle it before you build a dataset —
[`character-lora-training`](../character-lora-training/).

This gate is where **adult work** is decided, and it is the one place in this skill where the answer
is not a trade-off. Adult generation with invented adult characters is a first-class use of these
models and is covered as such throughout. Two lines are absolute and are not licence questions:
**sexual content depicting minors**, and **sexual imagery of real, identifiable people without their
consent**. Neither is a capability gap to work around. Everything else on this axis is craft, and
the craft is below.

**3. Where are you?** [`minimax-h3`](../minimax-h3/)'s licence **excludes the US, EU, UK and South
Korea**. It is the suite's only territory gate, and it rules out the model entirely rather than
limiting it.

Then the ordinary one: **what hardware**, or are you renting? See *Hardware* below.

---

## The one rule that changes everything

**Eliminate on constraints, then rank on quality — in that order, and never the reverse.**

Constraints are binary, published, and fatal. Quality gaps between the surviving models are small,
contested, and usually fixable with a second pass. People pick a model on a comparison thread, build
for a week, and discover a licence or a dialect problem that was knowable on day one.

**The elimination ladder**, in order. Each rung removes models; only the last one ranks them:

| # | Rung | What it removes |
|---|---|---|
| 1 | **Licence** — what leaves the building | Shipping or serving the weights kills [`anima`](../anima/) (whose *outputs* stay free), [`ideogram-4`](../ideogram-4/)'s open weights and FLUX.2 [dev]/9B. Adult work kills [`ltx-2-5`](../ltx-2-5/) |
| 2 | **Territory** | [`minimax-h3`](../minimax-h3/) if you are in the US/EU/UK/KR |
| 3 | **Hardware** | Under ~12 GB the field narrows to [`sdxl`](../sdxl/), [`anima`](../anima/), FLUX.2 [klein] 4B, quantised [`z-image`](../z-image/) and [`wan-2-2`](../wan-2-2/) 5B. See the table below |
| 4 | **Capability** — can it do the job at all | In-image typography → only [`ideogram-4`](../ideogram-4/). Tracked person-replacement → only [`scail-2`](../scail-2/). Cuts inside one generation → only [`ltx-2-5`](../ltx-2-5/). Native audio → only [`minimax-h3`](../minimax-h3/) and [`ltx-2-5`](../ltx-2-5/). **Adult work → a capability axis in its own right**, see below |
| 5 | **Dialect** — will it understand you | Booru tags into a prose-trained encoder land as noise, and sentences into CLIP hit a 77-token wall. This is an encoder-class fact, not a preference |
| 6 | **Quality** | *Now* rank. See below — and expect the gaps to be smaller than the threads suggest |

Rung 5 is the one people skip. [`sdxl`](../sdxl/) and [`anima`](../anima/) want tags;
[`flux-2`](../flux-2/), [`z-image`](../z-image/), [`krea-2`](../krea-2/) want sentences;
[`ideogram-4`](../ideogram-4/) wants a JSON document. A model prompted in the wrong dialect looks
like a bad model.

---

## Hardware — what actually fits

Elimination rung 3. Practitioner figures for a comfortable run at native resolution, not vendor
minimums — several vendors publish none. Per-model detail is in each skill's *Quantisation & VRAM*
section; the full table with quant filenames is
[`references/model-rankings.md`](references/model-rankings.md) §7.

| Card | What runs |
|---|---|
| **6–8 GB** | [`sdxl`](../sdxl/) fp16 (its long-standing advantage), [`anima`](../anima/) `[flagged — re-verify]`, FLUX.2 [klein] 4B fp8, quantised [`z-image`](../z-image/) — reported running on an **RTX 2060** `[community — Royal_Carpenter_1338, 1084 pts]` — [`krea-2`](../krea-2/) Turbo fp8_scaled on an **8 GB 3070 Ti** `[community — niechta, 600 pts]`, [`wan-2-2`](../wan-2-2/) 5B |
| **12–16 GB** | [`krea-2`](../krea-2/) fp8_scaled, [`wan-2-2`](../wan-2-2/) 14B at Q4_K_M — but below ~12 GB prefer the purpose-built 5B over a deeply-quantised 14B |
| **16–24 GB** | [`z-image`](../z-image/) Base, FLUX.2 [dev] fp8, [`ideogram-4`](../ideogram-4/) nf4, [`wan-2-2`](../wan-2-2/) 14B, [`scail-2`](../scail-2/) fp8_scaled |
| **32 GB+ / rent** | [`ltx-2-5`](../ltx-2-5/) `[contested]`, FLUX.2 [dev] unquantised, and **most LoRA training** — [`comfyui-on-runpod`](../comfyui-on-runpod/) |

**The bands are conservative at the bottom.** Two well-received reports put models a tier below
where this table places them — Z-Image on a 2060, Krea 2 Turbo on 8 GB — so read a row as *where it
is comfortable*, not where it becomes impossible. **Training moves the floor up**, which is why
renting is the usual answer — with one exception worth
knowing even if you never make anime: [`anima`](../anima/) trains in roughly **6 GB at 768 px**, and
the real cost of learning to train is the three failed runs, which are free there.

---

## The rankings — and what each one costs you

Verdicts here; the evidence, the disagreements and the second-place cases are in
[`references/model-rankings.md`](references/model-rankings.md). Every ranking is a *summary of the
model skills*, which own their own claims.

**Photoreal faces and skin.** [`z-image`](../z-image/) → [`flux-2`](../flux-2/) [dev] →
[`sdxl`](../sdxl/) photoreal finetune → [`krea-2`](../krea-2/). The suite routes *here* on this axis
from four directions, which is what makes it settled rather than argued. **The cost:** Z-Image has
one strong realism-leaning look, fights stylisation, and its ControlNet is Turbo-only — so the
standard move is not "pick the winner" but **compose and control in [`sdxl`](../sdxl/) or
[`krea-2`](../krea-2/), then finish the face in Z-Image at ~0.2 denoise**. Realism is a pipeline
position, not a model.

**Consistent characters without training anything.** On *capability*: [`flux-2`](../flux-2/)
(multi-reference + PuLID) → [`sdxl`](../sdxl/) (InstantID/HyperLoRA, `[SEP]` routing for several
characters) → [`krea-2`](../krea-2/) (Identity Edit). [`z-image`](../z-image/) has no adapter
shortcut at all. **The cost:** these are faster to start and weaker under pressure — a trained LoRA
still wins on a character you will render a thousand times.

**But that is capability, not practice.** A year-sorted r/StableDiffusion sweep on 2026-08-23
returned **no top post naming PuLID or InstantID at all**; the work has moved to **edit models** —
Krea 2 Identity Edit, Flux [klein] 9B, Qwen-Image-Edit, mixed freely in one job. The adapters still
do things edit models cannot, but an adapter route today is one you debug alone
([`references/model-rankings.md`](references/model-rankings.md) §3.2). **One trap that fails silently
in a stock graph:** Krea 2 Identity Edit is an *unofficial* community fine-tune needing the
`ComfyUI-Krea2Edit` node pack for its dual conditioning `[community — Enshitification, 611 pts]`.

**Easiest to train a character LoRA on — and this splits three ways.** There is no single winner,
and treating it as one is the mistake:

| "Easiest" meaning | Winner | Why |
|---|---|---|
| **Best likeness out of the run** | [`ideogram-4`](../ideogram-4/), then [`krea-2`](../krea-2/) sampled through Turbo | One named cross-model test, six bases, ~30 runs `[community — MesmerTools, 2026-07-14; single source]` |
| **Fastest loop — most attempts per day** | [`z-image`](../z-image/) (~90 min/run, good by step ~900), [`anima`](../anima/) (~6 GB, so failures are free) | Iteration count is what actually teaches you what a dataset is missing |
| **Most documented — least to invent** | [`sdxl`](../sdxl/) | Years of settled recipes, two trainers, separate Pony/Illustrious pools |

**Ecosystem size is a fourth axis, and it does not track the first three.** Counted on Civitai
2026-08-23 — and **re-measurable**, which matters more than the snapshot: run
[`scripts/civitai_census.py`](scripts/civitai_census.py) rather than trusting these figures once they
are a few weeks old. [`z-image`](../z-image/) Turbo, [`krea-2`](../krea-2/), [`anima`](../anima/) and the
SDXL family each carry **2,000+** published LoRAs; FLUX.2 [klein] 9B has 653 and **[klein] 4B just
133**; [`ideogram-4`](../ideogram-4/) has 34. Two traps fall out — **Z-Image's pool is on Turbo
(2,191+) not Base (671)**, which is the variant its own training doctrine trains on, and **picking
[klein] 4B for its Apache-2.0 licence costs you most of the FLUX.2 LoRA pool**. Full census, method
and caveats: [`references/model-rankings.md`](references/model-rankings.md) §4.5.

**The cost of the podium:** Ideogram 4's win is one author, one dataset; its **weights are
non-commercial**, so a LoRA trained there may be unshippable for the reason gate 1 names; and its
ecosystem is **34 LoRAs on Civitai, exactly one of them a character LoRA**
`[official — Civitai API, counted 2026-08-23]`. The model may well train beautifully. Nobody has
done it in public. Krea 2 trains slowly and pays off only if you remember to
*sample* on Turbo. FLUX.2 [dev] is the one to skip — it needed ~90 GB of system RAM to quantise and
that test never finished a usable LoRA on it. On video, [`wan-2-2`](../wan-2-2/) is the mature
ecosystem (two LoRAs, one per expert, from one dataset); [`scail-2`](../scail-2/) has **no training
path at all**.

**Adult and NSFW work.** A dominant use of open-weights models, and treated here as a capability
axis rather than only a licence one — because the model that wins it is not the model that wins
realism, and the difficulty is routinely misdiagnosed.

| | The answer | The catch |
|---|---|---|
| **Image** | [`krea-2`](../krea-2/) — the busiest adult checkpoint ecosystem on Civitai (`LUSTIFY!`, `FinePorn v3 TURBO`, Moody Krea 2 Mix), typically Euler or ER SDE, 10 steps, guidance 1.0 | The checkpoint does the work, not your settings. Krea 2's safety tuning also drives its muted-expression tax — the same tuning `krea2filterbypass`-class LoRAs exist to undo |
| **Anime / illustration** | [`sdxl`](../sdxl/)'s Pony, Illustrious and NoobAI — still the deepest pool — with [`anima`](../anima/) rising fast and running where nothing else will | Anima's weights are non-commercial; Pony/Illustrious are not |
| **Video** | **[`minimax-h3`](../minimax-h3/), decisively** — *"far above LTX and Wan"*, *"the most powerful open source model"* `[community — AidenAizawa, Revolutionary-Bar766; convergent]` | **Its licence excludes the US, EU, UK and South Korea.** The capability leader is the one many readers may not lawfully use — gate 3 is not a formality here |
| **Video, licence-clean** | [`wan-2-2`](../wan-2-2/) — Apache-2.0, **no acceptable-use clause at all**, the only unencumbered adult path in the suite | Weaker prompt adherence; anatomy needs an NSFW-merged checkpoint (below) |
| **Ruled out** | [`ltx-2-5`](../ltx-2-5/) — its AUP bars explicit content universally, local weights included. Adult LTX work happens on **2.3**, which is practice, not permission | — |

**One boundary on this table: it ranks adult *scene* generation, not training bases.** If the
deliverable is a character LoRA used in adult work, the photoreal ranking above wins the base
choice — train on [`z-image`](../z-image/), and let the checkpoint ecosystem re-enter at scene
time. The reconciliation: [`references/adult-work.md`](references/adult-work.md) §2.

**The one reframe that saves the most time: the limit is training data, not refusal.** Open-weights
models do not refuse; they render poor anatomy because the base saw little of it. This is why
swapping in an abliterated ("heretic") text encoder does nothing — refusal lives in output layers a
text encoder never uses. Change the base model or the checkpoint. Craft, captioning and anatomy
failure modes: [`character-lora-training`](../character-lora-training/)
`references/nsfw-training.md`.

**And the diagnostic that follows from it**, which generalises well beyond adult work: **when seed
is the only variable that moves the result, stop rolling and change the checkpoint.** One
27-generation single-variable study on Wan I2V anatomy collapse found prompt, steps, LoRA weight,
clip length, shift and source image all made no difference, and 2 of 28 seeds were usable — swapping
to an NSFW-merged checkpoint fixed it in one run `[community — RedMimicStudios]`. Numbers and the
measurable QC proxy: [`references/adult-work.md`](references/adult-work.md) §3.

**Structural control (pose, depth, canny, regional).** [`sdxl`](../sdxl/), and it is not close —
union ControlNet, IP-Adapter and regional prompting, all mature. Then
[`z-image`](../z-image/)/[`flux-2`](../flux-2/) (Fun Union, custom nodes, Turbo-only on Z-Image) →
[`anima`](../anima/) (LLLite: lineart/depth/scribble, **no pose, no canny**) → [`krea-2`](../krea-2/)
(depth only) → [`ideogram-4`](../ideogram-4/) (`bbox` layout only). **The cost:** SDXL's control
comes with a 77-token CLIP window and no in-image text, which is why it is so often the *front end*
of a chain rather than the whole of it.

**And a correction that shows this skill's own failure mode.** The suite rates
[`ideogram-4`](../ideogram-4/) weak on characters because it has no identity adapter, no edit variant
and one character LoRA. **Those clauses are true and the conclusion was wrong** — a published
workflow gets identity from it with no adapter and no training, by asking for the character *twice in
one canvas* and cropping `[community — reality_comes, 402 pts]`. **"No adapter exists" describes
tooling, not capability** ([`references/model-rankings.md`](references/model-rankings.md) §3.1).

**Everything else, one line each.** Typography → [`ideogram-4`](../ideogram-4/), with no real
second. Anime → [`anima`](../anima/), or [`sdxl`](../sdxl/)'s Illustrious/NoobAI/Pony finetunes when
you must ship the weights. Widest aesthetic range → [`krea-2`](../krea-2/). Cleanest licence →
[`z-image`](../z-image/).

**Video, by what you are actually doing:** animating a still → [`wan-2-2`](../wan-2-2/) (and its I2V
is far stronger than its T2V, so lock the still with an image model first). Sound in the same pass →
[`minimax-h3`](../minimax-h3/) or [`ltx-2-5`](../ltx-2-5/), and which one is a licence question, not
a quality one. Several cuts in one generation → [`ltx-2-5`](../ltx-2-5/), alone. Replacing a person
in footage frame-for-frame → [`scail-2`](../scail-2/), alone. **A named gap:** nothing in the suite
does a freeform camera path.

---

## Pick your job, get your stack

The routing table. "Install" is the set of skills that job needs; run the command in
[Installing what you need](#installing-what-you-need). Full step-by-step routes, with what to read
at each step, are in [`references/playbooks.md`](references/playbooks.md).

| The goal | Route | Install |
|---|---|---|
| **Realistic photos of a character I invented, on rented GPUs** | Playbook A — lock anchor → dataset → train → evaluate → deploy → production ladder | `generative-media-atlas` `z-image` `character-lora-training` `comfyui-on-runpod` `image-production-workflows` + RunPod's |
| **An anime character, on my own card** | Playbook B — the 6 GB loop | `anima` `character-lora-training` `image-production-workflows` |
| **A design or marketing image with real text in it** | Playbook C — typography plate → composite | `ideogram-4` `image-production-workflows` |
| **Turn a still into a shot** | Playbook D — the image-to-video handoff, and the audio licence fork | an image skill + `wan-2-2` (or `ltx-2-5` / `minimax-h3`) |
| **Put my character into footage I already have** | Playbook E — edit frame 0, then track | `krea-2` `scail-2` `character-lora-training` |
| **Run all this as an API** | Playbook F — API-format workflows on serverless | `comfyui-on-runpod` + RunPod's `runpod`, `flash` |
| **Adult work, image or video** | Playbook G — checkpoint first, then licence, then anatomy | `krea-2` or `sdxl` (image) / `wan-2-2` or `minimax-h3` (video) + `character-lora-training` |
| **What's deployed on my RunPod account, and what is it costing me** | `comfyui-on-runpod` *Cost guards that actually work* (burn check, two-timer guards, agent-free teardown) → RunPod's `runpod-mcp`/`runpodctl` to act on it | `comfyui-on-runpod` + RunPod's |
| **I just want to know which model** | The elimination ladder above, then the rankings | this skill alone |

---

## Installing what you need

**The skills CLI has no dependency mechanism** — a skill cannot declare that it needs another, and
nothing is pulled transitively. That is why this skill carries install commands instead of relying on
its links: **the relative links above resolve only when the sibling is also installed, and dangle
otherwise.** A dangling link is not a bug report; it is the install command you have not run yet.

```bash
# The atlas alone — enough to choose a model and plan a route
npx skills add ryannel/skills --skill generative-media-atlas

# A playbook's stack, in one command
npx skills add ryannel/skills --skill z-image --skill character-lora-training --skill comfyui-on-runpod --skill image-production-workflows

# Browse the catalogue first
npx skills add ryannel/skills --list
```

Add `-g` for global rather than project scope, `-a claude-code` to target one agent, `-y` to skip
prompts. `npx skills update` refreshes installed skills — worth running against this suite, whose
subjects move weekly. To read a skill once without installing it:
`npx skills use ryannel/skills@z-image`.

**Ask before installing globally or into a repo you do not own.** Installing writes files into the
user's agent directories; it is a visible change to their machine, not a lookup.

Scopes, agent targeting, symlink-vs-copy, private repos and troubleshooting:
[`references/installing-skills.md`](references/installing-skills.md).

---

## The ecosystem beyond this suite

This suite deliberately does not restate what its vendors publish well. Three canonical sources
matter, and knowing what each is *not* is as useful as knowing what it is.

| Source | Install | What it owns | What it is **not** |
|---|---|---|---|
| **RunPod** — `runpod/runpod-plugins-official` | `npx skills add runpod/runpod-plugins-official` | 7 skills — `runpod` (router), `runpod-usage`, `runpodctl`, `runpod-mcp`, `flash`, `companion-clis`, `runpod-migrate` — plus 24 golden paths including `02-comfyui-pod`, `07-network-volume-handoff`, `20-model-caching-endpoint`, `21-storage-tiers`, `25-bake-vs-mount` | Not ComfyUI-aware. Where models must sit so a fresh instance finds them is [`comfyui-on-runpod`](../comfyui-on-runpod/)'s job |
| **Comfy-Org** — `Comfy-Org/comfy-skills` | `/plugin marketplace add Comfy-Org/comfy-skills` then `/plugin install comfy-cloud@comfy-skills` | 12 skills wrapping the **Comfy Cloud MCP** — `comfy-generate-image`, `comfy-generate-video`, `comfy-search-models`, `comfy-search-nodes`, `comfy-search-templates`, `comfy-upscale-image`, and others | **Command wrappers, not craft.** They execute a job on Comfy Cloud; they carry no per-model settings, prompt dialects or licence analysis. They pair with this suite rather than replacing it |
| **Hugging Face** — `huggingface/skills` | `hf skills add <name>` | `hf-cli` (fetching weights), `hf-mem` (estimating VRAM from safetensors/GGUF) are the two that matter here | No diffusion-training or image-model skills; its trainers are LLM and vision-classification shaped |

**Two things changed recently enough to catch people out:** RunPod ships **7** skills, not the 6
widely cited — `runpod-migrate` was added `[official — repo tree, read 2026-08-23]` — and
`metadata.internal: true` now hides a skill from discovery unless `INSTALL_INTERNAL_SKILLS=1`, which
is how a repo keeps authoring machinery out of its published listing.

No agent skills from Black Forest Labs, Stability, Alibaba/Tongyi, Lightricks, MiniMax or Civitai were
findable as of **2026-08-23** `[flagged — negative result from search; re-verify]` — which is the gap this suite exists to fill. Full inventories, and how
to judge a third-party skill before trusting it:
[`references/ecosystem-map.md`](references/ecosystem-map.md).

---

## Failure modes & QC

| Symptom | Cause (mechanism) | Fix |
|---|---|---|
| A week of work, then the licence blocks delivery | Ranked on quality before eliminating on constraints — rung 6 before rung 1 | Run the ladder in order; settle gate 1 against the *deliverable*, not the picture |
| Links in this skill 404 | Siblings not installed; the CLI resolves no dependencies | Install the playbook's stack — [Installing what you need](#installing-what-you-need) |
| The trained LoRA cannot be published anywhere | Dataset was a real person — resemblance, not provenance, is the test | Synthetic character; [`character-lora-training`](../character-lora-training/) gate |
| The model ignores half the prompt | Wrong dialect for its encoder class — tags into an LLM encoder, or sentences past CLIP's 77 tokens | Rung 5; the model skill's `prompting-guide.md` |
| Great model, wrong country | [`minimax-h3`](../minimax-h3/)'s territory exclusion is a licence term, not a geoblock you can ignore | [`wan-2-2`](../wan-2-2/) |
| GPU bill with nothing to show | Rented before the graph ran end to end once | Smoke-test cheap; `--terminate-after`; [`comfyui-on-runpod`](../comfyui-on-runpod/) and RunPod's `runpod-usage` |
| Works locally, breaks on serverless | The dual mount root — `/workspace` vs `/runpod-volume` | [`comfyui-on-runpod`](../comfyui-on-runpod/) |
| Chose the "best realism" model and the render still looks AI | Realism is a pipeline position, not a model — one pass rarely gets there | The production ladder in [`image-production-workflows`](../image-production-workflows/) |
| Swapped in an abliterated encoder to "unlock" anatomy; nothing improved and adherence got worse | Refusal lives in LLM output layers a **text encoder never uses** — there is no refusal path to remove, only perturbed conditioning | Change the base or checkpoint. Use abliterated models only for a refusing *prompt-expander* stage |
| Trained a character LoRA and the anatomy is still wrong | **Two different jobs at different scales** were confused — teaching *who someone is* (15–30 images) vs teaching anatomy the base lacks (1,500+, rank 128+) | Pick a base that already has the coverage, or stack a capability LoRA under the character one |
| Endless rerolling on a shot the model keeps breaking | Seed is the only variable moving the result — the base cannot hold that composition | **Stop rolling, change the checkpoint.** See the adult-work section |
| A model is written off as incapable, and someone posts a workflow doing it anyway | **"No adapter exists" was read as "the model cannot."** Ideogram 4's character reference is the worked example — a prompting construction, not tooling | Ask what the *capability* is before accepting a tooling-shaped verdict; check for a published workflow |
| This skill and a model skill disagree | The atlas summarises; the model skill is the source | **The model skill wins.** Report the conflict |

---

## Pre-flight checklist

1. Gate 1 settled — is the deliverable a picture, a pipeline, or the model itself?
2. Gate 2 settled — is the character synthetic, or does it resemble a real person?
3. Gate 3 settled — does any candidate's licence exclude your territory or your revenue band?
4. Hardware known: your card's VRAM, or the decision to rent, made before model choice?
5. Ladder run **in order** — licence, territory, hardware, capability, dialect, *then* quality?
6. Capability checked against what only one model can do — typography, tracked replacement,
   multishot, native audio?
7. Prompt dialect matched to the encoder class you picked?
8. Route written down as a sequence of skills, with the handoffs named — and every one installed?
9. If training: base chosen as the model you will *render* on, not the one that trains best?
10. If renting: cost guard set, and the workflow proven cheaply first?

---

## The suite map

Every published skill, and the question it is the answer to. This is the suite keyed by *question*;
[`image-production-workflows`](../image-production-workflows/) keeps the suite map keyed by *pipeline
role* — who composes, who refines, who finishes — and the two are meant to be read together.

| Skill | The question it answers |
|---|---|
| [`z-image`](../z-image/) | "Why do the faces still look plastic?" — the suite's realism owner and standard face-pass finisher; Apache-2.0 throughout |
| [`flux-2`](../flux-2/) | "How do I keep this character without training anything?" — multi-reference identity, PuLID; [klein] 4B is the Apache-2.0 escape hatch |
| [`sdxl`](../sdxl/) | "How do I control the pose/composition exactly?" — the deepest control, adapter and LoRA ecosystem, on 6–8 GB |
| [`krea-2`](../krea-2/) | "How do I get a look that isn't the AI look?" — widest aesthetic range, style references, Identity Edit |
| [`ideogram-4`](../ideogram-4/) | "How do I put real text in the image?" — typography, layout, JSON captions. Open weights are non-commercial |
| [`anima`](../anima/) | "How do I make anime that understands booru tags?" — 2B, ~6 GB, outputs commercially free, weights not |
| [`wan-2-2`](../wan-2-2/) | "How do I make this still move?" — the strongest unencumbered I2V path, plus the camera and motion rigs |
| [`minimax-h3`](../minimax-h3/) | "How do I get video with sound in one pass?" — **and may I, where I live?** |
| [`ltx-2-5`](../ltx-2-5/) | "How do I get several cuts out of one generation?" — plus the suite's generative video upscaler |
| [`scail-2`](../scail-2/) | "How do I put a different person into this footage?" — tracked, not re-generated |
| [`character-lora-training`](../character-lora-training/) | "How do I make an identity that survives prompts it never saw — and may I publish it?" |
| [`image-production-workflows`](../image-production-workflows/) | "How do I get from a render to something shippable?" — the ladder, mixing models |
| [`comfyui-on-runpod`](../comfyui-on-runpod/) | "Why can't ComfyUI find my model?" — volumes, mount roots, serverless |
| **this skill** | "Which of the above, and in what order?" |

---

## How to read the claims in this skill — two bars, by claim type

This skill holds two kinds of claim to two different standards, because they fail in two different
ways — plus a third that is peculiar to a router and worth naming.

**Hard facts — must be exact or it breaks.** The names and install commands of every skill here and
in the three external sources; RunPod's seven-skill inventory and its golden-path filenames;
Comfy-Org's twelve; the `skills` CLI's flags, scopes and the absence of a dependency mechanism;
`metadata.internal`; the shape of each licence gate (territory, revenue line, weights-vs-outputs
split); the Civitai likeness ban and the TAKE IT DOWN enforcement date. **Source of truth is
official** — the repository trees read directly, the CLI's README, the model cards and licence texts
via the model skills. A wrong install command fails loudly; a misread licence gate is a legal
problem. Vendor skill repositories add and rename skills without notice —
**re-verify before relying on them, regardless of who said it.**

**Craft — what actually makes a good choice.** The elimination ladder and its ordering; every
ranking and the trade attached to it; the hardware bands; the playbook routes and where their
handoffs fail; the three-way split in what "easiest to train on" means. **The authoritative source
here is the community and the practitioners the sibling skills cite** — plus two pieces of
first-hand evidence gathered for this skill: one named cross-model test for LoRA trainability,
MesmerTools' six-base comparison of 2026-07-14, which is **a single author on a single dataset** and
is marked as such wherever it is used; a **census of the Civitai API taken 2026-08-23**, which is
a direct measurement rather than a report, bounded by being one host — one that bans real-person
likeness outright and therefore undercounts a whole category; and **primary Reddit sweeps the same
day** across r/StableDiffusion and r/unstable_diffusion, top-sorted over the past year and month,
read for the realism, identity and adult-work axes specifically — the adult stack in particular is
reported from where that work is actually discussed rather than inferred. Where a community claim here carries a point count, that is the sweep. Rankings are stated with
confidence and mean "this is where the practice lands", not "this is measured".

**Derived claims — the third bar.** Almost every comparative verdict here is *synthesised from the
sibling skills*, which are themselves two-bar documents with their own provenance and their own
freshness cadence. This skill adds no new evidence for them. Two consequences: it inherits their
confidence rather than exceeding it, and **where it disagrees with a model skill, the model skill is
right and this one is stale.**

**Contested / unresolved points:**

- The character-LoRA trainability podium rests on one author's test `[community — MesmerTools; single source]`.
- [`ltx-2-5`](../ltx-2-5/)'s VRAM floor is 32 GB in documentation against 16 and 12 in the same
  vendor's marketing, published the same week `[contested]`.
- [`anima`](../anima/)'s 8 GB inference floor is one report on one AMD card `[flagged — re-verify]`.
- Whether Ideogram 4's LoRA win survives a second independent test is unknown — nobody has published
  a character recipe for it `[flagged — re-verify]`.

**Facts dated 2026-08-23**; ecosystem counts measured the same day. Fastest-moving: the external
vendors' skill inventories (RunPod went 6→7 between this suite's last two passes), the `skills` CLI's
flags, the Civitai counts (Anima and Krea 2 are adding LoRAs weekly), and any ranking whose model
shipped in the last quarter — which today is most of them.

**What the sweeps changed.** Realism **held** — Z-Image owns that conversation, convergent with the
suite's routing. Identity did not: the capability ordering survives but the practice has moved to
edit models, and the "Ideogram is weak on characters" verdict was **wrong**. On adult work, the
Civitai census **inverts** the ordering in this suite's own existing table, most likely because that
metric reads preview images and so undercounts video. All three are corrected above and filed as
findings against the skills that own them.

---

## Reference files

| File | When to reach for it |
|---|---|
| [`references/model-rankings.md`](references/model-rankings.md) | You have a ranking above and need the evidence behind it, the second-place case, or the axis-by-axis matrix — realism, identity, LoRA trainability, control, typography, anime, licence, video |
| [`references/playbooks.md`](references/playbooks.md) | You have picked a goal and want the ordered route: which skill at which step, what to read in it, where the handoffs silently fail, and what to check before paying for the next stage |
| [`references/installing-skills.md`](references/installing-skills.md) | You are getting skills onto a machine: scopes, agent targeting, bundles per playbook, updating, private repos, `metadata.internal`, and why nothing installs transitively |
| [`references/adult-work.md`](references/adult-work.md) | You are doing adult work and need the model choice settled: the Civitai explicit-share census and why it undercounts video, the image and video stacks people actually run, MiniMax H3's prompting rules, the anatomy-collapse study and its checkpoint-swap tell, and two open gaps |
| [`references/ecosystem-map.md`](references/ecosystem-map.md) | You are deciding whether an external skill covers something this suite does not — the full RunPod, Comfy-Org and Hugging Face inventories, and how to judge a third-party skill before trusting it |
| [`scripts/civitai_census.py`](scripts/civitai_census.py) | **An ecosystem or adult-share number here looks stale, or you want one for a base this skill doesn't list.** Re-measures both from the Civitai API — run it rather than trusting the snapshot, and read its header first: it encodes the bitmask semantics and the dead `nsfw` field that make hand-rolled versions silently wrong |
