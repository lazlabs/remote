/**
 * Movie Room Remote — Service Worker
 * Caches the app shell for offline use and fast loads.
 * Version: bump CACHE_NAME to force update after deployments.
 */
const CACHE_NAME = 'movie-room-v3';

// Files to cache immediately on install
const PRECACHE = [
  './',
  './theater-remote.html',
  './manifest.json',
  './icon.svg',
  './sw.js',
];

// Origins we never cache (live API calls must always go to network)
const NETWORK_ONLY_ORIGINS = [
  'homeassistant',
  'nabu.casa',
  'googleapis.com',        // Google Fonts
  'fonts.gstatic.com',
  'api.anthropic.com',
];

// ── INSTALL: pre-cache app shell ──────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting())  // activate immediately
  );
});

// ── ACTIVATE: clean up old caches ────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    ).then(() => self.clients.claim())  // take control of all pages now
  );
});

// ── FETCH: cache-first for app shell, network-only for APIs ──────────
self.addEventListener('fetch', event => {
  const url = event.request.url;

  // Always go to network for API calls
  if(NETWORK_ONLY_ORIGINS.some(o => url.includes(o))) return;

  // Network-only for non-GET requests
  if(event.request.method !== 'GET') return;

  // For everything else: cache first, fall back to network
  event.respondWith(
    caches.match(event.request).then(cached => {
      if(cached) return cached;
      return fetch(event.request).then(response => {
        // Cache successful responses for app assets
        if(response && response.status === 200 && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => {
        // Offline fallback: return the cached app shell
        if(event.request.destination === 'document') {
          return caches.match('./theater-remote.html');
        }
      });
    })
  );
});
