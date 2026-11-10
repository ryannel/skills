# Friction log: s6-icons-taste-v2

Lead: Claude Code (Opus 5.5) as a subagent, running inside the Claude desktop app's agent process. Every loop command
ran with `ORCHESTRATE_HEADLESS=1` through `tools/loop.sh`, which records the raw output under `out/raw/` and the
result line in `out/loop-results.jsonl`. Hosts per the brief: Claude planner, one Claude builder, Codex reviewers.

Severity words: blocked, wasted (time or tokens), confusing, nitpick, worked well.

## Entries

### 1. Starting point was clear (worked well)
README "Start here" step 1 and build/SKILL.md both name `LOOP plan --worktree <repo> --task "<owner's words>"` for a
repo with no ORCHESTRATE.md, and plan-module says a loop planner takes the safest reading and lists its assumptions.
So the first command needed no guessing. I passed the owner's ask verbatim and told the planner nothing else (hosts are
given to the loop by flags, not to the planner).

### 2. Planner: PLANNED first turn, a sound taste-led plan (worked well)
`plan --host claude --task "<owner's words>"` returned PLANNED in one turn, 6 min wall, usage input 71k / cached
800k / output 34k, `cost_usd` 1.44 (list-price estimate). Two milestones as asked: M1 three variants of sun + high
tide with an `attended` pick item (M1.5), M2 the eight icons plus preview. The M1 bar follows the proofs.md rule
("variants held only to the floor ... full look judged from M2 on"), which fixes the v1 trap where "each variant"
had to meet the look. The planner wrote the Check script itself (`tools/check_icons.py`) so builders aren't graded by
their own checks, and listed its assumptions (1.5kb = 1500 bytes, names, crescent moon). Good.

### 3. Planner chose `Review host: same`, and `next` points the design review at the builder's host (confusing)
ORCHESTRATE.md came back with `- **Review host:** same`, and the PLANNED result's `next.command` is
`agent_loop.py review --module ICONS --milestone design ... --host claude`. build/SKILL.md says "Run each review on a
different host from the one that built the milestone, when two hosts work", and README's step 2 is silent on host.
The planner had no way to know two hosts are available (headless, the owner wasn't asked), so it took "same". A lead
that just runs `next` verbatim gets a same-vendor design review. I override with `run --review-host codex`.
Expected: the plan template defaulting to `other` when both CLIs are installed, or `next` omitting `--host` so the
profile/default decides. Cost: none, if the lead notices.

### 4. The pick depends on an owner command (`owner answer`) that no agent can type (expected stop, noted early)
The plan's M1.5 `attended` text tells the owner to run `agent_loop.py owner answer ... --text '<pick>'`. Under this
test's rules that is a stop: the lead can't type it. Logged now so the cost of this stop is visible when M1 gets there.

### 5. `quota` attributes another repository's ICONS module to this one (suspected bug, confusing)
`agent_loop.py quota --worktree <this repo>` before any build here printed
`ICONS M1 (open): under 0.1%-0.1%, 5 turns, 0.3 builder-h so far`. Nothing had run on ICONS M1 in this repository;
the v1 scenario (s4-icons-taste) has a module with the same name. The per-milestone line seems keyed by module name,
not repository. Verdict line was fine: "Too little data ... 46% is left until the reset in 104 h."

### 6. Codex design review: DESIGN CHANGES with two real, reproduced blockers (worked well)
`run --host claude --review-host codex` ran the owed design review first on Codex (gpt-6.1-sol, medium) inside a 100 s `run`, 1
turn, input 39k / cached 180k / output 3.7k. Both blockers were demonstrated with counterexamples run against the
planner's own checker: (1) the "contract floor" check accepts child-level stroke settings, butt caps and missing
width/height; (2) the preview check passes a page with no SVG at all, only path strings in a comment. Both are exactly
the "proof that wouldn't catch a convincing fake" the done-when reference warns about. The result's `next` was a
ready-to-run `plan --task 'Revise ICONS's design and plan as docs/evidence/ICONS/design-review.md asks'`, by:
planner. Clear hand-off; I ran it as given.

### 7. Design revision: PLANNED in one turn, both blockers fixed (worked well); `next` again says `--host claude`
Planner revision 2 min 45 s, input 58k / cached 640k / output 17k, cost_usd 0.94. It fixed the checker (logged as the
profile requires), added a rendered-page inspection to M1.4, and took the advisory. Its report worried "this worktree's
branch is one commit behind main ... the loop needs to merge them": the loop handled it (landed 9fe79d4 on main), so
that sentence was noise for the owner. `next.command` again named `review ... --host claude` despite the first design
review having run on codex: `next` follows the profile's `Review host: same`, not the host the lead used last.

### 8. Second `run`: DESIGN OK, then M1 built in one builder turn and BLOCKED on the pick, as designed (worked well)
355 s for the whole `run`: the Codex design review (input 43k / cached 223k / output 3.9k) said DESIGN OK, then the
Claude builder drew three hands of sun + high tide, a generator (`tools/gen_directions.py`, seeded), the index page and
evidence captures, in ONE turn (input 69k / cached 1.2M / output 23k, cost_usd 1.25). It did every non-attended item
first, then stopped `BLOCKED` naming M1.5, exactly as done-when.md says ("Builders do every other item first and
then report these together"). `LOOP check` agrees: M1.1, M1.4 and Check pass. The BLOCKED result's `next` was the exact
`owner answer` command, `by: owner`, with `then` naming the `run` to resume, and an explicit warning not to relay the
answer through `run --message`. This is the clearest owner hand-off in the suite.

### 9. The owner pick can only be delivered by a terminal-typed owner command, so an unattended run ends at M1 (blocked)
What I tried: deliver the owner's pick for M1.5. The only route is
`agent_loop.py owner answer --module ICONS --milestone M1 --item M1.5 --worktree <repo> --text '<pick>'`, which
`owner_confirm` refuses without a tty (`error: owner commands need the owner at a terminal; run it yourself, outside
any agent`). My one attempt to run it (stdin from /dev/null, to record the refusal text) was itself denied by this
session's permission classifier as a security-weakening action, so I quote the refusal from the source
(agent_loop.py `owner_confirm`) rather than from a run. build/SKILL.md's BLOCKED row offers the lead "If you can supply
what unblocks it from the files, do, then run `LOOP unblock`", but the pick is by definition not in the files, and the
loop says not to use `--message`. No other module or milestone is ready (M2 follows M1), so the build stops here:
1 of 2 milestones built, 0 accepted. This is the designed behaviour, and it's right that an agent can't make the pick.
The cost is that a taste-led project can never get past its first milestone without a human at a terminal, which the
README does say ("typed by you at a terminal"). Wished for: a way the owner can answer from where they are (the Codex
or Claude app, a file they edit and commit, a signed note) so a lead running on a phone-followed session isn't stuck.

### 10. The owner's view of the variants isn't produced for the owner (wasted time, small)
The builder's evidence is under `docs/evidence/ICONS/M1/` and the page is `directions/index.html` at 24/48 px. To
judge "does this look hand-inked" I had to render my own enlarged sheet (`out/owner-look/m1-big.png`): at 48 px the
difference between "a slow bend" and "an even sine wave" is a few pixels. A one-line "open this to pick" pointer to a
large-size comparison would make the owner's single sitting faster. Nitpick-to-moderate for taste work.

### 11. `profile`, `ready`, `status`, `check`, `cost` print multi-line JSON or text; the result-line contract is `run`/`review`/`plan` only (nitpick)
README says "Every result is one line of JSON". `ready` and `check` print an indented multi-line object, `status`
prints text, `report` printed its one-line result twice. My wrapper (which takes the last line starting with `{`)
recorded `{` for these until I re-parsed the raw logs. Harmless for a human, a trap for a lead scripting the loop.

### 12. `report` lists only the latest design verdict (nitpick)
The generated report's Verdicts section shows "ICONS design: ok" and links `design-review.md`; the first review
(DESIGN CHANGES, two blocking findings, kept as `design-review-1.md`) isn't listed, though it's the more useful verdict
to spot-check for reviewer calibration. I added it in the lead's notes by hand.

### 13. What worked well overall
- Three loop commands took an empty repo to a design-reviewed plan and a built first milestone, with every hand-off
  carried by `next`. I never had to read agent_loop.py to know what to run.
- Cross-vendor review caught real proof holes before any build was spent on them.
- The taste-led shape (variants held only to the floor, owner pick as anchor for M2) is exactly the fix for v1's
  "each variant must meet the look" trap.
- Total spend to this point: 5 turns, 282k input / 3.0M cached / 82k output tokens (`LOOP cost`), $3.63 list price on
  the Claude side; about 15 minutes of wall clock.
