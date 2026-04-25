import pytest
import numpy as np
import time
from core.input_manager import InputManager
from core.pooling import ElementPool
from core.elements import StaticBox, SmartPanel

def test_input_manager_gestures():
    """Test multi-touch gestures: Pinch, Pan and Swipe."""
    im = InputManager()
    
    # 1. Test Pinch (Scaling)
    # Pointer 1 at (0, 0)
    im.pointer_down(0, 0, 0)
    # Pointer 2 at (100, 0) -> Initial distance = 100
    im.pointer_down(1, 100, 0)
    
    assert im._initial_pinch_dist == 100.0
    
    # Move Pointer 2 to (200, 0) -> New distance = 200 (Scale x2)
    im.pointer_move(1, 200, 0)
    assert im.current_scale == pytest.approx(2.0)
    
    # Move Pointer 2 to (50, 0) -> distance = 50 (Scale / 4 relative to previous)
    # Previous distance was 200. 50/200 = 0.25. 2.0 * 0.25 = 0.5
    im.pointer_move(1, 50, 0)
    assert im.current_scale == pytest.approx(0.5)
    
    # 2. Test Pan (Multi-finger)
    # Average movement: P1 moved 0, P2 moved -150 (from 200 to 50)
    # Pan offset += dx / len(pointers) = 100/2 + -150/2 = 50 - 75 = -25.
    assert im.pan_offset[0] == pytest.approx(-25.0)
    
    # 3. Test Swipe & Kinetic Scroll
    im.reset()
    # Rapid movement: (0,0) to (1000, 0) in 0.01s
    im.pointer_down(0, 0, 0, element_index=0)
    time.sleep(0.01)
    im.pointer_move(0, 10, 0) # Just to fill history
    time.sleep(0.01)
    im.pointer_move(0, 20, 0)
    
    # We simulate a fast movement via get_throw_velocity logic
    # In a real test we'd need to control time.perf_counter()
    # Let's verify Kinetic Scroll state
    im._kinetic_vel = np.array([1000.0, 0.0], dtype=np.float32)
    im._is_scrolling = True
    
    im.update_kinetic_scroll(0.1) # 1000 * 0.1 = 100px movement
    assert im.pan_offset[0] > 0
    assert np.all(im._kinetic_vel < 1000.0) # Friction applied

def test_element_pooling():
    """Test acquisition, release and reset of elements."""
    pool = ElementPool()
    
    # 1. Acquire
    box = pool.acquire(StaticBox, x=10, y=10, w=100, h=100, color=(1,0,0,1), z=1)
    assert isinstance(box, StaticBox)
    assert box.rect[0] == 10
    assert box.z_index == 1
    
    # 2. Release
    pool.release(box)
    assert box._disposed is True
    
    # 3. Re-acquire (Should reuse)
    box2 = pool.acquire(StaticBox, x=50, y=50, w=200, h=200, color=(0,1,0,1), z=10)
    assert box is box2
    assert box2.rect[0] == 50
    assert box2.z_index == 10
    assert box2._disposed is False
    
    # 4. Prewarm
    pool.prewarm(SmartPanel, 5)
    assert len(pool._pools[SmartPanel]) == 5
    
    panel = pool.acquire(SmartPanel, 0, 0, 100, 100)
    assert len(pool._pools[SmartPanel]) == 4
