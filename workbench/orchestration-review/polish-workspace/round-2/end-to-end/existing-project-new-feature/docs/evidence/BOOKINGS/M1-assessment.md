# BOOKINGS M1 builder assessment

Target is Node 24.16.0 on this worktree, 2026-11-10. This is the builder's assessment for the claim. The lead runs the independent review.

## Assessment scope

The checklist for the code questions covers token generation, all SQL inputs, persisted database and WAL contents, nonce generation, key initialization, restart recovery, authentication failures, every appointment write, store uniqueness, contention fixtures and independently specified calendar expectations.

## M1.1

`M1-check.json` saves the exit code and output for `node --test test/bookings/free-times.test.js` on the node target. Eight tests pass. Expected lists are literal values, independent of the calculator. They cover Stockholm's spring gap and autumn repeat, both offset occurrences, nonexistent opening and closing boundaries, ambiguous opening and closing boundaries, elapsed slot duration, closing between grid points, exclusion of now, inclusion of the horizon endpoint, elapsed-week horizons across both clock changes, confirmed occupancy, other stylists, cancelled rows and live configuration edits. Each fixture uses a real temporary SQLite file and an injected clock. The default settings reader points at `config/salon.json`. Tests copy that file and edit an isolated settings path through the same reader.

## M1.2

`M1-check.json` saves the node contention check. Nine child processes open the same real database file, announce readiness and receive a common start signal. Offset, UTC and fractional-second spellings of one start yield one successful record, eight `taken` results, one booking and one encrypted outbox row. Direct SQL inserts and updates separately establish store enforcement, including the confirmed-only rule and rejection of text in the integer start column. Other stylists and cancelled rows may share a start. Invalid dates and starts without offsets leave both tables empty.

## M1.3 code question

Pass on the node target. `src/store.js` generates 32 random bytes per token and writes only its SHA-256 hash to the booking. Confirmation rendering, encryption and the authentication tag are completed in memory before either insert. SQL receives the booking fields and hash, then ciphertext, a fresh random 12-byte nonce and a 16-byte tag. Neither the key nor the plaintext email or token is bound to SQL. The key is supplied explicitly to `openStore`, copied into its closure and never persisted. Initialization rejects absent, string, short and long keys before opening a database.

The link-and-confirmation tests inspect booking and outbox rows and scan the live database, WAL and any journal or shared-memory files for raw tokens, URLs, raw/hex/base64 key values and rendered email markers. The two messages have different nonces. After closing the original store, a new Node process receives the original external key, opens the file and decrypts both messages. Its output agrees with a reopened store. The confirmation carries the time, stylist and a URL whose token resolves to the recorded appointment. Unknown tokens find nothing. A wrong key or a flipped ciphertext byte fails authenticated decryption and leaves the row pending. An SQL trigger that aborts the outbox insert rolls back the appointment too, verified after reopening. Detailed test output and exit status are in `M1-check.json`.

## M1.4

The constructor is unchanged. The exact compatibility assertion in the done-when file passes on Node. Its output and exit code are in `M1-check.json`.

## M1.5

The named source/config text scan passes. Its output and exit code are in `M1-check.json`.

## M1.6 code question

Pass for the M1 write paths. The sole appointment write is `recordBooking` in `src/store.js`. It parses an explicit-offset ISO start into integer epoch milliseconds before writing, opens `BEGIN IMMEDIATE`, inserts the booking and encrypted outbox row, and commits both together. A confirmed-only unique index over `(stylist, start_ms)` is the authority for conflicts. A violation is returned as `taken` after rollback. The direct-SQL tests prove the store enforces the rule even when the recording operation is bypassed. M1 adds no move write. The future move operation belongs to M2 and must use this same rule.

All acceptance tests use real files. The calendar tests inject their clocks and spell out expected instants for both DST changes, closing and the horizon. The contention test uses separate processes. No proxy target or mock store is used.

## Runtime choices

M1 initializes through `openStore({ path, outboxKey, settingsPath, clock })` from `src/store.js`. The required key is a 32-byte Uint8Array or Buffer. The optional settings path defaults to `config/salon.json`, and the clock defaults to `Date.now`. The returned methods include `recordBooking`, `freeTimes`, `findByLink`, `linkUrl`, `pendingConfirmations` and `close`. Recording accepts the unchanged constructor's confirmed booking with customer name and email. Success returns `{ booking, token, url }`, while a conflict returns `{ reason: 'taken' }`. The M1 lookup is for persistence verification. The full customer-page contract and delivery sender are M2 work.

Private URLs use `/appointment/<token>` under the configured public address. Malformed starts throw a TypeError before writing. Test-only cancelled fixtures use SQL, and failure injection uses a database trigger. The default salon name, contact details, Monday-to-Friday 09:00–17:00 hours and Sam/Alex stylist list are editable example settings because the owner has not supplied real salon values. The zone is Europe/Stockholm, slots are 30 minutes and the horizon is eight weeks, following the plan's assumptions.

## Automated verification

The required `agent_loop.py check --module BOOKINGS --milestone M1 --worktree .` passes. `M1-check.txt` saves its summary. `M1-check.json` saves each named check's exit code and output tail and the passing project check. The project check runs 14 passing tests. Node emits its existing package module-type warning. No dependencies were added.
