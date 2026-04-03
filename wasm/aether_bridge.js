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

    // Pyodide and engine references
    let pyodide = null;
    let engine = null;

    // FPS tracking
    let frameCount = 0;
    let lastFpsTime = performance.now();

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
     */
    function renderLoop() {
        if (!engine) {
            requestAnimationFrame(renderLoop);
            return;
        }

        const width = window.innerWidth;
        const height = window.innerHeight;

        try {
            // Call Python engine tick - returns a structured NumPy array as PyProxy
            const dataProxy = engine.tick(width, height);

            // Extract field proxies from the structured array
            const rectProxy = dataProxy.get('rect');
            const colorProxy = dataProxy.get('color');
            const zProxy = dataProxy.get('z');

            // Get number of elements
            const numElements = dataProxy.length;

            // Extract raw data from NumPy arrays via buffer protocol
            // This creates TypedArrays that share memory with the NumPy arrays
            const rects = rectProxy.getBuffer().data;    // Float32Array [x0,y0,w0,h0, x1,y1,w1,h1, ...]
            const colors = colorProxy.getBuffer().data;  // Float32Array [r0,g0,b0,a0, r1,g1,b1,a1, ...]
            const zIndices = zProxy.getBuffer().data;    // Int32Array [z0, z1, z2, ...]

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

                // Set fill color
                ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${a})`;

                // Draw rounded rectangle if available, fallback to regular rect
                if (ctx.roundRect && w > 20 && h > 20) {
                    ctx.beginPath();
                    ctx.roundRect(x, y, w, h, 8);
                    ctx.fill();
                } else {
                    ctx.fillRect(x, y, w, h);
                }
            }

            // CRITICAL: Destroy ALL PyProxy objects to prevent memory leaks
            // Each .get() call creates a new proxy that holds a reference to Python memory
            // If not destroyed, these accumulate and crash the browser
            rectProxy.destroy();
            colorProxy.destroy();
            zProxy.destroy();
            dataProxy.destroy();

        } catch (e) {
            console.error('Error in render loop:', e);
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
     * Main initialization sequence.
     */
    async function main() {
        try {
            // Resize canvas
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);

            // Initialize Pyodide
            pyodide = await loadPyodide({
                indexURL: 'https://cdn.jsdelivr.net/pyodide/v0.24.1/full/'
            });

            // Load numpy
            await pyodide.loadPackage('numpy');

            // Mount core Python files
            await mountCoreFiles();

            // Initialize AetherEngine
            await initEngine();

            // Hide loading screen
            loadingEl.style.display = 'none';

            // Start render loop
            requestAnimationFrame(renderLoop);

        } catch (e) {
            loadingEl.innerHTML = `<div style="color: #f66;">Error: ${e.message}</div>`;
            console.error('Aetheris initialization failed:', e);
        }
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', main);
    } else {
        main();
    }

})();
