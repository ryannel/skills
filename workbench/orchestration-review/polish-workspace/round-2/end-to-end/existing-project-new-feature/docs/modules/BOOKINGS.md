# BOOKINGS design: moving an appointment

## The owner's request
> for the salon app I want customers to be able to move an appointment themselves instead of phoning us. brief is fine to write up, I use claude and codex both
> 2026-11-10, on reading the brief: "Decision 5 is wrong: they can't move it less than 24 hours before. The rest looks fine."

Project brief: docs/modules/BRIEF.md. Decision numbers below are the brief's.

## What people need

- **A customer** who has only the confirmation email can move their appointment to another free time, and is never
  given a time that turns out to be taken by someone else. A moved appointment keeps the same stylist unless the
  customer picks a different one (decision 3: "A moved appointment must keep the same stylist unless the customer
  picks a different one."). They can't move it less than 24 hours before it starts (decision 5: "they can't move
  it less than 24 hours before."). After a move they get an email with the new time and a link that works for
  moving again (decision 6).
- **The front desk** never finds two customers in one stylist's slot (decision 4), is told by email of every move,
  and can see who moved an appointment and from when (decision 7).
- **Customers see "appointment"**, never "reservation", in every email (decision 1). The code keeps `booking`.
- **Creating bookings works as it does today**: `createBooking(customer, stylist, slot)` keeps its signature and
  returns the same object.

Out of scope (brief, "Not part of this"): accounts and sign-in, look-up by typed details, changing the service,
booking online, text messages, a front-desk screen. Choosing and paying for a real email provider, and sending real
email, are the owner's decisions; this module delivers email up to a transport the owner can plug a provider into.

## Mechanisms

**One store, and the store enforces "one confirmed appointment per stylist per slot".** Appointments live in one
SQLite database file through Node's built-in `node:sqlite` (no new dependency). A unique index over stylist and
start instant, limited to confirmed appointments, makes a double booking impossible to write. Recording and
moving normalize offset-bearing inputs to integer Unix epoch milliseconds before writing or comparing slots.
For example, `2026-12-01T10:00:00+01:00`, `2026-12-01T10:00:00.000+01:00` and
`2026-12-01T09:00:00Z` hold the same slot. Every write that can
put an appointment in a slot (recording one, moving one) is a single transaction that relies on that index. No
code checks "is it free?" and then writes separately, because two requests can both pass the check. A write that
hits the index is refused as `taken`. SQLite serialises writers to one file, so this holds for any number of
simultaneous requests and any number of processes on one machine. It does not hold for several machines sharing
the file over a network; deploying is the owner's decision, and a multi-machine deployment would need this
revisited.

**Slots are a fixed grid.** An appointment occupies one slot. Slots start at opening time and repeat every
slot length until the last one that ends by closing time. Assumption, logged in the plan.

**Salon settings live in one file the owner edits**, `config/salon.json`: the salon's name, phone, email address
for move notices, public address for links, IANA time zone, slot length, opening hours per weekday, the stylists,
and how far ahead free times are offered (the horizon, 8 weeks unless the owner sets another). Every stylist works
all opening hours (brief, "Still open"). Changing the file changes the free times with no code change.

**Free times** for a stylist are the grid slots that are inside opening hours, start after now, start within the
horizon, and hold no confirmed appointment of that stylist. The horizon ends inclusively at now plus the configured
number of elapsed weeks, each exactly 7 × 24 hours. Opening hours and grid labels are wall-clock times in the
salon's IANA time zone. Map each grid label to every matching instant using Node's `Intl` time-zone data, omit a
nonexistent local time, include both occurrences of a repeated time with their distinct offsets, and sort by
instant. A slot lasts the configured number of elapsed minutes and must end by closing. An ambiguous opening
uses its earlier occurrence and an ambiguous closing its later occurrence. A nonexistent opening or closing uses
the first valid instant after the gap. Assumptions are logged in the plan.

For a 30-minute grid open 01:00–04:00 in `Europe/Stockholm`, 2026-03-29 has starts at 01:00 and 01:30 with
`+01:00`, then 03:00 and 03:30 with `+02:00`. On 2026-10-25 it has 01:00 and 01:30 with `+02:00`, both 02:00
and 02:30 with `+02:00`, both again with `+01:00`, then 03:00 and 03:30 with `+01:00`. Tests use expected
instant lists for these days, closing and horizon boundaries. Stored instants are rendered with the salon's
offset at that instant when returned through the page interface. At 30-minute slots, 12 hours a day, 20 stylists
and 8 weeks, there are about 27,000 candidate slots, small enough to compute on each request.

**The 24-hour cut-off is measured in elapsed time**, between the moment the move is applied (server clock) and the
appointment's stored start. Exactly 24 hours or more before: allowed. Less: refused as `inside_cutoff`. It is
checked inside the move's transaction against the stored start, not against what the page showed. The new time
only has to be free (decision 4: in the future); it need not itself be 24 hours away. Assumption, logged.

**The private link** carries a random token of at least 128 bits from `crypto.randomBytes`. Lookup uses only its
SHA-256 hash on the booking. Every durable email payload is encrypted before it enters the database, as described
below. A database copy, including its journal or WAL and pending or sent outbox rows, therefore yields no usable
token without the separate encryption key. Delivered emails and the development transport's files contain the
working link and must be protected like the customer's email. An unknown token finds nothing and says nothing
about which appointments exist. The token belongs to the appointment and survives moves, so the link in every
email keeps working (decision 6). It is not single-use and doesn't expire on a timer: the link stops offering a
move once the cut-off passes or the appointment is cancelled. This is current practice for "manage your booking"
links, which differ from sign-in links.

**A move is one transaction** that: re-reads the appointment by link; refuses if cancelled or inside the cut-off;
refuses a start that isn't on the grid, in hours, in the future and within the horizon, or a stylist not in the
settings; changes the start, and the stylist only if the customer named one (decision 3); appends a history entry
(moved by the customer, from which start and stylist, to which, when; decision 7); and queues two emails. The old
slot is free the instant it commits (decision 6). A refused move leaves no trace in the appointment, its history or
the outbox.

**Emails go through an outbox.** Emails about an appointment are written to an outbox table in the same
transaction as the change that causes them, so a move is never applied without its emails, nor emails sent for a
move that didn't happen. Encrypt each complete email payload with AES-256-GCM using `node:crypto`, a fresh random
96-bit nonce per message and a 128-bit authentication tag. Persist only ciphertext, nonce, tag and delivery
metadata. The raw token and rendered plaintext never enter SQL, including temporary tables or error records.

BOOKINGS takes a 32-byte key supplied by the runtime, outside the database and salon settings. The same key must
be available to every recording, moving and sending process and retained across restarts. Tests supply it
explicitly. A fresh demo store may use a newly generated in-memory key for that store's lifetime. Reopening an
existing store requires the original key. A missing or malformed key fails initialization, and failed
authentication leaves the message unsent and reports a delivery error. A replacement key cannot recover pending
emails, so the runtime must retain the key while those emails may need delivery. Assumption, logged in the plan.

A sender decrypts queued emails only in memory, delivers them through a transport and marks each sent. If it
stops midway it resends on restart (at least once). Sent payloads remain encrypted. The development transport
writes each email as a file in a folder, which is what tests and reviewers read. A real provider is a second
transport, added when the owner chooses one. A failure after the appointment update but before both move emails
are queued must roll back the appointment, history and outbox together, even after the database is reopened.

Three emails, all saying "appointment":
- Confirmation, queued when an appointment is recorded: time, stylist, private link.
- Moved, to the customer: new time, stylist, the same private link (decision 6).
- Move notice, to the salon's address: who moved, from which time, to which time, with which stylist (brief, "Still
  open": the salon gets an email for each move).

**Recording an appointment.** `createBooking` stays a pure constructor, unchanged. A new operation records a
booking in the store (refused as `taken` if the slot is held), issues its private link and queues the
confirmation email. The customer value must carry a name and an email address, since the link travels by email.

## What this module provides

To APPOINTMENT_PAGE: `findByLink`, `freeTimesByLink`, `moveByLink` and `linkUrl`, as written in ARCHITECTURE.md.
To whatever records the salon's appointments: the record operation above. Nothing else writes the store.

Acceptance exercises these public exports against a real store. Record an appointment, resolve its link and
verify the customer name, stylist, start, status, move eligibility and salon name and phone. List selectable
stylists and free times with the appointment's stylist by default and an explicitly selected stylist, using
fixtures with free slots so an always-empty result fails. Move it and resolve the same link again for its updated
details. Unknown links resolve to nothing and list no choices or times. Cancelled and inside-cut-off links retain
the documented appointment and salon details, report `cancelled` or `inside_cutoff` respectively and list no
choices or times. `linkUrl` must use the configured public address and produce a link containing the same token.

## Mechanism references

SQLite documents uniqueness over the subset selected by a partial index. This design selects confirmed
appointments and compares their normalized instants. [SQLite partial indexes](https://www.sqlite.org/partialindex.html)

Node 24 supplies authenticated encryption, authentication tags and cryptographic randomness. The external key
allows a restarted sender to recover queued links while keeping a database copy insufficient to recover them.
[Node 24 crypto](https://nodejs.org/docs/latest-v24.x/api/crypto.html#cryptocreatecipherivalgorithm-key-iv-options)

The time-zone reference explains why a local time can correspond to zero or two instants. This design specifies
which candidates to offer in each case and uses elapsed time for duration and the horizon.
[TC39 time zones and ambiguity](https://tc39.es/proposal-temporal/docs/timezone.html)

## Cost
No cost target was set, and none is added here.
