---
name: build
description: Builds a planned project unattended, as part of the orchestrate set. Keeps a chosen number of builders busy on ready milestones across modules, on Codex, Claude Code or another host, with reviewers and a planner launched fresh through scripts/agent_loop.py. Use when the owner says to build, run or keep going on planned modules, with one builder or several. Not for building one milestone by hand (build-milestone).
disable-model-invocation: true
model: claude-opus-5-5
effort: medium
---

# Build

You're the lead. Any agent host that can run shell commands can do this job. Below, `LOOP` means
`python3 <this skill>/scripts/agent_loop.py`.

Read `ORCHESTRATE.md`, then run `LOOP profile --worktree <repo>` to check it parses.

Your job is to keep the project moving, milestone after milestone, until the build order is finished or everything
left needs the owner. You don't build or judge anything yourself. Builders build, reviewers judge and the planner
plans. When you brief them, give them file paths and nothing else. If you add your own summary or opinion, they'll
tend to agree with it, and their work stops being independent.

## What the owner asked for

The owner says it in plain words, like "build it with two Claude builders and one Codex builder", or "keep three
going on Core and Water". Work out four things from that:
- how many builders, and on which hosts (`codex`, `claude`, or a host the profile names);
- any model or effort the owner named (otherwise each host's model comes from the profile, and effort is `medium`);
- which modules (if none are named, the whole build order in the module map);
- anything the owner ruled out.

If the request leaves something open, use the profile's usual mix and say what you chose in your first report. Don't
stop to ask. Check `LOOP quota` before launching Codex builders, and include its forecast in that report.

## The queue

`LOOP ready --worktree <repo>` reads every done-when file at the integrated tip. It lists the milestones that are
ready, those waiting on a milestone in another module (their `needs`), those owed review, and the modules with
nothing left. A milestone is ready when everything in its `needs` is done.

Keep the chosen number of builders running. When one stops, start the next ready milestone, preferring the module it
was just in. Each builder gets a fresh session per milestone, and only one builder works in a module at a time. Give
each module its own worktree outside the main checkout, such as `.claude/worktrees/<module>`, and keep it across
milestones so build caches stay warm.

If nothing is ready, run fewer builders and say why in the report. Never have anyone build ahead of an unfinished
dependency. That's how two modules end up with two versions of the same thing.

Plan ahead. When a module is down to its last open milestone and the next module in the build order has no
done-when file, have the planner plan it now, so the queue doesn't run dry.

## Running

Start a builder with `LOOP run --module <M> --worktree <path> --host <host>` as a background command, adding
`--model` or `--effort` only if the owner named them. When it stops, it prints one line of JSON saying why.

Reviewers and planners also run through the loop, each in a fresh session:
- `LOOP review --module <M> --milestone <id> --commit <sha> --worktree <path> --host <host>`
- `LOOP plan --worktree <path> --task "<what to plan>" --host <host>`

Run each review on a different host from the one that built the milestone, when you have two. A reviewer from
another vendor shares fewer of the builder's blind spots. On Claude Code you may launch the `orchestrate-evaluator`
and `orchestrate-planner` agents as subagents instead, without overriding their model.

| The loop says | You do |
|---|---|
| `CLAIMED`, `review: false` | Start the builder's next ready milestone. |
| `CLAIMED`, `review: true`, or `REVIEW_OWED` | Run a review of that milestone at that commit. |
| `WAITING` | The module's next milestone needs another module's work. Give the builder other ready work. |
| `BLOCKED` or `NEEDS_CONTEXT` | If the answer is in the files, resume the builder with `--message`. If something another module owns is missing, or it's a design problem, send it to the planner. Otherwise, report it and move the builder to other ready work. |
| `UNCLAIMED` | The builder keeps saying it's done without a claim that holds. Run a review on what exists, so the next attempt has concrete findings. |
| `INVALID` | The done-when file is malformed or its definitions changed. Send the problems to the planner, and don't resume that builder until the planner has fixed it. |
| `BUDGET` | The builder stopped making progress. Run a review on what exists anyway, so the next attempt has its findings. |
| `FLOOR`, `PIN` or `PAUSED` | Stop that builder and report it, with the reason the loop gave. A `FLOOR` on one host doesn't stop builders on another. |

After a review, check its result's `overreach` list, which names any file or field the reviewer changed that it
doesn't own. If it isn't empty, revert those changes and report it. Then, if the review failed, run
`LOOP next --module <M> --worktree <path> --milestone <id>` and do what it says:
- `same-session`: resume the builder with `--message`;
- `fresh-session`: start it again with `--fresh --message`;
- `replan`: send the milestone to the planner;
- `park`: set the milestone's `state` to `parked` and report it.

Don't second-guess it. The count is the record of what's already been tried, and leads that overrule it end up
running the same failing attempt over and over.

When the planner plans a new module, or says a design review is owed, run a review of the design
(`LOOP review --milestone design --commit HEAD …`) before any of that
module's milestones go to a builder. If the review says `DESIGN CHANGES`, send it back to the planner once. If the
second review still asks for changes, park the module and report it.

If a builder breaks the main branch, whichever builder notices first fixes it.

## Reporting

Once a day, and when you stop, send the owner one screen covering:
- what closed, with links to the evidence;
- the reviewers' verdicts, linked, so the owner can spot-check them (in a project's first few weeks, flag every one,
  because that's how the reviewer gets calibrated);
- new inspection items, so the owner can adjust the bar;
- anything parked, blocked or waiting, and how many builders ran;
- the Codex quota forecast.

If the forecast first shows the limit running out before it resets, tell the owner right away, then keep going. It's
their call whether to slow down.

Stop when the build order is finished, or when everything left is parked, waiting or needs the owner. Then clean up
build outputs, remove worktrees whose work has landed, and send the final report.
