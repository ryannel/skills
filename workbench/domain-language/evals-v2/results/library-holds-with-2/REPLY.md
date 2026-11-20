I've looked through the README, the button text and `src/models.py`. Libraries have had standard words for all of this for a long time, so I'd use theirs instead of inventing new ones. Anyone who has worked a circulation desk, or used systems like Koha or Evergreen, will recognise them straight away.

**The main clash.** "Reserve" (docs and button), "claimed" (code) and "request" (you) are covering two different things:

1. **Hold**: the patron asking for a book. Libraries say a patron *places a hold*. That's what the Reserve button does, and I think it's what you mean by "request".
2. **On the Hold Shelf**: the status of a book that has come back and been put aside behind the desk for that patron. The code calls this `claimed`. Evergreen says "on holds shelf" and Koha says "Waiting".

Use **Hold** for the first and **On the Hold Shelf** for the second, and drop reserve, claimed and request?

**The others**, each the standard library term:

- **Patron** instead of "member" (README) and "user" (README, `users` table)
- **On Loan** instead of `out`
- **Overdue** instead of "late" / "late flag"
- **Pickup Period** for how long a book waits on the hold shelf. Evergreen calls it the shelf expire interval.
- **Expired Hold** for a book that wasn't collected in time and goes back to **Available**

All OK?

**Here's the main job using those names:**

1. A patron places a hold on a book that's on loan to someone else.
2. The other patron returns the book.
3. Desk staff put it on the hold shelf for the first patron. Its status becomes On the Hold Shelf.
4. The patron collects it within the pickup period, and it becomes On Loan to them.
5. If they don't, the hold expires after the pickup period and the book goes back to Available.
6. A patron who keeps a book past its due date makes it Overdue.

**Two things I need from you:**

- **Is "request" the same thing as a Hold?** I've assumed it is. If you sometimes use it for the book once it's set aside, tell me.
- **Does a hold on a book that's already on the open shelves count?** Say a patron places a hold on a book that's sitting there Available. Does it go straight to the hold shelf, or do they just go and take it?

**Something you should know.** You said 7 days, but the code puts a book back after **3**: `HOLD_DAYS = 3` in `src/models.py`. I haven't changed it. The glossary only records what you mean. Say if you want the code changed to 7.

**What I've done so far.** I wrote `GLOSSARY.md` with all of these, each marked *Proposed* until you agree. The names stored in the code and data (`claimed`, `out`, `late`, `users`, `HOLD_DAYS`) stay as they are. Renaming them would be a separate change. Each entry records its stored name, so you can still match them up.

Once you've agreed, I'll update the README and the on-screen text, for example the button becoming "Place hold", and the banner saying the book is on the hold shelf. The project has no `AGENTS.md` or `CLAUDE.md`, so later sessions won't know the glossary exists. I can add a short note pointing to it in whichever one you use.
