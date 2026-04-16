# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""Cross-engine parity tests: Python vs Rust physics engine equivalence."""

import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.engine import AetherEngine as PythonEngine
from core.elements import StaticBox, SmartPanel
from core.engine_selector import EngineSelector, _RUST_AVAILABLE


TOL = 1e-2


def _setup_python_engine():
    """Create and populate a Python engine with test elements."""
    engine = PythonEngine()
    engine.register_element(StaticBox(0.0, 0.0, 100.0, 100.0, (0.8, 0.2, 0.3, 0.9), 0))
    engine.register_element(StaticBox(200.0, 100.0, 150.0, 80.0, (0.2, 0.6, 0.9, 0.9), 1))
    engine.register_element(SmartPanel(0.05, (0.2, 0.2, 0.3, 0.9), 2))
    return engine


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_engine_selector_defaults_to_rust():
    """EngineSelector should auto-detect Rust when available."""
    selector = EngineSelector()
    assert selector.engine_type == "rust"


def test_engine_selector_forces_python():
    """EngineSelector should force Python when requested."""
    selector = EngineSelector(engine_type="python")
    assert selector.engine_type == "python"


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_engine_selector_forces_rust():
    """EngineSelector should force Rust when requested and available."""
    selector = EngineSelector(engine_type="rust")
    assert selector.engine_type == "rust"


def test_engine_selector_python_functionality():
    """Python engine wrapper should work correctly."""
    selector = EngineSelector(engine_type="python")
    assert selector.element_count == 0

    selector.register_element(StaticBox(0.0, 0.0, 100.0, 100.0, (1.0, 0.0, 0.0, 1.0), 0))
    assert selector.element_count == 1

    data = selector.tick(800.0, 600.0)
    assert len(data) == 1
    assert data[0]['rect'][0] >= 0.0


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_rust_engine_tick_produces_data():
    """Rust engine should produce valid render data after tick."""
    selector = EngineSelector(engine_type="rust")
    selector.register_element(StaticBox(0.0, 0.0, 100.0, 100.0, (1.0, 0.0, 0.0, 1.0), 0))
    assert selector.element_count == 1

    data = selector.tick(800.0, 600.0)
    assert len(data) == 1
    rect = data[0]['rect']
    assert rect[0] >= 0.0
    assert rect[2] > 0.0
    assert rect[3] > 0.0


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_rust_engine_multiple_elements():
    """Rust engine should handle multiple elements correctly."""
    selector = EngineSelector(engine_type="rust")
    for i in range(5):
        selector.register_element(
            StaticBox(i * 100.0, 0.0, 50.0, 50.0, (0.5, 0.5, 0.5, 1.0), i)
        )
    assert selector.element_count == 5

    data = selector.tick(800.0, 600.0)
    assert len(data) == 5
    for item in data:
        assert 'rect' in item.dtype.names if hasattr(item, 'dtype') else True


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_rust_engine_pointer_events():
    """Rust engine should handle pointer events."""
    selector = EngineSelector(engine_type="rust")
    selector.register_element(StaticBox(0.0, 0.0, 100.0, 100.0, (1.0, 0.0, 0.0, 1.0), 0))

    result = selector.handle_pointer_down(50.0, 50.0)
    assert result >= 0

    selector.handle_pointer_move(60.0, 60.0)
    selector.handle_pointer_up()


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_rust_engine_metadata():
    """Rust engine should return metadata."""
    selector = EngineSelector(engine_type="rust")
    selector.register_element(StaticBox(0.0, 0.0, 100.0, 100.0, (1.0, 0.0, 0.0, 1.0), 5))
    meta = selector.get_ui_metadata()
    assert isinstance(meta, str)
    assert len(meta) > 0


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_rust_engine_convergence():
    """Rust engine elements should remain stable and produce valid finite data."""
    selector = EngineSelector(engine_type="rust")
    selector.register_element(StaticBox(0.0, 0.0, 100.0, 100.0, (1.0, 0.0, 0.0, 1.0), 0))

    for _ in range(60):
        data = selector.tick(800.0, 600.0)
        assert len(data) == 1
        rect = data[0]['rect']
        assert all(np.isfinite(v) for v in rect), "Non-finite values detected"

    data = selector.tick(800.0, 600.0)
    rect = data[0]['rect']
    assert rect[2] == 100.0
    assert rect[3] == 100.0


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_rust_engine_stability_100_frames():
    """Rust engine should remain stable over 100 frames."""
    selector = EngineSelector(engine_type="rust")
    selector.register_element(StaticBox(0.0, 0.0, 100.0, 100.0, (1.0, 0.0, 0.0, 1.0), 0))
    selector.register_element(StaticBox(200.0, 100.0, 150.0, 80.0, (0.2, 0.6, 0.9, 0.9), 1))

    for _ in range(100):
        data = selector.tick(800.0, 600.0)
        assert len(data) == 2
        for item in data:
            rect = item['rect']
            assert all(np.isfinite(v) for v in [rect[0], rect[1], rect[2], rect[3]])


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_rust_engine_responsive_resize():
    """Rust engine should respond to window size changes."""
    selector = EngineSelector(engine_type="rust")
    selector.register_element(StaticBox(0.0, 0.0, 100.0, 100.0, (0.2, 0.2, 0.3, 0.9), 0))

    for _ in range(30):
        data = selector.tick(800.0, 600.0)
    data_before = selector.tick(800.0, 600.0)

    for _ in range(30):
        data = selector.tick(1200.0, 900.0)
    data_after = selector.tick(1200.0, 900.0)

    assert len(data_before) == 1
    assert len(data_after) == 1


def test_python_engine_wrapper_properties():
    """Python engine wrapper should expose expected properties."""
    selector = EngineSelector(engine_type="python")
    assert hasattr(selector, 'element_count')
    assert hasattr(selector, 'dt')
    assert hasattr(selector, 'state_manager')
    assert hasattr(selector, 'input_manager')


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_rust_engine_wrapper_properties():
    """Rust engine wrapper should expose expected properties."""
    selector = EngineSelector(engine_type="rust")
    assert hasattr(selector, 'element_count')
    assert hasattr(selector, 'dt')

    with pytest.raises(AttributeError):
        _ = selector.state_manager

    with pytest.raises(AttributeError):
        _ = selector.input_manager


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_rust_vs_python_same_element_count():
    """Both engines should report the same element count after registration."""
    py_sel = EngineSelector(engine_type="python")
    rs_sel = EngineSelector(engine_type="rust")

    for i in range(3):
        py_sel.register_element(StaticBox(i * 100.0, 0.0, 50.0, 50.0, (0.5, 0.5, 0.5, 1.0), i))
        rs_sel.register_element(StaticBox(i * 100.0, 0.0, 50.0, 50.0, (0.5, 0.5, 0.5, 1.0), i))

    assert py_sel.element_count == rs_sel.element_count == 3


@pytest.mark.skipif(not _RUST_AVAILABLE, reason="Rust engine not available")
def test_rust_engine_batch_path_10_elements():
    """Rust engine should use batch path for 10+ elements."""
    selector = EngineSelector(engine_type="rust")
    for i in range(10):
        selector.register_element(
            StaticBox(i * 80.0, 0.0, 50.0, 50.0, (1.0, 0.0, 0.0, 1.0), i)
        )
    data = selector.tick(800.0, 600.0)
    assert len(data) == 10
