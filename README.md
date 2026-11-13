# ryannel/skills

Deeply researched agent skills for Claude Code and other agents — grouped by domain, with sources tracked and claims re-checked against ecosystems that move weekly.

[![skills.sh](https://skills.sh/b/ryannel/skills)](https://skills.sh)

Skills live at `skills/<domain>/<skill-name>/`. See [`skills/README.md`](./skills/README.md)
for the layout and how to add a domain.

## Generative media

Image and video models, plus the craft that spans them. The image-to-video handoff —
lock a still with an image skill, then drive it with a video model — is why both live
together rather than in separate marketplaces.

**Start here if you don't know which skill you need.**
[`generative-media-atlas`](./skills/generative-media/generative-media-atlas/) is the
entry point: it ranks the models by job, settles most choices with a licence-first
elimination ladder, and routes a whole goal — *"realistic photos of a character I
invented, in ComfyUI on RunPod"* — through the skills it needs, with the install
commands for each. It is written to be useful installed on its own.

```bash
npx skills add ryannel/skills --skill generative-media-atlas
```

| Skill | Model | What it covers |
|---|---|---|
| [`generative-media-atlas`](./skills/generative-media/generative-media-atlas/) | **Cross-suite** | **Which model, and which skills.** Rankings by job (realism, identity, LoRA trainability, control, typography, anime, licence, video) with the trade behind each; the elimination ladder — licence → territory → hardware → capability → dialect → *then* quality; six end-to-end playbooks; install commands for this suite and for the canonical skills published by RunPod, Comfy-Org and Hugging Face |
| [`flux-2`](./skills/generative-media/flux-2/) | FLUX.2 (Black Forest Labs) | ComfyUI setup, 4-part prompting, hex color control, ControlNet, PuLID face identity, BFL API, LoRA training |
| [`ideogram-4`](./skills/generative-media/ideogram-4/) | Ideogram 4 (Ideogram, Inc.) | JSON caption schema, typography, bbox layout, web app / hosted API / self-hosted open weights |
| [`z-image`](./skills/generative-media/z-image/) | Z-Image (Alibaba Tongyi) | ComfyUI multi-stage pipelines, Fun Union ControlNet, character LoRA via FaceDetailer, LoRA training |
| [`qwen-image`](./skills/generative-media/qwen-image/) | Qwen-Image family (Alibaba Qwen) | Both open generations plus the hosted 2.0/3.0 surface: the Apache-2.0 20B family (T2I, Edit-2509/2511, 2512, Layered) — two-regime CFG rule, ComfyUI templates and quants, the Edit 1 MP-downscale bypass, bilingual text, ControlNet, diffusers, LoRA training, Edit-2511 as the no-training identity engine — and **Qwen-Image-2.1** (2026-09-20): 7B unified T2I + edit, native RGBA, ten references, mask-guided edits, `<image1>` tags, CFG off, under a **non-commercial research licence** |
| [`sdxl`](./skills/generative-media/sdxl/) | Stable Diffusion XL (Stability AI) | Finetune ecosystem, fast variants (Lightning/LCM/Hyper), ControlNet/IP-Adapter, photoreal prompting, LoRA training |
| [`krea-2`](./skills/generative-media/krea-2/) | Krea 2 (Krea AI) | Raw/Turbo open weights + hosted Medium/Large, ComfyUI setup, style references & style LoRAs, depth + pose ControlNets, the anti-AI-look craft, train-on-Raw/run-on-Turbo LoRA training with a live-use recipe and run ledger (render the dataset at 1024 native, 8–12 steps), Krea API & fal |
| [`anima`](./skills/generative-media/anima/) | Anima (CircleStone Labs) — **anime** | A 2B anime model that breaks the usual encoder rule: a Qwen3-0.6B LLM encoder that still takes Danbooru tags *and* attention weighting — at heavier weights than SDXL. Tag dialect and `@artist` prefixes, ~6 GB LoRA training via kohya-ss, and the **non-commercial licence** that decides it against Illustrious/NoobAI/Pony |
| [`wan-2-2`](./skills/generative-media/wan-2-2/) | Wan 2.2 (Alibaba Tongyi) — **video** | Task modes (I2V/T2V/FLF2V/S2V/Animate), the two-expert MoE wiring, motion & camera control (Fun Camera/Control/InP, VACE), the lightx2v speed LoRAs and their slow-motion tax, two-LoRA training, the image-to-video handoff, temporal failure modes |
| [`minimax-h3`](./skills/generative-media/minimax-h3/) | MiniMax H3 — **video + native audio** | Omni-modal video with synchronised stereo audio in one pass; **licence territory exclusions (US/EU/UK/KR) up front**; what's open vs hosted-only; FL2VA/Ref2VA modes, reference-audio conditioning, dual video+audio VAE wiring, prompting the soundtrack |
| [`ltx-2-5`](./skills/generative-media/ltx-2-5/) | LTX-2.5 (Lightricks) — **video** | **Native multishot** — several cuts in one generation, as a prompting technique with no node or flag; the 2.5-vs-2.3 split (different encoders, and the LoRA ecosystem still on 2.3), the `8k+1` frame lattice, distilled-at-CFG-1 defaults, and a licence that gates on **company revenue**, bars competing products at any size, and follows your LoRAs to whoever you give them to |
| [`scail-2`](./skills/generative-media/scail-2/) | SCAIL-2 (Z.ai / Zhipu) — **video** | Putting a different person into an existing video: a full fine-tune of Wan2.1-14B-I2V weights on a modified DiT, with SAM3 identity tracking. Mask semantics as the real control surface, the undocumented first-frame prep rule, multi-person limits, and why Wan LoRAs will not load |
| [`character-lora-training`](./skills/generative-media/character-lora-training/) | Cross-model | Character LoRA craft that transfers: dataset curation (count is not the lever, identity ratio, the resolution rule — render inside the base's band, never hi-res-then-downscale), caption-the-residual, checkpoint selection by rung and probe, synthetic dataset factories, blind pairwise evaluation and overfit signals — plus **adult/NSFW work as a first-class case** (base-model selection, explicit captioning, anatomy failures) and what makes a LoRA publishable at all (real-person likeness rules, NCII law) |
| [`comfyui-on-runpod`](./skills/generative-media/comfyui-on-runpod/) | Infrastructure | Running ComfyUI on rented GPUs so a fresh instance finds every model: the dual mount root (`/workspace` vs `/runpod-volume`), `extra_model_paths.yaml`, volume layout by loader, model manifests, pod vs serverless, API-format workflow deployment, cost guards |
| [`image-production-workflows`](./skills/generative-media/image-production-workflows/) | Cross-model | Multi-stage production pipelines (refine → detail → tiled upscale → finish), mixed-model handoffs between SDXL/Flux/Z-Image/Ideogram, regional prompting & inpainting craft, ComfyScript & workflows-as-code |

## Orchestration

A process for building software with AI agents in Claude Code and Codex: web apps, native apps, command-line tools,
libraries, engines, and work judged by taste. You talk to one agent, the lead. It finds out what you want, then starts
planners, builders and reviewers, and comes back to you when a decision is yours. A project describes itself once in
an `ORCHESTRATE.md` file of project settings, so the skills know nothing about your project in advance. The
[domain README](./skills/orchestration/README.md) walks through a whole project and gives the reasons for the design.

| Skill | What it does |
|---|---|
| [`interview-me`](./skills/orchestration/interview-me/) | Talks with you to find out what you want built and why, and writes the project brief that planning starts from |
| [`domain-language`](./skills/orchestration/domain-language/) | Agrees one name for each thing in the project with you, and keeps the glossary that plans, code and chat follow |
| [`plan-module`](./skills/orchestration/plan-module/) | Splits a project into modules, and writes each module's design, milestones and done-when file, and the project settings |
| [`build-milestone`](./skills/orchestration/build-milestone/) | Builds one milestone, proves it and merges it, in Claude Code or Codex |
| [`review-milestone`](./skills/orchestration/review-milestone/) | A new session judges a milestone that is Ready for Review, or a design, by using the product and reading the changed code |
| [`build`](./skills/orchestration/build/) | The lead's skill: runs the whole build with a chosen number of builders through `agent_loop.py`, which sets a milestone to Done only after running the checks itself |

Install the orchestration plugin and evaluator from an interactive terminal with Node.js, Git and Python 3:

```sh
npx @ryannel/orchestrate
```

Choose Claude Code, Codex or both when their CLIs are available. Choose **Global** for all projects, or
**Project** for Claude Code from inside the target Git repository. The full Codex plugin and evaluator
are installed globally. When Claude Code needs the project agents installed separately, the installer
writes portable copies to the project's `.claude/agents/` directory.

Restart open sessions and run `/plan-module` in the target project to write `ORCHESTRATE.md`.
For scripted installs, see [Setting up for Claude Code and Codex](#setting-up-for-claude-code-and-codex).
[Why it looks like this](./skills/orchestration/README.md).

<details>
<summary>Publish the installer</summary>

After merging, check out the merged revision. Sign in to npm with an account that can publish to the
`@ryannel` scope. Set a new version in `package.json` for each subsequent release, then run:

```sh
npm pack --dry-run
npm publish
```

The package is configured for public access on the npm registry. After publishing, verify with
`npx @ryannel/orchestrate --help`. The package versions the installer. Claude Code and Codex fetch
the orchestration plugin from the GitHub marketplace.

</details>

## Agent writing

The `skills/agent-writing/` folder holds two skills for writing what other AI agents act on. Each is its own
plugin. skill-creator and orchestrate both depend on prompting-agents, so installing either brings it with them;
orchestrate doesn't bring skill-creator.

[`prompting-agents`](./skills/agent-writing/prompting-agents/) is for any text another agent will act on: a brief
for a subagent or session, a goal for a long unattended run, a review request, a steer, a system prompt, or an
AGENTS.md or CLAUDE.md file. It says what such a text must carry, what to leave out, and how to write it plainly,
with one reference file per model. It is built from Anthropic's and OpenAI's guidance for Claude Opus 5.5, Claude
Fable 5.2, GPT-6 Astra and GPT-6.1 Sol; the research behind it is in
[workbench/prompting-agents](./workbench/prompting-agents/README.md). It replaced `instructing-agents` on
10 November 2026, and relies on its description to trigger, with no hook.

[`skill-creator`](./skills/agent-writing/skill-creator/) creates, rewrites and tests skills. It keeps the method of
Anthropic's skill-creator (write from a real task, test with and without the skill in fresh contexts, show the
person, fix the cause). Its one script, `check_skill.py`, finds the mistakes that make a skill fail without an
error. The research behind it is in [workbench/skill-creator](./workbench/skill-creator/README.md).

Install them with `python3 install.py --plugins prompting-agents,skill-creator` (see [Setting up for Claude Code
and Codex](#setting-up-for-claude-code-and-codex)).

## Install

```bash
# Browse everything in this repo without installing
npx skills add ryannel/skills --list

# One skill
npx skills add ryannel/skills --skill flux-2

# Several
npx skills add ryannel/skills --skill flux-2 --skill comfyui-on-runpod

# Pick interactively from the full list
npx skills add ryannel/skills
```

Install by **skill name** — it does not depend on which domain folder a skill sits in,
so these commands keep working if a skill is later regrouped. Target a specific agent
with `-a claude-code`, or install globally with `-g`.

Several skills cross-reference each other — `flux-2` points at
`character-lora-training` for shared training craft, the model skills point at
`comfyui-on-runpod` for deployment. Those links are relative between siblings, and
installing flattens the domain folder away, so they resolve **once both skills are
installed** and dangle if only one is. The `skills` CLI has no dependency mechanism,
so nothing is pulled transitively — if a skill you installed keeps referring to
another, install that one too. `generative-media-atlas` names the exact command for
whichever job you are doing.

As a Claude Code plugin instead:

```bash
/plugin marketplace add ryannel/skills
/plugin install generative-media-skills@ryannel-skills
```

These routes are for the generative-media skills. `prompting-agents`, `orchestrate` and `skill-creator` install
through `install.py`, below.

## Setting up for Claude Code and Codex

For `prompting-agents`, `orchestrate` and `skill-creator`, one command from a clone of this repo sets up both hosts
without editing settings by hand:

```bash
python3 install.py                       # all three plugins, both hosts, user scope
python3 install.py --replace-standalone  # the same, replacing an earlier npx-skills or hand install (see below)
python3 install.py --repo ~/code/app     # and set that repo up too
python3 install.py --plugins prompting-agents --host codex
```

It registers this repo on GitHub, `ryannel/skills`, as the `ryannel-skills` marketplace, so both hosts install
what is published into their own plugin caches. No session loads skills from a working copy that someone is
editing. If the marketplace is already registered from somewhere else, such as a local folder, it says so and
re-registers it from GitHub. To try changes before they are pushed, pass `--source .`, and run `install.py` again
without it afterwards. It ends by printing where each plugin loads from.

What each host gets (checked 9 November 2026 on Claude Code 2.1.239 and 2.1.317 and the Codex CLI 0.167.0-alpha.3.2
inside the Codex app):

| | Claude Code | Codex |
|---|---|---|
| How | adds `ryannel/skills` as the `ryannel-skills` marketplace, then `claude plugin install` for each plugin | the same marketplace through `codex plugin marketplace add` and `codex plugin add`; Codex reads `.claude-plugin/marketplace.json` itself. Without `codex` on PATH it uses the CLI inside `/Applications/ChatGPT.app` |
| Skills | each plugin's skills, as `plugin:skill` | each plugin's skills, listed as `plugin:skill`, where the app loads them (`$CODEX_HOME/plugins/cache`) |
| prompting-agents | the skill only; its description is what makes it trigger. Installing skill-creator or orchestrate installs it too, through the `dependencies` in `marketplace.json` | the skill, plus one line in `$CODEX_HOME/AGENTS.md` saying to apply it before a handoff. Codex ignores `dependencies`, so `install.py` adds it when you install skill-creator or orchestrate |
| orchestrate | the planner and evaluator agents, linked into `~/.claude/agents` from the installed plugin, because neither Claude Code version loads the `agents` a marketplace entry lists (`claude plugin details` shows `Agents (0)`) | the evaluator agent, linked into `$CODEX_HOME/agents` from the plugin cache by `install_agents.sh --global --codex-only` |
| `--repo` | says whether Claude will read the repo's AGENTS.md, judged from the CLI version and any `CLAUDE.md`, `.claude/CLAUDE.md` or `CLAUDE.local.md` in the repo or above it; when it won't and the repo has no `CLAUDE.md`, writes one holding `@AGENTS.md`. With orchestrate it checks `ORCHESTRATE.md`, and a failed check fails the run. `--scope project` declares the plugins in the repo's `.claude/settings.json` instead of user settings | nothing; Codex reads AGENTS.md |

**Replacing an earlier install.** Skills installed earlier with `npx skills` (in `~/.claude/skills`, `~/.agents/skills`
or `~/.codex/skills`) would load next to the plugins, giving two descriptions per skill, and an older hand-installed handoff hook in
`settings.json` would still fire. `install.py` finds them and stops before installing anything,
listing each one. `--replace-standalone` moves those copies to `~/.ryannel-skills-backup/<time>/`, removes the links
into them, and drops only the old hook's entry from `settings.json`, keeping a copy of the file there. A skill with
the same name that doesn't match any committed version of these skills is left alone.

**The retired `instructing-agents`.** `prompting-agents` replaced it. Installing `prompting-agents` uninstalls the
`instructing-agents` plugin, treats a standalone copy of the old skill as an earlier install, and rewrites the old
line in Codex's `AGENTS.md`.

**Updates.** Push to `main`, then run `install.py` again. Both hosts fetch the marketplace from GitHub and keep a
copy per plugin version. Claude Code re-copies a plugin only when its `version` changes, so `install.py` reinstalls
one whose copy was made from an older commit. Codex copies on every `install.py` run. With `--source <folder>`,
Claude Code 2.1.317 loads the plugins from that folder in place, which is why it is only for trying changes.

**Don't add a root `.claude-plugin/plugin.json`.** All four marketplace entries use the repo root as their source with
`strict: false` and declare their components, so a manifest there conflicts with every entry and none of the plugins
loads.

What stays manual:
- **Restart** open sessions; skills load at session start.
- **ORCHESTRATE.md.** `/plan-module` writes it, since its values are the project's.

**No hook, for now.** An earlier version shipped a PreToolUse hook that refused the first handoff in each context
with a one-line nudge to apply the skill, then called instructing-agents. It was removed on 9 November 2026 to test whether the description
alone triggers the skill, including late in a long session and after compaction. It's in git history if the trial
says it's needed.
