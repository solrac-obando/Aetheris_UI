from typing import Tuple, Dict

ColorType = Tuple[float, float, float, float]

class ThemeManager:
    """M15: Gestor Central de Temas para Aetheris UI.
    
    Gestiona colores dinámicos preestablecidos sin requerir dependencias externas,
    garantizando 100% de seguridad y cero latencia.
    """
    
    _themes: Dict[str, Dict[str, ColorType]] = {
        "dark": {
            "background": (0.05, 0.05, 0.05, 1.0),
            "primary": (0.2, 0.5, 1.0, 1.0),
            "secondary": (0.3, 0.3, 0.3, 1.0),
            "text": (1.0, 1.0, 1.0, 1.0),
            "border": (0.4, 0.4, 0.4, 1.0)
        },
        "light": {
            "background": (0.95, 0.95, 0.95, 1.0),
            "primary": (0.1, 0.3, 0.8, 1.0),
            "secondary": (0.9, 0.9, 0.9, 1.0),
            "text": (0.1, 0.1, 0.1, 1.0),
            "border": (0.8, 0.8, 0.8, 1.0)
        }
    }
    
    active_theme: str = "dark"

    @classmethod
    def get_color(cls, key: str) -> ColorType:
        """Obtiene el color RGB+A correspondiente a la clave para el tema activo."""
        return cls._themes.get(cls.active_theme, cls._themes["dark"]).get(key, (1.0, 1.0, 1.0, 1.0))
    
    @classmethod
    def switch_theme(cls, theme_name: str) -> None:
        """Cambia el tema global."""
        if theme_name in cls._themes:
            cls.active_theme = theme_name
