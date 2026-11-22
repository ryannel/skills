# Sweep A: what in the orchestrate skills belongs in the CLI

Read in full: lead (SKILL.md, stages 1-4, references/*), builder (SKILL.md, prompts/*), planner (SKILL.md, tasks/*,
references/profile.md, done-when.md, proofs.md, prompts/plan.md), reviewer (SKILL.md, tasks/*, prompts/*,
references/graded-examples.md), and the prompt texts in `agent_loop.py` (templates at 560-645, `SCRIPT_SETS_STATE`
5143, `resources_rule`/`session_rule`/`needs_rules`/`binding`/`handoff_note` 7045-7190, `FINISH`/`CLAUDE_TURN_NOTE`
8919, `WATCH_WHY` 14996). Checked every subcommand's `--help` and the result-building code named below.
Line numbers are as on disk on 2026-11-22.

Legend for "Where": SCRIPT (script does it), OUTPUT (result carries it), HELP (`<cmd> --help`), SETTINGS (a file the
CLI reads / `settings` prints), DELETE, KEEP (agent's judgement), CUT (shrink to a clause).
"CLI today" says whether the CLI already does or says it.

---

## 0. Enabling change the rest depends on: `--help` is nearly empty, while the docstring already says it all

Almost every "move to `--help`" below is cheap because the content already exists in the module docstring
(`agent_loop.py` 1-500: a section per subcommand with every result code, field and default), but no agent sees it:
top-level `--help` says "The docstring at the top of this file explains the whole design", and subcommand help has
no description at all (`run --help`, `merge --help`, `lock --help`, `human --help` print bare flag lists).

Defects found while checking:
- `human --help` lists the verbs `{accept,rereview,reopen,scope,release,feedback}` with no meaning for any of them.
- `run/plan/review --help`: `--host ... (default: see above)` refers to text that isn't in that help. `--model`
  help on `run` and `review` says "e.g. 'Claude planner'".
- `merge`, `lock`, `locks`, `background`, `jobs`, `ready`, `next`, `unblock`, `pause`, `adopt`, `settings`: no
  description of what the command does or prints.
- Exit-status contract (0/1/2, `merge`/`check`/`lock`/`wait`/`main-check` own statuses) is only in the docstring
  (lines 50-60), so the lead skill repeats it.

Fix: give each subparser `description=` (its docstring section) and an epilog listing its result codes and their
fields; put the exit-status contract and "every result's last line is JSON with `next`" in the top-level epilog.
With that done, the deletions below are safe.

## 1. Whole files that can go (largest wins)

### 1a. `lead/references/cleanup.md` (40 lines) - DELETE, keep one clause
- 5-18 "What stays on the computer" (evidence under `<git common dir>/orchestrate/evidence/`, verify checkouts,
  logs, ledgers): paths and inventory. HELP/OUTPUT: `cleanup --help` already names each kind
  (`--kind` help text, `CLEANUP_KINDS` 13891); a `paths` command (see 2a) gives the locations.
- 22-24 "lists ... WOULD_REMOVE ... run with --yes only on their yes ... Its next carries the question": CLI
  already says it: `cmd_cleanup` 14090-14096 emits `next` with `decides: human`, the `ask` text and the "nothing
  removed can be brought back" reason.
- 26-36 kind table, defaults, `--older-than`, `--json`, never touches held modules/plans/history: duplicates
  `cleanup --help` (`--kind` help lists the same five kinds and the default four). The "never touches" guarantee
  is a one-line addition to the help description (it's in the comment at 13884-13889).
- 38-40 "Offer --older-than when the user wants to keep recent captures": KEEP as one clause in stage 4's disk
  paragraph.

### 1b. `lead/references/settings.md` (16 lines) - DELETE
- 3-5 pointer to profile.md: DELETE (stage 2 and 4 already link it).
- 7-8 "adopt won't merge a changed ORCHESTRATE.md ... commit it with git in the main working copy, on the main
  branch, and push it when Merge: push": a procedure the script should do. SCRIPT: a `settings --commit
  --human-words '<what the user said>'` (or `adopt ORCHESTRATE.md --human-words ...`) that commits and merges a
  changed settings file, recording the user's words, as `adopt` does for plan files. CLI today: `adoptable()`
  12217-12221 refuses a changed settings file with "the lead commits and merges it with git once the user has agreed
  to it", and `profile_note` 3550-3557 says the same; neither does it.
- 10-12 `settings_read_from`, `settings_differ`: describe output fields whose own text already explains them
  (`EMIT_EXTRA["settings_read_from"]` 929, `profile_note` 3555). DELETE.
- 14-16 `ran_on` vs `observed`, `WRONG_MODEL_OR_EFFORT`, "check ran_on in the next result before you tell the user
  a change has taken effect": KEEP the last sentence (judgement about what to tell the user), as one line in stage 4;
  the rest is output (`ran_on` set at 6970).

### 1c. `lead/references/older-projects.md` (86 lines) - mostly HELP/OUTPUT
Only reached when a command refuses with a message naming `migrate`, so the refusal and `migrate`'s own output can
carry nearly all of it.
- 7-10 how to run migrate, `--to`, what it moves, `MIGRATED`/`NOTHING`: duplicates `migrate --help`. DELETE.
- 12-14 "After a move, start a planner with `plan --kind fix` to bring the plans into the current shape": OUTPUT.
  CLI today: `MIGRATED`'s `next` is `status` (13879-13881), not the planner task. Make `next` the `plan --kind fix`
  command with that task text, and delete the paragraph.
- 18-41 committed evidence: what migrate does, `definitions_naming_it`, links break in fresh clones, history
  rewrite, `--commit-map`: the evidence migration's result already carries most of this (the detail at 13865-13872
  and the `definitions_naming_it` hint at 6507). Move the "tell the user a docs link checker will report those
  links" and the "after rewriting history run `migrate --commit-map`" into that result's `next`/`why`. DELETE here.
- 45-48 worktrees with pre-migration commits: `migrate` already lists `worktrees_on_old_names`; give each entry its
  `migrate --branch --worktree <path>` command in OUTPUT. DELETE.
- 52-66 names changed in 2.2, `owner` -> `human`: history. The script accepts the old names and migrates them; the
  lead needs none of it. DELETE (the `CHANGES` dict already reports changes per version).
- 70-72 Ready for Review set by a builder before 2.1.0: CLI already says it (`INVALID` with `next` naming `run`).
  DELETE.
- 76-78 daily reports before 2.4: DELETE.
- 82-86 no `Graded examples:` line: OUTPUT - `settings`/`report` can warn "no Graded examples line; the user's
  overturned reviews aren't kept" with the line to add. CLI today: `settings` prints `graded_examples_named`
  (888) but no warning. Then DELETE.
- Net: file reduces to nothing; SKILL.md 125-126 keeps "a command that names `migrate`: run what its `next` says".

### 1d. `lead/references/locks.md` (59 lines) - split: mechanics to HELP, keep ~8 lines of judgement
- 8-12 what a lock is, exclusive vs shared, `.alone`: duplicates the builder prompt's `resources_rule` (7061-7081)
  and belongs in `lock --help` (empty today). The lead never takes a lock. DELETE.
- 14-15 lock doesn't make the machine quiet: duplicated in builder SKILL 187-188, done-when 225, proofs 112-113,
  `resources_rule`. Keep once (proofs.md, for planners). DELETE here.
- 17-19 Lock hold limit 30 min default, test command exempt with 1 h: defaults. SETTINGS/HELP (`settings` prints
  `lock_hold_limit_s`). DELETE.
- 21-26 `locks` / `flow` and how to read lock queueing ("busy most of the day ... fewer builders on that resource,
  a cheaper proof, or a check that runs once on the main branch"): KEEP (lead's judgement); fold into stage 4
  "Reading delivery" and drop the file.
- 30-41 main-branch checks: how runs are triggered, intervals, `main-check --start`, `ALREADY_RUNNING`,
  `runner.log`, `RAN`: mechanics. HELP (`main-check --help` has the flags but no results). DELETE.
- 42-47 on a failure: "Start a planner with `plan --kind fix` naming the commit ... or revert": OUTPUT. The
  failure already names the commit and modules (docstring 435-438); give `watch`'s warning sign a `next` with the
  `plan --kind fix` command and `alternative` naming the revert. KEEP one sentence of judgement: revert when the fix
  would take long.
- 49-53 revert procedure: `git revert`, tell the builder via `run --message`, `human rereview` if the reverted work
  was Done, then `main-check --start`: KEEP "revert, never rewrite" (it's in SKILL.md 89-90 already) and the
  rereview judgement; the start-a-run step is a SCRIPT job (`main-check` could start a run when the tip moves past a
  revert of a failing commit). CUT to two sentences.
- 55-59 exit 75 / `unjudged`, item waits without a turn: mechanics; the planner needs exit 75 (proofs.md 95-97
  has it). DELETE here.

### 1e. `lead/references/delivery-history.md` (51 lines) - CUT to ~6 lines in stage 4
- 5-12 read the history before proposing a process change, read a version's figures beside its turn count, offer
  the dashboard for cost/retro questions: KEEP (judgement).
- 16-23 what is copied, where (`~/.orchestrate/history/<repository>-<hash>/`, `$ORCHESTRATE_HISTORY_DIR`),
  `reviews/<MODULE>/`: paths and mechanics. CLI today: `history` prints `folder` (12139-12143); move the
  description into `history --help`. DELETE.
- 25-28 also reads sessions that ran without it: HELP. DELETE.
- 32-39 `history --json` / `dashboard --open` / `--json` contents: duplicates `history --help` and
  `dashboard --help`. DELETE except naming the two commands.
- 43-51 three cost measures, weighted-token ratios (cache 1/10, output x5 / x8): mechanics of the numbers. OUTPUT:
  the history output should label each figure (the file itself says "says which is which wherever it shows one").
  DELETE.

### 1f. `planner/references/profile.md` (149 lines) - template to SETTINGS, keep the judgement
- 7-13 how the script parses `- **Label:** value`, `settings` confirms, `Merge` and `Test command` required:
  CLI already says it: `settings` fails with the missing line named (`REQUIRED` 652-653 carries the explanation).
  CUT to one sentence.
- 22-49 the file template, with a `*(script: ...)*` note on every line giving defaults and meaning:
  this is the CLI's own schema (`PROFILE_FIELDS` 646-650, `ALLOWED`, `ONE_WORD`, `role_lines`) written out by hand.
  SCRIPT/SETTINGS: add `settings --template` (prints the template generated from `PROFILE_FIELDS` with each
  line's default and meaning) and have `settings` print, per line, value + `source: set|default`. Keep in the skill
  only the lines the script doesn't read (Purpose, Quality bar, References, Targets, Starting from a clean clone,
  Project guidance) and why they exist.
- 62-69 Rules lines' notes (Exclusive/Shared resources, Test command lock, Lock hold limit 30 min default,
  Main-branch check syntax `every`/`gap`/`lock`/`timeout`): same; the `Main-branch check` syntax is parsed by
  `main_check_lines` 14170 and should be in `settings --template` and `main-check --help`.
- 77-82 who writes which line; leave host/model lines out unless the user named one; Claude-only projects set
  `Default host: claude`: KEEP (judgement about the user's choices). The Default-host advice could be OUTPUT:
  `settings` preflight can warn when Codex isn't installed and no `Default host` is set.
- 84-86 Setup command reruns only when a manifest/lockfile changes; install into ignored folders, `npm ci` over
  `npm install`: first sentence is SCRIPT behaviour -> HELP/template note; second is planner judgement, KEEP one
  clause.
- 88-91 `Merge: push` is standing permission; note when AGENTS.md says not to push: KEEP.
- 93-104 `Review host` same/other/host semantics, `Planner host`: semantics -> template/`run --review-host` help
  (which already explains `other`). KEEP "write `other` when the user builds with both hosts, because a reviewer
  from another company shares fewer blind spots" - but it is duplicated in lead stage 4 175-178; keep it once.
- 106-110 fixed file names need no line; no status here: KEEP last sentence only.
- 114-147 per-role model/effort lines, the table, and the two precedence lists (model: `--model` > role line >
  host model line > built-in; effort: `--effort` > role-on-host > role > high/Effort): this is `role_setting()`
  (726-736) in prose. SETTINGS/OUTPUT: `settings` should print the resolved model and effort for each kind of agent
  on each host, and the forms should be in `settings --template`. KEEP: "a model belongs to one host" (2 lines, the
  reason a line names a host), "a larger model spends quota faster". The rest DELETE.
- Net: file falls from ~150 to ~40 lines.

### 1g. `planner/references/done-when.md` (420 lines) - roughly half is the script's state machine
- 20-41 "Where everything is" tree: duplicates planner SKILL 21-34, lead SKILL 76-79, module.md 6-7, builder SKILL
  30-31, reviewer SKILL 39-40, and the docstring 28-41. See group 2a. KEEP one copy (here) or replace all with
  `settings`/`paths` output.
- 47-50 evidence never committed, opens in every worktree via a link into `.git`, cleared with `cleanup`:
  mechanics, repeated in builder 51-57, reviewer 25-28, cleanup.md 7-13. CUT to "evidence lives in the working
  folder, uncommitted".
- 61-82 `STATUS.md` sections ("Needs you now", "Choices made for you", 7-day "Recently done"): describes script
  output. DELETE except 80-82 (name milestones for what someone can see; already in module.md 28-29 - keep once).
- 86-99 module table header: duplicated in planner tasks/project.md 10-17. KEEP one copy. The exact-header
  requirement is enforced by the script (`TABLE_HEADER` 12392); its refusal message should show the header.
- 124-127 `plan_ahead`, Waiting: For Planning mechanics: script behaviour; the planner only needs "name later
  milestones as headings without items". CUT.
- 152-155 the five plan-file checks (1,500 words, status lines, `###`, `## Log`, lines under Done): CLI already
  enforces them in `plan`/`adopt` with messages (`plan_checks`). CUT to "plan and adopt refuse a plan file that
  grows (status lines, long notes); the message says what".
- 161-163 LOG entry max 8 lines: CLI enforces (`LOG_ENTRY_LINES` 12299, message 12353). CUT the number.
- 222-233 `lock` and `reads` mechanics (reuse rules, `run_changes`, pathspec edge cases): keep what each field
  means (2 lines each); the reuse rules go in `check --help`. CUT.
- 236-246 `needs` types: duplicated in builder SKILL 94-109, lead stage 4 271-275, `needs_rules()`. KEEP here (the
  planner writes them), CUT the builder copy (see 3c).
- 250-253 `alone` mechanics: duplicated in lead stage 4 366-371 and proofs.md 98-101. KEEP the planner's judgement
  (one milestone per project), DELETE mechanics.
- 254-258 depends_on errors the script reports: CLI already reports them; CUT to "the script refuses impossible
  depends_on".
- 279-284 the three counts and `diagnosed_for_planner_finding`: script-owned fields. DELETE (the script puts back
  any change, per diagnose.md 34).
- 286-289 which milestones need a reviewer: duplicated in planner SKILL 143-144. KEEP once (SKILL).
- 293-329 Statuses table with "Printed as" column, blocked reasons, design statuses incl. `by: review_limit`:
  the "Printed as" column and design-status mechanics are output vocabulary -> `ready --help`/`status --help`.
  KEEP the status names and their meaning (agents write `status`), the blocked-reason table can go to HELP since
  every BLOCKED result carries `reason` and `next` naming who steps in. CUT by ~half.
- 333-351 the record file: hash, commits, usage, adoption of pre-existing repos: script internals. KEEP one
  sentence ("a milestone is Done only when RECORD.json says so; only the script writes it"). DELETE rest.
- 355-387 "Who changes what" table, 17 rows: 11 rows are transitions the script makes and enforces (and rejects
  violations with a message). KEEP a per-role list of fields each agent may change (3 lines: builder, reviewer,
  planner); DELETE the script rows. The builder, reviewer and binding() restatement already carry their own fields.
- 391-420 escalation steps table and counts reset rules: the script applies them and every FAIL result names
  `escalation` and carries `next` with the message/task already written. Move the table to `next --help`. KEEP
  404-406 ("after a failed review the milestone is finished when every item is true as written") - it's also in
  builder/prompts/findings.md, so maybe keep only there.
- Net: ~420 -> ~200 lines.

## 2. Groups that share one fix

### 2a. File layout and paths, written out 6+ times -> one `paths` command (or `settings` output)
Passages: lead SKILL 76-83; planner SKILL 18-36; done-when.md 22-41; planner tasks/module.md 6-7; builder SKILL
30-31 and 51-53 (`<evidence>/<MODULE>/<milestone>/`, default `.orchestrate/evidence`); builder 76
(`<milestone>-handoff.md`); reviewer SKILL 25-33 (evidence default, graded examples path); reviewer tasks
milestone.md 61-62, design.md 53; cleanup.md 11-17; delivery-history.md 19-23; report.md 13-14.
CLI today: `settings` prints `plans`, `evidence`, `graded_examples` (resolved, 886-888); prompts already pass
`{done}`, `{captures}`, `{handoff}`, `{review}`, `{glossary}`. Missing: the git-common-dir working folder,
results dir, history folder, reports dir, per-module file paths, and the graded examples file in the review prompt.
Fix: `paths --worktree . [--module M] [--milestone id]` printing every location (plans folder and each project file,
module files, evidence folder and its real target, handoff, review, graded examples, results, history, logs). Then
skills keep the concept names only ("the done-when file", "the working folder") and say "`paths` prints where each
is". Add `{graded}` to `review.md` so reviewer SKILL 30-33 can go.

### 2b. Defaults repeated in prose -> settings output only
- Plans folder `docs/plans`: lead SKILL 76, planner SKILL 19-23, done-when 22-23, profile 28.
- Evidence `.orchestrate/evidence`: builder 53, reviewer 26, planner SKILL 32, done-when 39/47, profile 29,
  older-projects 25.
- Effort medium / planners high: lead stage 4 26-28, profile 44 and 115-116 and 145, `--effort` help.
- Lead check-in 3 h: stage 4 62, profile 37 (`LEAD_CHECK_IN_S` 14986).
- Lock hold limit 30 min / test command 1 h: builder 197, locks.md 17-19, profile 66, proofs 71-72.
- `wait` nine minutes: builder 204 (`--timeout` help says 540).
- Fresh session at 60% full: `run --fresh` help only (good).
- No-progress 2 h warning, 15-minute open tool call (stage 4 63, 204).
Fix: `settings` prints effective values with `source`; skills drop the numbers (keep the reason a setting exists
where it is a judgement). CLI already prints most of them in `settings`.

### 2c. "What each result means" tables that `next` already covers
- lead stage 4 182-210 (result table + the paragraph of minor results + main_broken/merge_kept_later),
  stage 4 122-134 (`ready` groups table), 146-149 (`unmerged_plans` -> `adopt`), 172-173 (planner merges only on
  PLANNED), 203-205 (`unblock`, `stopped_turn`, `warnings`), 224-237 (escalation steps), 246-249 (design review
  rounds), 379-382 (graded example, human refuses during a run).
CLI today: `drift_fields` 3560-3573 writes the `adopt` next with its reason; `after_pass` 9443-9448 writes the
FINISHED next (incl. removing the worktree); `main_broken_result` 11262-11270 the builder's instruction; run's
docstring 75-140 lists every result code. KEEP from these only the rows that need the lead's judgement:
`HOST_FAILED` with a usage limit -> tell the user (moving hosts is theirs); `WRONG_MODEL_OR_EFFORT` -> tell the
user; `PAUSED` -> leave it to the user; a `BLOCKED` reason is the builder's reading, weigh it; "the counts are the
record, don't step around them"; "add nothing about which findings to fix". Move the rest into each result's `why`
(where it isn't already) and `run --help` epilog. ~60 lines.

### 2d. Builder-side passages the build prompt or `merge`'s output already carry
- builder SKILL 170-179 (`conflicts`, items changed by a planner, `main_broken`): CLI already says each, word for
  word in substance: conflict detail 11315-11319, stale definitions 10766-10771, `main_broken_result` 11267-11270.
  DELETE.
- builder SKILL 161-168 (merge rebases, runs test command, push vs fast-forward, batches, bisects, `batch` field):
  HELP (`merge --help` is empty). DELETE.
- builder SKILL 58-60 (`merge` refuses a commit that sets Ready for Review/Done): CLI already says it
  (`state_refusal` 10764, `SCRIPT_SETS_STATE` 5143). CUT to "leave status in_progress; the script sets the rest".
- builder SKILL 70-74 (after DONE the script reruns checks in a clean copy outside your sandbox ...): duplicated by
  build.md line 3. CUT to "no need to rerun checks after you merge".
- builder SKILL 94-109 (`needs` types and what to do): the prompt's `needs_rules()` 7139-7166 sends, per milestone,
  exactly which items need what and the ending to use, adapted to headless/visible. KEEP only judgement not in it:
  "when the user turns down every option, make new ones only if their words say what to change, else BLOCKED", "say
  which commit to run and how to start it", "a later session cites the recorded feedback". DELETE the rest.
- builder SKILL 183-198 (locks): the prompt's `resources_rule()` 7061-7081 names this project's resources, `lock`,
  `.alone`, the hold limit; `cmd_lock` 10411 refuses wrapping `check`/`merge` with the reason. KEEP: check the user
  is there before taking a lock for an attended run; do other work while waiting; BLOCKED only if the holder seems
  stuck. Move the rest to `lock --help`.
- builder SKILL 152-157 (main-check item results NOT_ON_MAIN/COVERED/PENDING/FAILING_ON_MAIN): each result carries
  a `why` (14508, 14542, 14552). CUT to "an item whose check is `main-check <name>` passes from the main branch's
  run after you merge; its result says what to do".
- builder SKILL 260-273 (without a lead: `run --checks-only`, then `review`, then `next`): READY_FOR_REVIEW's
  `next` is already the review command on the review host (docstring 83-84). CUT to "run `run --checks-only` and
  follow its `next`; only a review the script starts counts". SCRIPT option: `run --checks-only` could chain into
  the review itself (as `run` does with a lead).
- builder SKILL 76-81 handoff path, read-earlier, rewrite: `{handoff}` and `handoff_note()` 7110-7114 carry path
  and read/rewrite. KEEP only what to put in a handoff.
- builder SKILL 128-131 `check` mechanics (remembered pass): HELP. KEEP the command name.

### 2e. Worktrees: the user's example, and around it
- lead stage 4 37-41 "Give each module its own worktree ... `.git/info/exclude` ... `git worktree add -b
  build/<module> <folder>/<module> <remote>/<branch>` ... With Merge: local, branch from the local main branch":
  SCRIPT. CLI today: does not create builder worktrees (only its own detached checkouts: `git worktree add
  --detach` at 4666 and 14304); it already has the pieces (`git()` helpers, `ignore`-list writer at 1173 using
  `info/exclude`, `base_ref(prof)` for remote vs local). New behaviour: `run --module M` without `--worktree` (or
  with `--worktree auto`) creates or reuses `<ignored folder>/<module>` on `build/<module>` from the right base and
  prints its path. DELETE the paragraph, including the explanation of what a worktree is.
- lead stage 4 195 "FINISHED: Remove its worktree once nothing is unmerged", 400-401 "remove build outputs and the
  worktrees whose work is merged", and `after_pass` 9446 telling the lead to run `git worktree remove`: SCRIPT -
  the script knows when nothing is unmerged; it can remove a worktree it created on FINISHED (or `cleanup --kind
  worktrees`). Then DELETE.
- lead SKILL 53-57 "`next` names the worktree of the command that printed it, so a `next` from `ready` or `status`
  run in the main working copy needs the module's own worktree put in its place": a CLI defect described in prose.
  SCRIPT: the script records each module's worktree (`last-runs.json`, `RUNS_FILE` 2531, run state) and should put
  that worktree (or the one it would create) in `next`. Then DELETE.
- lead stage 4 267-268 "Every worktree keeps its own build outputs ... Clear those in worktrees nothing is using":
  same, `cleanup` could list stale worktrees' build outputs. CUT.

### 2f. Settings commits done by hand -> one script command
- lead stage 2 20-23 "commit the brief, the glossary and the settings with git on the main branch, and push them
  under Merge: push, because adopt never merges the settings": contradicts the CLI. `adoptable()` 12215-12221 and
  the docstring 264 say adopt DOES merge a first ORCHESTRATE.md (one the tip lacks); BRIEF.md and GLOSSARY.md are
  plan files `adopt` merges too. So on a new project `adopt --worktree <repo>` does all three. Fix the prose (CUT to
  "run adopt") - this is a correctness bug in the skill, not just duplication.
- lead stage 3 22-23 and stage 4 30-33/66 and settings.md 7-8 (commit a changed settings line by hand): SCRIPT, see
  1b (`settings --commit` with the user's words).

### 2g. Options/pick flow described five times
planner SKILL 124-134; proofs.md 160-182; planner tasks/project.md 39-41; tasks/change.md 21-26; lead stage 4
373-377. The script part (pick Done -> `plan_ahead` lists a planner task and `plan --kind change` per module) is
OUTPUT already. KEEP the full description once (proofs.md "Subjective work"), a 2-line pointer in planner SKILL,
and in lead stage 4 only "when the user turns every option down, give their words to a planner as a `--kind change`
task". DELETE the other copies.

### 2h. Same agent-behaviour advice duplicated across skills
- "Long commands: `background`/`wait`, few long waits beat many short looks, read the end of a log, judge video
  from stills": builder SKILL 202-209 and reviewer SKILL 77-81. Mechanics -> `background --help`; keep the
  cost reason once per skill as one sentence.
- Item kinds (check/inspect/ask) defined in builder SKILL 39-47, reviewer SKILL 39-48, planner SKILL 93-104,
  proofs.md 17-24, done-when 215-219. Fine to keep a 3-line definition per role, but the builder/reviewer copies
  can drop to one line each with the link.
- `ready`/`watch` moves list: lead stage 4 79-89 and `WATCH_WHY` 14996-14999 say the same moves. Keep the list in
  the skill (judgement); shorten `WATCH_WHY` to "act on these, then start this command again", or vice versa.
- `Review host: other` rationale: lead stage 4 175-178 and profile.md 100-101. Keep once.

## 3. Long passages by file (not already listed above)

### lead/SKILL.md
- 36-43 exit statuses, result_file, RUNNING: HELP (top-level epilog; docstring 50-60 has it). KEEP one sentence:
  "don't send output to /dev/null or `tail`, because a refused command looks like success" (agent behaviour), and
  "after a restart read the result files".
- 45-51 `next` / `decides: human` / placeholder: KEEP (how to use the tool), CUT by a third.
- 60-62 repeat `--task`/`--message`, single quotes, "zsh stops on brackets": `--message`/`--task` help already says
  repeatable. Shell quoting is general knowledge. CUT to a clause.
- 64-68 newer copy installed, `changed`: KEEP (re-read the skill is the lead's action).
- 72-83 project files and their paths: see 2a. KEEP the three definitions (module, milestone, item) and STATUS.md
  as the user's page.
- 99-100 "A note that says otherwise is from an older version of this set": DELETE.
- 116-120 run `settings` to confirm; it fails without Merge/Test command "because the script won't guess":
  CLI already says it (`REQUIRED` 652). CUT to "run `settings --worktree <repo>` once".
- 122-123 read `runs`, result files, `ready` before restarting "so you don't start a second run": CLI already
  refuses a second run on a held module (`IN_PROGRESS_ELSEWHERE`, run lock). CUT to a clause.
- Stage table 107-112: KEEP. Optional SCRIPT: `ready` could print a `stage` field (it already gives `unplanned`,
  and `run` refuses without a Builders count), which would make the table a lookup.

### lead/stages/1-interview.md (161 lines)
All of it is the lead's judgement (interview method, brief template). KEEP. Two small cuts:
- 103-105 "have a fresh subagent read it ... With no subagents, reread" - KEEP.
- 119-120 glossary "as the domain-language skill describes" - fine.
No CLI content here.

### lead/stages/2-start-planning.md
- 6-10 write settings from the template: KEEP, pointing at `settings --template` once it exists.
- 12-18 ask the user how agents should work, write host/Merge/Human decides, leave Builders out: KEEP
  (judgement). "because run starts no builder until it has one" - CLI already says it (run REFUSED with
  `decides: human` next). CUT.
- 20-23 see 2f (incorrect).
- 25-28 `plan --one-step` with the brief path and builder count in the task: KEEP. SCRIPT option: `plan` could add
  "The project brief is ..." and "up to <n> builders" itself, since it reads BRIEF.md and the Builders line - then
  the lead passes only the user's words.
- 31-34 `--kind change` "gives the planner its instructions for changing a plan" and "the changed milestones go
  back to Not Started": duplicates `plan --kind` help and script behaviour. CUT.
- 36-38 duplicate of stage 4 30-33. DELETE one.

### lead/stages/3-before-first-build.md
- 10-17 show assumptions, references, proposed names from the plan's report: KEEP. OUTPUT option: `plan`'s result
  could list `assumptions`, `references`, `proposed_names` as fields (stage 4 342 says "a later plan's
  `assumptions`" - check whether the field exists; the lead otherwise parses the report tail).
- 18 "Remove the `Proposed:` line ... and adopt the glossary": KEEP.
- 22-23 commit Builders line by hand: see 1b/2f.
- 25-28 /clear or /compact advice: KEEP.

### lead/stages/4-build.md (401 lines) - besides 2c, 2e
- 19-24 KEEP. 26-28 CUT to the judgement (pass `--model`/`--effort` only for a one-off ask; a flag hides later
  settings changes); defaults are in help.
- 43-53 what `run`/`plan` chain through, `steps_run`, `stopped_because`, `--one-step`: duplicates `run --one-step`
  / `plan --one-step` help. CUT to "read `stopped_because` first".
- 55-57 one background command per run, don't chain: KEEP (host behaviour).
- 61-72 `watch`: default 3 h, `CHECK_IN`/`WARNING_SIGNS`, restart it, `--runs`, `woke_for`: CLI already says
  restart (`WATCH_WHY` next 15304) and `--runs` (help). CUT to two sentences: keep `watch` running in the
  background; with a host that doesn't wake you, use `watch --runs`.
- 76-93 KEEP (core judgement).
- 97-118 KEEP; 102-104 `flow --since` detail is help.
- 136-144 `status --module`, `plan_ahead`: CUT; keep "a module whose Needs the script can't read, such as one
  waiting on the user's decision, isn't listed: plan it when the user says".
- 153-161 starting-agents table: KEEP the table (which command for what); it duplicates usage lines but is the
  "which command when" the target allows. Drop 160-161.
- 163-170 planner `--module` scope: duplicates `plan --module` help and `scope_text`. CUT to "give `--module` to a
  task that reaches one module, so planners run side by side".
- 175-178 review host: see 2h.
- 253-257 sandbox/network/`.git`: KEEP 2 sentences; `blocked_write` output has the fix.
- 259-262 browser module on Codex -> Claude, or ask the user about `danger-full-access`: KEEP (judgement; the user
  decides). `settings` preflight already has `browser_warnings`.
- 264-265 `ORCHESTRATE_VISIBLE=1`: KEEP a clause.
- 271-275 `needs_access`/`needs_hardware`, next with `ORCHESTRATE_VISIBLE=1`: CLI already says it (docstring
  93-97; next is that command). CUT to "put its `ask` to the user and run `next` when they're there".
- 279-288 stopping sessions: `pause` help + `turn_not_stopped` text (7744-7746) already tells what to do. KEEP:
  "never kill processes by name"; "wait for the user to stop a thread that didn't take the stop before running the
  module again". CUT rest.
- 292-312 what you pass on: KEEP; 305-308 `--kind change` description duplicates `plan --kind` help, CUT.
- 316-350 questions: KEEP.
- 354-364 human verbs table: HELP (verbs are undocumented in `human --help` today - must be added first). KEEP:
  "a reviewer can't count a `--message` as the user's words", and the `scope` rule (only for an edit the user
  dictated exactly; show the diff; run on their yes).
- 366-371 `alone` milestones: mechanics duplicated in done-when 250-253. KEEP: start it when other modules can
  spare the time; gather sittings; `pause` a builder rather than ask for one more slot.
- 386-396 KEEP.

### lead/references/report.md (46 lines)
- 10-14 `report` default window (since last report >1 h old, else 24 h), `--since`, `--write` path: duplicates
  `report --help` (`--since` and `--write` help give both). CUT to the command name and "pass `--since` for a
  stretch the user names".
- 16-18 list of the report's parts: describes output. DELETE.
- 22-46 KEEP (what the lead adds; judgement). 33-34 "while graded examples hold fewer than about ten, which the
  report flags": the flag is output, keep the action.

### builder/SKILL.md (275 lines) - besides 2a, 2d
- 12-18 roles, `python3 <lead folder>/scripts/agent_loop.py` "which your prompt gives": KEEP short (builder may run
  without a lead).
- 30-37 which milestone a task means; "A plan from an older version ... steps to tick and stop rules": the latter
  is legacy; `migrate`/`plan --kind fix` should convert; DELETE.
- 51-57 evidence path/default/commit rules: CUT to "evidence where your prompt says, uncommitted; commit code, plan
  files you change and anything a check reads"; keep the `ENGINE M3:` subject (the merge queue records the module
  itself, `LANDED_FILE` 10912, and falls back to the subject, 10918 - so it's still useful, keep one clause).
- 61-64 LOG.md 8 lines "the script refuses a longer entry": CUT the number; KEEP "verified kept apart from probably".
- 65-68 last-line forms and reasons: KEEP (contract the script parses; build.md says "The skill lists the reasons").
- 83-92 builder's three fields; stand-in rule: KEEP (binding() restates fields, but the stand-in judgement is only
  here).
- 111-124 KEEP.
- 133-150 KEEP (inspect yourself, link paths from repo root, recapture after `upstream_files`, keep check inputs
  in the repo).
- 213-218 KEEP.
- 222-231 On Codex: escalation request and `yield_time_ms` are host-specific facts worth keeping; "the sandbox
  refuses `ps`" KEEP a clause; 230-231 `apply_patch` vs `str.replace` is general tool knowledge for a Codex model -
  DELETE.
- 235-256 KEEP.

### builder/prompts/build.md, findings.md
Lean and correct; they carry per-session facts. No change, except: `{captures}` makes builder SKILL 51-53's path
redundant (done in 2d).

### planner/SKILL.md (177 lines) - besides 2a, 2g
- 18-36 path tree and "the settings' Plans: and Evidence: lines can move the two folders": see 2a.
- 40-161 KEEP (planning judgement), with 143-144 kept as the one copy of "which milestones get a reviewer".
- 153-154 changing items resets progress; `lock`/`reads` don't: KEEP (cost the planner weighs).
- 170-173 `check` from the prompt, fail vs error; "`plan` runs it before your files merge, and a failure sends your
  turn back": plan.md line 10 already gives the command and semantics; the last clause is OUTPUT. CUT to "every
  check you wrote should say fail on unbuilt work; error means the check is broken".

### planner/tasks/*.md
- change.md 11-14 how the script counts a change as the diagnosis / restarts a Too-Many-Failed-Reviews milestone:
  script behaviour; DELETE (no decision depends on it).
- diagnose.md 32-34 "Give each milestone you split off a `diagnoses` count one higher": a bookkeeping procedure
  the script could do. SCRIPT: carry the count to milestones a diagnosis adds (new IDs in the same module merged by
  that planner turn). Then DELETE. 47-49 "When your turn merges, the script records the diagnosis and resets the
  review counts": DELETE (the planner acts on nothing in it).
- module.md 6-9 the four files again: DELETE (2a). Rest KEEP.
- project.md 10-17 table header: duplicate of done-when 86-99; keep one. 54-61 settings lines the planner adds:
  KEEP; "`pytest || [ $? -eq 5 ]`" is general testing knowledge, but it's the concrete case of a test command that
  must pass on an empty suite - CUT to "use a test command that passes on an empty suite".
- revise.md 13-14 last round: fine (script tells it in the task).
- unblock.md 19-22 "the script lifts the block": KEEP short; the planner needs to know KEEP lifts it.
- fix.md: KEEP.

### planner/references/proofs.md (214 lines)
Mostly the planner's judgement; KEEP. Cuts:
- 56-76 how often checks run, merge batches, test command lock, hold-limit exemption, batch halving: some is the
  cost model the planner needs; the mechanics (one hour, halving, `Test command lock` behaviour) go to
  `settings --template` / `merge --help`. CUT to the conclusion: "the test command gates every merge, so keep it
  short and lock-free; checks that need a shared resource belong in item checks or main-branch checks".
- 165-173 options flow: see 2g (this is the copy to keep).

### reviewer/SKILL.md (81 lines)
- 25-28 evidence path/default: prompt gives `{review}` and `{captures}`. CUT.
- 30-33 graded examples file: see 2a (add `{graded}` to review.md). KEEP "they are the best guide to how strict
  to be" and the starting set link.
- 39-48 module files and item kinds: CUT to one line + link.
- 77-81 long commands: see 2h.
- 52-73 KEEP.

### reviewer/tasks/milestone.md, design.md
- milestone.md 43-46 where User Feedback is recorded (`RECORD.json` `human_feedback`): the review prompt's
  `feedback_note(..., "review")` (7039-7051) already quotes it with its location. CUT to "the user's recorded words
  in your prompt are the judgement; a lead's or builder's summary isn't".
- milestone.md 61-62 file paths: prompt has `{review}`/`{captures}`. CUT.
- milestone.md 67-70 "the script works out the rest ... status, review link, counts": DELETE after the first
  sentence.
- design.md 53-57 path is `{review}` in the prompt; "the script approves the planner's answer to the second
  without another review": KEEP as the reason for "put every Must Fix in this review".
- Everything else: KEEP.

### reviewer/references/graded-examples.md
KEEP whole (pure judgement).

### Prompt texts in agent_loop.py
These are the right home for per-session facts and mostly good. Notes:
- `resources_rule` and `needs_rules` make builder SKILL's locks and `needs` sections redundant (2d).
- `binding()` (7169-7195) restates the builder's fields; builder SKILL 83-85 can stay as the one long-form copy.
- `WATCH_WHY` duplicates stage 4 79-89 (2h).
- `after_pass` (9446) tells the lead to run `git worktree remove` - should become script behaviour (2e).
- `scope_text` (591-601) duplicates lead stage 4 163-170 and `plan --module` help; keep the prompt and help.
- review.md lacks the graded examples path (2a).

## 4. CLI changes the cleanup depends on (order matters)

1. Subcommand `--help` descriptions and result epilogs from the existing docstring; fix `(default: see above)`,
   the `--model` example on run/review, and document `human`'s verbs. Prerequisite for most deletions (1a, 1c,
   1d, 1e, 2c, 2d, 3).
2. `paths` command (or extend `settings`) printing every location, plus `{graded}` in the review prompt (2a).
3. `settings` prints effective values with `source: set|default`, and resolved model/effort per kind of agent per
   host; `settings --template` generated from `PROFILE_FIELDS` (1f, 2b).
4. `settings --commit --human-words ...` (or adopt accepting a changed ORCHESTRATE.md with the user's words) to
   commit and merge settings changes (1b, 2f). Fix the stage 2 prose now: adopt already merges a first
   ORCHESTRATE.md, BRIEF.md and GLOSSARY.md.
5. `run` creates and reuses each module's worktree when `--worktree` is omitted, puts the module's worktree in
   every `next` it prints from `ready`/`status`, and removes a worktree it made on FINISHED (2e).
6. New/changed `next` fields: MIGRATED -> `plan --kind fix` task; worktrees on old names -> their `migrate
   --branch` command; main-branch check failure in `watch` -> `plan --kind fix` with revert as `alternative`;
   `settings`/`report` warning when there's no `Graded examples:` line (1c, 1d).
7. Optional: carry `diagnoses` to split-off milestones in the script (diagnose.md 32-34); `plan` adds the brief
   path and builder count to the task itself (stage 2 25-27); `run --checks-only` chains into the review for a
   builder with no lead (2d); `ready` prints a `stage` field.

## 5. Size of the win (rough)

| Source | Lines now | After |
|---|---|---|
| lead/references/cleanup.md, settings.md, older-projects.md | 142 | 0 (a few clauses move to stage 4) |
| lead/references/locks.md, delivery-history.md | 110 | ~15, folded into stage 4 |
| lead/stages/4-build.md | 401 | ~250 |
| lead/SKILL.md | 126 | ~95 |
| planner/references/done-when.md | 420 | ~200 |
| planner/references/profile.md | 149 | ~40 |
| builder/SKILL.md | 275 | ~175 |
| reviewer/SKILL.md + tasks | 233 | ~200 |
| planner/SKILL.md + tasks + proofs | ~640 | ~580 |
