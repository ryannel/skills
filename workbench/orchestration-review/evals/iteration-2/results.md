# Iteration 2 results: end-to-end runs on Claude and Codex

10 November 2026. Nine runs of five fictitious projects, each taken from an empty repository through the loop
with real Claude and Codex sessions. A Claude Opus 5.5 subagent led each run and stood in for the owner. The
scenarios and grading statements are in [scenarios.md](scenarios.md), written before any run started. Each run's
folder here holds the lead's friction log, its `result.json` and every loop command with its raw result.

This is a set of single runs, one per scenario and suite version. It shows what broke and whether a fix held on the
next run. It doesn't measure how often anything happens.

## What was run

Five frozen copies of the suite were used, so fixes could go into the working tree while runs were in flight:

- **v1:** branch `orchestrate-polish` on top of orchestrate 1.5.4, before any fix from these runs.
- **v2:** v1 plus loop fix rounds one to three and the first skill-text fixes.
- **v3:** v2 plus rounds four to eight.
- **v4:** v3 plus rounds nine to fourteen.
- **v5:** v4 plus rounds fifteen to eighteen. Round eighteen made the owner's side chat-only, after the owner read
  the first eight runs: the lead runs every `owner` command on what the owner tells it, the typed confirmation
  and the separate `relay` command are gone, and `report` lists each decision recorded in the owner's name.

Round nineteen came after v5 and is covered by unit tests only.

All sessions ran headless (`ORCHESTRATE_HEADLESS=1`), on each host's default model (Codex `gpt-6.1-sol`, Claude
Opus 5.5) and default effort. The visible app path wasn't exercised.

| Run | Suite | Planner | Builder | Reviewer | Outcome | Wall clock |
|---|---|---|---|---|---|---|
| `s1-slug-claude` | v1 | the lead, in chat | Claude | Claude | 2 of 2 milestones accepted | 25 min |
| `s2-slug-codex` | v1 | Codex | Codex | Codex | 2 of 2 accepted; product drops `Ø` | 16.5 min |
| `s4-icons-taste` | v1 | Claude | Claude | Codex | 2 of 2 accepted, the first by `owner accept` after five failed reviews | 97 min |
| `s3-ledger-cross` | v2 | Claude | Claude and Codex at once | the other host | 3 of 3 accepted | 56 min |
| `s5-game-mixed` | v2 | Codex | Codex | Claude | stopped at the first milestone, nothing accepted | 31 min |
| `s6-icons-taste-v2` | v2, then v3 | Claude | Claude | Codex | stopped at the owner's pick on v2; carried on under v3 with a relayed answer, 2 of 2 accepted first time | 16 min, then 17 min |
| `s7-slug-cross` | v3 | Claude | Claude | Codex | 2 of 2 accepted; `Ørsted` gives `orsted` | 36 min |
| `s8-ledger-final` | v4 | Claude | Claude and Codex at once | the other host | 3 of 3 accepted, two after one failed review each | 53 min |
| `s9-icons-chat` | v5 | Claude | Claude | Codex | 2 of 2 accepted first time, with an owner's pick and a change of mind recorded by the lead | 85 min |

## Statements

| Statement | s1 | s2 | s4 | s3 | s5 | s6 | s7 | s8 | s9 |
|---|---|---|---|---|---|---|---|---|---|
| 1. Every milestone accepted, or the stop is the owner's | pass | pass | pass, by an owner accept | pass | pass: both stops needed the owner | pass | pass | pass | pass |
| 2. The product does what was asked, used directly | pass | fail: `Ørsted` gives `rsted` | pass | pass | fail: a prototype, no rounds or restart | pass, with a gentle hand | pass | pass | pass |
| 3. Every stop carried a usable `next` | fail | pass | fail | fail | fail | fail | fail | fail: one named a host the lead overrode | fail: an owner-only design finding went to the planner |
| 4. The lead never read `agent_loop.py` | pass | pass | pass | pass | pass | fail: read the source for a refusal message | pass | pass | pass |
| 5. README to first builder with no undocumented step | fail | fail | fail | fail | fail | n/a | pass, apart from owner answers on hosts | pass | pass |
| 6. Every headless claim and review carried `usage` | pass, paused turns missing | pass | pass, dollars double-counted | pass | pass | pass | pass | pass | pass |
| 7. No session changed a file outside its role unnoticed | pass | pass | pass | pass | pass | pass | pass | pass | pass |

Statement 3 fails in eight runs for different stops each time, which is why most loop fix rounds touched `next`:
DESIGN CHANGES and a passing review (s1), the re-plan rung (s4), a planner INVALID and a planner TAKEN (s3), a
mixed-cause BLOCKED (s5), CLAIMED with a review owed (s3, s6, s7), and a design review sent to the planner's
other host where `run` would have used the builder's (s8). Those are fixed in the working tree, and s8 and s9 saw
the fixes work. The s9 one is left as found, below.

Per scenario:

- **s1:** `pause` stopped the builder cleanly twice, `run` resumed the same session, and a second `run` got `TAKEN`.
- **s2:** `status` could be read cold. `quota` could not (325 lines of JSON).
- **s3:** the two builders overlapped and neither broke the other's integration. Every review ran on the other host.
- **s4:** the plan opened with a pick from three variants and the reviewer compared against the anchors. The plan
  also held every variant to the final look, which failed the milestone on the variants the owner had rejected.
- **s5:** the frame-rate number became a reviewer reading a timing sample, not a command. Feel went to the owner.
- **s6 on v3:** the variants were held only to the floor, and both milestones passed their first review.
- **s9:** the first live run of the chat-only owner. The lead asked the stand-in owner for the direction pick,
  recorded the answer with `owner answer`, sent a change of mind ("drop fog, add a storm icon") to a planner, and
  `report` listed both in the owner's words. Nothing told the owner to use a terminal. From the pick to the last
  milestone accepted took 20 minutes with the change, against 17 in s6 without one. The time went on design: the
  first design review failed because the plan had Codex reviewers judge the builder's screenshots, and the
  revision took 32 minutes.
- **s8:** every `CLAIMED` carried its review command on the right host, and a second planner turned away got the
  holder and the command to rerun. Both failed reviews were real: a reviewer reordered same-date entries in the
  code and every builder test still passed, and piping output into `head` printed a traceback. The two builders
  overlapped for only about four minutes, because both design reviews asked for changes and the planner revisions
  ran one after the other (13 minutes, then 3).

## Tokens

As the leads totalled them from result lines. Claude dollars are list price, and the v1 figures double-count resumed
turns (fixed in round three), so read the s4 figure as an upper bound.

| Run | Claude | Codex |
|---|---|---|
| s1 | 190k in, 2.2M cached, 54k out, $3.87 | none |
| s2 | none | 283k in, 1.9M cached, 35k out |
| s4 | builders 574k in, 29.2M cached, 257k out, at most $41; planners $2.47 | reviewers 802k in, 8.2M cached, 54k out |
| s3 | $12.15 across the Claude turns | part of 1.3M in, 16.0M cached, 291k out for all 17 turns |
| s5 | reviewers about $1.01 | part of 283k in, 3.7M cached, 69k out for the run |
| s6 | $6.45 for the whole project, 9 turns | two design reviews, two milestone reviews |
| s7 | $5.38, of which $3.15 planning | 297k in, 22.5k out |
| s8 | $10.82, of which $5.42 planning | part of 986k in, 10.6M cached, 228k out for all 17 turns |
| s9 | $10.70, of which $6.44 planning | part of 827k in, 11.3M cached, 163k out for all 11 turns |

Codex weekly quota went from 54% to 55% used across the first eight runs; s9 started and ended at 55%.

## What the runs changed

Loop script, nineteen fix rounds: `loops`, `check`, `cost`, `report`, `relay`, `owner answer`; a readable `quota`;
`next` as a command on every stop; a first plan that lands whole; the draft rule for `adopt`; a `Review host`
profile line; the loop doing a re-plan's bookkeeping; kept review rounds and captures; per-turn Claude cost.
Three clean-context code reviewers, between rounds, found a way to weaken a check through `adopt`, a `relay` that
a loop-started session could run, and a planner turn that could land an edited acceptance record. Each was
reworked and re-reviewed. The third reviewer's finding took four rounds to close, because each rule about whose
commit counted opened another gap; the fix that held was to stop taking a module "as it stands" once a repository
has any loop record. That reviewer's last pass said it would ship, and listed what's left: a module landed on the
side before the loop's first record, a commit made with plumbing that leaves no reflog entry, and a profile edit
that moves the plans folder. The README's known limits name all three.

The final script was also run read-only against a scratch clone of Thrum's `main` (five modules, all with
records): `status` and `ready` gave the same module states as the installed copy.

Skill text: planners take the owner's words at their ordinary width or log an assumption, add no requirement the
owner didn't ask for, and quote the request at the top of the design; taste-led variants are held only to the floor
and the direction pick is kept for work where the look is the product; critique rounds are capped; a re-review
starts from the last one and holds open-ended items to the range the design names; builders try their checks before
claiming and ask to run a browser outside Codex's sandbox before blocking; a design that promises exactness says
what keeps it exact and up to what size of input (both ledger runs lost a planner round to that finding).

## What the runs don't show

- **The visible app path.** Every session was headless. Thrum uses the visible path daily on 1.5.4.
- **Owner decisions other than an answer and a change of mind.** Until v5 the `owner` commands wanted a typed
  confirmation at a terminal, so no run used them as designed (the s4 lead drove them through `expect` on its own
  initiative; `relay`, since removed, was used once in s6). s9 exercised `owner answer` and a planner-landed change
  through the lead. `accept`, `rereview`, `unpark` and `scope` with a real edit are unit-tested only.
- **A real owner in the chat.** In every run the lead also played the owner, so no run shows how a lead words its
  questions to a person, or whether it ever records something the owner didn't say.
- **Round nineteen, and round eighteen's code review.** Round eighteen had a live run and no clean-context review;
  round nineteen has unit tests only. The suite stands at 268 tests.
- **A claim landing during a planner turn.** s3 hit it on v2; s8 didn't reproduce the timing.
- **Parallel speed-up.** Planner turns run one at a time, so two modules owed revisions wait in line. s8's two
  builders saved little wall clock over one.
- **Long builds.** The longest run was 97 minutes and the largest project three milestones.
- **A game finished.** s5 stopped at its first milestone. The causes are fixed in text and warned about by the
  loop, and no run has confirmed the fix.
- **Reviewer accuracy.** No verdict here was graded by a person.

## Required fields

- **Leakage checked:** partly. Leads were told to use the suite copy by path, not the installed `orchestrate`
  plugin. Sessions the loop starts are given the suite's skill files by path, but a Claude reviewer or planner
  launched with the installed agent file may also have loaded the installed 1.5.4 skill by name. The transcripts
  weren't searched for that.
- **Trigger trials:** not done.
- **Receiver-side run:** yes. Every plan here was built and reviewed by other sessions.
- **What the owner said:** not yet shown to the owner.

## Left as found

From s9, not changed: a design review's blocking finding that only the owner can settle still comes back with
`next` for the planner, and the build skill's prose is what tells the lead to stop and ask; the loop has no command
for an owner decision above a milestone, such as a profile setting, so the lead quotes those in its own part of the
report; when a planner's last message is a late notice, that notice is its `report` and the real summary is lost;
`adopt` won't land a changed profile on an existing project, so the lead commits it with git.

From s8, not changed: timestamps in `report` and `TAKEN` are UTC while the rest is local; a resumed result line
shows the session's running total, with the turn's own figure only in `cost`; `report --write` has no slot for the
builders and path the build skill asks the lead to cover; the loop's `.git/orchestrate/verify/*` worktrees stay
registered after a build, and nothing says whether the lead may remove them.
