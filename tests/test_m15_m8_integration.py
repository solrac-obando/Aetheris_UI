import pytest
import numpy as np
from core.theme_manager import ThemeManager
from core.elements import SmartThemePanel

def test_bulk_theme_update():
    """M15: El cambio de tema global debe propagarse a todos los SmartThemePanels."""
    # Crear 100 paneles
    panels = [SmartThemePanel(padding=0.1) for _ in range(100)]
    
    # Asegurar que inicien con el color de Dark (por defecto)
    ThemeManager.switch_theme("dark")
    dark_primary = ThemeManager.get_color("primary")
    for p in panels:
        p.update_theme() # Forzar actualización inicial
        assert p._color == pytest.approx(np.array(dark_primary, dtype=np.float32))
        
    # Cambiar a Light
    ThemeManager.switch_theme("light")
    light_primary = ThemeManager.get_color("primary")
    
    # Notificar paneles (en una app real esto lo haría el sistema de eventos o el engine)
    for p in panels:
        p.update_theme()
        assert p._color == pytest.approx(np.array(light_primary, dtype=np.float32))

def test_theme_fallback():
    """M15: El sistema debe fallar a colores neutros/seguros si las claves son inválidas."""
    ThemeManager.active_theme = "invalid_theme"
    # Fallback a dark si el tema no existe
    assert ThemeManager.get_color("background") == (0.05, 0.05, 0.05, 1.0)
    
    ThemeManager.switch_theme("dark")
    # Fallback a blanco si la clave de color no existe
    assert ThemeManager.get_color("non_existent_key") == (1.0, 1.0, 1.0, 1.0)

def test_type_hint_runtime_validation():
    """M8: Validación de que los Type Hints no son solo cosméticos (Runtime check simple)."""
    # Aunque Python no obliga tipos en runtime, las clases deben manejar datos 
    # coherentes con sus anotaciones.
    p = SmartThemePanel(padding=0.5)
    assert isinstance(p._padding, float)
    
    # Verificar que el constructor de SmartThemePanel hereda y tipa correctamente
    from typing import get_type_hints
    hints = get_type_hints(SmartThemePanel.__init__)
    assert hints['padding'] == float
