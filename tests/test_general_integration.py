# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
General integration tests for Aetheris architecture.

These tests verify the core engine integration with:
- Native elements registration
- Declarative API connection
- Headless bridge operation
"""
import pytest
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestEngineIntegration:
    """Test AetherEngine integration with core components."""
    
    def test_engine_initialization(self):
        """Test engine can be initialized."""
        from core.engine import AetherEngine
        
        engine = AetherEngine()
        
        assert engine is not None
        assert engine.element_count == 0
    
    def test_engine_element_registration(self):
        """Test elements can be registered to engine."""
        from core.engine import AetherEngine
        from core.elements import SmartPanel
        
        engine = AetherEngine()
        
        element = SmartPanel(x=10, y=20, w=100, h=50)
        engine.register(element)
        
        assert engine.element_count == 1
    
    def test_engine_tick_returns_numpy(self):
        """Test engine tick returns numpy array."""
        from core.engine import AetherEngine
        from core.elements import SmartPanel
        
        engine = AetherEngine()
        
        element = SmartPanel(x=0, y=0, w=100, h=50)
        engine.register(element)
        
        result = engine.tick(1280, 720)
        
        assert isinstance(result, np.ndarray)
    
    def test_engine_batch_registration(self):
        """Test batch element registration."""
        from core.engine import AetherEngine
        from core.elements import SmartPanel, StaticBox
        
        engine = AetherEngine()
        
        for i in range(10):
            element = SmartPanel(x=i*10, y=0, w=50, h=50)
            engine.register(element)
        
        assert engine.element_count == 10


class TestDeclarativeToEngineConnection:
    """Test declarative API connects properly to engine."""
    
    def test_page_registers_engine(self):
        """Test Page can register an engine."""
        from core.declarative_api import Page
        from core.engine import AetherEngine
        
        page = Page(title="Test", width=1280, height=720)
        engine = AetherEngine()
        
        page._register_engine(engine)
        
        assert page.engine is engine
    
    def test_widget_build_registers_elements(self):
        """Test widgets register elements to engine during build."""
        from core.declarative_api import Page, Text
        from core.engine import AetherEngine
        
        page = Page(title="Test", width=1280, height=720)
        engine = AetherEngine()
        page._register_engine(engine)
        
        page.add(Text("Hello World"))
        page._build()
        
        assert engine.element_count >= 1
    
    def test_column_children_layout(self):
        """Test Column computes layout for children."""
        from core.declarative_api import Column, Text
        
        col = Column(controls=[
            Text("Line 1"),
            Text("Line 2"),
        ])
        
        col._compute_layout(0, 0, 1000, 1000)
        
        assert col._computed_h > 0
        assert col._controls[0]._computed_y == 0
        assert col._controls[1]._computed_y > col._controls[0]._computed_y


class TestHeadlessBridgeIntegration:
    """Test headless bridge with engine."""
    
    def test_bridge_initialization(self):
        """Test headless bridge can be initialized."""
        from core.headless_bridge import HeadlessTextureBridge
        from core.engine import AetherEngine
        
        engine = AetherEngine()
        bridge = HeadlessTextureBridge(engine)
        
        assert bridge.engine is engine
        assert bridge.frame_width == 1280
    
    def test_bridge_frame_buffer_format(self):
        """Test bridge returns correct frame format."""
        from core.headless_bridge import HeadlessTextureBridge
        from core.engine import AetherEngine
        from core.elements import SmartPanel
        
        engine = AetherEngine()
        element = SmartPanel(x=0, y=0, w=100, h=50)
        engine.register(element)
        
        bridge = HeadlessTextureBridge(engine)
        frame = bridge.get_frame_buffer()
        
        assert frame.states.shape[1] == 11  # 11 float fields
    
    def test_bridge_tick_advances_engine(self):
        """Test bridge tick advances engine."""
        from core.headless_bridge import HeadlessTextureBridge
        from core.engine import AetherEngine
        
        engine = AetherEngine()
        bridge = HeadlessTextureBridge(engine)
        
        initial_count = engine.element_count
        
        bridge.tick()
        
        assert engine.element_count == initial_count


class TestEndToEndWorkflow:
    """Test complete workflow from declarative to render."""
    
    def test_declarative_to_headless_pipeline(self):
        """Test complete pipeline: declarative -> engine -> headless."""
        from core.declarative_api import Page, Column, Row, Container, Text
        from core.engine import AetherEngine
        from core.headless_bridge import HeadlessTextureBridge
        
        # 1. Create engine
        engine = AetherEngine()
        
        # 2. Create page with declarative API
        page = Page(title="Test App", width=1280, height=720)
        page._register_engine(engine)
        
        page.add(
            Column(controls=[
                Text("Title", size=24),
                Row(controls=[
                    Container(width=100, height=100, bgcolor=(1, 0, 0, 1)),
                    Container(width=100, height=100, bgcolor=(0, 1, 0, 1)),
                ])
            ])
        )
        
        # 3. Build declarative to native elements
        page._build()
        
        assert engine.element_count >= 3
        
        # 4. Create headless bridge
        bridge = HeadlessTextureBridge(engine)
        
        # 5. Get frame buffer
        frame = bridge.get_frame_buffer()
        
        assert frame.metadata.element_count >= 3
    
    def test_multi_frame_rendering(self):
        """Test multiple frames can be rendered."""
        from core.declarative_api import Page, Container
        from core.engine import AetherEngine
        from core.headless_bridge import HeadlessTextureBridge
        
        engine = AetherEngine()
        
        page = Page(width=1280, height=720)
        page._register_engine(engine)
        page.add(Container(width=100, height=100))
        page._build()
        
        bridge = HeadlessTextureBridge(engine)
        
        frames = []
        for _ in range(5):
            frame = bridge.get_frame_buffer()
            frames.append(frame)
            bridge.tick()
        
        assert len(frames) == 5
        assert frames[-1].metadata.frame_number == 5


class TestSecurityFeatures:
    """Test security features in integration."""
    
    def test_nan_protection_in_headless(self):
        """Test NaN values are protected in headless output."""
        from core.headless_bridge import HeadlessTextureBridge
        from core.engine import AetherEngine
        from core.elements import SmartPanel
        import json
        
        engine = AetherEngine()
        
        # Add element with potential NaN (via physics simulation)
        element = SmartPanel(x=0, y=0, w=100, h=50)
        element.tensor.state[0] = float('nan')  # Inject NaN
        engine.register(element)
        
        bridge = HeadlessTextureBridge(engine)
        frame = bridge.get_frame_buffer()
        
        # Check JSON output doesn't contain NaN
        json_output = bridge.get_json_snapshot()
        
        assert "nan" not in json_output.lower()
        assert "NaN" not in json_output
    
    def test_element_limit_enforcement(self):
        """Test element limit is enforced."""
        from core.engine import AetherEngine
        from core.elements import SmartPanel
        import os
        
        # Set limit for test
        original = os.environ.get("AETHERIS_ELEMENT_LIMIT", "false")
        os.environ["AETHERIS_ELEMENT_LIMIT"] = "true"
        os.environ["AETHERIS_MAX_ELEMENTS"] = "5"
        
        try:
            from importlib import reload
            import core.engine
            reload(core.engine)
            
            from core.engine import AetherEngine as EngineReloaded
            engine = EngineReloaded()
            
            for i in range(10):
                element = SmartPanel(x=i, y=0, w=10, h=10)
                try:
                    engine.register(element)
                except RuntimeError:
                    pass
            
            # Should be limited to 5
            assert engine.element_count <= 5
        finally:
            os.environ["AETHERIS_ELEMENT_LIMIT"] = original


if __name__ == "__main__":
    pytest.main([__file__, "-v"])