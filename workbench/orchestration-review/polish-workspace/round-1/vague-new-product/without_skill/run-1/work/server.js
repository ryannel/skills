// Route Age — static file server + sync endpoint. No dependencies.
//   node server.js
// Env: PORT (default 8080), DATA_FILE (default ./data/routes.json),
//      CREW_CODE (optional shared code the setters enter once on their phone)
'use strict';
const http = require('http');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const PORT = Number(process.env.PORT) || 8080;
const DATA_FILE = process.env.DATA_FILE || path.join(__dirname, 'data', 'routes.json');
const CREW_CODE = process.env.CREW_CODE || '';
const PUBLIC = path.join(__dirname, 'public');
const KINDS = ['walls', 'routes'];
const TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.webmanifest': 'application/manifest+json',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.woff2': 'font/woff2',
};

// data = { epoch, seq, records: { "<kind>/<id>": { kind, seq, rec } } }
// A missing file starts a fresh gym. A file that exists but can't be parsed stops
// the server rather than being overwritten.
let data;
try {
  data = JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
} catch (e) {
  if (e.code !== 'ENOENT') throw e;
  data = { epoch: crypto.randomUUID(), seq: 0, records: {} };
}

function persist() {
  fs.mkdirSync(path.dirname(DATA_FILE), { recursive: true });
  const tmp = DATA_FILE + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(data));
  fs.renameSync(tmp, DATA_FILE);
}

// Merge the phone's changes (newest edit of each record wins), then hand back
// everything the phone hasn't seen yet.
function sync(body) {
  const changes = Array.isArray(body.changes) ? body.changes : [];
  let changed = false;
  for (const c of changes) {
    const rec = c && c.rec;
    if (!c || !KINDS.includes(c.kind) || !rec || typeof rec.id !== 'string' || !rec.id || rec.id.length > 64) continue;
    if (!Number.isFinite(rec.updatedAt) || JSON.stringify(rec).length > 2000) continue;
    rec.updatedAt = Math.min(rec.updatedAt, Date.now() + 60000); // a fast phone clock can't win forever
    const key = c.kind + '/' + rec.id;
    const have = data.records[key];
    if (have && have.rec.updatedAt >= rec.updatedAt) continue;
    data.records[key] = { kind: c.kind, seq: ++data.seq, rec };
    changed = true;
  }
  if (changed) persist();
  const since = body.epoch === data.epoch && Number.isFinite(body.cursor) ? body.cursor : 0;
  const records = Object.values(data.records)
    .filter(r => r.seq > since)
    .map(r => ({ kind: r.kind, rec: r.rec }));
  return { epoch: data.epoch, cursor: data.seq, records };
}

function send(res, status, body, headers = {}) {
  res.writeHead(status, headers);
  res.end(body);
}

function serveStatic(req, res) {
  let rel = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (rel.endsWith('/')) rel += 'index.html';
  const file = path.join(PUBLIC, rel);
  if (!file.startsWith(PUBLIC + path.sep)) return send(res, 403, 'Forbidden');
  fs.readFile(file, (err, buf) => {
    if (err) return send(res, 404, 'Not found');
    send(res, 200, buf, {
      'content-type': TYPES[path.extname(file)] || 'application/octet-stream',
      'cache-control': 'no-cache',
    });
  });
}

http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  if (url.pathname !== '/api/sync') {
    if (req.method !== 'GET' && req.method !== 'HEAD') return send(res, 405, 'Method not allowed');
    return serveStatic(req, res);
  }
  if (req.method !== 'POST') return send(res, 405, 'Method not allowed');
  if (CREW_CODE && req.headers['x-crew-code'] !== CREW_CODE) return send(res, 401, 'Crew code required');
  let raw = '';
  req.on('data', chunk => {
    raw += chunk;
    if (raw.length > 2e6) req.destroy();
  });
  req.on('end', () => {
    let body;
    try {
      body = JSON.parse(raw);
    } catch {
      return send(res, 400, 'Bad JSON');
    }
    try {
      send(res, 200, JSON.stringify(sync(body || {})), { 'content-type': 'application/json' });
    } catch (e) {
      console.error(e);
      send(res, 500, 'Could not save');
    }
  });
}).listen(PORT, () => console.log(`Route Age running on http://localhost:${PORT}`));
