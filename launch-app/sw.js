const CACHE_PREFIX = "quran-launch-";
const CACHE_NAME = `${CACHE_PREFIX}v3`;
const PRECACHE_URLS = Object.freeze([
  "./",
  "./index.html",
  "./style.css",
  "./app.js",
  "./sw.js",
  "./manifest.json",
  "./README.md",
  "./assets/page-1.png",
  "./assets/page-2.png",
  "./assets/icon-180.png",
  "./assets/icon-192.png",
  "./assets/icon-512.png",
]);
const PRECACHE_REQUESTS = Object.freeze(
  PRECACHE_URLS.map((url) => new Request(url, { cache: "reload" })),
);

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then((cache) => cache.addAll(PRECACHE_REQUESTS))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key.startsWith(CACHE_PREFIX) && key !== CACHE_NAME)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") {
    return;
  }
  if (new URL(request.url).origin !== self.location.origin) {
    return;
  }

  event.respondWith(
    caches.match(request, { ignoreSearch: true }).then((cached) => {
      if (cached) {
        return cached;
      }
      if (request.mode === "navigate") {
        return caches.match("./index.html");
      }
      return fetch(request);
    }),
  );
});
