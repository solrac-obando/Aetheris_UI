# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""Aether-WASM — Python physics engine for Pyodide/WebAssembly.

Runs inside the browser via Pyodide. Exposes AetherEngine to JavaScript
and returns particle positions as a Float32Array for HTML5 Canvas rendering.
"""
import numpy as np

# ── Core imports (works in both WASM and standard Python) ──
try:
    import sys, os
    _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if _root not in sys.path:
        sys.path.insert(0, _root)
except Exception:
    pass

from core.aether_math import StateTensor, MAX_VELOCITY, clamp_magnitude, EPSILON

# JS interop — only available in Pyodide
try:
    from js import Float32Array
    _HAS_PYODIDE = True
except (ImportError, ModuleNotFoundError):
    _HAS_PYODIDE = False
    Float32Array = None

# ── Constants ──────────────────────────────────────────────────────────────
NODE_COUNT = 50
GRAVITY_STRENGTH = 8000.0
DAMPING = 0.98
CENTER_PULL = 0.002
CANVAS_W = 1280.0
CANVAS_H = 720.0


class ParticleNode:
    """Lightweight physics node for WASM — no Kivy dependencies."""
    __slots__ = ('x', 'y', 'vx', 'vy', 'radius', 'mass')

    def __init__(self, x, y, radius=5.0, mass=1.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = 0.0
        self.vy = 0.0
        self.radius = float(radius)
        self.mass = float(mass)


class AetherWASMEngine:
    """WASM-compatible physics engine — no external dependencies beyond numpy."""

    def __init__(self, n: int = NODE_COUNT, seed: int = 42):
        self.nodes = []
        rng = np.random.RandomState(seed)
        for _ in range(n):
            x = rng.uniform(100, CANVAS_W - 100)
            y = rng.uniform(100, CANVAS_H - 100)
            r = rng.uniform(3.0, 8.0)
            m = r / 5.0
            self.nodes.append(ParticleNode(x, y, r, m))
        self._cx = CANVAS_W / 2
        self._cy = CANVAS_H / 2
        self._buf = np.zeros(n * 4, dtype=np.float32)

    def tick(self, mouse_x: float, mouse_y: float, mode: str = "attract") -> "Float32Array":
        """Single physics step. Returns JS Float32Array of [x, y, vx, vy, ...]."""
        n = len(self.nodes)
        for i, node in enumerate(self.nodes):
            fx, fy = 0.0, 0.0

            # Mouse gravity/repel/vortex
            if mouse_x > 0 and mouse_y > 0:
                dx = mouse_x - node.x
                dy = mouse_y - node.y
                dist_sq = dx * dx + dy * dy + 100.0  # softening
                dist = np.sqrt(dist_sq)
                force = GRAVITY_STRENGTH * node.mass / dist_sq

                if mode == "attract":
                    fx += force * dx / dist
                    fy += force * dy / dist
                elif mode == "repel":
                    fx -= force * dx / dist
                    fy -= force * dy / dist
                elif mode == "vortex":
                    fx += force * (-dy / dist) * 0.5 + force * 0.3 * dx / dist
                    fy += force * (dx / dist) * 0.5 + force * 0.3 * dy / dist

            # Center pull (keep particles on screen)
            fx += (self._cx - node.x) * CENTER_PULL
            fy += (self._cy - node.y) * CENTER_PULL

            # Inter-particle repulsion (lightweight, only nearby)
            for j in range(i + 1, min(i + 8, n)):
                other = self.nodes[j]
                rdx = node.x - other.x
                rdy = node.y - other.y
                rd = np.sqrt(rdx * rdx + rdy * rdy) + 1.0
                if rd < 60.0:
                    rep = 20.0 / (rd * rd)
                    fx += rep * rdx / rd
                    fy += rep * rdy / rd
                    self.nodes[j].vx -= rep * rdx / rd * 0.5
                    self.nodes[j].vy -= rep * rdy / rd * 0.5

            # Integrate
            node.vx = (node.vx + fx) * DAMPING
            node.vy = (node.vy + fy) * DAMPING

            # Clamp velocity
            speed = np.sqrt(node.vx ** 2 + node.vy ** 2)
            if speed > MAX_VELOCITY:
                node.vx *= MAX_VELOCITY / speed
                node.vy *= MAX_VELOCITY / speed

            node.x += node.vx
            node.y += node.vy

            # Boundary bounce
            if node.x < node.radius:
                node.x = node.radius
                node.vx *= -0.6
            if node.x > CANVAS_W - node.radius:
                node.x = CANVAS_W - node.radius
                node.vx *= -0.6
            if node.y < node.radius:
                node.y = node.radius
                node.vy *= -0.6
            if node.y > CANVAS_H - node.radius:
                node.y = CANVAS_H - node.radius
                node.vy *= -0.6

            # Pack into buffer
            self._buf[i * 4] = np.float32(node.x)
            self._buf[i * 4 + 1] = np.float32(node.y)
            self._buf[i * 4 + 2] = np.float32(node.vx)
            self._buf[i * 4 + 3] = np.float32(node.vy)

        # Return JS Float32Array in Pyodide, numpy array in standard Python
        if _HAS_PYODIDE and Float32Array is not None:
            return Float32Array.new(self._buf)
        return self._buf

    def reset(self, seed: int = 42) -> None:
        """Reset all particles to initial positions."""
        rng = np.random.RandomState(seed)
        for node in self.nodes:
            node.x = rng.uniform(100, CANVAS_W - 100)
            node.y = rng.uniform(100, CANVAS_H - 100)
            node.vx = 0.0
            node.vy = 0.0

    def get_node_count(self) -> int:
        return len(self.nodes)

    def get_canvas_size(self) -> tuple:
        return (CANVAS_W, CANVAS_H)


# ── Global instance exposed to JS ──────────────────────────────────────────
AetherWASM = AetherWASMEngine(NODE_COUNT)


# ── Fallback for standard Python (non-WASM) testing ───────────────────────
def tick_standard(mx: float, my: float, mode: str = "attract") -> np.ndarray:
    """Standard Python tick — returns numpy array (for local testing)."""
    return AetherWASM.tick(mx, my, mode)
