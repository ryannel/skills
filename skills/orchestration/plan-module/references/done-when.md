# The plan file and the done-when file

Each module has two files that every agent working on it reads. The plan file says where the module stands. The
done-when file says what must be true before each milestone is Done, and how each thing will be proved. A planner
writes both. Builders, reviewers and the script then change only their own parts of them, in a fixed order, which
this file sets out.

Contents:
- [`<MODULE>-PLAN.md`](#module-planmd)
- [`<MODULE>-DONE.json`](#module-donejson)
- [Statuses and their stored names](#statuses-and-their-stored-names)
- [The record file](#the-record-file)
- [Who changes what, and when](#who-changes-what-and-when)
- [When a review fails](#when-a-review-fails)
- [What makes a good item](#what-makes-a-good-item)

## `<MODULE>-PLAN.md`

The plan file holds a module's milestones, a few status lines at the top, and a log. Whoever updates it rewrites
it in place, so it always describes the present. People and agents read the status lines first, so keep them
short. The `Reviews:` line holds only the latest review, and earlier ones go in the log, because a status line
that keeps growing stops being read.

```markdown
# <Module> plan
Reviews: <the latest review: what was reviewed, at which commit, the result, a link>
Milestone: M2 <name>
Now: <what is happening> (since <date>)
Next: <what follows>
Blocked: none

## M1 <name>: done
## M2 <name>: in progress
- [ ] <a piece of work: what exists or passes when it is finished>

## Log
- <date> <what changed and why>
```

## `<MODULE>-DONE.json`

The done-when file lists, for each milestone, its items: the things that must be true before the milestone is
Done. It is JSON because the script reads it, and because an agent is less likely to rewrite a whole JSON file
than a page of prose.

```json
{
  "module": "ONBOARDING",
  "milestones": [
    {
      "id": "M2",
      "name": "A new user signs up and lands on an empty dashboard",
      "state": "open",
      "fails": 0,
      "replans": 0,
      "needs": ["AUTH:M1"],
      "bar": "As quick and calm as Linear's sign-up, with an empty state as clear as Things'",
      "items": [
        {
          "id": "M2.1",
          "statement": "A valid email reaches the dashboard in three screens or fewer; invalid input is rejected inline",
          "check": "npx playwright test e2e/signup.spec.ts",
          "target": "web-chrome",
          "status": "open",
          "evidence": ""
        },
        {
          "id": "M2.2",
          "statement": "Every step is readable and tappable at 375 px with no layout shift as fields validate",
          "inspect": "each step and validation state at 375 px, as a screenshot sequence",
          "target": "web-mobile-safari",
          "status": "open",
          "evidence": "",
          "verdict": "",
          "review": ""
        }
      ]
    }
  ]
}
```

The planner writes the fields that say what a milestone asks for:

- `statement` says what must be true, in words a reviewer can judge.
- `check`, `inspect` and `ask` say how the item is proved: `check` is an Automated Check, `inspect` a Reviewer
  Inspection, and `ask` a Reviewer Question. An item uses at least one of them, and may use more.
  [Proofs](proofs.md) describes each.
- `target` is one of the targets in the project settings, meaning a device or platform the product runs on. When
  the proof runs on a stand-in, it is `proxy:<what it stands in for>`.
- `lock` is optional. It names an exclusive resource that the item's `check` needs, such as `gpu`, and the script
  takes that lock when it runs the check.
- `attended` is optional. It marks an item that needs human feedback, and says what a person or a piece of hardware
  has to do, such as "plug in the iPhone and approve the prompt". A builder does every other item first and
  reports these together, so the owner can settle them in one sitting.
- `bar` is the milestone's quality bar: how good it has to be, in words. It takes the quality bar in the project
  settings and makes it specific to this milestone, and it is what a Reviewer Inspection is judged against. Name
  real examples in it, or the project's [references](proofs.md#subjective-work) for subjective work.
- `needs` is optional. It lists the milestones in other modules that this one depends on, written `"AUTH:M1"`, and
  each must be Done before this one starts. Milestones inside one module already run in order, so listing an
  earlier one from the same module adds nothing. The script reports an error for a later milestone of the same
  module, for the milestone itself, for a milestone that is Too Many Failed Reviews, and for a cycle across
  modules, because none of those can ever be met.

Once approved, those fields are fixed. Only a planner that the `plan` command started, or the owner through the
`scope` command, changes them, because a builder who could edit them could pass anything.

The other fields record what happened:

- `status` is what the builder says about one item, `open` or `pass`, and `evidence` says where the builder's
  proof is saved.
- `verdict` is the reviewer's result for one item: `pass`, `fail`, or `cant_tell` for Could Not Judge. `review`
  links to the review file.
- `state` is the milestone's status, one of `open`, `in_progress`, `claimed`, `done`, `blocked` or `parked`. The
  next section says what each means. A Blocked milestone also has a `blocked` field saying what would unblock it.
- `findings` is the reviewer's list of the Must Fix findings of the last review, absent after a pass. Each finding
  has a short `name`, the `item` it fails (left out for one outside the items), and, when an item that failed
  before fails again for another reason, `different`, saying how it isn't the same defect. The script adds
  `repeat: true` to each finding an earlier round raised: one with the same name, or one on an item that failed
  before, unless `different` says otherwise.
- The script keeps four counts. `rounds` counts the failed reviews, and `fails` those with at least one repeated
  finding, both since the counts last started again. `replans` counts a planner's rewrites, and `diagnoses` its
  diagnoses (see [When a review fails](#when-a-review-fails)).

A milestone needs a reviewer if any of its items has `inspect` or `ask`, or if it is the module's last milestone.
The review of the last milestone reads the whole module, so work proved only by Automated Checks still gets read
by a reviewer once. Any other milestone is Done when its Automated Checks pass.

## Statuses and their stored names

The files and the script's output use shorter names than people do. The `In state` column is the value stored in
the `state` field, and the only thing to write there. The last column is the word the `ready` and `status`
commands print for a milestone in that status.

| Status | Means | In `state` | Printed as |
|---|---|---|---|
| Not Started | No builder has worked on it yet. | `open` | `ready`, when nothing stops it starting |
| Waiting on Dependency | It can't start until a milestone in another module is Done. | `open`, with `needs` | `waiting` |
| In Progress | A builder is working on it. | `in_progress` | `taken`, when another lead started it |
| Ready for Review | The builder has finished, and no review has run yet. | `claimed` | `review_owed` |
| Needs Human Feedback | It stopped on something only a person can decide. | `blocked`, on an item marked `attended` | `blocked` |
| Blocked | It stopped because something it needs is missing. | `blocked` | `blocked` |
| Awaiting Replan | Four failed reviews repeated an earlier finding, so a planner has to rewrite it. | `in_progress`, with `fails` at 4 | `replan_owed` |
| Awaiting Diagnosis | Six reviews failed, mostly on findings no earlier round raised, so a planner has to find out why. | `in_progress`, with `rounds` at 6 | `replan_owed` |
| Too Many Failed Reviews | It reached either of those again, after the rewrite or the diagnosis, and waits for the owner. | `parked` | `parked` |
| Done | Every check and review has passed. | `done` | `finished`, for a module whose milestones are all Done |

The commands also print `invalid` for a module whose done-when file is malformed, or has been changed by an agent
that may not change it.

A design has three statuses of its own. Design Ready for Review and Design Changes Requested are both printed as
`design_owed`. The reviewer's last line sets the status: `DESIGN OK` sets Design Approved, and `DESIGN CHANGES`
sets Design Changes Requested.

## The record file

Beside each done-when file, the script keeps `<MODULE>-ACCEPTED.json`, the record file. Only the script writes it,
in commits marked `Orchestrate-Loop: yes`. It is committed, so every worktree, every copy of the repository and
every lead reads the same one. For each milestone it holds:

- a hash of the items as last approved, by a planner run or by the owner;
- the commit the script tested, and the commit of the main branch it ran the checks on;
- every review;
- whether the milestone is Done, and what made it so: its Automated Checks, a reviewer, or the owner;
- a `usage` field on each builder run and each review, with the tokens used where the host reported them, so a
  milestone's cost can be read from the record.

It also holds the module's design review, against the design as it was then.

A milestone is Done only when the record file says so, under the key `accepted`, for the items as they are now. A
`done` in the done-when file is not enough, and that is what makes the done-when file safe for agents to edit.

In a repository that has never had a record file, the script takes each module as it stands the first time it
reads it, so work built before the project used these skills counts as Done. After that, a module with no record
file is new: nothing in it is Done, and its design needs a review.

## Who changes what, and when

Only one kind of agent changes each field at any time, and the hand-overs happen in this order.

| Change | Who | When |
|---|---|---|
| `state` from `open` to `in_progress` | Builder | It starts the milestone. |
| An item's `status` and `evidence` | Builder | While building. `pass` means it has proof from the item's target. |
| `state` from `in_progress` to `claimed` | Builder | Every item is `pass` with evidence, the checks pass and the work is merged, on a milestone that needs a reviewer. |
| `state` from `in_progress` to `done` | Builder | The same, on a milestone that needs no reviewer. The script runs the checks again before it records the milestone as Done. |
| `state` to `blocked`, with `blocked` | Script | The builder ends with `BLOCKED`. |
| `state` from `blocked` to `open` | Lead, with the `unblock` command | Whatever blocked it is resolved. |
| An item's `verdict` and `review` | Reviewer | Reviewing a milestone that is Ready for Review. Every item gets a result. |
| `state` from `claimed` to `done` | Reviewer | Every result is `pass`, and no Must Fix lies outside the items. |
| `state` from `claimed` to `in_progress`, and `findings` | Reviewer | Any result is `fail` or `cant_tell`, or a Must Fix lies outside the items. Every Must Fix is a finding, and every item that didn't pass is named by one. A Suggestion never is. |
| `findings` cleared | Script | The review passes. |
| 1 more in `rounds`, 1 more in `fails` if a finding repeated, and `repeat` on each finding | Script | After a failed review. A count a reviewer or planner writes is put back. |
| `status` back to `open` and `evidence` cleared, on the items that didn't pass | Script | After a failed review, so the next attempt is proved again. |
| `state` to `parked` | Script | After a failed review, when the escalation steps below reach Too Many Failed Reviews. |
| The planner's fields | Planner | A rewrite of a milestone that is Awaiting Replan, a revision after a design review, or a change the owner asked for. Milestones split off from a rewritten one start with its `replans` and `diagnoses` counts. The script saves the new items as the approved ones and clears the old proof. |
| `fails` and `rounds` back to 0, 1 more in `replans`, `state` to `open` | Script | A planner's plan, or the owner's `scope`, has changed the items of a milestone that was Awaiting Replan or Awaiting Diagnosis. After a diagnosis it also adds 1 to `diagnoses`. Done once, whatever the planner wrote in those fields. |
| `fails` and `rounds` back to 0, 1 more in `diagnoses`, and `state` to `parked` if the owner has to decide | Script | A diagnosing planner kept the plan and ended with `KEEP`. |
| The planner's fields, without counting as a rewrite | Owner | `owner scope`, when the owner changes what is wanted. On a milestone that is Awaiting Replan, the new scope is the rewrite. The script sets `fails`, `rounds` and `diagnoses` back to 0, and a Too Many Failed Reviews milestone back to `open`. |
| `state` to `done` with no review, back to `claimed` for a new review, or from `parked` to `open` | Owner | `owner accept`, `owner rereview` or `owner unpark`. An unpark sets `fails`, `rounds` and `diagnoses` back to 0. |

Reviewers and planners don't commit their own changes to these files. The script compares what they changed with
this table, and then either commits and merges all of the changes or rejects all of them.

`cant_tell` counts as a fail, because a milestone nobody could check is not Done. The review says what evidence
would settle the item, and the builder's next attempt has to produce it.

## When a review fails

These are the escalation steps, and they are written down only here. The `next` command, and the `next` field in
a review's result, apply them.

The steps follow two counts. `fails` counts the failed reviews that repeated a finding an earlier round raised,
which means fixes aren't holding. `rounds` counts every failed review, which catches a milestone whose fixes hold
but whose reviews keep finding something new. The first row that applies is the step.

| Counts | What happens |
|---|---|
| `fails` at 4 | The milestone is Awaiting Replan, and a planner rewrites it, because the plan may be the problem. If it has been rewritten before, the script sets it to Too Many Failed Reviews, and it waits for the owner. |
| `rounds` at 6 | The milestone is Awaiting Diagnosis. A planner reads every round and decides why it keeps failing. If it has been diagnosed before, the script sets it to Too Many Failed Reviews. |
| `fails` at 3, or `rounds` at 3 | A new builder session starts, with only the files and the review. |
| Any other failed review | The same builder fixes what the reviewer found, in the same session. |

A diagnosing planner either rewrites the milestone, which the script settles like a re-plan, or keeps the plan and
says who has to act. A builder who keeps breaking something gets a new session with the planner's reasons. A
reviewer whose findings go beyond the items is overruled: the next reviewer is told to judge the items as written.
A decision only the owner can make parks the milestone, with the diagnosis.

The counts start again from 0 after a rewrite, a diagnosis, `owner scope` or `owner unpark`. Rounds before that
no longer count as earlier rounds, so a finding they raised isn't a repeat.

When the script parks a milestone, its message to the owner lists what failed in each round, and offers three
answers as equals: accept the milestone as it is, change its scope, or unpark it for another try.

Each step exists because the one before it has already been tried. Repeating a step would spend the next attempt
on something already ruled out.

## What makes a good item

This section is for the planner. A good item is something you would refuse to call the milestone Done without.
Its proof would catch a convincing fake, and it depends only on this module. Keep an inspected item small, with
one quality in each, so a failure points at something specific. A milestone may have many items, as long as it
delivers one outcome.

Keep each item short: one thing that must be true, and the proof that would show it. Say what will be observed,
and leave it to the builder to arrange the observation. An item that scripts its own procedure breaks the first
time the builder learns something the plan didn't know, and each break costs a rewrite and another design review.
On one engine project the items grew to a median of 135 words, and its milestones were rewritten up to four times
each before any review had failed. In the rewrites we read from that project, the proof couldn't run as written.

Choose each proof on purpose, because `inspect` and `ask` are what bring in a reviewer.

- Use `ask` for something only reading can settle. Ask one question with a real answer, within the range the
  design names. "Would any violation fail this lint?" has no last answer, so each review finds one more corner and
  the milestone never finishes.
- If the builder will write the test that a `check` runs, add an `ask` that has the reviewer read that test,
  because a test written by the agent it grades proves little.
- A milestone the builder can do comfortably, proved by checks the builder didn't write, can be Done on those
  checks alone.
