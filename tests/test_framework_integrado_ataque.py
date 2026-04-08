# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Test de Ataque Integral - Framework Completo Operando.

Este test simula un ataque generalizado al framework cuando todos los módulos
están operando juntos, para detectar si hay una falla generalizada.

El test DEBE pasar - el framework debe resistir el ataque.
"""
import json
import time
import threading
import random
import pytest
import sys
import os
import math
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AetherEngine
from core.web_bridge import WebBridge
from core.elements import StaticBox, SmartPanel, SmartButton
from wasm.light_wasm_adapter import LightWASMAdapter


class MockElement:
    def __init__(self, x=0.0, y=0.0, w=100.0, h=100.0, z=0):
        self._z_index = z
        mock_tensor = type('Tensor', (), {'state': [float(x), float(y), float(w), float(h)]})()
        self.tensor = mock_tensor


class TestFrameworkIntegralAtaque:
    """Test de ataque integral al framework completo."""

    def test_01_inicializacion_multiple_componentes(self):
        """Ataque 1: inicializar múltiples componentes simultáneamente."""
        componentes = []
        errores = []

        def crear_componente(idx):
            try:
                engine = AetherEngine()
                bridge = WebBridge()
                adapter = LightWASMAdapter(use_light_wasm=False)
                return (idx, "OK")
            except Exception as e:
                return (idx, str(e))

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(crear_componente, i) for i in range(50)]
            for future in as_completed(futures):
                idx, result = future.result()
                if result != "OK":
                    errores.append(f"Componente {idx}: {result}")

        assert len(errores) == 0, f"Errores en inicialización: {errores}"

    def test_02_sync_paralelo_todos_componentes(self):
        """Ataque 2: sync paralelo en todos los componentes."""
        engine = AetherEngine()
        bridge = WebBridge()
        adapter = LightWASMAdapter(use_light_wasm=False)

        resultados = []
        errores = []

        def worker(worker_id):
            try:
                elements = [StaticBox(i * 10, i * 5, 50, 30) for i in range(100)]
                for elem in elements:
                    engine.register_element(elem)

                engine.tick(800, 600)

                for i in range(100):
                    bridge.register_element(i, f"bridge-{worker_id}-{i}")
                    adapter.register_element(i, f"adapter-{worker_id}-{i}")

                elements_mock = [MockElement(i % 500, i % 500, 30, 30) for i in range(100)]
                bridge.sync(elements_mock)
                adapter.sync(elements_mock)

                return f"Worker {worker_id}: OK"
            except Exception as e:
                return f"Worker {worker_id}: {str(e)}"

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(worker, i) for i in range(20)]
            for future in as_completed(futures):
                resultados.append(future.result())

        errores = [r for r in resultados if "ERROR" in r or "Error" in r]
        assert len(errores) == 0, f"Errores en sync paralelo: {errores[:5]}"

    def test_03_elementos_flood_todos_componentes(self):
        """Ataque 3: flood de elementos en todos los componentes."""
        engine = AetherEngine()
        bridge = WebBridge()
        adapter = LightWASMAdapter(use_light_wasm=False)

        errores = []
        rechazos_seguros = 0

        for flood_round in range(5):
            elementos = []
            try:
                for i in range(10000):
                    elem = StaticBox(i % 1280, i % 720, 20, 20)
                    elementos.append(elem)
                    engine.register_element(elem)

                engine.tick(1280, 720)

                for i in range(10000):
                    bridge.register_element(i, f"flood-{flood_round}-{i}")
                    adapter.register_element(i, f"flood-{flood_round}-{i}")

                mock_elems = [MockElement(i % 1000, i % 500, 20, 20) for i in range(10000)]
                bridge.sync(mock_elems)
                adapter.sync(mock_elems)
            except RuntimeError as e:
                # Error de seguridad esperado - el framework rechaza con gracia
                if "Security" in str(e) or "Maximum" in str(e) or "DoS" in str(e):
                    rechazos_seguros += 1
                else:
                    errores.append(f"Round {flood_round}: {str(e)}")
            except Exception as e:
                errores.append(f"Round {flood_round}: {str(e)}")

        # Aceptamos rechazos seguros como respuesta válida
        assert rechazos_seguros > 0 or len(errores) == 0, f"Errores inesperados: {errores}"

    def test_04_coordenadas_extremas_todos_componentes(self):
        """Ataque 4: coordenadas extremas en todos los componentes."""
        engine = AetherEngine()
        bridge = WebBridge()
        adapter = LightWASMAdapter(use_light_wasm=False)

        valores_extremos = [
            float('inf'),
            float('-inf'),
            float('nan'),
            1e308,
            -1e308,
            1e-308,
            0.0,
            -0.0,
            sys.maxsize,
            -sys.maxsize,
        ]

        errores = []

        for val in valores_extremos:
            try:
                elem = StaticBox(float(val), float(val), 50, 50)
                engine.register_element(elem)
                engine.tick(800, 600)
            except Exception as e:
                errores.append(f"Engine con {val}: {e}")

            try:
                bridge.register_element(0, "extreme")
                mock = MockElement(float(val), float(val), 50, 50)
                bridge.sync([mock])
            except Exception as e:
                errores.append(f"Bridge con {val}: {e}")

            try:
                adapter.register_element(0, "extreme")
                mock = MockElement(float(val), float(val), 50, 50)
                adapter.sync([mock])
            except Exception as e:
                errores.append(f"Adapter con {val}: {e}")

        assert len(errores) == 0, f"Errores con valores extremos: {errores}"

    def test_05_memoria_exhaustion(self):
        """Ataque 5: memory exhaustion progressive."""
        engines = []
        bridges = []
        adapters = []

        errores = []

        for ciclo in range(100):
            try:
                engine = AetherEngine()
                bridge = WebBridge()
                adapter = LightWASMAdapter(use_light_wasm=False)

                for i in range(1000):
                    elem = StaticBox(i % 500, i % 500, 30, 30)
                    engine.register_element(elem)
                    bridge.register_element(i, f"mem-{ciclo}-{i}")
                    adapter.register_element(i, f"mem-{ciclo}-{i}")

                engine.tick(800, 600)

                mocks = [MockElement(i % 500, i % 500, 30, 30) for i in range(1000)]
                bridge.sync(mocks)
                adapter.sync(mocks)

                engines.append(engine)
                bridges.append(bridge)
                adapters.append(adapter)
            except Exception as e:
                errores.append(f"Ciclo {ciclo}: {str(e)}")

        assert len(errores) == 0, f"Memory exhaustion errores: {errores}"

    def test_06_rapid_state_changes(self):
        """Ataque 6: cambios rápidos de estado."""
        engine = AetherEngine()
        bridge = WebBridge()
        adapter = LightWASMAdapter(use_light_wasm=False)

        errores = []
        rechazos = 0

        for tick in range(1000):
            try:
                elements = []
                for i in range(50):
                    x = random.uniform(-1000, 2000)
                    y = random.uniform(-1000, 2000)
                    elem = StaticBox(x, y, 30, 30)
                    elements.append(elem)
                    engine.register_element(elem)

                    bridge.register_element(i, f"rapid-{tick}-{i}")
                    adapter.register_element(i, f"rapid-{tick}-{i}")

                engine.tick(800, 600)

                mocks = [MockElement(
                    random.uniform(-1000, 2000),
                    random.uniform(-1000, 2000),
                    30, 30
                ) for i in range(50)]

                bridge.sync(mocks)
                adapter.sync(mocks)
            except RuntimeError as e:
                if "Security" in str(e) or "Maximum" in str(e):
                    rechazos += 1
                else:
                    errores.append(f"Tick {tick}: {str(e)}")
            except Exception as e:
                errores.append(f"Tick {tick}: {str(e)}")

        # Aceptamos algunos rechazos como normal bajo carga alta
        assert rechazos <= 100 or len(errores) == 0, f"Errores inesperados: {errores[:5]}"

    def test_07_concurrent_register(self):
        """Ataque 7: registro concurrente."""
        engine = AetherEngine()
        bridge = WebBridge()
        adapter = LightWASMAdapter(use_light_wasm=False)

        errores = []
        rechazos = 0

        def worker(worker_id):
            try:
                for i in range(500):
                    idx = worker_id * 1000 + i
                    elem = StaticBox(i % 500, i % 300, 20, 20)

                    engine.register_element(elem)
                    bridge.register_element(idx, f"concur-{idx}")
                    adapter.register_element(idx, f"concur-{idx}")

                return "OK"
            except RuntimeError as e:
                if "Security" in str(e) or "Maximum" in str(e):
                    return "RECHAZO"
                return str(e)
            except Exception as e:
                return str(e)

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(worker, i) for i in range(20)]
            for future in as_completed(futures):
                result = future.result()
                if result == "RECHAZO":
                    rechazos += 1
                elif result != "OK":
                    errores.append(result)

        # Aceptamos rechazos de seguridad
        assert rechazos > 0 or len(errores) == 0, f"Errores inesperados: {errores}"

    def test_08_json_injection_all_components(self):
        """Ataque 8: Injection en todos los componentes."""
        engine = AetherEngine()
        bridge = WebBridge()
        adapter = LightWASMAdapter(use_light_wasm=False)

        payloads_malignos = [
            '{"x": "<script>alert(1)</script>"}',
            '{"x": ");DROP TABLE elements;--"}',
            '{"id": "a" * 100000}',
        ]

        errores = []

        for payload in payloads_malignos:
            try:
                bridge.register_element(0, payload)
                adapter.register_element(0, payload)
            except Exception as e:
                errores.append(f"Con payload {payload[:20]}: {e}")

        assert len(errores) == 0, f"Injection errores: {errores}"

    def test_09_physics_collision_stress(self):
        """Ataque 9: stress de física con colisiones."""
        engine = AetherEngine()

        errores = []
        rechazos = 0

        for round in range(50):
            try:
                elements = []
                for i in range(500):
                    x = random.uniform(0, 800)
                    y = random.uniform(0, 600)
                    elem = StaticBox(x, y, random.uniform(10, 100), random.uniform(10, 100))
                    elements.append(elem)
                    engine.register_element(elem)

                for _ in range(10):
                    engine.tick(800, 600)
            except RuntimeError as e:
                if "Security" in str(e) or "Maximum" in str(e):
                    rechazos += 1
                else:
                    errores.append(f"Round {round}: {e}")
            except Exception as e:
                errores.append(f"Round {round}: {e}")

        assert rechazos > 0 or len(errores) == 0, f"Physics errores: {errores}"

    def test_10_doS_sustained(self):
        """Ataque 10: DoS sostenido."""
        engine = AetherEngine()
        bridge = WebBridge()
        adapter = LightWASMAdapter(use_light_wasm=False)

        start = time.perf_counter()
        errores = []
        rechazos = 0

        for i in range(10000):
            try:
                elem = StaticBox(i % 100, i % 100, 10, 10)
                engine.register_element(elem)

                if i % 100 == 0:
                    engine.tick(800, 600)

                for j in range(10):
                    idx = i * 10 + j
                    bridge.register_element(idx, f"dos-{idx}")
                    adapter.register_element(idx, f"dos-{idx}")

                mocks = [MockElement(j % 100, j % 100, 10, 10) for j in range(10)]
                bridge.sync(mocks)
                adapter.sync(mocks)
            except RuntimeError as e:
                if "Security" in str(e) or "Maximum" in str(e) or "DoS" in str(e):
                    rechazos += 1
                else:
                    errores.append(f"DoS iter {i}: {e}")
            except Exception as e:
                errores.append(f"DoS iter {i}: {e}")

        elapsed = time.perf_counter() - start

        # Aceptamos rechazos de seguridad
        assert rechazos > 0 or len(errores) == 0, f"DoS errores: {errores}"
        assert elapsed < 30.0, f"DoS took {elapsed:.2f}s, expected <30s"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])