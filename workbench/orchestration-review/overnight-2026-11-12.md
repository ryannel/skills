# Thrum overnight on orchestrate 2.1.0, 12–13 November

- 23:05 — 2.1.0 pushed to main (9579d90) and installed from skill-factory for Claude and Codex.
- 23:25 — No new lead session could be started remotely and the owner hadn't started one, so the 2.1.0 brief went to
  the existing Delivery Lead session. A check of Thrum runs every 20 minutes.
- Waiting for the next patch: `runs` printed "0 loops running"; now "0 runs going" in the source.
- 23:27 — Lead migrated Thrum (0a2fd1e7) and ran `migrate --branch` on six worktrees. Two conflicted at first
  (culling, effect-graph); the lead followed the printed `next` and both migrated. Started CULLING M1 and
  APPLE-PRESENTATION M2. Display work skipped: the screen locks after 10 minutes of display sleep, despite
  caffeinate. Left for the owner.
- Held for the next patch: `runs` header wording, and the step label counting the milestone's turns instead of
  this run's. Suite passes with both.
- 23:32 — Healthy. APPLE-PRESENTATION M2: the script is checking D2.1. CULLING M1: builder turn 1 in a new session. 57 GiB free.
- 23:52 — Healthy. APPLE-PRESENTATION M2's checks are in the GPU tests (cargo test, field_occlusion_gpu running); CULLING's builder queues on the GPU lock. 61 GiB free. Two healthy checks: moving to every 40 minutes or so.
- 00:08 — Healthy. APPLE-PRESENTATION M2's checks reached D2.5. CULLING's builder is waiting on its GPU jobs behind them. 67 GiB free.
- 00:37 — Working as designed. The script's clean-checkout checks failed APPLE-PRESENTATION M2 and set it back to In Progress (08b5e182): a flaky FSEvents watcher test and browser checks that assume an ignored web build exists. Those are real project faults the 2.0.0 flow let through. Its builder is fixing them in a new session. CULLING is still on turn 1, sharing the GPU. 52 GiB free.
- 01:08 — Healthy. Both builders active (CULLING turn 1 at 1h41m, close to the 2-hour turn limit; APPLE-PRESENTATION fixing its check failures). 50 GiB free. Backing off to hourly.
- 01:38 — Healthy. CULLING M1's builder merged its repair (c6e50cf6) and ended its turn; the script is running its checks (at M1.5). The usage row for that turn carries context 154k of 475k and version 2.1.0, so release 1 is recording. APPLE-PRESENTATION's builder is still fixing. 54 GiB free.
- 02:38 — Healthy. CULLING M1 finished, and CULLING M2 is building. APPLE-PRESENTATION M2: after the repair, the script's checks passed and it set Ready for Review (5b6c8aaa); the Astra review failed it on one real gap (D2.6's witness bypasses the production forward pass), accepting the script's check results instead of rerunning the gate (one 14-minute review, 143k input tokens). The lead is running EFFECT-GRAPH M2 in the second builder slot, so APPLE-PRESENTATION waits its turn. 41 GiB free.
- 03:38 — Healthy. CULLING M2 and EFFECT-GRAPH M2 building; EFFECT-GRAPH's turn reaches the 2-hour limit around 03:55, which will test the turn-limit token row. 39 GiB free.
- 04:38 — EFFECT-GRAPH M2 passed review (dbc32264). Turns that hit the 2-hour limit (exit 124) now have usage rows with tokens (EFFECT-GRAPH 02:54, CULLING 03:27). CULLING M2's session was 320k of 475k (67%), and the next turn started a new session, as release 2 intends. APPLE-PRESENTATION M2 is fixing its review finding. Disk is the concern: 32 GiB free, down about 7 GiB an hour; asked the lead to reclaim verify-checkout and finished-milestone build output under the owner's permission. Next check in 20 minutes.
- 04:50 — The lead reclaimed disk: 33 → 164 GiB free (verify checkouts' build output, finished milestones' scratch). It kept anything a pending review or re-record needs. Disk follow-up cancelled.
- 05:38 — Healthy. APPLE-PRESENTATION's builder merged its fix for the D2.6 finding (6aa152ca..e76ce61b) and is finishing its turn; CULLING M2 is on turn 2 in a new session. 167 GiB free.
