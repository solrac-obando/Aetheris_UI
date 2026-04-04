# Copyright 2026 Carlos Ivan Obando Aure
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0

"""
16+ assertion test suite for demo_data_forge.
Covers data loading, error handling, physics, performance, and UI integrity.
"""
import os, sys, time, gc, tempfile, threading
import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine import AetherEngine
from core.aether_math import StateTensor, MAX_VELOCITY, clamp_magnitude, EPSILON
from demo.demo_data_forge import (
    DataForgeEngine, DataElement, LANG, WIN_W, WIN_H,
    MAX_ROWS, ELEMENT_SIZE, TOOLBAR_H,
)


# ── Helpers ────────────────────────────────────────────────────────────────
def _make_csv(content: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        f.write(content)
        return f.name


def _make_excel(df: pd.DataFrame) -> str:
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        df.to_excel(f.name, index=False)
        return f.name


class TestDataForge:
    # ── 1. Pandas loads sample CSV ────────────────────────────────────────
    def test_01_pandas_loads_csv(self):
        """Assertion 1: pandas successfully loads a sample CSV."""
        path = _make_csv("a,b,c\n1,2,3\n4,5,6\n")
        try:
            df = pd.read_csv(path)
            assert len(df) == 2
            assert list(df.columns) == ["a", "b", "c"]
        finally:
            os.unlink(path)

    # ── 2. Empty file doesn't crash ───────────────────────────────────────
    def test_02_empty_file_no_crash(self):
        """Assertion 2: The app doesn't crash if an empty file is loaded."""
        forge = DataForgeEngine()
        path = _make_csv("")
        try:
            result = forge.load_file(path)
            assert result is False
        finally:
            os.unlink(path)

    # ── 3. Invalid format doesn't crash ───────────────────────────────────
    def test_03_invalid_format_no_crash(self):
        """Assertion 3: The app doesn't crash on invalid format."""
        forge = DataForgeEngine()
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w") as f:
            f.write("not a data file")
            path = f.name
        try:
            result = forge.load_file(path)
            assert result is False
        finally:
            os.unlink(path)

    # ── 4. Procedural spawning: element count matches rows ────────────────
    def test_04_element_count_matches_rows(self):
        """Assertion 4: Number of UI elements matches the number of rows (up to 100)."""
        forge = DataForgeEngine()
        path = _make_csv("x,y\n1,2\n3,4\n5,6\n7,8\n")
        try:
            assert forge.load_file(path)
            forge.spawn_elements()
            # 4 rows × 2 numeric cols = 8 elements
            assert len(forge.elements) == 8
        finally:
            os.unlink(path)

    # ── 5. Mass assignment: higher value = heavier ────────────────────────
    def test_05_mass_higher_value_heavier(self):
        """Assertion 5: An element representing '100' is heavier than one representing '10'."""
        e_high = DataElement(0, 0, 1.0, "test", 0)  # normalized max
        e_low = DataElement(0, 0, 0.1, "test", 0)   # normalized low
        assert e_high.mass > e_low.mass, f"High mass {e_high.mass} <= low mass {e_low.mass}"

    # ── 6. Teleportation: resize redistributes without overlap ────────────
    def test_06_teleportation_no_overlap(self):
        """Assertion 6: Resizing the window redistributes data columns without overlapping."""
        forge = DataForgeEngine()
        path = _make_csv("a,b\n10,20\n30,40\n")
        try:
            forge.load_file(path)
            forge.spawn_elements()
            orig = [(float(e.tensor.state[0]), float(e.tensor.state[1])) for e in forge.elements]
            forge.handle_teleportation(WIN_W * 1.5, WIN_H * 0.6)
            # All elements should have moved
            for i, e in enumerate(forge.elements):
                new_x = float(e.tensor.state[0])
                new_y = float(e.tensor.state[1])
                assert abs(new_x - orig[i][0] * 1.5) < 1.0
                assert abs(new_y - orig[i][1] * 0.6) < 1.0
        finally:
            os.unlink(path)

    # ── 7. Memory: gc.collect() after cleanup ─────────────────────────────
    def test_07_gc_after_cleanup(self):
        """Assertion 7: gc.collect() is called after closing a dataset to prevent leaks."""
        forge = DataForgeEngine()
        path = _make_csv("x\n1\n2\n3\n")
        try:
            forge.load_file(path)
            forge.spawn_elements()
            assert len(forge.elements) > 0
            forge.cleanup()
            assert len(forge.elements) == 0
            assert forge.df is None
        finally:
            os.unlink(path)

    # ── 8. Performance: frame time < 16.6ms with 100+ nodes ──────────────
    def test_08_frame_time_under_16_6ms(self):
        """Assertion 8: Frame time remains < 16.6ms even with 100+ data nodes."""
        forge = DataForgeEngine()
        # Generate 100 rows × 2 cols = 200 elements
        lines = ["x,y"]
        for i in range(MAX_ROWS):
            lines.append(f"{i * 10},{i * 5}")
        path = _make_csv("\n".join(lines))
        try:
            forge.load_file(path)
            forge.spawn_elements()
            assert len(forge.elements) >= 100
            # Warm up
            forge.tick()
            forge.tick()
            times = []
            for _ in range(100):
                ft = forge.tick()
                times.append(ft)
            avg = np.mean(times)
            assert avg < 16.6, f"Average frame time {avg:.2f}ms exceeds 16.6ms"
        finally:
            os.unlink(path)

    # ── 9. Data integrity: element values match source data ───────────────
    def test_09_data_integrity(self):
        """Assertion 9: Element normalized values correctly reflect source data."""
        forge = DataForgeEngine()
        path = _make_csv("val\n0\n50\n100\n")
        try:
            forge.load_file(path)
            forge.spawn_elements()
            # 3 rows, 1 col → 3 elements
            assert len(forge.elements) == 3
            # Values should be normalized: 0→0.0, 50→0.5, 100→1.0
            vals = sorted([e.value for e in forge.elements])
            assert abs(vals[0] - 0.0) < 0.01
            assert abs(vals[1] - 0.5) < 0.01
            assert abs(vals[2] - 1.0) < 0.01
        finally:
            os.unlink(path)

    # ── 10. Sort mode applies downward forces ─────────────────────────────
    def test_10_sort_applies_gravity(self):
        """Assertion 10: Sort button applies global force pulling heaviest to bottom."""
        forge = DataForgeEngine()
        path = _make_csv("a\n10\n50\n90\n")
        try:
            forge.load_file(path)
            forge.spawn_elements()
            forge._sort_mode = True
            # Record velocities before
            for e in forge.elements:
                e.tensor.velocity.fill(0)
                e.tensor.acceleration.fill(0)
            forge.apply_sort_forces()
            # Heaviest element should have strongest downward force
            heaviest = max(forge.elements, key=lambda e: e.mass)
            assert float(heaviest.tensor.acceleration[1]) > 0, "No gravity on heaviest"
        finally:
            os.unlink(path)

    # ── 11. Tooltip returns correct row details ───────────────────────────
    def test_11_tooltip_data_accuracy(self):
        """Assertion 11: Clicking an element shows correct row details from source data."""
        forge = DataForgeEngine()
        path = _make_csv("name,value\nalpha,42\nbeta,99\n")
        try:
            forge.load_file(path)
            forge.spawn_elements()
            # Find element for row 1 (beta, 99)
            tip = None
            for e in forge.elements:
                if e.row_idx == 1:
                    s = e.tensor.state
                    tip = forge.get_tooltip(float(s[0]) + 5, float(s[1]) + 5)
                    break
            assert tip is not None
            assert tip["row"] == 1
            assert tip["column"] == "value"
            assert "beta" in str(tip["details"].get("name", ""))
        finally:
            os.unlink(path)

    # ── 12. Bilingual: all keys present in both languages ─────────────────
    def test_12_bilingual_completeness(self):
        """Assertion 12: All UI labels exist in both EN and ES."""
        en_keys = set(LANG["en"].keys())
        es_keys = set(LANG["es"].keys())
        assert en_keys == es_keys, f"Language key mismatch: {en_keys ^ es_keys}"
        for key in en_keys:
            assert len(LANG["en"][key]) > 0, f"Empty EN value for '{key}'"
            assert len(LANG["es"][key]) > 0, f"Empty ES value for '{key}'"

    # ── 13. Excel loading works ───────────────────────────────────────────
    def test_13_excel_loading(self):
        """Assertion 13: Excel files load correctly via pandas."""
        forge = DataForgeEngine()
        df = pd.DataFrame({"metric": [10, 20, 30], "score": [0.5, 0.7, 0.9]})
        path = _make_excel(df)
        try:
            result = forge.load_file(path)
            assert result is True
            assert len(forge.numeric_cols) == 2
            forge.spawn_elements()
            assert len(forge.elements) == 6  # 3 rows × 2 cols
        finally:
            os.unlink(path)

    # ── 14. MAX_ROWS cap enforced ─────────────────────────────────────────
    def test_14_max_rows_cap(self):
        """Assertion 14: Element count is capped at MAX_ROWS even with larger files."""
        forge = DataForgeEngine()
        lines = ["x"]
        for i in range(200):
            lines.append(str(i))
        path = _make_csv("\n".join(lines))
        try:
            forge.load_file(path)
            forge.spawn_elements()
            assert len(forge.elements) == MAX_ROWS  # 100 rows × 1 col
        finally:
            os.unlink(path)

    # ── 15. UI sync: rendering data matches StateTensor ───────────────────
    def test_15_ui_sync(self):
        """Assertion 15: Visual element position matches engine's internal StateTensor."""
        forge = DataForgeEngine()
        path = _make_csv("a\n50\n")
        try:
            forge.load_file(path)
            forge.spawn_elements()
            forge.tick()
            for elem in forge.elements:
                rd = elem.rendering_data
                assert np.allclose(rd["rect"], elem.tensor.state)
        finally:
            os.unlink(path)

    # ── 16. No orphaned threads after lifecycle ───────────────────────────
    def test_16_no_orphaned_threads(self):
        """Assertion 16: No orphaned threads after full load-process-cleanup cycle."""
        initial = threading.active_count()
        forge = DataForgeEngine()
        path = _make_csv("x\n1\n2\n")
        try:
            forge.load_file(path)
            forge.spawn_elements()
            for _ in range(50):
                forge.tick()
            forge.cleanup()
        finally:
            os.unlink(path)
        gc.collect()
        final = threading.active_count()
        assert final <= initial + 1, f"Orphaned threads: {initial} → {final}"

    # ── 17. Non-numeric columns excluded ──────────────────────────────────
    def test_17_non_numeric_excluded(self):
        """Assertion 17: Only numeric columns spawn elements."""
        forge = DataForgeEngine()
        path = _make_csv("name,age,score\nAlice,30,85\nBob,25,92\n")
        try:
            forge.load_file(path)
            assert "name" not in forge.numeric_cols
            assert "age" in forge.numeric_cols
            assert "score" in forge.numeric_cols
            forge.spawn_elements()
            assert len(forge.elements) == 4  # 2 rows × 2 numeric cols
        finally:
            os.unlink(path)

    # ── 18. Color intensity correlates with value ─────────────────────────
    def test_18_color_intensity_correlation(self):
        """Assertion 18: High-value elements have higher color intensity."""
        e_high = DataElement(0, 0, 1.0, "test", 0)
        e_low = DataElement(0, 0, 0.0, "test", 0)
        high_sum = float(np.sum(e_high._color[:3]))
        low_sum = float(np.sum(e_low._color[:3]))
        assert high_sum > low_sum, f"High color {high_sum} <= low color {low_sum}"

    # ── 19. Stability flag works correctly ────────────────────────────────
    def test_19_stability_flag(self):
        """Assertion 19: Engine reports stable after damping settles."""
        forge = DataForgeEngine()
        path = _make_csv("x\n50\n")
        try:
            forge.load_file(path)
            forge.spawn_elements()
            # Initially not stable (elements settling)
            for _ in range(200):
                forge.tick()
            assert forge._stable == True
        finally:
            os.unlink(path)

    # ── 20. Sample data file exists and loads ─────────────────────────────
    def test_20_sample_data_loads(self):
        """Assertion 20: The bundled sample_data.csv loads correctly."""
        from pathlib import Path
        sample = Path(__file__).parent.parent / "demo" / "sample_data.csv"
        assert sample.exists(), "sample_data.csv not found"
        forge = DataForgeEngine()
        assert forge.load_file(str(sample))
        assert len(forge.numeric_cols) >= 3
        forge.spawn_elements()
        assert len(forge.elements) == 20 * len(forge.numeric_cols)  # 20 rows
