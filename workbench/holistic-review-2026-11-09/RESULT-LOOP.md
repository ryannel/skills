# Result: loop and orchestrate decisions 1–9

9 November 2026, branch `fix-loop`, commit `b9abffb` (all nine decisions). Sources: `SYNTHESIS.md`, `astra-REVIEW.md` and `fable-REVIEW.md`,
which are in `~/Workspace/skill-factory-integrate/workbench/holistic-review-2026-11-09/`, not in this worktree. Scope:
`skills/orchestration/**` and `tests/orchestration/**`. All tests use fake hosts. No model ran, and nothing was installed or
pushed.

Tests are in `tests/orchestration/test_agent_loop.py`, class `Holistic` unless another class is named.

| # | Decision | Status | What changed | Tests |
|---|---|---|---|---|
| 1 | Planner success needs a result | Resolved | `PLAN_TEMPLATE` now asks for the last line `PLANNED: <files>`, or for `BLOCKED`/`NEEDS_CONTEXT`. The new `plan_owed` accepts `PLANNED` only when the named files exist and changed, and every changed done-when file has a design beside it. Otherwise the planner gets a nudge naming the gap, at most twice. `one_session` now nudges with whatever the check says is owed. `BLOCKED`, `NEEDS_CONTEXT` and `UNFINISHED` land nothing and report `left_uncommitted`. | `test_holistic_1_*` (5): a progress report, a late plan after a nudge, a missing design, a blocked planner, named-file checks |
| 2 | Owner restrictions survive retries | Resolved, differently | Owner restrictions go in a separate `run --owner-rule TEXT` flag (repeatable), not in `--message`; `--clear-owner-rules` clears them. They're stored in the module's run state, survive `--fresh` and later milestones, and go in the first prompt and in every restatement. A Codex thread with an active goal also gets the rules line, since a rule can be newer than the goal. `build/SKILL.md` routes conversational restrictions to `--owner-rule`. | `test_holistic_2_*` (2) |
| 3 | Cap on progress-only continuations | Resolved | `STALL_TURNS = 3`: the loop stops after three turns in a row that change nothing (no committed or uncommitted work, no change to the builder's done-when fields) and report nothing. The result is `STALLED` with the open items. The two continuations in between say `Continue the objective. Still open: <ids>.` The lead treats `STALLED` like `BUDGET`. | `test_holistic_3_*` (2); updated `Fold.test_item5_codex_*` |
| 4 | Remove `model`/`effort` frontmatter | Resolved, wider | Removed from build-milestone, review-milestone and plan-module, and also from `build` and both Claude agent files (details below). | `test_holistic_4_*` |
| 5 | Model and effort only in the launch record | Resolved | Removed from all four templates and the Codex goal objective. Also removed "Run at medium effort…" from build-milestone and "starts you at medium effort" from review-milestone. README rule rewritten. | `Fold.test_holistic_5_*` (no template or prompt names model or effort; a `--effort high` reaches argv and the record but not the prompt); `Fold.fresh_review_and_plan` |
| 6 | Resumed Claude turns restate the objective | Resolved | `binding()` for builders now opens `Objective: <M> claimed, every item pass with evidence and the work integrated.` This applies on every host that restates. | `test_holistic_6_*`; `Fold.test_item5_*` (word cap 75 → 90) |
| 7 | Find plugin-installed skills and agents | Resolved, with a live check owed | The new `plugin_components()` reads `plugins/cache/<marketplace>/<plugin>/<version>/` on both hosts. It counts only the components that plugin's marketplace entry lists, falling back to the standard layout. For Claude it also reads an in-place local-path marketplace that is enabled in `settings.json`. It is used by `skill_warnings` (Claude and Codex), by `skill_note` (Codex prompts name `` `orchestrate:<skill>` `` plus the file path) and by `agent_installed` (plugin agents get `--agent`). `agent_installed` and `install_agents.sh --global` now honour `CLAUDE_CONFIG_DIR`. | `test_holistic_7_*` (2): this repo's nested layout, another plugin's copy not counted, `--agent` on a plugin install; `Fold.test_item7_*` |
| 8 | Reviewer fails only on material defects | Resolved | review-milestone: whether a finding blocks is set by the definitions, not by the reviewer's view. A finding blocks when it breaks an item statement or the `bar`, or, outside the items, when it causes a regression, breaks the design or a contract, loses data, is a security problem, or is a sign of faked work. Other findings are advisory: reported, but the state doesn't change. Last-line counts are blocking findings only. `done-when.md` transition table and `FINDINGS_TEMPLATE` updated to match. The leniency evidence is now dated to Opus 4.5/4.6. | `test_holistic_8_*` |
| 9 | Effort defaults | Answered, no code change | Orchestrate keeps medium for builders and reviewers and high for planners. `build/SKILL.md` and the README say medium is the owner's choice and to raise effort only where a run has been seen falling short. `profile.md` now says a planner ignores the profile's `Effort`, which settles Astra 13's precedence question by documenting it. The instructing-agents half of the decision belongs to the other agent. | none; prose only |

## Where a reviewer's claim didn't hold, or needed qualifying

- **A6/F3: the plugin glob misses this repo.** Both claims hold. `plugins/**/skills/<name>/SKILL.md` requires `skills/`
  to be the direct parent, and this repo installs at `skills/orchestration/<name>`. The old test passed only because it
  used a flat layout that this repo doesn't produce. A copy of the whole repo sits under every plugin's cache folder,
  so matching files on disk would also report skills that another plugin carries. That's why the resolver reads the
  marketplace entry.
- **F4/A6: `--agent` with a plugin agent.** The Claude sub-agents docs confirm a bare name works when it's
  unambiguous. The plugins reference confirms an entry's `agents` takes `.md` file paths, which is what the manifest
  has. So RESULT-D's `Agents (0)` has no explanation in the docs. If plugin agents really don't load, `--agent` on a
  plugin-only install could fail the review turn. That needs a live check (see Owed).
- **F1: frontmatter overrides the launch.** The skills docs confirm it, and it goes further than F1 said. A Claude
  agent file's `effort` also overrides the session effort, and the loop passes `--agent`. So the agent files had the
  same problem, and I fixed them too. The Codex TOML agent stays: the loop doesn't use it (`codex exec` takes the
  prompt), and for a Codex chat spawn it *is* the launch setting.
- **Synthesis 2 wording ("a restriction passed with `--message` is stored").** I didn't build that. `--message` also
  carries review findings and NEEDS_CONTEXT answers, which shouldn't persist. Astra's own advice was to keep findings
  separate, so a new findings message can't replace a permission. Scope is the module, not the milestone, because a
  conversational rule like "don't touch the schema" isn't tied to one milestone, and dropping it at the next milestone
  is the same loss. The state is per worktree: a lead in another worktree won't see it.
- **A1 "it also risks integrating partially written plans".** This holds. The fix lands nothing unless the result is
  `PLANNED`.
- **A3.** This holds: before the fix, nothing capped progress-only turns except the four-hour budget. Uncommitted
  edits now count as work, so a builder that is busy but hasn't committed isn't stopped.

## Per-turn cost

The builder's restatement grows by about 12 words (the objective), plus one short sentence per owner rule. A
continuation grows by the open item ids. The model/effort lines, about 6 words, are gone from every prompt. Skill
bodies changed by under 100 words in total.

## Checks

- `python3 -m unittest discover -s tests/orchestration -p 'test_*.py'`: 135 tests pass (121 before; 14 new).
- `check_skill.py` returns ok on build, build-milestone, plan-module and review-milestone.

## Owed (not done here)

- A live Claude plugin install: does `orchestrate-evaluator` load from the `strict: false` entry, and does `--agent`
  take the bare name? Also, does Codex accept `` `orchestrate:review-milestone` `` (or `$orchestrate:review-milestone`)
  as a skill mention? The prompt gives the file path either way.
- The live resumed-Claude claim from the synthesis, which shows the objective sentence and confirms the frontmatter no
  longer moves the effort.
