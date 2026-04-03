"""
Tests for the mathematical core: safe_divide, clamp_magnitude, and NaN guard.
"""
import pytest
import numpy as np
from core.aether_math import (
    safe_divide, clamp_magnitude, check_and_fix_nan,
    StateTensor, EPSILON, MAX_VELOCITY, MAX_ACCELERATION
)


class TestSafeDivide:
    """Tests for the epsilon-protected safe_divide function."""

    def test_normal_division(self):
        """Test standard division works correctly."""
        result = safe_divide(10.0, 2.0)
        assert result == pytest.approx(5.0, abs=1e-6)

    def test_division_by_zero(self):
        """Test that division by zero returns a large finite value, not inf."""
        result = safe_divide(1.0, 0.0)
        assert not np.isinf(result)
        assert not np.isnan(result)
        # Should be approximately 1.0 / EPSILON
        assert result == pytest.approx(1.0 / float(EPSILON), rel=1e-3)

    def test_division_by_tiny_number(self):
        """Test division by a number smaller than epsilon."""
        result = safe_divide(1.0, 1e-15)
        assert not np.isinf(result)
        assert not np.isnan(result)

    def test_preserves_positive_sign(self):
        """Test that positive denominator preserves sign."""
        result = safe_divide(5.0, 2.0)
        assert result > 0

    def test_preserves_negative_sign(self):
        """Test that negative denominator flips sign correctly."""
        result = safe_divide(5.0, -2.0)
        assert result < 0
        assert result == pytest.approx(-2.5, abs=1e-6)

    def test_negative_numerator(self):
        """Test negative numerator with positive denominator."""
        result = safe_divide(-5.0, 2.0)
        assert result == pytest.approx(-2.5, abs=1e-6)

    def test_array_division(self):
        """Test safe division with numpy arrays."""
        num = np.array([10.0, 0.0, -5.0], dtype=np.float32)
        den = np.array([2.0, 0.0, 1.0], dtype=np.float32)
        result = safe_divide(num, den)
        assert result[0] == pytest.approx(5.0, abs=1e-5)
        assert not np.isinf(result[1])  # 0/0 should not be inf
        assert result[2] == pytest.approx(-5.0, abs=1e-5)

    def test_zero_divided_by_zero(self):
        """Test 0/0 returns 0 (not NaN)."""
        result = safe_divide(0.0, 0.0)
        assert result == 0.0 or not np.isnan(result)


class TestClampMagnitude:
    """Tests for L2 Norm vector clamping."""

    def test_no_clamping_needed(self):
        """Test that vectors below threshold are unchanged."""
        v = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        result = clamp_magnitude(v, 100.0)
        np.testing.assert_array_almost_equal(result, v, decimal=5)

    def test_clamping_preserves_direction(self):
        """Test that clamped vector points in the same direction."""
        v = np.array([3000.0, 4000.0, 0.0, 0.0], dtype=np.float32)
        max_val = 1000.0
        result = clamp_magnitude(v, max_val)
        
        # Magnitude should be exactly max_val
        mag = np.linalg.norm(result)
        assert mag == pytest.approx(max_val, rel=1e-5)
        
        # Direction should be preserved: result / v should be constant
        ratio_0 = result[0] / v[0]
        ratio_1 = result[1] / v[1]
        assert ratio_0 == pytest.approx(ratio_1, rel=1e-5)

    def test_clamping_at_boundary(self):
        """Test vector exactly at threshold is unchanged."""
        v = np.array([3.0, 4.0, 0.0, 0.0], dtype=np.float32)  # ||v|| = 5.0
        result = clamp_magnitude(v, 5.0)
        np.testing.assert_array_almost_equal(result, v, decimal=5)

    def test_zero_vector(self):
        """Test that zero vector is handled without division by zero."""
        v = np.zeros(4, dtype=np.float32)
        result = clamp_magnitude(v, 100.0)
        np.testing.assert_array_equal(result, v)

    def test_single_component_vector(self):
        """Test clamping a vector with only one non-zero component."""
        v = np.array([10000.0, 0.0, 0.0, 0.0], dtype=np.float32)
        result = clamp_magnitude(v, MAX_VELOCITY)
        assert result[0] == pytest.approx(MAX_VELOCITY, rel=1e-5)
        assert result[1] == 0.0
        assert result[2] == 0.0
        assert result[3] == 0.0


class TestNaNGuard:
    """Tests for NaN/Inf detection and recovery."""

    def test_clean_array_unchanged(self):
        """Test that clean arrays pass through unchanged."""
        arr = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
        result = check_and_fix_nan(arr, "test")
        np.testing.assert_array_equal(result, arr)

    def test_nan_detected_and_reset(self):
        """Test that NaN values trigger reset to zero."""
        arr = np.array([1.0, np.nan, 3.0, 4.0], dtype=np.float32)
        with pytest.warns(RuntimeWarning, match="NaN/Inf detected"):
            result = check_and_fix_nan(arr, "test_tensor")
        np.testing.assert_array_equal(result, np.zeros(4, dtype=np.float32))

    def test_inf_detected_and_reset(self):
        """Test that Inf values trigger reset to zero."""
        arr = np.array([1.0, np.inf, 3.0, 4.0], dtype=np.float32)
        with pytest.warns(RuntimeWarning, match="NaN/Inf detected"):
            result = check_and_fix_nan(arr, "test_tensor")
        np.testing.assert_array_equal(result, np.zeros(4, dtype=np.float32))

    def test_negative_inf_detected(self):
        """Test that -Inf values trigger reset to zero."""
        arr = np.array([1.0, -np.inf, 3.0, 4.0], dtype=np.float32)
        with pytest.warns(RuntimeWarning, match="NaN/Inf detected"):
            result = check_and_fix_nan(arr, "test_tensor")
        np.testing.assert_array_equal(result, np.zeros(4, dtype=np.float32))

    def test_preserves_dtype(self):
        """Test that reset array preserves the original dtype."""
        arr = np.array([np.nan, 2.0, 3.0, 4.0], dtype=np.float32)
        with pytest.warns(RuntimeWarning):
            result = check_and_fix_nan(arr, "test")
        assert result.dtype == np.float32


class TestStateTensorSafety:
    """Tests for StateTensor integration with Aether-Guard."""

    def test_acceleration_clamping(self):
        """Test that apply_force clamps acceleration to MAX_ACCELERATION."""
        tensor = StateTensor(0, 0, 100, 100)
        huge_force = np.array([50000.0, 0.0, 0.0, 0.0], dtype=np.float32)
        tensor.apply_force(huge_force)
        
        mag = np.linalg.norm(tensor.acceleration)
        assert mag <= MAX_ACCELERATION + 1.0  # Allow small float tolerance

    def test_velocity_clamping_during_integration(self):
        """Test that euler_integrate clamps velocity to MAX_VELOCITY."""
        tensor = StateTensor(0, 0, 100, 100)
        # Apply a moderate force and integrate many times
        tensor.apply_force(np.array([1000.0, 0.0, 0.0, 0.0], dtype=np.float32))
        
        for _ in range(100):
            tensor.euler_integrate(0.016, viscosity=0.0)
        
        mag = np.linalg.norm(tensor.velocity)
        assert mag <= MAX_VELOCITY + 1.0

    def test_epsilon_snapping(self):
        """Test that elements snap to target when close enough."""
        tensor = StateTensor(0, 0, 100, 100)
        target = np.array([0.1, 0.1, 100.0, 100.0], dtype=np.float32)
        
        # Set state very close to target with tiny velocity
        tensor.state = np.array([0.2, 0.2, 100.0, 100.0], dtype=np.float32)
        tensor.velocity = np.array([0.1, 0.1, 0.0, 0.0], dtype=np.float32)
        
        tensor.euler_integrate(0.016, viscosity=0.5, target_state=target)
        
        # Should have snapped to target
        np.testing.assert_array_almost_equal(tensor.state, target, decimal=4)
        assert np.linalg.norm(tensor.velocity) == 0.0
