# Thrum harness audit, 2026-11-10 to 2026-11-12

Thrum ran orchestrate 1.7.1 throughout. The finding numbers below are not a ranking. Each row says whether the 2.0.0 source already covers it.

**Out of scope here:** disk space, and the stale GPU lock as such. The owner is fixing both in Thrum.

**Is 2.0.0 installed?**
- Yes, for Claude Code and Codex. Both caches hold 2.0.0, and the Claude copy matches the repo.
- It is not yet live in Thrum. The lead session hard-codes the 1.7.1 path (finding L1), and Thrum hasn't run `migrate`.

## What works

- Reviews and plans don't cycle: at most 2 review rounds, and every design-review change named a real defect.
- Planner escalations take 7–49 minutes.
- Builders run `check` before claiming and merge through the script.
- The lead waits on notifications, not sleep loops, and relays review findings accurately.
- The lead's messages to the owner are plain and clear.

## Cost and speed

| # | Finding | Evidence | Change | In 2.0.0? |
|---|---|---|---|---|
| C1 | Builders poll long jobs with sleep and tail. That is 30–89% of input tokens, each call re-reading 130–280K tokens of context. | CULLING spent 86M of 113M input tokens this way, with 61 identical `tail`s of one log. `build-milestone/SKILL.md:171` says to run long jobs in the background. EFFECT-GRAPH used 3 turns in 16 minutes as polls. | Add `agent_loop.py wait --pid/--file --until <regex> --timeout`: it blocks inside one tool call and returns a short tail. The skill says to wait with `wait`, never `sleep`. | No |
| C2 | Codex usage rows are cumulative per thread, about 83% over. | `usage_of`, line 3872. Ledger 1,935M cached tokens against 1,056M true. The doubling repeats in `add_usage` (lines 5248, 5413) and `claim_usage`. | Record each turn's increase over the session's previous total. | No |
| C3 | Sessions run close to the context window. | Builders reach about 450K of 475K, with up to 3 compactions. Reviewers compact within 25 minutes. What fills it: Computer Use screenshots (one 4.2 MB line), full `ps` command lines, and 40K-character opening reads. | Cap command output by default. The skill says to read only the tail of logs, use `ps -o pid,etime,comm`, and inspect still frames rather than video. Start a fresh session from the handoff file instead of resuming one over 400K tokens. | No |
| C4 | The 2-hour turn timeout is the usual way a builder turn ends. The resume prompt then lists every open item, and leaves out the last commit and the jobs still running. | 8 timeouts (exit 124) since 15:00 on 11 Nov. ATMOSPHERE turns 1–3 all hit it. | The resume prompt names the last commit, the live background jobs (pid and log) and the items already passed. | Partly (restatement only) |
| C5 | Reviewers redo work the script's check has already done. | They rebuild, run `./dev check` twice and record new captures (561 MB in one review). REVIEW_TEMPLATE says "Build and run the product". | Give the reviewer the script's verify output, and have it re-run only the items it doubts. Put a time bound on Computer Use calls. | No |
| C6 | After every rebase, builders re-run all their proofs. | `rebased-exact-verifier` (CULLING), `recapture-rebased-chrome` (ATMOSPHERE), `exact-rebased.log` (APPLE-PRESENTATION). | `merge` reports which upstream paths changed, so only the affected items' proofs re-run. Merge first, then take the final proof. | No |
| C7 | Commits are mostly bookkeeping, and evidence bloats the repo. | 128 of 205 commits are `orchestrate:`, 46 of them STATUS.md. Evidence in git grew from 0.54 to 2.26 GB in 30 h, against 9.4K lines of engine code. | Fold the STATUS.md update into the record commit. Keep large evidence outside git with a hashed manifest, and cap what a review commits. | No |

## Flow and correctness

| # | Finding | Evidence | Change | In 2.0.0? |
|---|---|---|---|---|
| F1 | Items that need someone at the Mac go to a reviewer who can't do them, and a could-not-judge FAIL costs a full builder round. | APPLE-TILE M3 round 1 failed on "the active Mac console is locked" (b87a9d77). Round 2 hung 98 minutes in `cua.getApp`. | Check access before such items. If missing, block as Needs Access, rerun only the review and spend no round. | No |
| F2 | Two timeouts in a row stop a run as "likely quota, sign-in or outage". An app-started thread that can't be resumed headless also stops the run. | CULLING and ATMOSPHERE state files. The 12:42 and 06:57 exit-1 pairs. The lead used `--fresh` 15 times to get round these. | Don't count exit 124 as a failure. When a headless resume fails, start fresh from the handoff file. Save stderr in the ledger. | Partly |
| F3 | The `Builders:` setting is never enforced. | 4–6 builders ran at once against "two Codex builders". | `run` refuses past the configured count unless given the owner's words for the extra builder. | Skill only |
| F4 | A change to one module broke another's exact images, and the builder's evidence came from an older binary. | APPLE-PRESENTATION M1 jitter (5258d963) caused two FAILs (e54ca2c2, 79b44720). | Exact-baseline comparison in the merge gate (BASELINE-GUARD M1). Reject evidence that names a commit other than the claimed tree. | Project side |
| F5 | Throwaway proof drivers in `tmp/` break the clean-checkout check. | ATMOSPHERE claim rejected: "ENOENT … verify/ATMOSPHERE/tmp" (15:12), costing another 22-minute turn. | The skill bans proof drivers that live in `tmp/`. | No |
| F6 | Codex edits code with Python `str.replace` heredocs, and few of them check that the anchor text exists. | ATMOSPHERE: 80 heredoc edits, 1 `apply_patch`. | The skill says: on Codex, edit with `apply_patch`. | No |
| F7 | About 24% of commands need a sandbox approval. | ATMOSPHERE: 170 of 701 commands. Mostly `ps`, `lsof` and `.git` index writes; only 2 were denied, both rightly. | Add a `jobs` command to list processes without `ps`. Route git writes through the script, or check the `.git/worktrees/<name>` writable root. | No |

## The lead

| # | Finding | Evidence | Change | In 2.0.0? |
|---|---|---|---|---|
| L1 | The lead runs without the skill text and on a fixed version path. | It never loaded `build`, and works from compaction summaries ("Use this copy from now on", line 14509). It used 11 version paths, 109 of them 1.7.1. It started 1.7.1 builders at 06:58 on 12 Nov, with 2.0.0 installed. | Every result line names the script version and warns when a newer installed copy exists. Ship a stable launcher path. The skill says to re-read SKILL.md after a compaction and never to store the script path. | No |
| L2 | The lead does by hand what the script could do. | 40 commands dig `{"result"` out of mixed output. It chains plan → design review in bash for-loops. Each build → review step costs one 180K-token wake. | Write each result to `.git/orchestrate/results/…json`. Add a plan → design review option that runs until OK. Optionally, `run --review` chains build → review → next milestone. | No |
| L3 | Flags and boilerplate are repeated in every message. | `--model/--effort` on 68 commands. `--message` repeats rules: "run long jobs in the background", `lock gpu`, "The owner is at the Mac now". | Result lines echo the resolved host, model and effort. Move the background-job and lock rules into the builder prompt. | No |
| L4 | No daily report has been run. | 0 `report` or `cost` calls. Speed questions were answered from `git log`. | Run `report --write` on the first result after midnight. | No |
| L5 | "Waiting on you" lists 30 lines; about 2–4 need the owner. The lead's real questions never reach it. | 28 are "assumes" lines, many technical (CIEDE2000, a half-float bound). Questions were repeated in chat (delete scratch, unlock the Mac). | Split the list into "Needs you now", including the lead's open questions, and "Choices made for you". Flag assumptions about milestones that are already done. | No |
| L6 | The lead carries two days of harness design in its context. | 13 compactions. About 180K tokens per wake. | Start the lead in its own session. | Practice |

## Smaller issues

- A design review re-ran on an unchanged design (CREATOR, 9b12c16a); 2.0.0 refuses this.
- Block messages link to absolute worktree paths, and some name no action and no one to act.
- Off-glossary words appear ("lease", "GPU slot", "parked").
- The CULLING builder ended with a "two-pixel mismatch … unexplained": a quality risk that was left in a block reason.

## Second pass, 08:00–12:35 on 12 Nov

Thrum was still on 1.7.1. A subagent read the lead's transcript, the Codex sessions and the records; two of its code claims were spot-checked against 2.1.0.

| # | Finding | Evidence | Change | In 2.1.0? |
|---|---|---|---|---|
| N1 | Mac M2's owner-attended recordings came from a binary rebuilt from an older commit, to match earlier evidence. | Builder rebuilt 10287802 at 09:06. Review FAIL 17bcde83: 96 of 406 source files differ. Cost the owner's sitting, 4 of 6 recordings, 68M input tokens, a round. | Attended work happens after merge, on a build of HEAD; never rebuild an old commit to match evidence. `claim` refuses evidence stamped with another source commit. | Partly |
| N2 | Code reaches main before the script's checks run. | CULLING merged 09:35 as claimed; claim check failed M1.2 at 10:57; main carried unaccepted code for 3 h and others rebased onto it. | `merge` runs the milestone's item checks on the rebased commit before it pushes, or the state change lands only with acceptance. | No |
| N3 | A failed check's message dropped the panic. | Builder asked at 12:06 for "the full stdout"; `check_failures` keeps the last 30 lines of stdout+stderr combined. | Save each check's full output to a file and name it; tail stdout and stderr apart. | No |
| N4 | End-of-milestone checks run three times on the same tree. | EFFECT-GRAPH: `check`, then `land`'s test run, then claim checks: 35 min. CULLING claim checks: 49 min. | Record check results by tree hash and skip a repeat. | No |
| N5 | The lead told the owner wrong things because it can't see what a run is doing. | Blamed GPU waits for a 116-min `cua.getApp` hang; said "merging" for a claim that had failed; said a reviewer could judge from recordings with the Mac locked. | `loops`/`status` show each run's phase and the script's last message. A timeout names the last tool call. Bound Computer Use calls. | No |
| N6 | `migrate` refuses while jobs run, so the upgrade waits indefinitely. | Refused at 08:11; lead asked "When should I stop the jobs and migrate?" 8 times. | Drain mode, or per-module migrate. | No |
| N7 | Headless agents ask questions nobody sees. | `request_user_input_async` from the Mac M2 reviewer (11:50) and CULLING builder (12:06). | The prompt says such questions reach no one; end with BLOCKED or NEEDS_CONTEXT. | No |
| N8 | The browser warning lists the whole project on every result. | 18 items on EFFECT-GRAPH's result. | Scope `browser_warnings` to the milestone being run. | No |

## Third pass, 12:35–16:30 on 12 Nov

Thrum ran `migrate` to 2.0.0 at 15:05 (9cba7417), and every live process uses the 2.0.0 path since. Finding P5 was checked against the 2.0.0 cache (line 5248).

| # | Finding | Evidence | Change | In 2.1.0? |
|---|---|---|---|---|
| P1 | `migrate` can't handle work in flight (N6, worse). | EFFECT-GRAPH M2 held about 2 h for the migration. APPLE-PRESENTATION's diverged worktree was refused by `run` for old names, and `migrate --worktree` was refused because other runs had started. The lead merged by hand, and the builder resolved three conflicts in 4 s by stripping markers; the next compile failed. | `migrate --worktree` works on one diverged branch while other modules run, and lists every worktree still on old names. | No |
| P2 | `same-session` resumes a pre-migration, nearly full thread. | CULLING resumed thread 01a1ce5e (started 07:07 under 1.7.1, goal names `land`) at 322K context; 446K by 16:28; 16M input tokens in 42 min. | Start fresh from the handoff when the thread predates the script version or migration, or its context is over about 300K. Replace the goal text when the task changes. | No |
| P3 | A merge that outlives its turn leaves no claim record. | CULLING's detached `land` pushed 4c2690bb after the turn was killed; `run` said FLOOR; `ready` showed `commit: null`; the reviewer had no checks note and ran `./dev check` for 35 min under the GPU lock. | `review` refuses, or runs the claim checks, for a Ready for Review milestone with no claim. After a timeout, `run` looks for a live merge or a new claim before reporting. | No |
| P4 | Turns stopped at the time limit record zero tokens. | Ledger rows for the 11:57 and 13:57 CULLING turns are `{"incomplete_turns": 1}`; about 61M input tokens missing. Codex approval-review sessions (5M+) aren't recorded. | On exit 124 read the last `token_count` from the rollout and record the increase (fixes C2 too). Record approval-review sessions. | No |
| P5 | The lead said 2.0.0 fixes the timeout; it doesn't. | 2.0.0 line 5248 counts exit 124 as a failed turn, so a second timeout in a row ends a run as FLOOR. | Ship 2.1.0. `migrate` prints what changed for the project. | Yes |

Confirmed again: C1, C3, C5, F2, F3 (three builders against two, after the lead said the setting came through), F5, L1 (now hard-coded to 2.0.0), L3, N2 (unaccepted code on main caused APPLE-PRESENTATION's conflicts). None shown wrong.

Went well: `migrate` itself (16 s, one commit, settings kept); reviewing across the migration commit; the old-names guard on `run`; the lead letting jobs finish rather than pausing a builder; a precise CULLING review.
