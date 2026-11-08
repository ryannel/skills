# Testing a skill

Contents:
- [Test cases](#test-cases)
- [Running them](#running-them)
- [Grading](#grading)
- [Does the description trigger?](#does-the-description-trigger)

## Test cases

Each test case is a folder under `evals/` in the skill. This is the layout `claude plugin eval` reads, so anyone with
Claude Code can rerun your tests later from a terminal or in CI. You don't need the CLI to use them, though. They're
plain files you write and read yourself.

```
my-skill/evals/flags-negative-quantity/
├── prompt.md      settings, then the prompt exactly as a user would type it
├── case.yaml      the case name, and what a good result looks like
├── graders/       one checkable statement per file
└── files/         input files, if the test needs any
```

The folder name says what's being tested, in lowercase with hyphens. Avoid `results`, `mocks`, `files`, `true`,
`false` and `null`, which the CLI treats specially.

`prompt.md` starts with a settings block, then the prompt:

```markdown
---
tags: [my-skill]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

ok so my boss sent me Q4 sales final v2.xlsx and wants a profit margin column. revenue is C, costs are D i think
```

The settings block ends at the first `---`, so keep free text out of it. An unknown key there stops the case loading.

`case.yaml` holds the schema version (in quotes, or it's read as a number), the name, and what success looks like:

```yaml
schema_version: "1.1"
name: flags-negative-quantity
expected_outcome: |
  Adds a margin column computed as (C-D)/C and flags the two rows with negative quantities.
```

Each grader is a file like `graders/01-adds-margin-column.md`, numbered to keep the order:

```markdown
---
type: llm
focus: trace
weight: 1
---

The output spreadsheet has a margin column equal to (revenue - cost) / revenue
```

A case with no graders won't load. Until you've written real ones, use a single placeholder whose body is "The result
matches this description: <the expected outcome>". Don't grade the placeholder yourself.

If a test needs input files, put them in `files/`, end the prompt with a line like `Input files: orders.csv`, and add
a `place-files.sh` script that copies `files/` into the working directory. Then name the script in `case.yaml` under
`context: scaffold_script: place-files.sh`.

## Running them

For each case, launch two fresh subagents in the same turn, so they finish together. One gets the skill's path and the
prompt. The other gets the same prompt, with no skill if this is a new skill, or a snapshot of the old version if
you're improving one. Take the snapshot before you edit. Save each run's outputs in a workspace folder next to the
skill, such as `my-skill-workspace/iteration-1/<case>/with_skill/` and `.../without_skill/`. Keep the same folder names
in later iterations, so it's easy to compare one round with the next.

When a run finishes, note its time and token count from the completion notice. That's the only moment you get them,
and they tell you whether the skill costs more than it helps.

`claude plugin eval . --allow-tools Write,Edit,Bash` runs the same cases from the skill's folder (add `--scaffold` if
any case has input files). Those are real model runs, so offer it to the person rather than starting it yourself.

## Grading

Grade each checkable statement as passed or failed, with the evidence: the line in the output, or the step in the
transcript. Write a script for anything a script can check, like a number, a file's existence or a format. It's
faster, it doesn't drift, and you can reuse it next round.

Good statements are about the result, not the process. They're specific enough that two people would agree. "The
summary states total revenue of 693.5" is a good one. "The summary is good" isn't.

Then look for patterns the pass rate hides. A statement that passes with and without the skill isn't telling you
anything, so replace it. A case whose result swings from run to run may be flaky. If the skill wins on quality but
doubles the time, say so.

Show the person every result before you change anything. Their judgement of the outputs matters more than your
grades, especially for writing, design or advice.

## Does the description trigger?

Write about twenty prompts, around half that should fire the skill and half that shouldn't. Make them realistic, with
file names, context, typos and casual phrasing. The useful ones that shouldn't fire are near misses: requests that
share words with the skill but need something else. "Write a fibonacci function" tells you nothing about a PDF skill.
"Extract the table from this scanned invoice into a spreadsheet" might.

Keep the prompts substantial. Agents only reach for a skill when the task is more than they'd handle alone, so a
one-line request may not fire even a perfect description.

Show the list to the person before using it, because bad test prompts produce a bad description. Then test each
prompt in a fresh subagent that sees the installed skill list, and note whether it loads the skill. Change the
description and test again, judging each version on prompts you didn't tune it against, so you don't fit it to the
test.

Anthropic's own skill-creator automates this loop, but its scripts start a `claude -p` process for every prompt, and
those are billed through the API rather than a subscription. Check how the person pays before using them.
