# Changes to orchestrate after the groundWork review-completeness finding

Written 2026-11-11 by a Claude Fable 5.2 session, from `delivery-record.md`, `review-completeness.md` and the
orchestrate source on branch `orchestrate-1.6.4` at `6989342` (1.7.1). Nothing outside this file was edited.
Paths are under `skills/orchestration/` unless they say otherwise.

## Summary

Eight changes, in the order I would make them. None adds a field, a state or a script rule. Seven are wording in
the three skills and their references. Two of them also change a prompt string inside `agent_loop.py`, because
that string is what the agent actually reads at the moment that matters.

| # | Change | File | Failure it is for |
|---|---|---|---|
| 1 | Say what a review is for, what a miss costs, and that the items set severity but not where to look | `review-milestone/SKILL.md` | Review misses |
| 2 | Teach "how to inspect" about behaviour: ways in, what is already there, how it ends | `plan-module/references/proofs.md` | Both (builders and reviewers share it) |
| 3 | Tell the builder what a finding is and what a fix is, in the skill and in the fix-round message | `build-milestone/SKILL.md`, `FINDINGS_TEMPLATE` | Fixes that introduce problems, and fixes of one case |
| 4 | Rewrite the re-review paragraph so the fix gets reviewed as new work | `review-milestone/SKILL.md` | Introduced problems that then got past a review |
| 5 | A finding reports how far the defect goes | `review-milestone/SKILL.md` | One-case-per-round runs |
| 6 | Two graded examples from this run | `review-milestone/references/graded-examples.md` | Review misses |
| 7 | Reword the "open-ended item" reason | `review-milestone/SKILL.md` | A line that may now push the wrong way |
| 8 | Let a diagnosis say "the reviews were incomplete" | `plan-module/SKILL.md`, `review_notes` and three echoes | The loop's own answer to this pattern |

## What I verified

In the evidence:

- 30 defects: 19 present at the first commit the earlier review judged, 11 first present at a later commit
  (`review-completeness.md`, the table).
- Of the 11 introduced, 7 were already in a commit that at least one later review judged and passed over. I
  derived this from the table's "How I checked" column and the coverage paragraphs, which say for each one which
  round's build first had it: Search refresh (in round 2's build, found round 3), failed Flight (round 2's, found
  round 4), wrong endpoint and pending flash (round 5's, found round 6), staged payload (round 5's, found round
  7), Inspector history (round 3's, found round 8), reciprocal exact calls (round 6's, found round 7). The other
  four were found by the first review that saw them.
- 8 of the 11 introduced defects sit on a mechanism the fix itself added: the route recovery at `0f4dda03` (2),
  the JSON replacement route at `e6a4c6f7` (4) and its extension to supporting views at `6557e2fd` (2). The other
  three broke something that had worked (Inspector history, reciprocal exact calls, Search highlight).
- INTEGRATION-ROLLUPS M2 failed rounds 4 to 8 on a link or caption that could not be clicked because another
  covered it, in five different arrangements. Four of the five were broken at the first reviewed commit.
- One miss was on the reviewer's own list: "retained selection after depth changes" was planned in round 1, and
  the collapse-loses-evidence defect was still passed over.
- Reviews ran 7 to 15 minutes. First reviews ran 11 to 15, later ones 7 to 12.
- The gap between one failed verdict and the next was 19 minutes to 2 hours (my subtraction of the recorded
  verdict times in `delivery-record.md`).
- The builder session behind SHARED-UI M3's first three claims reached 69M cached tokens.

In the skills:

- `review-milestone/SKILL.md` line 49 already says a reviewer "tries the obvious paths and skips the edges". The
  1.5.4 text the run mostly used said the same ("tends to test the obvious paths and skip the edges", `git show
  f3cc653`). So the reviewers were told about the weakness in general terms, and it was not enough.
- The only remedy that paragraph gives for skipped edges is line 58–59: "Run the edge conditions the project
  settings list for each item's target". The template for those (`plan-module/references/profile.md` line 54–55)
  is one fixed list per target: "empty, loading, error, slow network, resize".
- Line 51 says "your sense of whether a defect matters doesn't decide the result; the written items do". It is
  about severity. Nothing in the skill says separately where to look.
- "What finished looks like" (lines 66–99) defines finished as every item having a verdict and the files written.
- `proofs.md` "How to inspect" (lines 56–81) uses a boat, a cloud, a command-line tool and "a screen: its states
  and controls". It has nothing about one behaviour being reached several ways.
- The five starting graded examples vary one thing at a time. None shows two conditions meeting, and none is a
  second review.
- `review-milestone/SKILL.md` lines 111–112: "Start from the earlier review, and say whether each Must Fix in it
  is now fixed. Then judge the items again as they are written." Nothing says the fix is unreviewed code. This
  section and the earlier-rounds note did not exist in 1.5.4.
- Lines 123–125 ("Hold an open-ended item … each review finds one more corner") arrived in 1.6.2. They were not
  in the text INTEGRATION-ROLLUPS M2 or SHARED-UI M2 rounds 1–8 ran on.
- `build-milestone/SKILL.md` gives a fix after a failed review two sentences (lines 112–113), and their reason is
  the escalation count: "Repeats are what send a milestone back to a planner, so make sure those stay fixed."
  Line 80 asks for a test on an ordinary fix with no plan. Nothing asks for one on a review fix.
- A builder in a fix round is sent `FINDINGS_TEMPLATE` (`agent_loop.py` lines 407–412, used at 1712, 5214 and
  5629). It says "fix them, re-verify the affected items", and that the items that didn't pass were set back to
  open.
- `tests/orchestration/test_agent_loop.py` line 2339 asserts "Every blocking finding counts" is in that template.
  My replacement keeps the phrase.
- A diagnosing planner's choices (`plan-module/SKILL.md` lines 261–267) are: items too broad, a builder who keeps
  breaking something, a reviewer whose findings go beyond the items, or the owner. `review_notes` (line
  1580–1582) then tells the next reviewer "Judge the items as written."

## What I infer

- **Why capable reviewers stopped at ten minutes.** The skill's unit of work is the item, and its definition of
  finished is a verdict on each. A reviewer who has a list entry and a screenshot for every item has finished by
  the skill's own account. The general warning about edges had no consequence attached and pointed at a fixed
  list in another file.
- **Why purpose should work here when the general warning didn't.** The old text named a weakness. It did not say
  what an "edge" is in a product with state, and it did not say what a miss costs. Changes 1 and 2 say both, with
  the cases from this run. I have not tested this. The test is cheap to describe: run a first review at
  `53d73d23`, `7509f717` and `8494bf72` with the new text and count how many of the 15, 2 and 2 known misses it
  finds. It spends quota on the groundWork machine, so it is the owner's call.
- **Why the builder text matters more in the message than in the skill.** A fix round resumes a session that read
  the skill tens of millions of tokens earlier. I assume the skill body is compacted away by then and the message
  is what the builder acts on.
- The row counts under each change below are my reading of which rows the wording reaches. They are not
  reproductions.

## The changes

### 1. Say what the review is for and where defects are

**File.** `review-milestone/SKILL.md`, section "What reviewers get wrong", and one sentence in "What finished
looks like".

**Replace** the paragraph at lines 57–62 ("Use the product yourself … give it Could Not Judge.") with these three:

> Use the product yourself, on its real target, built from the commit you were given. Take your own screenshots
> and recordings, because the builder's show what the builder wanted you to see. Watch for work judged only in
> favourable conditions, such as slowed down, close up, or on a faster machine than the people who use the product
> have, and for work that is correct but too subtle for anyone to notice from where those people really are.
>
> The items decide what counts as a Must Fix. They don't mark out where to look. An item says one thing that must
> be true, and people reach that thing in more than one way: from different screens and triggers, with different
> things already selected, open or loading, and with the request behind it succeeding, failing, arriving late, or
> returning something well-formed that is wrong. The item has to hold in all of them, and the builder has usually
> tried one. On one project three milestones failed review five to eight times each. The reviewers had judged
> every item every time, and 19 of the 30 defects they found in the end had been in the first build they passed
> over: a selected call whose evidence vanished when its group was collapsed, a recovery that never started when
> a hover was what met the conflict, a retry that reloaded the whole page when the second request failed. So for
> each item, work out the ways in, what can already be on screen, and how the request or the input can turn out.
> Try the ones that could behave differently, and try two together where they could interfere.
> [How to inspect](../plan-module/references/proofs.md#how-to-inspect) says more. The edge conditions the project
> settings list for a target are where this starts, so run them and say which you ran. If you have seen something
> work only one way, you don't yet know that it works. Try the others, and give Could Not Judge to what you
> couldn't reach.
>
> What you pass over is not caught for nothing later. It comes back as another failed review, after another
> builder session, with the builder's fix as new code to judge. On that project each such round took between
> twenty minutes and two hours. A review that takes three times as long and finds what is there is the cheap one.

**Add** before the numbered list under "What finished looks like" (line 65):

> The review is finished when you would be surprised if a second reviewer, given this same commit, found a Must
> Fix that you hadn't. The five things below are how that is recorded.

**Rows.** Aimed at all 19 misses. I am most confident about the 12 that are a plain meeting of two conditions:
collapse with a selection, switching groups with a citation, a scope with one member and with none, the four
covered click targets, the stale title, hover as the only trigger, the switcher after a warm rename, the failed
People Flight. The six inventory rows are reached only through the "or the input" clause and change 2. "Exact-link
list omits the operation" is a plain content miss and I would not count it.

**Cost and risk.** Reviews get longer, perhaps two to four times. A review in the record cost 4 to 23M cached
tokens, and a round cost a builder session of 2 to 55M as well. More looking will find more, so the first
milestones under this text may fail more often before they fail fewer times. Severity is unchanged: a defect is
still a Must Fix only under lines 51–55. The risk is a reviewer who never stops. The "finished when" sentence is
the brake, and it is a judgement, not a count. About 330 words added to a 2,150-word skill.

**Why not structure.** `proposals-2.md` item 1 has the planner list each item's routes, states and outcomes. The
evidence argues against it. Reviewers covered what was listed and missed what wasn't, so a longer list moves the
edge of the list and keeps the failure. And 8 of the 30 defects were on mechanisms added after the first review,
4 of them by a builder's fix that no planner saw.

### 2. Teach "how to inspect" about behaviour

**File.** `plan-module/references/proofs.md`, section "How to inspect". Builders and reviewers both use it.

**Add** after the paragraph ending "…turn into stripy bands when you zoom in." (line 73):

> Behaviour hides things the same way, and a list of screens and controls won't show it. Anything a person does
> in the product has several ways in: a link, Search, the back button, a saved address, a hover, a cold load and
> a warm one. It has several things that may already be there when it happens: a selection, an open panel, a
> history trail, a request still pending, data another view has just changed. And it has several ways to end: the
> request succeeds, fails, is slow, returns nothing, or returns something well-formed that is wrong or belongs to
> something else. For data, it is each kind of input and each way that kind can be invalid, and none, one and
> many of anything that can overlap. Put on the list the combinations that could behave differently, and not only
> each piece once. In one project's reviews every piece was on the list and passed, and the defects were where
> two met: changing group while a citation was selected, two links drawn along the same path, a failed refresh
> reached through Search. When the product changes something, list every place on screen that shows it, because
> one of them is often left showing the old value.

**Change** the "User journey" row of the kinds table (line 52), last cell, from "Only the easy path was tried" to:

> Only the easy path was tried, or each state was reached one way only

**Rows.** The same 19, and through the builder's own check before Ready for Review (`build-milestone` line 88
sends the builder here) the 8 introduced defects on fix-added mechanisms. The last sentence is for the four
stale-revision rows (SHARED-UI M2 rounds 2 and 3, M3 round 2, and M3 round 1 in the delivery record).

**Cost and risk.** About 170 words in a reference. The lists of ways in and endings are web-shaped. A game or an
asset project will find them beside the point, though the section's other examples are a boat and a cloud, so the
mix is no worse. An agent could read the lists as a checklist and cross every entry with every other. "That
could behave differently" is the guard.

### 3. Tell the builder what a finding is and what a fix is

**File.** `build-milestone/SKILL.md`, section "The review", and `FINDINGS_TEMPLATE` in
`build/scripts/agent_loop.py`.

**Replace** lines 112–113 of the skill ("The milestone's `findings` … make sure those stay fixed.") with:

> A reviewer can't try everything, so each Must Fix is one place where a fault showed, and the next reviewer is a
> new agent who will try somewhere else. Fixing only the place that was reported is how a milestone fails round
> after round. On one project a milestone failed five reviews running on a link that couldn't be clicked because
> another covered it, each time in a different arrangement of links, and four of the five arrangements had been
> broken since the first build. So find the cause before you change anything. Then look for everywhere else that
> cause reaches: the other ways into the same code, the other views built the same way, the other inputs of the
> same kind. You know the code and the reviewer doesn't, so this part of the review is yours.
>
> Your fix is also new work that nobody has judged. On that project 11 of 30 Must Fixes were introduced by the
> fix for an earlier one. Most sat on something the fix had added: a recovery that worked from the page the
> reviewer had used and not from Search, a replacement response that was accepted when it was well-formed but for
> the wrong endpoint. Hold what you add in a fix to the same standard as the milestone. Before you set Ready for
> Review again, inspect it as [how to inspect](../plan-module/references/proofs.md#how-to-inspect) describes,
> along with whatever it replaced or rewired, which worked before and still has to.
>
> Where a test can reproduce a finding, write one that covers the family and not the one case, and add it to the
> project's tests. `land` then runs it every time, and the fix holds without anyone remembering it. In your
> `LOG.md` entry, say what the cause was and where else you looked.
>
> The milestone's `findings`, in the done-when file, lists each Must Fix and marks with `repeat` each one an
> earlier round raised. A repeat means a fix didn't hold.

**Replace** `FINDINGS_TEMPLATE` (lines 407–412) with:

> The reviewer failed {milestone}: see {evidence}/{module}/{milestone}-review.md. Every blocking finding counts,
> including cant_tell items (they need evidence the reviewer could reach) and blocking defects outside the items;
> advisory ones are your call. The milestone's `findings` in the done-when file lists each Must Fix, and marks
> with `repeat` any an earlier round raised. The reviewer sampled the product, so each finding is one place a
> fault showed: find its cause, fix it everywhere that cause reaches, and where a test can reproduce it, add one
> that covers the family. Your fix is new work nobody has judged, so before you claim again, inspect what you
> added and what it rewired as you inspected the milestone (build-milestone, "The review"). The loop has set the
> items that didn't pass back to open, so each needs fresh evidence. An item that passed was proved on the old
> code, so prove it again if your fix touches what it covers. Add the findings to the plan as work items, fix
> them, integrate, set the state back to claimed, and end with DONE, BLOCKED or NEEDS_CONTEXT.

**Rows.** The 8 introduced defects on fix-added mechanisms, if the builder inspects the mechanism's other ways in
and endings. Reciprocal exact calls (round 7), if a click-target test over the fixtures had been written after
round 4 or 5. As siblings of an earlier finding that were already in the code: wrong-side message parties and the
invalid trigger after unresolved GraphQL (the lead's notes say the validator rejected each and the inventory
counted it anyway, which reads as one cause), the shared GET and PUT path, the opposing collapsed links and the
dense lane after the covered caption, and hover-only recovery after Search recovery. I don't expect it to have
caught the Inspector history loss or the Search highlight. Each needed a specific sequence nobody had a reason to
try.

**Cost and risk.** Fix rounds get slower. A builder may widen a fix into a refactor, and a wider fix can itself
introduce more. "Don't build a later milestone" (line 135) still bounds it. The family test is builder-written,
so it can be weak; `done-when.md` line 361 already notes that about builder-written tests. The template edit is
script text and needs the test at line 2339 re-run, though the asserted phrase is kept. Dropped from the template:
"those are what escalate the milestone, so make sure they stay fixed", which gives the count as the reason.

**Why the template too.** See the third inference above. The same words in the skill alone would not be in front
of the builder at round 3.

### 4. Review the fix as new work

**File.** `review-milestone/SKILL.md`, section "A milestone that has been reviewed before".

**Replace** lines 111–112 ("Start from the earlier review … as they are written.") with:

> Start from the earlier review, and say whether each Must Fix in it is now fixed. Go beyond the steps the
> earlier reviewer gave, because those are the one case the builder is sure to have tried. The finding was one
> place a fault showed, so try the same fault's other ways in.
>
> Then read what changed since the commit the last review judged. The record file, `ACCEPTED.json`, names that
> commit for each round. This is the newest code in the milestone and nobody independent has seen it. On one
> project 11 of 30 Must Fixes were introduced by a fix, and 7 of those 11 got past at least one more review
> before anyone found them. A fix often adds a mechanism of its own, such as a new recovery request, with its own
> ways in and its own ways to fail. It also rewires things that worked, so use what it touched as well as what
> it added.
>
> Then judge the whole milestone again as if this were its first review. The earlier reviews passed over whatever
> they didn't try, so an earlier Pass on an item tells you little.

**Rows.** The 7 introduced defects that got past a later review: Search refresh, failed Flight, wrong endpoint,
pending flash, staged payload, Inspector history, reciprocal exact calls. Inspector history is the doubtful one.
It got past five reviews.

**Cost and risk.** Later reviews stop being the shorter ones. "As if this were its first review" drops "as they
are written", which was there to stop a later reviewer drifting past the items. Lines 51–55 still hold severity
to the items, and change 7 keeps the limit on unreachable inputs. If drift returns, it will show as Must Fixes
the owner overturns.

**Why not structure.** I considered having the script pass the previous commit in the reviewer's task. The
record file already holds it (`agent_loop.py` line 5043 writes `commit` on each review), so a sentence saying
where is enough.

### 5. A finding reports how far the defect goes

**File.** `review-milestone/SKILL.md`, "What finished looks like", item 3.

**Add** after "Put the worst finding first." (line 84):

> When you find a defect, find out how far it goes before you write it up. Vary it: another way in, another
> arrangement, the failing version of the request. Then report the extent in the one finding, with what breaks
> and what you tried nearby that works. The builder fixes what a finding describes, and a finding that describes
> one case gets one case fixed.

**Rows.** The runs where each round reported one more case of the same fault: click targets in rounds 5, 6 and 8
after round 4; the inventory counting rejected references in rounds 3 and 4 after round 2; the replacement
payload in rounds 6 and 7 after round 5. Eight rows, each one round earlier at least.

**Cost and risk.** A reviewer may state an extent wider than it tried, and a builder can't close a claim like
"all overlapping links". "What you tried nearby that works" is there so the finding carries its own boundary. It
overlaps change 3 on purpose. Either agent doing its half would have shortened those runs.

### 6. Two graded examples

**File.** `review-milestone/references/graded-examples.md`. Change its line 3 from "These five" to "These seven",
and add:

> ## Every item passes alone
>
> The milestone: a diagram of services whose links can be selected to show the evidence for each call, at three
> levels of detail. Its items say that links are selectable at each level, that the panel shows the selected
> call's evidence, and that a selection survives a change of level.
>
> The reviewer listed each level and a selection at each. Then it listed what could interfere: a selection held
> while its group was collapsed, a second group opened while a call in the first was selected, and two calls
> between the same services in opposite directions. Collapsing the group emptied the evidence panel. The two
> opposite calls were drawn along one path, and only one could be clicked. Two items got a Fail. The finding on
> the click target said how far it went: any two links that share a path, at every level, with the three
> arrangements the reviewer had tried.
>
> Why it is here: each item passed when it was tried by itself. On the project this comes from, a reviewer judged
> every item that way, and defects like these came back one at a time over the reviews that followed.
>
> ## The fix moved the fault
>
> The milestone had failed once: a view went on showing old data after the data changed underneath it. The
> builder added a request that fetches a replacement.
>
> The second reviewer confirmed that the earlier steps now worked. Then it read what had changed since the first
> review, and tried the new request's other ways in and its other endings. Started from Search, the replacement
> refreshed the header and left the drawing old. When the request failed, the whole page reloaded and the
> selection was lost. The earlier Must Fix was fixed. Two new ones were raised, both in code the first review
> never saw.
>
> Why it is here: confirming the earlier finding is the smallest part of a second review. The fix is new work.

**Rows.** Indirect. The skill calls these "the best guide to how strict to be" (line 26), and the existing five
all vary one condition at a time. Reinforces changes 1, 4 and 5.

**Cost and risk.** About 280 words in a file every reviewer reads. Both are web examples, which tilts a set that
was balanced across a command-line tool, a sign-up, a wake and props.

### 7. Reword the "open-ended item" reason

**File.** `review-milestone/SKILL.md`, lines 123–125.

**Replace** the last sentence ("Without this rule each review finds one more corner, and a sound milestone fails
round after round and goes back to a planner.") with:

> That is the only limit on where you look, and anything a person or a real input can reach is in range. Reviews
> that each find one more corner keep a sound milestone failing round after round. The cure is to find the
> corners in one review, not to leave them.

**Rows.** None directly. The line wasn't in the text most of the run used, so it did not cause those misses. I
propose it because the sentence tells a reviewer that finding a further corner is itself the failure, which is
the opposite of what the evidence asks for. The rule in the two sentences before it stays.

**Cost and risk.** Low. The original protected against unbounded `ask` items, and that protection is the rule,
not the reason.

### 8. Let a diagnosis say the reviews were incomplete

**Files.** `plan-module/SKILL.md` lines 256–267, `review_notes` in `agent_loop.py` lines 1580–1582, and the three
places that repeat the old meaning: `plan-module/references/done-when.md` lines 328–329, `build/SKILL.md` line
335 and `diagnose_task` line 1626.

**Add** to `plan-module/SKILL.md` after "Decide why, and say so in your report:" (line 259):

> First find out where the new findings came from, because the answer changes who has to act. Was each defect
> already in a build an earlier review passed, or did a fix bring it in? The record file names the commit each
> review judged.

**Change** in lines 265–266: "`builder` is for a builder who keeps breaking something" to "`builder` is for a
builder who keeps breaking something, or who fixes only the one case each finding names", and "`reviewer` is for
findings that go beyond the items, and the next reviewer is told to judge the items as written" to:

> `reviewer` is for reviews that have to change: findings that go beyond the items, or reviews that each found a
> little of what had been there all along. Say which, because the next reviewer is given your words.

**Change** the `review_notes` sentence to:

> A planner read the earlier reviews of {mid} and said what the next review should do differently: {why}.

**Rows.** None. Diagnosis arrived in 1.6.3 and the run never reached one. The reason is that six failed reviews
on new findings is exactly this run's pattern, and today the planner's choices lead to narrower items or to
"Judge the items as written". For 19 of these 30 that is the wrong answer.

**Cost and risk.** The widest edit and the weakest evidence, so it is last. It changes what `KEEP … reviewer`
means, in five places that must agree. A planner asked to trace defects to commits may spend a long session
doing what the groundWork lead did by hand. I would make it only after changes 1 to 5 have had a run.

## Considered and not recommended

- **The planner lists each item's routes, states and outcomes** (`proposals-2.md` 1 to 3). See change 1.
  `done-when.md` lines 350–354 also records that long items were rewritten up to four times each on another
  project.
- **A record of which combinations a reviewer tried.** It exists. `proofs.md` lines 75–76 keep the inspection
  list in the review, and the groundWork lead used those lists to write `review-completeness.md`.
- **The planner lists how a new mechanism can fail, at a replan** (`proposals-2.md` 4). This is the closest call.
  Four of the 11 introduced defects sit on the mechanism the SHARED-UI M2 replan brought in and two on a builder's
  extension of it in M3, and the replan's design review was recorded as approved two minutes after the replan ended. Against it: `plan-module` line 162 warns that reviewers fail the build on
  every requirement a planner adds, and the owner later relaxed this very scope for M3. I would see whether
  changes 2 and 3 make the builder do this before asking the planner to.
- **The script resets every item to open after a failed review.** The reviewer judges every item again anyway.
  One sentence in the template covers the builder's side.
- **A `class` field on findings, or a rule that the same cause counts as a repeat.** That changes when the loop
  escalates, not whether a defect is caught.

## Outside the two failures

The owner relaxed SHARED-UI M3's scope after five failed reviews, to allow a reload and transient resets. Several
Must Fixes in M2 and M3 were against that requirement. Wider reviews will fail more milestones on requirements of
that kind, so whether a costly requirement is really the owner's matters more after these changes than before.
`critique-of-proposals.md` covers that question under its item 3.
