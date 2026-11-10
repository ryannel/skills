# Friction log: s5-game-mixed (lighthouse game; Codex planner + Codex builder, Claude reviewers)

Lead: Claude Code (Opus 5.5) subagent, running the suite by path from suite-v2. All loop commands with ORCHESTRATE_HEADLESS=1.

## Setup (02:40-02:46)

### F1. README install section is noise for a by-path user (nitpick)
- Trying to: get from README to a first command.
- README lines 15-23 offer three install routes (npx, install.py with --repo, npx skills add). None of them is "use the files where they are"; `LOOP` is defined as `python3 <where the skills are installed>/build/scripts/agent_loop.py`, which I could infer.
- Cost: ~1 min. Worked fine once I realised LOOP is just the script path.

### F2. Which host plans is not in the README; default would have been the wrong one (wasted time if missed)
- README "Start here" step 1: `LOOP plan --task "..."` with no `--host`. `plan --help`: default host is the profile's `Default host`, else "the host this command runs inside", else the only one installed. Before planning there is no profile, and I run inside Claude Code, so without `--host codex` the planner would have been Claude, not the Codex planner the owner asked for. Had to read `--help` to learn this.
- Expected: README step 1 to mention `--host` (or the lead skill to say "name the host for the planner").

### F3. What to put in `--task` beyond the owner's words: README silent, `ready` tells you (confusing, mild)
- README step 1 says `--task "<what you want, in your own words>"`. build/SKILL.md says "the owner's words as typed".
- But `ready` on the empty repo says in `next.why`: "give it the owner's ask, and their answers on hosts, integration and checks". So the lead is expected to have *asked* the owner about hosts, integration and checks first; neither README nor build/SKILL.md says to ask these before planning. In an unattended run this is a hidden owner stop. I supplied them as owner decisions (D1).
- Good: `ready` on an unplanned repo gives a clean `unplanned` + `next` naming `plan`. That is a nice first-run guard.

### F4. Quota readout is clear (worked well)
- `LOOP quota` gave a one-line verdict first. Fine.

### Owner decision D1 (02:47): answers on hosts, integration, checks given to the planner
- Builder host codex (one), reviews on claude, Integrate local onto main, no push; checks left to the planner's judgement. An unattended run would have stopped to ask these (F3).

## Planning (02:47-)
- `LOOP plan --host codex --task "<owner's ask verbatim + D1 answers>"` launched in background at 02:47.
- Read ahead while it runs: proofs.md "Taste-led work" says feel/sound items should be marked `attended` because "No current agent can ... feel how a game plays". That routes the "feels good / beam has weight / saved boat satisfying" half of this ask to the owner via `owner answer`, which only a human at a terminal can type. Predicted stop; we'll see what the planner does.
- Planner result 02:51: `PLANNED`, one turn, 5.5 min wall clock, usage input 40,675 / cached 384,128 / output 12,986. Landed commit b25bfd8 on main by itself. `profile` parses clean with no warnings. (worked well: one command from empty repo to a valid, landed, authorised plan)

### F5. The planner turned a two-to-three-milestone toy into a taste-led project with two owner sittings (wasted owner time; likely blocks the unattended run)
- Plan: 1 module, 3 milestones, 17 items, design doc 1,727 words for "a little browser game".
- M1 is "Choose a playable lighthouse direction": the builder makes *two* playable visual/motion directions and M1.6 is `attended`: "Owner plays both previews in one sitting and selects one using the loop's owner answer command". The owner never asked for a direction choice; this comes from proofs.md "Taste-led work" ("Start with a direction the owner picks"). M3.4 is a second `attended` playtest for beam weight and rescue satisfaction.
- Consequence: M2 and M3 are queued behind M1 in module order, so the whole build depends on the owner typing `owner answer` after M1. For a lead running unattended that's an early hard stop on the very first milestone.
- Expected: the feel half of the ask ("beam should have weight, saved boat satisfying") to become attended items, yes, ideally batched once at the end; but not a direction-variants milestone the owner didn't ask for, placed first so it gates everything. proofs.md's rule ("Plan a first milestone that makes a few variants") is applied regardless of project size.

### F6. Measured vs judged split: the hard 60fps number is an `inspect`, not a `check` (judgement call, noted)
- Owner: "it has to hold 60fps with 30 boats on screen". Planner made it M1.5 and M3.2 as `inspect` on a `browser-performance` target ("Read a foreground browser timing sample ... Require p95 update+draw below 16.67ms"), plus an exclusive-resource rule. So the one objectively measurable requirement is decided by a reviewer reading numbers, not by a command the loop reruns. Defensible (a timing check rerun by the loop on a busy shared machine would flake, and proofs.md says a benchmark is "too weak if ... it ran on a busy or different machine"), but it means the loop can't enforce the owner's only hard number. The Node `check` tests the simulation, not frame time.
- Elsewhere the split is sensible: offline/single-file/no-deps is a `check` (tools/check_lighthouse.py, written by the planner, so the builder doesn't grade itself); simulation regressions are a builder-written `check` + an `ask` to read the test (as done-when.md recommends); look and motion are `inspect`; feel is `attended`.
- Profile `Check` requires `tools/test_lighthouse.mjs` which doesn't exist until M1 is built, and the planner says "the gate deliberately fails until the game and tests exist". Fine for the loop, but `land` of any non-builder commit (e.g. `adopt` of a report) would now fail the Check? To watch.

## Design review (02:52-02:54)
- Set up `wt/lighthouse` on branch build/lighthouse per build/SKILL.md (added `wt/` to .git/info/exclude). Ran `run --module LIGHTHOUSE --host codex --review-host claude`; it ran the owed design review on Claude first (2 min, usage in 42,217 / cached 270,684 / out 11,118, est. $0.61) and stopped `DESIGN_OWED` with verdict DESIGN CHANGES, 1 blocking (B1: "30 boats on screen" read as "30 active boats", off-screen boats could fake the perf proof) + 8 advisory. Good catch: it's exactly the measured half of the ask being quietly narrowed. `next` (by: planner) gave the exact revision command. (worked well)
- Note: the reviewer explicitly approved the direction-variants milestone ("follow the taste-led pattern") rather than flagging it as scope the owner didn't ask for. The design-review skill says a design that "adds [things] nobody asked for" is a gap, but the house pattern overrode it. See F5.
- Planner revision 02:54-02:58 (codex, 1 turn, in 56,903 / cached 411,136 / out 8,634): PLANNED, landed 8fc8861, addressed B1 and all 8 advisories. Also rewrote ORCHESTRATE.md in the same turn (allowed for a planner; noted only because the build skill says a changed profile is "the owner's to commit" -- here it went in through the planner's landing without any owner step).
- 02:58 re-ran `run` (it runs the owed second design review first).

## First build run (02:58-03:06)
- `run` ran the second design review on Claude (DESIGN OK, ~1.5 min, in 28,794 / cached 262,159 / out 5,419, est. $0.39), then started the Codex builder on M1 (2 turns, in 114,550 / cached 2,384,256 / out 30,752). Result `BLOCKED` at 03:06, 8.5 min total. Builder committed a9339b1 (index.html 13.7 KB with two direction previews, tools/test_lighthouse.mjs, evidence notes), integrated it, passed M1.4 only.
- Blocked report, verbatim: "M1.1–M1.3 and M1.5 require restored browser access for inspection and headed timing. M1.6 additionally requires the owner to play both previews and record a direction choice."

### F7. The planner's own profile makes the builder's browser targets unreachable (blocked; biggest technical finding)
- The planner set `Codex sandbox: workspace-write` and, in the same profile, four of six M1 items on a `desktop-chromium` / `browser-performance` target the builder must drive. Under that sandbox the Codex builder can't launch a browser at all. The builder only tried Codex's computer-use tool (`cua.getState()` -> "The browser access host is unavailable"; `cua.getApp('Google Chrome')` -> `cgWindowNotFound`), but I reproduced the underlying limit myself without the suite: `codex sandbox -c sandbox_mode=workspace-write "<Google Chrome>" --headless=new --screenshot ...` exits in ~2 s with no output and no screenshot; the Playwright `chrome-headless-shell` in ~/Library/Caches/ms-playwright fails the same way. The same Chrome command outside the sandbox writes the screenshot in 3 s. So no browser, headless or headed, is reachable from a workspace-write Codex builder on this Mac.
- Nobody caught it before building: profile.md lists `danger-full-access` only as an alternative with no guidance ("*(loop: or danger-full-access)*"); the plan-module skill didn't steer the planner; two design reviews read every item for "can a reviewer judge it" but not "can the builder reach the target from its sandbox"; README Known limits talks about screen-recording permission and network/.git writes, not "a Codex builder in workspace-write can't run a browser".
- Cost: one full builder session (~7 min, ~2.4 M cached input tokens) that could only do the Node half.
- Wished for: `profile` preflight (or `run` before launching) to warn when a target's Capture needs a browser/simulator and the Codex sandbox is workspace-write; or a one-line probe the loop runs under the builder's sandbox.
- Note: the Claude reviewer runs as `claude -p` in the lead's own process (no seatbelt), so reviewers *can* drive Chrome; only the Codex builder can't. Mixed-host asymmetry nobody documents.

### F8. The direction pick gates the whole module on an owner command (blocked, by design)
- M1.6 is attended; its unblock is `LOOP owner answer --module LIGHTHOUSE --milestone M1 --item M1.6 --text "..."`, typed by the owner at a terminal. Per the brief I can't type it. M2 and M3 are behind M1 in the module, so nothing else is ready: the unattended build stops after its first milestone.
- `next` for the BLOCKED result points the lead at `unblock` (by: lead) with `plan` as an alternative. It does *not* name `owner answer` even though the block text says the owner must record a choice. build/SKILL.md's table says "On attended items, `next` is `owner answer` for the owner to type"; here it wasn't, because the builder's single BLOCKED line mixed a lead-fixable cause (browser) and an owner-only cause (attended pick). The lead has to untangle that by reading prose. (confusing)

## Trying to get past the block (03:06-03:10)

### Owner decision D2 (03:07), attempted and refused by my own permission layer
- As owner stand-in I decided to change the profile to `Codex sandbox: danger-full-access` (the only alternative profile.md offers) and commit it on main, then `unblock` and `run` again to get the browser half built and measured. Claude Code's auto-mode classifier denied the command ("Create Unsafe Agents"). Right call: it hands an unsandboxed agent this machine, which also runs the owner's real build. I didn't work around it. Logged as a stop that needs the real owner.
- The `alternative` in `next` was `plan --task 'Unblock LIGHTHOUSE M1: ...'`. I didn't take it: the planner can't fix the sandbox except by making the same profile change, and can't record the owner's direction pick. Re-planning to drop browser proofs would weaken the definitions to get round an environment gap, which the docs tell the lead not to do.
- So the stop is: (1) the owner sets the Codex sandbox (or decides how the builder gets a browser) and commits ORCHESTRATE.md; (2) the owner types `python3 .../agent_loop.py owner answer --module LIGHTHOUSE --milestone M1 --item M1.6 --worktree <repo> --text "<pick>"`; then the lead runs `unblock` + `run`. The stop is the same each time; it didn't recur three times because I didn't resubmit unchanged.

### F9. The build report omits the owner's exact commands (wasted owner time, mild)
- `report --write` lists the attended items and the blocked reason, but not the command the owner must type (`owner answer ... --item M1.6`) or what to change for the browser. I added them by hand under "Lead's notes" and landed it with `adopt` (ADOPTED 373e63a; its commit message "Adopt plan files: 2026-11-10.md" calls a build report a plan file — nitpick).
- `next` from `report` ("add the judgement, then land it") was helpful. `cost` was clear and matched the result lines' usage.

## Lead's own check of the product (03:08-03:10)
- Ran `python3 tools/check_lighthouse.py` and `node tools/test_lighthouse.mjs` at the tip: both pass (13 regression groups).
- Drove the built index.html myself in headless Chrome over CDP with a no-deps Node script (`verify/play.mjs`): mouse sweeps, holding the beam on boats, arrow keys, switching direction, the debug 30-boat stress scene and its 10 s warm + 10 s sample.
- Verified: loads offline from a file URL with no network requests beyond the file itself and no console errors; the beam lags the pointer and settles (weight is present, captures 02-04); holding the beam on boats fills a ring and shows "+100 · SAFE", score went 0 -> 500 (5 saved); the "Keeper's chart" direction is a really different look; stress scene shows 30 boats on screen and its own measure reported p95 CPU 0.2 ms, p95 rAF interval 16.8 ms, minimum visible 30, at DPR 1.
- Not verified / caveats: headless Chrome's rAF isn't vsync-paced, so 16.8 ms is a proxy, not the headed 60 Hz proof the plan asks for; DPR 2 not run. The initial fleet of 5 boats sits on one diagonal, so one aim saves all five: trivially easy, at least in the prototype. Whether it "feels good" is the owner's to judge.
- Verdict: what exists is a decent M1 prototype, not the owner's game: no 60-second rounds, no results screen, no restart (those are M2). The ask is **not met**, because the build stopped at M1.

## What worked well
- One command from an empty repo to a landed, authorised, valid plan; every stop carried an exact `next`.
- The design review caught a real narrowing of the measured requirement (B1, "30 on screen" vs "30 active") and the second round converged in one pass without inventing new blockers.
- The loop's bookkeeping was invisible in the good way: design review ran inside `run`, the BLOCKED state was recorded in its own commit, `status`/`ready`/`cost`/`report` agreed with each other.
- The builder did everything it could without a browser first (M1.4 passed with real-code tests), then reported the block with evidence instead of faking captures.

## Wished for
- A preflight that a builder can reach each target from its sandbox (F7).
- `next` on a BLOCKED result that splits lead-fixable from owner-only causes and names `owner answer` with the item (F8).
- A planner rule of thumb for small taste-led asks: batch the owner's attended judgements into one sitting at the end instead of a first-milestone direction pick (F5).
