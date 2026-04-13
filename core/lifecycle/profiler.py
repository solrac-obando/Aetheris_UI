# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

from typing import Dict, Any, Optional, List
import gc
import sys
import tracemalloc
import weakref
from core.lifecycle.manager import get_lifecycle_manager


class MemoryProfiler:
    def __init__(self, enabled: bool = True):
        self._enabled = enabled
        self._tracking = False
        self._snapshots: List[Dict[str, Any]] = []
        self._peak_memory = 0

    def start(self) -> None:
        if not self._enabled:
            return
        self._tracking = True
        tracemalloc.start()

    def stop(self) -> Dict[str, Any]:
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
        return self._snapshots.copy()

    def clear_snapshots(self) -> None:
        self._snapshots.clear()

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled


_global_profiler: Optional[MemoryProfiler] = None


def get_profiler() -> MemoryProfiler:
    global _global_profiler
    if _global_profiler is None:
        _global_profiler = MemoryProfiler()
    return _global_profiler


def profile_memory(enabled: bool = True):
    def decorator(func):
        def wrapper(*args, **kwargs):
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