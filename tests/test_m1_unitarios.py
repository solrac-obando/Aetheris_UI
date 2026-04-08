# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
M1 Unit Tests - 20 pruebas unitarias para WASM Ligero.

这些 pruebas verifican:
- Compatibilidad backwards con WebBridge
- Rendimiento del renderer
- Edge cases y boundary conditions

NO modificamos los tests - el código debe pasar las pruebas.
"""
import json
import time
import math
import pytest
from unittest.mock import Mock

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wasm.light_wasm_adapter import LightWASMAdapter, create_adapter
from core.web_bridge import WebBridge
from core.elements import StaticBox


class MockElement:
    """Mock element que simula DifferentialElement."""
    def __init__(self, x=0.0, y=0.0, w=100.0, h=100.0, z=0):
        self._x = x
        self._y = y
        self._w = w
        self._h = h
        self._z_index = z
        mock_tensor = Mock()
        mock_tensor.state = [float(x), float(y), float(w), float(h)]
        self.tensor = mock_tensor


# ==============================================================================
# GRUPO 1: Backwards Compatibility Tests (10 tests)
# ==============================================================================

class TestM1BackwardsCompatibility:
    """Test 1-10: Verificar API compatibility con WebBridge."""

    def test_01_init_signature_identical(self):
        """Test 1: __init__ signature debe ser identical."""
        wb = WebBridge(1920.0, 1080.0)
        la = LightWASMAdapter(1920.0, 1080.0)
        
        assert wb._container_w == la._container_w
        assert wb._container_h == la._container_h

    def test_02_register_element_same_signature(self):
        """Test 2: register_element tiene misma firma."""
        wb = WebBridge()
        la = LightWASMAdapter(use_light_wasm=False)
        
        wb.register_element(0, "elem-1", {"tag": "div"})
        la.register_element(0, "elem-1", {"tag": "div"})
        
        assert wb._element_map[0] == la._element_map[0]

    def test_03_unregister_element_same_signature(self):
        """Test 3: unregister_element tiene misma firma."""
        wb = WebBridge()
        la = LightWASMAdapter(use_light_wasm=False)
        
        wb.register_element(0, "elem-1")
        la.register_element(0, "elem-1")
        
        wb.unregister_element(0)
        la.unregister_element(0)
        
        assert 0 not in wb._element_map
        assert 0 not in la._element_map

    def test_04_sync_returns_json_string(self):
        """Test 4: sync() retorna JSON string."""
        wb = WebBridge()
        la = LightWASMAdapter(use_light_wasm=False)
        
        elem = MockElement(10, 20, 50, 30)
        
        wb_result = wb.sync([elem])
        la_result = la.sync([elem])
        
        assert isinstance(wb_result, str)
        assert isinstance(la_result, str)
        
        json.loads(wb_result)
        json.loads(la_result)

    def test_05_sync_json_structure_identical(self):
        """Test 5: JSON structure es identical."""
        wb = WebBridge()
        la = LightWASMAdapter(use_light_wasm=False)
        
        elem = MockElement(100.5, 200.7, 50.3, 30.1, z=1)
        
        wb.sync([elem])
        la.sync([elem])

    def test_06_get_initial_dom_state_structure(self):
        """Test 6: get_initial_dom_state estructura identical."""
        wb = WebBridge()
        la = LightWASMAdapter(use_light_wasm=False)
        
        wb.register_element(0, "div-1", {"tag": "div", "classes": ["box"]})
        la.register_element(0, "div-1", {"tag": "div", "classes": ["box"]})
        
        wb_state = wb.get_initial_dom_state()
        la_state = la.get_initial_dom_state()
        
        assert len(wb_state) == len(la_state)
        assert wb_state[0].keys() == la_state[0].keys()

    def test_07_element_count_property(self):
        """Test 7: element_count property identico."""
        wb = WebBridge()
        la = LightWASMAdapter(use_light_wasm=False)
        
        for i in range(50):
            wb.register_element(i, f"elem-{i}")
            la.register_element(i, f"elem-{i}")
        
        assert wb.element_count == la.element_count == 50

    def test_08_stats_structure(self):
        """Test 8: stats property estructura."""
        wb = WebBridge()
        la = LightWASMAdapter(use_light_wasm=False)
        
        wb.register_element(0, "elem-1")
        la.register_element(0, "elem-1")
        
        wb.sync([MockElement(0, 0, 10, 10)])
        la.sync([MockElement(0, 0, 10, 10)])
        
        wb_stats = wb.stats
        la_stats = la.stats
        
        assert "elements" in wb_stats
        assert "elements" in la_stats

    def test_09_get_html_id_method(self):
        """Test 9: get_html_id method existe y funciona."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        la.register_element(5, "special-id")
        
        assert la.get_html_id(5) == "special-id"
        assert la.get_html_id(999) is None

    def test_10_get_element_metadata_method(self):
        """Test 10: get_element_metadata method existe y funciona."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        la.register_element(0, "elem-1", {"tag": "span", "text": "Hello"})
        
        meta = la.get_element_metadata("elem-1")
        assert meta["tag"] == "span"
        assert meta["text"] == "Hello"


# ==============================================================================
# GRUPO 2: Performance Tests (5 tests)
# ==============================================================================

class TestM1Performance:
    """Test 11-15: Verificar rendimiento."""

    def test_11_sync_1000_elements_under_16ms(self):
        """Test 11: Sync 1000 elementos en <16ms."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        for i in range(1000):
            la.register_element(i, f"elem-{i}")
        
        elements = [MockElement(i % 1000, i % 720, 50, 30) for i in range(1000)]
        
        times = []
        for _ in range(10):
            start = time.perf_counter()
            la.sync(elements)
            times.append((time.perf_counter() - start) * 1000)
        
        avg_ms = sum(times) / len(times)
        assert avg_ms < 16.0, f"Sync took {avg_ms:.2f}ms, expected <16ms"

    def test_12_sync_5000_elements_under_50ms(self):
        """Test 12: Sync 5000 elementos en <50ms."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        for i in range(5000):
            la.register_element(i, f"elem-{i}")
        
        elements = [MockElement(i % 1280, i % 720, 20, 20) for i in range(5000)]
        
        start = time.perf_counter()
        la.sync(elements)
        elapsed = (time.perf_counter() - start) * 1000
        
        assert elapsed < 50.0, f"Sync 5000 took {elapsed:.2f}ms, expected <50ms"

    def test_13_memory_no_leak_after_1000_syncs(self):
        """Test 13: No memory leak después de 1000 syncs."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        for i in range(100):
            la.register_element(i, f"elem-{i}")
        
        elements = [MockElement(i % 500, i % 500, 30, 30) for i in range(100)]
        
        for _ in range(1000):
            la.sync(elements)
        
        assert la._sync_count == 1000
        assert len(la._element_map) == 100

    def test_14_frame_counter_increments(self):
        """Test 14: Frame counter incrementa correctamente."""
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "elem-1")
        
        elem = MockElement(10, 10, 50, 50)
        
        for i in range(100):
            la.sync([elem])
        
        assert la._sync_count == 100

    def test_15_timestamp_updated(self):
        """Test 15: Timestamp se actualiza en cada sync."""
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "elem-1")
        
        elem = MockElement(10, 10, 50, 50)
        
        t0 = la._last_sync_time
        la.sync([elem])
        t1 = la._last_sync_time
        
        assert t1 > t0


# ==============================================================================
# GRUPO 3: Edge Case Tests (5 tests)
# ==============================================================================

class TestM1EdgeCases:
    """Test 16-20: Edge cases y boundary conditions."""

    def test_16_empty_elements_sync(self):
        """Test 16: Sync con lista vacía."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        result = la.sync([])
        data = json.loads(result)
        
        assert data["elements"] == []
        assert "frame" in data
        assert "timestamp" in data

    def test_17_nan_values_excluded(self):
        """Test 17: NaN values excluded del payload."""
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "nan-elem")
        
        nan_elem = MockElement(float('nan'), 100, 50, 50)
        
        result = la.sync([nan_elem])
        data = json.loads(result)
        
        assert len(data["elements"]) == 0

    def test_18_inf_values_excluded(self):
        """Test 18: Inf values excluded del payload."""
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "inf-elem")
        
        inf_elem = MockElement(float('inf'), 100, 50, 50)
        
        result = la.sync([inf_elem])
        data = json.loads(result)
        
        assert len(data["elements"]) == 0

    def test_19_negative_coordinates_clamped(self):
        """Test 19: Negative coordinates clamping."""
        la = LightWASMAdapter(container_width=100, container_height=100, use_light_wasm=False)
        la.register_element(0, "neg-elem")
        
        neg_elem = MockElement(-50, -50, 30, 30)
        
        result = la.sync([neg_elem])
        data = json.loads(result)
        
        assert data["elements"][0]["x"] >= 0
        assert data["elements"][0]["y"] >= 0

    def test_20_out_of_bounds_clamped(self):
        """Test 20: Coordinates fuera de bounds se clamped."""
        la = LightWASMAdapter(container_width=100, container_height=100, use_light_wasm=False)
        la.register_element(0, "out-elem")
        
        out_elem = MockElement(200, 200, 50, 50)
        
        result = la.sync([out_elem])
        data = json.loads(result)
        
        elem = data["elements"][0]
        assert elem["x"] + elem["w"] <= 100.0 + 0.01
        assert elem["y"] + elem["h"] <= 100.0 + 0.01


# ==============================================================================
# EJECUCIÓN DIRECTA
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])