# Worked examples

Copy the shape, not the content. Each example is short on purpose, because a short instruction is part of what it's
showing.

## A Codex goal

```text
/goal The checkout service's p95 latency on `bench/checkout --profile prod` is under 120 ms on three runs in a row.
Check this with that benchmark's output. The correctness suite (`make test-checkout`) stays green, and no test file
changes. Work only in services/checkout and its benchmarks. Ask before you touch shared libraries or add a dependency.
After each attempt, write in notes/checkout-perf.md what changed, what the benchmark showed, and what you'll try next.
If the benchmark can't run, or two days of attempts don't move p95, stop. Report the evidence, what you tried, and
what would unblock it.
```

## A Claude Code goal condition

```text
/goal `cargo test -p render` exits 0 and `./dev check` passes, with no test removed or marked ignored. Or stop after
30 turns and report what still fails.
```

## A steer

```text
Your M1 is too big to reach the game soon, and the proof is chasing accuracy the player can't see.
Evidence: the plan puts M1 at 10–16 days after the proof. The proof has run for 2.5 h with 0 of 19 boxes ticked, and
each step opens the next sub-question (DESIGN-PLAN.md, commits 15cef04..a3bfdad).
Threatens: the owner's choice of what to fund. That choice is waiting on a first milestone in the game.
Outcome: a first milestone you can prove in the game in about a day. Limit the proof to the cues the player actually
reads from the chase camera.
Pointers: the plan reference (milestone size) and the review calibration list. Edit the plan yourself, log why, and
have the change reviewed while you carry on.
```

## A subagent brief

```text
Find every caller of `Cache::invalidate` in the workspace, including tests, examples and the web crate.
I've already checked crates/render/src/runtime.rs, so skip it.
For each caller, give the file and line, whether it waits for completion, and whether it can run after device loss.
Return a table. Then add one line naming any caller that doesn't wait and can run after loss.
Read only. Don't edit anything.
```

## A reviewer brief

```text
You're reviewing a change you didn't write. Requirements: tmp/g3c-boundary/G3C-PLAN.md, M1 "Done when".
Artifacts: `git diff b848ad0 21586d3`, the captures in tmp/g3c-boundary/m1-chrome/, and the check logs next to them.
For each done-when item, say pass, fail or can't tell, and give the evidence. Then list everything else that's wrong,
worst first. Mark each one verified (file and line, or a way to reproduce it) or suspected. Say whether you looked at
motion or stills, and at what size. Don't edit files.
```

## An audit of a misbehaving agent

```text
Before changing any instruction, check the harness. Was the goal paused, over budget, or stopped because it made no
tool calls? Then quote each line in AGENTS.md, the active skills and the goal that bears on what you did. Mark each
one as a requirement or as your interpretation. Say which one made you stop at M1's first implementation.
```
