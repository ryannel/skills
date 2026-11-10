# Friction log: s6-icons-taste-v2, second lead (suite-v3)

Lead: Claude Code (Opus 5.5) as a subagent in the Claude desktop app's agent process, picking up the project the
first lead left BLOCKED on ICONS M1.5 (owner's pick) under suite-v2. From here every loop command uses
`suite-v3/orchestration/build/scripts/agent_loop.py` with `ORCHESTRATE_HEADLESS=1`, through `tools/loop3.sh`, which
writes raw output to `out2/raw/` and one record per command to `out2/loop-results.jsonl` (now parsing multi-line JSON
too, the gap the first lead's friction 11 hit). Hosts as set up: Claude builder, Codex reviewers.

Severity words: blocked, wasted (time or tokens), confusing, nitpick, worked well.

## Entries

### 1. Upgrading the suite mid-project needed nothing (worked well)
What I tried: point the v3 loop at a repo planned, design-reviewed and part-built by v2. `profile`, `ready` and
`status` all read the v2 profile, done-when file and acceptance record without complaint: no migration step, no
`profile_differs`, no `invalid`. `ready` still reports ICONS M1 blocked on M1.5. Neither README nor build/SKILL.md
says anything about upgrading the suite under a running project, and I'd have liked one line saying "records are
compatible across 1.5.x; just point at the new script", but the absence of a problem is the right result.

### 2. v3's `next` on the attended block now offers `relay` as `alternative` (worked well)
`ready` (v3) gives `next.command` = `owner answer ...` by owner, and a new `next.alternative` =
`agent_loop.py relay --module ICONS --milestone M1 --item M1.5 --worktree <repo> --text '<the owner's words, exactly
as they gave them to you>'`, with `why` spelling out when to use it ("If the owner can't reach a terminal and gave you
their answer in conversation ... never answer for them"). This is exactly the route the first lead wished for (its
friction 9). build/SKILL.md's BLOCKED row and "The owner's controls" say the same. Clear.

Small mismatch: the done-when file's own M1.5 `attended` text, written by the v2 planner, still names only
`owner answer`, and the `blocked` string the builder wrote repeats it. A lead reading the files rather than `next`
wouldn't learn about relay. Old plans can't know about new commands; nitpick.

### 3. `next.then` drops the hosts (confusing, as in v2)
`next.then` is `agent_loop.py run --module ICONS --worktree <repo>`, with no `--host` and no `--review-host`, and it
points at the main checkout rather than the builder's worktree `repo/.wt/ICONS`. The profile has no `Default host` and
`Review host: same`, so running `then` verbatim would start the builder on whatever host the lead runs in (Claude, by
luck right here) and, for any review `run` does, the same vendor. build/SKILL.md now says "name the host yourself on
each review" (v3 added that line), so the lead is warned, but `next` still can't be run verbatim. I add
`--host claude --review-host codex` and use the module worktree.

### 4. `relay` did what it says in under a second (worked well)
`relay --module ICONS --milestone M1 --item M1.5 --worktree <repo> --text "<owner's words verbatim>"` returned
`{"result": "DONE", "action": "relay", ..., "answer": {"by": "lead", ..., "relayed": true}, "unblocked": true, "next":
{"command": "... run --module ICONS --worktree <repo>", "by": "lead", ...}}` and landed its own commit on main
(`3de5259 orchestrate: relay ICONS M1: ...`). No tty prompt, no permission-classifier trouble (the first lead's
attempt at `owner answer` was refused by the session's classifier). The answer is stored with `by: lead`,
`relayed: true`, which is the right honesty marker. The builder's worktree is now one commit behind main; I'm
trusting `run` to bring it up, as v2 did.

### 5. Resumed builder: CLAIMED in 90 s, built a blend folder from the relayed words (worked well)
`run --module ICONS --worktree repo/.wt/ICONS --host claude --review-host codex` -> `CLAIMED`, `review: true`,
2 turns, input 88k / cached 2.0M / output 32k, cost_usd 1.74, 89 s wall. The builder caught up with main itself, drew
`directions/fineliner-loose/` (a blend gets its own folder, as M1.5 says), and wrote `directions/CHOSEN.md` that quotes
the relayed words verbatim and says plainly "relayed by the lead from conversation with the owner, not yet confirmed by
the owner". It translated each of the owner's notes into a concrete drawing rule (crest widths 0.75-1.3x, eight
different ray lengths 2.0-3.4). The relayed marker reached the builder as the docs promise.

### 6. `CLAIMED` with `review: true` carries no `next` (confusing, small)
The result line has `review: true` and the commit, but no `next` field, unlike every other stop. README says each of
`run`, `review`, `plan` "ends with one line of JSON whose `next` gives the command to run next". The build/SKILL.md
table covers it ("Run a review of that milestone at that commit"), so I built
`review --module ICONS --milestone M1 --commit fa6c577 --worktree repo/.wt/ICONS --host codex` by hand. A `next` here
would be the most-run command of a build.

### 7. Codex review of M1: PASS, and it was honest about the relay (worked well)
`review --module ICONS --milestone M1 --commit fa6c577 --host codex` -> `REVIEWED`, `PASS`, 1 turn, input 72k /
cached 734k / output 5.4k, 167 s. It wrote its inspection plan before looking, recognised icons from a label-hidden
copy first, and captured the page itself (so the browser did start for it, via escalation). On M1.5 it says the pass
"rests on the relayed answer ... by `lead`" and "does not establish direct owner confirmation". That's the right level
of honesty for a relay. `next` was the M2 `run`, with "`run` fast-forwards a clean worktree that's behind main itself,
so there's no need to merge first": a nice touch that answers the question before it's asked.

### 8. The loop warns against the reviewer host the owner chose (confusing)
The same result carries `warnings`: "target web-chrome, ICONS M1.2, ... need a browser, and a browser won't start
inside Codex's workspace-write sandbox ... Run this on Claude (--host claude), or have the owner set
`Codex sandbox: danger-full-access`". This run says otherwise: the Codex reviewer got Chrome and committed captures.
The warning fires after the review rather than before (README: "The loop warns before a Codex turn"), and for a
project whose owner asked for Codex reviewers it pushes the lead toward same-vendor review. I kept Codex since it
worked. Expected: the warning before launch, and softened once a Codex session in this repo has been seen to get a
browser.

### 9. M2 built in one Claude turn, 7 min 20 s (worked well)
`run ... --host claude --review-host codex` -> `CLAIMED`, `review: true`, commit d9622c0, 1 turn, input 99k /
cached 2.24M / output 33k, cost_usd 2.34. Eight icons 611-929 bytes, `preview.html` with 32 inline SVGs, all three
checks pass when I rerun them. Again no `next` on the CLAIMED line (entry 6), so I typed the review command.

### 10. Codex review of M2: PASS first time, with one real advisory (worked well)
`review --module ICONS --milestone M2 --commit d9622c0 --host codex` -> `PASS`, 1 turn, input 95k / cached 1.15M /
output 9.2k, 4 min 43 s. Named icons from an unlabelled, randomised capture first; compared the set against the anchor
files; rebuilt from source in an isolated, network-denied copy. Its one advisory is real and I reproduced it: the
builder committed `tools/__pycache__/gen_directions.cpython-315.pyc`, so rerunning the generator dirties the tree
(`git status` shows ` M tools/__pycache__/...pyc` after `python3 -I tools/gen_directions.py`). Same "browser won't
start in workspace-write" warning as entry 8, again after a review that got a browser.

Where I'd have marked it harder: M2.4 passes low tide as "lower water". Its water lines sit about 1-2 units lower than
high tide's; the pair really differs by the chevron alone. The item only asks that they "differ in one obvious way",
so the pass is fair to the words; the words were loose.

### 11. `report` stamps the first design verdict an hour after the second (bug, nitpick)
`report --write` lists "ICONS design: changes (2026-11-10T02:58:51Z), design-review-1.md" above "ICONS design: ok
(2026-11-10T01:58:51Z, codex)". The DESIGN CHANGES review landed at 01:53:50Z (`b682594 2026-11-10 02:53:50 +0100`).
02:58:51 is the local (+0100) time of `9993f92`, the DESIGN OK commit that renamed the old file to
`design-review-1.md`, printed with a `Z`. So the archived review takes the rename commit's time, in local time, labelled
UTC. Verified from `git log --date=iso`. It did fix the first lead's friction 12: the old verdict is now listed.

### 12. A resumed session's `usage` is cumulative over the session, not this run (confusing; suspected)
The v2 BLOCKED run and the v3 resumed run share thread `7bc5b68f`. The v2 line said 1 turn / 69k in / 1.20M cached;
the v3 CLAIMED line says 2 turns / 88k in / 2.00M cached. `report` and `cost` show M1 build as "2 turns, 88k in", so
the v3 line covers both turns, and summing result lines (what the brief asks of a lead) double-counts the first one. I
use `cost` for totals. The README's usage row doesn't say which way it counts.

### 13. Small things at the end
- `adopt` of the build report commits as `Adopt plan files: 2026-11-10.md` (a report, not a plan file).
- `ready` at the end: `next.command: null`, "every module is finished". Clear.
- build/SKILL.md says "remove worktrees whose work has landed"; `git worktree remove .wt/ICONS` was all it took. The
  loop's own `.git/orchestrate/verify/*` worktrees stay listed by `git worktree list`; nothing says whether the lead
  should leave them (I did).

### 14. What worked well overall
From the owner's chat answer to a finished, accepted set took five loop commands and 17 minutes of wall clock
(02:30-02:47Z): relay, run (M1 finish), review, run (M2), review. Every hand-off except the two CLAIMED lines came with
`next`. Relay closes the biggest gap the first lead found, and it stays honest: the relay marker travels to
`CHOSEN.md`, both reviews and the report, with the owner's confirm-or-overturn command ready to type. The suite
upgrade under a live project was invisible.

### Wished for
- `next` on `CLAIMED` with `review: true` (the review command, with the review host).
- `next` commands that keep the hosts and worktree the lead last used, or a profile default of `Review host: other`
  when both CLIs are present.
- Host warnings that take account of what actually happened in this repo, and that arrive before the turn.
