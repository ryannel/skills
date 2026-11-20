# Glossary

The agreed name for each thing in this project. Use these names in code, plans, tests and chat. An entry with a
`Proposed:` line hasn't been agreed by the human yet.

**Available**
A book on the open shelves that any patron can take out.
Stored as: `available`, in the `status` column of the `loans` table
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Hold**
A patron's request to have a particular book set aside for them when a copy is free. A patron places a hold.
Not: On the Hold Shelf. A hold can wait for weeks while the book is out; it is only on the hold shelf once the
book is back and put aside.
Avoid: reservation, reserve, request, claim
Source: the standard library term, used by circulation systems such as Koha and Evergreen ("place hold")
Stored as: the button string `reserve_button` in `web/strings.json`; the code has no record of a hold before the
book comes back
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Hold Shelf**
The shelf behind the desk where books that have come back for a patron's hold wait for them to collect.
Source: the standard library term, used by Evergreen ("holds shelf")
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**On the Hold Shelf**
The status of a book that has been put aside on the hold shelf for one patron, until they collect it or the
pickup period runs out.
Not: Hold. The hold is the patron's request; this is the book, set aside.
Avoid: claimed, reserved, waiting at the desk
Source: Evergreen's "on holds shelf"; Koha calls the same status "Waiting"
Stored as: `claimed`, in the `status` column of the `loans` table
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Pickup Period**
How long a book stays on the hold shelf for a patron before it goes back on the open shelves. The human says
7 days.
Avoid: hold days
Source: Evergreen calls it the hold shelf expire interval; Koha calls it the maximum pickup delay
Stored as: `HOLD_DAYS` in `src/models.py`
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Expired Hold**
A hold whose book sat on the hold shelf for the whole pickup period without being collected. The book goes back
to Available.
Avoid: expired claim
Source: the standard library term, used by Koha and Evergreen
Stored as: `expire_claims()` in `src/models.py`
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**On Loan**
A book a patron has taken out, until they bring it back.
Avoid: out, checked out
Source: the standard library term
Stored as: `out`, in the `status` column of the `loans` table
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Overdue**
A book on loan that a patron has kept past its due date.
Avoid: late, late flag
Source: the standard library term, used by every circulation system
Stored as: `late`, in the `status` column of the `loans` table; `late_banner` in `web/strings.json`
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

**Patron**
A person with a library card, who can take books out and place holds.
Avoid: member, user
Source: the standard library term, used by Koha and Evergreen
Stored as: `users` table
Proposed: by the agent, 2026-11-20. Not yet agreed by the human.

## Open questions

- "Request": the human's word. It reads as the Hold (the patron asking for a book), but it could mean the book
  once it's put aside. Waiting on the human.
