# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
Dynamic Resource Limits - Auto-detection based on hardware.

This module calculates optimal limits based on system capabilities:
- CPU threads detection via multiprocessing
- Element limits: base_per_thread * cpu_count
- Safety margin: 35% reduction for stable operation (as per M2 spec)
- Performance mode: Auto enable for 8+ threads

M2 SPEC: "If hardware detects theoretical capacity 80x, limit operative to 50x.
This ensures OS has enough headroom and FPS stay locked at 60 without fluctuation."
"""
import os
import multiprocessing

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False

# M2 SAFETY MARGIN: 35% - guarantees stable 60 FPS
SAFETY_MARGIN = 0.35


def get_cpu_count() -> int:
    """Get number of CPU threads available."""
    if _HAS_PSUTIL:
        return psutil.cpu_count(logical=True)
    return multiprocessing.cpu_count()


def get_optimal_max_elements(
    base_per_thread: int = 800,
    cpu_count: int = None,
    safety_margin: float = SAFETY_MARGIN
) -> int:
    """
    Calculate optimal max elements based on hardware with safety margin.
    
    M2 SPEC: operative_limit = theoretical_limit * (1 - safety_margin)
    With 35% safety margin: operative = theoretical * 0.65
    
    Args:
        base_per_thread: Base elements per CPU thread (default 800)
        cpu_count: Override CPU count (None = auto-detect)
        safety_margin: Safety reduction (default 35% for stable 60 FPS)
    
    Returns:
        Operative max elements for stable 60 FPS
    """
    if cpu_count is None:
        cpu_count = get_cpu_count()
    
    # Calculate theoretical capacity
    theoretical = cpu_count * base_per_thread
    
    # Apply safety margin for stable operation
    operative = int(theoretical * (1 - safety_margin))
    
    return operative


def get_optimal_batch_size(max_elements: int) -> int:
    """
    Get optimal batch size for given max elements.
    
    Args:
        max_elements: Maximum elements to process
        
    Returns:
        Optimal batch size (typically 10-20% of max)
    """
    return max(max_elements // 10, 100)


def get_theoretical_capacity(cpu_count: int = None) -> int:
    """Get theoretical maximum without safety margin."""
    if cpu_count is None:
        cpu_count = get_cpu_count()
    return cpu_count * 800


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
    
    base_per_thread = 800 if cpu_count <= 4 else 1000
    
    profile = {
        "cpu_count_logical": cpu_count,
        "cpu_count_physical": cpu_physical,
        "performance_mode": is_performance_mode(cpu_count),
        "safety_mode": cpu_count <= 4,
        "safety_margin": SAFETY_MARGIN,
        "base_per_thread": base_per_thread,
        "theoretical_capacity": get_theoretical_capacity(cpu_count),
    }
    
    # Apply safety margin
    profile["engine_limit"] = get_optimal_max_elements(base_per_thread, cpu_count, SAFETY_MARGIN)
    profile["bridge_limit"] = get_bridge_limit_from_engine(profile["engine_limit"], 3.0)
    
    return profile


def apply_limits_to_environment():
    """Apply calculated limits to environment variables."""
    profile = get_system_profile()
    
    os.environ["AETHERIS_MAX_ELEMENTS"] = str(profile["engine_limit"])
    os.environ["AETHERIS_MAX_SYNC_ELEMENTS"] = str(profile["bridge_limit"])
    os.environ["AETHERIS_PERFORMANCE_MODE"] = str(profile["performance_mode"]).lower()
    os.environ["AETHERIS_SAFETY_MARGIN"] = str(SAFETY_MARGIN)
    
    return profile


_MY_PROFILE = apply_limits_to_environment()