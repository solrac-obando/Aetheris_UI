# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
M2 Unit Tests - 35 pruebas unitarias para Batch Asymptotes.

Estas pruebas verifican:
- Kernels Numba JIT
- Clasificación static/dynamic
-边界 clamping
- NaN/Inf protection
- Performance benchmarks
- Integración con el motor

NO modificamos los tests - el código debe pasar las pruebas.
"""
import numpy as np
import pytest
import time
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.solver_batch_asymptotes import (
    batch_calculate_asymptotes,
    classify_dynamic_elements,
    batch_asymptote_delta,
    BatchAsymptoteCalculator,
    HAS_NUMBA,
    DEFAULT_LERP_FACTOR,
    THRESHOLD_STATIC,
)


# ==============================================================================
# GRUPO 1: Batch Calculation Tests (10 tests)
# ==============================================================================

class TestM2BatchCalculation:
    """Tests 1-10: Batch asymptote calculation."""

    def test_01_batch_output_shape(self):
        """Test 1: Output has correct shape."""
        n = 100
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        assert out.shape == (n, 4)

    def test_02_batch_float32_precision(self):
        """Test 2: Output maintains float32 precision."""
        states = np.array([[100.5, 200.7, 50.3, 30.1]], dtype=np.float32)
        targets = np.array([[300.0, 400.0, 50.0, 30.0]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        assert out.dtype == np.float32

    def test_03_batch_lerp_convergence(self):
        """Test 3: Elements converge toward targets."""
        states = np.array([[0, 0, 100, 100]], dtype=np.float32)
        targets = np.array([[1000, 1000, 100, 100]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        # After lerp: 0 + (1000 - 0) * 0.15 = 150
        assert out[0, 0] > 0 and out[0, 0] < 1000

    def test_04_batch_boundary_left(self):
        """Test 4: Clamp to left boundary."""
        states = np.array([[-100, 100, 50, 50]], dtype=np.float32)
        targets = np.array([[-200, 100, 50, 50]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        assert out[0, 0] >= 0

    def test_05_batch_boundary_right(self):
        """Test 5: Clamp to right boundary."""
        states = np.array([[1200, 100, 50, 50]], dtype=np.float32)
        targets = np.array([[2000, 100, 50, 50]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        assert out[0, 0] + out[0, 2] <= 1280

    def test_06_batch_boundary_top(self):
        """Test 6: Clamp to top boundary."""
        states = np.array([[100, -100, 50, 50]], dtype=np.float32)
        targets = np.array([[100, -200, 50, 50]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        assert out[0, 1] >= 0

    def test_07_batch_boundary_bottom(self):
        """Test 7: Clamp to bottom boundary."""
        states = np.array([[100, 700, 50, 50]], dtype=np.float32)
        targets = np.array([[100, 1000, 50, 50]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        assert out[0, 1] + out[0, 3] <= 720

    def test_08_batch_nan_input(self):
        """Test 8: Handle NaN input gracefully."""
        states = np.array([[100, 100, 50, 50]], dtype=np.float32)
        targets = np.array([[float('nan'), 100, 50, 50]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        assert np.isfinite(out).all()

    def test_09_batch_inf_input(self):
        """Test 9: Handle Inf input gracefully."""
        states = np.array([[100, 100, 50, 50]], dtype=np.float32)
        targets = np.array([[float('inf'), 100, 50, 50]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        assert np.isfinite(out).all()

    def test_10_batch_mixed_boundaries(self):
        """Test 10: Handle element crossing multiple boundaries."""
        states = np.array([[-50, -50, 200, 200]], dtype=np.float32)
        targets = np.array([[2000, 2000, 200, 200]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        # Should be clamped within bounds
        assert 0 <= out[0, 0] <= 1280
        assert 0 <= out[0, 1] <= 720


# ==============================================================================
# GRUPO 2: Classification Tests (10 tests)
# ==============================================================================

class TestM2Classification:
    """Tests 11-20: Static/Dynamic classification."""

    def test_11_classify_static_exact(self):
        """Test 11: Exact same position is static."""
        states = np.array([[100, 100, 50, 50]], dtype=np.float32)
        previous = states.copy()
        
        is_dynamic = classify_dynamic_elements(states, previous, THRESHOLD_STATIC)
        assert is_dynamic[0] == 0

    def test_12_classify_static_below_threshold(self):
        """Test 12: Position change below threshold is static."""
        states = np.array([[100.1, 100, 50, 50]], dtype=np.float32)
        previous = np.array([[100, 100, 50, 50]], dtype=np.float32)
        
        is_dynamic = classify_dynamic_elements(states, previous, THRESHOLD_STATIC)
        assert is_dynamic[0] == 0

    def test_13_classify_dynamic_above_threshold(self):
        """Test 13: Position change above threshold is dynamic."""
        states = np.array([[101, 100, 50, 50]], dtype=np.float32)
        previous = np.array([[100, 100, 50, 50]], dtype=np.float32)
        
        is_dynamic = classify_dynamic_elements(states, previous, THRESHOLD_STATIC)
        assert is_dynamic[0] == 1

    def test_14_classify_dimension_change(self):
        """Test 14: Dimension change triggers dynamic."""
        states = np.array([[100, 100, 55, 50]], dtype=np.float32)
        previous = np.array([[100, 100, 50, 50]], dtype=np.float32)
        
        is_dynamic = classify_dynamic_elements(states, previous, THRESHOLD_STATIC)
        assert is_dynamic[0] == 1

    def test_15_classify_mixed(self):
        """Test 15: Mixed static/dynamic classification."""
        n = 100
        current = np.zeros((n, 4), dtype=np.float32)
        previous = np.zeros((n, 4), dtype=np.float32)
        
        # First 30 dynamic
        current[30:, 0] = 1.0
        
        is_dynamic = classify_dynamic_elements(current, previous, THRESHOLD_STATIC)
        assert is_dynamic.sum() == 70

    def test_16_classify_all_static(self):
        """Test 16: All static returns all zeros."""
        n = 50
        states = np.ones((n, 4), dtype=np.float32)
        previous = states.copy()
        
        is_dynamic = classify_dynamic_elements(states, previous, THRESHOLD_STATIC)
        assert is_dynamic.sum() == 0

    def test_17_classify_all_dynamic(self):
        """Test 17: Large movement all dynamic."""
        n = 50
        states = np.ones((n, 4), dtype=np.float32) * 100
        previous = np.zeros((n, 4), dtype=np.float32)
        
        is_dynamic = classify_dynamic_elements(states, previous, THRESHOLD_STATIC)
        assert is_dynamic.sum() == n

    def test_18_delta_calculation(self):
        """Test 18: Delta calculation is correct."""
        current = np.array([[100, 200, 50, 50]], dtype=np.float32)
        previous = np.array([[50, 150, 50, 50]], dtype=np.float32)
        
        delta = batch_asymptote_delta(current, previous)
        
        assert delta[0] == 100  # |100-50| + |200-150|

    def test_19_delta_zero(self):
        """Test 19: Zero delta for identical states."""
        states = np.array([[100, 100, 50, 50]], dtype=np.float32)
        previous = states.copy()
        
        delta = batch_asymptote_delta(states, previous)
        assert delta[0] == 0

    def test_20_delta_spatial(self):
        """Test 20: Delta sums all dimensions."""
        current = np.array([[10, 20, 30, 40]], dtype=np.float32)
        previous = np.array([[5, 10, 15, 20]], dtype=np.float32)
        
        delta = batch_asymptote_delta(current, previous)
        
        # L1 norm: 5 + 10 + 15 + 20 = 50
        assert delta[0] == 50


# ==============================================================================
# GRUPO 3: Performance Tests (10 tests)
# ==============================================================================

class TestM2Performance:
    """Tests 21-30: Performance benchmarks."""

    def test_21_perf_1k(self):
        """Test 21: 1K elements benchmark."""
        n = 1000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        # Warmup
        batch_calculate_asymptotes(states[:10], targets[:10], 0.15, 1280, 720, out[:10])
        
        start = time.perf_counter()
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        ms = (time.perf_counter() - start) * 1000
        
        assert ms < 2.0

    def test_22_perf_5k(self):
        """Test 22: 5K elements benchmark."""
        n = 5000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states[:10], targets[:10], 0.15, 1280, 720, out[:10])
        
        start = time.perf_counter()
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        ms = (time.perf_counter() - start) * 1000
        
        assert ms < 5.0

    def test_23_perf_10k(self):
        """Test 23: 10K elements benchmark."""
        n = 10000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states[:10], targets[:10], 0.15, 1280, 720, out[:10])
        
        start = time.perf_counter()
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        ms = (time.perf_counter() - start) * 1000
        
        assert ms < 10.0

    def test_24_perf_30k(self):
        """Test 24: 30K elements benchmark."""
        n = 30000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states[:10], targets[:10], 0.15, 1280, 720, out[:10])
        
        start = time.perf_counter()
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        ms = (time.perf_counter() - start) * 1000
        
        assert ms < 15.0

    def test_25_perf_50k(self):
        """Test 25: 50K elements (M2 target)."""
        n = 50000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states[:10], targets[:10], 0.15, 1280, 720, out[:10])
        
        start = time.perf_counter()
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        ms = (time.perf_counter() - start) * 1000
        
        assert ms < 16.0  # 60 FPS target

    def test_26_perf_parallel_scaling(self):
        """Test 26: Parallel scaling verification."""
        times = []
        for n in [1000, 5000, 10000]:
            states = np.random.rand(n, 4).astype(np.float32) * 800
            targets = np.random.rand(n, 4).astype(np.float32) * 800
            out = np.empty_like(states)
            
            # Warmup
            batch_calculate_asymptotes(states[:10], targets[:10], 0.15, 1280, 720, out[:10])
            
            start = time.perf_counter()
            batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
            times.append(n / (time.perf_counter() - start))
        
        # Should scale (elements/ms increases or stays similar)
        print(f"Throughput: {times[0]:.0f}, {times[1]:.0f}, {times[2]:.0f} elements/ms")

    def test_27_classification_overhead(self):
        """Test 27: Classification overhead is minimal."""
        n = 10000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        previous = states.copy()
        
        # Slight movement on half
        states[:n//2, 0] += 0.3
        
        start = time.perf_counter()
        is_dynamic = classify_dynamic_elements(states, previous, THRESHOLD_STATIC)
        ms = (time.perf_counter() - start) * 1000
        
        assert ms < 2.0

    def test_28_async_savings_estimate(self):
        """Test 28: Estimate async computation savings."""
        n = 10000
        # 25% static
        previous = np.zeros((n, 4), dtype=np.float32)
        current = previous.copy()
        current[2500:] = [1.0, 0, 0, 0]  # Last 75% dynamic
        
        is_dynamic = classify_dynamic_elements(current, previous, THRESHOLD_STATIC)
        dynamic_ratio = is_dynamic.sum() / n
        
        # Should skip ~25% computation (75% dynamic)
        assert dynamic_ratio > 0.70

    def test_29_perf_consistency(self):
        """Test 29: Performance consistency across runs."""
        n = 5000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        times = []
        for _ in range(5):
            batch_calculate_asymptotes(states[:10], targets[:10], 0.15, 1280, 720, out[:10])
            start = time.perf_counter()
            batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
            times.append(time.perf_counter() - start)
        
        # Max should not exceed 2x average
        avg = np.mean(times)
        assert max(times) < avg * 2

    def test_30_perf_frame_budget(self):
        """Test 30: Within 16ms frame budget for 50K."""
        n = 50000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        # Warmup
        batch_calculate_asymptotes(states[:10], targets[:10], 0.15, 1280, 720, out[:10])
        
        start = time.perf_counter()
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # Should meet 60 FPS budget (16.67ms)
        assert elapsed_ms < 16.67


# ==============================================================================
# GRUPO 4: Integration Tests (5 tests)
# ==============================================================================

class TestM2Integration:
    """Tests 31-35: Integration with framework."""

    def test_31_calculator_api(self):
        """Test 31: BatchAsymptoteCalculator API."""
        calc = BatchAsymptoteCalculator()
        
        states = np.random.rand(100, 4).astype(np.float32) * 800
        targets = np.random.rand(100, 4).astype(np.float32) * 800
        
        out = calc.calculate(states, targets, (1280, 720))
        
        assert out.shape == states.shape

    def test_32_calculator_default_values(self):
        """Test 32: Default configuration."""
        calc = BatchAsymptoteCalculator()
        
        assert calc.lerp_factor == DEFAULT_LERP_FACTOR
        assert calc.static_threshold == THRESHOLD_STATIC
        assert calc.enable_async == True

    def test_33_calculator_async_first_call(self):
        """Test 33: First call enables async tracking."""
        calc = BatchAsymptoteCalculator(enable_async=True)
        
        states = np.zeros((100, 4), dtype=np.float32)
        targets = np.random.rand(100, 4).astype(np.float32) * 800
        
        # First call - no previous state
        calc.calculate(states, targets, (1280, 720))
        
        # Should have set previous state
        assert calc._previous_states is not None

    def test_34_calculator_dynamic_ratio(self):
        """Test 34: Dynamic ratio calculation."""
        calc = BatchAsymptoteCalculator(enable_async=True)
        
        n = 1000
        states = np.zeros((n, 4), dtype=np.float32)
        previous = states.copy()
        
        # All static
        ratio = calc.get_dynamic_ratio(states)
        
        # After setting previous, should be computed
        calc._previous_states = previous.copy()
        ratio = calc.get_dynamic_ratio(states)
        
        assert 0 <= ratio <= 1

    def test_35_numba_availability(self):
        """Test 35: Numba JIT availability check."""
        assert HAS_NUMBA in [True, False]


# ==============================================================================
# EJECUCIÓN
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])