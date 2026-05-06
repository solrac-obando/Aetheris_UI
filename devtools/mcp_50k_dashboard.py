# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");

import os
import sys
import json
import time
import numpy as np

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from core.engine_selector import EngineSelector
from core.ui_builder import UIBuilder
from core.logging import framework_logger

def create_50k_dashboard():
    print("🚀 Starting Aetheris 50K Stress Test...")
    
    # 1. Initialize Engine (Force Rust for performance)
    try:
        engine = EngineSelector(engine_type="rust")
        print(f"✅ Engine initialized: {engine.engine_type.upper()}")
    except Exception as e:
        print(f"❌ Failed to load Rust engine: {e}")
        print("Falling back to Python (performance will be lower)")
        engine = EngineSelector(engine_type="python")

    # 2. Generate 50,000 Elements
    print("📦 Generating 50,000 elements...")
    start_gen = time.perf_counter()
    
    # We'll use a mix of static boxes and status orbs
    elements = []
    for i in range(50000):
        elements.append({
            "id": f"e_{i}",
            "type": "static_box",
            "x": np.random.uniform(0, 1200),
            "y": np.random.uniform(0, 800),
            "w": 4,
            "h": 4,
            "color": [
                np.random.uniform(0.1, 0.4),
                np.random.uniform(0.5, 0.9),
                np.random.uniform(0.7, 1.0),
                0.8
            ],
            "z": 0
        })
    
    intent = {
        "layout": "absolute",
        "elements": elements,
        "animation": "fluid",
        "transition_speed_ms": 500
    }
    
    elapsed_gen = time.perf_counter() - start_gen
    print(f"✅ Generation complete in {elapsed_gen:.2f}s")

    # 3. Build UI
    print("🏗️ Building UI state tensors...")
    builder = UIBuilder()
    start_build = time.perf_counter()
    builder.build_from_intent(engine, intent)
    elapsed_build = time.perf_counter() - start_build
    print(f"✅ UI built in {elapsed_build:.2f}s")

    # 4. Benchmark Ticks (Native Rust Benchmark to avoid Python overhead)
    print("⏱️ Benchmarking 100 physics ticks (Native Rust)...")
    
    if engine.engine_type == "rust":
        # Using the internal wrapper to get to the PyAetherEngine object
        ms_total = engine._engine._engine.tick_benchmark(1200, 800, 100)
        avg_ms = ms_total / 100
    else:
        tick_times = []
        for _ in range(100):
            start_tick = time.perf_counter()
            engine.tick(1200, 800)
            tick_times.append(time.perf_counter() - start_tick)
        avg_ms = np.mean(tick_times) * 1000
    fps = 1000 / avg_ms if avg_ms > 0 else 0
    
    print("\n--- RESULTS ---")
    print(f"Total Elements: {engine.element_count}")
    print(f"Average Tick Time: {avg_ms:.2f} ms")
    print(f"Theoretical FPS: {fps:.2f} FPS")
    
    if fps >= 60:
        print("🏆 SUCCESS: Target 60 FPS exceeded!")
    else:
        print("⚠️ WARNING: Target 60 FPS not reached.")
    print("----------------\n")

    return engine

if __name__ == "__main__":
    create_50k_dashboard()
