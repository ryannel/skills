# The plan and the done-when file

## `<MODULE>-PLAN.md`

Rewrite it in place so it always reads as current. Tools read the status lines.

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

This file decides when a milestone is closed. It's JSON so agents edit fields rather than rewriting prose.

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

- **`state`:** `open`, `in_progress`, `done` or `parked`.
- **`status`:** `open`, `pass`, `fail` or `cant_tell`.
- **`check`, `inspect`, `ask`:** how the item is proved, in any mix, with at least one. See [proofs](proofs.md). Any
  `inspect` or `ask` means the evaluator closes the milestone. Give contract changes and a module's last milestone
  an `ask` item, so they get a review.
- **`target`:** a target from the profile, or `proxy:<what it stands in for>`.
- **`bar`:** the profile's quality bar made specific to this milestone, in words.

## Who writes what

Each field has one writer, so agents never overwrite each other's work.

| Who | Writes |
|---|---|
| Generator | Items' `status` and `evidence`; `state` (`in_progress`, or `done` when every item passes and none has `inspect` or `ask`) |
| Evaluator | Items' `status`, adding a review link to `evidence`; `state: done` on a pass; `fails` + 1 on a fail |
| Lead | `state: parked` |
| Planner | Everything else, including `replans` + 1 on a re-plan |

A good item is something you'd refuse to call the milestone done without. Its proof would catch the plausible wrong
substitute, and it depends only on this module's mechanisms. Inspection items should be granular: one observable
quality each, so a fail points at something specific. A milestone can have many items, as long as it delivers one
outcome.
