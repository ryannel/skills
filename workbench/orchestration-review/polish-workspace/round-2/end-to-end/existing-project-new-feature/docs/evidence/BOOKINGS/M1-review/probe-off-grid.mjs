import { mkdtempSync, writeFileSync, readFileSync } from 'node:fs'; import { tmpdir } from 'node:os'; import { join } from 'node:path'; import { randomBytes } from 'node:crypto';
const root = process.argv[2]; const { openStore } = await import(join(root, 'src/store.js')); const { createBooking } = await import(join(root, 'src/booking.js'));
const d = mkdtempSync(join(tmpdir(), 'og-')); const sp = join(d, 's.json'); writeFileSync(sp, readFileSync(join(root, 'config/salon.json')));
const s = openStore({ path: join(d, 'b.sqlite'), outboxKey: randomBytes(32), settingsPath: sp, clock: () => Date.parse('2026-12-01T07:00:00Z') });
for (const slot of ['2026-12-01T10:15:00+01:00', '2026-12-01T22:00:00+01:00', '2020-01-01T10:00:00+01:00', '2026-12-06T10:00:00+01:00']) console.log(slot, '->', s.recordBooking(createBooking({ name: 'A', email: 'a@x' }, 'Sam', slot)).reason ?? 'recorded');
console.log('free around 10:15:', s.freeTimes('Sam').filter(t => t.startsWith('2026-12-01T10')));
