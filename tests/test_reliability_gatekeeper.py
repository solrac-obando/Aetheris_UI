# Copyright 2026 Carlos Ivan Obando Aure
import numpy as np
import pytest
from core.engine import AetherEngine
from core.elements import DifferentialElement

class MockElement(DifferentialElement):
    def calculate_asymptotes(self, w, h):
        return np.array([0, 0, 100, 100], dtype=np.float32)

class ReliableElement(MockElement):
    pass

def test_nan_propagation_with_masking():
    """M16 Gatekeeper: El enmascaramiento no debe impedir que Aether-Guard limpie NaNs."""
    engine = AetherEngine()
    el = ReliableElement(0, 0, 100, 100)
    engine.register(el)
    
    # Inyectar un NaN en la velocidad
    el.tensor.velocity[0] = np.nan
    
    # Tick debe limpiar el NaN incluso si el elemento no está en 'sleep'
    engine.tick(800, 600)
    
    assert not np.isnan(el.tensor.velocity[0])
    assert el.tensor.velocity[0] == 0.0

def test_disposable_cleanup_extended():
    """Validar que los nuevos atributos no impactan el ciclo de vida de Disposable."""
    el = ReliableElement(0, 0, 100, 100)
    
    # Atributos M16 y M15
    assert hasattr(el, 'is_static')
    assert hasattr(el, 'is_sleeping')
    
    # Limpieza
    el.dispose()
    assert el.tensor is None

def test_numerical_stability_baldor():
    """Estabilidad Matemática (Baldor): Integración lineal bajo fricción constante.
    
    Verifica que la integración Euler sea estable y no diverja en 1000 iteraciones.
    """
    engine = AetherEngine()
    el = ReliableElement(0, 0, 100, 100)
    engine.register(el)
    
    # Aplicar un impulso inicial
    el.tensor.velocity[0] = 100.0
    
    # Correr 1000 iteraciones (viscosidad por defecto 0.1)
    for _ in range(1000):
        engine.tick(800, 600)
        
    # La fricción debería haber detenido el elemento casi por completo
    assert abs(el.tensor.velocity[0]) < 1e-4
    # La posición debe estar en un rango finito (no explotó al infinito)
    assert np.all(np.isfinite(el.tensor.state))
