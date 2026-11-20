I went through the README, the screen text (`web/strings.json`) and `src/models.py`. Libraries already have standard words for all of this, and systems like Koha and Evergreen use them, so I'd suggest we use those rather than invent our own.

**The main one: what you call a request is a Hold.** In library terms, a patron *places a hold* on a book. When the book is free it's set aside for them, and it is then *Waiting for Pickup* on the *hold shelf*. That covers all four of your words:

- "reserve" (docs and button) and "request" (you) → **Hold**. The button would read "Place Hold".
- "claimed" (code) → **Waiting for Pickup**. It's the book's status once it's set aside, which is different from the hold itself (the patron's request). The code can keep storing it as `claimed`. Only what people read changes.
- "the shelf behind the desk" → **Hold Shelf**.

A few other names were mixed up too:

- "Members" (README) and "users" (code) → **Patron**, the standard term for someone with a library card.
- "late" / "late flag" → **Overdue**.
- the `out` status → **Checked Out**.
- the time a book waits for collection → **Pickup Period**.

Here's how it all reads as one run:

1. A patron places a hold on a book that's checked out.
2. The other patron returns it, and staff put it on the hold shelf. Its status becomes Waiting for Pickup.
3. The patron sees "Your book is waiting at the desk."
4. The patron collects it within the pickup period, and it becomes Checked Out. If they don't, the app puts it back to Available.
5. If they keep it past the due date, it becomes Overdue.

**One thing doesn't match what you told me.** You said a book goes back on the shelf after 7 days. The code (`HOLD_DAYS = 3` in `src/models.py`) puts it back after 3. I haven't changed it. Which one is right?

I've put all of these in a new `GLOSSARY.md`, each marked as proposed until you agree. I haven't changed the README or the button yet. Once you say yes, I'll update the README to use these names and change the button to "Place Hold". Data and code names like `claimed`, `users` and `HOLD_DAYS` stay as they are, so nothing breaks. The glossary records what each one stands for. The project doesn't have an `AGENTS.md` or `CLAUDE.md` yet. If you want future sessions to follow these names automatically, I can add one that points to the glossary.

So:
1. Are you happy with **Hold**, **Waiting for Pickup**, **Patron** and **Overdue**, or do you want to keep "reservation" because your patrons use it?
2. Is the pickup period 7 days or 3?
3. One smaller question, which can wait: the code's `loans` table stores *every* book's status, including books on the shelf. Is that a list of loans, or really each book's record? It only matters if we ever rename it.
