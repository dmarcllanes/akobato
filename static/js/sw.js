/* ================================================================
   Akobato — Service Worker (PWA)
   Cache-first for static assets, network-first for HTML routes
   ================================================================ */

const CACHE   = 'akobato-v1';
const STATIC  = [
  '/static/manifest.json',
  '/static/img/logo.svg',
  '/static/img/icon.svg',
  '/static/css/custom.css',
  '/static/css/landing.css',
  '/static/js/landing.js',
];

self.addEventListener('install', e => {
  self.skipWaiting();
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC).catch(() => {}))
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Only handle same-origin
  if (url.origin !== self.location.origin) return;

  // Network-first for HTML / navigation
  if (e.request.mode === 'navigate' || e.request.headers.get('accept')?.includes('text/html')) {
    e.respondWith(
      fetch(e.request)
        .catch(() => caches.match(e.request))
    );
    return;
  }

  // Cache-first for static assets
  if (url.pathname.startsWith('/static/')) {
    e.respondWith(
      caches.match(e.request).then(cached => {
        if (cached) return cached;
        return fetch(e.request).then(res => {
          const clone = res.clone();
          caches.open(CACHE).then(c => c.put(e.request, clone));
          return res;
        });
      })
    );
  }
});
