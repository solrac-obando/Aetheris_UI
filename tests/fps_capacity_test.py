#!/usr/bin/env python3
"""
FPS Capacity Test: Find max elements at 60fps (16.67ms/frame) for each engine.
"""

import os
import sys
import time
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.engine import AetherEngine as PythonEngine
from core.elements import StaticBox, SmartPanel
from core.engine_selector import EngineSelector, _RUST_AVAILABLE

WIN_W, WIN_H = 1920.0, 1080.0
TARGET_FPS = 60
TARGET_MS = 1000.0 / TARGET_FPS  # 16.67ms
WARMUP_FRAMES = 30
MEASURE_FRAMES = 30


def test_engine_at_count(engine, count, label):
    """Test an engine at a given element count. Returns avg_ms."""
    for _ in range(WARMUP_FRAMES):
        engine.tick(WIN_W, WIN_H)

    times = []
    for _ in range(MEASURE_FRAMES):
        t0 = time.perf_counter()
        engine.tick(WIN_W, WIN_H)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000.0)

    avg_ms = sum(times) / len(times)
    fps = 1000.0 / avg_ms if avg_ms > 0 else float('inf')
    return avg_ms, fps


def find_max_elements_python():
    """Binary search for max Python elements at 60fps."""
    print(f"\n{'='*60}")
    print(f"  PYTHON ENGINE — Finding max elements at {TARGET_FPS}fps")
    print(f"  Target: < {TARGET_MS:.1f}ms/frame")
    print(f"{'='*60}")

    lo, hi = 100, 5000
    best = 0

    while lo <= hi:
        mid = (lo + hi) // 2
        engine = PythonEngine()
        for i in range(mid):
            x = (i % 50) * 38.4
            y = (i // 50) * 21.6
            engine.register_element(StaticBox(x, y, 30.0, 30.0, (0.8, 0.2, 0.3, 0.9), i % 10))

        import core.engine as eng_mod
        old_throttle = eng_mod._HPC_THROTTLE_ENABLED
        eng_mod._HPC_THROTTLE_ENABLED = False

        avg_ms, fps = test_engine_at_count(engine, mid, "Python")

        eng_mod._HPC_THROTTLE_ENABLED = old_throttle

        status = "✅" if avg_ms <= TARGET_MS else "❌"
        print(f"  {status} {mid:5d} elements | {avg_ms:.2f}ms | {fps:.1f} fps")

        if avg_ms <= TARGET_MS:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    return best


def find_max_elements_rust():
    """Binary search for max Rust elements at 60fps (pure compute)."""
    print(f"\n{'='*60}")
    print(f"  RUST ENGINE — Finding max elements at {TARGET_FPS}fps")
    print(f"  Target: < {TARGET_MS:.1f}ms/frame")
    print(f"{'='*60}")

    lo, hi = 1000, 50000
    best = 0

    while lo <= hi:
        mid = (lo + hi) // 2
        selector = EngineSelector(engine_type="rust")
        for i in range(mid):
            x = (i % 50) * 38.4
            y = (i // 50) * 21.6
            selector.register_element(StaticBox(x, y, 30.0, 30.0, (0.8, 0.2, 0.3, 0.9), i % 10))

        # Pure compute measurement
        total_ms = selector._engine._engine.tick_benchmark(WIN_W, WIN_H, MEASURE_FRAMES)
        avg_ms = total_ms / MEASURE_FRAMES
        fps = 1000.0 / avg_ms if avg_ms > 0 else float('inf')

        status = "✅" if avg_ms <= TARGET_MS else "❌"
        print(f"  {status} {mid:5d} elements | {avg_ms:.2f}ms | {fps:.1f} fps")

        if avg_ms <= TARGET_MS:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1

    return best


def estimate_web():
    """Estimate web (Pyodide/WASM) capacity based on known overhead."""
    print(f"\n{'='*60}")
    print(f"  WEB (Pyodide/WASM) — Estimación")
    print(f"{'='*60}")

    # Pyodide tiene ~3-5x overhead vs CPython nativo para NumPy operations
    # El motor Python puro en web es significativamente más lento
    # Basado en benchmarks públicos de Pyodide:
    # - NumPy operations: ~2-3x más lento que CPython
    # - Python puro: ~5-10x más lento que CPython
    # - Con Pyodide 1.0+ (WASM SIMD): mejoró ~30%

    # Estimación conservadora basada en proporción:
    # Si Python nativo = X elementos a 60fps
    # Pyodide ≈ X / 3 elementos (NumPy funciona bien en Pyodide)

    print(f"  Nota: Pyodide ejecuta el motor Python en WASM")
    print(f"  - NumPy en Pyodide: ~2-3x más lento que CPython")
    print(f"  - Python puro en Pyodide: ~5-10x más lento")
    print(f"  - Con WASM SIMD (Pyodide 1.0+): mejora ~30%")
    print()
    print(f"  Estimación conservadora: Python_max / 3")
    print(f"  Estimación optimista:    Python_max / 2")


def main():
    print(f"\n{'#'*60}")
    print(f"#  FPS CAPACITY TEST — Límite a {TARGET_FPS}fps")
    print(f"#  {'#'*58}")

    py_max = find_max_elements_python()

    if _RUST_AVAILABLE:
        rs_max = find_max_elements_rust()
    else:
        rs_max = 0
        print("\n  Rust engine no disponible, saltando...")

    estimate_web()

    print(f"\n{'='*60}")
    print(f"  RESULTADOS FINALES — Límite a {TARGET_FPS}fps")
    print(f"{'='*60}")
    print(f"  Python nativo:  ~{py_max:,} elementos")
    if rs_max > 0:
        print(f"  Rust nativo:    ~{rs_max:,} elementos ({rs_max/py_max:.0f}x más)")
    print(f"  Web (Pyodide):  ~{py_max//3:,}-{py_max//2:,} elementos (estimado)")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
