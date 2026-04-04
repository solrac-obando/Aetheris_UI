/**
 * Aether-Web Hybrid Sync Client
 *
 * Connects to the Python WebSocket server, creates DOM elements
 * from metadata, applies physics-driven transforms, and sends
 * pointer events back to the server.
 *
 * Zero dependencies — vanilla JS, no frameworks.
 */
(function () {
    'use strict';

    // ── Configuration ──────────────────────────────────────────────
    const WS_URL = `ws://${window.location.hostname}:${window.location.port || 8765}`;
    const root = document.getElementById('root');
    const statusText = document.getElementById('status-text');
    const fpsEl = document.getElementById('fps');
    const elCountEl = document.getElementById('el-count');
    const loadingEl = document.getElementById('loading');

    // ── State ──────────────────────────────────────────────────────
    let ws = null;
    let reconnectTimer = null;
    let frameCount = 0;
    let lastFpsTime = performance.now();
    let currentFps = 0;
    const elementCache = {};  // id -> DOM element

    // ── WebSocket Connection ───────────────────────────────────────
    function connect() {
        if (ws && ws.readyState === WebSocket.OPEN) return;

        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
            statusText.textContent = 'Connected';
            statusText.className = 'ok';
            loadingEl.classList.add('hidden');
            console.log('[Aether-Web] Connected to', WS_URL);
        };

        ws.onclose = () => {
            statusText.textContent = 'Disconnected — reconnecting…';
            statusText.className = 'err';
            loadingEl.classList.remove('hidden');
            clearTimeout(reconnectTimer);
            reconnectTimer = setTimeout(connect, 2000);
        };

        ws.onerror = (err) => {
            console.error('[Aether-Web] WebSocket error:', err);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleMessage(data);
            } catch (e) {
                console.warn('[Aether-Web] Invalid message:', event.data);
            }
        };
    }

    // ── Message Handler ────────────────────────────────────────────
    function handleMessage(data) {
        if (data.type === 'initial_dom') {
            createElements(data.elements);
        } else if (data.type === 'update') {
            applyTransforms(data.elements);
            updateFps();
        } else if (data.type === 'remove') {
            removeElements(data.ids);
        }
    }

    // ── DOM Element Creation ───────────────────────────────────────
    function createElements(elements) {
        elements.forEach(el => {
            if (elementCache[el.id]) return;  // Already exists

            const domEl = document.createElement(el.tag || 'div');
            domEl.id = el.id;
            domEl.style.position = 'absolute';
            domEl.style.willChange = 'transform';
            domEl.style.transform = `translate(${el.x || 0}px, ${el.y || 0}px)`;
            domEl.style.width = (el.w || 50) + 'px';
            domEl.style.height = (el.h || 30) + 'px';

            // Apply classes
            if (el.classes && el.classes.length) {
                el.classes.forEach(c => domEl.classList.add(c));
            }

            // Apply inline styles
            if (el.styles) {
                Object.entries(el.styles).forEach(([key, val]) => {
                    if (key.startsWith('data-')) {
                        domEl.dataset[key.slice(5)] = val;
                    } else {
                        domEl.style[key] = val;
                    }
                });
            }

            // Set text content
            if (el.text && el.tag !== 'input') {
                domEl.textContent = el.text;
            }

            // Input-specific attributes
            if (el.tag === 'input') {
                domEl.type = el.input_type || 'text';
                domEl.placeholder = el.placeholder || '';
                domEl.value = el.value || '';
                domEl.addEventListener('input', (e) => {
                    sendInputValue(el.id, e.target.value);
                });
            }

            // Pointer events for physics interaction
            domEl.addEventListener('pointerdown', (e) => {
                e.preventDefault();
                domEl.setPointerCapture(e.pointerId);
                sendPointer('pointerdown', el.id, e.clientX, e.clientY);
            });
            domEl.addEventListener('pointermove', (e) => {
                if (e.buttons > 0) {
                    sendPointer('pointermove', el.id, e.clientX, e.clientY);
                }
            });
            domEl.addEventListener('pointerup', (e) => {
                sendPointer('pointerup', el.id, e.clientX, e.clientY);
            });

            root.appendChild(domEl);
            elementCache[el.id] = domEl;
        });

        elCountEl.textContent = Object.keys(elementCache).length;
    }

    // ── Transform Application (the physics → DOM bridge) ───────────
    function applyTransforms(elements) {
        if (!elements || elements.length === 0) return;

        for (let i = 0; i < elements.length; i++) {
            const el = elements[i];
            const domEl = elementCache[el.id];
            if (!domEl) continue;

            // Use GPU-accelerated transform
            domEl.style.transform = `translate3d(${el.x}px, ${el.y}px, 0)`;
            domEl.style.width = el.w + 'px';
            domEl.style.height = el.h + 'px';
        }

        elCountEl.textContent = elements.length;
    }

    // ── Element Removal ────────────────────────────────────────────
    function removeElements(ids) {
        ids.forEach(id => {
            const domEl = elementCache[id];
            if (domEl) {
                domEl.remove();
                delete elementCache[id];
            }
        });
        elCountEl.textContent = Object.keys(elementCache).length;
    }

    // ── Pointer Event Sending ──────────────────────────────────────
    function sendPointer(type, elementId, x, y) {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        ws.send(JSON.stringify({
            type: type,
            element_id: elementId,
            x: x,
            y: y
        }));
    }

    // ── Input Value Sending ────────────────────────────────────────
    function sendInputValue(elementId, value) {
        if (!ws || ws.readyState !== WebSocket.OPEN) return;
        ws.send(JSON.stringify({
            type: 'input_value',
            element_id: elementId,
            value: value
        }));
    }

    // ── FPS Counter ────────────────────────────────────────────────
    function updateFps() {
        frameCount++;
        const now = performance.now();
        if (now - lastFpsTime >= 500) {
            currentFps = Math.round(frameCount / ((now - lastFpsTime) / 1000));
            fpsEl.textContent = currentFps;
            frameCount = 0;
            lastFpsTime = now;
        }
    }

    // ── Initialize ─────────────────────────────────────────────────
    connect();
})();
