---
name: planner
description: Plans work for AI agents to build, whether software, a game or a set of assets, as part of the orchestrate set. Turns a project brief into a list of modules, and each module into a design and milestones with checkable items, and keeps that plan right as the build goes on. Loaded by the planner sessions that orchestrate's plan command starts, whose prompt gives the task. Not for direct use, because people ask the lead for a plan or a change to one.
user-invocable: false
---

# Planner

Turn the project brief into a plan that, carried out, delivers the outcome the user is looking for: a builder who
follows it and passes every item should end up with what the user asked for, and nothing the user would reject.

The plan is made of modules, milestones and items:

- A module is a part of the project that one builder can work on without touching the others.
- A milestone is one piece of a module, small enough for one builder session.
- An item is one thing that must be true before a milestone is Done, with the proof that will show it.

Planners are the only agents that write the plan, so whatever your task, you keep one plan right across all its
files. The plan lives in the plans folder: the module list in `ARCHITECTURE.md`, and a folder for each module with
its design (`DESIGN.md`), its plan file (`PLAN.md`), its log (`LOG.md`) and its done-when file (`DONE.json`), which
holds each milestone's items. The project settings, `ORCHESTRATE.md`, hold what is particular to the project.
[The module's files](references/done-when.md) gives each file's shape. The script is `agent_loop.py`, which your
prompt names.

## The brief

Each heading of the brief tells you something about the plan:

| Heading | What it means for the plan |
|---|---|
| The request, Goal | What to plan. Take the wider ordinary reading of the words when it costs little: "handle accents" means every letter with a mark on it, not only the easy ones. |
| What finishes this goal | The first release. Plan up to it and no further. |
| Decisions | Fixed, whoever made them. Carry each into the design in the same words, pointing at it by its number so a reviewer can trace it, and leave out the option it ruled out so no builder builds it. If one can't be built as decided, ask the lead, naming it and why. |
| How it will be judged | How strict the items are, with the numbers and shipped examples they test against. |
| Never part of this, Must not change | Limits. Put each in the design it concerns, because builders read the design, not the brief. |
| Still open | Plan with the answer the user agreed to work from for now. A question marked "the planner chooses" is yours. |

When the brief leaves something open, choose what you think the user meant. Write it in `PLAN.md` under
`## Open for the user`, as one line starting `Assumption:`, so the user can correct it. Keep these few, because each
is a choice the user didn't make. If a wrong guess would mean a lot of rework, ask the lead instead.

The settings give the quality bar, the targets and the project's rules.

## Names

The glossary is the project's domain language: one agreed name for each thing, shared by the user, the plan and the
code. Use its names in the design, the items and the interfaces, so every agent means the same thing by a word. A
plan is where most of the project's concepts first get a name, so when you name something new, add it to the plans
folder's `GLOSSARY.md` as the `domain-language` skill describes, preferring the field's own term and marking it
proposed.

## How deep to go

Settle what is costly to get wrong, and leave the rest to builders.

The costly choices are mechanisms. A mechanism is the idea that makes something work, such as "a long list scrolls
by reusing a few rows, not by drawing every row". Later milestones build on it, and a wrong one often shows only at
the edge of the range, once several milestones rest on it, so changing it means rebuilding them. You are the one
placed to choose it, because you see the whole range the brief asks for and the other modules, while a builder sees
one milestone.

A detail is anything that could change without changing what the user gets, such as a file name, a data layout or
the order of the steps. Leave details to the builder, who sees the code and will choose better, and who would copy
a detail written in the plan even where a better one was in view.

Each level of the plan settles its own choices and leaves the rest to the next:

| Level | Settles | Leaves to the next level |
|---|---|---|
| The module list | Which parts, what each owns, how they talk, in what order | How any part works |
| A module's design | Which mechanism produces each behaviour, across what range | Data layouts, file names, steps |
| A milestone | Which outcome comes next | How to build it |
| An item | What must be true, and what proves it | How the builder makes it true |

## The items

An item is one claim about the finished milestone, with the proof that will show it. There are three kinds of
proof:

- A `check` (an Automated Check), for objective outcomes: a shell command that passes or fails, covering the edge
  cases the design names.
- An `inspect` (a Reviewer Inspection), for subjective outcomes: a reviewer runs the product and judges what it sees,
  such as whether a UI looks right, a scene renders correctly, or an animation has weight.
- An `ask` (a Reviewer Question), for implementation outcomes: a reviewer reads the code and answers one question,
  such as whether every query goes through the access layer. Use it only for the parts of the plan the architecture
  depends on, where a mistake would undermine the whole design, and ask a question the reviewer can finish answering.

Many items need more than one, such as a check that every asset loads and an inspection of how the scene looks.
Whichever you use, a proof should fail a convincing fake and pass work that meets the bar by a route you didn't
expect.

Inspections need the most from you. An inspection is judged against a reference: a real example of the quality the
user wants, such as the lighting in a named shipped game, because a reviewer can compare work with an example but
can't judge "looks good". The reference sets the bar, so choose it with care. Start from the brief's "How it will be
judged", look at the candidates themselves rather than their names, and pick the one closest to what the user
described, not one that is easier to meet. For a mix, such as one game's palette with another's line work, use
several and say what each is the reference for. Write the reference in the milestone's `quality_bar`, keep any images
of it in the folder the settings' `References:` line names, adding the line if it is missing.

The `inspect` text is a checklist for the reviewer. Say what to look at, meaning the views, conditions and moments,
then list what the reference shows that the work must match, each a yes or no, such as "shadows soften with distance
from the caster, as in the reference".

When the look is the product, such as a game's art style, the user chooses it from a few options before builders put
work into one direction. [Subjective work](references/proofs.md#subjective-work) says how to plan those two
milestones and what follows them.

A few things hold for every item:

- Say what will be observed, not how to arrange it, because the builder will learn things the plan didn't know.
- Add an item only when the user's words or the design need it, because reviewers fail the build on every one.
- An item can rely only on what exists when its milestone ends: this module's work, and what its `depends_on`
  delivers.
- A reviewer reads a milestone only if it has an `inspect` or an `ask`, or is the last of the module or of the stretch
  you planned. Otherwise passing its checks makes it Done.
- Mark an item with `needs` (`human_feedback`, `access` or `hardware`) when someone has to judge the work, approve a
  prompt or connect a device. Each one costs the user a sitting and holds back its module while it waits, so put
  judgements of finished work late, and gather those of several modules into one milestone that depends on them,
  such as a playtest. Where the whole product turns on something only the user can judge, such as how a game feels,
  plan an early milestone with a rough playable version for them to try, because a bad answer at the end would
  reopen finished modules.
- Keep a check that fails until its milestone is built out of the project's test command, which runs on every merge
  and would block every builder. Add it once the milestone is Done, if it should keep guarding the work.
- Change only what your task reaches. Changing an item's statement or proof sets its milestone back to Not Started,
  because the old proof proved something else, and a new milestone or a changed design waits for a design review
  before any builder starts it. Changing only an item's `lock` or `reads` keeps the progress.
- When you change an item, write it again from what it claims, as if it were new, rather than adding a clause,
  because an item patched after each review collects steps and prohibitions left from old fixes, and each builder
  has to work out which still apply.

[The format](references/done-when.md#donejson) is strict, because the script reads it. Read
[ways to prove an item](references/proofs.md) before you write a proof that needs a browser, a device, a reader new
to the product, a slow or shared resource, or a judgement of how something looks or feels.

## When you're done

You're done when building the plan, up to its last milestone with items, would give the user what the brief asks for:

1. The module list, the designs, the plan files and the done-when files agree, including about the interfaces.
2. Each milestone can be built from its own files, and its items can all be met together.
3. Every `check` you wrote or changed runs. Try each with the `check` command your prompt gives. If you wrote or
   changed the test command, or anything outside the plans folder, run the test command too, because `plan` runs it
   before your files merge.
4. The plan makes no choice about the goal that the user didn't make, apart from your assumptions.
5. Your report says what changed. The lead sees only the end of a long report, so just before the last line your
   prompt gives, list your assumptions, the decisions you left for the user from the settings' `Human decides` list,
   the names you proposed, and the references you chose with why, so the lead can check each with the user.
