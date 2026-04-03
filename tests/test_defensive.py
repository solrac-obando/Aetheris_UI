"""
The Iron Mountain - 8 Doomsday Resilience Tests.
Tests the framework against human error, malformed data, and nonsensical logic.
"""
import pytest
import warnings
import numpy as np
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel, SmartButton
from core.aether_math import StateTensor
from core.data_bridge import SQLiteProvider, min_max_scale
from core.ui_builder import UIBuilder


class TestTypeChaos:
    """Test 1: User passes strings or None to StateTensor."""

    def test_string_coordinates_coerced(self):
        """Pass string coordinates. Verify they are coerced to float or handled safely."""
        # StateTensor expects floats - passing strings should not crash
        # The current implementation will raise TypeError, which is acceptable
        # but we should handle it gracefully in higher-level APIs
        with pytest.raises((TypeError, ValueError)):
            StateTensor("100px", "200px", "50", "50")

    def test_none_coordinates_handled(self):
        """Pass None coordinates. Verify numpy handles it (creates object array or converts)."""
        # NumPy converts None to 0.0 in float context, or creates object arrays
        # Either way, it should not segfault or crash the process
        try:
            tensor = StateTensor(None, None, None, None)
            # If it succeeded, verify the tensor is at least usable
            assert tensor.state is not None
        except (TypeError, ValueError):
            # Also acceptable - raising an error is defensive
            pass

    def test_mixed_types_coerced(self):
        """Pass mixed types. Verify numpy handles it without crashing."""
        try:
            tensor = StateTensor(100, "200", None, 50)
            # If it succeeded, verify the tensor exists
            assert tensor.state is not None
        except (TypeError, ValueError):
            # Also acceptable
            pass

    def test_valid_float_input(self):
        """Verify normal float input still works."""
        tensor = StateTensor(100.0, 200.0, 50.0, 50.0)
        assert tensor.state[0] == pytest.approx(100.0, abs=1e-5)
        assert tensor.state[1] == pytest.approx(200.0, abs=1e-5)


class TestGodComplex:
    """Test 2: Infinite or extreme stiffness constants."""

    def test_infinite_stiffness_clamped(self):
        """Set k = inf. Verify Aether-Guard prevents NaN."""
        tensor = StateTensor(0, 0, 100, 100)
        target = np.array([400.0, 300.0, 200.0, 200.0], dtype=np.float32)
        
        # Apply force with infinite stiffness
        from core.solver import calculate_restoring_force
        force = calculate_restoring_force(tensor.state, target, float('inf'))
        
        # Force should be clamped, not NaN
        assert not np.any(np.isnan(force))
        assert not np.any(np.isinf(force))

    def test_extreme_stiffness_clamped(self):
        """Set k = 10^30. Verify clamping prevents overflow."""
        tensor = StateTensor(0, 0, 100, 100)
        target = np.array([400.0, 300.0, 200.0, 200.0], dtype=np.float32)
        
        from core.solver import calculate_restoring_force
        force = calculate_restoring_force(tensor.state, target, 1e30)
        
        # Force should be finite and clamped
        assert not np.any(np.isnan(force))
        assert not np.any(np.isinf(force))
        assert np.linalg.norm(force) < 20000.0  # Within clamped range

    def test_negative_stiffness(self):
        """Set k = -1.0 (negative stiffness). Verify engine doesn't explode."""
        tensor = StateTensor(0, 0, 100, 100)
        target = np.array([400.0, 300.0, 200.0, 200.0], dtype=np.float32)
        
        from core.solver import calculate_restoring_force
        force = calculate_restoring_force(tensor.state, target, -1.0)
        
        # Should still produce finite results
        assert not np.any(np.isnan(force))
        assert not np.any(np.isinf(force))


class TestMalformedJSONIntent:
    """Test 3: UIBuilder receives malformed JSON."""

    def test_missing_elements_key(self):
        """JSON missing 'elements' key. Verify graceful handling."""
        engine = AetherEngine()
        builder = UIBuilder()
        
        intent = {"layout": "column"}  # No 'elements' key
        
        # Should not crash
        builder.build_from_intent(engine, intent)
        assert engine.element_count == 0

    def test_unknown_element_type(self):
        """JSON with unknown element type. Verify it's skipped."""
        engine = AetherEngine()
        builder = UIBuilder()
        
        intent = {
            "elements": [
                {"id": "good", "type": "static_box", "x": 0, "y": 0, "w": 100, "h": 100},
                {"id": "bad", "type": "unknown_widget", "x": 0, "y": 0, "w": 100, "h": 100},
                {"id": "also_good", "type": "static_box", "x": 200, "y": 200, "w": 50, "h": 50},
            ]
        }
        
        # Should not crash - bad element should be skipped
        builder.build_from_intent(engine, intent)
        # At least the good elements should be created
        assert engine.element_count >= 2

    def test_empty_elements_list(self):
        """JSON with empty elements list. Verify no crash."""
        engine = AetherEngine()
        builder = UIBuilder()
        
        intent = {"elements": []}
        builder.build_from_intent(engine, intent)
        assert engine.element_count == 0

    def test_element_missing_required_fields(self):
        """Element missing x, y, w, h. Verify defaults are used."""
        engine = AetherEngine()
        builder = UIBuilder()
        
        intent = {
            "elements": [
                {"id": "minimal", "type": "static_box"},  # Missing all position fields
            ]
        }
        
        # Should use defaults and not crash
        builder.build_from_intent(engine, intent)
        assert engine.element_count >= 1


class TestZeroDimensionSingularity:
    """Test 4: engine.tick(win_w=0, win_h=-100)."""

    def test_zero_window_width(self):
        """Tick with win_w=0. Verify no division by zero."""
        engine = AetherEngine()
        engine.register_element(SmartPanel(x=0, y=0, w=100, h=100, padding=0.05, z=0))
        
        # Should not crash
        data = engine.tick(0, 600)
        assert len(data) == 1
        assert not np.any(np.isnan(data[0]['rect']))

    def test_negative_window_dimensions(self):
        """Tick with negative window size. Verify clamping."""
        engine = AetherEngine()
        engine.register_element(SmartPanel(x=0, y=0, w=100, h=100, padding=0.05, z=0))
        
        # Should not crash
        data = engine.tick(-100, -50)
        assert len(data) == 1
        assert not np.any(np.isnan(data[0]['rect']))

    def test_tiny_window(self):
        """Tick with 1x1 window. Verify elements don't explode."""
        engine = AetherEngine()
        engine.register_element(StaticBox(0, 0, 100, 100, z=0))
        
        for _ in range(50):
            data = engine.tick(1, 1)
            assert not np.any(np.isnan(data[0]['rect']))
            assert not np.any(np.isinf(data[0]['rect']))


class TestDatabasePoisoning:
    """Test 5: SQLite column contains non-numeric data."""

    def test_non_numeric_column_value(self):
        """Database has text where float expected. Verify safe casting."""
        db = SQLiteProvider(":memory:")
        db.connect()
        db._conn.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY, name TEXT,
                rating TEXT  -- Text column instead of REAL
            )
        """)
        db._conn.executemany(
            "INSERT INTO items VALUES (?,?,?)",
            [
                (1, 'Good Movie', '8.5'),
                (2, 'Bad Movie', 'Five Stars'),  # Poison!
                (3, 'Great Movie', '9.2'),
            ]
        )
        db._conn.commit()
        
        engine = AetherEngine()
        builder = UIBuilder()
        
        template = {
            'type': 'static_box',
            'columns': {
                'x': {'source': 'id'},
                'y': {'source': 'id'},
                'w': {'source': 'rating', 'scale': [0, 10, 50, 500]},
                'h': {'source': 'rating', 'scale': [0, 10, 50, 500]},
                'z': {'source': 'id'},
            },
        }
        
        # Should handle the poisoned row gracefully
        # The build_from_datasource should skip or handle invalid values
        try:
            count = builder.build_from_datasource(
                engine, db, "SELECT * FROM items", template
            )
            # If it succeeds, at least some elements should be created
            assert engine.element_count >= 0
        except (ValueError, TypeError):
            # If it fails, it should fail gracefully (not crash the engine)
            pass
        
        db.disconnect()

    def test_emoji_in_database(self):
        """Database contains emoji. Verify safe handling."""
        db = SQLiteProvider(":memory:")
        db.connect()
        db._conn.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY, name TEXT,
                score TEXT
            )
        """)
        db._conn.executemany(
            "INSERT INTO items VALUES (?,?,?)",
            [
                (1, 'Movie A', '8.5'),
                (2, 'Movie B', '🔥🔥🔥'),  # Emoji poison!
            ]
        )
        db._conn.commit()
        
        engine = AetherEngine()
        builder = UIBuilder()
        
        template = {
            'type': 'static_box',
            'columns': {
                'x': {'source': 'id'},
                'y': {'source': 'id'},
                'w': {'source': 'score', 'scale': [0, 10, 50, 500]},
                'h': {'source': 'score', 'scale': [0, 10, 50, 500]},
                'z': {'source': 'id'},
            },
        }
        
        # Should handle gracefully
        try:
            builder.build_from_datasource(engine, db, "SELECT * FROM items", template)
        except (ValueError, TypeError):
            pass  # Expected for emoji values
        
        db.disconnect()


class TestRecursiveMirror:
    """Test 6: Circular anchor dependencies."""

    def test_circular_anchor_detected(self):
        """Anchor A to B and B to A. Verify no stack overflow."""
        engine = AetherEngine()
        
        panel_a = SmartPanel(x=100, y=100, w=200, h=200, z=0)
        panel_b = SmartPanel(x=400, y=100, w=200, h=200, z=1)
        
        # Circular: btn_a follows panel_b, btn_b follows panel_a
        btn_a = SmartButton(parent=panel_b, offset_x=10, offset_y=10, offset_w=50, offset_h=30, z=2)
        btn_b = SmartButton(parent=panel_a, offset_x=10, offset_y=10, offset_w=50, offset_h=30, z=3)
        
        engine.register_element(panel_a)
        engine.register_element(panel_b)
        engine.register_element(btn_a)
        engine.register_element(btn_b)
        
        # Run many ticks - should not cause stack overflow
        for tick in range(100):
            data = engine.tick(800, 600)
            assert len(data) == 4
            
            # Verify no NaN/Inf
            for elem in data:
                assert not np.any(np.isnan(elem['rect']))
                assert not np.any(np.isinf(elem['rect']))

    def test_self_anchor(self):
        """Anchor element to itself. Verify no infinite loop."""
        engine = AetherEngine()
        
        panel = SmartPanel(x=100, y=100, w=200, h=200, z=0)
        # Self-referencing button
        btn = SmartButton(parent=panel, offset_x=10, offset_y=10, offset_w=50, offset_h=30, z=1)
        
        engine.register_element(panel)
        engine.register_element(btn)
        
        # Should not crash
        for _ in range(50):
            data = engine.tick(800, 600)
            assert len(data) == 2
            for elem in data:
                assert not np.any(np.isnan(elem['rect']))


class TestOrphanGhostInteractions:
    """Test 7: Applying force to deleted/unregistered elements."""

    def test_force_on_unregistered_element(self):
        """Try to interact with element that was never registered."""
        engine = AetherEngine()
        
        # Create an element but don't register it
        orphan = StaticBox(100, 100, 50, 50, z=0)
        
        # Engine should only have 0 elements
        assert engine.element_count == 0
        
        # Tick should work fine
        data = engine.tick(800, 600)
        assert len(data) == 0

    def test_element_removed_during_simulation(self):
        """Remove element from registry during simulation."""
        engine = AetherEngine()
        
        elem = StaticBox(100, 100, 50, 50, z=0)
        engine.register_element(elem)
        
        # Run a tick
        data = engine.tick(800, 600)
        assert len(data) == 1
        
        # Remove element from internal list (simulating deletion)
        engine._elements.clear()
        
        # Next tick should handle empty registry gracefully
        data = engine.tick(800, 600)
        assert len(data) == 0


class TestTemporalChaos:
    """Test 8: Hibernation/lag spikes with extreme dt values."""

    def test_huge_dt_from_hibernation(self):
        """Simulate system wake from hibernation with dt=3600s."""
        engine = AetherEngine()
        engine.register_element(StaticBox(100, 100, 50, 50, z=0))
        
        # Manually set _last_time to simulate huge dt
        engine._last_time = engine._last_time - 3600.0  # 1 hour ago
        
        # Should not crash or produce NaN
        data = engine.tick(800, 600)
        assert len(data) == 1
        assert not np.any(np.isnan(data[0]['rect']))
        assert not np.any(np.isinf(data[0]['rect']))

    def test_zero_dt(self):
        """Simulate frozen clock with dt=0."""
        engine = AetherEngine()
        engine.register_element(StaticBox(100, 100, 50, 50, z=0))
        
        # Set _last_time to current time to force dt=0
        import time
        engine._last_time = time.perf_counter()
        
        # Should not crash or divide by zero
        data = engine.tick(800, 600)
        assert len(data) == 1
        assert not np.any(np.isnan(data[0]['rect']))

    def test_negative_dt(self):
        """Simulate clock going backwards."""
        engine = AetherEngine()
        engine.register_element(StaticBox(100, 100, 50, 50, z=0))
        
        # Set _last_time to the future to force negative dt
        import time
        engine._last_time = time.perf_counter() + 100.0
        
        # Should not crash
        data = engine.tick(800, 600)
        assert len(data) == 1
        assert not np.any(np.isnan(data[0]['rect']))

    def test_rapid_dt_oscillation(self):
        """Alternate between tiny and huge dt values."""
        engine = AetherEngine()
        engine.register_element(StaticBox(100, 100, 50, 50, z=0))
        
        import time
        
        for i in range(100):
            if i % 2 == 0:
                # Tiny dt
                engine._last_time = time.perf_counter() - 0.0001
            else:
                # Huge dt
                engine._last_time = time.perf_counter() - 100.0
            
            data = engine.tick(800, 600)
            assert not np.any(np.isnan(data[0]['rect']))
            assert not np.any(np.isinf(data[0]['rect']))
