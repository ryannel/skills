# Critique of the second draft of proposals

Written 2026-11-11 against `proposals-2.md`, `review-completeness.md` and `delivery-record.md` (both written by
other agents, read here as data), and the orchestrate skills at `6989342` on branch `orchestrate-1.6.4`. File and
line references are to `skills/orchestration/` unless they name another file.

**Verified** means I read it in the skill text, the git history, or the rows of the two evidence files. **Inferred**
means my reading, not checked against a run. The groundWork review files themselves are on another machine, so
everything about what the reviewers did comes from `review-completeness.md`'s quotes and summaries, not from the
reviews.

## The verdict

| # | Change | Verdict | Lightest version |
|---|---|---|---|
| 1 | Planner lists routes, states and outcomes beside each item | **Drop.** Replace it with one example sentence in `proofs.md` | The pieces of a shared mechanism: each way in, each way it ends, every place that shows the result |
| 2 | Builder tests every combination, re-tests what a fix touched, keeps old reproductions as checks | **Replace with one sentence.** Keep only the part about re-testing what a fix touched | One sentence in `build-milestone`, plus the "look for the same cause elsewhere" line the first critique proposed |
| 3 | Reviewer covers the whole list, adds to it, records the combinations tried | **Drop.** It already exists | Nothing. The `proofs.md` sentence from change 1 reaches the reviewer too |
| 4 | A replan lists how its new mechanism can fail, and the design review checks the list is there | **Replace with one sentence.** Drop the design-review check | One sentence in `plan-module`'s replan section |

All four are aimed at a real pattern. Three of them answer it with a list that a planner writes before the code
exists and that the builder and reviewer then have to work through. The evidence says the agents mostly had the
reason and had a list already. What they lacked was a sharper idea of where defects collect in software that has
state, and, for one class, a check that would hold once the class had shown up twice.

## Verified: what already exists

The pieces the proposals build are already in the skills, apart from the "shared mechanism" idea:

- **Inspection lists, written before looking and kept in the review.** `review-milestone/SKILL.md` lines 69–71;
  `plan-module/references/proofs.md` lines 58–76. Line 75–76 says to keep the list "so anyone can see what was
  looked at and what wasn't". `proofs.md` line 58 says the method "applies to a builder checking its own work
  before Ready for Review, and to a reviewer".
- **Edges and the easy path.** `review-milestone` lines 48–49 ("tries the obvious paths and skips the edges") and
  59–62 (run the target's edge conditions; easy path only means `cant_tell`). The same wording, in older words, was
  in 1.5.4, the version most of the run used (`git show f3cc653:skills/orchestration/review-milestone/SKILL.md`,
  lines 25–26 and 35–36).
- **States of a screen.** `proofs.md` line 52, the User journey kind: "empty, loading, error and resize for a
  screen", and "too weak if only the easy path was tried". Line 64: "For a screen: its states and controls."
- **Builder judges as a reviewer will.** `build-milestone/SKILL.md` lines 88–89.
- **Regressions are Must Fixes.** `review-milestone` lines 52–53: a defect "that breaks something that worked
  before" is a Must Fix even outside the items.
- **Earlier findings are re-checked every round.** `review-milestone` line 111: "say whether each Must Fix in it is
  now fixed". The script marks repeats (`done-when.md` lines 219–223).
- **Tests for a fault coming back.** `build-milestone` line 80, but only for "an ordinary fix that has no plan".
  `plan-module` lines 211–213: "A finding that came up twice becomes a command ... or an item's `check`", but only
  when a planner next plans or rewrites the module.
- **Mechanisms checked across their range.** `plan-module` lines 145–148; the design reviewer looks for
  "mechanisms nobody has shown can produce their behaviour" (`review-milestone` lines 135–136). The replan section
  (`plan-module` lines 241–243) says "Redesign it" and nothing about the new mechanism's own failures.
- **Against long, procedural items.** `done-when.md` lines 350–354: "Say what will be observed, and leave it to the
  builder to arrange the observation"; an engine project's items reached a median of 135 words and were rewritten
  up to four times. `plan-module` lines 162–165: "reviewers fail the build on every requirement you add".
- **Against design reviews that never converge.** `review-milestone` lines 149–152.

## Verified: what the 30 rows are

My grouping of the 30 rows in `review-completeness.md` (the grouping is mine; the rows are theirs). M is a defect
an earlier review missed, I is one a fix introduced.

| Group | Rows | Count |
|---|---|---|
| **Recovery: a second way in or a bad ending.** A refresh reached through Search or hover, a failed or held response | SU-M2 r3 Search shell (I), r4 failed Flight (I), r6 warm flash while pending (I), r7 hover-only 409 (M); SU-M3 r3 failed People Flight (M), r4 Journey step blank (I), r4 churn returns 500 (I) | 7 |
| **A response that is well-formed but wrong** | SU-M2 r5 malformed nested facts (I), r6 wrong endpoint (I), r7 staged canonical payload (I) | 3 |
| **One instance out of many.** Each link clickable on its own; each view showing the new name | IR-M2 r4 Volvo caption, r5 GET/PUT share path, r6 opposing collapsed, r7 exact reciprocal (I), r8 dense lane; r2 exact-link list omits operation; SU-M2 r2 title stale; SU-M3 r2 switcher stale | 8 |
| **Inventory: the reader classifies an input wrongly** | IR-M2 r2 unresolved GraphQL, non-service message, cache purge; r3 wrong-side producer/consumer; r4 invalid trigger; r5 payload read | 6 |
| **Selection or scope at an edge** | IR-M2 r2 collapse loses selection, private store alone; r3 stale citation on group switch, zero matching bands | 4 |
| **A fix broke a neighbour that worked** (not counted above) | SU-M2 r8 Inspector history (I); SU-M3 r5 Search retargets after retry (I) | 2 |

Also from the evidence, verified as quoted there:

- IR-M2 round 1's inspection list "explicitly included 'retained selection after depth changes'", and the collapse
  defect was "within the planned situation". So that row was on a list and missed anyway.
- No review is described as stopping at its first Must Fix; "most gave a judgement against every acceptance item".
- Reviews ran 7–15 minutes (`review-completeness.md`); they used 4.5M–23.3M cached input tokens each, mostly 6–9M
  (`delivery-record.md`). Builder sessions reached 35–69M cached.
- The IR design took five review rounds (`delivery-record.md`, 9 November evening).
- SU-M3's replan kept mounted-state preservation; the owner relaxed it about three hours later (delivery record,
  M3 closing paragraph).
- No row is the return of an earlier finding's exact reproduction. The nearest, IR-M2 r7, failed at exact depth
  after r6's finding was at collapsed depth, and `review-completeness.md` classes it as introduced by the routing
  repair.

## 1. The planner names the routes, states and outcomes beside each item: drop

**What the skills say (verified).** The "states of a screen" and "only the easy path" ideas are in `proofs.md`
line 52 and line 64, and in `review-milestone` lines 48–49 and 59–62. `done-when.md` lines 350–354 tells the
planner not to script the observation inside an item, which is what this change asks for.

**Lacked the reason, or had it and didn't act? (mostly inferred).** Both, depending on the group.

- Recovery and well-formed-but-wrong rows (10): the reviewers knew to try edges and did run fault injection (SU-M2
  round 5 "did plan a warm trace fault"). What they lacked was the idea that the defects collect at a *second way
  into* the same mechanism and at its *non-success endings*. That is a missing idea, not a missing procedure, and
  an example fixes it.
- Instance rows (8): routes, states and outcomes don't describe them at all. "Links are selectable" was exercised;
  what was missing was "each link, including ones drawn on top of each other". A planner's list would not name the
  dense same-direction lane, because that arose from the routing the builder chose (inferred).
- Inventory rows (6): these are input kinds for a reader, not routes or screen states. The proposal's frame
  doesn't reach them.
- Selection and scope rows (4): one was on the reviewer's list and was still missed. A longer list can't fix that.

**The lightest version.** Add one sentence to the examples of pieces in `proofs.md` "How to inspect", after line
64 ("For a screen: its states and controls."):

> For a mechanism that several parts of the product use, such as a refresh or a router, the pieces are each way
> into it (a click, Search, hover, a bookmark), each way it can end (success, failure, a held response, a
> response that is well-formed but wrong), and every place that shows its result. "Each" means each: links are
> selectable only if every link can be picked on its own, including links drawn over one another. In one project
> most of the defects that reviews missed were a second way in, a failed ending, or one view out of several still
> showing the old data.

Because `proofs.md` line 58 already applies this section to builders and reviewers, this one sentence reaches
both. **Rows it would plausibly have caught (inferred):** the 7 recovery rows, the 3 well-formed-but-wrong rows,
and the 8 instance rows: 18 of 30, the same ground the proposal targets plus the instance group it misses.

**What the heavy version would cost (inferred unless marked).**

- Item length and rewrites. Every item gains a matrix the planner writes before any code exists, against the
  rule at `done-when.md` lines 350–354 and the 135-word failure it cites (verified text).
- New requirements. Each listed combination becomes something a reviewer must fail on (`plan-module` lines
  162–165, verified). The record already shows one requirement the owner later relaxed (SU-M3 mounted state,
  verified), and a planner listing "malformed data" for every item makes many more.
- Design rounds. An approved design is approved word for word, so every list change goes back for review. The IR
  design already took five rounds (verified).
- Size. SU-M2's recovery alone has at least four ways in (navigation, Search, hover, evidence selection), five
  endings (success, 409 then success, 409 then 503, malformed 200, wrong-endpoint 200) and five views (standalone,
  People, Journey, Interfaces, switcher): about 100 combinations for one item. Nobody runs 100 browser
  combinations in a 10-minute review, so the list gets sampled by judgement, which is what happens now, except the
  sampling is hidden behind a list that looks complete.

## 2. The builder tests every combination, re-tests what a fix touched, and keeps old reproductions: replace with one sentence

The proposal has three parts, and they fare differently.

**"Tests every combination on that list."** It depends on change 1's list, and the existing step already does the
rest: `build-milestone` lines 88–89, with `proofs.md` line 58. With the `proofs.md` sentence above, the builder's
self-check gets the same idea at no extra cost. Drop.

**"Keeps each earlier failed review's reproduction as a check."** Verified from the rows: none of the 30 is the
return of an earlier finding's reproduction, so this catches 0 rows of this evidence. The reviewer re-checks every
earlier Must Fix anyway (`review-milestone` line 111). Adding a test when you fix something is a good habit
`build-milestone` line 80 already states. Drop as a new rule.

**"Tests everything that uses a mechanism a fix changed."** This is the part the evidence supports. Eleven of the 30
rows were introduced by repairs (verified count from `review-completeness.md`). Four of those broke a neighbour that
worked before: IR-M2 r7 reciprocal, SU-M2 r8 Inspector history, SU-M3 r4 Journey step, SU-M3 r5 Search retarget.
The other seven are a new path's own endings, which the `proofs.md` sentence covers.

Did the builder have the reason? Not as written. The skills tell the *reviewer* that a regression is a Must Fix
(`review-milestone` 52–53), and tell the *builder* to judge the items. Nothing tells the builder that a fix to a
shared mechanism is where regressions come from. Whether the builders already re-tested neighbours can't be seen:
builder logs aren't in the evidence. So: lacked the reason, as far as the skills go.

**The lightest version.** One sentence in `build-milestone` "Before you set Ready for Review", after line 91:

> When a fix changes something other parts of the product rely on, such as routing, a shared store or how a
> refresh recovers, try those other parts again too. In one project, fixes caused 11 of the 30 Must Fixes that
> later reviews found, mostly by breaking something nearby that had worked.

And the first critique's line for `FINDINGS_TEMPLATE` (agent_loop.py line 407), which isn't on the branch yet
(verified by grep): before claiming, look for the same cause wherever else it could occur, and add a test that
would catch it, as `build-milestone` line 80 asks for ordinary fixes. This is the one place the evidence shows the
agents *had* the reason and it still didn't act, because the rule sat in the wrong place. Shared pointer targets
came up in IR-M2 rounds 4 and 5. `plan-module` lines 211–213 would turn that into a check, but only when a planner
next plans the module, and no planner ran between rounds 4 and 8. A builder who added "every rendered link has a
point that selects it" after round 5 would plausibly have caught rounds 6, 7 and 8 (inferred). That is the one
check-shaped change I'd keep, and it uses the existing test command, not a new field.

**What the heavy version would cost (inferred).** Builder sessions were already the largest cost: 35–69M cached
tokens, and 80–85% of wall-clock time (the first critique's figure from the record). Running every combination
before each claim multiplies the builder's browser time by the size of change 1's list, on every claim, including
the ones that would pass. A builder that writes "tested all 40 combinations" also gives the reviewer something to
lean on, against `review-milestone` lines 43–44, which tells it to form its own view before reading the builder's
evidence.

## 3. The reviewer covers the whole list, adds what the planner missed, and records what it tried: drop

**What the skills say (verified).** The reviewer already writes its own list before looking and keeps it in the
review (`review-milestone` lines 69–71, 87; `proofs.md` lines 75–76). Adding what the planner missed is the
reviewer's existing job: problems outside the items are reported (`review-milestone` lines 52–55, 85). Recording
what was tried is how `review-completeness.md` itself could tell, for each miss, whether it was on the list. That
part of the proposal already exists and already worked.

**Lacked the reason, or had it?** Had it. Every review in the evidence wrote a list, and judged every item. IR-M2
round 1 had the collapse case on its list and missed it (verified quote). The gap was what went on the lists, which
the `proofs.md` sentence addresses.

**The lightest version.** Nothing beyond the `proofs.md` sentence in change 1.

**What the heavy version would cost (inferred).** "Covers the whole list" turns the reviewer from someone hunting
for defects into someone ticking off a planner's matrix. A ticked matrix reads as thorough in the review file and
in the owner's status page, and IR round 1 shows a defect on the list can still be missed. Time spent on listed
cases that pass comes out of the 7–15 minutes a review has for cases nobody listed, which is where the 19 misses
were. It would also give a fresh ground for disputes between rounds: "the planner's list was covered" versus a new
finding outside it, which `review-milestone` lines 123–125 already struggles to bound.

## 4. A replan lists how the new mechanism can fail, and the design review checks the list: replace with one sentence

**What the skills say (verified).** `plan-module` lines 145–148 (check a mechanism across its whole range) and
lines 241–243 ("used a mechanism that can't work. Redesign it."). `review-milestone` lines 135–136 (a design
reviewer looks for mechanisms nobody has shown can produce their behaviour). Nothing says that the replacement
mechanism brings failures of its own.

**Lacked the reason, or had it?** Lacked it. The SU-M2 replan (18:02) moved recovery to an application-owned JSON
replacement. The next three reviews found three ways that replacement accepted a response it should have refused
(malformed nested facts, wrong endpoint, staged canonical payload) and one pending-state flash, all present at the
first JSON commit `e6a4c6f7` (verified rows). The SU-M3 replan (03:56) kept mounted content and selection; the next
review found the retained Search list retargeting after a retry (r5, `fe2e8d33`). These are the new mechanism's
own failure modes, and nothing in the planner's text pointed at them.

**The lightest version.** One sentence in `plan-module` "When a milestone keeps failing on the same finding",
after line 243:

> A new mechanism fixes the old failures and brings its own. Say in the design what it must refuse or survive,
> such as a response that is well-formed but for the wrong thing, or the moment before it settles, because the
> reviews after a replan find those next.

**Rows it would plausibly have caught (inferred):** the four SU-M2 JSON rows and SU-M3 r5, if the builder then
builds the refusals in rather than finding them one review at a time. Three of them are also covered by the
`proofs.md` sentence at review time, so the gain here is fewer rounds, not new coverage.

**What the heavy version would cost (inferred).** "The design review checks the list is there" is a presence check:
it passes any list, so it adds nothing a design reviewer reading the mechanism wouldn't already see. If instead the
reviewer judges whether the list is complete, every design round can find one more failure mode, which is the
non-converging review `review-milestone` lines 149–152 was written to stop, on a design path that already took five
rounds once (verified). Each design round is 70–130k uncached tokens and a planner revision (delivery record), and
the build can't start until it's approved.

## Under-built: what the four don't reach

1. **Inventory rows, 6 of 19 misses (verified count; remedy inferred).** All six were present at IR-M2's first
   reviewed commit and found by fixtures through the reader. Three are cases the validator already rejected and
   the reader still counted (wrong-side producer and consumer, invalid trigger, unresolved GraphQL). A browser
   review is the wrong tool for these, and so is a planner's list of routes. One automated check holds the whole
   class: every input the validator rejects is left out of the counts. `proofs.md` line 44 (Property or fuzz test)
   already offers this kind of proof; whether IR-M2's items used one can't be seen from here. If the owner wants
   text for it, one sentence in `done-when.md` "What makes a good item":

   > When two parts must agree about the same input, such as a validator and the reader that counts what it
   > accepts, prove they agree with a check over every kind of input, because a reviewer finds those
   > disagreements one at a time.

2. **Selection and scope edges, 4 rows.** One was on the list and missed. Zero matching bands and a private store
   as the only member are the edges of a range ("zero, one, many"), which `plan-module` line 147 already says a
   reviewer will try. The agents had the reason and didn't act on it. I can't see a cheap text change that would
   reliably fix that, and the evidence doesn't show why, so I'd leave it.

3. **How long reviews ran (inferred, unverified cause).** IR-M2 round 1 ran 15 minutes on a diff where 15 defects
   were already present; later rounds ran 8–11 minutes and found one to three each. That is consistent with a
   review that stops at about the same effort whatever it is judging. `review-completeness.md` says reviewers
   didn't stop at the first Must Fix, so this isn't the first critique's "finish the list" point. Before writing
   anything about it, it's worth checking whether review sessions in that project ran with a lower effort or a
   time limit.

## Text to add, all in one place

| File | Where | Text |
|---|---|---|
| `plan-module/references/proofs.md` | after line 64 | The shared-mechanism sentence in change 1 |
| `build-milestone/SKILL.md` | after line 91 | The "fix changes something others rely on" sentence in change 2 |
| `build/scripts/agent_loop.py` `FINDINGS_TEMPLATE` | line 407 | The first critique's "same cause elsewhere, add a test" line |
| `plan-module/SKILL.md` | after line 243 | The "new mechanism brings its own failures" sentence in change 4 |
| `plan-module/references/done-when.md` | "What makes a good item" | Optional: the "two parts must agree" sentence |

No new field in the done-when file, no new rule for the script, no new step for the reviewer.
