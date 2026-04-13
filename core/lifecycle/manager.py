# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

from typing import Dict, List, Any, Optional, Set
import weakref
import threading
import gc
import sys


class LifecycleManager:
    _instance: Optional["LifecycleManager"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._tracked: weakref.WeakSet = weakref.WeakSet()
        self._strong_refs: Dict[int, Any] = {}
        self._disposed: weakref.WeakSet = weakref.WeakSet()
        self._lock_internal = threading.Lock()
        self._initialized = True

    def track(self, element: Any) -> None:
        with self._lock_internal:
            try:
                self._tracked.add(element)
            except TypeError:
                pass

    def untrack(self, element: Any) -> None:
        with self._lock_internal:
            self._tracked.discard(element)

    def dispose_all(self) -> int:
        count = 0
        with self._lock_internal:
            elements = list(self._tracked)
            for element in elements:
                try:
                    if hasattr(element, "dispose") and callable(element.dispose):
                        element.dispose()
                        count += 1
                except Exception:
                    pass
            self._disposed.update(elements)
            self._tracked.clear()
        return count

    def get_tracked_count(self) -> int:
        with self._lock_internal:
            return len(self._tracked)

    def get_leaked_references(self) -> List[Dict[str, Any]]:
        gc.collect()
        leaked = []
        with self._lock_internal:
            for element in list(self._tracked):
                try:
                    if hasattr(element, "is_disposed"):
                        if not element.is_disposed:
                            leaked.append({
                                "type": type(element).__name__,
                                "has_dispose": hasattr(element, "dispose"),
                            })
                except Exception:
                    pass
        return leaked

    def force_garbage_collection(self) -> Dict[str, int]:
        before = len(self._tracked)
        gc.collect()
        after = len(self._tracked)
        return {"before": before, "after": after, "collected": before - after}

    def get_memory_stats(self) -> Dict[str, Any]:
        gc.collect()
        with self._lock_internal:
            return {
                "tracked": len(self._tracked),
                "disposed": len(self._disposed),
                "total_created": len(self._tracked) + len(self._disposed),
            }

    def reset(self) -> None:
        with self._lock_internal:
            self._tracked.clear()
            self._disposed.clear()
            self._strong_refs.clear()

    @classmethod
    def get_instance(cls) -> "LifecycleManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


def get_lifecycle_manager() -> LifecycleManager:
    return LifecycleManager.get_instance()