# Changes to the orchestrate skills after the groundWork review-completeness record

Written 2026-11-11 against the skills at `6989342` (orchestrate 1.7.1, branch `orchestrate-1.6.4`), from
`delivery-record.md` and `review-completeness.md`. Both were written by agents on another machine, so their facts
are taken as reported. Each claim below is marked **Verified** (read in the skills, the script, git history or the
two evidence files) or **Inferred** (my reading, not tested in a run).

## What the evidence says, and what it doesn't

**Verified, from `review-completeness.md`.**

- 30 defects: 19 already in the code an earlier review passed ("missed"), 11 introduced by a builder's fix.
- 15 of the 19 misses are INTEGRATION-ROLLUPS M2, all present at the first reviewed commit `53d73d23`.
- The reviews judged every item, and several kept going after their first Must Fix. Stopping early is not the
  cause. What they missed were combinations the item didn't name: another route into the same behaviour (Search
  instead of selection, hover as the only trigger), another starting state (a selection held, a view already warm,
  a name changed since load, a two-entry Inspector trail), another reply from the work behind it (a failed Flight,
  a malformed 200, a well-formed reply for the wrong endpoint or scope, a 500 instead of a 503), another thing
  sharing the same place (coincident, reciprocal and dense links on one path, a caption under another group), and
  for the reader, combinations of input features (unresolved GraphQL with store accesses, a non-service message
  party, a wrong-side producer).
- Reviews ran 6m57s to 15m11s. A failed round cost about 40 to 55 minutes of wall time (SHARED-UI M2: nine rounds
  in 8h18; `delivery-record.md`).

**Verified, by reading each row's narrative.** 7 of the 11 introduced defects then survived at least one later
review, which checked the earlier fix and not what the fix touched:

| Defect | Introduced at | Survived reviews | Found |
|---|---|---|---|
| Exact reciprocal calls share a hit target | `ecbabcf7` | IR M2 round 6 | round 7 |
| Search refresh updates shell, leaves canvas | `0f4dda03` | SU M2 round 2 | round 3 |
| Failed Flight reloads the document | `0f4dda03` | SU M2 rounds 2–3 | round 4 |
| Wrong endpoint accepted in replacement | `e6a4c6f7` | SU M2 round 5 | round 6 |
| Warm verification flashes while pending | `e6a4c6f7` | SU M2 round 5 | round 6 |
| Authored scope accepts staged canonical payload | `e6a4c6f7` | SU M2 rounds 5–6 | round 7 |
| Changing Flow loses Inspector history | `03b10574` | SU M2 rounds 3–7 | round 8 |

So 26 of the 30 defects were in front of at least one review that passed over them. Only four (malformed 200,
Journey step blanked, capture 500, Search retarget) were caught by the first review after they appeared. This is
the most useful single fact in the evidence: the review is where most of the cost could have been saved, and the
fixes are a second, smaller source.

**Verified, from git.** The run mostly used 1.5.4, and 1.6.2 for SHARED-UI M3 and M2's last review. Three lines in
force for the whole run are relevant below: the "break the thing into pieces" method in `proofs.md` How to inspect
(since `fc78586`), "Run the edge conditions the profile lists for each item's target" (in 1.5.x
`review-milestone`), and "fix them, re-verify the affected items" in `FINDINGS_TEMPLATE` (since `50a5342`). The
"reviewed before" section, the open-ended-item rule and the "repeats are what send a milestone back" lines arrived
in 1.6.0 and 1.6.3, so they did not shape most of these rows. I flag them as risks for the next run, not causes of
this one.

**One row the changes below don't reach (verified).** IR M2 round 1's own inspection list had "retained selection
after depth changes" on it, and still missed that collapsing a side drops the selected citation. The list named the
situation; the check of it was thin. A better list does not fix that. Only time spent per entry does, which change
2's cost sentence argues for but cannot force.

## The changes, in order

### 1. Teach inspection of stateful behaviour as routes, starting states and replies, taken from the code

**Why this and not just "be thorough" (inferred).** The reviewers were told to be thorough and to write a list,
and did both. The method they were given is a decomposition into parts ("the bow, the stern... For a screen: its
states and controls"), which suits an image or a model, and the only edges named are the device conditions in the
project settings (slow network, empty file). Nothing in the skills tells them that a behaviour reached by several
routes is several behaviours, or that the code, which they are already required to read, lists those routes. The
change is a purpose and a method for finding the list, not a field: no planner enumeration, no new schema.

**File:** `skills/orchestration/plan-module/references/proofs.md`, How to inspect. Insert after the paragraph ending
"For a screen: its states and controls." (line 64):

> A behaviour that keeps state, such as a screen that recovers from a conflict, a selection that survives a change
> of view, or a reader that counts records, needs a different list. Its defects are rarely in one piece seen on its
> own. They are in a combination the item's words don't name: the same result reached from another control (Search
> rather than the link, hover rather than a click), starting from another state (something already selected, a view
> already open, a name changed since the page loaded), with another reply from the work behind it (a refusal, a
> malformed reply, a well-formed reply for the wrong thing, a slow one), or beside something else that shares its
> place (two links on one path, two records with one name). An item that says recovery works is broken if it works
> from one control and not from another. So for each piece, list the routes into it, the states it can start from
> and the replies it can get, and take them from the code rather than from the item: the code shows every caller of
> the mechanism, every trigger, and every kind of reply it handles. You can't try every combination, and don't need
> to. Two routes that run the same code tell you the same thing. Try each place where the code goes a different
> way, and try each route at least once with a reply that fails. In one project, three milestones failed review
> five to eight times. Nineteen of the defects were already in code an earlier review had passed, and those reviews
> had judged every item. Each missed a combination like these.

**Same file, Kinds to start from, User journey row**, change the last column from "Only the easy path was tried" to:

> Only the easy path was tried, or each route was tried only from a fresh start with a reply that succeeded

**File:** `skills/orchestration/review-milestone/SKILL.md`, What reviewers get wrong. Replace lines 58–59, "Run the
edge conditions the project settings list for each item's target, and say which ones you ran." with:

> Run the edge conditions the project settings list for each item's target, and say which ones you ran. Those are
> conditions of the device. In a product that keeps state, most defects reviewers miss are elsewhere: the same
> behaviour reached by another route, from another starting state, or with a failed or wrong reply, as
> [how to inspect](../plan-module/references/proofs.md#how-to-inspect) describes. Find them all in this round. A
> defect you leave is found by the next reviewer, after a builder has spent a session on the ones you did find, and
> in the project that taught this a review took about ten minutes while each extra round cost close to an hour.

**Rows it would have caught (inferred).** All 19 misses are combinations of this kind, and so are the 7 introduced
defects that survived a review: 26 rows. By kind: route (hover-only 409; Search refresh splits shell and canvas;
Search-triggered 503 on People), starting state (warm title after rename; switcher after rename then People;
group switch keeps citation; Inspector trail then Flow change; standalone scope with zero bands or a lone private
store), reply (failed Flight ×2; wrong endpoint; staged canonical; pending verification flash), shared place
(coincident, opposing, reciprocal and dense hit targets; covered Volvo caption; the exact-link list label), input
combinations for the reader (unresolved GraphQL, non-service message, foreign purge endpoint, wrong-side parties,
invalid trigger, payload read). Whether a reviewer would in fact reach each is untested.

**Builder side, at no extra cost (verified).** `build-milestone` "Before you set Ready for Review" sends the builder
to the same How to inspect section, so its own pre-claim check widens too.

**Cost and risk (inferred).** Reviews get longer, plausibly 20 to 30 minutes instead of 10, and use more tokens
(round-one reviews used about 6 to 8M cached input; perhaps half again). One failed round costs a builder session of
2 to 65M cached input plus another review, so the change pays if it saves one round in several milestones. Risk:
reviewers fail milestones on combinations the product can't reach. The existing rule at `review-milestone` lines
123–125 (a hole only an unproduced input reaches is a Suggestion) bounds that, and "take them from the code" ties
the list to routes the product has. Risk: the paragraph is web-UI flavoured; the reader example keeps it general,
and the boat and cloud paragraph above stays for visual work.

### 2. A fix is a change to a mechanism, and the builder checks what else runs through it

**Why not leave it to the builder (inferred).** The builder's instruction after a failed review, in force for the
whole run, is "fix them, re-verify the affected items". That names the findings' items as the scope of checking,
which is the narrow scope the introduced defects escaped from. The 1.6.3 lines add a motive, and it points at the
counter: keep repeats fixed because repeats escalate. Neither says what the next review is for. Telling the builder
the purpose (the next reviewer judges everything again, so a fix that breaks a neighbour costs the same round)
should be enough; a sweep record or a class field would add a list nobody can check (as `critique-of-proposals.md`
also argues).

**File:** `skills/orchestration/build/scripts/agent_loop.py`, `FINDINGS_TEMPLATE` (line 407). Replace

> marks with `repeat` any an earlier round raised: those are what escalate the milestone, so make sure they stay
> fixed. Add them to the plan as work items, fix them, re-verify the affected items, integrate,

with

> marks with `repeat` any an earlier round raised, which means an earlier fix didn't hold. Add them to the plan as
> work items. Fix each at its cause, not at the steps the reviewer gave, and keep the change to what the cause
> needs. The next reviewer judges the whole milestone again, so a fix that makes the reported steps pass and breaks
> something next to them fails it just the same: before you claim, try what else runs through the code you changed,
> from its other routes, states and replies, as the build-milestone skill's How to inspect link describes, and
> re-verify every item that code serves. Then integrate,

**File:** `skills/orchestration/build-milestone/SKILL.md`, The review. Replace lines 112–113 ("The milestone's
`findings`... so make sure those stay fixed.") with:

> The milestone's `findings`, in the done-when file, lists each Must Fix and marks with `repeat` each one an earlier
> round raised, which means an earlier fix didn't hold. Fix each at its cause rather than at the reviewer's steps.
> Then work out what else runs through the code you changed, and try it the way
> [how to inspect](../plan-module/references/proofs.md#how-to-inspect) describes before you set Ready for Review
> again. The next reviewer judges the whole milestone, not your fix, and a fix that breaks its neighbour fails it
> just the same. In one project eleven of thirty defects that failed reviews came from fixes for earlier ones: a
> routing fix that made one of two opposite links open the other, and a refresh fix that wiped the history a later
> step needed.

**Rows (inferred).** The 11 introduced rows, most directly `ecbabcf7` (the routing repair broke reciprocal clicks
that worked through `00213c7c`), `0f4dda03` ×2 (the refresh repair reached Search and Flight failure, untried),
`03b10574` (the repair wiped the Inspector trail) and `fe2e8d33` (the retained list retargets after retry). The
`e6a4c6f7` and `6557e2fd` rows came with a new mechanism, which change 4 addresses better.

**Cost and risk (inferred).** Longer fix sessions. A builder told to fix "at the cause" may refactor more than the
finding needs, which is why the text bounds it to what the cause needs. "Repeat" stays visible, so nothing about
escalation is hidden from the builder; only the motive changes.

### 3. A re-review reads what changed since the last review, and treats it as the riskiest code

**Why (verified).** Seven introduced defects survived a later review (table above). The re-reviews' own records
show the pattern: SHARED-UI M2 round 2 "directly verified both previous fixes" and did not try Search-only recovery
or a failed Flight, both introduced by that very repair. The current section (1.6.0 on) tells a re-reviewer to
start from the earlier review and check each Must Fix, which anchors on the old findings. Nothing tells it which
code is new since it last looked, though the record file holds the commit each review judged
(`milestones.<id>.reviews[].commit`, `agent_loop.py` line 5043).

**File:** `skills/orchestration/review-milestone/SKILL.md`, A milestone that has been reviewed before. Replace
lines 111–112:

> Start from the earlier review, and say whether each Must Fix in it is now fixed. Then judge the items again as
> they are written.

with:

> Start from the earlier review, and say whether each Must Fix in it is now fixed, by its own steps. Then read what
> changed since the commit the earlier review judged, which the record file, `ACCEPTED.json`, keeps under the
> milestone's `reviews`. That change is the newest and least tried code in the milestone, written to make one set of
> steps pass. Work out what else runs through the code it touched, and try those routes, states and replies as
> well. Then judge the items again as they are written, the whole milestone and not only the fixes. In one project,
> seven defects that fixes brought in each survived at least one later review that checked the fix and not what it
> touched; one survived five.

**Rows (verified that they fit; inferred that it would catch them).** The 7 survivor rows. It would not have
prevented any defect, only shortened each one's life by one to five rounds.

**Cost and risk (inferred).** A re-review gets slightly longer. A re-reviewer could narrow onto the diff; the
closing sentence keeps the whole milestone in scope. Optional, one line of script: add `at <commit[:12]>` to each
entry in `history_lines` (line 1585), so the reviewer's task names the commits and it needn't open the record file.
I'd try the text alone first.

### 4. A mechanism that waits on another part says how it fails, most of all after a re-plan

**Why (verified facts, inferred link).** Six of the 11 introduced defects came with the JSON replacement that the
SHARED-UI re-plans brought in: four at `e6a4c6f7` (malformed nested facts, wrong endpoint, pending flash, staged
canonical payload) and two at `6557e2fd` when it was extended (step blanked, 500 for 503). The re-plan's design
review was approved two minutes after the plan landed (18:09 to 18:11, `delivery-record.md`). `plan-module` asks
that each mechanism can produce the behaviour "across the whole range", and the design review looks for
"mechanisms nobody has shown can produce their behaviour"; neither mentions how a mechanism fails. Whether those
six were design gaps or build gaps I can't tell from the evidence: the design text isn't here.

**File:** `skills/orchestration/plan-module/SKILL.md`, The design. After "A reviewer will try the edge of any range
the design leaves open." (line 148), add:

> The range includes failure. A mechanism that waits on another part, such as a server, a file or a device, says
> what is shown while it waits, and what it does when the answer is refused, malformed, or well formed but for
> something else. A re-plan's new mechanism needs this most, because it was chosen to get past failures and nobody
> has run it yet. In one project a re-plan replaced a failing refresh with a JSON replacement, and its first build
> accepted a reply for the wrong endpoint, crashed on a malformed one, and showed stale data while it waited.

**File:** `skills/orchestration/review-milestone/SKILL.md`, Reviewing a design, line 136. Change "and mechanisms
nobody has shown can produce their behaviour." to:

> and mechanisms nobody has shown can produce their behaviour, or that don't say what happens when what they wait
> on fails.

**Rows (inferred).** The 6 rows above, if the design's sentence reached the builder's implementation.

**Cost and risk (inferred).** A few more lines per design. It brushes against "leave details to the builder";
failure behaviour is behaviour the user sees, so it belongs in the design, but a planner could overdo it and
script error handling. One more thing a design review can fail on, against the 1.5.3 work to make design reviews
converge; the line is a single question, not a checklist.

### 5. Stop teaching that a late corner is the reviewer's fault

**Why (verified text; inferred effect).** Two 1.6.x lines explain the pattern in this run, findings one corner at a
time, as reviewer overreach:

- `review-milestone` lines 124–125: "Without this rule each review finds one more corner, and a sound milestone
  fails round after round and goes back to a planner."
- `plan-module` diagnosis, lines 265–266: `reviewer` "is for findings that go beyond the items, and the next
  reviewer is told to judge the items as written" (and `agent_loop.py` line 1581 sends exactly that).

Every groundWork finding was reachable through the product's own routes, so none was overreach, yet a diagnosing
planner at round six of a run like SHARED-UI M2 could read "findings beyond the items" and narrow the next review.
That is the opposite of what the evidence asks for. The rule itself (an unreachable input is a Suggestion) is
right; the reason attached to it, and the diagnosis category, need to say where the line is.

**File:** `skills/orchestration/review-milestone/SKILL.md`, replace the last sentence of line 124–125 ("Without this
rule each review finds one more corner, and a sound milestone fails round after round and goes back to a
planner.") with:

> Without this rule reviews fail sound milestones on inputs nobody sends. A corner the product's own routes reach is
> different: it is within the item, and the way to stop a milestone failing one such corner per round is to find
> them all in the first round.

**File:** `skills/orchestration/plan-module/SKILL.md`, the `reviewer` sentence at lines 265–266. Change "`reviewer` is
for findings that go beyond the items" to:

> `reviewer` is for findings that need inputs the product never produces, or requirements no item states. A finding
> reached through a route, state or reply the product really has is within its item however late it was found, and
> points at the earlier reviews or the builder, not the latest reviewer.

**Rows.** None directly; these lines weren't in force for most of the run. It removes a push toward narrow reviews
that would act on exactly this pattern next time.

**Cost.** Wording only.

### 6. Optional: one starting graded example of the same behaviour reached another way

**Why (verified).** `review-milestone` calls graded examples "the best guide to how strict to be", and the five
starting examples (`references/graded-examples.md`) include "works on the easy path only", but all are static
artefacts or a single path. Change 1 says the principle; an example shows the grain. I'd add it only if a replay
(below) shows change 1 alone doesn't move reviewers.

**File:** `skills/orchestration/review-milestone/references/graded-examples.md`, append:

> ## The same behaviour, reached another way
>
> The milestone: a view refreshes itself when its data changes under it, and keeps what the reader had open. The
> builder's recording showed a conflict caught after selecting an item, a successful refresh, and the selection
> kept.
>
> The reviewer read the refresh code and found three things that start it (selecting an item, Search, and hovering
> a link) and three replies it handles (success, a refused refresh, and a reply that arrives late). Its list crossed
> each trigger with a failure at least once. Hover started no refresh at all, and a refused refresh through Search
> reloaded the whole page and closed Search. The item got a Fail with both sequences. The selection case passed.
>
> Why it is here: the item was judged true on the route the builder showed. An item about a behaviour holds on every
> route the product has into it.

**Rows.** The hover-only 409 and both failed-Flight rows are its model. **Cost.** About 150 words in a file every
reviewer reads.

## Considered and not recommended

- **The planner lists routes, states and replies beside each item** (`proposals-2.md` 1). Verified:
  `done-when.md` "What makes a good item" records items growing to a median of 135 words on an engine project and
  being rewritten up to four times before any review failed. Inferred: the planner writes before the code exists, so
  it can't see the branches that decide which combinations matter, and a reviewer handed a list tends to stop at it.
  The reviewer and builder can read the routes off the code; change 1 tells them to.
- **A record of which combinations were tried, as a field.** Verified: the review already keeps its inspection
  lists (`review-milestone` line 87), and `review-completeness.md` used them to tell an omitted situation from a
  thin check. At the grain change 1 asks for, those lists already are that record.
- **A regression test for each finding.** Inferred from the table: no introduced row re-broke an earlier finding's
  own steps (`ecbabcf7` broke exact-depth reciprocal links; the earlier finding was collapsed). It guards against
  repeats, which weren't the problem here.
- **A minimum review time or a coverage count enforced by the script.** Review length is a symptom; a timer is met
  by waiting.

## How to check these before shipping (inferred, not done)

The groundWork lead still has throwaway worktrees at the historical commits. The cheapest test of changes 1 and 5
is to start one reviewer on Codex with the changed skills against INTEGRATION-ROLLUPS M2's first claim (`53d73d23`)
and one against SHARED-UI M2's round-2 claim (`0f4dda03`, as I read the table; for change 3 as well), and count how many of the known
rows each finds: 15 and 3 respectively are available. One or two reviews each, roughly 10 to 20M tokens, against a
known answer. If change 1 alone moves the count little, add change 6 and run it again.
