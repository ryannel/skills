# groundWork 36-hour record: why the rounds, and what to change

Written 2026-11-11 by Claude Fable 5.2 from `delivery-record.md` and the orchestrate 1.7.1 source
(`skills/orchestration/`, commit 6989342). I could not open the reviews, the done-when files or the project
settings of groundWork, so every statement about what a finding "was" rests on the record's one-line summary.

Three labels are used throughout:

- **Record**: stated in a row of the record, or arithmetic on its rows.
- **Source**: read in the 1.7.1 files or in `git log`.
- **Inference**: my reading. Each one says what it rests on.

## Short version

1. Nineteen of the 22 failed reviews fall into four families of defect. Each family took four or five rounds to
   exhaust, because a reviewer reported one or two members, the builder fixed exactly those, and the next reviewer
   found the next member. Nothing in 1.7.1 tells the builder to fix the family or the reviewer to sweep it.
2. One requirement, recovering from a failed refresh without reloading the page or losing state, entered through
   a review finding, was turned into a mechanism by two re-plans, and was relaxed by the owner at the end of the
   window. About 220M tokens (34% of the total) and about six hours sit downstream of it. No step asked the
   owner before the park.
3. The builder is never told to run the edge conditions the reviewer is told to run. Four of five milestones
   failed their first review.
4. About 12.7 of the 36 hours had no session making progress on a milestone: waits for the owner, one stalled
   session, a mid-milestone migration, and unexplained gaps.
5. The ladder that 1.7.1 ships (1.6.3) never judged a milestone in this record. All 26 milestone reviews ran on
   1.5.0 to 1.6.2. On paper the new ladder allows more failed rounds before the owner hears of it, not fewer.

## What the record shows

### Counts (Record)

| Milestone | Reviews | Failed | Re-plans | Parked | Builder start to Done |
|---|---|---|---|---|---|
| INTEGRATION-ROLLUPS M1 | 1 | 0 | 0 | no | 0h45 |
| INTEGRATION-ROLLUPS M2 | 9 | 8 | 1 | yes, 1h55 | 7h37 from planning |
| SHARED-UI M1 | 2 | 1 | 0 | no | 1h22 |
| SHARED-UI M2 | 9 | 8 | 1 | yes, 0h40 | 8h18 |
| SHARED-UI M3 | 5 | 5 | 1 | not yet | open at 7h33 |

The tables hold 26 milestone verdicts, 4 passes and 22 failures. The record's opening paragraph says 27 and 5.
See "What I couldn't explain".

### Tokens by kind of session (Record, summed from the rows; total 653.5M, matching the corrected total)

| Kind | Sessions | Tokens | Share |
|---|---|---|---|
| Builders | 15 | 368.7M | 56% |
| Milestone reviewers | 26 | 236.4M | 36% |
| Planners | 13 | 32.8M | 5% |
| Design reviewers | 13 | 15.4M | 2% |

A milestone review averaged 9.1M tokens and 10 to 13 minutes. A builder session averaged about 14M tokens per
claim. So one failed round cost roughly 23M tokens. In wall-clock time it cost 20 to 30 minutes on
INTEGRATION-ROLLUPS and 40 to 55 minutes on SHARED-UI, most of it the builder's fix turn. Builders, not
reviewers, are where both the time and the tokens went. The weekly quota meter moved from 54% to 62% over the
window, so time was the scarcer resource.

### Where the 36 hours went (Record for the intervals; Inference for the labels)

| Interval | Hours | What was happening |
|---|---|---|
| Milestones being built and reviewed | about 22.0 | the five milestones, less the waits below |
| Design and planning sessions | about 0.9 | less the waits below |
| Gaps with no session row: 9 Nov 22:39 to 01:59, 10 Nov 09:36 to 11:14 | 5.0 | unexplained |
| Gap inside the first design, 19:21 to 21:37 | 2.3 | unexplained |
| Stalled desktop design re-review, 11:34 to 13:31 | 2.0 | stall |
| Parked, waiting for the owner: 06:21 to 08:16 and 21:29 to 22:09 | 2.6 | wait |
| Migration to 1.7.0 and 1.7.1 in the middle of M3, 05:31 to 06:29 | 1.0 | upgrade |

## Causes

### C1. Each family of defect was found and fixed one member at a time

Rows (Record), grouped by me (Inference, from the one-line summaries):

| Family | Rounds | Summaries |
|---|---|---|
| What counts as an integration | INTEGRATION-ROLLUPS M2 r1 to r5 | wrong access and message counts; unresolved GraphQL counted; incompatible parties counted; rejected handler counted; non-record schema counted |
| Two paths share one pointer target | INTEGRATION-ROLLUPS M2 r4 to r8 | caption opened another group; coincident paths; opposing collapsed paths; opposing paths at exact depth; several calls into one surface |
| One surface stays on the old revision | SHARED-UI M2 r1 to r3, M3 r1 to r2 | search; removed area's drawing; heading, breadcrumb, title; canvas; breadcrumb, rail, Inspector; workspace switcher |
| A failed or malformed refresh | SHARED-UI M2 r4 to r7, M3 r3 to r4 | Flight failure reloads; malformed 200 crashes; wrong endpoint in a well-formed reply; conflict swallowed; 503 reloads; Journey refresh hides the step; 500 in place of 503 |

That is 19 of 22 failed rounds. The other three are SHARED-UI M1 r1, SHARED-UI M2 r8 (a regression outside the
items) and SHARED-UI M3 r5.

The record states the pattern itself in M3: "Interfaces passed. The workspace switcher still showed the old
name", then "The switcher passed. A People refresh returned 503". Each fix held. The next member of the family
failed the next round.

Source, on why 1.7.1 does not prevent it:

- The message a builder gets after a failed review (`FINDINGS_TEMPLATE` in `agent_loop.py`) says "fix them,
  re-verify the affected items". It asks for nothing about the cause or about other places the same cause
  reaches.
- `build-milestone/SKILL.md`, "The review", says only to make sure repeats stay fixed.
- `review-milestone/SKILL.md` asks for a result on every item and for findings a builder can reproduce. It does
  not ask the reviewer, having found one member, to look for the others before writing up.
- `plan-module/SKILL.md` has "A finding that came up twice becomes a command in the project's test command",
  added in 1.6.2. It applies only when a planner next plans or rewrites, so nothing between rounds uses it.

### C2. A requirement grew out of a review, was hardened by re-plans, and the owner was asked last

Rows (Record): SHARED-UI M2 r4 at 17:55 found that a failed Flight response reloaded the document. The re-plan at
18:02 was "around an application-owned JSON replacement". Reviews 5 to 7 then failed on faults of that
replacement. In M3, r3 found a 503 reloading the document, a new builder "extended JSON recovery to supporting
views" (55.4M tokens, the third-largest session), r4 failed and the 03:56 re-plan "kept mounted-state
preservation". At the cutoff the owner "allowed a user-triggered reload and transient state resets".

Arithmetic (Record): the sessions from the 18:02 re-plan to M2 r7, plus M3 r3 to r5, total about 220M tokens and
6h06 of wall-clock time.

Inference: the owner would have relaxed this requirement at 18:02 if asked, and much of that work would not have
been needed. Not all of it: retry, revision coherence and safe Search selection were kept, so some of those
rounds would still have failed.

Source: in 1.7.1 a re-plan never reaches the owner. `replan_task` tells the planner "the plan is wrong" and to
change the items "so it can be met". The `KEEP ... owner:` answer exists only for a diagnosis, at six rounds. The
owner first sees the milestone's history at the park. The rule "Add a requirement only when the owner's words or
the design need it" is in the first-plan section, and the re-plan section does not repeat or apply it.

### C3. The builder is not told to run what the reviewer runs

Record: four of the five milestones failed their first review, and 22 of 26 claims failed overall.

Source: `review-milestone/SKILL.md` says "Run the edge conditions the project settings list for each item's
target, and say which ones you ran". `build-milestone/SKILL.md` and `BUILD_TEMPLATE` never mention edge
conditions. The builder is sent to "How to inspect" in `proofs.md`, which mentions them in half a sentence as one
example of "a few conditions".

Inference: builders proved the items on the ordinary path and reviewers then did the first run under faults.
I can't confirm it, because I can't see what groundWork's settings list as edge conditions, or the builders'
evidence.

### C4. The space a reviewer may fail a milestone on has no edge

Record: after the first round, almost every failed review named a condition no earlier round had tried: a
malformed 200, a well-formed reply with the wrong endpoint, a 500 where a 503 was expected.

Source: 1.6.0 (10 Nov 20:59) added "Hold an open-ended item ... to the range the design names and the inputs the
product really has. A hole that only an input nothing produces can reach is a Suggestion." It sits under "A
milestone that has been reviewed before". All five M3 reviews ran on 1.6.2 with that rule present, and all five
failed, four of them on something new.

Inference: the rule is too weak for a stateful web product, where almost any fault is an input "the product
really has". Whether a given fault matters is the owner's or the planner's call, and the settings' edge-condition
list is where that call is written down. The reviewer skill doesn't treat that list as the limit. I can't tell
from the record whether these findings were against items or outside them.

### C5. The ladder counted rounds and reset them, so the owner heard late

Source: the ladder in force for every milestone review in the record (1.5.4, and the record's "1.6.2") was fixed:
a new builder session at the third failure, a re-plan at the fourth, a park at the fourth after the re-plan. The
record's rows match it exactly in all three long milestones.

Record: all three re-plans were followed by a failed review. Both parks were followed by a pass on the next
review. In SHARED-UI M2 the parking review had passed all six items and failed on one regression.

Source: 1.6.3 replaced this ladder, and no milestone review in the record ran on the new one (the last, M3 r5,
was at 05:11 on 1.6.2). Under 1.7.1 the M2 r8 park would probably not happen, since new findings don't count
toward a re-plan. But the new ladder is longer in the worst case. Reading `escalation`: four repeats send it to a
re-plan, six rounds to a diagnosis, each once, and the counts start again after each. A milestone can fail about
16 reviews before it is parked, where 1.5.4 allowed 8. At this record's rates that is about 370M tokens on one
milestone before the owner is asked anything.

### C6. Time lost outside building and reviewing

- Stalled design re-review, 11:34 to 13:31 (Record). Source: every role's turn has one default limit,
  `--turn-timeout-hours 2.0`. Inference: the session ran to that limit; 1h57 fits. 1.7.1 runs sessions headless
  by default, which removes the desktop cause but leaves the two-hour limit on a job that took 5 to 8 minutes
  every other time.
- Parked overnight for 1h55 (Record). Nothing else in the module could start (Source: later milestones wait).
- Upgrades mid-milestone (Record): 22:09 to 22:58 lost partly to a format gate on a file orchestrate wrote, and
  05:31 to 06:29 to the folder migration, a 13.6M-token planner session, a design re-review and a resume that
  failed because the thread had an active writer. Source: `cmd_migrate` refuses while a session is running, but
  not while a milestone is In Progress or Ready for Review.

### C7. Design review rounds (already fixed)

Record: the first design took five rounds on 1.3.1 and 1.5.0. Source: 1.5.3 (9 Nov 22:14) added "Raise a new Must
Fix only for something the revision broke". Record: every design after that took one or two rounds. No change
proposed.

## Changes, ranked by expected effect on a run like this one

Savings are estimates from this record's rates: about 23M tokens and 25 to 55 minutes per failed round avoided.

### 1. Treat a finding as a family: the builder fixes the cause and tests it, the reviewer sweeps it

Not in 1.7.1.

- `build/scripts/agent_loop.py`, `FINDINGS_TEMPLATE`: for each Must Fix, the builder writes one line on the
  cause, lists the other places that cause reaches (other surfaces, other inputs of the same kind), fixes those
  too, and adds a test that fails without the fix. Where a finding shares a cause with one from an earlier round,
  the test is a table that lists the family's cases.
- `build-milestone/SKILL.md`, "The review": the same, with the reason. The cause lines go in `LOG.md`.
- `review-milestone/SKILL.md`, "What finished looks like": when a Must Fix is found, try its neighbours before
  writing up, and report them as one finding with every member listed. Name the finding for its cause, so the
  name survives into the next round.
- `review-milestone/references/graded-examples.md`: one example of a review that found one stale surface and
  then listed the other four.

Effect on the record: the four families took 19 rounds. If each had closed in two or three, that is 8 to 10 fewer
failed rounds, roughly 180M to 230M tokens and five to seven hours. This is the largest and best-supported
saving, since the pattern shows in both modules.

Cost and risk: longer fix turns and longer reviews. A builder told to fix a family may touch more code and break
more, which is what the test is for. A reviewer sweeping neighbours may wander further from the items, so this
change should ship with change 3, which bounds where a Must Fix can come from.

### 2. At a re-plan, trace the failing requirement to the owner's words, and tell the owner

Partly in 1.7.1, at the diagnosis and the park only. Too late in this record.

- `plan-module/SKILL.md`, "When a milestone keeps failing on the same finding": before changing items, name the
  requirement the failed rounds turn on and where it comes from: the brief, the request, the design, or a review.
  One that came from a review or from the planner is cut to its cheaper reading with an `Assumption:` line, or
  goes to the owner. Allow the `KEEP <MODULE> <milestone>: owner: <why>` ending here as well as at a diagnosis.
- `agent_loop.py`, `replan_task` and `cmd_plan`: carry that instruction, and accept `KEEP ... owner` from a
  re-plan. Add the rounds, hours and tokens spent on the milestone to the task and to the park message, from the
  usage the script already records.
- `build/SKILL.md`, "After a review": on `replan` and `diagnose`, the lead tells the owner in the chat what keeps
  failing, what it has cost and which requirement drives it, and carries on without waiting.

Effect on the record: the owner hears at 18:02 on 10 November that SHARED-UI M2 is failing on reload-free
recovery, about 12 hours before they relaxed it. Up to 220M tokens and six hours sit downstream. I rank it
second because it rests on one chain and on the owner answering.

Cost and risk: more messages to the owner. A planner may cut a requirement the owner did want, which the
`Assumption:` line makes visible but does not prevent.

### 3. One list of conditions that the builder must run and the reviewer is held to

The reviewer half exists in 1.7.1 and is too weak (C4). The builder half is missing (C3).

- `build-milestone/SKILL.md`, "Before you set Ready for Review": run every edge condition the settings list for
  each item's target, and save evidence per condition.
- `agent_loop.py`, `BUILD_TEMPLATE`: one sentence saying so.
- `review-milestone/SKILL.md`, "What reviewers get wrong": move the 1.6.0 rule here so it applies to first
  reviews. A defect reached only under a condition that neither the settings, the item nor the design names is a
  Suggestion, unless it loses data, opens a security hole or breaks something that worked. The review proposes
  the condition for the list.
- `plan-module/SKILL.md` and `references/profile.md`: the planner fills the list for the product in hand, for
  example which failed responses a web app must survive, and treats additions as requirements.

Effect on the record: aimed at the four first-review failures and at the failed-refresh family. My guess is three
to five rounds, which overlaps with change 1.

Cost and risk: this is the change most able to let broken work through. A crash on a malformed 200 would be a
Suggestion if nobody listed malformed responses. The three exceptions and the proposal back to the list are the
guard. Builder sessions get longer.

### 4. Cap a milestone's failed rounds across resets, and report a failed round's cost

A regression in the worst case since 1.6.3 (C5).

- `agent_loop.py`, `escalation` and the record entry: keep a lifetime count of failed rounds that no reset
  clears, and park at a set number (8 matches what this owner lived with), whatever the other counts say.
- `done-when.md`, "When a review fails", `plan-module/SKILL.md`, `build/SKILL.md` and `GLOSSARY.md`: document it.

Effect on the record: none directly, because the old ladder already parked at 8. It stops the new ladder running
to about 16. Cost: a milestone that was converging gets parked, as SHARED-UI M2 was, and waits for the owner.

### 5. Shorter turn limits by role, and a no-activity limit

Partly in 1.7.1 (headless by default).

- `agent_loop.py`: default limits of about 20 minutes for a design review, 45 for a planner and 90 for a
  milestone review (the longest in the record took 58), with one automatic retry in a new session. The script
  already tracks each session's last activity for `loops`, so it can also stop a session silent for 15 minutes.

Effect on the record: about 1h45 of the 11:34 stall. Risk: a slow but healthy review is killed, and the retry
doubles its cost.

### 6. No upgrade or migration while a milestone is In Progress or Ready for Review

Partly in 1.7.1 ("Review claims made before migrate").

- `agent_loop.py`, `cmd_migrate`: refuse, or ask for `--force`, when any milestone is `in_progress` or `claimed`.
- `build/SKILL.md`: upgrade between milestones, and after an upgrade run `check` before resuming a builder.
- `plan-module/references/profile.md`: say that the project's formatter and linter should skip the plans and
  evidence folders, since the script writes files there.

Effect on the record: about an hour and 15M tokens in M3, and part of 22:09 to 22:58. Risk: a fix the run needs
waits for the milestone to end.

### 7. Let other work continue while a milestone is parked

Not in 1.7.1 as far as I read. Later milestones of the module wait, and the record shows nothing else started in
either park. In `build/SKILL.md`, have the lead plan the next module or start an independent one. Effect: up to
2h35. I can't tell whether groundWork had independent work ready.

## Considered and not proposed

- **Rotating builders every two claims.** The record does not show new sessions are cheaper per claim: resumed
  sessions cost 3M to 24M per claim, new ones 2M to 55M. All five new builder sessions started by the ladder
  were followed by a failed review.
- **Reviewing only the failed items on a later round.** Reviews are 36% of tokens, so it is tempting. But
  SHARED-UI M2 r8 caught a regression outside the items on a full pass, and fixes in a family break siblings.
- **A fresh subagent that reviews before the claim.** It may help, but it is a second reviewer at the builder's
  cost. Changes 1 and 3 give the builder the reviewer's method first. Worth a trial after them.
- **A `class` field the script counts.** The existing name match would already count a family as a repeat if
  reviewers named by cause, and a repeat leads to a re-plan, which is the wrong answer to a family the builder
  can fix. Change 1 handles it in the builder's message.

`proposals.md` in this folder, by another session, overlaps with changes 1, 2, 5 and 6. Its sixth proposal, cost
in the record, is already in 1.7.1 since 1.6.0 (`usage` on each run and review, and the `cost` and `report`
commands).

## What I couldn't explain

- **The verdict count.** The opening says 27 verdicts and 5 passes, with four passes closing milestones that had
  failed. The tables show 26 verdicts and 4 passes, three of them on milestones that had failed.
- **The "routing fix" before INTEGRATION-ROLLUPS M2 passed.** The record says the owner reopened M2 "after the
  routing fix landed". It doesn't say who wrote it or whether a review saw it. If the lead or the owner wrote it,
  that is the mechanism change four rounds of builders didn't make.
- **That final review.** It took 58 minutes and 14.8M tokens, against 10 to 13 minutes and about 8M elsewhere.
- **Three gaps with no sessions**: 19:21 to 21:37 and 22:39 to 01:59 on 9 November, and 09:36 to 11:14 on 10
  November, 7h14 in all. The owner being away, a quota wait or a lead that stopped would each fit.
- **Whether the findings were against items or outside them**, and whether the fault conditions were in
  groundWork's settings. Changes 3 and 2 depend on this more than the others do.
- **Whether the families are real.** I grouped them from summaries of a few words. The reviews would show
  whether the pointer-target rounds shared a cause or only a symptom.
- **Builder cost of the first three INTEGRATION-ROLLUPS M2 claims**, which the record says it could not recover,
  and the stalled session's tokens. The totals understate builders by that much.
- **The "ledger" that failed a format gate at 22:09.** I don't know which file it was or which gate.
- **Why SHARED-UI M3 reviews ran on "1.6.2" with the old ladder** when 1.6.3 was committed at 23:07, five minutes
  before M3 started. Probably the installed copy was older than the repository.
- **Model and effort.** Every session ran at high effort. Source: the script's default for builders and
  reviewers is medium. The record can't say whether medium would have changed the rounds.
