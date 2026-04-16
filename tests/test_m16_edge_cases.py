# Copyright 2026 Carlos Ivan Obando Aure
import numpy as np
import pytest
from core.engine import AetherEngine
from core.elements import StaticBox, DifferentialElement

class MockElement(DifferentialElement):
    def calculate_asymptotes(self, w, h):
        return np.array([0, 0, 100, 100], dtype=np.float32)

def test_wake_on_force():
    """M16: Un elemento en sleep debe despertar si se le aplica una fuerza externa."""
    engine = AetherEngine()
    el = MockElement(0, 0, 100, 100)
    engine.register(el)
    
    # Forzar sleep manualmente (simulando que se quedó quieto)
    el.tensor.velocity[:] = 0.0
    engine.tick(800, 600)
    assert el.is_sleeping is True
    
    # Aplicar fuerza externa
    el.tensor.apply_force(np.array([100.0, 0, 0, 0], dtype=np.float32))
    
    # El siguiente tick debe detectar movimiento (o intención de) y despertar
    engine.tick(800, 600)
    # NOTA: En la implementación actual, el "despertar" ocurre durante el SYNC
    # si la velocidad es > epsilon. 
    assert el.is_sleeping is False

def test_wake_on_drag():
    """M16: Un elemento en sleep debe despertar si el usuario empieza a arrastrarlo."""
    engine = AetherEngine()
    el = MockElement(0, 0, 100, 100)
    engine.register(el)
    
    el.tensor.velocity[:] = 0.0
    engine.tick(800, 600)
    assert el.is_sleeping is True
    
    # Simular drag
    engine.handle_pointer_down(10, 10) # Cae dentro del elemento
    
    # El tick durante el drag debe asegurar que no está durmiendo
    engine.tick(800, 600)
    assert el.is_sleeping is False
    engine.handle_pointer_up()

def test_static_immutability():
    """M16: Un elemento estático no debe moverse NUNCA, incluso con fuerzas masivas."""
    engine = AetherEngine()
    el = StaticBox(10, 10, 100, 100)
    el.is_static = True
    engine.register(el)
    
    initial_pos = el.tensor.state.copy()
    
    # Aplicar fuerza masiva (Baldor: "Magnitud infinita no altera lo inamovible")
    el.tensor.apply_force(np.array([1000000.0, 1000000.0, 0, 0], dtype=np.float32))
    
    for _ in range(10):
        engine.tick(800, 600)
        
    assert np.all(el.tensor.state == initial_pos)
    assert np.all(el.tensor.velocity == 0.0)

def test_mask_resizing_stress():
    """M16: El sistema de máscaras debe ser resiliente al cambio dinámico de elementos."""
    engine = AetherEngine()
    
    # Añadir 100 elementos
    for i in range(100):
        el = MockElement(0, 0, 10, 10)
        el.is_static = (i % 2 == 0)
        engine.register(el)
        
    engine.tick(800, 600)
    assert engine._static_mask.shape[0] == 100
    assert np.sum(engine._static_mask) == 50
    
    # Remover 50
    for _ in range(50):
        engine.remove(engine._elements[0])
        
    engine.tick(800, 600)
    assert engine._static_mask.shape[0] == 50
    assert len(engine._elements) == 50

def test_epsilon_boundary():
    """M16: Verificación de precisión matemática en el límite de epsilon."""
    engine = AetherEngine()
    el = MockElement(0, 0, 100, 100)
    el.sleep_epsilon = 1.0
    engine.register(el)
    
    # Velocidad justo debajo del límite (0.99 < 1.0)
    el.tensor.velocity = np.array([0.9, 0, 0, 0], dtype=np.float32) # mag = 0.9
    engine.tick(800, 600)
    assert el.is_sleeping is True
    
    # Velocidad justo encima del límite (1.01 > 1.0)
    el.tensor.velocity = np.array([1.1, 0, 0, 0], dtype=np.float32) # mag = 1.1
    engine.tick(800, 600)
    assert el.is_sleeping is False
