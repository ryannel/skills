# Prompting the current models, and building skills for them

This is a summary of what Anthropic and OpenAI say, in November 2026, about two jobs:

1. Writing a prompt that one of their best models will act on.
2. Building a skill for one of those models.

It covers four models: Claude Opus 5.5 and Claude Fable 5.2 from Anthropic, and GPT-6 Astra and GPT-6.1 Sol from
OpenAI. It is the basis of the `prompting-agents` skill, which is published in
[skills/prompting-agents](../../skills/prompting-agents/).

The skill had one round of tests on its first version: three tasks, each run once with the skill and once
without. The test cases are in [evals](evals/) and the results are in
[prompting-agents-workspace/iteration-1](prompting-agents-workspace/iteration-1/). After that round
the skill was cut down to the scope described [below](#what-this-means-for-the-new-skill), and the shorter
version has not been tested.

Some words used below:

- A **prompt** is any text a model will act on: a message to a subagent, a goal for a long run, a review request,
  a system prompt.
- An **instruction file** is a file an agent reads at the start of every session in a repository. Claude Code
  reads `CLAUDE.md`. Codex reads `AGENTS.md`.
- A **skill** is a folder with a `SKILL.md` file in it. The agent sees the skill's name and one-paragraph
  description all the time. It reads the rest only when a task matches the description.
- A **harness** is the program that runs the model in a loop and gives it tools. Claude Code and Codex are
  harnesses.
- A **subagent** is a second copy of a model that an agent starts to do part of its task.
- **Effort** is a setting, outside the prompt, for how much a model thinks before it answers. Its levels are
  `low`, `medium`, `high`, `xhigh` and `max`.

## How the research was done

I read 16 pages in Chrome on 10 November 2026, starting from each vendor's own documentation menus. After each
page I wrote a note file. The 17 notes are in [references](references/). Each one gives the page's address and
the date, and says in my words what the page says. Short quoted phrases are marked. The list is at the
[end of this file](#sources).

Four limits:

1. OpenAI has no separate prompting guide for GPT-6.1 Sol. Its guide says the advice was observed on GPT-6 Astra
   and is "a starting point across the GPT-6 model family". The only Sol-specific evidence is one engineering
   blog post ([note 15](references/15-openai-maintaining-software-gpt-6-family.md)).
2. Every number below is the vendor's own measurement on the vendor's own tasks. None was checked here.
3. I did not read the migration section of Anthropic's general prompting page, and GitHub showed only the top and
   bottom of OpenAI's `skill-creator`.
4. The pages will change. The notes are dated so that a later reader can tell what was true when.

## The four models

| | Claude Opus 5.5 | Claude Fable 5.2 | GPT-6 Astra | GPT-6.1 Sol |
|---|---|---|---|---|
| Place in its family | Below Fable | Anthropic's most capable | OpenAI's most capable | Near Astra, much cheaper |
| Effort to start from | `medium` | `high` | Keep what you had; no `none` | `medium`; no `none` |
| Can thinking be turned off? | No | No | No | No |
| Main thing to watch | Ends an unattended turn on a progress report | Follows every caution it finds, so old cautions pile up | Stops to ask where an earlier model would assume | Misses indirect cases that Astra finds |

Sources: notes [02](references/02-anthropic-prompting-fable-5-2.md),
[03](references/03-anthropic-prompting-opus-5-5.md), [08](references/08-openai-using-gpt-6.md),
[15](references/15-openai-maintaining-software-gpt-6-family.md).

## What both vendors agree on

These eleven points appear in both vendors' pages. They are the core of the new skill.

**1. The model is capable and has none of your context.** Anthropic's picture is a brilliant new employee who
doesn't know your norms. OpenAI's is a senior co-worker you give a goal to. So the useful part of a prompt is what
the model can't see: a decision made in a meeting, the reason for the work, what was already tried, which source
is the authoritative one. Claude Code's docs give a two-question test before writing anything down: could the
model find this by reading the code, and would it go and look? If both are yes, leave it out.

**2. Say what result you want. Leave the steps out.** OpenAI: "Start with the result, not a detailed list of
steps." Anthropic: "Prefer general instructions over prescriptive steps", because the model's own plan is often
better than one a person would write. OpenAI's Astra post goes further: skills written as detailed recipes "can now
hinder results where [they] previously helped". Steps still belong where the order is the task itself, such as a
database migration.

**3. Say what done looks like, and give the model a check it can run.** A model stops when the work looks done.
If it has a test, a build or a comparison that returns pass or fail, it can find its own mistakes and fix them.
OpenAI adds, for Astra: define completion before the work starts, because Astra may return after a first version.

**4. State each boundary once, and name the exact actions.** A boundary is something the model must not do, or
must ask about first. Both vendors found that current models take boundaries very seriously. Anthropic measured
it: a rule that listed "sending messages to people outside this conversation" made Fable 5.2 hold back about half
of its routine requests to colleagues. OpenAI says strong "ask first" wording written for an earlier model makes
Astra stop where you would want it to continue. Two things follow. Name the actions that need no approval, not
only the ones that do. And write the exception into the rule itself: under a "never" rule with a separate note
saying approved steps may proceed, Fable 5.2 took the approved step one time in ten. With the rule rewritten as
"get a go-ahead first", it took it nine times in ten.

**5. Give the reason with the rule.** A model that knows why a rule exists applies it correctly to cases the rule
didn't name. Anthropic's example: "never use ellipses" works less well than saying the text will be read aloud by
a speech engine that can't pronounce them.

**6. Write plainly. Capital letters and "be thorough" don't do what they used to.** Current models follow a
plainly worded line. Emphasis makes them apply the rule too widely. Phrases like "think hard" are ordinary text:
effort is the control for thinking, and words can't raise it past its setting.

**7. Fewer instructions work better.** OpenAI removed repeated instructions and examples from coding-agent system
prompts and measured scores about 10 to 15% higher with 41 to 66% fewer tokens. Anthropic found that one stale
"never retry" note among a dozen cut Fable 5.2's retries from nearly every try to about four in ten.

**8. Instructions written for an earlier model are now a risk.** Both vendors tell you to re-read everything you
carry over (system prompts, skills, instruction files, saved notes) at each new model, and both ship a tool that
does the audit: `/doctor prompt-audit` in Claude Code, and the OpenAI Docs skill in Codex.

**9. A rule that must hold every time does not belong in prose.** A prompt, an instruction file and a skill are
all read by the model, and the model decides what to do with them. A hook, a test, a permission rule or a
continuous-integration check is run by the harness, whatever the model decides. Claude Code's docs give the sign
that a line is in the wrong place: you keep adding emphasis and it is still missed.

**10. A subagent is the same model without your context.** It gives parallel work, a clean context for noisy
output, or a reviewer that hasn't seen your reasoning. It does not give a smarter answer. How much a model
delegates depends on the model and the harness, so both vendors say to state when delegating is worth it.

**11. Test a prompt or a skill by running it with and without.** Use a fresh context, realistic tasks, and a
person to judge what a check can't. Both vendors say to change one thing at a time and measure.

## Where the models differ

Anthropic's two model pages are organised by symptom: find what you observe, apply that fix. The table follows
the same idea across all four models.

| What you observe | Most likely on | What the vendor suggests |
|---|---|---|
| The turn ends with a list of what remains, or an offer to continue | Fable 5.2 at `low` or `medium`; Opus 5.5 in unattended runs | Say that ordinary obstacles (errors, timeouts) are to be worked through and deliberate ones (a protected file, withheld access) reported. On Opus 5.5, name the early stops you don't want and the stops you do. Have the harness treat a text-only turn as a report, not as done |
| It asks a question, or asks approval, before doing work it could have done | GPT-6 Astra | Tell it to do all the authorised work first, so approval is the last step on a concrete result. Give standing permission, with the reason, for workflows you know are safe |
| It returns after a first version | GPT-6 Astra | Put running the result, inspecting it and fixing failures into the request |
| It asks approvals it doesn't need, or stops retrying | Fable 5.2, GPT-6 Astra | Delete cautions that no longer apply. Check what reviewer agents and saved notes add. Name the steps that need no approval |
| It runs more tests than the change needs | GPT-6 Astra; Opus 5 | Remove "always run the tests" lines. Say what verification the change needs |
| It delegates too little, or too much | Astra (too little); Fable 5.2 (depends on the harness); Opus 5 (too much) | Say when a subagent is worth its cost and how to brief one |
| Its prose is choppy | Fable 5.2 under hard style limits | Remove limits like "20 words per sentence". Describe the reader instead |
| Its answers are heavy with lists and tables | GPT-6 Astra | Ask for paragraphs, with lists only for parallel or ordered items |
| It says nothing for long stretches | Fable 5.2, Opus 5.5 | First check that the client shows progress updates. Then ask for a one-line update every few tool calls |
| It finds fewer cases than the top model | GPT-6.1 Sol | Find the pattern it misses and name it in the prompt. Re-check that line at the next model |
| It refuses to write out its reasoning | All four | Don't ask for reasoning in the response. Read the thinking summaries |

## Where the sources disagree

**How strong should a skill's description be?** Anthropic's skill-creator says Claude tends not to use skills when
it should, so make descriptions "a little bit pushy". agentskills.io says the same. OpenAI's Astra post says the
opposite: make the description "as short as possible" while clear about when to use it, because descriptions that
over-state when to use a skill make the model load instructions that don't help. Two facts settle it for us. Both
hosts cut descriptions short when many skills are installed (Claude Code at 1% of the context window, Codex at
2%), so the first sentence is what survives. And Anthropic's own prompting page says prompts written to fight
under-triggering now over-trigger. We take: one sentence on what the skill does, one on when to use it, with the
main use first and a boundary where a neighbouring skill exists. Add reach only after a test shows a miss.

**Should a skill explain why?** Claude Code's skills page says "State what to do rather than narrating how or
why", because every line of a loaded skill is paid for on every turn. Anthropic's prompting pages and its
skill-creator say to explain why. These fit together: a reason that changes what the reader does stays, as one
clause. The story of how the author got there goes.

**Should instruction files tell the model to run the tests?** OpenAI's `AGENTS.md` page still shows "Always run
`npm test`" as a sample line. Its newer Astra post says such lines now cause needless testing. Anthropic says the
same about Opus 5. We take the newer advice: give the command that runs the check, and say when the check is
needed.

**Should a description be in the third person?** Anthropic's older page says yes. agentskills.io says to write it
as an instruction ("Use this skill when…"). Both require what and when. We write a what-sentence, then "Use
when…".

## Building a skill

A skill has three levels, and each is loaded at a different time.

1. The agent sees the name and description of every installed skill at the start of every session.
2. When a task matches a description, the agent reads that skill's `SKILL.md`.
3. `SKILL.md` links to other files in the folder. The agent reads one when `SKILL.md` says to.

What follows from that:

- The description does all the work of getting the skill used. Anything about when to use the skill that sits in
  the body is read only after the decision has been made.
- In Claude Code, `SKILL.md` enters the conversation once and stays. It is not read again. After the conversation
  is compacted, only the first 5,000 tokens of the skill are kept. So the instructions that matter most go at the
  top, and guidance that must hold all task is written as a standing instruction ("run the tests after every
  edit"), not a one-time step.
- Every line of a loaded skill competes with the task for the model's attention. The test for a line, from
  agentskills.io: "Would the agent get this wrong without this instruction?" If not, cut it.
- The parts worth the most are the facts that defy a reasonable guess. agentskills.io calls them gotchas: a
  column that marks deleted rows, an endpoint that reports healthy when the database is down.
- Give one default, not a menu. Teach the method for a class of problems, not the answer to one.
- Match how strict each part is to how fragile the task is. An exact command for a fragile operation; a
  description of what to look for where several approaches are fine.
- Keep `SKILL.md` under 500 lines. Move detail into reference files, and say when to read each one.
- A skill is read by every model that works in the repository. OpenAI: guidance that helps a smaller model may
  over-constrain Astra.

Anthropic's skill-creator supplies the method for getting from an idea to a tested skill: take the workflow and
the person's corrections from a real task, draft, run two or three realistic prompts with and without the skill
in fresh subagents, grade what can be graded, show the person everything else, and revise the cause, not the test
case. The research changes three things in how we use it. We do not make descriptions pushy by default. We leave
out lines like "take your time and really mull things over", which the newer pages call ordinary text. And we do
not head a template "ALWAYS use this exact template" unless a program reads the output.
[Note 17](references/17-anthropic-skill-creator.md) has the table.

## The writing style

The new skill asks for prose in the style of Randall Munroe's "What If?" articles, without the jokes. A "What If?"
article states its setup first, gives the answer early, then walks through what happens in order. Every sentence
names who or what is acting. Terms are ordinary, and a technical one is explained by the sentence it sits in.
Numbers come with something familiar to compare them to.

This is close to what both vendors ask for. Anthropic's block for final reports asks for writing aimed at an
intelligent reader with little context: short sentences, one idea each, active voice, the same word for the same
thing, no terms made up along the way. OpenAI's writing prompt for Astra asks for "familiar words, concrete
examples, and precise verbs", the main point early, and no invented compound labels.

It also suits a prompt for a practical reason. The question a receiving agent most often gets wrong is who is
meant to do a thing. A sentence with a named actor answers it. "The tests are run before merging" leaves it open.
"Run the tests before you merge" does not. [Note 16](references/16-randall-munroe-style.md) lists the traits and
the rules this repository's owner added.

## What this means for the new skill

The skill covers one thing: the words a writer puts into a prompt, an instruction file or a skill. A line belongs
in the skill only if it changes those words. Three kinds of line fail that test and stay out:

- What an agent may do in a particular project, such as whether an overnight run may push a branch. That is the
  project's decision. The skill only says how to state a decision clearly.
- How to set up a host or a harness: effort levels, approval modes, hooks, where skills are installed.
- Which model to choose, and what each costs.
- How to test a skill. That is the job of a skill-creator skill.

Within that scope:

1. Its centre is a short list of what a prompt must carry (the purpose, what done looks like and the check, the
   boundaries, the context the reader can't see, what comes back) and what it must leave out (invented steps,
   emphasis, pressure, the writer's conclusion).
2. The writing style is part of the main file, because it applies to every prompt.
3. Model-specific advice sits in one dated reference, organised by symptom, because it will go out of date first.
4. Skills and instruction files each get a reference, because they are loaded differently from a prompt and that
   changes how they should be written.
5. It says where an instruction should go: a prompt, an instruction file, a skill, or a hook.
6. It is tested the way skill-creator says: realistic tasks, with and without the skill, in fresh subagents, with a
   person reviewing the writing.

## Sources

| Note | Page | Publisher |
|---|---|---|
| [01](references/01-anthropic-prompting-best-practices.md) | [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) | Anthropic |
| [02](references/02-anthropic-prompting-fable-5-2.md) | [Prompting Claude Fable 5.2](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2) | Anthropic |
| [03](references/03-anthropic-prompting-opus-5-5.md) | [Prompting Claude Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5) | Anthropic |
| [04](references/04-anthropic-skill-authoring-best-practices.md) | [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) | Anthropic |
| [05](references/05-claude-code-skills.md) | [Extend Claude with skills](https://code.claude.com/docs/en/skills) | Anthropic (Claude Code) |
| [06](references/06-agentskills-io-best-practices-and-descriptions.md) | [Best practices for skill creators](https://agentskills.io/skill-creation/best-practices) and [Optimizing skill descriptions](https://agentskills.io/skill-creation/optimizing-descriptions) | Agent Skills (Linux Foundation) |
| [07](references/07-agentskills-io-evaluating-skills.md) | [Evaluating skill output quality](https://agentskills.io/skill-creation/evaluating-skills) | Agent Skills (Linux Foundation) |
| [08](references/08-openai-using-gpt-6.md) | [Using GPT-6](https://developers.openai.com/api/docs/guides/latest-model) | OpenAI |
| [09](references/09-openai-rethinking-skills-and-prompts-astra.md) | [Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | OpenAI |
| [10](references/10-openai-build-skills.md) | [Build skills](https://developers.openai.com/codex/build-skills) | OpenAI |
| [11](references/11-openai-prompting-and-agents-md.md) | [Prompting](https://developers.openai.com/codex/prompting) and [Custom instructions with AGENTS.md](https://developers.openai.com/codex/agent-configuration/agents-md) | OpenAI |
| [12](references/12-openai-prompt-engineering-and-skill-creator.md) | [Prompt engineering](https://developers.openai.com/api/docs/guides/prompt-engineering) and [OpenAI's skill-creator](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md) | OpenAI |
| [13](references/13-claude-code-instruction-files.md) | [How Claude remembers your project](https://code.claude.com/docs/en/memory) | Anthropic (Claude Code) |
| [14](references/14-claude-code-best-practices.md) | [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices) | Anthropic (Claude Code) |
| [15](references/15-openai-maintaining-software-gpt-6-family.md) | [Maintaining software with the GPT-6 family](https://developers.openai.com/blog/maintaining-software-with-the-gpt-6-family) | OpenAI |
| [16](references/16-randall-munroe-style.md) | [Relativistic Baseball](https://what-if.xkcd.com/1/), and the owner's corrections | Randall Munroe |
| [17](references/17-anthropic-skill-creator.md) | The `skill-creator` skill synced from claude.ai | Anthropic |
