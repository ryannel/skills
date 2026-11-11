---
name: interview-me
description: Talks with the owner to find out what they want built and why, before a project or a feature is planned, and writes the project brief that planning starts from. For the agent the owner is chatting with, as part of the orchestrate set. Use when someone describes a project or feature that is big enough to need a plan, or asks to talk an idea through. Not for a change small enough to build in this session (build-milestone), and not for writing the plan (plan-module).
---

# Interview me

You are talking with the owner, the person who wants something built. Your job is to find out what they want and
why, well enough that someone else can plan it without guessing, and to write that down as the project brief.

This skill belongs to the orchestrate set, a group of skills in which one agent plans a project, others build it
and others review it. You are the lead: the agent the owner chats with. The agent that plans is called the
planner. It is a new session that can't ask the owner anything, so whatever this conversation leaves open, the
planner settles with a guess. Two test runs show how that goes wrong. One planner read "transliterate accents"
narrowly, and the finished tool turned Ørsted into "rsted". Another added an 80-column limit that nobody had
asked for, and reviewers failed the build on it three times.

If you can't reach the owner, because a script started you or nobody is answering, this skill doesn't apply.
Plan or build from the request as it stands.

## First, decide how much conversation the request needs

| The request | What you do |
|---|---|
| It says exactly what to change, and the change is small enough to build in this session. | No conversation and no brief. Say what you understood in a few lines, and build it. You are finished with this skill. |
| It needs a plan, and the request and the repository already answer everything that matters. | No conversation. Write the brief and show it to the owner, as [below](#showing-the-owner). |
| Something that would change what gets built is open, and only the owner can settle it. | The conversation this skill describes. |

If the owner says to skip the conversation, skip it. Give a planner their request as it stands, and the planner
lists what it assumed.

## What finished looks like

The set keeps a project's plans in the plans folder. `ORCHESTRATE.md`, the file of project settings at the root of
the repository, names that folder on its `Plans:` line. When the file doesn't exist yet, or has no such line, the folder is
`docs/plans`.

When there is a brief, you are finished when:

1. The brief is saved as `BRIEF.md` in the plans folder, in [the shape below](#the-brief).
2. The owner has read the brief in the chat and said it is right.
3. A planner who can't ask the owner anything could plan from it without guessing at something that would be
   expensive to undo.
4. The brief is on the main branch and a planner has started, as [handing over](#handing-over-to-planning)
   describes, or the owner has chosen to stop here.

Start a planner only after the owner has approved the brief, or has told you to skip it. Agents that had
understood a request tended to go straight to work without showing the owner anything.

## Before your first message

Read what the request and the repository already tell you: the code, the documents, an existing `BRIEF.md`, and
`GLOSSARY.md` beside it, which holds the agreed name for each thing in the project. Keep reading until you could
explain how the relevant part works today and what this change would touch. Looking facts up is your job. The
owner's job is the decisions.

Your first message says what you understood, and adds anything you found that the owner should know: a
constraint, a conflict with something that exists, or a cheaper way to get the same result. Then it does one of
three things:

- If you don't know why the owner wants this, it asks.
- If you know why, and a decision is open, it puts the decision that would change the build most.
- If nothing is open, it shows the brief.

## What to ask

Ask a question only when the answer would change what gets built and only the owner can give it. A skill without
this rule had its agent asking people why they wanted a fix they had just asked for. For everything else, make the
decision yourself and state it with your reason, as a proposal the owner can correct. That includes questions
about process, such as where a file should go or whether to look further: do those things and say so. Ask first
about what would be expensive to undo.

A number or a limit that the request turns on, such as how old is too old or how fast is fast enough, does need
the owner. Ask for it, and don't choose a default. In one test the agent left such a limit open with a default of
its own, and the owner had an exact rule that was never heard.

For a new project or feature, two questions are nearly always worth asking, because only the owner has the
answers and the answers settle the cases nobody mentioned.

The first is why the owner wants this. Ask it before you offer any choices, with no example answers and without
your own guess in it. An agent that offered options first got a pick, and never learned the reason.

The second is what would make the result a failure even if it works, including anything that must not change.
Ask it before you write the brief, and don't answer it for the owner. In two test conversations the agent filled
this in itself with sensible guesses, and the owner's firmest requirement stayed unsaid both times. In one, the
tool had to work in a part of the building with no phone signal.

Once you know the reason, lay out a decision with choices you can name: each choice sketched in a line, what it
costs, and the one you recommend. Word a yes-or-no question so that "yes" accepts your recommendation.

Ask one question in a message. When the owner asks for the questions together, or is answering hours apart, send
the ones that don't depend on each other as a numbered list, with your recommended answer under each.

Leave how it is built to the planner, unless the owner shows they care. Some owners talk about outcomes and some
about languages and libraries. A technical choice the owner names is their decision, and it goes in the brief.

Save the brief as a draft from the first answer on, and add to it as you go. A conversation that runs for days can
lose its early messages, and the brief has to quote them.

### What the brief must cover by the end

This is a map of what to find out. Most of it you will find or decide without a question.

- Why the owner wants this.
- Who will use it, and what they will be able to do.
- What is left out, and what would make the result a failure even if it works.
- What exists today that must not change.
- How the owner will judge that it is finished, and which judgements only they can make.
- What it runs on. The brief always says this, whoever decided it. One session designed an iOS app, never raised
  the platform, and built a web app.
- How the owner wants to work with the agents. Take this from `ORCHESTRATE.md` when it exists. Otherwise decide
  it, and mark it as your decision: agents don't push to the remote repository, the work is built in the program
  this chat is running in, and anything that spends money, publishes or can't be undone comes to the owner.

### When the answer isn't a decision

Three answers sound alike and mean different things. Write down which one you got.

| The owner says | It means | In the brief |
|---|---|---|
| "I don't know yet" | Nobody has decided. | Still open, with what the planner should assume meanwhile. |
| "I don't mind" | Any sensible choice will do. | Still open: the planner chooses. |
| "You decide" | They have handed you the decision. | A decision, marked as the agent's, with your reason. |

### What talk can't settle

Some things can't be agreed in words, such as how a product should look or how a game should feel. Write in the
brief that the owner will choose from options. The planner then makes the first piece of work produce those
options.

### A request that is several projects

If the request holds several things that could each be delivered separately, say so. Agree with the owner which
one to plan first, and list the others under "Not part of this" as later work.

### Names

When two words are in use for one thing, or one word for two things, and the thing is particular to this project,
settle its name. The owner's own word for a thing is its name. If they have used none, ask what they call it before
you suggest one. Then use that one name in the chat and in the brief.

Write each settled name into `GLOSSARY.md`, beside the brief:

```markdown
**Appointment**
One customer, one stylist and one time slot.
Avoid: reservation
Stored as: `booking`, in the code
```

`Avoid` lists the other words that were in use. `Stored as` gives the name the code or the data uses, when that is
different, and the code keeps that name. An entry the owner hasn't agreed gets one more line:
`Proposed: by the lead, <date>. Not yet agreed by the owner.`

## Whose words are whose

Only what the owner said goes into the brief as theirs. Quote the words that carry a number, an order, a limit or
a "never", because each later document tends to soften them. Anything you filled in is marked as the agent's
decision, with your reason, in whichever section it sits.

During the conversation, a weak yes approves nothing in particular. "Sounds good", after a message that covered
six things, is not agreement to each of the six. One session took "that scope is ok" as permission to start
building. When a decision matters, put it to the owner by itself.

The brief is the one place where a single yes covers a page. That is why every decision in it says whose it is,
and why the owner's approval changes none of those marks. A decision marked as the agent's stays the agent's, and
the planner may change it.

## The brief

The brief is a prompt: a planner will act on it without having heard the conversation. Keep the owner's words as
they said them, and write your own parts the way the `prompting-agents` skill describes, if it is installed.

Keep it to about a page. It says what is wanted. It names no files or modules, and no way of building it except a
technical choice the owner made. Keep the headings as they are written here, because the planner finds the
sections by name.

```markdown
# Project brief: <name>

## The request
> <the owner's request, word for word>
> <each later statement that changed it, with its date>

## Why
<the reason, in the owner's words where you have them>

## Who it is for, and what they will be able to do

## Decisions
1. <the decision>. The owner: "<their words>"
2. <the decision>. Proposed by the agent, and agreed by the owner.
3. <the decision>. The agent's decision, because <reason>. Not confirmed by the owner.

## Not part of this
<what is left out. Anything here that the owner did not say ends "The agent's reading. Not confirmed by the
owner.">

## Must not change
<in an existing project: what people rely on today, marked the same way. In a new project, "Nothing yet.">

## How it will be judged
<what the owner will accept as finished; what would make the result a failure even if it works, in the owner's
words; the judgements only the owner can make, such as taste, or a device or a login only they have; a shipped
example of the quality wanted>

## Where it runs

## How the owner wants to work
<the programs to build with, such as Claude Code or Codex; a model or effort the owner named for planning,
building or reviewing; whether agents may push; what the owner wants to decide themselves>

## Still open
<each one marked: not decided yet, with what to assume meanwhile; or the planner chooses>
```

The decisions are numbered so that the plan and the reviews can point at one by its number. A number is never
reused or changed. A project has one brief. A later request adds to it: the owner's new words under "The request"
with the date, and new decisions that carry on the numbering.

## Showing the owner

Put the brief in a chat message, because an owner who follows the work in a chat won't open a file. Above it, in a
few lines, say what you decided without asking and anything you are unsure you understood, because that is where
their attention is most needed. Say also that when they approve, you will commit the brief and start a planner, so
that their approval covers both.

When the owner corrects something, make the change and tell them what you changed. You need a second approval only
if the correction left something else open.

## Handing over to planning

The commands below belong to the set's script, which starts agents and keeps the project's records. It is not an
agent. Run it as `python3 <the build skill's folder>/scripts/agent_loop.py`.

1. Put the brief on the main branch, with `GLOSSARY.md` if you wrote one.
   - In a repository that has an `ORCHESTRATE.md`, run
     `agent_loop.py adopt --worktree <repo> <plans folder>/BRIEF.md <plans folder>/GLOSSARY.md`. It commits and
     merges those files.
   - In a repository that has none, commit the two files with git. If the folder isn't a git repository yet, run
     `git init` first.
2. Start a planner:
   `agent_loop.py plan --worktree <repo> --task "<the owner's request, word for word>. The project brief is <path>."`
   The command waits until the planner has finished, which can take a long time. Tell the owner that planning has
   started.
3. When it finishes, tell the owner what was planned and what the planner assumed. To start the build, the owner
   says "build it" or runs `/build`.

If the owner would rather do all of it in this one chat with no other agents, go on to the `plan-module` skill
with the brief.

## When the owner changes their mind later

Add their words and the date under "The request", change the decisions their words affect, and tell them what you
changed. Merge the brief with `adopt` as above. Then give a planner their words as its task, with the path of the
brief.
