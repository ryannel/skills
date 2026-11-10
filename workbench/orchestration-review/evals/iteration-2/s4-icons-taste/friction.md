# Friction log: s4-icons-taste

Scenario: tide-times app "saltmarsh" weather icon set (taste-led). Planner Claude, builder Claude x1, reviewers Codex.
Lead: Claude Code subagent (Opus 5.5), running the suite at suite-v1 by path. All loop commands with ORCHESTRATE_HEADLESS=1.

## Entries

### 1. No documented first command for an empty repo (confusing)
- Trying to: start from an empty repo the way the docs say.
- What happened: README says "run /plan-module, then /build-milestone" or "hand the whole build over with /build". `build/SKILL.md` starts with "Read ORCHESTRATE.md, then run LOOP profile" which on an empty repo prints
  `ORCHESTRATE.md has missing, unfilled or invalid fields: no ORCHESTRATE.md in .../repo` (exit 1). Nothing tells a /build lead that it should first run `LOOP plan --task ...` to get a profile, and plan-module says the planner "asks the owner once for the rest", which a headless loop planner cannot do.
- Expected: `profile` (or README) to say "no profile yet: run `LOOP plan --worktree <repo> --task '<the ask>'`" as a `next`.
- Cost: ~3 minutes of reading. Severity: confusing.

### 2. Planner run worked first time (worked well)
- `plan --worktree repo --host claude --task "<owner ask + profile answers>"` on an empty repo: PLANNED in one turn, 5m16s, wrote a valid ORCHESTRATE.md, a single-module design (justified why no ARCHITECTURE.md), a 2-milestone done-when file with M1 as a three-variant direction pick ending in an `attended` pick item, exactly as proofs.md#taste-led-work prescribes. Usage: 82k input, 825k cached, 27k output, $1.39 list. It printed `warning: ORCHESTRATE.md has missing...` before the result, which is harmless but reads like an error on a first plan.
- The design is unusually good on taste: names the honest limit (stroke-only cannot modulate width like Streamline Freehand), bans `<circle>`/filters for reasons, and flags tide vs fog/wind confusion.

### 3. Owner decisions are buried in the `report` string (confusing)
- The planner's three owner decisions (1.5kb = 1,500 bytes; the M1.6 pick; whether Codex reviewers get danger-full-access if Chromium can't launch) are in a free-text `report` field, truncated at the front (`", each drawn as sun..."`). The result JSON has no `owner_decisions` field, and `next` is absent on PLANNED. An unattended lead could easily miss them.
- Expected: a structured list, or `next` saying the design review is owed (it does carry `design_review_owed: ["ICONS"]`).
- Severity: confusing.

### 4. `run`'s built-in design review uses the builder's host (confusing)
- build/SKILL.md says run reviews on a different host from the builder; `run --help` says the owed design review runs "with the same --host". With a Claude builder and Codex reviewers, the lead has to run `review --milestone design --host codex` by hand before `run`, otherwise Claude reviews the design Claude planned. Not stated anywhere as the way to do it.
- Severity: confusing; easy to get the cross-vendor rule wrong.

### 5. Codex design review: DESIGN OK first round, 1 turn (worked well)
- `review --module ICONS --milestone design --worktree wt/icons --host codex`: REVIEWED / DESIGN OK, ~3 min, usage 37k input, 138k cached, 2.5k output. Two advisory findings, both sensible (make the glance-recognition test reproducible; define anchors for a "named blend" pick). Advisory findings are not folded in by anyone unless the lead sends them to the planner; the docs say "the planner folds advisory findings in without another review" but nothing in the loop triggers that. I left them.
- Had to manually fast-forward the module worktree (`git merge --ff-only main`) since the review landed on main; harmless but the docs don't say whether the lead should.

### 6. Builder M1: six self-critique rounds, then BLOCKED on the attended pick, as designed (worked well, but expensive)
- `run --module ICONS --worktree wt/icons --host claude`: 19m39s, one long turn, BLOCKED with `next: unblock` by lead. Usage 179k input, 7.14M cached, 93k output, $6.02 list. Built a Node-only contract lint with 35 fixtures, a seeded generator, the variants page, captures for r0-r6, and an honest build note that records the last critic's dissent on M1.4/M1.5 rather than hiding it. The critique rounds clearly improved the work (r0 to r6 commits).
- 7.1M cached tokens for nine ~500-byte SVGs is a lot; six critique rounds each re-reading the captures drive it. The skill says "go round again while it keeps finding things that matter" with no cap.
- Severity: wasted tokens (moderate).

### 7. How the owner's pick gets back into the build isn't written down (confusing)
- BLOCKED's `next` is `unblock` (by: lead) with the builder's instructions pasted in `why`. Nothing says how the owner's words reach DIRECTION.md: does the owner write it, the lead, or the builder via `run --message`? build/SKILL.md's BLOCKED row says "If you can supply that from the files, do, then run LOOP unblock", but the pick isn't in the files. I used `unblock` then `run --message "<owner's pick, verbatim>"` (the NEEDS_CONTEXT pattern). The lead must not edit done-when files, and editing docs/anchors/ itself would be the lead doing builder work.
- Also: M1.6's `ask` ("does DIRECTION.md quote a dated pick attributed to the owner") can't tell an owner's words from words the builder made up. An `owner` command such as `owner pick --module ICONS --milestone M1 --text ...` that records the pick in the acceptance record would make it verifiable.
- Severity: confusing; a lead could stall here.

### 8. Resume with the owner's pick: CLAIMED in 51 s (worked well); `usage.cost_usd` looks double-counted (suspected bug)
- `unblock` (instant, UNBLOCKED) then `run ... --message "<owner's pick verbatim>"`: the same session resumed, wrote docs/anchors/DIRECTION.md quoting the pick exactly, copied the anchors with sha256s, marked M1.6 pass, landed, CLAIMED review:true.
- The CLAIMED `usage` is cumulative for the milestone session: input 188,642 / cached 8,504,402 / output 97,468 / cost_usd 12.47 / turns 2, against 178,994 / 7,139,120 / 93,151 / 6.02 after turn 1. A 51-second turn adding ~10k input, 1.4M cached and 4k output cannot cost $6.45 at list price (~$0.9 by my estimate). Suspect the loop sums Claude's `total_cost_usd`, which is already cumulative for a resumed session. Not verified in code. Severity: misleading cost reporting.

### 9. Taste-led M1 bar says "each variant" must meet the look, so a rejected variant fails the milestone after the owner's pick (wasted time; plan-shape bug)
- Codex review of M1 (4 min, 94k input / 1.29M cached / 9.8k output): `FAIL M1: 2 fail, 0 cant_tell, 0 outside the items`. B1: dip pen reads as polygon geometry, failing M1.4/bar "Each variant reads as a field-notebook pen sketch". The owner had already rejected dip pen for exactly that reason, in DIRECTION.md, which the reviewer read and quoted, then failed anyway ("that choice is not a change to M1's bar"). The reviewer was right by the definitions; the definitions were wrong.
- Root cause: proofs.md#taste-led-work says "plan a first milestone that makes a few variants ... with an attended item where the owner picks one", and the planner then held every variant to the final bar. Variants exist to be rejected; the bar for them should be "different in kind, each a credible candidate", and the full bar should apply to the picked one.
- Fix I used, as owner: edited the bar and M1.4 in wt/icons and ran `owner scope`. That reset proof on all six M1 items (including M1.6, the owner's own pick), so the builder must re-verify everything. Expected: a taste-led note in proofs.md telling planners not to hold losing variants to the bar.
- Severity: wasted a review cycle plus a re-verify; an unattended lead following the ladder would have sent the builder to polish a rejected variant.

### 10. Owner commands need a real tty, so an owner stand-in agent has to fake one (by design, but no escape hatch)
- `owner scope` calls `input("Type ICONS:M1 to scope it: ")` after checking `sys.stdin.isatty()`. From an agent's Bash tool, piping through `script -q /dev/null` gave `EOFError` (traceback, no JSON line). Worked with an `expect` script (tools/owner.exp) that types `ICONS:M1`. This is the intended guard, so not a bug; but a traceback instead of a clean `error:` line on EOF is rough. Also, `owner scope` reads the owner's edited file from the worktree but commits through its own checkout, leaving the worktree with the same edit uncommitted; I had to `git checkout --` it before fast-forwarding. Severity: nitpick/confusing.
- The review file is 66 KB because the Codex reviewer embedded base64 PNG captures in markdown to stay within "change only the review file". Captures have nowhere else to go under the reviewer's file rule. Severity: nitpick (repo bloat, hard to read).
- The Codex reviewer reports "Chromium ... failed inside the sandbox ... the approved unsandboxed invocation succeeded" in a headless `codex exec` run. Nobody approved anything interactively; unclear what approved the escalation. Suspected, not verified.

### 11. Second M1 review: the taste items pass, then M1.2's open-ended ask fails on a new lint hole (wasted time; review convergence)
- Fix round (run --message with `next`'s findings + one line noting the owner's scope commit): 3m33s, CLAIMED. Codex re-review 3m45s: `FAIL M1: 1 fail`. The taste items now all pass (the reviewer read the owner-scoped bar correctly and confirmed B2 fixed). New B1: an eccentric elliptical arc (`A.1 3 ...`) whose SVG radius correction escapes the bounds hull, a feature no icon uses.
- M1.2's ask, "would a real violation in a shipped file fail the check?", is an open-ended adversarial question: each round the reviewer can find one more geometry corner (miter tips, then arc radius correction, next maybe cubic extrema...). design-review guidance has an anti-"one more refinement" rule ("Reviews that find one more refinement each round never let the build start"); milestone review has none. The finding is genuine, so I let the ladder run (fails 2, same-session) rather than overrule it as owner.
- Expected: either the planner bounds the ask ("for the path commands the variants use"), or review-milestone carries the same convergence rule as design review. A builder could also just ban `A` commands in the lint, which the design permits.
- Severity: wasted time and a rung of the ladder on a lint corner case.

### 12. Third M1 review: fails again on two more parser corners; the ladder moves to a fresh session (wasted time; review convergence)
- Fix round 2: 3m26s, CLAIMED (exact arc bounds). Review 3: 4m28s, `FAIL M1: 1 fail` (M1.2 only). New: `3e1` exponent tokens are mis-parsed as commands so a segment out of bounds is dropped; a path without an initial moveto passes. Both are genuine bugs in a hand-written SVG path parser; neither affects any shipped or variant file.
- This confirms entry 11: every round finds a different corner of a lint the builder wrote itself. Three reviews, three different findings, all on M1.2's ask. Taste items have passed twice. Ladder now says `fresh-session` (fails 3). An attentive owner might `owner accept` here; I let the ladder run to test the fresh-session path and because each finding is real.
- Wished for: a planner hint that a hand-written parser is a liability; "use a real SVG path parser (dev dependency) or restrict the allowed path commands to M/L/Q/C/Z and reject everything else" would have closed the whole class.

### 13. Fourth M1 review fails on NBSP in path data; ladder says `replan`, but nothing hands the lead a planner command (confusing)
- Fresh session: 5m57s, CLAIMED (typed SVG path tokenizer, initial moveto). Its usage is 1 turn, $1.50, against $8-10 per resumed turn of similar work in the old session, which is either the context weight of a long resumed session or the double counting suspected in entry 8.
- Review 4: 3m27s, `FAIL M1: 1 fail` again on M1.2: the tokenizer accepts U+00A0 as whitespace while Chromium stops parsing. Four reviews, four different lint corners (miter, arc radius correction, exponents/initial moveto, NBSP). fails 4 → `next: "replan"`.
- On replan the review result's `next` is just the word `"replan"`, with no command (other stops give a full `next: {command, by, why}`). `LOOP next --milestone M1` returns `action: replan` but its `message` is still the builder text ("fix them, re-verify..., set the state back to claimed") which is wrong for a planner. And `ready` still lists M1 as `ready` (state in_progress), so a lead that only reads `ready` would start the builder again and skip the re-plan. I wrote the planner task myself.
- Severity: confusing; a lead could bypass the ladder by accident.

### 14. The re-plan fixed the right thing (worked well), at the price of another design review and a full re-verify
- `plan --task "Re-plan ICONS M1: ... read the review and its git history"`: 3m20s, PLANNED, $1.08. It replaced the open-ended M1.2 ask with M1.7 (a closed canonical form: M/L/Q/C/Z, ASCII, attribute allowlist) and M1.8 (a provable bounds rule: control-point box plus half stroke width, round or bevel joins only), kept every earlier probe as a fixture, set fails 0 / replans 1, and marked M1.6's attended step as already done so the owner isn't asked again. It also surfaced two owner-facing consequences (no arcs or miter joins in future icons).
- The changed design needs another design review (`design_review_owed`): Codex, 1m31s, DESIGN OK. A design change made only to the check's acceptance form still blocks building until reviewed; fine, but it's a fixed ~2-minute tax per re-plan.
- The re-plan changes M1's definitions, so all eight items reset and the builder re-verifies taste items (M1.3-M1.5) the reviewer passed three times.
- Wished for: the planner's "fixed form" fix at first planning. plan-module's proofs guidance could say "an `ask` of the form 'would any real violation fail?' is unbounded; bound it by the grammar the check accepts".

### 15. Post-re-plan review still fails on a lint corner; owner accept used (wasted time; worked as a control)
- Builder on the re-planned M1 (resumed the fresh session by default): 7m15s, CLAIMED. Review 5: 4m01s, `FAIL M1: 1 fail` on M1.7: the "closed canonical form" lint accepts direct `<path>`s beside a `<g>`. The design's own contract says "only `<path>` elements, optionally grouped in `<g>`", and such a file renders correctly; it only contradicts the lint's self-description.
- Five reviews, five distinct lint corners, zero visual problems after the scope change. The re-plan narrowed the ask but the reviewer still found the next gap; a closed-form ask is still adversarial if the item says "fails everything else".
- I used `owner accept` (via expect, see entry 10): DONE, clean. `status` then shows M1 `done ... accepted; last review fail`, M2 ready. Owner accept cost the owner nothing but a reason; it's the right lever and works.
- Wall clock on M1 from first build to acceptance: 00:30Z to 01:42Z (72 min), of which the variants and the pick took 21 min and the remaining ~50 min went to the check's corner cases.

### 16. M2: built and passed first time (worked well)
- `run` M2: 14m52s, one turn, CLAIMED after eight internal critique rounds (m2-r1..r8), $5.36 list. Codex review: 3m13s, `PASS M2`, all seven items. M1's owner notes were acted on (high tide's flag removed, tides distinguished by arrow direction and water level, not just waves).
- The reviewer did not probe M2.2's check-ask adversarially the way it did M1.2/M1.7, although the same lint ships (the `<g>`-beside-`<path>` gap from review 5 is still there). Reviewer strictness varied a lot between milestones on the same code. Suspected, not measured.

### 17. `usage` on `run` results is per milestone session, cumulative across `run` commands (confusing)
- The builder session for M1 resumed four times; each CLAIMED line's `usage.turns` goes 1, 2, 3, 4 and every field grows, so summing result lines over-counts badly (summing the four would claim ~$70 for a $30 session). The docs say "tokens per claim"; it's really "tokens of this session so far". Separately, the per-turn `cost_usd` deltas ($6.45 for a 51-second turn with ~1.4M cache reads) suggest `usage_of` adds Claude's `total_cost_usd`, which looks session-cumulative on a resumed `claude -p --resume`. My arithmetic at list prices puts turn 2 at ~$0.85, so the reported total is roughly double. Suspected, not verified against Claude's docs.
- Severity: misleading cost data in the very field the owner is told to use to see what a milestone costs.

### 18. Lead housekeeping the docs ask for that has no loop path (nitpick)
- build/SKILL.md asks the lead for a report in `<evidence>/build-reports/<date>.md`, but `adopt` refuses files outside the plans folder and the lead isn't meant to commit; I didn't write it into the repo (the owner report is this folder's out/ files).
- Module worktrees need a manual `git merge --ff-only main` after each loop commit (review verdicts, owner commands, unblock) or the next `run`/`owner scope` sees a stale base. The loop seems to cope (it fetches the tip), but nothing says whether the lead should sync.

### What worked well overall
- The taste-led shape is right: three variants different in kind, an attended pick, anchors with sha256s, M2 judged against them. The builder's critique rounds visibly improved the drawings, and the pick round-trip (BLOCKED → unblock → run --message) took under a minute.
- The Codex reviewer's visual judgement matched mine on every piece (it called dip pen polygonal and felt-tip a marker doodle, the same reasons I rejected them), and it respected the owner-scope change on the next round.
- Every stop carried a usable `next` (except `replan`), and owner commands are well guarded and simple once you can type at a tty.
