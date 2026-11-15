# Ways to prove an item

An item is one thing that must be true before a milestone is Done. This file is about how to prove one: which
kind of proof to choose when planning, how a builder or a reviewer inspects work, and how work judged by taste is
handled.

Contents:
- [The three ways](#the-three-ways)
- [Kinds to start from](#kinds-to-start-from)
- [What a proof costs](#what-a-proof-costs)
- [How to inspect](#how-to-inspect)
- [Subjective work](#subjective-work)

## The three ways

Every item in a done-when file says how it will be proved. There are three ways, and an item may use more than
one:

- An Automated Check is a shell command in the item's `check` field. It passes if it exits with 0. The builder
  runs it, and the script runs it again before it accepts the builder's word.
- A Reviewer Inspection, in the `inspect` field, says what to look at. A reviewer runs the product, takes
  screenshots or recordings, and judges what it sees against the item and the milestone's quality bar.
- A Reviewer Question, in the `ask` field, is a question a reviewer answers by reading code, an interface or a
  design.

An item passes only when every proof it names passes.
The done-when file's format, in `done-when.md`, says which milestones need a reviewer.

Choose the proof that would catch a convincing fake. Often one proof isn't enough, because each kind misses
different things. Take a boat bobbing in waves. A test that the energy never grows catches a slow drift that
nobody would notice by eye. A sequence of frames of the boat in a storm catches motion that is perfectly stable
and still looks wrong. So that item gets both.

A quality bar needs a real example to point at, whether or not the work is visual. "Help text as clear as
ripgrep's" gives a reviewer something to judge against. "Clear help text" doesn't.

## Kinds to start from

These are starting points, not a fixed list. A project can describe its own kinds in its project settings, in the
same shape.

| Kind | Uses | What to write | It is too weak if |
|---|---|---|---|
| Automated test | `check` | The behaviour, and a command that tests it end to end | It tests a mock, or only the easy path |
| Property or fuzz test | `check` | The rule that must always hold, the inputs to throw at it, and for how long | The inputs miss the cases that happen in real use |
| Golden output | `check` | The expected output, how close is close enough, and why it is right | The golden file was made by the code under test, and nobody checked it |
| Benchmark tripwire | `check` | What to measure, and a threshold from the project brief or a recorded baseline. When the human gave the number, such as a frame rate, use two proofs: a generous `check` that catches a collapse, and the precise measurement on the real target | Someone made the number up. It ran on a busy or different machine. The human's number is left to a reviewer reading one timing sample |
| Determinism | `check` | The same input, run twice, gives the same output (frames, files, results) | It compares a run only with itself in one process, or ignores timing and threads |
| Visual quality | `inspect` | One quality, and the views that show it | It is one flattering shot, or screenshots from a different build |
| 2D image | `inspect` | The parts of the image, each seen whole, cropped at full resolution, and at the size it is shown | It was judged only as a thumbnail, or in one condition |
| 3D asset | `inspect` | The parts of the model, each seen from several angles and distances, in its real lighting | It is one hero angle, or the turntable never shows the underside |
| Motion or behaviour | `inspect` | What moves (physics, animation, simulation), and a scenario that shows it, as a sequence of frames | It is one still, or a slowed-down or close-up recording |
| User journey | `inspect` | The steps and their states: empty, loading, error and resize for a screen; bad arguments, piped input and exit codes for a command-line tool | Only the easy path was tried |
| Options to choose from | `inspect`, and `needs` with the type `human_feedback` | A few options for one representative piece, different in kind, for the human to pick from | The options are one idea in three colours |
| Code or interface | `ask` | A question with a real answer, such as "does every caller handle the new error case?" | It asks for an opinion |

## What a proof costs

A proof is worth what it catches, set against what it costs, and both depend on how the build runs, not only on
the item. Most proofs are cheap, so this rarely decides anything. It decides a lot when a proof is slow, when it
needs something only one run at a time may use, or when it needs the human.

An Automated Check runs more often than it looks from the item. The builder runs it while working. After the builder
merges, the script runs every check again on the main branch's tip, one after another, before it sets the milestone
Ready for Review, and that run is the proof of record. A check that needs a resource only one run may use at a time
runs one after another across every builder, so with ten builders a fifteen-minute check can wait two hours for its
turn.

Two settings make that cheaper. An item's `reads` field names the files its check reads, and the script reuses the
check's last pass while those files and the command stay the same, so a check of one module isn't run again because
another module merged. And a resource that several runs can share, such as a GPU for renders and tests, goes on the
`Shared resources` line with how many runs it takes at once. Its item takes `"lock": "gpu"`, and only a measurement
that needs the machine quiet takes `"lock": "gpu.alone"`.

The project's test command costs more again, because every merge waits for it. Branches that arrive together are
merged as one batch with one run of the test command, but a batch still waits for the one before it, so the
command's length sets how many batches an hour the project can merge. A test command that takes fifteen minutes
allows about four, shared by every builder, and a failure costs a second run to find the branch that caused it.

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
  merged it, and a failure is fixed by the module that caused it while the others carry on. Say in the project
  settings how often that run happens and who acts on a failure, and give items that depend on it a check that reads
  its latest result rather than repeating it.
- A measurement that needs a quiet machine, such as a timing, rarely gets one while builders are working. Within
  a milestone, use a generous benchmark tripwire that catches a collapse. Put the precise numbers in the module's
  last milestone, measured in one sitting.
- A proof that needs the human, such as a run on a real device, costs a sitting each time. Gather those items into
  the module's last milestone too, so one sitting covers them.

Two more patterns make a proof's cost grow with the number of builders:

- A proof that has to be recorded before a merge and matched to the exact code goes stale whenever the main branch
  changes the files it covers. When making it takes longer than the main branch stays still, builders can spend
  their sessions remaking it. Prefer a run after the merge. Where it must come first, draw what it covers as
  narrowly as its real inputs.
- A resource held alone by work that doesn't need it alone makes everything queue. Timing needs a quiet machine,
  but comparing images or running a GPU test usually doesn't. List the resource under `Shared resources`, give
  ordinary items `"lock": "gpu"`, and keep `"lock": "gpu.alone"` for the few timing and realtime items, so the
  rest run side by side.

## How to inspect

This applies to a builder checking its own work before it ends with `DONE`, and to a reviewer. Before you look at
anything, write down what you are going to look at.

A reader without a list looks at whatever catches its eye, decides it looks fine, and misses the broken parts. So
break the thing into pieces first. For a command-line tool, the pieces might be its subcommands, its flags, its output
and its failure messages. A picture or a 3D model breaks into pieces the same way: a boat into the bow, the stern,
where the mast sits, and the guns.

Then decide how you need to see each piece. A 3D model needs a few angles. An image needs close crops as well as
the whole frame, so use a crop or zoom tool, and don't judge a scaled-down copy. Most things need a few
conditions, such as different times of day, or the edge conditions the project settings list for the target.
Anything that moves needs the moments where it changes.

You need more than one view because every view hides something. A bow wave can look perfect from the side while
it cuts straight through the hull from the front. A cloud can look fine as a thumbnail and turn into stripy
bands when you zoom in.

Then go through the list and judge each entry. Keep the list in the review or with the evidence, so anyone can
see what was looked at and what wasn't.

What you can perceive depends on your tools. Most agents today can't watch live video or hear sound, so record
anything that moves as a sequence of frames. Prove anything you can't perceive with a measurement, or give it
`could_not_judge`, which means Could Not Judge. Golden screenshots are good at catching a regression, but they never
prove that something looks right.

## Subjective work

Subjective work is work judged by taste: a game's look, a set of 3D assets, a visual design. A test can hold the
minimum requirements (the file loads, the model is under its triangle budget, the frame time holds), so write
those as `check` items as usual. The taste itself needs four more things.

### The human chooses the look first

People disagree about taste, so no reviewer can settle it for the human. When the look is the product, and a
wrong one means redoing most of the work (an asset set, a game's art style, a brand), plan a first milestone
that makes a few options for one representative piece, different in kind. Give it an item where the human
picks one, marked as needing human feedback: `"needs": {"type": "human_feedback", "what": "pick one option"}`.
Choosing early costs the human one sitting. Rejecting finished work costs the build. The human replies to the
lead in chat, and the lead saves the question and their reply with the `human feedback` command. The script
records it as Human Feedback, so the builder and every later reviewer can compare the work with the option the
human chose.

Have the builder lay the options out side by side for the human, at the size they will be used and also
enlarged, because a difference in line or texture can be a few pixels at real size. Have it save that as one
image in the evidence folder too. The human sees it in the chat with the lead, and won't open a file in the
repository.

Hold the options to two things only: the minimum requirements, and being different in kind. They exist so the human
can turn some down. The full quality bar starts with the chosen option, from the next milestone on. A quality bar that
says "each option" must meet the look would fail the milestone on the very options the human rejected.

When taste is one quality of a small build, such as how a little game feels, skip the options. Build it, and put
the human's judgement in one item on the last milestone, marked as needing human feedback, so nothing waits on the human until the rest
is finished.

### Reviewers compare with references

A reference is something concrete that the quality bar points at: the chosen option, a small set of reference
images, or the best version so far. The `Anchors:` line in the project settings says where they are kept. Compare
the qualities the item names, side by side with the reference. Don't try to match one image, because an agent
told to match a target copies its accidents too, such as its lighting or its crop. A set of references shows the
quality without fixing the accidents.

### The builder gets a fresh opinion before a review

A builder working on an item judged by taste gets an opinion from an agent that has seen none of the work, when the
host can start one: a subagent given only the item, the quality bar, the references and new screenshots. The builder
fixes what it finds, and asks again while the opinion keeps finding things that matter. Two or three attempts is
usual. Every attempt costs a fresh look at all the screenshots, so stop at the first one that finds nothing you would
change.

Commit each attempt, and keep the best one, which isn't always the last, because quality can peak in the middle. Options the human hasn't chosen from yet get one attempt at most, because most of them will be turned down.

This is the builder's own check, not the review. A failed review costs a whole builder run and counts towards sending
the milestone back to a planner, which is the wrong price for an ordinary attempt at polish.

### What agents can't perceive goes to the human

No current agent can hear a sound or feel how a game plays. Mark those items as needing human feedback when you
plan them. Left to a reviewer they come back `could_not_judge`, which fails the milestone and tells nobody
anything.
