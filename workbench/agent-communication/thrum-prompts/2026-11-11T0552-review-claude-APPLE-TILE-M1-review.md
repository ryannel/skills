# thrum · APPLE-TILE · M1 review

Host: claude. Role: review. Started: 2026-11-11T05:52:50Z. Session: 4760752f-a24e-470a-bf7e-8c95e553e225

## Turn 1: prompt sent

````text
Use the review-milestone skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.7.1/skills/orchestration/review-milestone/SKILL.md) to review milestone M1 of module APPLE-TILE. This folder is a clean checkout of commit bffdc07f447d4ae207cdfb5ab29151119e278b63, made for you by the loop; build and run the product from it. The done-when file is docs/plans/APPLE-TILE/DONE.json. Write the review to docs/evidence/APPLE-TILE/M1-review.md, and set the verdict fields, state and findings as the skill says; the loop sets the counts. Put captures and other evidence files in docs/evidence/APPLE-TILE/M1-review/ and link them from the review, rather than embedding them in it. Don't commit, push or change anything else: the loop checks what you changed, then integrates the review itself. Don't launch other agents. End with the skill's last line.
````

### Turn 1: last reply

````text
M1 passes. I gave all five items a pass verdict and set the milestone to done; there are no Must Fix findings. Every result below comes from my own build and runs of the claimed commit, and every GPU run held the `gpu` lock.

- **D1.1 (recipe choice):**
  - The selection tests pass.
  - The registry digests repeat exactly across the builder's runs and mine, on the Mac and in the simulator.
  - The registry records the features actually enabled, not the ones offered, and display facts stay with the platform.
- **D1.2 (attachment storage):**
  - The storage logs show the Apple tile day depth as memoryless and the depth that stars read as stored (Private).
  - The resident-memory figures match the builder's to the byte. Apple tile saves no resident memory, because stars keep a stored depth. The design expects this, and the builder reported it honestly.
- **D1.3 (Mac output):**
  - The native recipe script passes 38 exact comparisons against the retained pre-change baselines.
  - In the real-time route sequences, all 121 samples the two recipes share have identical frames.
  - The day↔night switch shows no glitch frames.
  - The stills and motion pass my inspection list.
- **D1.4 (Chrome):**
  - All 1,924 Chrome frames captured from this commit (day and night, SDR and scene-linear) match the pre-change hashes.
  - The Wasm dependency tree contains no Apple or Metal crates.
  - The named `run_v1_showcase.py moving` check passes.
- **D1.5 (iOS simulator):**
  - The registry reports `unified_memory=false` and runs portable.
  - The lifecycle steps and a rotation to landscape and back pass.
  - Forcing Apple tile is refused with `Recipe(UnsupportedAppleTile)` rather than mislabelled as portable.

The review records five Suggestions, none of which changes the result:

1. **Weak test:** the test meant to prove "no texture or pipeline creation when switching day/night" passes trivially in the normal gate. The counters it reads are always 0 unless `creation-counters` is enabled, and `./dev check` doesn't enable it. With the feature on, the test still passes, so the claim holds today, but a regression would go unnoticed.
2. **Latent coupling:** textures are allocated from the capture variant of the graph. A future capture-only reader of depth would quietly make the normal day depth stored again.
3. **Mislabelled metadata:** Chrome scene-linear capture manifests say RGBA8 with the wrong row stride; the pixel data itself is correct.
4. **Blown-out night lighting:** the midnight route's local-light pool clips to flat white. It is identical to the pre-change build, so it isn't an M1 defect; it belongs to whichever module owns night lighting or exposure.
5. **Misleading table:** the storage report's "nominal bytes" counts the memoryless depth at full size. This makes Apple tile look about 7 MB heavier when the driver shows about 32 KB more.

I didn't rerun the full `./dev check`, which the builder's gate already covers; I did run every item's own check. Storm conditions weren't tested because the product has no storm preset.

I changed only the reviewer fields in `docs/plans/APPLE-TILE/DONE.json` and didn't commit. Bulk captures stay in `tmp/review-m1/`.

Files are in `docs/evidence/APPLE-TILE/`:
- M1-review.md
- M1-review/

PASS M1
````

