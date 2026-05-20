// Dashboard service worker — minimal app-shell cache.
//
// Privacy: this SW caches ONLY the static dashboard shell (HTML/CSS/JS shipped
// from eidetic.works). It NEVER caches:
//   - Bridge URL responses (the user's local daemon endpoint they configured)
//   - Bearer tokens (stored only in the page's localStorage)
//   - Engram payloads (those come from the user's daemon and stay there)
//
// The cache exists so the dashboard works offline once the user has opened it
// once — they can come back to the splash + see "daemon unreachable" instead of
// a blank "no internet" Chrome page.

const CACHE_NAME = "eidetic-dashboard-v1";
const SHELL_URLS = [
  "/dashboard/",
  "/dashboard/index.html",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS))
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys
          .filter((k) => k !== CACHE_NAME && k.startsWith("eidetic-dashboard-"))
          .map((k) => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);

  // NEVER cache cross-origin (the daemon bridge URL the user pasted). Let those
  // requests pass through to fetch + fail naturally when daemon is offline.
  if (url.origin !== self.location.origin) {
    return;
  }

  // Cache-first for the dashboard shell; network-first for everything else.
  if (url.pathname.startsWith("/dashboard/")) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) {
          // Revalidate in background.
          fetch(event.request)
            .then((fresh) => {
              if (fresh.ok) {
                caches
                  .open(CACHE_NAME)
                  .then((cache) => cache.put(event.request, fresh.clone()));
              }
            })
            .catch(() => {});
          return cached;
        }
        return fetch(event.request).then((fresh) => {
          if (fresh.ok) {
            const copy = fresh.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, copy));
          }
          return fresh;
        });
      })
    );
  }
});
