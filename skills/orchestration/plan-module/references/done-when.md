# The plan and the done-when file

Contents:
- [`<MODULE>-PLAN.md`](#module-planmd)
- [`<MODULE>-DONE.json`](#module-donejson)
- [Who changes what, and when](#who-changes-what-and-when)
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
- `bar` is the profile's quality bar, made specific to this milestone, in words. It's what inspection is judged
  against, so name real examples.
- `needs` (optional) lists milestones that must be `done` before this one starts: `"M1"` in this module, or
  `"AUTH:M1"` in another. Milestones within a module run in order anyway, so list only what isn't already implied.

The loop pins those fields. If they change during a build, it rejects the claim, because a builder who could edit
them could pass anything. Only a re-plan changes them.

The others record what happened:
- `status` is the builder's claim, `open` or `pass`, and `evidence` is where the builder's proof is.
- `verdict` is the reviewer's judgement, `pass`, `fail` or `cant_tell`, and `review` links to the review file.
- `state` is `open`, `in_progress`, `claimed`, `done` or `parked`.
- `fails` counts failed reviews since the last re-plan, and `replans` counts re-plans.

A milestone needs review if any of its items has `inspect` or `ask`, or if it's the module's last milestone. That
final review reads the whole module, which is how work proved only by checks still gets a reviewer's eye. Other
milestones close on their checks alone.

## Who changes what, and when

Only one role changes each field at any one time, and the hand-offs happen in this order.

| Change | Who | When |
|---|---|---|
| `state` open → in_progress | Builder | It starts the milestone. |
| items' `status` and `evidence` | Builder | While building. `pass` means it has proof from the item's target. |
| `state` in_progress → claimed | Builder | Every item is `pass` with evidence, the checks pass, and the work is integrated, on a milestone that needs review. |
| `state` in_progress → done | Builder | The same, on a milestone that doesn't need review. Under `/build`, the loop reruns the checks before anyone believes it. |
| items' `verdict` and `review` | Reviewer | Reviewing a claimed milestone. Every item gets a verdict. |
| `state` claimed → done | Reviewer | Every verdict is `pass`, and nothing outside the items fails the milestone. |
| `state` claimed → in_progress, and 1 more `fails` | Reviewer | Any verdict is `fail` or `cant_tell`, or a defect outside the items fails it. |
| `state` → parked | Lead | The escalation says `park`. |
| the definitions, `fails` back to 0, 1 more `replans`, `state` → open | Planner | A re-plan, all in one commit. Milestones split from a re-planned one start with its `replans` count. |

`cant_tell` counts as a fail, because a milestone nobody could check isn't done. The review says what evidence would
settle it, and the builder's next attempt has to produce that evidence.

## What makes a good item

A good item is something you'd refuse to call the milestone done without. Its proof would catch a convincing fake,
and it only depends on this module. Keep inspection items small, one quality each, so that when one fails it points
at something specific. A milestone can have lots of items, as long as it delivers one outcome.
