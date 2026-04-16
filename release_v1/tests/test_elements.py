import pytest
import numpy as np
from core.elements import DifferentialElement, StaticBox
from core.aether_math import StateTensor


def test_differential_element_abstract():
    """Test that DifferentialElement cannot be instantiated directly."""
    with pytest.raises(TypeError):
        # This should fail because DifferentialElement is abstract
        DifferentialElement(0, 0, 50, 50)


def test_static_box_asymptotes():
    """Test that StaticBox correctly reports its fixed asymptotes."""
    # Create a static box at position (10, 20) with size (100, 50)
    box = StaticBox(10, 20, 100, 50)
    
    # The asymptote should always be the target rectangle regardless of container size
    asymptote_small = box.calculate_asymptotes(800, 600)
    asymptote_large = box.calculate_asymptotes(1920, 1080)
    
    expected = np.array([10, 20, 100, 50], dtype=np.float32)
    
    np.testing.assert_array_equal(asymptote_small, expected)
    np.testing.assert_array_equal(asymptote_large, expected)


def test_static_box_state_separation():
    """Test that changing StaticBox tensor state doesn't change its asymptote."""
    box = StaticBox(10, 20, 100, 50)
    
    # Verify initial state matches target
    assert np.array_equal(box.tensor.state, np.array([10, 20, 100, 50], dtype=np.float32))
    
    # Change the current state (simulate physics movement)
    box.tensor.state = np.array([50, 60, 80, 40], dtype=np.float32)
    
    # The asymptote should remain unchanged
    asymptote = box.calculate_asymptotes(800, 600)
    expected = np.array([10, 20, 100, 50], dtype=np.float32)
    
    np.testing.assert_array_equal(asymptote, expected)
    
    # Verify that the tensor state actually changed
    assert np.array_equal(box.tensor.state, np.array([50, 60, 80, 40], dtype=np.float32))
    assert not np.array_equal(box.tensor.state, asymptote)


def test_static_box_rendering_data():
    """Test that StaticBox rendering_data property works correctly."""
    box = StaticBox(5, 15, 30, 40, color=(0.5, 0.6, 0.7, 0.8), z=5)
    
    # Check initial rendering data
    data = box.rendering_data
    assert np.array_equal(data["rect"], np.array([5, 15, 30, 40], dtype=np.float32))
    assert np.array_equal(data["color"], np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float32))
    assert data["z"] == 5
    
    # Change tensor state and verify rendering data updates
    box.tensor.state = np.array([10, 20, 40, 50], dtype=np.float32)
    data = box.rendering_data
    assert np.array_equal(data["rect"], np.array([10, 20, 40, 50], dtype=np.float32))
    assert np.array_equal(data["color"], np.array([0.5, 0.6, 0.7, 0.8], dtype=np.float32))
    assert data["z"] == 5