# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
JSON utilities for Aether web compatibility.
Converts NaN/Inf to null for JavaScript compatibility.
"""
import json
import math
import numpy as np
from typing import Any, Union


def _clean_value(val: Any) -> Any:
    """Clean a single value, converting NaN/Inf to None."""
    # Python float NaN/Inf
    if isinstance(val, float):
        if math.isnan(val) or math.isinf(val):
            return None
    
    # NumPy floating types
    if isinstance(val, (np.floating, np.integer)):
        float_val = float(val)
        if math.isnan(float_val) or math.isinf(float_val):
            return None
        if isinstance(val, np.integer):
            return int(val)
        return float_val
    
    # NumPy bool
    if isinstance(val, np.bool_):
        return bool(val)
    
    # NumPy array
    if isinstance(val, np.ndarray):
        return _clean_value(val.tolist())
    
    # List/tuple
    if isinstance(val, (list, tuple)):
        return [_clean_value(item) for item in val]
    
    # Dict
    if isinstance(val, dict):
        return {k: _clean_value(v) for k, v in val.items()}
    
    return val


def to_json(
    obj: Any,
    *,
    indent: Union[int, None] = None,
    sort_keys: bool = False,
    **kwargs
) -> str:
    """Serialize obj to JSON string with NaN/Inf -> null conversion.
    
    Args:
        obj: Object to serialize
        indent: Indentation level (None for compact)
        sort_keys: Whether to sort keys
        **kwargs: Additional kwargs for json.dumps
    
    Returns:
        JSON string
    
    Example:
        data = {"x": float('nan'), "y": 42}
        json_str = to_json(data)  # '{"y": 42, "x": null}'
    """
    cleaned = _clean_value(obj)
    return json.dumps(
        cleaned,
        indent=indent,
        sort_keys=sort_keys,
        **kwargs
    )


def to_json_safe(
    json_str: str,
    **kwargs
) -> Any:
    """Parse JSON string safely.
    
    Args:
        json_str: JSON string to parse
        **kwargs: Additional kwargs for json.loads
    
    Returns:
        Parsed Python object
    
    Example:
        data = to_json_safe('{"x": null, "y": 42}')
    """
    return json.loads(json_str, **kwargs)


def clean_value(value: Any) -> Any:
    """Clean a single value, converting NaN/Inf to None.
    
    Args:
        value: Any value to clean
    
    Returns:
        Cleaned value (None for NaN/Inf)
    
    Example:
        clean_value(float('nan'))  # None
        clean_value(np.float32(42))  # 42.0
    """
    return _clean_value(value)


def clean_dict(data: dict) -> dict:
    """Clean all NaN/Inf values in a dictionary.
    
    Args:
        data: Dictionary to clean
    
    Returns:
        New dictionary with NaN/Inf converted to None
    """
    return _clean_value(data)


def clean_list(data: list) -> list:
    """Clean all NaN/Inf values in a list.
    
    Args:
        data: List to clean
    
    Returns:
        New list with NaN/Inf converted to None
    """
    return _clean_value(data)


# For backwards compatibility
__all__ = [
    "to_json",
    "to_json_safe",
    "clean_value",
    "clean_dict",
    "clean_list",
]