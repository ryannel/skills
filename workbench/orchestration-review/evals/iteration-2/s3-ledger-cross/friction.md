# Friction log — s3-ledger-cross

Lead: Claude Code (Opus 5.5) subagent, Agent SDK, running inside Claude desktop's Code session. Planner on Claude; builders Claude + Codex in parallel; reviews cross-host. All loop commands run with ORCHESTRATE_HEADLESS=1 via a wrapper (`bin/loop`), results logged by `bin/lrun`.

## Entries

### 1. `LOOP` as a shell variable doesn't work in zsh (nitpick)
- Trying: follow README's "`LOOP` is `python3 <path>/agent_loop.py`" literally with `LOOP="python3 ..."; $LOOP --help`.
- Happened: `(eval):1: no such file or directory: python3 /…/agent_loop.py` — zsh doesn't word-split unquoted vars.
- Cost: one round trip. Worked around with a tiny wrapper script. A shipped `orchestrate` shim or "alias LOOP=…" in the README would avoid it.

### 2. Loop output is pretty-printed JSON, but docs say "one line of JSON" (confusing)
- Trying: log each command's result line (README: "Every result is one line of JSON"; build SKILL: "prints one line of JSON").
- Happened: `ready` and `loops --json` print indented multi-line JSON; `tail -1` gives `}`. `quota` without --json prints prose.
- Cost: one re-do of my logger. Either print one line or say "a JSON object".

### 3. `ready` on an empty repo gives a good next step (worked well)
- `ready` → `unplanned` plus `next.command` = `plan --task 'Plan the project: <…>'` with `why` telling me to include the owner's answers on hosts, integration and checks. Clear.
- Owner decision D1 (logged): the owner ask has no answers on Integrate/Check/hosts; I appended "two builders (Claude + Codex), Review host: other, Integrate: local (no remote), any stdlib-fitting Check" to the owner's verbatim words. An unattended lead could do this from the scenario, but a real owner would be asked.

### 4. `loops` shows another scenario's loop with nulls (nitpick)
- `loops --json` listed s4's ICONS loop with model/effort/turns all null and `registered: false` because it was started by suite-v1. Expected per README ("older copy… listed from the process table"). Fine, but `--repo` is needed to avoid counting other repos' loops; the build skill does say so.

### 5. Planner turn: good plan, one turn, ~9 min, $2.19 list (worked well)
- `plan --host claude` → PLANNED in 536 s, 1 turn, usage input 97,921 / cached 1,708,602 / output 52,461, cost_usd 2.19. Two modules (CORE M1; REPORT M1, M2 needs CORE:M1), acceptance tests written by the planner and hash-pinned in the checks. `next` correctly named the design review on the other host (codex).
- The planner's "Decisions for you" list (8 assumptions: journal syntax, amount formats, multi-currency blank inference, -f/LEDGER_FILE, etc.) is useful. Owner decision D2: accept all assumptions as planned.
- Small: the planner touched `.gitignore`, `ledgerlite/__init__.py`, `tests/` — non-plan files — and the loop landed them. Fine here, but the README says the loop "commits and integrates the rest" of a planner's work without saying source files are allowed.
- Small: plan commit subject is the truncated task text (`Plan: Plan the project: want a small plain-text accounting thing i`) — the "Plan: Plan the project:" doubling comes from `ready`'s own suggested task prefix.

### 6. Hash-pinned acceptance tests embedded in check strings (observation)
- Check M1.1 is `python3 -c "import hashlib;...assert h=='626b…'"&& python3 -m unittest acceptance.test_core`. Clever workaround for README's known limit ("a script a check calls can still be changed by the builder"). Suggests the loop could offer pinning check-called files natively.

### 7. Worktree setup is manual (nitpick)
- Build skill says to give each module its own worktree in an ignored folder and add it to `.git/info/exclude`; I did `echo wt/ >> .git/info/exclude; git worktree add -b build/core wt/core main` by hand. A `LOOP worktree --module M` helper would remove a step every lead repeats.

### 8. CORE design review (Codex) → DESIGN CHANGES on Decimal context precision (worked as designed; arguably over-strict)
- `run --module CORE --host claude` ran the owed design review on codex first (Review host: other worked) → DESIGN_OWED with design_review.verdict `DESIGN CHANGES: 1 blocking findings` after ~70 s; usage input 61,335 / cached 186,624 / output 2,749. `next` = `plan --task 'Revise CORE's design…'` by: planner. Clear routing.
- The finding is real but edge-casey for a "small" tool: 28-digit amounts and caller-set low Decimal precision. A reasonable owner might have waved it through; the process has no cheap "owner says advisory" path at design stage short of re-planning. Cost: one more planner turn plus another design review before CORE could start.
- Note: the design-review `usage` lacks `cost_usd` (Codex), while Claude turns carry it — totals across hosts can't be summed in dollars.
- Builder for CORE never started; the claude "builder" slot sat idle while the plan revision ran. With two builder slots and one module blocked on design, the lead has nothing else to give it (REPORT is taken by Codex).

### 9. REPORT design review (Claude) → DESIGN CHANGES, 2 blocking; both real (worked well)
- B1: `pip install .` fails with flat layout because `acceptance/` is a second top-level package — the reviewer actually built a venv and proved M2.2's check would pass on an uninstallable pyproject. B2: non-UTF-8 journal → UnicodeDecodeError traceback, owned by nobody. Good catches. ~85 s, usage input 46,826 / cached 639,892 / output 14,621, $0.79.
- Reviewer wrote: "The owner's original request is truncated in the commit and loop metadata, so I took the module brief … as the brief." → the owner's verbatim ask isn't reaching reviewers. Only the truncated plan-commit subject carries it. (confusing; affects review fidelity)

### 10. Planner runs are serialised per repository: second module's revision gets TAKEN (wasted time)
- Both design reviews came back DESIGN CHANGES within a minute of each other. `plan --worktree wt/report --task "Revise REPORT's…"` while CORE's revision planner ran →
  `{"result": "TAKEN", … "by": "another planner on this repository (plan, pid 74547 … wt/core …)"}`.
- So the two "parallel" modules re-plan one after the other; the whole project is serialised behind the planner for ~10 min per revision. The build skill doesn't mention that `plan` is one-at-a-time per repo, nor how to queue a second plan task (I could fold both revisions into one planner task, but the skill's `next` gives per-module tasks). Wished for: `plan` accepting several tasks, or `TAKEN` carrying a `next` saying "rerun after pid X ends".
- `loops` for the running planner shows `module: null, turns: 0, tokens: null` for its whole first turn — no sign of progress for a ~9 min turn.

### 11. CORE revision planner: 3.5 min, $1.01, addressed finding + advisory (worked well)
- PLANNED, revised CORE.md (exact local Decimal context), strengthened M1.2 ask, added acceptance cases, re-pinned hash. Flagged that REPORT has the same rounding risk — I relayed that one line (a planner finding, not my opinion) into the REPORT revision task. Lead judgement call: the build skill says "brief with file paths and nothing else" but also "use --message for findings"; for a planner there's only `--task`, so it's unclear whether relaying another planner's cross-module note is allowed.

### 12. CORE: design OK on second review, then built and claimed in one Claude turn (worked well)
- `run --module CORE --host claude` (03:00–03:05): design re-review on codex → DESIGN OK (usage in 69,293 / cached 206,080 / out 2,994), then the builder claimed M1 in 1 turn (in 59,943 / cached 915,329 / out 22,500, $1.11). Loop reran checks itself; `review: true`. ~5 min wall total.
- `loops` during the build showed the *design review's* token numbers under the build row (tok = codex numbers with no cost) — confusing: the build row's tokens are the design review's, not the builder's.
- The CLAIMED line doesn't carry `next` (other stops do); the table in SKILL.md tells me to run a review, and I had to assemble the command by hand (module, milestone, commit, worktree, host). A `next` on CLAIMED with review:true would remove that step.

### 13. BUG — a planner turn is rejected because a concurrent builder's claim changed the acceptance records on the tip (blocked; worked around)
- Trying: revise REPORT's design (planner on wt/report, base 6ae8d90) while the CORE builder (wt/core) claimed M1, which landed `483102b orchestrate: claim CORE M1` (writes CORE-ACCEPTED.json) mid-turn.
- Happened: `plan --worktree wt/report --task "Revise REPORT's…"` → after a full 7-min, $1.98 planner turn that reported PLANNED:
  `{"result": "INVALID", … "landed": false, "problems": ["changed docs/plans/CORE-ACCEPTED.json; only the loop writes acceptance records", "changed docs/plans/REPORT-ACCEPTED.json; only the loop writes acceptance records"]}`
  The planner touched neither file (`git diff` in wt/report showed only ORCHESTRATE.md, acceptance/test_cli.py, ARCHITECTURE.md, REPORT-*.md/json + new acceptance/test_install.py). The loop appears to diff the planner's tree against the *current* tip rather than against the base the planner started from, so the tip's own loop commits look like planner edits.
- No `next` on this INVALID. It's precisely the parallel case the suite advertises (two modules, planner + builder at once).
- Expected: the planner's diff measured from its own start commit, then rebased/landed onto the tip.
- Workaround (no suite edits): `git stash -u; git merge --ff-only main; git stash pop` in wt/report, then `LOOP adopt --worktree wt/report` → ADOPTED, but only the 4 plan files under docs/plans/ (authorised REPORT's draft). It silently left behind `acceptance/test_cli.py`, `acceptance/test_install.py` and `ORCHESTRATE.md`, even though the newly authorised REPORT-DONE.json pins the sha256 of both acceptance files → integrated definitions would have failed forever. `adopt … acceptance/test_cli.py acceptance/test_install.py` → REFUSED "isn't a plan file … commit and integrate it another way".
- I then committed those three files verbatim (hashes verified equal to the pins) as the owner stand-in and ran `LOOP land --worktree wt/report` → LANDED 1703c74. Owner decision D3 (logged). An unattended lead would have had to stop here, or rerun the planner (~$2, 7 min) and hope no claim lands mid-turn again.
- Secondary bug: `adopt` authorising definitions whose checks pin files it refuses to land should at least warn, since it creates a done-when file that can never pass.
- Cost: ~10 min of lead time, one wasted (well, salvaged) $1.98 planner turn. Severity: blocked without a manual workaround.

### 14. CORE M1 review on Codex → PASS first time, thorough (worked well)
- `review --module CORE --milestone M1 --commit e47f581 --host codex` → REVIEWED PASS in ~2.5 min, usage in 65,783 / cached 320,512 / out 5,480. Review wrote its inspection list before capturing, ran its own probe (10,000-digit amounts, hostile caller contexts). `next.why`: "CORE is finished". CORE done at 03:07, ~22 min after planning finished.
- I exercised `ledgerlite.core` myself (multi-currency journal with blank posting, symbol currency, slash dates, an unbalanced txn): parsed, inferred per currency, and refused with `file:1: transaction 'Bad' doesn't balance: its postings sum to 1 USD…`. Verified.
- Nitpick: after CORE finished, the Claude builder slot had nothing to do (REPORT is one-at-a-time per module and assigned to Codex). The two-builder ask collapses to one builder for the remainder; the skill covers this ("run fewer builders and say why").

### 15. REPORT: design OK on second review (Claude), M1 claimed by Codex in one turn (worked well)
- `run --module REPORT --host codex` 03:08–03:14: design re-review on claude → DESIGN OK ($0.80), Codex builder claimed M1 in 1 turn (in 73,320 / cached 570,496 / out 10,303; `goal: complete`). ~6.5 min.
- Odd: the result carries `thread` for a headless `codex exec` run, and the Codex usage has no cost estimate, so per-milestone dollars can only be compared for Claude turns.

### 16. REPORT M1 review (Claude) → FAIL on East-Asian-wide characters overflowing 80 columns (fair, but a bar the owner never asked for)
- `review --module REPORT --milestone M1 --commit 6e9cafc --host claude` → FAIL, fails 1, next `same-session`; ~3.3 min, $1.11. The finding is real against REPORT.md's own "fits 80 columns" (which the planner added as an assumption in the revision), and the reviewer ran mutants and its own probes. But it's a planner-invented constraint failing a "small" tool; owner never asked for 80-col fitting.

### 17. `LOOP next` reads the lead's worktree, not the integrated tip, so it gives the wrong escalation (confusing; could mislead)
- Right after the FAIL, `next --module REPORT --worktree wt/report --milestone M1` → `{"fails": 0, "action": "none", …}` because wt/report was still at the builder's commit, before the loop's review commit landed on main. After `git merge --ff-only main` in wt/report → `{"fails": 1, "action": "same-session", …}`.
- `ready`/`status` read the tip; `next` doesn't. A lead following the skill literally would get `action: none` and not know what to do. Expected: `next` reads the tip like `ready`, or says the worktree is behind.

### 18. `cost` and `status` mid-run (worked well, one nit)
- `cost` gives a clean per-milestone split (planning / design review / build / review per host). It counted the INVALID planner turn under planning (3 turns, $5.17) — good, wasted spend isn't hidden.
- Nit: the total line says "($8.99 list price) on claude, codex" though the dollar figure is Claude-only; Codex turns have no price. Reads as if it were the whole run's cost.
- `status` is the most useful single view for "what's running": `REPORT: ready (M1); running: build M1 codex, pid 77110, 0 turns, last activity 4s ago`.

### 19. REPORT M1: same-session fix and re-review PASS (worked well)
- `run … --host codex --message "<next's message>"` → CLAIMED in ~2.5 min (resumed session; result `usage` is the session running total: in 175,763 / cached 2,027,008 / out 26,508, turns 2). Re-review on claude → PASS ($0.76, ~1.7 min). The PASS `next` names `run --module REPORT` and helpfully says `run` fast-forwards a clean worktree itself — which is the info I'd wanted in item 17.
- Lead choice: both builders idle with one ready milestone (REPORT M2). Skill: "prefer the module it was just in" (→ Codex) vs "fewer ready than builders → hosts in the order the owner listed" (→ Claude). I took the latter: M2 on Claude, review on Codex. The two rules can point different ways; a sentence on precedence would help.

### 20. REPORT M2: built in one Claude turn ($1.63, 4.6 min), review on Codex FAIL with 3 blocking — all edge cases of planner-invented layout rules (wasted time; reviewer strictness drift)
- Findings: B1 closed stdin (`<&-`) → traceback (fair: "never a traceback" is in the owner-facing contract). B2 a literal TAB inside a payee misaligns register columns at 8-col tab stops. B3 a 30-digit amount makes a register line 82 instead of 80 columns.
- B2/B3 are failures against the planner's own "fits 80 columns" assumption, at inputs no owner of a "small" tool would hit. Combined with REPORT M1's CJK-width fail, three of four review fails so far were on terminal-width rules nobody asked for. The suite's "the definitions decide what blocks" stance means a planner's over-specific design becomes a review-fail magnet. Wished for: reviewers told to weigh findings against the owner's ask (which they don't see in full, item 9), or a planner rule against inventing hard numeric layout bars.
- Before handing off I exercised the claimed CLI myself (bash): balance tree with multi-currency stacked rows and zero grand total, `register assets:bank` case-insensitive with running totals, out-of-order dates sorted, `--json` both commands parse via json.tool, unbalanced → `file:1: …` exit 1, missing file → one line exit 1, bad subcommand exit 2, `-f -`, `LEDGER_FILE`, Latin-1 file → one-line "not valid UTF-8" exit 1, `| head -1` clean. All good on what the owner asked.

### 21. REPORT M2 fix and re-review PASS; whole build accepted at 03:40 CET (worked well)
- Same-session fix on claude 2.6 min (session total $2.40); re-review on codex PASS 3.7 min. `next.why`: "REPORT is finished". `ready` → both finished, `next.command: null`.
- I re-verified at the tip: 63 tests pass; `pip install --no-build-isolation --no-index .` into a python3.11 venv gives a working `ledgerlite`; stdlib-only imports.

### 22. Final report: `report --write` + `adopt` worked smoothly (worked well, nits)
- `report --write` produced a good factual half (closed, verdicts with links, the "Definitions changed through adopt" section — which correctly surfaced my D3 workaround — cost per milestone). I added the judgement and `adopt` landed it (ADOPTED 9c6151d).
- Nits: the factual half doesn't list hosts for design-review verdicts, doesn't carry the Codex quota line (the skill asks for it), and says "build sessions: 3" without saying how many builders ran in parallel. Its cost lines are copied from `cost` with the same Claude-only-dollars total.
- The report is written into the main checkout (`repo/docs/evidence/build-reports/`), not the lead's worktree; fine with Integrate: local, but surprising.

### 23. Cleanup leaves loop verify worktrees behind (nitpick)
- After removing my wt/ worktrees, `git worktree list` still shows four detached worktrees under `.git/orchestrate/verify/{_ADOPT,_PLAN,CORE,REPORT}`, `_PLAN` still at an old commit. The skill's "remove worktrees whose work has landed" doesn't say whether these are caches to keep or leftovers to prune.

### 24. Tracking running work and cost across two builders (mixed)
- What worked: `status` (one line per module incl. live run, pid, last activity) and `cost` (per-milestone split by phase and host). `quota` on each Codex result line.
- What didn't: `loops --json` shows `turns: 0, tokens: null` for any turn in progress — and most sessions here were one long turn — so during a run it can't tell you what a builder has spent so far or whether it's progressing; `idle_s` was the only live signal (once 206 s on a Codex review that was fine). The build row inherited the design review's tokens. There's no "since the lead started" cost view; I kept my own via result lines.
- Wished for: a `LOOP watch --repo` (or `loops --follow`) that emits one line per state change (started, turn ended, claimed, reviewed), so a lead needn't poll and parse; Codex cost estimates beside Claude's.

## Wishlist (summary)
- Planner diff measured from its start commit (item 13), or plan runs serialised with builders' claims.
- `adopt` refusing (or warning) when it authorises definitions that pin files it won't land.
- `next` reading the tip like `ready` (item 17); `next` on CLAIMED/review:true (item 12).
- Owner's verbatim ask stored in the repo where reviewers see it (item 9).
- Reviewer guidance to weigh planner-invented numeric bars against the owner's ask (items 16, 20).
- One-line JSON output, or say "JSON object" (item 2); a shipped `LOOP` shim (item 1).
