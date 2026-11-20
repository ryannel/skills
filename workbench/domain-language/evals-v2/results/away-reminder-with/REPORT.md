# Report: Courtesy Notice

## What I added

- `send_courtesy_notices(loans, users, today)` in `src/notices.py`. It emails each patron whose loan is due back in
  two days and not yet returned, with the subject "Due soon: <title>" and the due date in the body. It returns how
  many it sent, like `send_overdue_notices`. Like that function, it only runs when something calls it: nothing
  schedules either one yet.
- `tests/test_notices.py`, three tests: sent two days before the due date, not sent on other days, not sent for a
  returned loan. `python3 -m unittest` passes.

## A name to agree

The glossary had no name for this email, so I added one, marked `Proposed:`:

**Courtesy Notice**: the email a patron gets two days before a loan's due date, reminding them when it is due back.
It is the term Evergreen, Alma and Sierra use for this notice (Koha calls it an "advance notice"), and it pairs
with the Overdue Notice already in the glossary.

The name is now in the code as `send_courtesy_notices`, so choosing a different name would mean a rename. If you're
happy with it, delete the `Proposed:` line in `GLOSSARY.md`.

## Other changes

- `AGENTS.md` now has a short "Names" section pointing later sessions to `GLOSSARY.md`.

## Worth knowing

- The existing code calls patrons `users` and `user_id`; I kept those stored names, as the glossary records.
- Neither notice is sent again if the job misses its day (the checks are `==` on a date), so a skipped run means a
  missed email. I left that as it is.
