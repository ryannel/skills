# Review of the groundWork 36-hour record: what to change in orchestrate

Written 2026-11-11 from `delivery-record.md` (the only evidence) and the orchestrate source at 1.7.1
(`6989342`). The lead's own list, `proposals.md`, was read after the record and is compared at the end. Each
claim is marked **[record]** (read in the delivery record), **[source]** (read in the 1.7.1 code or skills, or in
git history), or **[inferred]** (my reading, not shown by either).

## 1. Where the rounds, time and tokens went

**Rounds.** The tables show 26 milestone verdicts: 22 fails and 4 passes (INTEGRATION-ROLLUPS M1, INTEGRATION-ROLLUPS
M2 round 9, SHARED-UI M1 round 2, SHARED-UI M2 round 9) **[record]**. The record's summary says 27 and 5; see
section 5. Three milestones produced 21 of the 22 fails: INTEGRATION-ROLLUPS M2 (8), SHARED-UI M2 (8) and SHARED-UI
M3 (5, still open). Each of the three reached a replan at its fourth fail, and two of the three then failed four
more times after the replan **[record]**.

**Time.** The stretches from a milestone's first fail to its acceptance or the pause add up to about 21h45 of the
36 hours: INTEGRATION-ROLLUPS M2 02:29–09:36, SHARED-UI M1 14:18–14:53, SHARED-UI M2 15:37–23:11, SHARED-UI M3
00:14–06:45 **[record, my arithmetic]**. A failed round costs about 40–55 minutes of wall time: SHARED-UI M2 ran 9
rounds in 8h18, and INTEGRATION-ROLLUPS M2 ran 8 more rounds in 7h08, which includes a 1h55 park. Of that time,
claim-to-verdict, the reviewer's part, was about a fifth (1h44 of SHARED-UI M2's 8h18; 61 minutes of M3's six
hours) **[record]**. The rest is builder rework. About 4 hours went to operational problems, not to building or
reviewing: section 2, cause 6.

**Tokens.** Summing the table rows by kind of session gives exactly the corrected total of 653.5M **[record, my
arithmetic]**:

| Kind of session | Sessions | Uncached in | Cached in | Output | Share of total |
|---|---|---|---|---|---|
| Builders | 15 | 5.23M | 362.8M | 0.76M | 56% |
| Milestone reviews | 26 | 5.71M | 230.1M | 0.61M | 36% |
| Planners (plans, replans, corrections) | 13 | 1.34M | 31.4M | 0.14M | 5% |
| Design reviews | 13 | 1.13M | 14.2M | 0.08M | 2% |

The 22 failed reviews used about 198M tokens, 30% of the total **[record, arithmetic]**. Cached input is 97.7% of
all tokens, and it is usually priced well below uncached input. Counted in uncached input and output, which cost
more per token, reviews spend about as much as builders do (5.7M against 5.2M uncached) **[record]**. So under any
plausible weighting, a failed round costs a full review (about 6–9M tokens, sometimes 23M) plus a builder rework,
and **the number of failed rounds is the main lever on tokens as well as time** **[inferred from the arithmetic]**.
How long a builder session runs matters less (cause 5).

## 2. Causes

### Cause 1: the failures were new instances of a few rules, fixed one instance at a time

My classification of each failed round's one-line summary into the rule it breaks **[inferred: the summaries are
one line each, and the reviews themselves are unavailable]**:

| Rule broken | Rounds |
|---|---|
| A. What counts as an integration, delivery or store read | INTEGRATION-ROLLUPS M2 R1, R2, R3, R4, R5 |
| B. Each path has its own pointer target | INTEGRATION-ROLLUPS M2 R4, R5, R6, R7, R8 |
| C. Collapsing, folding or switching keeps the right UI state | INTEGRATION-ROLLUPS M2 R1, R2, R3 |
| D. Every part of the screen shows the same revision | SHARED-UI M2 R1, R2, R3, R6, R7; SHARED-UI M3 R1, R2 |
| E. A failed or malformed refresh recovers in place, with retry | SHARED-UI M2 R4, R5, R6; SHARED-UI M3 R3, R4 |
| One-offs | SHARED-UI M1 R1 (alias precedence), M2 R7 (canonical vs authored data), M2 R8 (regression outside the items), M3 R5 (Search selection) |

**16 of the 22 failed rounds hit a rule that an earlier round of the same module had already failed on.**
INTEGRATION-ROLLUPS M2 rounds 5–8 are four consecutive rounds of B ("coincident exact paths", "opposing collapsed
paths", "opposing paths at exact depth", "several calls into one API surface"). SHARED-UI M2 R1–R3 are three
consecutive rounds of D, each in a different view (Search, standalone detail, canvas) **[record]**. The pattern
is a builder fixing the named instance and a reviewer finding the next one. The record doesn't say whether the
later instances were present in earlier builds and missed, or were introduced by the fixes (section 5).

What 1.7.1 has against this **[source]**:
- `review-milestone`: "Hold an open-ended item … to the range the design names and the inputs the product really
  has" (added 1.6.0, `98619f5`). This limits how far a reviewer roams. It does nothing to make the builder fix the
  whole rule, and these instances look like real inputs, not contrived ones.
- `plan-module`: "A finding that came up twice becomes a command in the project's test command … When you plan a
  module's next piece, or rewrite one". It acts only at planning time, and it matches the same finding, not the
  same rule.
- `build-milestone` and `FINDINGS_TEMPLATE` (`agent_loop.py:407`): "Add them to the plan as work items, fix them,
  re-verify the affected items". This is fixing by instance. Nothing asks for every place the rule applies.
- `repeats()` (`agent_loop.py:1161`) counts a finding as a repeat by the same name or the same item, "unless the
  reviewer said under `different` how it isn't the same defect". `review-milestone` tells the reviewer to add
  `different` "when an item that failed before fails again for a different reason".

**1.6.3 likely reads this record the wrong way.** Its commit message: "A milestone that failed eight reviews, each
on something new, was parked". It shipped at 23:07 on 10 November, 98 minutes after SHARED-UI M2 was parked at
21:29, so it probably refers to this run **[source; the link is inferred]**. Its answer is to stop counting new
findings toward a replan and to diagnose after six rounds. In this record the "new" findings were mostly new
instances of the same rule. A reviewer following 1.7.1's naming rules would give each a new name and mark it
`different`. `fails` would then stay low, and the milestone would go to a planner at round 6, two rounds later than
it did under 1.5.4 **[inferred: depends on item ids the record lacks]**. Here the existing rule is too weak, and
on this record it may be counterproductive.

### Cause 2: replans changed the plan but not the fix-by-instance pattern

All three replans came at the fourth fail **[record]**. After the INTEGRATION-ROLLUPS M2 replan, rounds 5–8 were
all rule B. After the SHARED-UI M2 replan to "an application-owned JSON replacement", rounds 5–6 were still rule E
(a malformed 200, a well-formed reply carrying the wrong endpoint) **[record]**. The replans changed the mechanism
or the items, but neither summary mentions a check covering every case of the rule. 1.7.1's replan guidance
offers three diagnoses: too big, outside the module, mechanism can't work (`plan-module`, "When a milestone keeps
failing on the same finding") **[source]**. A fourth case, "the rule is right but nothing covers all its cases",
is missing, and it is the one this record shows **[inferred]**.

### Cause 3: a replan's lesson stayed inside its milestone

SHARED-UI M3 opened by failing the two rules M2 had just been through: D in R1–R2, E in R3–R4 **[record]**. M3's
fresh builder at 02:10 "extended JSON recovery to supporting views", the mechanism M2's replan had introduced at
18:02 **[record]**. M3's milestone was planned at 11:14, before that replan **[record]**. Nothing in 1.7.1 tells a
replanning planner to check later milestones of the module, or the design, for the same mechanism or rule
(`plan-module`, `replan_task` at `agent_loop.py:1600`) **[source]**. About 4h37 and four review rounds of M3 passed
before its own replan **[record]**.

### Cause 4: the owner saw the requirement's cost only when the build was stuck

SHARED-UI M3's replan at 03:56 kept mounted-state preservation. The owner then relaxed it, allowing a
user-triggered reload and transient state resets, about 2h40 after that replan and about 7h34 after the
milestone's first builder started **[record]**. M3 R3 and R4 were failures of that requirement (a document reload,
a hidden selected step) **[record]**, so at least two rounds and the replan went into something the owner later
gave up. INTEGRATION-ROLLUPS M2 sat parked for 1h55 overnight, waiting on the owner **[record]**. In 1.7.1 the
owner is asked only at a park, or when a diagnosis ends `KEEP … owner` (`park_next`, `diagnose_task`) **[source]**.
A replan never puts the requirement's cost to the owner. The record doesn't say whether the planner added the
requirement or the owner had asked for it (section 5).

### Cause 5: long builder sessions, a smaller and mixed effect

The three sessions that covered three claims each used 35.0M, 66.6M and 70.6M tokens (`c5bc-1c5`, `c673-d40`,
`c784-824`) **[record]**. Single-claim fresh builders used 8.7–24.6M, apart from `c827-f74` at 55.4M for one
claim. `c382-878` covered three claims in 9.1M **[record]**. Per claim, continuing a session cost about the same
as starting fresh, and most of its tokens are cached. 1.7.1 already starts a fresh session at round 3
(`FRESH_AFTER_ROUNDS`) **[source]**. I don't see a strong case here.

### Cause 6: operational losses, about four hours

All **[record]** unless marked:
- The SHARED-UI design re-review stalled from 11:34 to 13:31. That is two hours, the default `--turn-timeout-hours
  2.0` **[source]**. 1.7.1 runs sessions headless by default, which may remove this stall's cause **[inferred]**,
  but it has no idle timeout: a turn that produces no output still waits out the whole two hours **[source]**.
- At 22:09–22:58 a reopened claim was blocked by "formatting of an Orchestrate-written ledger". The script writes
  its JSON as `json.dumps(indent=2)` (`write_json`, `agent_loop.py:956`), whatever the project's formatter expects
  **[source]**. That this was the cause is **[inferred]**.
- From M3 R5 at 05:11 to the next builder at 06:29 is 78 minutes. The 1.7.0 migration, its planner (13.6M tokens)
  and the migrated design re-review fall in that gap. The headless resume then failed because "the desktop thread
  already had an active writer". 1.7.1's Codex headless resume (`host_command`, `codex exec … resume`) doesn't
  check whether the app owns the thread, though its Claude path does (comment at `agent_loop.py:3888`)
  **[source]**.
- INTEGRATION-ROLLUPS M2 waited 1h55 while parked, overnight.

### Cause 7: design-review rounds, already addressed

The INTEGRATION-ROLLUPS design took five rounds, between 19:14 and 21:54 **[record]**. 1.5.3 ("Make design reviews
converge", 22:14 that evening) came after it **[source]**. The four later design reviews in the record took one
or two rounds each **[record]**, which fits the rule having worked. I propose no change.

## 3. Ranked changes

The ranking is by expected effect on rounds, time and tokens in a record like this one. Each change still ends
with an independent reviewer judging the written items, so none of them lowers the bar a milestone must pass.

### 1. Fix the rule, not the instance: a `rule` on each finding, a sweep by both sides, an enumerating check, and rule-based repeats

**What changes.**
- `review-milestone/SKILL.md`: each Must Fix states, in one general sentence, the rule it breaks ("every part of
  the screen shows the same revision after navigation"). Before writing the review, the reviewer tries that rule
  in every place it can reach that the rule covers, and lists every instance it finds under one finding, not one
  per round. When a later finding breaks a rule an earlier round named, it reuses that rule text, and `different`
  can't exempt it.
- `build-milestone/SKILL.md` and `FINDINGS_TEMPLATE` (`agent_loop.py:407`): for each finding, list every place in
  the code where the rule applies, fix all of them, and add an automated test that loops over those places.
  Record the list and the test in `LOG.md` or the evidence folder. The next reviewer reads that test, as the
  existing "a test written by the agent it grades proves little" rule already asks.
- `plan-module/references/done-when.md`: `findings[].rule` in the field list, in "Who changes what" and in "When a
  review fails". `GLOSSARY.md`: define the term.
- `agent_loop.py`: `repeats()` also matches on `rule` (normalised text, or a rule id the planner gives in
  `DESIGN.md`), ignoring `different`. `findings_problems()` requires `rule` on each finding. `history_lines()`
  prints the rule, so the replan and diagnosis tasks show the family at a glance.

**What it would have changed here [inferred].** INTEGRATION-ROLLUPS M2 R6–R8 (rule B) and SHARED-UI M2 R2–R3
(rule D) are the clearest cases: one sweep with an enumerating test after the first instance plausibly saves
those five rounds, and some of the A and E repeats too. If 6–10 of the 22 failed rounds are saved, that is roughly
5–8 hours of wall time and 120–200M tokens (a review plus a rework at about 20M each). Rule-based repeats would
also have sent those milestones to a planner on evidence of a stuck rule, rather than on a raw count.

**What it could break or cost.** Rule text written by different reviewers won't always match, which is why a rule
id from the planner is better than matching free text. A reviewer could word every finding as one sweeping rule
and push milestones to replan too soon. "Hold an open-ended item to the range the design names" still has to cap
the sweep. Sweeps make each review and rework longer, perhaps by 10–20 minutes. Loop tests over views can be
brittle UI tests. This partly reverses 1.6.3's "a new finding doesn't count toward a replan", so it reopens the
problem 1.6.3 was solving: a sound milestone parked by one reviewer's broad reading. The diagnosis step's
`KEEP … reviewer` remains the guard.

### 2. A replan carries its lesson across the module and puts the requirement's cost to the owner

**What changes.**
- `plan-module/SKILL.md`, "When a milestone keeps failing": add the missing fourth diagnosis, "the rule is right,
  but nothing covers all its cases", whose answer is an enumerating `check` (change 1). Require the planner to
  search `DESIGN.md` and every later milestone of the module for the same mechanism and rule, update them in the
  same plan, and re-run the existing design review on the result.
- Ask the planner to name, in its report, the one requirement driving the failures and whether a cheaper reading
  of the owner's words would remove most of them, quoting those words.
- `agent_loop.py`, `replan_task` and `diagnose_task`: put both asks in the task text. Where the planner's report
  names a cheaper reading, carry it on the `plan` result as a `decides: owner` ask that the lead raises in chat
  **while the rewritten milestone builds**. It does not stop the build.
- `build/SKILL.md`: one line telling the lead to relay that ask.

**What it would have changed here [inferred].** At the SHARED-UI M2 replan (18:02), M3's plan would have gained JSON
recovery for supporting views and the revision-coherence check, before M3 started at 23:12. M3 R1–R4 failed on
exactly those, about four hours and four rounds. The owner would have been asked at 18:02, or at 03:56 at the
latest, about mounted-state preservation, rather than deciding at about 06:45. Even the later date saves the
2h40 between the M3 replan and the scope change.

**What it could break or cost.** A planner that offers a cheaper reading every time trains the owner to lower the
bar. The ask must name the cost in rounds and the evidence, and the owner decides, so no broken work passes by
default. Rewriting later milestones at a replan makes the replan longer, and it needs another design review
(1–3M tokens and a few minutes in this record). A planner may change milestones that didn't need it. Restricting
it to milestones that use the same mechanism or rule limits that.

### 3. Operational hardening (time, low risk)

**What changes**, all in `agent_loop.py` unless named:
- An idle timeout: a turn with no new output or rollout events for N minutes (say 20) is stopped and retried
  once in a fresh session. Today only the two-hour `--turn-timeout-hours` applies.
- Before `codex exec resume`, check whether the Codex app owns the thread, as the Claude path does (`codex_owner`
  already exists), and start a fresh session with a handoff if it does.
- `write_json` writes in the project's formatter style. Alternatively, `land` runs the profile's formatter on the
  script's own files, or `migrate`/`profile` tells the owner to exclude them from format gates.
- `migrate` refuses, or warns and waits, while a milestone is `claimed` or `in_progress`. In `build/SKILL.md`,
  tell the lead to upgrade between milestones.

**What it would have changed here.** About 1h50 of the design stall, part of the 49 minutes at 22:09, and most of
the 78-minute gap after M3 R5: roughly 3 hours **[record times; the share each fix recovers is inferred]**. Tokens
saved are small, apart from the 14.7M of migration planning and re-review.

**What it could break or cost.** An idle timeout can kill a long silent build or test step. N must be well above
the project's slowest check, or count child-process activity as progress. Checking app ownership depends on the
same experimental IPC as the visible mode. Formatting through the project's formatter adds a dependency to every
script write.

### 4. A fresh pre-claim check on the items' edge conditions (worth a trial, unproven)

**What changes.** `plan-module/references/proofs.md` has "The builder gets a fresh opinion before a review" for
taste items only. `build-milestone/SKILL.md` would extend it to every `inspect` item, and to the rules named in
earlier findings: before claiming, a subagent given only the items, the project's edge conditions and the
earlier findings' rules tries to break them.

**What it would have changed here [inferred].** 22 of 26 claims failed. Even a pre-check that catches a third of
what reviewers caught would save rounds, each worth about 45 minutes. But the record has no data on what the
builders checked themselves.

**What it could break or cost.** It costs close to a review per claim (6–9M tokens), so it pays only if it catches
more than the formal reviewer would on a second look. It can't replace the review, which is the independent gate.
Ranked below 1–3 because it pays per claim, not per family, and the evidence for it is indirect.

### 5. Cost recording: already in 1.7.1

The lead proposed recording session, version, times and tokens per verdict, and a `report` command. 1.7.1 has
`usage` on claim and review records, plus `cost` and `report` commands (`cmd_cost`, `report_text`) **[source]**.
The record's gaps ("not separately identified", "a dash means no … count was recovered") come from the 1.5.4 era
and from visible Codex turns, which report no tokens (`incomplete_turns`) **[source]**. Remaining gap: one could
add per-session start and end times to `usage`. Low priority.

### 6. Rotating builders after two claims: not recommended now

Covered by cause 5: the evidence is mixed, and 1.7.1 already rotates at round 3. If change 1 lands, the fresh
session would get the rules list, which is what a rotation is meant to carry.

## 4. Compared with the lead's proposals

`proposals.md` #1 (class plus sweep plus counting) matches my change 1. I differ on where the class comes from,
preferring a planner-given rule id over free text, and in noting that 1.6.3 pushes the other way. #3 matches the
owner half of my change 2, but I would raise the ask at the replan and not block the build on it. My change 2
adds the propagation to later milestones, which the record supports (cause 3) and the lead didn't name. #2 is my
change 4, ranked lower. #4 I don't recommend. #5 is my change 3. #6 is mostly already in 1.7.1.

## 5. What I couldn't explain from the evidence

- **Verdict counts.** The summary says 27 verdicts and 5 passes, with "four of the passes" closing previously
  failed milestones. The tables show 26 and 4, and only three passes after a fail. Either a row is missing or the
  summary is wrong.
- **Missed or introduced?** Were later-round defects present in earlier builds and missed by earlier reviewers, or
  introduced by the fixes? This decides whether the reviewer sweep or the builder sweep in change 1 matters more.
  Only SHARED-UI M2 R8 is labelled a regression.
- **The 08:16 "routing fix".** Who made it, inside or outside the loop, and why a 21-minute rebuild then passed
  INTEGRATION-ROLLUPS M2 after eight fails. If the lead or owner made a structural fix by hand, the loop's own
  route to it was missing.
- **Item ids and finding names**, without which 1.7.1's repeat counting can't be replayed on this record.
- **The mounted-state requirement.** Whether the owner asked for it or a planner added it. `plan-module` already
  warns against unrequested requirements.
- **The 2h16 gap** in the INTEGRATION-ROLLUPS design between round 2 (19:21) and the next revision (21:37).
- **Why the design re-review stalled**, and whether headless mode alone would have prevented it.
- **The ledger format failure.** Which ledger, and which formatter rejected it.
- **Outlier sessions.** Why `c827-f74` used 55M tokens for one claim, and `c784-824` 1.3M uncached tokens, about
  four times its peers.
- **Quota weighting.** The meter moved from 54% to 62% over the window, but the record doesn't say how Codex
  weights cached input, so the token shares above can't be turned into shares of quota.
- **Whether any of the passes let broken work through.** The record has no owner grading of the verdicts.
