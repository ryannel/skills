# Modules

Brief: docs/modules/BRIEF.md (customers move their own appointment).

## The modules

- **BOOKINGS** owns every stored fact about appointments: the store, each `booking` and its move history, the
  salon settings (opening hours, time zone, slot length, stylists, phone, addresses), which times are free, the
  private links, and the emails about appointments with the outbox they wait in. It is the only module that writes
  any of these. Built before this plan: `createBooking` in `src/booking.js` and the email subject in
  `src/email.js`. Design: BOOKINGS.md.
- **APPOINTMENT_PAGE** owns the web page a customer reaches from the private link, and its look. It stores
  nothing: it reads and moves appointments only through the BOOKINGS interface below. Design: APPOINTMENT_PAGE.md.

The earlier entry said BOOKINGS covers "creating and cancelling bookings. Done." The repository has no cancel
function, so this list no longer claims one (see the BOOKINGS plan's log).

## Order

1. BOOKINGS M1, then M2. They hold the riskiest parts: never double-booking a stylist, and getting free times
   right across a daylight-saving change.
2. APPOINTMENT_PAGE M1 (look options for the owner) runs alongside BOOKINGS, since it needs no real data.
3. APPOINTMENT_PAGE M2 starts once BOOKINGS:M2 is Done and the owner has chosen a look.

## Interface: BOOKINGS to APPOINTMENT_PAGE

Exported from `src/` as plain async functions. A start time is an ISO 8601 string with the salon's UTC offset,
such as `2026-12-01T10:00:00+01:00`, the same value the `slot` field of a `booking` holds. A token is the secret
part of a private link. BOOKINGS normalizes accepted starts to integer epoch milliseconds internally, so
equivalent offset or fractional-second spellings identify the same slot. Returned starts use the salon's offset
at that instant.

The runtime supplies BOOKINGS with a 32-byte outbox encryption key held outside the database and salon settings.
Recording, moving and sending use the same key, retained across restarts so pending emails remain recoverable.
The APPOINTMENT_PAGE demo creates a fresh store per run and may generate an in-memory key for that store's
lifetime. Reopening an existing store requires its original key. BOOKINGS owns encryption and decryption.

- `findByLink(token)` returns nothing for an unknown token. Otherwise it returns the appointment as the customer
  may see it: customer's name, stylist, start, status, whether it can be moved now and, if not, why
  (`inside_cutoff` or `cancelled`), and the salon's name and phone number.
- `freeTimesByLink(token, { stylist })` returns the stylists the customer may choose from, and the free start
  times for one stylist, the appointment's own stylist when none is named. Empty when the appointment can't be
  moved.
- `moveByLink(token, { start, stylist })` moves the appointment and returns it as `findByLink` would. With no
  `stylist`, the stylist stays the same. A refused move changes nothing and returns one reason: `not_found`,
  `cancelled`, `inside_cutoff`, `taken` (the time went while the customer was choosing), `not_free` (outside
  opening hours, in the past or beyond the horizon) or `unknown_stylist`.
- `linkUrl(token)` returns the full private link, from the salon settings' public address.

Delivered by BOOKINGS:M2. APPOINTMENT_PAGE builds against a stand-in with these signatures until then. A change
to this interface is proposed in a plan's log and settled by the planner for both modules.
