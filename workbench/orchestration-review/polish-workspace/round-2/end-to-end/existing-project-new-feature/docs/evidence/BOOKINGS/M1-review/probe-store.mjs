// Reviewer probe: real config edit, fresh-file normalization, persisted secrets.
// Usage: node probe-store.mjs <repo-root>
import { mkdtempSync, writeFileSync, readFileSync, cpSync, existsSync, readdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomBytes } from 'node:crypto';
import { fork } from 'node:child_process';
import { once } from 'node:events';
import { DatabaseSync } from 'node:sqlite';
const root = process.argv[2];
let failures = 0;
const log = (ok, msg) => { if (!ok) failures++; console.log(`${ok ? 'OK  ' : 'FAIL'} ${msg}`); };

// 1. Edit the real config/salon.json of a full copy of the repository, using the default settings path.
const copy = mkdtempSync(join(tmpdir(), 'review-m1-repo-'));
for (const d of ['src', 'config', 'package.json']) cpSync(join(root, d), join(copy, d), { recursive: true });
const { openStore } = await import(join(copy, 'src/store.js'));
const { createBooking } = await import(join(copy, 'src/booking.js'));
const dbDir = mkdtempSync(join(tmpdir(), 'review-m1-db-'));
const now = Date.parse('2026-11-30T12:00:00Z'); // Monday 13:00 Stockholm
const store = openStore({ path: join(dbDir, 'b.sqlite'), outboxKey: randomBytes(32), clock: () => now });
const before = store.freeTimes('Sam');
// now (13:00) is excluded; the horizon endpoint (13:00 eight weeks later) is included: 640 = 8*5*16 - 9 + 9
log(before[0] === '2026-11-30T13:30:00+01:00' && before.length === 640, `default config: first ${before[0]}, ${before.length} times`);
const cfgPath = join(copy, 'config/salon.json');
const cfg = JSON.parse(readFileSync(cfgPath, 'utf8'));
writeFileSync(cfgPath, JSON.stringify({ ...cfg, slotMinutes: 60, horizonWeeks: 1, stylists: ['Sam', 'Alex', 'Kim'], openingHours: { 6: ['10:00', '12:00'] } }));
const after = store.freeTimes('Sam');
log(JSON.stringify(after) === JSON.stringify(['2026-12-05T10:00:00+01:00', '2026-12-05T11:00:00+01:00']), `after editing config/salon.json (no restart): ${JSON.stringify(after)}`);
log(store.freeTimes('Kim').length === 2, 'stylist added in config/salon.json gets times');
writeFileSync(cfgPath, JSON.stringify(cfg));
store.close();

const fresh = mkdtempSync(join(tmpdir(), 'review-m1-norm-'));
const settingsPath = join(fresh, 's.json');
writeFileSync(settingsPath, JSON.stringify(cfg));

// 3. Same instant, different stylist, still allowed; distinct sub-second starts are distinct.
const p3 = join(fresh, 'norm.sqlite');
const s3 = openStore({ path: p3, outboxKey: randomBytes(32), settingsPath, clock: () => now });
const mk = (slot, st = 'Sam') => s3.recordBooking(createBooking({ name: 'Ana', email: 'a@example.com' }, st, slot));
const a = mk('2026-12-01T10:00:00+01:00');
log(!!a.token, 'record 10:00+01:00');
log(mk('2026-12-01T09:00:00.000999Z').reason === 'taken', 'sub-millisecond spelling 09:00:00.000999Z is the same slot (taken)');
log(mk('2026-12-01T10:00:00+01:00', 'Alex').token, 'other stylist same instant recorded');
log(mk('2026-12-01T10:00:00+01:00', 'Nobody').reason === 'unknown_stylist', 'unknown stylist refused');
let threw = 0; for (const bad of ['2026-12-01T10:00:00+0100', '2026-12-01 10:00:00+01:00', '2026-12-01T10:00:00+25:00']) { try { mk(bad); } catch { threw++; } }
log(threw === 3, `malformed offsets throw before writing (${threw}/3)`);

// 4. Persisted files contain no token, URL or key; customer data in plaintext is expected.
const secrets = [a.token, a.url, 'appointment/'];
for (const f of readdirSync(fresh).filter(f => f.startsWith('norm.sqlite'))) {
  const data = readFileSync(join(fresh, f));
  log(secrets.every(x => !data.includes(x)), `${f}: no token/url in ${data.length} bytes`);
}
log(s3.pendingConfirmations().length === 2 && s3.pendingConfirmations()[0].email.text.includes(a.url), 'pending confirmations decrypt with the key and carry the link');
log(s3.findByLink(a.token + 'x') === undefined && s3.findByLink(a.token.toUpperCase()) === undefined, 'near-miss tokens find nothing');
s3.close();
console.log(failures ? `${failures} FAIL` : 'all store probes pass');
