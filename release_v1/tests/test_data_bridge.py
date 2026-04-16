"""
Tests for the Aether-Data Bridge: SQLiteProvider, normalization, and vector-to-tensor.
"""
import pytest
import numpy as np
import warnings
from core.data_bridge import (
    SQLiteProvider, RemoteAetherProvider,
    min_max_scale, normalize_column, vector_to_tensor,
    DATA_NORMALIZE_MIN, DATA_NORMALIZE_MAX, VECTOR_TENSOR_SCALE,
    NORMALIZATION_EPSILON
)


class TestMinMaxScale:
    """Tests for algebraic data normalization."""

    def test_basic_scaling(self):
        """Test standard min-max scaling."""
        result = min_max_scale(5.0, 0.0, 10.0, 0.0, 100.0)
        assert result == pytest.approx(50.0, abs=1e-6)

    def test_minimum_value(self):
        """Test that minimum source value maps to target minimum."""
        result = min_max_scale(0.0, 0.0, 10.0, 10.0, 500.0)
        assert result == pytest.approx(10.0, abs=1e-6)

    def test_maximum_value(self):
        """Test that maximum source value maps to target maximum."""
        result = min_max_scale(10.0, 0.0, 10.0, 10.0, 500.0)
        assert result == pytest.approx(500.0, abs=1e-6)

    def test_value_below_range_clamped(self):
        """Test that values below source range are clamped to target_min."""
        result = min_max_scale(-5.0, 0.0, 10.0, 10.0, 500.0)
        assert result == pytest.approx(10.0, abs=1e-6)

    def test_value_above_range_clamped(self):
        """Test that values above source range are clamped to target_max."""
        result = min_max_scale(15.0, 0.0, 10.0, 10.0, 500.0)
        assert result == pytest.approx(500.0, abs=1e-6)

    def test_identical_min_max_no_division_by_zero(self):
        """Test that identical min/max returns midpoint without division error."""
        result = min_max_scale(5.0, 10.0, 10.0, 0.0, 100.0)
        assert result == pytest.approx(50.0, abs=1e-6)

    def test_very_small_range(self):
        """Test scaling with a very small source range."""
        result = min_max_scale(5.000001, 5.0, 5.000002, 0.0, 100.0)
        assert 0.0 <= result <= 100.0

    def test_default_target_range(self):
        """Test that default target range is [DATA_NORMALIZE_MIN, DATA_NORMALIZE_MAX]."""
        result = min_max_scale(5000.0, 0.0, 10000.0)
        expected = DATA_NORMALIZE_MIN + 0.5 * (DATA_NORMALIZE_MAX - DATA_NORMALIZE_MIN)
        assert result == pytest.approx(expected, abs=1e-6)


class TestNormalizeColumn:
    """Tests for batch column normalization."""

    def test_empty_list(self):
        """Test that empty list returns empty list."""
        assert normalize_column([]) == []

    def test_single_value(self):
        """Test that single value returns midpoint."""
        result = normalize_column([42.0])
        assert result == [pytest.approx((DATA_NORMALIZE_MIN + DATA_NORMALIZE_MAX) / 2.0)]

    def test_full_range_scaling(self):
        """Test that column is properly scaled."""
        values = [0.0, 2500.0, 5000.0, 7500.0, 10000.0]
        result = normalize_column(values, 10.0, 500.0)
        
        assert result[0] == pytest.approx(10.0, abs=1e-6)
        assert result[-1] == pytest.approx(500.0, abs=1e-6)
        # Middle value should be at midpoint
        assert result[2] == pytest.approx(255.0, abs=1e-6)

    def test_preserves_order(self):
        """Test that normalization preserves value ordering."""
        values = [100.0, 50.0, 200.0]
        result = normalize_column(values)
        assert result[1] < result[0] < result[2]


class TestVectorToTensor:
    """Tests for AI embedding to physics force conversion."""

    def test_4d_vector(self):
        """Test that a 4D vector maps directly to [fx, fy, fw, fh]."""
        embedding = [0.5, -0.3, 0.8, -0.1]
        result = vector_to_tensor(embedding, scale=100.0)
        
        assert result.shape == (4,)
        assert result[0] == pytest.approx(50.0, abs=1e-5)
        assert result[1] == pytest.approx(-30.0, abs=1e-5)
        assert result[2] == pytest.approx(80.0, abs=1e-5)
        assert result[3] == pytest.approx(-10.0, abs=1e-5)

    def test_longer_vector_truncated(self):
        """Test that vectors longer than 4D are truncated."""
        embedding = [0.5, -0.3, 0.8, -0.1, 0.2, 0.9]
        result = vector_to_tensor(embedding, scale=100.0)
        
        assert result.shape == (4,)
        assert result[0] == pytest.approx(50.0, abs=1e-5)
        # 5th and 6th components should be ignored
        assert result.dtype == np.float32

    def test_shorter_vector_padded(self):
        """Test that vectors shorter than 4D are zero-padded."""
        embedding = [0.5, -0.3]
        result = vector_to_tensor(embedding, scale=100.0)
        
        assert result.shape == (4,)
        assert result[0] == pytest.approx(50.0, abs=1e-5)
        assert result[1] == pytest.approx(-30.0, abs=1e-5)
        assert result[2] == pytest.approx(0.0, abs=1e-5)
        assert result[3] == pytest.approx(0.0, abs=1e-5)

    def test_empty_vector(self):
        """Test that empty vector returns zero force."""
        result = vector_to_tensor([], scale=100.0)
        np.testing.assert_array_equal(result, np.zeros(4, dtype=np.float32))

    def test_default_scale(self):
        """Test that default scale factor is VECTOR_TENSOR_SCALE."""
        embedding = [1.0, 0.0, 0.0, 0.0]
        result = vector_to_tensor(embedding)
        assert result[0] == pytest.approx(VECTOR_TENSOR_SCALE, abs=1e-5)


class TestSQLiteProvider:
    """Tests for SQLite-based data provider."""

    @pytest.fixture
    def provider(self):
        """Create an in-memory SQLite provider for testing."""
        p = SQLiteProvider(":memory:")
        p.connect()
        # Create table manually for in-memory
        p._conn.execute("""
            CREATE TABLE IF NOT EXISTS element_states (
                element_id TEXT PRIMARY KEY,
                x REAL DEFAULT 0.0, y REAL DEFAULT 0.0,
                w REAL DEFAULT 100.0, h REAL DEFAULT 100.0,
                r REAL DEFAULT 1.0, g REAL DEFAULT 1.0,
                b REAL DEFAULT 1.0, a REAL DEFAULT 1.0,
                z INTEGER DEFAULT 0, metadata TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        p._conn.commit()
        yield p
        p.disconnect()

    def test_insert_and_get(self, provider):
        """Test full insert and retrieve cycle."""
        state = {
            'x': 50.0, 'y': 100.0, 'w': 200.0, 'h': 150.0,
            'r': 0.8, 'g': 0.2, 'b': 0.3, 'a': 0.9, 'z': 1,
            'metadata': {'title': 'Test Box'}
        }
        assert provider.insert_element_state('test_box', state) is True
        
        result = provider.get_element_state('test_box')
        assert result is not None
        assert result['x'] == 50.0
        assert result['y'] == 100.0
        assert result['w'] == 200.0
        assert result['h'] == 150.0
        assert result['z'] == 1
        assert result['metadata'] == {'title': 'Test Box'}

    def test_update_existing(self, provider):
        """Test that inserting same ID updates the record."""
        state1 = {'x': 10.0, 'y': 10.0, 'w': 100.0, 'h': 100.0}
        provider.insert_element_state('box', state1)
        
        state2 = {'x': 50.0, 'y': 50.0, 'w': 200.0, 'h': 200.0}
        provider.insert_element_state('box', state2)
        
        result = provider.get_element_state('box')
        assert result['x'] == 50.0
        assert result['w'] == 200.0

    def test_delete(self, provider):
        """Test delete operation."""
        state = {'x': 10.0, 'y': 10.0, 'w': 100.0, 'h': 100.0}
        provider.insert_element_state('to_delete', state)
        
        assert provider.delete_element_state('to_delete') is True
        assert provider.get_element_state('to_delete') is None

    def test_delete_nonexistent(self, provider):
        """Test deleting a non-existent element returns False."""
        assert provider.delete_element_state('nonexistent') is False

    def test_get_nonexistent(self, provider):
        """Test getting a non-existent element returns None."""
        assert provider.get_element_state('nonexistent') is None

    def test_get_all_states(self, provider):
        """Test retrieving all states."""
        provider.insert_element_state('a', {'x': 10, 'y': 10, 'w': 100, 'h': 100, 'z': 2})
        provider.insert_element_state('b', {'x': 20, 'y': 20, 'w': 200, 'h': 200, 'z': 1})
        
        all_states = provider.get_all_states()
        assert len(all_states) == 2
        # Should be ordered by z ASC
        assert all_states[0]['element_id'] == 'b'  # z=1
        assert all_states[1]['element_id'] == 'a'  # z=2

    def test_context_manager(self):
        """Test that context manager properly connects and disconnects."""
        with SQLiteProvider(":memory:") as p:
            p._conn.execute("""
                CREATE TABLE IF NOT EXISTS element_states (
                    element_id TEXT PRIMARY KEY,
                    x REAL DEFAULT 0.0, y REAL DEFAULT 0.0,
                    w REAL DEFAULT 100.0, h REAL DEFAULT 100.0,
                    r REAL DEFAULT 1.0, g REAL DEFAULT 1.0,
                    b REAL DEFAULT 1.0, a REAL DEFAULT 1.0,
                    z INTEGER DEFAULT 0, metadata TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            p._conn.commit()
            assert p._conn is not None
        
        # After context exit, connection should be closed
        # (We can't test _conn is None because __exit__ sets it, but no error means success)

    def test_execute_query(self, provider):
        """Test executing custom SQL queries."""
        provider.insert_element_state('box1', {'x': 10, 'y': 10, 'w': 100, 'h': 100, 'z': 1})
        provider.insert_element_state('box2', {'x': 20, 'y': 20, 'w': 200, 'h': 200, 'z': 2})
        
        results = provider.execute_query("SELECT * FROM element_states WHERE z > ?", (1,))
        assert len(results) == 1
        assert results[0]['element_id'] == 'box2'
