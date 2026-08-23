# Playbooks — ordered routes from a goal to a finished file

SKILL.md routes a goal to a set of skills; this file is the route *through* them: which skill at
which step, what to read in it, where the joins fail silently, and what to check before paying for
the next stage.

**It owns sequence and handoffs only.** Every step's settings belong to the skill it names. Where a
playbook and a skill disagree on a number, the skill is right.

## Contents

1. [How to run a playbook](#1-how-to-run-a-playbook)
2. [A — a realistic character you invented, in ComfyUI on RunPod](#2-a--a-realistic-character-you-invented-in-comfyui-on-runpod)
3. [B — an anime character, on your own card](#3-b--an-anime-character-on-your-own-card)
4. [C — a design image with real text in it](#4-c--a-design-image-with-real-text-in-it)
5. [D — turn a still into a shot](#5-d--turn-a-still-into-a-shot)
6. [E — put your character into footage you already have](#6-e--put-your-character-into-footage-you-already-have)
7. [F — run the whole thing as an API](#7-f--run-the-whole-thing-as-an-api)
8. [G — adult work](#8-g--adult-work)
9. [The joins that fail silently](#9-the-joins-that-fail-silently)

---

## 1. How to run a playbook

**Install first, then work.** Each playbook opens with its stack. Nothing installs transitively —
see [`installing-skills.md`](installing-skills.md) — so a step that points at a skill you have not
installed will point at a dead link.

**Three rules that apply to all of them:**

1. **Settle the gates before step 1.** Licence, likeness and territory — SKILL.md's three gates. Each
   is cheap now and unrecoverable later.
2. **Prove the route cheaply before you scale it.** One image at low resolution, one 3-second clip,
   one 200-step training run. Every playbook below has a checkpoint marked **STOP** for this reason.
3. **Save the intermediate of every stage.** A bad final output diagnoses to a stage only if the
   stages left evidence.

---

## 2. A — a realistic character you invented, in ComfyUI on RunPod

**The goal:** a synthetic person you can render repeatedly, photoreal, on rented GPUs, in workflows
that a fresh instance opens without missing-model dialogs.

**Stack:**

```bash
npx skills add ryannel/skills --skill generative-media-atlas --skill z-image --skill character-lora-training --skill comfyui-on-runpod --skill image-production-workflows
npx skills add runpod/runpod-plugins-official
```

Substitute the render model if the elimination ladder sends you elsewhere — [`sdxl`](../../sdxl/) if
you need deep pose control, [`krea-2`](../../krea-2/) if you want a non-default look. **Whatever you
choose is also what you train on**, so make this choice before step 2, not after.

### Step 0 — gates

- **Likeness.** The character must not resemble an identifiable real person. Not "based on" — must
  not *resemble*. [`character-lora-training`](../../character-lora-training/), *Before anything: can
  you publish it?*
- **Licence.** If you will sell images, almost anything clears. If you will ship or host the
  pipeline, stay on [`z-image`](../../z-image/) (Apache-2.0, weights and outputs) or
  [`sdxl`](../../sdxl/), and keep every rung of the later ladder clear too.
- **Budget.** Set a cost guard before you create anything. RunPod's `runpod-usage` for GPU
  selection; every pod gets `--stop-after` at the session length plus `--terminate-after` as a
  backstop (batch pods: `--terminate-after` alone). And a rented-GPU session **ends with a burn
  check** — nothing `RUNNING`, volumes accounted for — before you call it done; the check and the
  why are in [`comfyui-on-runpod`](../../comfyui-on-runpod/), *Cost guards that actually work*.
  Agents running these playbooks: the burn check is a STOP gate, not a suggestion.

### Step 1 — lock the anchor image

One image that *is* the character. Everything downstream inherits it, so this step is worth more
attempts than it feels like it deserves.

- Render it in the model you will deploy on, at its native resolution bucket.
- Read that model's `prompting-guide.md` — the dialect decides whether you get the face you asked
  for. [`z-image`](../../z-image/) and [`krea-2`](../../krea-2/) want sentences;
  [`sdxl`](../../sdxl/) wants tags inside 77 tokens.
- If the look is right but the skin is not, this is already the pipeline problem, not a model
  problem: finish the face through a Z-Image pass at ~0.2 denoise `[community — nsfwVariant, Civitai; via z-image and sdxl]`
  ([`image-production-workflows`](../../image-production-workflows/)).

**STOP:** do you actually like this face at 100% zoom? Everything after this step makes it *more*
permanent, not better.

### Step 2 — build the dataset

15–30 curated images beat 100 mediocre ones, and coverage beats volume `[community — NanashiAnon, L3n4/Civitai 25645; convergent, via character-lora-training]`.

- **The 8-point rotation is the thing people skip**, and its absence is the number-one cause of a
  LoRA that collapses to one pose. Plus elevation, shot size, expression, lighting.
- **The chained approach is standard**: hold the character description fixed, vary exactly one clause
  at a time, generate from the anchor with an edit model, curate hard.
- **A video turnaround solves rotation rather than approximating it** `[community — via character-lora-training]` — prompt a slow 360° with no
  cuts, cut to frames. Check the harvested model's licence first: some bar using outputs to train.
- Full protocol: [`character-lora-training`](../../character-lora-training/)
  `references/dataset-and-captioning.md` §2.

### Step 3 — caption

**Caption the residual.** Describe what varies; never describe the face. A caption that names the
identity teaches the model that the identity is optional. The trigger-token form depends on the
encoder class — a rare literal token on CLIP, folded into a natural phrase on an LLM encoder.

### Step 4 — train

- Hyperparameters: your model skill's `lora-training.md` first, the cross-model starting ranges in
  [`character-lora-training`](../../character-lora-training/) second.
- **Save checkpoints throughout.** The best epoch is rarely the last, and a run without intermediates
  gives you a verdict instead of a choice.
- Model-specific things you cannot skip: Z-Image trains on Base and deploys via the detailer swap;
  Krea 2 trains on Raw and *samples* on Turbo; SDXL's base finetune choice dominates everything.

**STOP:** run 200 steps and look at the training samples before committing the full run.

### Step 5 — evaluate

1. Training samples — free, and only to find roughly where the useful region is.
2. A **checkpoint × strength grid**, fixed prompts and seed, generated in the tool you will ship
   from.
3. **Judge it blind.** Shuffle unlabelled, pick, then reveal. This routinely reverses the labelled
   grid's answer.

**Probe out of distribution or you have tested nothing** — a costume, a painted style, a wide shot
where the face is small. Score likeness and prompt-adherence **separately**; they peak at different
checkpoints. Tooling: [`character-lora-training`](../../character-lora-training/)
`references/evaluation-and-tooling.md`.

### Step 6 — deploy to RunPod

- **The dual mount root is the whole step.** The same volume is `/workspace/` on a pod and
  `/runpod-volume/` on a serverless worker, so `extra_model_paths.yaml` must declare **both roots
  with identical key sets**. Miss one and you get the signature failure: it works in the studio and
  breaks in serverless.
- Lay the volume out by **which loader node reads it**, and fold LoRAs by base model.
- Move weights with a **CPU pod or the S3 API**, never a GPU pod.
- Keep a **manifest** so a new pod reproduces the old one.
- All of this: [`comfyui-on-runpod`](../../comfyui-on-runpod/). Provisioning, GPU choice and pod
  lifecycle: RunPod's `runpod` and `runpod-usage`.

**STOP:** smoke-test on the cheapest GPU that fits, and check *every* output branch before scaling.

### Step 7 — the production ladder

Base gen → refine/hires → **FaceDetailer, where the character LoRA swaps in** → tiled upscale →
ColorMatch and finish. Every stage past the first is bypassable; preview before the expensive
passes.

**The identity rule that decides this step: re-assert the character *after* the last whole-image
pass.** Any refine above ~0.35 denoise drifts the face `[community — convergent; via image-production-workflows]`, so the detailer stage goes last. Settings:
[`image-production-workflows`](../../image-production-workflows/).

### Step 8 — optional: make it move

The still you just finished is what controls the shot — Wan's I2V is far stronger than its T2V. See
playbook D.

---

## 3. B — an anime character, on your own card

**The goal:** a consistent anime character without renting anything.

**Stack:** `anima`, `character-lora-training`, `image-production-workflows`.

**Why this is a different playbook, not a variant of A:** [`anima`](../../anima/) inverts three of
A's assumptions. It is 2B, so inference runs on ~8 GB and **LoRA training fits in ~6 GB** — failed
runs are free, which changes how you learn. It prompts in **Danbooru tags** despite having an LLM
encoder, so A's sentence-prompt advice is actively wrong here. And it knows thousands of characters
by tag already, so **check whether your character needs a LoRA at all** before training one.

1. **Licence, first and specifically.** Outputs are commercially free — the card puts them outside
   the non-commercial term. The **weights** are not. Selling illustrations is fine; shipping a
   product or API containing Anima is not. If you must ship the model, this playbook becomes
   [`sdxl`](../../sdxl/) with an Illustrious/NoobAI/Pony finetune.
2. **Learn the dialect before anything else** — tag order, the `@artist` prefix (mandatory), the
   `score_*` and rating tags, and weights pushed far past SDXL norms. A wrong-dialect prompt reads as
   a bad model.
3. **Train, and do not train the LLM adapter** (`llm_adapter_lr 0`). Training it rewrites prompt
   understanding globally and presents as "Anima got worse", not as a broken LoRA — the single most
   confusing failure here.
4. **Control is the gap.** LLLite covers lineart, depth and scribble; there is **no pose and no
   canny**. If the shot needs pose control, compose in an SDXL anime finetune and refine through
   Anima at low denoise — a live community pattern, and cheap at 2B.
5. Finish on the ladder as in A, minus the realism passes.

---

## 4. C — a design image with real text in it

**Stack:** `ideogram-4`, `image-production-workflows`.

1. **Decide the surface first, because the licence does.** [`ideogram-4`](../../ideogram-4/)'s open
   weights are non-commercial with **no escape variant** — the commercial path is the hosted API or
   web app, not another checkpoint. Settle this before you build anything.
2. **Write the prompt as a JSON document**, not prose. The caption schema and `bbox` layout are the
   model's actual control surface. `references/json-caption-guide.md`.
3. **Treat the result as a plate, not a picture.** The strongest use is a typography or design layer
   composited into imagery another model rendered — Ideogram is weak on photoreal faces and has no
   control or identity adapters from anyone.
4. **The composite step is reconstructed craft, not a published graph** `[flagged — no canonical
   workflow]` — expect to invent it. [`image-production-workflows`](../../image-production-workflows/).
5. **If it must move: animate around the type, not through it.** Rendered text does not survive
   motion cleanly.

---

## 5. D — turn a still into a shot

**Stack:** an image skill (whichever locked the still) + `wan-2-2`, or `ltx-2-5` / `minimax-h3`.

1. **Lock the still first.** This is the whole reason image and video live in one suite: I2V is much
   stronger than T2V, so the still carries the composition, the identity and the look. Spend the
   effort there.
2. **Pick the video model on the constraint, not the demo:**
   - Motion and camera control, and a licence with no conditions → [`wan-2-2`](../../wan-2-2/).
   - Sound generated in the same pass → [`minimax-h3`](../../minimax-h3/) **if you are outside the
     US/EU/UK/KR**, otherwise [`ltx-2-5`](../../ltx-2-5/) — and LTX bars explicit content and
     competing with Lightricks' products at any revenue.
   - Several connected cuts from one generation → [`ltx-2-5`](../../ltx-2-5/), alone.
3. **Match the handoff format.** Aspect ratio and resolution are per-model, and video models have
   frame lattices — LTX's `8n+1`, Wan's per-variant counts. A mismatch silently drops the tail.
4. **Post, in this order: restore or upscale first, interpolate second.** Reversed, the restorer
   inherits the interpolator's smears across double the frames. A per-frame image upscaler is wrong
   at either position — no cross-frame consistency, so it shimmers.
5. **If the clip has audio, most post nodes will drop it.** Re-mux deliberately.

---

## 6. E — put your character into footage you already have

**Stack:** `krea-2`, `scail-2`, `character-lora-training`.

This is the suite's most sequence-sensitive route, and the ordering is not obvious.

1. **You need real footage.** [`scail-2`](../../scail-2/) has no T2V and no I2V — it tracks a driving
   clip and cannot originate a shot.
2. **Edit the driving clip's own first frame into your character.** Not a reference image you like —
   *that clip's frame 0*, edited. [`krea-2`](../../krea-2/)'s Identity Edit is the standard tool.
   This is the undocumented step that decides whether the whole job works.
3. **Masks are the real control surface**, not the prompt — the prompt barely matters here.
4. **Know the limits before you shoot:** multi-person scenes are the known soft spot, clothing
   morphs past about five seconds, and **no SCAIL LoRA training path exists** — Wan LoRAs will not
   load either.
5. **If you need a specific likeness rather than "a different person"**, build the identity upstream
   first ([`character-lora-training`](../../character-lora-training/)) and bake it into frame 0.

---

## 7. F — run the whole thing as an API

**Stack:** `comfyui-on-runpod` + RunPod's `runpod`, `flash`, `runpodctl`.

1. **Build in the GUI, ship the API-format JSON.** Export (API) format is not the UI format; the
   `/prompt` endpoint takes the former. [`image-production-workflows`](../../image-production-workflows/)
   `references/workflows-as-code.md` compares the four automation routes.
2. **`/run` plus polling, never `/runsync`** for anything that takes real time.
3. **Validation errors arrive inside the status body**, not as an HTTP error — a job can "succeed"
   and produce nothing.
4. **Declare both mount roots** in `extra_model_paths.yaml`. This is where the studio/serverless
   split bites hardest, because it only appears in production.
5. **Smoke-test every output branch.** A video model with audio can emit a perfectly valid silent
   file.
6. Provisioning, autoscaling, webhooks and streaming are RunPod's own golden paths — `20-model-caching-endpoint`,
   `13-autoscaling-tuning`, `16-serverless-webhooks`.

---

## 8. G — adult work

**Stack:** `krea-2` or `sdxl` (image), `wan-2-2` or `minimax-h3` (video), plus
`character-lora-training`. Model choice and the census:
[`adult-work.md`](adult-work.md).

**Gate, and it is the one gate here with no trade-off.** Invented adult characters only. Sexual
content depicting minors, and sexual imagery of real identifiable people without consent, are
absolute lines — not licence questions and not capability gaps to route around. If a real person is
anywhere near the dataset, stop and read
[`character-lora-training`](../../character-lora-training/) `references/publishing-and-likeness.md`
before anything else.

1. **Pick the checkpoint before you pick settings.** This inverts the normal order and it is the
   single highest-leverage step. Adult results come from purpose-built finetunes and merges, not
   from a base plus clever prompting — reported settings on the leading Krea 2 adult checkpoints are
   deliberately plain (Euler or ER SDE, 10 steps, guidance 1.0) precisely because the checkpoint is
   doing the work.
2. **Settle the licence against what you are shipping**, not against the content.
   [`wan-2-2`](../../wan-2-2/) is the only video path with no acceptable-use clause at all;
   [`minimax-h3`](../../minimax-h3/) is the capability leader **and excludes the US/EU/UK/KR**;
   [`ltx-2-5`](../../ltx-2-5/) bars explicit content outright.
3. **If anatomy is wrong, do not reach for a conditioning trick.** The limit is training data, not
   refusal — an abliterated text encoder cannot help, because refusal lives in layers a text encoder
   never uses. Change the checkpoint.
4. **Do not try to fix missing anatomy with a character LoRA.** Teaching *who someone is* is 15–30
   images; teaching anatomy the base lacks is 1,500+ at rank 128+. Different jobs, different scale.
   Stacking a capability LoRA under a character LoRA is the usual move — and it frequently
   destabilises the character, which is a live unsolved constraint, not a solved recipe.
5. **Caption explicitly when training.** Euphemism teaches the model that the explicit content *is*
   the character. Automated captioners fail here, so adult video datasets are captioned by hand — a
   real cost on top of frame count.
6. **STOP:** before a long run or a rented GPU, generate one clip or one set. If only the seed moves
   the result, change the checkpoint rather than the seed.
7. **For video, work from a reference.** H3's undressing and anatomy work depends on a nude
   reference image (or close-up anatomy references); base nudity without one is unreliable. Ref2VA
   is the more flexible mode.
8. **Finish on the ordinary ladder** — detailers, restore-before-interpolate, ColorMatch. None of it
   changes here.

---

## 9. The joins that fail silently

The handoffs between skills are where the expensive failures live, because each side is individually
correct.

| Join | What fails | The rule |
|---|---|---|
| Image model → image model | Foreign latent produces black or deep-fried output, sometimes subtly | **Decode to pixels between families**, always |
| Refine pass → identity | Face drifts above ~0.35 denoise and nothing errors | Re-assert identity **after** the last whole-image pass |
| Training base → deployment base | LoRA loads on the distilled sibling at reduced strength and reads as "weak LoRA" | Train on what you will render on; record real compatibility in the manifest |
| Still → video | Aspect ratio, resolution or frame lattice mismatch; the tail is dropped without an error | Match the video model's buckets and frame arithmetic before generating |
| Restore ↔ interpolate | Interpolating first bakes noise into double the frames | Restore first, always |
| Pod → serverless | Model-not-found for a file visibly on the volume | Declare **both** mount roots with identical keys |
| Model licence → chain licence | Everything renders; delivery is blocked at the end | Settle the chain's terms, not each model's, before building |
| Skill → skill | A link points nowhere | The sibling is not installed — see [`installing-skills.md`](installing-skills.md) |
