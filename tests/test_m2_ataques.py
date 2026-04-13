# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
M2 Integration Attack Tests - Vulnerabilities Detection.

This test verifies that M2 implementation is secure against:
- Buffer overflow
- Memory exhaustion
- NaN/Inf injection
- Classification bypass
- Dynamic limit bypass
- Performance degradation attacks
"""
import numpy as np
import pytest
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.solver_batch_asymptotes import (
    batch_calculate_asymptotes,
    classify_dynamic_elements,
    BatchAsymptoteCalculator,
    THRESHOLD_STATIC,
)
from core.dynamic_limits import (
    SAFETY_MARGIN,
    get_optimal_max_elements,
    get_theoretical_capacity,
)


class TestM2VulnerabilityAttacks:
    """Attack tests for M2 vulnerabilities."""

    def test_attack_01_extreme_element_count(self):
        """Attack 1: Extreme element count overflow."""
        # Try with 1 million elements - should fail gracefully or use warning
        n = 1000000
        try:
            states = np.random.rand(n, 4).astype(np.float32) * 800
            targets = np.random.rand(n, 4).astype(np.float32) * 800
            out = np.empty_like(states)
            
            # This should timeout or be very slow
            start = time.perf_counter()
            batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
            elapsed = time.perf_counter() - start
            
            # Should not take more than 1 second for ANY count
            assert elapsed < 1.0, f"Extremely slow: {elapsed}s"
        except MemoryError:
            # Acceptable - system protects itself
            pass

    def test_attack_02_nan_injection(self):
        """Attack 2: Inject NaN to crash system."""
        n = 10000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        targets[0, 0] = float('nan')
        targets[1000, 0] = float('nan')
        targets[5000, 0] = float('nan')
        out = np.empty_like(states)
        
        # Should not propagate NaN
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        assert np.isfinite(out).all(), "NaN propagated!"

    def test_attack_03_inf_injection(self):
        """Attack 3: Inject Inf to crash system."""
        n = 10000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        targets[0, 0] = float('inf')
        targets[1000, 0] = float('-inf')
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        assert np.isfinite(out).all(), "Inf propagated!"

    def test_attack_04_negative_coordinates(self):
        """Attack 4: Negative coordinates overflow."""
        n = 1000
        states = np.array([[-1e10, -1e10, 50, 50]] * n, dtype=np.float32)
        targets = np.array([[-1e10, -1e10, 50, 50]] * n, dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        # Should clamp within bounds
        assert (out >= 0).all(), "Negative coordinates leaked!"

    def test_attack_05_extreme_coordinates(self):
        """Attack 5: Extreme coordinates overflow."""
        n = 1000
        states = np.array([[1e10, 1e10, 50, 50]] * n, dtype=np.float32)
        targets = np.array([[1e10, 1e10, 50, 50]] * n, dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        # Should clamp within bounds
        assert (out[:, 0] <= 1280).all(), "Extreme X leaked!"
        assert (out[:, 1] <= 720).all(), "Extreme Y leaked!"

    def test_attack_06_classification_bypass(self):
        """Attack 6: Bypass classification with small movements."""
        n = 1000
        previous = np.zeros((n, 4), dtype=np.float32)
        
        # Try to trick classifier with tiny movements
        current = previous.copy()
        for i in range(n):
            current[i, 0] = 0.49  # Just below threshold 0.5
        
        is_dynamic = classify_dynamic_elements(current, previous, THRESHOLD_STATIC)
        
        # All should be classified as STATIC (not dynamic)
        assert is_dynamic.sum() == 0, "Classification bypassed!"

    def test_attack_07_boundary_crossing(self):
        """Attack 7: Element crosses all boundaries."""
        states = np.array([[-1, -1, 100, 100]], dtype=np.float32)
        targets = np.array([[2000, 2000, 100, 100]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        # Must stay within bounds
        assert 0 <= out[0, 0] <= 1280
        assert 0 <= out[0, 1] <= 720

    def test_attack_08_safety_margin_respected(self):
        """Attack 8: Verify safety margin is applied."""
        cpu_count = os.cpu_count() or 4
        theoretical = get_theoretical_capacity(cpu_count)
        operative = get_optimal_max_elements(800, cpu_count, SAFETY_MARGIN)
        
        # operative must be less than theoretical
        assert operative < theoretical, "Safety margin bypassed!"
        
        # Check exact calculation: theoretical * (1 - 0.35)
        expected = int(theoretical * 0.65)
        assert operative == expected, f"Expected {expected}, got {operative}"

    def test_attack_09_parallel_overflow(self):
        """Attack 9: Thread overflow with parallel execution."""
        def worker(worker_id):
            n = 1000
            states = np.random.rand(n, 4).astype(np.float32) * 800
            targets = np.random.rand(n, 4).astype(np.float32) * 800
            out = np.empty_like(states)
            batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
            return np.isfinite(out).all()
        
        # Run in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]
        
        # All should succeed
        assert all(results), "Parallel execution failed!"

    def test_attack_10_zero_dimensions(self):
        """Attack 10: Zero-width/height elements."""
        states = np.array([[100, 100, 0, 0]], dtype=np.float32)
        targets = np.array([[100, 100, 0, 0]], dtype=np.float32)
        out = np.empty_like(states)
        
        batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        # Should handle without crash
        assert np.isfinite(out).all()

    def test_attack_11_perf_degradation(self):
        """Attack 11: Performance degradation attempt."""
        n = 50000
        states = np.random.rand(n, 4).astype(np.float32) * 800
        targets = np.random.rand(n, 4).astype(np.float32) * 800
        out = np.empty_like(states)
        
        times = []
        for _ in range(5):
            # Warmup
            batch_calculate_asymptotes(states[:100], targets[:100], 0.15, 1280, 720, out[:100])
            
            start = time.perf_counter()
            batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
            times.append(time.perf_counter() - start)
        
        avg_time = np.mean(times)
        
        # Should stay under 16ms (60 FPS)
        assert avg_time * 1000 < 16.0, f"Performance degraded: {avg_time*1000:.2f}ms"

    def test_attack_12_async_race_condition(self):
        """Attack 12: Race condition in async tracking."""
        calc = BatchAsymptoteCalculator(enable_async=True)
        
        n = 1000
        previous = np.zeros((n, 4), dtype=np.float32)
        
        # Trigger async tracking
        calc.calculate(previous, previous, (1280, 720))
        
        # Try to access previous simultaneously
        import threading
        results = []
        
        def read_state():
            try:
                ps = calc._previous_states
                results.append(ps is not None)
            except:
                results.append(False)
        
        threads = [threading.Thread(target=read_state) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All should succeed
        assert all(results)


class TestM2Stability:
    """Stability tests after attacks."""

    def test_stability_after_nan_flood(self):
        """Stability after NaN flood."""
        for _ in range(100):
            states = np.random.rand(1000, 4).astype(np.float32) * 800
            targets = np.random.rand(1000, 4).astype(np.float32) * 800
            targets[:, 0] = float('nan')
            
            out = np.empty_like(states)
            batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        # Should still work
        assert True

    def test_stability_after_inf_flood(self):
        """Stability after Inf flood."""
        for _ in range(100):
            states = np.random.rand(1000, 4).astype(np.float32) * 800
            targets = np.random.rand(1000, 4).astype(np.float32) * 800
            targets[::2, 0] = float('inf')
            targets[1::2, 0] = float('-inf')
            
            out = np.empty_like(states)
            batch_calculate_asymptotes(states, targets, 0.15, 1280, 720, out)
        
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])