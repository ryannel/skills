# Orchestrate cleanup: the audit

Seven reviewers read every agent-facing file in `skills/orchestration` and the prompts in `agent_loop.py`. Five
each looked for one kind of problem, and two read everything. Their reports are in `reports/`. This file merges
them.

The principle: a skill says what the tool is, which command to reach for when, and the judgement that is the
agent's own. The CLI holds how it works: paths, defaults, settings and procedures, through its `--help`, its
output, and work it does itself.

## Why the skills copy the CLI

The reviewers all reached the same reason. The script already documents almost every command, result and default
in the roughly 480-line description at the top of `agent_loop.py`, but no agent can reach that text through the
CLI. No subcommand's parser has a description, so `run --help`, `merge --help` and `human --help` print a list of
flags and nothing else. Some flags say "(default: see above)", which points at text `--help` never prints. With
nothing to read, the skills copy the content, and the copies drift.

## Size now and after

| Skill | Lines now | After |
|---|---|---|
| lead | 1,057 | about 400 |
| planner | 1,282 | about 760 |
| builder | 295 | about 185 |
| reviewer | 343 | about 300 |

## Drift: prose that is already wrong

- Stage 2 (lines 20-23) says to commit the settings by hand "because adopt never merges the settings". `adopt`
  does merge a first ORCHESTRATE.md (`adoptable()`), though its strict settings read stops when `Test command:` is
  missing.
- The lead skill's output rules (one JSON line with `version`, `warnings` and `result_file`, exit 0 for the
  command's own result) hold only for the commands that go through `emit()`. `ready` and `settings` print JSON over
  several lines with no `result`. `adopt` and `migrate` exit 1 on REFUSED or FAILED. `status`, `report` and `check`
  print text.
- `settings` reads the worktree's copy of ORCHESTRATE.md, while `run`, `review`, `plan` and `merge` read the main
  branch's. A lead confirming settings from an old worktree sees the wrong values.
- `cleanup` keeps `next` only with `--json`, so "its `next` carries the question" fails by default.
- The builder skill says the script refuses a LOG.md entry over eight lines. `merge` only warns; `plan` and
  `adopt` refuse.
- `done-when.md` hard-codes `.orchestrate/evidence/<MODULE>/` in three places, which is wrong for a project whose
  `Evidence:` line names another folder.
- `done-when.md` says the escalation steps are written down only there. There are five copies, and the README's
  table leaves out the return to the same builder after four or five failed reviews.
- 4-build says any command prints REFUSED. Only `run`, `adopt` and `migrate` do.
- The GLOSSARY says On Dependency needs an already planned milestone, and leaves out `for_planning`.
- The README gives the script as about 13,500 lines (it is 15,695), and leaves out the end-of-stretch review.
- The design-review prompt's `{briefs}` placeholder is always empty.
- `review` without `--commit` fails with "commit None doesn't exist" instead of using the Ready for Review record's
  commit.

## What the CLI needs, in the order it unlocks deletions

1. **Help on every command.** Move each command's part of the script's description into its parser's description
   and epilog: what it does, its results, its exit statuses, and the fields of its output. Write new help for
   `human` and its verbs, `cleanup`, `background`, `jobs`, `wait`, `history`, `dashboard` and `flow`. Put the result
   contract (exit codes, the last JSON line, `next`, `warnings`, `changed`) in the top-level `--help`. Fix "(default:
   see above)" and the missing defaults. This alone lets most deletions happen, with no change to behaviour.
2. **One output path.** Every command ends through `emit()`: one JSON line with `result` and `version`, and exit
   statuses that follow the contract. `cleanup` keeps `next`.
3. **`settings` reports everything.** Read the main branch's copy, as the other commands do, and say which copy.
   Print every location as an absolute path (plans, module folders, working folder, evidence, records, logs,
   history, runs, graded examples, the script, the skill folders), each setting with where its value came from
   (a line, a default, an environment variable), and the model and effort each kind of agent gets on each host.
   Add `settings --template`, built from a schema table in the script that holds each setting's default, allowed
   values and help. Add `settings set <Label> <value> --said "<the user's words>"`, which commits the line on the
   main branch (and pushes under `Merge: push`) and records it as the user's decision; it refuses inside an agent
   session. ORCHESTRATE.md stays one prose file, because several lines are the user's own words.
4. **The script owns module worktrees.** `run --module M` creates or reuses the module's worktree on
   `build/<module>`, from the remote under `Merge: push` and from the local main branch otherwise, in an ignored
   folder; it removes a clean, merged worktree when the module finishes. Every `next`, including the ones `ready`
   and `status` print, names that worktree. `cleanup --kind worktrees` removes leftovers.
5. **Prompts carry what agents now read from skills.** The review prompt names the graded examples file and the
   design round ("round 1 of 2"), and drops `{briefs}`. Build and review prompts name the module folder. Codex-only
   notes go in the Codex build prompt.
6. **`next` where an agent now reads a reference.** `MIGRATED` and `definitions_naming_it` point at their `plan
   --kind fix` task. A failing main-branch check in `watch` and FAILING_ON_MAIN give a real `plan --kind fix`
   command, with a revert as the alternative. `MERGED` outside a run points at `run --checks-only`. A usage limit,
   a wrong model and `turn_not_stopped` give `decides: human` with an `ask`. A warning names a missing `Graded
   examples:` line.
7. **Smaller script work.** The script carries the diagnosis count to milestones split off in a diagnosis, so the
   planner stops setting it. `review` defaults `--commit` to the Ready for Review record's commit. A `revert`
   command replaces the four-step revert in `locks.md`. `ready` or `watch` reports the runs that ended since the
   last look, so the lead's restart routine is one command.

## What the skills lose

Lead (1,057 → about 400):

- Delete all of `references/`. `cleanup.md`, `settings.md` and `older-projects.md` go to `cleanup`, `settings set`
  and `migrate` help and output. `locks.md` and `delivery-history.md` go to `lock`, `main-check` and `history`
  help. `report.md` keeps about 18 lines of what the lead adds, folded into 4-build.
- `SKILL.md` (126 → about 65): the output contract moves to the top-level `--help`. In its place goes a table of
  the commands, one line each saying when to reach for it. The zsh quoting and revert explanations go.
- `stages/4-build.md` (401 → about 155): the worktree setup, the `watch` mechanics, the `ready` groups, the result
  table, the escalation steps, the `human` verbs and `alone` scheduling all go to the CLI. Kept: when the lead is
  woken, reading delivery, questions from agents, what it passes on, telling the user, and the five or six result
  rows that are the lead's judgement (a usage limit, a wrong model, a builder the user paused).
- Stage 2: fix the `adopt` error, and fold in about 10 lines of judgement from `profile.md` (push only with the
  user's permission, leave out model lines the user didn't name, review on the other host when both hosts build).
- Stage 1: cut the explanations of a pre-mortem and of requirements gaps, and the repeated point about a hole in
  the brief.

Planner (1,282 → about 760):

- `references/profile.md` (149 → about 40, or gone): the template and the model and effort order come from
  `settings --template` and `settings`.
- `references/done-when.md` (420 → about 120): keep the module table, the shapes of PLAN.md and LOG.md, and the
  DONE.json fields the planner writes. The statuses, the record file, who changes what, the escalation steps and
  STATUS.md are the script's internals; they move to the README for people.
- The look-options plan is written out in both `SKILL.md` and `proofs.md`; keep it in `proofs.md`. The `tasks/`
  files stay, because the script puts them in the planner's prompt, less a few lines of mechanics.
- Cut the testing-practice list and the explanation of thin slices.

Builder (295 → about 185):

- Delete the `needs` rules, lock rules, merge-failure cases and main-check statuses: the build prompt and
  `merge`'s own `detail` already carry them. "Without a lead" becomes "follow `next`".
- Cut the advice on waiting and reading logs, the "when a behaviour won't come" section, and the force-push and
  `apply_patch` notes.

Reviewer (343 → about 300):

- Delete "the script ran the checks" (twice) and the location of User Feedback: the prompt says both. Cut the list
  of signs of faked work and the bug-report recipe.

Across the set:

- Paths written out in about ten places go to `settings`.
- "A lock doesn't make the machine quiet" (six copies), the check/inspect/ask definition (five), the options-then-
  pick flow (five) and "status goes stale" (five): one copy each, where its reader is.
- About a dozen defaults restated in prose (effort, the 3-hour check-in, the 30-minute lock hold, the 1-hour
  test-command limit, the 9-minute wait) go to `settings` and `--help`.

README and GLOSSARY, which are for people:

- The README takes the lifecycle material leaving the skills, and can drop "Our own practice", "What our own runs
  showed" and "How much this has been tested". Its broken escalation table is fixed by the move.
- The GLOSSARY keeps names only, and its `Stored as` lines stop giving paths.

`orchestration-skill`, the authoring spec, gains the rule this audit applies, and its references to
`done-when.md`'s tables, `profile.md` and `lead/references/` change. Strings in `agent_loop.py` that name the
deleted files change too.

## Order of work

1. CLI help and one output path (steps 1-2). No behaviour change; the tests stay as they are, plus help tests.
2. `settings` (step 3) and the prompt changes (step 5).
3. Module worktrees (step 4) and the new `next` fields and smaller work (steps 6-7).
4. Rewrite each skill whole against the new CLI, delete the references, move material to the README, update the
   glossary and the spec, regenerate the saved prompts.

Each step ends with the full test suite, the skill checks and `claude plugin validate .`.
