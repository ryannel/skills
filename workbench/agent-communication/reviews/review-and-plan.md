# What reached the reviewers and planners in Thrum, and what it cost

This report covers the 30 reviewer sessions and 14 planner sessions in `workbench/agent-communication/thrum-prompts/`.
It judges each prompt against the `prompting-agents` skill and against what `review-milestone` and `plan-module` already
tell each agent. The templates were read as they are at `HEAD` (orchestrate 1.7.1). The sessions span versions 1.4.0 to
1.7.1, so where a problem has already been fixed at `HEAD`, the report says so.

## The main finding

The costliest text was not the template wording, and it was not the lead's tasks. It was the sentences the script
generates about the work itself: which commit the reviewer is standing on, what failed in earlier rounds, what changed
since the last design review, and what a blocked builder found. When the script can't work one of these out, it either
says something false or says nothing, and the agent can't tell that anything is missing. The agents are capable enough
to read a review file or a git log themselves. What they can't do is distrust a sentence that looks authoritative.

The fix that would help most is a rule for the script's own text. When the script can't establish a fact, it should
name the file or commit where the fact lives, rather than state the fact or leave it out.

Two other problems came up repeatedly. Planners skipped or cut short the dry run of their checks because a builder was
using the GPU, so their checks went unverified. And a Claude reviewer ended its turn while a long command was still
running in the background, which used up turns from a budget of three.

The lead's own tasks were mostly good. Several of them are worth keeping as models, and they are listed near the end.

## Problems, costliest first

### 1. The reviewer was put on a commit that wasn't the builder's claim, and wasn't told

**Who wrote it:** the script, through `REVIEW_TEMPLATE` and `review_once`.

**The text** (CREATOR M1, second round, 2026-11-11 04:26):

> This folder is a clean checkout of commit 42fdce97856de3d10a9cd71a911463cbf24603ea, made for you by the loop; build
> and run the product from it.

**What it cost (seen in the reply).** Commit `42fdce97` was the loop's own `migrate` commit, not the builder's claim at
`f5a40b27`. The reviewer found that `./dev check` failed with 540 broken links. It then had to work out that the
script's move had caused them, check out the claim commit to show the builder's work passed there, and run every
later step of `./dev check` by hand. It reached the right verdict, but only by distrusting the prompt.

**At `HEAD`.** Version 1.7.1 now reviews such a claim at the first commit where the moved done-when file exists. That
is still the `migrate` commit. The explanation goes into `WARNINGS`, which only the lead sees. The reviewer's prompt
still says nothing.

**Fix.** Whenever the commit under review is not the claim commit, the script should add one sentence to the prompt:
"The builder claimed at `f5a40b27`. The plan files moved at `42fdce97`, so you are on that commit, and anything the
move broke is not the builder's doing." The script already composes this sentence for the lead, so it only needs to
pass it to the reviewer as well.

### 2. A design re-review was not told what had changed, because the files had moved

**Who wrote it:** the script, through `design_changes`.

**The text.** The prompts for the design reviews at 04:39, 04:47, 04:50, 05:56 and 06:08 on 11 November contain no
"Since the last design review..." sentence. All five modules already had a design review. `design_changes` reads the
done-when file at the last review's commit using the new path, finds nothing there, and returns an empty string. The
prompt then reads like a first review.

**What it cost.** It is clearest in the ATMOSPHERE review at 06:08. Five minutes earlier, a planner had changed the H2
precision bound and rewritten M5.2's reviewer question. The prompt did not mention M5.2. The reviewer returned
`DESIGN OK` with "two suggestions", and its reply does not say whether it examined the new bound. Whether it did is
not known. What is known is that the prompt failed to point at the one item that had changed, in the review that most
needed it. The other four reviews were repeat reviews after a reshape, and their replies mention "carried-forward"
suggestions. That suggests the reviewers found the earlier review on their own, at the cost of reading each design
in full.

A related case shows the opposite gap. At 22:27 on 10 November, a CREATOR design review ran three minutes after the
previous one, with "No item's definition has changed since the last design review". The reviewer could only repeat
that the blocker was unresolved. That session was wasted, and the script had the facts to refuse to start it.

**Fix.**
- Have `design_changes` find the done-when file at the last review's commit under its old path. The record or
  `git log --follow` can supply it.
- When the comparison fails, say so: "The script couldn't compare the items with the last design review
  (`<review>`, at `<commit>`). Find what changed yourself."
- Compare `DESIGN.md` as well as the items. A planner usually changes both, and at present the sentence lists only
  the item changes.
- Refuse to start a design re-review when neither file has changed since a `DESIGN CHANGES` verdict, and tell the
  lead that the planner hasn't acted yet.

### 3. "No findings recorded" told a reviewer that an earlier failed round had found nothing

**Who wrote it:** the script, through `review_notes` and `history_lines`.

**The text** (CREATOR M1, second round):

> Earlier failed rounds of M1 that still count, with their findings: round 1 (2026-11-11): no findings recorded.

**What it cost.** Round 1 had two Must Fix findings: a stale refusal message under M1.3, and a starter that no longer
built on Linux or Windows. Round 1 ran under 1.6.2, which recorded `fails` rather than `findings`, so the record had
nothing to list. The sentence is literally true, but it reads as "round 1 found nothing". The reviewer recovered,
because the skill says to start from the earlier review, and its reply walks through both findings. A reviewer that
trusted the prompt would not have known which names to keep, and the skill says a repeated finding must keep its
name for the counts to work.

**Fix.** When a round has no recorded findings, name its kept review file instead:
"round 1 (2026-11-11): its findings weren't recorded; read `docs/evidence/CREATOR/M1-review-1.md`."
`review_rounds` already knows that path.

### 4. A planner was sent to a builder's evidence file that wasn't in its checkout

**Who wrote it:** the script. The `Unblock <module> <milestone>: <blocked note>` task is generated at line 1875 and
cut at 300 characters. The blocked note itself is the builder's.

**The text** (ATMOSPHERE, 06:03 on 11 November):

> Unblock ATMOSPHERE M5: H2 fails its Metal precision bound. Current main retains the design instruction requiring a
> planner decision on this measured miss. Evidence: docs/evidence/ATMOSPHERE/m5-h2-blocker.md

**What it cost (seen in the reply).** The planner wrote: "The builder's blocker note and logs exist only in WIP commit
`7911c75b` on `build/atmosphere`, not on main." Since 1.7.0, planners work in the loop's own checkout of the integrated
tip, so a path in a builder's uncommitted or unmerged work isn't there. The planner had to search the branches for it.
The middle sentence is the builder's shorthand, and it means nothing to a reader who hasn't seen the builder's
session. The planner did well regardless, and the cost was search time. But the same task cut at 300 characters
would have lost the evidence path entirely if the note had been longer. `plan_task` cuts at 400 characters in the
same way.

**Fix.** When the script builds a task from a builder's `BLOCKED` note, it should add the commit and branch the note
was written on, which it knows from the claim and run state: "The builder's note and evidence are on `build/atmosphere`
at `7911c75b`; read them with `git show`." It should not truncate the note. If length matters, it should write the
whole note to a file and name the file. The lead's tasks at 13:47 on 9 November and 01:45 on 11 November did exactly
this, with "local in ...", "read it with git show" and "at 03bc878a", and those planners went straight to the evidence.

### 5. The dry-run sentence collides with a GPU that builders are using

**Who wrote it:** the template (`PLAN_TEMPLATE`), together with the skill's step 3, "Every `check` runs as written".

**The text:**

> To dry-run a milestone's checks, run `python3 {loop} check --module <M> --milestone <id> --worktree .`.

**What it cost (seen in the replies).** Of the Claude planners that wrote or changed checks, most did not complete
the dry run:
- ATMOSPHERE at 22:38: "I capped the `./dev check` items at 25 s to keep the shared GPU free, so they timed out
  rather than completing." The dry run produced timeouts, which say nothing about whether a check is broken.
- APPLE-PRESENTATION at 22:52: "I did not run the full `agent_loop.py check` dry-run for M2: it would run `./dev
  check` and the Chrome suite on the GPU while builders are working."
- The project plan at 22:13: "Not run: the full `agent_loop.py check`, because it runs `./dev check` on the GPU the
  live builder is using."
- PLATFORM-RUNTIME-MAC at 12:41 skipped it "under the contended GPU lock". In that case the checks were unchanged,
  so the skip was reasonable.

The skill states why the dry run exists: a check broken by shell quoting costs a builder a session. In these runs,
new checks went to builders unverified. The planners judged correctly that running the whole `./dev check` on a busy
GPU was the wrong call. The command gave them no cheaper way to answer the question.

**Fix.** This belongs in the script as structure, not in more wording. `check` runs the profile's whole Check before
the milestone's item checks (`check_failures`). A planner needs only the item checks it wrote, so give `check` a mode
that skips the profile Check and runs each item check under its own `lock`, waiting for the lock if a builder holds it.
Then the template sentence can say "it runs only the item checks, each under its lock". The planner no longer has to
choose between disturbing a builder and skipping the check.

### 6. A Claude reviewer ended its turn while its command ran in the background

**Who wrote it:** nobody. The prompt is missing a fact that the reviewer could not work out for itself.

**What happened (seen in the session).** In the CREATOR M1 first round at 03:14, the reviewer's first turn ended with
"Waiting for `./dev check` to finish; the review and done-when fields are already written." Turns 2 and 3 were the
host's background-task notifications, not the script's. The reviewer gave its verdict in turn 2 and repeated it in
turn 3. `one_session` allows three turns, so if one more notification had come, or if the verdict had come later, the
run would have ended `UNFINISHED`.

**Fix.** A Claude reviewer can't know that the script reads the end of its turn as the end of its work. Add one sentence
to the review and plan templates for Claude: "Your turn ending ends your session, so wait for long commands to finish
before you reply." The stronger fix is to start headless Claude sessions with background tasks turned off, which makes
the sentence unnecessary. Check which option the CLI offers before choosing.

### 7. The script's task after a failed design review gives no priority, and the planners widened scope

**Who wrote it:** the script (`design_review_next`, line 5111).

**The text:**

> Revise ATMOSPHERE's design and plan as docs/evidence/ATMOSPHERE/design-review.md asks

**What it cost (partly seen, partly suspected).** All four planners given this task answered every Must Fix, which
shows a capable planner needs no more than the review. They also acted on every Suggestion and added work beyond the
review:
- CREATOR rewrote items for S1–S3.
- APPLE-PRESENTATION "took the wider set" of Chrome rows than the review required, and M2's sizing rose from 2.5 to
  3.5 days.
- ATMOSPHERE added a non-unit exposure control taken from a Suggestion, and "beyond what the review asked", two risk
  rows.

The review skill warns that "Reviews that find one more refinement each round never let the build start". ATMOSPHERE's
design took three rounds, and its second blocker was in the texel-range rule the first revision had introduced. That
the bare "as ... asks" caused this widening is a suspicion, not something the replies show. Every one of these
planners did read the request as "do everything in the review".

**Fix.** The script knows the verdict and the count of Must Fix findings, so it can state them: "The design review
(`<path>`) found 2 Must Fix findings. Resolve those. Its Suggestions are yours to take or leave; say which you took."
Also end the sentence with a full stop. At present the template's next paragraph runs straight on from it.

### 8. The lead gave a planner an action it has no means to take

**Who wrote it:** the lead.

**The text** (PLATFORM-RUNTIME-MAC, 12:41 on 11 November):

> If the fix needs an owner action (such as enabling Developer mode, a security setting only the owner may change),
> mark it next.decides: owner and say exactly what to do.

**What it cost (seen in the reply).** `next.decides` is a field in the script's JSON output to the lead. A planner can't
set it. The planner replied with a heading "**`next.decides`: not owner.**", treating it as a label to write. In this
run, nothing was lost, because the answer was "not owner". Had the answer been yes, the lead would have found the
owner decision only in prose, while thinking it had asked for it as a field.

Two similar cases come from leads quoting script words to planners as if they were the planner's to act on:
- At 18:27 on 9 November and 15:00 on 9 November, the lead wrote "Done when the plan is committed", while the template
  says "The loop commits". The planners followed the template, so these cost nothing.
- At 04:36 on 11 November, the lead wrote "Your first landing will be refused until the oversized plans are trimmed;
  that is intended, so trim and land again", while the template says "don't commit, merge, pull or land". The reply is
  cut off before any account of what the planner did, so whether this caused confusion is not known.

**Fix.** These belong in the lead's guidance, the build skill's section on writing a planner's task, not in the
template. Ask in the planner's own terms: "If the fix needs the owner to change a setting, put it under the owner
decisions in your report, with the exact steps." Say what done looks like in terms of the planner's own output, which
is "your files are written and `PLANNED` names them", and leave committing and landing to the script.

### 9. A planner and the script disagreed about what counts as "the design"

**Who wrote it:** the skill and the script between them, and the planner relied on the wrong one.

**What happened (seen).** At 01:45 on 11 November, the APPLE-TILE planner changed only D0.2 in the done-when file and
reported: "Design review: none is owed. `APPLE-TILE.md` is untouched, so its DESIGN OK at `2514d824` still matches."
Three minutes later, the script ran a design review, because a change to an item's definition counts as a change to
the design. The lead received a report that contradicted the next step it was given.

**Fix.** In `plan-module`, say in the sentence that introduces design approval that the done-when items are part of
what a design review approves, so changing an item needs another review. The script could also add the fact to its
result: "D0.2 changed, so a design review is owed."

## A suspected risk in the reviewer's prompt that the corpus doesn't show

Two generated sentences hand the reviewer someone else's conclusion. The prompting-agents skill says this is what makes
a reviewer agree rather than judge.

- `review_notes`, after a diagnosis that kept the plan: "A planner read the earlier reviews of {mid} and judged that
  their findings went beyond its items: {why}. Judge the items as written." This tells a reviewer, whose known
  weakness is leniency, that earlier reviewers were too strict. No session in this corpus received it. A safer form
  states the scope as a fact and leaves out the verdict on earlier reviewers: "A diagnosis on <date> ruled that
  findings about <X> are outside M2's items, so report them as Suggestions."
- The design review's `briefs` sentence asks the reviewer to "judge the design against" every planner task. Those
  tasks are the lead's words and the script's ("Revise ... as ... asks", which carries no request), while the skill
  says to judge against the owner's request quoted in the design and against `BRIEF.md`. The prompt therefore names a
  second standard without saying which one wins. No reply shows harm. If the sentence stays, say that the owner's words
  and `BRIEF.md` win where a task disagrees with them, and leave the script-generated tasks out of `briefs`.

## What worked, and should be kept

- **The lead's tasks that carried evidence and marked guesses as guesses.** Examples are the COOKED-DRAW task at 13:47
  on 9 November ("The likely cause is pixel-quad derivatives or ordering at draw boundaries, which is unverified") and
  the PLATFORM-RUNTIME-MAC task at 12:41 on 11 November ("whether that causes the missing events is unverified"). The
  second planner showed by measurement that Developer mode was not the cause, and found a working cadence witness in
  traces already saved. A task that had asserted the lead's hypothesis would probably have produced a plan built on it.
- **The project-plan task at 22:13 on 10 November.** It sets out the purpose, what done means, and the boundaries with
  a reason for each ("because builders are on them"), and names the evidence by branch and path. It matches the skill's
  model brief closely.
- **The generated "changed since the last design review" sentence**, when it works. The APPLE-TILE review at 01:48
  ("D0.2 changed") and the PLATFORM-RUNTIME-MAC review at 12:46 got a precise delta and ran clean.
- **The script's nudge when a plan was incomplete.** At 18:27 on 9 November it said "PLATFORM-RUNTIME-MAC-DONE.json has
  no design at ...", and the planner fixed it in one turn. At `HEAD`, the template's sentence on the module folder
  layout prevents that case.
- **The milestone review prompt's core.** It names the commit, the done-when file, where to write and what not to
  change, and otherwise defers to the skill. Every reviewer ended with the right last line and changed only what it
  was allowed to.

## Lines that over-steer, with no cost seen in this corpus

These cost nothing that the replies show, but they appear in every planner prompt and make it harder for the owner
to read. Cut them the next time the template is rewritten from its purpose.

- "PLAN.md holds only the present: one `##` heading per milestone, no status lines and no log, and the loop refuses a
  plan that breaks this, saying why." The skill says this, and the script enforces it with a reason, so the template
  sentence adds nothing.
- "The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report." This
  is a patch for one past incident, and no planner in the corpus mentions PATH. If it is still needed, it belongs in
  the skill's section on the script.
- The last-line sentence: "`BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change, except for a
  diagnosis, which ends with its `KEEP` line)". It nests two exceptions in one parenthesis, and none of these 14
  sessions was a diagnosis. The diagnosis task generated by `diagnose_task` already gives the `KEEP` line, so the
  template can drop the exception.
