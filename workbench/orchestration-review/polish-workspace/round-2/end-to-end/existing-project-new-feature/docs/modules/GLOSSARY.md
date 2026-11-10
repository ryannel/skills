# Glossary

**Appointment**
One customer, one stylist and one time slot.
Avoid: reservation
Stored as: `booking`, in the code
Proposed: by the lead, 2026-11-10. Not yet agreed by the owner.

**Private link**
The link in an appointment's emails that lets the customer see and move it, with no account or password.
Avoid: magic link, login link
Stored as: a token's hash on the `booking`, in the code
Proposed: by the planner, 2026-11-10. Not yet agreed by the owner.

**Move**
Changing an appointment's time, and optionally its stylist, by the customer.
Avoid: reschedule, change, rebook (in customer-facing text)
Proposed: by the planner, 2026-11-10. Not yet agreed by the owner.

**Free time**
A start time the customer may move to: inside opening hours, in the future, within the horizon, with no confirmed appointment for that stylist.
Avoid: availability, open slot
Proposed: by the planner, 2026-11-10. Not yet agreed by the owner.

**Cut-off**
The 24 hours before an appointment starts, during which the customer can't move it.
Proposed: by the planner, 2026-11-10. Not yet agreed by the owner.

**Salon settings**
The one file the owner edits for opening hours, time zone, slot length, stylists, phone, addresses and horizon: `config/salon.json`.
Proposed: by the planner, 2026-11-10. Not yet agreed by the owner.
