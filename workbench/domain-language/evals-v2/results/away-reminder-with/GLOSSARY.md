# Glossary

**Patron**
A person with a library card, who can borrow books and place holds.
Avoid: user, member, borrower
Source: the standard library term
Stored as: `users` table

**Loan**
A book a patron has taken out, from checkout until it is returned.
Avoid: borrowing, checkout record
Source: the standard library term

**Courtesy Notice**
The email a patron gets two days before a loan's due date, while the book is still out, reminding them when it is due back.
Not: Overdue Notice. A courtesy notice goes before the due date; an overdue notice goes after it has passed.
Avoid: reminder, due-soon email, pre-due notice, advance notice
Source: the term used by circulation systems such as Evergreen, Alma and Sierra (Koha calls it an "advance notice")
Stored as: `send_courtesy_notices` in `src/notices.py`
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Due Date**
The day a loan has to be returned by.
Source: the standard library term
Stored as: `due`

**Overdue Notice**
The email a patron gets the day after a loan's due date has passed without the book coming back.
Avoid: late email
Source: the standard library term
