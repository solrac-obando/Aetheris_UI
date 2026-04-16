"""
Tests for WASM/Pyodide compatibility.
Verifies that the engine works correctly when Numba is unavailable,
ensuring the Structured NumPy Array bridge produces correct output.
"""
import pytest
import numpy as np
import sys
from unittest.mock import patch, MagicMock


def test_solver_bridge_without_numba():
    """Test that solver_bridge falls back to pure NumPy when Numba is unavailable."""
    # Import the bridge module
    from core import solver_bridge
    
    # The bridge should have loaded successfully
    assert hasattr(solver_bridge, 'calculate_restoring_force')
    assert hasattr(solver_bridge, 'calculate_boundary_forces')
    assert hasattr(solver_bridge, 'HAS_NUMBA')
    
    # Test that functions work correctly
    current = np.array([0.0, 0.0, 100.0, 100.0], dtype=np.float32)
    target = np.array([40.0, 30.0, 720.0, 540.0], dtype=np.float32)
    
    force = solver_bridge.calculate_restoring_force(current, target, 0.1)
    
    assert force.dtype == np.float32
    assert force.shape == (4,)
    # F = (target - current) * k
    assert force[0] == pytest.approx(4.0, abs=1e-5)   # (40-0) * 0.1
    assert force[1] == pytest.approx(3.0, abs=1e-5)   # (30-0) * 0.1
    assert force[2] == pytest.approx(62.0, abs=1e-5)  # (720-100) * 0.1
    assert force[3] == pytest.approx(44.0, abs=1e-5)  # (540-100) * 0.1


def test_boundary_forces_without_numba():
    """Test boundary forces work without Numba."""
    from core import solver_bridge
    
    # Test left boundary violation
    state = np.array([-10.0, 0.0, 100.0, 100.0], dtype=np.float32)
    force = solver_bridge.calculate_boundary_forces(state, 800, 600, 0.5)
    assert force[0] > 0  # Should push right
    assert force.dtype == np.float32
    
    # Test right boundary violation
    state = np.array([750.0, 0.0, 100.0, 100.0], dtype=np.float32)  # x+w = 850 > 800
    force = solver_bridge.calculate_boundary_forces(state, 800, 600, 0.5)
    assert force[0] < 0  # Should push left
    
    # Test no boundary violation
    state = np.array([100.0, 100.0, 100.0, 100.0], dtype=np.float32)
    force = solver_bridge.calculate_boundary_forces(state, 800, 600, 0.5)
    assert np.allclose(force, 0.0)


def test_lerp_without_numba():
    """Test linear interpolation works without Numba."""
    from core.state_manager import StateManager
    
    sm = StateManager()
    a = np.array([0.0, 0.0, 100.0, 100.0], dtype=np.float32)
    b = np.array([40.0, 30.0, 720.0, 540.0], dtype=np.float32)
    
    result = sm.lerp_arrays(a, b, 0.5)
    
    assert result.dtype == np.float32
    assert result[0] == pytest.approx(20.0, abs=1e-5)
    assert result[1] == pytest.approx(15.0, abs=1e-5)
    assert result[2] == pytest.approx(410.0, abs=1e-5)
    assert result[3] == pytest.approx(320.0, abs=1e-5)


def test_speed_to_stiffness_without_numba():
    """Test stiffness derivation works without Numba."""
    from core.tensor_compiler import TensorCompiler
    
    compiler = TensorCompiler()
    
    # Test with explicit transition speed
    intent = {
        "layout": "column",
        "animation": "organic",
        "transition_speed_ms": 300,
    }
    
    coefficients = compiler.compile_intent(intent)
    
    assert coefficients[0]['stiffness'] > 0
    assert coefficients[0]['viscosity'] > 0
    assert coefficients[0]['stiffness'] < 10000.0  # Should be capped


def test_engine_works_without_numba():
    """Test that AetherEngine runs correctly regardless of Numba availability."""
    from core.engine import AetherEngine
    from core.elements import StaticBox, SmartPanel
    
    engine = AetherEngine()
    
    # Register elements
    box = StaticBox(50, 50, 100, 80, color=(0.2, 0.6, 0.9, 1.0), z=0)
    panel = SmartPanel(color=(0.9, 0.2, 0.6, 0.8), z=1)
    
    engine.register_element(box)
    engine.register_element(panel)
    
    # Run multiple ticks
    for _ in range(10):
        data = engine.tick(800, 600)
        
        # Verify structured array format
        assert data.dtype == np.dtype([('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])
        assert len(data) == 2
        
        # Verify no NaN or infinity
        for elem_data in data:
            rect = elem_data['rect']
            color = elem_data['color']
            z = elem_data['z']
            
            assert not np.any(np.isnan(rect))
            assert not np.any(np.isinf(rect))
            assert not np.any(np.isnan(color))
            assert not np.any(np.isinf(color))
            assert isinstance(z, (int, np.integer))


def test_structured_array_bridge_for_webgl():
    """
    Test that the structured NumPy array format is compatible with WebGL rendering.
    
    In the browser, Pyodide's NumPy arrays can be converted to JavaScript TypedArrays
    for WebGL vertex buffer uploads. This test verifies the format is correct.
    """
    from core.engine import AetherEngine
    from core.elements import StaticBox
    
    engine = AetherEngine()
    box = StaticBox(10, 20, 50, 60, color=(1.0, 0.5, 0.0, 1.0), z=5)
    engine.register_element(box)
    
    data = engine.tick(800, 600)
    
    # Verify the exact dtype structure expected by WebGL shaders
    expected_dtype = np.dtype([('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])
    assert data.dtype == expected_dtype
    
    # Verify individual field sizes (important for WebGL attribute offsets)
    assert data.dtype['rect'].itemsize == 16  # 4 floats * 4 bytes
    assert data.dtype['color'].itemsize == 16  # 4 floats * 4 bytes
    assert data.dtype['z'].itemsize == 4  # 1 int * 4 bytes
    
    # Verify first element values
    assert data[0]['rect'][0] == pytest.approx(10.0, abs=1.0)
    assert data[0]['rect'][1] == pytest.approx(20.0, abs=1.0)
    assert data[0]['rect'][2] == pytest.approx(50.0, abs=1.0)
    assert data[0]['rect'][3] == pytest.approx(60.0, abs=1.0)
    
    assert data[0]['color'][0] == pytest.approx(1.0, abs=1e-5)
    assert data[0]['color'][1] == pytest.approx(0.5, abs=1e-5)
    assert data[0]['color'][2] == pytest.approx(0.0, abs=1e-5)
    assert data[0]['color'][3] == pytest.approx(1.0, abs=1e-5)
    
    assert data[0]['z'] == 5


def test_tensor_compiler_wasm_compatibility():
    """Test TensorCompiler works without Numba optimizations."""
    from core.tensor_compiler import TensorCompiler, HAS_NUMBA
    
    compiler = TensorCompiler()
    
    # Complex intent with multiple elements
    intent = {
        "layout": "grid",
        "spacing": 20,
        "animation": "snappy",
        "padding": [10, 20, 10, 20],
        "transition_speed_ms": 250,
        "elements": [
            {"id": "header", "animation": "rigid"},
            {"id": "content", "animation": "fluid"},
            {"id": "footer", "stiffness": 0.3, "viscosity": 0.6},
        ]
    }
    
    coefficients = compiler.compile_intent(intent)
    
    assert len(coefficients) == 3
    assert str(coefficients[0]['element_id']).strip() == "header"
    assert str(coefficients[1]['element_id']).strip() == "content"
    assert str(coefficients[2]['element_id']).strip() == "footer"
    
    # All values should be valid float32
    for coeff in coefficients:
        assert np.isfinite(coeff['stiffness'])
        assert np.isfinite(coeff['viscosity'])
        assert np.all(np.isfinite(coeff['boundary_padding']))
        assert np.isfinite(coeff['spacing'])
