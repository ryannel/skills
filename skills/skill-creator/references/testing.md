# Testing a skill

A test answers two separate questions. When the reader loads the skill, is its result better than without it?
And does the reader load the skill when it should? Watching a skill load answers only the second.

A check, in this file, is a statement about a result that is plainly true or false, such as "the summary states
total revenue of 693.5". The test files call a check a grader.

Contents: [Test cases](#test-cases) · [Writing the checks](#writing-the-checks) ·
[Keeping the two runs apart](#keeping-the-two-runs-apart) · [Running](#running) ·
[Without subagents](#without-subagents) · [Grading and reading the results](#grading-and-reading-the-results) ·
[When another agent acts on the output](#when-another-agent-acts-on-the-output) ·
[The results record](#the-results-record) · [Does the description load the skill?](#does-the-description-load-the-skill) ·
[Running the cases from a terminal](#running-the-cases-from-a-terminal)

## Test cases

A test case is a realistic request, any files it needs, and a description of a good result. Write the request
the way a person would type it, because that is what the skill will meet:

> Too clean: "Add a profit margin column to the spreadsheet."
>
> Realistic: "ok so my boss sent me q4-sales.csv and wants a profit margin column. revenue is C, costs are D i
> think. save it as q4-sales-margin.csv"

Make one of the cases awkward: bad input, an unusual request, or a place where the skill could be read two ways.

Keep each case as a folder under `evals/` in the skill. Claude Code's `claude plugin eval` command reads this
layout, so the same cases can later be run from a terminal. They are plain files, though, and you can use them
with no tool at all.

```
my-skill/evals/flags-negative-quantity/
├── prompt.md         settings, then the request exactly as a person would type it
├── case.yaml         the case name, a description of a good result, and how input files are placed
├── graders/          one check in each file
├── files/            input files, if the case needs any
└── place-files.sh    copies files/ into the run's folder; needed only when there are input files
```

`prompt.md` holds a few settings, which only the command reads, and then the request. An unknown setting stops
the case from loading.

```markdown
---
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

ok so my boss sent me q4-sales.csv and wants a profit margin column. revenue is C, costs are D i think. save it
as q4-sales-margin.csv
```

`case.yaml` describes the case. Put the schema version in quotes; without them it is read as a number, and the
case doesn't load.

```yaml
schema_version: "1.1"
name: flags-negative-quantity
expected_outcome: |
  Writes q4-sales-margin.csv with a margin column computed as (C-D)/C, and tells the person about the two rows
  with negative quantities.
context:
  scaffold_script: place-files.sh
```

`place-files.sh` copies the input files into the folder the run works in:

```bash
#!/usr/bin/env bash
set -eu
cp -R "$(dirname "$0")/files/." .
```

Each file in `graders/` holds one check, and a number at the front of its name keeps them in order, as in
`01-margin-formula.md`:

```markdown
---
type: llm
focus: { source: file, path: q4-sales-margin.csv }
---

PASS if the margin column equals (revenue - cost) / revenue on every row.
FAIL if any row differs, or the column is missing.
```

A case with no grader doesn't load. For a case only a person can judge, add one grader whose body is "The result
matches this description:" followed by the expected outcome, and leave it out of any score.

A skill made with Anthropic's skill-creator may also have an older `evals/evals.json`. Its tests still count, so
run them too. Don't edit, convert or delete that file unless the person asks.

The `evals/` folder is for the skill's author. Leave it out of the copy you install, upload or hand to a test
run.

## Writing the checks

Write the checks before any run. Once you have seen an output, your checks drift towards it.

A good check is about the result, and two people would agree on whether it holds. "The summary is good" is not
one. Neither is a check that looks for the skill's own wording or headings, because a result can be right in
other words.

Checks usually fall into four groups. Keep the list to what must hold.

| Group | Example |
|---|---|
| Outcome | The build passes. The file opens. The total is 693.5 |
| Process, only where a step is itself the requirement | The backup ran before the migration |
| Conventions the person asked for | Components are in `src/components/`, one per file |
| Cost | The run did not repeat the same command five times |

If the first results show a check is missing, add it, and grade it on both sides of every case.

## Keeping the two runs apart

The comparison means something only if the skill is the one difference between the two runs. There are five ways
something else gets in.

1. **An installed copy of the skill.** An agent can load any skill its host can see, whichever run it is in. A
   draft kept outside the skills folders can't get in this way. When you are improving an installed skill, turn
   the installed copy off for both runs and hand each run its own copy by path. In Claude Code, set
   `"skillOverrides": {"<name>": "off"}` in `.claude/settings.local.json`. That setting doesn't reach a plugin's
   skill, which you turn off through `/plugin`. If you can't turn it off, say so in the results record.
2. **The checks.** Hand each run a copy of the skill's folder without `evals/`. Otherwise the run with the skill
   can read what it will be graded on.
3. **This conversation.** Use subagents that start empty. In Claude Code an ordinary subagent starts empty, and a
   fork carries your history. Codex's `spawn_agent` carries your history unless you pass `fork_turns="none"`.
4. **A shared folder.** Give each run its own working folder and its own copy of the input files.
5. **A different model or effort.** A skill's own `model` or `effort` setting can move the run with the skill
   onto something else. Record what each run actually used.

Afterwards, read the transcript of each run without the skill. If it loaded the skill or opened its files, close
the gap and run it again.

## Running

Keep everything a test produces in a workspace folder that no host scans for skills, which means outside
`.claude/skills`, `.agents/skills` and `~/.codex/skills`:

```
my-skill-workspace/
├── old/my-skill/                          the untouched copy, when you are improving a skill
├── round-1/<case>/with_skill/run-1/       what the run with the skill produced
└── round-1/<case>/without_skill/run-1/    what the other run produced
```

Keep the same case names in later rounds, so one round can be compared with the next.

For each case, start both runs in the same turn. Give the run with the skill the path of its copy and the request.
Give the other run the same request and nothing else, or the path of the old copy when you are improving a skill.
Don't tell either run the answer you expect.

The same request gives different results from run to run. So when you compare versions over several runs, a
difference smaller than the spread between identical runs is not a difference.

If the host reports time and tokens when a run ends, write them down then, because they may not be kept anywhere
else. A skill that improves the result and triples the tokens is a different trade from one that is better and
cheaper.

Run the cases on each model the person uses, in that model's own host. If you can't run one, tell the person the
skill is untested there.

## Without subagents

Some hosts, such as a claude.ai chat, have no subagents. There, carry out each request yourself, one at a time,
following the skill as written, and skip the run without the skill. Tell the person this test is weaker, because
you wrote the skill and already know what it means. Show each result in the conversation and ask what they
think.

## Grading and reading the results

Mark each check passed or failed, with the evidence: the line in the output, or the step in the transcript. For
anything a script can check, such as a number, whether a file exists, or a format, write the script.

To compare an old version with a new one, have the grading done blind. Copy the two outputs to folders named A
and B, and give them to a fresh subagent with the checks and no word on which is which. An agent that knows which
output is the new one favours it, and you know which is which.

Then look at what the pass rate hides:

| What you see | What it means |
|---|---|
| A check passes with and without the skill | The reader didn't need the skill for that. Drop the check, or keep it as a guard against breakage |
| A check fails on both sides | Suspect the check or the case first |
| A check passes only with the skill | Find the line in the skill that did it. That line is what the skill is worth |
| Every case passes without the skill | The model may have outgrown the skill. Tell the person |
| Results swing between identical runs | The case is fragile, or a line in the skill can be read two ways |
| One run took far longer or used far more tokens | Read its transcript for the line that sent it astray |

Read the transcripts as well as the outputs. Wasted steps usually have one of three causes: a line too vague to
act on, a line that didn't apply to this task but was followed anyway, or a list of options with no default.

Show the person the results one case at a time: the request, then the two outputs side by side, then your grades.
Ask what they think of each. Their judgement of the outputs counts for more than your grades.

## When another agent acts on the output

Some skills produce something a second agent then acts on, such as a brief, a plan or a handoff. For those, the
real result is what the second agent does. Grading the brief itself rewards briefs that look the way the skill
says briefs should look, which proves nothing.

So hand each output to a fresh agent with the same input files, let it do the work, and grade that work. Take the
checks from the task: did the agent keep to the scope, respect the boundaries, finish, and back its claims with
evidence?

## The results record

Keep a short `results.md` in each round's folder. Next round, it is how you tell whether a change helped or the
results merely varied. Write down:

- the version of the skill, and of what it was compared with;
- the model and effort each run used;
- the cases, and how many runs of each;
- each grade, with its evidence;
- time and tokens, or "not available";
- whether you read each transcript without the skill for leaks, and what you found;
- what the person said.

## Does the description load the skill?

This test needs the skill installed beside the person's other skills, because it has to win against them. A
project's own skills folder is enough.

Write about twenty requests. Half should load the skill and half should not. Include four kinds:

- the skill named outright;
- the skill's exact situation, without its name;
- the same situation inside a longer, messier request;
- near misses, which share words with the skill but need something else. "Write a fibonacci function" tells you
  nothing about a PDF skill. "Extract the table from this scanned invoice into a spreadsheet" might.

Keep the requests substantial, because a reader reaches for a skill only when the task is more than it would do
alone. Show the list to the person before you use it. Set 40% of it aside, and don't look at that part while you
tune.

Each trial is a new session given one request. Whether a skill loads varies from run to run, so run each request
three times.

- In Claude Code, `claude -p "<request>" --output-format stream-json --verbose` prints the session's events. The
  skill loaded if they hold a `Skill` tool call that names it.
- In Codex, `codex exec --json "<request>"` prints the events of the run. Look there for the skill being read.
- On another host, start each session by hand and see whether the skill loaded.

A request that should load the skill passes when it loads in at least two of the three runs. A near miss passes
when it loads in at most one.

Twenty requests three times is sixty sessions, so give that number when you ask for approval. Six requests run
once each cost a tenth as much, and still catch a description that is badly wrong.

Don't ask a model which skill it would pick from a list. That tells it the test is about choosing skills, and it
picks far more readily than it does in real work.

Tune the description on the requests you kept. When a kind of request was missed, fix the description for that
kind, rather than pasting in the missed phrases. Then judge the final version on the part you set aside. If it
does much worse there, it has been fitted to the test, so make it more general.

Some skills are needed late in long work, such as a handoff after hours of building. Such a skill has to load
when the conversation is full of other things, so add one or two trials in a long session.

## Running the cases from a terminal

Both commands below start real model runs on the person's plan or API account.

**Claude Code: `claude plugin eval`** (2.1.269 or later). Run it from the skill's folder:

```bash
claude plugin eval . --scaffold --allow-tools Write Edit Bash
```

It runs each case three times with the skill and three times without, in empty folders with none of the person's
settings, memory or other skills loaded, and reports the difference. Because the folders are empty, its runs
without the skill can't pick the skill up, but it also can't show whether the skill wins against the person's
other skills. Some points are easy to miss:

- Claude Code 2.1.319 accepts a plain skill folder with no plugin manifest (checked 10 November 2026).
- `allowed_tools` in `prompt.md` only lists what a case wants. Tools that write files or run commands are granted
  on the command line, as above, and `--scaffold` is what lets each case's `place-files.sh` run.
- To check that the skill loaded, use a grader with `type: tool_used`, `tool: Skill` and an `input_match` on the
  skill's name. For a near miss, add `min: 0`, `max: 0` and `arm: both`.
- An `llm` grader shown the transcript (`focus: trace`) sees only its first twelve and last twelve messages. To
  grade what was made, point the grader at the file, or use a `regex` grader on the file for an exact value.
- `--ablation none` skips the runs without the skill and halves the cost. `--max-cost-usd` sets a ceiling.
- `claude plugin validate <folder>` checks frontmatter without running anything. On 2.1.319 it accepts a skills
  folder such as `.claude/skills`, or a plugin, and refuses a single skill folder with no plugin manifest.

**Codex: `codex exec --json "<request>"`** runs one request and prints each event of the run as a line of JSON.
A script can read those lines to check that a command ran and how it exited. To have a model grade the result,
add `--output-schema <file>` to a second, read-only run; the model then answers against your rubric in a fixed
JSON shape.
