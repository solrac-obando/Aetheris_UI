import pytest
import numpy as np
from core.renderer_base import BaseRenderer, MockRenderer, pixel_to_ndc


def test_base_renderer_abstract():
    """Test that BaseRenderer cannot be instantiated directly."""
    with pytest.raises(TypeError):
        # This should fail because BaseRenderer is abstract
        BaseRenderer()


def test_mock_renderer_basic():
    """Test that MockRenderer can be instantiated and used."""
    renderer = MockRenderer()
    
    # Should be able to initialize window
    renderer.init_window(800, 600, "Test Window")
    assert renderer.width == 800
    assert renderer.height == 600
    assert renderer.title == "Test Window"
    
    # Should be able to clear screen
    renderer.clear_screen((0.1, 0.2, 0.3, 1.0))
    
    # Should be able to swap buffers
    renderer.swap_buffers()


def test_mock_renderer_render_frame():
    """Test that MockRenderer correctly processes structured data."""
    renderer = MockRenderer()
    renderer.init_window(800, 600)
    
    # Create a test structured array with 3 elements
    dtype = [('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')]
    data = np.zeros(3, dtype=dtype)
    
    # Element 1: Red square at position (10, 20) size (50, 50)
    data[0]['rect'] = np.array([10.0, 20.0, 50.0, 50.0], dtype=np.float32)
    data[0]['color'] = np.array([1.0, 0.0, 0.0, 1.0], dtype=np.float32)
    data[0]['z'] = 0
    
    # Element 2: Green rectangle at (100, 50) size (30, 80)
    data[1]['rect'] = np.array([100.0, 50.0, 30.0, 80.0], dtype=np.float32)
    data[1]['color'] = np.array([0.0, 1.0, 0.0, 1.0], dtype=np.float32)
    data[1]['z'] = 1
    
    # Element 3: Blue rectangle at (200, 150) size (60, 40)
    data[2]['rect'] = np.array([200.0, 150.0, 60.0, 40.0], dtype=np.float32)
    data[2]['color'] = np.array([0.0, 0.0, 1.0, 1.0], dtype=np.float32)
    data[2]['z'] = 2
    
    # This should not raise an exception
    renderer.render_frame(data)
    
    # Test with empty array
    empty_data = np.zeros(0, dtype=dtype)
    renderer.render_frame(empty_data)  # Should not raise


def test_coordinate_mapping():
    """Test the pixel to NDC coordinate transformation formula."""
    # Test case 1: Center of 800x600 window should map to (0, 0) in NDC
    ndc_x, ndc_y = pixel_to_ndc(400.0, 300.0, 800.0, 600.0)
    assert ndc_x == pytest.approx(0.0, abs=1e-6)
    assert ndc_y == pytest.approx(0.0, abs=1e-6)
    
    # Test case 2: Top-left corner (0, 0) should map to (-1, 1) in NDC
    ndc_x, ndc_y = pixel_to_ndc(0.0, 0.0, 800.0, 600.0)
    assert ndc_x == pytest.approx(-1.0, abs=1e-6)
    assert ndc_y == pytest.approx(1.0, abs=1e-6)
    
    # Test case 3: Bottom-right corner (800, 600) should map to (1, -1) in NDC
    ndc_x, ndc_y = pixel_to_ndc(800.0, 600.0, 800.0, 600.0)
    assert ndc_x == pytest.approx(1.0, abs=1e-6)
    assert ndc_y == pytest.approx(-1.0, abs=1e-6)
    
    # Test case 4: Center of 1024x768 window
    ndc_x, ndc_y = pixel_to_ndc(512.0, 384.0, 1024.0, 768.0)
    assert ndc_x == pytest.approx(0.0, abs=1e-6)
    assert ndc_y == pytest.approx(0.0, abs=1e-6)
    
    # Test case 5: Arbitrary point
    ndc_x, ndc_y = pixel_to_ndc(100.0, 200.0, 800.0, 600.0)
    expected_x = (2.0 * 100.0 / 800.0) - 1.0  # 0.25 - 1.0 = -0.75
    expected_y = 1.0 - (2.0 * 200.0 / 600.0)  # 1.0 - 0.666... = 0.333...
    assert ndc_x == pytest.approx(expected_x, abs=1e-6)
    assert ndc_y == pytest.approx(expected_y, abs=1e-6)


def test_coordinate_mapping_generalization():
    """Test that the coordinate mapping works for any window size (Traslación de Ejes)."""
    # The formula should work for any positive width and height
    test_cases = [
        (100, 100),
        (800, 600),
        (1024, 768),
        (1920, 1080),
        (3840, 2160),  # 4K
    ]
    
    for width, height in test_cases:
        # Center point should always map to (0, 0)
        ndc_x, ndc_y = pixel_to_ndc(width / 2, height / 2, width, height)
        assert ndc_x == pytest.approx(0.0, abs=1e-6)
        assert ndc_y == pytest.approx(0.0, abs=1e-6)
        
        # Corners should map correctly
        ndc_x, ndc_y = pixel_to_ndc(0, 0, width, height)
        assert ndc_x == pytest.approx(-1.0, abs=1e-6)
        assert ndc_y == pytest.approx(1.0, abs=1e-6)
        
        ndc_x, ndc_y = pixel_to_ndc(width, height, width, height)
        assert ndc_x == pytest.approx(1.0, abs=1e-6)
        assert ndc_y == pytest.approx(-1.0, abs=1e-6)