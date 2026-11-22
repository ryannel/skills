# Structure audit: does each file earn its place?

Scope: the four orchestrate skills, plus README and GLOSSARY. Read-only, from the files on disk on 2026-11-22.
Line counts are `wc -l`. Verdicts: **stay**, **shrink** (to roughly N lines), **merge into X**, **CLI** (becomes a
command's `--help`, output or behaviour), **go**.

The principle applied: a skill holds what the tool is, which command to reach for when, and the agent's own
judgement (what to decide, what to ask the user, why). The CLI holds how it works: paths, defaults, overrides,
mechanics, procedures the script can carry out itself.

Current size, prose only (no scripts):

| Skill | Files | Lines now | Target | Cut |
|---|---|---|---|---|
| lead | SKILL.md, 4 stages, 6 references | 1,057 | ~400 | ~62% |
| planner | SKILL.md, 7 tasks, 3 references, 1 prompt | 1,282 | ~760 | ~40% |
| builder | SKILL.md, 2 prompts | 295 | ~185 | ~37% |
| reviewer | SKILL.md, 2 tasks, 1 reference, 2 prompts | 343 | ~300 | ~12% |
| README / GLOSSARY | 2 | 1,285 | ~1,150 (absorbs moved material) | — |

The lead is the bloated one, as the user said: 6 of its 11 files are reference material whose substance is either
already in a command's output or belongs in its `--help`, and its build stage (401 lines) is about half mechanics.
The planner's bloat is concentrated in one file, `done-when.md` (420 lines), which is mostly a description of the
script's state machine that no planner acts on.

---

## 1. Lead (start here)

### File-by-file verdicts

| File | Lines | Verdict | Why |
|---|---|---|---|
| `SKILL.md` | 126 | **shrink to ~65** | Keep role, mandate, the three things that aren't the lead's, the stage router. Lines 36-68 (exit codes, `next` mechanics, quoting, `argv`, worktree substitution) are the CLI's result contract and go to the top-level `--help`. Lines 70-83 (the file layout) go to a `paths` command. Lines 116-118 (`settings` fails on missing lines) are the command's own refusal. Lines 125-126 (migrate) go: the refusal already prints the `migrate` command (agent_loop.py:1206, 1617). |
| `stages/1-interview.md` | 161 | **stay, trim to ~140** | Almost all judgement: what only the user knows, research first, dialogue mapping, pre-mortem, fresh-reader check, brief template. Drop the contents list (8-15); it is a short file read whole. |
| `stages/2-start-planning.md` | 41 | **shrink to ~18** | Keep: write the user's choices into the settings (asking in their words), plan with `--one-step` so the user corrects before review, change of mind → brief + `plan --kind change`. Go to CLI: writing `ORCHESTRATE.md` from the template (→ `settings init`), the commit-on-main-and-push procedure (lines 20-23 → `settings init`/`settings set` commit it, `adopt` already commits the brief). Lines 36-38 duplicate 4-build 30-33 and settings.md: go. |
| `stages/3-before-first-build.md` | 30 | **stay, ~22** | Judgement: show the plan in plain words, assumptions, references, proposed names; suggest clearing context. Lines 22-23 (write and commit `Builders:`) become one `settings set Builders` call. |
| `stages/4-build.md` | 401 | **shrink to ~170** | Section breakdown below. About half is mechanics already in outputs (`next`, `stopped_because`, `escalation`, `ready` groups) or belonging in `--help`. |
| `references/cleanup.md` | 40 | **go → `cleanup --help` + output** | `cleanup --help` already lists every kind (checked). The output already carries the question in `next`. The one judgement (show the list, `--yes` only on the user's yes, offer `--older-than`) is two lines in 4-build. The "what stays on the computer" section is README material. |
| `references/delivery-history.md` | 51 | **go → `history`/`dashboard --help`, 3 lines in 4-build** | Judgement kept: read `history` before proposing a process change and after it has run; offer the dashboard for cost/retro questions. Storage location, what is copied, the three cost measures → `history --help` epilog and the dashboard page; README for people. |
| `references/locks.md` | 59 | **merge ~8 lines into 4-build, rest → `lock`/`locks`/`main-check --help`** | Judgement kept: lock contention is fixed around builders (fewer builders, cheaper proof, main-branch check); a main-branch failure goes to `plan --kind fix` or a revert, tell the module's builder, `human rereview` a Done milestone whose work was reverted. Mechanics (hold limit 30 min, test command 1 hour, exit 75, three tries, bisect, `RAN`, `ALREADY_RUNNING`) → help. The main-check failure's `next` already names `plan --kind fix` (agent_loop.py:11283). |
| `references/older-projects.md` | 86 | **go → `migrate --help` + `migrate` output** | Every case is triggered by a refusal that names `migrate`. What `migrate` does, `--to`, `--branch`, `--commit-map`, `definitions_naming_it`, and the history-rewrite warning belong in `migrate --help` and in `MIGRATED`'s `next`/`warnings`. The 2.2 renames section is history (old flags still work): delete, or one paragraph in a changelog. The "No Graded examples line" suggestion should be a `warnings` entry from `settings`/`ready`. |
| `references/report.md` | 46 | **merge "What you add" (~18 lines) into 4-build "Telling the user"; "The facts" → `report --help`** | `report --help` already has `--since` and `--write` (checked). The list of the report's parts is the output itself. What the lead adds on top is judgement and stays. |
| `references/settings.md` | 16 | **go → `settings set` command** | The whole file is a procedure (commit on main, push under `Merge: push`, read `settings_read_from`, `settings_differ`, `ran_on`). A `settings set <Label> <value>` command that commits on the main branch, pushes when allowed, and reports `ran_on` from the next launch makes it unnecessary. The user flagged this one. |

### `stages/4-build.md`, section by section

| Lines | Section | Verdict |
|---|---|---|
| 19-24 | What the user asked for | **keep** (~5): reading "two Claude builders, just checkout" into count, hosts, modules is judgement. |
| 26-33 | Model/effort defaults and per-role lines | **go**: defaults and resolution order → `settings --help`/`settings` output (resolved model and effort per role and host). Keep one line: pass `--model`/`--effort` only when the user asked for that one command. |
| 35-41 | Worktrees | **CLI behaviour**: the script should create the module's worktree (`build/<module>` from the remote or local main per `Merge:`, in an ignored folder, adding `.git/info/exclude` if needed). Today the script only makes detached checkouts for itself (agent_loop.py:4666, 14304); `run` requires an existing `--worktree`. The explanation of what a worktree is goes outright. |
| 43-53 | What `run`/`plan` carry on through | **`run --help`/`plan --help` epilog**; keep 2 lines: read `stopped_because` first, it is why you were woken. |
| 55-57 | One background command per run | **keep** (host behaviour the lead must act on, 3 lines). |
| 59-72 | Keeping watch | **`watch --help`** (cadence, `CHECK_IN`, `WARNING_SIGNS`, `--runs`, `woke_for`); keep 2 lines: keep `watch` running, restart it each time it ends, `--runs` if the host doesn't wake you. |
| 74-93 | When you're woken | **keep** (~15): the core question and the usual moves are the lead's judgement. Lock pointer becomes the merged locks paragraph. |
| 95-118 | Reading delivery | **keep** (~18): effort vs delivery, follow the effort, fewer builders. This is the lead's distinctive value. |
| 120-149 | What can start: `ready` groups table, `plan_ahead`, `unmerged_plans`, `adopt` limits | **go → `ready --help`** (currently has no description at all) and the output, whose `next` already names `adopt`/`plan`. Keep 1 line: plan a module whose Needs wait on a user decision when the user says so. |
| 151-178 | Starting agents table, planner `--module` rules, review host | **replace with a command map** (see outline). `--module` semantics are already in `plan --help` (checked). Review host default → settings help. Keep 2 lines of judgement: start a review yourself only when no run holds the milestone; review on the host that didn't build it when there are two. |
| 180-210 | Results table | **shrink to ~8 lines**: keep only results whose handling is a judgement or a user matter: `HOST_FAILED` with a usage limit (tell the user; their call), `WRONG_MODEL_OR_EFFORT` (tell the user), `PAUSED` (leave it to them), `BLOCKED` (weigh the builder's reason against what you see). The rest is "run `next`", which SKILL.md already says once. |
| 212-249 | A milestone that stopped; after a review; escalation; design review limit | **go** except two judgements: the builder's `reason` is one session's reading; add nothing to a builder's message about which findings to fix. Escalation steps are in `escalation`/`next` and documented in `next --help`. |
| 251-275 | Where sessions run | **keep 3 lines** (lead from where network and `.git` writes are allowed; a browser-driving module needs Claude or the user's choice of `danger-full-access`). `ORCHESTRATE_VISIBLE`, `blocked_write`, `needs_access` re-run → `run --help` and the existing `ask`/`next`. Disk → cleanup line. |
| 277-288 | Stopping sessions | **`pause --help`** plus `turn_not_stopped`'s own `ask`; keep 1 line: never stop processes by name. |
| 290-312 | What you pass on | **keep** (~15): what each reader should get is judgement. The flag mapping (`--task`, `--kind change`, `--human-rule`, `--message`) stays as one short list because it is "which flag when". |
| 314-350 | Questions from the agents | **keep** (~28): the answer ladder and how to spend the user's attention are the lead's core judgement. |
| 352-371 | `human` verbs table, `alone` milestones | **verbs → `human --help`** (the verbs have no descriptions today). Keep: save only what the user said; `scope` only for an edit the user dictated, with the diff shown; schedule `alone` milestones and user sittings when the build can spare them. |
| 373-382 | Option picks, graded example | **go**: `ready`'s `plan_ahead` already lists the follow-on tasks; `graded_example` is in the output. Keep one line: when the user rejects every option, give their words to a planner. |
| 384-396 | Telling the user | **keep**, and absorb report.md's "What you add". |
| 398-401 | When to stop | **keep**; worktree and build-output removal become script behaviour (see CLI work). |

### Target outline: lead (~400 lines)

```
lead/
  SKILL.md                      ~65
    - Role and mandate (as now, lines 8-28)
    - The script: what it is; how to find it (path from this skill); `--help` on every command;
      every result ends in JSON; run `next` unless you see a reason not to; `decides: human` means
      put `ask` to the user and fill in their words; reread this skill when `warnings` say a newer
      copy is installed and tell the user about `changed`. (~12 lines, down from 40)
    - The commands, by when you reach for them (a table of ~15 rows: run, plan, review, watch,
      ready, status, runs, pause, human, adopt, report, history/dashboard, flow, quota, cleanup,
      settings, paths). One line each, "when", not "how".
    - What isn't yours to change (~8): record/done-when files, commits, status only on STATUS.md,
      agents only through the script, every command is yours to run.
    - Where the project stands: the 4-row stage table; `paths` and `settings` to orient;
      after a restart read `runs` and `ready` first.
  stages/1-interview.md         ~140   judgement; brief template stays
  stages/2-start-planning.md    ~18
  stages/3-before-first-build.md ~22
  stages/4-build.md             ~155
    - What the user asked for (5)
    - How the build runs (8): one background command per run, read stopped_because, keep watch
    - When you're woken (15)
    - Reading delivery (25, including the locks/main-branch judgement from locks.md)
    - Results that need you (8)
    - What you pass on (15)
    - Questions from the agents (28)
    - The user's decisions (10)
    - Telling the user and the report (25, absorbing report.md)
    - Housekeeping (5): sandbox, cleanup only on the user's yes, history before process changes
    - When to stop (3)
  references/                   (empty: delete the folder)
  scripts/                      unchanged location
```

---

## 2. Planner

### File-by-file verdicts

| File | Lines | Verdict | Why |
|---|---|---|---|
| `SKILL.md` | 177 | **shrink to ~130** | Keep: the outcome, modules/milestones/items, the brief table, names, how deep to go, the items guidance, when you're done. Lines 19-36 (folder tree) → `paths` output, also in the planner prompt. Lines 124-134 restate proofs.md's "user chooses the look first" almost word for word: cut to 2 lines and a link. Lines 170-173 (how `check` behaves) duplicate prompts/plan.md line 10: keep only "try every check you wrote; `fail` is right, `error` means broken". |
| `tasks/change.md` | 35 | **stay, ~30** | Per-kind judgement. Lines 11-14 (how the script counts a change as a diagnosis, clears counts) are script mechanics → 1 line. |
| `tasks/diagnose.md` | 49 | **stay, ~38** | Judgement on where the fault is, KEEP vs PLANNED. Lines 32-34 (set `diagnoses` one higher on split milestones because the script can't tell) are a workaround for the script: CLI work so the script infers it (e.g. from an `"split_from"` field) and the line goes. Lines 47-49 (counts reset, one diagnosis) → go; the planner doesn't act on them. |
| `tasks/fix.md` | 21 | **stay** | Short and judgement. |
| `tasks/module.md` | 54 | **stay** | Judgement about designs, milestone size, interfaces. |
| `tasks/project.md` | 61 | **stay, ~55** | Module table header stays (format the script reads). The settings paragraph (52-61) stays as judgement (choose a test command that passes on an empty suite), but the "fill in Targets/clean clone" instruction should point at `settings init`'s template rather than restating it. |
| `tasks/revise.md` | 14 | **stay** | |
| `tasks/unblock.md` | 36 | **stay** | |
| `prompts/plan.md` | 12 | **stay** (CLI data) | Read by `prompt_text`. It is the CLI's, not the skill's; the spec keeps it beside the skill, which is fine. |
| `references/done-when.md` | 420 | **split: ~120 stay as the planner's file reference, the rest moves** | See below. |
| `references/profile.md` | 149 | **CLI: `settings init` / `settings --help`; ~10 lines of judgement move to lead stage 2** | The template, every line's meaning and default, the model/effort resolution order are all facts the script owns (`profile()` parses them). Keep in skills only the user-permission judgements: `Merge: push` only with permission; leave out host/model lines the user didn't name; `Review host: other` with two hosts; settings hold no status. |
| `references/proofs.md` | 214 | **stay, trim to ~185** | Planner craft, and its "How to inspect" is shared by builder and reviewer. Trim "What a proof costs" lines 56-60 and 68-76 (merge batching, bisecting halves, lock hold limit, one hour) to 2-3 sentences of consequence ("every merge waits for the test command, so its length caps merges per hour"). Lines 160-187 lose the duplication with SKILL.md. |

### `done-when.md`, section by section

| Lines | Section | Verdict |
|---|---|---|
| 1-59 | Where everything is, readers table | **shrink to ~15**: layout from `paths`; keep the readers table (who each file is written for is planner judgement). Evidence-folder mechanics → README. |
| 61-82 | `STATUS.md` | **README**; keep 2 lines in the planner: milestone names and the module table are what the user reads, so name them for what someone can see or do. |
| 84-99 | Module table | **stay** (format the script reads). Duplicated in tasks/project.md 10-17: keep one copy (here), link from the task. |
| 101-155 | `PLAN.md` | **stay, ~35**. The plan-file lint list (152-155) → the refusal messages from `plan`/`adopt` already name the problem: cut to one line. |
| 157-168 | `LOG.md` | **stay** (~8). |
| 170-261 | `DONE.json` example and planner fields | **stay** (~70). This is the schema the planner writes; it is load-bearing. Trim `reads` caching mechanics (230-233) and `alone` scheduling mechanics (250-253) to one sentence each. |
| 263-289 | Fields others write, counts, which milestones need a reviewer | **move**: builder fields to builder SKILL (already there), reviewer fields to reviewer task (already there), counts to README. Keep "which milestones need a reviewer" (286-289) in planner SKILL, where it already appears (143-144): delete here. |
| 291-329 | Statuses and stored names | **README + GLOSSARY** (people), `status --help` (agents). Planners don't set statuses. Note the orchestration-skill spec calls this table canonical (spec line 26), and agent_loop.py:12456 cites it in a docstring. |
| 331-351 | The record file | **README "What the script verifies"** (it already covers most of it). |
| 353-387 | Who changes what, and when | **README** for people; the script enforces it and its refusals say what was wrong. Builder and reviewer skills currently link here (builder 85, reviewer milestone.md 70): replace with their own one-line field lists, which they already have. Spec line 43 names this table as the place a change is recorded: update the spec. |
| 389-420 | When a review fails (escalation) | **README** + `next --help`. The lead acts on `escalation`/`next`; the planner gets the diagnosis kind in tasks/diagnose.md. |

### Target outline: planner (~760 lines)

```
planner/
  SKILL.md                     ~130  outcome; modules/milestones/items; the brief table; names;
                                     how deep; items (proof kinds, inspections, one claim, needs,
                                     rewriting on change); when you're done
  tasks/ (7 files)             ~240  as now, minus script mechanics
  references/plan-files.md     ~120  (renamed from done-when.md) readers table, module table,
                                     PLAN.md, LOG.md, DONE.json planner fields
  references/proofs.md         ~185
  prompts/plan.md               12   CLI data
  (profile.md removed: `settings init` writes the template, `settings --help` explains lines)
```

---

## 3. Builder

`SKILL.md` 275 lines, `prompts/build.md` 13, `prompts/findings.md` 7.

| Lines | Section | Verdict |
|---|---|---|
| 8-18 | Purpose and cast | **keep** (~10). |
| 20-47 | Where things are | **shrink to ~12**: the prompt gives the glossary, captures and handoff paths; plans paths → `paths`. Keep: read settings and project guidance; which milestone a task means; the planner's note is guidance, the breakdown is yours. |
| 49-68 | What finished looks like | **keep, ~15**: evidence uncommitted (one line, the prompt gives the folder; `merge` refuses evidence commits), commit subject `MODULE Mn:` (or make `merge` check it), `in_progress` only, LOG entry, the four last-line forms (a contract the script parses). |
| 70-74 | What the script does after `DONE` | **go**: the prompt (build.md line 3) already says it. |
| 76-81 | Handoff | **keep**. |
| 83-92 | Fields you change, stand-ins | **keep** (~8); drop the link to done-when's table. |
| 94-115 | `needs` items, `NEEDS_CONTEXT` | **keep**: judgement. |
| 117-124 | What you write | **keep**. |
| 126-150 | Proving | **keep ~14**: run `check`, judge inspect/ask yourself, record the commit, recapture after merge when `upstream_files` could change a capture, keep proof scripts in the repo. |
| 152-157 | `main-check` item statuses | **`main-check --help`**; keep 1 line: fix it if the breaking commit is yours, otherwise leave it. |
| 159-179 | Merging, batches, FAILED cases | **`merge --help`** (currently has no description) and `detail`; keep 2 lines: `main_broken` → handoff and `BLOCKED main_broken`, never race the owner's fix; a planner changed your items → reread them. |
| 181-198 | Shared resources | **keep ~6** (hold only for the command that needs it; check the user is there before a lock that needs them; `.alone` only for the whole device). Hold limit, exit 124, refusing `check`/`merge` → `lock --help`. |
| 200-209 | Long commands | **keep ~5** (the cost reasoning is the agent's); `background`/`wait` mechanics → help. |
| 211-218 | When a behaviour won't come | **keep**. |
| 220-231 | On Codex | **keep ~6**; drop the `apply_patch` paragraph (230-231), which is what Codex already does by default. |
| 233-249 | Limits; glossary names | **keep**. |
| 251-256 | A change no milestone covers | **keep**. |
| 258-275 | Without a lead | **shrink to ~6** if `run --checks-only` can go on to start the review itself (CLI work); otherwise keep as now. |

Target: one `SKILL.md` of ~170 lines plus the two prompts (CLI data). No new files.

---

## 4. Reviewer

Already lean. `SKILL.md` 81, `tasks/design.md` 57, `tasks/milestone.md` 95, `references/graded-examples.md` 71,
prompts 26.

| File / lines | Verdict |
|---|---|
| `SKILL.md` 20-48, Where things are | **shrink to ~12**: the prompt gives the review path, captures folder, glossary; working-folder mechanics go. Keep: graded examples are the guide to strictness; glossary drift is reportable but fails nothing. |
| `SKILL.md` rest | **stay**. |
| `tasks/design.md` | **stay**; lines 55-57 (two-review limit) shrink to "put every Must Fix in this review, because the second round of changes is the last". |
| `tasks/milestone.md` | **stay**; lines 67-70 drop the link to done-when's table (the script rejects other changes anyway). Lines 89-95 (truthful finding names) stay: it is the reviewer's judgement the counts depend on. |
| `references/graded-examples.md` | **stay**: calibration examples are exactly judgement. |
| `prompts/*.md` | **stay** (CLI data). |

Target: ~300 lines, same files.

---

## 5. README and GLOSSARY (for people)

These may hold more, because people read them to understand and trust the set, and they aren't loaded into an
agent's context. They should become where the explanation of the machinery lives once it leaves the skills.

**README (695) should keep**: what the set is and who is involved; how a project runs; milestone statuses; why it
is built this way; installing; starting a project with the "ask the lead / it runs" table; what the script verifies;
Claude Code and Codex; known limits; left out for now.

**README should absorb** (from skills that lose them): the statuses table and Blocked reasons (done-when 291-329),
who changes what (353-387), the escalation steps (389-420), the record file (331-351), what `STATUS.md` shows (61-82),
what stays on the computer and how cleanup works (cleanup.md 5-18), the delivery history and its three cost measures
(delivery-history.md 14-51), locks and main-branch checks in outline (locks.md). Roughly +150 lines.

**README could lose** (to a changelog or design-notes file, not installed): "Our own practice" (368-395), "What our
own runs showed" (396-403), "How much this has been tested" (625-651). They are history and evidence, valuable to
the author, not to a person deciding how to use the set. Roughly -80 lines.

**GLOSSARY (590)** already says it holds names only and that how things work lives in the skills and the help.
Keep it that way. Remove file-system paths from `Stored as` lines (e.g. `<git common dir>/orchestrate/merge-queue/`
under Merge batch), because they are implementation details that go stale; a stored name is a field, value, flag or
command. The Statuses section should hold the status names and stored values only, and point to the README for the
lifecycle. The Results section is fine as names.

---

## 6. CLI work the outline depends on

In rough order of how much skill text each unlocks:

1. **`settings init` and `settings set <Label> <value>`** (new). `init` writes `ORCHESTRATE.md` from a template
   held in the script, with each line's default and meaning as its note, and commits it on the main branch (pushing
   under `Merge: push`). `set` changes one line the same way and reports when the next launch's `ran_on` reflects
   it. `settings --help` (or `settings --explain <Label>`) documents each line and the model/effort resolution
   order, and `settings` prints the resolved model and effort for each kind of agent on each host. Unlocks: delete
   `planner/references/profile.md` (149) and `lead/references/settings.md` (16), most of `stages/2-start-planning.md`,
   and 4-build 26-33. Also update `profile()`'s docs and the orchestration-skill spec line 35, which names
   profile.md as the template.
2. **Worktree management in the script.** `run --module M` with `--worktree` naming the repository (or a new
   `worktree --module M` command) creates or reuses the module's worktree on `build/<module>`, branched from the
   remote or local main per `Merge:`, in an ignored folder; `FINISHED` removes it once nothing is unmerged, or its
   `next` says so. Unlocks 4-build 35-41 and the cleanup lines in 195 and 400.
3. **`paths` command** (new): prints, as JSON, the plans folder, every project file and module folder, the working
   folder and its per-module layout, the graded examples file, the references folder, the delivery history folder,
   the script path, each skill's folder and the version. Unlocks the file layouts in lead SKILL 70-83, planner SKILL
   19-36, done-when 20-41, builder 20-34 and 51-56, reviewer 20-28, cleanup.md 5-18, delivery-history.md 19-23.
4. **Descriptions and epilogs on every subcommand's `--help`.** Today `ready`, `merge`, `lock`, `watch`, `settings`,
   `migrate` and the `human` verbs have no description of what they do or what their results mean (checked). Each
   needs a short description, its result statuses, and the facts the skills currently carry: `ready` (the groups),
   `merge` (batches, FAILED cases, `upstream_files`), `lock` (`.alone`, hold limit, exit 124, refuses `check`/`merge`),
   `watch` (check-in cadence, `CHECK_IN`/`WARNING_SIGNS`/`RUN_ENDED`, `woke_for`), `main-check` (`NOT_ON_MAIN`,
   `COVERED`, `PENDING`, `FAILING_ON_MAIN`, exit 75, retries, bisect), `migrate` (everything in older-projects.md),
   `history`/`dashboard` (what is kept, where, cost measures), `cleanup` (approval guidance), `human` (each verb),
   `run` (routine steps, `ORCHESTRATE_VISIBLE`, `needs_access` re-run), `next` (escalation steps), `pause`
   (`turn_not_stopped`). Unlocks all five lead references and roughly half of 4-build.
5. **Top-level `--help` epilog for the result contract**: exit codes 0/1/2, the last JSON line, `result_file`,
   `next` (`by`, `decides`, `ask`, `argv`, placeholders), `warnings`, `changed`, and the two caveats (a `next`
   printed in the main working copy names that copy; a `next` reuses the module's last hosts). Unlocks lead SKILL
   36-62.
6. **Smaller output additions**: `turn_not_stopped` carries an `ask` for the user; `settings`/`ready` warn when
   there is no `Graded examples:` line; `MIGRATED` carries the history-rewrite and `definitions_naming_it` follow-ups
   in `next`.
7. **Script infers `diagnoses` for milestones split off a diagnosed one** (e.g. a `split_from` field), so
   tasks/diagnose.md 32-34 can go.
8. **Optional: `run --checks-only` goes on to start the review** for a builder with no lead, shrinking builder
   258-275 to a few lines.

Text that must change with the restructure, or it will point at deleted files:

- agent_loop.py:6503 ("Read the build skill's references/cleanup.md") and :6520 ("references/delivery-history.md")
  in the `changed` list; :362 and :12456 cite done-when.md; :1314 cites done-when.md's table.
- `.agents/skills/orchestration-skill/SKILL.md` lines 26, 35, 43 and 50-51 name `done-when.md`'s tables,
  `profile.md` as the template, and `lead/references/` as a folder. The spec would need to say the README holds the
  lifecycle tables, the script holds the settings template, and the lead has no references folder.
- `tests/orchestration/test_names.py` and the saved prompts under `tests/orchestration/prompts/` reference skill
  paths and will need regenerating if `tasks/` or links change.

Suggested order: 4 and 5 first (help text only, no behaviour change, and they let the five lead references and most
of 4-build go at once); then 3 (`paths`); then 1 (`settings init/set`, which retires profile.md and settings.md);
then 2 (worktrees); 6-8 as convenient.
