/**
 * Aetheris UI - Service Worker
 * 
 * Implements Cache-First strategy for Pyodide/WASM runtime and core Python files.
 * This ensures fast subsequent loads by caching the ~15MB Pyodide runtime.
 */

const CACHE_NAME = 'aetheris-v1';
const CORE_CACHE = 'aetheris-core-v1';

// Assets to cache on install (Pyodide runtime + our code)
const PRECACHE_URLS = [
  '/',
  '/static/manifest.json',
  '/wasm/aether_bridge.js',
  'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/pyodide.js',
];

// Core Python files to cache
const CORE_PY_FILES = [
  '/core/__init__.py',
  '/core/aether_math.py',
  '/core/solver.py',
  '/core/solver_wasm.py',
  '/core/solver_bridge.py',
  '/core/state_manager.py',
  '/core/tensor_compiler.py',
  '/core/elements.py',
  '/core/engine.py',
  '/core/renderer_base.py',
  '/core/ui_builder.py',
];

/**
 * Install event: Pre-cache critical assets.
 */
self.addEventListener('install', (event) => {
  console.log('[SW] Installing Aetheris Service Worker...');
  
  event.waitUntil(
    Promise.all([
      // Cache main assets
      caches.open(CACHE_NAME).then((cache) => {
        console.log('[SW] Caching main assets...');
        return cache.addAll(PRECACHE_URLS);
      }),
      // Cache core Python files
      caches.open(CORE_CACHE).then((cache) => {
        console.log('[SW] Caching core Python files...');
        return cache.addAll(CORE_PY_FILES);
      }),
    ]).then(() => {
      console.log('[SW] Installation complete, skipping waiting...');
      return self.skipWaiting();
    })
  );
});

/**
 * Activate event: Clean up old caches.
 */
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== CORE_CACHE)
          .map((name) => {
            console.log(`[SW] Deleting old cache: ${name}`);
            return caches.delete(name);
          })
      );
    }).then(() => {
      console.log('[SW] Activation complete, claiming clients...');
      return self.clients.claim();
    })
  );
});

/**
 * Fetch event: Cache-First strategy.
 * 
 * For core Python files and static assets, serve from cache first.
 * For everything else, try cache then network (stale-while-revalidate).
 */
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  
  // Core Python files - Cache First
  if (url.pathname.startsWith('/core/') && url.pathname.endsWith('.py')) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        // Not in cache, fetch and cache for next time
        return fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CORE_CACHE).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return networkResponse;
        });
      })
    );
    return;
  }
  
  // Static assets and Pyodide - Cache First
  if (
    url.pathname.startsWith('/static/') ||
    url.pathname.startsWith('/wasm/') ||
    url.hostname === 'cdn.jsdelivr.net'
  ) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          return cachedResponse;
        }
        return fetch(event.request).then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const responseClone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return networkResponse;
        }).catch(() => {
          // Offline fallback
          return new Response('Offline - Aetheris UI requires network for first load', {
            status: 503,
            statusText: 'Service Unavailable',
          });
        });
      })
    );
    return;
  }
  
  // Main page - Network First (always get latest HTML)
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).then((networkResponse) => {
        // Cache the HTML page too
        const responseClone = networkResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseClone);
        });
        return networkResponse;
      }).catch(() => {
        // Offline: serve cached page
        return caches.match(event.request);
      })
    );
    return;
  }
  
  // Default: Network First with cache fallback
  event.respondWith(
    fetch(event.request).then((networkResponse) => {
      const responseClone = networkResponse.clone();
      caches.open(CACHE_NAME).then((cache) => {
        cache.put(event.request, responseClone);
      });
      return networkResponse;
    }).catch(() => {
      return caches.match(event.request);
    })
  );
});

/**
 * Message handler: Allow the app to trigger cache updates.
 */
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data && event.data.type === 'CACHE_CORE_FILES') {
    // Dynamically cache additional core files if needed
    caches.open(CORE_CACHE).then((cache) => {
      return cache.addAll(event.data.urls || []);
    });
  }
});
