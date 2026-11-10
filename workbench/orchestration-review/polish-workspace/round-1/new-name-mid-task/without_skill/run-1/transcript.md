# new-name-mid-task, without skill

## Owner

The owner is away until tomorrow. Add a way for a courier to put a parcel back in a different locker when the first one's door is jammed. The glossary is GLOSSARY.md. Write the code in src/parcel.py, and end with a short report for the owner.

## Agent

## Report for the owner

A courier can now move a parcel to a different locker when the first locker's door is jammed: `redrop(record, new_locker_id)` in `src/parcel.py`. I tried it by hand (one good case, two refused cases) and it behaves as described; the project has no tests and I added none. Nothing is committed.

**What it does**
- Takes the record returned by `drop` and returns a new one pointing at the new locker.
- The parcel stays Waiting for Pickup (`state` is still `claimed`).
- The record gains a `jammed_locker` field holding the first locker's id, so someone can find the door that needs fixing.
- It refuses, with a `ValueError`, if the new locker is the same as the first, or if the parcel is not Waiting for Pickup.

**Decisions for you**
- **The name.** The glossary had no word for this, so I called it "Re-drop" and added it to `GLOSSARY.md`, marked "proposed — not yet agreed by the owner". If you prefer another name, change the glossary entry and the function name; nothing else uses it yet.
- **The `jammed_locker` field.** This is my addition, not something you asked for. The catch is that it only remembers the most recent jammed locker if a parcel is re-dropped twice. Say if you want it removed or turned into a list.

**Not done**
- Nothing checks that the new locker is empty or in the same bank, because the code has no record of lockers or banks to check against.

---

Ended: the case has no owner.
