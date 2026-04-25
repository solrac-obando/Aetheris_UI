# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

from typing import Dict, Any, Optional, List, Callable
import gc
import sys
import tracemalloc
import weakref
from core.lifecycle.manager import get_lifecycle_manager


class MemoryProfiler:
    """Utility to measure and record memory usage throughout the application lifecycle.
    
    Uses `tracemalloc` for detailed allocation tracking and `psutil` (if available)
    for process-level memory monitoring.
    """
    def __init__(self, enabled: bool = True) -> None:
        """Initialize the profiler."""
        self._enabled = enabled
        self._tracking = False
        self._snapshots: List[Dict[str, Any]] = []
        self._peak_memory = 0

    def start(self) -> None:
        """Start tracking memory allocations using `tracemalloc`."""
        if not self._enabled:
            return
        self._tracking = True
        tracemalloc.start()

    def stop(self) -> Dict[str, Any]:
        """Stop tracking and return current/peak memory statistics."""
        if not self._enabled or not self._tracking:
            return {"error": "Profiler not started"}
        self._tracking = False
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        self._peak_memory = peak
        return {
            "current_bytes": current,
            "peak_bytes": peak,
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024,
        }

    def take_snapshot(self, label: str = "") -> Dict[str, Any]:
        """Take a point-in-time snapshot of memory and lifecycle stats."""
        if not self._enabled:
            return {}
        gc.collect()
        manager = get_lifecycle_manager()
        snapshot = {
            "label": label,
            "memory": self._get_memory_info(),
            "lifecycle": manager.get_memory_stats(),
            "gc_stats": gc.get_stats(),
        }
        self._snapshots.append(snapshot)
        return snapshot

    def _get_memory_info(self) -> Dict[str, Any]:
        """Get RSS and VMS memory info from the current process."""
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            return {
                "rss_mb": mem_info.rss / 1024 / 1024,
                "vms_mb": mem_info.vms / 1024 / 1024,
            }
        except ImportError:
            return {}

    def get_snapshots(self) -> List[Dict[str, Any]]:
        """Return a copy of the recorded snapshots."""
        return self._snapshots.copy()

    def clear_snapshots(self) -> None:
        """Clear all recorded snapshots."""
        self._snapshots.clear()

    def is_enabled(self) -> bool:
        """Check if profiling is enabled."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable the profiler."""
        self._enabled = enabled


_global_profiler: Optional[MemoryProfiler] = None


def get_profiler() -> MemoryProfiler:
    """Get the global MemoryProfiler instance."""
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = MemoryProfiler()
    return _global_profiler


def profile_memory(enabled: bool = True) -> Callable:
    """Decorator to profile the memory usage of a function."""
    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            profiler = get_profiler()
            profiler.start()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                stats = profiler.stop()
                if stats.get("error"):
                    print(f"Memory profiler: {stats['error']}")
                else:
                    print(f"Memory - Current: {stats['current_mb']:.2f}MB, Peak: {stats['peak_mb']:.2f}MB")
        return wrapper
    return decorator