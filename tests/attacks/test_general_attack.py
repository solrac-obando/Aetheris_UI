# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Public Reference Attack Test: test_general_attack.py

This is the ONLY attack test publicly available as a reference.
It demonstrates basic resilience testing patterns without exposing
private internal security research.

Note: The main codebase already handles these attacks natively:
- NaN/Inf values are converted to null for web safety
- Input bounds checking in the math engine
- Element count limits via configuration
"""
import pytest
import math
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.json_utils import to_json
from core.aether_math import check_and_fix_nan


class TestPublicAttackReference:
    """Public reference tests - demonstrates framework resilience."""

    def test_nan_injection_web_safe(self):
        """Test that NaN values are handled safely for web output."""
        malicious_data = {
            "x": float('nan'),
            "y": float('inf'),
            "values": [1.0, float('nan'), float('-inf'), 3.0]
        }
        
        # Framework converts to null for web safety
        result = to_json(malicious_data)
        
        assert '"x": null' in result
        assert '"y": null' in result
        assert 'NaN' not in result
        assert 'Infinity' not in result

    def test_math_engine_nan_handling(self):
        """Test that math engine handles NaN safely."""
        # Simulate NaN injection
        tensor_with_nan = np.array([1.0, float('nan'), 3.0])
        
        # Engine automatically fixes NaN
        fixed = check_and_fix_nan(tensor_with_nan, "test_tensor")
        
        # NaN should be converted to safe value (0)
        assert not np.any(np.isnan(fixed))

    def test_extreme_value_bounds(self):
        """Test that extreme values are handled."""
        extreme_data = {
            "tiny": sys.float_info.min,
            "huge": sys.float_info.max,
            "epsilon": sys.float_info.epsilon,
        }
        
        result = to_json(extreme_data)
        
        # Should not crash
        assert "tiny" in result
        assert "huge" in result

    def test_array_overflow_protection(self):
        """Test array bounds are respected."""
        # Large but reasonable array
        large_arr = np.random.rand(10000)
        large_arr[::100] = float('nan')
        
        result = to_json({"array": large_arr})
        parsed = __import__('json').loads(result)
        
        # Should process without crash
        assert len(parsed["array"]) == 10000

    def test_dict_depth_limits(self):
        """Test deeply nested dicts don't cause issues."""
        # Create reasonable depth
        data = {"level": 0}
        for i in range(1, 20):
            data = {"nested": data}
        
        result = to_json({"deep": data})
        
        # Should handle without crash
        assert "nested" in result


# =============================================================================
# REFERENCE: How to run these tests
# =============================================================================
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])