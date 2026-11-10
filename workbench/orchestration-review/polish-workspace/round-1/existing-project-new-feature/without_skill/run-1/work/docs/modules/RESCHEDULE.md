# RESCHEDULE: customers move their own appointment

Status: planned, not started.

This brief is written for whichever coding agent picks it up (Claude or Codex). It is self-contained: read it, read `src/`, and build.

## Why

Today a customer who needs a different time has to phone the salon. That costs staff time on the phone, and customers who can't get through tend to no-show or cancel instead. We want the customer to move the appointment themselves, within rules the salon is comfortable with.

## What the customer can do

A customer with a confirmed booking can move it to a different free slot. The appointment stays with the same stylist unless the customer picks another one. They get an email confirming the new time. The old slot becomes available to other customers again.

## Where the code is today

The codebase is very small, so most of this feature is new ground.

- `src/booking.js` has `createBooking(customer, stylist, slot)`, which returns `{ customer, stylist, slot, status: "confirmed" }`. There is no storage, no booking id, and no notion of which slots are free.
- `src/email.js` has a single `subject(b)` for the confirmation email.
- `docs/modules/ARCHITECTURE.md` says cancelling is done, but there is no cancel function in `src/`. Do not build on a cancel function that isn't there; if you need a `"cancelled"` status check, write it against the status string.
- There are no tests yet. `npm test` runs `node --test`.
- `slot` is passed through as an opaque value. Nothing in the code says what format it has.

## Rules

1. Only a booking with status `"confirmed"` can be moved. A cancelled booking cannot.
2. The new slot must be free for the stylist the booking will end up with. The booking's own current slot does not count as taken.
3. The new slot must be in the future, and the move must change something: a request with the same slot and the same stylist is refused.
4. The booking keeps its stylist by default. The customer may pick a different stylist as part of the move, in which case the slot must be free for the new stylist. Keeping the time and changing only the stylist counts as a move and follows the same rules.
5. Moves are refused inside the cutoff window before the *current* appointment time. Default cutoff: 24 hours. Inside the window, the customer is told to phone the salon.
6. The move is all-or-nothing: the customer never ends up holding both slots or neither.
7. Each refusal has its own distinguishable reason (not confirmed, slot taken, slot in the past, nothing changed, too late to move), so the UI can say something useful to the customer.

Keep the cutoff as a single named constant so it is a one-line change.

## Shape of the change

Follow the style already in `src/booking.js`: plain exported functions, plain objects, no classes or framework.

- Add `rescheduleBooking(booking, change, context)` to `src/booking.js`, where `change` is `{ slot, stylist }` and `stylist` is optional (omitted means keep the current one). It returns a new booking object with the new slot and stylist rather than mutating the one passed in. `context` supplies the current time and a way to ask whether a slot is free for a stylist, both passed in so tests don't depend on the clock or on storage that doesn't exist yet.
- Add a subject line for the "your appointment has moved" email in `src/email.js`. It should name the new time. Note the existing subject says "reservation" while the code says "booking"; match the existing customer-facing word ("reservation") in the email and leave the rename question alone.
- The cutoff rule needs to compare a slot with the current time, so slots must be parseable as a date and time. Check how slots are actually produced before assuming a format; if nothing constrains it, treat a slot as an ISO 8601 string and say so in a comment on `createBooking`.

Out of scope for this piece of work:

- Changing the service while moving.
- A web page or UI for picking the new slot. This work delivers the booking logic and the email; the screen that calls it comes after.
- Customer login or identity checks. Whoever calls `rescheduleBooking` is trusted to have the right booking in hand.
- Limits on how many times a booking can be moved.
- Notifying the stylist.
- Persistence. Don't introduce a database for this.

## Done means

`npm test` passes, with tests (using `node:test`) that cover at least:

- A confirmed booking moved to a free future slot returns a confirmed booking with the new slot, same customer and stylist, and the original object is unchanged.
- A move that names a different stylist returns a booking with that stylist, and availability is checked against the new stylist, not the old one.
- Same slot with a different stylist is accepted; same slot with the same stylist is refused.
- Each refusal in rule 7 is triggered and reports its own reason.
- A move attempted exactly at the cutoff boundary, and one just either side of it.
- The rescheduled email subject contains the new slot.

Update the RESCHEDULE line in `docs/modules/ARCHITECTURE.md` to "Done." when finished.

## Decisions confirmed by the owner

- Customers can move an appointment up to 24 hours before it. Inside that window they phone the salon.
- The stylist stays the same unless the customer picks another one.
- Keeping the same time and changing only the stylist counts as a move.
- There is no limit on how many times a booking can be moved.
- The stylist is not notified when a booking moves; that is not part of this work.
