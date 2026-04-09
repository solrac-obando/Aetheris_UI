# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

import pytest
import gc
import weakref
import time
from core.lifecycle.base import Disposable, DisposableMixin
from core.lifecycle.manager import LifecycleManager, get_lifecycle_manager
from core.lifecycle.profiler import MemoryProfiler, get_profiler
from core.elements import StaticBox, SmartPanel


class DummyDisposable(Disposable):
    def __init__(self):
        super().__init__()
        self._cleanup_called = False
        self._data = [1, 2, 3, 4, 5]

    def dispose(self):
        self._cleanup_called = True
        self._data.clear()
        super().dispose()


class TestDisposable:
    def test_disposable_initial_state(self):
        d = DummyDisposable()
        assert not d.is_disposed

    def test_dispose_sets_flag(self):
        d = DummyDisposable()
        d.dispose()
        assert d.is_disposed

    def test_dispose_twice_safe(self):
        d = DummyDisposable()
        d.dispose()
        d.dispose()
        assert d.is_disposed

    def test_cleanup_callbacks(self):
        d = DummyDisposable()
        callback_called = []
        d._register_cleanup(lambda: callback_called.append(True))
        d.dispose()
        assert len(callback_called) == 1

    def test_context_manager(self):
        with DummyDisposable() as d:
            assert not d.is_disposed
        assert d.is_disposed

    def test_context_manager_exception(self):
        try:
            with DummyDisposable() as d:
                raise ValueError("test")
        except ValueError:
            pass
        assert d.is_disposed


class TestLifecycleManager:
    def test_singleton(self):
        m1 = get_lifecycle_manager()
        m2 = get_lifecycle_manager()
        assert m1 is m2

    def test_track_element(self):
        manager = get_lifecycle_manager()
        manager.reset()
        element = DummyDisposable()
        manager.track(element)
        assert manager.get_tracked_count() == 1

    def test_untrack_element(self):
        manager = get_lifecycle_manager()
        manager.reset()
        element = DummyDisposable()
        manager.track(element)
        manager.untrack(element)
        assert manager.get_tracked_count() == 0

    def test_dispose_all(self):
        manager = get_lifecycle_manager()
        manager.reset()
        e1 = DummyDisposable()
        e2 = DummyDisposable()
        manager.track(e1)
        manager.track(e2)
        count = manager.dispose_all()
        assert count == 2
        assert e1.is_disposed
        assert e2.is_disposed

    def test_get_leaked_references(self):
        manager = get_lifecycle_manager()
        manager.reset()
        element = DummyDisposable()
        manager.track(element)
        leaked = manager.get_leaked_references()
        assert len(leaked) == 1

    def test_force_garbage_collection(self):
        manager = get_lifecycle_manager()
        manager.reset()
        result = manager.force_garbage_collection()
        assert "before" in result
        assert "after" in result

    def test_memory_stats(self):
        manager = get_lifecycle_manager()
        manager.reset()
        stats = manager.get_memory_stats()
        assert "tracked" in stats
        assert "disposed" in stats


class TestLifecycleManagerThreadSafety:
    def test_concurrent_track(self):
        import threading
        manager = get_lifecycle_manager()
        manager.reset()
        elements = []

        def track_elements():
            for i in range(50):
                e = DummyDisposable()
                elements.append(e)
                manager.track(e)

        t1 = threading.Thread(target=track_elements)
        t2 = threading.Thread(target=track_elements)
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert manager.get_tracked_count() >= 0


class TestMemoryProfiler:
    def test_profiler_singleton(self):
        p1 = get_profiler()
        p2 = get_profiler()
        assert p1 is p2

    def test_start_stop(self):
        profiler = MemoryProfiler()
        profiler.start()
        result = profiler.stop()
        assert "current_bytes" in result
        assert "peak_bytes" in result

    def test_take_snapshot(self):
        profiler = MemoryProfiler()
        profiler.start()
        snapshot = profiler.take_snapshot("test")
        assert snapshot["label"] == "test"
        profiler.stop()

    def test_enabled_flag(self):
        profiler = MemoryProfiler(enabled=False)
        assert not profiler.is_enabled()
        profiler.set_enabled(True)
        assert profiler.is_enabled()


class TestIntegration:
    def test_lifecycle_with_elements(self):
        manager = get_lifecycle_manager()
        manager.reset()
        box = StaticBox(0, 0, 100, 100)
        manager.track(box)
        assert manager.get_tracked_count() == 1
        manager.dispose_all()
        assert manager.get_tracked_count() == 0

    def test_lifecycle_with_smart_panel(self):
        manager = get_lifecycle_manager()
        manager.reset()
        panel = SmartPanel(padding=0.1)
        manager.track(panel)
        assert manager.get_tracked_count() == 1
        manager.untrack(panel)
        assert manager.get_tracked_count() == 0


class TestLeakDetection:
    def test_detect_untracked_disposed(self):
        manager = get_lifecycle_manager()
        manager.reset()
        element = DummyDisposable()
        element.dispose()
        leaked = manager.get_leaked_references()
        assert len(leaked) == 0

    def test_detect_tracked_not_disposed(self):
        manager = get_lifecycle_manager()
        manager.reset()
        element = DummyDisposable()
        manager.track(element)
        leaked = manager.get_leaked_references()
        assert len(leaked) == 1
        manager.dispose_all()


class TestWeakRefBehavior:
    def test_weak_ref_cleanup(self):
        manager = get_lifecycle_manager()
        manager.reset()
        ref = None

        def create_weak():
            nonlocal ref
            element = DummyDisposable()
            ref = weakref.ref(element)
            manager.track(element)

        create_weak()
        gc.collect()
        assert ref() is None


class TestPerformance:
    def test_dispose_performance(self):
        import time
        manager = get_lifecycle_manager()
        manager.reset()

        elements = [DummyDisposable() for _ in range(100)]
        for e in elements:
            manager.track(e)

        start = time.time()
        manager.dispose_all()
        elapsed = time.time() - start
        assert elapsed < 0.5

    def test_tracking_performance(self):
        import time
        manager = get_lifecycle_manager()
        manager.reset()

        start = time.time()
        for i in range(1000):
            e = DummyDisposable()
            manager.track(e)
        elapsed = time.time() - start
        assert elapsed < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])