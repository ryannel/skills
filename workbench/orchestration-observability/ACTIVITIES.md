# What people do when they look at a project

The first step in designing orchestrate's observability page: the activities it serves, the questions each one asks, and where the answers come from. Layout comes after this.

## Who looks, and how

- **The user and collaborators.** Each runs the page on their own clone. A collaborator has none of the chat history, so the page explains itself in plain words.
- **On a computer or a phone screen.** The layout works at both sizes, served on localhost. The phone view leads with getting your bearings; the plan map, proof and diagnosis are built for a large screen.
- **Live.** The script serves the page and owns all of its data: one model behind `status`, `flow`, `history` and the page, pushed to open pages as it changes.
- **Show only.** The page takes no actions. Blocked work packages are shown as waiting; you resolve them, and anything else, through the lead and the agent tools.

## The activities

**1. Getting your bearings.** You come back after a while.
What changed since I last looked? Is it moving? What's running now? What's waiting, and on what? How close is each milestone?
"Since you last looked" is remembered per viewer in the browser.

**2. Understanding the project from cold.** Mostly collaborators.
What is this, what is the vision and scope document, what will it do when it's finished, and where are we?

**3. Reviewing the plan.** A module is planned, or the plan changes.
Does the breakdown from the vision and scope document to modules to work packages match what was asked? What depends on what? What is the longest chain of work packages before each milestone? What did the planners assume (Choices made for you)? Are the done-when items the right proof? What changed in the plan, and why?

**4. Following delivery.** While it runs.
What's running, on which host, and for how long? What's waiting, and on what: a work package it depends on, a lock, a review, a merge, or the user (needs access, needs hardware, needs user feedback)? Is it on pace? When will the next milestone close?

**5. Checking how it was proven.** A work package says done.
Which items, which checks passed, what the reviewer asked and judged, which reviews failed and what changed before it passed. Most work packages are proven by tests, so the core of this is items, checks and verdicts. Images and captures are the exception: shown when they still exist on this machine, and marked as cleared when they don't.

**6. Diagnosing orchestration.** Something feels slow or wrong.
Is the problem in the work or in the machinery? In the work: repeated findings, failed reviews, diagnoses, re-plans, stuck runs. In the machinery: slow checks, lock contention, merge waits, errors, machine load, Codex quota.

**7. Cost and limits.** Where is the spend going, and will we hit the weekly limit? The current dashboard covers most of this.

**8. Retro.** After a milestone.
What did it cost, what went wrong, and how good was the plan: work packages planned against work packages added, and failed reviews by module and by kind of agent.

## A first structure

| Area | Activities | Phone |
|---|---|---|
| **Now** | 1 | First screen |
| **Project** | 2 | Yes |
| **Plan** | 3 | Read only |
| **Delivery** | 4 | Summary |
| **Machinery** | 6, 7 | Large screen |
| **Retro** | 8 | Large screen |

**The module and work package pages hold it together.** Almost every question ends on one work package: its plan text, what it depends on and what depends on it, its status and what it's waiting on, its runs, its reviews and their item verdicts, its checks, and what it cost. Proof (activity 5) is a section of the work package page, not an area of its own. Every area drills into the same pages.

Three ideas run through every area:

- **Milestones give the plan a scale people can follow.** See [Milestones](#milestones) below.
- **Each stalled work package is waiting on exactly one thing,** shown the same way everywhere: a dependency, a lock, a review, a merge, the user, or a failure. That makes "what's waiting on what" and "find the blockers" the same view.
- **What changed is as important as what is.** That goes for status, the plan and the assumptions.

## Where the data is

| Data | Source | On a collaborator's clone |
|---|---|---|
| Vision and scope document, modules, designs, plans, logs | `docs/plans/` | Yes, through git |
| Work packages, items, checks, reviewer questions, `depends_on` | `DONE.json` | Yes |
| Review verdicts per item, finding names, commits, who reviewed | `RECORD.json` | Yes |
| Status page, Needs you now, Choices made for you | `STATUS.md` | Yes |
| Review text, handoffs, saved check output, images | `.orchestrate/evidence/` | No, local and untracked |
| Live runs, locks, jobs, machine load | the script's state | No, only the machine running the agents |
| Sessions, cost, quota, errors | delivery history | No, only the machine that ran the agents |

So on a collaborator's machine, Plan, Delivery (from records), Project and the core of the proof all work. Review text, evidence files, live runs and cost appear only where the agents ran. The page should say plainly when data isn't on this machine, rather than show empty charts.

## Decided

- **Each review gets a short summary in the record,** so a collaborator can see why a review failed, not only which findings it raised. The full review text stays local.
- **Serving the page is its own command,** separate from the supervisor.

## Milestones

Thrum's vision and scope document (`BRIEF.md`) lists milestones, which it calls gates: named checkpoints on the way to the first release (G3s, G4, G6, G7, and others). Each closes through one module, usually at a work package whose name ends "and G4 closes". Orchestrate itself has no such idea: its plan is modules and work packages, with `depends_on` links, up to the one goal. Thrum's milestones are prose in that document, so the script can't read them.

They are worth supporting, because a milestone answers "how far are we from the thing I care about?", which a list of 36 modules does not. The cheapest form: **a milestone is a work package marked as closing it.** Everything it needs follows from the plan: the work packages before it in its module, and its `depends_on` links, followed back. So progress toward a milestone, and what is left on its path, come from data the plan already has. On Thrum today:

| Milestone | Closing work package | Work packages it needs | Not done yet |
|---|---|---|---|
| G3s | `ATMOSPHERE:M6` | 27 | 0 |
| G6 | `CREATOR:M3` | 10 | 0 |
| G4 | `APPLE-PRESENTATION:M11` | 27 | 6, all in APPLE-PRESENTATION |

This assumes a module's work packages are built in plan order, as `run` builds "a module's next work package".

Agreed names (2026-11-24): goal, milestone, work package, task, vision and scope document; see the orchestrate glossary. Open: where the mark lives, probably a field on the closing work package in the done-when file, with the vision and scope document naming each milestone.
