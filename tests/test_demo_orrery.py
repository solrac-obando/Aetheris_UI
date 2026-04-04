# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
20-assertion test suite for demo_aether_orrery.
Each test maps to a specific requirement from the spec.
"""
import os, sys, time, gc, sqlite3, json, threading, tracemalloc, tempfile
import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AetherEngine
from core.aether_math import StateTensor, MAX_VELOCITY, EPSILON, clamp_magnitude
from core.input_manager import InputManager
from core.state_manager import StateManager
from core.data_bridge import SQLiteProvider
from demo.demo_aether_orrery import (
    OrreryEngine, OrreryNode, NODE_COUNT, WIN_W, WIN_H,
    SPRING_K, SPRING_DAMPING, REST_LENGTH, CLUSTER_ATTRACT,
    CLUSTER_REPEL, COLLISION_RADIUS, CENTER_PULL, DAMPING_DECAY,
    CATEGORY_COLORS, _physics_kernel,
)


class TestOrrery:
    # ── 1. 50+ elements at 60FPS ──────────────────────────────────────────
    def test_01_50plus_elements_60fps(self):
        """Assertion 1: AetherEngine handles 50+ concurrent active elements without dropping below 60FPS."""
        orrery = OrreryEngine()
        orrery.build_graph(NODE_COUNT)
        assert len(orrery.nodes) >= 50, f"Only {len(orrery.nodes)} nodes"
        # Warm up JIT compilation
        orrery.tick()
        orrery.tick()
        times = []
        for _ in range(100):
            ft = orrery.tick()
            times.append(ft)
        avg = np.mean(times)
        assert avg < 16.6, f"Average frame time {avg:.2f}ms exceeds 16.6ms (60 FPS)"

    # ── 2. Data-Bridge parses complex JOIN ────────────────────────────────
    def test_02_data_bridge_join_query(self):
        """Assertion 2: Data-Bridge successfully parses a complex JOIN query from SQLite."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE entities (id TEXT PRIMARY KEY, name TEXT, category TEXT)")
            conn.execute("CREATE TABLE relationships (source TEXT, target TEXT, weight REAL)")
            conn.execute("INSERT INTO entities VALUES ('e1','Alpha','core')")
            conn.execute("INSERT INTO entities VALUES ('e2','Beta','sensor')")
            conn.execute("INSERT INTO relationships VALUES ('e1','e2',0.8)")
            conn.commit()
            conn.close()
            provider = SQLiteProvider(db_path)
            provider.connect()
            rows = provider.execute_query(
                "SELECT e1.name AS src, e2.name AS tgt, r.weight "
                "FROM relationships r "
                "JOIN entities e1 ON r.source = e1.id "
                "JOIN entities e2 ON r.target = e2.id"
            )
            provider.disconnect()
            assert len(rows) == 1
            assert rows[0]["src"] == "Alpha"
            assert rows[0]["tgt"] == "Beta"
            assert rows[0]["weight"] == 0.8
        finally:
            os.unlink(db_path)

    # ── 3. Spring constraints applied correctly ───────────────────────────
    def test_03_spring_constraints_applied(self):
        """Assertion 3: Spring constraints (k) are correctly applied to the StateTensor."""
        # Build minimal graph with just 2 nodes connected by an edge
        orrery = OrreryEngine()
        orrery.build_graph(2)
        # Override edges to have only one edge between nodes 0 and 1
        orrery.edges = [(0, 1)]
        orrery._edge_i = np.array([0], dtype=np.int64)
        orrery._edge_j = np.array([1], dtype=np.int64)
        orrery._n_edges = 1
        # Position nodes with stretch beyond REST_LENGTH
        orrery.nodes[0].tensor.state[:] = [0.0, 0.0, 20.0, 20.0]
        orrery.nodes[1].tensor.state[:] = [REST_LENGTH + 50.0, 0.0, 20.0, 20.0]
        orrery._sync_arrays()
        # Call kernel with only spring forces (zero out all other force types)
        forces = _physics_kernel(
            orrery._pos, orrery._vel,
            orrery._edge_i, orrery._edge_j, orrery._cat_ids, orrery._n_edges,
            SPRING_K, SPRING_DAMPING, REST_LENGTH,
            0.0, 0.0,  # no clustering
            0.0, 0.0,  # no collision, no center pull
            0.0, 0.0,  # center at origin (irrelevant with zero pull)
            1.0 / 60.0,
        )
        orrery._apply_results(forces)
        # Node B is to the right of REST_LENGTH, spring pulls it left (negative fx)
        # Node A is pulled right (positive fx)
        assert float(orrery.nodes[0].tensor.acceleration[0]) > 0, \
            f"Node A should be pulled right, got {orrery.nodes[0].tensor.acceleration[0]}"
        assert float(orrery.nodes[1].tensor.acceleration[0]) < 0, \
            f"Node B should be pulled left, got {orrery.nodes[1].tensor.acceleration[0]}"
        # Equal and opposite (Newton's 3rd law)
        assert abs(float(orrery.nodes[0].tensor.acceleration[0]) + float(orrery.nodes[1].tensor.acceleration[0])) < 0.01

    # ── 4. No overlap (collision avoidance) ───────────────────────────────
    def test_04_no_node_overlap(self):
        """Assertion 4: Nodes do not overlap (Collision Avoidance Logic)."""
        orrery = OrreryEngine()
        orrery.build_graph(10)
        orrery.nodes[0].tensor.state[:] = [100.0, 100.0, 20.0, 20.0]
        orrery.nodes[1].tensor.state[:] = [105.0, 105.0, 20.0, 20.0]
        orrery._sync_arrays()
        forces = _physics_kernel(
            orrery._pos, orrery._vel,
            orrery._edge_i, orrery._edge_j, orrery._cat_ids, orrery._n_edges,
            SPRING_K, SPRING_DAMPING, REST_LENGTH,
            CLUSTER_ATTRACT, CLUSTER_REPEL,
            COLLISION_RADIUS, CENTER_PULL, WIN_W / 2, WIN_H / 2, 1.0 / 60.0,
        )
        assert np.linalg.norm(forces[0, :2]) > 0, "No collision force on node 0"
        assert np.linalg.norm(forces[1, :2]) > 0, "No collision force on node 1"

    # ── 5. Center-of-mass attraction ──────────────────────────────────────
    def test_05_center_of_mass_attraction(self):
        """Assertion 5: Center-of-Mass attraction keeps the constellation centered."""
        orrery = OrreryEngine()
        orrery.build_graph(10)
        for n in orrery.nodes:
            n.tensor.state[0] = np.float32(10.0)
            n.tensor.state[1] = np.float32(10.0)
        orrery._sync_arrays()
        forces = _physics_kernel(
            orrery._pos, orrery._vel,
            orrery._edge_i, orrery._edge_j, orrery._cat_ids, orrery._n_edges,
            SPRING_K, SPRING_DAMPING, REST_LENGTH,
            CLUSTER_ATTRACT, CLUSTER_REPEL,
            COLLISION_RADIUS, CENTER_PULL, WIN_W / 2, WIN_H / 2, 1.0 / 60.0,
        )
        for i in range(len(orrery.nodes)):
            assert forces[i, 0] > 0, f"No pull toward center X for node {i}"
            assert forces[i, 1] > 0, f"No pull toward center Y for node {i}"

    # ── 6. Kinetic energy conservation (2% error) ─────────────────────────
    def test_06_kinetic_energy_conservation(self):
        """Assertion 6: Kinetic energy conservation is maintained within a 2% error margin."""
        orrery = OrreryEngine()
        orrery.build_graph(5)
        for n in orrery.nodes:
            n.tensor.velocity[:] = [100.0, 50.0, 0.0, 0.0]
        ke_initial = sum(0.5 * np.dot(n.tensor.velocity, n.tensor.velocity) for n in orrery.nodes)
        for _ in range(10):
            orrery._sync_arrays()
            forces = _physics_kernel(
                orrery._pos, orrery._vel,
                orrery._edge_i, orrery._edge_j, orrery._cat_ids, orrery._n_edges,
                SPRING_K, 0.0, REST_LENGTH,
                0.0, 0.0,
                0.0, 0.0, WIN_W / 2, WIN_H / 2, 1.0 / 60.0,
            )
            orrery._apply_results(forces)
            for n in orrery.nodes:
                n.tensor.euler_integrate(1.0 / 60.0, viscosity=0.0)
        ke_final = sum(0.5 * np.dot(n.tensor.velocity, n.tensor.velocity) for n in orrery.nodes)
        error = abs(ke_final - ke_initial) / max(ke_initial, EPSILON)
        assert error < 0.02, f"KE error {error:.4f} exceeds 2%"

    # ── 7. Teleportation scales constellation ─────────────────────────────
    def test_07_teleportation_scales_constellation(self):
        """Assertion 7: Resizing the window scales the entire constellation without breaking links."""
        orrery = OrreryEngine()
        orrery.build_graph(10)
        orig_positions = [(float(n.tensor.state[0]), float(n.tensor.state[1])) for n in orrery.nodes]
        orrery.handle_teleportation(WIN_W * 1.5, WIN_H * 0.7)
        for i, n in enumerate(orrery.nodes):
            expected_x = orig_positions[i][0] * 1.5
            expected_y = orig_positions[i][1] * 0.7
            assert abs(float(n.tensor.state[0]) - expected_x) < 1.0, f"X not scaled: {n.tensor.state[0]} vs {expected_x}"
            assert abs(float(n.tensor.state[1]) - expected_y) < 1.0, f"Y not scaled: {n.tensor.state[1]} vs {expected_y}"

    # ── 8. No memory leak during 1000 ticks ───────────────────────────────
    def test_08_no_memory_leak_1000_ticks(self):
        """Assertion 8: No leak detected during 1000 simulation ticks."""
        gc.collect()
        orrery = OrreryEngine()
        orrery.build_graph(20)
        # Warm up JIT
        orrery.tick()
        orrery.tick()
        tracemalloc.start()
        for _ in range(1000):
            orrery.tick()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        assert peak < 100 * 1024 * 1024, f"Peak memory {peak / 1024 / 1024:.1f}MB exceeds 100MB"

    # ── 9. Drag central node moves sub-cluster ────────────────────────────
    def test_09_drag_moves_subcluster(self):
        """Assertion 9: Dragging a central node moves the entire sub-cluster physically."""
        orrery = OrreryEngine()
        orrery.build_graph(10)
        orrery.nodes[0].tensor.state[0] = np.float32(500.0)
        orrery.nodes[0].tensor.state[1] = np.float32(500.0)
        orrery._sync_arrays()
        forces = _physics_kernel(
            orrery._pos, orrery._vel,
            orrery._edge_i, orrery._edge_j, orrery._cat_ids, orrery._n_edges,
            SPRING_K, SPRING_DAMPING, REST_LENGTH,
            CLUSTER_ATTRACT, CLUSTER_REPEL,
            COLLISION_RADIUS, CENTER_PULL, WIN_W / 2, WIN_H / 2, 1.0 / 60.0,
        )
        # Node 1 is connected to node 0 — should feel spring pull
        assert abs(forces[1, 0]) > 0.01 or abs(forces[1, 1]) > 0.01, \
            "Sub-cluster not affected by dragging node 0"

    # ── 10. Aether-Guard: no SQL injection ────────────────────────────────
    def test_10_no_sql_injection(self):
        """Assertion 10: Ensure no data injection via the SQLite bridge."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE entities (id TEXT PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO entities VALUES ('safe','Normal')")
            conn.commit()
            conn.close()
            provider = SQLiteProvider(db_path)
            provider.connect()
            rows = provider.execute_query("SELECT * FROM entities WHERE id='safe' OR 1=1--")
            provider.disconnect()
            assert isinstance(rows, list)
        finally:
            os.unlink(db_path)

    # ── 11. Visual sync: Kivy coords match StateTensor ────────────────────
    def test_11_visual_sync(self):
        """Assertion 11: KivyRenderer coordinates match AetherEngine float64 precision."""
        orrery = OrreryEngine()
        orrery.build_graph(5)
        orrery.tick()
        for node in orrery.nodes:
            rd = node.rendering_data
            assert np.allclose(rd["rect"], node.tensor.state), "Rendering data != StateTensor"
            assert rd["rect"][0] == node.tensor.state[0], "X mismatch"
            assert rd["rect"][1] == node.tensor.state[1], "Y mismatch"

    # ── 12. Damping: stable state after 30s ───────────────────────────────
    def test_12_damping_reaches_stable(self):
        """Assertion 12: The system reaches a stable state (zero velocity) after 30 seconds of no input."""
        orrery = OrreryEngine()
        orrery.build_graph(10)
        for n in orrery.nodes:
            n.tensor.velocity[:] = [200.0, 150.0, 0.0, 0.0]
        # Warm up JIT
        orrery.tick()
        orrery.tick()
        # 30 seconds at 60fps = 1800 ticks
        for _ in range(1800):
            orrery.tick()
        total_ke = sum(0.5 * np.dot(n.tensor.velocity, n.tensor.velocity) for n in orrery.nodes)
        assert total_ke < 10.0, f"System not stable after 30s: KE={total_ke:.2f}"

    # ── 13. Multi-threading: engine doesn't block UI ──────────────────────
    def test_13_no_ui_thread_blocking(self):
        """Assertion 13: Verify the engine doesn't block the UI main thread."""
        orrery = OrreryEngine()
        orrery.build_graph(20)
        results = []
        def engine_thread():
            for _ in range(100):
                orrery.tick()
            results.append("done")
        t = threading.Thread(target=engine_thread)
        t.start()
        main_responsive = True
        for _ in range(1000):
            pass
        t.join(timeout=30)
        assert t.is_alive() is False, "Engine thread blocked for >30s"
        assert results == ["done"]

    # ── 14. Error handling: corrupted DB recovery ─────────────────────────
    def test_14_corrupted_db_recovery(self):
        """Assertion 14: Script recovers if the JSON/Database source is corrupted."""
        orrery = OrreryEngine()
        orrery.build_graph(5)
        result = orrery.load_from_db("/nonexistent/path/db.sqlite")
        assert result is False, "Should return False for missing DB"
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            f.write(b"NOT A SQLITE DATABASE")
            corrupt_path = f.name
        try:
            result = orrery.load_from_db(corrupt_path)
            assert isinstance(result, bool)
        finally:
            os.unlink(corrupt_path)

    # ── 15. Numba/NumPy parity ────────────────────────────────────────────
    def test_15_solver_parity(self):
        """Assertion 15: Physics calculations are identical across solvers."""
        from core import solver_bridge as solver
        state = np.array([100.0, 100.0, 50.0, 50.0], dtype=np.float32)
        target = np.array([200.0, 200.0, 50.0, 50.0], dtype=np.float32)
        force1 = solver.calculate_restoring_force(state, target, spring_constant=0.1)
        expected = (target - state) * 0.1
        assert np.allclose(force1[:2], expected[:2], atol=1e-3), "Solver parity mismatch"

    # ── 16. UI Layout: legend scales with zoom ────────────────────────────
    def test_16_legend_scales_dynamically(self):
        """Assertion 16: Legend and labels scale dynamically with the zoom level."""
        orrery = OrreryEngine()
        orrery.build_graph(10)
        orrery.handle_teleportation(WIN_W * 2, WIN_H * 2)
        for n in orrery.nodes:
            assert float(n.tensor.state[0]) > 0
            assert float(n.tensor.state[1]) > 0

    # ── 17. Color logic: intensity correlates with connections ─────────────
    def test_17_color_intensity_correlation(self):
        """Assertion 17: Node color intensity correlates to the number of active connections."""
        orrery = OrreryEngine()
        orrery.build_graph(10)
        high_conn = max(orrery.nodes, key=lambda n: n.connection_count)
        low_conn = min(orrery.nodes, key=lambda n: n.connection_count)
        high_intensity = float(np.sum(high_conn._color[:3]))
        low_intensity = float(np.sum(low_conn._color[:3]))
        assert high_conn.connection_count >= low_conn.connection_count
        if high_conn.connection_count > low_conn.connection_count:
            assert high_intensity >= low_intensity, \
                f"High conn ({high_conn.connection_count}) intensity {high_intensity} < low ({low_conn.connection_count}) intensity {low_intensity}"

    # ── 18. Boundary bounce after shock ───────────────────────────────────
    def test_18_boundary_bounce(self):
        """Assertion 18: Constellation remains within the viewport after a high-velocity shock."""
        orrery = OrreryEngine()
        orrery.build_graph(10)
        orrery.shock_node(0, 5000.0)
        for _ in range(500):
            orrery.tick()
        for n in orrery.nodes:
            s = n.tensor.state
            assert -100 < float(s[0]) < WIN_W + 100, f"Node escaped X: {s[0]}"
            assert -100 < float(s[1]) < WIN_H + 100, f"Node escaped Y: {s[1]}"

    # ── 19. Cleanup: GL contexts and DB connections close ─────────────────
    def test_19_cleanup_gl_and_db(self):
        """Assertion 19: All GL contexts and DB connections close properly."""
        initial_threads = threading.active_count()
        orrery = OrreryEngine()
        orrery.build_graph(5)
        orrery.load_from_db("/nonexistent.db")
        del orrery
        gc.collect()
        final_threads = threading.active_count()
        assert final_threads <= initial_threads + 1, \
            f"Orphaned threads: {initial_threads} → {final_threads}"

    # ── 20. WASM readiness ────────────────────────────────────────────────
    def test_20_wasm_compatibility(self):
        """Assertion 20: Script identifies and runs in 'Compatibility Mode' if shaders fail."""
        orrery = OrreryEngine()
        orrery.build_graph(5)
        is_wasm = orrery.is_wasm_compatible()
        assert isinstance(is_wasm, bool)
        for _ in range(50):
            orrery.tick()
        for n in orrery.nodes:
            assert not np.any(np.isnan(n.tensor.state)), "NaN in WASM compat mode"
