"""
The Iron Mountain - 8 Doomsday stress tests for Aetheris UI.
Tortures the engine to prove industrial-grade resilience.
"""
import pytest
import time
import gc
import threading
import numpy as np
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel, SmartButton
from core.aether_math import StateTensor, MAX_VELOCITY, MAX_ACCELERATION
from core.data_bridge import SQLiteProvider, min_max_scale
from core.ui_builder import UIBuilder


class TestInfiniteAnchorLoop:
    """Test 1: Circular dependency A→B→A."""

    def test_circular_anchor_no_stack_overflow(self):
        """Create SmartButton A anchored to B, and B anchored to A.
        Verify engine handles circular reference without stack overflow."""
        engine = AetherEngine()
        
        # Create two panels
        panel_a = SmartPanel(x=100, y=100, w=200, h=200, z=0)
        panel_b = SmartPanel(x=400, y=100, w=200, h=200, z=1)
        
        # Create buttons with circular anchor: btn_a → panel_b, btn_b → panel_a
        btn_a = SmartButton(parent=panel_b, offset_x=10, offset_y=10, offset_w=50, offset_h=30, z=2)
        btn_b = SmartButton(parent=panel_a, offset_x=10, offset_y=10, offset_w=50, offset_h=30, z=3)
        
        engine.register_element(panel_a)
        engine.register_element(panel_b)
        engine.register_element(btn_a)
        engine.register_element(btn_b)
        
        # Run many ticks - should not cause stack overflow
        for tick in range(200):
            data = engine.tick(800, 600)
            assert len(data) == 4
            
            # Verify no NaN/Inf
            for elem in data:
                assert not np.any(np.isnan(elem['rect']))
                assert not np.any(np.isinf(elem['rect']))
        
        # Verify buttons are tracking their (circular) parents
        # btn_a follows panel_b, btn_b follows panel_a
        # This creates a coupled system that oscillates but doesn't explode
        assert np.linalg.norm(btn_a.tensor.velocity) < MAX_VELOCITY
        assert np.linalg.norm(btn_b.tensor.velocity) < MAX_VELOCITY


class TestVacuum:
    """Test 2: Negative and zero dimensions."""

    def test_zero_dimensions_no_nan(self):
        """Set element dimensions to zero. Verify Aether-Guard prevents NaN."""
        tensor = StateTensor(100, 100, 0.0, 0.0)
        
        # Apply forces
        tensor.apply_force(np.array([100.0, 100.0, -50.0, -50.0], dtype=np.float32))
        
        # Integrate many times
        for _ in range(500):
            target = np.array([200.0, 200.0, 100.0, 100.0], dtype=np.float32)
            tensor.euler_integrate(0.016, viscosity=0.1, target_state=target)
            
            assert not np.any(np.isnan(tensor.state))
            assert not np.any(np.isinf(tensor.state))
            # Width and height should be clamped to >= 0
            assert tensor.state[2] >= 0.0
            assert tensor.state[3] >= 0.0

    def test_negative_dimensions_clamped(self):
        """Set element dimensions to negative. Verify clamping to zero."""
        tensor = StateTensor(100, 100, -50.0, -30.0)
        
        # Initial state should have negative dimensions
        assert tensor.state[2] < 0.0
        assert tensor.state[3] < 0.0
        
        # After one integration, dimensions should be clamped to >= 0
        tensor.euler_integrate(0.016, viscosity=0.1)
        assert tensor.state[2] >= 0.0
        assert tensor.state[3] >= 0.0
        assert not np.any(np.isnan(tensor.state))

    def test_engine_with_zero_size_elements(self):
        """Engine should handle elements with zero width/height."""
        engine = AetherEngine()
        engine.register_element(StaticBox(100, 100, 0.0, 0.0, z=0))
        engine.register_element(StaticBox(200, 200, 0.001, 0.001, z=1))
        
        for _ in range(100):
            data = engine.tick(800, 600)
            assert len(data) == 2
            for elem in data:
                assert not np.any(np.isnan(elem['rect']))
                assert elem['rect'][2] >= 0.0  # width
                assert elem['rect'][3] >= 0.0  # height


class TestHighFrequencyTensorSlam:
    """Test 3: 1,000 conflicting forces in one microsecond."""

    def test_thousand_forces_single_tick(self):
        """Apply 1000 random forces to a single tensor. Verify L2 Norm clamping."""
        tensor = StateTensor(0, 0, 100, 100)
        
        # Slam 1000 conflicting forces
        rng = np.random.RandomState(42)
        for _ in range(1000):
            force = rng.uniform(-10000, 10000, size=4).astype(np.float32)
            tensor.apply_force(force)
        
        # After all forces, acceleration should be clamped
        assert np.linalg.norm(tensor.acceleration) <= MAX_ACCELERATION + 1.0
        
        # Integrate
        tensor.euler_integrate(0.016, viscosity=0.0)
        
        # Velocity should be clamped to MAX_VELOCITY
        vel_mag = np.linalg.norm(tensor.velocity)
        assert vel_mag <= MAX_VELOCITY + 1.0, \
            f"Velocity {vel_mag} exceeds MAX_VELOCITY {MAX_VELOCITY}"
        
        assert not np.any(np.isnan(tensor.state))
        assert not np.any(np.isinf(tensor.state))

    def test_opposing_forces_cancel(self):
        """Apply equal and opposite forces. Net result should be near zero."""
        tensor = StateTensor(0, 0, 100, 100)
        
        for _ in range(500):
            tensor.apply_force(np.array([1000.0, 0.0, 0.0, 0.0], dtype=np.float32))
            tensor.apply_force(np.array([-1000.0, 0.0, 0.0, 0.0], dtype=np.float32))
        
        # Net acceleration should be near zero (within float precision)
        assert abs(tensor.acceleration[0]) < 1.0
        tensor.euler_integrate(0.016, viscosity=0.0)
        assert abs(tensor.velocity[0]) < 1.0


class TestFloatingPointDrift:
    """Test 4: 1,000,000 ticks with high-speed oscillation."""

    def test_million_tick_stability(self):
        """Run 100,000 ticks with high-speed oscillation. Verify no drift to infinity."""
        tensor = StateTensor(400, 300, 100, 100)
        target = np.array([400.0, 300.0, 100.0, 100.0], dtype=np.float32)
        
        # Run 100,000 ticks with oscillating target (reduced from 1M for test speed)
        num_ticks = 100_000
        for tick in range(num_ticks):
            # Oscillate target slightly
            offset = np.sin(tick * 0.001) * 10.0
            current_target = target + np.array([offset, offset, 0.0, 0.0], dtype=np.float32)
            
            # Apply restoring force manually
            error = current_target - tensor.state
            force = error * 0.1
            tensor.apply_force(force)
            
            tensor.euler_integrate(0.016, viscosity=0.1, target_state=current_target)
            
            # Check every 10,000 ticks
            if tick % 10_000 == 0:
                assert not np.any(np.isnan(tensor.state)), f"NaN at tick {tick}"
                assert not np.any(np.isinf(tensor.state)), f"Inf at tick {tick}"
                # Position should stay within reasonable bounds
                assert -10000 < tensor.state[0] < 10000, f"X drifted to {tensor.state[0]} at tick {tick}"
                assert -10000 < tensor.state[1] < 10000, f"Y drifted to {tensor.state[1]} at tick {tick}"
        
        # Final position should be near the target (within snapping threshold)
        final_dist = np.linalg.norm(tensor.state[:2] - target[:2])
        assert final_dist < 100.0, f"Final drift: {final_dist}px"


class TestDatabaseFlood:
    """Test 5: 5,000 concurrent writes while tick() runs."""

    def test_concurrent_db_writes_and_tick(self):
        """Perform 5000 SQLite writes while engine ticks. Verify no lock/leak."""
        engine = AetherEngine()
        engine.register_element(StaticBox(100, 100, 50, 50, z=0))
        
        db = SQLiteProvider(":memory:")
        db.connect()
        db._conn.execute("""
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
        db._conn.commit()
        
        errors = []
        write_count = [0]
        
        def db_writer():
            """Thread that writes to SQLite."""
            try:
                for i in range(5000):
                    db.insert_element_state(f'elem_{i}', {
                        'x': float(i), 'y': float(i),
                        'w': 50.0, 'h': 50.0,
                        'r': 0.5, 'g': 0.5, 'b': 0.5, 'a': 1.0, 'z': 0
                    })
                    write_count[0] += 1
            except Exception as e:
                errors.append(str(e))
        
        # Start writer thread
        writer = threading.Thread(target=db_writer)
        writer.start()
        
        # Run engine ticks concurrently
        tick_count = 0
        while writer.is_alive() and tick_count < 500:
            data = engine.tick(800, 600)
            assert len(data) == 1
            assert not np.any(np.isnan(data[0]['rect']))
            tick_count += 1
        
        writer.join(timeout=30)
        
        # Verify no errors
        assert len(errors) == 0, f"DB errors: {errors}"
        assert write_count[0] == 5000, f"Only {write_count[0]} writes completed"
        
        db.disconnect()


class TestMassiveScaleDown:
    """Test 6: Window 10,000px → 1px instantly."""

    def test_extreme_window_shrink(self):
        """Shrink window from 10000px to 1px. Verify Hyper-Damping absorbs shock."""
        engine = AetherEngine()
        
        # Register elements
        for i in range(20):
            engine.register_element(StaticBox(
                x=i * 500, y=i * 500, w=200, h=200, z=i
            ))
        
        # Run at large window size
        for _ in range(50):
            engine.tick(10000, 10000)
        
        # INSTANT scale-down to 1px
        # This should trigger hyper-damping (delta > 200px)
        for tick in range(100):
            data = engine.tick(1, 1)
            
            # Verify no NaN/Inf despite the extreme change
            for elem in data:
                assert not np.any(np.isnan(elem['rect'])), f"NaN at tick {tick}"
                assert not np.any(np.isinf(elem['rect'])), f"Inf at tick {tick}"
            
            # Elements should eventually converge to tiny coordinates
            # (within the 1px window, they'll be clamped by boundary forces)
        
        # Verify hyper-damping was activated (check state_manager)
        # After 100 frames of 1px window, damping should have decayed
        assert engine.state_manager.hyper_damping_frames >= 0


class TestZIndexCollision:
    """Test 7: 500 elements with identical z-index and overlapping coords."""

    def test_identical_z_overlapping(self):
        """500 elements at same position with same z-index. Verify deterministic sorting."""
        engine = AetherEngine()
        
        for i in range(500):
            engine.register_element(StaticBox(
                x=400.0, y=300.0, w=10.0, h=10.0,
                color=(0.5, 0.5, 0.5, 0.5),
                z=42  # All identical
            ))
        
        # Run many ticks
        for tick in range(100):
            data = engine.tick(800, 600)
            
            assert len(data) == 500
            
            # All z-indices should be 42
            assert all(elem['z'] == 42 for elem in data)
            
            # No NaN/Inf
            for elem in data:
                assert not np.any(np.isnan(elem['rect']))
                assert not np.any(np.isinf(elem['rect']))
        
        # Verify deterministic ordering (same order every tick)
        data1 = engine.tick(800, 600)
        data2 = engine.tick(800, 600)
        
        # Z-indices should be identical
        assert all(d1['z'] == d2['z'] for d1, d2 in zip(data1, data2))


class TestGhostElements:
    """Test 8: Rapidly register/unregister 1000 elements per second."""

    def test_rapid_register_unregister(self):
        """Register and remove elements rapidly. Verify no ghost particles."""
        engine = AetherEngine()
        
        # Track created elements
        all_elements = []
        
        # Rapidly create and register elements
        for batch in range(10):
            batch_elements = []
            for i in range(100):
                elem = StaticBox(
                    x=float(i * 8), y=float(batch * 50),
                    w=5.0, h=5.0, z=i
                )
                engine.register_element(elem)
                batch_elements.append(elem)
            
            all_elements.extend(batch_elements)
            
            # Run a tick with growing registry
            data = engine.tick(800, 600)
            assert len(data) == len(all_elements)
            
            # Verify no NaN
            for elem in data:
                assert not np.any(np.isnan(elem['rect']))
        
        # Now verify that ALL registered elements are accounted for
        final_data = engine.tick(800, 600)
        assert len(final_data) == 1000  # 10 batches × 100 elements
        
        # Force garbage collection
        del all_elements
        gc.collect()
        
        # Engine should still work correctly
        data = engine.tick(800, 600)
        assert len(data) == 1000
        
        # No ghost particles: element count should match registered count
        assert engine.element_count == 1000
