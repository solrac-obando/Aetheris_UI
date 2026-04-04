# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Web Integration Tests — 10 production-grade assertions for the
complete WebApp pipeline: Engine + Bridge + WebSocket + Client.

These tests verify the bidirectional event bridge, sync cycles,
and full lifecycle management. Tests are immutable — code must
be fixed to pass.
"""
import os, sys, json, time, gc
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.web_app import WebApp
from core.web_elements import WebButton, WebText, WebCard, WebInput, WebElement
from core.web_bridge import WebBridge
from core.web_server import WebServer


class TestWebIntegration:
    """Integration tests for the complete WebApp pipeline."""

    def test_webapp_init(self):
        """Test 1: Verifies initial configuration."""
        app = WebApp(title="Test App", width=1280, height=720, ws_port=19001)
        assert app.title == "Test App"
        assert app.width == 1280.0
        assert app.height == 720.0
        assert app.engine is not None
        assert app.bridge is not None
        assert app.server is not None
        assert not app._running
        assert len(app._elements) == 0

    def test_webapp_add_element(self):
        """Test 2: Verifies registration in the Bridge."""
        app = WebApp(ws_port=19002)
        btn = WebButton(text="Click", x=100, y=100, w=120, h=40)
        app.add(btn)
        assert len(app._elements) == 1
        assert app.engine.element_count == 1
        assert app.bridge.element_count == 1
        assert app.bridge.get_html_id(0) == btn._html_id

    def test_webapp_sync_cycle(self):
        """Test 3: A complete cycle of Tick -> Sync -> Broadcast."""
        app = WebApp(ws_port=19003)
        app.add(WebButton(text="Test", x=200, y=300, w=100, h=50))

        # Run one tick
        app.engine.tick(app.width, app.height)

        # Sync should produce valid payload
        payload = app.bridge.sync(app._elements)
        data = json.loads(payload)
        assert "elements" in data
        assert len(data["elements"]) == 1
        el = data["elements"][0]
        assert el["id"] == app._elements[0]._html_id
        assert el["x"] == 200.0
        assert el["y"] == 300.0
        assert el["w"] == 100.0
        assert el["h"] == 50.0

    def test_webapp_pointer_roundtrip(self):
        """Test 4: JS event reaches the Python engine."""
        app = WebApp(ws_port=19004)
        btn = WebButton(text="Drag Me", x=100, y=100, w=120, h=40)
        app.add(btn)
        app.engine.tick(app.width, app.height)

        # Simulate JS sending pointerdown
        app._handle_ws_message("client_1", json.dumps({
            "type": "pointerdown",
            "x": 150.0,
            "y": 120.0
        }))

        # Engine should be in dragging state
        assert app.engine.input_manager.is_dragging is True

        # Simulate pointerup
        app._handle_ws_message("client_1", json.dumps({
            "type": "pointerup"
        }))
        assert app.engine.input_manager.is_dragging is False

    def test_webapp_drag_physics(self):
        """Test 5: Web drag affects the StateTensor position."""
        app = WebApp(ws_port=19005)
        btn = WebButton(text="Drag", x=100, y=100, w=120, h=40)
        app.add(btn)

        # Initial state
        orig_x = float(btn.tensor.state[0])
        orig_y = float(btn.tensor.state[1])

        # Simulate drag — pointer at edge of button to generate force
        # Button spans x=100-220, y=100-140. Center is (160, 120).
        # Click at edge to create drag offset
        app._handle_ws_message("client_1", json.dumps({
            "type": "pointerdown",
            "x": 105.0,
            "y": 105.0
        }))
        app.engine.tick(app.width, app.height)

        # Move pointer far away
        app._handle_ws_message("client_1", json.dumps({
            "type": "pointermove",
            "x": 500.0,
            "y": 400.0
        }))
        app.engine.tick(app.width, app.height)

        # Release — applies throw velocity
        app._handle_ws_message("client_1", json.dumps({
            "type": "pointerup"
        }))
        app.engine.tick(app.width, app.height)

        # After drag + release with throw velocity, element should have moved
        new_x = float(btn.tensor.state[0])
        new_y = float(btn.tensor.state[1])
        moved = abs(new_x - orig_x) > 0.01 or abs(new_y - orig_y) > 0.01
        assert moved, "Drag did not affect element position"

    def test_webapp_50_elements(self):
        """Test 6: Bulk synchronization performance for 50 elements."""
        app = WebApp(ws_port=19006)
        for i in range(50):
            app.add(WebButton(
                text=f"Btn {i}",
                x=float((i % 10) * 120),
                y=float((i // 10) * 60),
                w=100, h=40
            ))

        # Warm up
        app.engine.tick(app.width, app.height)
        app.bridge.sync(app._elements)

        # Measure sync performance
        times = []
        for _ in range(50):
            app.engine.tick(app.width, app.height)
            t0 = time.perf_counter()
            app.bridge.sync(app._elements)
            times.append((time.perf_counter() - t0) * 1000)

        avg_ms = np.mean(times)
        assert avg_ms < 16.0, f"Sync latency {avg_ms:.2f}ms exceeds 16ms for 50 elements"

    def test_webapp_html_creation(self):
        """Test 7: Verifies metadata JSON generation for DOM creation."""
        app = WebApp(ws_port=19007)
        app.add(WebButton(text="Submit", x=0, y=0, w=100, h=40))
        app.add(WebText(text="Label", x=0, y=50, w=200, h=30))
        app.add(WebCard(title="Panel", x=0, y=100, w=300, h=200))
        app.add(WebInput(placeholder="Type...", x=0, y=320, w=200, h=36))

        dom_state = app.bridge.get_initial_dom_state()
        assert len(dom_state) == 4

        # Verify each element type
        tags = [d["tag"] for d in dom_state]
        assert "button" in tags
        assert "span" in tags
        assert "div" in tags
        assert "input" in tags

        # Verify text content
        texts = [d.get("text", "") for d in dom_state]
        assert "Submit" in texts
        assert "Label" in texts
        assert "Panel" in texts

    def test_webapp_input_value(self):
        """Test 8: Captures text from a WebInput."""
        app = WebApp(ws_port=19008)
        inp = WebInput(placeholder="Search...", x=0, y=0, w=200, h=36)
        app.add(inp)

        # Simulate JS sending input value
        app._handle_ws_message("client_1", json.dumps({
            "type": "input_value",
            "element_id": inp._html_id,
            "value": "hello world"
        }))

        assert inp._value == "hello world"

    def test_webapp_disconnect_reconnect(self):
        """Test 9: Tests server robustness on disconnect/reconnect."""
        app = WebApp(ws_port=19009)
        app.add(WebButton(text="Test", x=100, y=100))

        # Start server
        app.server.start()
        time.sleep(0.5)

        # Simulate disconnect
        app.server.handle_client_disconnect("fake_client")

        # Server should still be running
        assert app.server.is_running

        # Simulate reconnect — message handler should still work
        app._handle_ws_message("new_client", json.dumps({
            "type": "pointerdown",
            "x": 150.0,
            "y": 150.0
        }))
        # Message handler was called successfully (no crash)
        # is_dragging depends on hit test — just verify no exception
        assert app.server.is_running

        app.server.stop()

    def test_webapp_clean_shutdown(self):
        """Test 10: Closes threads and asyncio loops cleanly."""
        import threading
        initial_threads = threading.active_count()

        app = WebApp(ws_port=19010)
        app.add(WebButton(text="Test", x=100, y=100))
        app.add(WebText(text="Label", x=100, y=150))

        # Start in non-blocking mode
        app.run(blocking=False)
        time.sleep(1.0)

        # Stop
        app.stop()
        gc.collect()
        time.sleep(0.5)

        final_threads = threading.active_count()
        assert final_threads <= initial_threads + 1, \
            f"Orphaned threads: {initial_threads} -> {final_threads}"
        assert not app._running
        assert not app.server.is_running
