"""
Test for teleportation shock detection and hyper-damping in StateManager.
"""
import numpy as np
from core.state_manager import StateManager


def test_state_manager_initialization():
    """Test that StateManager initializes correctly."""
    sm = StateManager()
    assert sm.last_width == 0
    assert sm.last_height == 0
    assert sm.hyper_damping_frames == 0


def test_first_frame_no_shock():
    """Test that first frame returns no shock multiplier."""
    sm = StateManager()
    multiplier = sm.check_teleportation_shock(800, 600)
    assert multiplier == 1.0
    assert sm.last_width == 800
    assert sm.last_height == 600


def test_small_change_no_shock():
    """Test that small window changes don't trigger shock."""
    sm = StateManager()
    # Initialize
    sm.check_teleportation_shock(800, 600)
    # Small change
    multiplier = sm.check_teleportation_shock(850, 600)
    assert multiplier == 1.0
    assert sm.last_width == 850
    assert sm.hyper_damping_frames == 0


def test_large_change_triggers_shock():
    """Test that large window changes trigger hyper-damping."""
    sm = StateManager()
    # Initialize
    sm.check_teleportation_shock(800, 600)
    # Large change (>200px)
    multiplier = sm.check_teleportation_shock(1200, 600)
    assert multiplier == 5.0
    assert sm.last_width == 1200
    # After triggering shock, we've already decremented the counter
    assert sm.hyper_damping_frames == 14  # Started at 15, decremented once


def test_shock_decays_over_frames():
    """Test that hyper-damping effect decays over frames."""
    sm = StateManager()
    # Initialize
    sm.check_teleportation_shock(800, 600)
    # Trigger shock
    multiplier = sm.check_teleportation_shock(1200, 600)
    assert multiplier == 5.0
    # Counter is now 14
    
    # Next frames should decay
    for i in range(14):
        multiplier = sm.check_teleportation_shock(1200, 600)
        expected_frames_left = 13 - i  # Starting from 14, after this call it will be 13-i
        assert sm.hyper_damping_frames == expected_frames_left
        assert multiplier == 5.0
    
    # After 15 total frames (1 initial + 14 more), should return to normal
    multiplier = sm.check_teleportation_shock(1200, 600)
    assert sm.hyper_damping_frames == 0
    assert multiplier == 1.0


def test_no_negative_frames():
    """Test that hyper_damping_frames doesn't go negative."""
    sm = StateManager()
    # Initialize
    sm.check_teleportation_shock(800, 600)
    # Trigger shock
    sm.check_teleportation_shock(1200, 600)
    
    # Call many times to ensure no negative values
    for _ in range(100):
        multiplier = sm.check_teleportation_shock(1200, 600)
        assert multiplier >= 1.0
        assert sm.hyper_damping_frames >= 0


def test_width_specific_detection():
    """Test that only width changes trigger shock (as per spec)."""
    sm = StateManager()
    # Initialize
    sm.check_teleportation_shock(800, 600)
    # Large height change but small width change
    multiplier = sm.check_teleportation_shock(850, 1200)  # width +50, height +600
    assert multiplier == 1.0  # Should not trigger since width change < 200
    
    # Large width change
    multiplier = sm.check_teleportation_shock(1100, 1200)  # width +300
    assert multiplier == 5.0  # Should trigger