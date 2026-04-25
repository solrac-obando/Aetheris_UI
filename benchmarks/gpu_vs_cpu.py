import time
import json
import numpy as np
try:
    from aetheris_rust import AetherEngine, Vec4
except ImportError:
    print("Error: aetheris_rust no está instalado. Por favor, compila el módulo con 'maturin develop'.")
    # Mock para que el script no falle al guardarse
    class AetherEngine:
        def __init__(self): pass
        def enable_gpu(self): return False
        def register_static_box(self, *args): pass
        def tick_benchmark(self, w, h, it): return 100.0

def run_benchmark(count=50000, iterations=100):
    print(f"--- Aetheris UI Benchmarking: {count} elementos ---")
    
    # 1. Setup Engine CPU
    engine_cpu = AetherEngine()
    for i in range(count):
        engine_cpu.register_static_box(
            np.random.rand() * 800, 
            np.random.rand() * 600, 
            30, 30, 
            Vec4(1, 0, 0, 1), 
            i
        )
    
    print("Iniciando Benchmark CPU (Rayon Parallel)...")
    ms_cpu = engine_cpu.tick_benchmark(800.0, 600.0, iterations)
    avg_cpu = ms_cpu / iterations
    print(f"CPU Avg: {avg_cpu:.4f} ms/frame")

    # 2. Setup Engine GPU
    engine_gpu = AetherEngine()
    for i in range(count):
        engine_gpu.register_static_box(
            np.random.rand() * 800, 
            np.random.rand() * 600, 
            30, 30, 
            Vec4(0, 0, 1, 1), 
            i
        )
    
    print("Iniciando Benchmark GPU (WebGPU)...")
    gpu_ok = engine_gpu.enable_gpu()
    if not gpu_ok:
        print("ADVERTENCIA: WebGPU no disponible. El resultado será similar a CPU.")
    
    ms_gpu = engine_gpu.tick_benchmark(800.0, 600.0, iterations)
    avg_gpu = ms_gpu / iterations
    print(f"GPU Avg: {avg_gpu:.4f} ms/frame")

    # 3. Results Summary
    speedup = avg_cpu / avg_gpu if avg_gpu > 0 else 0
    print("\n--- RESUMEN ---")
    print(f"CPU (Rayon): {avg_cpu:.4f} ms")
    print(f"GPU (WebGPU): {avg_gpu:.4f} ms")
    print(f"Speedup: {speedup:.2f}x")
    
    if speedup > 3:
        print("\nResultado: ¡Éxito masivo! El kernel WGSL es significativamente más rápido.")
    elif speedup > 1:
        print("\nResultado: Mejora detectada. La GPU supera a la CPU paralelizada.")
    else:
        print("\nResultado: La latencia de copia (Round-trip) domina sobre el cálculo para este volumen.")

if __name__ == "__main__":
    run_benchmark(50000, 100)
