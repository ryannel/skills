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

**Due Date**
The day a loan has to be returned by.
Source: the standard library term
Stored as: `due`

**Overdue Notice**
The email a patron gets the day after a loan's due date has passed without the book coming back.
Avoid: late email
Source: the standard library term
