# Duplication and drift in the orchestrate set

Auditor: `duplication-drift`. Read-only. Files read as on disk on 2026-11-22: every file under
`skills/orchestration/` (four skills with their stages, tasks, references and prompts, `README.md`, `GLOSSARY.md`),
and `lead/scripts/agent_loop.py` (its docstring, constants, prompt templates, prompt-building functions, argparse
setup, and the commands named below). Every `--help` was run. Line numbers are from today's files.

Paths below are relative to `skills/orchestration/`. `al.py` is `lead/scripts/agent_loop.py`.

## Read this first: the CLI change everything else depends on

**Finding 0. Subcommand `--help` shows no description, so the mechanics the skills repeat have nowhere to go yet.**
Every `sub.add_parser(...)` (al.py L15365-15598) sets only `help=`, the one-liner in the top-level list. No
subparser sets `description=` or `epilog=` (grep: the only `description=` is the top-level parser, L15355). So
`agent_loop.py cleanup --help` shows flags only, `merge --help` shows `--no-check` and nothing else, and `human
--help` lists six verbs with no meaning. Meanwhile the module docstring (al.py L49-340, about 290 lines,
"Results and exit status", "Subcommands", "Routine steps") already holds most of what each command does, which
results it prints, and what its fields mean. An agent sees it only by reading the file; the top-level help says
"The docstring at the top of this file explains the whole design."

Fix: move each command's docstring paragraph into that subparser's `description=` (with
`RawDescriptionHelpFormatter`). Add paragraphs for the commands the docstring has none for: `cleanup`,
`background`, `jobs`, `wait`, `history`, `dashboard`, `flow`. This is the precondition for most deletions below,
because "the CLI already says it" is today true of the file, not of `--help`.

Related help defects found while checking:
- `run`, `review` and `plan` `--host` and `settings --host` say "(default: see above)" (the `--help` output of each;
  saved in helps.txt beside this report), pointing at text `--help` never prints (it is the docstring, al.py L14-16).
- `run --no-progress-hours` help: "stop the run when no item has passed for this long". It shows no default (4.0,
  al.py L15380) and leaves out the second condition the docstring states (L120-121: "no new passing item, and no
  commit of the builder's own outside the plans folder").
- `--turn-timeout-hours` (default 2.0, al.py L15363) has no help text, and no skill names the limit by number.

## Ranked findings

Each finding lists every place a fact appears, names one home, and says whether the CLI already covers it.
"Docstring only" means the script has the text but `--help` doesn't show it (see Finding 0).

### 1. Command output contract: the lead skill describes a uniform contract that half the commands don't follow (drift, mechanics)

`lead/SKILL.md` L36-43: "Every command ends by printing one line of JSON, its result, as the last line of its
output. Its exit status is 0 when that line is the command's own result ... `merge`, `check`, `lock`, `wait` and
`main-check` keep their own statuses." L41-42: "The same line is also saved in the file its `result_file` field
names". L64-68: "Each result carries the script's `version`, and its `warnings` say when a newer copy is
installed ... The first result after the version changes carries `changed`".

Also in: al.py docstring L49-58 (same contract), GLOSSARY.md L511-513 ("Every command of the script ends by printing
one JSON line, its result").

What the code does: only the commands that go through `emit()` (al.py L6887-6925) get `version`, `warnings`,
`changed`, `result_file` and the 0/1 exit rule, and those are `run`, `review`, `plan`, `pause`, `unblock` and
`watch`. The rest:

- `ready` ends `print(json.dumps(out, indent=2))` (L10248): multi-line JSON with no `result`, no `version`.
- `settings` ends `print(json.dumps(prof, indent=2))` (L10382): multi-line, no `result`.
- `next` prints a bare JSON object with no `result` (L10361).
- `adopt` and `migrate` use a local `done_with(result, code)` that prints `{"result": ..., **fields}` and exits
  with `code` (L12765-12767, L13785-13787): REFUSED and FAILED exit 1, and there's no `version`, `warnings` or
  `result_file`.
- `human`: `sys.exit(0 if ok else 1)` (cmd_human), no `version`.
- `status`, `report`, `check`, `cost`, `flow`, `quota`, `history` print text or markdown unless given `--json` or
  `--format`.
- `cleanup` prints text, then a JSON line (see Finding 7).

Where it should go: script behaviour. Route every command's final line through `emit()` (or one shared printer), so
the contract is true, then cut the lead skill to three sentences: read the last line; don't discard output or exit
status; follow `next`. Until then, the exceptions belong in each command's `--help`, not in the skill.

### 2. Worktree setup and teardown is a procedure the script should own (brief's own example; no CLI support)

- `lead/stages/4-build.md` L37-41: "Give each module its own worktree on its own branch, in a folder git ignores.
  A worktree is a second working copy ... `git worktree add -b build/<module> <folder>/<module> <remote>/<branch>`".
- `lead/stages/4-build.md` L195: "`FINISHED` | Remove its worktree once nothing is unmerged."
- `lead/stages/4-build.md` L400-401: "remove build outputs and the worktrees whose work is merged".
- `lead/stages/4-build.md` L267-269: "Every worktree keeps its own build outputs ... Clear those in worktrees nothing
  is using."
- `README.md` L100-102: "it makes one worktree for each module: a second working copy of the repository".
- al.py L9446-9449, the `next` the script prints for a finished module: "Remove the worktree you built it in (`git
  worktree remove <path>`) once nothing in it is unmerged".

CLI today: `run` requires `--worktree` and makes no worktree. The script already has the parts: it makes and drops
its own checkouts (`verify_tree`, `drop_tree` L4673-4683, `git worktree add --detach` L4666), adds folders to
`info/exclude` (`ignore_evidence` L1170-1184), and knows `Merge:`, `Remote:` and `Branch:`.

Where it should go: script behaviour. `run --module M` with no `--worktree` creates or reuses
`<ignored folder>/<module>` on `build/<module>`, branched per the `Merge:` line, and prints its path. A finished
module's worktree is removed by the script once merged, or listed by `cleanup` as a new kind. The skill keeps one
sentence: each module has its own worktree, which `run` makes. The general explanation of worktrees goes.

### 3. Result names and what to do about each: four copies

- `GLOSSARY.md` L509-564: the Results table, 45 result names with "Printed by" and "Means".
- `lead/stages/4-build.md` L180-210: "What each result means" table plus two paragraphs.
- al.py docstring L62-206: each command's results with meanings (the fullest copy).
- `README.md` L114-164 walkthrough and L463-512 "What the script verifies" (narrative).
- In the script's output: every non-routine result already carries `next` with `why` (docstring L148-160), and
  `stopped_because` (L14983).

Drift inside this cluster (mechanics):
- `4-build.md` L200-201: "Any command prints `REFUSED`, with `problems`, when it won't act, and changes nothing."
  Only `run` (`emit("REFUSED", ...)` L8313, L8355), `adopt` (L12804, L12875) and `migrate` (L13567-13663) print it.
  The others raise `SystemExit`, which `main` turns into `ERROR`. GLOSSARY L552 has it right ("`adopt`,
  `migrate`, `run`").
- `GLOSSARY.md` L533: PAUSED "Printed by `run`, `plan`, `pause`". `review` prints it too (docstring L183-184,
  "the host's HOST_FAILED, SCRIPT_FAILED, WRONG_MODEL_OR_EFFORT or PAUSED"). L534: INVALID omits `watch`, which emits
  INVALID on an unplanned project (cmd_watch, `emit("INVALID", problems=[not_yet["reason"]], ...)`).
- `GLOSSARY.md` L525: CHECKS_FAILED "The builder said it had finished, and the script's checks disagreed". The
  docstring (L94) says after three DONEs that didn't hold up; one failure sends the builder the failure and goes on.

Where it should go: each command's `--help` lists the results it prints (docstring text, moved per Finding 0), and
`next.why` carries what to do. The lead keeps only the judgement column, which is short: HOST_FAILED for a usage
limit is the user's call (wait or move hosts); WRONG_MODEL_OR_EFFORT is told to the user; PAUSED by the user is
left to them; INVALID from a review is run again on the other host. GLOSSARY keeps the names only, as its own
header says (L8: "How each thing works is in the skills and the script's help").

### 4. Escalation after a failed review: five copies, one claiming to be the only one (drift)

- `planner/references/done-when.md` L389-420 "When a review fails", which opens (L391): "These are the escalation
  steps, and they are written down only here."
- `lead/stages/4-build.md` L224-240 "After a review".
- `README.md` L120-136 (a table) and L372-376.
- `planner/tasks/diagnose.md` L47-49; `planner/tasks/change.md` L11-14.
- al.py docstring L196-206; the code `escalation()` L2133-2150 with `NEW_SESSION_AFTER_FAILED_REVIEWS = 3`,
  `REPEATS_TO_DIAGNOSE = 4`, `FAILED_REVIEWS_TO_DIAGNOSE = 6` (L2125-2127).
- In output: `escalation`, `next.escalation`, `next.command` with the message already written (docstring
  L200-206), and `next --module ...` reprints it.

Drift:
- done-when.md L391 "written down only here" is false: see the list above.
- README L128-136: the table is broken markdown (its rows are wrapped into one paragraph, starting "| Failed
  reviews | What runs | What happens | |---|---|---| | 1 or 2 | ..."). It says "| 3 | `run`, with a new builder |"
  and is silent on 4 and 5. The code (L2147) gives `new_builder_session` only when `failed_reviews == 3` exactly
  (or `with_repeat == 3`); 4 and 5 without repeats go back to `same_builder`. done-when L398-402 matches the code.

Where it should go: the counts are mechanics, and the script applies them and writes the next command. Home:
`review --help` and `next --help` for the thresholds, done-when.md for the planner's view of the counts (the one copy
that explains them). The lead keeps one sentence of judgement: follow `next`, because the counts record what has
been tried. README keeps a corrected, rendering table for people.

### 5. Paths: the working folder, evidence, handoffs, reviews and the module files are described in ten places

- `lead/references/cleanup.md` L7-18 (the working folder at `<git common dir>/orchestrate/evidence/`, checkouts
  under `verify/` and `main-checks/<name>/checkout/`, logs, ledgers).
- `planner/SKILL.md` L19-34 (file tree with `.orchestrate/evidence/<MODULE>/`).
- `planner/references/done-when.md` L20-50 (file tree and the working-folder paragraph), L134, L161.
- `builder/SKILL.md` L51-57 (`<evidence>/<MODULE>/<milestone>/`), L62, L76 (`<evidence>/<MODULE>/<milestone>-handoff.md`),
  L139-140.
- `reviewer/SKILL.md` L25-32; `reviewer/tasks/milestone.md` L61-62; `reviewer/tasks/design.md` L53.
- `lead/SKILL.md` L76-79; `README.md` L179-193, L481-484; `planner/references/profile.md` L28-30.
- `lead/references/delivery-history.md` L19-22 (`~/.orchestrate/history/<repository>-<hash>/`,
  `$ORCHESTRATE_HISTORY_DIR`); `README.md` L174, L618-619 (`~/.local/state/orchestrate/loops`,
  `ORCHESTRATE_LOOPS_DIR`).
- al.py docstring L28-37, L331-335.
- The prompts already carry the exact paths for the session: `builder/prompts/build.md` `{captures}`, `{handoff}`,
  `{done}`; `reviewer/prompts/*.md` `{review}`, `{captures}`; findings.md `{evidence}`.

Checked against code: all consistent today (`EVIDENCE_DEFAULT = ".orchestrate/evidence"` L1105;
`evidence_root()` = `<git common dir>/orchestrate/evidence` L1111-1113; `HISTORY_ROOT` delivery_history.py L50;
`LOOPS_DIR` L4150-4151). The risk is the next change.

CLI today: `settings` prints `plans` and `evidence` relative, nothing absolute, and no history, runs, results,
checks, jobs or reports folder. There is no command that prints them all.

Where it should go: a new `paths --worktree . [--module M --milestone ID]` command (or a `paths` block in
`settings`), printing absolute paths: working folder and its in-worktree link, plans folder and each module file,
the milestone's evidence, handoff, review and capture paths, the delivery history, runs, results, check logs, job
logs and reports folders. Skills then say "run `paths`" once. The prompts keep their filled-in paths, because a
started agent should not have to look them up. The builder skill still needs the rule "evidence is never committed"
and its reason, which is judgement.

### 6. Settings: defaults, precedence and how to change them (whole file `settings.md`, plus four other copies)

- `lead/references/settings.md` L1-16, the whole file: write the line, commit it with git because `adopt` won't
  merge a changed ORCHESTRATE.md, `settings_read_from`, `settings_differ`, `ran_on`, `observed`,
  `WRONG_MODEL_OR_EFFORT`.
- `planner/references/profile.md` L7-13 (shape of a line, required lines), L22-73 (template with each line's
  default in its note), L75-110, L112-149 (model and effort precedence).
- `lead/stages/4-build.md` L26-33 ("medium effort (high for planners)", the per-kind line forms).
- `lead/stages/2-start-planning.md` L36-38; `lead/stages/3-before-first-build.md` L22-23.
- `README.md` L26-31 (default model and effort per agent), L386-394.
- Code: `PROFILE_FIELDS` and `REQUIRED` (al.py L651-657), `ALLOWED` (L660-661), `DEFAULT_EFFORT` (L523),
  `DEFAULT_MODELS` (L517), `role_lines()`; `--model` and `--effort` help ("default: medium (high for planners), or the
  settings' Effort").

Checked against code: defaults match (Claude permissions `auto`, Codex sandbox `workspace-write`, Lead check-in 3h
`LEAD_CHECK_IN_S` L14986, Lock hold limit 30 min `DEFAULT_HOLD_LIMIT_S` L3692, Effort medium, planners high).
profile.md L11-13 matches `profile()` L790-793 (strict commands refuse; others warn and fall back).

Where it should go: profile.md keeps the template, because the lead and planner write the file, but each line's
default and the precedence lists move to `settings --help`. `settings` output should show, per kind of agent and
host, the resolved model and effort and which line set it. CLI today prints the resolved `roles` map, not the
source. settings.md can go once committing a settings change is a command (for example `settings set '<line>'
--said '<user's words>'`, which commits and merges ORCHESTRATE.md on the main branch, pushing under `Merge: push`).
The fields it explains (`settings_read_from`, `settings_differ`, `ran_on`) should carry their own one-line meaning in
the output. The lead keeps: write a settings line only when the user asks, and don't pass `--model` or `--effort` out
of habit, because a flag hides a later change to the settings (4-build L27-28).

### 7. `cleanup.md`: a whole file the CLI mostly covers, with one drifted claim (drift, mechanics)

- `lead/references/cleanup.md` L1-40 (whole file).
- Also: `4-build.md` L267-269; `README.md` L484; `done-when.md` L50; `delivery-history.md` L22-23.

CLI today: `cleanup --help` already holds the kinds table (L26-32 of the file, nearly word for word), the default
kinds, `--older-than`, `--yes`, `--json`.

Drift: cleanup.md L24 "Its `next` carries the question to put to them." In the default output the final JSON line
drops it: `print(json.dumps({k: v for k, v in out.items() if k not in ("next",)}))` (al.py L14116). `next`, with its
`decides: human` and `ask`, appears only with `--json` (L14100), which prints multi-line JSON.

Not in `--help` yet: what cleanup never touches (a module whose run lock is held, a milestone that isn't Done, the
plans, the delivery history: cleanup.md L35-36), and that it refuses inside a session the script started (L14077-14079).

Where it should go: `cleanup --help` for the rest, and the final line keeps `next`. The lead keeps two sentences:
show the user the list, and run `--yes` only on their yes, because nothing removed comes back; offer `--older-than`
when they want recent captures.

### 8. Locks and main-branch checks: `locks.md` plus four more copies

- `lead/references/locks.md` L1-59.
- `builder/SKILL.md` L152-157 (main-check answers), L181-198 (locks, `.alone`, 30 minutes, exit 124).
- `planner/references/profile.md` L63-67; `planner/references/done-when.md` L222-227.
- `README.md` L652-659; `GLOSSARY.md` L413-429.
- al.py docstring L267-274, L289-305; code comments L14102-14156; the builder prompt's `resources_rule()`
  (al.py L1056-1078), which already sends the project's resources, `lock <name> -- <command>`, `.alone`, and the
  hold limit to each builder of a project that has any.

Checked against code: 30 minutes (`DEFAULT_HOLD_LIMIT_S`), exit 124 (L3978-4006), the test command's hour
(`MERGE_TEST_TIMEOUT_S = 3600`), 55-minute wait (`MAIN_CHECK_WAIT_S = 3300`), three tries for exit 75
(`MAIN_CHECK_TRIES = 3`), a failed run retried once (comment L14108), `runner.log` (L14288). All match.

Where it should go: `lock --help` and `main-check --help` (the docstring paragraphs), and the builder's prompt for
the builder. builder SKILL L181-198 shrinks to the judgement: hold a lock only for the command that needs it; check
the user is there before taking a lock for a run that needs them; find a busy lock normal. locks.md keeps the lead's
judgement (L21-26: a busy lock is a limit more builders make worse; the fixes sit around the builders) and the
revert decision. The revert steps (L49-53: `git revert`, tell the builder, `human rereview`, `main-check <name>
--start`) could be the FAILING_ON_MAIN result's `next`.

### 9. Who changes which done-when field: five copies

- `planner/references/done-when.md` L353-387 (the full table).
- `builder/SKILL.md` L83-88, L58-60; `reviewer/tasks/milestone.md` L63-70.
- `README.md` L463-484.
- Code: `BUILDER_FIELDS`, `REVIEWER_FIELDS` (L2208-2209); `binding()` (L7166-7197) restates the builder's fields on
  every resumed turn; `builder/prompts/build.md` L3; `SCRIPT_SETS_STATE` (L5143-5146).

Where it should go: done-when.md keeps the table (the single reference others link to). The builder and reviewer
skills keep the rule and its reason in one sentence each and link the table, since the prompt states the exact
fields every turn.

### 10. Design review limit of two rounds: eight copies

- `lead/stages/4-build.md` L246-249; `planner/references/done-when.md` L324-329; `reviewer/tasks/design.md`
  L55-57; `planner/tasks/revise.md` L13-14; `README.md` L89-92; `GLOSSARY.md` L568-571 (open question).
- al.py docstring L324-325 (`DESIGN_REVIEW_ROUNDS`, L2346); `design_review_next()` (L9454-9476) already writes "This
  is the last of 2 design review rounds" into the planner's task and says it in `next.why`.

Where it should go: the script's output and prompts. Keep it in `reviewer/tasks/design.md`, because it changes the
reviewer's judgement ("put every Must Fix you find in this review"). revise.md L13-14 is conditional on the task
saying so, which the script does, so it can stay as a single line. Delete from 4-build (the `next` says it).

### 11. Statuses, Blocked reasons and `ready`'s groups: four copies, two disagreeing

- `planner/references/done-when.md` L291-329; `GLOSSARY.md` L321-364; `lead/stages/4-build.md` L120-138;
  `README.md` L195-201; `builder/SKILL.md` L65-67 (the five Blocked reasons a builder writes).
- al.py docstring L113-120 (`ready`), L84-127 (`run`'s results); `STATUSES`, `BLOCK_REASONS` (L530-537).

Drift between the prose copies (the code agrees with done-when.md):
- GLOSSARY L339: On Dependency, "another module's milestone, already planned". done-when L304: "whether or not that
  module has planned it yet". `depends_on` may name a heading-only milestone (done-when L258; planner/tasks/module.md
  L51-52).
- GLOSSARY's Waiting reasons (L335-340) leave out `for_planning`, which `ready` and `run` print (docstring
  L106-108; 4-build L128).

Where it should go: `ready --help` for its groups and `reason` values; done-when.md for the status table, linked
from lead and builder. GLOSSARY keeps the names and fixes the two rows.

### 12. Human decisions (`human <verb>`): four copies, and `--help` says nothing

- `lead/stages/4-build.md` L352-382; `README.md` L437-451, L508-512, L572-584; `planner/references/done-when.md`
  L376-377, L414-420; al.py docstring L230-247 (full meanings).
- `human --help`: verbs listed, no meanings (saved in helps.txt beside this report).

Where it should go: `human --help`, from the docstring. The lead keeps the judgement: never save a guess as the
user's answer; use `scope` only for an edit the user dictated exactly, show them the diff, run it on their yes; a
reviewer can't count a `--message` as the user's words, so their answers go through `human feedback`.

### 13. Items that need someone (`human_feedback`, `access`, `hardware`): five copies

- `builder/SKILL.md` L94-109; `planner/references/done-when.md` L234-246, L314-316; `lead/stages/4-build.md`
  L271-275; `README.md` L149-164.
- al.py `needs_rules()` (L7136-7163) puts the exact rule and ending for each such item into the builder's prompt,
  naming the items, headless or visible; `session_rule()` (L7081-7094); docstring L80-90.

Where it should go: done-when.md for the planner (what each means and when to use it). The builder prompt already
carries the per-milestone rule, so builder SKILL L94-109 can shrink to the judgement: do every other item first;
when the user turns down every option, make new ones only if their words say what to change. The lead keeps:
gather the user's sittings across modules, and a sitting takes a builder slot.

### 14. Visible sessions, sandboxes, Codex browser access: four copies

- `lead/stages/4-build.md` L251-288; `builder/SKILL.md` L220-231; `README.md` L514-528, L532-548, L605-614;
  `planner/references/profile.md` L46.
- al.py docstring L18-26, L262-266, L337-339; `session_rule()`; `settings` preflight browser warnings; output fields
  `path`, `path_reason`, `turn_not_stopped`, `blocked_write` (L1041).

Where it should go: README for people. The output fields should carry their own one-line meaning. The lead keeps:
whether to set `Codex sandbox: danger-full-access` is the user's choice; on `turn_not_stopped`, ask the user to press
Stop and wait before running the module again.

### 15. Merge mechanics: four copies

- `builder/SKILL.md` L159-179 (rebase, test command, push or fast-forward, batch, split on failure, `conflicts`,
  redefined items, `main_broken`); `README.md` L342-348; `GLOSSARY.md` L368-380; al.py docstring L92-111.
- `merge --help`: one flag (`--no-check`) and nothing else.

Where it should go: `merge --help` from the docstring; each FAILED `detail` already says what was wrong and what to
do (builder SKILL L170). The builder keeps two judgements: on `main_broken`, don't fix it yourself, because your fix
would race the owner's; on redefined items, take the main branch's plan files and rebuild against them.

### 16. Plan-file rules: three copies, one drifted (drift, mechanics)

- `planner/references/done-when.md` L152-155 (1,500 words, status lines, `###`, `## Log`, one line under Done; "`plan`
  and `adopt` refuse ... and `merge` warns"), L161-162 (LOG entries of at most eight lines).
- `builder/SKILL.md` L61-62: "`LOG.md` has an entry of up to eight lines ... The script refuses a longer entry".
- al.py `PLAN_WORDS`, `LOG_ENTRY_LINES`, `STATUS_LINE` (L12298-12300), `plan_checks()` (L12358), docstring L130-131.

Drift: the builder line is wrong for a builder. `merge` only warns: `warnings = plan_checks(worktree, prof, touched)`
(L10774), printed as `plan_warnings` (L10814), with the comment "A builder's edits to the plan files ... merge with
its work; the plan checks only warn here." The refusal is `plan`'s and `adopt`'s, as done-when says.

Where it should go: `plan_checks()` messages (they name the limit and the fix). done-when keeps the reason ("each is a
way a plan file grows until no builder reads all of it"). The builder line becomes "keep it to a few lines, and link
longer notes".

### 17. Watch and the lead's usual moves: the script already prints the list

- `lead/stages/4-build.md` L59-72 (watch: 3 hours, warning signs, `CHECK_IN`, `WARNING_SIGNS`, `--runs`,
  `RUN_ENDED`, `woke_for`), L79-89 (the usual moves).
- `README.md` L143-147, L311-316; `GLOSSARY.md` L436-452; `planner/references/profile.md` L37; al.py docstring
  L306-316 (the full list of signs and thresholds).
- `WATCH_WHY` (al.py L14996-14999), printed in watch's output: "message a builder (stop its run with `pause --module
  <M>`, then start it again with `run --message`), start a planner on a re-plan, change the order of the work, start a
  builder on ready work, or ask the user. Then start this command again in the background".

Checked: 3 hours (`LEAD_CHECK_IN_S`), 2 hours (`NO_PROGRESS_WARN_H`), 5 minutes (`READY_IDLE_WARN_S`) match.

Where it should go: `watch --help` (thresholds, result names) and `WATCH_WHY` (the moves). The lead keeps "Reading
delivery" (L95-118), which is the lead's real judgement, and the one-line rule to keep `watch` running.

### 18. `older-projects.md`: migration mechanics the docstring already holds

- `lead/references/older-projects.md` L1-86 (whole file).
- al.py docstring L144-185 covers `migrate`, `--to`, `--commit-map`, `--branch` and their results in more detail;
  `migrate --help` has the flags; `CHANGES` (L6352+) carries per-version notes into `changed`.

Where it should go: `migrate --help` and the refusal message that names `migrate` (it can name what to read and run).
The lead keeps: tell the user that a link checker will report links into `.orchestrate/evidence`; rewriting history
needs every run stopped; then `migrate --commit-map`. L50-66 (the 2.2 renames) and L68-86 are history, which the
`changed` output and `migrate` handle.

### 19. Delivery history, report and cost: storage and contents described three times

- `lead/references/delivery-history.md` L14-51; `README.md` L171-175; `GLOSSARY.md` L461-495;
  delivery_history.py docstring L1-30; al.py docstring L197-221 (`cost`, `report`).
- `lead/references/report.md` L10-18 ("The facts") repeats `report --help` and docstring L203-221.

Checked: weights (delivery_history.py L54-57: cache read 0.1, output 5.0 Claude, 8.0 Codex), Claude's 30 days
(delivery_history.py L5), report window (`REPORT_REPEAT_S = 3600`, `REPORT_DEFAULT_H = 24.0`), the "fewer than about
ten" graded-examples flag (L11884-11885). All match.

Where it should go: `history`, `dashboard` and `report` `--help`. The lead keeps delivery-history.md L5-12 (read it
before proposing a process change, and again after) and report.md "What you add" (L20-46).

### 20. Background jobs: three copies

- `builder/SKILL.md` L200-209; `reviewer/SKILL.md` L75-81; `reviewer/prompts/review.md` L10 and
  `design-review.md` L9; `GLOSSARY.md` L431-434.
- `background`, `wait` and `jobs` `--help` already give the defaults (`wait --timeout` 540, "under Claude's
  ten-minute Bash limit").

Where it should go: `--help`. Keep in both skills the reason that is judgement: every look re-reads the whole
session, so a few long waits cost less than many short looks.

### 21. Model and file-layout tables repeated across planner files

- Module table header: `planner/tasks/project.md` L10-17 and `planner/references/done-when.md` L84-99, the same table
  and "The script reads it, so keep this header"; al.py docstring L35-36; `TABLE_HEADER` L12392.
- File tree: `planner/SKILL.md` L21-34, `done-when.md` L25-41, `README.md` L185-189, `lead/SKILL.md` L76-79,
  `builder/SKILL.md` L30, `reviewer/SKILL.md` L39-41, al.py docstring L28-37.

Where it should go: done-when.md once, linked; and `paths` (Finding 5) for the actual locations.

### 22. The `next` field's rules: two copies

- `lead/SKILL.md` L45-62 (`next.by`, `decides: human`, `ask`, `argv`, the worktree it names, reused hosts, adding
  `--task` or `--message`).
- al.py docstring L148-160 says the same, including the worktree caveat and last-runs.json.

Where it should go: script behaviour for the worktree caveat. A `next` printed by `ready` or `status` in the main
checkout could name the module's worktree itself once the script makes worktrees (Finding 2), which removes L54-56.
The rest stays in the lead skill, which is the only reader.

### 23. Smaller duplications between the reviewer prompts and tasks

- `reviewer/tasks/design.md` L53 ("Write the review to `<evidence>/<MODULE>/design-review.md`") and
  `reviewer/tasks/milestone.md` L61-62 restate `{review}` and `{captures}`, which the prompt fills in.
- `reviewer/tasks/milestone.md` L43-46 (User Feedback location in RECORD.json) repeats `feedback_note()`
  (al.py L7039-7051), which puts the record path and the user's words into the prompt.
- `reviewer/prompts/design-review.md` L4 has a `{briefs}` placeholder that `review_prompt()` always fills with `""`
  (al.py L9496); the briefs go into `{changed}` (L9164-9168). Dead placeholder.

Where it should go: the prompt. The tasks say "the paths your prompt gives".

## Drift summary (every item verified against code)

| # | File, lines | Claim | What the code does | Mechanics? |
|---|---|---|---|---|
| D1 | `lead/SKILL.md` L36-43, L64-68 | Every command ends with one JSON line with `version`, `warnings`, `result_file`; exit 0 except ERROR/SCRIPT_FAILED, bar five named commands | Only `run`, `review`, `plan`, `pause`, `unblock`, `watch` go through `emit()` (L6887). `ready`/`settings` print `json.dumps(out, indent=2)`; `adopt`/`migrate` `done_with(...)` exit 1 on REFUSED/FAILED with no `version`; `human` exits 1 on FAILED; status/report/check/cost print text | Yes |
| D2 | `lead/stages/4-build.md` L200-201 | "Any command prints `REFUSED`" | Only `run` (L8313, L8355), `adopt` (L12804, L12875), `migrate` (L13567+) | Yes |
| D3 | `lead/stages/2-start-planning.md` L20-23 | Commit the settings with git "because `adopt` never merges the settings" | `adoptable()` L12217-12221 returns None for a first ORCHESTRATE.md, so `adopt` does merge it. But `cmd_adopt` calls `profile(worktree, strict=True)` (L12760), which exits on a missing `Test command:`, and stage 2 leaves that line out, so adopt can't run there anyway. The reason given is wrong, and the CLI has a dead path to resolve | Yes |
| D4 | `lead/references/cleanup.md` L24 | "Its `next` carries the question" | Final line drops `next` (L14116); only `--json` keeps it | Yes |
| D5 | `builder/SKILL.md` L61-62 | "The script refuses a longer entry" (LOG.md over 8 lines) | `merge` only warns, as `plan_warnings` (L10774, L10814); refusal is `plan`'s and `adopt`'s | Yes |
| D6 | `README.md` L298 | "a script of about 13,500 lines" | 15,695 lines | No (fact) |
| D7 | `README.md` L113-116, L377-378 | A reviewer is needed for inspect/ask items or the module's last milestone | `needs_review()` L2093-2103 also reviews the last milestone of a planned stretch (`ends_stretch`) unless it asks the user | Yes (behaviour added) |
| D8 | `planner/references/done-when.md` L391 | Escalation steps "are written down only here" | Also in 4-build L228-237, README L120-136, docstring L196-206, diagnose.md L47-49 | No (prose) |
| D9 | `README.md` L125-136 | Table: 3 failed reviews → new builder; silent on 4-5; table doesn't render | `escalation()` L2147: new session only at exactly 3 (or 3 repeats); 4-5 → `same_builder` | Yes |
| D10 | `GLOSSARY.md` L335-340 | On Dependency needs a milestone "already planned"; no For Planning reason | `depends_on` may name a heading-only milestone; `ready` prints `reason: for_planning` (docstring L106-108) | Partly |
| D11 | `run --help` and others | `--host` "(default: see above)"; `--no-progress-hours` without default or the commit condition; `--turn-timeout-hours` no help | Default host resolution is in the docstring L14-16; defaults 4.0 and 2.0 (L15380, L15363) | Yes (help text) |
| D12 | `reviewer/prompts/design-review.md` L4 | `{briefs}` placeholder | Always `""` (L9496) | Yes (template) |
| D13 | `GLOSSARY.md` L525, L533-534 | CHECKS_FAILED on one disagreement; PAUSED not from `review`; INVALID not from `watch` | Three DONEs (docstring L94); `review` prints PAUSED; `watch` emits INVALID | Yes |

Everything else checked matched the code: the escalation thresholds in done-when.md, the two design review rounds,
30-minute lock hold limit and exit 124, the test command's hour, `wait`'s nine minutes (`JOB_WAIT_S = 540`), the
15-minute open tool call (`TOOL_CALL_LIMIT_S`), three stalled turns (`STALL_TURNS`), 3-hour check-in and 2-hour
warning, main-check's 55-minute wait, three tries and one retry, report's window, the history weights and folder, the
runs folder, the checkout cleanup (6 hours, half an hour under 30 GB: L4595-4597), default models and efforts,
Claude permissions and Codex sandbox defaults, `approvals_reviewer=auto_review` and the two no-subagent flags
(L984-989, L5890).

## Related CLI improvements found while checking (not drift)

- `review --commit` isn't marked required. A milestone review without it fails INVALID with "commit None doesn't
  exist here" (L9074-9076). The script holds the Ready for Review record's commit and could default to it, which
  lets 4-build L157 and builder L267-268 drop "with the commit that result names".
- The module docstring is itself a third copy of the skills' mechanics. Once its paragraphs move into `--help`, it
  should shrink to the design notes, or it becomes the next thing to drift.

## CLI changes the cleanup depends on, in order

1. **Per-command `--help` descriptions** from the docstring, plus the missing commands, and the help-text fixes
   (Finding 0). Unblocks Findings 3, 4, 7, 8, 12, 15, 17, 18, 19, 20.
2. **One output path for every command** (`emit()`), so the lead skill's output contract is true (Finding 1, D1).
   Keep `next` on `cleanup`'s final line (D4).
3. **A `paths` command** (or a `paths` block in `settings`) with absolute locations (Finding 5, 21).
4. **`run` makes and removes module worktrees** (Finding 2), and `next` from `ready` names the module's worktree
   (Finding 22).
5. **A settings-change command** that commits and merges an ORCHESTRATE.md line with the user's words, and
   `settings` output that shows where each resolved model and effort came from (Finding 6). Resolve the `adopt`
   first-settings path that strict `profile()` makes unreachable (D3).
6. **`review` defaults `--commit`** to the Ready for Review record's commit.
7. **New output fields' meanings**: `settings_read_from`, `settings_differ`, `ran_on`, `turn_not_stopped`,
   `blocked_write`, `path_reason` carry a one-line meaning, so the lead skill needn't explain them (Findings 6, 14).
