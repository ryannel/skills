# Glossary

The agreed names for the things in this project. Documents and conversation use these names. A name under
`Avoid` is an older word for the same thing. `Stored as` gives the name the code and data use, which stays as
it is.

**Bank**
A wall of lockers.
Avoid: cabinet

**Code**
What the customer gets when their parcel is put in a locker, and brings to the pickup.

**Collected**
The status of a parcel after the customer's pickup.
Not: Pickup. The pickup is the customer's visit, and collected is the parcel's status afterwards.

**Locker**
One door in a bank, and the space behind it that a courier puts a parcel in.
Not: Bank. A bank is the whole wall, and a locker is one door in it.
Avoid: hopper, unit

**Overdue**
The status of a parcel that nobody has collected within 3 days of the courier putting it in a locker.
Avoid: stale
Stored as: `stale`, in the `state` field of `data/parcels.json` and in `STATES` in `src/parcel.py`

**Pickup**
The customer's visit to a locker, with their code, to take their parcel.
Not: Collected. Collected is the parcel's status after the pickup.

**Waiting for Pickup**
The status of a parcel that is in a locker and has not been collected, from the moment the courier shuts the
door.
Avoid: claimed, unclaimed
Stored as: `claimed`, in the `state` field of `data/parcels.json` and in `STATES` in `src/parcel.py`
