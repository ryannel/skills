# Checks: away-reminder

Graded on REPORT.md and the files left in the folder.

1. The new code works: src/notices.py has a function that emails a patron for each unreturned loan whose due
   date is two days away, and `python3 -m unittest` (or importing the module) doesn't fail.
2. New code, comments and REPORT.md use the glossary's names (patron, loan, due date), not the words under Avoid
   (user, member, borrower). Existing stored names such as `users` and `due` may still appear.
3. GLOSSARY.md has a new entry for the new email, marked as proposed / not yet agreed by the human.
4. The new entry's name is the library field's term for it (courtesy notice, pre-overdue notice, due date
   reminder or similar in use by library systems), or the entry or report says that a field term was looked for.
5. REPORT.md names the new entry and says it is proposed, so the human can pick another.
6. The four existing glossary entries are unchanged.
7. AGENTS.md now points to GLOSSARY.md and says to use its names, or REPORT.md says that it should.
8. The agent finished without waiting for the human.
