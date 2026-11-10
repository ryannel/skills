# existing-project-new-feature, without skill

## Owner

for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both

## Agent

The brief is written at `docs/modules/RESCHEDULE.md`, alongside your other module plans, and I added a "Planned" line for it in `docs/modules/ARCHITECTURE.md`. Nothing is committed. It's plain markdown with no tool-specific instructions, so Claude or Codex can pick it up as is.

The brief covers the booking logic and the "your appointment has moved" email, with tests. It leaves out the screen where the customer picks a new time, customer login, and any database, because the app has none of those yet.

I filled in four business rules with defaults. Tell me if any are wrong and I'll change the brief:

1. **Cutoff:** customers can move an appointment up to 24 hours before it; after that they're told to phone.
2. **Stylist:** the appointment stays with the same stylist.
3. **Number of moves:** no limit on how many times one booking can be moved.
4. **Stylist notification:** the stylist is not notified when a booking moves.

Two things in the repo that the brief works around:

- **Cancelling:** `ARCHITECTURE.md` says cancelling bookings is done, but there is no cancel function in `src/`. The brief tells the agent not to rely on one.
- **Slot format:** nothing in the code says what format a time slot is in. The cutoff rule needs real dates, so the brief tells the agent to check, and to treat slots as ISO date-time strings if nothing constrains them.

## Owner

Cutoff is right, 24 hours. On the stylist, it stays the same unless the customer picks another one. The other two are fine.

## Agent

The brief at `docs/modules/RESCHEDULE.md` now says the appointment keeps its stylist unless the customer picks another one, and the open questions are replaced by your four confirmed decisions. Still nothing committed.

Allowing a stylist change raised two cases you didn't mention, and I settled them like this:

- **Availability:** the new time has to be free for the stylist the customer ends up with, not the original one.
- **Same time, different stylist:** this counts as a move and is allowed, under the same 24-hour cutoff. Say if you'd rather a move always had to change the time.

## Owner

Fine by me, same time with a different stylist can count as a move.

## Agent

That's recorded as a confirmed decision in `docs/modules/RESCHEDULE.md`; the rule itself was already written that way. The brief has no open questions left and is ready to hand to Claude or Codex. It and the `ARCHITECTURE.md` line are still uncommitted — say if you want me to commit them or start the build.

---

Ended: the agent finished and asked nothing.
