# Critique of the six proposals from the groundWork 36-hour record

Written 2026-11-11 against `proposals.md`, `delivery-record.md` and the orchestrate 1.7.1 source at commit
`6989342` (branch `orchestrate-1.6.4`). Line numbers are in `skills/orchestration/build/scripts/agent_loop.py`
unless another file is named. Each section keeps **Verified** (read in the source, the git history or the record's
rows) apart from **Inferred** (my reading, not checked against a run).

## First, a fact that changes how to read every proposal

**Verified.** Almost none of the record ran on the code the proposals would change.

| Work in the record | Version it ran on |
|---|---|
| INTEGRATION-ROLLUPS design and M1 | 1.3.1, then 1.5.0 |
| INTEGRATION-ROLLUPS M2 (all nine reviews) | 1.5.4 |
| SHARED-UI M1, M2 reviews 1–8 | 1.5.4 |
| SHARED-UI M2 review 9, M3 reviews 1–5 | 1.6.2 |
| M3 migration, design re-review, the last builder | 1.7.0 / 1.7.1 |

The ladder those runs used counted **every** failed review (1.6.2's `escalation`, `git show 708b09e`: fresh session
at 3 fails, replan at 4). 1.6.3 (`557f3cc`, committed 23:07 on 10 November, in the middle of the run) replaced it
with the two counts now at lines 1134–1158: `fails` counts only rounds with a repeated finding, `rounds` counts all,
a fresh session at 3 of either, replan at 4 repeats, diagnosis at 6 rounds. Its commit message cites this run
("A milestone that failed eight reviews, each on something new, was parked"). The usage ledger, `cost` and
`report` arrived in 1.6.0; the headless default and the Claude open-session guard in 1.7.1.

So the record mostly shows the problems 1.6.0–1.7.1 already answered, and the proposals partly re-propose them.
A second consequence: six versions in 36 hours means the record cannot attribute behaviour to orchestrate's design
cleanly. Three of the operational incidents were caused by upgrading mid-run (see "What the six miss").

---

## 1. Fix the class, not the instance — **build changed (much smaller)**

**What 1.7.1 already does (verified).**
- A Must Fix already counts as a repeat when its `name` matches an earlier round's *or it fails an item that failed
  before*, unless the reviewer writes `different` (`repeats`, lines 1161–1165; `review-milestone/SKILL.md`
  lines 113–121). The item rule is a class rule at item granularity.
- Reviewers are given every counted earlier round with its findings (`review_notes`, lines 1566–1583), so names
  can stay stable across fresh reviewer sessions.
- The builder is told repeats are what escalate (`FINDINGS_TEMPLATE`, lines 407–412; `build-milestone/SKILL.md`
  lines 112–113). Nothing tells it to look for the same cause elsewhere.

**Does the record support it?**
- Verified: INTEGRATION-ROLLUPS M2 reviews 5–8 are mostly one class (pointer targets), but review 5 also failed on
  "a non-record schema counted as a store read", which is not.
- Verified: the example class "views read different revisions" fits SHARED-UI M2 reviews 1–3 and M3 review 1, but
  not M2 reviews 4–5 (failed Flight response, malformed HTTP 200: error recovery), M2 review 8 (a regression), or M3
  reviews 3–5 (503 handling, wrong status code, Search highlight and Enter after Cancel). Grouping the modules'
  failures into one class overstates it; there are at least three: revision coherence, failure recovery, and
  unrelated regressions/UI state.
- Verified: the premise "reaches the replan step at once" is wrong twice over. Reviews 5–8 came *after* a replan
  (04:10–04:20), so the next step was park, not replan, and 1.5.4 did park it at review 8. And under 1.7.1 counts
  restart at a replan (`done-when.md` line 333), so review 5 can't repeat anything; if 6, 7 and 8 were repeats,
  `fails` is 3 at review 8, which is a fresh session, and it parks at review 9. No class field makes a ladder with
  a threshold of 4 act "at once"; that needs a lower threshold, which is a different proposal.
- Verified: M2 finally passed (review 9) after "the routing fix landed" and an owner reopen. Inferred: if that fix
  was outside the milestone's code, a builder sweep of its own code would not have found it.

**Would it work as stated? (inferred)**
- The class label is free text the reviewer chooses, and it would decide escalation. Broad labels ("state bugs")
  make everything a repeat; narrow ones make nothing one. A fresh reviewer each round will drift. Exact matching
  is gamed by wording; fuzzy matching is arbitrary.
- The sweep is a list the builder writes. Nobody can check it is complete, so it is satisfied by writing it.
- The real gap is narrower: the `different` escape. A reviewer who sees the same cause at a new path can truthfully
  call it a different defect, so it doesn't count. That is where pointer-target rounds 6–8 could have escaped.
- Hosts: no host issue; it is prompt and script text.

**Cost.** As stated: a new findings field, its validation (`findings_problems`, lines 1031–1051), matching rules,
reviewer and builder skill text, tests. Moderate, and it overlaps `name`/`item`.

**Simpler change that gets most of it.**
1. In `review-milestone` (line 119–121) and the reviewer note (line 1577): `different` only when the *cause* differs;
   the same cause at another place, path or view is a repeat and keeps the name.
2. In `FINDINGS_TEMPLATE`: before claiming, look for the same cause wherever else it could occur, and add a test
   that would catch it, as `build-milestone` line 80 already asks for ordinary fixes.
No new field, no change to the ladder.

## 2. Builder self-review before claiming — **build changed (fold into the existing step; no fresh subagent on Codex)**

**What 1.7.1 already does (verified).** `build-milestone/SKILL.md` lines 83–91: before Ready for Review the
builder runs `check`, then judges every `inspect` and `ask` item "the way a reviewer will, on the exact build and the
real target". `proofs.md` lines 120–126 already prescribe a fresh-opinion subagent, for taste items only, "when the
host can start one".

**Does the record support it?**
- Verified: "7–9M tokens" is roughly the median *cached* input per milestone review (range 4.5M–23.3M; uncached
  about 150–590k, output about 15–55k). "Plus another builder round" ranges from 1.8M (c3d4) to 54.7M (c827).
- Verified: the quota meter moved 8 points (54% to 62%) over roughly 610M identified tokens from 02:03 on. Tokens
  were not the binding cost in this window. Time was: in SHARED-UI M2 the nine claim-to-verdict intervals were
  1h44m of 8h18m, in M3 61 minutes of about six hours. Reviews are 15–20% of the wall clock; builders are the rest.
  A self-review adds builder time to save review time.
- Inferred: many findings were failure-injection edges (503 on refresh, malformed 200, failed Flight response,
  Enter after Cancel). A builder that ran the profile's edge conditions would catch some. Whether the profile
  listed them can't be seen from here.

**Would it work as stated? (inferred)**
- On Codex, the run's host, a subagent starts with a copy of the whole parent conversation (`README.md` line 238).
  A builder's "fresh" subagent there is the builder again, with its blind spots, on a 35–69M-token context.
  `review-milestone` line 49 says being a separate agent doesn't cure leniency even when it is fresh.
- Gaming: the builder writes the subagent's brief and decides what to do with its answer; the script can't see
  that it ran. "Self-review passed" costs nothing to write.
- It needs the product on the real target (a browser), which on Codex's `workspace-write` sandbox needs escalation
  (`build-milestone` lines 123–125); a subagent may not ask.

**Cost.** Another browser-driving session per claim, several million tokens and 10–20 minutes, before every claim,
including the ones that would pass.

**Simpler.** Make the existing pre-claim step concrete: re-run every earlier round's findings and the edge
conditions the profile lists for each item's target, and log which ran (in `LOG.md` or the evidence folder). Keep
the subagent optional and Claude-only. If a second opinion is wanted, a script-started session is the only one that
is really fresh on both hosts, and that is just a review.

## 3. Ask the owner about cost at the replan — **build changed (non-blocking, and on the diagnosis too)**

**What 1.7.1 already does (verified).**
- A diagnosing planner can end `KEEP <M> <id>: owner: <why>`, which parks the milestone with the diagnosis for the
  owner (`plan-module/SKILL.md` lines 263–267). The replan path has no such outcome; its task says only "change the
  definitions so it can be met" (`replan_task`, lines 1600–1611).
- Planners record readings the owner may overturn as `Assumption:` lines in `## Open for the owner`, which `report`
  lists (`plan-module/SKILL.md` lines 152–158), and are told to add a requirement only when the owner's words or the
  design need it (lines 160–163).

**Does the record support it?**
- Verified: M3 replanned 03:56–04:09 "around retaining the mounted content and selection"; the scope change came
  with the pause at 06:45, about 2h40m later, and allowed reloads and transient resets. Between them: one builder
  claim (c89a, 24.1M cached), review 5 (8.8M), and the migration work.
- Not in the record: whether mounted-state preservation was the owner's requirement or the planner's. If the
  planner added it, the existing rule already forbade it, and this is a compliance gap rather than a missing step.
- Inferred: under 1.7.1 M3's rounds 1–4, if judged new findings, would go to a fresh session at 3 and a *diagnosis*
  at 6, not a replan at 4. So a question attached only to the replan would arrive two rounds later than in this run,
  or never.

**Would it work as stated? (inferred)**
- "Asks the owner" at a replan blocks the loop on a person. The M3 replan was at 04:00; the IR M2 park waited
  1h55m overnight. A blocking question at every replan trades tokens for hours.
- Gaming: none worth naming; a planner can write a perfunctory question, but the owner reads it.
- Hosts: none; the lead relays it in chat on either host.

**Cost.** Small: replan and diagnose task text, plan-module text, and a `next.owner_answers`-style question.

**Simpler and better.** The planner rewrites as now, and also names the requirement that drove the failures with an
`Assumption:` line ("kept mounted-state preservation; it caused rounds 3–4; relaxing it to X would remove them"). The
lead raises it in chat at once without stopping the build; `owner scope` already turns the answer into the replan
(`agent_loop.py` lines 258–262). Put the same instruction in the diagnosis task, since 1.7.1 sends new-finding runs
there.

## 4. Rotate builders after two claims — **drop**

**What 1.7.1 already does (verified).** The ladder starts a fresh builder after 3 failed rounds (`FRESH_AFTER_ROUNDS`,
line 1138; `run --fresh`, line 7113), with only the files and the latest review (`done-when.md` line 324). The record
shows it working: fresh builders at IR M2 claim 4, SU M2 claims 4 and 8, M3 claim 4.

**Does the record support it?**
- Verified: same-session totals did reach 34.7M (c5bc), 65.9M (c673) and 69.1M (c784) cached across three claims.
- Verified, against it: the fresh M3 builder c827 used 54.7M cached on **one** claim, and c89a 24.1M on one.
  Fresh sessions re-read the repository; per claim they were not cheaper here.
- Verified, against it: no fresh builder's claim passed in the record. The passes came from c571's second claim in
  the same session (SU M1), the reopened build c452 (IR M2), and c74b, which the record calls a resume of "the same
  builder" (though its id differs from c703's; the record is ambiguous there).
- Cached input is 97.7% of tokens; the meter cost of cached reads is what a long session inflates, and it was not
  binding (see 2).

**Would it work? (inferred)** It moves the existing fresh-session step from 3 rounds to 2 and throws away the
builder's knowledge of what it already tried, which `build-milestone` lines 115–121 rely on. The "class sweep" it
hands over depends on proposal 1. Codex compacts long threads on its own, so context size is bounded anyway.

**Cost.** Small to build, but more cold starts and less continuity. Nothing in the record says it buys quality.

## 5. Operational hardening — **build changed: two of four, and replace the migration rule with a version rule**

**5a. Stall timeout.**
- Verified: every turn already has a 2-hour deadline (`--turn-timeout-hours`, default 2.0, line 7107; enforced in
  `run_proc` line 2029 and the visible Codex path lines 4262–4270). `STALLED` stops after three turns that change and
  report nothing (line 4356, 4698–4700). `loops` already computes time since the last activity (`idle_s`, line 2498).
- Verified: the one stall in the record was a *desktop* (visible) design re-review, 11:34 to about 13:31. Visible is
  no longer the default (1.7.1).
- Inferred: an inactivity kill must be longer than the longest silent command, and `check` allows 3600 s per check
  (line 2769), so N is about an hour, little better than the 2-hour deadline. Cheaper: a shorter turn timeout for
  design reviews (they ran 5–10 minutes here), e.g. 30 minutes.

**5b. Refuse a resume while another session writes to the thread.**
- Verified: Claude already has this: a session open in Claude desktop gets PAUSED, not written to (lines 3533–3537,
  4334). Codex headless has no such guard: `_run_turn` goes straight to `codex exec resume` (lines 3530–3543).
- Verified: the 06:07 failure was exactly this case: a thread the desktop held, resumed headless after 1.7.1 made
  headless the default.
- **Build.** Detect a Codex thread the app holds (the `CodexIpc` client at line 4011 already talks to the app) and
  return PAUSED with a message, as for Claude. Small.

**5c. The script formats its own ledgers.**
- Verified: the script writes `json.dumps(..., indent=2)` (line 958) and generates `STATUS.md` (1.7.0), with no
  awareness of a project formatter. The 22:09 claim blocked on formatting of an orchestrate-written ledger.
- Inferred: the script can't know each project's formatter; Prettier, for one, collapses short arrays that
  `indent=2` expands, so the files will disagree with it again.
- **Build changed.** Not "format its ledgers" but: plan-module/profile guidance that the test command and format
  gate must exclude the plans folder's script-written files (`ACCEPTED.json`, `STATUS.md`), and a preflight warning
  in `profile` when a known formatter config doesn't exclude them. Optionally an `Format:` profile line the script
  runs on its own files before landing.

**5d. No file-layout migration while a module is mid-milestone.**
- Verified: `migrate` already refuses while any run, review, plan or adopt is running (lines 215–222), and 1.7.1
  reviews claims made before the migration (`6989342`). But 1.7.0 makes every other command refuse the flat layout
  (`fea7c17`), so after the 05:31 upgrade the migration was forced, not chosen.
- Verified cost of that one migration: planner c8e5 (13.4M cached), design re-review c8fd (1.0M), the failed resume,
  and a fresh builder c915 (11.2M).
- **Replace with:** don't upgrade orchestrate while a milestone is open; upgrade between milestones (see below).
  A rule against migrating mid-milestone would, under 1.7.0, just mean the loop can't run at all.

## 6. Record cost in the ledger — **build changed (fill two gaps, not a new ledger)**

**What 1.7.1 already does (verified).**
- Every turn appends to `<git common dir>/orchestrate/usage.jsonl` with end time, role, module, milestone, host,
  model, effort, session, path, exit code and tokens (`note_usage`, lines 2232–2250).
- Claim records carry commit, time, host, model, effort, CLI version, what was observed, and `usage` per claim plus
  `session_usage` (lines 4639–4641, `launch_record` 3681–3685); reviews carry the launch record and time
  (lines 5043–5046).
- `cost` gives tokens per milestone; `report` gives verdicts, owner decisions, assumptions and cost (usage text,
  lines 231–244).
- Headless (default since 1.7.1) reports tokens; visible Codex turns didn't, which is much of why the record has
  dashes and a "later correction".

**Gaps (verified).** Committed records lack the orchestrate version, the session id and a turn's start time; the
ledger is per machine. The record's author had to infer versions from "upgrade records".

**Build.** Add `orchestrate` (package version) and `session` to `launch_record`, and `started` to the ledger line;
let `report` print a per-session table. Small. A new `report` mode that writes the whole delivery record is not
needed: the factual parts are there.

---

## What the six miss

1. **Version churn caused three of the incidents (verified).** Six orchestrate versions in 36 hours. The ledger
   format block (22:09, after upgrading to 1.6.2), the forced migration and its re-review (05:31, 1.7.0), and the
   failed headless resume (06:07, 1.7.1 changing the default path) all followed mid-milestone upgrades. Missing
   rule: pin the orchestrate version for a milestone; the lead upgrades only between milestones, and a release
   that changes layout or session path says so. The `run` result could warn when the installed version differs
   from the one that started the milestone's session.

2. **The record was read as evidence about 1.7.1, and it isn't (verified).** Before building anything, the owner
   should know that proposals 1, 4 and 6 target behaviour 1.6.0–1.7.1 already changed. A short run on 1.7.1 would
   show whether the item rule and the diagnosis catch these patterns.

3. **Reviews surface one or two Must Fix per round, in sequence (verified pattern, inferred cause).** M3: round 2
   "Interfaces passed. The switcher...", round 3 "The switcher passed. A People refresh...". SU M2 the same. Either
   each fix exposes the next defect, or reviewers stop exploring after a Must Fix. If the latter, telling reviewers
   to finish their whole inspection list after the first Must Fix would cut rounds more than any of the six. Worth
   checking the actual review files on the groundWork machine before deciding.

4. **The cost question belongs earlier than the replan (inferred).** SHARED-UI M2 and M3 failed for 8 and 5 rounds
   on what the owner later treated as scope (mounted-state preservation, failure recovery). Both designs passed
   review first. A design-review check that every requirement costly to prove traces to the owner's words or the
   brief (plan-module lines 160–163 already says to add none otherwise) would catch it before any building.

5. **Idle time between modules (verified gap, cause unknown).** Nothing ran 06:21–08:16 (M2 parked) or
   09:36–11:14, and SHARED-UI started only after INTEGRATION-ROLLUPS M2 finished. If SHARED-UI didn't depend on
   it, a second builder could have run. The record doesn't say why it was serial.

## Verdicts

| # | Proposal | Verdict | Reason in one line |
|---|---|---|---|
| 1 | Fix the class | Build changed | 1.7.1's item rule already does most of it; tighten `different` and add a "look for the same cause" line instead of a gameable class field |
| 2 | Builder self-review | Build changed | The step exists; a Codex subagent isn't fresh; make the existing check run prior findings and edge conditions |
| 3 | Owner cost question at replan | Build changed | Right target; make it non-blocking via `Assumption:` + `owner scope`, and add it to the diagnosis |
| 4 | Rotate after two claims | Drop | Fresh sessions weren't cheaper per claim and never passed in the record; the ladder already rotates at 3 |
| 5 | Operational hardening | Build changed | Build the Codex open-thread guard and the formatter exclusion; timeout mostly exists; replace the migration rule with "no upgrades mid-milestone" |
| 6 | Cost in the ledger | Build changed | Ledger, `cost` and `report` exist since 1.6.0; add version, session id and start time |
