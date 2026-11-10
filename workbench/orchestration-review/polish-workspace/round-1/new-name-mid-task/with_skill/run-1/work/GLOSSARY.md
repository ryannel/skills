# Glossary

**Locker**
One door with a space behind it that holds one parcel.
Avoid: unit, cabinet, hopper

**Bank**
A wall of lockers at one address.

**Drop-off**
A courier putting a parcel into a locker.
Stored as: `drop` in `src/parcel.py`

**Pickup**
A customer taking their parcel out of a locker.

**Waiting for Pickup**
A parcel that is in a locker and has not been taken out.
Avoid: claimed
Stored as: `claimed`, in a parcel's `state`

**Move to Another Locker**
A courier putting a parcel into a different locker, because the door of the first locker is jammed. The parcel stays Waiting for Pickup.
Not: Drop-off. A drop-off is the first time the parcel goes into a locker.
Stored as: `move_to_another_locker` in `src/parcel.py`. The first locker is kept in the record's `moved_from`.
Proposed: by Claude, 10 November 2026. Not yet agreed by the owner.
