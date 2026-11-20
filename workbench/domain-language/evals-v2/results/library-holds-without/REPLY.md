I read the whole app (README.md, web/strings.json, src/models.py) and haven't changed anything yet. You're the one who has to say these words every day, so I'd like you to agree the names before I rename things. Here's what I found and what I suggest.

**I think your four words cover two different things.** The README says a member reserves a book, and "when it comes back it is claimed for them and put on the shelf behind the desk." So there are two steps:

1. A member asks for a book that isn't in yet. The docs and the button call this "reserve". You call it a request.
2. The book comes back and is put aside behind the desk for that member. The code calls this "claimed".

Part of the confusion is that one word gets used for both steps. That also means the code has no state for step 1. `STATUSES` goes straight to `claimed`, so a member waiting for a book that's still out isn't recorded anywhere.

**My suggestion, in standard library language:**

| Thing | Name | Replaces |
|---|---|---|
| A member's request for a book | **hold** ("place a hold") | reserve, request |
| A hold whose book is set aside behind the desk | **ready for pickup** (status `ready`) | claimed |
| How long a ready book waits before going back on the shelf | **pickup window**, 7 days | `HOLD_DAYS` |
| A person with a library card | **member** | the README's "users", `USERS_TABLE` |

The code already says `HOLD_DAYS`, so "hold" is half there. If you'd rather keep "reservation" because the button and docs use it, that works too. What matters is picking one word for step 1 and a different one for step 2.

**One thing that looks like a bug, not just a naming problem:** you said a book goes back on the shelf after 7 days, but `src/models.py` has `HOLD_DAYS = 3`. So right now it goes back after 3 days. Which is right?

**Two smaller things I'd fix along the way:**
- Holds are stored as rows in the loans table, and an uncollected one gets set to `available`. A book can be available, but a hold or loan can't. I'd make holds their own record and let an uncollected hold end as `expired`.
- The README talks about a "late flag", but in the code `late` is a loan status. I'd keep `late` and just change the README wording. (Or switch to "overdue" if that's what you say at the desk.)

**Before I make the changes, could you tell me:**
1. Is it 7 days or 3?
2. Are you happy with "hold" and "ready for pickup", or do you want "reservation"?
3. Is there a real database behind this with `claimed` already stored in it? If there is, renaming the status needs a small migration, not just a code edit.

Once you answer, I'll update the README, the button and banner text, and the code in one go, and add a short glossary to the README so the next person uses the same words.
