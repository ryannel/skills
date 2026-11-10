# Glossary of the orchestrate set

The agreed name for each thing in the orchestrate set. The skills, the README and the agent files use these
names, and each skill defines the ones it uses before their first use, because each skill is read alone. The
files and the script's output keep their stored names, because existing records use them.

This file is for the people and agents who write the set. It is not installed with the skills.

## People and agents

**Owner**
The person the project is being built for. The README speaks to the owner as "you".
Avoid: user, person (in the skills), the human

**Agent**
One AI session working in the owner's repository.

**Host**
The program an agent runs in: Claude Code or Codex.

**Lead**
The agent the owner chats with. It runs the script's commands and comes back to the owner when a decision is
theirs. It never writes or judges code.
Avoid: orchestrator, coordinator

**Planner**
An agent that writes the plan: the module list, and each module's design, plan file and done-when file.

**Builder**
An agent that writes the code for one milestone, proves it and merges it.
Avoid: implementer, worker

**Reviewer**
An agent that judges a design or a milestone. Always a new session, so it has seen none of the work it judges.
Avoid: evaluator
Stored as: `orchestrate-evaluator`, the agent file's name

**Subagent**
A helper agent that an agent starts from inside its own session. The lead doesn't use them to build or review.

**The script**
`build/scripts/agent_loop.py`. Not an agent: a set of commands that start agents, run the tests and keep the
records. Write "the lead runs the `plan` command", never "the lead tells the script to plan".
Avoid: the loop, the harness

## The plan

**Project brief**
What the owner wants and why, written by the lead before any planning: the owner's request word for word, the
reason, what is left out, how the owner will judge the result, and the decisions made so far.

**Glossary**
A project's file of agreed names, `GLOSSARY.md` in the plans folder. This file is the set's own glossary.

**Project settings**
The facts about one project that every agent reads first, in `ORCHESTRATE.md`: where the plans are, the test
command, the targets, the project's rules.
Avoid: profile
Stored as: `ORCHESTRATE.md`; the script's messages say "the profile"

**Target**
A device or platform the product runs on, such as Chrome on a desktop or an iPhone. The project settings list
the targets, with how to run the product on each and how to capture it.
Not: a goal. "Target" never means what a milestone aims at.
Stored as: the `target` field of an item; `proxy:<what it stands in for>` when the planner accepts a stand-in

**Stand-in**
Something a proof runs on in place of its target, such as a Mac standing in for an iPhone. Only the planner can
accept one.
Stored as: `proxy:` in an item's `target`

**Module**
A part of the project that one builder can work on without touching the other parts.
Avoid: component, package (unless the code uses the word)

**Module list**
The file that names each module and what each provides to the others.

**Interface**
What one module provides to the others, such as a function that returns the balances. Only a planner changes
one, and a builder who needs a change writes a proposal.

**Design**
A module's file saying what the module must do for the people who use it.

**Plan file**
A module's `<MODULE>-PLAN.md`: its milestones, a few status lines at the top and a log.

**Milestone**
A piece of a module small enough for one builder to finish in one session.

**Depends on**
A milestone depends on a milestone in another module when it can't start until that one is Done.

**Done-when file**
A module's `<MODULE>-DONE.json`. For each milestone, it lists the items, how each is proved and its quality bar.
It is written before building, and the builder can't change what it requires.
Avoid: acceptance file, DONE file

**Item**
One thing that must be true before a milestone is Done.
Avoid: criterion, requirement

**Quality bar**
The standard a milestone's work is judged against, with a real example to point at: "help text as clear as
ripgrep's".
Stored as: the milestone's `bar` field

**Record file**
A module's `<MODULE>-ACCEPTED.json`, which only the script writes. It records which milestones are Done.
Avoid: acceptance record (except in the script's messages)

**Worktree**
A second working copy of the repository. Each module is built in its own, so builders don't overwrite each
other's files.

## Proving and judging

**Automated Check**
A shell command that proves an item if it exits with 0. The builder runs it, and the script runs it again.
Stored as: the item's `check` field

**Reviewer Inspection**
A proof in which a reviewer runs the product on its target and judges what it sees.
Stored as: the item's `inspect` field

**Reviewer Question**
A proof in which a reviewer answers a question by reading the code, an interface or a design.
Stored as: the item's `ask` field

**Evidence**
Saved proof that an item passed, such as a test log or a screenshot, taken from the item's target.
Stored as: the item's `evidence` field, which says where the proof is saved

**Capture**
A screenshot, recording or log taken from a target while the product runs. A capture becomes evidence when it is
saved as proof of an item.
Avoid: captures as a word for all evidence

**Test command**
The project's own command that runs its tests, run before every merge.
Stored as: the `Check:` line of the project settings
Not: Automated Check. An Automated Check proves one item; the test command tests the whole project.

**Review**
A reviewer's written judgement of a design or a milestone. Only a review started by the script's `review`
command is saved.

**Finding**
One problem a review reports, with where it is.

**Must Fix**
A finding that fails the milestone or the design.
Avoid: blocking

**Suggestion**
A finding that doesn't fail anything.
Avoid: advisory

**Could Not Judge**
A reviewer's verdict on an item nobody could check. It counts as a fail.
Stored as: `cant_tell`

**Round**
One review of a milestone. A failed round is one the milestone failed.
Stored as: `rounds`, the count of failed rounds since the counts last started again

**Repeated finding**
A Must Fix that an earlier round also raised: one with the same name, or one on an item that failed before,
unless the reviewer says how it differs.
Stored as: `repeat` on the finding; `fails` counts the failed rounds with one
Avoid: recurring finding

**Diagnosis**
A planner's reading of every round of a milestone that keeps failing on new findings, to decide why. It either
rewrites the milestone or keeps the plan and names who has to act.
Stored as: `diagnoses`, and the `KEEP` line that ends a planner's turn

## Statuses

A milestone's status, in the order a milestone usually meets them:

| Status | Means | Stored as |
|---|---|---|
| Not Started | No builder has worked on it yet | `open` |
| Waiting on Dependency | It can't start until another module's milestone is Done | `waiting` |
| In Progress | A builder is working on it | `in_progress`, or `taken` when another lead started it |
| Ready for Review | The builder says it is finished, and nobody has verified it | `claimed` |
| Needs Human Feedback | It stopped on something only a person can decide | `blocked`, on an item marked `attended` |
| Blocked | It stopped because something it needs is missing | `blocked` |
| Awaiting Replan | Four failed rounds had a repeated finding, so a planner has to rewrite it | `replan_owed` |
| Awaiting Diagnosis | Six rounds failed, mostly on new findings, so a planner has to find out why | `replan_owed` |
| Too Many Failed Reviews | It reached either of those again after the rewrite or the diagnosis, and waits for the owner | `parked` |
| Done | Every check and review has passed | `done`, or "accepted" |

Avoid: claimed, parked, attended (in prose)

A design has three statuses of its own: Design Ready for Review, Design Changes Requested and Design Approved.

## Commands and settings

**Merge**
Bring a builder's work into the main branch, through the script's `land` command, which runs the test command
first and holds a lock so two builders can't merge at once.
Avoid: integrate, land (in prose)
Stored as: the `land` command; the `Integrate:` line of the project settings, which says whether to push or
fast-forward

**Owner decides list**
The line of the project settings that lists what only the owner may decide, such as spending or publishing.
Stored as: the `Owner decides` line

**Exclusive resource**
Something only one run at a time may use, such as a simulator. The script's `lock` command holds it.
Stored as: the `Exclusive resources` line of the project settings
