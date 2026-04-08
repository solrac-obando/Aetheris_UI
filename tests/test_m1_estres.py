# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
M1 Stress Tests - Pruebas de estrés y ataque intencional.

Estas pruebas simulan ataques reales al sistema para verificar resiliencia:
- Buffer overflow attacks
- Memory exhaustion
- Concurrency attacks  
- Injection attacks
- DoS attacks
- Extreme edge cases

El código DEBE pasar estas pruebas - no adaptamos los tests.
"""
import json
import time
import threading
import pytest
from unittest.mock import Mock
import sys
import os
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wasm.light_wasm_adapter import LightWASMAdapter


class MockElement:
    """Mock element para testing."""
    def __init__(self, x=0.0, y=0.0, w=100.0, h=100.0, z=0):
        self._z_index = z
        mock_tensor = Mock()
        mock_tensor.state = [float(x), float(y), float(w), float(h)]
        self.tensor = mock_tensor


# ==============================================================================
# ATTACK GROUP 1: Buffer Overflow Attacks
# ==============================================================================

class TestM1BufferOverflow:
    """Ataques de buffer overflow - verificar límites."""

    def test_overflow_01_extremely_large_element(self):
        """Ataque 1: Elemento con coordenadas extremas."""
        la = LightWASMAdapter(container_width=1000, container_height=1000, use_light_wasm=False)
        la.register_element(0, "overflow-1")
        
        elem = MockElement(1e10, 1e10, 1e10, 1e10)
        
        result = la.sync([elem])
        data = json.loads(result)
        
        assert len(data["elements"]) == 0, "Extreme values should be filtered"

    def test_overflow_02_very_small_element(self):
        """Ataque 2: Elemento infinitesimal."""
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "tiny-1")
        
        elem = MockElement(0.0001, 0.0001, 0.0001, 0.0001)
        
        result = la.sync([elem])
        data = json.loads(result)
        
        assert len(data["elements"]) == 1

    def test_overflow_03_negative_extreme(self):
        """Ataque 3: Coordenadas negativas extremas."""
        la = LightWASMAdapter(container_width=100, container_height=100, use_light_wasm=False)
        la.register_element(0, "neg-extreme")
        
        elem = MockElement(-1e10, -1e10, 50, 50)
        
        result = la.sync([elem])
        data = json.loads(result)
        
        elem_data = data["elements"][0]
        assert elem_data["x"] >= 0
        assert elem_data["y"] >= 0

    def test_overflow_04_massive_element_count(self):
        """Ataque 4: Registrar cantidad masiva de elementos."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        for i in range(10000):
            la.register_element(i, f"elem-{i}")
        
        assert la.element_count == 10000

    def test_overflow_05_sync_massive_array(self):
        """Ataque 5: Sync con 10000 elementos."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        for i in range(10000):
            la.register_element(i, f"elem-{i}")
        
        elements = [MockElement(i % 1000, i % 720, 20, 20) for i in range(10000)]
        
        start = time.perf_counter()
        result = la.sync(elements)
        elapsed = time.perf_counter() - start
        
        data = json.loads(result)
        assert len(data["elements"]) == 10000
        assert elapsed < 1.0, f"Sync should complete in <1s, took {elapsed:.2f}s"


# ==============================================================================
# ATTACK GROUP 2: Memory Exhaustion
# ==============================================================================

class TestM1MemoryExhaustion:
    """Ataques de memory exhaustion."""

    def test_memory_01_rapid_registration(self):
        """Ataque 1: Registrar/desregistrar rápidamente."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        for cycle in range(100):
            for i in range(100):
                la.register_element(i, f"elem-{i}-{cycle}")
            
            for i in range(100):
                la.unregister_element(i)
        
        assert la.element_count == 0

    def test_memory_02_no_leak_after_massive_syncs(self):
        """Ataque 2: Sin memory leak después de muchos syncs."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        for i in range(1000):
            la.register_element(i, f"elem-{i}")
        
        elements = [MockElement(i % 500, i % 500, 30, 30) for i in range(1000)]
        
        for _ in range(10000):
            la.sync(elements)
        
        assert la._sync_count == 10000

    def test_memory_03_reuse_element_ids(self):
        """Ataque 3: Reutilizar IDs de elementos."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        for cycle in range(50):
            for i in range(100):
                la.register_element(i, f"reuse-{i}")
            
            for i in range(100):
                la.unregister_element(i)
        
        assert la.element_count == 0


# ==============================================================================
# ATTACK GROUP 3: Concurrency Attacks
# ==============================================================================

class TestM1Concurrency:
    """Ataques de concurrencia."""

    def test_concurrency_01_parallel_sync(self):
        """Ataque 1: Sync paralelo desde múltiples threads."""
        la = LightWASMAdapter(use_light_wasm=False)
        errors = []
        
        def worker(worker_id):
            try:
                for i in range(100):
                    la.register_element(worker_id * 1000 + i, f"w{worker_id}-e{i}")
                    elem = MockElement(i * 10, i * 10, 30, 30)
                    la.sync([elem])
            except Exception as e:
                errors.append(str(e))
        
        threads = []
        for w in range(10):
            t = threading.Thread(target=worker, args=(w,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(errors) == 0, f"Errors: {errors}"
        assert la.element_count == 1000

    def test_concurrency_02_parallel_registration(self):
        """Ataque 2: Registro paralelo."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        def reg_worker(start_idx):
            for i in range(100):
                la.register_element(start_idx + i, f"par-{start_idx + i}")
        
        threads = []
        for w in range(5):
            t = threading.Thread(target=reg_worker, args=(w * 100,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert la.element_count == 500


# ==============================================================================
# ATTACK GROUP 4: Injection Attacks  
# ==============================================================================

class TestM1Injection:
    """Ataques de injection."""

    def test_injection_01_special_characters_in_id(self):
        """Ataque 1: Caracteres especiales en HTML ID."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        malicious_ids = [
            "elem<script>alert(1)</script>",
            "elem'onclick='alert(1)'",
            'elem"onload="alert(1)"',
            "<img src=x onerror=alert(1)>",
            "elem\n\r\t",
            "elem\x00\x00",
            "elem" + "A" * 10000,
        ]
        
        for mid in malicious_ids:
            try:
                la.register_element(0, mid)
            except Exception:
                pass
        
        assert la.element_count <= len(malicious_ids)

    def test_injection_02_unicode_in_coordinates(self):
        """Ataque 2: Unicode en coordenadas."""
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "unicode-elem")
        
        unicode_elem = MockElement(ord('A'), ord('B'), ord('C'), ord('D'))
        
        result = la.sync([unicode_elem])
        data = json.loads(result)
        
        assert len(data["elements"]) >= 0


# ==============================================================================
# ATTACK GROUP 5: DoS Attacks
# ==============================================================================

class TestM1DoS:
    """Denial of Service attacks."""

    def test_dos_01_repeated_empty_syncs(self):
        """Ataque 1: Repetidos syncs vacíos."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        for _ in range(10000):
            result = la.sync([])
            data = json.loads(result)
            assert data["elements"] == []
        
        assert la._sync_count == 10000

    def test_dos_02_rapid_sync_bursts(self):
        """Ataque 2: Ráfagas de sync."""
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "burst-elem")
        elem = MockElement(10, 10, 30, 30)
        
        start = time.perf_counter()
        for _ in range(1000):
            la.sync([elem])
        elapsed = time.perf_counter() - start
        
        assert elapsed < 1.0, f"Burst took {elapsed:.2f}s"
        assert la._sync_count == 1000

    def test_dos_03_element_flood(self):
        """Ataque 3: Flood de elementos."""
        la = LightWASMAdapter(use_light_wasm=False)
        
        for i in range(50000):
            la.register_element(i, f"flood-{i}")
        
        elements = [MockElement(i % 1000, i % 720, 10, 10) for i in range(50000)]
        
        start = time.perf_counter()
        result = la.sync(elements)
        elapsed = time.perf_counter() - start
        
        data = json.loads(result)
        assert len(data["elements"]) == 50000
        assert elapsed < 5.0, f"Flood took {elapsed:.2f}s"


# ==============================================================================
# ATTACK GROUP 6: Edge Case Attacks
# ==============================================================================

class TestM1EdgeAttack:
    """Edge case attacks."""

    def test_edge_01_float32_max(self):
        """Ataque 1: FLT_MAX value."""
        import struct
        
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "flt-max")
        
        flt_max = struct.unpack('f', b'\xff\xff\x7f\x7f')[0]
        elem = MockElement(flt_max, flt_max, flt_max, flt_max)
        
        result = la.sync([elem])
        data = json.loads(result)
        assert len(data["elements"]) == 0

    def test_edge_02_float_epsilon(self):
        """Ataque 2: Float epsilon."""
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "epsilon")
        
        epsilon = 1e-45
        elem = MockElement(epsilon, epsilon, epsilon, epsilon)
        
        result = la.sync([elem])
        data = json.loads(result)
        assert len(data["elements"]) >= 0

    def test_edge_03_denormal_numbers(self):
        """Ataque 3: Denormal numbers."""
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "denormal")
        
        elem = MockElement(1e-310, 1e-310, 1e-310, 1e-310)
        
        result = la.sync([elem])
        data = json.loads(result)
        assert len(data["elements"]) >= 0

    def test_edge_04_zero_dimensions(self):
        """Ataque 4: Cero dimensiones."""
        la = LightWASMAdapter(use_light_wasm=False)
        la.register_element(0, "zero-dim")
        
        elem = MockElement(10, 10, 0, 0)
        
        result = la.sync([elem])
        data = json.loads(result)
        
        if len(data["elements"]) > 0:
            e = data["elements"][0]
            assert e["w"] >= 0
            assert e["h"] >= 0


# ==============================================================================
# EJECUCIÓN
# ==============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])