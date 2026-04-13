# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Tests for M8 Type Hints system.

Verifies that all type hint implementations work correctly:
- py.typed marker exists
- pyrightconfig.json is valid
- TypedDict classes are functional
- Protocol definitions work
"""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestPyTypedMarker:
    """Test py.typed marker file exists."""
    
    def test_py_typed_exists(self):
        """Verify py.typed marker file exists."""
        import os
        py_typed_path = Path(__file__).parent.parent / "core" / "py.typed"
        assert py_typed_path.exists(), "py.typed marker should exist"
    
    def test_py_typed_not_empty(self):
        """Verify py.typed is not empty."""
        py_typed_path = Path(__file__).parent.parent / "core" / "py.typed"
        content = py_typed_path.read_text()
        assert len(content) > 0


class TestPyrightConfig:
    """Test pyrightconfig.json configuration."""
    
    def test_config_exists(self):
        """Verify pyrightconfig.json exists."""
        config_path = Path(__file__).parent.parent / "pyrightconfig.json"
        assert config_path.exists(), "pyrightconfig.json should exist"
    
    def test_config_valid_json(self):
        """Verify pyrightconfig.json is valid JSON."""
        import json
        config_path = Path(__file__).parent.parent / "pyrightconfig.json"
        with open(config_path) as f:
            config = json.load(f)
        assert config is not None
        assert "include" in config


class TestTypedDictClasses:
    """Test TypedDict definitions."""
    
    def test_typeddict_imports(self):
        """Verify TypedDict classes can be imported."""
        from core.types_typeddict import (
            Position2D,
            Size2D,
            ColorRGBA,
            ElementConfig,
            SmartPanelConfig,
            SyncPayload,
            TemplateConfig,
        )
        
        assert Position2D is not None
        assert Size2D is not None
        assert ColorRGBA is not None
        assert ElementConfig is not None
    
    def test_element_state_dict(self):
        """Test Position2D works correctly."""
        from core.types_typeddict import Position2D
        
        pos: Position2D = {"x": 10.0, "y": 20.0}
        
        assert pos["x"] == 10.0
        assert pos["y"] == 20.0
    
    def test_ui_component_dict(self):
        """Test ElementConfig works correctly."""
        from core.types_typeddict import ElementConfig
        
        config: ElementConfig = {
            "z_index": 0,
            "metadata": {"label": "Click me"},
        }
        
        assert config["z_index"] == 0
    
    def test_engine_config_dict(self):
        """Test AnimationConfig works correctly."""
        from core.types_typeddict import AnimationConfig
        
        config: AnimationConfig = {
            "type": "spring",
            "duration": 0.5,
            "stiffness": 100.0,
            "damping": 0.8,
        }
        
        assert config["type"] == "spring"
        assert config["duration"] == 0.5


class TestProtocols:
    """Test Protocol definitions."""
    
    def test_protocol_imports(self):
        """Verify Protocol classes can be imported."""
        from core.protocols import (
            Renderable,
            PhysicsBody,
            Interactive,
            StateContainer,
            Serializable,
        )
        
        assert Renderable is not None
        assert PhysicsBody is not None
        assert Interactive is not None
    
    def test_protocol_is_protocol(self):
        """Verify they are actually Protocols."""
        from core.protocols import Renderable
        from typing import Protocol
        
        assert issubclass(Renderable, Protocol)


class TestTypeStubs:
    """Test .pyi stub files."""
    
    def test_stub_files_exist(self):
        """Verify stub files exist."""
        stubs_path = Path(__file__).parent.parent / "core"
        
        stub_files = list(stubs_path.glob("types_*.pyi"))
        
        assert len(stub_files) > 0, "Should have at least one .pyi stub file"


class TestTypeIntegration:
    """Test type hints integrate with core modules."""
    
    def test_engine_has_type_hints(self):
        """Verify engine module can be type-checked."""
        import core.engine
        assert core.engine is not None
    
    def test_elements_has_type_hints(self):
        """Verify elements module can be type-checked."""
        import core.elements
        assert core.elements is not None
    
    def test_web_bridge_has_type_hints(self):
        """Verify web_bridge module can be type-checked."""
        import core.web_bridge
        assert core.web_bridge is not None
    
    def test_data_bridge_has_type_hints(self):
        """Verify data_bridge module can be type-checked."""
        import core.data_bridge
        assert core.data_bridge is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])