#!/usr/bin/env python3
"""
M17: Object Pool & Dynamic Limits Unit Tests - Simplified
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AetherEngine
from core.elements import StaticBox


def test_pool_init():
    """Test pool initialization."""
    engine = AetherEngine()
    assert hasattr(engine, '_free_indices')
    assert hasattr(engine, '_element_active')
    print("PASS: pool_init")


def test_element_append():
    """Test element appended correctly."""
    engine = AetherEngine()
    elem = StaticBox(0, 0, 100, 50, (1, 0, 0, 1), 0)
    engine.register_element(elem)
    assert len(engine._elements) == 1
    print("PASS: element_append")


def test_element_disposal():
    """Test element disposal goes to pool."""
    engine = AetherEngine()
    elem = StaticBox(0, 0, 100, 50, (1, 0, 0, 1), 0)
    engine.register_element(elem)
    engine.remove_element(elem)
    assert len(engine._free_indices) >= 1
    assert engine._element_active[0] == False
    print("PASS: element_disposal")


def test_element_reuse():
    """Test element reuse from pool."""
    engine = AetherEngine()
    elem1 = StaticBox(0, 0, 100, 50, (1, 0, 0, 1), 0)
    elem2 = StaticBox(10, 10, 100, 50, (0, 1, 0, 1), 1)
    engine.register_element(elem1)
    engine.remove_element(elem1)
    engine.register_element(elem2)
    assert len(engine._free_indices) == 0
    print("PASS: element_reuse")


def test_multiple_cycles():
    """Test multiple add/remove cycles."""
    engine = AetherEngine()
    elements = []
    for i in range(5):
        elem = StaticBox(i * 10, i * 10, 50, 50, (1, 0, 0, 1), i)
        engine.register_element(elem)
        elements.append(elem)
    for i in range(3):
        engine.remove_element(elements[i])
    assert len(engine._free_indices) == 3
    for i in range(3):
        elem = StaticBox(100 + i * 10, 100, 50, 50, (0, 1, 0, 1), i + 10)
        engine.register_element(elem)
    assert len(engine._elements) == 5
    print("PASS: multiple_cycles")


def test_gc():
    """Test GC compacts correctly."""
    engine = AetherEngine()
    engine._pool_gc_threshold = 0.3
    engine._gc_frames_required = 5
    engine._pool_gc_cooldown_frames = 0
    
    elements = []
    for i in range(10):
        elem = StaticBox(i * 10, i * 10, 50, 50, (1, 0, 0, 1), i)
        engine.register_element(elem)
        elements.append(elem)
    
    for i in range(8):
        engine.remove_element(elements[i])
    
    engine._collect_garbage()
    assert len(engine._elements) == 2
    assert len(engine._free_indices) == 0
    print("PASS: gc")


def test_limit():
    """Test limit enforcement."""
    from core import engine as eng_module
    engine = AetherEngine()
    engine._free_indices.clear()
    engine._element_active.clear()
    
    eng_module._ELEMENT_LIMIT_ENABLED = True
    
    limit = eng_module._MAX_ELEMENTS
    try:
        for i in range(limit + 1):
            elem = StaticBox(i, i, 10, 10, (1, 0, 0, 1), i)
            engine.register_element(elem)
        print("FAIL: limit - should have raised")
    except RuntimeError as e:
        if "Maximum element limit" in str(e):
            print("PASS: limit")
        else:
            print(f"FAIL: limit - wrong error: {e}")
    finally:
        eng_module._ELEMENT_LIMIT_ENABLED = False


def test_dynamic_limits():
    """Test dynamic limits calculation."""
    from core.dynamic_limits import get_system_profile
    profile = get_system_profile()
    assert profile['engine_limit'] > 0
    print(f"PASS: dynamic_limits (limit={profile['engine_limit']})")


if __name__ == '__main__':
    print("=" * 50)
    print("M17 Unit Tests")
    print("=" * 50)
    
    tests = [
        test_pool_init,
        test_element_append,
        test_element_disposal,
        test_element_reuse,
        test_multiple_cycles,
        test_gc,
        test_limit,
        test_dynamic_limits,
    ]
    
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__} - {e}")
    
    print("=" * 50)
    print(f"RESULTS: {passed}/{len(tests)} passed")
    print("=" * 50)