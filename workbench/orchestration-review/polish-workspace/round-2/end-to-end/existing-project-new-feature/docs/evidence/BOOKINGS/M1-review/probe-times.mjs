// Reviewer probe: independent brute-force oracle for free times.
// Usage: node probe-times.mjs <repo-root>
import { mkdtempSync, writeFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomBytes } from 'node:crypto';
const root = process.argv[2];
const { openStore } = await import(join(root, 'src/store.js'));
const { createBooking } = await import(join(root, 'src/booking.js'));
const base = JSON.parse(readFileSync(join(root, 'config/salon.json'), 'utf8'));
let failures = 0;
const log = (ok, msg) => { if (!ok) failures++; console.log(`${ok ? 'OK  ' : 'FAIL'} ${msg}`); };

// Oracle: scan every minute between now and horizon; an instant is a free start
// if its wall label is on the grid of an open weekday, and the elapsed slot
// [t, t+slot] stays inside the elapsed window [open instant, close instant], where
// open = earliest instant whose label >= open label on that local date, close = latest instant
// whose label <= close label... computed by minute scanning, not by the code under test.
function oracle(s, now) {
  const fmt = new Intl.DateTimeFormat('en-GB', { timeZone: s.timeZone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', weekday: 'short', hourCycle: 'h23' });
  const wd = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };
  const label = t => { const p = Object.fromEntries(fmt.formatToParts(t).map(x => [x.type, x.value])); return { date: `${p.year}-${p.month}-${p.day}`, wd: wd[p.weekday], min: +p.hour * 60 + +p.minute }; };
  const horizon = now + s.horizonWeeks * 7 * 864e5;
  const M = 60000;
  // per local date, collect instants (minute resolution) inside [open label, close label]
  const byDate = new Map();
  for (let t = Math.floor((now - 864e5) / M) * M; t <= horizon + 864e5; t += M) {
    const l = label(t); const h = s.openingHours[l.wd]; if (!h) continue;
    const [o, c] = h.map(x => +x.slice(0, 2) * 60 + +x.slice(3));
    if (!byDate.has(l.date)) byDate.set(l.date, []);
    byDate.get(l.date).push({ t, ...l, o, c });
  }
  const out = [];
  for (const mins of byDate.values()) {
    const inHours = mins.filter(m => m.min >= m.o && m.min <= m.c);
    if (!inHours.length) continue;
    const open = inHours[0].t, close = inHours.at(-1).t; // close label instant (latest)
    for (const m of inHours) {
      if (m.min < m.c && (m.min - m.o) % s.slotMinutes === 0 && m.t >= open && m.t + s.slotMinutes * M <= close && m.t > now && m.t <= horizon) out.push(m.t);
    }
  }
  return out.sort((a, b) => a - b);
}

function check(name, overrides, nowIso) {
  const dir = mkdtempSync(join(tmpdir(), 'review-m1-'));
  const settingsPath = join(dir, 's.json');
  const s = { ...base, ...overrides };
  writeFileSync(settingsPath, JSON.stringify(s));
  const now = Date.parse(nowIso);
  const store = openStore({ path: join(dir, 'b.sqlite'), outboxKey: randomBytes(32), settingsPath, clock: () => now });
  const got = store.freeTimes(s.stylists[0]).map(Date.parse);
  const want = oracle(s, now);
  const same = got.length === want.length && got.every((v, i) => v === want[i]);
  let diff = '';
  if (!same) {
    const g = new Set(got), w = new Set(want);
    diff = ` extra=${got.filter(x => !w.has(x)).slice(0, 4).map(x => new Date(x).toISOString())} missing=${want.filter(x => !g.has(x)).slice(0, 4).map(x => new Date(x).toISOString())}`;
  }
  log(same, `${name}: code ${got.length} slots, oracle ${want.length}${diff}`);
  store.close();
  return { store, got };
}

check('shipped config, 8 weeks across autumn change', {}, '2026-10-01T10:13:00Z');
check('shipped config, 8 weeks across spring change', {}, '2026-03-10T06:59:59.999Z');
check('shipped config, now exactly on a slot start', {}, '2026-12-01T08:00:00Z');
check('Stockholm 01:00-04:00 every day, 8 weeks over spring', { openingHours: Object.fromEntries([0,1,2,3,4,5,6].map(d => [d, ['01:00', '04:00']])) }, '2026-03-20T12:00:00Z');
check('Stockholm 01:00-04:00 every day, 8 weeks over autumn', { openingHours: Object.fromEntries([0,1,2,3,4,5,6].map(d => [d, ['01:00', '04:00']])) }, '2026-10-10T12:00:00Z');
check('Stockholm 00:00-23:59 every day, 15-min slots, autumn', { slotMinutes: 15, horizonWeeks: 2, openingHours: Object.fromEntries([0,1,2,3,4,5,6].map(d => [d, ['00:00', '23:59']])) }, '2026-10-20T00:00:00Z');
check('New York 00:30-04:00, 45-min slots, spring', { timeZone: 'America/New_York', slotMinutes: 45, horizonWeeks: 2, openingHours: Object.fromEntries([0,1,2,3,4,5,6].map(d => [d, ['00:30', '04:00']])) }, '2026-03-02T12:00:00Z');
check('New York 00:30-04:00, 45-min slots, autumn', { timeZone: 'America/New_York', slotMinutes: 45, horizonWeeks: 2, openingHours: Object.fromEntries([0,1,2,3,4,5,6].map(d => [d, ['00:30', '04:00']])) }, '2026-10-26T12:00:00Z');
check('Lord Howe (30-min DST) 01:00-03:00', { timeZone: 'Australia/Lord_Howe', horizonWeeks: 2, openingHours: Object.fromEntries([0,1,2,3,4,5,6].map(d => [d, ['01:00', '03:00']])) }, '2026-09-25T00:00:00Z');
check('Santiago (midnight DST) 00:00-02:00', { timeZone: 'America/Santiago', horizonWeeks: 2, openingHours: Object.fromEntries([0,1,2,3,4,5,6].map(d => [d, ['00:00', '02:00']])) }, '2026-08-30T00:00:00Z');
check('Santiago (midnight DST) autumn 00:00-02:00', { timeZone: 'America/Santiago', horizonWeeks: 2, openingHours: Object.fromEntries([0,1,2,3,4,5,6].map(d => [d, ['00:00', '02:00']])) }, '2026-03-30T00:00:00Z');
check('UTC, fractional horizon, closing between grid points', { timeZone: 'UTC', slotMinutes: 25, horizonWeeks: 0.5, openingHours: { 1: ['09:10', '17:05'], 3: ['09:10', '17:05'] } }, '2026-12-01T00:00:00Z');

// Editing the real config/salon.json in a copy of the repository changes the times (default settings path).
console.log(failures ? `${failures} FAIL` : 'all oracle comparisons agree');
