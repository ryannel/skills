# Audit: locations, settings and defaults described in prose (`paths-settings`)

Scope: every passage in `skills/orchestration` (skills, stages, tasks, references, prompts, README, GLOSSARY, and the
prompt templates `agent_loop.py` loads from `*/prompts/`) that says where a file or folder lives, how a path is found
or overridden, what a setting is called, its default, the precedence between settings, or an environment variable.

Paths below are relative to `/Users/ryannel/Workspace/skills/skills/orchestration/`. "Script" means
`lead/scripts/agent_loop.py`. Everything was read as it is on disk on 2026-11-22; nothing was edited.

## What the CLI already knows and says

Checked before ranking, because it decides which passages can simply go.

**The script already holds every location and default in one place:**

- `PROFILE_FIELDS` (line 651), `REQUIRED`, `ALLOWED`, `ONE_WORD`, `DEFAULT_MODELS` (517), `DEFAULT_EFFORT` (523),
  `LEAD_CHECK_IN_S` (14986), `DEFAULT_HOLD_LIMIT_S` (3692), `MERGE_TEST_TIMEOUT_S` (10883), `LOG_ENTRY_LINES` (12299),
  `JOB_WAIT_S` (10435), `TOOL_CALL_LIMIT_S` (6067), `DESIGN_REVIEW_ROUNDS` (2346).
- `MODULE_FILES` / `PROJECT_FILES` (1483–1487), which carry the comment "The layout of the plans folder, defined here
  and nowhere else". Also `module_file()`, `project_file()` and `handoff_rel()` (1520).
- `EVIDENCE_DEFAULT` (1106), `evidence_root()` (1111: `<git common dir>/orchestrate/evidence`), `loop_dir()` (1089)
  and the folders under it: `verify/`, `main-checks/<name>/checkout`, `checks/`, `jobs/`, `results/`,
  `merge-queue/`, `locks.jsonl`, `usage.jsonl`, `results.jsonl`, `watch.json`, `last-runs.json` and `version.json`.
- `LOOPS_DIR` (4150: `$ORCHESTRATE_LOOPS_DIR` or `$XDG_STATE_HOME/orchestrate/loops`) and the history folder (12059:
  `~/.orchestrate/history/<project>` or `$ORCHESTRATE_HISTORY_DIR`).
- Environment variables: `ORCHESTRATE_VISIBLE`, `ORCHESTRATE_ROLE`, `ORCHESTRATE_SCRIPT` (set at 14159),
  `ORCHESTRATE_CHECK_COMMIT`/`_MODULE`, `ORCHESTRATE_JOB_EXIT`, `ORCHESTRATE_CODEX`, `ORCHESTRATE_CLAUDE`,
  `ORCHESTRATE_LOOPS_DIR`, `ORCHESTRATE_HISTORY_DIR`, `ORCHESTRATE_NO_HISTORY` and `CODEX_HOME`.
- Precedence for model and effort is coded once, in `resolve()` (6953) and `role_setting()` (730). Each launch's
  result reports what was asked for as `ran_on`.

**What the CLI prints today:**

- **`settings` (alias `profile`)**, in `cmd_settings` (10365), prints the parsed profile dict as indented JSON, plus
  `preflight` warnings. I ran it on `~/Workspace/thrum` to see the shape. It gives `plans`, `evidence`,
  `graded_examples`, `merge`, `branch`, `remote`, `test_command`, `models`, `roles`, `default_host`,
  `review_host`, `planner_host`, `builders`, `check_in_s`, `lock_hold_limit_s`, `shared_resources`,
  `main_checks`, `roots` and `bounds`. It does **not** give:
  - any absolute path: no working folder, git common dir, results, checkouts, logs, history, loops folder or script
    path;
  - any module or milestone file paths;
  - which values came from a line and which are defaults;
  - the effective model and effort for each kind of agent on each host (the lead has to apply profile.md's two
    precedence lists by hand);
  - environment variables;
  - `version` or `result`. It is not the one-line JSON result that `lead/SKILL.md:36` promises for every command.
- **`status`** (10250) prints milestone lines, warnings about stray plan files ("a plan file outside
  {prof['plans']}"), and `settings_differ`. It prints no locations otherwise.
- **`ready`** prints `settings_differ` (`profile_note`, 3550) and `unmerged_plans`. Any command that uses `emit()`
  carries `settings_read_from` when the working copy's settings are only behind the tip (`settings_at_tip`, 913).
- **Prompts already give each session its own paths.** `BUILD_TEMPLATE` gives `{done}`, `{captures}`
  (`<evidence>/<MODULE>/<milestone>`), `{handoff}`, `{glossary}` and `{loop}`. `REVIEW_TEMPLATE` and
  `DESIGN_REVIEW_TEMPLATE` give `{review}`, `{captures}`, `{done}`, `{glossary}` and `{loop}`. `FINDINGS_TEMPLATE`
  gives `{evidence}/{module}/{milestone}-review.md`. The reviewer prompt does **not** name the graded examples file
  or the module's folder. The builder prompt does not name the module's folder, `DESIGN.md` or `PLAN.md`.
- **`cleanup --help`** already lists every kind with the same wording as `lead/references/cleanup.md`'s table. Its
  result already carries `next` with `decides: human` and an `ask`.

**Problems in the CLI found along the way:**

1. **`settings` reads a different file from the commands that act on it.** `cmd_settings` calls
   `profile(..., old_ok=True)`, and `old_ok` skips `settings_at_tip` (line 801). So `settings` prints the working
   copy's file, while `run`, `review`, `plan` and `merge` read the main branch's when the copy is only behind it.
   `lead/SKILL.md:116` tells the lead to run `settings` "to confirm the script can read it". In a stale worktree it
   confirms the wrong copy, and it never prints `settings_read_from`, because that goes through `EMIT_EXTRA` and
   `cmd_settings` doesn't call `emit()`. So `lead/references/settings.md:10-11` ("its result says so in
   `settings_read_from`") is not true of `settings` itself.
2. **`settings --help` points at text that doesn't exist.** It reads "also check that host's loader (default: see
   above)", but the subparser has no description, so there is nothing above it.
3. **The key names in `settings` are inconsistent.** `"exclusive resources"` keeps its space because it is never
   renamed out of `PROFILE_FIELDS`, while every other key is snake_case. `models` mixes built-in defaults with the
   user's lines without saying which is which, so `codex: gpt-6.2-sol` looks like a choice the user made.

## Findings, ranked by size of win

### A. One fix, "the CLI reports locations": every passage that spells out where files live

All of these give the same few facts by hand: the plans folder (`docs/plans` unless `Plans:` names another), the
module files, the working folder (`.orchestrate/evidence`, linked to `<git common dir>/orchestrate/evidence`), the
handoff and review paths, and the graded examples file. The script defines each of these once. These passages can
shrink to a pointer once a command prints them (section "The CLI side" below), and many already can, because the
prompts give the paths.

| # | File:lines | Quote | What it does | Where it goes | CLI already covers? |
|---|---|---|---|---|---|
| A1 | `planner/references/done-when.md:20-50` | "The plans folder is `docs/plans` unless the project settings name another." | A path tree with defaults, the evidence link mechanism, and why evidence isn't committed | Keep the table of what each file is for and who writes it, since that is the planner's craft. Replace the tree's literal folders and the evidence-link mechanics (47-50) with "`settings` prints where each is" | Partly: `MODULE_FILES`, `EVIDENCE_DEFAULT`, `evidence_root`. Not printed by any command yet |
| A2 | `planner/SKILL.md:18-36` | "The settings' `Plans:` and `Evidence:` lines can move the two folders:" | A second copy of the same tree | Delete. Keep one sentence naming the files' roles, and link done-when.md | Same as A1 |
| A3 | `builder/SKILL.md:51-56` | "It goes in the working folder, at `<evidence>/<MODULE>/<milestone>/`, where `<evidence>` is the settings' `Evidence:` path (`.orchestrate/evidence` unless they name another)." | Path, default, and the link mechanism | Command output. The prompt gives `{captures}`. Keep "leave evidence uncommitted; `merge` refuses a commit under it", which is the behaviour the builder must act on | Yes, for script-started builders (`BUILD_TEMPLATE` `{captures}`). `merge` refuses evidence commits (`evidence_in_commits`, 1220) |
| A4 | `builder/SKILL.md:76` | "first write a handoff at `<evidence>/<MODULE>/<milestone>-handoff.md`" | Path | Prompt or command output | Yes: `{handoff}` in `BUILD_TEMPLATE`, from `handoff_rel()` |
| A5 | `builder/SKILL.md:30-31`, `reviewer/SKILL.md:39-41` | "The module's files are in `<plans folder>/<MODULE>/`." | Module folder layout | Command output, and add `{module_dir}` to the build and review prompts | No: neither prompt names the module folder |
| A6 | `builder/SKILL.md:139-140` | "link evidence by its path from the repository's root, such as `.orchestrate/evidence/WATER/M2/run.log`" | A default path as an example | Keep the rule (repository-relative links). Use `{captures}` as the example | Yes: `{captures}` is already repository-relative |
| A7 | `builder/SKILL.md:61-62` | "put longer notes in `<evidence>/<MODULE>/` and link them" | Path | Pointer to the `settings` output, or `{captures}` | Partly |
| A8 | `reviewer/SKILL.md:25-33` | "the settings' `Evidence:` path, `.orchestrate/evidence` unless they name another." | Path, default, link mechanism, graded examples path and its default | Prompt: add `{graded_examples}` to `REVIEW_TEMPLATE` and `DESIGN_REVIEW_TEMPLATE`. Keep "graded examples are the best guide to strictness", which is judgement | Partly: `prof["graded_examples"]` is computed (884-888) but not sent to reviewers |
| A9 | `reviewer/SKILL.md:72-73` | "Link files in the working folder or on the main branch, so the link opens from any worktree." | Rule plus location | Keep the rule. It is short | n/a |
| A10 | `lead/SKILL.md:76-83` | "Everything else is in the plans folder, `docs/plans` unless the settings name another" | Paths and file names | Shrink to "`settings` prints where the plans, status page and module files are". Keep "STATUS.md is the user's page; the script rewrites it" (the lead's working knowledge) | Partly |
| A11 | `planner/references/done-when.md:114, 134, 161` | "[review](../../../.orchestrate/evidence/<MODULE>/M1-review.md)" | Hard-coded default evidence path in an example and two rules | Write `<evidence>/<MODULE>/`, or "the working folder `settings` names". This also breaks silently for a project with a non-default `Evidence:` | No |
| A12 | `lead/references/cleanup.md:5-18` | "The working folder, `<git common dir>/orchestrate/evidence/`, holds builders' proof…" | Lists every on-disk location the build keeps | Command output (`cleanup` already lists them by kind and size; `settings` should list the folders). Delete the section | Mostly: `cleanup` result and `CLEANUP_KINDS` |
| A13 | `lead/references/delivery-history.md:19-23` | "`~/.orchestrate/history/<repository>-<hash>/`, or under `$ORCHESTRATE_HISTORY_DIR` when that is set." | Path, default and environment override | `settings` output (`machine.history`), and the `history --json` result should name its folder | No: neither prints the folder |
| A14 | `lead/references/report.md:13-15` | "`--write` saves it under the repository's git folder, where no commit picks it up, and prints the path." | Location | `report --help`. Delete it here (the path is printed) | Yes: prints the path |
| A15 | `lead/references/older-projects.md:18-19, 24-25, 32, 76, 82-83` | "the settings, `docs/evidence` by default." | Old and new default paths | Mostly keep: this is history for a lead meeting a refusal, and `migrate`'s output reports what it moved. Lines 76 and 82-83 could go to the `migrate` result | Partly: the `MIGRATED` result carries `evidence` and `plans` |
| A16 | `GLOSSARY.md:228-229, 239, 318, 379, 463, 488, 586` | "Stored as: `<git common dir>/orchestrate/evidence/` … (`.orchestrate/evidence` by default)" | "Stored as" paths for each name | Keep, since the glossary's job is to say where each name lives. But drop the defaults and say "(see `settings`)" so it doesn't go stale. Low priority | n/a |
| A17 | `README.md:179-188, 481-482, 568-570, 618-619, 174` | "Every project keeps its plans in the same place, `docs/plans/`" | Paths for people | Keep for people, but name defaults as defaults and point at `settings`. Low priority, since no agent acts on the README | n/a |

**Size of the win:** about 70 lines across six skill files, plus two whole sections (done-when.md's tree and
cleanup.md's "What stays"). This needs three things:

- `{module_dir}` and `{graded_examples}` added to the prompts. This is small: both values are already computed.
- A `settings` (or `paths`) output that names the folders, for the cases with no prompt: a builder without a lead, and
  the lead.
- A rule that skills write `<evidence>` and `<plans>`, never the default strings.

### B. The settings reference, `planner/references/profile.md` (149 lines): split into a template the CLI prints and a short judgement section

| # | Lines | Quote | What it does | Where it goes | CLI already covers? |
|---|---|---|---|---|---|
| B1 | 7-13 | "It takes everything after the label as the value, so keep each of those lines in the shape `- **Label:** value`" | How the parser reads lines, and which lines are required | `settings --help` and the `settings --template` output. The refusal message already names the missing lines | Yes: `profile()` raises "ORCHESTRATE.md has missing, unfilled or invalid fields: …" naming `REQUIRED`'s reasons |
| B2 | 22-73 (the template block) | "- **Lead check-in:** 3h  *(script: optional; … left out, 3 hours)*" | 28 script-read lines, each with its default, allowed values and parsing notes in a `*( )*` note | **`settings --template`**, generated from a schema table in the script (label → default, allowed values, required, one-line help). Keep in the skill only the prose sections the lead and planner fill in by judgement: purpose, quality bar, references, starting from a clean clone, targets, rules, project guidance | Partly: `PROFILE_FIELDS`, `REQUIRED`, `ALLOWED` and `ONE_WORD` hold defaults and values but no help text. `role_lines`, `builders_count`, `lock_settings_from` and `main_check_lines` hold the rest |
| B3 | 84-86 | "The script runs `Setup command` again in a checkout only when a tracked manifest or lockfile there has changed" | Script behaviour | `settings --template` help text for `Setup command`. Keep "prefer `npm ci`" as the planner's guidance (one line) | Behaviour in `SETUP_FILES` (5035), undocumented in `--help` |
| B4 | 93-104 | "`Review host` says where a review runs when the lead names no host: `same` … `other` … A host name" | Allowed values and their meaning | Template help. Keep one sentence of judgement: "write `other` when the user builds with both hosts, because a reviewer from another company shares fewer blind spots". That sentence is also in `4-build.md:175-178` (duplicate) | Values validated in `profile()` (861-865) and resolved in `review_host()` |
| B5 | 112-147 | "For each launch, the script takes the first of these that is set. For the model: 1. `--model` on the command; 2. …" | Two precedence lists, the design-reviewer fallback, and four example lines | **Command output**: `settings` prints the effective model and effort for every role × host, with the source of each. Keep two sentences: a model line names its host, because a model belongs to one host; and the forms, by example | Yes, in code: `resolve()` 6953, `role_setting()` 730, `ROLE_FALLBACK`. Not printed by any command except `ran_on` after a launch |
| B6 | 77-82 | "Leave out each host or model line the user said nothing about. The script then uses the host it runs inside and each host's default model" | Default behaviour plus judgement | Keep the judgement ("leave lines out unless the user named them, so new models arrive by themselves"). The default itself goes in the output | Yes: `default_host()` 5861, `DEFAULT_MODELS` |
| B7 | 88-91, 106-110 | "`Merge: push` is standing permission…"; "This file holds settings, not progress." | Judgement and permissions | **Keep.** It is the agent's call what to write, and why | n/a |
| B8 | 149 | "A larger model or a higher effort spends the user's quota faster." | Judgement | Keep | n/a |

**Size of the win:** profile.md drops from 149 lines to about 40, keeping the judgement (who writes which line,
`Merge: push` as permission, leave model lines out, `Review host: other`, settings aren't status) and the prose
sections. It needs a schema table in the script, `settings --template` and effective-value output. That is new script
work, but small: about 30 labels, most of which already have entries in `PROFILE_FIELDS`.

### C. `lead/references/settings.md` (16 lines): the whole file can go

| # | Lines | Quote | What it does | Where it goes | CLI already covers? |
|---|---|---|---|---|---|
| C1 | 3-5 | "The lead writes a line in `ORCHESTRATE.md` when the user asks for one" | Pointer plus judgement | One sentence in `lead/SKILL.md`: "you write the settings lines the user asks for; `settings set` commits them" | n/a |
| C2 | 7-8 | "`adopt` won't merge a changed `ORCHESTRATE.md` … So commit it with git in the main working copy, on the main branch, and push it when the settings say `Merge: push`." | A git procedure the script could carry out | **Script behaviour**: `settings set '<Label>' '<value>' --text '<the user's words>' --worktree <repo>` edits the line, validates it with `profile()`, commits on the main branch and pushes under `Merge: push`. It records the user's words the way `human` does, then prints the effective settings. The `adopt` refusal's message should name this command | Partly: `adoptable()` (12214) refuses with "the lead commits and merges it with git", but offers no command. The script already edits settings lines in `migrate` (`set_setting_line`, around 13356) |
| C3 | 10-12 | "A worktree or module branch whose copy is only behind the main branch's then runs on the main branch's settings, and its result says so in `settings_read_from`." | Describes script behaviour and output fields | Delete. The fields explain themselves, and `settings` should print `read_from` (finding 1) | Yes, for `emit()` commands. Not for `settings` itself (bug) |
| C4 | 14-16 | "Each result's `ran_on` says what the script asked the host for … Check `ran_on` in the next result before you tell the user a change has taken effect." | Output fields, plus a rule | The rule is the lead's judgement; keep one line in 4-build.md's `WRONG_MODEL_OR_EFFORT` row. Better: `settings set`'s result says "takes effect from the next launch; the next result's `ran_on` confirms it" | Yes: `ran_on`, `WRONG_MODEL_OR_EFFORT` |

**Also delete the pointers to settings.md:** `lead/stages/4-build.md:33`, `4-build.md:66`,
`3-before-first-build.md:22-23` and `older-projects.md:85-86` ("A settings change is committed with git on the main
branch, as the lead skill says"). Each becomes "run `settings set …`". `2-start-planning.md:20-23` (commit the first
settings with git and push) stays as it is for a new project, or `settings set` can also create the first file.

### D. Worktree locations and creation (`lead/stages/4-build.md:37-41`)

| # | Lines | Quote | What it does | Where it goes | CLI already covers? |
|---|---|---|---|---|---|
| D1 | 4-build.md:37-41 | "If the repository ignores no folder, add one to `.git/info/exclude`. With `Merge: push`, branch from the remote: `git worktree add -b build/<module> <folder>/<module> <remote>/<branch>`." | Teaches worktrees (general knowledge), picks a folder and branch name, and has the base depend on `Merge` | **Script behaviour.** `run --module <M>` with no `--worktree` (or `--worktree auto`) creates or reuses `<builds folder>/<MODULE>` on `build/<module>`, from `Remote/Branch` or `Branch` by `Merge`. It excludes the folder through `info/exclude`, which the script already does for the evidence link (`exclude_path`, around 1173). A `Worktrees:` settings line (default e.g. `.orchestrate/worktrees`) overrides the folder, and `settings` prints it. Delete the passage | No. The script makes only its own detached checkouts (`verify_tree` 4655, `main_check_tree`). It already writes `info/exclude` and fast-forwards a clean worktree (`sync_worktree` 1303) |
| D2 | `lead/SKILL.md:54-56` | "a `next` from `ready` or `status` run in the main working copy needs the module's own worktree put in its place" | Describes a gap in `next` | Goes away with D1: `next` names the module's worktree (or none, when `run` makes it) | No |
| D3 | 4-build.md:195, 400-401 | "`FINISHED` … Remove its worktree once nothing is unmerged."; "remove build outputs and the worktrees whose work is merged" | Procedure | Script behaviour: `run`, on `FINISHED`, removes the worktree it created once merged (as `drop_tree` does for its own checkouts), or `cleanup --kind worktrees` lists them | Partly: `drop_tree` handles the script's checkouts only |
| D4 | 4-build.md:267-268 | "Every worktree keeps its own build outputs, so a long build can fill the disk. Clear those in worktrees nothing is using." | Procedure | `cleanup` kind `build-outputs` for script-made worktrees, or keep as the lead's judgement. `watch` already reports the disk | Partly: `watch_summary` reports disk |

**Size of the win:** six skill lines, the worktree tutorial the user named, and the "put the worktree in its place"
caveat. Medium script work, mostly reusing existing pieces.

### E. Defaults restated in prose (one-liners, but each goes stale independently)

Each states a number or default the script holds as a constant. The fix is the same for all: say "the settings'
`<Label>` line (`settings` prints the value in force)", or drop the number where the result carries it.

| # | File:line | Quote | Script constant | Note |
|---|---|---|---|---|
| E1 | `lead/stages/4-build.md:26-28` | "or medium effort (high for planners) when they name none" | `DEFAULT_EFFORT`, `resolve()` | Keep the judgement "pass `--model`/`--effort` only when the user asked for that one command". Drop the defaults |
| E2 | `lead/stages/4-build.md:62` | "every three hours unless the settings' `Lead check-in:` line says otherwise" | `LEAD_CHECK_IN_S` | The `watch` result could carry `next_check_in_s`. Drop the number |
| E3 | `lead/references/locks.md:17-19` | "`Lock hold limit`, 30 minutes unless they say otherwise … it keeps its own limit of an hour" | `DEFAULT_HOLD_LIMIT_S`, `MERGE_TEST_TIMEOUT_S` | Matches today. `settings` output and `lock --help` should carry it |
| E4 | `builder/SKILL.md:197` | "`Lock hold limit` (30 minutes by default), with exit code 124" | as E3 | Keep "split long work"; drop the number. 124 is correct (3665, 4006) and belongs in `lock --help` |
| E5 | `planner/references/proofs.md:70-72` | "The lock hold limit doesn't stop the test command, which runs for up to an hour" | `MERGE_TEST_TIMEOUT_S` | The planner's reasoning about merge throughput is judgement: keep it, and soften "an hour" to "its own limit" |
| E6 | `README.md:29-31, 386-392` | "Codex `gpt-6.2-sol` or Opus 5.5, medium" | `DEFAULT_MODELS` | For people. Will go stale at the next default bump. Say "each host's default model (`settings` shows it)" |
| E7 | `builder/SKILL.md:204`, `reviewer/SKILL.md` "Keeping your session small" | "or after nine minutes" | `JOB_WAIT_S = 540` | `wait --help` and the `wait` result already say it. Drop the number |
| E8 | `builder/SKILL.md:61-62`, `done-when.md:161-162` | "up to eight lines" / "an entry of more than eight lines" | `LOG_ENTRY_LINES` | `plan` and `adopt` refuse with the number. Keep "a few lines"; the refusal teaches the limit |
| E9 | `4-build.md:204-205` | "a non-shell tool call stayed open for 15 minutes" | `TOOL_CALL_LIMIT_S` | `stopped_turn` should carry the reason text. Drop it from the skill |
| E10 | `4-build.md:247-248` | "After two in a row, the script approves the planner's next revision without another." | `DESIGN_REVIEW_ROUNDS = 2` | The `next.why` already says "2 design reviews in a row …". Can go |
| E11 | `lead/references/report.md:11-12` | "By default it covers the time since the last report that is at least an hour old, or the last 24 hours" | `REPORT_REPEAT_S`, `REPORT_DEFAULT_H` | `report --help` |

### F. Environment variables in prose

| # | File:lines | Variable | What it does | Where it goes | CLI covers? |
|---|---|---|---|---|---|
| F1 | `4-build.md:264-265, 274` | `ORCHESTRATE_VISIBLE=1` | Describes visible sessions and says `next` adds it | Keep one sentence (the lead must tell the user sessions can show in the apps, and offer it for `needs_access`). Drop "(the same command with `ORCHESTRATE_VISIBLE=1`)", because `next` already carries it (3096, 9227) | Yes |
| F2 | `builder/SKILL.md:152`, `proofs.md:92` | `python3 "$ORCHESTRATE_SCRIPT" main-check <name>` | The form an item's check takes | **Keep.** It is the literal text a planner writes into `DONE.json`, and the script sets the variable (14159) | Yes |
| F3 | `delivery-history.md:20` | `ORCHESTRATE_HISTORY_DIR` | Override | `settings` → `machine.history` with `env` source | No |
| F4 | `README.md:578, 607-619` | `ORCHESTRATE_ROLE`, `ORCHESTRATE_VISIBLE`, `ORCHESTRATE_LOOPS_DIR` | For people | Keep (README) | n/a |
| F5 | none | `ORCHESTRATE_CODEX`, `ORCHESTRATE_CLAUDE`, `ORCHESTRATE_NO_HISTORY`, `CODEX_HOME` | Not documented in any skill | Fine as they are; list them in `settings` → `env` so they are discoverable without prose | n/a |

### G. Duplicated settings guidance across stages (small, but these are the passages that drift)

- `4-build.md:30-33` and `2-start-planning.md:36-38` say the same thing twice: "plan with Fable" becomes a settings
  line, with a link to profile.md. Keep one, in 4-build, as a pointer to `settings set`.
- `4-build.md:175-178` and `profile.md:100-101` both give the `Review host: other` judgement. Keep it once, in
  profile.md's short judgement section.
- `lead/SKILL.md:116-118` ("run `settings --worktree <repo>` to confirm the script can read it. That command fails on
  purpose when the `Merge:` or `Test command:` line is missing"). The second sentence is the refusal's own text.
  Keep "run `settings` first", and drop the rest once `settings` is a proper result with `problems` and `next`.
- `3-before-first-build.md:3-4` and `2-start-planning.md:17-18` ("`run` starts no builder until it has one"). `run`'s
  refusal says this. Keep once, as the reason the lead writes the line.
- `planner/tasks/project.md:52-61` (the planner adds `Test command`/`Setup command`, with the pytest exit-5 tip).
  **Keep.** This is the planner's job and craft. The script-read details (required, `none`) can point to
  `settings --template`.

## The CLI side

### What the settings file should be

**Keep `ORCHESTRATE.md` as one Markdown file, and keep the `- **Label:** value` lines. Don't add a machine-readable
block or a second file.** The reasons:

- **The prose is the stale part, not the format.** Every drift risk found above comes from prose that restates the
  parser's defaults and rules. The bullet format is parsed reliably (`profile_value`, 666) and is what Thrum and
  every planned project already have.
- **Several lines are deliberately the user's words, not values.** `Builders: two Codex builders` is read "as a
  person would" (`builders_count`), and `Human decides` and `Licences and paths not to touch` are sent verbatim on
  resumed turns. A TOML or YAML block would force these into quoted strings, or split them from their meaning.
- **A split file would not remove the prose sections** that agents must read (purpose, quality bar, clean clone,
  targets, guidance). It would only add a second file that every agent is told to read, and a migration.

What should change in the file:

1. **Group the script-read lines under one heading**, e.g. `## Settings the script reads`, separate from the
   judgement lines (`Purpose`, `Quality bar`, `References`) and the prose sections. The `*(script: …)*` notes then
   become unnecessary, and the per-line notes stop carrying defaults that drift. The parser needs no change, because
   it searches the whole file by label.
2. **Move the schema into the script:** one table of label → key, default, allowed values, required, one-line help.
   `PROFILE_FIELDS`, `REQUIRED`, `ALLOWED` and `ONE_WORD` merge into it, plus entries for the pattern lines
   (`<Host> model`, `<Host> <kind>`, `Host <name>`, `Main-branch check <name>`, `Shared resources`). The template,
   the `settings` output and `--help` are all generated from that table, so a new setting is documented where it is
   added.

### The command: make `settings` the one place an agent asks "where is everything, and what is in force"

Extend `settings` rather than add a new command, because the lead skill already sends every lead to it first. Add
`paths` as an alias if a short name for builders helps. The changes:

- **Print a proper result.** One JSON line, `"result": "SETTINGS"` (or `REFUSED` with `problems` and `next`), with
  `version`. Read the settings the way `run` does, through `settings_at_tip`, which fixes finding 1, and say which
  copy was read in `read_from`.
- **Report each value with its source:** `line`, `default`, `main-branch tip` or `env`.
- **Report the effective launch table**: role × host → model and effort, each with its source, computed by calling
  `resolve()`/`role_setting()`. It also shows the effective review host and planner host.
- **Report locations, absolute and repository-relative:** the settings file, the plans folder and each project file,
  the working folder (both its link path and its real folder), graded examples, references, and the script's
  machine folders.
- **`--module M [--milestone id]`** adds that module's and milestone's paths (done-when, plan, design, log, record,
  evidence folder, captures, handoff, review), for a builder or reviewer working without a prompt, and for the lead.
- **Report environment variables:** the ones the script reads, whether set, and what each changes.
- **`settings --template`** prints the template generated from the schema, with every default.
- **`settings --explain <Label>`** prints one line's help, allowed values and default.
- **`settings set '<Label>' '<value>' --text '<the user's words>'`** validates the line, writes it, commits it on the
  main branch and pushes under `Merge: push`. It saves the user's words and prints the new effective value. This
  replaces `lead/references/settings.md`. Like `human`, it refuses where `ORCHESTRATE_ROLE` is set, because the
  settings carry the user's permissions.

**Sketch of `settings --worktree ~/Workspace/thrum --module ENGINE --milestone M4`** (pretty-printed here; printed as
one line):

```json
{
  "result": "SETTINGS",
  "version": "2.9.0",
  "read_from": {"file": "ORCHESTRATE.md", "ref": "origin/main", "why": "this worktree's copy is behind origin/main"},
  "settings": {
    "merge":            {"value": "push", "source": "line", "means": "rebase onto origin/main and push without force"},
    "test_command":     {"value": "./dev check", "source": "line", "lock": null, "timeout_s": 3600},
    "setup_command":    {"value": null, "source": "default"},
    "branch":           {"value": "main", "source": "default"},
    "remote":           {"value": "origin", "source": "default"},
    "builders":         {"value": 2, "source": "line", "said": "two Codex builders"},
    "lead_check_in_s":  {"value": 10800, "source": "default"},
    "lock_hold_limit_s":{"value": 1800, "source": "default"},
    "codex_sandbox":    {"value": "danger-full-access", "source": "line"},
    "claude_permissions":{"value": "auto", "source": "default"},
    "writable_roots":   {"value": ["~/.cargo"], "source": "line"},
    "exclusive_resources": {"value": ["simulator"], "source": "line"},
    "shared_resources": {"value": {"gpu": 2, "chrome": 1}, "source": "line"},
    "main_checks":      {"exact-images": {"every_s": 14400, "locks": ["chrome", "gpu"], "timeout_s": 2700}, "...": "..."}
  },
  "launch": {
    "default_host": {"value": "codex", "source": "line"},
    "review_host":  {"value": "codex", "source": "line"},
    "planner_host": {"value": "claude", "source": "line"},
    "roles": {
      "plan":   {"claude": {"model": "claude-fable-5-2", "effort": "high", "source": "Claude planner line"},
                 "codex":  {"model": "gpt-6.2-sol", "effort": "high", "source": "built-in default; planners default to high"}},
      "build":  {"codex":  {"model": "gpt-6.2-sol", "effort": "medium", "source": "built-in default"},
                 "claude": {"model": "claude-opus-5-5", "effort": "medium", "source": "built-in default"}},
      "review": {"codex":  {"model": "gpt-6.2-astra", "effort": "medium", "source": "Codex reviewer line"},
                 "claude": {"model": "claude-opus-5-5", "effort": "high", "source": "Claude reviewer line"}},
      "design": {"codex":  {"model": "gpt-6.2-astra", "effort": "high", "source": "Codex design reviewer line"},
                 "claude": {"model": "claude-opus-5-5", "effort": "high", "source": "Claude reviewer line (design reviewers fall back to reviewers)"}}
    }
  },
  "paths": {
    "settings": "ORCHESTRATE.md",
    "plans": {"value": "docs/plans", "source": "default"},
    "brief": "docs/plans/BRIEF.md", "glossary": "docs/plans/GLOSSARY.md",
    "architecture": "docs/plans/ARCHITECTURE.md", "status": "docs/plans/STATUS.md",
    "evidence": {"value": ".orchestrate/evidence", "source": "default",
                 "folder": "/Users/…/thrum/.git/orchestrate/evidence", "committed": false},
    "graded_examples": {"value": ".orchestrate/evidence/GRADED-EXAMPLES.md", "source": "line", "gains_overturned_reviews": true},
    "references": null,
    "builder_worktrees": {"value": ".orchestrate/worktrees", "source": "default"},
    "module": {"name": "ENGINE", "folder": "docs/plans/ENGINE",
               "design": "docs/plans/ENGINE/DESIGN.md", "plan": "docs/plans/ENGINE/PLAN.md",
               "log": "docs/plans/ENGINE/LOG.md", "done": "docs/plans/ENGINE/DONE.json",
               "record": "docs/plans/ENGINE/RECORD.json", "evidence": ".orchestrate/evidence/ENGINE",
               "worktree": "/Users/…/thrum/.orchestrate/worktrees/ENGINE", "branch": "build/engine"},
    "milestone": {"id": "M4", "captures": ".orchestrate/evidence/ENGINE/M4",
                  "handoff": ".orchestrate/evidence/ENGINE/M4-handoff.md",
                  "review": ".orchestrate/evidence/ENGINE/M4-review.md"}
  },
  "machine": {
    "script": "/Users/…/lead/scripts/agent_loop.py",
    "git_common_dir": "/Users/…/thrum/.git",
    "orchestrate_folder": "/Users/…/thrum/.git/orchestrate",
    "results": "/Users/…/thrum/.git/orchestrate/results",
    "checkouts": ["…/orchestrate/verify", "…/orchestrate/main-checks/<name>/checkout"],
    "logs": ["…/orchestrate/checks", "…/orchestrate/jobs", "…/orchestrate/main-checks/<name>"],
    "history": {"value": "~/.orchestrate/history/thrum-1a2b3c", "source": "default", "env": "ORCHESTRATE_HISTORY_DIR"},
    "runs": {"value": "~/.local/state/orchestrate/loops", "source": "default", "env": "ORCHESTRATE_LOOPS_DIR"}
  },
  "env": {
    "ORCHESTRATE_VISIBLE": {"set": false, "means": "show sessions in the Codex app and Claude desktop"},
    "ORCHESTRATE_ROLE":    {"set": false, "means": "set in every session the script starts; `human`, `cleanup` and `settings set` refuse under it"},
    "ORCHESTRATE_NO_HISTORY": {"set": false}, "ORCHESTRATE_CODEX": {"set": false}, "ORCHESTRATE_CLAUDE": {"set": false}
  },
  "problems": [],
  "preflight": {"host": "codex", "warnings": []}
}
```

(`builder_worktrees`, `module.worktree` and `module.branch` assume finding D1's change. Without it, drop them.)

Also add to the prompts, so that sessions the script starts never need the command:

- `{module_dir}` in `BUILD_TEMPLATE`, `REVIEW_TEMPLATE` and `DESIGN_REVIEW_TEMPLATE`;
- `{graded_examples}` in both review templates.

### Passages the command (and `settings set`, `--template`, the prompt fields) would let us delete or shrink

Whole files or sections:

- `lead/references/settings.md`: the whole file (16 lines). Needs `settings set`, and `read_from` in `settings`.
- `planner/references/profile.md:7-13, 22-73` (the script-read lines and their notes), `84-86`, `93-99` and
  `112-147`: about 100 of 149 lines. Needs the schema, `--template` and the `launch` table.
- `lead/references/cleanup.md:5-18`, "What stays on the computer" (14 lines). Needs `paths`/`machine` in `settings`
  (`cleanup` already lists the kinds).
- `planner/SKILL.md:18-36`, the second copy of the tree (19 lines).
- `planner/references/done-when.md:20-50`: shrink the tree and the evidence mechanics (about 20 lines), keeping the
  file-roles table.

Passages:

- Worktrees: `lead/stages/4-build.md:37-41` and `lead/SKILL.md:54-56`. Needs `run` to make the worktree (D1).
- Evidence and handoff paths: `builder/SKILL.md:51-54, 61-62, 76, 139-140`, `reviewer/SKILL.md:25-33, 39-41` and
  `builder/SKILL.md:30-31`. Needs `{module_dir}` and `{graded_examples}` in the prompts, and `settings --module`.
- The plans folder: `lead/SKILL.md:76-80`.
- Default evidence paths: `done-when.md:114, 134, 161`.
- The history path: `delivery-history.md:19-21`.
- Settings pointers and duplicates: `4-build.md:26-33, 66, 175-178`, `2-start-planning.md:36-38`,
  `3-before-first-build.md:22-23`, `older-projects.md:85-86` and `lead/SKILL.md:117-118`.
- Defaults: `4-build.md:62, 204-205, 247-248, 274`, `locks.md:17-19`, `builder/SKILL.md:197, 204`, `report.md:11-15`
  and `proofs.md:71-72` (number only).

Keep: `$ORCHESTRATE_SCRIPT` in check commands, `Merge: push` as permission, "leave model lines out", `Review host:
other` and why, "settings aren't status", the planner's test-command craft (`tasks/project.md:52-61`), and the
README and GLOSSARY "Stored as" lines (for people; drop their defaults only).

## CLI changes the findings depend on, in the order they unlock deletions

1. **Fix `settings`, so the rest can lean on it.** Read through `settings_at_tip`, print `read_from`, print one JSON
   result line with `result` and `version`, give the `--help` a description, and make keys consistently snake_case.
   Small. It unlocks C3 and G's `lead/SKILL.md:117-118`.
2. **Add `{module_dir}` and `{graded_examples}` to the build and review prompts.** Trivial, because both values are
   computed already. It unlocks A3–A8.
3. **Add a settings schema table, `settings --template` and `--explain`, and source-tagged values plus the effective
   `launch` table in the output.** Medium. It unlocks B1–B6 and E1–E5, which is most of profile.md.
4. **Add `paths` and `machine` (and `--module`/`--milestone`) to the `settings` output.** Small to medium. It unlocks
   A1, A2, A10–A13, F3 and cleanup.md's first section.
5. **Add `settings set '<Label>' '<value>' --text '<the user's words>'`.** Medium: it reuses `set_setting_line` and
   the landing code. `adopt`'s refusal should name it. It unlocks all of settings.md and the stage pointers.
6. **Have `run` create and reuse the module's worktree**, with a `Worktrees:` line whose default is in the schema, and
   remove it on `FINISHED`. Medium. It unlocks D1–D3 and the `next` worktree caveat.
7. **Add `next_check_in_s` to the `watch` result, and a reason to `stopped_turn`.** Small. It unlocks E2 and E9.
