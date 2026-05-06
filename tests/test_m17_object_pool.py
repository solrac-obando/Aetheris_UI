#!/usr/bin/env python3
"""
M17: Object Pool & Dynamic Limits Unit Tests

Tests the object pool mechanism and dynamic limits security in the Python backend.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AetherEngine
from core.elements import StaticBox
from core.dynamic_limits import get_optimal_max_elements


class TestM17ObjectPoolPython:
    """Test suite for M17 Object Pool in Python backend."""
    
    def setup_method(self):
        """Set up test engine."""
        self.engine = AetherEngine()
    
    def test_pool_initialization(self):
        """Verify pool structures are initialized correctly."""
        assert hasattr(self.engine, '_free_indices')
        assert hasattr(self.engine, '_element_active')
        assert self.engine._free_indices == []
        assert self.engine._element_active == []
        print("PASS: Pool initialized correctly")
    
    def test_element_registration_append(self):
        """Test that new elements are appended when pool is empty."""
        elem1 = StaticBox(0, 0, 100, 50, (1, 0, 0, 1), 0)
        self.engine.register_element(elem1)
        
        assert len(self.engine._elements) == 1
        assert len(self.engine._element_active) == 1
        assert self.engine._element_active[0] is True
        assert self.engine._free_indices == []
        print("PASS: Element appended correctly")
    
    def test_element_disposal_goes_to_pool(self):
        """Test that removed elements have indices go to _free_indices."""
        elem1 = StaticBox(0, 0, 100, 50, (1, 0, 0, 1), 0)
        self.engine.register_element(elem1)
        
        # Remove the element
        self.engine.remove_element(elem1)
        
        # Verify removed element is tracked as inactive and index in pool
        assert len(self.engine._free_indices) >= 1
        assert self.engine._element_active[0] == False
        assert len(self.engine._elements) == 1  # NOT removed, just inactive
        print("PASS: Removed element index added to _free_indices")
    
    def test_element_registration_reuses_pool(self):
        """Test that registration reuses pooled indices."""
        elem1 = StaticBox(0, 0, 100, 50, (1, 0, 0, 1), 0)
        elem2 = StaticBox(10, 10, 100, 50, (0, 1, 0, 1), 1)
        
        # Register first element
        self.engine.register_element(elem1)
        
        # Remove first element (goes to pool)
        self.engine.remove_element(elem1)
        
        # Register second element (should reuse index 0)
        self.engine.register_element(elem2)
        
        assert self.engine._free_indices == []  # Pool is now empty (reused)
        assert self.engine._element_active[0] == True  # Reused slot
        # Note: elem2 is at index 0, replacing elem1
        print("PASS: Element reused pooled index correctly")
    
    def test_multiple_elements_pool_behavior(self):
        """Test pool with multiple add/remove cycles."""
        elements = []
        
        # Create and register 5 elements
        for i in range(5):
            elem = StaticBox(i * 10, i * 10, 50, 50, (1, 0, 0, 1), i)
            self.engine.register_element(elem)
            elements.append(elem)
        
        assert len(self.engine._elements) == 5
        assert self.engine._free_indices == []
        
        # Remove first 3
        for i in range(3):
            self.engine.remove_element(elements[i])
        
        assert len(self.engine._free_indices) == 3
        # Note: element_active has values as [False, False, False, True, True]
        active_list = self.engine._element_active
        assert active_list[0] == False and active_list[1] == False and active_list[2] == False
        assert active_list[3] == True and active_list[4] == True
        
        # Add 3 more (should reuse pooled indices)
        for i in range(3):
            elem = StaticBox(100 + i * 10, 100, 50, 50, (0, 1, 0, 1), i + 10)
            self.engine.register_element(elem)
        
        assert len(self.engine._elements) == 5  # Still 5, no expansion
        assert self.engine._free_indices == []  # All reused
        print("PASS: Multiple add/remove cycles work correctly")
    
    def test_gc_triggers_on_threshold(self):
        """Test that GC triggers when threshold exceeded."""
        # Set low threshold for testing
        self.engine._pool_gc_threshold = 0.3
        self.engine._gc_frames_required = 5
        self.engine._pool_gc_cooldown_frames = 0  # Ready to GC
        
        # Add 10 elements, remove 8
        elements = []
        for i in range(10):
            elem = StaticBox(i * 10, i * 10, 50, 50, (1, 0, 0, 1), i)
            self.engine.register_element(elem)
            elements.append(elem)
        
        # Remove 8 (80% inactive, above 30% threshold)
        for i in range(8):
            self.engine.remove_element(elements[i])
        
        # Initial state
        initial_free = len(self.engine._free_indices)
        
        # Trigger GC
        self.engine._collect_garbage()
        
        # GC should have compacted - now only 2 elements
        assert len(self.engine._elements) == 2
        assert len(self.engine._free_indices) == 0  # Freed indices cleared after compaction
        print("PASS: GC triggers and compacts correctly")
    
    def test_limit_enforcement(self):
        """Test that max element limit is enforced."""
        from core import engine as eng_module
        
        # Get limit
        limit = eng_module._MAX_ELEMENTS
        
        # Temporarily clear pool
        self.engine._free_indices.clear()
        self.engine._element_active.clear()
        
        # Fill to limit
        original_len = len(self.engine._elements)
        
        # Enable limit enforcement
        eng_module._ELEMENT_LIMIT_ENABLED = True
        
        # Try to add more than limit
        try:
            for i in range(limit + 1):
                elem = StaticBox(i, i, 10, 10, (1, 0, 0, 1), i)
                self.engine.register_element(elem)
            # Should not reach here
            assert False, "Should have raised exception"
        except RuntimeError as e:
            assert "Maximum element limit" in str(e)
            print(f"PASS: Limit enforced correctly - raised: {e}")
        finally:
            eng_module._ELEMENT_LIMIT_ENABLED = False
    
    def test_dynamic_limits_calculation(self):
        """Test dynamic limits calculation."""
        from core.dynamic_limits import SAFETY_MARGIN
        
        # Verify safety margin exists
        assert SAFETY_MARGIN == 0.35
        
        # Get profile
        from core.dynamic_limits import get_system_profile
        profile = get_system_profile()
        
        assert 'engine_limit' in profile
        assert 'bridge_limit' in profile
        assert profile['engine_limit'] > 0
        print(f"PASS: Dynamic limits calculated - engine_limit={profile['engine_limit']}")


def run_tests():
    """Run all M17 tests."""
    print("=" * 60)
    print("M17: Object Pool & Dynamic Limits - Python Unit Tests")
    print("=" * 60)
    
    test_suite = TestM17ObjectPoolPython()
    test_suite.setup_method()
    
    tests = [
        ('Pool Initialization', test_suite.test_pool_initialization),
        ('Element Registration Append', test_suite.test_element_registration_append),
        ('Element Disposal to Pool', test_suite.test_element_disposal_goes_to_pool),
        ('Element Reuse from Pool', test_suite.test_element_registration_reuses_pool),
        ('Multiple Elements Pool', test_suite.test_multiple_elements_pool_behavior),
        ('GC Threshold Trigger', test_suite.test_gc_triggers_on_threshold),
        ('Limit Enforcement', test_suite.test_limit_enforcement),
        ('Dynamic Limits Calculation', test_suite.test_dynamic_limits_calculation),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"FAIL: {name} - {e}")
            failed += 1
    
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)