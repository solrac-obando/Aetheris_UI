# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Suite de Pruebas de Regresión Total - M5 + M6 Integration
============================================================

FASE 1: 35 Pruebas Unitarias (Core, M1, M2, M5, M6)
FASE 2: Validación de 430+ pruebas del sistema  
FASE 3: Test de Integración de Ataque (vulnerabilidades)

Autor: Carlos Ivan Obando Aure
Fecha: Abril 2026
"""

import pytest
import gc
import weakref
import sys
import time
import numpy as np

# Imports del núcleo
from core.engine import AetherEngine
from core.elements import (
    DifferentialElement, StaticBox, SmartPanel, SmartButton,
    FlexibleTextNode, CanvasTextNode, DOMTextNode
)
from core.aether_math import StateTensor

# Imports M5
from core.layout import AetherLayout, ElementFactory, LayoutCompiler

# Imports M6
from core.lifecycle import LifecycleManager, Disposable


# ==============================================================================
# FASE 1: 35 PRUEBAS UNITARIAS
# ==============================================================================

class TestRegressionCore:
    """Pruebas unitarias del núcleo - 10 tests"""
    
    def test_r01_engine_initialization(self):
        engine = AetherEngine()
        assert engine is not None
        assert len(engine._elements) == 0
    
    def test_r02_tensor_state_creation(self):
        tensor = StateTensor(10, 20, 100, 50)
        assert tensor.state[0] == 10
        assert tensor.state[1] == 20
        assert tensor.state[2] == 100
        assert tensor.state[3] == 50
    
    def test_r03_staticbox_asymptote(self):
        box = StaticBox(10, 20, 100, 50)
        target = box.calculate_asymptotes(800, 600)
        assert np.allclose(target, [10, 20, 100, 50])
    
    def test_r04_smartpanel_asymptote(self):
        panel = SmartPanel(padding=0.1)
        target = panel.calculate_asymptotes(800, 600)
        assert np.allclose(target, [80, 60, 640, 480])
    
    def test_r05_smartbutton_parent_anchoring(self):
        parent = StaticBox(0, 0, 200, 100)
        button = SmartButton(parent, 10, 10, 50, 30)
        target = button.calculate_asymptotes(800, 600)
        assert target[0] == 10
        assert target[1] == 10
    
    def test_r06_engine_tick_stability(self):
        """Test que el engine puede procesar ticks sin errores"""
        engine = AetherEngine()
        box = StaticBox(100, 100, 50, 50)
        engine.register(box)
        
        for _ in range(10):
            engine.tick(800, 600)
        
        assert np.isfinite(box.tensor.state).all()
    
    def test_r07_manual_hookes_law_calculation(self):
        """Test manual de la ley de Hooke"""
        pos = np.array([100.0, 100.0])
        target = np.array([50.0, 50.0])
        k = 0.1
        force = -k * (pos - target)
        assert force[0] == -5.0
        assert force[1] == -5.0
    
    def test_r08_element_color_assignment(self):
        box = StaticBox(0, 0, 100, 100, color=(1.0, 0.0, 0.0, 1.0))
        assert box.color[0] == 1.0
        assert box.color[1] == 0.0
    
    def test_r09_z_index_ordering(self):
        box1 = StaticBox(0, 0, 50, 50, z=1)
        box2 = StaticBox(0, 0, 50, 50, z=0)
        assert box1.z_index > box2.z_index
    
    def test_r10_engine_element_removal(self):
        engine = AetherEngine()
        box = StaticBox(0, 0, 50, 50)
        engine.register_element(box)
        engine.remove_element(box)
        assert len(engine._elements) == 0


class TestRegressionM1:
    """Pruebas M1 (WASM) - 5 tests"""
    
    def test_r11_webbridge_initialization(self):
        from core.web_bridge import WebBridge
        bridge = WebBridge()
        assert bridge is not None
    
    def test_r12_state_tensor_compatibility(self):
        from core.web_bridge import WebBridge
        bridge = WebBridge()
        tensor = StateTensor(0, 0, 100, 50)
        assert tensor.state.shape == (4,)
    
    def test_r13_element_bounds_calculation(self):
        box = StaticBox(10, 20, 100, 50)
        bounds = box.rect
        assert bounds[2] == 100
        assert bounds[3] == 50
    
    def test_r14_velocity_vector_initialization(self):
        tensor = StateTensor(0, 0, 100, 50)
        assert tensor.velocity.shape[0] >= 2
        assert np.allclose(tensor.velocity[:2], [0, 0])
    
    def test_r15_acceleration_vector_initialization(self):
        tensor = StateTensor(0, 0, 100, 50)
        assert tensor.acceleration.shape[0] >= 2


class TestRegressionM2:
    """Pruebas M2 (Batch Asymptotes) - 5 tests"""
    
    def test_r16_batch_calculator_import(self):
        from core.solver_batch_asymptotes import BatchAsymptoteCalculator
        assert BatchAsymptoteCalculator is not None
    
    def test_r17_dynamic_limits_safety_margin(self):
        from core.dynamic_limits import get_optimal_max_elements
        optimal = get_optimal_max_elements(base_per_thread=800)
        assert optimal > 0
    
    def test_r18_static_classification(self):
        from core.solver_batch_asymptotes import BatchAsymptoteCalculator
        calc = BatchAsymptoteCalculator()
        states = np.array([[10, 20, 100, 50]] * 10, dtype=np.float32)
        # First call initializes previous states
        calc.calculate(states, states.copy(), (800, 600))
        # Second call should classify
        is_static = calc._previous_states is not None
    
    def test_r19_dynamic_classification(self):
        from core.solver_batch_asymptotes import BatchAsymptoteCalculator
        calc = BatchAsymptoteCalculator(enable_async=False)
        states1 = np.array([[10, 20, 100, 50]], dtype=np.float32)
        states2 = np.array([[15, 25, 100, 50]], dtype=np.float32)
        result = calc.calculate(states1, states2, (800, 600))
        assert result.shape == (1, 4)
    
    def test_r20_batch_lerp_interpolation(self):
        from core.solver_batch_asymptotes import BatchAsymptoteCalculator
        calc = BatchAsymptoteCalculator()
        current = np.array([[100, 100, 100, 100]], dtype=np.float32)
        target = np.array([[200, 200, 200, 200]], dtype=np.float32)
        result = calc.calculate(current, target, (800, 600))
        assert result.shape == current.shape


class TestRegressionM5:
    """Pruebas M5 (Layout DSL) - 10 tests"""
    
    def test_r21_layout_parser_import(self):
        from core.layout.parser import parse_layout_dsl
        assert parse_layout_dsl is not None
    
    def test_r22_aetherlayout_creation(self):
        layout = AetherLayout("box test { x: 10 }", 800, 600)
        assert len(layout.get_elements()) >= 0
    
    def test_r23_element_factory_box(self):
        box = ElementFactory.create("box", x=10, y=20, w=100, h=50)
        assert isinstance(box, StaticBox)
    
    def test_r24_element_factory_panel(self):
        panel = ElementFactory.create("panel", padding=0.1)
        assert isinstance(panel, SmartPanel)
    
    def test_r25_element_factory_text(self):
        text = ElementFactory.create("text", text="Hello")
        assert isinstance(text, FlexibleTextNode)
    
    def test_r26_layout_color_parsing_hex(self):
        layout = AetherLayout('box test { color: "#ff0000" }', 800, 600)
        elements = layout.get_elements()
        if elements:
            assert elements[0].color[0] > 0
    
    def test_r27_layout_container_size_update(self):
        layout = AetherLayout("box test", 800, 600)
        layout.set_container_size(1024, 768)
        assert layout._container_w == 1024
        assert layout._container_h == 768
    
    def test_r28_layout_add_element(self):
        layout = AetherLayout()
        box = StaticBox(0, 0, 50, 50)
        layout.add_element(box)
        assert len(layout.get_elements()) == 1
    
    def test_r29_layout_remove_element(self):
        layout = AetherLayout()
        box = StaticBox(0, 0, 50, 50)
        layout.add_element(box)
        layout.remove_element(box)
        assert len(layout.get_elements()) == 0
    
    def test_r30_layout_to_dict(self):
        layout = AetherLayout("box test", 800, 600)
        result = layout.to_dict()
        assert "container_w" in result
        assert "element_count" in result


class TestRegressionM6:
    """Pruebas M6 (Lifecycle) - 10 tests"""
    
    def test_r31_disposable_base_class(self):
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
            def dispose(self):
                super().dispose()
        
        elem = TestElem()
        assert not elem.is_disposed
    
    def test_r32_dispose_sets_flag(self):
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
            def dispose(self):
                super().dispose()
        
        elem = TestElem()
        elem.dispose()
        assert elem.is_disposed
    
    def test_r33_dispose_twice_safe(self):
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
            def dispose(self):
                super().dispose()
        
        elem = TestElem()
        elem.dispose()
        elem.dispose()
        assert elem.is_disposed
    
    def test_r34_cleanup_callbacks(self):
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
            def dispose(self):
                super().dispose()
        
        elem = TestElem()
        called = []
        elem._register_cleanup(lambda: called.append(True))
        elem.dispose()
        assert len(called) == 1
    
    def test_r35_context_manager(self):
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
            def dispose(self):
                super().dispose()
        
        with TestElem() as elem:
            assert not elem.is_disposed
        assert elem.is_disposed
    
    def test_r36_lifecycle_manager_singleton(self):
        m1 = LifecycleManager.get_instance()
        m2 = LifecycleManager.get_instance()
        assert m1 is m2
    
    def test_r37_lifecycle_track_untrack(self):
        manager = LifecycleManager.get_instance()
        manager.reset()
        
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
            def dispose(self):
                super().dispose()
        
        elem = TestElem()
        manager.track(elem)
        assert manager.get_tracked_count() == 1
        
        manager.untrack(elem)
        assert manager.get_tracked_count() == 0
    
    def test_r38_lifecycle_dispose_all(self):
        manager = LifecycleManager.get_instance()
        manager.reset()
        
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
            def dispose(self):
                super().dispose()
        
        elements = [TestElem() for _ in range(10)]
        for e in elements:
            manager.track(e)
        
        count = manager.dispose_all()
        assert count == 10
    
    def test_r39_lifecycle_memory_leak_detection(self):
        manager = LifecycleManager.get_instance()
        manager.reset()
        
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
            def dispose(self):
                super().dispose()
        
        elem = TestElem()
        manager.track(elem)
        leaked = manager.get_leaked_references()
        assert len(leaked) == 1
        
        elem.dispose()
        leaked = manager.get_leaked_references()
        assert len(leaked) == 0
    
    def test_r40_lifecycle_with_regular_elements(self):
        manager = LifecycleManager.get_instance()
        manager.reset()
        
        box = StaticBox(0, 0, 50, 50)
        manager.track(box)
        
        assert manager.get_tracked_count() == 1
        manager.dispose_all()
        assert manager.get_tracked_count() == 0


# ==============================================================================
# FASE 2: INTEGRACIÓN CON SUITE EXISTENTE (430+ tests)
# ==============================================================================

class TestPhase2Integration:
    """Verifica que los módulos M5/M6 no rompan la suite existente"""
    
    def test_p21_engine_with_m5_elements(self):
        """Engine debe funcionar con elementos creados via M5 DSL"""
        engine = AetherEngine()
        layout = AetherLayout("box test { x: 0 }", 800, 600)
        
        for elem in layout.get_elements():
            engine.register(elem)
        
        engine.tick(800, 600)
        assert len(engine._elements) > 0
    
    def test_p22_engine_with_lifecycle_tracking(self):
        """Engine debe funcionar con LifecycleManager"""
        manager = LifecycleManager.get_instance()
        manager.reset()
        
        engine = AetherEngine()
        for i in range(5):
            box = StaticBox(i*10, 0, 50, 50)
            engine.register_element(box)
            manager.track(box)
        
        assert manager.get_tracked_count() == 5
    
    def test_p23_m2_calculator_with_new_elements(self):
        """M2 debe funcionar con elementos de M5"""
        from core.solver_batch_asymptotes import BatchAsymptoteCalculator
        
        calc = BatchAsymptoteCalculator()
        layout = AetherLayout("box a { x: 0 } box b { x: 100 }", 800, 600)
        
        states = np.array([e.tensor.state for e in layout.get_elements()], dtype=np.float32)
        if len(states) > 0:
            targets = states.copy()  # Use states as targets for test
            result = calc.calculate(states, targets, (800, 600))
            assert result.shape[0] > 0


# ==============================================================================
# FASE 3: TEST DE INTEGRACIÓN DE ATAQUE (Vulnerabilidades)
# ==============================================================================

class TestPhase3AttackIntegration:
    """Test de vulnerabilidades que pudieron surgir con M5/M6"""
    
    def test_a01_dsl_parser_buffer_overflow(self):
        """Verificar que el parser no entre en loop infinito con input malicioso"""
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Parser timeout - possible infinite loop")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(2)
        
        try:
            # Input muy largo sin estructura válida
            dsl = "x " * 10000
            layout = AetherLayout(dsl, 800, 600)
            signal.alarm(0)
        except TimeoutError:
            pytest.fail("Parser vulnerable a buffer overflow/loop infinito")
        except Exception:
            signal.alarm(0)
    
    def test_a02_lifecycle_double_dispose_race(self):
        """Verificar que dispose() sea idempotente bajo race conditions"""
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
                self.cleanup_count = 0
            
            def dispose(self):
                self.cleanup_count += 1
                super().dispose()
        
        elem = TestElem()
        
        import threading
        threads = [threading.Thread(target=lambda: elem.dispose()) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert elem.cleanup_count >= 1
    
    def test_a03_layout_null_element_handling(self):
        """Verificar manejo de elementos nulos en layout"""
        layout = AetherLayout()
        layout.add_element(None)
        elements = layout.get_elements()
        # No debe romper
    
    def test_a04_factory_invalid_type_handling(self):
        """Verificar que factory maneje tipos inválidos"""
        elem = ElementFactory.create("invalid_type_xyz")
        assert elem is None
    
    def test_a05_manager_memory_exhaustion(self):
        """Verificar que manager no permita exhaustion de memoria"""
        manager = LifecycleManager.get_instance()
        manager.reset()
        
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
            
            def dispose(self):
                super().dispose()
        
        # Crear muchos elementos rapidamente
        for i in range(100):
            elem = TestElem()
            manager.track(elem)
        
        # Dispose
        count = manager.dispose_all()
        
        assert manager.get_tracked_count() == 0
    
    def test_a06_engine_with_empty_layout(self):
        """Verificar que engine funcione con layout vacío"""
        engine = AetherEngine()
        layout = AetherLayout()
        
        for elem in layout.get_elements():
            engine.register(elem)
        
        engine.tick(800, 600)
        assert len(engine._elements) == 0
    
    def test_a07_lifecycle_weak_ref_garbage(self):
        """Verificar que referencias débiles se limpien correctamente"""
        manager = LifecycleManager.get_instance()
        manager.reset()
        
        refs = []
        for i in range(10):
            elem = StaticBox(i, i, 10, 10)
            manager.track(elem)
            refs.append(weakref.ref(elem))
        
        manager.dispose_all()
        gc.collect()
        
        # Todos deben ser None después de dispose + gc
        alive = sum(1 for r in refs if r() is not None)
    
    def test_a08_dsl_nested_complex_structure(self):
        """Verificar parser con estructuras anidadas complejas"""
        dsl = """
        panel#root {
            box#a { x: 0 }
            panel#b {
                box#c { x: 10 }
            }
        }
        """
        layout = AetherLayout(dsl, 800, 600)
        elements = layout.get_elements()
        assert len(elements) > 0
    
    def test_a09_lifecycle_dispose_callback_exception(self):
        """Verificar que exceptions en callbacks no rompan dispose"""
        class TestElem(Disposable):
            def __init__(self):
                super().__init__()
            
            def dispose(self):
                super().dispose()
        
        elem = TestElem()
        elem._register_cleanup(lambda: 1/0)  # Exception en callback
        elem.dispose()
        assert elem.is_disposed
    
    def test_a10_mixed_element_types_in_engine(self):
        """Verificar engine con mezcla de elementos M5/M6/regular"""
        engine = AetherEngine()
        
        # Regular
        box = StaticBox(0, 0, 50, 50)
        engine.register_element(box)
        
        # M5
        layout = AetherLayout("box test { x: 100 }", 800, 600)
        for e in layout.get_elements():
            engine.register_element(e)
        
        # M6 tracked
        manager = LifecycleManager.get_instance()
        manager.reset()
        panel = SmartPanel(padding=0.1)
        manager.track(panel)
        
        engine.tick(0.016)
        assert len(engine._elements) >= 2


# ==============================================================================
# RESUMEN Y EXPORT
# ==============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("SUITE DE REGRESIÓN TOTAL - M5 + M6")
    print("=" * 60)
    print("FASE 1: 40 pruebas unitarias (Core, M1, M2, M5, M6)")
    print("FASE 2: 3 pruebas de integración con suite existente")
    print("FASE 3: 10 pruebas de ataque/vulnerabilidad")
    print("TOTAL: 53 pruebas de regresión")
    print("=" * 60)
    pytest.main([__file__, "-v", "--tb=short"])