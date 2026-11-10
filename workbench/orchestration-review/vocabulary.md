# Orchestrate vocabulary

Agreed with the owner on 10 November 2026. The rule: use the explicit, familiar name, even when it's longer. Define
each term before its first use. The files and commands keep their stored names, because existing records use them;
the docs use the names below and give the stored name once, where a reader will meet it.

The script is not an agent. Write "the lead runs the `plan` command", never "the lead tells the loop to plan".

## Who and what

| Term | Means | Was |
|---|---|---|
| agent | one AI session, in Claude Code or Codex, working in the repository | |
| host | Claude Code or Codex | host, vendor |
| lead | the agent the owner chats with; runs commands, never writes or judges code | |
| planner | an agent that writes the plan | |
| builder | an agent that writes the code | |
| reviewer | a new agent that judges a plan or code | reviewer, evaluator |
| the script | `agent_loop.py`, a set of commands the lead runs | the loop |
| owner, "you" | the person | |

## Parts of a project

| Term | Means | Was |
|---|---|---|
| module | a part of the project one builder can work on without touching the others | |
| milestone | a piece of a module small enough for one builder session | |
| item | one thing that must be true before a milestone is Done | |
| done-when file | the list of a module's items, by milestone | done-when file, definitions |
| project settings | `ORCHESTRATE.md` | profile |
| module list | which modules exist | module map, build order |
| interface | what one module provides to the others | contract |
| depends on | a milestone needs another module's milestone Done first | `needs` |
| scope | what the owner asked for | |
| project brief | `BRIEF.md` in the plans folder: what the owner wants, why, and how it will be judged, approved by the owner before planning (added 10 November 2026) | purpose doc, brief |
| glossary | `GLOSSARY.md` in the plans folder: the agreed name for each thing in the project (added 10 November 2026) | |
| a module's entry in the module list | the few lines that say what a module is for | the module's brief |
| worktree | a second working copy of the repository, one per builder | |
| main branch | | tip, integrated tip, base |
| merge | put work on the main branch | land, integrate, adopt |

## Milestone statuses

| Status | Means | Extra info | Stored or printed today as |
|---|---|---|---|
| Not Started | no builder has worked on it | | `open`, ready |
| Waiting on Dependency | can't start until another module's milestone is Done | which milestone | waiting, `needs` |
| In Progress | a builder is working on it | failed reviews so far; which lead started it | `in_progress`, taken |
| Ready for Review | the builder has finished and no review has run | | `claimed`, review owed |
| Needs Human Feedback | stopped on something only a person can decide | the question | `blocked` on an `attended` item |
| Blocked | stopped because something it needs is missing | what would unblock it | `blocked` |
| Awaiting Replan | failed four reviews; the planner has to rewrite it | | replan owed |
| Too Many Failed Reviews | failed four more after the rewrite; waits for the owner | | `parked` |
| Done | every check and review has passed | | accepted, `done` |

## Design statuses

| Status | Means | Was |
|---|---|---|
| Design Ready for Review | written, not yet read by a reviewer | draft, design owed |
| Design Changes Requested | a reviewer found a problem the planner must fix | `DESIGN CHANGES` |
| Design Approved | a reviewer passed it; building can start | `DESIGN OK` |

## Proving and reviewing

| Term | Means | Was |
|---|---|---|
| Automated Check | an item proved by a command that passes or fails | `check` |
| Reviewer Inspection | an item proved by a reviewer running the product and looking | `inspect` |
| Reviewer Question | an item proved by a reviewer reading the code | `ask` |
| Needs Human Feedback (on an item) | only a person can settle it | `attended` |
| Pass, Fail, Could Not Judge | a reviewer's result for one item | `pass`, `fail`, `cant_tell` |
| Must Fix, Suggestion | the two kinds of problem a reviewer reports | blocking, advisory |
| escalation steps | what happens after each failed review | the ladder |
| evidence | saved proof, such as screenshots | evidence, captures, proof |
| the project's test command | the settings file's `Check:` line | Check |

## Subjective work

| Term | Means | Was |
|---|---|---|
| subjective work | work judged by taste | taste-led |
| quality bar | how good it has to be, in words | bar |
| reference | what a reviewer compares the work against | anchor |
| option, chosen option | the alternatives the owner picks from, and the pick | variant, direction |
| minimum requirements | what every option must meet | floor |

## Running

| Term | Means | Was |
|---|---|---|
| in the background, in the app | where a session runs | headless, visible path |
| usage limit | the Codex weekly limit | quota |
| the question for the owner | what the lead asks the owner at a stop. The script prints it as `ask`; a rename to `question` was discussed and not made | `next.ask` |
