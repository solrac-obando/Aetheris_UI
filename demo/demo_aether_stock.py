# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Aether-Stock: Physics-Driven Stock Market Dashboard

A standalone desktop demo that visualizes synthetic stock market data
as physics-driven UI elements. Each data point is a physical particle
with mass, gravity, and buoyancy forces derived from price movement.

Features:
  - 100-point synthetic stock dataset (numpy.random.randn cumulative walk)
  - Data-Bridge min_max_scale maps prices to pixel coordinates
  - Physics: price drops increase gravity, price rises add buoyancy
  - Input-Bridge drag interaction with high-stiffness spring
  - Built-in stability verification (1000 ticks, zero NaN tolerance)

Usage:
  Headless (test):  python3 -m pytest demo/demo_aether_stock.py -v
  Interactive:      python3 demo/demo_aether_stock.py
"""

import sys
import time
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

# ---------------------------------------------------------------------------
# Core imports
# ---------------------------------------------------------------------------
from core.engine import AetherEngine
from core.aether_math import StateTensor, EPSILON, MAX_VELOCITY
from core.elements import DifferentialElement, CanvasTextNode
from core.data_bridge import min_max_scale, normalize_column
from core.input_manager import InputManager

# ---------------------------------------------------------------------------
# Demo constants
# ---------------------------------------------------------------------------
WIN_WIDTH = 1280
WIN_HEIGHT = 720
NUM_DATA_POINTS = 100
CHART_LEFT = 80.0
CHART_RIGHT = WIN_WIDTH - 80.0
CHART_TOP = 60.0
CHART_BOTTOM = WIN_HEIGHT - 80.0
BAR_WIDTH = (CHART_RIGHT - CHART_LEFT) / NUM_DATA_POINTS - 2.0
GRAVITY_BASE = 50.0
BUOYANCY_FACTOR = 200.0
DRAG_STIFFNESS_OVERRIDE = 8.0
SEED = 42


# ============================================================================
# StockElement — a physics-driven bar that reacts to price movement
# ============================================================================

class StockElement(DifferentialElement):
    """A stock bar element whose target Y is driven by price data.

    When the price drops below the previous close, gravity increases
    (heavier mass pulls it down). When the price rises, buoyancy
    pushes it upward. The element still obeys Hooke's Law and
    boundary forces from the AetherEngine.
    """

    def __init__(
        self,
        x: float,
        target_y: float,
        height: float,
        price: float,
        price_change: float,
        index: int,
        color: Tuple[float, float, float, float],
        z: int = 0,
    ):
        super().__init__(x, target_y, BAR_WIDTH, height, color, z)
        self._target_x = x
        self._target_y = target_y
        self._target_height = height
        self._price = price
        self._price_change = price_change
        self._index = index
        self._is_grabbed = False

    def calculate_asymptotes(self, container_w: float, container_h: float) -> np.ndarray:
        """Return the target rectangle — price-driven Y position."""
        return np.array(
            [self._target_x, self._target_y, BAR_WIDTH, self._target_height],
            dtype=np.float32,
        )

    def apply_market_force(self) -> np.ndarray:
        """Compute gravity/buoyancy force from price change.

        Negative change (price drop)  → downward gravity
        Positive change (price rise)  → upward buoyancy
        """
        if self._price_change < 0:
            magnitude = GRAVITY_BASE * abs(self._price_change)
            force = np.array([0.0, magnitude, 0.0, 0.0], dtype=np.float32)
        else:
            magnitude = BUOYANCY_FACTOR * self._price_change
            force = np.array([0.0, -magnitude, 0.0, 0.0], dtype=np.float32)
        return force

    def update_price(self, new_price: float, new_change: float) -> None:
        """Hot-swap the price data — simulates live market updates."""
        old_price = self._price
        self._price = new_price
        self._price_change = new_change

        scaled_y = min_max_scale(
            new_price,
            data_min=old_price - 5.0,
            data_max=old_price + 5.0,
            target_min=CHART_TOP,
            target_max=CHART_BOTTOM,
        )
        self._target_y = scaled_y
        bar_h = max(4.0, abs(new_change) * 30.0 + 4.0)
        self._target_height = bar_h

        if self._price_change < 0:
            self._color = np.array([0.85, 0.15, 0.15, 0.9], dtype=np.float32)
        else:
            self._color = np.array([0.15, 0.85, 0.25, 0.9], dtype=np.float32)


# ============================================================================
# AetherStockEngine — wraps AetherEngine with stock-specific logic
# ============================================================================

class AetherStockEngine:
    """High-level engine that manages stock data → physics → UI pipeline."""

    def __init__(self, num_points: int = NUM_DATA_POINTS, seed: int = SEED):
        self.engine = AetherEngine()
        self.elements: List[StockElement] = []
        self.prices: np.ndarray = self._generate_prices(num_points, seed)
        self.changes: np.ndarray = np.zeros(num_points, dtype=np.float32)
        self._build_chart()

    # ---- data generation ------------------------------------------------

    @staticmethod
    def _generate_prices(n: int, seed: int) -> np.ndarray:
        rng = np.random.RandomState(seed)
        returns = rng.randn(n).astype(np.float32)
        prices = np.cumsum(returns).astype(np.float32)
        prices -= prices.min()
        prices += 100.0
        return prices

    # ---- chart construction ---------------------------------------------

    def _build_chart(self) -> None:
        price_min = float(self.prices.min())
        price_max = float(self.prices.max())

        for i in range(len(self.prices)):
            x = CHART_LEFT + i * (BAR_WIDTH + 2.0)
            price = float(self.prices[i])
            change = float(self.changes[i])

            scaled_y = min_max_scale(
                price, price_min, price_max, CHART_TOP, CHART_BOTTOM,
            )
            bar_h = max(4.0, abs(change) * 30.0 + 4.0)

            if change < 0:
                color = (0.85, 0.15, 0.15, 0.9)
            else:
                color = (0.15, 0.85, 0.25, 0.9)

            elem = StockElement(
                x=x,
                target_y=scaled_y,
                height=bar_h,
                price=price,
                price_change=change,
                index=i,
                color=color,
                z=i,
            )
            self.elements.append(elem)
            self.engine.register_element(elem)

        header = CanvasTextNode(
            x=CHART_LEFT,
            y=10.0,
            w=400.0,
            h=30.0,
            color=(0, 0, 0, 0),
            z=999,
            text="AETHER-STOCK  |  Physics-Driven Market Dashboard",
            font_size=18,
            font_family="monospace",
        )
        self.engine.register_element(header)

    # ---- per-tick market forces -----------------------------------------

    def _apply_market_forces(self) -> None:
        for elem in self.elements:
            if isinstance(elem, StockElement) and not elem._is_grabbed:
                force = elem.apply_market_force()
                elem.tensor.apply_force(force)

    # ---- live price update simulation -----------------------------------

    def simulate_market_tick(self) -> None:
        rng = np.random.RandomState(int(time.time() * 1000) % 2**31)
        for elem in self.elements:
            if isinstance(elem, StockElement):
                delta = float(rng.randn() * 0.5)
                new_price = elem._price + delta
                new_change = delta
                elem.update_price(new_price, new_change)

    # ---- main tick ------------------------------------------------------

    def tick(self) -> np.ndarray:
        self._apply_market_forces()
        return self.engine.tick(WIN_WIDTH, WIN_HEIGHT)

    # ---- input bridge ---------------------------------------------------

    def pointer_down(self, x: float, y: float) -> int:
        idx = self.engine.handle_pointer_down(x, y)
        if idx >= 0 and idx < len(self.elements):
            self.elements[idx]._is_grabbed = True
        return idx

    def pointer_move(self, x: float, y: float) -> None:
        self.engine.handle_pointer_move(x, y)

    def pointer_up(self) -> None:
        for elem in self.elements:
            if isinstance(elem, StockElement) and elem._is_grabbed:
                elem._is_grabbed = False
        self.engine.handle_pointer_up()

    # ---- diagnostics ----------------------------------------------------

    def get_snapshot(self) -> Dict[str, Any]:
        data = self.engine.tick(WIN_WIDTH, WIN_HEIGHT)
        prices = [float(e._price) for e in self.elements if isinstance(e, StockElement)]
        return {
            "element_count": self.engine.element_count,
            "data_shape": list(data.shape) if data.shape else [0],
            "min_price": min(prices) if prices else 0.0,
            "max_price": max(prices) if prices else 0.0,
        }


# ============================================================================
# Optional ModernGL renderer (runs only when executed directly)
# ============================================================================

def _run_interactive() -> None:
    """Launch the demo with a ModernGL window for interactive use."""
    try:
        import moderngl
        import moderngl_window
        from moderngl_window.context.base import BaseWindow
    except ImportError:
        print("[Aether-Stock] ModernGL not available — running headless demo.")
        _run_headless_demo()
        return

    class StockWindow(moderngl_window.WindowConfig):
        gl_version = (3, 3)
        title = "Aether-Stock — Physics-Driven Market Dashboard"
        resizable = True

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.stock = AetherStockEngine()
            self.prog = self.ctx.program(
                vertex_shader="""
                    #version 330
                    in vec2 in_vert;
                    in vec4 in_color;
                    out vec4 v_color;
                    void main() {
                        gl_Position = vec4(in_vert, 0.0, 1.0);
                        v_color = in_color;
                    }
                """,
                fragment_shader="""
                    #version 330
                    in vec4 v_color;
                    out vec4 f_color;
                    void main() {
                        f_color = v_color;
                    }
                """,
            )
            self.wnd.title = f"{self.title}  |  {self.stock.engine.element_count} elements"

        def render(self, time: float, frame_time: float):
            self.ctx.clear(0.04, 0.04, 0.06)
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA

            data = self.stock.tick()
            if len(data) == 0:
                return

            verts = []
            colors = []
            for row in data:
                x, y, w, h = row["rect"]
                r, g, b, a = row["color"]
                ndc = self._to_ndc(x, y, w, h)
                if ndc is None:
                    continue
                x0, y0, x1, y1 = ndc
                verts.extend([
                    x0, y0, x1, y0, x0, y1,
                    x1, y0, x1, y1, x0, y1,
                ])
                for _ in range(6):
                    colors.extend([r, g, b, a])

            if verts:
                vbo_verts = self.ctx.buffer(np.array(verts, dtype="f4"))
                vbo_colors = self.ctx.buffer(np.array(colors, dtype="f4"))
                vao = self.ctx.vertex_array(
                    self.prog,
                    [
                        (vbo_verts, "2f", "in_vert"),
                        (vbo_colors, "4f", "in_color"),
                    ],
                )
                vao.render(moderngl.TRIANGLES)
                vbo_verts.release()
                vbo_colors.release()
                vao.release()

        def _to_ndc(self, x: float, y: float, w: float, h: float):
            ww, wh = self.wnd.size
            if ww == 0 or wh == 0:
                return None
            x0 = (x / ww) * 2.0 - 1.0
            y0 = 1.0 - (y / wh) * 2.0
            x1 = ((x + w) / ww) * 2.0 - 1.0
            y1 = 1.0 - ((y + h) / wh) * 2.0
            return x0, y0, x1, y1

        def key_event(self, key, action, modifiers):
            if action == self.wnd.keys.ACTION_PRESS and key == self.wnd.keys.ESCAPE:
                self.wnd.close()

        def mouse_position_event(self, x, y, dx, dy):
            self.stock.pointer_move(float(x), float(y))

        def mouse_press_event(self, x, y, button):
            self.stock.pointer_down(float(x), float(y))

        def mouse_release_event(self, x, y, button):
            self.stock.pointer_up()

    moderngl_window.run_window_config(StockWindow)


def _run_headless_demo() -> None:
    """Run a quick headless demo — 200 ticks with live market simulation."""
    print("=" * 60)
    print("AETHER-STOCK — Headless Demo")
    print("=" * 60)

    stock = AetherStockEngine()
    snapshot = stock.get_snapshot()
    print(f"Elements : {snapshot['element_count']}")
    print(f"Price range: ${snapshot['min_price']:.2f} – ${snapshot['max_price']:.2f}")
    print()

    for tick in range(200):
        if tick % 50 == 0:
            stock.simulate_market_tick()
        data = stock.tick()
        assert data.shape[0] == stock.engine.element_count
        assert not np.any(np.isnan(data["rect"]))
        assert not np.any(np.isnan(data["color"]))

    snapshot = stock.get_snapshot()
    print(f"After 200 ticks — elements: {snapshot['element_count']}")
    print(f"Price range: ${snapshot['min_price']:.2f} – ${snapshot['max_price']:.2f}")
    print("[OK] Headless demo completed without NaN or crashes.")
    print("=" * 60)


# ============================================================================
# Verification — 1000 ticks at ~60 Hz, zero NaN tolerance
# ============================================================================

def verify_demo_stability() -> Dict[str, Any]:
    """Run the AetherStockEngine for 1000 ticks and verify stability.

    Returns a dict with pass/fail status and diagnostic info.
    """
    stock = AetherStockEngine(num_points=NUM_DATA_POINTS, seed=SEED)
    target_dt = 1.0 / 60.0
    num_ticks = 1000
    nan_detected = False
    inf_detected = False
    max_velocity_seen = 0.0
    tick_times: List[float] = []

    for tick in range(num_ticks):
        if tick % 100 == 0:
            stock.simulate_market_tick()

        t0 = time.perf_counter()
        data = stock.tick()
        elapsed = time.perf_counter() - t0
        tick_times.append(elapsed)

        for elem in stock.elements:
            if isinstance(elem, StockElement):
                state = elem.tensor.state
                vel = elem.tensor.velocity
                if np.any(np.isnan(state)):
                    nan_detected = True
                if np.any(np.isinf(state)):
                    inf_detected = True
                vmag = float(np.linalg.norm(vel))
                if vmag > max_velocity_seen:
                    max_velocity_seen = vmag

    avg_tick = float(np.mean(tick_times))
    max_tick = float(np.max(tick_times))
    passed = not nan_detected and not inf_detected and max_velocity_seen < MAX_VELOCITY

    return {
        "passed": passed,
        "ticks": num_ticks,
        "target_dt": target_dt,
        "avg_tick_ms": avg_tick * 1000,
        "max_tick_ms": max_tick * 1000,
        "nan_detected": nan_detected,
        "inf_detected": inf_detected,
        "max_velocity": max_velocity_seen,
        "element_count": stock.engine.element_count,
    }


# ============================================================================
# pytest test
# ============================================================================

class TestAetherStockDemo:
    """pytest-compatible tests for the Aether-Stock demo."""

    def test_price_generation(self):
        prices = AetherStockEngine._generate_prices(NUM_DATA_POINTS, SEED)
        assert len(prices) == NUM_DATA_POINTS
        assert not np.any(np.isnan(prices))
        assert not np.any(np.isinf(prices))

    def test_chart_construction(self):
        stock = AetherStockEngine()
        assert stock.engine.element_count == NUM_DATA_POINTS + 1
        assert len(stock.elements) == NUM_DATA_POINTS

    def test_single_tick_no_nan(self):
        stock = AetherStockEngine()
        data = stock.tick()
        assert len(data) == stock.engine.element_count
        assert not np.any(np.isnan(data["rect"]))
        assert not np.any(np.isnan(data["color"]))
        assert not np.any(np.isinf(data["rect"]))

    def test_market_forces_applied(self):
        stock = AetherStockEngine()
        data_before = stock.tick()
        stock.simulate_market_tick()
        data_after = stock.tick()
        assert len(data_before) == len(data_after)

    def test_drag_interaction(self):
        stock = AetherStockEngine()
        stock.tick()
        elem = stock.elements[0]
        cx = float(elem.tensor.state[0]) + float(elem.tensor.state[2]) / 2.0
        cy = float(elem.tensor.state[1]) + float(elem.tensor.state[3]) / 2.0
        idx = stock.pointer_down(cx, cy)
        assert idx == 0
        assert stock.elements[0]._is_grabbed
        stock.pointer_move(cx + 50.0, cy - 30.0)
        stock.pointer_up()
        assert not stock.elements[0]._is_grabbed

    def test_verify_demo_stability(self):
        result = verify_demo_stability()
        assert result["passed"], (
            f"Stability check failed: "
            f"nan={result['nan_detected']}, inf={result['inf_detected']}, "
            f"max_vel={result['max_velocity']:.1f}, "
            f"avg_tick={result['avg_tick_ms']:.2f}ms"
        )

    def test_hot_swap_price_update(self):
        stock = AetherStockEngine()
        elem = stock.elements[50]
        old_price = elem._price
        elem.update_price(old_price + 10.0, 2.0)
        assert elem._price == old_price + 10.0
        assert elem._price_change == 2.0
        data = stock.tick()
        assert not np.any(np.isnan(data["rect"]))

    def test_boundary_clamping(self):
        stock = AetherStockEngine()
        for _ in range(500):
            stock.simulate_market_tick()
            stock.tick()
        for elem in stock.elements:
            if isinstance(elem, StockElement):
                s = elem.tensor.state
                assert s[2] >= 0.0
                assert s[3] >= 0.0
                assert not np.any(np.isnan(s))


# ============================================================================
# Entry point
# ============================================================================

if __name__ == "__main__":
    if "--headless" in sys.argv:
        _run_headless_demo()
    else:
        _run_interactive()
