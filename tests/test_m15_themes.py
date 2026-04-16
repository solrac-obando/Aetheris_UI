import math
from core.theme_manager import ThemeManager
from core.elements import SmartThemePanel

def test_theme_toggling_updates_color():
    """Valida que el cambio dinámico de tema funciona sin dependencias (M15)."""
    ThemeManager.active_theme = "dark"
    panel = SmartThemePanel(theme_key="primary")
    
    # 0.2 is the red channel of "primary" dark color
    assert math.isclose(panel.color[0], 0.2, abs_tol=1e-5)
    
    # Switch theme
    ThemeManager.active_theme = "light"
    # Should not auto-update yet without calling update_theme
    assert math.isclose(panel.color[0], 0.2, abs_tol=1e-5)
    
    panel.update_theme()
    # 0.1 is the red channel of "primary" light color
    assert math.isclose(panel.color[0], 0.1, abs_tol=1e-5)
    
def test_theme_manager_switch_class():
    """Valida la función switch_theme global."""
    ThemeManager.switch_theme("light")
    assert ThemeManager.active_theme == "light"
    # If the theme doesn't exist, it shouldn't change
    ThemeManager.switch_theme("non_existent")
    assert ThemeManager.active_theme == "light"
