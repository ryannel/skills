# The glossary format

A worked glossary, the text that points later sessions to it, and the commands that check for drift.

## A small glossary

```markdown
# Glossary

The agreed name for each thing in this project. Use these names in code, plans, tests and chat. An entry with a
`Proposed:` line hasn't been agreed by the human yet.

**Patron**
A person with a library card, who can borrow books and put them on hold.
Avoid: user, member
Source: the standard library term, used by circulation systems such as Koha and Evergreen
Stored as: `users` table

**On Hold**
A book that a patron has asked for, and that is waiting on the shelf for them to collect.
Not: On Loan. A book on hold has not left the library.
Avoid: reserved, claimed
Source: the standard library term, as used by circulation systems such as Koha and Evergreen
Stored as: `claimed`, in the `status` column of the `loans` table

**On Loan**
A book a patron has taken out, until they bring it back.
Avoid: checked out, borrowed
Source: the standard library term

**Overdue Notice**
The email a patron gets the day after a book on loan was due back.
Source: the standard library term
Proposed: by the agent, 2027-03-12. Not yet agreed by the human.

## Open questions

- "Renewal": the human uses it for extending a loan, and the code's `renew()` also resets the fine. One thing or
  two? Used in `loans/renew.py` and the help page.

## Retired

- "Reservation": now On Hold (2027-03-10). Still in old reviews, which are left as written.
```

What each part is for:

- The opening lines tell a reader who lands on the file what it is and how to treat it.
- Patron, On Hold, On Loan and Overdue Notice are the library field's own terms, so each says so on a `Source:`
  line. A name particular to the project has no `Source:` line.
- Entries are in an order a reader can follow, usually alphabetical. Keep each one to its name, one or two
  sentences, and the lines that apply.
- An open question names the clash and where each meaning is used, so whoever settles it can check.
- A retired name says what replaced it and when. Keep the section short, and drop a line once nothing current
  uses the old name. The old name also stays under `Avoid` in the entry that replaced it.

## The pointer for later sessions

Add this, or something close to it, to `AGENTS.md`, and to `CLAUDE.md` if the project has one:

```markdown
## Names

`GLOSSARY.md` holds the agreed name for each thing in this project. Read it before you write a plan, a design,
text a user will see or a report. Use its names in code, plans, tests and chat, and not the words under `Avoid`.
An entry marked `Proposed:` isn't agreed yet. If you need a name for something new, check the glossary first; if
it isn't there, add an entry marked `Proposed:` and say so in your report.
```

For Cursor, the same text goes in `.cursor/rules/glossary.mdc`, with `alwaysApply: true` in its frontmatter.

If the glossary is somewhere other than the root, give its path.

## Drift checks

Search the documents still in use for each word under `Avoid`. `-w` matches whole words, and `-i` ignores case:

```bash
git grep -n -i -w -e "reserved" -e "claimed" -- . ':!GLOSSARY.md' ':!docs/reviews'
```

Leave out the glossary and any folder of records of the past, such as finished reviews or logs. A match in a
sentence that gives a stored name ("stored as `claimed`") is fine.

Check that each `Stored as` name still exists in the code:

```bash
git grep -n -w "claimed" -- . ':!GLOSSARY.md' | head -3
```

No match means the code has moved on, and the entry needs updating.

When the human wants a name kept out for good, the first command can become a test in the project's own test
suite, which fails when it finds a match. Put the words it checks in the test, not in a separate list, so there is
one place to change.
