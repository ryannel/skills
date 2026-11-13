# Review of every instruction an agent reads in the orchestrate set

13 November 2026. Findings 1 to 7 were applied the same day, uncommitted when this was written; "Applied" at
the end says what changed and what was left. Finding 8 was looked at in Thrum's plans, and its section now says
what is there.

## What I measured each text against

An agent in this set is capable and new to the room. So each text was read with four questions, all taken from
the `prompting-agents` skill:

1. Does it give the reader the situation and what finished looks like, and leave the route to the reader?
2. Does it tell the reader something it couldn't have found out, or something it would do anyway?
3. Does each boundary say what to do and why, with its exception inside it?
4. Is it written as that skill describes: the main thing first, ordinary words, a new fact set beside the
   ordinary case, whole sentences, and each thing said once, close to the moment it applies?

## What was wrong with my two drafts

Both drafts were short because I squeezed them, and the skill says a prompt gets short by leaving things out.

- They used "cases", a word I made up and never defined.
- They gave a new fact without the ordinary case beside it. A builder's ordinary idea of a review is a list of
  what is wrong. The drafts never said that this is the idea being corrected.
- They left the reader to work out how four clipped sentences connect, and never said what finished looks like.

The same texts again, written the way the skill describes.

**The script's message to a builder after a failed review** (replaces `FINDINGS_TEMPLATE`):

> A reviewer has judged {milestone}, and it isn't finished yet. The review is at {path}.
>
> A reviewer can't try everything, so a review describes what one reviewer happened to try. Where it says an item
> failed, it shows one thing that makes the item untrue, and there may be others like it that the reviewer never
> reached. The next review is done by a new reviewer, who starts again from the items and chooses what to try.
>
> So the milestone is finished when every item is true as it is written, and that hasn't changed. The script has
> set the items that didn't pass back to open, and each needs new evidence. An item marked could_not_judge is one
> the reviewer couldn't see for itself, so it needs evidence a reviewer can reach. The Suggestions in the review
> are yours to take or leave.
>
> The `findings` list in the done-when file marks with `repeat` anything an earlier review also found. After four
> reviews with a repeat, the script sends the milestone to a planner instead of a builder.
>
> When the items are true, merge and end with DONE, and leave the state as in_progress. The script runs the
> checks again and sets Ready for Review itself.

**What a finding says, in the reviewer's skill** (replaces the opening of item 3 under "What finished looks
like"):

> Each finding is written for a builder who saw none of your session and will treat it as everything you know.
> Lead with the item, and say that its statement isn't true yet. Then give what you saw that shows it: what you
> did, what happened, what should have happened, and where, as a file and line, the steps, or a screenshot. Say
> what you tried and what you left untried. If the old name was still in the workspace switcher, and you didn't
> open the breadcrumb or the rail, the builder needs to know both.

## Findings, largest expected effect first

### 1. A failed review reaches the builder as a list to clear

This is the one we discussed. It is said in five places, so changing one would leave four saying the old thing.

| Where | What it says now |
|---|---|
| `agent_loop.py:507`, `FINDINGS_TEMPLATE` | "Fix every Must Fix finding", "Add the findings to the plan as work items, fix them, re-verify the affected items" |
| `build-milestone/SKILL.md:171-178` | `next` "tells you to fix what the reviewer found", and repeats: "make sure those stay fixed" |
| `plan-module/references/done-when.md`, "When a review fails" | "The same builder fixes what the reviewer found" |
| `build/SKILL.md:278` and `:358` | The lead resumes the builder "with `--message` and what the reviewer found" |
| `review-milestone/SKILL.md:99-103` | A finding is a bug report: what I did, what happened, what should have happened, where |

Change: the two redrafts above, and the same idea in one sentence in each of the other three places. The
`findings` list in the done-when file stays, because the script counts repeats from it.

### 2. The second reviewer starts from the first reviewer's list

`review-milestone/SKILL.md:131` says "Start from the earlier review, and say whether each Must Fix in it is now
fixed. Then judge the items again." The script's review prompt does the same thing earlier still: it prints the
earlier rounds' findings before the reviewer has looked at anything (`review.txt`, "Earlier failed rounds").

This is finding 1 seen from the other side. The reviewer is led to confirm that the named places are fixed. The
same skill already tells the reviewer to form its own view before it reads the builder's evidence, and gives
the reason. The earlier review deserves the same treatment:

> Judge the items as they are written before you read the earlier review, the same way you formed your own view
> before reading the builder's evidence. Read first, the earlier review tells you where to look, and the review
> turns into a check that the places it named are fixed. Then read it, and say whether each Must Fix in it is
> still there.

The earlier findings still have to reach the reviewer, because a repeated finding must keep its name. The
prompt can name the file that holds them and stop printing them.

A design review is different on purpose. There the skill tells the reviewer to start from the last round so the
design converges, and the record shows that worked. I would leave it.

### 3. The planner is handed the conclusion

`replan_task` (`agent_loop.py:2015`) tells the planner that four repeated findings mean "the plan is wrong".
`plan-module/SKILL.md:263-271` says the same and offers three causes, all of them faults in the plan. The
done-when reference says only that "the plan may be the problem".

A reader handed a conclusion tends to come back agreeing with it. On Groundwork most repeats looked like fixes
made in one place at a time, which is not a fault in the plan. A planner told the plan is wrong rewrites the
items, and a rewrite costs a design review and a rebuild.

Change in wording, which is free: say what happened (four reviews repeated a finding) and ask the planner to
decide why. Change in the script, which is not free: let a planner that finds the plan sound say so on a
re-plan, as it already can on a diagnosis with `KEEP`. I have not checked what the script does with `KEEP` on a
re-plan.

### 4. The same guidance is given two to four times

The comment above `BUILD_TEMPLATE` says the prompt "carries only what the build-milestone skill can't". It
carries more than that.

| Guidance | Where it is said |
|---|---|
| Wait with `background` and `wait`, not `sleep` and `tail` | The builder's skill ("Long commands"), the build prompt, the review prompt |
| Leave the state as `in_progress` | The build prompt's goal, the builder's skill three times, the resumed-turn message, the failed-review message |
| The reviewer leaves its files uncommitted | Both reviewer agent files, the reviewer's skill, the review prompt, the resumed-turn message |
| The planner leaves `ACCEPTED.json` and `STATUS.md` alone | The planner's agent file, the planner's skill, the plan prompt |
| What to do with an item that needs the human | The builder's skill, the build prompt, the resumed-turn message |
| The script's checks already passed; captures are linked, not embedded; `BLOCKED needs_access` | The reviewer's skill and the review prompt, each |

The skill warns that a caution stated three times gets applied too widely, and its notes on Fable and GPT-6 say
both take every caution at full strength.

Change: the first prompt carries the facts of this session (paths, whether it is visible, which items need
someone, the human's rules, the lead's note). The skill carries the guidance. The message on a resumed turn
stays, because a long Codex session can lose the skill when it is compacted.

Cost: the repeats were a net for a session that never read its skill. I don't know how often that happens, so
I would remove one repeat at a time and watch.

### 5. The script's prompts still list rules without reasons

The clean-up this morning covered the skills. The prompts the script sends were not part of it.

| Where | Now |
|---|---|
| `REVIEW_TEMPLATE`, under "Rules:" | "Don't commit, push or change anything else." "Don't start other agents." |
| `DESIGN_REVIEW_TEMPLATE`, under "Rules:" | "change nothing else", "Don't start other agents." |
| `PLAN_TEMPLATE`, under "Rules:" | "You can't start other agents." "Never edit an ACCEPTED.json file or the plans folder's STATUS.md" |
| `BUILD_TEMPLATE` | "Work only in this worktree." and, for a hardware item, "Don't ask anyone to confirm anything." |
| The resumed-turn message, `agent_loop.py:5043-5046` | "Still binding: change only …; don't commit, push or start agents." |

Each has a reason somewhere else in the set. The Codex reviewer's agent file has the one for other agents: "a
review whose reading was handed to a helper hasn't read the work." Change: the heading "Rules:" becomes "About
this session:", and each line says what to do and why, as the `src/gen/` example in the skill does. For
example: "Leave your review uncommitted. The script checks what you changed, then commits and merges it."

One slip to fix while there: line 5043 tells a resumed reviewer it may change "the verdict fields, state and
fails". `fails` is a count the script keeps. The reviewer's field is `findings`.

### 6. The lead's skill tells the lead what each result's `next` already says

`build/SKILL.md` has three tables that say what the lead does, 22 rows in all (lines 230-282). Nearly every row
restates the command and reason that the result carries in `next`. This is the same repeat as finding 4, in the
lead's skill.

I would not rewrite these now. The change you approved, where the script runs its own `next`, removes most of
the rows, and the tables should be cut when that lands.

### 7. Smaller things

- `plan-module/SKILL.md:136`: "Each rule below is here because a plan without it went wrong." This is a story
  line I missed, and it calls the guidance rules. Remove it.
- `build-milestone/SKILL.md:182`: "After three different approaches, each built and run, stop adjusting." A
  count for the builder to stop at. Say the fact: when adjusting isn't getting closer, the mechanism may be
  unable to produce the behaviour, and a small reproduction shows whether it can.
- `build/SKILL.md:364`: "don't answer for them, don't fill a gap with your own judgement, and don't save what
  you expect them to say" says one thing three times. The sentence before it already says it once.
- `replan_task` and `diagnose_task`: each is one sentence of colons, brackets and semicolons. Rewrite as short
  sentences.
- The planner's task after a design review: "Resolve its 2 Must Fix findings". The same list to clear, with a
  smaller effect, since designs now pass in one or two rounds.

### 8. What the plan file gives a builder besides the items

Read in five of Thrum's thirteen plans on `origin/main`: CULLING, CONTENT-LOOP, CREATOR, EFFECT-GRAPH and
APPLE-TILE.

- A ticked work list for each milestone. In four of the five its entries are the planner's implementation steps.
  CULLING M1: "Key the visible-last bits by logical slot on the bucket route, clear the next side each frame, and
  lift the refusal in mesh admission." The design already holds the mechanisms, in 3,766 words for CULLING.
- Lines a builder would do anyway. Every APPLE-TILE milestone ends "Retain actual target proof and run scoped
  checks plus `./dev check` before claiming."
- Failed reviews added as work. CULLING has a heading "Review round 1 — MF1" with three ticked entries, CREATOR
  has "The Must Fix findings F1 and F2 of review 1", and APPLE-TILE has "Resolve review MF1 by…". The old
  failed-review message asked for this, and no longer does.
- "Stop rules, for every milestone", one to five in each plan, mostly written as "Never…" and "do not…". Three of
  the five carry the same sentence about launching Chrome outside the Codex sandbox, which the builder's skill
  says. Some are true of the whole project and belong in the project settings. A few are facts about the module
  that a builder couldn't guess, such as which timing fields wait for another module's milestone.
- Work that no item asks for, such as "update the maturity ledger and the evidence page".

The script reads none of it. It checks the plan's length and headings and counts the `Assumption:` lines, and
nothing reads a tick. The list comes from the template in `done-when.md` and from two lines in the builder's
skill. The planner's skill never says what the list is for.

Proposed, not applied: each milestone in the plan file gets a short note in sentences, holding what a builder
couldn't work out from the items and the design: what already exists, what another module owns, an order where
the order matters, and any work no item covers, named as such. A boundary goes where it holds, with its reason:
the project settings for one that is true everywhere, the design for one about the module. The builder stops
ticking, because the items' `status`, the log and the handoff already say what an earlier session finished.
Existing plans keep working, since nothing reads the list. What is lost is a breakdown of the work that some
builders may lean on, and I can't tell from the record how many do.

## Every text, and what I found

| Text | Reader | Result |
|---|---|---|
| `BUILD_TEMPLATE`, with the goal line, the session notes, the notes on items that need someone, the Human Feedback note and the handoff note | Builder | The goal paragraph is good. Findings 4 and 5 |
| The new-session note and the message after a turn limit | Builder | Facts only. Leave |
| The resumed-turn message | Builder, reviewer | Findings 4 and 5, and the `fails` slip |
| `FINDINGS_TEMPLATE` | Builder | Finding 1 |
| The message when the script's checks fail | Builder | Good: what failed, where it ran, why that can differ. Leave |
| The messages when `merge` refuses a state, and for a branch from before 2.1.0 | Builder | A recovery in order, where the order is the task. Leave |
| The message after a stopped tool call | Builder | Says what happened and what to do if the cause is access. Leave |
| `REVIEW_TEMPLATE`, with the earlier rounds and the planner's diagnosis | Reviewer | Findings 2, 4 and 5 |
| `DESIGN_REVIEW_TEMPLATE` | Reviewer | Finding 5 |
| `PLAN_TEMPLATE` | Planner | Finding 5 |
| `replan_task` | Planner | Findings 3 and 7 |
| `diagnose_task` | Planner | Asks a fair question with three ways out. Finding 7 for its wording |
| The planner's task after a design review | Planner | Finding 7 |
| The planner's task for a missing dependency | Planner | Facts and where the work is. Leave |
| The note that a Claude turn ending is read as the work ending | Reviewer, planner | Good. Leave |
| The `why` and `ask` texts in each result's `next` | Lead, and you | They say what is true and who acts. Leave, apart from "with the findings" under finding 1 |
| Refusals, warnings and `problems` in results | Lead | I read the ones that forbid something and not every string. None reads as a rule without a reason |
| `build-milestone/SKILL.md` | Builder | Findings 1, 4 and 7. The rest gives reasons |
| `review-milestone/SKILL.md` | Reviewer | Findings 1 and 2 |
| `plan-module/SKILL.md` | Planner | Findings 3 and 7 |
| `build/SKILL.md` | Lead | Findings 1, 6 and 7 |
| `interview-me/SKILL.md` | Lead, with you | Guidance with reasons throughout. Its numbered steps are ones where the order is the task. Leave |
| `domain-language/SKILL.md` | Any agent, with you | The same. Leave |
| `plan-module/references/done-when.md` | All | Findings 1 and 8. The tables are facts about the script |
| `plan-module/references/proofs.md` | Planner, builder, reviewer | "Write down what you will look at before you look" is a step, with its reason, and it is the technique itself. Leave |
| `plan-module/references/profile.md` | Planner | A template and facts. Leave |
| `review-milestone/references/graded-examples.md` | Reviewer | Examples with the reason each is there. Leave |
| `build/references/older-projects.md` | Lead | Facts. Leave |
| The three agent files | Planner, reviewer | Clean after this morning. They repeat the skills (finding 4) |
| `.agents/skills/orchestration-skill/SKILL.md` | Whoever writes for the set | Needs one paragraph saying what this review measured against, so new text is written this way |

Not covered, because no agent in a build reads them: `README.md`, which is written for you, and `GLOSSARY.md`,
which is not installed.

## What I don't know

- Whether any of this reduces failed reviews. Finding 1 rests on the Groundwork record, where 19 of 22 failed
  rounds looked like four causes met one place at a time. That grouping was made from summaries a few words
  long.
- How a GPT-6.1 Sol builder reads the new failed-review message. The skill's note on Sol says it misses indirect
  examples of a thing unless the kind is named, which is the behaviour finding 1 is about.
- How often a session works without having read its skill, which decides how safe finding 4 is.

## Applied

- Finding 1: the script's message after a failed review, the builder's skill (a new section, "When a review
  fails"), the reviewer's skill (what a finding says), the reference, the lead's skill and the README.
- Finding 2: the reviewer's skill, and the review prompt, which now says where the earlier reviews are and no
  longer prints what they found.
- Finding 3: the re-plan task and the planner's skill say what happened and ask why. This needed one change in
  behaviour: a planner sent a re-plan can now end with `KEEP`, as on a diagnosis, and it counts as the
  milestone's re-plan, so a second run of four repeated failures still goes to the human.
- Finding 4: the first prompts keep the session's facts and lose what the skills say. Two things moved into
  skills that had been only in prompts: how a reviewer waits on a long command, and that a planner leaves its
  files uncommitted. The three agent files are down to two or three sentences each.
- Finding 5: "Rules:" is "About this session:" in all four prompts, and the lines left are facts or carry their
  reason. The resumed reviewer's message names `findings`, not `fails`.
- Finding 6: the two tables that repeated `next` word for word are gone from the lead's skill, 11 of the 22 rows.
  The table of what each result means stays, because its rows also say what the lead does with its other
  builders, which no single `next` can.
- Finding 7: all but the planner's task after a design review, which is left as it was. A design review is meant
  to close on the last round's findings, so "Resolve its 2 Must Fix findings" says what is wanted there.
- The authoring spec has a paragraph on where each kind of text goes.

`python3 tests/orchestration/run.py`: 372 tests pass. The ten saved prompts that changed are regenerated.
