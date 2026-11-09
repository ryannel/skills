# Examples

Contents:
- [A reviewer brief](#a-reviewer-brief)
- [A Codex goal](#a-codex-goal)
- [A Claude Code goal condition](#a-claude-code-goal-condition)
- [A subagent brief](#a-subagent-brief)
- [A brief where the list is the task](#a-brief-where-the-list-is-the-task)
- [A steer](#a-steer)
- [An audit of an agent that went wrong](#an-audit-of-an-agent-that-went-wrong)

Copy the shape, not the content. Each one is short on purpose, because being short is part of what it shows.

## A reviewer brief

This one was written for GPT-6 Astra through `codex exec`. The first draft ran to 101 lines. It described each skill
under review, listed 24 sources to "read these yourself", gave the reviewer five areas of correctness to check and 11
user requests to walk through, and set out nine report sections. Here's a taste of it:

```text
## Foundations to judge it against
Read these yourself. Check that the suite applies them correctly, and look for newer or contradicting guidance.
- https://www.anthropic.com/engineering/harness-design-long-running-apps
- https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  … 22 more
## What to report
- Host neutrality: walk a lead on Claude Code, one on Codex, and one on a host with no adapter through `build`. …
- Generic use: walk one web app, one CLI tool and one game through the suite, …
- Dogfooding, as its own section: … Start with these, and add others engineers will hit:
  - "Build just the auth module and stop."
  … 10 more
```

The person it was for rejected it: "These models are smarter than you are. Don't list what to look at." This is what
went instead, launched with `codex exec -m gpt-6-astra -c model_reasoning_effort=high`:

```text
Review the orchestrate suite (skills/orchestration/) and skill-creator (skills/skill-creator/) in this repo, second
round. They're meant to let capable agents plan, build and review software of any kind, on Claude Code, Codex or any
other agent host, with "done" resting on evidence rather than a builder's word, in the fewest plain words that work.

Yesterday's reviews, the decisions taken and the newest design are in workbench/review-2026-11-08/. Form your own
view first; another reviewer is working in parallel, so independence matters more than agreement.

Also dogfood it: think about what engineers actually want to do day to day with a suite like this, and judge whether
it handles each cleanly, awkwardly or not at all.

Thrum (~/Workspace/thrum/.claude/worktrees/platform-runtime-mac, see its ORCHESTRATE.md) is one real project using
it. A builder is active there, so don't write to it.

Judge against current vendor and research guidance, not just what the suite cites.

Read-only, except: write your report to workbench/review-2026-11-08/astra-REVIEW-2.md, and use
workbench/review-2026-11-08/astra-scratch/ for throwaway experiments (delete it when done). Don't run anything that
launches a model (agent_loop.py run/review/plan, codex exec, claude -p); it spends the owner's quota.

Report everything, ranked by consequence, each finding marked verified or suspected. Done when the report has a
verdict, which of yesterday's findings are still open, your new findings, and the sources you used.
```

Everything the reviewer couldn't know is still there: the purpose, where the earlier work is, the parallel reviewer,
the live builder, the quota, the one angle the person asked for, and what done is. What's gone is everything the
reviewer could work out for itself.

## A Codex goal

The first draft of this one told the agent which technique to use and set a frame-time budget nobody had asked for:

```text
/goal Implement the bow wake as a Kelvin-angle decal using a 256×256 height grid and Gerstner waves, then add foam
from the Jacobian, then tune until the frame costs under 0.8 ms at 1440p. Read docs/water/*.md and research/wake/*.md
first. Be thorough and keep going until it looks right.
```

The rewrite says where the work ends up and leaves the method to the agent:

Launched in a Sol thread set to high effort:

```text
/goal A player on the deck of the moving ship sees a bow wake that reads correctly at every speed the game allows, in the
shipped build. Done when the water inspection list in docs/water/M2-DONE.md passes in a capture you've watched in
motion, and `./dev check` passes. The wake research is in research/wake/. Several hull-contact trials have already
been rejected, so look for the established technique before trying another variant. Work in crates/water and its
docs. Don't change the ship or camera crates. If the build can't run on the device, or the inspection list asks for
something the design can't show, stop and report what you tried and what would unblock it.
```

Pointing at M2-DONE.md makes its items requirements, which is the intent here. The research folder is named as
background, so the loop doesn't audit against it.

## A Claude Code goal condition

```text
/goal `cargo test -p render` exits 0 and `./dev check` passes, with no test removed or marked ignored. Or stop after
30 turns and report what still fails.
```

The evaluator only reads the conversation, so the condition names checks whose results will appear in it.

## A subagent brief

```text
Find every caller of `Cache::invalidate` in the workspace, including tests, examples and the web crate. I've already
checked crates/render/src/runtime.rs, so skip it. I need to know which callers don't wait for completion and can run
after device loss, because the fix changes that contract. Return a table of file, line, waits (yes or no) and can run
after loss (yes, no or unsure). Read only.
```

It gives the reason, what's ruled out, the scope, and a return shape that will be merged. It doesn't say how to search.

## A brief where the list is the task

```text
The CSV export must open correctly in each spreadsheet the customer contract names: Excel 365 on Windows, Numbers 14,
LibreOffice 24.8 and Google Sheets. Last release broke dates in Numbers (issue #412 has the file that reproduces it).
Find out which of the four handle the current export, fix what doesn't, and add a fixture test for each. Don't change
the column order; two downstream importers depend on it. Report each app with pass or fail and how you checked it.
```

The four apps, the reproduction and the column-order rule stay because the agent couldn't know them. Leaving the apps
out to keep the brief short would lose the requirement.

## A steer

```text
Your M1 is too big to reach the game soon, and the proof is chasing accuracy the player can't see.
Evidence: the plan puts M1 at 10–16 days after the proof. The proof has run for 2.5 h with 0 of 19 boxes ticked, and
each step opens another sub-question (DESIGN-PLAN.md, commits 15cef04..a3bfdad).
Threatens: the owner's choice of what to fund, which is waiting on a first milestone in the game.
Outcome: a first milestone you can prove in the game in about a day, with the proof limited to what the player reads
from the chase camera.
Where to look: the plan reference on milestone size. Edit the plan yourself, log why, and have the change reviewed
while you carry on. This adds to your current goal; it doesn't replace it.
```

## An audit of an agent that went wrong

```text
You stopped after M1's first implementation with work left. First say whether the harness stopped you: a paused
goal, the budget, or turns with no tool calls. Then quote any line in AGENTS.md, the active skills or the goal that bore
on stopping, and mark each as what it says or how you read it. If no line caused it, say so. Report only, don't edit.
```
