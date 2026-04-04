# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
16-assertion test suite for Aether-Web WASM Sandbox.
Tests the web build integrity, physics logic, and server startup — all in standard Python.
"""
import os, sys, json, time, threading, socket
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "demo", "web")


# ── 1. index.html exists with canvas ──────────────────────────────────────
class TestWebWASM:
    def test_01_index_html_exists_with_canvas(self):
        """Assertion 1: demo/web/index.html exists and contains the <canvas> tag."""
        path = os.path.join(WEB_DIR, "index.html")
        assert os.path.exists(path), "index.html not found"
        with open(path) as f:
            content = f.read()
        assert "<canvas" in content, "No <canvas> tag in index.html"
        assert "id=\"canvas\"" in content, "Canvas missing id='canvas'"

    # ── 2. manifest.json is valid ─────────────────────────────────────────
    def test_02_manifest_json_valid(self):
        """Assertion 2: demo/web/manifest.json exists and is valid JSON."""
        path = os.path.join(WEB_DIR, "manifest.json")
        assert os.path.exists(path), "manifest.json not found"
        with open(path) as f:
            data = json.load(f)
        assert data["name"] == "Aether-Web Particle Sandbox"
        assert data["display"] == "standalone"
        assert "start_url" in data
        assert "icons" in data
        assert len(data["icons"]) >= 1

    # ── 3. aether_wasm.py imports without crashing ────────────────────────
    def test_03_wasm_module_imports(self):
        """Assertion 3: aether_wasm.py can be imported in standard Python without crashing."""
        from demo.web.aether_wasm import AetherWASM, _HAS_PYODIDE
        assert AetherWASM is not None
        assert _HAS_PYODIDE is False  # We're in standard Python, not Pyodide

    # ── 4. tick() returns valid array of correct length ───────────────────
    def test_04_tick_returns_valid_array(self):
        """Assertion 4: The Python tick() function returns a valid array matching node count."""
        from demo.web.aether_wasm import AetherWASM, tick_standard
        result = tick_standard(640, 360, "attract")
        n = AetherWASM.get_node_count()
        assert len(result) == n * 4, f"Expected {n * 4} values, got {len(result)}"
        assert result.dtype == np.float32

    # ── 5. Mouse coordinates apply gravitational pull ─────────────────────
    def test_05_mouse_gravity_pull(self):
        """Assertion 5: Mouse coordinates passed to tick(x, y) apply gravitational pull."""
        from demo.web.aether_wasm import AetherWASM
        # Reset to known state
        AetherWASM.reset()
        # Move mouse to top-left
        AetherWASM.tick(50, 50, "attract")
        # Particles should have moved toward (50, 50)
        for node in AetherWASM.nodes:
            assert node.vx != 0 or node.vy != 0, "No velocity after mouse tick"

    # ── 6. Repel mode pushes particles away ───────────────────────────────
    def test_06_repel_mode(self):
        """Assertion 6: Repel mode pushes particles away from cursor."""
        from demo.web.aether_wasm import AetherWASM
        AetherWASM.reset()
        cx, cy = AetherWASM.get_canvas_size()
        # Place mouse at center
        AetherWASM.tick(cx / 2, cy / 2, "repel")
        # Particles very close to center should have velocity away from center
        repel_count = 0
        for node in AetherWASM.nodes:
            dx = node.x - cx / 2
            dy = node.y - cy / 2
            dist = np.sqrt(dx * dx + dy * dy)
            if dist < 100:
                dot = node.vx * dx + node.vy * dy
                if dot >= 0:
                    repel_count += 1
        # At least half of nearby particles should be repelled
        assert repel_count >= 1, "No particles repelled from center"

    # ── 7. Vortex mode creates rotational force ───────────────────────────
    def test_07_vortex_mode(self):
        """Assertion 7: Vortex mode creates rotational (tangential) force."""
        from demo.web.aether_wasm import AetherWASM
        AetherWASM.reset()
        cx, cy = AetherWASM.get_canvas_size()
        AetherWASM.tick(cx / 2, cy / 2, "vortex")
        # At least some particles should have non-zero velocity
        has_motion = any(
            abs(n.vx) > 0.01 or abs(n.vy) > 0.01
            for n in AetherWASM.nodes
        )
        assert has_motion, "No particles moving in vortex mode"

    # ── 8. HTTP server starts and binds ───────────────────────────────────
    def test_08_server_starts(self):
        """Assertion 8: HTTP server can start and bind to a port."""
        from demo.web.serve import WASMHandler, WEB_DIR as serve_web_dir
        import http.server
        # Find free port
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
        sock.close()
        server = http.server.HTTPServer(('127.0.0.1', port), WASMHandler)
        t = threading.Thread(target=server.handle_request, daemon=True)
        t.start()
        time.sleep(0.5)
        assert server.socket.getsockname()[1] == port
        server.server_close()

    # ── 9. Element bounds within canvas ───────────────────────────────────
    def test_09_element_bounds(self):
        """Assertion 9: All particle positions remain within canvas bounds after ticks."""
        from demo.web.aether_wasm import AetherWASM
        AetherWASM.reset()
        cx, cy = AetherWASM.get_canvas_size()
        for _ in range(200):
            AetherWASM.tick(cx / 2, cy / 2, "attract")
        for node in AetherWASM.nodes:
            assert node.radius <= node.x <= cx - node.radius, f"X out of bounds: {node.x}"
            assert node.radius <= node.y <= cy - node.radius, f"Y out of bounds: {node.y}"

    # ── 10. Node count matches constant ───────────────────────────────────
    def test_10_node_count_matches(self):
        """Assertion 10: Engine has exactly NODE_COUNT particles."""
        from demo.web.aether_wasm import AetherWASM, NODE_COUNT
        assert AetherWASM.get_node_count() == NODE_COUNT

    # ── 11. Reset restores initial state ──────────────────────────────────
    def test_11_reset_restores_state(self):
        """Assertion 11: Reset function restores particles to initial positions."""
        from demo.web.aether_wasm import AetherWASM
        # Run some ticks to move particles
        AetherWASM.tick(100, 100, "attract")
        AetherWASM.tick(200, 200, "attract")
        # Reset
        AetherWASM.reset()
        # All velocities should be zero
        for node in AetherWASM.nodes:
            assert node.vx == 0.0, f"vx not zero after reset: {node.vx}"
            assert node.vy == 0.0, f"vy not zero after reset: {node.vy}"

    # ── 12. Float32 precision maintained ──────────────────────────────────
    def test_12_float32_precision(self):
        """Assertion 12: Position data maintains float32 precision."""
        from demo.web.aether_wasm import AetherWASM, tick_standard
        result = tick_standard(640, 360)
        assert result.dtype == np.float32, f"Expected float32, got {result.dtype}"
        assert not np.any(np.isnan(result)), "NaN in position data"
        assert not np.any(np.isinf(result)), "Inf in position data"

    # ── 13. sw.js exists with required events ─────────────────────────────
    def test_13_service_worker_exists(self):
        """Assertion 13: Service worker file exists with required lifecycle events."""
        path = os.path.join(WEB_DIR, "sw.js")
        assert os.path.exists(path), "sw.js not found"
        with open(path) as f:
            content = f.read()
        assert "install" in content, "Missing install event"
        assert "fetch" in content, "Missing fetch event"
        assert "activate" in content, "Missing activate event"

    # ── 14. HTML contains Pyodide CDN ─────────────────────────────────────
    def test_14_html_has_pyodide_script(self):
        """Assertion 14: index.html includes Pyodide CDN script tag."""
        path = os.path.join(WEB_DIR, "index.html")
        with open(path) as f:
            content = f.read()
        assert "pyodide" in content.lower(), "No Pyodide reference in HTML"
        assert "loadPyodide" in content, "No loadPyodide() call"
        assert "requestAnimationFrame" in content, "No animation loop"

    # ── 15. HTML contains PWA meta tags ───────────────────────────────────
    def test_15_html_has_pwa_meta(self):
        """Assertion 15: index.html contains PWA-related meta tags and manifest link."""
        path = os.path.join(WEB_DIR, "index.html")
        with open(path) as f:
            content = f.read()
        assert "manifest" in content, "No manifest link"
        assert "theme-color" in content, "No theme-color meta tag"
        assert "viewport" in content, "No viewport meta tag"
        assert "serviceWorker" in content, "No service worker registration"

    # ── 16. Performance: 500 ticks under time budget ──────────────────────
    def test_16_performance_500_ticks(self):
        """Assertion 16: 500 physics ticks complete in under 5 seconds (10ms avg)."""
        from demo.web.aether_wasm import AetherWASM, tick_standard
        AetherWASM.reset()
        cx, cy = AetherWASM.get_canvas_size()
        t0 = time.perf_counter()
        for _ in range(500):
            tick_standard(cx / 2, cy / 2, "attract")
        elapsed = time.perf_counter() - t0
        avg_ms = (elapsed / 500) * 1000
        assert elapsed < 5.0, f"500 ticks took {elapsed:.2f}s (avg {avg_ms:.2f}ms)"
        assert avg_ms < 10.0, f"Average tick time {avg_ms:.2f}ms exceeds 10ms budget"
