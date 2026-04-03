/**
 * Aetheris UI - WebAssembly Canvas Bridge
 * 
 * Interfaces Pyodide's AetherEngine with HTML5 Canvas 2D rendering.
 * Implements zero-leak PyProxy memory management in the animation loop.
 */

(function() {
    'use strict';

    // DOM elements
    const canvas = document.getElementById('aetherCanvas');
    const ctx = canvas.getContext('2d');
    const loadingEl = document.getElementById('loading');
    const fpsEl = document.getElementById('fps');
    const overlayEl = document.getElementById('aether-overlay');
    const progressBar = document.getElementById('progress-bar');
    const progressText = document.getElementById('progress-text');

    // Pyodide and engine references
    let pyodide = null;
    let engine = null;

    // FPS tracking
    let frameCount = 0;
    let lastFpsTime = performance.now();

    // DOM node tracking for hybrid compositing (DOMTextNode)
    const activeDOMNodes = {};
    
    // Progress bar state for Lerp smoothing
    let currentProgress = 0;
    let targetProgress = 0;
    let progressAnimFrame = null;

    /**
     * Algebraic Progress Bar Update using Linear Interpolation (Lerp).
     * 
     * Mathematical Foundation (Álgebra de Baldor - Proporciones):
     * v = a + t(b - a)
     * Where: a = current value, b = target value, t = smoothing factor
     * 
     * This creates a smooth, eased transition that feels natural rather than
     * the jarring jumps of direct assignment.
     * 
     * @param {number} target - Target progress (0-100)
     * @param {string} label - Status text to display
     */
    function updateProgress(target, label) {
        targetProgress = Math.max(0, Math.min(100, target));
        if (progressText) {
            progressText.textContent = label || `${Math.round(targetProgress)}%`;
        }
        
        // Start animation loop if not running
        if (!progressAnimFrame) {
            animateProgress();
        }
    }
    
    /**
     * Animate the progress bar using Lerp for smooth transitions.
     * Runs at ~60fps via requestAnimationFrame.
     */
    function animateProgress() {
        const smoothing = 0.15; // Lerp factor (higher = faster catch-up)
        
        // Lerp: current = current + (target - current) * smoothing
        currentProgress += (targetProgress - currentProgress) * smoothing;
        
        // Snap when very close (prevents infinite micro-adjustments)
        if (Math.abs(targetProgress - currentProgress) < 0.1) {
            currentProgress = targetProgress;
        }
        
        if (progressBar) {
            progressBar.style.width = `${currentProgress}%`;
        }
        
        // Continue animation if not yet at target
        if (Math.abs(targetProgress - currentProgress) > 0.01) {
            progressAnimFrame = requestAnimationFrame(animateProgress);
        } else {
            progressAnimFrame = null;
        }
    }

    /**
     * Resize canvas to fill viewport and sync with engine.
     */
    function resizeCanvas() {
        const dpr = window.devicePixelRatio || 1;
        canvas.width = window.innerWidth * dpr;
        canvas.height = window.innerHeight * dpr;
        ctx.scale(dpr, dpr);
    }

    /**
     * Load all core Python files into Pyodide's virtual filesystem.
     */
    async function mountCoreFiles() {
        const coreFiles = [
            'core/__init__.py',
            'core/aether_math.py',
            'core/solver.py',
            'core/solver_wasm.py',
            'core/solver_bridge.py',
            'core/state_manager.py',
            'core/tensor_compiler.py',
            'core/elements.py',
            'core/engine.py',
            'core/renderer_base.py',
            'core/ui_builder.py',
        ];

        // Create core directory
        pyodide.FS.mkdir('/core');

        // Fetch and write each file
        for (const file of coreFiles) {
            try {
                const response = await fetch(`/${file}`);
                if (!response.ok) {
                    console.warn(`Failed to fetch ${file}: ${response.status}`);
                    continue;
                }
                const content = await response.text();
                pyodide.FS.writeFile(`/${file}`, content);
            } catch (e) {
                console.warn(`Error loading ${file}: ${e.message}`);
            }
        }
    }

    /**
     * Initialize the Python AetherEngine using server-driven UI Intent JSON.
     * Reads the JSON from the injected script tag and passes it to Pyodide's
     * UIBuilder to dynamically create and register elements.
     */
    async function initEngine() {
        // Read the server-injected UI Intent JSON
        const intentEl = document.getElementById('aether-intent');
        const intentJsonString = intentEl ? intentEl.textContent.trim() : '{}';

        // Escape any problematic characters for safe Python string embedding
        const safeIntent = intentJsonString.replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '\\"');

        await pyodide.runPythonAsync(`
import sys
sys.path.insert(0, '/')

import json
import numpy as np
from core.engine import AetherEngine
from core.ui_builder import UIBuilder

# Create engine and builder
engine = AetherEngine()
builder = UIBuilder()

# Load intent from server-driven JSON
intent_data = json.loads("""${safeIntent}""")

# Build elements from intent and register with engine
builder.build_from_intent(engine, intent_data)

print(f"Aetheris Engine initialized with {engine.element_count} elements from server intent")
        `);

        // Get engine reference from Python globals
        engine = pyodide.globals.get('engine');
        return engine;
    }

    /**
     * Render loop - called via requestAnimationFrame at 60 FPS.
     * 
     * MEMORY MANAGEMENT: PyProxy objects from Pyodide must be explicitly
     * destroyed after use, otherwise they leak memory in the browser.
     * Every .get() call on a PyProxy creates a new proxy that must be .destroy()ed.
     * 
     * HYBRID COMPOSITING: We read both the NumPy physics array AND the JSON
     * metadata bridge to render text elements alongside physics-driven rectangles.
     * 
     * MEMORY MANAGEMENT: All PyProxy objects are destroyed in a finally block
     * to prevent leaks even when exceptions occur.
     */
    function renderLoop() {
        if (!engine) {
            requestAnimationFrame(renderLoop);
            return;
        }

        const width = window.innerWidth;
        const height = window.innerHeight;

        // Proxy references for cleanup in finally block
        let dataProxy = null;
        let rectProxy = null;
        let colorProxy = null;
        let zProxy = null;
        let rectBuffer = null;
        let colorBuffer = null;
        let zBuffer = null;
        let metadataProxy = null;

        try {
            // Call Python engine tick - returns a structured NumPy array as PyProxy
            dataProxy = engine.tick(width, height);

            // Extract field proxies from the structured array
            rectProxy = dataProxy.get('rect');
            colorProxy = dataProxy.get('color');
            zProxy = dataProxy.get('z');

            // Get number of elements
            const numElements = dataProxy.length;

            // Extract raw data from NumPy arrays via buffer protocol
            // Store buffer references so we can release them in finally
            rectBuffer = rectProxy.getBuffer();
            colorBuffer = colorProxy.getBuffer();
            zBuffer = zProxy.getBuffer();
            const rects = rectBuffer.data;    // Float32Array [x0,y0,w0,h0, ...]
            const colors = colorBuffer.data;  // Float32Array [r0,g0,b0,a0, ...]
            const zIndices = zBuffer.data;    // Int32Array [z0, z1, z2, ...]

            // HYBRID COMPOSITING: Get text metadata from engine via JSON bridge
            // This contains CanvasTextNode and DOMTextNode data keyed by z-index
            metadataProxy = engine.get_ui_metadata();
            const uiMetadata = JSON.parse(metadataProxy);
            metadataProxy.destroy();
            metadataProxy = null;

            // Track which DOM nodes are active this frame (for cleanup)
            const activeThisFrame = new Set();

            // Clear canvas
            ctx.fillStyle = 'rgba(10, 10, 10, 1.0)';
            ctx.fillRect(0, 0, width, height);

            // Render each element
            for (let i = 0; i < numElements; i++) {
                const idx = i * 4;

                // Extract rect [x, y, w, h]
                const x = rects[idx];
                const y = rects[idx + 1];
                const w = rects[idx + 2];
                const h = rects[idx + 3];

                // Extract color [r, g, b, a] (float32 0-1 range)
                const r = Math.round(colors[idx] * 255);
                const g = Math.round(colors[idx + 1] * 255);
                const b = Math.round(colors[idx + 2] * 255);
                const a = colors[idx + 3];

                // Get z-index for metadata lookup
                const z = zIndices[i];

                // Check if this element has text metadata
                const textData = uiMetadata[String(z)];
                if (textData && textData.type === 'dom_text') {
                    // DOMTextNode: Create/update HTML overlay element
                    const zKey = String(z);
                    activeThisFrame.add(zKey);

                    let node = activeDOMNodes[zKey];
                    if (!node) {
                        // Create new DOM element
                        node = document.createElement('div');
                        node.style.position = 'absolute';
                        node.style.pointerEvents = 'auto';
                        node.style.overflow = 'hidden';
                        node.style.display = 'flex';
                        node.style.alignItems = 'center';
                        node.style.justifyContent = 'center';
                        node.style.willChange = 'transform';
                        node.style.userSelect = 'text';
                        node.style.webkitUserSelect = 'text';
                        overlayEl.appendChild(node);
                        activeDOMNodes[zKey] = node;
                    }

                    // Update content and styling
                    const text = textData.text || '';
                    const fontSize = textData.size || 16;
                    const fontFamily = textData.family || 'Arial';
                    const tc = textData.color || [1, 1, 1, 1];
                    const tr = Math.round(tc[0] * 255);
                    const tg = Math.round(tc[1] * 255);
                    const tb = Math.round(tc[2] * 255);
                    const ta = tc[3];

                    node.textContent = text;
                    node.style.font = `${fontSize}px ${fontFamily}`;
                    node.style.color = `rgba(${tr}, ${tg}, ${tb}, ${ta})`;

                    // Hardware-accelerated CSS transforms for physics sync
                    node.style.transform = `translate3d(${x}px, ${y}px, 0)`;
                    node.style.width = `${w}px`;
                    node.style.height = `${h}px`;

                    // Don't draw anything on canvas for DOM text nodes
                } else if (textData && textData.type === 'canvas_text') {
                    // CanvasTextNode: Draw text directly on canvas
                    const text = textData.text || '';
                    const fontSize = textData.size || 24;
                    const fontFamily = textData.family || 'Arial';
                    const tc = textData.color || [1, 1, 1, 1];
                    const tr = Math.round(tc[0] * 255);
                    const tg = Math.round(tc[1] * 255);
                    const tb = Math.round(tc[2] * 255);
                    const ta = tc[3];

                    // Only draw rect background if alpha > 0
                    if (a > 0.01) {
                        ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${a})`;
                        if (ctx.roundRect && w > 20 && h > 20) {
                            ctx.beginPath();
                            ctx.roundRect(x, y, w, h, 8);
                            ctx.fill();
                        } else {
                            ctx.fillRect(x, y, w, h);
                        }
                    }

                    // Draw text centered in the rect
                    ctx.font = `${fontSize}px ${fontFamily}`;
                    ctx.fillStyle = `rgba(${tr}, ${tg}, ${tb}, ${ta})`;
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    const centerX = x + w / 2;
                    const centerY = y + h / 2;
                    ctx.fillText(text, centerX, centerY);
                } else {
                    // Regular physics element (no text metadata)
                    ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${a})`;
                    if (ctx.roundRect && w > 20 && h > 20) {
                        ctx.beginPath();
                        ctx.roundRect(x, y, w, h, 8);
                        ctx.fill();
                    } else {
                        ctx.fillRect(x, y, w, h);
                    }
                }
            }

            // Remove DOM nodes that are no longer needed
            for (const zKey of Object.keys(activeDOMNodes)) {
                if (!activeThisFrame.has(zKey)) {
                    const node = activeDOMNodes[zKey];
                    if (node && node.parentNode) {
                        node.parentNode.removeChild(node);
                    }
                    delete activeDOMNodes[zKey];
                }
            }

        } catch (e) {
            console.error('Error in render loop:', e);
        } finally {
            // CRITICAL: Destroy ALL PyProxy and PyBuffer objects to prevent memory leaks
            // This runs whether the frame succeeded or threw an exception
            if (rectBuffer) { rectBuffer.release(); rectBuffer = null; }
            if (colorBuffer) { colorBuffer.release(); colorBuffer = null; }
            if (zBuffer) { zBuffer.release(); zBuffer = null; }
            if (rectProxy) { rectProxy.destroy(); rectProxy = null; }
            if (colorProxy) { colorProxy.destroy(); colorProxy = null; }
            if (zProxy) { zProxy.destroy(); zProxy = null; }
            if (dataProxy) { dataProxy.destroy(); dataProxy = null; }
            if (metadataProxy) { metadataProxy.destroy(); metadataProxy = null; }
        }

        // FPS counter
        frameCount++;
        const now = performance.now();
        if (now - lastFpsTime >= 1000) {
            fpsEl.textContent = `FPS: ${frameCount}`;
            frameCount = 0;
            lastFpsTime = now;
        }

        // Schedule next frame
        requestAnimationFrame(renderLoop);
    }

    /**
     * Main initialization sequence with algebraic progress tracking.
     */
    async function main() {
        try {
            // Phase 1: Resize canvas (5%)
            updateProgress(5, 'Initializing viewport...');
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);

            // Phase 2: Load Pyodide runtime (10-40%)
            updateProgress(10, 'Loading Pyodide runtime...');
            pyodide = await loadPyodide({
                indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/',
            });
            updateProgress(40, 'Pyodide loaded');

            // Phase 3: Load numpy package (40-55%)
            updateProgress(45, 'Loading NumPy package...');
            await pyodide.loadPackage('numpy');
            updateProgress(55, 'NumPy ready');

            // Phase 4: Mount core Python files (55-80%)
            updateProgress(60, 'Loading core modules...');
            await mountCoreFiles();
            updateProgress(80, 'Core modules loaded');

            // Phase 5: Initialize AetherEngine (80-95%)
            updateProgress(85, 'Initializing physics engine...');
            await initEngine();
            updateProgress(95, 'Engine ready');

            // Phase 6: Complete (100%)
            updateProgress(100, 'Launching...');
            
            // Small delay to show 100% before hiding
            await new Promise(r => setTimeout(r, 300));

            // Hide loading screen with fade
            if (loadingEl) {
                loadingEl.classList.add('hidden');
                setTimeout(() => {
                    loadingEl.style.display = 'none';
                }, 500);
            }

            // Start render loop
            requestAnimationFrame(renderLoop);

        } catch (e) {
            if (loadingEl) {
                loadingEl.innerHTML = `<div style="color: #f66; font-family: monospace; text-align: center;">
                    <div style="font-size: 18px; margin-bottom: 8px;">Error</div>
                    <div style="font-size: 12px; color: #888;">${e.message}</div>
                </div>`;
            }
            console.error('Aetheris initialization failed:', e);
        }
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', main);
    } else {
        main();
    }

    // ========================================================================
    // Phase 19: Haptic Input Bridge (Drag, Drop, Throw)
    // ========================================================================
    
    let isPointerDown = false;
    let lastPointerX = 0;
    let lastPointerY = 0;
    let pointerMoveThrottle = false;

    /**
     * Hit test: find element under pointer using AABB check.
     * Returns element index or -1.
     */
    function hitTest(x, y, dataBuffer) {
        const rectProxy = dataBuffer.get('rect');
        const rectBuffer = rectProxy.getBuffer();
        const rects = rectBuffer.data;
        const n = dataBuffer.length;
        
        // Reverse order for z-index priority (top elements first)
        for (let i = n - 1; i >= 0; i--) {
            const idx = i * 4;
            const ex = rects[idx];
            const ey = rects[idx + 1];
            const ew = rects[idx + 2];
            const eh = rects[idx + 3];
            
            if (x >= ex && x <= ex + ew && y >= ey && y <= ey + eh) {
                rectBuffer.release();
                rectProxy.destroy();
                return i;
            }
        }
        
        rectBuffer.release();
        rectProxy.destroy();
        return -1;
    }

    function setupInputBridge() {
        const targets = [canvas, overlayEl];
        
        targets.forEach(target => {
            if (!target) return;
            
            target.addEventListener('pointerdown', (e) => {
                if (!engine) return;
                isPointerDown = true;
                lastPointerX = e.clientX;
                lastPointerY = e.clientY;
                
                // Get current frame data for hit testing
                const dataProxy = engine.tick(window.innerWidth, window.innerHeight);
                const hitIdx = hitTest(e.clientX, e.clientY, dataProxy);
                dataProxy.destroy();
                
                if (hitIdx >= 0) {
                    engine.handle_pointer_down(hitIdx, e.clientX, e.clientY);
                    target.setPointerCapture(e.pointerId);
                }
            });
            
            target.addEventListener('pointermove', (e) => {
                if (!engine || !isPointerDown) return;
                
                // Throttle to avoid overwhelming Pyodide
                if (pointerMoveThrottle) return;
                pointerMoveThrottle = true;
                setTimeout(() => { pointerMoveThrottle = false; }, 16);
                
                lastPointerX = e.clientX;
                lastPointerY = e.clientY;
                engine.handle_pointer_move(e.clientX, e.clientY);
            });
            
            target.addEventListener('pointerup', (e) => {
                if (!engine || !isPointerDown) return;
                isPointerDown = false;
                engine.handle_pointer_up();
                target.releasePointerCapture(e.pointerId);
            });
            
            target.addEventListener('pointercancel', (e) => {
                if (!engine || !isPointerDown) return;
                isPointerDown = false;
                engine.handle_pointer_up();
            });
        });
    }
    
    // Setup input bridge after engine initialization
    const _origMain = main;
    main = async function() {
        await _origMain();
        setupInputBridge();
    };

})();
