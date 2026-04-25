# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

from typing import Any, Optional, Set, Callable
import weakref
import gc


class Disposable:
    """Base class for objects that require explicit resource cleanup.
    
    Implements the RAII pattern via __enter__/__exit__ and provides a
    centralized cleanup mechanism using callbacks.
    """
    _disposed_instances: weakref.WeakSet = weakref.WeakSet()

    def __init__(self) -> None:
        """Initialize the disposable object and track it globally."""
        self._disposed = False
        self._cleanup_callbacks: list = []
        Disposable._disposed_instances.add(self)

    @property
    def is_disposed(self) -> bool:
        """Return True if the object has been disposed."""
        return self._disposed

    def dispose(self) -> None:
        """Execute cleanup logic and mark the object as disposed.
        
        Safe to call multiple times (idempotent).
        """
        if self._disposed:
            return
        self._disposed = True
        self._run_cleanup()

    def _register_cleanup(self, callback: Callable[[], None]) -> None:
        """Register a callback to be executed during disposal."""
        if not self._disposed:
            self._cleanup_callbacks.append(callback)

    def _run_cleanup(self) -> None:
        """Execute all registered cleanup callbacks."""
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception:
                # Suppress exceptions during cleanup to ensure all callbacks run
                pass
        self._cleanup_callbacks.clear()

    def __enter__(self) -> "Disposable":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.dispose()

    @classmethod
    def get_disposed_count(cls) -> int:
        """Get the current count of tracked disposed instances."""
        return len(cls._disposed_instances)


class DisposableMixin(Disposable):
    """Mixin to add Disposable behavior to existing classes."""
    def __init__(self) -> None:
        super().__init__()
        self._disposed = False

    def dispose(self) -> None:
        """Mark as disposed and run cleanup."""
        if self._disposed:
            return
        self._disposed = True
        self._run_cleanup()

    def __del__(self) -> None:
        """Finalizer fallback. Warning: __del__ is not guaranteed to run."""
        if not self._disposed:
            # Optionally log a warning here in debug mode
            pass