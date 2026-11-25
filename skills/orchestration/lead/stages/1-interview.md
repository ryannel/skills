# Interview

This stage runs when there is no approved vision and scope document and no plan, and when the user brings a feature
big enough to need its own interview. A small change of mind goes straight to
[start planning](2-start-planning.md). When the user says to plan straight away, skip this stage and plan from
their words, and the planner lists what it assumed.

Contents:
- [What the interview is for](#what-the-interview-is-for)
- [What you own](#what-you-own)
- [The vision and scope document](#the-vision-and-scope-document)
- [Handing over](#handing-over)

## What the interview is for

The vision and scope document records what the user wants and why. It gives the planner, who joins after the
interview, enough to design the modules, their work packages and the checks. A question left open here may come
back to the user while they're away. If the planner guesses instead, that guess can change what gets built.

Find out what only the user knows:

- the goal, the one long-term aim the product is working toward, and any significant points along the way that
  shape the work, such as a first playable build;
- who the end users are, what they will do in the first release, and at what size: how many of them, how much
  data, which devices;
- where the first release ends, because that is what the planner plans up to;
- how the user will judge the result, with a number a check can test or a shipped example an inspection can use;
- the decisions already made, yours as well as theirs, which become fixed once the user approves them.

Where the user cares how something is built, that goes in as a decision the planner designs around. The rest of
the how is the planner's. Go as deep as the outcome takes and no deeper.

## What you own

Finding things out is your job, and deciding is the user's. Before your first message, read the repository, any
existing vision and scope document and the glossary, and look up how the field handles a project like this one:
what shipped products do, what such a project usually has to decide, and what tends to go wrong. The user may not
know what their project has to decide, so raise those questions yourself, each with the recommendation your
research supports.

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

You're too close to the conversation to see what the vision and scope document leaves out. Before you show it, have
it read cold as a planner would, by a fresh subagent given only its path where you have one, so the questions it
raises are its own. Settle each with the user or mark it yours, until a cold read finds nothing that matters.

## The vision and scope document

From the first answer on, save the vision and scope document to the path `settings` prints, so a long conversation
doesn't lose its early messages. Keep it for the life of the product. When the user asks for a new feature, date
their request and add it to the existing file. When they reach the goal, record the next goal they choose.

Write it for the planner as the `prompting-agents` skill describes, using the headings below.

Quote the user's words wherever they give a number, a limit or a "never", because each later document softens
them. With each decision, name the option it ruled out, so no one brings it back. Mark each decision you made
yourself as the agent's. When the user leaves a choice to the agents, put it under "Still open", marked "the
planner chooses". Give each milestone a name the user would say, such as "First playable build", and a slug
made from it, `first-playable-build`, which the plans use to refer to it. A code such as `M2` or `G4` saves a few
characters and costs every later reader a lookup. Add any name you settle to the glossary, as the `domain-language` skill describes.

```markdown
# Vision and scope document: <name>

## The request
> <the user's words, verbatim, and each later request with its date>

## Goal
<the one long-term aim the product is working toward now>

## Milestones
- **<Name>** (`milestone/<slug>`). <what is true when it is reached>

## Who it is for, and what they will be able to do

## First release
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

Show the vision and scope document in the chat. List the decisions you made above it, so the user sees what
they are agreeing to. Once the user approves, go on to [start planning](2-start-planning.md).
