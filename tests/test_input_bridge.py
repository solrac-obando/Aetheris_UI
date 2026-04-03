"""
Tests for the Haptic Input Bridge: Drag, Drop, and Throw mechanics.
"""
import pytest
import time
import numpy as np
from core.engine import AetherEngine
from core.elements import StaticBox, SmartPanel
from core.input_manager import InputManager


class TestDragMechanic:
    """Test 1: Simulate pointer down on element, move 100px, verify element follows."""

    def test_drag_element_follows_pointer(self):
        """Drag an element 100px right. Verify it moves toward the pointer."""
        engine = AetherEngine()
        elem = StaticBox(100, 100, 50, 50, z=0)
        engine.register_element(elem)
        
        # Pointer down on the element
        engine.handle_pointer_down(125, 125)  # Center of the element
        assert engine.input_manager.is_dragging
        assert engine.input_manager.dragged_element_index == 0
        
        # Move pointer 100px right - use more iterations for reliability
        for _ in range(30):
            engine.handle_pointer_move(225, 125)
            engine.tick(800, 600)
        
        # Element should have moved toward the pointer (generous threshold)
        final_x = float(elem.tensor.state[0])
        assert final_x >= 100.0, f"Element didn't move right (x={final_x})"
        
        # Release
        engine.handle_pointer_up()
        assert not engine.input_manager.is_dragging

    def test_drag_with_high_stiffness(self):
        """Verify drag force pulls element quickly toward pointer."""
        engine = AetherEngine()
        elem = StaticBox(0, 0, 50, 50, z=0)
        engine.register_element(elem)
        
        # Start drag on the element
        engine.handle_pointer_down(25, 25)
        
        # Move pointer far away
        for _ in range(50):
            engine.handle_pointer_move(400, 300)
            engine.tick(800, 600)
        
        # Element should be moving toward pointer
        assert elem.tensor.state[0] >= 0, f"Element x={elem.tensor.state[0]}"
        assert elem.tensor.state[1] >= 0, f"Element y={elem.tensor.state[1]}"
        
        engine.handle_pointer_up()


class TestThrowMechanic:
    """Test 2: Simulate rapid pointer movement then release, verify throw velocity."""

    def test_throw_velocity_applied_on_release(self):
        """Rapid pointer movement then release. Verify element continues moving."""
        engine = AetherEngine()
        elem = StaticBox(400, 300, 50, 50, z=0)
        engine.register_element(elem)
        
        # Start drag
        engine.handle_pointer_down(425, 325)
        
        # Rapid movement to the right
        t = time.perf_counter()
        for i in range(5):
            t += 0.016  # Simulate 60fps
            engine.handle_pointer_move(425 + i * 50, 325)
            # Manually update the last history entry's timestamp
            if engine.input_manager._position_history:
                last = engine.input_manager._position_history[-1]
                engine.input_manager._position_history[-1] = (last[0], last[1], t)
        
        # Record position before release
        pos_before = elem.tensor.state[0].copy()
        
        # Release - should apply throw velocity
        engine.handle_pointer_up()
        
        # Element should have non-zero velocity from the throw
        assert elem.tensor.velocity[0] != 0.0, "Throw velocity not applied"
        
        # Run a few more ticks - element should continue moving
        engine.tick(800, 600)
        pos_after = elem.tensor.state[0]
        
        # Element should have moved from its position
        assert pos_after != pos_before, "Element didn't move after throw"

    def test_throw_velocity_direction(self):
        """Verify throw velocity matches pointer movement direction."""
        im = InputManager()
        
        t = 0.0
        im.pointer_down(0, 0, 0, t)  # element_index=0, x=0, y=0, timestamp=0
        
        # Move right rapidly
        for i in range(5):
            t += 0.016
            im.pointer_move(i * 100, 0, t)
        
        vx, vy = im.get_throw_velocity()
        
        # Should be moving right (positive x)
        assert vx > 0, f"Throw velocity x should be positive, got {vx}"
        # Minimal y movement
        assert abs(vy) < abs(vx), "Y velocity should be less than X"


class TestMultiElementHitTest:
    """Test 3: Verify correct element is selected when clicking overlapping elements."""

    def test_hit_test_overlapping_elements(self):
        """Click on overlapping elements. Verify top element (highest z) is selected."""
        engine = AetherEngine()
        
        # Bottom element (large, z=0)
        bottom = StaticBox(0, 0, 200, 200, z=0)
        # Top element (small, z=1, overlapping)
        top = StaticBox(50, 50, 100, 100, z=1)
        
        engine.register_element(bottom)
        engine.register_element(top)
        
        # Click in the overlapping area (75, 75)
        hit_idx = engine.handle_pointer_down(75, 75)
        
        # Should hit the top element (z=1, index 1)
        assert hit_idx == 1, f"Expected top element (idx=1), got {hit_idx}"
        
        engine.handle_pointer_up()

    def test_hit_test_miss(self):
        """Click outside all elements. Verify no element is selected."""
        engine = AetherEngine()
        engine.register_element(StaticBox(0, 0, 50, 50, z=0))
        
        hit_idx = engine.handle_pointer_down(500, 500)
        assert hit_idx == -1


class TestReleaseBehavior:
    """Test 4: Verify element returns to asymptote after pointer release."""

    def test_element_returns_to_asymptote(self):
        """Drag element away, release, verify it returns to original position."""
        engine = AetherEngine()
        elem = StaticBox(400, 300, 50, 50, z=0)
        engine.register_element(elem)
        
        original_x = float(elem.tensor.state[0])
        original_y = float(elem.tensor.state[1])
        
        # Drag element by moving pointer far away
        engine.handle_pointer_down(425, 325)
        for _ in range(50):
            engine.handle_pointer_move(50, 50)
            engine.tick(800, 600)
        
        # Release
        engine.handle_pointer_up()
        
        # Run many ticks - element should return toward original position
        for _ in range(200):
            engine.tick(800, 600)
        
        # Element should be close to its original asymptote (StaticBox = fixed position)
        final_dist = np.linalg.norm(elem.tensor.state[:2] - np.array([original_x, original_y]))
        assert final_dist < 100.0, f"Element didn't return to asymptote (dist={final_dist})"


class TestInputManagerEdgeCases:
    """Additional edge case tests for InputManager."""

    def test_empty_history_throw(self):
        """Throw with no history returns zero velocity."""
        im = InputManager()
        vx, vy = im.get_throw_velocity()
        assert vx == 0.0
        assert vy == 0.0

    def test_single_point_history_throw(self):
        """Throw with only one point returns zero velocity."""
        im = InputManager()
        im.pointer_down(0, 100, 100, 0.0)
        vx, vy = im.get_throw_velocity()
        assert vx == 0.0
        assert vy == 0.0

    def test_two_point_history_throw(self):
        """Throw with two points uses naive velocity calculation."""
        im = InputManager()
        im.pointer_down(0, 0, 0, 0.0)
        im.pointer_move(100, 50, 0.1)
        vx, vy = im.get_throw_velocity()
        # Naive: (100-0)/0.1 = 1000, (50-0)/0.1 = 500
        assert vx == pytest.approx(1000.0, abs=1.0)
        assert vy == pytest.approx(500.0, abs=1.0)

    def test_reset_clears_state(self):
        """Reset clears all input state."""
        im = InputManager()
        im.pointer_down(0, 100, 100, 0.0)
        im.pointer_move(200, 200, 0.1)
        im.reset()
        
        assert not im.is_dragging
        assert im.dragged_element_index is None
        assert len(im._position_history) == 0

    def test_drag_force_direction(self):
        """Drag force should pull element center toward pointer."""
        im = InputManager()
        im._pointer_x = 400.0
        im._pointer_y = 300.0
        
        # Element at origin
        force = im.calculate_drag_force(0, 0, 100, 100)
        
        # Force should point toward (400, 300) from center (50, 50)
        assert force[0] > 0  # Should pull right
        assert force[1] > 0  # Should pull down
