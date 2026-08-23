# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

`skill-factory` is a workspace for **authoring agent skills and publishing them to [skills.sh](https://skills.sh)**. It is not an application — there is no build, lint, or test step. The "work" here is researching a topic and hand-authoring skill files. Claude Code is the generator: you read the references and prompt in the workbench and write the finished skill yourself; there is no script or CLI that produces skills.

**The marketplace is organised by domain, and each domain is its own suite.** Skills live at `skills/<domain>/<skill-name>/`, and each domain gets its own plugin entry in `marketplace.json` — which is also the heading users see when browsing the repo.

`generative-media` is the only populated domain today: image and video models plus the craft spanning them. **That suite's coherence is the thing to protect, not the repo's.** Its leverage comes from a shared production line — the `media-model-skill` authoring spec, the house style, the two-bar provenance discipline, the freshness protocol — and that only pays off within one ecosystem family. Image and video belong together because they share the ComfyUI stack, the LoRA tooling, and the dominant image-to-video workflow, where a still locked with an image skill drives a video model.

**Adding a second domain does not dilute the first, provided you keep them apart.** Concretely:

- **A new domain gets its own authoring spec.** Do not stretch `media-model-skill` to cover writing or engineering skills; it is shaped around model ecosystems (variants, licences, encoder classes, VRAM) and would produce nonsense elsewhere. Write a sibling spec.
- **Cross-skill links stay inside a domain.** Every link in the published repo is `../sibling/` or `../../sibling/reference.md`. That is what let the domain folder be introduced without rewriting 89 links, and a link reaching across domains usually means the two skills belong in the same one.
- **Freshness cadence is per-skill, not per-repo.** A writing skill probably does not need the daily tier that a days-old model does.

The earlier framing said the repo should stay generative-media-only. The domain folder is how that intent survives a wider marketplace: the constraint was always about keeping a *suite* coherent, and separate domains do not compete for the same production line.

## Directory roles

- `workbench/<skill-name>/` — Staging area for a skill in progress. Holds reference material gathered for the skill and an optional `prompt.md` describing what the skill should do / how to generate it. (Current example: `workbench/z-image/prompt.md`.) Nothing here is published.
- `skills/<domain>/<skill-name>/` — **The published skills.** This repo *is* the skills.sh marketplace (remote: `github.com/ryannel/skills`). Registration in `.claude-plugin/marketplace.json` and the README table is what actually publishes a skill.
  - **`generative-media-atlas` is the domain's entry point and the one skill written to work installed alone.** It ranks the models by job, carries the licence-first elimination ladder, routes whole goals through several skills, and holds the install commands — for this suite and for the canonical skills RunPod, Comfy-Org and Hugging Face publish. It is a **hub skill**, a fourth shape alongside the model and cross-cutting shapes in `workbench/uniformity/STANDARD.md`, and it justifies two deviations from that document: it exceeds the cross-cutting SKILL.md word band, because standalone install means it must *carry* what a sibling would route; and it links every published skill, because being the map is its job. When you add a skill to this domain, add it to the atlas's suite map and its rankings, and add the atlas row back to the new skill's suite table.
- `.agents/skills/` — **Authoring machinery only.** `media-model-skill` (the spec for writing a model skill), `skill-freshness` (the freshness protocol), and vendored `skill-creator` (eval machinery). Symlinked at `.claude/skills` so Claude Code discovers them natively.

  **Do not run `skill-creator`'s scripts.** `scripts/run_eval.py` — and everything built on it (`run_loop.py`, `improve_description.py`, the benchmark flows) — spawns a `claude -p` subprocess per query. **`claude -p` is billed through the Anthropic API, not the Claude Code subscription.** Read skill-creator as documentation of the eval *method*; run trigger evals in-session instead. Before running any script here, grep it for `claude -p`.

## Scope — what does not belong here

**This repo authors and publishes skills. It does not run them.**

Operational tooling — RunPod skills, deployment credentials, anything that provisions infrastructure or spends money — belongs in **`../skill-testbed`**, which symlinks the skills under test back to `skills/<domain>/` and holds the cost-gate rules. Findings flow one way: testbed discovers, skill-factory fixes.

The line is worth holding because the two jobs have different risk profiles. Authoring is free, local, and reversible. Validation rents GPUs.

Also out of scope: production workloads, which live in `../video-generation` (itself a *consumer* of the published skills, and the operational source of truth that `comfyui-on-runpod` was generalised from).

## Are the meta-skills published?

**They are *visible* but not *catalogued*, and the distinction matters.** `media-model-skill` and `skill-freshness` live in `.agents/skills/` in this repo, so anyone browsing GitHub can read them. They are **not** listed in `.claude-plugin/marketplace.json`, so they are not part of the published catalogue.

The reason for keeping them out of the catalogue is that both are load-bearing on *this repo's layout* — canonical reference slots, `skills/<domain>/<name>/` placement, marketplace registration, `freshness.json` state, and named ground-truth skills to pattern-match against. Published as-is they would misfire for anyone else. Generalised enough to publish, they would lose the specificity that makes them work.

**Being in `.agents/skills/` is deliberate, not accidental:** that path plus the `.claude/skills` symlink is how Claude Code discovers them when working *in* this repo, which is the only place they make sense.

**Resolved 2026-08-23: they no longer appear in `npx skills add ryannel/skills --list`.** The CLI scans `.agents/skills/` and `.claude/skills/` as standard locations, so the repo used to report 12 skills where the catalogue had 10. The `metadata.internal` flag has since shipped in the `skills` CLI — a skill carrying

```yaml
metadata:
  internal: true
```

is hidden from discovery unless `INSTALL_INTERNAL_SKILLS=1` is set. Both meta-skills now carry it, and the shouty **REPO-INTERNAL AUTHORING MACHINERY** prefix their descriptions opened with has been softened to a normal sentence, since the listing no longer needs the warning. **Verified by running `npx skills add ./ --list`:** it now returns exactly the catalogue, while Claude Code still discovers both meta-skills through the `.claude/skills` symlink. ([vercel-labs/skills#572](https://github.com/vercel-labs/skills/issues/572) is still open as an issue; the feature shipped anyway.)

Revisit if either becomes true: the house style is wanted by people outside this repo, or a second factory needs the same machinery. Until then the cost of maintaining a generalised fork outweighs the benefit.

## Freshness protocol

Published skills are snapshots of fast-moving model ecosystems. **`freshness.json`** (repo root) is the central freshness state: per-skill volatility tier (`hot`/`active`/`stable` → check cadence), last-checked date, a watchlist of that skill's volatile claims, and open drift findings. The `/skill-freshness` skill (`.agents/skills/skill-freshness/`) runs the protocol: it checks due skills via one parallel subagent per skill, merges bounded reports back into the state file, and stages repairs separately. When publishing a new skill, register it with `/skill-freshness register <name>`.

## Agent skill format

Each skill is a folder whose entry point is a `SKILL.md` file: YAML frontmatter followed by a markdown instruction body, plus any supporting files/scripts the skill needs in the same folder.

```markdown
---
name: <kebab-case-name>
description: <what it does + when to use it — this is the trigger the agent matches on>
user-invocable: true        # optional
allowed-tools:              # optional — restricts the tools the skill may call
  - Read
  - Write
  - Bash(ls *)
---

# <Skill title>

<Instructions for the agent…>
```

The `description` is load-bearing: it is how an agent decides whether to invoke the skill, so it must state both the capability and the "use when…" trigger.

## Authoring workflow

For a **model skill** (image or video), invoke the `media-model-skill` meta-skill — it is the spec, and it covers the whole job. In outline:

1. Create `workbench/<skill-name>/`, gather reference material into it, and capture intent in `prompt.md`. Nothing here is published.
2. Read the references and prompt, then author the skill by hand into `skills/<domain>/<skill-name>/` in the agent-skill format above (`generative-media` for a model skill).
3. Register it: add it to `.claude-plugin/marketplace.json` and the README table (this is what publishes it), then `/skill-freshness register <name>` so it doesn't silently rot.
4. Commit and push — this repo is what skills.sh serves.
