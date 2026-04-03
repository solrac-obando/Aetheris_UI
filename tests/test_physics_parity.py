"""
Tests for solver parity (Numba vs NumPy) and engine integration.
"""
import pytest
import numpy as np
from core.solver import (
    calculate_restoring_force as restoring_numba,
    calculate_boundary_forces as boundary_numba,
)
from core.solver_wasm import (
    calculate_restoring_force as restoring_numpy,
    calculate_boundary_forces as boundary_numpy,
)
from core.engine import AetherEngine
from core.ui_builder import UIBuilder
from core.data_bridge import SQLiteProvider


class TestSolverParity:
    """Verify that Numba and NumPy solvers produce identical results."""

    def test_restoring_force_parity(self):
        """Test that Hooke's Law produces identical forces in both solvers."""
        current = np.array([100.0, 200.0, 50.0, 50.0], dtype=np.float32)
        target = np.array([400.0, 300.0, 200.0, 150.0], dtype=np.float32)
        k = 0.15

        force_numba = restoring_numba(current, target, k)
        force_numpy = restoring_numpy(current, target, k)

        np.testing.assert_allclose(force_numba, force_numpy, atol=1e-6)

    def test_restoring_force_zero_error(self):
        """Test that zero displacement produces zero force in both solvers."""
        state = np.array([100.0, 100.0, 100.0, 100.0], dtype=np.float32)
        k = 0.5

        force_numba = restoring_numba(state, state, k)
        force_numpy = restoring_numpy(state, state, k)

        np.testing.assert_allclose(force_numba, np.zeros(4, dtype=np.float32), atol=1e-6)
        np.testing.assert_allclose(force_numpy, np.zeros(4, dtype=np.float32), atol=1e-6)

    def test_boundary_forces_parity_no_violation(self):
        """Test that boundary forces are identical when element is inside bounds."""
        state = np.array([100.0, 100.0, 50.0, 50.0], dtype=np.float32)
        stiffness = 0.5

        force_numba = boundary_numba(state, 800, 600, stiffness)
        force_numpy = boundary_numpy(state, 800, 600, stiffness)

        np.testing.assert_allclose(force_numba, force_numpy, atol=1e-6)
        np.testing.assert_allclose(force_numba, np.zeros(4, dtype=np.float32), atol=1e-6)

    def test_boundary_forces_parity_left_violation(self):
        """Test boundary forces parity when element crosses left boundary."""
        state = np.array([-50.0, 100.0, 100.0, 100.0], dtype=np.float32)
        stiffness = 0.5

        force_numba = boundary_numba(state, 800, 600, stiffness)
        force_numpy = boundary_numpy(state, 800, 600, stiffness)

        np.testing.assert_allclose(force_numba, force_numpy, atol=1e-6)
        assert force_numba[0] > 0  # Should push right

    def test_boundary_forces_parity_right_violation(self):
        """Test boundary forces parity when element crosses right boundary."""
        state = np.array([750.0, 100.0, 100.0, 100.0], dtype=np.float32)  # x+w=850 > 800
        stiffness = 0.5

        force_numba = boundary_numba(state, 800, 600, stiffness)
        force_numpy = boundary_numpy(state, 800, 600, stiffness)

        np.testing.assert_allclose(force_numba, force_numpy, atol=1e-6)
        assert force_numba[0] < 0  # Should push left

    def test_boundary_forces_parity_top_violation(self):
        """Test boundary forces parity when element crosses top boundary."""
        state = np.array([100.0, -30.0, 100.0, 100.0], dtype=np.float32)
        stiffness = 0.5

        force_numba = boundary_numba(state, 800, 600, stiffness)
        force_numpy = boundary_numpy(state, 800, 600, stiffness)

        np.testing.assert_allclose(force_numba, force_numpy, atol=1e-6)
        assert force_numba[1] > 0  # Should push down

    def test_boundary_forces_parity_bottom_violation(self):
        """Test boundary forces parity when element crosses bottom boundary."""
        state = np.array([100.0, 550.0, 100.0, 100.0], dtype=np.float32)  # y+h=650 > 600
        stiffness = 0.5

        force_numba = boundary_numba(state, 800, 600, stiffness)
        force_numpy = boundary_numpy(state, 800, 600, stiffness)

        np.testing.assert_allclose(force_numba, force_numpy, atol=1e-6)
        assert force_numba[1] < 0  # Should push up

    def test_large_disparity_forces(self):
        """Test parity with extreme values that could cause overflow."""
        current = np.array([-10000.0, 10000.0, 0.001, 0.001], dtype=np.float32)
        target = np.array([10000.0, -10000.0, 1000.0, 1000.0], dtype=np.float32)
        k = 10.0

        force_numba = restoring_numba(current, target, k)
        force_numpy = restoring_numpy(current, target, k)

        np.testing.assert_allclose(force_numba, force_numpy, atol=1e-3)


class TestUIBuilderDatasource:
    """Tests for UIBuilder.build_from_datasource integration."""

    def test_build_from_datasource_creates_elements(self):
        """Test that build_from_datasource creates and registers elements."""
        # Set up in-memory SQLite with test data
        db = SQLiteProvider(":memory:")
        db.connect()
        db._conn.execute("""
            CREATE TABLE items (
                id INTEGER PRIMARY KEY, name TEXT,
                pos_x REAL, pos_y REAL,
                item_w REAL, item_h REAL
            )
        """)
        db._conn.executemany(
            "INSERT INTO items VALUES (?,?,?,?,?,?)",
            [
                (1, 'Item A', 10.0, 20.0, 100.0, 80.0),
                (2, 'Item B', 200.0, 50.0, 150.0, 120.0),
                (3, 'Item C', 400.0, 100.0, 80.0, 60.0),
            ]
        )
        db._conn.commit()

        engine = AetherEngine()
        builder = UIBuilder()

        template = {
            'type': 'static_box',
            'columns': {
                'x': {'source': 'pos_x'},
                'y': {'source': 'pos_y'},
                'w': {'source': 'item_w'},
                'h': {'source': 'item_h'},
                'z': {'source': 'id'},
            },
            'metadata_fields': ['name'],
        }

        count = builder.build_from_datasource(engine, db, "SELECT * FROM items", template)
        
        assert count == 3
        assert engine.element_count == 3
        
        # Verify physics works
        data = engine.tick(800, 600)
        assert len(data) == 3
        
        db.disconnect()

    def test_build_from_datasource_with_normalization(self):
        """Test that Min-Max scaling is applied to database values."""
        db = SQLiteProvider(":memory:")
        db.connect()
        db._conn.execute("""
            CREATE TABLE movies (
                id INTEGER PRIMARY KEY, title TEXT,
                rating_count INTEGER
            )
        """)
        db._conn.executemany(
            "INSERT INTO movies VALUES (?,?,?)",
            [
                (1, 'Movie A', 1000),
                (2, 'Movie B', 5000),
                (3, 'Movie C', 9000),
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
                'w': {'source': 'rating_count', 'scale': [1000, 9000, 50.0, 500.0]},
                'h': {'source': 'rating_count', 'scale': [1000, 9000, 50.0, 500.0]},
                'z': {'source': 'id'},
            },
            'metadata_fields': ['title'],
        }

        builder.build_from_datasource(engine, db, "SELECT * FROM movies", template)
        data = engine.tick(800, 600)
        
        # Movie A (1000 ratings) should have smallest width (50px)
        # Movie C (9000 ratings) should have largest width (500px)
        widths = [data[i]['rect'][2] for i in range(3)]
        assert widths[0] == pytest.approx(50.0, abs=1.0)   # Min scaled
        assert widths[2] == pytest.approx(500.0, abs=1.0)  # Max scaled
        
        db.disconnect()

    def test_build_from_datasource_empty_result(self):
        """Test that empty query result creates no elements."""
        db = SQLiteProvider(":memory:")
        db.connect()
        db._conn.execute("CREATE TABLE empty_table (id INTEGER PRIMARY KEY)")
        db._conn.commit()

        engine = AetherEngine()
        builder = UIBuilder()

        template = {
            'type': 'static_box',
            'columns': {
                'x': {'source': 'id'},
                'y': {'source': 'id'},
                'w': {'source': 'id'},
                'h': {'source': 'id'},
            },
        }

        count = builder.build_from_datasource(engine, db, "SELECT * FROM empty_table", template)
        
        assert count == 0
        assert engine.element_count == 0
        
        db.disconnect()
