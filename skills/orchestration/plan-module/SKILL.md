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
owner, the person the project is for, ask once for the rest. When the script's `plan` command started you, there
is nobody to ask, so take the safest reading and list what you assumed. The script is `agent_loop.py`, in the build
skill's `scripts/` folder. It is a set of commands that start agents, run the tests and keep the records. The lead,
the agent the owner chats with, runs those commands.

Two files in the plans folder say what the owner wants. Read them if they exist.

`BRIEF.md` is the project brief, which the owner approved before planning. Don't edit it. It is the owner's page,
and the lead changes it when the owner says something new. Its numbered decisions come in three kinds, and you
treat each differently:

- A decision in the owner's words, or one the owner agreed to, is fixed. Carry it into the design in the same
  words, and point at it by its number.
- A decision marked as the agent's is yours to change, with an `Assumption:` line in the plan's log that says so.
- Under "Still open", a question not yet decided is yours to settle with an `Assumption:` line. One marked "the
  planner chooses" is yours to settle without one.

Take the `Builders:`, `Integrate:` and `Owner decides` lines of the project settings from the brief's section "How
the owner wants to work". If the owner named a model or an effort for one kind of agent there, write the line for
it, as [the settings reference](references/profile.md#a-model-or-an-effort-for-one-kind-of-agent) describes.

`GLOSSARY.md` holds the agreed name for each thing in the project. Use those names in the design, the items and
the interfaces. When you need a name for something new, add an entry with the line
`Proposed: by planner, <date>. Not yet agreed by the owner.`, and mention it in your report.

## What you write

A module is a part of the project that one builder can work on without touching the other parts. A milestone is a
piece of a module small enough for one builder to finish in one session. An item is one thing that must be true
before a milestone is Done.

For each module you write three files, in the plans folder the project settings name:

- `<MODULE>.md` is the design. It says what the people who use the module need to see, feel or get, and across
  what range. It names the mechanisms that produce that, what the module provides to other modules, and what it
  may cost, if cost matters.
- `<MODULE>-PLAN.md` is the plan file: the milestones, a few status lines and a log.
- `<MODULE>-DONE.json` is the done-when file. For each milestone it lists the items and how each is proved. A
  script reads it, so [the format](references/done-when.md) is strict. [Ways to prove an item](references/proofs.md)
  explains the three proofs, Automated Check, Reviewer Inspection and Reviewer Question, and how to mix them.

Don't name a module `BRIEF`, `GLOSSARY` or `ARCHITECTURE`, because its design would overwrite the file of that name.

If a module already has a plan in another shape, such as a checklist in prose, convert it. Keep its log, turn each
milestone's "done when" list into items, and give every item a proof.

These three files are prompts: a builder and a reviewer act on them with nothing else to go on. Write them the
way the `prompting-agents` skill describes, if it is installed.

## The whole project

If the project has more than one module, plan the project before any module. Write the module list,
`ARCHITECTURE.md`, in the plans folder or wherever the project settings say. It names each module and what it owns,
gives the order to build them in, says what each is for, and lists each interface, which is what one module
provides to the others.

Draw the lines between modules around state, so that each kind of state has exactly one module in charge of it.
Most bugs between modules come from two of them editing the same thing. Put first the riskiest modules and the
ones most others depend on, because they are the most likely to force everything else to change.

A module doesn't change an interface by itself. A builder who needs a change writes a proposal in its plan's log,
and you settle it here, with every module that provides or uses that interface.

## Milestones that depend on another module

When you plan a module, list everything it uses from other modules. The module list says which module owns each
thing. Find the milestone in that module that delivers it, and add that milestone to the `needs` field of the
first milestone here that can't work without the real thing, written `"CORE:M3"`. The script won't start a
milestone until every milestone in its `needs` is Done, and until then the milestone is Waiting on Dependency. A
missing entry lets a builder start too early, and an unnecessary one holds work back.

If no milestone there delivers the thing yet, add one to that module, or move one earlier, as a rewrite of that
module's plan. Write the interface first, so this module can build against a stand-in until the milestone that
needs the real thing.

When a builder ends with `BLOCKED` because something another module owns is missing, decide from the module list
who owns it. If another module does, add the milestone there and the `needs` entry here. If it is really this
module's work, add it to this module's plan. If the module list was wrong, fix the list and the interface first.
Don't let the blocked builder build another module's part inside its own module, because then two modules would
own the same thing.

## What makes a plan work

Each rule below is here because a plan without it went wrong.

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

### The owner's words

Plan what the owner's words say, not a narrower thing that is easier to pin down. Where their words could be read
more widely than your plan covers, take the wider ordinary reading when it costs little: which letters count as
"accents", how a "cli called x" is run, what a size limit is measured in. Otherwise write the reading you chose in
the plan's log, as one line that starts `Assumption:`, so the owner can overturn it in a line. A question you
would have asked the owner goes there too, with the answer you assumed. The script counts those lines and lists
them in the owner's report. In one test run a planner read "transliterate accents" as letters that decompose in
Unicode, and said no decision was needed. Three reviewers then passed a tool that turned Ørsted into "rsted",
because it matched the plan.

Add a requirement only when the owner's words or the design need it, because reviewers fail the build on every
requirement you add. In another test run a planner decided that a small accounting tool's output must fit 80
columns. Three of the four findings that failed its reviews were about that limit, which the owner never asked
for.

Quote the owner's request word for word at the top of the design, and name the project brief there if there is
one. Reviewers judge the design against the request, and that quote is all they have of the owner. One reviewer
found the request cut short in a commit message, and judged against the planner's summary of it instead.

### Milestones and items

Make each milestone one outcome that a reviewer can judge, and put the riskiest first. Usually the outcome is
something a user could notice on a real target, meaning a device or platform the product runs on, as the project
settings list them. For internal work, such as a solver or a data pipeline, it can be a property you can measure,
as long as the items say how it is observed.

Size a milestone to what one builder session can finish unaided, which for current models is hours of work. Each
milestone costs a builder run, a run of the checks and usually a review, and Anthropic dropped fine-grained
splitting once its models could hold a longer build. A milestone may have as many items as it needs, but keep
each item short and choose its proof on purpose.
[What makes a good item](references/done-when.md#what-makes-a-good-item) says how, and why long items get rewritten.

Work judged by taste, such as a game's look, a set of 3D assets or a visual design, starts with options the owner
chooses from, because no reviewer can settle taste for them. Read
[subjective work](references/proofs.md#subjective-work) before you write its milestones.

Mark an item `attended` when it needs a person's feedback or physical hardware, such as a phone plugged in or a
permission prompt approved. Builders then do everything else first, and the owner gets those items together. A
milestone with such an item still open holds back every later milestone of the module, so put the owner's
judgements in the last milestone, unless later work depends on the answer.

### Targets and checks

Check that whoever has to reach a target can reach it, reviewers included. A browser won't start inside Codex's
default `workspace-write` sandbox, and other programs with a window can fail there too. A Codex agent runs one only
by asking to run that command outside the sandbox, and each request is granted or refused on its own. In test runs
a reviewer on Codex asked and was granted it each time. So plan for the review to move to Claude if it is refused,
and don't plan for a reviewer to judge the builder's screenshots in place of its own. A build that drives a
browser throughout shouldn't rest on asking. Say so in the design, and either list
`Codex sandbox: danger-full-access` as a decision for the owner, who is the one giving up the sandbox, or name a
Claude builder for that module.

A condition the work must survive, such as a locked screen or a denied permission, is not a condition for checking
it. Have the check record that state and pass either way, unless the claim really depends on it. Otherwise checking
stops whenever the owner uses the machine.

Use only cost targets that are real, from the project brief or from the owner. If nobody has set one, record
measurements and set tripwires, and don't make a number up.

When you plan a module's next piece, or rewrite one, look through its reviews. A finding that came up twice becomes
a command in the project's test command (the `Check:` line of the project settings) or an item's `check`, so it is
caught for nothing from then on.

## What finished looks like

1. The design, the plan file and the done-when file exist, and agree with each other, with the interfaces and with
   the module's entry in the module list.
2. A reviewer has read the design. Run `agent_loop.py review --module <M> --milestone design --worktree .`, which
   gives a new reviewer only the owner's request and the design, and saves the result. No builder starts on the
   module until that result is Design Approved. Act on what the review finds, and put the review on the plan
   file's `Reviews:` line. If the `plan` command started you and you can't start a review, say the design still
   needs one, and the lead runs it.
3. Every `check` runs as written. `agent_loop.py check --module <M> --milestone <id> --worktree .` tries a
   milestone's checks and saves nothing. Before the work exists, each should come back `fail`. An `error` means
   the check itself is broken, usually by shell quoting inside the JSON, and a builder would lose a session finding
   that out.
4. The plan file's `Milestone:`, `Now:`, `Next:` and `Blocked:` lines are up to date.
5. Your report ends with what is left for the owner: each decision on the `Owner decides` list in the project
   settings, and each assumption. Put them last, because the lead is shown the end of a long report.

The `Owner decides` list says what has to go to the owner. Every other decision about the plan is yours.

## When a milestone keeps failing on the same finding

A milestone with four failed reviews that each repeated a finding an earlier review had raised is Awaiting Replan
(the script prints `replan_owed`), which means something about the plan is wrong. Your task names the reviews.
Each round's review is kept beside the latest, as `<id>-review-1.md` and so on. Decide which of these happened,
and write why in the log:

- The milestone was too big. Split it.
- It depended on something outside this module. Change what it covers.
- It used a mechanism that can't work. Redesign it.

Then change the items. When your plan is merged, the script sets that milestone's `fails` and `rounds` to 0, adds
1 to `replans`, and sets its `state` to `open`, which is Not Started, once, whatever you wrote in those fields. It
saves the new items as the approved ones and clears the old proof, because that proved something else.

Give each milestone you split off the same `replans` and `diagnoses` counts as the one it came from. The script
can't tell which new milestone came from which, so you set them. With the counts carried over, a second run of
four repeated failures ends at Too Many Failed Reviews (`parked`), where the milestone waits for the owner, rather
than at another rewrite.

## When reviews keep finding something new

A milestone that has failed six reviews, mostly on findings no earlier review had raised, is Awaiting Diagnosis
(also printed `replan_owed`). Each finding was fixed, so the builder isn't stuck, but the milestone is getting no
closer to passing. Your task lists what failed in each round, and the reviews are kept as for a rewrite. Decide
why, and say so in your report:

- The items are too broad, or can't be met as written. Change them, and end with `PLANNED` as usual. The script
  settles it like a rewrite, and also counts the diagnosis.
- The plan is right. Change no file, and make your last line
  `KEEP <MODULE> <milestone>: builder|reviewer|owner: <why>`, naming who has to act. `builder` is for a builder
  who keeps breaking something, and starts a new builder session with your reasons. `reviewer` is for findings
  that go beyond the items, and the next reviewer is told to judge the items as written. `owner` is for a decision
  only the owner can make, and parks the milestone with your diagnosis.

The script starts the milestone's counts again either way, and a second run to six failed reviews parks it. Leave
the counts and `findings` alone: the script puts back any change a plan makes to them.

Don't edit a `<MODULE>-ACCEPTED.json` record file. Only the script writes those, and it rejects a plan that touches
one.

## When the owner changes what they want

The lead sends you the owner's words as your task, and has already added them to the brief if there is one. Change
the plan to match, and quote their words in the plan's log. This doesn't count as a rewrite after failed reviews,
unless the milestone was already Awaiting Replan; then your change is the rewrite, and the script counts it. A
milestone whose items you change is built and reviewed again, so change only what their words reach.

The script's own messages still use some older words. "The loop" is the script. "The profile" is the project
settings. "Integrate" means merge. "Claimed" means Ready for Review. A "blocking" finding is a Must Fix, and an
"advisory" one is a Suggestion.
