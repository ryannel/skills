# Dogfood 2: orchestrate 2.10.1 (installed copy), 23 Nov 2026

Projects: wordfreq M2 (carried on from dogfood 1) and a new csvstat (one module, two milestones). Claude builders
and planners on claude-sonnet-5-5 medium; Codex reviewers on gpt-6.2-sol medium. Both reached Done in about 55
minutes. Every launch ran on the configured model and effort.

## Main finding

Milestone reviews now stay within the brief: 3 of 5 passed (1 of 8 in dogfood 1), at most 2 reviews per milestone
(6 before). Passing re-reviews checked the earlier Must Fix first and raised new defects as Suggestions.

Design reviews still grow: csvstat's raised 9, then 5 Must Fix, and the design was approved at the round limit. Most
were fair proof weaknesses (checks ignoring exit status, GNU-only `timeout`, a pytest check any test passes). One
thread went beyond the brief: float overflow and exact summation, raised against an assumption the user had agreed,
which pushed Shewchuk summation into the design and later failed M2.6 on `1e308` inputs.

A smaller pattern: CSVSTAT M1 failed on error handling that M2.4 already schedules.

## Fixed after this run (2.11.0)

- reviewer/tasks/design.md: the range the brief names is what "How it will be judged" describes, not every value a
  type allows; a finding against an agreed assumption or decision is a Suggestion.
- reviewer/tasks/milestone.md: a defect a later milestone's item covers is a Suggestion.
- lead stage 4: a Must Fix that asks for more than the brief goes to a planner or the user, not back to the builder.
- `runs` crashed with KeyError 'loop' on an unregistered loop.
- Setup command note: `none` until the project has the files it installs from (the first plan failed to merge on
  a setup command for a project not yet built).

## Not fixed (minor)

- `settings --set Builders` returns no `next` (the supervisor now starts the build, so none is needed on hosts it can
  wake).
- A REFUSED `plan` still carries `ran_on`.
- `run` sent the lead to `adopt` a record already on main (adopt returned NOTHING).
- `report` lists 3 planner tasks beside 6 planner turns.
- `watch`'s signs don't include `flow`'s churn sign.

## Escalation, flow, report

Behaved as their help says. Both new flow signs fired on wordfreq; churn fired on csvstat; low-pass stayed quiet at
2 of 4. Diagnosis wasn't reached, so that path is untested in practice.

## Cost

csvstat: 16 turns, $2.13 Claude list price plus Codex 678k in / 8.1M cached / 112k out; planning took 13 of 52
minutes. Merges and tests cost nothing.
