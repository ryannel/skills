# Plan files: merged design (after three reviews)

Supersedes PROPOSAL.md. Sources: an independent from-scratch design, an adversarial critique checked against Thrum,
and a check against `agent_loop.py`.

## Layout

One fixed root (the `Plans:` line survives only for existing projects), one folder per module:

```
plans/                      (root name: owner to choose, plans/ or docs/plans/)
  STATUS.md                 the owner's page; generated, never hand-edited
  BRIEF.md  GLOSSARY.md
  ARCHITECTURE.md           opens with the module table; then interfaces
  <module>/
    DESIGN.md               planner; stable
    PLAN.md                 the present only
    LOG.md                  history, append-only, short entries
    DONE.json               unchanged
    ACCEPTED.json           script only
    BRIEF.md                optional feature brief
docs/evidence/<module>/     unchanged; review briefs go here too
```

Per-module folders end the reserved-name rule (plan-module/SKILL.md:59) and make a module one place to look.
Cost: ~28 path sites in agent_loop.py, module discovery by `*/DONE.json`, and a one-time `migrate` command (the
script must do it, since `adopt` refuses acceptance records).

## The whole project in one table

`ARCHITECTURE.md` opens with a fixed-shape table in build order, no status column:
`| # | Module | What it's for (plain words) | Needs |`. The planner keeps it; it changes only on a (re)plan. The
script parses it (~30 lines) and warns when a module folder has no row or a row has no folder.

## STATUS.md

Two sections. The overview comes first and is what the owner reads day to day; the full list is below it for the
occasional look at the whole project.

1. **Overview** (one screen):
   - a one-line progress summary, e.g. `4 of 11 modules done · 2 in progress · 5 to come`;
   - Waiting on you: open assumptions, attended items, parked milestones, proposed glossary names, unlanded plans;
   - Now and next: each running or ready milestone by its outcome-phrased name, with links to its plan and
     latest review;
   - Recently done: what the owner can now see or do, with review links; links the latest dated build report.
2. **All modules**: the ARCHITECTURE table joined to the records, in build order: `Done 3 Nov`,
   `M3 of 6 · Ready for Review`, `Waiting on SEA:M2`, `Not planned yet`.

Built only from stored facts (DONE.json, ACCEPTED.json, ARCHITECTURE table, PLAN.md's open assumptions) — never
from hand-written status prose. Extends `report_text`/`cmd_status`.

Committed, so the owner can read it on GitHub or a phone, but never in the record's commit: the script writes it in
a separate best-effort commit after a record lands. On conflict it regenerates from the new tip rather than
merging; if that fails it skips, and the next landing catches up. A record write never fails because of it.
`status --format md` prints the same page on demand.

## PLAN.md holds the present only

- No `Milestone/Now/Next/Blocked/Reviews` lines. The script already knows state; hand-written status is what
  rotted (COOKED-DRAW `Now:`, ARCHITECTURE's status column, BUILD-PLAN's "Active work").
- Each milestone is one outcome-phrased heading. A Done one shrinks to that line plus a review link.
- Only the current and future milestones carry work lists and stop rules; builders tick boxes.
- `## Open for the owner` holds `Assumption:` lines. Answered ones are deleted (the answer is recorded with the
  `owner` command), so the report lists only open ones. `assumptions()` keeps reading PLAN.md.
- No review briefs, handoffs or design sections. Briefs go to evidence; design goes to DESIGN.md.

## LOG.md

Dated entries of a few lines each; detail goes to evidence and is linked. Builders and planners append. Reviewers
may read it (keep the existing "form your view first" rule, review-milestone:42) — no ban.

## Checks, where plans land (planner turn, adopt, builder land)

Refuse on a planner turn, warn elsewhere:
- PLAN.md over ~1,500 words, or containing status lines, `###` sections, a log, or a body under a Done milestone.
- A LOG.md entry over ~8 lines.
- A tracked `*-PLAN.md` outside the plans root.
- `profile` warns when ORCHESTRATE.md exceeds about a page or carries status prose.

## Dropped from the first proposal

Hand-kept status lines, the 150-line cap, `.orchestrate/scratch/` (Thrum's tmp/ is already ignored; stray plans
are tracked files the planner converts or retires), and the reviewer's log ban.

## Thrum

A separate task in that repo after the skills ship: run `migrate`, rewrite ARCHITECTURE's opening table, move
review briefs out of plans, fold BUILD-PLAN.md into BRIEF.md, retire the stray plan files.
