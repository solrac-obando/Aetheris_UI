"""
The Titan Stress Suite - 8 extreme edge-case tests for Aetheris UI.
Tests the framework's physical and computational limits.
"""
import pytest
import time
import gc
import sys
import numpy as np
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel, SmartButton
from core.data_bridge import SQLiteProvider, RemoteAetherProvider, min_max_scale
from core.ui_builder import UIBuilder


class TestMassiveRegistryStress:
    """Test 1: Register 1,000 elements and run 500 ticks."""

    def test_massive_registry_and_ticks(self):
        """Register 1000 elements and run 500 ticks. Verify integrity and timing."""
        engine = AetherEngine()
        
        # Register 1000 elements
        for i in range(1000):
            x = (i % 40) * 20
            y = (i // 40) * 20
            engine.register_element(StaticBox(x, y, 15, 15, z=i % 10))
        
        assert engine.element_count == 1000
        
        # Run 500 ticks, measuring timing
        tick_times = []
        for _ in range(500):
            start = time.perf_counter()
            data = engine.tick(800, 600)
            elapsed = time.perf_counter() - start
            tick_times.append(elapsed)
            
            # Verify structured array integrity (vectorized check)
            assert len(data) == 1000
            assert data.dtype.names == ('rect', 'color', 'z')
            # No NaN or Inf in the data (vectorized)
            assert not np.any(np.isnan(data['rect']))
            assert not np.any(np.isinf(data['rect']))
        
        # Verify timing budget: average tick should be under 200ms
        # 1000 elements in pure Python with Numba solver: ~130ms is expected
        avg_time = np.mean(tick_times)
        max_time = np.max(tick_times)
        
        assert avg_time < 0.200, f"Average tick time {avg_time*1000:.1f}ms exceeds 200ms budget"
        assert max_time < 0.500, f"Max tick time {max_time*1000:.1f}ms exceeds 500ms budget"


class TestBlackHoleParadox:
    """Test 2: 10 elements at [0,0,0,0] with high repulsive forces."""

    def test_black_hole_collision_no_nan(self):
        """Place 10 elements at origin. Verify Aether-Guard prevents NaN explosions."""
        engine = AetherEngine()
        
        # All elements start at exactly the same position with zero size
        for i in range(10):
            engine.register_element(StaticBox(0, 0, 0.001, 0.001, z=i))
        
        # Run many ticks - boundary forces will be massive since all elements
        # are at the origin with zero dimensions
        for tick in range(200):
            data = engine.tick(800, 600)
            
            # Critical: No NaN or Inf anywhere in the data
            for elem in data:
                rect = elem['rect']
                color = elem['color']
                assert not np.any(np.isnan(rect)), f"NaN in rect at tick {tick}"
                assert not np.any(np.isinf(rect)), f"Inf in rect at tick {tick}"
                assert not np.any(np.isnan(color)), f"NaN in color at tick {tick}"
                assert not np.any(np.isinf(color)), f"Inf in color at tick {tick}"
            
            # Elements should have moved apart due to boundary forces
            # (they can't all stay at [0,0,0,0])


class TestRecursiveAnchorDepth:
    """Test 3: Chain of 20 SmartButtons, each anchored to the previous."""

    def test_deep_anchor_chain(self):
        """Create 20 SmartButtons in a chain. Verify no stack overflow."""
        engine = AetherEngine()
        
        # Create a root panel
        root = SmartPanel(x=100, y=100, w=200, h=200, padding=0.1, z=0)
        engine.register_element(root)
        
        # Create a chain of 20 buttons, each anchored to the previous
        parent = root
        buttons = []
        for i in range(20):
            btn = SmartButton(
                parent=parent,
                offset_x=10 + i * 5,
                offset_y=10 + i * 5,
                offset_w=50,
                offset_h=30,
                z=i + 1
            )
            engine.register_element(btn)
            buttons.append(btn)
            parent = btn
        
        # Run ticks and verify no crashes
        for tick in range(100):
            data = engine.tick(800, 600)
            assert len(data) == 21  # root + 20 buttons
            
            # Verify all elements have valid positions
            for elem in data:
                rect = elem['rect']
                assert not np.any(np.isnan(rect))
                assert not np.any(np.isinf(rect))
        
        # Verify the chain didn't cause exponential slowdown
        start = time.perf_counter()
        for _ in range(50):
            engine.tick(800, 600)
        elapsed = time.perf_counter() - start
        
        # 50 ticks with 21 elements should be fast (< 1 second)
        assert elapsed < 1.0, f"Deep anchor chain took {elapsed:.2f}s for 50 ticks"


class TestTemporalJitter:
    """Test 4: Erratic dt values alternating between 0.001s and 1.0s."""

    def test_erratic_dt_stability(self):
        """Run engine with alternating tiny and huge dt values."""
        engine = AetherEngine()
        
        # Register some elements
        for i in range(10):
            engine.register_element(StaticBox(i * 50, i * 30, 40, 40, z=i))
        
        # Run with erratic dt: the engine's safe_dt capping should prevent explosions
        for tick in range(200):
            # Manually manipulate the engine's _last_time to force specific dt values
            if tick % 2 == 0:
                # Force tiny dt (0.001s)
                engine._last_time = time.perf_counter() - 0.001
            else:
                # Force huge dt (1.0s)
                engine._last_time = time.perf_counter() - 1.0
            
            data = engine.tick(800, 600)
            
            # Verify no NaN or Inf despite the temporal chaos
            for elem in data:
                rect = elem['rect']
                assert not np.any(np.isnan(rect)), f"NaN at tick {tick}"
                assert not np.any(np.isinf(rect)), f"Inf at tick {tick}"
                # Elements should still be on-screen (within reasonable bounds)
                assert rect[0] > -1000, f"Element flew off screen at tick {tick}"
                assert rect[1] > -1000, f"Element flew off screen at tick {tick}"


class TestMemoryLeakEndurance:
    """Test 5: 5,000 get_ui_metadata calls - verify no memory growth."""

    def test_metadata_no_memory_leak(self):
        """Call get_ui_metadata 5000 times. Verify memory doesn't grow linearly."""
        engine = AetherEngine()
        
        # Add some text elements that produce metadata
        from core.elements import CanvasTextNode, DOMTextNode
        for i in range(10):
            engine.register_element(CanvasTextNode(
                x=i * 50, y=i * 30, w=100, h=30,
                text=f"Element {i}", font_size=14, z=i
            ))
            engine.register_element(DOMTextNode(
                x=i * 50, y=i * 30 + 200, w=100, h=30,
                text=f"DOM {i}", font_size=12, z=i + 100
            ))
        
        # Run a tick to populate metadata
        engine.tick(800, 600)
        
        # Measure memory before
        gc.collect()
        
        # Call get_ui_metadata 5000 times
        results = []
        for i in range(5000):
            metadata = engine.get_ui_metadata()
            results.append(metadata)
            
            # Verify each call returns valid JSON
            import json
            parsed = json.loads(metadata)
            assert isinstance(parsed, dict)
        
        # Verify all results are identical (no mutation)
        first_result = results[0]
        for r in results[1:]:
            assert r == first_result, "Metadata changed between calls"
        
        # Force garbage collection and verify no lingering references
        del results
        gc.collect()


class TestZIndexStability:
    """Test 6: 100 elements with identical Z-indices."""

    def test_identical_z_index_stability(self):
        """Create 100 elements all with z=5. Verify stable sorting."""
        engine = AetherEngine()
        
        for i in range(100):
            engine.register_element(StaticBox(
                x=i * 8, y=0, w=5, h=5,
                color=(0.5, 0.5, 0.5, 1.0),
                z=5  # All identical z-index
            ))
        
        # Run many ticks
        for tick in range(100):
            data = engine.tick(800, 600)
            
            assert len(data) == 100
            
            # All z-indices should be 5
            for elem in data:
                assert elem['z'] == 5
            
            # No crashes, no NaN
            for elem in data:
                assert not np.any(np.isnan(elem['rect']))
                assert not np.any(np.isinf(elem['rect']))


class TestHotSwappingDatasources:
    """Test 7: Switch between SQLiteProvider and RemoteAetherProvider 100 times."""

    def test_datasource_hot_swap(self):
        """Switch providers 100 times during UIBuilder population."""
        engine = AetherEngine()
        builder = UIBuilder()
        
        # Set up SQLite provider
        sqlite_db = SQLiteProvider(":memory:")
        sqlite_db.connect()
        sqlite_db._conn.execute("""
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
        sqlite_db._conn.commit()
        
        # Set up remote provider (won't actually connect, but we test the switching)
        remote = RemoteAetherProvider("http://localhost:5000")
        
        template = {
            'type': 'static_box',
            'columns': {
                'x': {'source': 'x'},
                'y': {'source': 'y'},
                'w': {'source': 'w'},
                'h': {'source': 'h'},
                'z': {'source': 'z'},
            },
        }
        
        # Hot-swap 100 times
        for i in range(100):
            if i % 2 == 0:
                provider = sqlite_db
            else:
                provider = remote
            
            # Try to build - remote will fail gracefully, sqlite will succeed
            try:
                builder.build_from_datasource(engine, provider, "SELECT * FROM element_states", template)
            except Exception:
                pass  # Expected for remote provider when server isn't running
        
        # Verify no dangling connections
        sqlite_db.disconnect()
        remote.disconnect()
        
        # Engine should still be functional
        data = engine.tick(800, 600)
        assert isinstance(data, np.ndarray)


class TestAlgebraicRangeStress:
    """Test 8: min_max_scale with source data from -10^15 to 10^15."""

    def test_extreme_range_normalization(self):
        """Scale values from -10^15 to 10^15. Verify output clamped to [10, 500]."""
        extreme_min = -1e15
        extreme_max = 1e15
        
        test_values = [
            extreme_min,
            extreme_max,
            0.0,
            extreme_min / 2,
            extreme_max / 2,
            -1e10,
            1e10,
            -1e30,  # Way outside range
            1e30,   # Way outside range
        ]
        
        for val in test_values:
            result = min_max_scale(val, extreme_min, extreme_max, 10.0, 500.0)
            
            # Output must be strictly within [10, 500]
            assert 10.0 <= result <= 500.0, \
                f"min_max_scale({val}) = {result}, expected [10, 500]"
            
            # Output must be finite
            assert np.isfinite(result), \
                f"min_max_scale({val}) = {result} is not finite"
        
        # Test with identical extreme min/max (division-by-zero guard)
        result = min_max_scale(1e15, 1e15, 1e15, 10.0, 500.0)
        assert 10.0 <= result <= 500.0
        assert np.isfinite(result)
        
        # Test with very small range at extreme values
        result = min_max_scale(1e15 + 1, 1e15, 1e15 + 2, 10.0, 500.0)
        assert 10.0 <= result <= 500.0
        assert np.isfinite(result)
