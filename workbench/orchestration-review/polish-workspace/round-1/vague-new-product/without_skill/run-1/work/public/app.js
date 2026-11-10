(() => {
'use strict';

const MAX_DAYS = 42;  // the rule: nothing stays up more than 6 weeks
const WARN_DAYS = 28; // amber from 4 weeks
// Hold colour -> [fill, text colour that reads on it]
const COLOURS = {
  red: ['#d93636', '#fff'], orange: ['#f08423', '#1b1b1b'], yellow: ['#f0c80e', '#1b1b1b'], green: ['#2f9e52', '#fff'],
  blue: ['#2c6fd9', '#fff'], purple: ['#7c4cc4', '#fff'], pink: ['#ec6aa8', '#1b1b1b'], black: ['#1b1b1b', '#fff'],
  white: ['#fafafa', '#1b1b1b'], grey: ['#8b9099', '#1b1b1b'],
};
const GROUPS = { over: 'Strip now', warn: 'Due within 2 weeks', ok: 'Under 4 weeks' };

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const uid = () => (crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2));

// Everything lives on the phone first; the server is only how phones share.
const store = {
  get(k, d) { try { const v = localStorage.getItem('rs.' + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { localStorage.setItem('rs.' + k, JSON.stringify(v)); },
};
let db = store.get('db', { walls: {}, routes: {} });
let me = store.get('me', '');
let code = store.get('code', '');
let cursor = store.get('cursor', 0);
let epoch = store.get('epoch', null);

let filterWall = null;
let sheet = null; // {type:'name'} | {type:'settings'} | {type:'route', draft, isNew, err}
let sync = { busy: false, again: false, failed: false, needCode: false };

// ---------- dates ----------
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const daysAgo = n => { const d = new Date(); d.setDate(d.getDate() - n); return iso(d); };
const ageDays = s => {
  const [y, m, d] = s.split('-').map(Number);
  const t = new Date(); t.setHours(0, 0, 0, 0);
  return Math.max(0, Math.round((t - new Date(y, m - 1, d)) / 864e5));
};
const span = n => (n < 7 ? `${n}d` : `${Math.floor(n / 7)}w${n % 7 ? ` ${n % 7}d` : ''}`);

// ---------- data ----------
function put(kind, rec) {
  rec.updatedAt = Date.now();
  rec.dirty = true;
  db[kind][rec.id] = rec;
  store.set('db', db);
  render();
  queueSync();
}
const walls = () => Object.values(db.walls).filter(w => !w.deleted).sort((a, b) => a.name.localeCompare(b.name));
const activeRoutes = () => Object.values(db.routes)
  .filter(r => !r.strippedAt && db.walls[r.wall] && !db.walls[r.wall].deleted)
  .map(r => ({ ...r, age: ageDays(r.setAt) }))
  .sort((a, b) => b.age - a.age || a.updatedAt - b.updatedAt);
const status = age => (age > MAX_DAYS ? 'over' : age >= WARN_DAYS ? 'warn' : 'ok');
const dirtyCount = () => ['walls', 'routes'].reduce((n, k) => n + Object.values(db[k]).filter(r => r.dirty).length, 0);
function knownGrades() {
  const count = {};
  for (const r of Object.values(db.routes)) count[r.grade] = (count[r.grade] || 0) + 1;
  return Object.keys(count).sort((a, b) => count[b] - count[a]).slice(0, 14)
    .sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
}
function knownSetters() {
  const s = new Set(Object.values(db.routes).map(r => r.setter).filter(Boolean));
  if (me) s.add(me);
  return [...s].sort();
}

// ---------- main screen ----------
function render() {
  const all = activeRoutes();
  const ws = walls();
  if (filterWall && !ws.some(w => w.id === filterWall)) filterWall = null;
  const shown = filterWall ? all.filter(r => r.wall === filterWall) : all;
  const count = st => shown.filter(r => status(r.age) === st).length;
  const over = count('over');
  const warn = count('warn');
  const plural = (n, word) => `${n} ${word}${n === 1 ? '' : 's'}`;
  let html = '';

  if (!ws.length) {
    html = `<div class="empty"><p>No walls yet. Add the names of your walls to get started.</p>
      <button class="btn primary" data-act="settings">Add walls</button></div>`;
  } else {
    const where = filterWall ? ` on ${esc(db.walls[filterWall].name)}` : '';
    html += `<section class="headline">${over
      ? `<p class="big"><b>${over}</b> route${over === 1 ? '' : 's'} past 6 weeks</p>`
      : `<p class="big clear">Nothing past 6 weeks</p>`}
      <p class="rest">${warn ? `${warn} due within 2 weeks · ` : ''}${plural(shown.length, 'route')} up${where}</p></section>`;
    html += `<div class="chips filters"><button class="chip ${filterWall ? '' : 'on'}" data-act="filter" data-id="">All walls</button>`;
    for (const w of ws) {
      const n = all.filter(r => r.wall === w.id && status(r.age) === 'over').length;
      html += `<button class="chip ${filterWall === w.id ? 'on' : ''}" data-act="filter" data-id="${esc(w.id)}">${esc(w.name)}${n ? `<em>${n}</em>` : ''}</button>`;
    }
    html += '</div>';
    if (!shown.length) {
      html += `<div class="empty"><p>Nothing logged${where || ' yet'}. Tap “Log a route” when you set one.</p></div>`;
    }
    for (const st of ['over', 'warn', 'ok']) {
      const rows = shown.filter(r => status(r.age) === st);
      if (!rows.length) continue;
      html += `<h2 class="group ${st}">${GROUPS[st]}<span>${rows.length}</span></h2><ul class="routes">`;
      for (const r of rows) {
        const left = MAX_DAYS - r.age;
        const note = st === 'over' ? `${span(-left)} over` : st === 'warn' ? (left ? `${span(left)} left` : 'due today') : '';
        const [fill, ink] = COLOURS[r.colour] || ['#999', '#fff'];
        const sub = [r.colour, r.note, r.setter].filter(Boolean).join(' · ');
        html += `<li class="row ${st}">
          <button class="info" data-act="edit" data-id="${esc(r.id)}">
            <span class="tile ${r.grade.length > 4 ? 'long' : ''}" style="background:${fill};color:${ink}">${esc(r.grade)}</span>
            <span class="txt"><strong>${esc(db.walls[r.wall].name)}</strong><small>${esc(sub)}</small></span>
            <span class="age"><b>${r.age ? span(r.age) : 'today'}</b>${note ? `<small>${note}</small>` : ''}</span>
          </button>
          <button class="strip" data-act="strip" data-id="${esc(r.id)}" aria-label="Strip ${esc(r.grade)} ${esc(r.colour)}">Strip</button></li>`;
      }
      html += '</ul>';
    }
  }
  $('#main').innerHTML = html;
  $('#add').hidden = !ws.length;
  renderSync();
}

function renderSync() {
  const n = dirtyCount();
  const el = $('#sync');
  el.className = n || sync.needCode ? 'pending' : '';
  el.textContent = sync.needCode ? 'Enter crew code'
    : sync.busy ? 'Syncing…'
    : n ? `${n} waiting for signal`
    : sync.failed ? 'Offline' : 'Synced';
}

// ---------- sheets ----------
function openSheet(s) { const fresh = !sheet; sheet = s; renderSheet(); if (fresh) $('#sheet .panel').classList.add('rise'); }
function closeSheet() { sheet = null; renderSheet(); }

function renderSheet() {
  const el = $('#sheet');
  if (!sheet) { el.hidden = true; el.innerHTML = ''; return; }
  el.hidden = false;
  let h = '';
  if (sheet.type === 'name') {
    h = `<h2>Who's setting?</h2><p>Your name goes on the routes you log from this phone.</p>
      <input type="text" id="f-me" placeholder="Your name" autocomplete="off" value="${esc(me)}">
      ${sheet.err ? `<div class="err">${esc(sheet.err)}</div>` : ''}
      <div class="actions"><button class="btn primary" data-act="save-name">Continue</button></div>`;
  } else if (sheet.type === 'settings') {
    const n = dirtyCount();
    h = `<h2>Setup <button class="x" data-act="close" aria-label="Close">×</button></h2>
      <h3>Your name</h3><input type="text" id="f-me" autocomplete="off" value="${esc(me)}">
      <h3>Walls</h3>`;
    for (const w of walls()) {
      h += `<div class="wallrow"><input type="text" data-wall="${esc(w.id)}" autocomplete="off" value="${esc(w.name)}">
        <button data-act="del-wall" data-id="${esc(w.id)}">Remove</button></div>`;
    }
    h += `<div class="wallrow"><input type="text" id="f-wall" placeholder="New wall name" autocomplete="off">
        <button data-act="add-wall">Add</button></div>
      ${sheet.err ? `<div class="err">${esc(sheet.err)}</div>` : ''}
      <h3>Sync</h3>
      <p>${sync.needCode ? 'This gym needs a crew code before this phone can sync.'
        : n ? `${n} change${n > 1 ? 's' : ''} saved on this phone, waiting for signal.`
        : sync.failed ? 'No connection right now. Changes are saved on this phone.' : 'Everything is synced.'}</p>
      ${sync.needCode || code ? `<input type="password" id="f-code" placeholder="Crew code" autocomplete="off" value="${esc(code)}">` : ''}
      <div class="actions"><button class="btn" data-act="sync-now">Sync now</button>
        <button class="btn primary" data-act="close">Done</button></div>`;
  } else if (sheet.type === 'route') {
    const d = sheet.draft;
    const chip = (act, val, label, on) => `<button class="chip ${on ? 'on' : ''}" data-act="${act}" data-val="${esc(val)}">${esc(label)}</button>`;
    h = `<h2>${sheet.isNew ? 'Log a route' : 'Edit route'} <button class="x" data-act="close" aria-label="Close">×</button></h2>
      <h3>Wall</h3><div class="chips">${walls().map(w => chip('d-wall', w.id, w.name, d.wall === w.id)).join('')}</div>
      <h3>Grade</h3><div class="chips">${knownGrades().map(g => chip('d-grade', g, g, d.grade === g)).join('')}</div>
      <input type="text" id="f-grade" placeholder="Grade, e.g. V4 or 6b" autocomplete="off" autocapitalize="off" value="${esc(d.grade)}">
      <h3>Hold colour</h3><div class="chips">${Object.keys(COLOURS).map(c =>
        `<button class="swatch ${d.colour === c ? 'on' : ''}" data-act="d-colour" data-val="${c}" aria-label="${c}" aria-pressed="${d.colour === c}" style="background:${COLOURS[c][0]}"></button>`).join('')}</div>
      <h3>Set</h3><div class="chips">${[0, 1, 2, 3, 4, 5, 6, 8].map(w =>
        chip('d-when', daysAgo(w * 7), w ? `~${w}w ago` : 'Today', d.setAt === daysAgo(w * 7))).join('')}</div>
      <input type="date" id="f-date" max="${daysAgo(0)}" value="${esc(d.setAt)}">
      <h3>Setter</h3><div class="chips">${knownSetters().map(s => chip('d-setter', s, s, d.setter === s)).join('')}</div>
      <h3>Note (optional)</h3>
      <input type="text" id="f-note" placeholder="e.g. left arête, lane 3" autocomplete="off" value="${esc(d.note)}">
      ${sheet.err ? `<div class="err">${esc(sheet.err)}</div>` : ''}
      <div class="actions">${sheet.isNew
        ? `<button class="btn" data-act="save-more">Save + another</button><button class="btn primary" data-act="save-route">Save</button>`
        : `<button class="btn danger" data-act="strip-edit">Strip</button><button class="btn primary" data-act="save-route">Save</button>`}</div>`;
  }
  const top = el.firstElementChild ? el.firstElementChild.scrollTop : 0;
  el.innerHTML = `<div class="panel">${h}</div>`;
  el.firstElementChild.scrollTop = top;
}

function saveRoute(keepOpen) {
  const d = sheet.draft;
  d.grade = d.grade.trim();
  d.note = d.note.trim();
  const missing = [!d.wall && 'a wall', !d.grade && 'a grade', !d.colour && 'a hold colour'].filter(Boolean);
  if (missing.length) { sheet.err = `Pick ${missing.join(' and ')} first.`; return renderSheet(); }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d.setAt) || d.setAt > daysAgo(0)) { sheet.err = 'Pick a set date that is today or earlier.'; return renderSheet(); }
  put('routes', { ...d });
  if (keepOpen) {
    // Walking a wall: keep wall, date and setter; clear what changes per route.
    openSheet({ type: 'route', isNew: true, draft: { ...d, id: uid(), grade: '', colour: '', note: '' } });
    toast(`Saved ${d.grade} ${d.colour}`);
  } else closeSheet();
}

function strip(id) {
  const r = db.routes[id];
  if (!r) return;
  put('routes', { ...r, strippedAt: Date.now(), strippedBy: me });
  toast(`Stripped ${r.grade} ${r.colour}`, () => put('routes', { ...db.routes[id], strippedAt: null, strippedBy: null }));
}

let toastTimer;
function toast(msg, undo) {
  const el = $('#toast');
  el.innerHTML = `<span>${esc(msg)}</span>${undo ? '<button>Undo</button>' : ''}`;
  el.hidden = false;
  if (undo) el.querySelector('button').onclick = () => { el.hidden = true; undo(); };
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, undo ? 6000 : 2000);
}

// ---------- events ----------
document.addEventListener('click', e => {
  if (e.target.id === 'sheet' && sheet && sheet.type !== 'name') return closeSheet();
  const b = e.target.closest('[data-act]');
  if (!b) return;
  const { act, id, val } = b.dataset;
  const d = sheet && sheet.draft;
  if (d) sheet.err = '';
  switch (act) {
    case 'settings': return openSheet({ type: 'settings' });
    case 'close': return closeSheet();
    case 'filter': filterWall = id || null; return render();
    case 'add':
      return openSheet({ type: 'route', isNew: true, draft: {
        id: uid(), wall: filterWall || (walls().length === 1 ? walls()[0].id : ''), grade: '', colour: '',
        setAt: daysAgo(0), setter: me, note: '', strippedAt: null } });
    case 'edit': return openSheet({ type: 'route', isNew: false, draft: { note: '', ...db.routes[id] } });
    case 'strip': return strip(id);
    case 'strip-edit': { const rid = d.id; closeSheet(); return strip(rid); }
    case 'd-wall': d.wall = val; return renderSheet();
    case 'd-grade': d.grade = val; return renderSheet();
    case 'd-colour': d.colour = val; return renderSheet();
    case 'd-when': d.setAt = val; return renderSheet();
    case 'd-setter': d.setter = val; return renderSheet();
    case 'save-route': return saveRoute(false);
    case 'save-more': return saveRoute(true);
    case 'save-name': {
      const name = $('#f-me').value.trim();
      if (!name) { sheet.err = 'Enter your name.'; return renderSheet(); }
      me = name; store.set('me', me);
      closeSheet();
      return render();
    }
    case 'add-wall': {
      const name = $('#f-wall').value.trim();
      if (!name) return;
      if (walls().some(w => w.name.toLowerCase() === name.toLowerCase())) { sheet.err = `There is already a wall called ${name}.`; return renderSheet(); }
      sheet.err = '';
      put('walls', { id: uid(), name, deleted: false });
      renderSheet();
      return $('#f-wall').focus();
    }
    case 'del-wall': {
      const n = activeRoutes().filter(r => r.wall === id).length;
      if (n) { sheet.err = `${db.walls[id].name} still has ${n} route${n > 1 ? 's' : ''} up. Strip ${n > 1 ? 'them' : 'it'} first.`; return renderSheet(); }
      sheet.err = '';
      put('walls', { ...db.walls[id], deleted: true });
      return renderSheet();
    }
    case 'sync-now': return doSync().then(() => { if (sheet && sheet.type === 'settings') renderSheet(); });
  }
});

document.addEventListener('input', e => {
  const d = sheet && sheet.draft;
  const t = e.target;
  if (d && t.id === 'f-grade') d.grade = t.value;
  if (d && t.id === 'f-note') d.note = t.value;
  if (d && t.id === 'f-date' && t.value) d.setAt = t.value;
});

document.addEventListener('change', e => {
  const t = e.target;
  if (t.id === 'f-date' && sheet && sheet.draft) return renderSheet();
  if (t.id === 'f-me' && sheet && sheet.type === 'settings' && t.value.trim()) { me = t.value.trim(); store.set('me', me); }
  if (t.id === 'f-code') { code = t.value.trim(); store.set('code', code); sync.needCode = false; queueSync(); }
  if (t.dataset.wall) {
    const w = db.walls[t.dataset.wall];
    const name = t.value.trim();
    if (name && name !== w.name) put('walls', { ...w, name });
    else t.value = w.name;
  }
});

// ---------- sync ----------
let syncTimer;
function queueSync() { clearTimeout(syncTimer); syncTimer = setTimeout(doSync, 400); }

async function doSync() {
  if (sync.busy) { sync.again = true; return; }
  sync.busy = true;
  renderSync();
  const sent = [];
  for (const kind of ['walls', 'routes']) {
    for (const r of Object.values(db[kind])) {
      if (r.dirty) { const { dirty, ...rec } = r; sent.push({ kind, rec }); }
    }
  }
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), 12000);
  try {
    const res = await fetch('api/sync', {
      method: 'POST', signal: ctl.signal,
      headers: { 'content-type': 'application/json', 'x-crew-code': code },
      body: JSON.stringify({ epoch, cursor, changes: sent }),
    });
    if (res.status === 401) { sync.needCode = true; return; }
    if (!res.ok) throw new Error('sync ' + res.status);
    const out = await res.json();
    // The server has these now, unless they were edited again while we waited.
    for (const { kind, rec } of sent) {
      const local = db[kind][rec.id];
      if (local && local.updatedAt === rec.updatedAt) delete local.dirty;
    }
    for (const { kind, rec } of out.records) {
      const local = db[kind][rec.id];
      if (!local || !local.dirty || rec.updatedAt > local.updatedAt) db[kind][rec.id] = rec;
    }
    // A different epoch means the server's data was replaced: give it everything we hold.
    if (epoch && out.epoch !== epoch) {
      for (const kind of ['walls', 'routes']) for (const r of Object.values(db[kind])) r.dirty = true;
      sync.again = true;
    }
    epoch = out.epoch; cursor = out.cursor;
    store.set('db', db); store.set('epoch', epoch); store.set('cursor', cursor);
    sync.failed = false; sync.needCode = false;
    if (out.records.length) { render(); if (sheet && sheet.type !== 'name') renderSheet(); }
  } catch {
    sync.failed = true; // no signal: changes stay on the phone and go up next time
  } finally {
    clearTimeout(timer);
    sync.busy = false;
    renderSync();
    if (sync.again) { sync.again = false; queueSync(); }
  }
}

window.addEventListener('online', doSync);
document.addEventListener('visibilitychange', () => { if (!document.hidden) { render(); doSync(); } });
setInterval(() => { if (!document.hidden) doSync(); }, 30000);

try {
  if ('serviceWorker' in navigator) navigator.serviceWorker.register('sw.js').catch(() => {});
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
} catch { /* offline install is unavailable in this browser; the app still runs */ }

render();
if (!me) openSheet({ type: 'name' });
doSync();
})();
