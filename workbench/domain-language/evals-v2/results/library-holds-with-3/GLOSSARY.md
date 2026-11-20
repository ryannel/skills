# Glossary

The agreed name for each thing in this project. Use these names in code, plans, tests and chat. An entry with a
`Proposed:` line hasn't been agreed by the human yet.

**Available**
A book on the open shelves that nobody has checked out or has waiting for them.
Stored as: `available`, in the `status` column of the `loans` table
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Checked Out**
A book a patron has taken home, until they bring it back.
Not: Waiting for Pickup. A book that is waiting for pickup has not left the library.
Avoid: out
Source: the standard circulation term, as used by Evergreen and Koha
Stored as: `out`, in the `status` column of the `loans` table
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Hold**
A patron's request to have a particular book kept for them. A patron places a hold; when the book is free, it is
set aside on the hold shelf for them.
Avoid: reservation, reserve, request, claim
Source: the standard library term, as used by circulation systems such as Koha and Evergreen
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Hold Shelf**
The shelf behind the desk where books waiting for pickup are kept.
Source: the standard library term ("holds shelf" in Evergreen)
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Overdue**
A checked-out book that is past its due date.
Avoid: late, late flag
Source: the standard circulation term
Stored as: `late`, in the `status` column of the `loans` table
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Patron**
A person with a library card, who can place holds and check out books.
Avoid: member, user
Source: the standard library term, as used by Koha and Evergreen
Stored as: `users` table, and `user_id` in the `loans` table
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Pickup Period**
How long a book waits on the hold shelf for the patron before it goes back on the open shelves.
Avoid: hold days
Source: the library term for the hold pickup window (Koha's setting for it is `ReservesMaxPickupDelay`)
Stored as: `HOLD_DAYS` in `src/models.py`
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Waiting for Pickup**
The status of a book that has been set aside on the hold shelf for one patron, who hasn't collected it yet.
Not: Hold. The hold is the patron's request; Waiting for Pickup is the book's status once it has been set aside.
Avoid: claimed, reserved
Source: Koha calls these holds "Waiting"; Evergreen's item status is "On holds shelf"
Stored as: `claimed`, in the `status` column of the `loans` table
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

## Open questions

- "Loan": the `loans` table holds every book's status, including books that are Available or Waiting for Pickup,
  which aren't loans in the library sense. Is a row in `loans` a Loan, or a book's circulation record? Used in
  `LOANS_TABLE` in `src/models.py`.
