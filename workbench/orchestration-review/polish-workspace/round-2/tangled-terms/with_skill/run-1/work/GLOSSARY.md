# Glossary

The agreed names for the things in this project. Documents and conversation use these names. Where the code or
the saved data uses a different name, the entry gives it under `Stored as`.

## People

**Courier**
The person who delivers a Parcel and puts it in a Locker.

**Customer**
The person a Parcel is for, who picks it up from the Locker.

## Things

**Parcel**
The item a Courier delivers for a Customer.

**Locker**
One compartment with one door, which holds one Parcel.
Not: Bank. A Bank is the whole wall; a Locker is one compartment in it.
Avoid: hopper, unit

**Bank**
A wall of Lockers. The Customer scans their Code at the Bank.
Avoid: cabinet

**Code**
What the Customer gets when their Parcel is dropped off, and scans at the Bank to pick the Parcel up.

## Parcel states

**Awaiting Pickup**
A Parcel that is in a Locker with the door shut, and that the Customer has not yet picked up.
Avoid: claimed
Stored as: `claimed`, in the `state` field of a parcel record (`src/parcel.py`, `data/parcels.json`)

**Picked Up**
A Parcel that the Customer has taken out of the Locker.
Avoid: collected
Stored as: `collected`, in the `state` field of a parcel record

**Overdue**
A Parcel that nobody picked up within 3 days (72 hours) of it being dropped off.
Not: Awaiting Pickup. An Overdue Parcel is still in the Locker, but its 3 days have run out.
Avoid: stale, unclaimed
Stored as: `stale`, in the `state` field of a parcel record
