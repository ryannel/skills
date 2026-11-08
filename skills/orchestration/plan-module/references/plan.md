# The plan and the done-when file

The plan turns the design into work anyone can follow. The done-when file decides a milestone's close, mechanically
where possible: `scripts/agent_loop.py`, the evaluator and the owner all read it.

## The plan: `<plans>/<MODULE>-PLAN.md`

- **Milestones are outcomes a user could observe,** such as "a new user signs up, verifies email and lands on an empty
  dashboard on mobile Safari", not components such as "the auth service".
  - The riskiest behaviour comes first, at shipped quality.
  - A milestone that needs more than about three done-when items is usually two milestones.
- **Work items** are the generator's to shape. Each says in one line what exists or passes when it's done.
- **Status lines** are plain lines tools read: `Milestone:` the one in progress; `Now:` what's happening, and since
  when; `Next:` what follows; `Blocked:` a blocker probed directly, with what would unblock it. Use
  `## M<n> <name>: <state>` headings.
- **Rewrite in place,** so the plan reads as current. A one-line log at the end records meaningful changes.

```markdown
# <Module> plan

Design: <plans>/<MODULE>.md · Done-when: <plans>/<MODULE>-DONE.json
Reviews: <what was reviewed @ revision, verdict>
Milestone: M2 <name> · Updated: <YYYY-MM-DD HH:MM UTC>
Now: <what is happening> (since <date>)
Next: <what follows>
Blocked: none

## M1 <name>: done
## M2 <name>: in progress
Work:
- [x] ...
- [ ] ...

## Log
- <date> <what changed and why>
```

## The done-when file: `<plans>/<MODULE>-DONE.json`

JSON, so agents edit fields rather than rewriting prose. Who writes what:
- **Generator:** items' `status` and `evidence`; the milestone's `state`, set to `in_progress` on starting and to `done`
  when every item passes and `review` is `false`.
- **Evaluator:** items' `status`, adding its review link to `evidence`; `state: done` on a pass; `fails` on a fail.
  `agent_loop.py next` turns `fails` into the escalation.
- **Lead:** `state: parked` when the loop says park.
- **Planner:** everything else, including `replans`, increased by one on each re-plan.

```json
{
  "module": "ONBOARDING",
  "milestones": [
    {
      "id": "M2",
      "name": "A new user signs up and lands on an empty dashboard",
      "state": "open",
      "review": true,
      "fails": 0,
      "replans": 0,
      "bar": "Would pass in a well-reviewed consumer app: sign-up as quick and calm as Linear's, empty state as clear as Things', judged in words, not against screenshots.",
      "items": [
        {
          "id": "M2.1",
          "statement": "Sign-up with a valid email reaches the dashboard in under three screens; invalid input is rejected inline",
          "proof": "oracle",
          "check": "npx playwright test e2e/signup.spec.ts",
          "target": "web-chrome",
          "status": "open",
          "evidence": ""
        },
        {
          "id": "M2.2",
          "statement": "Every step is readable and tappable at 375 px wide with no layout shift as fields validate",
          "proof": "inspection",
          "check": "scenario signup-mobile: screenshot sequence of each step and each validation state",
          "target": "web-mobile-safari",
          "status": "open",
          "evidence": ""
        }
      ]
    }
  ]
}
```

Fields:
- **`state`:** `open`, `in_progress`, `done` or `parked`.
- **item `status`:** `open`, `pass`, `fail` or `cant_tell` (the evaluator's "can't tell").
- **The inspection list** of a milestone is its `inspection` items: each statement is one observable quality, and its
  `check` says which scenario and captures show it.
- **`review`:** `true` when an evaluator must close the milestone: visual or interaction milestones, milestones that
  change a shared contract, and the module's last milestone. Otherwise the oracle closes it.
- **`proof`:** `oracle` (a command whose exit status decides), `inspection` (an inspection-list item judged on the
  running product by the evaluator), or `review` (a non-visual evaluator judgement, such as a code or contract review).
- **`target`:** a target named in the profile, or `proxy:<what it stands in for>`.
- **`bar`:** the profile's quality bar made specific to this milestone, naming the shipped examples it rests on. Not a
  reference image. Golden screenshots are regression tripwires, never done-when items.

What makes a good item:
- **Something you'd genuinely refuse to call the milestone done over.**
- **A check that would catch the plausible wrong substitute,** such as a spinner standing in for real loading, or a
  canned response standing in for the real query.
- **Only behaviour this module's mechanisms produce.** Anything that hinges on another module uses a fixed setup or
  moves to the milestone that integrates them.
- **No invented cost targets.** A real target from the purpose doc or the owner (Core Web Vitals, an SLO, a frame
  budget) can be an item; otherwise cost appears as recorded measurements and tripwires ([cost](cost.md)).

## Changing a milestone

Splitting, re-scoping or parking happens in the open: edit the plan and done-when file and log why. Update the design
if the change alters what the module must do. A milestone whose meaning changes gets a review of the change, and work
carries on while it runs.
