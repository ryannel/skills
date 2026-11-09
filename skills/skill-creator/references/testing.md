# Testing a skill

Contents:
- [Test cases](#test-cases)
- [Keeping the runs apart](#keeping-the-runs-apart)
- [Running them](#running-them)
- [Grading](#grading)
  - [When another agent acts on the output](#when-another-agent-acts-on-the-output)
- [The results record](#the-results-record)
- [Does the description trigger?](#does-the-description-trigger)
- [Running the cases with claude plugin eval](#running-the-cases-with-claude-plugin-eval)

## Test cases

Each test case is a folder under `evals/` in the skill. The layout is the one `claude plugin eval` reads, so the same
cases can be run headless later. You don't need the CLI to use them, though. They're plain files you write and read
yourself.

```
my-skill/evals/flags-negative-quantity/
├── prompt.md      settings, then the prompt exactly as a user would type it
├── case.yaml      the case name, what a good result looks like, and any context
├── graders/       one checkable statement per file
└── fixtures/      input files, if the test needs any
```

The folder name says what's being tested, in lowercase with hyphens. Avoid `results` and `mocks`, which the CLI
uses for its own folders.

`prompt.md` starts with a settings block, then the prompt:

```markdown
---
tags: [my-skill]
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill]
---

ok so my boss sent me Q4 sales final v2.xlsx and wants a profit margin column. revenue is C, costs are D i think
```

The settings block ends at the first `---`, so keep free text out of it. An unknown key there stops the case loading.
`allowed_tools` takes only read-only tools; a run that needs to write or run commands gets them from `--allow-tools`
on the command line, and listing `Write` or `Bash` here does nothing.

`case.yaml` holds the schema version (in quotes, or it's read as a number), the name, and what success looks like.
Input files go in a fixtures folder that the run can read, listed under `context.add_dirs`:

```yaml
schema_version: "1.1"
name: flags-negative-quantity
expected_outcome: |
  Adds a margin column computed as (C-D)/C and flags the two rows with negative quantities.
context:
  add_dirs: [fixtures]
```

Each run starts in an empty folder. If the files have to be in the working folder itself, use
`context.scaffold_script: place-files.sh` instead, with a Bash script in the case folder that copies them in.

Each grader is a file like `graders/01-adds-margin-column.md`, numbered to keep the order. Grade the thing the skill
made, not the agent's account of it. This grader reads the produced file:

```markdown
---
type: llm
focus: { source: file, path: q4-sales-margin.csv }
weight: 1
---

The margin column equals (revenue - cost) / revenue on every row
```

`focus: trace` shows a judge only the first and last twelve messages, so a confident final message can pass while the
file is wrong. Use it for questions about how the agent worked, not what it made. Other grader types are `regex`,
`file_exists`, `tool_used` and `tool_order`. A regex over a file's contents is the most reliable way to check an exact
value.

A case with no graders won't load. Until you've written real ones, use a single placeholder whose body is "The result
matches this description: <the expected outcome>", and treat the case as unscored. Don't count it in any result.

## Keeping the runs apart

The comparison only means something if the only difference between the two runs is the skill. Four things leak:

1. An installed copy of the skill. A subagent can invoke any skill it can see through the Skill tool, even one it
   wasn't given. Keep the draft outside the skill folders until testing is done. For a skill that's already installed,
   turn it off for the baseline: in Claude Code, set `"skillOverrides": {"<name>": "off"}` in
   `.claude/settings.local.json` for that run (written 8 November 2026; host version not recorded). Plugin skills are
   managed through `/plugin` instead. In Codex, disable the skill in its skills settings.
2. This conversation. Use fresh subagents that start empty, not forks that inherit the conversation; in Claude Code a
   fork carries your history, and an ordinary subagent doesn't.
3. A shared working folder. Give each run its own folder and its own copy of the inputs, so one run can't read or
   overwrite the other's output.
4. A different model or effort. A skill's own `model` or `effort` frontmatter can switch the with-skill run onto
   something else, so record the model and effort each run actually used, from its transcript or result, not what
   you asked for. Then say whether you're testing the instructions alone or the whole skill including its model
   choice.

Afterwards, read the baseline's transcript for any sign it loaded the skill or read its files. If it did, the
baseline isn't one, so fix the isolation and run it again.

If the skill is meant for several models, such as Claude and a Codex model, run the cases on each, because a skill
that works on one can misfire on another.

## Running them

For each case, launch both runs in the same turn, so they finish together. Give the with-skill run the skill's path
and the prompt. Give the baseline the same prompt, with no skill if this is a new skill, or a snapshot of the old
version if you're improving one. Take the snapshot before you edit.

Save each run's outputs in a workspace folder next to the skill, such as
`my-skill-workspace/iteration-1/<case>/with_skill/run-1/`. Keep the same folder names in later iterations, so it's
easy to compare one round with the next.

One run of each arm is a smoke test. It tells you whether the skill works at all. To decide between two versions, run
each arm two or three times, because the same prompt gives different results from run to run. A difference smaller
than that spread isn't a difference.

If the harness reports time and tokens when a run finishes, note them then, because they may not be stored anywhere
else. They tell you whether the skill costs more than it helps. If they aren't available, write "unavailable" rather
than guessing.

## Grading

Grade each checkable statement as passed or failed, with the evidence: the line in the output, or the step in the
transcript. Write a script for anything a script can check, like a number, a file's existence or a format. It's
faster, it doesn't drift, and you can reuse it next round.

Good statements are about the result, not the process. They're specific enough that two people would agree. "The
summary states total revenue of 693.5" is a good one. "The summary is good" isn't.

When you compare an old version with a new one, grade blind. Rename the outputs A and B, and only match them back to
versions after grading, because a grader that knows which output is new leans toward it.

Then look for patterns the pass rate hides. A statement that passes with and without the skill doesn't measure what
the skill adds. Keep it if it guards something that mustn't break, and mark it that way. Otherwise, swap it for one
that tells the two apart. A case whose result swings from run to run may be flaky. If the skill wins on quality but
doubles the time, say so.

Show the person every result before you change anything. Their judgement of the outputs matters more than your
grades, especially for writing, design or advice.

### When another agent acts on the output

Some skills make something another agent then acts on: a brief, a goal, a plan, a handoff, a prompt. For those, the
output isn't the result. What the receiving agent does with it is. Grading the brief itself tends to reward briefs
that look the way the skill says briefs should look, which proves nothing. So the results need at least one
receiver-side run: hand each output to a fresh agent with the same inputs and launch settings, let it do the work,
and grade what it did.

Take the grading statements from the task, not from the skill's rules. Ask whether the receiver kept to the scope,
respected the boundaries, actually finished, backed its claims with real evidence, and handled what it couldn't do,
rather than whether the brief used the skill's recommended shape. The exception is a contract, like an exact format a
program reads, which the statements should restate. Write the statements before you look at any output, and don't
change them afterwards, because statements written after seeing the results drift towards whichever output you
already prefer.

## The results record

Keep a short `results.md` in each iteration folder. Write down the revision of the skill under test and of the
baseline, the model and effort, the cases and how many runs each, every grade with its evidence, the time and tokens
(or "unavailable"), and what the person said. Without it, you can't tell next round whether a change helped or the
dice just rolled differently.

It also needs these fields, filled in even when the answer is "not done", because a record that leaves them out looks
complete when it isn't:
- Leakage checked: whether you read each baseline's and each trigger trial's transcript for leaks, and what you
  found.
- Trigger trials: for each, the context state (fresh, long, or after compaction), whether it fired, and its cost
  in tokens.
- Receiver-side run: for a skill whose output another agent acts on, whether one was done, and its grades.

## Does the description trigger?

Write about twenty prompts, around half that should fire the skill and half that shouldn't. Make them realistic, with
file names, context, typos and casual phrasing. The useful ones that shouldn't fire are near misses: requests that
share words with the skill but need something else. "Write a fibonacci function" tells you nothing about a PDF skill.
"Extract the table from this scanned invoice into a spreadsheet" might.

Keep the prompts substantial. Agents only reach for a skill when the task is more than they'd handle alone, so a
one-line request may not fire even a perfect description.

Show the list to the person before using it, because bad test prompts produce a bad description. Set aside about a
third of the prompts and don't look at them while you tune.

Test in real sessions where the skill is installed alongside the person's usual skills. Give each one a prompt that
doesn't mention the skill, and see whether it loads it. Run each prompt three times, because whether a skill fires
varies from run to run, and count how often it fired. Don't ask a model which skill it would pick from a list. That
tells the model it's being tested on skill choice, and it picks far more eagerly than it does in real work.

A fresh session is the easy case. A skill whose moment comes late in long work, like a handoff after hours of
building, has to fire when the context is full of other things, and possibly after compaction. For a skill like that,
add one or two trials in a long session and one or two after compaction. That's enough. These are a check on the
case that matters, not a suite. Compaction happens near the host's auto-compact window, which on one machine in
November 2026 was 350,000 tokens for Opus 5.5 (`autoCompactWindow` in `~/.claude/settings.json`). You can't fake
that state cheaply, so resume a real long session the person has already paid for (`claude --resume`, then `/compact`,
then the task) and record what each trial cost. Afterwards check what actually survived: Claude Code may re-attach a
skill's start after compacting, so an agent that doesn't call the skill again may still have it.

Check each trigger trial for leaks before you count it. A prompt that names the skill, a session that already loaded
it, or a hook that forces it all make it fire for reasons that have nothing to do with the description. A hook-forced
load tests the hook, which is worth testing too, but separately.

Tune the description on the prompts you kept, then judge the final version on the ones you set aside. If it does much
worse on those, it has been fitted to the test, so make it more general rather than adding the missed phrasings.

A `tool_used` grader under `claude plugin eval`, described below, runs real sessions and checks whether the Skill
tool was actually called. But its sessions load only the plugin under test, so it tells you whether the description
fires on its own, not whether it wins against the person's other skills. Do both: the eval for the bulk of the
prompts, and a few real sessions with the neighbouring skills installed.

## Running the cases with claude plugin eval

`claude plugin eval` runs the same cases headless, three times per arm by default, with and without the skill, and
reports the difference. It needs Claude Code 2.1.269 or later (checked 8 November 2026), and it evaluates plugins,
so the skill folder needs a `.claude-plugin/plugin.json` manifest. With that in place, Claude Code treats the folder as a plugin called
`<name>@skills-dir`. Pass `--scaffold` if any case uses a scaffold script, and `--allow-tools` for the tools the runs
need.

For trigger tests, a case per prompt with this grader passes when the skill was invoked:

```markdown
---
type: tool_used
tool: Skill
input_match: '"skill"\s*:\s*"(?:[\w-]+:)?my-skill"'
arm: both
---
```

For a near miss, set `min: 0` and `max: 0` so the case passes only when the skill wasn't used. In a with-and-without
run, a positive trigger case always shows a difference, because the arm without the plugin can't call it. Report it
as a trigger rate, not as evidence that the skill improves the work.

Eval runs also load none of your settings, `CLAUDE.md` files, memory or other skills, so the CLI gives you a clean
baseline for free. The subagent route is the one that can leak.

These are real model runs. Signed in with a Claude plan, they draw on the plan's limits. With an API key, they bill
the API. Either way, offer to run them rather than starting them yourself. `claude plugin validate <skills-folder>`
checks the frontmatter without running anything.
