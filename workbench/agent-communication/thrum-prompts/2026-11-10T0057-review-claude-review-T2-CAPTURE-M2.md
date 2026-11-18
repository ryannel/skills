# review T2-CAPTURE M2

Host: claude. Role: review. Started: 2026-11-10T00:57:24Z. Session: 5212e860-4bec-4955-92cf-e4382a899d3a

## Turn 1: prompt sent

````text
Use the review-milestone skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.5.4/skills/orchestration/review-milestone/SKILL.md) to review milestone M2 of module T2-CAPTURE. This folder is a clean checkout of commit 60b79a2b0401de3f82498e5c20156cf0286b117d, made for you by the loop; build and run the product from it. The done-when file is docs/design/modules/T2-CAPTURE-DONE.json. Write the review to docs/evidence/T2-CAPTURE/M2-review.md, and set the verdict fields, state and fails as the skill says. Don't commit, push or change anything else: the loop checks what you changed, then integrates the review itself. Don't launch other agents. End with the skill's last line.
````

### Turn 1: last reply

````text
I reviewed T2-CAPTURE M2 and it passes: both items pass, with no blocking findings and nine advisory ones. Nothing is committed.

**What I ran:**
- **Route:** built the app and asset cooker from commit `60b79a2b` and reran the full 12-case simulator route under the GPU lock. It passed.
  - The disk had 16 GiB free and the capture script refuses to start below 20 GiB, so I ran a copy with only that limit lowered to 11 GiB. The whole series used about 7 GB.
  - The read-only Screen Recording checks before and after came back denied, from the actual launcher process.
  - The console was locked the whole time; the builder's run went from unlocked to locked. The route passed both ways.
- **Captures:** decoded every capture in six sessions against its recorded hash and checked the video timing. I also measured the camera pan frame by frame: the scene moves the same way in every frame for 8.0 s, with no repeated frames and stable start and end holds.
- **Viewing:** looked at full-size frames, close crops, the moving test scene, and the first new frame after each lifecycle change (surface replaced, app backgrounded, GPU device lost).
- **Checks:** `./dev check` passed (0 failed, 0 ignored).

**Advisory findings, the main ones:**
- **A1:** the per-image surface-epoch field is copied from the capture session, so the script's stale-image check on it can never fail. The real proof that no old pixels are published is the device generation and submission order the renderer records, plus each session starting a fresh capture.
- **A2:** the stall and lifecycle cases use a scene that doesn't move, so a stale frame and a fresh one look identical. Freshness and progress after the 8 s stall are shown only by tick and generation numbers, not by pixels.
- **A3:** the 20 GiB free-space requirement is about three times what the series uses, so the documented command can't run on this disk as written.
- **A4:** the camera pan is driven by a test-only command, and the character moved by the normal controls is off-camera. Input response is proven by its recorded position, not by what's on screen.
- **A6:** during qualification, the builder reset the simulator service shared with your two other simulators. Both were rebooted, but their in-app state was lost. The committed script no longer does this.

The other four are minor: A5 (cancellation timing on backgrounding), A7 (a 145 ms frame gap under host load in one of the builder's pans; my run's worst was 23 ms), A8 (the builder needed single-threaded tests; my run didn't) and A9 (existing shadow and rock-texture look issues outside M2).

I changed only `docs/evidence/T2-CAPTURE/M2-review.md` (new) and the M2 verdict, review and state fields in `docs/design/modules/T2-CAPTURE-DONE.json`, with M2 set to `done`. My scratch output in `tmp/t2-m2-review/` (about 7 GB) can be deleted once the verdict lands.

PASS M2
````

