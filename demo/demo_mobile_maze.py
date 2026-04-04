# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""Aether-Mobile Haptic Maze — swipe-driven physics with teleportation resilience."""
import sys, os, time, numpy as np
from typing import List, Tuple
from core.engine import AetherEngine
from core.aether_math import StateTensor, MAX_VELOCITY, clamp_magnitude
from core.elements import DifferentialElement
from core.input_manager import InputManager
from core.state_manager import StateManager

# ── Constants ──────────────────────────────────────────────────────────────
WIN_W, WIN_H = 360.0, 640.0
CORE_RADIUS = 18.0
NODE_COUNT = 12
SWIPE_STIFFNESS = 3.0
DAMPING = 0.05
VELOCITY_COLOR_SCALE = 0.002


# ── HapticNode — color shifts with collision velocity ──────────────────────
class HapticNode(DifferentialElement):
    """Maze wall node that glows based on collision velocity."""
    def __init__(self, x, y, w, h, z=0):
        super().__init__(x, y, w, h, color=(0.15, 0.15, 0.2, 0.9), z=z)
        self._target = np.array([x, y, w, h], dtype=np.float32)

    def calculate_asymptotes(self, cw, ch):
        return self._target.copy()

    def update_color_from_velocity(self):
        vmag = float(np.linalg.norm(self.tensor.velocity))
        intensity = min(1.0, vmag * VELOCITY_COLOR_SCALE)
        self._color[:] = [0.15 + intensity * 0.7, 0.15, 0.2 + intensity * 0.5, 0.9]


# ── Maze builder ───────────────────────────────────────────────────────────
def build_maze(engine: AetherEngine, w: float, h: float) -> Tuple[StateTensor, List[HapticNode]]:
    """Create core player + haptic-node maze walls."""
    core = StateTensor(w / 2, h / 2, CORE_RADIUS * 2, CORE_RADIUS * 2)
    nodes: List[HapticNode] = []
    # Outer walls
    wall_t = 6.0
    walls = [
        (0, 0, w, wall_t, 0),
        (0, h - wall_t, w, wall_t, 1),
        (0, 0, wall_t, h, 2),
        (w - wall_t, 0, wall_t, h, 3),
    ]
    # Inner barriers
    for i in range(NODE_COUNT):
        bx = 40 + (i % 4) * (w - 80) / 4
        by = 60 + (i // 4) * (h - 120) / 3
        walls.append((bx, by, 8, 40, i + 10))
    for x, y, bw, bh, z in walls:
        node = HapticNode(x, y, bw, bh, z=z)
        engine.register_element(node)
        nodes.append(node)
    return core, nodes


# ── Swipe input via Input-Bridge ───────────────────────────────────────────
class SwipeBridge:
    """Transforms swipe gestures into directional force vectors."""
    def __init__(self, engine: AetherEngine):
        self.engine = engine
        self._active = False
        self._start = (0.0, 0.0)

    def swipe_start(self, x: float, y: float):
        self._active = True
        self._start = (x, y)
        self.engine.input_manager.pointer_down(0, x, y, time.perf_counter())

    def swipe_move(self, x: float, y: float):
        if self._active:
            self.engine.input_manager.pointer_move(x, y, time.perf_counter())

    def swipe_end(self):
        if self._active:
            self.engine.input_manager.pointer_up()
            self._active = False

    def apply_force_to_core(self, core: StateTensor, dx: float, dy: float):
        force = np.array([dx * SWIPE_STIFFNESS, dy * SWIPE_STIFFNESS, 0.0, 0.0], dtype=np.float32)
        core.apply_force(force)


# ── Physics tick with boundary collision ───────────────────────────────────
def tick_engine(engine: AetherEngine, core: StateTensor, nodes: List[HapticNode],
                win_w: float, win_h: float, swipe_dx: float = 0.0, swipe_dy: float = 0.0,
                swipe_bridge: SwipeBridge = None) -> float:
    """Single physics step. Returns frame time in ms."""
    t0 = time.perf_counter()

    if swipe_bridge and (swipe_dx != 0 or swipe_dy != 0):
        swipe_bridge.apply_force_to_core(core, swipe_dx, swipe_dy)

    # Boundary collision forces on core
    from core import solver_bridge as solver
    bf = solver.calculate_boundary_forces(core.state, win_w, win_h, boundary_stiffness=0.5)
    core.apply_force(bf)

    # Damping (kinetic energy decay)
    core.velocity *= np.float32(1.0 - DAMPING)
    core.velocity = clamp_magnitude(core.velocity, MAX_VELOCITY)

    # Integrate core
    core.euler_integrate(1.0 / 60.0, viscosity=0.05)

    # Engine tick for nodes
    engine.tick(win_w, win_h)

    # Update node colors from velocity
    for n in nodes:
        n.update_color_from_velocity()

    return (time.perf_counter() - t0) * 1000.0


# ── Teleportation handler ──────────────────────────────────────────────────
def handle_teleportation(state_mgr: StateManager, core: StateTensor,
                         old_w: float, old_h: float, new_w: float, new_h: float):
    """Reposition core on screen rotation without losing momentum."""
    shock = state_mgr.check_teleportation_shock(int(new_w), int(new_h))
    if shock > 1.0:
        scale_x = new_w / old_w if old_w > 0 else 1.0
        scale_y = new_h / old_h if old_h > 0 else 1.0
        core.state[0] = np.float32(float(core.state[0]) * scale_x)
        core.state[1] = np.float32(float(core.state[1]) * scale_y)
        core.state[2] = np.float32(float(core.state[2]) * scale_x)
        core.state[3] = np.float32(float(core.state[3]) * scale_y)
    return shock


# ── Kivy interactive renderer ──────────────────────────────────────────────
def _run_kivy():
    os.environ["KIVY_LOG_LEVEL"] = "warning"
    from kivy.app import App
    from kivy.uix.widget import Widget
    from kivy.graphics import Color, Rectangle
    from kivy.core.window import Window
    from kivy.clock import Clock

    Window.size = (int(WIN_W), int(WIN_H))
    Window.clearcolor = (0.02, 0.02, 0.04, 1.0)

    engine = AetherEngine()
    core, nodes = build_maze(engine, WIN_W, WIN_H)
    swipe = SwipeBridge(engine)
    state_mgr = StateManager()
    _old_w, _old_h = WIN_W, WIN_H

    class MazeWidget(Widget):
        def __init__(self, **kw):
            super().__init__(**kw)
            Clock.schedule_interval(self._tick, 1.0 / 60.0)

        def _tick(self, dt):
            nonlocal _old_w, _old_h
            cw, ch = self.width or WIN_W, self.height or WIN_H
            if abs(cw - _old_w) > 10 or abs(ch - _old_h) > 10:
                handle_teleportation(state_mgr, core, _old_w, _old_h, cw, ch)
                _old_w, _old_h = cw, ch
            tick_engine(engine, core, nodes, cw, ch, swipe_bridge=swipe)
            self.canvas.clear()
            with self.canvas:
                for n in nodes:
                    s = n.tensor.state
                    r, g, b, a = n._color
                    Color(r, g, b, a)
                    Rectangle(pos=(float(s[0]), float(s[1])), size=(float(s[2]), float(s[3])))
                cs = core.state
                Color(0.3, 0.8, 1.0, 0.9)
                Rectangle(pos=(float(cs[0]), float(cs[1])), size=(float(cs[2]), float(cs[3])))

        def on_touch_down(self, touch):
            swipe.swipe_start(touch.x, touch.y)
            touch.grab(self)
            return True

        def on_touch_move(self, touch):
            if touch.grab_current is self:
                swipe.swipe_move(touch.x, touch.y)
            return True

        def on_touch_up(self, touch):
            if touch.grab_current is self:
                swipe.swipe_end()
            return True

    class MazeApp(App):
        def build(self):
            return MazeWidget()

    MazeApp().run()


if __name__ == "__main__":
    if "--headless" in sys.argv:
        engine = AetherEngine()
        core, nodes = build_maze(engine, WIN_W, WIN_H)
        swipe = SwipeBridge(engine)
        for _ in range(300):
            tick_engine(engine, core, nodes, WIN_W, WIN_H, swipe_bridge=swipe)
        print(f"[OK] Headless maze — {len(nodes)} nodes, core pos=({core.state[0]:.1f},{core.state[1]:.1f})")
    else:
        _run_kivy()
