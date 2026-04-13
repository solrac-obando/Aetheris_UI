# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Stress tests for JSON utilities (NaN -> null conversion).
"""
import pytest
import json
import math
import sys
import time
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.json_utils import to_json


class TestJSONStressHighVolume:
    """Stress tests with high volume of data."""
    
    def test_10000_dicts_with_nan(self):
        """Test serializing 10000 dicts with NaN."""
        data = [{"x": float('nan'), "y": i} for i in range(10000)]
        
        result = to_json(data)
        parsed = json.loads(result)
        
        assert len(parsed) == 10000
        assert all(p["x"] is None for p in parsed)
    
    def test_1000_float_nans(self):
        """Test list with 1000 NaN values."""
        data = {"values": [float('nan') for _ in range(1000)]}
        
        result = to_json(data)
        
        # Should convert all NaN values
        parsed = json.loads(result)
        assert all(v is None for v in parsed["values"])
    
    def test_mixed_numpy_array_10k(self):
        """Test 10k element numpy array with mixed values."""
        arr = np.random.rand(10000)
        arr[::10] = float('nan')
        data = {"array": arr}
        
        result = to_json(data)
        parsed = json.loads(result)
        
        assert len(parsed["array"]) == 10000
    
    def test_tuple_with_nan(self):
        """Test tuple conversion."""
        data = {"tuple": (1.0, float('nan'), 3.0)}
        
        result = to_json(data)
        parsed = json.loads(result)
        
        assert isinstance(parsed["tuple"], list)
        assert parsed["tuple"][1] is None
    
    def test_nested_3_levels(self):
        """Test 3 level nested dict."""
        inner = {"value": float('nan')}
        middle = {"inner": inner}
        outer = {"middle": middle}
        
        result = to_json(outer)
        parsed = json.loads(result)
        
        assert parsed["middle"]["inner"]["value"] is None


class TestJSONStressMemory:
    """Memory stress tests."""
    
    def test_large_array_no_leak(self):
        """Test no memory leak with large arrays."""
        import tracemalloc
        
        tracemalloc.start()
        
        for _ in range(10):
            arr = np.random.rand(10000)
            arr[::100] = float('nan')
            data = {"arr": arr}
            result = to_json(data)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        assert peak < 50 * 1024 * 1024
    
    def test_repeated_serialization(self):
        """Test serializing same data repeatedly."""
        data = {"x": float('nan'), "y": 42, "arr": np.array([1, 2, float('nan'), 4])}
        
        for i in range(1000):
            result = to_json(data)
            parsed = json.loads(result)
            assert parsed["y"] == 42


class TestJSONStressConcurrent:
    """Concurrent serialization tests."""
    
    def test_parallel_serialization(self):
        """Test parallel serialization from multiple threads."""
        results = []
        
        def serialize_batch(start, count):
            batch_results = []
            for i in range(start, start + count):
                data = {
                    "index": i,
                    "value": float('nan') if i % 2 == 0 else i,
                    "arr": np.array([i, float('nan'), i + 1])
                }
                result = to_json(data)
                batch_results.append(result)
            return batch_results
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(serialize_batch, i * 250, 250)
                for i in range(4)
            ]
            for f in as_completed(futures):
                results.extend(f.result())
        
        assert len(results) == 1000
    
    def test_concurrent_same_data(self):
        """Test same data from multiple threads."""
        def serialize():
            data = {"x": float('nan'), "y": 42}
            return to_json(data)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: serialize(), range(100)))
        
        assert len(results) == 100
        for r in results:
            json.loads(r)


class TestJSONStressEdgeCases:
    """Edge case stress tests."""
    
    def test_all_numpy_dtypes(self):
        """Test all numpy dtypes."""
        data = {
            "float32": np.float32(1.5),
            "float64": np.float64(1.5),
            "int32": np.int32(1),
            "int64": np.int64(1),
            "bool": np.bool_(True),
            "nan_f32": np.float32(float('nan')),
            "inf_f64": np.float64(float('inf')),
        }
        
        result = to_json(data)
        parsed = json.loads(result)
        
        assert parsed["float32"] == 1.5
        assert parsed["nan_f32"] is None
        assert parsed["inf_f64"] is None
    
    def test_special_float_values(self):
        """Test special IEEE 754 values."""
        data = {
            "nan": float('nan'),
            "pos_inf": float('inf'),
            "neg_inf": float('-inf'),
            "pos_zero": 0.0,
            "neg_zero": -0.0,
            "epsilon": sys.float_info.epsilon,
            "max": sys.float_info.max,
            "min": sys.float_info.min,
        }
        
        result = to_json(data)
        parsed = json.loads(result)
        
        assert parsed["nan"] is None
        assert parsed["pos_inf"] is None
        assert parsed["neg_inf"] is None
    
    def test_nested_list(self):
        """Test nested list."""
        data = [[[[float('nan')]]]]
        
        result = to_json(data)
        parsed = json.loads(result)
        
        assert parsed[0][0][0][0] is None
    
    def test_performance_benchmark(self):
        """Benchmark serialization performance."""
        data = {
            "x": float('nan'),
            "y": 42,
            "arr": list(range(1000)),
            "nested": {"a": float('nan'), "b": 1}
        }
        
        iterations = 1000
        start = time.perf_counter()
        
        for _ in range(iterations):
            result = to_json(data)
        
        duration = time.perf_counter() - start
        rate = iterations / duration
        
        print(f"\n{iterations} serializations in {duration:.3f}s ({rate:.0f} ops/s)")
        
        # Should handle at least 100 ops/s (relaxed for containers)
        assert rate > 100


class TestJSONStressAttack:
    """Attack/malicious input tests."""
    
    def test_extremely_long_list(self):
        """Test with extremely long list."""
        data = {"values": [float('nan')] * 10000}
        
        result = to_json(data)
        parsed = json.loads(result)
        
        assert len(parsed["values"]) == 10000
    
    def test_wide_dict(self):
        """Test with wide dict (many keys)."""
        data = {f"key_{i}": float('nan') for i in range(5000)}
        
        result = to_json(data)
        parsed = json.loads(result)
        
        assert len(parsed) == 5000
    
    def test_nested_10_levels(self):
        """Test 10 level nested dict with NaN."""
        d = {"value": float('nan')}
        for _ in range(9):
            d = {"nested": d}
        
        result = to_json({"deep": d})
        parsed = json.loads(result)
        
        # Navigate through nested structure: deep -> nested(9 times) -> value = None
        current = parsed["deep"]
        for i in range(9):
            current = current["nested"]
        
        assert current["value"] is None
    
    def test_mixed_corner_cases(self):
        """Test mixed corner cases."""
        data = {
            "nan": float('nan'),
            "inf": float('inf'),
            "neg0": -0.0,
            "small": 1e-100,
            "large": 1e100,
            "arr": [1, float('nan'), -0.0],
            "nested": {"a": float('nan'), "b": float('inf')}
        }
        
        result = to_json(data)
        parsed = json.loads(result)
        
        assert parsed["nan"] is None
        assert parsed["inf"] is None
        assert parsed["nested"]["a"] is None
        assert parsed["nested"]["b"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])