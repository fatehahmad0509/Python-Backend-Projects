/**
 * MessageLMS — Service Worker
 * HTML always fetched fresh (never cached) so updates apply immediately.
 * Icons/manifest cached for offline support.
 */

const CACHE_NAME = 'messagelms-v3';

// Cache only truly static assets — NOT the HTML page itself
const STATIC_ASSETS = [
  '/manifest.json',
  '/icon-192.ico',
  '/icon-512.ico',
];

// ── Install: cache static assets ──────────────────────────────────────────
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS))
  );
  self.skipWaiting();
});

// ── Activate: clean old caches ────────────────────────────────────────────
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys
          .filter(key => key !== CACHE_NAME)
          .map(key => caches.delete(key))
      )
    )
  );
  self.clients.claim();
});

// ── Fetch ──────────────────────────────────────────────────────────────────
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  // Skip WebSocket — service workers can't intercept ws://
  if (url.protocol === 'ws:' || url.protocol === 'wss:') return;

  // HTML navigation requests — ALWAYS fetch fresh from network
  // This ensures users always get the latest version of the app.
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('/manifest.json'))
    );
    return;
  }

  // API calls — network only, no cache
  if (
    url.pathname.startsWith('/rooms') ||
    url.pathname.startsWith('/messages') ||
    url.pathname.startsWith('/config') ||
    url.pathname.startsWith('/subscribe') ||
    url.pathname.startsWith('/ws')
  ) {
    event.respondWith(
      fetch(event.request).catch(() =>
        new Response(
          JSON.stringify({ error: 'offline' }),
          { headers: { 'Content-Type': 'application/json' } }
        )
      )
    );
    return;
  }

  // Static assets (icons, manifest) — cache first, then network
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (event.request.method === 'GET' && response.status === 200) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      });
    })
  );
});

// ── Push Notifications ────────────────────────────────────────────────────

self.addEventListener('push', event => {
  let data = {
    title:     'MessageLMS',
    body:      'Yeni bir mesaj var!',
    room_id:   null,
    room_name: '',
  };

  try { data = { ...data, ...event.data.json() }; } catch (_) {}

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      // Skip if the app window is already focused
      if (clientList.some(c => c.focused)) return Promise.resolve();

      return self.registration.showNotification(data.title, {
        body:     data.body,
        icon:     '/icon-192.jpg',
        badge:    '/icon-192.jpg',
        vibrate:  [200, 100, 200],
        tag:      `msg-room-${data.room_id}`,
        renotify: true,
        data:     { room_id: data.room_id, room_name: data.room_name },
      });
    })
  );
});

// ── Notification Click ────────────────────────────────────────────────────

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const { room_id, room_name } = event.notification.data || {};

  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(clientList => {
      for (const client of clientList) {
        if (client.url.startsWith(self.location.origin)) {
          client.focus();
          if (room_id) client.postMessage({ type: 'OPEN_ROOM', room_id, room_name });
          return;
        }
      }
      return clients.openWindow(room_id ? `/?room=${room_id}` : '/');
    })
  );
});
