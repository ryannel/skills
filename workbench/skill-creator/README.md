# Building skills for the current models

This is a summary of what Anthropic, OpenAI and the Agent Skills project say, in November 2026, about building a
skill for one of four models: Claude Opus 5.5 and Claude Fable 5.2 from Anthropic, and GPT-6 Astra and GPT-6.1
Sol from OpenAI. It is the basis of the `skill-creator` skill, published in
[skills/skill-creator](../../skills/skill-creator/).

It builds on the earlier research into prompting the same four models, in
[workbench/prompting-agents](../prompting-agents/README.md). That research covers how to write any text a model
will act on. This one covers what is particular to a skill: how it is found, loaded, structured, tested and
shipped.

Some words used below:

- A **skill** is a folder with a `SKILL.md` file in it. `SKILL.md` starts with a short block of settings called
  the frontmatter, which holds the skill's **name** and **description**. The rest of the file is the **body**.
- A **host** is the program that runs a model and gives it skills. Claude Code and Codex are hosts. So are
  claude.ai and each vendor's API.
- A **reference** is another file in the skill's folder that the body tells the model to read at some point.
- A **test case** is a realistic request, with any files it needs, and a description of a good result.
- A **baseline** is the same test case run without the skill, or with the skill's previous version.

## How the research was done

I read ten pages in Chrome and one file on this machine on 10 November 2026, and wrote seven notes, which are in
[references](references/). Each note gives the address and the date and says in my words what the source says.
Short quoted phrases are marked. The earlier research already held eight notes on skills and four on the models.
The full list is at the [end of this file](#sources).

Four limits:

1. Neither vendor has a page on writing skills for one named model. Anthropic's skill pages don't name Opus 5.5
   or Fable 5.2. OpenAI's Astra post and the skill-creator that ships with Codex are the only sources written
   after GPT-6 Astra, and nothing about skills is specific to GPT-6.1 Sol. So the model-specific advice below is
   the vendors' prompting advice for each model, applied to a skill.
2. Every number is a vendor's or a customer's own measurement. None was checked here.
3. The end of the troubleshooting section of the plugin-evals page was cut off and not read.
4. Host facts (folders, limits, flags, version numbers) change between releases. The notes are dated.

## The newest source, and why it matters

OpenAI rewrote the skill-creator that ships with Codex after it released GPT-6 Astra. The file on this machine is
dated 6 November 2026 ([note 01](references/01-openai-codex-skill-creator.md)). It is 40% shorter than the
version on GitHub, and it reverses several things that version said. It is the only skill-authoring guide from
either vendor written with one of the four models in mind, so where the sources disagree it carries extra weight.
Its additions:

- A skill supports the task the user asked for. It must not widen the assignment or imply permission for more
  outside actions.
- One example, one past failure or one person's preference should not become a rule for every task.
- Fit the process to the request. A narrow update needs one edit and a check, not an interview and a test round.
- Tests check what the agent did or produced. A test that matches wording or headings proves nothing.

## What the sources agree on

**1. A skill is loaded in three stages, and the first decides everything.** Every host shows the model the name
and description of each installed skill at the start of a session. The model reads the body only when it decides
the task matches a description. It reads a reference only when the body sends it there. No host matches keywords;
the model decides. So anything about when to use the skill belongs in the description, because the body is read
after the decision.

**2. The description says what the skill does and when to use it, briefly.** Hosts shorten descriptions when
many skills are installed (Claude Code at 1% of the context window, Codex at 2%), so the main use goes first.
Name where the skill stops only when a neighbouring request would otherwise be routed to it.

**3. Add only what the model lacks.** The test for a line, from agentskills.io: "Would the agent get this wrong
without this instruction?" The lines worth most are facts that defy a reasonable guess. If the model does the
whole task well without the skill, the skill adds nothing.

**4. Write the skill from a real task.** The steps that worked and, above all, the corrections the person made.
A skill written from general knowledge says things like "handle errors appropriately", which the model does
anyway.

**5. Say what result is wanted, and be exact only where the work is fragile.** Both vendors use the same
picture: an open field needs a direction, and a narrow bridge with a drop on each side needs exact instructions.
Recipes written for earlier models now limit the current ones to the steps the author thought of.

**6. Give a skill one job, and keep it self-contained.** Too narrow, and several skills load for one task and may
disagree. Too broad, and no description can say when to use it.

**7. Keep `SKILL.md` short and move detail into references.** Link each reference from `SKILL.md` and say when
to read it. Don't chain references. Don't add a README, a changelog or notes on how the skill was made. A simple
skill needs no references at all.

**8. Put repeated or exact logic in a script.** The script's code never enters the model's context; only its
output does. A script an agent runs must never prompt for input, must explain its errors, and should print
structured data ([note 02](references/02-agentskills-io-specification-and-scripts.md)).

**9. A rule that must hold every time does not belong in prose.** The model weighs a skill's text against
everything else it has read. A hook runs whatever the model decides. On Claude Code a skill can carry its own
hooks in its frontmatter.

**10. Test by running real requests with and without the skill.** Use a fresh context for each run, because
context left over from writing the skill hides its gaps. Run each side more than once, because results vary. Let
a program check what a program can check, and let a person judge the rest. Measure two things separately: does
the model load the skill when it should, and is the result right when it does.

**11. A skill goes out of date.** Both vendors say to re-read every skill at each new model. Anthropic adds
that a skill which teaches a technique may stop being needed: when the test cases pass without it, the model has
caught up.

**12. A skill is code and instructions from someone else.** Its contents should match what its description says
it is for. It should not fetch its instructions from the network.

## What each model does with a skill

| Model | What the vendor reports | What it means for a skill |
|---|---|---|
| Claude Opus 5.5 | In unattended runs, ends a turn on a progress report. Its predecessor, Opus 5, tested and delegated more than needed when told to, and Anthropic says Opus 5 prompts carry over | Say what finished means. Leave out "always run the tests" and "use subagents" lines; say when each is worth it |
| Claude Fable 5.2 | Follows every caution it finds. One stale "never retry" note among a dozen cut its retries from nearly every try to four in ten | Each caution in a skill is paid for on every task. State a boundary once, name the exact action, and put the exception inside the rule |
| GPT-6 Astra | "More sensitive to instructions in skills". Unclear or conflicting guidance in a skill can make it pause and stop work early. Returns after a first version | Two lines that disagree are worse than neither. Say what the agent may do without asking. Put running and fixing the result into what finished means |
| GPT-6.1 Sol | Finds about 92% of what Astra finds, and misses indirect cases | A line that names the missed pattern helps Sol. The same line may over-constrain Astra, so keep it narrow and re-check it at the next model |

Two more facts come from OpenAI. In its Responses API, a skill's text is treated as user input, not as a system
prompt, so it has the priority of anything else the user says. And OpenAI's guide for Astra suggests a prompt
line saying that the user's instructions take precedence over a skill's guidelines. No Anthropic source in the
notes says the same, so the draft states this for OpenAI's models only.

## Where the sources disagree

**How much goes in the description?** Anthropic's skill-creator says to make descriptions "a little bit pushy",
because Claude used to skip skills. An OpenAI post from February 2026 says to add "don't use when" cases and
negative examples, and reports that a customer's triggering recovered after it did. OpenAI's newer sources say
the opposite: "as short as possible", with an exclusion only where it prevents a likely wrong match. We take the
newer advice, for two reasons. Hosts cut long descriptions short. And Anthropic's own prompting page says wording
written to fight under-triggering now over-triggers. Widen a description only after a test shows a miss.

**Should every skill be tested?** Anthropic's skill-creator runs its test loop by default and repeats the
instruction three times. The Codex skill-creator says a test run is for a skill "sufficiently complex or risky",
and that ordinary creation and small edits don't need one. We take: the amount of testing is the person's
decision. Offer a small test for any skill that will be used more than a few times, and say what it costs.

**When are the checks written?** agentskills.io says to write pass or fail checks after the first outputs,
because you often don't know what good looks like until then. OpenAI's January post says to define success
before writing the skill. We take: write down what a good result must contain before looking at any output,
because checks written afterwards drift towards the output you already prefer. A check added later is fine, but
it is re-run on both sides.

**Should a test check the steps the agent took?** OpenAI's January post checks that expected commands ran in
the expected order. The Codex skill-creator says to check "observable behavior or meaningful invariants" and
not wording, headings or patterns. We take: check the result, and check a step only when the step is the
requirement (the migration ran before the deploy). A run that reached the same result another way has not failed.

**Should the body explain why?** Claude Code's skills page says "State what to do rather than narrating how or
why". Anthropic's prompting pages and skill-creator say to give the reason. We take: a reason that changes what
the agent does stays, as one clause. The story of how the author got there goes.

**Imperative steps, or no fixed steps?** OpenAI's Build skills page lists "write imperative steps with explicit
inputs and outputs" as a best practice. The newer Codex skill-creator says not to prescribe "a fixed structure,
process, or number of steps when the task does not require one". We take the newer one.

**Should a skill with side effects load only when named?** Claude Code's skills page suggests
`disable-model-invocation: true` for a skill that deploys or sends a message. The Codex skill-creator says not
to infer this from a sensitive operation: keep the skill discoverable, and require authorisation "immediately
before the actual mutation". We take: it is the person's choice, and the draft describes both ways.

**Which test file format?** Claude Code's docs say the skill-creator plugin uses `evals/evals.json` and that
`claude plugin eval` can't read it. The skill-creator synced from claude.ai on 10 November 2026 writes one folder
per test case, in the layout `claude plugin eval` reads. The docs are behind. We use the folders.

## What changes from Anthropic's skill-creator

The new skill keeps Anthropic's method: take the workflow and the corrections from a real task, draft, run
realistic requests with and without the skill in fresh subagents, grade what can be graded, show the person
everything, and revise the cause. The research changes how the skill itself is written, and seven things in what
it teaches.

| Anthropic's skill-creator | Newer or measured guidance | What the new skill does |
|---|---|---|
| "Make the skill descriptions a little bit pushy" | Over-emphasis loads skills that don't help; hosts shorten descriptions | One sentence on what, one on when; widen only for a measured miss |
| "Take your time and really mull things over"; "we are trying to create billions a year" | How hard a model thinks is a setting outside the prompt; such lines are ordinary text | Left out |
| An output template headed "ALWAYS use this exact template"; "GENERATE THE EVAL VIEWER" in capitals | Emphasis makes current models apply a rule too widely | Plain wording. A template is marked exact only when a program reads the output |
| The core loop stated at the top, in the middle, and "one more time … for emphasis" at the end | A repeated instruction costs attention and makes Fable 5.2 and Astra over-apply it | Stated once |
| Four intake questions and an interview before writing | Ask only when the fact matters and can't be inferred | Take answers from the conversation first; ask about what is missing |
| The test loop as the default path | The amount of testing fits the risk, and is the person's call | A smoke test is offered; the person decides |
| Separate sections for Claude.ai and Cowork; description tuning through `claude -p` | A skill is read on several hosts and by several models | Host facts in one dated reference; a trigger test that works on any host |

## The two layers

The new skill has to work at two levels, and they need different things.

1. **It is itself a skill that one of these models will read.** So it follows the prompting research: say the
   main thing first, give the purpose, say what finished looks like, state each boundary once, leave out steps
   the agent would work out, and write in whole plain sentences.
2. **It teaches the agent to write a skill for one of these models.** The agent using it will write a
   description and a body, and those are prompts. So the skill carries its own account of what a skill must hold,
   what it must leave out and how to word it. It can't lean on the `prompting-agents` skill for this, because a
   skill has to work when installed alone.

What goes where in the skill:

| File | What it holds | When the agent reads it |
|---|---|---|
| `SKILL.md` | What a skill is and who reads it. The work from request to shipped skill. The core of what a skill carries, leaves out and how to word it. What the agent may do without asking | Every time |
| `references/writing.md` | Each writing rule at work, with examples. The description in detail. Matching strictness to the task | Before writing or rewriting a skill |
| `references/structure.md` | The folder, the frontmatter fields, what each host does, scripts, the mistakes that fail silently, where skills are installed. Dated | When laying out a skill, adding a script, or shipping to a host |
| `references/testing.md` | Test cases, keeping runs apart, grading, reading results, testing the description, and the two vendors' tools | When testing |
| `references/models.md` | What each of the four models does with a skill, by symptom, and how to move a skill to a newer model. Dated | When a skill misbehaves on one model, or at a model change |
| `scripts/check_skill.py` | Checks a skill folder for the mistakes that fail without an error | Before handing a skill over |

## How the skill was checked

`scripts/check_skill.py` prints `ok` on the draft. A fresh agent then read the draft as its reader and compared
it with Anthropic's skill-creator and the notes. It reported 24 findings, and the draft was revised for them. The
main ones:

- Test cases sat inside the folder handed to the run with the skill, so only that run could read what it was
  graded on. The draft now says to hand over a copy without `evals/`.
- Improving an installed skill had no safe place to work. The draft now says to copy the folder twice into a
  workspace no host scans, and to turn the installed copy off for both runs.
- The description test had no way to run it, no pass mark and no cost. It now has all three.
- Five facts were wrong or wider than their source: which skill wins when two share a name, what Claude Code
  keeps after compaction, the share of requests to set aside, a symlink claim, and test reminders described as
  harmful on all four models when the sources cover GPT-6 Astra and Claude Opus 5.
- The check script failed sound skills: it checked files under `evals/` and `assets/`, and read link syntax
  shown in backticks as a link.

Then one round of tests: three requests, each run once with the draft and once with the skill-creator it
replaces, graded blind by a fresh agent. The cases are in [evals](evals/) and the record is in
[skill-creator-workspace/round-1/results.md](skill-creator-workspace/round-1/results.md).

- The 32 checks did not separate the two versions: the draft passed all 32, and the old skill passed 31 with one
  unclear.
- Asked which output it would hand to the person, the grader chose the draft's in two cases and the old skill's
  in one, narrowly each time.
- Tokens and time were about equal.
- Two outputs made with the draft showed faults, and three lines were added to `SKILL.md` for them. Those lines
  are untested.

So the test shows the new skill is no worse than the old one on these requests. It does not show that it is
better.

Not done:

- No run on Claude Opus 5.5, GPT-6 Astra or GPT-6.1 Sol. All runs were on Claude Fable 5.2.
- No test of whether the description loads the skill.
- The testing and review parts of the skill were not exercised, because the runs had no person to answer.
- Some host facts in `structure.md` and `testing.md` come from the previous skill and from this machine, not
  from a note. They carry their dates.

## Sources

Notes from this round:

| Note | Source | Publisher |
|---|---|---|
| [01](references/01-openai-codex-skill-creator.md) | The `skill-creator` that ships with Codex (local file, dated 6 November 2026) | OpenAI |
| [02](references/02-agentskills-io-specification-and-scripts.md) | [Specification](https://agentskills.io/specification) and [Using scripts in skills](https://agentskills.io/skill-creation/using-scripts) | Agent Skills (Linux Foundation) |
| [03](references/03-agentskills-io-how-hosts-load-skills.md) | [How to add skills support to your agent](https://agentskills.io/client-implementation/adding-skills-support) | Agent Skills (Linux Foundation) |
| [04](references/04-claude-code-plugin-evals-and-anthropic-skills-overview.md) | [Test plugins with evals](https://code.claude.com/docs/en/plugin-evals) and [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) | Anthropic |
| [05](references/05-anthropic-improving-skill-creator.md) | [Improving skill-creator](https://claude.com/blog/improving-skill-creator-test-measure-and-refine-agent-skills) | Anthropic |
| [06](references/06-openai-skills-api-and-earlier-posts.md) | [Skills in the API](https://developers.openai.com/api/docs/guides/tools-skills), [Testing Agent Skills Systematically with Evals](https://developers.openai.com/blog/eval-skills), [Shell + Skills + Compaction](https://developers.openai.com/blog/skills-shell-tips) | OpenAI |
| [07](references/07-claude-code-skills-page-second-reading.md) | [Extend Claude with skills](https://code.claude.com/docs/en/skills), second reading | Anthropic (Claude Code) |

Notes from the prompting research that this summary also draws on, in
[workbench/prompting-agents/references](../prompting-agents/references/):

| Note | Subject |
|---|---|
| 02, 03 | Anthropic's prompting pages for Fable 5.2 and Opus 5.5 |
| 04 | Anthropic's skill authoring best practices |
| 05 | Claude Code's skills page, first reading |
| 06, 07 | agentskills.io on best practices, descriptions and evaluating skills |
| 08, 15 | OpenAI's Using GPT-6, and the post comparing Astra and Sol 6.1 |
| 09 | OpenAI's Rethinking skills and prompts for GPT-6 Astra |
| 10, 12 | OpenAI's Build skills page, and the older skill-creator on GitHub |
| 16 | The writing style |
| 17 | Anthropic's skill-creator |
