# BOOKINGS design review

Result — changes requested, with two Must Fix findings.

## Scope and request

Reviewed the integrated tip `bb1ebc7`. Read ORCHESTRATE.md, the single verbatim task in BOOKINGS-ACCEPTED.json, BRIEF.md, ARCHITECTURE.md, GLOSSARY.md, BOOKINGS.md, BOOKINGS-PLAN.md, every item in BOOKINGS-DONE.json, the adjoining APPOINTMENT_PAGE design, and the existing booking constructor and email subject. There is no previous design review or project graded-examples file. Applied the skill's starting graded examples.

The request is customer self-service moves through the confirmation email's private link, preserving the stylist unless the customer chooses another and refusing moves less than 24 elapsed hours before the stored appointment. The approved brief also requires free times, immediate release of the old slot, another working link after each move, notice emails and move history. The design covers these behaviours in principle. Its fixed duration grid, eight-week horizon, single-machine store, new recording operation, future-only destination rule and development email transport are explicitly recorded assumptions. They do not silently narrow the request. Creating bookings currently means a pure constructor, and that behaviour is preserved. There is no existing cancellation implementation to preserve.

This is a design review. Planned tests and product targets were assessed for judgeability, without treating their absence before implementation as a failure. No runtime captures were needed.

## Must Fix findings

### 1. The outbox contradicts the database token-protection guarantee

Verified design contradiction. BOOKINGS.md lines 59–60 promise that the store keeps only a token hash and a leaked database yields no working links. Lines 73–81 put confirmation and moved emails, including the working private link, into an outbox table in that database. M1.3 also requires hash-only token storage while queuing the confirmation.

Follow an ordinary appointment recording before the sender runs. Read the queued confirmation body from the outbox and extract its link. The link must work for the customer, so it also works for someone holding the database. Marking the email sent does not resolve the exposure while it is pending, and the design specifies no removal of the body afterward.

Specify a coherent treatment of the token in the durable outbox and the corresponding security guarantee. If retaining the database-leak guarantee, explain how the sender recovers the working link after restart without the database alone containing that capability, for example through encryption with a key held outside the database. Align M1.3 with that mechanism and require inspection of persisted outbox data as well as the booking row. A test that merely checks the booking's hash field would pass an implementation that violates the stated guarantee.

### 2. The customer-page interface lacks an acceptance proof

Verified acceptance gap. ARCHITECTURE.md's BOOKINGS-to-APPOINTMENT_PAGE interface requires `findByLink` to return customer details, current appointment, salon details and move eligibility, and `freeTimesByLink` to return selectable stylists and free times for the appointment's stylist by default, with empty results when moving is forbidden. BOOKINGS.md line 91 and the M2 plan promise these operations. No item explicitly checks those successful lookup and listing behaviours through the exported interface.

A convincing incomplete implementation could have a correct internal free-time calculator, working moves and emails, and unknown-token lookup, but return empty times from `freeTimesByLink` for every token. It could satisfy the listed free-time, move and unknown-token checks and both code-boundary questions. The customer page would never offer a time. Similarly, the listed checks do not require a known link to return the salon phone or the eligibility reason the page needs.

Add an acceptance proof through the public exports. Record an appointment, resolve its link, list times with the same stylist by default and with an explicitly selected stylist, move it, and resolve the same link again. Include unknown, cancelled and inside-cut-off links, verifying the documented fields and reasons and the empty listing for unmovable appointments. Include `linkUrl` using the configured public address. This can extend existing test files. It needs an explicit statement so the integration contract cannot be omitted while the lower-level tests pass.

## Suggestions

1. Specify a canonical instant for the uniqueness key and enforce it on recording and moving. BOOKINGS.md lines 29–31 and 49 describe an index on start time and storage with an offset, without defining its representation. Even the salon-offset strings `2026-12-01T10:00:00+01:00` and `2026-12-01T10:00:00.000+01:00` represent the same instant. A numeric instant or canonical serialization makes the intended index dependable. Add an equivalent-input case to M1.2/M1.6. The design already requires uniqueness by instant, so this is implementation clarification rather than a separate blocker.

2. Sharpen M2.5's phrase “in its own transaction” to require the same transaction as the appointment and history update. The design and M2 quality bar already require this. Inject a failure after the appointment update but before both emails are queued, then reopen the store and verify complete rollback. The existing refusal checks in M2.6 cover refused requests, which may all fail before the update begins.

3. Before implementation, state how grid generation handles nonexistent and repeated local times and whether the horizon is elapsed weeks or local calendar days. M1.1 is judgeable once these expected results are fixed. Its existing requirement to test both clock changes is appropriate. M2.8's future inspection should also exercise long customer and stylist names, as ORCHESTRATE.md requires.

## Done-when item assessment

All fourteen items were read. These are assessments of the planned proofs, not milestone verdicts.

| Item | Design-review assessment |
| --- | --- |
| M1.1 | Judgeable with configured opening hours, a controlled clock and explicit expected slot lists across both clock changes, closing and horizon boundaries. See suggestion 3. |
| M1.2 | Separate processes against one real file can prove contention and exactly one winner. See suggestion 1. |
| M1.3 | Recording, entropy source, unknown lookup and confirmation are judgeable. Its hash-only requirement conflicts with the outbox mechanism, covered by Must Fix 1. |
| M1.4 | The executable assertion matches the current constructor. Reading its small implementation can confirm preservation across supported values. |
| M1.5 | The source/config text scan is executable and catches the current email subject. M2.8 additionally checks generated emails. |
| M1.6 | The question directs the reviewer to all writes, database enforcement, actual files and clock control. This guards against a mocked concurrency proof. |
| M2.1 | Judgeable at exactly 24 hours and just inside it, including elapsed-time boundaries across DST. |
| M2.2 | Judgeable through successful default and explicit stylist moves, invalid stylist and each category of unavailable start. This does not establish listing and lookup, covered by Must Fix 2. |
| M2.3 | Real-process contention and immediate observation of both old and new slots provide a meaningful proof. |
| M2.4 | Persisted history can be checked against before/after records and a controlled clock, including repeated moves. |
| M2.5 | Email contents, recipients, stable links and restart delivery are judgeable. See suggestion 2 for a sharper atomicity proof. |
| M2.6 | The question explicitly covers all documented refusal reasons and persistent side effects using a real file. |
| M2.7 | Reading every move/retry path can judge preservation of the stylist. |
| M2.8 | Generated confirmation, moved and salon-notice emails can be inspected against the clarity bar for each named scenario. Include the project's long-name edge condition. |

The mechanisms for elapsed cut-off checks inside the write transaction, same-stylist preservation, transactional history and outbox insertion, and single-file database uniqueness are suitable for the scoped product. The two Must Fix findings concern a contradictory security mechanism and an unproved interface needed to deliver the requested customer flow.

DESIGN CHANGES: 2 blocking findings
