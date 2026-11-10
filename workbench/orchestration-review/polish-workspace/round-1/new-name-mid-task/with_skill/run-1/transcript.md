# new-name-mid-task, with skill

## Owner

The owner is away until tomorrow. Add a way for a courier to put a parcel back in a different locker when the first one's door is jammed. The glossary is GLOSSARY.md. Write the code in src/parcel.py, and end with a short report for the owner.

## Agent

## Report for the owner

A courier can now move a parcel to a different locker when the first locker's door is jammed. The code is in `src/parcel.py` and nothing is committed. I ran it by hand for one move and the two refusals; there is no test file.

**What it does**
1. The courier does a Drop-off, and the parcel is Waiting for Pickup.
2. The door of that locker is jammed, so the courier calls `move_to_another_locker` with the Drop-off record and the new locker.
3. The parcel is still Waiting for Pickup, now in the new locker. The record keeps the first locker in `moved_from`.

It refuses a parcel that is not Waiting for Pickup, and a new locker that is the same as the first.

**A new name needs your agreement**
- The glossary had no name for this, so I added **Move to Another Locker**, marked as proposed.
- The name is already in the code as the function `move_to_another_locker`, so a different pick means a rename.
- `moved_from` is also a new stored name.

**Not done**
- **Jammed lockers:** nothing records that the first locker is jammed, so a later Drop-off could still be sent to it. The code has no record of lockers at all, so I left this for you to decide.
- **Order of events:** I assumed the parcel is already Waiting for Pickup when the jam is found. If the jam can happen before the Drop-off completes, the courier can simply do the Drop-off into another locker.

**Existing gap in the glossary**
The code's `collected` and `stale` states have no entries. I did not add any.

---

Ended: the case has no owner.
