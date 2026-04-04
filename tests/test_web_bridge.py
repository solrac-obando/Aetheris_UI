# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Web Bridge Tests — Strict validation of coordinate translation & sync.
Tests are immutable. Code must be fixed to pass.
"""
import os, sys, json, time, math
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.web_bridge import WebBridge
from core.elements import StaticBox
from core.aether_math import StateTensor


class TestWebBridge:
    """Tests for WebBridge coordinate translation and synchronization."""

    def test_bridge_init(self):
        """Test 1: Initialization without errors, buffers pre-assigned."""
        bridge = WebBridge(1920.0, 1080.0)
        assert bridge._container_w == 1920.0
        assert bridge._container_h == 1080.0
        assert bridge._element_map == {}
        assert bridge._metadata == {}
        assert bridge._sync_count == 0

    def test_register_element(self):
        """Test 2: Assigns unique HTML ID and maps to StateTensor."""
        bridge = WebBridge()
        bridge.register_element(0, "btn_1", {"tag": "button", "text": "Click"})
        assert bridge.get_html_id(0) == "btn_1"
        assert bridge._metadata["btn_1"]["tag"] == "button"
        assert bridge._metadata["btn_1"]["text"] == "Click"

    def test_unregister_element(self):
        """Test 2b: Removing an element cleans up both map and metadata."""
        bridge = WebBridge()
        bridge.register_element(0, "btn_1", {"tag": "button"})
        bridge.unregister_element(0)
        assert bridge.get_html_id(0) is None
        assert "btn_1" not in bridge._metadata

    def test_get_html_mapping(self):
        """Test 3: Generates correct JSON for creating <div> in frontend."""
        bridge = WebBridge()
        bridge.register_element(0, "card_1", {
            "tag": "div", "classes": ["card"], "text": "Hello"
        })
        dom_state = bridge.get_initial_dom_state()
        assert len(dom_state) == 1
        assert dom_state[0]["id"] == "card_1"
        assert dom_state[0]["tag"] == "div"
        assert dom_state[0]["classes"] == ["card"]
        assert dom_state[0]["text"] == "Hello"

    def test_coordinate_sync(self):
        """Test 4: Converts float32 from engine to CSS px with precision."""
        bridge = WebBridge()
        bridge.register_element(0, "el_1")
        elem = StaticBox(100.5, 200.7, 50.3, 30.1, z=0)
        payload = json.loads(bridge.sync([elem]))
        assert len(payload["elements"]) == 1
        el = payload["elements"][0]
        assert el["id"] == "el_1"
        assert abs(el["x"] - 100.5) < 0.1
        assert abs(el["y"] - 200.7) < 0.1
        assert abs(el["w"] - 50.3) < 0.1
        assert abs(el["h"] - 30.1) < 0.1

    def test_boundary_clamp(self):
        """Test 5: Coordinates never exceed window.innerWidth/Height."""
        bridge = WebBridge(800.0, 600.0)
        bridge.register_element(0, "el_1")
        # Element positioned outside container
        elem = StaticBox(900.0, 700.0, 100.0, 100.0, z=0)
        payload = json.loads(bridge.sync([elem]))
        el = payload["elements"][0]
        # x + w must be <= container_w (800)
        assert el["x"] + el["w"] <= 800.0 + 0.1
        # y + h must be <= container_h (600)
        assert el["y"] + el["h"] <= 600.0 + 0.1
        # Coordinates must be >= 0
        assert el["x"] >= 0.0
        assert el["y"] >= 0.0

    def test_sync_latency(self):
        """Test 6: Sync of 100 elements takes < 16ms."""
        bridge = WebBridge()
        elements = []
        for i in range(100):
            bridge.register_element(i, f"el_{i}")
            elements.append(StaticBox(
                float(i * 10), float(i * 5), 50.0, 30.0, z=i
            ))

        # Warm up
        bridge.sync(elements)

        # Measure
        times = []
        for _ in range(50):
            t0 = time.perf_counter()
            bridge.sync(elements)
            times.append((time.perf_counter() - t0) * 1000)

        avg_ms = np.mean(times)
        assert avg_ms < 16.0, f"Sync latency {avg_ms:.2f}ms exceeds 16ms budget"

    def test_nan_protection(self):
        """Test 6b: NaN values are excluded from sync payload."""
        bridge = WebBridge()
        bridge.register_element(0, "el_nan")
        elem = StaticBox(100.0, 200.0, 50.0, 30.0, z=0)
        # Inject NaN
        elem.tensor.state[0] = np.float32(np.nan)
        payload = json.loads(bridge.sync([elem]))
        assert len(payload["elements"]) == 0, "NaN element should be excluded"

    def test_inf_protection(self):
        """Test 6c: Inf values are excluded from sync payload."""
        bridge = WebBridge()
        bridge.register_element(0, "el_inf")
        elem = StaticBox(100.0, 200.0, 50.0, 30.0, z=0)
        elem.tensor.state[1] = np.float32(np.inf)
        payload = json.loads(bridge.sync([elem]))
        assert len(payload["elements"]) == 0, "Inf element should be excluded"

    def test_frame_counter_increments(self):
        """Test 6d: Frame counter increments on each sync."""
        bridge = WebBridge()
        bridge.register_element(0, "el_1")
        elem = StaticBox(100.0, 100.0, 50.0, 30.0, z=0)
        p1 = json.loads(bridge.sync([elem]))
        p2 = json.loads(bridge.sync([elem]))
        assert p2["frame"] == p1["frame"] + 1

    def test_empty_elements_sync(self):
        """Test 6e: Sync with no elements returns valid empty payload."""
        bridge = WebBridge()
        payload = json.loads(bridge.sync([]))
        assert payload["elements"] == []
        assert "frame" in payload
        assert "timestamp" in payload

    def test_stats_property(self):
        """Test 6f: Stats property returns correct metadata."""
        bridge = WebBridge()
        bridge.register_element(0, "el_1")
        stats = bridge.stats
        assert stats["elements"] == 1
        assert stats["sync_frames"] == 0
        bridge.sync([StaticBox(0, 0, 10, 10)])
        stats = bridge.stats
        assert stats["sync_frames"] == 1
