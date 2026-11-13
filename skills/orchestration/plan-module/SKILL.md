---
name: plan-module
description: Plans work for AI agents to build, whether software, a game or a set of assets, as part of the orchestrate set. Splits a project into modules, writes each module's design, milestones and done-when file, and writes the ORCHESTRATE.md project settings. Use when starting or re-planning a project or a module, when an interface between modules has to change, or after a milestone has failed review repeatedly. Not for building (build-milestone) or judging (review-milestone).
---

# Plan

Your job is to write a plan that other agents can build from without asking you anything. The plan is good enough
when a builder, the agent that writes the code, can build each piece from it alone, and a reviewer, a new agent
that judges the work, can tell from it whether the piece is finished. Neither of them can ask you what you meant,
so everything they need has to be in the files you write. You are the planner.

## Where to start

The project settings are in `ORCHESTRATE.md` at the root of the repository. They say where things are kept, how
the project is tested, and what this project cares about. If there is no such file, write it from
[the template](references/profile.md), filling in what you can work out from the repository. In a chat with the
human, the person the project is for, ask once for the rest. When the script's `plan` command started you, there
is nobody to ask, so take the safest reading and list what you assumed.

The script is `agent_loop.py`, in the build skill's `scripts/` folder. It is a set of commands that start agents,
run the tests and keep the records. The lead, the agent the human chats with, runs those commands.

Two files in the plans folder say what the human wants. Read them if they exist.

`BRIEF.md` is the project brief, which the human approved before planning. Leave it as it is, because it is the
human's page, and the lead changes it when the human says something new. Its numbered decisions come in three kinds,
and you treat each differently:

- A decision in the human's words, or one the human agreed to, is fixed. Carry it into the design in the same
  words, and point at it by its number.
- A decision marked as the agent's is yours to change, with an `Assumption:` line in the plan that says so.
- Under "Still open", a question not yet decided is yours to settle with an `Assumption:` line. One marked "the
  planner chooses" is yours to settle without one.

Take the `Builders:`, `Merge:` and `Human decides` lines of the project settings from the brief's section "How the
human wants to work". A brief written by an older version of this set says "the owner" for the human, and calls that
section "How the owner wants to work". If the human named a model or an effort for one kind of agent there, write the
line for it, as [the settings reference](references/profile.md#a-model-or-an-effort-for-one-kind-of-agent) describes.

`GLOSSARY.md` holds the agreed name for each thing in the project. Use those names in the design, the items and
the interfaces. When you need a name for something new, add an entry with the line
`Proposed: by planner, <date>. Not yet agreed by the human.`, and mention it in your report.

## What you write

A module is a part of the project that one builder can work on without touching the other parts. A milestone is a
piece of a module small enough for one builder to finish in one session. An item is one thing that must be true
before a milestone is Done.

Every module has a folder of its own, `docs/plans/<MODULE>/` unless the project settings name another plans
folder. You write four files in it:

- `DESIGN.md` is the design. It says what the people who use the module need to see, feel or get, and across what
  range. It names the mechanisms that produce that, what the module provides to other modules, and what it may
  cost, if cost matters.
- `PLAN.md` is the plan file: what is left to build, milestone by milestone, and the assumptions still open for
  the human. Under a milestone it holds at most a short note for the builder. It has no status lines and no
  history.
- `LOG.md` is the module's history, one dated line per event, newest at the bottom.
- `DONE.json` is the done-when file. For each milestone it lists the items and how each is proved. A script reads
  it, so [the format](references/done-when.md#donejson) is strict. [Ways to prove an item](references/proofs.md)
  explains the three proofs, Automated Check, Reviewer Inspection and Reviewer Question, and how to mix them.

None of these files says where the work stands, and neither do the module list or the project settings. The
script writes that to `STATUS.md`. A line such as "M0 is Blocked" is wrong the next time M0 moves, and in a design
nobody can correct it without sending the design back for review, because an approved design is approved word for
word.

[The module's files](references/done-when.md) shows each file's shape and the whole layout of the plans folder.
Every project uses the same layout so the human and every agent always know where to look.

Name each milestone for what someone can see or do once it is Done, in plain words, such as "A new user signs up
and lands on an empty dashboard". The script puts those names on `STATUS.md`, the page the human reads, so a name
like "M2 auth handler refactor" tells the human nothing.

Keep the plan file short. A Done milestone shrinks to its heading and a link to its review. Briefs written for
reviews go to `docs/evidence/<MODULE>/`, and design goes in `DESIGN.md`. The script refuses a plan over about
1,500 words, or one with status lines, `###` headings or a log in it, because a plan file that collects those
grows until no builder reads all of it.

Under a milestone, write only what its builder couldn't work out from the items and the design: what already exists
and where it is, what another module owns that the milestone uses or could be tempted to change, or an order where the
order is part of the task. Write it in sentences, and leave the section empty when there is nothing to add. Leave out
a list of steps. The builder sees the code close up and plans the work better than a list written before the code
existed, and a builder handed steps to tick tends to tick them and stop there. If the milestone can't be Done without
some piece of work and no item asks for it, an item is what is missing, so add the item.

A limit on what a builder may do goes where it holds, with its reason. Put it in the project settings, or the
building guidance they link to, when it is true of every module, and in the design when it is about this module.
Only a limit on one milestone goes in that milestone's note.

If a module already has a plan in another shape or another place, such as a checklist in prose or a file called
`BUILD-PLAN.md` elsewhere in the repository, convert it into these files and delete the old one. Keep its history
in `LOG.md`, turn each milestone's "done when" list into items, and give every item a proof. A project still in the
older flat layout, with files such as `<MODULE>-PLAN.md`, moves with the script's `migrate` command, which the
lead runs.

These files are prompts: a builder and a reviewer act on them with nothing else to go on. Write them the way the
`prompting-agents` skill describes, if it is installed.

## The whole project

If the project has more than one module, plan the project before any module. Write the module list,
`ARCHITECTURE.md`, in the plans folder. It opens with a table of every module in the order to build them, which
the script reads:

```markdown
| # | Module | What it's for | Needs |
|---|---|---|---|
| 1 | AUTH | People sign in, and stay signed in across devices | |
```

`What it's for` is one plain sentence for the human. Leave status out of the table, because the script adds it on
`STATUS.md`, where a module you have listed but not yet planned shows as Not planned yet. After the table, say what
each module owns and list each interface, which is what one module provides to the others.

Draw the lines between modules around state, so that each kind of state has exactly one module in charge of it.
Most bugs between modules come from two of them editing the same thing. Put first the riskiest modules and the
ones most others depend on, because they are the most likely to force everything else to change.

A module doesn't change an interface by itself. A builder who needs a change writes a proposal in its module's log,
and you settle it here, with every module that provides or uses that interface.

## Milestones that depend on another module

When you plan a module, list everything it uses from other modules. The module list says which module owns each thing.
Find the milestone in that module that delivers it, and add that milestone to the `depends_on` field of the first
milestone here that can't work without the real thing, written `"CORE:M3"`. The script won't start a milestone until
every milestone in its `depends_on` is Done, and until then the milestone is Waiting, with the reason On Dependency. A
missing entry lets a builder start too early, and an unnecessary one holds work back.

If no milestone there delivers the thing yet, add one to that module, or move one earlier, as a change to that
module's plan. Write the interface first, so this module can build against a stand-in until the milestone that needs
the real thing.

When a builder ends with `BLOCKED needs_dependency` because something another module owns is missing, decide from the
module list who owns it. If another module does, add the milestone there and the `depends_on` entry here. If it is
really this module's work, add it to this module's plan. If the module list was wrong, fix the list and the interface
first. Plan the missing part in the module that owns it, and not inside the blocked builder's module, because then two
modules would own the same thing.

## What makes a plan work

### The design

Research before you design. Most problems have been solved before, in shipped products or published work, so find
out how before you invent something, and prefer current practice. Old code in the repository shows what someone
tried, not what to copy.

Settle the mechanisms, and leave the details to the builder. A mechanism is the core idea that produces the
behaviour, such as "the wake is a simulated height field, not a scrolling texture". Left open, a builder may pick
one that can't work. A detail is anything that can change without changing the behaviour, such as the data layout
or which file a function lives in. A wrong detail in a plan gets copied faithfully through the whole build, so
leave details out.

Check that each mechanism can produce the behaviour across the whole range before anyone builds on it, because a
lot of effort goes into tuning mechanisms that could never have worked. Where the product promises exactness, as
with money, say what keeps it exact and up to what size of input. A reviewer will try the edge of any range the
design leaves open.

### The human's words

Plan what the human's words say, not a narrower thing that is easier to pin down. Where their words could be read
more widely than your plan covers, take the wider ordinary reading when it costs little. If the human asks for
"accents" to be handled, plan for every letter with a mark on it, and not only for the ones that are simple to
detect.

When the wider reading costs a lot, write the reading you chose in the plan's `## Open for the human` section, as
one line that starts `Assumption:`, so the human can overturn it in a line. A question you would have asked the
human goes there too, with the answer you assumed. The script counts those lines and lists them in the human's
report. When the human answers, delete the line and note the answer in the log.

A narrow reading that nobody wrote down can't be caught later, because reviewers judge the work against the plan.
Read "accents" as only the letters that decompose in Unicode, and a tool that turns Ørsted into "rsted" passes
every review.

### Milestones and items

Make each milestone one outcome that a reviewer can judge, and put the riskiest first. Usually the outcome is
something a user could notice on a real target, meaning a device or platform the product runs on, as the project
settings list them. For internal work, such as a solver or a data pipeline, it can be a property you can measure,
as long as the items say how it is observed.

Size a milestone to what one builder session can finish unaided, which for current models is hours of work. Each
milestone costs a builder run, a run of the checks and usually a review, so a finer split pays those costs again
without making the work better. A milestone may have as many items as it needs, but keep each item short and choose
its proof on purpose. [What makes a good item](references/done-when.md#what-makes-a-good-item) says how, and why a
long item ends in a re-plan.

Work judged by taste, such as a game's look, a set of 3D assets or a visual design, starts with options the human
chooses from, because no reviewer can settle taste for them. Read
[subjective work](references/proofs.md#subjective-work) before you write its milestones.

Some items can't be finished by a builder alone. Mark each with a `needs` field, whose `type` says what is
needed, and whose `what` says it in plain words:

- `human_feedback`, when someone has to look at the result and judge it, because no agent can tell. The builder
  does everything else first, and the milestone stops until the human replies.
- `access`, when the human has to approve a permission or a prompt, such as screen recording. The builder can
  finish it only in a visible session while the human is at the machine, so the milestone runs when the human says
  they are there.
- `hardware`, when a device has to be connected, such as a phone. The builder can finish it only while the device
  is there.

A milestone with such an item still open holds back every later milestone of the module, so put the human's
judgements in the last milestone, unless later work depends on the answer. [The done-when
reference](references/done-when.md#donejson) has the field's form.

### Targets and checks

Check that whoever has to reach a target can reach it, reviewers included. A browser won't start inside Codex's
default `workspace-write` sandbox, and other programs with a window can fail there too. A Codex agent runs one only by
asking to run that command outside the sandbox, and each request is granted or refused on its own. A request is
usually granted, so plan for the reviewer to ask, and for the review to move to Claude if it is refused. The builder's
screenshots can't stand in for the reviewer's own, because they show only what the builder chose to capture. A build
that drives a browser throughout shouldn't depend on every one of those requests being granted. Say so in the design,
and either list `Codex sandbox: danger-full-access` as a decision for the human, who is the one giving up the sandbox,
or name a Claude builder for that module.

Write each check so that it still runs when the machine is in a state the product has to cope with, such as a locked
screen or a denied permission. Have the check record that state and pass either way, unless the item's statement
really depends on it. A check that needs an unlocked, idle machine stops whenever the human uses it.

Use only cost targets that are real, from the project brief or from the human. If nobody has set one, record the
measurement as a baseline, and write a check that fails only when the result falls well below it.
[Proofs](references/proofs.md) calls that a benchmark tripwire. A number you make up becomes a requirement that
reviewers fail the build on.

The same goes for every number an item tests against, such as a precision bound. A bound nobody measured is a
guess. Measure it while you plan, or make measuring it the milestone's first item, with the bound set from the
result. A wrong bound is found only when a builder can't meet it, and by then it has cost a builder session and
a new plan.

When you plan a module's next piece, or re-plan one, look through its reviews. A finding that came up twice becomes a
command in the project's test command (the `Test command:` line of the project settings) or an item's `check`, so from
then on it is caught without a review.

## What finished looks like

1. The design, the plan file and the done-when file exist, and agree with each other, with the interfaces and with
   the module's entry in the module list.
2. A reviewer has read the design, and the result is Design Approved. The review gives a new reviewer only the
   human's request and the design. The done-when items are part of what it approves, because they are what the
   builder will be held to, and no builder starts on the module before then. When the `plan` command started you,
   the lead runs the review after your turn, so say in your report that the design still needs one. When you are
   planning in a chat with the human, run it yourself with
   `agent_loop.py review --module <M> --milestone design --worktree .`, act on what it finds, and note the review
   in the log.
3. Every `check` runs as written. `agent_loop.py check --module <M> --milestone <id> --worktree . --items-only` tries
   a milestone's item checks and saves nothing. It leaves out the project's test command and waits for each item's
   lock, so it doesn't disturb builders that are working. Before the work exists, each check should come back `fail`.
   An `error` means the check itself is broken, usually by shell quoting inside the JSON, and a builder would lose a
   session finding that out.
4. The module table in `ARCHITECTURE.md` lists the module, and every milestone is named for what someone can see
   or do.
5. Your report ends with what is left for the human: each decision on the `Human decides` list in the project
   settings, and each assumption. Put them last, because the lead is shown the end of a long report.

The `Human decides` list says what has to go to the human. Every other decision about the plan is yours.

## When a milestone keeps failing review

A milestone that keeps failing review is Waiting, with the reason For Diagnosis (the script prints `waiting` with
`reason: for_diagnosis`). No builder works on it until a planner has found out why. It gets there in one of two
ways, and your task says which. Either four failed reviews each repeated a finding that an earlier review had
raised, which means the fixes aren't holding. Or six reviews failed, mostly on findings no earlier review had
raised, which means each fix held and the milestone still came no closer to passing. Each review is kept beside
the latest one, as `<id>-review-1.md` and so on. Read every review and the code, and decide why the milestone
keeps failing.

The cause may be in the plan. The milestone may be too big for one session, and should be split. It may depend
on something outside this module, so that what it covers has to change. It may use a mechanism that can't produce
the behaviour, and need a new design. Its items may be too broad, or impossible to meet as written. The cause may
also be outside the plan. A builder can fix the one place each review names while the same defect stays in places
no reviewer has tried yet, and a reviewer's findings can go beyond what the items ask. Changing the plan cures
neither of those, and it costs a design review and a rebuild.

When the plan is at fault, change the items, write the reason in `LOG.md`, and end with `PLANNED` as usual. This
is a re-plan. Write each changed item again from what it claims, as if it were new, and move the history to
`LOG.md`. Patching an item by adding a clause each time turns it into a procedure, full of steps and prohibitions
left over from old fixes, and each builder has to work out which still apply.

When the plan is sound, change no file, and make your last line
`KEEP <MODULE> <milestone>: builder|reviewer|human: <why>`, naming who has to act. `builder` is for a builder who
keeps breaking something, and it starts a new builder session with your reasons. `reviewer` is for findings that
go beyond the items, and the next reviewer is told to judge the items as written. `human` is for a decision only
the human can make, and it sets the milestone to Blocked: Too Many Failed Reviews, with your reasons.

A milestone gets one diagnosis, whichever way it ends. When your turn is merged, the script sets the milestone's
`failed_reviews` and `failed_reviews_with_repeat` to 0 and adds 1 to `diagnoses`, whatever you wrote in those
fields. After a re-plan it also sets the `status` to `not_started`, saves the new items as the approved ones and
clears the old proof, because that proved something else. If the milestone then reaches four repeated failures
or six failed reviews again, it is Blocked, with the reason Too Many Failed Reviews (`too_many_failed_reviews`),
and waits for the human.

Give each milestone you split off the same `diagnoses` count as the one it came from. The script can't tell which
new milestone came from which, so you set it. Leave the other counts and `findings` alone, because the script
puts back any change a plan makes to them.

## What the script does with your files

Leave the files you write uncommitted. When your turn ends with `PLANNED`, the `plan` command checks them, commits
and merges them, and saves the new items as the approved ones, so a commit, merge, pull or push of your own gets
in its way and it merges nothing. Leave each `RECORD.json` record file and `STATUS.md` as they are too. Only the
script writes those, and it rejects a plan that touches one.

## When the human changes what they want

The lead sends you the human's words as your task, and has already added them to the brief if there is one. Change the
plan to match, and quote their words in `LOG.md`. Write each item their words reach again from what it claims, as you
would in a re-plan. This doesn't count as the milestone's diagnosis, unless the milestone was already Waiting: For
Diagnosis. Then your change is the re-plan, and the script counts it. A milestone whose items you change is built and
reviewed again, so change only what their words reach.
