# How it works

The names used here are defined in [`GLOSSARY.md`](../GLOSSARY.md).

1. A Courier scans in, puts a Parcel in a Locker and shuts the door.
2. Once the door shuts, the Parcel is Awaiting Pickup. The code stores this state as `claimed`.
3. The Customer gets a Code.
4. The Customer scans the Code at the Bank and takes the Parcel. The Parcel is now Picked Up, which the code
   stores as `collected`.
5. A Parcel that is not Picked Up within 3 days (72 hours) is Overdue, and the Bank flags it. The code stores
   this state as `stale`.

A Locker is one compartment with one door. A Bank is a wall of Lockers.
