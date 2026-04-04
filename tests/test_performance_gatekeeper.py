# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Performance Gatekeeper — hard limit: 16.6ms per tick at 60 FPS.

This test is the final checkpoint before any merge. It benchmarks the
AetherEngine under high load (100 concurrent physics elements) and
enforces a strict frame-time budget.

If this test fails, the engine is NOT production-ready.
"""
import os, sys, time
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AetherEngine
from core.elements import StaticBox
from core.aether_math import StateTensor

# Gatekeeper thresholds
ELEMENT_COUNT = 100
TICK_COUNT = 500
FPS_TARGET = 60
MAX_FRAME_TIME_MS = 1000.0 / FPS_TARGET  # 16.666...ms


class TestPerformanceGatekeeper:
    """Hard performance gate — no exceptions, no retries."""

    def test_engine_100_elements_500_ticks_under_16_6ms(self):
        """Benchmark: 100 elements × 500 ticks must average < 16.6ms.

        This is the single most important performance test in the suite.
        It simulates a real-world heavy UI scenario and enforces the
        60 FPS frame budget.

        On failure, the exact millisecond count is printed to identify
        the bottleneck.
        """
        engine = AetherEngine()

        # Register 100 elements in a grid layout
        cols = 10
        for i in range(ELEMENT_COUNT):
            x = 50 + (i % cols) * 80
            y = 50 + (i // cols) * 60
            engine.register_element(StaticBox(x, y, 60, 40, z=i))

        assert engine.element_count == ELEMENT_COUNT

        # Warm up JIT (Numba compilation on first call)
        engine.tick(1280, 720)
        engine.tick(1280, 720)

        # Benchmark 500 consecutive ticks
        tick_times = np.empty(TICK_COUNT, dtype=np.float64)
        for i in range(TICK_COUNT):
            t0 = time.perf_counter()
            data = engine.tick(1280, 720)
            tick_times[i] = (time.perf_counter() - t0) * 1000.0
            # Verify data integrity every tick
            assert len(data) == ELEMENT_COUNT
            assert not np.any(np.isnan(data["rect"]))
            assert not np.any(np.isinf(data["rect"]))

        avg_ms = float(np.mean(tick_times))
        median_ms = float(np.median(tick_times))
        p95_ms = float(np.percentile(tick_times, 95))
        p99_ms = float(np.percentile(tick_times, 99))
        max_ms = float(np.max(tick_times))
        min_ms = float(np.min(tick_times))

        # Detailed performance report
        report = (
            f"\n{'=' * 60}\n"
            f"PERFORMANCE GATEKEEPER REPORT\n"
            f"{'=' * 60}\n"
            f"  Elements:       {ELEMENT_COUNT}\n"
            f"  Ticks:          {TICK_COUNT}\n"
            f"  Target FPS:     {FPS_TARGET} ({MAX_FRAME_TIME_MS:.2f}ms/frame)\n"
            f"  ──────────────────────────────────────────────────\n"
            f"  Average:        {avg_ms:.3f} ms\n"
            f"  Median:         {median_ms:.3f} ms\n"
            f"  Min:            {min_ms:.3f} ms\n"
            f"  Max:            {max_ms:.3f} ms\n"
            f"  P95:            {p95_ms:.3f} ms\n"
            f"  P99:            {p99_ms:.3f} ms\n"
            f"  {'=' * 60}\n"
        )

        if avg_ms > MAX_FRAME_TIME_MS:
            report += (
                f"  ❌ FAILED — Average {avg_ms:.3f}ms exceeds {MAX_FRAME_TIME_MS:.2f}ms budget\n"
                f"  Bottleneck: +{avg_ms - MAX_FRAME_TIME_MS:.3f}ms over budget\n"
                f"{'=' * 60}\n"
            )
        else:
            headroom = MAX_FRAME_TIME_MS - avg_ms
            report += (
                f"  ✅ PASSED — {headroom:.3f}ms headroom below budget\n"
                f"{'=' * 60}\n"
            )

        print(report)

        assert avg_ms <= MAX_FRAME_TIME_MS, (
            f"Performance gatekeeper FAILED: avg={avg_ms:.3f}ms "
            f"exceeds {MAX_FRAME_TIME_MS:.2f}ms budget "
            f"(+{avg_ms - MAX_FRAME_TIME_MS:.3f}ms over). "
            f"Median={median_ms:.3f}ms, P95={p95_ms:.3f}ms, P99={p99_ms:.3f}ms, Max={max_ms:.3f}ms"
        )

    def test_engine_stability_under_load(self):
        """Verify no NaN/Inf creeps in during the benchmark window."""
        engine = AetherEngine()
        for i in range(ELEMENT_COUNT):
            engine.register_element(StaticBox(
                50 + (i % 10) * 80, 50 + (i // 10) * 60, 60, 40, z=i
            ))
        # Warm up
        engine.tick(1280, 720)
        engine.tick(1280, 720)
        for _ in range(200):
            data = engine.tick(1280, 720)
            assert not np.any(np.isnan(data["rect"])), "NaN detected in rect data"
            assert not np.any(np.isnan(data["color"])), "NaN detected in color data"
            assert not np.any(np.isinf(data["rect"])), "Inf detected in rect data"
