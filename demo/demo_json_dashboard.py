# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""JSON-driven physics dashboard — loads config, instantiates elements, validates."""
import json, os, sys, numpy as np
from pathlib import Path
from core.engine import AetherEngine
from core.aether_math import StateTensor
from core.elements import DifferentialElement

CONFIG = Path(__file__).parent / "dashboard_config.json"


class DashElement(DifferentialElement):
    """Physics element with JSON-driven mass and stiffness."""
    def __init__(self, cfg):
        super().__init__(*cfg["initial_pos"], *cfg["size"], color=cfg["color"])
        self.label = cfg["label_text"]
        self.mass = cfg["mass"]
        self._stiffness = cfg["stiffness"]
        self._target = np.array([*cfg["initial_pos"], *cfg["size"]], dtype=np.float32)

    def calculate_asymptotes(self, cw, ch):
        return self._target.copy()


def build_dashboard(config_path: str = str(CONFIG)) -> dict:
    """Load JSON config, build engine with elements, return engine + elements."""
    with open(config_path) as f:
        cfg = json.load(f)
    engine = AetherEngine()
    elements = []
    for ecfg in cfg["elements"]:
        elem = DashElement(ecfg)
        engine.register_element(elem)
        elements.append(elem)
    return {"engine": engine, "elements": elements, "title": cfg["dashboard_title"]}


def validate(dash: dict) -> bool:
    """Run 200 ticks, verify no NaN, all JSON properties applied."""
    e, elems = dash["engine"], dash["elements"]
    for _ in range(200):
        data = e.tick(1280, 720)
    assert len(data) == len(elems)
    assert not np.any(np.isnan(data["rect"]))
    assert not np.any(np.isnan(data["color"]))
    for el in elems:
        assert el.mass > 0
        assert el._stiffness > 0
    return True


def _run_kivy(dash):
    os.environ["KIVY_LOG_LEVEL"] = "warning"
    from kivy.app import App
    from kivy.uix.widget import Widget
    from kivy.uix.label import Label
    from kivy.graphics import Color, Rectangle, Line
    from kivy.clock import Clock
    from kivy.core.window import Window
    Window.size = (960, 540)
    Window.clearcolor = (0.03, 0.03, 0.06, 1.0)

    class DashboardWidget(Widget):
        def __init__(self, **kw):
            super().__init__(**kw)
            self.dash = dash
            self.lbl = Label(text=dash["title"], pos=(10, 500), color=(0.6, 0.6, 0.7, 1), font_size=18)
            self.add_widget(self.lbl)
            Clock.schedule_interval(self._tick, 1.0 / 60.0)

        def _tick(self, dt):
            self.dash["engine"].tick(960, 540)
            self.canvas.clear()
            with self.canvas:
                for el in self.dash["elements"]:
                    s = el.tensor.state
                    x, y, w, h = float(s[0]), float(s[1]), float(s[2]), float(s[3])
                    r, g, b, a = el._color
                    Color(r, g, b, a * 0.3)
                    Rectangle(pos=(x, y), size=(w, h))
                    Color(r, g, b, a)
                    Line(rectangle=(x, y, w, h), width=2)
                    Color(0.9, 0.9, 0.9, 1)
                    Rectangle(pos=(x + 10, y + h - 30), size=(w - 20, 22))
                    Color(0.05, 0.05, 0.08, 1)
                    Rectangle(pos=(x + 11, y + h - 29), size=(w - 22, 20))
            for el in self.dash["elements"]:
                s = el.tensor.state
                lbl = Label(text=el.label, pos=(float(s[0]) + 14, float(s[1]) + float(s[3]) - 28),
                            color=(0.95, 0.95, 0.95, 1), font_size=13, halign="left")
                self.add_widget(lbl)

    class DashApp(App):
        def build(self):
            return DashboardWidget(size=Window.size)

    DashApp().run()


if __name__ == "__main__":
    dash = build_dashboard()
    print(f"[OK] {dash['title']} — {len(dash['elements'])} elements loaded from JSON")
    for el in dash["elements"]:
        print(f"  {el.label:15s}  mass={el.mass}  stiffness={el._stiffness}")
    assert validate(dash)
    print("[OK] 200-tick stability check passed — no NaN, all properties verified")
    if "--headless" not in sys.argv:
        _run_kivy(dash)
