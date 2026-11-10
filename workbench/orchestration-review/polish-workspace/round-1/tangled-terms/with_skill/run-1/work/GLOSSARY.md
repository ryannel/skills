# Glossary

The names this project uses for its things. Docs, plans and chat use these names. Code and saved data keep the
names they already have, which are given under `Stored as`. An entry with a `Proposed:` line has not been agreed
by the owner; every other entry has.

## People

**Courier**
The person who delivers a parcel to a bank and puts it in a locker.

**Customer**
The person a parcel is addressed to, who comes to the bank to collect it.

## Things

**Parcel**
One item a courier delivers for a customer.

**Locker**
One compartment with its own door, which holds one parcel.
Not: Bank. A bank is the whole wall; a locker is one compartment in it.
Avoid: hopper, unit, door (as a name for the compartment; "door" means only the physical door)
Stored as: `locker`, a locker number, in `data/parcels.json`; `locker_id` in `src/parcel.py`

**Bank**
A wall of lockers at one location.
Not: Locker. A bank contains many lockers.
Avoid: cabinet

**Collection Code**
The code the system sends to the customer, which opens the locker holding their parcel.
Avoid: code (on its own, where it could be mistaken for something else)

## Steps

**Drop-off**
The courier scans in at the bank, puts the parcel in a free locker and shuts the door.
Stored as: `drop`, the function in `src/parcel.py`

## Statuses of a parcel

**Awaiting Collection**
The parcel is in a locker with the door shut, and the customer has not yet collected it.
Not: Collected. A parcel awaiting collection is still in the locker.
Avoid: claimed, unclaimed. "Claimed" was used for this status, and "unclaimed" for a parcel the customer had not
picked up, so the word pointed both ways. Say "not collected" for the second meaning.
Stored as: `claimed`, in the `state` field of `data/parcels.json` and in `STATES` in `src/parcel.py`

**Collected**
The customer has taken the parcel out of the locker.
Stored as: `collected`, in the `state` field

**Stale**
The parcel was not collected within 72 hours of drop-off. The bank flags it.
Stored as: `stale`, in the `state` field
