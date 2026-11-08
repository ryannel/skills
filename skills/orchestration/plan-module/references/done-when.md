# The plan and the done-when file

## `<MODULE>-PLAN.md`

Rewrite this in place, so it always describes the present. Scripts read the status lines, so keep their shape.

```markdown
# <Module> plan
Reviews: <what was reviewed @ revision, verdict>
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

This file decides when a milestone is done. It's JSON because agents are less likely to rewrite a whole JSON file
than a page of prose, so each agent changes only its own fields.

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
          "check": "npx playwright test e2e/signup-mobile.spec.ts",
          "inspect": "screenshot sequence of each step and validation state at 375 px",
          "target": "web-mobile-safari",
          "status": "open",
          "evidence": ""
        }
      ]
    }
  ]
}
```

What the fields mean:
- `state` is `open`, `in_progress`, `done` or `parked`.
- `status` is `open`, `pass`, `fail` or `cant_tell`.
- `check`, `inspect` and `ask` are how the item is proved. Use any mix, but at least one ([proofs](proofs.md)). If
  any item has `inspect` or `ask`, a reviewer closes the milestone. Contract changes and a module's last milestone
  should always get a review, so give them an `ask` item.
- `target` is one of the profile's targets, or `proxy:<what it stands in for>` when you're using a stand-in.
- `bar` is the profile's quality bar, made specific to this milestone, in words. It's what inspection is judged
  against, so name real examples.

## Who writes what

Each field has exactly one writer, so agents never overwrite each other's work.

| Who | Writes |
|---|---|
| Builder | Items' `status` and `evidence`. The milestone's `state`: `in_progress` when it starts, `done` when everything passes and no item has `inspect` or `ask`. |
| Reviewer | Items' `status`, plus a link to the review in `evidence`. `state: done` on a pass, and 1 more `fails` on a fail. |
| Lead | `state: parked` |
| Planner | Everything else, including 1 more `replans` on each re-plan |

## What makes a good item

A good item is something you'd refuse to call the milestone done without. Its proof would catch a convincing fake,
and it only depends on this module. Keep inspection items small, one quality each, so that when one fails it points
at something specific. A milestone can have lots of items, as long as it delivers one outcome.
