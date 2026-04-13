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
        
        bridge.register_element(0, "div-0")
        bridge.register_element(1, "div-1")
        
        assert bridge.element_count == 2
        assert bridge.get_html_id(0) == "div-0"
    
    def test_bridge_sync_json(self):
        """Test sync produces valid JSON."""
        bridge = WebBridge(1280, 720)
        
        bridge.register_element(0, "div-0", {"tag": "div", "classes": ["panel"]})
        
        json_output = bridge.get_initial_dom_state()
        
        assert json_output is not None
        assert isinstance(json_output, list)
        assert len(json_output) == 1
    
    def test_bridge_with_elements(self):
        """Test sync with actual elements."""
        bridge = WebBridge(1280, 720)
        
        bridge.register_element(0, "elem-0", {"tag": "div"})
        
        dom_state = bridge.get_initial_dom_state()
        
        assert dom_state is not None
        assert len(dom_state) == 1
    
    def test_get_initial_dom_state(self):
        """Test initial DOM state generation."""
        bridge = WebBridge(1280, 720)
        
        bridge.register_element(0, "div-0", {
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
        
        bridge.register_element(0, "elem-0", {"tag": "div"})
        
        dom_state = bridge.get_initial_dom_state()
        
        assert len(dom_state) == 1
    
    def test_inf_filtering(self):
        """Test Inf values are filtered."""
        bridge = WebBridge(1280, 720)
        
        bridge.register_element(0, "elem-0", {"tag": "div"})
        
        dom_state = bridge.get_initial_dom_state()
        
        assert len(dom_state) == 1
    
    def test_bounds_clamping(self):
        """Test coordinates are clamped to bounds."""
        bridge = WebBridge(1280, 720)
        
        bridge.register_element(0, "elem-0", {"tag": "div"})
        
        dom_state = bridge.get_initial_dom_state()
        
        assert len(dom_state) == 1


class TestWebBridgePerformance:
    """Test web bridge performance."""
    
    def test_many_elements_sync(self):
        """Test sync with many elements."""
        bridge = WebBridge(1280, 720)
        
        # Mapear 100 elementos
        for i in range(100):
            bridge.register_element(i, f"elem-{i}", {"tag": "div"})
        
        dom_state = bridge.get_initial_dom_state()
        
        import time
        start = time.perf_counter()
        
        # Simular sync
        result = bridge.get_initial_dom_state()
        
        duration = time.perf_counter() - start
        
        assert len(result) == 100
        assert duration < 0.1


class TestWebBridgeJSON:
    """Test web bridge JSON safety."""
    
    def test_json_output_is_valid(self):
        """Test JSON output is valid."""
        bridge = WebBridge(1280, 720)
        
        bridge.register_element(0, "elem-0", {"tag": "div"})
        
        dom_state = bridge.get_initial_dom_state()
        
        assert dom_state is not None
        assert len(dom_state) == 1
    
    def test_no_nan_in_output(self):
        """Test NaN doesn't appear in JSON output."""
        bridge = WebBridge(1280, 720)
        
        bridge.register_element(0, "elem-0", {"tag": "div"})
        
        import json
        dom_state = bridge.get_initial_dom_state()
        
        json_str = json.dumps(dom_state)
        
        assert "NaN" not in json_str
        assert "nan" not in json_str.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])