# How it works

The names used here are defined in [`GLOSSARY.md`](../GLOSSARY.md).

A bank is a wall of lockers. A locker is one compartment with its own door, and holds one parcel.

1. The courier scans in at the bank and puts the parcel in a free locker. This is a drop-off.
2. When the locker door shuts, the system marks the parcel Awaiting Collection (stored as `claimed`).
3. The system sends the customer a collection code.
4. The customer enters the collection code, the locker opens and they take the parcel. The parcel is now
   Collected.
5. A parcel not collected within 72 hours of drop-off becomes Stale, and the bank flags it.
