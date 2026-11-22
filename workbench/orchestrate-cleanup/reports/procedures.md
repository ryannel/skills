# Audit: procedures that belong to the CLI (`procedures`)

Scope: step-by-step mechanics in `skills/orchestration/**` and the prompt templates that the script should do itself,
report in its output, or teach in a command's `--help`. Read-only. Line numbers are as on disk on 2026-11-22.
`agent_loop.py` means `skills/orchestration/lead/scripts/agent_loop.py`.

## The finding everything else depends on: per-command `--help` teaches nothing today

Every subcommand is built with `sub.add_parser(name, help=...)` (agent_loop.py 15365-15600) and **no subparser has a
`description=` or `epilog=`** (grep finds only the top-level `Parser(description=USAGE)` at 15355). So
`agent_loop.py run --help`, `merge --help`, `cleanup --help` etc. print only the usage line and flag help; even the
one-line `help=` summary shown in the top-level list is missing from the command's own help.

Meanwhile the module docstring (agent_loop.py 2-480) already holds a full per-command reference: every result code
of `run` (lines ~57-160), `review`, `plan`, `merge` (232-251), `ready` (253-260), `adopt` (261-275), `status`,
`migrate` (284-325, three forms), `check`, `next`, `unblock`, `human` (369-388), `lock` (405-411), `locks`, `runs`,
`main-check` (427-445), `watch` (446-456), plus "Results and exit status" (54-63) and "Routine steps" (458-468).
`USAGE` (15307) tells the reader "Each command has its own --help for its flags. The docstring at the top of this
file explains the whole design" - an agent can't usefully read a 15,700-line file's docstring.

**Fix (one CLI change, unlocks most deletions below):** give each subparser `description=` (the `help=` sentence)
and `epilog=` taken from its docstring section (split the docstring into a dict keyed by command, or move each
section next to its parser), with `RawDescriptionHelpFormatter`. Put "Results and exit status" and the `next`
contract into `USAGE`, so top-level `--help` carries them. After that, any skill passage that restates a docstring
section can simply be deleted and replaced by "see `<cmd> --help`".

---

## Ranked findings

### 1. Module worktrees: the script should make them (lead/stages/4-build.md 37-41, plus knock-ons)

- **4-build.md 37-41** - "Give each module its own worktree on its own branch, in a folder git ignores. A worktree
  is a second working copy..." - procedure + general git knowledge (what a worktree is, `git worktree add -b
  build/<module> <folder>/<module> <remote>/<branch>`, `.git/info/exclude`, Merge: push vs local base).
- **Where:** script behaviour, in `run`. When `--worktree` is the main working copy (or a new `--worktree` path that
  doesn't exist yet), `run` finds or creates the module's worktree: reuse the worktree whose branch is
  `build/<module>` (`git worktree list --porcelain`, already parsed at 3101/12066/13408), else `git worktree add -b
  build/<module> <folder>/<module> <base_ref(prof)>` where `base_ref` (1238) already encodes push vs local, and the
  folder is excluded the way `ignore_evidence` (1172) already writes `info/exclude`. Record the path in
  `last-runs.json` and print it as `worktree` in every result.
- **CLI today:** does not. `cmd_run` (8189) assumes `--worktree` exists; it only fast-forwards a clean one
  (`sync_worktree`, 1303). The script makes worktrees only for its own checkouts (`verify_tree`, 4664; 14304). All
  the building blocks exist.
- **Knock-ons that go with the same change:**
  - **lead/SKILL.md 53-58** - "It names the worktree of the command that printed it, so a `next` from `ready` or
    `status` run in the main working copy needs the module's own worktree put in its place." The script knows the
    worktree per module once it records it; `fit_command` (2566) explicitly says "The worktree is left as the command
    names it" - change it to fill the module's worktree the way it already fills hosts. Then the caveat goes. (The
    docstring at ~151 carries the same caveat; update it too.)
  - **agent_loop.py 3202** (`next_for`, can_start) - "Run it in the module's worktree" - becomes unnecessary.
  - **4-build.md 195 (`FINISHED` row), 267-269, 400-401** and **next_for at 9444-9448**, which tells the lead to run
    `git worktree remove <path>`: the script already removes its own verify checkout there (`drop_tree`, 4673). It can
    also remove the module's worktree when it is clean and its branch is merged, and report `worktree_removed`;
    otherwise say why it kept it. Then "Remove its worktree once nothing is unmerged" and "remove build outputs and
    the worktrees whose work is merged" go from the skill.
  - **builder/prompts/build.md 6** ("This worktree is yours...") stays; it is session fact the script fills.

### 2. The lead's result tables restate the docstring and the `next`/`why` fields (lead/stages/4-build.md 120-210, 352-382)

- **4-build.md 120-138** - the `ready` group table (`can_start`, `waiting` with `on_dependency`/`for_diagnosis`/
  `for_planning`, `in_progress_elsewhere`, ...). Prose explaining JSON output. **Where:** `ready --help` (from the
  docstring 253-260, which covers some of it; add the group list there). Delete from the skill.
- **4-build.md 140-149** - `plan_ahead`, `unmerged_plans`, `adopt` refusing revised items after approval. Output
  field explanation; each case already carries its own `next` (docstring 253-275; `adopt` refusal names `plan` and
  `human scope`). **Where:** `ready --help` / `adopt --help`; keep one judgement line ("use `adopt`, not your own
  commit"). The "plan it when the user says it's time" sentence for unreadable Needs is judgement - keep.
- **4-build.md 160-178** - reviewer/planner checkout mechanics, `--module` scoping and planner queueing,
  "merges only on PLANNED... `stash` and `branch` hold what the planner changed", `Review host: other` defaults.
  Mostly already in `plan --help` (`--module`, `--one-step`, `--kind`) and `run --help` (`--review-host`). **Where:**
  `plan --help` epilog for the queueing and the PLANNED-only merge; delete from skill. Keep "run each review on the
  host that didn't build" as judgement (one sentence), since the settings line makes it the default anyway.
- **4-build.md 180-210** - "What each result means" table and the paragraphs under it (`NEEDS_REVIEW`,
  `PLAN_NOT_MERGED`, `UNFINISHED`, `REFUSED`, `stopped_turn`, `warnings`, `main_broken`, `merge_kept_later`). The
  docstring's `run` section (57-160) documents every one of these results, and each carries `next` with `why`
  (`merge_kept_later` with its own why at 10044-10048). **Where:** `run --help`/`plan --help` epilogs; delete. Keep the
  three rows that are the lead's judgement about the user: HOST_FAILED for a usage limit (tell the user; their call),
  WRONG_MODEL_OR_EFFORT (tell the user), PAUSED (leave the user's builder alone). Better still, emit those as
  `next.decides: human` with an `ask`, as `cleanup` and the Builders refusal already do, and the rows go too.
- **4-build.md 224-249** - "After a review": `found`, `filled`, the escalation ladder (`same_builder` ->
  `new_builder_session` -> `diagnosis` -> `too_many_failed_reviews`), design review DESIGN OK/CHANGES and the
  two-round auto-approval. All script mechanics; the docstring's `next` (362-364) and "Routine steps" (458-468)
  cover them, and done-when.md 389-420 is the canonical copy. **Where:** `next --help` and `review --help`; delete
  from 4-build. Keep 239-240 ("add nothing about which findings to fix") - genuine lead judgement.
- **4-build.md 352-364** - the `human` verb table. The parser lists the verbs with no meanings; the docstring
  369-388 explains each. **Where:** `human --help` epilog; delete the table. Keep the `scope` judgement ("only for an
  edit the user dictated exactly... run it on their yes").
- **4-build.md 366-371** - `"alone": true` mechanics (waits for turns, holds back reviews/planners/main-checks).
  Output/`--help` of `run`; keep "start it when the other modules can spare the time; gather sittings" (judgement).
- **4-build.md 373-377** - after a pick, `plan_ahead` lists planner tasks. Output already does it; delete, keep
  "when the user turns every option down, give their words to a planner as `--kind change`".
- **4-build.md 379-382** - graded examples appended on `accept`/`rereview` (`graded_example`), and `human` refusing
  while a run holds the module. The refusal message teaches the second; the first is output. Delete.

### 3. `lead/references/older-projects.md` (86 lines) - almost all of it is `migrate --help` and `migrate`'s `next`

- **7-14** - what `migrate` does and the follow-up "start a planner with `plan --kind fix`". **CLI:** docstring
  284-325 covers the moves; but `MIGRATED`'s `next` is only `status` (agent_loop.py ~13878). **Where:** make
  `MIGRATED`'s `next` the `plan --kind fix` task (with the list of shape fixes in its `--task`) - new output.
- **16-30** - committed-evidence migration mechanics. Duplicates `evidence_refusal` (1201) and docstring; the 2.6.0
  `changed` entry (~6500-6510) says the same. `definitions_naming_it` should carry its own `next` (a `plan --kind fix`
  task naming those items) - today it is a bare field (13401). Delete prose.
- **32-41** - links not opening in a clean clone, history rewrite, `--commit-map`. Mechanics + one fact to tell the
  user. **Where:** put "tell the user ..." into the `MIGRATED` result's `evidence.note` (it already has a note,
  ~13867-13871, missing the docs-link-checker point) as an `ask`/`tell_user` field; `--commit-map` is in
  `migrate --help` already. Delete.
- **43-48** - worktrees with old commits -> `migrate --branch`. Already output: `worktrees_on_old_names`, each with
  its `migrate --branch` command (docstring 323-325). Delete.
- **50-66** - names changed in 2.2, old command aliases. History; parser keeps the aliases; `changed` reports it.
  Delete.
- **68-72, 74-78** - Ready for Review set by a builder; daily reports before 2.4. Script handles both (INVALID with
  `next`). Delete.
- **80-86** - no `Graded examples:` line. Should be a `ready`/`settings` warning with the line to add. New output;
  then delete.
- **lead/SKILL.md 125-126** (pointer to this file) shrinks to "a command naming `migrate`: run what its `next` says".
  Net: the whole file can go once `MIGRATED` and `definitions_naming_it` carry `next`.

### 4. builder/SKILL.md: merge, locks, long commands, main-checks and Codex mechanics (~90 of 275 lines)

- **159-179 Merging** - what `merge` does, batching, `batch`, the three FAILED cases. **CLI:** docstring 232-251
  covers all of it; the FAILED `detail` texts already say the exact fix: conflicts (11315-11319: "Fetch, rebase...
  resolve the conflicts, commit, and run merge again"), stale items (10766-10770: "Rebase... taking its copy of the
  plan files, read the items again"), main_broken (11271: "`BLOCKED main_broken: ...`; the lead gives the fix to
  whoever owns it"). **Where:** `merge --help`; delete the section, leaving one line: "merge with `merge --worktree
  .`; when it fails, do what its `detail` says."
- **58-60** - "`merge` refuses a commit that sets either" - the refusal (`state_refusal`) teaches it. Keep only
  "leave status `in_progress`".
- **70-74** - what the script does after `DONE`. Duplicates the build prompt's goal line (builder/prompts/build.md
  3: "When you end with DONE, the script runs the checks on the merged work and sets the status itself"). Delete.
- **128-131** - `check` "is remembered" detail -> `check --help`. Keep "run `check` before you finish".
- **142-146** - `upstream_files` explanation. Output field; make `merge`'s result say it ("files the rebase brought
  in; retake any capture they could change") in `detail` or a `why`. Keep the judgement "one capture pass after your
  last merge; prove user-attended items after the last merge".
- **152-157** - `main-check` answers `NOT_ON_MAIN`/`COVERED`/`PENDING`/`FAILING_ON_MAIN`. **CLI:** docstring 427-445
  covers all, with exit codes. **Where:** `main-check --help`; keep "if the breaking commit is yours, fix it; if
  another module's, leave it" (the run already waits without a turn).
- **181-198 Shared resources** - **CLI:** the build prompt already injects the project's resource rules per project
  (`resources_rule`, 7058-7073, incl. `.alone` and "doesn't make the machine quiet"); `lock` refuses wrapping
  `check`/`merge` with a full explanation (10409-10414); the hold limit and exit 124 are in docstring 405-411. Delete
  all but the judgement: check the user is present before taking a lock for an attended run; end BLOCKED only when
  the holder seems stuck.
- **200-209 Long commands** - `background`/`wait`/`jobs` usage. `--help` covers the flags (and `wait`'s 540s default,
  which the skill restates as "nine minutes" - a duplicated default). Keep the one sentence of reasoning (one long
  wait costs less than many short looks); delete the rest. Same in **reviewer/SKILL.md 78-81**.
- **220-231 On Codex** - sandbox escalation, `yield_time_ms` 300000, `ps` refused, `apply_patch`. Host mechanics the
  script knows at prompt time. **Where:** command output in the sense of the prompt: add Codex-only lines in
  `session_rule(headless, host)` (7081) or a `{host_notes}` field in build.md, filled only when `host == "codex"`.
  **CLI today:** not in any template (grep finds no `yield_time_ms`/`apply_patch`). Then delete the section (it is
  noise for a Claude builder).
- **258-273 Without a lead** - three-step procedure (`run --checks-only`, then `review ... --commit <sha>`, then
  `next`). **CLI:** `MERGED` has no `next` (10781-10800). `--checks-only`'s READY_FOR_REVIEW already names the review
  command as `next` (docstring ~78). **Where:** new output: when `merge` runs outside a script-started session
  (`ORCHESTRATE_ROLE` unset) and no `run` holds the module, `MERGED` carries `next` = `run --module <M> --checks-only`;
  then each step's `next` chains. Skill shrinks to "with no lead, after `merge`, follow `next` until the milestone is
  reviewed; start the review with no message of your own".

### 5. `lead/references/cleanup.md` (40 lines) -> `cleanup --help` and output

- **5-18** - what is kept where (working folder, verify/main-checks checkouts, logs, ledgers). **CLI:** `cleanup
  --kind` help (agent_loop.py 15562-15571 via `CLEANUP_KINDS` 13889) and the comment block above it say the same.
  **Where:** `cleanup --help` epilog. Delete.
- **26-36** - kind table, defaults, `--older-than`, `--json`, never-touched list. Already in `--kind`/`--older-than`
  help except the never-touched list (in the code comment at 13883-13887). **Where:** `cleanup --help`. Delete.
- **22-24** - "Its `next` carries the question to put to them." **Bug to note:** only `--json` prints `next`; the
  default text path prints the result line with `next` stripped (14116: `if k not in ("next",)`), so a lead following
  this skill sees no `next`. Fix the script (keep `next` on the last line), then the sentence can go.
- **38-40** - "Offer `--older-than` when the user wants to keep recent captures" - judgement; keep as one line in
  4-build.md, or put in the `next.why`.
- **New behaviour that removes other passages:** a `cleanup --kind worktrees` (or `build-outputs`) listing module
  worktrees whose branch is merged and nothing runs in them, with sizes, removed on `--yes`. That replaces
  4-build.md 267-268 ("Every worktree keeps its own build outputs... Clear those in worktrees nothing is using") and
  the stop step at 400-401. Net: the file goes; one line in 4-build says "show the user `cleanup`'s list and run its
  `next` on their yes".

### 6. `lead/references/locks.md` (59 lines) -> `lock`/`main-check`/`watch` help and `next`

- **8-19** - lock semantics, `.alone`, hold limit 30 min, test command's hour. Duplicates docstring 405-411 and
  `resources_rule`. -> `lock --help`. Delete.
- **21-26** - reading `locks` and `flow` for a lock that limits delivery. Judgement (fewer builders, cheaper proof,
  move to a main-branch check) - keep, and it could fold into 4-build "Reading delivery".
- **30-40** - main-branch check mechanics, `watch` starting due checks, `MAIN_CHECKS`/`STARTED`/`ALREADY_RUNNING`,
  `runner.log`/`RAN`. Docstring 427-456. -> `main-check --help`. Delete.
- **42-47** - on a held failure: `plan --kind fix` naming the commit, or revert. **Where:** the `watch` warning sign
  for a failing main-branch check should carry `next` = the `plan --kind fix` task naming commit and modules (as
  `main_broken_next` does for the test command), with revert as `alternative`. Verify: the sign text exists in
  `watch`, but I found no `next` for it. Keep the judgement "revert if the fix would take long".
- **49-53** - revert procedure: `git revert` on main, tell the module's builder by `run --message`, `human rereview`
  if the reverted work was Done, then `main-check <name> --start`. Four mechanical steps the lead must not get wrong,
  and the lead "doesn't write code". **Where:** new script behaviour: a `revert --commit <sha> --worktree <repo>`
  command that reverts through the merge queue, starts the due main-checks, and returns `next` items for the
  affected module (rereview of a Done milestone with `decides: human` if needed, and the `--message` for a running
  builder). **CLI today:** no such command.
- **55-59** - exit 75 / `unjudged` / tried three times. Docstring 427-445 and planner/references/proofs.md 93-96 (the
  planner does need to know to exit 75 - keep it there). -> `main-check --help`. Keep "if runs keep coming back
  unjudged, the check needs work for its owning module" (judgement).
- **4-build.md 91-93** (when to read locks.md) shrinks with it.

### 7. lead/SKILL.md "The script" section (36-68): exit statuses and the `next` contract

- **36-43** - exit 0/1/2, which commands keep their own statuses, `result_file`, `RUNNING` with a gone process.
  Docstring 54-63 holds this. **Where:** top-level `--help` (`USAGE`). Keep the one instruction an agent needs and
  wouldn't guess: "don't send output to /dev/null or cut it with `tail`; read the last line".
- **45-51** - `next`, `why`, `by`, `decides: human`, `ask`, placeholders. Output contract -> `USAGE`; the skill keeps
  "run `next` unless you see a reason not to; when `decides: human`, put its `ask` to the user and substitute their
  words".
- **53-58** - worktree and host caveats on `next`. The worktree half goes with finding 1; the host half ("name the
  host yourself when the user works with two") could be removed by having `fit_command` refuse to guess when the
  settings name two hosts and no run is known (emit `decides: lead` with both commands).
- **60-62** - adding words with repeated `--task`/`--message` and zsh quoting. `--help` already says "give it more
  than once"; the quoting point is general shell knowledge. Delete or keep one clause.
- **64-68** - re-read the skill when `warnings` says a newer copy exists; `changed`. Keep (it's the agent's
  behaviour across versions), but the paths point is something `next` already handles ("A `next` names the newest
  installed copy", docstring 62).
- **122-123** - after a host restart, read `runs`, the result files and `ready`. **Where:** new output - `ready` (or
  `watch`) lists `ended_since` (result files written since the last `watch`, from `<git common dir>/orchestrate/
  results/`) and `running` (from the loops dir), so one command answers "what happened while I was gone". Then the
  skill says "after a restart, run `ready` before starting anything".

### 8. Settings and the brief: committing procedures the script half-does (lead/references/settings.md, stage 2, stage 3)

(The settings/paths auditor will cover the file itself; these are the procedure parts.)

- **stages/2-start-planning.md 20-23** - "commit the brief, the glossary and the settings with git on the main
  branch, and push them under `Merge: push`, because `adopt` never merges the settings". **Stale:** docstring 263-264
  and `cmd_adopt` (12758, "first ORCHESTRATE.md") say `adopt` *does* merge a first ORCHESTRATE.md (one the tip
  doesn't have). Only an empty repository needs a hand commit, and `adopt` then fails with a `next` saying how
  (docstring 275, `no_base` 1260). So the passage reduces to "`adopt --worktree <repo>` the brief, glossary and
  settings". Verify on a scratch repo before deleting.
- **references/settings.md 7-8**, **stages/3-before-first-build.md 22-23**, **4-build.md 30-33, 65-66** - "commit
  ORCHESTRATE.md with git in the main working copy, on the main branch, and push it when the settings say `Merge:
  push`". A git procedure repeated four times. **Where:** new script behaviour - `settings --set '<Label>: <value>'
  --said '<the user's words>'` (mirroring `run --more-builders HUMAN_WORDS` and `human --said`) that edits the line,
  validates it with the same parser, commits as the script on the main branch, pushes under push, and records the
  user's words in the decisions the report lists (report.md 31-32 says settings changes currently escape that list).
  **CLI today:** `adopt` refuses a changed ORCHESTRATE.md the tip already has; no setter exists.
- **settings.md 10-16** - `settings_read_from`, `settings_differ`, `ran_on`, `observed`. Output-field prose. ->
  `settings --help`/`run --help`. Keep "check `ran_on` before telling the user a change took effect" as one line.

### 9. Delivery history and report references: output/`--help` prose

- **references/delivery-history.md 14-28** - what the history keeps, where, `$ORCHESTRATE_HISTORY_DIR`, the
  `reviews/<MODULE>/` copy, sessions read at `report`/`history`/`dashboard`. -> `history --help` epilog (the paths
  are the paths auditor's). **32-39** duplicates `history --help`/`dashboard --help` flag text. **41-51** explains
  the three cost measures in the output -> `history --help`/`cost --help` (and the dashboard already labels them).
  Keep **5-12** (when to read it, read a version's figures beside its turn count, offer the dashboard for a retro) -
  judgement. Net: the file shrinks to ~10 lines and could merge into 4-build "Reading delivery".
- **references/report.md 10-18** - default window, `--since`, `--write` location, the list of parts. `report --help`
  covers the flags and defaults (agent_loop.py report help); the parts are the output itself. Delete. Keep 20-46
  (what the lead adds) - judgement.

### 10. Visible sessions, access and stopping (lead/stages/4-build.md 251-288)

- **253-257** - sandbox inheritance and `blocked_write`. `blocked_write` carries the path and the fix (docstring
  476-479, `WriteBlocked.fields` 1041). Keep "lead from where network and `.git` writes are allowed" (judgement);
  delete the field explanation.
- **264-265** - `ORCHESTRATE_VISIBLE=1`, `path`. Run docstring 17-25. -> `run --help`. Keep one line for the lead.
- **271-275** - `needs_access`/`needs_hardware`: run its `next` (same command with ORCHESTRATE_VISIBLE=1). The
  `next` already is that command (docstring ~80-87). Delete the mechanics; keep "put its `ask` to the user; gather
  sittings" or emit it as `decides: human` with an `ask`.
- **279-288** - `pause` vs killing by name; Codex app `turn_not_stopped` -> ask the user to press Stop and wait.
  **Where:** `pause --help` for the first; for the second, results with `turn_not_stopped` should carry `next` with
  `decides: human` and the `ask` ("open thread X and press Stop"). Verify; I found the field documented (docstring
  22-25) but not a `next` for it.

### 11. planner/references/done-when.md: script state machine written for agents (291-420)

- **353-387 "Who changes what"** - 16 rows, of which 12 are "Script" transitions. Planner, builder and reviewer each
  need only their own fields; the script's transitions are its behaviour. **Where:** the Script rows -> `status
  --help` epilog (or the docstring's "What the script owns", 41-50); keep the Builder/Reviewer/Planner/User rows.
  The builder (83-86) and reviewer (67-70) already state their fields and link here; the link can then point at a
  short table.
- **389-420 "When a review fails"** - thresholds (3, 4, 6), `escalation` values, reset rules. Self-described as
  "written down only here. The `next` command... apply them" - so the code is the real source and this is a second
  copy. **Where:** `next --help`; keep in the skill only what a planner needs for a diagnosis (that a milestone gets
  one diagnosis; Re-plan vs Plan Kept). Also duplicated at 4-build.md 228-237 (finding 2).
- **291-330 statuses and reasons** - the "Printed as" column is output explanation -> `ready --help`/`status --help`.
  The status names and Blocked reasons are shared vocabulary for builders (who write the BLOCKED reasons) - keep.

### 12. Smaller ones (one-liners)

- **builder/SKILL.md 62-63** - LOG entry of up to eight lines; "the script refuses a longer entry". `plan`/`adopt`
  refuse and `merge` warns with the reason (done-when.md 154-161). Keep the limit as contract, drop the mechanism.
- **builder/SKILL.md 76-81** - handoff path. The prompt's `{handoff}` already gives it (build.md 13). Keep the
  content guidance (what to write), drop the path.
- **builder/SKILL.md 16-18** - how to run the script. Prompt line build.md 8 gives `python3 {loop}`. Keep a clause
  for a builder started by the user without a prompt.
- **lead/stages/4-build.md 26-28** - model/effort defaults "medium (high for planners)". Duplicates `run --effort`
  help. Keep "don't pass `--model`/`--effort` out of habit" (judgement); drop the default.
- **4-build.md 61-69** - `watch` cadence (3 h, `Lead check-in:`), `CHECK_IN`/`WARNING_SIGNS`/`RUN_ENDED`, start it
  again. `watch`'s result already carries `next` = `watch` again (15303) and the docstring 446-456 covers the rest.
  -> `watch --help`. Keep "keep `watch` running in the background for the whole build; use `--runs` if your host
  doesn't wake you".
- **4-build.md 80-82, 203-205** - `runs --json`, `quota`, `unblock` descriptions. `--help` one-liners cover them.
- **4-build.md 305-311** - `--kind change` cases, `--human-rule`/`--clear-human-rules`. `plan --kind` and `run
  --human-rule` help say this. Keep the judgement of which words go where (rule vs message vs task) in one line each.
- **planner/SKILL.md 170-173** - "Try each with the script's `check` command... `fail`... `error` means the check is
  broken, often by shell quoting" - the plan prompt already gives the command (plan.md 10). Keep the meaning of
  `error` vs `fail` or move it to `check --help` (its help lists pass/fail but the `error` gloss is only in the
  docstring ~330).
- **reviewer/tasks/milestone.md 67-70** - "Leave the done-when file, the review and its folder uncommitted. The
  script works out the rest" - contract; keep.
- **reviewer/SKILL.md 78-81, builder 200-209** - background/wait (see finding 4).
- **README.md 418-512** - for people, not agents; the command table and "What the script verifies" are fine as
  human documentation, but they will drift with the CLI. Once per-command help exists, the README can point at it
  instead of restating `run`/`review`/`plan` checks (463-495).

## Prompt templates (agent_loop.py `*_TEMPLATE`, i.e. the `prompts/` files)

They are lean and mostly session facts the script fills, which is the right home. Two notes:
- **builder/prompts/build.md 3** already carries "When you end with DONE, the script runs the checks... and sets the
  status itself", which is why builder/SKILL.md 70-74 can go.
- Host-specific instructions (finding 4, On Codex) and the "merge, then follow `next`" chain for a lead-less builder
  belong here or in `session_rule`, filled by host and situation, rather than in the skill every builder reads.
- **planner/prompts/plan.md 10** explains `check --items-only` inline; fine as is, or shorten to "see `check --help`"
  once that help exists.

## CLI changes the cleanup depends on (in suggested order)

1. **Per-command `--help` from the docstring** (description + epilog per subparser; exit statuses and the `next`
   contract in `USAGE`). Pure text move; unblocks deleting findings 2, 3 (partly), 4, 5, 6, 7, 9, 11, 12.
2. **`cleanup` prints `next` on its default last line** (bug at agent_loop.py 14116).
3. **New `next` fields:** `MIGRATED` -> `plan --kind fix`; `definitions_naming_it` -> its planner task; `MERGED`
   outside a run -> `run --checks-only`; main-branch-check warning sign -> `plan --kind fix` (revert as
   `alternative`); `turn_not_stopped`, HOST_FAILED usage limit, WRONG_MODEL_OR_EFFORT -> `decides: human` with `ask`;
   a `ready`/`settings` warning for a missing `Graded examples:` line.
4. **`run` creates and reuses module worktrees** (`build/<module>` under an excluded folder, from `base_ref`),
   records the path in `last-runs.json`, fills it into every `next`, and removes a clean merged worktree on
   FINISHED. Plus **`cleanup --kind worktrees`** for build outputs.
5. **`ready` (or `watch`) reports `ended_since` and `running`**, so a restarted lead runs one command.
6. **`settings --set ... --said ...`**: edit, validate, commit and push a settings line as the script, recorded as a
   user decision. Also confirm and document that `adopt` merges a first ORCHESTRATE.md (stage 2 says it doesn't).
7. **`revert --commit`** for a commit breaking a main-branch check, doing the revert, the main-check restart and the
   follow-ups as `next` items.
8. **Codex host notes in the build prompt** (`session_rule` or a `{host_notes}` field).

Rough size of what can go once 1-4 land: lead/references/cleanup.md, older-projects.md and locks.md almost whole
(~185 lines), ~150 lines of 4-build.md, ~90 lines of builder/SKILL.md, ~45 lines of done-when.md, and most of
delivery-history.md and report.md's "facts" sections.
