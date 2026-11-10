---
name: prompting-agents
description: Writes and repairs text that another AI agent will act on, for Claude Opus 5.5, Claude Fable 5.2, GPT-6 Astra and GPT-6.1 Sol. Use when about to write or send a brief for a subagent or session, a goal for a long unattended run, a review request, a steer, a system prompt, a CLAUDE.md or AGENTS.md, or a skill. Also use when moving instructions to a newer model, or when an agent stopped early, asked for approval it didn't need, tested or delegated too much, or ignored an instruction. Not for the process of creating and testing a skill (skill-creator).
---

# Prompting agents

A prompt, in this skill, is any text another agent will act on. The agent that reads it is called the reader.

The reader is a capable model. On most tasks it plans at least as well as you do. But it knows only what you
write down and what it can find in the files it opens. So a prompt goes wrong in two ways: it tells the reader
how to do the work, or it leaves out a fact the reader needed and could not have found.

Before you send a prompt, read it once as an agent that has seen nothing else, and check it against the three
sections that follow.

## What a prompt carries

**The purpose.** Say in a sentence or two what the work is for. The reader uses the purpose to decide the cases
you did not think of.

**What done looks like, and the check.** Say what must be true at the end and what will show it: a test that
passes, a build that succeeds, a file with a verdict in it, a screenshot beside the design. A reader with no
check stops when the work looks finished. If finishing includes running the result and fixing what fails, say so,
because some models return after a first version. Ask for the evidence (the command and its output), not the
words "all tests pass".

**The boundaries.** A boundary is something the reader must not do, or must get a go-ahead for. Take boundaries
from the project's own rules and from what the person told you. Don't add one out of caution.

- State each one once. A repeated boundary makes current models ask for approvals they don't need.
- Name the exact action. "Don't push to `main`" works. "Be careful with git" makes the reader hesitate over
  every git command.
- Put the exception inside the rule. "Get a go-ahead before you run a migration" works. "Never run a migration",
  with a separate line saying approved ones are fine, mostly doesn't.
- Give the reason in one clause, so the reader can apply the rule to a case you didn't name.
- Then say what the reader may do without asking. For example: "Reading files, editing code inside `src/billing`
  and running the local tests need no approval. The tests use throwaway fixtures."

**What the reader can't see.** Decisions made in conversation. What was already tried and ruled out. Which
source or version is the authoritative one. Steps that reproduce the bug. The person's preference between two
reasonable approaches. If you have the thing itself (a file path, an error log, a screenshot), hand it over
instead of describing it. Mark quoted logs and web text as quoted, so the reader doesn't take them for
instructions. Check any claim before you pass it on, because a prompt turns your guess into the reader's
requirement.

**What comes back.** Say where the result goes. Give an exact format only when a program or the next agent
depends on it. Otherwise ask for two things: the main finding first, and what was verified kept apart from what
is suspected.

A list that is the task stays in, whatever its shape: the browsers that must work, the cases the person named,
the steps that reproduce a bug.

## What a prompt leaves out

- **Steps you made up.** Also reading orders, techniques and report sections. They limit the reader to what you
  thought of. Give steps only when the order is the task, as in a data migration.
- **Emphasis and pressure.** Capitals, "IMPORTANT", "be thorough", "think hard", "don't be lazy". Current models
  follow a plain line, and emphasis makes them apply a rule too widely. How hard a model thinks is a setting
  outside the prompt, and words in the prompt can't raise it.
- **Reminders to do what the reader does anyway.** "Run the tests", "check your work" and "keep going" now cause
  extra testing and over-work. A check that is part of done is different; keep that.
- **Your conclusion,** when you ask for a review or an investigation. A reader handed your answer tends to come
  back agreeing with it.
- **The same point made again.** A second wording of a rule, or a second and third example of the same thing,
  costs the reader attention and tells it nothing new.
- **The story so far,** unless the reader will use it.

When you have an older prompt to hand, don't edit it into shape. Start from the purpose, done, boundaries and
context. Then take from the old prompt only the facts that are still true. Editing keeps its lists and its
emphasis along with its facts.

## How to write it

Write the way Randall Munroe writes in "What If?", without the jokes: for a clever reader who is new to the
subject. A prompt needs this more than most writing, because its reader can't ask what you meant.

1. **Say the main thing first.** The first lines of a prompt are the lines least likely to be lost.
2. **Name who does each thing.** "Run the tests before you merge" tells the reader it is the reader's job. "The
   tests are run before merging" doesn't say whose job it is.
3. **Explain a term before you use it, then keep using that word.** If you call it a "module" in one sentence and
   a "component" in the next, the reader has to decide whether those are two things. Don't make up a label for
   something that already has a name.
4. **Use ordinary words.** A technical word is fine when it is the name of the thing.
5. **Tell things in the order they happen.** Use numbered steps only when the order matters, and name who does
   each step.
6. **Be concrete.** A file path, a number, a command or one example carries more than a description of them.
7. **Write whole sentences.** A prompt stays small because of what you leave out. Don't shrink it by dropping
   words until the sentences turn into labels the reader has to decode.
8. **Say what to do.** "Write in paragraphs" works better than "don't use bullet points".
9. **A script is not an agent.** An agent runs a command, and the command does something. Don't write "tell the
   build script to", because the reader may go looking for something to talk to.

Before and after:

> Before: "CRITICAL: Auth must be thoroughly reviewed!! Check everything carefully and make sure nothing is
> broken. Be comprehensive."
>
> After: "Review the diff on branch `auth-refresh` against `docs/auth-spec.md`. The change makes a session renew
> its access token when the token is within five minutes of expiring. Report any requirement in the spec that the
> diff does not meet, and any case where a user could be logged out mid-request. Leave style alone. For each
> finding, give the file and line and say whether you confirmed it by running something."

## Where an instruction belongs

An instruction works best close to the moment it applies.

| The instruction | Put it in |
|---|---|
| Applies to one task | The prompt |
| A fact needed in every session in this repository | The instruction file (`CLAUDE.md`, `AGENTS.md`) |
| A procedure needed for some tasks | A skill |
| Must hold through a long unattended run | The goal for that run, or a notes file the reader keeps re-reading |
| Must hold every time, with no exceptions | A hook, a test or a permission rule. The program that runs the model applies these whatever the model decides |

If you keep strengthening the wording of a line and the reader still misses it, the line is in the wrong place.
Move it down the table.

## Which model is reading

The four current models respond differently to the same prompt.

| Model | Watch for |
|---|---|
| Claude Opus 5.5 | In unattended runs, a turn that ends on a progress report with work left |
| Claude Fable 5.2 | Following every caution it finds, including stale ones in notes and instruction files |
| GPT-6 Astra | Stopping to ask, or returning after a first version, where you wanted it to continue |
| GPT-6.1 Sol | Missing indirect cases that Astra finds |

When an agent did the wrong thing, look for the instruction that caused it before you add a new one. An agent
that stops to ask too often has usually read an old caution, a rule stated three times, or two files that
disagree. Removing that line fixes more than adding "don't ask" does.

[Models](references/models.md) lists what to change in the prompt for each symptom, with the date it was checked.
Read it when an agent misbehaved, or when you move instructions to a newer model.

## More

- [Kinds of prompt](references/kinds.md): what a subagent brief, a goal for a long run, a review request, a
  steer and a system prompt each add, with an example of each. Read it when you write one of these.
- [Instruction files](references/instruction-files.md): `CLAUDE.md` and `AGENTS.md`. Read it before you write
  or trim one.
- [Skills](references/skills.md): how a skill is loaded, and what goes in the description and the body. Read it
  before you write or revise a skill. Testing a skill is the job of a skill-creator skill, not this one.
- [Writing style](references/writing-style.md): each writing rule at work. Read it before you write anything
  long, such as a skill or an instruction file.
