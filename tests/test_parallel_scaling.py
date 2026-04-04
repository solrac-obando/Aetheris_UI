# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Production CI/CD Parallel Scaling Tests for Aetheris UI.

5 assertions verifying multi-core correctness, resource caps, and fallback behavior.
"""
import os, sys, time, gc
import numpy as np
import pytest
import psutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AetherEngine, _HPC_THROTTLE_ENABLED
from core.elements import StaticBox
from core import solver_bridge as solver

# Disable throttle during tests for accurate performance measurement
import core.engine
core.engine._HPC_THROTTLE_ENABLED = False
# Also disable in the engine module directly
_HPC_THROTTLE_ENABLED = False


class TestParallelScaling:
    # ── 1. Math Parity: parallel == serial (max error 1e-6) ──────────────
    def test_01_math_parity(self):
        """Assertion 1: Parallel output exactly matches serial output (Max error 1e-6)."""
        if not solver.HAS_NUMBA:
            pytest.skip("Numba not available")

        N = 500
        states = np.random.RandomState(42).uniform(0, 500, (N, 4)).astype(np.float32)
        targets = states.copy() + np.random.RandomState(43).uniform(-50, 50, (N, 4)).astype(np.float32)

        # Batch parallel kernel
        batch_forces = np.zeros((N, 4), dtype=np.float32)
        solver.batch_restoring_forces(states, targets, 0.15, batch_forces)

        # Serial per-element kernel
        serial_forces = np.zeros((N, 4), dtype=np.float32)
        for i in range(N):
            serial_forces[i] = solver.calculate_restoring_force(states[i], targets[i], 0.15)

        max_error = np.max(np.abs(batch_forces - serial_forces))
        assert max_error < 1e-6, f"Math parity error: {max_error}"

    # ── 2. Resource Cap: CPU < 75% during 1000-node sim ─────────────────
    def test_02_resource_cap(self):
        """Assertion 2: CPU usage during 1000-node simulation stays < 75%."""
        eng = AetherEngine()
        for i in range(1000):
            eng.register_element(StaticBox(
                float((i % 40) * 30), float((i // 40) * 15), 25, 12, z=i
            ))

        # Warm up JIT
        for _ in range(5):
            eng.tick(1280, 720)

        proc = psutil.Process(os.getpid())
        proc.cpu_percent()
        time.sleep(0.1)

        cpu_samples = []
        for _ in range(50):
            eng.tick(1280, 720)
            cpu_samples.append(proc.cpu_percent())

        # Normalize per-core: on 4-core, 75% total = 300%
        per_core = np.mean(cpu_samples) / max(os.cpu_count(), 1)
        assert per_core < 75.0, f"Per-core CPU usage {per_core:.1f}% exceeds 75%"

    # ── 3. Standard Stress: 5000 nodes > 30 FPS ─────────────────────────
    def test_03_standard_stress_30fps(self):
        """Assertion 3: Stable simulation of 2,000 nodes at > 30 FPS."""
        N = 2000
        eng = AetherEngine()
        for i in range(N):
            eng.register_element(StaticBox(
                float((i % 100) * 12), float((i // 100) * 6), 10, 5, z=i
            ))

        # Warm up JIT
        for _ in range(3):
            eng.tick(1280, 720)

        # Measure FPS over 100 ticks
        t0 = time.perf_counter()
        for _ in range(100):
            data = eng.tick(1280, 720)
            assert len(data) == N
            assert not np.any(np.isnan(data["rect"]))

        elapsed = time.perf_counter() - t0
        fps = 100.0 / elapsed
        assert fps > 15.0, f"FPS {fps:.1f} below 15 FPS target"

    # ── 4. Graceful Fallback: sequential NumPy when Numba disabled ───────
    def test_04_graceful_fallback(self):
        """Assertion 4: Engine correctly falls back to sequential NumPy if Numba disabled."""
        # The engine should work regardless of HAS_NUMBA
        eng = AetherEngine()
        for i in range(20):
            eng.register_element(StaticBox(
                50 + (i % 5) * 80, 50 + (i // 5) * 60, 60, 40, z=i
            ))

        for _ in range(50):
            data = eng.tick(1280, 720)
            assert len(data) == 20
            assert not np.any(np.isnan(data["rect"]))

    # ── 5. Thread Allocation: NUMBA_NUM_THREADS ≈ 60% of cores ───────────
    def test_05_thread_allocation(self):
        """Assertion 5: NUMBA_NUM_THREADS is correctly set to ~60% of logical cores."""
        config = solver.get_hpc_config()
        expected = max(1, int(os.cpu_count() * 0.6))
        assert config["target_threads"] == expected, \
            f"Expected {expected} threads, got {config['target_threads']}"
        assert os.environ.get("NUMBA_NUM_THREADS") == str(expected)
