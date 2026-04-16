// Aetheris GESTNE - Empty Service Worker
// This file exists only to suppress 404 errors from previous cached sessions on port 8080.
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.clients.claim());
