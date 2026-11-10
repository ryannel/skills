# BOOKINGS design review (round 2)

Result: approved. No Must Fix findings. Six Suggestions are listed for the planner's next turn.

## Scope

I reviewed the integrated tip `277fe2c` against the previous round at `bb1ebc7`. I read ORCHESTRATE.md, both
verbatim briefs in BOOKINGS-ACCEPTED.json (the owner's request, and the loop's "Revise BOOKINGS's design and plan as
docs/evidence/BOOKINGS/design-review.md asks"), BRIEF.md, GLOSSARY.md, ARCHITECTURE.md (including its diff since
`bb1ebc7`), BOOKINGS.md, BOOKINGS-PLAN.md and every item in BOOKINGS-DONE.json. I read each item that changed in
full: M1.1, M1.2, M1.3, M1.6, M2.3, M2.5, M2.6, M2.8 and the new M2.9. I also read the APPOINTMENT_PAGE design,
plan and items that use the interface, and the current `src/booking.js` and `src/email.js`. The project has no
graded-examples file yet, so I used the skill's starting set.

This is a design review, so nothing has been built yet to run. I checked the design's DST worked example against
Node 24.16's `Intl` data for `Europe/Stockholm`. 2026-03-29 goes from 01:30 +01:00 to 03:00 +02:00. On
2026-10-25, 02:00 and 02:30 occur first at +02:00 and then at +01:00. Both days match BOOKINGS.md exactly. I made
no captures.

## Previous Must Fix findings

### 1. The outbox contradicted the database token-protection guarantee: resolved

BOOKINGS.md now encrypts every complete email payload with AES-256-GCM before it reaches SQL. Each message gets a
fresh 96-bit nonce. The 32-byte key is held outside the database and the salon settings, and the design says the
raw token and the rendered plaintext never enter SQL, including temporary tables and error records. The
guarantee has been narrowed to fit: a copy of the database (with its journal or WAL, and pending or sent outbox
rows) yields no token without the key. The design also says outright that delivered emails and the
development-transport files contain working links.

The design covers what happens on restart: the original key decrypts pending mail, a missing or malformed key
fails initialization, a wrong key or tampered ciphertext leaves the message unsent with a delivery error, and losing
the key loses pending mail. That last point is logged as an assumption. ARCHITECTURE.md carries the key
requirement across the module boundary, including the demo's in-memory key for a fresh store.

M1.3 now requires that persisted booking rows and pending outbox data expose no usable token, plaintext link or
key. Its `ask` extends that to the journal or WAL, nonce freshness, restart decryption and both failure modes. M2.6
covers the sent outbox rows. A test that checks only the hash column no longer satisfies the item, so the fake I
raised last round is closed.

### 2. The customer-page interface lacked an acceptance proof: resolved

The new item M2.9 adds a check (`test/bookings/page-interface.test.js`) and an `ask`. Together they require the
public exports against a real store to do all of the following:

- return every lookup field, including the eligibility reason and the salon's name and phone
- list nonempty selectable stylists and the expected free times, both for the default stylist and for an explicit one
- show the updated details after a move through the same token
- return nothing for an unknown link
- give reasons and empty listings for cancelled and inside-cut-off links
- build `linkUrl` from the configured public address

BOOKINGS.md now requires fixtures with free slots so that "an always-empty result fails". The fake I raised last
round would fail this item, because it returned no times for every token.

## Previous Suggestions

1. **Canonical instant:** taken up. Starts are normalized to integer epoch milliseconds, with examples in
   BOOKINGS.md and ARCHITECTURE.md. Equivalent spellings are part of M1.2 and M2.3, and the M1.6 `ask` checks the
   normalization on every write.
2. **Same-transaction emails with injected-failure rollback:** taken up in M2.5 and M2.6.
3. **DST and horizon rules, and long names:** taken up. The design gives explicit rules for times that don't exist
   or occur twice, for ambiguous opening and closing times, and for elapsed-week horizon endpoints, with a worked
   example. M2.8 now inspects long customer and stylist names.

## Changed items

I checked each changed item for whether the revision made its proof easier to pass.

| Item | What changed | Easier to fake? |
| --- | --- | --- |
| M1.1 | It now cites the design's explicit DST, closing and horizon rules, and expected instant lists. "At closing time and at the horizon's end" became "boundary cases". | No. The new rules make the expected results determinable, and the M1.6 `ask` names closing and the elapsed-week horizon. See Suggestion 5. |
| M1.2 | Uniqueness is now per start instant, and equivalent ISO spellings are covered. | No, it is sharper. |
| M1.3 | Encryption, persisted-data exposure, restart recovery and an `ask`. | No, it is sharper. |
| M1.6 | The `ask` now names normalization, separate processes and independently expected instant lists. It drops the explicit "no check-then-write path" wording. | No. A check made before writing is harmless while the confirmed-only index still enforces uniqueness in the same transaction, and the `ask` still requires that. |
| M2.3 | Equivalent ISO spellings were added. | No, it is sharper. |
| M2.5 | Same-transaction queuing, injected-failure rollback after reopening, and encrypted delivery after restart. The explicit list of email contents became "the required details". | Slightly vaguer on content. M2.8 covers it. See Suggestion 3. |
| M2.6 | Real-file tests for each refusal and for the injected failure, reopening the store, decrypted contents, and no plaintext in pending or sent rows. | No, it is sharper. |
| M2.8 | Long names were added. | No, it is sharper. |
| M2.9 | New: the public-interface acceptance test. | Not open to the fake from round 1. A reviewer can judge it. |

The unchanged items (M1.4, M1.5, M2.1, M2.2, M2.4 and M2.7) still stand as assessed in round 1.

## Must Fix findings

None. The revision breaks nothing that the request, the brief or the interface depends on. I found nothing from
round 1 that rises to a Must Fix.

## Suggestions

1. **Say how BOOKINGS receives its key and store path, and what the record operation returns.** I verified this by
   reading the documents. ARCHITECTURE.md says "the runtime supplies" the key, and that the four exports are plain
   functions that take no key or store. ORCHESTRATE.md says the demo takes the store's path from the environment.
   Neither document names the mechanism: an environment variable, or an `open({ path, key })` call made before the
   exports work. The APPOINTMENT_PAGE demo has to "print each private link". The token exists only in memory and
   inside encrypted payloads, so the record operation must return the token or link to its caller, and that isn't
   written down either. This isn't a Must Fix, because APPOINTMENT_PAGE M2 starts only after BOOKINGS M2 is Done and
   can adopt whatever BOOKINGS exports. Naming it now avoids an interface change being settled later in a plan log.
2. **Name the failure-injection seam for M2.5.** The item needs a failure after the appointment update and before
   both emails are queued. Without a stated mechanism, a builder may add a branch that runs only under test, which
   the next review should treat as suspect. Two clean options are a SQLite trigger that the test installs to
   `RAISE(ABORT)` on the second outbox insert, or an outbox writer passed in from outside. State which one is
   acceptable.
3. **Restore the explicit email contents in M2.5's statement.** Round 1 listed the customer email's new time,
   stylist and same link, and the salon email's who, from, to and stylist. These became "the required details".
   M2.8 still inspects them, so nothing is lost overall, but the automated check is the one that runs on every
   change.
4. **Say how tests produce a cancelled appointment.** M2.6 and M2.9 need one. The plan assumes cancelling isn't
   built here, and BOOKINGS.md says "Nothing else writes the store". State whether tests may set `status` through
   SQL, or whether the record operation takes a status, so that the reviewer doesn't read a test-only write path as
   a defect.
5. **Name closing and the horizon end in M1.1's statement**, as round 1 did, rather than "boundary cases". The
   M1.6 `ask` names them, so M1.1 can still be judged as written.
6. **Say how malformed starts are treated.** BOOKINGS.md normalizes "offset-bearing inputs" and doesn't say what
   happens to a start with no offset, or with seconds off the grid. On-grid checking would refuse the second case as
   `not_free`. Say that a start with no offset is refused as `not_free` rather than read in the server's zone.

DESIGN OK
