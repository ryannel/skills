# Critique of the proposed fixes for the five delivery-lead failures

Read-only review. Checked against the working tree on `orchestrate-polish` (orchestrate 1.6.2) and against
`origin/main`, which already carries **1.6.3** (`557f3cc`). The local `main` branch is stale; 1.6.3 is on
`origin/main` only, and it already ships part of failure 1's fix. Base the work on `origin/main`.

## Recommended fix set

| # | Fix | Where | Size |
|---|---|---|---|
| 1 | Already mostly shipped in 1.6.3. Add one script change: stop emitting `next.by: "owner"`. `by` always names who runs the command (`lead` or `planner`). Mark an owner decision with `decides: "owner"` plus the existing `ask`. Drop proposal 1(a). Keep 1(c) as the owner's working habit. | `next_cmd`/`owner_next`/`owner_answers_next` in `agent_loop.py`; `build/SKILL.md` "What each result means"; about 6 test asserts | Small |
| 2 | Run the planner in one checkout that the script owns and reuses, as reviews already do. On any result except `PLANNED`, stash what the planner left. Delete a module's verify checkout once the module is `FINISHED`. Reject the `Disk needed:` profile line and the delete-when-disk-is-short logic. | `cmd_plan`, the `FINISHED` path in `agent_loop.py`; `build/SKILL.md` table row and "When to stop" | Medium-small |
| 3 | Make `plan` wait for the planner lock by default, with no flag. Delete `TAKEN` for `plan` and its retry `next`. Reject per-module planner locks. | `cmd_plan`; `build/SKILL.md` around line 206 | Small |
| 4 | Keep the design-review question, but write it as a clause in rules that already exist, in three places. Reject the new stop reason: the existing `BLOCKED` route to a planner worked. | `done-when.md` "What makes a good item"; `review-milestone` "Reviewing a design"; one clause in `build-milestone` | Tiny |
| 5 | Delete prose status from the suite's own formats, starting with the status lines that `plan-module` currently *requires* in the plan file. Add one rule that designs, the module list and the project settings say what is wanted, never where it stands. Reject the lint. Agree with rejecting the hash exemption. | `done-when.md` plan-file template; `plan-module` "What finished looks like" item 4; `build-milestone` step 4 | Small |

Overall, the fix set deletes more than it adds. It removes the planner's clean-worktree rule and its two `INVALID`
paths, the `TAKEN` result for `plan`, and the plan file's status lines. The only additions are one field rename,
one stash call and one cleanup on finish.

---

## 1. The lead asked the owner to type a command

### What the code shows

- **Up to 1.5.x, the skill told the lead to do exactly this.** `git show 1c08066:skills/orchestration/build/SKILL.md`,
  line 99: `` `by: owner` is a decision only the owner may make, such as `owner accept`: put it in your report for
  them to type``. Line 151 of the same file: "The commands below the owner types at a terminal, and the loop
  refuses them inside any session it started". 1.6.0 (`98619f5`) reversed this. The lead's words, "The loop
  refuses that command from agents, so you need to run it yourself", echo the old line 151 almost verbatim.
- 1.6.2 already gets proposal 1(b) right for `next`. `owner_cmd` (agent_loop.py:1454) appends
  `--text '<the owner's words, as they gave them>'`, and `owner_next` (1460) says "Ask the owner in chat; once
  they've decided, run the command with their words in --text". The guard's message (5902) says "the lead records
  the owner's decisions".
- 1.6.3 on `origin/main` adds "Never give the owner a command to type" to the skill. It also adds "A note or
  summary that says the owner must type these commands at a terminal is from an older version of this set", and
  makes the planner-or-run refusal in `owner_guard` say "Nothing more is needed from the owner … run this same
  command again once that has stopped".
- The field that still says otherwise is `next.by: "owner"`. `build/SKILL.md` line 246 calls `by` "whose move it
  is", and the script's docstring (line 127) says "`owner unpark` (by: owner)". That is the one place in current
  output that still reads as "the owner runs this", and it is the hook the old rule hung on.
- No planner was running when the lead asked (transcript, 21:39: "Nothing else is planned"), so the guard did not
  refuse anything. The lead never tried the command. It acted on its stale belief.

### Verdict

- **1(a), re-read the skill after a compaction: drop it.** The stale rule reached the lead as a "standing
  constraint" in the compaction summary, which reads as the user's own instruction. Re-reading a skill that the
  lead believes is outranked by the user does not reliably fix that. 1.6.3's line naming the old-version note is
  the targeted antidote, and it is already shipped. *(Inference: I have not tested how Claude Code re-attaches
  invoked skills after a compaction.)*
- **1(b): already done.** 1.6.2 does it for `next`, and 1.6.3 does it for the guard's refusal. Nothing further
  is needed beyond the rename below.
- **1(c), keep suite development out of the delivery lead's session: right, and it is the root cause.** That
  session had been reading and editing older versions of the skills, so its context held both rules. This is the
  owner's habit, not suite text, so record it in memory or CLAUDE.md rather than in the skills.

### Better fix, enforced by the script

Rename the field rather than adding prose. `next.by` should only ever be `lead` or `planner`, the one who runs
the command. Mark a decision with `decides: "owner"` next to the existing `ask`. The skill row becomes: "`decides:
owner` means put `ask` to the owner in chat, then run `command` yourself with their words." The 1.6.3 sentence
about older notes can then be retired in a later release.

- Where: `next_cmd`, `owner_next` and `owner_answers_next`, plus the two "report it" `INVALID` results (lines
  4495 and 4812 here), which have no command and so stay pure decisions. Also the `by` sentences in the docstring
  and `build/SKILL.md` lines 246–249. The tests assert `next.by == "owner"` at about six places (test_agent_loop.py
  1034, 1513, 1519, 2758, 2993, 3008).
- Size: small, under 30 lines. It changes output that leads parse, so it needs a release note.

*Aside (inference):* `owner_guard` refuses every owner decision in the repository while any planner runs (the
`_plan` check), not just decisions about the module being planned. With long Fable planners, and with fix 3
queueing planners back to back, that window gets longer. The check is load-bearing: Codex app threads have no
`ORCHESTRATE_ROLE` (line 3704). So do not delete it, but it is worth watching.

## 2. Disk full

### What the code shows

- **Reviews already run in a checkout the script owns.** `review_once` calls `verify_tree(worktree, stem, start)`
  (line 4447) for milestone and design reviews alike. `--worktree` only locates the repository. The lead's five
  hand-made worktrees for "planning and reviews" were unnecessary for the reviews. The skill table (line 194)
  doesn't ask for a clean worktree for reviewers; the lead over-applied the planner row.
- **Planners run in the worktree the lead passes,** and `plan` refuses it unless it is clean (`INVALID`) and has
  no commits the tip lacks. That second case returns a `next` that makes yet another detached worktree
  (`fresh_wt`, around line 4770). Only the planner row says "in a clean worktree" (line 195).
- **The script already keeps a `_PLAN` checkout.** `loop_write(worktree, prof, "_plan", …)` in `cmd_plan` calls
  `verify_tree(worktree, "_plan", tip)`, so `.git/orchestrate/verify/_PLAN` exists in every planned repository.
- `verify_tree` runs `git clean -ffdq` without `-x`, so ignored build output survives. That is the intended warm
  cache. One checkout per module plus the lead's per-module worktree means each module's build cache can exist
  twice. *(The doubling is inference: I did not measure Thrum's verify folder.)*
- The builder's `BLOCKED` already named the exact need ("needs 16 GiB free, 14 available"). The stop itself worked;
  what was missing was a way to reclaim space.

### Verdict and better fix

- **2(a), create-and-remove per run, kept on failure: more machinery than needed.** Only one planner runs per
  repository, under the `_plan` lock, so one reused checkout is enough. Run the planner in a script-owned checkout
  (`verify_tree(worktree, "_planner", tip)`, or `_PLAN` itself if the ordering with `loop_write` is kept straight)
  and keep it between plans, as reviews do.
  - On `BLOCKED`, `NEEDS_CONTEXT`, `UNFINISHED` or `INVALID`, run `git stash push --include-untracked -m
    "<task>"` and name the stash in the result. The `INVALID` path already uses this mechanism (its `next` stashes
    with "refused planner turn"). The next plan then starts clean, with no keep-or-delete rules.
  - This deletes the clean-worktree `INVALID`, the ahead-commits `INVALID` and its `fresh_wt` command, and the
    "in a clean worktree" instruction in the skill. Reviews and plans then work the same way.
  - Edge case to handle: the first plan, when no `ORCHESTRATE.md` exists yet. There is no base branch to check
    out, so keep today's behaviour there. *(Inferred from the `missing_ok` path in `cmd_plan`; not traced
    fully.)*
  - Planners on Codex will write inside `.git/orchestrate/verify/…`. Codex reviewers already write their review
    files there (`tree / review_path`), and design reviews ran there in Thrum, so this is confirmed to work.
  - Size: medium-small. Roughly 30–50 lines in `cmd_plan`, adjusted tests, and one skill row.
- **2(b), the `Disk needed:` profile line: reject.** The 16 GiB is one milestone's capture need, not a
  project-wide number, so a profile line is the wrong granularity, and someone has to measure and maintain it. The
  builder already reports the shortfall precisely, at the cost of one short turn. If a milestone has a known need,
  its item or runbook can say so in words.
- **2(c), delete Done modules' verify checkouts when disk is short: right target, wrong trigger.** Delete a
  module's verify checkout when the module reaches `FINISHED`, every time, with no free-space logic. `verify_tree`
  recreates it on demand for a later `owner rereview` or a record write, which costs one cold build. Size: about
  5 lines.
- **Add to the skill:** one sentence in "When to stop" or "Keeping builders busy": remove a module's own worktree
  once the module is finished, not only when the whole build stops. The lead's per-module worktrees came to 47 GB
  in Thrum, and the skill only asks for cleanup at the end, which three days of running never reached.

*Not addressed, worth noting (inference):* a 158 MB evidence folder means captures are being committed.
`profile.md` already has a "Large captures:" line for where bulky evidence goes, so this is a planning-quality
issue in Thrum, not a missing mechanism.

## 3. The planner lock skipped a round

### What the code shows

- `cmd_plan` takes `run_lock(worktree, "_plan")`, which uses `take_file_lock` with `LOCK_PATIENCE_S = 0.5`. If the
  lock is held, `plan` emits `TAKEN` with a retry `next`.
- **`emit` always exits 0** (agent_loop.py, `def emit`: `sys.exit(0)`), including on `TAKEN`, `INVALID` and
  `BLOCKED`. The lead's chain ("planner fix then design re-review") therefore carried straight on, and its task
  notification read "completed (exit code 0)", so nothing looked wrong.
- The lock is taken before the clean check and the sync to the tip, so a planner that waits for the lock still
  starts from the latest tip.

### Verdict and better fix

- **`plan --wait`: right idea, but don't add a flag. Make waiting the default.** There is no case where the lead
  wants `TAKEN` from `plan`. Every `TAKEN` leads to the same instruction, run it again when the other planner
  stops. Wait with an unbounded `take_file_lock`. That deletes the `TAKEN` branch, its `next`, and the skill
  sentence "When two modules both need a planner, run them in turn".
  - Register the waiting process with `loops` as waiting, so `loops` still shows it. *(Small; inferred to be
    needed, because `loop_register` currently runs after the lock.)*
  - Add "as a background command" to the planner row, as the builder row already says.
  - Size: about 10 lines, plus one test.
- **Per-module lock: reject.** A planner's task is free text that can touch several modules and `ARCHITECTURE.md`.
  The script can't know in advance which modules it will touch, and conflicts on shared files would turn into
  failed rebases at land time. Planners are few and short next to builds, so serialising them costs little.
- **Optional, separate decision:** exit nonzero when nothing happened (`TAKEN`, `INVALID`, `FLOOR`). That protects
  every chain the lead writes, not just planner chains. It changes behaviour that leads may rely on, so leave it
  out of this set unless the owner wants it.

## 4. An item needed a later milestone

### What the code shows

- The script rejects a later milestone only in the `needs` field (`done-when.md` line 101). Item text is free
  prose, and the script cannot judge it in general (web, CLI, native, engine).
- `done-when.md` "What makes a good item" already says an item "depends only on this module". That is the natural
  sentence to extend.
- The design reviewer is already asked, of each item, "whether you could really judge it" (`review-milestone`,
  around line 127).
- The routing already exists. `build-milestone` says to end with `BLOCKED` when something is missing (line 128),
  and `build/SKILL.md` says "If something another module owns is missing, or the design is the problem, send it
  to a planner". In Thrum this route took six minutes: 01:42 to 01:48 in the transcript.

### Verdict and better fix

- **Checklist question: keep it, but as clauses in existing sentences.**
  - In `done-when.md`: "…and it depends only on this module, and on what exists when this milestone ends."
  - In the design review: "…whether you could really judge it when its milestone ends, with only the milestones
    before it built."
  - In `build-milestone` line 128: "Don't build something another module owns, or a later milestone of this one."
  - Size: three clauses.
- **Named stop reason: reject.** It would need a template line, a parser, a result value and a skill row, to do
  what `BLOCKED` plus "the design is the problem → planner" already did here.

## 5. Status in prose went stale

### What the code shows

- **The suite itself requires prose status.** `done-when.md` lines 19–36 define the plan file's `Reviews:`,
  `Milestone:`, `Now:`, `Next:` and `Blocked:` lines, and milestone headings such as `## M2 <name>: in
  progress`. `plan-module` "What finished looks like" item 4 requires those lines to be "up to date".
  `build-milestone` step 4 has builders update them. The script reads none of them; it computes status from
  `state` in the done-when file (`ready`, `status --module`).
- Design approval is a hash of the whole design file (`text_hash(design.read_text())` in `owner accept` and the
  review path). Any status line in a design therefore costs a re-approval whenever it changes.

### Verdict and better fix

- **The proposal's direction is right, but as written it contradicts the suite's own plan-file format.** Telling
  planners "don't write milestone status in prose" while the template demands `Now:` and `Blocked:` lines leaves
  the cause in place. The fix is deletion:
  - Remove the five status lines and the `: done` / `: in progress` heading suffixes from the plan-file template.
  - Remove item 4 from "What finished looks like".
  - Builders keep only the per-milestone work checklist and the log.
  - Add one sentence to `plan-module`: "Designs, the module list and the project settings say what is wanted,
    never where it stands; where it stands is `status`."
  - Size: small, mostly deletions in three files.
- **Lint or review flag: reject.** A pattern such as "parked", "blocked" or "in progress" would misfire on designs
  that describe those states as product behaviour (a job queue, a game). The design hash already punishes status
  in a design.
- **Rejecting the hash exemption: agree.** Parsing status lines out of the hash would keep the disease and add
  machinery.
- One-off cleanup in Thrum: the `APPLE-TILE.md` header needs a planner edit and a design re-review (or
  `owner accept --milestone design` if the owner prefers). `docs/BUILD-PLAN.md` is the project's own document and
  outside the suite's reach.

## What I confirmed versus what I inferred

**Confirmed in code or git:**
- The pre-1.6.0 skill told leads to have the owner type commands.
- 1.6.2 `next` and 1.6.3 refusals already say to record the owner's words.
- `by: owner` is still emitted.
- Reviews run in `verify_tree`, and a `_PLAN` verify checkout already exists.
- `plan` requires a clean worktree and emits `TAKEN` on a held lock.
- `emit` always exits 0.
- `needs` is the only later-milestone check.
- The plan-file template mandates status lines that the script never reads.
- The design hash covers the whole file.

**Inferred:**
- That re-reading the skill after a compaction wouldn't have overridden the summary.
- That module caches are doubled across verify checkouts and lead worktrees.
- The first-plan edge case for a script-owned planner checkout.
- That `loops` needs a "waiting" entry.
- That a nonzero exit would change existing lead behaviour.
