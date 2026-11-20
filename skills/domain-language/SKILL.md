---
name: domain-language
description: Agrees one name for each thing in a project with the human, preferring the field's established terms, keeps the names in GLOSSARY.md, and keeps code, plans and chat using them. Use when people or agents use different words for one thing or one word for two things, when a project's terms have become confusing, before planning a project with many concepts, or when asked for a glossary, ubiquitous language or domain language. Not for naming one variable or function, or for a throwaway script.
---

# Domain language

A project's domain language is the set of names that the human and the agents agree to use for the things in it.
The human is the person the project is being built for. The names are kept in one file, the glossary. This skill
is for finding the names, agreeing them with the human, writing them down, and keeping to them.

Names matter more with agents than with a team of people. Each agent starts new and knows only what is in the
files, so a name that isn't written down gets invented again by the next agent, slightly differently. After a few
sessions the plan says "claimed", the code says `pending_review` and the human says "ready for review", and nobody
is sure those are one thing. The glossary is as much for the human, following the work, as for the agents doing
it.

Where the field the project works in already has a name for a thing, that is the name to use. Someone who knows
the field, joining the project later, should recognise its plans, code and screens at once, and the agents read
the field's own words in everything they were trained on. The human may be new to the field, so agreeing the
names is also a chance to teach them the words their field uses.

## How much to do

Fit the work to the project.

- A job that takes a day, or a throwaway script, needs no glossary.
- A small tool with five things in it needs five entries and no conversation. Write them, and show them to the
  human in the chat.
- A project where the human, the plans and the code already disagree, or a new project with many things to name,
  needs the conversation below.

## What finished looks like

1. The main thing the project does can be written as numbered steps, using only everyday words and names that
   have an entry in the glossary. Each step says who or what does it. The people and programs involved, the steps
   and the statuses need names, not only the objects.
2. The human has seen those steps in the chat and agreed the names in them. Every entry the human hasn't agreed is
   marked `Proposed:`.
3. The documents still in use follow the names. A search for each word listed under `Avoid` finds it only in the
   glossary, in records of the past, and in a sentence that gives a stored name.
4. A later session, which won't have this skill loaded, can find the glossary from the project's agent
   instructions file and knows what to do with it.

## Which name to choose

The aim is a name that someone who knows the field understands on sight, and that the human can learn once and
then use.

- The field's established term comes first. If libraries say "hold" and "loan", accountants say "journal entry"
  and "ledger", and warehouses say "pick", "pack" and "ship", those are the names, even where the human or the
  code uses another word. Where the field has competing terms, take the one its main standard or its most widely
  used tools use, and list the others under `Avoid`.
- A name people already know from the tools they use counts as established. "In Progress", "Blocked" and "Done"
  need no explaining.
- Where the field has no term, because the thing is particular to this project, the human's own word comes next.
  Where they have none either, choose the explicit, familiar name, even when it is longer: "Ready for Review"
  rather than "claimed", and "Needs Human Feedback" rather than "attended". A short name that has to be explained
  is worse than a long one the reader understands on sight.
- The human can keep their own word over the field's, for instance because their customers say it. That is their
  decision. Write the field's term into the entry's first line, so a newcomer can still connect the two.
- Leave a good short name alone. Turning every name into a phrase makes the text harder to read.
- One thing has one name. When two names are in use, choose one, and list the other under `Avoid`.
- One name means one thing. If "account" means both the customer and their login, those are two entries with two
  names. A status that covers two causes is split the same way.
- Name only what is particular to this project. "Timeout" and "cache" get an entry only if the project gives them
  a meaning of its own.

The names most likely to need replacing are the ones an agent made up in the middle of a task and kept using,
such as "the sweep" for a nightly cleanup or "the shelf" for orders waiting on stock. Nobody told the human what
they meant.

## Finding the names

1. Hear the human first. You need to know what things, steps and statuses exist and what the human means by
   each, before you can look up what the field calls them. Often the request and the repository already tell you.
   Where they don't, ask the human to walk through one real run of the main job, from start to finish: who does
   what, with what, in what order. Ask only about what you can't tell, and recommend names for the rest in the
   same message, so the human isn't asked to repeat what they already said.
2. Collect what the repository uses yourself. Look at the data (tables, columns, saved files), the code (types,
   status values, routes, commands), the text on screen, and the README and docs. Note where each name came from.
   Finding these is your job, not the human's. Read the declared model, the schema and the core types, rather
   than every file. The code shows which names are in use, but it doesn't decide which name is right.
3. Look up what the field calls each thing. Search for the field's standards and glossaries, its main textbooks or
   references, and the documentation of its most widely used tools, and see how practitioners write about it.
   Note the source for each term, so you can tell the human where it comes from. Check that the field's term means
   the same thing as the human's: a near match with a different meaning is worse than no match. Do this before
   your first message about names, so the human hears the field's term the first time a name comes up. If you
   can't search the web, say which names you couldn't check.
4. Find the clashes. There are four kinds:
   - one thing with several names, such as a table `purchases`, a type `Order` and a button that says "Basket";
   - one name for several things;
   - a thing with no name, which shows up as a phrase repeated in place of a word ("the orders that are paid but
     not yet packed"), or as a rule described step by step ("if it's paid and nobody has picked it up and it's
     past noon…");
   - a name only the code or an agent uses, which the human has never said;
   - a name in use where the field has an established term for the same thing.

## Settling them with the human

Put the clashes to the human in the chat, a few at a time, in rounds. Use the host's question tool if it has one.
Write the names into the message itself, because a human following the work in a chat won't open a file to read
them.

- Where the field has a term, recommend it, in one line that says what it means and where it comes from:
  "Libraries call this a hold: a book kept for a patron to collect. Use Hold rather than Reservation?" The human
  learns the word as it is agreed. Where their word already is the field's term, say so and move on.
- Where the field has no term and the human's telling gave a word, that word is the name.
- Where neither gave one, ask what they call the thing, and suggest nothing in that message, because a human
  tends to take the first name offered. Suggest a name in your next message only if they have no word for it.
- Where several names are in use, show them side by side and recommend one, worded so that "yes" accepts it:
  "The table is `purchases`, the type is `Order` and the button says Basket. Call all three an Order?"
- Where two things sit close together, invent a case that falls on the line between them: "A customer pays for
  three items and one ships a week late. Is that one Order or two?" The answer gives the `Not:` line, which says
  how a thing differs from its nearest neighbour.
- When the human states a rule about a thing ("an Order can't be changed once it's paid"), search once for the
  code that enforces it. If the code disagrees, say so before you write the entry. If nothing enforces it, say
  that too. The glossary records what the human means, so don't change it to match a bug, and don't fix the bug
  unasked either.
- When the human can't settle a clash yet, put it under `## Open questions` in the glossary, with where each name
  is used, and carry on.
- When the human changes only the spelling of a name, it's a rename. When they change what it means, the entry
  may need to split in two.

Write each entry as soon as its name is agreed, so that a conversation that stops halfway still leaves the agreed
names on disk.

Then show the names in use. Write the main job as numbered steps that use the names, each step saying who or what
does it. A table of terms is hard to judge, because a name shows what it means only when it is used. The steps
also show what is missing: if you can't write a step without a new word, that word needs an entry. The human's
reply to the steps agrees the names in the steps, and not entries they haven't been shown.

You can't confirm on the human's behalf that a word is right. A field term the human accepted once you explained
it is sound. A name you made up and the human only accepted is weaker, and an objection is worth more than a
reluctant "ok".

## The glossary file

The glossary is `GLOSSARY.md` at the root of the repository. If the project already keeps a glossary somewhere
else, such as a plans folder, use that one, because two glossaries drift apart. Create the file when the first
name is agreed.

```markdown
**On Hold**
A book that a patron has asked for, and that is waiting on the shelf for them to collect.
Not: On Loan. A book on hold has not left the library.
Avoid: reserved, claimed
Source: the standard library term, as used by circulation systems such as Koha and Evergreen
Stored as: `claimed`, in the `status` column of the `loans` table
Proposed: by the agent, 2027-03-12. Not yet agreed by the human.
```

- The first line after the name says what the thing is, in one or two sentences that make sense to a reader with
  nothing else open.
- `Not:` names the thing it is most easily confused with, and the difference. Leave it out when there is none.
- `Avoid:` lists the other names that have been used for it.
- `Source:` says where a term from the field comes from, so a reader can check it and learn more. Leave it out
  for a name particular to the project.
- `Stored as:` gives the name in the code, the data, an API or a command, when that differs.
- `Proposed:` marks an entry the human hasn't agreed. It starts with that word, so a search finds every one, and
  it goes when the human agrees. An agent reading the glossary treats every other entry as the human's decision,
  so an unmarked guess is worse than no entry.

Use a bold name with lines under it rather than a table, so a search for a word finds its whole entry and a change
to one entry is one small diff.

The glossary holds names and what they mean, and nothing else. Decisions, plans, findings and how a thing is built
go in other files. A glossary that takes those in gets rewritten after every answer, until it is a second plan that
disagrees with the first. A mismatch you found between the code and the human's rule goes in your report, not in
the file.

A large project keeps one glossary. If two parts of it really do use one word for two different things, give each
part its own heading, and say in each entry which part it belongs to.

[The glossary format](references/glossary-format.md) has a worked example of each kind of line, the open questions
and retired names sections, the text for the agent instructions file, and the drift checks. Read it when you
create a glossary or add the pointer to it.

## Names that already exist in code and in saved data

A new name in the glossary renames nothing. A name that already exists in the code, a saved file, a database
column, an API or a command that people type stays as it is, because existing records and callers use it. Record
it under `Stored as`. Documents and the chat use the glossary's name, and give the stored name once, where the
reader will meet it.

In code, keep to the word the code already uses for a thing. If the code has `createBooking`, the function that
moves one is `moveBooking`, whatever the glossary calls a booking. A thing that is new to the code takes the
glossary's name. Comments count as code here. List any that use a word under `Avoid` in your report, rather than
editing them.

Renaming what is stored is building work. The human asks for it, and it is planned like any other change, with
care for anything outside the project that reads the name.

## Keeping to it

Read the glossary before you write a plan, a design, text a user will see, or a report to the human.

When you need a name for a new thing, look for an entry first. If there is none, choose a name by the rules above,
add the entry with a `Proposed:` line in the same change, and carry on. Name the entry in your report, and say if
the name is now in the code, so the human knows a different pick would mean a rename. This works whether or not
the human is there to ask.

When the human uses a word that disagrees with the glossary, ask at that moment: "The glossary calls that an
Order. Do you mean an Order, or something new?" Either they meant the same thing, or the glossary is missing an
entry. When you notice you have drifted from the glossary yourself, use its name from your next message on.

When you write a brief for another agent, copy the entries it needs into the brief, word for word. The other
agent may never open the glossary.

Three things are the human's decision: changing an agreed name, removing an agreed entry, and merging two agreed
entries. Keep using the agreed names, and put what you would change, and why, in your report. When the human does
change a name, move the old one to `Avoid`, leave logs, finished reviews and other records of the past as they were
written, and update the documents still in use, changing the names and keeping every fact.

Entries have to leave the glossary as well as arrive, or it grows until nobody reads it. Propose removing an entry
when the thing it names is gone, and say where it went: merged into another entry, renamed, or deleted from the
project. If you can't tell where it went, leave it.

## Making later sessions find it

A later session has to find the glossary without this skill loaded. Add a short section to the project's agent
instructions file, `AGENTS.md`, and to `CLAUDE.md` if the project has one, that says where the glossary is and what
to do with it. If the project has Cursor rules in `.cursor/rules/`, add it there too, as a rule that always applies.
Say in your report which files you changed. Don't create an instructions file the project doesn't use for this
alone; tell the human where the pointer would go instead.

## Checking for drift

Two checks find drift, and both are cheap enough to run before you report:

- each word under `Avoid`, searched for in the documents still in use, leaving out the glossary and records of the
  past;
- each name under `Stored as`, searched for in the code, because a stored name that no longer exists means the
  glossary is out of date the other way.

If the human wants a name kept out for good, and nothing stores it, offer to turn the first check into a test that
fails when the name appears. Otherwise, say plainly that nothing enforces the glossary, so nobody counts on a check
that isn't there.
