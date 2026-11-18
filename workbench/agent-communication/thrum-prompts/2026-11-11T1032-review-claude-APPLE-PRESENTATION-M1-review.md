# thrum · APPLE-PRESENTATION · M1 review

Host: claude. Role: review. Started: 2026-11-11T10:32:10Z. Session: 45eb429a-1217-478d-83a3-0cf53834581b

## Turn 1: prompt sent

````text
Use the review-milestone skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.7.1/skills/orchestration/review-milestone/SKILL.md) to review milestone M1 of module APPLE-PRESENTATION. This folder is a clean checkout of commit 40319eafb334754d9753706283e9655c94bf3eb6, made for you by the loop; build and run the product from it. The done-when file is docs/plans/APPLE-PRESENTATION/DONE.json. Write the review to docs/evidence/APPLE-PRESENTATION/M1-review.md, and set the verdict fields, state and findings as the skill says; the loop sets the counts. Put captures and other evidence files in docs/evidence/APPLE-PRESENTATION/M1-review/ and link them from the review, rather than embedding them in it. Don't commit, push or change anything else: the loop checks what you changed, then integrates the review itself. Don't launch other agents. End with the skill's last line.
````

### Turn 1: last reply

````text
M1 fails review. All five items pass, but one Must Fix outside the items fails the milestone: the shipped game now shows jittered frames with nothing to smooth them.

**The Must Fix (`jitter-presented-without-reconstruction`).** The game now turns jitter on for every frame (`scene_source.rs:513`), and TAAU, which would resolve it, doesn't exist until M3. I held the camera on the valley at 640×360, the game's real render size, and compared consecutive frames. Every silhouette, the skyline, ridge and shadow edges and the ground texture change from frame to frame, by up to 208 colour codes. Scaled up to the window, that is visible edge crawl. Before M1 a held or paused view gave identical frames. The builder changed two existing tests (`lifecycle_gpu.rs` and `recovery_gpu.rs`) to absorb this, which is how it got through. The review proposes an item that would have caught it: with no reconstructor, held paused frames are byte-identical again.

**The items:**
- **D1.1–D1.3:** `./dev check` passes on the clean checkout. I read the tests and they assert what each item asks.
- **D1.4:** I traced all four cases (spawn, camera cut, device replacement, cooked asset swap) through the code on both sides. No forward drawer writes zero motion for geometry with no history.
- **D1.5:** I made 11 captures from this commit on the Mac and reviewed them as frame sequences, with native crops and values decoded from the motion view:
  - Motion matches the real image movement between colour frames, apart from the expected jitter difference of up to about 0.9 px.
  - The skyline is continuous to within 0.06 px.
  - Near objects show parallax, stars carry their slow sidereal drift, and the moving cube reads correctly.
  - Motion starts and stops on the right ticks.
  - I also ran a fast pan, low sun, far distance and a cut. I couldn't run storm or full refresh.

**Suggestions** (they don't fail the milestone):
- The motion view clamps at ±8 px, and clamped fast motion shows the same magenta that marks invalid history.
- The sky and stars ignore camera cuts and missing history.
- The cooked volume marks everything behind it as invalid.
- The mip bias is a fixed -1, correct only at native scale.
- The capture tool can't record the first frames after a cut.
- Light clusters and shadows use the unjittered view while geometry is drawn jittered.

In `DONE.json`, every item's verdict is `pass` with its review field set, M1's state is back to `in_progress`, and the one finding is listed. Nothing is committed. My raw captures and the check log are in `tmp/m1-review/`, about 13 GB, and not committed.

Files are in `docs/evidence/APPLE-PRESENTATION/`:
- M1-review.md
- M1-review/ (crops, contact sheets and my route files)

FAIL M1: 0 fail, 0 cant_tell, 1 outside the items
````

