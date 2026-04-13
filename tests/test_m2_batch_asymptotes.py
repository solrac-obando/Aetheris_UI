# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
M2 Batch Asymptotes Tests.

Tests for the vectorized asymptote calculation with Numba JIT
and async interpolation optimization.
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


class TestM2BatchAsymptotes:
    """Tests for M2 batch asymptote calculation."""

    def test_batch_calculate_basic(self):
        """Test basic asymptote calculation."""
        n = 100
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        assert out.shape == (n, 4)
        assert np.isfinite(out).all()

    def test_batch_boundary_clamp(self):
        """Test boundary clamping."""
        n = 10
        states = np.array([[-10, -10, 100, 100]] * n, dtype=np.float32)
        targets = np.array([[2000, 2000, 100, 100]] * n, dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        # Should clamp within bounds
        assert (out[:, 0] >= 0).all()
        assert (out[:, 1] >= 0).all()
        assert (out[:, 0] + out[:, 2] <= 1280).all()
        assert (out[:, 1] + out[:, 3] <= 720).all()

    def test_batch_nan_protection(self):
        """Test NaN/Inf protection."""
        n = 10
        states = np.array([[100, 100, 50, 50]] * n, dtype=np.float32)
        targets = np.array([[float('nan'), float('inf'), 50, 50]] * n, dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        # Should not propagate NaN/Inf
        assert np.isfinite(out).all()

    def test_classify_static(self):
        """Test static/dynamic classification."""
        n = 100
        previous = np.zeros((n, 4), dtype=np.float32)
        
        # 50 static, 50 dynamic
        current = np.zeros((n, 4), dtype=np.float32)
        current[50:] = [[1, 0, 0, 0]] * 50
        
        is_dynamic = classify_dynamic_elements(current, previous, THRESHOLD_STATIC)
        
        assert is_dynamic.sum() == 50

    def test_performance_10k(self):
        """Test performance with 10K elements."""
        n = 10000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        # Warmup
        batch_calculate_asymptotes(states[:10], targets[:10], 0.15, 1280, 720, out[:10])
        
        # Benchmark
        times = []
        for _ in range(10):
            start = time.perf_counter()
            batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
            times.append(time.perf_counter() - start)
        
        avg_ms = np.mean(times) * 1000
        assert avg_ms < 5.0, f"Too slow: {avg_ms:.2f}ms for 10K elements"

    def test_performance_50k(self):
        """Test performance with 50K elements."""
        n = 50000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        # Warmup
        batch_calculate_asymptotes(states[:100], targets[:100], 0.15, 1280, 720, out[:100])
        
        start = time.perf_counter()
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # Target: under 16ms for 60 FPS
        assert elapsed_ms < 16.0, f"Missed 60 FPS target: {elapsed_ms:.2f}ms"

    def test_async_optimization(self):
        """Test async optimization saves computation."""
        calc = BatchAsymptoteCalculator(enable_async=True)
        
        n = 10000
        states = np.zeros((n, 4), dtype=np.float32)
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        
        # First call - full calculation
        out1 = calc.calculate(states, targets, (1280, 720))
        
        # Small movement - should classify mostly static
        states_small = states.copy()
        states_small[:, 0] += 0.1  # Below threshold
        
        ratio = calc.get_dynamic_ratio(states_small)
        
        # Most should be static
        print(f"Dynamic ratio with small movement: {ratio*100:.1f}%")
        assert ratio < 0.10, f"Expected mostly static, got {ratio*100:.1f}%"


class TestM2SafetyMargin:
    """Tests for safety margin."""

    def test_safety_margin_35_percent(self):
        """Verify safety margin is 35%."""
        from core.dynamic_limits import SAFETY_MARGIN
        assert SAFETY_MARGIN == 0.35

    def test_operative_limit(self):
        """Test operative limit calculation."""
        from core.dynamic_limits import get_theoretical_capacity, get_optimal_max_elements
        
        # 4 cores = 3200 theoretical
        theoretical = get_theoretical_capacity(4)
        operative = get_optimal_max_elements(800, 4, 0.35)
        
        # Expected: 3200 * (1 - 0.35) = 2080
        assert operative == 2080


if __name__ == "__main__":
    pytest.main([__file__, "-v"])