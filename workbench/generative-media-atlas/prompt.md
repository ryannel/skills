# generative-media-atlas — authoring intent and sources

**Authored 2026-08-23.** The suite's first **hub skill**: not a model, not model-agnostic craft, but
the layer *above* both — the skill you read before you know which skill you need.

## Why it exists

The user's framing: *"some kind of skill that sits across all of these… which is the easiest model to
train character loras with, or which models produce the best realism and how they would be ranked or
traded off… It should know about the skills that exist, both the ones in this repo as well as others
from canonical sources like runpod… Ideally the user should be able to pull down just this skill and
it will pull the others as needed."*

Four jobs fall out of that, and all four are genuinely uncovered:

1. **Comparative verdicts.** Every model skill has a `Where X sits in the suite` table, but each is
   one model's view. Nothing held the *global* ranking, and nothing stated the trade behind a
   ranking.
2. **Routing a whole goal**, not a question. "Realistic photos of a character I invented, in ComfyUI
   on RunPod" crosses four skills and two vendors, and the expensive failures are at the joins.
3. **Knowing the external ecosystem.** `comfyui-on-runpod` already routes to RunPod's skills; nothing
   knew about Comfy-Org's or Hugging Face's, or told you what each is *not*.
4. **Installation.** The `skills` CLI has no dependency mechanism, so "install one and it pulls the
   rest" is impossible declaratively. It is possible *instructionally*, which is what this skill does.

## The design decisions worth recording

**The one rule is an elimination order, not a quality claim.** *Licence → territory → hardware →
capability → dialect → then quality.* This was chosen over a "best model" framing because it is what
the suite's own evidence supports: the constraints are binary and public, and the quality gaps at the
top are small and usually fixable with a second pass. It also makes the skill's answer stable as
models churn — the ladder outlives any particular ranking.

**"Easiest to train a character LoRA on" is deliberately answered as three questions, not one.** Best
likeness, fastest loop, and most documented have different winners (Ideogram 4 / Z-Image and Anima /
SDXL), and collapsing them is the actual mistake people make. This is the shape of the user's example
question and the shape of the honest answer.

**Rankings are derived, not researched.** The atlas synthesises from the sibling skills rather than
re-deriving model facts, and says so in a **third confidence bar**. The alternative — independent
research per axis — was rejected because it would drift against the model skills, which are already
maintained on their own freshness cadence. The rule that follows is stated in the skill: **where the
atlas and a model skill disagree, the model skill wins.**

**Two pieces of first-hand evidence sit under the derived rankings.** One published cross-model
comparison exists and is used as such — MesmerTools' 2026-07-14 six-base LoRA test (~30 runs, two
subjects, 16 GB cards), marked single-source everywhere it appears. And a **Civitai API census taken
2026-08-23** (§4.5 of `model-rankings.md`), which is measurement rather than report and corrected
three things the derived rankings had wrong or vague: Z-Image's LoRA pool is *large* (2,191+ on
Turbo) and sits on the opposite variant from its own training doctrine (Base: 671); FLUX.2 [klein]
4B, the Apache-2.0 escape hatch, carries 133 LoRAs to 9B's 653, so clearing the licence gate costs
the ecosystem; and Ideogram 4 — ranked *first* on trainability — has **34 LoRAs total and exactly one
tagged `character`**.

## Two justified deviations from `workbench/uniformity/STANDARD.md`

Both follow from the same fact — **this is the one skill designed to be useful installed alone.**

1. **SKILL.md is ~3,900 words against the cross-cutting band of 2,000–3,200** (total corpus ~12,000
   against 5,000–10,000). The cross-cutting band was derived from three *craft* skills, which own a
   technique and route everything else. A hub skill cannot route what the reader has not installed,
   so what a sibling would delegate, this must carry. Every section passes §5.3's test — delete it
   and the reader's next action changes. The overage is structural, not padding: the apparatus
   sections (§3.7–§3.11) are fixed-cost, and the required suite map is 14 rows here.
2. **It links every published skill.** §6.5's bidirectionality rule was honoured — a row pointing
   back to the atlas was added to all 13 siblings' suite tables — but the atlas is the one skill for
   which "links everything" is the job rather than a smell.

A third, smaller one: §3.9 names `image-production-workflows`'s suite map as the suite's canonical
map. It still is, for **pipeline roles** — who composes, who refines, who finishes. The atlas carries
a second `## The suite map` keyed by **the question each skill answers**, which is a different axis;
the two say so and are cross-linked rather than merged.

## Sources

**Internal (the authority for every comparative claim):** the ten model skills' `Where X sits in the
suite` tables, `character-lora-training`'s base-model table and evaluation protocol,
`image-production-workflows`'s suite map and handoff rules, `comfyui-on-runpod`'s routing table.

**External, read directly on 2026-08-23:**

| Source | What it gave |
|---|---|
| `vercel-labs/skills` README | The CLI surface, scopes, `skills use`, and the **confirmed absence of any dependency mechanism** — the fact the whole install story is built on |
| `runpod/runpod-plugins-official` repo tree | **7** skills, not the 6 this repo had recorded — `runpod-migrate` was added — and the 24 golden-path filenames |
| `Comfy-Org/comfy-skills` repo tree + skill bodies | 12 skills, all Comfy Cloud MCP command wrappers. Reading the bodies is what established they carry no model craft — the boundary claim in the skill |
| `huggingface/skills` | ~25 skills; only `hf-cli` and `hf-mem` are relevant, and there is no diffusion trainer |
| MesmerTools, 2026-07-14 | The only published cross-model character-LoRA comparison |
| Civitai `/api/v1/models`, censused 2026-08-23 | Per-base LoRA and character-LoRA counts, and the velocity sample. Reached by plain `curl` from Bash — no browser needed, unlike the Reddit route |
| r/StableDiffusion, swept 2026-08-23 | The realism and identity axes, top-sorted over the past year and month. Source of the Ideogram correction, the capability-vs-practice split, and two VRAM data points below the suite's stated bands |

**The Reddit sweep ran after all** (2026-08-23, via the Chrome extension, once a browser-pairing
handshake was completed — the extension being installed and signed in was not sufficient; a staged
Chrome update had left the native-messaging port dead until Chrome restarted). Reddit now redirects
anonymous requests to `old.reddit.com/login/?reason=lor2`, and the in-app browser blocks the domain
by policy, so a logged-in Chrome is the only route. Both facts are recorded in the
`community-research-method` memory.

**What the sweep changed.** Realism **held** — Z-Image owns that conversation across realism LoRAs,
finetunes and demonstrations, convergent with where the rest of the suite already routes. Identity
produced two corrections:

1. **The suite's Ideogram-4 character verdict is wrong**, and wrong in an instructive way. Every fact
   was right (no adapter, no edit variant, one character LoRA on Civitai) and the inference from them
   — incapable — was not. A 402-point workflow gets identity with no adapter and no training by
   asking for the character twice in one canvas and cropping. **Tooling absence was read as
   capability absence**, which is the failure mode a catalogue-shaped survey produces by
   construction. Written up as `model-rankings.md` §3.1 and filed as a finding against `ideogram-4`.
2. **The identity ordering is capability, not practice.** PuLID and InstantID appear in no top post
   in a year-sorted search for their own names; the work has moved to edit models mixed freely.
   The ordering stands, with the split stated — §3.2.

**One near-miss worth recording.** The atlas's first draft called Krea 2 Identity Edit a "mature
no-training option" — dropping that it is an *unofficial* community fine-tune needing its own node
pack. `krea-2` states both, in SKILL.md **and** `characters.md`. This is exactly STANDARD §6.2's
summarise-up hop: attribution and caveats lost on the way up into a summary. A hub skill summarises
thirteen skills at once, so it is structurally the most exposed to that failure in the suite —
worth a specific check on every freshness pass, not just a principle.

## Adult work is a first-class axis, not a licence footnote

**The first draft got this wrong in a specific way**: it mentioned NSFW only where a *licence*
prohibits it, and nowhere as a capability. Since adult content is a dominant use of open-weights
models, that made the routing layer silently useless for a large share of its readers — the model
that wins realism is not the model that wins this, and the difficulty is misdiagnosed by default.

Corrected by adding an adult-work ranking to SKILL.md, a capability clause to elimination rung 4,
Playbook G, and a dedicated `references/adult-work.md` — a **named file, not an appendix section**,
matching how `character-lora-training` gives it `nsfw-training.md`. Craft stays there; the atlas owns
only model choice and the trade.

**Two lines are stated as absolute** — sexual content depicting minors, and sexual imagery of real
identifiable people without consent — framed as *not licence questions and not capability gaps to
route around*, which is the only place in the skill where an answer is not a trade-off. Keeping that
sharp is what makes the rest of the coverage usable rather than coy.

**The measurement lesson from this pass.** The first census run scored `nsfwLevel > 1` as adult and
produced shares of 54–100%, which would have inverted the suite's table on bad arithmetic:
`nsfwLevel` is a **bitmask** (1 PG · 2 PG-13 · 4 R · 8 X · 16 XXX), so `>1` counts PG-13. The
`nsfw` boolean is separately **dead** — false for every model sampled, including XXX ones. The
re-run tests `L & (8|16)` and is the number that shipped. It still disagrees with
`nsfw-training.md`'s 2026-08-13 table, and that is filed as a finding with the likely cause named
(preview-image-derived levels undercount video LoRAs) rather than silently overriding a sibling.

## Audited against `skill-creator`

Run as documentation, not as machinery — `skill-creator`'s eval scripts spawn `claude -p`, which
CLAUDE.md forbids because it bills the API rather than the subscription.

**Passed as-is:** SKILL.md under the 500-line ideal (469); a `## Contents` TOC on every reference,
including both that exceed 300 lines; no all-caps `MUST`/`ALWAYS`/`NEVER` anywhere — the spec's
yellow flag for heavy-handed instruction; references organised by concern so only the relevant one
is read; "when to use" living entirely in the description rather than the body.

**Two real gaps, both fixed:**

1. **The description was descriptive where the spec says be pushy**, and — worse — it did not
   mention adult work at all, which had just become a first-class axis. Somebody asking "best model
   for NSFW video" would not have matched it. Rewritten with explicit adult triggers, an
   "even when they never say the words" clause, and a closing tiebreaker ("routing costs one read,
   choosing the wrong model costs a week") that addresses the spec's stated concern about
   *under*-triggering. 316 words, inside the suite's 180–320 band.

2. **No bundled script, despite an obviously repeatable deterministic task.** The spec's test is
   whether the same helper keeps getting rewritten — and the Civitai census is exactly that, plus it
   is the thing this session got *wrong* on the first attempt. Shipped as
   `scripts/civitai_census.py`, the suite's first bundled script. It encodes both traps in its
   header (the dead `nsfw` boolean; `nsfwLevel` being a bitmask where `> 1` counts PG-13) and
   reproduces the published figures exactly on a smoke test. The point is not convenience: it turns
   the skill's most perishable numbers from a snapshot into something the reader re-measures, which
   is the right shape for a fast-moving ecosystem and makes two freshness watchlist items
   mechanical.

**Evals written, not run.** `evals/evals.json` holds six task prompts covering the axes this skill
exists for, with assertions only where an answer is objectively checkable — routing, named
constraints, install commands — because the spec is explicit that subjective output should not have
assertions forced onto it, and comparative judgement is most of what this skill produces.
`evals/trigger-evals.json` holds 20 triggering queries, 10 positive and 10 near-miss negatives; the
negatives are deliberately adjacent (a denoise question, a missing-LoRA-on-RunPod question, a rank/
alpha question, a node-name question) since those are where a routing skill would wrongly fire.
Running either needs subagents, and the description optimiser needs `claude -p`; both were left for
a session where that is appropriate.

## Side effects of this pass

- **`metadata.internal: true` applied to both meta-skills.** The flag shipped in the `skills` CLI
  (though [#572](https://github.com/vercel-labs/skills/issues/572) is still open as an issue), which
  closes the wart CLAUDE.md documented. Verified with `npx skills add ./ --list`: the listing now
  returns exactly the 14 catalogue skills, while Claude Code still discovers the meta-skills through
  the `.claude/skills` symlink. Their descriptions' shouty `REPO-INTERNAL AUTHORING MACHINERY` prefix
  was softened, per CLAUDE.md's standing instruction.
- **Drift found in `workbench/comfyui-on-runpod/prompt.md`**, which records RunPod as shipping six
  skills. The published skill does not state a count, so nothing user-facing is wrong — but the
  atlas's `runpod-skill-inventory` watchlist item now covers both.

## Status

**Unvalidated in the sense that matters for a router:** no one has yet run a playbook end to end
against it. Playbook A is the one worth testing first, in `../skill-testbed`, because it is the
longest chain and the one the user asked for by name.
