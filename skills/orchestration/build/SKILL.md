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

Read `ORCHESTRATE.md`, then run `LOOP profile --worktree <repo>` to check it parses. A profile that leaves out
`Integrate` or `Check` fails here on purpose: the loop won't guess whether it may push, or what gate it should run.

Your job is to keep the project moving, milestone after milestone, until the build order is finished or everything
left needs the owner. You don't build or judge anything yourself. Builders build, reviewers judge and the planner
plans. When you brief them, give them file paths and nothing else. If you add your own summary or opinion, they'll
tend to agree with it, and their work stops being independent. That means withholding your conclusions, not the task:
a restriction the owner gave only in conversation, such as "don't touch the schema", goes to the builder with
`--message`.

The loop decides what is accepted, not you and not the agents. It keeps `<MODULE>-ACCEPTED.json` next to each
done-when file, writes it only in its own commits, and counts a milestone finished only when that record accepts it.
So don't edit done-when files or records yourself, and don't revert anyone's commits. If something looks wrong, the
loop's result says what, and the table below says who fixes it.

## Where you run

Every builder, reviewer and planner the loop starts headless runs inside your process, so it gets your sandbox and
your operating-system permissions, not its own. On a Mac where the Codex app is running, Codex sessions run inside
the app instead, as threads it lists under the project, with the sandbox the loop sets and the app's permissions.
Claude sessions run in the loop's own `claude -p`, and with Claude desktop running and the CLI signed in, they're also
listed in its Code tab. Each result line says which path ran (`path`, with `path_reason` when it's `headless`). If your host sandboxes you without network or without writes to `.git`,
the builders can't fetch, commit or integrate either, so start the lead where those are allowed. On macOS, a builder
that records the screen or uses the camera needs that permission granted to the app you run in (Terminal, the Codex
app or Claude), and its first attempt fails until the owner grants it. Say which app you're running in, and which
path the sessions ran on, in your first report.

## What the owner asked for

The owner says it in plain words, like "build it with two Claude builders and one Codex builder", "keep three going
on Core and Water", or "just do Water M3". Work out from that:
- how many builders, and on which hosts (`codex`, `claude`, or a host the profile names);
- any model or effort the owner named (otherwise each host's model comes from the profile, and effort is `medium`);
- which modules, or which single milestone (if none is named, the whole build order in the module map,
  `ARCHITECTURE.md` in the profile's plans folder);
- anything the owner ruled out.

If the request leaves something open, use the profile's `Builders` line and say what you chose in your first report.
Don't stop to ask. Pass `--model` or `--effort` to the loop only when the owner asked for something other than the
default, because the loop already uses the profile's model and medium effort. Without `--host`, the loop uses the
profile's `Default host`, else the host it runs inside. Check `LOOP quota` before launching Codex builders, and
include its forecast in that report.

When the owner names one milestone or one module, that is the whole job. Once it's accepted, report and stop, rather
than moving on to the next ready milestone.

## The queue

`LOOP ready --worktree <repo>` reads every module at the integrated tip. For each one it lists the next milestone as
ready, waiting on another module (`needs`), owed review, owed a design review, blocked, parked, taken by another lead
or invalid, plus the modules with nothing left. `LOOP status` gives the same in a few lines, and `--module` lists
every milestone of one module with its last verdict. Only each module's next milestone matters, because milestones
in a module run in order.

Keep the chosen number of builders running, up to the number of ready milestones. When one stops, start the next
ready milestone, preferring the module it was just in. When there are fewer ready milestones than builders, give them
to the hosts in the order the owner listed. Each builder gets a fresh session per milestone, and only one builder
works in a module at a time. The loop claims the milestone before it starts, in a ref every clone can see, so a
second lead on the same project gets `TAKEN` instead of duplicating the work.

Give each module its own worktree on its own branch, in a folder git ignores, and keep it across milestones so build
caches stay warm. With `Integrate: push`, branch from the remote: `git worktree add -b build/<module>
<folder>/<module> <remote>/<branch>`. With `Integrate: local`, branch from the local base branch instead. Builders
integrate with `LOOP land`, which rebases, runs the Check and pushes or fast-forwards the base branch under one lock.

If nothing is ready, run fewer builders and say why in the report. Never have anyone build ahead of an unfinished
dependency. That's how two modules end up with two versions of the same thing.

Plan ahead. When a module is down to its last open milestone and the next module in the build order has no
done-when file, have the planner plan it now, so the queue doesn't run dry.

## Running

Start a builder with `LOOP run --module <M> --worktree <path> --host <host>` as a background command. When it stops,
it prints one line of JSON saying why.

Reviewers and planners also run through the loop, each in a fresh session, because only the loop can check their
work and record it:
- a milestone: `LOOP review --module <M> --milestone <id> --commit <sha> --worktree <path> --host <host>`
- a design: `LOOP review --module <M> --milestone design --worktree <path> --host <host>`
- planning: `LOOP plan --worktree <path> --task "<what to plan>" --host <host>` (in a clean worktree)

Run each review on a different host from the one that built the milestone, when two hosts work. A reviewer from
another vendor shares fewer of the builder's blind spots. If the other host fails to start (a `FLOOR`), use the same
host in a fresh session, and say so in the report.

| The loop says | You do |
|---|---|
| `CLAIMED`, `review: false` | The loop has accepted it. Start the builder's next ready milestone. |
| `CLAIMED`, `review: true`, or `REVIEW_OWED` | Run a review of that milestone at that commit. |
| `DESIGN_OWED` | Run a design review of the module. |
| `WAITING` or `TAKEN` | The milestone needs another module's work, or another lead has it. Give the builder other ready work. |
| `BLOCKED` | The loop has recorded `state: blocked` and what unblocks it. If you can supply that from the files, do, then run `LOOP unblock`. If something another module owns is missing, or it's a design problem, send it to the planner. Otherwise, put it in the report and move the builder on. |
| `NEEDS_CONTEXT` | If the answer is in the files, resume the builder with `--message`. Otherwise treat it like `BLOCKED`. |
| `UNCLAIMED` or `BUDGET` | The builder keeps saying it's done without a claim that holds, or it stopped making progress. Run a review on what exists, so the next attempt has concrete findings. |
| `INVALID` | The done-when file is malformed, an agent changed something its role doesn't own, or the definitions aren't the authorised ones. Send the problems to the planner, and don't resume that builder until a planner turn has fixed them. |
| `PARKED` or `FINISHED` | Nothing more for this module. Report a parked milestone. |
| `FLOOR`, `PIN` or `PAUSED` | Stop that builder and report it, with the reason the loop gave. A `FLOOR` on one host doesn't stop builders on another. A `PAUSED` with a `reason` means the owner stopped the session in the app or has it open there: leave it to them until they say to carry on. |

A review prints `REVIEWED` with the verdict, or `INVALID` when the reviewer did something a reviewer doesn't, such as
editing source, writing no review or naming the wrong milestone. Nothing from an invalid review lands, so run it
again, on the other host if you can. On a `FAIL`, the result's `next` says what the number of failed reviews calls
for, and `LOOP next --module <M> --worktree <path> --milestone <id>` gives the findings message to send:
- `same-session`: resume the builder with `--message`;
- `fresh-session`: start it again with `--fresh --message`;
- `replan`: send the milestone to the planner;
- `park`: the loop has parked it, so report it.

Don't second-guess it. The count is the record of what's already been tried, and leads that overrule it end up
running the same failing attempt over and over. The whole ladder is in
[the done-when reference](../plan-module/references/done-when.md#when-a-review-fails).

When the planner plans a new module, its result lists the modules owed a design review, and the queue holds them
until one passes. If the review says `DESIGN CHANGES`, send it back to the planner once. If the second review still
asks for changes, leave the module out and report it.

If a builder breaks the main branch, whichever builder notices first fixes it.

## The owner's controls

Tell the owner in your first report that these exist. Sessions on the visible path can be watched in the Codex app or
Claude's Code tab, and the owner can type into a Codex thread to steer it. Pressing Stop on a Codex thread, or opening
a Claude session to work in it, pauses that builder (`PAUSED`) and leaves the session to the owner; `LOOP run` hands it
back. The commands below the owner types at a terminal, and the loop refuses them inside any session it started, so
no agent can make these calls for the owner:
- `LOOP pause --worktree <repo>` stops running loops and their agents cleanly, and `LOOP run` carries on later;
- `LOOP owner accept|rereview|unpark|scope --module <M> --milestone <id> --reason "..."` accepts without review,
  sends an accepted milestone back for a fresh review (keeping the old one), unparks, or takes the owner's edited
  done-when file as the new scope without spending a re-plan.

## Reporting

Once a day, and when you stop, write the owner one screen in `<evidence>/build-reports/<date>.md`, and send it
however the owner follows this session. Cover:
- what closed, with links to the evidence;
- the reviewers' verdicts, linked, so the owner can spot-check them (while the project's graded examples hold fewer
  than about ten verdicts, flag every one, because that's how the reviewer gets calibrated);
- new inspection items, so the owner can adjust the bar;
- anything parked, blocked or waiting, with what unblocks it, and every attended item that needs a person or
  hardware gathered into one list, so the owner can do them in one sitting;
- how many builders ran, and the Codex quota forecast.

If the forecast first shows the limit running out before it resets (its `runs_out` is set), tell the owner right
away, then keep going. It's their call whether to slow down.

Stop when the build order is finished, or when everything left is parked, blocked, waiting or needs the owner. Then
clean up build outputs, remove worktrees whose work has landed, and send the final report.
