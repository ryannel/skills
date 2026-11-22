# Ways to prove an item

An item is one thing that must be true before a milestone is Done. This file is about how to prove one: which
kind of proof to choose when planning, how a builder or a reviewer inspects work, and how work judged by taste is
handled.

Contents:
- [The three ways](#the-three-ways)
- [Kinds to start from](#kinds-to-start-from)
- [What a proof costs](#what-a-proof-costs)
- [How to inspect](#how-to-inspect)
- [Who can give the proof](#who-can-give-the-proof)
- [Subjective work](#subjective-work)

## The three ways

Every item names one or more proofs, and passes only when each of them passes:

- A `check` is a shell command that passes when it exits with 0. The builder runs it, and the script runs it again
  before it accepts the builder's word.
- An `inspect` is a yes/no checklist the planner drew from the reference in the milestone's `quality_bar`. A reviewer
  runs the product and answers each line, as [how to inspect](#how-to-inspect) says.
- An `ask` is a question a reviewer answers by reading the code, an interface or a design, kept to the parts of the
  plan the architecture depends on.

Often one proof isn't enough, because each kind misses different things. Take a ball bouncing in a physics game. A
check that the energy never grows catches a slow drift nobody would notice by eye. A sequence of frames of the ball
rolling down a steep slope catches motion that is stable and still looks wrong. So that item gets both.

## Kinds to start from

These are starting points, not a fixed list. A project can describe its own kinds in a guidance file its settings
list under Project guidance, in the same shape.

| Kind | Uses | What to write | It is too weak if |
|---|---|---|---|
| Automated test | `check` | The behaviour, and a command that tests it end to end | It tests a mock, or only the easy path |
| Property or fuzz test | `check` | The rule that must always hold, the inputs to throw at it, and for how long | The inputs miss the cases that happen in real use |
| Golden output | `check` | The expected output, how close is close enough, and why it is right | The golden file was made by the code under test, and nobody checked it |
| Benchmark tripwire | `check` | What to measure, and a threshold from the brief or a recorded baseline; see [what a proof costs](#what-a-proof-costs) for a number the user gave | Someone made the number up. It ran on a busy or different machine |
| Determinism | `check` | The same input, run twice, gives the same output (frames, files, results) | It compares a run only with itself in one process, or ignores timing and threads |
| Visual quality | `inspect` | One quality, and the views that show it | It is one flattering shot, or screenshots from a different build |
| 2D image | `inspect` | The parts of the image, each seen whole, cropped at full resolution, and at the size it is shown | It was judged only as a thumbnail, or in one condition |
| 3D asset | `inspect` | The parts of the model, each seen from several angles and distances, in its real lighting | It is one hero angle, or the turntable never shows the underside |
| Motion or behaviour | `inspect` | What moves (physics, animation, simulation), and a scenario that shows it, as a sequence of frames | It is one still, or a slowed-down or close-up recording |
| User journey | `inspect` | The steps and their states: empty, loading, error and resize for a screen; bad arguments, piped input and exit codes for a command-line tool | Only the easy path was tried |
| Options to choose from | `inspect`; the pick in the milestone after it carries `needs` with the type `human_feedback` | A few options for one representative piece, different in kind, for the user to pick from | The options are one idea in three colours |
| Code or interface | `ask` | A question about a part the architecture depends on, with a real answer, such as "does every query go through the access layer?" | It asks for an opinion, or about a detail a check or the builder could settle |

## What a proof costs

A proof is worth what it catches, set against what it costs, and both depend on how the build runs, not only on
the item. Most proofs are cheap, so this rarely decides anything. It decides a lot when a proof is slow, when it
needs something only one run at a time may use, or when it needs the user.

A check runs more often than it looks from the item. The builder runs it while working. After the builder
merges, the script runs every check again on the main branch's tip, one after another, before it sets the milestone
Ready for Review, and that run is the proof of record. A check that needs a resource only one run may use at a time
runs one after another across every builder, so with ten builders a fifteen-minute check can wait two hours for its
turn.

Two settings make that cheaper. An item's `reads` field names the files its check reads, and the script reuses the
check's last pass while those files and the command stay the same, so a check of one module isn't run again because
another module merged. And a resource that several runs can share, such as a GPU for renders and tests, goes on the
`Shared resources` line with how many runs it can serve at once. Its items take `"lock": "gpu"`, and only an item
whose run needs the whole device, such as all of its memory, takes `"lock": "gpu.alone"`.

The project's test command costs more again, because every merge waits for it. Keep work that needs a shared resource,
such as GPU tests, in item checks or main-branch checks that take the lock where you can. When the test command has to
use the device, name its lock on the `Test command lock` line, such as `gpu`, and the script takes it wherever it runs
the test command. Merges then wait for the device as well as for each other. The lock hold limit doesn't stop the test
command, which runs for up to an hour, because one stopped part way would fail every merge. Branches that arrive
together are merged as one batch with one run of the test command, but a batch still waits for the one before it, so
the command's length sets how many batches an hour the project can merge. A test command that takes fifteen minutes
allows about four, shared by every builder, and a failure costs more runs, because the script splits the batch in
halves until it finds the branch that broke it.

So for each proof, weigh four things: what it would catch, how likely that fault is here, what the fault would cost
if it were caught later instead, and what the proof costs now, in time and in queueing for the builders who share
its resource. When a project has history, its past reviews show which proofs found real faults. Often most of them
were found by reading the code or by a quick test on the CPU, and those deserve the most items.

Where a proof runs follows from who a fault would hurt:

- A fault that would stop every builder, such as a broken build or a failing test on the main branch, is worth
  catching before the merge. Put the cheap, repeatable checks that catch it in the test command, and keep that
  command quick enough that merges don't queue behind it.
- A fault that would cost only its own module an hour or two, such as an image that moved or a slower frame, is
  cheaper to find after the merge. One run on the main branch covers everything merged since the last run, whoever
  merged it, and a failure is fixed by the module that caused it while the others carry on. Declare such a check as
  a `Main-branch check` line in the project settings, with how often it may run and the locks it needs, and give
  each item that depends on it the check `python3 "$ORCHESTRATE_SCRIPT" main-check <name>`, which passes from the
  shared run. Give that item no `lock` of its own: the settings line takes the locks for the run, and an item lock
  held while it waits would block the very run it is waiting for. Such a check runs while builders are busy, so
  if load can spoil a run without saying anything about the code, as when a capture drops frames, have the check
  notice and exit 75. That tells the script the run couldn't judge the commit, so it tries again and doesn't blame
  whichever commit happened to run on a busy machine.
- A measurement that needs a quiet machine, such as a timing, rarely gets one while builders are working. Within
  a milestone, use a generous benchmark tripwire that catches a collapse. Put the precise numbers in one milestone
  and give it `"alone": true`, so the script builds it with no other agent working. When several modules need
  precise numbers, gather them into one milestone near the end of the project, so the machine is held once.
- A proof that needs the user, such as a run on a real device, costs a sitting each time. Gather those items into
  the module's last milestone too, so one sitting covers them.

Two more patterns make a proof's cost grow with the number of builders:

- A proof that has to be recorded before a merge and matched to the exact code goes stale whenever the main branch
  changes the files it covers. When making it takes longer than the main branch stays still, builders can spend
  their sessions remaking it. Prefer a run after the merge. Where it must come first, draw what it covers as
  narrowly as its real inputs.
- A resource held alone by work that doesn't need it alone makes everything queue, which is why `.alone` is only for
  runs that need the whole device. It doesn't buy a quiet machine for a timing either, because a lock keeps out only
  runs that take it, and builders' own builds and tests take none.

Write each check so it still runs when the machine is in a state the product has to cope with, such as a locked screen
or a denied permission. Have the check record that state and pass either way, unless the item really depends on it.

## How to inspect

This applies to a builder checking its own work before it ends with `DONE`, and to a reviewer. An `inspect` item is a
checklist the planner wrote from the milestone's reference: what to look at, then each thing the work must match, as
a yes or no. Work down it, because a reader without a list looks at whatever catches its eye, decides it looks fine,
and misses the broken parts.

Look at each entry in the views and conditions it needs. A 3D model needs a few angles. An image needs close crops as
well as the whole frame, so use a crop or zoom tool rather than judge a scaled-down copy. Most things need a few
conditions, such as different times of day, or the edge conditions the settings list for the target. Anything that
moves needs the moments where it changes. Every view hides something: a bow wave can look right from the side and cut
through the hull from the front, and a cloud can look fine as a thumbnail and turn into bands when you zoom in. Put
the reference beside the work for each line, rather than judging from memory of it.

Answer each line in the review or with the evidence, so anyone can see what was looked at and what wasn't. If the
checklist misses a part of the work you can see is wrong, report that too.

What you can perceive depends on your tools. Record anything that moves as a sequence of frames, because most agents
can't watch live video. Prove what you can't perceive with a measurement. If nothing can measure it, a builder ends
with `BLOCKED needs_human_feedback` and a reviewer gives `could_not_judge`. Golden screenshots catch a regression, but
they don't prove that something looks right.

## Who can give the proof

Check that whoever you name can give the proof.

A reviewer reads the settings and the design before it judges, so it can't stand in for a reader new to something,
such as "a new end user can follow the setup guide alone". Have the builder start a new agent for it, given only what
that reader would have, and have the reviewer read what that agent was given and what it reported.

Check that the reviewer can reach the target too. A browser won't start inside Codex's default `workspace-write`
sandbox, and other programs with a window can fail there too. A Codex agent runs one by asking to run that command
outside the sandbox, which is usually granted, so plan for the reviewer to ask. The builder's screenshots can't stand
in for the reviewer's own, because they show only what the builder chose. When a module drives a browser throughout,
say so in its design, so the lead can choose its hosts.

## Subjective work

Subjective work is work judged by taste: a game's look, a set of 3D assets, a visual design. A test can hold the
minimum requirements (the file loads, the model is under its triangle budget, the frame time holds), so write
those as `check` items as usual. The taste itself needs four more things.

### The user chooses the look first

People disagree about taste, so no reviewer can settle it for the user. When the look is the product, and a
wrong one means redoing most of the work (an asset set, a game's art style, a brand), plan two first milestones. The
first makes a few options for one representative piece, different in kind, and a reviewer checks them. The second
depends on it and has an item where the user picks one, marked as needing user feedback:
`"needs": {"type": "human_feedback", "what": "pick one option"}`, with a check that the builder saved the chosen
option in the references folder. Splitting them means a review that fails the options can't throw away a pick.
Choosing early costs the user one sitting. Rejecting finished work costs the build. The user replies to the lead in
chat, and the lead saves the question and their reply with the `human feedback` command. The script records it as
User Feedback. The user has judged the pick, so it closes without a reviewer once its checks pass. The milestones
after the pick are named in the plan file without items, so once the pick is Done the script asks for a planner, who
writes them against the chosen option. Options that are pictures or sounds made outside the product don't wait for
the milestone that lays down the project, so the user can choose while it is built.

Have the builder lay the options out side by side for the user, at the size they will be used and also
enlarged, because a difference in line or texture can be a few pixels at real size. Have it save that as one
image in the working folder too. The user sees it in the chat with the lead, and won't open a file in the
repository.

Hold the options to two things only: the minimum requirements, and being different in kind. They exist so the user
can turn some down. The full quality bar starts with the chosen option, from the next milestone on. A quality bar that
says "each option" must meet the look would fail the milestone on the very options the user rejected.

When taste is one quality of a small build, skip the options. Build it, and put the user's judgement in one item on
the last milestone, marked as needing user feedback, so nothing waits on the user until the rest is finished. When the
whole product turns on something only the user can judge, such as how a game feels, plan an early milestone with a
rough playable version for them to try instead, because a bad answer at the end would reopen finished modules.

### Where references are kept

The chosen option and any reference sets live in the repository, in the folder the settings' `References:` line
names, because reviewers compare with them for as long as the project runs. The checklist names the qualities to
match, so the work is held to those and not to a reference's accidents, such as its lighting or its crop. Several
references that share a quality make it easier to tell the quality from the accidents.

### The builder gets a fresh opinion before a review

A builder working on an item judged by taste gets an opinion from an agent that has seen none of the work, when the
host can start one: a subagent given only the item with its checklist, the quality bar, the references and new
screenshots. The builder fixes what it finds, and asks again while the opinion keeps finding things that matter. Two
or three attempts is usual. Every attempt costs a fresh look at all the screenshots, so stop at the first one that
finds nothing you would change.

Commit each attempt, and keep the best one, which isn't always the last, because quality can peak in the middle.
Options the user hasn't chosen from yet get one attempt at most, because most of them will be turned down.

This is the builder's own check, not the review. A failed review costs a whole builder run and counts towards sending
the milestone back to a planner, which is the wrong price for an ordinary attempt at polish.

### What agents can't perceive goes to the user

No current agent can hear a sound or feel how a game plays. Mark those items as needing user feedback when you
plan them. Left to a reviewer they come back `could_not_judge`, which fails the milestone and tells nobody
anything.
