# Round 1 results

10 November 2026. Three requests, each run once with the new draft and once with the published skill-creator.
One run of each side is a smoke test: it shows whether the draft works at all, and cannot show a small difference.

## What was compared

- **New:** the draft in `workbench/skill-creator/skill-creator/` as it stood before the edits listed under
  [What changed afterwards](#what-changed-afterwards).
- **Old:** `skills/skill-creator/` at commit `4dee0ab`.
- **Model:** Claude Fable 5.2, in fresh subagents of one Claude Code 2.1.319 session. Effort was the session's and
  was not recorded. Not run on Claude Opus 5.5, GPT-6 Astra or GPT-6.1 Sol.
- **Cases:** [workflow-to-skill](../../evals/workflow-to-skill/), [modernise-old-skill](../../evals/modernise-old-skill/)
  and [rule-that-needs-a-hook](../../evals/rule-that-needs-a-hook/). The 32 checks were written before any run.
- **Each run was told** that the person could not answer questions, and not to start test runs or subagents. So
  the testing and review parts of both skills were not exercised.

## Grades

A fresh agent graded each pair as A and B without being told which was which. Its tables, with the evidence for
every check, are in [grading](../grading/).

| Case | Checks | New | Old | Which output the grader would hand to the person |
|---|---|---|---|---|
| workflow-to-skill | 11 | 11 | 11 | Old, narrowly |
| modernise-old-skill | 14 | 14 | 14 | New, narrowly |
| rule-that-needs-a-hook | 7 | 7 | 6, and 1 unclear | New |
| Total | 32 | 32 | 31, and 1 unclear | |

In `grading/`, A is the old skill in workflow-to-skill, and the new draft in the other two cases.

The checks do not separate the two versions. Every check but one passed on both sides, so these checks show that
the draft did not break anything, and nothing more.

## What the grader found outside the checks

- **workflow-to-skill, new:** the skill it wrote says "That needs no go-ahead, and neither does any other step
  here". The person's notes waived asking only for the tag push. The old skill's output kept the waiver to the
  tag, and also covered a failed CI run and a failed publish job.
- **modernise-old-skill, new:** the skill it wrote states "Running it again after a failure is safe on
  migrate-tool 3.2" as a fact, when the run had only guessed it. It also dropped one old step without listing it.
- **modernise-old-skill, old:** it narrowed "never touch production" to "don't run a migration against
  production" without telling the person.
- **rule-that-needs-a-hook:** both versions said a skill's text can't guarantee the rule, and both built a hook.
  The new draft's hook stops a command it can't work out. The old skill's hook lets it through: the grader got a
  commit onto main past it with `git checkout - && git commit`.
- **Test artefact:** one new-draft reply says "you asked for no test runs". That came from this test's own
  instruction to the run, not from the request.

## Cost

| Case | New: tokens, time | Old: tokens, time |
|---|---|---|
| workflow-to-skill | 93,036, 127 s | 100,383, 260 s |
| modernise-old-skill | 112,426, 257 s | 96,707, 224 s |
| rule-that-needs-a-hook | 197,384, 979 s | 217,812, 815 s |
| Total | 402,846, 1,362 s | 414,902, 1,299 s |

The grading run used 181,114 tokens.

## Leaks

Each run's transcript was searched. No run called the Skill tool, and each run read only its own version's
folder. The installed `skill-creator` and `prompting-agents` plugins could not be turned off for the subagents, so
each run was told to use no other skill. Neither version's folder held test cases.

## What changed afterwards

Three lines were added to the draft's `SKILL.md` for the findings above, and are untested:

1. When saying what the reader may do without asking, name only actions the person or the project has cleared.
2. Write down only what the source supports, and put a guess to the person as a question.
3. When handing back a changed skill, list each thing removed and why.

Two host facts were corrected after being checked on this machine: `claude plugin validate` accepts a skills
folder or a plugin and refuses a single skill folder, and Claude Code 2.1.319 reads an unquoted description with
a colon in it.

## What the person said

Not yet reviewed by the person.
