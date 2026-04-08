# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Dynamic Resource Limits - Auto-detection based on hardware.

This module calculates optimal limits based on system capabilities:
- CPU threads detection via multiprocessing
- Element limits: 800/hilo (Python) / 3000/hilo (Rust-like)
- Safety buffer: 20% reduction for 4 or fewer threads
- Performance mode: Auto enable for 8+ threads
"""
import os
import multiprocessing

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


def get_cpu_count() -> int:
    """Get number of CPU threads available."""
    if _HAS_PSUTIL:
        return psutil.cpu_count(logical=True)
    return multiprocessing.cpu_count()


def get_optimal_max_elements(
    base_per_thread: int = 800,
    cpu_count: int = None,
    safety_buffer: float = 0.20
) -> int:
    """
    Calculate optimal max elements based on hardware.
    
    Args:
        base_per_thread: Base elements per CPU thread (default 800)
        cpu_count: Override CPU count (None = auto-detect)
        safety_buffer: Safety reduction for low-end systems (20%)
    
    Returns:
        Optimal max elements for this hardware
    """
    if cpu_count is None:
        cpu_count = get_cpu_count()
    
    if cpu_count <= 4:
        effective_per_thread = int(base_per_thread * (1 - safety_buffer))
    else:
        effective_per_thread = base_per_thread
    
    return cpu_count * effective_per_thread


def get_bridge_limit_from_engine(engine_limit: int, multiplier: float = 3.0) -> int:
    """
    Calculate bridge limit from engine limit.
    Bridge can handle more elements (faster serialization).
    """
    return int(engine_limit * multiplier)


def is_performance_mode(cpu_count: int = None) -> bool:
    """Check if system should run in performance mode."""
    if cpu_count is None:
        cpu_count = get_cpu_count()
    return cpu_count >= 8


def get_system_profile() -> dict:
    """
    Get complete system profile for resource allocation.
    
    Returns:
        Dict with hardware profile and recommended limits
    """
    cpu_count = get_cpu_count()
    cpu_physical = psutil.cpu_count(logical=False) if _HAS_PSUTIL else cpu_count // 2
    
    profile = {
        "cpu_count_logical": cpu_count,
        "cpu_count_physical": cpu_physical,
        "performance_mode": is_performance_mode(cpu_count),
        "safety_mode": cpu_count <= 4,
    }
    
    if profile["safety_mode"]:
        profile["engine_limit"] = get_optimal_max_elements(800, cpu_count, 0.20)
        profile["bridge_limit"] = get_bridge_limit_from_engine(profile["engine_limit"], 3.0)
    elif profile["performance_mode"]:
        profile["engine_limit"] = get_optimal_max_elements(1000, cpu_count, 0.0)
        profile["bridge_limit"] = get_bridge_limit_from_engine(profile["engine_limit"], 4.0)
    else:
        profile["engine_limit"] = get_optimal_max_elements(800, cpu_count, 0.10)
        profile["bridge_limit"] = get_bridge_limit_from_engine(profile["engine_limit"], 3.0)
    
    return profile


def apply_limits_to_environment():
    """Apply calculated limits to environment variables."""
    profile = get_system_profile()
    
    os.environ["AETHERIS_MAX_ELEMENTS"] = str(profile["engine_limit"])
    os.environ["AETHERIS_MAX_SYNC_ELEMENTS"] = str(profile["bridge_limit"])
    os.environ["AETHERIS_PERFORMANCE_MODE"] = str(profile["performance_mode"]).lower()
    
    return profile


_MY_PROFILE = apply_limits_to_environment()