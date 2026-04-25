"""
Aetheris Disk Analyzer — Herramienta real de análisis de disco.
Escanea un directorio y visualiza cada archivo como una entidad física
cuyo tamaño visual corresponde al peso real del archivo en disco.

Uso: python3 aether_disk_analyzer.py [ruta_opcional]
Si no se pasa ruta, escanea el propio repositorio de Aetheris UI.
"""
import sys
import os
import tkinter as tk
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.engine import AetherEngine
from core.elements import StaticBox
from core.tkinter_renderer import TkinterRenderer, color_to_hex

# ─── Configuración ────────────────────────────────────────────────
CANVAS_W = 900
CANVAS_H = 700
MAX_FILES = 200
IGNORE_DIRS = {'node_modules', '__pycache__', '.git', 'venv', 'env', '.mcp',
               'tests_backup', '.mypy_cache', '.pytest_cache'}

# ─── Colores por extensión ────────────────────────────────────────
EXT_COLORS = {
    '.py':   (0.30, 0.65, 1.00, 0.90),
    '.js':   (0.95, 0.85, 0.25, 0.90),
    '.ts':   (0.20, 0.50, 0.85, 0.90),
    '.tsx':  (0.25, 0.55, 0.90, 0.90),
    '.html': (0.92, 0.45, 0.20, 0.90),
    '.css':  (0.25, 0.75, 0.95, 0.90),
    '.json': (0.40, 0.80, 0.40, 0.90),
    '.md':   (0.80, 0.80, 0.80, 0.90),
    '.txt':  (0.65, 0.65, 0.65, 0.90),
    '.sql':  (0.85, 0.55, 0.20, 0.90),
    '.yml':  (0.60, 0.40, 0.80, 0.90),
    '.yaml': (0.60, 0.40, 0.80, 0.90),
    '.toml': (0.55, 0.45, 0.75, 0.90),
    '.cfg':  (0.55, 0.45, 0.75, 0.90),
    '.sh':   (0.45, 0.75, 0.45, 0.90),
    '.jpg':  (0.80, 0.30, 0.80, 0.90),
    '.png':  (0.80, 0.30, 0.80, 0.90),
    '.svg':  (0.75, 0.35, 0.75, 0.90),
    '.db':   (0.90, 0.25, 0.25, 0.90),
    '.lock': (0.90, 0.20, 0.20, 0.90),
    '.log':  (0.70, 0.50, 0.30, 0.90),
    '.rst':  (0.70, 0.70, 0.50, 0.90),
}
DEFAULT_COLOR = (0.50, 0.50, 0.50, 0.90)


def format_size(size_bytes: int) -> str:
    if size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


def scan_directory(path: str):
    """Escanea un directorio y retorna lista de dicts con info de archivos."""
    files = []
    for root_dir, dirs, filenames in os.walk(path):
        # Filtrar directorios ignorados
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fname in filenames:
            fpath = os.path.join(root_dir, fname)
            try:
                size = os.path.getsize(fpath)
                if size > 0:
                    _, ext = os.path.splitext(fname)
                    rel = os.path.relpath(fpath, path)
                    files.append({
                        'name': fname,
                        'rel_path': rel,
                        'ext': ext.lower(),
                        'size': size,
                    })
            except (OSError, PermissionError):
                pass
            if len(files) >= MAX_FILES:
                break
        if len(files) >= MAX_FILES:
            break

    # Ordenar por tamaño descendente para que los grandes se vean primero
    files.sort(key=lambda f: f['size'], reverse=True)
    return files


def build_engine(files: list) -> AetherEngine:
    """Crea un AetherEngine con un StaticBox por cada archivo."""
    engine = AetherEngine()
    if not files:
        return engine

    sizes = [f['size'] for f in files]
    min_s, max_s = min(sizes), max(sizes)
    log_min = np.log1p(min_s)
    log_max = np.log1p(max_s)
    log_range = max(log_max - log_min, 1.0)

    # Distribuir en cuadrícula expandida desde el centro
    n = len(files)
    cols = int(np.ceil(np.sqrt(n)))

    for idx, f in enumerate(files):
        # Tamaño visual proporcional al log del peso (para que no dominen los gigantes)
        t = (np.log1p(f['size']) - log_min) / log_range
        box_size = 12.0 + t * 80.0

        color = EXT_COLORS.get(f['ext'], DEFAULT_COLOR)

        # Posición inicial tipo cuadrícula con algo de ruido
        col = idx % cols
        row = idx // cols
        spacing = 95.0
        x = 50 + col * spacing + np.random.uniform(-10, 10)
        y = 30 + row * spacing + np.random.uniform(-10, 10)

        box = StaticBox(x=x, y=y, w=box_size, h=box_size, color=color, z=idx)
        box._file_info = f  # Adjuntar metadatos
        engine.register_element(box)

    return engine


class DiskRenderer(TkinterRenderer):
    """Renderer que soporta hover para mostrar info de archivos."""

    def __init__(self):
        super().__init__()
        self._color_cache = {}
        self._hover_label = None
        self._file_elements = []  # referencia a engine._elements

    def _cached_color(self, c):
        key = (round(float(c[0]), 3), round(float(c[1]), 3), round(float(c[2]), 3))
        if key not in self._color_cache:
            self._color_cache[key] = color_to_hex(c)
        return self._color_cache[key]

    def render_frame(self, data_buffer, metadata=None):
        if self._canvas is None or len(data_buffer) == 0:
            return
        for i, elem in enumerate(data_buffer):
            r = elem['rect']
            x1, y1 = float(r[0]), float(r[1])
            x2, y2 = x1 + float(r[2]), y1 + float(r[3])
            hc = self._cached_color(elem['color'])
            if i in self._item_tags:
                self._canvas.coords(self._item_tags[i], x1, y1, x2, y2)
                self._canvas.itemconfig(self._item_tags[i], fill=hc)
            else:
                self._item_tags[i] = self._canvas.create_rectangle(
                    x1, y1, x2, y2, fill=hc, outline="")
        to_del = [k for k in self._item_tags if k >= len(data_buffer)]
        for k in to_del:
            self._canvas.delete(self._item_tags.pop(k))

    def _update(self):
        if not self._running or self._engine is None or self._canvas is None:
            return
        try:
            data = self._engine.tick(self._width, self._height)
            self.clear_screen((0.08, 0.08, 0.12, 1.0))
            self.render_frame(data)
            self.swap_buffers()
            if self._running:
                self._root.after(16, self._update)
        except tk.TclError:
            self._running = False
        except Exception as e:
            print(f"Error: {e}")
            self._running = False

    def on_hover(self, event):
        """Detecta qué archivo está bajo el cursor y actualiza el label."""
        mx, my = event.x, event.y
        for elem in self._file_elements:
            s = elem.tensor.state
            if s[0] <= mx <= s[0] + s[2] and s[1] <= my <= s[1] + s[3]:
                if hasattr(elem, '_file_info'):
                    f = elem._file_info
                    self._hover_label.config(
                        text=f"📄 {f['name']}\n📁 {f['rel_path']}\n💾 {format_size(f['size'])}")
                return
        self._hover_label.config(text="Pasa el ratón sobre\nuna caja para ver\ndetalles del archivo")


def main():
    # ── 1. Determinar qué directorio escanear ──
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        scan_path = os.path.abspath(sys.argv[1])
    else:
        # Por defecto: el propio repositorio de Aetheris UI
        scan_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    print(f"Escaneando: {scan_path}")
    files = scan_directory(scan_path)
    print(f"Encontrados: {len(files)} archivos")

    if not files:
        print("No se encontraron archivos. Saliendo.")
        return

    # ── 2. Construir motor con los archivos ──
    engine = build_engine(files)
    print(f"Motor inicializado con {engine.element_count} elementos físicos")

    # ── 3. Estadísticas rápidas ──
    total_size = sum(f['size'] for f in files)
    ext_counts = {}
    for f in files:
        ext_counts[f['ext']] = ext_counts.get(f['ext'], 0) + 1
    top_exts = sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)[:6]

    # ── 4. Construir UI ──
    renderer = DiskRenderer()
    renderer.init_window(CANVAS_W + 250, CANVAS_H,
                         f"Aetheris Disk Analyzer — {os.path.basename(scan_path)}")
    renderer._file_elements = engine._elements

    # Panel lateral
    side = tk.Frame(renderer._root, width=250, bg="#0d1117")
    side.pack(side=tk.LEFT, fill=tk.Y)
    side.pack_propagate(False)
    renderer._canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

    # Título
    tk.Label(side, text="⚛ Aetheris\nDisk Analyzer", fg="#58a6ff", bg="#0d1117",
             font=("Arial", 15, "bold"), justify=tk.CENTER).pack(pady=(18, 4))
    tk.Label(side, text=f"Ruta: .../{os.path.basename(scan_path)}",
             fg="#8b949e", bg="#0d1117", font=("Arial", 8)).pack(pady=(0, 12))

    # Separador
    tk.Frame(side, height=1, bg="#30363d").pack(fill=tk.X, padx=12)

    # Estadísticas
    tk.Label(side, text="📊 Estadísticas", fg="#c9d1d9", bg="#0d1117",
             font=("Arial", 11, "bold")).pack(pady=(12, 4), padx=12, anchor=tk.W)
    tk.Label(side, text=f"Archivos: {len(files)}\nPeso total: {format_size(total_size)}\n"
             f"Mayor: {format_size(files[0]['size'])} ({files[0]['name']})",
             fg="#8b949e", bg="#0d1117", font=("Arial", 9), justify=tk.LEFT,
             wraplength=220).pack(padx=12, anchor=tk.W)

    # Top extensiones
    tk.Frame(side, height=1, bg="#30363d").pack(fill=tk.X, padx=12, pady=10)
    tk.Label(side, text="🏷 Extensiones", fg="#c9d1d9", bg="#0d1117",
             font=("Arial", 11, "bold")).pack(padx=12, anchor=tk.W)
    ext_text = "\n".join(f"  {ext or '(sin ext)'}: {count} archivos" for ext, count in top_exts)
    tk.Label(side, text=ext_text, fg="#8b949e", bg="#0d1117", font=("Arial", 9),
             justify=tk.LEFT).pack(padx=12, anchor=tk.W, pady=(2, 0))

    # Leyenda de colores
    tk.Frame(side, height=1, bg="#30363d").pack(fill=tk.X, padx=12, pady=10)
    tk.Label(side, text="🎨 Leyenda", fg="#c9d1d9", bg="#0d1117",
             font=("Arial", 11, "bold")).pack(padx=12, anchor=tk.W)
    legend_items = [
        ("Python (.py)", "#4da6ff"), ("JavaScript (.js)", "#f2d93b"),
        ("HTML (.html)", "#eb7332"), ("CSS (.css)", "#40bff2"),
        ("Data (.json)", "#66cc66"), ("Docs (.md)", "#cccccc"),
        ("Config (.yml/.toml)", "#9966cc"), ("Otros", "#808080"),
    ]
    for name, color in legend_items:
        row = tk.Frame(side, bg="#0d1117")
        row.pack(padx=12, anchor=tk.W, pady=1)
        tk.Canvas(row, width=10, height=10, bg=color, highlightthickness=0).pack(side=tk.LEFT, padx=(0, 6))
        tk.Label(row, text=name, fg="#8b949e", bg="#0d1117", font=("Arial", 8)).pack(side=tk.LEFT)

    # Info hover (parte inferior)
    tk.Frame(side, height=1, bg="#30363d").pack(fill=tk.X, padx=12, pady=10)
    hover_lbl = tk.Label(side, text="Pasa el ratón sobre\nuna caja para ver\ndetalles del archivo",
                         fg="#f0c040", bg="#161b22", font=("Arial", 10),
                         justify=tk.LEFT, relief=tk.FLAT, padx=8, pady=8)
    hover_lbl.pack(fill=tk.X, padx=12, side=tk.BOTTOM, pady=(0, 12))
    renderer._hover_label = hover_lbl

    # Bind hover
    renderer._canvas.bind("<Motion>", renderer.on_hover)

    # ── 5. Arrancar el motor ──
    print("Iniciando visualización... ¡Pasa el ratón sobre las cajas!")
    renderer.start(engine)


if __name__ == "__main__":
    main()
