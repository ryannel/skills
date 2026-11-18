# Whole-set review, 18 November 2026

Four reviews of orchestrate 2.3.8, read together: process (Fable 5.2), writing (Opus 5.5), skills against script (Opus 5.5), generic harness (Opus 5.5). A fifth agent is fixing the mid-merge dead ends (a builder's branch after a failed merge; a block left on after a hand merge). Paths are under `skills/orchestration/`; "script" is `build/scripts/agent_loop.py`.

## Fixes to make whatever is decided

Script:
- CHECKS_FAILED, NO_PROGRESS_FOR_HOURS, STALLED carry no `next` (script ~7337, 7492, 7517, 7523); the skill (build 324-326) sends the lead to `review`, which refuses anything not Ready for Review (7683) and whose INVALID points at itself (8059). Give them `run --fresh` with the reasons, or `plan` when an item can't be met; drop the self-pointing next.
- Planner endings: PLANNED with a failed land has no next (8365); BLOCKED/NEEDS_CONTEXT/UNFINISHED have no next (8281); `PLAN_TEMPLATE` says end BLOCKED if nothing should change, skill says KEEP; after an answered needs_dependency the primary next is `plan` again with `unblock` as alternative (2723).
- `human_guard` refuses while any planner holds `_plan` (10602); the skill says only work on the module. Drop the `_plan` check.
- A main-branch check that exits 75 (not judged yet) counts as a builder failure (4313, 7489).
- Script-landed commits (plan, review, adopt) skip the test command; when a branch fails alone in a batch, test the base once and report `main_broken`.
- A planner re-plans the milestone a run is building: the run keeps its old authorised hash (7118) and ends CHECKS_FAILED. Compare after each turn; `merge` should refuse a branch whose definitions differ from the tip's authorised ones.
- Findings only a planner can settle (wrong prover, contradictory items) route back to the builder (`escalation()` 1856). Let a finding say it is for a planner.
- `builders_count` reads the first number only (679), so "two Claude builders and one Codex builder" means two.
- `pause` prints no `result` (9390).
- CHANGES skips 2.3.0 to 2.3.7, so 2.3.7's default Codex model change was never announced. Add a test that each VERSION has a CHANGES entry.
- `stale_session` restarts every builder session on any version change (6904).

Skills:
- build-milestone description and line 28 can take over ad-hoc work; line 171 reads as licence to fix anything.
- review-milestone 206-210 tells the reviewer to add graded examples, which would get its review rejected (140). Make it the lead's job, or have `human accept/rereview` append it.
- review-milestone 61-62: try the edges before Could Not Judge.
- done-when.md 117 and plan-module 210: "records the answer with the `human` command" — no such verb. Route through a planner.
- build 55 "run next as printed" vs 309-312 exceptions.
- Escalation thresholds repeated in ~8 places, including builders and FINDINGS_TEMPLATE.
- build-milestone 203-212 repeats FINDINGS_TEMPLATE; 168-169 repeats merge-refused-state.
- build: implementation detail the lead doesn't act on (45-48, 191-193, 255-271 detail, 355-361).
- plan-module 304-306: a twice-seen finding becomes a test-command check; say put it where it costs least.
- Diagnosis template "change M2's items so that they can be met" vs plan-module 326.
- build 153-158 settings: says a run reads its own copy (now the tip when only behind); no route named for committing ORCHESTRATE.md.
- `ran_on` is what was requested, `observed` is what ran (build 147).
- done-when.md table rows 333, 338, 339 disagree with the script.
- Status page described with avoided names (done-when 62-68, README 156).
- Terms: "attended", "building guidance" vs "Project guidance", "design reviewer" missing from glossary, proposed-entry line shapes.
- Thrum examples: "Water M3", "port timing", "IINA", repeated boat/wake/guns.
- domain-language 64-65 internal history.
- "Keeping builders busy" heading pushes towards the maximum.
- README stale: line count, version 1.5, "check that rejects status" listed as left out.
- Planner's last line disagrees between agent file, plan.txt and plan-module.
- plan-module: keep tests meant to fail out of the test command until their milestone.
- Template example values are Thrum's (profile.md 33-38).
- Small style slips (semicolons, unwrapped lines).

## Changes the reviews proposed, and what to do about each

Most of these are fixes with an obvious answer, and I'll just make them. Two change something you chose on purpose, so they're yours to decide.

### Yours to decide

**Should the script carry on to the next step itself?** Today, when a builder finishes a milestone, the script stops and prints "next: review this milestone". The lead wakes up, runs that command, waits, reads the result, and runs the next one it prints. The lead adds nothing at those steps: the skill tells it to run them as printed. In Thrum's 36 hours there were about 170 agent sessions, and each cost the lead a turn to start it and another to read it. That load is why the lead was compacted four times and wrote its own scripts to run `next` for it. The fix is a flag, say `run --through`, with which the script runs the review itself, then the next build, and so on, stopping when the human has to decide something, when something is blocked, or when the same milestone keeps failing. The README says this chaining was left out on purpose: the lead gets a look between every step. So this reverses your earlier choice. My recommendation is to add it as a flag, with the lead choosing when to use it. That keeps the old way for anyone who wants it.

**How often should the daily report be asked for?** Today the first run, review or plan of each day asks the lead for a report. On a small project, a two-hour build gets asked for one. The review suggests asking only when a build runs past a day boundary, or when it stops. You cared about the daily report, so I'd rather ask than guess. My recommendation is to keep it daily for builds that run past a day, and skip it for a build that starts and finishes the same day.

### I'll just do these

- **Install dependencies in the script's own checkouts.** The script tests merges in a clean copy of the repository. For a Rust project that works, because `cargo` fetches what it needs. A Node or Python project fails its first merge because nothing installed its dependencies. A `Setup command:` line in ORCHESTRATE.md, run once in each new copy, fixes it.
- **Don't fill the settings template with Thrum's choices.** The template's examples say "Codex builders, Claude planner". A planner copying it gives a Claude-only user Codex builders that fail on the first run. The template will leave host and model lines for the planner to fill from what the human said.
- **Only restart builder sessions when something they rely on changed.** Today every new version of the script, even a one-line fix, starts every builder over with no memory of its work. It will restart them only when the prompts they were given changed.
- **Route the human's answer to an assumption through a planner.** The skills say "the lead records the answer with the `human` command", but that command can't. Only planners change plan files, so the lead passes the human's words to a planner, who records them.
- **Record a graded example when the human overturns a review.** The skill tells the reviewer to do this, but the reviewer's session has ended by then, and touching that file would get its review rejected. `human accept` and `human rereview` already carry the human's words, so they'll add the example.
- **Let the script write a review's bookkeeping.** A reviewer writes its results and findings, then also a status, pointers and counts that follow from them. One slip in the second part throws away the whole review. The script will work those out from the results.
- **Move locks and main-branch checks out of the lead's main skill** into a reference it reads when the project uses them. A small project never needs them, and they make the skill harder to read.
- **Leave four large ideas for later, noted in the README:** merging through pull requests, a spending budget, a planner lock per module, and support for a Codex lead. Each is worth doing, and each needs its own design.

## Keep

The record file and definitions hash; checks re-run in a clean checkout; the merge queue with batching and bisect; `reads` reuse; the handoff; goal restated on resume; `decides: human` with `ask`; review isolation; light prompt templates; plan-module's mechanisms-not-details and quality bar; interview-me's three answers; proofs.md's cost and inspection sections.

## Build notes (merge and skill rewrite)

Small fixes branch `worktree-agent-ac7ac0dd3693ab5ef` (2dec4ab). CHANGES entries to write:
- 2.3.0: slow checks run once on main; GPU shared up to the settings' count; lock hold limit; batch merges; checks reused while the files they read are unchanged; changing an item's lock or reads keeps progress.
- 2.3.1: locks limit how many runs share a device and don't make the machine quiet; `.alone` takes the whole device.
- 2.3.2: idle checkouts removed after 6 hours, or 30 minutes when the disk is low.
- 2.3.3: pruning by the script's own mark only, before every turn and on `status`.
- 2.3.4: a re-plan lifts a Needs Dependency or Needs Context block.
- 2.3.5: `flow` splits failed jobs into stopped, the script's answers and errors; `lock` refuses the script's own commands.
- 2.3.6: exit 75 means unjudged and is retried; a bisect stops at an unjudged commit.
- 2.3.7: Codex default model is gpt-6.2-sol; gpt-6.2-astra named as the stronger model.
Skills must say: review-milestone writes verdicts, findings and the review file only, last line `PASS <m>`/`FAIL <m>`, no "add graded examples yourself". build: `pause` results; Builders counts add up; sessions survive script fixes; `found`, `filled`, `graded_example` fields. plan-module: ask the human about hosts, builders and models; Setup command. GLOSSARY: `pause` under PAUSED and NOTHING.

Report branch `worktree-agent-a250d7700e3707322` (50e9ad4). `report_due`, `--write` to build-reports and the status page's report line are gone; adopt still merges build-reports for old projects. `report` prints markdown (`--since` hours or time; default since last report over an hour old, else 24 h; `--write [PATH]` to `<git common dir>/orchestrate/reports/`). Sections: Needs you now, Decisions recorded in your name, Done, Verdicts, Now and next, What has slowed down, Planner turns, Definitions changed through adopt, Flow, Choices made for you, Cost. Skills must say: build "Reports": run `report` when the human asks and when the lead stops, add judgement; drop daily wording; line ~217 numbers now under Flow; README step 26 and report row; older-projects.md build-reports note. Delete build/references/daily-report.md or turn it into the on-demand report guide.

Chaining branch `worktree-agent-a31e8ef0abb517f60` (194afbf). `run` and `plan` carry on by default, each step a child `--one-step` process; results add `steps_run`, `stopped_because`; `--one-step` keeps the old way; parent record role `steps`. Continues: Ready for Review → review; FAIL with same_builder/new_builder_session → run again; PASS → next milestone; DESIGN CHANGES → one planner revision then resume; plan PLANNED → owed design reviews, stop after DESIGN OK. Stops: decides human/ask; second DESIGN CHANGES; module finished; next milestone can't start; next not a plain script command; main broken; stop signal or newer install; 40 steps; any other result. A standalone review stays one step; plan doesn't start builders. `watch --worktree <repo> [--runs]` → CHECK_IN, WARNING_SIGNS, RUN_ENDED with `woke_for`, `warning_signs` and a summary; state in `<git dir>/orchestrate/watch.json`. Warning signs: no progress 2 h; same items failing in two counted reviews; ready work 30 min with a free slot; planner queued 1 h; disk < 30 GB; main-branch check failing on the tip. Setting `Lead check-in: 3h` (add to profile.md). CHECK_IN, WARNING_SIGNS, RUN_ENDED proposed in GLOSSARY and on test_names' SKILL_TEXT_TO_COME; remove from that list once skills explain them.

Dead-ends branch `worktree-agent-a117b16ecfba3faf0` (9d50d8a). CHECKS_FAILED/STALLED/NO_PROGRESS_FOR_HOURS next `run --fresh --message`, planner task as alternative (first when builder said an item can't be met); review INVALID no longer self-points. PLAN_NOT_MERGED (proposed); planner endings all carry next; PLAN_TEMPLATE names KEEP; KEEP on an answered block lifts it; `unblock` primary after a plan merged post-block. human_guard checks only the module's lock. Exit 75 waits, no turn/strike. merge tests main alone when a branch fails alone → `main_broken` with culprit; next to its planner or lead. Run ends INVALID next `run` when definitions re-planned mid-run; merge refuses stale definitions. Finding `planner` field → straight to diagnosis; KEEP clears. Skills: build (all of these), plan-module (KEEP lifts answered block), review-milestone + done-when (`planner` field; then drop the prompt line), build-milestone (stop on main_broken; merge refuses stale definitions).

## Second-round review: skills (Opus)

1. main_broken never reaches the lead: builder's plain BLOCKED becomes needs_context (block_for), next is run --message; cmd_run doesn't copy main_broken from merge. Carry main_broken and its next on the run's result; builder ends with a named reason; build skill names which result carries it.
2. stuck_next planner task ("If every item can be met, change no file and say so") has no legal ending: KEEP is INVALID (not owed a diagnosis, ~8639). Accept `KEEP <M> <id>: builder: <why>` for it, next run --fresh; put the line in the task.
3. locks.md 36 "run main-check --due each time you're woken": item checks start runs themselves; let watch run --due itself, or correct the text.
4. build results table (313–328) still reads as relay; say rows are met mostly as where a chain stopped or after --one-step; keep usual next only where judgement is needed.
5. build/SKILL.md grew (6,474 → 6,603 words); repeats at 198/226/locks 26, 227/231/locks 26, 199/234/297; ready table overlaps watch summary. Say each once under "Reading delivery".
6. watch's free-slot sign counts against Builders line, but a lower number in chat is the lead's to keep; WATCH_WHY says `run --message` but build 196 says pause first. One sentence in "Keeping watch"; align WATCH_WHY.
7. build-milestone 28: a module named without a milestone means its first milestone not Done.
8. report.md 39–40 (lead adopts glossary) vs domain-language 155–157 (only a planner). Agreeing a proposed name is the lead's through adopt; renaming goes to a planner.
9. build 454: graded example added only when `Graded examples:` is set; say so; older-projects.md suggests adding the line.
10. review-milestone 120–121: link files in that folder or already on the main branch.
11. Stale templates: PLAN_TEMPLATE "The lead runs the design review after that"; BUILD_TEMPLATE "the lead starts the reviewer"; FINDINGS_TEMPLATE thresholds.
12. interview-me brief "How the human wants to work" should ask how many builders, on which program.
13. Unwrapped lines: build 341, build-milestone 31/195/209, plan-module 115/198/343, done-when 137/149. graded-examples.md 36–40 boat wake. build 340 RAN is a runner.log line.

## Second-round review: script (Opus)

1. broken_base `passes()` (~9961) runs the test command without run_setup in BATCH_TREE → false main_broken with a Setup command. Call run_setup first; setup failure → None (can't tell). Scratch test: scratchpad/t/test_scratch_setup.py.
2. Chain drops the planner's `report` (STEP_FIELDS ~12775, step_entry ~12928): the human's decisions never reach the lead. Keep report (or tail) for plan steps, or stop after a PLANNED whose report names a decision.
3. `carried` (~12877) keeps --model but drops --host for later run steps. Add ("--host","host").
4. stale_definitions (~9638) refuses a branch that only lags a re-plan of another module. Skip done-when files the branch hasn't changed since the merge-base. Scratch test: scratchpad/t/test_scratch_stale.py.
5. cmd_pause (~10115) signals only run-*.lock holders: a chain's parent (role steps) and a planner revision step aren't stopped; between-steps pause lost. Also SIGTERM live `steps` records (by module).
6. A diagnosis PLANNED that changes something other than the milestone's definitions leaves it Waiting for Diagnosis (settle_replanned ~2524, keep_counts); KEEP refuses a turn with changes (~8628). Let PLANNED on that milestone's diagnosis settle it.
7. keep_plan INVALIDs (~8616–8640) and answered_block have no next; stuck_next's planner task gives no KEEP line. Task: "end with PLANNED having changed nothing" or accept KEEP builder (see skills finding 2); give INVALIDs a plan-again next.
8. judged_checks (~7707) NO_PROGRESS when a main-branch check never judges → run --fresh repeats the wait. Point next at the main-branch check or the lead.
9. main_check_attempt (~12436) records setup failure as the check's result → bisect, main_broken. Record as exit 75.
10. escalation (~1924) with for_planner: any earlier diagnosis → straight to the human. Diagnosis unless the last diagnosis was also from a planner finding.
11. builders_count undercounts "2 Codex, 1 Claude", "two Codex and one Claude", "2 Codex and 1 Claude builder" (now 1!), "two Codex builders (one Claude builder…)". Number within three words of a host name counts; add up.
12. A chain in its review step frees its builder slot to watch/builders_running; count run-origin steps parents as builders.
