# s8-ledger-final friction log

Lead: Claude Code (Opus 5.5) agent, running headless loop commands (ORCHESTRATE_HEADLESS=1) from a Bash tool.
Suite: suite-v4/orchestration. Repo: s8-ledger-final/repo (local only, Integrate: local expected).

## 1. Empty repo: `status`/`ready` point straight at `plan` (worked well)
`status` on the empty repo printed a ready-to-paste `plan` command with `next.by: lead` and a `why` saying to include hosts, integration and checks. `quota` gave a clear verdict (45% left, other use needs ~0.8%). No friction.

## 2. Planner: one turn, 9.5 min, $2.17 list, good plan (worked well; one false alarm)
`plan --task '<owner words>'` (claude, opus high) -> PLANNED in 1 turn, 04:35:54-04:45:26. 99k input / 1.26M cached / 56k output.
Two modules, CORE M1 and REPORT M1 both startable at once (REPORT M1 against stand-in objects), REPORT M2 `needs: CORE:M1`. 39 acceptance tests in docs/acceptance/, checked against a throwaway implementation. Profile: Integrate local, Check `python3 -m unittest discover -s tests`, Review host other, Builders "CORE on claude, REPORT on codex". 10 Assumption lines, all reasonable.
- False alarm (confusing, minor): the planner's report tells the owner "`codex` isn't on the PATH here, so the loop may not be able to start the Codex builder". The loop finds Codex on its own (README/brief). The planner prompt could say the loop locates hosts itself, so planners don't raise this.
- The result line names its status `result`, not `status` (fine, just noting for anyone scripting against it).

## 3. Worktrees by hand, then two `run`s at once; each design review went to the other host (worked well)
Made `.worktrees/{core,report}` (added to .git/info/exclude) on `build/core`, `build/report` from local main, as build/SKILL.md says. `run --module CORE --host claude` ran CORE's design review on codex; `run --module REPORT --host codex` ran REPORT's on claude: `Review host: other` did the right thing with no extra flags. `loops --repo` showed both with host/model/effort straight away.
- Nit: `ready`'s `next` for the design review has no `--host` (`review --module CORE --milestone design --worktree <main>`), while the planner's PLANNED `next` carried `--host codex`. A lead copying `ready`'s line would review on the lead's own host (claude) — same host as the planner. Using `run` avoids it.

## 4. CORE design review (codex, 1.5 min, 40k in / 2.7k out) -> DESIGN CHANGES, 1 blocking: Decimal context precision (worked as designed; arguably over-strict)
Same finding as the s3 run of this ask: a 29-digit quantity, or a caller-set context of precision 4, makes a Decimal sum round, so an unbalanced txn could be accepted. Real but far from what the owner asked about. The planner prompt didn't pre-empt it even though an earlier run hit exactly this; the plan skill could carry "state the Decimal context / exactness mechanism" as a standard line for money work. `run` returned DESIGN_OWED with `next.by: planner` and a ready plan command in the CORE worktree: clear.

## 5. REPORT design review (claude, 2 min, $0.70) -> DESIGN CHANGES, 1 blocking (worked well)
Blocking: M1.1/M1.2 were proved only by the builder's own tests, so a self-consistent fake (wrong JSON keys, wrong layout) would pass M1. Fair and well argued, with two fix options. Advisories: empty-total text undefined; acceptance tests need Python 3.11 while the profile says 3.10+.

## 6. Second planner while the first runs: TAKEN now explains itself (fixed since the earlier run; still costs wall-clock)
`plan --worktree .worktrees/report --task "Revise REPORT's ..."` while CORE's revision planner ran returned at once:
`{"result": "TAKEN", ..., "by": "another planner on this repository (plan, pid 25704 in .../.worktrees/core since 2026-11-10T03:47:51Z)", "holder": {...}, "next": {"command": "...plan ... --task 'Revise REPORT...'", "by": "lead", "why": "only one planner runs per repository at a time, and another holds it (...); run this again once it stops (`loops --repo` shows when)"}}`
That is the explanation the earlier run lacked: holder, where, since when, and the exact rerun command. Good.
Cost: both modules now sit idle behind one planner — no builder can start until CORE's revision lands, and REPORT's revision can't even start. With two design reviews both returning DESIGN CHANGES (likely on a first plan), the serial planner turns the "two at once" build into a serial one at this stage. The skill mentions "give one planner both tasks" as the alternative; the loop's `next` could offer that (a combined task) since it knows both are owed. `since` is in UTC (`03:47:51Z`) while everything else I see is local time — minor.

## 7. CORE revision planner: PLANNED in 13.3 min, $2.31 list, 2 turns counted (wasted time)
04:47:51-05:01:09. Landed CORE.md/PLAN/DONE and test_core_m1.py. Its report ends with: "A background job of mine hit its time limit and was stopped. It was a disk-wide search for `agent_loop.py`...". The planner went looking for the loop script across the disk — the prompt evidently didn't hand it the path, or it didn't trust it. Planner wall-clock is what both modules wait on (item 6), so this hurts twice. 6 Assumption lines now for CORE.

## 8. REPORT revision planner ran while CORE's design review landed a record commit: planner landed fine (fixed since the earlier run)
REPORT planner 05:01:25-05:04:15 (2.8 min, $0.94). During it, CORE's re-review committed `6d7049f orchestrate: review of CORE design: DESIGN OK` to main. The planner's turn still landed (`ea45b57` + `e310f1d authorise`). In the earlier run a concurrent record commit got the planner turn rejected; that no longer happens, at least for a design-review record. (A builder *claim* during a planner turn is the case the earlier run hit; not exercised here because CORE's build started after the planner was nearly done — see later entries if it recurs.)
The planner also caught a cross-module knock-on itself: CORE's revision made seven refusals into eight, and it fixed REPORT M2.7 to match. Good.
- Confusing (could mislead): this PLANNED's `next` is `review --module REPORT --milestone design ... --host codex`, "on the host the planner didn't use". REPORT is built on Codex, so a Codex design reviewer is the same vendor as the builder — the opposite of what the owner asked and of `Review host: other`. I used `run --host codex` instead, which picks claude for the design review (as it did first time). The planner-relative rule and the builder-relative rule disagree.

## 9. CORE: design OK on re-review (codex, 34k in/3k out), then built and claimed in ONE Claude turn; CLAIMED now carries `next` (worked well; fixed since the earlier run)
`run --module CORE --host claude` 05:01:25-05:05:46 (4.4 min total incl. design review). Build turn: 50k in / 652k cached / 15.5k out, $0.84 list. Result `CLAIMED`, `review: true`, commit 01f72d4, and `next` = `review --module CORE --milestone M1 --commit 01f72d4... --host codex`, by lead, "waits for its review, on codex, the review host". The earlier run's "CLAIMED with no next step" is gone.
REPORT's design OK (claude) landed on main between CORE's code commit and CORE's claim commit; the claim still held.

## 10. CORE M1 review (codex, 3 min, 82k in / 7k out) -> PASS first time; CORE finished at 05:09 (worked well)
Thorough review: inspection list written before running, independent probes (300 generated 60-digit journals vs a scaled-integer oracle, hostile Decimal contexts), whole-diff read. `next.command: null` with a `why` saying CORE is finished and pointing at `ready`. Clear.
After this the Claude builder has nothing to do: REPORT M1 is with the Codex builder and REPORT M2 is behind it in the same module. Correct by the rules (one builder per module), just noting that the plan's "two builders at once" only overlapped for ~4 minutes of building, because both design reviews failed first and the planner was serial (items 4-8).

## 11. REPORT: design OK on re-review (claude, $0.53), M1 built and claimed by Codex in one turn (worked well)
`run --module REPORT --host codex` 05:04:37-05:10:11 (5.6 min incl. design review). Build turn 42k in / 548k cached / 8.9k out; `goal: complete`; no `cost_usd` for Codex (expected). `next` = review on claude. Fine.

## 12. REPORT M1 review (claude, 3 min, $0.98) -> FAIL, 1 blocking: tests don't pin "file order within a date" (worked well; fair)
The reviewer ran mutants against a copy of report.py: sorting same-date txns by payee, or postings by account, survived every builder test. Code is right, tests too weak for M1.3's ask. A real gap, cheaply shown, with a concrete fix. `ladder: same-session`, `next` = `run ... --message '<findings boilerplate>' --host codex --review-host claude`, ready to paste. Followed it verbatim.

## 13. REPORT M1 fix (codex same session, 2.3 min) -> CLAIMED; re-review (claude, 1.9 min, $0.69) -> PASS (worked well)
`next` after PASS: `run --module REPORT ... --host codex --review-host claude`, with a `why` explaining that `run` fast-forwards a clean worktree itself. Good touch — that answered the question I was about to have.
- Nit on usage: the resumed claim's `usage` is the session running total (113k in / 1.88M cached / 22k out, `turns: 2`), so the fix turn alone isn't visible on the line; documented in the README hosts table, `cost` adds it up.

## 14. `cost` mid-run (worked well; one observation)
Clear per-phase split. Planning: 3 turns, $5.42 of the $9.15 Claude list total so far — planning (incl. two design revisions) is ~60% of Claude spend on a project this small. "planning: 3 turns" while the planner results said turns 1, 2, 1 (=4): the CORE revision reported `usage.turns: 2` but `turns: 1`. Minor inconsistency.

## 15. REPORT M2 built and claimed by Codex in one turn (2.5 min, 49k in / 5.6k out) (worked well)
05:18:27-05:21:00. While its claude review ran I used the product myself at the claimed commit (separate detached worktree `s8-ledger-final/verify`): see result.json `verdict`. It does what was asked.
- Nit for my own lead work: I first wrote `L="python3 -m ledgerlite"; $L ...` and zsh refused to split it — the very trap the README warns about for `LOOP`. The README's warning is worth keeping.

## 16. REPORT M2 review (claude, 2.75 min, $0.94) -> FAIL, 1 blocking: BrokenPipeError traceback when piping into `head` (worked well; fair against the bar)
The bar says "never a traceback"; `register Assets --json | head -c 100` on a 2,000-txn journal printed one. Fix is standard. Four advisories (non-UTF-8 stdout, `-f ""` message, wide chars, `--json` position). A reviewer finding a real edge the acceptance tests missed — the cross-host split is earning its keep. Followed `next` (same-session) verbatim.

## 17. REPORT M2 fix (codex same session, 2.2 min) -> CLAIMED (worked well)
My own check at 206f2ff: piping 3,000-txn `register` into `head` now prints no traceback, but one stderr line `ledgerlite: stdout: broken pipe (output reader closed)` and exit 1. Not what json.tool/hledger do (silent), but within "never a traceback". Suite 37 OK; both acceptance files OK.

## 18. REPORT M2 re-review (claude, 2.1 min, $0.72) -> PASS; whole build accepted at 05:28:51, 53 min after the first command (worked well)
`next.command: null`, "REPORT is finished". `status` shows all three milestones done/accepted.

## 19. Final report: `report --write` then `adopt` (worked well; nits)
`report --write` wrote the factual half (closed, verdicts with links, all planner Assumption lines, cost, the "graded examples hold 0 verdicts, spot-check every one" flag) and `next` pointed at `adopt`. I appended the lead's half; `adopt` landed it as one commit. Smooth.
- Nits: timestamps in the report are UTC (`04:09:03Z`) while the run, `status` hints and the owner's clock are local — an owner reading "accepted 04:28Z" at 05:30 CET has to convert. "build sessions: 3" is ambiguous next to "two builders" (it means three builder sessions: CORE M1, REPORT M1, REPORT M2). The report has no section for "how many builders ran / which app / which path", which build/SKILL.md asks the lead to cover; easy to forget.

## 20. Cleanup leaves the loop's verify worktrees registered (nitpick, still present)
After removing my worktrees, `git worktree list` still shows `.git/orchestrate/verify/{_ADOPT,_PLAN,CORE,REPORT}` as detached worktrees. The skill says to remove worktrees whose work has landed but also not to touch the loop's lock files; nothing says whether these are mine to remove. I left them. Same as the s3 run.

## 21. The three points the earlier run hit (summary)
- Planner turn rejected when another module's record commit landed during it: **not reproduced**. REPORT's revision planner landed although CORE's design-review record commit hit main mid-turn (item 8). A builder *claim* commit during a planner turn did not occur in this run (timing), so that exact case is untested here.
- `CLAIMED` with no next step: **fixed**. Every CLAIMED carried `next` with the review command on the right host (items 9, 11, 13, 15, 17).
- Second planner turned away with no explanation: **fixed**. TAKEN names the holder (pid, role, worktree, since) and gives the rerun command (item 6). It still costs wall-clock: both modules waited ~13 min behind one planner.

## What worked well overall
- Every stop carried a paste-ready `next` with the right host; I never had to work out a command myself except to correct one host (item 8).
- Cross-vendor reviews found real things each time (Decimal context, self-consistent fake, unpinned ordering via mutants, broken pipe) and passed sound work first time (CORE M1).
- `loops --repo`, `status`, `cost`, `quota` answered "what's running / what did it cost" without reading logs.

## Wishlist
- When two modules are owed planner revisions at once, have `next` (or TAKEN) offer one combined planner task, so the second module doesn't idle behind the first.
- Make the design-review host after a planner turn follow the module's builder host (as `run` does), not "the host the planner didn't use".
- Give planners the loop script's path (or tell them they don't need it) so they don't search the disk for `agent_loop.py`.
- Local-time (or both) timestamps in `report` and TAKEN's `since`.
- A per-turn usage figure on resumed result lines, alongside the running total.
