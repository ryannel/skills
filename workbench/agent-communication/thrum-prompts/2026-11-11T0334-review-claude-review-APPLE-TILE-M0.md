# review APPLE-TILE M0

Host: claude. Role: review. Started: 2026-11-11T03:34:50Z. Session: ce8d39b4-c185-4f24-88cb-85087eef3b78

## Turn 1: prompt sent

````text
Use the review-milestone skill (the file is /Users/ryannel/.claude/plugins/cache/ryannel-skills/orchestrate/1.6.2/skills/orchestration/review-milestone/SKILL.md) to review milestone M0 of module APPLE-TILE. This folder is a clean checkout of commit c2b6e42e2102b79e5a7a0339c08283e23376ebcc, made for you by the loop; build and run the product from it. The done-when file is docs/design/modules/APPLE-TILE-DONE.json. Write the review to docs/evidence/APPLE-TILE/M0-review.md, and set the verdict fields, state and fails as the skill says. Put captures and other evidence files in docs/evidence/APPLE-TILE/M0-review/ and link them from the review, rather than embedding them in it. Don't commit, push or change anything else: the loop checks what you changed, then integrates the review itself. Don't launch other agents. End with the skill's last line.
````

### Turn 1: last reply

````text
APPLE-TILE M0 passes review. All five items pass, there are no Must Fix findings, and the milestone is set to `done`.

The strongest evidence is that I rebuilt the game from the claimed commit and its output matched the builder's saved baseline images byte for byte. That covers the route stills (both formats), the sun and night stills, and both scaled, letterboxed present checks. Every negative control failed comparison with the same changed-pixel counts the builder recorded. The mirrored cube's diff is the cube and its shadow, not noise.

- **D0.1:** the documented command passes. It refuses a missing or mismatched cooked store. The motion capture cuts once at the scheduled tick, and the noon→night→noon switch is present.
- **D0.2:** repeats are exact, and the saved baselines reproduce from a fresh build.
- **D0.3:** the named test passes (12 tests). Every production pipeline is created through the counted wrapper, and default builds call wgpu directly.
- **D0.4:** the traffic probe states its counter, units, per-encoder attribution and limits.
- **D0.5:** the Chrome moving-route command passes on two real Chrome runs. All 481 saved Chrome baseline frames check out against their recorded hashes.

I also repeated a twilight still twice as an extra low-sun case, and it was exact. I did not run storm because the game has no storm preset, and I did not run the full `./dev check`. I judged motion from frame strips, not live video.

Four Suggestions, none of which change the result:
1. **Baseline at risk:** the 481-frame Chrome baseline that M1 needs, and the 2.4 GB of capture sources, exist only in the builder's worktree. The evidence README gives the path as plain `tmp/g3t-m0`, and there is no backup. Removing that worktree would lose them.
2. **Weak-light control:** zeroing the 1000 cd light lets a 250 cd light take its cluster slot. The control compares the two lights rather than removing one, though it still proves the comparison catches the change.
3. **Existing look issues M0 doesn't touch:**
   - The night sky is flat grey.
   - The sun still has a hard step between terrain bands.
   - In the twilight still, the sphere and rock show no visible contact shadow and look like they float.
   - The foreground blurs heavily while the camera moves fast.
4. **No storm case:** the project settings list storm as an edge condition, but no preset exists.

Files are in `docs/evidence/APPLE-TILE/`:
- `M0-review.md`
- `M0-review/` (captures)

The only other change is the verdicts and state in `docs/design/modules/APPLE-TILE-DONE.json`. Nothing is committed.

PASS M0
````

