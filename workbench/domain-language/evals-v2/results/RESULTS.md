# Results, 20 November 2026

One run each with and without the skill, graded against each case's `checks.md`. The library case was run twice
more with the skill after a fix.

| Case | With the skill | Without |
|---|---|---|
| bakery-books | 6/6 | 6/6 |
| library-holds, first draft | 3/7 | 6/7 |
| library-holds, after the fix (two runs) | 7/7, 7/7 | |
| away-reminder | 8/8 | 4/8 |

- **bakery-books.** Both runs named the accounting terms. With the skill, every recommendation was the field's
  term, with where it comes from (QuickBooks, Xero, Sage) and a one-line meaning, and the glossary entries were
  marked proposed. Without it, the agent listed the field's terms but recommended its own ("monthly summary",
  "unpaid bills") and offered to rename the code.
- **library-holds, first draft.** The skill's "hear the human first, before you offer any name" made the agent
  ask for a walkthrough and offer no names, though the request was clear, and it skipped the field lookup. The fix:
  ask only about what the request and repository don't tell you, recommend names for the rest in the same
  message, and look the field's terms up before the first message about names. After it, both runs searched Koha
  and Evergreen documentation and recommended Hold, Patron and Overdue with sources, raised 7 days against
  `HOLD_DAYS = 3`, and left the code alone.
- **away-reminder.** With the skill: Courtesy Notice, found in Evergreen, Alma and Sierra documentation, added
  with a `Proposed:` line and a `Not:` line against Overdue Notice, reported, and a Names section added to
  AGENTS.md. Without: "Due Date Reminder" in code, no glossary entry, no pointer.

What these don't test: a whole conversation with a human answering, and whether a later session follows the
AGENTS.md pointer.
