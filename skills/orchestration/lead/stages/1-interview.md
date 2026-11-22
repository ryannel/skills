# Interview

This stage runs when there is no approved brief and no plan, and when the user brings a feature big enough to need
its own interview. A small change of mind goes straight to [start planning](2-start-planning.md). When the user says
to plan straight away, skip this stage and plan from their words, and the planner lists what it assumed.

Contents:
- [What the interview is for](#what-the-interview-is-for)
- [What you own](#what-you-own)
- [The brief](#the-brief)
- [Handing over](#handing-over)

## What the interview is for

The outcome is a project brief the user has approved, from which a planner can plan without working around a hole
in what the user wants.

The planner is a new session. The brief is all it knows of the goal, and it designs the best way there: the modules,
the milestones and the checks each milestone is judged by. A question the brief leaves open comes back to the user
later, through you, often while they're away. Worse, the planner may work around it, and each workaround is a choice
about the goal the user didn't make. A few of those, carried through every module, are enough to build the wrong
thing well.

So the brief says what the user wants and why, and holds what only the user knows:

- who the end users are, what they will do in the first release, and at what size: how many of them, how much
  data, which devices;
- where the first release ends, because the planner plans up to "What finishes this goal" and no further;
- how the user will judge the result, each judgement pinned to a number a check can test or a shipped example an
  inspection can use as its reference, because a check is made only as strict as the brief says;
- the decisions already made, which become fixed once the brief is approved, yours as much as theirs.

Where the user cares how something is built, that goes in as a decision the planner designs around. The rest of
the how is the planner's. Go as deep as the outcome takes and no deeper.

## What you own

Finding things out is your job, and deciding is the user's. Before your first message, read the repository, any
existing brief and the glossary, and look up how the field handles a project like this one: what shipped products
do, what such a project usually has to decide, and what tends to go wrong. The user may not know what their project
has to decide, so raise those questions yourself, each with the recommendation your research supports.

Ask only what would change what gets built and only the user can answer. Decide the rest yourself and say so, with
your reason, so they can correct it. A number or a limit the project turns on, such as how old is too old, is the
exception: ask for it rather than proposing one, because a sensible default keeps the user's own rule from being
said. A technical choice the user names is their decision.

How you run the conversation is yours. A few habits keep the user's answers quick and their reasons on record. Ask
the goal first, open and with no recommendation, because once options are on the table the user picks one and the
reason goes unsaid. Number the questions across the whole interview (Q1, Q2, never reused), so the user can answer
"Q3 yes, Q4: weekly". With each choice, say what it commits the project to, the way someone who has built one would,
then what you recommend, because the user can't weigh a cost they can't see:

> **Q2: Which platforms should it run on?**
>
> What it means: a game that looks AAA draws its lighting with each platform's own graphics system, so every
> platform you add means writing and tuning that lighting again, for months.
>
> I recommend: Windows PC first, and PS5 later.

Say what follows from the user's answers, with the step that led there, and record what they leave standing as your
decisions: "It's for your eight-year-old on an old iPad, so I've taken it that she plays by touch, with no accounts
and no typing." Make bigger jumps as the answers come in, and keep asking wherever a jump would rest on your
preference rather than on what they said.

You're too close to the conversation to see what the brief leaves out. Before you show it, have it read cold as a
planner would, by a fresh subagent given only its path where you have one, so the questions it raises are its own.
Settle each with the user or mark it yours, until a cold read finds nothing that matters.

## The brief

Save the brief as `BRIEF.md` where `settings` says the brief goes, from the first answer on, so a long conversation
doesn't lose its early messages. If a brief is already there, the request is a feature of that project: add to the
brief rather than replace it, and date the new request. The planner reads the brief by its headings, so keep them.

Quote the user's words wherever they give a number, a limit or a "never", because each later document softens
them. With each decision, name the option it ruled out, so no one brings it back. Mark each decision you made
yourself as the agent's. When the user leaves a choice to the agents, put it under "Still open", marked "the
planner chooses". Add any name you settle to the glossary, as the `domain-language` skill describes.

```markdown
# Project brief: <name>

## The request
> <the user's words, verbatim, and each later request with its date>

## Goal

## Who it is for, and what they will be able to do

## What finishes this goal
<the first release: what the end users will be able to do when it is done>

## Later
<the work agreed for after the first release>

## Decisions
1. <decision>, rather than <the option ruled out>. The user, Q3: "<their words>"
2. <decision>, rather than <the option ruled out>. The agent's, because <reason>.

## How it will be judged
<what would be a failure even if it works, each with its number or shipped example>

## Never part of this

## Must not change

## Where it runs

## Still open
<what the user can't decide yet, each with what they agreed to proceed with meanwhile; or "the planner chooses">
```

## Handing over

Show the brief in the chat, with the decisions you made yourself listed above it, so that approving the brief
confirms them. Once the user approves, go on to [start planning](2-start-planning.md).
