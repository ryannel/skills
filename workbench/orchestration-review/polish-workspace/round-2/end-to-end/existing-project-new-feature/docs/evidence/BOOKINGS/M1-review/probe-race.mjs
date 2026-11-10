// Reviewer probe: N separate processes race to record one slot on a fresh database file, 5 rounds.
// Usage: node probe-race.mjs <repo-root> [N]
import { mkdtempSync, writeFileSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { randomBytes } from 'node:crypto';
import { fork } from 'node:child_process';
import { DatabaseSync } from 'node:sqlite';
const root = process.argv[2];
const dir = mkdtempSync(join(tmpdir(), 'review-m1-race-'));
const settingsPath = join(dir, 's.json');
writeFileSync(settingsPath, readFileSync(join(root, 'config/salon.json')));
const key = randomBytes(32).toString('hex');
const spellings = ['2026-12-01T10:00:00+01:00', '2026-12-01T09:00:00Z', '2026-12-01T09:00:00.000Z', '2026-12-01T10:00:00.000+01:00',
  '2026-12-01T04:00:00.000000-05:00', '2026-12-01T14:30:00+05:30', '2026-12-01T10:00+01:00', '2026-12-01T09:00:00.0004Z'];
const N = +process.argv[3] || 24;
for (let r = 0; r < 5; r++) {
  const path = join(dir, `race-${r}.sqlite`);
  const ws = Array.from({ length: N }, (_, i) => {
    const w = fork(join(root, 'test-support/record-worker.js'), [path, settingsPath, key, spellings[i % spellings.length]], { stdio: ['ignore', 'ignore', 'pipe', 'ipc'] });
    const st = { msgs: [], err: '', code: null };
    w.on('message', m => { st.msgs.push(m); if (m === 'ready') st.ready?.(); });
    w.stderr.on('data', d => st.err += d);
    st.exited = new Promise(res => w.on('exit', c => { st.code = c; st.ready?.(); res(); }));
    st.readyP = new Promise(res => st.ready = res);
    st.w = w; return st;
  });
  await Promise.race([Promise.all(ws.map(s => s.readyP)), new Promise(r => setTimeout(r, 15000))]);
  ws.forEach(s => { try { s.w.send('go'); } catch {} });
  await Promise.race([Promise.all(ws.map(s => s.exited)), new Promise(r => setTimeout(r, 20000))]);
  ws.forEach(s => s.w.kill());
  const db = new DatabaseSync(path);
  const n = db.prepare('SELECT count(*) c FROM bookings').get().c, o = db.prepare('SELECT count(*) c FROM outbox').get().c; db.close();
  const tally = {}; ws.forEach(s => { const k = `${s.msgs.join('>')}|exit ${s.code}`; tally[k] = (tally[k] || 0) + 1; });
  const errLine = ws.map(s => s.err.split('\n').find(l => /Error|error/.test(l) && !/MODULE_TYPELESS/.test(l))).find(Boolean);
  console.log(`${N} processes, fresh file, round ${r}: rows=${n} outbox=${o} ${JSON.stringify(tally)}${errLine ? ' first error: ' + errLine : ''}`);
}
