# Orchestration suite: assessment against 2026 guidance

9 November 2026. Reviews `skills/orchestration/` at `1c08066` (orchestrate 1.5.0) against the research in
[the report](reports/Multi%20agent%20delivery%20harnesses%202026.md) and its
[notes](research_notes/Multi%20agent%20delivery%20harnesses%202026/).

What I read: the four SKILL.md files, the three references, the graded examples, both agent files, the README, the
authoring spec, and the loop's docstring and prompt templates. I did not read the loop's 3,600 lines of logic, so
nothing here judges its code quality. Each finding says whether it rests on a measurement, on vendor advice, or on my
own inference.

I also read the records of Thrum (`~/Workspace/thrum`, `origin/main` at 9 November 21:05), the engine project that
has been building under the suite for about 20 hours: its profile, the five done-when files and acceptance records,
the commit log, and one milestone review in full. The first draft of this assessment repeated the README's line that
no project had run a full milestone cycle. That line is out of date, and the sections below are corrected.

## Verdict

The core idea is the best-supported one in the field: acceptance defined before building, in a file the builder
can't change, with the loop re-running every check itself and a reviewer who uses the product. Keep that.

Around that core the suite has three problems.

1. **It works, but it is heavy and its cost is unmeasured.** Thrum shows the cycle running end to end, with a
   reviewer that does fail work. It also shows where the weight sits: in planning and design review, not in building.
   The loop is 3,643 lines with 14 subcommands and 17 result states. Both vendors now say the same thing about
   harnesses: each part encodes a guess about what the model can't do, so remove parts one at a time against your
   own tasks. Thrum can be those tasks, but nothing yet records what a milestone costs or whether the reviewer's
   verdicts were right.
2. **It is shaped for software with tests.** Subjective work gets a binary pass or fail against a bar written in
   words, a ladder that treats a taste miss as a plan failure, and no point where the owner picks a direction.
3. **It spends where it doesn't need to.** An Opus lead runs a lookup table for days. Every role uses one model.
   Review is triggered by the kind of proof, not by risk. Claude runs record no token counts.

## What Thrum shows

Thrum is an engine with measurable and visual proofs, built by one Codex builder on `gpt-6.1-sol`, with reviews on
the same model at higher effort. These are counts from its commit log and records, not a controlled test.

- **The cycle works.** Since about 02:30 on 9 November, four milestones were claimed and passed review: T2-CAPTURE
  M0 and M1, PLATFORM-RUNTIME-IOS M7 and COOKED-DRAW M1.
- **The reviewer fails work, and the first rung of the ladder held.** T2-CAPTURE M0 failed twice (three failing
  items, then two) and passed on the third review. The other three passed first time. That is two fails in six
  milestone reviews.
- **The reviewer follows the method.** The COOKED-DRAW M1 review wrote its inspection lists before viewing captures,
  took its own captures, read the whole diff, separated advisory from blocking findings and recorded what it could
  not cover.
- **Nobody has graded a verdict.** Thrum's graded-examples file still says "None yet". So six verdicts exist and
  none is confirmed or overturned, and the two fails could be sound or over-strict.
- **Planning is where the time goes.** Of the loop's 19 recorded actions in its last eight hours, eight were design
  reviews (five of them on COOKED-DRAW's design), three were plan authorisations and four were block or unblock,
  against two claims and two milestone reviews. Open milestones carry one to four re-plans each with no failed
  review behind them, and APPLE-TILE is parked after two failed design reviews.
- **Plans are heavy.** COOKED-DRAW has one milestone. Its design is 4,248 words, its plan 3,389 and its done-when
  file 3,550, with a median of 135 words per item and one of 436. The review of that milestone is 3,047 words.
- **Every milestone gets a review.** Every milestone in all five modules has at least one `ask` item, so the "checks
  alone" path has never been taken.
- **Process files outnumber code.** In the 33 commits since the loop's first recorded action, 381 file changes were
  under evidence and plans and about 70 under code and scripts. This is a crude count.
- **Attended work is the hard block.** PLATFORM-RUNTIME-MAC M2 waits on an unlocked Mac, and the profile's Targets
  section has grown a long paragraph of current status about it.
- **Sessions ran on the visible app path** in every record, so that path is in real use.

## What the evidence says about each part

| Part of the suite | Evidence | Call |
|---|---|---|
| Done-when items fixed before building, builder can't edit them | Anthropic's JSON feature list; OpenAI's goal contract; TDFlow: 94.3% with human-written tests against about 69.8% with self-written ones (measured) | Keep. The checks are planner-written, so their quality is the ceiling |
| Loop re-runs checks in a clean checkout, never trusts `DONE` | OverclaimBench; METR found merge rates about 24 points below grader pass rates; Cohere found verifiers catching false "done" claims gave the biggest gain (measured) | Keep |
| Reviewer drives the running product | Anthropic harness post; Cognition calls clean-context review its most successful pattern (vendor reports) | Keep |
| Fresh-context reviewer beats self-review | Cognition reports its review loop works best when coder and reviewer share no context (about 2 bugs per PR, 58% severe, production report). Fable 5 page agrees, with no number. Opus 5 page says remove separate verification steps. No controlled test found | Keep. Vendor-reported, model-dependent, never measured head to head |
| Review on every milestone with `inspect` or `ask` | Anthropic dropped per-sprint evaluation for Opus 4.6 and kept one end pass; the evaluator paid off "at the edge of the model's solo ability" | Change |
| Check-only milestones skip review | METR and UTBoost show passing tests often aren't mergeable work (measured, older models) | Change |
| One builder per module, worktrees, one integrate lock | Cognition keeps writes single-threaded; Cohere found more than 2–4 implementers got worse; Cursor's locks only failed at 20 agents | Keep at 1–3 builders |
| Planner says what, builder decides how | Anthropic kept the planner when it cut everything else | Keep |
| Escalation ladder (2 fixes, fresh session, re-plan, park) | Nothing found beyond folklore. On Thrum, one milestone failed twice and passed on the third review, so only the first rung has been used | House practice. Keep for objective work, log outcomes per rung |
| Medium effort everywhere, high for planners | Vendors say sweep effort per model on your own tasks. Opus 5 page says review accuracy holds at lower effort | House practice. Make it per role |
| Cross-vendor reviewer | Cognition ran Claude and GPT together in production and reports gains on the hardest cases. Same-family judge bias of 3–8 points, measured on old open models, not code | Modest support. Keep as a preference |
| Bar in words, never a target image | No evidence either way. Anthropic used few-shot scored examples | House rule. Loosen |
| LLM lead dispatching the queue | No source supports an LLM for a deterministic table. OpenAI: "Instructions aren't enforcement" | Change (my inference) |
| Visible app sessions over internal surfaces | No source. Every Thrum session ran on this path, so the owner uses it. The README says it can break on any app update | Keep for the owner, separate from the core |
| Codex quota forecast (about 1,000 lines) | None found on forecasting quota from local files | Shrink |

## Findings, most important first

### 1. Thrum proves the cycle, and three numbers are still missing

Thrum answers "does it run" and "does the reviewer ever fail anything". It can't yet answer what the choices below
cost or whether they pay. Three gaps, cheapest first:

- **Grade the six verdicts already on record.** This spends no quota. It is the calibration step the suite's own
  design depends on, and it is the only way to learn whether the two fails on T2-CAPTURE M0 were right.
- **Record tokens per role per milestone** in the loop, on both hosts. Then planning, building and review each have
  a cost, and the planning churn above has a price.
- **Run one comparison** when a suitable milestone comes up: the same milestone built by a solo agent at high effort
  with the done-when file and no reviewer. Anthropic's advice is to remove one part at a time and run each task more
  than once. This spends quota, so it's the owner's call.

Planted-defect commits would measure how often the reviewer catches a fake. That is worth doing once the first two
are in place.

Also fix the README: "No project has run a complete milestone cycle under this version yet" is no longer true.

### 2. Planning churn and design re-review are the largest visible cost

This comes from Thrum's records, not from the research. Eight of 19 loop actions were design reviews, COOKED-DRAW's
design was reviewed five times, and milestones collect re-plans without a failed review. Three things in the suite
produce this:

- **Any change to a design needs a fresh design review.** The loop hashes the whole design file, so a wording fix
  and a new mechanism cost the same. Reading COOKED-DRAW's history afterwards showed this was not what drove its
  five reviews: three followed planner revisions that changed the definitions too, which is a fair reason to review
  again. So the rule is a latent cost, not the observed one, and I left the code alone. One thing to settle: 1.5.3's
  text says the planner folds advisory findings in "without another review", and the loop will still ask for one
  if that edit touches the design.
- **Items are long.** `done-when.md` asks for "small specific items", and Thrum's median item is 135 words with an
  `ask` of several questions. Anthropic kept its planner's spec high-level because detailed specs carry their
  errors forward, and long items give a re-plan more to get wrong. A length the loop warns on would help.
- **Three planning files per module, plus a brief.** For a one-milestone module that is over 11,000 words before
  building starts. Böckeler's criticism of spec-driven tools (many verbose files, small work turned into long
  criteria) applies here.

I then read the three COOKED-DRAW re-plans. Each followed a builder blocked on an item whose proof couldn't run as
written: a parity oracle, a simulator check, and a locked-console precondition (the last already addressed by
1.5.2). That makes long, procedure-heavy items the likeliest cause, and it is what the new item guidance targets.
APPLE-TILE's re-plans came from design-review findings instead, and I did not read the other modules'.

### 3. Subjective work needs a critique loop, and the suite only has a gate

Anthropic's design work ran 5 to 15 generator and critic rounds, scores rose and then levelled off, and the author
sometimes preferred a middle round. In the suite each round is a full claim: integrate, re-run checks in a clean
checkout, start a fresh reviewer, land the verdict, resume the builder. After four rounds the ladder declares the
plan wrong, and after eight it parks. That is the right response to a failing test and the wrong one to a taste miss.

What's missing, in order of value:

- **A direction step.** Designers agree with each other only weakly on preference (Krippendorff's alpha about 0.25,
  measured), so no judge can settle taste for the owner. The cheapest fix is one early milestone that produces a few
  variants and has the owner pick. `attended` already batches owner work, so this needs little new machinery. The
  README lists "trying several designs in parallel" as deliberately left out; for subjective work that omission is
  the wrong one.
- **An inner critique loop** before the claim: the builder asks a fresh critic to judge the working tree, for a
  budgeted number of rounds, and keeps the best round, not the last.
- **Anchors.** The "never a target image" rule guards against copying one image's accidents. It also rules out
  reference sets, the owner's chosen variant, and comparison with the previous best, which are the anchors that work.
  Make it the project's choice in the profile.
- **Scored criteria for taste items.** Anthropic used a few weighted criteria with thresholds and scored examples to
  stop drift. The suite's per-item verdicts and `cant_tell` already match the "one judge per dimension, with an
  unknown option" advice. The four starter graded examples are all functional, though; none shows a taste call.
- **Send what agents can't perceive straight to the owner.** Audio and game feel can't be judged by any current
  agent. Today those become `cant_tell`, which counts as a fail and climbs the ladder. The planner should mark them
  `attended` from the start.

The objective floor for creative work (file loads, polycount, frame time) already fits `check`, and mixing proofs on
one item is a real strength. Keep it.

### 4. Review is gated by proof type, which is wrong in both directions

A UI or game project has `inspect` on nearly every milestone, so it gets the per-sprint review Anthropic dropped. A
module with only checks gets no reviewer until its last milestone, which is where test-gaming hides. The README
already flags this as a trade-off to revisit.

Thrum shows how the rule behaves in practice. Its planner put an `ask` on every milestone of every module, so every
milestone is reviewed and the checks-alone path has never run. The trigger is a side effect of how the planner
writes items, not a decision about risk. Thrum's reviews look worth their cost on hard engine work (one caught
failing items twice), which fits Anthropic's "edge of the model's ability" rule. The point is that the planner
should make that call on purpose.

Change it to a per-milestone policy the planner sets from risk: review each, review at the end, or none. Pair it
with a cheap mechanical scan on every claim for the fingerprints the reviewer is asked to find (tests deleted or
weakened, check scripts touched), and send a claim to review when the scan hits.

The README also admits a builder can change a script that a pinned check calls. Agents weakening tests is one of the
better-measured failures, so pin the contents of the files a check runs, or fail a claim that edits them.

### 5. The lead is an LLM doing a scheduler's job

`build/SKILL.md` is 2,347 words, and most of it is a table from loop results to next commands, ending in "don't
second-guess it". The loop already computes `next`. A `LOOP build` supervisor could run the queue in code and call a
model only to triage `BLOCKED` and `NEEDS_CONTEXT` and to write the daily report. That removes a long-lived Opus
context, removes the ways a lead can stop early or overrule the ladder, and shrinks the skill to a few hundred
words. This is my inference from the skill's own text; no source measured it.

### 6. The reviewer should be read-only and return a structured verdict

Today the reviewer edits the done-when file by hand, following a transition table, and the loop then checks its
edits. OpenAI's reviewer pattern is a read-only agent returning structured output; both `codex exec` and `claude -p`
accept a schema. The loop can write the fields itself. That deletes the "did the reviewer change only its own
fields" path, about a third of `review-milestone`, and one whole class of `INVALID` results.

The builder also needs a way to contest a finding. Cognition found the bridge back from reviewer to coder is what
stops looping and out-of-scope work: the coder filters the reviewer's findings using what it knows of the task. Here
every blocking finding binds, a wrong one costs a rung of the ladder, and the reviewer's false-fail rate is unknown.
A contested finding could go to the planner, as contract proposals already do.

### 7. Spend levers that aren't used

- **One model for every role.** Add per-role model and effort lines to the profile. Vendor advice supports lower
  effort for review. Cheaper builders are not clearly a win: Cohere found a weak lead with cheap workers lost to a
  strong solo agent, and Cognition found a cheap primary with a strong advisor only pays off when the primary is
  itself strong. So add the setting and measure before changing a default.
- **No token record on Claude.** `claude -p` reports usage per turn. Record it per role and milestone for both
  hosts. Cost per accepted milestone, review's share and rework's share are the numbers every other decision needs.
  Anthropic's own run put QA at 5–8% of spend; this suite's share is unknown.
- **The quota forecast** is about 1,000 lines reading Codex's internal files and fitting tokens to percent. A plain
  "used and reset time" read does most of the job.

### 8. Cut or shrink

- **Visible app sessions** (about 440 lines over Codex IPC, deep links and Claude desktop import). Thrum ran every
  session this way, so this is not a cut. It is fragile and host-version-specific, and it overlaps `codexctl`, which
  already reads and steers Codex threads. Move it behind the host adapter as an optional piece, so the published
  core rests only on documented CLI flags.
- **Multi-lead claim refs.** They guard against two leads on one project, which nothing suggests has happened.
- **Status lines in `<MODULE>-PLAN.md`.** State now lives in three places: those lines, the done-when file and the
  acceptance record. `LOOP status` derives it. Keep the log, drop the lines. On Thrum the `Now:` line has grown to
  a paragraph, and current status has also leaked into the profile's Targets section.
- **The Opus 4.5/4.6 leniency note in `review-milestone`.** It's a dated, model-specific caution in a file every
  reviewer reads, including GPT reviewers. Anthropic reports stale cautions make current models hold back, and the
  Opus 5 page warns of over-verification. Keep the rule (the definitions decide what blocks) and move the history to
  the README.

### 9. Process weight and milestone size

Team gains over a solo agent were small and uneven in 2026 tests (Vals: between −0.3 and +7.3 points at 1.8–5.1x
cost), and Anthropic dropped sprint decomposition for Opus 4.6. OpenAI's harness team reports single Codex runs of
six hours or more on one task, with light throwaway plans for small changes and checked-in plans only for complex
work. The planner is told to make each milestone "one coherent outcome", with nothing about size. Say it: a
milestone is about what the builder can finish in one session unaided, which for current models is hours of work. A
one-module project shouldn't need a design, a plan, a done-when file and a design review before the first line is
built.

### 10. Repeated findings should become checks

OpenAI's harness team feeds review comments and bugs back into tooling: "When documentation falls short, we promote
the rule into code", as lints whose error messages tell the agent how to fix the problem. They also run recurring
clean-up agents against drift. The suite has half of this. A reviewer who finds a defect outside the items proposes
an item that would have caught it, and the owner's overturned verdicts become graded examples. Nothing moves a
finding seen twice into the profile's `Check`, where it costs nothing on every later claim. Make that a planner
duty at the end of each module. This is one team's report on a greenfield project, so treat it as a cheap bet.

### 11. The suite against its own authoring rules

- The spec says each SKILL.md stays near 400 words. They run 870, 1,175, 1,272 and 2,347.
- The spec says model and effort are named in each skill's first line. The README says the skills carry neither, and
  they don't. The spec is stale.
- Descriptions and the README say "software". A request to build a game's art or a set of 3D assets may never
  trigger `plan-module`. If the scope widens, the descriptions have to.
- What follows the two skills well: reasons given with rules, outcome-first templates in the loop, done-when sections,
  permission lines, and a README that separates borrowed practice from house practice.

## Suggested order

1. Grade Thrum's six recorded verdicts into its graded examples, and record tokens per role on both hosts. Neither
   spends quota. Read a few of Thrum's re-plans to see what caused them.
2. Make the free cuts in finding 8, fix the spec, and correct the README's "no complete cycle" line.
3. Design re-review only when definitions or contracts change; a warning on long items.
4. Read-only reviewer with a structured verdict; pin check-script contents; review policy by risk.
5. Direction milestone, critique loop and anchors for subjective work, tried on one real asset or game project.
6. Move the lead's table into the loop.
7. Per-role models, changed only where step 1's numbers show a gain.

## Changes made on branch `orchestrate-polish`

Made on 9 November, uncommitted, on top of orchestrate 1.5.3. The assessment above was written against 1.5.0;
`origin/main` moved to 1.5.3 while it was being written, and 1.5.3's blocking-or-advisory design reviews already
address part of finding 2.

Done:

- **Tokens per claim and review** (finding 1 and 7). The loop reads the usage that `claude -p` and `codex exec`
  report and stores it as `usage` in the acceptance record and result lines. Turns that run in the Codex app report
  none. Four new tests; the suite passes.
- **Item and milestone guidance** (findings 2, 4 and 9). Milestones are sized to one builder session. Items stay
  short and say what is observed. `ask` and `inspect` are chosen on purpose, with an `ask` to read any test the
  builder wrote itself.
- **Taste-led work** (finding 3). A new section in `proofs.md`: a direction the owner picks from variants, anchors,
  critique rounds that keep the best version, and sending what agents can't perceive to the owner. An `Anchors`
  profile line, a `Direction` proof kind and a fifth graded example go with it. The "never a target image" rule
  keeps its reason and now allows reference sets.
- **Repeated findings become checks** (finding 10), as a planner duty.
- **The dated leniency note** (finding 8) moved from `review-milestone` to the README.
- **README and spec** (findings 1 and 11). The stale "no complete cycle" and "nobody has measured" lines are
  corrected, and the spec's model-and-effort line matches the skills.

Tested: [iteration 1](evals/iteration-1/results.md) compared old and revised `plan-module` in six fresh planner
runs, graded blind. The revised skill produced an owner's pick from variants in both taste-led runs where the old
one produced neither, and items about a quarter to a third shorter. It cost the same to run. One possible
regression: the revised plan for the measurable case covered less with checks, on one run.

Not done, and why:

- **Read-only reviewer with a structured verdict** (finding 6), **the lead's table moved into the loop** (finding
  5), and **shrinking the quota forecast and separating the app-session code** (finding 8). Each changes how a
  running build behaves, and Thrum is mid-build on the installed version. They need the owner's go-ahead and a
  quiet moment.
- **Pinning the files a check runs** (finding 4). In practice the builder usually writes the test a check names,
  so a pin would send almost every checks-only milestone to review. The guidance now asks for a reviewer to read
  builder-written tests instead.
- **Per-role models** (finding 7). Wait for `usage` numbers from a real run.
- **Design re-review on any edit** (finding 2). Not shown to be the cost on Thrum.
- **Word counts against the spec's 400-word target** (finding 11). The skills grew slightly. The target is the
  owner's to move or enforce.
- **No version bump or release.** Installed copies, including Thrum's, are unchanged until one is made.

## Iteration 2: end-to-end runs, and what they changed

10 November, still uncommitted, now on top of orchestrate 1.5.4. The owner asked for made-up projects planned and
built through the loop on both hosts, the problems ironed out, and tools an engineer would want, such as a way to
see running loops. The record is [iteration 2](evals/iteration-2/results.md).

What was run: nine runs of five projects (a slug tool, a two-module ledger, a taste-led icon set, a browser game,
and the slug tool, ledger and icon set again as confirmation), each led by an Opus 5.5 subagent standing in for
the owner, with Claude and Codex as planner, builder and reviewer in different mixes. Seven ended with every
milestone accepted and a product that did what was asked. One shipped a slug tool that dropped `Ø`. The game stopped at its first
milestone.

What the runs found, in order of cost:

- **Stops without a next step.** Eight of nine leads hit a stop whose `next` was missing, vague or wrong, each a
  different stop. Every stop now carries a command, and none of them reverts, resets or branches.
- **Plans narrower or wider than the owner's words.** One plan read "accents" as Latin-1 only; another added an
  80-column rule nobody asked for. Planners now quote the request, take the ordinary reading, and log each
  assumption on a line the loop counts and reports.
- **Taste-led work held every variant to the final bar.** The first icon run took 97 minutes and five failed
  reviews on variants the owner would reject anyway. Held only to the floor, the rerun passed both milestones
  first time in 17 minutes.
- **A Codex builder that never asked for a browser.** The game blocked on four items inside the sandbox. Builders
  are now told to ask, and the loop warns once.
- **No way to see what's running or what it cost.** Added `loops`, `cost`, `report`, `check`, a readable `quota`,
  and `status` marking live runs.
- **An owner who isn't at a terminal.** I first added `relay`, a second command for a lead recording an answer
  given in chat. The owner's reading of that was better than mine: "I don't want to be driving anything from the
  terminal at all. This whole orchestration needs to be chat only." So the typed confirmation and `relay` both
  went. The lead runs every `owner` command with the owner's words, and `report` lists each decision recorded in
  the owner's name. The script got smaller. What's given up is that the loop no longer tries to tell the owner's
  decision from a lead's invention; the report is the check.

Nineteen fix rounds went into the loop script, with three clean-context reviewers between the first seventeen. They found three
ways a session could get work accepted that hadn't earned it, all introduced or exposed by this iteration's own
changes. The last took four rounds, and the fix that held removed a behaviour (taking a module "as it stands" once
a repository has any record) where the earlier attempts had added rules. The final reviewer's verdict was to ship,
with three remaining routes that need a deliberate agent; the README names them. The suite grew from 171 tests to
268. The final script reads Thrum's `main` the same as the installed copy does.

What this still doesn't show:

- The visible app path, which is what Thrum uses. Every run was headless.
- A real owner in the chat. Each lead also played the owner. The last run had the lead record a pick and a change
  of mind; `accept`, `rereview`, `unpark` and `scope` are unit-tested only.
- A clean-context review of the chat-only change.
- Whether `ORCHESTRATE_ROLE` reaches sessions the Codex app runs. It reaches headless ones.
- The last fix round in a live run.
- A game finished, a build longer than 97 minutes, or a project larger than three milestones.
- Reviewer accuracy. Reviewers failed real defects in these runs (a test suite that survived reordering, a
  traceback on a closed pipe), but no verdict was graded by a person.
- Much gain from two builders. Planner turns run one at a time, and the second ledger run's builders overlapped
  for about four minutes.

Still not done from the list above: the read-only reviewer with a structured verdict, per-role models, trigger
tests for the descriptions, a version bump and a release.

## Limits of this review

- The research found no controlled test of fresh-context against same-context review, of plan granularity, of
  re-plan policy, or of any harness on games or 3D assets. Findings 3 and 5 rest partly on inference.
- I read OpenAI's harness engineering post and Cognition's April 2026 post in full after the researchers could not;
  the report still describes both as second-hand. Several 2026 benchmark numbers came from search summaries, and the
  notes mark which.
- Most vendor evidence is a single team or a single author on one or two projects.
- Thrum is one project with one Codex builder, and its numbers are counts from the commit log and records. I read
  one of its six milestone reviews in full, none of its design reviews, and not the reasons for its re-plans. It is
  engine work, so it says nothing about taste-led projects.
- Nothing covered Jules, Amp, Factory, Replit or the Copilot agent first-hand.
