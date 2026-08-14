---
name: skill-freshness
description: >
  Run the freshness protocol for the published skills in this repo — detect whether the facts in
  skills/generative-media/* have drifted from reality, on a per-skill cadence driven by central
  state in freshness.json. Use this whenever the user wants to check, validate, audit, or refresh
  the skills' currency — "are the skills up to date?", "run a freshness check", "check if anything
  changed for ideogram", "has Z-Image-Edit shipped yet?", "what's due for a check?" — and also to
  apply fixes for previously detected drift ("fix the stale findings") or to register a newly
  published skill into the freshness state. It is state-driven (fast-moving skills are checked
  daily, frozen ones monthly), context-cheap (one subagent per due skill reports back a bounded
  JSON summary; the orchestrator never loads skill bodies), and it separates detection from
  repair.
user-invocable: true
---

# Skill freshness protocol

The published skills are snapshots of a moving world: models ship, licences get reconciled, single-maintainer repos cut releases, pricing pages change, and "announced, not yet released" becomes released. This protocol keeps them honest **without re-researching everything every time**: central state in **`freshness.json`** (repo root) records how fast each skill's area is moving and exactly which claims are volatile, so each check verifies a short watchlist instead of the whole skill.

**Three invariants — do not violate these:**

1. **The orchestrator (you, in the main conversation) never reads skill bodies.** You read `freshness.json`, spawn subagents, merge their reports, and update `freshness.json`. Subagents read the skill files and the web. This is the whole point of the design — the main context stays small no matter how many skills are checked.
2. **One subagent per due skill, launched in parallel** (all `Agent` calls in a single message). Each returns one bounded JSON report.
3. **Detection and repair are separate.** A check run updates state and reports findings; it edits no skill files. Repair is its own mode, run when the user asks.

## Modes

Parse the invocation argument:

| Argument | Mode |
|---|---|
| *(none)* | **Check** skills that are due (`last_checked + cadence_days ≤ today`) |
| `all` | Check every skill regardless of due date |
| `<skill-name>` | Check just that skill (e.g. `/skill-freshness z-image`) |
| `status` | Print the state table only — no subagents, no web. Cheap. |
| `fix` (optionally `fix <skill-name>`) | **Repair** open findings — see *Repair mode* |
| `register <skill-name>` | Seed a state entry for a newly published skill — see *Registering* |

## Check protocol

**Step 1 — read state.** Read `freshness.json`. Compute due skills for the mode. If nothing is due, print the status table (skill / tier / last checked / next due / open findings count) and stop — say when the next check falls due.

**Step 2 — fan out.** For each due skill, spawn one subagent (`general-purpose`, `run_in_background` not needed) **in a single message so they run in parallel**. Give each subagent this prompt, filling the placeholders — pass the watchlist and open findings as compact JSON inline:

```
You are a freshness checker for one published agent skill. Report facts, not edits — you must
not modify any file.

Skill: {name} at {absolute path to skill folder}
Last verified: {last_checked}. Today: {today}.

Its volatile-claims watchlist (the claims most likely to have drifted):
{watchlist JSON}

Already-known open findings — do NOT re-research or re-report these:
{open_findings JSON, or "none"}

Do, in order:
1. For each watchlist item, run its "check" against the live web (WebSearch/WebFetch: official
   repos, HF model cards, vendor docs/pricing pages, release feeds). Read the skill file(s) named
   in "where" only as needed to compare claim vs reality.
2. One broad sweep: search "what's new since {last_checked}" for this skill's subject (new
   releases, licence changes, major community shifts). Catches drift the watchlist doesn't cover.
3. Skim the skill files for NEW volatile claims worth watching ("as of", "not yet released",
   "contested", "[flagged]", version pins, prices) that the watchlist misses, and for watchlist
   items that have aged out.
4. Judge the area's current rate of change: hot (re-check daily), active (weekly-ish), or
   stable (monthly).

Return ONLY this JSON (no prose around it). Hard limits: ≤10 findings, every string ≤2 sentences,
include evidence URLs. A finding is "major" if acting on the skill's current text would mislead
someone (wrong licence verdict, released thing described as unreleased, wrong tool recommendation,
broken install path); "minor" if it's a stale date-stamp, drifted price, or aged framing.

{
  "skill": "{name}",
  "verdict": "fresh" | "drift",
  "flux": "hot" | "active" | "stable",
  "flux_evidence": "one line on why",
  "findings": [
    { "id": "kebab-slug", "severity": "major" | "minor",
      "claim": "what the skill says", "reality": "what is true now",
      "evidence": "URL(s)", "fix_hint": "file + section — what to change" }
  ],
  "watchlist_updates": {
    "resolved": ["item-id with reason it no longer needs watching"],
    "add": [ { "id": "...", "type": "...", "claim": "...", "where": "...", "check": "..." } ],
    "amend": [ { "id": "...", "check": "updated check text" } ]
  }
}
```

**Step 3 — merge reports into state.** For each report, update that skill's entry in `freshness.json`:

- `last_checked` ← today; if `verdict: drift`, `last_drift_found` ← today.
- Append new findings to `open_findings` (carry `found` date); keep already-open ones.
- Apply `watchlist_updates` (remove resolved, add, amend). Keep watchlists curated — ~5–9 items; if a subagent adds more, fold near-duplicates together.
- **Cadence adjustment:**
  - Drift found → `quiet_streak` = 0. No drift → `quiet_streak` += 1.
  - **Promote** (toward `hot`) when the subagent's `flux` is faster than the current tier, or a `pending-release` watch item resolved as *released* — a landed release means days of follow-on churn. Reset `quiet_streak`, update `why_tier` with one line of reasoning.
  - **Demote** one tier (hot→active→stable) when `quiet_streak` ≥ 3. Reset streak. Never demote a skill that has open **major** findings.
  - `cadence_days` follows the tier defaults in the `tiers` map unless there's a stated reason to override (record it in `why_tier`).
- **Linked skills:** if a skill with `linked_skills` pointing at it takes a *major* finding (check `image-production-workflows.linked_skills`), add a linked finding to the dependent skill referencing the source finding, so cross-references get swept during its repair.
- Bump top-level `updated`.

If a subagent returns null/garbage, leave that skill's state untouched except a note, and tell the user that skill's check failed.

**Step 4 — report to the user.** Compact and scannable:

- A table: skill / verdict / tier (with any change marked, e.g. `active → hot`) / next due.
- Major findings in full (claim → reality → evidence). Minor findings as one line each.
- If there are open findings, end with: run `/skill-freshness fix` to repair.

## Repair mode (`fix`)

Work from `open_findings` in `freshness.json` — no re-research; the evidence was captured at detection.

1. List open findings; if `fix <skill-name>`, filter to it.
2. **Minor findings** (date stamps, prices, aged framing, version pins): apply directly with one subagent per affected skill — give it the findings (with `fix_hint` and evidence) and have it make the edits in house style, reporting back a one-line summary per edit. Keep the two-bar confidence discipline: a fact verified from an official source today may upgrade tier; keep `[community]`/`[flagged]` attribution where the source class hasn't changed.
3. **Major findings** (a release landed, a licence verdict changed, new tooling exists): these need real research and authoring, not a patch. Stage them: create/append `workbench/<skill-name>/freshness-findings.md` with the finding details, and tell the user to run a proper update pass with the `media-model-skill` conventions. Only fix inline if the user explicitly says so.
4. Mark repaired findings: move from `open_findings` to a `resolved` list on the skill entry (keep `id`, add `resolved` date and one-line resolution). Re-promote consideration: a skill that just absorbed a major update is usually `hot` for the following week.

## Registering a new skill (`register <name>`)

When a new skill is published under `skills/generative-media/<name>/`:

1. One subagent reads the new skill and extracts its watchlist — search the files for `as of`, `not yet released`, `announced`, `contested`, `[flagged]`, prices, version pins, single-maintainer dependencies. Have it propose `tier` + `why_tier` from the model's release date and ecosystem velocity (released < 1 month ago → `hot`; active ecosystem → `active`; frozen/mature → `stable`).
2. Add the entry to `freshness.json` with `last_checked` = the authoring date (authoring counts as a full verification), `quiet_streak` 0, empty `open_findings`.
3. If the skill cross-references other skills' facts, add it to the relevant `linked_skills` arrays.

## State file reference

`freshness.json` — top level: `version`, `updated`, `tiers` (tier → default cadence days), `skills`. Per skill: `path`, `tier`, `cadence_days`, `last_checked`, `last_drift_found`, `quiet_streak`, `why_tier`, optional `linked_skills`, `watchlist[]` (`id`, `type`, `claim`, `where`, `check`), `open_findings[]` (finding + `found` date), optional `resolved[]`.

Watchlist item `type` vocabulary (informational, not enforced): `pending-release`, `contested`, `flagged-inference`, `pricing`, `ecosystem-gap`, `version-pin`, `date-stamp`, `community`, `structural`, `gap`.
