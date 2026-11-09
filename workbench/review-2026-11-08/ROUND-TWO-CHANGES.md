# Round-two changes

9 November 2026, branch `round-two`. This maps each decision in `SYNTHESIS-2.md`, and each ranked finding in
`astra-REVIEW-2.md` (P1 and P2) and `fable-REVIEW-2.md` (all 23, which are unbanded), to what changed, what was
deferred, and why. Tests are in `tests/orchestration/`. A test named `test_astra_N_...` or `test_fable_N_...`
reproduces that finding and now passes. Decision 8, sessions visible in the apps' GUIs, came after the rest of the
round, once its research had finished; it has its own section below.

`LOOP` below is `skills/orchestration/build/scripts/agent_loop.py`.

## The design in one paragraph

The loop now owns acceptance. Next to each done-when file it keeps `<MODULE>-ACCEPTED.json`, written only in
commits it makes, which carry the trailer `Orchestrate-Loop: yes`. Per milestone, the record holds the authorised
definition hash, the claim the loop checked (the code commit, and the integrated tip it ran the checks on), the
reviews, and the acceptance (by checks, review, owner or adoption). It also holds the design review, against a hash
of `<MODULE>.md`. Those writes happen in a loop-owned *verify tree*, a detached worktree under
`<git common dir>/orchestrate/verify/<MODULE>`. It's kept across uses, so ignored build caches stay warm, and it's
reset with `checkout --force` and `clean -ffd`. The loop then lands them with `land()`: rebase, an optional Check, and
a push or local fast-forward under the integrate lock. Reviews run in the same verify tree at the claimed commit. The
loop validates what the reviewer changed, then applies the verdict field by field to the tip. Readiness is one
function, `next_step`, used by `ready`, `status` and `run`.

## Decisions

| # | Decision | What changed | Deferred, and why |
|---|---|---|---|
| 1 | The loop owns acceptance | The acceptance record above. `delta_problems` validates the whole done-when delta per role (build, review, design, plan). Upstream versions count only if a loop-made commit wrote them, because builders push to the same branch. Definitions are authorised only by `LOOP plan` (after the planner's turn) or `owner scope`. A builder bumping `replans` authorises nothing. `next_step` is the one readiness predicate, and `--milestone` only confirms the next milestone, never skips one. `owner scope` keeps `fails` and `replans`. A failed review resets the items that didn't pass (`reset_proof`), and a re-plan clears proof on changed milestones. | A module the loop has never seen is adopted as it stands, once (trust on first use). |
| 2 | Every role is validated, and the loop integrates role output | `cmd_review` checks that the commit exists and is integrated, that it was claimed at that commit and at the tip, that the reviewer changed only allowed paths, that the review file was written, that the last line names the milestone and agrees with the verdicts, that `fails` went up by exactly one on a fail, and the done-when delta. On INVALID nothing lands. `cmd_plan` needs a clean tree, validates the planner's files, rejects a plan that grants passes or touches records, commits the leftovers, lands them, authorises the definitions, and returns `design_review_owed`. Design review is recorded in the record and gates `ready`. Review and plan pass `FLOOR`, `PIN` and `PAUSED` through with reasons, and a missing CLI is exit 127, a controlled FLOOR. | None. |
| 3 | Overreach measured only on the reviewer's own change; the lead never reverts | Reviews run in a clean checkout of the claimed commit, and `changed_paths` diffs only that tree against its start. Upstream work landed meanwhile never appears (`test_fable_2_...`). The `overreach`/revert step is gone from `build/SKILL.md`; an invalid review simply doesn't land. | None. |
| 4 | Checks run on the integrated tip | `claim_problems` fetches fresh and requires HEAD to be contained in the tip. It refuses if the record was edited outside the loop, or if the tip's definitions aren't the authorised ones. It runs the Check and every item `check` in the verify tree at the tip, and fails the claim if a check leaves files behind. | Containerised checks (in "Not now"). |
| 5 | Profiles fail loudly | `Integrate` and `Check` are required in strict mode, which `run`, `review`, `land`, `unblock`, `owner` and the plan's result use; `ready`, `status` and `next` read loosely so they still report on a half-written profile. `Check: none` is the explicit no-gate choice. The non-strict fallback is `local`, never `push`. A `Default host` line, then the host the loop runs inside, then the only one installed, else `codex`. Placeholder detection now matches only `<words>`, so `< /dev/null` in a Check passes. | Sign-in isn't detected, only installation; a signed-out Claude still gives a FLOOR with the reason. |
| 6 | Engineers' workflows | **Blocked:** `BLOCKED` writes `state: blocked` plus `blocked: <reason>` through the loop, and `LOOP unblock` re-queues it. **Attended items:** an `attended` field (a definition key); the builder does the rest first, and the loop batches unpassed attended items into the blocked reason. **Pause:** `LOOP pause` sends SIGTERM to the pid in each run lock; the loop stops its child's process group (TERM, then KILL) and reports PAUSED. **Owner commands:** `LOOP owner accept, rereview, unpark, scope, release`, refused when `ORCHESTRATE_ROLE` is set (every child the loop starts has it), and needing a TTY with the target typed back; rereview keeps the old review as `<mid>-review-<n>.md`. **Needs errors:** forward and self needs in a module are validation errors, and needs on parked milestones and cross-module cycles are reported as invalid. **Status:** project-wide `LOOP status`, or `--module`. **Two leads:** claim refs at `refs/orchestrate/claims/<MODULE>/<mid>`, created on the remote (a push that fails if the ref exists) or locally with `update-ref` and a zero old value; the second lead gets `TAKEN`. **One milestone:** the lead stops after the named milestone is accepted. **Fix a bug:** build-milestone's ordinary-fix route integrates with `LOOP land`. The loop also parks a milestone itself when the ladder says `park`. | Two leads on the *same* clone share the run lock, so the second gets TAKEN at the module level; that's intended. Claims aren't released automatically if a lead dies (`owner release`). |
| 7 | Host neutrality | README "Where you run" and "Known limits" say the lead's sandbox and OS permissions wrap every child. Codex reviewers and planners get `-c features.multi_agent=false` (the flag exists in local codex 0.167 `features list`). Prompts give each skill's file path for hosts without skills. The README notes the `claude -p` sign-in dependency and the `--bare` risk, with tested versions. A host table sets the per-host gaps side by side. | Claude effort isn't checked per turn (the stream doesn't report it); stated in the host table. |
| 9 | Docs and fidelity | The sprint-contract citation is corrected, and the Cursor lock-bottleneck finding is cited as a deliberate trade. The stray "fan" is fixed. The "Unverified" comparisons are removed: the Opus 5.5 medium-vs-Opus 5 high comparison and the "hard caps on subagents" claim in `models.md`. The OpenAI attribution in `instructing-agents/SKILL.md` and `skill-creator/references/writing.md` now reads "define completion and where to stop". skill-creator: the `allowed_tools` example is read-only with a note on `--allow-tools`; trigger prompts run three times; `plugin eval` isolation versus competition and the `arm: both` delta are explained; the effective model and effort are recorded; contexts are fresh and not forked; the cases run on each target model; reserved folder names are cut to the two the page names. `check_skill.py` uses PyYAML when present, otherwise a strict scan (an unquoted `: `, an unterminated quote, a duplicate key, a stray line), and adds reserved words and anchor checks. Trimmed: the escalation ladder lives once in `done-when.md#when-a-review-fails`; `build`, `build-milestone`, the README and `next` point there; `models.md`'s time-signal and frontend-look paragraphs and the `tool_choice` line are gone. | `instructing-agents/SKILL.md` 72–80, the noun list: left alone, because a separate rebuild of that skill is in progress and edits there would collide. |

## Decision 8: sessions the owner can see in the apps

**What changed.** On a Mac, `run_turn` now picks a path per turn for the `codex` and `claude` hosts, and every result
line from a turn says which ran: `path` is `visible` or `headless`, with `path_reason` when headless (and
`app_settings` for Codex, the model and effort the app window reports). Other hosts are untouched and get no `path`
field. The methods come from `~/Workspace/codexctl` (`VISIBLE-THREADS.md`, `CLAUDE-VISIBLE-SESSIONS.md`); what the
loop needs was brought into `LOOP` itself (`CodexAppServer`, `CodexIpc` and the functions around them), so the skill
still ships one self-contained file.

- **Codex, visible.** For a new session a short-lived bundled `codex app-server` creates the thread (source
  `vscode`, cwd the worktree or verify tree), runs one bootstrap turn at the requested model and effort so the rollout
  records them, and names it `build <MODULE> <M>`, `review <MODULE> <M>` or `plan: <task>`. `codex://threads/<id>`
  gives the app window the thread, so the IPC router can stop it. Each loop turn queues the prompt (`codex queue`) and
  fires `codex://threads/wake/<id>`; the app's own app-server runs it. The loop reads the rollout from the offset it
  noted, and the turn ends when every started turn has completed or aborted, nothing is queued, and nothing new has
  started for `SETTLE_S` (20 s), so the goal turns the app chains count as one loop turn. The pin check, goal status
  and quota read the same files as before. Pause (`LOOP pause`) and timeouts send the app's Stop over IPC; a timeout
  then re-activates a goal that was active, since Stop pauses it. The owner pressing Stop, which aborts the turn, gives
  `PAUSED` with a reason rather than a failed turn, and `run` again re-activates the paused goal and carries on.
- **Claude, visible.** Only the app can sign in a process it starts, and a shell can't start or wake an app session
  without a relay session, so the loop keeps running its own `claude -p` per turn, now under a session id it chooses
  (`--session-id`), and imports the session into the Code tab with `claude://resume?session=<id>` as soon as its
  transcript exists, so the first turn can be watched too. If the app doesn't list the session within 15 s, the
  result says `headless` with that reason. Before resuming, the loop looks in `~/.claude/sessions/` for a live app
  process on the session; if the owner has it open, the turn reports `PAUSED` instead of writing to it at the same
  time. `clean_env` now keeps `CLAUDE_CODE_OAUTH_TOKEN`, the plan's own token, so `claude setup-token` can sign the
  loop in.
- **Fallback.** `visible_unavailable` names the reason to run headless: `ORCHESTRATE_HEADLESS=1`, not macOS, the app
  not installed, the app not running (no Codex IPC router; no Claude desktop process), or the Claude CLI signed out
  (`claude auth status`). Headless is the old path, unchanged. It's checked per turn; a Codex thread made visibly can
  be resumed headless with `codex exec resume`, and the reverse, so a switch doesn't start a fresh session.
- **Skill text.** `build/SKILL.md` ("Where you run", the `PAUSED` row and the owner's controls) and the README's host
  table and known limits say what the owner can do in each app and which path ran. The README's duplicated, stale
  "Known limits" section was removed.

**Verified.**
- Unit tests with fake hosts (`VisibleCodex`, `VisibleClaude`, `VisibleChoice`; 104 tests in all, all pass): a build
  claimed on a visible thread with the requested model, effort, role, title and folder; resumed turns go to the same
  thread with the message; a turn on another effort is `PIN`; Stop in the app is `PAUSED`; a pause and a timeout stop
  the app's turn, and the timeout keeps an active goal active; `run` again re-activates a goal paused in the app; a
  review runs in its own visible thread in the verify tree; without the app the result says `headless` and why; a
  Claude build gets `--session-id` and one import link; the loop won't resume a Claude session the owner has open;
  each fallback reason; other hosts unaffected.
- One live Codex run (9 Nov, driven only through links, IPC and files; whether the Mac was locked wasn't checked): a one-item milestone in
  `~/Workspace/scratch/orch-vis-test`, `--effort low`. Result `CLAIMED`, `path: visible`, `app_settings:
  gpt-6.1-sol low`; the builder committed, landed through `LOOP land`, and the loop recorded the claim. Both turns in
  the rollout (bootstrap and build) ran on gpt-6.1-sol low. The app's own sidebar query (`thread/list`, `sourceKinds:
  []`, `useStateDbOnly: true`) lists the thread as "build HELLO M1", source `vscode`, cwd under the `scratch` project
  root, so the app groups it under that project. Not seen on screen.
- Claude, partly, because the standalone CLI is signed out: `visible_unavailable("claude")` correctly reports the
  CLI signed out, so Claude runs fall back to headless (which then fails on sign-in, as before). The import itself was
  run live: a signed-out `claude -p --session-id` wrote the transcript, and `claude_import` produced the Code tab's
  record (`local_<id>.json`, `fromCliTranscript: true`) in 2.5 s. `pgrep -x Claude` turned out not to see the app on
  this Mac, so the check reads `ps` instead.

**Not verified, and limits.**
- A signed-in Claude turn on the visible path, and whether the Code tab refreshes live while the loop's process
  writes. The relay method (an app session that wakes imported sessions) isn't built: it needs a session the owner
  keeps open, and a relay acts on a peer's word, which can't carry the owner's authority.
- **The Codex app applies its own permissions to the thread.** The bootstrap turn records the loop's sandbox
  (writable roots including the git common dir, network on), but when the app resumes the thread it applies its
  default profile: workspace-write on the folder only, network restricted, `.git` read-only, approvals by
  auto_review. In the live run the push to a repository outside the folder still went through, by escalation, but a
  worktree's commits and any network use will escalate too. Setting the app's thread permissions (the IPC
  `thread-follower-update-thread-settings`) wasn't explored. The same goes for `features.multi_agent=false` on
  reviewers and planners: it's passed in the thread's config, but whether the app keeps it is unchecked.
- A new Codex thread opens in the app window, bringing the app forward; the thread's preview is the bootstrap line;
  the bootstrap costs one tiny turn. The deep links, IPC method versions and experimental app-server methods are
  pinned to app 26.1103 and CLI 0.167.0-alpha.3.2. Owner steering by typing into a Codex thread wasn't tested inside
  a loop run.
- Left for the owner to archive (the app holds them, so only the app can): the Codex thread "build HELLO M1"
  (`01a1be11-a7c4-7443-8527-c4e481c5e672`) in the scratch project, and the imported, untitled Claude Code session
  `93a4733b-2686-42a7-901b-4e8bd594c7fe` (cwd `~/Workspace/scratch/orch-vis-claude`). Their folders are deleted.

## Astra review 2

| Finding | Status |
|---|---|
| 1 P1 Acceptance pin trusts builder-editable fields | Fixed (decision 1). `test_astra_1_weakening_...` (weakened check plus bumped replans gives INVALID, and stays INVALID on a fresh run), `test_astra_1_forging_...`, `test_astra_1_a_record_edited_outside_the_loop_...`. |
| 2 P1 Queue releases dependents before accepted proof | Fixed: `next_step` needs record acceptance. `test_astra_2_*` (a done state with no review, a forged done, an open milestone with all items passing, `--milestone` skipping). |
| 3 P1 Review accepted on its last sentence | Fixed (decision 2). `test_astra_3_*` (a missing commit, `PASS M999` with no review). |
| 4 P1 Overreach misses real changes / invites reverts | Fixed (decision 3). `test_astra_4_*` (an uncommitted source edit, a deleted milestone). |
| 5 P1 Integration proves an old checkout | Fixed (decision 4). `test_astra_5_*` (an old ancestor HEAD, a check leaving untracked files). |
| 6 P1 Verification runs mutable code with the lead's permissions | Deferred per "Not now"; still a stated limit in the README. |
| 7 P2 Incomplete profile authorises push | Fixed (decision 5). `test_astra_7_and_fable_1_...`. |
| 8 P2 Re-planning keeps stale proof; proof not bound to a revision | Partly fixed: the record binds acceptance to definitions, claim commit and checked tip, and re-plans and failed reviews clear proof; review history is kept in the record, and `rereview` archives the old file. Deferred: giving the reviewer an explicit base commit for "the milestone's whole diff", because it needs a milestone start marker that the claim flow doesn't yet record. |
| 9 P2 No durable design gate | Fixed (decision 2). `test_design_owed_holds_the_module`. Bootstrap still needs an interactive planner for the very first profile, as before. |
| 10 P2 Local-only and PR workflows | Local fixed: `land()` fast-forwards the base branch in whichever worktree holds it, or with `update-ref`, and `build/SKILL.md` branches from the local base. `test_astra_10_...`. PRs stay out, as listed in the README. |
| 11 P2 Warm worktrees need sync; one builder per module is lead-managed | Fixed: `run` fast-forwards a clean worktree to the tip before choosing; a per-module run lock and milestone claims enforce one builder per module. If a planner changes the running milestone's definitions mid-build, the claim is refused, because the tip's definitions no longer match the ones the run started with; the lead restarts the builder. |
| 12 P2 Skill frontmatter can undo model overrides | Deferred. The Claude skills keep `model`/`effort` frontmatter, which can override a launch flag when the skill loads. Removing it changes how the skills run in ordinary chats, so that's an owner decision; the host table states that effort isn't checked per turn. |
| 13 P2 Review/planner host failures lose the result | Fixed (decision 2). `test_astra_13_*`. |
| 14 P2 Validation crashes | Fixed: `validate` type-checks shapes, ids, proofs and counters; unreadable JSON gives INVALID; reads fail closed on a bad fetch (`TipError`). `test_astra_14_*`. Targets aren't validated against the profile's table, because the table is prose. |
| 15 P2 Instructions disagree on plan changes; "paths and nothing else" | Partly fixed: `build/SKILL.md` now says independence means withholding conclusions, not the task, and owner restrictions go with `--message`. Deferred: the `goals-and-briefs.md` boundary, because of the parallel instructing-agents rebuild. |
| 16 P2 Environment blockers spend the retry ladder | Partly fixed: `BLOCKED` records a blocked state without adding to `fails`, and attended items are batched. A reviewer's `cant_tell` from a missing device still counts as a fail, as decided in round one. |
| 17 P2 Checker accepts malformed YAML | Fixed. `test_check_skill.test_astra_17_...`, plus duplicate keys, quotes, reserved words and anchors. |
| 18 P2 Comparisons need effective configuration and fresh contexts | Fixed in `testing.md`. |
| 19 P2 Trigger runner tests in isolation | Fixed in `testing.md`. |
| 20 P2 Reviewer accuracy unmeasured | Deferred per "Not now"; the README still says so, now including false rejection. |

## Fable review 2

| Finding | Status |
|---|---|
| 1 Profile omitting Integrate or Check | Fixed (decision 5). |
| 2 Overreach flags others' work; lead told to revert | Fixed (decision 3). `test_fable_2_...`. |
| 3 Failed review leaves items `pass` | Fixed: the loop resets them. `test_fable_3_...`. |
| 4 No coordination between leads or clones | Fixed: claim refs. `test_fable_4_...`. |
| 5 Lead's sandbox ignored | Documented (decision 7). |
| 6 No pause; killing leaves the child running | Fixed. `test_fable_6_*` (a grandchild killed, pause signalling the pid). |
| 7 Owner scope change costs the only re-plan | Fixed: `owner scope`. `test_fable_7_...`. |
| 8 Needs cycles, forward needs, parked needs | Fixed. `test_fable_8_*`. |
| 9 New module invisible until pushed | Fixed: `plan` lands it. `test_fable_9_...`. |
| 10 Default host always Codex | Fixed. `test_fable_10_...`. |
| 11 Reviewer's working tree | Fixed: a clean checkout of the claimed commit, as the skill says. |
| 12 Lock bottleneck uncited | Cited in the README as a deliberate trade. Running the Check before taking the lock is deferred with lock granularity ("Not now"). |
| 13 Sprint contract | Fixed. |
| 14 `--bare` default risk | Documented, with tested versions. |
| 15 Codex reviewers unrestricted | Fixed: `features.multi_agent=false`. `test_fable_15_...`. |
| 16 Generic hosts get skill names, not paths | Fixed. `test_fable_16_*`. |
| 17 `ready` and `run` disagree | Fixed: one predicate. `test_astra_2_and_fable_17_...`. |
| 18 Thrum AGENTS.md versus profile push | `profile.md` now says the Integrate note should name itself as the authorisation AGENTS.md refers to. Thrum itself was not touched, as instructed. |
| 19 Thrum items have no `check`; review paths | Not changed (Thrum is out of scope). Under the new loop, review files must be at `<evidence>/<MODULE>/<mid>-review.md`, so Thrum's convention would give INVALID reviews until its profile's Evidence or its habit changes. Flag for the Thrum lead. |
| 20 Fidelity | Fixed: the attribution, the Opus comparison, subagent caps. Testing on each model is added to `testing.md`. |
| 21 skill-creator test format | Fixed: `allowed_tools`, reserved names, the eval isolation line. |
| 22 Bloat and voice | Partly fixed: the ladder lives once, the models.md trims, the stray "fan", the attempt now defined ("three different approaches, each built and run"). `build/SKILL.md` grew (152 lines, from 116) because it now carries owner controls, the sandbox note and new results; the instructing-agents noun list was left for the rebuild. |
| 23 Smaller items | Fixed: reflog progress ignores rebased-in commits (`test_fable_23_...`); module names are case-insensitive (`module_stem`); a design review of a module with no done-when file now says it isn't planned, rather than giving a misleading parse error. Deferred: a Claude `--model` alias still trips PIN (`startswith`), because resolving aliases needs the CLI's mapping; `check_skill` reserved words are now flagged. |

## Other trade-offs worth knowing

- The first use of the verify tree for a module is a cold build; after that, ignored caches persist.
- Codex `workspace-write` sandboxes haven't been tried writing inside `.git/orchestrate/verify`, because no real model
  was launched. If they refuse, reviewers need `danger-full-access` or a writable root for that folder.
- The record is protected by detection, not cryptography. A deliberately forged trailer gets past it.
- Owner commands need a TTY, so an owner driving everything through an agent chat must run them in a terminal.
- A review done by a subagent outside the loop can't be recorded; the owner would use `owner accept`.
- `Integrate: local` fast-forwards the base branch in whichever worktree has it checked out, which is the owner's
  main checkout in the usual setup; that's what "local" means here, and it's stated in `profile.md`.
- The module's last milestone needs review, judged at the time. If a planner later appends milestones, an earlier
  "last" milestone accepted by review stays accepted.

## Verification

- `python3 -m unittest discover tests/orchestration`: 104 tests, all pass (fake hosts only; no model launched). The
  live decision 8 checks are in its section.
- `check_skill.py` on the five orchestrate skills and skill-creator: all ok. Output on the generative-media skills
  is identical before and after the checker change.
- `claude plugin validate .`: the marketplace manifest passes.
- `npx skills add ./ --list` not run, because it would download a package.
