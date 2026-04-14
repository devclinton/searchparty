const CACHE_NAME = "searchparty-v2";
const API_CACHE_NAME = "searchparty-api-v1";
const OFFLINE_URL = "/offline";

const PRECACHE_URLS = ["/", "/offline", "/manifest.json"];

// API paths that should be cached for offline use
const CACHEABLE_API_PATTERNS = [
  /\/api\/v1\/incidents$/,
  /\/api\/v1\/incidents\/[^/]+$/,
  /\/api\/v1\/incidents\/[^/]+\/teams$/,
  /\/api\/v1\/incidents\/[^/]+\/hazards$/,
  /\/api\/v1\/incidents\/[^/]+\/segments$/,
  /\/api\/v1\/incidents\/[^/]+\/clues$/,
  /\/api\/v1\/lpb\/categories$/,
  /\/api\/v1\/lpb\/profiles\//,
  /\/api\/v1\/lpb\/incidents\/[^/]+\/rings$/,
  /\/api\/v1\/lpb\/incidents\/[^/]+\/behaviors$/,
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(PRECACHE_URLS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys
          .filter((key) => key !== CACHE_NAME && key !== API_CACHE_NAME)
          .map((key) => caches.delete(key)),
      );
    }),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // Navigation requests: network-first with offline fallback
  if (event.request.mode === "navigate") {
    event.respondWith(
      fetch(event.request).catch(
        () => caches.match(OFFLINE_URL).then((r) => r || caches.match("/")),
      ),
    );
    return;
  }

  // API GET requests: network-first, cache response for offline
  if (url.pathname.startsWith("/api/") && event.request.method === "GET") {
    const isCacheable = CACHEABLE_API_PATTERNS.some((p) => p.test(url.pathname));
    if (isCacheable) {
      event.respondWith(
        fetch(event.request)
          .then((response) => {
            if (response.ok) {
              const clone = response.clone();
              caches.open(API_CACHE_NAME).then((cache) => cache.put(event.request, clone));
            }
            return response;
          })
          .catch(() => caches.match(event.request)),
      );
      return;
    }
  }

  // API mutation requests (POST/PATCH/DELETE): if offline, notify client to queue
  if (url.pathname.startsWith("/api/") && event.request.method !== "GET") {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(
          JSON.stringify({
            error: "offline",
            message: "Request queued for sync when online",
          }),
          {
            status: 503,
            headers: { "Content-Type": "application/json" },
          },
        );
      }),
    );
    return;
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(event.request).then((cached) => {
      if (cached) return cached;
      return fetch(event.request).then((response) => {
        if (response.ok && url.origin === self.location.origin) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      });
    }),
  );
});

// Listen for sync events from the client
self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
  if (event.data?.type === "CLEAR_API_CACHE") {
    caches.delete(API_CACHE_NAME);
  }
});
