# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Tests for LightWASM Adapter (M1).

These tests verify the implementation of the lightweight WASM adapter
and its compatibility with the existing WebBridge API.
"""
import json
import pytest
from unittest.mock import Mock, patch


class MockDifferentialElement:
    """Mock differential element for testing."""
    
    def __init__(self, x=0.0, y=0.0, w=100.0, h=100.0, z=0):
        self._x = x
        self._y = y
        self._w = w
        self._h = h
        self._z_index = z
        
        mock_tensor = Mock()
        mock_tensor.state = [x, y, w, h]
        self.tensor = mock_tensor


class TestLightWASMAdapter:
    """Tests for LightWASMAdapter."""
    
    def test_adapter_creation(self):
        """Test that adapter can be created with default parameters."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter()
        assert adapter is not None
        assert adapter.element_count == 0
    
    def test_adapter_with_dimensions(self):
        """Test adapter creation with custom dimensions."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(container_width=1920.0, container_height=1080.0)
        assert adapter._container_w == 1920.0
        assert adapter._container_h == 1080.0
    
    def test_register_element(self):
        """Test element registration."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        adapter.register_element(0, "element-1", {"tag": "div"})
        
        assert adapter.element_count == 1
        assert adapter.get_html_id(0) == "element-1"
    
    def test_unregister_element(self):
        """Test element unregistration."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        adapter.register_element(0, "element-1")
        adapter.unregister_element(0)
        
        assert adapter.element_count == 0
        assert adapter.get_html_id(0) is None
    
    def test_sync_returns_json(self):
        """Test that sync returns valid JSON."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        adapter.register_element(0, "element-1", {"tag": "div"})
        
        elements = [MockDifferentialElement(10, 10, 100, 100)]
        result = adapter.sync(elements)
        
        data = json.loads(result)
        assert "frame" in data
        assert "elements" in data
        assert len(data["elements"]) == 1
    
    def test_sync_with_coordinates(self):
        """Test sync preserves element coordinates."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        adapter.register_element(0, "elem-1")
        
        elements = [MockDifferentialElement(50.5, 75.3, 200.0, 150.0)]
        result = adapter.sync(elements)
        
        data = json.loads(result)
        elem = data["elements"][0]
        
        assert elem["x"] == 50.5
        assert elem["y"] == 75.3
        assert elem["w"] == 200.0
        assert elem["h"] == 150.0
    
    def test_sync_clamps_coordinates(self):
        """Test that coordinates are clamped to container bounds."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(
            container_width=100.0,
            container_height=100.0,
            use_light_wasm=False
        )
        adapter.register_element(0, "elem-1")
        
        elements = [MockDifferentialElement(200, 200, 50, 50)]
        result = adapter.sync(elements)
        
        data = json.loads(result)
        elem = data["elements"][0]
        
        assert elem["x"] == 50.0
        assert elem["y"] == 50.0
    
    def test_get_initial_dom_state(self):
        """Test initial DOM state generation."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        adapter.register_element(0, "element-1", {"tag": "div", "classes": ["box"]})
        adapter.register_element(1, "element-2", {"tag": "span", "text": "Hello"})
        
        state = adapter.get_initial_dom_state()
        
        assert len(state) == 2
        assert state[0]["id"] == "element-1"
        assert state[1]["id"] == "element-2"
    
    def test_adapter_stats(self):
        """Test adapter statistics."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        adapter.register_element(0, "elem-1")
        
        elements = [MockDifferentialElement(10, 10, 100, 100)]
        adapter.sync(elements)
        
        stats = adapter.stats
        assert stats["elements"] == 1
        assert stats["sync_frames"] == 1
    
    def test_adapter_type_property(self):
        """Test adapter type detection."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        
        adapter_type = adapter.adapter_type
        assert adapter_type in ["pyodide", "js_renderer", "webgl", "unknown"]
    
    def test_bundle_size(self):
        """Test bundle size estimation."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        
        size = adapter.bundle_size
        assert size >= 0
    
    def test_backwards_compatibility(self):
        """Test backwards compatibility with WebBridge API."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        from core.web_bridge import WebBridge
        
        lb_adapter = LightWASMAdapter(use_light_wasm=False)
        wb_bridge = WebBridge()
        
        lb_adapter.register_element(0, "test-elem", {"tag": "div"})
        wb_bridge.register_element(0, "test-elem", {"tag": "div"})
        
        elements = [MockDifferentialElement(10, 20, 100, 100)]
        
        lb_result = lb_adapter.sync(elements)
        wb_result = wb_bridge.sync(elements)
        
        lb_data = json.loads(lb_result)
        wb_data = json.loads(wb_result)
        
        assert lb_data["frame"] == wb_data["frame"]
        assert len(lb_data["elements"]) == len(wb_data["elements"])
    
    def test_feature_flag_env_variable(self):
        """Test environment variable feature flag."""
        import os
        import importlib
        
        original = os.environ.get("AETHERIS_USE_LIGHT_WASM")
        
        os.environ["AETHERIS_USE_LIGHT_WASM"] = "false"
        
        import wasm.light_wasm_adapter
        importlib.reload(wasm.light_wasm_adapter)
        
        from wasm.light_wasm_adapter import _USE_LIGHT_WASM
        
        assert _USE_LIGHT_WASM == False
        
        if original is not None:
            os.environ["AETHERIS_USE_LIGHT_WASM"] = original
        else:
            os.environ.pop("AETHERIS_USE_LIGHT_WASM", None)
    
    def test_set_preferred_adapter(self):
        """Test manual adapter selection."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        
        adapter.set_preferred_adapter("pyodide")
        assert adapter._fallback_mode == True
        
        adapter.set_preferred_adapter("js_renderer")
        assert adapter._fallback_mode == False
    
    def test_detect_capabilities(self):
        """Test capability detection."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        
        caps = adapter.detect_capabilities()
        
        assert "canvas_2d" in caps
        assert caps["canvas_2d"] == True
    
    def test_multiple_elements_sync(self):
        """Test syncing multiple elements."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        
        for i in range(100):
            adapter.register_element(i, f"elem-{i}")
        
        elements = [
            MockDifferentialElement(i * 10, i * 10, 50, 50, z=i)
            for i in range(100)
        ]
        
        result = adapter.sync(elements)
        data = json.loads(result)
        
        assert len(data["elements"]) == 100


class TestAdapterInterface:
    """Tests for adapter interface compliance."""
    
    def test_js_renderer_interface(self):
        """Test JSRenderer implements AdapterInterface."""
        from wasm.adapters.js_renderer import JSRenderer
        
        renderer = JSRenderer()
        
        assert hasattr(renderer, "sync")
        assert hasattr(renderer, "register_element")
        assert hasattr(renderer, "unregister_element")
        assert hasattr(renderer, "get_initial_dom_state")
        assert hasattr(renderer, "element_count")
        assert hasattr(renderer, "stats")
        assert hasattr(renderer, "adapter_type")
        assert hasattr(renderer, "bundle_size")
    
    def test_pyodide_fallback_interface(self):
        """Test PyodideFallback implements AdapterInterface."""
        from wasm.adapters.pyodide_fallback import PyodideFallback
        
        fallback = PyodideFallback()
        
        assert hasattr(fallback, "sync")
        assert hasattr(fallback, "register_element")
        assert hasattr(fallback, "unregister_element")
        assert hasattr(fallback, "get_initial_dom_state")
        assert hasattr(fallback, "element_count")
        assert hasattr(fallback, "stats")
        assert hasattr(fallback, "adapter_type")
        assert hasattr(fallback, "bundle_size")


class TestWebGLRenderer:
    """Tests for WebGL renderer."""
    
    def test_webgl_renderer_creation(self):
        """Test WebGL renderer can be created."""
        from wasm.adapters.js_renderer import WebGLRenderer
        
        renderer = WebGLRenderer()
        
        assert renderer is not None
        assert renderer._use_webgl == True
    
    def test_webgl_capabilities(self):
        """Test WebGL capabilities detection."""
        from wasm.adapters.js_renderer import WebGLRenderer
        
        renderer = WebGLRenderer()
        caps = renderer.detect_capabilities()
        
        assert caps["webgl"] == True


class TestCapabilityDetector:
    """Tests for capability detector."""
    
    def test_detect_capabilities(self):
        """Test capability detection."""
        from wasm.adapters.base import CapabilityDetector, RendererCapability
        
        caps = [
            RendererCapability.CANVAS_2D,
            RendererCapability.WEBGL,
        ]
        
        available = CapabilityDetector.detect(caps)
        
        assert len(available) > 0
    
    def test_select_adapter(self):
        """Test adapter selection."""
        from wasm.adapters.base import CapabilityDetector, RendererCapability, AdapterType
        
        caps = [
            RendererCapability.CANVAS_2D,
            RendererCapability.WEBGL,
        ]
        
        adapter_type = CapabilityDetector.select_adapter(caps)
        
        assert adapter_type in [AdapterType.WEBGL, AdapterType.JS_RENDERER]


class TestCreateAdapterFactory:
    """Tests for create_adapter factory function."""
    
    def test_create_adapter_default(self):
        """Test factory creates adapter with defaults."""
        from wasm.light_wasm_adapter import create_adapter
        
        adapter = create_adapter()
        
        assert adapter is not None
    
    def test_create_adapter_with_dimensions(self):
        """Test factory with custom dimensions."""
        from wasm.light_wasm_adapter import create_adapter
        
        adapter = create_adapter(
            container_width=1920.0,
            container_height=1080.0,
        )
        
        assert adapter._container_w == 1920.0
        assert adapter._container_h == 1080.0
    
    def test_create_adapter_force(self):
        """Test factory with forced adapter."""
        from wasm.light_wasm_adapter import create_adapter
        
        adapter = create_adapter(force_adapter="pyodide")
        
        assert adapter._fallback_mode == True


class TestPerformance:
    """Performance benchmark tests."""
    
    def test_sync_performance_1000_elements(self):
        """Test sync performance with 1000 elements."""
        from wasm.light_wasm_adapter import LightWASMAdapter
        
        adapter = LightWASMAdapter(use_light_wasm=False)
        
        for i in range(1000):
            adapter.register_element(i, f"elem-{i}")
        
        elements = [
            MockDifferentialElement(i % 1280, i % 720, 50, 50)
            for i in range(1000)
        ]
        
        import time
        start = time.perf_counter()
        
        for _ in range(10):
            adapter.sync(elements)
        
        elapsed = time.perf_counter() - start
        avg_time = elapsed / 10
        
        assert avg_time < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])