# Friction log: s2-slug-codex (all-Codex hosts, headless)

Times are local (CET). Severity: blocked / wasted / confusing / nitpick / good.

## 1. Starting from an empty repo: which entry point? (confusing, ~5 min reading)
- Trying to: go from the owner's one-line ask to a planned project with a Codex planner launched by the loop.
- README's "two speeds" says run `/plan-module` in a chat, or "hand the whole build over with `/build`". `build/SKILL.md`
  assumes a profile exists ("Read ORCHESTRATE.md, then run LOOP profile"). Nothing in build/SKILL.md says what the lead
  does when there is no ORCHESTRATE.md and no plans.
- What did help: `ready` on the empty repo returned `next: plan --task 'Plan the project'` (by: lead). Good signpost.
- But `plan --task` is the only channel for the owner's ask. plan-module says "ask the owner once for the rest", which a
  headless planner can't do, and the brief says to give agents "file paths and nothing else". Where the owner's own words
  should live (a purpose doc? the task text?) isn't stated. I put the ask verbatim into `--task`.
- `profile` on the empty repo: `ORCHESTRATE.md has missing, unfilled or invalid fields: no ORCHESTRATE.md in <repo>`, exit 1.
  Clear enough, but "missing, unfilled or invalid fields" for a missing file reads oddly.

## 2. `ready` prints pretty-printed multi-line JSON, `run` is documented as "one JSON line" (nitpick)
- My logging wrapper took the last line (`}`). Had to parse from the last line starting with `{`.

## 3. Readout check #1, during planning: `quota` and `status` (confusing)
- `quota --worktree repo` printed 325 lines of pretty JSON (fit weights, "plausible" weight sets, per_mtok ranges,
  other_windows...). The one sentence an owner wants, `forecast.verdict`, is the 3rd-last field:
  "Quota lasts: other use need about 0% (at most 0%) before the reset in 105 h, and 46% is left."
  Usable only if you know to scroll to the bottom. `used_percent: 54.0` is at the top and is clear. Fields like
  `fit.plausible[].weights`, `rms_pct`, `rise`, `behind_mb` mean nothing without reading codex_quota.py. No
  human-readable mode (`--brief`) exists. Also the verdict grammar "other use need about 0%" is garbled.
- `use_this_window.loop_pct` (~3%) counts every loop on this Codex account (other scenarios, thrum), not this repo's,
  though the field name suggests "this loop". Can't tell from the readout.
- `status --worktree repo` while the planner was running: printed only the missing-profile warning and nothing else,
  exit 0. No "planner running" or "no modules yet" line. An owner checking in sees nothing at all. Expected at least
  "no modules planned; a plan session is running (pid, since HH:MM)".

## 4. Planning worked first time (good), 222 s, one turn
- `plan` returned PLANNED with a sensible profile, design, 2 milestones, 7 items; usage 83.5k uncached / 345k cached / 9.4k out.
  `design_review_owed: ["SLUGLINE"]` and the result's compact `quota` field (used, reset, burn, verdict) is exactly the
  owner-sized readout that `quota` itself lacks.
- The result still began with `warning: ... no ORCHESTRATE.md` (printed at start, before the planner wrote one). Harmless
  but alarming on a successful run.
- The planner made product choices on its own (ASCII-only, `x` fallback for empty slugs, batch-local uniqueness, existing
  file read-only, exit 2 on errors). Reasonable, and listed in its report; nothing was flagged for the owner.
- `plan` says "Runs a fresh planner in a clean worktree" but `git worktree list` showed only the main checkout while it ran.

## 5. Where to put the module worktree (nitpick)
- build/SKILL.md: "Give each module its own worktree ... in a folder git ignores". The fresh repo has no .gitignore, so
  following it literally means the lead commits a .gitignore. I put it outside the repo (`../wt/SLUGLINE`) instead.
  A one-liner like `LOOP worktree --module M` would remove the guesswork.

## 6. `run` did design review + M1 build + claim in 203 s (good), but the result hides the design review (confusing)
- `run` result: `CLAIMED`, review: true, usage 35.6k/317k/5.9k. The design review it ran first (DESIGN OK, its own
  24k/163k/2k tokens) is not mentioned in the result line at all; I only found it in `git log` and in
  SLUGLINE-ACCEPTED.json `.design`. An owner tallying cost from result lines would miss it. Expected a `design_review`
  field on success too, not just on a non-OK outcome.
- A CLAIMED result with review: true carries no `next` (other stops do). The table in build/SKILL.md covers it, and
  `ready` gives the exact review command, so minor.
- Odd-looking commit: `refs/orchestrate/claims/SLUGLINE/M1` points at a commit whose message is
  `Ryans-MacBook-Pro.local:/private/tmp/.../repo/.git`. It's the claim marker, but in `git log --all` it looks like junk.
- Plan commit subject is the first ~60 chars of my --task text ("Plan: Plan the project. The owner asked, verbatim: \"need a tiny py").

## 7. Readout check #2, after M1 claim: `status` (good) / `ready` (ok)
- `status` is the best readout: one line per milestone, state, fails, items passing, "review owed". Understandable cold.
  `--module` printed the same thing as plain `status` for a one-module project.
- Missing from it: anything about cost (tokens per milestone, quota) or what is running now. Cost lives only in result
  lines, ACCEPTED.json, and the 325-line `quota` dump.

## 8. M1 review: PASS in 114 s, thorough (good)
- Review file is ~1,080 words: a pre-declared checklist, literal API cases (İ, ﬃ, U+200D, suffix 9->10/99->100), and a
  seeded 3,000-case differential test against an independent reference. It even owned up to a bug in its own harness.
  This is a real review, not a rubber stamp.
- `status` while the reviewer was running still said "review owed": nothing shows a review is in progress (same as #3
  for planning). An owner can't tell "waiting for someone to start it" from "running now".
- The result's quota verdict now reads: "Quota lasts: the 1 open milestones and other use need about 0% (at most 0%)".
  "0% (at most 0%)" for a whole open milestone is not believable, even if this project is tiny: four headless Codex
  sessions so far used ~187k uncached + ~1.1M cached input. Either headless `codex exec` rollouts aren't being costed
  or the rounding hides it. Plural "1 open milestones".
- REVIEWED PASS carries `next: null`. Fine, but "next: run M2" would save a `ready` call.

## 9. Readout check #3, mid-M2: `quota` milestones section (correction to #8; confusing)
- Digging into `quota`'s `milestones` array: M1 cost 0.01-0.02% of the weekly limit (2 turns, 1 round, 0.1 builder-hours),
  and `forecast.per_milestone` is 0.01-0.04%. So the "about 0% (at most 0%)" verdict is integer rounding of a real,
  tiny number, not a costing gap. I retract the suspicion in #8. But the verdict sentence should keep one decimal for
  small values, and the per-milestone cost, which is the most useful owner number in the whole dump, is buried in a
  325-line JSON with no summary line. M1 tokens from result lines: design review 24k/163k/2k + build 36k/317k/6k +
  review 44k/303k/5k (uncached/cached/output).
- M2 shows `pct: [0,0,0]` and `builder_hours: 0.0` while its builder has been running a couple of minutes: in-flight
  usage isn't counted until the turn ends (headless). Expected, but not labelled.

## 10. M2 claimed in 219 s, one turn (good). My own use of the product while M2 was in review
- Verified by running it (clone of main at d80a7a7): 25 tests pass; é/è/û/ï -> plain letters, ß -> ss, lowercase,
  hyphens, default 60 whole-word (30x"word" -> 59 chars), --max-length 20 cuts at a word boundary, --existing file with
  hello-world, -2, -4 gives -3, -5, -6 for three repeats and the file is untouched, args and stdin both work, bad
  file / --max-length 0 exit 2 with argparse-style errors. Imports are stdlib only.
- Product gap the whole pipeline missed (planner, design reviewer, M1 reviewer): Latin letters without a Unicode
  decomposition are dropped and split the word. `Ørsted Łódź Æsir Đorđe þorn` -> `rsted-odz-sir-or-e-orn`;
  `Ærø Café` -> `r-cafe`. The design (SLUGLINE.md line 25) explicitly chose NFKD+strip-marks and says remaining
  characters "act as separators", calling it "the supported transliteration range". So the build matches the plan; the
  plan under-read "transliterate accents". The planner marked it "no owner decision required". A plan that narrows the
  owner's words this way should surface it as an owner decision, and the design reviewer, who gets the brief, should
  test the owner's term against common inputs, not only the planner's examples.
- Debatable choices, documented in the design, not flagged to the owner: a single word longer than the limit becomes
  `x` (not truncated); a blank stdin line prints `x` and reserves it, so later blanks become x-2, x-3.

## 11. Finish: M2 PASS (139 s), `status` says "SLUGLINE: finished" (good)
- Final `status`: both milestones `done ... accepted; last review pass <UTC timestamp>`. Clear. Timestamps are UTC with Z
  while everything else the owner sees (quota reset "Sat 14 Nov 10:28") is local; mixed.
- `ready` at the end: `next: {command: null, by: lead, why: "every module is finished; plan more work ..."}`. Fine.
- Reporting: build/SKILL.md says to write `<evidence>/build-reports/<date>.md` (inside the repo) when stopping, but no
  loop command lands it, and `adopt` only takes plan files. Following the skill leaves an untracked file in the
  project, or the lead hand-commits to main, which the skill otherwise steers away from. Skipped it.
- No single readout answers "what did this build cost?". I had to sum six result lines plus the design review from
  ACCEPTED.json. A `status --cost` (tokens per milestone split build/review, plus % of weekly quota) would answer it.
- After `git worktree remove`, `git worktree list` still shows two loop worktrees under `.git/orchestrate/verify/`
  (`_PLAN` detached at the old plan commit). Internal, but visible to an owner who looks.

## Summary of what worked well
- Zero owner stops, zero failed reviews, zero INVALID/FLOOR. 16.5 min wall clock from empty repo to two accepted
  milestones, all on Codex headless.
- `ready`'s `next` with an exact command and `by:` made every lead step unambiguous.
- `status` is the one readout an owner can read cold.
- The M1 reviewer's work was genuinely independent and deep.

## Wished for
- A human summary mode for `quota` (verdict + per-milestone cost in 3 lines).
- `status` showing what is running now (planner/builder/reviewer, since when).
- A design-review prompt that asks the reviewer to test the owner's own words against common inputs (would have caught ø/ł).
