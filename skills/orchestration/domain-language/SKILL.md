---
name: domain-language
description: Agrees one name for each thing in a project with the owner, and keeps those names in a glossary that the plans, the code and the chat all follow. Use when the owner and the agents are using different words for the same thing, when the terms in a project have become confusing, or when someone asks for a glossary or a domain language. Not for naming one variable or function.
---

# Domain language

A project's domain language is the set of names that its owner and its agents agree to use for the things in it.
The owner is the person the project is being built for. The names are kept in one file, the glossary. Use this
skill to agree the names with the owner, to write them down, and to keep to them.

Names matter more with agents than with a team of people. Each agent starts new and knows only what is in the
files. A name that isn't written down gets invented again by the next agent, slightly differently. After a few
sessions the plan says "claimed", the code says `pending_review` and the owner says "ready for review", and
nobody is sure those are one thing.

## Where the glossary is

Some projects are built with the orchestrate set, a group of skills in which separate agents plan, build and
review. Such a project has a file of settings, `ORCHESTRATE.md`, at its root, and a plans folder that the
settings name on their `Plans:` line (`docs/modules` unless they say otherwise). In that kind of project, or one
that is about to be planned that way, the glossary is `GLOSSARY.md` in the plans folder. The agents that build
work on their own branches, so a glossary you write in the owner's chat has to reach the main branch before they
can read it. Run the set's script to merge it:
`python3 <the build skill's folder>/scripts/agent_loop.py adopt --worktree <repo> <plans folder>/GLOSSARY.md`.

In any other project it is `GLOSSARY.md` at the root of the repository.

## What finished looks like

1. The main thing the product does can be written as numbered steps, using only everyday words and names that
   have an entry in the glossary. Things that need a name include the people and programs involved, the steps
   and the statuses, and not only the objects.
2. The owner has seen those steps in the chat and agreed to the names in them. Any entry the owner has not seen
   in a message is marked as proposed.
3. The plans and documents still in use follow the names. To check, search them for each name listed under
   `Avoid`, for example `grep -rniw "claimed" docs`. A match is fine in three places: the glossary, a record of
   the past, and a sentence that gives a stored name.

Fit the work to the project. A small tool with five things in it needs five entries and no conversation: write
them, and show the owner. A job that takes a day may need no glossary at all. A project where the owner, the
plan and the code already disagree needs the conversation below.

## Which name to choose

Most of these rules come from names an owner rejected.

- The owner's own word wins. If the owner already calls a thing something, that is its name, even where you
  would have picked another.
- Otherwise choose the explicit, familiar name, even when it is longer. One owner replaced "claimed" with "Ready
  for Review", and "attended" with "Needs Human Feedback". A short name that has to be explained is worse than a
  long one the reader understands on sight.
- A name people already know from the tools they use beats a new one. "In Progress", "Blocked" and "Done" need
  no explaining.
- Leave a good short name alone. The same owner kept "Blocked" and "Done", and said a draft that turned every
  name into a phrase had gone too far.
- One thing has one name. When two names are in use, choose one, and list the other under `Avoid`.
- One name means one thing. If "account" means both the customer and their login, those are two entries with two
  names. A status that covers two causes is split the same way.
- Name only what is particular to this project. "Timeout" and "cache" get an entry only if the project gives
  them a meaning of its own.

The names most likely to need replacing are the ones an agent made up in the middle of a task and then kept
using: "the loop", "the ladder", "parked". The owner was never told what they meant.

## An entry

```markdown
**On Hold**
A book that a member has asked for, and that is waiting on the shelf for them to collect.
Not: On Loan. A book on hold has not left the library.
Avoid: reserved, claimed
Stored as: `claimed`, in the `status` column of the `loans` table
Proposed: by a builder, 12 March 2027. Not yet agreed by the owner.
```

- The first line after the name says what the thing is, in one or two sentences.
- `Not:` names the thing it is most easily confused with, and the difference. Leave the line out when there is
  no such thing.
- `Avoid:` lists the other names that have been used for this thing.
- `Stored as:` gives the name in the code, a file or an API, when that differs from the entry's name.
- `Proposed:` marks an entry the owner hasn't agreed, and starts with that word so that a search finds every
  one. Remove the line when the owner agrees. An agent that reads the glossary treats every other entry as the
  owner's decision, so an unmarked guess is worse than no entry.

The glossary holds names and what they mean, and nothing else. Decisions, plans and how a thing is built go in
other files. In one widely used skill library this was the most-reported problem: agents rewrote the glossary
after every answer, until it was a second plan.

## Agreeing the names with the owner

1. Collect the names before you ask anything. Take them from the owner's words in the chat, and from the
   repository: identifiers, text on screen, documents, table and column names. Finding these is your job, not
   the owner's. Code shows which names are in use. It doesn't decide which name is right.
2. Get the owner's own words before you propose any. If the chat doesn't already hold them, ask the owner to
   say, in their own words, what the product does from start to finish. That one question gives you their word
   for most of the things at once. A name that appears only in the code or the documents is not the owner's
   word until they use it. In two test conversations the agent proposed tidy names of its own, the owner
   accepted them, and the words the owner uses every day were never heard.
3. Find the things whose names clash, the names the owner didn't use, and the things that have no name and keep
   being described with a phrase. Put those to the owner in the chat, a few at a time. Where the owner's
   telling gave a word, that word is the name. Where it gave none, ask what they call the thing, with no
   suggestion in that message, because the owner tends to take a name that is offered. Suggest one in your next
   message only if they have no word for it. Where the owner uses two names themselves, say which you recommend and
   why. Write the names into the message itself, because an owner who follows the work in a chat won't open a
   file to read them.
4. Show the names in use. Write the main thing the product does as numbered steps that use the names, with each
   step saying who or what does it. One owner was shown a table of terms, and could not tell what the terms
   meant until the same terms appeared in steps. The steps also showed that a term was missing. If you can't
   write a step without a new word, that word needs an entry.
5. When the owner objects to a name, offer others and take the one they pick. Write each entry as soon as its
   name is agreed.

The owner's reply to the steps agrees the names that are in the steps. It doesn't agree entries they haven't
been shown.

When the owner uses a word that disagrees with the glossary, say so at that moment: "The glossary calls that an
Order. Do you mean an Order, or something new?" Either the owner meant the same thing, or the glossary is missing
an entry.

## Names that already exist in code and in saved data

A new name in the glossary renames nothing. A name that already exists in the code, a saved file, a database
column, an API or a command that people type stays as it is, because existing records and callers use it.
Record it under `Stored as`. Documents and the chat use the glossary's name, and give the stored name once, at
the place the reader will meet it.

Comments in the code count as code here. Leave them as they are, and list in your report any that use a name
under `Avoid`, because the owner asked for names and not for a change to the code.

In code, keep to the word the code already uses for a thing. If the code has `createBooking`, the function that
moves one is `moveBooking`, whatever the glossary calls a booking. A thing that is new to the code takes the
glossary's name.

Renaming what is stored is building work. The owner asks for it, and it is planned and built like any other
change.

## Keeping to it

Read the glossary before you write a plan, a design, text a user will see, or a report to the owner.

When you need a name for a new thing, look for an entry first. If there is none, choose a name by the rules
above, add the entry with a `Proposed:` line in the same change, and name it in your report. Carry on with the
work. Say in the report that the name is now in the code, so that the owner knows a different pick would mean a
rename.

Three things are the owner's decision: changing a name that has been agreed, removing an agreed entry, and
merging two agreed entries. Keep using the agreed names, and put what you would change, and why, in your
report.

When the owner does change a name, put the old one under `Avoid`. Leave logs, finished reviews and other
records of the past as they were written. In a project built with the orchestrate set, only the agent that
plans, called a planner, changes the plan files, so the agent the owner chats with gives a planner the owner's
words. The set also keeps each piece of work's checks and results in JSON files beside the plans. Don't edit
those to change a name. In any other project, update the documents still in use yourself. Change the names in a
document and keep every fact it states. In one test the agent cut two steps from an overview because the owner
had no name for them.

Entries have to leave the glossary as well as arrive. One project's glossary took 380 lines of additions and 11
of removals over 25 changes. Propose removing an entry when the thing it names is gone.

A later session has to be able to find the glossary without this skill. In the orchestrate set, each agent's own
skill tells it to read `GLOSSARY.md` in the plans folder. In any other project, add one line that names the file
to `AGENTS.md`, and to `CLAUDE.md` if the project has one, and say in your report that you did.

If the owner wants a name kept out for good, and nothing stores it, make that a check: a command in the
project's tests that fails when the name appears in the documents.

A large project keeps one glossary. If two parts of it really do need the same word for different things, give
each part its own heading, and say in each entry which part it belongs to.
