# The module's files

Each module has a folder of its own in the plans folder, `docs/plans/<MODULE>/`, and every agent working on the
module reads the files in it. The plan file says what is left to build. The done-when file says what must be true
before each milestone is Done, and how each thing will be proved. A planner writes both. Builders, reviewers and
the script then change only their own parts of them, in a fixed order, which this file sets out.

Contents:
- [Where everything is](#where-everything-is)
- [`STATUS.md`, the human's page](#statusmd-the-humans-page)
- [The module table](#the-module-table)
- [`PLAN.md`](#planmd)
- [`LOG.md`](#logmd)
- [`DONE.json`](#donejson)
- [Statuses and their stored names](#statuses-and-their-stored-names)
- [The record file](#the-record-file)
- [Who changes what, and when](#who-changes-what-and-when)
- [When a review fails](#when-a-review-fails)
- [What makes a good item](#what-makes-a-good-item)

## Where everything is

Every project keeps its plans in the same place, so the human and every agent can always find them. The plans
folder is `docs/plans` unless the project settings name another.

```
ORCHESTRATE.md               the project settings
docs/plans/
  STATUS.md                  the human's page; the script writes it
  BRIEF.md                   what the human wants and why
  GLOSSARY.md                the agreed name for each thing
  ARCHITECTURE.md            the list of modules, then the interfaces between them
  <MODULE>/
    DESIGN.md                the design: mechanisms and interfaces
    PLAN.md                  what is left to build
    LOG.md                   what happened, oldest first
    DONE.json                the done-when file
    RECORD.json            the record file; the script writes it
    BRIEF.md                 optional: the human's brief for this module alone
docs/evidence/<MODULE>/      proof, reviews, and the briefs written for reviews
```

A project's plans live in these files and nowhere besides. A plan written in another shape or another place is
converted into these files and the old one deleted, because two plans for one thing drift apart and the human can't
tell which is current. Notes an agent keeps while it works stay out of the repository.

Each file has its readers, and is written for them:

| File | Written for | So it is written |
|---|---|---|
| `STATUS.md` | The human, and the lead | By the script, from stored facts |
| `ARCHITECTURE.md`'s module table, milestone names | The human | In plain words, as what someone can see or do |
| `DESIGN.md`, the notes in `PLAN.md`, `DONE.json` | Builders and reviewers | Precisely, with paths and IDs, as the `prompting-agents` skill describes |
| `LOG.md` | Planners and the lead, later | One dated entry per event, a few lines at most |

## `STATUS.md`, the human's page

The script writes `STATUS.md` after every record it merges, and nobody edits it, because a page somebody has to
remember to update goes stale. It is built only from what the script stores: the done-when and record files, the
module table, and the open assumptions in each plan. `agent_loop.py status --format md` prints the same page.

It has two sections. The overview comes first, because it is what the human reads day to day:

- one line of progress, such as `4 of 11 modules done · 2 in progress · 5 to come`;
- what is waiting on the human: open assumptions, items that need a person or hardware, milestones that are Too
  Many Failed Reviews, proposed names in the glossary;
- what is happening now and what comes next, each milestone by its name;
- what was recently done.

Below it, all the modules in build order, with each one's status: Done, how far along it is, what it waits on, or
Not planned yet.

Because the page is made from milestone names and the module table, those are the words the human reads. Name a
milestone for what someone can see or do once it is Done ("A new user signs up and lands on an empty dashboard"),
not for the work inside it ("Auth handler refactor").

## The module table

`ARCHITECTURE.md` opens with a table of every module, in the order they are built. The script reads it, so keep
this exact header:

```markdown
| # | Module | What it's for | Needs |
|---|---|---|---|
| 1 | AUTH | People sign in, and stay signed in across devices | |
| 2 | ONBOARDING | A new user gets from sign-up to a first project | AUTH |
```

`What it's for` is one sentence in plain words, for the human. The table has no status column, because the script
adds the status in `STATUS.md`. A module the planner has listed but not yet planned shows there as Not planned
yet, which is how the human sees what is still to come. The rest of `ARCHITECTURE.md`, what each module owns and
the interfaces, comes after the table.

## `PLAN.md`

The plan file says what is left to build, and nothing else. It holds no status lines, because the script knows
each milestone's status and writes it to `STATUS.md`. Status written by hand goes stale, and grows into
paragraphs nobody reads.

```markdown
# <Module> plan

## Open for the human
- Assumption: <a reading of the human's words the planner chose, which the human can overturn>

## M1 <what someone can see or do>: done
[review](../../evidence/<MODULE>/review.md)

## M2 <what someone can see or do>
<A few sentences for the builder, on what the items and the design don't say. Nothing, when there is nothing.>

## M3 <what someone can see or do>
```

- A Done milestone shrinks to its heading and one link to its review. The detail stays in the review, the log and
  git.
- `Open for the human` holds only open assumptions. When the human answers one, delete the line. The lead records the
  answer with the `human` command.
- Briefs written for reviews go to `docs/evidence/<MODULE>/`, beside the review. Design goes in `DESIGN.md`.

Under a milestone that isn't Done goes a note for its builder, and only when there is something the items and the
design don't say. That is usually one of three things: what already exists that the milestone builds on, and where it
is; what another module owns that the milestone uses or could be tempted to change; or an order, where the order is
part of the task, as when one item's measurement sets the bound another item tests. Many milestones need no note, and
have only their heading.

The note is written in sentences, and it has no list of steps to tick. What must be true is in the done-when file
and how the module works is in the design, so a list of steps would say both again, in an order chosen before the
code existed. The builder sees the code close up and plans the work better from there. Nothing reads a tick
either: the items' `builder_result`, the log and a handoff already tell a later session what an earlier one finished.

A limit on what a builder may do goes where it holds, with its reason beside it. One that is true of every module,
such as how a browser is started or a path nobody edits, goes in the project settings or the building guidance
they link to. One about this module goes in the design. Only a limit on this one milestone goes in its note.

The script checks every plan file when it is merged, for five things: a plan over about 1,500 words, a status line
(`Now:`, `Next:`, `Blocked:`, `Milestone:` or `Reviews:`), a `###` heading, a log, and more than one line under a Done
milestone. On a planner's turn it refuses a plan that has one of them, and elsewhere it warns. Each is a way a plan
file grows until no builder reads all of it.

## `LOG.md`

The log is the module's history: decisions, proposals to change an interface, what a failed review found, and
what the human said. Each entry is one dated line, with at most a few lines under it, and the newest at the
bottom. Longer detail goes in `docs/evidence/<MODULE>/` with a link. The script warns about an entry over eight
lines. Nobody reads the log to find out where the module stands, so it may grow.

```markdown
- 2026-11-03 M2: review failed on the empty state; fixed, and the second review passed.
- 2026-11-05 Human: "keep the old URL working" (quoted from chat).
```

## `DONE.json`

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
      "status": "not_started",
      "failed_reviews": 0,
      "failed_reviews_with_repeat": 0,
      "depends_on": ["AUTH:M1"],
      "quality_bar": "As quick and calm as Linear's sign-up, with an empty state as clear as Things'",
      "items": [
        {
          "id": "M2.1",
          "statement": "A valid email reaches the dashboard in three screens or fewer; invalid input is rejected inline",
          "check": "npx playwright test e2e/signup.spec.ts",
          "target": "web-chrome",
          "builder_result": "open",
          "evidence": ""
        },
        {
          "id": "M2.2",
          "statement": "Every step is readable and tappable at 375 px with no layout shift as fields validate",
          "inspect": "each step and validation state at 375 px, as a screenshot sequence",
          "target": "web-mobile-safari",
          "builder_result": "open",
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
  The proofs reference, `proofs.md`, describes each.
- `target` is one of the targets in the project settings, meaning a device or platform the product runs on. When
  the proof runs on a stand-in, it is `stand_in:<what it stands in for>`.
- `lock` is optional. It names an exclusive resource that the item's `check` needs, such as `gpu`, and the script
  takes that lock when it runs the check.
- `needs` is optional. It marks an item that a builder can't finish alone, as `{"type": ..., "what": ...}`. The
  `type` is one of three:
  - `human_feedback`: someone has to look at the result and judge it, because no agent can tell, such as whether
    a sound is pleasant. The builder does every other item first, then stops with the milestone Blocked, and the
    lead puts the question to the human. The human's reply is recorded as Human Feedback.
  - `access`: the human has to approve a permission or a prompt, such as Computer Use for an app. The builder can
    finish it only in a visible session while the human is at the machine, and asks for the access as soon as it
    starts. The approval itself is all it needs, so nothing is recorded.
  - `hardware`: a device has to be connected, such as an iPhone. The builder can finish it only when the device
    is there.

  `what` says in plain words what is needed, such as "approve Computer Use for IINA" or "plug in the iPhone".
  Builders do these items together, so the human can settle them in one sitting.
- `quality_bar` is the milestone's quality bar: how good it has to be, in words. It takes the quality bar in the project
  settings and makes it specific to this milestone, and it is what a Reviewer Inspection is judged against. Name
  real examples in it, or the project's reference sets for subjective work.
- `depends_on` is optional. It lists the milestones in other modules that this one depends on, written `"AUTH:M1"`, and
  each must be Done before this one starts. Milestones inside one module already run in order, so listing an
  earlier one from the same module adds nothing. The script reports an error for a later milestone of the same
  module, for the milestone itself, for a milestone that is Too Many Failed Reviews, and for a cycle across
  modules, because none of those can ever be met.

Once approved, those fields are fixed. Only a planner that the `plan` command started, or the human through the
`scope` command, changes them, because a builder who could edit them could pass anything.

The other fields record what happened:

- `builder_result` is what the builder says about one item, `open` or `pass`, and `evidence` says where the builder's
  proof is saved.
- `verdict` is the reviewer's result for one item: `pass`, `fail`, or `could_not_judge` for Could Not Judge. `review`
  links to the review file.
- `status` is the milestone's status, one of `not_started`, `in_progress`, `ready_for_review`, `done` or `blocked`.
  The next section says what each means. A Blocked milestone also has a `blocked` field, with the `reason`, the
  `items` it concerns, and `what` would unblock it.
- `findings` is the reviewer's list of the Must Fix findings of the last review. It is absent after a pass. Each
  finding has a short `name`, and the `item` it fails, which is left out for a finding outside the items. The
  script adds `repeat: true` to a finding that an earlier review also raised, meaning one with the same name or
  one on an item that failed before. When an item that failed before fails again for another reason, the reviewer
  adds `different`, saying how it isn't the same defect, and the script doesn't count it as a repeat.
- The script keeps three counts. `failed_reviews` counts the failed reviews, and `failed_reviews_with_repeat`
  those with at least one repeated finding, both since the counts last started again. `diagnoses` counts the
  times a planner has diagnosed the milestone, which is 0 or 1 (see [When a review fails](#when-a-review-fails)).

A milestone needs a reviewer if any of its items has `inspect` or `ask`, or if it is the module's last milestone.
The review of the last milestone reads the whole module, so work proved only by Automated Checks still gets read
by a reviewer once. Any other milestone is Done when its Automated Checks pass.

## Statuses and their stored names

The `In status` column is the value stored in the milestone's `status` field, and the only thing to write there.
The last column is what the `ready` and `status` commands print for a milestone in that status.

A milestone that is Waiting isn't stuck: its next step is already lined up, and happens without anyone stepping
in. A milestone that is Blocked can't move until someone steps in. Each carries a reason.

| Status | Means | In `status` | Printed as |
|---|---|---|---|
| Not Started | No builder has worked on it yet. | `not_started` | `can_start`, when nothing stops it starting |
| In Progress | A builder is working on it. | `in_progress` | `in_progress_elsewhere`, when another lead started it |
| Ready for Review | The builder has finished and merged, the script's checks passed on the merged work, and no review has run yet. Only the script sets it. | `ready_for_review` | `ready_for_review` |
| Waiting: On Dependency | It can't start until a milestone in another module, already planned, is Done. | `not_started`, with `depends_on` | `waiting`, `reason: on_dependency` |
| Waiting: For Diagnosis | It keeps failing review, so a planner finds out why before any more building. Either four failed reviews repeated an earlier finding, or six reviews failed in all. | `in_progress`, with `failed_reviews_with_repeat` at 4 or `failed_reviews` at 6 | `waiting`, `reason: for_diagnosis`, with the `cause` |
| Blocked | It can't move until someone steps in. The `blocked` field's `reason` says why. | `blocked` | `blocked`, with its `reason` |
| Done | Every check and review has passed. | `done` | `finished`, for a module whose milestones are all Done |

A Blocked milestone's `reason` is one of these:

| Reason | Means, and who steps in |
|---|---|
| `needs_human_feedback` | A builder couldn't judge an item and asked for a human eye. The human's reply, recorded as Human Feedback, unblocks it. |
| `needs_access` | A builder couldn't get a permission or an approval prompt. The next visible run, with the human at the machine, unblocks it. |
| `needs_hardware` | A device wasn't connected. The next run with the device there unblocks it. |
| `needs_context` | The builder is missing a fact. The lead supplies it. |
| `needs_dependency` | It needs something another module owns that no plan provides yet. A planner adds it. |
| `too_many_failed_reviews` | It kept failing review after its diagnosis, or the planner found that the decision is the human's. The human decides what happens to it. |

The commands also print `invalid` for a module whose done-when file is malformed, or has been changed by an agent
that may not change it.

A design has three statuses of its own. Design Ready for Review and Design Changes Requested are both printed as
`design_not_approved`. The reviewer's last line sets the status: `DESIGN OK` sets Design Approved, and `DESIGN CHANGES`
sets Design Changes Requested.

## The record file

Beside each done-when file, the script keeps `RECORD.json`, the record file. Only the script writes it,
in commits marked `Orchestrate-Script: yes`. It is committed, so every worktree, every copy of the repository and
every lead reads the same one. For each milestone it holds:

- a hash of the items as last approved, by a planner run or by the human;
- the commit the script tested, and the commit of the main branch it ran the checks on;
- every review;
- whether the milestone is Done, and what made it so: its Automated Checks, a reviewer, or the human;
- a `usage` field on each builder run and each review, with the tokens used where the host reported them, so a
  milestone's cost can be read from the record.

It also holds the module's design review, against the design as it was then.

A milestone is Done only when the record file says so, under the key `done`, for the items as they are now. A
`done` in the done-when file is not enough, and that is what makes the done-when file safe for agents to edit.

In a repository that has never had a record file, the script takes each module as it stands the first time it
reads it, so work built before the project used these skills counts as Done. After that, a module with no record
file is new: nothing in it is Done, and its design needs a review.

## Who changes what, and when

Only one kind of agent changes each field at any time, and the hand-overs happen in this order.

| Change | Who | When |
|---|---|---|
| `status` from `not_started` to `in_progress` | Builder | It starts the milestone. |
| An item's `builder_result` and `evidence` | Builder | While building. `pass` means it has proof from the item's target. |
| `status` from `in_progress` to `ready_for_review`, with the Ready for Review record | Script | Every item is `pass` with evidence, the builder has merged the work and ended with `DONE`, and the test command and every item's check pass when the script runs them in its own clean checkout of the main branch. The script writes the record and the status in one commit, on a milestone that needs a reviewer. |
| `status` from `in_progress` to `done`, with `done` in the record file | Script | The same, on a milestone that needs no reviewer. |
| `status` from `ready_for_review` or `done` back to `in_progress` | Script | The main branch says Ready for Review or Done without the script's record, as a builder set it before 2.1.0, and the script's checks fail. |
| `status` to `blocked`, with `blocked` | Script | The builder ends with `BLOCKED` or `NEEDS_CONTEXT`. |
| `status` from `blocked` to `in_progress` | Lead, with the `unblock` command, or the script when it records Human Feedback | Whatever blocked it is resolved. |
| An item's `verdict` and `review` | Reviewer | Reviewing a milestone that is Ready for Review. Every item gets a result. |
| `status` from `ready_for_review` to `done` | Reviewer | Every result is `pass`, and no Must Fix lies outside the items. |
| `status` from `ready_for_review` to `in_progress`, and `findings` | Reviewer | Any result is `fail` or `could_not_judge`, or a Must Fix lies outside the items. Every Must Fix is a finding, and every item that didn't pass is named by one. A Suggestion never is. |
| `findings` cleared | Script | The review passes. |
| 1 more in `failed_reviews`, 1 more in `failed_reviews_with_repeat` if a finding repeated, and `repeat` on each finding | Script | After a failed review. A count a reviewer or planner writes is put back. |
| `builder_result` back to `open` and `evidence` cleared, on the items that didn't pass | Script | After a failed review, so the next attempt is proved again. |
| `status` to `blocked`, with `reason: too_many_failed_reviews` | Script | After a failed review, when the escalation steps below reach Too Many Failed Reviews. |
| The planner's fields | Planner | A re-plan of a milestone that is Waiting: For Diagnosis, a revision after a design review, or a change the human asked for. A milestone split off from a re-planned one starts with its `diagnoses` count. The script saves the new items as the approved ones and clears the old proof. |
| `failed_reviews` and `failed_reviews_with_repeat` back to 0, 1 more in `diagnoses`, `status` to `not_started` | Script | A planner's plan has changed the items of a milestone that was Waiting: For Diagnosis. Done once, whatever the planner wrote in those fields. |
| `failed_reviews` and `failed_reviews_with_repeat` back to 0, 1 more in `diagnoses`, and `status` to `blocked`, with `reason: too_many_failed_reviews`, if the human has to decide | Script | A planner kept the plan and ended with `KEEP`. |
| The planner's fields | Human | `human scope`, when the human changes what is wanted. The script sets `failed_reviews`, `failed_reviews_with_repeat` and `diagnoses` back to 0, and a milestone that was Waiting: For Diagnosis, or Blocked with Too Many Failed Reviews, back to `not_started`. |
| `status` to `done` with no review, back to `ready_for_review` for a new review, or from Blocked with Too Many Failed Reviews to `in_progress` | Human | `human accept`, `human rereview` or `human reopen`. A reopen sets `failed_reviews`, `failed_reviews_with_repeat` and `diagnoses` back to 0. |

A builder leaves `ready_for_review` and `done` to the script. If a builder set one, the main branch would say a
milestone had passed checks that hadn't run yet, and other builders rebase onto the main branch. So `merge` refuses
a builder's commits that set either status, and a milestone that is Ready for Review without the script's record is
checked by `run` rather than reviewed.

Reviewers and planners don't commit their own changes to these files. The script compares what they changed with
this table, and then either commits and merges all of the changes or rejects all of them.

`could_not_judge` counts as a fail, because a milestone nobody could check is not Done. The review says what evidence
would settle the item, and the builder's next attempt has to produce it.

## When a review fails

These are the escalation steps, and they are written down only here. The `next` command, and the `next` field in
a review's result, apply them.

The steps follow two counts. `failed_reviews` counts every failed review. `failed_reviews_with_repeat` counts
those that repeated a finding an earlier review raised, which means fixes aren't holding. The first row that
applies is the step, and a result names it under `escalation`.

| Counts | What happens | `escalation` |
|---|---|---|
| `failed_reviews_with_repeat` at 4, or `failed_reviews` at 6 | The milestone is Waiting: For Diagnosis. A planner reads every review and decides why it keeps failing. The `cause` says which count it reached: "a finding keeps coming back", or "reviews keep finding something new". A milestone gets one diagnosis. If it has had it, the script sets the milestone to Blocked: Too Many Failed Reviews, and it waits for the human. | `diagnosis`, or `too_many_failed_reviews` |
| `failed_reviews_with_repeat` at 3, or `failed_reviews` at 3 | A new builder session starts, with only the files and the review. | `new_builder_session` |
| Any other failed review | The same builder carries on in the same session, with the review. | `same_builder` |

A review shows what one reviewer tried, and the next reviewer starts again from the items. So after any failed
review the milestone is finished when every item is true as it is written. Clearing the places a review named
doesn't by itself make it so.

A diagnosis ends in one of two ways. In a Re-plan, the planner changes the milestone's items. In Plan Kept, the
planner leaves them as they are and says who has to act. A builder who keeps breaking something gets a new
session with the planner's reasons. A reviewer whose findings go beyond the items is overruled: the next reviewer
is told to judge the items as written. A decision only the human can make sets the milestone to Blocked: Too
Many Failed Reviews, with the planner's reasons. Either way, it is the milestone's one diagnosis.

The two counts of failed reviews start again from 0 after a diagnosis, `human scope` or `human reopen`. Reviews
before that no longer count as earlier reviews, so a finding they raised isn't a repeat. The human's two
commands also set `diagnoses` back to 0, so the milestone can be diagnosed once more.

When the script sets a milestone to Blocked: Too Many Failed Reviews, its message to the human lists what failed
in each review, and offers three answers as equals: accept the milestone as it is, change its scope, or reopen it
for another try.

Each step exists because the one before it has already been tried. Repeating a step would spend the next attempt
on something already ruled out.

## What makes a good item

This section is for the planner. A good item is something you would refuse to call the milestone Done without. Its
proof would catch a convincing fake, and it depends only on this module and on what exists when its milestone ends. An
item whose proof needs a later milestone's work can't pass until then, and it holds up the milestone it sits in. Put
it in the later milestone. Keep an inspected item small, with one quality in each, so a failure points at something
specific. A milestone may have many items, as long as it delivers one outcome.

Keep each item short: one thing that must be true, and the proof that would show it. Say what will be observed,
and leave it to the builder to arrange the observation. An item that scripts its own procedure breaks the first
time the builder learns something the plan didn't know, and each break costs a re-plan and another design review.

Choose each proof on purpose, because `inspect` and `ask` are what bring in a reviewer.

- Use `ask` for something only reading can settle. Ask one question with a real answer, within the range the
  design names. "Would any violation fail this lint?" has no last answer, so each review finds one more corner and
  the milestone never finishes.
- If the builder will write the test that a `check` runs, add an `ask` that has the reviewer read that test,
  because a test written by the agent it grades proves little.
- A milestone the builder can do comfortably, proved by checks the builder didn't write, can be Done on those
  checks alone.
