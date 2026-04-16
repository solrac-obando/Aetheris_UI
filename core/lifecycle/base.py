# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

from typing import Any, Optional, Set, Callable
import weakref
import gc


class Disposable:
    _disposed_instances: weakref.WeakSet = weakref.WeakSet()

    def __init__(self):
        self._disposed = False
        self._cleanup_callbacks: list = []
        Disposable._disposed_instances.add(self)

    @property
    def is_disposed(self) -> bool:
        return self._disposed

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        self._run_cleanup()

    def _register_cleanup(self, callback: Callable[[], None]) -> None:
        if not self._disposed:
            self._cleanup_callbacks.append(callback)

    def _run_cleanup(self) -> None:
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception:
                pass
        self._cleanup_callbacks.clear()

    def __enter__(self) -> "Disposable":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.dispose()

    @classmethod
    def get_disposed_count(cls) -> int:
        return len(cls._disposed_instances)


class DisposableMixin(Disposable):
    def __init__(self):
        super().__init__()
        self._disposed = False

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        self._run_cleanup()

    def __del__(self):
        if not self._disposed:
            pass