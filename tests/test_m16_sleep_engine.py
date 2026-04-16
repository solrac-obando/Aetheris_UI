import pytest
import numpy as np
import time
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel

def test_static_element_masking():
    """Valida que un elemento is_static no integra física en el batch procesador."""
    engine = AetherEngine()
    
    # Crear 10 elementos para activar HPC Batch
    for _ in range(9):
        engine.register(StaticBox(0, 0, 10, 10))
        
    elem_static = StaticBox(100, 100, 50, 50)
    elem_static.is_static = True
    # Inyectar una velocidad ridícula. Si el objeto no está enmascarado, la integrará.
    elem_static.tensor.velocity = np.array([500.0, 500.0, 0.0, 0.0], dtype=np.float32)
    engine.register(elem_static)
    
    # Simular un frame
    engine.tick(800, 600)
    
    # Si la máscara de estáticos funciona, la velocidad la conservará o la volverá 0 en el integrador
    # pero NO se sumará a su posición state porque fue enmascarado
    assert float(elem_static.tensor.state[0]) == 100.0
    assert float(elem_static.tensor.state[1]) == 100.0
    
def test_auto_sleep_elements():
    """Valida que los elementos con bajísima velocidad entren en auto-sleep ahorrando overhead."""
    engine = AetherEngine()
    
    elem_sleepy = SmartPanel()
    elem_sleepy.tensor.velocity = np.array([0.01, 0.01, 0.0, 0.0], dtype=np.float32)
    engine.register(elem_sleepy)
    
    # Un SmartPanel normal tiene offset de padding (5%). Si duerme, NO calculará su asintota.
    engine.tick(1000, 1000)
    
    # Después de un tick, la velocidad baja del limit epsilon (0.05) debería haber puesto a sleep al panel
    assert elem_sleepy.is_sleeping == True
    
    # Despertador por fuerza de la naturaleza (ej: gravedad/input)
    elem_sleepy.tensor.velocity[0] = 100.0
    engine.tick(1000, 1000)
    
    assert elem_sleepy.is_sleeping == False
