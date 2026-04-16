# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""Engine Selector: Unified facade for choosing between Python and Rust physics engines.

Usage:
    # Auto-detect (tries Rust, falls back to Python)
    engine = EngineSelector()

    # Force Python
    engine = EngineSelector(engine_type="python")

    # Force Rust (raises error if not available)
    engine = EngineSelector(engine_type="rust")

Environment variable:
    AETHER_ENGINE=python|rust|auto  (default: auto)
"""

import os
import time
import logging
import numpy as np
from typing import List, Optional, Any
from .protocols import AetherEngineProtocol

logger = logging.getLogger(__name__)

# ── Engine Detection ──────────────────────────────────────────────────────

_RUST_AVAILABLE = False
try:
    import aether_pyo3
    _RUST_AVAILABLE = True
    logger.info("Rust engine (aether_pyo3) is available")
except ImportError:
    logger.info("Rust engine not available, falling back to Python")


def _resolve_engine_type(engine_type: str) -> str:
    """Resolve engine type from parameter + environment variable."""
    env = os.environ.get("AETHER_ENGINE", "").lower().strip()
    if env in ("python", "rust", "auto"):
        engine_type = env

    if engine_type == "auto":
        return "rust" if _RUST_AVAILABLE else "python"
    if engine_type == "rust" and not _RUST_AVAILABLE:
        raise RuntimeError(
            "Rust engine requested but aether_pyo3 module is not available. "
            "Build it with: cd aetheris-rust && maturin develop"
        )
    return engine_type


# ── Wrapper for Rust Engine ───────────────────────────────────────────────

class _RustEngineWrapper:
    """Wraps the Rust PyO3 engine to match the Python engine API."""

    def __init__(self):
        self._engine = aether_pyo3.AetherEngine()
        self._dt = 0.0
        self._last_time = time.perf_counter()

    @property
    def element_count(self) -> int:
        return self._engine.element_count()

    @property
    def dt(self) -> float:
        return self._dt

    def register_element(self, element) -> None:
        """Register a Python element by extracting its properties and creating
        the corresponding Rust element."""
        elem_type = type(element).__name__

        if elem_type == "StaticBox":
            rect = element.tensor.state
            self._engine.register_static_box(
                float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]),
                _vec4_from_color(element.color),
                element.z_index,
            )
        elif elem_type == "SmartPanel":
            self._engine.register_smart_panel(
                element._padding,
                _vec4_from_color(element.color),
                element.z_index,
            )
        elif elem_type == "SmartButton":
            self._engine.register_smart_button(
                element._parent_index,
                element._offset_x, element._offset_y,
                element._offset_w, element._offset_h,
                _vec4_from_color(element.color),
                element.z_index,
            )
        elif elem_type == "CanvasTextNode":
            rect = element.tensor.state
            self._engine.register_canvas_text_node(
                float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]),
                _vec4_from_color(element.color),
                element.z_index,
                element.text,
                element.font_size,
                element.font_family,
            )
        elif elem_type == "FlexibleTextNode":
            rect = element.tensor.state
            self._engine.register_flexible_text_node(
                float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]),
                _vec4_from_color(element.color),
                element.z_index,
                element.text,
            )
        elif elem_type == "DOMTextNode":
            rect = element.tensor.state
            self._engine.register_flexible_text_node(
                float(rect[0]), float(rect[1]), float(rect[2]), float(rect[3]),
                _vec4_from_color(element.color),
                element.z_index,
                element.text,
            )
        else:
            logger.warning(f"Unknown element type: {elem_type}, skipping registration")

    def handle_pointer_down(self, x: float, y: float) -> None:
        self._engine.handle_pointer_down(float(x), float(y))

    def handle_pointer_move(self, x: float, y: float) -> None:
        self._engine.handle_pointer_move(float(x), float(y))

    def handle_pointer_up(self) -> None:
        self._engine.handle_pointer_up()

    def tick(self, win_w: float, win_h: float) -> np.ndarray:
        tick_start = time.perf_counter()
        current_time = time.perf_counter()
        self._dt = current_time - self._last_time
        self._last_time = current_time

        render_data = self._engine.tick(float(win_w), float(win_h))

        n = len(render_data)
        if n == 0:
            return np.zeros(0, dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])

        data = np.zeros(n, dtype=[('rect', 'f4', 4), ('color', 'f4', 4), ('z', 'i4')])
        for i, item in enumerate(render_data):
            rect = item['rect']
            color = item['color']
            data[i]['rect'] = [rect['x'], rect['y'], rect['w'], rect['h']]
            data[i]['color'] = [color['r'], color['g'], color['b'], color['a']]
            data[i]['z'] = item['z']

        return data

    def get_ui_metadata(self) -> str:
        return self._engine.get_ui_metadata()

    @property
    def state_manager(self) -> Any:
        return None

    @property
    def input_manager(self) -> Any:
        return None

    @property
    def tensor_compiler(self) -> Any:
        return None


def _vec4_from_color(color) -> 'aether_pyo3.Vec4':
    """Convert a color tuple/list to a PyO3 Vec4."""
    c = list(color) if hasattr(color, '__iter__') else [color, color, color, 1.0]
    while len(c) < 4:
        c.append(1.0)
    return aether_pyo3.Vec4(float(c[0]), float(c[1]), float(c[2]), float(c[3]))


# ── Python Engine Wrapper ─────────────────────────────────────────────────

class _PythonEngineWrapper:
    """Wraps the existing Python AetherEngine to match the unified API."""

    def __init__(self):
        from core.engine import AetherEngine
        self._engine = AetherEngine()

    @property
    def element_count(self) -> int:
        return self._engine.element_count

    @property
    def dt(self) -> float:
        return self._engine.dt

    def register_element(self, element) -> None:
        self._engine.register_element(element)

    def handle_pointer_down(self, x: float, y: float) -> None:
        self._engine.handle_pointer_down(x, y)

    def handle_pointer_move(self, x: float, y: float) -> None:
        self._engine.handle_pointer_move(x, y)

    def handle_pointer_up(self) -> None:
        self._engine.handle_pointer_up()

    def tick(self, win_w: float, win_h: float) -> np.ndarray:
        return self._engine.tick(win_w, win_h)

    def get_ui_metadata(self) -> str:
        return self._engine.get_ui_metadata()

    @property
    def state_manager(self):
        return self._engine.state_manager

    @property
    def input_manager(self):
        return self._engine.input_manager

    @property
    def tensor_compiler(self):
        return self._engine.tensor_compiler


# ── Public Facade ──────────────────────────────────────────────────────────

class EngineSelector:
    """Unified facade that allows choosing between Python or Rust physics engine.

    Args:
        engine_type: "auto" (default), "python", or "rust"

    Environment variable:
        AETHER_ENGINE=python|rust|auto  (overrides constructor parameter)
    """

    def __init__(self, engine_type: str = "auto"):
        resolved = _resolve_engine_type(engine_type)
        self._engine_type = resolved
        self._engine: AetherEngineProtocol

        if resolved == "rust":
            self._engine = _RustEngineWrapper()
            logger.info("Using Rust physics engine (aether_pyo3)")
        else:
            self._engine = _PythonEngineWrapper()
            logger.info("Using Python physics engine")

    @property
    def engine_type(self) -> str:
        """Returns 'rust' or 'python'."""
        return self._engine_type

    @property
    def element_count(self) -> int:
        return self._engine.element_count

    @property
    def dt(self) -> float:
        return self._engine.dt

    def register_element(self, element) -> None:
        self._engine.register_element(element)

    def register_state(self, name: str, state_data: dict) -> None:
        """No-op for Rust engine, delegates to Python engine."""
        if hasattr(self._engine, 'register_state'):
            self._engine.register_state(name, state_data)

    def transition_to(self, state_name: str) -> None:
        """No-op for Rust engine, delegates to Python engine."""
        if hasattr(self._engine, 'transition_to'):
            self._engine.transition_to(state_name)

    def handle_pointer_down(self, x: float, y: float) -> None:
        self._engine.handle_pointer_down(x, y)

    def handle_pointer_move(self, x: float, y: float) -> None:
        self._engine.handle_pointer_move(x, y)

    def handle_pointer_up(self) -> None:
        self._engine.handle_pointer_up()

    def tick(self, win_w: float, win_h: float) -> np.ndarray:
        return self._engine.tick(win_w, win_h)

    def get_ui_metadata(self) -> str:
        return self._engine.get_ui_metadata()

    @property
    def state_manager(self):
        """Only available on Python engine."""
        if hasattr(self._engine, 'state_manager'):
            return self._engine.state_manager
        raise AttributeError("state_manager not available on Rust engine")

    @property
    def input_manager(self):
        """Only available on Python engine."""
        if hasattr(self._engine, 'input_manager'):
            return self._engine.input_manager
        raise AttributeError("input_manager not available on Rust engine")

    @property
    def tensor_compiler(self):
        """Only available on Python engine."""
        if hasattr(self._engine, 'tensor_compiler'):
            return self._engine.tensor_compiler
        raise AttributeError("tensor_compiler not available on Rust engine")

    @property
    def audio_bridge(self):
        if hasattr(self._engine, '_engine') and hasattr(self._engine._engine, '_audio_bridge'):
            return self._engine._engine._audio_bridge
        return None

    @audio_bridge.setter
    def audio_bridge(self, bridge):
        if hasattr(self._engine, '_engine') and hasattr(self._engine._engine, '_audio_bridge'):
            self._engine._engine._audio_bridge = bridge

    def _apply_genre_orbit(self, genre_idx: int, stiffness: float,
                           center_x: float, center_y: float) -> None:
        """Only available on Python engine."""
        if hasattr(self._engine, '_apply_genre_orbit'):
            self._engine._apply_genre_orbit(genre_idx, stiffness, center_x, center_y)

    def _trigger_supernova(self, center_x: float, center_y: float) -> None:
        """Only available on Python engine."""
        if hasattr(self._engine, '_trigger_supernova'):
            self._engine._trigger_supernova(center_x, center_y)
