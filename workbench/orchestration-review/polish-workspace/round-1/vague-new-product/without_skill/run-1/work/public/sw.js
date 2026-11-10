// Keeps the app itself on the phone so it opens with no signal.
// Bump CACHE when you want phones to drop old cached files entirely.
const CACHE = 'route-age-v2';
const SHELL = ['./', 'style.css', 'app.js', 'manifest.webmanifest', 'icon-180.png', 'icon-192.png', 'icon-512.png',
  'fonts/barlow-condensed-600.woff2', 'fonts/barlow-condensed-700.woff2'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Serve from the phone straight away, and refresh the copy in the background when there is signal.
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET' || url.origin !== location.origin || url.pathname.includes('/api/')) return;
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const hit = await cache.match(e.request, { ignoreSearch: true });
    const fresh = fetch(e.request)
      .then(res => { if (res.ok) cache.put(e.request, res.clone()); return res; })
      .catch(async () => hit || (e.request.mode === 'navigate' && (await cache.match('./'))) || Response.error());
    if (hit) { e.waitUntil(fresh); return hit; }
    return fresh;
  })());
});
