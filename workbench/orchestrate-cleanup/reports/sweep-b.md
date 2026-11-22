# Sweep B: what in the orchestrate skills belongs in the CLI

Read in reverse order: reviewer, planner, builder, lead, then the prompt templates (`*/prompts/*.md` and the prompt
builders in `agent_loop.py`). Every agent-facing file in `skills/orchestration` was read in full. `README.md` and
`GLOSSARY.md` are for people and were not judged. Line numbers are from the files on disk on 2026-11-22.

Verdicts: **KEEP** (the agent's judgement), **CLAUSE** (cut to one clause or a pointer), **MOVE** (to script
behaviour, command output, a command's `--help`, or a settings file the CLI reads), **DELETE** (already said by the
CLI or the prompt, or general knowledge).

## A finding that comes first: `--help` is empty today

Every subcommand is registered with `sub.add_parser(name, help=...)` only (`agent_loop.py` 15365-15598). No parser
has `description=` or `epilog=` (the only `description=` is the top-level `Parser(description=USAGE)` at 15355). So
`agent_loop.py cleanup --help`, `ready --help`, `human --help` and the rest print a bare flag list, without even the
one-line summary that the top-level list shows. The top-level help says "The docstring at the top of this file
explains the whole design", but `--help` never prints that docstring.

So every "move to `--help`" below depends on one piece of script work: give each subparser a `description` (and
an `epilog` where needed) built from the matching part of the module docstring, which already holds most of this
text (lines 1-440: results, statuses, `next`, escalation, migrate, main-check). Do this first. Most of the cuts below
then mean moving text once, not writing it.

## Ranked findings

### 1. `planner/references/done-when.md`: about 300 of 420 lines are script mechanics

The planner needs the shape of the files it writes and the rules for writing them. Most of this file describes what
the script does with them, which the script enforces anyway, and which the module docstring already documents.

| Lines | Quote | What it is | Where it goes | Does the CLI already have it? |
|---|---|---|---|---|
| 291-329 | "The `In status` column is the value stored in the milestone's `status` field" | Status table, Blocked reasons, design statuses, `by: review_limit` | DELETE from the skill; MOVE to `ready --help` / `status --help` epilog | Yes: docstring 79-130 (run results, WAITING reasons), `ready` and `status` output each carry `reason` and `next` |
| 331-351 | "Beside each done-when file, the script keeps `RECORD.json`" | Record file contents and first-adoption rule | DELETE | Yes: docstring 41-48 ("What the script owns") says the same |
| 353-387 | "Only one kind of agent changes each field at any time" (the "Who changes what" table) | Who sets each field, and when | DELETE. Each role's prompt already names its own fields: build goal (`builder/prompts/build.md` 3), `binding()` 7182-7185, review prompt line 3. The script rejects anything else with a message | Yes: enforcement in `review`/`merge`/`plan` refusals; `SCRIPT_SETS_STATE` 5143 |
| 389-420 | "These are the escalation steps, and they are written down only here" | Thresholds (4 / 6 / 3), Re-plan vs Plan Kept, counts reset | DELETE; MOVE to `next --help` epilog. Keep one clause in `planner/tasks/diagnose.md` ("a milestone gets one diagnosis") | Yes: `FAILED_REVIEWS_TO_DIAGNOSE` 2127, `NEW_SESSION_AFTER_FAILED_REVIEWS` 2125; every failed review's result carries `escalation` and `next` with the message already written |
| 263-289 | "The other fields record what happened" | `builder_result`, `verdict`, `findings`, the three counts, `diagnosed_for_planner_finding`, when a milestone needs a reviewer | DELETE the counts and `diagnosed_for_planner_finding` (the planner never writes them, and the script puts back any change). KEEP 286-289 as one sentence in planner `SKILL.md`, which already has it at 143-145 (so this copy goes) | Yes: `needs_review()` 2097 |
| 20-50 | "Every project keeps its plans in the same place" + tree + "Evidence is never committed" | Paths, the evidence link, cleanup | MOVE to a `paths` command (see CLI change B). KEEP 43-45 ("A project's plans live in these files and nowhere besides") as judgement | Partly: `settings` prints `plans`, `evidence`, `graded_examples` |
| 61-82 | "The script writes `STATUS.md` after every record it merges" | What the script-written page contains | CLAUSE: keep 80-82 ("name a milestone for what someone can see or do") | Yes: `status --format md` prints it |
| 124-127 | "When a module has one planned milestone left, `ready` lists the module under `plan_ahead`" | Lead-side mechanics | DELETE (it's for the lead, and `ready` output carries it) | Yes: `ready` `plan_ahead` |
| 152-155 | "The script checks every plan file it merges for five things" | Plan lint rules | CLAUSE ("`plan` and `adopt` refuse a plan file that collects status or history, and say why") | Yes: `PLAN_WORDS` 12298, `LOG_ENTRY_LINES` 12299, refusal messages 12350-12353 |
| 161-163 | "`plan` and `adopt` refuse an entry of more than eight lines" | Log limit | CLAUSE | Yes: same as above |
| 222-233 | "`lock` is optional ... `reads` is optional ... The script remembers a check that passed" | Lock semantics and check-reuse cache | CLAUSE each to what to write ("`reads`: the files the check reads, as pathspecs, so a pass is reused while they stay the same"). The cache rules (uncommitted changes, no-match) go to `check --help` | Partly: `check --help` is bare today |
| 250-253 | "Its run waits for the turns under way to end, and no new builder turn ... starts" | What `alone` does to scheduling | CLAUSE ("`alone: true` holds every other agent back while it runs, so use it for the one milestone of precise measurements") | No help text; docstring only |
| 254-258 | "The script reports an error for a later milestone of the same module ..." | `depends_on` validation | DELETE the list; the validator's own messages say it | Yes: done-when validation errors |
| 47-50, 134-135, 161 | evidence path `.orchestrate/evidence/<MODULE>/` repeated | Path | DELETE (see group 7) | `settings` `evidence` |

What stays: the readers table (52-59), the module table header (84-99, which the script parses), the PLAN.md shape and
the guidance on notes and limits (101-150), the LOG.md shape (157-168), and the `DONE.json` example and planner fields
(170-259, trimmed as above). Roughly 120 lines.

Knock-on links to fix: reviewer `tasks/milestone.md` 70, builder `SKILL.md` 85, lead `stages/4-build.md` 137, 217
and 235 all link to sections that would go. Each can lose its link, because the CLI output those passages describe
already gives the agent its next step.

### 2. `planner/references/profile.md` (149 lines) and `lead/references/settings.md` (16 lines): a settings schema in prose

This is the user's "settings belongs in the CLI" case. The file is a template of every `ORCHESTRATE.md` line, each
with its default and what the script does with it, plus the model/effort resolution order.

| Lines | Quote | What it is | Where it goes | CLI has it? |
|---|---|---|---|---|
| 7-13 | "The script, `agent_loop.py`, reads the lines marked *(script)*" | Parse rules, required lines | MOVE to `settings --help` | `profile_value()` 680; `REQUIRED` 656 has the reasons |
| 20-73 | the whole template with `*(script: ...)*` notes | Labels, defaults, allowed values | MOVE to `settings --template` (CLI change C), generated from `PROFILE_FIELDS` 650, `REQUIRED`, `ALLOWED` 660, so defaults can't drift | Defaults and allowed values exist in code; no command prints them as a template |
| 84-86 | "The script runs `Setup command` again in a checkout only when a tracked manifest or lockfile there has changed" | Script behaviour | MOVE to the template note | Code only |
| 93-99, 103-104 | "`Review host` says where a review runs ..." | Semantics of same/other | MOVE to template note and `review --help` (whose `--host` says "default: see above" with nothing above) | `run --review-host` help has it |
| 106-110 | "`BRIEF.md`, `GLOSSARY.md` ... sit in the plans folder by name" | Paths | DELETE | — |
| 112-147 | "For each launch, the script takes the first of these that is set" | Model/effort resolution order and the role-line table | MOVE to `settings --help`; the `settings` output could also show the resolved model and effort per role and host, with where each came from | `role_lines()` 718; `--model`/`--effort` help states the order briefly |
| 77-82, 88-91, 100-101, 149 | "Leave out each host or model line the user said nothing about"; "`Merge: push` is standing permission ... set it only if the user has given that permission"; "Write `other` when the user builds with both hosts"; "A larger model ... spends the user's quota faster" | The lead's judgement on the user's choices | KEEP, but move into `lead/stages/2-start-planning.md` beside the step that writes them; the planner never writes these lines | — |

`lead/references/settings.md`:

| Lines | Quote | Verdict | CLI has it? |
|---|---|---|---|
| 3-5 | "The lead writes a line in `ORCHESTRATE.md` when the user asks" | CLAUSE into stage 2 | — |
| 7-8 | "`adopt` won't merge a changed `ORCHESTRATE.md` ... So commit it with git in the main working copy" | MOVE to script behaviour: `settings set <Label> <value> --said "<user's words>"` writes the line, commits on the main branch and pushes under `Merge: push` (CLI change C) | `ready` `settings_differ` already tells the lead to commit it (`profile_note()` 3550); `set_setting_line()` exists (used by migrate, 13356) |
| 10-12 | "A worktree ... then runs on the main branch's settings, and its result says so in `settings_read_from`" | DELETE | Yes: `settings_read_from` 929, `settings_differ` |
| 14-16 | "Check `ran_on` in the next result before you tell the user a change has taken effect" | CLAUSE into stage 2 (it's a judgement about what to tell the user) | `ran_on`, `WRONG_MODEL_OR_EFFORT` |

Result: delete `settings.md`, cut `profile.md` to nothing (or to a short "how to choose" section in the lead), and
point at `settings --template` / `settings set`. Also fixes the oddity that a planner reference holds lead-only
judgement.

### 3. `lead/stages/4-build.md` (401 lines): about 150 lines describe what commands do or print

| Lines | Quote | What it is | Where it goes | CLI has it? |
|---|---|---|---|---|
| 37-41 | "Give each module its own worktree on its own branch, in a folder git ignores. A worktree is a second working copy" | Procedure plus general git knowledge | MOVE to script behaviour (CLI change D): `run --module M` without `--worktree` makes or reuses `build/<module>` in an ignored folder (it already knows `info/exclude`, 1173, and how to `worktree add`, 4666), branching from the remote under `Merge: push` | No: script makes only its own checkouts |
| 195, 400-401 | "`FINISHED` ... Remove its worktree once nothing is unmerged"; "remove build outputs and the worktrees whose work is merged" | Procedure | MOVE: the script removes a module worktree it made once FINISHED and nothing is unmerged | `after_pass()` 9449 already tells the lead to `git worktree remove`; it could do it |
| 26-33 | "The script already picks the model and effort from the project settings, or medium effort (high for planners)" | Defaults | CLAUSE: keep "pass `--model`/`--effort` only when the user asked for that one command" (judgement); defaults are in `--effort` help | Yes: `--effort` help "default: medium (high for planners)" |
| 43-53 | "`run --module <M> --worktree <path>` starts a builder ... carries on through the steps that need no judgement" | What run/plan chain does, `steps_run`, `stopped_because` | CLAUSE to two sentences; detail to `run --help` / `plan --help` (`--one-step` help already describes the chain) | Yes, mostly: `--one-step` help on both |
| 61-72 | "It wakes you in two cases ... every three hours unless the settings' `Lead check-in:` line says otherwise ... Start `watch` again each time it ends" | watch mechanics, default | CLAUSE ("keep `watch` running; it wakes you at the check-in or a warning sign"); MOVE the default and the result names to `watch --help` | Yes: `watch` result's `next` is `watch` again (15303); `--runs` help covers 68-69 |
| 122-149 | the `ready` group table and `plan_ahead` / `unmerged_plans` / `adopt` approval | What `ready` prints | MOVE table to `ready --help` epilog; DELETE `plan_ahead` and `adopt` mechanics (each comes with `next`) | Yes: `ready` output carries `next` per module, `unmerged_plans` → `next` `adopt` |
| 163-173 | "Reviewers and planners work in a checkout the script keeps for them ... A planner given `--module <M>` may change only ..." | Planner scope and merge rules | DELETE most; `plan --module` help says it; keep "give `--module` to a task of yours that reaches one module" | Yes: `plan --module` help; `scope_text()` 591 tells the planner |
| 175-178 | "`Review host: other` in the project settings makes that the default" | Setting semantics | CLAUSE (keep the reason: a reviewer from another company shares fewer blind spots) | `run --review-host` help |
| 182-210 | "What each result means" table and the paragraphs after it | Per-result handling | DELETE the rows whose handling is "run `next`" (`WAITING`, `CHECKS_FAILED`/`STALLED`, `INVALID`, `SCRIPT_FAILED`, `FINISHED`, `NEEDS_REVIEW`, `PLAN_NOT_MERGED`, `UNFINISHED`, `ADOPTED`, `RELEASED`, `UNBLOCKED`, `REFUSED`, `main_broken`, `merge_kept_later`, `stopped_turn`). KEEP the three that are judgement: tell the user on a `HOST_FAILED` usage limit, on `WRONG_MODEL_OR_EFFORT`, and leave a `PAUSED` builder to the user | Yes: docstring 79-130 and every result's `next`/`why` |
| 224-249 | "As the counts rise, the same builder carries on (`same_builder`), then ..." | Escalation ladder, `found`, `filled`, `INVALID` review, design-review rounds | CLAUSE; KEEP 233-234 ("stepping around the counts repeats an attempt that already failed") and 239-240 ("add nothing about which findings to fix") | Yes: `escalation`, `next` with message written; `design_review_next()` 9453 |
| 264-265 | "With `ORCHESTRATE_VISIBLE=1` on a Mac ..." | Env var | KEEP as a clause (lead's choice when the user is present) | docstring 18-25 |
| 271-275 | "can only finish in a visible session ... run its `next` (the same command with `ORCHESTRATE_VISIBLE=1`)" | Already the `next` | CLAUSE (keep "put its `ask` to the user, run `next` when they're there") | Yes: BLOCKED needs_access `next` |
| 286-288 | "`turn_not_stopped`, naming the thread ... Ask the user to open it and press Stop" | Output field | KEEP (needs the user), or MOVE into that result's `next` with `decides: human` | Field exists; no `next` |
| 305-312 | "`--kind change` ... `--human-rule` ... `--clear-human-rules` ... `--message`" | Flag semantics | CLAUSE; flag help already says each | Yes: `run --human-rule`, `--clear-human-rules`, `plan --kind` help |
| 354-364 | the `human <verb>` table | What each verb saves | MOVE to `human --help` epilog (the positional `action` has no help); KEEP the `scope` judgement ("only for an edit the user dictated exactly ... show them the diff, and run it on their yes") | No: `human --help` lists verbs with no meaning |
| 366-371 | "A milestone with `"alone": true` ... Its run waits for the turns under way to end" | Mechanics, third copy (done-when 250-253, proofs 98-101) | CLAUSE; KEEP the judgement ("start it when other modules can spare the time; gather sittings; pause a builder rather than ask for another slot") | docstring |
| 373-377 | "Once the pick is Done, `ready` lists under `plan_ahead` a planner task to write them" | ready output | DELETE (keep "when the user turns every option down, the reference may be the problem") | Yes: `plan_ahead` with `next` |
| 379-382 | "the script adds the review to that file ... The `human` commands refuse to run while a `run` ... is working" | Output and refusal | DELETE | Yes: `graded_example` field 13124; refusal message |

What stays is the core of the stage: When you're woken (76-93), Reading delivery (95-118), Where sessions run's
sandbox judgement (253-262), What you pass on (292-303), Questions from the agents (316-350), Telling the user
(386-396), When to stop.

### 4. `lead/references/cleanup.md` (40 lines): delete the file

| Lines | Quote | CLI has it? |
|---|---|---|
| 5-18 | "The working folder, `<git common dir>/orchestrate/evidence/`, holds builders' proof ..." | Paths: `cleanup --json` lists every path with size; move a one-paragraph "what is kept where" to `cleanup --help` description |
| 22-24 | "lists what it would remove ... `WOULD_REMOVE` ... run it again with `--yes` only on their yes" | Yes: `next` with `ask` and "run it only on the user's yes" (`cmd_cleanup` 14093-14095) |
| 26-36 | the `--kind` table, `--older-than`, `--json`, what it never touches | Yes, nearly word for word: `cleanup --help` `--kind` text; "never touches" is in the comment at 13886 and should go in the description |
| 38-40 | "Evidence for a milestone that is Done has served its reviewer ... Offer `--older-than`" | One clause of judgement; fold into the lead's one-line pointer to `cleanup` |

Replace with one line in `4-build.md` 267-269: "`cleanup` lists what the build keeps on this computer; show the user
and remove only on their yes."

### 5. `lead/references/older-projects.md` (86 lines): the refusals already carry the commands

| Lines | Quote | What / where | CLI has it? |
|---|---|---|---|
| 3-10 | "Run `migrate --worktree <repo>` once, adding `--to docs/plans`" | DELETE | Yes: `flat_refusal()` 1623, `old_names_refusal()` 1613, `evidence_refusal()` 1201 print the exact command; `migrate --to` help |
| 12-14 | "After a move, start a planner with `plan --kind fix` to bring the plans into the current shape" | MOVE to MIGRATED's `next` (today `next` is `status`, 13880) — small script change F | No |
| 18-41 | evidence migration details, link checker, history rewrite, `--commit-map` | MOVE to `migrate --help` description; the "tell the user a link checker will report these" line is the only judgement (already in MIGRATED `evidence` detail, 13866-13872) | Partly: `--commit-map` help; evidence detail in output |
| 45-48 | "Run `migrate --branch --worktree <its worktree>` instead" | DELETE | Yes: refusal text and `migrate` lists `worktrees_on_old_names` |
| 50-66 | names changed in 2.2 | DELETE (or `migrate --help`) | `old_names_refusal` lists what it found; `owner` alias kept |
| 70-72 | builder-set Ready for Review | DELETE | Yes: `review` prints INVALID with `next` |
| 74-78 | daily report files | DELETE | — |
| 80-86 | "No `Graded examples:` line ... Suggest to the user that you add the line" | MOVE to a `settings` preflight warning (the script can see the file exists and the line doesn't) | No |

### 6. The three other lead references: keep the judgement, move the mechanics

`lead/references/locks.md` (59 lines):
- 8-19 "A lock lets runs share something ... 30 minutes unless they say otherwise ... the test command ... keeps its own limit of an hour": MOVE to `lock --help` (bare today); third copy of builder `SKILL.md` 183-198 and `proofs.md` 62-76.
- 21-26 "A lock that is busy most of the day ... is a limit that more builders make worse": KEEP (reading delivery). Fold into `4-build.md` Reading delivery.
- 30-40 main-check mechanics, `MAIN_CHECKS`, `STARTED`, `ALREADY_RUNNING`, `runner.log`, `RAN`: MOVE to `main-check --help` description.
- 42-47 "Start a planner with `plan --kind fix`, naming the commit": MOVE into FAILING_ON_MAIN's `next` (today `next_cmd(None, ...)` with prose, 14546-14556) as a real `plan --kind fix` command — CLI change F.
- 49-53 revert: KEEP (lead decision: tell the module's builder, `human rereview` a Done milestone whose work was reverted). Could also be a `next` after a revert lands.
- 55-59 exit 75 / `unjudged`: MOVE to `main-check --help`.
- Result: about 12 lines, which fit in `4-build.md`, so the file can go.

`lead/references/delivery-history.md` (51 lines):
- 5-12: KEEP (when to read the history and offer the dashboard).
- 16-28 "Claude Code deletes its session files after 30 days ... `~/.orchestrate/history/<repository>-<hash>/`, or under `$ORCHESTRATE_HISTORY_DIR`": MOVE to `history --help` description.
- 32-39 what `history --json` and `dashboard` print: MOVE to their `--help` (`--json` help already says "the summary: totals, errors by kind ...").
- 43-51 weighted tokens, multipliers: DELETE; the brief itself says the history "says which is which wherever it shows one", so the output labels it. Multipliers belong in `cost`/`history --help`.
- Result: 8 lines, foldable into `4-build.md` Reading delivery.

`lead/references/report.md` (46 lines):
- 10-14 default window, `--since`, `--write` path: DELETE; `report --help` says it word for word.
- 16-18 the report's parts: DELETE (the output has headings).
- 3-6, 22-46: KEEP (what the lead adds; it's all judgement). Small enough to stay as a file or move into `4-build.md` Telling the user.

### 7. Paths described in every skill: one `paths` command, and the prompts already give per-session paths

The plans folder, module files, evidence root and its layout, graded examples and references are described in:

- planner `SKILL.md` 19-36 (tree), `done-when.md` 20-50 (tree), `tasks/module.md` 6-7
- lead `SKILL.md` 70-83, `stages/4-build.md` 267-269, `references/cleanup.md` 5-18
- reviewer `SKILL.md` 20-40 ("Reviews, captures and the builder's evidence are in the working folder, written `<evidence>` below: the settings' `Evidence:` path, `.orchestrate/evidence` unless they name another"), `tasks/milestone.md` 61-62, `tasks/design.md` 53
- builder `SKILL.md` 20-37, 51-57 ("It goes in the working folder, at `<evidence>/<MODULE>/<milestone>/`, where `<evidence>` is the settings' `Evidence:` path"), 76, 139-140
- the docstring 27-38 (the canonical one)

Fix: a `paths` command, or a `paths` block in `settings` output (CLI change B), that prints every location resolved
for this project: plans folder and each project file, a module's files, the evidence root and per-module layout
(captures, reviews, handoffs), graded examples, references, the script, and the git-dir folders (jobs, results,
reports, verify, history). Each skill then says "run `settings` for where things are", and keeps only what a file is
for.

The spawned agents don't need even that. Their prompts already carry the paths: the review prompt gives `{review}`,
`{captures}`, `{done}`, `{glossary}` (`review_prompt()` 9486); the build prompt gives `{done}`, `{captures}`,
`{handoff}`, `{glossary}` (`build_prompt()` 7119). The one gap: the review prompt doesn't name the graded examples
file, though the script computes it (`graded_examples`, 884-888), so reviewer `SKILL.md` 30-33 has to explain the
fallback rule. Add `{graded}` to `reviewer/prompts/review.md` and `design-review.md`, then cut 30-33 to "read the
graded examples your prompt names".

### 8. Passages the prompt already says to the same agent

These go outright, because the script already sends the text, filled in for this milestone:

| Skill passage | Quote | The prompt text that already says it |
|---|---|---|
| builder `SKILL.md` 94-109 | "`human_feedback`: someone has to judge the result ... `access` ... `hardware`" | `needs_rules()` 7135, in `{needs}` of the build prompt and in every resumed turn (`binding()` 7186), naming the items. KEEP only 99-103 (what to do when the user turns every option down) |
| builder `SKILL.md` 183-188 | "wrap it in `agent_loop.py lock <name> -- <command>`. A lock is about capacity" | `resources_rule()` 7058, in `{resources}`, with this project's resource names and counts and the hold limit |
| builder `SKILL.md` 70-74 | "When you end with `DONE`, the script runs the test command and every item's check on the merged work" | The goal line of `builder/prompts/build.md` 3 |
| builder `SKILL.md` 172-179 | "`conflicts` names files that clash ... `main_broken` means ..." | `merge`'s own `detail`: `build_batch()` 11315 (conflicts: "Fetch, rebase ... run merge again"), `main_broken_result()` 11265 ("end your turn with `BLOCKED main_broken: ...`") |
| builder `SKILL.md` 152-157 | "On your branch it answers `NOT_ON_MAIN` ... `FAILING_ON_MAIN` names the commit" | `main-check` result `why` and `next` (14536-14556) |
| builder `SKILL.md` 263-273 | "After you merge, run `run --checks-only` ... Otherwise start the reviewer with `review ...` ... After a failed review, run `next`" | `--checks-only` help; READY_FOR_REVIEW's `next` is the review command (docstring 79-90); `next` command. Keep step 1 as a clause and the rule that only a `review`-started review counts |
| reviewer `tasks/milestone.md` 3-5, 34-36 | "The script then ran the project's test command and every item's check on the merged work"; "you can rely on that result, so run a check again only when you have a reason to doubt it" | `checks_note()` 7918, in `{checks}`: "Run one again only if you doubt that result" |
| reviewer `tasks/milestone.md` 43-46 | "The script records it as User Feedback in `RECORD.json`, under `human_feedback`, with the question the lead asked" | `feedback_note()` 7039 in `{answers}`, with the record path and "Check any claim about what the user chose against it" |
| reviewer `tasks/milestone.md` 84 | "your prompt says how many the script is counting and where they are" | KEEP (it points at `review_notes()` 2688, which is right) |
| planner `tasks/module.md` 52-54 | "When your task is limited to this module ... end with `BLOCKED: needs <MODULE>'s files`" | `scope_text()` 591, word for word |
| planner `SKILL.md` 170-171 | "Try each with the script's `check` command from your prompt, which saves nothing" | `planner/prompts/plan.md` 10. Keep the judgement ("on work not built yet it should say `fail`; `error` means the check is broken") |
| reviewer `SKILL.md` 15-18 | "When you finish, that command checks what you changed, records your result and merges it" | review prompt line 11 ("the script keeps them there") and `binding()` 7179 |

### 9. Long-command and lock mechanics repeated across roles

- builder `SKILL.md` 200-209 and reviewer `SKILL.md` 75-81 both explain `background` / `wait` / `jobs`, including
  "after nine minutes". MOVE the mechanics to `background --help` and `wait --help` (`--timeout` help already says
  540 s and why). KEEP one sentence each: "a command that can outlast your turn goes through `background` and
  `wait`; a few long waits cost far less than many short looks". The reviewer prompt line "for the `background` and
  `wait` commands the skill describes" can then say "see `background --help`".
- builder `SKILL.md` 190-198: "`check` takes each item's lock itself and `merge` waits in its own queue, so don't
  wrap either in `lock`, which refuses them" — DELETE; `cmd_lock()` 10409-10414 refuses with that explanation. "The
  script stops a command that holds a lock longer than the settings' `Lock hold limit` (30 minutes by default),
  with exit code 124" — MOVE to `lock --help`; `resources_rule()` already tells builders the limit. KEEP: "before you
  take a lock for a run that needs the user or the screen, check the user is there" and "end with BLOCKED only if
  the holder seems stuck".
- builder `SKILL.md` 165-168 "`merge` queues their branches and merges them as one batch ... splits the batch"
  and `proofs.md` 72-76 (same): MOVE to `merge --help`. Keep in `proofs.md` only the planning consequence ("the test
  command's length sets how many merges an hour the project gets").

### 10. The definition of `check` / `inspect` / `ask` is written five times

planner `SKILL.md` 93-103, `proofs.md` 17-24, `done-when.md` 215-219, reviewer `SKILL.md` 41-46, builder
`SKILL.md` 39-45. Keep it in planner `SKILL.md` (the author of items) and `proofs.md` (the reference). In the reviewer
and builder, one line and the link is enough. `done-when.md` 215-219 goes.

### 11. The "options, then the user's pick" pattern is written four times

planner `SKILL.md` 124-134, `proofs.md` 160-182, `tasks/project.md` 39-41, `tasks/change.md` 21-26, plus lead
`4-build.md` 373-377. Keep it in `proofs.md#subjective-work`; the SKILL keeps two sentences and the link; `project.md`
keeps the one ordering fact (options made outside the product needn't wait for the project's first milestone). Also
`proofs.md` 168-171 ("the lead saves the question and their reply with the `human feedback` command. The script
records it as User Feedback") is lead/script mechanics the planner doesn't act on: DELETE.

### 12. Procedures the planner does by hand that the script could do

- planner `tasks/diagnose.md` 32-34: "Give each milestone you split off a `diagnoses` count one higher than the one
  it came from shows, because the script adds one to that milestone when your turn merges, and can't tell which new
  milestone came from which." The planner does bookkeeping because the script lacks a link. MOVE to script
  behaviour (CLI change G): a `split_from` field on a new milestone, or the script inheriting the count for every
  milestone added in a diagnosis turn. Then delete the paragraph and the matching row in `done-when.md` 373.
- planner `tasks/diagnose.md` 47-49 and `tasks/change.md` 11-14 (what the script does to counts and statuses when
  the turn merges): DELETE; the planner's choice doesn't depend on them, and the lead's result reports them.
- planner `tasks/unblock.md` 19-22: "the script lifts the block, and the milestone waits only for any design review":
  CLAUSE.
- planner `tasks/module.md` 33-35 "When a module has one planned milestone left, the lead starts a planner":
  CLAUSE (keep "plan the next one or two milestones; later ones as headings").

### 13. The lead's own `SKILL.md`: the `next` caveat is a script gap

- `SKILL.md` 53-58: "It names the worktree of the command that printed it, so a `next` from `ready` or `status` run
  in the main working copy needs the module's own worktree put in its place. And a `next` that runs a module reuses
  the hosts of that module's latest builder run ..." The lead is told to edit the script's commands because the
  script doesn't know each module's worktree. With CLI change D (the script owns module worktrees), `next` can name
  the right worktree and this paragraph goes. The host half stays as a clause.
- `SKILL.md` 36-43: exit statuses 0/1/2, `merge`/`check`/`lock`/`wait`/`main-check` keep their own: DELETE; the
  docstring 49-59 says it, and should be in the top-level `--help` epilog. KEEP "don't send output to `/dev/null` or
  cut it with `tail`" and "`result_file` lets you read what finished while you were gone".
- `SKILL.md` 60-62: "Words added without a flag, or brackets left unquoted, are read by the shell, and zsh stops on
  them": general shell knowledge, DELETE. "Both flags can be given more than once" is in `run --message` / `plan
  --task` help.
- `SKILL.md` 76-83: file list and STATUS.md contents: CLAUSE (group 7).
- `SKILL.md` 116-118: "That command fails on purpose when the `Merge:` or `Test command:` line is missing": DELETE;
  the refusal names the line and the reason (`REQUIRED` 656).
- `stages/2-start-planning.md` 20-23: "commit the brief, the glossary and the settings with git on the main branch,
  and push them under `Merge: push`, because `adopt` never merges the settings". MOVE to `settings set` (change C)
  for the settings; for a new project, `adopt` could land the first brief and glossary too, so the lead never
  commits by hand.
- `stages/3-before-first-build.md` 22-23 links `settings.md`: becomes `settings set Builders <n> --said ...`.

### 14. General knowledge to delete

- planner `SKILL.md` 97-98: "Hold it to good testing practice: exact expected values, the edge cases the design names,
  and the same result on every run." Capable models know this; keep "the edge cases the design names" at most.
- planner `tasks/project.md` 59-61: "`pytest`, for one, fails when it finds no tests, and `pytest || [ $? -eq 5 ]`
  lets that case pass." Keep "on a new repository use a test command that passes on an empty suite".
- builder `SKILL.md` 230-231: "A script that replaces text, such as Python's `str.replace`, changes nothing and says
  nothing in that case." Keep "edit with `apply_patch`" if it matters on Codex; drop the explanation.
- lead `stages/4-build.md` 37-38: "A worktree is a second working copy of the repository" (the user's own example).
- builder `SKILL.md` 237-238: "A force-push would replace history the other worktrees rest on": keep "bring work in
  only with `merge`"; the reason is general git knowledge.

### 15. Smaller items

- builder `SKILL.md` 56-57: "Start each commit's subject with the module and milestone ... because that is how the
  script tells whose commit broke a check" — the merge queue already notes the module of each landing (6409, 14374),
  so the subject is a fallback. `merge` could stamp a trailer itself; then this goes. Low priority.
- builder `SKILL.md` 83-88: "In the done-when file you change three fields" — the build prompt goal and `binding()`
  state it each turn; CLAUSE ("change only your items' `builder_result` and `evidence`; the script rejects anything
  else").
- builder `SKILL.md` 222-228 "The script starts Codex so that each request is granted or refused automatically";
  "A command still running after 30 seconds hands control back ... `yield_time_ms`": host mechanics. Keep the
  agent's actions (ask to run a browser outside the sandbox; use `jobs`, not `ps`), cut the explanation. This text
  is a candidate for the build prompt's `{session}` line (`session_rule()` 7081), which already knows the host.
- reviewer `tasks/design.md` 53-57: "A design gets at most two reviews in a row that ask for changes, and the script
  approves the planner's answer to the second without another review". The script knows the round
  (`design_changes_in_a_row()`); put "This is design review round N of 2" in the design-review prompt and cut this to
  "put every Must Fix you find in this review".
- reviewer `tasks/design.md` 44: "If a `design-review.md` is already there" — the prompt's `{changed}`
  (`design_changes()` 2053) already names the last review and what changed; CLAUSE.
- reviewer `tasks/milestone.md` 67-70: "The script works out the rest from your verdicts and findings ... as [who
  changes what] sets out": keep "change only those fields; leave them uncommitted"; drop the link.
- reviewer `tasks/milestone.md` 75-76: "After a planner has settled one such finding, the next goes to the user":
  mechanics; CLAUSE.
- planner `SKILL.md` 153-154: "Changing only its `lock` or `reads` keeps the progress" — fine as a clause; the
  long form in `done-when.md` 225-227 goes.
- lead `stages/4-build.md` 79-82: "`runs --repo <repo> --json` lists every session in the repository, and `quota
  --worktree <path>` forecasts ..." — keep (which command when), it's a pointer.

## Prompt templates

- `reviewer/prompts/design-review.md` line 4: `{changed}{briefs}` — `review_prompt()` 9494-9496 always passes
  `briefs=""` and puts the briefs note into `context` (= `{changed}`) instead (9164-9168). Dead placeholder: remove
  `{briefs}`.
- Both review prompts lack the graded examples path and the design round number (see groups 7 and 15).
- The review prompts say "The script is `python3 {loop}`, for the `background` and `wait` commands the skill
  describes"; after group 9 they should point at `--help`.
- `builder/prompts/build.md`, `findings.md`, `planner/prompts/plan.md`: no problems found; they carry exactly the
  per-session facts and the CLI's own commands, which is the target. `findings.md` 7 (what `repeat` means) is the
  right home for that fact, so the skill copies elsewhere can go.
- `needs_rules()`, `resources_rule()`, `session_rule()`, `feedback_note()`, `checks_note()`, `scope_text()`,
  `handoff_note()` all hold text that is also in a skill (group 8). In each case the prompt copy is the better one,
  because it is filled in for this milestone and changes with the script; the skill copy is what should go.
- The design reviewer's skill says "Your prompt says where the planner's tasks are saved" (`tasks/design.md` 9), but
  that sentence is in the prompt only when the record has `briefs` (9164). Either always say it, or the skill should
  say "if your prompt names them".

## CLI changes the cleanup depends on (in order)

A. **Subcommand `description` / `epilog` for every parser** (15365-15598), built from the module docstring. Today
   `<cmd> --help` prints only flags. Every "move to `--help`" depends on this. Highest priority, low risk.
B. **A `paths` command** (or a `paths` block in `settings` output): every location resolved for the project — plans
   folder and project files, a module's files, the evidence root and layout, graded examples, references, script,
   jobs/results/reports/history folders. Lets groups 1 and 7 go from all four skills.
C. **`settings --template`** generated from `PROFILE_FIELDS`/`REQUIRED`/`ALLOWED`, with each line's meaning; the
   `settings` output showing each line's effective value, its source (file or default) and the resolved model and
   effort per role and host; and **`settings set <Label> <value> --said "<words>"`**, which writes the line, commits
   on the main branch and pushes under `Merge: push`. Lets `profile.md` and `settings.md` go, and stage 2 stop
   committing by hand.
D. **Module worktrees owned by the script**: `run --module M` with no `--worktree` makes or reuses `build/<module>` in
   an ignored folder, from the remote under `Merge: push`; the script removes it on FINISHED once nothing is
   unmerged; `next` names the module's worktree. Removes `4-build.md` 37-41, 195, 400-401 and lead `SKILL.md` 53-56.
E. **Review prompt fields**: add the graded examples path and "design review round N of 2"; drop the dead
   `{briefs}`.
F. **Better `next` fields**: MIGRATED → `plan --kind fix` with the plan-shape task (today `status`);
   FAILING_ON_MAIN → a real `plan --kind fix` command naming the commit (today `next` has no command);
   `turn_not_stopped` → a `next` with `decides: human`; a `settings` preflight warning for a missing `Graded
   examples:` line when the file exists.
G. **Diagnosis splits**: the script carries the `diagnoses` count to milestones split off in a diagnosis turn
   (a `split_from` field or inheritance), so `diagnose.md` 32-34 goes.
H. **`human --help`** describing each verb, **`ready --help` / `status --help`** with the group and status tables,
   **`lock --help`**, **`main-check --help`**, **`merge --help`** with the batch behaviour, **`history --help`** with
   where the history lives. All part of A, listed because the skill text they replace is the largest.

Estimated effect: `done-when.md` 420 → ~120 lines; `profile.md` 149 and `settings.md` 16 → 0 (a few lines move to
stage 2); `cleanup.md` 40, `older-projects.md` 86, `locks.md` 59, `delivery-history.md` 51 → 0 (about 25 lines of
judgement move into `4-build.md`); `4-build.md` 401 → ~250; builder `SKILL.md` 275 → ~190; reviewer files lose about
40 lines; planner `SKILL.md` and tasks lose about 40.
