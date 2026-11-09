# Fold-learnings part B: result

9 November 2026, branch `fold-b` off round-two (`8a65c7e`). Implementation commit `0588360`. Opus 5.5, medium.
Plan: `workbench/fold-learnings-2026-11-09/PLAN.md` in the main checkout (items 5–8).

The claim here is that the implementation is correct, shown by deterministic tests with fake hosts. Behaviour is
unproven: no live model run was launched, and the plan's live loop claim with a resumed turn is still owed.

Verification: `python3 -m unittest discover -s tests/orchestration -p 'test_*.py'` ran 121 tests, all OK (104
before). `check_skill.py` passes on `build`, `build-milestone`, `review-milestone` and `plan-module`.

## Item to commit and tests

All of the code is in `0588360`. New tests are in `tests/orchestration/test_agent_loop.py`, class `Fold`.

| Item | What changed | Tests |
|---|---|---|
| 5 Constraints that survive a resumed turn | `binding()` builds the restatement from a single source: the profile as read at run start (Integrate mode via `land`, Check, and the new `bounds` lines `Licences and paths not to touch` and `Owner decides`), the done-when path and field ownership, and attended items. It's about 60 words. Claude gets it on every resumed turn. A generic host gets it on each turn after the first. Codex gets it only when the goal isn't `active`. `goal` is recorded in the state and the result after each Codex turn. A missing or placeholder bounds line goes to `constraints_missing` and a stderr warning, and is left out of the restatement rather than guessed. A reviewer's nudge carries its own boundaries and never the builder's instruction to integrate. In `profile.md`, the two lines are marked as restated. | `test_item5_a_resumed_claude_turn_restates_the_binding_constraints`, `..._a_turn_resumed_inside_a_run_restates_too`, `..._codex_restates_only_when_no_goal_is_active_and_records_the_goal`, `..._a_generic_host_continuation_restates`, `..._a_missing_out_of_bounds_line_is_reported_not_guessed`, `..._a_reviewer_restatement_never_tells_it_to_integrate`; updated `test_fable_3_...`, `test_decision_8_a_resumed_turn_...` |
| 6 Launch records | `launch_record()` adds requested `effort`, `cli` (the resolved binary's `--version`, or the app's bundled CLI on a visible Codex turn, else null), `path`, and `observed`. That last field holds only what `pin_check()` verified from the host's output: model and effort from a Codex rollout, the model only from Claude's stream, and nothing for generic hosts or a Codex run with no rollout. One unverified turn drops a field for the rest of the session. This covers claims, milestone reviews and design reviews. The model and effort sentence moved from the build template's head to a trailing line. | `test_item6_the_build_prompt_no_longer_opens_with_the_model`, `..._a_claude_claim_records_effort_cli_and_only_the_observed_model`, `..._a_codex_claim_without_a_rollout_observes_nothing`, `..._a_visible_review_records_what_the_rollout_showed`, `..._one_unverified_turn_drops_a_field_for_good` |
| 7 Loader check | `preflight()` runs in `run`, `review` and `plan` after `resolve()`, on that host's actual binary (`CLAUDE` / `CODEX`). It only warns: a `warnings` field in the result and on stderr, each naming its fix. Claude: the repo has AGENTS.md, no shadowing CLAUDE file and a CLI older than 2.1.277, or a version that can't be read, gives a warning that names the `@AGENTS.md` import. A CLAUDE.md, .claude/CLAUDE.md or CLAUDE.local.md in the folder or above it, with no import, also warns, because it stops Claude reading AGENTS.md on any version (the user's `~/.claude/CLAUDE.md` is excluded, since it doesn't count). Skills: the role's skill is looked for where the host finds skills by name. For Claude that's `~/.claude/skills`, `.claude/skills` up the tree, or a plugin. For Codex it's `~/.agents/skills`, `.agents/skills` up the tree, or `/etc/codex/skills`, and a copy found only in `~/.codex/skills` is flagged as not in Codex's documented list. `profile --host H` prints the same checks. | `test_item7_an_agents_md_only_repo_warns_on_the_claude_binary_the_launch_uses`, `..._the_profile_default_host_isnt_checked_when_the_launch_resolves_to_another`, `..._which_instruction_files_stop_claude_reading_agents_md`, `..._a_skill_missing_where_the_host_loads_it_is_a_warning` |
| 8 Fresh reviewers and planners | One sentence in `review-milestone/SKILL.md`. The `one_session` docstring states the property. | `test_item8_codex_reviewers_and_planners_start_a_new_session`, `test_item8_claude_reviewers_and_planners_start_a_new_session`: no `resume` / `--resume` on the first review or plan turn, the prompt is only the role's template, and the review runs in its clean checkout |

Smoke check against real files: `instruction_warnings` on Thrum (AGENTS.md, no CLAUDE files) with the PATH
`claude` (2.1.239) gives the old-CLI warning. That matches Fable's finding 1.

## Reviewer claims checked against the code

- Astra 2 (`--message` is consumed and not durable) is correct. Astra 5 (`profile --strict` isn't an option, because
  `profile` is already strict, and `profile()` runs before `resolve()`) is correct. Astra 7 (Claude effort is never
  verified, and a missing rollout looks like no mismatch) is correct, and item 6's `observed` now makes that gap
  visible instead of looking like a pin.
- Fable 4 (the model line comes before `{goal}` in the build template) is correct. Fable 5 (no test that a first
  review or plan turn has no resume) is correct, and that test now exists.
- Plan item 7 named only the old-CLI case. Astra 5 said a CLAUDE.md or CLAUDE.local.md also suppresses AGENTS.md.
  The Claude Code memory page (fetched 9 Nov 2026) confirms that this holds on any version, so the check covers it
  too.
- I found no reviewer claim about the code that was wrong. One small drift: Fable cites `shutil.which` at line 130,
  but on round-two it's line 133.

## Left undone, and why

- **Durable conversational restrictions** (Astra 2: a restriction passed once through `--message` survives `--fresh`
  or a new lead). PLAN v2 limited item 5 to sources that already exist, so the restatement can't carry these, and a
  fresh retry still loses them. This needs a data contract (writer, scope, replacement) before it's built.
- **Mid-run profile changes** aren't picked up. The restatement is built once at run start from the profile, on
  purpose, so a builder editing ORCHESTRATE.md in its worktree can't rewrite its own rules. A changed rule applies
  from the next `run`.
- **Nudging a Codex builder that never made its goal.** `goal: none` is recorded, and its turns restate the rules,
  but there's no nudge to create the goal. The plan didn't ask for one, and the README says headless `codex exec`
  may never write the goal store.
- **The model and effort sentence is still at the head of the review, design-review and plan templates.** The plan
  named only the build template, the only one that becomes a goal objective.
- **The Claude 2.1.281 exception** (Bedrock or telemetry-off sessions before 2.1.281) isn't checked, because the loop
  can't see those settings. The `@AGENTS.md` fix it names covers that case too.
- **Live run.** No model was launched (out of scope for this commission). The plan's live loop claim with a resumed
  turn remains the behavioural test for 5 and 6.
- **Scope note.** Besides `skills/orchestration`, I edited `tests/orchestration/test_agent_loop.py` (the loop's
  tests) and wrote this file, as the brief required.
