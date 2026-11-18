# thrum · PLATFORM-RUNTIME-MAC · plan: Scoped re-plan of PLATFORM-RUNTIME-MAC M2: the attended Inst

Host: claude. Role: plan. Started: 2026-11-11T12:41:23Z. Session: 33e9b77a-bcb4-4d43-b9a6-927972370473

## Turn 1: prompt sent

````text
Use the plan-module skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.7.1/skills/orchestration/plan-module/SKILL.md) for this task: Scoped re-plan of PLATFORM-RUNTIME-MAC M2: the attended Instruments Game Performance traces (owner present, console unlocked, panel awake) saved readable traces but their display-event tables are empty, so physical cadence on the built-in ProMotion panel can't be judged. DevToolsSecurity reports Developer mode disabled; whether that causes the missing events is unverified. See docs/evidence/render/mac-m2-20261111/README.md and the LOG. Diagnose the likely cause from evidence and documentation, and revise M2 so the next attempt has a display-event source that's known to work, or a different authoritative cadence witness. If the fix needs an owner action (such as enabling Developer mode, a security setting only the owner may change), mark it next.decides: owner and say exactly what to do.

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit an ACCEPTED.json file or the plans folder's STATUS.md, which the loop writes, and don't commit, merge, pull or land. Each module's files go in its own folder under the plans folder: DESIGN.md, PLAN.md, LOG.md and DONE.json. PLAN.md holds only the present: one `##` heading per milestone, no status lines and no log, and the loop refuses a plan that breaks this, saying why. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change, except for a diagnosis, which ends with its `KEEP` line); the loop lands nothing then. To dry-run a milestone's checks, run `python3 /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.7.1/skills/orchestration/build/scripts/agent_loop.py check --module <M> --milestone <id> --worktree .`. The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report.
````

### Turn 1: last reply

````text
M2 is re-planned around a cadence witness that already works in the saved traces; Developer mode is not the cause, and no owner security change is needed.

## Diagnosis

I exported row counts from scratch copies of both retained 11 November traces (no new recording, originals untouched).

- **Authorization is not the cause.** The capture-OFF trace holds 7.7 million system-wide kernel events, and both traces include events from the kernel and WindowServer. A recording refused kernel tracing could not contain them.
- **One kernel source is silent.** The table for codes `0x34,0x11`/`0x34,0x0f` has zero rows in both traces, and every display table is empty with it. Why this Mac emits none is not established, and I found no documented switch for it.
- **The recordings were also windowed.** Game Performance records as a ring buffer and kept only about 2.9 seconds, starting after the pan began. Even a populated swap table would have failed the full-interval criterion.
- **A working witness is already there.** `ca-client-presented-handler` has one row per game drawable with an OS-reported presented time on the 120 Hz grid: 349 consecutive drawables with capture OFF, 343 with capture ON.
- **It registers missed refreshes.** It shows three two-refresh intervals (16.67 ms) across the two traces. One coincides with the game's own 15.47 ms present-call gap; another is a miss the game's log cannot see.

## What changed in M2

- **M2.4 (unattended, no recording):** one reusable command turns a trace into presented intervals per drawable and must reproduce the three known missed refreshes from the retained tables.
- **M2.5 (new, attended):** a fresh recording whose retained rows span both `MacM2Whole` markers, with the time conversion validated against the markers.
- **M2.2 (attended):** the same three arms, with the capture-OFF arm judged from the witness and every interval over one refresh listed and investigated.
- **Recordings:** six are granted across M2.5 and M2.2; the old allowance is spent. Empty display tables are recorded and no longer block.
- **M3.2:** its wording now follows the same witness; nothing else in M3 changed.

I ran `./dev check-docs`, which passes. I did not run the M2 dry-run, since its only check is M2.3's unchanged `./dev check` under the contended GPU lock.

M2 is still stored as blocked, so the lead needs to run `unblock`. The design changed and still needs an independent design review before a builder starts.

## For the owner

- **`next.decides`: not owner.** The only owner action is the existing attended setup: unlock the Mac, wake the built-in panel and keep it awake for the sitting. No Developer mode, Instruments authorization or Screen Recording grant.
- **Assumption to confirm or overturn:** the OS-reported presented time of each game drawable is an acceptable witness for built-in ProMotion cadence, in place of the Instruments display-swap table. It is not the kernel's swap record or photons. Overturning it means finding why the display source is silent before M2 can close.

Sources:
- [Analyzing the performance of your Metal app](https://developer.apple.com/documentation/xcode/analyzing-the-performance-of-your-metal-app)
- [MTLDrawable.presentedTime](https://developer.apple.com/documentation/metal/mtldrawable/presentedtime)
- [xctrace(1)](https://keith.github.io/xcode-man-pages/xctrace.1.html)
- [DevToolsSecurity(8)](https://keith.github.io/xcode-man-pages/DevToolsSecurity.8.html)

PLANNED: docs/plans/PLATFORM-RUNTIME-MAC/DESIGN.md, docs/plans/PLATFORM-RUNTIME-MAC/PLAN.md, docs/plans/PLATFORM-RUNTIME-MAC/DONE.json, docs/plans/PLATFORM-RUNTIME-MAC/LOG.md, docs/evidence/PLATFORM-RUNTIME-MAC/m2-display-event-diagnosis.md, docs/evidence/PLATFORM-RUNTIME-MAC/m2-presented-off-traced.tsv.gz, docs/evidence/PLATFORM-RUNTIME-MAC/m2-presented-on-traced.tsv.gz
````

