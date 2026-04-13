# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Tests for JSON utilities (NaN -> null conversion).
"""
import pytest
import json
import math
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.json_utils import (
    to_json,
    to_json_safe,
    clean_value,
    clean_dict,
    clean_list,
)


class TestAetherJSONEncoder:
    """Tests for NaN/Inf to null conversion."""
    
    def test_nan_to_null(self):
        """Test NaN converts to null."""
        data = {"value": float('nan')}
        result = to_json(data)
        
        # Should be null in JSON (without quotes), not NaN
        assert "null" in result.lower()
    
    def test_inf_to_null(self):
        """Test Infinity converts to null."""
        data = {"value": float('inf')}
        result = to_json(data)
        
        # null or Infinity should not appear as NaN-like
        assert "Infinity" not in result
    
    def test_negative_inf_to_null(self):
        """Test -Infinity converts to null."""
        data = {"value": float('-inf')}
        result = to_json(data)
        
        assert "-Infinity" not in result
    
    def test_normal_float(self):
        """Test normal float passes through."""
        data = {"value": 42.5}
        result = to_json(data)
        
        assert "42.5" in result
    
    def test_numpy_float32_nan(self):
        """Test np.float32 NaN converts to null."""
        data = {"value": np.float32(float('nan'))}
        result = to_json(data)
        
        # NaN should not appear as literal NaN
        assert "NaN" not in result
    
    def test_numpy_float64_nan(self):
        """Test np.float64 NaN converts to null."""
        data = {"value": np.float64(float('nan'))}
        result = to_json(data)
        
        assert "NaN" not in result
    
    def test_numpy_float32_normal(self):
        """Test np.float32 normal value."""
        data = {"value": np.float32(42.5)}
        result = to_json(data)
        
        assert "42.5" in result
    
    def test_numpy_int32(self):
        """Test np.int32 converts to int."""
        data = {"value": np.int32(42)}
        result = to_json(data)
        
        assert "42" in result
    
    def test_numpy_int64(self):
        """Test np.int64 converts to int."""
        data = {"value": np.int64(100)}
        result = to_json(data)
        
        assert "100" in result
    
    def test_numpy_array(self):
        """Test numpy array converts to list."""
        data = {"arr": np.array([1, 2, 3])}
        result = to_json(data)
        
        assert "[1, 2, 3]" in result
    
    def test_numpy_array_with_nan(self):
        """Test numpy array with NaN."""
        arr = np.array([1.0, float('nan'), 3.0])
        data = {"arr": arr}
        result = to_json(data)
        
        # Should not contain literal NaN
        assert "NaN" not in result
    
    def test_nested_dict(self):
        """Test nested dictionary."""
        data = {"outer": {"inner": float('nan')}}
        result = to_json(data)
        
        # Should convert to null
        assert "NaN" not in result
    
    def test_list_with_nan(self):
        """Test list with NaN."""
        data = [1.0, float('nan'), 3.0]
        result = to_json(data)
        
        # Should convert to null
        assert "NaN" not in result
    
    def test_mixed_types(self):
        """Test mixed numpy types."""
        data = {
            "float": np.float32(1.5),
            "int": np.int32(42),
            "nan": float('nan'),
            "inf": float('inf'),
            "normal": 3.14
        }
        result = to_json(data)
        
        # Should not contain NaN or Infinity
        assert "NaN" not in result
        assert "Infinity" not in result
    
    def test_roundtrip(self):
        """Test roundtrip with null."""
        original = {"x": float('nan'), "y": 42}
        json_str = to_json(original)
        parsed = json.loads(json_str)
        
        assert parsed["y"] == 42
        assert parsed["x"] is None


class TestCleanValue:
    """Tests for clean_value function."""
    
    def test_clean_nan(self):
        """Test NaN returns None."""
        assert clean_value(float('nan')) is None
    
    def test_clean_inf(self):
        """Test Infinity returns None."""
        assert clean_value(float('inf')) is None
    
    def test_clean_negative_inf(self):
        """Test -Infinity returns None."""
        assert clean_value(float('-inf')) is None
    
    def test_clean_float(self):
        """Test normal float passes."""
        assert clean_value(3.14) == 3.14
    
    def test_clean_numpy_float32(self):
        """Test np.float32 passes."""
        assert clean_value(np.float32(42.5)) == 42.5
    
    def test_clean_numpy_int(self):
        """Test np.int32 converts to int."""
        assert clean_value(np.int32(42)) == 42


class TestCleanDict:
    """Tests for clean_dict function."""
    
    def test_dict_with_nan(self):
        """Test dictionary with NaN."""
        data = {"x": float('nan'), "y": 42}
        result = clean_dict(data)
        
        assert result["x"] is None
        assert result["y"] == 42
    
    def test_nested_dict(self):
        """Test nested dictionary."""
        data = {"outer": {"inner": float('nan')}}
        result = clean_dict(data)
        
        assert result["outer"]["inner"] is None
    
    def test_list_in_dict(self):
        """Test list inside dictionary."""
        data = {"arr": [1.0, float('nan')]}
        result = clean_dict(data)
        
        assert result["arr"][1] is None


class TestCleanList:
    """Tests for clean_list function."""
    
    def test_list_with_nan(self):
        """Test list with NaN."""
        data = [1.0, float('nan'), 3.0]
        result = clean_list(data)
        
        assert result[1] is None
    
    def test_empty_list(self):
        """Test empty list."""
        data = []
        result = clean_list(data)
        
        assert result == []


class TestToJsonSafe:
    """Tests for to_json_safe."""
    
    def test_parse_null(self):
        """Test parsing null."""
        result = to_json_safe('{"x": null, "y": 42}')
        
        assert result["x"] is None
        assert result["y"] == 42
    
    def test_parse_complex(self):
        """Test parsing complex JSON."""
        json_str = '{"arr": [1, 2, 3], "nested": {"a": 1}}'
        result = to_json_safe(json_str)
        
        assert result["arr"] == [1, 2, 3]


class TestEdgeCases:
    """Edge case tests."""
    
    def test_all_nans(self):
        """Test all values are NaN."""
        data = {"a": float('nan'), "b": float('nan')}
        result = to_json(data)
        
        # Should not contain literal NaN
        assert "NaN" not in result
    
    def test_no_nan(self):
        """Test no NaN values."""
        data = {"x": 1, "y": 2, "z": 3}
        result = to_json(data)
        
        assert "null" not in result
    
    def test_boolean(self):
        """Test boolean values."""
        data = {"flag": True, "active": False}
        result = to_json(data)
        
        assert "true" in result
        assert "false" in result
    
    def test_numpy_bool(self):
        """Test numpy boolean."""
        data = {"flag": np.bool_(True)}
        result = to_json(data)
        
        assert "true" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])