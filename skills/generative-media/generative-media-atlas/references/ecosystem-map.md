# The ecosystem map — canonical skills published outside this suite

This suite deliberately does not restate what its vendors already publish well. This file inventories
what those vendors publish, says what each source is *not*, and shows how to judge a third-party skill before
you trust it.

**These inventories were read directly from the repository trees on 2026-08-23.** Vendor skill repositories add
and rename skills without notice, so re-check before relying on a name.

## Contents

1. [RunPod — the infrastructure layer](#1-runpod--the-infrastructure-layer)
2. [Comfy-Org — the execution layer](#2-comfy-org--the-execution-layer)
3. [Hugging Face — the weights and memory layer](#3-hugging-face--the-weights-and-memory-layer)
4. [What nobody publishes](#4-what-nobody-publishes)
5. [Judging a third-party skill](#5-judging-a-third-party-skill)

---

## 1. RunPod — the infrastructure layer

**`runpod/runpod-plugins-official`** (the `runpod/skills` repo redirects here).

```bash
npx skills add runpod/runpod-plugins-official
```

**Seven skills** — one more than the six widely cited. `runpod-migrate` was added
`[official — repo tree, read 2026-08-23]`:

| Skill | What it owns |
|---|---|
| `runpod` | The router — start here when it is not obvious which of the others applies. Also hosts the golden paths |
| `runpod-usage` | Concepts: pods vs serverless, containers, storage tiers, **GPU selection** |
| `runpodctl` | The CLI — infrastructure, Hub, file transfer, SSH, doctor |
| `runpod-mcp` | The same management surface as structured MCP tool calls |
| `flash` | Writing and deploying your own code on RunPod serverless |
| `companion-clis` | Prerequisite CLIs: `hf`, `docker`, `gh`, `aws` |
| `runpod-migrate` | Migrating from the GraphQL API or REST v1 to REST v2 |

**Golden paths** live under `plugins/runpod/skills/runpod/golden-paths/` — 24 numbered recipes. Here
are the ones this suite routes to:

| Path | Why it matters here |
|---|---|
| `02-comfyui-pod` | ComfyUI on a pod, two variants — from scratch, and the prebuilt `runpod/comfyui` image (the default) |
| `07-network-volume-handoff` | Moving a volume between contexts |
| `20-model-caching-endpoint` | Keeping weights warm for a serverless endpoint |
| `21-storage-tiers` | Which storage class for which job |
| `25-bake-vs-mount` | Bake weights into the image, or mount from a volume |

Others cover autoscaling, webhooks, streaming, load balancing, multi-region and monitoring.

**What RunPod's skills are not: ComfyUI-aware.** They will get you a pod with ComfyUI running. They
will not tell you where a text encoder must sit so `CLIPLoader` finds it. They will not tell you
that the volume mounts at a different root under serverless, or how to make a workflow JSON open
with every node resolved. That gap is exactly [`comfyui-on-runpod`](../../comfyui-on-runpod/)'s scope, and it is why this suite
routes to it instead of restating it.

**One deliberate omission worth knowing:** no skill in this suite quotes GPU prices. They go stale
within weeks and are model-specific. `runpod-usage` owns the general question, and `runpodctl gpu list`
owns the current number.

---

## 2. Comfy-Org — the execution layer

**`Comfy-Org/comfy-skills`**, installed as a Claude Code plugin:

```bash
/plugin marketplace add Comfy-Org/comfy-skills
/plugin install comfy-cloud@comfy-skills
```

**Twelve skills**, all wrapping the **Comfy Cloud MCP** server: `comfy-generate-image`,
`comfy-generate-video`, `comfy-generate-audio`, `comfy-generate-3d`, `comfy-upscale-image`,
`comfy-remove-background`, `comfy-search-models`, `comfy-search-nodes`, `comfy-search-templates`,
`comfy-help`, `technique-combine-people`, and one joke.

**What they are: command wrappers.** Each is a procedure — search for a template, build API-format
workflow JSON, submit, poll, retrieve. They are genuinely good at that, and two details in them are
worth borrowing no matter where you run. **Validate that a workflow has both an input node and a
save node before submitting** — partner API nodes commonly produce a tensor with no save node, so the
job succeeds and produces nothing. And **tell OSS and paid partner routes apart by node category**
(`partner/…` versus `model/…`), not by name.

**What they are not: craft.** They carry no per-model settings, no prompt dialects, no LoRA
hyperparameters, no licence analysis, and no comparison between models. `comfy-search-models` finds
a checkpoint, but it does not tell you which one to want. They also **do nothing without the Comfy Cloud
MCP server connected**, and they target Comfy Cloud rather than your own ComfyUI.

**They pair with this suite cleanly:** Comfy's skills know how to execute; this suite knows what to
execute and why. Use both when you are on Comfy Cloud. Use this suite plus
[`comfyui-on-runpod`](../../comfyui-on-runpod/) when you are running your own.

---

## 3. Hugging Face — the weights and memory layer

**`huggingface/skills`**, installed through the Hugging Face CLI:

```bash
hf skills add hf-cli
hf skills add hf-mem
```

Around 25 skills. Two matter for generative media:

- **`hf-cli`** — the Hub CLI for models, datasets, spaces and repos. This is how weights get fetched,
  and it is the tool RunPod's `companion-clis` sets up.
- **`hf-mem`** — estimates the memory needed to load safetensors or GGUF weights. Useful for
  sanity-checking a quant against a card before renting one, in a field where several vendors publish
  no VRAM figure at all.

The rest are shaped for LLM, Spaces, SageMaker and evaluation work. **`huggingface-vision-trainer` is not a
diffusion trainer** — it fine-tunes detection, classification and segmentation models. There is no
Hugging Face skill for training a diffusion LoRA.

---

## 4. What nobody publishes

As of **2026-08-23**, no agent skills for their models could be found from Black Forest Labs,
Stability AI, Alibaba/Tongyi, Lightricks, MiniMax, Z.ai or Civitai `[flagged — negative result from
search; re-verify]`. What exists instead is model cards,
inference repos and community write-ups of very uneven quality. That is the gap this suite fills,
and the reason its two-bar provenance discipline exists.

**Two consequences follow.** First, for any model in this suite, the model skill *is* the closest thing to a
canonical agent-readable source. The official artefacts it cites sit in the layer beneath it.
Second, if a vendor here does publish skills later, the right move is to route to them and delete the
overlap rather than maintain a second copy. That is the pattern
[`comfyui-on-runpod`](../../comfyui-on-runpod/) already follows against RunPod.

---

## 5. Judging a third-party skill

The ecosystem is large — a thousand-plus skills across community indexes — and quality varies
enormously. Here are five questions, in order of how much they tell you:

1. **Does it name sources, per claim?** A skill full of numbers with no attribution is somebody's
   single workflow generalised into confident prose. It may still be right, but you cannot tell, and you
   cannot re-verify it when it breaks.
2. **Is it dated?** Anything in this field without a date stamp is undatable, and therefore
   unmaintainable. A skill that says when its facts were checked is making a falsifiable claim.
3. **Does it separate hard facts from craft?** Filenames and licence terms fail loudly and must be
   exact. Denoise bands and rank choices are ranges that depend on your data. A skill that treats both
   with the same confidence is wrong about one of them.
4. **Is it a command wrapper or is it knowledge?** Wrappers age with an API and are cheap to replace.
   Knowledge ages with an ecosystem and is expensive. Both are legitimate, but know which you are
   installing, because they fail differently.
5. **Does it say who it is not for?** A skill that never routes you elsewhere has not thought about
   its boundary. That usually means it overlaps something else you already have.

**Then check what it does to your context.** A skill is loaded, not called: its `description` decides
when the agent reaches for it, and an over-broad description makes it fire on unrelated work. If a
newly installed skill starts appearing in answers it has nothing to do with, that is the description
at fault, not the model.
