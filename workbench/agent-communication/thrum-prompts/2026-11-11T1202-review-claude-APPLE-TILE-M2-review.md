# thrum · APPLE-TILE · M2 review

Host: claude. Role: review. Started: 2026-11-11T12:02:22Z. Session: 19fbb4e0-1a90-4e1a-b967-8f023b08c1f4

## Turn 1: prompt sent

````text
Use the review-milestone skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.7.1/skills/orchestration/review-milestone/SKILL.md) to review milestone M2 of module APPLE-TILE. This folder is a clean checkout of commit a6101020a94c50e386bc33ce7f41743a84937957, made for you by the loop; build and run the product from it. The done-when file is docs/plans/APPLE-TILE/DONE.json. Write the review to docs/evidence/APPLE-TILE/M2-review.md, and set the verdict fields, state and findings as the skill says; the loop sets the counts. Put captures and other evidence files in docs/evidence/APPLE-TILE/M2-review/ and link them from the review, rather than embedding them in it. Don't commit, push or change anything else: the loop checks what you changed, then integrates the review itself. The owner's answers for M2 are in docs/plans/APPLE-TILE/ACCEPTED.json under milestones.M2.owner_answers (for D2.5, D2.3). Check any claim about what the owner chose against them. Don't launch other agents. End with the skill's last line.
````

### Turn 1: last reply

````text
M2 fails review on one item, D2.3. At the claimed commit `a6101020`, the image is no longer byte-exact against the M0 baseline. The other four items pass.

**Cause.** The M2 code itself is sound. The break comes from APPLE-PRESENTATION M1 (`5258d963`), which landed after M2's code commit and before M2 was claimed. It turns on camera jitter for every game view, so each frame is rendered slightly shifted.
- **Claimed commit:** both reproduction scripts fail at their first exact comparison. The letterbox image differs in 316,181 pixels and the SDR approach checkpoint in 472,377.
- **Window:** with the world paused and the camera held, consecutive window captures differ in about half the pixels.
- **Parent commit `3870a021`:** this has the M2 code without the jitter change. It is exact 4/4, and its held window is byte-identical between captures.
- **Builder's evidence:** my build of that parent has exactly the same hash as the builder's evidence binary (`1b55ef38…`). So none of the builder's evidence was produced from the commit it claimed.

**Must Fix.** One, `d23-exactness-broken-at-claimed-commit`, against D2.3. The likely fix belongs to APPLE-PRESENTATION: its own M1 review already has this jitter as its Must Fix. Once that lands, the M2 builder should rerun both scripts on the commit being claimed and record its git revision. The M0 baseline should not be refreshed or widened.

**Items that pass:**
- **D2.1 (one split graph):** I read the graph, executor and host code and the tests, and found the scene and present phases correctly separated.
- **D2.2 (refusal, loss and replacement):** the existing tests pass under `./dev check` (exit 0), and my own window run showed same-process surface replacement recovering cleanly.
- **D2.4 (iOS simulator):** my run of the lease, background and replacement route passed. Rotation was not exercised.
- **D2.5 (real window):** I captured the window myself on both recipes:
  - Sun, night and noon match their engine references in content.
  - Key presses turn the camera.
  - The letterbox measures 12/13 rows at 1520×880 and 146/147 at 1400×1080, and restoring the window brings back the full image.
  - Surface replacement recovers in the OS video.

  The held-camera crawl also affects this item but is counted once, under the D2.3 finding.

The review also lists four suggestions that don't change the result. They cover a misleading error name in the resize code, a missing Mac test for device loss after acquisition, manifests that don't record the git revision, and rerunning proofs after a rebase that brings in rendering changes.

I wrote `docs/evidence/APPLE-TILE/M2-review.md` with its evidence folder `M2-review/` (13 MB). In `DONE.json` I set the five verdicts and review links, set M2 back to `in_progress`, and added the one finding. Nothing is committed.

FAIL M2: 1 fail, 0 cant_tell, 0 outside the items
````

