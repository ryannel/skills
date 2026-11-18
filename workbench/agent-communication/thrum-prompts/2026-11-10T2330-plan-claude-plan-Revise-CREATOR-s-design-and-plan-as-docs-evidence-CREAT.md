# plan: Revise CREATOR's design and plan as docs/evidence/CREATOR/de

Host: claude. Role: plan. Started: 2026-11-10T23:30:02Z. Session: dfa7bd71-ecfb-489a-a866-490c348dbc8c

## Turn 1: prompt sent

````text
Use the plan-module skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/plan-module/SKILL.md) for this task: Revise CREATOR's design and plan as docs/evidence/CREATOR/design-review.md asks

You can't launch other agents. The loop commits and integrates the files you leave, and records the new definitions; never edit a *-ACCEPTED.json file, and don't commit, merge, pull or land. Say what changed and any decision the owner must make. Your last line is `PLANNED: <every file you wrote or changed, comma-separated>` once those files are written, or `BLOCKED: ...` or `NEEDS_CONTEXT: ...` (including when nothing should change); the loop lands nothing then. To dry-run a milestone's checks, run `python3 /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/build/scripts/agent_loop.py check --module <M> --milestone <id> --worktree .`. The loop finds the host CLIs (codex, claude) itself, so one missing from your PATH isn't a problem to report.
````

### Turn 1: last reply

````text
efore a builder starts.

Dry-runs: the M2 browser checks come back `fail` as they should before the work exists, and `./dev check` and `./dev check-docs` pass. M3.3's check already passes today because its script exists; that item is unchanged and still has its inspection.

## What changed

- **F1, the profiler's producer interface.** The design now settles a "frame timing feed" instead of a read-only profiler:
  - **Fresh samples:** each shell also hands every completed frame sample to a bounded most-recent window that the profiler reads. The web shell's first-600 report buffer keeps its meaning.
  - **Rows by real source:** the interval row is the frame-callback interval, never display cadence. Encode and submit are one row, because the runtime measures them as one span.
  - **Timing on/off:** one switch on the frame host, on by default so existing consumers are unchanged. The design states what happens to frames in flight, across device replacement, and for report and qualification runs (they stay timed).
  - **A new read-only table control** in `thrum-controls`, because today's readouts are single numbers declared at startup and cannot hold a reason or a changing set of GPU pass rows.
- **Sequencing.** M2 now has `needs: ["APPLE-TILE:M3"]`. APPLE-TILE M2 reworks the functions the switch touches and M3 replaces the positional GPU slots with pass names, so building earlier would collide with in-flight work. The module list gains the interface row and a seam ruling, and moves CREATOR M2 from step 2 to step 5 of the build order. No APPLE-TILE or PLATFORM-RUNTIME-MAC file changed.
- **M2 items.** Rewritten as seven items. New proofs include a Chrome load change after frame 600 and a live on/off switch case (`profiler` and `profiler-switch` in the browser check).
- **S1.** M2.6 names two changes that run today: pausing the valley's world, and a starter material-hook edit. The design lists which rows move together, and changes are judged against each row's no-change spread.
- **S2.** M3.1 puts the newcomer exercise before the rest of the review, with a read log. A reviewer that read the design or engine source first gives Could Not Judge.
- **S3.** M3.4's attended text is setup only (unlocked display, Screen Recording and Accessibility grants). The agent drags, saves and captures the real window.
- **M1** is untouched.

## For the owner

Nothing here is on the `Owner decides` list. These assumptions are in the plan log and can each be overturned in a line:

1. **The profiler waits for APPLE-TILE:M3.** This puts CREATOR M2 and M3 behind APPLE-TILE's attended items; only M1 is ready now. The alternative is to build the readouts now on the positional slots and add the switch later, which means one migration and two reviews.
2. **Encode and submit are one row, and the interval row is the callback interval.** Those are what the engine measures; physical cadence stays with the Mac qualification.
3. **The profiler is off by default.** A kit scene and the V1 window then run untimed unless the profiler is on or a frames report was asked for. Mac qualification runs keep timing on, so they measure today's path.
4. **M3.4 setup needs Screen Recording and Accessibility grants** for the agent's process. Without Accessibility, a person does the slider drag only.

Carried over unchanged: the starter gets a Chrome form now; the reviewer is the fresh agent; G6 closes without the held overlays.

Sources:
- [Chrome: new in WebGPU 121 (timestamp queries)](https://developer.chrome.com/blog/new-in-webgpu-121)
- [Chrome: WebGPU developer features](https://developer.chrome.com/docs/web-platform/webgpu/developer-features)
- [wgpu-profiler](https://github.com/Wumpf/wgpu-profiler)
- [Bevy RenderDiagnosticsPlugin](https://docs.rs/bevy_render/latest/bevy_render/diagnostic/struct.RenderDiagnosticsPlugin.html)

PLANNED: docs/design/modules/CREATOR.md, docs/design/modules/CREATOR-PLAN.md, docs/design/modules/CREATOR-DONE.json, docs/design/modules/ARCHITECTURE.md
````

