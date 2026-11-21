# Interview

This stage runs when there is no approved brief and no `ORCHESTRATE.md`. Interview the user and write the project
brief that planning starts from. When the user says to plan straight away, skip it, and the planner lists what it
assumed.

Contents:
- [What the planner does with the brief](#what-the-planner-does-with-the-brief)
- [When you're done](#when-youre-done)
- [Research first, then ask](#research-first-then-ask)
- [Map the dialogue](#map-the-dialogue)
- [Check the brief before you show it](#check-the-brief-before-you-show-it)
- [The brief](#the-brief)
- [Handing over](#handing-over)

## What the planner does with the brief

The planner is a new session that reads the brief as a description of what the user wants to accomplish, and
designs the best way to get there: it breaks the work into modules and milestones, and writes the checks each
milestone is judged by. It can't ask the user anything, so the brief is all it knows of the goal.

The brief says what the user wants and why. Where the user cares how something is built, that goes in too, as a
decision the planner designs around. The rest of the how is the planner's to choose. What the planner can't work
out is what only the user knows:

- Who the end users are, what they will do in the first release, and at what size: how many of them, how much
  data, which devices.
- Where the first release ends. The planner plans up to "What finishes this goal" and no further.
- How the user will judge the result. Each check is made as strict as that, and a number goes into a check only if
  the brief gives one.
- The decisions already made. One in the user's words is fixed. One marked as the agent's, the planner may change.

Every hole in the brief is a risk. The planner has to work around it, and each workaround is a choice about the
goal that the user didn't make. A few of them, carried through every module and milestone, are enough for the
project to drift and build the wrong thing, well and on time.

## When you're done

You're done when the user has approved the brief, and the planner could do all of that without working around a
hole in what the user wants. Go as deep as that takes and no deeper: the choices left to the planner should be how
to build it, and anything the user said the planner may choose.

A brief can hold everything the user said and still fall short:

- It contradicts itself: it says "never touch the monorepo" for a tool that has to live there.
- A rule has a gap: it says "archive inactive accounts" but not how long an account must sit unused to count as
  inactive.
- A worry has no measure: it says "scrolling mustn't feel slow" but not how fast is fast enough.
- It leaves out the size: a booking app for one shop and one for a chain of fifty need different plans.

## Research first, then ask

Finding things out is your job. Deciding is the user's. Before your first message, read the repository, an
existing brief and the plans folder's `GLOSSARY.md`. The plans folder is `docs/plans` unless `ORCHESTRATE.md`
names another. Then look up how the field handles a project like this one: what shipped products do, what such a
project usually has to decide, and what tends to go wrong. The user may not know what their project has to decide,
so raise those questions yourself, each with the recommendation your research supports.

Ask the user only what would change what gets built and only they can answer. Decide everything else yourself and
say so, with your reason, so the user can correct it. That includes how to work, such as where a file goes or
whether to look further: do it and say so. A number or a limit the project turns on, such as how old is too old,
does need the user, so ask for it rather than proposing a default, because a sensible default keeps the user's own
rule from being said. Leave how it is built to the planner, unless the user shows they care. A technical choice
the user names is their decision, and goes in the brief.

## Map the dialogue

Run the interview as dialogue mapping, with the brief's sections as the root questions.

Ask the goal first, on its own and open, with no recommended answer, because once options are on the table the user
picks one and the reason goes unsaid. After that, ask in numbered rounds of a few questions each (Q1, Q2 and on,
never reused), so the user can answer quickly with "Q3 yes, Q4: weekly".

With each choice, say what it would commit the project to, the way someone who has built one would, and then
what you recommend. The user can't weigh a choice whose cost they can't see.

> **Q2: Which platforms should it run on?**
>
> What it means: a game that looks AAA draws its lighting with each platform's own graphics system, so every
> platform you add means writing and tuning that lighting again, for months.
>
> I recommend: Windows PC first, and PS5 later.

Between rounds, join the dots. Work out what follows from the user's answers and say it, with the step that led
there: "It's for your eight-year-old on an old iPad, so I've taken it that she plays by touch, with no accounts and
no typing." Invite the user to overturn any of it, and record what they leave standing as your decisions. Each
answer gives you more to reason from, so make bigger jumps as the interview goes on, and ask fewer questions. Keep
asking where a jump would rest on your preference rather than on what the user said, such as their own numbers and
how they will judge the result.

Settle the scope: what the end users will be able to do in the first release, and what comes later. Recommend
where the line falls, and ask what would make the user call this goal finished, because the planner plans to that
line and no further.

Run a pre-mortem: ask the user to imagine the first release has disappointed them, and say why. Their answers
are how they will judge it. Pin each one to a number or a shipped example, so a reviewer can check it.

## Check the brief before you show it

You're too close to the conversation to see what the brief leaves out, so have a fresh subagent read it as the
planner would and list each question about what to build that it would still need answered. Give it only the
brief's path, not your own view, or it will tend to agree with you. With no subagents, reread the brief as if new.

Put each question to the user in another round, or decide it and mark it as yours. Repeat until the reader finds
nothing that matters.

## The brief

Save the brief as `BRIEF.md` in the plans folder, from the first answer on, so a long conversation doesn't lose its
early messages. If a brief is already there, the request is a feature of that project: add to the brief rather
than replace it, and date the new request. The planner reads the brief by its headings, so keep them.

Quote the user's words wherever they give a number, a limit or a "never", because each later document softens
them. With each decision, name the option it ruled out, so no one brings it back. Mark each decision you made
yourself as the agent's. When the user leaves a choice to the agents, put it under "Still open", marked "the
planner chooses". Add any name you settle to the plans folder's `GLOSSARY.md`, preferring the field's established
term.

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
<what would be a failure even if it works, from the pre-mortem, each with its number or shipped example>

## Never part of this

## Must not change

## Where it runs

## Still open
<what the user can't decide yet, each with what they agreed to proceed with meanwhile; or "the planner chooses">
```

## Handing over

Show the brief in the chat, with the decisions you made yourself listed above it. Approving the brief confirms
them.

Once the user approves, go on to [start planning](2-start-planning.md), which commits the brief and starts the planner.
