# Worked examples

Copy the shape, not the content. Each example is short on purpose.

## A Codex goal

```text
/goal The checkout service's p95 latency on `bench/checkout --profile prod` is under 120 ms on three consecutive runs.
Verify with that benchmark's output. The correctness suite (`make test-checkout`) stays green and no test file changes.
Work only in services/checkout and its benchmarks; ask before touching shared libraries or adding a dependency.
Each iteration, record in notes/checkout-perf.md what changed, what the benchmark showed and the next experiment.
If the benchmark can't run, or two days of attempts don't move p95, stop and report the evidence, what was tried and
what would unblock it.
```

## A Claude Code goal condition

```text
/goal `cargo test -p render` exits 0 and `./dev check` passes, with no test removed or marked ignored; or stop
after 30 turns and report what still fails.
```

## A steer

```text
Your M1 is too large to reach the game soon, and the proof is chasing accuracy the player can't see.
Evidence: the plan estimates M1 at 10–16 days after the proof; the proof has run 2.5 h with 0 of 19 boxes ticked, each
step opening the next sub-question (DESIGN-PLAN.md, commits 15cef04..a3bfdad).
Threatens: the owner's choice of what to fund, which waits on a first in-game milestone.
Outcome: a first milestone you can prove in the game within about a day, with the proof bounded by the cues the player
reads at the chase camera.
Pointers: the plan reference (milestone size) and the review calibration list. Edit the plan yourself, log why and have
the change reviewed while you carry on.
```

## A subagent brief

```text
Find every caller of `FrameHost::capture` across the workspace, including tests, examples and the browser crate.
I've already checked crates/render/src/runtime.rs; skip it.
For each caller, return the file and line, whether it waits on completion, and whether it can run after device loss.
Return a table, then one line naming any caller that both skips waiting and can run after loss.
Read only; don't edit anything.
```

## A reviewer brief

```text
You're reviewing a change you didn't write. Requirements: tmp/g3c-boundary/G3C-PLAN.md, M1 "Done when".
Artifacts: `git diff b848ad0 21586d3`, the captures in tmp/g3c-boundary/m1-chrome/ and the check logs beside them.
For each done-when item, say pass, fail or can't tell, with evidence. Then list everything else that's wrong, ranked
by consequence, each marked verified (file and line, or a reproduction) or suspected. Say whether you inspected motion
or stills, and at what size. Don't edit files.
```

## An audit of a misbehaving agent

```text
Before changing any instruction, check the harness: was the goal paused, over budget, or stopped for lack of tool calls?
Then quote each line in AGENTS.md, the active skills and the goal that bears on the behaviour, mark it as a requirement
or as your interpretation, and say which one made you stop at M1's first implementation.
```
