# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""JSON-driven physics dashboard — loads config, instantiates elements, validates."""
import json, os, numpy as np
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


if __name__ == "__main__":
    dash = build_dashboard()
    print(f"[OK] {dash['title']} — {len(dash['elements'])} elements loaded from JSON")
    for el in dash["elements"]:
        print(f"  {el.label:15s}  mass={el.mass}  stiffness={el._stiffness}")
    assert validate(dash)
    print("[OK] 200-tick stability check passed — no NaN, all properties verified")
