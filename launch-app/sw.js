const CACHE_PREFIX = 'quran-kiosk-';
const CACHE_NAME = `${CACHE_PREFIX}v2`;
const LEGACY_CACHE_PREFIXES = Object.freeze([
  'quran-launch-',
  'quran-microsite-',
]);
const APP_SHELL = Object.freeze([
  './',
  './index.html',
  './sw.js',
]);

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(
        APP_SHELL.map((url) => new Request(url, { cache: 'reload' })),
      ))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(
        keys
          .filter((key) => (
            key.startsWith(CACHE_PREFIX)
            || LEGACY_CACHE_PREFIXES.some((prefix) => key.startsWith(prefix))
          ) && key !== CACHE_NAME)
          .map((key) => caches.delete(key)),
      ))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener('fetch', (event) => {
  const { request } = event;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  event.respondWith(
    caches.open(CACHE_NAME).then((cache) => (
      cache.match(request, { ignoreSearch: true }).then((cached) => {
        if (cached) return cached;
        if (request.mode === 'navigate') return cache.match('./index.html');
        return fetch(request);
      })
    )),
  );
});
