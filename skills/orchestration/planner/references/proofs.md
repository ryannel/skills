# Ways to prove an item

An item is one thing that must be true before a work package is Done. It names one or more proofs, a `check`, an
`inspect` or an `ask`, and passes only when each of them passes. This file is about how to prove one: which kind of
proof to choose when planning, how a builder or a reviewer inspects work, and how work judged by taste is handled.

Contents:
- [Kinds to start from](#kinds-to-start-from)
- [What a proof costs](#what-a-proof-costs)
- [How to inspect](#how-to-inspect)
- [Who can give the proof](#who-can-give-the-proof)
- [Subjective work](#subjective-work)

## Kinds to start from

These are starting points, not a fixed list. A project can describe its own kinds in a guidance file its settings
list under Project guidance, in the same shape.

| Kind | Uses | What to write | It is too weak if |
|---|---|---|---|
| Benchmark tripwire | `check` | What to measure, and a threshold from the vision and scope document or a recorded baseline; see [what a proof costs](#what-a-proof-costs) for a number the user gave | Someone made the number up. It ran on a busy or different machine |
| Visual quality | `inspect` | One quality, and the views that show it | It is one flattering shot, or screenshots from a different build |
| 2D image | `inspect` | The parts of the image, each seen whole, cropped at full resolution, and at the size it is shown | It was judged only as a thumbnail, or in one condition |
| 3D asset | `inspect` | The parts of the model, each seen from several angles and distances, in its real lighting | It is one hero angle, or the turntable never shows the underside |
| Motion or behaviour | `inspect` | What moves (physics, animation, simulation), and a scenario that shows it, as a sequence of frames | It is one still, or a slowed-down or close-up recording |
| User journey | `inspect` | The steps and their states: empty, loading, error and resize for a screen; bad arguments, piped input and exit codes for a command-line tool | Only the easy path was tried |
| Options to choose from | `inspect`; the pick in the work package after it carries `needs` with the type `human_feedback` | A few options for one representative piece, different in kind, for the user to pick from | The options are one idea in three colours |
| Code or interface | `ask` | A question about a part the architecture depends on, with a real answer, such as "does every query go through the access layer?" | It asks for an opinion, or about a detail a check or the builder could settle |

## What a proof costs

Most proofs are cheap. A proof's cost decides a lot only when it is slow, when it needs something only one run at a
time may use, or when it needs the user, and then it depends on how the build runs, not only on the item.

A check runs more often than it looks from the item. The builder runs it while working, and after the builder
merges, the script runs every check again on the main branch's tip before it accepts the work package. A check that
needs a resource only one run may use at a time runs one after another across every builder, so with ten builders a
fifteen-minute check can wait two hours for its turn.

Two things make that cheaper. An item's `reads` field names the files its check reads, so a check of one module
isn't run again because another module merged. And a resource that several runs can share, such as a GPU for renders
and tests, goes on the `Shared resources` line with how many runs it can serve at once. Its items take
`"lock": "gpu"`, and only an item whose run needs the whole device, such as all of its memory, takes
`"lock": "gpu.alone"`.

The project's test command costs more again, because every merge waits for it, and its length caps how many merges
an hour the whole project gets. Keep it quick, and keep work that needs a shared resource, such as GPU tests, in item
checks or main-branch checks that take the lock. When the test command has to use the device, name its lock on the
`Test command lock` line, and merges then wait for the device as well as for each other. No item needs to run the test
command itself, because the merge already ran it on the merged work.

When a project has history, its past reviews show which proofs found real faults. Often most were found by reading
the code or by a quick test on the CPU, and those deserve the most items.

Where a proof runs follows from who a fault would hurt:

- A fault that would stop every builder, such as a broken build or a failing test on the main branch, is worth
  catching before the merge. Put the cheap, repeatable checks that catch it in the test command, and keep that
  command quick enough that merges don't queue behind it.
- A fault that would cost only its own module an hour or two, such as an image that moved or a slower frame, is
  cheaper to find after the merge. One run on the main branch covers everything merged since the last run, whoever
  merged it, and a failure is fixed by the module that caused it while the others carry on. Write such a check as a
  `Main-branch check` line in the project settings, whose note in `settings --template` says how the line is
  written. No item waits on it, because a work package is done on what it can show before the merge, and a builder
  waiting on a slow shared check holds up its module for nothing. Such a check runs while builders are busy, so if load can spoil a run without
  saying anything about the code, as when a capture drops frames, have the check notice and exit 75. That tells the
  script the run couldn't judge the commit, so it tries again and doesn't blame whichever commit happened to run on
  a busy machine.
- A measurement that needs a quiet machine, such as a timing, rarely gets one while builders are working, and a
  `.alone` lock doesn't make one, because builders' own builds and tests take no lock. Within a work package, use a
  generous benchmark tripwire that catches a collapse. Put the precise numbers in one work package
  and give it `"alone": true`, so the script builds it with no other agent working. When several modules need
  precise numbers, gather them into one work package near the end of the project, so the machine is held once.

A proof that has to be recorded before a merge and matched to the exact code costs more with every builder, because
it goes stale whenever the main branch changes the files it covers. When making it takes longer than the main branch
stays still, builders can spend their sessions remaking it. Prefer a run after the merge. Where it must come first,
draw what it covers as narrowly as its real inputs.

Write each check so it still runs when the machine is in a state the product has to cope with, such as a locked screen
or a denied permission. Have the check record that state and pass either way, unless the item really depends on it.

## How to inspect

This applies to a builder checking its own work before it ends with `DONE`, and to a reviewer. An `inspect` item is a
checklist the planner wrote from the work package's reference. Answer each line in the views and conditions it names
(the table under [kinds to start from](#kinds-to-start-from) gives them for each kind), with crops at full resolution
rather than a scaled-down copy, the edge conditions the settings list for the target, and the reference open beside
the work rather than your memory of it.

What you can perceive depends on your tools. Record anything that moves as a sequence of frames, because most agents
can't watch live video. Prove what you can't perceive with a measurement.

## Who can give the proof

Check that whoever you name can give the proof.

A reviewer reads the settings and the design before it judges, so it can't stand in for a reader new to something,
such as "a new end user can follow the setup guide alone". Have the builder start a new agent for it, given only what
that reader would have, and have the reviewer read what that agent was given and what it reported.

Check that the reviewer can reach the target too. Under the settings' `Codex sandbox: workspace-write`, a browser or
another program with a window opens only once the agent asks to run it outside the sandbox, so plan for the reviewer
to ask. The builder's screenshots can't stand in for the reviewer's own, because they show only what the builder
chose.

## Subjective work

Subjective work is work judged by taste: a game's look, a set of 3D assets, a visual design. A test can hold the
minimum requirements (the file loads, the model is under its triangle budget, the frame time holds), so write
those as `check` items as usual. The taste itself needs four more things.

### The user chooses the look first

People disagree about taste, so no reviewer can settle it for the user. When the look is the product, and a
wrong one means redoing most of the work (an asset set, a game's art style, a brand), plan two first work packages. The
first makes a few options for one representative piece, different in kind, and a reviewer checks them. The second
depends on it and has an item where the user picks one, marked as needing user feedback:
`"needs": {"type": "human_feedback", "what": "pick one option"}`, with a check that the builder saved the chosen
option in the folder the settings' `References:` line names. Splitting them means a review that fails the options
can't throw away a pick. Choosing early costs the user one sitting. Rejecting finished work costs the build. End
the module's planned stretch at the pick, and name the work packages after it in the plan file without items, because
their quality bars and checklists come from the chosen option, which doesn't exist yet. Once the pick is Done, a
planner writes them against it.

Have the builder lay the options out side by side for the user, at the size they will be used and also
enlarged, because a difference in line or texture can be a few pixels at real size. Have it save that as one
image in the working folder too. The user sees it in the chat with the lead, and won't open a file in the
repository.

Hold the options to two things only: the minimum requirements, and being different in kind. They exist so the user
can turn some down. The full quality bar starts with the chosen option, from the next work package on. A quality bar that
says "each option" must meet the look would fail the work package on the very options the user rejected.

When taste is one quality of a small build, skip the options. Build it, and put the user's judgement in one late
item marked as needing user feedback, as the planner skill says for every judgement of finished work.

### Where references are kept

The chosen option and any reference sets live in the repository, in the folder the settings' `References:` line
names, because reviewers compare with them for as long as the project runs. The checklist names the qualities to
match, so the work is held to those and not to a reference's accidents, such as its lighting or its crop.

### The builder gets a fresh opinion before a review

A builder working on an item judged by taste gets an opinion from an agent that has seen none of the work, when the
host can start one: a subagent given only the item with its checklist, the quality bar, the references and new
screenshots. The builder fixes what it finds, and asks again while the opinion keeps finding things that matter. Two
or three attempts is usual. Every attempt costs a fresh look at all the screenshots, so stop at the first one that
finds nothing you would change.

Commit each attempt, and keep the best one, which isn't always the last, because quality can peak in the middle.
Options the user hasn't chosen from yet get one attempt at most, because most of them will be turned down.

This is the builder's own check, not the review. A failed review costs a whole builder run and counts towards sending
the work package back to a planner, which is the wrong price for an ordinary attempt at polish.

### What agents can't perceive goes to the user

No current agent can hear a sound or feel how a game plays. Mark those items as needing user feedback when you
plan them. Left to a reviewer they come back `could_not_judge`, which fails the work package and tells nobody
anything.
