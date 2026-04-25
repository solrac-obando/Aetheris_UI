"""
Aetheris UI - Demo Tkinter Optimizada.
Carga 100 elementos de la DB de Odyssey y los renderiza a 60FPS
con controles nativos de Tkinter en el panel lateral.
"""
import sys
import os
import tkinter as tk
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import AetherEngine
from core.elements import StaticBox
from core.tkinter_renderer import TkinterRenderer, color_to_hex


class OptimizedTkinterRenderer(TkinterRenderer):
    """Renderizador con caché de colores para 60FPS sostenidos."""

    def __init__(self):
        super().__init__()
        self._color_cache = {}
        self._supernova_trigger = False
        self._genre_focus = None

    def _cached_color(self, color_array):
        key = (round(float(color_array[0]), 3),
               round(float(color_array[1]), 3),
               round(float(color_array[2]), 3))
        if key not in self._color_cache:
            self._color_cache[key] = color_to_hex(color_array)
        return self._color_cache[key]

    def render_frame(self, data_buffer, metadata=None):
        if self._canvas is None or len(data_buffer) == 0:
            return

        for i, elem in enumerate(data_buffer):
            rect = elem['rect']
            color = elem['color']
            x1, y1 = float(rect[0]), float(rect[1])
            x2, y2 = x1 + float(rect[2]), y1 + float(rect[3])
            hc = self._cached_color(color)

            if i in self._item_tags:
                self._canvas.coords(self._item_tags[i], x1, y1, x2, y2)
                self._canvas.itemconfig(self._item_tags[i], fill=hc)
            else:
                self._item_tags[i] = self._canvas.create_rectangle(
                    x1, y1, x2, y2, fill=hc, outline="")

        # Limpiar items sobrantes
        to_del = [k for k in self._item_tags if k >= len(data_buffer)]
        for k in to_del:
            self._canvas.delete(self._item_tags.pop(k))

    def _update(self):
        if not self._running or self._engine is None or self._canvas is None:
            return
        try:
            # Gravedad de género
            if self._genre_focus:
                self._engine._apply_genre_orbit(
                    {'action': 0, 'scifi': 1, 'drama': 2, 'comedy': 3}.get(self._genre_focus, 0),
                    0.05, self._width / 2, self._height / 2)

            # Supernova
            if self._supernova_trigger:
                self._engine._trigger_supernova(self._width / 2, self._height / 2)
                self._supernova_trigger = False

            data = self._engine.tick(self._width, self._height)
            self.clear_screen((0.05, 0.05, 0.1, 1.0))
            self.render_frame(data)
            self.swap_buffers()

            if self._running:
                self._root.after(16, self._update)
        except tk.TclError:
            self._running = False
        except Exception as e:
            print(f"Error en loop: {e}")
            self._running = False


def create_simple_engine(n=80):
    """Crea un motor con N elementos de colores aleatorios si no hay DB."""
    engine = AetherEngine()
    np.random.seed(42)
    for i in range(n):
        size = 15.0 + np.random.random() * 60.0
        x = 100 + np.random.random() * 700
        y = 50 + np.random.random() * 500
        r, g, b = np.random.random(), np.random.random(), np.random.random()
        box = StaticBox(x=x, y=y, w=size, h=size, color=(r, g, b, 0.9), z=i)
        engine.register_element(box)
    return engine


def main():
    renderer = OptimizedTkinterRenderer()
    renderer.init_window(1000, 700, "Aetheris UI – Tkinter Optimizado")

    # Panel lateral
    side = tk.Frame(renderer._root, width=200, bg="#1a1a2e")
    side.pack(side=tk.LEFT, fill=tk.Y)
    side.pack_propagate(False)
    renderer._canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    tk.Label(side, text="✦ Aetheris UI ✦", fg="#e94560", bg="#1a1a2e",
             font=("Arial", 14, "bold")).pack(pady=(20, 5))
    tk.Label(side, text="Motor de Físicas en\nTkinter a 60 FPS", fg="#8899aa",
             bg="#1a1a2e", font=("Arial", 9)).pack(pady=(0, 15))

    # Intentar cargar Odyssey DB; si falla, usar elementos simples
    engine = None
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo', 'odyssey.db')
    try:
        from demo.odyssey_master import create_odyssey_engine
        engine = create_odyssey_engine(db_path)
        print(f"Motor cargado con {engine.element_count} elementos de Odyssey DB")
    except Exception as e:
        print(f"No se pudo cargar Odyssey DB ({e}), usando elementos simples...")
        engine = create_simple_engine(80)
        print(f"Motor cargado con {engine.element_count} elementos generados")

    # Botones de control
    def toggle_genre(genre):
        if renderer._genre_focus == genre:
            renderer._genre_focus = None
        else:
            renderer._genre_focus = genre

    btn_style = {"bg": "#16213e", "fg": "white", "activebackground": "#0f3460",
                 "activeforeground": "white", "bd": 0, "relief": tk.FLAT,
                 "font": ("Arial", 10)}

    tk.Button(side, text="🌌 Gravedad: Sci-Fi",
              command=lambda: toggle_genre('scifi'), **btn_style).pack(fill=tk.X, padx=10, pady=3)
    tk.Button(side, text="⚔️ Gravedad: Acción",
              command=lambda: toggle_genre('action'), **btn_style).pack(fill=tk.X, padx=10, pady=3)
    tk.Button(side, text="🎭 Gravedad: Drama",
              command=lambda: toggle_genre('drama'), **btn_style).pack(fill=tk.X, padx=10, pady=3)
    tk.Button(side, text="😂 Gravedad: Comedia",
              command=lambda: toggle_genre('comedy'), **btn_style).pack(fill=tk.X, padx=10, pady=3)

    tk.Frame(side, height=2, bg="#e94560").pack(fill=tk.X, padx=10, pady=15)

    tk.Button(side, text="💥 SUPERNOVA",
              command=lambda: setattr(renderer, '_supernova_trigger', True),
              bg="#e94560", fg="white", activebackground="#c81d4e",
              font=("Arial", 11, "bold"), bd=0, relief=tk.FLAT).pack(fill=tk.X, padx=10, pady=3)

    # Info en la parte inferior
    info = tk.Label(side, text=f"Elementos: {engine.element_count}\nTarget: 60 FPS (~16ms)",
                    fg="#556677", bg="#1a1a2e", font=("Arial", 8), justify=tk.LEFT)
    info.pack(side=tk.BOTTOM, pady=10, padx=10)

    # Arrancar
    renderer.start(engine)


if __name__ == "__main__":
    main()
