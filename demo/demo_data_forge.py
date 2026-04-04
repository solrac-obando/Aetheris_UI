# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""Aether-Data Forge v1.0 — Functional Excel/CSV-to-UI physics data processor.

Bilingual (EN/ES), physics-driven data visualization with pandas integration.
"""
import os, sys, time, gc, json, threading
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from tkinter import Tk, filedialog

from core.engine import AetherEngine
from core.aether_math import StateTensor, MAX_VELOCITY, clamp_magnitude, EPSILON
from core.elements import DifferentialElement
from core.state_manager import StateManager

# ── Localization ───────────────────────────────────────────────────────────
LANG = {
    "en": {
        "title": "AETHER-DATA FORGE",
        "subtitle": "Excel/CSV → Physics Visualization",
        "open": "Open File",
        "sort": "Sort by Weight",
        "reset": "Reset View",
        "lang": "Español",
        "no_data": "No data loaded — open a CSV or Excel file",
        "rows": "rows",
        "cols": "columns",
        "stable": "Stable",
        "processing": "Processing",
        "error_title": "Error",
        "error_invalid": "Invalid or empty file",
        "error_format": "Unsupported format. Use .csv or .xlsx",
        "column": "Column",
        "value": "Value",
        "row": "Row",
        "mass": "Mass",
    },
    "es": {
        "title": "AETHER-DATA FORGE",
        "subtitle": "Excel/CSV → Visualización Física",
        "open": "Abrir Archivo",
        "sort": "Ordenar por Peso",
        "reset": "Restablecer Vista",
        "lang": "English",
        "no_data": "Sin datos — abre un archivo CSV o Excel",
        "rows": "filas",
        "cols": "columnas",
        "stable": "Estable",
        "processing": "Procesando",
        "error_title": "Error",
        "error_invalid": "Archivo inválido o vacío",
        "error_format": "Formato no soportado. Use .csv o .xlsx",
        "column": "Columna",
        "value": "Valor",
        "row": "Fila",
        "mass": "Masa",
    },
}

WIN_W, WIN_H = 1280.0, 720.0
MAX_ROWS = 100
TOOLBAR_H = 50.0
ELEMENT_SIZE = 14.0


# ── DataElement — physics-driven cell representation ──────────────────────
class DataElement(DifferentialElement):
    """Represents a single data cell as a physics element."""
    def __init__(self, x, y, value, col_name, row_idx, z=0):
        norm = max(0.0, min(1.0, value))
        mass = 0.2 + norm * 2.0
        size = ELEMENT_SIZE + norm * 8.0
        # Color: blue (low) → red (high) with glow
        r = np.float32(0.15 + norm * 0.75)
        g = np.float32(0.3 + (1.0 - abs(norm - 0.5) * 2.0) * 0.4)
        b = np.float32(0.85 - norm * 0.65)
        a = np.float32(0.5 + norm * 0.45)
        super().__init__(x, y, size, size, color=(r, g, b, a), z=z)
        self.value = value
        self.col_name = col_name
        self.row_idx = row_idx
        self.mass = mass
        self._target = np.array([x, y, size, size], dtype=np.float32)

    def calculate_asymptotes(self, cw, ch):
        return self._target.copy()


# ── DataForge Engine ──────────────────────────────────────────────────────
class DataForgeEngine:
    """Core engine: loads data, spawns physics elements, manages state."""
    def __init__(self):
        self.engine = AetherEngine()
        self.elements: List[DataElement] = []
        self.df: Optional[pd.DataFrame] = None
        self.numeric_cols: List[str] = []
        self.state_mgr = StateManager()
        self._last_w, self._last_h = WIN_W, WIN_H
        self._stable = False
        self._sort_mode = False
        self._tooltip: Optional[Dict[str, Any]] = None

    def load_file(self, filepath: str) -> bool:
        """Load CSV or Excel file via pandas."""
        try:
            ext = Path(filepath).suffix.lower()
            if ext == ".csv":
                self.df = pd.read_csv(filepath)
            elif ext in (".xlsx", ".xls"):
                self.df = pd.read_excel(filepath)
            else:
                return False
            if self.df.empty or len(self.df) == 0:
                return False
            self.numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
            if not self.numeric_cols:
                return False
            return True
        except Exception:
            return False

    def spawn_elements(self) -> None:
        """Procedurally generate physics elements from loaded data."""
        self.elements.clear()
        self.engine = AetherEngine()
        if self.df is None or not self.numeric_cols:
            return
        n_cols = len(self.numeric_cols)
        n_rows = min(len(self.df), MAX_ROWS)
        col_spacing = (WIN_W - 80) / max(n_cols, 1)
        row_spacing = (WIN_H - TOOLBAR_H - 60) / max(n_rows, 1)
        z_counter = 0
        for ci, col in enumerate(self.numeric_cols):
            col_data = self.df[col].dropna()
            col_min = col_data.min()
            col_max = col_data.max()
            col_range = col_max - col_min if col_max != col_min else 1.0
            cx = 40 + ci * col_spacing + col_spacing / 2
            for ri in range(n_rows):
                val = float(self.df[col].iloc[ri]) if ri < len(self.df) else 0.0
                norm = (val - col_min) / col_range
                cy = TOOLBAR_H + 30 + ri * row_spacing + row_spacing / 2
                elem = DataElement(cx, cy, norm, col, ri, z=z_counter)
                self.engine.register_element(elem)
                self.elements.append(elem)
                z_counter += 1

    def apply_sort_forces(self) -> None:
        """Apply gravity forces: heaviest elements sink to bottom."""
        for elem in self.elements:
            gravity = elem.mass * 15.0
            elem.tensor.apply_force(np.array([0.0, gravity, 0.0, 0.0], dtype=np.float32))
            cx = WIN_W / 2
            dx = cx - float(elem.tensor.state[0])
            elem.tensor.apply_force(np.array([dx * 0.002, 0.0, 0.0, 0.0], dtype=np.float32))

    def apply_normal_forces(self) -> None:
        """Normal mode: elements stay near their data grid positions (vectorized)."""
        n = len(self.elements)
        if n == 0:
            return
        targets = np.array([[float(e._target[0]), float(e._target[1])] for e in self.elements], dtype=np.float32)
        states = np.array([[float(e.tensor.state[0]), float(e.tensor.state[1])] for e in self.elements], dtype=np.float32)
        forces = (targets - states) * 0.05
        for i, elem in enumerate(self.elements):
            elem.tensor.apply_force(np.array([forces[i, 0], forces[i, 1], 0.0, 0.0], dtype=np.float32))

    def tick(self, win_w: float = WIN_W, win_h: float = WIN_H) -> float:
        t0 = time.perf_counter()
        n = len(self.elements)
        if n == 0:
            return 0.0

        if self._sort_mode:
            self.apply_sort_forces()
        else:
            self.apply_normal_forces()

        # Vectorized integration: batch all states/velocities/accelerations
        states = np.zeros((n, 4), dtype=np.float32)
        vels = np.zeros((n, 4), dtype=np.float32)
        accs = np.zeros((n, 4), dtype=np.float32)
        for i, e in enumerate(self.elements):
            states[i] = e.tensor.state
            vels[i] = e.tensor.velocity
            accs[i] = e.tensor.acceleration

        # Damping
        vels *= np.float32(0.92)

        # Clamp velocity magnitude (vectorized L2 norm)
        vel_mag = np.linalg.norm(vels[:, :2], axis=1, keepdims=True)
        mask = vel_mag > float(MAX_VELOCITY)
        if np.any(mask):
            scale = np.float32(MAX_VELOCITY) / np.where(mask, vel_mag, 1.0)
            vels[:, :2] *= scale

        # Euler integrate: v += a*dt, s += v*dt
        dt = np.float32(1.0 / 60.0)
        vels += accs * dt
        states += vels * dt

        # Clamp dimensions
        states[:, 2] = np.maximum(states[:, 2], np.float32(0.0))
        states[:, 3] = np.maximum(states[:, 3], np.float32(0.0))

        # NaN guard
        states = np.where(np.isnan(states), np.float32(0.0), states)
        vels = np.where(np.isnan(vels), np.float32(0.0), vels)

        # Write back
        for i, e in enumerate(self.elements):
            e.tensor.state[:] = states[i]
            e.tensor.velocity[:] = vels[i]
            e.tensor.acceleration.fill(np.float32(0.0))

        ke = 0.5 * np.sum(vels[:, :2] ** 2)
        self._stable = float(ke) < 5.0
        return (time.perf_counter() - t0) * 1000.0

    def handle_teleportation(self, new_w: float, new_h: float) -> None:
        if self._last_w == 0:
            self._last_w, self._last_h = new_w, new_h
            return
        sx = new_w / self._last_w if self._last_w > 0 else 1.0
        sy = new_h / self._last_h if self._last_h > 0 else 1.0
        for elem in self.elements:
            elem.tensor.state[0] = np.float32(float(elem.tensor.state[0]) * sx)
            elem.tensor.state[1] = np.float32(float(elem.tensor.state[1]) * sy)
            elem._target[0] = np.float32(float(elem._target[0]) * sx)
            elem._target[1] = np.float32(float(elem._target[1]) * sy)
        self._last_w, self._last_h = new_w, new_h

    def get_tooltip(self, x: float, y: float) -> Optional[Dict[str, Any]]:
        """Find element under cursor and return its data details."""
        for elem in self.elements:
            s = elem.tensor.state
            if float(s[0]) <= x <= float(s[0]) + float(s[2]) and \
               float(s[1]) <= y <= float(s[1]) + float(s[3]):
                row_data = {}
                if self.df is not None and elem.row_idx < len(self.df):
                    for col in self.df.columns:
                        row_data[col] = str(self.df[col].iloc[elem.row_idx])
                return {
                    "row": elem.row_idx,
                    "column": elem.col_name,
                    "value": f"{elem.value:.3f}",
                    "mass": f"{elem.mass:.2f}",
                    "details": row_data,
                }
        return None

    def cleanup(self) -> None:
        """Release resources and run garbage collection."""
        self.elements.clear()
        self.df = None
        self.engine = AetherEngine()
        gc.collect()


# ── Kivy Application ──────────────────────────────────────────────────────
def _run_kivy():
    os.environ["KIVY_LOG_LEVEL"] = "warning"
    from kivy.app import App
    from kivy.uix.widget import Widget
    from kivy.uix.label import Label
    from kivy.uix.button import Button
    from kivy.uix.behaviors import ButtonBehavior
    from kivy.graphics import Color, RoundedRectangle, Line
    from kivy.core.window import Window
    from kivy.clock import Clock

    Window.size = (int(WIN_W), int(WIN_H))
    Window.clearcolor = (0.04, 0.05, 0.08, 1.0)

    forge = DataForgeEngine()
    lang_code = "en"

    def _(key):
        return LANG[lang_code].get(key, key)

    # ── Custom styled button ──────────────────────────────────────────────
    class NeonButton(ButtonBehavior, Widget):
        """Sleek dark button with rounded corners and glow border."""
        def __init__(self, text="", **kw):
            super().__init__(**kw)
            self._label = Label(text=text, color=(0.85, 0.85, 0.9, 1), font_size=12)
            self.add_widget(self._label)
            self._pressed = False
            self.bind(size=self._redraw, pos=self._redraw)
            self._redraw()

        def _redraw(self, *args):
            self.canvas.clear()
            bg = (0.12, 0.13, 0.18, 0.9) if not self._pressed else (0.18, 0.2, 0.28, 0.95)
            border = (0.25, 0.35, 0.6, 0.6) if self._pressed else (0.15, 0.15, 0.2, 0.3)
            with self.canvas:
                # Glow
                Color(*border[:3], 0.12)
                RoundedRectangle(pos=(self.x - 3, self.y - 3),
                                 size=(self.width + 6, self.height + 6),
                                 radius=[8, 8, 8, 8])
                # Background
                Color(*bg)
                RoundedRectangle(pos=self.pos, size=self.size, radius=[6, 6, 6, 6])
                # Border
                Color(*border)
                Line(rounded_rectangle=(self.x, self.y, self.width, self.height, 6, 6, 6, 6), width=1.2)
            self._label.pos = (self.x, self.y + (self.height - self._label.texture_size[1]) / 2)
            self._label.size = self._label.texture_size
            self._label.center_x = self.center_x

        def on_touch_down(self, touch):
            if self.collide_point(*touch.pos):
                self._pressed = True
                self._redraw()
                touch.grab(self)
                return True
            return super().on_touch_down(touch)

        def on_touch_up(self, touch):
            if touch.grab_current is self:
                self._pressed = False
                self._redraw()
                self.dispatch('on_release')
                touch.ungrab(self)
                return True
            return super().on_touch_up(touch)

    class ForgeWidget(Widget):
        def __init__(self, **kw):
            super().__init__(**kw)
            self._title = Label(text=_("title"), pos=(20, WIN_H - 28),
                                color=(0.55, 0.6, 0.75, 1), font_size=17)
            self._subtitle = Label(text=_("subtitle"), pos=(22, WIN_H - 52),
                                   color=(0.3, 0.32, 0.4, 1), font_size=11)
            self._status = Label(text=_("no_data"), pos=(20, 8),
                                 color=(0.35, 0.38, 0.45, 1), font_size=10)
            self._tooltip_lbl = Label(text="", pos=(0, 0), color=(0.85, 0.88, 0.95, 1),
                                      font_size=10, halign="left", valign="top",
                                      size=(260, 160))
            self._col_labels = []
            self.add_widget(self._title)
            self.add_widget(self._subtitle)
            self.add_widget(self._status)
            self.add_widget(self._tooltip_lbl)

            # Custom buttons
            self._btn_open = NeonButton(text=_("open"), pos=(WIN_W - 290, WIN_H - 44),
                                         size=(100, 30))
            self._btn_open.bind(on_release=self._do_open)
            self._btn_sort = NeonButton(text=_("sort"), pos=(WIN_W - 180, WIN_H - 44),
                                         size=(100, 30))
            self._btn_sort.bind(on_release=self._do_sort)
            self._btn_reset = NeonButton(text=_("reset"), pos=(WIN_W - 180, WIN_H - 80),
                                          size=(100, 30))
            self._btn_reset.bind(on_release=self._do_reset)
            self._btn_lang = NeonButton(text=_("lang"), pos=(WIN_W - 70, WIN_H - 44),
                                         size=(55, 30))
            self._btn_lang.bind(on_release=self._do_lang)
            for btn in [self._btn_open, self._btn_sort, self._btn_reset, self._btn_lang]:
                self.add_widget(btn)
            Clock.schedule_interval(self._tick, 1.0 / 60.0)

        def _do_open(self, *args):
            root = Tk()
            root.withdraw()
            filepath = filedialog.askopenfilename(
                filetypes=[("Data files", "*.csv *.xlsx *.xls"), ("All files", "*.*")]
            )
            root.destroy()
            if filepath:
                if forge.load_file(filepath):
                    forge.spawn_elements()
                    n_rows = min(len(forge.df), MAX_ROWS)
                    n_cols = len(forge.numeric_cols)
                    self._status.text = f"{n_rows} {_('rows')} × {n_cols} {_('cols')} — {len(forge.elements)} nodes"
                    self._build_col_labels()
                else:
                    self._status.text = _("error_invalid")

        def _build_col_labels(self):
            for lbl in self._col_labels:
                self.remove_widget(lbl)
            self._col_labels.clear()
            cw = self.width or WIN_W
            n_cols = len(forge.numeric_cols)
            if n_cols == 0:
                return
            col_spacing = (cw - 80) / n_cols
            for ci, col in enumerate(forge.numeric_cols):
                cx = 40 + ci * col_spacing + col_spacing / 2
                lbl = Label(text=col, pos=(cx - 35, TOOLBAR_H + 8),
                            color=(0.45, 0.48, 0.58, 1), font_size=9,
                            halign="center", size=(70, 16))
                self.add_widget(lbl)
                self._col_labels.append(lbl)

        def _do_sort(self, *args):
            forge._sort_mode = not forge._sort_mode
            self._btn_sort._label.text = _("reset") if forge._sort_mode else _("sort")
            self._btn_sort._redraw()

        def _do_reset(self, *args):
            forge._sort_mode = False
            forge.spawn_elements()
            self._btn_sort._label.text = _("sort")
            self._btn_sort._redraw()
            self._build_col_labels()

        def _do_lang(self, *args):
            nonlocal lang_code
            lang_code = "es" if lang_code == "en" else "en"
            self._title.text = _("title")
            self._subtitle.text = _("subtitle")
            self._btn_open._label.text = _("open")
            self._btn_open._redraw()
            self._btn_sort._label.text = _("sort") if not forge._sort_mode else _("reset")
            self._btn_sort._redraw()
            self._btn_reset._label.text = _("reset")
            self._btn_reset._redraw()
            self._btn_lang._label.text = _("lang")
            self._btn_lang._redraw()

        def _tick(self, dt):
            cw, ch = self.width or WIN_W, self.height or WIN_H
            if abs(cw - forge._last_w) > 10 or abs(ch - forge._last_h) > 10:
                forge.handle_teleportation(cw, ch)
            if forge.elements:
                forge.tick(cw, ch)
            self.canvas.before.clear()
            with self.canvas.before:
                n_cols = len(forge.numeric_cols)
                if n_cols > 0:
                    col_spacing = (cw - 80) / n_cols
                # Gravity lanes
                for ci in range(n_cols):
                    cx = 40 + ci * col_spacing + col_spacing / 2
                    Color(1, 1, 1, 0.04)
                    Line(points=[cx, TOOLBAR_H + 25, cx, ch - 10], width=1)
                # Elements with glow
                for elem in forge.elements:
                    s = elem.tensor.state
                    x, y, w, h = float(s[0]), float(s[1]), float(s[2]), float(s[3])
                    r, g, b, a = elem._color
                    # Glow layer
                    Color(r, g, b, 0.12)
                    RoundedRectangle(pos=(x - 4, y - 4), size=(w + 8, h + 8),
                                     radius=[6, 6, 6, 6])
                    # Main element
                    Color(r, g, b, a)
                    RoundedRectangle(pos=(x, y), size=(w, h), radius=[6, 6, 6, 6])
                    # Subtle inner highlight
                    Color(1, 1, 1, 0.08)
                    RoundedRectangle(pos=(x + 1, y + 1), size=(w - 2, h * 0.4),
                                     radius=[5, 5, 1, 1])
                # Tooltip
                if forge._tooltip:
                    tx, ty = forge._tooltip.get("x", 0), forge._tooltip.get("y", 0)
                    Color(0.04, 0.05, 0.1, 0.95)
                    RoundedRectangle(pos=(tx + 12, ty + 12), size=(265, 125),
                                     radius=[6, 6, 6, 6])
                    Color(0.2, 0.35, 0.6, 0.5)
                    Line(rounded_rectangle=(tx + 12, ty + 12, 265, 125, 6, 6, 6, 6), width=1)
            self._status.text = (
                f"{len(forge.elements)} nodes  •  "
                f"{'● ' + _('stable') if forge._stable else '○ ' + _('processing')}  •  "
                f"Sort: {'ON' if forge._sort_mode else 'OFF'}"
            )

        def on_touch_down(self, touch):
            tip = forge.get_tooltip(touch.x, touch.y)
            if tip:
                forge._tooltip = {"x": touch.x, "y": touch.y, **tip}
                lines = [
                    f"{_('row')}: {tip['row']}  |  {_('column')}: {tip['column']}",
                    f"{_('value')}: {tip['value']}  |  {_('mass')}: {tip['mass']}",
                ]
                if tip.get("details"):
                    for k, v in list(tip["details"].items())[:3]:
                        lines.append(f"  {k}: {v}")
                self._tooltip_lbl.text = "\n".join(lines)
                self._tooltip_lbl.pos = (touch.x + 18, touch.y + 18)
            else:
                forge._tooltip = None
                self._tooltip_lbl.text = ""
            return super().on_touch_down(touch)

    class ForgeApp(App):
        def build(self):
            w = ForgeWidget(size=Window.size)
            sample = Path(__file__).parent / "sample_data.csv"
            if sample.exists() and forge.load_file(str(sample)):
                forge.spawn_elements()
                n_rows = min(len(forge.df), MAX_ROWS)
                n_cols = len(forge.numeric_cols)
                w._status.text = f"{n_rows} {_('rows')} × {n_cols} {_('cols')} — {len(forge.elements)} nodes"
                Clock.schedule_once(lambda dt: w._build_col_labels(), 0.1)
            return w

    ForgeApp().run()


if __name__ == "__main__":
    if "--headless" in sys.argv:
        forge = DataForgeEngine()
        sample = Path(__file__).parent / "sample_data.csv"
        if sample.exists() and forge.load_file(str(sample)):
            forge.spawn_elements()
            print(f"[OK] Loaded {len(forge.elements)} elements from sample_data.csv")
            for _ in range(100):
                forge.tick()
            print(f"[OK] 100 ticks completed. Stable: {forge._stable}")
        else:
            print("[WARN] sample_data.csv not found — run with no args for GUI")
    else:
        _run_kivy()
