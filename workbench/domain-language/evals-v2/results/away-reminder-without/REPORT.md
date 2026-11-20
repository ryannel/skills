# Report: email two days before a loan is due

## What I added
- `send_due_date_reminders(loans, users, today)` in `src/notices.py`. It emails each patron whose loan is not yet returned and whose due date is exactly two days after `today`. It returns how many emails it sent, the same way `send_overdue_notices` does.
- Subject: `Due soon: <title>`. Body: `This book is due back on <YYYY-MM-DD>.`
- Tests in `tests/test_notices.py` (with an empty `tests/__init__.py` so `python3 -m unittest` finds them). They cover the two-days-before case, other days, returned loans, and check the Overdue Notice still works. All 4 pass.

## For you to decide
- **Name.** The glossary has no term for this email yet. I called it a "Due Date Reminder" in the code and docstring, in the same style as "Overdue Notice". I did not edit `GLOSSARY.md`. If you agree with the name, add an entry like: *Due Date Reminder: the email a patron gets two days before a loan's due date, while the book is still out.* If you prefer another name, rename the function.
- **Wording.** The subject and body are placeholders in the same plain style as the Overdue Notice. Change them as you like.
- **Scheduling.** Nothing calls the new function yet, just as nothing in this repo calls `send_overdue_notices`. It needs to run once a day wherever the Overdue Notice runs. If a day is missed, that day's reminders are not sent later.
