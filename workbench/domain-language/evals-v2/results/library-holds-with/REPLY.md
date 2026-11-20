Yes, let's sort them out. I've read the whole app (the README, `web/strings.json` and `src/models.py`), and it's worse than four words for one thing. Here's what's in use:

| What | README | Code | Screen | You |
|---|---|---|---|---|
| Asking for a book | "reserve" | – | Reserve button | "request"? |
| A book set aside at the desk | "claimed", "the shelf behind the desk" | status `claimed`, `expire_claims()` | "Your book is waiting at the desk" | "put aside" |
| A book someone has taken home | – | status `out`, `loans` table | – | – |
| Kept past its due date | "late flag" | status `late` | "This book is late" | – |
| The person borrowing | "Members", "Users" | `users` table | – | "someone" |

Three things stand out:

1. **"Shelf" means two opposite things.** The README says a claimed book is "put on the shelf behind the desk", and you said a book "goes back on the shelf" when nobody collects it. One shelf is where it waits for one person; the other is where anyone can take it.
2. **I can't yet tell if "request" and "put aside" are one thing or two.** Asking for a book (maybe while someone else has it) and the book actually sitting at the desk waiting could be the same record, or two steps. The code only has the second one.
3. **The code says 3 days, not 7.** `HOLD_DAYS = 3` in `src/models.py`, and `expire_claims()` sends a book back to available after 3 days uncollected. If 7 is the rule, the code is wrong; I haven't changed it, since that's your call.

Before I suggest any names, could you walk me through one real case from start to finish? Something like: a member wants a book that someone else has out. What do they do, what does the library staff do, what happens when the book comes back, and what happens if they collect it, or don't? Who does each step, in your own words, is what I need.

Then I'll come back with one name for each thing. Libraries have long-standing standard words for most of this, used in the big library systems, so I'll recommend those where they fit and tell you where each comes from. Once we agree them I'll write them into a `GLOSSARY.md` so the next session uses them too. The project has no `AGENTS.md` or `CLAUDE.md` yet, which is where a short pointer to the glossary would normally go; tell me if you use either and I'll add it there. I won't rename anything in the code or database; the stored names stay and the glossary records them.
