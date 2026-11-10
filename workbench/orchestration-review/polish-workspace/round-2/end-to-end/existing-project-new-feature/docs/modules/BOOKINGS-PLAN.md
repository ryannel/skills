# BOOKINGS plan
Reviews: revised design approved at f570e63; docs/evidence/BOOKINGS/design-review.md; M1 awaits milestone review
Milestone: M1 Appointments are recorded, free times are right, and no stylist can be double-booked
Now: M1 claimed and ready for review (since 2026-11-10)
Next: M2 A move by private link follows the owner's rules exactly, and tells the customer and the salon
Blocked: none

## Before this plan: done
`createBooking` in `src/booking.js` and the email subject in `src/email.js`. No tests, no store, no cancel.

## M1 Appointments are recorded, free times are right, and no stylist can be double-booked: claimed
- [x] `config/salon.json` holds the salon settings; free times come from it and the store
- [x] A SQLite store whose unique rule uses normalized start instants, including equivalent ISO inputs
- [x] Recording issues its private link and queues an encrypted confirmation, recoverable after restart with an external key
- [x] Customers see "appointment", never "reservation"

## M2 A move by private link follows the owner's rules exactly, and tells the customer and the salon: not started
- [ ] `findByLink`, `freeTimesByLink`, `moveByLink`, `linkUrl` as in ARCHITECTURE.md
- [ ] Public-export acceptance proves nonempty default and selected-stylist listings, all lookup fields and refusal states, and reuse of the link after moving
- [ ] The 24-hour cut-off, same-stylist default, history entry and both emails, in one transaction
- [ ] An outbox sender with a development transport that writes emails to a folder
- [ ] A failure between updating the appointment and queuing both emails rolls back the appointment, history and outbox after reopening

## Log
- 2026-11-10 M1 claimed after all named checks and the project check passed on Node 24.16.0, with 14 tests. Evidence in docs/evidence/BOOKINGS/M1-check.json and M1-assessment.md covers both clock changes and boundary rules, nine-process normalized-start contention, store-enforced uniqueness, encrypted outbox persistence, new-process restart recovery and authentication failures. The constructor compatibility check and customer-text scan pass. Both M1 code questions were assessed by the builder. Independent milestone review remains for the lead.
- 2026-11-10 M1 runtime initialization uses `openStore({ path, outboxKey, settingsPath, clock })` from src/store.js. Recording returns `{ booking, token, url }` or a refusal reason. Private URLs use `/appointment/<token>`. Malformed or zone-less starts throw before writing. Isolated tests use direct SQL for cancelled fixtures and a trigger for rollback injection. Default salon contact details, hours and stylists are editable examples pending real owner settings. The full customer-page exports and sender remain M2. These implementation choices fill the open runtime details from the approved design review.
- 2026-11-10 Revised for docs/evidence/BOOKINGS/design-review.md at bb1ebc7. Resolved the token/outbox contradiction by encrypting complete email payloads before persistence with an externally supplied key. M1.3 now covers persisted outbox data and restart decryption. Added M2.9 to prove the customer-page contract through the public exports. Clarified normalized instants in the design, module interface and uniqueness proofs, same-transaction email insertion with failure rollback in M2.5, DST and horizon expectations in M1.1, and long-name email inspection in M2.8. The existing review remains Changes Requested until a new review approves this revision. The lead must run that review because this planning run cannot launch other agents.
- 2026-11-10 Dry-ran both milestones with `agent_loop.py check --module BOOKINGS --milestone M1 --worktree .` and the corresponding M2 command. M1 reported 2 pass and 4 fail, M2 reported 1 pass and 6 fail, with no check errors. The constructor and project check pass today. Feature-test files are absent and the existing email still says reservation, so those checks fail before implementation as expected.
- 2026-11-10 Planned from the brief and the owner's correction to decision 5: "they can't move it less than 24 hours before." Two milestones; APPOINTMENT_PAGE M2 needs M2.
- 2026-11-10 The module list said BOOKINGS covers creating and cancelling, done; the repository has no cancel function. Corrected the module list.
- Assumption: cancelling happens outside this repository or isn't built; this plan doesn't add it. A booking whose status isn't `confirmed` holds no slot, and its link shows it as cancelled.
- Assumption: the store built here becomes the salon's record of appointments, and appointments get into it through the new record operation. If the salon's bookings live in another system today, free times will be wrong until it feeds this store, and the owner should say where they live.
- Assumption: the customer value given to `createBooking` carries a name and an email address. Today's code doesn't say what it holds.
- Assumption: an appointment occupies one slot on a fixed grid set by the slot length in the settings (30 minutes unless the owner sets another). Services of different lengths are not modelled, since a booking has one `slot`.
- Assumption: free times are offered up to 8 weeks ahead, a setting the owner can change. The owner named no horizon.
- Assumption: the new time only has to be free and in the future (decision 4); it may itself be less than 24 hours away. The other reading, that the new time must also be 24 hours or more away, is one setting to change.
- Assumption: exactly 24 hours before the start still allows a move; "less than 24 hours" is refused.
- Assumption: emails go to an outbox and a development transport writes them to a folder. Choosing a real provider and sending real email is the owner's decision.
- Assumption: the store is one SQLite file on one machine (`node:sqlite`, built into Node 24, no new dependency). Running on several machines would need the double-booking rule revisited.
- Assumption: the planner chose the hosts: BOOKINGS is built on Codex, and reviewed on Claude.
- Assumption: retain the database-copy token-protection guarantee by encrypting complete durable email payloads with AES-256-GCM. The runtime supplies one 32-byte key outside the database and salon settings, shared by writers and sender and retained across restarts. A fresh demo store may use a fresh in-memory key. Losing or replacing the key prevents recovery of pending emails. Delivered development email files contain working links and require protection.
- Assumption: a horizon week is exactly 7 × 24 elapsed hours, with starts at its endpoint included and starts at now excluded. Grid labels in a DST gap are omitted and repeated labels offer both instants. Slots last elapsed minutes. Ambiguous opening uses the earlier instant and closing the later one. A nonexistent opening or closing uses the first valid instant after the gap.
