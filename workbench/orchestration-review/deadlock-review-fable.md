# Review of the review-failure escalation proposal

Reviewer: Claude Fable 5.1, 10 November 2026. Read against `skills/orchestration/build/scripts/agent_loop.py` on
branch `orchestrate-polish` (6188 lines), the done-when reference, the build and review-milestone skills, and
`tests/orchestration/test_agent_loop.py`. The other project's files aren't here, so everything about the case
itself is reasoning from the quoted description. Line numbers are from the file as it stands now.

## Verdict

Build it, with four changes. The proposal fixes the case's actual deadlock: under it, the eighth review (six items
pass, one new regression outside them) would not have parked M2. The script already holds the data to tell an
item-level repeat from a new failure at the moment it lands a review, so point 1 is cheap. But as written:

1. **"Repeat" is the wrong unit in both directions.** Comparing against the previous review only lets two findings
   alternate forever (A, B, A, B is never a repeat), and comparing by item id makes every distinct defect under one
   broad item a repeat, which is probably what the case's rounds 1 to 4 and 5 to 8 looked like, so rule 1 may not
   have changed the ladder for them at all. Compare each Must Fix against every round since the last rewrite, and
   let the unit be the named finding (point 2) for items as well as for things outside them.
2. **The backstop counts the wrong thing.** A raw total of eight fires at exactly the review where the case needed one
   more builder round, and it never resets, so a milestone that is unparked re-parks on its next fail. Count rounds
   since the last rewrite or owner decision, and let the planner answer "the plan is fine" without that being a
   dead end.
3. **Point 2 needs a structured field, not a name in the prose.** The script reads nothing from the review file but
   its last line, and the record keeps no per-item or per-finding data per round. A reviewer-owned list in the
   done-when file, copied into the record's `reviews` entry, gives points 1, 3 and 4 the data they need.
4. **Move `fails` to the script.** Today the reviewer increments it and the script checks the arithmetic. Once the
   count depends on earlier rounds, the reviewer can't compute it, and shouldn't.

Setting the judge aside is right. The planner at the re-plan step is already that judge, badly briefed; brief it
better.

## 1. Does it fix the case?

Reasoning from the description. The case has three deadlocks, and the proposal addresses one and a half.

- **The park at review 8.** Six planned items passed; a regression outside them failed the milestone; that was the
  fourth fail after the rewrite, so `escalation(4, 1)` returned `park` (line 961) and the loop set the state
  (lines 4603 to 4604). Under rule 1 that review's failures are all new, so `fails` stays at 3 and the builder
  resumes. Under rule 2 the regression gets a name; the next review finds it fixed and passes. Fixed.
- **Rounds 5 to 8 "each consumed a slot".** Only fixed if those gaps were in different items. The description says
  the acceptance scope "was still broad", and lists five gaps (nested response validation, endpoint identity,
  evidence shown while verification pending, authored scope, hover recovery). If three of those fell under one
  broad item, rule 1 counts them as repeats and the ladder runs as it does today. I can't tell from here. This is
  why the unit of repetition matters (section 3).
- **Rounds 1 to 4: "fixing one path exposed another".** Same question. If "recovery" was one item, the four rounds
  were repeats under rule 1 and the re-plan at review 4 happens as before. The description says that re-plan was
  the right call (it found a design problem and fixed the transport), so this isn't a loss, but it means the
  proposal's benefit in the case is narrower than it looks: it saves the park, not the four rounds before the
  rewrite.
- **M3 to M5 waiting on M2.** Not addressed, and it is the part of the case that cost the most wall-clock. Milestones
  in a module run in order by construction (`validate`, lines 866 to 870, rejects `needs` on a later milestone of
  the same module for the same reason). The owner's only ways past a parked M2 are `unpark`, `accept` or `scope`
  (lines 6004 to 6023). That's acceptable as long as the park message (point 4) makes `accept` an obvious one-word
  answer when the only thing left is a Suggestion-sized regression. See section 6.
- **Reopening needed the owner at a terminal.** Already fixed, per the case; `owner_guard` (lines 5897 to 5908)
  refuses `owner` inside a loop session but the lead runs it from chat.

## 2. Can the script tell a repeat from a new failure with the data it records today?

Confirmed in the code: **yes for items, at the moment a review lands; no for findings outside items; and no for
either from the record afterwards.**

- At review time the script loads `before_doc`, the done-when file at the claim commit (line 4436), and `after`,
  the file the reviewer left (lines 4523 to 4529). `after` has this round's `verdict` per item. `before_doc` still
  has the previous round's, because `reset_proof(target, only_failed=True)` clears only `status` and `evidence`
  and leaves `verdict` and `review` alone (lines 964 to 973), and the builder can't touch them: `BUILDER_FIELDS`
  is `{status, evidence}` (line 978) and `delta_problems` stops the run if a builder changes anything else
  (lines 1026 to 1030). So in `change()` at line 4596, `{i["id"]: i["verdict"] for i in before_doc's milestone}`
  against the same for `reviewed` is the item-level repeat test, with no new data.
- One wrinkle: when every item passed and the fail was outside them, `reset_proof` resets all items' `status` but
  keeps their `verdict: pass` (line 968's condition is false, so `items` stays the full list). So the previous round
  reads as "all pass" and the next round's item failures are all new, which is the intended answer.
- The record's `reviews` entries hold `verdict`, `commit`, `review`, launch fields and `at` (lines 4614 to 4615):
  no per-item verdicts, no findings. `review_rounds` (lines 1329 to 1339) returns only the review file paths since
  `authorised.at`. So anything that needs more than the previous round (section 3's "any round since the rewrite",
  the backstop, the owner message) needs a new field in that entry. The git history of the done-when file does
  hold every round's verdicts, since each review lands as its own loop commit (line 4622), but reading it back
  is the wrong tool when adding `"items": {id: verdict}` to the entry at line 4614 is one line.
- Findings outside the items exist only in the review prose and in the last line's count. `REVIEW_LINE`
  (line 4378) captures the verdict and the milestone id, not the `<n> outside the items` count, and nothing else
  parses the review file. So point 2 is new structure, not a reading of what's there.
- `fails` is written by the reviewer and checked by the script: `REVIEWER_FIELDS` includes `fails` (line 979) and
  line 1038 rejects a fail that doesn't add exactly 1. Under the proposal the reviewer can't know whether to add 1.
  Set it in the script in `change()` (line 4597 already does `target.update(state=..., fails=...)` from the
  reviewer's copy) and relax line 1038 to "a review doesn't change `fails`", or drop `fails` from the reviewer's
  fields entirely. Everything downstream reads `fails` from the file (`escalation` at 954, `next_step` at 1208,
  `cmd_next` at 5057, `settle_replans` at 1391), so if `fails` becomes "repeat fails" nothing else moves.

## 3. Can a reviewer or builder game the repeat rule?

Reasoning from the rules, checked against who may write what.

**Builder.** It can't write verdicts or findings, so it can't mark anything "new". What it can do is choose what to
fix, and rule 1 rewards one pattern: fix the named finding in a way that breaks a different item. Each round then
fails on something new. With "previous review only" as the comparison, two findings can alternate indefinitely
(round n fails A, round n+1 fixes A and fails B, round n+2 fixes B and re-breaks A: A is "new" because round n+1
didn't fail it). Compare against every round since the last rewrite and the oscillation is a repeat on round n+2.
Whack-a-mole with always-new breakage is what the backstop is for. Neither needs intent; a builder that patches
symptoms produces both by accident.

**Reviewer.** A reviewer has no stake in the count, but the rule is sensitive to its habits in two ways:

- Same item, different defect, counts as a repeat under rule 1. A strict reviewer that keeps finding new corners of
  one broad item escalates the builder for the reviewer's thoroughness. `done-when.md` lines 211 to 213 already
  say to keep items narrow for exactly this reason, and `review-milestone` lines 97 to 99 already tell the
  reviewer to hold open-ended items to the design's range; rule 1 makes both load-bearing.
- Different name, same defect, counts as new under rule 2. The reviewer is a fresh session each round, told to
  start from the earlier review (`review-milestone` line 94), so it can copy names, but nothing makes it. A
  renamed finding costs the builder nothing and the project one more round; a wrongly reused name escalates. Both
  are sloppiness, not gaming, and the cure is the same: the previous round's names are in the done-when file in
  front of the reviewer (section 7), and the skill says to reuse a name when the defect is the same and to say so.

Neither agent can forge the count once the script computes it from the record.

## 4. Is the backstop the right shape?

Half right. "Endless new findings" is real, the case shows it, and sending every review to a planner (which
`replan_task` already does, lines 1342 to 1350, listing each kept round) is the right destination. Three things are
wrong with the shape:

- **A raw total.** Eight total reviews is exactly where the case was when the ninth would have passed. Under the
  proposal the park becomes a second re-plan at the same point: better than parking, but still a planner turn,
  a definitions change and a re-proof of the items, when the state was "one regression, fix in hand". Count rounds
  since the last rewrite (that's what `review_rounds` already filters on, via `authorised.at`, line 1337), and set
  the backstop to fire later than the repeat ladder's re-plan would.
- **No reset.** `owner unpark` sets `fails` to 0 (line 6023) and nothing else; `authorised` doesn't change. A total
  that never resets re-parks an unparked milestone on its first fail. Whatever counter drives the backstop has to
  reset where `fails` does: `settle_replans` (line 1395), `unpark` (line 6023), and `owner scope` on a changed
  milestone (lines 5976 to 5980).
- **"Narrow its checks" presumes the fault is the plan.** The planner's current brief for a re-plan says "the plan is
  wrong ... find what keeps failing and change the definitions" (line 1348), and the plan-module skill (lines 196
  to 208) offers three diagnoses, all of them plan faults. If the planner concludes the plan is fine and the builder
  is the problem, it has no move: `settle_replans` only settles a milestone whose definitions changed (lines 1393
  to 1394), and `next_step` keeps saying `replan_owed` (lines 1208 to 1210) until they do. That is a smaller
  deadlock sitting under the proposed one. Let the backstop's planner answer with one of four words (plan too
  broad, builder, reviewer, owner decision) and let "builder" or "reviewer" land as a decision that resets the
  round count and resumes, once; the second time through, park.

With those three, the backstop is one more ladder step rather than a separate mechanism: `fails` (repeats) climbs
the ladder as now, `rounds` (every fail since the rewrite) trips a planner look at, say, six, and the two meet at
park.

## 5. Is setting the judge aside right?

Yes. The judge's four classes (builder, reviewer, impossible check, owner decision) are the right questions, but a
new agent kind isn't the place to ask them. The planner at the re-plan step already reads every round and decides
what's wrong; its brief just doesn't offer "builder" or "reviewer" as answers, so it changes definitions whether or
not they were the problem. Put the four classes in the planner's backstop brief and in the lead's park message,
and the judge's job is done by agents that already exist, on hosts the profile already picks (`Review host:
other` already sends a design review to the host that didn't write the plan, `design_review_host`, lines 3248
to 3256; the same rule can pick the backstop's planner). A judge on a third host would also be a third
session's worth of quota per deadlock, and the case's project burned enough on nine reviews.

The one thing a judge would add that the planner can't is independence from the plan it wrote. If that matters,
the existing lever is the profile's `Review host` for the backstop's planner turn, not a new kind of agent.

## 6. Point 4: the park message

Right, and the cheapest of the four to build once the record holds per-round data. Today the park `ask` is one
sentence with the count (lines 1418 to 1423), and `report` says "parked after N failed reviews" (line 5454). The
owner can't answer "accept" in one word without knowing that the last round's only Must Fix was a regression the
builder has since fixed. Two things to pin down:

- The script can draft the factual half (each round: which items and which named findings failed, and which of
  those were repeats) from the record. The recommendation is the lead's, as the proposal says; keep it out of the
  script so the owner can see which half is fact.
- Make `accept` and `scope` first-class answers in the ask, not an afterthought in `why`. In the case, `accept` plus
  a new item on M3 for the regression would have let M3 to M5 move the same day.

## 7. What I'd do differently

Concretely, this is the design I'd build, which is the proposal with the four changes applied.

1. **One reviewer-owned list, `findings`, on the milestone in the done-when file.** Each entry: `name` (short, stable
   across rounds), `item` (an item id, or absent for one outside the items), `repeat` (true when the reviewer says
   it is the defect an earlier round named), `fixed` (true when the earlier round's finding is now fixed and this
   entry closes it). Validate it in `validate` (line 809), add it to `REVIEWER_FIELDS` (line 979), require every
   non-pass item to have at least one finding naming it (a check beside line 4532), and copy it into the `reviews`
   entry at line 4614 alongside `items: {id: verdict}`. The last line's counts then come from the list rather than
   from the reviewer's arithmetic.
2. **Repeat means: a finding whose `name` matches, or whose `item` has failed before, in any round since the rewrite,
   unless the reviewer marked it `repeat: false` with a reason.** The item-id fallback catches a renamed finding;
   the reviewer's explicit "different defect under the same item" stops thoroughness escalating the builder.
   Script decides, reviewer informs.
3. **`fails` counts rounds with at least one repeat; `rounds` counts every failed review. Both reset together** at
   the three places `fails` resets now. The ladder on `fails` stays as it is (same, same, fresh, replan, +4 park).
   `rounds` at 6 since the last rewrite sends the milestone to a planner with every round and a four-way question;
   the planner either changes definitions (settled as a re-plan, as now) or answers builder, reviewer or owner, and
   the script records that, resets `rounds`, and resumes the builder (fresh session, since the old one is probably
   the problem) or asks the owner. A second backstop on the same milestone parks it.
4. **Step 3 of the ladder on rounds, not only on repeats.** Rule 1 lets a builder sit at `fails` 2 for six rounds in
   one session. The fresh-session step exists partly because context fills; trigger it at `rounds` 3 as well.
5. **The park and backstop messages carry the per-round table** from the record, and the ask lists `unpark`,
   `accept`, `scope` as equals.

Smaller things to catch while building, all confirmed in the code:

- `FINDINGS_TEMPLATE` (line 364) tells the builder every blocking finding counts; it should now say which were
  repeats, since those are what move the ladder.
- The done-when reference's escalation table (lines 199 to 204), the build skill's ladder table (lines 305 to 310)
  and the status table's "fails at 4" (line 133) all state the count as "failed reviews"; they'll need to say
  "repeated failures" and name the backstop, and `plan-module` lines 196 to 213 need the four-way question.
- `test_escalation_ladder` (test line 67) and `test_the_loop_parks_a_milestone_when_the_ladder_runs_out`
  (test line 1027) pin the current arithmetic; the parking test writes `fails: 3, replans: 1` then one fail, which
  under the new rule must be a repeat to park. The 273 tests pass as the branch stands (`python3 -m unittest
  discover -s tests/orchestration`, run during this review).
- `owner scope` on a milestone keeps `reviews` but restamps `authorised` (lines 5986 to 5987), so `review_rounds`
  and anything built on it already treat a scope as a reset. Good; keep the new counters on the same stamp.
