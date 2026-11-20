---
name: domain-language
description: Builds and sharpens a project's ubiquitous language with the user, in a glossary that follows the field's standard terms, and fixes code and docs that drift from it. Use when a project has many concepts, when words in the code, docs or conversation are ambiguous or inconsistent, or when asked for a glossary, ubiquitous language or domain language. Not for naming one variable or function.
---

# Domain language

Use domain-driven design's ubiquitous language in this project: one vocabulary that you, the user, the code and
the docs all share. Keep it in `GLOSSARY.md` at the repository root, or in the glossary the project already has.

This is ongoing work, not a document written once. Whenever a concept comes up, in conversation or in the code,
check it against the glossary, and build and sharpen the glossary with the user as you go.

## Prefer the field's terms

Where the industry has an established term, use it, even when the user or the code says something else. Look it
up in standards, textbooks and the docs of widely used tools rather than going from memory, and check that its
meaning really matches: a near match with a different meaning is worse than no match. Someone who knows the field
should recognise the project's language on sight. Where the field has no term, use the user's word, or else the
plainest name that explains itself.

## Hunt for ambiguity

Look for it in the conversation, the code (types, tables, status values), the UI text and the docs:

- one word used for more than one thing: split it into separate terms;
- one thing called by several words: pick one, and list the rest under `Avoid`;
- a concept with no name, which shows up as a phrase repeated in place of a word;
- a field term used here with a different meaning from the field's.

When two terms sit close together, an invented edge case settles where the line falls: "A customer pays for three
items and one ships late. Is that one order or two?"

## Align with the user

Use the agreed terms yourself, every time. When the user uses an avoided word or a non-standard one, offer the
agreed term with its meaning, the way a colleague would: "Libraries call that a hold. Use Hold?" The user learns
the field's language this way.

Once a term is agreed, it stands until someone deliberately changes it. Loose wording in conversation, from the
user or anyone else, doesn't change the glossary; answer in the agreed term.

## Fix what drifts

When you find a wrong name in the code, the docs or the UI, fix it then and there, as part of the change you are
making. Rename every use, including tests and comments. Where the old name is in saved data or a public API, the
rename includes migrating the data or keeping the old name working for its callers, so say so to the user first.

## The glossary

```markdown
### Hold

A book kept on the shelf for a patron to collect.

- **Not:**
  - **Loan**: a book on loan has left the library; a book on hold hasn't.
  - **Recall**: a recall asks a patron to bring back a book on loan early; a hold only waits on the shelf.
- **Avoid:**
  - reservation: what patrons often say, but not the library term.
  - request: also means an interlibrary loan request.
- **Source:** the standard library term (Koha, Evergreen)
- **Proposed:** by the agent, 2026-11-20. Not yet agreed by the user.
```

One entry per term, defined in a sentence or two that makes sense on its own. `Not:` lists the terms it is most
easily confused with, each with how it differs. `Avoid:` lists the words not to use for it, each with why.
`Source:` says where a field term comes from. Leave out any of these that doesn't apply.
The glossary holds terms and their meanings, not decisions or designs.

When you name something without the user, add its entry with a `Proposed:` line and say so in your reply. A later
agent treats every unmarked entry as the user's decision, so an unmarked guess is worse than no entry. Remove the
line when the user agrees.

## Make it findable

Later sessions won't have this skill loaded, so add a pointer to the project's agent instructions, `AGENTS.md`,
and `CLAUDE.md` if the project has one:

```markdown
## Domain language

`GLOSSARY.md` holds this project's agreed terms. Use them in code, docs and conversation, never the words under
`Avoid`, and fix any drift you find. An entry marked `Proposed:` isn't agreed yet. Add new terms there, marked
`Proposed:`, and tell the user.
```
