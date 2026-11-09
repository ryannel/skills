# The plan and the done-when file

Contents:
- [`<MODULE>-PLAN.md`](#module-planmd)
- [`<MODULE>-DONE.json`](#module-donejson)
- [The acceptance record](#the-acceptance-record)
- [Who changes what, and when](#who-changes-what-and-when)
- [When a review fails](#when-a-review-fails)
- [What makes a good item](#what-makes-a-good-item)

## `<MODULE>-PLAN.md`

Rewrite this in place, so it always describes the present. People and agents read the status lines first, so keep
them short. The `Reviews:` line holds only the latest review. Earlier ones go in the log, because a status line that
keeps growing stops being read.

```markdown
# <Module> plan
Reviews: <the latest review: what @ revision, verdict, link>
Milestone: M2 <name>
Now: <what is happening> (since <date>)
Next: <what follows>
Blocked: none

## M1 <name>: done
## M2 <name>: in progress
- [ ] <work item: what exists or passes when it's done>

## Log
- <date> <what changed and why>
```

## `<MODULE>-DONE.json`

This file decides when a milestone is done. It's JSON because a script reads it, and because agents are less likely
to rewrite a whole JSON file than a page of prose.

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

The planner writes what each milestone asks for:
- `statement` says what must be true, in words a reviewer can judge.
- `check`, `inspect` and `ask` are how the item is proved. Use any mix, but at least one ([proofs](proofs.md)).
- `target` is one of the profile's targets, or `proxy:<what it stands in for>` when you're using a stand-in.
- `lock` (optional) names an exclusive resource the item's `check` needs, such as `gpu`. The loop takes that lock
  when it reruns the check.
- `attended` (optional) says what a person or physical hardware has to do for the item, such as "plug in the
  iPhone and approve the prompt". Builders do every other item first and then report these together, so the owner
  can do them in one sitting instead of being interrupted once per item.
- `bar` is the profile's quality bar, made specific to this milestone, in words. It's what inspection is judged
  against, so name real examples.
- `needs` (optional) lists milestones that must be accepted before this one starts, in another module: `"AUTH:M1"`.
  Milestones within a module run in order anyway, so a need on an earlier one here adds nothing, and a need on a later
  one, or on itself, can never be met, so the loop reports it as an error. So does a need on a parked milestone, or a
  cycle of needs across modules.

The loop pins those fields. Only a planner turn the loop ran, or the owner's `scope` command, changes them, because a
builder who could edit them could pass anything.

The others record what happened:
- `status` is the builder's claim, `open` or `pass`, and `evidence` is where the builder's proof is.
- `verdict` is the reviewer's judgement, `pass`, `fail` or `cant_tell`, and `review` links to the review file.
- `state` is `open`, `in_progress`, `claimed`, `done`, `blocked` or `parked`. A blocked milestone has a `blocked`
  field saying what would unblock it.
- `fails` counts failed reviews since the last re-plan, and `replans` counts re-plans.

A milestone needs review if any of its items has `inspect` or `ask`, or if it's the module's last milestone. That
final review reads the whole module, which is how work proved only by checks still gets a reviewer's eye. Other
milestones close on their checks alone.

## The acceptance record

Next to each done-when file, the loop keeps `<MODULE>-ACCEPTED.json`. Only the loop writes it, in commits marked
`Orchestrate-Loop: yes`, and it's committed so every worktree, clone and lead reads the same one. For each milestone
it holds the hash of the definitions last authorised (by a planner turn or the owner), the commit the loop checked and
the tip it ran the checks on, every review, and whether the milestone was accepted, and by what: its checks, a
reviewer, or the owner. It also holds the module's design review, against the design as it was.

A milestone is finished only when the record accepts it with its current definitions. A `done` state in the
done-when file isn't enough on its own, which is what makes the file safe for agents to edit. A module with no record
yet is taken as it stands the first time the loop reads it.

## Who changes what, and when

Only one role changes each field at any one time, and the hand-offs happen in this order.

| Change | Who | When |
|---|---|---|
| `state` open → in_progress | Builder | It starts the milestone. |
| items' `status` and `evidence` | Builder | While building. `pass` means it has proof from the item's target. |
| `state` in_progress → claimed | Builder | Every item is `pass` with evidence, the checks pass, and the work is integrated, on a milestone that needs review. |
| `state` in_progress → done | Builder | The same, on a milestone that doesn't need review. The loop reruns the checks before it accepts it. |
| `state` → blocked, with `blocked` | Loop | The builder reports `BLOCKED`. |
| `state` blocked → open | Lead, through the loop | Whatever blocked it is resolved (`unblock`). |
| items' `verdict` and `review` | Reviewer | Reviewing a claimed milestone. Every item gets a verdict. |
| `state` claimed → done | Reviewer | Every verdict is `pass`, and nothing outside the items fails the milestone. |
| `state` claimed → in_progress, and 1 more `fails` | Reviewer | Any verdict is `fail` or `cant_tell`, or a blocking defect outside the items fails it (advisory findings never do). |
| items' `status` back to open, `evidence` cleared, on items that didn't pass | Loop | After a failed review, so the next claim is verified again. |
| `state` → parked | Loop | After a failed review, when the ladder below says `park`. |
| the definitions, `fails` back to 0, 1 more `replans`, `state` → open | Planner | A re-plan, all in one commit. Milestones split from a re-planned one start with its `replans` count. The loop records the new definitions and clears old proof. |
| the definitions, without spending a re-plan | Owner | `owner scope`, when the owner changes what's wanted. |
| `state` → done without review, back to claimed for a re-review, or parked → open | Owner | `owner accept`, `rereview` or `unpark`. |

Reviewers and planners don't commit their own changes to these files. The loop checks what they changed against the
table, then commits and integrates it, or rejects all of it.

`cant_tell` counts as a fail, because a milestone nobody could check isn't done. The review says what evidence would
settle it, and the builder's next attempt has to produce that evidence.

## When a review fails

This is the one place the ladder is written down; `LOOP next` and the review result's `next` apply it.

| Failed reviews (`fails`) | What happens |
|---|---|
| 1 or 2 | The builder fixes the findings in the same session. |
| 3 | A fresh builder session starts, with only the files and the review. |
| 4 | The plan is wrong: the planner re-plans the milestone. |
| 4 again, after a re-plan | The loop parks it for the owner. |

Each step exists because the one before it has been tried: repeating it would spend the next attempt on something
already ruled out.

## What makes a good item

A good item is something you'd refuse to call the milestone done without. Its proof would catch a convincing fake,
and it only depends on this module. Keep inspection items small, one quality each, so that when one fails it points
at something specific. A milestone can have lots of items, as long as it delivers one outcome.
