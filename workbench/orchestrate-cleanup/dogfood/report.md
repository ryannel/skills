# Dogfood report: orchestrate 2.10.0 (working copy) leading `wordfreq`

Project: `/private/tmp/claude-501/-Users-ryannel-Workspace-skills/83533ccc-d83f-405b-ae66-ba7f9b3dcc39/scratchpad/dogfood/wordfreq`
Settings: 1 Claude builder, Default host claude, Review host other (Codex), headless, Merge local,
`Claude model: claude-sonnet-5-5`, `Codex model: gpt-6.2-sol`, `Claude planner: claude-sonnet-5-5 medium`,
`Codex reviewer: gpt-6.2-sol medium`, `Effort: medium`.

Outcome: **not Done.** WORDFREQ:M1 is Done (after 5 failed reviews). WORDFREQ:M2 failed 2 reviews (one finding
repeated) and I paused it at about 85 minutes of active time, under the "same failure repeats twice" and ~90-minute
limits. Spend: $4.81 Claude list price (floor) plus about 0.88M input / 9.0M cached / 95k output tokens on Codex,
across 31 turns, for a ~150-line CLI.

Note on time: the host suspended this session from about 00:23 to 08:23 CET. Active time was 23:39-00:23 and
08:23-09:03. Every wall-clock figure the script prints that spans that gap (flow `hours`, watch check-in) is
inflated by it.

---

## Main finding: reviewers are not held to the brief's size, so a small tool can't converge (verified)

The brief asked for "a small Python command-line tool" with a pytest suite that "covers the above, and `pytest`
passes". The Quality bar line said "a small, tidy standard-library Python CLI ... in the manner of `wc`/`sort | uniq
-c`". Nothing in the reviewer side stopped the Codex reviewers from escalating far beyond that:

- Design review 1: **10 Must Fix**; design review 2: **6 Must Fix**; design approved only by the 2-in-a-row limit.
  The revisions turned M1.7 into a mutation-testing item ("...and fails when any one of those behaviours is broken",
  backed by `docs/plans/WORDFREQ/checks/suite_guard.py`).
- M1 reviews 1-3 each failed M1.7 on **new** single-defect variants the suite didn't catch (ten-line cap; ties at
  the limit; ASCII decoding of FILE; doubled apostrophes; cross-line undercount; letter-digit split; marks after
  digits). `watch` called each round "0 on a finding an earlier review raised", so the escalation counts never
  reached diagnosis: an open-ended item gets the same builder over and over.
- After I (as the user) had a change planner close M1.7 to the listed variants, design review 3 raised 2 new Must
  Fix, including "the parser rejects positive integers" of 5,000 digits (CPython's int-conversion limit). The
  revision added a 1,000,000,000 limit as an assumption. M2's reviews then failed M2.2 twice on
  **Arabic-Indic zero-padded 5,000-digit numbers** (`.orchestrate/evidence/WORDFREQ/M2-review.md`).
- M1 review 4 failed M1.5 on subscript digits (`H₂O`) that design review 3 had itself introduced by reading the
  brief's "Unicode digits" as `str.isdigit()`, while the builder had followed the approved design's `Nd`.

Net: 8 milestone reviews, 1 pass, 0 first-review passes; 4 design reviews; 9 planner turns.

What would fix it: the reviewer prompts (`reviewer/prompts/review.md`, `reviewer/prompts/design-review.md`) should
judge a finding against the brief's "How it will be judged" and the Quality bar, and file anything beyond them (input
sizes the brief never mentions, adversarial encodings) as a Suggestion, not Must Fix. A planner item phrased "fails
when any behaviour is broken" should be refused by the planner's done-when guidance (`planner/references/done-when.md`)
as unbounded. And the escalation counts should treat "same item failed again on a new finding" as a repeat for the
purpose of reaching diagnosis, since the watch sign already notices it ("failed its last two reviews on the same
items (M1.7)") while the counts say 0 repeats.

---

## Places a skill, help or `next` was wrong, missing or made me guess

### Verified

1. **A planner can't remove a module.** `plan --kind change` asked to drop the ACCEPTANCE module (the user had said
   "one module"). Result: `INVALID`, problem `"changed docs/plans/ACCEPTANCE/RECORD.json; only the script writes
   record files"`. The `next` just reruns the same task, which fails the same way. Deleting a module folder
   necessarily deletes its record. I got through by adding a lead `--task`: "delete everything in
   docs/plans/ACCEPTANCE except RECORD.json". Now an orphan `docs/plans/ACCEPTANCE/RECORD.json` stays on main for good.
   Fix: let the script accept deleting a record whose module has nothing built (no milestone past not_started), or
   give the `next` the right instruction, and say in `planner/tasks/change.md` how to drop a module.

2. **The planner overrides the user's "one module".** The task said "Plan it as one module with one or two
   milestones". The planner wrote two modules because `planner/tasks/project.md` "## The acceptance module" says to
   always add an `ACCEPTANCE` module. Its report said: "The task asks for an acceptance module even in a one-module
   project". Fix: say in project.md that when the user limits the module count, the acceptance items go in the last
   milestone of the last module instead.

3. **`next` drops `--one-step`.** `plan --one-step` was REFUSED for unmerged files. Its `next.then` was the plan
   command **without** `--one-step`. The INVALID retry `next` after finding 1 also lacked it. Following `then`
   literally would have run the design reviews before the user saw the plan, which stage 3 forbids. Fix: carry
   `--one-step` (and every other flag the lead gave) into `then` and the retry `next`.

4. **`adopt`'s `next` forgets the refused command.** After the REFUSED plan above, `adopt` returned `next: ready`
   rather than the plan command it was adopting for. The lead has to remember `then` from the earlier result. Fix:
   have adopt print the pending `then`, or have plan's REFUSED tell the lead to run `then` after adopt.

5. **First plan's `next` has `command: null`.** PLANNED ended with
   `"why": "...show the user the plan as the stage before the first build says, then write the line and review
   WORDFREQ's design"`, with no command or argv. I had to compose the review command myself, or (as stage 4 implies)
   know that `run` does the design review. Fix: give `settings --set Builders ...` with `decides: human`, then `run`.

6. **`ready` lists `can_start` with no `next`.** After the design was approved, `ready` returned `can_start:
   [WORDFREQ M1]` and `next: null`. Fix: `next` = the `run --module WORDFREQ` command.

7. **The routine design revision told me to `adopt` a builder's unfinished commit.** After my `pause`, the paused
   builder's work stayed committed on `build/wordfreq` (`144332c`, tests and `checks/suite_guard.py`). The resumed
   `run` ended `DESIGN_NOT_APPROVED` with stopped_because `"...plan files aren't there:
   docs/plans/WORDFREQ/checks/suite_guard.py (committed here, not merged). adopt commits only those plan files and
   merges them"`. Its `next` was `adopt --worktree .../.orchestrate/worktrees/wordfreq`. That would merge half of an
   unreviewed builder commit to main, split from its tests. The cause is that check scripts the builder must edit
   live in the plans folder. I ran the revise planner from the main checkout instead, which worked. Fix: don't
   treat builder-owned check scripts under `<module>/checks/` as plan files for this test, or point `then` at the
   main checkout and leave the builder branch alone. Also, its `then` had `"by": "planner"` for a command the lead
   runs.

8. **The template's Setup command defaults to `npm ci`.** `settings --template` prints `- **Setup command:** npm ci`.
   Stage 2 says "Leave the test and setup commands to the planner". A lead copying the template into a Python
   project gets an `npm ci` that fails. Fix: print `none` as the template value, as Test command does.

9. **Glossary mark mismatch.** Stage 3 says "Take the `Proposed:` mark off each name the user agrees". The planner
   wrote a table with a `Status` column holding `proposed`. Fix: make the stage and the planner use one form.

10. **Plan REFUSED exits 0 and carries `ran_on`.** `plan` REFUSED for unmerged files exited 0. The top-level help
    lists only adopt, migrate and human as exiting 1 on REFUSED, so this is consistent but easy to miss. The
    result also carries `"ran_on": {"host": "claude", ...}` though nothing ran. Fix: drop `ran_on` when no turn ran.

11. **`report` contradicts `status` on M2.** After pausing, `report` said M2 is "Ready for Review, and waiting for a
    review: ... 2026-11-23T07:57:48Z". `status` said `M2 in_progress failed_reviews=2 ... last review fail
    2026-11-23T08:01:52Z`. Its "Needs you now" said "Nothing" with the run paused.

12. **`report` lists one design review twice.** When design review 3 started, the old `design-review.md` was kept
    as `design-review-2.md` (same 8680 bytes). `report` then listed "design: changes (22:56:53Z) design-review.md"
    **and** "design: changes (2026-11-22T23:20:09Z) design-review-2.md". The second has the rename's time, no host,
    and is the same review.

13. **`flow` names no sign on a struggling build.** Over 12 h: 8 reviews, 1 passed, 0 of 2 first reviews passed;
    79 commits, 10 of them code. Still `"signs": []`. `report` showed only one heuristic ("2 build sessions brought
    0 milestones to Ready for Review"), and that one was wrong: M1 had reached Ready for Review 3 times by then.

14. **`watch` details.**
    - A new watch with no earlier one reported `since` = start minus 3 h and flow `hours: 3.5`.
    - The check-in counts from when the last watch *ended*. So a watch started after a gap wakes at once:
      "check-in: 5h 10m since a watch last woke you" at 0 s.
    - It counted the `steps` parent as a builder: `"builders": {"running": 2, "limit": 1}`, and
      `"not_moving": ["WORDFREQ : building for 0s"]` with the milestone missing.
    - It showed `back_and_forth` "the counts now call for new_builder_session" after a change planner reset M1 to
      not_started, so the line was stale.
    - The sign "failed its last two reviews on the same items (M1.7)" sat beside "0 on a finding an earlier review
      raised". Item-level and finding-level repeats are both called "same", which confuses.

15. **`runs` shows the steps parent as stalled.** `WORDFREQ steps host not known ... 0 turns done, last activity
    27m ago` looked like a hung process while its child builder was active. Fix: show the child step's activity.

16. **Failed-review counts weren't reset by a definition change.** The change planner rewrote M1.7, and M1 went
    to not_started. But the later reviews continued `failed_reviews: 4, 5`, and `status` says `failed_reviews=5`.
    The `plan --help` text ("its counts start again") applies only to `replanned` milestones owed a diagnosis, which
    M1 wasn't. That may be intended, but the lead can't tell from the help whether a scope change resets the counts.

17. **A narrow change re-triggers a whole design review.** Closing M1.7 (3 files, wording only) made the design
    review owed again. The new review raised new, unrelated Must Fix (Unicode digits, 5,000-digit integers),
    restarting the loop. Fix: scope a design review after a change to the changed parts. Or say in stage 2 that a
    change to the done-when file costs a full design review.

18. **Model and effort for agents the user didn't name.** `settings` shows `codex planner: effort high, from the
    planners' default` even though Effort is medium. That is correct per the help, but a cost-conscious lead would
    expect `Effort:` to cover planners. The template note says Effort is "for builders and reviewers". It's fine,
    just easy to miss.

### Suspected (not confirmed)

- `flow`'s "milestones that reached Ready for Review: 0" in an early `report` seems to count only milestones whose
  current state is past Ready for Review, not events. Watch and status disagreed at the time.
- `watch`'s quota line quoted burn "on gpt-6.2-astra/high". This project never used that model, so the figure
  comes from the user's other Codex use. It's harmless, but the lead may misread it as this build's cost.

---

## Failures

- `plan --one-step` (first): `REFUSED`, exit 0, unmerged ORCHESTRATE.md and BRIEF.md (expected; fixed by `adopt`).
- `plan --kind change` (drop ACCEPTANCE): `INVALID`, exit 0, `changed docs/plans/ACCEPTANCE/RECORD.json; only the
  script writes record files` (finding 1).
- `run --module WORDFREQ` after the pause and change plan: `DESIGN_NOT_APPROVED` with `next` = `adopt` of a builder
  commit in the module worktree (finding 7).
- No SCRIPT_FAILED, no tracebacks, no HOST_FAILED.

## Model and effort on every launch

Every result's `ran_on` (13 results) was `claude / claude-sonnet-5-5 / medium`. Every usage-ledger row (31 turns)
named its model and effort: Claude turns `claude-sonnet-5-5 medium`, Codex turns `gpt-6.2-sol medium`. The M2 review
records carry `"observed": {"model": "gpt-6.2-sol", "effort": "medium"}`. **No WRONG_MODEL_OR_EFFORT** anywhere.

## Time and cost by stage (from steps_run minutes, timestamps and `cost`)

| Stage | When (CET) | Time | Cost |
|---|---|---|---|
| Interview, brief, cold read, settings | 23:39-23:41 | ~2 min | (lead only) |
| First plan (`--one-step`) | 23:41-23:43 | 2.5 min | $0.48 |
| Change plan (drop ACCEPTANCE), 2 tries | 23:44-23:45 | 1 min | $0.19 + $0.15 |
| Design reviews 1-2, revisions, approved at limit | 23:45-00:01 | ~15 min (2.2 + 5.9 + 3.1 + ~4) | 2 Codex review turns + 2 planner turns |
| M1 build/review rounds 1-3, then pause | 00:01-00:18 | ~17 min | — |
| Change plan (close M1.7/M2.7) | 00:19-00:20 | 1 min | $0.15 |
| Design review 3 | 00:20-00:22 | 2.6 min | 1 Codex turn |
| (host suspended) | 00:23-08:23 | — | — |
| Revise, design review 4, revise, approved at limit | 08:23-08:27 | 4 min | 1 Codex + 2 planner turns |
| M1 rounds 4-6, then PASS (Done) | 08:28-08:47 | ~19 min | — |
| M2 build, 2 failed reviews, then paused | 08:47-09:03 | ~16 min | — |

`cost` totals:

| Work | Turns | Tokens | Claude list price |
|---|---|---|---|
| Planning, Claude | 9 | 379k in, 3.7M cached, 108k out | $2.97 |
| Design review, Codex | 4 | 283k in, 1.8M cached, 24k out | — |
| M1 build, Claude | 7 | — | $1.45 |
| M1 review, Codex | 6 | 458k in, 5.3M cached, 53k out | — |
| M2 build, Claude | 3 | — | $0.39 |
| M2 review, Codex | 2 | 141k in, 1.9M cached, 18k out | — |
| **Total** | **31** | | **$4.81 (floor)**, plus Codex tokens |

`flow --since 12`: merges 8 and test-command runs 8, all 0.0 min median with no failures. Locks were never
contended. Reviews: 8, of which 1 passed. Signs: none (finding 13). The time went entirely into review/fix loops
(the main finding), not into merges, tests or waiting.

## State left behind

`wordfreq` on main: M1 is Done, M2 is in_progress (paused, 8/9 items pass, M2.2 failing). No runs are going and no
watch is running. Nothing outside the scratch folder and the script's own folders was touched. `cleanup` would free
31.3 MB (WOULD_REMOVE listing only; nothing removed).
