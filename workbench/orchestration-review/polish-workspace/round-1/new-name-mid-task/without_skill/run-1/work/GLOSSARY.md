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

**Re-drop** (proposed — not yet agreed by the owner)
A courier putting a parcel into a different locker because the first locker's door is jammed.
Stored as: `redrop` in `src/parcel.py`
