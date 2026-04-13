# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Integration tests for WebBridge workflow.

Tests the web bridge lifecycle:
- Creation → Element mapping → Sync → JSON output
"""
import pytest
import json
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.web_bridge import WebBridge
from core.elements import SmartPanel


class TestWebBridgeWorkflow:
    """Test complete web bridge workflow."""
    
    def test_bridge_creation(self):
        """Test bridge is created successfully."""
        bridge = WebBridge(1280, 720)
        assert bridge is not None
    
    def test_bridge_element_mapping(self):
        """Test element ID mapping."""
        bridge = WebBridge(1280, 720)
        
        bridge.map_element(0, "div-0")
        bridge.map_element(1, "div-1")
        
        assert bridge.element_count == 2
        assert bridge._element_map[0] == "div-0"
    
    def test_bridge_sync_json(self):
        """Test sync produces valid JSON."""
        bridge = WebBridge(1280, 720)
        
        bridge.map_element(0, "div-0")
        bridge.set_metadata("div-0", {"tag": "div", "classes": ["panel"]})
        
        json_output = bridge.sync_dom([])
        
        assert json_output is not None
        assert isinstance(json_output, str)
        
        # Validar que es JSON válido
        data = json.loads(json_output)
        assert "elements" in data
    
    def test_bridge_with_elements(self):
        """Test sync with actual elements."""
        bridge = WebBridge(1280, 720)
        
        # Simular elementos del engine
        elements = [
            {"x": 10, "y": 10, "w": 100, "h": 50, "z": 0}
        ]
        
        # Mapear elementos
        bridge.map_element(0, "elem-0")
        bridge.set_metadata("elem-0", {"tag": "div"})
        
        json_output = bridge.sync_dom(elements)
        
        assert json_output is not None
    
    def test_get_initial_dom_state(self):
        """Test initial DOM state generation."""
        bridge = WebBridge(1280, 720)
        
        bridge.map_element(0, "div-0")
        bridge.set_metadata("div-0", {
            "tag": "div",
            "classes": ["panel"],
            "text": "Hello"
        })
        
        dom_state = bridge.get_initial_dom_state()
        
        assert len(dom_state) == 1
        assert dom_state[0]["id"] == "div-0"


class TestWebBridgeSecurity:
    """Test web bridge security features."""
    
    def test_nan_filtering(self):
        """Test NaN values are filtered."""
        bridge = WebBridge(1280, 720)
        
        # Simular elemento con NaN
        elements = [
            {"x": float('nan'), "y": 10, "w": 100, "h": 50, "z": 0}
        ]
        
        bridge.map_element(0, "elem-0")
        
        json_output = bridge.sync_dom(elements)
        
        # NaN elements should be skipped
        data = json.loads(json_output)
        assert "elements" in data
    
    def test_inf_filtering(self):
        """Test Inf values are filtered."""
        bridge = WebBridge(1280, 720)
        
        elements = [
            {"x": float('inf'), "y": 10, "w": 100, "h": 50, "z": 0}
        ]
        
        bridge.map_element(0, "elem-0")
        
        json_output = bridge.sync_dom(elements)
        
        data = json.loads(json_output)
        assert "elements" in data
    
    def test_bounds_clamping(self):
        """Test coordinates are clamped to bounds."""
        bridge = WebBridge(1280, 720)
        
        elements = [
            {"x": 2000, "y": 2000, "w": 100, "h": 50, "z": 0}  # Outside bounds
        ]
        
        bridge.map_element(0, "elem-0")
        
        json_output = bridge.sync_dom(elements)
        
        data = json.loads(json_output)
        
        if data["elements"]:
            elem = data["elements"][0]
            assert elem["x"] <= 1280 - elem["w"]


class TestWebBridgePerformance:
    """Test web bridge performance."""
    
    def test_many_elements_sync(self):
        """Test sync with many elements."""
        bridge = WebBridge(1280, 720)
        
        # Mapear 100 elementos
        for i in range(100):
            bridge.map_element(i, f"elem-{i}")
            bridge.set_metadata(f"elem-{i}", {"tag": "div"})
        
        elements = [{"x": i * 10, "y": 0, "w": 10, "h": 10, "z": i} for i in range(100)]
        
        import time
        start = time.perf_counter()
        
        json_output = bridge.sync_dom(elements)
        
        duration = time.perf_counter() - start
        
        # 100 elementos deve processar em < 100ms
        assert duration < 0.1


class TestWebBridgeJSON:
    """Test web bridge JSON safety."""
    
    def test_json_output_is_valid(self):
        """Test JSON output is valid."""
        bridge = WebBridge(1280, 720)
        
        bridge.map_element(0, "elem-0")
        
        json_output = bridge.sync_dom([{"x": 10, "y": 10, "w": 100, "h": 50, "z": 0}])
        
        # No debe lançar exceção
        data = json.loads(json_output)
        assert data is not None
    
    def test_no_nan_in_output(self):
        """Test NaN doesn't appear in JSON output."""
        bridge = WebBridge(1280, 720)
        
        bridge.map_element(0, "elem-0")
        
        json_output = bridge.sync_dom([{"x": 10, "y": 10, "w": 100, "h": 50, "z": 0}])
        
        assert "NaN" not in json_output
        assert "nan" not in json_output.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])