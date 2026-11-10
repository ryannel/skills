# BOOKINGS M1 review

Milestone: M1, "Appointments are recorded, free times are right, and no stylist can be double-booked".
Commit: bf25938, in a clean checkout. Target: node, run on Node v24.16.0 (macOS).
Reviewer: Claude, as an independent reviewer. This is the first review of M1, so there are no earlier Must Fix findings to recheck.
Graded examples: the project has no `docs/evidence/graded-examples.md` yet, so I used the starting set that comes with the skill.

**Result: PASS.** All six items pass. I found no Must Fix inside or outside the items. There are four Suggestions.

## Evidence (my own runs, not the builder's)

- [named-checks.txt](M1-review/named-checks.txt): every `check` command from the done-when file, with its exit code. All exit 0.
- [npm-test.txt](M1-review/npm-test.txt): `npm test` runs 14 tests, and all 14 pass.
- [probes-output.txt](M1-review/probes-output.txt): output from my three probe scripts.
  - [probe-times.mjs](M1-review/probe-times.mjs): free times compared against a brute-force oracle. The oracle scans every minute and labels it with `Intl` without using `src/times.js`.
  - [probe-store.mjs](M1-review/probe-store.mjs): edits the real `config/salon.json` in a copy of the repository, then probes normalization, persisted secrets and near-miss tokens.
  - [probe-race.mjs](M1-review/probe-race.mjs): separate processes race to record one slot in a fresh database file.
- [off-grid-recording.txt](M1-review/off-grid-recording.txt): the output behind Suggestion 1.

Edge conditions I ran for the node target, as the project settings list them:

| Edge condition | What I ran |
|---|---|
| DST change | Stockholm in spring and autumn. New York in both directions with 45-minute slots and 00:30 opening. Lord Howe, which has a 30-minute DST shift. Santiago, where the clocks change at midnight so 00:00 doesn't exist one day. |
| End of the booking horizon | Eight-week horizons across both Stockholm changes. A fractional horizon (0.5 weeks). `now` falling exactly on a slot start. |
| Closing time | A 25-minute grid whose closing falls between grid points. Opening hours running from 00:00 to 23:59. |
| Concurrent writers | 24 and 48 separate processes, five rounds each. Each round used a fresh database file with no schema yet, and eight different spellings of one instant. |

## Items

### M1.1 Free times: pass

I ran the check `node --test test/bookings/free-times.test.js`. It exits 0, with 8 passing tests.

I worked out the test's expected lists myself before reading the builder's notes. All of them agree with the design and with real Stockholm transitions:
- Spring: on 2026-03-29 at 01:00Z the clock goes from 02:00 to 03:00, so 01:00 and 01:30 are listed at +01:00, and 03:00 and 03:30 at +02:00.
- Autumn: the repeated 02:00 and 02:30 appear twice, in instant order.
- An opening or closing time inside the spring gap moves to the first valid instant after the gap.
- An ambiguous opening uses the earlier occurrence, and an ambiguous closing uses the later one.
- With a 90-minute slot, slot length is counted in elapsed minutes.
- `now` itself is excluded, and the horizon endpoint is included. The autumn test shows the horizon is counted in elapsed hours, not wall-clock days: 09:00 local seven days later falls one hour after the horizon and is correctly left out.

My brute-force oracle agreed with `freeTimes` on 12 scenarios out of 12, covering every edge condition in the table above (see [probes-output.txt](M1-review/probes-output.txt)).

The item asks that editing `config/salon.json` changes the times. The tests edit a copy of the settings, so I edited the real `config/salon.json` in a full copy of the repository and opened the store with the default settings path. The free times changed on the next call with no restart, and a stylist added in the file got free times too.

Confirmed appointments remove their slot only for their own stylist. Cancelled rows free their slot again. An unknown stylist gets an empty list.

### M1.2 No double booking across processes: pass

I ran the check and it exits 0, with 3 passing tests. The test starts 9 processes with `fork`, waits for every one to report ready, then releases them together on one real file, using four spellings of one instant. Exactly one records, and 8 get `taken`.

I ran a harder version myself, starting from a fresh file each time so schema creation races too:
- Rounds: 5 rounds with 24 processes, then 5 rounds with 48.
- Spellings: `+01:00`, `Z`, `.000Z`, `.000+01:00`, `.000000-05:00`, `+05:30`, `10:00+01:00` with no seconds, and `.0004Z`.
- Outcome of every round: exactly 1 recorded and the rest `taken`. Each round left 1 booking row and 1 outbox row, and every process exited 0.

### M1.3 Private link and encrypted confirmation: pass

I ran the check and it exits 0, with 3 passing tests.

Answer to the Reviewer Question: yes. I read `src/store.js` lines 58–111 and the tests.
- **Token:** made from `randomBytes(32)`, so 256 bits. Only its SHA-256 hex is written, to `bookings.token_hash`.
- **Encryption:** the confirmation is rendered and encrypted in memory before the transaction starts (lines 69–73). SQL receives only `nonce`, `ciphertext` and `tag`.
- **Nonces and tags:** AES-256-GCM, with a fresh `randomBytes(12)` nonce for each message and the default 16-byte tag. The test asserts the nonce and tag lengths, and that two messages have different nonces.
- **Key:** passed in by the caller to `openStore`. It is never bound to SQL.
- **Missing or malformed key:** `undefined`, a string, 31 bytes and 33 bytes each throw before the database is opened (lines 13–15, and the test at line 60).
- **Restart:** after the original store is closed, a new Node process decrypts both messages with the original key. The link in the email resolves to the appointment.
- **Wrong key or tampering:** a wrong key, or one flipped ciphertext byte, throws `Unsupported state or unable to authenticate data`. The row stays pending.
- **Unknown tokens:** an unknown token, `undefined`, the real token with one extra character, and the real token in upper case all return nothing (my probe covers the last two).
- **Persisted files:** the test scans the live database, `-wal`, `-journal` and `-shm` files for the raw token, the URL, the key in raw, hex and base64 forms, and plaintext markers from the email. My probe repeated the scan for the token, the URL and the path fragment `appointment/` on a 86 KB WAL. None were found.

The confirmation contains the time, the stylist and the link, and says "appointment".

### M1.4 `createBooking` unchanged: pass

The check exits 0. `src/booking.js` is not in the diff. `recordBooking` builds its stored value by spreading `createBooking(...)` and adding `id` to a new object, so the constructor's return value is not changed.

### M1.5 No "reservation": pass

The check exits 0. The diff changes the only occurrence, the email subject, to "Your appointment on …". The new confirmation body says "appointment" throughout.

### M1.6 The store enforces uniqueness: pass

Answer to the Reviewer Question: yes, for every write that exists in M1. Moving is M2 work and isn't in this diff.
- **The only write path:** `recordBooking` is the only code that writes an appointment.
- **Normalization:** it normalizes the start with `startInstant`. That accepts only explicit-offset ISO strings and returns `Date.parse` epoch milliseconds, which are checked to be a safe integer.
- **Transaction:** it opens `BEGIN IMMEDIATE` and inserts the booking and its outbox row in one transaction. It never checks whether a slot is free before writing.
- **Conflicts:** the partial unique index `confirmed_stylist_start ON bookings(stylist, start_ms) WHERE status = 'confirmed'` decides conflicts. A violation (`errcode` 2067, naming those columns) is rolled back and returned as `taken`.
- **Column type:** the table is `STRICT`, so a text start is rejected. The test asserts this.
- **Direct SQL:** a duplicate confirmed insert is rejected, and so is an update from cancelled to confirmed. A cancelled row may share a slot.
- **Test setup:** the tests use real temporary SQLite files, a separate forked process for each writer, and an injected clock. The instant lists for both DST changes, closing and the horizon are literal values, and I confirmed them independently (see M1.1).

## Changed lines read

I read the whole diff of bf25938:
- **Code and settings:** `src/store.js`, `src/times.js`, `src/settings.js`, `src/email.js` and `config/salon.json`.
- **Tests and helpers:** the three test files and the three `test-support` files.
- **The builder's documents:** the evidence files and its changes to the done-when file and the plan.

I looked for the signs of work that only looks finished:
- No hard-coded return values or canned data. The `freeTimes` results come from the grid and the store.
- No feature flags, and no branches that run only under test. The clock and settings path can be injected, and default to `Date.now` and `config/salon.json`.
- No tests were weakened or skipped.
- No warnings were silenced. The `MODULE_TYPELESS_PACKAGE_JSON` warning was already there before this milestone.
- No output files were committed in place of being computed.

The builder's changes to the done-when file touch only `status` and `evidence`.

## Findings

None are Must Fix. All of the following are Suggestions.

1. **Suggestion (verified): recording accepts times that aren't on the grid, outside opening hours, or in the past.**
   - What I did: I called `recordBooking` with these starts:
     - `2026-12-01T10:15:00+01:00`, which is off the grid.
     - `22:00` that day, which is after closing.
     - A date in 2020, which is in the past.
     - A Sunday, when the salon is closed.
   - What happened: all four were recorded. With 10:15 held, `freeTimes('Sam')` still offers 10:00 and 10:30, so a move in M2 could land in an overlapping half-hour. See [off-grid-recording.txt](M1-review/off-grid-recording.txt), made by [probe-off-grid.mjs](M1-review/probe-off-grid.mjs).
   - Why this isn't Must Fix: the design only asks that recording refuses a slot that is `taken`. Nothing in the product calls `recordBooking` yet.
   - Proposal: the planner decides whether recording should reject starts that aren't free-time candidates, or at least starts off the grid, before something that records appointments for the salon is wired in.
   - Where: `src/store.js` lines 58–68.
2. **Suggestion (verified by reading): the encryption isn't tied to its row.** AES-GCM is used without additional authenticated data, so someone with write access to the database could swap ciphertext between outbox rows without the decryption noticing. Binding the outbox `id` and `booking_id` as additional authenticated data (`setAAD`) would stop this. It isn't required by M1.3 or the design. Where: `src/store.js` lines 71 and 106.
3. **Suggestion (verified by reading): the settings file doesn't say how weekdays are numbered.** `config/salon.json` keys opening hours by JavaScript weekday numbers (`0` is Sunday). This is the one file the owner edits, and nothing tells the owner the numbering. Weekday names, or a note in the plan or the README, would prevent an owner opening on the wrong days. Where: `config/salon.json` and `src/times.js` line 73.
4. **Suggestion (suspected, not reproduced with realistic hours): a repeated closing time drops one slot.** When closing time falls on a repeated autumn label, the grid stops at the closing label, not at the closing instant. For example, with hours 02:00–02:30 on 2026-10-25, the first 02:30 (+02:00) isn't offered, even though it ends before the later 02:30. The design's "until the last one that ends by closing" can be read either way, and no salon opens across 02:00–03:00. Where: `src/times.js` line 80.

None of these is a hole that would let a convincing fake pass an item. The items held up against my oracle and my stress runs, so I propose no new item.

PASS M1
