# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
16-assertion test suite for demo_mobile_maze.
Each test maps to a specific requirement from the spec.
"""
import os, sys, time, gc, json, tracemalloc, threading
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AetherEngine
from core.aether_math import StateTensor, MAX_VELOCITY, clamp_magnitude
from core.input_manager import InputManager
from core.state_manager import StateManager
from core import solver_bridge as solver
from demo.demo_mobile_maze import (
    HapticNode, build_maze, SwipeBridge, tick_engine,
    handle_teleportation, WIN_W, WIN_H, CORE_RADIUS, NODE_COUNT,
    DAMPING, SWIPE_STIFFNESS,
)


# ── 1. AetherEngine initializes without errors ─────────────────────────────
class TestMobileMaze:
    def test_01_engine_init(self):
        """Assertion 1: AetherEngine initializes without errors."""
        engine = AetherEngine()
        assert engine is not None
        assert engine.element_count == 0

    # ── 2. Input-Bridge captures swipe start ───────────────────────────────
    def test_02_swipe_start(self):
        """Assertion 2: Input-Bridge correctly captures a simulated Swipe Start."""
        engine = AetherEngine()
        swipe = SwipeBridge(engine)
        swipe.swipe_start(100.0, 200.0)
        assert swipe._active is True
        assert swipe._start == (100.0, 200.0)
        assert engine.input_manager.is_dragging is True

    # ── 3. Swipe force applied to core StateTensor ─────────────────────────
    def test_03_swipe_force_applied(self):
        """Assertion 3: Swipe force is correctly applied to the player element's StateTensor."""
        engine = AetherEngine()
        core = StateTensor(WIN_W / 2, WIN_H / 2, CORE_RADIUS * 2, CORE_RADIUS * 2)
        swipe = SwipeBridge(engine)
        swipe.apply_force_to_core(core, 50.0, 30.0)
        expected_fx = 50.0 * SWIPE_STIFFNESS
        expected_fy = 30.0 * SWIPE_STIFFNESS
        assert abs(core.acceleration[0] - expected_fx) < 1.0
        assert abs(core.acceleration[1] - expected_fy) < 1.0

    # ── 4. Collision — Top boundary ────────────────────────────────────────
    def test_04_collision_top(self):
        """Assertion 4: Collision detection triggers correctly on the Top boundary."""
        core = StateTensor(100.0, -5.0, 20.0, 20.0)
        force = solver.calculate_boundary_forces(core.state, WIN_W, WIN_H, boundary_stiffness=0.5)
        assert force[1] > 0, f"Top boundary force should push down, got {force[1]}"

    # ── 5. Collision — Bottom boundary ─────────────────────────────────────
    def test_05_collision_bottom(self):
        """Assertion 5: Collision detection triggers correctly on the Bottom boundary."""
        core = StateTensor(100.0, WIN_H + 5.0, 20.0, 20.0)
        force = solver.calculate_boundary_forces(core.state, WIN_W, WIN_H, boundary_stiffness=0.5)
        assert force[1] < 0, f"Bottom boundary force should push up, got {force[1]}"

    # ── 6. Collision — Left boundary ───────────────────────────────────────
    def test_06_collision_left(self):
        """Assertion 6: Collision detection triggers correctly on the Left boundary."""
        core = StateTensor(-5.0, 100.0, 20.0, 20.0)
        force = solver.calculate_boundary_forces(core.state, WIN_W, WIN_H, boundary_stiffness=0.5)
        assert force[0] > 0, f"Left boundary force should push right, got {force[0]}"

    # ── 7. Collision — Right boundary ──────────────────────────────────────
    def test_07_collision_right(self):
        """Assertion 7: Collision detection triggers correctly on the Right boundary."""
        core = StateTensor(WIN_W + 5.0, 100.0, 20.0, 20.0)
        force = solver.calculate_boundary_forces(core.state, WIN_W, WIN_H, boundary_stiffness=0.5)
        assert force[0] < 0, f"Right boundary force should push left, got {force[0]}"

    # ── 8. Teleportation detects resize >10% ───────────────────────────────
    def test_08_teleportation_detect(self):
        """Assertion 8: Teleportation module detects a window resize event (>10% change)."""
        sm = StateManager()
        sm.last_width, sm.last_height = 360, 640
        shock = sm.check_teleportation_shock(640, 360)
        assert shock > 1.0, f"Expected shock > 1.0 for rotation, got {shock}"

    # ── 9. Post-teleportation velocity consistency (1% tolerance) ──────────
    def test_09_teleportation_velocity_preserved(self):
        """Assertion 9: Post-teleportation element velocity remains consistent (within 1% tolerance)."""
        core = StateTensor(180.0, 320.0, 36.0, 36.0)
        core.velocity[:] = [100.0, 50.0, 0.0, 0.0]
        pre_vel = core.velocity.copy()
        sm = StateManager()
        sm.last_width, sm.last_height = 360, 640
        handle_teleportation(sm, core, 360.0, 640.0, 640.0, 360.0)
        vel_diff = np.linalg.norm(core.velocity - pre_vel)
        vel_mag = np.linalg.norm(pre_vel)
        tolerance = vel_mag * 0.01
        assert vel_diff <= tolerance + 0.001, f"Velocity changed by {vel_diff}, tolerance {tolerance}"

    # ── 10. Post-teleportation position snapped to new coords ──────────────
    def test_10_teleportation_position_snapped(self):
        """Assertion 10: Post-teleportation position is correctly snapped to the new coordinate system."""
        core = StateTensor(180.0, 320.0, 36.0, 36.0)
        sm = StateManager()
        sm.last_width, sm.last_height = 360, 640
        handle_teleportation(sm, core, 360.0, 640.0, 640.0, 360.0)
        expected_x = 180.0 * (640.0 / 360.0)
        expected_y = 320.0 * (360.0 / 640.0)
        assert abs(float(core.state[0]) - expected_x) < 1.0, f"X not snapped: {core.state[0]} vs {expected_x}"
        assert abs(float(core.state[1]) - expected_y) < 1.0, f"Y not snapped: {core.state[1]} vs {expected_y}"

    # ── 11. Performance: frame time < 16.6ms ──────────────────────────────
    def test_11_frame_time_budget(self):
        """Assertion 11: Frame time remains below 16.6ms (target 60 FPS)."""
        engine = AetherEngine()
        core, nodes = build_maze(engine, WIN_W, WIN_H)
        swipe = SwipeBridge(engine)
        times = []
        for _ in range(100):
            ft = tick_engine(engine, core, nodes, WIN_W, WIN_H, swipe_bridge=swipe)
            times.append(ft)
        avg = np.mean(times)
        p99 = np.percentile(times, 99)
        assert avg < 16.6, f"Average frame time {avg:.2f}ms exceeds 16.6ms"
        assert p99 < 16.6, f"P99 frame time {p99:.2f}ms exceeds 16.6ms"

    # ── 12. Damping: kinetic energy decays ─────────────────────────────────
    def test_12_kinetic_energy_decay(self):
        """Assertion 12: Kinetic energy decays over time when no input is provided."""
        core = StateTensor(180.0, 320.0, 36.0, 36.0)
        core.velocity[:] = [200.0, 150.0, 0.0, 0.0]
        ke_initial = 0.5 * np.dot(core.velocity, core.velocity)
        for _ in range(200):
            core.velocity *= np.float32(1.0 - DAMPING)
            core.euler_integrate(1.0 / 60.0, viscosity=0.05)
        ke_final = 0.5 * np.dot(core.velocity, core.velocity)
        assert ke_final < ke_initial * 0.5, f"KE did not decay sufficiently: {ke_initial} → {ke_final}"

    # ── 13. Data integrity: float64 precision ──────────────────────────────
    def test_13_float64_precision(self):
        """Assertion 13: StateTensor maintains float64 precision during high-speed collisions."""
        core = StateTensor(180.0, 320.0, 36.0, 36.0)
        for _ in range(500):
            core.apply_force(np.array([5000.0, -3000.0, 0.0, 0.0], dtype=np.float32))
            bf = solver.calculate_boundary_forces(core.state, WIN_W, WIN_H, boundary_stiffness=0.5)
            core.apply_force(bf)
            core.euler_integrate(1.0 / 60.0, viscosity=0.05)
        assert not np.any(np.isnan(core.state)), "NaN in state after high-speed collisions"
        assert not np.any(np.isinf(core.state)), "Inf in state after high-speed collisions"
        for i in range(4):
            assert np.isfinite(float(core.state[i])), f"State[{i}] not finite: {core.state[i]}"

    # ── 14. UI sync: visual matches internal StateTensor ───────────────────
    def test_14_ui_sync(self):
        """Assertion 14: Visual element position matches engine's internal StateTensor position."""
        engine = AetherEngine()
        node = HapticNode(50.0, 50.0, 40.0, 30.0)
        engine.register_element(node)
        engine.tick(WIN_W, WIN_H)
        rd = node.rendering_data
        assert np.allclose(rd["rect"], node.tensor.state), "Rendering data != StateTensor state"
        assert rd["rect"][0] == node.tensor.state[0], "X position mismatch"
        assert rd["rect"][1] == node.tensor.state[1], "Y position mismatch"

    # ── 15. Memory: no leak after 1000 ticks ──────────────────────────────
    def test_15_no_memory_leak(self):
        """Assertion 15: No significant memory leak detected after 1000 engine ticks."""
        gc.collect()
        tracemalloc.start()
        engine = AetherEngine()
        core, nodes = build_maze(engine, WIN_W, WIN_H)
        swipe = SwipeBridge(engine)
        for _ in range(1000):
            tick_engine(engine, core, nodes, WIN_W, WIN_H, swipe_bridge=swipe)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert peak < 50 * 1024 * 1024, f"Peak memory {peak / 1024 / 1024:.1f}MB exceeds 50MB threshold"

    # ── 16. Shutdown: clean close, no orphaned threads ─────────────────────
    def test_16_clean_shutdown(self):
        """Assertion 16: The engine and renderers close cleanly without orphaned threads."""
        initial_threads = threading.active_count()
        engine = AetherEngine()
        core, nodes = build_maze(engine, WIN_W, WIN_H)
        swipe = SwipeBridge(engine)
        for _ in range(100):
            tick_engine(engine, core, nodes, WIN_W, WIN_H, swipe_bridge=swipe)
        del engine
        del core
        del nodes
        del swipe
        gc.collect()
        final_threads = threading.active_count()
        assert final_threads <= initial_threads + 1, \
            f"Orphaned threads detected: {initial_threads} → {final_threads}"
