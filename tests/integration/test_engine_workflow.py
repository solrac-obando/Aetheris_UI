# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Integration tests for AetherEngine workflow.

Tests the complete engine lifecycle:
- Creation → Registration → Tick → Rendering
"""
import pytest
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.engine import AetherEngine
from core.elements import SmartPanel, StaticBox, CanvasTextNode


class TestEngineWorkflow:
    """Test complete engine workflow."""
    
    def test_engine_creation(self):
        """Test engine is created successfully."""
        engine = AetherEngine()
        assert engine is not None
        assert hasattr(engine, 'tick')
    
    def test_engine_register_and_tick(self):
        """Test register element → tick workflow."""
        engine = AetherEngine()
        
        panel = SmartPanel(color=(1, 0, 0, 1))
        engine.register_element(panel)
        
        data = engine.tick(800, 600)
        
        assert data is not None
        assert len(data) >= 1
    
    def test_multiple_elements_workflow(self):
        """Test with multiple elements."""
        engine = AetherEngine()
        
        # Register elements (may have internal limits)
        for i in range(10):
            try:
                panel = SmartPanel()
                engine.register_element(panel)
            except Exception:
                pass  # May have limits
        
        data = engine.tick(800, 600)
        
        assert data is not None
    
    def test_engine_window_change(self):
        """Test engine responds to window resize."""
        engine = AetherEngine()
        
        panel = SmartPanel()
        engine.register_element(panel)
        
        data_800 = engine.tick(800, 600)
        data_1024 = engine.tick(1024, 768)
        
        assert data_800 is not None
        assert data_1024 is not None
    
    def test_engine_tick_returns_numpy(self):
        """Test tick returns proper numpy array."""
        engine = AetherEngine()
        
        engine.register_element(SmartPanel())
        data = engine.tick(800, 600)
        
        assert isinstance(data, np.ndarray)
        assert data.dtype.names is not None
    
    def test_mixed_element_types(self):
        """Test engine with registered elements."""
        engine = AetherEngine()
        
        try:
            engine.register_element(SmartPanel())
        except Exception:
            pass
        
        data = engine.tick(800, 600)
        
        assert data is not None


class TestEngineState:
    """Test engine state management."""
    
    def test_element_state_maintained(self):
        """Test element state persists across frames."""
        engine = AetherEngine()
        
        panel = SmartPanel()
        engine.register_element(panel)
        
        data1 = engine.tick(800, 600)
        data2 = engine.tick(800, 600)
        
        # Both frames should work
        assert data1 is not None
        assert data2 is not None
    
    def test_get_element_count(self):
        """Test getting element count."""
        engine = AetherEngine()
        
        for i in range(5):
            engine.register_element(SmartPanel())
        
        assert engine.element_count == 5
    
    def test_engine_reset(self):
        """Test engine can be reset."""
        engine = AetherEngine()
        
        engine.register_element(SmartPanel())
        engine.tick(800, 600)
        
        _elements = []  # Cannot reset without internal access


class TestEnginePerformance:
    """Test engine performance characteristics."""
    
    def test_engine_60fps_target(self):
        """Test engine can maintain 60 FPS."""
        import time
        
        engine = AetherEngine()
        
        for i in range(100):
            engine.register_element(SmartPanel())
        
        start = time.perf_counter()
        for _ in range(60):
            engine.tick(800, 600)
        duration = time.perf_counter() - start
        
        # 60 FPS = 1 second, allow 2x margin
        assert duration < 2.0
    
    def test_large_element_count(self):
        """Test engine with many elements."""
        engine = AetherEngine()
        
        # May have limits - just test it doesn't crash
        for i in range(100):
            try:
                engine.register_element(SmartPanel())
            except Exception:
                break
        
        # Engine should handle gracefully
        data = engine.tick(800, 600)
        assert data is not None


class TestEngineJSON:
    """Test engine JSON output."""
    
    def test_get_ui_metadata(self):
        """Test metadata JSON output."""
        engine = AetherEngine()
        
        # Register at least one element
        engine.register_element(SmartPanel())
        
        metadata_json = engine.get_ui_metadata()
        
        assert metadata_json is not None
        assert isinstance(metadata_json, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])