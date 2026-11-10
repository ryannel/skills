---
name: prompting-agents
description: Helps you write text that another AI agent will act on, such as a brief for a subagent or session, a goal for a long unattended run, a review request, a steer, a system prompt, or a CLAUDE.md or AGENTS.md. Use before you write or send one, when you move instructions to a newer model, or when an agent stopped early, asked for approval it didn't need or ignored an instruction. Covers Claude Opus 5.5, Claude Fable 5.2, GPT-6 Astra and GPT-6.1 Sol. Not for writing or testing a skill (skill-creator).
---

# Prompting agents

When you hand work to another agent, you're handing it to someone who is probably as good at the job as you are,
but who just walked into the room. It hasn't seen your conversation, doesn't know what you tried yesterday, and
can't ask what you meant. Everything it knows about the task is what you wrote, plus whatever it happens to find
in the files. This skill calls that agent the reader, and anything you write for it a prompt: a brief, a goal, a
system prompt, an instruction file.

That gives a prompt two ways to fail. You can tell the reader how to do work it already knows how to do, which
limits it to what you thought of. Or you can leave out something it needed and had no way to find. Almost
everything below is one of those two mistakes, so before you send a prompt, read it once as if you had seen
nothing else.

## What the reader needs from you

Start with what the work is for. A sentence is enough. When the reader meets a case you didn't anticipate, the
purpose is what it decides with.

Then say what done looks like, and how anyone will know: a test that passes, a build that succeeds, a verdict
written to a file, a screenshot next to the design. Without a check, the reader stops when the work looks
finished, which is not the same thing. If done includes running the result and fixing what breaks, say so,
because some models hand back their first version otherwise. Ask for the evidence, meaning the command and its
output, rather than the sentence "all tests pass".

Next come the boundaries: the things the reader must not do, or must get approval for. Take them from the
project's rules and from what the person told you, not from your own caution. Name the exact action. "Don't
push to `main`" is clear, while "be careful with git" makes the reader hesitate over every git command. Put any
exception inside the rule itself: write "get approval before you run a migration", not "never run a migration"
with a separate line saying approved ones are fine. Give the reason in a clause, so the reader can apply the rule
to cases you didn't list. If a boundary sits close to ordinary work, say where it stops: "Get approval before you
touch the production database. The test database is throwaway, so use it freely." Don't list the ordinary work
itself; the reader already assumes that.

The part most often missing is whatever lives only in your head: decisions made in conversation, approaches
already tried and ruled out, which source is the authoritative one, how to reproduce the bug, which of two
reasonable designs the person prefers. Where you have the thing itself, such as a path, a log or a screenshot,
hand it over rather than describing it. Mark quoted logs and web text as quotes, so the reader doesn't take them
for instructions. And check your claims before you pass them on, because once a guess is in a prompt, it becomes
the reader's requirement.

Finally, say where the result should go. Specify a format only when a program or another agent will read it.
Otherwise ask for the main finding first, with what was verified kept apart from what is suspected.

## What to leave out

Most of what makes a prompt long also makes it worse, and the reason is the same each time: the reader treats
everything you wrote as something it is meant to act on.

Invented steps are the clearest case. A reading order, a technique or a set of report sections limits the
reader to your plan. Give steps only when the order is the task, as in a data migration. A list that *is* the
task, such as the browsers that must work or the cases the person named, is different and stays.

Emphasis and repetition backfire in the same way. Capitals, "IMPORTANT", "be thorough", or a caution stated
three times don't make a rule stronger. They make the reader apply it too widely, until it is asking for
approval on things that don't need it.

"Think hard" is different: it does nothing, because how hard a model reasons is a setting outside the prompt.
"Answer without deliberating" does nothing either, for the same reason.

Reminders to do what the reader does anyway, such as "run the tests", "check your work" and "keep going", were
useful on older models. On current ones they cause too much testing and work nobody asked for. A check that
defines done is different, and it stays.

When you ask for a review or an investigation, leave out your own conclusion. A reader handed the answer tends to
come back agreeing with it.

When you have an old prompt to update, don't fix it line by line. Start again from the purpose, what done
looks like, the boundaries and the missing context, and copy across only the facts that are still true.
Editing keeps the old emphasis and lists along with the facts.

## How to write it

Write for a reader who is clever but new to the subject, and who can't interrupt to ask what you meant. The style
to copy is Randall Munroe's in "What If?", without the jokes. He explains hard things in plain words, starts
from something the reader already knows, and moves one step at a time, so nothing has to be taken on faith.

In a prompt, that comes down to a few habits:

- Put the main thing first.
- Use ordinary words. Keep a technical term only when it is the name of the thing.
- Define a term once, then keep to that word. A reader who sees "module" and then "component" has to wonder
  whether they are two things.
- Explain a new fact next to the ordinary case it differs from: "Normally a subagent starts with your
  instruction files. The `Explore` agent starts without them, so put everything it needs in the brief."
- Make it clear whose job each action is. "The tests are run before merging" could mean the reader runs them or
  that CI already does, while "run the tests before you merge" leaves no doubt.
- Prefer a path, a number or one example over a description of them.
- Write whole sentences. A prompt stays short through what you leave out, not by squeezing what's left into
  labels.

[Writing style](references/writing-style.md) shows each habit at work in longer examples.

Here is the difference on a small review request:

> Before: "CRITICAL: Auth must be thoroughly reviewed!! Check everything carefully and make sure nothing is
> broken. Be comprehensive."
>
> After: "Review the diff on branch `auth-refresh` against `docs/auth-spec.md`. The change makes a session renew
> its access token when the token is within five minutes of expiring. Report any requirement in the spec that the
> diff does not meet, and any case where a user could be logged out mid-request. Leave style alone. For each
> finding, give the file and line and say whether you confirmed it by running something."

## Where an instruction belongs

An instruction works best close to the moment it applies, so where you put it matters as much as how you word
it.

| The instruction | Put it in |
|---|---|
| Applies to one task | The prompt |
| A fact needed in every session in this repository | The instruction file (`CLAUDE.md`, `AGENTS.md`) |
| A procedure needed for some tasks | A skill |
| Must hold through a long unattended run | The goal for that run, or a notes file the reader keeps re-reading |
| Must hold every time, with no exceptions | A hook, a test or a permission rule, which the program running the model enforces whatever the model decides |

If you keep strengthening a line and the reader keeps missing it, the wording isn't the problem. The line is in
the wrong place. Move it further down the table, where less depends on the reader remembering it.

## Write for the model that will read it

The four current models respond differently to the same prompt: one stops too early where another pushes too
hard. Each has habits you can predict, so before you write, find out which model will run the prompt and read
its file:

- Claude Opus 5.5: [claude-opus-5-5.md](references/models/claude-opus-5-5.md)
- Claude Fable 5.2: [claude-fable-5-2.md](references/models/claude-fable-5-2.md)
- GPT-6 Astra and GPT-6.1 Sol: [gpt-6.md](references/models/gpt-6.md)

If the model is newer than these, read its vendor's prompting guide instead. These files go out of date faster
than anything else in this skill.

If an agent still goes wrong, look for the line that caused it before you add a new one. Deleting a stale
caution usually fixes more than adding "don't ask".

When you move to a new model, re-read everything that carries over: system prompts, skills, instruction files,
saved notes, and text the host adds to messages. Lines written to push an older model now push too hard, so
check each one against "What to leave out" above. In Claude Code, `/doctor prompt-audit` does this reading for
you and also reports files that contradict each other. In Codex, ask the model to audit your skills and
`AGENTS.md` against OpenAI's migration guide.

## More

- [Kinds of prompt](references/kinds.md): what a subagent brief, a goal for a long run, a review request, a
  steer and a system prompt each add. Read the section for the kind you are writing.
- [Instruction files](references/instruction-files.md): read before you write or trim a `CLAUDE.md` or
  `AGENTS.md`.
- [Writing style](references/writing-style.md): each writing habit at work. Read it before you write anything
  long.
