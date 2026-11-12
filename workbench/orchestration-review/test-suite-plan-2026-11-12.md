# Test suite plan for the orchestrate set, 12 November 2026

The suite is slow because it does the same git work over and over, one test at a time, not because it waits.
Run in eight processes instead of one, it already takes 102 seconds instead of 505, with every test passing
(measured). The rest of this plan cuts the repeated work: a test that needs a milestone with four failed reviews
now builds that history from scratch, at about 7 seconds each time, when restoring a copy of it takes 0.09
seconds (measured). With the changes below, the estimate is about 320 seconds of serial work and about 60 to 75
seconds of wall time on eight processes.

Line numbers are for `tests/orchestration/test_agent_loop.py` and `skills/orchestration/build/scripts/agent_loop.py`
as they stood at 21:57 on 12 November (test file md5 `f1eddc02`). Other agents are editing both files, so find
each test by its class and name, and use the line numbers only as a guide.

## What was measured, and what is estimated

Everything in this section was measured on this Mac (14 cores, Python 3.15.2) on 12 November. Other agents were
running tests at the same time, so single figures are a little high.

| What | Time |
| --- | --- |
| The whole suite, serial, `python3 -m unittest discover tests/orchestration` (366 tests then) | 505 s |
| The same suite in the per-test timing run (375 tests, under load from another agent's run) | 615 s summed |
| The same 375 tests split over 8 processes by a stdlib runner, longest first | 102 s wall, all pass |
| `Repo.setUp`: a bare origin, a repository, a first commit and push | 0.17 s |
| Restoring the same repository from a saved copy at the same path | 0.02 s |
| One builder turn through to Ready for Review (`Repo.run_loop()`) | 1.9 to 2.2 s |
| One review of that milestone (`Repo.review()`) | 1.3 s |
| One planner turn (`cmd_plan`) | 1.8 s |
| `FirstRuns.four_fails()`: two builds and two failed reviews | 6.8 s |
| Saving a copy of the repository after `four_fails()` / restoring it | 0.07 s / 0.09 s |
| Writing a Ready for Review state directly (`write_done(..., ready=("M1",))` and a commit) | 0.17 s |
| The fake host answering `exec --help`, which the script asks on every Codex turn | 0.04 s |

One builder turn makes 112 subprocesses, 92 of them git. That is where the 2 seconds go: the profile shows 1.6 of
the 2.2 seconds waiting on child processes, and no sleep longer than a poll.

Where the 615 summed seconds went, by class: `FirstRuns` 290 s (105 tests), `Building` 60 s, `Fold` 45 s,
`VisibleCodex` 35 s, `Reviewing` 34 s, `Holistic` 23 s, `OnlyTheScriptSetsReadyForReview` 21 s, `PlanFiles`
18 s, `Guidance` 17 s, `TokensAndSessions` 15 s, `ReviewerAccess` 13 s; everything else under 12 s each. The
slowest tests are `FirstRuns.test_a_diagnosis_that_keeps_the_plan_names_who_acts` (21.8 s),
`FirstRuns.test_r8_the_loop_does_the_replans_bookkeeping_once` (14.9 s),
`FirstRuns.test_a_failure_says_how_it_differs_or_counts_as_a_repeat` (9.7 s) and
`FirstRuns.test_item7_reviewed_and_planned_name_what_comes_next` (9.4 s). 94 tests take under 0.1 s and 158 under
0.5 s. The per-test timings are in
`/private/tmp/claude-501/-Users-ryannel-Workspace-skills/61212d0e-4f87-41e0-891e-fbcd5b29ad91/scratchpad/times.json`.

The savings given for each change below are estimates, worked out from these measured unit costs and the number of
tests each change touches. Treat them as serial seconds; on eight processes, divide by about five.

## The order to work in

1. Make every test start from the same state (section 1). The parallel runner and the saved copies both depend on
   it.
2. Add the parallel runner (section 2) and switch CI to it.
3. Restore repositories from saved copies (section 3).
4. Give review tests their Ready for Review state directly (section 4).
5. Move tests that need no repository off `Repo` (section 5).
6. Delete and merge the tests in section 6.
7. Shorten the waits in section 7.
8. Make the three small script changes in section 8.
9. Add the tests for the gaps in section 10.

After each step, run the parallel runner and check two things: every test passes, and the count of tests only
falls by the number this plan deletes or merges. Don't run the serial suite more than once a step; other agents
share the machine.

## 1. Make every test start from the same state

Tests run many commands in one process, and the script keeps per-process state in module globals, so today a test
can pass or fail depending on which test ran before it. The parallel run passed, but it ran tests in a different
order from the serial run, so these are latent faults rather than current ones. Fix them before splitting the
suite, because splitting changes the order every time the timings change.

**Clear every `FAKE_` variable, not a list of them.** `FAKE_ENV` (line 807) is the list `Repo.setUp` and
`Repo.tearDown` clear, and it is missing `FAKE_HANDOFF` and `FAKE_PLAN_BARE`. 
`Holistic.test_a_planner_ends_with_planned_alone_and_the_script_lists_the_files` (line 2628) sets
`FAKE_PLAN_BARE=1` and never unsets it, so every later planner turn in that process ends with a bare `PLANNED`.
Replace the list with a loop that pops every key starting with `FAKE_`, plus `ORCHESTRATE_ROLE` and
`ORCHESTRATE_VISIBLE`.

**Reset the script's module globals in `release()` (line 88).** `new_command()` (script line 4541) clears four of
them. These stay set from one test to the next: `RUN_HERE` (line 1816, which outranks the file on disk when `next`
reuses a module's hosts), `TURN_USAGE`, `TURN_SIZE`, `TURN_STOP` (4169 to 4171), `WARNINGS` (4534), `CONTEXT`
(2714), `SESSION_PATH` (5068), `_IMPORTS_SENT` (5069), `_VERSIONS` (4761, the cached `--version` of each host
binary), `_COMMON` (2717) and `QUOTA_WORKTREE` (3659), as well as the `functools.lru_cache` on `claude_supports`
(line 770), which is keyed by the flag alone and so keeps the answer of whichever fake `claude` binary ran first.
Copy each global's starting value when the test module is imported, and put every one back in `release()`, with
`claude_supports.cache_clear()`. This matters more after section 3: once every test in a process uses the same
path for its fake host, `_VERSIONS` would hand one test's `FAKE_VERSION` to the next.

**Point every host and home at the test, before the script is imported.** `agent_loop` reads `CODEX_HOME`,
`CLAUDE_CONFIG_DIR`, `XDG_STATE_HOME` and `XDG_CACHE_HOME` once, at import (script lines 391 to 394, 2707,
5071, 5072, and `codex_quota.py` lines 43 and 44). `Repo.setUp` patches the module's copies, but the
`unittest.TestCase` classes don't, and nor do the scripts that tests start as subprocesses
(`BackgroundJobs.script`, `MergeUpstream`, `test_names.RenamedInOldProjects.test_loops_still_runs_the_runs_command`).
Those can write loop records under the real `~/.local/state/orchestrate/loops`. Make a small shared module,
`tests/orchestration/support.py`, that every test file imports first. It makes one temporary folder per process
and sets `HOME`-style variables to folders in it: `CODEX_HOME`, `CLAUDE_CONFIG_DIR`, `XDG_STATE_HOME`,
`XDG_CACHE_HOME`, `ORCHESTRATE_LOOPS_DIR`, and `ORCHESTRATE_CODEX` and `ORCHESTRATE_CLAUDE` set to `/no/such/host`,
so a test that forgets to install a fake host fails at once instead of starting the real CLI. It also sets
`GIT_CONFIG_GLOBAL=/dev/null` and `GIT_CONFIG_NOSYSTEM=1`, so the owner's own git settings (this machine sets
`pull.rebase` and the LFS filters) don't reach the test repositories; CI has different ones. Move the shared
helpers (`put`, `done`, `item`, `milestone`, `release`, `FAKE_HOST`, `Repo`) there as well, so `test_prompts.py`
and `test_names.py` stop importing `agent_loop` in their own way.

**Install the fake `claude` in `Repo.setUp`.** Today `Repo.setUp` sets `agent_loop.CODEX` to the fake and leaves
`agent_loop.CLAUDE` at the real binary. Five places write the same fake under the name `claude` by hand:
`Building.test_claude_builder_claims_with_a_clean_environment` (line 1230), `ReviewerAccess` (1862),
`VisibleClaude.setUp` (2252), `Fold.use_claude` (2353, borrowed by `Holistic`) and `FirstRuns.fake_claude`
(2839). Write both fakes once in setup and delete those five copies. The fake already picks its Claude behaviour
from the name it was started under.

Saving: none directly. This is what makes sections 2 and 3 safe.

## 2. Run the suite in parallel

**Add `tests/orchestration/run.py`, a stdlib-only runner.** It discovers the tests the way `unittest discover`
does, flattens them to test ids, and splits the ids across worker processes. Each worker is
`python3 -c` or a small worker script that loads its ids with `unittest.defaultTestLoader.loadTestsFromName`
after putting `tests/orchestration` on `sys.path`, runs them, and writes its report to a file. The runner waits
for all workers, prints each failing worker's report, and exits non-zero if any worker failed. It should accept
test names to run a subset, and `-j N` for the worker count, defaulting to `min(8, os.cpu_count())`.

Split by test, not by class: no class uses `setUpClass`, and splitting `FirstRuns` (290 s) by class would leave
one worker running for most of the run. Balance by recorded time, longest first, into the emptiest worker. Keep
the timings the last run measured in a file the runner writes, `tests/orchestration/.timings.json`, ignored by
git; when it is missing, deal the ids out round-robin in discovery order, which balances well enough because slow
tests are spread through the file.

The runner used for the measured 102-second run is in
`/private/tmp/claude-501/-Users-ryannel-Workspace-skills/61212d0e-4f87-41e0-891e-fbcd5b29ad91/scratchpad/par/run.py`
and `worker.py` beside it; start from those. Eight workers took 102 s for 505 s of serial work, about five
times faster rather than eight, because the workers compete for the same cores running git. Twelve workers were
not measured.

**Switch CI to the runner.** `.github/workflows` runs `python3 -m unittest discover tests/orchestration` on Python
3.13. Keep the runner compatible with 3.13, and keep `python3 -m unittest discover tests/orchestration` working,
since that is how the owner and other agents run it today.

**What can break in parallel, and why it doesn't today.** Each worker is its own process, so module globals,
`os.environ` and signal handlers are per worker. Nothing in the tests or the script calls `os.chdir`. Nothing
listens on a port: the Codex app connection is a Unix socket under `CODEX_HOME`, which every test that reaches it
points at its own folder (`Repo.setUp`, `Processes`, `VisibleChoice`). Temporary folders come from `tempfile` and
are unique. Two things are shared across the machine. First, `live_loops` reads the whole process table (`ps -A`,
script line 2893); the `Loops` tests filter what they read by their own repository, so another worker's processes
don't match, and they should keep doing so. Second, the loop records directory defaults to the real
`~/.local/state/orchestrate/loops`; section 1 closes that. The timing assertions are loose enough to survive load
(`assertLess(..., 15)` in `Processes`, `assertGreater(..., 2)` in
`FirstRuns.test_r10_a_second_planner_waits_for_the_first`), and the parallel run passed with them.

Saving: measured, 505 s to 102 s of wall time with the suite as it is.

## 3. Restore repositories from saved copies instead of rebuilding them

A git repository can't simply be copied to a new folder: the remote URL, the `.git/worktrees` entries for the
script's own checkouts (under `.git/orchestrate/verify`) and `ORCHESTRATE_LOOPS_DIR` all hold absolute paths.
They stay right if the copy goes back to the same path. Within one worker, tests run one at a time, so every
`Repo` test in a worker can use the same folder.

**Give each worker one case folder.** In `support.py`, make `CASE = <per-process temp folder>/case` and
`SAVED = <per-process temp folder>/saved`. `Repo.setUp` builds the base repository in `CASE` the first time and
copies it to `SAVED/base`; every later `setUp` removes `CASE` and copies `SAVED/base` back with
`shutil.copytree(..., symlinks=True)`. `tearDown` no longer deletes the folder; the next `setUp` replaces it, and
an `atexit` hook removes the per-process folder. Write the fake hosts into the base copy, so they are never
written again.

**Save the long histories the same way.** Add `Repo.restore(name, build)`: if `SAVED/<name>` exists, copy it
into `CASE`; otherwise run `build()` on the base repository and save the result. The builder must leave
`os.environ` as it found it (pop the `FAKE_` variables it set), because the copy saves files, not the process.
Use it for:

- `FirstRuns.four_fails` (line 3819). Six builds today: `test_r8_every_review_round_is_kept_and_named`, the two
  subtests of `test_r8_the_loop_does_the_replans_bookkeeping_once`, `test_keep_is_refused_when_no_diagnosis_is_owed`,
  `test_r8_owner_scope_on_an_owed_milestone_is_the_replan` and `test_r9_each_kept_round_keeps_its_captures`. It
  returns the last review's result line, so save that as a JSON file in the case folder and read it back.
- `FirstRuns.six_rounds` (line 3875), saved once for `diagnoses=0` and once for `diagnoses=1`. Seven builds today
  across `test_six_rounds_of_new_findings_owe_a_diagnosis_not_a_replan`,
  `test_a_diagnosis_that_changes_the_plan_settles_like_a_replan`, the three subtests of
  `test_a_diagnosis_that_keeps_the_plan_names_who_acts`, `test_a_second_diagnosis_blocks_it_with_each_rounds_failures`
  and `test_owner_scope_restarts_the_counts_and_unblocks_it`.
- `TokensAndSessions.stalled_run` (line 5546) with the default contexts, used by four tests.
- The first `run_loop()` that `VisibleCodex.test_decision_8_run_again_reactivates_a_goal_paused_in_the_app` and
  `test_decision_8_run_after_unblock_reactivates_a_blocked_goal` share (see section 6).

In the tests that rebuild inside a subtest (`self.tearDown(); self.setUp()` in
`test_r8_the_loop_does_the_replans_bookkeeping_once` at line 3852 and
`test_a_diagnosis_that_keeps_the_plan_names_who_acts` at line 3924), replace the pair with `self.restore(...)`.

Measured in a probe: after `four_fails()` was restored into the same path, a re-planning `cmd_plan` turn ran and
returned `PLANNED` with `replanned: ["WATER M1"]`, so the copies, worktrees included, work.

Saving, estimated: base setUp 0.15 s on about 280 `Repo` tests, about 40 s; `four_fails` five rebuilds of 6.8 s,
about 33 s; `six_rounds` five rebuilds of about 3.3 s, about 16 s; `stalled_run` three rebuilds, about 6 s.
About 95 s in all.

## 4. Give review tests their Ready for Review state directly

Most review tests run a builder turn only to get a milestone to Ready for Review. `Repo.write_done` already takes
`ready=("M1",)`, which writes the record the script writes after its checks pass. Measured: writing M1 as
`ready_for_review` with its items passed and evidence filled (the `proved` helper), with `ready=("M1",)`, then
`commit_all()`, took 0.17 s, and `review(commit=<that commit>)` returned `REVIEWED`, `PASS`. The builder turn it
replaces took 1.9 s.

Add `Repo.ready_for_review(**milestone_kw)` that does this and returns the commit, and use it in:

- `Reviewing.claim` (line 1272), which ten tests call, except in `test_a_passing_review_lands_and_accepts`. That
  one keeps the real builder turn, so one test still covers a claim the script made followed by its review.
  `test_a_passing_review_lands_and_accepts` also checks the reviewed commit follows the builder's commit; keep that
  check there.
- `ReviewerAccess.setUp` (line 1828), which runs a builder turn before each of its four tests.
- Tests in `FirstRuns` whose builder turn exists only to be reviewed:
  `test_item9_a_reviewers_captures_land_beside_the_review`,
  `test_r15_a_record_forged_during_a_review_refuses_it`, `test_r16_a_reviewer_that_commits_is_refused` and
  `test_a_review_must_list_its_findings_on_a_fail_and_none_on_a_pass`.

Leave alone the tests that read what the builder's turn recorded, such as usage, session or launch fields
(`test_item5_each_claim_records_what_it_spent_since_the_last`, `test_item5_every_turn_lands_in_the_ledger_and_cost_adds_it_up`,
`test_r4_cost_falls_back_to_the_committed_record_when_the_ledger_has_nothing`).

Saving, estimated: about 17 builder turns at 1.7 s, about 29 s.

## 5. Move tests that need no repository off `Repo`

These tests subclass `Repo` and so pay 0.17 s of setup each, but they call pure functions, or read only
`ORCHESTRATE.md` through `profile(self.wt)`. Move them to plain `unittest.TestCase` classes. Where a test uses
`profile(self.wt)`, give it a temporary folder holding only `ORCHESTRATE.md`; check that `profile` (script line
617) doesn't need git first.

- `ReviewerAccess.test_a_codex_call_open_in_the_rollout_stops_the_turn_and_a_shell_command_doesnt` (line 1879)
  and `ReviewerAccess.test_a_turn_stopped_at_the_turn_limit_names_the_last_open_tool_call` (line 1907). These test
  `HeadlessWatch` alone, but `ReviewerAccess.setUp` runs a builder turn first: 2.1 s each today. Move them next
  to `Processes.test_a_codex_turn_that_completed_ends_without_its_process_exiting`.
- `WhatTheLeadSees.test_profile_reads_the_builders_count_as_a_digit_or_a_word`.
- `Fold.test_item5_a_rule_that_runs_over_several_lines_is_restated_whole`,
  `Fold.test_item6_one_unverified_turn_drops_a_field_for_good`,
  `Fold.test_item7_which_instruction_files_stop_claude_reading_agents_md`.
- `Holistic.test_holistic_1_named_files_must_exist_and_be_changed` (uses `head_commit`, so it needs a repository;
  give it the base copy only if it fails without one), `Holistic.test_holistic_4_no_skill_or_claude_agent_file_sets_model_or_effort`,
  `Holistic.test_holistic_8_review_skill_and_findings_message_separate_blocking_from_advisory`.
- In `FirstRuns`: `test_item5_a_paused_claude_turn_counts_the_tokens_it_showed`,
  `test_item6_quota_rounds_small_costs_and_counts_in_words`,
  `test_item11_a_long_report_keeps_its_end`, `test_r5_next_gives_a_command_on_every_rung`,
  `test_r18_owner_stops_ask_in_chat_and_never_send_anyone_to_a_terminal`,
  `test_session_titles_group_by_repository_then_module`, `test_r6_quota_counts_only_this_repositorys_milestones`,
  `test_r8_a_plan_that_leaves_an_owed_milestone_alone_settles_nothing`, `test_a_planner_cant_change_the_counts`,
  `test_r9_a_review_host_the_profile_cant_resolve_is_a_problem`, `test_r9_loop_started_codex_shells_carry_the_role`,
  `test_r10_live_turns_and_dollars_say_what_they_are`.
- `PlanFiles.test_plan_checks`, `OnlyTheScriptSetsReadyForReview.test_a_record_older_than_a_failed_review_is_not_current`.

Some of these may turn out to need the repository after all (for example a `next` that reads the worktree);
leave those on `Repo`, which after section 3 costs 0.02 s.

Saving, estimated: about 4 s for the two `HeadlessWatch` tests and about 4 s for the rest.

## 6. Tests to delete or merge

Each of these duplicates another test, or checks the same code path with a second fixture.

**Delete:**

1. `Reviewing.test_astra_4_reviewer_deleting_a_milestone_is_caught` (lines 1346 to 1349). The detection is
   `delta_problems`, which `Deltas.test_astra_4_reviewer_deleting_a_milestone_is_caught` (line 327) tests
   directly. That the review command turns a delta problem into `INVALID` and lands nothing is tested end to end
   by `Reviewing.test_astra_4_reviewer_source_edits_are_caught_and_not_landed`.
2. `Building.test_fable_16_build_prompt_names_the_skill_file` (lines 1009 to 1012). The build prompt fixtures
   `build-codex-headless-full.txt` and `build-claude-visible-plain.txt` hold the skill path and the merge
   command, once section 8 makes them render through the script's own code. `Profiles.test_fable_16_prompts_carry_the_skill_path_for_hosts_without_skills`
   keeps the unit check.
3. `Holistic.test_holistic_6_the_restatement_opens_with_what_the_builder_may_change_and_the_goal` (lines 2717 to
   2721). The fixture `build-resumed-restatement.txt` is that exact text.
4. `Holistic.test_a_resumed_turn_after_the_lead_writes_leaves_out_the_needs_line` (lines 2723 to 2727). The two
   fixtures `build-resumed-restatement.txt` (with the needs line) and `build-resumed-after-the-lead-wrote.txt`
   (without it) render the same milestone both ways.
5. `Fold.test_item5_a_reviewer_restatement_never_tells_it_to_integrate` (lines 2448 to 2454). The fixture
   `review-restatement.txt` is that exact text.
6. `TokensAndSessions.test_a_full_session_left_by_an_earlier_run_is_not_resumed` (lines 5565 to 5572). The
   60% rule is `stale_session`, tested directly by `StaleSessions.test_a_session_over_60_percent_full_is_not_resumed`,
   and its wiring into a run is tested by `test_a_session_that_crosses_60_percent_mid_run_is_replaced_before_the_next_turn`.
   Keep `test_a_session_from_a_state_file_2_0_0_wrote_is_not_resumed`: it also checks the version is rewritten
   and the next run resumes.

**Merge the plain Codex build tests into one.** Each of these runs one headless Codex builder turn to Ready for
Review on the same repository and checks a different field of the result. Make
`Building.test_claims_check_only_milestone_and_accepts_it_in_the_record` the one test, run it with
`effort="high"` and an `AGENTS.md` committed first, and move into it the assertions of:

- `Fold.test_item6_a_codex_claim_without_a_rollout_observes_nothing` (the launch record: effort, observed, cli,
  path),
- `Fold.test_item7_the_profile_default_host_isnt_checked_when_the_launch_resolves_to_another` (no `AGENTS.md`
  warning for Codex),
- `VisibleCodex.test_decision_8_without_the_app_the_loop_runs_headless_and_says_why` (`path`, `path_reason`,
  `exec` argv),
- `Leads.test_a_claim_is_released_when_the_milestone_is_accepted` (no hold left),
- `FirstRuns.test_item5_a_turn_with_no_tokens_is_marked_incomplete` (the ledger row and `cost_line`).

Then delete those five. Merge `WhatTheLeadSees.test_runs_prints_the_step_each_run_is_on` into
`Loops.test_a_running_build_is_listed_with_its_record_and_leaves_nothing_when_it_ends`: both set `FAKE_LOOPS`
so the fake host runs `runs --json` during the turn, and both read what it saw.

**Merge the plain Claude build tests into one.** Make `Building.test_claude_builder_claims_with_a_clean_environment`
the one test, with `ANTHROPIC_API_KEY` set, `effort="high"`, `FAKE_VERSION="2.1.239 (Claude Code)"` and an
`AGENTS.md` committed, and move into it the assertions of:

- `Fold.test_item6_a_claude_claim_records_effort_cli_and_only_the_observed_model` (adjust the expected effort and
  cli to the merged values),
- the `run_loop` half of `Fold.test_holistic_5_model_and_effort_are_in_no_prompt_only_the_launch_record` (the
  template half stays as a unit test, moved off `Repo`),
- `Fold.test_item7_an_agents_md_only_repo_warns_on_the_claude_binary_the_launch_uses`,
- `FirstRuns.test_item6_a_claude_turn_carries_no_quota`.

**Merge the two goal reactivation tests.** `VisibleCodex.test_decision_8_run_again_reactivates_a_goal_paused_in_the_app`
and `test_decision_8_run_after_unblock_reactivates_a_blocked_goal` differ only in the status written to the goals
database; the script reads both with one check, `goal_status(...) in ("paused", "blocked")` (script line 5866).
Make one test that saves the state after the first `run_loop()` (section 3), then for each status restores it,
writes the status and runs again.

**Fix a test that claims more than it checks.** `FirstRuns.test_a_review_must_list_its_findings_on_a_fail_and_none_on_a_pass`
(line 4044) loops over one case only, `FAKE_NO_FINDINGS` with a failing review, and rebuilds the repository with
`self.tearDown(); self.setUp()` for it. Nothing tests the pass half: `FAKE_PASS_FINDINGS` is defined in the fake
host and cleared in `FAKE_ENV`, but no test sets it. Drop the rebuild, use `ready_for_review()` from section 4, and
add the pass case with `FAKE_PASS_FINDINGS=1`.

**Check the claim conditions without a builder turn.** `Building.test_uncommitted_pass_is_not_ready_for_review`,
`test_untracked_files_block_the_claim`, `test_failing_profile_check_blocks_the_claim` and
`test_astra_5_a_check_that_leaves_untracked_files_blocks_the_claim` each run a builder turn with `budget_hours=0`
to reach one reason in `not_ready_reasons`. The reasons come from `ready_problems` (script line 3468) and
`check_failures` (3406), which run git in a real tree, so these stay git tests, but they don't need the host or the
loop. Make one test that prepares each tree state on the base repository and calls `ready_problems` directly,
one subtest per former test, and keep `test_astra_5_checks_run_on_the_integrated_tip_not_an_older_ancestor` as
the end-to-end run, since it needs a push to land during the turn.

Saving, estimated: deletions about 4 s; the Codex merge about 6 builder turns, 12 s; the Claude merge about 3
turns, 6 s; the goal merge 2 s; the claim conditions about 5 s. About 30 s.

## 7. Cut the waiting

None of the waits is long, but each test that hits one pays about a second or more. Make each one a module
constant in the script, with its current value, so the script behaves the same, and set a short value in the
tests.

| Wait | Where | Tests that pay it (measured time) | Change |
| --- | --- | --- | --- |
| `run_proc` checks `watch`, `tick` and a pause once a second, `proc.wait(timeout=1.0)` | script line 2541 | `Processes.test_fable_6_a_pause_stops_the_whole_process_group`, `test_a_watch_ends_a_run_whose_turn_is_over`, `ReviewerAccess.test_a_tool_call_open_too_long_stops_the_turn_and_the_next_prompt_names_it` (4.7 s), `TokensAndSessions.test_a_turn_stopped_at_the_turn_limit_gets_a_row_with_its_tokens` (2.2 s) | `RUN_POLL_S = 1.0`; tests set 0.05. Then set `TOOL_CALL_LIMIT_S` to 0.1 in the tool call test, and pass a turn limit of 0.3 s instead of 2 in the turn limit test. |
| `kill_group` waits 10 s after SIGTERM, then 5 s after SIGKILL | script lines 2486 to 2495 | none today (see gap 3) | `KILL_GRACE_S = (10, 5)`, so the new test can use (0.2, 0.2). |
| `wait_for_merges` polls every 2 s | script line 7403 | `OnlyTheScriptSetsReadyForReview.test_the_run_waits_for_a_merge_left_running_in_the_background` (2.2 s) | `MERGE_POLL_S = 2.0`; the test sets 0.05, its merge job sleeps 0.3 instead of 1.5, and it asserts `0.2 < elapsed < 20`. |
| A second planner polls every 2 s for the first | script line 6906 | `FirstRuns.test_r10_a_second_planner_waits_for_the_first` (5.0 s) | `PLANNER_POLL_S = 2.0`; the test sets 0.05, kills the first planner after 0.5 s instead of 3, and asserts more than 0.4 s. |
| A run waits out a held run lock for `LOCK_PATIENCE_S = 0.5` | script line 2569 | every test that expects `TAKEN` or `REFUSED` against a holder process | Set 0.0 in `Repo.setUp`. No test checks the patience itself; add one unit test of `take_file_lock` with a patience, against a lock held by another process. |
| The Codex app fake: `START_S=0.2`, `STALL_START_S=1.0` | `FakeCodexApp.installed`, line 2119 | `VisibleCodex.test_decision_8_a_turn_the_app_never_starts_is_unqueued_so_it_cant_run_unwatched` (5.3 s) | 0.05 and 0.3. `test_decision_8_a_turn_the_app_starts_late_is_waited_for_not_given_up_on` needs three ignored wakes to fit inside the stall limit: 3 × 0.05 is well under 2 × 0.05 + 0.3. |
| The visible turn limit, `turn_timeout_hours=0.5 / 3600` | `VisibleCodex.test_decision_8_a_timeout_interrupts_the_apps_turn_and_keeps_an_active_goal`, line 2189 | three turns of 0.5 s | 0.1 / 3600. |
| `time.sleep(1.1)` so the run state is written after the process started | `Loops.test_a_loop_without_a_record_is_found_in_the_process_table`, line 1601 | 1.1 s | The script compares the file's mtime with the start time `ps` gives in whole seconds (script line 2941). Set the file's mtime two seconds ahead with `os.utime` instead of sleeping. |
| `threading.Timer(0.5, ...)` before a pause | `Processes.test_fable_6_a_pause_stops_the_whole_process_group`, line 529 | 0.5 s | 0.1 s, once `RUN_POLL_S` is short. |

Saving, estimated: about 15 s.

## 8. Three small changes to the script

These change `agent_loop.py`, so coordinate them with whoever is editing it.

**Ask `codex exec --help` once per binary, not once per turn.** `codex_supports` (script line 779) starts the
host's `--help` every time it is called, and the script calls it on every Codex turn. `claude_supports` already
caches, but by flag alone. Cache both by `(binary, flag)`. It costs the real script nothing to cache, and in the
tests each turn saves one start of the fake host, measured at 0.04 s. The test source has about 165 `run_loop` calls, 60
`review` calls and 40 planner calls, several of them in loops, so the saving is roughly 15 to 25 s, estimated. Clear both caches in
`release()` (section 1).

**Build the argument parser in a function.** `main()` (script line 9073) builds the parser inline, so the tests
never use it: `Repo.run_loop`, `Repo.review`, `Repo.owner` and the planner helpers build `argparse.Namespace`
objects by hand. `cmd_run` reads 21 of its arguments with `getattr(a, "...", default)`, so a flag renamed in the
parser, or a default changed there, goes unnoticed. Move the parser into `build_parser()`, and make the test
helpers turn their keyword arguments into an argv list and parse it. This is gap 2 below; it costs nothing at run
time.

**Build the first build prompt in a function.** `cmd_run` fills `BUILD_TEMPLATE` inline (script lines 6075 to
6084), and `tests/orchestration/test_prompts.py` repeats that call in its own `build_prompt` (lines 35 to 55). If
`cmd_run` starts passing something different, the fixture still renders the old way and passes. Move the call
into `agent_loop.build_prompt(...)` with the values as arguments, call it from `cmd_run`, and call the same
function from `test_prompts.py`. Do the same for the review prompt (script line 6419) if its arguments are worked
out inline.

## 9. Which end-to-end runs stay, and where a unit test is enough

Keep at least one end-to-end run of each main path. After the changes above these remain:

- A builder turn through to Ready for Review: `Building.test_claims_check_only_milestone_and_accepts_it_in_the_record`
  (Codex, merged) and `Building.test_claude_builder_claims_with_a_clean_environment` (Claude, merged);
  `OnlyTheScriptSetsReadyForReview.test_the_builder_merges_in_progress_and_the_script_sets_ready_for_review` for a
  milestone that needs a review.
- A review: `Reviewing.test_a_passing_review_lands_and_accepts` (with a real claim first) and
  `Reviewing.test_fable_3_a_failed_review_resets_the_items_that_failed`.
- A merge: `MergeUpstream.test_merge_lists_the_files_the_rebase_brought_in`, which starts the script as a
  subprocess, and `Landing.test_astra_10_local_integration_with_no_remote_fast_forwards_the_branch`.
- A plan: `OwnerAndPlanner.test_fable_9_a_planned_module_is_committed_landed_and_queued`.
- Migrate: `PlanFiles.test_migrate_moves_each_module_into_its_folder_and_keeps_acceptance`.

The end-to-end run is the only honest check wherever the behaviour is git's or the operating system's, and these
should stay as they are, apart from the waits in section 7: the process group tests in `Processes`; the pause
signal in `Leads.test_fable_6_pause_signals_the_running_loop`; the process table in `Loops`; the planner
refusals in `FirstRuns` from `test_r13_a_planner_that_lands_a_forged_record_itself_is_refused` through
`test_r16_a_repository_with_no_records_still_adopts_modules_as_they_stand`, which depend on reflogs and refs;
work landing on the tip during a turn (`Reviewing.test_fable_2_upstream_work_landed_during_review_isnt_the_reviewers`,
the `test_r15_` tests); `Building.test_fable_23_rebased_upstream_commits_are_not_the_builders_progress`; and
`BackgroundJobs`, which runs the real command line.

A unit test gives the same confidence where the end-to-end run only reaches one pure function: the claim
conditions in section 6, the stale-session reasons (already in `StaleSessions`), restatement text (already in the
prompt fixtures) and `HeadlessWatch` (section 5).

One rule for the end-to-end tests that remain: assert that the right piece reached the prompt, by one short
marker such as `"Still binding:"`, and leave the wording to the prompt fixtures. Several tests in `Fold` and
`Holistic` assert whole sentences of prompts, and each wording change then has to be made in a fixture and in
those tests. This saves no time, but it stops one edit from failing several tests.

## 10. Gaps, worst first

Each of these is behaviour in the script that no test reaches today, ranked by how bad it would be if it broke
without anyone noticing.

1. **Merging when git pushes back.** `land` (script lines 3125 to 3175) retries once when the push is rejected,
   aborts the rebase when it conflicts, and refuses when the main branch is checked out in another worktree that
   can't fast-forward. No test makes any of these happen with real git; the only conflict in the tests is a
   mocked `land` in `PlanFiles.test_status_md_that_cant_land_never_fails_the_record`. A silent break here loses a
   builder's work or leaves a rebase half done in its tree. Add three tests on the base repository: a second clone
   pushes first, so the first push is rejected and the retry lands (or install a `pre-receive` hook in the origin
   that rejects once); two edits to the same line, so the rebase conflicts and the tree is left with no rebase in
   progress; and the local merge mode with `main` checked out in a worktree holding an uncommitted change. About
   0.3 s each.
2. **The command line the lead types.** See section 8: no test parses `run`, `review`, `plan`, `owner`, `adopt` or
   `migrate` arguments, and the `next.command` strings the script prints are only checked by substring. A flag
   renamed in one place leaves every result line telling the lead to run a command that fails. After
   `build_parser()` exists, wrap `Repo.call` so that every `next.command` in a result is split with `shlex` and
   parsed by `build_parser()`; a command that doesn't parse fails the test that printed it.
3. **A host that ignores SIGTERM.** `kill_group` sends SIGKILL after 10 seconds, but every test's child dies on
   SIGTERM. If the escalation broke, a pause or a turn limit would hang on such a host and hold the milestone.
   Add one test in `Processes` with `sh -c "trap '' TERM; sleep 30"`, `KILL_GRACE_S` set short, and a turn limit,
   that checks the run returns 124 and the process is gone.
4. **Pausing a real `run` process.** `Leads.test_fable_6_pause_signals_the_running_loop` sends `pause` to a
   `python3 -c` process that imports the script and calls `install_stop`. Nothing starts `agent_loop.py run` itself
   and pauses it, so the path from SIGTERM through the turn being stopped to a `PAUSED` result line is never run
   whole. Add one subprocess test: start `run` with a fake host that sleeps, call `pause`, and check the result
   line and that the host's process group is gone.
5. **A script checkout left broken.** `verify_tree` (script line 3085) removes and re-adds a checkout whose
   `checkout` fails, for example after a crash removed its `.git/worktrees` entry. No test breaks one first.
   Add a test that deletes the worktree metadata for `.git/orchestrate/verify/WATER` and then runs the checks.
6. **Writes interrupted half way.** `note_run` (script line 1830) and the loop records (2806) write a temporary
   file and rename it. Nothing checks that a reader never sees half a file. This is unlikely to break, so test it
   only if one of those writes changes.

## 11. The exact prompt fixtures

Keep them. The 19 files in `tests/orchestration/prompts/` hold 17 KB of text and the one test that compares them
takes 0.01 s. They exist so the owner can read a change to what the agents are told as a diff, and nothing
smaller does that. Their cost is that every wording change needs `ORCHESTRATE_WRITE_PROMPTS=1` and a look at the
diff, which is the point.

Two changes make them worth more. Render them through the script's own functions (section 8), so they check what
the script sends, not a copy of how it once built it. And let them own the wording: delete the end-to-end
assertions that repeat a fixture's sentences (section 6, items 2 to 5, and the rule at the end of section 9).

## Expected result

| | Serial work | Wall time, 8 processes |
| --- | --- | --- |
| Today | 505 s (measured) | 102 s (measured) |
| After sections 1 to 8 | about 320 s (estimated) | about 60 to 75 s (estimated) |

The serial estimate is 505 s less about 95 s from saved copies, 29 s from direct Ready for Review states, 8 s
from moving tests off `Repo`, 30 s from deletions and merges, 15 s from shorter waits and 20 s from caching the
host's `--help`. The wall-time estimate applies the measured five-times speedup of eight processes; the slowest
single test should fall from 21.8 s to about 3 s, so it no longer sets the floor. Section 10 adds about 2 s.

Not in this plan, but worth a look later: one builder turn makes 92 git calls, of which 17 are `git_common_dir`
and 6 are fetches in `tip`. Caching those inside one command would speed the real script and every end-to-end
test with it.
