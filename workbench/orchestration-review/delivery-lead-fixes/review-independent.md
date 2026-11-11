# Independent review: fixes for the five delivery-lead failures

Reviewed against orchestrate 1.6.2 as it stands on branch `orchestrate-polish` (commit 708b09e). Read-only: nothing
in the skills, the script or the tests was changed. Line numbers are from that commit.

## Recommendation, in order

1. **The script owns the planner's slot: one checkout and one queue (fixes 3, and most of 2).** `plan` runs its
   planner in a loop-owned checkout, as `review` already does, and waits for the planner lock instead of returning
   `TAKEN`. The lead stops making worktrees for planners and reviewers, and stops retrying planners by hand. This
   is mostly deletion: the clean-worktree refusal, the "commits ahead of the tip" refusal, its suggestion to make a
   fresh worktree, and the `TAKEN` retry all go.
2. **Drop a module's loop checkout when the module is finished, and have the script say when to remove the
   builder's worktree (the rest of 2).** About 10 lines in the script and a changed `why` string.
3. **Status lives only in the script's record (fixes 5).** Add one rule that no design, settings file or project
   document says where a milestone stands. Delete the plan file's status lines that copy the done-when file. This
   changes documentation only.
4. **One clause in the design review (fixes 4).** Have the reviewer ask whether each item can be proved by its own
   milestone and the ones before it. This is cheap, so it is worth doing, but it is low priority.
5. **Make the result line say that the lead runs the owner's commands (hardening for 1).** The main cause of
   failure 1 was a stale rule in the lead's compacted memory, which no change to the suite can reach. The only
   current signal that pointed the same way is `next.by: "owner"`, and that is a few lines to change. This is
   optional.

### Shared causes

- **2 and 3 are partly one failure.** The planner needs two things: a working copy and the one-per-repository
  planner slot. The script leaves both for the lead to manage by hand. The lead made a worktree for each planner
  run (and, needlessly, for each review), nothing removed them, and a `TAKEN` result had to be noticed and retried.
  Fix 1 addresses both. Failure 2 also has a second cause that the planner doesn't touch: loop checkouts and
  builder worktrees of finished modules are never released.
- **1 and 5 have the same shape.** Each is a copy of something the script holds, kept where the script can't
  update it: an old rule in the lead's memory, and milestone status written in prose. The fix is the same in
  spirit: remove the copy and make the script's output the only source. For 5 there are real copies in the suite's
  own conventions to delete. For 1 the copy lived only in the lead's compaction summary, so the suite can only make
  its own output impossible to misread.
- **4 stands alone.** It is a mistake in how one plan was written that two design reviews missed. The recovery
  path already worked: `BLOCKED`, then a planner, then a re-review, about six minutes from the lead's diagnosis to
  the re-reviewed plan.

---

## Failure 3: a planner fix was skipped because of the planner lock

### Confirmed by reading the code

- `cmd_plan` (agent_loop.py 4747–4752) takes the `_plan` run lock without waiting. If another planner holds it,
  `emit("TAKEN", ...)` prints a result whose `next` repeats the same `plan` command.
- `emit` (3200–3210) always ends with `sys.exit(0)`. So `TAKEN`, `BLOCKED`, `INVALID` and the other results all
  exit 0, and `plan ... && review ...` carries on after a `TAKEN`.
- The design review that followed ran against the unchanged design. `review_once` has no check for "nothing
  changed since the last `DESIGN CHANGES`", so CREATOR spent a review to learn what it already knew.
- `test_r10_a_second_planner_is_told_to_wait_for_the_first` (test_agent_loop.py 3746) pins the current
  behaviour.

### Recommended fix: `plan` waits for the planner lock

In `cmd_plan`, replace the `TAKEN` branch with a wait.

1. Register with `loop_register(..., waiting_for="planner")` first, so that `loops` and `status` show a queued
   planner.
2. Call `install_stop()` before waiting, so that `pause` still stops the waiting planner. The waiting planner then
   returns `PAUSED`.
3. Loop on `take_file_lock(path, patience)` until the lock is free, printing one stderr line naming the holder
   (from `run_holder_info`).

Everything after the lock is taken stays as it is, and that is what makes waiting better than retrying: the
planner syncs to the tip after the earlier planner has landed, so it plans on top of that work.

- **Size:** about 15 lines in `cmd_plan`. Rewrite test 3746 to start a holder, release it, and assert that the
  second plan lands. In `build/SKILL.md` around line 206, replace "A second `plan` gets `TAKEN` … or give one
  planner both tasks" with one sentence: "A second `plan` waits for it, then plans from the tip the first one
  merged." Change the docstring at agent_loop.py line 146 the same way.
- **Why this is the elegant fix:** it removes a mechanism (`TAKEN` and the lead's retry) instead of adding one, and
  it works for any caller: a shell chain, a second lead, or a lead that has been compacted. The lead's own goal,
  running the planners "in sequence, so they don't collide on ARCHITECTURE.md", becomes what the script does.

### Rejected alternatives

- **Non-zero exit codes for results that aren't successes.** This turns a silent skip into a visible stop, but the
  retry is still manual. It also changes the contract of every command at once, and leads read the JSON, not the
  exit code.
- **Refusing a design review when the design hasn't changed since `DESIGN CHANGES`.** This catches the symptom
  and adds a new check. With the wait in place the case can't arise from this cause.
- **A line in the skill telling the lead to check each result before chaining.** That is a rule the agent has to
  remember, and a compacted lead is exactly the one that forgets it.

### Watch for (inferred)

`owner_guard` (5897–5909) refuses every `owner` command while any planner holds `_plan`. With planners queued back
to back, that window grows, and the refusal ("…while a planner is running…") is easy to misread as "the loop
refuses agents". That misreading is the confusion behind failure 1. Neither failure needs the guard changed now.
If it shows up, narrow the lock part of the guard to the module's own lock: the `ORCHESTRATE_ROLE` check already
stops every session the loop started.

`review` has the same `TAKEN`-and-exit-0 shape for the module lock (4407–4410). The evidence doesn't show it
biting, so leave it.

---

## Failure 2: a builder stopped because the disk was full

### Confirmed by reading the code and measuring Thrum

- **Reviewers never needed the lead's worktrees.** `review_once` runs the reviewer in
  `verify_tree(worktree, stem, start)` (4447, then `one_session(..., tree, ...)` at 4473), the loop's own checkout
  for that module. Its `--worktree` only identifies the repository. The lead still made a worktree for each review.
  The transcript at 22:15 says "Launching the three design reviews … and the swarm-game planner …, each in its own
  clean worktree."
- **Planners do run in the lead's worktree.** `one_session(..., worktree, ...)` (4785). `cmd_plan` refuses a dirty
  worktree (4758–4760) and one with commits the tip lacks (4762–4778). The second refusal's `next` tells the lead to
  `git worktree add --detach <name>-plan-<timestamp>`, so the script itself creates disposable worktrees that
  nothing removes. `build/SKILL.md` line 195 says to run the planner "in a clean worktree".
- **Loop checkouts are never released.** `verify_tree` (2230–2243) keeps one checkout per module for warm caches.
  Nothing removes one when its module is finished.
- **Measured in `~/Workspace/thrum/.git/orchestrate/verify/` (du, read-only):**
  - COOKED-DRAW is 6.9 GB, and every milestone of that module is `done` on `origin/main`.
  - T2-CAPTURE (529 MB) and PLATFORM-RUNTIME-IOS (213 MB) are also finished.
  - That is about 7.6 GB held for finished modules. Freeing it would have covered the 2 GiB shortfall several times
    over.
  - The lead's own `.claude/worktrees/t2-capture` is a further 7.2 GB, for a finished module.
- **Builder worktree cleanup is attached to an event that never came.** `build/SKILL.md` "When to stop" (388–389)
  is the only place that says to remove merged worktrees, and a lead that runs for three days doesn't stop.

### Recommended fix, part 1 (shared with failure 3): `plan` runs in a loop-owned planner checkout

Only one planner runs per repository, so one checkout is enough.

- **What changes:** after taking `_plan`, set `tree = verify_tree(worktree, "_PLAN", tip)` and run the planner,
  `plan_owed`, the commit and `land` in `tree`. `loop_write` already uses a `_PLAN` checkout for the planner's
  record commit. Using it for the planner as well is safe because the planner's commit has landed before
  `loop_write` resets it. On a land failure the commit has to be kept (on a branch, or stashed) before the next
  reset.
- **What gets deleted:** the dirty-worktree `INVALID`, the "ahead of the tip" `INVALID` and its fresh-worktree
  `next`, and the `sync_worktree` call.
- **Planner files that don't land:** on `BLOCKED`, `NEEDS_CONTEXT` or `UNFINISHED` they currently "stay
  uncommitted for you to report and then clear". Stash them instead, with
  `git stash push --include-untracked -m "planner: <task>"`, and name the stash in the result. That is the pattern
  the refused-plan `next` (4842–4849) already uses, so the two paths become one.
- **Unchanged:** Codex placement already falls back to the repository's project (`codex_project_for`, 3676), and
  the writable roots already include the git common dir (3703), as they do for reviewers.
- **Docs:** in `build/SKILL.md` line 195, drop "in a clean worktree". After the table, add one sentence: "For
  `review` and `plan`, `--worktree` only names the repository; the script runs the agent in a checkout of its own."
- **Size:** about 30 lines changed in `cmd_plan`, with a net deletion. Tests at 3719–3721 (ahead-of-tip) and
  2131–2137 (`left_uncommitted`) need rewriting or deleting. The planner can no longer see the lead's uncommitted
  files, but `plan` already refuses those today, and the brief already has to be on main.

### Recommended fix, part 2: release finished modules' trees

- **Loop checkouts:** add a small `drop_tree(worktree, name)` that runs `git worktree remove --force` on
  `verify/<NAME>` and then `git worktree prune`. Call it from `after_pass` (4656) when `step["status"] ==
  "finished"`, and from `cmd_ready` for each module it sorts as `finished`. The `cmd_ready` call also reclaims
  trees left by earlier runs, such as COOKED-DRAW's. `owner rereview` of a finished module still works:
  `verify_tree` rebuilds the checkout on demand, only with a cold cache. Size: about 10 lines and one test.
- **The builder's worktree:** the script doesn't know which worktree the lead used for a module, so don't delete
  it from the script. Put the instruction where the event happens. In `after_pass`, extend the finished `why` to
  "…is finished: every milestone is accepted. Remove its worktree (`git worktree remove <path>`) once nothing in it
  is unmerged, then start other ready work." In "When to stop" (388–389), the line becomes "remove each module's
  worktree when it finishes". Size: one string and one sentence.

### Rejected alternatives

- **A free-disk preflight before `run`.** How much space a project needs is project-specific: the 16 GiB came
  from APPLE-TILE's own capture check, which already reported the shortage accurately.
- **Dropping the warm checkouts altogether.** Warm caches are worth keeping for modules still being built. Only
  finished modules lose their checkout.
- **A `cleanup` command.** It would be one more command for the lead to remember. Attaching cleanup to `finished`,
  which the script already detects, needs nothing extra.

### Not a cause, recorded for the owner (measured, not fixed)

Each Thrum checkout is about 583 MB clean, of which 565 MB is committed `docs/evidence/` (557 MB of it under
`render/`). There are about 30 checkouts (9 loop checkouts, plus the lead's and other sessions' worktrees), so
committed evidence alone accounts for roughly 15–17 GB of the disk.

`keep_round` (1353) copies each review round's captures folder rather than moving it. Git stores identical
content only once, so the repository isn't inflated, but every checkout writes the copies out again.

This is the project's evidence policy interacting with many checkouts, not one of the five failures, so I'd leave
it. If it becomes the next disk problem, the fix is to keep large captures out of the tree (Thrum's `tmp/` rule
already says to), not to change the script.

---

## Failure 5: status written in prose went stale

### Confirmed by reading the code and Thrum's files

- `design_ok` (1111) compares a hash of the whole design file. Any edit to the design, a status line included,
  sends the module back to `design_owed`. So the planner was right not to touch the header.
- A changed `ORCHESTRATE.md` is an owner decision (`plan_drift` / `profile_note`, 1624–1650, and `build/SKILL.md`
  158). So every status line in the settings turns a routine status update into a question for the owner. That is
  why nobody updated the Targets section.
- Thrum's `ORCHESTRATE.md` Targets section on `origin/main` carries many lines of milestone status: "T2 M0 (Mac)
  and M1 (Chrome) are done; simulator M2 is implemented and claimed…", "APPLE-TILE remains parked…".
  `APPLE-TILE.md`'s header carries "M0 remains parked and no … unpark is claimed" and "T2 M0 … and M1 … are done".
  This is a habit across the project, not a single stray line.
- **The suite itself asks for prose status.** `plan-module/references/done-when.md` lines 3 and 19–30 say the plan
  file "says where the module stands", with `Reviews:`, `Milestone:`, `Now:`, `Next:` and `Blocked:` lines and
  `## M1 <name>: done` headings. `plan-module/SKILL.md` 197 and `build-milestone/SKILL.md` 27 and 52 require them
  to be kept up to date. The script never reads them (grep finds no use in agent_loop.py). They copy the
  done-when `state` and `blocked` fields and the record's reviews, which the script already shows with
  `status --module <M>`.

### Recommended fix

1. **One rule, in the two places that write project documents.**
   - In `plan-module/SKILL.md` "What you write": "No file you write says where the work stands: not the design,
     the module list, the project settings or any other project document. The script's record holds that, and
     `status` shows it. A status line in prose is wrong the next time a milestone moves. In a design, changing it
     also voids the design's approval, and in the project settings it needs the owner."
   - In `build/SKILL.md`, after "What only the script decides", add the same in one sentence for the lead, who
     wrote the Targets and BUILD-PLAN lines.
2. **Delete the status copies the suite mandates.**
   - In `done-when.md`, drop the `Reviews:`, `Milestone:` and `Blocked:` lines and the `: done` / `: in progress`
     heading suffixes.
   - Keep `Now:` and `Next:` together with the log, as the builder's working notes between sessions.
   - Change line 3 to "The plan file holds the milestones' work and a log", and change `plan-module/SKILL.md` 197
     to match.
   - In `build-milestone/SKILL.md` 27 ("your milestone is the next one in PLAN.md"), point to the done-when file
     instead, which is what the script actually uses.
   - Update `GLOSSARY.md` 87.

Size: about 10 lines of documentation across 5 files. No script change.

Thrum's existing status prose is a one-time clean-up for the project, not the suite. Removing it from
`APPLE-TILE.md` costs one design re-review, because of the whole-file hash. Do it the next time a planner revises
that design.

### Rejected alternatives

- **Excluding a "status header" from the design hash.** That adds a mechanism to protect a copy that shouldn't
  exist, and it does nothing for `ORCHESTRATE.md` or `BUILD-PLAN.md`.
- **Having the script lint designs and settings for milestone ids next to words like "parked" or "done".** That
  would be fragile, and it would misfire on history that is legitimate ("M0 was parked after…" belongs in the
  plan log).
- **Having the script write a status block into these files.** That makes more copies, all of which need to be
  kept in step.

---

## Failure 4: a milestone item could only be proved by a later milestone

### Confirmed by reading the code and skills

- The script's check is mechanical. `validate` rejects a `needs` that points at a later milestone of the same
  module (`done-when.md` 99–102). It can't see a dependency implied by an item's `statement` or `check` wording.
  No script signal exists either: before the work exists every check is expected to `fail`.
- The design review asks of each item "whether you could really judge it, and whether a convincing fake would
  pass it" (`review-milestone/SKILL.md` 128–129). It doesn't ask whether this milestone can produce the proof.
  The Must Fix list (133–135) doesn't name that case either.

### Recommended fix

In `review-milestone/SKILL.md`:

- Line 128 becomes "…ask of each whether you could really judge it, whether its milestone, with only the ones
  before it, can produce that proof, and whether a convincing fake would pass it."
- In the Must Fix list, add "an item its milestone can't prove".

Size: two clauses. Optionally, put one matching sentence in `done-when.md` "What makes a good item", which is
where the planner learns how to write an item.

### Is it worth fixing?

Only just. It is semantic, so nothing the script can enforce, and the existing recovery path worked. The cost was
some builder time on M0 and one planner turn plus one re-review. I include it because the fix is two clauses and
engines and native apps often stage proofs across milestones. If the owner prefers the suite unchanged here,
treating it as a one-off is defensible.

---

## Failure 1: the lead asked the owner to type a loop command

### Confirmed by reading the code and the history

- **The current skill and script say the opposite of what the lead did.**
  - `build/SKILL.md` 323–324: the owner "never uses a terminal, so every command is yours to run".
  - `ladder_next`'s park branch and `owner_next` (1460–1465) produce `ask` text and a `why` that says "Ask the
    owner in chat; once they've decided, run the command with their words in --text".
  - Test `test_r18_owner_stops_ask_in_chat_and_never_send_anyone_to_a_terminal` asserts no "terminal" and no
    `--reason` in any owner `next`.
- **The lead's wording comes from the version before 1.6.0.** Up to commit 2ad09f8, `build/SKILL.md` said "The
  commands below the owner types at a terminal, and the loop refuses them inside any session it started, so no
  agent can make these calls for the owner." It used `--reason`. Commit 98619f5 (orchestrate 1.6.0, 10 Nov)
  replaced that with "never uses a terminal".
- **The lead's command used `--reason`.** It is still accepted as a hidden alias (`main`, 6121). The current
  `next` prints `--text`. So the lead wrote the command from memory of the older text rather than copying the
  `next` the script printed.
- **One current signal does point the wrong way.** `next_cmd`'s docstring (1319–1322) defines `by` as "who runs
  it (`lead`, or `owner` …)". Owner decisions carry `by: "owner"`, while every other `by` value names who runs the
  command. A lead that skims the JSON reads "the owner runs this", which agrees with a stale memory.

### Inferred, not confirmed

The transcript doesn't show the lead trying the command and being refused. At 21:39 no planner or run held
APPLE-TILE, so `owner_guard` would not have refused it. "The loop refuses that command from agents" is most likely
the pre-1.6.0 sentence, carried in the lead's compaction summary next to its standing rule "Never sign owner loop
commands as the owner unless the owner explicitly says to". That rule is right as far as it goes. The lead
generalised it into "the owner must type it".

### Recommendation: mostly a one-off; harden the output cheaply

The cause was a lead session that started under 1.5.x, kept running across the 1.6.0 change, and was compacted
about ten times, while also developing the skill. A lead that loads 1.6.x fresh never sees the old rule. Adding
more skill text wouldn't help: the right text is already there, and the lead wasn't reading it.

The one change worth making removes the remaining ambiguity in the script's output, because that output is current
however stale the lead is:

- In `owner_next`, in `owner_answers_next`, and at the two tampering stops (4495, 4812), set `by: "lead"`. The
  owner's part is already carried by `ask`, which those results have. The contract becomes "`by` always names who
  runs `command`; a `next` with `ask` waits for the owner's answer". That removes one value from the vocabulary
  instead of adding a field.
- Update the `next_cmd` docstring, the module docstring (93–103), and `build/SKILL.md` 246–249 ("`owner` means…"
  becomes "a `next` with `ask` is a decision only the owner may make…").
- Change about 12 test assertions that check `by == "owner"`.
- Optionally, drop the `--reason` alias. A command written from old memory then fails with "required: --text",
  which points to the current form. It is one line, but it doesn't touch the chat message that was the actual
  failure, so it is low value.

Size: about 6 lines of script, about 12 test assertions and 2 sentences of skill.

### Rejected alternatives

- **A skill line telling the lead to re-read `build/SKILL.md` after compaction.** It is exactly the kind of line a
  compacted lead drops.
- **Letting a planner's revision of a parked milestone clear the park automatically, so that no unpark is
  needed.** The park after a second failed rewrite is deliberately the owner's gate (`escalation`, 954–961). The
  owner said "You unpark it for me", which is the gate working as designed once the lead asked properly.
