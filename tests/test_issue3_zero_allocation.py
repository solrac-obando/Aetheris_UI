"""
Issue 3 Validation Tests: Zero-Allocation Tick
Tests that verify the direct property access (rect, color, z_index)
eliminates per-frame dict allocations in the tick loop.
"""
import pytest
import numpy as np
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel, SmartButton, DifferentialElement
from core.aether_math import StateTensor


class TestDirectPropertyAccess:
    """Test that direct properties (rect, color, z_index) work correctly."""

    def test_rect_property_returns_state_tensor(self):
        """Verify rect property returns reference to StateTensor.state."""
        box = StaticBox(10, 20, 100, 50)
        rect = box.rect
        assert isinstance(rect, np.ndarray)
        assert rect.dtype == np.float32
        np.testing.assert_array_equal(rect, np.array([10, 20, 100, 50], dtype=np.float32))

    def test_color_property_returns_numpy_array(self):
        """Verify color property returns reference to internal color array."""
        box = StaticBox(0, 0, 50, 50, color=(0.1, 0.2, 0.3, 0.4))
        color = box.color
        assert isinstance(color, np.ndarray)
        assert color.dtype == np.float32
        np.testing.assert_array_equal(color, np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32))

    def test_z_index_property_returns_int(self):
        """Verify z_index property returns integer."""
        box = StaticBox(0, 0, 50, 50, z=5)
        assert box.z_index == 5

    def test_rect_is_live_reference(self):
        """Verify rect property is a live reference to the state, not a copy."""
        box = StaticBox(10, 20, 100, 50)
        rect = box.rect
        rect[0] = 999
        assert box.tensor.state[0] == 999

    def test_color_is_live_reference(self):
        """Verify color property is a live reference, not a copy."""
        box = StaticBox(0, 0, 50, 50, color=(0.1, 0.2, 0.3, 0.4))
        color = box.color
        color[0] = np.float32(0.9)
        assert box._color[0] == pytest.approx(0.9)


class TestEngineZeroAllocation:
    """Test that engine uses direct properties for zero-allocation."""

    def test_engine_extracts_rect_via_property(self):
        """Verify engine extracts rect via direct property."""
        engine = AetherEngine()
        box = StaticBox(10, 20, 30, 40, color=(0.5, 0.6, 0.7, 0.8), z=3)
        engine.register_element(box)
        data = engine.tick(800, 600)
        np.testing.assert_array_equal(data[0]['rect'], np.array([10, 20, 30, 40], dtype=np.float32))

    def test_engine_extracts_color_via_property(self):
        """Verify engine extracts color via direct property."""
        engine = AetherEngine()
        box = StaticBox(0, 0, 50, 50, color=(0.1, 0.2, 0.3, 0.4))
        engine.register_element(box)
        data = engine.tick(800, 600)
        np.testing.assert_array_almost_equal(data[0]['color'], np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32))

    def test_engine_extracts_z_index_via_property(self):
        """Verify engine extracts z_index via direct property."""
        engine = AetherEngine()
        box = StaticBox(0, 0, 50, 50, z=7)
        engine.register_element(box)
        data = engine.tick(800, 600)
        assert data[0]['z'] == 7

    def test_engine_multiple_elements_properties(self):
        """Verify engine handles multiple elements with direct properties."""
        engine = AetherEngine()
        box1 = StaticBox(10, 20, 30, 40, z=1)
        box2 = StaticBox(50, 60, 70, 80, z=2)
        engine.register_element(box1)
        engine.register_element(box2)
        data = engine.tick(800, 600)
        assert len(data) == 2
        np.testing.assert_array_equal(data[0]['rect'], np.array([10, 20, 30, 40], dtype=np.float32))
        np.testing.assert_array_equal(data[1]['rect'], np.array([50, 60, 70, 80], dtype=np.float32))

    def test_engine_updates_state_across_ticks(self):
        """Verify engine correctly tracks state changes across ticks."""
        engine = AetherEngine()
        box = StaticBox(0, 0, 50, 50)
        engine.register_element(box)
        engine.tick(800, 600)
        box.tensor.state = np.array([100, 200, 300, 400], dtype=np.float32)
        data = engine.tick(800, 600)
        np.testing.assert_array_equal(data[0]['rect'], np.array([100, 200, 300, 400], dtype=np.float32))


class TestBackwardCompatibility:
    """Verify backward compatibility with rendering_data property."""

    def test_rendering_data_still_works(self):
        """Verify rendering_data dict property still works for existing code."""
        box = StaticBox(10, 20, 30, 40, color=(0.5, 0.6, 0.7, 0.8), z=3)
        r_data = box.rendering_data
        assert isinstance(r_data, dict)
        np.testing.assert_array_equal(r_data['rect'], np.array([10, 20, 30, 40], dtype=np.float32))
        np.testing.assert_array_equal(r_data['color'], np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float32))
        assert r_data['z'] == 3

    def test_rendering_data_returns_current_state(self):
        """Verify rendering_data reflects current tensor state."""
        box = StaticBox(10, 20, 30, 40)
        box.tensor.state = np.array([50, 60, 70, 80], dtype=np.float32)
        r_data = box.rendering_data
        np.testing.assert_array_equal(r_data['rect'], np.array([50, 60, 70, 80], dtype=np.float32))


class TestSmartPanelProperties:
    """Test that SmartPanel also supports direct properties."""

    def test_smart_panel_rect_property(self):
        """Verify SmartPanel has rect property."""
        panel = SmartPanel()
        rect = panel.rect
        assert isinstance(rect, np.ndarray)
        assert rect.shape == (4,)

    def test_smart_panel_color_property(self):
        """Verify SmartPanel has color property."""
        panel = SmartPanel()
        color = panel.color
        assert isinstance(color, np.ndarray)
        assert color.shape == (4,)

    def test_smart_panel_z_index_property(self):
        """Verify SmartPanel has z_index property."""
        panel = SmartPanel()
        assert isinstance(panel.z_index, int)
