# Glossary of the orchestrate set

The agreed name for each thing in the orchestrate set. The skills, the README and the agent files use these
names, and each skill defines the ones it uses before their first use, because each skill is read alone. The
script, its files, its commands and its messages use these names too. `Stored as` gives the name as it is
written in a file, a command or the script's output, where that differs from the entry's name.

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
Stored as: `orchestrate-reviewer`, the agent file's name

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
Stored as: `ORCHESTRATE.md`

**Target**
A device or platform the product runs on, such as Chrome on a desktop or an iPhone. The project settings list
the targets, with how to run the product on each and how to capture it.
Not: a goal. "Target" never means what a milestone aims at.
Stored as: the `target` field of an item; `stand_in:<what it stands in for>` when the planner accepts a stand-in

**Stand-in**
Something a proof runs on in place of its target, such as a Mac standing in for an iPhone. Only the planner can
accept one.
Stored as: `stand_in:` in an item's `target`

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
A module's `PLAN.md`: what is left to build, milestone by milestone, and the assumptions open for the owner.

**Log**
A module's `LOG.md`: its history, one dated entry per event.

**Status page**
`STATUS.md` in the plans folder, which only the script writes: an overview for the owner, then every module in
build order with its status.
Avoid: dashboard, status lines

**Module table**
The table at the top of `ARCHITECTURE.md` listing every module in build order, what each is for and what it needs.

**Milestone**
A piece of a module small enough for one builder to finish in one session.

**Depends on**
A milestone depends on a milestone in another module when it can't start until that one is Done.
Stored as: the milestone's `depends_on` list, such as `["CORE:M3"]`

**Done-when file**
A module's `DONE.json`. For each milestone, it lists the items, how each is proved and its quality bar.
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
A module's `ACCEPTED.json`, which only the script writes. It records which milestones are Done.
Avoid: acceptance record
Stored as: `ACCEPTED.json`

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
Stored as: the `Test command:` line of the project settings
Not: Automated Check. An Automated Check proves one item; the test command tests the whole project.

**Review**
A reviewer's written judgement of a design or a milestone. Only a review started by the script's `review`
command is saved.

**Finding**
One problem a review reports, with where it is.

**Must Fix**
A finding that fails the milestone or the design.
Avoid: blocking
Stored as: `must_fix`

**Suggestion**
A finding that doesn't fail anything.
Avoid: advisory
Stored as: `suggestion`

**Could Not Judge**
A reviewer's verdict on an item nobody could check. It counts as a fail.
Stored as: `could_not_judge`

**Needs human feedback, needs access, needs hardware**
How a planner marks an item that a builder can't finish alone. Needs human feedback: someone has to look at the
result and judge it, because the builder can't tell. Needs access: someone has to approve a permission or a
prompt, so the builder runs in a visible session while the owner is at the machine, and asks for access as soon
as it starts. Needs hardware: a device has to be connected, so the builder runs the same way.
Avoid: attended, needs a person, person or hardware
Stored as: the item's `needs` field, such as `{"type": "access", "what": "approve Computer Use for IINA"}`,
with `type` one of `human_feedback`, `access` or `hardware`

**Human Feedback**
The owner's verdict on an item a builder couldn't judge, such as "looks good to me". The script records it with
the question the lead asked, the owner's words, the items it covers and the time, and the reviewer reads it as the
owner's own words.
Not: approving access or connecting a device. Those are done, not said, so nothing is recorded. Not a `--message`
from the lead either, which a reviewer can't count as the owner's words.
Avoid: owner answer, owner's answers
Stored as: `human_feedback` in the record file, each with `asked`, `said`, `items` and `at`; recorded by the
`owner feedback` command

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

A milestone's status, in the order a milestone usually meets them. Waiting and Blocked each carry a reason, written
after a colon, such as "Blocked: Needs Access".

| Status | Means | Stored as |
|---|---|---|
| Not Started | No builder has worked on it yet | `not_started` |
| In Progress | A builder is working on it | `in_progress`, or `taken` when another lead started it |
| Ready for Review | The builder says it is finished, and nobody has verified it | `ready_for_review` |
| Waiting | It isn't stuck. The next step is already lined up, and happens without anyone stepping in | `waiting`, in the script's output, with its `reason` |
| Blocked | It can't move until someone steps in | `blocked`, with the milestone's `blocked` field giving `reason`, `items` and `what` |
| Done | Every check and review has passed | `done`, or "accepted" |

The reasons a milestone is Waiting:

| Reason | Means | Stored as |
|---|---|---|
| On Dependency | It can't start until another module's milestone, already planned, is Done | `on_dependency` |
| For Replan | Four failed rounds had a repeated finding, so a planner rewrites it | `for_replan` |
| For Diagnosis | Six rounds failed, mostly on new findings, so a planner finds out why | `for_diagnosis` |

The reasons a milestone is Blocked, and who steps in:

| Reason | Means | Stored as |
|---|---|---|
| Needs Human Feedback | A builder couldn't judge an item and asked for a human eye. The lead shows the owner the evidence and the question, and the owner's reply is the Human Feedback | `needs_human_feedback` |
| Needs Access | A builder couldn't get a permission or an approval prompt, usually because it ran where nobody could approve it. The next visible run, with the owner at the machine, unblocks it | `needs_access` |
| Needs Hardware | A device wasn't connected. The next run with the device there unblocks it | `needs_hardware` |
| Needs Context | The builder is missing a fact. The lead supplies it | `needs_context`, from the builder's `NEEDS_CONTEXT` ending |
| Needs Dependency | It needs something another module owns that no plan provides yet. A planner adds it | `needs_dependency` |
| Too Many Failed Reviews | It reached For Replan or For Diagnosis again after the rewrite or the diagnosis. The owner decides what happens to it, and the `owner reopen` command records it | `too_many_failed_reviews` |

A milestone stops only when it is finished or Blocked. Nothing should ask the owner to confirm a step they have
already taken, such as approving a prompt.

Avoid: claimed, parked, attended, Waiting on Dependency, Awaiting Replan, Awaiting Diagnosis, Needs Human
Feedback as a status of its own (in prose)

A design has three statuses of its own: Design Ready for Review, Design Changes Requested and Design Approved.

## Commands and settings

**Merge**
Bring a builder's work into the main branch, through the script's `merge` command, which runs the test command
first and holds a lock so two builders can't merge at once.
Avoid: integrate, land (in prose)
Stored as: the `merge` command, and the `merge` lock; the `Merge:` line of the project settings, which says
whether to push or fast-forward

**Owner decides list**
The line of the project settings that lists what only the owner may decide, such as spending or publishing.
Stored as: the `Owner decides` line

**Exclusive resource**
Something only one run at a time may use, such as a simulator. The script's `lock` command holds it.
Stored as: the `Exclusive resources` line of the project settings
